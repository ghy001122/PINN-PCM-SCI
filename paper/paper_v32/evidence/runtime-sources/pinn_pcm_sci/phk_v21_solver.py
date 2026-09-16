"""Non-voting PHK-V2.1 phase-solver candidates.

This module is intentionally separate from :mod:`pinn_pcm_sci.phk_benchmark`.
The frozen PHK-V2 implementation and its failed intent therefore remain byte-
addressable historical evidence.  These routines are engineering candidates
only until one scheme is selected and copied by identity into a new PHK-V2.1
scientific contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Any, Mapping

import numpy as np
from numpy.typing import NDArray
from scipy import optimize, sparse
from scipy.sparse import linalg as sparse_linalg

from .phk_benchmark import PhkGrid, _phase_residual_and_jacobian


FloatArray = NDArray[np.float64]


class PhkV21PhaseAlgorithm(str, Enum):
    TRUST_REGION_REFLECTIVE_PHASE = "TRUST_REGION_REFLECTIVE_PHASE"
    LOGIT_NEWTON_ANALYTIC_JACOBIAN = "LOGIT_NEWTON_ANALYTIC_JACOBIAN"
    PSEUDO_TRANSIENT_NEWTON = "PSEUDO_TRANSIENT_NEWTON"


@dataclass(frozen=True)
class PhkV21PhaseSolve:
    algorithm: str
    phase: FloatArray
    converged: bool
    iterations: int
    residual_evaluations: int
    jacobian_evaluations: int
    linear_solves: int
    final_residual_inf: float
    residual_history: tuple[float, ...]
    accepted_step_history: tuple[float, ...]
    jacobian_diagonal_scale_ratio_history: tuple[float, ...]
    bound_rejections: int
    decrease_rejections: int
    output_clipping_count: int


def _maximum_absolute(value: FloatArray) -> float:
    return float(np.max(np.abs(value))) if value.size else 0.0


def _diagonal_scale_ratio(jacobian: sparse.spmatrix) -> float:
    diagonal = np.abs(np.asarray(jacobian.diagonal(), dtype=np.float64))
    positive = diagonal[diagonal > 0.0]
    if positive.size == 0:
        return math.inf
    return float(np.max(positive) / np.min(positive))


def _validate_inputs(
    *,
    phase_old: FloatArray,
    initial_guess: FloatArray,
    temperature: FloatArray,
    grid: PhkGrid,
    lower_bound: float,
    upper_bound: float,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    old = np.asarray(phase_old, dtype=np.float64)
    guess = np.asarray(initial_guess, dtype=np.float64)
    thermal = np.asarray(temperature, dtype=np.float64)
    expected = (grid.cell_count,)
    if old.shape != expected or guess.shape != expected or thermal.shape != expected:
        raise ValueError("PHK-V2.1 phase candidate array shape mismatch")
    if not all(np.isfinite(item).all() for item in (old, guess, thermal)):
        raise ValueError("PHK-V2.1 phase candidate inputs must be finite")
    if not (math.isfinite(lower_bound) and math.isfinite(upper_bound)):
        raise ValueError("PHK-V2.1 phase bounds must be finite")
    if lower_bound >= upper_bound:
        raise ValueError("PHK-V2.1 phase lower bound must be below upper bound")
    if np.any(old < lower_bound) or np.any(old > upper_bound):
        raise ValueError("PHK-V2.1 previous phase is outside the physical range")
    if np.any(guess < lower_bound) or np.any(guess > upper_bound):
        raise ValueError("PHK-V2.1 initial phase guess is outside the physical range")
    return old, guess, thermal


def _residual_jacobian(
    phase: FloatArray,
    *,
    phase_old: FloatArray,
    temperature: FloatArray,
    grid: PhkGrid,
    dt: float,
    coefficients: Mapping[str, Any],
    interface_width: float,
) -> tuple[FloatArray, sparse.csr_matrix]:
    return _phase_residual_and_jacobian(
        phase,
        phase_old=phase_old,
        temperature=temperature,
        grid=grid,
        dt=dt,
        coefficients=coefficients,
        interface_width=interface_width,
    )


def _solve_trust_region(
    *,
    phase_old: FloatArray,
    initial_guess: FloatArray,
    temperature: FloatArray,
    grid: PhkGrid,
    dt: float,
    coefficients: Mapping[str, Any],
    interface_width: float,
    tolerance: float,
    lower_bound: float,
    upper_bound: float,
) -> PhkV21PhaseSolve:
    residual_history: list[float] = []
    scale_history: list[float] = []
    residual_evaluations = 0
    jacobian_evaluations = 0

    def residual(phase: FloatArray) -> FloatArray:
        nonlocal residual_evaluations
        value, _ = _residual_jacobian(
            phase,
            phase_old=phase_old,
            temperature=temperature,
            grid=grid,
            dt=dt,
            coefficients=coefficients,
            interface_width=interface_width,
        )
        residual_evaluations += 1
        residual_history.append(_maximum_absolute(value))
        return value / tolerance

    def jacobian(phase: FloatArray) -> sparse.csr_matrix:
        nonlocal jacobian_evaluations
        _, value = _residual_jacobian(
            phase,
            phase_old=phase_old,
            temperature=temperature,
            grid=grid,
            dt=dt,
            coefficients=coefficients,
            interface_width=interface_width,
        )
        jacobian_evaluations += 1
        scale_history.append(_diagonal_scale_ratio(value))
        return value / tolerance

    result = optimize.least_squares(
        residual,
        initial_guess,
        jac=jacobian,
        bounds=(lower_bound, upper_bound),
        method="trf",
        x_scale="jac",
        ftol=1.0e-14,
        xtol=1.0e-14,
        gtol=1.0e-14,
        max_nfev=120,
    )
    final, _ = _residual_jacobian(
        np.asarray(result.x, dtype=np.float64),
        phase_old=phase_old,
        temperature=temperature,
        grid=grid,
        dt=dt,
        coefficients=coefficients,
        interface_width=interface_width,
    )
    norm = _maximum_absolute(final)
    if norm > tolerance:
        raise RuntimeError(
            "PHK-V2.1 trust-region phase solve did not meet the frozen residual tolerance"
        )
    return PhkV21PhaseSolve(
        algorithm=PhkV21PhaseAlgorithm.TRUST_REGION_REFLECTIVE_PHASE.value,
        phase=np.asarray(result.x, dtype=np.float64),
        converged=True,
        iterations=int(result.njev or 0),
        residual_evaluations=residual_evaluations + 1,
        jacobian_evaluations=jacobian_evaluations,
        linear_solves=int(result.njev or 0),
        final_residual_inf=norm,
        residual_history=tuple(residual_history) + (norm,),
        accepted_step_history=(),
        jacobian_diagonal_scale_ratio_history=tuple(scale_history),
        bound_rejections=0,
        decrease_rejections=0,
        output_clipping_count=0,
    )


def _stable_sigmoid(value: FloatArray) -> FloatArray:
    result = np.empty_like(value)
    positive = value >= 0.0
    result[positive] = 1.0 / (1.0 + np.exp(-value[positive]))
    exp_value = np.exp(value[~positive])
    result[~positive] = exp_value / (1.0 + exp_value)
    return result


def _solve_logit_newton(
    *,
    phase_old: FloatArray,
    initial_guess: FloatArray,
    temperature: FloatArray,
    grid: PhkGrid,
    dt: float,
    coefficients: Mapping[str, Any],
    interface_width: float,
    tolerance: float,
    lower_bound: float,
    upper_bound: float,
) -> PhkV21PhaseSolve:
    span = upper_bound - lower_bound
    normalized = (initial_guess - lower_bound) / span
    if np.any(normalized <= 0.0) or np.any(normalized >= 1.0):
        raise RuntimeError("PHK-V2.1 logit phase solver requires a strictly interior state")
    latent = np.log(normalized) - np.log1p(-normalized)
    residual_history: list[float] = []
    step_history: list[float] = []
    scale_history: list[float] = []
    residual_evaluations = 0
    jacobian_evaluations = 0
    linear_solves = 0
    decrease_rejections = 0
    maximum_iterations = 30
    minimum_step = 2.0 ** -20

    for iteration in range(maximum_iterations + 1):
        unit = _stable_sigmoid(latent)
        phase = lower_bound + span * unit
        residual, jacobian = _residual_jacobian(
            phase,
            phase_old=phase_old,
            temperature=temperature,
            grid=grid,
            dt=dt,
            coefficients=coefficients,
            interface_width=interface_width,
        )
        residual_evaluations += 1
        jacobian_evaluations += 1
        norm = _maximum_absolute(residual)
        residual_history.append(norm)
        scale_history.append(_diagonal_scale_ratio(jacobian))
        if norm <= tolerance:
            return PhkV21PhaseSolve(
                algorithm=PhkV21PhaseAlgorithm.LOGIT_NEWTON_ANALYTIC_JACOBIAN.value,
                phase=phase,
                converged=True,
                iterations=iteration,
                residual_evaluations=residual_evaluations,
                jacobian_evaluations=jacobian_evaluations,
                linear_solves=linear_solves,
                final_residual_inf=norm,
                residual_history=tuple(residual_history),
                accepted_step_history=tuple(step_history),
                jacobian_diagonal_scale_ratio_history=tuple(scale_history),
                bound_rejections=0,
                decrease_rejections=decrease_rejections,
                output_clipping_count=0,
            )
        if iteration == maximum_iterations:
            break
        derivative = span * unit * (1.0 - unit)
        transformed = jacobian @ sparse.diags(derivative)
        update = sparse_linalg.spsolve(transformed.tocsc(), -residual).astype(
            np.float64
        )
        linear_solves += 1
        step = 1.0
        accepted = False
        while step >= minimum_step:
            candidate_latent = latent + step * update
            candidate_unit = _stable_sigmoid(candidate_latent)
            candidate_phase = lower_bound + span * candidate_unit
            candidate_residual, _ = _residual_jacobian(
                candidate_phase,
                phase_old=phase_old,
                temperature=temperature,
                grid=grid,
                dt=dt,
                coefficients=coefficients,
                interface_width=interface_width,
            )
            residual_evaluations += 1
            if _maximum_absolute(candidate_residual) < norm:
                latent = candidate_latent
                step_history.append(step)
                accepted = True
                break
            decrease_rejections += 1
            step *= 0.5
        if not accepted:
            raise RuntimeError(
                "PHK-V2.1 logit phase Newton line search reached its frozen minimum step"
            )
    raise RuntimeError("PHK-V2.1 logit phase Newton exceeded its frozen iteration limit")


def _solve_pseudo_transient(
    *,
    phase_old: FloatArray,
    initial_guess: FloatArray,
    temperature: FloatArray,
    grid: PhkGrid,
    dt: float,
    coefficients: Mapping[str, Any],
    interface_width: float,
    tolerance: float,
    lower_bound: float,
    upper_bound: float,
) -> PhkV21PhaseSolve:
    phase = initial_guess.copy()
    shift = 1.0e-3
    residual_history: list[float] = []
    step_history: list[float] = []
    scale_history: list[float] = []
    residual_evaluations = 0
    jacobian_evaluations = 0
    linear_solves = 0
    bound_rejections = 0
    decrease_rejections = 0
    maximum_iterations = 30
    minimum_step = 2.0 ** -20

    for iteration in range(maximum_iterations + 1):
        residual, jacobian = _residual_jacobian(
            phase,
            phase_old=phase_old,
            temperature=temperature,
            grid=grid,
            dt=dt,
            coefficients=coefficients,
            interface_width=interface_width,
        )
        residual_evaluations += 1
        jacobian_evaluations += 1
        norm = _maximum_absolute(residual)
        residual_history.append(norm)
        scale_history.append(_diagonal_scale_ratio(jacobian))
        if norm <= tolerance:
            return PhkV21PhaseSolve(
                algorithm=PhkV21PhaseAlgorithm.PSEUDO_TRANSIENT_NEWTON.value,
                phase=phase,
                converged=True,
                iterations=iteration,
                residual_evaluations=residual_evaluations,
                jacobian_evaluations=jacobian_evaluations,
                linear_solves=linear_solves,
                final_residual_inf=norm,
                residual_history=tuple(residual_history),
                accepted_step_history=tuple(step_history),
                jacobian_diagonal_scale_ratio_history=tuple(scale_history),
                bound_rejections=bound_rejections,
                decrease_rejections=decrease_rejections,
                output_clipping_count=0,
            )
        if iteration == maximum_iterations:
            break
        shifted = jacobian + shift * sparse.eye(grid.cell_count, format="csr")
        update = sparse_linalg.spsolve(shifted.tocsc(), -residual).astype(np.float64)
        linear_solves += 1
        step = 1.0
        accepted = False
        while step >= minimum_step:
            candidate = phase + step * update
            if np.any(candidate < lower_bound) or np.any(candidate > upper_bound):
                bound_rejections += 1
                step *= 0.5
                continue
            candidate_residual, _ = _residual_jacobian(
                candidate,
                phase_old=phase_old,
                temperature=temperature,
                grid=grid,
                dt=dt,
                coefficients=coefficients,
                interface_width=interface_width,
            )
            residual_evaluations += 1
            if _maximum_absolute(candidate_residual) < norm:
                phase = candidate
                step_history.append(step)
                shift = max(shift * 0.3, 1.0e-12)
                accepted = True
                break
            decrease_rejections += 1
            step *= 0.5
        if not accepted:
            shift = min(shift * 10.0, 1.0e12)
            if shift >= 1.0e12:
                raise RuntimeError(
                    "PHK-V2.1 pseudo-transient phase solve exhausted its frozen shift"
                )
    raise RuntimeError(
        "PHK-V2.1 pseudo-transient phase solve exceeded its frozen iteration limit"
    )


def solve_phase_candidate(
    *,
    algorithm: PhkV21PhaseAlgorithm,
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
) -> PhkV21PhaseSolve:
    """Run one frozen non-voting phase-solver candidate without clipping."""

    old, guess, thermal = _validate_inputs(
        phase_old=phase_old,
        initial_guess=initial_guess,
        temperature=temperature,
        grid=grid,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
    )
    if not (math.isfinite(dt) and dt > 0.0):
        raise ValueError("PHK-V2.1 phase dt must be positive and finite")
    tolerance = float(solver["transport_newton_residual_tolerance"])
    common = dict(
        phase_old=old,
        initial_guess=guess,
        temperature=thermal,
        grid=grid,
        dt=float(dt),
        coefficients=coefficients,
        interface_width=float(interface_width),
        tolerance=tolerance,
        lower_bound=float(lower_bound),
        upper_bound=float(upper_bound),
    )
    if algorithm is PhkV21PhaseAlgorithm.TRUST_REGION_REFLECTIVE_PHASE:
        return _solve_trust_region(**common)
    if algorithm is PhkV21PhaseAlgorithm.LOGIT_NEWTON_ANALYTIC_JACOBIAN:
        return _solve_logit_newton(**common)
    if algorithm is PhkV21PhaseAlgorithm.PSEUDO_TRANSIENT_NEWTON:
        return _solve_pseudo_transient(**common)
    raise ValueError(f"unsupported PHK-V2.1 phase algorithm: {algorithm}")
