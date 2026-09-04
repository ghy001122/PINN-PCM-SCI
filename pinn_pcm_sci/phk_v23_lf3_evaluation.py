"""Post-shutdown nominal evaluation and three-level LF3 adjudication."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .phk_benchmark import PhkControl
from .phk_v22r_evaluator import evaluate_prediction
from .phk_v22r_training import ROOT
from .phk_v23_lf0 import _sha256_path
from .phk_v23_lf0_evaluation import (
    _prediction_potential_guard,
    _sanitize_nonfinite,
    competence_vector,
    write_strict_json,
)
from .phk_v23_lf1_evaluation import (
    B0_ROLE as LF1_B0_ROLE,
    B_FINAL_ROLE as LF1_B_FINAL_ROLE,
    LF_ONLY_ROLE,
    _competent,
    _evaluation_valid,
    compare_b_to_comparator,
)
from .phk_v23_lf2_evaluation import (
    LF2_FINAL_ROLE as _POOL_FINAL_ROLE,
    LF2_M0_ROLE as _POOL_M0_ROLE,
    _component_floors,
    _fixed_physics_values,
    _inherited_prediction_paths,
    _safe_bound_path,
)
from .phk_v23_lf3 import TASK_ID, TRAJECTORY, load_contracts, read_cpu_qualification


LF2_M0_ROLE = "LF2_M0_CALIBRATED_CARRIER"
LF3_T0_ROLE = "LF3_T0_LATENT_CARRIER"
LF3_P0_ROLE = "LF3_P0_FULL_PHYSICS"
GPU_LIFECYCLE_SHUTDOWN_VERIFIED = "SHUTDOWN_VERIFIED"


def _artifact_path(root: Path, summary: Mapping[str, Any], key: str, *, required: bool = True) -> Path | None:
    record = summary.get("artifacts", {}).get(key)
    if record is None and not required:
        return None
    if not isinstance(record, Mapping):
        raise ValueError(f"LF3 recovered run lacks artifact: {key}")
    relative = Path(str(record.get("path", "")))
    if relative.is_absolute() or ".." in relative.parts:
        raise PermissionError(f"LF3 artifact escaped run root: {key}")
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise PermissionError(f"LF3 artifact escaped run root: {key}") from exc
    if (
        not path.is_file()
        or path.stat().st_size != int(record.get("size_bytes", -1))
        or _sha256_path(path) != str(record.get("sha256", "")).upper()
    ):
        raise ValueError(f"LF3 recovered artifact drift: {key}")
    return path


def _run_files(path: Path) -> dict[str, Any]:
    root = Path(path).resolve()
    summary_path = root / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    allowed = {
        "LF3_REFERENCE_BLIND_GPU_TRAJECTORY_COMPLETE", "LF3_NUMERICAL_OR_IDENTITY_INVALID",
        "LF3_TEMPORAL_CARRIER_FAILURE", "LF3_CARRIER_NOT_ESTABLISHED", "LF3_P0_PRESERVATION_FAILED",
    }
    if (
        summary.get("schema_id") != "phk-v23-lf3-reference-blind-run-summary-v1"
        or summary.get("task_id") != TASK_ID or summary.get("trajectory") != TRAJECTORY
        or summary.get("status") not in allowed
        or summary.get("prediction_reference_free") is not True
        or summary.get("fine_extra_fine_lf_only_or_evaluator_read") is not False
        or summary.get("stress_fields_or_metrics_read") is not False
    ):
        raise ValueError("LF3 recovered run identity drift")
    result = {
        "root": root, "summary": summary_path, "summary_payload": summary,
        "prediction_t0": _artifact_path(root, summary, "prediction_t0"),
        "checkpoint_t0": _artifact_path(root, summary, "checkpoint_t0"),
        "T0_gate": _artifact_path(root, summary, "T0_gate"),
        "T0_hashes": _artifact_path(root, summary, "T0_measure_batch_hashes"),
        "prediction_p0": _artifact_path(root, summary, "prediction_p0", required=False),
        "checkpoint_p0": _artifact_path(root, summary, "checkpoint_p0", required=False),
        "P0_gate": _artifact_path(root, summary, "P0_gate", required=False),
        "P0_hashes": _artifact_path(root, summary, "P0_physics_batch_hashes", required=False),
    }
    return result


def _terminal(outcome: str, *, contract: Mapping[str, Any], details: Mapping[str, Any] | None = None) -> dict[str, Any]:
    mapping = contract["machine_outcomes_and_unique_next"]
    if outcome not in mapping:
        raise ValueError(f"unmapped LF3 outcome: {outcome}")
    return {
        "status": "TERMINAL", "outcome": outcome,
        "candidate": LF3_P0_ROLE if outcome == "LF3_PROVISIONAL_CANDIDATE_SIGNAL" else None,
        "unique_next": mapping[outcome], **dict(details or {}),
    }


def adjudicate(
    *,
    contract: Mapping[str, Any],
    run_status: str,
    evaluations: Mapping[str, Mapping[str, Any]],
    potential_guards: Mapping[str, Mapping[str, Any]],
    comparisons: Mapping[str, Mapping[str, Any]],
    physics: Mapping[str, Any],
    t0_gate: Mapping[str, Any],
    p0_gate: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if run_status == "LF3_NUMERICAL_OR_IDENTITY_INVALID":
        return _terminal("LF3_NUMERICAL_OR_IDENTITY_INVALID", contract=contract)
    mandatory = {LF_ONLY_ROLE, LF1_B0_ROLE, LF1_B_FINAL_ROLE, LF2_M0_ROLE, LF3_T0_ROLE}
    if LF3_P0_ROLE in evaluations:
        mandatory.add(LF3_P0_ROLE)
    if any(not _evaluation_valid(evaluations[role]) for role in mandatory) or any(potential_guards[role].get("passed") is not True for role in mandatory):
        return _terminal("LF3_NUMERICAL_OR_IDENTITY_INVALID", contract=contract)
    if run_status == "LF3_TEMPORAL_CARRIER_FAILURE" or t0_gate.get("temporal_only_failure") is True:
        return _terminal("LF3_TEMPORAL_CARRIER_FAILURE", contract=contract)
    if run_status == "LF3_CARRIER_NOT_ESTABLISHED" or t0_gate.get("passed") is not True:
        return _terminal("LF3_CARRIER_NOT_ESTABLISHED", contract=contract)
    if run_status == "LF3_P0_PRESERVATION_FAILED" or p0_gate is None or p0_gate.get("passed") is not True:
        return _terminal("LF3_P0_PRESERVATION_FAILED", contract=contract)
    if run_status != "LF3_REFERENCE_BLIND_GPU_TRAJECTORY_COMPLETE" or LF3_P0_ROLE not in evaluations:
        raise ValueError("LF3 run status is unsupported at adjudication")

    t0_compare = comparisons["P0_vs_T0"]
    pool = physics.get("final_to_M0", {})
    level2 = bool(
        _competent(evaluations[LF3_T0_ROLE]) and _competent(evaluations[LF3_P0_ROLE])
        and t0_compare["phase_noninferiority_passed"] and t0_compare["preservation_passed"]
        and pool.get("passed") is True
    )
    if not level2:
        return _terminal(
            "LF3_NO_PINN_PARETO", contract=contract,
            details={
                "level_1_carrier_success": True, "level_2_single_seed_pinn_specific_pilot": False,
                "competence": {role: competence_vector(evaluations[role]) for role in (LF3_T0_ROLE, LF3_P0_ROLE)},
                "P0_vs_T0": t0_compare, "fixed_physics_gate": pool,
            },
        )
    direct = comparisons["P0_vs_LF_ONLY"]
    level3 = bool(
        _competent(evaluations[LF_ONLY_ROLE]) and _competent(evaluations[LF3_P0_ROLE])
        and direct["phase_noninferiority_passed"] and direct["preservation_passed"]
        and potential_guards[LF_ONLY_ROLE]["passed"] and potential_guards[LF3_P0_ROLE]["passed"]
    )
    if not level3:
        return _terminal(
            "LF3_DIRECT_BASELINE_GAP", contract=contract,
            details={
                "level_1_carrier_success": True, "level_2_single_seed_pinn_specific_pilot": True,
                "level_3_candidate_signal": False, "P0_vs_LF_ONLY": direct,
            },
        )
    return _terminal(
        "LF3_PROVISIONAL_CANDIDATE_SIGNAL", contract=contract,
        details={"level_1_carrier_success": True, "level_2_single_seed_pinn_specific_pilot": True, "level_3_candidate_signal": True},
    )


def evaluate_lf3_campaign(
    *, output_directory: Path, run_directory: Path, cpu_qualification_path: Path,
    case_control: str = "FULL", gpu_lifecycle: str = GPU_LIFECYCLE_SHUTDOWN_VERIFIED,
) -> dict[str, Any]:
    if case_control != PhkControl.FULL.value:
        raise PermissionError("LF3 evaluation is nominal-only; stress stays sealed")
    if gpu_lifecycle != GPU_LIFECYCLE_SHUTDOWN_VERIFIED:
        raise PermissionError("LF3 local evaluation requires verified GPU shutdown")
    contracts = load_contracts()
    read_cpu_qualification(cpu_qualification_path)
    contract = contracts["decision"]
    # These references are intentionally first touched only after the lifecycle gate above.
    for name, binding in contracts["data"]["local_evaluation_only"].items():
        _safe_bound_path(binding, label=f"local {name}")
    run = _run_files(run_directory)
    paths = _inherited_prediction_paths(contract)
    paths.pop("A_RANGE_PRESERVING_SCRATCH", None)
    paths[LF2_M0_ROLE] = _safe_bound_path(contracts["data"]["inherited_comparators"]["lf2_m0_prediction"], label="LF2-M0 prediction")
    paths[LF3_T0_ROLE] = run["prediction_t0"]
    if run["prediction_p0"] is not None:
        paths[LF3_P0_ROLE] = run["prediction_p0"]
    evaluations = {role: evaluate_prediction(prediction_path=path, control=PhkControl.FULL) for role, path in paths.items()}
    tolerance = float(contract["potential_maximum_principle"]["absolute_tolerance"])
    potential = {role: _prediction_potential_guard(path, absolute_tolerance=tolerance) for role, path in paths.items()}
    floors = _component_floors(contract)
    comparisons: dict[str, Any] = {}
    if LF3_P0_ROLE in evaluations:
        comparisons = {
            "P0_vs_T0": compare_b_to_comparator(evaluations[LF3_P0_ROLE], evaluations[LF3_T0_ROLE], component_floors=floors),
            "P0_vs_LF_ONLY": compare_b_to_comparator(evaluations[LF3_P0_ROLE], evaluations[LF_ONLY_ROLE], component_floors=floors),
        }
    checkpoints = {_POOL_M0_ROLE: run["checkpoint_t0"]}
    if run["checkpoint_p0"] is not None:
        checkpoints[_POOL_FINAL_ROLE] = run["checkpoint_p0"]
    pool_contract = {
        "local_evaluation": contract["local_evaluation"],
        "provisional_positive_gate": {"fixed_physics_objective_ratio_final_to_M0_maximum": 0.5},
    }
    physics = _fixed_physics_values(checkpoints, contract=pool_contract)
    if physics["fixed_pool_sha256"] != contract["local_evaluation"]["fixed_reference_blind_physics_pool"]["sha256"]:
        raise ValueError("LF3 fixed physics pool identity drift")
    summary = run["summary_payload"]
    decision = adjudicate(
        contract=contract, run_status=str(summary["status"]), evaluations=evaluations,
        potential_guards=potential, comparisons=comparisons, physics=physics,
        t0_gate=summary["T0_gate"], p0_gate=summary.get("P0_gate"),
    )
    sanitized, replaced = _sanitize_nonfinite(evaluations)
    report = {
        "schema_id": "phk-v23-lf3-local-adjudication-v1", "task_id": TASK_ID,
        "status": "COMPLETE", "case_control": "FULL", "gpu_lifecycle": gpu_lifecycle,
        "run_status": summary["status"], "roles_evaluated": list(paths),
        "prediction_bindings": {role: {"path": str(path), "sha256": _sha256_path(path), "size_bytes": path.stat().st_size} for role, path in paths.items()},
        "evaluations": sanitized, "evaluator_nonfinite_diagnostics_represented_as_json_null": replaced,
        "potential_maximum_principle": potential, "component_floors": floors,
        "comparisons": comparisons, "fixed_physics_objective": physics,
        "full_medium_gates": {"T0": summary["T0_gate"], "P0": summary.get("P0_gate")},
        "decision": decision,
        "three_level_boundary": contract["decision_levels"],
        "claim_boundary": contract["claim_boundary"],
        "lf_only_role": "STRONGEST_DIRECT_MEDIUM_BASELINE_NOT_A_PINN",
        "fine_extra_fine_use": "LOCAL_NOMINAL_EVALUATION_ONLY_AFTER_SHUTDOWN",
        "stress_status": "TWO_STRESS_REFERENCES_SEALED_UNREAD",
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = evaluate_lf3_campaign(output_directory=args.output_directory, run_directory=args.run_directory, cpu_qualification_path=args.cpu_qualification)
    print(json.dumps({"outcome": report["decision"]["outcome"], "candidate": report["decision"]["candidate"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["LF3_P0_ROLE", "LF3_T0_ROLE", "adjudicate", "evaluate_lf3_campaign"]
