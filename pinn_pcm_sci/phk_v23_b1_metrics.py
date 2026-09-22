"""NumPy-only B1 interval measures; old full-trajectory metrics are untouched."""
import numpy as np


def interval_weights(times, intervals):
    """Unnormalized trapezoids on each closed segment; never bridge a gap."""
    times=np.asarray(times);weights=np.zeros(len(times))
    for lo,hi in intervals:
        left,right=(int(np.argmin(abs(times-v))) for v in (lo,hi))
        if abs(times[left]-lo)>1e-12 or abs(times[right]-hi)>1e-12:
            raise ValueError('Frozen window endpoint missing; no implicit interpolation rule')
        if left>=right:
            raise ValueError('Empty or reversed scoring interval')
        delta=np.diff(times[left:right+1])
        weights[left:right]+=.5*delta
        weights[left+1:right+1]+=.5*delta
    np.testing.assert_allclose(weights.sum(),sum(hi-lo for lo,hi in intervals),rtol=1e-13,atol=1e-14)
    return weights


def window_records(fields,reference,device,cfg):
    t=reference.time;rs=cfg['qualification_event']['roi'];g=reference.grid
    roi=(abs(g.cell_x)<=rs['abs_x_max'])&(g.cell_z>=rs['z_min'])&(g.cell_z<=rs['z_max'])
    threshold=cfg['qualification_event']['phase_threshold']
    weights={'window':interval_weights(t,[(1.01,2.02)]),
             'outside':interval_weights(t,[(0.,1.01),(2.02,2.5)]),
             'full':interval_weights(t,[(0.,2.5)])}
    np.testing.assert_allclose(weights['window']+weights['outside'],weights['full'],rtol=0,atol=1e-15)
    # Numerators are stored before square root/normalization for exact accounting.
    series=dict(S=np.mean((fields['phase']>=threshold)!=(reference.phase>=threshold),axis=1),
        Ephi=np.mean((fields['phase'][:,roi]-reference.phase[:,roi])**2,axis=1),
        ET=np.mean((fields['temperature'][:,roi]-reference.temperature[:,roi])**2,axis=1),
        EV=np.mean((fields['potential']-reference.potential)**2,axis=1),
        EI=(device['top_current']-reference.top_current)**2,
        bottom_current_NRMSE=(device['bottom_current']-reference.top_current)**2,
        power_trace_NRMSE=(device['joule_power']-reference.joule_power)**2)
    result={}
    for scope,w in weights.items():
        duration=float(w.sum());num={k:float(w@v) for k,v in series.items()}
        normal=dict(top_current=float(np.sqrt(w@(reference.top_current**2)/duration)),
                    power=float(np.sqrt(w@(reference.joule_power**2)/duration)),temperature=.45,potential=1.,phase=1.)
        metrics={k:float(np.sqrt(v/duration)) for k,v in num.items()}
        metrics['S']=num['S']/duration
        metrics['ET']/=.45
        metrics['EI']/=max(normal['top_current'],1e-12)
        metrics['bottom_current_NRMSE']/=max(normal['top_current'],1e-12)
        metrics['power_trace_NRMSE']/=max(normal['power'],1e-12)
        result[scope]=dict(metrics=metrics,normalizers=normal,duration=duration,
            unnormalized_error_integrals=num,valid=all(np.isfinite(v) for v in metrics.values()),
            current_guard_identity='predicted native top_current versus reference native top_current',
            bottom_current_identity='historical predicted bottom_current versus reference top_current',
            T_phase_grid=[160,80],potential_measure='full-domain raw RMS; fine V volume restriction only')
    for k in series:
        np.testing.assert_allclose(result['window']['unnormalized_error_integrals'][k]+result['outside']['unnormalized_error_integrals'][k],
            result['full']['unnormalized_error_integrals'][k],rtol=2e-12,atol=2e-14)
    return result


def outside_cost(candidate,control,cfg):
    tol=cfg['decision']['absolute_tolerance']
    return {k:bool(candidate['metrics'][k]>control['metrics'][k]+max(.05*control['metrics'][k],tol.get(k,1e-6)))
            for k in ('S','Ephi','ET','EI','EV','bottom_current_NRMSE','power_trace_NRMSE')}
