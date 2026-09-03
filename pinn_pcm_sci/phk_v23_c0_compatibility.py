"""CPU-only PHK-V2.3 C0 reference/strong-form compatibility audit.

This module never constructs or loads a neural model.  It reads only the
frozen nominal development carriers and the already-produced R1X E2 prediction
carrier, then emits compact statistics.  Stress references are deliberately
unreachable from this API.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.interpolate import RegularGridInterpolator
import torch

from .phk_benchmark import PhkGrid, _conductivity
from .phk_v21_benchmark import (
    PhkV21CaseSpec,
    PhkV21OracleResult,
    evaluate_phk_v21_event,
    load_phk_v21_physical,
    read_phk_v21_result,
)
from .phk_v22r_pinn import CollocationMixture, PhkCollocationSampler, PhkV22RPhysics
from .phk_v22r_prediction import read_prediction_carrier


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "configs" / "phk_v23" / (
    "c0_reference_discrete_strongform_compatibility_contract.json"
)
PROGRAM_V21 = ROOT / "configs" / "phk_v21" / "program_contract.json"
OBJECT_V21 = ROOT / "configs" / "phk_v21" / "object_numerical_contract.json"
PROGRAM_V2 = ROOT / "configs" / "phk_v2" / "program_contract.json"
OBJECT_V2 = ROOT / "configs" / "phk_v2" / "object_numerical_contract.json"

ALLOWED_OUTCOMES = (
    "C0_STRONGFORM_COMPATIBLE_LOW_FIDELITY_ALLOWED",
    "C0_READINESS_GATE_MISALIGNED",
    "C0_DISCRETE_STRONGFORM_MISMATCH_DOMINANT",
    "C0_OUTPUT_TRANSFORM_INADMISSIBLE",
    "C0_INCONCLUSIVE_EXACT_NATIVE_REPLAY_REQUIRED",
)


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _sha256_tensor(value: torch.Tensor) -> str:
    array = value.detach().to(device="cpu").contiguous().numpy()
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(json.dumps(list(array.shape), separators=(",", ":")).encode("ascii"))
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest().upper()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write_json_exclusive(path: Path, value: Mapping[str, Any]) -> None:
    exact = Path(path)
    exact.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(
        value,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    )
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(exact, flags, 0o644)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(raw)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        exact.unlink(missing_ok=True)
        raise


def _finite(value: Any) -> Any:
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("C0 statistic is non-finite")
        return float(value)
    if isinstance(value, dict):
        return {str(key): _finite(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_finite(item) for item in value]
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(f"unsupported C0 JSON value: {type(value)!r}")


def load_contract() -> dict[str, Any]:
    contract = _read_json(CONTRACT_PATH)
    if contract.get("schema_id") != (
        "phk-v23-c0-reference-discrete-strongform-compatibility-contract-v1"
    ):
        raise ValueError("unsupported C0 contract")
    if contract.get("status") != "FROZEN_BEFORE_SINGLE_CPU_DIAGNOSTIC":
        raise ValueError("C0 contract is not frozen before execution")
    if tuple(contract["machine_adjudication"]["allowed_primary_outcomes"]) != (
        ALLOWED_OUTCOMES
    ):
        raise ValueError("C0 outcome taxonomy drift")
    return contract


def assert_input_identities(contract: Mapping[str, Any]) -> dict[str, Any]:
    records: dict[str, Any] = {}
    inputs = contract["inputs"]
    for record in inputs["contracts_and_implementations"]:
        path = ROOT / record["path"]
        actual = _sha256_path(path)
        if actual != record["sha256"]:
            raise ValueError(f"C0 source identity mismatch: {record['path']}")
        records[record["path"]] = {"sha256": actual, "size_bytes": path.stat().st_size}
    for name, record in inputs["nominal_development_carriers"].items():
        path = ROOT / record["path"]
        if not path.is_file():
            raise FileNotFoundError(f"required nominal C0 input is absent: {name}")
        actual = _sha256_path(path)
        if actual != record["sha256"]:
            raise ValueError(f"C0 nominal carrier identity mismatch: {name}")
        records[name] = {"path": record["path"], "sha256": actual, "size_bytes": path.stat().st_size}
    record = inputs["e2_prediction"]
    path = ROOT / record["path"]
    actual = _sha256_path(path)
    if actual != record["sha256"]:
        raise ValueError("C0 E2 prediction identity mismatch")
    records["e2_prediction"] = {
        "path": record["path"],
        "sha256": actual,
        "size_bytes": path.stat().st_size,
    }
    return records


def _physical() -> tuple[Any, PhkV21CaseSpec, PhkV22RPhysics]:
    physical = load_phk_v21_physical(
        program_path=PROGRAM_V21,
        object_path=OBJECT_V21,
        legacy_program_path=PROGRAM_V2,
        legacy_object_path=OBJECT_V2,
    )
    case = PhkV21CaseSpec.nominal(physical)
    return physical, case, PhkV22RPhysics.from_contract(physical, case)


def build_readiness_pool(physics: PhkV22RPhysics) -> np.ndarray:
    sampler = PhkCollocationSampler(
        physics=physics,
        mixture=CollocationMixture(),
        seed=17,
    )
    pool = sampler.interior_uniform(
        2048,
        active_windows=4,
        dtype=torch.float64,
        device=torch.device("cpu"),
    ).detach()
    expected = load_contract()["inputs"]["r1x_readiness_pool"]
    if tuple(pool.shape) != (expected["count"], 3):
        raise ValueError("C0 readiness pool shape drift")
    if _sha256_tensor(pool) != expected["canonical_tensor_sha256"]:
        raise ValueError("C0 readiness pool byte identity drift")
    return pool.numpy().copy()


def initial_phase_analytic(
    x: np.ndarray, z: np.ndarray, physics: PhkV22RPhysics
) -> dict[str, np.ndarray]:
    dx = x - physics.initial_seed_center_x
    dz = z - physics.initial_seed_center_z
    gaussian = physics.initial_seed_excess * np.exp(
        -0.5
        * (
            (dx / physics.initial_seed_sigma_x) ** 2
            + (dz / physics.initial_seed_sigma_z) ** 2
        )
    )
    phase = physics.initial_phase_background + gaussian
    derivative_x = -gaussian * dx / physics.initial_seed_sigma_x**2
    derivative_z = -gaussian * dz / physics.initial_seed_sigma_z**2
    laplacian = gaussian * (
        dx**2 / physics.initial_seed_sigma_x**4
        - 1.0 / physics.initial_seed_sigma_x**2
        + dz**2 / physics.initial_seed_sigma_z**4
        - 1.0 / physics.initial_seed_sigma_z**2
    )
    return {
        "phase": phase.astype(np.float64),
        "dx": derivative_x.astype(np.float64),
        "dz": derivative_z.astype(np.float64),
        "laplacian": laplacian.astype(np.float64),
    }


def phase_components(
    *,
    temperature: np.ndarray,
    phase: np.ndarray,
    laplacian: np.ndarray,
    physics: PhkV22RPhysics,
) -> dict[str, np.ndarray]:
    barrier = (
        2.0
        * physics.barrier_scale
        * phase
        * (1.0 - phase)
        * (1.0 - 2.0 * phase)
    )
    thermal_tilt = (
        6.0
        * physics.thermal_drive
        * (physics.theta_transition - temperature)
        * phase
        * (1.0 - phase)
    )
    argument = np.clip(
        (temperature - physics.theta_transition) / physics.mobility_width,
        -50.0,
        50.0,
    )
    mobility = physics.mobility_cold + (
        physics.mobility_hot - physics.mobility_cold
    ) / (1.0 + np.exp(-argument))
    diffusion = physics.interface_width**2 * laplacian
    rhs = mobility * (diffusion - barrier - thermal_tilt)
    return {
        "diffusion": diffusion,
        "barrier_derivative": barrier,
        "thermal_tilt_derivative": thermal_tilt,
        "potential_derivative": barrier + thermal_tilt,
        "mobility": mobility,
        "kinetic_rhs": rhs,
    }


def cold_growth_threshold(
    phase: np.ndarray, laplacian: np.ndarray, physics: PhkV22RPhysics
) -> np.ndarray:
    denominator = np.maximum(phase * (1.0 - phase), 1.0e-15)
    return (
        physics.theta_transition
        + physics.barrier_scale * (1.0 - 2.0 * phase) / (3.0 * physics.thermal_drive)
        - physics.interface_width**2
        * laplacian
        / (6.0 * physics.thermal_drive * denominator)
    )


def _waveform(time_axis: np.ndarray, physics: PhkV22RPhysics) -> np.ndarray:
    local = np.remainder(time_axis - physics.time_start, physics.period)
    value = np.where(
        local < physics.ramp_up_end,
        physics.waveform_amplitude * local / physics.ramp_up_end,
        np.where(
            local <= physics.hold_end,
            physics.waveform_amplitude,
            np.where(
                local < physics.ramp_down_end,
                physics.waveform_amplitude
                * (physics.ramp_down_end - local)
                / (physics.ramp_down_end - physics.hold_end),
                0.0,
            ),
        ),
    )
    return np.where(
        (time_axis >= physics.time_start) & (time_axis < physics.time_end),
        value,
        0.0,
    ).astype(np.float64)


def _grid_axes(grid: PhkGrid) -> tuple[np.ndarray, np.ndarray]:
    return grid.x_centers.astype(np.float64), grid.z_centers.astype(np.float64)


def _field_laplacian(field: np.ndarray, grid: PhkGrid) -> np.ndarray:
    shaped = field.reshape(grid.nz, grid.nx)
    if grid.nx < 4 or grid.nz < 4:
        raise ValueError("C0 second-order one-sided Laplacian needs at least four cells per axis")

    def second(values: np.ndarray, *, spacing: float, axis: int) -> np.ndarray:
        moved = np.moveaxis(values, axis, -1)
        result = np.empty_like(moved)
        result[..., 1:-1] = (
            moved[..., 2:] - 2.0 * moved[..., 1:-1] + moved[..., :-2]
        ) / spacing**2
        result[..., 0] = (
            2.0 * moved[..., 0]
            - 5.0 * moved[..., 1]
            + 4.0 * moved[..., 2]
            - moved[..., 3]
        ) / spacing**2
        result[..., -1] = (
            2.0 * moved[..., -1]
            - 5.0 * moved[..., -2]
            + 4.0 * moved[..., -3]
            - moved[..., -4]
        ) / spacing**2
        return np.moveaxis(result, -1, axis)

    return (second(shaped, spacing=grid.dx, axis=1) + second(shaped, spacing=grid.dz, axis=0)).reshape(-1)


def _continuous_joule_density(
    potential: np.ndarray,
    temperature: np.ndarray,
    phase: np.ndarray,
    grid: PhkGrid,
    physics: PhkV22RPhysics,
) -> np.ndarray:
    shaped = potential.reshape(grid.nz, grid.nx)
    gradient_x = np.gradient(shaped, grid.dx, axis=1, edge_order=2)
    gradient_z = np.gradient(shaped, grid.dz, axis=0, edge_order=2)
    sigma = _conductivity(
        temperature,
        phase,
        phase_ratio=physics.conductivity_phase_ratio,
        temperature_gain=physics.conductivity_temperature_gain,
    )
    return sigma * (gradient_x.reshape(-1) ** 2 + gradient_z.reshape(-1) ** 2)


def _native_joule_density_from_saved_potential(
    potential: np.ndarray,
    conductivity: np.ndarray,
    applied_voltage: float,
    grid: PhkGrid,
    heater_width_fraction: float,
) -> np.ndarray:
    density_power = np.zeros(grid.cell_count, dtype=np.float64)
    first = grid.internal_first
    second = grid.internal_second
    resistance_first = grid.internal_half_distance / (
        conductivity[first] * grid.internal_area
    )
    resistance_second = grid.internal_half_distance / (
        conductivity[second] * grid.internal_area
    )
    current = (potential[first] - potential[second]) / (
        resistance_first + resistance_second
    )
    np.add.at(density_power, first, current * current * resistance_first)
    np.add.at(density_power, second, current * current * resistance_second)
    top = np.arange((grid.nz - 1) * grid.nx, grid.nz * grid.nx, dtype=np.int64)
    top_r = (0.5 * grid.dz) / (conductivity[top] * grid.dx)
    top_i = (applied_voltage - potential[top]) / top_r
    np.add.at(density_power, top, top_i * top_i * top_r)
    overlaps = grid.bottom_overlap(heater_width_fraction)
    bottom = np.flatnonzero(overlaps > 0.0)
    bottom_r = (0.5 * grid.dz) / (conductivity[bottom] * overlaps[bottom])
    bottom_i = potential[bottom] / bottom_r
    np.add.at(density_power, bottom, bottom_i * bottom_i * bottom_r)
    return density_power / grid.cell_volumes


def native_masks(grid: PhkGrid, *, layers: int = 2) -> dict[str, np.ndarray]:
    boundary = np.zeros((grid.nz, grid.nx), dtype=bool)
    boundary[:layers, :] = True
    boundary[-layers:, :] = True
    boundary[:, :layers] = True
    boundary[:, -layers:] = True
    strict = ~boundary
    return {"boundary_strip": boundary.reshape(-1), "strict_interior": strict.reshape(-1)}


def _roi_mask(grid: PhkGrid) -> np.ndarray:
    return (
        (np.abs(grid.cell_x) <= 0.55)
        & (grid.cell_z >= 0.0)
        & (grid.cell_z <= 0.55)
    )


def _window_mask(time_axis: np.ndarray, name: str) -> np.ndarray:
    bounds = {"W1": (0.0, 0.35), "W3": (1.25, 1.60)}[name]
    return (time_axis >= bounds[0]) & (time_axis <= bounds[1])


def _summary(value: np.ndarray) -> dict[str, float]:
    flat = np.asarray(value, dtype=np.float64).reshape(-1)
    if flat.size == 0 or not np.isfinite(flat).all():
        raise ValueError("C0 summary requires nonempty finite values")
    return {
        "min": float(np.min(flat)),
        "q05": float(np.quantile(flat, 0.05)),
        "q50": float(np.quantile(flat, 0.50)),
        "q95": float(np.quantile(flat, 0.95)),
        "abs_q95": float(np.quantile(np.abs(flat), 0.95)),
        "max": float(np.max(flat)),
        "rms": float(np.sqrt(np.mean(flat * flat))),
    }


def _sign_agreement(first: np.ndarray, second: np.ndarray, *, epsilon: float = 1.0e-12) -> float:
    a = np.asarray(first).reshape(-1)
    b = np.asarray(second).reshape(-1)
    active = (np.abs(a) > epsilon) | (np.abs(b) > epsilon)
    if not np.any(active):
        return 1.0
    return float(np.mean(np.sign(a[active]) == np.sign(b[active])))


def _interpolate(
    *,
    values: np.ndarray,
    time_axis: np.ndarray,
    grid: PhkGrid,
    points: np.ndarray,
) -> np.ndarray:
    x_axis, z_axis = _grid_axes(grid)
    shaped = values.reshape(time_axis.size, grid.nz, grid.nx)
    interpolation = RegularGridInterpolator(
        (time_axis, z_axis, x_axis),
        shaped,
        method="linear",
        bounds_error=False,
        fill_value=None,
    )
    return np.asarray(interpolation(points[:, (2, 1, 0)]), dtype=np.float64)


def readiness_metrics(
    *,
    time_axis: np.ndarray,
    potential: np.ndarray,
    temperature: np.ndarray,
    phase_for_joule: np.ndarray,
    grid: PhkGrid,
    physics: PhkV22RPhysics,
    pool: np.ndarray,
) -> dict[str, Any]:
    initial = initial_phase_analytic(grid.cell_x, grid.cell_z, physics)
    cold_threshold = cold_growth_threshold(initial["phase"], initial["laplacian"], physics)
    qj = np.empty_like(temperature)
    qj_native = np.empty_like(temperature)
    applied_voltage = _waveform(time_axis, physics)
    for index in range(time_axis.size):
        sigma = _conductivity(
            temperature[index],
            phase_for_joule[index],
            phase_ratio=physics.conductivity_phase_ratio,
            temperature_gain=physics.conductivity_temperature_gain,
        )
        qj[index] = _continuous_joule_density(
            potential[index],
            temperature[index],
            phase_for_joule[index],
            grid,
            physics,
        )
        qj_native[index] = _native_joule_density_from_saved_potential(
            potential[index],
            sigma,
            float(applied_voltage[index]),
            grid,
            physics.heater_width_fraction,
        )
    dense: dict[str, Any] = {}
    pooled: dict[str, Any] = {}
    roi = _roi_mask(grid)
    pool_roi = (np.abs(pool[:, 0]) <= 0.55) & (pool[:, 1] >= 0.0) & (pool[:, 1] <= 0.55)
    pool_temperature = _interpolate(
        values=temperature, time_axis=time_axis, grid=grid, points=pool
    )
    pool_qj = _interpolate(values=qj, time_axis=time_axis, grid=grid, points=pool)
    pool_qj_native = _interpolate(
        values=qj_native, time_axis=time_axis, grid=grid, points=pool
    )
    pool_lap = initial_phase_analytic(pool[:, 0], pool[:, 1], physics)["laplacian"]
    pool_phi0 = initial_phase_analytic(pool[:, 0], pool[:, 1], physics)["phase"]
    pool_threshold = cold_growth_threshold(pool_phi0, pool_lap, physics)
    for block_index, name in ((0, "W1"), (2, "W3")):
        times = _window_mask(time_axis, name)
        t_values = temperature[np.ix_(times, roi)].reshape(-1)
        q_values = qj[np.ix_(times, roi)].reshape(-1)
        q_native_values = qj_native[np.ix_(times, roi)].reshape(-1)
        thresholds = np.broadcast_to(cold_threshold[roi], (int(np.count_nonzero(times)), int(np.count_nonzero(roi)))).reshape(-1)
        dense[name] = {
            "sample_count": int(t_values.size),
            "thermal_activation_fraction": float(np.mean(t_values >= physics.theta_transition)),
            "positive_cold_kinetic_growth_fraction": float(np.mean(t_values > thresholds)),
            "joule_q95_roi": float(np.quantile(q_values, 0.95)),
            "joule_q95_roi_native_fvm_sensitivity": float(
                np.quantile(q_native_values, 0.95)
            ),
            "temperature_max": float(np.max(t_values)),
        }
        block = np.zeros(pool.shape[0], dtype=bool)
        block[block_index * 512 : (block_index + 1) * 512] = True
        selected = block & pool_roi
        pooled[name] = {
            "sample_count": int(np.count_nonzero(selected)),
            "thermal_activation_fraction": float(np.mean(pool_temperature[selected] >= physics.theta_transition)),
            "positive_cold_kinetic_growth_fraction": float(np.mean(pool_temperature[selected] > pool_threshold[selected])),
            "joule_q95_roi": float(np.quantile(pool_qj[selected], 0.95)),
            "joule_q95_roi_native_fvm_sensitivity": float(
                np.quantile(pool_qj_native[selected], 0.95)
            ),
            "temperature_max": float(np.max(pool_temperature[selected])),
        }
    def passed(record: Mapping[str, Mapping[str, float]]) -> bool:
        return all(
            record[name]["thermal_activation_fraction"] >= 0.02
            and record[name]["positive_cold_kinetic_growth_fraction"] >= 0.02
            and record[name]["joule_q95_roi"] > 1.0e-12
            for name in ("W1", "W3")
        )
    coverage = {
        name: {
            "positive_cold_growth_pool_minus_dense": float(
                pooled[name]["positive_cold_kinetic_growth_fraction"]
                - dense[name]["positive_cold_kinetic_growth_fraction"]
            ),
            "positive_cold_growth_pool_to_dense_ratio": (
                float(
                    pooled[name]["positive_cold_kinetic_growth_fraction"]
                    / dense[name]["positive_cold_kinetic_growth_fraction"]
                )
                if dense[name]["positive_cold_kinetic_growth_fraction"] > 0.0
                else None
            ),
            "thermal_activation_pool_minus_dense": float(
                pooled[name]["thermal_activation_fraction"]
                - dense[name]["thermal_activation_fraction"]
            ),
        }
        for name in ("W1", "W3")
    }
    return {
        "dense": dense,
        "sobol_pool": pooled,
        "dense_pass": passed(dense),
        "sobol_pool_pass": passed(pooled),
        "pool_miss": passed(dense) and not passed(pooled),
        "pool_coverage": coverage,
        "joule_identity": {
            "voting": "R1X_MATCHED_CONTINUOUS_FINITE_DIFFERENCE_PROXY",
            "sensitivity": "NATIVE_FVM_EDGE_DISSIPATION_RECONSTRUCTED_FROM_SAVED_POTENTIAL",
        },
        "cold_growth_critical_temperature_roi": _summary(cold_threshold[roi]),
        "pool_cell_center_extrapolation_fraction": float(
            np.mean(
                (pool[:, 0] < grid.x_centers[0])
                | (pool[:, 0] > grid.x_centers[-1])
                | (pool[:, 1] < grid.z_centers[0])
                | (pool[:, 1] > grid.z_centers[-1])
            )
        ),
    }


def initial_boundary_compatibility(
    result: PhkV21OracleResult, physics: PhkV22RPhysics
) -> dict[str, Any]:
    grid = result.grid
    initial = initial_phase_analytic(grid.cell_x, grid.cell_z, physics)
    native = np.asarray(grid.phase_laplacian @ initial["phase"], dtype=np.float64)
    difference = native - initial["laplacian"]
    masks = native_masks(grid)
    roi = _roi_mask(grid)
    bottom_seed = (
        (grid.cell_z <= grid.z_min + 2.0 * grid.dz)
        & (np.abs(grid.cell_x - physics.initial_seed_center_x) <= 2.0 * physics.initial_seed_sigma_x)
    )
    x_line = grid.x_centers
    z_line = grid.z_centers
    left = initial_phase_analytic(np.full_like(z_line, grid.x_min), z_line, physics)
    right = initial_phase_analytic(np.full_like(z_line, grid.x_max), z_line, physics)
    bottom = initial_phase_analytic(x_line, np.full_like(x_line, grid.z_min), physics)
    top = initial_phase_analytic(x_line, np.full_like(x_line, grid.z_max), physics)
    return {
        "normal_derivative": {
            "left": _summary(-left["dx"]),
            "right": _summary(right["dx"]),
            "bottom": _summary(-bottom["dz"]),
            "top": _summary(top["dz"]),
        },
        "analytic_laplacian": _summary(initial["laplacian"]),
        "native_fvm_neumann_laplacian": _summary(native),
        "native_minus_analytic": {
            "global": _summary(difference),
            "roi": _summary(difference[roi]),
            "bottom_seed": _summary(difference[bottom_seed]),
            "boundary_strip": _summary(difference[masks["boundary_strip"]]),
            "strict_interior": _summary(difference[masks["strict_interior"]]),
            "sign_agreement_global": _sign_agreement(native, initial["laplacian"]),
        },
    }


def _event_indices(result: PhkV21OracleResult) -> dict[str, int]:
    roi = _roi_mask(result.grid)
    active_fraction = np.mean(result.phase[:, roi] >= 0.5, axis=1)
    indices: dict[str, int] = {}
    for cycle in (1, 2):
        start = (cycle - 1) * result.case.period
        end = cycle * result.case.period
        in_cycle = np.flatnonzero(
            (result.time >= start)
            & (result.time <= end if cycle == 2 else result.time < end)
        )
        onset_candidates = in_cycle[active_fraction[in_cycle] >= 0.02]
        if onset_candidates.size == 0:
            raise ValueError(f"reference lacks C0 event onset in cycle {cycle}")
        onset = int(onset_candidates[0])
        peak = int(in_cycle[int(np.argmax(active_fraction[in_cycle]))])
        pre = max(int(in_cycle[0]), onset - 1)
        excursion = float(active_fraction[peak] - active_fraction[pre])
        recovery_target = float(active_fraction[peak] - 0.10 * excursion)
        recovery_candidates = in_cycle[
            (in_cycle > peak) & (active_fraction[in_cycle] <= recovery_target)
        ]
        if recovery_candidates.size == 0:
            raise ValueError(f"reference lacks C0 early recovery in cycle {cycle}")
        indices[f"cycle_{cycle}_pre_onset"] = pre
        indices[f"cycle_{cycle}_onset"] = onset
        indices[f"cycle_{cycle}_peak"] = peak
        indices[f"cycle_{cycle}_early_recovery"] = int(recovery_candidates[0])
    return indices


def _region_mechanism(
    *,
    derivative: np.ndarray,
    native_laplacian: np.ndarray,
    continuous_laplacian: np.ndarray,
    temperature: np.ndarray,
    phase: np.ndarray,
    mask: np.ndarray,
    physics: PhkV22RPhysics,
) -> dict[str, Any]:
    native = phase_components(
        temperature=temperature,
        phase=phase,
        laplacian=native_laplacian,
        physics=physics,
    )
    continuous = phase_components(
        temperature=temperature,
        phase=phase,
        laplacian=continuous_laplacian,
        physics=physics,
    )
    residual_native = derivative - native["kinetic_rhs"]
    residual_continuous = derivative - continuous["kinetic_rhs"]
    native_rhs_rms = max(
        float(np.sqrt(np.mean(native["kinetic_rhs"][mask] ** 2))), 1.0e-15
    )
    continuous_rhs_rms = max(
        float(np.sqrt(np.mean(continuous["kinetic_rhs"][mask] ** 2))), 1.0e-15
    )
    return {
        "sample_count": int(np.count_nonzero(mask)),
        "phase_time_difference": _summary(derivative[mask]),
        "epsilon2_laplacian_native": _summary(native["diffusion"][mask]),
        "epsilon2_laplacian_continuous": _summary(continuous["diffusion"][mask]),
        "barrier_derivative": _summary(native["barrier_derivative"][mask]),
        "thermal_tilt_derivative": _summary(native["thermal_tilt_derivative"][mask]),
        "mobility": _summary(native["mobility"][mask]),
        "kinetic_rhs_native": _summary(native["kinetic_rhs"][mask]),
        "kinetic_rhs_continuous": _summary(continuous["kinetic_rhs"][mask]),
        "saved_cadence_residual_native": _summary(residual_native[mask]),
        "saved_cadence_residual_continuous": _summary(residual_continuous[mask]),
        "derivative_native_rhs_sign_agreement": _sign_agreement(
            derivative[mask], native["kinetic_rhs"][mask]
        ),
        "native_continuous_rhs_sign_agreement": _sign_agreement(
            native["kinetic_rhs"][mask], continuous["kinetic_rhs"][mask]
        ),
        "native_continuous_rhs_relative_rms_difference": float(
            np.sqrt(np.mean((native["kinetic_rhs"][mask] - continuous["kinetic_rhs"][mask]) ** 2))
            / max(np.sqrt(np.mean(native["kinetic_rhs"][mask] ** 2)), 1.0e-15)
        ),
        "component_rms_to_rhs_rms": {
            "native_diffusion": float(
                np.sqrt(np.mean(native["diffusion"][mask] ** 2)) / native_rhs_rms
            ),
            "continuous_diffusion": float(
                np.sqrt(np.mean(continuous["diffusion"][mask] ** 2))
                / continuous_rhs_rms
            ),
            "barrier": float(
                np.sqrt(np.mean(native["barrier_derivative"][mask] ** 2))
                / native_rhs_rms
            ),
            "thermal_tilt": float(
                np.sqrt(np.mean(native["thermal_tilt_derivative"][mask] ** 2))
                / native_rhs_rms
            ),
        },
    }


def event_mechanism(
    result: PhkV21OracleResult, physics: PhkV22RPhysics
) -> dict[str, Any]:
    indices = _event_indices(result)
    roi = _roi_mask(result.grid)
    regions = native_masks(result.grid)
    records: dict[str, Any] = {}
    for label, index in indices.items():
        before = max(0, index - 1)
        delta = float(result.time[index] - result.time[before])
        if delta <= 0.0:
            after = min(result.time.size - 1, index + 1)
            delta = float(result.time[after] - result.time[index])
            derivative = (result.phase[after] - result.phase[index]) / delta
        else:
            derivative = (result.phase[index] - result.phase[before]) / delta
        phase = result.phase[index]
        temperature = result.temperature[index]
        native_lap = np.asarray(result.grid.phase_laplacian @ phase, dtype=np.float64)
        continuous_lap = _field_laplacian(phase, result.grid)
        internal_step = max(0, min(result.phase_residual_history.size - 1, int(round(result.time[index] / result.resolution.dt)) - 1))
        record: dict[str, Any] = {
            "saved_time": float(result.time[index]),
            "saved_time_index": int(index),
            "saved_cadence_dt": delta,
            "time_derivative_identity": "SAVED_CADENCE_BACKWARD_DIFFERENCE_NOT_EXACT_INTERNAL_STEP",
            "native_internal_scalar_phase_equation_residual_inf": float(result.phase_residual_history[internal_step]),
            "native_internal_scalar_residual_rate_floor": float(result.phase_residual_history[internal_step] / result.resolution.dt),
        }
        for region_name, region_mask in regions.items():
            mask = roi & region_mask
            record[region_name] = _region_mechanism(
                derivative=derivative,
                native_laplacian=native_lap,
                continuous_laplacian=continuous_lap,
                temperature=temperature,
                phase=phase,
                mask=mask,
                physics=physics,
            )
        boundary = record["boundary_strip"]
        strict = record["strict_interior"]
        record["boundary_sensitivity"] = {
            "continuous_residual_abs_q95_boundary_to_strict_ratio": float(
                boundary["saved_cadence_residual_continuous"]["abs_q95"]
                / max(
                    strict["saved_cadence_residual_continuous"]["abs_q95"],
                    1.0e-15,
                )
            ),
            "native_continuous_rhs_difference_boundary_to_strict_ratio": float(
                boundary["native_continuous_rhs_relative_rms_difference"]
                / max(strict["native_continuous_rhs_relative_rms_difference"], 1.0e-15)
            ),
        }
        records[label] = record
    return records


def _event_support_masks(
    result: PhkV21OracleResult,
) -> dict[str, np.ndarray]:
    roi = _roi_mask(result.grid)
    masks: dict[str, np.ndarray] = {}
    for name in ("W1", "W3"):
        masks[name] = (
            _window_mask(result.time, name)[:, None]
            & roi[None, :]
            & (result.phase >= 0.5)
        )
    return masks


def _envelope_record(
    value: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    mask: np.ndarray,
    *,
    scale: float | np.ndarray,
) -> dict[str, Any]:
    selected = mask & np.isfinite(value) & np.isfinite(lower) & np.isfinite(upper)
    if not np.any(selected):
        return {"sample_count": 0, "violation_fraction": 0.0, "q95_relative_excess": 0.0, "maximum_absolute_excess": 0.0}
    excess = np.maximum(lower - value, value - upper)
    positive = np.maximum(excess[selected], 0.0)
    if isinstance(scale, np.ndarray):
        local_scale = np.maximum(np.asarray(scale, dtype=np.float64)[selected], 1.0e-12)
        relative = positive / local_scale
    else:
        relative = positive / max(float(scale), 1.0e-12)
    return {
        "sample_count": int(np.count_nonzero(selected)),
        "violation_fraction": float(np.mean(positive > 1.0e-10)),
        "q95_relative_excess": float(np.quantile(relative, 0.95)),
        "maximum_absolute_excess": float(np.max(positive)),
    }


def output_transform_admissibility(
    result: PhkV21OracleResult, physics: PhkV22RPhysics
) -> dict[str, Any]:
    waveform = _waveform(result.time, physics)[:, None]
    z_fraction = (result.grid.cell_z - physics.z_min) / (physics.z_max - physics.z_min)
    startup = 1.0 - np.exp(-(result.time - physics.time_start) / 0.35)
    temperature_upper = 2.5 * startup[:, None] * (1.0 - z_fraction[None, :])
    support = _event_support_masks(result)
    all_points = np.ones_like(result.potential, dtype=bool)
    global_envelope = {
        "potential_legacy": _envelope_record(
            result.potential,
            np.zeros_like(result.potential),
            np.broadcast_to(waveform, result.potential.shape),
            all_points,
            scale=np.broadcast_to(np.maximum(waveform, 1.0e-12), result.potential.shape),
        ),
        "potential_e2_top_hard_lift": _envelope_record(
            result.potential,
            np.broadcast_to(waveform * z_fraction[None, :], result.potential.shape),
            np.broadcast_to(waveform, result.potential.shape),
            all_points,
            scale=np.broadcast_to(np.maximum(waveform, 1.0e-12), result.potential.shape),
        ),
        "temperature": _envelope_record(
            result.temperature,
            np.zeros_like(result.temperature),
            temperature_upper,
            all_points,
            scale=np.maximum(temperature_upper, 1.0e-12),
        ),
    }
    windows: dict[str, Any] = {}
    for name, mask in support.items():
        legacy = _envelope_record(
            result.potential,
            np.zeros_like(result.potential),
            np.broadcast_to(waveform, result.potential.shape),
            mask,
            scale=np.broadcast_to(np.maximum(waveform, 1.0e-12), result.potential.shape),
        )
        e2 = _envelope_record(
            result.potential,
            np.broadcast_to(waveform * z_fraction[None, :], result.potential.shape),
            np.broadcast_to(waveform, result.potential.shape),
            mask,
            scale=np.broadcast_to(np.maximum(waveform, 1.0e-12), result.potential.shape),
        )
        thermal = _envelope_record(
            result.temperature,
            np.zeros_like(result.temperature),
            temperature_upper,
            mask,
            scale=np.maximum(temperature_upper, 1.0e-12),
        )
        windows[name] = {
            "potential_legacy": legacy,
            "potential_e2_top_hard_lift": e2,
            "temperature": thermal,
        }
    valid_t = (startup[:, None] > 1.0e-12) & (temperature_upper > 1.0e-12)
    raw_temp_ratio = result.temperature[valid_t] / temperature_upper[valid_t]
    representable_temperature = (raw_temp_ratio > 0.0) & (raw_temp_ratio < 1.0)
    temp_ratio = raw_temp_ratio[representable_temperature]
    temp_latent = np.log(temp_ratio) - np.log1p(-temp_ratio)
    phi0 = initial_phase_analytic(result.grid.cell_x, result.grid.cell_z, physics)["phase"]
    valid_phase_time = startup > 1.0e-12
    raw_phase_values = result.phase[valid_phase_time]
    representable_phase = (raw_phase_values > 0.0) & (raw_phase_values < 1.0)
    phase_values = np.clip(raw_phase_values, 1.0e-15, 1.0 - 1.0e-15)
    phase_latent_all = (
        np.log(phase_values)
        - np.log1p(-phase_values)
        - (np.log(phi0) - np.log1p(-phi0))[None, :]
    ) / (8.0 * startup[valid_phase_time, None])
    phase_latent = phase_latent_all[representable_phase]
    max_fraction = max(windows[name]["potential_e2_top_hard_lift"]["violation_fraction"] for name in ("W1", "W3"))
    max_excess = max(windows[name]["potential_e2_top_hard_lift"]["q95_relative_excess"] for name in ("W1", "W3"))
    return {
        "global": global_envelope,
        "event_support": windows,
        "phase_hard_transform": {
            "initial_maximum_absolute_error": float(np.max(np.abs(result.phase[0] - phi0))),
            "strict_bound_violation_fraction": float(
                np.mean((result.phase <= 0.0) | (result.phase >= 1.0))
            ),
        },
        "required_temperature_latent": {
            **_summary(temp_latent),
            "defined_fraction": float(np.mean(representable_temperature)),
        },
        "required_phase_latent_non_voting": {
            **_summary(phase_latent),
            "defined_fraction": float(np.mean(representable_phase)),
        },
        "audited_e2_transform": "E2_TOP_DIRICHLET_HARD_LIFT_POTENTIAL_PLUS_LEGACY_TEMPERATURE",
        "legacy_potential_reported_non_voting_comparator": True,
        "e2_audited_violation_fraction_max": max_fraction,
        "e2_audited_q95_relative_excess_max": max_excess,
    }


def prediction_transform_integrity(
    *,
    time_axis: np.ndarray,
    potential: np.ndarray,
    temperature: np.ndarray,
    phase: np.ndarray,
    grid: PhkGrid,
    physics: PhkV22RPhysics,
) -> dict[str, Any]:
    waveform = _waveform(time_axis, physics)[:, None]
    z_fraction = (grid.cell_z - physics.z_min) / (physics.z_max - physics.z_min)
    startup = 1.0 - np.exp(-(time_axis - physics.time_start) / 0.35)
    temperature_upper = 2.5 * startup[:, None] * (1.0 - z_fraction[None, :])
    phi0 = initial_phase_analytic(grid.cell_x, grid.cell_z, physics)["phase"]
    lower_v = waveform * z_fraction[None, :]
    upper_v = np.broadcast_to(waveform, potential.shape)
    potential_excess = np.maximum(lower_v - potential, potential - upper_v)
    temperature_excess = np.maximum(-temperature, temperature - temperature_upper)
    record = {
        "identity": "E2_TOP_DIRICHLET_HARD_LIFT_OUTPUT_TRANSFORM_SELF_CHECK",
        "potential_maximum_absolute_excess": float(
            np.max(np.maximum(potential_excess, 0.0))
        ),
        "temperature_maximum_absolute_excess": float(
            np.max(np.maximum(temperature_excess, 0.0))
        ),
        "phase_initial_maximum_absolute_error": float(
            np.max(np.abs(phase[0] - phi0))
        ),
        "phase_strict_bound_violation_fraction": float(
            np.mean((phase <= 0.0) | (phase >= 1.0))
        ),
    }
    if (
        record["potential_maximum_absolute_excess"] > 1.0e-10
        or record["temperature_maximum_absolute_excess"] > 1.0e-10
        or record["phase_initial_maximum_absolute_error"] > 1.0e-10
        or record["phase_strict_bound_violation_fraction"] > 0.0
    ):
        raise ValueError("C0 E2 prediction violates its declared output transform")
    return record


def compatibility_floor(
    mechanisms: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    names = ("medium", "fine", "extra_fine", "medium_half_dt", "fine_exact_replay")
    if any(name not in mechanisms for name in names):
        return {"sufficient": False, "reason": "REQUIRED_RESOLUTION_SUMMARY_MISSING"}
    records: dict[str, Any] = {}
    ratios: list[float] = []
    sign_agreements: list[float] = []
    for label in mechanisms["extra_fine"]:
        values = {
            name: mechanisms[name][label]["strict_interior"]["saved_cadence_residual_continuous"]["rms"]
            for name in names
        }
        residual = abs(values["extra_fine"])
        space_floor = max(abs(values["medium"] - values["fine"]), abs(values["fine"] - values["extra_fine"]))
        time_floor = abs(values["medium"] - values["medium_half_dt"])
        replay_floor = abs(values["fine"] - values["fine_exact_replay"])
        native_floor = mechanisms["extra_fine"][label]["native_internal_scalar_residual_rate_floor"]
        floor = max(space_floor, time_floor, replay_floor, native_floor, 1.0e-12)
        ratio = residual / floor
        sign = mechanisms["extra_fine"][label]["strict_interior"]["native_continuous_rhs_sign_agreement"]
        ratios.append(float(ratio))
        sign_agreements.append(float(sign))
        records[label] = {
            "continuous_saved_residual_rms": residual,
            "space_floor": space_floor,
            "time_floor": time_floor,
            "exact_replay_floor": replay_floor,
            "native_internal_scalar_rate_floor": native_floor,
            "combined_floor": floor,
            "residual_to_floor_ratio": ratio,
            "native_continuous_rhs_sign_agreement": sign,
        }
    return {
        "sufficient": True,
        "saved_cadence_limitation": "NO_CELLWISE_INTERNAL_STEP_STATE_OR_RESIDUAL_IN_EXISTING_CARRIERS",
        "fine_exact_replay_limitation": "BITWISE_REPLAY_AT_SAME_SAVED_CADENCE_NOT_INTERNAL_STEP_FIELD_CARRIER",
        "records": records,
        "maximum_residual_to_floor_ratio": max(ratios),
        "minimum_native_continuous_rhs_sign_agreement": min(sign_agreements),
    }


def adjudicate(
    *,
    reference_event_pass: bool,
    reference_readiness: Mapping[str, Any],
    compatibility: Mapping[str, Any],
    output: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    rules = contract["machine_adjudication"]
    candidates: list[tuple[str, float]] = []
    output_rule = rules["output_inadmissible"]
    if bool(output["trigger_confirmed"]):
        score = float(output["trigger_normalized_evidence_ratio"])
        candidates.append(("C0_OUTPUT_TRANSFORM_INADMISSIBLE", score))
    if reference_event_pass and (
        not bool(reference_readiness["dense_pass"])
        or not bool(reference_readiness["sobol_pool_pass"])
    ):
        deficits = []
        for role in ("dense", "sobol_pool"):
            for window in ("W1", "W3"):
                item = reference_readiness[role][window]
                deficits.extend(
                    (
                        0.02 / max(float(item["thermal_activation_fraction"]), 1.0e-15),
                        0.02 / max(float(item["positive_cold_kinetic_growth_fraction"]), 1.0e-15),
                        1.0e-12 / max(float(item["joule_q95_roi"]), 1.0e-30),
                    )
                )
        candidates.append(("C0_READINESS_GATE_MISALIGNED", max(deficits)))
    compatibility_gray_zone = False
    if not bool(compatibility.get("sufficient")):
        if not candidates:
            primary = "C0_INCONCLUSIVE_EXACT_NATIVE_REPLAY_REQUIRED"
            return {
                "primary": primary,
                "secondary": None,
                "triggered_pathologies": [],
                "strongform_compatible_subverdict": False,
                "next_recommendation": rules["next_recommendation"][primary],
            }
    else:
        mismatch_rule = rules["discrete_strongform_mismatch"]
        ratio = float(compatibility["maximum_residual_to_floor_ratio"])
        sign = float(compatibility["minimum_native_continuous_rhs_sign_agreement"])
        if ratio >= float(mismatch_rule["minimum_residual_to_resolution_floor_ratio"]) and sign <= float(mismatch_rule["maximum_rhs_sign_agreement"]):
            score = min(
                ratio / float(mismatch_rule["minimum_residual_to_resolution_floor_ratio"]),
                float(mismatch_rule["maximum_rhs_sign_agreement"]) / max(sign, 1.0e-15),
            )
            candidates.append(("C0_DISCRETE_STRONGFORM_MISMATCH_DOMINANT", score))
        compatible_rule = rules["strongform_compatible"]
        compatibility_gray_zone = (
            ratio > float(compatible_rule["maximum_residual_to_resolution_floor_ratio"])
            and ratio < float(mismatch_rule["minimum_residual_to_resolution_floor_ratio"])
        )
    compatible_subverdict = False
    if bool(compatibility.get("sufficient")):
        compatible_rule = rules["strongform_compatible"]
        compatible_subverdict = (
            float(compatibility["maximum_residual_to_floor_ratio"])
            <= float(compatible_rule["maximum_residual_to_resolution_floor_ratio"])
            and float(compatibility["minimum_native_continuous_rhs_sign_agreement"])
            >= float(compatible_rule["minimum_rhs_sign_agreement"])
            and bool(reference_readiness["dense_pass"])
            and bool(reference_readiness["sobol_pool_pass"])
        )
    if candidates:
        if compatibility_gray_zone:
            candidates.append(
                (
                    "C0_INCONCLUSIVE_EXACT_NATIVE_REPLAY_REQUIRED",
                    float(compatibility["maximum_residual_to_floor_ratio"])
                    / float(rules["strongform_compatible"]["maximum_residual_to_resolution_floor_ratio"]),
                )
            )
        order = {name: index for index, name in enumerate(ALLOWED_OUTCOMES)}
        ranked = sorted(candidates, key=lambda item: (-item[1], order[item[0]]))
        primary = ranked[0][0]
        secondary = ranked[1][0] if len(ranked) > 1 else None
    elif bool(compatibility.get("sufficient")):
        if compatible_subverdict:
            primary = "C0_STRONGFORM_COMPATIBLE_LOW_FIDELITY_ALLOWED"
        else:
            primary = "C0_INCONCLUSIVE_EXACT_NATIVE_REPLAY_REQUIRED"
        secondary = None
    else:
        primary = "C0_INCONCLUSIVE_EXACT_NATIVE_REPLAY_REQUIRED"
        secondary = None
    return {
        "primary": primary,
        "secondary": secondary,
        "triggered_pathologies": [
            {"outcome": name, "trigger_normalized_evidence_ratio": score}
            for name, score in sorted(candidates, key=lambda item: (-item[1], item[0]))
        ],
        "strongform_compatible_subverdict": compatible_subverdict,
        "next_recommendation": rules["next_recommendation"][primary],
    }


def _git_text(*arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _current_git_head() -> str:
    return _git_text("rev-parse", "HEAD").lower()


def _git_blob_identity(source_commit: str, relative_path: str) -> tuple[str, str]:
    committed = _git_text("rev-parse", f"{source_commit}:{relative_path}").lower()
    working = _git_text(
        "hash-object", "--path", relative_path, relative_path
    ).lower()
    return committed, working


def _assert_execution_sources_match_commit(
    source_commit: str, *, expected_base_commit: str
) -> None:
    if _current_git_head() != source_commit:
        raise ValueError("C0 execution source commit does not match current HEAD")
    parent = _git_text("rev-parse", f"{source_commit}^").lower()
    if parent != expected_base_commit.lower():
        raise ValueError("C0 execution source commit is not the direct child of expected base")
    for relative_path in (
        "configs/phk_v23/c0_reference_discrete_strongform_compatibility_contract.json",
        "pinn_pcm_sci/phk_v23_c0_compatibility.py",
    ):
        committed, working = _git_blob_identity(source_commit, relative_path)
        if committed != working:
            raise ValueError(f"C0 execution source differs from commit: {relative_path}")


def run_c0(
    *,
    output_path: Path,
    run_id: str,
    source_commit: str,
    reference_role: str = "NOMINAL_LOCAL_DEVELOPMENT_DIAGNOSTIC_ONLY",
) -> dict[str, Any]:
    refuse_reference_role(reference_role)
    started = time.perf_counter()
    if not run_id or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]+", run_id):
        raise ValueError("invalid C0 run id")
    normalized_source = source_commit.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", normalized_source):
        raise ValueError("C0 source commit must be a full Git SHA")
    contract = load_contract()
    _assert_execution_sources_match_commit(
        normalized_source,
        expected_base_commit=str(contract["expected_base_commit"]),
    )
    identities_before = assert_input_identities(contract)
    physical, case, physics = _physical()
    pool = build_readiness_pool(physics)
    reference_summaries: dict[str, Any] = {}
    mechanisms: dict[str, Any] = {}
    extra_readiness: dict[str, Any] | None = None
    extra_output: dict[str, Any] | None = None
    extra_initial: dict[str, Any] | None = None
    extra_events_pass = False
    for name, identity in contract["inputs"]["nominal_development_carriers"].items():
        result = read_phk_v21_result(ROOT / identity["path"], physical=physical)
        event = evaluate_phk_v21_event(result, physical=physical)
        result_phi0 = initial_phase_analytic(
            result.grid.cell_x, result.grid.cell_z, physics
        )["phase"]
        readiness = readiness_metrics(
            time_axis=result.time,
            potential=result.potential,
            temperature=result.temperature,
            phase_for_joule=np.broadcast_to(result_phi0, result.phase.shape),
            grid=result.grid,
            physics=physics,
            pool=pool,
        )
        initial = initial_boundary_compatibility(result, physics)
        mechanism = event_mechanism(result, physics)
        output = output_transform_admissibility(result, physics)
        mechanisms[name] = mechanism
        reference_summaries[name] = {
            "resolution": {
                "nx": result.grid.nx,
                "nz": result.grid.nz,
                "native_dt": result.resolution.dt,
                "save_every": result.resolution.save_every,
                "saved_cadence": float(result.resolution.dt * result.resolution.save_every),
            },
            "event_pass": event.passed,
            "event_failures": list(event.failures),
            "readiness": readiness,
            "initial_boundary": initial,
            "event_mechanism": mechanism,
            "output_transform": output,
        }
        if name == "extra_fine":
            extra_readiness = readiness
            extra_output = output
            extra_initial = initial
            extra_events_pass = bool(event.passed)
    assert extra_readiness is not None and extra_output is not None and extra_initial is not None
    compatibility = compatibility_floor(mechanisms)
    fine_output = reference_summaries["fine"]["output_transform"]
    output_rule = contract["machine_adjudication"]["output_inadmissible"]
    fraction_threshold = float(output_rule["minimum_event_support_violation_fraction"])
    excess_threshold = float(output_rule["minimum_q95_relative_excess"])
    confirmed_by_window: dict[str, Any] = {}
    transform_candidates: list[dict[str, Any]] = []
    for window in ("W1", "W3"):
        confirmed_by_window[window] = {}
        for transform in output_rule["audited_event_support_transforms"]:
            fine_record = fine_output["event_support"][window][transform]
            extra_record = extra_output["event_support"][window][transform]
            score = min(
                float(fine_record["violation_fraction"]) / fraction_threshold,
                float(fine_record["q95_relative_excess"]) / excess_threshold,
                float(extra_record["violation_fraction"]) / fraction_threshold,
                float(extra_record["q95_relative_excess"]) / excess_threshold,
            )
            record = {
                "fine": fine_record,
                "extra_fine": extra_record,
                "both_thresholds_pass_in_both_resolutions": bool(score >= 1.0),
                "trigger_normalized_evidence_ratio": score,
            }
            confirmed_by_window[window][transform] = record
            if record["both_thresholds_pass_in_both_resolutions"]:
                transform_candidates.append(
                    {"window": window, "transform": transform, **record}
                )
    hard_tolerance = float(output_rule["hard_initial_or_bound_tolerance"])
    phase_hard_score = max(
        max(
            float(fine_output["phase_hard_transform"]["initial_maximum_absolute_error"]),
            float(extra_output["phase_hard_transform"]["initial_maximum_absolute_error"]),
        )
        / hard_tolerance,
        max(
            float(fine_output["phase_hard_transform"]["strict_bound_violation_fraction"]),
            float(extra_output["phase_hard_transform"]["strict_bound_violation_fraction"]),
        )
        / max(fraction_threshold, 1.0e-15),
    )
    phase_hard_confirmed = (
        float(fine_output["phase_hard_transform"]["initial_maximum_absolute_error"])
        > hard_tolerance
        and float(extra_output["phase_hard_transform"]["initial_maximum_absolute_error"])
        > hard_tolerance
    ) or (
        float(fine_output["phase_hard_transform"]["strict_bound_violation_fraction"])
        > 0.0
        and float(extra_output["phase_hard_transform"]["strict_bound_violation_fraction"])
        > 0.0
    )
    if phase_hard_confirmed:
        transform_candidates.append(
            {
                "window": "INITIAL_OR_ALL_TIMES",
                "transform": "phase_hard_ic_or_strict_bounds",
                "both_thresholds_pass_in_both_resolutions": True,
                "trigger_normalized_evidence_ratio": phase_hard_score,
            }
        )
    confirmed_output = {
        "trigger_confirmed": bool(transform_candidates),
        "trigger_normalized_evidence_ratio": (
            max(
                float(record["trigger_normalized_evidence_ratio"])
                for record in transform_candidates
            )
            if transform_candidates
            else 0.0
        ),
        "confirmed_transform_candidates": transform_candidates,
        "by_window": confirmed_by_window,
        "phase_hard_constraint_confirmed": phase_hard_confirmed,
        "confirmation_resolutions": ["fine", "extra_fine"],
    }
    e2_identity = contract["inputs"]["e2_prediction"]
    e2_metadata, e2 = read_prediction_carrier(ROOT / e2_identity["path"])
    e2_grid = PhkGrid.build(
        nx=e2["x"].size,
        nz=e2["z"].size,
        x_min=physics.x_min,
        x_max=physics.x_max,
        z_min=physics.z_min,
        z_max=physics.z_max,
    )
    if not np.array_equal(e2["x"], e2_grid.x_centers) or not np.array_equal(
        e2["z"], e2_grid.z_centers
    ):
        raise ValueError("C0 E2 prediction grid identity mismatch")
    phi0 = initial_phase_analytic(e2_grid.cell_x, e2_grid.cell_z, physics)["phase"]
    e2_readiness = readiness_metrics(
        time_axis=e2["time"],
        potential=e2["potential"],
        temperature=e2["temperature"],
        phase_for_joule=np.broadcast_to(phi0, e2["temperature"].shape),
        grid=e2_grid,
        physics=physics,
        pool=pool,
    )
    e2_transform_integrity = prediction_transform_integrity(
        time_axis=e2["time"],
        potential=e2["potential"],
        temperature=e2["temperature"],
        phase=e2["phase"],
        grid=e2_grid,
        physics=physics,
    )
    decision = adjudicate(
        reference_event_pass=extra_events_pass,
        reference_readiness=extra_readiness,
        compatibility=compatibility,
        output=confirmed_output,
        contract=contract,
    )
    identities_after = assert_input_identities(contract)
    if identities_before != identities_after:
        raise RuntimeError("C0 protected input identity changed during audit")
    result = _finite(
        {
            "schema_id": "phk-v23-c0-reference-discrete-strongform-compatibility-artifact-v1",
            "run_id": run_id,
            "task_id": contract["phase_id"],
            "status": "COMPLETE",
            "contract": {"path": str(CONTRACT_PATH.relative_to(ROOT)).replace("\\", "/"), "sha256": _sha256_path(CONTRACT_PATH)},
            "execution": {
                "device": "CPU",
                "dtype": "FLOAT64",
                "gpu_used": False,
                "gpu_hours": 0.0,
                "cloud_cost_cny": 0.0,
                "neural_checkpoint_loaded": False,
                "neural_model_constructed": False,
                "neural_forward_backward": False,
                "optimizer_constructed_or_stepped": False,
                "reference_solver_replayed": False,
                "stress_fields_or_metrics_read": False,
                "autodl": "RETAINED_BY_PRIOR_USER_OVERRIDE_NOT_TOUCHED_BY_C0",
                "wall_seconds": time.perf_counter() - started,
            },
            "source_identity": {
                "expected_base_commit": contract["expected_base_commit"],
                "execution_source_commit": normalized_source,
                "protected_inputs_before": identities_before,
                "protected_inputs_after_equal": True,
                "readiness_pool_sha256": contract["inputs"]["r1x_readiness_pool"]["canonical_tensor_sha256"],
            },
            "reference_role": "NOMINAL_LOCAL_DEVELOPMENT_DIAGNOSTIC_ONLY",
            "reference_resolutions": reference_summaries,
            "reference_readiness_qualification": extra_readiness,
            "readiness_pool_coverage_interpretation": (
                "REFERENCE_SUPPORT_CAPTURED"
                if extra_readiness["dense_pass"] and extra_readiness["sobol_pool_pass"]
                else "REFERENCE_POOL_MISS"
                if extra_readiness["dense_pass"] and not extra_readiness["sobol_pool_pass"]
                else "REFERENCE_PHYSICS_DOES_NOT_PASS_READINESS"
            ),
            "e2_prediction_contrast": {
                "metadata_schema_id": e2_metadata.get("schema_id"),
                "readiness": e2_readiness,
                "readiness_interpretation": (
                    "E2_LOCAL_DRIVE_PRESENT"
                    if e2_readiness["dense_pass"] and e2_readiness["sobol_pool_pass"]
                    else "E2_POOL_MISS"
                    if e2_readiness["dense_pass"] and not e2_readiness["sobol_pool_pass"]
                    else "E2_FIELD_LACKS_LOCAL_COLD_GROWTH_DRIVE"
                ),
                "output_transform_integrity": e2_transform_integrity,
            },
            "initial_boundary_compatibility_extra_fine": extra_initial,
            "event_aligned_mechanism_extra_fine": mechanisms["extra_fine"],
            "discrete_strongform_compatibility": compatibility,
            "output_transform_admissibility_extra_fine": extra_output,
            "output_transform_audit_confirmation": confirmed_output,
            "machine_adjudication": decision,
            "claim_boundary": "CPU_ONLY_NOMINAL_DEVELOPMENT_COMPATIBILITY_DIAGNOSTIC_NOT_METHOD_COMPETENCE_CONTINUUM_TRUTH_FORMAL_OOD_OR_STRESS_EVIDENCE",
            "stress_reference_status": "TWO_STRESS_REFERENCES_SEALED_UNREAD",
            "next_research_execution_authorized": False,
        }
    )
    _write_json_exclusive(output_path, result)
    return result


def refuse_reference_role(role: str) -> None:
    if role != "NOMINAL_LOCAL_DEVELOPMENT_DIAGNOSTIC_ONLY":
        raise PermissionError("C0 refuses every non-nominal reference role before I/O")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--device", default="cpu", choices=("cpu",))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = run_c0(
        output_path=args.output,
        run_id=args.run_id,
        source_commit=args.source_commit,
    )
    print(json.dumps({"status": result["status"], "outcome": result["machine_adjudication"]["primary"], "output": str(args.output.resolve())}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ALLOWED_OUTCOMES",
    "adjudicate",
    "build_readiness_pool",
    "cold_growth_threshold",
    "initial_phase_analytic",
    "load_contract",
    "main",
    "native_masks",
    "phase_components",
    "prediction_transform_integrity",
    "readiness_metrics",
    "refuse_reference_role",
    "run_c0",
]
