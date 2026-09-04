"""Post-shutdown nominal evaluation and adjudication for PHK-V2.3 LF2."""

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
    _prediction_potential_guard,
    _sanitize_nonfinite,
    _tensor_digest,
    compare_physics_batch_logs,
    competence_vector,
    safe_error_ratio,
    write_strict_json,
)
from .phk_v23_lf1 import ARM_A as LF1_ARM_A
from .phk_v23_lf1 import ARM_B as LF1_ARM_B
from .phk_v23_lf1 import TASK_ID as LF1_TASK_ID
from .phk_v23_lf1_evaluation import (
    A_ROLE as LF1_A_ROLE,
    B0_ROLE as LF1_B0_ROLE,
    B_FINAL_ROLE as LF1_B_FINAL_ROLE,
    LF_ONLY_ROLE,
    _competent,
    _evaluation_valid,
    compare_b_to_comparator,
)
from .phk_v23_lf2 import (
    TASK_ID,
    TRAJECTORY,
    load_contracts,
    read_cpu_qualification,
)


LF2_M0_ROLE = "LF2_M0_CALIBRATED_CARRIER"
LF2_FINAL_ROLE = "LF2_M1_FINAL"
GPU_LIFECYCLE_SHUTDOWN_VERIFIED = "SHUTDOWN_VERIFIED"
LF1_A_RUN_ROOT = (
    ROOT
    / "outputs"
    / "runs"
    / "20260903T134252Z-phk-v23-lf1-a-range-preserving-dc091be-er1"
)
LF1_B_RUN_ROOT = (
    ROOT
    / "outputs"
    / "runs"
    / "20260903T152501Z-phk-v23-lf1-b-event-replay-dc091be-er1"
)


def _terminal(
    outcome: str,
    *,
    contract: Mapping[str, Any],
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    mapping = contract["machine_outcomes_and_unique_next"]
    if outcome not in mapping:
        raise ValueError(f"unmapped LF2 outcome: {outcome}")
    return {
        "status": "TERMINAL",
        "outcome": outcome,
        "candidate": (
            LF2_FINAL_ROLE
            if outcome == "LF2_MEASURE_CALIBRATED_FEASIBLE_PINN_PROVISIONAL_SIGNAL"
            else None
        ),
        "unique_next": mapping[outcome],
        **dict(details or {}),
    }


def _safe_bound_path(record: Mapping[str, Any], *, label: str) -> Path:
    raw = record.get("path")
    if not isinstance(raw, str):
        raise ValueError(f"LF2 path binding is malformed: {label}")
    path = Path(raw)
    exact = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
    try:
        exact.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PermissionError(f"LF2 path binding escaped repository: {label}") from exc
    if (
        not exact.is_file()
        or _sha256_path(exact) != str(record.get("sha256", "")).upper()
        or (
            "size_bytes" in record
            and exact.stat().st_size != int(record.get("size_bytes", -1))
        )
    ):
        raise ValueError(f"LF2 path binding drift: {label}")
    return exact


def _artifact_path(
    root: Path, summary: Mapping[str, Any], key: str, *, required: bool = True
) -> Path | None:
    record = summary.get("artifacts", {}).get(key)
    if record is None and not required:
        return None
    if not isinstance(record, Mapping):
        raise ValueError(f"LF2 recovered run lacks artifact binding: {key}")
    relative = Path(str(record.get("path", "")))
    if relative.is_absolute() or ".." in relative.parts:
        raise PermissionError(f"LF2 recovered artifact escaped run root: {key}")
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise PermissionError(f"LF2 recovered artifact escaped run root: {key}") from exc
    if (
        not path.is_file()
        or path.stat().st_size != int(record.get("size_bytes", -1))
        or _sha256_path(path) != str(record.get("sha256", "")).upper()
    ):
        raise ValueError(f"LF2 recovered artifact drift: {key}")
    return path


def _lf2_run_files(path: Path) -> dict[str, Any]:
    root = Path(path).resolve()
    summary_path = root / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    statuses = {
        "LF2_REFERENCE_BLIND_GPU_TRAJECTORY_COMPLETE",
        "LF2_NUMERICAL_OR_IDENTITY_INVALID",
        "LF2_CALIBRATED_CARRIER_NOT_ESTABLISHED",
        "LF2_FEASIBILITY_PRESERVATION_FAILED",
    }
    if (
        summary.get("schema_id") != "phk-v23-lf2-reference-blind-run-summary-v1"
        or summary.get("task_id") != TASK_ID
        or summary.get("trajectory") != TRAJECTORY
        or summary.get("status") not in statuses
        or summary.get("prediction_reference_free") is not True
        or summary.get("fine_extra_fine_or_evaluator_read") is not False
        or summary.get("stress_fields_or_metrics_read") is not False
    ):
        raise ValueError("LF2 recovered run identity drift")
    result: dict[str, Any] = {
        "root": root,
        "summary": summary_path,
        "summary_payload": summary,
        "prediction_m0": _artifact_path(root, summary, "prediction_m0"),
        "checkpoint_m0": _artifact_path(root, summary, "checkpoint_m0"),
        "measure_hashes": _artifact_path(
            root, summary, "measure_data_batch_hashes"
        ),
        "m0_gate": _artifact_path(root, summary, "m0_gate"),
    }
    result["prediction_final"] = _artifact_path(
        root, summary, "prediction_final", required=False
    )
    result["checkpoint_final"] = _artifact_path(
        root, summary, "checkpoint_final", required=False
    )
    result["physics_hashes"] = _artifact_path(
        root, summary, "physics_batch_hashes", required=False
    )
    result["m1_gate"] = _artifact_path(
        root, summary, "m1_feasibility_gate", required=False
    )
    return result


def _lf1_run_artifact(root: Path, *, arm: str, key: str) -> Path:
    summary_path = root / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if (
        summary.get("schema_id") != "phk-v23-lf1-reference-blind-run-summary-v1"
        or summary.get("task_id") != LF1_TASK_ID
        or summary.get("run_arm") != arm
        or summary.get("status") != "LF1_REFERENCE_BLIND_GPU_RUN_COMPLETE"
    ):
        raise ValueError("LF2 inherited LF1 run identity drift")
    result = _artifact_path(root, summary, key)
    assert result is not None
    return result


def _inherited_prediction_paths(contract: Mapping[str, Any]) -> dict[str, Path]:
    adjudication_path = _safe_bound_path(
        contract["qualification_inputs"]["lf1_raw_adjudication"],
        label="LF1 terminal raw adjudication",
    )
    report = json.loads(adjudication_path.read_text(encoding="utf-8"))
    if (
        report.get("schema_id") != "phk-v23-lf1-local-adjudication-v1"
        or report.get("task_id") != LF1_TASK_ID
        or report.get("decision", {}).get("outcome")
        != "LF1_DATA_ONLY_VALUE_NO_PINN_GAIN"
        or report.get("stress_status") != "TWO_STRESS_REFERENCES_SEALED_UNREAD"
    ):
        raise ValueError("LF2 inherited LF1 adjudication identity drift")
    bindings = report.get("prediction_bindings", {})
    required = (LF1_A_ROLE, LF_ONLY_ROLE, LF1_B0_ROLE, LF1_B_FINAL_ROLE)
    if any(role not in bindings for role in required):
        raise ValueError("LF2 inherited comparator set is incomplete")
    return {
        role: _safe_bound_path(bindings[role], label=f"inherited {role}")
        for role in required
    }


def _component_floors(contract: Mapping[str, Any]) -> dict[str, float]:
    _safe_bound_path(
        contract["qualification_inputs"]["oracle_floor_contract"],
        label="PHK-V2.1 oracle and floor contract",
    )
    seal_path = _safe_bound_path(
        contract["qualification_inputs"]["oracle_floor_seal"],
        label="PHK-V2.1 oracle floor seal",
    )
    payload = json.loads(seal_path.read_text(encoding="utf-8"))
    order = payload.get("component_order")
    floors = payload.get("component_floors_U")
    if (
        payload.get("schema_id") != "phk-v21-oracle-floor-seal-v1"
        or not isinstance(order, list)
        or not isinstance(floors, list)
        or len(order) != len(floors)
    ):
        raise ValueError("LF2 oracle floor seal is malformed")
    by_name = {name: float(value) for name, value in zip(order, floors, strict=True)}
    return {
        "phase_roi_continuous_rms": by_name["PHASE_FIELD_ROI_RMS"],
        "time_averaged_phase_region_symmetric_difference": by_name[
            "TIME_AVERAGED_PHASE_REGION_SYMMETRIC_DIFFERENCE"
        ],
    }


def _verify_local_references(contracts: Mapping[str, Mapping[str, Any]]) -> None:
    for name, binding in contracts["data"]["local_evaluation_only"].items():
        _safe_bound_path(binding, label=f"local {name} reference")


def _fixed_physics_values(
    checkpoints: Mapping[str, Path], *, contract: Mapping[str, Any]
) -> dict[str, Any]:
    if set(checkpoints) not in ({LF2_M0_ROLE}, {LF2_M0_ROLE, LF2_FINAL_ROLE}):
        raise ValueError("LF2 fixed physics checkpoint roles are invalid")
    pool = contract["local_evaluation"]["fixed_reference_blind_physics_pool"]
    device = torch.device("cpu")
    loaded = {
        role: _load_model(path, device=device) for role, path in checkpoints.items()
    }
    if any(config.case_control != "FULL" for _, config, _ in loaded.values()):
        raise PermissionError("LF2 fixed physics diagnostic is nominal-only")
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
    total_boundary = int(pool["boundary_points_total"])
    if total_boundary % 4:
        raise ValueError("LF2 fixed boundary point total is not divisible by four")
    boundary = sampler.boundary(
        total_boundary // 4,
        active_windows=int(pool["active_windows"]),
        dtype=torch.float64,
        device=device,
    )
    initial = sampler.initial(
        int(pool["initial_points"]), dtype=torch.float64, device=device
    )
    ordered = tuple(boundary[name] for name in ("left", "right", "bottom", "top"))
    digest = _tensor_digest(
        interior,
        *ordered,
        initial,
        metadata="PHK_V23_LF2_FIXED_REFERENCE_BLIND_FULL_W1_W4",
    )
    batch = PhysicsBatch(
        interior=interior,
        boundary=boundary,
        initial=initial,
        active_windows=4,
        refreshed=True,
        interior_sha256=_tensor_digest(interior, metadata="LF2_FIXED_INTERIOR"),
        boundary_sha256=_tensor_digest(*ordered, metadata="LF2_FIXED_BOUNDARY"),
        initial_sha256=_tensor_digest(initial, metadata="LF2_FIXED_INITIAL"),
        batch_sha256=digest,
    )
    values: dict[str, float] = {}
    components: dict[str, Any] = {}
    for role, (model, config, _) in loaded.items():
        with torch.enable_grad():
            _, scalars = _physics_objective(model, _clone_batch(batch), config)
        values[role] = float(scalars["physics_total"])
        components[role] = scalars
    ratio = None
    defined = False
    if LF2_FINAL_ROLE in values:
        ratio, defined = safe_error_ratio(
            values[LF2_FINAL_ROLE], values[LF2_M0_ROLE]
        )
    maximum = float(
        contract["provisional_positive_gate"][
            "fixed_physics_objective_ratio_final_to_M0_maximum"
        ]
    )
    return {
        "fixed_pool_sha256": digest,
        "seed": int(pool["seed"]),
        "active_windows": int(pool["active_windows"]),
        "objective": pool["objective"],
        "values": values,
        "components": components,
        "final_to_M0": {
            "ratio": ratio,
            "defined": defined,
            "maximum": maximum,
            "passed": bool(defined and ratio is not None and ratio <= maximum),
        },
        "reference_or_low_fidelity_values_read": False,
        "device": "CPU",
        "dtype": "FLOAT64",
    }


def adjudicate(
    *,
    contract: Mapping[str, Any],
    run_status: str,
    evaluations: Mapping[str, Mapping[str, Any]],
    potential_guards: Mapping[str, Mapping[str, Any]],
    comparisons: Mapping[str, Mapping[str, Any]],
    physics: Mapping[str, Any],
    physics_batch_identity: Mapping[str, Any] | None,
    m0_gate: Mapping[str, Any],
    m1_gate: Mapping[str, Any] | None,
) -> dict[str, Any]:
    mandatory_roles = {LF_ONLY_ROLE, LF1_B0_ROLE, LF2_M0_ROLE}
    if LF2_FINAL_ROLE in evaluations:
        mandatory_roles.add(LF2_FINAL_ROLE)
    if (
        any(not _evaluation_valid(value) for value in evaluations.values())
        or any(
            potential_guards[role].get("passed") is not True
            for role in mandatory_roles
        )
        or run_status == "LF2_NUMERICAL_OR_IDENTITY_INVALID"
    ):
        return _terminal("LF2_NUMERICAL_OR_IDENTITY_INVALID", contract=contract)
    if run_status == "LF2_CALIBRATED_CARRIER_NOT_ESTABLISHED" or m0_gate.get(
        "passed"
    ) is not True:
        return _terminal("LF2_CALIBRATED_CARRIER_NOT_ESTABLISHED", contract=contract)
    if (
        run_status == "LF2_FEASIBILITY_PRESERVATION_FAILED"
        or m1_gate is None
        or m1_gate.get("passed") is not True
    ):
        return _terminal("LF2_FEASIBILITY_PRESERVATION_FAILED", contract=contract)
    if run_status != "LF2_REFERENCE_BLIND_GPU_TRAJECTORY_COMPLETE":
        raise ValueError("LF2 run status is unsupported at adjudication")
    if (
        physics_batch_identity is None
        or physics_batch_identity.get("passed") is not True
    ):
        return _terminal("LF2_NUMERICAL_OR_IDENTITY_INVALID", contract=contract)

    competence_pass = all(
        _competent(evaluations[role])
        for role in (LF_ONLY_ROLE, LF2_M0_ROLE, LF2_FINAL_ROLE)
    )
    comparison_pass = all(
        comparisons[role]["phase_noninferiority_passed"]
        and comparisons[role]["preservation_passed"]
        for role in (LF_ONLY_ROLE, LF2_M0_ROLE)
    )
    physics_pass = physics.get("final_to_M0", {}).get("passed") is True
    if not (competence_pass and comparison_pass and physics_pass):
        return _terminal(
            "LF2_NO_PINN_SPECIFIC_GAIN",
            contract=contract,
            details={
                "competence": {
                    role: competence_vector(evaluations[role])
                    for role in (LF_ONLY_ROLE, LF2_M0_ROLE, LF2_FINAL_ROLE)
                },
                "comparison_gate_passed": comparison_pass,
                "fixed_physics_gate_passed": physics_pass,
            },
        )
    return _terminal(
        "LF2_MEASURE_CALIBRATED_FEASIBLE_PINN_PROVISIONAL_SIGNAL",
        contract=contract,
    )


def evaluate_lf2_campaign(
    *,
    output_directory: Path,
    run_directory: Path,
    cpu_qualification_path: Path,
    case_control: str = "FULL",
    gpu_lifecycle: str = GPU_LIFECYCLE_SHUTDOWN_VERIFIED,
) -> dict[str, Any]:
    if case_control != PhkControl.FULL.value:
        raise PermissionError("LF2 evaluation is nominal-only; stress stays sealed")
    if gpu_lifecycle != GPU_LIFECYCLE_SHUTDOWN_VERIFIED:
        raise PermissionError("LF2 local evaluation requires verified GPU shutdown")
    contracts = load_contracts()
    read_cpu_qualification(cpu_qualification_path)
    contract = contracts["decision"]
    _verify_local_references(contracts)
    output = Path(output_directory).resolve()
    output.mkdir(parents=True, exist_ok=False)
    run = _lf2_run_files(run_directory)
    prediction_paths = _inherited_prediction_paths(contract)
    prediction_paths[LF2_M0_ROLE] = run["prediction_m0"]
    if run["prediction_final"] is not None:
        prediction_paths[LF2_FINAL_ROLE] = run["prediction_final"]

    evaluations = {
        role: evaluate_prediction(prediction_path=path, control=PhkControl.FULL)
        for role, path in prediction_paths.items()
    }
    tolerance = float(contract["potential_maximum_principle"]["absolute_tolerance"])
    potential_guards = {
        role: _prediction_potential_guard(path, absolute_tolerance=tolerance)
        for role, path in prediction_paths.items()
    }
    floors = _component_floors(contract)
    comparisons = (
        {
            role: compare_b_to_comparator(
                evaluations[LF2_FINAL_ROLE],
                evaluations[role],
                component_floors=floors,
            )
            for role in (LF_ONLY_ROLE, LF2_M0_ROLE)
        }
        if LF2_FINAL_ROLE in evaluations
        else {}
    )

    checkpoint_paths = {LF2_M0_ROLE: run["checkpoint_m0"]}
    if run["checkpoint_final"] is not None:
        checkpoint_paths[LF2_FINAL_ROLE] = run["checkpoint_final"]
    physics = _fixed_physics_values(checkpoint_paths, contract=contract)
    batch_identity = None
    if run["physics_hashes"] is not None and run["checkpoint_final"] is not None:
        lf1_a = _lf1_run_artifact(
            LF1_A_RUN_ROOT, arm=LF1_ARM_A, key="physics_batch_hashes"
        )
        lf1_b = _lf1_run_artifact(
            LF1_B_RUN_ROOT, arm=LF1_ARM_B, key="physics_batch_hashes"
        )
        against_a = compare_physics_batch_logs(lf1_a, run["physics_hashes"])
        against_b = compare_physics_batch_logs(lf1_b, run["physics_hashes"])
        batch_identity = {
            "passed": against_a["passed"] and against_b["passed"],
            "LF2_equals_LF1_A_stepwise": against_a,
            "LF2_equals_LF1_B_stepwise": against_b,
        }

    summary = run["summary_payload"]
    m0_gate = summary.get("m0_gate")
    m1_gate = summary.get("m1_feasibility_gate")
    if not isinstance(m0_gate, Mapping):
        raise ValueError("LF2 recovered summary lacks M0 gate")
    decision = adjudicate(
        contract=contract,
        run_status=str(summary["status"]),
        evaluations=evaluations,
        potential_guards=potential_guards,
        comparisons=comparisons,
        physics=physics,
        physics_batch_identity=batch_identity,
        m0_gate=m0_gate,
        m1_gate=m1_gate if isinstance(m1_gate, Mapping) else None,
    )
    sanitized, replaced = _sanitize_nonfinite(evaluations)
    report = {
        "schema_id": "phk-v23-lf2-local-adjudication-v1",
        "task_id": TASK_ID,
        "status": "COMPLETE",
        "case_control": "FULL",
        "gpu_lifecycle": gpu_lifecycle,
        "run_status": summary["status"],
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
        "full_medium_gates": {"M0": m0_gate, "M1": m1_gate},
        "decision": decision,
        "source_attribution": contract["source_attribution"],
        "claim_boundary": contract["claim_boundary"],
        "lf_only_role": "REUSED_MEDIUM_DIRECT_COMPARATOR_NOT_A_PINN",
        "fine_extra_fine_use": "LOCAL_NOMINAL_EVALUATION_ONLY_AFTER_SHUTDOWN",
        "stress_status": "TWO_STRESS_REFERENCES_SEALED_UNREAD",
    }
    write_strict_json(output / "adjudication.json", report)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--run-directory", type=Path, required=True)
    parser.add_argument("--cpu-qualification", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    report = evaluate_lf2_campaign(
        output_directory=arguments.output_directory,
        run_directory=arguments.run_directory,
        cpu_qualification_path=arguments.cpu_qualification,
    )
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


__all__ = [
    "GPU_LIFECYCLE_SHUTDOWN_VERIFIED",
    "LF2_FINAL_ROLE",
    "LF2_M0_ROLE",
    "adjudicate",
    "evaluate_lf2_campaign",
]
