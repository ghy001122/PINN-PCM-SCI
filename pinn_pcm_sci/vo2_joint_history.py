"""Exact author-history replay with an analytical selected-branch reverse VJP.

The discrete joint 0.01 K trigger, signs, clipping and reversal order are those
of :mod:`vo2_author_reproduction`.  Between reversals only ``Tr`` and ``Tpr``
carry differentiable history.  Their derivatives are propagated across every
reversal; neither history nor the resulting resistance is a stop-gradient.

The derivative is the derivative *within the selected event sequence*. Event
indices/signs are discrete and are not differentiated. Cross-event finite
changes therefore require separate reporting. Only first derivatives are
implemented. Fixed physical parameters and the legal initial history are not
trainable. No source trajectory or future source state is read here.

Provenance: the pinned author adaptation and MIT attribution are documented in
``vo2_author_reproduction.py``. This module adds a segmented analytical VJP,
without changing the constitutive formulas or trigger semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from torch.autograd.function import once_differentiable

from .vo2_author_reproduction import Hysteresis, Parameters, P


@dataclass
class _Tape:
    starts: np.ndarray
    events: list[tuple[int, np.ndarray, np.ndarray, np.ndarray, np.ndarray]]
    direct: np.ndarray
    state_tr: np.ndarray
    state_tpr: np.ndarray
    clip_derivative: np.ndarray


def _validate(temperature: np.ndarray) -> np.ndarray:
    t = np.asarray(temperature)
    if t.dtype != np.float64 or t.ndim != 2 or t.shape[1] not in (1, 2) or not len(t):
        raise ValueError("temperature must be a nonempty FP64 [time, 1 or 2] array")
    if not np.isfinite(t).all():
        raise FloatingPointError("nonfinite input temperature")
    return t


def _event_scan(clipped: np.ndarray, p: Parameters):
    """Scan only discrete decisions; branch math is independent of Tr/Tpr."""
    n, d = clipped.shape
    delta = np.ones(d, dtype=np.float64)
    last = np.full(d, p.Tbase - .1, dtype=np.float64)
    last_indices = np.empty(n, dtype=np.int64)
    last_index = -1
    events = []
    # Scalar comparisons avoid thousands of tiny temporary NumPy arrays. The
    # order/strict inequality matches max(abs(T - T_last)) > .01 exactly.
    for i in range(n):
        change0 = float(clipped[i, 0] - last[0])
        change1 = float(clipped[i, 1] - last[1]) if d == 2 else 0.
        if max(abs(change0), abs(change1)) > .01:
            signs = np.array([np.sign(change0), np.sign(change1)][:d])
            mask = (signs != delta) & (signs != 0.)
            if np.any(mask):
                delta[mask] = signs[mask]
                events.append((i, mask, delta.copy()))
            last[:] = clipped[i]
            last_index = i
        last_indices[i] = last_index
    return events, last_indices


def _g_and_partials(t, tr, tpr, delta, reversed_, p):
    """Return original g and analytical partials in t, Tr, Tpr."""
    denominator = tpr + 1e-6
    x = (t - tr) / denominator
    sinus = np.sin(p.gamma * x)
    tanh_u = np.tanh(np.pi**2 - 2*np.pi*x)
    proximity = .5 * (1-sinus) * (1+tanh_u)
    tp = tpr * proximity * reversed_
    tanh_z = np.tanh(p.beta * (delta*p.w/2 + p.Tc - (t+tp)))
    g = .5 + .5*tanh_z
    dp = .5 * (-p.gamma*np.cos(p.gamma*x)*(1+tanh_u)
               - 2*np.pi*(1-sinus)*(1-tanh_u*tanh_u))
    common = -.5*p.beta*(1-tanh_z*tanh_z)
    gt = common * (1 + reversed_*tpr*dp/denominator)
    gtr = common * (-reversed_*tpr*dp/denominator)
    gtpr = common * reversed_ * (proximity-tpr*dp*x/denominator)
    return g, gt, gtr, gtpr


def _forward(temperature: np.ndarray, p: Parameters, *, history: bool, tape: bool):
    t = _validate(temperature)
    clipped = np.clip(t, 305., 370.)
    events, last_indices = _event_scan(clipped, p)
    n, d = t.shape
    h = Hysteresis(d, p)
    result: dict[str, Any] = {
        "resistance": np.empty_like(t),
        "g": np.empty_like(t),
    }
    if history:
        for key in ("delta", "reversed", "Tr", "gr", "Tpr"):
            result[key] = np.empty_like(t)
        indices = np.maximum(last_indices, 0)
        result["T_last"] = clipped[indices].copy()
        result["T_last"][last_indices < 0] = p.Tbase - .1
        result["event_rows"] = np.array([e[0] for e in events], dtype=np.int64)
        result["event_masks"] = np.array([e[1] for e in events], dtype=bool).reshape(-1, d)
        result["event_delta"] = np.array([e[2] for e in events], dtype=np.float64).reshape(-1, d)
        result["trigger_rows"] = np.flatnonzero(np.r_[last_indices[0] >= 0, np.diff(last_indices) != 0])
    direct = np.empty_like(t) if tape else None
    state_tr = np.empty_like(t) if tape else None
    state_tpr = np.empty_like(t) if tape else None
    derivative_events = []
    # Initial event at row zero is possible with arbitrary legal query input;
    # avoid introducing an empty initial segment into the reverse reduction.
    starts = sorted(set([0] + [e[0] for e in events]))
    event_by_row = {e[0]: e for e in events}
    for start, stop in zip(starts, starts[1:] + [n]):
        if start in event_by_row:
            _, mask, new_delta = event_by_row[start]
            g_before, gt, gtr, gtpr = _g_and_partials(
                clipped[start], h.Tr, h.Tpr, h.delta, h.reversed, p)
            if tape:
                # tpr(new) = delta(new)*w/2 + Tc - atanh(2*g-1)/beta - t
                factor = np.zeros(d)
                factor[mask] = -2 / (p.beta * (1-(2*g_before[mask]-1)**2))
                derivative_events.append((start, mask.copy(),
                                          factor*gt - mask.astype(np.float64),
                                          factor*gtr, factor*gtpr))
            h.gr[mask] = g_before[mask]
            h.delta[mask] = new_delta[mask]
            h.reversed[mask] = 1.
            h.Tr[mask] = clipped[start, mask]
            h.Tpr[mask] = h.tpr()[mask]
        block = clipped[start:stop]
        g, gt, gtr, gtpr = _g_and_partials(block, h.Tr, h.Tpr, h.delta, h.reversed, p)
        prefactor = p.R0*np.exp(p.Ea/block)
        result["g"][start:stop] = g
        result["resistance"][start:stop] = prefactor*g+p.Rm0*p.k
        if tape:
            direct[start:stop] = prefactor*(gt-p.Ea*g/(block*block))
            state_tr[start:stop] = prefactor*gtr
            state_tpr[start:stop] = prefactor*gtpr
        if history:
            for key in ("delta", "reversed", "Tr", "gr", "Tpr"):
                result[key][start:stop] = getattr(h, key)
    if not np.isfinite(result["resistance"]).all():
        raise FloatingPointError("author constitutive replay produced nonfinite resistance")
    saved_tape = None
    if tape:
        saved_tape = _Tape(np.array(starts, dtype=np.int64), derivative_events,
                           direct, state_tr, state_tpr,
                           ((t >= 305.) & (t <= 370.)).astype(np.float64))
        if not all(np.isfinite(a).all() for a in (direct, state_tr, state_tpr)):
            raise FloatingPointError("nonfinite analytical history derivative")
    return result, saved_tape


def replay_with_history(temperature: np.ndarray, parameters: Parameters = P) -> dict[str, np.ndarray]:
    """Replay legal history; return same-time R/g/H and discrete event evidence.

    No evolved temperature clipping is performed; only the original law's
    internal 305--370 K clipping is retained. No current or source data is read.
    """
    return _forward(temperature, parameters, history=True, tape=False)[0]


def selected_event_signature(temperature: np.ndarray, parameters: Parameters = P):
    """Hashable signature for qualification within a fixed selected branch."""
    events, trigger_indices = _event_scan(np.clip(_validate(temperature), 305., 370.), parameters)
    return (tuple((i, tuple(mask), tuple(delta)) for i, mask, delta in events),
            trigger_indices.tobytes())


def _vjp(saved: _Tape, output_gradient: np.ndarray) -> np.ndarray:
    w = np.asarray(output_gradient, dtype=np.float64)
    grad = w*saved.direct
    # Segment-wise summation followed by an event-only reverse chain. All
    # dependence through Tr and Tpr, including g at each reversal, is retained.
    bar_tr = np.add.reduceat(w*saved.state_tr, saved.starts, axis=0)
    bar_tpr = np.add.reduceat(w*saved.state_tpr, saved.starts, axis=0)
    event_map = {e[0]: e for e in saved.events}
    carry_tr = np.zeros(w.shape[1])
    carry_tpr = np.zeros(w.shape[1])
    for j in range(len(saved.starts)-1, -1, -1):
        row = int(saved.starts[j])
        carry_tr += bar_tr[j]
        carry_tpr += bar_tpr[j]
        if row in event_map:
            _, mask, dtemp, dtr, dtpr = event_map[row]
            grad[row, mask] += carry_tr[mask] + carry_tpr[mask]*dtemp[mask]
            old_tr = carry_tpr[mask]*dtr[mask]
            old_tpr = carry_tpr[mask]*dtpr[mask]
            carry_tr[mask] = old_tr
            carry_tpr[mask] = old_tpr
    grad *= saved.clip_derivative
    if not np.isfinite(grad).all():
        raise FloatingPointError("nonfinite analytical reverse history derivative")
    return grad


class _ResistanceFromTemperature(torch.autograd.Function):
    @staticmethod
    def forward(ctx, temperature: torch.Tensor, parameters: Parameters):
        if temperature.dtype != torch.float64:
            raise TypeError("FP64 temperature required")
        values = temperature.detach().cpu().numpy()
        result, tape = _forward(values, parameters, history=False, tape=True)
        ctx.history_tape = tape
        ctx.input_device = temperature.device
        return torch.from_numpy(result["resistance"]).to(device=temperature.device)

    @staticmethod
    @once_differentiable
    def backward(ctx, output_gradient: torch.Tensor):
        grad = _vjp(ctx.history_tape, output_gradient.detach().cpu().numpy())
        return torch.from_numpy(grad).to(device=ctx.input_device), None


def resistance_from_temperature(temperature: torch.Tensor, parameters: Parameters = P) -> torch.Tensor:
    """Same-time dynamic R with exact analytical T -> history -> R first VJP.

    Input/output may reside on CPU or GPU; this small sequential constitutive
    operator runs in CPU NumPy. Transfers and the full selected-branch history
    derivative are inside the custom autograd operator. It does not support
    higher derivatives; the authorized finite-difference residual uses first
    derivatives with respect to trainable parameters only.
    """
    return _ResistanceFromTemperature.apply(temperature, parameters)
