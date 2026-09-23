"""Focused mathematical/interface checks; no scientific optimizer updates."""
import json
import math
from pathlib import Path
import unittest

import numpy as np
import torch

from pinn_pcm_sci.phk_v23_lf11_followup_fit import fit_model
from pinn_pcm_sci.phk_v23_lf11_elimination_physics import fields, grid_for, coordinates, thermal_phase_residual
from pinn_pcm_sci.phk_v23_phase_moments import (
    PanelSampler, phase_quantities, stable_coordinate, interval_moments,
    phase_value_gradient, calibrate, panel_values, select_order, KINDS,
)


def fixture():
    torch.set_num_threads(2)
    c = json.loads(Path('configs/phk_v23/lf11_b1_sprint.json').read_text())
    c.update(width=8, layers=2, phase_panels=dict(widths=[.025, .1], space_points=3, fixed_per_window_scale=1))
    m = fit_model(c, adapter=True)
    for p in m.heads['potential'].parameters():
        p.requires_grad_(False)
    return c, m, grid_for(m.physics, 8, 4)


def grad(value, model, retain=False):
    ps = [p for p in model.parameters() if p.requires_grad]
    gs = torch.autograd.grad(value, ps, allow_unused=True, retain_graph=retain)
    return torch.cat([(torch.zeros_like(p) if g is None else g).ravel() for p, g in zip(ps, gs)])


def test_original_fields_and_thermal_value_gradient_unchanged():
    c, m, grid = fixture()
    q = coordinates(grid, .175)
    original = m.read_only_output_diagnostics(q).output.fields
    exposed = fields(m, q, potential=True, phase_latent=True)
    for j, k in enumerate(('potential', 'temperature', 'phase')):
        torch.testing.assert_close(original[:, j], exposed[k], rtol=0, atol=0)
    torch.testing.assert_close(torch.sigmoid(exposed['phase_latent']), exposed['phase'], rtol=0, atol=0)
    heat = torch.ones(grid.cell_count, dtype=torch.float64)
    for t in (.175, 1.28):
        old = thermal_phase_residual(m, grid, t, np.arange(8), heat)
        new = thermal_phase_residual(m, grid, t, np.arange(8), heat, include_phase=False)
        torch.testing.assert_close(old['thermal'], new['thermal'], rtol=0, atol=0)
        torch.testing.assert_close(grad(old['thermal'].square().mean(), m),
                                   grad(new['thermal'].square().mean(), m), rtol=0, atol=0)


def test_complete_latent_residual_chain_and_parameter_gradients():
    c, m, grid = fixture()
    rng = np.random.default_rng(733)
    q = torch.tensor(rng.uniform([-1., 0., .01], [1., 1., 2.5], (45, 3)), requires_grad=True)
    r = phase_quantities(m, q)
    torch.testing.assert_close(r['rphi'], r['s']*r['rpsi'], rtol=2e-11, atol=1e-13)
    torch.testing.assert_close(grad(r['rphi'].square().sum(), m, True),
                               grad((r['s']*r['rpsi']).square().sum(), m, True), rtol=3e-10, atol=1e-12)
    derivative = 1/(r['phi']+1e-8)+1/(1-r['phi']+1e-8)
    torch.testing.assert_close(r['rzeta'], derivative*r['rphi'], rtol=2e-10, atol=2e-12)
    torch.testing.assert_close(grad(r['rzeta'].square().sum(), m, True),
                               grad((derivative*r['rphi']).square().sum(), m, True), rtol=3e-9, atol=2e-9)
    dtz = torch.autograd.grad(r['zeta'].sum(), q, create_graph=True)[0][:, 2]
    torch.testing.assert_close(dtz-r['Fzeta'], r['rzeta'], rtol=1e-11, atol=1e-12)
    assert r['dpsi'][:, :2].abs().max() > 1e-3
    assert float(torch.linalg.vector_norm(grad(r['rzeta'].square().mean(), m))) > 1e-5


def test_stable_coordinate_derivatives_in_saturated_tails():
    psi = torch.linspace(-60, 60, 241, dtype=torch.float64, requires_grad=True)
    z, s, a = stable_coordinate(psi, 1e-8)
    dz = torch.autograd.grad(z.sum(), psi, create_graph=True)[0]
    ddz = torch.autograd.grad(dz.sum(), psi, retain_graph=True)[0]
    da = torch.autograd.grad(a.sum(), psi)[0]
    assert torch.isfinite(z).all() and torch.isfinite(ddz).all()
    torch.testing.assert_close(dz, a, rtol=1e-10, atol=2e-15)
    torch.testing.assert_close(ddz, da, rtol=1e-8, atol=2e-15)
    assert (a > 0).all() and a[0] < 1e-10 and a[-1] < 1e-10
    assert torch.sigmoid(psi[-1]) == 1.


def test_endpoint_moments_and_their_cancellation_blind_spot():
    for order in (8, 16, 32):
        x, w = np.polynomial.legendre.leggauss(order)
        x, w = torch.tensor((x+1)/2), torch.tensor(w/2)
        p1 = math.sqrt(3)*(2*x-1)
        examples = [(2*x, torch.ones_like(x)*2, [0., 2.], 2., 0.),
                    (math.sqrt(3)*(x*x-x), p1, [0., 0.], 0., 1.),
                    (2*x**3-3*x*x+x, 6*x*x-6*x+1, [0., 0.], 0., 0.)]
        for y, r, ends, v0, v1 in examples:
            d0, d1 = interval_moments(y, torch.zeros_like(y), torch.tensor(ends), 1., x, w)
            torch.testing.assert_close(d0, (w*r).sum(), rtol=1e-10, atol=2e-14)
            torch.testing.assert_close(d1, (w*p1*r).sum(), rtol=1e-10, atol=2e-14)
            np.testing.assert_allclose([float(d0), float(d1)], [v0, v1], atol=2e-14)
            point = (w*r*r).sum()
            mixed = .5*point+.5*(d0*d0+d1*d1)
            assert .5*point-1e-13 <= mixed <= point+1e-13
        # Nonzero source and both differentiable endpoints on a physical-width panel.
        parameter = torch.tensor(.7, dtype=torch.float64, requires_grad=True)
        a, h = .31, .09
        times = a+h*x
        y = torch.exp(parameter*times)
        source = .2*y
        ends = torch.exp(parameter*torch.tensor([a, a+h], dtype=torch.float64))
        d0, d1 = interval_moments(y, source, ends, h, x, w)
        direct = ((parameter-.2)*y*w).sum()
        torch.testing.assert_close(d0, direct, rtol=1e-11, atol=1e-12)
        g0 = torch.autograd.grad(d0, parameter, retain_graph=True)[0]
        gd = torch.autograd.grad(direct, parameter)[0]
        torch.testing.assert_close(g0, gd, rtol=1e-11, atol=1e-12)


def test_panel_measure_and_frozen_calibration():
    c, m, grid = fixture()
    sampler = PanelSampler(c, grid, 928)
    for item in sampler.catalog:
        lengths = np.diff(item['bounds'], axis=1).ravel()
        np.testing.assert_allclose(item['probability'], lengths/lengths.sum())
        assert np.all(lengths > 0) and np.max(lengths) <= c['phase_panels']['widths'][item['scale']]+1e-12
    panels = sampler.sample(True)
    for window, mass in enumerate(c['window_masses']):
        for scale in (0, 1):
            assert abs(sum(p['mass'] for p in panels if p['window']==window and p['scale']==scale)-mass/2)<1e-15
    assert panels == PanelSampler(c, grid, 928).sample(True)
    values, gradients = phase_value_gradient(m, grid, panels, 8)
    chunked_values, chunked_gradients = phase_value_gradient(m, grid, panels, 8, chunk=1)
    for k in KINDS:
        np.testing.assert_allclose(values[k],chunked_values[k],rtol=2e-13,atol=2e-14)
        torch.testing.assert_close(gradients[k],chunked_gradients[k],rtol=2e-12,atol=2e-13)
    cal = calibrate(values, gradients)
    for arm, k in [('L','Ppsi'),('R','Pzeta'),('I','Iphi'),('RI','Izeta'),('RIM','Mzeta')]:
        np.testing.assert_allclose(cal['factors'][arm]*values[k], values['Pphi'], rtol=1e-13)
    np.testing.assert_allclose(cal['factors']['G']*np.linalg.norm(gradients['Pphi'].numpy()),
                               cal['G_target_gradient_norm'], rtol=1e-13)
    for kind in KINDS:
        value = panel_values(m, grid, panels, 8, kind=kind)[kind]
        torch.testing.assert_close(value, value.new_tensor(values[kind]), rtol=2e-13, atol=2e-14)
    records = {n:dict(values=values, gradient_norms=cal['gradient_norms']) for n in (8,16,32)}
    assert select_order(records)['selected_order']==8


def test_eight_arm_objective_differences_and_electrical_counts():
    from tests.test_phk_v23_b1 import fixture as visible_fixture, vector
    from pinn_pcm_sci.phk_v23_b1_observations import VisibleData, visible_bundle
    from pinn_pcm_sci.phk_v23_b1 import B1Electric
    from pinn_pcm_sci.phk_v23_lf11_elimination import TimeSampler
    from pinn_pcm_sci.phk_v23_phase_moments_run import PhaseExperiment
    from pinn_pcm_sci.phk_v23_phase_moments import ARMS, ARM_KIND
    c,m,grid,raw=visible_fixture()
    c['phase_panels']=dict(widths=[.025,.1],space_points=3,fixed_per_window_scale=1,order=8,chunk_panels=2)
    data=VisibleData(arrays=visible_bundle(raw))
    sampler=TimeSampler(c,m.physics,grid,82)
    pool=dict(times={1.175:dict(mass=1.,cells=np.arange(8),sides=sampler.boundaries(1.175,2))},initial=np.array([[0.,.2]]))
    pool['phase_panels']=PanelSampler(c,grid,819).sample(True)
    for p in m.heads['potential'].parameters():p.requires_grad_(False)
    vals,gs=phase_value_gradient(m,grid,pool['phase_panels'],8)
    cal=dict(aE=.2,bE=.7,phase=calibrate(vals,gs))
    results={}
    for arm in ARMS:
        exp=PhaseExperiment(c,m.state_dict(),data,'cpu',arm)
        v,parts=exp.objective({1.175:(4,1.)},pool,cal,.1,backward=True,counter='complete')
        results[arm]=(float(v),parts,vector(exp.model).clone())
        assert exp.calls['complete_objective_gradient_evaluations']==1
        assert exp.layer.backend.counts.forward_solves==1
        assert exp.layer.backend.counts.adjoint_solves==1
        assert exp.calls['optimizer_updates']==0
        if arm=='D':assert exp.phase_work['phase_derivative_positions']==0
        else:
            np.testing.assert_allclose(parts['phase'],vals[ARM_KIND[arm]]*cal['phase']['factors'][arm],rtol=1e-12,atol=1e-14)
            np.testing.assert_allclose(float(v)-results['D'][0],.1*(parts['thermal']+parts['phase'])/(3*cal['bE']),rtol=1e-10,atol=1e-12)
        for k in ('observation','boundary','initial'):
            np.testing.assert_allclose(parts[k],results['D'][1][k],rtol=0,atol=0)
    old=B1Electric(c,m.state_dict(),data,'cpu','D_E')
    value,_=old.objective({1.175:(4,1.)},pool,cal,.1,backward=True)
    np.testing.assert_allclose(float(value),results['D'][0],rtol=0,atol=0)
    torch.testing.assert_close(vector(old.model),results['D'][2],rtol=0,atol=0)
    # G changes only phase pressure: its isolated direction is exactly kappa P.
    isolated=PhaseExperiment(c,m.state_dict(),data,'cpu','P')
    value=panel_values(isolated.model,grid,pool['phase_panels'],8,kind='Pphi')['Pphi']
    (.1*(cal['phase']['factors']['G']-1)*value/(3*cal['bE'])).backward()
    torch.testing.assert_close(results['G'][2]-results['P'][2],vector(isolated.model),rtol=1e-7,atol=1e-11)


if __name__ == '__main__':
    suite = unittest.TestSuite(unittest.FunctionTestCase(v) for k,v in list(globals().items()) if k.startswith('test_'))
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
