"""Own-field inference and zero-update checks without reading reference fields."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import torch
from .phk_v23_lf11 import SparseData, save_json, now, ROOT
from .phk_v23_lf11_elimination import RUN, Experiment, load_inputs, TimeSampler
from .phk_v23_lf11_elimination_physics import fields, grid_for, coordinates, thermal_phase_residual
from .phk_v23_lf11_electric_layer import ElectricalLayer
from .phk_v23_lf11_followup_fit import fit_model
from .phk_v23_lf11_readout import interpolate_sparse


def baseline(data, grid, times, physics):
    # Contact/waveform variants only alter V. Their T and phase are B_logit.
    predicted = interpolate_sparse(data, grid.x_centers, grid.z_centers, times, physics, 'B_logit')
    return {k: predicted[k] for k in ('temperature', 'phase')}


def infer_time(model, layer, when, device, role, baseline_fields=None, chunk=4096):
    grid = layer.grid
    if baseline_fields is None:
        q = coordinates(grid, when, device=device)
        pieces = []
        with torch.no_grad():
            for lo in range(0, len(q), chunk):
                f = fields(model, q[lo:lo+chunk], potential=role == 'P_F')
                pieces.append({k: v.cpu().numpy() for k, v in f.items() if k != 'delta_logit'})
        predicted = {k: np.concatenate([v[k] for v in pieces]) for k in pieces[0]}
    else:
        predicted = baseline_fields
    # The solver backend lives on CPU for inference; no network derivative is needed.
    sigma = np.exp(model.physics.conductivity_temperature_gain*predicted['temperature']+
                   np.log(model.physics.conductivity_phase_ratio)*predicted['phase']**2*(3-2*predicted['phase']))
    st = torch.tensor(sigma, dtype=torch.float64)
    u = float(model.physics.waveform(torch.tensor(when, dtype=torch.float64)))
    with torch.no_grad():
        if role == 'P_F':
            vt = torch.tensor(predicted['potential'], dtype=torch.float64)
            heat = layer.deposition(vt, st, u)['density']
        else:
            vt, heat = layer(st, u)
            predicted['potential'] = vt.numpy()
        d = layer.deposition(vt, st, u)
    return {**predicted, 'joule_density': heat.numpy()}, {k: float(d[k]) for k in
        ('top_current', 'bottom_current', 'joule_power', 'internal_power', 'top_power', 'bottom_power')}


def zero_checks(root=RUN, device='cpu'):
    cfg = json.loads((root/'frozen-config.json').read_text())
    torch.set_num_threads(cfg['cpu_threads'])
    state, data = load_inputs(cfg, device)
    exp = Experiment(cfg, state, data, device, 'P_E')
    result = {'status': 'ZERO_UPDATE_INTERFACE_CHECKS', 'reference_read': False,
              'optimizer_updates': 0, 'times': cfg['zero_update_times'], 'records': {}, 'gradients': {}}
    # Exact full observation measure: compare against the inherited implementation
    # using P_F's unchanged raw network V, so both sides represent the same function.
    from .phk_v23_lf11_joint import full_observation
    pf = Experiment(cfg, state, data, device, 'P_F')
    if device == 'cpu':
        with torch.no_grad():
            inherited = full_observation(pf.model, data, cfg)
            ours = sum(float(pf.obs.loss(pf.model, group, None, 'P_F')[0]) for group in pf.obs.groups().values())
        np.testing.assert_allclose(ours, inherited['observation'], atol=1e-14, rtol=1e-11)
        result['complete_observation_identity_error'] = abs(ours-inherited['observation'])
    # Coordinate-only fixed zero-update comparison; no result selects a parent.
    be = baseline(data, exp.grid, np.asarray(cfg['zero_update_times']), exp.model.physics)
    for role in ('E0', 'B_E'):
        layer = ElectricalLayer(exp.grid, exp.model.physics.heater_width_fraction)
        records = []
        for j, t in enumerate(cfg['zero_update_times']):
            supplied = {k: v[j] for k, v in be.items()} if role == 'B_E' else None
            f, d = infer_time(exp.model, layer, t, device, role, supplied)
            d.update(time=t, current_gap=d['top_current']-d['bottom_current'],
                     power_gap=d['joule_power']-float(exp.model.physics.waveform(torch.tensor(t, dtype=torch.float64)))*d['top_current'],
                     temperature_max=float(f['temperature'].max()), phase_max=float(f['phase'].max()))
            records.append(d)
        result['records'][role] = {'values': records, 'electrical_counts': layer.backend.snapshot()}
    # Actual 80x40 parent and both parameter heads: joint observed voltage,
    # thermal/phase PDE and boundary gradients, at one predeclared observation time.
    t = float(exp.obs.times[9])
    sampler = TimeSampler(cfg, exp.model.physics, exp.grid, cfg['audit_pool_seed'])
    batch = {'times': {t: {'mass': 1., 'cells': np.arange(0, exp.grid.cell_count, 25),
                          'sides': sampler.boundaries(t, 8)}},
             'initial': np.array([[0., .2], [.5, .5]])}
    groups = {t: (9, 1./exp.obs.proposal[9])}
    cal = json.loads((root/'calibration.json').read_text())
    def objective(backward=False):
        return exp.objective(groups, batch, cal, .1, backward=backward)[0]
    exp.model.zero_grad(set_to_none=True)
    analytic_loss = objective(True)
    for name in ('temperature', 'phase'):
        p = list(exp.model.heads[name].parameters())[-1]
        original, analytic = p.detach().clone(), float(p.grad.sum())
        eps = 1e-5
        with torch.no_grad(): p.copy_(original+eps)
        plus = float(objective().detach())
        with torch.no_grad(): p.copy_(original-eps)
        minus = float(objective().detach())
        with torch.no_grad(): p.copy_(original)
        numeric = (plus-minus)/(2*eps)
        error = abs(analytic-numeric)
        passed = error <= max(cfg['gradient_absolute_tolerance'], cfg['gradient_relative_tolerance']*max(abs(numeric), abs(analytic)))
        result['gradients'][name] = {'analytic': analytic, 'central_difference': numeric,
            'absolute_error': error, 'relative_error': error/max(abs(numeric), abs(analytic), 1e-12), 'passed': passed}
        if not passed: raise AssertionError(result['gradients'][name])
    result['joint_check_statistics'] = exp.statistics()
    result['joint_loss'] = float(analytic_loss)
    result['device'] = device
    path = root/('zero-update-checks-'+device.replace(':', '-')+'.json')
    if path.exists(): raise FileExistsError('zero-update check already recorded; reuse it')
    save_json(path, result)
    print(json.dumps(result), flush=True)


def predict(root, role, device='cpu'):
    cfg = json.loads((root/'frozen-config.json').read_text())
    torch.set_num_threads(cfg['cpu_threads'])
    source = root/'parent.pt' if role in ('E0', 'B_E') else root/role/'checkpoint.pt'
    saved = torch.load(source, map_location='cpu', weights_only=False)
    model = fit_model(cfg, saved['model_state_dict'], adapter=True).to(device)
    from .phk_v22r_prediction import _evaluation_axes
    from .phk_v22r_training import PhkTrainingConfig
    x, z, times = _evaluation_axes(PhkTrainingConfig(arm='STRONG_RAW', case_control='FULL'))
    if (len(x), len(z)) != tuple(cfg['inference_grid']): raise ValueError('changed frozen query grid')
    grid = grid_for(model.physics, len(x), len(z))
    np.testing.assert_array_equal(x, grid.x_centers)
    np.testing.assert_array_equal(z, grid.z_centers)
    layer = ElectricalLayer(grid, model.physics.heater_width_fraction, cfg['linear_tolerance'])
    folder = root/role
    folder.mkdir(exist_ok=True)
    destination = folder/'prediction.npz'
    if destination.exists(): raise FileExistsError('fixed own prediction exists; reuse it')
    array = {k: np.empty((len(times), grid.cell_count)) for k in ('potential', 'temperature', 'phase', 'joule_density')}
    traces = {}
    data = SparseData(ROOT/cfg['sparse']) if role == 'B_E' else None
    prepared_baseline = baseline(data, grid, times, model.physics) if data else None
    for j, t in enumerate(times):
        supplied = {k: v[j] for k, v in prepared_baseline.items()} if prepared_baseline else None
        f, d = infer_time(model, layer, t, device, role, supplied)
        for k in array: array[k][j] = f[k]
        for k, v in d.items(): traces.setdefault(k, []).append(v)
        if j % 200 == 0: print(json.dumps({'prediction_role': role, 'time_index': j, 'total': len(times)}), flush=True)
    with destination.open('xb') as stream:
        np.savez_compressed(stream, x=x, z=z, time=times, **array)
    np.savez_compressed(folder/'own-readout.npz', time=times, **{k: np.asarray(v) for k,v in traces.items()})
    save_json(folder/'prediction.json', {'status': 'FIXED_OWN_PREDICTION', 'role': role, 'grid': [len(x), len(z)],
        'times': len(times), 'electrical_counts': layer.backend.snapshot(), 'reference_read': False,
        'fine_electrical_solve_used': role != 'P_F', 'device': device, 'created_utc': now()})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'predict'])
    parser.add_argument('--root', type=Path, default=RUN)
    parser.add_argument('--device', default='cpu')
    parser.add_argument('--role', choices=['E0', 'B_E', 'D_E', 'P_E', 'P_F'])
    args = parser.parse_args()
    if args.action == 'check': zero_checks(args.root, args.device)
    elif args.role: predict(args.root, args.role, args.device)
    else: parser.error('--role required for own-field prediction')
