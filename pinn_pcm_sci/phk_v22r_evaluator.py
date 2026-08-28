"""Local-only evaluator and sealed-reference access gate for PHK-V2.2R."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

from .phk_benchmark import PhkControl
from .phk_v21_benchmark import (
    PhkV21OracleResult,
    PhkV21CaseSpec,
    load_phk_v21_physical,
    read_phk_v21_result,
)
from .phk_v22r_prediction import read_prediction_carrier
from .phk_v22r_pinn import PhkV22RArm


ROOT = Path(__file__).resolve().parents[1]
PROGRAM_CONTRACT = ROOT / "configs" / "phk_v22r" / "program_contract.json"
METHOD_CONTRACT = ROOT / "configs" / "phk_v22r" / "method_contract.json"
CANDIDATE_FREEZE = ROOT / "configs" / "phk_v22r" / "candidate_freeze.json"
NOMINAL_REFERENCE = (
    ROOT
    / "outputs"
    / "runs"
    / "20260828T-phk-v21-s1-q-06-nominal-extra-fine"
    / "result-intent-06.npz"
)
STRESS_REFERENCES = {
    PhkControl.INTERFACE_WIDTH_0_025: ROOT
    / "outputs"
    / "sealed"
    / "phk_v22r"
    / "narrow_interface_extra_fine"
    / "reference.npz",
    PhkControl.HEATER_WIDTH_0_50: ROOT
    / "outputs"
    / "sealed"
    / "phk_v22r"
    / "wide_heater_extra_fine"
    / "reference.npz",
}
STRESS_REFERENCES_BY_VALUE = {control.value: path for control, path in STRESS_REFERENCES.items()}


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _portable_path(path: Path) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def _physical_contract():
    return load_phk_v21_physical(
        program_path=ROOT / "configs" / "phk_v21" / "program_contract.json",
        object_path=ROOT / "configs" / "phk_v21" / "object_numerical_contract.json",
        legacy_program_path=ROOT / "configs" / "phk_v2" / "program_contract.json",
        legacy_object_path=ROOT / "configs" / "phk_v2" / "object_numerical_contract.json",
    )


def validate_candidate_freeze(
    path: Path = CANDIDATE_FREEZE,
) -> dict[str, Any]:
    """Validate the one-way method freeze before any stress carrier is opened."""

    exact = Path(path)
    try:
        payload = json.loads(exact.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PermissionError(
            "stress references are sealed until candidate_freeze.json exists"
        ) from exc
    if payload.get("schema_id") != "phk-v22r-candidate-freeze-v1":
        raise PermissionError("unsupported V2.2R candidate freeze schema")
    if payload.get("status") != "FROZEN":
        raise PermissionError("stress references remain sealed before FROZEN status")
    if payload.get("program_contract_sha256") != _sha256_path(PROGRAM_CONTRACT):
        raise PermissionError("candidate freeze is not bound to the live V2.2R contract")
    if payload.get("method_contract_sha256") != _sha256_path(METHOD_CONTRACT):
        raise PermissionError("candidate freeze is not bound to the live method contract")
    selected = payload.get("selected_candidate")
    if not isinstance(selected, dict):
        raise PermissionError("candidate freeze lacks a selected candidate")
    required_candidate = {
        "arm",
        "training_config_sha256",
        "seed",
        "updates",
        "architecture",
        "training_config",
        "decision_status",
    }
    if not required_candidate.issubset(selected):
        raise PermissionError("candidate freeze is missing selected-candidate identity")
    if int(selected["seed"]) != 17:
        raise PermissionError("candidate freeze changed the confirmation seed")
    if payload.get("strongest_component") not in {
        PhkV22RArm.MF_ONLY.value,
        PhkV22RArm.SAMPLER_ONLY.value,
    }:
        raise PermissionError("candidate freeze lacks a valid strongest component")
    equal_raw = payload.get("equal_compute_raw_identity")
    if not isinstance(equal_raw, dict) or equal_raw.get("arm") != PhkV22RArm.STRONG_RAW.value:
        raise PermissionError("candidate freeze lacks the equal-compute raw identity")
    seals = payload.get("stress_reference_seals")
    if not isinstance(seals, dict):
        raise PermissionError("candidate freeze lacks stress reference byte seals")
    for control in STRESS_REFERENCES:
        item = seals.get(control.value)
        if not isinstance(item, dict):
            raise PermissionError(f"candidate freeze lacks {control.value} byte seal")
        sha = item.get("carrier_sha256")
        if not isinstance(sha, str) or len(sha) != 64:
            raise PermissionError(f"candidate freeze has invalid {control.value} hash")
    return payload


def _validate_stress_prediction_identity(
    metadata: Mapping[str, Any], freeze: Mapping[str, Any]
) -> str:
    config = metadata.get("training_config")
    if not isinstance(config, dict):
        raise ValueError("stress prediction lacks a training configuration")
    selected = freeze["selected_candidate"]
    selected_config = selected["training_config"]
    strongest = freeze["strongest_component"]
    equal_raw = freeze["equal_compute_raw_identity"]
    arm = config.get("arm")
    if arm == selected["arm"]:
        role = "SELECTED_METHOD"
        template = selected_config
    elif arm == strongest:
        role = "STRONGEST_COMPONENT"
        template = {
            **selected_config,
            "arm": strongest,
            "hidden_width": 64,
            "hidden_layers": 4,
        }
    elif (
        arm == PhkV22RArm.STRONG_RAW.value
        and int(config.get("hidden_width", -1))
        == int(equal_raw.get("hidden_width", -2))
    ):
        role = "EQUAL_COMPUTE_RAW"
        template = {
            **selected_config,
            "arm": PhkV22RArm.STRONG_RAW.value,
            "hidden_width": int(equal_raw["hidden_width"]),
            "hidden_layers": int(equal_raw["hidden_layers"]),
        }
    else:
        raise ValueError("stress prediction is outside the frozen three-arm matrix")
    frozen_keys = (
        "arm",
        "updates",
        "seed",
        "hidden_width",
        "hidden_layers",
        "frequency_band",
        "learning_rate",
        "gradient_clip_norm",
        "interior_points",
        "boundary_points",
        "initial_points",
        "candidate_pool_multiplier",
        "refresh_updates",
        "pde_weight",
        "boundary_weight",
        "initial_weight",
        "dtype",
    )
    for key in frozen_keys:
        if config.get(key) != template.get(key):
            raise ValueError(f"stress prediction changed frozen training key: {key}")
    if config.get("case_control") not in STRESS_REFERENCES_BY_VALUE:
        raise ValueError("stress prediction is not a frozen stress case")
    return role


def load_reference(
    control: PhkControl | str,
    *,
    candidate_freeze_path: Path = CANDIDATE_FREEZE,
) -> tuple[PhkV21OracleResult, str]:
    """Open nominal freely for development; fail closed for stress before freeze."""

    selected = PhkControl(control)
    physical = _physical_contract()
    if selected is PhkControl.FULL:
        program = json.loads(PROGRAM_CONTRACT.read_text(encoding="utf-8"))
        expected = program["reference_roles"]["nominal_development"]["sha256"]
        path = NOMINAL_REFERENCE
    elif selected in STRESS_REFERENCES:
        freeze = validate_candidate_freeze(candidate_freeze_path)
        path = STRESS_REFERENCES[selected]
        expected = freeze["stress_reference_seals"][selected.value]["carrier_sha256"]
    else:
        raise ValueError("reference case is outside the PHK-V2.2R matrix")
    actual = _sha256_path(path)
    if actual != expected:
        raise ValueError(f"reference byte hash mismatch for {selected.value}")
    result = read_phk_v21_result(path, physical=physical)
    if result.case.control is not selected:
        raise ValueError("reference case-control identity mismatch")
    return result, actual


def _time_rms(trace: np.ndarray, time: np.ndarray) -> float:
    duration = float(time[-1] - time[0])
    return float(math.sqrt(np.trapezoid(trace * trace, time) / duration))


def _event_summary(
    phase: np.ndarray,
    *,
    time: np.ndarray,
    roi: np.ndarray,
    period: float,
    phase_threshold: float,
    event_fraction: float,
) -> dict[str, Any]:
    roi_fraction = np.mean(phase[:, roi] >= phase_threshold, axis=1)
    full_fraction = np.mean(phase >= phase_threshold, axis=1)
    outside_fraction = np.mean(phase[:, ~roi] >= phase_threshold, axis=1)
    cycles = []
    failures = []
    for cycle_index in range(2):
        start = cycle_index * period
        end = (cycle_index + 1) * period
        mask = (time >= start) & (time <= end if cycle_index == 1 else time < end)
        indices = np.flatnonzero(mask)
        values = roi_fraction[indices]
        peak_position = int(np.argmax(values))
        peak_index = int(indices[peak_position])
        crossing = None
        for before, after in zip(indices[:-1], indices[1:], strict=True):
            low = float(roi_fraction[before])
            high = float(roi_fraction[after])
            if low < event_fraction <= high and high > low:
                fraction = (event_fraction - low) / (high - low)
                crossing = float(time[before] + fraction * (time[after] - time[before]))
                break
        pre = float(values[0])
        peak = float(values[peak_position])
        excursion = peak - pre
        recovery = (
            float((peak - float(values[-1])) / excursion) if excursion > 0.0 else 0.0
        )
        cycle = {
            "cycle": cycle_index + 1,
            "event_time": crossing,
            "pre_roi_fraction": pre,
            "peak_roi_fraction": peak,
            "peak_full_domain_fraction": float(full_fraction[peak_index]),
            "peak_outside_roi_fraction": float(outside_fraction[peak_index]),
            "recovery_fraction": recovery,
            "peak_time_index": peak_index,
        }
        cycles.append(cycle)
        if crossing is None:
            failures.append(f"cycle_{cycle_index + 1}_event_missing")
        if peak < 0.02:
            failures.append(f"cycle_{cycle_index + 1}_roi_peak_below_minimum")
        if cycle["peak_full_domain_fraction"] > 0.45:
            failures.append(f"cycle_{cycle_index + 1}_false_global_transition")
        if cycle["peak_outside_roi_fraction"] > 0.10:
            failures.append(f"cycle_{cycle_index + 1}_locality_failure")
        if recovery < 0.70:
            failures.append(f"cycle_{cycle_index + 1}_recovery_failure")
    return {
        "cycles": cycles,
        "roi_fraction": roi_fraction,
        "full_fraction": full_fraction,
        "outside_fraction": outside_fraction,
        "failures": failures,
        "passed": not failures,
    }


def _interface_hausdorff(
    prediction: np.ndarray,
    reference: np.ndarray,
    *,
    x_axis: np.ndarray,
    z_axis: np.ndarray,
    time_indices: list[int],
) -> float:
    distances = []
    x_mesh, z_mesh = np.meshgrid(x_axis, z_axis, indexing="xy")
    for index in time_indices:
        pred_region = prediction[index].reshape(z_axis.size, x_axis.size) >= 0.5
        ref_region = reference[index].reshape(z_axis.size, x_axis.size) >= 0.5
        pred_edge = pred_region & ~ndimage.binary_erosion(pred_region)
        ref_edge = ref_region & ~ndimage.binary_erosion(ref_region)
        if not np.any(pred_edge) or not np.any(ref_edge):
            return math.inf
        pred_points = np.column_stack((x_mesh[pred_edge], z_mesh[pred_edge]))
        ref_points = np.column_stack((x_mesh[ref_edge], z_mesh[ref_edge]))
        pred_tree = cKDTree(pred_points)
        ref_tree = cKDTree(ref_points)
        forward = float(ref_tree.query(pred_points, k=1)[0].max())
        reverse = float(pred_tree.query(ref_points, k=1)[0].max())
        distances.append(max(forward, reverse))
    return float(np.mean(distances)) if distances else math.inf


def _high_k_relative_error(
    prediction: np.ndarray,
    reference: np.ndarray,
    *,
    nx: int,
    nz: int,
) -> float:
    pred_grid = prediction.reshape(prediction.shape[0], nz, nx)
    ref_grid = reference.reshape(reference.shape[0], nz, nx)
    pred_fft = np.fft.rfft2(pred_grid, axes=(1, 2))
    ref_fft = np.fft.rfft2(ref_grid, axes=(1, 2))
    kz = np.fft.fftfreq(nz)[:, None]
    kx = np.fft.rfftfreq(nx)[None, :]
    radius = np.sqrt(kx * kx + kz * kz)
    high = radius >= 0.25
    numerator = float(np.sum(np.abs(pred_fft[:, high] - ref_fft[:, high]) ** 2))
    denominator = float(np.sum(np.abs(ref_fft[:, high]) ** 2))
    return math.sqrt(numerator / max(denominator, 1.0e-30))


def _hotspot_metrics(
    prediction: np.ndarray,
    reference: np.ndarray,
    *,
    x_axis: np.ndarray,
    z_axis: np.ndarray,
) -> dict[str, float]:
    ref_peak = int(np.argmax(reference))
    time_index, cell_index = np.unravel_index(ref_peak, reference.shape)
    pred_grid = prediction[time_index].reshape(z_axis.size, x_axis.size)
    ref_grid = reference[time_index].reshape(z_axis.size, x_axis.size)
    pred_location = np.unravel_index(int(np.argmax(pred_grid)), pred_grid.shape)
    ref_location = np.unravel_index(int(np.argmax(ref_grid)), ref_grid.shape)
    distance = math.hypot(
        float(x_axis[pred_location[1]] - x_axis[ref_location[1]]),
        float(z_axis[pred_location[0]] - z_axis[ref_location[0]]),
    )

    def width(profile: np.ndarray) -> float:
        maximum = float(np.max(profile))
        if maximum <= 0.0:
            return 0.0
        active = np.flatnonzero(profile >= 0.5 * maximum)
        if active.size < 2:
            return 0.0
        return float(x_axis[active[-1]] - x_axis[active[0]])

    pred_width = width(pred_grid[pred_location[0]])
    ref_width = width(ref_grid[ref_location[0]])
    return {
        "hotspot_location_error": distance,
        "temperature_fwhm_prediction": pred_width,
        "temperature_fwhm_reference": ref_width,
        "temperature_fwhm_absolute_error": abs(pred_width - ref_width),
    }


def evaluate_prediction(
    *,
    prediction_path: Path,
    control: PhkControl | str,
    candidate_freeze_path: Path = CANDIDATE_FREEZE,
) -> dict[str, Any]:
    selected = PhkControl(control)
    prediction_metadata, prediction = read_prediction_carrier(prediction_path)
    if prediction_metadata["training_config"]["case_control"] != selected.value:
        raise ValueError("prediction and requested case controls differ")
    confirmation_role = None
    if selected in STRESS_REFERENCES:
        freeze = validate_candidate_freeze(candidate_freeze_path)
        confirmation_role = _validate_stress_prediction_identity(
            prediction_metadata, freeze
        )
    reference, reference_sha = load_reference(
        selected, candidate_freeze_path=candidate_freeze_path
    )
    x_axis = reference.grid.x_centers
    z_axis = reference.grid.z_centers
    if not np.array_equal(prediction["x"], x_axis):
        raise ValueError("prediction x axis differs from the reference grid")
    if not np.array_equal(prediction["z"], z_axis):
        raise ValueError("prediction z axis differs from the reference grid")
    if not np.array_equal(prediction["time"], reference.time):
        raise ValueError("prediction time axis differs from the reference carrier")
    for name in ("potential", "temperature", "phase"):
        if prediction[name].shape != getattr(reference, name).shape:
            raise ValueError(f"prediction/reference {name} shape mismatch")

    physical = _physical_contract()
    event = physical.payload["qualification_event"]
    roi_spec = event["roi"]
    roi = (
        (np.abs(reference.grid.cell_x) <= float(roi_spec["abs_x_max"]))
        & (reference.grid.cell_z >= float(roi_spec["z_min"]))
        & (reference.grid.cell_z <= float(roi_spec["z_max"]))
    )
    time = reference.time
    duration = float(time[-1] - time[0])
    pred_active = prediction["phase"] >= float(event["phase_threshold"])
    ref_active = reference.phase >= float(event["phase_threshold"])
    symmetric_fraction = np.mean(np.logical_xor(pred_active, ref_active), axis=1)
    primary = float(np.trapezoid(symmetric_fraction, time) / duration)
    phase_roi_mse = np.mean(
        (prediction["phase"][:, roi] - reference.phase[:, roi]) ** 2,
        axis=1,
    )
    temperature_roi_mse = np.mean(
        (prediction["temperature"][:, roi] - reference.temperature[:, roi]) ** 2,
        axis=1,
    )
    potential_mse = np.mean(
        (prediction["potential"] - reference.potential) ** 2,
        axis=1,
    )
    phase_roi_rms = float(math.sqrt(np.trapezoid(phase_roi_mse, time) / duration))
    temperature_roi_rms = float(
        math.sqrt(np.trapezoid(temperature_roi_mse, time) / duration)
    )
    potential_rms = float(math.sqrt(np.trapezoid(potential_mse, time) / duration))
    current_rms = _time_rms(prediction["top_current"] - reference.top_current, time)
    current_reference_rms = _time_rms(reference.top_current, time)
    current_nrmse = current_rms / max(current_reference_rms, 1.0e-12)
    pulse_energy_error = abs(
        float(np.trapezoid(prediction["joule_power"], time))
        - float(np.trapezoid(reference.joule_power, time))
    ) / max(abs(float(np.trapezoid(reference.joule_power, time))), 1.0e-12)

    prediction_event = _event_summary(
        prediction["phase"],
        time=time,
        roi=roi,
        period=reference.case.period,
        phase_threshold=float(event["phase_threshold"]),
        event_fraction=float(event["event_threshold_roi_fraction"]),
    )
    reference_event = _event_summary(
        reference.phase,
        time=time,
        roi=roi,
        period=reference.case.period,
        phase_threshold=float(event["phase_threshold"]),
        event_fraction=float(event["event_threshold_roi_fraction"]),
    )
    if all(
        cycle["event_time"] is not None
        for cycle in prediction_event["cycles"] + reference_event["cycles"]
    ):
        event_time_rms = math.sqrt(
            sum(
                (
                    (pred["event_time"] - ref["event_time"])
                    / reference.case.period
                )
                ** 2
                for pred, ref in zip(
                    prediction_event["cycles"], reference_event["cycles"], strict=True
                )
            )
            / 2.0
        )
    else:
        event_time_rms = math.inf
    recovery_rms = math.sqrt(
        sum(
            (pred["recovery_fraction"] - ref["recovery_fraction"]) ** 2
            for pred, ref in zip(
                prediction_event["cycles"], reference_event["cycles"], strict=True
            )
        )
        / 2.0
    )
    interface_indices = [
        int(cycle["peak_time_index"]) for cycle in reference_event["cycles"]
    ]
    hausdorff = _interface_hausdorff(
        prediction["phase"],
        reference.phase,
        x_axis=x_axis,
        z_axis=z_axis,
        time_indices=interface_indices,
    )
    high_k = _high_k_relative_error(
        prediction["phase"],
        reference.phase,
        nx=x_axis.size,
        nz=z_axis.size,
    )
    hotspot = _hotspot_metrics(
        prediction["temperature"],
        reference.temperature,
        x_axis=x_axis,
        z_axis=z_axis,
    )
    finite = all(np.isfinite(value).all() for value in prediction.values())
    phase_range = bool(
        np.min(prediction["phase"]) >= -1.0e-10
        and np.max(prediction["phase"]) <= 1.0 + 1.0e-10
    )
    hard_guard_failures = list(prediction_event["failures"])
    if not finite:
        hard_guard_failures.append("nonfinite_prediction")
    if not phase_range:
        hard_guard_failures.append("phase_range_failure")

    return {
        "schema_id": "phk-v22r-evaluation-v1",
        "status": "EVALUATED_LOCAL_REFERENCE_ONLY",
        "case_control": selected.value,
        "prediction_path": _portable_path(prediction_path),
        "prediction_sha256": _sha256_path(prediction_path),
        "reference_path": str(
            (NOMINAL_REFERENCE if selected is PhkControl.FULL else STRESS_REFERENCES[selected])
            .resolve()
            .relative_to(ROOT)
        ),
        "reference_sha256": reference_sha,
        "program_contract_sha256": _sha256_path(PROGRAM_CONTRACT),
        "method_contract_sha256": _sha256_path(METHOD_CONTRACT),
        "training_config_sha256": prediction_metadata["training_config_sha256"],
        "confirmation_role": confirmation_role,
        "architecture": prediction_metadata["architecture"],
        "metrics": {
            "time_averaged_phase_region_symmetric_difference": primary,
            "phase_roi_continuous_rms": phase_roi_rms,
            "phase_roi_continuous_nrmse_by_0_5": phase_roi_rms / 0.5,
            "temperature_roi_rms": temperature_roi_rms,
            "temperature_roi_nrmse_by_0_45": temperature_roi_rms / 0.45,
            "potential_full_rms": potential_rms,
            "terminal_current_trace_rms": current_rms,
            "terminal_current_trace_nrmse": current_nrmse,
            "two_cycle_event_time_rms_period_normalized": event_time_rms,
            "two_cycle_recovery_rms": recovery_rms,
            "interface_hausdorff_at_cycle_peaks": hausdorff,
            "phase_high_k_relative_error": high_k,
            "pulse_energy_relative_error": pulse_energy_error,
            **hotspot,
        },
        "hard_guards": {
            "passed": not hard_guard_failures,
            "failures": hard_guard_failures,
            "finite_values": finite,
            "phase_range": phase_range,
            "event_topology": prediction_event,
        },
        "reference_event": reference_event,
        "claim_boundary": "FIXED_DISCRETE_CASE_SPECIFIC_NUMERICAL_EVIDENCE",
    }


def write_evaluation(path: Path, report: Mapping[str, Any]) -> None:
    exact = Path(path)
    exact.parent.mkdir(parents=True, exist_ok=True)
    with exact.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prediction", type=Path, required=True)
    parser.add_argument(
        "--control",
        choices=[
            PhkControl.FULL.value,
            PhkControl.INTERFACE_WIDTH_0_025.value,
            PhkControl.HEATER_WIDTH_0_50.value,
        ],
        required=True,
    )
    parser.add_argument("--candidate-freeze", type=Path, default=CANDIDATE_FREEZE)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = evaluate_prediction(
        prediction_path=args.prediction,
        control=args.control,
        candidate_freeze_path=args.candidate_freeze,
    )
    write_evaluation(args.output, report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "case_control": report["case_control"],
                "primary": report["metrics"][
                    "time_averaged_phase_region_symmetric_difference"
                ],
                "co_primary": report["metrics"]["phase_roi_continuous_rms"],
                "hard_guards_passed": report["hard_guards"]["passed"],
                "output": str(args.output.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CANDIDATE_FREEZE",
    "NOMINAL_REFERENCE",
    "STRESS_REFERENCES",
    "evaluate_prediction",
    "load_reference",
    "main",
    "validate_candidate_freeze",
    "write_evaluation",
]
