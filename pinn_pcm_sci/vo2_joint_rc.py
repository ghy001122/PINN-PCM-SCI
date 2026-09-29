"""FP64 elimination of the frozen explicit-Euler RC relation.

This module solves the *discrete* relation, not the continuous RC equation.
Native arrays include the initial state: R has N rows, v has N rows, and R[-1]
does not drive a further step.  Both passes use O(N) bidiagonal linear algebra
on the CPU.  The custom first-order VJP retains every temporal dependency on R;
no histories are detached inside the mathematical recurrence.
"""
from __future__ import annotations

import numpy as np
import torch
from scipy.linalg import solve_banded
from torch.autograd.function import once_differentiable


def _frozen_numpy(value, name: str) -> np.ndarray:
    if torch.is_tensor(value):
        if value.requires_grad:
            raise ValueError(f"{name} is frozen in this interface; only R is differentiable")
        value = value.detach().cpu().numpy()
    result = np.asarray(value, dtype=np.float64)
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must contain finite values")
    return result


def _forward(R, h, C, RL, Vin, v0):
    resistance = np.asarray(R, dtype=np.float64)
    original_shape = resistance.shape
    if resistance.ndim == 1:
        resistance = resistance[:, None]
    if (resistance.ndim != 2 or resistance.shape[0] < 1
            or resistance.shape[1] not in (1, 2)
            or not np.all(np.isfinite(resistance)) or np.any(resistance <= 0.)):
        raise ValueError("R must be positive finite (N,) or (N, one/two devices)")
    h, C, RL = (float(_frozen_numpy(x, name)) for x, name in ((h, 'h'), (C, 'C'), (RL, 'RL')))
    if h <= 0. or C <= 0. or RL <= 0.:
        raise ValueError("h, C and RL must be positive SI values")
    count, devices = resistance.shape
    vin = np.broadcast_to(_frozen_numpy(Vin, 'Vin'), (devices,)).copy()
    initial = np.broadcast_to(_frozen_numpy(v0, 'v0'), (devices,)).copy()
    alpha = h / C
    with np.errstate(over='raise', divide='raise', invalid='raise'):
        coefficient = 1. - alpha * (1. / RL + 1. / resistance[:-1])
        drive = alpha * vin / RL
    voltage = np.empty_like(resistance)
    voltage[0] = initial
    if count > 1:
        # Unknowns are v[1], ..., v[N-1].  The first boundary term is a[0]*v0.
        # The subdiagonal contains -a[1], ..., -a[N-2].  A banded solve performs
        # the original causal recurrence without a 40k-operation Torch graph.
        for device in range(devices):
            bands = np.zeros((2, count - 1), dtype=np.float64)
            bands[0] = 1.
            bands[1, :-1] = -coefficient[1:, device]
            rhs = np.full(count - 1, drive[device], dtype=np.float64)
            rhs[0] += coefficient[0, device] * initial[device]
            voltage[1:, device] = solve_banded((1, 0), bands, rhs, check_finite=False,
                                              overwrite_ab=True, overwrite_b=True)
    if not np.all(np.isfinite(voltage)):
        raise FloatingPointError("Discrete RC evolution became non-finite; no clipping is applied")
    return resistance, voltage, coefficient, alpha, original_shape


def rc_forward(R, h, C, RL, Vin, v0=0) -> np.ndarray:
    """Common-readout NumPy recurrence, with output shape identical to R.

    h [s], C [F], RL/R [ohm], Vin/v0 [V].  Vin and v0 are scalars or one value
    per device; they are fixed controls for the authorized constant-drive case.
    """
    _, voltage, _, _, original_shape = _forward(R, h, C, RL, Vin, v0)
    return voltage.reshape(original_shape)


class _RCVoltage(torch.autograd.Function):
    @staticmethod
    def forward(ctx, R, h, C, RL, Vin, v0):
        # This numerical transfer is paired with the complete analytic reverse
        # below.  It is not a stop-gradient approximation to R.
        copied = R.detach().cpu().numpy().copy()
        resistance, voltage, coefficient, alpha, shape = _forward(copied, h, C, RL, Vin, v0)
        output = torch.as_tensor(voltage.reshape(shape), dtype=R.dtype, device=R.device)
        ctx.save_for_backward(R, output)  # Preserve Torch's in-place version checks.
        ctx.resistance = resistance
        ctx.voltage = voltage
        ctx.coefficient = coefficient
        ctx.alpha = alpha
        ctx.original_shape = shape
        return output

    @staticmethod
    @once_differentiable
    def backward(ctx, grad_voltage):
        R, _ = ctx.saved_tensors
        incoming = grad_voltage.detach().cpu().numpy().reshape(ctx.resistance.shape)
        if not np.all(np.isfinite(incoming)):
            raise FloatingPointError("RC incoming adjoint contains non-finite values")
        count, devices = incoming.shape
        derivative = np.zeros_like(ctx.resistance)
        if count > 1:
            for device in range(devices):
                # lambda[n] = g[n] + a[n]*lambda[n+1].  The upper-bidiagonal
                # solve includes losses from every future native output.
                bands = np.zeros((2, count), dtype=np.float64)
                bands[1] = 1.
                bands[0, 1:] = -ctx.coefficient[:, device]
                adjoint = solve_banded((0, 1), bands, incoming[:, device].copy(),
                                       check_finite=False, overwrite_ab=True, overwrite_b=True)
                derivative[:-1, device] = (adjoint[1:] * ctx.alpha * ctx.voltage[:-1, device]
                                           / ctx.resistance[:-1, device]**2)
        if not np.all(np.isfinite(derivative)):
            raise FloatingPointError("RC resistance adjoint became non-finite")
        result = torch.as_tensor(derivative.reshape(ctx.original_shape), dtype=R.dtype, device=R.device)
        return result, None, None, None, None, None


def rc_voltage(R: torch.Tensor, h, C, RL, Vin, v0=0) -> torch.Tensor:
    """Eliminate discrete RC with a full-history first-order R gradient.

    R must be FP64.  Inputs other than R are frozen; differentiating them or
    requesting higher-order derivatives is outside this task's interface.
    The final R row has zero RC-only derivative because no final extra step is
    taken; its direct contribution to same-layer Joule power/readout remains
    available to the surrounding Torch objective.
    """
    if not torch.is_tensor(R) or R.dtype != torch.float64:
        raise TypeError("rc_voltage requires an FP64 Torch resistance tensor")
    return _RCVoltage.apply(R, h, C, RL, Vin, v0)
