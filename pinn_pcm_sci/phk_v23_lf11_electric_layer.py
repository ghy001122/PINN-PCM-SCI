"""Implicit harmonic-resistance electrical layer and conservative Joule deposition.

The face network and half-resistance allocation are those in phk_benchmark.
SciPy/SuperLU performs sparse factorization; a custom PyTorch VJP returns the
complete derivative to every conductance, including the electrode RHS term.
This is established implicit differentiation, not a new linear solver.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import splu
import torch

from .phk_benchmark import PhkGrid


@dataclass
class SolveCounts:
    forward_queries: int = 0
    zero_drive_queries: int = 0
    factorizations: int = 0
    forward_solves: int = 0
    adjoint_solves: int = 0
    zero_adjoint_queries: int = 0
    max_forward_scaled_residual: float = 0.
    max_adjoint_scaled_residual: float = 0.


class SparseElectricalBackend:
    def __init__(self, grid, heater_width_fraction, tolerance=1e-10):
        self.grid, self.tolerance = grid, tolerance
        self.first, self.second = grid.internal_first, grid.internal_second
        self.top = np.arange((grid.nz-1)*grid.nx, grid.cell_count)
        overlap = grid.bottom_overlap(heater_width_fraction)
        self.bottom = np.flatnonzero(overlap > 0)
        self.overlap = overlap[self.bottom]
        self.rows = np.r_[self.first, self.first, self.second, self.second,
                          self.top, self.bottom]
        self.cols = np.r_[self.first, self.second, self.first, self.second,
                          self.top, self.bottom]
        self.counts = SolveCounts()

    def matrix(self, g, gt, gb):
        values = np.r_[g, -g, -g, g, gt, gb]
        if not np.isfinite(values).all() or min(g.min(), gt.min(), gb.min()) <= 0:
            raise FloatingPointError("nonpositive/nonfinite electrical conductance")
        return sp.coo_matrix((values, (self.rows, self.cols)),
                             shape=(self.grid.cell_count,)*2).tocsc()

    def scaled_residual(self, matrix, value, rhs, *, transpose=False):
        residual = (matrix.T if transpose else matrix) @ value - rhs
        scaled = float(np.max(np.abs(residual)) / max(1., np.max(np.abs(rhs))))
        if not np.isfinite(value).all() or not np.isfinite(scaled) or scaled > self.tolerance:
            raise FloatingPointError(f"electrical linear solve residual {scaled:.4g}")
        return scaled

    def snapshot(self):
        return asdict(self.counts)


class _ImplicitVoltage(torch.autograd.Function):
    @staticmethod
    def forward(ctx, g, gt, gb, voltage, backend):
        # Numerical-kernel conversion only. backward supplies the full VJP.
        ng, nt, nb = [x.detach().cpu().numpy() for x in (g, gt, gb)]
        matrix = backend.matrix(ng, nt, nb)
        rhs = np.zeros(backend.grid.cell_count)
        rhs[backend.top] = nt * voltage
        factor = splu(matrix, permc_spec="MMD_AT_PLUS_A")
        backend.counts.factorizations += 1
        value = factor.solve(rhs)
        backend.counts.forward_solves += 1
        err = backend.scaled_residual(matrix, value, rhs)
        backend.counts.max_forward_scaled_residual = max(
            backend.counts.max_forward_scaled_residual, err)
        ctx.backend, ctx.factor, ctx.matrix = backend, factor, matrix
        ctx.value, ctx.voltage = value, voltage
        ctx.device, ctx.dtype = g.device, g.dtype
        return torch.as_tensor(value, dtype=g.dtype, device=g.device)

    @staticmethod
    def backward(ctx, grad_output):
        b = ctx.backend
        rhs = grad_output.detach().cpu().numpy()
        if np.any(rhs):
            z = ctx.factor.solve(rhs, trans="T")
            b.counts.adjoint_solves += 1
            err = b.scaled_residual(ctx.matrix, z, rhs, transpose=True)
            b.counts.max_adjoint_scaled_residual = max(b.counts.max_adjoint_scaled_residual, err)
        else:
            z = np.zeros_like(rhs)
            b.counts.zero_adjoint_queries += 1
        v = ctx.value
        dg = -(z[b.first]-z[b.second])*(v[b.first]-v[b.second])
        # Top derivative contains both df and dA; ground has only dA.
        dt = z[b.top]*(ctx.voltage-v[b.top])
        db = -z[b.bottom]*v[b.bottom]
        result = tuple(torch.as_tensor(x, dtype=ctx.dtype, device=ctx.device) for x in (dg, dt, db))
        return (*result, None, None)


class ElectricalLayer:
    """One scalar, known voltage per call. Differentiable in cell conductivity."""
    def __init__(self, grid: PhkGrid, heater_width_fraction: float, tolerance=1e-10):
        self.grid = grid
        self.backend = SparseElectricalBackend(grid, heater_width_fraction, tolerance)
        self._tensors = {}

    def tensors(self, like):
        key = (str(like.device), like.dtype)
        if key not in self._tensors:
            b, g = self.backend, self.grid
            value = dict(first=b.first, second=b.second, top=b.top, bottom=b.bottom,
                         half=g.internal_half_distance, area=g.internal_area,
                         overlap=b.overlap, volume=g.cell_volumes)
            self._tensors[key] = {k: torch.as_tensor(v, device=like.device,
                dtype=torch.long if k in {"first", "second", "top", "bottom"} else like.dtype)
                for k, v in value.items()}
        return self._tensors[key]

    def resistances(self, sigma):
        t = self.tensors(sigma)
        ri = t["half"] / (sigma[t["first"]]*t["area"])
        rj = t["half"] / (sigma[t["second"]]*t["area"])
        gt = 2*sigma[t["top"]]*self.grid.dx/self.grid.dz
        gb = 2*sigma[t["bottom"]]*t["overlap"]/self.grid.dz
        return ri, rj, 1/(ri+rj), gt, gb

    def __call__(self, sigma, voltage):
        sigma = sigma.reshape(-1)
        if len(sigma) != self.grid.cell_count:
            raise ValueError("conductivity/grid mismatch")
        self.backend.counts.forward_queries += 1
        if float(voltage) == 0.:
            self.backend.counts.zero_drive_queries += 1
            zero = sigma*0
            return zero, zero
        _, _, g, gt, gb = self.resistances(sigma)
        v = _ImplicitVoltage.apply(g, gt, gb, float(voltage), self.backend)
        return v, self.deposition(v, sigma, voltage)["density"]

    def deposition(self, v, sigma, voltage):
        """Explicit resistance derivatives remain in this ordinary torch graph."""
        t = self.tensors(sigma)
        ri, rj, g, gt, gb = self.resistances(sigma)
        edge_current = g*(v[t["first"]]-v[t["second"]])
        pi, pj = edge_current.square()*ri, edge_current.square()*rj
        pt = gt*(float(voltage)-v[t["top"]]).square()
        pb = gb*v[t["bottom"]].square()
        cell = torch.zeros_like(v).index_add(0, t["first"], pi)
        cell = cell.index_add(0, t["second"], pj)
        cell = cell.index_add(0, t["top"], pt).index_add(0, t["bottom"], pb)
        return dict(density=cell/t["volume"], cell_power=cell,
                    half_power_first=pi, half_power_second=pj,
                    internal_power=pi.sum()+pj.sum(), top_power=pt.sum(), bottom_power=pb.sum(),
                    top_current=(gt*(float(voltage)-v[t["top"]])).sum(),
                    bottom_current=(gb*v[t["bottom"]]).sum(),
                    joule_power=cell.sum())

    def balance(self, v, sigma, voltage):
        """Cell electrical residual (A v-f)/volume for the P_F control."""
        t = self.tensors(sigma)
        _, _, g, gt, gb = self.resistances(sigma)
        edge = g*(v[t["first"]]-v[t["second"]])
        net = torch.zeros_like(v).index_add(0, t["first"], edge)
        net = net.index_add(0, t["second"], -edge)
        net = net.index_add(0, t["top"], gt*(v[t["top"]]-float(voltage)))
        net = net.index_add(0, t["bottom"], gb*v[t["bottom"]])
        return net/t["volume"]
