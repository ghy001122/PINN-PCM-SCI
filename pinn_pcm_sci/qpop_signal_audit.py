"""Development-only signal audit for a Q-POP structural trajectory."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import time
from typing import Any, Sequence

import numpy as np

from .artifacts import CaseArtifact
from .ledger import ExperimentLedger, RunManifest


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _write_json_once(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def audit_structural_signal(artifact: CaseArtifact) -> dict[str, Any]:
    if "eta" not in artifact.fields:
        raise ValueError("structural signal audit requires the eta field")
    eta = np.asarray(artifact.fields["eta"], dtype=np.float64)
    time_axis = np.asarray(artifact.field_time, dtype=np.float64)
    if eta.ndim != 2 or eta.shape[0] != time_axis.size or eta.shape[0] < 3:
        raise ValueError("eta trajectory must contain at least three aligned snapshots")
    if not np.isfinite(eta).all() or not np.isfinite(time_axis).all():
        raise ValueError("structural trajectory contains non-finite values")
    delta_time = np.diff(time_axis)
    if np.any(delta_time <= 0.0):
        raise ValueError("field time must increase strictly")
    local_rate = np.abs(np.diff(eta, axis=0)) / delta_time[:, None]
    temporal_activity = np.mean(local_rate, axis=1)
    positive_activity = temporal_activity[temporal_activity > np.finfo(np.float64).tiny]
    if positive_activity.size < 2:
        temporal_dynamic_range = 1.0
    else:
        low = float(np.percentile(positive_activity, 10.0))
        high = float(np.percentile(positive_activity, 90.0))
        temporal_dynamic_range = high / max(low, np.finfo(np.float64).tiny)
    spatial_cv = np.std(local_rate, axis=1) / np.maximum(
        np.mean(local_rate, axis=1), np.finfo(np.float64).tiny
    )

    initial_scale = float(np.median(np.abs(eta[0])))
    phase_threshold = 0.5 * initial_scale
    structural_phase_fraction = np.mean(np.abs(eta) >= phase_threshold, axis=1)
    minimum_index = int(np.argmin(structural_phase_fraction))
    formation_drop = float(structural_phase_fraction[0] - structural_phase_fraction[minimum_index])
    recovery_rise = float(
        np.max(structural_phase_fraction[minimum_index:])
        - structural_phase_fraction[minimum_index]
    )
    formation_present = formation_drop >= 0.2
    recovery_present = recovery_rise >= 0.2
    eta_excursion = float(np.max(np.abs(eta - eta[0:1])))
    target_event = bool(formation_present and eta_excursion >= 0.25 * max(initial_scale, 1e-12))

    circuit_ranges = {
        name: float(np.max(values) - np.min(values))
        for name, values in artifact.circuit.items()
    }
    return {
        "schema_version": "qpop-structural-signal-audit-v1",
        "case_id": artifact.case_id,
        "evidence_identity": artifact.evidence_identity,
        "field_snapshots": int(time_axis.size),
        "observed_time_window": [float(time_axis[0]), float(time_axis[-1])],
        "eta_initial_scale": initial_scale,
        "eta_peak_excursion": eta_excursion,
        "phase_threshold": phase_threshold,
        "phase_fraction_initial": float(structural_phase_fraction[0]),
        "phase_fraction_minimum": float(structural_phase_fraction[minimum_index]),
        "phase_fraction_final": float(structural_phase_fraction[-1]),
        "formation_drop": formation_drop,
        "recovery_rise": recovery_rise,
        "target_structure_event_present": target_event,
        "formation_recovery_present": bool(formation_present and recovery_present),
        "temporal_rate_dynamic_range": float(temporal_dynamic_range),
        "spatial_rate_heterogeneity_peak": float(np.max(spatial_cv)),
        "circuit_channel_ranges": circuit_ranges,
        "clock_signal_present": bool(
            target_event
            and temporal_dynamic_range > 1.25
            and float(np.max(spatial_cv)) > 0.1
        ),
        "qualification_status": "DEVELOPMENT_SIGNAL_ONLY_ORACLE_QUALIFICATION_REQUIRED",
    }


def run_signal_audit(
    *, run_id: str, artifact_path: Path, output_root: Path, experiment_root: Path
) -> int:
    started_at = _utc_now()
    started = time.monotonic()
    run_root = output_root / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    intent_path = experiment_root / "intents" / f"{run_id}.json"
    _write_json_once(
        intent_path,
        {
            "schema_version": "qpop-signal-audit-intent-v1",
            "run_id": run_id,
            "tier": "pilot",
            "scientific_role": "bottleneck_audit",
            "gate": "G5",
            "claim_status": "NO_SCIENTIFIC_CLAIMS_UNQUALIFIED_ORACLE",
            "started_at": started_at,
        },
    )
    artifact = CaseArtifact.read(artifact_path)
    report = audit_structural_signal(artifact)
    report_path = run_root / "signal_audit.json"
    _write_json_once(report_path, report)
    signal_present = bool(report["clock_signal_present"])
    manifest = RunManifest(
        run_id=run_id,
        experiment_group_id="g5-qpop-development-signal-audit-v1",
        tier="pilot",
        scientific_role="bottleneck_audit",
        gate="G5",
        started_at=started_at,
        ended_at=_utc_now(),
        command=["python", "-m", "pinn_pcm_sci.qpop_signal_audit"],
        execution_status="COMPLETED",
        numerical_validity="VALID_DEVELOPMENT_DIAGNOSTIC",
        gate_outcome=(
            "DEVELOPMENT_CLOCK_SIGNAL_PRESENT"
            if signal_present
            else "DEVELOPMENT_CLOCK_SIGNAL_NOT_DETECTED"
        ),
        route_disposition=(
            "CONTINUE_METHOD_DEVELOPMENT_ONLY"
            if signal_present
            else "PAUSE_KC_PENDING_QUALIFIED_ORACLE"
        ),
        evidence_identity=artifact.evidence_identity,
        claim_status="NO_SCIENTIFIC_CLAIMS_UNQUALIFIED_ORACLE",
        code_identity={"kind": "working-tree", "dirty": True},
        environment={"python": platform.python_version(), "device": "cpu"},
        physical_contract_id=artifact.physical_contract_id,
        split_id="DEVELOPMENT_ONLY_NO_FORMAL_SPLIT",
        method_id="qpop-structural-signal-audit-v1",
        case_id=artifact.case_id,
        seed=0,
        planned_budget={"case_artifacts": 1, "model_updates": 0},
        actual_budget={
            "case_artifacts": 1,
            "model_updates": 0,
            "wall_seconds": time.monotonic() - started,
        },
        checkpoint={"id": "NOT_APPLICABLE", "selection": "NOT_APPLICABLE_AUDIT"},
        evaluator_id="frozen-project-qpop-signal-audit-v1",
        artifacts={
            "intent": str(intent_path),
            "source_case": str(artifact_path),
            "report": str(report_path),
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
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs/runs"))
    parser.add_argument("--experiment-root", type=Path, default=Path("docs/experiment"))
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    return run_signal_audit(
        run_id=args.run_id,
        artifact_path=args.artifact,
        output_root=args.output_root,
        experiment_root=args.experiment_root,
    )


if __name__ == "__main__":
    raise SystemExit(main())
