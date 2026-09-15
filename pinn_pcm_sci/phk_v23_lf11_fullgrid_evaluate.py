"""Post-shutdown V31 scoring. Reuses the original scientific metrics and gates."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import numpy as np
import torch
from .phk_v23_lf11 import ROOT,save_json,now
from .phk_v23_lf11_fullgrid import RUN
from .phk_v23_lf11_training_coupling import read


def pair(candidate,base,cfg):
    from .phk_v23_lf11_evaluation import comparison
    from .phk_v23_lf11_joint_evaluate import functional_comparison
    if any(record.get('training_budget_complete') is False for record in (candidate,base)):
        return {layer:dict(passed=False,reason='matched_training_endpoint_incomplete') for layer in ('A','B')}
    return dict(A=comparison(candidate,base,cfg['decision']),B=functional_comparison(candidate,base,cfg))


def noninferior(candidate,base,keys,cfg):
    c,b=candidate['metrics'],base['metrics']
    tol=cfg['decision']['absolute_tolerance']
    return {k:bool(c.get(k) is not None and b.get(k) is not None and
        c[k]<=b[k]+max(.05*b[k],tol.get(k,1e-6))) for k in keys}


def select_soft(records,cfg):
    """No scalar ranking: device domination must also preserve field guards."""
    names=[r for r in cfg['comparator_selection']['candidates'] if
           records.get(r+'/projected',{}).get('valid') and
           records[r+'/projected'].get('training_budget_complete')]
    domination={r:[] for r in names};details={}
    axes=cfg['comparator_selection']['device_axes']
    for a in names:
        for b in names:
            if a==b: continue
            ra,rb=records[a+'/projected'],records[b+'/projected']
            ma,mb=ra['metrics'],rb['metrics']
            identifiable=all(ma.get(k) is not None and mb.get(k) is not None for k in axes)
            ni=noninferior(ra,rb,cfg['comparator_selection']['field_guard'],cfg)
            dominates=bool(identifiable and all(ma[k]<=mb[k]+1e-6 for k in axes)
                and any(ma[k]<mb[k]-1e-6 for k in axes) and all(ni.values()))
            details[a+'_vs_'+b]=dict(dominates=dominates,field_noninferiority=ni)
            if dominates: domination[b].append(a)
    frontier=[r for r in names if not domination[r]]
    selected=frontier[0] if len(frontier)==1 else None
    return dict(status='UNIQUE_COMPARATOR_LOCKED' if selected else 'NO_UNIQUE_COMPARATOR_STOP_STAGE_B',
        selected=selected,valid_candidates=names,nondominated=frontier,dominated_by=domination,
        pair_details=details,stage_B_enabled=selected is not None,development_selection=True,
        reference_checkpoint_selection=False,scalarization_used=False)


def stage_a_decision(records,cfg):
    pairs={}
    for soft in ('F_raw','F_bal','F_full'):
        for mode in ('network','projected'):
            name=soft+'/'+mode
            if name in records:
                pairs['E_vs_'+name]=pair(records['P_E'],records[name],cfg)
                pairs[name+'_vs_E']=pair(records[name],records['P_E'],cfg)
        if all(soft+'/'+m in records for m in ('network','projected')):
            pairs[soft+'_projection_vs_network']=pair(records[soft+'/projected'],records[soft+'/network'],cfg)
    for c,b in [('F_full/projected','F_raw/projected'),('F_raw/projected','F_full/projected')]:
        if c in records and b in records:pairs[c+'_vs_'+b]=pair(records[c],records[b],cfg)
    usable=all(records.get(r+'/projected',{}).get('valid') and records[r+'/projected'].get('training_budget_complete')
               for r in ('F_raw','F_bal','F_full'))
    layers={k:bool(usable and all(pairs['E_vs_'+s+'/projected'][k]['passed'] for s in ('F_raw','F_bal','F_full'))) for k in ('A','B')}
    return dict(comparisons=pairs,all_soft_valid_complete=usable,E_same_layer_all_soft=layers,
        selection=select_soft(records,cfg),historical_results_unchanged=True,
        claim_scope='Spatial integral only; temporal enforcement, voltage initialization, parameterization and gradient maps still differ.')


def stage_b_decision(records,cfg):
    soft=cfg['selected_soft'];e=records['E/projected'];f=records[soft+'/projected']
    return dict(seed=cfg['seed'],selected_soft=soft,E_vs_soft=pair(e,f,cfg),soft_vs_E=pair(f,e,cfg),
        E_vs_B_E=pair(e,records['B_E'],cfg),soft_vs_B_E=pair(f,records['B_E'],cfg),
        no_new_D_E=True,remaining_PDE_necessity='UNKNOWN',historical_seed17_not_pooled=True,
        qualification='one clean initialization pair on already exposed nominal support; not a new case or formal OOD')


def evaluate(root=RUN,stage='A'):
    root=Path(root);proof=read(root/'compute-closure.json')
    if not (proof.get('training_complete') and proof.get('compute_stopped_before_reference_read')):
        raise ValueError('completed current batch and compute closure required')
    if proof.get('mode')=='cloud' and not all(proof.get(k) for k in
        ('recovery_verified','shutdown_requested','instance_shutdown_confirmed')):
        raise ValueError('current authenticated cloud shutdown required')
    cfg=read(root/'frozen-config.json');cfg['evaluation']={'readout':'COMMON_FV_FACE_FLUX_EDGE_DISSIPATION_V1'}
    torch.set_num_threads(cfg['cpu_threads'])
    from .phk_v23_lf11_followup_fit import fit_model
    saved=torch.load(root/'parent.pt',map_location='cpu',weights_only=False)
    physics=fit_model(cfg,saved['model_state_dict'],adapter=True).physics
    from .phk_benchmark import PhkControl
    from .phk_v22r_evaluator import load_reference,_event_summary,_physical_contract
    from .phk_v23_lf11_evaluation import metrics,field_rms
    from .phk_v23_lf11_followup_evaluate import add_power_metrics
    from .phk_v23_lf11_electric_layer import ElectricalLayer
    # This is the first full-reference access, after the current shutdown check.
    reference,identity=load_reference(PhkControl.FULL)
    previous=ROOT/cfg['training_coupling_root']/'evaluation'
    old=read(previous/'results.json')
    if old['reference_sha256']!=identity:raise ValueError('reference identity differs from reused controls')
    grid,times=reference.grid,reference.time
    out=root/'evaluation';out.mkdir(exist_ok=False)
    layer=ElectricalLayer(grid,physics.heater_width_fraction)
    refheat=np.empty_like(reference.temperature)
    with torch.no_grad():
        for j,t in enumerate(times):
            sigma=physics.conductivity(torch.tensor(reference.temperature[j]),torch.tensor(reference.phase[j]))
            refheat[j]=layer.deposition(torch.tensor(reference.potential[j]),sigma,float(physics.waveform(torch.tensor(t,dtype=torch.float64))))['density'].numpy()
    qscale=field_rms(refheat,np.zeros_like(refheat),times)
    ev=_physical_contract().payload['qualification_event'];reg=ev['roi']
    roi=(np.abs(grid.cell_x)<=reg['abs_x_max'])&(grid.cell_z>=reg['z_min'])&(grid.cell_z<=reg['z_max'])
    events=_event_summary(reference.phase,time=times,roi=roi,period=physics.period,
        phase_threshold=ev['phase_threshold'],event_fraction=ev['event_threshold_roi_fraction'])
    peaks=[c['peak_time_index'] for c in events['cycles']]
    records={};traces={};snapshots={'reference__'+k:getattr(reference,k)[peaks] for k in ('potential','temperature','phase')}
    for role in cfg['roles']:
        terminal=read(root/role/'terminal.json');lb=terminal['lbfgs']
        stop=lb['termination']
        accepted_stop=(stop in ('GRADIENT_CONVERGED','NO_ACCEPTED_PROGRESS') or
            (lb['evaluations']==cfg['lbfgs_evaluations'] and stop in
             ('EVALUATION_BUDGET_EXHAUSTED','EVALUATION_BUDGET_EXHAUSTED_TRIAL_ROLLED_BACK')))
        complete=(terminal['status']=='VALID_FIXED_ENDPOINT' and terminal['adam_updates']==cfg['branch_updates'] and accepted_stop)
        modes=['projected'] if role=='E' else ['network','projected']
        prior=None
        for mode in modes:
            name=role+'/'+mode;folder=root/role/mode
            with np.load(folder/'prediction.npz',allow_pickle=False) as data:
                for key,axis in (('x',grid.x_centers),('z',grid.z_centers),('time',times)):
                    np.testing.assert_array_equal(data[key],axis)
                predicted={k:data[k] for k in ('potential','temperature','phase')};heat=data['joule_density']
            if prior is not None:
                for k in ('temperature','phase'):np.testing.assert_array_equal(prior[k],predicted[k])
            else:prior={k:predicted[k].copy() for k in ('temperature','phase')}
            record,trace=metrics(predicted,reference,physics,cfg)
            if record['valid']:
                add_power_metrics(record,trace,times,reference.top_current,reference.joule_power)
                record['metrics']['local_joule_NRMSE']=field_rms(heat,refheat,times)/qscale if qscale>1e-12 else None
            if trace:
                with np.load(folder/'own-readout.npz',allow_pickle=False) as own:
                    for k in ('top_current','bottom_current','joule_power'):
                        np.testing.assert_allclose(own[k],trace[k],rtol=1e-10,atol=1e-11)
            record.update(training_budget_complete=complete,training_termination=stop,readout=mode,
                learned_state=role,electrical_inference=read(folder/'prediction.json'))
            records[name]=record;traces[name]=trace
            for k,v in predicted.items():snapshots[name+'__'+k]=v[peaks].copy()
            snapshots[name+'__joule_density']=heat[peaks].copy()
            print(json.dumps(dict(evaluated=name,valid=record['valid'],metrics=record['metrics'])),flush=True)
        if len(modes)==2 and all(records[role+'/'+m]['valid'] for m in modes):
            a,b=[records[role+'/'+m] for m in modes]
            for k in ('S','Ephi','ET'):assert a['metrics'][k]==b['metrics'][k]
            assert a['cycles']==b['cycles']
    reused=['E0','D_E','P_E','B_E','F_raw/network','F_raw/projected','F_bal/network','F_bal/projected'] if stage=='A' else ['B_E']
    with np.load(previous/'traces.npz',allow_pickle=False) as archive:
        for name in reused:
            records[name]=copy.deepcopy(old['records'][name]);records[name]['origin']='FIXED_HISTORICAL_RESULT_REUSED'
            traces[name]={k.split('__',1)[1]:archive[k].copy() for k in archive.files if k.startswith(name+'__')}
    decision=stage_a_decision(records,cfg) if stage=='A' else stage_b_decision(records,cfg)
    result=dict(status='COMPLETED_V31_STAGE_'+stage,records=records,decision=decision,
        reference_sha256=identity,recorded_utc=now(),scope='already exposed nominal; current own-field predictions fixed before evaluation')
    save_json(out/'results.json',result);save_json(out/'method-decision.json',decision)
    np.savez_compressed(out/'traces.npz',time=times,reference_current=reference.top_current,
        reference_power=reference.joule_power,reference_roi_fraction=events['roi_fraction'],
        **{r+'__'+k:v for r,tr in traces.items() for k,v in tr.items()})
    np.savez_compressed(out/'snapshots.npz',x=grid.x_centers,z=grid.z_centers,phase_times=times[peaks],**snapshots)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RUN);p.add_argument('--stage',choices=['A','B'],default='A')
    args=p.parse_args();evaluate(args.root,args.stage)
