"""One local, post-screen equation-by-head Adam direction diagnosis for LF11.

No optimizer step is performed. Real saved moments condition a hypothetical
next proposal; the decomposition uses one common total-gradient denominator.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import torch

from .phk_benchmark import PhkControl
from .phk_v22r_evaluator import load_reference, _physical_contract
from .phk_v23_lf11 import (SparseData, PhysicsSampler, build_model, tensor, pde_terms,
                          boundary_initial_loss, save_json, now)


def flatten_gradient(value, params, retain_graph=True):
    if not value.requires_grad:
        return torch.zeros(sum(p.numel() for p in params),dtype=torch.float64)
    gs=torch.autograd.grad(value,params,retain_graph=retain_graph,allow_unused=True)
    return torch.cat([(g if g is not None else torch.zeros_like(p)).reshape(-1) for p,g in zip(params,gs)])


def decompose_adam(gradients, state_dict, config, params, fresh=False):
    """Exact algebra for one prospective Adam step, including global clipping."""
    total=sum(gradients.values())
    clip=min(1.,config['gradient_clip']/(float(total.norm())+1e-6))
    gc=clip*total
    states=state_dict['state']
    ids=state_dict['param_groups'][0]['params']
    beta1,beta2=config['betas']
    old_m=[];old_v=[];steps=[]
    for identifier,param in zip(ids,params,strict=True):
        s={} if fresh else states.get(identifier,{})
        old_m.append(s.get('exp_avg',torch.zeros_like(param)).reshape(-1))
        old_v.append(s.get('exp_avg_sq',torch.zeros_like(param)).reshape(-1))
        steps.append(int(s.get('step',0)))
    if len(set(steps))!=1: raise ValueError('unequal per-parameter Adam clocks need explicit handling')
    step=steps[0]+1
    old_m,old_v=torch.cat(old_m),torch.cat(old_v)
    v=beta2*old_v+(1-beta2)*gc.square()
    denominator=(v/(1-beta2**step)).sqrt()+config['eps']
    coefficient=-config['branch_lr']/((1-beta1**step)*denominator)
    directions={k:coefficient*(1-beta1)*clip*g for k,g in gradients.items()}
    directions['historical_momentum']=coefficient*beta1*old_m
    actual=coefficient*(beta1*old_m+(1-beta1)*gc)
    mismatch=float((sum(directions.values())-actual).abs().max())
    return directions,actual,{'proposal_step':step,'global_clip_coefficient':clip,
        'total_gradient_norm_before_clip':float(total.norm()),'decomposition_max_abs_error':mismatch,
        'optimizer_moments':'fresh as in the four-arm launch' if fresh else 'actual saved endpoint moments',
        'shared_denominator':True,'executed_optimizer_updates':0}


def reference_probes(reference, physics):
    """Fixed nominal diagnostic samples, never training or formal metric replacements."""
    grid=reference.grid; time=reference.time
    rng=np.random.default_rng(80117)
    event=_physical_contract().payload['qualification_event']['roi']
    roi=(np.abs(grid.cell_x)<=event['abs_x_max'])&(grid.cell_z>=event['z_min'])&(grid.cell_z<=event['z_max'])
    queries={}
    for kind in ('global','roi'):
        ti=rng.integers(0,len(time),4096)
        cells=rng.choice(np.flatnonzero(roi) if kind=='roi' else np.arange(grid.cell_count),len(ti))
        q=np.column_stack((grid.cell_x[cells],grid.cell_z[cells],time[ti]))
        target=np.column_stack([getattr(reference,k)[ti,cells] for k in ('potential','temperature','phase')])
        queries[kind]=(tensor(q),tensor(target))
    indices=np.unique(np.linspace(0,len(time)-1,64,dtype=int))
    ti=np.repeat(indices,grid.nx)
    cells=np.tile(np.arange((grid.nz-1)*grid.nx,grid.cell_count),len(indices))
    queries['current']=(tensor(np.column_stack((grid.cell_x[cells],grid.cell_z[cells],time[ti]))),
                        tensor(reference.top_current[indices]),tensor(time[indices]),grid)
    return queries


def diagnostic_objectives(model, probes):
    global_q,global_target=probes['global']
    roi_q,roi_target=probes['roi']
    gp=model(global_q); rp=model(roi_q)
    result={
        'EV_squared':(gp[:,0]-global_target[:,0]).square().mean(),
        'ET_squared':((rp[:,1]-roi_target[:,1])/.45).square().mean(),
        'Ephi_squared':(rp[:,2]-roi_target[:,2]).square().mean(),
        'soft_event_mse':(torch.sigmoid((gp[:,2]-.5)/.05)-(global_target[:,2]>=.5).double()).square().mean(),
    }
    q,target,times,grid=probes['current']
    values=model(q).reshape(len(times),grid.nx,3)
    p=model.physics
    sigma=torch.exp(p.conductivity_temperature_gain*values[...,1]+np.log(p.conductivity_phase_ratio)*values[...,2]**2*(3-2*values[...,2]))
    current=(sigma*grid.dx/(.5*grid.dz)*(p.waveform(times)[:,None]-values[...,0])).sum(dim=1)
    result['EI_squared']=torch.trapezoid((current-target).square(),times)/torch.trapezoid(target.square(),times).clamp_min(1e-24)
    return result


def analyze_checkpoint(path, data, config, cal, probes, warm=False):
    checkpoint=torch.load(path,map_location='cpu',weights_only=False)
    model=build_model(config)
    model.load_state_dict(checkpoint['model_state_dict'])
    params=list(model.parameters())
    role='P_U' if warm else checkpoint['role']
    step=1 if warm else checkpoint['updates']+1
    # Regenerate the exact next batch in this role's frozen stochastic stream.
    rng=np.random.default_rng(60117)
    sampler=PhysicsSampler(data,config,60217,model.physics)
    for _ in range(step):
        idx,ng=data.indices(rng,config['data_points'])
        pb=sampler.interior(role in ('P_I','P_M')) if role!='D_B' else None
        bc_ic=sampler.boundary_initial()
    obs=data.loss(model,idx,ng,config,'cpu')['observation']
    bc,ic=boundary_initial_loss(model,*bc_ic,config,'cpu')
    lam=config['lambda_max']*min(step/config['lambda_ramp'],1)
    pieces={'observation':obs/max(cal['a0'],1e-12),
            'boundary':lam*5*bc/max(cal['b0'],1e-12),'initial':lam*ic/max(cal['b0'],1e-12)}
    if role!='D_B':
        terms,pq=pde_terms(model,pb,'cpu')
        if role=='P_M': terms['phase']=cal['c0']*pq
        pieces.update({k:lam*v/(3*max(cal['b0'],1e-12)) for k,v in terms.items()})
    gradients={k:flatten_gradient(v,params) for k,v in pieces.items()}
    directions,actual,identity=decompose_adam(gradients,checkpoint['optimizer_state_dict'],config,params,fresh=warm)
    objectives=diagnostic_objectives(model,probes)
    target_gradients={k:flatten_gradient(v,params) for k,v in objectives.items()}
    target_values={k:float(v.detach()) for k,v in objectives.items()}
    slices={};offset=0
    for name,param in model.named_parameters():
        head=name.split('.')[1]
        slices.setdefault(head,[]).append((offset,offset+param.numel()))
        offset+=param.numel()
    rows=[]
    for source,direction in directions.items():
        for head,ranges in slices.items():
            row={'equation':source,'head':head,
                 'raw_gradient_norm':float(torch.sqrt(sum(gradients[source][lo:hi].square().sum() for lo,hi in ranges))) if source in gradients else None,
                 'adam_direction_norm':float(torch.sqrt(sum(direction[lo:hi].square().sum() for lo,hi in ranges))),
                 'directional_effect':{k:float(sum(g[lo:hi]@direction[lo:hi] for lo,hi in ranges)) for k,g in target_gradients.items()}}
            row['relative_first_order_rms_effect']={k:.5*v/max(target_values[k],1e-18) for k,v in row['directional_effect'].items() if k!='soft_event_mse'}
            rows.append(row)
    return {'role':'common_parent_fresh_P_U' if warm else role,'checkpoint_updates':checkpoint['updates'],
            'identity':identity,'loss_components':{k:float(v.detach()) for k,v in pieces.items()},
            'diagnostic_metric_squared':target_values,'rows':rows,
            'total_directional_effect':{k:float(g@actual) for k,g in target_gradients.items()}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args()
    torch.set_num_threads(2)
    root=args.root
    evaluation=json.loads((root/'local/results.json').read_text())
    if evaluation['outcome']['positive_matched_pairs']:
        raise ValueError('negative-path diagnosis not triggered; follow the positive attribution branch')
    output=root/'local/equation-head-diagnosis.json'
    if output.exists(): raise FileExistsError('bounded diagnosis already exists; do not repeat it')
    config=json.loads((root/'formal/frozen_config.json').read_text())
    cal=json.loads((root/'formal/calibration.json').read_text())
    reference,_=load_reference(PhkControl.FULL)
    probes=reference_probes(reference,build_model(config).physics)
    data=SparseData(root/'input/sparse.npz')
    records=[]
    for role in ('warm_start','D_B','P_U','P_I','P_M'):
        path=root/'formal'/role/'checkpoint.pt'
        if not path.exists(): continue
        record=analyze_checkpoint(path,data,config,cal,probes,warm=role=='warm_start')
        records.append(record)
        print(json.dumps({'diagnosis_completed':record['role'],'identity':record['identity'],
                          'total_directional_effect':record['total_directional_effect']}),flush=True)
    save_json(output,{'schema_id':'lf11-one-equation-by-head-diagnosis-v1','recorded_utc':now(),
        'status':'LOCAL_DIRECTIONAL_EVIDENCE_NOT_LONG_TERM_CAUSAL_PROOF','records':records,
        'optimizer_updates':0,'reference_access':'local nominal only after formal screen and cloud closure',
        'probe_scope':'4096 fixed samples per spatial scope; 64 fixed current times; no formal metric replacement',
        'interpretation':'positive directional effect means locally increasing that error; history is separated, not assigned to a current residual equation'})


if __name__=='__main__': main()
