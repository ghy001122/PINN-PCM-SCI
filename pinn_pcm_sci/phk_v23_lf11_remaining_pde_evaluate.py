"""V29 post-shutdown evaluation reuses V28 definitions and frozen old results."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import torch
from .phk_v23_lf11 import save_json, now
from .phk_v23_lf11_remaining_pde import RUN
from .phk_v23_lf11_followup_fit import fit_model


def conditional_rule(records, config):
    from .phk_v23_lf11_evaluation import comparison
    from .phk_v23_lf11_joint_evaluate import functional_comparison
    candidates=[r for r in config['roles'] if r!='D_C']
    pairs={}
    support={}
    for role in candidates:
        pairs[role]={name:{'A':comparison(records[role],records[name],config['decision']),
                          'B':functional_comparison(records[role],records[name],config)}
                     for name in ('D_C','D_E','B_E')}
        if role=='P_kappa':
            pairs[role]['P1']={'A':comparison(records[role],records['P1'],config['decision']),
                              'B':functional_comparison(records[role],records['P1'],config)}
        support[role]={}
        for layer,core,keys in (
            ('A',('S','Ephi'),('S','Ephi','ET','EI','EV')),
            ('B',('bottom_current_NRMSE','power_trace_NRMSE'),
             ('bottom_current_NRMSE','power_trace_NRMSE','S','Ephi','ET','EI','EV'))):
            ni={}
            tol=config['decision']['absolute_tolerance']
            for baseline in ('D_E','B_E'):
                c,b=records[role]['metrics'],records[baseline]['metrics']
                valid=records[role]['valid'] and records[baseline]['valid'] and all(c.get(k) is not None and b.get(k) is not None for k in keys)
                ni[baseline]={k:bool(c[k]<=b[k]+max(.05*b[k],tol.get(k,1e-6))) for k in keys} if valid else {}
            matched=pairs[role]['D_C'][layer]['passed']
            eligible=bool(matched and all(ni[n] and all(ni[n].values()) for n in ni))
            support[role][layer]={'matched_vs_D_C':matched,'historical_noninferiority':ni,'supported':eligible}
    selected=next((r for r in ('P1','P_kappa') if r in support and any(v['supported'] for v in support[r].values())),None)
    return {'comparisons':pairs,'support':support,'selected_simple_first':selected,
            'P_F_proposal_supported':selected is not None,'run_P_F':False,
            'P_F_status':'PROPOSED_NOT_AUTHORIZED' if selected else 'NOT_TRIGGERED_NOT_RUN',
            'kappa_increment_vs_P1': pairs.get('P_kappa',{}).get('P1'),
            'same_layer_required':True,'strict_device_gate_separate':True,
            'no_reference_endpoint_or_kappa_selection':True}


def common_heat_balance(fields, heat, grid, physics, times):
    """Shared a-posteriori proxy; NOT the AD surface quadrature used in training."""
    enthalpy = fields['temperature']+physics.latent_ratio*fields['phase']
    dt = np.gradient(enthalpy, times, axis=0, edge_order=2)
    diffusion = (grid.thermal_laplacian(physics.thermal_robin_biot) @ fields['temperature'].T).T
    residual = dt+physics.volumetric_cooling*fields['temperature']-physics.thermal_diffusivity*diffusion-physics.joule_gain*heat
    rms_t = np.sqrt(np.mean(residual**2, axis=1))
    signed = np.sum(residual*grid.cell_volumes[None], axis=1)
    rms = float(np.sqrt(np.trapezoid(rms_t**2, times)/(times[-1]-times[0])))
    return {'rms': rms, 'definition': 'common sampled-time derivative and FV thermal boundary operator; diagnostic, not training loss or continuum truth'}, rms_t, signed


def evaluate(root=RUN):
    proof = json.loads((root/'compute-closure.json').read_text())
    if not proof.get('training_complete') or not proof.get('compute_stopped_before_reference_read'):
        raise ValueError('current training closure required before reference access')
    if proof.get('mode') == 'cloud' and not all(proof.get(k) for k in ('recovery_verified', 'shutdown_requested', 'instance_shutdown_confirmed')):
        raise ValueError('actual cloud recovery and shutdown confirmation required')
    cfg = json.loads((root/'frozen-config.json').read_text())
    roles = cfg['roles']
    for role in roles:
        if json.loads((root/role/'terminal.json').read_text())['status'] != 'VALID_FIXED_ENDPOINT':
            raise ValueError(f'{role} lacks a valid fixed endpoint')
    cfg = json.loads((root/'frozen-config.json').read_text())
    cfg['evaluation'] = {'readout': 'COMMON_FV_FACE_FLUX_EDGE_DISSIPATION_V1'}
    torch.set_num_threads(cfg['cpu_threads'])
    parent = torch.load(root/'parent.pt', map_location='cpu', weights_only=False)
    physics = fit_model(cfg, parent['model_state_dict'], adapter=True).physics
    # First reference-field read is below the current compute-closure check.
    from .phk_benchmark import PhkControl
    from .phk_v22r_evaluator import load_reference, _event_summary, _physical_contract
    from .phk_v23_lf11_evaluation import metrics, field_rms, time_rms
    from .phk_v23_lf11_followup_evaluate import add_power_metrics
    from .phk_v23_lf11_electric_layer import ElectricalLayer
    reference, identity = load_reference(PhkControl.FULL)
    grid, times = reference.grid, reference.time
    output = root/'evaluation'
    output.mkdir(exist_ok=False)
    layer = ElectricalLayer(grid, physics.heater_width_fraction)
    refheat = np.empty_like(reference.temperature)
    with torch.no_grad():
        for j, t in enumerate(times):
            st = physics.conductivity(torch.tensor(reference.temperature[j]), torch.tensor(reference.phase[j]))
            refheat[j] = layer.deposition(torch.tensor(reference.potential[j]), st, float(physics.waveform(torch.tensor(t, dtype=torch.float64))))['density'].numpy()
    ev = _physical_contract().payload['qualification_event']
    region = ev['roi']
    roi = (np.abs(grid.cell_x) <= region['abs_x_max']) & (grid.cell_z >= region['z_min']) & (grid.cell_z <= region['z_max'])
    events = _event_summary(reference.phase, time=times, roi=roi, period=physics.period,
                           phase_threshold=ev['phase_threshold'], event_fraction=ev['event_threshold_roi_fraction'])
    peaks = [c['peak_time_index'] for c in events['cycles']]
    heat_peaks = [int(np.flatnonzero((times >= lo) & (times <= hi))[np.argmax(reference.joule_power[(times >= lo) & (times <= hi)])]) for lo, hi in (cfg['windows'][0], cfg['windows'][2])]
    records, traces = {}, {}
    snapshots = {'reference__'+k: getattr(reference, k)[peaks] for k in ('potential', 'temperature', 'phase')}
    snapshots['reference__heat_temperature'] = reference.temperature[heat_peaks]
    snapshots['reference__joule_density'] = refheat[heat_peaks]
    refbalance, refbalance_t, refsigned = common_heat_balance(
        {'temperature': reference.temperature, 'phase': reference.phase}, refheat, grid, physics, times)
    for role in roles:
        with np.load(root/role/'prediction.npz', allow_pickle=False) as source:
            for key, axis in (('x', grid.x_centers), ('z', grid.z_centers), ('time', times)):
                np.testing.assert_array_equal(source[key], axis)
            predicted = {k: source[k] for k in ('potential', 'temperature', 'phase')}
            heat = source['joule_density']
        record, trace = metrics(predicted, reference, physics, cfg)
        if record['valid']:
            add_power_metrics(record, trace, times, reference.top_current, reference.joule_power)
            qscale = field_rms(refheat, np.zeros_like(refheat), times)
            record['metrics']['local_joule_NRMSE'] = field_rms(heat, refheat, times)/qscale if qscale > 1e-12 else None
            balance, bal_t, bal_signed = common_heat_balance(predicted, heat, grid, physics, times)
            record['common_thermal_balance'] = balance
            trace.update(thermal_balance_rms=bal_t, thermal_balance_signed=bal_signed)
        with np.load(root/role/'own-readout.npz', allow_pickle=False) as own:
            for k in ('top_current', 'bottom_current', 'joule_power'):
                np.testing.assert_allclose(own[k], trace[k], rtol=1e-10, atol=1e-11)
        record['electrical_inference'] = json.loads((root/role/'prediction.json').read_text())
        records[role], traces[role] = record, trace
        snapshots.update({role+'__'+k: v[peaks].copy() for k, v in predicted.items()})
        snapshots[role+'__heat_temperature'] = predicted['temperature'][heat_peaks].copy()
        snapshots[role+'__joule_density'] = heat[heat_peaks].copy()
        print(json.dumps({'evaluated': role, 'metrics': record['metrics']}), flush=True)
        del predicted, heat
    # Old fixed metrics/predictions are reused, never reevaluated or retrained.
    from .phk_v23_lf11 import ROOT
    historical = ROOT/cfg['historical_root']/'evaluation'
    previous = json.loads((historical/'results.json').read_text())
    for role in ('E0','D_E','P_E','B_E'):
        records[role]=previous['records'][role]
    with np.load(historical/'traces.npz',allow_pickle=False) as old:
        for role in ('E0','D_E','P_E','B_E'):
            traces[role]={key.split('__',1)[1]:old[key].copy() for key in old.files if key.startswith(role+'__')}
    with np.load(historical/'snapshots.npz',allow_pickle=False) as old:
        for key in old.files:
            if any(key.startswith(role+'__') for role in ('E0','D_E','P_E','B_E')): snapshots[key]=old[key].copy()
    decision = conditional_rule(records, cfg)
    result = {'status': 'VALID_REMAINING_PDE_FIXED_COUNTERFACTUAL_EVALUATION', 'records': records,
              'conditional_decision': decision, 'reference_sha256': identity, 'recorded_utc': now(),
              'common_reference_thermal_balance': refbalance,
              'scope': 'specified V28 D_E parent and same exposed nominal observations; fixed terminal comparisons, no new initialization, OOD or material calibration'}
    save_json(output/'results.json', result)
    save_json(output/'conditional-decision.json', decision)
    np.savez_compressed(output/'traces.npz', time=times, reference_current=reference.top_current,
        reference_power=reference.joule_power, reference_roi_fraction=events['roi_fraction'],
        reference_thermal_balance=refbalance_t, reference_thermal_balance_signed=refsigned,
        **{role+'__'+k: v for role, tr in traces.items() for k,v in tr.items()})
    np.savez_compressed(output/'snapshots.npz', x=grid.x_centers, z=grid.z_centers,
        phase_times=times[peaks], heat_times=times[heat_peaks], **snapshots)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=RUN)
    args = p.parse_args()
    evaluate(args.root)
