"""Local nominal evaluation and machine adjudication for PHK-V2.3 LF1."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import torch

from .phk_benchmark import PhkControl
from .phk_v22r_evaluator import evaluate_prediction
from .phk_v22r_pinn import PhkCollocationSampler
from .phk_v22r_prediction import _load_model
from .phk_v22r_training import ROOT, load_case_physics
from .phk_v23_lf0 import PhysicsBatch, _physics_objective, _sha256_path
from .phk_v23_lf0_evaluation import (
    _clone_batch,
    _load_component_floors,
    _prediction_potential_guard,
    _sanitize_nonfinite,
    compare_physics_batch_logs,
    competence_vector,
    safe_error_ratio,
    write_strict_json,
)
from .phk_v23_lf1 import (
    ARM_A,
    ARM_B,
    ARM_C,
    DECISION_CONTRACT_PATH,
    TASK_ID,
    contract_identity,
    load_contracts,
)


A_ROLE = "A_RANGE_PRESERVING_SCRATCH"
B_FINAL_ROLE = "B_FINAL"
B0_ROLE = "B0_LF_DATA_ONLY"
LF_ONLY_ROLE = "LF_ONLY_MEDIUM_DIRECT"
C_ROLE = "C_DATA_ONLY_CONTINUATION"
GPU_LIFECYCLE_SHUTDOWN_VERIFIED = "SHUTDOWN_VERIFIED"


def _metrics(report: Mapping[str, Any]) -> dict[str, float]:
    values = report.get("metrics")
    if not isinstance(values, Mapping):
        raise ValueError("LF1 evaluation lacks frozen metrics")
    names = (
        "time_averaged_phase_region_symmetric_difference",
        "phase_roi_continuous_rms",
        "temperature_roi_nrmse_by_0_45",
        "terminal_current_trace_nrmse",
    )
    result = {name: float(values[name]) for name in names}
    if not all(math.isfinite(value) and value >= 0.0 for value in result.values()):
        raise ValueError("LF1 decision metrics must be finite and nonnegative")
    return result


def _evaluation_valid(report: Mapping[str, Any]) -> bool:
    hard = report.get("hard_guards")
    if not isinstance(hard, Mapping):
        return False
    if hard.get("finite_values") is not True or hard.get("phase_range") is not True:
        return False
    try:
        _metrics(report)
    except (KeyError, TypeError, ValueError):
        return False
    return True


def _competent(report: Mapping[str, Any]) -> bool:
    hard = report.get("hard_guards")
    return bool(isinstance(hard, Mapping) and hard.get("passed") is True)


def _terminal(
    outcome: str,
    *,
    contract: Mapping[str, Any],
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    mapping = contract["machine_outcomes_and_unique_next"]
    if outcome not in mapping:
        raise ValueError(f"unmapped LF1 outcome: {outcome}")
    return {
        "status": "TERMINAL",
        "outcome": outcome,
        "unique_next": mapping[outcome],
        **dict(details or {}),
    }


def compare_b_to_comparator(
    b_report: Mapping[str, Any],
    comparator_report: Mapping[str, Any],
    *,
    component_floors: Mapping[str, float],
) -> dict[str, Any]:
    b = _metrics(b_report)
    comparator = _metrics(comparator_report)
    primary = "time_averaged_phase_region_symmetric_difference"
    co_primary = "phase_roi_continuous_rms"
    primary_ratio, primary_defined = safe_error_ratio(b[primary], comparator[primary])
    co_ratio, co_defined = safe_error_ratio(b[co_primary], comparator[co_primary])
    geometric = (
        math.sqrt(float(primary_ratio) * float(co_ratio))
        if primary_defined
        and co_defined
        and primary_ratio is not None
        and co_ratio is not None
        else None
    )
    ratio_pass = bool(
        primary_ratio is not None
        and co_ratio is not None
        and geometric is not None
        and primary_ratio <= 0.98
        and co_ratio <= 0.98
        and geometric <= 0.95
    )
    floor_pass = (
        b[primary]
        <= comparator[primary] + float(component_floors[primary])
        and b[co_primary]
        <= comparator[co_primary] + float(component_floors[co_primary])
    )
    temperature_pass = b["temperature_roi_nrmse_by_0_45"] <= max(
        1.10 * comparator["temperature_roi_nrmse_by_0_45"], 0.05
    )
    current_pass = b["terminal_current_trace_nrmse"] <= max(
        1.10 * comparator["terminal_current_trace_nrmse"], 0.15
    )
    return {
        "b_competent": _competent(b_report),
        "comparator_competent": _competent(comparator_report),
        "primary_ratio": primary_ratio,
        "co_primary_ratio": co_ratio,
        "geometric_mean_ratio": geometric,
        "ratio_gate_passed": ratio_pass,
        "primary_component_floor": float(component_floors[primary]),
        "co_primary_component_floor": float(component_floors[co_primary]),
        "floor_noninferiority_passed": floor_pass,
        "phase_noninferiority_passed": floor_pass or ratio_pass,
        "temperature_preservation_passed": temperature_pass,
        "current_preservation_passed": current_pass,
        "preservation_passed": temperature_pass and current_pass,
    }


def _fixed_physics_values(
    checkpoints: Mapping[str, Path],
    *,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    pool = contract["reference_blind_physics_diagnostic_pool"]
    device = torch.device("cpu")
    loaded = {
        role: _load_model(path, device=device) for role, path in checkpoints.items()
    }
    configs = [item[1] for item in loaded.values()]
    if any(config.case_control != "FULL" for config in configs):
        raise PermissionError("LF1 fixed physics diagnostic is nominal-only")
    physics, _, _ = load_case_physics("FULL")
    sampler = PhkCollocationSampler(physics=physics, seed=int(pool["seed"]))
    first_model = next(iter(loaded.values()))[0]
    interior = sampler.select_interior(
        first_model,
        count=int(pool["interior_points"]),
        active_windows=int(pool["active_windows"]),
        physics_aware=False,
        dtype=torch.float64,
        device=device,
    ).detach()
    boundary = sampler.boundary(
        int(pool["boundary_points_per_side"]),
        active_windows=int(pool["active_windows"]),
        dtype=torch.float64,
        device=device,
    )
    initial = sampler.initial(
        int(pool["initial_points"]), dtype=torch.float64, device=device
    )
    from .phk_v23_lf0_evaluation import _tensor_digest

    ordered = tuple(boundary[name] for name in ("left", "right", "bottom", "top"))
    digest = _tensor_digest(
        interior,
        *ordered,
        initial,
        metadata="PHK_V23_LF1_FIXED_REFERENCE_BLIND_FULL_W1_W4",
    )
    batch = PhysicsBatch(
        interior=interior,
        boundary=boundary,
        initial=initial,
        active_windows=4,
        refreshed=True,
        interior_sha256=_tensor_digest(interior, metadata="LF1_FIXED_INTERIOR"),
        boundary_sha256=_tensor_digest(*ordered, metadata="LF1_FIXED_BOUNDARY"),
        initial_sha256=_tensor_digest(initial, metadata="LF1_FIXED_INITIAL"),
        batch_sha256=digest,
    )
    values: dict[str, float] = {}
    components: dict[str, Any] = {}
    for role, (model, config, _) in loaded.items():
        with torch.enable_grad():
            _, scalars = _physics_objective(model, _clone_batch(batch), config)
        values[role] = float(scalars["physics_total"])
        components[role] = scalars
    ratios: dict[str, Any] = {}
    if B_FINAL_ROLE in values and B0_ROLE in values:
        ratio, defined = safe_error_ratio(values[B_FINAL_ROLE], values[B0_ROLE])
        ratios["B_FINAL_TO_B0"] = {
            "ratio": ratio,
            "defined": defined,
            "maximum": 0.5,
            "passed": bool(defined and ratio is not None and ratio <= 0.5),
        }
    if B_FINAL_ROLE in values and C_ROLE in values:
        ratio, defined = safe_error_ratio(values[B_FINAL_ROLE], values[C_ROLE])
        ratios["B_FINAL_TO_C"] = {
            "ratio": ratio,
            "defined": defined,
            "maximum": 0.5,
            "passed": bool(defined and ratio is not None and ratio <= 0.5),
        }
    return {
        "fixed_pool_sha256": digest,
        "seed": int(pool["seed"]),
        "active_windows": int(pool["active_windows"]),
        "objective": pool["objective"],
        "values": values,
        "components": components,
        "ratios": ratios,
        "reference_or_low_fidelity_values_read": False,
        "device": "CPU",
        "dtype": "FLOAT64",
    }


def _artifact_path(root: Path, summary: Mapping[str, Any], key: str) -> Path:
    record = summary.get("artifacts", {}).get(key)
    if not isinstance(record, Mapping):
        raise ValueError(f"LF1 recovered run lacks artifact binding: {key}")
    path = (root / str(record.get("path", ""))).resolve()
    if (
        not path.is_file()
        or path.stat().st_size != int(record.get("size_bytes", -1))
        or _sha256_path(path) != str(record.get("sha256", "")).upper()
    ):
        raise ValueError(f"LF1 recovered artifact drift: {key}")
    return path


def _run_files(path: Path, *, arm: str) -> dict[str, Any]:
    root = Path(path).resolve()
    summary_path = root / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if (
        summary.get("schema_id") != "phk-v23-lf1-reference-blind-run-summary-v1"
        or summary.get("task_id") != TASK_ID
        or summary.get("run_arm") != arm
        or summary.get("prediction_reference_free") is not True
        or summary.get("stress_fields_or_metrics_read") is not False
    ):
        raise ValueError("LF1 recovered run identity drift")
    allowed_status = {
        "LF1_REFERENCE_BLIND_GPU_RUN_COMPLETE",
        "LF1_DATA_TRANSFER_NO_EVENT",
        "LF1_NUMERICAL_OR_IDENTITY_INVALID",
    }
    if summary.get("status") not in allowed_status:
        raise ValueError("LF1 recovered run status is unsupported")
    result = {
        "root": root,
        "summary": summary_path,
        "summary_payload": summary,
        "prediction_final": _artifact_path(root, summary, "prediction_final"),
        "checkpoint_final": _artifact_path(root, summary, "checkpoint_final"),
    }
    if arm == ARM_A:
        result["physics_hashes"] = _artifact_path(root, summary, "physics_batch_hashes")
    if arm == ARM_B:
        result["prediction_b0"] = _artifact_path(root, summary, "prediction_b0")
        result["checkpoint_b0"] = _artifact_path(root, summary, "checkpoint_b0")
        result["physics_hashes"] = _artifact_path(root, summary, "physics_batch_hashes")
        result["b0_gate"] = _artifact_path(root, summary, "b0_data_transfer_gate")
    return result


def _read_cpu_qualification(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if (
        payload.get("schema_id") != "phk-v23-lf1-cpu-qualification-v1"
        or payload.get("task_id") != TASK_ID
        or payload.get("status") != "LF1_CPU_QUALIFICATION_PASS"
        or payload.get("gpu_execution_authorized_by_cpu_gate") is not True
        or payload.get("fine_extra_fine_reference_read") is not False
        or payload.get("stress_fields_or_metrics_read") is not False
        or payload.get("contracts") != contract_identity()
    ):
        raise PermissionError("LF1 CPU qualification is absent, stale, or did not pass")
    return payload


def _write_c_trigger(
    path: Path,
    *,
    inputs: Mapping[str, Path],
    conditions: Mapping[str, bool],
) -> dict[str, Any]:
    if not conditions or not all(value is True for value in conditions.values()):
        raise ValueError("LF1 C trigger requires every frozen condition")
    payload = {
        "schema_id": "phk-v23-lf1-c-trigger-v1",
        "task_id": TASK_ID,
        "action": "RUN_C_DATA_ONLY_CONTINUATION_FROM_EXACT_B0",
        "conditions": dict(conditions),
        "input_bindings": {
            name: {
                "path": str(Path(value).resolve()),
                "sha256": _sha256_path(value),
                "size_bytes": Path(value).stat().st_size,
            }
            for name, value in sorted(inputs.items())
        },
        "stress_fields_or_metrics_read": False,
    }
    write_strict_json(path, payload)
    return payload


def adjudicate(
    *,
    contract: Mapping[str, Any],
    evaluations: Mapping[str, Mapping[str, Any]],
    potential_guards: Mapping[str, Mapping[str, Any]],
    b_status: str | None,
    comparisons: Mapping[str, Mapping[str, Any]],
    physics: Mapping[str, Any] | None,
    physics_batch_identity: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if any(not _evaluation_valid(value) for value in evaluations.values()) or any(
        value.get("passed") is not True for value in potential_guards.values()
    ):
        return _terminal("LF1_NUMERICAL_OR_IDENTITY_INVALID", contract=contract)
    if B_FINAL_ROLE not in evaluations:
        return {
            "status": "INTERIM",
            "interim_status": "LF1_A_VALID_RUN_B_REQUIRED",
            "unique_next": "RUN_B_AFTER_AUTODL_RESTART",
        }
    if b_status == "LF1_DATA_TRANSFER_NO_EVENT":
        return _terminal("LF1_DATA_TRANSFER_NO_EVENT", contract=contract)
    if physics_batch_identity is None or physics_batch_identity.get("passed") is not True:
        return _terminal("LF1_NUMERICAL_OR_IDENTITY_INVALID", contract=contract)
    if not _competent(evaluations[B_FINAL_ROLE]):
        return _terminal(
            "LF1_PHYSICS_FORGETTING_PERSISTS",
            contract=contract,
            details={"competence": competence_vector(evaluations[B_FINAL_ROLE])},
        )
    required = (LF_ONLY_ROLE, B0_ROLE)
    comparison_pass = all(
        comparisons[role]["phase_noninferiority_passed"]
        and comparisons[role]["preservation_passed"]
        for role in required
    )
    b0_physics_pass = bool(
        physics
        and physics.get("ratios", {}).get("B_FINAL_TO_B0", {}).get("passed") is True
    )
    if not (comparison_pass and b0_physics_pass):
        return _terminal("LF1_DATA_ONLY_VALUE_NO_PINN_GAIN", contract=contract)
    if C_ROLE not in evaluations:
        return {
            "status": "INTERIM",
            "interim_status": "LF1_C_TRIGGERED",
            "unique_next": "RUN_C_DATA_ONLY_CONTINUATION_AFTER_AUTODL_RESTART",
            "conditions": {
                "b_final_two_cycle_competent": True,
                "phase_noninferiority_and_preservation_vs_lf_only": True,
                "phase_noninferiority_and_preservation_vs_b0": True,
                "b_final_to_b0_physics_ratio_passed": True,
                "potential_validity_passed": True,
            },
        }
    c_comparison = comparisons[C_ROLE]
    b_to_c_physics_pass = bool(
        physics
        and physics.get("ratios", {}).get("B_FINAL_TO_C", {}).get("passed") is True
    )
    if not (
        c_comparison["phase_noninferiority_passed"]
        and c_comparison["preservation_passed"]
        and b_to_c_physics_pass
    ):
        return _terminal("LF1_DATA_ONLY_VALUE_NO_PINN_GAIN", contract=contract)
    return _terminal("LF1_EVENT_PRESERVING_PINN_PROVISIONAL_SIGNAL", contract=contract)


def evaluate_lf1_campaign(
    *,
    output_directory: Path,
    a_run_directory: Path,
    cpu_qualification_path: Path,
    b_run_directory: Path | None = None,
    c_run_directory: Path | None = None,
    case_control: str = "FULL",
    gpu_lifecycle: str = GPU_LIFECYCLE_SHUTDOWN_VERIFIED,
) -> dict[str, Any]:
    if case_control != PhkControl.FULL.value:
        raise PermissionError("LF1 evaluation is nominal-only; stress stays sealed")
    if gpu_lifecycle != GPU_LIFECYCLE_SHUTDOWN_VERIFIED:
        raise PermissionError("LF1 local evaluation requires verified GPU shutdown")
    contracts = load_contracts()
    _read_cpu_qualification(cpu_qualification_path)
    contract = contracts["decision"]
    output = Path(output_directory).resolve()
    output.mkdir(parents=True, exist_ok=False)
    source = contracts["data"]["local_cpu_diagnostic_inputs"]["lf_only_prediction"]
    lf_only = (ROOT / source["path"]).resolve()
    if _sha256_path(lf_only) != str(source["sha256"]).upper():
        raise ValueError("LF1 LF_ONLY comparator identity drift")
    a_files = _run_files(a_run_directory, arm=ARM_A)
    b_files = _run_files(b_run_directory, arm=ARM_B) if b_run_directory else None
    c_files = _run_files(c_run_directory, arm=ARM_C) if c_run_directory else None
    prediction_paths: dict[str, Path] = {
        A_ROLE: a_files["prediction_final"],
        LF_ONLY_ROLE: lf_only,
    }
    if b_files:
        prediction_paths[B_FINAL_ROLE] = b_files["prediction_final"]
        prediction_paths[B0_ROLE] = b_files["prediction_b0"]
    if c_files:
        prediction_paths[C_ROLE] = c_files["prediction_final"]
    evaluations = {
        role: evaluate_prediction(prediction_path=path, control=PhkControl.FULL)
        for role, path in prediction_paths.items()
    }
    tolerance = float(contract["potential_maximum_principle"]["absolute_tolerance"])
    potential_guards = {
        role: _prediction_potential_guard(path, absolute_tolerance=tolerance)
        for role, path in prediction_paths.items()
    }
    floors = _load_component_floors(contract)
    comparisons = (
        {
            role: compare_b_to_comparator(
                evaluations[B_FINAL_ROLE],
                evaluations[role],
                component_floors=floors,
            )
            for role in prediction_paths
            if role not in {A_ROLE, B_FINAL_ROLE}
        }
        if b_files
        else {}
    )
    batch_identity = (
        compare_physics_batch_logs(
            a_files["physics_hashes"], b_files["physics_hashes"]
        )
        if b_files and b_files["summary_payload"]["status"] == "LF1_REFERENCE_BLIND_GPU_RUN_COMPLETE"
        else None
    )
    checkpoint_paths: dict[str, Path] = {}
    if b_files and b_files["summary_payload"]["status"] == "LF1_REFERENCE_BLIND_GPU_RUN_COMPLETE":
        checkpoint_paths = {
            B_FINAL_ROLE: b_files["checkpoint_final"],
            B0_ROLE: b_files["checkpoint_b0"],
        }
        if c_files:
            checkpoint_paths[C_ROLE] = c_files["checkpoint_final"]
    physics = (
        _fixed_physics_values(checkpoint_paths, contract=contract)
        if checkpoint_paths
        else None
    )
    decision = adjudicate(
        contract=contract,
        evaluations=evaluations,
        potential_guards=potential_guards,
        b_status=b_files["summary_payload"]["status"] if b_files else None,
        comparisons=comparisons,
        physics=physics,
        physics_batch_identity=batch_identity,
    )
    sanitized, replaced = _sanitize_nonfinite(evaluations)
    report = {
        "schema_id": "phk-v23-lf1-local-adjudication-v1",
        "task_id": TASK_ID,
        "status": "COMPLETE" if decision["status"] == "TERMINAL" else "INTERIM",
        "case_control": "FULL",
        "gpu_lifecycle": gpu_lifecycle,
        "roles_evaluated": list(prediction_paths),
        "prediction_bindings": {
            role: {
                "path": str(path),
                "sha256": _sha256_path(path),
                "size_bytes": path.stat().st_size,
            }
            for role, path in prediction_paths.items()
        },
        "evaluations": sanitized,
        "evaluator_nonfinite_diagnostics_represented_as_json_null": replaced,
        "potential_maximum_principle": potential_guards,
        "component_floors": floors,
        "comparisons": comparisons,
        "physics_batch_identity": batch_identity,
        "fixed_physics_objective": physics,
        "decision": decision,
        "lf_only_role": "REUSED_MEDIUM_DIRECT_COMPARATOR_NOT_A_PINN",
        "stress_status": "TWO_STRESS_REFERENCES_SEALED_UNREAD",
    }
    if decision.get("interim_status") == "LF1_C_TRIGGERED":
        assert b_files is not None
        trigger = _write_c_trigger(
            output / "c-trigger.json",
            conditions=decision["conditions"],
            inputs={
                "decision_contract": DECISION_CONTRACT_PATH,
                "cpu_qualification": cpu_qualification_path,
                "a_prediction": a_files["prediction_final"],
                "a_physics_hashes": a_files["physics_hashes"],
                "b_prediction": b_files["prediction_final"],
                "b0_prediction": b_files["prediction_b0"],
                "b_final_checkpoint": b_files["checkpoint_final"],
                "b0_checkpoint": b_files["checkpoint_b0"],
                "b_physics_hashes": b_files["physics_hashes"],
                "lf_only_prediction": lf_only,
            },
        )
        report["c_trigger"] = {
            "path": str((output / "c-trigger.json").resolve()),
            "sha256": _sha256_path(output / "c-trigger.json"),
            "conditions": trigger["conditions"],
        }
    write_strict_json(output / "adjudication.json", report)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--a-run-directory", type=Path, required=True)
    parser.add_argument("--cpu-qualification", type=Path, required=True)
    parser.add_argument("--b-run-directory", type=Path)
    parser.add_argument("--c-run-directory", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    report = evaluate_lf1_campaign(
        output_directory=arguments.output_directory,
        a_run_directory=arguments.a_run_directory,
        cpu_qualification_path=arguments.cpu_qualification,
        b_run_directory=arguments.b_run_directory,
        c_run_directory=arguments.c_run_directory,
    )
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
