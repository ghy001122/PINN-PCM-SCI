"""Intent-first process boundary for PHK-V2.1 oracle qualification."""

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
from typing import Any, Mapping, Sequence

import numpy as np
import scipy

from .ledger import ExperimentLedger, RunManifest
from .phk_benchmark import PhkControl, PhkConvergenceReport, PhkGuardReport
from .phk_v21_benchmark import (
    PhkV21CaseSpec,
    PhkV21OracleCase,
    PhkV21OracleResult,
    build_phk_v21_split_manifest,
    compare_phk_v21_results,
    evaluate_phk_v21_event,
    load_phk_v21_physical,
    load_phk_v21_split_manifest,
    phk_v21_resolution,
    read_phk_v21_result,
    run_phk_v21_manufactured_checks,
    write_phk_v21_result,
)
from .phk_v21_evaluator import (
    COMPONENT_ORDER,
    adjudicate_phk_v21_q,
    build_phk_v21_oracle_floor_seal,
    load_phk_v21_oracle_contract,
    validate_phk_v21_oracle_floor_seal,
    write_phk_v21_oracle_floor_seal,
)
from .phk_v21_solver import PhkV21PhaseAlgorithm


EXPERIMENT_GROUP_ID = "phk-v21-oracle-qualification"
SUMMARY_GROUP_ID = "phk-v21-oracle-terminal-adjudication"
ORACLE_METHOD_ID = "phk-v21-independent-cartesian-fv-logit-newton-v1"
SPLIT_ID = "phk-v21-complete-case-split-v1"
AMENDMENT_SCHEMA_ID = "phk-v21-s1-implementation-amendment-v1"
NO_EVENT_CARRIER_DEFECT_ID = "DATACLASS_ASDICT_TUPLE_REJECTED_BY_LIST_ONLY_NO_EVENT_CHECK"
ADJUDICATION_AMENDMENT_SCHEMA_ID = "phk-v21-s1-adjudication-amendment-v1"
COMPONENT_LABEL_DEFECT_ID = "LEGACY_COMPARATOR_LABELS_NOT_CANONICAL_V21_ENDPOINT_LABELS"
LEGACY_COMPONENT_ORDER = (
    "PHASE_FIELD_ROI_RMS",
    "TEMPERATURE_FIELD_ROI_RMS",
    "CURRENT_TRACE_RMS",
    "EVENT_TIME",
    "PHASE_REGION_SYMMETRIC_DIFFERENCE",
    "RECOVERY",
)


class PhkV21RunnerContractError(ValueError):
    """A process request does not consume the exact PHK-V2.1 freeze."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def _validate_run_id(run_id: str) -> None:
    if not run_id or run_id in {".", ".."}:
        raise PhkV21RunnerContractError("run_id is empty or invalid")
    if Path(run_id).name != run_id or any(item in run_id for item in ("/", "\\")):
        raise PhkV21RunnerContractError("run_id must be one filesystem-safe name")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PhkV21RunnerContractError(f"invalid JSON evidence: {path}") from exc
    if not isinstance(payload, dict):
        raise PhkV21RunnerContractError(f"JSON evidence must be an object: {path}")
    return payload


def _write_new_json(path: Path, payload: Mapping[str, Any]) -> None:
    exact = Path(path)
    if not exact.parent.is_dir():
        raise FileNotFoundError(f"output parent does not exist: {exact.parent}")
    encoded = (
        json.dumps(
            payload,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    descriptor = os.open(exact, flags, 0o644)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        exact.unlink(missing_ok=True)
        raise


def _load_bundle(
    *,
    program_path: Path,
    object_path: Path,
    legacy_program_path: Path,
    legacy_object_path: Path,
    split_path: Path,
    oracle_contract_path: Path,
    implementation_amendment_path: Path | None = None,
    adjudication_amendment_path: Path | None = None,
    require_final: bool = True,
) -> tuple[Any, Mapping[str, Any], Mapping[str, Any], Mapping[str, Any] | None]:
    physical = load_phk_v21_physical(
        program_path=program_path,
        object_path=object_path,
        legacy_program_path=legacy_program_path,
        legacy_object_path=legacy_object_path,
    )
    split = load_phk_v21_split_manifest(split_path, physical=physical)
    oracle = load_phk_v21_oracle_contract(
        oracle_contract_path,
        program_sha256=physical.program.sha256,
        object_sha256=physical.object.sha256,
        split_file_sha256=_sha256(split_path),
        split_manifest_sha256=str(split["manifest_sha256"]),
        require_final=require_final,
    )
    if require_final:
        root = Path(program_path).resolve().parents[2]
        bindings = oracle["bindings"]
        for relative, key in (
            ("pinn_pcm_sci/phk_v21_benchmark.py", "benchmark_implementation_sha256"),
            ("pinn_pcm_sci/phk_v21_solver.py", "phase_solver_implementation_sha256"),
            ("pinn_pcm_sci/phk_v21_evaluator.py", "evaluator_implementation_sha256"),
        ):
            if _sha256(root / relative) != bindings[key]:
                raise PhkV21RunnerContractError(
                    f"PHK-V2.1 implementation binding mismatch: {relative}"
                )
        current_runner_sha = _sha256(root / "pinn_pcm_sci/phk_v21_runner.py")
        original_runner_sha = str(bindings["runner_implementation_sha256"])
        amendment: Mapping[str, Any] | None = None
        if current_runner_sha != original_runner_sha:
            if implementation_amendment_path is None:
                raise PhkV21RunnerContractError(
                    "PHK-V2.1 runner drift requires an explicit frozen implementation amendment"
                )
            if adjudication_amendment_path is None:
                amendment = _load_implementation_amendment(
                    implementation_amendment_path,
                    oracle_contract_path=oracle_contract_path,
                    original_runner_sha256=original_runner_sha,
                    amended_runner_sha256=current_runner_sha,
                )
            else:
                declared_first = _read_json(implementation_amendment_path)
                intermediate_runner_sha = str(
                    declared_first.get("amended_runner_sha256", "")
                )
                amendment = _load_implementation_amendment(
                    implementation_amendment_path,
                    oracle_contract_path=oracle_contract_path,
                    original_runner_sha256=original_runner_sha,
                    amended_runner_sha256=intermediate_runner_sha,
                )
                adjudication = _load_adjudication_amendment(
                    adjudication_amendment_path,
                    oracle_contract_path=oracle_contract_path,
                    prior_amendment_path=implementation_amendment_path,
                    previous_runner_sha256=intermediate_runner_sha,
                    amended_runner_sha256=current_runner_sha,
                )
                amendment["adjudication_amendment"] = adjudication
        elif implementation_amendment_path is not None or adjudication_amendment_path is not None:
            raise PhkV21RunnerContractError(
                "PHK-V2.1 implementation amendment is not applicable to the bound runner"
            )
    else:
        amendment = None
    return physical, split, oracle, amendment


def _load_implementation_amendment(
    path: Path,
    *,
    oracle_contract_path: Path,
    original_runner_sha256: str,
    amended_runner_sha256: str,
) -> Mapping[str, Any]:
    payload = _read_json(path)
    exact = {
        "schema_id": AMENDMENT_SCHEMA_ID,
        "status": "FROZEN_BEFORE_CONTINUING_INTENT_03_NO_SOLVER_RERUN",
        "defect_identity": NO_EVENT_CARRIER_DEFECT_ID,
        "original_oracle_contract_sha256": _sha256(oracle_contract_path),
        "original_runner_sha256": original_runner_sha256,
        "amended_runner_sha256": amended_runner_sha256,
        "changes_physics_numerics_thresholds_cases_or_results": False,
        "solver_rerun_authorized": False,
    }
    for key, expected in exact.items():
        if payload.get(key) != expected:
            raise PhkV21RunnerContractError(
                f"PHK-V2.1 implementation amendment mismatch: {key}"
            )
    correction = payload.get("correction")
    if not isinstance(correction, dict):
        raise PhkV21RunnerContractError("PHK-V2.1 amendment lacks correction record")
    required = {
        "qualification_intent": 2,
        "stored_expected_no_event_passed": False,
        "corrected_expected_no_event_passed": True,
        "solver_rerun": False,
    }
    for key, expected in required.items():
        if correction.get(key) != expected:
            raise PhkV21RunnerContractError(
                f"PHK-V2.1 correction mismatch: {key}"
            )
    for key in (
        "run_id",
        "manifest_sha256",
        "report_sha256",
        "result_sha256",
    ):
        value = correction.get(key)
        if not isinstance(value, str) or not value:
            raise PhkV21RunnerContractError(
                f"PHK-V2.1 correction lacks immutable {key}"
            )
    payload["amendment_file_sha256"] = _sha256(path)
    return payload


def _load_adjudication_amendment(
    path: Path,
    *,
    oracle_contract_path: Path,
    prior_amendment_path: Path,
    previous_runner_sha256: str,
    amended_runner_sha256: str,
) -> Mapping[str, Any]:
    payload = _read_json(path)
    exact = {
        "schema_id": ADJUDICATION_AMENDMENT_SCHEMA_ID,
        "status": "FROZEN_BEFORE_FIRST_SUCCESSFUL_TERMINAL_SUMMARY_NO_SOLVER_RERUN",
        "defect_identity": COMPONENT_LABEL_DEFECT_ID,
        "original_oracle_contract_sha256": _sha256(oracle_contract_path),
        "prior_implementation_amendment_sha256": _sha256(prior_amendment_path),
        "previous_runner_sha256": previous_runner_sha256,
        "amended_runner_sha256": amended_runner_sha256,
        "changes_component_values_formulas_order_physics_or_results": False,
        "solver_rerun_authorized": False,
    }
    for key, expected in exact.items():
        if payload.get(key) != expected:
            raise PhkV21RunnerContractError(
                f"PHK-V2.1 adjudication amendment mismatch: {key}"
            )
    mapping = payload.get("label_mapping")
    if not isinstance(mapping, dict):
        raise PhkV21RunnerContractError(
            "PHK-V2.1 adjudication amendment lacks label mapping"
        )
    if tuple(mapping.get("legacy_component_order", ())) != LEGACY_COMPONENT_ORDER:
        raise PhkV21RunnerContractError("legacy component order mapping drift")
    if tuple(mapping.get("canonical_component_order", ())) != COMPONENT_ORDER:
        raise PhkV21RunnerContractError("canonical component order mapping drift")
    payload["amendment_file_sha256"] = _sha256(path)
    return payload


def _qualification_rows(oracle: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    rows = oracle.get("qualification_ladder")
    if not isinstance(rows, list) or len(rows) != 14:
        raise PhkV21RunnerContractError("PHK-V2.1 Q ladder is not exact 14 rows")
    result: list[dict[str, Any]] = []
    for expected, row in enumerate(rows, start=1):
        if not isinstance(row, dict) or row.get("order") != expected:
            raise PhkV21RunnerContractError("PHK-V2.1 Q ladder order drift")
        result.append(dict(row))
    return tuple(result)


def _existing_manifests(experiment_root: Path) -> list[dict[str, Any]]:
    root = Path(experiment_root) / "manifests"
    if not root.exists():
        return []
    result: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json")):
        payload = _read_json(path)
        if payload.get("experiment_group_id") == EXPERIMENT_GROUP_ID:
            result.append(payload)
    return result


def _assert_no_orphans(experiment_root: Path) -> None:
    finalized = {str(item.get("run_id", "")) for item in _existing_manifests(experiment_root)}
    for directory, schema in (
        ("intents", "phk-v21-qualification-intent-v1"),
        ("intent_claims", "phk-v21-qualification-claim-v1"),
    ):
        root = Path(experiment_root) / directory
        if not root.exists():
            continue
        for path in sorted(root.glob("*.json")):
            payload = _read_json(path)
            if payload.get("schema_version") == schema and payload.get("run_id") not in finalized:
                raise PhkV21RunnerContractError(
                    "ORPHAN_PHK_V21_INTENT_RECONCILIATION_REQUIRED: "
                    f"{path}; automatic replay is prohibited"
                )


def _is_reconciled_false_no_event(
    experiment_root: Path,
    manifest: Mapping[str, Any],
    intent_number: int,
    amendment: Mapping[str, Any] | None,
) -> bool:
    if amendment is None:
        return False
    correction = amendment["correction"]
    if int(correction["qualification_intent"]) != intent_number:
        return False
    run_id = str(manifest.get("run_id", ""))
    if run_id != correction["run_id"]:
        return False
    manifest_path = Path(experiment_root) / "manifests" / f"{run_id}.json"
    if _sha256(manifest_path) != correction["manifest_sha256"]:
        return False
    artifacts = manifest.get("artifacts")
    code_identity = manifest.get("code_identity")
    if not isinstance(artifacts, dict) or not isinstance(code_identity, dict):
        return False
    if artifacts.get("report_sha256") != correction["report_sha256"]:
        return False
    if artifacts.get("result_sha256") != correction["result_sha256"]:
        return False
    if code_identity.get("phk_v21_runner_sha256") != amendment["original_runner_sha256"]:
        return False
    report_path = Path(str(artifacts.get("report", "")))
    result_path = Path(str(artifacts.get("result", "")))
    if _sha256(report_path) != correction["report_sha256"]:
        return False
    if _sha256(result_path) != correction["result_sha256"]:
        return False
    report = _read_json(report_path)
    return (
        manifest.get("execution_status") == "COMPLETED"
        and manifest.get("gate_outcome") == "PHK_V21_Q_CASE_NO_GO"
        and report.get("expected_no_event_passed") is False
        and isinstance(report.get("event"), dict)
        and _no_event(report["event"])
    )


def _assert_order(
    experiment_root: Path,
    intent_number: int,
    amendment: Mapping[str, Any] | None = None,
) -> None:
    by_number: dict[int, dict[str, Any]] = {}
    for manifest in _existing_manifests(experiment_root):
        actual = manifest.get("actual_budget")
        if not isinstance(actual, dict) or "qualification_intent" not in actual:
            raise PhkV21RunnerContractError("prior PHK-V2.1 manifest lacks intent identity")
        number = int(actual["qualification_intent"])
        if number in by_number:
            raise PhkV21RunnerContractError("duplicate PHK-V2.1 qualification intent")
        by_number[number] = manifest
    if intent_number in by_number:
        raise PhkV21RunnerContractError("PHK-V2.1 qualification intent already consumed")
    if set(by_number) != set(range(1, intent_number)):
        raise PhkV21RunnerContractError(
            "all prior PHK-V2.1 Q intents must exist exactly once"
        )
    for number, manifest in sorted(by_number.items()):
        if manifest.get("execution_status") != "COMPLETED":
            raise PhkV21RunnerContractError(
                f"prior PHK-V2.1 Q intent {number} failed; route is stopped"
            )
        if str(manifest.get("route_disposition", "")).startswith("STOP") and not _is_reconciled_false_no_event(
            experiment_root, manifest, number, amendment
        ):
            raise PhkV21RunnerContractError(
                f"prior PHK-V2.1 Q intent {number} closed the route"
            )
        if amendment is not None and number > int(amendment["correction"]["qualification_intent"]):
            artifacts = manifest.get("artifacts")
            if not isinstance(artifacts, dict) or artifacts.get(
                "implementation_amendment_sha256"
            ) != amendment["amendment_file_sha256"]:
                raise PhkV21RunnerContractError(
                    f"prior PHK-V2.1 Q intent {number} lacks the active amendment binding"
                )


def _claim(
    experiment_root: Path,
    *,
    run_id: str,
    intent_number: int,
    row: Mapping[str, Any],
    started_at: str,
    contract_hashes: Mapping[str, str],
) -> Path:
    path = (
        Path(experiment_root)
        / "intent_claims"
        / f"phk-v21-q-intent-{intent_number:02d}.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_new_json(
        path,
        {
            "schema_version": "phk-v21-qualification-claim-v1",
            "run_id": run_id,
            "started_at": started_at,
            "qualification_intent": dict(row),
            **dict(contract_hashes),
            "disposition_if_unfinalized": (
                "ORPHAN_PHK_V21_INTENT_RECONCILIATION_REQUIRED_NO_AUTOMATIC_REPLAY"
            ),
        },
    )
    return path


def _control(row: Mapping[str, Any]) -> PhkControl:
    value = row.get("control")
    if not isinstance(value, str):
        raise PhkV21RunnerContractError("PHK-V2.1 Q row lacks control")
    try:
        return PhkControl(value)
    except ValueError as exc:
        raise PhkV21RunnerContractError(f"unknown PHK-V2.1 control: {value}") from exc


def _algorithm(row: Mapping[str, Any]) -> PhkV21PhaseAlgorithm:
    value = row.get("algorithm")
    if not isinstance(value, str):
        raise PhkV21RunnerContractError("PHK-V2.1 Q row lacks phase algorithm")
    try:
        return PhkV21PhaseAlgorithm(value)
    except ValueError as exc:
        raise PhkV21RunnerContractError(f"unknown PHK-V2.1 algorithm: {value}") from exc


def _no_event(report: Mapping[str, Any]) -> bool:
    cycles = report.get("cycles")
    if not isinstance(cycles, (list, tuple)) or len(cycles) != 2:
        return False
    return all(
        isinstance(item, dict)
        and item.get("event_time") is None
        and float(item.get("peak_roi_fraction", math.inf)) == 0.0
        for item in cycles
    )


def _canonicalize_comparison_labels(
    report: PhkConvergenceReport,
) -> PhkConvergenceReport:
    """Map inherited V2 labels to the frozen V2.1 names without moving values."""

    order = tuple(report.component_order)
    if order == COMPONENT_ORDER:
        return report
    if order != LEGACY_COMPONENT_ORDER:
        raise PhkV21RunnerContractError(
            "PHK-V2.1 comparison carries an unknown component order"
        )
    return PhkConvergenceReport(
        component_order=COMPONENT_ORDER,
        component_deltas=np.asarray(report.component_deltas, dtype=np.float64).copy(),
        finite=bool(report.finite),
    )


def _immediate_case_pass(
    intent_number: int,
    report: Mapping[str, Any],
    oracle: Mapping[str, Any],
) -> tuple[bool, str]:
    guard = report.get("guard")
    if not isinstance(guard, dict) or guard.get("passed") is not True:
        return False, "HARD_NUMERICAL_GUARD_FAILED"
    event = report.get("event")
    if not isinstance(event, dict):
        return False, "EVENT_REPORT_MISSING"
    required = {
        row["order"]
        for row in oracle["qualification_ladder"]
        if row["intent_id"]
        in set(oracle["event_and_control_policy"]["nominal_event_required_on"])
    }
    if intent_number in required and event.get("passed") is not True:
        return False, "NOMINAL_TWO_CYCLE_EVENT_GATE_FAILED"
    if intent_number in {2, 9} and not bool(report.get("expected_no_event_passed")):
        return False, "CONTROL_FALSE_EVENT"
    return True, "IMMEDIATE_CASE_GATE_PASS"


def run_qualification_intent(
    *,
    run_id: str,
    intent_number: int,
    program_path: Path,
    object_path: Path,
    legacy_program_path: Path,
    legacy_object_path: Path,
    split_path: Path,
    oracle_contract_path: Path,
    output_root: Path,
    experiment_root: Path,
    implementation_amendment_path: Path | None = None,
    adjudication_amendment_path: Path | None = None,
) -> int:
    """Consume exactly one ordered Q intent and finalize its ledger row."""

    _validate_run_id(run_id)
    physical, split, oracle, amendment = _load_bundle(
        program_path=program_path,
        object_path=object_path,
        legacy_program_path=legacy_program_path,
        legacy_object_path=legacy_object_path,
        split_path=split_path,
        oracle_contract_path=oracle_contract_path,
        implementation_amendment_path=implementation_amendment_path,
        adjudication_amendment_path=adjudication_amendment_path,
    )
    if amendment is not None and "adjudication_amendment" in amendment:
        raise PhkV21RunnerContractError(
            "PHK-V2.1 adjudication amendment is summary-only and cannot open a solver intent"
        )
    rows = _qualification_rows(oracle)
    if not 1 <= intent_number <= 14:
        raise PhkV21RunnerContractError("PHK-V2.1 intent is outside 1..14")
    row = rows[intent_number - 1]
    ledger = ExperimentLedger(experiment_root)
    ledger.validate()
    _assert_no_orphans(experiment_root)
    _assert_order(experiment_root, intent_number, amendment)
    started_at = _utc_now()
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    contract_hashes = {
        "program_contract_sha256": physical.program.sha256,
        "object_contract_sha256": physical.object.sha256,
        "split_file_sha256": _sha256(split_path),
        "split_manifest_sha256": str(split["manifest_sha256"]),
        "oracle_contract_sha256": _sha256(oracle_contract_path),
    }
    if amendment is not None:
        contract_hashes["implementation_amendment_sha256"] = amendment[
            "amendment_file_sha256"
        ]
    claim_path = _claim(
        experiment_root,
        run_id=run_id,
        intent_number=intent_number,
        row=row,
        started_at=started_at,
        contract_hashes=contract_hashes,
    )
    run_root = Path(output_root) / run_id
    run_root.mkdir(parents=False, exist_ok=False)
    intent_path = Path(experiment_root) / "intents" / f"{run_id}.json"
    intent_path.parent.mkdir(parents=True, exist_ok=True)
    intent_payload = {
        "schema_version": "phk-v21-qualification-intent-v1",
        "run_id": run_id,
        "started_at": started_at,
        "qualification_intent": row,
        **contract_hashes,
        "method_pool_access": False,
        "result_adaptive_rescue": False,
    }
    _write_new_json(intent_path, intent_payload)
    artifacts: dict[str, str] = {
        "intent_claim": str(claim_path),
        "intent": str(intent_path),
        "program_contract": str(Path(program_path).resolve()),
        "object_contract": str(Path(object_path).resolve()),
        "split_manifest": str(Path(split_path).resolve()),
        "oracle_contract": str(Path(oracle_contract_path).resolve()),
        **contract_hashes,
    }
    if amendment is not None and implementation_amendment_path is not None:
        artifacts["implementation_amendment"] = str(
            Path(implementation_amendment_path).resolve()
        )
        artifacts["implementation_amendment_sha256"] = amendment[
            "amendment_file_sha256"
        ]
    if (
        amendment is not None
        and "adjudication_amendment" in amendment
        and adjudication_amendment_path is not None
    ):
        artifacts["adjudication_amendment"] = str(
            Path(adjudication_amendment_path).resolve()
        )
        artifacts["adjudication_amendment_sha256"] = amendment[
            "adjudication_amendment"
        ]["amendment_file_sha256"]
    if amendment is not None and implementation_amendment_path is not None:
        artifacts["implementation_amendment"] = str(
            Path(implementation_amendment_path).resolve()
        )
        artifacts["implementation_amendment_sha256"] = amendment[
            "amendment_file_sha256"
        ]
    failure: BaseException | None = None
    solver_statistics: dict[str, int | float] = {}
    gate_outcome = "PHK_V21_Q_EXECUTION_FAILED"
    route_disposition = "STOP_OR_EXPLICIT_RECONCILIATION"
    numerical_validity = "NOT_EVALUATED"
    case_id = str(row["intent_id"])
    try:
        if intent_number == 1:
            report = run_phk_v21_manufactured_checks(physical)
            immediate_pass = bool(report["passed"])
            gate_outcome = (
                "PHK_V21_Q_MANUFACTURED_PASS"
                if immediate_pass
                else "PHK_V21_Q_MANUFACTURED_NO_GO"
            )
            route_disposition = (
                "CONTINUE_PHK_V21_Q_INTENT_02"
                if immediate_pass
                else "STOP_PHK_V21_ORACLE_ROUTE"
            )
            numerical_validity = "VALID_NO_SCIENTIFIC_FIELD_RESULT"
        else:
            control = _control(row)
            algorithm = _algorithm(row)
            case = PhkV21CaseSpec.nominal(physical, control=control)
            resolution = phk_v21_resolution(
                physical,
                str(row["resolution"]),
                period=case.period,
            )
            result = PhkV21OracleCase(
                physical=physical,
                case=case,
                resolution=resolution,
                phase_algorithm=algorithm,
            ).solve()
            solver_statistics = dict(result.solver_statistics)
            guard = PhkGuardReport.from_result(result, physical=physical)
            event = evaluate_phk_v21_event(result, physical=physical)
            event_payload = asdict(event)
            expected_no_event = _no_event(event_payload) if intent_number in {2, 9} else None
            report = {
                "schema_id": "phk-v21-q-case-report-v1",
                "intent": row,
                "case_id": case.case_id,
                "resolution": asdict(resolution),
                "phase_algorithm": algorithm.value,
                "guard": asdict(guard),
                "event": event_payload,
                "expected_no_event_passed": expected_no_event,
                "solver_statistics": solver_statistics,
                "single_case_adjudication": "PENDING_COMPLETE_Q_LADDER",
                "claim_status": "NO_ORACLE_OR_METHOD_CLAIM_SINGLE_CASE_ONLY",
            }
            immediate_pass, immediate_reason = _immediate_case_pass(
                intent_number, report, oracle
            )
            report["immediate_gate_passed"] = immediate_pass
            report["immediate_gate_reason"] = immediate_reason
            result_path = run_root / f"result-intent-{intent_number:02d}.npz"
            write_phk_v21_result(result_path, result)
            artifacts["result"] = str(result_path)
            artifacts["result_sha256"] = _sha256(result_path)
            gate_outcome = (
                "PHK_V21_Q_CASE_COMPLETED"
                if immediate_pass
                else "PHK_V21_Q_CASE_NO_GO"
            )
            route_disposition = (
                f"CONTINUE_PHK_V21_Q_INTENT_{intent_number + 1:02d}"
                if immediate_pass and intent_number < 14
                else (
                    "AWAIT_COMPLETE_PHK_V21_Q_ADJUDICATION"
                    if immediate_pass
                    else "STOP_PHK_V21_ORACLE_ROUTE"
                )
            )
            numerical_validity = (
                "VALID_PENDING_COMPLETE_Q_LADDER"
                if guard.passed
                else "INVALID_HARD_NUMERICAL_GUARD"
            )
            case_id = case.case_id
        report_path = run_root / "report.json"
        _write_new_json(report_path, report)
        artifacts["report"] = str(report_path)
        artifacts["report_sha256"] = _sha256(report_path)
    except BaseException as exc:
        failure = exc

    wall_seconds = time.perf_counter() - wall_start
    cpu_seconds = time.process_time() - cpu_start
    failure_identity = None if failure is None else f"{type(failure).__name__}: {failure}"
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
            "NONE_AUTOMATIC_RECONCILIATION_REQUIRED"
            if failure
            else "NOT_APPLICABLE"
        ),
        **solver_statistics,
    }
    execution_status = "FAILED" if failure else "COMPLETED"
    if failure:
        gate_outcome = "PHK_V21_Q_EXECUTION_FAILED"
        route_disposition = "STOP_OR_EXPLICIT_RECONCILIATION"
        numerical_validity = "NOT_EVALUATED"
    manifest = RunManifest(
        run_id=run_id,
        experiment_group_id=EXPERIMENT_GROUP_ID,
        tier="qualification",
        scientific_role=(
            "manufactured_operator_check" if intent_number == 1 else "oracle_qualification"
        ),
        gate="PHK_V21_S1_Q",
        started_at=started_at,
        ended_at=_utc_now(),
        command=[
            "python",
            "-m",
            "pinn_pcm_sci.phk_v21_runner",
            "qualify",
            "--run-id",
            run_id,
            "--intent",
            str(intent_number),
        ],
        execution_status=execution_status,
        numerical_validity=numerical_validity,
        gate_outcome=gate_outcome,
        route_disposition=route_disposition,
        evidence_identity=(
            "MANUFACTURED_NO_SCIENTIFIC_FIELD_RESULT"
            if intent_number == 1
            else "TRANSPARENT_DIMENSIONLESS_SYNTHETIC_BENCHMARK"
        ),
        claim_status=(
            "NO_ORACLE_OR_METHOD_CLAIM_EXECUTION_FAILURE"
            if failure
            else "NO_ORACLE_OR_METHOD_CLAIM_SINGLE_INTENT_ONLY"
        ),
        code_identity={
            "kind": "pre-voting-byte-bound",
            "phk_v21_runner_sha256": _sha256(Path(__file__)),
            "phk_v21_benchmark_sha256": _sha256(
                Path(__file__).with_name("phk_v21_benchmark.py")
            ),
            "phk_v21_evaluator_sha256": _sha256(
                Path(__file__).with_name("phk_v21_evaluator.py")
            ),
            "phk_v21_solver_sha256": _sha256(
                Path(__file__).with_name("phk_v21_solver.py")
            ),
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
            "oracle_cpu_process_core_hour_cap": float(
                oracle["execution_order_and_accounting"][
                    "oracle_cpu_process_core_hour_cap"
                ]
            ),
            "failed_intents_count_against_budget": True,
            "result_adaptive_rescue": False,
        },
        actual_budget=actual_budget,
        checkpoint={"id": "NOT_APPLICABLE", "selection": "INDEPENDENT_CPU_ORACLE"},
        evaluator_id="phk-v21-q-event-guard-convergence-evaluator-v1",
        artifacts=artifacts,
        failure_class=None if failure is None else type(failure).__name__,
        replay_of=("Q_NOMINAL_FINE" if intent_number == 8 else None),
        supersedes=None,
    )
    ledger.record(manifest)
    ledger.validate()
    return 1 if failure else 0


def _verified_artifact(manifest: Mapping[str, Any], key: str) -> Path:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise PhkV21RunnerContractError("PHK-V2.1 manifest lacks artifacts")
    value = artifacts.get(key)
    declared = artifacts.get(f"{key}_sha256")
    if not isinstance(value, str) or not isinstance(declared, str):
        raise PhkV21RunnerContractError(f"PHK-V2.1 manifest lacks {key} identity")
    path = Path(value)
    if not path.is_file() or _sha256(path) != declared:
        raise PhkV21RunnerContractError(f"PHK-V2.1 {key} hash mismatch")
    return path


def _max_result_difference(
    first: PhkV21OracleResult,
    second: PhkV21OracleResult,
) -> float:
    names = (
        "time",
        "potential",
        "temperature",
        "phase",
        "top_current",
        "bottom_current",
        "joule_power",
        "current_balance_history",
        "thermal_residual_history",
        "phase_residual_history",
        "coupled_change_history",
        "linear_residual_history",
    )
    values: list[float] = []
    for name in names:
        first_array = np.asarray(getattr(first, name), dtype=np.float64)
        second_array = np.asarray(getattr(second, name), dtype=np.float64)
        if first_array.shape != second_array.shape:
            return float("inf")
        values.append(float(np.max(np.abs(first_array - second_array))))
    return max(values)


def run_summarize_q(
    *,
    run_id: str,
    program_path: Path,
    object_path: Path,
    legacy_program_path: Path,
    legacy_object_path: Path,
    split_path: Path,
    oracle_contract_path: Path,
    output_root: Path,
    experiment_root: Path,
    implementation_amendment_path: Path | None = None,
    adjudication_amendment_path: Path | None = None,
) -> int:
    """Adjudicate the ordered Q prefix without opening any neural case pool."""

    _validate_run_id(run_id)
    physical, split, oracle, amendment = _load_bundle(
        program_path=program_path,
        object_path=object_path,
        legacy_program_path=legacy_program_path,
        legacy_object_path=legacy_object_path,
        split_path=split_path,
        oracle_contract_path=oracle_contract_path,
        implementation_amendment_path=implementation_amendment_path,
        adjudication_amendment_path=adjudication_amendment_path,
    )
    ledger = ExperimentLedger(experiment_root)
    ledger.validate()
    _assert_no_orphans(experiment_root)
    by_intent: dict[int, dict[str, Any]] = {}
    contract_hashes = {
        "program_contract_sha256": physical.program.sha256,
        "object_contract_sha256": physical.object.sha256,
        "split_file_sha256": _sha256(split_path),
        "split_manifest_sha256": str(split["manifest_sha256"]),
        "oracle_contract_sha256": _sha256(oracle_contract_path),
    }
    for manifest in _existing_manifests(experiment_root):
        actual = manifest.get("actual_budget")
        if not isinstance(actual, dict) or "qualification_intent" not in actual:
            raise PhkV21RunnerContractError("PHK-V2.1 case manifest lacks intent")
        number = int(actual["qualification_intent"])
        if number in by_intent:
            raise PhkV21RunnerContractError("duplicate PHK-V2.1 Q intent")
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, dict):
            raise PhkV21RunnerContractError("PHK-V2.1 case manifest lacks artifacts")
        for key, expected in contract_hashes.items():
            if artifacts.get(key) != expected:
                raise PhkV21RunnerContractError(
                    f"PHK-V2.1 case manifest {number} has stale {key}"
                )
        if amendment is not None and number > int(amendment["correction"]["qualification_intent"]):
            if artifacts.get("implementation_amendment_sha256") != amendment[
                "amendment_file_sha256"
            ]:
                raise PhkV21RunnerContractError(
                    f"PHK-V2.1 case manifest {number} lacks the active amendment binding"
                )
        by_intent[number] = manifest
    if not by_intent or set(by_intent) != set(range(1, max(by_intent) + 1)):
        raise PhkV21RunnerContractError("PHK-V2.1 Q bundle is not a contiguous prefix")
    last = by_intent[max(by_intent)]
    complete = set(by_intent) == set(range(1, 15))
    terminal_prefix = (
        last.get("execution_status") == "FAILED"
        or (
            str(last.get("route_disposition", "")).startswith("STOP")
            and not _is_reconciled_false_no_event(
                experiment_root, last, max(by_intent), amendment
            )
        )
    )
    if not (complete or terminal_prefix):
        raise PhkV21RunnerContractError(
            "PHK-V2.1 Q summary requires all 14 intents or a terminal stopped prefix"
        )

    statuses = {
        number: str(manifest["execution_status"])
        for number, manifest in by_intent.items()
    }
    reports: dict[int, dict[str, Any]] = {}
    results: dict[int, PhkV21OracleResult] = {}
    for number, manifest in sorted(by_intent.items()):
        if manifest["execution_status"] != "COMPLETED":
            continue
        reports[number] = _read_json(_verified_artifact(manifest, "report"))
        if number >= 2:
            results[number] = read_phk_v21_result(
                _verified_artifact(manifest, "result"),
                physical=physical,
            )
    guard_pass = {
        number: bool(report["guard"]["passed"])
        for number, report in reports.items()
        if number >= 2
    }
    event_pass = {
        number: bool(report["event"]["passed"])
        for number, report in reports.items()
        if number in {3, 4, 5, 6, 7, 8, 14}
    }
    zero_no_event = bool(reports.get(2, {}).get("expected_no_event_passed", False))
    if 2 in by_intent and _is_reconciled_false_no_event(
        experiment_root, by_intent[2], 2, amendment
    ):
        zero_no_event = _no_event(reports[2]["event"])
    joule_no_event = bool(reports.get(9, {}).get("expected_no_event_passed", False))
    replay_limit = float(
        oracle["numerical_guard_policy"]["maximum_exact_replay_array_difference"]
    )
    replay_max = (
        _max_result_difference(results[5], results[8])
        if 5 in results and 8 in results
        else float("inf")
    )
    comparisons_payload: dict[str, Any] = {}
    floor: dict[str, Any] | None = None
    floor_path: Path | None = None
    if complete and all(manifest["execution_status"] == "COMPLETED" for manifest in by_intent.values()):
        comparisons = {
            "medium_fine": _canonicalize_comparison_labels(
                compare_phk_v21_results(results[4], results[5], physical=physical)
            ),
            "fine_extra_fine": _canonicalize_comparison_labels(
                compare_phk_v21_results(results[5], results[6], physical=physical)
            ),
            "medium_half_dt": _canonicalize_comparison_labels(
                compare_phk_v21_results(results[4], results[7], physical=physical)
            ),
            "fine_replay": _canonicalize_comparison_labels(
                compare_phk_v21_results(results[5], results[8], physical=physical)
            ),
            "medium_solver_crosscheck": _canonicalize_comparison_labels(
                compare_phk_v21_results(results[4], results[14], physical=physical)
            ),
        }
        comparisons_payload = {
            key: {
                "component_order": list(value.component_order),
                "component_deltas": value.component_deltas.tolist(),
                "finite": value.finite,
            }
            for key, value in comparisons.items()
        }
        floor = build_phk_v21_oracle_floor_seal(
            oracle_contract=oracle,
            medium_fine=comparisons["medium_fine"],
            fine_extra_fine=comparisons["fine_extra_fine"],
            medium_half_dt=comparisons["medium_half_dt"],
            fine_replay=comparisons["fine_replay"],
            medium_solver_crosscheck=comparisons["medium_solver_crosscheck"],
            source_run_ids=[str(by_intent[index]["run_id"]) for index in range(1, 15)],
        )
        validate_phk_v21_oracle_floor_seal(floor, oracle_contract=oracle)

    decision = adjudicate_phk_v21_q(
        execution_status_by_intent=statuses,
        guard_pass_by_intent=guard_pass,
        event_pass_by_intent=event_pass,
        manufactured_pass=bool(reports.get(1, {}).get("passed", False)),
        zero_drive_no_event=zero_no_event,
        joule_off_no_event=joule_no_event,
        replay_max_array_difference=replay_max,
        replay_limit=replay_limit,
        floor_seal=floor,
    )
    started_at = _utc_now()
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    run_root = Path(output_root) / run_id
    run_root.mkdir(parents=False, exist_ok=False)
    if floor is not None:
        floor_path = run_root / "oracle-floor-seal.json"
        write_phk_v21_oracle_floor_seal(floor_path, floor)
    gross_cpu = sum(
        float(item["actual_budget"].get("process_cpu_seconds", 0.0))
        for item in by_intent.values()
    )
    gross_wall = sum(
        float(item["actual_budget"].get("wall_clock_seconds", 0.0))
        for item in by_intent.values()
    )
    failure_records = [
        {
            "intent": number,
            "failure_class": item.get("failure_class"),
            "failure_identity": item["actual_budget"].get("failure_identity"),
        }
        for number, item in sorted(by_intent.items())
        if item["execution_status"] == "FAILED"
    ]
    summary = {
        "schema_id": "phk-v21-q-terminal-summary-v1",
        **contract_hashes,
        "source_run_ids": [str(by_intent[index]["run_id"]) for index in sorted(by_intent)],
        "execution_status_by_intent": statuses,
        "not_reached_intents": decision["not_reached_intents"],
        "comparisons": comparisons_payload,
        "event_reports": {
            str(number): report["event"]
            for number, report in reports.items()
            if number >= 2
        },
        "control_outcomes": {
            "zero_drive_no_event": zero_no_event,
            "joule_gain_zero_no_event": joule_no_event,
            "other_control_event_status_is_recorded_not_forced": True,
        },
        "implementation_amendment": (
            {
                "amendment_id": amendment.get("amendment_id"),
                "amendment_file_sha256": amendment["amendment_file_sha256"],
                "reconciled_intent": amendment["correction"]["qualification_intent"],
                "solver_rerun": False,
                "adjudication_amendment": (
                    {
                        "amendment_id": amendment["adjudication_amendment"].get(
                            "amendment_id"
                        ),
                        "amendment_file_sha256": amendment[
                            "adjudication_amendment"
                        ]["amendment_file_sha256"],
                        "component_values_reordered": False,
                        "solver_rerun": False,
                    }
                    if "adjudication_amendment" in amendment
                    else None
                ),
            }
            if amendment is not None
            else None
        ),
        "replay_max_array_difference": (
            replay_max if math.isfinite(replay_max) else None
        ),
        "floor_seal": floor,
        "failure_records": failure_records,
        "gross_compute": {
            "process_cpu_seconds": gross_cpu,
            "process_cpu_core_hours": gross_cpu / 3600.0,
            "sum_single_thread_wall_seconds": gross_wall,
            "failed_intents": len(failure_records),
        },
        "adjudication": decision,
        "claim_status": (
            "PHK_V21_SYNTHETIC_ORACLE_QUALIFIED_NO_PINN_OR_METHOD_EVIDENCE"
            if decision["oracle_qualified"]
            else "PHK_V21_ORACLE_NO_GO_NO_PINN_OR_METHOD_EVIDENCE"
        ),
    }
    summary_path = run_root / "summary.json"
    _write_new_json(summary_path, summary)
    artifacts: dict[str, str] = {
        "summary": str(summary_path),
        "summary_sha256": _sha256(summary_path),
        "program_contract": str(Path(program_path).resolve()),
        "object_contract": str(Path(object_path).resolve()),
        "split_manifest": str(Path(split_path).resolve()),
        "oracle_contract": str(Path(oracle_contract_path).resolve()),
        **contract_hashes,
    }
    if amendment is not None and implementation_amendment_path is not None:
        artifacts["implementation_amendment"] = str(
            Path(implementation_amendment_path).resolve()
        )
        artifacts["implementation_amendment_sha256"] = amendment[
            "amendment_file_sha256"
        ]
    if (
        amendment is not None
        and "adjudication_amendment" in amendment
        and adjudication_amendment_path is not None
    ):
        artifacts["adjudication_amendment"] = str(
            Path(adjudication_amendment_path).resolve()
        )
        artifacts["adjudication_amendment_sha256"] = amendment[
            "adjudication_amendment"
        ]["amendment_file_sha256"]
    if floor_path is not None:
        artifacts["oracle_floor_seal"] = str(floor_path)
        artifacts["oracle_floor_seal_sha256"] = _sha256(floor_path)
    manifest = RunManifest(
        run_id=run_id,
        experiment_group_id=SUMMARY_GROUP_ID,
        tier="qualification_summary",
        scientific_role="oracle_gate_terminal_adjudication",
        gate="PHK_V21_S1_ORACLE_GATE",
        started_at=started_at,
        ended_at=_utc_now(),
        command=["python", "-m", "pinn_pcm_sci.phk_v21_runner", "summarize-q"],
        execution_status="COMPLETED",
        numerical_validity=(
            "VALID_BOUNDED_SYNTHETIC_ORACLE_QUALIFICATION"
            if decision["oracle_qualified"]
            else "VALID_BOUNDED_SYNTHETIC_NEGATIVE_QUALIFICATION"
        ),
        gate_outcome=str(decision["outcome"]),
        route_disposition=(
            "CONTINUE_TO_BASELINE_REPLICATION"
            if decision["oracle_qualified"]
            else "STOP_BEFORE_PINN_TRAINING"
        ),
        evidence_identity="TRANSPARENT_DIMENSIONLESS_SYNTHETIC_BENCHMARK",
        claim_status=str(summary["claim_status"]),
        code_identity={
            "kind": "pre-voting-byte-bound",
            "phk_v21_runner_sha256": _sha256(Path(__file__)),
            "phk_v21_benchmark_sha256": _sha256(
                Path(__file__).with_name("phk_v21_benchmark.py")
            ),
            "phk_v21_evaluator_sha256": _sha256(
                Path(__file__).with_name("phk_v21_evaluator.py")
            ),
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
        method_id="phk-v21-q-bundle-adjudicator-v1",
        case_id=f"phk-v21-q-terminal-prefix-01-through-{max(by_intent):02d}",
        seed=0,
        planned_budget={"source_intents": list(range(1, max(by_intent) + 1)), "method_pool_access": False},
        actual_budget={
            "wall_clock_seconds": time.perf_counter() - wall_start,
            "process_cpu_seconds": time.process_time() - cpu_start,
            "source_process_cpu_core_hours": gross_cpu / 3600.0,
            "source_failed_intents": len(failure_records),
        },
        checkpoint={"id": "NOT_APPLICABLE", "selection": "Q_BUNDLE"},
        evaluator_id="phk-v21-q-adjudication-v1",
        artifacts=artifacts,
        failure_class=None,
        replay_of=None,
        supersedes=None,
    )
    ledger.record(manifest)
    ledger.validate()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="phk-v21-runner")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("qualify", "summarize-q"):
        command = subparsers.add_parser(name)
        command.add_argument("--run-id", required=True)
        if name == "qualify":
            command.add_argument("--intent", type=int, required=True)
        command.add_argument("--program", type=Path, required=True)
        command.add_argument("--object", dest="object_path", type=Path, required=True)
        command.add_argument("--legacy-program", type=Path, required=True)
        command.add_argument("--legacy-object", type=Path, required=True)
        command.add_argument("--split", type=Path, required=True)
        command.add_argument("--oracle-contract", type=Path, required=True)
        command.add_argument("--implementation-amendment", type=Path)
        command.add_argument("--adjudication-amendment", type=Path)
        command.add_argument("--output-root", type=Path, default=Path("outputs/runs"))
        command.add_argument("--experiment-root", type=Path, default=Path("docs/experiment"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    common = {
        "run_id": args.run_id,
        "program_path": args.program,
        "object_path": args.object_path,
        "legacy_program_path": args.legacy_program,
        "legacy_object_path": args.legacy_object,
        "split_path": args.split,
        "oracle_contract_path": args.oracle_contract,
        "implementation_amendment_path": args.implementation_amendment,
        "adjudication_amendment_path": args.adjudication_amendment,
        "output_root": args.output_root,
        "experiment_root": args.experiment_root,
    }
    if args.command == "qualify":
        return run_qualification_intent(intent_number=args.intent, **common)
    if args.command == "summarize-q":
        return run_summarize_q(**common)
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "PhkV21RunnerContractError",
    "build_parser",
    "main",
    "run_qualification_intent",
    "run_summarize_q",
]
