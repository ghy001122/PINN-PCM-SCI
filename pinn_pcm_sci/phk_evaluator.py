"""Disk-independent PHK Q-gate logic.

Numerical carrier loading and metric calculation live in ``phk_benchmark``;
this module owns the terminal decision semantics so event, guard, replay and
execution failures cannot be averaged into one favourable score.
"""

from __future__ import annotations

import math
from typing import Mapping


def adjudicate_phk_q(
    *,
    execution_status_by_intent: Mapping[int, str],
    guard_pass_by_intent: Mapping[int, bool],
    event_pass_by_intent: Mapping[int, bool],
    manufactured_pass: bool,
    replay_max_component_difference: float,
    replay_limit: float,
    thermal_effect_established: bool,
) -> dict[str, object]:
    """Apply the frozen ordered PHK Q gate without score averaging."""

    statuses = {int(key): str(value) for key, value in execution_status_by_intent.items()}
    if not statuses or 1 not in statuses:
        raise ValueError("missing qualification intent 1")
    unknown = set(statuses) - set(range(1, 13))
    if unknown:
        raise ValueError(f"unknown qualification intents: {sorted(unknown)}")
    failed = sorted(number for number, status in statuses.items() if status == "FAILED")
    invalid_status = {
        number: status
        for number, status in statuses.items()
        if status not in {"COMPLETED", "FAILED"}
    }
    if invalid_status:
        raise ValueError(f"invalid qualification execution status: {invalid_status}")
    if len(failed) > 1:
        raise ValueError("more than one consumed failure violates the stop rule")
    terminal = failed[0] if failed else 12
    expected_reached = set(range(1, terminal + 1))
    if set(statuses) != expected_reached:
        missing = sorted(expected_reached - set(statuses))
        extra = sorted(set(statuses) - expected_reached)
        raise ValueError(
            "missing qualification intent before terminal disposition: "
            f"missing={missing}, extra={extra}"
        )
    if not failed and set(statuses) != set(range(1, 13)):
        raise ValueError("missing qualification intent without a consumed failure")

    not_reached = list(range(terminal + 1, 13)) if failed else []
    completed_solver_intents = [
        number for number in range(2, terminal + 1) if statuses[number] == "COMPLETED"
    ]
    missing_guards = [
        number for number in completed_solver_intents if number not in guard_pass_by_intent
    ]
    if missing_guards:
        raise ValueError(f"missing guard adjudication for intents {missing_guards}")
    guard_failures = [
        number for number in completed_solver_intents if not guard_pass_by_intent[number]
    ]
    nominal_event_intents = [number for number in range(3, 8) if number <= terminal]
    missing_events = [number for number in nominal_event_intents if number not in event_pass_by_intent]
    if missing_events:
        raise ValueError(f"missing event adjudication for intents {missing_events}")
    event_failures = [
        number for number in nominal_event_intents if not event_pass_by_intent[number]
    ]
    replay_finite = math.isfinite(float(replay_max_component_difference))
    replay_pass = bool(
        7 in statuses
        and statuses[7] == "COMPLETED"
        and replay_finite
        and float(replay_max_component_difference) <= float(replay_limit)
    )

    reasons: list[str] = []
    if not manufactured_pass:
        reasons.append("MANUFACTURED_OPERATOR_GATE_FAILED")
    if guard_failures:
        reasons.append("HARD_GUARD_FAILURE")
    if event_failures:
        reasons.append("TWO_CYCLE_EVENT_CONTRACT_FAILED")
    if not replay_pass:
        reasons.append("EXACT_REPLAY_GATE_FAILED_OR_NOT_REACHED")
    if not thermal_effect_established:
        reasons.append("THERMAL_JOULE_EFFECT_NOT_ESTABLISHED")
    if failed:
        reasons.append("QUALIFICATION_CONTROL_EXECUTION_FAILED")

    positive = bool(
        not reasons
        and set(statuses) == set(range(1, 13))
        and all(status == "COMPLETED" for status in statuses.values())
    )
    if positive:
        outcome = "PHK_V2_ORACLE_GATE_PASS"
        route = "CONTINUE_TO_STRONG_RAW"
    else:
        if event_failures and failed:
            outcome = "PHK_V2_ORACLE_NO_GO_EVENT_CONTRACT_AND_CONTROL_EXECUTION_FAILURE"
        elif event_failures:
            outcome = "PHK_V2_ORACLE_NO_GO_EVENT_CONTRACT"
        elif failed:
            outcome = "PHK_V2_ORACLE_NO_GO_CONTROL_EXECUTION_FAILURE"
        else:
            outcome = "PHK_V2_ORACLE_NO_GO_OTHER_QUALIFICATION_GATE"
        route = "STOP_BEFORE_PINN_TRAINING"
    return {
        "schema_id": "phk-v2-q-adjudication-v1",
        "outcome": outcome,
        "oracle_qualified": positive,
        "method_route": route,
        "terminal_intent": terminal,
        "not_reached_intents": not_reached,
        "manufactured_pass": bool(manufactured_pass),
        "hard_guard_failure_intents": guard_failures,
        "event_failure_intents": event_failures,
        "replay_pass": replay_pass,
        "replay_max_component_difference": float(replay_max_component_difference),
        "replay_limit": float(replay_limit),
        "thermal_effect_established": bool(thermal_effect_established),
        "execution_failure_intents": failed,
        "reasons": reasons,
        "claim_ceiling": (
            "TRANSPARENT_SYNTHETIC_BENCHMARK_QUALIFICATION_ONLY_"
            "NO_PINN_METHOD_OR_EXPERIMENTAL_EVIDENCE"
        ),
    }


__all__ = ["adjudicate_phk_q"]
