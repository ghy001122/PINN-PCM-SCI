"""LF6 matched event-frontier screen and safety-gated physics pilot.

All optimization batches are read from the CPU-F materialized ledger.  This
module deliberately contains no sampling engine: the remote runtime verifies
the complete ledger before constructing an optimizer and then consumes it in
strict array order.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import time
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .phk_v22r_pinn import PhkV22RModel
from .phk_v22r_prediction import write_prediction_carrier
from .phk_v22r_training import (
    METHOD_CONTRACT_PATH as V22R_METHOD_CONTRACT_PATH,
    PROGRAM_CONTRACT_PATH as V22R_PROGRAM_CONTRACT_PATH,
    ROOT,
    _checkpoint_payload,
    load_case_physics,
)
from .phk_v23_lf0 import (
    PhysicsBatch,
    _artifact_record,
    _physics_objective,
    _read_json,
    _sha256_path,
    _write_json_exclusive,
)
from .phk_v23_lf2 import CATEGORY_NAMES, CATEGORY_QUOTAS, MeasureBatch, MediumMeasureDataset, _batch_sha256, load_medium_dataset
from .phk_v23_lf3 import (
    LOGIT_SPAN,
    _phase_state_sha256,
    build_training_config,
    full_medium_audit,
    measure_decoupled_terms,
    phase_logit_targets,
)
from .phk_v23_lf4 import (
    ExtraBatch,
    _field_state_sha256,
    _gradient_group_norm,
    load_lf3_t0_model,
    normalized_logit_mse,
)


TASK_ID = "PHK_V23_LF6_EVENT_FRONTIER_RANK_BAND_AND_SAFETY_GATED_PHYSICS_PILOT_EXECUTE"
TITLE = "PHK-V2.3 LF6 cycle-resolved event-frontier rank-band alignment and safety-gated physics pilot"
DEV_U = "DEV_U_GENERIC_ENDPOINT_CONTROL"
DEV_R = "DEV_R_EVENT_FRONTIER_RANK_BAND"
DEV_M = "DEV_M_INTERFACE_BAND_MSE"
DEV_ORDER = (DEV_U, DEV_R)
P0_CANDIDATE_ORDER = (DEV_M, DEV_U, DEV_R)
FRONTIER_POOL_NAMES = ("C1_PRE", "C1_POST", "C2_PRE", "C2_POST")
DEV_UPDATES = 400
P0_UPDATES = 1200
P0_PHASE_FREEZE_STEPS = 550
EXPECTED_PARTITION_SHA256 = "EFD70886DD85AC467F06F38B48FB0EE6C0132471CE74817E3A4D68E752B7A515"
EXPECTED_BASE_400_SHA256 = "3870D0C1411B3DF6E04C5BA316B3F0F77233D94A73A19E84523D81B62F692E4A"
EXPECTED_SPATIAL_400_SHA256 = "4DB1728CC543B1AB18BD3F74B83B29EBFE5F95624D98DAFEA615B0ECDC69DEC4"
EXPECTED_P0_PHYSICS_SHA256 = "536E6706A0B68EBB1277A97F402D273AFA2EA1E0B27106F26CB4222B7EC05C53"
EXPECTED_FIXED_POOL_SHA256 = "FD285AFC67C011CE9778E36C5FEE8FA7EAECB933690AF346993B7677AF0E64CF"
PHASE_MSE_MAXIMUM = 0.001330588465425399

PROGRAM_CONTRACT_PATH = ROOT / "configs/phk_v23/program_contract_lf6_event_frontier.json"
METHOD_CONTRACT_PATH = ROOT / "configs/phk_v23/method_contract_lf6_event_frontier.json"
DATA_CONTRACT_PATH = ROOT / "configs/phk_v23/data_contract_lf6_event_frontier.json"
DECISION_CONTRACT_PATH = ROOT / "configs/phk_v23/decision_contract_lf6_event_frontier.json"
CONTRACT_PATHS = {
    "program": PROGRAM_CONTRACT_PATH,
    "method": METHOD_CONTRACT_PATH,
    "data": DATA_CONTRACT_PATH,
    "decision": DECISION_CONTRACT_PATH,
}
EXPECTED_SCHEMAS = {
    "program": "phk-v23-lf6-program-contract-v1",
    "method": "phk-v23-lf6-method-contract-v1",
    "data": "phk-v23-lf6-data-contract-v1",
    "decision": "phk-v23-lf6-decision-contract-v1",
}

LEDGER_ARRAY_NAMES = (
    "base_coordinates", "base_targets", "base_batch_sha256",
    "spatial_coordinates", "spatial_targets", "spatial_batch_sha256",
    "frontier_coordinates", "frontier_targets", "frontier_offsets",
    "uniform_coordinates", "uniform_targets", "uniform_offsets",
    "p0_interior", "p0_left", "p0_right", "p0_bottom", "p0_top",
    "p0_initial", "p0_active_windows", "p0_refreshed",
    "p0_interior_sha256", "p0_boundary_sha256", "p0_initial_sha256",
    "p0_batch_sha256", "fixed_interior", "fixed_left", "fixed_right",
    "fixed_bottom", "fixed_top", "fixed_initial",
)


def _pending(value: Any) -> bool:
    return not isinstance(value, str) or value.startswith("PENDING")


def load_contracts(*, require_ledger_freeze: bool = True) -> dict[str, dict[str, Any]]:
    contracts = {name: _read_json(path) for name, path in CONTRACT_PATHS.items()}
    for name, schema in EXPECTED_SCHEMAS.items():
        if contracts[name].get("schema_id") != schema:
            raise ValueError(f"unsupported LF6 {name} contract")
    relative = {name: path.relative_to(ROOT).as_posix() for name, path in CONTRACT_PATHS.items()}
    if contracts["program"].get("phase_id") != TASK_ID:
        raise ValueError("LF6 task identity drift")
    if any(contracts[name].get("program_contract") != relative["program"] for name in ("method", "data", "decision")):
        raise ValueError("LF6 program binding drift")
    decision = contracts["decision"]
    if decision.get("method_contract") != relative["method"] or decision.get("data_contract") != relative["data"]:
        raise ValueError("LF6 decision binding drift")
    limits = contracts["program"]["hard_limits"]
    if limits.get("maximum_scientific_gpu_trajectories") != 3 or limits.get("maximum_optimizer_updates") != 2000:
        raise ValueError("LF6 run bounds drift")
    common = contracts["method"]["common_identity"]
    if common.get("dtype") != "FLOAT64" or common.get("seed") != 17 or float(common.get("clip_epsilon")) != 1.0e-8:
        raise ValueError("LF6 common identity drift")
    data = contracts["data"]
    if data["target_measure"].get("partition_sha256") != EXPECTED_PARTITION_SHA256:
        raise ValueError("LF6 partition identity drift")
    if data["base_stream_source"].get("rolling_sha256") != EXPECTED_BASE_400_SHA256:
        raise ValueError("LF6 base source identity drift")
    if data["spatial_stream_source"].get("rolling_sha256") != EXPECTED_SPATIAL_400_SHA256:
        raise ValueError("LF6 spatial source identity drift")
    if tuple(data["event_frontier"].get("pool_order", ())) != FRONTIER_POOL_NAMES:
        raise ValueError("LF6 frontier pool order drift")
    ledger = data["materialized_ledger"]
    if ledger.get("P0_physics_1200_sha256") != EXPECTED_P0_PHYSICS_SHA256 or ledger.get("fixed_blind_pool_sha256") != EXPECTED_FIXED_POOL_SHA256:
        raise ValueError("LF6 inherited physics ledger identity drift")
    if require_ledger_freeze:
        required = ("file_sha256", "manifest_sha256", "semantic_sha256", "base_400_sha256", "spatial_400_sha256", "frontier_endpoint_sha256", "uniform_endpoint_sha256")
        if any(_pending(ledger.get(name)) for name in required) or not isinstance(data["event_frontier"].get("brackets"), Mapping):
            raise PermissionError("LF6 CPU-F ledger identities are not frozen")
        if ledger["base_400_sha256"] != EXPECTED_BASE_400_SHA256 or ledger["spatial_400_sha256"] != EXPECTED_SPATIAL_400_SHA256:
            raise ValueError("LF6 materialized inherited stream drift")
    if len(decision.get("machine_outcomes_and_unique_next", {})) != 13:
        raise ValueError("LF6 machine outcome mapping is incomplete")
    if decision.get("stress_status") != "TWO_STRESS_REFERENCES_SEALED_UNREAD":
        raise PermissionError("LF6 stress boundary drift")
    return contracts


def contract_identity() -> dict[str, dict[str, str]]:
    return {name: {"path": path.relative_to(ROOT).as_posix(), "sha256": _sha256_path(path)} for name, path in CONTRACT_PATHS.items()}


def array_sha256(name: str, value: np.ndarray) -> str:
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256(b"PHK_V23_LF6_ARRAY_V1\n")
    digest.update(name.encode("ascii")); digest.update(b"\n")
    digest.update(array.dtype.str.encode("ascii")); digest.update(b"\n")
    digest.update(json.dumps(list(array.shape), separators=(",", ":")).encode("ascii")); digest.update(b"\n")
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest().upper()


def semantic_ledger_sha256(array_hashes: Mapping[str, str]) -> str:
    digest = hashlib.sha256(b"PHK_V23_LF6_MATERIALIZED_LEDGER_V1\n")
    for name in sorted(array_hashes):
        digest.update(f"{name}={array_hashes[name]}\n".encode("ascii"))
    return digest.hexdigest().upper()


def rolling_batch_sha256(domain: str, values: Sequence[str]) -> str:
    digest = hashlib.sha256(domain.encode("ascii"))
    for value in values:
        digest.update(bytes.fromhex(str(value)))
    return digest.hexdigest().upper()


def _decode_hashes(array: np.ndarray) -> list[str]:
    return [bytes(value).decode("ascii") if isinstance(value, np.bytes_) else str(value) for value in array.reshape(-1)]


@dataclass(frozen=True)
class EndpointBatch:
    coordinates: torch.Tensor
    targets: torch.Tensor
    offsets: tuple[int, ...]
    role: str


class MaterializedLedger:
    """Verified, strictly ordered CPU-F arrays; never generates points."""

    def __init__(self, path: Path, *, contracts: Mapping[str, Mapping[str, Any]], qualification: Mapping[str, Any]) -> None:
        self.path = Path(path).resolve()
        binding = contracts["data"]["materialized_ledger"]
        expected = (ROOT / binding["path"]).resolve()
        if self.path != expected or not self.path.is_file() or _sha256_path(self.path) != binding["file_sha256"]:
            raise ValueError("LF6 materialized ledger file binding drift")
        qledger = qualification.get("ledger", {})
        if qledger.get("sha256") != binding["file_sha256"] or qledger.get("semantic_sha256") != binding["semantic_sha256"]:
            raise ValueError("LF6 qualification ledger binding drift")
        manifest_path = (ROOT / binding["manifest_path"]).resolve()
        if not manifest_path.is_file() or _sha256_path(manifest_path) != binding["manifest_sha256"]:
            raise ValueError("LF6 materialized ledger manifest drift")
        manifest = _read_json(manifest_path)
        if manifest.get("schema_id") != "phk-v23-lf6-materialized-ledger-manifest-v1" or manifest.get("task_id") != TASK_ID:
            raise ValueError("LF6 ledger manifest identity drift")
        with np.load(self.path, allow_pickle=False) as archive:
            if set(archive.files) != set(LEDGER_ARRAY_NAMES):
                raise ValueError("LF6 ledger array key drift")
            self.arrays = {name: np.asarray(archive[name]) for name in LEDGER_ARRAY_NAMES}
        hashes = {name: array_sha256(name, value) for name, value in self.arrays.items()}
        expected_arrays = manifest.get("arrays", {})
        for name in LEDGER_ARRAY_NAMES:
            record = expected_arrays.get(name, {})
            if hashes[name] != record.get("sha256") or list(self.arrays[name].shape) != record.get("shape") or self.arrays[name].dtype.str != record.get("dtype"):
                raise ValueError(f"LF6 ledger array drift: {name}")
        if semantic_ledger_sha256(hashes) != binding["semantic_sha256"] or manifest.get("semantic_sha256") != binding["semantic_sha256"]:
            raise ValueError("LF6 ledger semantic identity drift")
        base_hashes = _decode_hashes(self.arrays["base_batch_sha256"])
        spatial_hashes = _decode_hashes(self.arrays["spatial_batch_sha256"])
        physics_hashes = _decode_hashes(self.arrays["p0_batch_sha256"])
        for index in range(DEV_UPDATES):
            base_actual = _batch_sha256(
                torch.as_tensor(self.arrays["base_coordinates"][index], dtype=torch.float64),
                torch.as_tensor(self.arrays["base_targets"][index], dtype=torch.float64),
                metadata=f"LF2:M0:{1201 + index}:{EXPECTED_PARTITION_SHA256}",
            )
            spatial_actual = _batch_sha256(
                torch.as_tensor(self.arrays["spatial_coordinates"][index], dtype=torch.float64),
                torch.as_tensor(self.arrays["spatial_targets"][index], dtype=torch.float64),
                metadata=f"LF4:BAND:{index + 1}:{EXPECTED_PARTITION_SHA256}",
            )
            if base_actual != base_hashes[index] or spatial_actual != spatial_hashes[index]:
                raise ValueError(f"LF6 materialized development step hash drift at {index + 1}")
        for index in range(P0_UPDATES):
            windows = int(self.arrays["p0_active_windows"][index])
            tensors = [torch.as_tensor(self.arrays[f"p0_{name}"][index], dtype=torch.float64) for name in ("interior", "left", "right", "bottom", "top", "initial")]
            actual_interior = _batch_sha256(tensors[0], metadata=f"PHYSICS_INTERIOR_WINDOWS:{windows}")
            actual_boundary = _batch_sha256(*tensors[1:5], metadata=f"PHYSICS_BOUNDARY_WINDOWS:{windows}")
            actual_initial = _batch_sha256(tensors[5], metadata=f"PHYSICS_INITIAL_WINDOWS:{windows}")
            actual_batch = _batch_sha256(*tensors, metadata=f"PHYSICS_WINDOWS:{windows}")
            expected_components = (
                _decode_hashes(self.arrays["p0_interior_sha256"][index:index + 1])[0],
                _decode_hashes(self.arrays["p0_boundary_sha256"][index:index + 1])[0],
                _decode_hashes(self.arrays["p0_initial_sha256"][index:index + 1])[0],
                physics_hashes[index],
            )
            if (actual_interior, actual_boundary, actual_initial, actual_batch) != expected_components:
                raise ValueError(f"LF6 materialized physics step hash drift at {index + 1}")
        self.streams = {
            "base_400_sha256": rolling_batch_sha256("PHK_V23_LF4_BASE_DRAWS_1201_1600", base_hashes),
            "spatial_400_sha256": rolling_batch_sha256("PHK_V23_LF4_INTERFACE_BAND", spatial_hashes),
            "P0_physics_1200_sha256": rolling_batch_sha256("PHK_V23_LF0_PHYSICS_BATCHES", physics_hashes),
        }
        if self.streams["base_400_sha256"] != EXPECTED_BASE_400_SHA256 or self.streams["spatial_400_sha256"] != EXPECTED_SPATIAL_400_SHA256 or self.streams["P0_physics_1200_sha256"] != EXPECTED_P0_PHYSICS_SHA256:
            raise ValueError("LF6 materialized stream aggregate drift")
        fixed_digest = _fixed_pool_digest(self.arrays)
        if fixed_digest != EXPECTED_FIXED_POOL_SHA256:
            raise ValueError("LF6 fixed blind pool drift")
        self.base_hashes = base_hashes
        self.spatial_hashes = spatial_hashes
        self.physics_hashes = physics_hashes

    def base_batch(self, step: int, dataset: MediumMeasureDataset) -> MeasureBatch:
        index = _step_index(step, DEV_UPDATES, "development")
        return MeasureBatch(
            torch.as_tensor(self.arrays["base_coordinates"][index], dtype=torch.float64),
            torch.as_tensor(self.arrays["base_targets"][index], dtype=torch.float64),
            dict(zip(CATEGORY_NAMES, CATEGORY_QUOTAS, strict=True)),
            dict(dataset.category_masses),
            self.base_hashes[index],
        )

    def spatial_batch(self, step: int) -> ExtraBatch:
        index = _step_index(step, DEV_UPDATES, "development")
        return ExtraBatch(
            torch.as_tensor(self.arrays["spatial_coordinates"][index], dtype=torch.float64),
            torch.as_tensor(self.arrays["spatial_targets"][index], dtype=torch.float64),
            {name: 64 for name in ("C1_INNER_POSITIVE", "C1_OUTER_NEGATIVE", "C2_INNER_POSITIVE", "C2_OUTER_NEGATIVE")},
            self.spatial_hashes[index],
        )

    def endpoint_batch(self, arm: str) -> EndpointBatch:
        prefix = "uniform" if arm == DEV_U else "frontier"
        offsets = tuple(int(value) for value in self.arrays[f"{prefix}_offsets"].tolist())
        return EndpointBatch(
            torch.as_tensor(self.arrays[f"{prefix}_coordinates"], dtype=torch.float64),
            torch.as_tensor(self.arrays[f"{prefix}_targets"], dtype=torch.float64),
            offsets,
            arm,
        )

    def physics_batch(self, step: int, *, device: torch.device) -> PhysicsBatch:
        index = _step_index(step, P0_UPDATES, "physics")
        tensor = lambda name: torch.as_tensor(self.arrays[name][index], dtype=torch.float64, device=device)
        return PhysicsBatch(
            interior=tensor("p0_interior"),
            boundary={name: tensor(f"p0_{name}") for name in ("left", "right", "bottom", "top")},
            initial=tensor("p0_initial"),
            active_windows=int(self.arrays["p0_active_windows"][index]),
            refreshed=bool(self.arrays["p0_refreshed"][index]),
            interior_sha256=self._physics_hash("p0_interior_sha256", index),
            boundary_sha256=self._physics_hash("p0_boundary_sha256", index),
            initial_sha256=self._physics_hash("p0_initial_sha256", index),
            batch_sha256=self.physics_hashes[index],
        )

    def _physics_hash(self, name: str, index: int) -> str:
        return _decode_hashes(self.arrays[name][index:index + 1])[0]


def _step_index(step: int, maximum: int, label: str) -> int:
    value = int(step)
    if value < 1 or value > maximum:
        raise ValueError(f"LF6 {label} step out of range")
    return value - 1


def _fixed_pool_digest(arrays: Mapping[str, np.ndarray]) -> str:
    digest = hashlib.sha256(b"PHK_V23_LF2_FIXED_REFERENCE_BLIND_FULL_W1_W4")
    for name in ("interior", "left", "right", "bottom", "top", "initial"):
        array = np.ascontiguousarray(arrays[f"fixed_{name}"], dtype=np.float64)
        digest.update(str(tuple(array.shape)).encode("ascii"))
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest().upper()


def endpoint_logit_loss(model: PhkV22RModel, batch: EndpointBatch, *, physics: Any, device: torch.device) -> dict[str, Any]:
    coordinates = batch.coordinates.to(device=device, dtype=torch.float64)
    targets = batch.targets.to(device=device, dtype=torch.float64)
    diagnostics = model.read_only_output_diagnostics(coordinates)
    delta_star, startup, mask = phase_logit_targets(coordinates, targets[:, 2:3], physics=physics)
    if not bool(torch.all(mask)):
        raise ValueError("LF6 event-frontier endpoints unexpectedly include startup nodes")
    delta_theta = 8.0 * startup * diagnostics.latents["phase"]
    pointwise = ((delta_theta - delta_star) / LOGIT_SPAN).square().reshape(-1)
    if len(batch.offsets) != len(FRONTIER_POOL_NAMES) + 1 or batch.offsets[0] != 0 or batch.offsets[-1] != pointwise.numel():
        raise ValueError("LF6 endpoint pool offsets drift")
    per_pool = {name: torch.mean(pointwise[batch.offsets[index]:batch.offsets[index + 1]]) for index, name in enumerate(FRONTIER_POOL_NAMES)}
    if any(not bool(torch.isfinite(value)) for value in per_pool.values()):
        raise FloatingPointError("LF6 endpoint loss is non-finite")
    return {"loss": sum(per_pool.values()) / 4.0, "pool_losses": per_pool}


def _cycle(audit: Mapping[str, Any], cycle: int) -> Mapping[str, Any]:
    return audit["event_metrics"][f"cycle_{cycle}"]


def safety_gate(audit: Mapping[str, Any], lf1_b0: Mapping[str, Any], *, vt_unchanged: bool, development: bool = True) -> dict[str, Any]:
    checks: dict[str, bool] = {
        "finite": audit.get("all_values_finite") is True,
        "phase_range": audit.get("phase_range", {}).get("passed") is True,
        "potential": audit.get("potential_maximum_principle", {}).get("passed") is True,
        "phase_maximum": float(audit.get("phase_maximum", -math.inf)) >= 0.90,
        "two_cycle_events": audit.get("two_cycle_events") is True,
        "phase_weighted_mse": float(audit["weighted_errors"]["phase"]) <= PHASE_MSE_MAXIMUM,
        "V_T_bitwise_unchanged": bool(vt_unchanged) if development else True,
    }
    topology = audit["event_topology_hard_guard"]["cycles"]
    for cycle in (1, 2):
        metrics = _cycle(audit, cycle); topo = topology[cycle - 1]; prefix = f"cycle_{cycle}"
        recall = metrics.get("hard_recall"); precision = metrics.get("hard_precision"); mass = metrics.get("hard_active_mass_ratio"); timing = metrics.get("event_time_absolute_error")
        checks[f"{prefix}_recall"] = recall is not None and float(recall) >= 0.90
        checks[f"{prefix}_precision"] = precision is not None and float(precision) >= 0.80
        checks[f"{prefix}_mass"] = mass is not None and 0.80 <= float(mass) <= 1.20
        maximum = 0.010533333333333339 + 1.0e-12 if cycle == 1 else 0.004999999999999893 + 1.0e-12
        checks[f"{prefix}_timing"] = timing is not None and float(timing) <= maximum
        checks[f"{prefix}_roi_peak"] = float(topo["peak_roi_fraction"]) >= 0.02
        checks[f"{prefix}_full_peak"] = float(topo["peak_full_domain_fraction"]) <= 0.45
        checks[f"{prefix}_outside_peak"] = float(topo["peak_outside_roi_fraction"]) <= 0.10
        checks[f"{prefix}_recovery"] = float(topo["recovery_fraction"]) >= 0.70
    ratios = {}
    maxima = {"potential": 1.10, "temperature": 0.50, "phase": 0.50}
    for field, maximum in maxima.items():
        ratios[field] = float(audit["weighted_errors"][field]) / max(float(lf1_b0["weighted_errors"][field]), 1.0e-12)
        checks[f"{field}_vs_LF1_B0"] = ratios[field] <= maximum
    failed = sorted(name for name, passed in checks.items() if not passed)
    return {"passed": not failed, "checks": checks, "failed_checks": failed, "weighted_mse_ratios_to_LF1_B0": ratios}


def strict_gate(audit: Mapping[str, Any], lf1_b0: Mapping[str, Any], *, vt_unchanged: bool, development: bool = True) -> dict[str, Any]:
    safety = safety_gate(audit, lf1_b0, vt_unchanged=vt_unchanged, development=development)
    checks = dict(safety["checks"])
    for cycle in (1, 2):
        timing = _cycle(audit, cycle).get("event_time_absolute_error")
        checks[f"cycle_{cycle}_strict_timing"] = timing is not None and float(timing) <= 0.005
    failed = sorted(name for name, passed in checks.items() if not passed)
    return {"passed": not failed, "checks": checks, "failed_checks": failed, "safety_passed": safety["passed"], "weighted_mse_ratios_to_LF1_B0": safety["weighted_mse_ratios_to_LF1_B0"]}


def mechanism_outcome(arms: Mapping[str, Mapping[str, Any]]) -> str:
    if any(not bool(arms[name].get("numerical_valid")) for name in DEV_ORDER):
        return "MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID"
    if arms[DEV_U]["strict_gate"]["passed"]:
        return "GENERIC_TEMPORAL_ENDPOINT_SUFFICIENT"
    if arms[DEV_R]["strict_gate"]["passed"]:
        return "EVENT_FRONTIER_SUPPORTED"
    return "NO_RANK_SPECIFIC_INCREMENT"


def _timing_score(record: Mapping[str, Any]) -> float:
    audit = record["audit"]
    return max(float(_cycle(audit, 1)["event_time_absolute_error"]) / 0.010533333333333339, float(_cycle(audit, 2)["event_time_absolute_error"]) / 0.004999999999999893)


def select_p0_candidate(candidates: Mapping[str, Mapping[str, Any]]) -> str | None:
    """Apply strict precedence, then the frozen safety/timing/calibration rule."""
    if candidates.get(DEV_U, {}).get("strict_gate", {}).get("passed") is True:
        return DEV_U
    if candidates.get(DEV_R, {}).get("strict_gate", {}).get("passed") is True:
        return DEV_R
    eligible = [name for name in P0_CANDIDATE_ORDER if candidates.get(name, {}).get("safety_gate", {}).get("passed") is True and candidates[name].get("numerical_valid", True)]
    if not eligible:
        return None
    simplicity = {DEV_M: 0, DEV_U: 1, DEV_R: 2}
    return min(eligible, key=lambda name: (_timing_score(candidates[name]), float(candidates[name]["audit"]["weighted_errors"]["phase"]), simplicity[name]))


def p0_preservation_gate(audit: Mapping[str, Any], selected: Mapping[str, Any], lf1_b0: Mapping[str, Any]) -> dict[str, Any]:
    safety = safety_gate(audit, lf1_b0, vt_unchanged=True, development=False)
    strict = strict_gate(audit, lf1_b0, vt_unchanged=True, development=False)
    ratios = {field: float(audit["weighted_errors"][field]) / max(float(selected["weighted_errors"][field]), 1.0e-12) for field in ("potential", "temperature", "phase")}
    ratios["topology"] = float(audit["topology_weighted_loss"]) / max(float(selected["topology_weighted_loss"]), 1.0e-12)
    limits = {"potential": 1.20, "temperature": 1.05, "phase": 1.05, "topology": 1.05}
    preservation = {f"{name}_preserved": value <= limits[name] for name, value in ratios.items()}
    return {"passed": bool(safety["passed"] and all(preservation.values())), "safety_gate": safety, "strict_gate": strict, "relative_selected": ratios, "preservation_checks": preservation}


def read_cpu_qualification(path: Path) -> dict[str, Any]:
    payload = _read_json(Path(path))
    if payload.get("schema_id") != "phk-v23-lf6-cpu-qualification-v1" or payload.get("task_id") != TASK_ID or payload.get("status") != "LF6_CPU_F_QUALIFICATION_PASS" or payload.get("contracts") != contract_identity() or payload.get("gpu_execution_authorized_by_cpu_gate") is not True:
        raise PermissionError("LF6 CPU-F qualification is absent, stale, or failed")
    return payload


def _load_bound_model(path: Path, *, expected_sha256: str, initial_checkpoint: Path, physics: Any, config: Any, device: torch.device) -> tuple[PhkV22RModel, dict[str, Any]]:
    supplied = Path(path).resolve()
    if not supplied.is_file() or _sha256_path(supplied) != expected_sha256:
        raise ValueError("LF6 checkpoint input absent or hash-drifted")
    model, _ = load_lf3_t0_model(initial_checkpoint, physics=physics, config=config, device=device, expected_sha256=_sha256_path(initial_checkpoint))
    payload = torch.load(supplied, map_location=device, weights_only=False)
    if payload.get("architecture") != model.architecture_manifest():
        raise PermissionError("LF6 inherited checkpoint architecture drift")
    model.load_state_dict(payload["model_state_dict"], strict=True); model.train()
    return model, payload


def _write_checkpoint(path: Path, *, model: PhkV22RModel, optimizer: torch.optim.Optimizer, config: Any, update: int, role: str, source_identity: str, contracts: Mapping[str, Any], parent_sha256: str, physics_program_sha256: str, physics_object_sha256: str) -> Path:
    payload = _checkpoint_payload(model=model, optimizer=optimizer, config=config, update=update, program_contract_sha256=_sha256_path(V22R_PROGRAM_CONTRACT_PATH), method_contract_sha256=_sha256_path(V22R_METHOD_CONTRACT_PATH), physical_program_sha256=physics_program_sha256, physical_object_sha256=physics_object_sha256)
    payload["lf6"] = {"schema_id":"phk-v23-lf6-checkpoint-metadata-v1","task_id":TASK_ID,"role":role,"optimizer_update":int(update),"source_identity":source_identity,"contracts":dict(contracts),"parent_checkpoint_sha256":parent_sha256,"medium_labels_used":role in DEV_ORDER,"physics_residual_used":role=="P0","runtime_sampling_used":False,"stress_read":False}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        torch.save(payload, handle)
    return path


def _append(handle: Any, payload: Mapping[str, Any]) -> None:
    handle.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n"); handle.flush()


def _run_development_arm(*, arm: str, root: Path, ledger: MaterializedLedger, dataset: MediumMeasureDataset, initial_checkpoint: Path, contracts: Mapping[str, Any], qualification: Mapping[str, Any], physics: Any, config: Any, device: torch.device, source_identity: str, physics_program_sha256: str, physics_object_sha256: str, started: float) -> tuple[dict[str, Any], Path]:
    directory = root / ("dev_u" if arm == DEV_U else "dev_r"); directory.mkdir(parents=True, exist_ok=False)
    model, _ = load_lf3_t0_model(initial_checkpoint, physics=physics, config=config, device=device, expected_sha256=contracts["data"]["initial_checkpoint"]["sha256"])
    for field in ("potential", "temperature"):
        model.encoders[field].requires_grad_(False); model.heads[field].requires_grad_(False)
    phase_parameters = tuple(model.encoders["phase"].parameters()) + tuple(model.heads["phase"].parameters())
    vt_before = {field: _field_state_sha256(model, field) for field in ("potential", "temperature")}
    optimizer = torch.optim.Adam(phase_parameters, lr=1.0e-3, betas=(0.9, 0.999), eps=1.0e-8, weight_decay=0.0, amsgrad=False)
    endpoint = ledger.endpoint_batch(arm); final_audit: dict[str, Any] | None = None; numerical_valid = True; executed = 0
    telemetry_path = directory / "telemetry.jsonl"; batches_path = directory / "batch_ledger.jsonl"
    with telemetry_path.open("x", encoding="utf-8", newline="\n") as telemetry, batches_path.open("x", encoding="utf-8", newline="\n") as batches:
        for step in range(1, DEV_UPDATES + 1):
            optimizer.zero_grad(set_to_none=True)
            base = ledger.base_batch(step, dataset); spatial = ledger.spatial_batch(step)
            base_loss = measure_decoupled_terms(model, base, physics=physics, device=device)["phase_logit"]
            spatial_loss = normalized_logit_mse(model, spatial, physics=physics, device=device)
            endpoint_terms = endpoint_logit_loss(model, endpoint, physics=physics, device=device)
            total = 0.50 * base_loss + 0.25 * spatial_loss + 0.25 * endpoint_terms["loss"]
            if not bool(torch.isfinite(total)):
                numerical_valid = False; break
            total.backward(); grad_norm = _gradient_group_norm(phase_parameters)
            if not math.isfinite(grad_norm):
                numerical_valid = False; break
            torch.nn.utils.clip_grad_norm_(phase_parameters, 10.0); optimizer.step(); executed = step
            _append(batches, {"step":step,"base_sha256":base.batch_sha256,"spatial_sha256":spatial.batch_sha256,"endpoint_semantic_sha256":contracts["data"]["materialized_ledger"]["uniform_endpoint_sha256" if arm == DEV_U else "frontier_endpoint_sha256"]})
            if step == 1 or step % 50 == 0:
                final_audit = full_medium_audit(model, dataset, device=device)
                _append(telemetry, {"arm":arm,"step":step,"L_base":float(base_loss.detach().cpu()),"L_spatial":float(spatial_loss.detach().cpu()),"L_endpoint":float(endpoint_terms["loss"].detach().cpu()),"L_total":float(total.detach().cpu()),"endpoint_pool_losses":{name:float(value.detach().cpu()) for name,value in endpoint_terms["pool_losses"].items()},"gradient_norm_before_clip":grad_norm,"audit":final_audit})
            if time.perf_counter() - started > float(contracts["program"]["hard_limits"]["maximum_wall_seconds"]):
                raise RuntimeError("LF6_RUN_BOUND_EXCEEDED")
    vt_after = {field: _field_state_sha256(model, field) for field in ("potential", "temperature")}; vt_unchanged = vt_before == vt_after
    if final_audit is None:
        final_audit = full_medium_audit(model, dataset, device=device)
    numerical_valid = bool(numerical_valid and executed == DEV_UPDATES and vt_unchanged and final_audit["all_values_finite"] and final_audit["phase_range"]["passed"] and final_audit["potential_maximum_principle"]["passed"])
    safety = safety_gate(final_audit, qualification["lf1_b0_full_medium_audit"], vt_unchanged=vt_unchanged)
    strict = strict_gate(final_audit, qualification["lf1_b0_full_medium_audit"], vt_unchanged=vt_unchanged)
    checkpoint = _write_checkpoint(directory/"checkpoint.pt", model=model, optimizer=optimizer, config=config, update=executed, role=arm, source_identity=source_identity, contracts=contract_identity(), parent_sha256=_sha256_path(initial_checkpoint), physics_program_sha256=physics_program_sha256, physics_object_sha256=physics_object_sha256)
    prediction = write_prediction_carrier(checkpoint_path=checkpoint, output_path=directory/"prediction.npz", device_name=str(device))
    gate_payload = {"arm":arm,"numerical_valid":numerical_valid,"safety_gate":safety,"strict_gate":strict,"audit":final_audit,"V_T_state_sha256":{"before":vt_before,"after":vt_after}}
    _write_json_exclusive(directory/"gate.json", gate_payload); _write_json_exclusive(directory/"exit.json", {"returncode":0,"executed_updates":executed,"numerical_valid":numerical_valid})
    result = {**gate_payload,"executed_updates":executed,"checkpoint_sha256":_sha256_path(checkpoint),"prediction_sha256":_sha256_path(prediction),"batch_streams":{"base":ledger.streams["base_400_sha256"],"spatial":ledger.streams["spatial_400_sha256"]}}
    del optimizer, model; torch.cuda.empty_cache()
    return result, checkpoint


def execute_reference_blind_gpu_campaign(*, output_root: Path, medium_carrier: Path, initial_checkpoint: Path, materialized_ledger: Path, dev_m_checkpoint: Path | None, cpu_qualification_path: Path, device_name: str, source_identity: str) -> dict[str, Any]:
    contracts = load_contracts(); qualification = read_cpu_qualification(cpu_qualification_path)
    if not device_name.startswith("cuda") or not torch.cuda.is_available():
        raise RuntimeError("LF6 requires CUDA")
    device = torch.device(device_name); gpu_name = torch.cuda.get_device_name(device)
    if gpu_name != "Tesla V100-PCIE-32GB":
        raise RuntimeError("LF6 requires Tesla V100-PCIE-32GB")
    root = Path(output_root).resolve(); root.mkdir(parents=True, exist_ok=True)
    if any((root/name).exists() for name in ("dev_u", "dev_r", "p0", "run_summary.json")):
        raise FileExistsError("LF6 scientific outputs already exist")
    config = build_training_config(device_name); physics, physics_program_sha256, physics_object_sha256 = load_case_physics(config.case_control)
    dataset = load_medium_dataset(Path(medium_carrier), physics=physics, contracts=contracts)
    if dataset.partition_sha256 != qualification["partition_sha256"]:
        raise ValueError("LF6 qualified partition drift")
    ledger = MaterializedLedger(materialized_ledger, contracts=contracts, qualification=qualification)
    started = time.perf_counter(); started_at = datetime.now(timezone.utc).isoformat()
    random.seed(17); np.random.seed(17); torch.manual_seed(17); torch.cuda.manual_seed_all(17)
    arms: dict[str, Any] = {}; checkpoints: dict[str, Path] = {}
    for arm in DEV_ORDER:
        arms[arm], checkpoints[arm] = _run_development_arm(arm=arm, root=root, ledger=ledger, dataset=dataset, initial_checkpoint=Path(initial_checkpoint), contracts=contracts, qualification=qualification, physics=physics, config=config, device=device, source_identity=source_identity, physics_program_sha256=physics_program_sha256, physics_object_sha256=physics_object_sha256, started=started)
    mechanism = mechanism_outcome(arms)
    dev_m_audit = qualification["dev_m_full_medium_audit"]
    dev_m_safety = safety_gate(dev_m_audit, qualification["lf1_b0_full_medium_audit"], vt_unchanged=True)
    dev_m_strict = strict_gate(dev_m_audit, qualification["lf1_b0_full_medium_audit"], vt_unchanged=True)
    candidates = {DEV_M:{"audit":dev_m_audit,"safety_gate":dev_m_safety,"strict_gate":dev_m_strict,"numerical_valid":qualification.get("dev_m_input_valid") is True}, **arms}
    selected = select_p0_candidate(candidates)
    p0_result: dict[str, Any] | None = None
    if selected is not None:
        if selected == DEV_M:
            if dev_m_checkpoint is None:
                raise PermissionError("LF6 selected exact DEV-M fallback but no explicitly authorized checkpoint was supplied")
            selected_checkpoint = Path(dev_m_checkpoint)
            if _sha256_path(selected_checkpoint) != contracts["data"]["LF4_DEV_M"]["sha256"]:
                raise ValueError("LF6 DEV-M fallback hash drift")
        else:
            selected_checkpoint = checkpoints[selected]
        directory = root/"p0"; directory.mkdir(parents=True, exist_ok=False)
        model, _ = _load_bound_model(selected_checkpoint, expected_sha256=_sha256_path(selected_checkpoint), initial_checkpoint=Path(initial_checkpoint), physics=physics, config=config, device=device)
        phase_parameters = tuple(model.encoders["phase"].parameters()) + tuple(model.heads["phase"].parameters())
        for parameter in phase_parameters:
            parameter.requires_grad_(False)
        phase_before = _phase_state_sha256(model)
        optimizer = torch.optim.Adam(model.parameters(), lr=1.0e-3, betas=(0.9,0.999), eps=1.0e-8, weight_decay=0.0, amsgrad=False)
        telemetry_path=directory/"telemetry.jsonl"; batch_path=directory/"batch_ledger.jsonl"; final_audit=None; step550=None; numerical_valid=True; executed=0
        with telemetry_path.open("x",encoding="utf-8",newline="\n") as telemetry, batch_path.open("x",encoding="utf-8",newline="\n") as batches:
            for step in range(1,P0_UPDATES+1):
                if step == P0_PHASE_FREEZE_STEPS + 1:
                    if _phase_state_sha256(model) != phase_before or sum(parameter in optimizer.state for parameter in phase_parameters) != 0:
                        raise RuntimeError("LF6 P0 phase freeze identity drift")
                    for parameter in phase_parameters:
                        parameter.requires_grad_(True)
                optimizer.zero_grad(set_to_none=True); batch=ledger.physics_batch(step,device=device); loss,components=_physics_objective(model,batch,config)
                if not bool(torch.isfinite(loss)):
                    numerical_valid=False; break
                loss.backward(); trainable=tuple(parameter for parameter in model.parameters() if parameter.requires_grad); grad_norm=float(torch.nn.utils.clip_grad_norm_(trainable,10.0).detach().cpu())
                if not math.isfinite(grad_norm):
                    numerical_valid=False; break
                optimizer.step(); executed=step
                _append(batches,{"step":step,"interior_coordinate_sha256":batch.interior_sha256,"boundary_coordinate_sha256":batch.boundary_sha256,"initial_coordinate_sha256":batch.initial_sha256,"batch_sha256":batch.batch_sha256})
                if step==1 or step%50==0 or step in {550,551,1200}:
                    final_audit=full_medium_audit(model,dataset,device=device); _append(telemetry,{"step":step,**components,"total_loss":float(loss.detach().cpu()),"gradient_norm_before_clip":grad_norm,"phase_sha256":_phase_state_sha256(model),"phase_frozen":step<=550,"audit":final_audit})
                if step==550:
                    state_entries=sum(parameter in optimizer.state for parameter in phase_parameters); current=_phase_state_sha256(model)
                    step550={"phase_before_sha256":phase_before,"phase_after_sha256":current,"bitwise_preserved":current==phase_before,"phase_optimizer_state_entries":state_entries,"physics_hash_prefix":rolling_batch_sha256("PHK_V23_LF0_PHYSICS_BATCHES",ledger.physics_hashes[:550]),"finite":bool(final_audit and final_audit["all_values_finite"]),"potential_valid":bool(final_audit and final_audit["potential_maximum_principle"]["passed"])}
                    if not step550["bitwise_preserved"] or state_entries != 0:
                        raise RuntimeError("LF6 P0 step550 identity drift")
                if time.perf_counter()-started>float(contracts["program"]["hard_limits"]["maximum_wall_seconds"]):
                    raise RuntimeError("LF6_RUN_BOUND_EXCEEDED")
        if final_audit is None:
            final_audit=full_medium_audit(model,dataset,device=device)
        numerical_valid=bool(numerical_valid and executed==P0_UPDATES and final_audit["all_values_finite"] and final_audit["phase_range"]["passed"] and final_audit["potential_maximum_principle"]["passed"])
        preservation=p0_preservation_gate(final_audit,candidates[selected]["audit"],qualification["lf1_b0_full_medium_audit"])
        checkpoint=_write_checkpoint(directory/"checkpoint.pt",model=model,optimizer=optimizer,config=config,update=executed,role="P0",source_identity=source_identity,contracts=contract_identity(),parent_sha256=_sha256_path(selected_checkpoint),physics_program_sha256=physics_program_sha256,physics_object_sha256=physics_object_sha256)
        prediction=write_prediction_carrier(checkpoint_path=checkpoint,output_path=directory/"prediction.npz",device_name=device_name)
        gate_payload={"numerical_valid":numerical_valid,"selected_role":selected,"audit":final_audit,"preservation_gate":preservation,"strict_gate":preservation["strict_gate"],"step550":step550,"physics_stream_sha256":ledger.streams["P0_physics_1200_sha256"]}
        _write_json_exclusive(directory/"gate.json",gate_payload); _write_json_exclusive(directory/"exit.json",{"returncode":0,"executed_updates":executed,"numerical_valid":numerical_valid})
        p0_result={**gate_payload,"executed_updates":executed,"checkpoint_sha256":_sha256_path(checkpoint),"prediction_sha256":_sha256_path(prediction)}
    artifacts={}
    for arm,folder in ((DEV_U,"dev_u"),(DEV_R,"dev_r")):
        for key,name in (("telemetry","telemetry.jsonl"),("batch_ledger","batch_ledger.jsonl"),("checkpoint","checkpoint.pt"),("prediction","prediction.npz"),("gate","gate.json"),("exit","exit.json")):
            artifacts[f"{arm}_{key}"]=_artifact_record(root/folder/name,root)
    if p0_result is not None:
        for key,name in (("telemetry","telemetry.jsonl"),("batch_ledger","batch_ledger.jsonl"),("checkpoint","checkpoint.pt"),("prediction","prediction.npz"),("gate","gate.json"),("exit","exit.json")):
            artifacts[f"P0_{key}"]=_artifact_record(root/"p0"/name,root)
    if any(not arms[name]["numerical_valid"] for name in DEV_ORDER): status="LF6_MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID"
    elif selected is None: status="LF6_NO_VALID_SAFETY_CARRIER"
    elif p0_result is not None and not p0_result["numerical_valid"]: status="LF6_P0_NUMERICAL_OR_IDENTITY_INVALID"
    else: status="LF6_REFERENCE_BLIND_GPU_CAMPAIGN_COMPLETE"
    summary={"schema_id":"phk-v23-lf6-reference-blind-run-summary-v1","task_id":TASK_ID,"title":TITLE,"status":status,"started_at_utc":started_at,"finished_at_utc":datetime.now(timezone.utc).isoformat(),"source_identity":source_identity,"gpu":gpu_name,"dtype":"FLOAT64","seed":17,"optimizer_updates":sum(int(arms[name]["executed_updates"]) for name in DEV_ORDER)+(int(p0_result["executed_updates"]) if p0_result else 0),"development":arms,"mechanism_outcome":mechanism,"candidates":candidates,"selected_role":selected,"P0_disposition":"EXECUTED" if p0_result else "NOT_RUN_NO_VALID_SAFETY_CARRIER","P0":p0_result,"ledger":{"path":str(Path(materialized_ledger)),"sha256":_sha256_path(Path(materialized_ledger)),"semantic_sha256":contracts["data"]["materialized_ledger"]["semantic_sha256"],"streams":ledger.streams},"wall_seconds":time.perf_counter()-started,"artifacts":artifacts,"prediction_reference_free":True,"fine_extra_lf_only_evaluator_stress_read":False}
    _write_json_exclusive(root/"run_summary.json",summary); return summary


def _parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root",type=Path,required=True); parser.add_argument("--medium-carrier",type=Path,required=True); parser.add_argument("--initial-checkpoint",type=Path,required=True); parser.add_argument("--materialized-ledger",type=Path,required=True); parser.add_argument("--dev-m-checkpoint",type=Path); parser.add_argument("--cpu-qualification",type=Path,required=True); parser.add_argument("--device",default="cuda:0"); parser.add_argument("--source-identity",required=True)
    return parser


def main(argv: Sequence[str] | None=None) -> int:
    args=_parser().parse_args(argv); summary=execute_reference_blind_gpu_campaign(output_root=args.output_root,medium_carrier=args.medium_carrier,initial_checkpoint=args.initial_checkpoint,materialized_ledger=args.materialized_ledger,dev_m_checkpoint=args.dev_m_checkpoint,cpu_qualification_path=args.cpu_qualification,device_name=args.device,source_identity=args.source_identity); print(json.dumps({"status":summary["status"],"optimizer_updates":summary["optimizer_updates"],"mechanism_outcome":summary["mechanism_outcome"],"selected_role":summary["selected_role"]},sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["DEV_M","DEV_R","DEV_U","DEV_ORDER","FRONTIER_POOL_NAMES","LEDGER_ARRAY_NAMES","MaterializedLedger","TASK_ID","array_sha256","contract_identity","endpoint_logit_loss","execute_reference_blind_gpu_campaign","load_contracts","mechanism_outcome","p0_preservation_gate","rolling_batch_sha256","safety_gate","select_p0_candidate","semantic_ledger_sha256","strict_gate"]
