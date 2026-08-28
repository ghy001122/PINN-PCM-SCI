"""Bounded, non-voting PHK-V2.1 solver and object engineering harness.

The harness deliberately reuses the frozen PHK-V2 finite-volume operators
without altering their source file.  A process-local, locked phase-solver seam
is used only for engineering probes.  The selected scheme must later be copied
into an independently frozen PHK-V2.1 scientific benchmark implementation;
this module is never a scientific oracle by itself.
"""

from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path
import threading
from typing import Any, Iterator, Mapping

from . import phk_benchmark as _legacy
from .phk_benchmark import (
    PhkCaseSpec,
    PhkControl,
    PhkEventReport,
    PhkGuardReport,
    PhkOracleCase,
    PhkOracleResult,
    PhkPhysicalContract,
    PhkResolution,
)
from .phk_contract import PhkObjectContract, PhkProgramContract
from .phk_v21_solver import (
    PhkV21PhaseAlgorithm,
    solve_phase_candidate,
)


_PHASE_PATCH_LOCK = threading.RLock()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


@dataclass(frozen=True)
class PhkV21EngineeringOverrides:
    case_id: str
    period: float = 1.0
    volumetric_cooling: float = 1.5
    mobility_cold: float = 0.2
    thermal_drive: float = 4.0
    waveform_amplitude: float = 0.75
    pulse_hold_end: float = 0.30
    latent_ratio: float = 0.15
    mobility_hot: float = 5.0
    heater_width_fraction: float = 0.35
    interface_width: float = 0.04

    def validate(self) -> None:
        if not self.case_id:
            raise ValueError("PHK-V2.1 engineering case_id cannot be empty")
        if self.period <= 0.35:
            raise ValueError("PHK-V2.1 engineering period must exceed the pulse fall")
        if not 0.05 < self.pulse_hold_end < 0.35:
            raise ValueError("PHK-V2.1 engineering hold must stay between rise and fall")
        for name in (
            "volumetric_cooling",
            "mobility_cold",
            "thermal_drive",
            "mobility_hot",
            "heater_width_fraction",
            "interface_width",
        ):
            if float(getattr(self, name)) <= 0.0:
                raise ValueError(f"PHK-V2.1 engineering {name} must be positive")
        if self.mobility_hot < self.mobility_cold:
            raise ValueError("PHK-V2.1 engineering hot mobility cannot be below cold mobility")
        if self.waveform_amplitude < 0.0 or self.latent_ratio < 0.0:
            raise ValueError("PHK-V2.1 engineering amplitude/latent ratio cannot be negative")


@dataclass(frozen=True)
class PhkV21EngineeringRun:
    result: PhkOracleResult
    event: PhkEventReport
    guard: PhkGuardReport
    phase_solver_statistics: Mapping[str, int | float | str]
    evidence_identity: str = "NON_VOTING_ENGINEERING_ONLY"


def build_engineering_physical(
    *,
    legacy: PhkPhysicalContract,
    phk_v21_program_path: Path,
    overrides: PhkV21EngineeringOverrides,
) -> PhkPhysicalContract:
    """Create an in-memory engineering view without writing a new object contract."""

    overrides.validate()
    program_path = Path(phk_v21_program_path).resolve()
    raw = program_path.read_bytes()
    program_payload = json.loads(raw.decode("utf-8"))
    program = PhkProgramContract(
        path=program_path,
        payload=program_payload,
        sha256=hashlib.sha256(raw).hexdigest().upper(),
    )
    payload = deepcopy(dict(legacy.payload))
    payload["schema_id"] = "phk-v21-engineering-object-view-v1"
    payload["contract_id"] = f"PHK_V21_ENGINEERING_{overrides.case_id}"
    payload["status"] = "NON_VOTING_ENGINEERING_ONLY"
    payload["coordinates"]["time_period"] = float(overrides.period)
    payload["coordinates"]["time_end"] = float(2.0 * overrides.period)
    payload["coefficients"]["volumetric_cooling"] = float(
        overrides.volumetric_cooling
    )
    payload["coefficients"]["mobility_cold"] = float(overrides.mobility_cold)
    payload["coefficients"]["mobility_hot"] = float(overrides.mobility_hot)
    payload["coefficients"]["thermal_drive"] = float(overrides.thermal_drive)
    payload["coefficients"]["latent_ratio"] = float(overrides.latent_ratio)
    payload["coefficients"]["interface_width"] = float(overrides.interface_width)
    payload["geometry"]["nominal_heater_width_fraction_of_total_x"] = float(
        overrides.heater_width_fraction
    )
    payload["waveform"]["amplitude"] = float(overrides.waveform_amplitude)
    payload["waveform"]["hold_end"] = float(overrides.pulse_hold_end)
    payload["fields"]["phase_fraction"]["range_guard"] = [0.0, 1.0]
    object_raw = _canonical_json(payload)
    object_contract = PhkObjectContract(
        path=Path("<PHK_V21_NON_VOTING_ENGINEERING_VIEW>"),
        payload=payload,
        sha256=hashlib.sha256(object_raw).hexdigest().upper(),
        program_sha256=program.sha256,
    )
    return PhkPhysicalContract(program=program, object=object_contract)


@contextmanager
def _patched_phase_solver(
    algorithm: PhkV21PhaseAlgorithm,
    statistics: dict[str, int | float | str],
) -> Iterator[None]:
    """Install one candidate for one serial engineering solve, then restore V2."""

    with _PHASE_PATCH_LOCK:
        original = _legacy._solve_phase_newton

        def solve(**kwargs: Any) -> tuple[Any, int, int, float]:
            solved = solve_phase_candidate(
                algorithm=algorithm,
                phase_old=kwargs["phase_old"],
                initial_guess=kwargs["initial_guess"],
                temperature=kwargs["temperature"],
                grid=kwargs["grid"],
                dt=float(kwargs["dt"]),
                coefficients=kwargs["coefficients"],
                interface_width=float(kwargs["interface_width"]),
                solver=kwargs["solver"],
                lower_bound=0.0,
                upper_bound=1.0,
            )
            statistics["phase_calls_total"] = int(
                statistics.get("phase_calls_total", 0)
            ) + 1
            for target, value in (
                ("phase_iterations_total", solved.iterations),
                ("phase_linear_solves_total", solved.linear_solves),
                ("phase_residual_evaluations_total", solved.residual_evaluations),
                ("phase_jacobian_evaluations_total", solved.jacobian_evaluations),
                ("phase_bound_rejections_total", solved.bound_rejections),
                ("phase_decrease_rejections_total", solved.decrease_rejections),
                ("phase_output_clipping_total", solved.output_clipping_count),
            ):
                statistics[target] = int(statistics.get(target, 0)) + int(value)
            statistics["maximum_phase_residual_inf"] = max(
                float(statistics.get("maximum_phase_residual_inf", 0.0)),
                float(solved.final_residual_inf),
            )
            return (
                solved.phase,
                solved.iterations,
                solved.linear_solves,
                solved.final_residual_inf,
            )

        _legacy._solve_phase_newton = solve
        try:
            yield
        finally:
            _legacy._solve_phase_newton = original


def run_engineering_case(
    *,
    legacy: PhkPhysicalContract,
    phk_v21_program_path: Path,
    overrides: PhkV21EngineeringOverrides,
    control: PhkControl,
    resolution: PhkResolution,
    algorithm: PhkV21PhaseAlgorithm,
) -> PhkV21EngineeringRun:
    """Run one in-memory, non-voting engineering case."""

    if resolution.evidence_identity != "NON_SCIENTIFIC_TEST_FIXTURE":
        raise ValueError("PHK-V2.1 engineering requires an explicit non-scientific resolution")
    physical = build_engineering_physical(
        legacy=legacy,
        phk_v21_program_path=phk_v21_program_path,
        overrides=overrides,
    )
    base_case = PhkCaseSpec.qualification(physical, control)
    case = replace(base_case, case_id=overrides.case_id)
    statistics: dict[str, int | float | str] = {"algorithm": algorithm.value}
    with _patched_phase_solver(algorithm, statistics):
        result = PhkOracleCase(
            physical=physical,
            case=case,
            resolution=resolution,
            allow_non_scientific_fixture=True,
        ).solve()
    event = PhkEventReport.from_result(result, physical=physical)
    guard = PhkGuardReport.from_result(result, physical=physical)
    return PhkV21EngineeringRun(
        result=result,
        event=event,
        guard=guard,
        phase_solver_statistics=statistics,
    )
