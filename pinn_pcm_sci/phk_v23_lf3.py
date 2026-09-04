"""PHK-V2.3 LF3 measure-decoupled phase-latent carrier pilot.

T0 is a data-only neural-carrier experiment.  Only a carrier that passes the
frozen full-medium gate enters P0, where the unchanged full physics objective
is optimized without label replay.  Fine, extra-fine, the frozen evaluator,
and stress carriers are intentionally unreachable from this module.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
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
    _physics_objective,
    _read_json,
    _sha256_path,
    _write_json_exclusive,
)
from .phk_v23_lf2 import (
    CATEGORY_NAMES,
    CATEGORY_QUOTAS,
    M0_SEEDS,
    MeasureBatch,
    MeasureCalibratedBatchStream,
    MediumMeasureDataset,
    full_medium_audit as _lf2_full_medium_audit,
    load_lf1_b0_initialization,
    load_medium_dataset,
)


TASK_ID = "PHK_V23_LF3_MEASURE_DECOUPLED_STARTUP_SCALED_PHASE_LATENT_CARRIER_PILOT_EXECUTE"
TRAJECTORY = "LF3_MEASURE_DECOUPLED_PHASE_LATENT_CARRIER_PILOT"
T0_STAGE = "T0_MEASURE_DECOUPLED_PHASE_LATENT_CARRIER"
P0_STAGE = "P0_LABEL_FREE_FULL_PHYSICS_REFINEMENT"
T0_UPDATES = 1200
P0_UPDATES = 1200
PHASE_FREEZE_STEPS = 550
CLIP_EPSILON = 1.0e-8
PHASE_LATENT_SCALE = 8.0
LOGIT_SPAN = 36.84136146790473
Q_ABSOLUTE_BOUND = 4.605170183488091
EXPECTED_PARTITION_SHA256 = "EFD70886DD85AC467F06F38B48FB0EE6C0132471CE74817E3A4D68E752B7A515"
EXPECTED_T0_STREAM_SHA256 = "6E9957E861BE0FD10E19A1585635C7B2C323077D89908159B1736734FB548F28"
EXPECTED_P0_STREAM_SHA256 = "536E6706A0B68EBB1277A97F402D273AFA2EA1E0B27106F26CB4222B7EC05C53"

PROGRAM_CONTRACT_PATH = ROOT / "configs" / "phk_v23" / "program_contract_lf3_phase_latent_carrier.json"
METHOD_CONTRACT_PATH = ROOT / "configs" / "phk_v23" / "method_contract_lf3_phase_latent_carrier.json"
DATA_CONTRACT_PATH = ROOT / "configs" / "phk_v23" / "data_contract_lf3_phase_latent_carrier.json"
DECISION_CONTRACT_PATH = ROOT / "configs" / "phk_v23" / "decision_contract_lf3_phase_latent_carrier.json"
CONTRACT_PATHS = {
    "program": PROGRAM_CONTRACT_PATH,
    "method": METHOD_CONTRACT_PATH,
    "data": DATA_CONTRACT_PATH,
    "decision": DECISION_CONTRACT_PATH,
}
EXPECTED_SCHEMAS = {
    "program": "phk-v23-lf3-program-contract-v1",
    "method": "phk-v23-lf3-method-contract-v1",
    "data": "phk-v23-lf3-data-contract-v1",
    "decision": "phk-v23-lf3-decision-contract-v1",
}


def load_contracts() -> dict[str, dict[str, Any]]:
    contracts = {name: _read_json(path) for name, path in CONTRACT_PATHS.items()}
    for name, schema in EXPECTED_SCHEMAS.items():
        if contracts[name].get("schema_id") != schema:
            raise ValueError(f"unsupported LF3 {name} contract")
    relative = {name: path.relative_to(ROOT).as_posix() for name, path in CONTRACT_PATHS.items()}
    program, method, data, decision = (
        contracts["program"], contracts["method"], contracts["data"], contracts["decision"]
    )
    if program.get("phase_id") != TASK_ID:
        raise ValueError("LF3 task identity drift")
    if (
        method.get("program_contract") != relative["program"]
        or data.get("program_contract") != relative["program"]
        or decision.get("program_contract") != relative["program"]
        or decision.get("method_contract") != relative["method"]
        or decision.get("data_contract") != relative["data"]
    ):
        raise ValueError("LF3 cross-contract identity drift")
    limits = program["hard_limits"]
    if (
        limits.get("maximum_scientific_gpu_trajectories") != 1
        or limits.get("maximum_optimizer_updates") != 2400
        or limits.get("gpu_price_or_cost_reporting") is not False
    ):
        raise ValueError("LF3 run bounds drift")
    common = method["common_identity"]
    if (
        common.get("gpu") != "TESLA_V100_PCIE_32GB_ONLY"
        or common.get("dtype") != "FLOAT64"
        or common.get("seed") != 17
        or common.get("potential_transform") != POTENTIAL_TRANSFORM_EXACT_TOP_RANGE_PRESERVING
        or float(common.get("clip_epsilon")) != CLIP_EPSILON
        or float(common.get("phase_latent_scale")) != PHASE_LATENT_SCALE
    ):
        raise ValueError("LF3 model identity drift")
    trajectory = method["trajectory"]
    if (
        trajectory["T0"].get("updates") != T0_UPDATES
        or trajectory["P0"].get("updates") != P0_UPDATES
        or trajectory.get("maximum_global_updates") != T0_UPDATES + P0_UPDATES
    ):
        raise ValueError("LF3 stage bounds drift")
    proposal = data["T0_proposal_per_step"]
    if (
        tuple(proposal.get("category_quotas_in_partition_order", ())) != CATEGORY_QUOTAS
        or tuple(proposal.get("sobol_seeds_in_partition_order", ())) != M0_SEEDS
        or proposal.get("rolling_sha256") != EXPECTED_T0_STREAM_SHA256
        or data["P0_physics_stream"].get("rolling_sha256") != EXPECTED_P0_STREAM_SHA256
        or data["target_measure"].get("partition_sha256") != EXPECTED_PARTITION_SHA256
    ):
        raise ValueError("LF3 sampling identity drift")
    if tuple(data["partition"].get("priority_order", ())) != CATEGORY_NAMES:
        raise ValueError("LF3 partition identity drift")
    if decision.get("stress_status") != "TWO_STRESS_REFERENCES_SEALED_UNREAD":
        raise PermissionError("LF3 stress boundary drift")
    if len(decision.get("machine_outcomes_and_unique_next", {})) != 15:
        raise ValueError("LF3 machine outcome mapping is incomplete")
    return contracts


def contract_identity() -> dict[str, dict[str, str]]:
    return {
        name: {"path": path.relative_to(ROOT).as_posix(), "sha256": _sha256_path(path)}
        for name, path in CONTRACT_PATHS.items()
    }


def build_training_config(device_name: str) -> PhkTrainingConfig:
    config = PhkTrainingConfig(
        arm="STRONG_RAW", case_control="FULL", updates=2400, seed=17,
        hidden_width=64, hidden_layers=4, frequency_band="BAND_A",
        learning_rate=1.0e-3, gradient_clip_norm=10.0,
        interior_points=512, boundary_points=128, initial_points=128,
        candidate_pool_multiplier=4, refresh_updates=250, log_every=50,
        checkpoint_every=2400, pde_weight=1.0, boundary_weight=5.0,
        initial_weight=1.0, dtype="float64", device=device_name,
    )
    config.validate()
    return config


def startup_factor(time_value: torch.Tensor, physics: PhkV22RPhysics) -> torch.Tensor:
    return 1.0 - torch.exp(-(time_value - physics.time_start) / 0.35)


def phase_logit_targets(
    coordinates: torch.Tensor,
    phase_target: torch.Tensor,
    *,
    physics: PhkV22RPhysics,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    initial = physics.initial_phase(coordinates).clamp(CLIP_EPSILON, 1.0 - CLIP_EPSILON)
    target = phase_target.clamp(CLIP_EPSILON, 1.0 - CLIP_EPSILON)
    delta = torch.logit(target) - torch.logit(initial)
    startup = startup_factor(coordinates[:, 2:3], physics)
    mask = coordinates[:, 2:3] > physics.time_start
    return delta, startup, mask


def measure_decoupled_terms(
    model: PhkV22RModel,
    batch: MeasureBatch,
    *,
    physics: PhkV22RPhysics,
    device: torch.device,
) -> dict[str, Any]:
    """Return target-measure V/T and equal-category phase-logit losses."""

    coordinates = batch.coordinates.to(device=device, dtype=torch.float64)
    target = batch.targets.to(device=device, dtype=torch.float64)
    diagnostics = model.read_only_output_diagnostics(coordinates)
    prediction = diagnostics.output.fields
    squared_v = ((prediction[:, 0] - target[:, 0]) / physics.waveform_amplitude).square()
    squared_t = ((prediction[:, 1] - target[:, 1]) / physics.theta_transition).square()
    delta_star, startup, mask = phase_logit_targets(
        coordinates, target[:, 2:3], physics=physics
    )
    delta_theta = PHASE_LATENT_SCALE * startup * diagnostics.latents["phase"]
    latent_squared = ((delta_theta - delta_star) / LOGIT_SPAN).square().reshape(-1)
    mask_flat = mask.reshape(-1)
    potential = prediction.new_zeros(())
    temperature = prediction.new_zeros(())
    phase_logit = prediction.new_zeros(())
    category_phase: dict[str, torch.Tensor] = {}
    offset = 0
    for name in CATEGORY_NAMES:
        count = int(batch.category_counts[name])
        stop = offset + count
        mass = float(batch.category_masses[name])
        potential = potential + mass * torch.mean(squared_v[offset:stop])
        temperature = temperature + mass * torch.mean(squared_t[offset:stop])
        selected = latent_squared[offset:stop][mask_flat[offset:stop]]
        if selected.numel() == 0:
            raise ValueError(f"LF3 T0 category has no t>t0 phase-teacher nodes: {name}")
        category_phase[name] = torch.mean(selected)
        phase_logit = phase_logit + category_phase[name] / len(CATEGORY_NAMES)
        offset = stop
    if offset != prediction.shape[0]:
        raise ValueError("LF3 category slices do not cover the T0 batch")
    return {
        "potential": potential,
        "temperature": temperature,
        "phase_logit": phase_logit,
        "total": (potential + temperature + phase_logit) / 3.0,
        "category_phase_logit": category_phase,
        "delta_logit_target_min": torch.min(delta_star),
        "delta_logit_target_max": torch.max(delta_star),
        "phase_teacher_mask_fraction": torch.mean(mask.to(dtype=torch.float64)),
    }


def medium_event_topology(phase: np.ndarray, dataset: MediumMeasureDataset) -> dict[str, Any]:
    values = np.asarray(phase, dtype=np.float64).reshape(dataset.time.size, dataset.cell_count)
    roi_fraction = np.mean(values[:, dataset.roi_cells] >= 0.5, axis=1)
    full_fraction = np.mean(values >= 0.5, axis=1)
    outside_fraction = np.mean(values[:, ~dataset.roi_cells] >= 0.5, axis=1)
    cycles: list[dict[str, Any]] = []
    failures: list[str] = []
    period = float(dataset.result.case.period)
    for cycle_index in range(2):
        start, end = cycle_index * period, (cycle_index + 1) * period
        mask = (dataset.time >= start) & (dataset.time <= end if cycle_index == 1 else dataset.time < end)
        indices = np.flatnonzero(mask)
        series = roi_fraction[indices]
        peak_position = int(np.argmax(series))
        peak_index = int(indices[peak_position])
        crossing = None
        for before, after in zip(indices[:-1], indices[1:], strict=True):
            low, high = float(roi_fraction[before]), float(roi_fraction[after])
            if low < 0.02 <= high and high > low:
                fraction = (0.02 - low) / (high - low)
                crossing = float(dataset.time[before] + fraction * (dataset.time[after] - dataset.time[before]))
                break
        pre, peak = float(series[0]), float(series[peak_position])
        excursion = peak - pre
        recovery = float((peak - float(series[-1])) / excursion) if excursion > 0.0 else 0.0
        cycle = {
            "cycle": cycle_index + 1, "event_time": crossing,
            "pre_roi_fraction": pre, "peak_roi_fraction": peak,
            "peak_full_domain_fraction": float(full_fraction[peak_index]),
            "peak_outside_roi_fraction": float(outside_fraction[peak_index]),
            "recovery_fraction": recovery, "peak_time_index": peak_index,
        }
        cycles.append(cycle)
        prefix = f"cycle_{cycle_index + 1}"
        if crossing is None: failures.append(f"{prefix}_event_missing")
        if peak < 0.02: failures.append(f"{prefix}_roi_peak_below_minimum")
        if cycle["peak_full_domain_fraction"] > 0.45: failures.append(f"{prefix}_false_global_transition")
        if cycle["peak_outside_roi_fraction"] > 0.10: failures.append(f"{prefix}_locality_failure")
        if recovery < 0.70: failures.append(f"{prefix}_recovery_failure")
    return {"cycles": cycles, "failures": failures, "passed": not failures}


def full_medium_audit(
    model: PhkV22RModel,
    dataset: MediumMeasureDataset,
    *,
    device: torch.device,
    absolute_tolerance: float = 1.0e-6,
) -> dict[str, Any]:
    audit = _lf2_full_medium_audit(
        model, dataset, device=device, absolute_tolerance=absolute_tolerance
    )
    # The LF2 helper intentionally returns aggregate fields only.  A second
    # chunked prediction is acceptable at sparse telemetry points and keeps
    # the cloud bundle independent of the frozen evaluator implementation.
    from .phk_v23_lf2 import _predict_medium

    prediction = _predict_medium(model, dataset, device=device)
    phase = prediction[:, 2]
    audit["phase_range"] = {
        "minimum": float(np.min(phase)), "maximum": float(np.max(phase)),
        "passed": bool(np.min(phase) >= -1.0e-10 and np.max(phase) <= 1.0 + 1.0e-10),
    }
    audit["event_topology_hard_guard"] = medium_event_topology(phase, dataset)
    return audit


def carrier_gate(
    audit: Mapping[str, Any],
    lf1_b0: Mapping[str, Any],
    *,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    gate = contract["T0_carrier_competence_gate"]
    checks: dict[str, bool] = {
        "all_values_finite": audit.get("all_values_finite") is True,
        "phase_range": audit.get("phase_range", {}).get("passed") is True,
        "potential_guard_pass": audit.get("potential_maximum_principle", {}).get("passed") is True,
        "phase_maximum": float(audit.get("phase_maximum", -math.inf)) >= float(gate["phase_maximum_minimum"]),
        "two_cycle_events": audit.get("two_cycle_events") is True,
    }
    for cycle_index, cycle in enumerate(("cycle_1", "cycle_2")):
        metrics = audit["event_metrics"][cycle]
        checks[f"{cycle}:hard_recall"] = metrics["hard_recall"] is not None and float(metrics["hard_recall"]) >= float(gate["hard_recall_each_cycle_minimum"])
        checks[f"{cycle}:hard_precision"] = metrics["hard_precision"] is not None and float(metrics["hard_precision"]) >= float(gate["hard_precision_each_cycle_minimum"])
        ratio = metrics["hard_active_mass_ratio"]
        checks[f"{cycle}:hard_active_mass_ratio"] = ratio is not None and float(gate["hard_active_mass_ratio_each_cycle_minimum"]) <= float(ratio) <= float(gate["hard_active_mass_ratio_each_cycle_maximum"])
        timing = metrics["event_time_absolute_error"]
        checks[f"{cycle}:event_time"] = timing is not None and float(timing) <= float(gate["event_time_absolute_error_each_cycle_maximum"])
        topology = audit["event_topology_hard_guard"]["cycles"][cycle_index]
        checks[f"{cycle}:roi_peak"] = float(topology["peak_roi_fraction"]) >= float(gate["roi_peak_fraction_each_cycle_minimum"])
        checks[f"{cycle}:full_domain_peak"] = float(topology["peak_full_domain_fraction"]) <= float(gate["full_domain_peak_fraction_each_cycle_maximum"])
        checks[f"{cycle}:outside_roi_peak"] = float(topology["peak_outside_roi_fraction"]) <= float(gate["outside_roi_peak_fraction_each_cycle_maximum"])
        checks[f"{cycle}:recovery"] = float(topology["recovery_fraction"]) >= float(gate["recovery_fraction_each_cycle_minimum"])
    ratios: dict[str, float] = {}
    for field, key in (
        ("potential", "potential_weighted_mse_to_lf1_b0_maximum_ratio"),
        ("temperature", "temperature_weighted_mse_to_lf1_b0_maximum_ratio"),
        ("phase", "phase_weighted_mse_to_lf1_b0_maximum_ratio"),
    ):
        ratios[field] = float(audit["weighted_errors"][field]) / max(float(lf1_b0["weighted_errors"][field]), 1.0e-12)
        checks[f"{field}_weighted_mse"] = ratios[field] <= float(gate[key])
    failed = sorted(name for name, passed in checks.items() if not passed)
    temporal_names = {f"cycle_{i}:{name}" for i in (1, 2) for name in ("event_time", "recovery")}
    temporal_only = bool(failed and set(failed).issubset(temporal_names))
    return {
        "passed": not failed, "checks": checks, "failed_checks": failed,
        "temporal_only_failure": temporal_only,
        "weighted_mse_ratios_to_lf1_b0": ratios,
        "failure_outcome": None if not failed else ("LF3_TEMPORAL_CARRIER_FAILURE" if temporal_only else "LF3_CARRIER_NOT_ESTABLISHED"),
    }


def p0_preservation_gate(
    audit: Mapping[str, Any],
    t0_audit: Mapping[str, Any],
    lf1_b0: Mapping[str, Any],
    *,
    contract: Mapping[str, Any],
    physics_stream_sha256: str,
) -> dict[str, Any]:
    competence = carrier_gate(audit, lf1_b0, contract=contract)
    limits = contract["P0_preservation_gate"]
    ratios = {
        field: float(audit["weighted_errors"][field]) / max(float(t0_audit["weighted_errors"][field]), 1.0e-12)
        for field in ("potential", "temperature", "phase")
    }
    ratios["topology"] = float(audit["topology_weighted_loss"]) / max(float(t0_audit["topology_weighted_loss"]), 1.0e-12)
    checks = dict(competence["checks"])
    for field in ("potential", "temperature", "phase"):
        checks[f"{field}_preserved_vs_T0"] = ratios[field] <= float(limits[f"{field}_weighted_mse_to_T0_maximum_ratio"])
    checks["topology_preserved_vs_T0"] = ratios["topology"] <= float(limits["topology_weighted_loss_to_T0_maximum_ratio"])
    checks["physics_stream_identity"] = physics_stream_sha256 == limits["physics_stream_rolling_sha256"]
    return {
        "passed": all(checks.values()), "checks": checks,
        "error_ratios_to_T0": ratios,
        "failure_outcome": None if all(checks.values()) else "LF3_P0_PRESERVATION_FAILED",
    }


def read_cpu_qualification(path: Path) -> dict[str, Any]:
    payload = _read_json(Path(path))
    if (
        payload.get("schema_id") != "phk-v23-lf3-cpu-qualification-v1"
        or payload.get("task_id") != TASK_ID
        or payload.get("status") != "LF3_CPU_QUALIFICATION_PASS"
        or payload.get("gpu_execution_authorized_by_cpu_gate") is not True
        or payload.get("contracts") != contract_identity()
        or payload.get("fine_extra_fine_reference_read") is not False
        or payload.get("stress_fields_or_metrics_read") is not False
    ):
        raise PermissionError("LF3 CPU qualification is absent, stale, or failed")
    return payload


def _write_checkpoint(
    path: Path,
    *,
    model: PhkV22RModel,
    optimizer: torch.optim.Optimizer,
    config: PhkTrainingConfig,
    global_step: int,
    stage: str,
    source_identity: str,
    contracts: Mapping[str, Mapping[str, str]],
    parent_checkpoint_sha256: str,
    physics_program_sha256: str,
    physics_object_sha256: str,
) -> Path:
    payload = _checkpoint_payload(
        model=model, optimizer=optimizer, config=config, update=global_step,
        program_contract_sha256=_sha256_path(V22R_PROGRAM_CONTRACT_PATH),
        method_contract_sha256=_sha256_path(V22R_METHOD_CONTRACT_PATH),
        physical_program_sha256=physics_program_sha256,
        physical_object_sha256=physics_object_sha256,
    )
    payload["lf3"] = {
        "schema_id": "phk-v23-lf3-checkpoint-metadata-v1", "task_id": TASK_ID,
        "trajectory": TRAJECTORY, "stage": stage,
        "global_optimizer_step": global_step, "source_identity": source_identity,
        "contracts": dict(contracts), "parent_checkpoint_sha256": parent_checkpoint_sha256,
        "medium_training_labels_used": stage == T0_STAGE,
        "physics_residual_used": stage == P0_STAGE,
        "prediction_reference_free": True, "stress_fields_or_metrics_read": False,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        torch.save(payload, handle)
    return path


def _append(handle: Any, payload: Mapping[str, Any]) -> None:
    handle.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n")
    handle.flush()


def _state_sha256(module: torch.nn.Module) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(module.state_dict().items()):
        digest.update(name.encode("utf-8"))
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest().upper()


def _phase_state_sha256(model: PhkV22RModel) -> str:
    digest = hashlib.sha256()
    for prefix, module in (("encoder", model.encoders["phase"]), ("head", model.heads["phase"])):
        for name, value in sorted(module.state_dict().items()):
            digest.update(f"{prefix}:{name}".encode("utf-8"))
            digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest().upper()


def execute_reference_blind_gpu_trajectory(
    *,
    output_root: Path,
    medium_carrier: Path,
    initial_checkpoint: Path,
    cpu_qualification_path: Path,
    device_name: str,
    source_identity: str,
) -> dict[str, Any]:
    contracts = load_contracts()
    identities = contract_identity()
    qualification = read_cpu_qualification(cpu_qualification_path)
    if not device_name.startswith("cuda") or not torch.cuda.is_available():
        raise RuntimeError("LF3 scientific execution requires CUDA")
    device = torch.device(device_name)
    gpu_name = torch.cuda.get_device_name(device)
    if gpu_name != "Tesla V100-PCIE-32GB":
        raise RuntimeError("LF3 requires Tesla V100-PCIE-32GB")
    output = Path(output_root).resolve()
    output.mkdir(parents=True, exist_ok=False)
    config = build_training_config(device_name)
    physics, physics_program_sha256, physics_object_sha256 = load_case_physics(config.case_control)
    dataset = load_medium_dataset(Path(medium_carrier), physics=physics, contracts=contracts)
    model, _ = load_lf1_b0_initialization(
        Path(initial_checkpoint), physics=physics, config=config,
        contracts=contracts, device=device,
    )
    if dataset.partition_sha256 != qualification["partition"]["partition_sha256"]:
        raise ValueError("LF3 CPU-qualified partition drift")
    baseline = qualification.get("lf1_b0_full_medium_audit")
    if not isinstance(baseline, Mapping):
        raise ValueError("LF3 qualification lacks LF1-B0 baseline")

    random.seed(17); np.random.seed(17); torch.manual_seed(17); torch.cuda.manual_seed_all(17)
    torch.cuda.reset_peak_memory_stats(device)
    started_at = datetime.now(timezone.utc).isoformat()
    started = time.perf_counter()
    parent_hash = _sha256_path(Path(initial_checkpoint))
    _write_json_exclusive(output / "manifest-start.json", {
        "schema_id": "phk-v23-lf3-run-manifest-v1", "task_id": TASK_ID,
        "status": "RUNNING_REFERENCE_BLIND_GPU_TRAJECTORY", "started_at_utc": started_at,
        "source_identity": source_identity, "contracts": identities,
        "trajectory": TRAJECTORY, "training_config": asdict(config),
        "training_config_sha256": config.identity, "architecture": model.architecture_manifest(),
        "device": gpu_name, "dtype": "FLOAT64", "seed": 17,
        "input_bindings": {
            "medium": {"path": str(Path(medium_carrier).resolve()), "sha256": _sha256_path(Path(medium_carrier))},
            "lf1_b0_checkpoint": {"path": str(Path(initial_checkpoint).resolve()), "sha256": parent_hash},
            "cpu_qualification": {"path": str(Path(cpu_qualification_path).resolve()), "sha256": _sha256_path(Path(cpu_qualification_path))},
        },
        "fine_extra_fine_lf_only_evaluator_read": False,
        "stress_fields_or_metrics_read": False, "manual_early_stop": False,
        "accuracy_checkpoint_selection": False, "gpu_price_or_cost_reported": False,
    })
    maximum_seconds = float(contracts["program"]["hard_limits"]["maximum_wall_seconds"])
    t0_stream = MeasureCalibratedBatchStream(dataset, role="M0")
    t0_optimizer = torch.optim.Adam(model.parameters(), lr=1.0e-3, betas=(0.9, 0.999), eps=1.0e-8, weight_decay=0.0, amsgrad=False)
    t0_audit = None
    p0_audit = None
    p0_gate = None
    p0_stream = None
    t0_gate = None
    checkpoints: dict[str, Path] = {}
    predictions: dict[str, Path] = {}
    executed = 0
    minimum_total = math.inf
    t0_audit_steps = {1, 50, 100, 200, 400, 800, 1200}
    p0_audit_steps = {1, 50, 100, 200, 400, 600, 800, 1000, 1200}
    log_path = output / "training-log.jsonl"
    data_hash_path = output / "T0-measure-batch-hashes.jsonl"
    physics_hash_path = output / "P0-physics-batch-hashes.jsonl"
    audit_path = output / "full-medium-audits.jsonl"

    def step(total: torch.Tensor, optimizer: torch.optim.Optimizer, parameters: Sequence[torch.nn.Parameter]) -> tuple[float, float]:
        nonlocal minimum_total
        if not bool(torch.isfinite(total)):
            raise FloatingPointError("LF3 non-finite objective")
        total.backward()
        norm = torch.nn.utils.clip_grad_norm_(parameters, 10.0)
        if not bool(torch.isfinite(norm)):
            raise FloatingPointError("LF3 non-finite gradient")
        optimizer.step()
        value = float(total.detach().cpu())
        minimum_total = min(minimum_total, value)
        if time.perf_counter() - started > maximum_seconds:
            raise RuntimeError("LF3_RUN_BOUND_EXCEEDED")
        return value, float(norm.detach().cpu())

    with (
        log_path.open("x", encoding="utf-8", newline="\n") as log_handle,
        data_hash_path.open("x", encoding="utf-8", newline="\n") as data_handle,
        physics_hash_path.open("x", encoding="utf-8", newline="\n") as physics_handle,
        audit_path.open("x", encoding="utf-8", newline="\n") as audit_handle,
    ):
        for global_step in range(1, T0_UPDATES + 1):
            t0_optimizer.zero_grad(set_to_none=True)
            batch = t0_stream.draw(global_step)
            terms = measure_decoupled_terms(model, batch, physics=physics, device=device)
            total_value, grad_norm = step(terms["total"], t0_optimizer, tuple(model.parameters()))
            executed = global_step
            _append(data_handle, {"global_step": global_step, "stage": T0_STAGE, "batch_sha256": batch.batch_sha256, "category_counts": batch.category_counts})
            if global_step in t0_audit_steps:
                scalars = {
                    "potential_loss": float(terms["potential"].detach().cpu()),
                    "temperature_loss": float(terms["temperature"].detach().cpu()),
                    "phase_logit_loss": float(terms["phase_logit"].detach().cpu()),
                    "total_loss": total_value, "gradient_norm_before_clip": grad_norm,
                }
                _append(log_handle, {"global_step": global_step, "stage": T0_STAGE, **scalars})
                t0_audit = full_medium_audit(model, dataset, device=device, absolute_tolerance=1.0e-6)
                _append(audit_handle, {"global_step": global_step, "stage": T0_STAGE, **t0_audit})
        if t0_stream.rolling_sha256 != EXPECTED_T0_STREAM_SHA256:
            raise RuntimeError("LF3 T0 batch-stream identity drift")
        assert t0_audit is not None
        checkpoints["t0"] = _write_checkpoint(
            output / "checkpoint-t0-step-1200.pt", model=model, optimizer=t0_optimizer,
            config=config, global_step=1200, stage=T0_STAGE, source_identity=source_identity,
            contracts=identities, parent_checkpoint_sha256=parent_hash,
            physics_program_sha256=physics_program_sha256, physics_object_sha256=physics_object_sha256,
        )
        predictions["t0"] = write_prediction_carrier(
            checkpoint_path=checkpoints["t0"], output_path=output / "prediction-t0-step-1200.npz", device_name=device_name
        )
        t0_gate = carrier_gate(t0_audit, baseline, contract=contracts["decision"])
        _write_json_exclusive(output / "t0-carrier-gate.json", t0_gate)

        numerical_valid = bool(
            t0_audit["all_values_finite"]
            and t0_audit["phase_range"]["passed"]
            and t0_audit["potential_maximum_principle"]["passed"]
        )
        status = "LF3_NUMERICAL_OR_IDENTITY_INVALID" if not numerical_valid else str(t0_gate["failure_outcome"] or "LF3_T0_CARRIER_ESTABLISHED")
        phase_freeze = None
        if numerical_valid and t0_gate["passed"]:
            phase_parameters = tuple(model.heads["phase"].parameters())
            for parameter in phase_parameters:
                parameter.requires_grad_(False)
            phase_before = _phase_state_sha256(model)
            p0_optimizer = torch.optim.Adam(model.parameters(), lr=1.0e-3, betas=(0.9, 0.999), eps=1.0e-8, weight_decay=0.0, amsgrad=False)
            p0_stream = LF0PhysicsBatchStream(
                physics=physics, interior_points=512, boundary_points=128,
                initial_points=128, refresh_updates=250, seed=17,
            )
            for local_step in range(1, P0_UPDATES + 1):
                if local_step == PHASE_FREEZE_STEPS + 1:
                    phase_after_frozen = _phase_state_sha256(model)
                    if phase_after_frozen != phase_before:
                        raise RuntimeError("LF3 phase parameters changed during frozen P0 block")
                    phase_state_entries_before_unfreeze = sum(parameter in p0_optimizer.state for parameter in phase_parameters)
                    if phase_state_entries_before_unfreeze != 0:
                        raise RuntimeError("LF3 phase optimizer state appeared before unfreeze")
                    for parameter in phase_parameters:
                        parameter.requires_grad_(True)
                global_step = T0_UPDATES + local_step
                p0_optimizer.zero_grad(set_to_none=True)
                physics_batch = p0_stream.draw(model, local_step, dtype=torch.float64, device=device)
                physics_loss, physics_components = _physics_objective(model, physics_batch, config)
                trainable = tuple(parameter for parameter in model.parameters() if parameter.requires_grad)
                total_value, grad_norm = step(physics_loss, p0_optimizer, trainable)
                executed = global_step
                _append(physics_handle, {
                    "global_step": global_step, "physics_local_step": local_step,
                    "active_windows": physics_batch.active_windows, "refreshed": physics_batch.refreshed,
                    "interior_coordinate_sha256": physics_batch.interior_sha256,
                    "boundary_coordinate_sha256": physics_batch.boundary_sha256,
                    "initial_coordinate_sha256": physics_batch.initial_sha256,
                    "batch_sha256": physics_batch.batch_sha256,
                })
                if local_step in p0_audit_steps:
                    _append(log_handle, {"global_step": global_step, "stage": P0_STAGE, **physics_components, "total_loss": total_value, "gradient_norm_before_clip": grad_norm, "phase_frozen": local_step <= PHASE_FREEZE_STEPS})
                    p0_audit = full_medium_audit(model, dataset, device=device, absolute_tolerance=1.0e-6)
                    _append(audit_handle, {"global_step": global_step, "stage": P0_STAGE, **p0_audit})
            assert p0_audit is not None and p0_stream is not None
            phase_freeze = {
                "steps": [1, PHASE_FREEZE_STEPS], "before_sha256": phase_before,
                "after_sha256": phase_after_frozen, "bitwise_preserved": phase_before == phase_after_frozen,
                "phase_optimizer_state_entries_before_unfreeze": phase_state_entries_before_unfreeze,
            }
            p0_gate = p0_preservation_gate(
                p0_audit, t0_audit, baseline, contract=contracts["decision"],
                physics_stream_sha256=p0_stream.rolling_sha256,
            )
            _write_json_exclusive(output / "p0-preservation-gate.json", p0_gate)
            checkpoints["p0"] = _write_checkpoint(
                output / "checkpoint-p0-final.pt", model=model, optimizer=p0_optimizer,
                config=config, global_step=2400, stage=P0_STAGE, source_identity=source_identity,
                contracts=identities, parent_checkpoint_sha256=_sha256_path(checkpoints["t0"]),
                physics_program_sha256=physics_program_sha256, physics_object_sha256=physics_object_sha256,
            )
            predictions["p0"] = write_prediction_carrier(
                checkpoint_path=checkpoints["p0"], output_path=output / "prediction-p0-final.npz", device_name=device_name
            )
            p0_numerical = bool(p0_audit["all_values_finite"] and p0_audit["phase_range"]["passed"] and p0_audit["potential_maximum_principle"]["passed"])
            status = "LF3_NUMERICAL_OR_IDENTITY_INVALID" if not p0_numerical else ("LF3_REFERENCE_BLIND_GPU_TRAJECTORY_COMPLETE" if p0_gate["passed"] else "LF3_P0_PRESERVATION_FAILED")

    artifacts: dict[str, Any] = {
        "manifest_start": _artifact_record(output / "manifest-start.json", output),
        "training_log": _artifact_record(log_path, output),
        "T0_measure_batch_hashes": _artifact_record(data_hash_path, output),
        "full_medium_audits": _artifact_record(audit_path, output),
        "checkpoint_t0": _artifact_record(checkpoints["t0"], output),
        "prediction_t0": _artifact_record(predictions["t0"], output),
        "T0_gate": _artifact_record(output / "t0-carrier-gate.json", output),
    }
    if p0_stream is not None:
        artifacts.update({
            "P0_physics_batch_hashes": _artifact_record(physics_hash_path, output),
            "P0_gate": _artifact_record(output / "p0-preservation-gate.json", output),
            "checkpoint_p0": _artifact_record(checkpoints["p0"], output),
            "prediction_p0": _artifact_record(predictions["p0"], output),
        })
    summary = {
        "schema_id": "phk-v23-lf3-reference-blind-run-summary-v1",
        "task_id": TASK_ID, "trajectory": TRAJECTORY, "status": status,
        "started_at_utc": started_at, "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_identity": source_identity, "contracts": identities,
        "gpu": gpu_name, "dtype": "FLOAT64", "seed": 17,
        "optimizer_updates": executed,
        "stage_updates": {T0_STAGE: min(executed, 1200), P0_STAGE: max(executed - 1200, 0)},
        "T0_measure_draws": t0_stream.draw_count,
        "T0_measure_rolling_sha256": t0_stream.rolling_sha256,
        "P0_medium_draws": 0,
        "P0_physics_draws": 0 if p0_stream is None else p0_stream.local_step,
        "P0_physics_rolling_sha256": None if p0_stream is None else p0_stream.rolling_sha256,
        "P0_disposition": "EXECUTED" if p0_stream is not None else "NOT_TRIGGERED_BECAUSE_T0_GATE_FAILED",
        "phase_freeze": phase_freeze, "minimum_training_objective": minimum_total,
        "T0_audit": t0_audit, "T0_gate": t0_gate, "P0_audit": p0_audit, "P0_gate": p0_gate,
        "wall_seconds_including_predictions": time.perf_counter() - started,
        "artifacts": artifacts, "prediction_reference_free": True,
        "fine_extra_fine_lf_only_or_evaluator_read": False,
        "stress_fields_or_metrics_read": False, "gpu_price_or_cost_reported": False,
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    summary = execute_reference_blind_gpu_trajectory(
        output_root=args.output_root, medium_carrier=args.medium_carrier,
        initial_checkpoint=args.initial_checkpoint, cpu_qualification_path=args.cpu_qualification,
        device_name=args.device, source_identity=args.source_identity,
    )
    print(json.dumps({"status": summary["status"], "optimizer_updates": summary["optimizer_updates"], "output_root": str(args.output_root.resolve())}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CLIP_EPSILON", "LOGIT_SPAN", "P0_STAGE", "Q_ABSOLUTE_BOUND", "TASK_ID",
    "T0_STAGE", "carrier_gate", "contract_identity", "execute_reference_blind_gpu_trajectory",
    "full_medium_audit", "load_contracts", "measure_decoupled_terms",
    "medium_event_topology", "p0_preservation_gate", "phase_logit_targets", "startup_factor",
]
