"""Independent four-field oracle for the bounded QPOP-R4-v1 reduction.

The public seam is :class:`DynamicOrderOracleCase`.  It hides a split finite-
volume solve for quasi-static electric potential, implicit temperature, and
coupled implicit structural/electronic Allen-Cahn dynamics.  Unlike R3, the
electronic order parameter is a history-carrying state and is never projected
onto the globally lowest Landau basin.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from numpy.typing import NDArray
from scipy import sparse
from scipy.sparse.linalg import factorized

from .artifacts import CaseArtifact
from .qpop_physics import QPopParameters
from .reduced_oracle import (
    ReducedOracleGrid,
    ReducedOracleResult,
    _conductivity,
    _df_deta,
    _df_dmu,
    _fermi,
    _laplacian_no_flux,
    _robin_laplacian,
    _tc_variance,
    _unit_electric_solution,
    pulse_train_voltage,
)


FloatArray = NDArray[np.float64]


def _dfermi(gamma: FloatArray) -> FloatArray:
    gamma = np.asarray(gamma, dtype=np.float64)
    clipped = np.clip(-gamma, -100.0, 100.0)
    regular_fermi = 1.0 / (
        np.exp(clipped)
        + 3.0 * math.sqrt(math.pi) / 4.0 * (4.0 + gamma**2) ** (-0.75)
    )
    regular = regular_fermi**2 * (
        np.exp(clipped)
        + 9.0
        * math.sqrt(math.pi)
        / 8.0
        * (4.0 + gamma**2) ** (-1.75)
        * gamma
    )
    high = 2.0 / math.sqrt(math.pi) * gamma * (4.0 + gamma**2) ** (-0.25)
    return np.where(gamma < -100.0, 0.0, np.where(gamma > 100.0, high, regular))


def _electronic_force_and_derivative(
    p: QPopParameters,
    eta: FloatArray,
    mu: FloatArray,
    temperature: FloatArray,
    tc_variance: FloatArray,
    potential: FloatArray,
) -> tuple[FloatArray, FloatArray]:
    safe_temperature = np.maximum(p.kb * temperature, 1.0e-12)
    gap = p.chi * mu**2 / 2.0
    gamma_intrinsic = -gap / safe_temperature
    gamma_electron = -(gap - p.charge * potential) / safe_temperature
    gamma_hole = -(gap + p.charge * potential) / safe_temperature
    intrinsic = p.electron_density_of_states * _fermi(gamma_intrinsic)
    electron = p.electron_density_of_states * _fermi(gamma_electron)
    hole = p.hole_density_of_states * _fermi(gamma_hole)
    excess = electron + hole - 2.0 * intrinsic
    carrier_force = p.chi * mu * excess

    dgamma = -p.chi * mu / safe_temperature
    dintrinsic = p.electron_density_of_states * _dfermi(gamma_intrinsic) * dgamma
    delectron = p.electron_density_of_states * _dfermi(gamma_electron) * dgamma
    dhole = p.hole_density_of_states * _dfermi(gamma_hole) * dgamma
    dexcess = delectron + dhole - 2.0 * dintrinsic
    dcarrier = p.chi * excess + p.chi * mu * dexcess

    landau = _df_dmu(p, eta, mu, temperature, tc_variance)
    dlandau = (
        p.au1 * (temperature - p.t2 - tc_variance) / p.tc
        + 3.0 * p.au2 * mu**2
        + 5.0 * p.au3 * mu**4
        - p.gnu2 * eta**2
    )
    return landau + carrier_force, dlandau + dcarrier


def _coupled_reaction_step(
    p: QPopParameters,
    eta_old: FloatArray,
    mu_old: FloatArray,
    temperature: FloatArray,
    tc_variance: FloatArray,
    potential: FloatArray,
    dt: float,
) -> tuple[FloatArray, FloatArray, float, float]:
    eta = eta_old.copy()
    mu = mu_old.copy()
    eta_residual = np.zeros_like(eta)
    mu_residual = np.zeros_like(mu)
    for _ in range(64):
        eta_force = _df_deta(p, eta, mu, temperature, tc_variance)
        mu_force, dmu_force = _electronic_force_and_derivative(
            p, eta, mu, temperature, tc_variance, potential
        )
        eta_residual = (
            eta - eta_old + dt * 2.0 * p.structural_mobility * eta_force
        )
        mu_residual = mu - mu_old + dt * 2.0 * p.electronic_mobility * mu_force
        if max(
            float(np.max(np.abs(eta_residual))),
            float(np.max(np.abs(mu_residual))),
        ) <= 1.0e-8:
            break

        cross = (
            p.gnu1
            - 2.0 * p.gnu2 * eta * mu
            + 1.5 * p.gnu3 * eta**2
        )
        j_eta_eta = 1.0 + dt * 2.0 * p.structural_mobility * (
            p.an1 * (temperature - p.t1 - tc_variance) / p.tc
            + 3.0 * p.an2 * eta**2
            + 5.0 * p.an3 * eta**4
            - p.gnu2 * mu**2
            + 3.0 * p.gnu3 * eta * mu
        )
        j_eta_mu = dt * 2.0 * p.structural_mobility * cross
        j_mu_eta = dt * 2.0 * p.electronic_mobility * cross
        j_mu_mu = 1.0 + dt * 2.0 * p.electronic_mobility * dmu_force
        determinant = j_eta_eta * j_mu_mu - j_eta_mu * j_mu_eta
        safe_determinant = np.where(
            np.abs(determinant) < 1.0e-12,
            np.copysign(1.0e-12, determinant + 1.0e-30),
            determinant,
        )
        delta_eta = (
            eta_residual * j_mu_mu - j_eta_mu * mu_residual
        ) / safe_determinant
        delta_mu = (
            j_eta_eta * mu_residual - j_mu_eta * eta_residual
        ) / safe_determinant
        eta -= np.clip(delta_eta, -0.15, 0.15)
        mu -= np.clip(delta_mu, -0.15, 0.15)
    else:
        raise RuntimeError("QPOP-R4-v1 coupled eta-mu reaction did not converge")

    eta_scale = max(float(np.max(np.abs(eta_old))), 1.0)
    mu_scale = max(float(np.max(np.abs(mu_old))), 1.0)
    return (
        eta,
        mu,
        float(np.max(np.abs(eta_residual)) / eta_scale),
        float(np.max(np.abs(mu_residual)) / mu_scale),
    )


def dynamic_result_to_artifact(
    result: ReducedOracleResult,
    *,
    grid: ReducedOracleGrid,
    case_id: str,
) -> CaseArtifact:
    if result.nodes.shape[0] != grid.nx * grid.ny:
        raise ValueError("result nodes do not match the registered R4 grid")
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
            for value in (
                120.0 * period,
                120.0 * period + 5.0,
                120.0 * period + 60.0,
                120.0 * period + 65.0,
            )
            if 0.0 <= value <= float(result.time_ns[-1])
        ),
        dtype=np.float64,
    )
    return CaseArtifact(
        case_id=case_id,
        physical_contract_id="qpop-r4-v1",
        evidence_identity="QPOP_R4_V1_DYNAMIC_ORDER_REDUCED_SYNTHETIC_ORACLE",
        nodes=result.nodes,
        cells=np.asarray(cells, dtype=np.int64),
        mesh_unit="nm",
        field_time=result.time_ns,
        circuit_time=result.time_ns,
        time_unit="ns",
        fields={
            "eta": result.eta,
            "mu": result.mu,
            "electric_potential": result.electric_potential,
            "temperature": result.temperature,
        },
        field_units={
            "eta": "1",
            "mu": "1",
            "electric_potential": "V",
            "temperature": "K",
        },
        breakpoints=breakpoints,
        circuit={
            "qpop_r4_device_voltage": result.device_voltage,
            "qpop_r4_current": result.current_amp,
        },
        circuit_units={
            "qpop_r4_device_voltage": "V",
            "qpop_r4_current": "A",
        },
    )


@dataclass(frozen=True)
class DynamicOrderOracleCase:
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
            raise ValueError("R4 time controls must be positive")
        if self.drive_voltage_v < 0.0 or self.series_resistance_ohm <= 0.0:
            raise ValueError("R4 electrical controls are invalid")
        if self.heat_transfer_multiplier <= 0.0 or self.save_every <= 0:
            raise ValueError("R4 thermal/save controls are invalid")
        steps = self.end_time_ns / self.time_step_ns
        if abs(steps - round(steps)) > 1.0e-10:
            raise ValueError("R4 end time must be an integer number of steps")

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
        mu = np.full(nx * ny, p.mu_initial, dtype=np.float64)
        temperature = np.full(nx * ny, p.temperature_initial, dtype=np.float64)
        dt = self.time_step_ns
        identity = sparse.identity(nx * ny, format="csc")
        thermal_laplacian = _laplacian_no_flux(grid, dx, dy)
        eta_laplacian, eta_source = _robin_laplacian(
            grid, dx, dy, p.effective_boundary_length, p.eta_surrounding
        )
        mu_laplacian, mu_source = _robin_laplacian(
            grid, dx, dy, p.effective_boundary_length, p.mu_surrounding
        )
        heat_loss = p.heat_transfer * self.heat_transfer_multiplier / p.lz
        thermal_matrix = (
            identity
            - dt
            * p.thermal_conductivity
            / p.volumetric_heat_capacity
            * thermal_laplacian
            + dt * heat_loss / p.volumetric_heat_capacity * identity
        ).tocsc()
        eta_matrix = (
            identity
            - dt * p.structural_mobility * p.structural_gradient * eta_laplacian
        ).tocsc()
        mu_matrix = (
            identity
            - dt * p.electronic_mobility * p.electronic_gradient * mu_laplacian
        ).tocsc()
        solve_temperature = factorized(thermal_matrix)
        solve_eta_diffusion = factorized(eta_matrix)
        solve_mu_diffusion = factorized(mu_matrix)
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

        def electric_state(
            time_value: float,
        ) -> tuple[FloatArray, float, float, FloatArray, float]:
            sigma_x, sigma_y = _conductivity(p, mu, temperature)
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
            circuit_residual = abs(
                drive - device - resistance_dimensionless * current
            ) / max(abs(drive), 1.0)
            phi_value = unit_phi * device
            phi_grid = phi_value.reshape(ny, nx)
            edge_y, edge_x = np.gradient(phi_grid, dy, dx, edge_order=1)
            joule = (
                sigma_x.reshape(ny, nx) * edge_x**2
                + sigma_y.reshape(ny, nx) * edge_y**2
            )
            return phi_value, device, current, joule.ravel(), circuit_residual

        def save(
            time_value: float, phi: FloatArray, device: float, current: float
        ) -> None:
            saved_time.append(time_value)
            saved_eta.append(eta.copy())
            saved_mu.append(mu.copy())
            saved_temperature.append(temperature.copy() * 338.0)
            saved_phi.append(phi.copy() * 1.0e-3)
            saved_voltage.append(device * 1.0e-3)
            saved_current.append(current * current_unit_amp)

        phi, device, current, _, circuit_violation = electric_state(0.0)
        balance_history.append(
            {
                "time_ns": 0.0,
                "electric": circuit_violation,
                "thermal": 0.0,
                "structural": 0.0,
                "electronic": 0.0,
            }
        )
        save(0.0, phi, device, current)

        total_steps = int(round(self.end_time_ns / dt))
        for step in range(1, total_steps + 1):
            time_value = step * dt
            phi_for_reaction, _, _, joule, _ = electric_state(time_value)
            old_temperature = temperature.copy()
            thermal_rhs = (
                old_temperature
                + dt * joule / p.volumetric_heat_capacity
                + dt
                * heat_loss
                / p.volumetric_heat_capacity
                * p.substrate_temperature
            )
            temperature = np.asarray(solve_temperature(thermal_rhs), dtype=np.float64)
            thermal_residual = thermal_matrix @ temperature - thermal_rhs
            thermal_violation = float(
                np.max(np.abs(thermal_residual))
                / max(float(np.max(np.abs(thermal_rhs))), 1.0)
            )

            reacted_eta, reacted_mu, eta_reaction, mu_reaction = (
                _coupled_reaction_step(
                    p,
                    eta,
                    mu,
                    temperature,
                    tc_variance,
                    phi_for_reaction,
                    dt,
                )
            )
            eta_rhs = (
                reacted_eta
                + dt
                * p.structural_mobility
                * p.structural_gradient
                * eta_source
            )
            mu_rhs = (
                reacted_mu
                + dt
                * p.electronic_mobility
                * p.electronic_gradient
                * mu_source
            )
            eta = np.asarray(solve_eta_diffusion(eta_rhs), dtype=np.float64)
            mu = np.asarray(solve_mu_diffusion(mu_rhs), dtype=np.float64)
            eta_diffusion = eta_matrix @ eta - eta_rhs
            mu_diffusion = mu_matrix @ mu - mu_rhs
            structural_violation = max(
                eta_reaction,
                float(
                    np.max(np.abs(eta_diffusion))
                    / max(float(np.max(np.abs(eta_rhs))), 1.0)
                ),
            )
            electronic_violation = max(
                mu_reaction,
                float(
                    np.max(np.abs(mu_diffusion))
                    / max(float(np.max(np.abs(mu_rhs))), 1.0)
                ),
            )
            if not (
                np.all(np.isfinite(eta))
                and np.all(np.isfinite(mu))
                and np.all(np.isfinite(temperature))
            ):
                raise RuntimeError("QPOP-R4-v1 produced a non-finite state")
            phi, device, current, _, circuit_violation = electric_state(time_value)
            balance_history.append(
                {
                    "time_ns": time_value,
                    "electric": circuit_violation,
                    "thermal": thermal_violation,
                    "structural": structural_violation,
                    "electronic": electronic_violation,
                }
            )
            if step % self.save_every == 0 or step == total_steps:
                save(time_value, phi, device, current)

        max_violation = max(
            max(value for key, value in record.items() if key != "time_ns")
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
