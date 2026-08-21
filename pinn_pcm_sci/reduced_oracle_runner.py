"""Bounded smoke and development signal runs for QPOP-R3-v1."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import platform
import time
from typing import Any, Sequence

import numpy as np
import scipy

from .ledger import ExperimentLedger, RunManifest
from .qpop_method_pilot import _utc_now, _write_json_once
from .qpop_physics import QPopParameters
from .reduced_oracle import (
    ReducedOracleCase,
    ReducedOracleGrid,
    ReducedOracleResult,
    reduced_result_to_artifact,
)


SIGNAL_VOLTAGES_V = (7.5, 9.0, 10.5)
SIGNAL_RESISTANCES_OHM = (3.0e5, 5.0e5, 7.0e5)
STRUCTURE_THRESHOLD = 0.5595005728407872


def _event_diagnostics(result: ReducedOracleResult) -> dict[str, Any]:
    fractions = np.mean(result.eta >= STRUCTURE_THRESHOLD, axis=1)
    cycles: list[dict[str, Any]] = []
    for index in range(4):
        start, stop = 120.0 * index, 120.0 * (index + 1)
        selected = (result.time_ns >= start) & (result.time_ns <= stop)
        if np.count_nonzero(selected) < 2:
            continue
        values = fractions[selected]
        cycle_range = float(np.max(values) - np.min(values))
        cycles.append(
            {
                "cycle": index + 1,
                "range": cycle_range,
                "nondegenerate": cycle_range >= 0.02,
            }
        )
    return {
        "phase_fraction_min": float(np.min(fractions)),
        "phase_fraction_max": float(np.max(fractions)),
        "phase_fraction_range": float(np.max(fractions) - np.min(fractions)),
        "nondegenerate_cycle_count": sum(bool(cycle["nondegenerate"]) for cycle in cycles),
        "cycles": cycles,
    }


def _record(
    *,
    run_id: str,
    mode: str,
    started_at: str,
    started: float,
    artifacts: dict[str, str],
    planned_budget: dict[str, Any],
    actual_budget: dict[str, Any],
    outcome: str,
    route: str,
    failure: Exception | None,
    experiment_root: Path,
    supersedes: str | None,
) -> None:
    manifest = RunManifest(
        run_id=run_id,
        experiment_group_id="qpop-r3-v1-reduced-oracle",
        tier="smoke" if mode == "smoke" else "pilot",
        scientific_role="oracle_qualification",
        gate="N3B",
        started_at=started_at,
        ended_at=_utc_now(),
        command=["python", "-m", "pinn_pcm_sci.reduced_oracle_runner", mode],
        execution_status="FAILED" if failure else "COMPLETED",
        numerical_validity="NOT_EVALUATED" if failure else "VALID_REDUCED_ORACLE_NUMERICS",
        gate_outcome=outcome,
        route_disposition=route,
        evidence_identity="QPOP_R3_V1_REDUCED_SYNTHETIC_ORACLE",
        claim_status="NO_SCIENTIFIC_CLAIMS_REDUCED_ORACLE_DEVELOPMENT",
        code_identity={"kind": "working-tree", "dirty": True},
        environment={
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "dtype": "float64",
            "device": "cpu",
        },
        physical_contract_id="qpop-r3-v1",
        split_id="qpop-r3-v1-development-signal-grid-v1",
        method_id=f"qpop-r3-v1-{mode}",
        case_id="qpop-r3-v1-smoke" if mode == "smoke" else "qpop-r3-v1-3x3-signal-grid",
        seed=0,
        planned_budget=planned_budget,
        actual_budget={**actual_budget, "wall_seconds": time.monotonic() - started},
        checkpoint={"id": "NOT_APPLICABLE", "selection": "INDEPENDENT_NUMERICAL_ORACLE"},
        evaluator_id="qpop-r3-v1-event-diagnostic-v1",
        artifacts=artifacts,
        failure_class=None if failure is None else type(failure).__name__,
        replay_of=None,
        supersedes=supersedes,
    )
    ledger = ExperimentLedger(experiment_root)
    ledger.record(manifest)
    ledger.validate()


def run_smoke(
    *,
    run_id: str,
    input_path: Path,
    output_root: Path,
    experiment_root: Path,
    supersedes: str | None = None,
) -> int:
    started_at, started = _utc_now(), time.monotonic()
    run_root = output_root / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    intent_path = experiment_root / "intents" / f"{run_id}.json"
    _write_json_once(
        intent_path,
        {
            "schema_version": "qpop-r3-v1-intent-v1",
            "run_id": run_id,
            "tier": "smoke",
            "scientific_role": "oracle_qualification",
            "gate": "N3B",
            "grid": [6, 4],
            "end_time_ns": 2.0,
            "time_step_ns": 1.0,
            "drive_voltage_v": 0.0,
            "series_resistance_ohm": 5.0e5,
            "started_at": started_at,
            "supersedes": supersedes,
        },
    )
    artifacts = {"intent": str(intent_path), "run_root": str(run_root)}
    failure: Exception | None = None
    summary: dict[str, Any] = {}
    try:
        result = ReducedOracleCase(
            parameters=QPopParameters.from_input(input_path),
            grid=ReducedOracleGrid(6, 4),
            end_time_ns=2.0,
            time_step_ns=1.0,
            drive_voltage_v=0.0,
            series_resistance_ohm=5.0e5,
            save_every=1,
        ).solve()
        artifact = reduced_result_to_artifact(
            result, grid=ReducedOracleGrid(6, 4), case_id="qpop-r3-v1-smoke"
        )
        artifact_path = run_root / "case.h5"
        artifact.write(artifact_path)
        artifact.read(artifact_path)
        summary = {
            "schema_version": "qpop-r3-v1-smoke-summary-v1",
            "max_balance_violation": result.max_balance_violation,
            "finite": bool(
                np.all(np.isfinite(result.eta))
                and np.all(np.isfinite(result.temperature))
            ),
        }
        artifacts["case"] = str(artifact_path)
    except Exception as exc:
        failure = exc
    summary["failure"] = None if failure is None else str(failure)
    summary_path = run_root / "summary.json"
    _write_json_once(summary_path, summary)
    artifacts["summary"] = str(summary_path)
    passed = failure is None and bool(summary.get("finite")) and float(summary.get("max_balance_violation", 1.0)) <= 0.01
    _record(
        run_id=run_id,
        mode="smoke",
        started_at=started_at,
        started=started,
        artifacts=artifacts,
        planned_budget={"cases": 1, "grid": [6, 4], "time_steps": 2},
        actual_budget={"cases": 0 if failure else 1, "time_steps": 0 if failure else 2},
        outcome="QPOP_R3_SMOKE_PASS" if passed else "QPOP_R3_SMOKE_FAILED",
        route="CONTINUE_QPOP_R3_SIGNAL_SCREEN" if passed else "REDUCED_ORACLE_NO_SIGNAL",
        failure=failure,
        experiment_root=experiment_root,
        supersedes=supersedes,
    )
    if failure:
        raise failure
    if not passed:
        raise RuntimeError("QPOP-R3-v1 smoke failed its frozen validity gate")
    return 0


def run_signal_screen(
    *,
    run_id: str,
    input_path: Path,
    output_root: Path,
    experiment_root: Path,
    supersedes: str | None = None,
) -> int:
    started_at, started = _utc_now(), time.monotonic()
    run_root = output_root / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    intent_path = experiment_root / "intents" / f"{run_id}.json"
    cases = [
        {"voltage_v": voltage, "resistance_ohm": resistance}
        for voltage in SIGNAL_VOLTAGES_V
        for resistance in SIGNAL_RESISTANCES_OHM
    ]
    _write_json_once(
        intent_path,
        {
            "schema_version": "qpop-r3-v1-intent-v1",
            "run_id": run_id,
            "tier": "pilot",
            "scientific_role": "oracle_qualification",
            "gate": "N3B",
            "grid": [50, 20],
            "end_time_ns": 494.0,
            "time_step_ns": 1.0,
            "pulse_protocol": "four-60ns-on-60ns-off-5ns-edge",
            "cases": cases,
            "structure_threshold": STRUCTURE_THRESHOLD,
            "started_at": started_at,
            "supersedes": supersedes,
        },
    )
    artifacts = {"intent": str(intent_path), "run_root": str(run_root)}
    reports: list[dict[str, Any]] = []
    failure: Exception | None = None
    try:
        parameters = QPopParameters.from_input(input_path)
        grid = ReducedOracleGrid(50, 20)
        for case in cases:
            voltage = float(case["voltage_v"])
            resistance = float(case["resistance_ohm"])
            case_id = f"qpop-r3-v1-v{voltage:g}-r{resistance:g}"
            result = ReducedOracleCase(
                parameters=parameters,
                grid=grid,
                end_time_ns=494.0,
                time_step_ns=1.0,
                drive_voltage_v=voltage,
                series_resistance_ohm=resistance,
                save_every=5,
            ).solve()
            artifact_path = run_root / f"case-{case_id}.h5"
            artifact = reduced_result_to_artifact(result, grid=grid, case_id=case_id)
            artifact.write(artifact_path)
            artifact.read(artifact_path)
            event = _event_diagnostics(result)
            report = {
                "case_id": case_id,
                **case,
                **event,
                "max_balance_violation": result.max_balance_violation,
                "temperature_min_k": float(np.min(result.temperature)),
                "temperature_max_k": float(np.max(result.temperature)),
                "artifact": str(artifact_path),
            }
            reports.append(report)
            artifacts[f"case_{len(reports):02d}"] = str(artifact_path)
    except Exception as exc:
        failure = exc
    signal_cases = sum(
        report["phase_fraction_range"] >= 0.05
        and report["nondegenerate_cycle_count"] >= 2
        and report["max_balance_violation"] <= 0.01
        for report in reports
    )
    passed = failure is None and len(reports) == 9 and signal_cases >= 3
    summary = {
        "schema_version": "qpop-r3-v1-signal-screen-summary-v1",
        "reports": reports,
        "signal_case_count": signal_cases,
        "gate_outcome": "REDUCED_ORACLE_SIGNAL_PRESENT" if passed else "REDUCED_ORACLE_NO_SIGNAL",
        "failure": None if failure is None else str(failure),
    }
    summary_path = run_root / "summary.json"
    _write_json_once(summary_path, summary)
    artifacts["summary"] = str(summary_path)
    _record(
        run_id=run_id,
        mode="signal",
        started_at=started_at,
        started=started,
        artifacts=artifacts,
        planned_budget={"cases": 9, "grid": [50, 20], "time_steps_per_case": 494},
        actual_budget={"cases": len(reports), "signal_cases": signal_cases},
        outcome=summary["gate_outcome"] if failure is None else "QPOP_R3_SIGNAL_SCREEN_FAILED",
        route="CONTINUE_QPOP_R3_QUALIFICATION" if passed else "REDUCED_ORACLE_NO_SIGNAL",
        failure=failure,
        experiment_root=experiment_root,
        supersedes=supersedes,
    )
    if failure:
        raise failure
    return 0


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    for mode in ("smoke", "signal"):
        command = subparsers.add_parser(mode)
        command.add_argument("--run-id", required=True)
        command.add_argument("--input", type=Path, required=True)
        command.add_argument("--output-root", type=Path, default=Path("outputs/runs"))
        command.add_argument("--experiment-root", type=Path, default=Path("docs/experiment"))
        command.add_argument("--supersedes")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    kwargs = {
        "run_id": args.run_id,
        "input_path": args.input,
        "output_root": args.output_root,
        "experiment_root": args.experiment_root,
        "supersedes": args.supersedes,
    }
    return run_smoke(**kwargs) if args.mode == "smoke" else run_signal_screen(**kwargs)


if __name__ == "__main__":
    raise SystemExit(main())
