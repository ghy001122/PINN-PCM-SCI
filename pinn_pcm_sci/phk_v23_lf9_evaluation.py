"""Post-shutdown local adjudication for the PHK-V2.3 LF9 campaign."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .phk_benchmark import PhkControl
from .phk_v22r_evaluator import evaluate_prediction
from .phk_v22r_prediction import _load_model
from .phk_v22r_training import ROOT, load_case_physics
from .phk_v23_lf0 import _read_json, _sha256_path
from .phk_v23_lf0_evaluation import _prediction_potential_guard, _sanitize_nonfinite, write_strict_json
from .phk_v23_lf1_evaluation import LF_ONLY_ROLE, _competent, _evaluation_valid, compare_b_to_comparator
from .phk_v23_lf2 import load_medium_dataset
from .phk_v23_lf2_evaluation import _component_floors, _inherited_prediction_paths, _safe_bound_path
from .phk_v23_lf3 import build_training_config, full_medium_audit
from .phk_v23_lf9 import (
    ARM_DIRECTORIES,
    ARM_ORDER,
    CONTROL_DIRECTORY,
    ER_CV,
    ER_S,
    EXPECTED_DEV_R_SHA256,
    EXPECTED_FIXED_POOL_SHA256,
    EXPECTED_PARTITION_SHA256,
    EXPECTED_STRONG_SEMANTIC_SHA256,
    FULL_ACCEPTED_UPDATES,
    FULL_ATTEMPTED_CAP,
    MaterializedCVLedger,
    SCREEN_ATTEMPTED_CAP,
    TASK_ID,
    _runtime_contracts,
    competence_gate,
    fixed_blind_metrics,
    load_contracts,
    read_cpu_qualification,
)
from . import phk_v23_lf7 as lf7


DEV_R_ROLE = "LF6_DEV_R_SAFETY_NEAR_CARRIER"
SELECTED_FULL_ROLE = "LF9_SELECTED_FILTERED_FULL"
CONTROL_ROLE = "LF9_NO_FILTER_CONTROL"
SCREEN_ROLES = {ER_S: "LF9_ER_S_SCREEN", ER_CV: "LF9_ER_CV_SCREEN"}
SHUTDOWN_PROOF_SCHEMA = "phk-v23-lf9-autodl-shutdown-proof-v1"


def _verify_shutdown_proof(path: Path) -> dict[str, Any]:
    payload = _read_json(Path(path).resolve())
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
        raise PermissionError("LF9 local evaluation requires verified recovery and shutdown")
    return payload


def _artifact_path(root: Path, summary: Mapping[str, Any], key: str, *, required: bool = True) -> Path | None:
    record = summary.get("artifacts", {}).get(key)
    if record is None and not required:
        return None
    if not isinstance(record, Mapping):
        raise ValueError(f"LF9 recovered artifact missing: {key}")
    relative = Path(str(record.get("path", "")))
    if relative.is_absolute() or ".." in relative.parts:
        raise PermissionError(f"LF9 recovered artifact escaped run root: {key}")
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise PermissionError(f"LF9 recovered artifact escaped run root: {key}") from exc
    if (
        not path.is_file()
        or path.stat().st_size != int(record.get("size_bytes", -1))
        or _sha256_path(path) != str(record.get("sha256", "")).upper()
    ):
        raise ValueError(f"LF9 recovered artifact drift: {key}")
    return path


def _bound_input(record: Mapping[str, Any], path_key: str, sha_key: str) -> Path:
    path = (ROOT / str(record[path_key])).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PermissionError("LF9 frozen input escaped repository") from exc
    if not path.is_file() or _sha256_path(path) != str(record[sha_key]).upper():
        raise ValueError("LF9 frozen input binding drift")
    return path


def _prediction_checkpoint_sha(path: Path) -> str:
    with np.load(path, allow_pickle=False) as archive:
        raw = archive["metadata_json"]
        text = str(raw.item()) if raw.shape == () else str(raw.reshape(-1)[0])
    return str(json.loads(text)["checkpoint_sha256"]).upper()


def _verify_checkpoint(path: Path, *, summary: Mapping[str, Any], role_prefix: str) -> None:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    metadata = payload.get("lf9", {})
    if (
        payload.get("schema_id") != "phk-v22r-checkpoint-v1-1"
        or metadata.get("schema_id") != "phk-v23-lf9-checkpoint-metadata-v1"
        or metadata.get("task_id") != TASK_ID
        or not str(metadata.get("role", "")).startswith(role_prefix)
        or metadata.get("source_identity") != summary.get("source_identity")
        or metadata.get("parent_checkpoint_sha256") != EXPECTED_DEV_R_SHA256
        or metadata.get("equation_routing_used") is not True
        or metadata.get("medium_gradient_used") is not False
        or metadata.get("runtime_sampling_used") is not False
        or metadata.get("stress_read") is not False
    ):
        raise ValueError(f"LF9 checkpoint provenance drift: {path.name}")


def _run_files(run_directory: Path, contracts: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    root = Path(run_directory).resolve()
    summary_path = root / "run_summary.json"
    summary = _read_json(summary_path)
    arms = summary.get("arms", {})
    if (
        summary.get("schema_id") != "phk-v23-lf9-reference-blind-run-summary-v1"
        or summary.get("task_id") != TASK_ID
        or summary.get("status") not in {"LF9_REFERENCE_BLIND_GPU_CAMPAIGN_COMPLETE", "LF9_POSTSTEP_IDENTITY_INVALID"}
        or set(arms) != set(ARM_ORDER)
        or summary.get("medium_gradient_used") is not False
        or summary.get("runtime_sampling_used") is not False
        or summary.get("fine_extra_lf_only_evaluator_stress_read") is not False
        or any(int(arms[name].get("attempted_updates", 0)) > SCREEN_ATTEMPTED_CAP for name in ARM_ORDER)
        or int(summary.get("full_refinement", {}).get("attempted_updates", 0)) > FULL_ATTEMPTED_CAP
    ):
        raise ValueError("LF9 recovered run identity drift")
    for key in summary.get("artifacts", {}):
        _artifact_path(root, summary, key)
    files: dict[str, Any] = {
        "root": root,
        "summary": summary_path,
        "summary_payload": summary,
        "checkpoints": {},
        "predictions": {},
    }
    for arm in ARM_ORDER:
        directory = ARM_DIRECTORIES[arm]
        checkpoint = _artifact_path(root, summary, f"{directory}/screen-checkpoint.pt", required=arms[arm].get("endpoint_valid") is True)
        prediction = _artifact_path(root, summary, f"{directory}/screen-prediction.npz", required=checkpoint is not None)
        if checkpoint is not None and prediction is not None:
            _verify_checkpoint(checkpoint, summary=summary, role_prefix=f"{arm}:SCREEN")
            if _prediction_checkpoint_sha(prediction) != _sha256_path(checkpoint):
                raise ValueError("LF9 screen prediction/checkpoint binding drift")
            files["checkpoints"][SCREEN_ROLES[arm]] = checkpoint
            files["predictions"][SCREEN_ROLES[arm]] = prediction
    selected = summary.get("selected_arm")
    full = summary.get("full_refinement", {})
    if full.get("executed") and selected in ARM_ORDER and full.get("endpoint_valid"):
        directory = ARM_DIRECTORIES[selected]
        checkpoint = _artifact_path(root, summary, f"{directory}/full-checkpoint.pt")
        prediction = _artifact_path(root, summary, f"{directory}/full-prediction.npz")
        _verify_checkpoint(checkpoint, summary=summary, role_prefix=f"{selected}:FULL")
        if _prediction_checkpoint_sha(prediction) != _sha256_path(checkpoint):
            raise ValueError("LF9 full prediction/checkpoint binding drift")
        files["checkpoints"][SELECTED_FULL_ROLE] = checkpoint
        files["predictions"][SELECTED_FULL_ROLE] = prediction
    control = summary.get("control", {})
    if control.get("executed") and control.get("endpoint_valid"):
        checkpoint = _artifact_path(root, summary, f"{CONTROL_DIRECTORY}/checkpoint.pt")
        prediction = _artifact_path(root, summary, f"{CONTROL_DIRECTORY}/prediction.npz")
        _verify_checkpoint(checkpoint, summary=summary, role_prefix="NO_FILTER_CONTROL")
        if _prediction_checkpoint_sha(prediction) != _sha256_path(checkpoint):
            raise ValueError("LF9 control prediction/checkpoint binding drift")
        files["checkpoints"][CONTROL_ROLE] = checkpoint
        files["predictions"][CONTROL_ROLE] = prediction
    initial = contracts["data"]["initial_DEV_R"]
    files["checkpoints"][DEV_R_ROLE] = _bound_input(initial, "checkpoint_path", "checkpoint_sha256")
    files["predictions"][DEV_R_ROLE] = _bound_input(initial, "prediction_path", "prediction_sha256")
    return files


def _level_for_endpoint(
    *,
    raw: Mapping[str, Any],
    evaluation: Mapping[str, Any] | None,
    potential: Mapping[str, Any] | None,
    medium: Mapping[str, Any] | None,
    baseline_medium: Mapping[str, Any],
    comparison_dev_r: Mapping[str, Any] | None,
    comparison_direct: Mapping[str, Any] | None,
    blind: Mapping[str, float] | None,
    blind_baseline: Mapping[str, float],
    selected_arm: str | None,
) -> dict[str, Any]:
    endpoint_valid = bool(
        raw.get("endpoint_valid") is True
        and isinstance(evaluation, Mapping) and _evaluation_valid(evaluation)
        and isinstance(potential, Mapping) and potential.get("passed") is True
        and isinstance(medium, Mapping)
    )
    safety = competence_gate(medium, baseline_medium) if isinstance(medium, Mapping) else {"passed": False, "failed_checks": ["missing_post_shutdown_medium_audit"]}
    strict = competence_gate(medium, baseline_medium, strict_timing=True) if isinstance(medium, Mapping) else {"passed": False, "failed_checks": ["missing_post_shutdown_medium_audit"]}
    ratios = {
        key: float(blind[key]) / float(blind_baseline[key])
        for key in ("J_S", "J_M", "CV1", "CV4")
    } if isinstance(blind, Mapping) else {key: None for key in ("J_S", "J_M", "CV1", "CV4")}
    own_key = "J_S" if selected_arm == ER_S else "J_M"
    ratios_available = all(isinstance(ratios[key], (int, float)) for key in (own_key, "CV1", "CV4"))
    local_ni = bool(
        isinstance(comparison_dev_r, Mapping)
        and comparison_dev_r.get("phase_noninferiority_passed") is True
        and comparison_dev_r.get("preservation_passed") is True
    )
    direct_value = bool(
        isinstance(comparison_direct, Mapping)
        and comparison_direct.get("phase_noninferiority_passed") is True
        and comparison_direct.get("preservation_passed") is True
        and comparison_direct.get("b_competent") is True
        and isinstance(potential, Mapping) and potential.get("passed") is True
    )
    prelocal = bool(
        int(raw.get("accepted_updates", -1)) == FULL_ACCEPTED_UPDATES
        and safety.get("passed") is True and strict.get("passed") is True
        and ratios_available
        and ratios[own_key] <= 0.50 and ratios["CV1"] <= 0.75 and ratios["CV4"] <= 0.75
    )
    complete = bool(
        endpoint_valid and prelocal and isinstance(evaluation, Mapping)
        and _competent(evaluation) and local_ni
    )
    return {
        "endpoint_valid": endpoint_valid,
        "safety_gate": safety,
        "strict_gate": strict,
        "blind": dict(blind or {}),
        "blind_ratios_to_DEV_R": ratios,
        "prelocal_internal_pareto_recomputed": prelocal,
        "complete_internal_pareto": complete,
        "frozen_evaluator_competent": bool(isinstance(evaluation, Mapping) and _competent(evaluation)),
        "phase_temperature_current_noninferiority": local_ni,
        "direct_paper_value": bool(complete and direct_value),
    }


def terminal_outcome(*, run: Mapping[str, Any], local: Mapping[str, Any]) -> dict[str, Any]:
    """Apply the mutually exclusive LF9 terminal-outcome priority."""

    arms = run.get("arms", {})
    full = dict(run.get("full_refinement", {}))
    control = dict(run.get("control", {}))
    local_full = local.get("full", {}) if isinstance(local, Mapping) else {}
    local_control = local.get("control", {}) if isinstance(local, Mapping) else {}
    full.update(local_full if isinstance(local_full, Mapping) else {})
    control.update(local_control if isinstance(local_control, Mapping) else {})
    if any(arms.get(arm, {}).get("identity_valid") is not True for arm in ARM_ORDER):
        outcome = "LF9_SCREEN_IDENTITY_INVALID"
    elif run.get("mechanism_outcome") == "NO_SAFE_MIXED_FORM_SCREEN" or run.get("selected_arm") not in ARM_ORDER:
        outcome = "LF9_NO_SAFE_MIXED_FORM_SCREEN"
    else:
        disposition = str(full.get("scientific_disposition", full.get("disposition", "")))
        if disposition in {"PHASE_FROZEN_THERMAL_ROUTE_FAILED", "LF9_PHASE_FROZEN_THERMAL_ROUTE_FAILED"}:
            outcome = "LF9_PHASE_FROZEN_THERMAL_ROUTE_FAILED"
        elif disposition in {"PHASE_KINETIC_PRIMARY_BLOCKER", "PHASE_KINETIC_BECOMES_PRIMARY_BLOCKER", "LF9_PHASE_KINETIC_PRIMARY_BLOCKER"}:
            outcome = "LF9_PHASE_KINETIC_PRIMARY_BLOCKER"
        elif full.get("complete_internal_pareto") is not True:
            outcome = "LF9_FULL_PATH_STALLED_OR_PHYSICS_GATE_MISSED"
        elif control.get("executed") is not True:
            outcome = "LF9_RECOVERY_OR_LOCAL_EVALUATION_BLOCKED"
        elif control.get("complete_internal_pareto") is True:
            outcome = "LF9_SCHEDULE_AND_ROUTING_SUFFICIENT"
        elif full.get("direct_paper_value") is True:
            outcome = "LF9_PROVISIONAL_SINGLE_SEED_DENSE_SIGNAL"
        else:
            outcome = "LF9_FILTER_LOAD_BEARING_DIRECT_BASELINE_GAP"
    mapping = load_contracts()["decision"]["machine_outcomes_and_unique_next"]
    if outcome not in mapping:
        raise ValueError(f"unmapped LF9 outcome: {outcome}")
    candidate = run.get("selected_arm") if outcome == "LF9_PROVISIONAL_SINGLE_SEED_DENSE_SIGNAL" else None
    return {
        "machine_outcome": outcome,
        "unique_next": mapping[outcome],
        "candidate": candidate,
        "next_research_execution_authorized": False,
    }


def _local_blind_metrics(
    checkpoints: Mapping[str, Path],
    *,
    contracts: Mapping[str, Mapping[str, Any]],
    qualification: Mapping[str, Any],
) -> dict[str, dict[str, float]]:
    strong = lf7.MaterializedPhysicsLedger(
        ROOT / contracts["data"]["strong_ledger"]["path"],
        contracts=_runtime_contracts(contracts),
        qualification={"ledger": qualification["strong_ledger"]},
    )
    cv = MaterializedCVLedger(
        ROOT / contracts["data"]["cv_ledger"]["path"],
        ROOT / contracts["data"]["cv_ledger"]["manifest_path"],
        contracts=contracts, qualification=qualification,
    )
    config = build_training_config("cpu")
    scale = float(qualification["cv_normalization"]["s_cv"])
    values: dict[str, dict[str, float]] = {}
    for role, path in checkpoints.items():
        model, _, _ = _load_model(path, device=torch.device("cpu"))
        values[role] = fixed_blind_metrics(
            model, strong, cv, config, cv_scale=scale, device=torch.device("cpu")
        )
    baseline = qualification["blind_baseline"]
    for key in ("J_S", "J_M", "CV1", "CV4"):
        if not math.isclose(float(values[DEV_R_ROLE][key]), float(baseline[key]), rel_tol=1e-9, abs_tol=1e-12):
            raise ValueError(f"LF9 DEV-R post-shutdown blind baseline drift: {key}")
    return values


def evaluate_lf9_campaign(
    *,
    output_directory: Path,
    run_directory: Path,
    cpu_qualification_path: Path,
    shutdown_proof_path: Path,
    case_control: str = "FULL",
) -> dict[str, Any]:
    if case_control != PhkControl.FULL.value:
        raise PermissionError("LF9 evaluation is nominal-only")

    # This is deliberately first: reference-bearing inputs remain unread until
    # recovery, zero-process state, shutdown, TCP closure and SSH refusal exist.
    shutdown = _verify_shutdown_proof(shutdown_proof_path)
    contracts = load_contracts()
    qualification = read_cpu_qualification(cpu_qualification_path)
    files = _run_files(run_directory, contracts)
    run = files["summary_payload"]

    for name, binding in contracts["data"]["local_evaluation_only"].items():
        if isinstance(binding, Mapping) and "path" in binding:
            _safe_bound_path(binding, label=f"LF9 local {name}")
    lf3_decision = _read_json(ROOT / "configs/phk_v23/decision_contract_lf3_phase_latent_carrier.json")
    inherited = _inherited_prediction_paths(lf3_decision)
    direct_path = inherited[LF_ONLY_ROLE]
    if _sha256_path(direct_path) != contracts["data"]["local_evaluation_only"]["direct_LF_ONLY_prediction_sha256"]:
        raise ValueError("LF9 direct LF_ONLY prediction binding drift")

    prediction_paths = {DEV_R_ROLE: files["predictions"][DEV_R_ROLE], LF_ONLY_ROLE: direct_path}
    prediction_paths.update(files["predictions"])
    evaluations = {
        role: evaluate_prediction(prediction_path=path, control=PhkControl.FULL)
        for role, path in prediction_paths.items()
    }
    potential = {
        role: _prediction_potential_guard(path, absolute_tolerance=1e-6)
        for role, path in prediction_paths.items()
    }
    if not _evaluation_valid(evaluations[DEV_R_ROLE]) or not _evaluation_valid(evaluations[LF_ONLY_ROLE]):
        raise ValueError("LF9 frozen comparator evaluation invalid")

    floors = _component_floors(lf3_decision)
    comparisons: dict[str, Any] = {}
    for role in (SELECTED_FULL_ROLE, CONTROL_ROLE):
        if role not in evaluations:
            continue
        comparisons[f"{role}_vs_DEV_R"] = compare_b_to_comparator(
            evaluations[role], evaluations[DEV_R_ROLE], component_floors=floors
        )
        comparisons[f"{role}_vs_LF_ONLY"] = compare_b_to_comparator(
            evaluations[role], evaluations[LF_ONLY_ROLE], component_floors=floors
        )

    medium_path = _bound_input(contracts["data"]["training_source"], "path", "sha256")
    medium_physics, _, _ = load_case_physics("FULL")
    dataset = load_medium_dataset(medium_path, physics=medium_physics, contracts=contracts)
    if dataset.partition_sha256 != EXPECTED_PARTITION_SHA256:
        raise ValueError("LF9 post-shutdown medium partition drift")
    medium_audits: dict[str, Mapping[str, Any]] = {}
    for role in (SELECTED_FULL_ROLE, CONTROL_ROLE):
        if role not in files["checkpoints"]:
            continue
        model, _, _ = _load_model(files["checkpoints"][role], device=torch.device("cpu"))
        medium_audits[role] = full_medium_audit(model, dataset, device=torch.device("cpu"))

    blind = _local_blind_metrics(
        files["checkpoints"], contracts=contracts, qualification=qualification
    )
    selected = run.get("selected_arm") if run.get("selected_arm") in ARM_ORDER else None
    full_raw = run.get("full_refinement", {})
    control_raw = run.get("control", {})
    full_level = _level_for_endpoint(
        raw=full_raw,
        evaluation=evaluations.get(SELECTED_FULL_ROLE),
        potential=potential.get(SELECTED_FULL_ROLE),
        medium=medium_audits.get(SELECTED_FULL_ROLE),
        baseline_medium=qualification["dev_r_full_medium_audit"],
        comparison_dev_r=comparisons.get(f"{SELECTED_FULL_ROLE}_vs_DEV_R"),
        comparison_direct=comparisons.get(f"{SELECTED_FULL_ROLE}_vs_LF_ONLY"),
        blind=blind.get(SELECTED_FULL_ROLE),
        blind_baseline=qualification["blind_baseline"],
        selected_arm=selected,
    )
    control_level = _level_for_endpoint(
        raw=control_raw,
        evaluation=evaluations.get(CONTROL_ROLE),
        potential=potential.get(CONTROL_ROLE),
        medium=medium_audits.get(CONTROL_ROLE),
        baseline_medium=qualification["dev_r_full_medium_audit"],
        comparison_dev_r=comparisons.get(f"{CONTROL_ROLE}_vs_DEV_R"),
        comparison_direct=comparisons.get(f"{CONTROL_ROLE}_vs_LF_ONLY"),
        blind=blind.get(CONTROL_ROLE),
        blind_baseline=qualification["blind_baseline"],
        selected_arm=selected,
    )
    local = {
        "full": full_level,
        "control": control_level,
        "cloud_prelocal_claim_consistent": bool(
            not full_raw.get("prelocal_internal_pareto")
            or full_level["prelocal_internal_pareto_recomputed"]
        ),
    }
    decision = terminal_outcome(run=run, local=local)
    decision.update({
        "mechanism_outcome": run.get("mechanism_outcome"),
        "selected_arm": selected,
        "full_complete_internal_pareto": full_level["complete_internal_pareto"],
        "control_complete_internal_pareto": control_level["complete_internal_pareto"],
        "direct_paper_value": full_level["direct_paper_value"],
    })
    sanitized, replaced = _sanitize_nonfinite(evaluations)
    report = {
        "schema_id": "phk-v23-lf9-local-adjudication-v1",
        "task_id": TASK_ID,
        "status": "COMPLETE",
        "case_control": case_control,
        "gpu_lifecycle": "SHUTDOWN_VERIFIED",
        "shutdown_proof": {
            "schema_id": shutdown["schema_id"],
            "sha256": _sha256_path(Path(shutdown_proof_path).resolve()),
        },
        "run_summary_sha256": _sha256_path(files["summary"]),
        "run_status": run["status"],
        "evaluations": sanitized,
        "evaluator_nonfinite_diagnostics_represented_as_json_null": replaced,
        "potential_maximum_principle": potential,
        "component_floors": floors,
        "comparisons": comparisons,
        "post_shutdown_full_medium_audits": medium_audits,
        "post_shutdown_blind_metrics": blind,
        "prelocal_vs_complete_internal_pareto": local,
        "decision": decision,
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
    report = evaluate_lf9_campaign(
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
    "CONTROL_ROLE", "DEV_R_ROLE", "SELECTED_FULL_ROLE",
    "SHUTDOWN_PROOF_SCHEMA", "evaluate_lf9_campaign", "main",
    "terminal_outcome",
]
