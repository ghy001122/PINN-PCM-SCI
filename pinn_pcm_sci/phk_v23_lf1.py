"""PHK-V2.3 LF1 admissible event-preserving multi-fidelity pilot.

This module owns the bounded LF1 reference-blind GPU state machine.  It reuses
the frozen V2.2R strong-form objective and the LF0 physics stream.  Medium is
the only label source; nominal fine/extra-fine and stress carriers are not
reachable from this module.
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
    FrequencyBand,
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
    LF0LowFidelityBatchStream,
    LF0PhysicsBatchStream,
    PhysicsBatch,
    _artifact_record,
    _batch_sha256,
    _physical_object,
    _physics_objective,
    _read_json,
    _sha256_path,
    _write_json_exclusive,
    potential_maximum_principle_windowed_guard,
)


PROGRAM_CONTRACT_PATH = (
    ROOT
    / "configs"
    / "phk_v23"
    / "program_contract_lf1_event_preserving_multifidelity.json"
)
METHOD_CONTRACT_PATH = (
    ROOT
    / "configs"
    / "phk_v23"
    / "method_contract_lf1_event_preserving_multifidelity.json"
)
DATA_CONTRACT_PATH = (
    ROOT / "configs" / "phk_v23" / "data_contract_lf1_medium_event_replay.json"
)
DECISION_CONTRACT_PATH = (
    ROOT / "configs" / "phk_v23" / "decision_contract_lf1_event_preserving.json"
)
DEPLOYED_SOURCE_MANIFEST_PATH = (
    ROOT / "cloud" / "phk_v23_lf1_autodl" / "deployed-source-manifest.json"
)
CONTRACT_PATHS = {
    "program": PROGRAM_CONTRACT_PATH,
    "method": METHOD_CONTRACT_PATH,
    "data": DATA_CONTRACT_PATH,
    "decision": DECISION_CONTRACT_PATH,
}
EXPECTED_CONTRACT_SCHEMAS = {
    "program": "phk-v23-lf1-program-contract-v1",
    "method": "phk-v23-lf1-method-contract-v1",
    "data": "phk-v23-lf1-data-contract-v1",
    "decision": "phk-v23-lf1-decision-contract-v1",
}
TASK_ID = "PHK_V23_LF1_EVENT_PRESERVING_MULTIFIDELITY_PILOT"
ARM_A = "A_RANGE_PRESERVING_SCRATCH"
ARM_B = "B_EVENT_DISTILLATION_PERSISTENT_REPLAY"
ARM_C = "C_DATA_ONLY_CONTINUATION_IF_TRIGGERED"
RUN_ARMS = (ARM_A, ARM_B, ARM_C)
POOL_NAMES = (
    "event_cycle_1",
    "event_cycle_2",
    "transition_cycle_1",
    "transition_cycle_2",
    "recovery_cycle_1",
    "recovery_cycle_2",
)
DISTILLATION_COUNTS = (128, 128, 64, 64, 64, 64)
REPLAY_COUNTS = (128, 128, 64, 64, 64, 64)
DISTILLATION_SEEDS = (17101, 17102, 17103, 17104, 17105, 17106)
REPLAY_SEEDS = (17201, 17202, 17203, 17204, 17205, 17206)


def _is_upper_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and value == value.upper()
        and all(character in "0123456789ABCDEF" for character in value)
    )


def load_contracts() -> dict[str, dict[str, Any]]:
    """Load and cross-check the four pre-execution LF1 contracts."""

    contracts = {name: _read_json(path) for name, path in CONTRACT_PATHS.items()}
    for name, schema in EXPECTED_CONTRACT_SCHEMAS.items():
        if contracts[name].get("schema_id") != schema:
            raise ValueError(f"unsupported LF1 {name} contract")
    relative = {
        name: path.relative_to(ROOT).as_posix() for name, path in CONTRACT_PATHS.items()
    }
    program = contracts["program"]
    method = contracts["method"]
    data = contracts["data"]
    decision = contracts["decision"]
    if program.get("phase_id") != TASK_ID:
        raise ValueError("LF1 task identity drift")
    if tuple(program.get("run_limits", {}).get("fixed_order", ())) != RUN_ARMS:
        raise ValueError("LF1 run order drift")
    if (
        method.get("program_contract") != relative["program"]
        or data.get("program_contract") != relative["program"]
        or decision.get("program_contract") != relative["program"]
        or decision.get("method_contract") != relative["method"]
        or decision.get("data_contract") != relative["data"]
    ):
        raise ValueError("LF1 cross-contract identity drift")
    authorization = program.get("authorization", {})
    if not all(
        authorization.get(name) is True
        for name in (
            "contract_code_test_document_writes",
            "cpu_event_transfer_qualification",
            "gpu_run_a",
            "gpu_run_b_after_valid_a",
            "conditional_gpu_run_c",
            "seed_17_only",
        )
    ):
        raise PermissionError("LF1 bounded campaign is not fully authorized")
    if any(
        authorization.get(name) is not False
        for name in (
            "selective_commit_or_push",
            "new_seed",
            "phase_latent_teacher_backup",
            "stress_prediction_or_unseal",
            "pjgr_or_r2",
            "benchmark_pde_constitutive_geometry_parameter_reference_or_evaluator_change",
        )
    ):
        raise PermissionError("LF1 authorization boundary drift")
    identity = method.get("common_gpu_identity", {})
    if (
        identity.get("gpu") != "TESLA_V100_PCIE_32GB_ONLY"
        or identity.get("dtype") != "FLOAT64"
        or identity.get("seed") != 17
        or identity.get("potential_transform")
        != POTENTIAL_TRANSFORM_EXACT_TOP_RANGE_PRESERVING
    ):
        raise ValueError("LF1 model or device identity drift")
    runs = method.get("runs", {})
    if (
        runs.get("A", {}).get("physics_updates") != 1200
        or runs.get("B", {}).get("B0", {}).get("updates") != 1200
        or runs.get("B", {}).get("B1", {}).get("updates") != 1200
        or runs.get("C", {}).get("additional_data_updates") != 1200
    ):
        raise ValueError("LF1 update budget drift")
    source = data.get("training_source", {})
    if (
        source.get("resolution") != "medium"
        or source.get("only_gpu_training_label_source") is not True
    ):
        raise PermissionError("LF1 medium-only label identity drift")
    if decision.get("stress_status") != "TWO_STRESS_REFERENCES_SEALED_UNREAD":
        raise PermissionError("LF1 stress boundary drift")
    if set(decision.get("machine_outcomes_and_unique_next", {})) != {
        "LF1_CPU_OR_REPRESENTABILITY_BLOCKED",
        "LF1_DATA_TRANSFER_NO_EVENT",
        "LF1_PHYSICS_FORGETTING_PERSISTS",
        "LF1_DATA_ONLY_VALUE_NO_PINN_GAIN",
        "LF1_EVENT_PRESERVING_PINN_PROVISIONAL_SIGNAL",
        "LF1_NUMERICAL_OR_IDENTITY_INVALID",
        "LF1_ENGINEERING_BLOCKED",
    }:
        raise ValueError("LF1 machine outcome map is not exhaustive")
    return contracts


def contract_identity() -> dict[str, dict[str, str]]:
    return {
        name: {"path": path.relative_to(ROOT).as_posix(), "sha256": _sha256_path(path)}
        for name, path in CONTRACT_PATHS.items()
    }


def build_training_config(arm: str, device_name: str) -> PhkTrainingConfig:
    if arm not in RUN_ARMS:
        raise ValueError(f"unknown LF1 arm: {arm}")
    updates = 1200 if arm == ARM_A else 2400
    config = PhkTrainingConfig(
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
        checkpoint_every=updates,
        pde_weight=1.0,
        boundary_weight=5.0,
        initial_weight=1.0,
        dtype="float64",
        device=device_name,
    )
    config.validate()
    return config


def build_range_preserving_model(
    *, physics: PhkV22RPhysics, config: PhkTrainingConfig
) -> PhkV22RModel:
    return PhkV22RModel(
        physics=physics,
        arm="STRONG_RAW",
        hidden_width=config.hidden_width,
        hidden_layers=config.hidden_layers,
        frequency_band=FrequencyBand.band_a(),
        potential_output_transform=POTENTIAL_TRANSFORM_EXACT_TOP_RANGE_PRESERVING,
    )


@dataclass(frozen=True)
class EventBatch:
    coordinates: torch.Tensor
    targets: torch.Tensor
    category_counts: Mapping[str, int]
    batch_sha256: str


class MediumEventDataset:
    """Frozen medium grid plus six deterministic event-topology pools."""

    def __init__(self, result: PhkV21OracleResult, *, physics: PhkV22RPhysics) -> None:
        self.physics = physics
        self.time = np.asarray(result.time, dtype=np.float64).reshape(-1)
        self.x = np.asarray(result.grid.x_centers, dtype=np.float64).reshape(-1)
        self.z = np.asarray(result.grid.z_centers, dtype=np.float64).reshape(-1)
        shape = (self.time.size, self.z.size, self.x.size)
        self.fields = {
            name: np.asarray(getattr(result, name), dtype=np.float64).reshape(shape)
            for name in ("potential", "temperature", "phase")
        }
        if any(not np.isfinite(values).all() for values in self.fields.values()):
            raise ValueError("LF1 medium carrier contains non-finite fields")
        phase = self.fields["phase"]
        derivative = np.gradient(phase, self.time, axis=0, edge_order=1)
        tt = self.time[:, None, None]
        w1 = (tt >= 0.0) & (tt <= 0.35)
        w2 = (tt > 0.35) & (tt <= 1.25)
        w3 = (tt >= 1.25) & (tt <= 1.60)
        w4 = (tt > 1.60) & (tt <= 2.50)
        roi = (
            (self.x[None, None, :] >= -0.55)
            & (self.x[None, None, :] <= 0.55)
            & (self.z[None, :, None] <= 0.55)
        )
        roi_mean = np.mean(phase[:, roi[0]], axis=1)
        first_peak_time = float(self.time[np.argmax(np.where(self.time <= 1.25, roi_mean, -np.inf))])
        second_domain = self.time >= 1.25
        second_peak_index = int(
            np.argmax(np.where(second_domain, roi_mean, -np.inf))
        )
        second_peak_time = float(self.time[second_peak_index])
        initial = phase[0:1]
        masks = {
            "event_cycle_1": w1 & (phase >= 0.5),
            "event_cycle_2": w3 & (phase >= 0.5),
            "transition_cycle_1": w1 & (phase < 0.5) & (derivative > 0.0),
            "transition_cycle_2": w3 & (phase < 0.5) & (derivative > 0.0),
            "recovery_cycle_1": w2 & (tt > first_peak_time) & (derivative < 0.0) & (phase > initial),
            "recovery_cycle_2": w4 & (tt > second_peak_time) & (derivative < 0.0) & (phase > initial),
        }
        self.pool_coordinates: dict[str, torch.Tensor] = {}
        self.pool_targets: dict[str, torch.Tensor] = {}
        self.pool_indices: dict[str, np.ndarray] = {}
        for name in POOL_NAMES:
            indices = np.argwhere(np.broadcast_to(masks[name], shape))
            self.pool_indices[name] = indices
            if indices.size == 0:
                coordinates = np.empty((0, 3), dtype=np.float64)
                targets = np.empty((0, 3), dtype=np.float64)
            else:
                ti, zi, xi = indices.T
                coordinates = np.column_stack((self.x[xi], self.z[zi], self.time[ti]))
                targets = np.column_stack(
                    tuple(self.fields[field][ti, zi, xi] for field in ("potential", "temperature", "phase"))
                )
            self.pool_coordinates[name] = torch.as_tensor(coordinates, dtype=torch.float64)
            self.pool_targets[name] = torch.as_tensor(targets, dtype=torch.float64)
        self.background = LF0LowFidelityBatchStream.from_result(
            result, physics=physics, points_per_stratum=64
        )

    @property
    def pool_counts(self) -> dict[str, int]:
        return {name: int(self.pool_coordinates[name].shape[0]) for name in POOL_NAMES}

    def all_grid_coordinates(self) -> np.ndarray:
        tt, zz, xx = np.meshgrid(self.time, self.z, self.x, indexing="ij")
        return np.column_stack((xx.reshape(-1), zz.reshape(-1), tt.reshape(-1)))


class MediumEventBatchStream:
    """Independent deterministic Sobol streams for distillation or replay."""

    def __init__(
        self,
        dataset: MediumEventDataset,
        *,
        role: str,
    ) -> None:
        if role not in {"DISTILLATION", "REPLAY"}:
            raise ValueError("LF1 event stream role is invalid")
        self.dataset = dataset
        self.role = role
        self.counts = DISTILLATION_COUNTS if role == "DISTILLATION" else REPLAY_COUNTS
        seeds = DISTILLATION_SEEDS if role == "DISTILLATION" else REPLAY_SEEDS
        self.engines = tuple(
            torch.quasirandom.SobolEngine(1, scramble=True, seed=seed) for seed in seeds
        )
        self.draw_count = 0
        self._rolling = hashlib.sha256(f"PHK_V23_LF1_{role}_BATCHES".encode("ascii"))

    @property
    def rolling_sha256(self) -> str:
        return self._rolling.copy().hexdigest().upper()

    def fast_forward(self, draws: int) -> None:
        count = int(draws)
        if self.draw_count != 0 or count < 0:
            raise ValueError("LF1 event stream fast-forward is only valid from its origin")
        if self.role == "DISTILLATION":
            for engine in self.dataset.background.engines:
                engine.fast_forward(count * self.dataset.background.points_per_stratum)
            self.dataset.background.draw_count = count
        for engine, points in zip(self.engines, self.counts, strict=True):
            engine.fast_forward(count * points)
        self.draw_count = count
        self._rolling.update(f"FAST_FORWARD:{count}".encode("ascii"))

    @staticmethod
    def _select(
        engine: torch.quasirandom.SobolEngine,
        coordinates: torch.Tensor,
        targets: torch.Tensor,
        count: int,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        size = int(coordinates.shape[0])
        if size <= 0:
            raise ValueError("LF1 required event pool is empty")
        unit = engine.draw(int(count), dtype=torch.float64).reshape(-1)
        indices = torch.floor(unit * size).to(dtype=torch.long).clamp_max(size - 1)
        return coordinates[indices], targets[indices]

    def draw(self, step: int) -> EventBatch:
        exact_step = int(step)
        if exact_step != self.draw_count + 1:
            raise ValueError("LF1 event stream must be consumed in strict step order")
        coordinates: list[torch.Tensor] = []
        targets: list[torch.Tensor] = []
        category_counts: dict[str, int] = {}
        if self.role == "DISTILLATION":
            background = self.dataset.background.draw(exact_step)
            coordinates.append(background.coordinates)
            targets.append(background.targets)
            category_counts["background_original_eight_strata"] = int(
                background.coordinates.shape[0]
            )
        for name, engine, count in zip(
            POOL_NAMES, self.engines, self.counts, strict=True
        ):
            selected_coordinates, selected_targets = self._select(
                engine,
                self.dataset.pool_coordinates[name],
                self.dataset.pool_targets[name],
                count,
            )
            coordinates.append(selected_coordinates)
            targets.append(selected_targets)
            category_counts[name] = int(count)
        joined_coordinates = torch.cat(coordinates, dim=0)
        joined_targets = torch.cat(targets, dim=0)
        digest = _batch_sha256(
            joined_coordinates,
            joined_targets,
            metadata=f"LF1:{self.role}:{exact_step}",
        )
        self._rolling.update(bytes.fromhex(digest))
        self.draw_count = exact_step
        return EventBatch(joined_coordinates, joined_targets, category_counts, digest)


def event_distillation_loss(
    model: PhkV22RModel,
    batch: EventBatch,
    *,
    physics: PhkV22RPhysics,
    device: torch.device,
    topology_temperature: float = 0.05,
) -> tuple[torch.Tensor, dict[str, float]]:
    """Equal field loss plus the frozen soft event-topology BCE."""

    coordinates = batch.coordinates.to(device=device, dtype=torch.float64)
    target = batch.targets.to(device=device, dtype=torch.float64)
    prediction = model(coordinates)
    scales = prediction.new_tensor(
        [physics.waveform_amplitude, physics.theta_transition, 0.5]
    )
    field_components = torch.mean(((prediction - target) / scales).square(), dim=0)
    field = torch.mean(field_components)
    topology_target = (target[:, 2:3] >= 0.5).to(dtype=prediction.dtype)
    topology_logits = (prediction[:, 2:3] - 0.5) / float(topology_temperature)
    topology = functional.binary_cross_entropy_with_logits(
        topology_logits, topology_target
    )
    total = field + topology
    return total, {
        "field": float(field.detach().cpu()),
        "potential": float(field_components[0].detach().cpu()),
        "temperature": float(field_components[1].detach().cpu()),
        "phase": float(field_components[2].detach().cpu()),
        "topology": float(topology.detach().cpu()),
    }


def _load_medium_dataset(
    path: Path,
    *,
    physics: PhkV22RPhysics,
    contracts: Mapping[str, Mapping[str, Any]],
) -> MediumEventDataset:
    source = contracts["data"]["training_source"]
    expected = (ROOT / Path(str(source["path"]).replace("/", os.sep))).resolve()
    supplied = Path(path).resolve()
    if supplied != expected:
        raise PermissionError("only the exact frozen LF1 medium carrier is allowed")
    if _sha256_path(supplied) != str(source["sha256"]).upper():
        raise ValueError("LF1 medium carrier byte identity drift")
    return MediumEventDataset(
        read_phk_v21_result(supplied, physical=_physical_object()), physics=physics
    )


def _write_checkpoint(
    *,
    path: Path,
    model: PhkV22RModel,
    optimizer: torch.optim.Optimizer,
    config: PhkTrainingConfig,
    global_step: int,
    physics_program_sha256: str,
    physics_object_sha256: str,
    arm: str,
    stage: str,
    source_identity: str,
    contracts: Mapping[str, Mapping[str, str]],
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
    payload["lf1"] = {
        "schema_id": "phk-v23-lf1-checkpoint-metadata-v1",
        "task_id": TASK_ID,
        "run_arm": arm,
        "stage": stage,
        "global_optimizer_step": int(global_step),
        "source_identity": source_identity,
        "contracts": dict(contracts),
        "potential_transform": POTENTIAL_TRANSFORM_EXACT_TOP_RANGE_PRESERVING,
        "medium_training_labels_used": arm in {ARM_B, ARM_C},
        "nominal_evaluation_reference_read": False,
        "prediction_reference_free": True,
        "stress_fields_or_metrics_read": False,
    }
    exact = Path(path)
    exact.parent.mkdir(parents=True, exist_ok=True)
    with exact.open("xb") as handle:
        torch.save(payload, handle)
    return exact


def _append_json_line(handle: Any, payload: Mapping[str, Any]) -> None:
    handle.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n")
    handle.flush()


def _predict_medium(
    model: PhkV22RModel,
    dataset: MediumEventDataset,
    *,
    device: torch.device,
    chunk_points: int = 65536,
) -> tuple[np.ndarray, np.ndarray]:
    coordinates = dataset.all_grid_coordinates()
    potential = np.empty(coordinates.shape[0], dtype=np.float64)
    phase = np.empty(coordinates.shape[0], dtype=np.float64)
    model.eval()
    with torch.no_grad():
        for start in range(0, coordinates.shape[0], chunk_points):
            end = min(start + chunk_points, coordinates.shape[0])
            values = model(
                torch.as_tensor(
                    coordinates[start:end], dtype=torch.float64, device=device
                )
            ).detach().cpu().numpy()
            potential[start:end] = values[:, 0]
            phase[start:end] = values[:, 2]
    model.train()
    shape = (dataset.time.size, dataset.z.size * dataset.x.size)
    return potential.reshape(shape), phase.reshape(shape)


def b0_data_transfer_gate(
    model: PhkV22RModel,
    dataset: MediumEventDataset,
    *,
    device: torch.device,
    absolute_tolerance: float,
) -> dict[str, Any]:
    potential, phase = _predict_medium(model, dataset, device=device)
    waveform = dataset.physics.waveform(
        torch.as_tensor(dataset.time, dtype=torch.float64).reshape(-1, 1)
    ).detach().cpu().numpy().reshape(-1)
    potential_guard = potential_maximum_principle_windowed_guard(
        potential,
        dataset.time,
        waveform,
        absolute_tolerance=absolute_tolerance,
    )
    flattened_phase = phase.reshape(-1)
    shape = (dataset.time.size, dataset.z.size, dataset.x.size)
    active_counts: dict[str, int] = {}
    for name in ("event_cycle_1", "event_cycle_2"):
        indices = dataset.pool_indices[name]
        flat = np.ravel_multi_index(indices.T, shape)
        active_counts[name] = int(np.count_nonzero(flattened_phase[flat] >= 0.5))
    counts = dataset.pool_counts
    passed = (
        potential_guard["passed"]
        and float(np.max(phase)) >= 0.5
        and all(value >= 1 for value in active_counts.values())
        and all(value > 0 for value in counts.values())
    )
    return {
        "passed": bool(passed),
        "potential_maximum_principle": potential_guard,
        "phase_maximum": float(np.max(phase)),
        "teacher_event_support_predicted_active_count": active_counts,
        "pool_counts": counts,
        "failure_outcome": None if passed else "LF1_DATA_TRANSFER_NO_EVENT",
    }


def _prediction_guard(
    prediction_path: Path,
    *,
    physics: PhkV22RPhysics,
    absolute_tolerance: float,
) -> dict[str, Any]:
    from .phk_v22r_prediction import read_prediction_carrier

    _, arrays = read_prediction_carrier(prediction_path)
    times = torch.as_tensor(arrays["time"], dtype=torch.float64).reshape(-1, 1)
    waveform = physics.waveform(times).detach().cpu().numpy().reshape(-1)
    return potential_maximum_principle_windowed_guard(
        arrays["potential"],
        arrays["time"],
        waveform,
        absolute_tolerance=absolute_tolerance,
    )


def _load_c_checkpoint(
    path: Path,
    *,
    model: PhkV22RModel,
    optimizer: torch.optim.Adam,
    contracts: Mapping[str, Mapping[str, str]],
    device: torch.device,
) -> None:
    checkpoint = torch.load(Path(path), map_location=device, weights_only=False)
    metadata = checkpoint.get("lf1", {})
    if (
        checkpoint.get("schema_id") != "phk-v22r-checkpoint-v1-1"
        or metadata.get("task_id") != TASK_ID
        or metadata.get("run_arm") != ARM_B
        or metadata.get("stage") != "B0_EVENT_DATA_ONLY"
        or metadata.get("global_optimizer_step") != 1200
        or metadata.get("potential_transform")
        != POTENTIAL_TRANSFORM_EXACT_TOP_RANGE_PRESERVING
        or metadata.get("contracts") != dict(contracts)
    ):
        raise PermissionError("LF1 C parent is not the exact valid B0 checkpoint")
    if checkpoint.get("architecture") != model.architecture_manifest():
        raise ValueError("LF1 C parent architecture drift")
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    optimizer.load_state_dict(checkpoint["optimizer_state_dict"])


def _validate_c_trigger(path: Path, *, b0_checkpoint: Path) -> dict[str, Any]:
    trigger = _read_json(Path(path))
    conditions = trigger.get("conditions")
    bindings = trigger.get("input_bindings")
    if (
        trigger.get("schema_id") != "phk-v23-lf1-c-trigger-v1"
        or trigger.get("task_id") != TASK_ID
        or trigger.get("action") != "RUN_C_DATA_ONLY_CONTINUATION_FROM_EXACT_B0"
        or not isinstance(conditions, dict)
        or not conditions
        or not all(value is True for value in conditions.values())
        or not isinstance(bindings, dict)
        or trigger.get("stress_fields_or_metrics_read") is not False
    ):
        raise PermissionError("LF1 C trigger is absent or its conditions did not pass")
    required = {"decision_contract", "cpu_qualification", "b0_checkpoint"}
    if not required.issubset(bindings):
        raise PermissionError("LF1 C trigger evidence bindings are incomplete")
    for name, binding in bindings.items():
        if (
            not isinstance(binding, dict)
            or not _is_upper_sha256(str(binding.get("sha256", "")).upper())
            or not isinstance(binding.get("size_bytes"), int)
            or isinstance(binding.get("size_bytes"), bool)
            or int(binding["size_bytes"]) <= 0
        ):
            raise ValueError(f"LF1 C trigger binding is malformed: {name}")
    if bindings["b0_checkpoint"]["sha256"].upper() != _sha256_path(b0_checkpoint):
        raise ValueError("LF1 C trigger B0 checkpoint binding drift")
    if bindings["b0_checkpoint"]["size_bytes"] != Path(b0_checkpoint).stat().st_size:
        raise ValueError("LF1 C trigger B0 checkpoint size drift")
    if bindings["decision_contract"]["sha256"].upper() != _sha256_path(
        DECISION_CONTRACT_PATH
    ):
        raise ValueError("LF1 C trigger decision contract drift")
    return trigger


def execute_reference_blind_gpu_arm(
    *,
    arm: str,
    output_root: Path,
    device_name: str,
    source_identity: str,
    hourly_price_cny: float,
    medium_carrier: Path | None = None,
    b0_checkpoint: Path | None = None,
    c_trigger: Path | None = None,
) -> dict[str, Any]:
    """Execute one bounded LF1 arm without opening evaluation references."""

    if arm not in RUN_ARMS:
        raise ValueError(f"unknown LF1 arm: {arm}")
    contracts = load_contracts()
    identities = contract_identity()
    if not isinstance(source_identity, str) or not source_identity.startswith(
        "LF1-BUNDLE-"
    ):
        raise ValueError("LF1 source identity is missing or malformed")
    price = float(hourly_price_cny)
    if not math.isfinite(price) or price <= 0.0:
        raise ValueError("LF1 hourly price must be positive and finite")
    if device_name != "cuda:0" or not torch.cuda.is_available():
        raise PermissionError("LF1 requires cuda:0")
    device = torch.device(device_name)
    gpu_name = torch.cuda.get_device_name(device)
    if gpu_name != "Tesla V100-PCIE-32GB":
        raise PermissionError(f"LF1 GPU identity mismatch: {gpu_name}")
    if arm in {ARM_B, ARM_C} and medium_carrier is None:
        raise ValueError("LF1 B/C require the frozen medium carrier")
    if arm == ARM_A and (medium_carrier is not None or b0_checkpoint is not None):
        raise PermissionError("LF1 A must not open a label carrier or parent checkpoint")
    if arm == ARM_C and b0_checkpoint is None:
        raise PermissionError("LF1 C requires the exact B0 checkpoint")
    if arm != ARM_C and b0_checkpoint is not None:
        raise PermissionError("only LF1 C may load a B0 parent checkpoint")
    if arm == ARM_C and c_trigger is None:
        raise PermissionError("LF1 C requires the post-B local trigger record")
    if arm != ARM_C and c_trigger is not None:
        raise PermissionError("only LF1 C may consume a C trigger")
    if arm == ARM_C:
        assert b0_checkpoint is not None and c_trigger is not None
        _validate_c_trigger(Path(c_trigger), b0_checkpoint=Path(b0_checkpoint))

    output = Path(output_root).resolve()
    output.mkdir(parents=True, exist_ok=False)
    config = build_training_config(arm, device_name)
    physics, physical_program_sha256, physical_object_sha256 = load_case_physics(
        config.case_control
    )
    random.seed(config.seed)
    np.random.seed(config.seed)
    torch.manual_seed(config.seed)
    torch.cuda.manual_seed_all(config.seed)
    torch.cuda.reset_peak_memory_stats(device)
    model = build_range_preserving_model(physics=physics, config=config).to(
        device=device, dtype=torch.float64
    )
    if model.architecture_manifest()["potential_output_transform"] != (
        POTENTIAL_TRANSFORM_EXACT_TOP_RANGE_PRESERVING
    ):
        raise ValueError("LF1 range-preserving model identity drift")
    dataset = (
        _load_medium_dataset(Path(medium_carrier), physics=physics, contracts=contracts)
        if medium_carrier is not None
        else None
    )
    started_at = datetime.now(timezone.utc).isoformat()
    started = time.perf_counter()
    run_identity = contracts["method"]["runs"][
        {ARM_A: "A", ARM_B: "B", ARM_C: "C"}[arm]
    ]["identity"]
    manifest_start = {
        "schema_id": "phk-v23-lf1-run-manifest-v1",
        "task_id": TASK_ID,
        "status": "RUNNING_REFERENCE_BLIND_GPU_ARM",
        "started_at_utc": started_at,
        "source_identity": source_identity,
        "contracts": identities,
        "run_arm": arm,
        "run_identity": run_identity,
        "training_config": asdict(config),
        "training_config_sha256": config.identity,
        "architecture": model.architecture_manifest(),
        "device": gpu_name,
        "dtype": "FLOAT64",
        "seed": 17,
        "medium_training_labels_used": arm in {ARM_B, ARM_C},
        "fine_extra_fine_or_evaluator_read": False,
        "stress_fields_or_metrics_read": False,
        "manual_early_stop": False,
        "accuracy_checkpoint_selection": False,
    }
    _write_json_exclusive(output / "manifest-start.json", manifest_start)

    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    distillation: MediumEventBatchStream | None = None
    replay: MediumEventBatchStream | None = None
    physics_stream: LF0PhysicsBatchStream | None = None
    optimizer_instances = 1
    if arm == ARM_A:
        physics_stream = LF0PhysicsBatchStream(
            physics=physics,
            interior_points=config.interior_points,
            boundary_points=config.boundary_points,
            initial_points=config.initial_points,
            refresh_updates=config.refresh_updates,
            seed=config.seed,
        )
    else:
        assert dataset is not None
        distillation = MediumEventBatchStream(dataset, role="DISTILLATION")
    if arm == ARM_C:
        assert b0_checkpoint is not None and distillation is not None
        _load_c_checkpoint(
            Path(b0_checkpoint),
            model=model,
            optimizer=optimizer,
            contracts=identities,
            device=device,
        )
        distillation.fast_forward(1200)

    log_path = output / "training-log.jsonl"
    physics_hash_path = output / "physics-batch-hashes.jsonl"
    data_hash_path = output / "event-data-batch-hashes.jsonl"
    minimum_total = math.inf
    final_scalars: dict[str, float] = {}
    checkpoints: dict[str, Path] = {}
    predictions: dict[str, Path] = {}
    executed_updates = 0
    b0_gate: dict[str, Any] | None = None

    def take_step(total: torch.Tensor) -> tuple[float, float]:
        nonlocal minimum_total
        if not bool(torch.isfinite(total)):
            raise FloatingPointError("LF1 non-finite objective")
        total.backward()
        norm = torch.nn.utils.clip_grad_norm_(model.parameters(), config.gradient_clip_norm)
        if not bool(torch.isfinite(norm)):
            raise FloatingPointError("LF1 non-finite gradient")
        optimizer.step()
        value = float(total.detach().cpu())
        minimum_total = min(minimum_total, value)
        return value, float(norm.detach().cpu())

    with (
        log_path.open("x", encoding="utf-8", newline="\n") as log_handle,
        physics_hash_path.open("x", encoding="utf-8", newline="\n") as physics_handle,
        data_hash_path.open("x", encoding="utf-8", newline="\n") as data_handle,
    ):
        if arm == ARM_A:
            assert physics_stream is not None
            for local_step in range(1, 1201):
                optimizer.zero_grad(set_to_none=True)
                batch = physics_stream.draw(
                    model, local_step, dtype=torch.float64, device=device
                )
                total, components = _physics_objective(model, batch, config)
                total_value, norm = take_step(total)
                executed_updates = local_step
                final_scalars = {**components, "total_loss": total_value, "gradient_norm_before_clip": norm}
                _append_json_line(physics_handle, {
                    "global_step": local_step,
                    "physics_local_step": local_step,
                    "active_windows": batch.active_windows,
                    "refreshed": batch.refreshed,
                    "interior_coordinate_sha256": batch.interior_sha256,
                    "boundary_coordinate_sha256": batch.boundary_sha256,
                    "initial_coordinate_sha256": batch.initial_sha256,
                    "batch_sha256": batch.batch_sha256,
                })
                if local_step == 1 or local_step % config.log_every == 0 or local_step == 1200:
                    _append_json_line(log_handle, {"global_step": local_step, "stage": "A_PURE_PHYSICS", **final_scalars})
        elif arm == ARM_B:
            assert distillation is not None and dataset is not None
            for global_step in range(1, 1201):
                optimizer.zero_grad(set_to_none=True)
                batch = distillation.draw(global_step)
                total, components = event_distillation_loss(
                    model, batch, physics=physics, device=device
                )
                total_value, norm = take_step(total)
                executed_updates = global_step
                final_scalars = {**components, "total_loss": total_value, "gradient_norm_before_clip": norm}
                _append_json_line(data_handle, {"global_step": global_step, "data_local_step": global_step, "role": "DISTILLATION", "category_counts": batch.category_counts, "batch_sha256": batch.batch_sha256})
                if global_step == 1 or global_step % config.log_every == 0 or global_step == 1200:
                    _append_json_line(log_handle, {"global_step": global_step, "stage": "B0_EVENT_DATA_ONLY", **final_scalars})
            checkpoints["b0"] = _write_checkpoint(
                path=output / "checkpoint-b0-step-1200.pt",
                model=model,
                optimizer=optimizer,
                config=config,
                global_step=1200,
                physics_program_sha256=physical_program_sha256,
                physics_object_sha256=physical_object_sha256,
                arm=arm,
                stage="B0_EVENT_DATA_ONLY",
                source_identity=source_identity,
                contracts=identities,
            )
            absolute_tolerance = float(contracts["decision"]["potential_maximum_principle"]["absolute_tolerance"])
            b0_gate = b0_data_transfer_gate(
                model,
                dataset,
                device=device,
                absolute_tolerance=absolute_tolerance,
            )
            _write_json_exclusive(output / "b0-data-transfer-gate.json", b0_gate)
            predictions["b0"] = write_prediction_carrier(
                checkpoint_path=checkpoints["b0"],
                output_path=output / "prediction-b0-step-1200.npz",
                device_name=device_name,
            )
            if b0_gate["passed"]:
                del optimizer
                optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
                optimizer_instances = 2
                physics_stream = LF0PhysicsBatchStream(
                    physics=physics,
                    interior_points=config.interior_points,
                    boundary_points=config.boundary_points,
                    initial_points=config.initial_points,
                    refresh_updates=config.refresh_updates,
                    seed=config.seed,
                )
                replay = MediumEventBatchStream(dataset, role="REPLAY")
                for local_step in range(1, 1201):
                    global_step = 1200 + local_step
                    optimizer.zero_grad(set_to_none=True)
                    physics_batch = physics_stream.draw(
                        model, local_step, dtype=torch.float64, device=device
                    )
                    physics_loss, physics_components = _physics_objective(
                        model, physics_batch, config
                    )
                    replay_batch = replay.draw(local_step)
                    replay_loss, replay_components = event_distillation_loss(
                        model, replay_batch, physics=physics, device=device
                    )
                    total = physics_loss + 0.1 * replay_loss
                    total_value, norm = take_step(total)
                    executed_updates = global_step
                    final_scalars = {
                        **physics_components,
                        **{f"replay:{name}": value for name, value in replay_components.items()},
                        "replay_weight": 0.1,
                        "total_loss": total_value,
                        "gradient_norm_before_clip": norm,
                    }
                    _append_json_line(physics_handle, {"global_step": global_step, "physics_local_step": local_step, "active_windows": physics_batch.active_windows, "refreshed": physics_batch.refreshed, "interior_coordinate_sha256": physics_batch.interior_sha256, "boundary_coordinate_sha256": physics_batch.boundary_sha256, "initial_coordinate_sha256": physics_batch.initial_sha256, "batch_sha256": physics_batch.batch_sha256})
                    _append_json_line(data_handle, {"global_step": global_step, "data_local_step": local_step, "role": "REPLAY", "category_counts": replay_batch.category_counts, "batch_sha256": replay_batch.batch_sha256})
                    if local_step == 1 or local_step % config.log_every == 0 or local_step == 1200:
                        _append_json_line(log_handle, {"global_step": global_step, "stage": "B1_PHYSICS_PLUS_PERSISTENT_REPLAY", **final_scalars})
        else:
            assert distillation is not None and dataset is not None
            for global_step in range(1201, 2401):
                optimizer.zero_grad(set_to_none=True)
                batch = distillation.draw(global_step)
                total, components = event_distillation_loss(
                    model, batch, physics=physics, device=device
                )
                total_value, norm = take_step(total)
                executed_updates = global_step
                final_scalars = {**components, "total_loss": total_value, "gradient_norm_before_clip": norm}
                _append_json_line(data_handle, {"global_step": global_step, "data_local_step": global_step, "role": "DISTILLATION_CONTINUATION", "category_counts": batch.category_counts, "batch_sha256": batch.batch_sha256})
                if global_step == 1201 or global_step % config.log_every == 0 or global_step == 2400:
                    _append_json_line(log_handle, {"global_step": global_step, "stage": "C_DATA_ONLY_CONTINUATION", **final_scalars})

    b_stopped_at_gate = arm == ARM_B and b0_gate is not None and not b0_gate["passed"]
    final_stage = {
        ARM_A: "A_PURE_PHYSICS",
        ARM_B: "B0_EVENT_DATA_ONLY" if b_stopped_at_gate else "B1_PHYSICS_PLUS_PERSISTENT_REPLAY",
        ARM_C: "C_DATA_ONLY_CONTINUATION",
    }[arm]
    if not (arm == ARM_B and b_stopped_at_gate):
        expected = 1200 if arm == ARM_A else 2400
        if executed_updates != expected:
            raise RuntimeError("LF1 arm ended before its frozen update limit")
        checkpoints["final"] = _write_checkpoint(
            path=output / "checkpoint-final.pt",
            model=model,
            optimizer=optimizer,
            config=config,
            global_step=executed_updates,
            physics_program_sha256=physical_program_sha256,
            physics_object_sha256=physical_object_sha256,
            arm=arm,
            stage=final_stage,
            source_identity=source_identity,
            contracts=identities,
        )
        predictions["final"] = write_prediction_carrier(
            checkpoint_path=checkpoints["final"],
            output_path=output / "prediction-final.npz",
            device_name=device_name,
        )
    elif "b0" in checkpoints:
        checkpoints["final"] = checkpoints["b0"]
        predictions["final"] = predictions["b0"]

    absolute_tolerance = float(
        contracts["decision"]["potential_maximum_principle"]["absolute_tolerance"]
    )
    potential_guards = {
        name: _prediction_guard(path, physics=physics, absolute_tolerance=absolute_tolerance)
        for name, path in predictions.items()
    }
    numerical_valid = all(item["passed"] for item in potential_guards.values())
    status = (
        "LF1_NUMERICAL_OR_IDENTITY_INVALID"
        if not numerical_valid
        else (
            "LF1_DATA_TRANSFER_NO_EVENT"
            if b_stopped_at_gate
            else "LF1_REFERENCE_BLIND_GPU_RUN_COMPLETE"
        )
    )
    torch.cuda.synchronize(device)
    wall_seconds = time.perf_counter() - started
    environment_path = output / "environment.json"
    _write_json_exclusive(environment_path, {
        "schema_id": "phk-v23-lf1-environment-v1",
        "gpu_name": gpu_name,
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "numpy_version": np.__version__,
        "python": os.sys.version,
        "medium_training_labels_present": arm in {ARM_B, ARM_C},
        "fine_extra_fine_evaluator_present": False,
        "stress_fields_present": False,
    })
    manifest_final_path = output / "manifest-final.json"
    _write_json_exclusive(manifest_final_path, {
        **manifest_start,
        "status": status,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "executed_global_optimizer_steps": executed_updates,
        "optimizer_instance_count": optimizer_instances,
        "physics_batch_draws": physics_stream.local_step if physics_stream else 0,
        "physics_batch_rolling_sha256": physics_stream.rolling_sha256 if physics_stream else None,
        "distillation_draws": distillation.draw_count if distillation else 0,
        "distillation_rolling_sha256": distillation.rolling_sha256 if distillation else None,
        "replay_draws": replay.draw_count if replay else 0,
        "replay_rolling_sha256": replay.rolling_sha256 if replay else None,
        "b0_data_transfer_gate": b0_gate,
        "potential_maximum_principle": potential_guards,
    })
    files: dict[str, Path] = {
        "manifest_start": output / "manifest-start.json",
        "manifest_final": manifest_final_path,
        "training_log": log_path,
        "physics_batch_hashes": physics_hash_path,
        "event_data_batch_hashes": data_hash_path,
        "environment": environment_path,
        **({"b0_data_transfer_gate": output / "b0-data-transfer-gate.json"} if b0_gate is not None else {}),
        **{f"checkpoint_{name}": path for name, path in checkpoints.items()},
        **{f"prediction_{name}": path for name, path in predictions.items()},
    }
    summary = {
        "schema_id": "phk-v23-lf1-reference-blind-run-summary-v1",
        "task_id": TASK_ID,
        "status": status,
        "run_arm": arm,
        "run_identity": run_identity,
        "source_identity": source_identity,
        "contracts": identities,
        "device": gpu_name,
        "dtype": "FLOAT64",
        "seed": 17,
        "architecture": model.architecture_manifest(),
        "executed_global_optimizer_steps": executed_updates,
        "stage_update_counts": (
            {"A_PURE_PHYSICS": 1200}
            if arm == ARM_A
            else (
                {"B0_EVENT_DATA_ONLY": 1200, "B1_PHYSICS_PLUS_PERSISTENT_REPLAY": 0 if b_stopped_at_gate else 1200}
                if arm == ARM_B
                else {"C_DATA_ONLY_CONTINUATION": 1200}
            )
        ),
        "minimum_total_loss_across_stage_objectives": minimum_total,
        "final_scalars": final_scalars,
        "b0_data_transfer_gate": b0_gate,
        "potential_maximum_principle": potential_guards,
        "wall_seconds_including_prediction": wall_seconds,
        "gpu_hours": wall_seconds / 3600.0,
        "hourly_price_cny": price,
        "estimated_incremental_cost_cny": wall_seconds / 3600.0 * price,
        "medium_training_labels_used": arm in {ARM_B, ARM_C},
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
    parser.add_argument("--arm", choices=RUN_ARMS, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--source-identity", required=True)
    parser.add_argument("--hourly-price-cny", type=float, required=True)
    parser.add_argument("--medium-carrier", type=Path)
    parser.add_argument("--b0-checkpoint", type=Path)
    parser.add_argument("--c-trigger", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    summary = execute_reference_blind_gpu_arm(
        arm=arguments.arm,
        output_root=arguments.output_root,
        device_name=arguments.device,
        source_identity=arguments.source_identity,
        hourly_price_cny=arguments.hourly_price_cny,
        medium_carrier=arguments.medium_carrier,
        b0_checkpoint=arguments.b0_checkpoint,
        c_trigger=arguments.c_trigger,
    )
    print(json.dumps(summary, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


__all__ = [
    "ARM_A",
    "ARM_B",
    "ARM_C",
    "CONTRACT_PATHS",
    "MediumEventBatchStream",
    "MediumEventDataset",
    "TASK_ID",
    "b0_data_transfer_gate",
    "build_range_preserving_model",
    "contract_identity",
    "event_distillation_loss",
    "execute_reference_blind_gpu_arm",
    "load_contracts",
]
