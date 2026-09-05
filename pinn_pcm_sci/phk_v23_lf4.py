"""PHK-V2.3 LF4 matched interface-band mechanism screen and conditional P0."""

from __future__ import annotations

import argparse
from collections import deque
from dataclasses import asdict, dataclass
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
import torch.nn.functional as functional

from .phk_v22r_pinn import POTENTIAL_TRANSFORM_EXACT_TOP_RANGE_PRESERVING, PhkV22RModel
from .phk_v22r_prediction import write_prediction_carrier
from .phk_v22r_training import (
    METHOD_CONTRACT_PATH as V22R_METHOD_CONTRACT_PATH,
    PROGRAM_CONTRACT_PATH as V22R_PROGRAM_CONTRACT_PATH,
    ROOT,
    _checkpoint_payload,
    load_case_physics,
)
from .phk_v23_lf0 import (
    LF0PhysicsBatchStream,
    _artifact_record,
    _physics_objective,
    _read_json,
    _sha256_path,
    _write_json_exclusive,
)
from .phk_v23_lf1 import build_range_preserving_model
from .phk_v23_lf2 import (
    CATEGORY_NAMES,
    CATEGORY_QUOTAS,
    M0_SEEDS,
    MeasureBatch,
    MeasureCalibratedBatchStream,
    MediumMeasureDataset,
    _batch_sha256,
    _predict_medium,
    load_medium_dataset,
)
from .phk_v23_lf3 import (
    CLIP_EPSILON,
    LOGIT_SPAN,
    TASK_ID as LF3_TASK_ID,
    T0_STAGE as LF3_T0_STAGE,
    _phase_state_sha256,
    _state_sha256,
    build_training_config,
    carrier_gate as lf3_carrier_gate,
    full_medium_audit,
    measure_decoupled_terms,
    phase_logit_targets,
    startup_factor,
)


TASK_ID = "PHK_V23_LF4_THRESHOLD_ALIGNED_INTERFACE_BAND_MECHANISM_AND_CONDITIONAL_PHYSICS_PILOT_EXECUTE"
TITLE = "PHK-V2.3 LF4 threshold-aligned two-sided interface-band mechanism screen and conditional physics pilot"
ARM_G = "DEV_G_GLOBAL_MSE_CONTROL"
ARM_M = "DEV_M_INTERFACE_BAND_MSE"
ARM_C = "DEV_C_THRESHOLD_ALIGNED_INTERFACE"
ARM_ORDER = (ARM_G, ARM_M, ARM_C)
ARM_SIMPLE_ORDER = {ARM_G: 0, ARM_M: 1, ARM_C: 2}
BAND_POOL_NAMES = (
    "C1_INNER_POSITIVE",
    "C1_OUTER_NEGATIVE",
    "C2_INNER_POSITIVE",
    "C2_OUTER_NEGATIVE",
)
DEV_UPDATES = 400
P0_UPDATES = 1200
P0_PHASE_FREEZE_STEPS = 550
GLOBAL_EXTRA_SEED = 17401
BAND_SEEDS = (17411, 17412, 17413, 17414)
EXPECTED_PARTITION_SHA256 = "EFD70886DD85AC467F06F38B48FB0EE6C0132471CE74817E3A4D68E752B7A515"
EXPECTED_LF3_PREFIX_SHA256 = "6E9957E861BE0FD10E19A1585635C7B2C323077D89908159B1736734FB548F28"
EXPECTED_P0_STREAM_SHA256 = "536E6706A0B68EBB1277A97F402D273AFA2EA1E0B27106F26CB4222B7EC05C53"

PROGRAM_CONTRACT_PATH = ROOT / "configs/phk_v23/program_contract_lf4_interface_band.json"
METHOD_CONTRACT_PATH = ROOT / "configs/phk_v23/method_contract_lf4_interface_band.json"
DATA_CONTRACT_PATH = ROOT / "configs/phk_v23/data_contract_lf4_interface_band.json"
DECISION_CONTRACT_PATH = ROOT / "configs/phk_v23/decision_contract_lf4_interface_band.json"
LF3_DECISION_CONTRACT_PATH = ROOT / "configs/phk_v23/decision_contract_lf3_phase_latent_carrier.json"
CONTRACT_PATHS = {
    "program": PROGRAM_CONTRACT_PATH,
    "method": METHOD_CONTRACT_PATH,
    "data": DATA_CONTRACT_PATH,
    "decision": DECISION_CONTRACT_PATH,
}
EXPECTED_SCHEMAS = {
    "program": "phk-v23-lf4-program-contract-v1",
    "method": "phk-v23-lf4-method-contract-v1",
    "data": "phk-v23-lf4-data-contract-v1",
    "decision": "phk-v23-lf4-decision-contract-v1",
}


def load_contracts(*, require_stream_freeze: bool = True) -> dict[str, dict[str, Any]]:
    contracts = {name: _read_json(path) for name, path in CONTRACT_PATHS.items()}
    for name, schema in EXPECTED_SCHEMAS.items():
        if contracts[name].get("schema_id") != schema:
            raise ValueError(f"unsupported LF4 {name} contract")
    rel = {name: path.relative_to(ROOT).as_posix() for name, path in CONTRACT_PATHS.items()}
    if contracts["program"].get("phase_id") != TASK_ID:
        raise ValueError("LF4 task identity drift")
    if any(
        contracts[name].get("program_contract") != rel["program"]
        for name in ("method", "data", "decision")
    ):
        raise ValueError("LF4 program binding drift")
    decision = contracts["decision"]
    if decision.get("method_contract") != rel["method"] or decision.get("data_contract") != rel["data"]:
        raise ValueError("LF4 decision binding drift")
    limits = contracts["program"]["hard_limits"]
    if limits.get("maximum_scientific_gpu_trajectories") != 4 or limits.get("maximum_optimizer_updates") != 2400:
        raise ValueError("LF4 run bounds drift")
    common = contracts["method"]["common_identity"]
    if common.get("dtype") != "FLOAT64" or common.get("seed") != 17 or float(common.get("clip_epsilon")) != CLIP_EPSILON:
        raise ValueError("LF4 common identity drift")
    data = contracts["data"]
    if data["target_measure"].get("partition_sha256") != EXPECTED_PARTITION_SHA256:
        raise ValueError("LF4 partition identity drift")
    if tuple(data["base_stream"].get("quota", ())) != CATEGORY_QUOTAS or tuple(data["base_stream"].get("seeds", ())) != M0_SEEDS:
        raise ValueError("LF4 base stream drift")
    if tuple(data["band_stream"].get("seeds", ())) != BAND_SEEDS or tuple(data["band_stream"].get("pool_order", ())) != BAND_POOL_NAMES:
        raise ValueError("LF4 band stream drift")
    if int(data["global_extra_stream"].get("seed")) != GLOBAL_EXTRA_SEED:
        raise ValueError("LF4 global stream drift")
    if require_stream_freeze:
        frozen = (
            data["base_stream"].get("development_window_sha256"),
            data["base_stream"].get("rolling_1600_sha256"),
            data["global_extra_stream"].get("rolling_sha256"),
            data["band_stream"].get("rolling_sha256"),
        )
        if any(not isinstance(value, str) or value.startswith("PENDING") for value in frozen):
            raise PermissionError("LF4 stream identities are not frozen")
    if len(decision.get("machine_outcomes_and_unique_next", {})) != 13:
        raise ValueError("LF4 machine outcome mapping is incomplete")
    if decision.get("stress_status") != "TWO_STRESS_REFERENCES_SEALED_UNREAD":
        raise PermissionError("LF4 stress boundary drift")
    return contracts


def contract_identity() -> dict[str, dict[str, str]]:
    return {
        name: {"path": path.relative_to(ROOT).as_posix(), "sha256": _sha256_path(path)}
        for name, path in CONTRACT_PATHS.items()
    }


@dataclass(frozen=True)
class ExtraBatch:
    coordinates: torch.Tensor
    targets: torch.Tensor
    pool_counts: Mapping[str, int]
    batch_sha256: str


class InterfaceBandDataset:
    """Four nonperiodic, two-sided teacher-interface pools on W1 and W3."""

    def __init__(self, dataset: MediumMeasureDataset) -> None:
        self.dataset = dataset
        x_values = np.unique(dataset.cell_x)
        z_values = np.unique(dataset.cell_z)
        if x_values.size * z_values.size != dataset.cell_count:
            raise ValueError("LF4 medium cells are not a complete rectangular grid")
        lookup = {(float(x), float(z)): index for index, (x, z) in enumerate(zip(dataset.cell_x, dataset.cell_z, strict=True))}
        self.neighbours: list[tuple[int, ...]] = []
        for x, z in zip(dataset.cell_x, dataset.cell_z, strict=True):
            ix = int(np.searchsorted(x_values, x)); iz = int(np.searchsorted(z_values, z))
            adjacent: list[int] = []
            for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nx, nz = ix + dx, iz + dz
                if 0 <= nx < x_values.size and 0 <= nz < z_values.size:
                    adjacent.append(lookup[(float(x_values[nx]), float(z_values[nz]))])
            self.neighbours.append(tuple(adjacent))
        phase = dataset.fields["phase"]
        pools: dict[str, list[int]] = {name: [] for name in BAND_POOL_NAMES}
        for cycle, window in ((1, "W1"), (2, "W3")):
            for time_index in np.flatnonzero(dataset.window_time_masks[window]):
                labels = phase[time_index] >= 0.5
                for cell_index, adjacent in enumerate(self.neighbours):
                    if labels[cell_index] and any(not labels[j] for j in adjacent):
                        pools[f"C{cycle}_INNER_POSITIVE"].append(time_index * dataset.cell_count + cell_index)
                    elif (not labels[cell_index]) and any(labels[j] for j in adjacent):
                        pools[f"C{cycle}_OUTER_NEGATIVE"].append(time_index * dataset.cell_count + cell_index)
        self.pool_indices: dict[str, np.ndarray] = {}
        self.pool_counts: dict[str, int] = {}
        self.pool_masses: dict[str, float] = {}
        self.pool_cdf: dict[str, torch.Tensor] = {}
        self.pool_hashes: dict[str, str] = {}
        for name in BAND_POOL_NAMES:
            indices = np.asarray(pools[name], dtype=np.int64)
            if indices.size == 0:
                raise ValueError(f"LF4 boundary pool is empty: {name}")
            weights = dataset.node_weights[indices]
            mass = float(weights.sum())
            probabilities = weights / mass
            cdf = np.cumsum(probabilities); cdf[-1] = 1.0
            digest = hashlib.sha256(f"PHK_V23_LF4_{name}".encode("ascii"))
            digest.update(indices.astype("<i8", copy=False).tobytes())
            digest.update(probabilities.astype("<f8", copy=False).tobytes())
            self.pool_indices[name] = indices
            self.pool_counts[name] = int(indices.size)
            self.pool_masses[name] = mass
            self.pool_cdf[name] = torch.as_tensor(cdf, dtype=torch.float64)
            self.pool_hashes[name] = digest.hexdigest().upper()

    def sample(self, name: str, unit: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        values = unit.detach().cpu().to(torch.float64).reshape(-1)
        selected = torch.searchsorted(self.pool_cdf[name], values, right=True)
        selected = selected.clamp_max(self.pool_counts[name] - 1).numpy()
        indices = self.pool_indices[name][selected]
        return (
            torch.as_tensor(self.dataset.coordinates[indices], dtype=torch.float64),
            torch.as_tensor(self.dataset.targets[indices], dtype=torch.float64),
        )


class BaseDevelopmentStream:
    def __init__(self, dataset: MediumMeasureDataset) -> None:
        self.stream = MeasureCalibratedBatchStream(dataset, role="M0")
        for step in range(1, 1201):
            self.stream.draw(step)
        if self.stream.rolling_sha256 != EXPECTED_LF3_PREFIX_SHA256:
            raise ValueError("LF4 base stream prefix drift")
        self.local_step = 0
        self._window = hashlib.sha256(b"PHK_V23_LF4_BASE_DRAWS_1201_1600")

    @property
    def window_sha256(self) -> str:
        return self._window.copy().hexdigest().upper()

    @property
    def rolling_1600_sha256(self) -> str:
        return self.stream.rolling_sha256

    def draw(self, local_step: int) -> MeasureBatch:
        if int(local_step) != self.local_step + 1:
            raise ValueError("LF4 base development stream call-order drift")
        batch = self.stream.draw(1200 + int(local_step))
        self._window.update(bytes.fromhex(batch.batch_sha256))
        self.local_step = int(local_step)
        return batch


class GlobalExtraStream:
    def __init__(self, dataset: MediumMeasureDataset) -> None:
        self.dataset = dataset
        cdf = np.cumsum(dataset.node_weights); cdf[-1] = 1.0
        self.cdf = torch.as_tensor(cdf, dtype=torch.float64)
        self.engine = torch.quasirandom.SobolEngine(1, scramble=True, seed=GLOBAL_EXTRA_SEED)
        self.local_step = 0
        self._rolling = hashlib.sha256(b"PHK_V23_LF4_GLOBAL_EXTRA_TARGET_MEASURE")

    @property
    def rolling_sha256(self) -> str:
        return self._rolling.copy().hexdigest().upper()

    def draw(self, local_step: int) -> ExtraBatch:
        if int(local_step) != self.local_step + 1:
            raise ValueError("LF4 global stream call-order drift")
        unit = self.engine.draw(256, dtype=torch.float64).reshape(-1)
        selected = torch.searchsorted(self.cdf, unit, right=True).clamp_max(self.dataset.node_count - 1).numpy()
        coordinates = torch.as_tensor(self.dataset.coordinates[selected], dtype=torch.float64)
        targets = torch.as_tensor(self.dataset.targets[selected], dtype=torch.float64)
        digest = _batch_sha256(coordinates, targets, metadata=f"LF4:GLOBAL_EXTRA:{local_step}:{self.dataset.partition_sha256}")
        self._rolling.update(bytes.fromhex(digest)); self.local_step = int(local_step)
        return ExtraBatch(coordinates, targets, {"GLOBAL_EXTRA": 256}, digest)


class BandStream:
    def __init__(self, band: InterfaceBandDataset) -> None:
        self.band = band
        self.engines = tuple(torch.quasirandom.SobolEngine(1, scramble=True, seed=seed) for seed in BAND_SEEDS)
        self.local_step = 0
        self._rolling = hashlib.sha256(b"PHK_V23_LF4_INTERFACE_BAND")

    @property
    def rolling_sha256(self) -> str:
        return self._rolling.copy().hexdigest().upper()

    def draw(self, local_step: int) -> ExtraBatch:
        if int(local_step) != self.local_step + 1:
            raise ValueError("LF4 band stream call-order drift")
        coordinates: list[torch.Tensor] = []; targets: list[torch.Tensor] = []
        for name, engine in zip(BAND_POOL_NAMES, self.engines, strict=True):
            xy, value = self.band.sample(name, engine.draw(64, dtype=torch.float64).reshape(-1))
            coordinates.append(xy); targets.append(value)
        joined_coordinates = torch.cat(coordinates); joined_targets = torch.cat(targets)
        digest = _batch_sha256(joined_coordinates, joined_targets, metadata=f"LF4:BAND:{local_step}:{self.band.dataset.partition_sha256}")
        self._rolling.update(bytes.fromhex(digest)); self.local_step = int(local_step)
        return ExtraBatch(joined_coordinates, joined_targets, {name: 64 for name in BAND_POOL_NAMES}, digest)


def precompute_stream_identities(dataset: MediumMeasureDataset) -> dict[str, str]:
    band = InterfaceBandDataset(dataset)
    base = BaseDevelopmentStream(dataset); global_stream = GlobalExtraStream(dataset); band_stream = BandStream(band)
    matched = hashlib.sha256(b"PHK_V23_LF4_MATCHED_BASE_PLUS_EXTRA")
    for step in range(1, DEV_UPDATES + 1):
        base_batch = base.draw(step); global_batch = global_stream.draw(step); band_batch = band_stream.draw(step)
        matched.update(bytes.fromhex(base_batch.batch_sha256)); matched.update(bytes.fromhex(band_batch.batch_sha256))
    return {
        "lf3_prefix_1200_sha256": EXPECTED_LF3_PREFIX_SHA256,
        "base_window_1201_1600_sha256": base.window_sha256,
        "base_rolling_1600_sha256": base.rolling_1600_sha256,
        "global_extra_400_sha256": global_stream.rolling_sha256,
        "band_400_sha256": band_stream.rolling_sha256,
        "matched_base_band_400_sha256": matched.hexdigest().upper(),
    }


def normalized_logit_mse(model: PhkV22RModel, batch: ExtraBatch, *, physics: Any, device: torch.device) -> torch.Tensor:
    coordinates = batch.coordinates.to(device=device, dtype=torch.float64)
    target = batch.targets.to(device=device, dtype=torch.float64)
    diagnostics = model.read_only_output_diagnostics(coordinates)
    delta_star, startup, mask = phase_logit_targets(coordinates, target[:, 2:3], physics=physics)
    delta_theta = 8.0 * startup * diagnostics.latents["phase"]
    selected = ((delta_theta - delta_star) / LOGIT_SPAN).square().reshape(-1)[mask.reshape(-1)]
    if selected.numel() == 0:
        raise ValueError("LF4 extra batch has no post-startup teacher nodes")
    return torch.mean(selected)


def band_losses(model: PhkV22RModel, batch: ExtraBatch, *, physics: Any, device: torch.device) -> dict[str, Any]:
    coordinates = batch.coordinates.to(device=device, dtype=torch.float64)
    target = batch.targets.to(device=device, dtype=torch.float64)
    diagnostics = model.read_only_output_diagnostics(coordinates)
    delta_star, startup, mask = phase_logit_targets(coordinates, target[:, 2:3], physics=physics)
    if not bool(torch.all(mask)):
        raise ValueError("LF4 interface band unexpectedly contains startup nodes")
    delta_theta = 8.0 * startup * diagnostics.latents["phase"]
    pointwise_mse = ((delta_theta - delta_star) / LOGIT_SPAN).square().reshape(-1)
    initial = physics.initial_phase(coordinates).clamp(CLIP_EPSILON, 1.0 - CLIP_EPSILON)
    z_theta = torch.logit(initial) + delta_theta
    pool_mse: dict[str, torch.Tensor] = {}; pool_cls: dict[str, torch.Tensor] = {}
    offset = 0
    for name in BAND_POOL_NAMES:
        stop = offset + 64
        pool_mse[name] = torch.mean(pointwise_mse[offset:stop])
        logits = z_theta[offset:stop]
        pool_cls[name] = torch.mean(functional.softplus(-logits) if name.endswith("POSITIVE") else functional.softplus(logits)) / math.log(2.0)
        offset = stop
    return {
        "mse": sum(pool_mse.values()) / 4.0,
        "classification": sum(pool_cls.values()) / 4.0,
        "pool_mse": pool_mse,
        "pool_classification": pool_cls,
    }


def boundary_geometry_report(dataset: MediumMeasureDataset, band: InterfaceBandDataset, phase_prediction: np.ndarray) -> dict[str, Any]:
    prediction = np.asarray(phase_prediction, dtype=np.float64).reshape(dataset.time.size, dataset.cell_count)
    if not np.isfinite(prediction).all():
        raise ValueError("LF4 geometry prediction is non-finite")
    teacher = dataset.fields["phase"] >= 0.5; predicted = prediction >= 0.5
    window = np.broadcast_to((dataset.window_time_masks["W1"] | dataset.window_time_masks["W3"])[:, None], teacher.shape)
    weights = dataset.node_weights.reshape(teacher.shape)
    tp = window & teacher & predicted; fn = window & teacher & ~predicted; fp = window & ~teacher & predicted
    weighted_tp = float(weights[tp].sum()); weighted_fn = float(weights[fn].sum()); weighted_fp = float(weights[fp].sum())
    denominator_j = weighted_tp + weighted_fn + weighted_fp
    denominator_d = 2.0 * weighted_tp + weighted_fn + weighted_fp
    hist_fn: dict[str, int] = {}; hist_fp: dict[str, int] = {}
    for time_index in np.flatnonzero(dataset.window_time_masks["W1"] | dataset.window_time_masks["W3"]):
        boundary = np.zeros(dataset.cell_count, dtype=bool)
        labels = teacher[time_index]
        for cell, adjacent in enumerate(band.neighbours):
            boundary[cell] = any(labels[cell] != labels[j] for j in adjacent)
        distance = np.full(dataset.cell_count, -1, dtype=np.int32)
        queue: deque[int] = deque(int(value) for value in np.flatnonzero(boundary))
        for value in queue: distance[value] = 0
        while queue:
            current = queue.popleft()
            for adjacent in band.neighbours[current]:
                if distance[adjacent] < 0:
                    distance[adjacent] = distance[current] + 1; queue.append(adjacent)
        for mask, histogram in ((fn[time_index], hist_fn), (fp[time_index], hist_fp)):
            unique, counts = np.unique(distance[mask], return_counts=True)
            for value, count in zip(unique, counts, strict=True):
                key = str(int(value)); histogram[key] = histogram.get(key, 0) + int(count)
    clipped = np.clip(prediction, CLIP_EPSILON, 1.0 - CLIP_EPSILON)
    margin = np.abs(np.log(clipped / (1.0 - clipped)))
    boundary_indices = np.concatenate(tuple(band.pool_indices.values()))
    flat_margin = margin.reshape(-1)
    quantiles = (0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0)
    return {
        "pool_counts": band.pool_counts,
        "pool_masses": band.pool_masses,
        "pool_hashes": band.pool_hashes,
        "confusion_counts": {"TP": int(tp.sum()), "FN": int(fn.sum()), "FP": int(fp.sum())},
        "weighted_jaccard": weighted_tp / denominator_j if denominator_j else 1.0,
        "weighted_dice": 2.0 * weighted_tp / denominator_d if denominator_d else 1.0,
        "FN_graph_distance_histogram": hist_fn,
        "FP_graph_distance_histogram": hist_fp,
        "absolute_full_logit_margin_quantiles": {str(q): float(np.quantile(flat_margin, q)) for q in quantiles},
        "absolute_boundary_logit_margin_quantiles": {str(q): float(np.quantile(flat_margin[boundary_indices], q)) for q in quantiles},
        "nonperiodic_four_neighbour": True,
    }


def load_lf3_t0_model(path: Path, *, physics: Any, config: Any, device: torch.device, expected_sha256: str) -> tuple[PhkV22RModel, dict[str, Any]]:
    supplied = Path(path).resolve()
    if _sha256_path(supplied) != expected_sha256:
        raise ValueError("LF4 LF3-T0 checkpoint hash drift")
    payload = torch.load(supplied, map_location=device, weights_only=False)
    metadata = payload.get("lf3", {})
    if payload.get("schema_id") != "phk-v22r-checkpoint-v1-1" or metadata.get("task_id") != LF3_TASK_ID or metadata.get("stage") != LF3_T0_STAGE or metadata.get("global_optimizer_step") != 1200:
        raise PermissionError("LF4 initialization is not exact LF3-T0")
    model = build_range_preserving_model(physics=physics, config=config).to(device=device, dtype=torch.float64)
    if payload.get("architecture") != model.architecture_manifest():
        raise ValueError("LF4 LF3-T0 architecture drift")
    model.load_state_dict(payload["model_state_dict"], strict=True); model.train()
    return model, payload


def _field_state_sha256(model: PhkV22RModel, field: str) -> str:
    digest = hashlib.sha256()
    for prefix, module in (("encoder", model.encoders[field]), ("head", model.heads[field])):
        for name, value in sorted(module.state_dict().items()):
            digest.update(f"{prefix}:{name}".encode("utf-8")); digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest().upper()


def _audit_cycle(audit: Mapping[str, Any], cycle: int) -> Mapping[str, Any]:
    return audit["event_metrics"][f"cycle_{cycle}"]


def development_gate(audit: Mapping[str, Any], baseline: Mapping[str, Any], *, vt_unchanged: bool, contract: Mapping[str, Any]) -> dict[str, Any]:
    gate = contract["P0_entry_gate"]
    checks: dict[str, bool] = {
        "finite": audit.get("all_values_finite") is True,
        "phase_range": audit.get("phase_range", {}).get("passed") is True,
        "potential": audit.get("potential_maximum_principle", {}).get("passed") is True,
        "two_cycle_events": audit.get("two_cycle_events") is True,
        "phase_weighted_error": float(audit["weighted_errors"]["phase"]) <= float(gate["phase_weighted_mse_to_exact_lf3_t0_maximum_ratio"]) * float(baseline["weighted_errors"]["phase"]),
        "V_T_bitwise_unchanged": bool(vt_unchanged),
    }
    topology = audit["event_topology_hard_guard"]["cycles"]
    for cycle in (1, 2):
        metrics = _audit_cycle(audit, cycle); topo = topology[cycle - 1]; prefix = f"cycle_{cycle}"
        recall = metrics.get("hard_recall"); precision = metrics.get("hard_precision"); mass = metrics.get("hard_active_mass_ratio"); timing = metrics.get("event_time_absolute_error")
        checks[f"{prefix}_recall"] = recall is not None and float(recall) >= 0.80
        checks[f"{prefix}_precision"] = precision is not None and float(precision) >= 0.80
        checks[f"{prefix}_mass"] = mass is not None and 0.80 <= float(mass) <= 1.20
        checks[f"{prefix}_timing"] = timing is not None and float(timing) <= 0.005
        checks[f"{prefix}_roi_peak"] = float(topo["peak_roi_fraction"]) >= 0.02
        checks[f"{prefix}_full_peak"] = float(topo["peak_full_domain_fraction"]) <= 0.45
        checks[f"{prefix}_outside_peak"] = float(topo["peak_outside_roi_fraction"]) <= 0.10
        checks[f"{prefix}_recovery"] = float(topo["recovery_fraction"]) >= 0.70
    failed = sorted(name for name, passed in checks.items() if not passed)
    recalls = [float(_audit_cycle(audit, cycle).get("hard_recall") or 0.0) for cycle in (1, 2)]
    return {"passed": not failed, "checks": checks, "failed_checks": failed, "Rmin": min(recalls)}


def strict_carrier_gate(audit: Mapping[str, Any], lf1_b0: Mapping[str, Any]) -> dict[str, Any]:
    return lf3_carrier_gate(audit, lf1_b0, contract=_read_json(LF3_DECISION_CONTRACT_PATH))


def _quality_preserved(candidate: Mapping[str, Any], control: Mapping[str, Any]) -> bool:
    for cycle in (1, 2):
        cm = _audit_cycle(candidate, cycle); gm = _audit_cycle(control, cycle)
        if float(cm.get("hard_precision") or 0.0) < 0.82 or not 0.85 <= float(cm.get("hard_active_mass_ratio") or 0.0) <= 1.10:
            return False
        if float(cm.get("event_time_absolute_error") or math.inf) > float(gm.get("event_time_absolute_error") or math.inf) + 1.0e-12:
            return False
        ct = candidate["event_topology_hard_guard"]["cycles"][cycle - 1]; gt = control["event_topology_hard_guard"]["cycles"][cycle - 1]
        if float(ct["peak_outside_roi_fraction"]) > float(gt["peak_outside_roi_fraction"]) + 1.0e-12 or float(ct["recovery_fraction"]) + 1.0e-12 < float(gt["recovery_fraction"]):
            return False
    return all(float(candidate["weighted_errors"][field]) <= float(control["weighted_errors"][field]) * 1.0000000001 for field in ("potential", "temperature"))


def mechanism_decision(arms: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    g, m, c = (arms[name] for name in ARM_ORDER)
    boundary = bool(m["gate"]["Rmin"] - g["gate"]["Rmin"] >= 0.03 and _quality_preserved(m["audit"], g["audit"]))
    threshold = bool(c["gate"]["Rmin"] - m["gate"]["Rmin"] >= 0.03 and _quality_preserved(c["audit"], m["audit"]))
    if threshold:
        classification = "THRESHOLD_ALIGNED_LOSS_SUPPORTED"
    elif boundary:
        classification = "BOUNDARY_EXPOSURE_SUPPORTED"
    elif g["gate"]["passed"]:
        classification = "GENERIC_EXTENSION_SUFFICIENT"
    else:
        classification = "NO_MECHANISM_INCREMENT_CLAIM"
    return {
        "classification": classification,
        "boundary_exposure_supported": boundary,
        "threshold_aligned_supported": threshold,
        "Rmin": {name: float(arms[name]["gate"]["Rmin"]) for name in ARM_ORDER},
        "M_minus_G": float(m["gate"]["Rmin"] - g["gate"]["Rmin"]),
        "C_minus_M": float(c["gate"]["Rmin"] - m["gate"]["Rmin"]),
    }


def select_development_arm(arms: Mapping[str, Mapping[str, Any]]) -> str | None:
    eligible = [name for name in ARM_ORDER if arms[name]["gate"]["passed"] and arms[name].get("numerical_valid", True)]
    if not eligible:
        return None
    strict = [name for name in eligible if arms[name]["strict_gate"]["passed"]]
    candidates = strict or eligible
    best_r = max(float(arms[name]["gate"]["Rmin"]) for name in candidates)
    near = [name for name in candidates if best_r - float(arms[name]["gate"]["Rmin"]) < 0.01]
    if len(near) > 1:
        return min(near, key=lambda name: ARM_SIMPLE_ORDER[name])
    winners = [name for name in candidates if float(arms[name]["gate"]["Rmin"]) == best_r]
    return min(winners, key=lambda name: (float(arms[name]["audit"]["weighted_errors"]["phase"]), ARM_SIMPLE_ORDER[name]))


def _write_checkpoint(path: Path, *, model: PhkV22RModel, optimizer: torch.optim.Optimizer, config: Any, update: int, role: str, source_identity: str, contracts: Mapping[str, Any], parent_sha256: str, physics_program_sha256: str, physics_object_sha256: str) -> Path:
    payload = _checkpoint_payload(model=model, optimizer=optimizer, config=config, update=update, program_contract_sha256=_sha256_path(V22R_PROGRAM_CONTRACT_PATH), method_contract_sha256=_sha256_path(V22R_METHOD_CONTRACT_PATH), physical_program_sha256=physics_program_sha256, physical_object_sha256=physics_object_sha256)
    payload["lf4"] = {"schema_id": "phk-v23-lf4-checkpoint-metadata-v1", "task_id": TASK_ID, "role": role, "optimizer_update": update, "source_identity": source_identity, "contracts": dict(contracts), "parent_checkpoint_sha256": parent_sha256, "medium_labels_used": role in ARM_ORDER, "physics_residual_used": role == "P0", "stress_read": False}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle: torch.save(payload, handle)
    return path


def _append(handle: Any, payload: Mapping[str, Any]) -> None:
    handle.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n"); handle.flush()


def _gradient_group_norm(parameters: Sequence[torch.nn.Parameter]) -> float:
    values = [torch.sum(parameter.grad.detach().square()) for parameter in parameters if parameter.grad is not None]
    return float(torch.sqrt(sum(values)).detach().cpu()) if values else 0.0


def read_cpu_qualification(path: Path) -> dict[str, Any]:
    payload = _read_json(Path(path))
    if payload.get("schema_id") != "phk-v23-lf4-cpu-qualification-v1" or payload.get("task_id") != TASK_ID or payload.get("status") != "LF4_CPU_QUALIFICATION_PASS" or payload.get("contracts") != contract_identity() or payload.get("gpu_execution_authorized_by_cpu_gate") is not True:
        raise PermissionError("LF4 CPU qualification is absent, stale, or failed")
    return payload


def execute_reference_blind_gpu_campaign(*, output_root: Path, medium_carrier: Path, initial_checkpoint: Path, cpu_qualification_path: Path, device_name: str, source_identity: str) -> dict[str, Any]:
    contracts = load_contracts(); identities = contract_identity(); qualification = read_cpu_qualification(cpu_qualification_path)
    if not device_name.startswith("cuda") or not torch.cuda.is_available(): raise RuntimeError("LF4 requires CUDA")
    device = torch.device(device_name); gpu_name = torch.cuda.get_device_name(device)
    if gpu_name != "Tesla V100-PCIE-32GB": raise RuntimeError("LF4 requires Tesla V100-PCIE-32GB")
    output = Path(output_root).resolve(); output.mkdir(parents=True, exist_ok=False)
    config = build_training_config(device_name); physics, physics_program_sha256, physics_object_sha256 = load_case_physics(config.case_control)
    dataset = load_medium_dataset(Path(medium_carrier), physics=physics, contracts=contracts)
    if dataset.partition_sha256 != qualification["partition_sha256"]: raise ValueError("LF4 qualified partition drift")
    expected_streams = qualification["stream_identities"]; parent_hash = _sha256_path(Path(initial_checkpoint))
    started = time.perf_counter(); started_at = datetime.now(timezone.utc).isoformat(); random.seed(17); np.random.seed(17); torch.manual_seed(17); torch.cuda.manual_seed_all(17)
    _write_json_exclusive(output / "manifest-start.json", {"schema_id":"phk-v23-lf4-run-manifest-v1","task_id":TASK_ID,"status":"RUNNING_REFERENCE_BLIND_GPU_CAMPAIGN","source_identity":source_identity,"contracts":identities,"gpu":gpu_name,"dtype":"FLOAT64","seed":17,"input_bindings":{"medium":{"sha256":_sha256_path(Path(medium_carrier))},"lf3_t0":{"sha256":parent_hash},"cpu_qualification":{"sha256":_sha256_path(Path(cpu_qualification_path))}},"fine_extra_lf_only_evaluator_stress_read":False})
    baseline = qualification["lf3_t0_full_medium_audit"]; lf1_b0 = qualification["lf1_b0_full_medium_audit"]
    band_dataset = InterfaceBandDataset(dataset); arm_results: dict[str, Any] = {}; arm_checkpoints: dict[str, Path] = {}; numerical_invalid_arms: list[str] = []
    telemetry_path = output / "development-telemetry.jsonl"; hashes_path = output / "development-batch-hashes.jsonl"
    with telemetry_path.open("x", encoding="utf-8", newline="\n") as telemetry, hashes_path.open("x", encoding="utf-8", newline="\n") as hashes:
        for arm in ARM_ORDER:
            model, _ = load_lf3_t0_model(Path(initial_checkpoint), physics=physics, config=config, device=device, expected_sha256=contracts["data"]["initial_checkpoint"]["sha256"])
            for field in ("potential", "temperature"):
                model.encoders[field].requires_grad_(False); model.heads[field].requires_grad_(False)
            phase_parameters = tuple(model.encoders["phase"].parameters()) + tuple(model.heads["phase"].parameters())
            vt_before = {field: _field_state_sha256(model, field) for field in ("potential", "temperature")}
            optimizer = torch.optim.Adam(phase_parameters, lr=1.0e-3, betas=(0.9,0.999), eps=1.0e-8, weight_decay=0.0, amsgrad=False)
            base_stream = BaseDevelopmentStream(dataset); extra_stream: Any = GlobalExtraStream(dataset) if arm == ARM_G else BandStream(band_dataset)
            final_audit: dict[str, Any] | None = None; arm_valid = True; executed = 0
            for step in range(1, DEV_UPDATES + 1):
                optimizer.zero_grad(set_to_none=True); base_batch = base_stream.draw(step); extra_batch = extra_stream.draw(step)
                base_loss = measure_decoupled_terms(model, base_batch, physics=physics, device=device)["phase_logit"]
                if arm == ARM_G:
                    component = normalized_logit_mse(model, extra_batch, physics=physics, device=device); pool_components: dict[str, float] = {}
                else:
                    components = band_losses(model, extra_batch, physics=physics, device=device)
                    component = components["mse"] if arm == ARM_M else components["classification"]
                    chosen = components["pool_mse"] if arm == ARM_M else components["pool_classification"]
                    pool_components = {name: float(value.detach().cpu()) for name, value in chosen.items()}
                total = 0.5 * base_loss + 0.5 * component
                if not bool(torch.isfinite(total)): arm_valid = False; numerical_invalid_arms.append(arm); break
                total.backward(); grad_norm = _gradient_group_norm(phase_parameters)
                if not math.isfinite(grad_norm): arm_valid = False; numerical_invalid_arms.append(arm); break
                torch.nn.utils.clip_grad_norm_(phase_parameters, 10.0); optimizer.step(); executed = step
                _append(hashes, {"arm":arm,"step":step,"base_sha256":base_batch.batch_sha256,"extra_sha256":extra_batch.batch_sha256})
                if step == 1 or step % 50 == 0:
                    final_audit = full_medium_audit(model, dataset, device=device)
                    _append(telemetry, {"arm":arm,"step":step,"L_base":float(base_loss.detach().cpu()),"L_extra":float(component.detach().cpu()),"L_total":float(total.detach().cpu()),"pool_losses":pool_components,"gradient_norm_before_clip":grad_norm,"audit":final_audit})
                if time.perf_counter() - started > float(contracts["program"]["hard_limits"]["maximum_wall_seconds"]): raise RuntimeError("LF4_RUN_BOUND_EXCEEDED")
            stream_ok = base_stream.window_sha256 == expected_streams["base_window_1201_1600_sha256"] and base_stream.rolling_1600_sha256 == expected_streams["base_rolling_1600_sha256"] and extra_stream.rolling_sha256 == expected_streams["global_extra_400_sha256" if arm == ARM_G else "band_400_sha256"]
            if not stream_ok: raise RuntimeError(f"LF4 {arm} stream identity drift")
            vt_after = {field: _field_state_sha256(model, field) for field in ("potential", "temperature")}; vt_unchanged = vt_before == vt_after
            if not vt_unchanged: raise RuntimeError(f"LF4 {arm} changed frozen V/T")
            if final_audit is None: final_audit = full_medium_audit(model, dataset, device=device)
            numerical_valid = bool(arm_valid and final_audit["all_values_finite"] and final_audit["phase_range"]["passed"] and final_audit["potential_maximum_principle"]["passed"])
            if not numerical_valid and arm not in numerical_invalid_arms: numerical_invalid_arms.append(arm)
            gate = development_gate(final_audit, baseline, vt_unchanged=vt_unchanged, contract=contracts["decision"])
            strict = strict_carrier_gate(final_audit, lf1_b0)
            checkpoint = _write_checkpoint(output / f"checkpoint-{arm.lower().replace('_','-')}-step-400.pt", model=model, optimizer=optimizer, config=config, update=executed, role=arm, source_identity=source_identity, contracts=identities, parent_sha256=parent_hash, physics_program_sha256=physics_program_sha256, physics_object_sha256=physics_object_sha256)
            arm_checkpoints[arm] = checkpoint; arm_results[arm] = {"executed_updates":executed,"numerical_valid":numerical_valid,"audit":final_audit,"gate":gate,"strict_gate":strict,"V_T_state_sha256":{"before":vt_before,"after":vt_after},"checkpoint_sha256":_sha256_path(checkpoint),"base_window_sha256":base_stream.window_sha256,"extra_rolling_sha256":extra_stream.rolling_sha256}
            del optimizer, model; torch.cuda.empty_cache()
    mechanism = mechanism_decision(arm_results); selected = select_development_arm(arm_results)
    selected_prediction: Path | None = None; p0_checkpoint: Path | None = None; p0_prediction: Path | None = None; p0_result: dict[str, Any] | None = None
    if selected is not None:
        selected_prediction = write_prediction_carrier(checkpoint_path=arm_checkpoints[selected], output_path=output / "prediction-selected-development-step-400.npz", device_name=device_name)
        model, _ = load_lf3_t0_model(Path(initial_checkpoint), physics=physics, config=config, device=device, expected_sha256=contracts["data"]["initial_checkpoint"]["sha256"])
        selected_payload = torch.load(arm_checkpoints[selected], map_location=device, weights_only=False); model.load_state_dict(selected_payload["model_state_dict"], strict=True); model.train()
        phase_parameters = tuple(model.encoders["phase"].parameters()) + tuple(model.heads["phase"].parameters())
        for parameter in phase_parameters: parameter.requires_grad_(False)
        phase_before = _phase_state_sha256(model)
        optimizer = torch.optim.Adam(model.parameters(), lr=1.0e-3, betas=(0.9,0.999), eps=1.0e-8, weight_decay=0.0, amsgrad=False)
        physics_stream = LF0PhysicsBatchStream(physics=physics, interior_points=512, boundary_points=128, initial_points=128, refresh_updates=250, seed=17)
        p0_telemetry_path = output / "p0-telemetry.jsonl"; p0_hashes_path = output / "p0-physics-batch-hashes.jsonl"; final_p0_audit = None; step550 = None
        with p0_telemetry_path.open("x",encoding="utf-8",newline="\n") as telemetry, p0_hashes_path.open("x",encoding="utf-8",newline="\n") as hashes:
            for step in range(1, P0_UPDATES + 1):
                if step == P0_PHASE_FREEZE_STEPS + 1:
                    frozen_hash = _phase_state_sha256(model); phase_state_count = sum(parameter in optimizer.state for parameter in phase_parameters)
                    if frozen_hash != phase_before or phase_state_count != 0: raise RuntimeError("LF4 P0 phase freeze identity drift")
                    for parameter in phase_parameters: parameter.requires_grad_(True)
                optimizer.zero_grad(set_to_none=True); batch = physics_stream.draw(model, step, dtype=torch.float64, device=device); loss, components = _physics_objective(model, batch, config)
                if not bool(torch.isfinite(loss)): raise FloatingPointError("LF4 P0 non-finite objective")
                loss.backward(); groups = {field:_gradient_group_norm(tuple(model.encoders[field].parameters()) + tuple(model.heads[field].parameters())) for field in ("potential","temperature","phase")}
                trainable = tuple(parameter for parameter in model.parameters() if parameter.requires_grad); grad_norm = float(torch.nn.utils.clip_grad_norm_(trainable,10.0).detach().cpu()); optimizer.step()
                _append(hashes,{"step":step,"interior_coordinate_sha256":batch.interior_sha256,"boundary_coordinate_sha256":batch.boundary_sha256,"initial_coordinate_sha256":batch.initial_sha256,"batch_sha256":batch.batch_sha256})
                if step == 1 or step % 50 == 0 or step in {550,551,1200}:
                    final_p0_audit = full_medium_audit(model,dataset,device=device)
                    _append(telemetry,{"step":step,**components,"total_loss":float(loss.detach().cpu()),"gradient_norm_before_clip":grad_norm,"per_head_gradient_norm":groups,"phase_sha256":_phase_state_sha256(model),"phase_frozen":step<=550,"audit":final_p0_audit})
                if step == 550:
                    step550={"phase_before_sha256":phase_before,"phase_after_sha256":_phase_state_sha256(model),"bitwise_preserved":phase_before==_phase_state_sha256(model),"phase_optimizer_state_entries":sum(parameter in optimizer.state for parameter in phase_parameters),"physics_hash_prefix":physics_stream.rolling_sha256,"finite":bool(final_p0_audit and final_p0_audit["all_values_finite"]),"potential_valid":bool(final_p0_audit and final_p0_audit["potential_maximum_principle"]["passed"])}
                if time.perf_counter()-started > float(contracts["program"]["hard_limits"]["maximum_wall_seconds"]): raise RuntimeError("LF4_RUN_BOUND_EXCEEDED")
        if physics_stream.rolling_sha256 != EXPECTED_P0_STREAM_SHA256: raise RuntimeError("LF4 P0 physics stream identity drift")
        assert final_p0_audit is not None
        p0_entry = development_gate(final_p0_audit, baseline, vt_unchanged=True, contract=contracts["decision"])
        p0_strict = strict_carrier_gate(final_p0_audit, lf1_b0)
        preservation_ratios={field:float(final_p0_audit["weighted_errors"][field])/max(float(arm_results[selected]["audit"]["weighted_errors"][field]),1e-12) for field in ("potential","temperature","phase")}
        preservation_ratios["topology"]=float(final_p0_audit["topology_weighted_loss"])/max(float(arm_results[selected]["audit"]["topology_weighted_loss"]),1e-12)
        preservation=bool(p0_entry["passed"] and preservation_ratios["potential"]<=1.20 and preservation_ratios["temperature"]<=1.05 and preservation_ratios["phase"]<=1.05 and preservation_ratios["topology"]<=1.05)
        p0_checkpoint=_write_checkpoint(output/"checkpoint-p0-final.pt",model=model,optimizer=optimizer,config=config,update=1200,role="P0",source_identity=source_identity,contracts=identities,parent_sha256=_sha256_path(arm_checkpoints[selected]),physics_program_sha256=physics_program_sha256,physics_object_sha256=physics_object_sha256)
        p0_prediction=write_prediction_carrier(checkpoint_path=p0_checkpoint,output_path=output/"prediction-p0-final.npz",device_name=device_name)
        p0_result={"executed_updates":1200,"audit":final_p0_audit,"entry_gate":p0_entry,"strict_gate":p0_strict,"preservation_ratios":preservation_ratios,"entry_preservation_passed":preservation,"step550":step550,"physics_stream_sha256":physics_stream.rolling_sha256,"checkpoint_sha256":_sha256_path(p0_checkpoint)}
    artifacts={"manifest_start":_artifact_record(output/"manifest-start.json",output),"development_telemetry":_artifact_record(telemetry_path,output),"development_batch_hashes":_artifact_record(hashes_path,output)}
    for arm,path in arm_checkpoints.items(): artifacts[f"checkpoint_{arm}"]=_artifact_record(path,output)
    if selected_prediction is not None: artifacts["prediction_selected"]=_artifact_record(selected_prediction,output)
    if p0_checkpoint is not None and p0_prediction is not None:
        artifacts.update({"checkpoint_p0":_artifact_record(p0_checkpoint,output),"prediction_p0":_artifact_record(p0_prediction,output),"p0_telemetry":_artifact_record(output/"p0-telemetry.jsonl",output),"p0_physics_batch_hashes":_artifact_record(output/"p0-physics-batch-hashes.jsonl",output)})
    status="LF4_NUMERICAL_OR_IDENTITY_INVALID" if numerical_invalid_arms else ("LF4_NO_DEVELOPMENT_ENTRY" if selected is None else "LF4_REFERENCE_BLIND_GPU_CAMPAIGN_COMPLETE")
    summary={"schema_id":"phk-v23-lf4-reference-blind-run-summary-v1","task_id":TASK_ID,"title":TITLE,"status":status,"started_at_utc":started_at,"finished_at_utc":datetime.now(timezone.utc).isoformat(),"source_identity":source_identity,"gpu":gpu_name,"dtype":"FLOAT64","seed":17,"optimizer_updates":sum(int(v["executed_updates"]) for v in arm_results.values())+(1200 if p0_result else 0),"development":arm_results,"mechanism_decision":mechanism,"selected_role":selected,"P0_disposition":"EXECUTED" if p0_result else "NOT_RUN_NO_DEVELOPMENT_ENTRY","P0":p0_result,"numerical_invalid_arms":numerical_invalid_arms,"wall_seconds":time.perf_counter()-started,"artifacts":artifacts,"prediction_reference_free":True,"fine_extra_lf_only_evaluator_stress_read":False}
    _write_json_exclusive(output/"summary.json",summary); return summary


def _parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--output-root",type=Path,required=True); parser.add_argument("--medium-carrier",type=Path,required=True); parser.add_argument("--initial-checkpoint",type=Path,required=True); parser.add_argument("--cpu-qualification",type=Path,required=True); parser.add_argument("--device",default="cuda:0"); parser.add_argument("--source-identity",required=True); return parser


def main(argv: Sequence[str] | None=None)->int:
    args=_parser().parse_args(argv); summary=execute_reference_blind_gpu_campaign(output_root=args.output_root,medium_carrier=args.medium_carrier,initial_checkpoint=args.initial_checkpoint,cpu_qualification_path=args.cpu_qualification,device_name=args.device,source_identity=args.source_identity); print(json.dumps({"status":summary["status"],"optimizer_updates":summary["optimizer_updates"],"selected_role":summary["selected_role"]},sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())


__all__=["ARM_C","ARM_G","ARM_M","ARM_ORDER","BAND_POOL_NAMES","BandStream","BaseDevelopmentStream","GlobalExtraStream","InterfaceBandDataset","TASK_ID","band_losses","boundary_geometry_report","development_gate","execute_reference_blind_gpu_campaign","load_contracts","mechanism_decision","precompute_stream_identities","select_development_arm"]
