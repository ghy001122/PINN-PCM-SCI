"""Fixed voltage-only circuit screen of saved trajectories; no system integrator.

Author-model identities, observations and tolerances are frozen in the task JSON.
Prediction takes no hidden states. Scoring consumes the immutable prediction files.
"""
from __future__ import annotations
import argparse
import csv
from functools import lru_cache
import hashlib
import json
import platform
from pathlib import Path
import sys
import time
from datetime import datetime, timezone

import numpy as np
import scipy
from scipy.interpolate import PchipInterpolator, PPoly

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pinn_pcm_sci.vo2_author_reproduction import detect_peaks

EPS = np.finfo(np.float64).eps
WINDOWS = {'full': (0., 20e-6), 'transient': (0., 10e-6), 'tail': (10e-6, 20e-6)}

def now():
    return datetime.now(timezone.utc).isoformat()

def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def resolve(root, relative):
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError('Input/output must stay under the explicitly supplied root')
    return target

def trap_weights(t):
    t = np.asarray(t, dtype=np.float64)
    dt = np.diff(t)
    if len(t) < 2 or not np.all(np.isfinite(t)) or not np.all(dt > 0):
        raise ValueError('Time must be finite and strictly increasing')
    w = np.empty(len(t))
    w[0], w[-1] = dt[0]/2, dt[-1]/2
    w[1:-1] = (dt[:-1]+dt[1:])/2
    return w / (t[-1]-t[0])

def observation_times(t0, tend, spacing=102.4e-9):
    # Integer multiplication rather than accumulated floating-point increments.
    k = np.arange(int(np.floor((tend-t0)/spacing))+1, dtype=np.int64)
    s = t0+k*spacing
    tolerance = 8*EPS*max(abs(t0), abs(tend), spacing)
    s = s[s <= tend+tolerance]
    if abs(s[-1]-tend) <= tolerance:
        s[-1] = tend
    else:
        s = np.append(s, tend)
    if not np.all(np.diff(s) > 0):
        raise ValueError('Duplicate observation times')
    return s

def experimental_indices(n, stride=32):
    if n < 2:
        raise ValueError('Insufficient rows')
    return np.unique(np.r_[np.arange(0, n, stride, dtype=int), n-1])

def export_observations(t, voltage, spacing):
    s = observation_times(float(t[0]), float(t[-1]), spacing)
    values = np.column_stack([np.interp(s, t, voltage[:, j]) for j in range(voltage.shape[1])])
    return s, values

def predict(obs_time, obs_voltage, source_voltage, resistance, capacitance, query_time,
            time_scale=1e-6):
    """The entire prediction interface: finite voltage observations and known circuit."""
    obs_time = np.asarray(obs_time, dtype=np.float64)
    obs_voltage = np.asarray(obs_voltage, dtype=np.float64)
    query_time = np.asarray(query_time, dtype=np.float64)
    if obs_voltage.ndim == 1:
        obs_voltage = obs_voltage[:, None]
    if np.any(query_time < obs_time[0]) or np.any(query_time > obs_time[-1]):
        raise ValueError('No extrapolation is permitted')
    if resistance <= 0 or (capacitance is not None and capacitance <= 0):
        raise ValueError('Circuit parameters must be positive')
    pp = PchipInterpolator((obs_time-obs_time[0])/time_scale, obs_voltage,
                           axis=0, extrapolate=False)
    tau = (query_time-obs_time[0])/time_scale
    v = pp(tau)
    derivative = pp.derivative(1)(tau)/time_scale
    load = (np.asarray(source_voltage)-v)/resistance
    out = {'time': query_time, 'observation_time': obs_time, 'observation_voltage': obs_voltage,
           'voltage': v, 'voltage_derivative': derivative, 'load_current': load,
           'polynomial_coefficients': pp.c, 'polynomial_breakpoints': pp.x,
           'time_origin': np.asarray(obs_time[0]), 'time_scale': np.asarray(time_scale)}
    if capacitance is not None:
        out['capacitor_current'] = capacitance*derivative
        out['device_current'] = load-out['capacitor_current']
    if not all(np.isfinite(x).all() for x in out.values()):
        raise FloatingPointError('Non-finite prediction')
    return out

def prediction_charge(pred, left, right, vin, rl, capacitance):
    scale = float(pred['time_scale']); origin = float(pred['time_origin'])
    pp = PPoly(pred['polynomial_coefficients'], pred['polynomial_breakpoints'], extrapolate=False)
    a, b = (left-origin)/scale, (right-origin)/scale
    ql = (np.asarray(vin)*(right-left)-scale*pp.integrate(a, b))/rl
    qd = None if capacitance is None else ql-capacitance*(pp(b)-pp(a))
    return ql, qd

def branch_eligibility(q):
    common = all(q.get(k, False) for k in ['legal_voltage', 'interval_drive', 'load_resistance', 'equivalent_topology'])
    if not common:
        return {'predict_load': False, 'score_load': False, 'predict_device': False, 'score_device': False}
    device = q.get('capacitance_known', False)
    return {'predict_load': True, 'score_load': q.get('independent_load_measurement', False),
            'predict_device': device, 'score_device': device and q.get('independent_device_measurement', False)}

def allowed_experimental_member(member, config):
    return member in config['experimental_development_allowlist'] and member != config['sealed_member']

def peak_matches(reference_times, prediction_times, max_gap=0.25e-6):
    a, b = tuple(reference_times), tuple(prediction_times)
    tolerance = 8*EPS*max((max_gap, *map(abs, a), *map(abs, b)))
    @lru_cache(None)
    def solve(i, j):
        if i == len(a) or j == len(b):
            return ()
        choices = [solve(i+1, j), solve(i, j+1)]
        if abs(a[i]-b[j]) <= max_gap+tolerance:
            choices.append(((i, j),)+solve(i+1, j+1))
        # Most matches, then least total displacement, then earliest times.
        return min(choices, key=lambda pairs: (-len(pairs), sum(abs(a[x]-b[y]) for x,y in pairs),
                                               tuple((a[x], b[y]) for x,y in pairs)))
    pairs = list(solve(0, 0))
    used_a, used_b = {x for x,y in pairs}, {y for x,y in pairs}
    return pairs, [i for i in range(len(a)) if i not in used_a], [j for j in range(len(b)) if j not in used_b]

def metrics(t, prediction, reference):
    d = np.asarray(prediction)-np.asarray(reference)
    w = trap_weights(t)
    mse = float(w @ (d*d))
    return {'MSE_A2': mse, 'RMS_A': float(np.sqrt(mse)), 'RMS_uA': float(np.sqrt(mse)*1e6),
            'NRMSE_1mA': float(np.sqrt(mse)/1e-3), 'max_abs_A': float(np.max(np.abs(d))),
            'signed_mean_A': float(w @ d), 'measure': 'trapz_weighted_native', 'includes_endpoints': True}

def circuit_checks(t, v, device, load, capacitor, vin, rl, c, safety):
    h = np.diff(t)
    f = np.diff(v)/h
    load_formula = (vin-v)/rl
    same = load-device-capacitor
    same_tol = safety*EPS*(abs(load)+abs(device)+abs(capacitor)+1e-300)
    load_tol = safety*EPS*((abs(vin)+abs(v))/rl+abs(load)+1e-300)
    kappa = load_formula[:-1]-device[:-1]-c*f
    # Operation scale, including cancellation and absolute time representation.
    scale = (abs(load_formula[:-1])+abs(device[:-1])
             + c*(abs(v[:-1])+abs(v[1:]))/h
             + c*abs(f)*(abs(t[:-1])+abs(t[1:]))/h + 1e-300)
    kappa_tol = safety*EPS*scale
    w = trap_weights(t[:-1])
    checks = {'same_level': {'max_abs_A': float(max(abs(same))),
                             'max_tolerance_A': float(max(same_tol)),
                             'pass': bool(np.all(abs(same) <= same_tol)),
                             'source': 'three separately saved source-RHS branch arrays; serialization consistency, not independent physical measurement'},
              'load_readout': {'max_abs_A': float(max(abs(load-load_formula))),
                               'pass': bool(np.all(abs(load-load_formula) <= load_tol))},
              'step_kappa': {'max_abs_A': float(max(abs(kappa))), 'RMS_A': float(np.sqrt(w@(kappa*kappa))),
                             'max_at_s': float(t[np.argmax(abs(kappa))]),
                             'max_tolerance_A': float(max(kappa_tol)),
                             'max_scaled_defect': float(max(abs(kappa)/kappa_tol)),
                             'pass': bool(np.all(abs(kappa) <= kappa_tol)),
                             'interval_s': [float(t[0]),float(t[-2])]},
              'safety_factor': safety, 'tolerance_kind': 'FP64 operation-scale engineering allowance, not a solution-error bound'}
    checks['pass'] = all(checks[k]['pass'] for k in ['same_level','load_readout','step_kappa'])
    return f, kappa, checks

def decomposition(t, v, device, pred_v, pred_dv, pred_i, f, kappa, rl, c, safety):
    a = (pred_v[:-1]-v[:-1])/rl
    b = c*(pred_dv[:-1]-f)
    di = pred_i[:-1]-device[:-1]
    w = trap_weights(t[:-1])
    A, B, X = float(w@(a*a)), float(w@(b*b)), float(2*(w@(a*b)))
    K = float(w@(kappa*kappa)-2*(w@((a+b)*kappa)))
    direct = float(w@(di*di))
    closure = direct-(A+B+X+K)
    algebra = di+a+b-kappa
    algebra_tol = safety*EPS*(abs(pred_i[:-1])+abs(device[:-1])+abs(a)+abs(b)+abs(kappa)+1e-300)
    # The squared error may be tiny after subtracting two much larger currents.
    # Propagate the predeclared current-operation allowance through the square;
    # a relative allowance on MSE alone misses this cancellation scale.
    tolerance = (safety*EPS*(abs(direct)+abs(A)+abs(B)+abs(X)+abs(K)+1e-300)
                 + float(w@(2*abs(di)*algebra_tol+algebra_tol**2)))
    return {'A_A2':A,'B_A2':B,'X_A2':X,'K_A2':K,'direct_MSE_A2':direct,
            'closure_A2':closure,'closure_tolerance_A2':tolerance,
            'identity_max_abs_A':float(max(abs(algebra))),
            'pass': bool(abs(closure)<=tolerance and np.all(abs(algebra)<=algebra_tol)),
            'measure':'trapz_weighted_nonendpoint_renormalized',
            'interval_s':[float(t[0]),float(t[-2])],
            'interpretation':'Algebra verification only; separate KCL checks establish serialization/timing consistency.'}

def charge_accounting(t, v, current, vin, rl, c, kappa, safety):
    h = np.diff(t)
    qleft = float(h@current[:-1])
    qtrap = float(np.trapezoid(current, t))
    load_left = float(h@((vin-v[:-1])/rl))
    capacitor_change = float(c*(v[-1]-v[0]))
    correction = float(h@kappa)
    defect = qleft-(load_left-capacitor_change-correction)
    trap_minus_left = qtrap-qleft
    expected_diff = float(.5*np.sum(h*np.diff(current)))
    scale = abs(qleft)+abs(load_left)+abs(capacitor_change)+abs(correction)+1e-300
    return {'Q_device_left_C':qleft,'Q_device_trap_C':qtrap,'Q_load_left_C':load_left,
            'capacitor_charge_change_C':capacitor_change,'integrated_kappa_C':correction,
            'Euler_closure_C':defect,'trap_minus_left_C':trap_minus_left,
            'trap_minus_left_from_increments_C':expected_diff,
            'pass':bool(abs(defect)<=safety*EPS*scale and abs(trap_minus_left-expected_diff)<=safety*EPS*scale),
            'scope':'saved numerical Euler data only; not a continuous conservation certificate'}

def summarize_peaks(t, reference, prediction, gap):
    ir, ip = detect_peaks(t, reference), detect_peaks(t, prediction)
    result = {}
    for window, (lo, hi) in WINDOWS.items():
        r, p = ir[(t[ir]>=lo)&(t[ir]<=hi)], ip[(t[ip]>=lo)&(t[ip]<=hi)]
        pairs, ur, up = peak_matches(t[r].tolist(), t[p].tolist(), gap)
        record = {'reference_times_s':t[r].tolist(),'prediction_times_s':t[p].tolist(),
                  'reference_heights_A':reference[r].tolist(),'prediction_heights_A':prediction[p].tolist(),
                  'reference_count':len(r),'prediction_count':len(p),
                  'pairs': [{'reference_time_s':float(t[r[x]]),'prediction_time_s':float(t[p[y]]),
                             'signed_time_difference_s':float(t[p[y]]-t[r[x]]),
                             'signed_height_difference_A':float(prediction[p[y]]-reference[r[x]])} for x,y in pairs],
                  'unmatched_reference_times_s':t[r[ur]].tolist(), 'unmatched_prediction_times_s':t[p[up]].tolist(),
                  'timing_RMS_s':float(np.sqrt(np.mean([(t[p[y]]-t[r[x]])**2 for x,y in pairs]))) if pairs else None,
                  'reference_first_peak_s':float(t[r[0]]) if len(r) else None,
                  'prediction_first_peak_s':float(t[p[0]]) if len(p) else None,
                  'reference_ISI_s':np.diff(t[r]).tolist(),'prediction_ISI_s':np.diff(t[p]).tolist(),
                  'reference_frequency_Hz':float(1/np.mean(np.diff(t[r]))) if len(r)>1 else None,
                  'prediction_frequency_Hz':float(1/np.mean(np.diff(t[p]))) if len(p)>1 else None,
                  'matching_max_gap_s':gap,'functional_state_prediction':None}
        result[window] = record
    return result

def write_csv(path, rows):
    if not rows:
        return
    with Path(path).open('w',encoding='utf-8',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)

def make_predictions(config, root, out):
    start = time.perf_counter(); records = []
    contract = json.loads(resolve(root,config['source_contract']).read_text(encoding='utf-8'))
    params = contract['parameters_SI']; c, rl = params['C'], params['RL']
    cases = {x['id']:x for x in contract['cases']}
    for item in config['simulation_inputs']:
        original = resolve(root,item['path']); target = out/'predictions'/(item['id']+'.npz')
        meta_path = target.with_suffix('.json')
        if target.exists() or meta_path.exists():
            raise FileExistsError('Frozen prediction already exists; use score/figures to reuse it')
        with np.load(original,allow_pickle=False) as data:
            t, v = data['time'].copy(), data['voltage'].copy()
            if t.dtype != np.float64 or v.dtype != np.float64 or v.shape[0]!=len(t):
                raise ValueError('Unexpected precision or shape')
            expected = int(round(contract['end_seconds']/item['dt_s']))+1
            if len(t)!=expected or abs(t[-1]-20e-6)>1e-19 or not np.allclose(np.diff(t),item['dt_s'],rtol=1e-10,atol=0):
                raise ValueError('Native time identity does not match frozen trajectory')
            obs_t, obs_v = export_observations(t,v,config['observation_interval_s'])
            if len(obs_t)!=197:
                raise ValueError('Unexpected observation count')
            pred = predict(obs_t,obs_v,cases[item['case']]['Vin'],rl,c,t,config['time_scale_s'])
            target.parent.mkdir(parents=True,exist_ok=True)
            np.savez_compressed(target,**pred)
            meta = {'input':item,'source_fields':list(data.files),
                    'consumed_prediction_fields':['time','voltage'],
                    'shape':[int(x) for x in v.shape],'dtype':'float64','time_unit':'s','voltage_unit':'V',
                    'current_unit':'A','saved_native_step_s':item['dt_s'],'states':len(t),
                    'observations':len(obs_t),'last_observation_interval_s':float(obs_t[-1]-obs_t[-2]),
                    'C_F':c,'RL_ohm':rl,'source_voltage_V':cases[item['case']]['Vin'],
                    'fixed_at':now(),'prediction_sha256':sha(target),'score_read_before_prediction_lock':False}
            save_json(meta_path,meta);records.append(meta)
    save_json(out/'predictions-locked.json',{'task_id':config['task_id'],'records':records,
              'elapsed_seconds':time.perf_counter()-start,'new_system_steps':0,'new_training_steps':0,
              'scipy_version':scipy.__version__,'numpy_version':np.__version__,'python':platform.python_version(),
              'execution_device':'CPU SciPy on the authorized GPU instance; no GPU arithmetic required by PCHIP'})

def score(config, root, out):
    locked=json.loads((out/'predictions-locked.json').read_text(encoding='utf-8'))
    records=[];wave_rows=[];charge_rows=[];decomp_rows=[]
    safety=config['engineering_safety_factor']
    for meta in locked['records']:
        item=meta['input'];case=item['case'];rl=meta['RL_ohm'];c=meta['C_F']
        pred_path=out/'predictions'/(item['id']+'.npz')
        # Identity is established once before scoring the immutable prediction.
        if sha(pred_path)!=meta['prediction_sha256']:
            raise ValueError('Prediction identity changed after lock')
        with np.load(resolve(root,item['path']),allow_pickle=False) as original, np.load(pred_path,allow_pickle=False) as pred:
            t=original['time'];devices=[];all_metrics={}
            for j,vin in enumerate(meta['source_voltage_V']):
                label=chr(65+j);v=original['voltage'][:,j]
                idata=original['device_current'][:,j]
                f,kappa,checks=circuit_checks(t,v,idata,original['load_current'][:,j],original['capacitor_current'][:,j],vin,rl,c,safety)
                if not checks['pass']:
                    save_json(out/(item['id']+'-invalid.json'),checks)
                    raise ValueError('Native array identity/KCL failed; no shift or solver rescue')
                dec=decomposition(t,v,idata,pred['voltage'][:,j],pred['voltage_derivative'][:,j],pred['device_current'][:,j],f,kappa,rl,c,safety)
                charge_check=charge_accounting(t,v,idata,vin,rl,c,kappa,safety)
                if not dec['pass'] or not charge_check['pass']:
                    raise ArithmeticError('Algebra verification failed')
                wave={};charge={}
                for window,(lo,hi) in WINDOWS.items():
                    mask=(t>=lo)&(t<=hi);tw=t[mask]
                    wave[window]={}
                    charge[window]={}
                    ql,qd=prediction_charge(pred,float(tw[0]),float(tw[-1]),meta['source_voltage_V'],rl,c)
                    for branch in ['device_current','load_current']:
                        met=metrics(tw,pred[branch][mask,j],original[branch][mask,j])
                        wave[window][branch]=met
                        all_metrics[j,window,branch]=met
                        wave_rows.append({'case':case,'step_ns':item['dt_s']*1e9,'device':label,'window':window,'branch':branch,**met})
                        qp=float(qd[j] if branch=='device_current' else ql[j])
                        qr=float(np.trapezoid(original[branch][mask,j],tw))
                        q={'prediction_C':qp,'saved_trapezoid_C':qr,'signed_difference_C':qp-qr,
                           'absolute_difference_C':abs(qp-qr),'signed_difference_nC':(qp-qr)*1e9,
                           'relative_error':None,'interpretation':'different integration rules retained'}
                        charge[window][branch]=q
                        charge_rows.append({'case':case,'step_ns':item['dt_s']*1e9,'device':label,'window':window,'branch':branch,**q})
                    dv=pred['voltage'][mask,j]-v[mask]
                    wave[window]['voltage_RMS_V']=float(np.sqrt(trap_weights(tw)@(dv*dv)))
                    wave[window]['voltage_max_abs_V']=float(max(abs(dv)))
                pi=pred['device_current'][:,j]
                minimum=int(np.argmin(pi));neg_tol=safety*EPS*max(float(max(abs(pi))),1e-300)
                negative=pi < -neg_tol
                neg={'minimum_A':float(pi[minimum]),'minimum_at_s':float(t[minimum]),
                     'first_below_roundoff_s':float(t[np.flatnonzero(negative)[0]]) if negative.any() else None,
                     'last_below_roundoff_s':float(t[np.flatnonzero(negative)[-1]]) if negative.any() else None,
                     'weighted_fraction_below_roundoff':float(trap_weights(t)@negative),
                     'roundoff_threshold_A':neg_tol,'clipped':False}
                device={'device':label,'waveforms':wave,'charges':charge,'KCL':checks,'decomposition':dec,
                        'Euler_charge':charge_check,'peaks':summarize_peaks(t,idata,pi,config['peak_match_max_gap_s']),
                        'load_peaks':None,'load_peaks_reason':'No predeclared load-current detector',
                        'negative_prediction':neg,'execution':'VALID_SAVED_ARRAY_SCREEN',
                        'measurement':'AUTHOR_MODEL_SAVED_NUMERICAL_TRAJECTORY','sufficiency':'UNKNOWN',
                        'task_tolerance_A':None,'implication':'Fixed interpolation/circuit ability only; no PINN necessity or material validation'}
                devices.append(device)
                decomp_rows.append({'case':case,'step_ns':item['dt_s']*1e9,'device':label,
                                    **{k:dec[k] for k in ['A_A2','B_A2','X_A2','K_A2','direct_MSE_A2','closure_A2','pass']}})
            joint=[]
            if len(devices)==2:
                for window in WINDOWS:
                    for branch in ['device_current','load_current']:
                        mse=sum(all_metrics[j,window,branch]['MSE_A2'] for j in range(2))/2
                        joint.append({'window':window,'branch':branch,'MSE_A2':mse,'RMS_uA':float(np.sqrt(mse)*1e6),
                                      'NRMSE_1mA':float(np.sqrt(mse)/1e-3),'device_weight':'equal MSE weights'})
            records.append({'id':item['id'],'case':case,'dt_s':item['dt_s'],'devices':devices,'joint_metrics':joint})
    sensitivity=[]
    for case in dict.fromkeys(x['case'] for x in config['simulation_inputs']):
        items=sorted([x for x in config['simulation_inputs'] if x['case']==case],key=lambda x:x['dt_s'],reverse=True)
        coarse,fine=items
        with np.load(resolve(root,coarse['path']),allow_pickle=False) as oc, np.load(resolve(root,fine['path']),allow_pickle=False) as of, np.load(out/'predictions'/(coarse['id']+'.npz'),allow_pickle=False) as pc, np.load(out/'predictions'/(fine['id']+'.npz'),allow_pickle=False) as pf:
            t=oc['time'];np.testing.assert_allclose(t,of['time'][::2],rtol=0,atol=1e-20)
            for j in range(oc['voltage'].shape[1]):
                for branch in ['device_current','load_current']:
                    orig=metrics(t,oc[branch][:,j],of[branch][::2,j])
                    pred=metrics(t,pc[branch][:,j],pf[branch][::2,j])
                    ec=pc[branch][:,j]-oc[branch][:,j];ef=pf[branch][::2,j]-of[branch][::2,j]
                    em=metrics(t,ec,ef)
                    common_c=metrics(t,pc[branch][:,j],oc[branch][:,j])['RMS_A']
                    common_f=metrics(t,pf[branch][::2,j],of[branch][::2,j])['RMS_A']
                    sensitivity.append({'case':case,'device':chr(65+j),'branch':branch,'measure':'trapz_weighted_common_1ns',
                      'original_coarse_fine_RMS_A':orig['RMS_A'],'original_coarse_fine_max_A':orig['max_abs_A'],
                      'reconstruction_error_curve_difference_RMS_A':em['RMS_A'],
                      'reconstruction_RMS_signed_difference_common_A':common_c-common_f,
                      'reconstructed_coarse_fine_RMS_A':pred['RMS_A'],'reconstructed_coarse_fine_max_A':pred['max_abs_A'],
                      'interpretation':'Sensitivity only; not an error bound or independent repetition'})
    save_json(out/'results.json',{'task_id':config['task_id'],'records':records,'sensitivity':sensitivity,
              'experimental':config['experimental_qualification'],'tau_task':None,
              'new_PINN_method_increment_evaluated':False,'new_system_steps':0,'new_training_steps':0,
              'scientific_arrays_generated':'14 voltage reconstructions in 10 NPZ files; no new device trajectory',
              'experimental_raw_numeric_members_opened':[],'sealed_protocol_numeric_read':False})
    write_csv(out/'waveform-metrics.csv',wave_rows);write_csv(out/'charge-metrics.csv',charge_rows)
    write_csv(out/'error-decomposition.csv',decomp_rows);write_csv(out/'step-sensitivity.csv',sensitivity)

def figures(config,root,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    result=json.loads((out/'results.json').read_text(encoding='utf-8'))
    dest=out/'figures';dest.mkdir(exist_ok=True)
    for case in dict.fromkeys(x['case'] for x in config['simulation_inputs']):
        items=sorted([x for x in config['simulation_inputs'] if x['case']==case],key=lambda x:x['dt_s'],reverse=True)
        with np.load(resolve(root,items[0]['path']),allow_pickle=False) as x:
            n=x['voltage'].shape[1]
        fig,axes=plt.subplots(n,2,figsize=(12,3.2*n),squeeze=False,layout='constrained')
        for index,item in enumerate(items):
            with np.load(resolve(root,item['path']),allow_pickle=False) as original, np.load(out/'predictions'/(item['id']+'.npz'),allow_pickle=False) as pred:
                for j in range(n):
                    for k,branch in enumerate(['device_current','load_current']):
                        ax=axes[j,k];ns=item['dt_s']*1e9
                        ax.plot(original['time']*1e6,original[branch][:,j]*1e3,color=['#111111','#888888'][index],lw=.85,label=f'Saved {ns:g} ns')
                        ax.plot(pred['time']*1e6,pred[branch][:,j]*1e3,color=['#007D8A','#D77528'][index],lw=.9,ls=['--','-'][index],label=f'PCHIP {ns:g} ns')
                        ax.set(xlabel='Time (microseconds)',ylabel='Current (mA)',title=f'Device {chr(65+j)} / {branch.replace("_"," ")}')
                        ax.grid(alpha=.18);ax.legend(fontsize=8,ncol=2)
        fig.suptitle(case+' | Fixed 102.4 ns voltage observations; no alignment',fontsize=12)
        fig.savefig(dest/(case+'.png'),dpi=180);plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(12,8),layout='constrained')
    for ax,dt in zip(axes,[1e-9,.5e-9]):
        values=[(r['case']+'/'+d['device'],d['decomposition']) for r in result['records'] if r['dt_s']==dt for d in r['devices']]
        x=np.arange(len(values))
        for offset,(key,color) in enumerate(zip(['A_A2','B_A2','X_A2','K_A2'],['#4477AA','#EE7733','#228833','#AA3377'])):
            ax.bar(x+(offset-1.5)*.18,[d[key]*1e12 for _,d in values],width=.18,color=color,label=key[:-3])
        ax.axhline(0,color='black',lw=.6);ax.set_xticks(x,[a for a,_ in values],rotation=20,ha='right')
        ax.set_yscale('symlog',linthresh=1.);ax.set_ylabel('Signed terms (microampere squared)')
        ax.set_title(f'{dt*1e9:g} ns source | nonendpoint trapezoidal measure');ax.legend(ncol=4)
    fig.savefig(dest/'signed-error-decomposition.png',dpi=180);plt.close(fig)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',required=True);parser.add_argument('--root',default=str(ROOT))
    parser.add_argument('--mode',choices=['predict','score','figures','all'],default='all')
    args=parser.parse_args();root=Path(args.root).resolve()
    config=json.loads(Path(args.config).read_text(encoding='utf-8'))
    if scipy.__version__!='1.14.1':
        raise RuntimeError('Frozen SciPy 1.14.1 required')
    out=resolve(root,config['output']);out.mkdir(parents=True,exist_ok=True)
    started=now();tic=time.perf_counter()
    if args.mode in ['predict','all']:make_predictions(config,root,out)
    if args.mode in ['score','all']:score(config,root,out)
    if args.mode in ['figures','all']:figures(config,root,out)
    save_json(out/('execution-'+args.mode+'.json'),{'started':started,'finished':now(),'elapsed_seconds':time.perf_counter()-tic,
        'mode':args.mode,'config':str(Path(args.config)),'source_identity':sha(Path(__file__)),'new_ODE_PDE_steps':0,
        'new_training_steps':0,'GPU_arithmetic':False})
    print(json.dumps({'output':str(out),'mode':args.mode,'status':'COMPLETE'}))

if __name__=='__main__':
    main()
