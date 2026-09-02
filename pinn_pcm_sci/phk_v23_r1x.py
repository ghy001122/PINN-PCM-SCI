"""Bounded clean-coupling exploration and confirmation campaign for PHK-V2.3."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .phk_v22r_pinn import (
    CollocationMixture,
    FrequencyBand,
    PHASE_TRANSFORM_JACOBIAN_NORMALIZED,
    PHASE_TRANSFORM_LEGACY,
    POTENTIAL_TRANSFORM_LEGACY,
    POTENTIAL_TRANSFORM_TOP_DIRICHLET_HARD_LIFT,
    PhkCollocationSampler,
    PhkV22RModel,
    PhkV22RPhysics,
    interior_diagnostic_terms,
    phase_kinetic_rhs_from_laplacian,
)
from .phk_v22r_prediction import write_prediction_carrier
from .phk_v22r_training import (
    PhkTrainingConfig,
    TrainingObservation,
    TrainingStepSpec,
    train,
)
from .phk_v23_r1a_config import ConFIGGradientCombiner


ROOT = Path(__file__).resolve().parents[1]
PROGRAM_CONTRACT_PATH = (
    ROOT / "configs" / "phk_v23" / "program_contract_r1x_bounded_clean_coupling.json"
)
METHOD_CONTRACT_PATH = (
    ROOT / "configs" / "phk_v23" / "method_contract_r1x_clean_coupling.json"
)
EXPLORATION_CONTRACT_PATH = (
    ROOT / "configs" / "phk_v23" / "exploration_contract_r1x_bounded_clean_coupling.json"
)
DEPLOYED_SOURCE_MANIFEST_PATH = (
    ROOT / "cloud" / "phk_v23_r1x_autodl" / "deployed-source-manifest.json"
)

ET_GROUPS = (
    "G1_ELECTRIC_PDE",
    "G2_THERMAL_PDE",
    "G4_ET_AUXILIARY",
)
PHASE_GROUPS = ("G3_PHASE_PDE", "G4_PHASE_AUXILIARY")
JOINT_GROUPS = (
    "G1_ELECTRIC_PDE",
    "G2_THERMAL_PDE",
    "G3_PHASE_PDE",
    "G4_BOUNDARY_INITIAL",
)
READINESS_STEPS = (200, 225, 250, 275, 300)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected one JSON object: {path}")
    return value


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _sha256_tensor(value: torch.Tensor) -> str:
    array = value.detach().to(device="cpu").contiguous().numpy()
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(json.dumps(list(array.shape), separators=(",", ":")).encode("ascii"))
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest().upper()


def _write_json_exclusive(path: Path, payload: Mapping[str, Any]) -> None:
    exact = Path(path)
    exact.parent.mkdir(parents=True, exist_ok=True)
    with exact.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def _finite(value: torch.Tensor | float) -> float:
    result = float(value.detach().cpu()) if isinstance(value, torch.Tensor) else float(value)
    if not math.isfinite(result):
        raise FloatingPointError("R1X_NUMERICAL_INVALID: non-finite scalar")
    return result


@dataclass(frozen=True)
class CampaignVariant:
    variant_id: str
    potential_transform: str
    phase_transform: str
    ramp_length: int
    maximum_updates: int
    extra_full_joint_updates: int = 0

    def __post_init__(self) -> None:
        allowed = {
            "E1_CLEAN_COUPLING_EXPLORATION",
            "E2_TOP_DIRICHLET_HARD_LIFT",
            "E2_PHASE_JACOBIAN_NORMALIZED_OUTPUT",
            "E2_SMOOTHER_COUPLING_RAMP",
        }
        if self.variant_id not in allowed:
            raise ValueError("unknown or non-exclusive campaign variant")
        changed_potential = self.potential_transform != POTENTIAL_TRANSFORM_LEGACY
        changed_phase = self.phase_transform != PHASE_TRANSFORM_LEGACY
        if changed_potential and changed_phase:
            raise ValueError("an E2 variant may change only one output-transform axis")
        if self.ramp_length not in {400, 800}:
            raise ValueError("campaign ramp length must be 400 or 800")
        if self.maximum_updates not in {1800, 2200}:
            raise ValueError("campaign base update count must be 1800 or 2200")
        if self.extra_full_joint_updates not in {0, 500}:
            raise ValueError("E3 may add exactly zero or 500 full-joint updates")

    @property
    def total_updates(self) -> int:
        return self.maximum_updates + self.extra_full_joint_updates

    def with_e3_extension(self) -> "CampaignVariant":
        if self.extra_full_joint_updates:
            raise ValueError("E3 extension is already present")
        return CampaignVariant(
            self.variant_id,
            self.potential_transform,
            self.phase_transform,
            self.ramp_length,
            self.maximum_updates,
            500,
        )


E1 = CampaignVariant(
    "E1_CLEAN_COUPLING_EXPLORATION",
    POTENTIAL_TRANSFORM_LEGACY,
    PHASE_TRANSFORM_LEGACY,
    400,
    1800,
)
E2_TOP_HARD_LIFT = CampaignVariant(
    "E2_TOP_DIRICHLET_HARD_LIFT",
    POTENTIAL_TRANSFORM_TOP_DIRICHLET_HARD_LIFT,
    PHASE_TRANSFORM_LEGACY,
    400,
    1800,
)
E2_PHASE_NORMALIZED = CampaignVariant(
    "E2_PHASE_JACOBIAN_NORMALIZED_OUTPUT",
    POTENTIAL_TRANSFORM_LEGACY,
    PHASE_TRANSFORM_JACOBIAN_NORMALIZED,
    400,
    1800,
)
E2_SMOOTHER_RAMP = CampaignVariant(
    "E2_SMOOTHER_COUPLING_RAMP",
    POTENTIAL_TRANSFORM_LEGACY,
    PHASE_TRANSFORM_LEGACY,
    800,
    2200,
)
VARIANTS = {
    variant.variant_id: variant
    for variant in (E1, E2_TOP_HARD_LIFT, E2_PHASE_NORMALIZED, E2_SMOOTHER_RAMP)
}


def load_r1x_contracts() -> dict[str, dict[str, Any]]:
    contracts = {
        "program": _read_json(PROGRAM_CONTRACT_PATH),
        "method": _read_json(METHOD_CONTRACT_PATH),
        "exploration": _read_json(EXPLORATION_CONTRACT_PATH),
    }
    expected = {
        "program": "phk-v23-r1x-program-contract-v1",
        "method": "phk-v23-r1x-method-contract-v1",
        "exploration": "phk-v23-r1x-exploration-contract-v1",
    }
    for name, schema in expected.items():
        if contracts[name].get("schema_id") != schema:
            raise ValueError(f"unsupported R1X {name} contract")
    authorization = contracts["program"]["authorization"]
    for key in (
        "contract_code_test_document_writes",
        "non_voting_explorations",
        "one_frozen_confirmation_after_competence_signal",
        "reference_free_cloud_prediction",
        "local_nominal_evaluation_after_shutdown",
        "selective_commit_and_push_main",
    ):
        if authorization.get(key) is not True:
            raise PermissionError(f"R1X authorization missing: {key}")
    for key in (
        "fourth_exploration",
        "second_confirmation",
        "seed_change",
        "stress_prediction_or_unseal",
        "pjgr_or_r2",
        "low_fidelity_route",
        "benchmark_physics_reference_or_evaluator_change",
        "submission_external_contact_or_disclosure",
    ):
        if authorization.get(key) is not False:
            raise PermissionError(f"R1X out-of-scope authorization detected: {key}")
    return contracts


def _contract_identity() -> dict[str, dict[str, str]]:
    return {
        name: {
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": _sha256_path(path),
        }
        for name, path in (
            ("program", PROGRAM_CONTRACT_PATH),
            ("method", METHOD_CONTRACT_PATH),
            ("exploration", EXPLORATION_CONTRACT_PATH),
        )
    }


def validate_campaign_counts(*, explorations: int, confirmations: int) -> None:
    if not 0 <= int(explorations) <= 3:
        raise PermissionError("R1X exploration count exceeds the frozen maximum")
    if not 0 <= int(confirmations) <= 1:
        raise PermissionError("R1X confirmation count exceeds the frozen maximum")


def accelerated_active_windows(optimizer_step: int) -> int:
    step = int(optimizer_step)
    if step <= 0:
        raise ValueError("optimizer step must be positive")
    if step <= 50:
        return 1
    if step <= 100:
        return 2
    if step <= 150:
        return 3
    return 4


def smoothstep_alpha(position: int, length: int) -> float:
    index = int(position)
    count = int(length)
    if count < 2 or not 0 <= index < count:
        raise ValueError("ramp position is outside its frozen inclusive endpoints")
    r = index / float(count - 1)
    return 3.0 * r * r - 2.0 * r * r * r


def readiness_gate(metrics: Mapping[str, Any]) -> bool:
    if metrics.get("finite") is not True:
        return False
    try:
        for window in ("W1", "W3"):
            values = metrics[window]
            if float(values["thermal_activation_fraction"]) < 0.02:
                return False
            if float(values["positive_cold_kinetic_growth_fraction"]) < 0.02:
                return False
            if float(values["joule_q95_roi"]) <= 1.0e-12:
                return False
            if not all(math.isfinite(float(value)) for value in values.values()):
                return False
    except (KeyError, TypeError, ValueError):
        return False
    return True


class CampaignController:
    """Reference-blind staged state machine queried before every optimizer step."""

    def __init__(self, variant: CampaignVariant) -> None:
        self.variant = variant
        self.ready_step: int | None = None
        self.stop_requested = False
        self.reference_blind_outcome = "RUNNING"
        self._last_readiness_step: int | None = None
        self._consecutive_readiness_passes = 0
        self.readiness_history: list[dict[str, Any]] = []

    @property
    def ramp_start(self) -> int | None:
        return None if self.ready_step is None else self.ready_step + 1

    @property
    def ramp_end(self) -> int | None:
        return (
            None
            if self.ramp_start is None
            else self.ramp_start + self.variant.ramp_length - 1
        )

    def record_readiness(self, optimizer_step: int, metrics: Mapping[str, Any]) -> None:
        step = int(optimizer_step)
        if step not in READINESS_STEPS:
            raise ValueError("readiness may only vote at frozen checkpoints")
        if self.ready_step is not None:
            return
        if self._last_readiness_step is not None and step <= self._last_readiness_step:
            raise ValueError("readiness checkpoints must be strictly ordered")
        passed = readiness_gate(metrics)
        self.readiness_history.append({"optimizer_step": step, "passed": passed, "metrics": dict(metrics)})
        self._consecutive_readiness_passes = (
            self._consecutive_readiness_passes + 1 if passed else 0
        )
        self._last_readiness_step = step
        if self._consecutive_readiness_passes >= 2:
            self.ready_step = step
            self.reference_blind_outcome = "ET_READY_CONTINUE"
        elif step == 300:
            self.stop_requested = True
            self.reference_blind_outcome = "ET_NOT_READY"

    def step_spec(self, optimizer_step: int, total_updates: int) -> TrainingStepSpec:
        step = int(optimizer_step)
        if int(total_updates) != self.variant.total_updates:
            raise ValueError("R1X total update identity drift")
        windows = accelerated_active_windows(step)
        if self.ready_step is None or step <= self.ready_step:
            return TrainingStepSpec(
                stage="CLEAN_ELECTROTHERMAL_WARMUP",
                block_type="ELECTROTHERMAL_BLOCK",
                active_windows=windows,
                coupling_alpha=0.0,
                active_heads=("potential", "temperature"),
                active_loss_groups=ET_GROUPS,
            )
        assert self.ramp_start is not None and self.ramp_end is not None
        if step <= self.ramp_end:
            local_position = step - self.ramp_start
            cycle = (local_position + 1) % 5
            if cycle in {1, 2}:
                block = "ELECTROTHERMAL_BLOCK"
                heads = ("potential", "temperature")
                groups = ET_GROUPS
            elif cycle in {3, 4}:
                block = "PHASE_BLOCK"
                heads = ("phase",)
                groups = PHASE_GROUPS
            else:
                block = "JOINT_BLOCK"
                heads = ("potential", "temperature", "phase")
                groups = JOINT_GROUPS
            return TrainingStepSpec(
                stage="COUPLING_RAMP_AND_BLOCK_ALTERNATION",
                block_type=block,
                active_windows=windows,
                coupling_alpha=smoothstep_alpha(local_position, self.variant.ramp_length),
                active_heads=heads,
                active_loss_groups=groups,
            )
        return TrainingStepSpec(
            stage="FULL_PHYSICS_JOINT_CLOSURE",
            block_type="JOINT_BLOCK",
            active_windows=4,
            coupling_alpha=1.0,
            active_heads=("potential", "temperature", "phase"),
            active_loss_groups=JOINT_GROUPS,
        )


def build_campaign_model(
    *,
    physics: PhkV22RPhysics,
    hidden_width: int,
    hidden_layers: int,
    frequency_band: FrequencyBand,
    variant: CampaignVariant,
) -> PhkV22RModel:
    return PhkV22RModel(
        physics=physics,
        arm="STRONG_RAW",
        hidden_width=hidden_width,
        hidden_layers=hidden_layers,
        frequency_band=frequency_band,
        potential_output_transform=variant.potential_transform,
        phase_output_transform=variant.phase_transform,
        phase_jacobian_beta_cap=32.0,
    )


def _model_factory(variant: CampaignVariant):
    def factory(*, physics, config, frequency_band):
        return build_campaign_model(
            physics=physics,
            hidden_width=config.hidden_width,
            hidden_layers=config.hidden_layers,
            frequency_band=frequency_band,
            variant=variant,
        )

    return factory


def _head_vector(model: PhkV22RModel, head: str) -> torch.Tensor:
    return torch.cat(
        tuple(parameter.detach().reshape(-1) for parameter in model.heads[head].parameters())
    )


def _relative_update(before: torch.Tensor, after: torch.Tensor) -> float:
    denominator = max(_finite(torch.linalg.vector_norm(before)), 1.0e-18)
    return _finite(torch.linalg.vector_norm(after - before)) / denominator


def _second_axis(value: torch.Tensor, coordinates: torch.Tensor, axis: int) -> torch.Tensor:
    first = torch.autograd.grad(
        value,
        coordinates,
        grad_outputs=torch.ones_like(value),
        create_graph=True,
        retain_graph=True,
    )[0][:, axis : axis + 1]
    return torch.autograd.grad(
        first,
        coordinates,
        grad_outputs=torch.ones_like(first),
        create_graph=True,
        retain_graph=True,
    )[0][:, axis : axis + 1]


def _quantile(value: torch.Tensor, q: float) -> float:
    return _finite(torch.quantile(value.detach().reshape(-1), q))


def build_readiness_pool(
    *, model: PhkV22RModel, dtype: torch.dtype, device: torch.device
) -> torch.Tensor:
    sampler = PhkCollocationSampler(
        physics=model.physics,
        mixture=CollocationMixture(),
        seed=17,
    )
    return sampler.interior_uniform(
        2048,
        active_windows=4,
        dtype=dtype,
        device=device,
    ).detach()


def _pool_metrics(
    model: PhkV22RModel,
    pool: torch.Tensor,
    *,
    coupling_alpha: float,
) -> dict[str, Any]:
    q = pool.detach().clone().requires_grad_(True)
    terms = interior_diagnostic_terms(
        model, q, coupling_alpha=coupling_alpha
    )
    fields = model(q)
    temperature = fields[:, 1:2]
    phase = fields[:, 2:3]
    initial_phase = model.physics.initial_phase(q)
    initial_laplacian = _second_axis(initial_phase, q, 0) + _second_axis(
        initial_phase, q, 1
    )
    cold_kinetic = phase_kinetic_rhs_from_laplacian(
        model.physics,
        temperature=temperature,
        phase=initial_phase,
        phase_laplacian=initial_laplacian,
    )
    roi = (q[:, 0].abs() <= 0.55) & (q[:, 1] >= 0.0) & (q[:, 1] <= 0.55)
    windows: dict[str, Any] = {}
    for index, window in ((0, "W1"), (2, "W3")):
        block = torch.zeros(q.shape[0], dtype=torch.bool, device=q.device)
        block[index * 512 : (index + 1) * 512] = True
        mask = block & roi
        if not bool(torch.any(mask)):
            raise RuntimeError(f"R1X readiness pool has no ROI points in {window}")
        windows[window] = {
            "thermal_activation_fraction": _finite(
                torch.mean((temperature[mask] >= model.physics.theta_transition).to(torch.float64))
            ),
            "positive_cold_kinetic_growth_fraction": _finite(
                torch.mean((cold_kinetic[mask] > 0.0).to(torch.float64))
            ),
            "joule_q95_roi": _quantile(terms["joule_density"][mask], 0.95),
        }
    late_recovery: dict[str, float] = {}
    for index, window in ((1, "W2"), (3, "W4")):
        block = torch.zeros(q.shape[0], dtype=torch.bool, device=q.device)
        block[index * 512 : (index + 1) * 512] = True
        mask = block & roi
        late_recovery[f"temperature_q95_roi_{window}"] = _quantile(
            temperature[mask], 0.95
        )
    diagnostics = model.read_only_output_diagnostics(q)
    jacobian = diagnostics.analytic_output_jacobians["phase"]
    global_q95 = _quantile(terms["joule_density"], 0.95)
    roi_q95 = _quantile(terms["joule_density"][roi], 0.95)
    result = {
        **windows,
        "finite": True,
        "phase_max": _finite(torch.max(phase)),
        "phase_activity_fraction": _finite(torch.mean((phase >= 0.5).to(torch.float64))),
        "positive_kinetic_growth_fraction": _finite(
            torch.mean((terms["phase_kinetic_rhs"] > 0.0).to(torch.float64))
        ),
        "temperature_max": _finite(torch.max(temperature)),
        "joule_q95_global": global_q95,
        "joule_q95_roi": roi_q95,
        "joule_localization_q95_ratio": (
            None if global_q95 <= 0.0 else roi_q95 / global_q95
        ),
        "phase_jacobian_q50": _quantile(jacobian, 0.50),
        "phase_jacobian_q95": _quantile(jacobian, 0.95),
        **late_recovery,
    }
    if not all(
        value is None or isinstance(value, (bool, str)) or math.isfinite(float(value))
        for value in result.values()
        if not isinstance(value, dict)
    ):
        result["finite"] = False
    return result


class R1XTelemetryObserver:
    """Small reference-blind observer for readiness and mechanism telemetry."""

    requested_phases = frozenset(
        {"PRE_RUN", "PRE_BACKWARD", "POST_BACKWARD_PRE_CLIP", "POST_STEP"}
    )

    def __init__(self, *, controller: CampaignController, run_directory: Path) -> None:
        self.controller = controller
        self.run_directory = Path(run_directory)
        self.telemetry_path = self.run_directory / "r1x-telemetry.jsonl"
        self.handle = None
        self.pool: torch.Tensor | None = None
        self.pool_sha256: str | None = None
        self.phase_initial: dict[str, torch.Tensor] | None = None
        self.pre_step_heads: dict[str, torch.Tensor] = {}
        self.current_combination: Mapping[str, Any] | None = None
        self.record_count = 0
        self.first_phase_max_0_1_step: int | None = None
        self.first_phase_activity_step: int | None = None
        self.phase_signal_disappeared_after_alpha_one = False
        self.maximum_phase = -math.inf
        self.final_phase_max = math.nan
        self.final_phase_activity = math.nan
        self.started = time.perf_counter()

    def _possible_boundary_step(self, step: int) -> bool:
        candidates = {
            49, 50, 51, 99, 100, 101, 149, 150, 151,
            199, 200, 201, 224, 225, 226, 249, 250, 251,
            274, 275, 276, 299, 300, 301,
        }
        if self.controller.ramp_start is not None and self.controller.ramp_end is not None:
            candidates.update(
                {
                    self.controller.ramp_start - 1,
                    self.controller.ramp_start,
                    self.controller.ramp_start + 1,
                    self.controller.ramp_end - 1,
                    self.controller.ramp_end,
                    self.controller.ramp_end + 1,
                }
            )
        return step in candidates

    def _mechanism_due(self, step: int) -> bool:
        return step % 100 == 0 or self._possible_boundary_step(step)

    def _telemetry_due(self, step: int) -> bool:
        return step % 25 == 0 or self._possible_boundary_step(step)

    def observe(self, observation: TrainingObservation) -> None:
        if observation.phase == "PRE_RUN":
            device = next(observation.model.parameters()).device
            self.pool = build_readiness_pool(
                model=observation.model, dtype=torch.float64, device=device
            )
            self.pool_sha256 = _sha256_tensor(self.pool)
            self.phase_initial = {
                name: value.detach().clone()
                for name, value in observation.model.heads["phase"].state_dict().items()
            }
            return
        step = observation.optimizer_step
        if observation.phase == "PRE_BACKWARD":
            if self._mechanism_due(step):
                self.pre_step_heads = {
                    name: _head_vector(observation.model, name)
                    for name in ("potential", "temperature", "phase")
                }
            return
        if observation.phase == "POST_BACKWARD_PRE_CLIP":
            if self._mechanism_due(step):
                self.current_combination = observation.gradient_combination_diagnostics
            return
        if not self._telemetry_due(step):
            return
        assert self.pool is not None
        metadata = dict(observation.step_metadata or {})
        alpha = float(metadata["coupling_alpha"])
        metrics = _pool_metrics(observation.model, self.pool, coupling_alpha=alpha)
        if step in READINESS_STEPS and self.controller.ready_step is None:
            assert self.phase_initial is not None
            for name, initial in self.phase_initial.items():
                current = observation.model.heads["phase"].state_dict()[name]
                if not torch.equal(initial, current):
                    raise RuntimeError("R1X warm-up changed phase-head state")
            self.controller.record_readiness(step, metrics)
        phase_max = float(metrics["phase_max"])
        activity = float(metrics["phase_activity_fraction"])
        self.maximum_phase = max(self.maximum_phase, phase_max)
        if phase_max >= 0.10 and self.first_phase_max_0_1_step is None:
            self.first_phase_max_0_1_step = step
        if activity > 0.0 and self.first_phase_activity_step is None:
            self.first_phase_activity_step = step
        if alpha == 1.0 and self.maximum_phase >= 0.10 and phase_max < 0.10:
            self.phase_signal_disappeared_after_alpha_one = True
        head_updates = None
        combination = None
        if self._mechanism_due(step):
            head_updates = {
                name: _relative_update(before, _head_vector(observation.model, name))
                for name, before in self.pre_step_heads.items()
            }
            combination = dict(self.current_combination or {})
        record = {
            "schema_id": "phk-v23-r1x-telemetry-step-v1",
            "optimizer_step": step,
            "active_windows": observation.active_windows,
            "stage": metadata["stage"],
            "block_type": metadata["block_type"],
            "alpha": alpha,
            "active_heads": metadata["active_heads"],
            "active_loss_groups": metadata["active_loss_groups"],
            "pool_metrics": metrics,
            "readiness_pass": readiness_gate(metrics) if step in READINESS_STEPS else None,
            "head_relative_update": head_updates,
            "gradient_combination": combination,
            "training_scalars": dict(observation.scalars),
            "boundary_observables": self._boundary_observables(observation),
            "elapsed_seconds": time.perf_counter() - self.started,
            "reference_fields_read": False,
            "stress_fields_or_metrics_read": False,
        }
        if self.handle is None:
            self.handle = self.telemetry_path.open("x", encoding="utf-8", newline="\n")
        self.handle.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
        self.handle.flush()
        self.record_count += 1
        self.final_phase_max = phase_max
        self.final_phase_activity = activity

    def finalize(self, executed_updates: int) -> dict[str, Any]:
        if self.handle is not None:
            self.handle.close()
            self.handle = None
        return {
            "schema_id": "phk-v23-r1x-telemetry-summary-v1",
            "record_count": self.record_count,
            "executed_updates": int(executed_updates),
            "ready_step": self.controller.ready_step,
            "readiness_history": self.controller.readiness_history,
            "reference_blind_outcome": self.controller.reference_blind_outcome,
            "first_phase_max_0_1_step": self.first_phase_max_0_1_step,
            "first_phase_activity_step": self.first_phase_activity_step,
            "phase_signal_ever": self.maximum_phase >= 0.10 or self.first_phase_activity_step is not None,
            "phase_signal_disappeared_after_alpha_one": self.phase_signal_disappeared_after_alpha_one,
            "maximum_observed_phase": self.maximum_phase,
            "final_phase_max": self.final_phase_max,
            "final_phase_activity": self.final_phase_activity,
            "telemetry_path": self.telemetry_path.name,
            "telemetry_sha256": _sha256_path(self.telemetry_path),
            "readiness_pool_sha256": self.pool_sha256,
            "reference_fields_read": False,
            "stress_fields_or_metrics_read": False,
        }

    @staticmethod
    def _boundary_observables(observation: TrainingObservation) -> dict[str, float | None]:
        if observation.boundary is None:
            return {"potential_top_rms": None, "potential_heater_rms": None}
        model = observation.model
        top = observation.boundary["top"]
        bottom = observation.boundary["bottom"]
        with torch.no_grad():
            top_field = model(top)[:, 0:1]
            bottom_field = model(bottom)[:, 0:1]
        top_error = top_field - model.physics.waveform(top[:, 2:3])
        heater = bottom[:, 0].abs() <= model.physics.heater_half_width
        return {
            "potential_top_rms": _finite(torch.sqrt(torch.mean(top_error.square()))),
            "potential_heater_rms": (
                _finite(torch.sqrt(torch.mean(bottom_field[heater].square())))
                if bool(torch.any(heater))
                else None
            ),
        }


def _strong_raw_config(device: str, updates: int) -> PhkTrainingConfig:
    return PhkTrainingConfig(
        arm="STRONG_RAW",
        case_control="FULL",
        updates=updates,
        seed=17,
        hidden_width=64,
        hidden_layers=4,
        frequency_band="BAND_A",
        learning_rate=1.0e-3,
        gradient_clip_norm=10.0,
        interior_points=512,
        boundary_points=128,
        initial_points=128,
        candidate_pool_multiplier=4,
        refresh_updates=250,
        log_every=25,
        checkpoint_every=10_000,
        pde_weight=1.0,
        boundary_weight=5.0,
        initial_weight=1.0,
        dtype="float64",
        device=device,
    )


def _assert_deployed_source_identity(source_identity: str) -> None:
    manifest = _read_json(DEPLOYED_SOURCE_MANIFEST_PATH)
    if manifest.get("schema_id") != "phk-v23-r1x-deployed-source-manifest-v1":
        raise ValueError("unsupported R1X deployed-source manifest")
    if manifest.get("source_identity") != source_identity:
        raise ValueError("R1X deployed-source identity mismatch")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("R1X deployed-source manifest has no files")
    for relative, expected in files.items():
        exact = (ROOT / relative).resolve()
        try:
            exact.relative_to(ROOT.resolve())
        except ValueError as exc:
            raise PermissionError("R1X deployed-source path escaped project") from exc
        if not exact.is_file() or _sha256_path(exact) != expected:
            raise ValueError(f"R1X deployed-source drift: {relative}")


def run_reference_blind_trajectory(
    *,
    output_root: Path,
    device_name: str,
    source_identity: str,
    hourly_price_cny: float,
    variant_id: str,
    e3_extension: bool = False,
    role: str = "NON_VOTING_DEVELOPMENT_EXPLORATION",
) -> dict[str, Any]:
    load_r1x_contracts()
    _assert_deployed_source_identity(source_identity)
    if variant_id not in VARIANTS:
        raise ValueError("unknown R1X trajectory variant")
    variant = VARIANTS[variant_id]
    if e3_extension:
        variant = variant.with_e3_extension()
    if role not in {
        "NON_VOTING_DEVELOPMENT_EXPLORATION",
        "FROZEN_FROM_SCRATCH_CONFIRMATION",
    }:
        raise ValueError("unknown R1X trajectory role")
    output = Path(output_root).resolve()
    if output.exists():
        raise FileExistsError(f"R1X output already exists: {output}")
    if device_name != "cuda:0" or not torch.cuda.is_available():
        raise PermissionError("R1X requires authorized CUDA device cuda:0")
    device = torch.device(device_name)
    gpu_name = torch.cuda.get_device_name(device)
    if gpu_name != "Tesla V100-PCIE-32GB":
        raise PermissionError(f"R1X GPU identity mismatch: {gpu_name}")
    price = float(hourly_price_cny)
    if not math.isfinite(price) or price <= 0.0:
        raise ValueError("R1X hourly price must be positive and finite")
    config = _strong_raw_config(device_name, variant.total_updates)
    controller = CampaignController(variant)
    arm_directory = output / "strong_raw"
    observer = R1XTelemetryObserver(controller=controller, run_directory=arm_directory)
    combiner = ConFIGGradientCombiner(
        allowed_group_orders=(ET_GROUPS, PHASE_GROUPS, JOINT_GROUPS)
    )
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    outcome = train(
        config,
        run_directory=arm_directory,
        observer=observer,
        gradient_combiner=combiner,
        step_policy=controller,
        model_factory=_model_factory(variant),
        execution_metadata={
            "task_id": "PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE",
            "source_identity": source_identity,
            "contracts": _contract_identity(),
            "trajectory_role": role,
            "variant": variant.variant_id,
            "e3_extension": bool(e3_extension),
            "reference_blind": True,
            "stress_fields_read": False,
        },
    )
    telemetry = observer.finalize(outcome.executed_updates)
    prediction_path = arm_directory / "prediction.npz"
    write_prediction_carrier(
        checkpoint_path=outcome.checkpoint_path,
        output_path=prediction_path,
        device_name=device_name,
    )
    torch.cuda.synchronize(device)
    wall_seconds = time.perf_counter() - started
    environment = {
        "schema_id": "phk-v23-r1x-environment-v1",
        "gpu_name": gpu_name,
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "numpy_version": np.__version__,
        "python": os.sys.version,
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
        "reference_fields_present": False,
        "stress_fields_present": False,
    }
    _write_json_exclusive(output / "environment.json", environment)
    files = {
        "checkpoint": outcome.checkpoint_path,
        "training_log": arm_directory / "training-log.jsonl",
        "manifest_start": arm_directory / "manifest-start.json",
        "manifest_final": arm_directory / "manifest-final.json",
        "telemetry": observer.telemetry_path,
        "prediction": prediction_path,
        "environment": output / "environment.json",
    }
    summary = {
        "schema_id": "phk-v23-r1x-reference-blind-run-summary-v1",
        "task_id": "PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE",
        "status": "R1X_REFERENCE_BLIND_GPU_TRAJECTORY_COMPLETE",
        "trajectory_role": role,
        "variant": variant.variant_id,
        "e3_extension": bool(e3_extension),
        "started_at_utc": started_at,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_identity": source_identity,
        "contracts": _contract_identity(),
        "device": gpu_name,
        "dtype": "FLOAT64",
        "seed": 17,
        "arm": "STRONG_RAW",
        "optimizer_updates_planned": variant.total_updates,
        "optimizer_updates_executed": outcome.executed_updates,
        "single_adam_instance": True,
        "config_application_count": combiner.calls,
        "reference_blind_outcome": telemetry["reference_blind_outcome"],
        "ready_step": telemetry["ready_step"],
        "ramp_updates": 0 if telemetry["ready_step"] is None else variant.ramp_length,
        "full_physics_joint_updates": (
            0
            if telemetry["ready_step"] is None
            else max(0, outcome.executed_updates - int(telemetry["ready_step"]) - variant.ramp_length)
        ),
        "first_phase_max_0_1_step": telemetry["first_phase_max_0_1_step"],
        "first_phase_activity_step": telemetry["first_phase_activity_step"],
        "phase_signal_ever": telemetry["phase_signal_ever"],
        "phase_signal_disappeared_after_alpha_one": telemetry["phase_signal_disappeared_after_alpha_one"],
        "maximum_observed_phase": telemetry["maximum_observed_phase"],
        "final_phase_max": telemetry["final_phase_max"],
        "final_phase_activity": telemetry["final_phase_activity"],
        "wall_seconds_including_prediction": wall_seconds,
        "gpu_hours": wall_seconds / 3600.0,
        "hourly_price_cny": price,
        "estimated_incremental_cost_cny": wall_seconds / 3600.0 * price,
        "reference_fields_read": False,
        "stress_fields_or_metrics_read": False,
        "artifacts": {
            name: {
                "path": str(path.relative_to(output)).replace("\\", "/"),
                "sha256": _sha256_path(path),
                "size_bytes": path.stat().st_size,
            }
            for name, path in files.items()
        },
    }
    _write_json_exclusive(output / "summary.json", summary)
    return summary


def _has_cycle_event(evaluation: Mapping[str, Any]) -> bool:
    cycles = evaluation.get("hard_guards", {}).get("event_topology", {}).get("cycles", [])
    return any(cycle.get("event_time") is not None for cycle in cycles)


def select_local_outcome(
    *,
    variant: CampaignVariant,
    run_summary: Mapping[str, Any],
    evaluation: Mapping[str, Any],
) -> str:
    if evaluation.get("hard_guards", {}).get("passed") is True:
        prefix = "E1" if variant.variant_id == E1.variant_id else "E2"
        return f"{prefix}_COMPETENCE_SIGNAL_OBSERVED"
    if variant.variant_id == E1.variant_id:
        if run_summary.get("reference_blind_outcome") == "ET_NOT_READY":
            return "E1_ET_NOT_READY"
        material = (
            bool(run_summary.get("phase_signal_ever"))
            or float(run_summary.get("final_phase_max", 0.0)) >= 0.10
            or _has_cycle_event(evaluation)
        )
        return (
            "E1_PHASE_SIGNAL_INCOMPLETE_OR_COLLAPSED"
            if material
            else "E1_ET_READY_PHASE_NO_RESPONSE"
        )
    material = (
        bool(run_summary.get("phase_signal_ever"))
        or float(run_summary.get("final_phase_max", 0.0)) >= 0.10
        or _has_cycle_event(evaluation)
    )
    return "E2_MATERIAL_PHASE_SIGNAL_INCOMPLETE" if material else "PURE_SCRATCH_EXPLORATION_STOP"


def machine_action(outcome: str, *, explorations_completed: int) -> str:
    validate_campaign_counts(explorations=explorations_completed, confirmations=0)
    mapping = {
        "E1_ET_NOT_READY": "RUN_E2_TOP_DIRICHLET_HARD_LIFT",
        "E1_ET_READY_PHASE_NO_RESPONSE": "RUN_E2_PHASE_JACOBIAN_NORMALIZED_OUTPUT",
        "E1_PHASE_SIGNAL_INCOMPLETE_OR_COLLAPSED": "RUN_E2_SMOOTHER_COUPLING_RAMP",
        "E1_COMPETENCE_SIGNAL_OBSERVED": "RUN_FROZEN_CONFIRMATION",
        "E2_COMPETENCE_SIGNAL_OBSERVED": "RUN_FROZEN_CONFIRMATION",
    }
    if outcome == "E2_MATERIAL_PHASE_SIGNAL_INCOMPLETE":
        return "RUN_E3_FULL_JOINT_EXTENSION" if explorations_completed < 3 else "PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED"
    return mapping.get(outcome, "PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED")


def adjudicate_local_nominal(
    *, run_summary_path: Path, evaluation_path: Path, output_path: Path
) -> dict[str, Any]:
    summary = _read_json(run_summary_path)
    evaluation = _read_json(evaluation_path)
    if summary.get("status") != "R1X_REFERENCE_BLIND_GPU_TRAJECTORY_COMPLETE":
        raise ValueError("R1X run summary is not complete")
    if evaluation.get("status") != "EVALUATED_LOCAL_REFERENCE_ONLY":
        raise ValueError("R1X evaluation is not local nominal evidence")
    variant = VARIANTS[str(summary["variant"])]
    if summary.get("trajectory_role") == "FROZEN_FROM_SCRATCH_CONFIRMATION":
        outcome = (
            "R1C_RAW_COMPETENCE_CONFIRMED_DEVELOPMENT_ONLY"
            if evaluation.get("hard_guards", {}).get("passed") is True
            else "R1C_CONFIRMATION_NO_COMPETENCE"
        )
        claim_boundary = "FROZEN_SINGLE_SEED_NOMINAL_DEVELOPMENT_CONFIRMATION"
    else:
        outcome = select_local_outcome(
            variant=variant, run_summary=summary, evaluation=evaluation
        )
        claim_boundary = "NON_VOTING_NOMINAL_DEVELOPMENT_EXPLORATION"
    result = {
        "schema_id": "phk-v23-r1x-local-adjudication-v1",
        "status": outcome,
        "competence_signal": evaluation["hard_guards"]["passed"] is True,
        "hard_guard_failures": list(evaluation["hard_guards"]["failures"]),
        "event_topology": evaluation["hard_guards"]["event_topology"],
        "metrics": evaluation["metrics"],
        "run_summary_sha256": _sha256_path(run_summary_path),
        "evaluation_sha256": _sha256_path(evaluation_path),
        "claim_boundary": claim_boundary,
        "stress_unseal_authorized": False,
        "written_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json_exclusive(output_path, result)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--output-root", type=Path, required=True)
    run.add_argument("--device", required=True)
    run.add_argument("--source-identity", required=True)
    run.add_argument("--hourly-price-cny", type=float, required=True)
    run.add_argument("--variant", choices=sorted(VARIANTS), required=True)
    run.add_argument("--e3-extension", action="store_true")
    run.add_argument(
        "--role",
        choices=("NON_VOTING_DEVELOPMENT_EXPLORATION", "FROZEN_FROM_SCRATCH_CONFIRMATION"),
        default="NON_VOTING_DEVELOPMENT_EXPLORATION",
    )
    decide = commands.add_parser("adjudicate")
    decide.add_argument("--run-summary", type=Path, required=True)
    decide.add_argument("--evaluation", type=Path, required=True)
    decide.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "run":
        result = run_reference_blind_trajectory(
            output_root=args.output_root,
            device_name=args.device,
            source_identity=args.source_identity,
            hourly_price_cny=args.hourly_price_cny,
            variant_id=args.variant,
            e3_extension=args.e3_extension,
            role=args.role,
        )
    else:
        result = adjudicate_local_nominal(
            run_summary_path=args.run_summary,
            evaluation_path=args.evaluation,
            output_path=args.output,
        )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CampaignController",
    "CampaignVariant",
    "E1",
    "E2_PHASE_NORMALIZED",
    "E2_SMOOTHER_RAMP",
    "E2_TOP_HARD_LIFT",
    "accelerated_active_windows",
    "adjudicate_local_nominal",
    "build_campaign_model",
    "build_readiness_pool",
    "load_r1x_contracts",
    "machine_action",
    "main",
    "readiness_gate",
    "run_reference_blind_trajectory",
    "select_local_outcome",
    "smoothstep_alpha",
    "validate_campaign_counts",
]
