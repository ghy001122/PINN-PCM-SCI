"""Separated numerical and post-lock development-reference evaluation.

The numerical entry never opens reference arrays. The reference entry requires
both a trajectory lock and the prospective numerical gate; no model is queried.
"""
from __future__ import annotations
import argparse
import csv
from pathlib import Path
import time
import numpy as np
from .phk_benchmark import PhkGrid,_mobility,_phase_free_energy_derivatives
from .phk_v23_conditional_phase import (phase_rhs,phase_jet,common_derivative,time_weights,
    mean_square,thermal_decision,reference_direction)
from .phk_v23_conditional_phase_run import ROOT,CONFIG,read,save,now,Resources,digest
from .phk_v23_spatial_comparison import CellRestriction


def csv_write(path,rows):
    with Path(path).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def metric_vector(value,grid,scale=1.):
    v=np.asarray(value);k=int(np.argmax(np.abs(v)))
    return dict(rms=float(np.sqrt(np.average(v*v,weights=grid.cell_volumes))),
                max_absolute=float(np.abs(v[k])),max_cell=k,x=float(grid.cell_x[k]),z=float(grid.cell_z[k]),
                scaled_rms=float(scale*np.sqrt(np.average(v*v,weights=grid.cell_volumes))),
                scaled_max_absolute=float(scale*np.abs(v[k])))


def numerical(cfg,out):
    if (out/'numerical-evaluation.json').exists():raise FileExistsError('Numerical evaluation already exists')
    started=time.perf_counter();resources=Resources(cfg,'cpu')
    if not (out/'trajectories-locked.json').exists():
        result=dict(status='NUMERICAL_UNRESOLVED',numerical_qualification_passed=False,reference_read=False,
                    reason='Both complete locked trajectories are unavailable',
                    execution_stop=read(out/'run-stop.json') if (out/'run-stop.json').exists() else None,utc=now())
        save(out/'numerical-evaluation.json',result);save(out/'result.json',result);return result
    p=read(out/'physics.json');g=PhkGrid.build(nx=80,nz=40,**{k:p[k] for k in ('x_min','x_max','z_min','z_max')})
    c=out/'cache';t=np.load(c/'time_common.npy');w=time_weights(t);volume=g.cell_volumes/g.cell_volumes.sum()
    T=np.load(c/'temperature_fine.npy',mmap_mode='r')[::2]
    Tt=np.load(c/'temperature_t_AD.npy',mmap_mode='r');flux=np.load(c/'thermal_flux.npy',mmap_mode='r')
    base_dt=np.load(c/'B0_phase_t_AD.npy',mmap_mode='r')
    fields={'B0':np.load(c/'B0_phase.npy',mmap_mode='r'),
        'coarse':np.load(out/'coarse/phase.npy',mmap_mode='r'),
        'fine':np.load(out/'fine/phase.npy',mmap_mode='r')[::2]}
    common_temp=Tt+p['volumetric_cooling']*T-p['thermal_diffusivity']*flux
    summaries={};traces=[];rhss={}
    for label,phi in fields.items():
        resources.check();rhs=np.stack([phase_rhs(phi[k],T[k],g,p) for k in range(len(t))]);rhss[label]=rhs
        diff=common_derivative(phi,cfg['dt'][0]);residual=diff-rhs
        primary=common_temp+p['latent_ratio']*(base_dt if label=='B0' else rhs)
        cross=common_temp+p['latent_ratio']*diff
        summaries[label]=dict(phase_common_MS=mean_square(residual,t,g.cell_volumes),
            thermal_conditional_semidiscrete_MS=mean_square(primary,t,g.cell_volumes),
            thermal_common_fd_MS=mean_square(cross,t,g.cell_volumes),
            phase_min=float(phi.min()),phase_max=float(phi.max()),
            neural_AD_strong_residual='endpoint only' if label=='B0' else 'NOT_APPLICABLE')
        for k,tk in enumerate(t):
            traces.append(dict(state=label,time=float(tk),weight=float(w[k]),
                phase_common_MS=float(volume@(residual[k]**2)),thermal_conditional_semidiscrete_MS=float(volume@(primary[k]**2)),
                thermal_common_fd_MS=float(volume@(cross[k]**2))))
    csv_write(out/'common-components.csv',traces)
    save(out/'common-metrics.json',dict(measure=cfg['measure'],time_count=len(t),cell_count=g.cell_count,
        derivative=cfg['common_derivative'],state_metrics=summaries,
        AD_note='No conditional neural AD residual is constructed; common residual uses independent finite differences, not RHS minus itself.'))
    decisions={q:thermal_decision(*[summaries[label]['thermal_'+q+'_MS'] for label in ('B0','coarse','fine')])
               for q in ('conditional_semidiscrete','common_fd')}
    delta=fields['coarse'][::4]-fields['fine'][::4]
    rms=float(np.sqrt(mean_square(delta,t[::4],g.cell_volumes)));end=float(np.max(np.abs(delta[-1])))
    thermal_delta=decisions['conditional_semidiscrete']['observed_step_difference']
    threshold=cfg['numerical_qualification'];heat_limit=threshold['thermal_difference_fraction']*max(decisions['conditional_semidiscrete']['base'],1e-12)
    passed=bool(rms<=threshold['phase_RMS'] and end<=threshold['endpoint_max_absolute'] and thermal_delta<=heat_limit)
    qualification=dict(phase_difference_RMS=rms,phase_RMS_limit=threshold['phase_RMS'],endpoint_max_absolute=end,
        endpoint_limit=threshold['endpoint_max_absolute'],primary_thermal_difference=thermal_delta,primary_thermal_difference_limit=heat_limit,
        phase_RMS_pass=rms<=threshold['phase_RMS'],endpoint_pass=end<=threshold['endpoint_max_absolute'],
        primary_thermal_pass=thermal_delta<=heat_limit,passed=passed,
        interpretation='Finite two-time-step consistency only; no spatial/continuum convergence or order claim')
    jets=np.load(c/'endpoint-AD.npz');vectors={};seams={};seam_rows=[];L=cfg['interval'][1]-cfg['interval'][0]
    for label in ('coarse','fine'):
        seams[label]={}
        for side,k in [('left',0),('right',-1)]:
            phi=fields[label][k];velocity,acceleration=phase_jet(phi,T[k],Tt[k],g,p)
            errors=(phi-jets[side+'_phase'],velocity-jets[side+'_phase_t'],acceleration-jets[side+'_phase_tt'])
            seams[label][side]={}
            for order,value in enumerate(errors):
                vectors[f'{label}_{side}_order{order}']=value
                stats=metric_vector(value,g,L**order);seams[label][side][str(order)]=stats
                seam_rows.append(dict(state=label,side=side,order=order,**stats))
    same_left={str(order):float(np.max(np.abs(vectors[f'coarse_left_order{order}']-vectors[f'fine_left_order{order}']))) for order in (0,1,2)}
    m=_mobility(T[0],p);first,_=_phase_free_energy_derivatives(fields['B0'][0],T[0],barrier=p['barrier_scale'],thermal_drive=p['thermal_drive'],transition_temperature=p['theta_transition'])
    raw_ad=jets['left_phase_t']-m*(p['interface_width']**2*jets['left_phase_laplacian_AD']-first)
    spatial=m*p['interface_width']**2*(g.phase_laplacian@fields['B0'][0]-jets['left_phase_laplacian_AD'])
    identity=vectors['coarse_left_order1']-(spatial-raw_ad)
    vectors.update(left_spatial_operator_difference=spatial,left_B0_AD_phase_residual=raw_ad,left_decomposition_error=identity)
    csv_write(out/'endpoint-seams.csv',seam_rows);np.savez_compressed(out/'endpoint-seam-vectors.npz',**vectors)
    normals=np.load(c/'B0_boundary_normal_AD.npy',mmap_mode='r');counts=[g.nz,g.nz,g.nx,g.nx];offset=0;boundary={}
    for side,count in zip(('left','right','bottom','top'),counts):
        arr=normals[:,offset:offset+count];boundary[side]=dict(B0_AD_normal_MS=float(w@np.mean(arr*arr,axis=1)),B0_AD_max_absolute=float(np.max(np.abs(arr))),face_count=count,
             IVP_discrete_boundary_flux=0.,interpretation='zero flux is imposed by the discrete operator; not the same layer as neural AD BC')
        offset+=count
    result=dict(status='NUMERICALLY_QUALIFIED_PENDING_REFERENCE' if passed else 'NUMERICAL_UNRESOLVED',
        numerical_qualification_passed=passed,qualification=qualification,thermal=decisions,seams=seams,boundaries=boundary,
        left_step_difference=same_left,left_decomposition=metric_vector(identity,g),
        left_structural_note='Identical left input makes RHS jets identical across dt. Nonzero mismatch to B0 is structural for this semidiscrete IVP, not temporal error; zero inter-dt difference is not proof of physical compatibility.',
        reference_read=False,seconds=time.perf_counter()-started,resources=resources.record(),utc=now())
    save(out/'numerical-evaluation.json',result)
    if not passed:save(out/'result.json',result)
    print('NUMERICAL_QUALIFICATION',passed,qualification,flush=True)
    return result


def score_reference(cfg,out):
    if (out/'reference-evaluation.json').exists():raise FileExistsError('Reference evaluation already complete')
    if not (out/'trajectories-locked.json').exists():raise RuntimeError('Trajectory lock missing')
    numerical_result=read(out/'numerical-evaluation.json')
    if numerical_result['numerical_qualification_passed'] is not True:raise RuntimeError('Reference access forbidden: numerical gate not passed')
    started=time.perf_counter();resources=Resources(cfg,'cpu');resources.check()
    c=out/'cache';t=np.load(c/'time_common.npy')[::4];grid=np.load(c/'grid.npz');volumes=grid['volumes'];w=time_weights(t)
    fields={'B0':np.load(c/'B0_phase.npy',mmap_mode='r')[::4],
            'coarse':np.load(out/'coarse/phase.npy',mmap_mode='r')[::4],
            'fine':np.load(out/'fine/phase.npy',mmap_mode='r')[::8]}
    path=ROOT/cfg['reference']
    save(out/'reference-access.json',dict(utc=now(),reason='Locked trajectories and numerical qualification passed',path=cfg['reference'],use='post-lock development only'))
    with np.load(path,allow_pickle=False) as f:
        rt=f['time'];idx=np.rint(t/.0025).astype(int);np.testing.assert_allclose(rt[idx],t,atol=2e-12,rtol=0)
        native=f['phase'][idx]
    op=CellRestriction(160,80,80,40);truth=op(native);native_active=op((native>=.5).astype(float));del native
    restricted_active=(truth>=.5).astype(float)
    masks={'full':np.ones(len(volumes),dtype=bool),
           'roi':(np.abs(grid['x'])<=cfg['roi']['abs_x_max'])&(grid['z']>=cfg['roi']['z_min'])&(grid['z']<=cfg['roi']['z_max'])}
    records={};traces=[]
    for scope,mask in masks.items():
        v=volumes[mask];v=v/v.sum();records[scope]={}
        for label,phi in fields.items():
            error=phi[:,mask]-truth[:,mask]
            E=float(np.sqrt(w@(error*error@v)))
            records[scope][label]=dict(Ephi_D_80=E,cells=int(mask.sum()))
            for k,tk in enumerate(t):
                traces.append(dict(scope=scope,state=label,time=float(tk),weight=float(w[k]),phase_MSE=float(error[k]**2@v),
                    predicted_active_fraction=float((phi[k,mask]>=.5)@v),
                    reference_restricted_native_indicator_fraction=float(native_active[k,mask]@v),
                    reference_threshold_after_restriction_fraction=float(restricted_active[k,mask]@v)))
        records[scope]['direction']=reference_direction(*[records[scope][label]['Ephi_D_80'] for label in ('B0','coarse','fine')])
    heat_dirs=[v['direction'] for v in numerical_result['thermal'].values()];ref_dirs=[r['direction']['direction'] for r in records.values()]
    if all(v=='WITHIN_BUDGET' for v in heat_dirs) and all(v=='IMPROVES' for v in ref_dirs):
        status='CONDITIONAL_IVP_SUPPORTS_FURTHER_WITNESS_SEARCH'
        reason='Both thermal conventions and both reference scopes give resolved favorable evidence; original-family seam accommodation remains unproved.'
    elif all(v=='EXCEEDS_BUDGET' for v in heat_dirs) and all(v=='WORSENS' for v in ref_dirs):
        status='CONDITIONAL_IVP_MISMATCH';reason='Both thermal conventions and both reference scopes give resolved adverse evidence for this conditional IVP.'
    else:
        status='CONDITIONAL_IVP_FEASIBILITY_UNKNOWN';reason='Evidence is mixed or unresolved; no scalar total score or seam tolerance is invented.'
    csv_write(out/'reference-traces.csv',traces)
    np.savez_compressed(out/'reference-diagnostic-265.npz',time=t,phase_restricted=truth,
        restricted_native_indicator=native_active,threshold_after_restriction=restricted_active)
    reference=dict(reference=cfg['reference'],reference_sha256=digest(path),reference_read=True,utc=now(),
        grid=[80,40],interval=cfg['interval'],time_count=len(t),records=records,seconds=time.perf_counter()-started,
        formal_A_w=False,formal_ood=False,interpretation='Observed step differences are sensitivity indicators, not true-error bounds or confidence intervals')
    save(out/'reference-evaluation.json',reference)
    result={**numerical_result,'status':status,'recommendation_status':'SUPPORTED_INTERPRETATION',
            'reference_read':True,'reference':reference,'recommendation_reason':reason,
            'original_C2_family_feasibility':'UNKNOWN','additional_runs_authorized':False,'new_training_updates':0,'utc':now()}
    save(out/'result.json',result);print(status,records,flush=True)
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=('numerical','reference'));p.add_argument('--config',type=Path,default=CONFIG)
    a=p.parse_args();cfg=read(a.config);out=ROOT/cfg['run']
    (numerical if a.mode=='numerical' else score_reference)(cfg,out)

if __name__=='__main__':main()
