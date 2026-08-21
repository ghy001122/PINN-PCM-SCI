"""Strict import of the CPC-bundled, historical Q-POP reference output.

This path is intentionally separate from the native-run converter.  The CPC
archive contains a 10-column historical log without a completion trailer and
ends before the configured 2000 ns terminal time.  It is therefore useful only
as an explicitly unqualified development oracle, never as a successful native
reproduction or an official evaluator result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import time
from typing import Any, Sequence

import numpy as np

from .artifacts import CaseArtifact
from .ledger import ExperimentLedger, RunManifest
from .qpop_conversion import _ConversionState, _parse_fields


HISTORICAL_HEADER = (
    "#Step Time Time step Tfail Nfail Other fail Av. EOP norm Av. T (K) "
    "VO2 V drop (V) VO2 R (Ohm)"
)
HISTORICAL_COLUMNS = (
    "step",
    "time",
    "dt",
    "tfail",
    "nfail",
    "otherfail",
    "eop_norm",
    "average_temperature",
    "reported_voltage_drop",
    "reported_resistance",
)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json_once(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def parse_historical_reference_log(path: Path) -> dict[str, np.ndarray]:
    lines = path.read_text(encoding="utf-8").splitlines()
    nonempty = [line for line in lines if line.strip()]
    if not nonempty or " ".join(nonempty[0].split()) != HISTORICAL_HEADER:
        raise ValueError("historical reference log header differs from the frozen profile")
    rows: list[list[float]] = []
    for line in nonempty[1:]:
        tokens = line.split()
        if len(tokens) != len(HISTORICAL_COLUMNS):
            raise ValueError("historical reference log must contain numeric rows only")
        try:
            row = [float(token) for token in tokens]
        except ValueError as exc:
            raise ValueError("historical reference log must contain numeric rows only") from exc
        if not np.isfinite(row).all():
            raise ValueError("historical reference log contains non-finite values")
        rows.append(row)
    if not rows:
        raise ValueError("historical reference log contains no data rows")
    matrix = np.asarray(rows, dtype=np.float64)
    if np.any(np.diff(matrix[:, 0]) != 1.0) or np.any(np.diff(matrix[:, 1]) <= 0.0):
        raise ValueError("historical reference steps and times must increase strictly")
    return {name: matrix[:, index] for index, name in enumerate(HISTORICAL_COLUMNS)}


def import_cpc_reference(
    *, reference_root: Path, spec_path: Path, artifact_path: Path, report_path: Path
) -> dict[str, Any]:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if spec.get("schema_version") != "qpop-reference-import-spec-v1":
        raise ValueError("unsupported Q-POP reference import spec")
    reference_root = reference_root.resolve()
    input_path = reference_root / str(spec["input_path"])
    log_path = reference_root / str(spec["log_path"])
    if _sha256(input_path) != spec["input_sha256"]:
        raise ValueError("CPC reference input hash mismatch")
    if _sha256(log_path) != spec["log_sha256"]:
        raise ValueError("CPC historical log hash mismatch")

    state = _ConversionState(reference_root)
    state.consume(input_path)
    state.consume(log_path)
    field_time, nodes, cells, fields, field_units, registry = _parse_fields(spec, state)
    log = parse_historical_reference_log(log_path)
    expected = spec["expected_observed_extent"]
    if int(log["step"][-1]) != int(expected["last_step"]):
        raise ValueError("CPC historical log last step differs from the frozen extent")
    if not np.isclose(log["time"][-1], float(expected["last_time_ns"]), rtol=0.0, atol=5e-5):
        raise ValueError("CPC historical log last time differs from the frozen extent")
    if field_time.size != int(expected["field_snapshots"]):
        raise ValueError("CPC reference field snapshot count differs from the frozen extent")
    if field_time[-1] >= float(spec["configured_terminal_time_ns"]):
        raise ValueError("historical reference unexpectedly claims the configured terminal time")

    artifact = CaseArtifact(
        case_id=str(spec["case_id"]),
        physical_contract_id=str(spec["physical_contract_id"]),
        evidence_identity=str(spec["evidence_identity"]),
        nodes=nodes,
        cells=cells,
        mesh_unit=str(spec["mesh"]["coordinate_unit"]),
        field_time=field_time,
        circuit_time=log["time"],
        time_unit="ns",
        fields=fields,
        field_units=field_units,
        field_registry=registry,
        breakpoints=np.asarray(spec["protocol_breakpoints"], dtype=np.float64),
        circuit={
            "qpop_cpc_v1_reported_voltage_drop": log["reported_voltage_drop"],
            "qpop_cpc_v1_reported_resistance": log["reported_resistance"],
        },
        circuit_units={
            "qpop_cpc_v1_reported_voltage_drop": "V",
            "qpop_cpc_v1_reported_resistance": "Ohm",
        },
    )
    artifact.write(artifact_path)
    CaseArtifact.read(artifact_path)
    report = {
        "schema_version": "qpop-reference-import-report-v1",
        "status": "IMPORTED_UNQUALIFIED_DEVELOPMENT_ORACLE",
        "case_id": artifact.case_id,
        "evidence_identity": artifact.evidence_identity,
        "configured_terminal_time_ns": float(spec["configured_terminal_time_ns"]),
        "observed_terminal_time_ns": float(log["time"][-1]),
        "last_field_time_ns": float(field_time[-1]),
        "field_snapshots": int(field_time.size),
        "circuit_samples": int(log["time"].size),
        "nodes": int(nodes.shape[0]),
        "cells": int(cells.shape[0]),
        "artifact_sha256": _sha256(artifact_path),
        "source_files_consumed": len(state.consumed),
        "source_file_hashes": dict(sorted(state.consumed.items())),
        "qualification_status": "NOT_A_COMPLETE_AUTHOR_CASE_REPRODUCTION",
        "scientific_use": "DEVELOPMENT_ONLY",
    }
    _write_json_once(report_path, report)
    return report


def run_reference_import(
    *,
    run_id: str,
    reference_root: Path,
    spec_path: Path,
    output_root: Path,
    experiment_root: Path,
) -> int:
    started_at = _utc_now()
    started = time.monotonic()
    run_root = output_root / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    intent_path = experiment_root / "intents" / f"{run_id}.json"
    _write_json_once(
        intent_path,
        {
            "schema_version": "qpop-reference-import-intent-v1",
            "run_id": run_id,
            "tier": "smoke",
            "scientific_role": "oracle_qualification",
            "gate": "G3",
            "claim_status": "NO_SCIENTIFIC_CLAIMS",
            "started_at": started_at,
        },
    )
    artifact_path = run_root / "case.h5"
    report_path = run_root / "reference_import_report.json"
    failure: Exception | None = None
    report: dict[str, Any] | None = None
    try:
        report = import_cpc_reference(
            reference_root=reference_root,
            spec_path=spec_path,
            artifact_path=artifact_path,
            report_path=report_path,
        )
    except Exception as exc:  # the run must still enter the immutable ledger
        failure = exc
    manifest = RunManifest(
        run_id=run_id,
        experiment_group_id="g3-qpop-author-reference-import-v1",
        tier="smoke",
        scientific_role="oracle_qualification",
        gate="G3",
        started_at=started_at,
        ended_at=_utc_now(),
        command=["python", "-m", "pinn_pcm_sci.qpop_reference", "import"],
        execution_status="FAILED" if failure else "COMPLETED",
        numerical_validity="NOT_EVALUATED" if failure else "VALID_STATIC_ARTIFACT_IMPORT",
        gate_outcome="G3_REFERENCE_IMPORT_BLOCKED" if failure else "G3_REFERENCE_IMPORT_PASS",
        route_disposition="BLOCKED" if failure else "CONTINUE_DEVELOPMENT_ONLY",
        evidence_identity="QPOP_CPC_V1_BUNDLED_REFERENCE_UNQUALIFIED",
        claim_status="NO_SCIENTIFIC_CLAIMS",
        code_identity={"kind": "working-tree", "dirty": True},
        environment={"python": platform.python_version(), "device": "cpu"},
        physical_contract_id="PROVISIONAL_G3_QPOP_CPC_V1_IMT_CONTRACT",
        split_id="DEVELOPMENT_ONLY_NO_FORMAL_SPLIT",
        method_id="strict-cpc-reference-import-v1",
        case_id="qpop-cpc-v1-imt-intrinsic-voltage-osc-bundled-reference",
        seed=0,
        planned_budget={"qpop_processes": 0, "static_imports": 1},
        actual_budget={
            "qpop_processes": 0,
            "wall_seconds": time.monotonic() - started,
            "field_snapshots": 0 if report is None else report["field_snapshots"],
        },
        checkpoint={"id": "NOT_APPLICABLE", "selection": "NOT_APPLICABLE_IMPORT"},
        evaluator_id="NOT_RUN_REFERENCE_IMPORT",
        artifacts={
            "intent": str(intent_path),
            "run_root": str(run_root),
            "case_artifact": str(artifact_path) if artifact_path.exists() else "NOT_CREATED",
            "report": str(report_path) if report_path.exists() else "NOT_CREATED",
        },
        failure_class=None if failure is None else type(failure).__name__,
        replay_of=None,
        supersedes=None,
    )
    ledger = ExperimentLedger(experiment_root)
    ledger.record(manifest)
    ledger.validate()
    if failure is not None:
        raise failure
    return 0


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs/runs"))
    parser.add_argument("--experiment-root", type=Path, default=Path("docs/experiment"))
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    return run_reference_import(
        run_id=args.run_id,
        reference_root=args.reference_root,
        spec_path=args.spec,
        output_root=args.output_root,
        experiment_root=args.experiment_root,
    )


if __name__ == "__main__":
    raise SystemExit(main())
