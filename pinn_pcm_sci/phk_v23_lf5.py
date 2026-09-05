"""PHK-V2.3 LF5 temporal zero-level alignment and conditional physics pilot."""

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
    LF0PhysicsBatchStream,
    _artifact_record,
    _physics_objective,
    _read_json,
    _sha256_path,
    _write_json_exclusive,
)
from .phk_v23_lf3 import (
    CLIP_EPSILON,
    LOGIT_SPAN,
    TASK_ID as LF3_TASK_ID,
    T0_STAGE as LF3_T0_STAGE,
    _phase_state_sha256,
    build_training_config,
    carrier_gate as lf3_carrier_gate,
    full_medium_audit,
    measure_decoupled_terms,
    startup_factor,
)
from .phk_v23_lf4 import (
    BAND_POOL_NAMES,
    BAND_SEEDS,
    BandStream,
    BaseDevelopmentStream,
    InterfaceBandDataset,
    band_losses,
    load_lf3_t0_model,
    _append,
    _field_state_sha256,
    _gradient_group_norm,
)
from .phk_v23_lf2 import MediumMeasureDataset, load_medium_dataset


TASK_ID = "PHK_V23_LF5_CYCLE_RESOLVED_TEMPORAL_ZERO_LEVEL_ALIGNMENT_AND_CONDITIONAL_PHYSICS_PILOT_EXECUTE"
TITLE = "PHK-V2.3 LF5 calibration-preserving cycle-resolved temporal zero-level alignment and conditional physics pilot"
DEV_T_ROLE = "DEV_T_TEMPORAL_ZERO_LEVEL"
P0_ROLE = "LF5_P0_FULL_PHYSICS"
TEMPORAL_POOL_NAMES = ("C1_ONSET", "C1_RECOVERY", "C2_ONSET", "C2_RECOVERY")
TEMPORAL_SEEDS = (17511, 17512, 17513, 17514)
DEV_UPDATES = 400
P0_UPDATES = 1200
P0_PHASE_FREEZE_STEPS = 550
PHASE_MSE_MAXIMUM = 0.001330588465425399
EXPECTED_PARTITION_SHA256 = "EFD70886DD85AC467F06F38B48FB0EE6C0132471CE74817E3A4D68E752B7A515"
EXPECTED_BASE_WINDOW_SHA256 = "3870D0C1411B3DF6E04C5BA316B3F0F77233D94A73A19E84523D81B62F692E4A"
EXPECTED_BAND_SHA256 = "4DB1728CC543B1AB18BD3F74B83B29EBFE5F95624D98DAFEA615B0ECDC69DEC4"
EXPECTED_P0_STREAM_SHA256 = "536E6706A0B68EBB1277A97F402D273AFA2EA1E0B27106F26CB4222B7EC05C53"

PROGRAM_CONTRACT_PATH = ROOT / "configs/phk_v23/program_contract_lf5_temporal_zero_level.json"
METHOD_CONTRACT_PATH = ROOT / "configs/phk_v23/method_contract_lf5_temporal_zero_level.json"
DATA_CONTRACT_PATH = ROOT / "configs/phk_v23/data_contract_lf5_temporal_zero_level.json"
DECISION_CONTRACT_PATH = ROOT / "configs/phk_v23/decision_contract_lf5_temporal_zero_level.json"
LF3_DECISION_CONTRACT_PATH = ROOT / "configs/phk_v23/decision_contract_lf3_phase_latent_carrier.json"
CONTRACT_PATHS = {
    "program": PROGRAM_CONTRACT_PATH,
    "method": METHOD_CONTRACT_PATH,
    "data": DATA_CONTRACT_PATH,
    "decision": DECISION_CONTRACT_PATH,
}
EXPECTED_SCHEMAS = {
    "program": "phk-v23-lf5-program-contract-v1",
    "method": "phk-v23-lf5-method-contract-v1",
    "data": "phk-v23-lf5-data-contract-v1",
    "decision": "phk-v23-lf5-decision-contract-v1",
}


def load_contracts(*, require_stream_freeze: bool = True) -> dict[str, dict[str, Any]]:
    contracts = {name: _read_json(path) for name, path in CONTRACT_PATHS.items()}
    relative = {name: path.relative_to(ROOT).as_posix() for name, path in CONTRACT_PATHS.items()}
    for name, schema in EXPECTED_SCHEMAS.items():
        if contracts[name].get("schema_id") != schema:
            raise ValueError(f"unsupported LF5 {name} contract")
    if contracts["program"].get("phase_id") != TASK_ID:
        raise ValueError("LF5 task identity drift")
    if any(contracts[name].get("program_contract") != relative["program"] for name in ("method", "data", "decision")):
        raise ValueError("LF5 program binding drift")
    if contracts["decision"].get("method_contract") != relative["method"] or contracts["decision"].get("data_contract") != relative["data"]:
        raise ValueError("LF5 decision binding drift")
    limits = contracts["program"]["hard_limits"]
    if limits.get("maximum_scientific_gpu_trajectories") != 1 or limits.get("maximum_optimizer_updates") != 1600:
        raise ValueError("LF5 run bounds drift")
    common = contracts["method"]["common_identity"]
    if common.get("dtype") != "FLOAT64" or common.get("seed") != 17 or float(common.get("clip_epsilon")) != CLIP_EPSILON:
        raise ValueError("LF5 common identity drift")
    data = contracts["data"]
    if data["target_measure"].get("partition_sha256") != EXPECTED_PARTITION_SHA256:
        raise ValueError("LF5 partition identity drift")
    if tuple(data["spatial_band_stream"].get("seeds", ())) != BAND_SEEDS or tuple(data["spatial_band_stream"].get("pool_order", ())) != BAND_POOL_NAMES:
        raise ValueError("LF5 spatial stream drift")
    temporal = data["temporal_edge_stream"]
    if tuple(temporal.get("seeds", ())) != TEMPORAL_SEEDS or tuple(temporal.get("pool_order", ())) != TEMPORAL_POOL_NAMES:
        raise ValueError("LF5 temporal stream drift")
    if require_stream_freeze:
        frozen = (
            data["base_stream"].get("development_window_sha256"),
            data["spatial_band_stream"].get("rolling_sha256"),
            temporal.get("rolling_sha256"),
            data.get("P0_physics_stream_sha256"),
        )
        if any(not isinstance(value, str) or len(value) != 64 or value.startswith("PENDING") for value in frozen):
            raise PermissionError("LF5 stream identities are not frozen")
    if len(contracts["decision"].get("machine_outcomes_and_unique_next", {})) != 15:
        raise ValueError("LF5 machine outcome mapping is incomplete")
    if contracts["decision"].get("stress_status") != "TWO_STRESS_REFERENCES_SEALED_UNREAD":
        raise PermissionError("LF5 stress boundary drift")
    return contracts


def contract_identity() -> dict[str, dict[str, str]]:
    return {name: {"path": path.relative_to(ROOT).as_posix(), "sha256": _sha256_path(path)} for name, path in CONTRACT_PATHS.items()}


@dataclass(frozen=True)
class TemporalBatch:
    coordinates_k: torch.Tensor
    coordinates_k1: torch.Tensor
    rho_star: torch.Tensor
    teacher_denominator: torch.Tensor
    delta_t: torch.Tensor
    pool_counts: Mapping[str, int]
    batch_sha256: str


class TemporalEdgeDataset:
    """First onset in W1/W3 and first subsequent recovery in W2/W4, without wrap."""

    cycle_specs = (
        (1, 0.0, 0.35, 1.25),
        (2, 1.25, 1.60, 2.50),
    )

    def __init__(self, dataset: MediumMeasureDataset) -> None:
        self.dataset = dataset
        phase = np.clip(dataset.fields["phase"], CLIP_EPSILON, 1.0 - CLIP_EPSILON)
        z_star = np.log(phase / (1.0 - phase))
        self.records: dict[str, dict[str, np.ndarray]] = {}
        self.pool_counts: dict[str, int] = {}
        self.pool_hashes: dict[str, str] = {}
        self.invalid_edge_count = 0
        self.candidate_edge_count = 0
        for cycle, onset_start, onset_end, cycle_end in self.cycle_specs:
            raw: dict[str, list[tuple[int, int, int, float, float, float]]] = {"ONSET": [], "RECOVERY": []}
            onset_indices = np.flatnonzero((dataset.time >= onset_start) & (dataset.time <= onset_end))
            cycle_indices = np.flatnonzero((dataset.time >= onset_start) & (dataset.time <= cycle_end))
            for cell in np.flatnonzero(dataset.roi_cells):
                onset_edges = [int(k) for k in onset_indices[:-1] if z_star[k, cell] < 0.0 <= z_star[k + 1, cell]]
                if not onset_edges:
                    continue
                onset = onset_edges[0]
                self._accept(raw["ONSET"], z_star, dataset, int(cell), onset)
                recovery_edges = [int(k) for k in cycle_indices[:-1] if k > onset and z_star[k, cell] >= 0.0 > z_star[k + 1, cell]]
                if recovery_edges:
                    self._accept(raw["RECOVERY"], z_star, dataset, int(cell), recovery_edges[0])
            for direction in ("ONSET", "RECOVERY"):
                name = f"C{cycle}_{direction}"
                if not raw[direction]:
                    raise ValueError(f"LF5 temporal pool is empty: {name}")
                matrix = np.asarray(raw[direction], dtype=np.float64)
                cell = matrix[:, 0].astype(np.int64)
                k = matrix[:, 1].astype(np.int64)
                k1 = matrix[:, 2].astype(np.int64)
                rho = matrix[:, 3].astype(np.float64)
                denominator = matrix[:, 4].astype(np.float64)
                edge_weight = matrix[:, 5].astype(np.float64)
                probability = edge_weight / edge_weight.sum()
                cdf = np.cumsum(probability); cdf[-1] = 1.0
                record = {"cell": cell, "k": k, "k1": k1, "rho": rho, "denominator": denominator, "edge_weight": edge_weight, "probability": probability, "cdf": cdf}
                self.records[name] = record
                self.pool_counts[name] = int(cell.size)
                digest = hashlib.sha256(f"PHK_V23_LF5_{name}".encode("ascii"))
                for key, dtype in (("cell", "<i8"), ("k", "<i8"), ("k1", "<i8"), ("rho", "<f8"), ("edge_weight", "<f8"), ("probability", "<f8")):
                    digest.update(np.asarray(record[key]).astype(dtype, copy=False).tobytes())
                self.pool_hashes[name] = digest.hexdigest().upper()
        if self.candidate_edge_count == 0:
            raise ValueError("LF5 temporal geometry has no candidate edges")
        self.invalid_edge_fraction = self.invalid_edge_count / self.candidate_edge_count
        if self.invalid_edge_fraction > 0.01:
            raise ValueError("LF5 temporal invalid-edge fraction exceeds 0.01")

    def _accept(self, target: list[tuple[int, int, int, float, float, float]], z: np.ndarray, dataset: MediumMeasureDataset, cell: int, k: int) -> None:
        self.candidate_edge_count += 1
        left, right = float(z[k, cell]), float(z[k + 1, cell])
        denominator = right - left
        threshold = 64.0 * np.finfo(np.float64).eps * max(1.0, abs(left), abs(right))
        if (left == 0.0 and right == 0.0) or abs(denominator) <= threshold:
            self.invalid_edge_count += 1
            return
        rho = -left / denominator
        if not 0.0 <= rho <= 1.0:
            self.invalid_edge_count += 1
            return
        flat_k = k * dataset.cell_count + cell
        flat_k1 = (k + 1) * dataset.cell_count + cell
        weight = 0.5 * (float(dataset.node_weights[flat_k]) + float(dataset.node_weights[flat_k1]))
        target.append((cell, k, k + 1, rho, denominator, weight))

    def _batch(self, selected_by_pool: Mapping[str, np.ndarray], *, metadata: str) -> TemporalBatch:
        coordinates_k: list[np.ndarray] = []; coordinates_k1: list[np.ndarray] = []
        rho: list[np.ndarray] = []; denominator: list[np.ndarray] = []; delta_t: list[np.ndarray] = []
        digest = hashlib.sha256(metadata.encode("ascii"))
        counts: dict[str, int] = {}
        for name in TEMPORAL_POOL_NAMES:
            selected = np.asarray(selected_by_pool[name], dtype=np.int64)
            record = self.records[name]
            counts[name] = int(selected.size)
            cell = record["cell"][selected]; k = record["k"][selected]; k1 = record["k1"][selected]
            flat_k = k * self.dataset.cell_count + cell; flat_k1 = k1 * self.dataset.cell_count + cell
            coordinates_k.append(self.dataset.coordinates[flat_k]); coordinates_k1.append(self.dataset.coordinates[flat_k1])
            rho.append(record["rho"][selected]); denominator.append(record["denominator"][selected])
            delta_t.append(self.dataset.time[k1] - self.dataset.time[k])
            digest.update(name.encode("ascii"))
            for values, dtype in ((cell, "<i8"), (k, "<i8"), (k1, "<i8"), (record["rho"][selected], "<f8"), (record["edge_weight"][selected], "<f8"), (record["probability"][selected], "<f8")):
                digest.update(np.asarray(values).astype(dtype, copy=False).tobytes())
        return TemporalBatch(
            torch.as_tensor(np.concatenate(coordinates_k), dtype=torch.float64),
            torch.as_tensor(np.concatenate(coordinates_k1), dtype=torch.float64),
            torch.as_tensor(np.concatenate(rho)[:, None], dtype=torch.float64),
            torch.as_tensor(np.concatenate(denominator)[:, None], dtype=torch.float64),
            torch.as_tensor(np.concatenate(delta_t)[:, None], dtype=torch.float64),
            counts,
            digest.hexdigest().upper(),
        )

    def sample(self, units: Mapping[str, torch.Tensor], *, step: int) -> TemporalBatch:
        selected: dict[str, np.ndarray] = {}
        for name in TEMPORAL_POOL_NAMES:
            values = units[name].detach().cpu().to(torch.float64).reshape(-1)
            cdf = torch.as_tensor(self.records[name]["cdf"], dtype=torch.float64)
            selected[name] = torch.searchsorted(cdf, values, right=True).clamp_max(self.pool_counts[name] - 1).numpy()
        return self._batch(selected, metadata=f"LF5:TEMPORAL:{step}:{self.dataset.partition_sha256}")

    def full_batch(self) -> TemporalBatch:
        selected = {name: np.arange(self.pool_counts[name], dtype=np.int64) for name in TEMPORAL_POOL_NAMES}
        return self._batch(selected, metadata=f"LF5:TEMPORAL:FULL:{self.dataset.partition_sha256}")


class TemporalEdgeStream:
    def __init__(self, edges: TemporalEdgeDataset) -> None:
        self.edges = edges
        self.engines = {name: torch.quasirandom.SobolEngine(1, scramble=True, seed=seed) for name, seed in zip(TEMPORAL_POOL_NAMES, TEMPORAL_SEEDS, strict=True)}
        self.local_step = 0
        self._rolling = hashlib.sha256(b"PHK_V23_LF5_TEMPORAL_ZERO_LEVEL_EDGES")

    @property
    def rolling_sha256(self) -> str:
        return self._rolling.copy().hexdigest().upper()

    def draw(self, local_step: int) -> TemporalBatch:
        if int(local_step) != self.local_step + 1:
            raise ValueError("LF5 temporal stream call-order drift")
        units = {name: self.engines[name].draw(32, dtype=torch.float64).reshape(-1) for name in TEMPORAL_POOL_NAMES}
        batch = self.edges.sample(units, step=int(local_step))
        self._rolling.update(bytes.fromhex(batch.batch_sha256)); self.local_step = int(local_step)
        return batch


def precompute_temporal_stream_identity(dataset: MediumMeasureDataset) -> dict[str, Any]:
    edges = TemporalEdgeDataset(dataset); stream = TemporalEdgeStream(edges)
    for step in range(1, DEV_UPDATES + 1):
        stream.draw(step)
    return {
        "rolling_sha256": stream.rolling_sha256,
        "pool_counts": edges.pool_counts,
        "pool_hashes": edges.pool_hashes,
        "invalid_edge_count": edges.invalid_edge_count,
        "candidate_edge_count": edges.candidate_edge_count,
        "invalid_edge_fraction": edges.invalid_edge_fraction,
    }


def _phase_logits(model: PhkV22RModel, coordinates: torch.Tensor, *, physics: Any) -> torch.Tensor:
    diagnostics = model.read_only_output_diagnostics(coordinates)
    initial = physics.initial_phase(coordinates).clamp(CLIP_EPSILON, 1.0 - CLIP_EPSILON)
    return torch.logit(initial) + 8.0 * startup_factor(coordinates[:, 2:3], physics) * diagnostics.latents["phase"]


def temporal_zero_level_terms(model: PhkV22RModel, batch: TemporalBatch, *, physics: Any, device: torch.device) -> dict[str, Any]:
    ck = batch.coordinates_k.to(device=device, dtype=torch.float64)
    ck1 = batch.coordinates_k1.to(device=device, dtype=torch.float64)
    rho = batch.rho_star.to(device=device, dtype=torch.float64)
    residual = (1.0 - rho) * _phase_logits(model, ck, physics=physics) + rho * _phase_logits(model, ck1, physics=physics)
    denominator = batch.teacher_denominator.to(device=device, dtype=torch.float64)
    delta_t = batch.delta_t.to(device=device, dtype=torch.float64)
    pointwise = (residual / LOGIT_SPAN).square().reshape(-1)
    delta_t_hat = -delta_t * residual / denominator
    pool_losses: dict[str, torch.Tensor] = {}; pool_reports: dict[str, dict[str, float]] = {}
    offset = 0
    for name in TEMPORAL_POOL_NAMES:
        stop = offset + int(batch.pool_counts[name]); values = residual[offset:stop]; corrections = delta_t_hat[offset:stop]
        pool_losses[name] = torch.mean(pointwise[offset:stop])
        pool_reports[name] = {
            "mean_absolute_residual": float(torch.mean(torch.abs(values)).detach().cpu()),
            "mean_signed_residual": float(torch.mean(values).detach().cpu()),
            "mean_delta_t_hat": float(torch.mean(corrections).detach().cpu()),
            "maximum_absolute_residual": float(torch.max(torch.abs(values)).detach().cpu()),
        }
        offset = stop
    return {"loss": sum(pool_losses.values()) / 4.0, "pool_losses": pool_losses, "pool_reports": pool_reports, "residual": residual}


def temporal_pool_report(model: PhkV22RModel, edges: TemporalEdgeDataset, *, physics: Any, device: torch.device) -> dict[str, Any]:
    with torch.no_grad():
        batch = edges.full_batch()
        terms = temporal_zero_level_terms(model, batch, physics=physics, device=device)
    residual = terms["residual"].detach().cpu().numpy().reshape(-1)
    reports: dict[str, dict[str, float]] = {}; offset = 0; losses: list[float] = []
    for name in TEMPORAL_POOL_NAMES:
        stop = offset + edges.pool_counts[name]
        values = residual[offset:stop]; weights = edges.records[name]["probability"]
        reports[name] = {
            "weighted_mean_absolute_residual": float(np.sum(weights * np.abs(values))),
            "weighted_mean_signed_residual": float(np.sum(weights * values)),
            "maximum_absolute_residual": float(np.max(np.abs(values))),
        }
        losses.append(float(np.sum(weights * np.square(values / LOGIT_SPAN))))
        offset = stop
    return {"pool_reports": reports, "full_weighted_loss": float(np.mean(losses))}


def strict_carrier_gate(audit: Mapping[str, Any], lf1_b0: Mapping[str, Any], *, vt_unchanged: bool) -> dict[str, Any]:
    result = lf3_carrier_gate(audit, lf1_b0, contract=_read_json(LF3_DECISION_CONTRACT_PATH))
    checks = dict(result["checks"])
    checks["V_T_bitwise_unchanged"] = bool(vt_unchanged)
    checks["phase_weighted_mse_vs_DEV_M"] = float(audit["weighted_errors"]["phase"]) <= PHASE_MSE_MAXIMUM
    failed = sorted(name for name, passed in checks.items() if not passed)
    return {**result, "passed": not failed, "checks": checks, "failed_checks": failed}


def p0_preservation_gate(audit: Mapping[str, Any], dev: Mapping[str, Any], lf1_b0: Mapping[str, Any]) -> dict[str, Any]:
    checks: dict[str, bool] = {
        "finite": audit.get("all_values_finite") is True,
        "phase_range": audit.get("phase_range", {}).get("passed") is True,
        "potential": audit.get("potential_maximum_principle", {}).get("passed") is True,
        "two_cycle_events": audit.get("two_cycle_events") is True,
    }
    topology = audit["event_topology_hard_guard"]["cycles"]
    for cycle in (1, 2):
        metrics = audit["event_metrics"][f"cycle_{cycle}"]; topo = topology[cycle - 1]; prefix = f"cycle_{cycle}"
        checks[f"{prefix}_recall"] = metrics.get("hard_recall") is not None and float(metrics["hard_recall"]) >= 0.80
        checks[f"{prefix}_precision"] = metrics.get("hard_precision") is not None and float(metrics["hard_precision"]) >= 0.80
        checks[f"{prefix}_mass"] = metrics.get("hard_active_mass_ratio") is not None and 0.80 <= float(metrics["hard_active_mass_ratio"]) <= 1.20
        checks[f"{prefix}_timing"] = metrics.get("event_time_absolute_error") is not None and float(metrics["event_time_absolute_error"]) <= 0.005
        checks[f"{prefix}_roi_peak"] = float(topo["peak_roi_fraction"]) >= 0.02
        checks[f"{prefix}_full_peak"] = float(topo["peak_full_domain_fraction"]) <= 0.45
        checks[f"{prefix}_outside_peak"] = float(topo["peak_outside_roi_fraction"]) <= 0.10
        checks[f"{prefix}_recovery"] = float(topo["recovery_fraction"]) >= 0.70
    ratios = {field: float(audit["weighted_errors"][field]) / max(float(dev["weighted_errors"][field]), 1.0e-12) for field in ("potential", "temperature", "phase")}
    ratios["topology"] = float(audit["topology_weighted_loss"]) / max(float(dev["topology_weighted_loss"]), 1.0e-12)
    checks.update({"potential_ratio": ratios["potential"] <= 1.20, "temperature_ratio": ratios["temperature"] <= 1.05, "phase_ratio": ratios["phase"] <= 1.05, "topology_ratio": ratios["topology"] <= 1.05})
    strict = strict_carrier_gate(audit, lf1_b0, vt_unchanged=True)
    failed = sorted(name for name, passed in checks.items() if not passed)
    return {"passed": not failed, "checks": checks, "failed_checks": failed, "ratios_to_DEV_T": ratios, "strict_gate": strict}


def _write_checkpoint(path: Path, *, model: PhkV22RModel, optimizer: torch.optim.Optimizer, config: Any, update: int, role: str, source_identity: str, contracts: Mapping[str, Any], parent_sha256: str, physics_program_sha256: str, physics_object_sha256: str) -> Path:
    payload = _checkpoint_payload(model=model, optimizer=optimizer, config=config, update=update, program_contract_sha256=_sha256_path(V22R_PROGRAM_CONTRACT_PATH), method_contract_sha256=_sha256_path(V22R_METHOD_CONTRACT_PATH), physical_program_sha256=physics_program_sha256, physical_object_sha256=physics_object_sha256)
    payload["lf5"] = {"schema_id": "phk-v23-lf5-checkpoint-metadata-v1", "task_id": TASK_ID, "role": role, "optimizer_update": update, "source_identity": source_identity, "contracts": dict(contracts), "parent_checkpoint_sha256": parent_sha256, "medium_labels_used": role == DEV_T_ROLE, "physics_residual_used": role == P0_ROLE, "stress_read": False}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle: torch.save(payload, handle)
    return path


def read_cpu_qualification(path: Path, *, allow_user_override: bool = False) -> dict[str, Any]:
    payload = _read_json(Path(path))
    identity_valid = payload.get("schema_id") == "phk-v23-lf5-cpu-qualification-v1" and payload.get("task_id") == TASK_ID and payload.get("contracts") == contract_identity()
    gate_passed = payload.get("status") == "LF5_CPU_T_QUALIFICATION_PASS" and payload.get("gpu_execution_authorized_by_cpu_gate") is True
    user_override_valid = allow_user_override and payload.get("status") == "LF5_TZL_ALIGNMENT_NOT_SUPPORTED_CPU" and payload.get("gpu_execution_authorized_by_cpu_gate") is False
    if not identity_valid or not (gate_passed or user_override_valid):
        raise PermissionError("LF5 CPU-T qualification is absent, stale, or failed")
    return {**payload, "post_qualification_user_override": bool(user_override_valid)}


def execute_reference_blind_gpu_campaign(*, output_root: Path, medium_carrier: Path, initial_checkpoint: Path, cpu_qualification_path: Path, device_name: str, source_identity: str, user_override_cpu_gate: bool = False) -> dict[str, Any]:
    contracts = load_contracts(); identities = contract_identity(); qualification = read_cpu_qualification(cpu_qualification_path, allow_user_override=user_override_cpu_gate)
    if not device_name.startswith("cuda") or not torch.cuda.is_available(): raise RuntimeError("LF5 requires CUDA")
    device = torch.device(device_name); gpu_name = torch.cuda.get_device_name(device)
    if gpu_name != "Tesla V100-PCIE-32GB": raise RuntimeError("LF5 requires Tesla V100-PCIE-32GB")
    output = Path(output_root).resolve(); output.mkdir(parents=True, exist_ok=False)
    config = build_training_config(device_name); physics, physics_program_sha256, physics_object_sha256 = load_case_physics(config.case_control)
    dataset = load_medium_dataset(Path(medium_carrier), physics=physics, contracts=contracts)
    if dataset.partition_sha256 != EXPECTED_PARTITION_SHA256: raise ValueError("LF5 qualified partition drift")
    started = time.perf_counter(); started_at = datetime.now(timezone.utc).isoformat(); random.seed(17); np.random.seed(17); torch.manual_seed(17); torch.cuda.manual_seed_all(17)
    parent_hash = _sha256_path(Path(initial_checkpoint))
    _write_json_exclusive(output / "manifest-start.json", {"schema_id":"phk-v23-lf5-run-manifest-v1","task_id":TASK_ID,"status":"RUNNING_REFERENCE_BLIND_GPU_CAMPAIGN","evidence_role":"POST_QUALIFICATION_USER_OVERRIDE_EXPLORATORY" if qualification["post_qualification_user_override"] else "PREREGISTERED_CPU_QUALIFIED","source_identity":source_identity,"contracts":identities,"gpu":gpu_name,"dtype":"FLOAT64","seed":17,"input_bindings":{"medium":{"sha256":_sha256_path(Path(medium_carrier))},"lf3_t0":{"sha256":parent_hash},"cpu_qualification":{"sha256":_sha256_path(Path(cpu_qualification_path))}},"cpu_gate_passed":not qualification["post_qualification_user_override"],"post_qualification_user_override":qualification["post_qualification_user_override"],"fine_extra_lf_only_evaluator_stress_read":False})
    model, _ = load_lf3_t0_model(Path(initial_checkpoint), physics=physics, config=config, device=device, expected_sha256=contracts["data"]["initial_checkpoint"]["sha256"])
    for field in ("potential", "temperature"):
        model.encoders[field].requires_grad_(False); model.heads[field].requires_grad_(False)
    phase_parameters = tuple(model.encoders["phase"].parameters()) + tuple(model.heads["phase"].parameters())
    vt_before = {field: _field_state_sha256(model, field) for field in ("potential", "temperature")}
    optimizer = torch.optim.Adam(phase_parameters, lr=1.0e-3, betas=(0.9,0.999), eps=1.0e-8, weight_decay=0.0, amsgrad=False)
    base_stream = BaseDevelopmentStream(dataset); band_stream = BandStream(InterfaceBandDataset(dataset)); temporal_stream = TemporalEdgeStream(TemporalEdgeDataset(dataset))
    telemetry_path = output / "dev-t-telemetry.jsonl"; hashes_path = output / "dev-t-batch-hashes.jsonl"; final_audit = None; executed = 0; numerical_valid = True
    with telemetry_path.open("x", encoding="utf-8", newline="\n") as telemetry, hashes_path.open("x", encoding="utf-8", newline="\n") as hashes:
        for step in range(1, DEV_UPDATES + 1):
            optimizer.zero_grad(set_to_none=True); base_batch = base_stream.draw(step); band_batch = band_stream.draw(step); temporal_batch = temporal_stream.draw(step)
            lbase = measure_decoupled_terms(model, base_batch, physics=physics, device=device)["phase_logit"]
            spatial = band_losses(model, band_batch, physics=physics, device=device); temporal = temporal_zero_level_terms(model, temporal_batch, physics=physics, device=device)
            loss = 0.50 * lbase + 0.25 * spatial["mse"] + 0.25 * temporal["loss"]
            if not bool(torch.isfinite(loss)): numerical_valid = False; break
            loss.backward(); grad_norm = _gradient_group_norm(phase_parameters)
            if not math.isfinite(grad_norm): numerical_valid = False; break
            torch.nn.utils.clip_grad_norm_(phase_parameters, 10.0); optimizer.step(); executed = step
            _append(hashes, {"step":step,"base_sha256":base_batch.batch_sha256,"spatial_sha256":band_batch.batch_sha256,"temporal_sha256":temporal_batch.batch_sha256})
            if step == 1 or step % 50 == 0:
                final_audit = full_medium_audit(model, dataset, device=device)
                _append(telemetry, {"step":step,"L_base":float(lbase.detach().cpu()),"L_spatial":float(spatial["mse"].detach().cpu()),"L_TZL":float(temporal["loss"].detach().cpu()),"L_total":float(loss.detach().cpu()),"spatial_pool_losses":{k:float(v.detach().cpu()) for k,v in spatial["pool_mse"].items()},"temporal_pool_reports":temporal["pool_reports"],"gradient_norm_before_clip":grad_norm,"stream_hashes":{"base":base_stream.window_sha256,"spatial":band_stream.rolling_sha256,"temporal":temporal_stream.rolling_sha256},"audit":final_audit})
            if time.perf_counter() - started > float(contracts["program"]["hard_limits"]["maximum_wall_seconds"]): raise RuntimeError("LF5_RUN_BOUND_EXCEEDED")
    if base_stream.window_sha256 != EXPECTED_BASE_WINDOW_SHA256 or band_stream.rolling_sha256 != EXPECTED_BAND_SHA256 or temporal_stream.rolling_sha256 != contracts["data"]["temporal_edge_stream"]["rolling_sha256"]:
        raise RuntimeError("LF5 DEV-T stream identity drift")
    vt_after = {field: _field_state_sha256(model, field) for field in ("potential", "temperature")}; vt_unchanged = vt_before == vt_after
    if not vt_unchanged: raise RuntimeError("LF5 DEV-T changed frozen V/T")
    if final_audit is None: final_audit = full_medium_audit(model, dataset, device=device)
    numerical_valid = bool(numerical_valid and final_audit["all_values_finite"] and final_audit["phase_range"]["passed"] and final_audit["potential_maximum_principle"]["passed"])
    gate = strict_carrier_gate(final_audit, qualification["lf1_b0_full_medium_audit"], vt_unchanged=vt_unchanged)
    dev_checkpoint = _write_checkpoint(output / "checkpoint-dev-t-step-400.pt", model=model, optimizer=optimizer, config=config, update=executed, role=DEV_T_ROLE, source_identity=source_identity, contracts=identities, parent_sha256=parent_hash, physics_program_sha256=physics_program_sha256, physics_object_sha256=physics_object_sha256)
    dev_prediction = write_prediction_carrier(checkpoint_path=dev_checkpoint, output_path=output / "prediction-dev-t-step-400.npz", device_name=device_name)
    dev_result = {"executed_updates":executed,"numerical_valid":numerical_valid,"audit":final_audit,"carrier_gate":gate,"V_T_state_sha256":{"before":vt_before,"after":vt_after},"checkpoint_sha256":_sha256_path(dev_checkpoint),"prediction_sha256":_sha256_path(dev_prediction),"stream_identities":{"base_window":base_stream.window_sha256,"spatial_band":band_stream.rolling_sha256,"temporal":temporal_stream.rolling_sha256}}
    p0_result = None; p0_checkpoint = None; p0_prediction = None
    if numerical_valid and gate["passed"]:
        for field in ("potential", "temperature"):
            model.encoders[field].requires_grad_(True); model.heads[field].requires_grad_(True)
        for parameter in phase_parameters: parameter.requires_grad_(False)
        phase_before = _phase_state_sha256(model)
        p0_optimizer = torch.optim.Adam(model.parameters(), lr=1.0e-3, betas=(0.9,0.999), eps=1.0e-8, weight_decay=0.0, amsgrad=False)
        physics_stream = LF0PhysicsBatchStream(physics=physics, interior_points=512, boundary_points=128, initial_points=128, refresh_updates=250, seed=17)
        p0_telemetry = output / "p0-telemetry.jsonl"; p0_hashes = output / "p0-physics-batch-hashes.jsonl"; final_p0_audit = None; step550 = None
        with p0_telemetry.open("x",encoding="utf-8",newline="\n") as telemetry, p0_hashes.open("x",encoding="utf-8",newline="\n") as hashes:
            for step in range(1, P0_UPDATES + 1):
                if step == P0_PHASE_FREEZE_STEPS + 1:
                    frozen_hash = _phase_state_sha256(model); state_count = sum(parameter in p0_optimizer.state for parameter in phase_parameters)
                    if frozen_hash != phase_before or state_count != 0: raise RuntimeError("LF5 P0 phase freeze identity drift")
                    for parameter in phase_parameters: parameter.requires_grad_(True)
                p0_optimizer.zero_grad(set_to_none=True); batch = physics_stream.draw(model, step, dtype=torch.float64, device=device); loss, components = _physics_objective(model, batch, config)
                if not bool(torch.isfinite(loss)): raise FloatingPointError("LF5 P0 non-finite objective")
                loss.backward(); trainable = tuple(parameter for parameter in model.parameters() if parameter.requires_grad); grad_norm = float(torch.nn.utils.clip_grad_norm_(trainable,10.0).detach().cpu()); p0_optimizer.step()
                _append(hashes,{"step":step,"interior_coordinate_sha256":batch.interior_sha256,"boundary_coordinate_sha256":batch.boundary_sha256,"initial_coordinate_sha256":batch.initial_sha256,"batch_sha256":batch.batch_sha256})
                if step == 1 or step % 50 == 0 or step in {550,551,1200}:
                    final_p0_audit = full_medium_audit(model,dataset,device=device)
                    _append(telemetry,{"step":step,**components,"total_loss":float(loss.detach().cpu()),"gradient_norm_before_clip":grad_norm,"phase_sha256":_phase_state_sha256(model),"phase_frozen":step<=550,"audit":final_p0_audit})
                if step == 550:
                    step550={"phase_before_sha256":phase_before,"phase_after_sha256":_phase_state_sha256(model),"bitwise_preserved":phase_before==_phase_state_sha256(model),"phase_optimizer_state_entries":sum(parameter in p0_optimizer.state for parameter in phase_parameters),"physics_hash_prefix":physics_stream.rolling_sha256,"finite":bool(final_p0_audit and final_p0_audit["all_values_finite"]),"potential_valid":bool(final_p0_audit and final_p0_audit["potential_maximum_principle"]["passed"])}
                if time.perf_counter()-started > float(contracts["program"]["hard_limits"]["maximum_wall_seconds"]): raise RuntimeError("LF5_RUN_BOUND_EXCEEDED")
        if physics_stream.rolling_sha256 != EXPECTED_P0_STREAM_SHA256: raise RuntimeError("LF5 P0 physics stream identity drift")
        assert final_p0_audit is not None
        preservation = p0_preservation_gate(final_p0_audit, final_audit, qualification["lf1_b0_full_medium_audit"])
        p0_checkpoint = _write_checkpoint(output/"checkpoint-p0-final.pt",model=model,optimizer=p0_optimizer,config=config,update=1200,role=P0_ROLE,source_identity=source_identity,contracts=identities,parent_sha256=_sha256_path(dev_checkpoint),physics_program_sha256=physics_program_sha256,physics_object_sha256=physics_object_sha256)
        p0_prediction = write_prediction_carrier(checkpoint_path=p0_checkpoint,output_path=output/"prediction-p0-final.npz",device_name=device_name)
        p0_result={"executed_updates":1200,"audit":final_p0_audit,"preservation_gate":preservation,"strict_gate":preservation["strict_gate"],"step550":step550,"physics_stream_sha256":physics_stream.rolling_sha256,"checkpoint_sha256":_sha256_path(p0_checkpoint),"prediction_sha256":_sha256_path(p0_prediction)}
    artifacts={"manifest_start":_artifact_record(output/"manifest-start.json",output),"dev_t_telemetry":_artifact_record(telemetry_path,output),"dev_t_batch_hashes":_artifact_record(hashes_path,output),"checkpoint_dev_t":_artifact_record(dev_checkpoint,output),"prediction_dev_t":_artifact_record(dev_prediction,output)}
    if p0_checkpoint is not None and p0_prediction is not None:
        artifacts.update({"checkpoint_p0":_artifact_record(p0_checkpoint,output),"prediction_p0":_artifact_record(p0_prediction,output),"p0_telemetry":_artifact_record(output/"p0-telemetry.jsonl",output),"p0_physics_batch_hashes":_artifact_record(output/"p0-physics-batch-hashes.jsonl",output)})
    status = "LF5_NUMERICAL_OR_IDENTITY_INVALID" if not numerical_valid else ("LF5_DEV_T_CARRIER_ESTABLISHED" if gate["passed"] else "LF5_DEV_T_CARRIER_NOT_ESTABLISHED")
    summary={"schema_id":"phk-v23-lf5-reference-blind-run-summary-v1","task_id":TASK_ID,"title":TITLE,"status":status,"evidence_role":"POST_QUALIFICATION_USER_OVERRIDE_EXPLORATORY" if qualification["post_qualification_user_override"] else "PREREGISTERED_CPU_QUALIFIED","cpu_gate_passed":not qualification["post_qualification_user_override"],"post_qualification_user_override":qualification["post_qualification_user_override"],"started_at_utc":started_at,"finished_at_utc":datetime.now(timezone.utc).isoformat(),"source_identity":source_identity,"gpu":gpu_name,"dtype":"FLOAT64","seed":17,"optimizer_updates":executed+(1200 if p0_result else 0),"DEV_T":dev_result,"P0_disposition":"EXECUTED" if p0_result else "NOT_RUN_DEV_T_GATE","P0":p0_result,"wall_seconds":time.perf_counter()-started,"artifacts":artifacts,"prediction_reference_free":True,"fine_extra_lf_only_evaluator_stress_read":False}
    _write_json_exclusive(output/"summary.json",summary); return summary


def _parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--output-root",type=Path,required=True); parser.add_argument("--medium-carrier",type=Path,required=True); parser.add_argument("--initial-checkpoint",type=Path,required=True); parser.add_argument("--cpu-qualification",type=Path,required=True); parser.add_argument("--device",default="cuda:0"); parser.add_argument("--source-identity",required=True); parser.add_argument("--user-override-cpu-gate",action="store_true"); return parser


def main(argv: Sequence[str] | None=None)->int:
    args=_parser().parse_args(argv); summary=execute_reference_blind_gpu_campaign(output_root=args.output_root,medium_carrier=args.medium_carrier,initial_checkpoint=args.initial_checkpoint,cpu_qualification_path=args.cpu_qualification,device_name=args.device,source_identity=args.source_identity,user_override_cpu_gate=args.user_override_cpu_gate); print(json.dumps({"status":summary["status"],"optimizer_updates":summary["optimizer_updates"],"P0_disposition":summary["P0_disposition"],"evidence_role":summary["evidence_role"]},sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())


__all__ = ["DEV_T_ROLE","P0_ROLE","TASK_ID","TEMPORAL_POOL_NAMES","TEMPORAL_SEEDS","TemporalBatch","TemporalEdgeDataset","TemporalEdgeStream","contract_identity","execute_reference_blind_gpu_campaign","load_contracts","p0_preservation_gate","precompute_temporal_stream_identity","strict_carrier_gate","temporal_pool_report","temporal_zero_level_terms"]
