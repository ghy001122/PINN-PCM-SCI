"""Saved-polynomial and saved-power energy accounting; no system integration.

Public energy functions return FP64 arrays of shape ``(n_devices,)`` in joules,
including a one-element array for scalar signals. The Euler checker returns one
JSON-compatible dictionary per device. Its tolerance checks algebra at FP64
operation scales, not numerical-solution accuracy or scientific sufficiency.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.interpolate import PPoly


EPS = np.finfo(np.float64).eps


def _matrix(values, name):
    values = np.asarray(values, dtype=np.float64)
    if values.ndim == 1:
        values = values[:, None]
    if values.ndim != 2 or not np.all(np.isfinite(values)):
        raise ValueError(f"{name} must be a finite time-by-device array")
    return values


def _time(t):
    t = np.asarray(t, dtype=np.float64)
    if t.ndim != 1 or len(t) < 2 or not np.all(np.isfinite(t)) or not np.all(np.diff(t) > 0):
        raise ValueError("Time must be finite and strictly increasing")
    return t


def _interval(left, right, lower, upper):
    left, right = float(left), float(right)
    if not np.isfinite(left) or not np.isfinite(right) or left > right:
        raise ValueError("Energy bounds must be finite and ordered")
    if left < lower or right > upper:
        raise ValueError("Energy integration does not extrapolate")
    return left, right


def _circuit(vin, rl, c, n_devices):
    vin = np.asarray(vin, dtype=np.float64)
    if vin.ndim > 1 or vin.size not in (1, n_devices) or not np.all(np.isfinite(vin)):
        raise ValueError("Constant input voltage must be scalar or one value per device")
    if not np.isfinite(rl) or rl <= 0 or not np.isfinite(c) or c <= 0:
        raise ValueError("Resistance and capacitance must be finite and positive")
    return np.broadcast_to(vin, (n_devices,)), float(rl), float(c)


def _sum_columns(values):
    """Use compensated summation so cancellation is not a summation-order claim."""
    return np.asarray([math.fsum(values[:, j]) for j in range(values.shape[1])])


def _poly_integral_between(coefficients, left, right):
    """Integrate descending-power coefficients on one local polynomial segment.

    Evaluate the antiderivative *difference* with factored power differences;
    this avoids subtracting two nearby antiderivative values for short slices.
    Coefficients may have trailing device columns.
    """
    degree = coefficients.shape[0] - 1
    terms = []
    for row, coefficient in enumerate(coefficients):
        power = degree - row + 1
        divided_difference = math.fsum(
            right ** (power - 1 - k) * left ** k for k in range(power)
        )
        terms.append(coefficient * ((right - left) / power) * divided_difference)
    return _sum_columns(np.asarray(terms))


def prediction_energy(pred, left, right, vin, rl, c):
    """Analytic device dissipation from an already saved piecewise cubic voltage.

    Required ``pred`` keys are ``polynomial_coefficients`` (4, intervals,
    devices), ``polynomial_breakpoints``, ``time_origin`` (seconds), and
    ``time_scale`` (seconds per internal time unit). Scalar PPoly coefficients
    (4, intervals) are also accepted. No prediction fitting occurs here.

    Return integral((Vin*p-p**2)/RL) - C/2*(p(right)**2-p(left)**2), in J.
    Every overlap with a real polynomial segment is integrated separately;
    p**2 is formed by coefficient convolution, not by squaring integral(p).
    """
    coeff = np.asarray(pred["polynomial_coefficients"], dtype=np.float64)
    if coeff.ndim == 2:
        coeff = coeff[:, :, None]
    breaks = _time(pred["polynomial_breakpoints"])
    if coeff.ndim != 3 or coeff.shape[:2] != (4, len(breaks) - 1) or not np.all(np.isfinite(coeff)):
        raise ValueError("Saved coefficients must describe finite piecewise cubics")
    origin, scale = float(pred["time_origin"]), float(pred["time_scale"])
    if not np.isfinite(origin) or not np.isfinite(scale) or scale <= 0:
        raise ValueError("Polynomial time origin/scale must be finite with positive scale")
    vin, rl, c = _circuit(vin, rl, c, coeff.shape[2])
    left, right = _interval(left, right, origin + scale * breaks[0], origin + scale * breaks[-1])
    if left == right:
        return np.zeros(coeff.shape[2], dtype=np.float64)
    a, b = (left - origin) / scale, (right - origin) / scale
    # Physical endpoint arithmetic can differ by one ulp after unit conversion.
    # These snaps only undo that representation issue after strict SI checks.
    if left == origin + scale * breaks[0]:
        a = breaks[0]
    if right == origin + scale * breaks[-1]:
        b = breaks[-1]
    integrals = []
    for segment in range(len(breaks) - 1):
        lo, hi = max(a, breaks[segment]), min(b, breaks[segment + 1])
        if hi <= lo:
            continue
        local_left, local_right = lo - breaks[segment], hi - breaks[segment]
        p = coeff[:, segment, :]
        p_squared = np.column_stack([np.convolve(p[:, j], p[:, j]) for j in range(p.shape[1])])
        p_integral = _poly_integral_between(p, local_left, local_right)
        square_integral = _poly_integral_between(p_squared, local_left, local_right)
        integrals.append(scale * (vin * p_integral - square_integral) / rl)
    pp = PPoly(coeff, breaks, extrapolate=False)
    pa, pb = pp(a), pp(b)
    # Factor the endpoint square difference to reduce cancellation.
    capacitor_change = 0.5 * c * (pb - pa) * (pb + pa)
    energy = _sum_columns(np.asarray(integrals)) - capacitor_change
    if not np.all(np.isfinite(energy)):
        raise FloatingPointError("Non-finite polynomial energy")
    return energy


def reference_energy(t, power, left, right):
    """Exact integral of the piecewise-linear *power* represented by saved samples.

    Pass same-time V*I_device as ``power``. Off-node endpoints interpolate power,
    never V and I separately. No extrapolation and no source reintegration.
    """
    t = _time(t)
    power = _matrix(power, "Power")
    if len(power) != len(t):
        raise ValueError("Power and time lengths differ")
    left, right = _interval(left, right, t[0], t[-1])
    if left == right:
        return np.zeros(power.shape[1], dtype=np.float64)
    inner = (t > left) & (t < right)
    knots = np.r_[left, t[inner], right]
    p_left = np.array([np.interp(left, t, power[:, j]) for j in range(power.shape[1])])
    p_right = np.array([np.interp(right, t, power[:, j]) for j in range(power.shape[1])])
    values = np.vstack((p_left, power[inner], p_right))
    return _sum_columns(0.5 * np.diff(knots)[:, None] * (values[:-1] + values[1:]))


def euler_energy_check(t, v, device, vin, rl, c, safety=64):
    """Check the Euler left-sum identity on complete saved native steps only.

    ``t,v,device`` must already be sliced to an endpoint-inclusive native window.
    Returned dictionaries contain per-device J values: left_J, trapezoid_J,
    trapezoid_minus_left_J, voltage_input_J (= sum h*v*(Vin-v)/RL),
    capacitor_change_J, discrete_correction_J (= +C/2 sum (delta v)**2),
    kappa_term_J (= sum h*v*kappa, which is SUBTRACTED in rhs_J), closure_error_J,
    tolerance_J and valid. The final sample is used for trapezoidal energy and
    the capacitor endpoint; it is not an additional Euler step.

    kappa is computed from the same saved numerical arrays. This is an algebra
    check only: independent KCL/source timing checks remain necessary. In
    particular, passing this identity does not certify that kappa is small.
    """
    t, v, device = _time(t), _matrix(v, "Voltage"), _matrix(device, "Device current")
    if v.shape != device.shape or len(v) != len(t):
        raise ValueError("Voltage, current and time shapes differ")
    if not np.isfinite(safety) or safety <= 0:
        raise ValueError("Safety factor must be finite and positive")
    vin, rl, c = _circuit(vin, rl, c, v.shape[1])
    h = np.diff(t)[:, None]
    dv = np.diff(v, axis=0)
    forward = dv / h
    load = (vin - v[:-1]) / rl
    kappa = load - device[:-1] - c * forward
    power = v * device
    left_terms = h * power[:-1]
    voltage_terms = h * v[:-1] * load
    correction_terms = 0.5 * c * dv * dv
    kappa_terms = h * v[:-1] * kappa
    trap_terms = 0.5 * h * (power[:-1] + power[1:])
    trap_delta_terms = 0.5 * h * np.diff(power, axis=0)
    left, voltage_input, correction, integrated_kappa, trapezoid, trap_delta = map(
        _sum_columns, (left_terms, voltage_terms, correction_terms, kappa_terms, trap_terms, trap_delta_terms)
    )
    capacitor_change = 0.5 * c * (v[-1] - v[0]) * (v[-1] + v[0])
    rhs = voltage_input - capacitor_change + correction - integrated_kappa
    closure = left - rhs

    # Fixed before real-data scoring: include the absolute scales of products,
    # branch subtraction and differencing, even when their resulting values
    # nearly cancel. fsum controls summation error; this factor is an FP64
    # engineering allowance, not a fitted relative-to-scientific-error gate.
    kappa_operation_scale = ((np.abs(vin) + np.abs(v[:-1])) / rl + np.abs(device[:-1])
                             + c * (np.abs(v[1:]) + np.abs(v[:-1])) / h)
    operation_scale = _sum_columns(
        np.abs(left_terms) + np.abs(voltage_terms) + np.abs(correction_terms)
        + np.abs(kappa_terms) + np.abs(trap_terms) + np.abs(trap_delta_terms)
        + np.abs(h * v[:-1]) * kappa_operation_scale
    ) + 0.5 * c * (v[-1] ** 2 + v[0] ** 2)
    tolerance = safety * EPS * (operation_scale + np.finfo(np.float64).tiny)
    trap_minus_left = trapezoid - left
    trap_identity_error = trap_minus_left - trap_delta
    results = []
    for j in range(v.shape[1]):
        results.append({
            "left_J": float(left[j]), "trapezoid_J": float(trapezoid[j]),
            "trapezoid_minus_left_J": float(trap_minus_left[j]),
            "voltage_input_J": float(voltage_input[j]),
            "capacitor_change_J": float(capacitor_change[j]),
            "discrete_correction_J": float(correction[j]),
            "kappa_term_J": float(integrated_kappa[j]), "rhs_J": float(rhs[j]),
            "closure_error_J": float(closure[j]), "tolerance_J": float(tolerance[j]),
            "operation_scale_J": float(operation_scale[j]),
            "trapezoid_minus_left_from_increments_J": float(trap_delta[j]),
            "trapezoid_identity_error_J": float(trap_identity_error[j]),
            "kappa_max_abs_A": float(np.max(np.abs(kappa[:, j]))),
            "safety_factor": float(safety),
            "valid": bool(abs(closure[j]) <= tolerance[j] and abs(trap_identity_error[j]) <= tolerance[j]),
            "scope": "FP64 algebra of saved native steps; not continuous energy accuracy or small-kappa certification",
        })
    return results
