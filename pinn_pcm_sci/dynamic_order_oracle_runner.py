"""Bounded smoke and fixed three-case signal gate for QPOP-R4-v1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import time
from typing import Any, Sequence

import numpy as np
import scipy

from .dynamic_order_oracle import DynamicOrderOracleCase, dynamic_result_to_artifact
from .ledger import ExperimentLedger, RunManifest
from .qpop_method_pilot import _utc_now, _write_json_once
from .qpop_physics import QPopParameters
from .reduced_oracle import ReducedOracleGrid, ReducedOracleResult


R4_SIGNAL_CASES = ((9.0, 5.0e5), (10.5, 3.0e5), (7.5, 7.0e5))
R4_SIGNAL_TIME_STEP_NS = 0.1
R4_SMOKE_TIME_STEP_NS = 1.0
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
        "nondegenerate_cycle_count": sum(
            bool(cycle["nondegenerate"]) for cycle in cycles
        ),
        "cycles": cycles,
    }


def classify_r4_signal(reports: list[dict[str, Any]]) -> dict[str, Any]:
    signal_count = sum(
        bool(report.get("finite"))
        and float(report.get("phase_fraction_range", 0.0)) >= 0.05
        and int(report.get("nondegenerate_cycle_count", 0)) >= 2
        and float(report.get("max_balance_violation", 1.0)) <= 0.01
        for report in reports
    )
    return {
        "signal_case_count": signal_count,
        "required_signal_case_count": 2,
        "gate_outcome": "R4_SIGNAL_PRESENT" if signal_count >= 2 else "R4_NO_SIGNAL",
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
        experiment_group_id="qpop-r4-v1-dynamic-order-reduced-oracle",
        tier="smoke" if mode == "smoke" else "pilot",
        scientific_role="oracle_qualification",
        gate="R4-S0" if mode == "smoke" else "R4-S1",
        started_at=started_at,
        ended_at=_utc_now(),
        command=["python", "-m", "pinn_pcm_sci.dynamic_order_oracle_runner", mode],
        execution_status="FAILED" if failure else "COMPLETED",
        numerical_validity=(
            "NOT_EVALUATED" if failure else "VALID_REDUCED_ORACLE_NUMERICS"
        ),
        gate_outcome=outcome,
        route_disposition=route,
        evidence_identity="QPOP_R4_V1_DYNAMIC_ORDER_REDUCED_SYNTHETIC_ORACLE",
        claim_status="NO_SCIENTIFIC_CLAIMS_REDUCED_ORACLE_DEVELOPMENT",
        code_identity={"kind": "working-tree", "dirty": True},
        environment={
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "dtype": "float64",
            "device": "cpu",
        },
        physical_contract_id="qpop-r4-v1",
        split_id="qpop-r4-v1-development-fixed-three-case-gate-v1",
        method_id=f"qpop-r4-v1-dynamic-order-{mode}",
        case_id=(
            "qpop-r4-v1-smoke" if mode == "smoke" else "qpop-r4-v1-fixed-three-case-gate"
        ),
        seed=0,
        planned_budget=planned_budget,
        actual_budget={**actual_budget, "wall_seconds": time.monotonic() - started},
        checkpoint={"id": "NOT_APPLICABLE", "selection": "INDEPENDENT_NUMERICAL_ORACLE"},
        evaluator_id="qpop-r4-v1-event-diagnostic-v1",
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
            "schema_version": "qpop-r4-v1-intent-v1",
            "run_id": run_id,
            "tier": "smoke",
            "scientific_role": "oracle_qualification",
            "gate": "R4-S0",
            "grid": [6, 4],
            "end_time_ns": 2.0,
            "time_step_ns": R4_SMOKE_TIME_STEP_NS,
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
        grid = ReducedOracleGrid(6, 4)
        result = DynamicOrderOracleCase(
            parameters=QPopParameters.from_input(input_path),
            grid=grid,
            end_time_ns=2.0,
            time_step_ns=R4_SMOKE_TIME_STEP_NS,
            drive_voltage_v=0.0,
            series_resistance_ohm=5.0e5,
            save_every=1,
        ).solve()
        artifact = dynamic_result_to_artifact(
            result, grid=grid, case_id="qpop-r4-v1-smoke"
        )
        artifact_path = run_root / "case.h5"
        artifact.write(artifact_path)
        artifact.read(artifact_path)
        summary = {
            "schema_version": "qpop-r4-v1-smoke-summary-v1",
            "max_balance_violation": result.max_balance_violation,
            "finite": bool(
                np.all(np.isfinite(result.eta))
                and np.all(np.isfinite(result.mu))
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
    passed = (
        failure is None
        and bool(summary.get("finite"))
        and float(summary.get("max_balance_violation", 1.0)) <= 0.01
    )
    _record(
        run_id=run_id,
        mode="smoke",
        started_at=started_at,
        started=started,
        artifacts=artifacts,
        planned_budget={"cases": 1, "grid": [6, 4], "time_steps": 2, "wall_minutes": 10},
        actual_budget={"cases": 0 if failure else 1, "time_steps": 0 if failure else 2},
        outcome="R4_SMOKE_PASS" if passed else "R4_SMOKE_FAILED",
        route=(
            "CONTINUE_R4_SIGNAL_GATE"
            if passed
            else "R4_EXECUTION_INVALID"
            if failure is not None
            else "R4_NO_SIGNAL"
        ),
        failure=failure,
        experiment_root=experiment_root,
        supersedes=supersedes,
    )
    if failure:
        raise failure
    if not passed:
        raise RuntimeError("QPOP-R4-v1 smoke failed its frozen validity gate")
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
    _write_json_once(
        intent_path,
        {
            "schema_version": "qpop-r4-v1-intent-v1",
            "run_id": run_id,
            "tier": "pilot",
            "scientific_role": "oracle_qualification",
            "gate": "R4-S1",
            "grid": [50, 20],
            "end_time_ns": 494.0,
            "time_step_ns": R4_SIGNAL_TIME_STEP_NS,
            "pulse_protocol": "four-60ns-on-60ns-off-5ns-edge",
            "cases": [
                {"voltage_v": voltage, "resistance_ohm": resistance}
                for voltage, resistance in R4_SIGNAL_CASES
            ],
            "structure_threshold": STRUCTURE_THRESHOLD,
            "signal_gate": {
                "phase_fraction_range_min": 0.05,
                "nondegenerate_cycle_count_min": 2,
                "max_balance_violation": 0.01,
                "required_case_count": 2,
            },
            "wall_minutes": 30,
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
        for voltage, resistance in R4_SIGNAL_CASES:
            case_id = f"qpop-r4-v1-v{voltage:g}-r{resistance:g}"
            result = DynamicOrderOracleCase(
                parameters=parameters,
                grid=grid,
                end_time_ns=494.0,
                time_step_ns=R4_SIGNAL_TIME_STEP_NS,
                drive_voltage_v=voltage,
                series_resistance_ohm=resistance,
                save_every=5,
            ).solve()
            artifact_path = run_root / f"case-{case_id}.h5"
            dynamic_result_to_artifact(
                result, grid=grid, case_id=case_id
            ).write(artifact_path)
            diagnostics = _event_diagnostics(result)
            report = {
                "case_id": case_id,
                "voltage_v": voltage,
                "resistance_ohm": resistance,
                "finite": bool(
                    np.all(np.isfinite(result.eta))
                    and np.all(np.isfinite(result.mu))
                    and np.all(np.isfinite(result.temperature))
                ),
                "max_balance_violation": result.max_balance_violation,
                "temperature_min_k": float(np.min(result.temperature)),
                "temperature_max_k": float(np.max(result.temperature)),
                "eta_min": float(np.min(result.eta)),
                "eta_max": float(np.max(result.eta)),
                "mu_min": float(np.min(result.mu)),
                "mu_max": float(np.max(result.mu)),
                "artifact": str(artifact_path),
                **diagnostics,
            }
            reports.append(report)
            artifacts[f"case_{len(reports):02d}"] = str(artifact_path)
    except Exception as exc:
        failure = exc
    classification = (
        classify_r4_signal(reports)
        if failure is None
        else {
            "signal_case_count": 0,
            "required_signal_case_count": 2,
            "gate_outcome": "R4_EXECUTION_FAILED",
        }
    )
    summary = {
        "schema_version": "qpop-r4-v1-signal-summary-v1",
        "reports": reports,
        **classification,
        "failure": None if failure is None else str(failure),
    }
    summary_path = run_root / "summary.json"
    _write_json_once(summary_path, summary)
    artifacts["summary"] = str(summary_path)
    passed = classification["gate_outcome"] == "R4_SIGNAL_PRESENT"
    _record(
        run_id=run_id,
        mode="signal",
        started_at=started_at,
        started=started,
        artifacts=artifacts,
        planned_budget={"cases": 3, "grid": [50, 20], "time_steps_per_case": 4940, "wall_minutes": 30},
        actual_budget={"cases": len(reports), "time_steps_per_completed_case": 4940},
        outcome=str(classification["gate_outcome"]),
        route=(
            "CONTINUE_R4_PINN_SMOKE"
            if passed
            else "R4_EXECUTION_INVALID"
            if failure is not None
            else "R4_NO_SIGNAL"
        ),
        failure=failure,
        experiment_root=experiment_root,
        supersedes=supersedes,
    )
    if failure:
        raise failure
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    for name in ("smoke", "signal"):
        command = subparsers.add_parser(name)
        command.add_argument("--run-id", required=True)
        command.add_argument("--input", type=Path, required=True)
        command.add_argument("--output-root", type=Path, default=Path("outputs/runs"))
        command.add_argument("--experiment-root", type=Path, default=Path("docs/experiment"))
        command.add_argument("--supersedes")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    function = run_smoke if arguments.mode == "smoke" else run_signal_screen
    return function(
        run_id=arguments.run_id,
        input_path=arguments.input,
        output_root=arguments.output_root,
        experiment_root=arguments.experiment_root,
        supersedes=arguments.supersedes,
    )


if __name__ == "__main__":
    raise SystemExit(main())
