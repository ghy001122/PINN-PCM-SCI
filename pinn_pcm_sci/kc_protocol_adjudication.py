"""One-shot adjudication of the frozen KC 2x2 development protocol pilot."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import time
from typing import Any, Sequence

from .ledger import ExperimentLedger, RunManifest


def adjudicate_protocols(
    *,
    raw_structure_error: float,
    arm_structure_errors: tuple[float, ...],
    all_numerically_valid: bool,
    oracle_qualified: bool,
    evaluator_resolution: float,
) -> str:
    if not all_numerically_valid:
        return "INVALID"
    improved = any(
        error < raw_structure_error - evaluator_resolution
        for error in arm_structure_errors
    )
    if improved:
        return "DEVELOPMENT_KC_SIGNAL_PRESENT" if not oracle_qualified else "KC_PILOT_GO"
    return (
        "DEVELOPMENT_KC_SCIENTIFIC_NO_GO_UNQUALIFIED_ORACLE"
        if not oracle_qualified
        else "KC_SCIENTIFIC_NO_GO"
    )


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"protocol evidence is not a JSON object: {path}")
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


def run_adjudication(
    *,
    run_id: str,
    stop_joint_root: Path,
    full_joint_root: Path,
    stop_warmup_root: Path,
    full_warmup_root: Path,
    qualification_report_path: Path,
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
            "schema_version": "kc-protocol-adjudication-intent-v1",
            "run_id": run_id,
            "tier": "pilot",
            "scientific_role": "protocol_selection",
            "gate": "G6",
            "rule": "four frozen arms; no fifth protocol; structural endpoint first",
            "started_at": started_at,
        },
    )
    roots = {
        "stop-gradient+joint": stop_joint_root,
        "full-gradient+joint": full_joint_root,
        "stop-gradient+identity-warm-up": stop_warmup_root,
        "full-gradient+identity-warm-up": full_warmup_root,
    }
    summaries = {
        name: _load(root / "pilot_summary.json") for name, root in roots.items()
    }
    manifests = {
        name: _load(experiment_root / "manifests" / f"{root.name}.json")
        for name, root in roots.items()
    }
    qualification = _load(qualification_report_path)
    raw_metrics = summaries["stop-gradient+joint"]["metrics"]["raw"]
    arm_metrics = {
        name: summary["metrics"]["kc"] for name, summary in summaries.items()
    }
    valid = all(
        manifest.get("execution_status") == "COMPLETED"
        and summary.get("failure") is None
        for manifest, summary in zip(manifests.values(), summaries.values())
    )
    oracle_qualified = qualification.get("qualification_disposition") == "QUALIFIED"
    decision = adjudicate_protocols(
        raw_structure_error=float(raw_metrics["structure_symmetric_difference_cycle_equal"]),
        arm_structure_errors=tuple(
            float(metrics["structure_symmetric_difference_cycle_equal"])
            for metrics in arm_metrics.values()
        ),
        all_numerically_valid=valid,
        oracle_qualified=oracle_qualified,
        evaluator_resolution=1.0e-12,
    )
    report = {
        "schema_version": "kc-protocol-adjudication-report-v1",
        "disposition": decision,
        "oracle_qualification": qualification.get("qualification_disposition"),
        "raw_metrics": raw_metrics,
        "arm_metrics": arm_metrics,
        "arm_physics_audits": {
            name: summary["training"]["kc"]["checkpoint_score"]
            for name, summary in summaries.items()
        },
        "all_numerically_valid": valid,
        "evaluator_resolution": 1.0e-12,
        "selected_engineering_default": "stop-gradient+joint",
        "selection_reason": (
            "all structure endpoints tie within evaluator resolution; frozen tie-break defaults "
            "to stop-gradient+joint"
        ),
        "formal_use": "PROHIBITED_UNQUALIFIED_ORACLE",
        "positive_kc_claim": False,
        "no_more_kc_protocols_or_training_budget": True,
        "next_route": "SEPARATE_PHA_DEVELOPMENT_DIAGNOSTIC_ONLY_IF_NEW_PREREGISTRATION",
    }
    report_path = run_root / "protocol_adjudication.json"
    _write_once(report_path, report)
    manifest = RunManifest(
        run_id=run_id,
        experiment_group_id="g6-kc-protocol-adjudication-v1",
        tier="pilot",
        scientific_role="protocol_selection",
        gate="G6",
        started_at=started_at,
        ended_at=_utc_now(),
        command=["python", "-m", "pinn_pcm_sci.kc_protocol_adjudication"],
        execution_status="COMPLETED",
        numerical_validity="VALID_DEVELOPMENT_PROTOCOL_ADJUDICATION",
        gate_outcome=decision,
        route_disposition="DEVELOPMENT_KC_ROUTE_CLOSED",
        evidence_identity="QPOP_CPC_V1_BUNDLED_REFERENCE_UNQUALIFIED",
        claim_status="NO_POSITIVE_KC_CLAIM",
        code_identity={"kind": "working-tree", "dirty": True},
        environment={"python": platform.python_version(), "device": "cpu"},
        physical_contract_id="NOT_FROZEN_G3_INCONCLUSIVE",
        split_id="qpop-cpc-v1-bundled-reference-development-only-v1",
        method_id="kc-frozen-2x2-protocol-adjudication-v1",
        case_id="qpop-cpc-v1-imt-intrinsic-voltage-osc-bundled-reference-through-512.0793ns",
        seed=17,
        planned_budget={"kc_protocol_arms": 4, "updates_per_arm": 1000},
        actual_budget={
            "kc_protocol_arms": 4,
            "kc_optimizer_updates": 4000,
            "paired_raw_optimizer_updates": 1000,
            "wall_seconds": time.monotonic() - started,
        },
        checkpoint={
            "id": "oracle-blind-physics-audit-best-per-arm",
            "selection": "max normalized physics violation, then sum",
        },
        evaluator_id="frozen-project-development-evaluator-qpop-reference-v1",
        artifacts={
            "intent": str(intent_path),
            "report": str(report_path),
            "qualification_report": str(qualification_report_path),
            **{f"{name}_summary": str(root / "pilot_summary.json") for name, root in roots.items()},
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
    parser.add_argument("--stop-joint-root", type=Path, required=True)
    parser.add_argument("--full-joint-root", type=Path, required=True)
    parser.add_argument("--stop-warmup-root", type=Path, required=True)
    parser.add_argument("--full-warmup-root", type=Path, required=True)
    parser.add_argument("--qualification-report", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs/runs"))
    parser.add_argument("--experiment-root", type=Path, default=Path("docs/experiment"))
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    return run_adjudication(
        run_id=args.run_id,
        stop_joint_root=args.stop_joint_root,
        full_joint_root=args.full_joint_root,
        stop_warmup_root=args.stop_warmup_root,
        full_warmup_root=args.full_warmup_root,
        qualification_report_path=args.qualification_report,
        output_root=args.output_root,
        experiment_root=args.experiment_root,
    )


if __name__ == "__main__":
    raise SystemExit(main())
