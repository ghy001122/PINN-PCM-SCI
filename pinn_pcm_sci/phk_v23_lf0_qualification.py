"""CPU-only qualification gate for PHK-V2.3 LF0.

The module deliberately exposes one interface, :func:`qualify_cpu`.  It reads
only the three nominal development carriers and the already-consumed C0/oracle
artifacts.  It never constructs a neural model, checkpoint, optimizer, or GPU
object.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from .phk_v21_benchmark import (
    PhkV21CaseSpec,
    compare_phk_v21_results,
    evaluate_phk_v21_event,
    load_phk_v21_physical,
    read_phk_v21_result,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT
    / "configs"
    / "phk_v23"
    / "decision_contract_lf0_attribution.json"
)

EXPECTED_SCHEMA = "phk-v23-lf0-decision-contract-v1"
EXPECTED_CONTRACT = "PHK_V23_LF0_ATTRIBUTION_DECISION"
EXPECTED_DATA_SCHEMA = "phk-v23-lf0-data-contract-v1"
EXPECTED_DATA_CONTRACT = "PHK_V23_LF0_MEDIUM_ONLY_DATA"
EXPECTED_METHOD_SCHEMA = "phk-v23-lf0-method-contract-v1"
EXPECTED_METHOD_CONTRACT = "PHK_V23_LF0_EXACT_TOP_MEDIUM_WARMSTART_METHOD"
EXPECTED_PROGRAM_SCHEMA = "phk-v23-lf0-program-contract-v1"
EXPECTED_PROGRAM_CONTRACT = "PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION"
EXPECTED_TASK = "PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE"
EXPECTED_C0_TASK = "PHK_V23_C0_REFERENCE_DISCRETE_STRONGFORM_COMPATIBILITY_AUDIT_EXECUTE"
PHASE_SCALE = 0.5


def _read_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid {label}: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} root must be an object")
    return value


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _verify_identity(identity: Mapping[str, Any], label: str) -> Path:
    exact = _input_path(identity.get("path"), label)
    expected = identity.get("sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError(f"{label} SHA-256 is missing")
    if not exact.is_file() or _sha256_path(exact) != expected.upper():
        raise ValueError(f"{label} byte identity differs from LF0 contract")
    return exact


def _input_path(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} path must be a nonempty string")
    portable = value.replace("\\", "/")
    lowered = f"/{portable.lower().strip('/')}"
    if "/sealed/" in lowered or "stress" in lowered:
        raise ValueError(f"stress or sealed input path is forbidden before I/O: {label}")
    if "checkpoint" in lowered or Path(portable).suffix.lower() in {".pt", ".pth", ".ckpt"}:
        raise ValueError(f"neural checkpoint input is forbidden: {label}")
    relative = Path(portable)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"{label} must be a repository-relative path")
    return ROOT / relative


def _load_contract_bundle(contract_path: Path) -> dict[str, Any]:
    decision = _read_object(Path(contract_path), "LF0 decision contract")
    if decision.get("schema_id") != EXPECTED_SCHEMA:
        raise ValueError("unsupported LF0 qualification contract schema")
    if decision.get("contract_id") != EXPECTED_CONTRACT:
        raise ValueError("unexpected LF0 qualification contract identity")
    program_path = _input_path(decision.get("program_contract"), "program_contract")
    method_path = _input_path(decision.get("method_contract"), "method_contract")
    data_path = _input_path(decision.get("data_contract"), "data_contract")
    qualification_inputs = decision.get("qualification_inputs")
    if not isinstance(qualification_inputs, dict):
        raise ValueError("LF0 decision contract lacks qualification inputs")
    for label in ("c0_artifact", "oracle_floor_seal"):
        identity = qualification_inputs.get(label)
        if not isinstance(identity, dict):
            raise ValueError(f"LF0 decision contract lacks {label} identity")
        _input_path(identity.get("path"), label)

    program = _read_object(program_path, "LF0 program contract")
    if (
        program.get("schema_id") != EXPECTED_PROGRAM_SCHEMA
        or program.get("contract_id") != EXPECTED_PROGRAM_CONTRACT
        or program.get("phase_id") != EXPECTED_TASK
        or program.get("authorization", {}).get("cpu_qualification") is not True
    ):
        raise ValueError("unexpected LF0 program identity or CPU authorization")

    data = _read_object(data_path, "LF0 data contract")
    if (
        data.get("schema_id") != EXPECTED_DATA_SCHEMA
        or data.get("contract_id") != EXPECTED_DATA_CONTRACT
        or data.get("program_contract") != decision.get("program_contract")
    ):
        raise ValueError("unexpected LF0 data contract identity")
    method = _read_object(method_path, "LF0 method contract")
    if (
        method.get("schema_id") != EXPECTED_METHOD_SCHEMA
        or method.get("contract_id") != EXPECTED_METHOD_CONTRACT
        or method.get("program_contract") != decision.get("program_contract")
    ):
        raise ValueError("unexpected LF0 method contract identity")
    training_source = data.get("training_source")
    if not isinstance(training_source, dict):
        raise ValueError("LF0 data contract lacks its medium training source")
    qualification = data.get("qualification_only")
    if not isinstance(qualification, dict):
        raise ValueError("LF0 data contract lacks qualification-only inputs")
    required = {
        "low_fidelity_training_source": training_source,
        "qualification_fine": qualification.get("fine"),
        "qualification_extra_fine": qualification.get("extra_fine"),
    }
    for label, identity in required.items():
        if not isinstance(identity, dict):
            raise ValueError(f"LF0 data contract lacks {label} identity")
        _input_path(identity.get("path"), label)
    return {
        "decision": decision,
        "program": program,
        "method": method,
        "data": data,
        "paths": {
            "program": program_path,
            "method": method_path,
            "data": data_path,
            "decision": Path(contract_path).resolve(),
        },
    }


def _physical():
    return load_phk_v21_physical(
        program_path=ROOT / "configs" / "phk_v21" / "program_contract.json",
        object_path=ROOT / "configs" / "phk_v21" / "object_numerical_contract.json",
        legacy_program_path=ROOT / "configs" / "phk_v2" / "program_contract.json",
        legacy_object_path=ROOT / "configs" / "phk_v2" / "object_numerical_contract.json",
    )


def _waveform(time: np.ndarray, *, period: float, physical: Any) -> np.ndarray:
    spec = physical.payload["waveform"]
    start = float(physical.coordinates["time_start"])
    end = float(physical.coordinates["time_end"])
    amplitude = float(spec["amplitude"])
    ramp_up_end = float(spec["ramp_up_end"])
    hold_end = float(spec["hold_end"])
    ramp_down_end = float(spec["ramp_down_end"])
    local = np.remainder(np.asarray(time, dtype=np.float64) - start, period)
    values = np.where(
        local < ramp_up_end,
        amplitude * local / ramp_up_end,
        np.where(
            local <= hold_end,
            amplitude,
            np.where(
                local < ramp_down_end,
                amplitude * (ramp_down_end - local) / (ramp_down_end - hold_end),
                0.0,
            ),
        ),
    )
    return np.where((time >= start) & (time < end), values, 0.0).astype(np.float64)


def _required_latent_and_guard(
    result: Any,
    *,
    physical: Any,
    absolute_tolerance: float,
    maximum_violation_fraction: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    waveform = _waveform(result.time, period=float(result.case.period), physical=physical)
    upper = np.broadcast_to(waveform[:, None], result.potential.shape)
    amplitude = float(physical.payload["waveform"]["amplitude"])
    z_min = float(physical.coordinates["z_min"])
    z_max = float(physical.coordinates["z_max"])
    zeta = (result.grid.cell_z - z_min) / (z_max - z_min)
    one_minus_zeta = np.broadcast_to(1.0 - zeta[None, :], result.potential.shape)
    waveform_grid = upper
    defined = (waveform_grid >= 1.0e-8 * amplitude) & (one_minus_zeta >= 1.0e-12)
    latent = (
        result.potential[defined] / waveform_grid[defined] - zeta[None, :].repeat(
            result.time.size, axis=0
        )[defined]
    ) / one_minus_zeta[defined]
    zero_waveform = waveform_grid < 1.0e-8 * amplitude
    zero_waveform_error = np.abs(result.potential[zero_waveform])
    top_fixed = (~zero_waveform) & (one_minus_zeta < 1.0e-12)
    top_fixed_error = np.abs(
        result.potential[top_fixed]
        - waveform_grid[top_fixed]
        * zeta[None, :].repeat(result.time.size, axis=0)[top_fixed]
    )
    latent_finite = bool(latent.size > 0 and np.isfinite(latent).all())
    zero_waveform_maximum = (
        float(np.max(zero_waveform_error)) if zero_waveform_error.size else 0.0
    )
    top_fixed_maximum = float(np.max(top_fixed_error)) if top_fixed_error.size else 0.0
    quantiles = (
        np.quantile(latent, [0.05, 0.50, 0.95, 0.99])
        if latent.size
        else np.full(4, np.nan)
    )
    latent_report = {
        "formula": "(V_REFERENCE/WAVEFORM-ZETA)/(1-ZETA)",
        "mask": "WAVEFORM>=1E-8*AMPLITUDE_AND_1-ZETA>=1E-12",
        "defined_point_count": int(latent.size),
        "zero_waveform_point_count": int(zero_waveform_error.size),
        "top_fixed_point_count": int(top_fixed_error.size),
        "all_finite": latent_finite,
        "minimum": float(np.min(latent)) if latent.size else None,
        "maximum": float(np.max(latent)) if latent.size else None,
        "q05": float(quantiles[0]) if latent.size else None,
        "q50": float(quantiles[1]) if latent.size else None,
        "q95": float(quantiles[2]) if latent.size else None,
        "q99": float(quantiles[3]) if latent.size else None,
        "maximum_absolute": float(np.max(np.abs(latent))) if latent.size else None,
        "zero_waveform_maximum_absolute_error": zero_waveform_maximum,
        "top_fixed_maximum_absolute_error": top_fixed_maximum,
        "passed": (
            latent_finite
            and zero_waveform_maximum <= 1.0e-8 * amplitude
            and top_fixed_maximum <= absolute_tolerance
        ),
    }

    values_finite = bool(np.isfinite(result.potential).all())
    if values_finite:
        lower = np.minimum(0.0, upper)
        upper_bound = np.maximum(0.0, upper)
        excess = np.maximum.reduce(
            (
                lower - result.potential,
                result.potential - upper_bound,
                np.zeros_like(result.potential),
            )
        )
        maximum_excess = float(np.max(excess))
        violation_fraction = float(np.mean(excess > absolute_tolerance))
    else:
        excess = np.full_like(result.potential, np.inf, dtype=np.float64)
        maximum_excess = math.inf
        violation_fraction = 1.0
    window_bounds = {
        "W1": (0.0, 0.35),
        "W2": (0.35, 1.25),
        "W3": (1.25, 1.60),
        "W4": (1.60, 2.50),
    }
    by_window: dict[str, Any] = {}
    for name, (start, stop) in window_bounds.items():
        time_mask = (result.time >= start) & (
            result.time <= stop if name == "W4" else result.time < stop
        )
        window_excess = excess[time_mask]
        by_window[name] = {
            "point_count": int(window_excess.size),
            "maximum_absolute_excess": float(np.max(window_excess)) if window_excess.size else 0.0,
            "violation_fraction_above_tolerance": (
                float(np.mean(window_excess > absolute_tolerance))
                if window_excess.size
                else 0.0
            ),
        }
    guard_report = {
        "lower": "MIN(0,WAVEFORM)",
        "upper": "MAX(0,WAVEFORM)",
        "absolute_tolerance": absolute_tolerance,
        "maximum_violation_fraction": maximum_violation_fraction,
        "all_pointwise_values_finite": values_finite,
        "maximum_excess": maximum_excess,
        "violation_fraction": violation_fraction,
        "by_physical_window": by_window,
        "passed": (
            values_finite
            and maximum_excess <= absolute_tolerance
            and violation_fraction <= maximum_violation_fraction
        ),
    }
    return latent_report, guard_report


def _official_c0_gate(
    contract: Mapping[str, Any], c0: Mapping[str, Any], medium_identity: Mapping[str, Any]
) -> dict[str, Any]:
    if c0.get("task_id") != EXPECTED_C0_TASK or c0.get("status") != "COMPLETE":
        raise ValueError("C0 artifact is not the consumed compatibility result")
    compatibility = c0.get("discrete_strongform_compatibility")
    adjudication = c0.get("machine_adjudication")
    if not isinstance(compatibility, dict) or not isinstance(adjudication, dict):
        raise ValueError("C0 artifact lacks compatibility adjudication")
    bound = (
        c0.get("source_identity", {})
        .get("protected_inputs_before", {})
        .get("medium")
    )
    if not isinstance(bound, dict):
        raise ValueError("C0 artifact lacks its medium reference binding")
    if bound.get("path") != medium_identity.get("path") or bound.get("sha256") != medium_identity.get("sha256"):
        raise ValueError("LF0 medium source differs from the C0-bound medium carrier")

    rule = contract["cpu_qualification"]["c0_official_strongform_subverdict"]
    ratio = float(compatibility.get("maximum_residual_to_floor_ratio", math.inf))
    sign = float(compatibility.get("minimum_native_continuous_rhs_sign_agreement", -math.inf))
    ratio_limit = float(rule["maximum_residual_to_floor_ratio"])
    sign_minimum = float(rule["minimum_rhs_sign_agreement"])
    passed = bool(
        compatibility.get("sufficient") is True
        and adjudication.get("strongform_compatible_subverdict") is True
        and math.isfinite(ratio)
        and ratio <= ratio_limit
        and math.isfinite(sign)
        and sign >= sign_minimum
    )
    return {
        "official_cross_resolution_gate_reused": True,
        "numerator_resolution": "EXTRA_FINE_AS_FROZEN_BY_C0",
        "medium_role": "BOUND_INPUT_TO_CROSS_RESOLUTION_FLOOR",
        "maximum_residual_to_floor_ratio": ratio,
        "maximum_allowed_ratio": ratio_limit,
        "minimum_rhs_sign_agreement": sign,
        "minimum_allowed_sign_agreement": sign_minimum,
        "passed": passed,
    }


def _headroom(
    medium: Any,
    extra_fine: Any,
    floor: Mapping[str, Any],
    *,
    physical: Any,
    rule: Mapping[str, Any],
) -> dict[str, Any]:
    report = compare_phk_v21_results(medium, extra_fine, physical=physical)
    deltas = np.asarray(report.component_deltas, dtype=np.float64)
    floor_order = tuple(floor.get("component_order", ()))
    floors = np.asarray(floor.get("component_floors_U"), dtype=np.float64)
    if floor.get("schema_id") != "phk-v21-oracle-floor-seal-v1":
        raise ValueError("unsupported PHK-V2.1 oracle floor seal")
    if floor_order != (
        "PHASE_FIELD_ROI_RMS",
        "TEMPERATURE_FIELD_ROI_RMS",
        "TERMINAL_CURRENT_TRACE_RMS",
        "TWO_CYCLE_EVENT_TIME_RMS",
        "TIME_AVERAGED_PHASE_REGION_SYMMETRIC_DIFFERENCE",
        "TWO_CYCLE_RECOVERY_RMS",
    ):
        raise ValueError("oracle floor component order drift")
    if floors.shape != (6,) or not np.isfinite(floors).all() or np.any(floors <= 0.0):
        raise ValueError("oracle component floors must be finite and positive")
    if deltas.shape != (6,) or not np.isfinite(deltas).all():
        raise ValueError("medium-versus-extra-fine component comparison is invalid")

    primary_index = int(rule["primary_floor_index"])
    co_primary_index = int(rule["co_primary_normalized_floor_index"])
    phase_scale = float(rule["co_primary_unnormalized_scale"])
    if primary_index != 4 or co_primary_index != 0 or phase_scale != PHASE_SCALE:
        raise ValueError("unsupported LF0 correction-headroom component identity")
    d_primary = float(deltas[primary_index])
    d_co_normalized = float(deltas[co_primary_index])
    d_co_unnormalized = phase_scale * d_co_normalized
    u_primary = float(floors[primary_index])
    u_co_normalized = float(floors[co_primary_index])
    u_co_unnormalized = phase_scale * u_co_normalized
    primary_pass = d_primary > u_primary
    co_primary_pass = d_co_unnormalized > u_co_unnormalized
    return {
        "comparison": "PHK_V21_MEDIUM_VS_EXTRA_FINE_ON_MEDIUM_COMMON_CARRIER",
        "E_primary_medium": d_primary,
        "E_primary_extra_fine": 0.0,
        "D_primary": d_primary,
        "U_primary": u_primary,
        "primary_exceeds_floor": primary_pass,
        "E_co_primary_medium_unnormalized": d_co_unnormalized,
        "E_co_primary_extra_fine_unnormalized": 0.0,
        "D_co_primary_unnormalized": d_co_unnormalized,
        "U_co_primary_unnormalized": u_co_unnormalized,
        "D_co_primary_normalized_by_0_5": d_co_normalized,
        "U_co_primary_normalized_by_0_5": u_co_normalized,
        "co_primary_exceeds_floor": co_primary_pass,
        "pass_logic": "PRIMARY_STRICTLY_EXCEEDS_FLOOR_OR_CO_PRIMARY_STRICTLY_EXCEEDS_FLOOR",
        "passed": bool(primary_pass or co_primary_pass),
        "floor_role": "FIXED_DISCRETIZATION_RESOLUTION_SENSITIVITY_MARGIN_NOT_CONTINUUM_ERROR_BOUND",
    }


def _event_payload(event: Any) -> dict[str, Any]:
    payload = asdict(event)
    payload["cycles"] = [dict(cycle) for cycle in payload["cycles"]]
    payload["failures"] = list(payload["failures"])
    return payload


def _strict_json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def qualify_cpu(
    contract_path: Path,
    output_path: Path | None = None,
    *,
    source_identity: str | None = None,
    source_commit: str | None = None,
) -> dict[str, Any]:
    """Run the frozen local nominal-only LF0 CPU qualification.

    Gate failures are returned as ``passed=False`` with explicit blockers.
    Malformed identities or forbidden paths raise ``ValueError`` before any
    carrier is opened.
    """

    if (source_identity is None) != (source_commit is None):
        raise ValueError("LF0 qualified source identity and commit must be supplied together")
    if source_identity is not None and (
        not source_identity.startswith("LF0-BUNDLE-")
        or len(source_identity) != len("LF0-BUNDLE-") + 64
        or any(character not in "0123456789ABCDEF" for character in source_identity[11:])
    ):
        raise ValueError("LF0 qualified source identity is malformed")
    if source_commit is not None and (
        len(source_commit) != 40
        or any(character not in "0123456789abcdefABCDEF" for character in source_commit)
    ):
        raise ValueError("LF0 qualified source commit is malformed")

    bundle = _load_contract_bundle(Path(contract_path))
    contract = bundle["decision"]
    data_contract = bundle["data"]
    inputs = contract["qualification_inputs"]
    c0_path = _verify_identity(inputs["c0_artifact"], "c0_artifact")
    floor_path = _verify_identity(inputs["oracle_floor_seal"], "oracle_floor_seal")
    _verify_identity(inputs["c0_contract"], "c0_contract")
    _verify_identity(inputs["oracle_floor_contract"], "oracle_floor_contract")
    medium_identity = data_contract["training_source"]
    fine_identity = data_contract["qualification_only"]["fine"]
    extra_identity = data_contract["qualification_only"]["extra_fine"]
    medium_path = _verify_identity(medium_identity, "low_fidelity_training_source")
    fine_path = _verify_identity(fine_identity, "qualification_fine")
    extra_path = _verify_identity(extra_identity, "qualification_extra_fine")

    c0 = _read_object(c0_path, "C0 artifact")
    floor = _read_object(floor_path, "oracle floor seal")
    c0_gate = _official_c0_gate(contract, c0, medium_identity)
    actual_medium_sha = _sha256_path(medium_path)

    physical = _physical()
    expected_case = PhkV21CaseSpec.nominal(physical)
    carriers = {
        "medium": read_phk_v21_result(medium_path, physical=physical),
        "fine": read_phk_v21_result(fine_path, physical=physical),
        "extra_fine": read_phk_v21_result(extra_path, physical=physical),
    }
    for name, carrier in carriers.items():
        if (
            carrier.case.control != expected_case.control
            or carrier.case.physics_identity() != expected_case.physics_identity()
        ):
            raise ValueError(f"{name} carrier is not the nominal development case")

    guard_rule = contract["potential_maximum_principle"]
    tolerance = float(guard_rule["absolute_tolerance"])
    maximum_violation_fraction = float(guard_rule["maximum_violation_fraction"])
    references: dict[str, Any] = {}
    blockers: list[str] = []
    for name, carrier in carriers.items():
        latent, guard = _required_latent_and_guard(
            carrier,
            physical=physical,
            absolute_tolerance=tolerance,
            maximum_violation_fraction=maximum_violation_fraction,
        )
        references[name] = {
            "path": str(
                {
                    "medium": medium_identity,
                    "fine": fine_identity,
                    "extra_fine": extra_identity,
                }[name]["path"]
            ),
            "required_exact_top_latent": latent,
            "potential_maximum_principle": guard,
        }
        if not latent["passed"]:
            blockers.append(f"{name.upper()}_EXACT_TOP_REQUIRED_LATENT_FAILED")
        if not guard["passed"]:
            blockers.append(f"{name.upper()}_POTENTIAL_MAXIMUM_PRINCIPLE_FAILED")

    medium_event = _event_payload(
        evaluate_phk_v21_event(carriers["medium"], physical=physical)
    )
    headroom = _headroom(
        carriers["medium"],
        carriers["extra_fine"],
        floor,
        physical=physical,
        rule=contract["cpu_qualification"]["correction_headroom"],
    )
    if not c0_gate["passed"]:
        blockers.append("C0_STRONGFORM_GATE_FAILED")
    if not medium_event["passed"]:
        blockers.append("MEDIUM_TWO_CYCLE_COMPETENCE_FAILED")
    if not headroom["passed"]:
        blockers.append("CORRECTION_HEADROOM_FAILED")

    passed = not blockers
    contract_identities = {
        role: {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": _sha256_path(path),
        }
        for role, path in bundle["paths"].items()
    }
    input_paths = {
        "low_fidelity_training_source": medium_path,
        "qualification_fine": fine_path,
        "qualification_extra_fine": extra_path,
        "c0_artifact": c0_path,
        "c0_contract": _input_path(inputs["c0_contract"]["path"], "c0_contract"),
        "oracle_floor_contract": _input_path(
            inputs["oracle_floor_contract"]["path"], "oracle_floor_contract"
        ),
        "oracle_floor_seal": floor_path,
    }
    input_identities = {
        label: {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": _sha256_path(path),
            "size_bytes": path.stat().st_size,
        }
        for label, path in input_paths.items()
    }
    report: dict[str, Any] = {
        "schema_id": "phk-v23-lf0-cpu-qualification-v1",
        "task_id": EXPECTED_TASK,
        "status": "LF0_CPU_QUALIFIED" if passed else "LF0_CPU_QUALIFICATION_BLOCKED",
        "passed": passed,
        "blockers": blockers,
        "qualified_source_identity": source_identity,
        "source_commit": source_commit,
        "contract_identities": contract_identities,
        "input_identities": input_identities,
        "contract_path": str(Path(contract_path).resolve()),
        "data_contract_path": contract["data_contract"],
        "medium_source_sha256": actual_medium_sha,
        "c0_strongform_gate": c0_gate,
        "references": references,
        "medium_event_competence": medium_event,
        "correction_headroom": headroom,
        "execution_boundary": {
            "device": "CPU",
            "dtype": "FLOAT64",
            "gpu_hours": 0,
            "neural_checkpoint_loaded": False,
            "neural_model_constructed": False,
            "optimizer_constructed_or_stepped": False,
            "stress_read": False,
            "reference_role": "LOCAL_NOMINAL_DEVELOPMENT_QUALIFICATION_ONLY",
        },
    }
    encoded = _strict_json_bytes(report)
    if output_path is not None:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as handle:
            handle.write(encoded)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--source-identity")
    parser.add_argument("--source-commit")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = qualify_cpu(
        args.contract,
        output_path=args.output,
        source_identity=args.source_identity,
        source_commit=args.source_commit,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "passed": report["passed"],
                "blockers": report["blockers"],
                "output": str(args.output.resolve()) if args.output else None,
            },
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
    )
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["DEFAULT_CONTRACT", "main", "qualify_cpu"]
