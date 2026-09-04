"""Local CPU qualification for the PHK-V2.3 LF1 pilot."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .phk_v22r_pinn import range_preserving_exact_top_fraction
from .phk_v22r_prediction import _load_model, read_prediction_carrier
from .phk_v22r_training import ROOT, load_case_physics
from .phk_v23_lf0 import (
    LF0LowFidelityBatchStream,
    _physical_object,
    _sha256_path,
)
from .phk_v23_lf1 import (
    DATA_CONTRACT_PATH,
    MediumEventDataset,
    TASK_ID,
    contract_identity,
    load_contracts,
)


def _verify_binding(binding: Mapping[str, Any], label: str) -> Path:
    relative = binding.get("path")
    expected_hash = binding.get("sha256")
    if not isinstance(relative, str) or not isinstance(expected_hash, str):
        raise ValueError(f"LF1 qualification binding is malformed: {label}")
    path = (ROOT / Path(relative.replace("/", "\\"))).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PermissionError(f"LF1 qualification input escaped root: {label}") from exc
    if not path.is_file():
        raise FileNotFoundError(f"LF1 qualification input is absent: {label}")
    actual = _sha256_path(path)
    if actual != expected_hash.upper():
        raise ValueError(f"LF1 qualification input hash drift: {label}")
    return path


def _strict_write(path: Path, payload: Mapping[str, Any]) -> Path:
    encoded = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8") + b"\n"
    exact = Path(path).resolve()
    exact.parent.mkdir(parents=True, exist_ok=True)
    with exact.open("xb") as handle:
        handle.write(encoded)
    return exact


def _safe_ratio(numerator: int, denominator: int) -> float | None:
    return float(numerator / denominator) if denominator else None


def _cycle_masks(time: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(time, dtype=np.float64).reshape(-1)
    return (values >= 0.0) & (values <= 0.35), (values >= 1.25) & (values <= 1.60)


def _old_sampler_exposure(
    dataset: MediumEventDataset,
    *,
    physics: Any,
    draws: int,
) -> dict[str, Any]:
    stream = LF0LowFidelityBatchStream.from_structured_arrays(
        physics=physics,
        time=dataset.time,
        x=dataset.x,
        z=dataset.z,
        fields=dataset.fields,
        points_per_stratum=128,
    )
    counts = {"cycle_1": 0, "cycle_2": 0, "all_points": 0}
    steps_with_event = {"cycle_1": 0, "cycle_2": 0}
    for step in range(1, int(draws) + 1):
        batch = stream.draw(step)
        time = batch.coordinates[:, 2].numpy()
        phase = batch.targets[:, 2].numpy()
        first = (time >= 0.0) & (time <= 0.35) & (phase >= 0.5)
        second = (time >= 1.25) & (time <= 1.60) & (phase >= 0.5)
        counts["cycle_1"] += int(np.count_nonzero(first))
        counts["cycle_2"] += int(np.count_nonzero(second))
        counts["all_points"] += int(phase.size)
        steps_with_event["cycle_1"] += int(np.any(first))
        steps_with_event["cycle_2"] += int(np.any(second))
    return {
        "draws": int(draws),
        "points": counts,
        "event_fraction_of_all_points": {
            name: _safe_ratio(counts[name], counts["all_points"])
            for name in ("cycle_1", "cycle_2")
        },
        "steps_with_at_least_one_event_point": steps_with_event,
        "rolling_sha256": stream.rolling_sha256,
    }


def _topology_masks_from_direct(
    arrays: Mapping[str, np.ndarray],
) -> dict[str, np.ndarray]:
    phase = np.asarray(arrays["phase"], dtype=np.float64)
    time = np.asarray(arrays["time"], dtype=np.float64).reshape(-1)
    derivative = np.gradient(phase, time, axis=0, edge_order=1)
    first, second = _cycle_masks(time)
    initial = phase[0:1]
    nx = int(np.asarray(arrays["x"]).size)
    nz = int(np.asarray(arrays["z"]).size)
    roi_spatial = (
        (np.asarray(arrays["x"])[None, :] >= -0.55)
        & (np.asarray(arrays["x"])[None, :] <= 0.55)
        & (np.asarray(arrays["z"])[:, None] <= 0.55)
    ).reshape(nx * nz)
    roi_mean = np.mean(phase[:, roi_spatial], axis=1)
    first_peak = float(time[np.argmax(np.where(time <= 1.25, roi_mean, -np.inf))])
    second_peak = float(time[np.argmax(np.where(time >= 1.25, roi_mean, -np.inf))])
    tt = time[:, None]
    masks = {
        "event_cycle_1": first[:, None] & (phase >= 0.5),
        "event_cycle_2": second[:, None] & (phase >= 0.5),
        "transition_cycle_1": first[:, None] & (phase < 0.5) & (derivative > 0.0),
        "transition_cycle_2": second[:, None] & (phase < 0.5) & (derivative > 0.0),
        "recovery_cycle_1": (tt > 0.35) & (tt <= 1.25) & (tt > first_peak) & (derivative < 0.0) & (phase > initial),
        "recovery_cycle_2": (tt > 1.60) & (tt <= 2.50) & (tt > second_peak) & (derivative < 0.0) & (phase > initial),
    }
    occupied = np.zeros_like(phase, dtype=bool)
    for mask in masks.values():
        occupied |= mask
    masks["background_complement"] = ~occupied
    return masks


def _old_prediction_diagnostics(
    old_arrays: Mapping[str, np.ndarray],
    direct_arrays: Mapping[str, np.ndarray],
    *,
    physics: Any,
    tolerance: float,
) -> dict[str, Any]:
    for name in ("x", "z", "time"):
        if not np.array_equal(old_arrays[name], direct_arrays[name]):
            raise ValueError(f"old B0 and LF_ONLY {name} axes do not align")
    if old_arrays["phase"].shape != direct_arrays["phase"].shape:
        raise ValueError("old B0 and LF_ONLY phase shapes do not align")
    masks = _topology_masks_from_direct(direct_arrays)
    phase_error = ((old_arrays["phase"] - direct_arrays["phase"]) / 0.5) ** 2
    loss_by_category: dict[str, Any] = {}
    for name, mask in masks.items():
        count = int(np.count_nonzero(mask))
        loss_by_category[name] = {
            "point_count": count,
            "normalized_phase_mse": float(np.mean(phase_error[mask])) if count else None,
        }
    recall_precision: dict[str, Any] = {}
    first, second = _cycle_masks(direct_arrays["time"])
    for name, time_mask in (("cycle_1", first), ("cycle_2", second)):
        teacher = direct_arrays["phase"][time_mask] >= 0.5
        predicted = old_arrays["phase"][time_mask] >= 0.5
        true_positive = int(np.count_nonzero(teacher & predicted))
        predicted_positive = int(np.count_nonzero(predicted))
        teacher_positive = int(np.count_nonzero(teacher))
        recall_precision[name] = {
            "teacher_positive": teacher_positive,
            "predicted_positive": predicted_positive,
            "true_positive": true_positive,
            "recall": _safe_ratio(true_positive, teacher_positive),
            "precision": _safe_ratio(true_positive, predicted_positive),
        }
    time = torch.as_tensor(old_arrays["time"], dtype=torch.float64).reshape(-1, 1)
    waveform = physics.waveform(time).detach().cpu().numpy().reshape(-1, 1)
    potential = np.asarray(old_arrays["potential"], dtype=np.float64)
    lower = np.minimum(0.0, waveform)
    upper = np.maximum(0.0, waveform)
    violation = np.maximum(lower - potential, potential - upper) > tolerance
    teacher_event = masks["event_cycle_1"] | masks["event_cycle_2"]
    overlap = violation & teacher_event
    return {
        "phase_loss_by_teacher_topology_category": loss_by_category,
        "event_recall_precision": recall_precision,
        "phase_maximum": float(np.max(old_arrays["phase"])),
        "potential_violation_event_overlap": {
            "absolute_tolerance": float(tolerance),
            "violation_count": int(np.count_nonzero(violation)),
            "teacher_event_count": int(np.count_nonzero(teacher_event)),
            "overlap_count": int(np.count_nonzero(overlap)),
            "fraction_of_violations_on_teacher_event_support": _safe_ratio(
                int(np.count_nonzero(overlap)), int(np.count_nonzero(violation))
            ),
            "fraction_of_teacher_event_support_violating": _safe_ratio(
                int(np.count_nonzero(overlap)), int(np.count_nonzero(teacher_event))
            ),
        },
    }


def _summary(values: np.ndarray) -> dict[str, float]:
    finite = np.asarray(values, dtype=np.float64)
    if finite.size == 0 or not np.isfinite(finite).all():
        raise ValueError("LF1 latent diagnostic received invalid values")
    return {
        "minimum": float(np.min(finite)),
        "q05": float(np.quantile(finite, 0.05)),
        "median": float(np.median(finite)),
        "q95": float(np.quantile(finite, 0.95)),
        "maximum": float(np.max(finite)),
    }


def _old_latent_diagnostic(
    checkpoint_path: Path,
    direct_arrays: Mapping[str, np.ndarray],
) -> dict[str, Any]:
    try:
        model, _, _ = _load_model(checkpoint_path, device=torch.device("cpu"))
        active = np.argwhere(np.asarray(direct_arrays["phase"]) >= 0.5)
        if active.shape[0] == 0:
            raise ValueError("LF_ONLY direct carrier has no active event support")
        choose = np.linspace(0, active.shape[0] - 1, min(4096, active.shape[0]), dtype=np.int64)
        selected = active[choose]
        nx = int(np.asarray(direct_arrays["x"]).size)
        ti = selected[:, 0]
        cell = selected[:, 1]
        zi = cell // nx
        xi = cell % nx
        coordinates = torch.as_tensor(
            np.column_stack(
                (
                    np.asarray(direct_arrays["x"])[xi],
                    np.asarray(direct_arrays["z"])[zi],
                    np.asarray(direct_arrays["time"])[ti],
                )
            ),
            dtype=torch.float64,
        )
        with torch.no_grad():
            diagnostic = model.read_only_output_diagnostics(coordinates)
        latent = diagnostic.latents["phase"].detach().cpu().numpy().reshape(-1)
        jacobian = diagnostic.analytic_output_jacobians["phase"].detach().cpu().numpy().reshape(-1)
        prediction = diagnostic.output.fields[:, 2].detach().cpu().numpy().reshape(-1)
        return {
            "status": "AVAILABLE",
            "sample_count": int(coordinates.shape[0]),
            "phase_latent": _summary(latent),
            "phase_output_jacobian": _summary(jacobian),
            "predicted_phase": _summary(prediction),
        }
    except (FileNotFoundError, OSError) as exc:
        return {"status": "UNKNOWN_CHECKPOINT_UNAVAILABLE", "reason": str(exc)}


def _new_transform_diagnostic(dataset: MediumEventDataset) -> dict[str, Any]:
    latent_values = torch.tensor(
        [-1000.0, -100.0, -10.0, 0.0, 10.0, 100.0, 1000.0],
        dtype=torch.float64,
    )
    zeta_values = torch.tensor([0.0, 0.2, 0.5, 0.9, 1.0], dtype=torch.float64)
    latent_grid, zeta_grid = torch.meshgrid(latent_values, zeta_values, indexing="ij")
    latent = latent_grid.reshape(-1, 1).requires_grad_(True)
    zeta = zeta_grid.reshape(-1, 1).requires_grad_(True)
    fraction = range_preserving_exact_top_fraction(latent, zeta)
    derivative_h = torch.autograd.grad(
        fraction,
        latent,
        grad_outputs=torch.ones_like(fraction),
        create_graph=True,
        retain_graph=True,
    )[0]
    expected_h = fraction * (1.0 - fraction)
    moderate_h = torch.tensor([[-10.0], [0.0], [10.0]], dtype=torch.float64, requires_grad=True)
    top = torch.ones_like(moderate_h, requires_grad=True)
    top_fraction = range_preserving_exact_top_fraction(moderate_h, top)
    derivative_zeta = torch.autograd.grad(
        top_fraction, top, grad_outputs=torch.ones_like(top_fraction)
    )[0]
    expected_zeta = torch.exp(-moderate_h.detach())

    potential = dataset.fields["potential"]
    tt, zz, _ = np.meshgrid(dataset.time, dataset.z, dataset.x, indexing="ij")
    time_tensor = torch.as_tensor(dataset.time, dtype=torch.float64).reshape(-1, 1)
    waveform = dataset.physics.waveform(time_tensor).detach().cpu().numpy().reshape(-1, 1, 1)
    zeta_array = (zz - dataset.physics.z_min) / (dataset.physics.z_max - dataset.physics.z_min)
    nonzero_waveform = np.abs(waveform) > 1.0e-14
    ratio = np.divide(
        potential,
        waveform,
        out=np.zeros_like(potential),
        where=np.broadcast_to(nonzero_waveform, potential.shape),
    )
    tolerance = 1.0e-6
    admissible = (
        np.isfinite(ratio)
        & (ratio >= -tolerance)
        & (ratio <= 1.0 + tolerance)
    ) | ~np.broadcast_to(nonzero_waveform, ratio.shape)
    reconstructable = (
        np.broadcast_to(nonzero_waveform, ratio.shape)
        & (zeta_array < 1.0)
        & (ratio > 0.0)
        & (ratio < 1.0)
    )
    selected_ratio = ratio[reconstructable]
    selected_gap = (1.0 - zeta_array)[reconstructable]
    required_latent = np.log(selected_ratio * selected_gap / (1.0 - selected_ratio))
    sample_indices = np.linspace(
        0, required_latent.size - 1, min(65536, required_latent.size), dtype=np.int64
    )
    sample_h = torch.as_tensor(required_latent[sample_indices], dtype=torch.float64).reshape(-1, 1)
    sample_zeta = torch.as_tensor(
        zeta_array[reconstructable][sample_indices], dtype=torch.float64
    ).reshape(-1, 1)
    reconstructed = range_preserving_exact_top_fraction(sample_h, sample_zeta).numpy().reshape(-1)
    reconstruction_error = float(
        np.max(np.abs(reconstructed - selected_ratio[sample_indices]))
    )
    passed = (
        bool(torch.isfinite(fraction).all())
        and bool(torch.all((fraction >= 0.0) & (fraction <= 1.0)))
        and bool(torch.all(fraction[zeta.reshape(-1) == 1.0] == 1.0))
        and float(torch.max(torch.abs(derivative_h - expected_h)).detach()) <= 1.0e-12
        and float(torch.max(torch.abs(derivative_zeta - expected_zeta)).detach()) <= 1.0e-10
        and bool(np.all(admissible))
        and reconstruction_error <= 1.0e-12
    )
    return {
        "passed": passed,
        "synthetic_all_finite": bool(torch.isfinite(fraction).all()),
        "synthetic_range_minimum": float(torch.min(fraction).detach()),
        "synthetic_range_maximum": float(torch.max(fraction).detach()),
        "top_exact": bool(torch.all(fraction[zeta.reshape(-1) == 1.0] == 1.0)),
        "maximum_latent_derivative_error": float(torch.max(torch.abs(derivative_h - expected_h)).detach()),
        "maximum_top_zeta_derivative_error": float(torch.max(torch.abs(derivative_zeta - expected_zeta)).detach()),
        "medium_all_potential_ratios_admissible_with_tolerance": bool(np.all(admissible)),
        "medium_reconstructable_point_count": int(required_latent.size),
        "medium_nonfinite_required_latent_endpoint_count": int(
            np.count_nonzero(np.broadcast_to(nonzero_waveform, ratio.shape) & ~reconstructable)
        ),
        "required_latent": _summary(required_latent),
        "maximum_sampled_reconstruction_error": reconstruction_error,
    }


def qualify_cpu(*, output_path: Path) -> dict[str, Any]:
    contracts = load_contracts()
    identities = contract_identity()
    decision = contracts["decision"]
    source = contracts["data"]["training_source"]
    source_path = _verify_binding(source, "medium training source")
    diagnostic_inputs = contracts["data"]["local_cpu_diagnostic_inputs"]
    old_checkpoint = _verify_binding(diagnostic_inputs["old_b0_checkpoint"], "old B0 checkpoint")
    old_prediction = _verify_binding(diagnostic_inputs["old_b0_prediction"], "old B0 prediction")
    direct_prediction = _verify_binding(diagnostic_inputs["lf_only_prediction"], "LF_ONLY direct prediction")
    qualification_inputs = {
        label: {
            "path": binding["path"],
            "sha256": _sha256_path(_verify_binding(binding, label)),
        }
        for label, binding in decision["qualification_inputs"].items()
    }
    physics, _, _ = load_case_physics("FULL")
    result = __import__(
        "pinn_pcm_sci.phk_v21_benchmark", fromlist=["read_phk_v21_result"]
    ).read_phk_v21_result(source_path, physical=_physical_object())
    dataset = MediumEventDataset(result, physics=physics)
    _, old_arrays = read_prediction_carrier(old_prediction)
    _, direct_arrays = read_prediction_carrier(direct_prediction)
    tolerance = float(decision["potential_maximum_principle"]["absolute_tolerance"])
    pool_counts = dataset.pool_counts
    transform = _new_transform_diagnostic(dataset)
    report = {
        "schema_id": "phk-v23-lf1-cpu-qualification-v1",
        "task_id": TASK_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "contracts": identities,
        "bound_qualification_inputs": qualification_inputs,
        "old_lf0_event_exposure_by_cycle": _old_sampler_exposure(
            dataset,
            physics=physics,
            draws=int(decision["cpu_qualification"]["old_sampler_draws"]),
        ),
        "old_b0_prediction_diagnostics": _old_prediction_diagnostics(
            old_arrays,
            direct_arrays,
            physics=physics,
            tolerance=tolerance,
        ),
        "old_b0_event_point_phase_latent_and_jacobian": _old_latent_diagnostic(
            old_checkpoint, direct_arrays
        ),
        "new_medium_event_pool_counts": pool_counts,
        "new_transform_range_latent_reconstruction_and_derivative": transform,
        "fine_extra_fine_reference_read": False,
        "stress_fields_or_metrics_read": False,
    }
    passed = all(value > 0 for value in pool_counts.values()) and transform["passed"]
    report["status"] = (
        "LF1_CPU_QUALIFICATION_PASS"
        if passed
        else "LF1_CPU_OR_REPRESENTABILITY_BLOCKED"
    )
    report["gpu_execution_authorized_by_cpu_gate"] = bool(passed)
    written = _strict_write(output_path, report)
    report["output_path"] = written.relative_to(ROOT).as_posix()
    report["output_sha256"] = _sha256_path(written)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    report = qualify_cpu(output_path=arguments.output)
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    return 0 if report["gpu_execution_authorized_by_cpu_gate"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
