"""Post-shutdown fixed-reference V32 scores and report-only history diagnostics."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import numpy as np
import torch
from .phk_v23_lf11 import ROOT, save_json, now, digest
from .phk_v23_lf11_protocol import validate_case, case_physics, inference_times
from .phk_v23_lf11_protocol_reference import RUN
from .phk_v22r_training import load_case_physics
from .phk_v22r_evaluator import _physical_contract, _event_summary
from .phk_v21_benchmark import read_phk_v21_result
from .phk_v23_lf11_evaluation import metrics, field_rms, time_rms
from .phk_v23_lf11_followup_evaluate import add_power_metrics
from .phk_v23_lf11_fullgrid_evaluate import pair
from .phk_v23_lf11_electric_layer import ElectricalLayer
from .phk_v23_lf11_training_coupling import read


def history_diagnostics(fields, reference, traces, physics, cfg, roi):
    """Fixed reporting windows; none of these indicators changes a formal gate."""
    spec=cfg['case_spec'];t=reference.time
    index=int(np.argmin(abs(t-spec['pulse_starts'][1])))
    if abs(t[index]-spec['pulse_starts'][1])>1e-12:raise ValueError('missing prepulse time')
    before={}
    for field,scale in [('temperature',.45),('phase',1.)]:
        pred,ref=fields[field][index,roi],getattr(reference,field)[index,roi]
        before[field]=dict(predicted_ROI_mean=float(pred.mean()),reference_ROI_mean=float(ref.mean()),
            signed_mean_error=float(np.mean(pred-ref)),ROI_RMS_error=float(np.sqrt(np.mean((pred-ref)**2))),
            normalized_ROI_RMS_error=float(np.sqrt(np.mean((pred-ref)**2))/scale))
    pulses=[]
    for cycle,(lo,hi) in enumerate(spec['windows'][::2],1):
        mask=(t>=lo)&(t<=hi);when=t[mask]
        error=traces['joule_power'][mask]-reference.joule_power[mask]
        ref=reference.joule_power[mask];energy=float(np.trapezoid(ref,when))
        scale=time_rms(ref,when);signed=float(np.trapezoid(error,when))
        absolute=float(np.trapezoid(abs(error),when))
        pulses.append(dict(cycle=cycle,window=[lo,hi],reference_energy=energy,
            power_NRMSE=time_rms(error,when)/scale if scale>1e-12 else None,
            signed_energy_error=signed,absolute_signed_energy_error=abs(signed),
            integrated_absolute_power_error=absolute,
            relative_signed_energy_error=signed/energy if abs(energy)>1e-12 else None,
            relative_absolute_energy_error=abs(signed)/abs(energy) if abs(energy)>1e-12 else None,
            relative_integrated_absolute_power_error=absolute/abs(energy) if abs(energy)>1e-12 else None))
    second=(t>=spec['recovery_cycles'][1][0])&(t<=spec['recovery_cycles'][1][1])
    when=t[second];power=reference.joule_power[second];current=reference.top_current[second]
    def normalized(error,ref):
        scale=time_rms(ref,when)
        return time_rms(error,when)/scale if scale>1e-12 else None
    second_metrics=dict(Ephi=field_rms(fields['phase'][second],reference.phase[second],when,roi),
        ET=field_rms(fields['temperature'][second],reference.temperature[second],when,roi)/.45,
        current_NRMSE=normalized(traces['top_current'][second]-current,current),
        power_NRMSE=normalized(traces['joule_power'][second]-power,power))
    tail=t>spec['tail'][0]
    return dict(status='PREDECLARED_REPORT_ONLY',prepulse_time=float(t[index]),prepulse=before,
        per_pulse=pulses,second_cycle=second_metrics,
        recovery_windows=spec['recovery_cycles'],tail_window=spec['tail'],
        tail_max_absolute_drive=float(torch.max(abs(physics.waveform(torch.tensor(t[tail],dtype=torch.float64))))),
        tail_phase_ROI_RMS=field_rms(fields['phase'][tail],reference.phase[tail],t[tail],roi),
        tail_does_not_extend_recovery=True)


def complete_endpoint(folder,cfg):
    terminal=read(folder/'terminal.json');lb=terminal['lbfgs']
    stop=lb['termination']
    valid_stop=(stop in ('GRADIENT_CONVERGED','NO_ACCEPTED_PROGRESS') or
        (lb['evaluations']==cfg['lbfgs_evaluations'] and stop in
         ('EVALUATION_BUDGET_EXHAUSTED','EVALUATION_BUDGET_EXHAUSTED_TRIAL_ROLLED_BACK')))
    complete=(terminal['status']=='VALID_FIXED_ENDPOINT' and terminal['adam_updates']==cfg['branch_updates'] and valid_stop)
    return complete,terminal


def execution_summary(root,cfg):
    records={};total=dict(adam=0,complete_evaluations=0,E_forward=0,E_adjoint=0,
                         calibration_forward=0,calibration_adjoint=0,inference_forward=0)
    for seed in cfg['confirmation']['seeds']:
        directory=root/f'seed-{seed}';fit=read(directory/'common-fit/fit-summary.json')
        cal=read(directory/'calibration.json');items={}
        total['adam']+=fit['adam_updates'];total['complete_evaluations']+=fit['complete_evaluations']
        for key in ('forward','adjoint'):total['calibration_'+key]+=cal['statistics']['electrical'][key+'_solves']
        for role in ('E','F_raw'):
            complete,term=complete_endpoint(directory/role,cfg);items[role]=dict(complete=complete,terminal=term)
            total['adam']+=term['adam_updates'];total['complete_evaluations']+=term['lbfgs']['evaluations']
            if role=='E':
                for key in ('forward','adjoint'):total['E_'+key]+=term['statistics']['electrical'][key+'_solves']
            counts=read(directory/role/'projected/prediction.json')['electrical_counts']
            total['inference_forward']+=counts['forward_solves']
        records[str(seed)]=dict(parent=fit,calibration=cal,branches=items)
    total['inference_forward']+=read(root/'B_E/projected/prediction.json')['electrical_counts']['forward_solves']
    initial_identity={}
    for seed in cfg['confirmation']['seeds']:
        fresh=torch.load(root/f'seed-{seed}/common-fit/initial.pt',map_location='cpu',weights_only=False)
        old=torch.load(ROOT/f'paper/paper_v31/evidence/confirmation/seed-{seed}/common-fit/initial.pt',map_location='cpu',weights_only=False)
        a,b=fresh['model_state_dict'],old['model_state_dict']
        initial_identity[str(seed)]=dict(exact_same_zero_update_tensors=(a.keys()==b.keys() and all(torch.equal(a[k],b[k]) for k in a)),
            old_trained_weights_loaded=False,verification_after_training=True)
    caps=dict(adam=10800,complete_evaluations=2400,E_forward=54000,E_adjoint=54000,
              calibration_forward=1000,calibration_adjoint=1000,inference_forward=1390)
    if any(total[k]>caps[k] for k in total):raise ValueError(('actual execution exceeds cap',total,caps))
    result=dict(totals=total,caps=caps,records=records,cross_case_random_initial_identity=initial_identity)
    save_json(root/'execution-summary.json',result)
    return result


def evaluate(root=RUN):
    root=Path(root);proof=read(root/'compute-closure.json')
    if not all(proof.get(k) for k in ('training_complete','recovery_verified','shutdown_requested',
                                     'instance_shutdown_confirmed','compute_stopped_before_reference_read')):
        raise ValueError('current training, recovery and actual shutdown must be confirmed')
    cfg=read(root/'frozen-config.json');validate_case(cfg['case_spec'])
    cfg['evaluation']={'readout':'COMMON_FV_FACE_FLUX_EDGE_DISSIPATION_V1'}
    physics=case_physics(load_case_physics()[0],cfg['case_spec']);torch.set_num_threads(cfg['cpu_threads'])
    path=root/'local-reference/reference/result.npz'
    if read(path.parent/'terminal.json')['status']!='VALID_FIXED_REFERENCE_CARRIER':raise ValueError('reference not valid')
    reference=read_phk_v21_result(path,physical=_physical_contract())
    time,grid=reference.time,reference.grid
    np.testing.assert_array_equal(time,inference_times(cfg['case_spec']))
    out=root/'evaluation';out.mkdir(exist_ok=False)
    ev=_physical_contract().payload['qualification_event'];reg=ev['roi']
    roi=(abs(grid.cell_x)<=reg['abs_x_max'])&(grid.cell_z>=reg['z_min'])&(grid.cell_z<=reg['z_max'])
    ref_events=_event_summary(reference.phase,time=time,roi=roi,period=physics.period,
        phase_threshold=ev['phase_threshold'],event_fraction=ev['event_threshold_roi_fraction'])
    peaks=[c['peak_time_index'] for c in ref_events['cycles']]
    refheat=np.empty_like(reference.temperature);layer=ElectricalLayer(grid,physics.heater_width_fraction)
    with torch.no_grad():
        for i,t in enumerate(time):
            sigma=physics.conductivity(torch.tensor(reference.temperature[i]),torch.tensor(reference.phase[i]))
            refheat[i]=layer.deposition(torch.tensor(reference.potential[i]),sigma,
                float(physics.waveform(torch.tensor(t,dtype=torch.float64))))['density'].numpy()
    qscale=field_rms(refheat,np.zeros_like(refheat),time)
    records={};traces={};snapshots={k:getattr(reference,k)[peaks] for k in ('potential','temperature','phase')}
    snapshot_arrays={'reference__'+k:v for k,v in snapshots.items()}
    snapshot_arrays['reference__joule_density']=refheat[peaks].copy()
    def score(name,folder,complete=True):
        with np.load(folder/'prediction.npz',allow_pickle=False) as saved:
            for key,axis in [('x',grid.x_centers),('z',grid.z_centers),('time',time)]:np.testing.assert_array_equal(saved[key],axis)
            fields={k:saved[k] for k in ('potential','temperature','phase')};heat=saved['joule_density']
        record,trace=metrics(fields,reference,physics,cfg)
        if record['valid']:
            add_power_metrics(record,trace,time,reference.top_current,reference.joule_power)
            record['metrics']['local_joule_NRMSE']=field_rms(heat,refheat,time)/qscale if qscale>1e-12 else None
            record['history_diagnostics']=history_diagnostics(fields,reference,trace,physics,cfg,roi)
        with np.load(folder/'own-readout.npz',allow_pickle=False) as own:
            for key in ('top_current','bottom_current','joule_power'):
                np.testing.assert_allclose(own[key],trace[key],rtol=1e-10,atol=1e-11)
        record.update(training_budget_complete=complete,readout_identity=read(folder/'prediction.json'),origin='NEW_PROTOCOL_FIXED_ENDPOINT')
        records[name]=record;traces[name]=trace
        for key,v in fields.items():snapshot_arrays[name+'__'+key]=v[peaks].copy()
        snapshot_arrays[name+'__joule_density']=heat[peaks].copy()
        print(json.dumps(dict(evaluated=name,valid=record['valid'],metrics=record['metrics'])),flush=True)
        return fields
    score('B_E',root/'B_E/projected')
    decisions={}
    for seed in cfg['confirmation']['seeds']:
        directory=root/f'seed-{seed}';scfg=read(directory/'frozen-config.json')
        if scfg['case_spec']!=cfg['case_spec']:raise ValueError('model case conflict')
        complete,_=complete_endpoint(directory/'E',scfg)
        score(f'{seed}/E/projected',directory/'E/projected',complete)
        complete,_=complete_endpoint(directory/'F_raw',scfg)
        network=score(f'{seed}/F_raw/network',directory/'F_raw/network',complete)
        projected=score(f'{seed}/F_raw/projected',directory/'F_raw/projected',complete)
        for key in ('temperature','phase'):np.testing.assert_array_equal(network[key],projected[key])
        nr,pr=records[f'{seed}/F_raw/network'],records[f'{seed}/F_raw/projected']
        assert nr['cycles']==pr['cycles']
        for key in ('S','Ephi','ET'):assert nr['metrics'][key]==pr['metrics'][key]
        del network,projected
        e,f=records[f'{seed}/E/projected'],records[f'{seed}/F_raw/projected']
        decisions[str(seed)]=dict(E_vs_soft=pair(e,f,cfg),soft_vs_E=pair(f,e,cfg),
            E_vs_B_E=pair(e,records['B_E'],cfg),soft_vs_B_E=pair(f,records['B_E'],cfg))
    second_reference_event=(ref_events['cycles'][1]['event_time'] is not None and
        ref_events['cycles'][1]['pre_roi_fraction']<ev['event_threshold_roi_fraction'])
    for record in records.values():
        for c,rc in zip(record['cycles'],ref_events['cycles'],strict=True):
            c['reference_event_present']=rc['event_time'] is not None
            c['false_positive_event']=rc['event_time'] is None and c['event_time'] is not None
    # The baseline and neural checkpoints remain fixed. These are descriptions
    # of the authorized change, not any input to training or endpoint selection.
    cross_case={}
    for seed in cfg['confirmation']['seeds']:
        previous=read(ROOT/f'paper/paper_v31/evidence/confirmation/seed-{seed}/evaluation/results.json')
        cross_case[str(seed)]={}
        for role in ('E/projected','F_raw/projected','B_E'):
            before=previous['records'][role]['metrics']
            after=records['B_E' if role=='B_E' else f'{seed}/{role}']['metrics']
            cross_case[str(seed)][role]={k:dict(original=before[k],new=after[k],
                absolute_change=after[k]-before[k],ratio_new_to_original=after[k]/before[k] if before[k]>1e-12 else None)
                for k in ('S','Ephi','ET','EV','EI','bottom_current_NRMSE','power_trace_NRMSE','energy_error')}
    oldpath=ROOT/'outputs/runs/20260828T-phk-v21-s1-q-06-nominal-extra-fine/result-intent-06.npz'
    physical_history={}
    with np.load(oldpath,allow_pickle=False) as old:
        old_i=int(np.argmin(abs(old['time']-1.25)));new_i=int(np.argmin(abs(time-1.01)))
        for field in ('temperature','phase'):
            old_state=old[field][old_i,roi];new_state=getattr(reference,field)[new_i,roi]
            physical_history[field]=dict(original_prepulse_time=1.25,new_prepulse_time=1.01,
                original_ROI_mean=float(old_state.mean()),new_ROI_mean=float(new_state.mean()),
                original_ROI_max=float(old_state.max()),new_ROI_max=float(new_state.max()),
                signed_mean_change=float(new_state.mean()-old_state.mean()))
    result=dict(status='COMPLETED_V32_NEW_PROTOCOL',case_spec=cfg['case_spec'],records=records,
        decisions=decisions,reference_events=ref_events,
        cross_case_error_changes=cross_case,reference_prepulse_history=physical_history,
        second_independent_reference_event=second_reference_event,
        no_event_case_replaced=False,reference_sha256=digest(path),recorded_utc=now(),
        evidence_scope='Two seeds on one new protocol, each fit to that case support; no zero-shot or formal OOD claim')
    save_json(out/'results.json',result)
    np.savez_compressed(out/'traces.npz',time=time,reference_current=reference.top_current,
        reference_power=reference.joule_power,reference_roi_fraction=ref_events['roi_fraction'],
        drive=physics.waveform(torch.tensor(time,dtype=torch.float64)).numpy(),
        **{r+'__'+k:v for r,tr in traces.items() for k,v in tr.items()})
    np.savez_compressed(out/'snapshots.npz',x=grid.x_centers,z=grid.z_centers,phase_times=time[peaks],**snapshot_arrays)
    execution_summary(root,cfg)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RUN)
    evaluate(p.parse_args().root)
