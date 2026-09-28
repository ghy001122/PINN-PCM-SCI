"""Fixed CS comparison and saved-array energy analysis; no model integration.

Prediction is separate from packaging/scoring. The transferable scorer resolves
all inputs under its supplied root and has no fallback to the research checkout.
"""
from __future__ import annotations
import argparse
import json
import platform
import shutil
import sys
import time
from pathlib import Path
import numpy as np
import scipy
from scipy.interpolate import CubicSpline

sys.path.insert(0, str(Path(__file__).resolve().parent))
import circuit_screen_metrics as legacy
from circuit_energy_tools import prediction_energy, reference_energy, euler_energy_check

ROOT = Path(__file__).resolve().parents[1]
SHARED = ('time', 'observation_time', 'observation_voltage')
SOURCE_FIELDS = ('time', 'voltage', 'device_current', 'load_current', 'capacitor_current')

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def arrays(path):
    with np.load(path, allow_pickle=False) as x:
        return {k: x[k] for k in x.files}

def predict_cs(obs_time, obs_voltage, source_voltage, resistance, capacitance, query_time,
               time_scale=1e-6):
    """Finite voltage observations and known circuit parameters only."""
    obs_time = np.asarray(obs_time, dtype=np.float64)
    obs_voltage = np.asarray(obs_voltage, dtype=np.float64)
    query_time = np.asarray(query_time, dtype=np.float64)
    if obs_voltage.ndim == 1:
        obs_voltage = obs_voltage[:, None]
    if resistance <= 0 or capacitance <= 0 or time_scale <= 0:
        raise ValueError('Positive circuit parameters and time scale required')
    if np.any(query_time < obs_time[0]) or np.any(query_time > obs_time[-1]):
        raise ValueError('No extrapolation')
    cs = CubicSpline((obs_time-obs_time[0])/time_scale, obs_voltage, axis=0,
                     bc_type='not-a-knot', extrapolate=False)
    tau = (query_time-obs_time[0])/time_scale
    v = cs(tau)
    dv = cs.derivative(1)(tau)/time_scale
    il = (np.asarray(source_voltage)-v)/resistance
    ic = capacitance*dv
    result = dict(time=query_time, observation_time=obs_time, observation_voltage=obs_voltage,
                  voltage=v, voltage_derivative=dv, load_current=il,
                  capacitor_current=ic, device_current=il-ic,
                  polynomial_coefficients=cs.c, polynomial_breakpoints=cs.x,
                  time_origin=np.asarray(obs_time[0]), time_scale=np.asarray(time_scale))
    if not all(np.isfinite(x).all() for x in result.values()):
        raise FloatingPointError('Nonfinite CS prediction; no clipping or rescue')
    return result

def make_predictions(config, root):
    out = legacy.resolve(root, config['output'])
    out.mkdir(parents=True, exist_ok=True)
    if (out/'predictions-locked.json').exists():
        raise FileExistsError('CS already locked; reuse score/figures')
    started = legacy.now(); tic = time.perf_counter(); records = []
    for item in config['simulation_inputs']:
        path = out/'predictions-CS'/f"{item['id']}.npz"
        if path.exists():
            raise FileExistsError('Existing fixed prediction cannot be overwritten')
        # Only three permitted fields of the old prediction are loaded here.
        with np.load(legacy.resolve(root, item['pchip']), allow_pickle=False) as old:
            obs_t, obs_v, t = (old[k].copy() for k in ('observation_time','observation_voltage','time'))
        if len(obs_t) != 197 or not np.isclose(obs_t[-1]-obs_t[-2], 32e-9, rtol=0, atol=1e-19):
            raise ValueError('Frozen observation identity differs')
        pred = predict_cs(obs_t, obs_v, item['source_voltage_V'], item['RL_ohm'], item['C_F'], t, config['time_scale_s'])
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, **pred)
        meta = dict(item, prediction_sha256=legacy.sha(path), method='CS',
                    states=len(t), devices=obs_v.shape[1], observations=len(obs_t),
                    frozen_at=legacy.now(), score_fields_read_before_lock=False)
        legacy.save_json(path.with_suffix('.json'), meta); records.append(meta)
    legacy.save_json(out/'predictions-locked.json',dict(task_id=config['task_id'], records=records,
        started=started, locked_at=legacy.now(), elapsed_seconds=time.perf_counter()-tic,
        source_identity={n:legacy.sha(Path(__file__).parent/n) for n in
                         ['run_cubic_energy_comparison.py','circuit_screen_metrics.py','circuit_energy_tools.py']},
        source_score_arrays_opened=False, new_system_steps=0, new_training_steps=0,
        environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,device='local CPU FP64')))

def package_subset(config, root):
    out=legacy.resolve(root,config['output']); bundle=legacy.resolve(root,config['subset'])
    if (bundle/'config.json').exists():
        raise FileExistsError('Subset already prepared; do not duplicate or overwrite')
    lock=read_json(out/'predictions-locked.json')
    if len(lock['records'])!=10:
        raise ValueError('All ten CS predictions must be locked before source scoring access')
    tic=time.perf_counter(); records=[]
    for item in lock['records']:
        original=legacy.resolve(root,item['path'])
        csfile=out/'predictions-CS'/f"{item['id']}.npz"
        if legacy.sha(csfile)!=item['prediction_sha256']:
            raise ValueError('New prediction changed after locking')
        cp=arrays(csfile); pp=arrays(legacy.resolve(root,item['pchip']))
        with np.load(original,allow_pickle=False) as source:
            raw={k:source[k].copy() for k in SOURCE_FIELDS}
        for field in SHARED:
            if not np.array_equal(cp[field],pp[field]):
                raise ValueError('Methods do not have identical frozen observation/query inputs')
        if not np.array_equal(raw['time'],cp['time']):
            raise ValueError('Prediction and source native time mismatch')
        # Shared time/observations and reference arrays occur once per system,
        # not once per method or device role, in the transferable representation.
        raw.update({k:cp[k] for k in SHARED if k!='time'})
        source_path=bundle/'inputs'/f"{item['id']}.npz"
        source_path.parent.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(source_path,**raw)
        prediction_paths={}
        for method,pred in [('PCHIP',pp),('CS',cp)]:
            target=bundle/'predictions'/method/f"{item['id']}.npz"
            target.parent.mkdir(parents=True,exist_ok=True)
            np.savez_compressed(target,**{k:v for k,v in pred.items() if k not in SHARED})
            prediction_paths[method]=target.relative_to(bundle).as_posix()
        records.append(dict(id=item['id'],case=item['case'],dt_s=item['dt_s'],
            source=source_path.relative_to(bundle).as_posix(),predictions=prediction_paths,
            source_voltage_V=item['source_voltage_V'],C_F=item['C_F'],RL_ohm=item['RL_ohm'],
            provenance=dict(original_path=item['path'],original_size_bytes=original.stat().st_size,
                original_mtime_ns=original.stat().st_mtime_ns,original_prediction_path=item['pchip'],
                locked_CS_sha256=item['prediction_sha256']),
            units=dict(time='s',voltage='V',currents='A',energy='J'),
            shape=list(raw['voltage'].shape),dtype=str(raw['voltage'].dtype)))
    for name in ['run_cubic_energy_comparison.py','circuit_screen_metrics.py','circuit_energy_tools.py']:
        (bundle/'scripts').mkdir(exist_ok=True)
        shutil.copyfile(Path(__file__).parent/name,bundle/'scripts'/name)
    for name in ['test_cubic_energy_comparison.py','test_circuit_energy_tools.py']:
        (bundle/'tests').mkdir(exist_ok=True)
        shutil.copyfile(root/'tests'/name,bundle/'tests'/name)
    shutil.copyfile(legacy.resolve(root,config['original_results']),bundle/'expected-pchip-results.json')
    shutil.copyfile(out/'predictions-locked.json',bundle/'cs-lock-provenance.json')
    if (root/'LICENSE').exists():shutil.copyfile(root/'LICENSE',bundle/'LICENSE')
    portable=dict(task_id=config['task_id'], baseline=config['baseline'],records=records,
                  engineering_safety_factor=config['engineering_safety_factor'],
                  peak_match_max_gap_s=config['peak_match_max_gap_s'],
                  output='results',scipy_version=config['scipy_version'],tau_task=None,
                  shared_prediction_fields=list(SHARED),source_access_after_CS_lock=legacy.now(),
                  no_absolute_path_fallback=True,new_system_steps=0,new_training_steps=0,
                  provenance_paths_are_not_runtime_inputs=True)
    legacy.save_json(bundle/'config.json',portable)
    manifest=[]
    for path in sorted(bundle.rglob('*')):
        if path.is_file():manifest.append(dict(path=path.relative_to(bundle).as_posix(),bytes=path.stat().st_size,sha256=legacy.sha(path)))
    legacy.save_json(bundle/'transfer-manifest.json',dict(files=manifest,elapsed_seconds=time.perf_counter()-tic,
        shared_arrays='time/observations/source arrays once per system; method predictions refer to the shared input',
        source_fields=list(SOURCE_FIELDS),no_experimental_CSV=True,no_model_states=True,
        external_access='NOT_PUBLISHED_P03_OPEN',remote='PENDING_NEXT_AUTHORIZED_SESSION_SYNC'))

def loaded_record(root,item):
    original=arrays(legacy.resolve(root,item['source']))
    predictions={}
    for method,path in item['predictions'].items():
        pred=arrays(legacy.resolve(root,path))
        pred.update({k:original[k] for k in SHARED})
        if not all(np.isfinite(x).all() for x in pred.values()):
            raise FloatingPointError('Nonfinite saved prediction')
        predictions[method]=pred
    return original,predictions

def score(config,root):
    out=legacy.resolve(root,config['output']);out.mkdir(parents=True,exist_ok=True)
    records=[];wave_rows=[];decomp_rows=[];charge_rows=[];pair_rows=[];energy_rows=[];interval_rows=[];cumulative_rows=[];euler_rows=[];peak_rows=[]
    safety=config['engineering_safety_factor']
    old_results=read_json(root/'expected-pchip-results.json')
    old_by_id={r['id']:r for r in old_results['records']}
    pchip_checks=[]
    for item in config['records']:
        original,preds=loaded_record(root,item);t=original['time'];rl=item['RL_ohm'];c=item['C_F'];vin=np.asarray(item['source_voltage_V'])
        devices=[];shared={};energy={};euler={}
        # Native power is interpolated as power, not as separately interpolated V and I.
        power=original['voltage']*original['device_current']
        boundaries=original['observation_time']
        ref_intervals=np.stack([reference_energy(t,power,a,b) for a,b in zip(boundaries[:-1],boundaries[1:])])
        for window,(lo,hi) in legacy.WINDOWS.items():
            mask=(t>=lo)&(t<=hi)
            euler[window]=euler_energy_check(t[mask],original['voltage'][mask],original['device_current'][mask],vin,rl,c,safety)
            if not all(d['valid'] for d in euler[window]):raise ArithmeticError('Euler energy closure failed')
            for j,d in enumerate(euler[window]):euler_rows.append(dict(id=item['id'],device=chr(65+j),window=window,**d))
        for method,pred in preds.items():
            pred_intervals=np.stack([prediction_energy(pred,a,b,vin,rl,c) for a,b in zip(boundaries[:-1],boundaries[1:])])
            err=pred_intervals-ref_intervals
            energy[method]=dict(windows={}, interval_summary=[])
            for window,(lo,hi) in legacy.WINDOWS.items():
                wr=reference_energy(t,power,lo,hi);wp=prediction_energy(pred,lo,hi,vin,rl,c)
                energy[method]['windows'][window]=[]
                for j in range(len(vin)):
                    d=dict(prediction_J=float(wp[j]),reference_trapezoid_J=float(wr[j]),signed_error_J=float(wp[j]-wr[j]),absolute_error_J=float(abs(wp[j]-wr[j])),
                           prediction_nJ=float(wp[j]*1e9),reference_nJ=float(wr[j]*1e9),signed_error_nJ=float((wp[j]-wr[j])*1e9),relative_error=None,
                           reference_measure='exact piecewise-linear integral of saved power')
                    energy[method]['windows'][window].append(d)
                    energy_rows.append(dict(id=item['id'],device=chr(65+j),method=method,window=window,**d))
            for j in range(len(vin)):
                es=dict(sum_absolute_interval_error_J=float(np.abs(err[:,j]).sum()),absolute_sum_interval_error_J=float(abs(err[:,j].sum())),
                        max_absolute_interval_error_J=float(np.abs(err[:,j]).max()),max_interval_index=int(np.abs(err[:,j]).argmax()),
                        intervals=196,last_interval_s=float(boundaries[-1]-boundaries[-2]))
                energy[method]['interval_summary'].append(es)
                for k in range(196):interval_rows.append(dict(id=item['id'],device=chr(65+j),method=method,interval=k,left_s=float(boundaries[k]),right_s=float(boundaries[k+1]),
                    prediction_J=float(pred_intervals[k,j]),reference_J=float(ref_intervals[k,j]),signed_error_J=float(err[k,j]),absolute_error_J=float(abs(err[k,j]))))
                pr=np.r_[0.,np.cumsum(pred_intervals[:,j])];rr=np.r_[0.,np.cumsum(ref_intervals[:,j])]
                for k in range(197):cumulative_rows.append(dict(id=item['id'],device=chr(65+j),method=method,time_s=float(boundaries[k]),prediction_J=float(pr[k]),reference_J=float(rr[k]),signed_error_J=float(pr[k]-rr[k])))
        for j,volts in enumerate(vin):
            label=chr(65+j);v=original['voltage'][:,j];idata=original['device_current'][:,j]
            f,kappa,checks=legacy.circuit_checks(t,v,idata,original['load_current'][:,j],original['capacitor_current'][:,j],volts,rl,c,safety)
            qcheck=legacy.charge_accounting(t,v,idata,volts,rl,c,kappa,safety)
            if not checks['pass'] or not qcheck['pass']:raise ArithmeticError('Source KCL/Euler charge identity failed')
            d=dict(device=label,KCL=checks,Euler_charge=qcheck,methods={})
            for method,pred in preds.items():
                dec=legacy.decomposition(t,v,idata,pred['voltage'][:,j],pred['voltage_derivative'][:,j],pred['device_current'][:,j],f,kappa,rl,c,safety)
                if not dec['pass']:raise ArithmeticError('Fixed-tolerance error decomposition failed')
                wave={};charges={}
                for window,(lo,hi) in legacy.WINDOWS.items():
                    mask=(t>=lo)&(t<=hi);tw=t[mask];wave[window]={};charges[window]={}
                    ql,qd=legacy.prediction_charge(pred,float(tw[0]),float(tw[-1]),vin,rl,c)
                    for branch in ['device_current','load_current']:
                        m=legacy.metrics(tw,pred[branch][mask,j],original[branch][mask,j]);wave[window][branch]=m
                        wave_rows.append(dict(id=item['id'],device=label,method=method,window=window,branch=branch,**m))
                        qpred=float(qd[j] if branch=='device_current' else ql[j]);qref=float(np.trapezoid(original[branch][mask,j],tw))
                        qm=dict(prediction_C=qpred,saved_trapezoid_C=qref,signed_difference_C=qpred-qref,absolute_difference_C=abs(qpred-qref),signed_difference_nC=(qpred-qref)*1e9,relative_error=None)
                        charges[window][branch]=qm;charge_rows.append(dict(id=item['id'],device=label,method=method,window=window,branch=branch,**qm))
                    dv=pred['voltage'][mask,j]-v[mask]
                    wave[window].update(voltage_RMS_V=float(np.sqrt(legacy.trap_weights(tw)@(dv*dv))),voltage_max_abs_V=float(max(abs(dv))),voltage_signed_mean_V=float(legacy.trap_weights(tw)@dv))
                peaks=legacy.summarize_peaks(t,idata,pred['device_current'][:,j],config['peak_match_max_gap_s'])
                for window,p in peaks.items():
                    for k,x in enumerate(p['pairs']):peak_rows.append(dict(id=item['id'],device=label,method=method,window=window,pair=k,**x))
                extrema={}
                for name,values in [('voltage_V',pred['voltage'][:,j]),('device_current_A',pred['device_current'][:,j]),('load_current_A',pred['load_current'][:,j]),('capacitor_current_A',pred['capacitor_current'][:,j]),('power_W',pred['voltage'][:,j]*pred['device_current'][:,j])]:
                    imin=int(np.argmin(values));imax=int(np.argmax(values))
                    extrema[name]=dict(minimum=float(values[imin]),minimum_at_s=float(t[imin]),maximum=float(values[imax]),maximum_at_s=float(t[imax]),negative_sample_count=int(np.count_nonzero(values<0)),scope='saved query times only; no continuous-extrema claim')
                d['methods'][method]=dict(waveforms=wave,charges=charges,decomposition=dec,peaks=peaks,load_peaks=None,native_extrema=extrema,
                                         sufficiency='UNKNOWN',tau_task=None,measurement='SAVED_AUTHOR_MODEL_NUMERICAL_DATA',execution='COMPLETE',implication='Developmental interpolation comparison only')
                decomp_rows.append(dict(id=item['id'],device=label,method=method,**dec))
                if method=='PCHIP':
                    old=old_by_id[item['id']]['devices'][j]
                    reproduced=[]
                    for window in legacy.WINDOWS:
                        for branch in ['device_current','load_current']:
                            for key in ['MSE_A2','RMS_A','max_abs_A','signed_mean_A']:
                                actual=wave[window][branch][key];expected=old['waveforms'][window][branch][key]
                                scale=abs(actual)+abs(expected)
                                if key=='signed_mean_A':
                                    scale+=wave[window][branch]['RMS_A']
                                tolerance=safety*np.finfo(np.float64).eps*(scale+1e-300)
                                if abs(actual-expected)>tolerance:
                                    raise ArithmeticError('Packed PCHIP legacy score changed')
                                reproduced.append(dict(window=window,branch=branch,metric=key,
                                    difference=actual-expected,tolerance=tolerance,exact=actual==expected))
                    if peaks!=old['peaks']:raise ArithmeticError('Packed PCHIP peak contract changed')
                    pchip_checks.append(dict(id=item['id'],device=label,
                        waveforms_exact=all(x['exact'] for x in reproduced),waveforms_FP64_reproduced=True,
                        details=reproduced,peaks_exact=True))
            row=dict(id=item['id'],case=item['case'],step_ns=item['dt_s']*1e9,device=label)
            for branch,short in [('device_current','device'),('load_current','load')]:
                ep=d['methods']['PCHIP']['waveforms']['full'][branch]['RMS_A'];ec=d['methods']['CS']['waveforms']['full'][branch]['RMS_A']
                row.update({short+'_PCHIP_RMS_uA':ep*1e6,short+'_CS_RMS_uA':ec*1e6,short+'_absolute_change_uA':(ep-ec)*1e6,short+'_relative_change':None if ep==0 else (ep-ec)/ep})
            pair_rows.append(row);devices.append(d)
        joint=[]
        if len(vin)==2:
            for method in preds:
                for window in legacy.WINDOWS:
                    for branch in ['device_current','load_current']:
                        mse=sum(d['methods'][method]['waveforms'][window][branch]['MSE_A2'] for d in devices)/2
                        joint.append(dict(method=method,window=window,branch=branch,MSE_A2=mse,RMS_uA=float(np.sqrt(mse)*1e6),device_weights='equal MSE weights'))
        records.append(dict(id=item['id'],case=item['case'],dt_s=item['dt_s'],devices=devices,joint_metrics=joint,energy=energy,Euler_energy=euler))
    sensitivity=[]
    for case in dict.fromkeys(x['case'] for x in config['records']):
        coarse,fine=sorted([x for x in config['records'] if x['case']==case],key=lambda x:x['dt_s'],reverse=True)
        oc,pc=loaded_record(root,coarse);of,pf=loaded_record(root,fine);t=oc['time']
        np.testing.assert_allclose(t,of['time'][::2],rtol=0,atol=1e-20)
        for method in pc:
            for j in range(oc['voltage'].shape[1]):
                for branch in ['device_current','load_current']:
                    orig=legacy.metrics(t,oc[branch][:,j],of[branch][::2,j]);pred=legacy.metrics(t,pc[method][branch][:,j],pf[method][branch][::2,j])
                    ec=pc[method][branch][:,j]-oc[branch][:,j];ef=pf[method][branch][::2,j]-of[branch][::2,j]
                    difference=legacy.metrics(t,ec,ef)
                    sensitivity.append(dict(case=case,device=chr(65+j),method=method,branch=branch,measure='trapz_weighted_common_1ns',
                        source_coarse_fine_RMS_A=orig['RMS_A'],error_curve_difference_RMS_A=difference['RMS_A'],
                        reconstruction_curve_difference_RMS_A=pred['RMS_A'],
                        reconstruction_RMS_signed_difference_common_A=legacy.metrics(t,pc[method][branch][:,j],oc[branch][:,j])['RMS_A']-legacy.metrics(t,pf[method][branch][::2,j],of[branch][::2,j])['RMS_A']))
    result=dict(task_id=config['task_id'],records=records,sensitivity=sensitivity,pchip_reproduction=pchip_checks,
                tau_task=None,experimental_numeric_read=False,new_PINN_method_increment_evaluated=False,new_system_steps=0,new_training_steps=0,
                scientific_status='VERIFIED_SAVED_ARRAY_COMPARISON_ABSOLUTE_SUFFICIENCY_UNKNOWN')
    legacy.save_json(out/'results.json',result)
    for name,rows in [('paired-comparison',pair_rows),('waveform-metrics',wave_rows),('charge-metrics',charge_rows),('error-decomposition',decomp_rows),('matched-peaks',peak_rows),('step-sensitivity',sensitivity),('energy-windows',energy_rows),('energy-intervals',interval_rows),('energy-cumulative',cumulative_rows),('euler-energy',euler_rows)]:
        legacy.write_csv(out/(name+'.csv'),rows)

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',default=str(ROOT));p.add_argument('--config',required=True)
    p.add_argument('--mode',choices=['predict','package','score'],required=True);args=p.parse_args()
    root=Path(args.root).resolve();config=read_json(legacy.resolve(root,args.config))
    if scipy.__version__!=config['scipy_version']:raise RuntimeError('Frozen SciPy version required')
    started=legacy.now();tic=time.perf_counter()
    if args.mode=='predict':make_predictions(config,root)
    elif args.mode=='package':package_subset(config,root)
    else:score(config,root)
    out=legacy.resolve(root,config['output'])
    legacy.save_json(out/('execution-'+args.mode+'.json'),dict(started=started,finished=legacy.now(),elapsed_seconds=time.perf_counter()-tic,
        mode=args.mode,python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,device='local CPU FP64',
        source_sha256=legacy.sha(Path(__file__)),new_system_steps=0,new_training_steps=0))
    print(json.dumps(dict(status='COMPLETE',mode=args.mode,output=str(out))))

if __name__=='__main__':main()
