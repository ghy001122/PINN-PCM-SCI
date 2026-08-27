"""Independent finite-volume benchmark for the frozen PHK-V2 object.

The implementation is intentionally separate from every PINN residual and
training module.  It consumes the exact pre-result JSON contracts, uses a
cell-centred Cartesian finite-volume discretisation, and fails closed whenever
the frozen nonlinear or coupled tolerances are not met.

The small ``NON_SCIENTIFIC_TEST_FIXTURE`` resolution exists only so operator
and process tests can exercise the real numerical path quickly.  Scientific Q
intents must use :meth:`PhkResolution.from_contract`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from numpy.typing import NDArray
from scipy import sparse
from scipy.interpolate import RegularGridInterpolator
from scipy.sparse import linalg as sparse_linalg

from .phk_contract import PhkObjectContract, PhkProgramContract


FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _maximum_absolute(value: FloatArray) -> float:
    return float(np.max(np.abs(value))) if value.size else 0.0


@dataclass(frozen=True)
class PhkPhysicalContract:
    """Typed binding between the program and object contract bytes."""

    program: PhkProgramContract
    object: PhkObjectContract

    @classmethod
    def from_files(
        cls,
        *,
        program_path: Path,
        object_path: Path,
    ) -> "PhkPhysicalContract":
        program = PhkProgramContract.load(Path(program_path))
        physical = PhkObjectContract.load(Path(object_path), program=program)
        return cls(program=program, object=physical)

    @property
    def payload(self) -> Mapping[str, Any]:
        return self.object.payload

    @property
    def contract_id(self) -> str:
        return self.object.contract_id

    @property
    def coefficients(self) -> Mapping[str, Any]:
        return self.object.coefficients

    @property
    def coordinates(self) -> Mapping[str, Any]:
        return _mapping(self.payload["coordinates"], "coordinates")

    @property
    def nonlinear_solver(self) -> Mapping[str, Any]:
        return _mapping(self.payload["nonlinear_solver"], "nonlinear_solver")


class PhkControl(str, Enum):
    FULL = "FULL"
    ZERO_DRIVE = "ZERO_DRIVE"
    JOULE_GAIN_ZERO = "JOULE_GAIN_ZERO"
    CONDUCTIVITY_PHASE_RATIO_ONE = "CONDUCTIVITY_PHASE_RATIO_ONE"
    LATENT_RATIO_ZERO = "LATENT_RATIO_ZERO"
    HEATER_WIDTH_0_50 = "HEATER_WIDTH_0_50"
    INTERFACE_WIDTH_0_025 = "INTERFACE_WIDTH_0_025"
    EXACT_REPLAY_OF_Q_NOMINAL_FINE = "EXACT_REPLAY_OF_Q_NOMINAL_FINE"


@dataclass(frozen=True)
class PhkCaseSpec:
    control: PhkControl
    heater_width_fraction: float
    interface_width: float
    waveform_amplitude: float
    pulse_hold_end: float
    initial_phase_background: float
    constitutive_branch: str
    case_id: str

    @classmethod
    def qualification(
        cls,
        physical: PhkPhysicalContract,
        control: PhkControl,
    ) -> "PhkCaseSpec":
        coefficients = physical.coefficients
        geometry = _mapping(physical.payload["geometry"], "geometry")
        waveform = _mapping(physical.payload["waveform"], "waveform")
        heater = float(geometry["nominal_heater_width_fraction_of_total_x"])
        interface = float(coefficients["interface_width"])
        amplitude = float(waveform["amplitude"])
        if control is PhkControl.ZERO_DRIVE:
            amplitude = 0.0
        elif control is PhkControl.HEATER_WIDTH_0_50:
            heater = 0.50
        elif control is PhkControl.INTERFACE_WIDTH_0_025:
            interface = 0.025
        return cls(
            control=control,
            heater_width_fraction=heater,
            interface_width=interface,
            waveform_amplitude=amplitude,
            pulse_hold_end=float(waveform["hold_end"]),
            initial_phase_background=float(coefficients["initial_phase_background"]),
            constitutive_branch="NOMINAL",
            case_id=f"PHK_Q_{control.value}",
        )


@dataclass(frozen=True)
class PhkResolution:
    name: str
    nx: int
    nz: int
    dt: float
    time_end: float
    save_every: int
    evidence_identity: str

    @classmethod
    def from_contract(
        cls,
        physical: PhkPhysicalContract,
        name: str,
    ) -> "PhkResolution":
        resolutions = _mapping(physical.payload["resolutions"], "resolutions")
        if name not in resolutions:
            raise ValueError(f"unknown frozen resolution: {name}")
        item = _mapping(resolutions[name], f"resolutions.{name}")
        return cls(
            name=name,
            nx=int(item["nx"]),
            nz=int(item["nz"]),
            dt=float(item["dt"]),
            time_end=float(physical.coordinates["time_end"]),
            save_every=int(item["save_every"]),
            evidence_identity="PHK_V2_FROZEN_Q_RESOLUTION",
        )

    @classmethod
    def non_scientific_fixture(
        cls,
        *,
        nx: int,
        nz: int,
        dt: float,
        time_end: float,
        save_every: int,
    ) -> "PhkResolution":
        if min(nx, nz, save_every) <= 0 or dt <= 0.0 or time_end <= 0.0:
            raise ValueError("fixture resolution values must be positive")
        return cls(
            name="NON_SCIENTIFIC_TEST_FIXTURE",
            nx=int(nx),
            nz=int(nz),
            dt=float(dt),
            time_end=float(time_end),
            save_every=int(save_every),
            evidence_identity="NON_SCIENTIFIC_TEST_FIXTURE",
        )


def _neumann_laplacian(nx: int, nz: int, dx: float, dz: float) -> sparse.csr_matrix:
    rows: list[int] = []
    columns: list[int] = []
    data: list[float] = []

    def add_pair(first: int, second: int, coefficient: float) -> None:
        rows.extend((first, first, second, second))
        columns.extend((first, second, second, first))
        data.extend((-coefficient, coefficient, -coefficient, coefficient))

    for iz in range(nz):
        for ix in range(nx - 1):
            left = iz * nx + ix
            add_pair(left, left + 1, 1.0 / (dx * dx))
    for iz in range(nz - 1):
        for ix in range(nx):
            bottom = iz * nx + ix
            add_pair(bottom, bottom + nx, 1.0 / (dz * dz))
    return sparse.coo_matrix(
        (data, (rows, columns)), shape=(nx * nz, nx * nz), dtype=np.float64
    ).tocsr()


@dataclass(frozen=True)
class PhkGrid:
    nx: int
    nz: int
    x_min: float
    x_max: float
    z_min: float
    z_max: float
    dx: float
    dz: float
    cell_x: FloatArray
    cell_z: FloatArray
    cell_volumes: FloatArray
    internal_first: IntArray
    internal_second: IntArray
    internal_area: FloatArray
    internal_half_distance: FloatArray
    phase_laplacian: sparse.csr_matrix

    @property
    def cell_count(self) -> int:
        return self.nx * self.nz

    @property
    def x_centers(self) -> FloatArray:
        return self.x_min + (np.arange(self.nx, dtype=np.float64) + 0.5) * self.dx

    @property
    def z_centers(self) -> FloatArray:
        return self.z_min + (np.arange(self.nz, dtype=np.float64) + 0.5) * self.dz

    @classmethod
    def build(
        cls,
        *,
        nx: int,
        nz: int,
        x_min: float,
        x_max: float,
        z_min: float,
        z_max: float,
    ) -> "PhkGrid":
        if nx <= 1 or nz <= 1 or not x_max > x_min or not z_max > z_min:
            raise ValueError("invalid PHK Cartesian grid")
        dx = (float(x_max) - float(x_min)) / nx
        dz = (float(z_max) - float(z_min)) / nz
        x_axis = float(x_min) + (np.arange(nx, dtype=np.float64) + 0.5) * dx
        z_axis = float(z_min) + (np.arange(nz, dtype=np.float64) + 0.5) * dz
        x_mesh, z_mesh = np.meshgrid(x_axis, z_axis, indexing="xy")

        first: list[int] = []
        second: list[int] = []
        area: list[float] = []
        half_distance: list[float] = []
        for iz in range(nz):
            for ix in range(nx - 1):
                cell = iz * nx + ix
                first.append(cell)
                second.append(cell + 1)
                area.append(dz)
                half_distance.append(0.5 * dx)
        for iz in range(nz - 1):
            for ix in range(nx):
                cell = iz * nx + ix
                first.append(cell)
                second.append(cell + nx)
                area.append(dx)
                half_distance.append(0.5 * dz)

        return cls(
            nx=nx,
            nz=nz,
            x_min=float(x_min),
            x_max=float(x_max),
            z_min=float(z_min),
            z_max=float(z_max),
            dx=dx,
            dz=dz,
            cell_x=x_mesh.reshape(-1).astype(np.float64),
            cell_z=z_mesh.reshape(-1).astype(np.float64),
            cell_volumes=np.full(nx * nz, dx * dz, dtype=np.float64),
            internal_first=np.asarray(first, dtype=np.int64),
            internal_second=np.asarray(second, dtype=np.int64),
            internal_area=np.asarray(area, dtype=np.float64),
            internal_half_distance=np.asarray(half_distance, dtype=np.float64),
            phase_laplacian=_neumann_laplacian(nx, nz, dx, dz),
        )

    def bottom_overlap(self, heater_width_fraction: float) -> FloatArray:
        if not 0.0 < heater_width_fraction <= 1.0:
            raise ValueError("heater_width_fraction must be in (0, 1]")
        total_width = self.x_max - self.x_min
        half_width = 0.5 * total_width * heater_width_fraction
        left = -half_width
        right = half_width
        cell_left = self.x_centers - 0.5 * self.dx
        cell_right = self.x_centers + 0.5 * self.dx
        return np.maximum(0.0, np.minimum(cell_right, right) - np.maximum(cell_left, left))

    def thermal_laplacian(self, biot: float) -> sparse.csr_matrix:
        matrix = self.phase_laplacian.tolil(copy=True)
        volume = self.dx * self.dz
        top_coefficient = 2.0 / (self.dz * self.dz)
        for ix in range(self.nx):
            matrix[(self.nz - 1) * self.nx + ix, (self.nz - 1) * self.nx + ix] -= top_coefficient
            matrix[ix, ix] -= biot * self.dx / volume
        side_coefficient = biot * self.dz / volume
        for iz in range(self.nz):
            left = iz * self.nx
            right = left + self.nx - 1
            matrix[left, left] -= side_coefficient
            matrix[right, right] -= side_coefficient
        return matrix.tocsr()


@dataclass(frozen=True)
class PhkElectricResult:
    potential: FloatArray
    joule_density: FloatArray
    top_current: float
    bottom_current: float
    current_balance_relative: float
    joule_power_total: float
    linear_residual_scaled: float


def _conductance_matrix(
    grid: PhkGrid,
    conductivity: FloatArray,
    heater_width_fraction: float,
) -> tuple[sparse.csr_matrix, FloatArray, FloatArray, FloatArray]:
    if conductivity.shape != (grid.cell_count,) or not np.isfinite(conductivity).all():
        raise ValueError("conductivity must be a finite cell array")
    if np.any(conductivity <= 0.0):
        raise ValueError("conductivity must be positive")
    first = grid.internal_first
    second = grid.internal_second
    resistance_first = grid.internal_half_distance / (
        conductivity[first] * grid.internal_area
    )
    resistance_second = grid.internal_half_distance / (
        conductivity[second] * grid.internal_area
    )
    conductance = 1.0 / (resistance_first + resistance_second)

    rows = np.concatenate((first, first, second, second))
    columns = np.concatenate((first, second, second, first))
    data = np.concatenate((conductance, -conductance, conductance, -conductance))
    matrix = sparse.coo_matrix(
        (data, (rows, columns)),
        shape=(grid.cell_count, grid.cell_count),
        dtype=np.float64,
    ).tolil()

    top_cells = np.arange((grid.nz - 1) * grid.nx, grid.nz * grid.nx, dtype=np.int64)
    top_resistance = (0.5 * grid.dz) / (conductivity[top_cells] * grid.dx)
    top_conductance = 1.0 / top_resistance
    for cell, value in zip(top_cells, top_conductance, strict=True):
        matrix[cell, cell] += value

    bottom_cells = np.arange(grid.nx, dtype=np.int64)
    overlaps = grid.bottom_overlap(heater_width_fraction)
    active = overlaps > 0.0
    bottom_cells = bottom_cells[active]
    bottom_resistance = (0.5 * grid.dz) / (
        conductivity[bottom_cells] * overlaps[active]
    )
    bottom_conductance = 1.0 / bottom_resistance
    for cell, value in zip(bottom_cells, bottom_conductance, strict=True):
        matrix[cell, cell] += value
    return matrix.tocsr(), top_conductance, bottom_cells, bottom_conductance


def solve_electric_field(
    *,
    grid: PhkGrid,
    conductivity: FloatArray,
    applied_voltage: float,
    heater_width_fraction: float,
) -> PhkElectricResult:
    matrix, top_conductance, bottom_cells, bottom_conductance = _conductance_matrix(
        grid, np.asarray(conductivity, dtype=np.float64), heater_width_fraction
    )
    top_cells = np.arange((grid.nz - 1) * grid.nx, grid.nz * grid.nx, dtype=np.int64)
    rhs = np.zeros(grid.cell_count, dtype=np.float64)
    rhs[top_cells] = top_conductance * float(applied_voltage)
    potential = sparse_linalg.spsolve(matrix, rhs).astype(np.float64)
    linear_residual = _maximum_absolute(matrix @ potential - rhs) / max(
        1.0, _maximum_absolute(rhs)
    )

    top_current = float(np.sum(top_conductance * (float(applied_voltage) - potential[top_cells])))
    bottom_current = float(np.sum(bottom_conductance * potential[bottom_cells]))
    current_balance = abs(top_current - bottom_current) / max(
        abs(top_current), abs(bottom_current), 1.0e-14
    )

    density_power = np.zeros(grid.cell_count, dtype=np.float64)
    first = grid.internal_first
    second = grid.internal_second
    half = grid.internal_half_distance
    area = grid.internal_area
    resistance_first = half / (conductivity[first] * area)
    resistance_second = half / (conductivity[second] * area)
    face_current = (potential[first] - potential[second]) / (
        resistance_first + resistance_second
    )
    np.add.at(density_power, first, face_current * face_current * resistance_first)
    np.add.at(density_power, second, face_current * face_current * resistance_second)

    top_resistance = 1.0 / top_conductance
    top_face_current = (float(applied_voltage) - potential[top_cells]) / top_resistance
    np.add.at(density_power, top_cells, top_face_current * top_face_current * top_resistance)
    bottom_resistance = 1.0 / bottom_conductance
    bottom_face_current = potential[bottom_cells] / bottom_resistance
    np.add.at(
        density_power,
        bottom_cells,
        bottom_face_current * bottom_face_current * bottom_resistance,
    )
    joule_power_total = float(np.sum(density_power))
    joule_density = density_power / grid.cell_volumes
    return PhkElectricResult(
        potential=potential,
        joule_density=joule_density,
        top_current=top_current,
        bottom_current=bottom_current,
        current_balance_relative=current_balance,
        joule_power_total=joule_power_total,
        linear_residual_scaled=linear_residual,
    )


@dataclass(frozen=True)
class PhkOracleResult:
    physical_contract_id: str
    program_contract_sha256: str
    object_contract_sha256: str
    case: PhkCaseSpec
    resolution: PhkResolution
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

    @classmethod
    def synthetic_for_test(
        cls,
        *,
        physical: PhkPhysicalContract,
        grid: PhkGrid,
        time: FloatArray,
        potential: FloatArray,
        temperature: FloatArray,
        phase: FloatArray,
    ) -> "PhkOracleResult":
        time_array = np.asarray(time, dtype=np.float64)
        shape = (time_array.size, grid.cell_count)
        for name, array in (
            ("potential", potential),
            ("temperature", temperature),
            ("phase", phase),
        ):
            if np.asarray(array).shape != shape:
                raise ValueError(f"synthetic {name} has wrong shape")
        zeros = np.zeros(time_array.size, dtype=np.float64)
        resolution = PhkResolution.non_scientific_fixture(
            nx=grid.nx,
            nz=grid.nz,
            dt=float(time_array[1] - time_array[0]) if time_array.size > 1 else 1.0,
            time_end=float(time_array[-1]) if time_array[-1] > 0.0 else 1.0,
            save_every=1,
        )
        return cls(
            physical_contract_id=physical.contract_id,
            program_contract_sha256=physical.program.sha256,
            object_contract_sha256=physical.object.sha256,
            case=PhkCaseSpec.qualification(physical, PhkControl.FULL),
            resolution=resolution,
            grid=grid,
            time=time_array,
            potential=np.asarray(potential, dtype=np.float64),
            temperature=np.asarray(temperature, dtype=np.float64),
            phase=np.asarray(phase, dtype=np.float64),
            top_current=zeros,
            bottom_current=zeros,
            joule_power=zeros,
            current_balance_history=zeros,
            thermal_residual_history=zeros,
            phase_residual_history=zeros,
            coupled_change_history=zeros,
            linear_residual_history=zeros,
            solver_statistics={},
            evidence_identity="NON_SCIENTIFIC_TEST_FIXTURE",
        )


def write_phk_result(path: Path, result: PhkOracleResult) -> None:
    """Write one immutable, identity-bound PHK oracle carrier."""

    exact = Path(path)
    metadata = {
        "schema_id": "phk-v2-oracle-result-npz-v1",
        "physical_contract_id": result.physical_contract_id,
        "program_contract_sha256": result.program_contract_sha256,
        "object_contract_sha256": result.object_contract_sha256,
        "case": asdict(result.case),
        "resolution": asdict(result.resolution),
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


def read_phk_result(
    path: Path,
    *,
    physical: PhkPhysicalContract,
) -> PhkOracleResult:
    """Load a PHK carrier only after exact contract and mesh validation."""

    exact = Path(path)
    required = {
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
    try:
        with np.load(exact, allow_pickle=False) as archive:
            if set(archive.files) != required:
                raise ValueError("PHK result contains missing or unknown arrays")
            metadata = json.loads(str(archive["metadata_json"].item()))
            arrays = {
                name: np.asarray(archive[name], dtype=np.float64).copy()
                for name in required - {"metadata_json"}
            }
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        raise ValueError(f"invalid PHK result carrier: {exact}") from exc
    if not isinstance(metadata, dict) or metadata.get("schema_id") != "phk-v2-oracle-result-npz-v1":
        raise ValueError("unsupported PHK result schema")
    expected_identity = {
        "physical_contract_id": physical.contract_id,
        "program_contract_sha256": physical.program.sha256,
        "object_contract_sha256": physical.object.sha256,
    }
    for key, expected in expected_identity.items():
        if metadata.get(key) != expected:
            raise ValueError(f"PHK result {key} mismatch")
    case_payload = metadata.get("case")
    resolution_payload = metadata.get("resolution")
    if not isinstance(case_payload, dict) or not isinstance(resolution_payload, dict):
        raise ValueError("PHK result lacks case or resolution identity")
    try:
        case = PhkCaseSpec(
            **{**case_payload, "control": PhkControl(case_payload["control"])}
        )
        resolution = PhkResolution(**resolution_payload)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid PHK result case or resolution identity") from exc
    coordinates = physical.coordinates
    grid = PhkGrid.build(
        nx=resolution.nx,
        nz=resolution.nz,
        x_min=float(coordinates["x_min"]),
        x_max=float(coordinates["x_max"]),
        z_min=float(coordinates["z_min"]),
        z_max=float(coordinates["z_max"]),
    )
    for name, expected in (
        ("x", grid.cell_x),
        ("z", grid.cell_z),
        ("cell_volumes", grid.cell_volumes),
    ):
        if not np.array_equal(arrays[name], expected):
            raise ValueError(f"PHK result mesh array mismatch: {name}")
    time_array = arrays["time"]
    field_shape = (time_array.size, grid.cell_count)
    if time_array.ndim != 1 or np.any(np.diff(time_array) <= 0.0):
        raise ValueError("PHK result time axis is invalid")
    for name in ("potential", "temperature", "phase"):
        if arrays[name].shape != field_shape:
            raise ValueError(f"PHK result field shape mismatch: {name}")
    for name in ("top_current", "bottom_current", "joule_power"):
        if arrays[name].shape != (time_array.size,):
            raise ValueError(f"PHK result trace shape mismatch: {name}")
    numeric_arrays = tuple(arrays.values())
    if not all(np.isfinite(array).all() for array in numeric_arrays):
        raise ValueError("PHK result carrier contains non-finite values")
    statistics = metadata.get("solver_statistics")
    if not isinstance(statistics, dict):
        raise ValueError("PHK result lacks solver statistics")
    return PhkOracleResult(
        physical_contract_id=physical.contract_id,
        program_contract_sha256=physical.program.sha256,
        object_contract_sha256=physical.object.sha256,
        case=case,
        resolution=resolution,
        grid=grid,
        time=time_array,
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


def _phase_free_energy_derivatives(
    phase: FloatArray,
    temperature: FloatArray,
    *,
    barrier: float,
    thermal_drive: float,
    transition_temperature: float,
) -> tuple[FloatArray, FloatArray]:
    delta = transition_temperature - temperature
    first = (
        2.0 * barrier * phase * (1.0 - phase) * (1.0 - 2.0 * phase)
        + 6.0 * thermal_drive * delta * phase * (1.0 - phase)
    )
    second = (
        2.0 * barrier * (1.0 - 6.0 * phase + 6.0 * phase * phase)
        + 6.0 * thermal_drive * delta * (1.0 - 2.0 * phase)
    )
    return first, second


def _mobility(temperature: FloatArray, coefficients: Mapping[str, Any]) -> FloatArray:
    cold = float(coefficients["mobility_cold"])
    hot = float(coefficients["mobility_hot"])
    width = float(coefficients["mobility_width"])
    transition = float(coefficients["theta_transition"])
    argument = np.clip((temperature - transition) / width, -50.0, 50.0)
    return cold + (hot - cold) / (1.0 + np.exp(-argument))


def _phase_residual_and_jacobian(
    phase: FloatArray,
    *,
    phase_old: FloatArray,
    temperature: FloatArray,
    grid: PhkGrid,
    dt: float,
    coefficients: Mapping[str, Any],
    interface_width: float,
) -> tuple[FloatArray, sparse.csr_matrix]:
    mobility = _mobility(temperature, coefficients)
    first, second = _phase_free_energy_derivatives(
        phase,
        temperature,
        barrier=float(coefficients["barrier_scale"]),
        thermal_drive=float(coefficients["thermal_drive"]),
        transition_temperature=float(coefficients["theta_transition"]),
    )
    residual = (
        phase
        - phase_old
        - dt * mobility * (interface_width * interface_width * (grid.phase_laplacian @ phase) - first)
    )
    jacobian = (
        sparse.eye(grid.cell_count, format="csr")
        - dt
        * sparse.diags(mobility * interface_width * interface_width)
        @ grid.phase_laplacian
        + dt * sparse.diags(mobility * second)
    )
    return residual.astype(np.float64), jacobian.tocsr()


def _solve_phase_newton(
    *,
    phase_old: FloatArray,
    initial_guess: FloatArray,
    temperature: FloatArray,
    grid: PhkGrid,
    dt: float,
    coefficients: Mapping[str, Any],
    interface_width: float,
    solver: Mapping[str, Any],
    lower_bound: float,
    upper_bound: float,
) -> tuple[FloatArray, int, int, float]:
    phase = np.asarray(initial_guess, dtype=np.float64).copy()
    tolerance = float(solver["transport_newton_residual_tolerance"])
    maximum_iterations = int(solver["transport_newton_max_iterations"])
    initial_step = float(solver["newton_initial_step"])
    reduction = float(solver["line_search_reduction"])
    minimum_step = float(solver["line_search_min_step"])
    linear_solves = 0
    for iteration in range(maximum_iterations + 1):
        residual, jacobian = _phase_residual_and_jacobian(
            phase,
            phase_old=phase_old,
            temperature=temperature,
            grid=grid,
            dt=dt,
            coefficients=coefficients,
            interface_width=interface_width,
        )
        norm = _maximum_absolute(residual)
        if norm <= tolerance:
            return phase, iteration, linear_solves, norm
        if iteration == maximum_iterations:
            break
        update = sparse_linalg.spsolve(jacobian, -residual).astype(np.float64)
        linear_solves += 1
        step = initial_step
        accepted = False
        while step >= minimum_step:
            candidate = phase + step * update
            if np.all(candidate >= lower_bound) and np.all(candidate <= upper_bound):
                candidate_residual, _ = _phase_residual_and_jacobian(
                    candidate,
                    phase_old=phase_old,
                    temperature=temperature,
                    grid=grid,
                    dt=dt,
                    coefficients=coefficients,
                    interface_width=interface_width,
                )
                if _maximum_absolute(candidate_residual) < norm:
                    phase = candidate
                    accepted = True
                    break
            step *= reduction
        if not accepted:
            raise RuntimeError("PHK phase Newton line search reached its frozen minimum step")
    raise RuntimeError("PHK phase Newton exceeded its frozen iteration limit")


def _conductivity(
    temperature: FloatArray,
    phase: FloatArray,
    *,
    phase_ratio: float,
    temperature_gain: float,
) -> FloatArray:
    smooth_phase = phase * phase * (3.0 - 2.0 * phase)
    return np.exp(math.log(phase_ratio) * smooth_phase + temperature_gain * temperature)


def _initial_phase(grid: PhkGrid, coefficients: Mapping[str, Any], background: float) -> FloatArray:
    exponent = -0.5 * (
        ((grid.cell_x - float(coefficients["initial_seed_center_x"])) / float(coefficients["initial_seed_sigma_x"])) ** 2
        + ((grid.cell_z - float(coefficients["initial_seed_center_z"])) / float(coefficients["initial_seed_sigma_z"])) ** 2
    )
    return background + float(coefficients["initial_seed_excess"]) * np.exp(exponent)


@dataclass
class _SolverCounters:
    time_steps: int = 0
    coupled_blocks: int = 0
    electric_linear_solves: int = 0
    thermal_linear_solves: int = 0
    phase_linear_solves: int = 0
    phase_newton_iterations: int = 0
    final_residual_evaluations: int = 0


class PhkOracleCase:
    """Frozen independent CPU finite-volume qualification case."""

    def __init__(
        self,
        *,
        physical: PhkPhysicalContract,
        case: PhkCaseSpec,
        resolution: PhkResolution,
        allow_non_scientific_fixture: bool = False,
    ) -> None:
        if (
            resolution.evidence_identity == "NON_SCIENTIFIC_TEST_FIXTURE"
            and not allow_non_scientific_fixture
        ):
            raise ValueError("non-scientific fixture requires explicit opt-in")
        if (
            resolution.evidence_identity != "NON_SCIENTIFIC_TEST_FIXTURE"
            and resolution.evidence_identity != "PHK_V2_FROZEN_Q_RESOLUTION"
        ):
            raise ValueError("unknown resolution evidence identity")
        self.physical = physical
        self.case = case
        self.resolution = resolution

    def _waveform(self, time_value: float) -> float:
        waveform = _mapping(self.physical.payload["waveform"], "waveform")
        coordinates = self.physical.coordinates
        if time_value < float(coordinates["time_start"]) or time_value >= self.resolution.time_end:
            return 0.0
        period = float(coordinates["time_period"])
        phase = time_value % period
        amplitude = self.case.waveform_amplitude
        rise = float(waveform["ramp_up_end"])
        hold = self.case.pulse_hold_end
        fall = float(waveform["ramp_down_end"])
        if phase < rise:
            return amplitude * phase / rise
        if phase <= hold:
            return amplitude
        if phase < fall:
            return amplitude * (fall - phase) / (fall - hold)
        return 0.0

    def solve(self) -> PhkOracleResult:
        coordinates = self.physical.coordinates
        grid = PhkGrid.build(
            nx=self.resolution.nx,
            nz=self.resolution.nz,
            x_min=float(coordinates["x_min"]),
            x_max=float(coordinates["x_max"]),
            z_min=float(coordinates["z_min"]),
            z_max=float(coordinates["z_max"]),
        )
        dt = self.resolution.dt
        step_count_float = self.resolution.time_end / dt
        step_count = int(round(step_count_float))
        if not math.isclose(step_count_float, step_count, rel_tol=0.0, abs_tol=1.0e-12):
            raise ValueError("time_end must contain an integral number of steps")
        coefficients = dict(self.physical.coefficients)
        if self.case.control is PhkControl.JOULE_GAIN_ZERO:
            coefficients["joule_gain"] = 0.0
        if self.case.control is PhkControl.CONDUCTIVITY_PHASE_RATIO_ONE:
            coefficients["conductivity_phase_ratio"] = 1.0
        if self.case.control is PhkControl.LATENT_RATIO_ZERO:
            coefficients["latent_ratio"] = 0.0

        field_guards = _mapping(self.physical.payload["fields"], "fields")
        phase_range = _mapping(field_guards["phase_fraction"], "fields.phase_fraction")["range_guard"]
        lower_bound, upper_bound = float(phase_range[0]), float(phase_range[1])
        phase_old = _initial_phase(
            grid, coefficients, self.case.initial_phase_background
        ).astype(np.float64)
        if np.any(phase_old < lower_bound) or np.any(phase_old > upper_bound):
            raise RuntimeError("initial PHK phase violates the frozen range guard")
        temperature_old = np.zeros(grid.cell_count, dtype=np.float64)

        geometry = _mapping(self.physical.payload["geometry"], "geometry")
        thermal_laplacian = grid.thermal_laplacian(float(geometry["thermal_robin_biot"]))
        thermal_matrix = (
            sparse.eye(grid.cell_count, format="csc")
            - dt * float(coefficients["thermal_diffusivity"]) * thermal_laplacian.tocsc()
            + dt * float(coefficients["volumetric_cooling"]) * sparse.eye(grid.cell_count, format="csc")
        )
        thermal_factor = sparse_linalg.splu(thermal_matrix)
        solver = self.physical.nonlinear_solver
        maximum_blocks = int(solver["coupled_max_blocks"])
        block_tolerance = float(solver["coupled_relative_change_tolerance"])
        residual_tolerance = float(solver["coupled_residual_tolerance"])
        relaxation = float(solver["coupled_relaxation"])
        if relaxation != 1.0:
            raise ValueError("PHK-V2 v1 only admits its frozen unit block relaxation")

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
            applied_voltage=self._waveform(0.0),
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
        counters = _SolverCounters(electric_linear_solves=1)

        for step in range(1, step_count + 1):
            time_value = step * dt
            temperature_iter = temperature_old.copy()
            phase_iter = phase_old.copy()
            accepted: tuple[PhkElectricResult, FloatArray, FloatArray, float, float] | None = None
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
                    applied_voltage=self._waveform(time_value),
                    heater_width_fraction=self.case.heater_width_fraction,
                )
                counters.electric_linear_solves += 1
                phase_target, newton_iterations, phase_solves, _ = _solve_phase_newton(
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
                counters.phase_newton_iterations += newton_iterations
                counters.phase_linear_solves += phase_solves
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
                        temperature_gain=float(coefficients["conductivity_temperature_gain"]),
                    )
                    final_electric = solve_electric_field(
                        grid=grid,
                        conductivity=final_conductivity,
                        applied_voltage=self._waveform(time_value),
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
                        - float(coefficients["latent_ratio"]) * (phase_iter - phase_old)
                        + dt * float(coefficients["joule_gain"]) * final_electric.joule_density
                    )
                    thermal_residual = thermal_matrix @ temperature_iter - final_thermal_rhs
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
                raise RuntimeError("PHK electrothermal-phase block exceeded its frozen iteration limit")
            final_electric, temperature_new, phase_new, thermal_norm, phase_norm = accepted
            if not (
                np.isfinite(temperature_new).all()
                and np.isfinite(phase_new).all()
                and np.isfinite(final_electric.potential).all()
            ):
                raise RuntimeError("PHK solver produced non-finite state")
            if np.any(phase_new < lower_bound) or np.any(phase_new > upper_bound):
                raise RuntimeError("PHK accepted phase violates the frozen range guard")

            current_balance_history[step - 1] = final_electric.current_balance_relative
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

        statistics = {
            "time_steps_total": counters.time_steps,
            "coupled_blocks_total": counters.coupled_blocks,
            "electric_linear_solves_total": counters.electric_linear_solves,
            "thermal_linear_solves_total": counters.thermal_linear_solves,
            "phase_linear_solves_total": counters.phase_linear_solves,
            "phase_newton_iterations_total": counters.phase_newton_iterations,
            "final_residual_evaluations_total": counters.final_residual_evaluations,
            "linear_solves_total": (
                counters.electric_linear_solves
                + counters.thermal_linear_solves
                + counters.phase_linear_solves
            ),
        }
        return PhkOracleResult(
            physical_contract_id=self.physical.contract_id,
            program_contract_sha256=self.physical.program.sha256,
            object_contract_sha256=self.physical.object.sha256,
            case=self.case,
            resolution=self.resolution,
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


@dataclass(frozen=True)
class PhkCycleEvent:
    cycle_index: int
    event_time: float | None
    pre_roi_fraction: float
    peak_roi_fraction: float
    peak_full_domain_fraction: float
    peak_outside_roi_fraction: float
    recovery_fraction: float
    saved_steps_at_or_above_threshold: int


@dataclass(frozen=True)
class PhkEventReport:
    cycles: tuple[PhkCycleEvent, ...]
    cycle_peak_relative_drift: float
    passed: bool
    failures: tuple[str, ...]

    @classmethod
    def from_result(
        cls,
        result: PhkOracleResult,
        *,
        physical: PhkPhysicalContract,
    ) -> "PhkEventReport":
        event = _mapping(physical.payload["qualification_event"], "qualification_event")
        roi_spec = _mapping(event["roi"], "qualification_event.roi")
        roi = (
            (np.abs(result.grid.cell_x) <= float(roi_spec["abs_x_max"]))
            & (result.grid.cell_z >= float(roi_spec["z_min"]))
            & (result.grid.cell_z <= float(roi_spec["z_max"]))
        )
        if not np.any(roi) or np.all(roi):
            raise ValueError("event ROI must be a nonempty strict subset of the grid")
        threshold = float(event["phase_threshold"])
        weights = result.grid.cell_volumes
        active = result.phase >= threshold
        roi_fraction = np.sum(active[:, roi] * weights[roi], axis=1) / np.sum(weights[roi])
        full_fraction = np.sum(active * weights, axis=1) / np.sum(weights)
        outside_fraction = np.sum(active[:, ~roi] * weights[~roi], axis=1) / np.sum(weights)
        event_threshold = float(event["event_threshold_roi_fraction"])
        period = float(physical.coordinates["time_period"])
        cycle_reports: list[PhkCycleEvent] = []
        failures: list[str] = []

        for cycle_index in range(int(physical.coordinates["pulse_cycles"])):
            start_time = cycle_index * period
            end_time = (cycle_index + 1) * period
            if cycle_index + 1 == int(physical.coordinates["pulse_cycles"]):
                indices = np.flatnonzero((result.time >= start_time) & (result.time <= end_time))
            else:
                indices = np.flatnonzero((result.time >= start_time) & (result.time < end_time))
            if indices.size < 2:
                failures.append(f"cycle_{cycle_index + 1}_insufficient_saved_times")
                continue
            values = roi_fraction[indices]
            pre = float(values[0])
            local_peak_position = int(np.argmax(values))
            peak_index = int(indices[local_peak_position])
            peak = float(roi_fraction[peak_index])
            crossing: float | None = None
            for before, after in zip(indices[:-1], indices[1:], strict=True):
                low = float(roi_fraction[before])
                high = float(roi_fraction[after])
                if low < event_threshold <= high and high > low:
                    fraction = (event_threshold - low) / (high - low)
                    crossing = float(result.time[before] + fraction * (result.time[after] - result.time[before]))
                    break
            end_fraction = float(values[-1])
            excursion = peak - pre
            recovery = (peak - end_fraction) / excursion if excursion > 0.0 else 0.0
            at_or_above = int(np.count_nonzero(values >= event_threshold))
            cycle = PhkCycleEvent(
                cycle_index=cycle_index + 1,
                event_time=crossing,
                pre_roi_fraction=pre,
                peak_roi_fraction=peak,
                peak_full_domain_fraction=float(full_fraction[peak_index]),
                peak_outside_roi_fraction=float(outside_fraction[peak_index]),
                recovery_fraction=float(recovery),
                saved_steps_at_or_above_threshold=at_or_above,
            )
            cycle_reports.append(cycle)
            if crossing is None:
                failures.append(f"cycle_{cycle_index + 1}_event_missing")
            if peak < float(event["minimum_peak_roi_fraction"]):
                failures.append(f"cycle_{cycle_index + 1}_roi_peak_below_minimum")
            if cycle.peak_full_domain_fraction > float(event["maximum_peak_full_domain_fraction"]):
                failures.append(f"cycle_{cycle_index + 1}_full_domain_peak_too_large")
            if cycle.peak_outside_roi_fraction > float(event["maximum_peak_outside_roi_fraction"]):
                failures.append(f"cycle_{cycle_index + 1}_outside_roi_peak_too_large")
            if excursion < float(event["minimum_peak_minus_pre_fraction"]):
                failures.append(f"cycle_{cycle_index + 1}_excursion_too_small")
            if recovery < float(event["minimum_recovery_fraction"]):
                failures.append(f"cycle_{cycle_index + 1}_recovery_too_small")
            if at_or_above < int(event["minimum_event_saved_steps"]):
                failures.append(f"cycle_{cycle_index + 1}_event_under_resolved")

        if len(cycle_reports) == 2:
            peaks = [cycle.peak_roi_fraction for cycle in cycle_reports]
            drift = abs(peaks[1] - peaks[0]) / max(abs(peaks[0]), 1.0e-14)
            if drift > float(event["maximum_cycle_peak_relative_drift"]):
                failures.append("cycle_peak_relative_drift_too_large")
        else:
            drift = math.inf
            failures.append("two_complete_cycles_not_available")
        return cls(
            cycles=tuple(cycle_reports),
            cycle_peak_relative_drift=float(drift),
            passed=not failures,
            failures=tuple(failures),
        )


@dataclass(frozen=True)
class PhkGuardReport:
    passed: bool
    failures: tuple[str, ...]
    nonfinite_count: int
    maximum_current_balance_relative: float
    maximum_thermal_residual_scaled: float
    maximum_phase_residual_scaled: float
    maximum_linear_residual_scaled: float
    maximum_no_flux_residual_scaled: float
    potential_range: tuple[float, float]
    temperature_range: tuple[float, float]
    phase_range: tuple[float, float]

    @classmethod
    def from_result(
        cls,
        result: PhkOracleResult,
        *,
        physical: PhkPhysicalContract,
    ) -> "PhkGuardReport":
        arrays = (result.potential, result.temperature, result.phase, result.top_current, result.bottom_current)
        nonfinite = sum(int(np.size(array) - np.count_nonzero(np.isfinite(array))) for array in arrays)
        potential_range = (float(np.nanmin(result.potential)), float(np.nanmax(result.potential)))
        temperature_range = (float(np.nanmin(result.temperature)), float(np.nanmax(result.temperature)))
        phase_range = (float(np.nanmin(result.phase)), float(np.nanmax(result.phase)))
        thresholds = _mapping(physical.payload["hard_guard_thresholds"], "hard_guard_thresholds")
        fields = _mapping(physical.payload["fields"], "fields")
        failures: list[str] = []
        if nonfinite > int(thresholds["maximum_nonfinite_count"]):
            failures.append("nonfinite_output")
        for name, actual in (
            ("potential", potential_range),
            ("reduced_temperature", temperature_range),
            ("phase_fraction", phase_range),
        ):
            guard = _mapping(fields[name], f"fields.{name}")["range_guard"]
            if actual[0] < float(guard[0]) or actual[1] > float(guard[1]):
                failures.append(f"{name}_range")
        max_current = _maximum_absolute(result.current_balance_history)
        max_thermal = _maximum_absolute(result.thermal_residual_history)
        max_phase = _maximum_absolute(result.phase_residual_history)
        max_linear = _maximum_absolute(result.linear_residual_history)
        no_flux = 0.0  # zero-normal faces are absent from the conservative phase operator
        if max_current > float(thresholds["maximum_electric_current_balance_relative"]):
            failures.append("terminal_current_balance")
        if max_thermal > float(thresholds["maximum_thermal_balance_relative"]):
            failures.append("thermal_balance")
        if max_phase > float(thresholds["maximum_phase_equation_residual_scaled"]):
            failures.append("phase_equation_residual")
        if no_flux > float(thresholds["maximum_no_flux_residual_scaled"]):
            failures.append("phase_no_flux")
        return cls(
            passed=not failures,
            failures=tuple(failures),
            nonfinite_count=nonfinite,
            maximum_current_balance_relative=max_current,
            maximum_thermal_residual_scaled=max_thermal,
            maximum_phase_residual_scaled=max_phase,
            maximum_linear_residual_scaled=max_linear,
            maximum_no_flux_residual_scaled=no_flux,
            potential_range=potential_range,
            temperature_range=temperature_range,
            phase_range=phase_range,
        )


def _interpolate_field_to(
    source: PhkOracleResult,
    target: PhkOracleResult,
    values: FloatArray,
) -> FloatArray:
    if (
        source.grid.nx == target.grid.nx
        and source.grid.nz == target.grid.nz
        and np.array_equal(source.time, target.time)
    ):
        return values.copy()
    source_values = values.reshape(source.time.size, source.grid.nz, source.grid.nx)
    interpolator = RegularGridInterpolator(
        (source.time, source.grid.z_centers, source.grid.x_centers),
        source_values,
        method="linear",
        bounds_error=True,
    )
    target_t, target_z, target_x = np.meshgrid(
        target.time,
        target.grid.z_centers,
        target.grid.x_centers,
        indexing="ij",
    )
    points = np.column_stack((target_t.ravel(), target_z.ravel(), target_x.ravel()))
    return interpolator(points).reshape(target.time.size, target.grid.cell_count)


def _interpolate_trace(source_time: FloatArray, source: FloatArray, target_time: FloatArray) -> FloatArray:
    if np.array_equal(source_time, target_time):
        return source.copy()
    return np.interp(target_time, source_time, source).astype(np.float64)


@dataclass(frozen=True)
class PhkConvergenceReport:
    component_order: tuple[str, ...]
    component_deltas: FloatArray
    finite: bool


def compare_phk_results(
    coarse: PhkOracleResult,
    fine: PhkOracleResult,
    *,
    physical: PhkPhysicalContract,
) -> PhkConvergenceReport:
    if coarse.physical_contract_id != fine.physical_contract_id or coarse.physical_contract_id != physical.contract_id:
        raise ValueError("PHK convergence comparison contract mismatch")
    fine_phase_on_coarse = _interpolate_field_to(fine, coarse, fine.phase)
    fine_temperature_on_coarse = _interpolate_field_to(fine, coarse, fine.temperature)
    roi_spec = _mapping(
        _mapping(physical.payload["qualification_event"], "qualification_event")["roi"],
        "qualification_event.roi",
    )
    roi = (
        (np.abs(coarse.grid.cell_x) <= float(roi_spec["abs_x_max"]))
        & (coarse.grid.cell_z >= float(roi_spec["z_min"]))
        & (coarse.grid.cell_z <= float(roi_spec["z_max"]))
    )
    phase_rms = float(
        np.sqrt(np.mean((coarse.phase[:, roi] - fine_phase_on_coarse[:, roi]) ** 2))
    ) / 0.5
    temperature_rms = float(
        np.sqrt(
            np.mean(
                (coarse.temperature[:, roi] - fine_temperature_on_coarse[:, roi]) ** 2
            )
        )
    ) / 0.45
    fine_current_on_coarse = _interpolate_trace(fine.time, fine.top_current, coarse.time)
    current_scale = max(
        float(np.sqrt(np.mean(fine_current_on_coarse * fine_current_on_coarse))),
        1.0e-12,
    )
    current_rms = float(
        np.sqrt(np.mean((coarse.top_current - fine_current_on_coarse) ** 2))
    ) / current_scale

    coarse_event = PhkEventReport.from_result(coarse, physical=physical)
    fine_event = PhkEventReport.from_result(fine, physical=physical)
    event_deltas: list[float] = []
    recovery_deltas: list[float] = []
    if len(coarse_event.cycles) == len(fine_event.cycles):
        for first, second in zip(coarse_event.cycles, fine_event.cycles, strict=True):
            if first.event_time is None and second.event_time is None:
                event_deltas.append(0.0)
            elif first.event_time is None or second.event_time is None:
                event_deltas.append(math.inf)
            else:
                event_deltas.append(abs(first.event_time - second.event_time))
            recovery_deltas.append(abs(first.recovery_fraction - second.recovery_fraction))
    else:
        event_deltas.append(math.inf)
        recovery_deltas.append(math.inf)
    event_time_delta = float(np.sqrt(np.mean(np.square(event_deltas))))
    recovery_delta = float(np.sqrt(np.mean(np.square(recovery_deltas))))

    coarse_active = coarse.phase >= float(
        _mapping(physical.payload["qualification_event"], "qualification_event")["phase_threshold"]
    )
    fine_active = fine_phase_on_coarse >= float(
        _mapping(physical.payload["qualification_event"], "qualification_event")["phase_threshold"]
    )
    region_delta = float(np.mean(np.logical_xor(coarse_active, fine_active)))
    order = tuple(
        _mapping(physical.payload["convergence"], "convergence")["component_order"]
    )
    deltas = np.asarray(
        (phase_rms, temperature_rms, current_rms, event_time_delta, region_delta, recovery_delta),
        dtype=np.float64,
    )
    return PhkConvergenceReport(
        component_order=order,
        component_deltas=deltas,
        finite=bool(np.isfinite(deltas).all()),
    )


def run_phk_manufactured_checks(physical: PhkPhysicalContract) -> dict[str, Any]:
    """Exercise independent operators without producing a scientific field case."""

    grid = PhkGrid.build(
        nx=10,
        nz=6,
        x_min=float(physical.coordinates["x_min"]),
        x_max=float(physical.coordinates["x_max"]),
        z_min=float(physical.coordinates["z_min"]),
        z_max=float(physical.coordinates["z_max"]),
    )
    electric = solve_electric_field(
        grid=grid,
        conductivity=np.ones(grid.cell_count, dtype=np.float64),
        applied_voltage=0.75,
        heater_width_fraction=1.0,
    )
    electric_error = _maximum_absolute(electric.potential - 0.75 * grid.cell_z)
    electric_power_error = abs(electric.joule_power_total - electric.top_current * 0.75)

    probe = (
        0.21
        + 0.03 * np.sin(math.pi * grid.cell_x)
        * np.cos(0.5 * math.pi * grid.cell_z)
    ).astype(np.float64)
    old = (probe - 0.001 * np.cos(0.7 * grid.cell_x)).astype(np.float64)
    temperature = (0.40 + 0.04 * grid.cell_z + 0.01 * grid.cell_x).astype(np.float64)
    direction = (
        np.cos(1.3 * grid.cell_x) * np.sin(0.8 + grid.cell_z)
    ).astype(np.float64)
    direction /= float(np.linalg.norm(direction))
    coefficients = physical.coefficients
    residual, jacobian = _phase_residual_and_jacobian(
        probe,
        phase_old=old,
        temperature=temperature,
        grid=grid,
        dt=0.0025,
        coefficients=coefficients,
        interface_width=float(coefficients["interface_width"]),
    )
    step = 1.0e-6
    plus, _ = _phase_residual_and_jacobian(
        probe + step * direction,
        phase_old=old,
        temperature=temperature,
        grid=grid,
        dt=0.0025,
        coefficients=coefficients,
        interface_width=float(coefficients["interface_width"]),
    )
    minus, _ = _phase_residual_and_jacobian(
        probe - step * direction,
        phase_old=old,
        temperature=temperature,
        grid=grid,
        dt=0.0025,
        coefficients=coefficients,
        interface_width=float(coefficients["interface_width"]),
    )
    finite_difference = (plus - minus) / (2.0 * step)
    analytic = jacobian @ direction
    jacobian_error = float(np.linalg.norm(finite_difference - analytic)) / max(
        float(np.linalg.norm(finite_difference)), 1.0e-14
    )

    phase_conservation = abs(
        float(np.sum((grid.phase_laplacian @ probe) * grid.cell_volumes))
    )
    geometry = _mapping(physical.payload["geometry"], "geometry")
    biot = float(geometry["thermal_robin_biot"])
    thermal_laplacian = grid.thermal_laplacian(biot)
    constant = np.ones(grid.cell_count, dtype=np.float64)
    integrated_thermal_sink = -float(
        np.sum((thermal_laplacian @ constant) * grid.cell_volumes)
    )
    width = grid.x_max - grid.x_min
    height = grid.z_max - grid.z_min
    expected_sink = (
        2.0 * width / grid.dz
        + biot * width
        + 2.0 * biot * height
    )
    thermal_boundary_error = abs(integrated_thermal_sink - expected_sink)
    checks = {
        "electric_linear_max_abs_error": electric_error,
        "electric_current_balance_relative": electric.current_balance_relative,
        "electric_power_identity_abs_error": electric_power_error,
        "phase_neumann_integral_abs_error": phase_conservation,
        "phase_jacobian_directional_relative_l2": jacobian_error,
        "phase_residual_probe_linf": _maximum_absolute(residual),
        "thermal_boundary_integral_abs_error": thermal_boundary_error,
    }
    passed = bool(
        electric_error <= 5.0e-12
        and electric.current_balance_relative <= 5.0e-12
        and electric_power_error <= 5.0e-12
        and phase_conservation <= 5.0e-12
        and jacobian_error <= 2.0e-7
        and thermal_boundary_error <= 5.0e-12
        and all(math.isfinite(float(value)) for value in checks.values())
    )
    return {
        "schema_id": "phk-v2-manufactured-operator-report-v1",
        "evidence_identity": "NO_SCIENTIFIC_FIELD_RESULT",
        "program_contract_sha256": physical.program.sha256,
        "object_contract_sha256": physical.object.sha256,
        "grid": {"nx": grid.nx, "nz": grid.nz},
        "checks": checks,
        "passed": passed,
    }


__all__ = [
    "PhkCaseSpec",
    "PhkControl",
    "PhkConvergenceReport",
    "PhkCycleEvent",
    "PhkElectricResult",
    "PhkEventReport",
    "PhkGrid",
    "PhkGuardReport",
    "PhkOracleCase",
    "PhkOracleResult",
    "PhkPhysicalContract",
    "PhkResolution",
    "compare_phk_results",
    "read_phk_result",
    "run_phk_manufactured_checks",
    "solve_electric_field",
    "write_phk_result",
]
