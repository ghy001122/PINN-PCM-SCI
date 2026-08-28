"""Intent-first process adapter for the PHK-V2.1 engineering campaign."""

from __future__ import annotations

import argparse
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import time
from typing import Any, Sequence

import numpy as np
import scipy

from .ledger import ExperimentLedger, RunManifest
from .phk_benchmark import PhkControl, PhkPhysicalContract, PhkResolution
from .phk_v21_design import (
    PhkV21CandidateOutcome,
    PhkV21DesignCase,
    build_stage1_cases,
    build_stage2_cases,
    select_medium_promotions,
    select_nominal_medium,
    select_stage1_parents,
)
from .phk_v21_engineering import run_engineering_case
from .phk_v21_solver import PhkV21PhaseAlgorithm


EXPERIMENT_GROUP_ID = "phk-v21-engineering-object-search"
METHOD_ID = "phk-v21-logit-newton-independent-engineering-v1"
PHYSICAL_CONTRACT_ID = "PHK_V21_ENGINEERING_CANDIDATE_UNIVERSE_V1"
SPLIT_ID = "NOT_APPLICABLE_NON_VOTING_ENGINEERING_SEARCH"


class PhkV21DesignRunnerError(ValueError):
    """The campaign request does not consume the exact engineering chain."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PhkV21DesignRunnerError(f"invalid PHK-V2.1 JSON: {path}") from exc
    if not isinstance(value, dict):
        raise PhkV21DesignRunnerError(f"PHK-V2.1 JSON must be an object: {path}")
    return value


def _write_new_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    descriptor = os.open(path, flags, 0o644)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _append_json_line(path: Path, value: dict[str, Any]) -> None:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        allow_nan=False,
    )
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(encoded + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _validate_run_id(run_id: str) -> None:
    if not run_id or Path(run_id).name != run_id or any(
        item in run_id for item in ("/", "\\")
    ):
        raise PhkV21DesignRunnerError("run_id must be one filesystem-safe name")


def _resolution(case: PhkV21DesignCase, name: str) -> PhkResolution:
    if name == "coarse":
        return PhkResolution.non_scientific_fixture(
            nx=40,
            nz=20,
            dt=0.005,
            time_end=2.0 * case.overrides.period,
            save_every=2,
        )
    if name == "medium":
        return PhkResolution.non_scientific_fixture(
            nx=80,
            nz=40,
            dt=0.0025,
            time_end=2.0 * case.overrides.period,
            save_every=2,
        )
    raise PhkV21DesignRunnerError(f"unsupported engineering resolution: {name}")


def _run_candidate(
    *,
    legacy: PhkPhysicalContract,
    program_path: Path,
    case: PhkV21DesignCase,
    resolution_name: str,
    control: PhkControl,
) -> tuple[PhkV21CandidateOutcome, dict[str, Any]]:
    resolution = _resolution(case, resolution_name)
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    run = None
    failure: BaseException | None = None
    try:
        run = run_engineering_case(
            legacy=legacy,
            phk_v21_program_path=program_path,
            overrides=case.overrides,
            control=control,
            resolution=resolution,
            algorithm=PhkV21PhaseAlgorithm.LOGIT_NEWTON_ANALYTIC_JACOBIAN,
        )
    except BaseException as exc:
        failure = exc
    cpu_seconds = time.process_time() - cpu_start
    wall_seconds = time.perf_counter() - wall_start
    if failure is None:
        assert run is not None
        outcome = PhkV21CandidateOutcome.completed(
            case=case,
            run=run,
            process_cpu_seconds=cpu_seconds,
        )
        detail = {
            "event": asdict(run.event),
            "guard": asdict(run.guard),
            "phase_solver_statistics": dict(run.phase_solver_statistics),
        }
    else:
        identity = f"{type(failure).__name__}: {failure}"
        outcome = PhkV21CandidateOutcome.failed(
            case=case,
            failure_identity=identity,
            process_cpu_seconds=cpu_seconds,
        )
        detail = {"failure_identity": identity}
    record = {
        "schema_id": "phk-v21-engineering-case-record-v1",
        "evidence_identity": "NON_VOTING_ENGINEERING_ONLY",
        "resolution_name": resolution_name,
        "resolution": asdict(resolution),
        "control": control.value,
        "wall_clock_seconds": wall_seconds,
        "outcome": outcome.to_json_dict(),
        **detail,
    }
    return outcome, record


def _control_case(
    selected: PhkV21CandidateOutcome,
    control: PhkControl,
) -> PhkV21DesignCase:
    overrides = replace(
        selected.case.overrides,
        case_id=f"{selected.case.overrides.case_id}_{control.value}",
    )
    identity = hashlib.sha256(
        json.dumps(
            {
                "selected_physical_identity_sha256": (
                    selected.case.physical_identity_sha256
                ),
                "control": control.value,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest().upper()
    return PhkV21DesignCase(
        stage="CONTROL",
        parent_case_id=selected.case.overrides.case_id,
        physical_identity_sha256=identity,
        overrides=overrides,
    )


def _verify_bindings(
    *,
    program_path: Path,
    engineering_path: Path,
    selection_path: Path,
) -> tuple[dict[str, Any], dict[str, str]]:
    program = _read_json(program_path)
    engineering = _read_json(engineering_path)
    selection = _read_json(selection_path)
    hashes = {
        "program_contract_sha256": _sha256(program_path),
        "engineering_contract_sha256": _sha256(engineering_path),
        "e1_solver_selection_sha256": _sha256(selection_path),
    }
    expected = selection.get("contract_bindings")
    if not isinstance(expected, dict):
        raise PhkV21DesignRunnerError("E1 selection lacks contract bindings")
    if expected.get("program_contract_sha256") != hashes["program_contract_sha256"]:
        raise PhkV21DesignRunnerError("PHK-V2.1 program contract drift after E1")
    if (
        expected.get("engineering_contract_sha256_current")
        != hashes["engineering_contract_sha256"]
    ):
        raise PhkV21DesignRunnerError("PHK-V2.1 engineering contract drift after E1")
    if (
        selection.get("selection_verdict")
        != "PHK_V21_E1_PASS_LOGIT_NEWTON_FIXED_FOR_ENGINEERING_OBJECT_SEARCH"
    ):
        raise PhkV21DesignRunnerError("PHK-V2.1 E1 selection is not a PASS")
    if program.get("contract_id") != "PHK_V21_REPEATABLE_EVENT_PROGRAM_V1":
        raise PhkV21DesignRunnerError("unsupported PHK-V2.1 program identity")
    if engineering.get("contract_id") != "PHK_V21_ENGINEERING_SANDBOX_V1":
        raise PhkV21DesignRunnerError("unsupported PHK-V2.1 engineering identity")
    return engineering, hashes


def run_campaign(
    *,
    run_id: str,
    program_path: Path,
    engineering_path: Path,
    selection_path: Path,
    legacy_program_path: Path,
    legacy_object_path: Path,
    output_root: Path,
    experiment_root: Path,
) -> int:
    """Execute the complete preregistered E2 campaign exactly once."""

    _validate_run_id(run_id)
    engineering, hashes = _verify_bindings(
        program_path=program_path,
        engineering_path=engineering_path,
        selection_path=selection_path,
    )
    legacy = PhkPhysicalContract.from_files(
        program_path=legacy_program_path,
        object_path=legacy_object_path,
    )
    expected_legacy = _read_json(selection_path)["contract_bindings"]
    legacy_source = Path(__file__).with_name("phk_benchmark.py")
    if _sha256(legacy_source) != expected_legacy["legacy_phk_v2_implementation_sha256"]:
        raise PhkV21DesignRunnerError("historical PHK-V2 implementation drift")

    run_root = Path(output_root) / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    journal_path = run_root / "case-records.jsonl"
    started_at = _utc_now()
    intent_path = Path(experiment_root) / "intents" / f"{run_id}.json"
    intent = {
        "schema_version": "phk-v21-engineering-campaign-intent-v1",
        "run_id": run_id,
        "started_at": started_at,
        "evidence_identity": "NON_VOTING_ENGINEERING_ONLY",
        "program_contract_sha256": hashes["program_contract_sha256"],
        "engineering_contract_sha256": hashes["engineering_contract_sha256"],
        "e1_solver_selection_sha256": hashes["e1_solver_selection_sha256"],
        "algorithm": PhkV21PhaseAlgorithm.LOGIT_NEWTON_ANALYTIC_JACOBIAN.value,
        "stage_1_cases": 16,
        "stage_2_cases": 16,
        "medium_promotions": 3,
        "selected_candidate_controls": 6,
        "scientific_claims_from_campaign": False,
        "result_adaptive_replacement": False,
    }
    _write_new_json(intent_path, intent)

    campaign_wall_start = time.perf_counter()
    campaign_cpu_start = time.process_time()
    case_records = 0
    failed_records = 0

    def execute(
        case: PhkV21DesignCase,
        *,
        role: str,
        resolution_name: str,
        control: PhkControl = PhkControl.FULL,
    ) -> PhkV21CandidateOutcome:
        nonlocal case_records, failed_records
        outcome, record = _run_candidate(
            legacy=legacy,
            program_path=program_path,
            case=case,
            resolution_name=resolution_name,
            control=control,
        )
        record["campaign_role"] = role
        record["ordinal"] = case_records + 1
        record.update(hashes)
        _append_json_line(journal_path, record)
        case_records += 1
        if outcome.execution_status != "COMPLETED":
            failed_records += 1
        print(
            json.dumps(
                {
                    "role": role,
                    "ordinal": case_records,
                    "case_id": case.overrides.case_id,
                    "execution": outcome.execution_status,
                    "guard": outcome.numerical_guard_passed,
                    "event": outcome.event_contract_passed,
                    "score": outcome.event_and_locality_guards_passed_count,
                    "minimum_recovery": (
                        outcome.minimum_cycle_recovery
                        if np.isfinite(outcome.minimum_cycle_recovery)
                        else None
                    ),
                },
                sort_keys=True,
            ),
            flush=True,
        )
        return outcome

    stage1_cases = build_stage1_cases(engineering_path)
    stage1 = tuple(
        execute(case, role="STAGE1_COARSE", resolution_name="coarse")
        for case in stage1_cases
    )
    parents = select_stage1_parents(stage1)
    stage2_cases = build_stage2_cases(engineering_path, parents)
    stage2 = tuple(
        execute(case, role="STAGE2_COARSE", resolution_name="coarse")
        for case in stage2_cases
    )
    promotions = select_medium_promotions(stage2)
    medium = tuple(
        execute(
            item.case,
            role="STAGE2_MEDIUM_PROMOTION",
            resolution_name="medium",
        )
        for item in promotions
    )
    selected = select_nominal_medium(medium)

    control_records: list[dict[str, Any]] = []
    controls_passed = False
    controls = tuple(
        PhkControl(item)
        for item in engineering["p1_search"]["final_candidate_controls"]
    )
    if selected is not None:
        for control in controls:
            case = _control_case(selected, control)
            outcome = execute(
                case,
                role="SELECTED_MEDIUM_CONTROL",
                resolution_name="medium",
                control=control,
            )
            control_records.append(
                {
                    "control": control.value,
                    "case_id": case.overrides.case_id,
                    "execution_status": outcome.execution_status,
                    "numerical_guard_passed": outcome.numerical_guard_passed,
                    "event_contract_passed": outcome.event_contract_passed,
                    "failure_identity": outcome.failure_identity,
                }
            )
        controls_passed = all(
            item["execution_status"] == "COMPLETED"
            and item["numerical_guard_passed"]
            for item in control_records
        ) and all(
            not item["event_contract_passed"]
            for item in control_records
            if item["control"] in {"ZERO_DRIVE", "JOULE_GAIN_ZERO"}
        )

    accepted = selected is not None and controls_passed
    gate_outcome = (
        "PHK_V21_E2_ENGINEERING_OBJECT_CANDIDATE_SELECTED"
        if accepted
        else "PHK_V21_ENGINEERING_NO_ADMISSIBLE_REPEATABLE_EVENT_OBJECT"
    )
    summary = {
        "schema_id": "phk-v21-engineering-campaign-summary-v1",
        "run_id": run_id,
        "evidence_identity": "NON_VOTING_ENGINEERING_ONLY",
        **hashes,
        "algorithm": PhkV21PhaseAlgorithm.LOGIT_NEWTON_ANALYTIC_JACOBIAN.value,
        "stage_1_outcomes": [item.to_json_dict() for item in stage1],
        "selected_stage_1_parents": [
            item.case.overrides.case_id for item in parents
        ],
        "stage_2_outcomes": [item.to_json_dict() for item in stage2],
        "selected_medium_promotions": [
            item.case.overrides.case_id for item in promotions
        ],
        "medium_outcomes": [item.to_json_dict() for item in medium],
        "selected_nominal_case": (
            None if selected is None else selected.case.to_json_dict()
        ),
        "control_outcomes": control_records,
        "controls_not_reached": (
            [] if selected is not None else [item.value for item in controls]
        ),
        "accepted_for_new_scientific_freeze": accepted,
        "gate_outcome": gate_outcome,
        "scientific_claim_status": "NO_OBJECT_ORACLE_EVENT_PINN_METHOD_OR_FORMAL_EVIDENCE",
        "gross_compute": {
            "case_records": case_records,
            "failed_case_records": failed_records,
            "process_cpu_seconds": time.process_time() - campaign_cpu_start,
            "process_cpu_core_hours": (
                time.process_time() - campaign_cpu_start
            ) / 3600.0,
            "wall_clock_seconds": time.perf_counter() - campaign_wall_start,
        },
    }
    summary_path = run_root / "summary.json"
    _write_new_json(summary_path, summary)

    ended_at = _utc_now()
    source = Path(__file__)
    artifacts = {
        "intent": str(intent_path),
        "intent_sha256": _sha256(intent_path),
        "case_records": str(journal_path),
        "case_records_sha256": _sha256(journal_path),
        "summary": str(summary_path),
        "summary_sha256": _sha256(summary_path),
        "program_contract": str(Path(program_path)),
        "program_contract_sha256": hashes["program_contract_sha256"],
        "engineering_contract": str(Path(engineering_path)),
        "engineering_contract_sha256": hashes["engineering_contract_sha256"],
        "e1_solver_selection": str(Path(selection_path)),
        "e1_solver_selection_sha256": hashes["e1_solver_selection_sha256"],
    }
    manifest = RunManifest(
        run_id=run_id,
        experiment_group_id=EXPERIMENT_GROUP_ID,
        tier="engineering",
        scientific_role="benchmark_engineering_non_voting",
        gate="PHK_V21_E2",
        started_at=started_at,
        ended_at=ended_at,
        command=["python", "-m", "pinn_pcm_sci.phk_v21_design_runner", "run"],
        execution_status="COMPLETED",
        numerical_validity="NON_VOTING_ENGINEERING_SCREEN_COMPLETE",
        gate_outcome=gate_outcome,
        route_disposition=(
            "FREEZE_NEW_SCIENTIFIC_CONTRACT_BEFORE_ORACLE"
            if accepted
            else "STOP_PHK_V21_ENGINEERING_ROUTE_AND_BUILD_TERMINAL_PACKAGE"
        ),
        evidence_identity="NON_VOTING_ENGINEERING_ONLY",
        claim_status="NO_OBJECT_ORACLE_EVENT_PINN_METHOD_OR_FORMAL_EVIDENCE",
        code_identity={
            "kind": "working-tree",
            "runner_sha256": _sha256(source),
            "design_sha256": _sha256(source.with_name("phk_v21_design.py")),
            "engineering_sha256": _sha256(source.with_name("phk_v21_engineering.py")),
            "solver_sha256": _sha256(source.with_name("phk_v21_solver.py")),
            "legacy_phk_v2_sha256": _sha256(legacy_source),
        },
        environment={
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "dtype": "float64",
            "device": "cpu",
        },
        physical_contract_id=PHYSICAL_CONTRACT_ID,
        split_id=SPLIT_ID,
        method_id=METHOD_ID,
        case_id="phk-v21-e2-preregistered-16-plus-16-plus-3-plus-controls",
        seed=0,
        planned_budget={
            "stage_1_cases": 16,
            "stage_2_cases": 16,
            "medium_promotions": 3,
            "maximum_medium_controls": 6,
            "maximum_cpu_process_core_hours": 24.0,
            "failed_intents_count": True,
            "replacement_case": False,
        },
        actual_budget=dict(summary["gross_compute"]),
        checkpoint={"id": "NOT_APPLICABLE", "selection": "E2_ENGINEERING_CAMPAIGN"},
        evaluator_id="phk-v21-engineering-event-locality-ranking-v1",
        artifacts=artifacts,
        failure_class=None,
        replay_of=None,
        supersedes=None,
    )
    ledger = ExperimentLedger(experiment_root)
    ledger.validate()
    ledger.record(manifest)
    ledger.validate()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="phk-v21-design-runner")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--run-id", required=True)
    run.add_argument("--program", type=Path, required=True)
    run.add_argument("--engineering", type=Path, required=True)
    run.add_argument("--selection", type=Path, required=True)
    run.add_argument("--legacy-program", type=Path, required=True)
    run.add_argument("--legacy-object", type=Path, required=True)
    run.add_argument("--output-root", type=Path, default=Path("outputs/runs"))
    run.add_argument(
        "--experiment-root", type=Path, default=Path("docs/experiment")
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.command == "run":
        return run_campaign(
            run_id=arguments.run_id,
            program_path=arguments.program,
            engineering_path=arguments.engineering,
            selection_path=arguments.selection,
            legacy_program_path=arguments.legacy_program,
            legacy_object_path=arguments.legacy_object,
            output_root=arguments.output_root,
            experiment_root=arguments.experiment_root,
        )
    raise AssertionError("unreachable command")


if __name__ == "__main__":
    raise SystemExit(main())
