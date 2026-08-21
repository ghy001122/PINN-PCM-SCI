"""Independent finite-volume oracle for the approved QPOP-R3-v1 reduction.

The reduction retains the Q-POP bulk Landau coefficients, intrinsic carrier
mapping, anisotropic mobilities, Joule heating, heat loss, and structural
Allen-Cahn dynamics.  It intentionally removes carrier dynamics, Poisson space
charge, and independent electronic-order-parameter dynamics.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy import sparse
from scipy.sparse.linalg import factorized, spsolve

from .artifacts import CaseArtifact
from .qpop_physics import QPopParameters


FloatArray = NDArray[np.float64]


def _fermi(gamma: FloatArray) -> FloatArray:
    gamma = np.asarray(gamma, dtype=np.float64)
    regular = 1.0 / (
        np.exp(np.clip(-gamma, -100.0, 100.0))
        + 3.0 * math.sqrt(math.pi) / 4.0 * (4.0 + gamma**2) ** (-0.75)
    )
    high = 4.0 / (3.0 * math.sqrt(math.pi)) * (4.0 + gamma**2) ** 0.75
    return np.where(gamma < -100.0, 0.0, np.where(gamma > 100.0, high, regular))


def bulk_free_energy(
    parameters: QPopParameters,
    eta: FloatArray,
    mu: FloatArray,
    temperature: FloatArray,
    tc_variance: FloatArray,
) -> FloatArray:
    p = parameters
    return (
        p.an1 * (temperature - p.t1 - tc_variance) / (2.0 * p.tc) * eta**2
        + p.an2 / 4.0 * eta**4
        + p.an3 / 6.0 * eta**6
        + p.au1 * (temperature - p.t2 - tc_variance) / (2.0 * p.tc) * mu**2
        + p.au2 / 4.0 * mu**4
        + p.au3 / 6.0 * mu**6
        + p.gnu1 * eta * mu
        - p.gnu2 / 2.0 * eta**2 * mu**2
        + p.gnu3 / 2.0 * eta**3 * mu
    )


def _df_dmu(
    p: QPopParameters,
    eta: FloatArray,
    mu: FloatArray,
    temperature: FloatArray,
    tc_variance: FloatArray,
) -> FloatArray:
    return (
        p.au1 * (temperature - p.t2 - tc_variance) / p.tc * mu
        + p.au2 * mu**3
        + p.au3 * mu**5
        + p.gnu1 * eta
        - p.gnu2 * eta**2 * mu
        + 0.5 * p.gnu3 * eta**3
    )


def stable_mu_equilibrium(
    parameters: QPopParameters,
    eta: FloatArray,
    temperature: FloatArray,
    tc_variance: FloatArray,
) -> FloatArray:
    """Select the lowest frozen-Q-POP stable local minimum over multiple basins."""
    p = parameters
    eta_values, temperature_values, tc_values = np.broadcast_arrays(
        np.asarray(eta, dtype=np.float64),
        np.asarray(temperature, dtype=np.float64),
        np.asarray(tc_variance, dtype=np.float64),
    )
    starts = np.linspace(-2.4, 2.4, 13, dtype=np.float64)
    candidates = np.broadcast_to(
        starts.reshape((-1,) + (1,) * eta_values.ndim),
        (starts.size,) + eta_values.shape,
    ).copy()
    expanded_eta = eta_values[None, ...]
    expanded_temperature = temperature_values[None, ...]
    expanded_tc = tc_values[None, ...]
    linear = (
        p.au1 * (expanded_temperature - p.t2 - expanded_tc) / p.tc
        - p.gnu2 * expanded_eta**2
    )
    constant = p.gnu1 * expanded_eta + 0.5 * p.gnu3 * expanded_eta**3
    for _ in range(48):
        residual = (
            p.au3 * candidates**5
            + p.au2 * candidates**3
            + linear * candidates
            + constant
        )
        curvature = 5.0 * p.au3 * candidates**4 + 3.0 * p.au2 * candidates**2 + linear
        safe = np.where(np.abs(curvature) < 1.0e-10, np.copysign(1.0e-10, curvature + 1.0e-30), curvature)
        candidates -= np.clip(residual / safe, -0.25, 0.25)
    residual = np.abs(
        p.au3 * candidates**5
        + p.au2 * candidates**3
        + linear * candidates
        + constant
    )
    curvature = 5.0 * p.au3 * candidates**4 + 3.0 * p.au2 * candidates**2 + linear
    energies = bulk_free_energy(
        p, expanded_eta, candidates, expanded_temperature, expanded_tc
    )
    admissible = (residual <= 1.0e-7) & (curvature > 1.0e-9)
    ranked = np.where(admissible, energies, np.inf)
    selected = np.argmin(ranked, axis=0)
    result = np.take_along_axis(candidates, selected[None, ...], axis=0)[0]
    if not np.all(np.isfinite(np.min(ranked, axis=0))):
        raise RuntimeError("Q-POP stable electronic equilibrium was not resolved")
    return result


def pulse_train_voltage(time_ns: FloatArray, *, amplitude: float) -> FloatArray:
    """Four 60 ns on / 60 ns off pulses with registered 5 ns linear edges."""
    time = np.asarray(time_ns, dtype=np.float64)
    phase = np.mod(time, 120.0)
    active = (time >= 0.0) & (time < 480.0)
    value = np.zeros_like(time)
    rising = phase < 5.0
    plateau = (phase >= 5.0) & (phase <= 60.0)
    falling = (phase > 60.0) & (phase < 65.0)
    value = np.where(rising, amplitude * phase / 5.0, value)
    value = np.where(plateau, amplitude, value)
    value = np.where(falling, amplitude * (65.0 - phase) / 5.0, value)
    return np.where(active, value, 0.0)


@dataclass(frozen=True)
class ReducedOracleGrid:
    nx: int
    ny: int

    def __post_init__(self) -> None:
        if self.nx < 3 or self.ny < 3:
            raise ValueError("reduced-oracle grid requires at least 3 by 3 cells")


def _laplacian_no_flux(grid: ReducedOracleGrid, dx: float, dy: float) -> sparse.csc_matrix:
    nx, ny = grid.nx, grid.ny
    rows: list[int] = []
    columns: list[int] = []
    values: list[float] = []
    for j in range(ny):
        for i in range(nx):
            index = j * nx + i
            diagonal = 0.0
            for ni, nj, coefficient in (
                (i - 1, j, 1.0 / dx**2),
                (i + 1, j, 1.0 / dx**2),
                (i, j - 1, 1.0 / dy**2),
                (i, j + 1, 1.0 / dy**2),
            ):
                if 0 <= ni < nx and 0 <= nj < ny:
                    rows.append(index)
                    columns.append(nj * nx + ni)
                    values.append(coefficient)
                    diagonal -= coefficient
            rows.append(index)
            columns.append(index)
            values.append(diagonal)
    return sparse.csc_matrix((values, (rows, columns)), shape=(nx * ny, nx * ny))


def _robin_laplacian(
    grid: ReducedOracleGrid,
    dx: float,
    dy: float,
    effective_length: float,
    surrounding: float,
) -> tuple[sparse.csc_matrix, FloatArray]:
    matrix = _laplacian_no_flux(grid, dx, dy).tolil()
    source = np.zeros(grid.nx * grid.ny, dtype=np.float64)
    for j in range(grid.ny):
        for i in range(grid.nx):
            index = j * grid.nx + i
            boundary_scales: list[float] = []
            if i == 0 or i == grid.nx - 1:
                boundary_scales.append(1.0 / (effective_length * dx))
            if j == 0 or j == grid.ny - 1:
                boundary_scales.append(1.0 / (effective_length * dy))
            for scale in boundary_scales:
                matrix[index, index] -= scale
                source[index] += scale * surrounding
    return matrix.tocsc(), source


def _tc_variance(p: QPopParameters, x: FloatArray, y: FloatArray) -> FloatArray:
    radius = np.sqrt((x - p.lx / 2.0) ** 2 + y**2)
    return p.tc_shift * (-np.tanh(2.0 * (radius - p.nucleus_radius) / p.domain_wall_width) + 1.0) / 2.0


def _conductivity(
    p: QPopParameters, mu: FloatArray, temperature: FloatArray
) -> tuple[FloatArray, FloatArray]:
    gamma = -(p.chi * mu**2 / 2.0) / np.maximum(p.kb * temperature, 1.0e-12)
    density = p.electron_density_of_states * _fermi(gamma)
    sigma_x = p.charge * density * (p.electron_mobility_x + p.hole_mobility_x)
    sigma_y = p.charge * density * (p.electron_mobility_y + p.hole_mobility_y)
    return np.maximum(sigma_x, 1.0e-14), np.maximum(sigma_y, 1.0e-14)


def _unit_electric_solution(
    grid: ReducedOracleGrid,
    dx: float,
    dy: float,
    lz: float,
    sigma_x: FloatArray,
    sigma_y: FloatArray,
) -> tuple[FloatArray, float]:
    nx, ny = grid.nx, grid.ny
    sx = sigma_x.reshape(ny, nx)
    sy = sigma_y.reshape(ny, nx)
    rows: list[int] = []
    columns: list[int] = []
    values: list[float] = []
    rhs = np.zeros(nx * ny, dtype=np.float64)

    def harmonic(left: float, right: float) -> float:
        return 2.0 * left * right / max(left + right, 1.0e-30)

    for j in range(ny):
        for i in range(nx):
            index = j * nx + i
            diagonal = 0.0
            if i > 0:
                conductance = harmonic(sx[j, i], sx[j, i - 1]) / dx**2
                rows.append(index); columns.append(index - 1); values.append(-conductance)
                diagonal += conductance
            if i + 1 < nx:
                conductance = harmonic(sx[j, i], sx[j, i + 1]) / dx**2
                rows.append(index); columns.append(index + 1); values.append(-conductance)
                diagonal += conductance
            if j > 0:
                conductance = harmonic(sy[j, i], sy[j - 1, i]) / dy**2
                rows.append(index); columns.append(index - nx); values.append(-conductance)
                diagonal += conductance
            else:
                diagonal += 2.0 * sy[j, i] / dy**2
            if j + 1 < ny:
                conductance = harmonic(sy[j, i], sy[j + 1, i]) / dy**2
                rows.append(index); columns.append(index + nx); values.append(-conductance)
                diagonal += conductance
            else:
                boundary = 2.0 * sy[j, i] / dy**2
                diagonal += boundary
                rhs[index] += boundary
            rows.append(index); columns.append(index); values.append(diagonal)
    matrix = sparse.csc_matrix((values, (rows, columns)), shape=(nx * ny, nx * ny))
    potential = np.asarray(spsolve(matrix, rhs), dtype=np.float64)
    top = potential.reshape(ny, nx)[-1]
    top_flux = 2.0 * sy[-1] * (1.0 - top) / dy
    conductance = float(np.sum(top_flux) * dx * lz)
    return potential, max(conductance, 0.0)


def _df_deta(
    p: QPopParameters,
    eta: FloatArray,
    mu: FloatArray,
    temperature: FloatArray,
    tc_variance: FloatArray,
) -> FloatArray:
    return (
        p.an1 * (temperature - p.t1 - tc_variance) / p.tc * eta
        + p.an2 * eta**3
        + p.an3 * eta**5
        + p.gnu1 * mu
        - p.gnu2 * eta * mu**2
        + 1.5 * p.gnu3 * eta**2 * mu
    )


def _reaction_step(
    p: QPopParameters,
    eta_old: FloatArray,
    temperature: FloatArray,
    tc_variance: FloatArray,
    dt: float,
) -> tuple[FloatArray, float]:
    eta = eta_old.copy()
    # First-order operator splitting: the algebraic electronic equilibrium is
    # frozen over this Allen-Cahn substep and is closed again after the update.
    # Re-solving its full multi-basin problem inside every Newton iteration is
    # mathematically redundant for the registered split scheme and dominated
    # the 494 ns runtime.
    mu = stable_mu_equilibrium(p, eta_old, temperature, tc_variance)
    residual = np.zeros_like(eta)
    for _ in range(48):
        force = _df_deta(p, eta, mu, temperature, tc_variance)
        residual = eta - eta_old + dt * 2.0 * p.structural_mobility * force
        derivative = 1.0 + dt * 2.0 * p.structural_mobility * (
            p.an1 * (temperature - p.t1 - tc_variance) / p.tc
            + 3.0 * p.an2 * eta**2
            + 5.0 * p.an3 * eta**4
            - p.gnu2 * mu**2
            + 3.0 * p.gnu3 * eta * mu
        )
        safe = np.where(np.abs(derivative) < 1.0e-9, np.copysign(1.0e-9, derivative + 1.0e-30), derivative)
        delta = np.clip(residual / safe, -0.1, 0.1)
        eta -= delta
        if float(np.max(np.abs(residual))) <= 1.0e-8:
            break
    scale = max(float(np.max(np.abs(eta_old))), 1.0)
    return eta, float(np.max(np.abs(residual)) / scale)


@dataclass
class ReducedOracleResult:
    time_ns: FloatArray
    nodes: FloatArray
    eta: FloatArray
    mu: FloatArray
    temperature: FloatArray
    electric_potential: FloatArray
    device_voltage: FloatArray
    current_amp: FloatArray
    balance_history: list[dict[str, float]]
    max_balance_violation: float


def reduced_result_to_artifact(
    result: ReducedOracleResult,
    *,
    grid: ReducedOracleGrid,
    case_id: str,
) -> CaseArtifact:
    if result.nodes.shape[0] != grid.nx * grid.ny:
        raise ValueError("result nodes do not match the registered reduced grid")
    cells: list[tuple[int, int, int]] = []
    for j in range(grid.ny - 1):
        for i in range(grid.nx - 1):
            lower_left = j * grid.nx + i
            lower_right = lower_left + 1
            upper_left = lower_left + grid.nx
            upper_right = upper_left + 1
            cells.append((lower_left, lower_right, upper_right))
            cells.append((lower_left, upper_right, upper_left))
    breakpoints = np.asarray(
        sorted(
            value
            for period in range(4)
            for value in (120.0 * period, 120.0 * period + 5.0, 120.0 * period + 60.0, 120.0 * period + 65.0)
            if 0.0 <= value <= float(result.time_ns[-1])
        ),
        dtype=np.float64,
    )
    return CaseArtifact(
        case_id=case_id,
        physical_contract_id="qpop-r3-v1",
        evidence_identity="QPOP_R3_V1_REDUCED_SYNTHETIC_ORACLE",
        nodes=result.nodes,
        cells=np.asarray(cells, dtype=np.int64),
        mesh_unit="nm",
        field_time=result.time_ns,
        circuit_time=result.time_ns,
        time_unit="ns",
        fields={
            "eta": result.eta,
            "mu_equilibrium": result.mu,
            "electric_potential": result.electric_potential,
            "temperature": result.temperature,
        },
        field_units={
            "eta": "1",
            "mu_equilibrium": "1",
            "electric_potential": "V",
            "temperature": "K",
        },
        breakpoints=breakpoints,
        circuit={
            "qpop_r3_device_voltage": result.device_voltage,
            "qpop_r3_current": result.current_amp,
        },
        circuit_units={
            "qpop_r3_device_voltage": "V",
            "qpop_r3_current": "A",
        },
    )


@dataclass(frozen=True)
class ReducedOracleCase:
    parameters: QPopParameters
    grid: ReducedOracleGrid
    end_time_ns: float
    time_step_ns: float
    drive_voltage_v: float
    series_resistance_ohm: float
    heat_transfer_multiplier: float = 1.0
    save_every: int = 5

    def __post_init__(self) -> None:
        if self.end_time_ns <= 0.0 or self.time_step_ns <= 0.0:
            raise ValueError("oracle time controls must be positive")
        if self.drive_voltage_v < 0.0 or self.series_resistance_ohm <= 0.0:
            raise ValueError("oracle electrical controls are invalid")
        if self.heat_transfer_multiplier <= 0.0 or self.save_every <= 0:
            raise ValueError("oracle thermal/save controls are invalid")
        steps = self.end_time_ns / self.time_step_ns
        if abs(steps - round(steps)) > 1.0e-10:
            raise ValueError("oracle end time must be an integer number of steps")

    def solve(self) -> ReducedOracleResult:
        p, grid = self.parameters, self.grid
        nx, ny = grid.nx, grid.ny
        dx, dy = p.lx / nx, p.ly / ny
        x = (np.arange(nx, dtype=np.float64) + 0.5) * dx
        y = (np.arange(ny, dtype=np.float64) + 0.5) * dy
        xx, yy = np.meshgrid(x, y)
        nodes = np.column_stack([xx.ravel(), yy.ravel()])
        tc_variance = _tc_variance(p, nodes[:, 0], nodes[:, 1])
        eta = np.full(nx * ny, p.eta_initial, dtype=np.float64)
        temperature = np.full(nx * ny, p.temperature_initial, dtype=np.float64)
        dt = self.time_step_ns
        identity = sparse.identity(nx * ny, format="csc")
        thermal_laplacian = _laplacian_no_flux(grid, dx, dy)
        eta_laplacian, eta_source = _robin_laplacian(
            grid, dx, dy, p.effective_boundary_length, p.eta_surrounding
        )
        heat_loss = p.heat_transfer * self.heat_transfer_multiplier / p.lz
        thermal_matrix = (
            identity
            - dt * p.thermal_conductivity / p.volumetric_heat_capacity * thermal_laplacian
            + dt * heat_loss / p.volumetric_heat_capacity * identity
        ).tocsc()
        eta_matrix = (
            identity - dt * p.structural_mobility * p.structural_gradient * eta_laplacian
        ).tocsc()
        solve_temperature = factorized(thermal_matrix)
        solve_eta_diffusion = factorized(eta_matrix)
        resistance_dimensionless = p.resistor * self.series_resistance_ohm / 5.0e5
        current_unit_amp = (1.3806504e-23 * 338.0 / 1.0e-3) / 1.0e-9

        saved_time: list[float] = []
        saved_eta: list[FloatArray] = []
        saved_mu: list[FloatArray] = []
        saved_temperature: list[FloatArray] = []
        saved_phi: list[FloatArray] = []
        saved_voltage: list[float] = []
        saved_current: list[float] = []
        balance_history: list[dict[str, float]] = []

        def electric_state(time_value: float) -> tuple[FloatArray, float, float, FloatArray]:
            mu_value = stable_mu_equilibrium(p, eta, temperature, tc_variance)
            sigma_x, sigma_y = _conductivity(p, mu_value, temperature)
            unit_phi, conductance = _unit_electric_solution(
                grid, dx, dy, p.lz, sigma_x, sigma_y
            )
            drive = float(
                pulse_train_voltage(
                    np.asarray([time_value]), amplitude=self.drive_voltage_v / 1.0e-3
                )[0]
            )
            device = drive / (1.0 + resistance_dimensionless * conductance)
            current = conductance * device
            circuit_residual = abs(drive - device - resistance_dimensionless * current) / max(abs(drive), 1.0)
            phi_value = unit_phi * device
            phi_grid = phi_value.reshape(ny, nx)
            edge_y, edge_x = np.gradient(phi_grid, dy, dx, edge_order=1)
            joule = sigma_x.reshape(ny, nx) * edge_x**2 + sigma_y.reshape(ny, nx) * edge_y**2
            return phi_value, device, current, joule.ravel(), circuit_residual

        def save(time_value: float, phi: FloatArray, device: float, current: float) -> None:
            saved_time.append(time_value)
            saved_eta.append(eta.copy())
            saved_mu.append(stable_mu_equilibrium(p, eta, temperature, tc_variance))
            saved_temperature.append(temperature.copy() * 338.0)
            saved_phi.append(phi.copy() * 1.0e-3)
            saved_voltage.append(device * 1.0e-3)
            saved_current.append(current * current_unit_amp)

        phi, device, current, _, circuit_residual = electric_state(0.0)
        balance_history.append(
            {"time_ns": 0.0, "electric": circuit_residual, "thermal": 0.0, "phase": 0.0}
        )
        save(0.0, phi, device, current)
        total_steps = int(round(self.end_time_ns / dt))
        for step in range(1, total_steps + 1):
            time_value = step * dt
            _, _, _, joule, _ = electric_state(time_value)
            old_temperature = temperature.copy()
            thermal_rhs = (
                old_temperature
                + dt * joule / p.volumetric_heat_capacity
                + dt * heat_loss / p.volumetric_heat_capacity * p.substrate_temperature
            )
            temperature = np.asarray(solve_temperature(thermal_rhs), dtype=np.float64)
            thermal_residual = thermal_matrix @ temperature - thermal_rhs
            thermal_violation = float(
                np.max(np.abs(thermal_residual)) / max(float(np.max(np.abs(thermal_rhs))), 1.0)
            )

            reacted_eta, reaction_violation = _reaction_step(
                p, eta, temperature, tc_variance, dt
            )
            eta_rhs = reacted_eta + dt * p.structural_mobility * p.structural_gradient * eta_source
            eta = np.asarray(solve_eta_diffusion(eta_rhs), dtype=np.float64)
            diffusion_residual = eta_matrix @ eta - eta_rhs
            phase_violation = max(
                reaction_violation,
                float(np.max(np.abs(diffusion_residual)) / max(float(np.max(np.abs(eta_rhs))), 1.0)),
            )
            if not np.all(np.isfinite(eta)) or not np.all(np.isfinite(temperature)):
                raise RuntimeError("QPOP-R3-v1 produced a non-finite state")
            phi, device, current, _, circuit_residual = electric_state(time_value)
            balance_history.append(
                {
                    "time_ns": time_value,
                    "electric": circuit_residual,
                    "thermal": thermal_violation,
                    "phase": phase_violation,
                }
            )
            if step % self.save_every == 0 or step == total_steps:
                save(time_value, phi, device, current)

        max_violation = max(
            max(record["electric"], record["thermal"], record["phase"])
            for record in balance_history
        )
        return ReducedOracleResult(
            time_ns=np.asarray(saved_time, dtype=np.float64),
            nodes=nodes,
            eta=np.stack(saved_eta),
            mu=np.stack(saved_mu),
            temperature=np.stack(saved_temperature),
            electric_potential=np.stack(saved_phi),
            device_voltage=np.asarray(saved_voltage, dtype=np.float64),
            current_amp=np.asarray(saved_current, dtype=np.float64),
            balance_history=balance_history,
            max_balance_violation=float(max_violation),
        )
