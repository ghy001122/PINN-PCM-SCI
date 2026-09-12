"""Three saved-node, sparse-only Adam diagnostics for the joint protocol.

These are prospective local directions, not executed additional updates or
proofs of a whole training trajectory's cause. Amplitude detachment is confined
to the analytic diagnostic; the training objectives remain fully coupled.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import torch

from .phk_v23_lf11 import ROOT, SparseData, PhysicsSampler, tensor, now, save_json
from .phk_v23_lf11_followup_fit import fit_model
from .phk_v23_lf11_diagnosis import flatten_gradient, decompose_adam
from .phk_v23_lf11_joint import RUN, batch_components
from .phk_v22r_pinn import interior_diagnostic_terms, boundary_residuals
from .phk_v22r_training import BOUNDARY_SCALES, PDE_SCALES


def amplitude_surrogates(model, config, cal, pb, bc_ic):
    """Gradient of these surrogates is exactly 2 r^2 grad(log sigma)."""
    lam, b = config['lambda_max'], max(cal['b_star'],1e-12)
    q, weight, mass = pb
    terms=interior_diagnostic_terms(model,tensor(q))
    electric=2*lam/(3*b)*torch.sum(tensor(mass*weight)[:,None]*
        (terms['electric_residual'].detach()/PDE_SCALES['electric']).square()*torch.log(terms['conductivity']))
    insulation=next(model.parameters()).new_zeros(())
    for window_mass,sides in zip(config['window_masses'],bc_ic[0],strict=True):
        by_side={side:boundary_residuals(model,tensor(q),side=side) for side,q in sides.items()}
        count=sum(len(v) for v in by_side.values())
        for side,residuals in by_side.items():
            for name,r in residuals.items():
                if 'insulating' not in name:
                    continue
                q=tensor(sides[side]); values=model(q)
                log_sigma=torch.log(model.physics.conductivity(values[:,1:2],values[:,2:3]))
                if side=='bottom':
                    log_sigma=log_sigma[q[:,0].abs()>model.physics.heater_half_width]
                insulation=insulation+2*lam*5*window_mass/(b*count)*torch.mean(
                    (r.detach()/BOUNDARY_SCALES[name]).square()*log_sigma)
    return {'electric':electric,'bc_insulation':insulation}


def visible_target_gradient(model,data,config,name):
    model.zero_grad(set_to_none=True)
    positive=data.coordinates[:,2]>model.physics.time_start
    if name in ('phase','phase_raw'):
        probability=data.prob*positive; probability=probability/probability.sum()
        if name=='phase' and data.has_interface:
            probability=.5*probability+.5*data.endpoint_prob/data.endpoint_prob.sum()
    else:
        probability=data.prob/data.prob.sum()
    total=0.
    for lo in range(0,len(data.coordinates),config['full_observation_chunk']):
        sl=slice(lo,lo+config['full_observation_chunk'])
        q,target=tensor(data.coordinates[sl]),tensor(data.targets[sl])
        d=model.read_only_output_diagnostics(q)
        if name=='phase':
            eps=config['phase_logit_epsilon']
            initial=model.physics.initial_phase(q).clamp(eps,1-eps)
            desired=torch.logit(target[:,2:3].clamp(eps,1-eps))-torch.logit(initial)
            startup=1-torch.exp(-(q[:,2:3]-model.physics.time_start)/model.startup_time)
            error=((model.phase_latent_scale*startup*d.latents['phase']-desired)/config['phase_logit_divisor']).ravel()
        else:
            col={'potential':0,'temperature':1,'phase_raw':2}[name]
            scale={'potential':model.physics.waveform_amplitude,'temperature':model.physics.theta_transition,'phase_raw':1.}[name]
            error=(d.output.fields[:,col]-target[:,col])/scale
        value=torch.dot(tensor(probability[sl]),error.square())
        value.backward(); total+=float(value.detach())
    gradient=torch.cat([(p.grad if p.grad is not None else torch.zeros_like(p)).reshape(-1) for p in model.parameters()])
    return gradient,total


def analyze(path,data):
    saved=torch.load(path,map_location='cpu',weights_only=False)
    cfg,cal=saved['config'],saved['calibration']
    model=fit_model(cfg,saved['model_state_dict'],saved['temperature_adapter'])
    params=list(model.parameters())
    rng=np.random.default_rng(); rng.bit_generator.state=saved['observation_rng_state']
    sampler=PhysicsSampler(data,cfg,cfg['sampling_seed'],model.physics)
    sampler.rng.bit_generator.state=saved['interior_rng_state']
    sampler.bc_rng.bit_generator.state=saved['boundary_rng_state']
    idx,ng=data.indices(rng,cfg['data_points'])
    pb,bc_ic=sampler.interior(False),sampler.boundary_initial()
    pieces,_=batch_components(model,data,cfg,cal,'P_U',saved['updates']+1,idx,ng,pb,bc_ic)
    raw={k:flatten_gradient(v,params) for k,v in pieces.items()}
    amp={k:flatten_gradient(v,params) for k,v in amplitude_surrogates(model,cfg,cal,pb,bc_ic).items()}
    separated={k:v for k,v in raw.items() if k not in amp}
    for key,value in amp.items():
        separated[key+'_amplitude']=value
        separated[key+'_shape']=raw[key]-value
    directions,total_direction,identity=decompose_adam(separated,saved['optimizer_state_dict'],cfg,params)
    identity['checkpoint_step']=saved['updates']
    identity['total_gradient_split_max_error']=float((sum(separated.values())-sum(raw.values())).abs().max())
    targets={}; target_values={}
    for target in ('potential','temperature','phase','phase_raw'):
        targets[target],target_values[target]=visible_target_gradient(model,data,cfg,target)
    slices={}; offset=0
    for name,p in model.named_parameters():
        head=name.split('.')[1]
        slices.setdefault(head,[]).append((offset,offset+p.numel())); offset+=p.numel()
    def norm(vector,ranges):
        return float(torch.sqrt(sum(vector[lo:hi].square().sum() for lo,hi in ranges)))
    def effect(gradient,direction,ranges):
        return float(sum(gradient[lo:hi]@direction[lo:hi] for lo,hi in ranges))
    rows=[]
    for source,direction in {**directions,'total_proposal':total_direction}.items():
        for head,ranges in slices.items():
            rows.append({'source':source,'head':head,
                         'raw_gradient_norm':norm(separated[source],ranges) if source in separated else None,
                         'adam_direction_norm':norm(direction,ranges),
                         'visible_directional_effect':{k:effect(g,direction,ranges) for k,g in targets.items()}})
    tests=[]; cond=cfg['conditional']
    for block in amp:
        for head in ('temperature','phase'):
            ranges=slices[head]
            denominator=norm(raw[block],ranges)
            ratio=norm(amp[block],ranges)/denominator if denominator>1e-24 else None
            d=effect(targets[head],directions[block+'_amplitude'],ranges)
            competing={k:effect(targets[head],directions[k],ranges) for k in ('bc_heater','bc_phase_no_flux')}
            competing_dominates=any(v>=d for v in competing.values()) if d>cond['directional_materiality_absolute'] else False
            supported=(ratio is not None and ratio>=cond['materiality_min_ratio'] and
                       d>cond['directional_materiality_absolute'] and not competing_dominates)
            g=raw[block]; t=targets[head]
            cosine=effect(g,t,ranges)/max(norm(g,ranges)*norm(t,ranges),1e-24)
            tests.append({'block':block,'head':head,'amplitude_to_full_gradient_norm':ratio,
                          'amplitude_effect_on_visible_head_error':d,'direct_BC_effects':competing,
                          'direct_BC_dominates':competing_dominates,'raw_gradient_cosine_with_visible_target':cosine,
                          'directional_channel_supported':bool(supported)})
    return {'step':saved['updates'],'identity':identity,'loss_components':{k:float(v.detach()) for k,v in pieces.items()},
            'visible_target_values':target_values,'rows':rows,'amplitude_tests':tests,
            'total_visible_effect':{k:float(g@total_direction) for k,g in targets.items()},
            'reference_read':False,'optimizer_updates_executed':0}


def analyze_node(root,step,data=None):
    root=Path(root)
    cfg=json.loads((root/'frozen-config.json').read_text())
    if step not in cfg['conditional']['nodes']:
        raise ValueError('only the three predeclared nodes may be diagnosed')
    destination=root/'diagnosis-nodes'/f'{step}.json'
    if destination.exists():
        record=json.loads(destination.read_text())
        if record['step']!=step:raise ValueError('cached node identity mismatch')
        return record
    torch.set_num_threads(cfg['cpu_threads'])
    data=data if data is not None else SparseData(ROOT/cfg['sparse'])
    path=root/'P_U'/f'adam-{step}.pt'
    record=analyze(path,data)
    record['source_checkpoint']=str(path.relative_to(root))
    record['computed_before_main_campaign_close']=not (root/'campaign.json').exists()
    destination.parent.mkdir(exist_ok=True)
    save_json(destination,record)
    print(json.dumps({'diagnosed_step':step,'amplitude_tests':record['amplitude_tests']}),flush=True)
    return record


def run(root=RUN):
    root=Path(root); output=root/'equation-head-diagnosis.json'
    if output.exists(): raise FileExistsError('reuse existing bounded diagnosis')
    cfg=json.loads((root/'frozen-config.json').read_text())
    torch.set_num_threads(cfg['cpu_threads'])
    data=SparseData(ROOT/cfg['sparse'])
    records=[]; missing=[]
    for step in cfg['conditional']['nodes']:
        path=root/'P_U'/f'adam-{step}.pt'
        if not path.exists(): missing.append(step); continue
        record=analyze_node(root,step,data); records.append(record)
    supported=None
    for record in records:
        present={(r['block'],r['head']) for r in record['amplitude_tests'] if r['directional_channel_supported']}
        supported=present if supported is None else supported & present
    result={'schema_id':'lf11-joint-three-node-amplitude-diagnosis-v1','recorded_utc':now(),
            'records':records,'missing_nodes':missing,'all_three_nodes_supported':bool(not missing and supported),
            'consistent_supported_channels':sorted(supported or []),
            'reference_read':False,'optimizer_updates_executed':0,
            'scope':'Exact prospective Adam algebra using saved states and next batches; local visible-target directions, not whole-path causality. All three nodes and final matched damage are required to trigger a conditional trial.'}
    save_json(output,result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--root',type=Path,default=RUN)
    p.add_argument('--node',type=int,choices=(500,1000,1500))
    args=p.parse_args()
    analyze_node(args.root,args.node) if args.node else run(args.root)
