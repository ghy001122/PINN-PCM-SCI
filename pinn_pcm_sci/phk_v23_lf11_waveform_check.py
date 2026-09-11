"""Posthoc same-observation voltage-envelope check; no training or new physics."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator, RegularGridInterpolator
import torch
from .phk_benchmark import PhkControl
from .phk_v22r_evaluator import load_reference
from .phk_v23_lf11 import SparseData, build_model, tensor, save_json, now
from .phk_v23_lf11_readout import interpolate_sparse
from .phk_v23_lf11_evaluation import metrics


def normalized_voltage(data,x,z,times,physics):
    a=data.arrays
    source_t=a['time']; source_u=physics.waveform(tensor(source_t)).numpy()
    target_u=physics.waveform(tensor(times)).numpy()
    source=data.targets[:,0].reshape(len(source_t),len(a['z']),len(a['x']))
    response=np.zeros((len(times),len(a['z']),len(a['x'])))
    for cycle in range(2):
        # Zero-voltage observations contain no information about V/U.
        visible=(source_u>1e-12)&(source_t>=cycle*physics.period)&(source_t<(cycle+1)*physics.period)
        target=(target_u>1e-12)&(times>=cycle*physics.period)&(times<(cycle+1)*physics.period)
        ts=source_t[visible]
        if len(ts)<2: raise ValueError('insufficient visible positive-voltage samples')
        beta=source[visible]/source_u[visible,None,None]
        query=np.clip(times[target],ts[0],ts[-1])
        response[target]=PchipInterpolator(ts,beta,axis=0)(query)
    response=np.pad(response,((0,0),(1,1),(1,1)),mode='edge')
    sx=np.r_[physics.x_min,a['x'],physics.x_max]
    sz=np.r_[physics.z_min,a['z'],physics.z_max]
    response[:,-1,:]=1
    response[:,0,np.abs(sx)<=physics.heater_half_width]=0
    xx,zz=np.meshgrid(x,z,indexing='xy')
    query=np.column_stack((zz.ravel(),xx.ravel()))
    beta=np.stack([RegularGridInterpolator((sz,sx),v,bounds_error=True)(query) for v in response])
    return target_u[:,None]*np.clip(beta,0,1)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    a=p.parse_args()
    root=a.root
    config=json.loads((root/'formal/frozen_config.json').read_text())
    previous=json.loads((root/'local/results.json').read_text())
    output=root/'local/waveform-diagnostic.json'
    if output.exists(): raise FileExistsError('the bounded waveform diagnosis already exists')
    torch.set_num_threads(2)
    physics=build_model(config).physics
    data=SparseData(root/'input/sparse.npz')
    # Check source interpolation exactly, before reading any new target values.
    source_prediction=normalized_voltage(data,data.arrays['x'],data.arrays['z'],data.arrays['time'],physics)
    expected=data.targets[:,0].reshape(source_prediction.shape)
    preservation=float(np.max(np.abs(source_prediction-expected)))
    if preservation>1e-12: raise ValueError('visible voltage observations changed')
    reference,_=load_reference(PhkControl.FULL)
    fields=interpolate_sparse(data,reference.grid.x_centers,reference.grid.z_centers,reference.time,physics,'B_logit')
    fields['potential']=normalized_voltage(data,reference.grid.x_centers,reference.grid.z_centers,reference.time,physics)
    record,traces=metrics(fields,reference,physics,config)
    for key in ('S','Ephi','ET'):
        if record['metrics'][key]!=previous['records']['B_logit']['metrics'][key]:
            raise ValueError('non-voltage field metric changed in the voltage-only diagnostic')
    with np.load(root/'local/traces.npz',allow_pickle=False) as f:
        original_current=f['B_logit__top_current']
    knots=np.array([.05,.27,.35,1.30,1.52,1.60])
    near=np.min(np.abs(reference.time[:,None]-knots),axis=1)<=.02+1e-14
    error=(original_current-reference.top_current)**2
    fraction=float(np.trapezoid(error*near,reference.time)/np.trapezoid(error,reference.time))
    save_json(output,{'schema_id':'lf11-posthoc-voltage-envelope-diagnostic-v1','recorded_utc':now(),
        'role':'B_logit_waveform','status':'POSTHOC_SAME_OBSERVATION_BASELINE_DIAGNOSTIC',
        'record':record,'original_B_logit':previous['records']['B_logit']['metrics'],
        'visible_voltage_reconstruction_max_abs':preservation,'unchanged_phase_and_temperature_metrics':True,
        'original_current_squared_error_fraction_near_known_knots':fraction,
        'known_knot_neighborhood_halfwidth':.02,'known_knots':knots.tolist(),
        'optimizer_updates':0,'new_observations':0,'PDE_solve':False,
        'interpretation':'factor the already known voltage envelope before PCHIP; retain raw temporal baselines and original four-arm adjudication; no blind confirmation claim'})
    np.savez_compressed(root/'local/waveform-traces.npz',time=reference.time,**traces)
    print(json.dumps({'waveform_diagnostic_complete':True,'metrics':record['metrics'],
                     'visible_voltage_reconstruction_max_abs':preservation,
                     'original_current_error_near_knots':fraction}),flush=True)


if __name__=='__main__': main()
