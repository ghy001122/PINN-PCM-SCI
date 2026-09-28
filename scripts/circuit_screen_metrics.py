"""Exact reused frozen scoring functions, without any model integration entry.
Sources: paper/paper_revision_20260927_circuit_screen/circuit-screen/scoring-source.py
and pinn_pcm_sci/vo2_author_reproduction.py:detect_peaks (project MIT license).
"""
from pathlib import Path
from datetime import datetime, timezone
from functools import lru_cache
import csv, hashlib, json
import numpy as np
from scipy.interpolate import PPoly
EPS=np.finfo(np.float64).eps
WINDOWS={'full':(0.,20e-6),'transient':(0.,10e-6),'tail':(10e-6,20e-6)}
def detect_peaks(times,current):
    candidates=np.flatnonzero((current[1:-1]>current[:-2])&(current[1:-1]>=current[2:])&(current[1:-1]>.0015))+1
    chosen=[]
    for i in sorted(candidates,key=lambda j:(-current[j],times[j])):
        if all(abs(times[i]-times[j])>=.5e-6-1e-18 for j in chosen):chosen.append(int(i))
    return np.array(sorted(chosen),dtype=int)

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

def prediction_charge(pred, left, right, vin, rl, capacitance):
    scale = float(pred['time_scale']); origin = float(pred['time_origin'])
    pp = PPoly(pred['polynomial_coefficients'], pred['polynomial_breakpoints'], extrapolate=False)
    a, b = (left-origin)/scale, (right-origin)/scale
    ql = (np.asarray(vin)*(right-left)-scale*pp.integrate(a, b))/rl
    qd = None if capacitance is None else ql-capacitance*(pp(b)-pp(a))
    return ql, qd

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
    algebra_tol = safety*EPS*(abs(pred_i[:-1])+abs(device[:-1])+abs(a)+abs(b)+abs(kappa)
                  +(abs(pred_v[:-1])+abs(v[:-1]))/rl+c*(abs(pred_dv[:-1])+abs(f))+1e-300)
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
