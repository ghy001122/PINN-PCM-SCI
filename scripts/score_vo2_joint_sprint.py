"""One locked-endpoint comparison; training code never reads these sources."""
from pathlib import Path
import argparse,csv,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from pinn_pcm_sci.vo2_joint_reconstruction import RUN,P,read,save,trap
from pinn_pcm_sci.vo2_joint_rc import rc_forward
from circuit_screen_metrics import summarize_peaks
from conditional_history_tools import reversal_events
def load(p):
    with np.load(p,allow_pickle=False) as f:return {k:f[k] for k in f.files}
def rms(x,w):return float(np.sqrt(w@np.mean(x*x,axis=1)))
def evaluate(label,T,R,v,history,source,inputs,cfg):
    time=source['time'];w=trap(time);h=cfg['dt_s'];Vin=np.array(cfg['Vin_V']);K=P.Sth*np.array([[1.,-.12],[-.12,1.]])
    I=v/R;heat=P.Cth*np.diff(T,axis=0)/h+(T[:-1]-P.Tbase)@K.T-v[:-1]**2/R[:-1]
    rc=P.C*np.diff(v,axis=0)/h-(Vin-v[:-1])/P.RL+v[:-1]/R[:-1]
    obs=np.stack([np.interp(inputs['observation_time'],time,v[:,j]) for j in range(2)],axis=1)
    obs_error=obs-inputs['observation_voltage'];ow=inputs['observation_weights']
    row=dict(method=label,joint_current_RMS_A=rms(I-source['device_current'],w),joint_current_RMS_uA=1e6*rms(I-source['device_current'],w),
        temperature_RMS_K=rms(T-source['temperature'],w),observation_RMS_V=rms(obs_error,ow),
        thermal_RMS_W=float(np.sqrt(np.mean(heat*heat))),RC_RMS_A=float(np.sqrt(np.mean(rc*rc))),
        full_voltage_RMS_V=rms(v-source['voltage'],w),negative_power_samples=int(np.sum(v*I<0)),
        temperature_min_K=float(T.min()),temperature_max_K=float(T.max()),
        outside_constitutive_range_samples=int(np.sum((T<305)|(T>370))))
    devices=[];events=reversal_events(time,history);sourceevents=reversal_events(time,source)
    for j in range(2):
        devices.append(dict(device='AB'[j],current_RMS_A=float(np.sqrt(w@((I[:,j]-source['device_current'][:,j])**2))),
            temperature_RMS_K=float(np.sqrt(w@((T[:,j]-source['temperature'][:,j])**2))),
            voltage_RMS_V=float(np.sqrt(w@((v[:,j]-source['voltage'][:,j])**2))),
            thermal_RMS_W=float(np.sqrt(np.mean(heat[:,j]**2))),observation_RMS_V=float(np.sqrt(ow@(obs_error[:,j]**2))),
            candidate_reversals=events[j],source_reversals=sourceevents[j],
            peaks=summarize_peaks(time,source['device_current'][:,j],I[:,j],.25e-6)))
    return row,devices,dict(time=time,T=T,R=R,v=v,device_current=I,rT=heat,rRC=rc,observation_error=obs_error)
def score(seed):
    cfg=read(RUN/'config.json');locked=read(RUN/f'seed-{seed}-locked.json')
    if (RUN/f'seed-{seed}-results.json').exists():raise RuntimeError('Endpoints already scored; reuse saved results')
    source=load(ROOT/cfg['original_source_for_scoring_only']);inputs=load(RUN/'input.npz')
    results=[];details={};out=RUN/f'seed-{seed}-readout';out.mkdir(exist_ok=True)
    valid=locked['all_valid'];roles=['N_dyn','F_dyn','S_dyn'] if seed==29 else ['N_dyn','F_dyn']
    for role in roles:
        entry=RUN/f'seed-{seed}'/role
        term=read(entry/'termination.json')
        if term['status']!='VALID_COMPLETE':
            details[role]=dict(status=term['status'],not_used_in_increment=True);continue
        a=load(entry/'endpoint.npz')
        # Common RC replay already saved by the endpoint exporter; T is not
        # altered. Evaluate its power, not the original F network power.
        row,devices,arr=evaluate(role,a['T'],a['R'],a['common_voltage'],a,source,inputs,cfg)
        results.append(row);details[role]=dict(status=term['status'],devices=devices,optimizer=term)
        np.savez_compressed(out/(role+'.npz'),**arr)
        row_native,devices_native,arr_native=evaluate(role+'_native',a['T'],a['R'],a['v'],a,source,inputs,cfg)
        details[role]['native_metrics']=row_native;details[role]['native_devices']=devices_native
        if role=='F_dyn':np.savez_compressed(out/'F_dyn_native.npz',**arr_native)
    # Source is the previously saved known-parameter forward trajectory; no
    # new forward ODE is generated. It is an information-rich reference row.
    vsource=rc_forward(source['resistance'],cfg['dt_s'],P.C,P.RL,np.array(cfg['Vin_V']),0.)
    row,devices,arr=evaluate('known_parameter_forward_common_RC',source['temperature'],source['resistance'],vsource,source,source,inputs,cfg)
    results.append(row);details[row['method']]=dict(devices=devices,identity='Known-parameter saved forward reference; not a learned candidate and not an independent test')
    raw,_,_=evaluate('known_parameter_forward_native',source['temperature'],source['resistance'],source['voltage'],source,source,inputs,cfg)
    details[row['method']]['native_metrics']=raw
    # Keep previously computed conditional P/CS controls by reusing their
    # arrays; do not generate new heat or history trajectories.
    old=ROOT/'paper/paper_revision_20260928_conditional_thermal/arrays/pair_excitation-0p5ns'
    temps=load(old/'thermal.npz')
    for method,pk in [('P','PCHIP'),('CS','CS')]:
        pred=load(ROOT/f'paper/paper_revision_20260928_circuit_comparison/scoring-subset/predictions/{pk}/pair_excitation-0p5ns.npz')
        history=load(old/f'history-{method}.npz')
        # These controls retain original KCL currents, which are not v/R.
        control=dict(method=pk+'_original_conditional',joint_current_RMS_A=rms(pred['device_current']-source['device_current'],trap(source['time'])),
            temperature_RMS_K=rms(temps['T_'+method]-source['temperature'],trap(source['time'])),
            closure_RMS_A=rms(history['r_close'],trap(source['time'])),
            note='Original KCL current and old conditionally computed T; not a joint constitutive solution; no new replay')
        details[control['method']]=control
    gates={};trigger=False
    lookup={x['method']:x for x in results}
    if valid:
        controls=['F_dyn','S_dyn'] if seed==29 else ['F_dyn']
        if seed==43:
            oldresults=read(RUN/'seed-29-results.json')['joint_rows'];lookup['S_dyn']=next(x for x in oldresults if x['method']=='S_dyn');controls.append('S_dyn')
        n=lookup['N_dyn']
        for control in controls:
            c=lookup[control];gain=c['joint_current_RMS_A']-n['joint_current_RMS_A']
            current=gain>=max(.1*c['joint_current_RMS_A'],1e-5)
            noninferior={k:n[k]<=max(1.05*c[k],c[k]+floor) for k,floor in cfg['increment']['absolute_floors'].items()}
            gates[control]=dict(current_gain_A=gain,current_relative_gain=gain/c['joint_current_RMS_A'] if c['joint_current_RMS_A'] else None,
                current_pass=current,noninferiority=noninferior,passed=current and all(noninferior.values()))
        trigger=all(x['passed'] for x in gates.values())
    save(RUN/f'seed-{seed}-gate.json',dict(all_valid=valid,gates=gates,trigger_seed43=bool(trigger and seed==29),
        joint_increment=bool(trigger),interpretation='Prospective development comparison; no formal OOD or material validation'))
    report=dict(task_id=cfg['task_id'],seed=seed,all_valid=valid,joint_rows=results,details=details,gates=gates,joint_increment=trigger,
        source_access='After all current-seed endpoints locked; no source fields entered training',
        original_time_sensitivity='Reuse preceding 0.5/1 ns source sensitivity; not independent repetitions',
        source_common_RC_replay_calls=1,learned_endpoints_common_RC_already_saved=True)
    save(RUN/f'seed-{seed}-results.json',report)
    with (RUN/f'seed-{seed}-comparison.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(results[0]));writer.writeheader();writer.writerows(results)
    print(json.dumps(dict(rows=results,gates=gates,trigger_seed43=trigger and seed==29)),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=29);score(p.parse_args().seed)
