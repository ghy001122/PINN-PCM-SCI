"""PHK-V2.3 R0B minimal first-switch replay and local adjudication."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import random
import subprocess
import time
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .phk_v22r_pinn import PhkCollocationSampler, PhkV22RArm, PhkV22RModel
from .phk_v22r_prediction import write_prediction_carrier
from .phk_v22r_training import (
    PhkTrainingConfig,
    TrainingObservation,
    load_case_physics,
    train,
)
from .phk_v23_diagnostics import (
    gradient_matrix_preserving_state,
    state_identity,
    summarize_model_mapping,
    write_json_exclusive_atomic,
)


ROOT = Path(__file__).resolve().parents[1]
PROGRAM_CONTRACT_PATH = (
    ROOT / "configs" / "phk_v23" / "program_contract_r0b_minimal_v2.json"
)
METHOD_CONTRACT_PATH = (
    ROOT / "configs" / "phk_v23" / "method_contract_r0b_minimal_v2.json"
)
DIAGNOSTIC_CONTRACT_PATH = (
    ROOT / "configs" / "phk_v23" / "r0b_diagnostic_contract_minimal_v2.json"
)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected one JSON object: {path}")
    return payload


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _tensor_sha256(tensor: torch.Tensor) -> str:
    raw = tensor.detach().to(device="cpu").contiguous().numpy().tobytes(order="C")
    return hashlib.sha256(raw).hexdigest().upper()


def _finite(value: Any) -> float:
    result = float(value.detach().cpu()) if isinstance(value, torch.Tensor) else float(value)
    if not math.isfinite(result):
        raise FloatingPointError("R0B produced a non-finite scalar")
    return result


def load_r0b_contracts() -> dict[str, dict[str, Any]]:
    program = _read_json(PROGRAM_CONTRACT_PATH)
    method = _read_json(METHOD_CONTRACT_PATH)
    diagnostic = _read_json(DIAGNOSTIC_CONTRACT_PATH)
    if program.get("schema_id") != "phk-v23-program-contract-r0b-minimal-v2":
        raise ValueError("unsupported R0B program contract")
    if method.get("schema_id") != "phk-v23-method-contract-r0b-minimal-v2":
        raise ValueError("unsupported R0B method contract")
    if diagnostic.get("schema_id") != "phk-v23-r0b-diagnostic-contract-minimal-v2":
        raise ValueError("unsupported R0B diagnostic contract")
    authorization = program["authorization"]
    for name in (
        "contract_and_implementation_writes_authorized",
        "selective_commit_and_push_authorized",
        "r0b_reference_blind_gpu_replay_authorized",
        "local_reference_blind_adjudication_authorized",
        "conditional_local_cpu_gradient_factorial_authorized",
        "local_nominal_non_voting_appendix_authorized",
        "instance_shutdown_after_recovery_required",
    ):
        if authorization.get(name) is not True:
            raise PermissionError(f"R0B authorization missing: {name}")
    for name in (
        "r1_or_recovery_intervention_authorized",
        "pjgr_or_other_method_authorized",
        "stress_reference_access_authorized",
        "second_gpu_run_or_seed_change_authorized",
        "submission_or_external_contact_authorized",
    ):
        if authorization.get(name) is not False:
            raise PermissionError(f"R0B out-of-scope authorization detected: {name}")
    identity = method["execution_identity"]
    if identity["scientific_schedule_denominator"] != 1000:
        raise ValueError("R0B scientific schedule denominator drift")
    if identity["canonical_optimizer_steps"] != 175:
        raise ValueError("R0B canonical step count drift")
    if diagnostic["reference_boundary"]["cloud_reference_fields_read"] is not False:
        raise PermissionError("R0B cloud reference boundary is not fail-closed")
    if diagnostic["reference_boundary"]["stress_reference_fields_or_metrics_may_be_read"] is not False:
        raise PermissionError("R0B stress boundary is not fail-closed")
    return {"program": program, "method": method, "diagnostic": diagnostic}


def _contract_identity() -> dict[str, dict[str, str]]:
    return {
        "program": {
            "path": str(PROGRAM_CONTRACT_PATH.relative_to(ROOT)).replace("\\", "/"),
            "sha256": _sha256_path(PROGRAM_CONTRACT_PATH),
        },
        "method": {
            "path": str(METHOD_CONTRACT_PATH.relative_to(ROOT)).replace("\\", "/"),
            "sha256": _sha256_path(METHOD_CONTRACT_PATH),
        },
        "diagnostic": {
            "path": str(DIAGNOSTIC_CONTRACT_PATH.relative_to(ROOT)).replace("\\", "/"),
            "sha256": _sha256_path(DIAGNOSTIC_CONTRACT_PATH),
        },
    }


def _numpy_rng_equal(first: tuple[Any, ...], second: tuple[Any, ...]) -> bool:
    return (
        first[0] == second[0]
        and np.array_equal(first[1], second[1])
        and first[2:] == second[2:]
    )


def _grad_snapshot(model: PhkV22RModel) -> list[torch.Tensor | None]:
    return [
        None if parameter.grad is None else parameter.grad.detach().clone()
        for parameter in model.parameters()
    ]


def _assert_grads_equal(
    model: PhkV22RModel, before: Sequence[torch.Tensor | None]
) -> None:
    for parameter, expected in zip(model.parameters(), before, strict=True):
        if expected is None:
            if parameter.grad is not None:
                raise RuntimeError("R0B observer created a persistent gradient")
        elif parameter.grad is None or not torch.equal(parameter.grad, expected):
            raise RuntimeError("R0B observer changed an existing gradient")


def _cpu_batches(
    batches: Mapping[str, torch.Tensor] | None,
) -> dict[str, torch.Tensor] | None:
    if batches is None:
        return None
    return {
        name: value.detach().to(device="cpu").clone() for name, value in batches.items()
    }


class R0BObserver:
    """Deep read-only observer behind the single training-observer interface."""

    def __init__(
        self,
        *,
        run_directory: Path,
        contracts: Mapping[str, Mapping[str, Any]],
        source_identity: str,
        soft_stop_seconds: float,
    ) -> None:
        self.run_directory = Path(run_directory)
        self.contracts = contracts
        self.source_identity = str(source_identity)
        self.soft_stop_seconds = float(soft_stop_seconds)
        observer = contracts["method"]["observer"]
        self.cheap_steps = frozenset(int(item) for item in observer["cheap_post_step_observations"])
        self.full_steps = frozenset(int(item) for item in observer["full_gradient_observations"])
        self.loss_rows = tuple(
            contracts["method"]["loss_head_gradient_matrix"]["loss_rows"]
        )
        self.started = time.perf_counter()
        self.telemetry_path = self.run_directory / "r0b-telemetry.jsonl"
        self.transition_path = self.run_directory / "transition-151-diagnostic-bundle.pt"
        self.handle = None
        self.pool: torch.Tensor | None = None
        self.w1: torch.Tensor | None = None
        self.w2: torch.Tensor | None = None
        self.gradient_w1: torch.Tensor | None = None
        self.boundary_w1: dict[str, torch.Tensor] | None = None
        self.boundary_w2: dict[str, torch.Tensor] | None = None
        self.initial: torch.Tensor | None = None
        self.pool_identity: dict[str, Any] = {}
        self.raw_states: dict[int, dict[str, torch.Tensor]] = {}
        self.previous_phase_parameters: torch.Tensor | None = None
        self.previous_observation_step: int | None = None
        self.old_transition_batches: dict[str, Any] | None = None
        self.observer_elapsed_seconds = 0.0
        self.record_count = 0

    def _open(self) -> None:
        if self.handle is None:
            self.handle = self.telemetry_path.open("x", encoding="utf-8", newline="\n")

    def _append(self, record: Mapping[str, Any]) -> None:
        self._open()
        assert self.handle is not None
        self.handle.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
        self.handle.flush()
        self.record_count += 1

    def _build_pools(self, model: PhkV22RModel) -> None:
        contract = self.contracts["method"]["diagnostic_pool"]
        device = next(model.parameters()).device
        dtype = next(model.parameters()).dtype
        sampler = PhkCollocationSampler(
            physics=model.physics,
            seed=int(contract["seed"]),
        )
        pool = sampler.interior_uniform(
            int(contract["scalar_points_total"]),
            active_windows=2,
            dtype=dtype,
            device=device,
        ).detach()
        per_window = int(contract["scalar_points_per_window"])
        self.pool = pool
        self.w1 = pool[:per_window]
        self.w2 = pool[per_window : 2 * per_window]
        self.gradient_w1 = self.w1[: int(contract["gradient_points_w1"])]
        boundary = sampler.boundary(
            2 * int(contract["boundary_points_per_side_w1"]),
            active_windows=2,
            dtype=dtype,
            device=device,
        )
        self.boundary_w1 = {
            side: coordinates[coordinates[:, 2] < 0.35].detach()
            for side, coordinates in boundary.items()
        }
        self.boundary_w2 = {
            side: coordinates[coordinates[:, 2] >= 0.35].detach()
            for side, coordinates in boundary.items()
        }
        self.initial = sampler.initial(
            int(contract["initial_points"]), dtype=dtype, device=device
        ).detach()
        self.pool_identity = {
            "seed": int(contract["seed"]),
            "pool_sha256": _tensor_sha256(pool),
            "w1_sha256": _tensor_sha256(self.w1),
            "w2_sha256": _tensor_sha256(self.w2),
            "gradient_w1_sha256": _tensor_sha256(self.gradient_w1),
            "initial_sha256": _tensor_sha256(self.initial),
            "scalar_points_total": int(pool.shape[0]),
            "scalar_points_per_window": per_window,
            "gradient_points_w1": int(self.gradient_w1.shape[0]),
            "boundary_points_per_side_w1": {
                side: int(value.shape[0]) for side, value in self.boundary_w1.items()
            },
        }

    @staticmethod
    def _q95(summary: Mapping[str, Any]) -> float:
        return float(summary["quantiles"]["q95"])

    def _fixed_metrics(self, model: PhkV22RModel, step: int) -> dict[str, Any]:
        assert self.pool is not None
        assert self.w1 is not None
        assert self.boundary_w1 is not None
        fields, phase, electro, _ = summarize_model_mapping(
            model,
            self.pool,
            self.boundary_w1,
            self.contracts,
        )
        w1_field = fields["per_window"][0]
        w2_field = fields["per_window"][1]
        w1_phase = phase["per_window"][0]
        w2_phase = phase["per_window"][1]
        w1_electro = electro["per_window"][0]
        w2_electro = electro["per_window"][1]
        j_global = self._q95(w1_electro["joule_density"])
        j_roi_summary = w1_electro["joule_density_roi"]
        j_roi = self._q95(j_roi_summary) if j_roi_summary else 0.0
        boundary = fields["potential_boundary_saturation"]
        top_error = boundary["top"].get("dirichlet_sigmoid_error")
        bottom_error = boundary["bottom"].get("dirichlet_sigmoid_error")
        output = model.read_only_output_diagnostics(self.w1)
        jacobian = output.analytic_output_jacobians["phase"].detach()
        raw = {
            "phase": output.output.fields[:, 2:3].detach().to(device="cpu"),
            "latent": output.latents["phase"].detach().to(device="cpu"),
            "jacobian": jacobian.to(device="cpu"),
        }
        if step in {0, 1, 10}:
            self.raw_states[step] = {name: value.clone() for name, value in raw.items()}
        phase_parameters = torch.cat(
            [
                parameter.detach().reshape(-1).to(device="cpu")
                for parameter in model.heads["phase"].parameters()
            ]
        )
        update_relative = None
        if self.previous_phase_parameters is not None:
            update_relative = _finite(
                torch.linalg.vector_norm(phase_parameters - self.previous_phase_parameters)
                / torch.clamp(
                    torch.linalg.vector_norm(self.previous_phase_parameters), min=1.0e-300
                )
            )
        self.previous_phase_parameters = phase_parameters.clone()
        self.previous_observation_step = step
        metrics: dict[str, Any] = {
            "phase_max_w1": float(w1_field["fields"]["phase"]["max"]),
            "phase_q95_w1": self._q95(w1_field["fields"]["phase"]),
            "phase_max_w2": float(w2_field["fields"]["phase"]["max"]),
            "phase_activity_fraction_w1": float(w1_field["phase_activity_fraction"]),
            "temperature_max_w1": float(w1_field["fields"]["temperature"]["max"]),
            "temperature_max_w2": float(w2_field["fields"]["temperature"]["max"]),
            "temperature_above_transition_fraction_w1": float(
                w1_electro["temperature_above_transition_fraction"]
            ),
            "phase_jacobian_q95_w1": self._q95(
                w1_field["analytic_output_jacobians"]["phase"]
            ),
            "phase_jacobian_below_floor_fraction_w1": _finite(
                torch.mean((jacobian < 0.01).to(torch.float64))
            ),
            "positive_growth_roi_fraction_w1": w1_phase["positive_growth_roi_fraction"],
            "positive_growth_roi_fraction_w2": w2_phase["positive_growth_roi_fraction"],
            "joule_q95_w1": j_global,
            "joule_roi_q95_w1": j_roi,
            "joule_localization_ratio_w1": (
                j_roi / j_global if abs(j_global) > 1.0e-18 else None
            ),
            "electric_residual_rms_w1": float(
                w1_electro["electric_terms"]["electric_residual"]["rms"]
            ),
            "thermal_residual_rms_w1": float(
                w1_electro["thermal_terms"]["thermal_residual"]["rms"]
            ),
            "phase_residual_rms_w1": float(
                w1_phase["terms"]["phase_residual"]["rms"]
            ),
            "potential_top_sigmoid_error_rms_w1": (
                float(top_error["rms"]) if top_error else None
            ),
            "potential_bottom_sigmoid_error_rms_w1": (
                float(bottom_error["rms"]) if bottom_error else None
            ),
            "phase_parameter_update_relative_l2_since_previous_observation": update_relative,
            "w2_active_pulse_boundary_and_joule_vote": None,
            "w2_not_applicable_reason": "NOT_APPLICABLE_ZERO_DRIVE",
        }
        if step == 10 and {0, 1, 10}.issubset(self.raw_states):
            epsilon = float(
                self.contracts["diagnostic"]["decision"]["thresholds"]["epsilon"]
            )

            def capacity(first: int, second: int) -> float:
                start = self.raw_states[first]
                end = self.raw_states[second]
                rate = torch.abs(end["latent"] - start["latent"]) / float(second - first)
                numerator = torch.quantile(torch.abs(start["jacobian"]) * rate, 0.95)
                denominator = max(
                    0.5 - _finite(torch.quantile(start["phase"], 0.95)), epsilon
                )
                return _finite(numerator) / denominator

            metrics["phase_output_capacity_0_1"] = capacity(0, 1)
            metrics["phase_output_capacity_1_10"] = capacity(1, 10)
        del output
        return metrics

    def _full_gradient(
        self,
        model: PhkV22RModel,
        *,
        interior: torch.Tensor,
        boundary: Mapping[str, torch.Tensor],
        initial: torch.Tensor,
    ) -> dict[str, Any]:
        return gradient_matrix_preserving_state(
            model,
            interior,
            boundary,
            self.contracts,
            initial=initial,
            loss_rows=self.loss_rows,
        )

    def _record_post_step(
        self, observation: TrainingObservation, *, step: int
    ) -> None:
        assert self.gradient_w1 is not None
        assert self.boundary_w1 is not None
        assert self.initial is not None
        record: dict[str, Any] = {
            "phase": "POST_STEP_FIXED_POOL",
            "optimizer_step": step,
            "active_windows": observation.active_windows,
            "collocation_refreshed": observation.collocation_refreshed,
            "training_scalars": dict(observation.scalars),
            "metrics": self._fixed_metrics(observation.model, step),
            "full_gradient": None,
        }
        if step in self.full_steps:
            record["full_gradient"] = self._full_gradient(
                observation.model,
                interior=self.gradient_w1,
                boundary=self.boundary_w1,
                initial=self.initial,
            )
        self._append(record)

    def _save_transition_bundle(self, observation: TrainingObservation) -> None:
        if self.old_transition_batches is None:
            raise RuntimeError("step-151 new batch arrived without the old batch snapshot")
        if observation.interior is None or observation.boundary is None or observation.initial is None:
            raise RuntimeError("step-151 transition batch is incomplete")
        payload = {
            "schema_id": "phk-v23-r0b-transition-151-gradient-bundle-v1",
            "checkpoint_selectable": False,
            "optimizer_state_included": False,
            "source_identity": self.source_identity,
            "contracts": _contract_identity(),
            "optimizer_step": 151,
            "model_state_dict_theta_150": {
                name: tensor.detach().to(device="cpu").clone()
                for name, tensor in observation.model.state_dict().items()
            },
            "old": self.old_transition_batches,
            "new": {
                "interior": observation.interior.detach().to(device="cpu").clone(),
                "boundary": _cpu_batches(observation.boundary),
                "initial": observation.initial.detach().to(device="cpu").clone(),
            },
        }
        with self.transition_path.open("xb") as handle:
            torch.save(payload, handle)

    def _observe_impl(self, observation: TrainingObservation) -> None:
        if time.perf_counter() - self.started > self.soft_stop_seconds:
            raise TimeoutError("R0B paid-work soft stop reached inside observer")
        if observation.phase == "PRE_RUN":
            self._build_pools(observation.model)
            self._append(
                {
                    "phase": "PRE_RUN",
                    "optimizer_step": 0,
                    "pool_identity": self.pool_identity,
                    "contracts": _contract_identity(),
                    "source_identity": self.source_identity,
                }
            )
            self._record_post_step(observation, step=0)
            return
        if observation.phase == "PRE_REFRESH" and observation.optimizer_step == 151:
            if observation.interior is None or observation.boundary is None or observation.initial is None:
                raise RuntimeError("old transition batch is incomplete")
            self.old_transition_batches = {
                "interior": observation.interior.detach().to(device="cpu").clone(),
                "boundary": _cpu_batches(observation.boundary),
                "initial": observation.initial.detach().to(device="cpu").clone(),
            }
            self._append(
                {
                    "phase": "PRE_151_BEFORE_REFRESH",
                    "optimizer_step": 151,
                    "old_interior_sha256": _tensor_sha256(observation.interior),
                    "old_boundary_sha256": {
                        name: _tensor_sha256(value)
                        for name, value in observation.boundary.items()
                    },
                    "old_initial_sha256": _tensor_sha256(observation.initial),
                }
            )
            return
        if observation.phase == "PRE_BACKWARD" and observation.optimizer_step == 151:
            assert observation.interior is not None
            assert observation.boundary is not None
            assert observation.initial is not None
            actual_gradient = self._full_gradient(
                observation.model,
                interior=observation.interior,
                boundary=observation.boundary,
                initial=observation.initial,
            )
            self._append(
                {
                    "phase": "PRE_151_AFTER_REFRESH_BEFORE_BACKWARD",
                    "optimizer_step": 151,
                    "active_windows": observation.active_windows,
                    "collocation_refreshed": observation.collocation_refreshed,
                    "new_interior_sha256": _tensor_sha256(observation.interior),
                    "new_boundary_sha256": {
                        name: _tensor_sha256(value)
                        for name, value in observation.boundary.items()
                    },
                    "new_initial_sha256": _tensor_sha256(observation.initial),
                    "actual_batch_gradient": actual_gradient,
                }
            )
            self._save_transition_bundle(observation)
            return
        if observation.phase == "POST_STEP" and observation.optimizer_step in self.cheap_steps:
            self._record_post_step(observation, step=observation.optimizer_step)

    def observe(self, observation: TrainingObservation) -> None:
        if observation.phase == "PRE_BACKWARD" and observation.optimizer_step != 151:
            return
        if observation.phase == "PRE_REFRESH" and observation.optimizer_step != 151:
            return
        if observation.phase == "POST_STEP" and observation.optimizer_step not in self.cheap_steps:
            return
        model = observation.model
        device = next(model.parameters()).device
        before_identity = state_identity(model)
        before_grads = _grad_snapshot(model)
        before_mode = model.training
        before_python = random.getstate()
        before_numpy = np.random.get_state()
        before_cpu_rng = torch.random.get_rng_state().clone()
        before_cuda_rng = (
            torch.cuda.get_rng_state(device).clone() if device.type == "cuda" else None
        )
        started = time.perf_counter()
        try:
            self._observe_impl(observation)
        except BaseException:
            if self.handle is not None:
                self.handle.close()
                self.handle = None
            raise
        if state_identity(model) != before_identity:
            raise RuntimeError("R0B observer changed model parameters or buffers")
        _assert_grads_equal(model, before_grads)
        if model.training != before_mode:
            raise RuntimeError("R0B observer changed model mode")
        if random.getstate() != before_python:
            raise RuntimeError("R0B observer changed Python RNG state")
        if not _numpy_rng_equal(np.random.get_state(), before_numpy):
            raise RuntimeError("R0B observer changed NumPy RNG state")
        if not torch.equal(torch.random.get_rng_state(), before_cpu_rng):
            raise RuntimeError("R0B observer changed Torch CPU RNG state")
        if before_cuda_rng is not None and not torch.equal(
            torch.cuda.get_rng_state(device), before_cuda_rng
        ):
            raise RuntimeError("R0B observer changed Torch CUDA RNG state")
        self.observer_elapsed_seconds += time.perf_counter() - started

    def finalize(self) -> dict[str, Any]:
        if self.handle is not None:
            self.handle.close()
            self.handle = None
        if not self.telemetry_path.exists():
            raise RuntimeError("R0B observer emitted no telemetry")
        summary = {
            "schema_id": "phk-v23-r0b-telemetry-summary-v1",
            "status": "REFERENCE_BLIND_TELEMETRY_COMPLETE",
            "record_count": self.record_count,
            "telemetry_path": self.telemetry_path.name,
            "telemetry_sha256": _sha256_path(self.telemetry_path),
            "transition_bundle_path": (
                self.transition_path.name if self.transition_path.exists() else None
            ),
            "transition_bundle_sha256": (
                _sha256_path(self.transition_path) if self.transition_path.exists() else None
            ),
            "observer_elapsed_seconds": self.observer_elapsed_seconds,
            "pool_identity": self.pool_identity,
            "reference_fields_read": False,
            "stress_fields_or_metrics_read": False,
            "cloud_shadow_optimizer_steps": 0,
            "observer_invariants": {
                "model_state_unchanged_per_callback": True,
                "existing_grad_state_preserved_per_callback": True,
                "python_numpy_torch_cpu_cuda_rng_preserved_per_callback": True,
                "model_mode_preserved_per_callback": True,
            },
        }
        write_json_exclusive_atomic(
            self.run_directory / "r0b-telemetry-summary.json", summary
        )
        return summary


def _git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def _strong_raw_config(device: str) -> PhkTrainingConfig:
    return PhkTrainingConfig(
        arm=PhkV22RArm.STRONG_RAW.value,
        case_control="FULL",
        updates=1000,
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
        checkpoint_every=1000,
        pde_weight=1.0,
        boundary_weight=5.0,
        initial_weight=1.0,
        dtype="float64",
        device=device,
    )


def _assert_method_identity(config: PhkTrainingConfig, contracts: Mapping[str, Mapping[str, Any]]) -> None:
    expected = contracts["method"]["legacy_identity"]
    observed = {
        "arm": config.arm,
        "case_control": config.case_control,
        "initialization": "SCRATCH_START",
        "seed": config.seed,
        "dtype": "FLOAT64",
        "hidden_width": config.hidden_width,
        "hidden_layers": config.hidden_layers,
        "frequency_band": config.frequency_band,
        "learning_rate": config.learning_rate,
        "gradient_clip_norm": config.gradient_clip_norm,
        "interior_points": config.interior_points,
        "boundary_points": config.boundary_points,
        "initial_points": config.initial_points,
        "candidate_pool_multiplier": config.candidate_pool_multiplier,
        "refresh_updates": config.refresh_updates,
        "checkpoint_every": config.checkpoint_every,
        "loss_weights": {
            "pde": config.pde_weight,
            "boundary": config.boundary_weight,
            "initial": config.initial_weight,
        },
    }
    for name, value in observed.items():
        if expected.get(name) != value:
            raise ValueError(f"R0B strong-raw identity drift: {name}")
    for path_name, hash_name in (
        ("v22r_program_contract", "v22r_program_contract_sha256"),
        ("v22r_method_contract", "v22r_method_contract_sha256"),
    ):
        if _sha256_path(ROOT / expected[path_name]) != expected[hash_name]:
            raise ValueError(f"R0B inherited contract drift: {path_name}")


def run_reference_blind_gpu_replay(
    *,
    output_root: Path,
    device_name: str,
    source_identity: str,
    hourly_price_cny: float,
) -> dict[str, Any]:
    contracts = load_r0b_contracts()
    if _git_head() != source_identity:
        raise ValueError("R0B source identity differs from Git HEAD")
    output = Path(output_root).resolve()
    if output.exists():
        raise FileExistsError(f"R0B output already exists: {output}")
    if device_name != "cuda:0" or not torch.cuda.is_available():
        raise PermissionError("R0B requires the authorized CUDA device cuda:0")
    gpu_name = torch.cuda.get_device_name(torch.device(device_name))
    if gpu_name != "Tesla V100-PCIE-32GB":
        raise PermissionError(f"R0B GPU identity mismatch: {gpu_name}")
    budget = contracts["program"]["execution_budget"]
    price = float(hourly_price_cny)
    if not math.isfinite(price) or price <= 0.0:
        raise ValueError("R0B hourly price must be positive and finite")
    projected_hours = 0.35
    if projected_hours > float(budget["gpu_wall_hours_hard_cap"]):
        raise TimeoutError("R0B projected GPU time exceeds the hard cap")
    if projected_hours * price > float(budget["estimated_incremental_cost_cny_hard_cap"]):
        raise TimeoutError("R0B projected cloud cost exceeds the hard cap")
    config = _strong_raw_config(device_name)
    _assert_method_identity(config, contracts)
    arm_directory = output / "strong_raw"
    observer = R0BObserver(
        run_directory=arm_directory,
        contracts=contracts,
        source_identity=source_identity,
        soft_stop_seconds=60.0 * float(budget["gpu_paid_work_soft_stop_minutes"]),
    )
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    outcome = train(
        config,
        run_directory=arm_directory,
        execution_limit=175,
        observer=observer,
        execution_metadata={
            "task_id": "PHK_V23_R0B_FIRST_SWITCH_175_MINIMAL_V2",
            "source_identity": source_identity,
            "contracts": _contract_identity(),
            "reference_blind": True,
            "stress_fields_read": False,
            "cloud_shadow_optimizer_steps": 0,
        },
    )
    telemetry = observer.finalize()
    if outcome.status != "DIAGNOSTIC_PREFIX":
        raise RuntimeError(f"unexpected R0B training status: {outcome.status}")
    prediction_path = arm_directory / "prediction-extra-fine-axes.npz"
    write_prediction_carrier(
        checkpoint_path=outcome.checkpoint_path,
        output_path=prediction_path,
        device_name=device_name,
    )
    torch.cuda.synchronize(torch.device(device_name))
    wall_seconds = time.perf_counter() - started
    hard_seconds = 3600.0 * float(budget["gpu_wall_hours_hard_cap"])
    if wall_seconds > hard_seconds:
        raise TimeoutError("R0B GPU wall-time hard cap exceeded")
    estimated_cost = wall_seconds / 3600.0 * price
    if estimated_cost > float(budget["estimated_incremental_cost_cny_hard_cap"]):
        raise TimeoutError("R0B estimated incremental cost hard cap exceeded")
    environment = {
        "schema_id": "phk-v23-r0b-environment-v1",
        "gpu_name": gpu_name,
        "cuda_device_count": torch.cuda.device_count(),
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "numpy_version": np.__version__,
        "python": os.sys.version,
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
        "reference_fields_present": False,
    }
    write_json_exclusive_atomic(output / "environment.json", environment)
    files = {
        "checkpoint": outcome.checkpoint_path,
        "prediction": prediction_path,
        "training_log": arm_directory / "training-log.jsonl",
        "manifest_start": arm_directory / "manifest-start.json",
        "manifest_final": arm_directory / "manifest-final.json",
        "telemetry": arm_directory / "r0b-telemetry.jsonl",
        "telemetry_summary": arm_directory / "r0b-telemetry-summary.json",
        "transition_bundle": arm_directory / "transition-151-diagnostic-bundle.pt",
        "environment": output / "environment.json",
    }
    summary = {
        "schema_id": "phk-v23-r0b-reference-blind-run-summary-v1",
        "task_id": "PHK_V23_R0B_FIRST_SWITCH_175_MINIMAL_V2",
        "status": "R0B_REFERENCE_BLIND_GPU_REPLAY_COMPLETE",
        "started_at_utc": started_at,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_identity": source_identity,
        "contracts": _contract_identity(),
        "device": gpu_name,
        "dtype": "FLOAT64",
        "seed": 17,
        "arm": "STRONG_RAW",
        "initialization": "SCRATCH_START",
        "scientific_schedule_denominator": 1000,
        "canonical_optimizer_steps": 175,
        "cloud_shadow_optimizer_steps": 0,
        "wall_seconds": wall_seconds,
        "hourly_price_cny": price,
        "estimated_incremental_cost_cny": estimated_cost,
        "reference_fields_read": False,
        "stress_fields_or_metrics_read": False,
        "telemetry_record_count": telemetry["record_count"],
        "artifacts": {
            name: {
                "path": str(path.relative_to(output)).replace("\\", "/"),
                "sha256": _sha256_path(path),
                "size_bytes": path.stat().st_size,
            }
            for name, path in files.items()
        },
    }
    write_json_exclusive_atomic(output / "summary.json", summary)
    return summary


def read_telemetry(path: Path) -> list[dict[str, Any]]:
    records = [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not records:
        raise ValueError("R0B telemetry is empty")
    return records


def _post_records(records: Sequence[Mapping[str, Any]]) -> dict[int, Mapping[str, Any]]:
    result = {
        int(record["optimizer_step"]): record
        for record in records
        if record.get("phase") == "POST_STEP_FIXED_POOL"
    }
    required = {0, 1, 10, 25, 100, 149, 150, 151, 160, 175}
    if not required.issubset(result):
        raise ValueError(f"R0B telemetry lacks required observations: {sorted(required - set(result))}")
    return result


def _first_persistent(
    records: Mapping[int, Mapping[str, Any]],
    steps: Sequence[int],
    predicate,
    minimum_gap: int,
) -> tuple[int, int] | None:
    ordered = [int(step) for step in steps if int(step) in records]
    for first_index, onset in enumerate(ordered):
        if not predicate(records[onset]):
            continue
        for confirmation in ordered[first_index + 1 :]:
            if confirmation - onset < minimum_gap:
                continue
            between = [step for step in ordered[first_index : ordered.index(confirmation) + 1]]
            if all(predicate(records[step]) for step in between):
                return onset, confirmation
            break
    return None


def _material_conflict(record: Mapping[str, Any], threshold: float, floor: float) -> bool:
    gradient = record.get("full_gradient")
    if not gradient:
        return False
    total = float(gradient["gradient_norms"]["TOTAL_OBJECTIVE"]["phase"])
    if total <= 0.0:
        return False
    norms = gradient["gradient_norms"]
    for key, item in gradient["same_head_pairwise_cosines"]["phase"].items():
        cosine = item["cosine"]
        if cosine is None or float(cosine) > threshold:
            continue
        first, second = key.split("__", 1)
        if first in {"INITIAL", "TOTAL_OBJECTIVE"} or second in {"INITIAL", "TOTAL_OBJECTIVE"}:
            continue
        if float(norms[first]["phase"]) >= floor * total and float(norms[second]["phase"]) >= floor * total:
            return True
    return False


def adjudicate_reference_blind(
    records: Sequence[Mapping[str, Any]],
    contracts: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    post = _post_records(records)
    decision = contracts["diagnostic"]["decision"]
    threshold = decision["thresholds"]
    persistence = int(threshold["minimum_persistence_optimizer_steps"])
    cheap_steps = contracts["method"]["observer"]["cheap_post_step_observations"]
    full_steps = contracts["method"]["observer"]["full_gradient_observations"]
    candidates: list[dict[str, Any]] = []

    def add(name: str, timing: tuple[int, int] | None, basis: str) -> None:
        if timing is not None:
            candidates.append(
                {
                    "candidate": name,
                    "onset_step": timing[0],
                    "confirmation_step": timing[1],
                    "basis": basis,
                }
            )

    boundary_floor = float(threshold["boundary_sigmoid_error_rms"])
    add(
        "ELECTRICAL_OR_BOUNDARY_CONDITIONING",
        _first_persistent(
            post,
            [step for step in cheap_steps if step >= 25],
            lambda record: max(
                float(record["metrics"]["potential_top_sigmoid_error_rms_w1"] or 0.0),
                float(record["metrics"]["potential_bottom_sigmoid_error_rms_w1"] or 0.0),
            )
            >= boundary_floor,
            persistence,
        ),
        "W1_ACTIVE_PULSE_BOUNDARY_SIGMOID_ERROR",
    )
    temperature_floor = float(threshold["temperature_fraction_of_transition_floor"]) * 0.45
    positive_floor = float(threshold["low_positive_drive_fraction"])
    add(
        "ELECTROTHERMAL_DRIVE_DEFICIT",
        _first_persistent(
            post,
            [step for step in cheap_steps if step >= 100],
            lambda record: float(record["metrics"]["temperature_max_w1"]) <= temperature_floor
            and float(record["metrics"]["positive_growth_roi_fraction_w1"] or 0.0)
            <= positive_floor,
            persistence,
        ),
        "W1_TEMPERATURE_AND_PHASE_DRIVE_REMAIN_LOW",
    )
    capacity_record = post[10]["metrics"]
    conditioning = (
        float(capacity_record.get("phase_output_capacity_0_1", math.inf))
        <= float(threshold["phase_jacobian_floor"])
        and float(capacity_record.get("phase_output_capacity_1_10", math.inf))
        <= float(threshold["phase_jacobian_floor"])
        and float(post[10]["metrics"]["phase_jacobian_below_floor_fraction_w1"])
        >= float(threshold["low_jacobian_fraction"])
    )
    if conditioning:
        candidates.append(
            {
                "candidate": "PHASE_OUTPUT_CONDITIONING",
                "onset_step": 0,
                "confirmation_step": 10,
                "basis": "PHASE_OUTPUT_CAPACITY_0_1_AND_1_10",
            }
        )

    gradient_floor = float(threshold["gradient_material_fraction"])

    def starved(record: Mapping[str, Any]) -> bool:
        gradient = record.get("full_gradient")
        if not gradient:
            return False
        norms = gradient["gradient_norms"]["TOTAL_OBJECTIVE"]
        return float(norms["phase"]) <= gradient_floor * max(
            float(norms["potential"]), float(norms["temperature"]), 1.0e-300
        )

    add(
        "GRADIENT_STARVATION",
        _first_persistent(
            post,
            [step for step in full_steps if step >= 10],
            starved,
            persistence,
        ),
        "PHASE_HEAD_TOTAL_OBJECTIVE_GRADIENT_FRACTION",
    )
    add(
        "GRADIENT_CONFLICT",
        _first_persistent(
            post,
            [step for step in full_steps if step >= 10],
            lambda record: _material_conflict(
                record,
                float(threshold["conflict_cosine"]),
                gradient_floor,
            ),
            persistence,
        ),
        "MATERIAL_PHASE_HEAD_LOSS_PAIR_CONFLICT",
    )

    epsilon = float(threshold["epsilon"])
    shock_metrics = (
        "phase_max_w1",
        "phase_jacobian_q95_w1",
        "temperature_max_w1",
        "positive_growth_roi_fraction_w1",
    )
    shocked: list[dict[str, Any]] = []
    for name in shock_metrics:
        m100 = float(post[100]["metrics"][name] or 0.0)
        m149 = float(post[149]["metrics"][name] or 0.0)
        m150 = float(post[150]["metrics"][name] or 0.0)
        m151 = float(post[151]["metrics"][name] or 0.0)
        m160 = float(post[160]["metrics"][name] or 0.0)
        delta = m151 - m150
        d_pre = max(abs(m150 - m149), abs(m149 - m100) / 49.0, epsilon)
        relative = abs(delta) / max(abs(m150), epsilon)
        persistent = m160 <= m150 + float(threshold["switch_persistence_fraction_at_step_160"]) * delta
        if (
            delta < 0.0
            and abs(delta) / d_pre >= float(threshold["order_of_magnitude_ratio"])
            and relative >= float(threshold["material_relative_change"])
            and persistent
        ):
            shocked.append(
                {
                    "metric": name,
                    "jump_ratio": abs(delta) / d_pre,
                    "relative_change": relative,
                }
            )
    if len(shocked) >= 2 and any(
        item["metric"] in {"phase_max_w1", "phase_jacobian_q95_w1"}
        for item in shocked
    ):
        candidates.append(
            {
                "candidate": "SWITCH_INDUCED",
                "onset_step": 151,
                "confirmation_step": 160,
                "basis": "STEP_151_MATERIAL_SHOCK_PERSISTING_TO_160",
                "shock_metrics": shocked,
            }
        )

    earliest = min((item["onset_step"] for item in candidates), default=None)
    earliest_candidates = (
        [item for item in candidates if item["onset_step"] == earliest]
        if earliest is not None
        else []
    )
    if len(earliest_candidates) == 1:
        primary = earliest_candidates[0]
        status = "R0B_PRECURSOR_CANDIDATE_IDENTIFIED"
        primary_name = primary["candidate"]
        reason = "EARLIEST_UNIQUE_PERSISTENT_REFERENCE_BLIND_PRECURSOR"
    elif len(earliest_candidates) > 1:
        primary = None
        status = "R0B_INCONCLUSIVE_STOP"
        primary_name = "R0B_INCONCLUSIVE_STOP"
        reason = "EARLIEST_PRECURSOR_TIE"
    elif float(post[175]["metrics"]["phase_activity_fraction_w1"]) == 0.0:
        primary = {
            "candidate": "OPTIMIZATION_UNRESOLVED",
            "onset_step": 175,
            "confirmation_step": 175,
            "basis": "NO_EARLIER_PERSISTENT_PRECURSOR_AND_NO_PHASE_ACTIVITY_AT_175",
        }
        status = "R0B_PRECURSOR_CANDIDATE_IDENTIFIED"
        primary_name = "OPTIMIZATION_UNRESOLVED"
        reason = "BOUNDED_PREFIX_REMAINS_INCOMPETENT_WITHOUT_EARLIER_CLASS"
    else:
        primary = None
        status = "R0B_INCONCLUSIVE_STOP"
        primary_name = "R0B_INCONCLUSIVE_STOP"
        reason = "NO_UNIQUE_PERSISTENT_PRECURSOR"
    return {
        "schema_id": "phk-v23-r0b-reference-blind-adjudication-v1",
        "task_id": "PHK_V23_R0B_FIRST_SWITCH_175_MINIMAL_V2",
        "status": status,
        "PRIMARY_PRECURSOR_CANDIDATE": primary_name,
        "primary_detail": primary,
        "all_supported_candidates": candidates,
        "reason": reason,
        "factorial_required": primary_name == "SWITCH_INDUCED",
        "reference_fields_read": False,
        "stress_fields_or_metrics_read": False,
        "causal_root_cause_identified": False,
        "claim_boundary": "TEMPORAL_PRECURSOR_CANDIDATE_NOT_CAUSAL_ROOT_PROOF",
        "next_stage_authorized": False,
    }


def write_reference_blind_adjudication(
    *, telemetry_path: Path, output_path: Path
) -> dict[str, Any]:
    contracts = load_r0b_contracts()
    records = read_telemetry(telemetry_path)
    result = adjudicate_reference_blind(records, contracts)
    result["telemetry_path"] = str(Path(telemetry_path).resolve())
    result["telemetry_sha256"] = _sha256_path(telemetry_path)
    result["contracts"] = _contract_identity()
    result["written_at_utc"] = datetime.now(timezone.utc).isoformat()
    write_json_exclusive_atomic(output_path, result)
    return result


def run_local_gradient_factorial(
    *, transition_bundle_path: Path, output_path: Path
) -> dict[str, Any]:
    contracts = load_r0b_contracts()
    payload = torch.load(transition_bundle_path, map_location="cpu", weights_only=False)
    if payload.get("schema_id") != "phk-v23-r0b-transition-151-gradient-bundle-v1":
        raise ValueError("unsupported R0B transition bundle")
    if payload.get("checkpoint_selectable") is not False:
        raise PermissionError("R0B transition bundle is checkpoint-selectable")
    physics, _, _ = load_case_physics("FULL")
    config = _strong_raw_config("cpu")
    model = PhkV22RModel(
        physics=physics,
        arm=config.arm,
        hidden_width=config.hidden_width,
        hidden_layers=config.hidden_layers,
    ).to(device="cpu", dtype=torch.float64)
    model.load_state_dict(payload["model_state_dict_theta_150"], strict=True)
    old = payload["old"]
    new = payload["new"]
    old_w1 = old["interior"][:256]
    new_w1 = new["interior"][:256]
    new_w2 = new["interior"][256:512]
    rows = contracts["method"]["loss_head_gradient_matrix"]["loss_rows"]
    cells: dict[str, Any] = {}
    for window_mixture in (0, 1):
        for w1_resample in (0, 1):
            for boundary_refresh in (0, 1):
                chosen_w1 = new_w1 if w1_resample else old_w1
                interior = (
                    torch.cat((chosen_w1, new_w2), dim=0)
                    if window_mixture
                    else torch.cat((chosen_w1, chosen_w1), dim=0)
                )
                boundary = new["boundary"] if boundary_refresh else old["boundary"]
                initial = new["initial"] if boundary_refresh else old["initial"]
                key = f"W{window_mixture}_R{w1_resample}_B{boundary_refresh}"
                cells[key] = {
                    "factors": {
                        "WINDOW_MIXTURE": window_mixture,
                        "W1_RESAMPLE": w1_resample,
                        "BOUNDARY_IC_REFRESH_MIXTURE": boundary_refresh,
                    },
                    "gradient": gradient_matrix_preserving_state(
                        model,
                        interior,
                        boundary,
                        contracts,
                        initial=initial,
                        loss_rows=rows,
                    ),
                }
    responses = {
        key: {
            "total_loss": float(
                value["gradient"]["loss_values_with_existing_effective_weights"][
                    "TOTAL_OBJECTIVE"
                ]
            ),
            "phase_total_gradient_norm": float(
                value["gradient"]["gradient_norms"]["TOTAL_OBJECTIVE"]["phase"]
            ),
        }
        for key, value in cells.items()
    }
    main_effects: dict[str, dict[str, float]] = {}
    factor_codes = {
        "WINDOW_MIXTURE": "W",
        "W1_RESAMPLE": "R",
        "BOUNDARY_IC_REFRESH_MIXTURE": "B",
    }
    for factor, code in factor_codes.items():
        main_effects[factor] = {}
        for response in ("total_loss", "phase_total_gradient_norm"):
            high = [responses[key][response] for key in responses if f"{code}1" in key]
            low = [responses[key][response] for key in responses if f"{code}0" in key]
            main_effects[factor][response] = float(np.mean(high) - np.mean(low))
    result = {
        "schema_id": "phk-v23-r0b-local-gradient-factorial-v1",
        "status": "NON_VOTING_LOCAL_CPU_GRADIENT_CONTEXT_COMPLETE",
        "transition_bundle_sha256": _sha256_path(transition_bundle_path),
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "parameter_updates": 0,
        "reference_fields_read": False,
        "stress_fields_or_metrics_read": False,
        "cells": cells,
        "responses": responses,
        "main_effects_high_minus_low": main_effects,
        "claim_boundary": "ASSOCIATION_CONTEXT_ONLY_NOT_CAUSAL_FACTOR_PROOF",
    }
    write_json_exclusive_atomic(output_path, result)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--output-root", type=Path, required=True)
    run_parser.add_argument("--device", default="cuda:0")
    run_parser.add_argument("--source-identity", required=True)
    run_parser.add_argument("--hourly-price-cny", type=float, required=True)
    adjudicate_parser = subparsers.add_parser("adjudicate")
    adjudicate_parser.add_argument("--telemetry", type=Path, required=True)
    adjudicate_parser.add_argument("--output", type=Path, required=True)
    factorial_parser = subparsers.add_parser("factorial")
    factorial_parser.add_argument("--transition-bundle", type=Path, required=True)
    factorial_parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.mode == "run":
        result = run_reference_blind_gpu_replay(
            output_root=args.output_root,
            device_name=args.device,
            source_identity=args.source_identity,
            hourly_price_cny=args.hourly_price_cny,
        )
    elif args.mode == "adjudicate":
        result = write_reference_blind_adjudication(
            telemetry_path=args.telemetry, output_path=args.output
        )
    else:
        result = run_local_gradient_factorial(
            transition_bundle_path=args.transition_bundle,
            output_path=args.output,
        )
    print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DIAGNOSTIC_CONTRACT_PATH",
    "METHOD_CONTRACT_PATH",
    "PROGRAM_CONTRACT_PATH",
    "R0BObserver",
    "adjudicate_reference_blind",
    "load_r0b_contracts",
    "main",
    "read_telemetry",
    "run_local_gradient_factorial",
    "run_reference_blind_gpu_replay",
    "write_reference_blind_adjudication",
]
