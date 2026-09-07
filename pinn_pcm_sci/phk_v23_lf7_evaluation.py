"""Post-shutdown nominal evaluation and terminal adjudication for LF7."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import torch

from .phk_benchmark import PhkControl
from .phk_v22r_evaluator import evaluate_prediction
from .phk_v22r_prediction import _load_model
from .phk_v22r_training import ROOT
from .phk_v23_lf0 import _physics_objective, _read_json, _sha256_path
from .phk_v23_lf0_evaluation import (
    _prediction_potential_guard,
    _sanitize_nonfinite,
    safe_error_ratio,
    write_strict_json,
)
from .phk_v23_lf1_evaluation import (
    LF_ONLY_ROLE,
    _competent,
    _evaluation_valid,
    compare_b_to_comparator,
)
from .phk_v23_lf2_evaluation import (
    _component_floors,
    _inherited_prediction_paths,
    _safe_bound_path,
)
from .phk_v23_lf7 import (
    ARM_ORDER,
    EXPECTED_FIXED_POOL_SHA256,
    EXPECTED_J0,
    MAX_FILTER_ATTEMPTED_UPDATES,
    MaterializedPhysicsLedger,
    P0_F,
    P0_S,
    P0_UPDATES,
    TASK_ID,
    load_contracts,
    read_cpu_qualification,
)


DEV_R_ROLE = "LF6_DEV_R_SAFETY_NEAR_CARRIER"
GPU_LIFECYCLE_SHUTDOWN_VERIFIED = "SHUTDOWN_VERIFIED"
SHUTDOWN_PROOF_SCHEMA = "phk-v23-lf7-autodl-shutdown-proof-v1"


def _verify_shutdown_proof(path: Path) -> dict[str, Any]:
    """Verify the recovery/shutdown sequence before any local reference I/O."""

    supplied = Path(path).resolve()
    payload = _read_json(supplied)
    pre = payload.get("pre_shutdown", {})
    post = payload.get("post_shutdown", {})
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
        raise PermissionError("LF7 local evaluation requires exact recovery and shutdown proof")
    return payload


def _artifact_path(
    root: Path, summary: Mapping[str, Any], key: str, *, required: bool = True
) -> Path | None:
    record = summary.get("artifacts", {}).get(key)
    if record is None and not required:
        return None
    if not isinstance(record, Mapping):
        raise ValueError(f"LF7 recovered run lacks artifact: {key}")
    relative = Path(str(record.get("path", "")))
    if relative.is_absolute() or ".." in relative.parts:
        raise PermissionError(f"LF7 artifact escaped run root: {key}")
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise PermissionError(f"LF7 artifact escaped run root: {key}") from exc
    if (
        not path.is_file()
        or path.stat().st_size != int(record.get("size_bytes", -1))
        or _sha256_path(path) != str(record.get("sha256", "")).upper()
    ):
        raise ValueError(f"LF7 recovered artifact drift: {key}")
    return path


def _bound_input_path(
    record: Mapping[str, Any], *, path_key: str, sha_key: str, label: str
) -> Path:
    raw = record.get(path_key)
    if not isinstance(raw, str):
        raise ValueError(f"LF7 malformed input path: {label}")
    path = (ROOT / raw).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PermissionError(f"LF7 input escaped repository: {label}") from exc
    if not path.is_file() or _sha256_path(path) != str(record.get(sha_key, "")).upper():
        raise ValueError(f"LF7 input binding drift: {label}")
    return path


def _run_files(path: Path, *, contracts: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    root = Path(path).resolve()
    summary_path = root / "run_summary.json"
    summary = _read_json(summary_path)
    arms = summary.get("arms", {})
    if (
        summary.get("schema_id") != "phk-v23-lf7-reference-blind-run-summary-v1"
        or summary.get("task_id") != TASK_ID
        or summary.get("status")
        not in {
            "LF7_REFERENCE_BLIND_GPU_CAMPAIGN_COMPLETE",
            "LF7_MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID",
        }
        or set(arms) != set(ARM_ORDER)
        or summary.get("fine_extra_lf_only_evaluator_stress_read") is not False
        or summary.get("runtime_sampling_used") is not False
        or summary.get("medium_gradient_used") is not False
        or int(summary.get("total_attempted_optimizer_updates", -1))
        != sum(int(arms[role].get("attempted_updates", -1)) for role in ARM_ORDER)
        or int(summary.get("total_attempted_optimizer_updates", -1)) > 3600
    ):
        raise ValueError("LF7 recovered run identity drift")

    files: dict[str, Any] = {
        "root": root,
        "summary": summary_path,
        "summary_payload": summary,
        "checkpoints": {},
        "predictions": {},
    }
    for role in ARM_ORDER:
        arm = arms[role]
        if int(arm.get("accepted_updates", -1)) < 0:
            raise ValueError(f"LF7 invalid accepted-update count: {role}")
        if role == P0_S and int(arm.get("attempted_updates", -1)) > P0_UPDATES:
            raise ValueError("LF7 P0-S exceeded its update bound")
        if role == P0_F and int(arm.get("attempted_updates", -1)) > MAX_FILTER_ATTEMPTED_UPDATES:
            raise ValueError("LF7 P0-F exceeded its attempt bound")
        for name in ("telemetry.jsonl", "batch_ledger.jsonl", "gate.json", "exit.json"):
            _artifact_path(root, summary, f"{role}:{name}")
        valid = arm.get("numerical_valid") is True
        checkpoint = _artifact_path(root, summary, f"{role}:checkpoint.pt", required=valid)
        prediction = _artifact_path(root, summary, f"{role}:prediction.npz", required=valid)
        if valid and (checkpoint is None or prediction is None):
            raise ValueError(f"LF7 valid arm lacks endpoint artifacts: {role}")
        if checkpoint is not None:
            files["checkpoints"][role] = checkpoint
        if prediction is not None:
            files["predictions"][role] = prediction

    initial = contracts["data"]["initial_DEV_R"]
    files["checkpoints"][DEV_R_ROLE] = _bound_input_path(
        initial, path_key="checkpoint_path", sha_key="checkpoint_sha256", label="exact DEV-R checkpoint"
    )
    files["predictions"][DEV_R_ROLE] = _bound_input_path(
        initial, path_key="prediction_path", sha_key="prediction_sha256", label="exact DEV-R prediction"
    )
    return files


def _fixed_physics(
    checkpoints: Mapping[str, Path],
    *,
    contracts: Mapping[str, Mapping[str, Any]],
    qualification: Mapping[str, Any],
) -> dict[str, Any]:
    if DEV_R_ROLE not in checkpoints or not set(checkpoints).issubset({DEV_R_ROLE, P0_S, P0_F}):
        raise ValueError("LF7 fixed-physics checkpoint roles drift")
    ledger = MaterializedPhysicsLedger(
        ROOT / contracts["data"]["materialized_ledger"]["path"],
        contracts=contracts,
        qualification=qualification,
    )
    device = torch.device("cpu")
    values: dict[str, float] = {}
    components: dict[str, Mapping[str, float]] = {}
    for role, path in checkpoints.items():
        model, config, _ = _load_model(path, device=device)
        with torch.enable_grad():
            _, scalars = _physics_objective(model, ledger.fixed_batch(device=device), config)
        values[role] = float(scalars["physics_total"])
        components[role] = scalars
    if not math.isclose(values[DEV_R_ROLE], EXPECTED_J0, rel_tol=1.0e-10, abs_tol=1.0e-12):
        raise ValueError("LF7 local fixed-blind DEV-R objective drift")
    arms: dict[str, Any] = {}
    for role in ARM_ORDER:
        if role not in values:
            continue
        ratio, defined = safe_error_ratio(values[role], values[DEV_R_ROLE])
        arms[role] = {
            "ratio_to_DEV_R": ratio,
            "defined": defined,
            "maximum": 0.50,
            "passed": bool(defined and ratio is not None and ratio <= 0.50),
        }
    return {
        "fixed_pool_sha256": EXPECTED_FIXED_POOL_SHA256,
        "source": "CPU_POST_SHUTDOWN_PREMATERIALIZED_LEDGER_NO_RUNTIME_SAMPLING",
        "values": values,
        "components": components,
        "arms": arms,
        "reference_or_low_fidelity_values_read": False,
        "device": "CPU",
        "dtype": "FLOAT64",
    }


def _arm_levels(
    role: str,
    *,
    run: Mapping[str, Any],
    evaluations: Mapping[str, Mapping[str, Any]],
    potential: Mapping[str, Mapping[str, Any]],
    comparisons: Mapping[str, Mapping[str, Any]],
    physics: Mapping[str, Any],
) -> dict[str, bool]:
    arm = run["arms"][role]
    endpoint_valid = bool(
        arm.get("numerical_valid") is True
        and role in evaluations
        and _evaluation_valid(evaluations[role])
        and potential.get(role, {}).get("passed") is True
    )
    fixed = physics.get("arms", {}).get(role, {})
    dense = bool(
        endpoint_valid
        and arm.get("safety_gate", {}).get("passed") is True
        and fixed.get("passed") is True
        and (role != P0_F or int(arm.get("accepted_blocks", 0)) >= 1)
    )
    strict = bool(dense and arm.get("strict_gate", {}).get("passed") is True)
    within = comparisons.get(f"{role}_vs_DEV_R", {})
    local = bool(
        strict
        and _competent(evaluations[DEV_R_ROLE])
        and _competent(evaluations[role])
        and potential.get(DEV_R_ROLE, {}).get("passed") is True
        and within.get("phase_noninferiority_passed") is True
        and within.get("preservation_passed") is True
        and fixed.get("passed") is True
    )
    direct_comparison = comparisons.get(f"{role}_vs_LF_ONLY", {})
    direct = bool(
        local
        and _competent(evaluations[LF_ONLY_ROLE])
        and direct_comparison.get("phase_noninferiority_passed") is True
        and direct_comparison.get("preservation_passed") is True
        and potential.get(LF_ONLY_ROLE, {}).get("passed") is True
    )
    return {
        "endpoint_valid": endpoint_valid,
        "dense_safety_pareto": dense,
        "strict_carrier": strict,
        "local_pinn_pareto": local,
        "direct_paper_value": direct,
    }


def matched_mechanism_outcome(
    run: Mapping[str, Any], levels: Mapping[str, Mapping[str, bool]]
) -> str:
    """Apply the frozen matched rule to DENSE safety-Pareto, not safety alone."""

    if any(not levels[role]["endpoint_valid"] for role in ARM_ORDER):
        return "MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID"
    if levels[P0_S]["dense_safety_pareto"]:
        return "SMALL_LR_SUFFICIENT_FILTER_NOT_LOAD_BEARING"
    if levels[P0_F]["dense_safety_pareto"]:
        return "COMPETENCE_FILTER_LOAD_BEARING"
    if str(run["arms"][P0_F].get("disposition", "")).startswith("CFBR_STALLED"):
        return "FILTER_STALLED_NO_FEASIBLE_BLOCK_PATH"
    return "NO_PRESERVATION_COMPATIBLE_STRONG_FORM_PATH_FOUND"


def _terminal(
    outcome: str,
    *,
    contract: Mapping[str, Any],
    candidate: str | None = None,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    mapping = contract["machine_outcomes_and_unique_next"]
    if outcome not in mapping:
        raise ValueError(f"unmapped LF7 outcome: {outcome}")
    return {
        "status": "TERMINAL",
        "outcome": outcome,
        "candidate": candidate,
        "unique_next": mapping[outcome],
        "next_research_execution_authorized": False,
        **dict(details or {}),
    }


def adjudicate(
    *,
    contract: Mapping[str, Any],
    run: Mapping[str, Any],
    evaluations: Mapping[str, Mapping[str, Any]],
    potential: Mapping[str, Mapping[str, Any]],
    comparisons: Mapping[str, Mapping[str, Any]],
    physics: Mapping[str, Any],
) -> dict[str, Any]:
    levels = {
        role: _arm_levels(
            role,
            run=run,
            evaluations=evaluations,
            potential=potential,
            comparisons=comparisons,
            physics=physics,
        )
        for role in ARM_ORDER
    }
    mechanism = matched_mechanism_outcome(run, levels)
    detail = {
        "mechanism_outcome": mechanism,
        "gpu_reported_mechanism_outcome": run.get("mechanism_outcome"),
        "safety_pareto_outcome": {role: levels[role]["dense_safety_pareto"] for role in ARM_ORDER},
        "strict_carrier_outcome": {role: levels[role]["strict_carrier"] for role in ARM_ORDER},
        "local_pinn_outcome": {role: levels[role]["local_pinn_pareto"] for role in ARM_ORDER},
        "direct_baseline_outcome": {role: levels[role]["direct_paper_value"] for role in ARM_ORDER},
        "arm_levels": levels,
    }
    if mechanism == "MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID":
        return _terminal("LF7_MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID", contract=contract, details=detail)
    if not any(levels[role]["dense_safety_pareto"] for role in ARM_ORDER):
        outcome = (
            "LF7_FILTER_STALLED_NO_FEASIBLE_BLOCK_PATH"
            if mechanism == "FILTER_STALLED_NO_FEASIBLE_BLOCK_PATH"
            else "LF7_NO_PRESERVATION_COMPATIBLE_STRONG_FORM_PATH"
        )
        return _terminal(outcome, contract=contract, details=detail)
    if not any(levels[role]["local_pinn_pareto"] for role in ARM_ORDER):
        return _terminal("LF7_SAFETY_PRESERVING_PHYSICS_SIGNAL_ONLY", contract=contract, details=detail)
    direct_roles = [role for role in ARM_ORDER if levels[role]["direct_paper_value"]]
    if not direct_roles:
        return _terminal("LF7_SINGLE_SEED_PINN_PILOT_DIRECT_BASELINE_GAP", contract=contract, details=detail)
    candidate = P0_S if P0_S in direct_roles else P0_F
    return _terminal(
        "LF7_PROVISIONAL_SINGLE_SEED_DENSE_SIGNAL",
        contract=contract,
        candidate=candidate,
        details={**detail, "single_seed_only": True},
    )


def evaluate_lf7_campaign(
    *,
    output_directory: Path,
    run_directory: Path,
    cpu_qualification_path: Path,
    shutdown_proof_path: Path,
    case_control: str = "FULL",
) -> dict[str, Any]:
    if case_control != PhkControl.FULL.value:
        raise PermissionError("LF7 local evaluation is nominal-only; stress stays sealed")
    shutdown = _verify_shutdown_proof(shutdown_proof_path)
    contracts = load_contracts()
    qualification = read_cpu_qualification(cpu_qualification_path)

    # These local references are intentionally first touched after shutdown proof.
    for name, binding in contracts["data"]["local_evaluation_only"].items():
        if isinstance(binding, Mapping) and "path" in binding:
            _safe_bound_path(binding, label=f"LF7 local {name}")
    run_files = _run_files(run_directory, contracts=contracts)
    run = run_files["summary_payload"]

    lf3_decision = _read_json(ROOT / "configs/phk_v23/decision_contract_lf3_phase_latent_carrier.json")
    inherited = _inherited_prediction_paths(lf3_decision)
    direct_path = inherited[LF_ONLY_ROLE]
    expected_direct = contracts["data"]["local_evaluation_only"]["direct_LF_ONLY_prediction_sha256"]
    if _sha256_path(direct_path) != expected_direct:
        raise ValueError("LF7 direct LF_ONLY prediction binding drift")

    paths = {DEV_R_ROLE: run_files["predictions"][DEV_R_ROLE], LF_ONLY_ROLE: direct_path}
    paths.update({role: path for role, path in run_files["predictions"].items() if role in ARM_ORDER})
    evaluations = {
        role: evaluate_prediction(prediction_path=path, control=PhkControl.FULL)
        for role, path in paths.items()
    }
    potential = {
        role: _prediction_potential_guard(path, absolute_tolerance=1.0e-6)
        for role, path in paths.items()
    }
    if not _evaluation_valid(evaluations[DEV_R_ROLE]) or not _evaluation_valid(evaluations[LF_ONLY_ROLE]):
        raise ValueError("LF7 frozen comparator evaluation is invalid")

    floors = _component_floors(lf3_decision)
    comparisons: dict[str, Any] = {}
    for role in ARM_ORDER:
        if role not in evaluations:
            continue
        comparisons[f"{role}_vs_DEV_R"] = compare_b_to_comparator(
            evaluations[role], evaluations[DEV_R_ROLE], component_floors=floors
        )
        comparisons[f"{role}_vs_LF_ONLY"] = compare_b_to_comparator(
            evaluations[role], evaluations[LF_ONLY_ROLE], component_floors=floors
        )
    physics = _fixed_physics(
        run_files["checkpoints"], contracts=contracts, qualification=qualification
    )
    decision = adjudicate(
        contract=contracts["decision"],
        run=run,
        evaluations=evaluations,
        potential=potential,
        comparisons=comparisons,
        physics=physics,
    )
    sanitized, replaced = _sanitize_nonfinite(evaluations)
    report = {
        "schema_id": "phk-v23-lf7-local-adjudication-v1",
        "task_id": TASK_ID,
        "status": "COMPLETE",
        "case_control": "FULL",
        "gpu_lifecycle": GPU_LIFECYCLE_SHUTDOWN_VERIFIED,
        "shutdown_proof": {
            "path": str(Path(shutdown_proof_path).resolve()),
            "sha256": _sha256_path(Path(shutdown_proof_path).resolve()),
            "schema_id": shutdown["schema_id"],
        },
        "run_status": run["status"],
        "roles_evaluated": list(paths),
        "prediction_bindings": {
            role: {"path": str(path), "sha256": _sha256_path(path), "size_bytes": path.stat().st_size}
            for role, path in paths.items()
        },
        "evaluations": sanitized,
        "evaluator_nonfinite_diagnostics_represented_as_json_null": replaced,
        "potential_maximum_principle": potential,
        "component_floors": floors,
        "comparisons": comparisons,
        "fixed_physics_objective": physics,
        "gpu_arm_gates": {role: run["arms"][role] for role in ARM_ORDER},
        "decision": decision,
        "claim_boundary": contracts["decision"]["claim_boundary"],
        "lf_only_role": "STRONGEST_DIRECT_MEDIUM_BASELINE_NOT_A_PINN",
        "fine_extra_use": "LOCAL_NOMINAL_ONLY_AFTER_VERIFIED_SHUTDOWN",
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
    parser.add_argument("--shutdown-proof", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = evaluate_lf7_campaign(
        output_directory=args.output_directory,
        run_directory=args.run_directory,
        cpu_qualification_path=args.cpu_qualification,
        shutdown_proof_path=args.shutdown_proof,
    )
    print(
        json.dumps(
            {"outcome": report["decision"]["outcome"], "candidate": report["decision"]["candidate"]},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DEV_R_ROLE",
    "GPU_LIFECYCLE_SHUTDOWN_VERIFIED",
    "SHUTDOWN_PROOF_SCHEMA",
    "_arm_levels",
    "_verify_shutdown_proof",
    "adjudicate",
    "evaluate_lf7_campaign",
    "matched_mechanism_outcome",
]
