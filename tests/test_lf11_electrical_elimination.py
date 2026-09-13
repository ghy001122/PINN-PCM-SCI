"""Zero-optimizer-update checks for the authorized implicit physical interface."""
import json
from pathlib import Path
import numpy as np
import torch
from pinn_pcm_sci.phk_benchmark import PhkGrid, solve_electric_field
from pinn_pcm_sci.phk_v23_lf11_electric_layer import ElectricalLayer
from pinn_pcm_sci.phk_v23_lf11_followup_fit import fit_model
from pinn_pcm_sci.phk_v23_lf11_elimination_physics import (
    grid_for, fields, coordinates, thermal_phase_residual, face_quadrature,
)


def small_grid():
    return PhkGrid.build(nx=8, nz=4, x_min=-1., x_max=1., z_min=0., z_max=1.)


def test_forward_mixed_boundary_and_half_resistance_deposition():
    grid = small_grid()
    sigma = torch.exp(torch.linspace(-2., 2., grid.cell_count, dtype=torch.float64))
    layer = ElectricalLayer(grid, .17)
    v, q = layer(sigma, .72)
    original = solve_electric_field(grid=grid, conductivity=sigma.numpy(), applied_voltage=.72, heater_width_fraction=.17)
    np.testing.assert_allclose(v.numpy(), original.potential, atol=1e-12, rtol=1e-11)
    np.testing.assert_allclose(q.numpy(), original.joule_density, atol=1e-11, rtol=1e-10)
    d = layer.deposition(v, sigma, .72)
    assert torch.max(torch.abs(layer.balance(v, sigma, .72))) < 1e-10
    torch.testing.assert_close(d['top_current'], d['bottom_current'], atol=1e-11, rtol=1e-10)
    torch.testing.assert_close(d['joule_power'], .72*d['top_current'], atol=1e-11, rtol=1e-10)
    torch.testing.assert_close(torch.sum(q*grid.dx*grid.dz), d['joule_power'])
    # Unequal material half resistances must receive unequal deposited heat.
    ri, rj, *_ = layer.resistances(sigma)
    torch.testing.assert_close(d['half_power_first']*rj, d['half_power_second']*ri)
    assert not torch.allclose(d['half_power_first'], d['half_power_second'])


def test_uniform_full_electrode_exact_linear_voltage_and_zero_drive():
    grid = small_grid()
    layer = ElectricalLayer(grid, 1.)
    sigma = torch.full((grid.cell_count,), 3., dtype=torch.float64, requires_grad=True)
    v, q = layer(sigma, .72)
    torch.testing.assert_close(v, torch.tensor(.72*grid.cell_z), atol=1e-12, rtol=1e-11)
    torch.testing.assert_close(q, torch.full_like(q, 3*.72**2), atol=1e-11, rtol=1e-10)
    before = layer.backend.snapshot()
    v0, q0 = layer(sigma, 0.)
    assert torch.count_nonzero(v0) == 0 and torch.count_nonzero(q0) == 0
    assert layer.backend.counts.factorizations == before['factorizations']
    (v0.sum()+q0.sum()).backward()
    assert torch.count_nonzero(sigma.grad) == 0


def test_full_conductivity_vjp_voltage_local_heat_and_combined_loss():
    grid = small_grid()
    layer = ElectricalLayer(grid, .17)
    rng = np.random.default_rng(917)
    x = torch.tensor(rng.normal(0., .6, grid.cell_count), requires_grad=True)
    direction = torch.tensor(rng.normal(size=grid.cell_count))
    direction /= torch.linalg.vector_norm(direction)
    target = torch.tensor(rng.uniform(.1, .4, grid.cell_count))
    weights = torch.linspace(.2, 1.3, grid.cell_count, dtype=torch.float64)
    def loss(value, kind):
        v, q = layer(value.exp(), .63)
        if kind == 'voltage':
            return torch.dot(weights, v.square())
        if kind == 'local_heat':
            return torch.dot(weights, (q-target).square())
        return ((v-target)/.72).square().mean()+((.1-4*q)/4).square().mean()
    for kind in ('voltage', 'local_heat', 'combined'):
        analytic = torch.dot(torch.autograd.grad(loss(x, kind), x)[0], direction)
        with torch.no_grad():
            eps = 1e-5
            numeric = (loss(x+eps*direction, kind)-loss(x-eps*direction, kind))/(2*eps)
        torch.testing.assert_close(analytic, numeric, rtol=1e-5, atol=1e-8)
    counts = layer.backend.snapshot()
    assert counts['adjoint_solves'] == 3
    assert counts['max_adjoint_scaled_residual'] <= 1e-10


def test_outputs_phase_equation_and_joint_neural_gradient():
    # Small artificial network only; no research checkpoint, label or optimizer.
    torch.set_num_threads(2)
    config = dict(seed=17, width=8, layers=2)
    model = fit_model(config)
    grid = grid_for(model.physics, 8, 4)
    layer = ElectricalLayer(grid, model.physics.heater_width_fraction)
    q = coordinates(grid, .175)
    f = fields(model, q, potential=True)
    inherited = model.read_only_output_diagnostics(q)
    for j, name in enumerate(('potential', 'temperature', 'phase')):
        torch.testing.assert_close(f[name], inherited.output.fields[:, j], rtol=0, atol=0)
    cells = np.arange(grid.cell_count)
    _, incidence = face_quadrature(grid, cells)
    assert incidence[0, 1] == incidence[1, 0]
    assert incidence[0, 3] == incidence[grid.nx, 2]
    from pinn_pcm_sci.phk_v22r_pinn import interior_residuals
    old_phase = interior_residuals(model, q)['phase'].ravel()
    fv = thermal_phase_residual(model, grid, .175, cells, torch.zeros(grid.cell_count, dtype=torch.float64))
    torch.testing.assert_close(fv['phase'], old_phase, atol=1e-12, rtol=1e-11)
    parameter = list(model.heads['temperature'].parameters())[-1]
    original = parameter.detach().clone()
    direction = torch.ones_like(parameter)
    def objective():
        out = fields(model, q)
        sigma = model.physics.conductivity(out['temperature'], out['phase'])
        v, heat = layer(sigma, .63)
        r = thermal_phase_residual(model, grid, .175, cells, heat)
        return ((v-.2)/.72).square().mean()+((out['temperature']-.1)/.45).square().mean()+((r['thermal']/4).square().mean()+(r['phase']/5).square().mean())/3
    analytic = torch.sum(torch.autograd.grad(objective(), parameter)[0]*direction)
    eps = 1e-5
    with torch.no_grad(): parameter.copy_(original+eps*direction)
    plus = float(objective().detach())
    with torch.no_grad(): parameter.copy_(original-eps*direction)
    minus = float(objective().detach())
    with torch.no_grad(): parameter.copy_(original)
    torch.testing.assert_close(analytic, torch.tensor((plus-minus)/(2*eps), dtype=torch.float64), rtol=1e-5, atol=1e-8)


def test_conditional_trigger_does_not_mix_claim_layers():
    from pinn_pcm_sci.phk_v23_lf11_elimination_evaluate import conditional_rule
    cfg = json.loads(Path('configs/phk_v23/lf11_elimination_sprint.json').read_text())
    def record(s, ph, bottom, power):
        return {'valid': True, 'metrics': dict(S=s, Ephi=ph, ET=1., EI=1., EV=1.,
                                               bottom_current_NRMSE=bottom, power_trace_NRMSE=power)}
    records = {'D_E': record(1., 1., 1., 1.), 'P_E': record(.8, .8, 1.2, 1.2),
               'B_E': record(.79, .79, 2., 2.)}
    decision = conditional_rule(records, cfg)
    assert decision['comparisons']['D_E']['A']['passed']
    assert not decision['layers']['B']['matched_pass']
    assert any(decision['layers']['B']['B_E_core_gain'].values())
    assert not decision['run_P_F']
    records['B_E'] = record(.8, 1., 2., 2.)
    assert conditional_rule(records, cfg)['run_P_F']


if __name__ == '__main__':
    import unittest
    suite = unittest.TestSuite(unittest.FunctionTestCase(value) for name, value in
        list(globals().items()) if name.startswith('test_') and callable(value))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
