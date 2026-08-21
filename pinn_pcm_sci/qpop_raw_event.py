"""Bounded strong raw-time PINN event-competence smoke and development pilot."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .artifacts import CaseArtifact, PredictionArtifact
from .ledger import ExperimentLedger, RunManifest
from .qpop_method_pilot import _utc_now, _write_json_once, _write_prediction
from .qpop_physics import QPopParameters
from .qpop_pinn import QPopPINN
from .training_protocol import (
    AnchorDiagnosticReport,
    AnchorSet,
    EventCompetenceReport,
    QPopTrainingSession,
    TrainingProtocol,
    TrainingResult,
    phase_fraction_dynamic_range,
    select_sparse_anchor_indices,
    select_screen_protocol,
)


SCREEN_UPDATES = 200
EXTENSION_UPDATES = 800
SEED = 17
SCREEN_WALL_LIMIT_SECONDS = 90 * 60
EXTENSION_WALL_LIMIT_SECONDS = 90 * 60
ANCHOR_UPDATES = 1000
ANCHOR_NODE_COUNT = 82


def frozen_raw_protocols() -> tuple[TrainingProtocol, ...]:
    return (
        TrainingProtocol(
            protocol_id="r1-grouped-joint",
            aggregation="grouped_mean",
            temporal_schedule="joint",
        ),
        TrainingProtocol(
            protocol_id="r2-smooth-joint",
            aggregation="smooth_max",
            temporal_schedule="joint",
        ),
        TrainingProtocol(
            protocol_id="r3-grouped-causal",
            aggregation="grouped_mean",
            temporal_schedule="four_prefix_warmup",
        ),
        TrainingProtocol(
            protocol_id="r4-smooth-causal",
            aggregation="smooth_max",
            temporal_schedule="four_prefix_warmup",
        ),
    )


def _read_metric_spec(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("metric specification must be a JSON object")
    return payload


def _evaluate_checkpoint(
    *,
    model: QPopPINN,
    oracle: CaseArtifact,
    oracle_path: Path,
    split_path: Path,
    metric_spec_path: Path,
    run_root: Path,
    artifact_stem: str,
    method_id: str,
) -> dict[str, Any]:
    checkpoint_path = run_root / f"checkpoint-{artifact_stem}.pt"
    torch.save(model.state_dict(), checkpoint_path)
    prediction_path = run_root / f"prediction-{artifact_stem}.h5"
    _write_prediction(
        model=model,
        oracle=oracle,
        method_id=method_id,
        path=prediction_path,
    )
    metrics_path = run_root / f"metrics-{artifact_stem}.json"
    stdout_path = run_root / f"evaluator-{artifact_stem}.stdout.log"
    stderr_path = run_root / f"evaluator-{artifact_stem}.stderr.log"
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
            command,
            stdout=stdout,
            stderr=stderr,
            timeout=300,
            check=False,
        )
    if completed.returncode != 0:
        raise RuntimeError(
            f"independent evaluator failed for {artifact_stem} with {completed.returncode}"
        )
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    prediction = PredictionArtifact.read(prediction_path)
    metric_spec = _read_metric_spec(metric_spec_path)
    event_range = phase_fraction_dynamic_range(
        prediction.fields[str(metric_spec["structure_field"])],
        prediction.field_time,
        threshold=float(metric_spec["structure_threshold"]),
        analysis_end_ns=494.0,
    )
    return {
        "metrics": metrics,
        "phase_fraction_range": event_range,
        "checkpoint": str(checkpoint_path),
        "prediction": str(prediction_path),
        "metrics_path": str(metrics_path),
        "evaluator_stdout": str(stdout_path),
        "evaluator_stderr": str(stderr_path),
    }


def _model(parameters: QPopParameters, horizon_ns: float) -> QPopPINN:
    torch.manual_seed(SEED)
    return QPopPINN(
        parameters=parameters,
        horizon_ns=horizon_ns,
        method="raw",
        hidden_width=24,
        hidden_layers=3,
    ).double()


def _manifest(
    *,
    run_id: str,
    tier: str,
    started_at: str,
    started: float,
    execution_status: str,
    numerical_validity: str,
    gate_outcome: str,
    route_disposition: str,
    planned_budget: Mapping[str, Any],
    actual_budget: Mapping[str, Any],
    artifacts: Mapping[str, str],
    failure: Exception | None,
    supersedes: str | None,
) -> RunManifest:
    return RunManifest(
        run_id=run_id,
        experiment_group_id="n1-strong-raw-event-competence-v1",
        tier=tier,
        scientific_role="pipeline" if tier == "smoke" else "bottleneck_audit",
        gate="N1",
        started_at=started_at,
        ended_at=_utc_now(),
        command=["python", "-m", "pinn_pcm_sci.qpop_raw_event", tier],
        execution_status=execution_status,
        numerical_validity=numerical_validity,
        gate_outcome=gate_outcome,
        route_disposition=route_disposition,
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
        method_id=(
            "strong-raw-engineering-smoke-v1"
            if tier == "smoke"
            else "paired-strong-raw-2x2-event-competence-v1"
        ),
        case_id=(
            "qpop-cpc-v1-imt-intrinsic-voltage-osc-"
            "bundled-reference-through-512.0793ns"
        ),
        seed=SEED,
        planned_budget=dict(planned_budget),
        actual_budget={**dict(actual_budget), "wall_seconds": time.monotonic() - started},
        checkpoint={
            "id": "oracle-blind-physics-audit-best",
            "selection": "max normalized raw physics violation, then sum, then earliest",
        },
        evaluator_id="frozen-project-development-evaluator-qpop-reference-v1",
        artifacts=dict(artifacts),
        failure_class=None if failure is None else type(failure).__name__,
        replay_of=None,
        supersedes=supersedes,
    )


def run_raw_event_smoke(
    *,
    run_id: str,
    oracle_path: Path,
    input_path: Path,
    split_path: Path,
    metric_spec_path: Path,
    output_root: Path,
    experiment_root: Path,
    supersedes: str | None = None,
) -> int:
    started_at = _utc_now()
    started = time.monotonic()
    run_root = output_root / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    intent_path = experiment_root / "intents" / f"{run_id}.json"
    _write_json_once(
        intent_path,
        {
            "schema_version": "qpop-raw-event-intent-v1",
            "run_id": run_id,
            "tier": "smoke",
            "scientific_role": "pipeline",
            "gate": "N1",
            "protocol_id": "r4-smooth-causal",
            "optimizer_updates": 1,
            "seed": SEED,
            "training_uses_qpop_transient_labels": False,
            "started_at": started_at,
            "supersedes": supersedes,
        },
    )
    artifacts: dict[str, str] = {"intent": str(intent_path), "run_root": str(run_root)}
    failure: Exception | None = None
    training_summary: dict[str, Any] = {}
    evaluation: dict[str, Any] = {}
    try:
        oracle = CaseArtifact.read(oracle_path)
        parameters = QPopParameters.from_input(input_path)
        horizon = max(float(oracle.field_time[-1]), float(oracle.circuit_time[-1]))
        protocol = frozen_raw_protocols()[-1]
        model = _model(parameters, horizon)
        session = QPopTrainingSession.freeze(model, protocol, seed=SEED)
        result = session.train(model, protocol, seed=SEED, updates=1)
        training_summary = result.summary()
        training_path = run_root / "training-smoke.json"
        _write_json_once(training_path, training_summary)
        evaluation = _evaluate_checkpoint(
            model=model,
            oracle=oracle,
            oracle_path=oracle_path,
            split_path=split_path,
            metric_spec_path=metric_spec_path,
            run_root=run_root,
            artifact_stem="smoke",
            method_id="qpop-strong-raw-r4-one-update-smoke-v1",
        )
        artifacts.update(
            {
                "training": str(training_path),
                "checkpoint": str(evaluation["checkpoint"]),
                "prediction": str(evaluation["prediction"]),
                "metrics": str(evaluation["metrics_path"]),
            }
        )
    except Exception as exc:
        failure = exc
    summary_path = run_root / "smoke_summary.json"
    _write_json_once(
        summary_path,
        {
            "schema_version": "qpop-raw-event-smoke-summary-v1",
            "training": training_summary,
            "evaluation": evaluation,
            "failure": None if failure is None else str(failure),
        },
    )
    artifacts["summary"] = str(summary_path)
    manifest = _manifest(
        run_id=run_id,
        tier="smoke",
        started_at=started_at,
        started=started,
        execution_status="FAILED" if failure else "COMPLETED",
        numerical_validity="NOT_EVALUATED" if failure else "VALID_ENGINEERING_SMOKE",
        gate_outcome="N1_RAW_EVENT_SMOKE_FAILED" if failure else "N1_RAW_EVENT_SMOKE_PASS",
        route_disposition="BLOCKED_ENGINEERING" if failure else "CONTINUE_N1_SCREEN",
        planned_budget={"optimizer_updates": 1, "protocols": 1},
        actual_budget={"optimizer_updates": 0 if failure else 1, "training": training_summary},
        artifacts=artifacts,
        failure=failure,
        supersedes=supersedes,
    )
    ledger = ExperimentLedger(experiment_root)
    ledger.record(manifest)
    ledger.validate()
    if failure is not None:
        raise failure
    return 0


def run_raw_event_pilot(
    *,
    run_id: str,
    oracle_path: Path,
    input_path: Path,
    split_path: Path,
    metric_spec_path: Path,
    output_root: Path,
    experiment_root: Path,
    supersedes: str | None = None,
) -> int:
    started_at = _utc_now()
    started = time.monotonic()
    run_root = output_root / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    intent_path = experiment_root / "intents" / f"{run_id}.json"
    protocols = frozen_raw_protocols()
    _write_json_once(
        intent_path,
        {
            "schema_version": "qpop-raw-event-intent-v1",
            "run_id": run_id,
            "tier": "pilot",
            "scientific_role": "bottleneck_audit",
            "gate": "N1",
            "protocols": [
                {
                    "protocol_id": protocol.protocol_id,
                    "aggregation": protocol.aggregation,
                    "temporal_schedule": protocol.temporal_schedule,
                }
                for protocol in protocols
            ],
            "screen_updates_per_arm": SCREEN_UPDATES,
            "extension_updates": EXTENSION_UPDATES,
            "seed": SEED,
            "training_uses_qpop_transient_labels": False,
            "started_at": started_at,
            "supersedes": supersedes,
        },
    )
    artifacts: dict[str, str] = {"intent": str(intent_path), "run_root": str(run_root)}
    failure: Exception | None = None
    screen: dict[str, dict[str, Any]] = {}
    training_results: dict[str, TrainingResult] = {}
    models: dict[str, QPopPINN] = {}
    selected_protocol: str | None = None
    final_evaluation: dict[str, Any] = {}
    competence: EventCompetenceReport | None = None
    try:
        oracle = CaseArtifact.read(oracle_path)
        parameters = QPopParameters.from_input(input_path)
        horizon = max(float(oracle.field_time[-1]), float(oracle.circuit_time[-1]))
        base_model = _model(parameters, horizon)
        common_state = base_model.state_dict()
        session = QPopTrainingSession.freeze(base_model, protocols[0], seed=SEED)
        screen_started = time.monotonic()
        for protocol in protocols:
            model = _model(parameters, horizon)
            model.load_state_dict(common_state)
            result = session.train(
                model,
                protocol,
                seed=SEED,
                updates=SCREEN_UPDATES,
            )
            training_results[protocol.protocol_id] = result
            models[protocol.protocol_id] = model
            training_path = run_root / f"training-screen-{protocol.protocol_id}.json"
            _write_json_once(training_path, result.summary())
            evaluation = _evaluate_checkpoint(
                model=model,
                oracle=oracle,
                oracle_path=oracle_path,
                split_path=split_path,
                metric_spec_path=metric_spec_path,
                run_root=run_root,
                artifact_stem=f"screen-{protocol.protocol_id}",
                method_id=f"qpop-strong-raw-{protocol.protocol_id}-screen-v1",
            )
            metrics = evaluation["metrics"]
            structure_error = float(
                metrics["structure_symmetric_difference_cycle_equal"]
            )
            device_nrmse = float(metrics["device_trajectory_nrmse"])
            physics_max = float(
                result.checkpoint_score["max_normalized_violation"]
            )
            valid = bool(
                result.selected_step > 0
                and physics_max <= 1.25
                and np.isfinite(structure_error)
                and np.isfinite(device_nrmse)
                and np.isfinite(evaluation["phase_fraction_range"])
            )
            screen[protocol.protocol_id] = {
                "valid": valid,
                "selected_step": result.selected_step,
                "structure_error": structure_error,
                "device_nrmse": device_nrmse,
                "phase_fraction_range": evaluation["phase_fraction_range"],
                "physics_audit_max": physics_max,
                "training": result.summary(),
                "evaluation": evaluation,
            }
            artifacts.update(
                {
                    f"training_screen_{protocol.protocol_id}": str(training_path),
                    f"prediction_screen_{protocol.protocol_id}": str(evaluation["prediction"]),
                    f"metrics_screen_{protocol.protocol_id}": str(evaluation["metrics_path"]),
                    f"checkpoint_screen_{protocol.protocol_id}": str(evaluation["checkpoint"]),
                }
            )
            if time.monotonic() - screen_started > SCREEN_WALL_LIMIT_SECONDS:
                raise TimeoutError("strong raw four-arm screen exceeded 90 minutes")

        if any(bool(report["valid"]) for report in screen.values()):
            selected_protocol = select_screen_protocol(screen)
            protocol = next(
                item for item in protocols if item.protocol_id == selected_protocol
            )
            extension_started = time.monotonic()
            extended = session.train(
                models[selected_protocol],
                protocol,
                seed=SEED,
                updates=EXTENSION_UPDATES,
                continuation=training_results[selected_protocol].continuation,
            )
            if time.monotonic() - extension_started > EXTENSION_WALL_LIMIT_SECONDS:
                raise TimeoutError("strong raw extension exceeded 90 minutes")
            final_training_path = (
                run_root / f"training-final-{selected_protocol}.json"
            )
            _write_json_once(final_training_path, extended.summary())
            final_evaluation = _evaluate_checkpoint(
                model=models[selected_protocol],
                oracle=oracle,
                oracle_path=oracle_path,
                split_path=split_path,
                metric_spec_path=metric_spec_path,
                run_root=run_root,
                artifact_stem=f"final-{selected_protocol}",
                method_id=f"qpop-strong-raw-{selected_protocol}-1000-update-v1",
            )
            metrics = final_evaluation["metrics"]
            competence = EventCompetenceReport.adjudicate(
                selected_step=extended.selected_step,
                phase_fraction_range=float(
                    final_evaluation["phase_fraction_range"]
                ),
                structure_error=float(
                    metrics["structure_symmetric_difference_cycle_equal"]
                ),
                device_nrmse=float(metrics["device_trajectory_nrmse"]),
                physics_audit_max=float(
                    extended.checkpoint_score["max_normalized_violation"]
                ),
            )
            artifacts.update(
                {
                    "training_final": str(final_training_path),
                    "prediction_final": str(final_evaluation["prediction"]),
                    "metrics_final": str(final_evaluation["metrics_path"]),
                    "checkpoint_final": str(final_evaluation["checkpoint"]),
                }
            )
            training_results[selected_protocol] = extended
    except Exception as exc:
        failure = exc

    summary_path = run_root / "pilot_summary.json"
    _write_json_once(
        summary_path,
        {
            "schema_version": "qpop-strong-raw-event-pilot-summary-v1",
            "screen": screen,
            "selected_protocol": selected_protocol,
            "final_evaluation": final_evaluation,
            "competence": None if competence is None else asdict(competence),
            "oracle_qualification": "UNQUALIFIED",
            "scientific_use": "DEVELOPMENT_ONLY",
            "failure": None if failure is None else str(failure),
        },
    )
    artifacts["summary"] = str(summary_path)
    if failure is not None:
        gate_outcome = "N1_RAW_EVENT_PILOT_FAILED"
        route = "CONTINUE_N2_SPARSE_ANCHOR_DIAGNOSTIC"
        numerical_validity = "NOT_EVALUATED"
    elif competence is not None and competence.passed:
        gate_outcome = competence.gate_outcome
        route = "CONTINUE_N3A_QPOP_494NS_QUALIFICATION"
        numerical_validity = "VALID_DEVELOPMENT_PILOT"
    else:
        gate_outcome = (
            "RAW_EVENT_SCREEN_INVALID"
            if competence is None
            else competence.gate_outcome
        )
        route = "CONTINUE_N2_SPARSE_ANCHOR_DIAGNOSTIC"
        numerical_validity = "VALID_DEVELOPMENT_NEGATIVE"
    actual_updates = sum(
        result.actual_updates if protocol_id != selected_protocol else 0
        for protocol_id, result in training_results.items()
    )
    if selected_protocol is not None and selected_protocol in training_results:
        actual_updates += training_results[selected_protocol].actual_updates
    manifest = _manifest(
        run_id=run_id,
        tier="pilot",
        started_at=started_at,
        started=started,
        execution_status="FAILED" if failure else "COMPLETED",
        numerical_validity=numerical_validity,
        gate_outcome=gate_outcome,
        route_disposition=route,
        planned_budget={
            "protocols": 4,
            "screen_updates_per_arm": SCREEN_UPDATES,
            "extension_updates": EXTENSION_UPDATES,
            "total_optimizer_updates": 1600,
        },
        actual_budget={
            "optimizer_updates": actual_updates,
            "selected_protocol": selected_protocol,
            "training": {
                protocol_id: result.summary()
                for protocol_id, result in training_results.items()
            },
        },
        artifacts=artifacts,
        failure=failure,
        supersedes=supersedes,
    )
    ledger = ExperimentLedger(experiment_root)
    ledger.record(manifest)
    ledger.validate()
    if failure is not None:
        raise failure
    return 0


def run_anchor_diagnostic(
    *,
    run_id: str,
    oracle_path: Path,
    input_path: Path,
    split_path: Path,
    metric_spec_path: Path,
    baseline_run_root: Path,
    output_root: Path,
    experiment_root: Path,
    supersedes: str | None = None,
) -> int:
    """Run the single preregistered solver-assisted N2 diagnostic."""
    started_at = _utc_now()
    started = time.monotonic()
    run_root = output_root / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    intent_path = experiment_root / "intents" / f"{run_id}.json"
    _write_json_once(
        intent_path,
        {
            "schema_version": "qpop-sparse-anchor-diagnostic-intent-v1",
            "run_id": run_id,
            "tier": "pilot",
            "scientific_role": "bottleneck_audit",
            "gate": "N2",
            "baseline_run_root": str(baseline_run_root),
            "target_times_ns": [130.0, 260.0, 390.0, 494.0],
            "node_sample_count": ANCHOR_NODE_COUNT,
            "node_sampling_seed": SEED,
            "eta_scale": 1.6,
            "anchor_weight": 1.0,
            "optimizer_updates": ANCHOR_UPDATES,
            "physics_ceiling": 1.25,
            "scientific_use": "SOLVER_ASSISTED_DIAGNOSTIC_ONLY",
            "started_at": started_at,
            "supersedes": supersedes,
        },
    )
    artifacts: dict[str, str] = {"intent": str(intent_path), "run_root": str(run_root)}
    failure: Exception | None = None
    training_summary: dict[str, Any] = {}
    evaluation: dict[str, Any] = {}
    report: AnchorDiagnosticReport | None = None
    protocol_id: str | None = None
    anchor_contract: dict[str, Any] = {}
    try:
        baseline_summary = json.loads(
            (baseline_run_root / "pilot_summary.json").read_text(encoding="utf-8")
        )
        if bool((baseline_summary.get("competence") or {}).get("passed")):
            raise ValueError("N2 is forbidden after a passing N1 capability gate")
        protocol_id = str(baseline_summary.get("selected_protocol") or "")
        protocols = {protocol.protocol_id: protocol for protocol in frozen_raw_protocols()}
        if protocol_id not in protocols:
            raise ValueError("N2 requires the unique stable protocol selected by N1")
        protocol = protocols[protocol_id]
        oracle = CaseArtifact.read(oracle_path)
        metric_spec = _read_metric_spec(metric_spec_path)
        structure_field = str(metric_spec["structure_field"])
        parameters = QPopParameters.from_input(input_path)
        horizon = max(float(oracle.field_time[-1]), float(oracle.circuit_time[-1]))
        time_indices, node_indices = select_sparse_anchor_indices(
            oracle.field_time,
            node_count=oracle.nodes.shape[0],
            sample_count=ANCHOR_NODE_COUNT,
            seed=SEED,
        )
        rows: list[list[float]] = []
        eta_targets: list[float] = []
        for time_index in time_indices:
            normalized_time = float(oracle.field_time[time_index]) / horizon
            for node_index in node_indices:
                x, y = oracle.nodes[node_index]
                rows.append(
                    [float(x) / parameters.lx, float(y) / parameters.ly, normalized_time]
                )
                eta_targets.append(float(oracle.fields[structure_field][time_index, node_index]))
        anchors = AnchorSet(
            coordinates=torch.as_tensor(rows, dtype=torch.float64),
            eta_targets=torch.as_tensor(eta_targets, dtype=torch.float64).reshape(-1, 1),
        )
        anchor_contract = {
            "schema_version": "qpop-sparse-eta-anchor-contract-v1",
            "target_times_ns": [130.0, 260.0, 390.0, 494.0],
            "selected_time_indices": list(time_indices),
            "selected_times_ns": [float(oracle.field_time[index]) for index in time_indices],
            "selected_node_indices": list(node_indices),
            "node_sampling_seed": SEED,
            "label_count": len(eta_targets),
            "field": structure_field,
            "eta_scale": 1.6,
            "anchor_weight": 1.0,
            "scientific_use": "SOLVER_ASSISTED_DIAGNOSTIC_ONLY",
        }
        contract_path = run_root / "anchor_contract.json"
        _write_json_once(contract_path, anchor_contract)
        artifacts["anchor_contract"] = str(contract_path)

        model = _model(parameters, horizon)
        session = QPopTrainingSession.freeze(model, protocol, seed=SEED)
        result = session.train_anchor_diagnostic(
            model,
            protocol,
            anchors=anchors,
            seed=SEED,
            updates=ANCHOR_UPDATES,
        )
        if time.monotonic() - started > EXTENSION_WALL_LIMIT_SECONDS:
            raise TimeoutError("sparse anchor diagnostic exceeded 90 minutes")
        training_summary = result.summary()
        training_path = run_root / "training-anchor.json"
        _write_json_once(training_path, training_summary)
        evaluation = _evaluate_checkpoint(
            model=model,
            oracle=oracle,
            oracle_path=oracle_path,
            split_path=split_path,
            metric_spec_path=metric_spec_path,
            run_root=run_root,
            artifact_stem="anchor",
            method_id=f"qpop-raw-{protocol_id}-sparse-eta-anchor-diagnostic-v1",
        )
        metrics = evaluation["metrics"]
        report = AnchorDiagnosticReport.adjudicate(
            phase_fraction_range=float(evaluation["phase_fraction_range"]),
            structure_error=float(metrics["structure_symmetric_difference_cycle_equal"]),
            physics_audit_max=float(result.checkpoint_score["max_normalized_violation"]),
        )
        artifacts.update(
            {
                "training": str(training_path),
                "checkpoint": str(evaluation["checkpoint"]),
                "prediction": str(evaluation["prediction"]),
                "metrics": str(evaluation["metrics_path"]),
            }
        )
    except Exception as exc:
        failure = exc

    summary_path = run_root / "anchor_summary.json"
    _write_json_once(
        summary_path,
        {
            "schema_version": "qpop-sparse-eta-anchor-diagnostic-summary-v1",
            "baseline_run_root": str(baseline_run_root),
            "protocol_id": protocol_id,
            "anchor_contract": anchor_contract,
            "training": training_summary,
            "evaluation": evaluation,
            "diagnostic": None if report is None else asdict(report),
            "oracle_qualification": "UNQUALIFIED",
            "scientific_use": "SOLVER_ASSISTED_DIAGNOSTIC_ONLY",
            "failure": None if failure is None else str(failure),
        },
    )
    artifacts["summary"] = str(summary_path)
    outcome = "N2_DIAGNOSTIC_FAILED" if failure else report.gate_outcome
    manifest = RunManifest(
        run_id=run_id,
        experiment_group_id="n2-sparse-eta-anchor-diagnostic-v1",
        tier="pilot",
        scientific_role="bottleneck_audit",
        gate="N2",
        started_at=started_at,
        ended_at=_utc_now(),
        command=["python", "-m", "pinn_pcm_sci.qpop_raw_event", "anchor"],
        execution_status="FAILED" if failure else "COMPLETED",
        numerical_validity="NOT_EVALUATED" if failure else "VALID_DEVELOPMENT_DIAGNOSTIC",
        gate_outcome=outcome,
        route_disposition="CLOSE_QPOP_PINN_CONTINUE_N3B_REDUCED_ORACLE",
        evidence_identity="QPOP_CPC_V1_BUNDLED_REFERENCE_UNQUALIFIED_SOLVER_ASSISTED",
        claim_status="NO_SCIENTIFIC_CLAIMS_DIAGNOSTIC_ONLY",
        code_identity={"kind": "working-tree", "dirty": True},
        environment={
            "python": platform.python_version(),
            "torch": torch.__version__,
            "dtype": "float64",
            "device": "cpu",
        },
        physical_contract_id="PROVISIONAL_G3_QPOP_CPC_V1_IMT_CONTRACT",
        split_id="qpop-cpc-v1-bundled-reference-development-only-v1",
        method_id=f"qpop-raw-{protocol_id or 'unknown'}-sparse-eta-anchor-diagnostic-v1",
        case_id="qpop-cpc-v1-imt-intrinsic-voltage-osc-bundled-reference-through-512.0793ns",
        seed=SEED,
        planned_budget={
            "optimizer_updates": ANCHOR_UPDATES,
            "snapshot_count": 4,
            "nodes_per_snapshot": ANCHOR_NODE_COUNT,
            "wall_seconds": EXTENSION_WALL_LIMIT_SECONDS,
        },
        actual_budget={
            "optimizer_updates": int(training_summary.get("actual_updates", 0)),
            "wall_seconds": time.monotonic() - started,
            "label_count": int(anchor_contract.get("label_count", 0)),
        },
        checkpoint={
            "id": "solver-assisted-diagnostic-anchor-best",
            "selection": "physics max <= 1.25, then anchor loss, physics max, sum, earliest",
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
    subparsers = parser.add_subparsers(dest="tier", required=True)
    for tier in ("smoke", "pilot", "anchor"):
        command = subparsers.add_parser(tier)
        command.add_argument("--run-id", required=True)
        command.add_argument("--oracle", type=Path, required=True)
        command.add_argument("--input", type=Path, required=True)
        command.add_argument("--split", type=Path, required=True)
        command.add_argument("--metric-spec", type=Path, required=True)
        command.add_argument("--output-root", type=Path, default=Path("outputs/runs"))
        command.add_argument(
            "--experiment-root", type=Path, default=Path("docs/experiment")
        )
        command.add_argument("--supersedes")
        if tier == "anchor":
            command.add_argument("--baseline-run-root", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    kwargs = {
        "run_id": args.run_id,
        "oracle_path": args.oracle,
        "input_path": args.input,
        "split_path": args.split,
        "metric_spec_path": args.metric_spec,
        "output_root": args.output_root,
        "experiment_root": args.experiment_root,
        "supersedes": args.supersedes,
    }
    if args.tier == "smoke":
        return run_raw_event_smoke(**kwargs)
    if args.tier == "pilot":
        return run_raw_event_pilot(**kwargs)
    return run_anchor_diagnostic(
        **kwargs,
        baseline_run_root=args.baseline_run_root,
    )


if __name__ == "__main__":
    raise SystemExit(main())
