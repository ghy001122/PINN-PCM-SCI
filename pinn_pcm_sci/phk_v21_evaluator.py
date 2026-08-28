"""PHK-V2.1 oracle-floor and hard-gate evaluator.

The benchmark module owns fields and numerical comparison.  This module owns
the irreversible scientific decision: execution, hard guards, event identity,
convergence, replay, and solver cross-check remain separate gates and cannot be
averaged into a favourable score.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from .phk_benchmark import PhkConvergenceReport


COMPONENT_ORDER = (
    "PHASE_FIELD_ROI_RMS",
    "TEMPERATURE_FIELD_ROI_RMS",
    "TERMINAL_CURRENT_TRACE_RMS",
    "TWO_CYCLE_EVENT_TIME_RMS",
    "TIME_AVERAGED_PHASE_REGION_SYMMETRIC_DIFFERENCE",
    "TWO_CYCLE_RECOVERY_RMS",
)


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _read_json(path: Path, name: str) -> tuple[bytes, dict[str, Any]]:
    raw = Path(path).read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid UTF-8 JSON {name}: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{name} root must be an object")
    return raw, payload


def load_phk_v21_oracle_contract(
    path: Path,
    *,
    program_sha256: str,
    object_sha256: str,
    split_file_sha256: str,
    split_manifest_sha256: str,
    require_final: bool = True,
) -> Mapping[str, Any]:
    """Load the exact oracle contract and reject any stale upstream binding."""

    _, payload = _read_json(path, "PHK-V2.1 oracle/floor contract")
    if payload.get("schema_id") != "phk-v21-oracle-and-floor-contract-v1":
        raise ValueError("unsupported PHK-V2.1 oracle/floor contract schema")
    if payload.get("contract_id") != "PHK_V21_ORACLE_FLOOR_V1":
        raise ValueError("unexpected PHK-V2.1 oracle/floor contract identity")
    if require_final and payload.get("status") != "PRE_FIRST_VOTING_SOLVE_FREEZE":
        raise ValueError("PHK-V2.1 oracle/floor contract is not final")
    bindings = payload.get("bindings")
    if not isinstance(bindings, dict):
        raise ValueError("PHK-V2.1 oracle/floor contract lacks bindings")
    expected = {
        "program_contract_sha256": program_sha256,
        "object_contract_sha256": object_sha256,
        "split_file_sha256": split_file_sha256,
        "split_manifest_sha256": split_manifest_sha256,
    }
    for key, value in expected.items():
        if bindings.get(key) != value:
            raise ValueError(f"PHK-V2.1 oracle/floor binding mismatch: {key}")
    ladder = payload.get("qualification_ladder")
    if not isinstance(ladder, list) or [row.get("order") for row in ladder] != list(
        range(1, 15)
    ):
        raise ValueError("PHK-V2.1 qualification ladder must be exact 1..14")
    endpoint = payload.get("component_endpoint")
    if not isinstance(endpoint, dict) or tuple(endpoint.get("component_order", ())) != (
        COMPONENT_ORDER
    ):
        raise ValueError("PHK-V2.1 endpoint component order drift")
    if require_final:
        for key, value in bindings.items():
            if key.endswith("_sha256") and (
                not isinstance(value, str)
                or len(value) != 64
                or value != value.upper()
            ):
                raise ValueError(f"PHK-V2.1 oracle binding is not frozen: {key}")
    return payload


def _vector(report: PhkConvergenceReport, name: str) -> np.ndarray:
    if tuple(report.component_order) != COMPONENT_ORDER:
        raise ValueError(f"{name} component order mismatch")
    values = np.asarray(report.component_deltas, dtype=np.float64)
    if values.shape != (6,) or not np.isfinite(values).all() or np.any(values < 0.0):
        raise ValueError(f"{name} deltas must be six finite nonnegative values")
    return values


def build_phk_v21_oracle_floor_seal(
    *,
    oracle_contract: Mapping[str, Any],
    medium_fine: PhkConvergenceReport,
    fine_extra_fine: PhkConvergenceReport,
    medium_half_dt: PhkConvergenceReport,
    fine_replay: PhkConvergenceReport,
    medium_solver_crosscheck: PhkConvergenceReport,
    source_run_ids: Sequence[str],
) -> dict[str, Any]:
    """Seal component floors and convergence gates before any neural work."""

    vectors = {
        "medium_fine": _vector(medium_fine, "medium_fine"),
        "fine_extra_fine": _vector(fine_extra_fine, "fine_extra_fine"),
        "medium_half_dt": _vector(medium_half_dt, "medium_half_dt"),
        "fine_replay": _vector(fine_replay, "fine_replay"),
        "medium_solver_crosscheck": _vector(
            medium_solver_crosscheck, "medium_solver_crosscheck"
        ),
    }
    floor_spec = oracle_contract.get("oracle_floor")
    if not isinstance(floor_spec, dict):
        raise ValueError("PHK-V2.1 oracle contract lacks oracle_floor")
    declared_payload = floor_spec.get("declared_component_solver_tolerance")
    if not isinstance(declared_payload, dict) or tuple(declared_payload) != COMPONENT_ORDER:
        raise ValueError("PHK-V2.1 declared component tolerance order mismatch")
    declared = np.asarray(
        [float(declared_payload[name]) for name in COMPONENT_ORDER], dtype=np.float64
    )
    if not np.isfinite(declared).all() or np.any(declared <= 0.0):
        raise ValueError("PHK-V2.1 declared component tolerances must be positive")

    medium_fine_values = vectors["medium_fine"]
    fine_extra_values = vectors["fine_extra_fine"]
    monotonic = fine_extra_values <= np.maximum(medium_fine_values, declared)
    contracted = (fine_extra_values <= 0.90 * medium_fine_values) | (
        (fine_extra_values <= declared) & (medium_fine_values <= declared)
    )
    co_primary_indices = (2, 4)
    convergence_pass = bool(
        np.all(monotonic)
        and np.count_nonzero(contracted) >= 4
        and all(monotonic[index] and contracted[index] for index in co_primary_indices)
    )
    floors = np.maximum.reduce(
        (
            fine_extra_values,
            vectors["medium_half_dt"],
            vectors["fine_replay"],
            vectors["medium_solver_crosscheck"],
            declared,
        )
    )
    if not np.isfinite(floors).all() or np.any(floors <= 0.0):
        raise ValueError("PHK-V2.1 oracle floors are not finite and positive")
    tau = float(np.sqrt(np.mean(floors**2)))
    payload: dict[str, Any] = {
        "schema_id": "phk-v21-oracle-floor-seal-v1",
        "seal_status": "SEALED_BEFORE_NEURAL_WORK",
        "oracle_contract_id": oracle_contract["contract_id"],
        "oracle_contract_sha256": _sha256(_canonical_json(oracle_contract)),
        "component_order": list(COMPONENT_ORDER),
        "source_run_ids": list(source_run_ids),
        "component_deltas": {
            key: value.tolist() for key, value in vectors.items()
        },
        "declared_component_solver_tolerance": declared.tolist(),
        "space_monotonic_by_component": monotonic.tolist(),
        "strict_contraction_by_component": contracted.tolist(),
        "strict_contraction_count": int(np.count_nonzero(contracted)),
        "convergence_gate_passed": convergence_pass,
        "component_floors_U": floors.tolist(),
        "tau": tau,
        "source_joint_uncertainty": 0.0,
        "prediction_score_formula": "Z=sqrt(mean((component_error_j/U_j)^2))",
    }
    payload["seal_sha256"] = _sha256(_canonical_json(payload))
    return payload


def validate_phk_v21_oracle_floor_seal(
    payload: Mapping[str, Any],
    *,
    oracle_contract: Mapping[str, Any],
) -> None:
    if payload.get("schema_id") != "phk-v21-oracle-floor-seal-v1":
        raise ValueError("unsupported PHK-V2.1 oracle floor seal")
    if payload.get("seal_status") != "SEALED_BEFORE_NEURAL_WORK":
        raise ValueError("PHK-V2.1 oracle floor was not sealed before neural work")
    if tuple(payload.get("component_order", ())) != COMPONENT_ORDER:
        raise ValueError("PHK-V2.1 oracle floor component order mismatch")
    unsigned = dict(payload)
    declared_sha = unsigned.pop("seal_sha256", None)
    if declared_sha != _sha256(_canonical_json(unsigned)):
        raise ValueError("PHK-V2.1 oracle floor seal hash mismatch")
    if payload.get("oracle_contract_sha256") != _sha256(
        _canonical_json(oracle_contract)
    ):
        raise ValueError("PHK-V2.1 oracle floor contract binding mismatch")
    floors = np.asarray(payload.get("component_floors_U"), dtype=np.float64)
    if floors.shape != (6,) or not np.isfinite(floors).all() or np.any(floors <= 0.0):
        raise ValueError("PHK-V2.1 oracle floor values are invalid")
    tau = float(payload.get("tau", math.nan))
    if not math.isclose(
        tau,
        float(np.sqrt(np.mean(floors**2))),
        rel_tol=1.0e-14,
        abs_tol=0.0,
    ):
        raise ValueError("PHK-V2.1 oracle floor tau mismatch")


def write_phk_v21_oracle_floor_seal(
    path: Path,
    payload: Mapping[str, Any],
) -> None:
    encoded = (
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    descriptor = os.open(Path(path), flags, 0o644)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        Path(path).unlink(missing_ok=True)
        raise


def adjudicate_phk_v21_q(
    *,
    execution_status_by_intent: Mapping[int, str],
    guard_pass_by_intent: Mapping[int, bool],
    event_pass_by_intent: Mapping[int, bool],
    manufactured_pass: bool,
    zero_drive_no_event: bool,
    joule_off_no_event: bool,
    replay_max_array_difference: float,
    replay_limit: float,
    floor_seal: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Apply the ordered 14-intent Q gate without averaging hard failures."""

    statuses = {int(key): str(value) for key, value in execution_status_by_intent.items()}
    if not statuses or 1 not in statuses:
        raise ValueError("missing PHK-V2.1 qualification intent 1")
    unknown = set(statuses) - set(range(1, 15))
    if unknown:
        raise ValueError(f"unknown PHK-V2.1 qualification intents: {sorted(unknown)}")
    invalid = {
        key: value
        for key, value in statuses.items()
        if value not in {"COMPLETED", "FAILED"}
    }
    if invalid:
        raise ValueError(f"invalid PHK-V2.1 execution status: {invalid}")
    failed = sorted(key for key, value in statuses.items() if value == "FAILED")
    if len(failed) > 1:
        raise ValueError("more than one PHK-V2.1 consumed failure violates stop rules")
    terminal = failed[0] if failed else max(statuses)
    if set(statuses) != set(range(1, terminal + 1)):
        raise ValueError("PHK-V2.1 Q intents are not a contiguous ordered prefix")
    not_reached = list(range(terminal + 1, 15))
    completed_fields = [
        number
        for number in range(2, terminal + 1)
        if statuses[number] == "COMPLETED"
    ]
    missing_guards = [
        number for number in completed_fields if number not in guard_pass_by_intent
    ]
    if missing_guards:
        raise ValueError(f"missing PHK-V2.1 guards: {missing_guards}")
    guard_failures = [
        number for number in completed_fields if not guard_pass_by_intent[number]
    ]
    nominal_event_intents = {3, 4, 5, 6, 7, 8, 14}
    reached_nominal = sorted(nominal_event_intents & set(completed_fields))
    missing_events = [
        number for number in reached_nominal if number not in event_pass_by_intent
    ]
    if missing_events:
        raise ValueError(f"missing PHK-V2.1 event reports: {missing_events}")
    event_failures = [
        number for number in reached_nominal if not event_pass_by_intent[number]
    ]
    replay_pass = bool(
        8 in statuses
        and statuses[8] == "COMPLETED"
        and math.isfinite(float(replay_max_array_difference))
        and float(replay_max_array_difference) <= float(replay_limit)
    )
    floor_pass = bool(
        floor_seal is not None
        and floor_seal.get("convergence_gate_passed") is True
        and floor_seal.get("seal_status") == "SEALED_BEFORE_NEURAL_WORK"
    )

    reasons: list[str] = []
    if not manufactured_pass:
        reasons.append("MANUFACTURED_OPERATOR_GATE_FAILED")
    if guard_failures:
        reasons.append("HARD_NUMERICAL_GUARD_FAILED")
    if event_failures:
        reasons.append("NOMINAL_TWO_CYCLE_EVENT_GATE_FAILED")
    if 2 in statuses and statuses[2] == "COMPLETED" and not zero_drive_no_event:
        reasons.append("ZERO_DRIVE_FALSE_EVENT")
    if 9 in statuses and statuses[9] == "COMPLETED" and not joule_off_no_event:
        reasons.append("JOULE_OFF_FALSE_EVENT")
    if 8 in statuses and not replay_pass:
        reasons.append("EXACT_REPLAY_GATE_FAILED")
    if len(statuses) == 14 and not floor_pass:
        reasons.append("CONVERGENCE_OR_FLOOR_GATE_FAILED")
    if failed:
        reasons.append("QUALIFICATION_EXECUTION_FAILED")
    complete = set(statuses) == set(range(1, 15)) and not failed
    qualified = bool(complete and not reasons and floor_pass)
    return {
        "schema_id": "phk-v21-q-adjudication-v1",
        "outcome": (
            "PHK_V21_ORACLE_GATE_PASS"
            if qualified
            else "PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN"
        ),
        "oracle_qualified": qualified,
        "method_route": "CONTINUE_TO_BASELINE_REPLICATION" if qualified else "STOP_BEFORE_PINN_TRAINING",
        "terminal_intent": terminal,
        "not_reached_intents": not_reached,
        "manufactured_pass": bool(manufactured_pass),
        "hard_guard_failure_intents": guard_failures,
        "event_failure_intents": event_failures,
        "zero_drive_no_event": bool(zero_drive_no_event),
        "joule_off_no_event": bool(joule_off_no_event),
        "replay_pass": replay_pass,
        "replay_max_array_difference": (
            float(replay_max_array_difference)
            if math.isfinite(float(replay_max_array_difference))
            else None
        ),
        "replay_value_finite": math.isfinite(float(replay_max_array_difference)),
        "replay_limit": float(replay_limit),
        "floor_sealed_and_converged": floor_pass,
        "execution_failure_intents": failed,
        "reasons": reasons,
        "claim_ceiling": (
            "TRANSPARENT_SYNTHETIC_BENCHMARK_QUALIFICATION_ONLY_"
            "NO_PINN_METHOD_MATERIAL_OR_EXPERIMENTAL_EVIDENCE"
        ),
    }


__all__ = [
    "COMPONENT_ORDER",
    "adjudicate_phk_v21_q",
    "build_phk_v21_oracle_floor_seal",
    "load_phk_v21_oracle_contract",
    "validate_phk_v21_oracle_floor_seal",
    "write_phk_v21_oracle_floor_seal",
]
