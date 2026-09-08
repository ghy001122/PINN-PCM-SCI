"""Post-shutdown nominal adjudication for LF8 competence-filter attribution."""

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
from .phk_v22r_training import ROOT, load_case_physics
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
from .phk_v23_lf2 import load_medium_dataset
from .phk_v23_lf3 import full_medium_audit
from .phk_v23_lf8 import (
    ARM_ORDER,
    EXPECTED_FIXED_POOL_SHA256,
    EXPECTED_J0,
    MAX_FILTER_ATTEMPTED_UPDATES,
    MaterializedPhysicsLedger,
    P0_C,
    P0_FSTAR,
    P0_UPDATES,
    TASK_ID,
    competence_gate,
    filter_path_disposition,
    load_contracts,
    read_cpu_qualification,
)


DEV_R_ROLE = "LF6_DEV_R_SAFETY_NEAR_CARRIER"
SHUTDOWN_PROOF_SCHEMA = "phk-v23-lf8-autodl-shutdown-proof-v1"


def evidence_levels(
    *,
    accepted_updates: int,
    endpoint_valid: bool,
    safety_passed: bool,
    strict_passed: bool,
    fixed_blind_ratio: float,
    local_noninferiority: bool,
    direct_noninferiority: bool,
) -> dict[str, bool]:
    complete = bool(
        endpoint_valid
        and accepted_updates == P0_UPDATES
        and safety_passed
        and math.isfinite(fixed_blind_ratio)
        and fixed_blind_ratio < 1.0
    )
    single = bool(
        complete
        and strict_passed
        and fixed_blind_ratio <= 0.50
        and local_noninferiority
    )
    return {
        "complete_safety_path": complete,
        "single_seed_pinn_pareto": single,
        "dense_paper_value": bool(single and direct_noninferiority),
    }


def matched_schedule_outcome(arms: Mapping[str, Mapping[str, Any]]) -> str:
    fstar = arms.get(P0_FSTAR, {})
    control = arms.get(P0_C, {})
    if not (
        fstar.get("endpoint_valid") is True
        and control.get("endpoint_valid") is True
        and int(fstar.get("accepted_updates", -1)) == P0_UPDATES
        and int(control.get("accepted_updates", -1)) == P0_UPDATES
    ):
        return "MATCHED_ATTRIBUTION_UNAVAILABLE"
    if fstar.get("safety_gate", {}).get("passed") is not True:
        return "MATCHED_ATTRIBUTION_UNAVAILABLE"
    if control.get("safety_gate", {}).get("passed") is True:
        return "SCHEDULE_SUFFICIENT_FILTER_NOT_LOAD_BEARING"
    return "COMPETENCE_FILTER_LOAD_BEARING_FOR_PRESERVATION"


def terminal_outcome(
    decision: Mapping[str, Any],
    *,
    fstar_disposition: str,
    identity_valid: bool = True,
    safety: bool = False,
    physics: bool = False,
    strict: bool = False,
    local: bool = False,
    direct: bool = False,
    mechanism: str = "MATCHED_ATTRIBUTION_UNAVAILABLE",
) -> str:
    if not identity_valid or fstar_disposition == "POSTSTEP_IDENTITY_INVALID":
        outcome = "LF8_POSTSTEP_IDENTITY_INVALID"
    elif fstar_disposition == "NO_FEASIBLE_FIRST_BLOCK":
        outcome = "LF8_NO_FEASIBLE_FIRST_BLOCK"
    elif fstar_disposition == "FILTER_STALLED_WITH_VALID_PREFIX":
        outcome = "LF8_FILTER_STALLED_WITH_VALID_PREFIX"
    elif fstar_disposition != "COMPLETE":
        outcome = "LF8_POSTSTEP_IDENTITY_INVALID"
    elif not safety:
        outcome = "LF8_SAFETY_PATH_STRICT_OR_LOCAL_FAILED"
    elif not physics:
        outcome = "LF8_FULL_SAFETY_PATH_PHYSICS_GATE_MISSED"
    elif not strict or not local:
        outcome = "LF8_SAFETY_PATH_STRICT_OR_LOCAL_FAILED"
    elif mechanism == "SCHEDULE_SUFFICIENT_FILTER_NOT_LOAD_BEARING":
        outcome = "LF8_SCHEDULE_SUFFICIENT_FILTER_NOT_LOAD_BEARING"
    elif not direct:
        outcome = "LF8_FILTER_LOAD_BEARING_DIRECT_BASELINE_GAP"
    else:
        outcome = "LF8_PROVISIONAL_SINGLE_SEED_DENSE_SIGNAL"
    if outcome not in decision["machine_outcomes_and_unique_next"]:
        raise ValueError(f"unmapped LF8 outcome: {outcome}")
    return outcome


def _verify_shutdown_proof(path: Path) -> dict[str, Any]:
    payload = _read_json(Path(path).resolve())
    pre, post, ordering = (
        payload.get("pre_shutdown", {}),
        payload.get("post_shutdown", {}),
        payload.get("ordering", {}),
    )
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
        raise PermissionError("LF8 local evaluation requires verified recovery and shutdown")
    return payload


def _artifact_path(
    root: Path, summary: Mapping[str, Any], key: str, *, required: bool = True
) -> Path | None:
    record = summary.get("artifacts", {}).get(key)
    if record is None and not required:
        return None
    if not isinstance(record, Mapping):
        raise ValueError(f"LF8 recovered artifact missing: {key}")
    relative = Path(str(record.get("path", "")))
    if relative.is_absolute() or ".." in relative.parts:
        raise PermissionError(f"LF8 artifact escaped run root: {key}")
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise PermissionError(f"LF8 artifact escaped run root: {key}") from exc
    if (
        not path.is_file()
        or path.stat().st_size != int(record.get("size_bytes", -1))
        or _sha256_path(path) != str(record.get("sha256", "")).upper()
    ):
        raise ValueError(f"LF8 recovered artifact drift: {key}")
    return path


def _bound_input(record: Mapping[str, Any], path_key: str, sha_key: str) -> Path:
    path = (ROOT / str(record[path_key])).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PermissionError("LF8 input escaped repository") from exc
    if not path.is_file() or _sha256_path(path) != str(record[sha_key]).upper():
        raise ValueError("LF8 frozen input binding drift")
    return path


def _run_files(
    run_directory: Path, contracts: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    root = Path(run_directory).resolve()
    summary_path = root / "run_summary.json"
    summary = _read_json(summary_path)
    arms = summary.get("arms", {})
    allowed = {P0_FSTAR, P0_C}
    if (
        summary.get("schema_id") != "phk-v23-lf8-reference-blind-run-summary-v1"
        or summary.get("task_id") != TASK_ID
        or summary.get("status")
        not in {"LF8_REFERENCE_BLIND_GPU_CAMPAIGN_COMPLETE", "LF8_POSTSTEP_IDENTITY_INVALID"}
        or P0_FSTAR not in arms
        or not set(arms).issubset(allowed)
        or summary.get("medium_gradient_used") is not False
        or summary.get("runtime_sampling_used") is not False
        or summary.get("fine_extra_lf_only_evaluator_stress_read") is not False
        or int(arms[P0_FSTAR].get("attempted_updates", -1)) > MAX_FILTER_ATTEMPTED_UPDATES
    ):
        raise ValueError("LF8 recovered run identity drift")
    files: dict[str, Any] = {
        "root": root,
        "summary": summary_path,
        "summary_payload": summary,
        "checkpoints": {},
        "predictions": {},
    }
    for role, arm in arms.items():
        for name in ("telemetry.jsonl", "batch_ledger.jsonl", "gate.json", "exit.json"):
            _artifact_path(root, summary, f"{role}:{name}")
        valid = arm.get("endpoint_valid") is True
        checkpoint = _artifact_path(root, summary, f"{role}:checkpoint.pt", required=valid)
        prediction = _artifact_path(root, summary, f"{role}:prediction.npz", required=valid)
        if checkpoint is not None:
            files["checkpoints"][role] = checkpoint
        if prediction is not None:
            files["predictions"][role] = prediction
    initial = contracts["data"]["initial_DEV_R"]
    files["checkpoints"][DEV_R_ROLE] = _bound_input(
        initial, "checkpoint_path", "checkpoint_sha256"
    )
    files["predictions"][DEV_R_ROLE] = _bound_input(
        initial, "prediction_path", "prediction_sha256"
    )
    return files


def _fixed_physics(
    checkpoints: Mapping[str, Path],
    contracts: Mapping[str, Mapping[str, Any]],
    qualification: Mapping[str, Any],
) -> dict[str, Any]:
    ledger = MaterializedPhysicsLedger(
        ROOT / contracts["data"]["materialized_ledger"]["path"],
        contracts=contracts,
        qualification=qualification,
    )
    values: dict[str, float] = {}
    components: dict[str, Any] = {}
    for role, path in checkpoints.items():
        model, config, _ = _load_model(path, device=torch.device("cpu"))
        with torch.enable_grad():
            _, scalars = _physics_objective(
                model, ledger.fixed_batch(device=torch.device("cpu")), config
            )
        values[role] = float(scalars["physics_total"])
        components[role] = scalars
    if not math.isclose(values[DEV_R_ROLE], EXPECTED_J0, rel_tol=1e-10, abs_tol=1e-12):
        raise ValueError("LF8 DEV-R fixed-blind objective drift")
    return {
        "fixed_pool_sha256": EXPECTED_FIXED_POOL_SHA256,
        "values": values,
        "components": components,
        "ratios_to_DEV_R": {
            role: safe_error_ratio(value, values[DEV_R_ROLE])[0]
            for role, value in values.items()
            if role != DEV_R_ROLE
        },
        "source": "CPU_POST_SHUTDOWN_PREMATERIALIZED_LEDGER",
    }


def adjudicate(
    *,
    contract: Mapping[str, Any],
    run: Mapping[str, Any],
    evaluations: Mapping[str, Mapping[str, Any]],
    potential: Mapping[str, Mapping[str, Any]],
    comparisons: Mapping[str, Mapping[str, Any]],
    physics: Mapping[str, Any],
    baseline_medium: Mapping[str, Any],
    medium_audits: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    enriched: dict[str, dict[str, Any]] = {}
    levels: dict[str, dict[str, bool]] = {}
    for role, raw in run["arms"].items():
        arm = dict(raw)
        endpoint_valid = bool(
            raw.get("endpoint_valid") is True
            and role in evaluations
            and _evaluation_valid(evaluations[role])
            and potential.get(role, {}).get("passed") is True
        )
        medium = (medium_audits or {}).get(role)
        if not isinstance(medium, Mapping) and role == P0_FSTAR:
            medium = raw.get("final_audit", {}).get("medium")
        if not isinstance(medium, Mapping):
            safety = raw.get("safety_gate", {})
            strict = raw.get("strict_gate", {})
        else:
            safety = competence_gate(medium, baseline_medium)
            strict = competence_gate(medium, baseline_medium, strict_timing=True)
        arm["endpoint_valid"] = endpoint_valid
        arm["safety_gate"] = safety
        arm["strict_gate"] = strict
        enriched[role] = arm
        ratio = physics["ratios_to_DEV_R"].get(role, math.inf)
        within = comparisons.get(f"{role}_vs_DEV_R", {})
        direct = comparisons.get(f"{role}_vs_LF_ONLY", {})
        levels[role] = evidence_levels(
            accepted_updates=int(raw.get("accepted_updates", -1)),
            endpoint_valid=endpoint_valid,
            safety_passed=safety.get("passed") is True,
            strict_passed=strict.get("passed") is True,
            fixed_blind_ratio=float(ratio),
            local_noninferiority=bool(
                within.get("phase_noninferiority_passed") is True
                and within.get("preservation_passed") is True
            ),
            direct_noninferiority=bool(
                direct.get("phase_noninferiority_passed") is True
                and direct.get("preservation_passed") is True
            ),
        )
    fstar = enriched[P0_FSTAR]
    mechanism = matched_schedule_outcome(enriched)
    fstar_levels = levels[P0_FSTAR]
    outcome = terminal_outcome(
        contract,
        fstar_disposition=str(fstar.get("disposition", "")),
        identity_valid=bool(
            fstar.get("endpoint_valid") is True
            and all(arm.get("endpoint_valid") is True for arm in enriched.values())
        ),
        safety=fstar.get("safety_gate", {}).get("passed") is True,
        physics=fstar_levels["complete_safety_path"]
        and float(physics["ratios_to_DEV_R"].get(P0_FSTAR, math.inf)) <= 0.50,
        strict=fstar.get("strict_gate", {}).get("passed") is True,
        local=fstar_levels["single_seed_pinn_pareto"],
        direct=fstar_levels["dense_paper_value"],
        mechanism=mechanism,
    )
    candidate = None
    if outcome == "LF8_PROVISIONAL_SINGLE_SEED_DENSE_SIGNAL":
        candidate = P0_C if levels.get(P0_C, {}).get("dense_paper_value") else P0_FSTAR
    return {
        "status": "TERMINAL",
        "outcome": outcome,
        "candidate": candidate,
        "unique_next": contract["machine_outcomes_and_unique_next"][outcome],
        "next_research_execution_authorized": False,
        "mechanism_outcome": mechanism,
        "arm_levels": levels,
        "post_shutdown_arm_gates": enriched,
    }


def evaluate_lf8_campaign(
    *,
    output_directory: Path,
    run_directory: Path,
    cpu_qualification_path: Path,
    shutdown_proof_path: Path,
    case_control: str = "FULL",
) -> dict[str, Any]:
    if case_control != PhkControl.FULL.value:
        raise PermissionError("LF8 evaluation is nominal-only")
    shutdown = _verify_shutdown_proof(shutdown_proof_path)
    contracts = load_contracts()
    qualification = read_cpu_qualification(cpu_qualification_path)
    for name, binding in contracts["data"]["local_evaluation_only"].items():
        if isinstance(binding, Mapping) and "path" in binding:
            _safe_bound_path(binding, label=f"LF8 local {name}")
    files = _run_files(run_directory, contracts)
    run = files["summary_payload"]
    lf3_decision = _read_json(
        ROOT / "configs/phk_v23/decision_contract_lf3_phase_latent_carrier.json"
    )
    inherited = _inherited_prediction_paths(lf3_decision)
    direct_path = inherited[LF_ONLY_ROLE]
    if _sha256_path(direct_path) != contracts["data"]["local_evaluation_only"]["direct_LF_ONLY_prediction_sha256"]:
        raise ValueError("LF8 direct LF_ONLY binding drift")
    paths = {DEV_R_ROLE: files["predictions"][DEV_R_ROLE], LF_ONLY_ROLE: direct_path}
    paths.update(files["predictions"])
    evaluations = {
        role: evaluate_prediction(prediction_path=path, control=PhkControl.FULL)
        for role, path in paths.items()
    }
    potential = {
        role: _prediction_potential_guard(path, absolute_tolerance=1e-6)
        for role, path in paths.items()
    }
    if not _evaluation_valid(evaluations[DEV_R_ROLE]) or not _evaluation_valid(evaluations[LF_ONLY_ROLE]):
        raise ValueError("LF8 frozen comparator evaluation invalid")
    floors = _component_floors(lf3_decision)
    comparisons: dict[str, Any] = {}
    for role in (P0_FSTAR, P0_C):
        if role not in evaluations:
            continue
        comparisons[f"{role}_vs_DEV_R"] = compare_b_to_comparator(
            evaluations[role], evaluations[DEV_R_ROLE], component_floors=floors
        )
        comparisons[f"{role}_vs_LF_ONLY"] = compare_b_to_comparator(
            evaluations[role], evaluations[LF_ONLY_ROLE], component_floors=floors
        )
    physics = _fixed_physics(files["checkpoints"], contracts, qualification)
    medium_path = _bound_input(
        contracts["data"]["training_source"], "path", "sha256"
    )
    medium_physics, _, _ = load_case_physics("FULL")
    dataset = load_medium_dataset(medium_path, physics=medium_physics, contracts=contracts)
    medium_audits: dict[str, Mapping[str, Any]] = {}
    for role in (P0_FSTAR, P0_C):
        if role not in files["checkpoints"]:
            continue
        model, _, _ = _load_model(files["checkpoints"][role], device=torch.device("cpu"))
        medium_audits[role] = full_medium_audit(
            model, dataset, device=torch.device("cpu")
        )
    decision = adjudicate(
        contract=contracts["decision"],
        run=run,
        evaluations=evaluations,
        potential=potential,
        comparisons=comparisons,
        physics=physics,
        baseline_medium=qualification["dev_r_full_medium_audit"],
        medium_audits=medium_audits,
    )
    sanitized, replaced = _sanitize_nonfinite(evaluations)
    report = {
        "schema_id": "phk-v23-lf8-local-adjudication-v1",
        "task_id": TASK_ID,
        "status": "COMPLETE",
        "case_control": case_control,
        "gpu_lifecycle": "SHUTDOWN_VERIFIED",
        "shutdown_proof": {"schema_id": shutdown["schema_id"], "sha256": _sha256_path(Path(shutdown_proof_path).resolve())},
        "run_status": run["status"],
        "evaluations": sanitized,
        "evaluator_nonfinite_diagnostics_represented_as_json_null": replaced,
        "potential_maximum_principle": potential,
        "component_floors": floors,
        "comparisons": comparisons,
        "fixed_physics_objective": physics,
        "post_shutdown_full_medium_audits": medium_audits,
        "decision": decision,
        "claim_boundary": contracts["decision"].get("claim_boundary", {}),
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
    report = evaluate_lf8_campaign(
        output_directory=args.output_directory,
        run_directory=args.run_directory,
        cpu_qualification_path=args.cpu_qualification,
        shutdown_proof_path=args.shutdown_proof,
    )
    print(json.dumps(report["decision"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DEV_R_ROLE",
    "SHUTDOWN_PROOF_SCHEMA",
    "adjudicate",
    "evidence_levels",
    "evaluate_lf8_campaign",
    "matched_schedule_outcome",
    "terminal_outcome",
]
