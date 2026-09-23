"""Authorized midpoint thermal cell balance and unchanged phase AD equation.

Shared face derivatives implement a surface quadrature, not the old pointwise
thermal Laplacian. Electrode Joule heat comes from ElectricalLayer exactly once.
"""
from __future__ import annotations
import numpy as np
import torch
from .phk_benchmark import PhkGrid
from .phk_v22r_pinn import _gradient, range_preserving_exact_top_fraction


def grid_for(physics, nx=80, nz=40):
    return PhkGrid.build(nx=nx, nz=nz, x_min=physics.x_min, x_max=physics.x_max,
                         z_min=physics.z_min, z_max=physics.z_max)


def fields(model, q, *, potential=False, phase_latent=False):
    """Exact inherited independent-head outputs without computing a discarded V."""
    p = model.physics
    normalized = p.normalize(q)
    names = ["temperature", "phase"] + (["potential"] if potential else [])
    latent = {k: model.heads[k](model.encoders[k](normalized)) for k in names}
    startup = 1-torch.exp(-(q[:, 2:3]-p.time_start)/model.startup_time)
    zfrac = (q[:, 1:2]-p.z_min)/(p.z_max-p.z_min)
    t = model.temperature_scale*startup*(1-zfrac)*torch.sigmoid(latent["temperature"])
    initial = p.initial_phase(q).clamp(1e-8, 1-1e-8)
    delta = model.phase_latent_scale*startup*latent["phase"]
    psi = torch.logit(initial)+delta
    phase = torch.sigmoid(psi)
    result = {"temperature": t[:, 0], "phase": phase[:, 0], "delta_logit": delta[:, 0]}
    if phase_latent:
        result["phase_latent"] = psi[:, 0]
    if potential:
        result["potential"] = (p.waveform(q[:, 2:3]) *
            range_preserving_exact_top_fraction(latent["potential"], zfrac))[:, 0]
    return result


def coordinates(grid, time, *, cells=None, device="cpu", requires_grad=False):
    xy = np.column_stack([grid.cell_x, grid.cell_z])
    if cells is not None:
        xy = xy[cells]
    return torch.tensor(np.column_stack([xy, np.full(len(xy), time)]),
                        dtype=torch.float64, device=device, requires_grad=requires_grad)


def face_quadrature(grid, cells):
    """Unique face midpoint and opposite-normal incidence for selected cells."""
    cells = np.asarray(cells, dtype=np.int64)
    iz, ix = np.divmod(cells, grid.nx)
    nxfaces = (grid.nx+1)*grid.nz
    ids = np.column_stack([iz*(grid.nx+1)+ix, iz*(grid.nx+1)+ix+1,
                           nxfaces+iz*grid.nx+ix, nxfaces+(iz+1)*grid.nx+ix])
    unique, inverse = np.unique(ids, return_inverse=True)
    vertical = unique < nxfaces
    xy = np.zeros((len(unique), 2))
    row, col = np.divmod(unique[vertical], grid.nx+1)
    xy[vertical, 0] = grid.x_min+col*grid.dx
    xy[vertical, 1] = grid.z_min+(row+.5)*grid.dz
    row, col = np.divmod(unique[~vertical]-nxfaces, grid.nx)
    xy[~vertical, 0] = grid.x_min+(col+.5)*grid.dx
    xy[~vertical, 1] = grid.z_min+row*grid.dz
    return xy, inverse.reshape(-1, 4)


def thermal_phase_residual(model, grid, time, cells, joule_density, *, include_phase=True):
    device = next(model.parameters()).device
    q = coordinates(grid, time, cells=cells, device=device, requires_grad=True)
    f = fields(model, q)
    dt, dp = _gradient(f["temperature"], q), _gradient(f["phase"], q)
    xy, incidence = face_quadrature(grid, cells)
    face = torch.tensor(np.column_stack([xy, np.full(len(xy), time)]),
                        dtype=torch.float64, device=device, requires_grad=True)
    # One AD value per shared face; adjacent cells use opposite signs.
    face_t = fields(model, face)["temperature"]
    grad = _gradient(face_t, face)
    index = torch.as_tensor(incidence, dtype=torch.long, device=device)
    flux = grid.dz*(grad[index[:, 1], 0]-grad[index[:, 0], 0])
    flux = flux+grid.dx*(grad[index[:, 3], 1]-grad[index[:, 2], 1])
    p = model.physics
    thermal = (dt[:, 2]+p.latent_ratio*dp[:, 2]+p.volumetric_cooling*f["temperature"]
               -p.thermal_diffusivity*flux/(grid.dx*grid.dz)
               -p.joule_gain*joule_density[torch.as_tensor(cells, device=device)])
    if not include_phase:
        return {"thermal": thermal, "temperature": f["temperature"],
                "phase_value": f["phase"], "thermal_surface_flux": flux}
    lap_phase = (_gradient(dp[:, 0], q)[:, 0] + _gradient(dp[:, 1], q)[:, 1])
    phase = f["phase"]
    potential_derivative = (2*p.barrier_scale*phase*(1-phase)*(1-2*phase)
                            +6*p.thermal_drive*(p.theta_transition-f["temperature"])*phase*(1-phase))
    mobility = p.mobility(f["temperature"])
    phase_residual = dp[:, 2]-mobility*(p.interface_width**2*lap_phase-potential_derivative)
    return {"thermal": thermal, "phase": phase_residual,
            "temperature": f["temperature"], "phase_value": phase,
            "thermal_surface_flux": flux}


def boundary_loss(model, sides):
    """Retain the original 13-term denominator with five electric terms zero."""
    device = next(model.parameters()).device
    total = torch.zeros((), dtype=torch.float64, device=device)
    normal = {"left": (-1., 0.), "right": (1., 0.), "bottom": (0., -1.), "top": (0., 1.)}
    for side, values in sides.items():
        q = torch.tensor(values, dtype=torch.float64, device=device, requires_grad=True)
        f = fields(model, q)
        dt, dp = _gradient(f["temperature"], q), _gradient(f["phase"], q)
        nx, nz = normal[side]
        phase_bc = nx*dp[:, 0]+nz*dp[:, 1]
        thermal_bc = (f["temperature"] if side == "top" else
                      nx*dt[:, 0]+nz*dt[:, 1]+model.physics.thermal_robin_biot*f["temperature"])
        total = total+phase_bc.square().mean()+thermal_bc.square().mean()
    return total/13


def initial_loss(model, xy):
    device = next(model.parameters()).device
    q = torch.tensor(np.column_stack([xy, np.full(len(xy), model.physics.time_start)]),
                     dtype=torch.float64, device=device)
    f = fields(model, q)
    initial = model.physics.initial_phase(q).reshape(-1)
    return (f["temperature"].square().mean()+((f["phase"]-initial)/.03).square().mean())/3
