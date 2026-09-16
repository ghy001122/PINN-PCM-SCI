"""Conditionally authorized V31 clean pairs. No historical weights or references.

The locked soft configuration is selected by Stage A outside this module.
All fitting is on already visible observations, without a new qualification gate.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import numpy as np
import torch
from .phk_v23_lf11 import ROOT,SparseData,save_json,now
from .phk_v23_lf11_fullgrid import CONFIG
from .phk_v23_lf11_training_coupling import read,SoftExperiment,train,gradient_vector,BLOCKS
from .phk_v23_lf11_followup_fit import fit_model,head_field
from .phk_v23_lf11_v_continue import continued_lbfgs
from .phk_v23_lf11_elimination import Experiment,ObservationTimes,TimeSampler,serialize_pool,deserialize_pool,train_role
from .phk_v23_lf11_elimination_physics import grid_for

RUN=ROOT/'outputs/runs/20260914-lf11-clean-confirmation'


class BoundedElectricExperiment(Experiment):
    def electric(self,t,needed):
        u=float(self.model.physics.waveform(torch.tensor(t,dtype=torch.float64,device=self.device)))
        if needed and u!=0. and self.layer.backend.counts.forward_solves>=self.c['per_E_forward_limit']:
            raise RuntimeError('predeclared E forward-solve limit reached before next solve')
        return super().electric(t,needed)


def observation_objective(model,obs,groups,head=None,backward=False):
    total=0.;parts={k:0. for k in ('obs_V','obs_T','obs_phase')}
    key={'potential':'obs_V','temperature':'obs_T','phase':'obs_phase'}.get(head)
    for group in groups.values():
        combined,pieces=obs.loss(model,group,None,'P_F')
        loss=pieces[key]/3 if head else combined
        if backward:loss.backward()
        total+=float(loss.detach())
        for k,v in pieces.items():parts[k]+=float(v.detach())
    return torch.tensor(total,dtype=torch.float64,device=obs.device),parts


def full_observation_head(model,obs,head,backward=True,chunk=4096):
    """Exact complete head target in chunks, avoiding unrelated head forwards."""
    q=obs.q.reshape(-1,3);target=obs.target.reshape(-1,3)
    weight=(obs.phase_weight if head=='phase' else obs.global_weight).reshape(-1)
    total=torch.zeros((),dtype=torch.float64,device=obs.device)
    for lo in range(0,len(q),chunk):
        coords=obs.tensor(q[lo:lo+chunk]);values=obs.tensor(target[lo:lo+chunk]);mass=obs.tensor(weight[lo:lo+chunk])
        if head=='phase':
            normalized=model.physics.normalize(coords)
            latent=model.heads['phase'](model.encoders['phase'](normalized)).ravel()
            startup=1-torch.exp(-(coords[:,2]-model.physics.time_start)/model.startup_time)
            initial=model.physics.initial_phase(coords).reshape(-1).clamp(obs.config['phase_logit_epsilon'],1-obs.config['phase_logit_epsilon'])
            desired=torch.logit(values[:,2].clamp(obs.config['phase_logit_epsilon'],1-obs.config['phase_logit_epsilon']))-torch.logit(initial)
            error=(model.phase_latent_scale*startup*latent-desired)/obs.config['phase_logit_divisor']
        else:
            col,scale=(0,model.physics.waveform_amplitude) if head=='potential' else (1,model.physics.theta_transition)
            error=(head_field(model,head,coords)-values[:,col])/scale
        loss=torch.dot(mass,error.square())/3
        if backward:loss.backward()
        total+=loss.detach()
    return total


def fit_parent(folder,cfg,device):
    """One fresh zero-adapter parent; no imported trained state is accepted."""
    folder.mkdir(parents=True,exist_ok=False)
    model=fit_model(cfg,adapter=True).to(device)
    adapter=model.heads['temperature'].residual.output
    assert torch.count_nonzero(adapter.weight)==0 and torch.count_nonzero(adapter.bias)==0
    obs=ObservationTimes(SparseData(ROOT/cfg['sparse']),grid_for(model.physics,*cfg['grid']),model.physics,cfg,device)
    plan=cfg['confirmation'];parameters=list(model.parameters())
    torch.save(dict(model_state_dict=model.state_dict(),seed=cfg['seed'],temperature_adapter=True,
        loaded_trained_weights=False,adapter_zero_output=True,optimizer_updates=0),folder/'initial.pt')
    rng=np.random.default_rng(61100+cfg['seed'])
    adam=torch.optim.Adam(parameters,lr=plan['parent_lr'],betas=tuple(cfg['betas']),eps=cfg['eps'])
    used=0;history={}
    with (folder/'fit-telemetry.jsonl').open('x',encoding='utf-8') as log:
        def record(obj):
            log.write(json.dumps(obj,allow_nan=False)+'\n');log.flush()
            print(json.dumps(dict(seed=cfg['seed'],fit=obj)),flush=True)
        with torch.no_grad():
            initial_loss,initial_parts=observation_objective(model,obs,obs.groups())
        for step in range(1,plan['parent_adam']+1):
            adam.zero_grad(set_to_none=True)
            value,parts=observation_objective(model,obs,obs.groups(rng,plan['parent_observation_times']),backward=True)
            torch.nn.utils.clip_grad_norm_(parameters,cfg['gradient_clip'],error_if_nonfinite=True)
            adam.step()
            if not all(torch.isfinite(p).all() for p in parameters):raise FloatingPointError('illegal observation fit')
            if step==1 or step%200==0:record(dict(stage='Adam',step=step,loss=float(value),components=parts))
        torch.save(dict(model_state_dict=model.state_dict(),optimizer_state_dict=adam.state_dict(),
            observation_rng_state=rng.bit_generator.state,adam_updates=plan['parent_adam']),folder/'adam-parent.pt')
        for head,limit in plan['parent_lbfgs_by_head'].items():
            for name,p in model.named_parameters():p.requires_grad_(name.startswith('heads.'+head+'.'))
            phead=list(model.heads[head].parameters())
            def progress(row):
                if row['accepted_steps']==1 or row['accepted_steps']%20==0:record(dict(stage='LBFGS',head=head,**row))
            result,optimizer=continued_lbfgs(phead,
                lambda:full_observation_head(model,obs,head),limit,progress)
            used+=result['evaluations'];history[head]=result
            torch.save(dict(optimizer_state_dict=optimizer.state_dict(),result=result,
                parameter_names=[n for n,p in model.named_parameters() if p.requires_grad]),folder/('lbfgs-'+head+'.pt'))
        for p in model.parameters():p.requires_grad_(True)
        with torch.no_grad():final_loss,final_parts=observation_objective(model,obs,obs.groups())
        torch.save(dict(model_state_dict=model.state_dict(),temperature_adapter=True,seed=cfg['seed'],
            config=cfg,adam_updates=plan['parent_adam'],complete_evaluations=used,
            initial_weights='fresh per seed, zero-output T adapter',reference_read=False),folder/'parent.pt')
        summary=dict(status='LEGAL_FIXED_PARENT_NO_FIT_GATE',seed=cfg['seed'],
            adam_updates=plan['parent_adam'],complete_evaluations=used,lbfgs=history,
            original_complete_objective=float(initial_loss),final_complete_objective=float(final_loss),
            original_components=initial_parts,final_components=final_parts,
            electrical_forward=0,electrical_adjoint=0,reference_read=False,
            seed_rescue=False,old_V_gate_applied=False,observation_only_audits=2)
        save_json(folder/'fit-summary.json',summary)
    return folder/'parent.pt'


def prepare_seed(root,cfg,seed,selected,device):
    cfg=copy.deepcopy(cfg);cfg.update(seed=seed,selected_soft=selected,roles=['E',selected],
        source_parent='fresh observation-only fit',per_E_forward_limit=27000,
        observation_seed=60100+seed,sampling_seed=60200+seed,calibration_seed=130900+seed,
        lbfgs_pool_seed=230900+seed,audit_pool_seed=330900+seed,
        electric_spatial_reduction='full' if selected=='F_full' else 'sampled')
    root.mkdir(parents=True,exist_ok=False)
    save_json(root/'frozen-fit-config.json',cfg)
    parent=fit_parent(root/'common-fit',cfg,device)
    state=torch.load(parent,map_location='cpu',weights_only=False)
    cfg['parent']=parent.relative_to(ROOT).as_posix()
    data=SparseData(ROOT/cfg['sparse'])
    exp=BoundedElectricExperiment(cfg,state['model_state_dict'],data,device,'P_E')
    pools={}
    for label in ('calibration','lbfgs','audit'):
        key=label+'_seed' if label=='calibration' else label+'_pool_seed'
        pools[label]=TimeSampler(cfg,exp.model.physics,exp.grid,cfg[key]).sample(fixed=True)
        save_json(root/(label+'-pool.json'),serialize_pool(pools[label]))
    _,values=exp.objective(exp.obs.groups(),pools['calibration'],dict(aE=1.,bE=1.),1.)
    calibration=dict(aE=values['observation'],bE=(values['thermal']+values['phase'])/3+5*values['boundary']+values['initial'],
        components=values,status='ONCE_PER_CLEAN_PARENT_SHARED',statistics=exp.statistics(),reference_read=False)
    if not np.isfinite([calibration['aE'],calibration['bE']]).all():raise FloatingPointError('nonfinite clean calibration')
    if exp.layer.backend.counts.forward_solves>500:raise RuntimeError('clean calibration solve allocation')
    save_json(root/'calibration.json',calibration)
    torch.save(dict(model_state_dict=state['model_state_dict'],temperature_adapter=True,config=cfg,
        calibration=calibration,reference_read=False,role='CLEAN_E0'),root/'parent.pt')
    if selected=='F_bal':
        soft=SoftExperiment(cfg,state['model_state_dict'],data,device)
        norms={};vectors={}
        for block in BLOCKS:
            soft.model.zero_grad(set_to_none=True)
            value,_=soft.objective(soft.obs.groups(),pools['calibration'],calibration,.1,backward=True,blocks={block:1.})
            vectors[block]=gradient_vector(soft)
            norms[block]=dict(norm=float(np.linalg.norm(vectors[block])),weighted_objective=float(value))
        g0=float(np.sqrt(sum(norms[k]['norm']**2 for k in BLOCKS[:-1])))
        ge=norms['electric']['norm']
        if min(g0,ge)<=cfg['balance_gradient_floor'] or not np.isfinite([g0,ge]).all():
            save_json(root/'calibration-failure.json',dict(reason='selected balanced rule unidentifiable',blocks=norms))
            raise RuntimeError('selected comparator eta not identifiable; do not replace it')
        cfg['eta_bal']=g0/ge
        save_json(root/'eta-calibration.json',dict(eta_bal=cfg['eta_bal'],G0=g0,ge=ge,blocks=norms,reference_read=False))
        np.savez_compressed(root/'five-block-gradients.npz',**vectors)
    else:cfg['eta_bal']=1.
    save_json(root/'frozen-config.json',cfg)
    return cfg


def predict_e(root,device):
    """Single E readout on the common fine electrical grid; no fake network pair."""
    from .phk_v23_lf11_elimination_predict import infer_time
    from .phk_v23_lf11_electric_layer import ElectricalLayer
    from .phk_v22r_prediction import _evaluation_axes
    from .phk_v22r_training import PhkTrainingConfig
    cfg=read(root/'frozen-config.json');state=torch.load(root/'E/checkpoint.pt',map_location='cpu',weights_only=False)
    model=fit_model(cfg,state['model_state_dict'],adapter=True).to(device)
    x,z,times=_evaluation_axes(PhkTrainingConfig(arm='STRONG_RAW',case_control='FULL'))
    assert (len(x),len(z))==tuple(cfg['inference_grid'])
    grid=grid_for(model.physics,*cfg['inference_grid']);layer=ElectricalLayer(grid,model.physics.heater_width_fraction,cfg['linear_tolerance'])
    arrays={k:np.empty((len(times),grid.cell_count)) for k in ('potential','temperature','phase','joule_density')};traces={}
    for i,t in enumerate(times):
        f,d=infer_time(model,layer,t,device,'P_E')
        for k in arrays:arrays[k][i]=f[k]
        for k,v in d.items():traces.setdefault(k,[]).append(v)
        if layer.backend.counts.forward_solves>278:raise RuntimeError('clean E inference limit')
        if i%200==0:print(json.dumps(dict(seed=cfg['seed'],prediction='E',index=i)),flush=True)
    target=root/'E/projected';target.mkdir(exist_ok=False)
    np.savez_compressed(target/'prediction.npz',x=x,z=z,time=times,**arrays)
    np.savez_compressed(target/'own-readout.npz',time=times,**{k:np.asarray(v) for k,v in traces.items()})
    save_json(target/'prediction.json',dict(status='FIXED_OWN_PREDICTION',role='E',readout='projected',
        grid=cfg['inference_grid'],times=len(times),electrical_counts=layer.backend.snapshot(),reference_read=False))


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RUN)
    p.add_argument('--selection',type=Path,required=True);p.add_argument('--config',type=Path,default=CONFIG)
    p.add_argument('--device',default='cuda:0');a=p.parse_args()
    cfg=read(a.config);selection=read(a.selection)
    if not selection.get('stage_B_enabled') or selection.get('selected') not in ('F_raw','F_bal','F_full'):
        raise ValueError('no unique authorized comparator: no clean training')
    selected=selection['selected'];torch.set_num_threads(cfg['cpu_threads'])
    a.root.mkdir(parents=True,exist_ok=False);save_json(a.root/'selected-comparator.json',selection)
    for seed in cfg['confirmation']['seeds']:
        directory=a.root/f'seed-{seed}'
        c=prepare_seed(directory,cfg,seed,selected,a.device)
        train_role(directory,'P_E',c,a.device,output_role='E',experiment_type=BoundedElectricExperiment)
        if not train(directory,selected,c,a.device):raise RuntimeError('clean soft endpoint invalid')
        predict_e(directory,a.device)
        from .phk_v23_lf11_training_coupling_predict import predict_pair
        predict_pair(directory,selected,a.device)
        save_json(directory/'training-and-own-inference-complete.json',dict(completed=True,
            valid_roles=c['roles'],reference_read=False,created_utc=now()))
    save_json(a.root/'training-and-own-inference-complete.json',dict(completed=True,
        clean_seeds=cfg['confirmation']['seeds'],reference_read=False,created_utc=now()))


if __name__=='__main__':main()
