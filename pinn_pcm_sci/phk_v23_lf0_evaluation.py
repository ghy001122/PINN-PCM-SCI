"""Local-only evaluation and attribution adjudication for PHK-V2.3 LF0.

This module is deliberately downstream of cloud recovery and shutdown.  It
reuses the frozen V2.2R evaluator without changing it, constructs the declared
medium-grid ``LF_ONLY`` comparator on the evaluator axes, and owns the small
machine-decision surface for A/B/(optional C).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.interpolate import RegularGridInterpolator
import torch

from .phk_benchmark import PhkControl
from .phk_v21_benchmark import load_phk_v21_physical, read_phk_v21_result
from .phk_v22r_evaluator import evaluate_prediction
from .phk_v22r_pinn import PhkCollocationSampler
from .phk_v22r_prediction import (
    _evaluation_axes,
    _load_model,
    read_prediction_carrier,
)
from .phk_v22r_training import ROOT, PhkTrainingConfig, load_case_physics
from .phk_v23_lf0 import (
    ARM_A,
    ARM_B,
    ARM_C,
    PhysicsBatch,
    _physics_objective,
    potential_maximum_principle_windowed_guard,
)


DECISION_CONTRACT_PATH = (
    ROOT / "configs" / "phk_v23" / "decision_contract_lf0_attribution.json"
)
A_ROLE = "A_EXACT_TOP_SCRATCH"
B_FINAL_ROLE = "B_FINAL"
LF_DATA_ONLY_ROLE = "LF_DATA_ONLY"
LF_ONLY_ROLE = "LF_ONLY"
C_ROLE = "C_EXACT_TOP_COMPUTE_CONTROL"
PRE_C_COMPARATORS = (A_ROLE, LF_ONLY_ROLE, LF_DATA_ONLY_ROLE)
REQUIRED_TRIGGER_FIELDS = (
    "b_competent",
    "b_provisional_increment_vs_all_comparators",
    "pde_ratio_pass",
    "preservation_pass",
    "potential_validity_pass",
)


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _canonical_sha(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def _contains_nonfinite(value: Any) -> bool:
    if isinstance(value, (float, np.floating)):
        return not math.isfinite(float(value))
    if isinstance(value, Mapping):
        return any(_contains_nonfinite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_nonfinite(item) for item in value)
    return False


def _sanitize_nonfinite(value: Any) -> tuple[Any, int]:
    if isinstance(value, (float, np.floating)):
        if math.isfinite(float(value)):
            return float(value), 0
        return None, 1
    if isinstance(value, np.integer):
        return int(value), 0
    if isinstance(value, np.bool_):
        return bool(value), 0
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        count = 0
        for key, item in value.items():
            safe, local = _sanitize_nonfinite(item)
            result[str(key)] = safe
            count += local
        return result, count
    if isinstance(value, (list, tuple)):
        result_list = []
        count = 0
        for item in value:
            safe, local = _sanitize_nonfinite(item)
            result_list.append(safe)
            count += local
        return result_list, count
    return value, 0


def write_strict_json(path: Path, payload: Mapping[str, Any]) -> Path:
    """Write one new JSON object while refusing every non-finite number."""

    if _contains_nonfinite(payload):
        raise ValueError("strict LF0 JSON cannot contain NaN or infinity")
    exact = Path(path)
    exact.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    ) + "\n"
    with exact.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(encoded)
    return exact


def load_decision_contract(path: Path = DECISION_CONTRACT_PATH) -> dict[str, Any]:
    contract = json.loads(Path(path).read_text(encoding="utf-8"))
    if contract.get("schema_id") != "phk-v23-lf0-decision-contract-v1":
        raise ValueError("unsupported LF0 decision contract schema")
    if contract.get("contract_id") != "PHK_V23_LF0_ATTRIBUTION_DECISION":
        raise ValueError("unexpected LF0 decision contract identity")
    pool = contract.get("reference_blind_physics_diagnostic_pool", {})
    expected = {
        "device": "CPU",
        "dtype": "FLOAT64",
        "seed": 17031,
        "active_windows": 4,
        "interior_points": 512,
        "boundary_points_total": 128,
        "initial_points": 128,
        "objective": "NORMALIZED_PDE_PLUS_5_TIMES_BOUNDARY_PLUS_INITIAL",
        "reference_or_low_fidelity_values_read": False,
    }
    if any(pool.get(key) != value for key, value in expected.items()):
        raise ValueError("LF0 fixed reference-blind physics pool drift")
    return contract


def safe_error_ratio(numerator: float, denominator: float) -> tuple[float | None, bool]:
    """Apply the frozen zero-denominator rule without emitting infinity."""

    top = float(numerator)
    bottom = float(denominator)
    if not all(math.isfinite(value) and value >= 0.0 for value in (top, bottom)):
        raise ValueError("LF0 error ratios require finite nonnegative errors")
    if bottom == 0.0:
        return (1.0, True) if top == 0.0 else (None, False)
    return top / bottom, True


def _metrics(report: Mapping[str, Any]) -> dict[str, float]:
    raw = report.get("metrics")
    if not isinstance(raw, Mapping):
        raise ValueError("LF0 evaluation lacks frozen metrics")
    names = (
        "time_averaged_phase_region_symmetric_difference",
        "phase_roi_continuous_rms",
        "temperature_roi_nrmse_by_0_45",
        "terminal_current_trace_nrmse",
    )
    result = {name: float(raw[name]) for name in names}
    if not all(math.isfinite(value) and value >= 0.0 for value in result.values()):
        raise ValueError("LF0 decision metrics must be finite and nonnegative")
    return result


def _evaluation_valid(report: Mapping[str, Any]) -> bool:
    hard = report.get("hard_guards")
    if not isinstance(hard, Mapping):
        return False
    if hard.get("finite_values") is not True or hard.get("phase_range") is not True:
        return False
    try:
        _metrics(report)
    except (KeyError, TypeError, ValueError):
        return False
    return True


def _competent(report: Mapping[str, Any]) -> bool:
    hard = report.get("hard_guards")
    return bool(isinstance(hard, Mapping) and hard.get("passed") is True)


def competence_vector(report: Mapping[str, Any]) -> dict[str, Any]:
    """Expose the frozen two-cycle guard categories without inventing a score."""

    hard = report.get("hard_guards", {})
    topology = hard.get("event_topology", {}) if isinstance(hard, Mapping) else {}
    cycles = topology.get("cycles", []) if isinstance(topology, Mapping) else []
    result_cycles = []
    for index, cycle in enumerate(cycles[:2], start=1):
        result_cycles.append(
            {
                "cycle": index,
                "event_present": cycle.get("event_time") is not None,
                "roi_peak_passed": float(cycle.get("peak_roi_fraction", 0.0)) >= 0.02,
                "false_global_transition_absent": float(
                    cycle.get("peak_full_domain_fraction", math.inf)
                ) <= 0.45,
                "locality_passed": float(
                    cycle.get("peak_outside_roi_fraction", math.inf)
                ) <= 0.10,
                "recovery_passed": float(cycle.get("recovery_fraction", 0.0)) >= 0.70,
            }
        )
    return {
        "competent": _competent(report),
        "finite_values": bool(hard.get("finite_values") is True),
        "phase_range": bool(hard.get("phase_range") is True),
        "cycles": result_cycles,
        "partial_category_count_is_non_voting": True,
    }


def compare_b_to_comparator(
    b_report: Mapping[str, Any],
    comparator_report: Mapping[str, Any],
    *,
    component_floors: Mapping[str, float],
) -> dict[str, Any]:
    """Apply the frozen category, ratio, floor, and preservation rules."""

    b = _metrics(b_report)
    comparator = _metrics(comparator_report)
    primary_name = "time_averaged_phase_region_symmetric_difference"
    co_name = "phase_roi_continuous_rms"
    primary_ratio, primary_defined = safe_error_ratio(
        b[primary_name], comparator[primary_name]
    )
    co_ratio, co_defined = safe_error_ratio(b[co_name], comparator[co_name])
    geometric = (
        math.sqrt(float(primary_ratio) * float(co_ratio))
        if primary_defined and co_defined and primary_ratio is not None and co_ratio is not None
        else None
    )
    primary_pass = bool(primary_defined and primary_ratio is not None and primary_ratio <= 0.98)
    co_pass = bool(co_defined and co_ratio is not None and co_ratio <= 0.98)
    geometric_pass = bool(geometric is not None and geometric <= 0.95)
    continuous_pass = primary_pass and co_pass and geometric_pass
    b_competent = _competent(b_report)
    comparator_competent = _competent(comparator_report)
    category_upgrade = b_competent and not comparator_competent
    primary_reduction = comparator[primary_name] - b[primary_name]
    co_reduction = comparator[co_name] - b[co_name]
    primary_floor = float(component_floors[primary_name])
    co_floor = float(component_floors[co_name])
    if not all(
        math.isfinite(value) and value > 0.0 for value in (primary_floor, co_floor)
    ):
        raise ValueError("LF0 component floors must be positive and finite")
    floor_pass = primary_reduction > primary_floor or co_reduction > co_floor
    category_or_ratio = category_upgrade or (
        b_competent and comparator_competent and continuous_pass
    )
    temperature_pass = b["temperature_roi_nrmse_by_0_45"] <= max(
        1.10 * comparator["temperature_roi_nrmse_by_0_45"], 0.05
    )
    current_pass = b["terminal_current_trace_nrmse"] <= max(
        1.10 * comparator["terminal_current_trace_nrmse"], 0.15
    )
    return {
        "b_competent": b_competent,
        "comparator_competent": comparator_competent,
        "category_upgrade": category_upgrade,
        "primary_ratio": primary_ratio,
        "co_primary_ratio": co_ratio,
        "geometric_mean_ratio": geometric,
        "primary_ratio_passed": primary_pass,
        "co_primary_ratio_passed": co_pass,
        "geometric_mean_ratio_passed": geometric_pass,
        "continuous_ratio_gate_passed": continuous_pass,
        "primary_error_reduction": primary_reduction,
        "co_primary_error_reduction": co_reduction,
        "primary_component_floor": primary_floor,
        "co_primary_component_floor": co_floor,
        "component_floor_improvement_passed": floor_pass,
        "increment_passed": category_or_ratio and floor_pass,
        "temperature_preservation_passed": temperature_pass,
        "current_preservation_passed": current_pass,
        "preservation_passed": temperature_pass and current_pass,
    }


def _terminal(outcome: str, *, details: Mapping[str, Any] | None = None) -> dict[str, Any]:
    next_by_outcome = {
        "LF0_CPU_QUALIFICATION_BLOCKED": "LF0_CPU_BLOCKED_REQUIRES_NEW_USER_DECISION",
        "LF0_EXACT_TOP_SCRATCH_COMPETENCE_ONLY": "EXACT_TOP_COMPETENT_BACKBONE_CORE_GATE_REVIEW_NOT_AUTHORIZED",
        "LF0_WARMSTART_PINN_PROVISIONAL_METHOD_SIGNAL": "LF0_MULTI_SEED_AND_CORE_ATTRIBUTION_REQUIRES_NEW_EXECUTE",
        "LF0_GUIDED_SOLVER_RESCUE_NO_METHOD_GAIN": "RETAIN_GUIDED_SOLVER_AS_NON_HEADLINE_AND_STOP_METHOD_CLAIM",
        "LF0_LOW_FIDELITY_ROUTE_NO_COMPETENCE": "RETAIN_BOUNDED_NEGATIVE_PACKAGE",
        "LF0_NUMERICAL_OR_IDENTITY_INVALID": "INVALID_RUN_REQUIRES_USER_REVIEW_NO_AUTOMATIC_SCIENTIFIC_RETRY",
        "LF0_ENGINEERING_BLOCKED": "IDENTICAL_ENGINEERING_RETRY_WITHIN_CAMPAIGN",
    }
    return {
        "status": "TERMINAL",
        "outcome": outcome,
        "unique_next": next_by_outcome[outcome],
        **dict(details or {}),
    }


def adjudicate_campaign(
    *,
    cpu_qualification_passed: bool,
    evaluations: Mapping[str, Mapping[str, Any]],
    potential_guards: Mapping[str, Mapping[str, Any]],
    component_floors: Mapping[str, float],
    physics_batch_identity: Mapping[str, Any] | None = None,
    physics_objective_ratio: Mapping[str, Any] | None = None,
    engineering_blocked_reason: str | None = None,
) -> dict[str, Any]:
    """Return one exhaustive terminal outcome or one frozen interim action."""

    if engineering_blocked_reason:
        return _terminal(
            "LF0_ENGINEERING_BLOCKED",
            details={"engineering_blocked_reason": str(engineering_blocked_reason)},
        )
    if not cpu_qualification_passed:
        return _terminal("LF0_CPU_QUALIFICATION_BLOCKED")
    initial_required = (A_ROLE, LF_ONLY_ROLE)
    if any(role not in evaluations or role not in potential_guards for role in initial_required):
        return _terminal(
            "LF0_ENGINEERING_BLOCKED",
            details={"engineering_blocked_reason": "required A/LF_ONLY evidence missing"},
        )
    available = tuple(evaluations)
    if any(
        not _evaluation_valid(evaluations[role])
        or potential_guards.get(role, {}).get("passed") is not True
        for role in available
    ):
        return _terminal("LF0_NUMERICAL_OR_IDENTITY_INVALID")
    if B_FINAL_ROLE not in evaluations:
        if LF_DATA_ONLY_ROLE in evaluations or C_ROLE in evaluations:
            return _terminal("LF0_NUMERICAL_OR_IDENTITY_INVALID")
        return {
            "status": "INTERIM",
            "interim_status": "LF0_A_VALID_RUN_B_REQUIRED",
            "unique_next": "RUN_B_MEDIUM_WARMSTART_AFTER_AUTODL_RESTART",
            "competence": {
                role: competence_vector(report) for role, report in evaluations.items()
            },
        }
    if LF_DATA_ONLY_ROLE not in evaluations or LF_DATA_ONLY_ROLE not in potential_guards:
        return _terminal(
            "LF0_ENGINEERING_BLOCKED",
            details={"engineering_blocked_reason": "B LF_DATA_ONLY evidence missing"},
        )
    if physics_batch_identity is None or physics_objective_ratio is None:
        return _terminal(
            "LF0_ENGINEERING_BLOCKED",
            details={"engineering_blocked_reason": "post-B physics attribution evidence missing"},
        )
    if physics_batch_identity.get("passed") is not True:
        return _terminal("LF0_NUMERICAL_OR_IDENTITY_INVALID")

    comparisons = {
        role: compare_b_to_comparator(
            evaluations[B_FINAL_ROLE], evaluations[role], component_floors=component_floors
        )
        for role in PRE_C_COMPARATORS
    }
    b_competent = _competent(evaluations[B_FINAL_ROLE])
    increments_pass = all(item["increment_passed"] for item in comparisons.values())
    preservation_pass = all(item["preservation_passed"] for item in comparisons.values())
    potential_pass = all(
        potential_guards[role].get("passed") is True
        for role in (A_ROLE, B_FINAL_ROLE, LF_ONLY_ROLE, LF_DATA_ONLY_ROLE)
    )
    objective_pass = physics_objective_ratio.get("passed") is True
    trigger_conditions = {
        "b_competent": b_competent,
        "b_provisional_increment_vs_all_comparators": increments_pass,
        "pde_ratio_pass": objective_pass,
        "preservation_pass": preservation_pass,
        "potential_validity_pass": potential_pass,
    }
    trigger_pass = all(trigger_conditions.values())
    common = {
        "competence": {
            role: competence_vector(report) for role, report in evaluations.items()
        },
        "comparisons": comparisons,
        "physics_batch_identity": dict(physics_batch_identity),
        "full_summed_physics_objective_ratio": dict(physics_objective_ratio),
        "c_trigger": trigger_conditions,
    }
    if C_ROLE not in evaluations:
        if trigger_pass:
            return {
                "status": "INTERIM",
                "interim_status": "LF0_C_TRIGGERED",
                "unique_next": "RUN_C_EXACT_TOP_COMPUTE_CONTROL_AFTER_AUTODL_RESTART",
                **common,
            }
        if _competent(evaluations[A_ROLE]):
            return _terminal("LF0_EXACT_TOP_SCRATCH_COMPETENCE_ONLY", details=common)
        if b_competent:
            return _terminal("LF0_GUIDED_SOLVER_RESCUE_NO_METHOD_GAIN", details=common)
        return _terminal("LF0_LOW_FIDELITY_ROUTE_NO_COMPETENCE", details=common)

    if not trigger_pass:
        return _terminal("LF0_NUMERICAL_OR_IDENTITY_INVALID", details=common)
    comparison_c = compare_b_to_comparator(
        evaluations[B_FINAL_ROLE], evaluations[C_ROLE], component_floors=component_floors
    )
    common["comparisons"] = {**comparisons, C_ROLE: comparison_c}
    b_beats_c = (not _competent(evaluations[C_ROLE])) or (
        comparison_c["increment_passed"] and comparison_c["preservation_passed"]
    )
    if b_beats_c:
        return _terminal("LF0_WARMSTART_PINN_PROVISIONAL_METHOD_SIGNAL", details=common)
    if _competent(evaluations[A_ROLE]) or _competent(evaluations[C_ROLE]):
        return _terminal("LF0_EXACT_TOP_SCRATCH_COMPETENCE_ONLY", details=common)
    if b_competent:
        return _terminal("LF0_GUIDED_SOLVER_RESCUE_NO_METHOD_GAIN", details=common)
    return _terminal("LF0_LOW_FIDELITY_ROUTE_NO_COMPETENCE", details=common)



def _read_hash_log(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            local_step = int(row["physics_local_step"])
            active_windows = int(row["active_windows"])
            digest = str(row["batch_sha256"]).upper()
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid LF0 physics hash log at line {line_number}") from exc
        if local_step != len(rows) + 1 or not 1 <= active_windows <= 4:
            raise ValueError("LF0 physics hash log is not contiguous or has invalid windows")
        if len(digest) != 64 or any(character not in "0123456789ABCDEF" for character in digest):
            raise ValueError("LF0 physics batch hash is malformed")
        rows.append(
            {
                "physics_local_step": local_step,
                "active_windows": active_windows,
                "batch_sha256": digest,
            }
        )
    if not rows:
        raise ValueError("LF0 physics hash log is empty")
    return rows


def compare_physics_batch_logs(
    a_path: Path, b_path: Path, c_path: Path | None = None
) -> dict[str, Any]:
    """Compare A=B stepwise and, when present, C's matching prefix."""

    a = _read_hash_log(a_path)
    b = _read_hash_log(b_path)
    c = _read_hash_log(c_path) if c_path is not None else None
    expected_windows = lambda step: 1 if step <= 150 else (2 if step <= 350 else (3 if step <= 550 else 4))
    schedule_passed = all(
        row["active_windows"] == expected_windows(row["physics_local_step"])
        for rows in (a, b, c or [])
        for row in rows
    )
    count_passed = len(a) == 1200 and len(b) == 1200 and (c is None or len(c) == 2000)
    first_mismatch: int | None = None
    if len(a) != len(b):
        first_mismatch = min(len(a), len(b)) + 1
    else:
        for left, right in zip(a, b, strict=True):
            if left != right:
                first_mismatch = int(left["physics_local_step"])
                break
    c_prefix_passed = True
    c_mismatch: int | None = None
    if c is not None:
        if len(c) < len(a):
            c_prefix_passed = False
            c_mismatch = len(c) + 1
        else:
            for left, right in zip(a, c[: len(a)], strict=True):
                if left != right:
                    c_prefix_passed = False
                    c_mismatch = int(left["physics_local_step"])
                    break
    return {
        "passed": count_passed and schedule_passed and first_mismatch is None and c_prefix_passed,
        "frozen_record_counts_passed": count_passed,
        "causal_window_schedule_passed": schedule_passed,
        "a_record_count": len(a),
        "b_record_count": len(b),
        "c_record_count": len(c) if c is not None else None,
        "a_equals_b_stepwise": first_mismatch is None,
        "first_mismatch_physics_local_step": first_mismatch,
        "c_first_a_count_equals_a": c_prefix_passed if c is not None else None,
        "c_first_mismatch_physics_local_step": c_mismatch,
        "a_log_sha256": _sha256_path(a_path),
        "b_log_sha256": _sha256_path(b_path),
        "c_log_sha256": _sha256_path(c_path) if c_path is not None else None,
    }


def interpolate_low_fidelity_arrays(
    *,
    source_axes: tuple[np.ndarray, np.ndarray, np.ndarray],
    target_axes: tuple[np.ndarray, np.ndarray, np.ndarray],
    fields: Mapping[str, np.ndarray],
    scalar_traces: Mapping[str, np.ndarray],
) -> dict[str, np.ndarray]:
    """Trilinearly map medium fields and linearly map scalar traces."""

    source_time, source_z, source_x = (
        np.asarray(axis, dtype=np.float64) for axis in source_axes
    )
    target_time, target_z, target_x = (
        np.asarray(axis, dtype=np.float64) for axis in target_axes
    )
    z_mesh, x_mesh = np.meshgrid(target_z, target_x, indexing="ij")
    spatial = np.column_stack((z_mesh.reshape(-1), x_mesh.reshape(-1)))
    result: dict[str, np.ndarray] = {}
    source_shape = (source_time.size, source_z.size, source_x.size)
    for name in ("potential", "temperature", "phase"):
        values = np.asarray(fields[name], dtype=np.float64)
        if values.shape != source_shape:
            raise ValueError(f"LF_ONLY source {name} shape does not match source axes")
        interpolator = RegularGridInterpolator(
            (source_time, source_z, source_x),
            values,
            method="linear",
            bounds_error=False,
            fill_value=None,
        )
        mapped = np.empty((target_time.size, spatial.shape[0]), dtype=np.float64)
        for index, time_value in enumerate(target_time):
            query = np.column_stack(
                (np.full(spatial.shape[0], time_value), spatial)
            )
            mapped[index] = interpolator(query)
        result[name] = mapped
    for name in ("top_current", "joule_power"):
        values = np.asarray(scalar_traces[name], dtype=np.float64)
        if values.shape != source_time.shape:
            raise ValueError(f"LF_ONLY source {name} shape does not match source time")
        result[name] = np.interp(target_time, source_time, values)
    if not all(np.isfinite(value).all() for value in result.values()):
        raise ValueError("LF_ONLY interpolation produced non-finite values")
    return result


def _physical_contract():
    return load_phk_v21_physical(
        program_path=ROOT / "configs" / "phk_v21" / "program_contract.json",
        object_path=ROOT / "configs" / "phk_v21" / "object_numerical_contract.json",
        legacy_program_path=ROOT / "configs" / "phk_v2" / "program_contract.json",
        legacy_object_path=ROOT / "configs" / "phk_v2" / "object_numerical_contract.json",
    )


def write_lf_only_prediction_carrier(
    *,
    medium_carrier_path: Path,
    output_path: Path,
    expected_medium_sha256: str,
    case_control: str = "FULL",
) -> Path:
    """Write the declared medium direct comparator on extra-fine axes."""

    if case_control != PhkControl.FULL.value:
        raise PermissionError("LF0 local evaluation is nominal-only; stress stays sealed")
    medium_path = Path(medium_carrier_path)
    if _sha256_path(medium_path) != str(expected_medium_sha256).upper():
        raise ValueError("LF_ONLY medium source byte identity drift")
    physical = _physical_contract()
    source = read_phk_v21_result(medium_path, physical=physical)
    config = PhkTrainingConfig(arm="STRONG_RAW", case_control="FULL")
    target_x, target_z, target_time = _evaluation_axes(config)
    fields = {
        name: np.asarray(getattr(source, name), dtype=np.float64).reshape(
            source.time.size, source.grid.z_centers.size, source.grid.x_centers.size
        )
        for name in ("potential", "temperature", "phase")
    }
    mapped = interpolate_low_fidelity_arrays(
        source_axes=(source.time, source.grid.z_centers, source.grid.x_centers),
        target_axes=(target_time, target_z, target_x),
        fields=fields,
        scalar_traces={
            "top_current": source.top_current,
            "joule_power": source.joule_power,
        },
    )
    training_config = {
        "arm": "LF_ONLY_MEDIUM_DIRECT_NOT_PINN",
        "case_control": "FULL",
        "updates": 0,
        "seed": 17,
        "dtype": "float64",
        "device": "cpu",
    }
    metadata = {
        "schema_id": "phk-v22r-prediction-carrier-v1-1",
        "checkpoint_sha256": None,
        "checkpoint_update": 0,
        "training_config": training_config,
        "training_config_sha256": _canonical_sha(training_config),
        "architecture": {
            "role": "LF_ONLY_MEDIUM_LINEAR_INTERPOLATION_NOT_A_PINN",
            "neural_model": False,
            "pde_residual_claim": False,
        },
        "program_contract_sha256": _sha256_path(
            ROOT / "configs" / "phk_v22r" / "program_contract.json"
        ),
        "method_contract_sha256": _sha256_path(
            ROOT / "configs" / "phk_v22r" / "method_contract.json"
        ),
        "physical_program_sha256": _sha256_path(
            ROOT / "configs" / "phk_v21" / "program_contract.json"
        ),
        "physical_object_sha256": _sha256_path(
            ROOT / "configs" / "phk_v21" / "object_numerical_contract.json"
        ),
        "reference_fields_read": False,
        "medium_low_fidelity_source_read": True,
        "extra_fine_reference_values_read": False,
        "evaluation_grid_identity": "CONTRACT_DERIVED_EXTRA_FINE_AXES_WITHOUT_REFERENCE_VALUES",
        "mapping": "LINEAR_TIME_Z_X_FIELDS_AND_LINEAR_TIME_SCALAR_TRACES",
        "source_sha256": str(expected_medium_sha256).upper(),
        "top_current_definition": "INTERPOLATED_NATIVE_MEDIUM_TOP_CURRENT",
        "joule_power_definition": "INTERPOLATED_NATIVE_MEDIUM_JOULE_POWER",
    }
    exact = Path(output_path)
    exact.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    descriptor = os.open(exact, flags, 0o644)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            np.savez_compressed(
                handle,
                metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
                x=target_x,
                z=target_z,
                time=target_time,
                potential=mapped["potential"],
                temperature=mapped["temperature"],
                phase=mapped["phase"],
                top_current=mapped["top_current"],
                joule_power=mapped["joule_power"],
            )
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        exact.unlink(missing_ok=True)
        raise
    return exact


def _prediction_potential_guard(
    prediction_path: Path, *, absolute_tolerance: float
) -> dict[str, Any]:
    metadata, arrays = read_prediction_carrier(prediction_path)
    if metadata["training_config"]["case_control"] != "FULL":
        raise PermissionError("LF0 local evaluation is nominal-only")
    physics, _, _ = load_case_physics("FULL")
    times = torch.as_tensor(arrays["time"], dtype=torch.float64).reshape(-1, 1)
    waveform = physics.waveform(times).detach().cpu().numpy().reshape(-1)
    return potential_maximum_principle_windowed_guard(
        arrays["potential"],
        arrays["time"],
        waveform,
        absolute_tolerance=absolute_tolerance,
    )


def _tensor_digest(*values: torch.Tensor, metadata: str) -> str:
    digest = hashlib.sha256(metadata.encode("utf-8"))
    for value in values:
        array = value.detach().cpu().to(torch.float64).contiguous().numpy()
        digest.update(str(tuple(array.shape)).encode("ascii"))
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest().upper()


def _clone_batch(batch: PhysicsBatch) -> PhysicsBatch:
    return PhysicsBatch(
        interior=batch.interior.detach().clone(),
        boundary={name: value.detach().clone() for name, value in batch.boundary.items()},
        initial=batch.initial.detach().clone(),
        active_windows=batch.active_windows,
        refreshed=True,
        interior_sha256=batch.interior_sha256,
        boundary_sha256=batch.boundary_sha256,
        initial_sha256=batch.initial_sha256,
        batch_sha256=batch.batch_sha256,
    )


def compute_fixed_physics_objective_ratio(
    *,
    b_final_checkpoint: Path,
    lf_data_only_checkpoint: Path,
    decision_contract_path: Path = DECISION_CONTRACT_PATH,
) -> dict[str, Any]:
    """Compare B final and step-800 on one reference-blind CPU physics batch."""

    contract = load_decision_contract(decision_contract_path)
    pool = contract["reference_blind_physics_diagnostic_pool"]
    device = torch.device("cpu")
    b_model, b_config, b_payload = _load_model(b_final_checkpoint, device=device)
    lf_model, lf_config, lf_payload = _load_model(lf_data_only_checkpoint, device=device)
    for payload, expected_stage in (
        (b_payload, "B2_PURE_PHYSICS"),
        (lf_payload, "B0_LF_ONLY"),
    ):
        lf0 = payload.get("lf0", {})
        if lf0.get("run_arm") != ARM_B or lf0.get("stage") != expected_stage:
            raise ValueError("LF0 B checkpoint role/stage identity drift")
    if b_config != lf_config or b_config.case_control != "FULL":
        raise ValueError("LF0 B checkpoint configurations differ")
    physics, _, _ = load_case_physics("FULL")
    sampler = PhkCollocationSampler(physics=physics, seed=int(pool["seed"]))
    dtype = torch.float64
    interior = sampler.select_interior(
        b_model,
        count=int(pool["interior_points"]),
        active_windows=4,
        physics_aware=False,
        dtype=dtype,
        device=device,
    ).detach()
    boundary = sampler.boundary(
        int(pool["boundary_points_per_side"]),
        active_windows=4,
        dtype=dtype,
        device=device,
    )
    initial = sampler.initial(int(pool["initial_points"]), dtype=dtype, device=device)
    ordered = tuple(boundary[name] for name in ("left", "right", "bottom", "top"))
    digest = _tensor_digest(
        interior,
        *ordered,
        initial,
        metadata="PHK_V23_LF0_FIXED_REFERENCE_BLIND_FULL_W1_W4",
    )
    interior_sha = _tensor_digest(interior, metadata="LF0_FIXED_INTERIOR")
    boundary_sha = _tensor_digest(*ordered, metadata="LF0_FIXED_BOUNDARY")
    initial_sha = _tensor_digest(initial, metadata="LF0_FIXED_INITIAL")
    batch = PhysicsBatch(
        interior=interior,
        boundary=boundary,
        initial=initial,
        active_windows=4,
        refreshed=True,
        interior_sha256=interior_sha,
        boundary_sha256=boundary_sha,
        initial_sha256=initial_sha,
        batch_sha256=digest,
    )
    with torch.enable_grad():
        _, b_scalars = _physics_objective(b_model, _clone_batch(batch), b_config)
        _, lf_scalars = _physics_objective(lf_model, _clone_batch(batch), lf_config)
    b_value = float(b_scalars["physics_total"])
    lf_value = float(lf_scalars["physics_total"])
    ratio, defined = safe_error_ratio(b_value, lf_value)
    threshold = float(
        contract["increment_gate"][
            "full_summed_physics_objective_ratio_B_final_to_LF_DATA_ONLY_maximum"
        ]
    )
    return {
        "passed": bool(defined and ratio is not None and ratio <= threshold),
        "ratio": ratio,
        "maximum_allowed_ratio": threshold,
        "objective": "NORMALIZED_PDE_PLUS_5_TIMES_BOUNDARY_PLUS_INITIAL",
        "b_final_full_summed_physics_objective": b_value,
        "lf_data_only_full_summed_physics_objective": lf_value,
        "b_final_components": b_scalars,
        "lf_data_only_components": lf_scalars,
        "fixed_pool_sha256": digest,
        "interior_sha256": interior_sha,
        "boundary_sha256": boundary_sha,
        "initial_sha256": initial_sha,
        "fixed_pool_seed": int(pool["seed"]),
        "active_windows": 4,
        "counts": {"interior": 512, "boundary_total": 128, "initial": 128},
        "reference_or_low_fidelity_values_read": False,
        "device": "CPU",
        "dtype": "FLOAT64",
    }


def _load_component_floors(contract: Mapping[str, Any]) -> dict[str, float]:
    record = contract["qualification_inputs"]["oracle_floor_seal"]
    path = ROOT / record["path"]
    if _sha256_path(path) != str(record["sha256"]).upper():
        raise ValueError("LF0 oracle floor seal byte identity drift")
    payload = json.loads(path.read_text(encoding="utf-8"))
    order = payload.get("component_order")
    floors = payload.get("component_floors_U")
    if not isinstance(order, list) or not isinstance(floors, list) or len(order) != len(floors):
        raise ValueError("LF0 oracle floor seal is malformed")
    by_name = {name: float(value) for name, value in zip(order, floors, strict=True)}
    return {
        "phase_roi_continuous_rms": by_name["PHASE_FIELD_ROI_RMS"],
        "time_averaged_phase_region_symmetric_difference": by_name[
            "TIME_AVERAGED_PHASE_REGION_SYMMETRIC_DIFFERENCE"
        ],
    }


def _read_cpu_qualification(
    path: Path,
    *,
    decision_contract_path: Path,
    expected_medium_sha256: str,
) -> bool:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if (
        payload.get("schema_id") != "phk-v23-lf0-cpu-qualification-v1"
        or payload.get("task_id")
        != "PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE"
        or Path(str(payload.get("contract_path", ""))).resolve()
        != Path(decision_contract_path).resolve()
        or str(payload.get("medium_source_sha256", "")).upper()
        != str(expected_medium_sha256).upper()
        or payload.get("execution_boundary", {}).get("stress_read") is not False
    ):
        raise ValueError("unsupported LF0 CPU qualification record")
    return payload.get("passed") is True and payload.get("status") == "LF0_CPU_QUALIFIED"


def _run_files(path: Path, *, arm: str) -> dict[str, Any]:
    root = Path(path)
    summary_path = root / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    expected = {ARM_A: ARM_A, ARM_B: ARM_B, ARM_C: ARM_C}[arm]
    if (
        summary.get("status") != "LF0_REFERENCE_BLIND_GPU_RUN_COMPLETE"
        or summary.get("run_arm") != expected
        or summary.get("prediction_reference_free") is not True
        or summary.get("stress_fields_or_metrics_read") is not False
    ):
        raise ValueError(f"LF0 recovered {arm} summary identity or validity drift")
    result = {
        "root": root,
        "summary": summary_path,
        "summary_payload": summary,
        "prediction_final": root / "prediction-final.npz",
        "checkpoint_final": root / "checkpoint-final.pt",
        "physics_hashes": root / "physics-batch-hashes.jsonl",
    }
    if arm == ARM_B:
        result.update(
            {
                "prediction_lf_data_only": root / "prediction-lf-data-only-step-800.npz",
                "checkpoint_lf_data_only": root / "checkpoint-lf-data-only-step-800.pt",
            }
        )
    path_items = {
        name: candidate
        for name, candidate in result.items()
        if name not in {"root", "summary_payload"}
    }
    missing = [name for name, candidate in path_items.items() if not candidate.is_file()]
    if missing:
        raise FileNotFoundError(f"LF0 recovered {arm} files missing: {missing}")
    artifact_keys = {
        "prediction_final": "prediction_final",
        "checkpoint_final": "checkpoint_final",
        "physics_hashes": "physics_batch_hashes",
    }
    if arm == ARM_B:
        artifact_keys.update(
            {
                "prediction_lf_data_only": "prediction_lf_data_only",
                "checkpoint_lf_data_only": "checkpoint_lf_data_only",
            }
        )
    artifacts = summary.get("artifacts")
    if not isinstance(artifacts, Mapping):
        raise ValueError(f"LF0 recovered {arm} summary lacks artifact bindings")
    for local_name, artifact_name in artifact_keys.items():
        candidate = result[local_name]
        record = artifacts.get(artifact_name)
        if not isinstance(record, Mapping):
            raise ValueError(f"LF0 recovered {arm} lacks {artifact_name} binding")
        bound_path = (root / str(record.get("path", ""))).resolve()
        if (
            bound_path != candidate.resolve()
            or int(record.get("size_bytes", -1)) != candidate.stat().st_size
            or str(record.get("sha256", "")).upper() != _sha256_path(candidate)
        ):
            raise ValueError(f"LF0 recovered {arm} {artifact_name} binding drift")
    return result


def write_c_trigger(
    path: Path,
    *,
    conditions: Mapping[str, bool],
    bound_inputs: Mapping[str, Path],
) -> dict[str, Any]:
    if set(conditions) != set(REQUIRED_TRIGGER_FIELDS) or not all(
        conditions[name] is True for name in REQUIRED_TRIGGER_FIELDS
    ):
        raise ValueError("LF0 C trigger requires all five frozen conditions")
    bindings = {
        name: {
            "path": str(Path(input_path).resolve()),
            "sha256": _sha256_path(input_path),
            "size_bytes": Path(input_path).stat().st_size,
        }
        for name, input_path in sorted(bound_inputs.items())
    }
    trigger = {
        "schema_id": "phk-v23-lf0-c-trigger-v1",
        "task_id": "PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE",
        "action": "RUN_C_EXACT_TOP_COMPUTE_CONTROL_IF_TRIGGERED",
        **{name: bool(conditions[name]) for name in REQUIRED_TRIGGER_FIELDS},
        "input_bindings": bindings,
        "stress_fields_or_metrics_read": False,
    }
    write_strict_json(path, trigger)
    return trigger


def evaluate_lf0_campaign(
    *,
    output_directory: Path,
    a_run_directory: Path,
    cpu_qualification_path: Path | None = None,
    b_run_directory: Path | None = None,
    c_run_directory: Path | None = None,
    case_control: str = "FULL",
    decision_contract_path: Path = DECISION_CONTRACT_PATH,
) -> dict[str, Any]:
    """Evaluate recovered LF0 arms locally and emit a strict machine record."""

    # This check must precede every contract, directory, checkpoint, or carrier I/O.
    if case_control != PhkControl.FULL.value:
        raise PermissionError("LF0 local evaluation is nominal-only; stress stays sealed")
    contract = load_decision_contract(decision_contract_path)
    if cpu_qualification_path is None:
        raise ValueError("LF0 local adjudication requires the CPU qualification record")
    data_contract = json.loads(
        (ROOT / contract["data_contract"]).read_text(encoding="utf-8")
    )
    source = data_contract["training_source"]
    cpu_passed = _read_cpu_qualification(
        cpu_qualification_path,
        decision_contract_path=decision_contract_path,
        expected_medium_sha256=source["sha256"],
    )
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=False)
    if not cpu_passed:
        decision = adjudicate_campaign(
            cpu_qualification_passed=False,
            evaluations={},
            potential_guards={},
            component_floors=_load_component_floors(contract),
        )
        report = {
            "schema_id": "phk-v23-lf0-local-adjudication-v1",
            "status": "COMPLETE",
            "decision": decision,
            "stress_status": "TWO_STRESS_REFERENCES_SEALED_UNREAD",
        }
        write_strict_json(output / "adjudication.json", report)
        return report

    lf_only_path = write_lf_only_prediction_carrier(
        medium_carrier_path=ROOT / source["path"],
        output_path=output / "prediction-lf-only-medium-direct.npz",
        expected_medium_sha256=source["sha256"],
    )
    a_files = _run_files(a_run_directory, arm=ARM_A)
    b_files = _run_files(b_run_directory, arm=ARM_B) if b_run_directory else None
    c_files = _run_files(c_run_directory, arm=ARM_C) if c_run_directory else None
    recovered = [item for item in (a_files, b_files, c_files) if item is not None]
    contract_identities = {
        json.dumps(item["summary_payload"].get("contracts"), sort_keys=True)
        for item in recovered
    }
    if (
        any(not item["summary_payload"].get("source_identity") for item in recovered)
        or len(contract_identities) != 1
    ):
        raise ValueError("LF0 recovered runs lack source identity or share no contract identity")
    prediction_paths: dict[str, Path] = {
        A_ROLE: a_files["prediction_final"],
        LF_ONLY_ROLE: lf_only_path,
    }
    if b_files:
        prediction_paths.update(
            {
                B_FINAL_ROLE: b_files["prediction_final"],
                LF_DATA_ONLY_ROLE: b_files["prediction_lf_data_only"],
            }
        )
    if c_files:
        prediction_paths[C_ROLE] = c_files["prediction_final"]
    evaluations = {
        role: evaluate_prediction(prediction_path=path, control=PhkControl.FULL)
        for role, path in prediction_paths.items()
    }
    tolerance = float(contract["potential_maximum_principle"]["absolute_tolerance"])
    potential_guards = {
        role: _prediction_potential_guard(path, absolute_tolerance=tolerance)
        for role, path in prediction_paths.items()
    }
    batch_identity = None
    objective_ratio = None
    if b_files:
        batch_identity = compare_physics_batch_logs(
            a_files["physics_hashes"],
            b_files["physics_hashes"],
            c_files["physics_hashes"] if c_files else None,
        )
        objective_ratio = compute_fixed_physics_objective_ratio(
            b_final_checkpoint=b_files["checkpoint_final"],
            lf_data_only_checkpoint=b_files["checkpoint_lf_data_only"],
            decision_contract_path=decision_contract_path,
        )
    floors = _load_component_floors(contract)
    decision = adjudicate_campaign(
        cpu_qualification_passed=True,
        evaluations=evaluations,
        potential_guards=potential_guards,
        component_floors=floors,
        physics_batch_identity=batch_identity,
        physics_objective_ratio=objective_ratio,
    )
    sanitized_evaluations, replaced = _sanitize_nonfinite(evaluations)
    report: dict[str, Any] = {
        "schema_id": "phk-v23-lf0-local-adjudication-v1",
        "task_id": "PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE",
        "status": "COMPLETE",
        "case_control": "FULL",
        "reference_role": "NOMINAL_LOCAL_DEVELOPMENT_ONLY_AFTER_GPU_SHUTDOWN",
        "roles_evaluated": list(prediction_paths),
        "prediction_bindings": {
            role: {
                "path": str(path.resolve()),
                "sha256": _sha256_path(path),
                "size_bytes": path.stat().st_size,
            }
            for role, path in prediction_paths.items()
        },
        "evaluations": sanitized_evaluations,
        "evaluator_nonfinite_diagnostics_represented_as_json_null": replaced,
        "potential_maximum_principle": potential_guards,
        "physics_batch_identity": batch_identity,
        "full_summed_physics_objective_ratio": objective_ratio,
        "component_floors": floors,
        "decision": decision,
        "lf_only_role": "LINEARLY_MAPPED_MEDIUM_DIRECT_COMPARATOR_NOT_A_PINN_RESIDUAL",
        "stress_status": "TWO_STRESS_REFERENCES_SEALED_UNREAD",
    }
    if decision.get("interim_status") == "LF0_C_TRIGGERED":
        assert b_files is not None
        bound = {
            "decision_contract": decision_contract_path,
            "a_prediction": a_files["prediction_final"],
            "a_final_checkpoint": a_files["checkpoint_final"],
            "a_physics_hash_log": a_files["physics_hashes"],
            "b_prediction": b_files["prediction_final"],
            "b_lf_data_only_prediction": b_files["prediction_lf_data_only"],
            "b_final_checkpoint": b_files["checkpoint_final"],
            "b_lf_data_only_checkpoint": b_files["checkpoint_lf_data_only"],
            "b_physics_hash_log": b_files["physics_hashes"],
            "lf_only_prediction": lf_only_path,
        }
        trigger = write_c_trigger(
            output / "c-trigger.json",
            conditions=decision["c_trigger"],
            bound_inputs=bound,
        )
        report["c_trigger_record"] = {
            "path": str((output / "c-trigger.json").resolve()),
            "sha256": _sha256_path(output / "c-trigger.json"),
            "conditions": {name: trigger[name] for name in REQUIRED_TRIGGER_FIELDS},
        }
    write_strict_json(output / "adjudication.json", report)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--a-run-directory", type=Path, required=True)
    parser.add_argument("--b-run-directory", type=Path)
    parser.add_argument("--c-run-directory", type=Path)
    parser.add_argument("--cpu-qualification", type=Path, required=True)
    parser.add_argument("--case-control", default="FULL")
    parser.add_argument("--decision-contract", type=Path, default=DECISION_CONTRACT_PATH)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = evaluate_lf0_campaign(
        output_directory=args.output_directory,
        a_run_directory=args.a_run_directory,
        cpu_qualification_path=args.cpu_qualification,
        b_run_directory=args.b_run_directory,
        c_run_directory=args.c_run_directory,
        case_control=args.case_control,
        decision_contract_path=args.decision_contract,
    )
    print(json.dumps(report["decision"], sort_keys=True, allow_nan=False))
    return 0 if report["decision"].get("outcome") not in {
        "LF0_CPU_QUALIFICATION_BLOCKED",
        "LF0_NUMERICAL_OR_IDENTITY_INVALID",
        "LF0_ENGINEERING_BLOCKED",
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "A_ROLE",
    "B_FINAL_ROLE",
    "C_ROLE",
    "LF_DATA_ONLY_ROLE",
    "LF_ONLY_ROLE",
    "adjudicate_campaign",
    "compare_b_to_comparator",
    "compare_physics_batch_logs",
    "competence_vector",
    "compute_fixed_physics_objective_ratio",
    "evaluate_lf0_campaign",
    "interpolate_low_fidelity_arrays",
    "load_decision_contract",
    "main",
    "safe_error_ratio",
    "write_c_trigger",
    "write_lf_only_prediction_carrier",
    "write_strict_json",
]
