"""Bounded saved-input conditional thermal study; never calls source simulate/run.

compute: the frozen 40+40 responses and qualified one-pass history replay.
score: saved arrays only, no thermal propagation or history replay.
"""
from pathlib import Path
import os
for _name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_name]='4'
import argparse,csv,hashlib,json,platform,sys,time
from dataclasses import asdict
from datetime import datetime,timezone
import numpy as np
import scipy
from scipy.interpolate import PPoly
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pinn_pcm_sci.vo2_author_reproduction import P,HKEYS
from conditional_thermal_tools import thermal_matrix,power_response,voltage_response
from circuit_screen_metrics import trap_weights
HERE=ROOT/'paper/paper_revision_20260928_conditional_thermal'
def save_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def load(path):
    with np.load(path,allow_pickle=False) as a:return {k:a[k] for k in a.files}
def linear(t,v):
    return PPoly(np.stack((np.diff(v,axis=0)/np.diff(t)[:,None],v[:-1])),t,extrapolate=False)
def locked(pred):
    pp=PPoly(pred['polynomial_coefficients'],pred['polynomial_breakpoints'],extrapolate=False)
    origin=float(pred['time_origin']);scale=float(pred['time_scale'])
    return lambda t:pp((t-origin)/scale),origin+scale*pp.x
def compute():
    from conditional_history_tools import replay_temperatures,verify_source_replay
    config=json.loads((HERE/'config.json').read_text(encoding='utf-8'))
    source_contract=json.loads((ROOT/config['source_contract']).read_text(encoding='utf-8'))
    if asdict(P)!=config['parameters_SI'] or asdict(P)!=source_contract['parameters_SI']:
        raise ValueError('Physical contract changed; do not silently change the fixed inputs')
    if (HERE/'execution.json').exists():raise RuntimeError('Compute already attempted: use saved arrays; no automatic rerun')
    started=time.perf_counter();counts=dict(main_system_responses=0,verification_responses=0,source_history_checks=0,prediction_history_replays=0)
    ledger=dict(task_id=config['task_id'],start_utc=datetime.now(timezone.utc).isoformat(),status='RUNNING',counts=counts,records=[],
        environment=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,platform=platform.platform(),threads=4,device='CPU'),
        boundaries=dict(new_closed_loop_source_steps=0,training_updates=0,GPU_used=False,experimental_csv_read=False,heldout_read=False,reference_fields_in_prediction=False),
        source_identity={})
    for name in ['scripts/run_conditional_thermal_closure.py','scripts/conditional_thermal_tools.py','scripts/conditional_history_tools.py','pinn_pcm_sci/vo2_author_reproduction.py']:
        ledger['source_identity'][name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    save_json(HERE/'execution.json',ledger)
    for item in config['records']:
        ident=item['id'];out=HERE/'arrays'/ident;out.mkdir(parents=True,exist_ok=True)
        rec=dict(id=ident,status='RUNNING',responses={});ledger['records'].append(rec)
        rstart=time.perf_counter()
        try:
            # Only these three source channels enter reference forcing. T/H are not
            # loaded until conditional temperatures are locked and qualified.
            with np.load(ROOT/item['source'],allow_pickle=False) as src:
                t=src['time'];v=src['voltage'];idevice=src['device_current']
            predictions={k:load(ROOT/path) for k,path in item['predictions'].items()}
            A=thermal_matrix(P.Sth,P.Cth,v.shape[1],item['eta'])
            q=linear(t,v*idevice);vref=linear(t,v)
            forcing={'Q_ref':(q,t),'V_ref':(vref,t),'P':locked(predictions['PCHIP']),'CS':locked(predictions['CS'])}
            output=dict(time=t)
            for method,(fn,breaks) in forcing.items():
                kw=dict(cth=P.Cth,T_base=P.Tbase,T_initial=config['initial_temperature_K'],breakpoints_s=breaks)
                f=power_response if method=='Q_ref' else voltage_response
                if method!='Q_ref':kw.update(V_in=np.array(item['source_voltage_V']),R_load=P.RL,C=P.C)
                tstart=time.perf_counter()
                counts['main_system_responses']+=1;main=f(t,A,fn,gauss_order=4,**kw)
                counts['verification_responses']+=1;check=f(t,A,fn,gauss_order=8,**kw)
                difference=main.temperature_K-check.temperature_K
                maximum=float(np.max(abs(difference)))
                output['T_'+method]=main.temperature_K;output['quadrature_difference_'+method]=difference
                rec['responses'][method]=dict(max_quad_difference_K=maximum,numerical_pass=maximum<=1e-6,
                    segments=main.evolution.segment_count,main_forcing_evaluations=main.evolution.forcing_evaluations,
                    verification_forcing_evaluations=check.evolution.forcing_evaluations,seconds=time.perf_counter()-tstart)
                del main,check
            np.savez_compressed(out/'thermal.npz',**output)
            rec['temperature_numerical_pass']=all(x['numerical_pass'] for x in rec['responses'].values())
            if rec['temperature_numerical_pass']:
                source=load(ROOT/item['source'])
                history_start=time.perf_counter();source_replay=replay_temperatures(source['temperature'])
                counts['source_history_checks']+=1
                verified=verify_source_replay(source,source_replay)
                save_json(out/'source-history-check.json',verified)
                rec['source_history_pass']=verified['passed'];rec['source_history_seconds']=time.perf_counter()-history_start
                if verified['passed']:
                    rec['history_seconds']={}
                    for method,predkey in [('P','PCHIP'),('CS','CS')]:
                        hstart=time.perf_counter();h=replay_temperatures(output['T_'+method]);counts['prediction_history_replays']+=1
                        h['I_R']=predictions[predkey]['voltage']/h['resistance']
                        h['r_close']=h['I_R']-predictions[predkey]['device_current']
                        np.savez_compressed(out/('history-'+method+'.npz'),**h)
                        rec['history_seconds'][method]=time.perf_counter()-hstart
                    rec['status']='COMPLETE'
                else:rec['status']='SOURCE_HISTORY_UNRESOLVED'
            else:rec['status']='TEMPERATURE_NUMERICAL_UNRESOLVED'
        except (FileNotFoundError,KeyError,ValueError,FloatingPointError) as exc:
            rec['status']='STOPPED_AFFECTED_RECORD';rec['error']=repr(exc)
        rec['seconds']=time.perf_counter()-rstart
        ledger['seconds']=time.perf_counter()-started
        save_json(HERE/'execution.json',ledger)
        print(json.dumps(dict(id=ident,status=rec['status'],seconds=rec['seconds'],counts=counts)),flush=True)
    ledger['status']='COMPLETE' if all(x['status']=='COMPLETE' for x in ledger['records']) else 'COMPLETE_WITH_UNRESOLVED_ANALYSES'
    ledger['seconds']=time.perf_counter()-started;ledger['end_utc']=datetime.now(timezone.utc).isoformat()
    assert all(counts[k]<=config['limits'][k] for k in counts)
    save_json(HERE/'execution.json',ledger)

def stats(t,candidate,reference,unit):
    d=np.asarray(candidate)-np.asarray(reference);w=trap_weights(t)
    return {f'rms_{unit}':float(np.sqrt(w@(d*d))),f'max_abs_{unit}':float(np.max(abs(d))),
        f'signed_mean_{unit}':float(w@d),f'end_difference_{unit}':float(d[-1]),
        f'candidate_end_{unit}':float(candidate[-1]),f'reference_end_{unit}':float(reference[-1]),
        f'candidate_min_{unit}':float(np.min(candidate)),f'candidate_max_{unit}':float(np.max(candidate)),
        f'reference_min_{unit}':float(np.min(reference)),f'reference_max_{unit}':float(np.max(reference))}
def csvwrite(path,rows):
    if not rows:return
    with path.open('w',encoding='utf-8',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)
def score():
    from conditional_history_tools import history_diagnostics
    config=json.loads((HERE/'config.json').read_text(encoding='utf-8'))
    execution=json.loads((HERE/'execution.json').read_text(encoding='utf-8'))
    rows=[];decrows=[];closure=[];histories=[];numerical=[];step=[];sourcechecks=[]
    for item in config['records']:
        ident=item['id'];out=HERE/'arrays'/ident
        if not (out/'thermal.npz').exists():continue
        source=load(ROOT/item['source']);a=load(out/'thermal.npz');t=a['time']
        pointwise=dict(time=t,V_ref_minus_Q_ref=a['T_V_ref']-a['T_Q_ref'],Q_ref_minus_saved=a['T_Q_ref']-source['temperature'])
        for m in ['P','CS']:
            pointwise[m+'_minus_V_ref']=a['T_'+m]-a['T_V_ref']
            pointwise[m+'_minus_saved']=a['T_'+m]-source['temperature']
        np.savez_compressed(out/'decomposition.npz',**pointwise)
        if (out/'source-history-check.json').exists():sourcechecks.append(dict(id=ident,**json.loads((out/'source-history-check.json').read_text())))
        for j in range(source['voltage'].shape[1]):
            base=dict(id=ident,case=item['case'],dt_s=item['dt_s'],device='AB'[j])
            for name,(lo,hi) in config['windows_s'].items():
                mask=(t>=lo-1e-18)&(t<=hi+1e-18);ts=t[mask]
                for m in ['Q_ref','V_ref','P','CS']:
                    rows.append(dict(**base,window=name,method=m,**stats(ts,a['T_'+m][mask,j],source['temperature'][mask,j],'K')))
                for m in ['P','CS']:
                    parts=[pointwise[m+'_minus_V_ref'][:,j],pointwise['V_ref_minus_Q_ref'][:,j],pointwise['Q_ref_minus_saved'][:,j]]
                    total=pointwise[m+'_minus_saved'][:,j]
                    decrows.append(dict(**base,window=name,method=m,
                        interpolation_rms_K=float(np.sqrt(trap_weights(ts)@(parts[0][mask]**2))),
                        voltage_power_representation_rms_K=float(np.sqrt(trap_weights(ts)@(parts[1][mask]**2))),
                        continuous_vs_saved_Euler_rms_K=float(np.sqrt(trap_weights(ts)@(parts[2][mask]**2))),
                        total_rms_K=float(np.sqrt(trap_weights(ts)@(total[mask]**2))),
                        pointwise_closure_max_K=float(np.max(abs(total[mask]-sum(x[mask] for x in parts))))))
            for m in ['Q_ref','V_ref','P','CS']:
                qmax=float(np.max(abs(a['quadrature_difference_'+m][:,j])))
                effect=float(np.sqrt(trap_weights(t)@((a['T_'+m][:,j]-source['temperature'][:,j])**2)))
                numerical.append(dict(**base,method=m,quadrature_max_K=qmax,effect_rms_K=effect,
                    numerical_pass=qmax<=1e-6,quadrature_to_effect_ratio=qmax/effect if effect else None))
        for m,pk in [('P','PCHIP'),('CS','CS')]:
            if not (out/('history-'+m+'.npz')).exists():continue
            h=load(out/('history-'+m+'.npz'));pred=load(ROOT/item['predictions'][pk])
            _,diagnostic=history_diagnostics(t,a['T_'+m],pred['voltage'],pred['device_current'],h,source,config['windows_s'])
            histories.append(dict(id=ident,method=m,diagnostics=diagnostic))
            for j in range(source['voltage'].shape[1]):
                for name,(lo,hi) in config['windows_s'].items():
                    mask=(t>=lo-1e-18)&(t<=hi+1e-18);ts=t[mask]
                    row=dict(id=ident,case=item['case'],dt_s=item['dt_s'],device='AB'[j],window=name,method=m)
                    for label,cand,ref,unit in [('R',h['resistance'],source['resistance'],'ohm'),('g',h['g'],source['g'],'fraction'),
                        ('I_R',h['I_R'],source['device_current'],'A'),('I_KCL',pred['device_current'],source['device_current'],'A'),
                        ('closure',h['r_close'],np.zeros_like(h['r_close']),'A')]:
                        row.update({label+'_'+k:v for k,v in stats(ts,cand[mask,j],ref[mask,j],unit).items()})
                    row['negative_I_KCL_samples']=int(np.sum(pred['device_current'][mask,j]<0))
                    row['negative_power_samples']=int(np.sum((pred['voltage']*pred['device_current'])[mask,j]<0))
                    row['I_KCL_min_A']=float(np.min(pred['device_current'][mask,j]))
                    row['power_min_W']=float(np.min((pred['voltage']*pred['device_current'])[mask,j]))
                    closure.append(row)
    for coarse in [x for x in config['records'] if x['dt_s']==1e-9]:
        fine=next(x for x in config['records'] if x['case']==coarse['case'] and x['dt_s']==.5e-9)
        s1=load(ROOT/coarse['source']);s2=load(ROOT/fine['source']);t=s1['time']
        p1=HERE/'arrays'/coarse['id']/'thermal.npz';p2=HERE/'arrays'/fine['id']/'thermal.npz'
        if not (p1.exists() and p2.exists()):continue
        c1=load(p1);c2=load(p2)
        for j in range(s1['voltage'].shape[1]):
            for method in ['saved','Q_ref','V_ref','P','CS']:
                v1=s1['temperature'] if method=='saved' else c1['T_'+method]
                v2=s2['temperature'] if method=='saved' else c2['T_'+method]
                step.append(dict(case=coarse['case'],device='AB'[j],method=method,**stats(t,v1[:,j],v2[::2,j],'K')))
    dest=HERE/'results';dest.mkdir(exist_ok=True)
    for name,data in [('temperature',rows),('decomposition',decrows),('closure',closure),('numerical',numerical),('source-step-sensitivity',step)]:csvwrite(dest/(name+'.csv'),data)
    save_json(dest/'history-diagnostics.json',histories);save_json(dest/'source-history-checks.json',sourcechecks)
    save_json(dest/'summary.json',dict(temperature_rows=len(rows),closure_rows=len(closure),decomposition_rows=len(decrows),
        numerical_rows=len(numerical),source_history_pass=sum(x['passed'] for x in sourcechecks),history_records=len(histories),
        max_quadrature_K=max(x['quadrature_max_K'] for x in numerical),
        max_decomposition_closure_K=max(x['pointwise_closure_max_K'] for x in decrows),
        mode='Saved array scoring only; no thermal or history recomputation',tau_task=None,claim_status='VERIFIED'))
    print(json.dumps(json.loads((dest/'summary.json').read_text())))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['compute','score']);args=parser.parse_args()
    compute() if args.mode=='compute' else score()
