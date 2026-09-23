"""Relative phase coordinates and local time moments (no reference inputs).

PCM-20260922-RELATIVE-PHASE-MOMENTS-01. Interval regularization adapts
Feng et al., arXiv:2503.23729v1, sec. 3.1; Legendre testing has VPINN
precedent (arXiv:1912.00873). No upstream implementation is copied.
"""
from __future__ import annotations

import math
import numpy as np
import torch
import torch.nn.functional as F

from .phk_v22r_pinn import _gradient
from .phk_v23_lf11_elimination_physics import fields

KINDS = ("Pphi", "Ppsi", "Pzeta", "Iphi", "Izeta", "Mzeta")
ARM_KIND = {"P": "Pphi", "L": "Ppsi", "R": "Pzeta", "I": "Iphi",
            "RI": "Izeta", "RIM": "Mzeta", "G": "Pphi"}
ARMS = ("D", "P", "L", "R", "I", "RI", "RIM", "G")
KNOTS = (0., .05, .27, .35, 1.01, 1.06, 1.28, 1.36, 2.5)


def stable_coordinate(psi, delta):
    log_p, log_c = F.logsigmoid(psi), F.logsigmoid(-psi)
    log_delta = psi.new_tensor(math.log(delta))
    zeta = torch.logaddexp(log_p, log_delta)-torch.logaddexp(log_c, log_delta)
    s = torch.exp(log_p+log_c)
    attenuation = (1+2*delta)*s/(s+delta+delta*delta)
    return zeta, s, attenuation


def phase_quantities(model, q, delta=1e-8, kind=None):
    """Differentiate complete latent, including spatial IC and startup.

    Raw controls differentiate the original sigmoid field. Relative controls
    use the analytic pullback without division by a rounded phase value.
    """
    f = fields(model, q, phase_latent=True)
    p = model.physics
    phi, psi, temperature = f['phase'], f['phase_latent'], f['temperature']
    zeta, s, attenuation = stable_coordinate(psi, delta)
    mobility = p.mobility(temperature)
    drive = -2*p.barrier_scale*(1-2*phi)+6*p.thermal_drive*(temperature-p.theta_transition)
    out = dict(phi=phi, psi=psi, zeta=zeta, s=s, attenuation=attenuation,
               temperature=temperature)
    if kind is None or kind in ('Pphi', 'Iphi'):
        dp = _gradient(phi, q)
        lap = _gradient(dp[:, 0], q)[:, 0]+_gradient(dp[:, 1], q)[:, 1]
        source = mobility*(p.interface_width**2*lap+phi*(1-phi)*drive)
        out.update(Fphi=source, rphi=dp[:, 2]-source, dphi=dp)
    if kind is None or kind in ('Ppsi', 'Pzeta', 'Izeta', 'Mzeta'):
        du = _gradient(psi, q)
        lap = _gradient(du[:, 0], q)[:, 0]+_gradient(du[:, 1], q)[:, 1]
        source = mobility*(p.interface_width**2*(lap+(1-2*phi)*du[:, :2].square().sum(1))+drive)
        residual = du[:, 2]-source
        out.update(Fpsi=source, rpsi=residual, Fzeta=attenuation*source,
                   rzeta=attenuation*residual, dpsi=du)
    return out


def interval_moments(y, source, endpoints, width, nodes, weights):
    """Shapes (..., q), (..., 2), (...); both endpoints remain differentiable."""
    ya, yb = endpoints[..., 0], endpoints[..., 1]
    increment = yb-ya
    p1 = math.sqrt(3)*(2*nodes-1)
    d0 = increment/width-(source*weights).sum(-1)
    d1 = (math.sqrt(3)*(increment-2*((y-ya[..., None])*weights).sum(-1))/width
          -(source*weights*p1).sum(-1))
    return d0, d1


class PanelSampler:
    """Length-proportional panels, independent uniform cells, two equal scales."""
    def __init__(self, config, grid, seed):
        self.config, self.grid = config, grid
        self.rng = np.random.default_rng(seed)
        self.catalog = []
        for window, ((lo, hi), mass) in enumerate(zip(config['windows'], config['window_masses'])):
            for scale, target in enumerate(config['phase_panels']['widths']):
                panels = []
                for a, b in zip(KNOTS[:-1], KNOTS[1:]):
                    if a >= lo-1e-12 and b <= hi+1e-12:
                        n = math.ceil((b-a)/target)
                        edges = np.linspace(a, b, n+1)
                        panels.extend(zip(edges[:-1], edges[1:]))
                panels = np.asarray(panels)
                lengths = panels[:, 1]-panels[:, 0]
                np.testing.assert_allclose(lengths.sum(), hi-lo, atol=1e-12)
                self.catalog.append(dict(window=window, scale=scale, mass=mass/2,
                                         bounds=panels, probability=lengths/lengths.sum()))

    def sample(self, fixed=False):
        count = self.config['phase_panels']['fixed_per_window_scale'] if fixed else 1
        nspace = self.config['phase_panels']['space_points']
        result = []
        for item in self.catalog:
            for index in self.rng.choice(len(item['bounds']), count, p=item['probability']):
                a, b = item['bounds'][index]
                result.append(dict(a=float(a), b=float(b), mass=item['mass']/count,
                    window=item['window'], scale=item['scale'],
                    cells=self.rng.choice(self.grid.cell_count, nspace, replace=True).tolist()))
        return result


def panel_values(model, grid, panels, order, delta=1e-8, kind=None, work=None):
    """Deterministic Gauss objective; panel/space sampling is separate."""
    device = next(model.parameters()).device
    xi, w = np.polynomial.legendre.leggauss(order)
    xi, w = (xi+1)/2, w/2
    cells = np.asarray([p['cells'] for p in panels])
    a = np.asarray([p['a'] for p in panels])
    b = np.asarray([p['b'] for p in panels])
    shape = (*cells.shape, order)
    q = np.empty((*shape, 3))
    q[..., 0] = grid.cell_x[cells][..., None]
    q[..., 1] = grid.cell_z[cells][..., None]
    q[..., 2] = (a[:, None]+(b-a)[:, None]*xi)[:, None, :]
    qt = torch.tensor(q.reshape(-1, 3), dtype=torch.float64, device=device, requires_grad=True)
    data = phase_quantities(model, qt, delta, kind)
    weights = qt.new_tensor(w)
    nodes = qt.new_tensor(xi)
    mass = qt.new_tensor([p['mass'] for p in panels])
    values = {}
    for name, residual in (('Pphi', 'rphi'), ('Ppsi', 'rpsi'), ('Pzeta', 'rzeta')):
        if residual in data:
            values[name] = ((data[residual].reshape(shape)/5).square()*weights).sum(-1)
    need_moments = kind is None or kind in ('Iphi', 'Izeta', 'Mzeta')
    if need_moments:
        qe = np.empty((*cells.shape, 2, 3))
        qe[..., :2] = q[..., :1, :2]
        qe[..., 2] = np.stack([a, b], -1)[:, None, :]
        ef = fields(model, qt.new_tensor(qe.reshape(-1, 3)), phase_latent=True)
        endpoints = {'phi': ef['phase'], 'zeta': stable_coordinate(ef['phase_latent'], delta)[0]}
        for coordinate, local, name in (('phi', 'Pphi', 'Iphi'), ('zeta', 'Pzeta', 'Izeta')):
            if local not in values:
                continue
            d0, d1 = interval_moments(data[coordinate].reshape(shape),
                data['F'+coordinate].reshape(shape), endpoints[coordinate].reshape(*cells.shape, 2),
                qt.new_tensor(b-a)[:, None], nodes, weights)
            values[name] = .5*values[local]+.5*(d0/5).square()
            if coordinate == 'zeta':
                values['Mzeta'] = values[name]+.5*(d1/5).square()
        if work is not None:
            work['phase_endpoint_queries'] += cells.size*2
    if work is not None:
        work['phase_derivative_positions'] += int(np.prod(shape))
        work['phase_spatial_second_ad_components'] += int(np.prod(shape))*(4 if kind is None else 2)
    values = {k: torch.dot(mass, v.mean(1)) for k, v in values.items()}
    return values if kind is None else {kind: values[kind]}


def phase_value_gradient(model, grid, panels, order, delta=1e-8, chunk=8):
    """Zero-update values and complete parameter-gradient vectors for calibration."""
    # Keep the six shared second-derivative graphs bounded on an 8 GB CPU host.
    chunk = min(chunk, max(1, 512//(order*len(panels[0]['cells']))))
    parameters = [p for p in model.parameters() if p.requires_grad]
    size = sum(p.numel() for p in parameters)
    device = parameters[0].device
    values = dict.fromkeys(KINDS, 0.)
    gradients = {k: torch.zeros(size, dtype=torch.float64, device=device) for k in KINDS}
    for start in range(0, len(panels), chunk):
        local = panel_values(model, grid, panels[start:start+chunk], order, delta)
        for i, k in enumerate(KINDS):
            values[k] += float(local[k].detach())
            g = torch.autograd.grad(local[k], parameters, retain_graph=i<len(KINDS)-1, allow_unused=True)
            gradients[k] += torch.cat([(torch.zeros_like(p) if v is None else v).detach().reshape(-1)
                                      for p, v in zip(parameters, g)])
    if not all(np.isfinite(v) for v in values.values()) or not all(torch.isfinite(g).all() for g in gradients.values()):
        raise FloatingPointError('nonfinite phase calibration')
    return values, gradients


def calibrate(values, gradients, floor=1e-12):
    if any(not np.isfinite(values[k]) or values[k] <= floor for k in KINDS):
        raise FloatingPointError('phase loss calibration is numerically unidentifiable')
    factors = {arm: values['Pphi']/values[kind] for arm, kind in ARM_KIND.items() if arm not in ('P', 'G')}
    norm = float(torch.linalg.vector_norm(gradients['Pphi']))
    target = float(torch.linalg.vector_norm(factors['RIM']*gradients['Mzeta']))
    if norm <= floor or not np.isfinite([norm, target]).all():
        raise FloatingPointError('G gradient calibration is numerically unidentifiable')
    factors.update(P=1., G=target/norm)
    return dict(factors=factors, phase_values=values,
                gradient_norms={k: float(torch.linalg.vector_norm(v)) for k, v in gradients.items()},
                G_target_gradient_norm=target, reference_read=False,
                identity='loss-value matching except G: initial RIM phase-gradient norm')


def quadrature_comparison(low, high):
    rows = {}
    for k in KINDS:
        lv, lg = low['values'][k], low['gradient_norms'][k]
        hv, hg = high['values'][k], high['gradient_norms'][k]
        dv, dg = abs(lv-hv)/max(abs(hv), 1e-12), abs(lg-hg)/max(abs(hg), 1e-12)
        rows[k] = dict(value_relative_change=dv, gradient_norm_relative_change=dg,
                       passed=dv <= .01 and dg <= .05)
    return rows


def select_order(records):
    a, b = quadrature_comparison(records[8], records[16]), quadrature_comparison(records[16], records[32])
    order = None if not all(v['passed'] for v in b.values()) else (8 if all(v['passed'] for v in a.values()) else 16)
    return dict(status='QUADRATURE_UNRESOLVED' if order is None else 'QUADRATURE_VALID',
                selected_order=order, comparisons={'8_to_16': a, '16_to_32': b})
