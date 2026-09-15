"""Common finite-volume readout for LF11 predicted fields, never a solver."""
from __future__ import annotations
import numpy as np
from scipy.interpolate import PchipInterpolator, RegularGridInterpolator
from scipy.special import expit, logit

from .phk_benchmark import PhkGrid


def make_grid(x, z, physics):
    return PhkGrid.build(nx=len(x), nz=len(z), x_min=physics.x_min,
                         x_max=physics.x_max, z_min=physics.z_min, z_max=physics.z_max)


def readout(potential, temperature, phase, grid, voltage, physics):
    """Evaluate the frozen harmonic face network without solving its equations.

    Electrode currents and edge-dissipation power are independent observables.
    A nonzero discrete balance defect is reported rather than hidden by P/U.
    """
    first, second = grid.internal_first, grid.internal_second
    half, area = grid.internal_half_distance, grid.internal_area
    top = np.arange((grid.nz-1)*grid.nx, grid.nz*grid.nx)
    overlap = grid.bottom_overlap(physics.heater_width_fraction)
    bottom = np.flatnonzero(overlap > 0)
    records = {key: [] for key in ("top_current", "bottom_current", "joule_power",
                                    "input_power", "power_defect", "electric_fv_rms")}
    for v, t, ph, u in zip(potential, temperature, phase, voltage, strict=True):
        sigma = np.exp(physics.conductivity_temperature_gain*t+
                       np.log(physics.conductivity_phase_ratio)*ph**2*(3-2*ph))
        conductance = 1/(half/(sigma[first]*area)+half/(sigma[second]*area))
        dv = v[first]-v[second]
        current = conductance*dv
        gt = sigma[top]*grid.dx/(.5*grid.dz)
        gb = sigma[bottom]*overlap[bottom]/(.5*grid.dz)
        it = gt*(u-v[top]); ib = gb*v[bottom]
        power = np.sum(conductance*dv**2)+np.sum(gt*(u-v[top])**2)+np.sum(gb*v[bottom]**2)
        defect = np.zeros(grid.cell_count)
        np.add.at(defect, first, current); np.add.at(defect, second, -current)
        defect[top] -= it; defect[bottom] += ib
        records["top_current"].append(float(it.sum()))
        records["bottom_current"].append(float(ib.sum()))
        records["joule_power"].append(float(power))
        records["input_power"].append(float(u*it.sum()))
        records["power_defect"].append(float(power-u*it.sum()))
        records["electric_fv_rms"].append(float(np.sqrt(np.mean((defect/grid.cell_volumes)**2))))
    return {key: np.asarray(value) for key, value in records.items()}


def interpolate_sparse(data, x, z, times, physics, kind):
    """Known-BC extension, linear space, and linear/PCHIP time.

    No target values, target currents, teacher derivatives or event pools are
    accepted. Added boundary knots contain only known BC or analytic Robin
    extension of the visible nearest observation. Phase is never output-clipped.
    """
    a = data.arrays
    shape = (len(a["time"]), len(a["z"]), len(a["x"]))
    fields = a["targets"].reshape(*shape, 3).copy()
    x0, z0 = a["x"], a["z"]
    source_x = np.r_[physics.x_min, x0, physics.x_max]
    source_z = np.r_[physics.z_min, z0, physics.z_max]
    import torch
    use_logit = kind == "B_logit"
    if use_logit:
        q0 = data.coordinates[:len(x0)*len(z0)]
        initial0 = physics.initial_phase(torch.as_tensor(q0, dtype=torch.float64)).numpy().reshape(len(z0), len(x0))
        fields[..., 2] = logit(np.clip(fields[..., 2], 1e-8, 1-1e-8))-logit(np.clip(initial0, 1e-8, 1-1e-8))[None]
        fields[0, ..., 2] = 0
    # Time interpolation at the visible spatial nodes, then known boundary
    # extension at EACH query time. In particular a pulse knot absent from the
    # observation mask must still obey its analytically known electrode value.
    if kind == "B_L":
        pos = np.clip(np.searchsorted(a["time"], times, side="right")-1, 0, len(a["time"])-2)
        fraction = ((times-a["time"][pos])/(a["time"][pos+1]-a["time"][pos]))[:, None, None, None]
        temporal = (1-fraction)*fields[pos]+fraction*fields[pos+1]
    else:
        temporal = PchipInterpolator(a["time"], fields, axis=0)(times)
    f = np.pad(temporal, ((0, 0), (1, 1), (1, 1), (0, 0)), mode="edge")
    f[:, :, 0, 1] /= 1+physics.thermal_robin_biot*(x0[0]-physics.x_min)
    f[:, :, -1, 1] /= 1+physics.thermal_robin_biot*(physics.x_max-x0[-1])
    f[:, 0, :, 1] /= 1+physics.thermal_robin_biot*(z0[0]-physics.z_min)
    f[:, -1, :, 1] = 0
    source_voltage = physics.waveform(torch.as_tensor(times, dtype=torch.float64)).numpy()
    f[:, -1, :, 0] = source_voltage[:, None]
    heater = np.abs(source_x) <= physics.heater_half_width
    f[:, 0, heater, 0] = 0
    # Spatial interpolation is convex and uses no fine-grid field values.
    xx, zz = np.meshgrid(x, z, indexing="xy")
    query_space = np.column_stack([zz.ravel(), xx.ravel()])
    predictions = {}
    for index, name in enumerate(("potential", "temperature", "phase")):
        source = f[..., index].copy()
        predicted = np.stack([RegularGridInterpolator((source_z, source_x), value,
                            method="linear", bounds_error=True)(query_space) for value in source])
        if use_logit and name == "phase":
            q = np.column_stack([xx.ravel(), zz.ravel(), np.zeros(xx.size)])
            initial = physics.initial_phase(torch.as_tensor(q, dtype=torch.float64)).numpy().ravel()
            predicted = expit(predicted+logit(np.clip(initial, 1e-8, 1-1e-8))[None])
        if name == "potential":
            # The known maximum principle and zero-voltage off state are
            # equally available to neural hard transforms and interpolation.
            predicted = np.minimum(np.maximum(predicted, 0), source_voltage[:, None])
        # Known analytic IC belongs to every method, not to the teacher budget.
        if times[0] == physics.time_start:
            if name in ("potential", "temperature"): predicted[0] = 0
            else:
                q = np.column_stack([xx.ravel(), zz.ravel(), np.zeros(xx.size)])
                predicted[0] = physics.initial_phase(torch.as_tensor(q, dtype=torch.float64)).numpy().ravel()
        predictions[name] = predicted
    return predictions
