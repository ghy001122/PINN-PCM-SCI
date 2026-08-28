"""Independent PHK-V2.1 benchmark and result-carrier seam.

PHK-V2.1 inherits the byte-frozen PHK-V2 finite-volume operators, but it does
not inherit the failed PHK-V2 nonlinear acceptance range or any PHK-V2 result.
This module materializes the new object from exact pre-result contracts, binds
one selected phase solver without dynamic switching, and exposes the only
scientific CPU-oracle interface admitted by the PHK-V2.1 program.

Nothing in this module turns the non-voting E1/E2 engineering results into
scientific evidence.  A scientific claim requires a separately recorded Q run
that consumes the final object, split, oracle/floor, baseline, and method
contract hashes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import copy
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from numpy.typing import NDArray
from scipy import sparse
from scipy.sparse import linalg as sparse_linalg

from .phk_benchmark import (
    PhkControl,
    PhkConvergenceReport,
    PhkCycleEvent,
    PhkGrid,
    PhkGuardReport,
    PhkPhysicalContract,
    PhkResolution,
    _conductivity,
    _initial_phase,
    _interpolate_field_to,
    _interpolate_trace,
    _mapping,
    _maximum_absolute,
    _phase_residual_and_jacobian,
    run_phk_manufactured_checks,
    solve_electric_field,
)
from .phk_contract import PhkObjectContract, PhkProgramContract
from .phk_v21_solver import (
    PhkV21PhaseAlgorithm,
    solve_phase_candidate,
)


FloatArray = NDArray[np.float64]


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _read_json(path: Path, name: str) -> tuple[bytes, dict[str, Any]]:
    exact = Path(path).resolve()
    raw = exact.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid UTF-8 JSON {name}: {exact}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{name} root must be an object")
    return raw, payload


def _require_sha(actual: bytes, declared: Any, name: str) -> None:
    if not isinstance(declared, str) or declared != declared.upper():
        raise ValueError(f"{name} must be an uppercase SHA256")
    if _sha256(actual) != declared:
        raise ValueError(f"{name} byte identity mismatch")


def _deep_update(target: dict[str, Any], updates: Mapping[str, Any]) -> None:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)
        else:
            target[key] = copy.deepcopy(value)


def load_phk_v21_physical(
    *,
    program_path: Path,
    object_path: Path,
    legacy_program_path: Path,
    legacy_object_path: Path,
) -> PhkPhysicalContract:
    """Materialize the V2.1 object only after every inherited byte is verified."""

    program_raw, program_payload = _read_json(program_path, "PHK-V2.1 program")
    object_raw, overlay = _read_json(object_path, "PHK-V2.1 object overlay")
    if program_payload.get("schema_id") != "phk-v21-program-contract-v1":
        raise ValueError("unsupported PHK-V2.1 program schema")
    if program_payload.get("contract_id") != "PHK_V21_REPEATABLE_EVENT_PROGRAM_V1":
        raise ValueError("unexpected PHK-V2.1 program identity")
    if overlay.get("schema_id") != "phk-v21-object-overlay-contract-v1":
        raise ValueError("unsupported PHK-V2.1 object overlay schema")
    if overlay.get("contract_id") != "PHK_V21_REPEATABLE_EVENT_2D_NUMERICAL_V1":
        raise ValueError("unexpected PHK-V2.1 object identity")
    if overlay.get("status") not in {
        "DRAFT_PRE_VOTING_RESULT_IMPLEMENTATION_HASH_PENDING",
        "PRE_FIRST_VOTING_SOLVE_FREEZE",
    }:
        raise ValueError("PHK-V2.1 object is not in a pre-voting freeze state")
    if overlay.get("program_contract_sha256") != _sha256(program_raw):
        raise ValueError("PHK-V2.1 program/object binding mismatch")

    base = _mapping(overlay.get("base_identity"), "base_identity")
    legacy_program_raw = Path(legacy_program_path).resolve().read_bytes()
    legacy_object_raw = Path(legacy_object_path).resolve().read_bytes()
    _require_sha(
        legacy_program_raw,
        base.get("legacy_program_sha256"),
        "legacy program",
    )
    _require_sha(
        legacy_object_raw,
        base.get("legacy_object_sha256"),
        "legacy object",
    )
    legacy = PhkPhysicalContract.from_files(
        program_path=legacy_program_path,
        object_path=legacy_object_path,
    )

    root = Path(program_path).resolve().parents[2]
    engineering = _mapping(overlay.get("engineering_bindings"), "engineering_bindings")
    engineering_raw = (root / "configs" / "phk_v21" / "engineering_contract.json").read_bytes()
    _require_sha(
        engineering_raw,
        engineering.get("engineering_contract_sha256"),
        "PHK-V2.1 engineering contract",
    )
    selection_raw = (root / "configs" / "phk_v21" / "e1_solver_selection.json").read_bytes()
    _require_sha(
        selection_raw,
        engineering.get("e1_selection_sha256"),
        "PHK-V2.1 E1 solver selection",
    )
    e2_summary_path = (
        root / "outputs" / "runs" / str(engineering["e2_run_id"]) / "summary.json"
    )
    e2_raw, e2_payload = _read_json(e2_summary_path, "PHK-V2.1 E2 summary")
    _require_sha(e2_raw, engineering.get("e2_summary_sha256"), "PHK-V2.1 E2 summary")
    if e2_payload.get("accepted_for_new_scientific_freeze") is not True:
        raise ValueError("PHK-V2.1 E2 candidate was not admitted for a new freeze")
    selected = e2_payload.get("selected_nominal_case")
    if not isinstance(selected, dict):
        raise ValueError("PHK-V2.1 E2 summary lacks selected_case")
    if selected.get("physical_identity_sha256") != engineering.get(
        "selected_physical_identity_sha256"
    ):
        raise ValueError("PHK-V2.1 selected engineering physical identity mismatch")
    selected_overrides = selected.get("overrides")
    if not isinstance(selected_overrides, dict) or selected_overrides.get(
        "case_id"
    ) != engineering.get("selected_engineering_case_id"):
        raise ValueError("PHK-V2.1 selected engineering case mismatch")

    operator_path = root / str(base["legacy_operator_implementation_path"])
    _require_sha(
        operator_path.read_bytes(),
        base.get("legacy_operator_implementation_sha256"),
        "legacy finite-volume operator implementation",
    )
    implementation = _mapping(
        overlay.get("implementation_bindings"), "implementation_bindings"
    )
    for relative, key, label in (
        (
            "pinn_pcm_sci/phk_v21_benchmark.py",
            "phk_v21_benchmark_sha256",
            "PHK-V2.1 benchmark implementation",
        ),
        (
            "pinn_pcm_sci/phk_v21_solver.py",
            "phk_v21_solver_sha256",
            "PHK-V2.1 selected phase-solver implementation",
        ),
        (
            "tests/test_phk_v21_benchmark.py",
            "tests_sha256",
            "PHK-V2.1 benchmark regression tests",
        ),
    ):
        _require_sha(
            (root / relative).read_bytes(),
            implementation.get(key),
            label,
        )

    materialized = copy.deepcopy(dict(legacy.payload))
    overrides = _mapping(
        overlay.get("materialization_overrides"), "materialization_overrides"
    )
    ordinary_overrides = {
        key: value for key, value in overrides.items() if key != "fields"
    }
    _deep_update(materialized, ordinary_overrides)
    field_overrides = _mapping(overrides.get("fields"), "materialization_overrides.fields")
    phase_guard = field_overrides.get("phase_fraction_range_guard")
    if phase_guard != [0.0, 1.0]:
        raise ValueError("PHK-V2.1 physical phase range must be exactly [0, 1]")
    materialized["fields"]["phase_fraction"]["range_guard"] = [0.0, 1.0]

    fixed = _mapping(overlay.get("fixed_solver"), "fixed_solver")
    if fixed.get("primary_algorithm") != PhkV21PhaseAlgorithm.LOGIT_NEWTON_ANALYTIC_JACOBIAN.value:
        raise ValueError("PHK-V2.1 primary phase solver is not the E1 selection")
    if fixed.get("crosscheck_algorithm") != PhkV21PhaseAlgorithm.PSEUDO_TRANSIENT_NEWTON.value:
        raise ValueError("PHK-V2.1 crosscheck phase solver identity mismatch")
    if fixed.get("dynamic_switching") is not False:
        raise ValueError("PHK-V2.1 dynamic phase-solver switching is prohibited")
    if fixed.get("output_clipping") is not False:
        raise ValueError("PHK-V2.1 output clipping is prohibited")
    if fixed.get("result_adaptive_rescue") is not False:
        raise ValueError("PHK-V2.1 result-adaptive rescue is prohibited")
    materialized["nonlinear_solver"].update(
        {
            "transport_newton_residual_tolerance": float(fixed["residual_tolerance"]),
            "transport_newton_max_iterations": int(fixed["maximum_iterations"]),
            "newton_initial_step": float(fixed["logit_initial_step"]),
            "line_search_reduction": float(fixed["line_search_reduction"]),
            "line_search_min_step": float(fixed["line_search_min_step"]),
            "coupled_relative_change_tolerance": float(
                fixed["coupled_relative_change_tolerance"]
            ),
            "coupled_residual_tolerance": float(fixed["coupled_residual_tolerance"]),
            "coupled_max_blocks": int(fixed["coupled_max_blocks"]),
            "coupled_relaxation": float(fixed["coupled_relaxation"]),
            "failure_is_consumed_intent": bool(fixed["failed_intent_is_consumed"]),
            "result_adaptive_rescue": bool(fixed["result_adaptive_rescue"]),
        }
    )
    materialized["resolutions"] = copy.deepcopy(overlay["resolutions"])
    materialized["qualification_intents"] = copy.deepcopy(
        overlay["qualification_intents"]
    )
    factors = _mapping(overlay["complete_case_factors"], "complete_case_factors")
    materialized["factor_supports"] = {
        "heater_width_fraction": list(factors["nominal_geometry"]["heater_width_fraction"]),
        "interface_width": list(factors["nominal_geometry"]["interface_width"]),
        **copy.deepcopy(dict(factors["protocol_and_state_support"])),
        "constitutive_branch": [factors["fixed"]["constitutive_branch"]],
    }
    materialized["split_rules"] = copy.deepcopy(overlay["split_generation"])
    materialized["prohibitions"] = copy.deepcopy(overlay["prohibitions"])

    coordinates = _mapping(materialized["coordinates"], "coordinates")
    if int(coordinates.get("pulse_cycles", 0)) != 2:
        raise ValueError("PHK-V2.1 requires exactly two cycles")
    if not math.isclose(
        float(coordinates["time_end"]),
        2.0 * float(coordinates["time_period"]),
        rel_tol=0.0,
        abs_tol=1.0e-15,
    ):
        raise ValueError("PHK-V2.1 object time_end must equal two periods")
    selected_expected = {
        "period": coordinates["time_period"],
        "volumetric_cooling": materialized["coefficients"]["volumetric_cooling"],
        "mobility_cold": materialized["coefficients"]["mobility_cold"],
        "mobility_hot": materialized["coefficients"]["mobility_hot"],
        "thermal_drive": materialized["coefficients"]["thermal_drive"],
        "latent_ratio": materialized["coefficients"]["latent_ratio"],
        "waveform_amplitude": materialized["waveform"]["amplitude"],
        "pulse_hold_end": materialized["waveform"]["hold_end"],
        "heater_width_fraction": materialized["geometry"][
            "nominal_heater_width_fraction_of_total_x"
        ],
        "interface_width": materialized["coefficients"]["interface_width"],
    }
    for key, value in selected_expected.items():
        if selected_overrides.get(key) != value:
            raise ValueError(f"PHK-V2.1 materialized object drifts from E2: {key}")

    program = PhkProgramContract(
        path=Path(program_path).resolve(),
        payload=program_payload,
        sha256=_sha256(program_raw),
    )
    physical = PhkObjectContract(
        path=Path(object_path).resolve(),
        payload=materialized,
        sha256=_sha256(object_raw),
        program_sha256=program.sha256,
    )
    return PhkPhysicalContract(program=program, object=physical)


@dataclass(frozen=True)
class PhkV21CaseSpec:
    """Complete PHK-V2.1 physical-case identity."""

    control: PhkControl
    heater_width_fraction: float
    interface_width: float
    waveform_amplitude: float
    pulse_hold_end: float
    period: float
    volumetric_cooling: float
    mobility_cold: float
    mobility_hot: float
    initial_phase_background: float
    thermal_drive: float
    latent_ratio: float
    constitutive_branch: str
    case_id: str

    def validate(self, physical: PhkPhysicalContract) -> None:
        waveform = _mapping(physical.payload["waveform"], "waveform")
        positive = (
            "heater_width_fraction",
            "interface_width",
            "period",
            "volumetric_cooling",
            "mobility_cold",
            "mobility_hot",
            "thermal_drive",
        )
        for name in positive:
            value = float(getattr(self, name))
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"PHK-V2.1 case {name} must be positive and finite")
        if not 0.0 < self.heater_width_fraction <= 1.0:
            raise ValueError("PHK-V2.1 heater width must be in (0, 1]")
        if not 0.0 <= self.waveform_amplitude <= 1.0:
            raise ValueError("PHK-V2.1 waveform amplitude must be in [0, 1]")
        if not float(waveform["ramp_up_end"]) < self.pulse_hold_end < float(
            waveform["ramp_down_end"]
        ):
            raise ValueError("PHK-V2.1 pulse hold must lie between ramp breakpoints")
        if self.period <= float(waveform["ramp_down_end"]):
            raise ValueError("PHK-V2.1 period must include a recovery segment")
        if not 0.0 < self.initial_phase_background < 0.5:
            raise ValueError("PHK-V2.1 initial phase must be in the cold basin")
        if not math.isfinite(self.latent_ratio) or self.latent_ratio < 0.0:
            raise ValueError("PHK-V2.1 latent ratio must be finite and nonnegative")
        if self.constitutive_branch != "NOMINAL":
            raise ValueError("PHK-V2.1 admits only its frozen nominal branch")
        if not self.case_id:
            raise ValueError("PHK-V2.1 case_id cannot be empty")

    def physics_identity(self) -> dict[str, Any]:
        return {
            "geometry": {
                "heater_width_fraction": self.heater_width_fraction,
                "interface_width": self.interface_width,
            },
            "constitutive_branch": self.constitutive_branch,
            "initial_state": {
                "phase_background": self.initial_phase_background,
            },
            "full_waveform": {
                "amplitude": self.waveform_amplitude,
                "pulse_hold_end": self.pulse_hold_end,
                "period": self.period,
                "cycles": 2,
            },
            "full_history": {
                "volumetric_cooling": self.volumetric_cooling,
                "mobility_cold": self.mobility_cold,
                "mobility_hot": self.mobility_hot,
                "thermal_drive": self.thermal_drive,
                "latent_ratio": self.latent_ratio,
            },
        }

    @classmethod
    def nominal(
        cls,
        physical: PhkPhysicalContract,
        *,
        control: PhkControl = PhkControl.FULL,
        case_id: str | None = None,
    ) -> "PhkV21CaseSpec":
        coefficients = physical.coefficients
        geometry = _mapping(physical.payload["geometry"], "geometry")
        waveform = _mapping(physical.payload["waveform"], "waveform")
        coordinates = physical.coordinates
        heater = float(geometry["nominal_heater_width_fraction_of_total_x"])
        interface = float(coefficients["interface_width"])
        amplitude = float(waveform["amplitude"])
        if control is PhkControl.ZERO_DRIVE:
            amplitude = 0.0
        elif control is PhkControl.HEATER_WIDTH_0_50:
            heater = 0.50
        elif control is PhkControl.INTERFACE_WIDTH_0_025:
            interface = 0.025
        provisional = cls(
            control=control,
            heater_width_fraction=heater,
            interface_width=interface,
            waveform_amplitude=amplitude,
            pulse_hold_end=float(waveform["hold_end"]),
            period=float(coordinates["time_period"]),
            volumetric_cooling=float(coefficients["volumetric_cooling"]),
            mobility_cold=float(coefficients["mobility_cold"]),
            mobility_hot=float(coefficients["mobility_hot"]),
            initial_phase_background=float(coefficients["initial_phase_background"]),
            thermal_drive=float(coefficients["thermal_drive"]),
            latent_ratio=float(coefficients["latent_ratio"]),
            constitutive_branch="NOMINAL",
            case_id=case_id or "PENDING",
        )
        if case_id is None:
            digest = _sha256(_canonical_json(provisional.physics_identity()))
            provisional = cls(
                **{
                    **asdict(provisional),
                    "control": control,
                    "case_id": f"PHK_V21_Q_{control.value}_{digest[:16]}",
                }
            )
        provisional.validate(physical)
        return provisional


def phk_v21_resolution(
    physical: PhkPhysicalContract,
    name: str,
    *,
    period: float,
) -> PhkResolution:
    resolutions = _mapping(physical.payload["resolutions"], "resolutions")
    if name not in resolutions:
        raise ValueError(f"unknown PHK-V2.1 frozen resolution: {name}")
    item = _mapping(resolutions[name], f"resolutions.{name}")
    return PhkResolution(
        name=name,
        nx=int(item["nx"]),
        nz=int(item["nz"]),
        dt=float(item["dt"]),
        time_end=2.0 * float(period),
        save_every=int(item["save_every"]),
        evidence_identity="PHK_V21_FROZEN_Q_RESOLUTION",
    )


def _case_from_factors(
    physical: PhkPhysicalContract,
    *,
    factors: Mapping[str, Any],
    control: PhkControl = PhkControl.FULL,
) -> PhkV21CaseSpec:
    fixed = physical.coefficients
    provisional = PhkV21CaseSpec(
        control=control,
        heater_width_fraction=float(factors["heater_width_fraction"]),
        interface_width=float(factors["interface_width"]),
        waveform_amplitude=float(factors["waveform_amplitude"]),
        pulse_hold_end=float(factors["pulse_hold_end"]),
        period=float(factors["period"]),
        volumetric_cooling=float(factors["volumetric_cooling"]),
        mobility_cold=float(fixed["mobility_cold"]),
        mobility_hot=float(fixed["mobility_hot"]),
        initial_phase_background=float(factors["initial_phase_background"]),
        thermal_drive=float(fixed["thermal_drive"]),
        latent_ratio=float(fixed["latent_ratio"]),
        constitutive_branch="NOMINAL",
        case_id="PENDING",
    )
    digest = _sha256(_canonical_json(provisional.physics_identity()))
    case = PhkV21CaseSpec(
        **{
            **asdict(provisional),
            "control": control,
            "case_id": f"PHK_V21_{digest}",
        }
    )
    case.validate(physical)
    return case


def build_phk_v21_split_manifest(
    *,
    physical: PhkPhysicalContract,
) -> dict[str, Any]:
    """Build the exact outcome-blind 128-case D/I/formal/reserve split."""

    _, overlay = _read_json(physical.object.path, "PHK-V2.1 object overlay")
    if _sha256(Path(physical.object.path).read_bytes()) != physical.object.sha256:
        raise ValueError("PHK-V2.1 object bytes drifted after physical materialization")
    factors = _mapping(overlay["complete_case_factors"], "complete_case_factors")
    protocol = _mapping(
        factors["protocol_and_state_support"],
        "complete_case_factors.protocol_and_state_support",
    )
    nominal_geometry = _mapping(
        factors["nominal_geometry"], "complete_case_factors.nominal_geometry"
    )
    axes = (
        "waveform_amplitude",
        "pulse_hold_end",
        "period",
        "volumetric_cooling",
        "initial_phase_background",
    )
    if tuple(protocol) != axes:
        raise ValueError("PHK-V2.1 protocol/state axis order drifted")
    nominal_candidates: list[PhkV21CaseSpec] = []
    for values in itertools.product(*(protocol[name] for name in axes)):
        item = dict(zip(axes, values, strict=True))
        item.update(
            {
                "heater_width_fraction": nominal_geometry[
                    "heater_width_fraction"
                ][0],
                "interface_width": nominal_geometry["interface_width"][0],
            }
        )
        nominal_candidates.append(_case_from_factors(physical, factors=item))
    nominal_candidates.sort(key=lambda item: item.case_id)
    if len(nominal_candidates) != 243 or len(
        {item.case_id for item in nominal_candidates}
    ) != 243:
        raise ValueError("PHK-V2.1 nominal candidate universe is not 243 unique cases")

    nominal_pools = (
        ("D", 24),
        ("I1", 12),
        ("I2", 12),
        ("F_A", 32),
        ("R", 16),
    )
    cases: dict[str, dict[str, Any]] = {}
    cursor = 0
    for pool, count in nominal_pools:
        for case in nominal_candidates[cursor : cursor + count]:
            cases[case.case_id] = {
                "pool": pool,
                "selection_role": "NOMINAL_HASH_ORDER_PREFIX",
                "case": asdict(case),
                "physics_identity": case.physics_identity(),
            }
        cursor += count
    if cursor != 96:
        raise AssertionError("PHK-V2.1 nominal split cursor drifted")

    orthogonal = _mapping(
        factors["formal_orthogonal_axes"],
        "complete_case_factors.formal_orthogonal_axes",
    )
    formal_axes = (
        ("heater_width_fraction", value)
        for value in orthogonal["heater_width_fraction"]
    )
    formal_values = list(formal_axes) + [
        ("interface_width", value) for value in orthogonal["interface_width"]
    ]
    for held_axis, held_value in formal_values:
        candidates: list[PhkV21CaseSpec] = []
        for values in itertools.product(*(protocol[name] for name in axes)):
            item = dict(zip(axes, values, strict=True))
            item.update(
                {
                    "heater_width_fraction": nominal_geometry[
                        "heater_width_fraction"
                    ][0],
                    "interface_width": nominal_geometry["interface_width"][0],
                    held_axis: held_value,
                }
            )
            candidates.append(_case_from_factors(physical, factors=item))
        candidates.sort(key=lambda item: item.case_id)
        for case in candidates[:8]:
            if case.case_id in cases:
                raise ValueError("PHK-V2.1 case crossed a pool boundary")
            cases[case.case_id] = {
                "pool": "F_O",
                "selection_role": "WHOLE_FACTOR_HASH_PREFIX",
                "held_out_factor": held_axis,
                "held_out_value": held_value,
                "case": asdict(case),
                "physics_identity": case.physics_identity(),
            }

    counts = {
        pool: sum(1 for item in cases.values() if item["pool"] == pool)
        for pool in ("D", "I1", "I2", "F_A", "F_O", "R")
    }
    expected_counts = _mapping(
        _mapping(overlay["split_generation"], "split_generation")["pool_counts"],
        "split_generation.pool_counts",
    )
    if counts != dict(expected_counts) or len(cases) != 128:
        raise ValueError("PHK-V2.1 generated pool counts do not match the freeze")
    payload: dict[str, Any] = {
        "schema_id": "phk-v21-complete-case-split-manifest-v1",
        "contract_id": "PHK_V21_CASE_SPLIT_V1",
        "status": "PRE_FIRST_CASE_RESULT_WRITE_ONCE_FREEZE",
        "evidence_identity": "OUTCOME_BLIND_COMPLETE_PHYSICAL_CASE_SPLIT",
        "program_contract_sha256": physical.program.sha256,
        "object_contract_sha256": physical.object.sha256,
        "case_identity_formula": overlay["split_generation"]["case_id"],
        "candidate_universe": {
            "nominal_count": 243,
            "nominal_case_ids_sorted": [
                item.case_id for item in nominal_candidates
            ],
            "nominal_selected_prefix_count": 96,
            "formal_orthogonal_candidates_per_whole_factor_value": 243,
            "formal_orthogonal_selected_per_whole_factor_value": 8,
            "engineering_cases_included": 0,
        },
        "pool_counts": counts,
        "pool_open_policy": {
            "Q": "SEPARATE_QUALIFICATION_INTENTS_ONLY",
            "D": "TRAINING_AND_HYPERPARAMETER_DEVELOPMENT_ONLY",
            "I1": "OPEN_ONCE_AFTER_BOTTLENECK_ARMS_FREEZE",
            "I2": "OPEN_ONCE_AFTER_FACTORIAL_ARMS_FREEZE",
            "F_A": "SEALED_UNSEEN_PROTOCOL_CASES",
            "F_O": "SEALED_WHOLE_GEOMETRY_FACTOR_HOLDOUTS",
            "R": "NEVER_OPEN_IN_THIS_GOAL",
        },
        "cases": {key: cases[key] for key in sorted(cases)},
    }
    payload["manifest_sha256"] = _sha256(_canonical_json(payload))
    return payload


def write_phk_v21_split_manifest(path: Path, payload: Mapping[str, Any]) -> None:
    """Write a canonical split manifest exactly once."""

    exact = Path(path)
    raw = _canonical_json(payload) + b"\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    descriptor = os.open(exact, flags, 0o644)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        exact.unlink(missing_ok=True)
        raise


def load_phk_v21_split_manifest(
    path: Path,
    *,
    physical: PhkPhysicalContract,
) -> Mapping[str, Any]:
    """Fail closed unless a split is byte-equivalent to exact regeneration."""

    _, payload = _read_json(path, "PHK-V2.1 split manifest")
    expected = build_phk_v21_split_manifest(physical=physical)
    if payload != expected:
        raise ValueError("PHK-V2.1 split does not match the frozen contracts")
    return payload


@dataclass(frozen=True)
class PhkV21OracleResult:
    physical_contract_id: str
    program_contract_sha256: str
    object_contract_sha256: str
    case: PhkV21CaseSpec
    resolution: PhkResolution
    phase_algorithm: str
    grid: PhkGrid
    time: FloatArray
    potential: FloatArray
    temperature: FloatArray
    phase: FloatArray
    top_current: FloatArray
    bottom_current: FloatArray
    joule_power: FloatArray
    current_balance_history: FloatArray
    thermal_residual_history: FloatArray
    phase_residual_history: FloatArray
    coupled_change_history: FloatArray
    linear_residual_history: FloatArray
    solver_statistics: Mapping[str, int | float]
    evidence_identity: str


@dataclass
class _V21Counters:
    time_steps: int = 0
    coupled_blocks: int = 0
    electric_linear_solves: int = 0
    thermal_linear_solves: int = 0
    phase_solver_calls: int = 0
    phase_iterations: int = 0
    phase_residual_evaluations: int = 0
    phase_jacobian_evaluations: int = 0
    phase_linear_solves: int = 0
    phase_bound_rejections: int = 0
    phase_decrease_rejections: int = 0
    output_clipping_count: int = 0
    final_residual_evaluations: int = 0


class PhkV21OracleCase:
    """One fixed-algorithm V2.1 finite-volume case; no result-adaptive rescue."""

    def __init__(
        self,
        *,
        physical: PhkPhysicalContract,
        case: PhkV21CaseSpec,
        resolution: PhkResolution,
        phase_algorithm: PhkV21PhaseAlgorithm = (
            PhkV21PhaseAlgorithm.LOGIT_NEWTON_ANALYTIC_JACOBIAN
        ),
        allow_non_scientific_fixture: bool = False,
    ) -> None:
        case.validate(physical)
        if (
            resolution.evidence_identity == "NON_SCIENTIFIC_TEST_FIXTURE"
            and not allow_non_scientific_fixture
        ):
            raise ValueError("non-scientific fixture requires explicit opt-in")
        if resolution.evidence_identity not in {
            "NON_SCIENTIFIC_TEST_FIXTURE",
            "PHK_V21_FROZEN_Q_RESOLUTION",
        }:
            raise ValueError("unknown PHK-V2.1 resolution evidence identity")
        admitted = {
            PhkV21PhaseAlgorithm.LOGIT_NEWTON_ANALYTIC_JACOBIAN,
            PhkV21PhaseAlgorithm.PSEUDO_TRANSIENT_NEWTON,
        }
        if phase_algorithm not in admitted:
            raise ValueError("phase algorithm is not admitted by the V2.1 object freeze")
        self.physical = physical
        self.case = case
        self.resolution = resolution
        self.phase_algorithm = phase_algorithm

    def waveform(self, time_value: float) -> float:
        waveform = _mapping(self.physical.payload["waveform"], "waveform")
        start = float(self.physical.coordinates["time_start"])
        if time_value < start or time_value >= self.resolution.time_end:
            return 0.0
        local = (float(time_value) - start) % self.case.period
        amplitude = self.case.waveform_amplitude
        rise = float(waveform["ramp_up_end"])
        hold = self.case.pulse_hold_end
        fall = float(waveform["ramp_down_end"])
        if local < rise:
            return amplitude * local / rise
        if local <= hold:
            return amplitude
        if local < fall:
            return amplitude * (fall - local) / (fall - hold)
        return 0.0

    def solve(self) -> PhkV21OracleResult:
        coordinates = self.physical.coordinates
        grid = PhkGrid.build(
            nx=self.resolution.nx,
            nz=self.resolution.nz,
            x_min=float(coordinates["x_min"]),
            x_max=float(coordinates["x_max"]),
            z_min=float(coordinates["z_min"]),
            z_max=float(coordinates["z_max"]),
        )
        dt = float(self.resolution.dt)
        step_count_float = self.resolution.time_end / dt
        step_count = int(round(step_count_float))
        if not math.isclose(step_count_float, step_count, rel_tol=0.0, abs_tol=1.0e-12):
            raise ValueError("PHK-V2.1 time_end must contain an integral number of steps")

        coefficients = dict(self.physical.coefficients)
        coefficients.update(
            {
                "volumetric_cooling": self.case.volumetric_cooling,
                "mobility_cold": self.case.mobility_cold,
                "mobility_hot": self.case.mobility_hot,
                "thermal_drive": self.case.thermal_drive,
                "latent_ratio": self.case.latent_ratio,
            }
        )
        if self.case.control is PhkControl.JOULE_GAIN_ZERO:
            coefficients["joule_gain"] = 0.0
        if self.case.control is PhkControl.CONDUCTIVITY_PHASE_RATIO_ONE:
            coefficients["conductivity_phase_ratio"] = 1.0
        if self.case.control is PhkControl.LATENT_RATIO_ZERO:
            coefficients["latent_ratio"] = 0.0

        field_guards = _mapping(self.physical.payload["fields"], "fields")
        phase_range = _mapping(
            field_guards["phase_fraction"], "fields.phase_fraction"
        )["range_guard"]
        lower_bound, upper_bound = float(phase_range[0]), float(phase_range[1])
        if (lower_bound, upper_bound) != (0.0, 1.0):
            raise ValueError("PHK-V2.1 solver requires the physical phase range [0, 1]")
        phase_old = _initial_phase(
            grid, coefficients, self.case.initial_phase_background
        ).astype(np.float64)
        if np.any(phase_old <= lower_bound) or np.any(phase_old >= upper_bound):
            raise RuntimeError("initial PHK-V2.1 phase must be strictly interior")
        temperature_old = np.zeros(grid.cell_count, dtype=np.float64)

        geometry = _mapping(self.physical.payload["geometry"], "geometry")
        thermal_laplacian = grid.thermal_laplacian(
            float(geometry["thermal_robin_biot"])
        )
        identity = sparse.eye(grid.cell_count, format="csc")
        thermal_matrix = (
            identity
            - dt
            * float(coefficients["thermal_diffusivity"])
            * thermal_laplacian.tocsc()
            + dt * float(coefficients["volumetric_cooling"]) * identity
        )
        thermal_factor = sparse_linalg.splu(thermal_matrix)
        solver = self.physical.nonlinear_solver
        maximum_blocks = int(solver["coupled_max_blocks"])
        block_tolerance = float(solver["coupled_relative_change_tolerance"])
        residual_tolerance = float(solver["coupled_residual_tolerance"])
        if float(solver["coupled_relaxation"]) != 1.0:
            raise ValueError("PHK-V2.1 admits only its frozen unit block relaxation")
        if solver.get("result_adaptive_rescue") is not False:
            raise ValueError("PHK-V2.1 result-adaptive rescue must remain disabled")

        save_steps = list(range(0, step_count + 1, self.resolution.save_every))
        if save_steps[-1] != step_count:
            save_steps.append(step_count)
        save_lookup = {step: index for index, step in enumerate(save_steps)}
        saved_count = len(save_steps)
        times = np.asarray(save_steps, dtype=np.float64) * dt
        potential_saved = np.empty((saved_count, grid.cell_count), dtype=np.float64)
        temperature_saved = np.empty_like(potential_saved)
        phase_saved = np.empty_like(potential_saved)
        top_current = np.empty(saved_count, dtype=np.float64)
        bottom_current = np.empty(saved_count, dtype=np.float64)
        joule_power = np.empty(saved_count, dtype=np.float64)

        conductivity_initial = _conductivity(
            temperature_old,
            phase_old,
            phase_ratio=float(coefficients["conductivity_phase_ratio"]),
            temperature_gain=float(coefficients["conductivity_temperature_gain"]),
        )
        electric_initial = solve_electric_field(
            grid=grid,
            conductivity=conductivity_initial,
            applied_voltage=self.waveform(0.0),
            heater_width_fraction=self.case.heater_width_fraction,
        )
        potential_saved[0] = electric_initial.potential
        temperature_saved[0] = temperature_old
        phase_saved[0] = phase_old
        top_current[0] = electric_initial.top_current
        bottom_current[0] = electric_initial.bottom_current
        joule_power[0] = electric_initial.joule_power_total

        current_balance_history = np.empty(step_count, dtype=np.float64)
        thermal_residual_history = np.empty(step_count, dtype=np.float64)
        phase_residual_history = np.empty(step_count, dtype=np.float64)
        coupled_change_history = np.empty(step_count, dtype=np.float64)
        linear_residual_history = np.empty(step_count, dtype=np.float64)
        counters = _V21Counters(electric_linear_solves=1)
        maximum_candidate_residual = 0.0

        for step in range(1, step_count + 1):
            time_value = step * dt
            temperature_iter = temperature_old.copy()
            phase_iter = phase_old.copy()
            accepted: tuple[Any, FloatArray, FloatArray, float, float] | None = None
            for _block in range(1, maximum_blocks + 1):
                conductivity = _conductivity(
                    temperature_iter,
                    phase_iter,
                    phase_ratio=float(coefficients["conductivity_phase_ratio"]),
                    temperature_gain=float(coefficients["conductivity_temperature_gain"]),
                )
                electric = solve_electric_field(
                    grid=grid,
                    conductivity=conductivity,
                    applied_voltage=self.waveform(time_value),
                    heater_width_fraction=self.case.heater_width_fraction,
                )
                counters.electric_linear_solves += 1
                phase_solve = solve_phase_candidate(
                    algorithm=self.phase_algorithm,
                    phase_old=phase_old,
                    initial_guess=phase_iter,
                    temperature=temperature_iter,
                    grid=grid,
                    dt=dt,
                    coefficients=coefficients,
                    interface_width=self.case.interface_width,
                    solver=solver,
                    lower_bound=lower_bound,
                    upper_bound=upper_bound,
                )
                counters.phase_solver_calls += 1
                counters.phase_iterations += int(phase_solve.iterations)
                counters.phase_residual_evaluations += int(
                    phase_solve.residual_evaluations
                )
                counters.phase_jacobian_evaluations += int(
                    phase_solve.jacobian_evaluations
                )
                counters.phase_linear_solves += int(phase_solve.linear_solves)
                counters.phase_bound_rejections += int(phase_solve.bound_rejections)
                counters.phase_decrease_rejections += int(
                    phase_solve.decrease_rejections
                )
                counters.output_clipping_count += int(
                    phase_solve.output_clipping_count
                )
                maximum_candidate_residual = max(
                    maximum_candidate_residual, float(phase_solve.final_residual_inf)
                )
                if not phase_solve.converged:
                    raise RuntimeError("PHK-V2.1 phase solver returned unconverged")
                phase_target = phase_solve.phase
                thermal_rhs = (
                    temperature_old
                    - float(coefficients["latent_ratio"]) * (phase_target - phase_old)
                    + dt * float(coefficients["joule_gain"]) * electric.joule_density
                )
                temperature_target = thermal_factor.solve(thermal_rhs).astype(np.float64)
                counters.thermal_linear_solves += 1
                block_change = max(
                    _maximum_absolute(temperature_target - temperature_iter)
                    / max(1.0, _maximum_absolute(temperature_target)),
                    _maximum_absolute(phase_target - phase_iter)
                    / max(1.0, _maximum_absolute(phase_target)),
                )
                temperature_iter = temperature_target
                phase_iter = phase_target
                counters.coupled_blocks += 1
                if block_change <= block_tolerance:
                    final_conductivity = _conductivity(
                        temperature_iter,
                        phase_iter,
                        phase_ratio=float(coefficients["conductivity_phase_ratio"]),
                        temperature_gain=float(
                            coefficients["conductivity_temperature_gain"]
                        ),
                    )
                    final_electric = solve_electric_field(
                        grid=grid,
                        conductivity=final_conductivity,
                        applied_voltage=self.waveform(time_value),
                        heater_width_fraction=self.case.heater_width_fraction,
                    )
                    counters.electric_linear_solves += 1
                    counters.final_residual_evaluations += 1
                    phase_residual, _ = _phase_residual_and_jacobian(
                        phase_iter,
                        phase_old=phase_old,
                        temperature=temperature_iter,
                        grid=grid,
                        dt=dt,
                        coefficients=coefficients,
                        interface_width=self.case.interface_width,
                    )
                    final_thermal_rhs = (
                        temperature_old
                        - float(coefficients["latent_ratio"])
                        * (phase_iter - phase_old)
                        + dt
                        * float(coefficients["joule_gain"])
                        * final_electric.joule_density
                    )
                    thermal_residual = (
                        thermal_matrix @ temperature_iter - final_thermal_rhs
                    )
                    phase_norm = _maximum_absolute(phase_residual)
                    thermal_norm = _maximum_absolute(thermal_residual)
                    if max(phase_norm, thermal_norm) <= residual_tolerance:
                        accepted = (
                            final_electric,
                            temperature_iter,
                            phase_iter,
                            thermal_norm,
                            phase_norm,
                        )
                        coupled_change_history[step - 1] = block_change
                        break
            if accepted is None:
                raise RuntimeError(
                    "PHK-V2.1 electrothermal-phase block exceeded its frozen iteration limit"
                )
            final_electric, temperature_new, phase_new, thermal_norm, phase_norm = accepted
            if not (
                np.isfinite(temperature_new).all()
                and np.isfinite(phase_new).all()
                and np.isfinite(final_electric.potential).all()
            ):
                raise RuntimeError("PHK-V2.1 solver produced non-finite state")
            if np.any(phase_new < lower_bound) or np.any(phase_new > upper_bound):
                raise RuntimeError("PHK-V2.1 accepted phase is outside [0, 1]")

            current_balance_history[step - 1] = (
                final_electric.current_balance_relative
            )
            thermal_residual_history[step - 1] = thermal_norm
            phase_residual_history[step - 1] = phase_norm
            linear_residual_history[step - 1] = final_electric.linear_residual_scaled
            counters.time_steps += 1
            if step in save_lookup:
                index = save_lookup[step]
                potential_saved[index] = final_electric.potential
                temperature_saved[index] = temperature_new
                phase_saved[index] = phase_new
                top_current[index] = final_electric.top_current
                bottom_current[index] = final_electric.bottom_current
                joule_power[index] = final_electric.joule_power_total
            temperature_old = temperature_new
            phase_old = phase_new

        if counters.output_clipping_count != 0:
            raise RuntimeError("PHK-V2.1 output clipping count must remain zero")
        statistics = {
            "time_steps_total": counters.time_steps,
            "coupled_blocks_total": counters.coupled_blocks,
            "electric_linear_solves_total": counters.electric_linear_solves,
            "thermal_linear_solves_total": counters.thermal_linear_solves,
            "phase_solver_calls_total": counters.phase_solver_calls,
            "phase_iterations_total": counters.phase_iterations,
            "phase_residual_evaluations_total": counters.phase_residual_evaluations,
            "phase_jacobian_evaluations_total": counters.phase_jacobian_evaluations,
            "phase_linear_solves_total": counters.phase_linear_solves,
            "phase_bound_rejections_total": counters.phase_bound_rejections,
            "phase_decrease_rejections_total": counters.phase_decrease_rejections,
            "output_clipping_count": counters.output_clipping_count,
            "final_residual_evaluations_total": counters.final_residual_evaluations,
            "maximum_phase_candidate_residual_inf": maximum_candidate_residual,
            "linear_solves_total": (
                counters.electric_linear_solves
                + counters.thermal_linear_solves
                + counters.phase_linear_solves
            ),
        }
        return PhkV21OracleResult(
            physical_contract_id=self.physical.contract_id,
            program_contract_sha256=self.physical.program.sha256,
            object_contract_sha256=self.physical.object.sha256,
            case=self.case,
            resolution=self.resolution,
            phase_algorithm=self.phase_algorithm.value,
            grid=grid,
            time=times,
            potential=potential_saved,
            temperature=temperature_saved,
            phase=phase_saved,
            top_current=top_current,
            bottom_current=bottom_current,
            joule_power=joule_power,
            current_balance_history=current_balance_history,
            thermal_residual_history=thermal_residual_history,
            phase_residual_history=phase_residual_history,
            coupled_change_history=coupled_change_history,
            linear_residual_history=linear_residual_history,
            solver_statistics=statistics,
            evidence_identity=self.resolution.evidence_identity,
        )


def write_phk_v21_result(path: Path, result: PhkV21OracleResult) -> None:
    """Write one immutable, identity-bound V2.1 result carrier."""

    exact = Path(path)
    metadata = {
        "schema_id": "phk-v21-oracle-result-npz-v1",
        "physical_contract_id": result.physical_contract_id,
        "program_contract_sha256": result.program_contract_sha256,
        "object_contract_sha256": result.object_contract_sha256,
        "case": asdict(result.case),
        "resolution": asdict(result.resolution),
        "phase_algorithm": result.phase_algorithm,
        "evidence_identity": result.evidence_identity,
        "solver_statistics": dict(result.solver_statistics),
    }
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    descriptor = os.open(exact, flags, 0o644)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            np.savez_compressed(
                handle,
                metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
                x=result.grid.cell_x,
                z=result.grid.cell_z,
                cell_volumes=result.grid.cell_volumes,
                time=result.time,
                potential=result.potential,
                temperature=result.temperature,
                phase=result.phase,
                top_current=result.top_current,
                bottom_current=result.bottom_current,
                joule_power=result.joule_power,
                current_balance_history=result.current_balance_history,
                thermal_residual_history=result.thermal_residual_history,
                phase_residual_history=result.phase_residual_history,
                coupled_change_history=result.coupled_change_history,
                linear_residual_history=result.linear_residual_history,
            )
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        exact.unlink(missing_ok=True)
        raise


_RESULT_ARRAYS = {
    "metadata_json",
    "x",
    "z",
    "cell_volumes",
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
}


def read_phk_v21_result(
    path: Path,
    *,
    physical: PhkPhysicalContract,
) -> PhkV21OracleResult:
    """Load a V2.1 carrier after exact contract, mesh, time, and shape checks."""

    exact = Path(path)
    try:
        with np.load(exact, allow_pickle=False) as archive:
            if set(archive.files) != _RESULT_ARRAYS:
                raise ValueError("PHK-V2.1 result contains missing or unknown arrays")
            metadata = json.loads(str(archive["metadata_json"].item()))
            arrays = {
                name: np.asarray(archive[name], dtype=np.float64).copy()
                for name in _RESULT_ARRAYS - {"metadata_json"}
            }
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        raise ValueError(f"invalid PHK-V2.1 result carrier: {exact}") from exc
    if not isinstance(metadata, dict) or metadata.get("schema_id") != (
        "phk-v21-oracle-result-npz-v1"
    ):
        raise ValueError("unsupported PHK-V2.1 result schema")
    expected = {
        "physical_contract_id": physical.contract_id,
        "program_contract_sha256": physical.program.sha256,
        "object_contract_sha256": physical.object.sha256,
    }
    for key, value in expected.items():
        if metadata.get(key) != value:
            raise ValueError(f"PHK-V2.1 result {key} mismatch")
    case_payload = metadata.get("case")
    resolution_payload = metadata.get("resolution")
    if not isinstance(case_payload, dict) or not isinstance(resolution_payload, dict):
        raise ValueError("PHK-V2.1 result lacks case or resolution identity")
    try:
        case = PhkV21CaseSpec(
            **{**case_payload, "control": PhkControl(case_payload["control"])}
        )
        case.validate(physical)
        resolution = PhkResolution(**resolution_payload)
        algorithm = PhkV21PhaseAlgorithm(metadata["phase_algorithm"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid PHK-V2.1 result case or resolution identity") from exc
    if algorithm not in {
        PhkV21PhaseAlgorithm.LOGIT_NEWTON_ANALYTIC_JACOBIAN,
        PhkV21PhaseAlgorithm.PSEUDO_TRANSIENT_NEWTON,
    }:
        raise ValueError("PHK-V2.1 result phase algorithm is not admitted")

    coordinates = physical.coordinates
    grid = PhkGrid.build(
        nx=resolution.nx,
        nz=resolution.nz,
        x_min=float(coordinates["x_min"]),
        x_max=float(coordinates["x_max"]),
        z_min=float(coordinates["z_min"]),
        z_max=float(coordinates["z_max"]),
    )
    for name, value in (
        ("x", grid.cell_x),
        ("z", grid.cell_z),
        ("cell_volumes", grid.cell_volumes),
    ):
        if not np.array_equal(arrays[name], value):
            raise ValueError(f"PHK-V2.1 result mesh array mismatch: {name}")
    time = arrays["time"]
    if time.ndim != 1 or time.size < 2 or np.any(np.diff(time) <= 0.0):
        raise ValueError("PHK-V2.1 result time axis is invalid")
    if not math.isclose(float(time[0]), 0.0, abs_tol=1.0e-15) or not math.isclose(
        float(time[-1]), resolution.time_end, rel_tol=0.0, abs_tol=1.0e-12
    ):
        raise ValueError("PHK-V2.1 result time endpoints mismatch")
    field_shape = (time.size, grid.cell_count)
    for name in ("potential", "temperature", "phase"):
        if arrays[name].shape != field_shape:
            raise ValueError(f"PHK-V2.1 result field shape mismatch: {name}")
    for name in ("top_current", "bottom_current", "joule_power"):
        if arrays[name].shape != (time.size,):
            raise ValueError(f"PHK-V2.1 result trace shape mismatch: {name}")
    step_count = int(round(resolution.time_end / resolution.dt))
    for name in (
        "current_balance_history",
        "thermal_residual_history",
        "phase_residual_history",
        "coupled_change_history",
        "linear_residual_history",
    ):
        if arrays[name].shape != (step_count,):
            raise ValueError(f"PHK-V2.1 result history shape mismatch: {name}")
    if not all(np.isfinite(array).all() for array in arrays.values()):
        raise ValueError("PHK-V2.1 result contains non-finite values")
    statistics = metadata.get("solver_statistics")
    if not isinstance(statistics, dict):
        raise ValueError("PHK-V2.1 result lacks solver statistics")
    return PhkV21OracleResult(
        physical_contract_id=physical.contract_id,
        program_contract_sha256=physical.program.sha256,
        object_contract_sha256=physical.object.sha256,
        case=case,
        resolution=resolution,
        phase_algorithm=algorithm.value,
        grid=grid,
        time=time,
        potential=arrays["potential"],
        temperature=arrays["temperature"],
        phase=arrays["phase"],
        top_current=arrays["top_current"],
        bottom_current=arrays["bottom_current"],
        joule_power=arrays["joule_power"],
        current_balance_history=arrays["current_balance_history"],
        thermal_residual_history=arrays["thermal_residual_history"],
        phase_residual_history=arrays["phase_residual_history"],
        coupled_change_history=arrays["coupled_change_history"],
        linear_residual_history=arrays["linear_residual_history"],
        solver_statistics=statistics,
        evidence_identity=str(metadata.get("evidence_identity", "")),
    )


@dataclass(frozen=True)
class PhkV21EventReport:
    cycles: tuple[PhkCycleEvent, ...]
    cycle_peak_relative_drift: float
    passed: bool
    failures: tuple[str, ...]


def evaluate_phk_v21_event(
    result: PhkV21OracleResult,
    *,
    physical: PhkPhysicalContract,
) -> PhkV21EventReport:
    """Evaluate the frozen event using the complete case's own period."""

    event = _mapping(physical.payload["qualification_event"], "qualification_event")
    roi_spec = _mapping(event["roi"], "qualification_event.roi")
    roi = (
        (np.abs(result.grid.cell_x) <= float(roi_spec["abs_x_max"]))
        & (result.grid.cell_z >= float(roi_spec["z_min"]))
        & (result.grid.cell_z <= float(roi_spec["z_max"]))
    )
    if not np.any(roi) or np.all(roi):
        raise ValueError("PHK-V2.1 event ROI must be a nonempty strict subset")
    threshold = float(event["phase_threshold"])
    weights = result.grid.cell_volumes
    active = result.phase >= threshold
    roi_fraction = np.sum(active[:, roi] * weights[roi], axis=1) / np.sum(weights[roi])
    full_fraction = np.sum(active * weights, axis=1) / np.sum(weights)
    outside_fraction = np.sum(active[:, ~roi] * weights[~roi], axis=1) / np.sum(
        weights[~roi]
    )
    event_threshold = float(event["event_threshold_roi_fraction"])
    period = result.case.period
    cycles: list[PhkCycleEvent] = []
    failures: list[str] = []
    for cycle_index in range(2):
        start = cycle_index * period
        end = (cycle_index + 1) * period
        if cycle_index == 1:
            indices = np.flatnonzero((result.time >= start) & (result.time <= end))
        else:
            indices = np.flatnonzero((result.time >= start) & (result.time < end))
        if indices.size < 2:
            failures.append(f"cycle_{cycle_index + 1}_insufficient_saved_times")
            continue
        values = roi_fraction[indices]
        pre = float(values[0])
        peak_position = int(np.argmax(values))
        peak_index = int(indices[peak_position])
        peak = float(roi_fraction[peak_index])
        crossing: float | None = None
        for before, after in zip(indices[:-1], indices[1:], strict=True):
            low = float(roi_fraction[before])
            high = float(roi_fraction[after])
            if low < event_threshold <= high and high > low:
                fraction = (event_threshold - low) / (high - low)
                crossing = float(
                    result.time[before]
                    + fraction * (result.time[after] - result.time[before])
                )
                break
        excursion = peak - pre
        end_fraction = float(values[-1])
        recovery = (peak - end_fraction) / excursion if excursion > 0.0 else 0.0
        saved = int(np.count_nonzero(values >= event_threshold))
        cycle = PhkCycleEvent(
            cycle_index=cycle_index + 1,
            event_time=crossing,
            pre_roi_fraction=pre,
            peak_roi_fraction=peak,
            peak_full_domain_fraction=float(full_fraction[peak_index]),
            peak_outside_roi_fraction=float(outside_fraction[peak_index]),
            recovery_fraction=float(recovery),
            saved_steps_at_or_above_threshold=saved,
        )
        cycles.append(cycle)
        if crossing is None:
            failures.append(f"cycle_{cycle_index + 1}_event_missing")
        if peak < float(event["minimum_peak_roi_fraction"]):
            failures.append(f"cycle_{cycle_index + 1}_roi_peak_below_minimum")
        if cycle.peak_full_domain_fraction > float(
            event["maximum_peak_full_domain_fraction"]
        ):
            failures.append(f"cycle_{cycle_index + 1}_full_domain_peak_too_large")
        if cycle.peak_outside_roi_fraction > float(
            event["maximum_peak_outside_roi_fraction"]
        ):
            failures.append(f"cycle_{cycle_index + 1}_outside_roi_peak_too_large")
        if excursion < float(event["minimum_peak_minus_pre_fraction"]):
            failures.append(f"cycle_{cycle_index + 1}_excursion_too_small")
        if recovery < float(event["minimum_recovery_fraction"]):
            failures.append(f"cycle_{cycle_index + 1}_recovery_too_small")
        if saved < int(event["minimum_event_saved_steps"]):
            failures.append(f"cycle_{cycle_index + 1}_event_under_resolved")
    if len(cycles) == 2:
        drift = abs(cycles[1].peak_roi_fraction - cycles[0].peak_roi_fraction) / max(
            abs(cycles[0].peak_roi_fraction), 1.0e-14
        )
        if drift > float(event["maximum_cycle_peak_relative_drift"]):
            failures.append("cycle_peak_relative_drift_too_large")
    else:
        drift = math.inf
        failures.append("two_complete_cycles_not_available")
    return PhkV21EventReport(
        cycles=tuple(cycles),
        cycle_peak_relative_drift=float(drift),
        passed=not failures,
        failures=tuple(failures),
    )


def _same_physics(first: PhkV21CaseSpec, second: PhkV21CaseSpec) -> bool:
    if first.physics_identity() != second.physics_identity():
        return False
    controls = {first.control, second.control}
    return first.control == second.control or controls == {
        PhkControl.FULL,
        PhkControl.EXACT_REPLAY_OF_Q_NOMINAL_FINE,
    }


def compare_phk_v21_results(
    coarse: PhkV21OracleResult,
    fine: PhkV21OracleResult,
    *,
    physical: PhkPhysicalContract,
) -> PhkConvergenceReport:
    """Compute six frozen dimensionless component deltas on a common carrier."""

    if not (
        coarse.physical_contract_id
        == fine.physical_contract_id
        == physical.contract_id
    ):
        raise ValueError("PHK-V2.1 convergence comparison contract mismatch")
    if not _same_physics(coarse.case, fine.case):
        raise ValueError("PHK-V2.1 convergence comparison case mismatch")
    fine_phase = _interpolate_field_to(fine, coarse, fine.phase)
    fine_temperature = _interpolate_field_to(fine, coarse, fine.temperature)
    roi_spec = _mapping(
        _mapping(physical.payload["qualification_event"], "qualification_event")[
            "roi"
        ],
        "qualification_event.roi",
    )
    roi = (
        (np.abs(coarse.grid.cell_x) <= float(roi_spec["abs_x_max"]))
        & (coarse.grid.cell_z >= float(roi_spec["z_min"]))
        & (coarse.grid.cell_z <= float(roi_spec["z_max"]))
    )
    duration = float(coarse.time[-1] - coarse.time[0])
    if duration <= 0.0:
        raise ValueError("PHK-V2.1 comparison requires positive duration")
    roi_weights = coarse.grid.cell_volumes[roi]
    phase_mse_time = np.sum(
        (coarse.phase[:, roi] - fine_phase[:, roi]) ** 2 * roi_weights,
        axis=1,
    ) / np.sum(roi_weights)
    phase_rms = float(
        np.sqrt(np.trapezoid(phase_mse_time, coarse.time) / duration) / 0.5
    )
    temperature_mse_time = np.sum(
        (coarse.temperature[:, roi] - fine_temperature[:, roi]) ** 2
        * roi_weights,
        axis=1,
    ) / np.sum(roi_weights)
    temperature_rms = float(
        np.sqrt(np.trapezoid(temperature_mse_time, coarse.time) / duration) / 0.45
    )
    fine_current = _interpolate_trace(fine.time, fine.top_current, coarse.time)
    current_scale = max(
        float(np.sqrt(np.trapezoid(fine_current**2, coarse.time) / duration)),
        1.0e-12,
    )
    current_rms = float(
        np.sqrt(
            np.trapezoid((coarse.top_current - fine_current) ** 2, coarse.time)
            / duration
        )
        / current_scale
    )
    coarse_event = evaluate_phk_v21_event(coarse, physical=physical)
    fine_event = evaluate_phk_v21_event(fine, physical=physical)
    event_deltas: list[float] = []
    recovery_deltas: list[float] = []
    if len(coarse_event.cycles) == len(fine_event.cycles):
        for first, second in zip(
            coarse_event.cycles, fine_event.cycles, strict=True
        ):
            if first.event_time is None and second.event_time is None:
                event_deltas.append(0.0)
            elif first.event_time is None or second.event_time is None:
                event_deltas.append(math.inf)
            else:
                event_deltas.append(
                    abs(first.event_time - second.event_time) / fine.case.period
                )
            recovery_deltas.append(
                abs(first.recovery_fraction - second.recovery_fraction)
            )
    else:
        event_deltas.append(math.inf)
        recovery_deltas.append(math.inf)
    event_time = float(np.sqrt(np.mean(np.square(event_deltas))))
    recovery = float(np.sqrt(np.mean(np.square(recovery_deltas))))
    threshold = float(
        _mapping(physical.payload["qualification_event"], "qualification_event")[
            "phase_threshold"
        ]
    )
    symmetric = np.logical_xor(coarse.phase >= threshold, fine_phase >= threshold)
    symmetric_fraction = np.sum(
        symmetric * coarse.grid.cell_volumes,
        axis=1,
    ) / np.sum(coarse.grid.cell_volumes)
    region = float(np.trapezoid(symmetric_fraction, coarse.time) / duration)
    order = tuple(_mapping(physical.payload["convergence"], "convergence")["component_order"])
    deltas = np.asarray(
        (phase_rms, temperature_rms, current_rms, event_time, region, recovery),
        dtype=np.float64,
    )
    return PhkConvergenceReport(
        component_order=order,
        component_deltas=deltas,
        finite=bool(np.isfinite(deltas).all()),
    )


def run_phk_v21_manufactured_checks(
    physical: PhkPhysicalContract,
) -> dict[str, Any]:
    """Run inherited operator checks without creating a scientific field result."""

    report = run_phk_manufactured_checks(physical)
    return {
        **report,
        "schema_id": "phk-v21-manufactured-operator-report-v1",
        "evidence_identity": "MANUFACTURED_NO_SCIENTIFIC_FIELD_RESULT",
        "inherited_operator_identity": "PHK_V2_BYTE_FROZEN_FINITE_VOLUME_OPERATORS",
        "selected_phase_algorithm": (
            PhkV21PhaseAlgorithm.LOGIT_NEWTON_ANALYTIC_JACOBIAN.value
        ),
    }


__all__ = [
    "PhkV21CaseSpec",
    "PhkV21EventReport",
    "PhkV21OracleCase",
    "PhkV21OracleResult",
    "build_phk_v21_split_manifest",
    "compare_phk_v21_results",
    "evaluate_phk_v21_event",
    "load_phk_v21_physical",
    "load_phk_v21_split_manifest",
    "phk_v21_resolution",
    "read_phk_v21_result",
    "run_phk_v21_manufactured_checks",
    "write_phk_v21_split_manifest",
    "write_phk_v21_result",
]
