"""PHK-V2.3 LF2 measure-calibrated feasible PINN pilot.

LF2 has one bounded reference-blind GPU trajectory.  M0 calibrates the exact
LF1 B0 model with a target-measure stratified medium objective.  Conditional
M1 then minimizes the unchanged full physics objective subject to explicit
accuracy and event-feasibility inequalities.  Fine, extra-fine, the frozen
evaluator, and stress carriers are intentionally unreachable from this module.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import random
import time
from typing import Any, Mapping, Sequence

import numpy as np
import torch
import torch.nn.functional as functional

from .phk_v21_benchmark import PhkV21OracleResult, read_phk_v21_result
from .phk_v22r_pinn import (
    POTENTIAL_TRANSFORM_EXACT_TOP_RANGE_PRESERVING,
    PhkV22RModel,
    PhkV22RPhysics,
)
from .phk_v22r_prediction import write_prediction_carrier
from .phk_v22r_training import (
    METHOD_CONTRACT_PATH as V22R_METHOD_CONTRACT_PATH,
    PROGRAM_CONTRACT_PATH as V22R_PROGRAM_CONTRACT_PATH,
    ROOT,
    PhkTrainingConfig,
    _checkpoint_payload,
    load_case_physics,
)
from .phk_v23_lf0 import (
    LF0PhysicsBatchStream,
    _artifact_record,
    _batch_sha256,
    _physical_object,
    _physics_objective,
    _read_json,
    _sha256_path,
    _write_json_exclusive,
    potential_maximum_principle_windowed_guard,
)
from .phk_v23_lf1 import (
    ARM_B as LF1_ARM_B,
    TASK_ID as LF1_TASK_ID,
    build_range_preserving_model,
)


PROGRAM_CONTRACT_PATH = (
    ROOT
    / "configs"
    / "phk_v23"
    / "program_contract_lf2_measure_calibrated_feasible_pinn.json"
)
METHOD_CONTRACT_PATH = (
    ROOT
    / "configs"
    / "phk_v23"
    / "method_contract_lf2_measure_calibrated_feasible_pinn.json"
)
DATA_CONTRACT_PATH = (
    ROOT / "configs" / "phk_v23" / "data_contract_lf2_measure_calibrated_medium.json"
)
DECISION_CONTRACT_PATH = (
    ROOT
    / "configs"
    / "phk_v23"
    / "decision_contract_lf2_measure_calibrated_feasible_pinn.json"
)
CONTRACT_PATHS = {
    "program": PROGRAM_CONTRACT_PATH,
    "method": METHOD_CONTRACT_PATH,
    "data": DATA_CONTRACT_PATH,
    "decision": DECISION_CONTRACT_PATH,
}
EXPECTED_CONTRACT_SCHEMAS = {
    "program": "phk-v23-lf2-program-contract-v1",
    "method": "phk-v23-lf2-method-contract-v1",
    "data": "phk-v23-lf2-data-contract-v1",
    "decision": "phk-v23-lf2-decision-contract-v1",
}
TASK_ID = "PHK_V23_LF2_MEASURE_CALIBRATED_FEASIBLE_PINN_EXECUTE"
TRAJECTORY = "LF2_MEASURE_CALIBRATED_FEASIBLE_PINN"
M0_STAGE = "M0_MEASURE_CALIBRATED_DATA_ONLY"
M1_STAGE = "M1_FEASIBILITY_CONSTRAINED_FULL_PHYSICS"
CATEGORY_NAMES = (
    "EVENT_CYCLE_1",
    "EVENT_CYCLE_2",
    "TRANSITION_CYCLE_1",
    "TRANSITION_CYCLE_2",
    "RECOVERY_CYCLE_1",
    "RECOVERY_CYCLE_2",
    "W1_ROI_REMAINDER",
    "W1_OUTSIDE_REMAINDER",
    "W2_ROI_REMAINDER",
    "W2_OUTSIDE_REMAINDER",
    "W3_ROI_REMAINDER",
    "W3_OUTSIDE_REMAINDER",
    "W4_ROI_REMAINDER",
    "W4_OUTSIDE_REMAINDER",
)
CATEGORY_QUOTAS = (128, 128, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64, 64)
M0_SEEDS = (17101, 17102, 17103, 17104, 17105, 17106, 17017, 17018, 17019, 17020, 17021, 17022, 17023, 17024)
M1_SEEDS = (17401, 17402, 17403, 17404, 17405, 17406, 17407, 17408, 17409, 17410, 17411, 17412, 17413, 17414)
CYCLE_CATEGORY_NAMES = {
    "cycle_1": (
        "EVENT_CYCLE_1",
        "TRANSITION_CYCLE_1",
        "W1_ROI_REMAINDER",
        "W1_OUTSIDE_REMAINDER",
    ),
    "cycle_2": (
        "EVENT_CYCLE_2",
        "TRANSITION_CYCLE_2",
        "W3_ROI_REMAINDER",
        "W3_OUTSIDE_REMAINDER",
    ),
}


def stage_stream_policy(stage: str) -> dict[str, Any]:
    """Return the executable RNG boundary for one frozen LF2 stage."""

    if stage == M0_STAGE:
        return {
            "measure_stream_role": "M0",
            "physics_stream_constructed": False,
            "physics_stream_draws": 0,
        }
    if stage == M1_STAGE:
        return {
            "measure_stream_role": "M1_CONSTRAINT",
            "physics_stream_constructed": True,
            "physics_local_steps": [1, 1200],
        }
    raise ValueError("LF2 stage stream policy is undefined")


def load_contracts() -> dict[str, dict[str, Any]]:
    """Load and fail closed on the four frozen LF2 contracts."""

    contracts = {name: _read_json(path) for name, path in CONTRACT_PATHS.items()}
    for name, schema in EXPECTED_CONTRACT_SCHEMAS.items():
        if contracts[name].get("schema_id") != schema:
            raise ValueError(f"unsupported LF2 {name} contract")
    relative = {
        name: path.relative_to(ROOT).as_posix() for name, path in CONTRACT_PATHS.items()
    }
    program = contracts["program"]
    method = contracts["method"]
    data = contracts["data"]
    decision = contracts["decision"]
    if program.get("phase_id") != TASK_ID:
        raise ValueError("LF2 task identity drift")
    if (
        method.get("program_contract") != relative["program"]
        or data.get("program_contract") != relative["program"]
        or decision.get("program_contract") != relative["program"]
        or decision.get("method_contract") != relative["method"]
        or decision.get("data_contract") != relative["data"]
    ):
        raise ValueError("LF2 cross-contract identity drift")
    authorization = program.get("authorization", {})
    if not all(
        authorization.get(name) is True
        for name in (
            "contract_code_test_document_writes",
            "cpu_partition_qualification",
            "one_gpu_trajectory_after_cpu_gate",
            "local_nominal_evaluation_after_shutdown",
            "selective_commit_and_push_main",
            "seed_17_only",
        )
    ):
        raise PermissionError("LF2 campaign authorization is incomplete")
    if any(
        authorization.get(name) is not False
        for name in (
            "new_seed",
            "phase_latent_teacher_backup",
            "stress_prediction_or_unseal",
            "pjgr_or_r2",
            "benchmark_pde_constitutive_geometry_parameter_reference_roi_threshold_or_evaluator_change",
        )
    ):
        raise PermissionError("LF2 authorization boundary drift")
    limits = program.get("hard_limits", {})
    if (
        limits.get("maximum_scientific_gpu_trajectories") != 1
        or limits.get("maximum_optimizer_updates") != 2400
        or float(limits.get("maximum_v100_wall_hours", math.inf)) != 1.0
        or float(limits.get("maximum_incremental_cost_cny", math.inf)) != 3.0
    ):
        raise ValueError("LF2 run budget drift")
    identity = method.get("common_identity", {})
    if (
        identity.get("gpu") != "TESLA_V100_PCIE_32GB_ONLY"
        or identity.get("dtype") != "FLOAT64"
        or identity.get("seed") != 17
        or identity.get("potential_transform")
        != POTENTIAL_TRANSFORM_EXACT_TOP_RANGE_PRESERVING
    ):
        raise ValueError("LF2 model or device identity drift")
    trajectory = method.get("trajectory", {})
    if (
        trajectory.get("M0", {}).get("updates") != 1200
        or trajectory.get("M1", {}).get("updates") != 1200
        or trajectory.get("maximum_global_updates") != 2400
    ):
        raise ValueError("LF2 stage budget drift")
    proposal = data.get("proposal_per_step", {})
    if (
        tuple(proposal.get("category_quotas_in_partition_order", ())) != CATEGORY_QUOTAS
        or tuple(proposal.get("M0_sobol_seeds_in_partition_order", ())) != M0_SEEDS
        or tuple(proposal.get("M1_constraint_sobol_seeds_in_partition_order", ()))
        != M1_SEEDS
        or proposal.get("total") != sum(CATEGORY_QUOTAS)
    ):
        raise ValueError("LF2 proposal identity drift")
    if tuple(data.get("partition", {}).get("priority_order", ())) != CATEGORY_NAMES:
        raise ValueError("LF2 partition priority drift")
    source = data.get("training_source", {})
    parent = data.get("initial_checkpoint", {})
    if (
        source.get("resolution") != "medium"
        or source.get("only_gpu_training_label_source") is not True
        or parent.get("load_model_weights") is not True
        or parent.get("load_optimizer_state") is not False
    ):
        raise PermissionError("LF2 data identity drift")
    if decision.get("stress_status") != "TWO_STRESS_REFERENCES_SEALED_UNREAD":
        raise PermissionError("LF2 stress boundary drift")
    expected_outcomes = {
        "LF2_ENGINEERING_BLOCKED",
        "LF2_CPU_OR_PARTITION_BLOCKED",
        "LF2_NUMERICAL_OR_IDENTITY_INVALID",
        "LF2_CALIBRATED_CARRIER_NOT_ESTABLISHED",
        "LF2_FEASIBILITY_PRESERVATION_FAILED",
        "LF2_NO_PINN_SPECIFIC_GAIN",
        "LF2_MEASURE_CALIBRATED_FEASIBLE_PINN_PROVISIONAL_SIGNAL",
    }
    if set(decision.get("machine_outcomes_and_unique_next", {})) != expected_outcomes:
        raise ValueError("LF2 machine outcome mapping is not exhaustive")
    return contracts


def contract_identity() -> dict[str, dict[str, str]]:
    return {
        name: {"path": path.relative_to(ROOT).as_posix(), "sha256": _sha256_path(path)}
        for name, path in CONTRACT_PATHS.items()
    }


def build_training_config(device_name: str) -> PhkTrainingConfig:
    config = PhkTrainingConfig(
        arm="STRONG_RAW",
        case_control="FULL",
        updates=2400,
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
        log_every=50,
        checkpoint_every=2400,
        pde_weight=1.0,
        boundary_weight=5.0,
        initial_weight=1.0,
        dtype="float64",
        device=device_name,
    )
    config.validate()
    return config


def trapezoid_node_weights(time_axis: np.ndarray) -> np.ndarray:
    """Return normalized one-dimensional trapezoid weights."""

    time = np.asarray(time_axis, dtype=np.float64).reshape(-1)
    if time.size < 2 or not np.isfinite(time).all() or np.any(np.diff(time) <= 0.0):
        raise ValueError("LF2 time axis is invalid")
    delta = np.diff(time)
    weights = np.empty_like(time)
    weights[0] = 0.5 * delta[0]
    weights[-1] = 0.5 * delta[-1]
    weights[1:-1] = 0.5 * (delta[:-1] + delta[1:])
    return weights / np.sum(weights)


def _weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    exact_values = np.asarray(values, dtype=np.float64).reshape(-1)
    exact_weights = np.asarray(weights, dtype=np.float64).reshape(-1)
    if exact_values.shape != exact_weights.shape or exact_values.size == 0:
        raise ValueError("LF2 weighted mean inputs do not align")
    total = float(np.sum(exact_weights))
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("LF2 weighted mean has no positive mass")
    return float(np.sum(exact_values * exact_weights) / total)


class MediumMeasureDataset:
    """Medium saved nodes partitioned into fourteen target-measure categories."""

    def __init__(self, result: PhkV21OracleResult, *, physics: PhkV22RPhysics) -> None:
        self.physics = physics
        self.result = result
        self.time = np.asarray(result.time, dtype=np.float64).reshape(-1)
        self.cell_x = np.asarray(result.grid.cell_x, dtype=np.float64).reshape(-1)
        self.cell_z = np.asarray(result.grid.cell_z, dtype=np.float64).reshape(-1)
        self.cell_volumes = np.asarray(
            result.grid.cell_volumes, dtype=np.float64
        ).reshape(-1)
        self.cell_count = self.cell_x.size
        expected = (self.time.size, self.cell_count)
        self.fields = {
            name: np.asarray(getattr(result, name), dtype=np.float64).reshape(expected)
            for name in ("potential", "temperature", "phase")
        }
        if any(not values.size or not np.isfinite(values).all() for values in self.fields.values()):
            raise ValueError("LF2 medium carrier contains invalid fields")
        if (
            self.cell_z.size != self.cell_count
            or self.cell_volumes.size != self.cell_count
            or not np.isfinite(self.cell_volumes).all()
            or np.any(self.cell_volumes <= 0.0)
        ):
            raise ValueError("LF2 medium spatial measure is invalid")

        time_weights = trapezoid_node_weights(self.time)
        spatial_weights = self.cell_volumes / np.sum(self.cell_volumes)
        self.node_weights = (time_weights[:, None] * spatial_weights[None, :]).reshape(-1)
        self.coordinates = np.column_stack(
            (
                np.tile(self.cell_x, self.time.size),
                np.tile(self.cell_z, self.time.size),
                np.repeat(self.time, self.cell_count),
            )
        )
        self.targets = np.column_stack(
            tuple(self.fields[name].reshape(-1) for name in ("potential", "temperature", "phase"))
        )
        self.roi_cells = (
            (np.abs(self.cell_x) <= 0.55) & (self.cell_z >= 0.0) & (self.cell_z <= 0.55)
        )
        if not np.any(self.roi_cells) or np.all(self.roi_cells):
            raise ValueError("LF2 ROI identity is invalid")
        self.window_time_masks = {
            "W1": (self.time >= 0.0) & (self.time <= 0.35),
            "W2": (self.time > 0.35) & (self.time < 1.25),
            "W3": (self.time >= 1.25) & (self.time <= 1.60),
            "W4": (self.time > 1.60) & (self.time <= 2.50),
        }
        covered_time = np.zeros(self.time.shape, dtype=bool)
        for mask in self.window_time_masks.values():
            if np.any(covered_time & mask):
                raise ValueError("LF2 background windows overlap on saved nodes")
            covered_time |= mask
        if not np.all(covered_time):
            raise ValueError("LF2 background windows do not cover the saved time axis")

        phase = self.fields["phase"]
        derivative = np.gradient(phase, self.time, axis=0, edge_order=1)
        roi_weights = self.cell_volumes[self.roi_cells]
        roi_mean = np.average(phase[:, self.roi_cells], axis=1, weights=roi_weights)
        first_peak = float(
            self.time[np.argmax(np.where(self.time <= 1.25, roi_mean, -np.inf))]
        )
        second_peak = float(
            self.time[np.argmax(np.where(self.time >= 1.25, roi_mean, -np.inf))]
        )
        initial = phase[0:1]
        w1 = self.window_time_masks["W1"][:, None]
        w2 = self.window_time_masks["W2"][:, None]
        w3 = self.window_time_masks["W3"][:, None]
        w4 = self.window_time_masks["W4"][:, None]
        tt = self.time[:, None]
        masks: dict[str, np.ndarray] = {
            "EVENT_CYCLE_1": w1 & (phase >= 0.5),
            "EVENT_CYCLE_2": w3 & (phase >= 0.5),
            "TRANSITION_CYCLE_1": w1 & (phase < 0.5) & (derivative > 0.0),
            "TRANSITION_CYCLE_2": w3 & (phase < 0.5) & (derivative > 0.0),
            "RECOVERY_CYCLE_1": w2 & (tt > first_peak) & (derivative < 0.0) & (phase > initial),
            "RECOVERY_CYCLE_2": w4 & (tt > second_peak) & (derivative < 0.0) & (phase > initial),
        }
        for window in ("W1", "W2", "W3", "W4"):
            window_mask = np.broadcast_to(
                self.window_time_masks[window][:, None], expected
            )
            roi_mask = np.broadcast_to(self.roi_cells[None, :], expected)
            masks[f"{window}_ROI_REMAINDER"] = window_mask & roi_mask
            masks[f"{window}_OUTSIDE_REMAINDER"] = window_mask & ~roi_mask

        assignment = np.full(expected, -1, dtype=np.int16)
        for category_index, name in enumerate(CATEGORY_NAMES):
            available = masks[name] & (assignment < 0)
            assignment[available] = category_index
        if np.any(assignment < 0):
            raise ValueError("LF2 fourteen-category partition is not exhaustive")
        self.assignment = assignment.reshape(-1)
        self.category_indices: dict[str, np.ndarray] = {}
        self.category_counts: dict[str, int] = {}
        self.category_masses: dict[str, float] = {}
        self.category_cdf: dict[str, torch.Tensor] = {}
        for index, name in enumerate(CATEGORY_NAMES):
            indices = np.flatnonzero(self.assignment == index)
            if indices.size == 0:
                raise ValueError(f"LF2 required category is empty: {name}")
            weights = self.node_weights[indices]
            mass = float(np.sum(weights))
            probabilities = weights / mass
            cdf = np.cumsum(probabilities)
            cdf[-1] = 1.0
            self.category_indices[name] = indices
            self.category_counts[name] = int(indices.size)
            self.category_masses[name] = mass
            self.category_cdf[name] = torch.as_tensor(cdf, dtype=torch.float64)
        if not math.isclose(sum(self.category_masses.values()), 1.0, rel_tol=0.0, abs_tol=1.0e-14):
            raise ValueError("LF2 category masses do not sum to the target measure")
        digest = hashlib.sha256(b"PHK_V23_LF2_TARGET_MEASURE_PARTITION")
        digest.update(self.assignment.tobytes(order="C"))
        digest.update(self.node_weights.astype("<f8", copy=False).tobytes(order="C"))
        digest.update("\n".join(CATEGORY_NAMES).encode("ascii"))
        self.partition_sha256 = digest.hexdigest().upper()

    @property
    def node_count(self) -> int:
        return int(self.coordinates.shape[0])

    def category_sample(self, name: str, unit: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        if name not in self.category_indices:
            raise KeyError(name)
        values = unit.detach().to(device="cpu", dtype=torch.float64).reshape(-1)
        selected = torch.searchsorted(self.category_cdf[name], values, right=True)
        selected = selected.clamp_max(self.category_counts[name] - 1).numpy()
        indices = self.category_indices[name][selected]
        return (
            torch.as_tensor(self.coordinates[indices], dtype=torch.float64),
            torch.as_tensor(self.targets[indices], dtype=torch.float64),
        )


@dataclass(frozen=True)
class MeasureBatch:
    coordinates: torch.Tensor
    targets: torch.Tensor
    category_counts: Mapping[str, int]
    category_masses: Mapping[str, float]
    batch_sha256: str


class MeasureCalibratedBatchStream:
    """Strict stateful Sobol proposal over the frozen fourteen categories."""

    def __init__(self, dataset: MediumMeasureDataset, *, role: str) -> None:
        if role not in {"M0", "M1_CONSTRAINT"}:
            raise ValueError("LF2 measure stream role is invalid")
        self.dataset = dataset
        self.role = role
        seeds = M0_SEEDS if role == "M0" else M1_SEEDS
        self.engines = tuple(
            torch.quasirandom.SobolEngine(1, scramble=True, seed=seed) for seed in seeds
        )
        self.draw_count = 0
        self._rolling = hashlib.sha256(
            f"PHK_V23_LF2_{role}_MEASURE_BATCHES".encode("ascii")
        )

    @property
    def rolling_sha256(self) -> str:
        return self._rolling.copy().hexdigest().upper()

    def draw(self, step: int) -> MeasureBatch:
        exact_step = int(step)
        if exact_step != self.draw_count + 1:
            raise ValueError("LF2 measure stream must be consumed in strict step order")
        coordinates: list[torch.Tensor] = []
        targets: list[torch.Tensor] = []
        counts: dict[str, int] = {}
        for name, quota, engine in zip(
            CATEGORY_NAMES, CATEGORY_QUOTAS, self.engines, strict=True
        ):
            unit = engine.draw(quota, dtype=torch.float64).reshape(-1)
            selected_coordinates, selected_targets = self.dataset.category_sample(
                name, unit
            )
            coordinates.append(selected_coordinates)
            targets.append(selected_targets)
            counts[name] = quota
        joined_coordinates = torch.cat(coordinates, dim=0)
        joined_targets = torch.cat(targets, dim=0)
        digest = _batch_sha256(
            joined_coordinates,
            joined_targets,
            metadata=f"LF2:{self.role}:{exact_step}:{self.dataset.partition_sha256}",
        )
        self._rolling.update(bytes.fromhex(digest))
        self.draw_count = exact_step
        return MeasureBatch(
            joined_coordinates,
            joined_targets,
            counts,
            dict(self.dataset.category_masses),
            digest,
        )


def weighted_measure_terms(
    model: PhkV22RModel,
    batch: MeasureBatch,
    *,
    physics: PhkV22RPhysics,
    device: torch.device,
    topology_temperature: float = 0.05,
) -> dict[str, Any]:
    """Return differentiable target-measure field, topology, and event terms."""

    coordinates = batch.coordinates.to(device=device, dtype=torch.float64)
    target = batch.targets.to(device=device, dtype=torch.float64)
    prediction = model(coordinates)
    scales = prediction.new_tensor(
        [physics.waveform_amplitude, physics.theta_transition, 0.5]
    )
    squared = ((prediction - target) / scales).square()
    topology_target = (target[:, 2:3] >= 0.5).to(dtype=prediction.dtype)
    topology_logits = (prediction[:, 2:3] - 0.5) / float(topology_temperature)
    topology_pointwise = functional.binary_cross_entropy_with_logits(
        topology_logits, topology_target, reduction="none"
    ).reshape(-1)
    soft = torch.sigmoid(topology_logits).reshape(-1)
    components = torch.zeros(3, dtype=prediction.dtype, device=device)
    topology = torch.zeros((), dtype=prediction.dtype, device=device)
    category_soft_means: dict[str, torch.Tensor] = {}
    offset = 0
    for name in CATEGORY_NAMES:
        count = int(batch.category_counts[name])
        stop = offset + count
        mass = float(batch.category_masses[name])
        components = components + mass * torch.mean(squared[offset:stop], dim=0)
        topology = topology + mass * torch.mean(topology_pointwise[offset:stop])
        category_soft_means[name] = torch.mean(soft[offset:stop])
        offset = stop
    if offset != prediction.shape[0]:
        raise ValueError("LF2 batch category slices do not cover predictions")
    return {
        "field_components": components,
        "field": torch.mean(components),
        "topology": topology,
        "category_soft_means": category_soft_means,
    }


def m0_constraint_tensors(
    terms: Mapping[str, Any], dataset: MediumMeasureDataset
) -> dict[str, torch.Tensor]:
    means = terms["category_soft_means"]
    constraints: dict[str, torch.Tensor] = {}
    for cycle, event_name in (
        ("cycle_1", "EVENT_CYCLE_1"),
        ("cycle_2", "EVENT_CYCLE_2"),
    ):
        recall = means[event_name]
        active_mass = sum(
            float(dataset.category_masses[name]) * means[name]
            for name in CYCLE_CATEGORY_NAMES[cycle]
        )
        teacher_mass = float(dataset.category_masses[event_name])
        ratio = active_mass / teacher_mass
        constraints[f"{cycle}:recall_lower"] = 0.90 - recall
        constraints[f"{cycle}:mass_lower"] = 0.80 - ratio
        constraints[f"{cycle}:mass_upper"] = ratio - 1.20
    return constraints


def m1_constraint_tensors(
    terms: Mapping[str, Any],
    dataset: MediumMeasureDataset,
    *,
    m0_audit: Mapping[str, Any],
    denominator_floor: float = 1.0e-12,
) -> dict[str, torch.Tensor]:
    components = terms["field_components"]
    baseline = m0_audit["weighted_errors"]
    constraints = {
        "potential_error_upper": components[0]
        / max(float(baseline["potential"]), denominator_floor)
        - 1.20,
        "temperature_error_upper": components[1]
        / max(float(baseline["temperature"]), denominator_floor)
        - 1.05,
        "phase_error_upper": components[2]
        / max(float(baseline["phase"]), denominator_floor)
        - 1.05,
        "topology_error_upper": terms["topology"]
        / max(float(m0_audit["topology_weighted_loss"]), denominator_floor)
        - 1.05,
    }
    constraints.update(m0_constraint_tensors(terms, dataset))
    return constraints


def augmented_lagrangian_inequality(
    g: torch.Tensor, multiplier: float, *, rho: float = 1.0
) -> torch.Tensor:
    if rho <= 0.0 or not math.isfinite(rho) or multiplier < 0.0 or not math.isfinite(multiplier):
        raise ValueError("LF2 augmented-Lagrangian state is invalid")
    shifted = float(multiplier) + float(rho) * g
    return (
        torch.clamp(shifted, min=0.0).square() - float(multiplier) ** 2
    ) / (2.0 * float(rho))


def augmented_lagrangian_sum(
    constraints: Mapping[str, torch.Tensor],
    multipliers: Mapping[str, float],
    *,
    rho: float = 1.0,
) -> torch.Tensor:
    if set(constraints) != set(multipliers) or not constraints:
        raise ValueError("LF2 augmented-Lagrangian keys do not align")
    return sum(
        augmented_lagrangian_inequality(
            constraints[name], float(multipliers[name]), rho=rho
        )
        for name in constraints
    )


def update_multipliers(
    constraints: Mapping[str, torch.Tensor],
    multipliers: Mapping[str, float],
    *,
    rho: float = 1.0,
) -> dict[str, float]:
    return {
        name: max(
            0.0,
            float(multipliers[name]) + float(rho) * float(value.detach().cpu()),
        )
        for name, value in constraints.items()
    }


def _event_time(
    phase: np.ndarray,
    *,
    dataset: MediumMeasureDataset,
    cycle_index: int,
) -> float | None:
    roi_fraction = np.mean(phase[:, dataset.roi_cells] >= 0.5, axis=1)
    period = float(dataset.result.case.period)
    start = cycle_index * period
    end = (cycle_index + 1) * period
    mask = (dataset.time >= start) & (
        dataset.time <= end if cycle_index == 1 else dataset.time < end
    )
    indices = np.flatnonzero(mask)
    threshold = 0.02
    for before, after in zip(indices[:-1], indices[1:], strict=True):
        low = float(roi_fraction[before])
        high = float(roi_fraction[after])
        if low < threshold <= high and high > low:
            fraction = (threshold - low) / (high - low)
            return float(
                dataset.time[before]
                + fraction * (dataset.time[after] - dataset.time[before])
            )
    return None


def _predict_medium(
    model: PhkV22RModel,
    dataset: MediumMeasureDataset,
    *,
    device: torch.device,
    chunk_points: int = 65536,
) -> np.ndarray:
    output = np.empty((dataset.node_count, 3), dtype=np.float64)
    was_training = model.training
    model.eval()
    with torch.no_grad():
        for start in range(0, dataset.node_count, chunk_points):
            stop = min(start + chunk_points, dataset.node_count)
            output[start:stop] = (
                model(
                    torch.as_tensor(
                        dataset.coordinates[start:stop],
                        dtype=torch.float64,
                        device=device,
                    )
                )
                .detach()
                .cpu()
                .numpy()
            )
    model.train(was_training)
    return output


def full_medium_audit(
    model: PhkV22RModel,
    dataset: MediumMeasureDataset,
    *,
    device: torch.device,
    absolute_tolerance: float = 1.0e-6,
) -> dict[str, Any]:
    prediction = _predict_medium(model, dataset, device=device)
    finite = bool(np.isfinite(prediction).all())
    scales = np.asarray(
        [dataset.physics.waveform_amplitude, dataset.physics.theta_transition, 0.5],
        dtype=np.float64,
    )
    squared = ((prediction - dataset.targets) / scales) ** 2
    weighted_errors = {
        name: float(np.sum(dataset.node_weights * squared[:, index]))
        for index, name in enumerate(("potential", "temperature", "phase"))
    }
    logits = (prediction[:, 2] - 0.5) / 0.05
    topology_target = (dataset.targets[:, 2] >= 0.5).astype(np.float64)
    topology_pointwise = np.logaddexp(0.0, logits) - topology_target * logits
    topology = float(np.sum(dataset.node_weights * topology_pointwise))
    shape = (dataset.time.size, dataset.cell_count)
    potential = prediction[:, 0].reshape(shape)
    phase = prediction[:, 2].reshape(shape)
    waveform = (
        dataset.physics.waveform(
            torch.as_tensor(dataset.time, dtype=torch.float64).reshape(-1, 1)
        )
        .detach()
        .cpu()
        .numpy()
        .reshape(-1)
    )
    potential_guard = potential_maximum_principle_windowed_guard(
        potential,
        dataset.time,
        waveform,
        absolute_tolerance=absolute_tolerance,
    )
    event_metrics: dict[str, Any] = {}
    for cycle, window, event_name, cycle_index in (
        ("cycle_1", "W1", "EVENT_CYCLE_1", 0),
        ("cycle_2", "W3", "EVENT_CYCLE_2", 1),
    ):
        window_nodes = np.broadcast_to(
            dataset.window_time_masks[window][:, None], shape
        ).reshape(-1)
        teacher_active = dataset.assignment == CATEGORY_NAMES.index(event_name)
        predicted_active = prediction[:, 2] >= 0.5
        true_positive = teacher_active & predicted_active
        teacher_mass = float(np.sum(dataset.node_weights[teacher_active]))
        predicted_mass = float(
            np.sum(dataset.node_weights[window_nodes & predicted_active])
        )
        true_positive_mass = float(np.sum(dataset.node_weights[true_positive]))
        teacher_time = _event_time(
            dataset.fields["phase"], dataset=dataset, cycle_index=cycle_index
        )
        predicted_time = _event_time(
            phase, dataset=dataset, cycle_index=cycle_index
        )
        event_metrics[cycle] = {
            "teacher_active_target_mass": teacher_mass,
            "predicted_active_target_mass": predicted_mass,
            "true_positive_target_mass": true_positive_mass,
            "hard_recall": true_positive_mass / teacher_mass if teacher_mass else None,
            "hard_precision": true_positive_mass / predicted_mass if predicted_mass else None,
            "hard_active_mass_ratio": predicted_mass / teacher_mass if teacher_mass else None,
            "teacher_event_time": teacher_time,
            "predicted_event_time": predicted_time,
            "event_time_absolute_error": (
                abs(predicted_time - teacher_time)
                if predicted_time is not None and teacher_time is not None
                else None
            ),
        }
    return {
        "all_values_finite": finite,
        "weighted_errors": weighted_errors,
        "topology_weighted_loss": topology,
        "phase_maximum": float(np.max(prediction[:, 2])) if finite else None,
        "temperature_maximum": float(np.max(prediction[:, 1])) if finite else None,
        "potential_maximum_principle": potential_guard,
        "event_metrics": event_metrics,
        "two_cycle_events": all(
            value["predicted_event_time"] is not None for value in event_metrics.values()
        ),
        "target_measure_identity": "TRAPEZOID_TIME_TIMES_CELL_VOLUME",
        "partition_sha256": dataset.partition_sha256,
    }


def m0_full_medium_gate(
    audit: Mapping[str, Any],
    baseline: Mapping[str, Any],
    *,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    gate = contract["M0_full_medium_gate"]
    checks: dict[str, bool] = {
        "all_values_finite": audit.get("all_values_finite") is True,
        "potential_guard_pass": audit.get("potential_maximum_principle", {}).get("passed") is True,
        "phase_maximum": float(audit.get("phase_maximum", -math.inf))
        >= float(gate["phase_maximum_minimum"]),
        "two_cycle_events": audit.get("two_cycle_events") is True,
    }
    for cycle in ("cycle_1", "cycle_2"):
        metrics = audit["event_metrics"][cycle]
        checks[f"{cycle}:hard_recall"] = (
            metrics["hard_recall"] is not None
            and float(metrics["hard_recall"])
            >= float(gate["hard_recall_each_cycle_minimum"])
        )
        checks[f"{cycle}:hard_precision"] = (
            metrics["hard_precision"] is not None
            and float(metrics["hard_precision"])
            >= float(gate["hard_precision_each_cycle_minimum"])
        )
        checks[f"{cycle}:hard_active_mass_ratio"] = (
            metrics["hard_active_mass_ratio"] is not None
            and float(gate["hard_active_mass_ratio_each_cycle_minimum"])
            <= float(metrics["hard_active_mass_ratio"])
            <= float(gate["hard_active_mass_ratio_each_cycle_maximum"])
        )
        checks[f"{cycle}:event_time"] = (
            metrics["event_time_absolute_error"] is not None
            and float(metrics["event_time_absolute_error"])
            <= float(gate["event_time_absolute_error_each_cycle_maximum"])
        )
    ratios: dict[str, float] = {}
    for field, maximum_key in (
        ("potential", "potential_weighted_mse_to_lf1_b0_maximum_ratio"),
        ("temperature", "temperature_weighted_mse_to_lf1_b0_maximum_ratio"),
        ("phase", "phase_weighted_mse_to_lf1_b0_maximum_ratio"),
    ):
        denominator = max(float(baseline["weighted_errors"][field]), 1.0e-12)
        ratio = float(audit["weighted_errors"][field]) / denominator
        ratios[field] = ratio
        checks[f"{field}_weighted_mse"] = ratio <= float(gate[maximum_key])
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "weighted_mse_ratios_to_lf1_b0": ratios,
        "failure_outcome": None
        if all(checks.values())
        else "LF2_CALIBRATED_CARRIER_NOT_ESTABLISHED",
    }


def m1_full_medium_feasibility_gate(
    audit: Mapping[str, Any],
    m0_audit: Mapping[str, Any],
    *,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    limits = contract["M1_feasibility_constraints_relative_to_M0"]
    floor = float(limits["denominator_floor"])
    ratios = {
        field: float(audit["weighted_errors"][field])
        / max(float(m0_audit["weighted_errors"][field]), floor)
        for field in ("potential", "temperature", "phase")
    }
    ratios["topology"] = float(audit["topology_weighted_loss"]) / max(
        float(m0_audit["topology_weighted_loss"]), floor
    )
    checks: dict[str, bool] = {
        "all_values_finite": audit.get("all_values_finite") is True,
        "potential_guard_pass": audit.get("potential_maximum_principle", {}).get("passed") is True,
        "potential_error_ratio": ratios["potential"]
        <= float(limits["potential_weighted_mse_maximum_ratio"]),
        "temperature_error_ratio": ratios["temperature"]
        <= float(limits["temperature_weighted_mse_maximum_ratio"]),
        "phase_error_ratio": ratios["phase"]
        <= float(limits["phase_weighted_mse_maximum_ratio"]),
        "topology_error_ratio": ratios["topology"]
        <= float(limits["topology_weighted_loss_maximum_ratio"]),
    }
    for cycle in ("cycle_1", "cycle_2"):
        metrics = audit["event_metrics"][cycle]
        checks[f"{cycle}:hard_recall"] = (
            metrics["hard_recall"] is not None
            and float(metrics["hard_recall"])
            >= float(limits["hard_recall_each_cycle_minimum"])
        )
        checks[f"{cycle}:hard_active_mass_ratio"] = (
            metrics["hard_active_mass_ratio"] is not None
            and float(limits["hard_active_mass_ratio_each_cycle_minimum"])
            <= float(metrics["hard_active_mass_ratio"])
            <= float(limits["hard_active_mass_ratio_each_cycle_maximum"])
        )
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "error_ratios_to_M0": ratios,
        "failure_outcome": None
        if all(checks.values())
        else "LF2_FEASIBILITY_PRESERVATION_FAILED",
    }


def _binding_path(binding: Mapping[str, Any], *, label: str) -> Path:
    relative = binding.get("path")
    expected_hash = binding.get("sha256")
    if not isinstance(relative, str) or not isinstance(expected_hash, str):
        raise ValueError(f"LF2 binding is malformed: {label}")
    exact = (ROOT / Path(relative.replace("/", os.sep))).resolve()
    try:
        exact.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PermissionError(f"LF2 binding escaped the repository: {label}") from exc
    if not exact.is_file() or _sha256_path(exact) != expected_hash.upper():
        raise ValueError(f"LF2 binding is absent or drifted: {label}")
    return exact


def load_medium_dataset(
    path: Path,
    *,
    physics: PhkV22RPhysics,
    contracts: Mapping[str, Mapping[str, Any]],
) -> MediumMeasureDataset:
    binding = contracts["data"]["training_source"]
    expected = _binding_path(binding, label="medium training source")
    supplied = Path(path).resolve()
    if supplied != expected:
        raise PermissionError("only the exact LF2 medium carrier is allowed")
    result = read_phk_v21_result(supplied, physical=_physical_object())
    return MediumMeasureDataset(result, physics=physics)


def load_lf1_b0_initialization(
    path: Path,
    *,
    physics: PhkV22RPhysics,
    config: PhkTrainingConfig,
    contracts: Mapping[str, Mapping[str, Any]],
    device: torch.device,
) -> tuple[PhkV22RModel, dict[str, Any]]:
    binding = contracts["data"]["initial_checkpoint"]
    expected = _binding_path(binding, label="LF1 B0 initialization checkpoint")
    supplied = Path(path).resolve()
    if supplied != expected:
        raise PermissionError("only the exact frozen LF1 B0 checkpoint is allowed")
    checkpoint = torch.load(supplied, map_location=device, weights_only=False)
    metadata = checkpoint.get("lf1", {})
    if (
        checkpoint.get("schema_id") != "phk-v22r-checkpoint-v1-1"
        or metadata.get("task_id") != LF1_TASK_ID
        or metadata.get("run_arm") != LF1_ARM_B
        or metadata.get("stage") != "B0_EVENT_DATA_ONLY"
        or metadata.get("global_optimizer_step") != 1200
        or metadata.get("potential_transform")
        != POTENTIAL_TRANSFORM_EXACT_TOP_RANGE_PRESERVING
        or metadata.get("medium_training_labels_used") is not True
        or metadata.get("stress_fields_or_metrics_read") is not False
    ):
        raise PermissionError("LF2 initialization is not the exact LF1 B0 scientific role")
    model = build_range_preserving_model(physics=physics, config=config).to(
        device=device, dtype=torch.float64
    )
    if checkpoint.get("architecture") != model.architecture_manifest():
        raise ValueError("LF2 initialization architecture drift")
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.train()
    return model, checkpoint


def read_cpu_qualification(path: Path) -> dict[str, Any]:
    payload = _read_json(Path(path))
    if (
        payload.get("schema_id") != "phk-v23-lf2-cpu-qualification-v1"
        or payload.get("task_id") != TASK_ID
        or payload.get("status") != "LF2_CPU_QUALIFICATION_PASS"
        or payload.get("gpu_execution_authorized_by_cpu_gate") is not True
        or payload.get("contracts") != contract_identity()
        or payload.get("fine_extra_fine_reference_read") is not False
        or payload.get("stress_fields_or_metrics_read") is not False
    ):
        raise PermissionError("LF2 CPU qualification is absent, stale, or did not pass")
    return payload


def _write_checkpoint(
    *,
    path: Path,
    model: PhkV22RModel,
    optimizer: torch.optim.Optimizer,
    config: PhkTrainingConfig,
    global_step: int,
    stage: str,
    physics_program_sha256: str,
    physics_object_sha256: str,
    source_identity: str,
    contracts: Mapping[str, Mapping[str, str]],
    parent_checkpoint_sha256: str,
    m0_audit: Mapping[str, Any] | None,
) -> Path:
    payload = _checkpoint_payload(
        model=model,
        optimizer=optimizer,
        config=config,
        update=global_step,
        program_contract_sha256=_sha256_path(V22R_PROGRAM_CONTRACT_PATH),
        method_contract_sha256=_sha256_path(V22R_METHOD_CONTRACT_PATH),
        physical_program_sha256=physics_program_sha256,
        physical_object_sha256=physics_object_sha256,
    )
    payload["lf2"] = {
        "schema_id": "phk-v23-lf2-checkpoint-metadata-v1",
        "task_id": TASK_ID,
        "trajectory": TRAJECTORY,
        "stage": stage,
        "global_optimizer_step": int(global_step),
        "source_identity": source_identity,
        "contracts": dict(contracts),
        "parent_checkpoint_sha256": parent_checkpoint_sha256,
        "potential_transform": POTENTIAL_TRANSFORM_EXACT_TOP_RANGE_PRESERVING,
        "medium_training_labels_used": True,
        "nominal_evaluation_reference_read": False,
        "prediction_reference_free": True,
        "stress_fields_or_metrics_read": False,
        "m0_full_medium_audit": dict(m0_audit) if m0_audit is not None else None,
    }
    exact = Path(path)
    exact.parent.mkdir(parents=True, exist_ok=True)
    with exact.open("xb") as handle:
        torch.save(payload, handle)
    return exact


def _append_json_line(handle: Any, payload: Mapping[str, Any]) -> None:
    handle.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n")
    handle.flush()


def _tensor_scalars(terms: Mapping[str, Any]) -> dict[str, float]:
    components = terms["field_components"]
    return {
        "field": float(terms["field"].detach().cpu()),
        "potential": float(components[0].detach().cpu()),
        "temperature": float(components[1].detach().cpu()),
        "phase": float(components[2].detach().cpu()),
        "topology": float(terms["topology"].detach().cpu()),
    }


def _constraint_scalars(
    constraints: Mapping[str, torch.Tensor]
) -> dict[str, float]:
    return {name: float(value.detach().cpu()) for name, value in constraints.items()}


def execute_reference_blind_gpu_trajectory(
    *,
    output_root: Path,
    medium_carrier: Path,
    initial_checkpoint: Path,
    cpu_qualification_path: Path,
    device_name: str,
    source_identity: str,
    hourly_price_cny: float,
) -> dict[str, Any]:
    """Execute the sole frozen LF2 M0 -> conditional M1 trajectory."""

    contracts = load_contracts()
    identities = contract_identity()
    qualification = read_cpu_qualification(cpu_qualification_path)
    if not device_name.startswith("cuda") or not torch.cuda.is_available():
        raise RuntimeError("LF2 scientific execution requires CUDA")
    device = torch.device(device_name)
    gpu_name = torch.cuda.get_device_name(device)
    if gpu_name != "Tesla V100-PCIE-32GB":
        raise RuntimeError("LF2 requires the exact Tesla V100-PCIE-32GB")
    price = float(hourly_price_cny)
    limits = contracts["program"]["hard_limits"]
    if not math.isfinite(price) or price <= 0.0:
        raise ValueError("LF2 live hourly price must be positive and finite")
    if price * float(limits["maximum_v100_wall_hours"]) > float(
        limits["maximum_incremental_cost_cny"]
    ):
        raise RuntimeError("LF2 projected cost exceeds the frozen hard cap")

    output = Path(output_root).resolve()
    output.mkdir(parents=True, exist_ok=False)
    config = build_training_config(device_name)
    physics, physical_program_sha256, physical_object_sha256 = load_case_physics(
        config.case_control
    )
    dataset = load_medium_dataset(
        Path(medium_carrier), physics=physics, contracts=contracts
    )
    model, _ = load_lf1_b0_initialization(
        Path(initial_checkpoint),
        physics=physics,
        config=config,
        contracts=contracts,
        device=device,
    )
    if qualification.get("partition", {}).get("partition_sha256") != dataset.partition_sha256:
        raise ValueError("LF2 CPU-qualified partition identity drift")
    baseline = qualification.get("lf1_b0_full_medium_audit")
    if not isinstance(baseline, Mapping):
        raise ValueError("LF2 CPU qualification lacks the LF1 B0 baseline")

    random.seed(config.seed)
    np.random.seed(config.seed)
    torch.manual_seed(config.seed)
    torch.cuda.manual_seed_all(config.seed)
    torch.cuda.reset_peak_memory_stats(device)
    started_at = datetime.now(timezone.utc).isoformat()
    started = time.perf_counter()
    parent_hash = _sha256_path(Path(initial_checkpoint))
    manifest_start = {
        "schema_id": "phk-v23-lf2-run-manifest-v1",
        "task_id": TASK_ID,
        "status": "RUNNING_REFERENCE_BLIND_GPU_TRAJECTORY",
        "started_at_utc": started_at,
        "source_identity": source_identity,
        "contracts": identities,
        "trajectory": TRAJECTORY,
        "training_config": asdict(config),
        "training_config_sha256": config.identity,
        "architecture": model.architecture_manifest(),
        "device": gpu_name,
        "dtype": "FLOAT64",
        "seed": 17,
        "input_bindings": {
            "medium": {
                "path": str(Path(medium_carrier).resolve()),
                "sha256": _sha256_path(Path(medium_carrier)),
                "size_bytes": Path(medium_carrier).stat().st_size,
            },
            "lf1_b0_checkpoint": {
                "path": str(Path(initial_checkpoint).resolve()),
                "sha256": parent_hash,
                "size_bytes": Path(initial_checkpoint).stat().st_size,
            },
            "cpu_qualification": {
                "path": str(Path(cpu_qualification_path).resolve()),
                "sha256": _sha256_path(Path(cpu_qualification_path)),
                "size_bytes": Path(cpu_qualification_path).stat().st_size,
            },
        },
        "medium_training_labels_used": True,
        "fine_extra_fine_or_evaluator_read": False,
        "stress_fields_or_metrics_read": False,
        "manual_early_stop": False,
        "accuracy_checkpoint_selection": False,
    }
    _write_json_exclusive(output / "manifest-start.json", manifest_start)

    log_path = output / "training-log.jsonl"
    data_hash_path = output / "measure-data-batch-hashes.jsonl"
    physics_hash_path = output / "physics-batch-hashes.jsonl"
    audit_log_path = output / "full-medium-audits.jsonl"
    m0_stream_boundary = stage_stream_policy(M0_STAGE)
    if m0_stream_boundary["physics_stream_constructed"] is not False:
        raise RuntimeError("LF2 M0 physics RNG boundary drift")
    m0_stream = MeasureCalibratedBatchStream(
        dataset, role=str(m0_stream_boundary["measure_stream_role"])
    )
    m1_stream: MeasureCalibratedBatchStream | None = None
    physics_stream: LF0PhysicsBatchStream | None = None
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    m0_multipliers = {
        name: 0.0
        for name in (
            "cycle_1:recall_lower",
            "cycle_1:mass_lower",
            "cycle_1:mass_upper",
            "cycle_2:recall_lower",
            "cycle_2:mass_lower",
            "cycle_2:mass_upper",
        )
    }
    m1_multipliers: dict[str, float] | None = None
    executed_updates = 0
    optimizer_instances = 1
    minimum_total = math.inf
    final_scalars: dict[str, float] = {}
    m0_audit: dict[str, Any] | None = None
    final_audit: dict[str, Any] | None = None
    m0_gate: dict[str, Any] | None = None
    feasibility_gate: dict[str, Any] | None = None
    checkpoints: dict[str, Path] = {}
    predictions: dict[str, Path] = {}

    def enforce_budget() -> None:
        elapsed_hours = (time.perf_counter() - started) / 3600.0
        if elapsed_hours > float(limits["maximum_v100_wall_hours"]):
            raise RuntimeError("LF2 V100 wall hard cap exceeded")
        if elapsed_hours * price > float(limits["maximum_incremental_cost_cny"]):
            raise RuntimeError("LF2 incremental cost hard cap exceeded")

    def take_step(total: torch.Tensor) -> tuple[float, float]:
        nonlocal minimum_total
        if not bool(torch.isfinite(total)):
            raise FloatingPointError("LF2 non-finite objective")
        total.backward()
        norm = torch.nn.utils.clip_grad_norm_(
            model.parameters(), config.gradient_clip_norm
        )
        if not bool(torch.isfinite(norm)):
            raise FloatingPointError("LF2 non-finite gradient")
        optimizer.step()
        value = float(total.detach().cpu())
        minimum_total = min(minimum_total, value)
        return value, float(norm.detach().cpu())

    with (
        log_path.open("x", encoding="utf-8", newline="\n") as log_handle,
        data_hash_path.open("x", encoding="utf-8", newline="\n") as data_handle,
        physics_hash_path.open("x", encoding="utf-8", newline="\n") as physics_handle,
        audit_log_path.open("x", encoding="utf-8", newline="\n") as audit_handle,
    ):
        for global_step in range(1, 1201):
            optimizer.zero_grad(set_to_none=True)
            batch = m0_stream.draw(global_step)
            terms = weighted_measure_terms(
                model, batch, physics=physics, device=device
            )
            constraints = m0_constraint_tensors(terms, dataset)
            penalty = augmented_lagrangian_sum(
                constraints, m0_multipliers, rho=1.0
            )
            total = terms["field"] + terms["topology"] + penalty
            total_value, norm = take_step(total)
            m0_multipliers = update_multipliers(
                constraints, m0_multipliers, rho=1.0
            )
            executed_updates = global_step
            final_scalars = {
                **_tensor_scalars(terms),
                "augmented_lagrangian": float(penalty.detach().cpu()),
                "total_loss": total_value,
                "gradient_norm_before_clip": norm,
            }
            _append_json_line(
                data_handle,
                {
                    "global_step": global_step,
                    "stage": M0_STAGE,
                    "data_local_step": global_step,
                    "batch_sha256": batch.batch_sha256,
                    "category_counts": batch.category_counts,
                },
            )
            if global_step == 1 or global_step % 50 == 0 or global_step == 1200:
                _append_json_line(
                    log_handle,
                    {
                        "global_step": global_step,
                        "stage": M0_STAGE,
                        **final_scalars,
                        "constraints": _constraint_scalars(constraints),
                        "multipliers_after_update": m0_multipliers,
                    },
                )
                m0_audit = full_medium_audit(
                    model,
                    dataset,
                    device=device,
                    absolute_tolerance=float(
                        contracts["decision"]["potential_maximum_principle"][
                            "absolute_tolerance"
                        ]
                    ),
                )
                _append_json_line(
                    audit_handle,
                    {"global_step": global_step, "stage": M0_STAGE, **m0_audit},
                )
                enforce_budget()
        assert m0_audit is not None
        checkpoints["m0"] = _write_checkpoint(
            path=output / "checkpoint-m0-step-1200.pt",
            model=model,
            optimizer=optimizer,
            config=config,
            global_step=1200,
            stage=M0_STAGE,
            physics_program_sha256=physical_program_sha256,
            physics_object_sha256=physical_object_sha256,
            source_identity=source_identity,
            contracts=identities,
            parent_checkpoint_sha256=parent_hash,
            m0_audit=m0_audit,
        )
        predictions["m0"] = write_prediction_carrier(
            checkpoint_path=checkpoints["m0"],
            output_path=output / "prediction-m0-step-1200.npz",
            device_name=device_name,
        )
        m0_gate = m0_full_medium_gate(
            m0_audit, baseline, contract=contracts["decision"]
        )
        _write_json_exclusive(output / "m0-full-medium-gate.json", m0_gate)

        m0_numerical_valid = bool(
            m0_audit["all_values_finite"]
            and m0_audit["potential_maximum_principle"]["passed"]
        )
        if m0_numerical_valid and m0_gate["passed"]:
            m1_stream_boundary = stage_stream_policy(M1_STAGE)
            if m1_stream_boundary["physics_stream_constructed"] is not True:
                raise RuntimeError("LF2 M1 physics RNG boundary drift")
            del optimizer
            optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
            optimizer_instances = 2
            m1_stream = MeasureCalibratedBatchStream(
                dataset, role=str(m1_stream_boundary["measure_stream_role"])
            )
            physics_stream = LF0PhysicsBatchStream(
                physics=physics,
                interior_points=config.interior_points,
                boundary_points=config.boundary_points,
                initial_points=config.initial_points,
                refresh_updates=config.refresh_updates,
                seed=config.seed,
            )
            prototype_batch = m1_stream.draw(1)
            optimizer.zero_grad(set_to_none=True)
            prototype_terms = weighted_measure_terms(
                model, prototype_batch, physics=physics, device=device
            )
            prototype_constraints = m1_constraint_tensors(
                prototype_terms, dataset, m0_audit=m0_audit
            )
            m1_multipliers = {name: 0.0 for name in prototype_constraints}
            for local_step in range(1, 1201):
                global_step = 1200 + local_step
                optimizer.zero_grad(set_to_none=True)
                data_batch = (
                    prototype_batch if local_step == 1 else m1_stream.draw(local_step)
                )
                terms = (
                    prototype_terms
                    if local_step == 1
                    else weighted_measure_terms(
                        model, data_batch, physics=physics, device=device
                    )
                )
                constraints = (
                    prototype_constraints
                    if local_step == 1
                    else m1_constraint_tensors(
                        terms, dataset, m0_audit=m0_audit
                    )
                )
                physics_batch = physics_stream.draw(
                    model, local_step, dtype=torch.float64, device=device
                )
                physics_loss, physics_components = _physics_objective(
                    model, physics_batch, config
                )
                assert m1_multipliers is not None
                penalty = augmented_lagrangian_sum(
                    constraints, m1_multipliers, rho=1.0
                )
                total = physics_loss + penalty
                total_value, norm = take_step(total)
                m1_multipliers = update_multipliers(
                    constraints, m1_multipliers, rho=1.0
                )
                executed_updates = global_step
                final_scalars = {
                    **physics_components,
                    **{
                        f"constraint_data:{name}": value
                        for name, value in _tensor_scalars(terms).items()
                    },
                    "augmented_lagrangian": float(penalty.detach().cpu()),
                    "total_loss": total_value,
                    "gradient_norm_before_clip": norm,
                }
                _append_json_line(
                    data_handle,
                    {
                        "global_step": global_step,
                        "stage": M1_STAGE,
                        "data_local_step": local_step,
                        "batch_sha256": data_batch.batch_sha256,
                        "category_counts": data_batch.category_counts,
                    },
                )
                _append_json_line(
                    physics_handle,
                    {
                        "global_step": global_step,
                        "physics_local_step": local_step,
                        "active_windows": physics_batch.active_windows,
                        "refreshed": physics_batch.refreshed,
                        "interior_coordinate_sha256": physics_batch.interior_sha256,
                        "boundary_coordinate_sha256": physics_batch.boundary_sha256,
                        "initial_coordinate_sha256": physics_batch.initial_sha256,
                        "batch_sha256": physics_batch.batch_sha256,
                    },
                )
                if local_step == 1 or local_step % 50 == 0 or local_step == 1200:
                    _append_json_line(
                        log_handle,
                        {
                            "global_step": global_step,
                            "stage": M1_STAGE,
                            **final_scalars,
                            "constraints": _constraint_scalars(constraints),
                            "multipliers_after_update": m1_multipliers,
                        },
                    )
                    final_audit = full_medium_audit(
                        model,
                        dataset,
                        device=device,
                        absolute_tolerance=float(
                            contracts["decision"]["potential_maximum_principle"][
                                "absolute_tolerance"
                            ]
                        ),
                    )
                    _append_json_line(
                        audit_handle,
                        {"global_step": global_step, "stage": M1_STAGE, **final_audit},
                    )
                    enforce_budget()
            assert final_audit is not None
            feasibility_gate = m1_full_medium_feasibility_gate(
                final_audit, m0_audit, contract=contracts["decision"]
            )
            _write_json_exclusive(
                output / "m1-full-medium-feasibility-gate.json", feasibility_gate
            )
            checkpoints["final"] = _write_checkpoint(
                path=output / "checkpoint-final.pt",
                model=model,
                optimizer=optimizer,
                config=config,
                global_step=2400,
                stage=M1_STAGE,
                physics_program_sha256=physical_program_sha256,
                physics_object_sha256=physical_object_sha256,
                source_identity=source_identity,
                contracts=identities,
                parent_checkpoint_sha256=parent_hash,
                m0_audit=m0_audit,
            )
            predictions["final"] = write_prediction_carrier(
                checkpoint_path=checkpoints["final"],
                output_path=output / "prediction-final.npz",
                device_name=device_name,
            )

    if m0_audit is None or m0_gate is None:
        raise RuntimeError("LF2 M0 ended without its frozen audit and gate")
    if not (
        m0_audit["all_values_finite"]
        and m0_audit["potential_maximum_principle"]["passed"]
    ):
        status = "LF2_NUMERICAL_OR_IDENTITY_INVALID"
    elif not m0_gate["passed"]:
        status = "LF2_CALIBRATED_CARRIER_NOT_ESTABLISHED"
    elif final_audit is None or feasibility_gate is None:
        raise RuntimeError("LF2 M1 was required but did not form a final audit")
    elif not (
        final_audit["all_values_finite"]
        and final_audit["potential_maximum_principle"]["passed"]
    ):
        status = "LF2_NUMERICAL_OR_IDENTITY_INVALID"
    elif not feasibility_gate["passed"]:
        status = "LF2_FEASIBILITY_PRESERVATION_FAILED"
    else:
        status = "LF2_REFERENCE_BLIND_GPU_TRAJECTORY_COMPLETE"

    torch.cuda.synchronize(device)
    enforce_budget()
    wall_seconds = time.perf_counter() - started
    environment_path = output / "environment.json"
    _write_json_exclusive(
        environment_path,
        {
            "schema_id": "phk-v23-lf2-environment-v1",
            "gpu_name": gpu_name,
            "torch_version": torch.__version__,
            "torch_cuda_version": torch.version.cuda,
            "numpy_version": np.__version__,
            "python": os.sys.version,
            "medium_and_lf1_b0_inputs_present": True,
            "fine_extra_fine_evaluator_present": False,
            "stress_fields_present": False,
        },
    )
    manifest_final_path = output / "manifest-final.json"
    _write_json_exclusive(
        manifest_final_path,
        {
            **manifest_start,
            "status": status,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "executed_global_optimizer_steps": executed_updates,
            "optimizer_instance_count": optimizer_instances,
            "M0_measure_draws": m0_stream.draw_count,
            "M0_measure_rolling_sha256": m0_stream.rolling_sha256,
            "M1_constraint_draws": m1_stream.draw_count if m1_stream else 0,
            "M1_constraint_rolling_sha256": m1_stream.rolling_sha256 if m1_stream else None,
            "physics_batch_draws": physics_stream.local_step if physics_stream else 0,
            "physics_batch_rolling_sha256": physics_stream.rolling_sha256 if physics_stream else None,
            "m0_gate": m0_gate,
            "m1_feasibility_gate": feasibility_gate,
        },
    )
    files: dict[str, Path] = {
        "manifest_start": output / "manifest-start.json",
        "manifest_final": manifest_final_path,
        "training_log": log_path,
        "measure_data_batch_hashes": data_hash_path,
        "physics_batch_hashes": physics_hash_path,
        "full_medium_audits": audit_log_path,
        "environment": environment_path,
        "m0_gate": output / "m0-full-medium-gate.json",
        **(
            {"m1_feasibility_gate": output / "m1-full-medium-feasibility-gate.json"}
            if feasibility_gate is not None
            else {}
        ),
        **{f"checkpoint_{name}": path for name, path in checkpoints.items()},
        **{f"prediction_{name}": path for name, path in predictions.items()},
    }
    summary = {
        "schema_id": "phk-v23-lf2-reference-blind-run-summary-v1",
        "task_id": TASK_ID,
        "status": status,
        "trajectory": TRAJECTORY,
        "source_identity": source_identity,
        "contracts": identities,
        "device": gpu_name,
        "dtype": "FLOAT64",
        "seed": 17,
        "architecture": model.architecture_manifest(),
        "parent_checkpoint_sha256": parent_hash,
        "partition_sha256": dataset.partition_sha256,
        "executed_global_optimizer_steps": executed_updates,
        "stage_update_counts": {
            M0_STAGE: 1200,
            M1_STAGE: max(0, executed_updates - 1200),
        },
        "stage_stream_boundaries": {
            M0_STAGE: m0_stream_boundary,
            M1_STAGE: stage_stream_policy(M1_STAGE),
        },
        "minimum_total_loss_across_stage_objectives": minimum_total,
        "final_scalars": final_scalars,
        "lf1_b0_full_medium_baseline": baseline,
        "m0_full_medium_audit": m0_audit,
        "m0_gate": m0_gate,
        "m1_final_full_medium_audit": final_audit,
        "m1_feasibility_gate": feasibility_gate,
        "wall_seconds_including_predictions": wall_seconds,
        "gpu_hours": wall_seconds / 3600.0,
        "hourly_price_cny": price,
        "estimated_incremental_cost_cny": wall_seconds / 3600.0 * price,
        "medium_training_labels_used": True,
        "fine_extra_fine_or_evaluator_read": False,
        "prediction_reference_free": True,
        "stress_fields_or_metrics_read": False,
        "manual_early_stop": False,
        "accuracy_checkpoint_selection": False,
        "artifacts": {name: _artifact_record(path, output) for name, path in files.items()},
    }
    _write_json_exclusive(output / "summary.json", summary)
    return summary


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--medium-carrier", type=Path, required=True)
    parser.add_argument("--initial-checkpoint", type=Path, required=True)
    parser.add_argument("--cpu-qualification", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--source-identity", required=True)
    parser.add_argument("--hourly-price-cny", type=float, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    summary = execute_reference_blind_gpu_trajectory(
        output_root=arguments.output_root,
        medium_carrier=arguments.medium_carrier,
        initial_checkpoint=arguments.initial_checkpoint,
        cpu_qualification_path=arguments.cpu_qualification,
        device_name=arguments.device,
        source_identity=arguments.source_identity,
        hourly_price_cny=arguments.hourly_price_cny,
    )
    print(json.dumps(summary, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


__all__ = [
    "CATEGORY_NAMES",
    "CATEGORY_QUOTAS",
    "CONTRACT_PATHS",
    "M0_SEEDS",
    "M1_SEEDS",
    "MeasureBatch",
    "MeasureCalibratedBatchStream",
    "MediumMeasureDataset",
    "TASK_ID",
    "augmented_lagrangian_inequality",
    "augmented_lagrangian_sum",
    "build_training_config",
    "contract_identity",
    "execute_reference_blind_gpu_trajectory",
    "full_medium_audit",
    "load_contracts",
    "load_lf1_b0_initialization",
    "load_medium_dataset",
    "m0_constraint_tensors",
    "m0_full_medium_gate",
    "m1_constraint_tensors",
    "m1_full_medium_feasibility_gate",
    "stage_stream_policy",
    "trapezoid_node_weights",
    "update_multipliers",
    "weighted_measure_terms",
]
