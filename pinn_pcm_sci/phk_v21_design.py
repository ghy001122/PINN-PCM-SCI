"""Deterministic PHK-V2.1 non-voting object-design campaign.

The public interface generates the exact preregistered candidates, converts
engineering solver results into frozen ranking records, and performs the three
selection operations.  Numerical solution remains behind
``run_engineering_case``; no scientific oracle identity is exposed here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .phk_v21_engineering import (
    PhkV21EngineeringOverrides,
    PhkV21EngineeringRun,
)


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _finite_or_none(value: float) -> float | None:
    return float(value) if math.isfinite(value) else None


@dataclass(frozen=True)
class PhkV21DesignCase:
    stage: str
    parent_case_id: str | None
    physical_identity_sha256: str
    overrides: PhkV21EngineeringOverrides

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "parent_case_id": self.parent_case_id,
            "physical_identity_sha256": self.physical_identity_sha256,
            "overrides": asdict(self.overrides),
        }


@dataclass(frozen=True)
class PhkV21CandidateOutcome:
    case: PhkV21DesignCase
    execution_status: str
    failure_identity: str | None
    numerical_guard_passed: bool
    event_contract_passed: bool
    event_and_locality_guards_passed_count: int
    minimum_cycle_recovery: float
    cycle_peak_drift: float
    outside_roi_peak: float
    process_cpu_seconds: float
    cycle_records: tuple[Mapping[str, float | int | None], ...]

    @classmethod
    def completed(
        cls,
        *,
        case: PhkV21DesignCase,
        run: PhkV21EngineeringRun,
        process_cpu_seconds: float,
    ) -> "PhkV21CandidateOutcome":
        cycles = run.event.cycles
        if len(cycles) == 2:
            atomic_count = 0
            cycle_records: list[dict[str, float | int | None]] = []
            recoveries: list[float] = []
            outside: list[float] = []
            for cycle in cycles:
                excursion = cycle.peak_roi_fraction - cycle.pre_roi_fraction
                checks = (
                    cycle.event_time is not None,
                    cycle.peak_roi_fraction >= 0.02,
                    excursion >= 0.02,
                    cycle.recovery_fraction >= 0.70,
                    cycle.peak_full_domain_fraction <= 0.45,
                    cycle.peak_outside_roi_fraction <= 0.10,
                    cycle.saved_steps_at_or_above_threshold >= 3,
                )
                atomic_count += sum(int(item) for item in checks)
                recoveries.append(float(cycle.recovery_fraction))
                outside.append(float(cycle.peak_outside_roi_fraction))
                cycle_records.append(
                    {
                        "cycle_index": int(cycle.cycle_index),
                        "event_time": (
                            None if cycle.event_time is None else float(cycle.event_time)
                        ),
                        "pre_roi_fraction": float(cycle.pre_roi_fraction),
                        "peak_roi_fraction": float(cycle.peak_roi_fraction),
                        "peak_full_domain_fraction": float(
                            cycle.peak_full_domain_fraction
                        ),
                        "peak_outside_roi_fraction": float(
                            cycle.peak_outside_roi_fraction
                        ),
                        "recovery_fraction": float(cycle.recovery_fraction),
                        "saved_steps_at_or_above_threshold": int(
                            cycle.saved_steps_at_or_above_threshold
                        ),
                    }
                )
            if run.event.cycle_peak_relative_drift <= 0.20:
                atomic_count += 1
            minimum_recovery = min(recoveries)
            outside_peak = max(outside)
            drift = float(run.event.cycle_peak_relative_drift)
        else:
            atomic_count = 0
            cycle_records = []
            minimum_recovery = -math.inf
            outside_peak = math.inf
            drift = math.inf
        if not run.guard.passed:
            atomic_count = -1
        return cls(
            case=case,
            execution_status="COMPLETED",
            failure_identity=None,
            numerical_guard_passed=bool(run.guard.passed),
            event_contract_passed=bool(run.event.passed and run.guard.passed),
            event_and_locality_guards_passed_count=atomic_count,
            minimum_cycle_recovery=float(minimum_recovery),
            cycle_peak_drift=float(drift),
            outside_roi_peak=float(outside_peak),
            process_cpu_seconds=float(process_cpu_seconds),
            cycle_records=tuple(cycle_records),
        )

    @classmethod
    def failed(
        cls,
        *,
        case: PhkV21DesignCase,
        failure_identity: str,
        process_cpu_seconds: float,
    ) -> "PhkV21CandidateOutcome":
        if not failure_identity:
            raise ValueError("failed PHK-V2.1 design case requires a failure identity")
        return cls(
            case=case,
            execution_status="FAILED_CONSUMED",
            failure_identity=failure_identity,
            numerical_guard_passed=False,
            event_contract_passed=False,
            event_and_locality_guards_passed_count=-2,
            minimum_cycle_recovery=-math.inf,
            cycle_peak_drift=math.inf,
            outside_roi_peak=math.inf,
            process_cpu_seconds=float(process_cpu_seconds),
            cycle_records=(),
        )

    def ranking_key(self) -> tuple[float | str, ...]:
        return (
            -float(self.event_and_locality_guards_passed_count),
            -float(self.minimum_cycle_recovery),
            float(self.cycle_peak_drift),
            float(self.outside_roi_peak),
            float(self.process_cpu_seconds),
            self.case.overrides.case_id,
        )

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "case": self.case.to_json_dict(),
            "execution_status": self.execution_status,
            "failure_identity": self.failure_identity,
            "numerical_guard_passed": self.numerical_guard_passed,
            "event_contract_passed": self.event_contract_passed,
            "event_and_locality_guards_passed_count": (
                self.event_and_locality_guards_passed_count
            ),
            "minimum_cycle_recovery": _finite_or_none(self.minimum_cycle_recovery),
            "cycle_peak_drift": _finite_or_none(self.cycle_peak_drift),
            "outside_roi_peak": _finite_or_none(self.outside_roi_peak),
            "process_cpu_seconds": self.process_cpu_seconds,
            "cycle_records": [dict(item) for item in self.cycle_records],
        }


def _make_case(
    *,
    stage: str,
    parent_case_id: str | None,
    values: Mapping[str, float],
) -> PhkV21DesignCase:
    physical = {
        "period": float(values["period"]),
        "volumetric_cooling": float(values["volumetric_cooling"]),
        "mobility_cold": float(values["mobility_cold"]),
        "thermal_drive": float(values["thermal_drive"]),
        "waveform_amplitude": float(values["waveform_amplitude"]),
        "pulse_hold_end": float(values["pulse_hold_end"]),
        "latent_ratio": float(values["latent_ratio"]),
        "mobility_hot": float(values["mobility_hot"]),
        "heater_width_fraction": float(values.get("heater_width_fraction", 0.35)),
        "interface_width": float(values.get("interface_width", 0.04)),
    }
    identity = hashlib.sha256(_canonical_json(physical)).hexdigest().upper()
    overrides = PhkV21EngineeringOverrides(
        case_id=f"PHK_V21_E2_{stage}_{identity[:16]}",
        **physical,
    )
    overrides.validate()
    return PhkV21DesignCase(
        stage=stage,
        parent_case_id=parent_case_id,
        physical_identity_sha256=identity,
        overrides=overrides,
    )


def _load_search(contract_path: Path) -> Mapping[str, Any]:
    payload = json.loads(Path(contract_path).read_text(encoding="utf-8"))
    if payload.get("schema_id") != "phk-v21-engineering-contract-v1":
        raise ValueError("unsupported PHK-V2.1 engineering contract")
    search = payload.get("p1_search")
    if not isinstance(search, dict):
        raise ValueError("PHK-V2.1 engineering contract has no p1_search")
    return search


def build_stage1_cases(contract_path: Path) -> tuple[PhkV21DesignCase, ...]:
    search = _load_search(contract_path)
    stage = search["stage_1_full_factorial"]
    fixed = stage["fixed"]
    cases = tuple(
        _make_case(
            stage="STAGE1",
            parent_case_id=None,
            values={
                "period": period,
                "volumetric_cooling": cooling,
                "mobility_cold": mobility,
                "thermal_drive": drive,
                "waveform_amplitude": fixed["amplitude"],
                "pulse_hold_end": fixed["hold_end"],
                "latent_ratio": fixed["latent_ratio"],
                "mobility_hot": fixed["mobility_hot"],
            },
        )
        for period, cooling, mobility, drive in itertools.product(
            stage["period"],
            stage["volumetric_cooling"],
            stage["mobility_cold"],
            stage["thermal_drive"],
        )
    )
    if len(cases) != int(stage["case_count"]):
        raise ValueError("PHK-V2.1 stage-1 case count does not match the contract")
    if len({case.physical_identity_sha256 for case in cases}) != len(cases):
        raise ValueError("PHK-V2.1 stage-1 contains duplicate physical cases")
    return cases


def build_stage2_cases(
    contract_path: Path,
    parents: Sequence[PhkV21CandidateOutcome],
) -> tuple[PhkV21DesignCase, ...]:
    search = _load_search(contract_path)
    refinement = search["stage_2_predeclared_refinement"]
    if len(parents) != int(refinement["parents"]):
        raise ValueError("PHK-V2.1 stage-2 requires exactly two frozen parents")
    cases: list[PhkV21DesignCase] = []
    for parent in parents:
        base = parent.case.overrides
        for amplitude, hold, latent in itertools.product(
            refinement["amplitude"],
            refinement["hold_end"],
            refinement["latent_ratio"],
        ):
            cases.append(
                _make_case(
                    stage="STAGE2",
                    parent_case_id=base.case_id,
                    values={
                        "period": base.period,
                        "volumetric_cooling": base.volumetric_cooling,
                        "mobility_cold": base.mobility_cold,
                        "thermal_drive": base.thermal_drive,
                        "waveform_amplitude": amplitude,
                        "pulse_hold_end": hold,
                        "latent_ratio": latent,
                        "mobility_hot": base.mobility_hot,
                        "heater_width_fraction": base.heater_width_fraction,
                        "interface_width": base.interface_width,
                    },
                )
            )
    if len(cases) != int(refinement["case_count"]):
        raise ValueError("PHK-V2.1 stage-2 case count does not match the contract")
    if len({case.physical_identity_sha256 for case in cases}) != len(cases):
        raise ValueError("PHK-V2.1 stage-2 contains duplicate physical cases")
    return tuple(cases)


def rank_outcomes(
    outcomes: Iterable[PhkV21CandidateOutcome],
) -> tuple[PhkV21CandidateOutcome, ...]:
    values = tuple(outcomes)
    if len({item.case.overrides.case_id for item in values}) != len(values):
        raise ValueError("PHK-V2.1 outcomes contain duplicate case identities")
    return tuple(sorted(values, key=PhkV21CandidateOutcome.ranking_key))


def select_stage1_parents(
    outcomes: Sequence[PhkV21CandidateOutcome],
) -> tuple[PhkV21CandidateOutcome, ...]:
    if len(outcomes) != 16:
        raise ValueError("PHK-V2.1 parent selection requires all 16 stage-1 outcomes")
    return rank_outcomes(outcomes)[:2]


def select_medium_promotions(
    outcomes: Sequence[PhkV21CandidateOutcome],
) -> tuple[PhkV21CandidateOutcome, ...]:
    if len(outcomes) != 16:
        raise ValueError("PHK-V2.1 promotion selection requires all 16 stage-2 outcomes")
    return rank_outcomes(outcomes)[:3]


def select_nominal_medium(
    outcomes: Sequence[PhkV21CandidateOutcome],
) -> PhkV21CandidateOutcome | None:
    if len(outcomes) != 3:
        raise ValueError("PHK-V2.1 nominal selection requires all three promotions")
    for outcome in rank_outcomes(outcomes):
        if outcome.numerical_guard_passed and outcome.event_contract_passed:
            return outcome
    return None
