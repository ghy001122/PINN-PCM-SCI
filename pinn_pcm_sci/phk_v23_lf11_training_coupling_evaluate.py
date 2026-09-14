"""Post-shutdown V30 scoring and predeclared same-layer, two-control decision."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import numpy as np
import torch
from .phk_v23_lf11 import ROOT,save_json,now
from .phk_v23_lf11_training_coupling import RUN,read
from .phk_v23_lf11_followup_fit import fit_model


def comparisons(records,cfg):
    from .phk_v23_lf11_evaluation import comparison
    from .phk_v23_lf11_joint_evaluate import functional_comparison
    def compare(c,b):
        return {'A':comparison(c,b,cfg['decision']),'B':functional_comparison(c,b,cfg)}
    invalid={'valid':False,'metrics':None}
    pairs={}
    for arm in ('F_raw','F_bal'):
        network=records.get(arm+'/network',invalid)
        projected=records.get(arm+'/projected',invalid)
        pairs[arm]={'E_vs_network':compare(records['P_E'],network),
                    'E_vs_projected':compare(records['P_E'],projected),
                    'projection_vs_network':compare(projected,network),
                    'network_vs_E':compare(network,records['P_E']),
                    'projected_vs_E':compare(projected,records['P_E'])}
    complete=all(records.get(arm+'/projected',{}).get('valid',False) and
                 records[arm+'/projected'].get('training_budget_complete',False) for arm in ('F_raw','F_bal'))
    layers={layer:bool(complete and all(pairs[arm]['E_vs_projected'][layer]['passed']
             for arm in ('F_raw','F_bal'))) for layer in ('A','B')}
    return {'comparisons':pairs,'both_controls_valid_and_complete':complete,
            'training_coupling_supported_layers':layers,'training_coupling_signal':any(layers.values()),
            'same_layer_across_both_controls_required':True,
            'historical_P_F_trigger_unchanged':True,'independent_confirmation_authorized':False,
            'scope':'training method package: different voltage observation maps, initial V, active parameters and full-grid hard versus sampled soft electric enforcement; not an isolated VJP intervention or proof of remaining-PDE necessity'}


def evaluate(root=RUN):
    proof=read(root/'compute-closure.json')
    completion_path=root/'training-and-own-inference-complete.json'
    completion=read(completion_path) if completion_path.exists() else {}
    recovered_complete=(completion.get('training_complete') and completion.get('own_inference_complete')
        and completion.get('gpu_remained_off') and not completion.get('training_repeated'))
    if not (proof.get('training_complete') or recovered_complete) or not proof.get('compute_stopped_before_reference_read'):
        raise ValueError('current run must finish and stop before reference access')
    if proof.get('mode')=='cloud' and not all(proof.get(k) for k in ('recovery_verified','shutdown_requested','instance_shutdown_confirmed')):
        raise ValueError('current authenticated recovery and shutdown required')
    cfg=read(root/'frozen-config.json');cfg['evaluation']={'readout':'COMMON_FV_FACE_FLUX_EDGE_DISSIPATION_V1'}
    torch.set_num_threads(cfg['cpu_threads'])
    saved=torch.load(root/'parent.pt',map_location='cpu',weights_only=False)
    physics=fit_model(cfg,saved['model_state_dict'],adapter=True).physics
    from .phk_benchmark import PhkControl
    from .phk_v22r_evaluator import load_reference,_event_summary,_physical_contract
    from .phk_v23_lf11_evaluation import metrics,field_rms
    from .phk_v23_lf11_followup_evaluate import add_power_metrics
    from .phk_v23_lf11_electric_layer import ElectricalLayer
    reference,identity=load_reference(PhkControl.FULL)
    hist=ROOT/cfg['historical_root']/'evaluation'
    old=read(hist/'results.json')
    background=read(ROOT/cfg['background_root']/'evaluation/results.json')
    if old['reference_sha256']!=identity or background['reference_sha256']!=identity:
        raise ValueError('reused historical scores and current evaluation must share one reference')
    grid,times=reference.grid,reference.time
    out=root/'evaluation';out.mkdir(exist_ok=False)
    layer=ElectricalLayer(grid,physics.heater_width_fraction)
    refheat=np.empty_like(reference.temperature)
    with torch.no_grad():
        for j,t in enumerate(times):
            sigma=physics.conductivity(torch.tensor(reference.temperature[j]),torch.tensor(reference.phase[j]))
            refheat[j]=layer.deposition(torch.tensor(reference.potential[j]),sigma,float(physics.waveform(torch.tensor(t,dtype=torch.float64))))['density'].numpy()
    qscale=field_rms(refheat,np.zeros_like(refheat),times)
    ev=_physical_contract().payload['qualification_event'];region=ev['roi']
    roi=(np.abs(grid.cell_x)<=region['abs_x_max'])&(grid.cell_z>=region['z_min'])&(grid.cell_z<=region['z_max'])
    events=_event_summary(reference.phase,time=times,roi=roi,period=physics.period,
                         phase_threshold=ev['phase_threshold'],event_fraction=ev['event_threshold_roi_fraction'])
    peaks=[c['peak_time_index'] for c in events['cycles']]
    records,traces={},{}
    projection_energy={}
    snapshots={'reference__'+k:getattr(reference,k)[peaks] for k in ('potential','temperature','phase')}
    for arm in cfg['roles']:
        if not (root/arm/'paired-readout-identity.json').exists():
            for mode in ('network','projected'):
                records[arm+'/'+mode]={'valid':False,'metrics':None,'training_budget_complete':False,'reason':'no completed paired prediction'}
            continue
        terminal=read(root/arm/'terminal.json')
        lb=terminal['lbfgs']
        finished_fixed_stage=(lb['evaluations']==cfg['lbfgs_evaluations'] and
            lb['termination'] in ('EVALUATION_BUDGET_EXHAUSTED','EVALUATION_BUDGET_EXHAUSTED_TRIAL_ROLLED_BACK')) or lb['termination']=='GRADIENT_CONVERGED'
        complete=(terminal['adam_updates']==cfg['branch_updates'] and
                  terminal['status']=='VALID_FIXED_ENDPOINT' and finished_fixed_stage)
        preserved=None
        for mode in ('network','projected'):
            role=arm+'/'+mode;folder=root/arm/mode
            with np.load(folder/'prediction.npz',allow_pickle=False) as data:
                for key,axis in (('x',grid.x_centers),('z',grid.z_centers),('time',times)): np.testing.assert_array_equal(data[key],axis)
                predicted={k:data[k] for k in ('potential','temperature','phase')};heat=data['joule_density']
            if preserved is None: preserved={k:predicted[k].copy() for k in ('temperature','phase')}
            else:
                for k in preserved: np.testing.assert_array_equal(predicted[k],preserved[k])
            record,trace=metrics(predicted,reference,physics,cfg)
            if record['valid']:
                add_power_metrics(record,trace,times,reference.top_current,reference.joule_power)
                record['metrics']['local_joule_NRMSE']=field_rms(heat,refheat,times)/qscale if qscale>1e-12 else None
            if trace:
                with np.load(folder/'own-readout.npz',allow_pickle=False) as own:
                    for key in ('top_current','bottom_current','joule_power'):
                        np.testing.assert_allclose(own[key],trace[key],rtol=1e-10,atol=1e-11)
            record.update(training_budget_complete=complete,training_termination=lb['termination'],readout=mode,learned_state=arm,
                          electrical_inference=read(folder/'prediction.json'))
            records[role]=record;traces[role]=trace
            for k,v in predicted.items(): snapshots[role+'__'+k]=v[peaks].copy()
            snapshots[role+'__joule_density']=heat[peaks].copy()
            print(json.dumps(dict(evaluated=role,valid=record['valid'],metrics=record['metrics'])),flush=True)
        nr,pr=records[arm+'/network'],records[arm+'/projected']
        for key in ('S','Ephi','ET'):
            if nr['valid'] and pr['valid']: assert nr['metrics'][key]==pr['metrics'][key]
        if nr['valid'] and pr['valid']: assert nr['cycles']==pr['cycles']
        if not traces[arm+'/network'] or not traces[arm+'/projected']:
            projection_energy[arm]=dict(available=False,reason='invalid fields; paired trace diagnostic unavailable')
            continue
        pnet=traces[arm+'/network']['joule_power'];psolved=traces[arm+'/projected']['joule_power']
        gap=pnet-psolved
        tolerance=1e-10*max(1.,float(np.max(np.abs(pnet))),float(np.max(np.abs(psolved))))
        projection_energy[arm]=dict(minimum_power_gap=float(gap.min()),numerical_tolerance=tolerance,
            nonnegative_within_tolerance=bool(gap.min()>=-tolerance),
            network_integrated_power=float(np.trapezoid(pnet,times)),
            projected_integrated_power=float(np.trapezoid(psolved,times)),
            integral_power_gap=float(np.trapezoid(gap,times)),
            interpretation='Same-conductivity Dirichlet-energy minimization; not a prediction-gain criterion. The quadratic identity is analytically derived, not independently matrix-recomputed here.')
    for role in ('E0','D_E','P_E','B_E'):
        records[role]=copy.deepcopy(old['records'][role]);records[role]['origin']='V28_FIXED_1500_ADAM_300_EVALUATIONS_REUSED'
    with np.load(hist/'traces.npz',allow_pickle=False) as data:
        for role in ('E0','D_E','P_E','B_E'): traces[role]={k.split('__',1)[1]:data[k].copy() for k in data.files if k.startswith(role+'__')}
    for role in ('D_C','P1','P_kappa'):
        records['V29_'+role]=copy.deepcopy(background['records'][role])
        records['V29_'+role]['origin']='DIFFERENT_LONGER_DEVELOPMENT_HISTORY_NOT_MATCHED_CONTROL'
    decision=comparisons(records,cfg)
    result=dict(status='COMPLETED_TRAINING_COUPLING_POSTHOC_COMPARISON',records=records,
                projection_energy_diagnostic=projection_energy,
                decision=decision,reference_sha256=identity,recorded_utc=now(),
                scope='one inherited E0 parent, exposed nominal sparse observations; no independent initialization or case')
    save_json(out/'results.json',result);save_json(out/'method-decision.json',decision)
    np.savez_compressed(out/'traces.npz',time=times,reference_current=reference.top_current,
        reference_power=reference.joule_power,reference_roi_fraction=events['roi_fraction'],
        **{role+'__'+k:v for role,tr in traces.items() for k,v in tr.items()})
    np.savez_compressed(out/'snapshots.npz',x=grid.x_centers,z=grid.z_centers,phase_times=times[peaks],**snapshots)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=RUN)
    evaluate(p.parse_args().root)
