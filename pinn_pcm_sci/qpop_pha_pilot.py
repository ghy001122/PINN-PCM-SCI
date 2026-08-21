"""Bounded development-only PHA attribution pilot on the Q-POP equations."""

from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .artifacts import CaseArtifact
from .ledger import ExperimentLedger, RunManifest
from .qpop_method_pilot import (
    PilotBatches,
    _all_residuals,
    _train_method,
    _utc_now,
    _write_json_once,
    _write_prediction,
)
from .qpop_physics import QPopParameters
from .qpop_pinn import PHA_METHODS, QPopPINN, residual_scales


def adjudicate_pha_screen(
    metrics: Mapping[str, Mapping[str, Any]],
    training: Mapping[str, Mapping[str, Any]],
    *,
    min_structure_effect: float,
    physics_noninferiority_ratio: float,
) -> dict[str, Any]:
    """Apply the predeclared shared-gate attribution screen."""

    required = set(PHA_METHODS)
    if set(metrics) != required or set(training) != required:
        raise ValueError("PHA screen requires all four frozen attribution arms")
    if min_structure_effect <= 0.0 or physics_noninferiority_ratio < 1.0:
        raise ValueError("PHA screen thresholds are invalid")
    structure_key = "structure_symmetric_difference_cycle_equal"
    device_key = "device_trajectory_nrmse"
    shared_structure = float(metrics["pha_shared"][structure_key])
    competitors = ("fourier_global", "pha_capacity", "pha_sampling")
    margins = {
        method: float(metrics[method][structure_key]) - shared_structure
        for method in competitors
    }
    structure_pass = all(
        np.isfinite(margin) and margin >= min_structure_effect
        for margin in margins.values()
    )
    shared_physics = float(
        training["pha_shared"]["checkpoint_score"]["max_normalized_violation"]
    )
    global_physics = float(
        training["fourier_global"]["checkpoint_score"][
            "max_normalized_violation"
        ]
    )
    physics_pass = (
        np.isfinite(shared_physics)
        and np.isfinite(global_physics)
        and shared_physics <= physics_noninferiority_ratio * global_physics
    )
    shared_device = float(metrics["pha_shared"][device_key])
    global_device = float(metrics["fourier_global"][device_key])
    device_pass = (
        np.isfinite(shared_device)
        and np.isfinite(global_device)
        and shared_device <= global_device
    )
    all_pass = structure_pass and physics_pass and device_pass
    return {
        "schema_version": "pha-development-screen-adjudication-v1",
        "disposition": (
            "DEVELOPMENT_PHA_SIGNAL_PRESENT"
            if all_pass
            else "DEVELOPMENT_PHA_SIGNAL_NOT_DETECTED"
        ),
        "all_required_checks_pass": all_pass,
        "checks": {
            "shared_beats_all_attribution_arms": structure_pass,
            "physics_noninferiority_to_global_fourier": physics_pass,
            "device_not_worse_than_global_fourier": device_pass,
        },
        "structure_margins": margins,
        "min_structure_effect": min_structure_effect,
        "physics_noninferiority_ratio": physics_noninferiority_ratio,
        "shared_physics_max": shared_physics,
        "global_fourier_physics_max": global_physics,
    }


def _gate_diagnostics(model: QPopPINN, *, seed: int) -> dict[str, float]:
    coordinates = torch.rand(
        (256, 3), generator=torch.Generator().manual_seed(seed), dtype=torch.float64
    )
    with torch.no_grad():
        output = model.phase_hotspot_diagnostics(coordinates)
    gate = output.physical_gate[:, 0]
    return {
        "minimum": float(gate.min()),
        "maximum": float(gate.max()),
        "mean": float(gate.mean()),
        "standard_deviation": float(gate.std()),
        "dynamic_range": float(gate.max() - gate.min()),
        "phase_indicator_mean": float(output.phase_indicator.mean()),
        "joule_indicator_mean": float(output.joule_indicator.mean()),
    }


def run_pha_development_pilot(
    *,
    run_id: str,
    oracle_path: Path,
    input_path: Path,
    split_path: Path,
    metric_spec_path: Path,
    baseline_run_root: Path,
    output_root: Path,
    experiment_root: Path,
    seed: int,
    updates: int,
    min_structure_effect: float = 1.0e-4,
    physics_noninferiority_ratio: float = 1.05,
    supersedes: str | None = None,
) -> int:
    if updates <= 0:
        raise ValueError("PHA pilot updates must be positive")
    started_at = _utc_now()
    started = time.monotonic()
    run_root = output_root / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    intent_path = experiment_root / "intents" / f"{run_id}.json"
    _write_json_once(
        intent_path,
        {
            "schema_version": "qpop-pha-development-pilot-intent-v1",
            "run_id": run_id,
            "tier": "pilot",
            "scientific_role": "protocol_selection",
            "gate": "G6_PHA",
            "methods": list(PHA_METHODS),
            "seed": seed,
            "updates_per_method": updates,
            "candidate_multiplier": 4,
            "min_structure_effect": min_structure_effect,
            "physics_noninferiority_ratio": physics_noninferiority_ratio,
            "baseline_run_root": str(baseline_run_root),
            "training_uses_qpop_transient_labels": False,
            "oracle_qualification": "UNQUALIFIED",
            "scientific_use": "DEVELOPMENT_ONLY",
            "claim_status": "NO_SCIENTIFIC_CLAIMS_UNQUALIFIED_ORACLE",
            "supersedes": supersedes,
            "started_at": started_at,
        },
    )

    failure: Exception | None = None
    metrics_by_method: dict[str, dict[str, Any]] = {}
    training_by_method: dict[str, dict[str, Any]] = {}
    gate_by_method: dict[str, dict[str, float]] = {}
    adjudication: dict[str, Any] | None = None
    artifacts: dict[str, str] = {"intent": str(intent_path), "run_root": str(run_root)}
    try:
        oracle = CaseArtifact.read(oracle_path)
        parameters = QPopParameters.from_input(input_path)
        horizon = max(float(oracle.field_time[-1]), float(oracle.circuit_time[-1]))
        models: dict[str, QPopPINN] = {}
        common_state: dict[str, Any] | None = None
        for method in PHA_METHODS:
            torch.manual_seed(seed)
            model = QPopPINN(
                parameters=parameters,
                horizon_ns=horizon,
                method=method,
                hidden_width=24,
                hidden_layers=3,
            ).double()
            if common_state is None:
                common_state = copy.deepcopy(model.state_dict())
            else:
                model.load_state_dict(common_state)
            models[method] = model

        audit_batches = PilotBatches.fixed(
            seed=seed + 100000,
            interior=12,
            initial=8,
            boundary_per_side=5,
        )
        shared_scales = residual_scales(
            _all_residuals(models["fourier_global"], audit_batches)
        )
        baseline_metrics_path = baseline_run_root / "metrics-raw.json"
        baseline_summary_path = baseline_run_root / "pilot_summary.json"
        baseline_metrics = json.loads(
            baseline_metrics_path.read_text(encoding="utf-8")
        )
        artifacts.update(
            {
                "frozen_raw_baseline_metrics": str(baseline_metrics_path),
                "frozen_raw_baseline_summary": str(baseline_summary_path),
            }
        )
        for method, model in models.items():
            training = _train_method(
                model=model,
                seed=seed,
                updates=updates,
                scales=shared_scales,
                audit_batches=audit_batches,
                stop_gradient_clock_target=True,
            )
            training_by_method[method] = training
            gate_by_method[method] = _gate_diagnostics(model, seed=seed + 200000)
            checkpoint_path = run_root / f"checkpoint-{method}.pt"
            torch.save(model.state_dict(), checkpoint_path)
            training_path = run_root / f"training-{method}.json"
            _write_json_once(training_path, training)
            prediction_path = run_root / f"prediction-{method}.h5"
            _write_prediction(
                model=model,
                oracle=oracle,
                method_id=f"qpop-{method}-development-pilot-v1",
                path=prediction_path,
            )
            metrics_path = run_root / f"metrics-{method}.json"
            stdout_path = run_root / f"evaluator-{method}.stdout.log"
            stderr_path = run_root / f"evaluator-{method}.stderr.log"
            command = [
                sys.executable,
                "-m",
                "pinn_pcm_sci.evaluate",
                "--prediction",
                str(prediction_path),
                "--oracle",
                str(oracle_path),
                "--split",
                str(split_path),
                "--metric-spec",
                str(metric_spec_path),
                "--out",
                str(metrics_path),
            ]
            with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
                completed = subprocess.run(
                    command, stdout=stdout, stderr=stderr, timeout=300, check=False
                )
            if completed.returncode != 0:
                raise RuntimeError(
                    f"independent evaluator failed for {method} with {completed.returncode}"
                )
            metrics_by_method[method] = json.loads(
                metrics_path.read_text(encoding="utf-8")
            )
            artifacts.update(
                {
                    f"checkpoint_{method}": str(checkpoint_path),
                    f"training_{method}": str(training_path),
                    f"prediction_{method}": str(prediction_path),
                    f"metrics_{method}": str(metrics_path),
                }
            )
        adjudication = adjudicate_pha_screen(
            metrics_by_method,
            training_by_method,
            min_structure_effect=min_structure_effect,
            physics_noninferiority_ratio=physics_noninferiority_ratio,
        )
        adjudication["gate_diagnostics"] = gate_by_method
        adjudication["frozen_raw_baseline_context"] = baseline_metrics
        gate_valid = gate_by_method["pha_shared"]["dynamic_range"] > 1.0e-3
        adjudication["checks"]["shared_gate_nonconstant"] = gate_valid
        adjudication["all_required_checks_pass"] = bool(
            adjudication["all_required_checks_pass"] and gate_valid
        )
        if not adjudication["all_required_checks_pass"]:
            adjudication["disposition"] = "DEVELOPMENT_PHA_SIGNAL_NOT_DETECTED"
    except Exception as exc:
        failure = exc

    summary_path = run_root / "pilot_summary.json"
    _write_json_once(
        summary_path,
        {
            "schema_version": "qpop-pha-development-pilot-summary-v1",
            "metrics": metrics_by_method,
            "training": training_by_method,
            "gate_diagnostics": gate_by_method,
            "adjudication": adjudication,
            "oracle_qualification": "UNQUALIFIED",
            "scientific_use": "DEVELOPMENT_ONLY",
            "failure": None if failure is None else str(failure),
        },
    )
    artifacts["summary"] = str(summary_path)
    disposition = (
        "BLOCKED_ENGINEERING"
        if failure
        else str(adjudication["disposition"])
    )
    manifest = RunManifest(
        run_id=run_id,
        experiment_group_id="g6-pha-qpop-development-screen-v1",
        tier="pilot",
        scientific_role="protocol_selection",
        gate="G6_PHA",
        started_at=started_at,
        ended_at=_utc_now(),
        command=["python", "-m", "pinn_pcm_sci.qpop_pha_pilot"],
        execution_status="FAILED" if failure else "COMPLETED",
        numerical_validity="NOT_EVALUATED" if failure else "VALID_DEVELOPMENT_PILOT",
        gate_outcome="G6_PHA_DEVELOPMENT_PILOT_FAILED" if failure else disposition,
        route_disposition=disposition,
        evidence_identity="QPOP_CPC_V1_BUNDLED_REFERENCE_UNQUALIFIED",
        claim_status="NO_SCIENTIFIC_CLAIMS_UNQUALIFIED_ORACLE",
        code_identity={"kind": "working-tree", "dirty": True},
        environment={
            "python": platform.python_version(),
            "torch": torch.__version__,
            "dtype": "float64",
            "device": "cpu",
        },
        physical_contract_id="PROVISIONAL_G3_QPOP_CPC_V1_IMT_CONTRACT",
        split_id="qpop-cpc-v1-bundled-reference-development-only-v1",
        method_id="paired-pha-four-arm-shared-gate-screen-v1",
        case_id=(
            "qpop-cpc-v1-imt-intrinsic-voltage-osc-"
            "bundled-reference-through-512.0793ns"
        ),
        seed=seed,
        planned_budget={
            "methods": len(PHA_METHODS),
            "optimizer_updates_per_method": updates,
            "candidate_multiplier": 4,
        },
        actual_budget={
            "optimizer_updates": 0 if failure else len(PHA_METHODS) * updates,
            "wall_seconds": time.monotonic() - started,
            "training": training_by_method,
        },
        checkpoint={
            "id": "oracle-blind-physics-audit-best",
            "selection": "max normalized raw physics violation, then sum",
        },
        evaluator_id="frozen-project-development-evaluator-qpop-reference-v1",
        artifacts=artifacts,
        failure_class=None if failure is None else type(failure).__name__,
        replay_of=None,
        supersedes=supersedes,
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
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument("--metric-spec", type=Path, required=True)
    parser.add_argument("--baseline-run-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs/runs"))
    parser.add_argument(
        "--experiment-root", type=Path, default=Path("docs/experiment")
    )
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--updates", type=int, default=40)
    parser.add_argument("--min-structure-effect", type=float, default=1.0e-4)
    parser.add_argument("--physics-noninferiority-ratio", type=float, default=1.05)
    parser.add_argument("--supersedes")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    return run_pha_development_pilot(
        run_id=args.run_id,
        oracle_path=args.oracle,
        input_path=args.input,
        split_path=args.split,
        metric_spec_path=args.metric_spec,
        baseline_run_root=args.baseline_run_root,
        output_root=args.output_root,
        experiment_root=args.experiment_root,
        seed=args.seed,
        updates=args.updates,
        min_structure_effect=args.min_structure_effect,
        physics_noninferiority_ratio=args.physics_noninferiority_ratio,
        supersedes=args.supersedes,
    )


if __name__ == "__main__":
    raise SystemExit(main())
