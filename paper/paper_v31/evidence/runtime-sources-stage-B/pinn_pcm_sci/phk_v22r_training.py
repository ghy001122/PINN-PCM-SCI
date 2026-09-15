"""Bounded training and profiling runner for PHK-V2.2R method arms."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import time
from typing import Any, Mapping, Protocol

import numpy as np
import torch

from .phk_benchmark import PhkControl
from .phk_v21_benchmark import PhkV21CaseSpec, load_phk_v21_physical
from .phk_v22r_pinn import (
    CollocationMixture,
    FrequencyBand,
    PhkCollocationSampler,
    PhkV22RArm,
    PhkV22RModel,
    PhkV22RPhysics,
    boundary_residuals,
    initial_residuals,
    interior_residuals,
    normalized_residual_loss,
)


ROOT = Path(__file__).resolve().parents[1]
PROGRAM_CONTRACT_PATH = ROOT / "configs" / "phk_v22r" / "program_contract.json"
METHOD_CONTRACT_PATH = ROOT / "configs" / "phk_v22r" / "method_contract.json"


PDE_SCALES: Mapping[str, float] = {
    "electric": 1.0,
    "thermal": 4.0,
    "phase": 5.0,
}

BOUNDARY_SCALES: Mapping[str, float] = {
    "bc_potential_top": 0.72,
    "bc_potential_heater": 0.72,
    "bc_electric_insulating_bottom": 1.0,
    "bc_electric_insulating_side": 1.0,
    "bc_temperature_top": 1.0,
    "bc_temperature_robin": 1.0,
    "bc_phase_no_flux": 1.0,
}

INITIAL_SCALES: Mapping[str, float] = {
    "ic_potential": 0.72,
    "ic_temperature": 1.0,
    "ic_phase": 0.03,
}


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _write_json_exclusive(path: Path, payload: Mapping[str, Any]) -> None:
    exact = Path(path)
    exact.parent.mkdir(parents=True, exist_ok=True)
    with exact.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


@dataclass(frozen=True)
class PhkTrainingConfig:
    arm: str
    case_control: str = "FULL"
    updates: int = 1000
    seed: int = 17
    hidden_width: int = 64
    hidden_layers: int = 4
    frequency_band: str = "BAND_A"
    learning_rate: float = 1.0e-3
    gradient_clip_norm: float = 10.0
    interior_points: int = 512
    boundary_points: int = 128
    initial_points: int = 128
    candidate_pool_multiplier: int = 4
    refresh_updates: int = 250
    log_every: int = 25
    checkpoint_every: int = 1000
    pde_weight: float = 1.0
    boundary_weight: float = 5.0
    initial_weight: float = 1.0
    dtype: str = "float64"
    device: str = "cpu"

    def validate(self) -> None:
        PhkV22RArm(self.arm)
        control = PhkControl(self.case_control)
        if control not in {
            PhkControl.FULL,
            PhkControl.INTERFACE_WIDTH_0_025,
            PhkControl.HEATER_WIDTH_0_50,
        }:
            raise ValueError("training case is outside the V2.2R matrix")
        positive_ints = {
            "updates": self.updates,
            "hidden_width": self.hidden_width,
            "hidden_layers": self.hidden_layers,
            "interior_points": self.interior_points,
            "boundary_points": self.boundary_points,
            "initial_points": self.initial_points,
            "candidate_pool_multiplier": self.candidate_pool_multiplier,
            "refresh_updates": self.refresh_updates,
            "log_every": self.log_every,
            "checkpoint_every": self.checkpoint_every,
        }
        for name, value in positive_ints.items():
            if int(value) <= 0:
                raise ValueError(f"{name} must be positive")
        if self.boundary_points % 4:
            raise ValueError("boundary_points must be divisible by four")
        for name in (
            "learning_rate",
            "gradient_clip_norm",
            "pde_weight",
            "boundary_weight",
            "initial_weight",
        ):
            value = float(getattr(self, name))
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be positive and finite")
        if self.dtype != "float64":
            raise ValueError("PHK-V2.2R training is frozen to float64")
        if self.frequency_band not in {"BAND_A", "BAND_B_CONSERVATIVE"}:
            raise ValueError("unknown frozen frequency band")
        if self.device != "cpu" and not self.device.startswith("cuda"):
            raise ValueError("device must be cpu or a CUDA device")

    @property
    def identity(self) -> str:
        return hashlib.sha256(_canonical_json(asdict(self))).hexdigest().upper()


@dataclass(frozen=True)
class TrainingOutcome:
    run_directory: Path
    status: str
    final_loss: float
    minimum_loss: float
    wall_seconds: float
    seconds_per_update: float
    peak_gpu_memory_bytes: int
    checkpoint_path: Path
    executed_updates: int


@dataclass(frozen=True)
class TrainingStepSpec:
    """Generic per-step controls for a bounded staged training campaign."""

    stage: str
    block_type: str
    active_windows: int
    coupling_alpha: float
    active_heads: tuple[str, ...]
    active_loss_groups: tuple[str, ...]

    def validate(self) -> None:
        if not self.stage or not self.block_type:
            raise ValueError("training stage and block type must be non-empty")
        if not 1 <= int(self.active_windows) <= 4:
            raise ValueError("active windows must lie in [1, 4]")
        alpha = float(self.coupling_alpha)
        if not math.isfinite(alpha) or not 0.0 <= alpha <= 1.0:
            raise ValueError("coupling alpha must lie in [0, 1]")
        if not self.active_heads or any(name not in {"potential", "temperature", "phase"} for name in self.active_heads):
            raise ValueError("active head set is invalid")
        if len(set(self.active_heads)) != len(self.active_heads):
            raise ValueError("active head set contains duplicates")
        if not self.active_loss_groups or len(set(self.active_loss_groups)) != len(self.active_loss_groups):
            raise ValueError("active loss groups are empty or duplicated")


class TrainingStepPolicy(Protocol):
    """A bounded controller that selects an immutable spec before each step."""

    stop_requested: bool

    def step_spec(
        self, optimizer_step: int, total_updates: int
    ) -> TrainingStepSpec: ...


class TrainingModelFactory(Protocol):
    """Construct a model while leaving the legacy default factory untouched."""

    def __call__(
        self,
        *,
        physics: PhkV22RPhysics,
        config: PhkTrainingConfig,
        frequency_band: FrequencyBand,
    ) -> PhkV22RModel: ...


@dataclass(frozen=True)
class TrainingObservation:
    """Read-only view exposed at the optional training-observer seam."""

    phase: str
    optimizer_step: int
    update_index: int | None
    active_windows: int
    collocation_refreshed: bool
    model: PhkV22RModel
    interior: torch.Tensor | None
    boundary: Mapping[str, torch.Tensor] | None
    initial: torch.Tensor | None
    scalars: Mapping[str, float]
    optimizer_state_summary: Mapping[str, Mapping[str, float | int]] | None = None
    gradient_combination_diagnostics: Mapping[str, Any] | None = None
    step_metadata: Mapping[str, Any] | None = None


class TrainingObserver(Protocol):
    """Optional observer; implementations must not mutate the supplied state."""

    def observe(self, observation: TrainingObservation) -> None: ...


class GradientCombiner(Protocol):
    """Single seam for replacing the legacy summed-loss backward operation."""

    def combine(
        self,
        *,
        model: PhkV22RModel,
        loss_groups: Mapping[str, torch.Tensor],
        legacy_total: torch.Tensor,
    ) -> Mapping[str, Any]: ...

    def manifest(self) -> Mapping[str, Any]: ...


_LEGACY_OBSERVER_PHASES = frozenset(
    {"PRE_RUN", "PRE_REFRESH", "PRE_BACKWARD", "POST_STEP"}
)


def _observer_wants_phase(observer: TrainingObserver | None, phase: str) -> bool:
    if observer is None:
        return False
    requested = getattr(observer, "requested_phases", _LEGACY_OBSERVER_PHASES)
    return phase in requested


def _emit_observation(
    observer: TrainingObserver | None, observation: TrainingObservation
) -> None:
    if _observer_wants_phase(observer, observation.phase):
        assert observer is not None
        observer.observe(observation)


def _optimizer_scalar_summary(
    model: PhkV22RModel, optimizer: torch.optim.Optimizer
) -> dict[str, dict[str, float | int]]:
    """Return detached scalar Adam-state summaries without exposing the optimizer."""

    result: dict[str, dict[str, float | int]] = {}
    for name, parameter in model.named_parameters():
        state = optimizer.state.get(parameter, {})
        step = state.get("step", 0)
        if isinstance(step, torch.Tensor):
            step_value = int(step.detach().cpu())
        else:
            step_value = int(step)
        exp_avg = state.get("exp_avg")
        exp_avg_sq = state.get("exp_avg_sq")
        result[name] = {
            "step": step_value,
            "exp_avg_l2": (
                float(torch.linalg.vector_norm(exp_avg.detach()).cpu())
                if isinstance(exp_avg, torch.Tensor)
                else 0.0
            ),
            "exp_avg_sq_l2": (
                float(torch.linalg.vector_norm(exp_avg_sq.detach()).cpu())
                if isinstance(exp_avg_sq, torch.Tensor)
                else 0.0
            ),
        }
    return result


def load_case_physics(
    control: PhkControl | str = PhkControl.FULL,
) -> tuple[PhkV22RPhysics, str, str]:
    """Load only contracts; this function never opens a reference carrier."""

    physical = load_phk_v21_physical(
        program_path=ROOT / "configs" / "phk_v21" / "program_contract.json",
        object_path=ROOT / "configs" / "phk_v21" / "object_numerical_contract.json",
        legacy_program_path=ROOT / "configs" / "phk_v2" / "program_contract.json",
        legacy_object_path=ROOT / "configs" / "phk_v2" / "object_numerical_contract.json",
    )
    selected = PhkControl(control)
    if selected not in {
        PhkControl.FULL,
        PhkControl.INTERFACE_WIDTH_0_025,
        PhkControl.HEATER_WIDTH_0_50,
    }:
        raise ValueError("training case is outside the V2.2R matrix")
    case = PhkV21CaseSpec.nominal(physical, control=selected)
    physics = PhkV22RPhysics.from_contract(physical, case)
    return physics, physical.program.sha256, physical.object.sha256


def _frequency_band(name: str) -> FrequencyBand:
    if name == "BAND_A":
        return FrequencyBand.band_a()
    if name == "BAND_B_CONSERVATIVE":
        return FrequencyBand.conservative()
    raise ValueError(f"unknown frequency band: {name}")


def _active_windows(update: int, total_updates: int) -> int:
    """Open windows at frozen fractions 0, 0.15, 0.35, and 0.55."""

    fraction = update / max(total_updates, 1)
    if fraction < 0.15:
        return 1
    if fraction < 0.35:
        return 2
    if fraction < 0.55:
        return 3
    return 4


def _merge_residuals(
    groups: Mapping[str, Mapping[str, torch.Tensor]],
) -> dict[str, torch.Tensor]:
    merged: dict[str, list[torch.Tensor]] = {}
    for prefix, residuals in groups.items():
        for name, value in residuals.items():
            merged.setdefault(f"{prefix}:{name}", []).append(value.reshape(-1, 1))
    return {name: torch.cat(values, dim=0) for name, values in merged.items()}


def _boundary_loss(
    model: PhkV22RModel,
    batches: Mapping[str, torch.Tensor],
    *,
    coupling_alpha: float = 1.0,
) -> tuple[torch.Tensor, dict[str, float]]:
    total, diagnostics, _ = _boundary_loss_by_field(
        model, batches, coupling_alpha=coupling_alpha
    )
    return total, diagnostics


def _boundary_field(name: str) -> str:
    if name.startswith("bc_phase"):
        return "phase"
    if name.startswith("bc_temperature"):
        return "temperature"
    if name.startswith("bc_potential") or name.startswith("bc_electric"):
        return "potential"
    raise KeyError(f"unknown boundary residual family: {name}")


def _boundary_loss_by_field(
    model: PhkV22RModel,
    batches: Mapping[str, torch.Tensor],
    *,
    coupling_alpha: float = 1.0,
) -> tuple[torch.Tensor, dict[str, float], dict[str, torch.Tensor]]:
    residuals = _merge_residuals(
        {
            side: boundary_residuals(
                model,
                coordinates,
                side=side,
                coupling_alpha=coupling_alpha,
            )
            for side, coordinates in batches.items()
        }
    )
    losses: list[torch.Tensor] = []
    fields: list[str] = []
    diagnostics = {}
    for qualified_name, value in residuals.items():
        base_name = qualified_name.split(":", 1)[1]
        scale = BOUNDARY_SCALES[base_name]
        item = torch.mean((value / scale).square())
        losses.append(item)
        fields.append(_boundary_field(base_name))
        diagnostics[qualified_name] = float(item.detach().cpu())
    denominator = float(len(losses))
    by_field = {
        name: torch.stack(
            [item for item, field in zip(losses, fields, strict=True) if field == name]
        ).sum()
        / denominator
        for name in ("potential", "temperature", "phase")
    }
    return torch.stack(losses).mean(), diagnostics, by_field


def _initial_loss_by_field(
    residuals: Mapping[str, torch.Tensor],
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    ordered = ("ic_potential", "ic_temperature", "ic_phase")
    losses = {
        name.removeprefix("ic_"): torch.mean(
            (residuals[name] / float(INITIAL_SCALES[name])).square()
        )
        / float(len(ordered))
        for name in ordered
    }
    # Keep the scalar on the exact legacy reduction path.  The split values are
    # used only by staged objectives and retain the same denominator.
    return normalized_residual_loss(residuals, scales=INITIAL_SCALES), losses


def canonical_weighted_loss_groups(
    *,
    interior: Mapping[str, torch.Tensor],
    boundary_loss: torch.Tensor,
    initial_loss: torch.Tensor,
    config: PhkTrainingConfig,
) -> dict[str, torch.Tensor]:
    """Decompose the frozen objective without changing its scalar semantics."""

    required = ("electric", "thermal", "phase")
    missing = [name for name in required if name not in interior]
    if missing:
        raise KeyError(f"missing canonical PDE residuals: {missing}")
    pde_groups = {
        f"G{index}_{name.upper()}_PDE": (
            config.pde_weight
            * torch.mean((interior[name] / float(PDE_SCALES[name])).square())
            / 3.0
        )
        for index, name in enumerate(required, start=1)
    }
    return {
        **pde_groups,
        "G4_BOUNDARY_INITIAL": (
            config.boundary_weight * boundary_loss
            + config.initial_weight * initial_loss
        ),
    }


def campaign_weighted_loss_groups(
    *,
    interior: Mapping[str, torch.Tensor],
    boundary_by_field: Mapping[str, torch.Tensor],
    initial_by_field: Mapping[str, torch.Tensor],
    config: PhkTrainingConfig,
) -> dict[str, torch.Tensor]:
    """Expose exact field-split auxiliaries for staged ConFIG objectives.

    Each field contribution retains the denominator of the legacy aggregate,
    so the ET and phase auxiliary pieces sum exactly to the R1a G4 scalar.
    """

    required_fields = ("potential", "temperature", "phase")
    if any(name not in boundary_by_field for name in required_fields):
        raise KeyError("missing boundary field contribution")
    if any(name not in initial_by_field for name in required_fields):
        raise KeyError("missing initial field contribution")
    pde = canonical_weighted_loss_groups(
        interior=interior,
        boundary_loss=torch.stack(tuple(boundary_by_field.values())).sum(),
        initial_loss=torch.stack(tuple(initial_by_field.values())).sum(),
        config=config,
    )
    auxiliary_by_field = {
        name: config.boundary_weight * boundary_by_field[name]
        + config.initial_weight * initial_by_field[name]
        for name in required_fields
    }
    et = auxiliary_by_field["potential"] + auxiliary_by_field["temperature"]
    phase = auxiliary_by_field["phase"]
    return {
        "G1_ELECTRIC_PDE": pde["G1_ELECTRIC_PDE"],
        "G2_THERMAL_PDE": pde["G2_THERMAL_PDE"],
        "G3_PHASE_PDE": pde["G3_PHASE_PDE"],
        "G4_ET_AUXILIARY": et,
        "G4_PHASE_AUXILIARY": phase,
        "G4_BOUNDARY_INITIAL": et + phase,
    }


def _checkpoint_payload(
    *,
    model: PhkV22RModel,
    optimizer: torch.optim.Optimizer,
    config: PhkTrainingConfig,
    update: int,
    program_contract_sha256: str,
    method_contract_sha256: str,
    physical_program_sha256: str,
    physical_object_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_id": "phk-v22r-checkpoint-v1-1",
        "update": int(update),
        "training_config": asdict(config),
        "training_config_sha256": config.identity,
        "architecture": model.architecture_manifest(),
        "program_contract_sha256": program_contract_sha256,
        "method_contract_sha256": method_contract_sha256,
        "physical_program_sha256": physical_program_sha256,
        "physical_object_sha256": physical_object_sha256,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "torch_version": torch.__version__,
    }


def train(
    config: PhkTrainingConfig,
    *,
    run_directory: Path,
    execution_limit: int | None = None,
    observer: TrainingObserver | None = None,
    gradient_combiner: GradientCombiner | None = None,
    step_policy: TrainingStepPolicy | None = None,
    model_factory: TrainingModelFactory | None = None,
    execution_metadata: Mapping[str, Any] | None = None,
) -> TrainingOutcome:
    """Run one bounded arm from scratch and emit an immutable evidence directory."""

    config.validate()
    execution_updates = (
        config.updates if execution_limit is None else int(execution_limit)
    )
    if not 1 <= execution_updates <= config.updates:
        raise ValueError("execution_limit must be within the frozen schedule")
    diagnostic_prefix = execution_updates < config.updates
    output = Path(run_directory).resolve()
    output.mkdir(parents=True, exist_ok=False)
    program_contract_sha256 = _sha256_path(PROGRAM_CONTRACT_PATH)
    method_contract_sha256 = _sha256_path(METHOD_CONTRACT_PATH)
    physics, physical_program_sha256, physical_object_sha256 = load_case_physics(
        config.case_control
    )
    device = torch.device(config.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA training requested but CUDA is unavailable")
    dtype = torch.float64
    random.seed(config.seed)
    np.random.seed(config.seed)
    torch.manual_seed(config.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(config.seed)
        torch.cuda.reset_peak_memory_stats(device)

    band = _frequency_band(config.frequency_band)
    if model_factory is None:
        model = PhkV22RModel(
            physics=physics,
            arm=config.arm,
            hidden_width=config.hidden_width,
            hidden_layers=config.hidden_layers,
            frequency_band=band,
        )
    else:
        model = model_factory(physics=physics, config=config, frequency_band=band)
    model = model.to(device=device, dtype=dtype)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    mixture = CollocationMixture(
        candidate_pool_multiplier=config.candidate_pool_multiplier
    )
    sampler = PhkCollocationSampler(
        physics=physics,
        mixture=mixture,
        seed=config.seed,
    )
    manifest = {
        "schema_id": "phk-v22r-training-run-manifest-v1-1",
        "status": "RUNNING_DIAGNOSTIC_PREFIX" if diagnostic_prefix else "RUNNING",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "training_config": asdict(config),
        "training_config_sha256": config.identity,
        "architecture": model.architecture_manifest(),
        "program_contract": str(PROGRAM_CONTRACT_PATH.relative_to(ROOT)),
        "program_contract_sha256": program_contract_sha256,
        "method_contract": str(METHOD_CONTRACT_PATH.relative_to(ROOT)),
        "method_contract_sha256": method_contract_sha256,
        "physical_program_sha256": physical_program_sha256,
        "physical_object_sha256": physical_object_sha256,
        "reference_fields_read": False,
        "training_labels_used": False,
        "anchor_fields_used": False,
        "initialization": "SCRATCH_START",
        "checkpoint_policy": (
            "FINAL_ONLY"
            if config.checkpoint_every >= execution_updates
            else "PERIODIC_PLUS_FINAL"
        ),
        "sampler_inputs": (
            ["SOBOL", "PDE_RESIDUAL", "PREDICTED_PHASE", "PREDICTED_JOULE"]
            if PhkV22RArm(config.arm).uses_physics_sampler
            else ["SOBOL"]
        ),
        "pde_scales": dict(PDE_SCALES),
        "boundary_scales": dict(BOUNDARY_SCALES),
        "initial_scales": dict(INITIAL_SCALES),
        "loss_weights": {
            "pde": config.pde_weight,
            "boundary": config.boundary_weight,
            "initial": config.initial_weight,
        },
        "causal_window_open_fractions": (
            [0.0, 0.15, 0.35, 0.55] if step_policy is None else None
        ),
    }
    if diagnostic_prefix:
        manifest.update(
            {
                "scientific_schedule_denominator": config.updates,
                "canonical_optimizer_steps_planned": execution_updates,
                "execution_identity": "DIAGNOSTIC_PREFIX",
            }
        )
    if execution_metadata is not None:
        manifest["execution_metadata"] = dict(execution_metadata)
    if gradient_combiner is not None:
        manifest["gradient_combiner"] = dict(gradient_combiner.manifest())
    if step_policy is not None:
        manifest["step_policy"] = type(step_policy).__name__
        manifest["causal_window_schedule"] = (
            "STEP_POLICY_CONTROLLED_SEE_EXECUTION_METADATA_AND_FROZEN_CONTRACT"
        )
    _write_json_exclusive(output / "manifest-start.json", manifest)

    log_path = output / "training-log.jsonl"
    checkpoint_path = output / "checkpoint-final.pt"
    cached_interior: torch.Tensor | None = None
    cached_boundary: dict[str, torch.Tensor] | None = None
    cached_initial: torch.Tensor | None = None
    cached_windows = 0
    minimum_loss = math.inf
    final_loss = math.inf
    start = time.perf_counter()
    status = "DIAGNOSTIC_PREFIX" if diagnostic_prefix else "COMPLETE"
    executed_updates = 0
    try:
        if observer is not None:
            _emit_observation(
                observer,
                TrainingObservation(
                    phase="PRE_RUN",
                    optimizer_step=0,
                    update_index=None,
                    active_windows=0,
                    collocation_refreshed=False,
                    model=model,
                    interior=None,
                    boundary=None,
                    initial=None,
                    scalars={},
                )
            )
        with log_path.open("x", encoding="utf-8", newline="\n") as log_handle:
            for update in range(execution_updates):
                optimizer_step = update + 1
                if step_policy is None:
                    step_spec = TrainingStepSpec(
                        stage="LEGACY_JOINT",
                        block_type="JOINT_BLOCK",
                        active_windows=_active_windows(update, config.updates),
                        coupling_alpha=1.0,
                        active_heads=("potential", "temperature", "phase"),
                        active_loss_groups=(
                            "G1_ELECTRIC_PDE",
                            "G2_THERMAL_PDE",
                            "G3_PHASE_PDE",
                            "G4_BOUNDARY_INITIAL",
                        ),
                    )
                else:
                    step_spec = step_policy.step_spec(optimizer_step, config.updates)
                step_spec.validate()
                active_windows = step_spec.active_windows
                active_head_set = set(step_spec.active_heads)
                for head_name, head in model.heads.items():
                    active = head_name in active_head_set
                    for parameter in head.parameters():
                        parameter.requires_grad_(active)
                if model.high_temperature is not None:
                    for parameter in model.high_temperature.parameters():
                        parameter.requires_grad_("temperature" in active_head_set)
                if model.high_phase is not None:
                    for parameter in model.high_phase.parameters():
                        parameter.requires_grad_("phase" in active_head_set)
                step_metadata = {
                    "stage": step_spec.stage,
                    "block_type": step_spec.block_type,
                    "coupling_alpha": step_spec.coupling_alpha,
                    "active_heads": list(step_spec.active_heads),
                    "active_loss_groups": list(step_spec.active_loss_groups),
                }
                needs_refresh = (
                    cached_interior is None
                    or update % config.refresh_updates == 0
                    or active_windows != cached_windows
                )
                if needs_refresh:
                    if observer is not None and cached_interior is not None:
                        _emit_observation(
                            observer,
                            TrainingObservation(
                                phase="PRE_REFRESH",
                                optimizer_step=update + 1,
                                update_index=update,
                                active_windows=cached_windows,
                                collocation_refreshed=True,
                                model=model,
                                interior=cached_interior,
                                boundary=cached_boundary,
                                initial=cached_initial,
                                scalars={},
                                step_metadata=step_metadata,
                            )
                        )
                    cached_interior = sampler.select_interior(
                        model,
                        count=config.interior_points,
                        active_windows=active_windows,
                        physics_aware=PhkV22RArm(config.arm).uses_physics_sampler,
                        dtype=dtype,
                        device=device,
                    ).detach()
                    cached_boundary = sampler.boundary(
                        config.boundary_points // 4,
                        active_windows=active_windows,
                        dtype=dtype,
                        device=device,
                    )
                    cached_initial = sampler.initial(
                        config.initial_points,
                        dtype=dtype,
                        device=device,
                    )
                    cached_windows = active_windows
                assert cached_interior is not None
                assert cached_boundary is not None
                assert cached_initial is not None

                if observer is not None:
                    _emit_observation(
                        observer,
                        TrainingObservation(
                            phase="PRE_BACKWARD",
                            optimizer_step=update + 1,
                            update_index=update,
                            active_windows=active_windows,
                            collocation_refreshed=needs_refresh,
                            model=model,
                            interior=cached_interior,
                            boundary=cached_boundary,
                            initial=cached_initial,
                            scalars={},
                            step_metadata=step_metadata,
                        )
                    )

                optimizer.zero_grad(set_to_none=True)
                interior = interior_residuals(
                    model,
                    cached_interior,
                    coupling_alpha=step_spec.coupling_alpha,
                )
                pde_loss = normalized_residual_loss(interior, scales=PDE_SCALES)
                bc_loss, bc_diagnostics, boundary_by_field = _boundary_loss_by_field(
                    model,
                    cached_boundary,
                    coupling_alpha=step_spec.coupling_alpha,
                )
                ic = initial_residuals(model, cached_initial)
                ic_loss, initial_by_field = _initial_loss_by_field(ic)
                full_total = (
                    config.pde_weight * pde_loss
                    + config.boundary_weight * bc_loss
                    + config.initial_weight * ic_loss
                )
                available_groups = campaign_weighted_loss_groups(
                    interior=interior,
                    boundary_by_field=boundary_by_field,
                    initial_by_field=initial_by_field,
                    config=config,
                )
                if step_policy is None:
                    loss_groups = {
                        name: available_groups[name]
                        for name in step_spec.active_loss_groups
                    }
                    total = full_total
                else:
                    unknown_groups = [
                        name
                        for name in step_spec.active_loss_groups
                        if name not in available_groups
                    ]
                    if unknown_groups:
                        raise KeyError(f"unknown staged loss groups: {unknown_groups}")
                    loss_groups = {
                        name: available_groups[name]
                        for name in step_spec.active_loss_groups
                    }
                    total = torch.stack(tuple(loss_groups.values())).sum()
                if not bool(torch.isfinite(total)) or not bool(torch.isfinite(full_total)):
                    raise FloatingPointError(f"nonfinite loss at update {update + 1}")
                gradient_combination_diagnostics: Mapping[str, Any] | None = None
                if gradient_combiner is None:
                    total.backward()
                else:
                    gradient_combination_diagnostics = gradient_combiner.combine(
                        model=model,
                        loss_groups=loss_groups,
                        legacy_total=total,
                    )
                if observer is not None:
                    _emit_observation(
                        observer,
                        TrainingObservation(
                            phase="POST_BACKWARD_PRE_CLIP",
                            optimizer_step=update + 1,
                            update_index=update,
                            active_windows=active_windows,
                            collocation_refreshed=needs_refresh,
                            model=model,
                            interior=cached_interior,
                            boundary=cached_boundary,
                            initial=cached_initial,
                            scalars={
                                "loss": float(total.detach().cpu()),
                                "pde_loss": float(pde_loss.detach().cpu()),
                                "boundary_loss": float(bc_loss.detach().cpu()),
                                "initial_loss": float(ic_loss.detach().cpu()),
                                "full_all_group_total_at_current_coupling": float(
                                    full_total.detach().cpu()
                                ),
                            },
                            gradient_combination_diagnostics=(
                                gradient_combination_diagnostics
                            ),
                            step_metadata=step_metadata,
                        ),
                    )
                gradient_norm = torch.nn.utils.clip_grad_norm_(
                    model.parameters(), config.gradient_clip_norm
                )
                if not bool(torch.isfinite(gradient_norm)):
                    raise FloatingPointError(
                        f"nonfinite gradient norm at update {update + 1}"
                    )
                if observer is not None:
                    _emit_observation(
                        observer,
                        TrainingObservation(
                            phase="POST_CLIP_PRE_STEP",
                            optimizer_step=update + 1,
                            update_index=update,
                            active_windows=active_windows,
                            collocation_refreshed=needs_refresh,
                            model=model,
                            interior=cached_interior,
                            boundary=cached_boundary,
                            initial=cached_initial,
                            scalars={
                                "gradient_norm_before_clip": float(
                                    gradient_norm.detach().cpu()
                                )
                            },
                            gradient_combination_diagnostics=(
                                gradient_combination_diagnostics
                            ),
                            step_metadata=step_metadata,
                        ),
                    )
                optimizer.step()
                final_loss = float(total.detach().cpu())
                minimum_loss = min(minimum_loss, final_loss)

                if observer is not None:
                    optimizer_summary = (
                        _optimizer_scalar_summary(model, optimizer)
                        if bool(
                            getattr(
                                observer, "include_optimizer_state_summary", False
                            )
                        )
                        else None
                    )
                    _emit_observation(
                        observer,
                        TrainingObservation(
                            phase="POST_STEP",
                            optimizer_step=update + 1,
                            update_index=update,
                            active_windows=active_windows,
                            collocation_refreshed=needs_refresh,
                            model=model,
                            interior=cached_interior,
                            boundary=cached_boundary,
                            initial=cached_initial,
                            scalars={
                                "loss": final_loss,
                                "pde_loss": float(pde_loss.detach().cpu()),
                                "boundary_loss": float(bc_loss.detach().cpu()),
                                "initial_loss": float(ic_loss.detach().cpu()),
                                "gradient_norm_before_clip": float(
                                    gradient_norm.detach().cpu()
                                ),
                                "full_all_group_total_at_current_coupling": float(
                                    full_total.detach().cpu()
                                ),
                            },
                            optimizer_state_summary=optimizer_summary,
                            gradient_combination_diagnostics=(
                                gradient_combination_diagnostics
                            ),
                            step_metadata=step_metadata,
                        )
                    )
                executed_updates = optimizer_step

                should_log = (
                    update == 0
                    or (update + 1) % config.log_every == 0
                    or update + 1 == execution_updates
                )
                if should_log:
                    record = {
                        "update": update + 1,
                        "active_windows": active_windows,
                        "collocation_refreshed": needs_refresh,
                        "loss": final_loss,
                        "pde_loss": float(pde_loss.detach().cpu()),
                        "boundary_loss": float(bc_loss.detach().cpu()),
                        "initial_loss": float(ic_loss.detach().cpu()),
                        "gradient_norm_before_clip": float(gradient_norm.detach().cpu()),
                        "electric_rms": float(
                            torch.sqrt(torch.mean(interior["electric"].detach().square())).cpu()
                        ),
                        "thermal_rms": float(
                            torch.sqrt(torch.mean(interior["thermal"].detach().square())).cpu()
                        ),
                        "phase_rms": float(
                            torch.sqrt(torch.mean(interior["phase"].detach().square())).cpu()
                        ),
                        "boundary_components": bc_diagnostics,
                        "elapsed_seconds": time.perf_counter() - start,
                        "stage": step_spec.stage,
                        "block_type": step_spec.block_type,
                        "coupling_alpha": step_spec.coupling_alpha,
                        "active_heads": list(step_spec.active_heads),
                        "active_loss_groups": list(step_spec.active_loss_groups),
                        "full_all_group_total_at_current_coupling": float(
                            full_total.detach().cpu()
                        ),
                    }
                    log_handle.write(json.dumps(record, sort_keys=True) + "\n")
                    log_handle.flush()
                if (update + 1) % config.checkpoint_every == 0 and (
                    update + 1 < execution_updates
                ):
                    torch.save(
                        _checkpoint_payload(
                            model=model,
                            optimizer=optimizer,
                            config=config,
                            update=update + 1,
                            program_contract_sha256=program_contract_sha256,
                            method_contract_sha256=method_contract_sha256,
                            physical_program_sha256=physical_program_sha256,
                            physical_object_sha256=physical_object_sha256,
                        ),
                        output / f"checkpoint-{update + 1:06d}.pt",
                    )
                if step_policy is not None and bool(step_policy.stop_requested):
                    status = "EARLY_POLICY_STOP"
                    break
        for parameter in model.parameters():
            parameter.requires_grad_(True)
        torch.save(
            _checkpoint_payload(
                model=model,
                optimizer=optimizer,
                config=config,
                update=executed_updates,
                program_contract_sha256=program_contract_sha256,
                method_contract_sha256=method_contract_sha256,
                physical_program_sha256=physical_program_sha256,
                physical_object_sha256=physical_object_sha256,
            ),
            checkpoint_path,
        )
    except BaseException:
        status = "FAILED"
        raise
    finally:
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        wall_seconds = time.perf_counter() - start
        peak_memory = (
            int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else 0
        )
        final_manifest = {
            **manifest,
            "status": status,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "wall_seconds": wall_seconds,
            "seconds_per_update": wall_seconds / max(executed_updates, 1),
            "peak_gpu_memory_bytes": peak_memory,
            "final_loss": final_loss,
            "minimum_loss": minimum_loss,
        }
        if diagnostic_prefix:
            final_manifest["canonical_optimizer_steps_executed"] = executed_updates
        if step_policy is not None:
            final_manifest["canonical_optimizer_steps_executed"] = executed_updates
            final_manifest["scientific_schedule_denominator"] = config.updates
        _write_json_exclusive(output / "manifest-final.json", final_manifest)
    return TrainingOutcome(
        run_directory=output,
        status=status,
        final_loss=final_loss,
        minimum_loss=minimum_loss,
        wall_seconds=wall_seconds,
        seconds_per_update=wall_seconds / max(executed_updates, 1),
        peak_gpu_memory_bytes=peak_memory,
        checkpoint_path=checkpoint_path,
        executed_updates=executed_updates,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=[arm.value for arm in PhkV22RArm], required=True)
    parser.add_argument(
        "--case-control",
        choices=[
            PhkControl.FULL.value,
            PhkControl.INTERFACE_WIDTH_0_025.value,
            PhkControl.HEATER_WIDTH_0_50.value,
        ],
        default=PhkControl.FULL.value,
    )
    parser.add_argument("--run-directory", type=Path, required=True)
    parser.add_argument("--updates", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--hidden-width", type=int, default=64)
    parser.add_argument("--hidden-layers", type=int, default=4)
    parser.add_argument(
        "--frequency-band",
        choices=["BAND_A", "BAND_B_CONSERVATIVE"],
        default="BAND_A",
    )
    parser.add_argument("--learning-rate", type=float, default=1.0e-3)
    parser.add_argument("--interior-points", type=int, default=512)
    parser.add_argument("--boundary-points", type=int, default=128)
    parser.add_argument("--initial-points", type=int, default=128)
    parser.add_argument("--candidate-pool-multiplier", type=int, default=4)
    parser.add_argument("--refresh-updates", type=int, default=250)
    parser.add_argument("--log-every", type=int, default=25)
    parser.add_argument("--checkpoint-every", type=int, default=1000)
    parser.add_argument("--device", default="cpu")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    config = PhkTrainingConfig(
        arm=args.arm,
        case_control=args.case_control,
        updates=args.updates,
        seed=args.seed,
        hidden_width=args.hidden_width,
        hidden_layers=args.hidden_layers,
        frequency_band=args.frequency_band,
        learning_rate=args.learning_rate,
        interior_points=args.interior_points,
        boundary_points=args.boundary_points,
        initial_points=args.initial_points,
        candidate_pool_multiplier=args.candidate_pool_multiplier,
        refresh_updates=args.refresh_updates,
        log_every=args.log_every,
        checkpoint_every=args.checkpoint_every,
        device=args.device,
    )
    outcome = train(config, run_directory=args.run_directory)
    print(
        json.dumps(
            {
                "status": outcome.status,
                "run_directory": str(outcome.run_directory),
                "final_loss": outcome.final_loss,
                "minimum_loss": outcome.minimum_loss,
                "wall_seconds": outcome.wall_seconds,
                "seconds_per_update": outcome.seconds_per_update,
                "peak_gpu_memory_bytes": outcome.peak_gpu_memory_bytes,
                "checkpoint": str(outcome.checkpoint_path),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "BOUNDARY_SCALES",
    "INITIAL_SCALES",
    "METHOD_CONTRACT_PATH",
    "PDE_SCALES",
    "PhkTrainingConfig",
    "TrainingModelFactory",
    "TrainingObservation",
    "TrainingObserver",
    "TrainingOutcome",
    "TrainingStepPolicy",
    "TrainingStepSpec",
    "campaign_weighted_loss_groups",
    "canonical_weighted_loss_groups",
    "load_case_physics",
    "main",
    "train",
]
