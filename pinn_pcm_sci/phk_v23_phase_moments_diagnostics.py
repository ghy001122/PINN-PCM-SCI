"""Saved-array analysis and separately labeled zero-update checkpoint diagnostics."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import numpy as np
import torch
from .phk_v23_lf11 import ROOT, save_json
from .phk_v23_b1_metrics import interval_weights


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def saved_arrays(run):
    package=ROOT/'outputs/submission-rescore-20260921/b1'
    manifest=read(package/'run/readout-manifest.json')
    definitions=read(package/'reference-inputs/manifest.json')['protocols']['shorter']
    scored=read(package/'first-score/results.json')
    report=[];traces={};events={}
    for refname, path in definitions['references'].items():
        with np.load(package/'reference-inputs'/path,allow_pickle=False) as f:
            ref=f['phase']>=.5;times=f['time']
        wh=interval_weights(times,[(1.01,1.36)])
        wc=interval_weights(times,[(1.36,2.02)])
        ww=interval_weights(times,[(1.01,2.02)])
        np.testing.assert_allclose(wh+wc,ww,rtol=0,atol=1e-15)
        assert ref.shape==(1001,12800)
        traces[refname+'/reference_active']=ref.mean(1)
        for item in manifest['objects']:
            with np.load(package/item['prediction'],allow_pickle=False) as f:
                pred=f['phase']>=.5
                np.testing.assert_array_equal(times,f['time'])
            fn=np.mean(ref&~pred,axis=1);fp=np.mean(~ref&pred,axis=1)
            oid=item['id'];S=float(ww@(fn+fp)/ww.sum())
            np.testing.assert_allclose(S,scored['windows'][refname]['coarse'][oid]['window']['metrics']['S'],rtol=1e-13,atol=1e-15)
            row=dict(reference=refname,id=oid,S=S,
                heating_FN_integral=float(wh@fn),heating_FP_integral=float(wh@fp),
                subsequent_FN_integral=float(wc@fn),subsequent_FP_integral=float(wc@fp),
                W_FN_integral=float(ww@fn),W_FP_integral=float(ww@fp),W_duration=float(ww.sum()))
            np.testing.assert_allclose(sum(row[k] for k in ('heating_FN_integral','heating_FP_integral',
                'subsequent_FN_integral','subsequent_FP_integral')),S*ww.sum(),rtol=1e-13,atol=1e-15)
            report.append(row)
            for k,v in dict(FN=fn,FP=fp,predicted_active=pred.mean(1)).items():
                traces[refname+'/'+oid+'/'+k]=v
            old=scored['records'][refname]['coarse'][oid]
            events[refname+'/'+oid]={k:old[k] for k in ('cycles','strict_device_pass','event_failures')}
    with (run/'saved-array-decomposition.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(report[0]));writer.writeheader();writer.writerows(report)
    np.savez_compressed(run/'saved-array-traces.npz',time=times,**traces)
    save_json(run/'saved-array-events.json',dict(source='existing first-score/results.json; no event redefinition',records=events))
    save_json(run/'saved-array-analysis.json',dict(status='VERIFIED_SAVED_ARRAY_POSTHOC',rows=report,
        full_spatial_cells=12800,phase_threshold=.5,contributions='unnormalized time integrals; common node split between trapezoids',
        new_field_evaluations=0,new_electrical_solves=0))
    print(json.dumps(dict(stage='saved_arrays',records=len(report),status='VERIFIED')))


def checkpoints(run, cfg):
    from .phk_v23_lf11_followup_fit import fit_model
    from .phk_v23_lf11_elimination_physics import fields,grid_for
    from .phk_v23_phase_moments import phase_quantities
    from .phk_v23_b1_observations import VisibleData,VisibleTimes
    from .phk_v23_phase_moments_run import parent_model
    torch.set_num_threads(cfg['cpu_threads'])
    model,_=parent_model(cfg);grid=grid_for(model.physics,*cfg['grid'])
    panels=read(run/'phase-calibration-pool.json')
    # The diagnostic does not choose quadrature or train; use the predeclared high order.
    order=32;xi,w=np.polynomial.legendre.leggauss(order);xi=(xi+1)/2;w=w/2
    sources={'parent29':ROOT/cfg['parent'],'old_E29':ROOT/cfg['source_b1']/'E/checkpoint.pt',
             'old_D_E29':ROOT/cfg['source_b1']/'D_E/checkpoint.pt'}
    data=VisibleData(ROOT/cfg['sparse']);delta=cfg['phase_logit_epsilon'];records={}
    for label,source in sources.items():
        state=torch.load(source,map_location='cpu',weights_only=False)['model_state_dict']
        model=fit_model(cfg,state,adapter=True)
        for p in model.parameters():p.requires_grad_(False)
        arrays={}
        for panel in panels:
            cells=np.asarray(panel['cells']);q=np.empty((len(cells),order,3))
            q[...,0]=grid.cell_x[cells,None];q[...,1]=grid.cell_z[cells,None]
            q[...,2]=panel['a']+(panel['b']-panel['a'])*xi
            qt=torch.tensor(q.reshape(-1,3),dtype=torch.float64,requires_grad=True)
            result=phase_quantities(model,qt,delta)
            result['weight']=qt.new_tensor(np.broadcast_to(w,(len(cells),order)).ravel()*panel['mass']/len(cells))
            result['time']=qt[:,2]
            for k,v in result.items():
                arrays.setdefault(k,[]).append(v.detach().numpy())
        arrays={k:np.concatenate(v) for k,v in arrays.items()}
        phi=arrays['phi'];weight=arrays['weight'];pure=(phi<.01)|(phi>.99)
        deep=(phi<delta)|(phi>1-delta)
        parts={}
        for k in ('rphi','rpsi','rzeta'):
            energy=weight*arrays[k]**2;total=energy.sum()
            parts[k]=dict(weighted_square=float(total),near_pure_share=float(energy[pure].sum()/total),
                          transition_share=float(energy[~pure].sum()/total),below_clip_share=float(energy[deep].sum()/total))
        temporal=[]
        for lo,hi in cfg['windows']:
            mask=(arrays['time']>=lo)&(arrays['time']<hi)
            mass=float(weight[mask].sum())
            temporal.append(dict(interval=[lo,hi],sample_mass=mass,
                residual_square_contribution={k:float(np.sum(weight[mask]*arrays[k][mask]**2)) for k in ('rphi','rpsi','rzeta')}))
        for k in ('rphi','rpsi','rzeta'):
            np.testing.assert_allclose(sum(row['residual_square_contribution'][k] for row in temporal),
                                       parts[k]['weighted_square'],rtol=2e-13,atol=1e-14)
        obs=VisibleTimes(data,grid,model.physics,cfg,'cpu')
        ind=data.arrays['phase_indices'];vals=data.arrays['phase_values']
        clipped=(vals<delta)|(vals>1-delta);label_loss=np.zeros(len(vals))
        for start in range(0,len(ind),2048):
            select=ind[start:start+2048];q=torch.tensor(data.coordinates[select],dtype=torch.float64)
            with torch.no_grad():
                f=fields(model,q)
                initial=model.physics.initial_phase(q).clamp(delta,1-delta).ravel()
                target=torch.logit(torch.tensor(vals[start:start+2048]).clamp(delta,1-delta))-torch.logit(initial)
                label_loss[start:start+2048]=((f['delta_logit']-target)/cfg['phase_logit_divisor']).square().numpy()
        ow=obs.phase_weight.ravel()[ind];contribution=ow*label_loss/3
        stats=dict(source=str(source.relative_to(ROOT)),sample_count=len(phi),quadrature_order=order,
            near_pure_definition='phi < 0.01 or phi > 0.99; diagnostic only',
            empirical_unweighted_quantiles={k:np.quantile(arrays[k],[0,.01,.1,.5,.9,.99,1]).tolist() for k in ('s','psi','attenuation')},
            nonfinite={k:int(np.count_nonzero(~np.isfinite(v))) for k,v in arrays.items()},
            rounded_zero_count=int((phi==0).sum()),rounded_one_count=int((phi==1).sum()),
            weighted_near_pure_mass=float(weight[pure].sum()),weighted_below_clip_mass=float(weight[deep].sum()),
            residual_distribution=parts,
            residual_distribution_by_physics_window=temporal,
            derivative_rms={k:np.sqrt((weight[:,None]*arrays[k]**2).sum(0)).tolist() for k in ('dphi','dpsi')},
            visible_clip=dict(count=int(clipped.sum()),total=len(vals),fraction=float(clipped.mean()),
                below_count=int((vals<delta).sum()),above_count=int((vals>1-delta).sum()),
                below_fraction=float((vals<delta).mean()),above_fraction=float((vals>1-delta).mean()),
                includes_analytic_initial_labels=True,
                phase_weight_mass=float(ow[clipped].sum()),loss_from_clipped_labels=float(contribution[clipped].sum()),
                total_phase_observation_loss=float(contribution.sum()),
                fraction_of_phase_loss=float(contribution[clipped].sum()/contribution.sum()),
                meaning='numerical target clipping, not observation noise'),
            optimizer_updates=0,electrical_solves=0,reference_read=False)
        records[label]=stats
        save_json(run/f'diagnostic-{label}.json',stats)
        print(json.dumps(dict(stage='checkpoint_diagnostic',model=label,parts=parts)),flush=True)
    save_json(run/'checkpoint-diagnostics.json',dict(status='VERIFIED_ZERO_UPDATE_DIAGNOSTICS',records=records))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('arrays','checkpoints'))
    p.add_argument('--config',type=Path,default=ROOT/'configs/phk_v23/phase_moments_20260923.json')
    a=p.parse_args();cfg=read(a.config);run=ROOT/cfg['run'];run.mkdir(parents=True,exist_ok=True)
    if a.action=='arrays':saved_arrays(run)
    else:checkpoints(run,cfg)


if __name__=='__main__':main()
