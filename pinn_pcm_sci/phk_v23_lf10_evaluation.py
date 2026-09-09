"""Post-shutdown LF10 threshold robustness and terminal adjudication."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .phk_benchmark import PhkControl
from .phk_v22r_evaluator import evaluate_prediction, load_reference
from .phk_v22r_prediction import _load_model, read_prediction_carrier
from .phk_v22r_training import ROOT, load_case_physics
from .phk_v23_lf0 import _physics_objective, _read_json, _sha256_path
from .phk_v23_lf0_evaluation import _prediction_potential_guard, _sanitize_nonfinite, write_strict_json
from .phk_v23_lf1_evaluation import LF_ONLY_ROLE, _competent, _evaluation_valid, compare_b_to_comparator
from .phk_v23_lf2 import load_medium_dataset
from .phk_v23_lf2_evaluation import _component_floors, _inherited_prediction_paths
from .phk_v23_lf3 import full_medium_audit
from .phk_v23_lf10 import (
    DIRECTION_ARM_ORDER,
    FULL_ACCEPTED_UPDATES,
    FULL_ATTEMPTED_CAP,
    SCREEN_ATTEMPTED_CAP,
    _strong_qualification,
    _strong_runtime_bindings,
    load_contracts,
    read_cpu_qualification,
)
from . import phk_v23_lf7 as lf7


TASK_ID = "PHK_V23_LF10_EVENT_COMPETENCE_FEASIBLE_DIRECTION_AND_HEADLINE_EVIDENCE_REPLICATION_EXECUTE"
PHASE_THRESHOLDS = (0.40, 0.45, 0.50, 0.55, 0.60)
ACTIVE_FRACTION_THRESHOLDS = (0.01, 0.015, 0.02, 0.03, 0.05)
SHUTDOWN_PROOF_SCHEMA = "phk-v23-lf10-autodl-shutdown-proof-v1"
DEV_R_ROLE = "LF6_DEV_R_SAFETY_NEAR_CARRIER"
SELECTED_FULL_ROLE = "LF10_SELECTED_FILTERED_FULL"


def _crossing_time(time: np.ndarray, fraction: np.ndarray, threshold: float) -> float | None:
    for before, after in zip(range(len(time) - 1), range(1, len(time)), strict=True):
        low, high = float(fraction[before]), float(fraction[after])
        if low < threshold <= high and high > low:
            rho = (threshold - low) / (high - low)
            return float(time[before] + rho * (time[after] - time[before]))
    return None


def _cycle_record(
    prediction: np.ndarray,
    reference: np.ndarray,
    *,
    time: np.ndarray,
    roi: np.ndarray,
    period: float,
    cycle_index: int,
    phase_threshold: float,
    active_fraction_threshold: float,
) -> dict[str, Any]:
    start, end = cycle_index * period, (cycle_index + 1) * period
    mask = (time >= start) & (time <= end if cycle_index == 1 else time < end)
    indices = np.flatnonzero(mask)
    pred_active = prediction[indices][:, roi] >= phase_threshold
    ref_active = reference[indices][:, roi] >= phase_threshold
    tp = int(np.count_nonzero(pred_active & ref_active))
    fp = int(np.count_nonzero(pred_active & ~ref_active))
    fn = int(np.count_nonzero(~pred_active & ref_active))
    union = int(np.count_nonzero(pred_active | ref_active))
    pred_count, ref_count = int(np.count_nonzero(pred_active)), int(np.count_nonzero(ref_active))
    pred_fraction = np.mean(prediction[:, roi] >= phase_threshold, axis=1)
    ref_fraction = np.mean(reference[:, roi] >= phase_threshold, axis=1)
    pred_time = _crossing_time(time[indices], pred_fraction[indices], active_fraction_threshold)
    ref_time = _crossing_time(time[indices], ref_fraction[indices], active_fraction_threshold)
    pred_values, ref_values = pred_fraction[indices], ref_fraction[indices]
    pred_peak, ref_peak = int(np.argmax(pred_values)), int(np.argmax(ref_values))
    pred_excursion = float(pred_values[pred_peak] - pred_values[0])
    ref_excursion = float(ref_values[ref_peak] - ref_values[0])
    pred_recovery = float((pred_values[pred_peak] - pred_values[-1]) / pred_excursion) if pred_excursion > 0 else 0.0
    ref_recovery = float((ref_values[ref_peak] - ref_values[-1]) / ref_excursion) if ref_excursion > 0 else 0.0
    return {
        "event_exists": pred_time is not None,
        "reference_event_exists": ref_time is not None,
        "recall": float(tp / max(tp + fn, 1)),
        "precision": float(tp / max(tp + fp, 1)),
        "active_mass_ratio": float(pred_count / max(ref_count, 1)),
        "event_time": pred_time,
        "reference_event_time": ref_time,
        "event_time_absolute_error": (
            abs(pred_time - ref_time) if pred_time is not None and ref_time is not None else None
        ),
        "recovery_fraction": pred_recovery,
        "reference_recovery_fraction": ref_recovery,
        "symmetric_difference": float(np.mean(pred_active ^ ref_active)),
        "iou": float(tp / max(union, 1)),
    }


def threshold_grid_metrics(
    prediction_phase: np.ndarray,
    reference_phase: np.ndarray,
    *,
    time: np.ndarray,
    cell_x: np.ndarray,
    cell_z: np.ndarray,
    period: float,
    phase_thresholds: Sequence[float] = PHASE_THRESHOLDS,
    active_fraction_thresholds: Sequence[float] = ACTIVE_FRACTION_THRESHOLDS,
) -> dict[str, Any]:
    """Evaluate the frozen event topology over the auxiliary 5x5 threshold grid."""

    prediction_phase = np.asarray(prediction_phase, dtype=np.float64)
    reference_phase = np.asarray(reference_phase, dtype=np.float64)
    time = np.asarray(time, dtype=np.float64).reshape(-1)
    cell_x, cell_z = np.asarray(cell_x).reshape(-1), np.asarray(cell_z).reshape(-1)
    if prediction_phase.shape != reference_phase.shape or prediction_phase.shape != (time.size, cell_x.size):
        raise ValueError("LF10 threshold grid shape mismatch")
    if cell_x.shape != cell_z.shape or not all(np.isfinite(v).all() for v in (prediction_phase, reference_phase, time, cell_x, cell_z)):
        raise ValueError("LF10 threshold grid contains invalid values")
    roi = (np.abs(cell_x) <= 0.55) & (cell_z >= 0.0) & (cell_z <= 0.55)
    if not np.any(roi) or np.all(roi):
        raise ValueError("LF10 threshold ROI is invalid")
    rows: list[dict[str, Any]] = []
    for phase_threshold in phase_thresholds:
        for active_threshold in active_fraction_thresholds:
            cycles = [
                _cycle_record(
                    prediction_phase,
                    reference_phase,
                    time=time,
                    roi=roi,
                    period=float(period),
                    cycle_index=cycle,
                    phase_threshold=float(phase_threshold),
                    active_fraction_threshold=float(active_threshold),
                )
                for cycle in range(2)
            ]
            rows.append({
                "phase_threshold": float(phase_threshold),
                "active_fraction_threshold": float(active_threshold),
                "cycles": cycles,
                "both_events_exist": all(c["event_exists"] for c in cycles),
                "minimum_recall": min(c["recall"] for c in cycles),
                "minimum_precision": min(c["precision"] for c in cycles),
                "mean_symmetric_difference": float(np.mean([c["symmetric_difference"] for c in cycles])),
                "mean_iou": float(np.mean([c["iou"] for c in cycles])),
            })
    return {
        "phase_thresholds": [float(v) for v in phase_thresholds],
        "active_fraction_thresholds": [float(v) for v in active_fraction_thresholds],
        "grid_size": len(rows),
        "formal_machine_threshold": {"phase": 0.5, "active_fraction": 0.02},
        "rows": rows,
    }


def robustness_comparison(grids: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Summarise the three preregistered direction-of-effect questions."""

    def paired(left: str, right: str, predicate: Any) -> dict[str, Any]:
        if left not in grids or right not in grids:
            return {"status": "SKIPPED_MISSING_PREDICTION", "numerator": 0, "denominator": 0, "fraction": None}
        a, b = grids[left]["rows"], grids[right]["rows"]
        if len(a) != len(b):
            raise ValueError("LF10 threshold grids are not matched")
        count = sum(bool(predicate(x, y)) for x, y in zip(a, b, strict=True))
        return {"status": "COMPLETE", "numerator": count, "denominator": len(a), "fraction": count / len(a)}

    interface = paired("LF4_DEV_M", "LF4_DEV_G", lambda m, g: m["minimum_recall"] > g["minimum_recall"])
    forgetting = paired(
        "LF6_P0", "LF6_DEV_R",
        lambda p0, dev: (p0["minimum_recall"] < dev["minimum_recall"]) or (dev["both_events_exist"] and not p0["both_events_exist"]),
    )
    interface_replications = {
        str(seed): paired(
            f"LF10_INTERFACE_{seed}_DEV_M",
            f"LF10_INTERFACE_{seed}_DEV_G",
            lambda m, g: m["minimum_recall"] > g["minimum_recall"],
        )
        for seed in (23, 29)
    }
    forgetting_replications = {
        str(seed): paired(
            f"LF10_FORGETTING_{seed}",
            "LF6_DEV_R",
            lambda p0, dev: (p0["minimum_recall"] < dev["minimum_recall"])
            or (dev["both_events_exist"] and not p0["both_events_exist"]),
        )
        for seed in (23, 29)
    }
    direct = {"status": "SKIPPED_MISSING_PREDICTION", "comparisons": {}, "wins": 0, "total": 0, "fraction": None}
    if "DIRECT_LF_ONLY" in grids:
        direct["status"] = "COMPLETE"
        for role, grid in grids.items():
            if role == "DIRECT_LF_ONLY":
                continue
            result = paired("DIRECT_LF_ONLY", role, lambda d, x: d["mean_symmetric_difference"] < x["mean_symmetric_difference"])
            direct["comparisons"][role] = result
            direct["wins"] += result["numerator"]
            direct["total"] += result["denominator"]
        direct["fraction"] = direct["wins"] / direct["total"] if direct["total"] else None
    return {
        "interface_support_same_sign": interface,
        "physics_forgetting_persists": forgetting,
        "historical_interface_support_same_sign": interface,
        "historical_physics_forgetting_persists": forgetting,
        "interface_replication_by_stream": interface_replications,
        "forgetting_replication_by_stream": forgetting_replications,
        "direct_lf_only_lead": direct,
    }


def _verify_shutdown_proof(path: Path) -> dict[str, Any]:
    payload = _read_json(Path(path).resolve())
    pre, post = payload.get("pre_shutdown", {}), payload.get("post_shutdown", {})
    ordering = payload.get("ordering", {})
    if (
        payload.get("schema_id") != SHUTDOWN_PROOF_SCHEMA
        or payload.get("task_id") != TASK_ID
        or pre.get("artifacts_recovered_and_hash_verified") is not True
        or int(pre.get("training_process_count", -1)) != 0
        or int(pre.get("gpu_compute_process_count", -1)) != 0
        or payload.get("shutdown_requested") is not True
        or post.get("tcp_open") is not False
        or post.get("verified_closed") is not True
        or int(post.get("ssh_exit_code", 0)) == 0
        or "connection refused" not in str(post.get("ssh_terminal_evidence", "")).lower()
        or ordering.get("shutdown_observation_preceded_local_adjudication") is not True
    ):
        raise PermissionError("LF10 local evaluation requires verified recovery and shutdown")
    return payload


def primary_terminal_outcome(
    *,
    feasible_direction_outcome: str,
    safe_path_updates: int,
    within_architecture_pareto: bool,
    direct_noninferiority: bool,
) -> str:
    if within_architecture_pareto:
        return "LF10_PROVISIONAL_SINGLE_SEED_DENSE_SIGNAL" if direct_noninferiority else "LF10_WITHIN_ARCHITECTURE_PINN_PARETO_DIRECT_BASELINE_GAP"
    if safe_path_updates >= 200:
        return "LF10_SAFE_PATH_EXTENDED_FULL_PARETO_NOT_REACHED"
    return "LF10_FEASIBLE_DIRECTION_SCREEN_NEGATIVE_PAPER_STRENGTHENED"


def _historical_prediction_bindings() -> dict[str, Path | None]:
    """Literal historical prediction carriers; absent LF4 carriers stay absent."""

    root = Path(__file__).resolve().parents[1]
    return {
        "LF3_T0": root / "outputs/runs/20260904T150300Z-phk-v23-lf3-phase-latent-97a5b74/prediction-t0-step-1200.npz",
        "LF4_DEV_G": None,
        "LF4_DEV_M": None,
        "LF4_DEV_C": None,
        "LF6_DEV_R": root / "outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/dev_r/prediction.npz",
        "LF6_P0": root / "outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/p0/prediction.npz",
        "LF8_PREFIX": root / "outputs/runs/20260908T050343Z-phk-v23-lf8-competence-filter-completion-pilot/p0-fstar/prediction.npz",
        "LF9_ER_S": root / "outputs/runs/20260908T145333Z-phk-v23-lf9-equation-routed-thermal-cv/gpu/lf9-run-bc3950a/er-s/screen-prediction.npz",
        "LF9_ER_CV": root / "outputs/runs/20260908T145333Z-phk-v23-lf9-equation-routed-thermal-cv/gpu/lf9-run-bc3950a/er-cv/screen-prediction.npz",
        "DIRECT_LF_ONLY": root / "outputs/runs/20260903T092005Z-phk-v23-lf0-local-final-172ae2c/prediction-lf-only-medium-direct.npz",
    }


def evaluate_threshold_robustness(extra_predictions: Mapping[str, Path] | None = None) -> dict[str, Any]:
    reference, reference_sha = load_reference(PhkControl.FULL)
    bindings = _historical_prediction_bindings()
    bindings.update({str(k): Path(v) for k, v in (extra_predictions or {}).items()})
    grids: dict[str, Any] = {}
    skipped: dict[str, str] = {}
    for role, path in bindings.items():
        if path is None or not Path(path).is_file():
            skipped[role] = "SKIPPED_MISSING_PREDICTION"
            continue
        metadata, values = read_prediction_carrier(Path(path))
        grids[role] = threshold_grid_metrics(
            values["phase"], reference.phase,
            time=reference.time,
            cell_x=reference.grid.cell_x,
            cell_z=reference.grid.cell_z,
            period=reference.case.period,
        )
        grids[role]["prediction_path"] = Path(path).resolve().as_posix()
        grids[role]["prediction_sha256"] = _sha256_path(Path(path))
        grids[role]["prediction_role"] = metadata.get("role")
    return {
        "schema_id": "phk-v23-lf10-threshold-robustness-v1",
        "reference_sha256": reference_sha,
        "grids": grids,
        "skipped": skipped,
        "comparison": robustness_comparison(grids),
        "formal_machine_outcomes_unchanged": True,
    }


def canonical_run_view(run: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and expose the canonical LF10 runner summary fields."""

    arms = run.get("direction_arms")
    decision = run.get("direction_screen_decision")
    full = run.get("full_refinement")
    if (
        run.get("schema_id") != "phk-v23-lf10-reference-blind-run-summary-v1"
        or run.get("task_id") != TASK_ID
        or not isinstance(arms, Mapping)
        or set(arms) != set(DIRECTION_ARM_ORDER)
        or not isinstance(decision, Mapping)
        or not isinstance(full, Mapping)
        or run.get("feasible_direction_outcome") != decision.get("feasible_direction_outcome")
        or any(int(arms[arm].get("attempted_updates", 0)) > SCREEN_ATTEMPTED_CAP for arm in DIRECTION_ARM_ORDER)
        or int(full.get("attempted_updates", 0)) > FULL_ATTEMPTED_CAP
        or run.get("medium_audit_gradient_used_for_direction_only") is not True
        or run.get("medium_audit_entered_physics_loss") is not False
        or run.get("runtime_sampling_used") is not False
        or run.get("fine_extra_lf_only_evaluator_stress_read") is not False
    ):
        raise ValueError("LF10 recovered run identity drift")
    return {
        "arms": dict(arms),
        "direction": dict(decision),
        "feasible_direction_outcome": str(run["feasible_direction_outcome"]),
        "selected_arm": run.get("selected_direction_arm"),
        "full": dict(full),
        "interface_outcome": str(run.get("interface_replication_outcome", "INTERFACE_REPLICATION_INCOMPLETE")),
        "forgetting_outcome": str(run.get("forgetting_replication_outcome", "FORGETTING_REPLICATION_INCOMPLETE")),
    }


def _artifact_path(root: Path, run: Mapping[str, Any], relative: str) -> Path:
    record = run.get("artifacts", {}).get(relative)
    if not isinstance(record, Mapping):
        raise ValueError(f"LF10 recovered artifact missing: {relative}")
    declared = Path(str(record.get("path", "")))
    if declared.as_posix() != relative or declared.is_absolute() or ".." in declared.parts:
        raise PermissionError(f"LF10 recovered artifact escaped run root: {relative}")
    exact = (root / declared).resolve()
    try:
        exact.relative_to(root.resolve())
    except ValueError as exc:
        raise PermissionError(f"LF10 recovered artifact escaped run root: {relative}") from exc
    if (
        not exact.is_file()
        or exact.stat().st_size != int(record.get("size_bytes", -1))
        or _sha256_path(exact) != str(record.get("sha256", "")).upper()
    ):
        raise ValueError(f"LF10 recovered artifact drift: {relative}")
    return exact


def _prediction_role(relative: str) -> str:
    parts = Path(relative).parts
    if len(parts) == 3 and parts[0] == "direction":
        arm = parts[1].upper()
        if parts[2] == "full-prediction.npz":
            return SELECTED_FULL_ROLE
        if parts[2] == "screen-prediction.npz":
            return f"LF10_DIRECTION_{arm}_SCREEN"
    if len(parts) == 4 and parts[0] == "interface" and parts[1].startswith("seed-"):
        seed = parts[1].removeprefix("seed-")
        arm = parts[2].replace("-", "_").upper()
        return f"LF10_INTERFACE_{seed}_{arm}"
    if len(parts) == 3 and parts[0] == "forgetting" and parts[1].startswith("seed-"):
        seed = parts[1].removeprefix("seed-")
        return f"LF10_FORGETTING_{seed}"
    return "LF10_" + relative.replace("\\", "/").replace("/", ":").upper()


def _prediction_checkpoint_sha(path: Path) -> str:
    with np.load(path, allow_pickle=False) as archive:
        raw = archive["metadata_json"]
        text = str(raw.item()) if raw.shape == () else str(raw.reshape(-1)[0])
    return str(json.loads(text)["checkpoint_sha256"]).upper()


def _run_files(root: Path, run: Mapping[str, Any], contracts: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    view = canonical_run_view(run)
    predictions: dict[str, Path] = {}
    checkpoints: dict[str, Path] = {}
    for relative in sorted(run.get("artifacts", {})):
        if not relative.endswith("prediction.npz"):
            continue
        prediction = _artifact_path(root, run, relative)
        role = _prediction_role(relative)
        if role in predictions:
            raise ValueError(f"LF10 duplicate prediction role: {role}")
        checkpoint_relative = relative.removesuffix("prediction.npz") + "checkpoint.pt"
        checkpoint = _artifact_path(root, run, checkpoint_relative)
        if _prediction_checkpoint_sha(prediction) != _sha256_path(checkpoint):
            raise ValueError(f"LF10 prediction/checkpoint binding drift: {relative}")
        payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
        metadata = payload.get("lf10", {})
        if (
            payload.get("schema_id") != "phk-v22r-checkpoint-v1-1"
            or metadata.get("schema_id") != "phk-v23-lf10-checkpoint-metadata-v1"
            or metadata.get("task_id") != TASK_ID
            or metadata.get("source_identity") != run.get("source_identity")
            or metadata.get("runtime_sampling_used") is not False
            or metadata.get("stress_read") is not False
        ):
            raise ValueError(f"LF10 checkpoint provenance drift: {checkpoint_relative}")
        predictions[role] = prediction
        checkpoints[role] = checkpoint

    data = contracts["data"]
    dev_r_checkpoint = (ROOT / data["DEV_R"]["checkpoint_path"]).resolve()
    dev_r_prediction = _historical_prediction_bindings()["LF6_DEV_R"]
    if (
        not dev_r_checkpoint.is_file()
        or _sha256_path(dev_r_checkpoint) != data["DEV_R"]["checkpoint_sha256"]
        or dev_r_prediction is None
        or not dev_r_prediction.is_file()
        or _sha256_path(dev_r_prediction) != data["DEV_R"]["prediction_sha256"]
    ):
        raise ValueError("LF10 DEV-R comparator binding drift")
    checkpoints[DEV_R_ROLE] = dev_r_checkpoint
    predictions[DEV_R_ROLE] = dev_r_prediction
    return {"view": view, "predictions": predictions, "checkpoints": checkpoints}


def _fixed_blind_j(
    checkpoints: Mapping[str, Path],
    *,
    contracts: Mapping[str, Mapping[str, Any]],
    qualification: Mapping[str, Any],
) -> dict[str, float]:
    strong = lf7.MaterializedPhysicsLedger(
        ROOT / contracts["data"]["strong_ledger"]["path"],
        contracts=_strong_runtime_bindings(contracts),
        qualification=_strong_qualification(qualification),
    )
    values: dict[str, float] = {}
    for role, path in checkpoints.items():
        model, config, _ = _load_model(path, device=torch.device("cpu"))
        with torch.enable_grad():
            _, scalars = _physics_objective(model, strong.fixed_batch(device=torch.device("cpu")), config)
        values[role] = float(scalars["physics_total"])
    expected = float(contracts["data"]["DEV_R_baseline"]["fixed_blind_strong_J0"])
    if not math.isclose(values[DEV_R_ROLE], expected, rel_tol=1e-9, abs_tol=1e-12):
        raise ValueError("LF10 DEV-R fixed-blind baseline drift")
    return values


def _full_level(
    *,
    raw: Mapping[str, Any],
    evaluation: Mapping[str, Any] | None,
    potential: Mapping[str, Any] | None,
    medium: Mapping[str, Any] | None,
    baseline_medium: Mapping[str, Any],
    comparison_dev_r: Mapping[str, Any] | None,
    comparison_direct: Mapping[str, Any] | None,
    fixed_j: float | None,
    baseline_j: float,
) -> dict[str, Any]:
    strict = (
        lf7.competence_gate(medium, baseline_medium, strict_timing=True)
        if isinstance(medium, Mapping)
        else {"passed": False, "failed_checks": ["missing_post_shutdown_medium_audit"]}
    )
    j_ratio = float(fixed_j) / float(baseline_j) if fixed_j is not None else None
    endpoint_valid = bool(
        raw.get("identity_valid") is not False
        and raw.get("numerical_valid") is True
        and isinstance(evaluation, Mapping)
        and _evaluation_valid(evaluation)
        and isinstance(potential, Mapping)
        and potential.get("passed") is True
        and isinstance(medium, Mapping)
    )
    within_ni = bool(
        isinstance(comparison_dev_r, Mapping)
        and comparison_dev_r.get("phase_noninferiority_passed") is True
        and comparison_dev_r.get("preservation_passed") is True
    )
    complete = bool(
        endpoint_valid
        and int(raw.get("accepted_updates", -1)) == FULL_ACCEPTED_UPDATES
        and strict.get("passed") is True
        and j_ratio is not None
        and j_ratio <= 0.50
        and _competent(evaluation)
        and within_ni
    )
    direct_ni = bool(
        isinstance(comparison_direct, Mapping)
        and comparison_direct.get("phase_noninferiority_passed") is True
        and comparison_direct.get("preservation_passed") is True
        and comparison_direct.get("b_competent") is True
        and comparison_direct.get("comparator_competent") is True
        and isinstance(potential, Mapping)
        and potential.get("passed") is True
    )
    return {
        "endpoint_valid": endpoint_valid,
        "strict_gate_recomputed": strict,
        "fixed_blind_J": fixed_j,
        "fixed_blind_J_ratio_to_DEV_R": j_ratio,
        "frozen_evaluator_competent": bool(isinstance(evaluation, Mapping) and _competent(evaluation)),
        "phase_temperature_current_noninferiority_vs_DEV_R": within_ni,
        "complete_internal_pareto": complete,
        "direct_noninferiority": bool(complete and direct_ni),
    }


def evaluate_lf10_campaign(
    *,
    output_directory: Path,
    run_directory: Path,
    cpu_qualification_path: Path,
    shutdown_proof_path: Path,
) -> dict[str, Any]:
    shutdown = _verify_shutdown_proof(shutdown_proof_path)
    root = Path(run_directory).resolve()
    summary_path = root / "run_summary.json"
    run = _read_json(summary_path)
    contracts = load_contracts()
    qualification = read_cpu_qualification(cpu_qualification_path)
    files = _run_files(root, run, contracts)
    view = files["view"]
    extra = files["predictions"]
    threshold = evaluate_threshold_robustness(extra)

    lf3_decision = _read_json(ROOT / "configs/phk_v23/decision_contract_lf3_phase_latent_carrier.json")
    direct_path = _inherited_prediction_paths(lf3_decision)[LF_ONLY_ROLE]
    if _sha256_path(direct_path) != contracts["data"]["local_evaluation_only"]["direct_LF_ONLY_prediction_sha256"]:
        raise ValueError("LF10 direct LF_ONLY prediction binding drift")
    prediction_paths = {**extra, LF_ONLY_ROLE: direct_path}
    endpoint_evaluations = {
        role: evaluate_prediction(prediction_path=path, control=PhkControl.FULL)
        for role, path in prediction_paths.items()
    }
    potential = {
        role: _prediction_potential_guard(path, absolute_tolerance=1e-6)
        for role, path in prediction_paths.items()
    }
    if not _evaluation_valid(endpoint_evaluations[DEV_R_ROLE]) or not _evaluation_valid(endpoint_evaluations[LF_ONLY_ROLE]):
        raise ValueError("LF10 frozen comparator evaluation invalid")

    floors = _component_floors(lf3_decision)
    comparisons: dict[str, Any] = {}
    if SELECTED_FULL_ROLE in endpoint_evaluations:
        comparisons["FULL_vs_DEV_R"] = compare_b_to_comparator(
            endpoint_evaluations[SELECTED_FULL_ROLE], endpoint_evaluations[DEV_R_ROLE], component_floors=floors
        )
        comparisons["FULL_vs_DIRECT_LF_ONLY"] = compare_b_to_comparator(
            endpoint_evaluations[SELECTED_FULL_ROLE], endpoint_evaluations[LF_ONLY_ROLE], component_floors=floors
        )

    physics, _, _ = load_case_physics("FULL")
    medium_path = (ROOT / contracts["data"]["medium"]["path"]).resolve()
    if not medium_path.is_file() or _sha256_path(medium_path) != contracts["data"]["medium"]["sha256"]:
        raise ValueError("LF10 medium input binding drift")
    dataset = load_medium_dataset(medium_path, physics=physics, contracts=contracts)
    if dataset.partition_sha256 != contracts["data"]["medium"]["partition_sha256"]:
        raise ValueError("LF10 medium partition drift")
    medium_audits: dict[str, Any] = {}
    for role in (DEV_R_ROLE, SELECTED_FULL_ROLE):
        if role in files["checkpoints"]:
            model, _, _ = _load_model(files["checkpoints"][role], device=torch.device("cpu"))
            medium_audits[role] = full_medium_audit(model, dataset, device=torch.device("cpu"))
    fixed = _fixed_blind_j(
        {role: path for role, path in files["checkpoints"].items() if role in {DEV_R_ROLE, SELECTED_FULL_ROLE}},
        contracts=contracts,
        qualification=qualification,
    )
    full_level = _full_level(
        raw=view["full"],
        evaluation=endpoint_evaluations.get(SELECTED_FULL_ROLE),
        potential=potential.get(SELECTED_FULL_ROLE),
        medium=medium_audits.get(SELECTED_FULL_ROLE),
        baseline_medium=qualification["dev_r_full_medium_audit"],
        comparison_dev_r=comparisons.get("FULL_vs_DEV_R"),
        comparison_direct=comparisons.get("FULL_vs_DIRECT_LF_ONLY"),
        fixed_j=fixed.get(SELECTED_FULL_ROLE),
        baseline_j=fixed[DEV_R_ROLE],
    )
    accepted = max([int(v.get("accepted_updates", 0)) for v in view["arms"].values()] + [0])
    within = full_level["complete_internal_pareto"]
    direct = full_level["direct_noninferiority"]
    primary = primary_terminal_outcome(
        feasible_direction_outcome=view["feasible_direction_outcome"],
        safe_path_updates=max(accepted, int(view["full"].get("accepted_updates", 0))),
        within_architecture_pareto=within,
        direct_noninferiority=direct,
    )
    report = {
        "schema_id": "phk-v23-lf10-local-adjudication-v1",
        "task_id": TASK_ID,
        "status": "COMPLETE",
        "run_summary_sha256": _sha256_path(summary_path),
        "cpu_qualification_sha256": _sha256_path(Path(cpu_qualification_path)),
        "shutdown_proof_sha256": _sha256_path(Path(shutdown_proof_path)),
        "threshold_robustness": threshold,
        "endpoint_evaluations": _sanitize_nonfinite(endpoint_evaluations)[0],
        "potential_maximum_principle": potential,
        "component_floors": floors,
        "comparisons": comparisons,
        "post_shutdown_full_medium_audits": medium_audits,
        "post_shutdown_fixed_blind_J": fixed,
        "full_pareto_recomputed": full_level,
        "decision": {
            "feasible_direction_outcome": view["feasible_direction_outcome"],
            "interface_replication_outcome": view["interface_outcome"],
            "forgetting_replication_outcome": view["forgetting_outcome"],
            "full_complete_internal_pareto": within,
            "direct_noninferiority": direct,
            "primary_outcome": primary,
            "candidate": "PROVISIONAL_SINGLE_SEED_DENSE_SIGNAL" if primary == "LF10_PROVISIONAL_SINGLE_SEED_DENSE_SIGNAL" else None,
        },
        "fine_extra_use": "LOCAL_NOMINAL_ONLY_AFTER_VERIFIED_SHUTDOWN",
        "stress_status": "TWO_STRESS_REFERENCES_SEALED_UNREAD",
        "shutdown_schema": shutdown["schema_id"],
    }
    output = Path(output_directory).resolve()
    output.mkdir(parents=True, exist_ok=False)
    write_strict_json(output / "adjudication.json", report)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--run-directory", type=Path, required=True)
    parser.add_argument("--cpu-qualification", type=Path, required=True)
    parser.add_argument("--shutdown-proof", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = evaluate_lf10_campaign(output_directory=args.output_directory, run_directory=args.run_directory, cpu_qualification_path=args.cpu_qualification, shutdown_proof_path=args.shutdown_proof)
    print(json.dumps(report["decision"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ACTIVE_FRACTION_THRESHOLDS", "PHASE_THRESHOLDS", "SHUTDOWN_PROOF_SCHEMA",
    "canonical_run_view", "evaluate_lf10_campaign", "evaluate_threshold_robustness", "primary_terminal_outcome",
    "robustness_comparison", "threshold_grid_metrics",
]
