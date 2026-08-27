"""Process boundary for PHK-V2 freezes and later intent-first runs."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import time
from typing import Any, Sequence

import numpy as np
import scipy

from .phk_contract import (
    PhkObjectContract,
    PhkProgramContract,
    PhkSplitManifest,
    build_phk_split_manifest,
)
from .phk_benchmark import (
    PhkCaseSpec,
    PhkControl,
    PhkEventReport,
    PhkGuardReport,
    PhkOracleCase,
    PhkOracleResult,
    PhkPhysicalContract,
    PhkResolution,
    compare_phk_results,
    read_phk_result,
    run_phk_manufactured_checks,
    write_phk_result,
)
from .phk_evaluator import adjudicate_phk_q
from .ledger import ExperimentLedger, RunManifest


class PhkRunnerContractError(ValueError):
    """A process request does not consume the exact frozen PHK chain."""


EXPERIMENT_GROUP_ID = "phk-v2-qualification"
ORACLE_METHOD_ID = "phk-v2-independent-cartesian-fv-v1"
SPLIT_ID = "phk-v2-complete-case-split-v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _validate_run_id(run_id: str) -> None:
    if not run_id or run_id in {".", ".."}:
        raise PhkRunnerContractError("run_id is empty or invalid")
    if Path(run_id).name != run_id or any(character in run_id for character in ("/", "\\")):
        raise PhkRunnerContractError("run_id must be one filesystem-safe name")


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PhkRunnerContractError(f"invalid JSON evidence: {path}") from exc
    if not isinstance(payload, dict):
        raise PhkRunnerContractError(f"JSON evidence must be an object: {path}")
    return payload


def _write_new_json(path: Path, payload: dict[str, Any]) -> None:
    parent = path.parent
    if not parent.is_dir():
        raise FileNotFoundError(f"output parent does not exist: {parent}")
    encoded = (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        # A partial write is never a valid freeze.  Removal is scoped to the
        # just-created exact output and makes retry semantics explicit.
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise


def run_freeze_splits(
    *,
    program_path: Path,
    object_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    program = PhkProgramContract.load(program_path)
    physical = PhkObjectContract.load(object_path, program=program)
    manifest = build_phk_split_manifest(program=program, physical=physical)
    _write_new_json(Path(output_path), manifest)
    return manifest


def _qualification_rows(physical: PhkPhysicalContract) -> tuple[dict[str, Any], ...]:
    rows = physical.payload["qualification_intents"]
    if not isinstance(rows, list) or len(rows) != 12:
        raise PhkRunnerContractError("PHK qualification ladder is not the frozen 12 rows")
    result: list[dict[str, Any]] = []
    for expected, row in enumerate(rows, start=1):
        if not isinstance(row, dict) or int(row.get("order", 0)) != expected:
            raise PhkRunnerContractError("PHK qualification ladder order drift")
        result.append(dict(row))
    return tuple(result)


def _existing_phk_manifests(experiment_root: Path) -> list[dict[str, Any]]:
    root = experiment_root / "manifests"
    if not root.exists():
        return []
    manifests: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json")):
        payload = _read_json_object(path)
        if payload.get("experiment_group_id") == EXPERIMENT_GROUP_ID:
            manifests.append(payload)
    return manifests


def _assert_no_orphan_intents(experiment_root: Path) -> None:
    finalized = {
        str(item.get("run_id", "")) for item in _existing_phk_manifests(experiment_root)
    }
    candidates = (
        (experiment_root / "intents", "phk-v2-qualification-intent-v1"),
        (experiment_root / "intent_claims", "phk-v2-qualification-claim-v1"),
    )
    for root, schema in candidates:
        if not root.exists():
            continue
        for path in sorted(root.glob("*.json")):
            payload = _read_json_object(path)
            if payload.get("schema_version") != schema:
                continue
            run_id = payload.get("run_id")
            if not isinstance(run_id, str) or run_id not in finalized:
                raise PhkRunnerContractError(
                    "ORPHAN_PHK_INTENT_RECONCILIATION_REQUIRED: "
                    f"{path}; automatic replay is prohibited"
                )


def _assert_intent_order(experiment_root: Path, intent_number: int) -> None:
    manifests = _existing_phk_manifests(experiment_root)
    by_number: dict[int, dict[str, Any]] = {}
    for manifest in manifests:
        actual = manifest.get("actual_budget")
        if not isinstance(actual, dict) or "qualification_intent" not in actual:
            raise PhkRunnerContractError("prior PHK manifest lacks intent identity")
        number = int(actual["qualification_intent"])
        if number in by_number:
            raise PhkRunnerContractError("duplicate PHK qualification intent in ledger")
        by_number[number] = manifest
    if intent_number in by_number:
        raise PhkRunnerContractError("requested PHK qualification intent is already consumed")
    expected_prior = set(range(1, intent_number))
    if set(by_number) != expected_prior:
        raise PhkRunnerContractError(
            "all prior qualification intents must exist exactly once before this intent"
        )
    for number in sorted(by_number):
        manifest = by_number[number]
        if manifest.get("execution_status") != "COMPLETED":
            raise PhkRunnerContractError(
                f"prior qualification intent {number} did not complete; route is stopped"
            )
        if number == 1 and manifest.get("gate_outcome") != "PHK_V2_Q_MANUFACTURED_PASS":
            raise PhkRunnerContractError("manufactured operator gate did not pass")


def _claim_intent(
    experiment_root: Path,
    *,
    run_id: str,
    intent_number: int,
    row: dict[str, Any],
    started_at: str,
    physical: PhkPhysicalContract,
    split: PhkSplitManifest,
) -> Path:
    path = experiment_root / "intent_claims" / f"phk-v2-q-intent-{intent_number:02d}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "phk-v2-qualification-claim-v1",
        "run_id": run_id,
        "started_at": started_at,
        "qualification_intent": row,
        "program_contract_sha256": physical.program.sha256,
        "object_contract_sha256": physical.object.sha256,
        "split_manifest_sha256": split.file_sha256,
        "split_manifest_internal_sha256": split.manifest_sha256,
        "disposition_if_unfinalized": (
            "ORPHAN_PHK_INTENT_RECONCILIATION_REQUIRED_NO_AUTOMATIC_REPLAY"
        ),
    }
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    try:
        descriptor = os.open(path, flags, 0o644)
    except FileExistsError as exc:
        raise PhkRunnerContractError(
            f"immutable qualification intent {intent_number} is already claimed"
        ) from exc
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    return path


def _write_result_once(path: Path, result: PhkOracleResult) -> None:
    write_phk_result(path, result)


def _control_from_row(row: dict[str, Any]) -> PhkControl:
    value = row.get("control")
    if not isinstance(value, str):
        raise PhkRunnerContractError("qualification case row has no control")
    try:
        return PhkControl(value)
    except ValueError as exc:
        raise PhkRunnerContractError(f"unknown PHK qualification control: {value}") from exc


def run_qualification_intent(
    *,
    run_id: str,
    intent_number: int,
    program_path: Path,
    object_path: Path,
    split_path: Path,
    output_root: Path,
    experiment_root: Path,
) -> int:
    """Consume exactly one ordered Q intent and finalize its immutable ledger row."""

    _validate_run_id(run_id)
    physical = PhkPhysicalContract.from_files(
        program_path=Path(program_path), object_path=Path(object_path)
    )
    split = PhkSplitManifest.load(
        Path(split_path), program=physical.program, physical=physical.object
    )
    rows = _qualification_rows(physical)
    if not 1 <= intent_number <= len(rows):
        raise PhkRunnerContractError("qualification intent number is outside the frozen ladder")
    row = rows[intent_number - 1]
    ledger = ExperimentLedger(experiment_root)
    ledger.validate()
    _assert_no_orphan_intents(experiment_root)
    _assert_intent_order(experiment_root, intent_number)

    started_at = _utc_now()
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    claim_path = _claim_intent(
        experiment_root,
        run_id=run_id,
        intent_number=intent_number,
        row=row,
        started_at=started_at,
        physical=physical,
        split=split,
    )
    run_root = Path(output_root) / run_id
    run_root.mkdir(parents=False, exist_ok=False)
    intent_path = Path(experiment_root) / "intents" / f"{run_id}.json"
    intent_path.parent.mkdir(parents=True, exist_ok=True)
    intent_payload = {
        "schema_version": "phk-v2-qualification-intent-v1",
        "run_id": run_id,
        "started_at": started_at,
        "qualification_intent": row,
        "program_contract_path": str(Path(program_path).resolve()),
        "program_contract_sha256": physical.program.sha256,
        "object_contract_path": str(Path(object_path).resolve()),
        "object_contract_sha256": physical.object.sha256,
        "split_manifest_path": str(split.path),
        "split_manifest_sha256": split.file_sha256,
        "split_manifest_internal_sha256": split.manifest_sha256,
        "formal_or_method_pool_access": False,
        "result_adaptive_rescue": False,
    }
    _write_new_json(intent_path, intent_payload)
    artifacts: dict[str, str] = {
        "intent_claim": str(claim_path),
        "intent": str(intent_path),
        "program_contract": str(physical.program.path),
        "program_contract_sha256": physical.program.sha256,
        "object_contract": str(physical.object.path),
        "object_contract_sha256": physical.object.sha256,
        "split_manifest": str(split.path),
        "split_manifest_sha256": split.file_sha256,
        "split_manifest_internal_sha256": split.manifest_sha256,
    }
    failure: BaseException | None = None
    solver_statistics: dict[str, int | float] = {}
    outcome = "PHK_V2_Q_EXECUTION_FAILED"
    numerical_validity = "NOT_EVALUATED"
    case_id = str(row["id"])
    try:
        if intent_number == 1:
            report = run_phk_manufactured_checks(physical)
            outcome = (
                "PHK_V2_Q_MANUFACTURED_PASS"
                if report["passed"]
                else "PHK_V2_Q_MANUFACTURED_NO_GO"
            )
            numerical_validity = "VALID_NO_SCIENTIFIC_FIELD_RESULT"
        else:
            resolution_name = row.get("resolution")
            if not isinstance(resolution_name, str):
                raise PhkRunnerContractError("qualification row lacks resolution")
            resolution = PhkResolution.from_contract(physical, resolution_name)
            control = _control_from_row(row)
            case = PhkCaseSpec.qualification(physical, control)
            result = PhkOracleCase(
                physical=physical,
                case=case,
                resolution=resolution,
            ).solve()
            solver_statistics = dict(result.solver_statistics)
            guard = PhkGuardReport.from_result(result, physical=physical)
            event = (
                None
                if control is PhkControl.ZERO_DRIVE
                else PhkEventReport.from_result(result, physical=physical)
            )
            report = {
                "schema_id": "phk-v2-q-case-report-v1",
                "intent": row,
                "case_id": case.case_id,
                "resolution": asdict(resolution),
                "guard": asdict(guard),
                "event": None if event is None else asdict(event),
                "solver_statistics": solver_statistics,
                "single_case_adjudication": "PENDING_COMPLETE_Q_LADDER",
                "claim_status": "NO_ORACLE_EVENT_OR_METHOD_CLAIM_SINGLE_CASE_ONLY",
            }
            result_path = run_root / f"result-intent-{intent_number:02d}.npz"
            _write_result_once(result_path, result)
            artifacts["result"] = str(result_path)
            artifacts["result_sha256"] = _sha256(result_path)
            outcome = "PHK_V2_Q_CASE_COMPLETED"
            numerical_validity = "PENDING_COMPLETE_Q_LADDER_ADJUDICATION"
            case_id = case.case_id
        report_path = run_root / "report.json"
        _write_new_json(report_path, report)
        artifacts["report"] = str(report_path)
        artifacts["report_sha256"] = _sha256(report_path)
    except BaseException as exc:
        failure = exc

    wall_seconds = time.perf_counter() - wall_start
    cpu_seconds = time.process_time() - cpu_start
    failure_identity = (
        None if failure is None else f"{type(failure).__name__}: {failure}"
    )
    actual_budget: dict[str, Any] = {
        "qualification_intent": intent_number,
        "intent_id": run_id,
        "method_id": ORACLE_METHOD_ID,
        "case_id": case_id,
        "seed": 0,
        "wall_clock_seconds": wall_seconds,
        "process_cpu_seconds": cpu_seconds,
        "gross_compute": {
            "process_cpu_core_hours": cpu_seconds / 3600.0,
            "single_thread_wall_upper_bound_core_hours": wall_seconds / 3600.0,
        },
        "failure_identity": failure_identity,
        "failed_intents": 0 if failure is None else 1,
        "superseding_rerun_eligibility": (
            "NONE_AUTOMATIC_RECONCILIATION_REQUIRED" if failure else "NOT_APPLICABLE"
        ),
        **solver_statistics,
    }
    execution_status = "FAILED" if failure else "COMPLETED"
    route_disposition = (
        "STOP_OR_EXPLICIT_RECONCILIATION"
        if failure
        else (
            "CONTINUE_PHK_Q_INTENT_2"
            if outcome == "PHK_V2_Q_MANUFACTURED_PASS"
            else (
                "STOP_PHK_ORACLE_ROUTE"
                if outcome == "PHK_V2_Q_MANUFACTURED_NO_GO"
                else "AWAIT_COMPLETE_Q_LADDER_ADJUDICATION"
            )
        )
    )
    source_file = Path(__file__)
    benchmark_file = Path(__file__).with_name("phk_benchmark.py")
    manifest = RunManifest(
        run_id=run_id,
        experiment_group_id=EXPERIMENT_GROUP_ID,
        tier="qualification",
        scientific_role=(
            "manufactured_operator_check" if intent_number == 1 else "oracle_qualification"
        ),
        gate="PHK_V2_S2_Q",
        started_at=started_at,
        ended_at=_utc_now(),
        command=[
            "python",
            "-m",
            "pinn_pcm_sci.phk_runner",
            "qualify",
            "--run-id",
            run_id,
            "--intent",
            str(intent_number),
        ],
        execution_status=execution_status,
        numerical_validity=numerical_validity,
        gate_outcome=outcome,
        route_disposition=route_disposition,
        evidence_identity=(
            "NO_SCIENTIFIC_FIELD_RESULT"
            if intent_number == 1
            else "TRANSPARENT_DIMENSIONLESS_REDUCED_BENCHMARK"
        ),
        claim_status=(
            "NO_ORACLE_EVENT_OR_METHOD_CLAIM_EXECUTION_FAILURE"
            if failure
            else "NO_ORACLE_EVENT_OR_METHOD_CLAIM_SINGLE_INTENT_ONLY"
        ),
        code_identity={
            "kind": "working-tree",
            "phk_runner_sha256": _sha256(source_file),
            "phk_benchmark_sha256": _sha256(benchmark_file),
        },
        environment={
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "dtype": "float64",
            "device": "cpu",
        },
        physical_contract_id=physical.contract_id,
        split_id=SPLIT_ID,
        method_id=ORACLE_METHOD_ID,
        case_id=case_id,
        seed=0,
        planned_budget={
            "qualification_intent": row,
            "cpu_core_hours_total_cap": float(
                physical.program.payload["budgets"]["cpu_core_hours"]
            ),
            "failed_intents_count_against_budget": True,
            "result_adaptive_rescue": False,
        },
        actual_budget=actual_budget,
        checkpoint={"id": "NOT_APPLICABLE", "selection": "INDEPENDENT_CPU_ORACLE"},
        evaluator_id="phk-v2-q-event-guard-convergence-evaluator-v1",
        artifacts=artifacts,
        failure_class=None if failure is None else type(failure).__name__,
        replay_of=("Q_NOMINAL_FINE" if intent_number == 7 else None),
        supersedes=None,
    )
    ledger.record(manifest)
    ledger.validate()
    return 1 if failure else 0


def _verified_artifact_path(
    manifest: dict[str, Any],
    key: str,
) -> Path:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise PhkRunnerContractError("PHK manifest lacks artifacts")
    value = artifacts.get(key)
    declared = artifacts.get(f"{key}_sha256")
    if not isinstance(value, str) or not isinstance(declared, str):
        raise PhkRunnerContractError(f"PHK manifest lacks {key} identity")
    path = Path(value)
    if not path.is_file() or _sha256(path) != declared:
        raise PhkRunnerContractError(f"PHK {key} artifact hash mismatch")
    return path


def run_summarize_q(
    *,
    run_id: str,
    program_path: Path,
    object_path: Path,
    split_path: Path,
    output_root: Path,
    experiment_root: Path,
) -> int:
    """Adjudicate the terminal ordered Q bundle without opening method pools."""

    _validate_run_id(run_id)
    physical = PhkPhysicalContract.from_files(
        program_path=Path(program_path), object_path=Path(object_path)
    )
    split = PhkSplitManifest.load(
        Path(split_path), program=physical.program, physical=physical.object
    )
    ledger = ExperimentLedger(experiment_root)
    ledger.validate()
    _assert_no_orphan_intents(experiment_root)
    manifests = _existing_phk_manifests(experiment_root)
    by_intent: dict[int, dict[str, Any]] = {}
    for manifest in manifests:
        actual = manifest.get("actual_budget")
        if not isinstance(actual, dict) or "qualification_intent" not in actual:
            raise PhkRunnerContractError("PHK case manifest lacks intent identity")
        number = int(actual["qualification_intent"])
        if number in by_intent:
            raise PhkRunnerContractError("duplicate PHK qualification intent")
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, dict):
            raise PhkRunnerContractError("PHK case manifest lacks artifacts")
        expected_hashes = {
            "program_contract_sha256": physical.program.sha256,
            "object_contract_sha256": physical.object.sha256,
            "split_manifest_sha256": split.file_sha256,
            "split_manifest_internal_sha256": split.manifest_sha256,
        }
        for key, expected in expected_hashes.items():
            if artifacts.get(key) != expected:
                raise PhkRunnerContractError(
                    f"PHK case manifest {number} has stale {key}"
                )
        by_intent[number] = manifest

    statuses = {
        number: str(manifest["execution_status"])
        for number, manifest in by_intent.items()
    }
    reports: dict[int, dict[str, Any]] = {}
    results: dict[int, PhkOracleResult] = {}
    for number, manifest in sorted(by_intent.items()):
        if manifest["execution_status"] != "COMPLETED":
            continue
        report_path = _verified_artifact_path(manifest, "report")
        reports[number] = _read_json_object(report_path)
        if number >= 2:
            result_path = _verified_artifact_path(manifest, "result")
            results[number] = read_phk_result(result_path, physical=physical)

    required_results = set(range(2, 9))
    if set(results) != required_results:
        raise PhkRunnerContractError(
            f"terminal PHK bundle must contain results 2..8, got {sorted(results)}"
        )
    comparisons = {
        "coarse_medium": compare_phk_results(results[3], results[4], physical=physical),
        "medium_fine": compare_phk_results(results[4], results[5], physical=physical),
        "medium_medium_half_dt": compare_phk_results(
            results[4], results[6], physical=physical
        ),
        "fine_exact_replay": compare_phk_results(
            results[5], results[7], physical=physical
        ),
    }
    comparison_payload = {
        key: {
            "component_order": list(value.component_order),
            "component_deltas": value.component_deltas.tolist(),
            "finite": value.finite,
        }
        for key, value in comparisons.items()
    }
    replay_max = float(
        np.max(comparisons["fine_exact_replay"].component_deltas)
    )
    replay_limit = float(
        physical.payload["hard_guard_thresholds"][
            "maximum_replay_component_difference"
        ]
    )

    guard_pass = {
        number: bool(report["guard"]["passed"])
        for number, report in reports.items()
        if number >= 2
    }
    event_pass = {
        number: bool(report["event"]["passed"])
        for number, report in reports.items()
        if number >= 3 and report.get("event") is not None
    }
    nominal_peak_temperature = float(np.max(results[4].temperature))
    joule_off_peak_temperature = float(np.max(results[8].temperature))
    nominal_peak_roi = max(
        float(item["peak_roi_fraction"])
        for item in reports[4]["event"]["cycles"]
    )
    joule_off_peak_roi = max(
        float(item["peak_roi_fraction"])
        for item in reports[8]["event"]["cycles"]
    )
    space = comparisons["medium_fine"].component_deltas
    temporal = comparisons["medium_medium_half_dt"].component_deltas
    temperature_joint_uncertainty = 0.45 * float(
        math.sqrt(space[1] * space[1] + temporal[1] * temporal[1])
    )
    phase_joint_uncertainty = 0.5 * float(
        math.sqrt(space[0] * space[0] + temporal[0] * temporal[0])
    )
    thermal_effect = bool(
        nominal_peak_temperature - joule_off_peak_temperature
        > temperature_joint_uncertainty
        and nominal_peak_roi - joule_off_peak_roi > phase_joint_uncertainty
    )
    thermal_effect_payload = {
        "comparison": "Q_NOMINAL_MEDIUM_MINUS_Q_JOULE_OFF_MEDIUM",
        "peak_temperature_difference": (
            nominal_peak_temperature - joule_off_peak_temperature
        ),
        "temperature_joint_space_time_uncertainty": temperature_joint_uncertainty,
        "peak_roi_phase_fraction_difference": nominal_peak_roi - joule_off_peak_roi,
        "phase_joint_space_time_uncertainty": phase_joint_uncertainty,
        "established": thermal_effect,
        "interpretation": (
            "BOUNDED_SYNTHETIC_JOULE_CAUSAL_CONTROL_ONLY_NOT_MATERIAL_VALIDATION"
        ),
    }
    decision = adjudicate_phk_q(
        execution_status_by_intent=statuses,
        guard_pass_by_intent=guard_pass,
        event_pass_by_intent=event_pass,
        manufactured_pass=bool(reports[1]["passed"]),
        replay_max_component_difference=replay_max,
        replay_limit=replay_limit,
        thermal_effect_established=thermal_effect,
    )
    gross_process_cpu_seconds = sum(
        float(manifest["actual_budget"].get("process_cpu_seconds", 0.0))
        for manifest in by_intent.values()
    )
    gross_wall_seconds = sum(
        float(manifest["actual_budget"].get("wall_clock_seconds", 0.0))
        for manifest in by_intent.values()
    )
    failure_records = [
        {
            "intent": number,
            "failure_class": manifest.get("failure_class"),
            "failure_identity": manifest["actual_budget"].get("failure_identity"),
        }
        for number, manifest in sorted(by_intent.items())
        if manifest["execution_status"] == "FAILED"
    ]
    event_payload = {
        str(number): report["event"]
        for number, report in reports.items()
        if report.get("event") is not None
    }
    summary = {
        "schema_id": "phk-v2-q-terminal-summary-v1",
        "program_contract_sha256": physical.program.sha256,
        "object_contract_sha256": physical.object.sha256,
        "split_manifest_sha256": split.file_sha256,
        "source_run_ids": [
            str(by_intent[number]["run_id"]) for number in sorted(by_intent)
        ],
        "execution_status_by_intent": statuses,
        "not_reached_intents": decision["not_reached_intents"],
        "comparisons": comparison_payload,
        "event_reports": event_payload,
        "thermal_effect": thermal_effect_payload,
        "failure_records": failure_records,
        "gross_compute": {
            "process_cpu_seconds": gross_process_cpu_seconds,
            "process_cpu_core_hours": gross_process_cpu_seconds / 3600.0,
            "sum_single_thread_wall_seconds": gross_wall_seconds,
            "failed_intents": len(failure_records),
        },
        "floor_disposition": (
            "NOT_SEALED_FOR_NEURAL_WORK_ORACLE_GATE_FAILED_BEFORE_METHOD_STAGE"
        ),
        "adjudication": decision,
        "claim_status": (
            "PHK_V2_ORACLE_NO_GO_NO_PINN_OR_PHA_OR_KC_OR_FORMAL_EVIDENCE"
        ),
    }

    started_at = _utc_now()
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    run_root = Path(output_root) / run_id
    run_root.mkdir(parents=False, exist_ok=False)
    summary_path = run_root / "summary.json"
    _write_new_json(summary_path, summary)
    artifacts = {
        "summary": str(summary_path),
        "summary_sha256": _sha256(summary_path),
        "program_contract": str(physical.program.path),
        "program_contract_sha256": physical.program.sha256,
        "object_contract": str(physical.object.path),
        "object_contract_sha256": physical.object.sha256,
        "split_manifest": str(split.path),
        "split_manifest_sha256": split.file_sha256,
    }
    evaluator_file = Path(__file__).with_name("phk_evaluator.py")
    manifest = RunManifest(
        run_id=run_id,
        experiment_group_id="phk-v2-q-terminal-adjudication",
        tier="qualification_summary",
        scientific_role="oracle_gate_terminal_adjudication",
        gate="PHK_V2_S2_ORACLE_GATE",
        started_at=started_at,
        ended_at=_utc_now(),
        command=["python", "-m", "pinn_pcm_sci.phk_runner", "summarize-q"],
        execution_status="COMPLETED",
        numerical_validity="VALID_BOUNDED_SYNTHETIC_NEGATIVE_QUALIFICATION",
        gate_outcome=str(decision["outcome"]),
        route_disposition="STOP_BEFORE_PINN_TRAINING_BEGIN_V2_NEGATIVE_CLOSEOUT",
        evidence_identity="TRANSPARENT_DIMENSIONLESS_REDUCED_BENCHMARK",
        claim_status=str(summary["claim_status"]),
        code_identity={
            "kind": "working-tree",
            "phk_runner_sha256": _sha256(Path(__file__)),
            "phk_benchmark_sha256": _sha256(Path(__file__).with_name("phk_benchmark.py")),
            "phk_evaluator_sha256": _sha256(evaluator_file),
        },
        environment={
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "dtype": "float64",
            "device": "cpu",
        },
        physical_contract_id=physical.contract_id,
        split_id=SPLIT_ID,
        method_id="phk-v2-q-bundle-adjudicator-v1",
        case_id="phk-v2-q-terminal-bundle-intents-01-through-09",
        seed=0,
        planned_budget={
            "source_intents": list(range(1, 10)),
            "not_reached_after_failure": [10, 11, 12],
            "method_pool_access": False,
        },
        actual_budget={
            "wall_clock_seconds": time.perf_counter() - wall_start,
            "process_cpu_seconds": time.process_time() - cpu_start,
            "source_process_cpu_core_hours": gross_process_cpu_seconds / 3600.0,
            "source_failed_intents": len(failure_records),
        },
        checkpoint={"id": "NOT_APPLICABLE", "selection": "Q_BUNDLE"},
        evaluator_id="phk-v2-q-adjudication-v1",
        artifacts=artifacts,
        failure_class=None,
        replay_of=None,
        supersedes=None,
    )
    ledger.record(manifest)
    ledger.validate()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="phk-runner")
    subparsers = parser.add_subparsers(dest="command", required=True)
    freeze = subparsers.add_parser("freeze-splits")
    freeze.add_argument("--program", type=Path, required=True)
    freeze.add_argument("--object", dest="object_path", type=Path, required=True)
    freeze.add_argument("--out", type=Path, required=True)
    qualify = subparsers.add_parser("qualify")
    qualify.add_argument("--run-id", required=True)
    qualify.add_argument("--intent", type=int, required=True)
    qualify.add_argument("--program", type=Path, required=True)
    qualify.add_argument("--object", dest="object_path", type=Path, required=True)
    qualify.add_argument("--split", type=Path, required=True)
    qualify.add_argument("--output-root", type=Path, default=Path("outputs/runs"))
    qualify.add_argument(
        "--experiment-root", type=Path, default=Path("docs/experiment")
    )
    summarize = subparsers.add_parser("summarize-q")
    summarize.add_argument("--run-id", required=True)
    summarize.add_argument("--program", type=Path, required=True)
    summarize.add_argument("--object", dest="object_path", type=Path, required=True)
    summarize.add_argument("--split", type=Path, required=True)
    summarize.add_argument("--output-root", type=Path, default=Path("outputs/runs"))
    summarize.add_argument(
        "--experiment-root", type=Path, default=Path("docs/experiment")
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.command == "freeze-splits":
        manifest = run_freeze_splits(
            program_path=arguments.program,
            object_path=arguments.object_path,
            output_path=arguments.out,
        )
        print(
            json.dumps(
                {
                    "status": "PHK_V2_SPLIT_MANIFEST_FROZEN",
                    "manifest_sha256": manifest["manifest_sha256"],
                    "case_count": len(manifest["cases"]),
                    "pool_counts": manifest["pool_counts"],
                },
                sort_keys=True,
            )
        )
        return 0
    if arguments.command == "qualify":
        return run_qualification_intent(
            run_id=arguments.run_id,
            intent_number=arguments.intent,
            program_path=arguments.program,
            object_path=arguments.object_path,
            split_path=arguments.split,
            output_root=arguments.output_root,
            experiment_root=arguments.experiment_root,
        )
    if arguments.command == "summarize-q":
        return run_summarize_q(
            run_id=arguments.run_id,
            program_path=arguments.program,
            object_path=arguments.object_path,
            split_path=arguments.split,
            output_root=arguments.output_root,
            experiment_root=arguments.experiment_root,
        )
    raise AssertionError("unreachable command")


if __name__ == "__main__":
    raise SystemExit(main())
