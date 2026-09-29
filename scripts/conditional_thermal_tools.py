"""Fixed-input thermal convolution; no source-trajectory or hysteresis solver.

Times, powers, heat capacities and temperatures are SI quantities.  The
quadrature is applied separately on every native-output / forcing-breakpoint
interval.  Four points are the production rule; eight points are the single
permitted numerical check.  Neither rule adapts its mesh or its order.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

import numpy as np
from numpy.polynomial.legendre import leggauss

ArrayFunction = Callable[[np.ndarray], np.ndarray]


@dataclass(frozen=True)
class ConvolutionResult:
    """Solution of x' + A x = f; all arrays are detached FP64 numbers."""

    values: np.ndarray
    segment_time_s: np.ndarray
    segment_values: np.ndarray
    gauss_order: int
    forcing_evaluations: int

    @property
    def segment_count(self) -> int:
        return self.segment_time_s.size - 1


@dataclass(frozen=True)
class ThermalResponse:
    temperature_K: np.ndarray
    evolution: ConvolutionResult
    capacitor_energy_J: np.ndarray | None


def thermal_matrix(sth: float, cth: float, n_devices: int, eta: float = 0.) -> np.ndarray:
    """Return the frozen single-node or coupled two-node A matrix in s^-1."""
    if not np.isfinite(sth) or not np.isfinite(cth) or sth <= 0. or cth <= 0.:
        raise ValueError("Positive finite SI thermal conductance and capacity required")
    if n_devices == 1:
        if eta != 0.:
            raise ValueError("Single-node thermal matrix has no coupling")
        return np.array([[sth / cth]], dtype=np.float64)
    if n_devices == 2 and np.isfinite(eta) and 0. <= eta < 1.:
        return (sth / cth) * np.array([[1., -eta], [-eta, 1.]], dtype=np.float64)
    raise ValueError("Only one or two nodes with 0 <= eta < 1 are supported")


def segment_grid(time_s: np.ndarray, breakpoints_s: Iterable[float] = ()) -> np.ndarray:
    """Exact sorted union: no rounding or merging of distinct saved times."""
    time = np.asarray(time_s, dtype=np.float64)
    breaks = np.asarray(list(breakpoints_s), dtype=np.float64)
    if time.ndim != 1 or time.size < 2 or not np.all(np.isfinite(time)):
        raise ValueError("At least two finite native times are required")
    if np.any(np.diff(time) <= 0.):
        raise ValueError("Native times must be strictly increasing")
    if breaks.ndim != 1 or not np.all(np.isfinite(breaks)):
        raise ValueError("Breakpoints must be a finite one-dimensional sequence")
    breaks = breaks[(breaks >= time[0]) & (breaks <= time[-1])]
    return np.unique(np.concatenate((time, breaks)))


def _rows(function: ArrayFunction, time: np.ndarray, n_devices: int) -> np.ndarray:
    result = np.asarray(function(time), dtype=np.float64)
    if n_devices == 1 and result.shape == time.shape:
        result = result[:, None]
    if result.shape != (time.size, n_devices):
        raise ValueError(f"Forcing shape {result.shape} differs from {(time.size, n_devices)}")
    if not np.all(np.isfinite(result)):
        raise ValueError("Forcing is non-finite; no clipping or extrapolation rescue is allowed")
    return result


def _node_vector(value: np.ndarray | float, n_devices: int, name: str) -> np.ndarray:
    result = np.broadcast_to(np.asarray(value, dtype=np.float64), (n_devices,)).copy()
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must be finite")
    return result


def linear_convolution(
    time_s: np.ndarray,
    A: np.ndarray,
    initial: np.ndarray | float,
    forcing: ArrayFunction,
    *,
    breakpoints_s: Iterable[float] = (),
    gauss_order: int = 4,
) -> ConvolutionResult:
    """Stable matrix-exponential recurrence at the full segment union.

    ``forcing`` receives a flat vector of SI times and returns (N, nodes).
    The symmetric A is diagonalized once.  Gaussian forcing integrals are
    vectorized; only the causal recurrence is sequential.  Native output times
    are selected exactly, never reconstructed from surrounding temperatures.
    """
    if gauss_order not in (4, 8):
        raise ValueError("The frozen rules are four-point production and eight-point verification")
    A = np.asarray(A, dtype=np.float64)
    if A.shape not in ((1, 1), (2, 2)) or not np.all(np.isfinite(A)):
        raise ValueError("A must be a finite one-node or two-node matrix")
    if not np.array_equal(A, A.T):
        raise ValueError("The frozen thermal matrix must be symmetric")
    eigenvalues, eigenvectors = np.linalg.eigh(A)
    if np.any(eigenvalues <= 0.):
        raise ValueError("The frozen thermal matrix must have positive eigenvalues")
    n_devices = A.shape[0]
    initial = _node_vector(initial, n_devices, "Initial state")
    time = np.asarray(time_s, dtype=np.float64)
    segment_time = segment_grid(time, breakpoints_s)
    dt = np.diff(segment_time)
    nodes, weights = leggauss(gauss_order)
    fraction = .5 * (nodes + 1.)
    query = segment_time[:-1, None] + dt[:, None] * fraction[None, :]
    sample = _rows(forcing, query.ravel(), n_devices).reshape(-1, gauss_order, n_devices)
    modal_forcing = sample @ eigenvectors
    propagation = np.exp(-dt[:, None] * eigenvalues[None, :])
    kernel = np.exp(-dt[:, None, None] * (1. - fraction)[None, :, None]
                    * eigenvalues[None, None, :])
    integral = .5 * dt[:, None] * np.sum(weights[None, :, None] * kernel * modal_forcing, axis=1)
    modal_state = np.empty((segment_time.size, n_devices), dtype=np.float64)
    modal_state[0] = initial @ eigenvectors
    for j in range(dt.size):
        modal_state[j + 1] = propagation[j] * modal_state[j] + integral[j]
    segment_values = modal_state @ eigenvectors.T
    # Do not perturb a legal initial condition by eigensystem roundoff.
    segment_values[0] = initial
    if not np.all(np.isfinite(segment_values)):
        raise FloatingPointError("Thermal response became non-finite")
    indices = np.searchsorted(segment_time, time)
    if not np.array_equal(segment_time[indices], time):
        raise RuntimeError("Native times missing from integration partition")
    return ConvolutionResult(segment_values[indices].copy(), segment_time,
                             segment_values, gauss_order, query.size)


def power_response(
    time_s: np.ndarray, A: np.ndarray, power: ArrayFunction, *,
    cth: float, T_base: float, T_initial: np.ndarray | float,
    breakpoints_s: Iterable[float] = (), gauss_order: int = 4,
) -> ThermalResponse:
    """Q_ref: theta' + A theta = q/Cth; negative input is preserved."""
    if not np.isfinite(cth) or cth <= 0. or not np.isfinite(T_base):
        raise ValueError("Finite base temperature and positive SI capacity required")
    initial = _node_vector(T_initial, np.asarray(A).shape[0], "Initial temperature") - T_base
    result = linear_convolution(time_s, A, initial,
                                lambda t: np.asarray(power(t), dtype=np.float64) / cth,
                                breakpoints_s=breakpoints_s, gauss_order=gauss_order)
    temperature = T_base + result.values
    temperature[0] = np.asarray(T_initial, dtype=np.float64)
    return ThermalResponse(temperature, result, None)


def voltage_response(
    time_s: np.ndarray, A: np.ndarray, voltage: ArrayFunction, *,
    V_in: np.ndarray | float, R_load: float, C: float,
    cth: float, T_base: float, T_initial: np.ndarray | float,
    breakpoints_s: Iterable[float] = (), gauss_order: int = 4,
) -> ThermalResponse:
    """Derivative-free voltage forcing using y=Cth*(T-Tbase)+C*p^2/2.

    All products/squares are nodewise except A@E, which includes thermal
    coupling.  The capacitor contribution is removed again at every readout;
    it is never added to Joule heating a second time.
    """
    if (not np.isfinite(R_load) or R_load <= 0. or not np.isfinite(C) or C <= 0.
            or not np.isfinite(cth) or cth <= 0. or not np.isfinite(T_base)):
        raise ValueError("Positive finite SI R/C/Cth and finite base temperature required")
    A = np.asarray(A, dtype=np.float64)
    n_devices = A.shape[0]
    vin = _node_vector(V_in, n_devices, "Source voltage")
    initial_T = _node_vector(T_initial, n_devices, "Initial temperature")
    time = np.asarray(time_s, dtype=np.float64)
    native_voltage = _rows(voltage, time, n_devices)
    energy = .5 * C * native_voltage ** 2

    def forcing(t: np.ndarray) -> np.ndarray:
        p = _rows(voltage, t, n_devices)
        E = .5 * C * p ** 2
        F = p * (vin - p) / R_load
        return F + E @ A.T

    result = linear_convolution(time, A, cth * (initial_T - T_base) + energy[0], forcing,
                                breakpoints_s=breakpoints_s, gauss_order=gauss_order)
    temperature = T_base + (result.values - energy) / cth
    temperature[0] = initial_T
    return ThermalResponse(temperature, result, energy)
