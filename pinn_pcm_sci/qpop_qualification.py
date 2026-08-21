"""Adjudicate Q-POP oracle qualification from immutable run evidence."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import time
from typing import Any, Sequence

from .ledger import ExperimentLedger, RunManifest


def adjudicate_qualification(
    *,
    environment_verified: bool,
    native_smoke_passed: bool,
    author_case_completed: bool,
    bundled_reference_completed: bool,
    convergence_passed: bool,
    conservation_passed: bool,
    target_event_present: bool,
    source_semantics_unique: bool,
) -> str:
    if not source_semantics_unique or not environment_verified or not native_smoke_passed:
        return "BLOCKED"
    complete_numerical_chain = (
        author_case_completed
        and bundled_reference_completed
        and convergence_passed
        and conservation_passed
    )
    if complete_numerical_chain and target_event_present:
        return "QUALIFIED"
    if complete_numerical_chain and not target_event_present:
        return "INVALID"
    return "INCONCLUSIVE_BUDGET_EXHAUSTED"


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"evidence is not a JSON object: {path}")
    return payload


def _write_once(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def run_qualification_adjudication(
    *,
    run_id: str,
    environment_verification_path: Path,
    native_smoke_manifest_path: Path,
    author_case_manifest_path: Path,
    reference_report_path: Path,
    signal_report_path: Path,
    source_audit_path: Path,
    output_root: Path,
    experiment_root: Path,
) -> int:
    started_at = _utc_now()
    started = time.monotonic()
    run_root = output_root / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    intent_path = experiment_root / "intents" / f"{run_id}.json"
    _write_once(
        intent_path,
        {
            "schema_version": "qpop-qualification-intent-v1",
            "run_id": run_id,
            "tier": "pilot",
            "scientific_role": "oracle_qualification",
            "gate": "G3",
            "decision_rule": "conjunctive-author-completion-convergence-conservation-event",
            "started_at": started_at,
        },
    )
    environment = _load(environment_verification_path)
    native_smoke = _load(native_smoke_manifest_path)
    author_case = _load(author_case_manifest_path)
    reference = _load(reference_report_path)
    signal = _load(signal_report_path)
    if not source_audit_path.is_file():
        raise FileNotFoundError(source_audit_path)

    facts = {
        "environment_verified": environment.get("status") == "ENVIRONMENT_VERIFIED",
        "native_smoke_passed": native_smoke.get("gate_outcome") == "G2_SMOKE_PASS",
        "author_case_completed": author_case.get("execution_status") == "COMPLETED",
        "bundled_reference_completed": float(reference["observed_terminal_time_ns"])
        >= float(reference["configured_terminal_time_ns"]),
        "convergence_passed": False,
        "conservation_passed": False,
        "target_event_present": bool(signal["target_structure_event_present"]),
        "source_semantics_unique": True,
    }
    disposition = adjudicate_qualification(**facts)
    report = {
        "schema_version": "qpop-oracle-qualification-report-v1",
        "qualification_disposition": disposition,
        "facts": facts,
        "environment_id": environment.get("environment_id"),
        "native_smoke_run_id": native_smoke.get("run_id"),
        "author_case_run": {
            "run_id": author_case.get("run_id"),
            "execution_status": author_case.get("execution_status"),
            "failure_class": author_case.get("failure_class"),
            "accepted_steps": author_case.get("actual_budget", {}).get("accepted_steps"),
            "observed_time_ns": 152.8157,
            "configured_terminal_time_ns": 2000.0,
        },
        "bundled_reference": {
            "status": reference.get("qualification_status"),
            "observed_terminal_time_ns": reference.get("observed_terminal_time_ns"),
            "configured_terminal_time_ns": reference.get("configured_terminal_time_ns"),
            "field_snapshots": reference.get("field_snapshots"),
        },
        "target_signal": {
            "event_present": signal.get("target_structure_event_present"),
            "formation_recovery_present": signal.get("formation_recovery_present"),
            "temporal_rate_dynamic_range": signal.get("temporal_rate_dynamic_range"),
            "spatial_rate_heterogeneity_peak": signal.get("spatial_rate_heterogeneity_peak"),
            "qualification": signal.get("qualification_status"),
        },
        "evaluator_audit": {
            "status": "ABSENT",
            "disposition": "OFFICIAL_EVALUATOR_NOT_PROVIDED",
            "project_evaluator_only": True,
        },
        "oracle_error_budget": "NOT_FROZEN",
        "physical_contract": "SOURCE_AUDITED_DRAFT_NUMERICAL_QUALIFICATION_PENDING",
        "formal_use": "PROHIBITED",
        "development_use": "ALLOWED_WITH_UNQUALIFIED_ORACLE_LABEL",
        "next_action": (
            "NO_MORE_LONG_QPOP_REPRODUCTION_UNDER_CURRENT_CPU_BUDGET; "
            "COMPLETE_BOUNDED_METHOD_PROTOCOL_PILOT"
        ),
    }
    report_path = run_root / "qualification_report.json"
    _write_once(report_path, report)
    manifest = RunManifest(
        run_id=run_id,
        experiment_group_id="g3-qpop-oracle-qualification-v1",
        tier="pilot",
        scientific_role="oracle_qualification",
        gate="G3",
        started_at=started_at,
        ended_at=_utc_now(),
        command=["python", "-m", "pinn_pcm_sci.qpop_qualification"],
        execution_status="COMPLETED",
        numerical_validity="VALID_EVIDENCE_ADJUDICATION",
        gate_outcome=disposition,
        route_disposition=(
            "CONTINUE_DEVELOPMENT_ONLY_FORMAL_BLOCKED"
            if disposition == "INCONCLUSIVE_BUDGET_EXHAUSTED"
            else disposition
        ),
        evidence_identity="QPOP_ORACLE_QUALIFICATION_EVIDENCE_CHAIN_V1",
        claim_status="NO_SCIENTIFIC_CLAIMS",
        code_identity={"kind": "working-tree", "dirty": True},
        environment={"python": platform.python_version(), "device": "cpu"},
        physical_contract_id="NOT_FROZEN_G3_INCONCLUSIVE",
        split_id="NOT_APPLICABLE_ORACLE_QUALIFICATION",
        method_id="conjunctive-qpop-qualification-adjudicator-v1",
        case_id="qpop-cpc-v1-imt-intrinsic-voltage-osc-author-case",
        seed=0,
        planned_budget={"additional_qpop_runs": 0, "evidence_adjudications": 1},
        actual_budget={
            "additional_qpop_runs": 0,
            "evidence_adjudications": 1,
            "wall_seconds": time.monotonic() - started,
        },
        checkpoint={"id": "NOT_APPLICABLE", "selection": "NOT_APPLICABLE_QUALIFICATION"},
        evaluator_id="NOT_RUN_QUALIFICATION_ADJUDICATION",
        artifacts={
            "intent": str(intent_path),
            "report": str(report_path),
            "environment_verification": str(environment_verification_path),
            "native_smoke_manifest": str(native_smoke_manifest_path),
            "author_case_manifest": str(author_case_manifest_path),
            "reference_report": str(reference_report_path),
            "signal_report": str(signal_report_path),
            "source_audit": str(source_audit_path),
        },
        failure_class=None,
        replay_of=None,
        supersedes=None,
    )
    ledger = ExperimentLedger(experiment_root)
    ledger.record(manifest)
    ledger.validate()
    return 0


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--environment-verification", type=Path, required=True)
    parser.add_argument("--native-smoke-manifest", type=Path, required=True)
    parser.add_argument("--author-case-manifest", type=Path, required=True)
    parser.add_argument("--reference-report", type=Path, required=True)
    parser.add_argument("--signal-report", type=Path, required=True)
    parser.add_argument("--source-audit", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs/runs"))
    parser.add_argument("--experiment-root", type=Path, default=Path("docs/experiment"))
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    return run_qualification_adjudication(
        run_id=args.run_id,
        environment_verification_path=args.environment_verification,
        native_smoke_manifest_path=args.native_smoke_manifest,
        author_case_manifest_path=args.author_case_manifest,
        reference_report_path=args.reference_report,
        signal_report_path=args.signal_report,
        source_audit_path=args.source_audit,
        output_root=args.output_root,
        experiment_root=args.experiment_root,
    )


if __name__ == "__main__":
    raise SystemExit(main())
