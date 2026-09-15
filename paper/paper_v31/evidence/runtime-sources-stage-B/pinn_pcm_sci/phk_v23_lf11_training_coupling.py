"""New authorized soft-electric comparison, independent of the old P_F trigger.

The V28 P_F face operator, thermal/phase equations and training streams are
retained. Only one fixed scalar electric weight differs between the two arms.
This module reads sparse data and known physics, never reference fields.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import traceback
import numpy as np
import torch

from .phk_v23_lf11 import ROOT, SparseData, save_json, now
from .phk_v23_lf11_elimination import Experiment, TimeSampler, deserialize_pool, save_checkpoint
from .phk_v23_lf11_elimination_physics import thermal_phase_residual, boundary_loss, initial_loss
from .phk_v23_lf11_v_continue import continued_lbfgs

RUN=ROOT/'outputs/runs/20260913-lf11-training-coupling'
CONFIG=ROOT/'configs/phk_v23/lf11_training_coupling_sprint.json'
BLOCKS=('observation','boundary','thermal','phase','electric')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def gradient_vector(exp):
    return torch.cat([(p.grad if p.grad is not None else torch.zeros_like(p)).detach().reshape(-1).cpu()
                      for p in exp.parameters]).numpy()


class SoftExperiment(Experiment):
    def __init__(self, config, state, data, device='cpu', eta=1.):
        super().__init__(config,state,data,device,'P_F')
        self.eta=float(eta)
        self.work={k:0 for k in ('full_grid_network_evaluations','explicit_face_evaluations',
                  'thermal_phase_groups','boundary_groups','observation_groups')}

    def electric(self,t,needed):
        # The inherited P_F path uses explicit differentiable face operations.
        u=float(self.model.physics.waveform(torch.tensor(t,dtype=torch.float64,device=self.device)))
        if needed and u!=0.:
            self.work['full_grid_network_evaluations']+=1
            self.work['explicit_face_evaluations']+=1
        return super().electric(t,needed)

    def electric_square_mean(self,electric,cells):
        """V30 defaults to sampled cells; V31 changes this reduction only.

        The inherited grid is uniform, so its cell-volume integral is exactly
        the arithmetic mean. The original cells are still drawn by TimeSampler
        and consumed by both thermal and phase residuals.
        """
        if self.c.get('electric_spatial_reduction','sampled')=='full':
            if electric.numel()!=self.grid.cell_count:
                raise ValueError('full electric reduction requires every grid cell')
            residual=electric
        else:
            residual=electric[torch.as_tensor(cells,device=self.device)]
        return (residual/self.c['pde_scales']['electric']).square().mean()

    def objective(self,groups,pool,calibration,lam,*,backward=False,counter='audit',blocks=None):
        coefficients={k:1. for k in BLOCKS} if blocks is None else blocks
        co,cb,ct,cp,ce=[float(coefficients.get(k,0.)) for k in BLOCKS]
        if backward:
            key={'complete':'complete_objective_gradient_evaluations','adam':'adam_objective_gradient_evaluations'}.get(counter,'audit_objective_gradient_evaluations')
        else: key='audit_objective_evaluations'
        self.calls[key]+=1
        a,b=max(calibration['aE'],1e-12),max(calibration['bE'],1e-12)
        groups=groups if co else {}
        times=pool['times'] if cb or ct or cp or ce else {}
        totals={k:0. for k in ('observation','obs_V','obs_T','obs_phase','boundary','initial','thermal','phase','electric','objective')}
        for t in sorted(set(groups)|set(times)):
            obs,phys=groups.get(t),times.get(t)
            # V observations evaluate the original network directly, requiring no
            # extra full-grid work; the PDE needs q and/or the FV electric balance.
            v,heat,electric=self.electric(t,phys is not None and bool(ct or ce))
            loss=torch.zeros((),dtype=torch.float64,device=self.device)
            if obs is not None:
                value,pieces=self.obs.loss(self.model,obs,v,'P_F')
                loss=loss+co*value/a
                totals['observation']+=float(value.detach())
                for k,value in pieces.items(): totals[k]+=float(value.detach())
                self.work['observation_groups']+=1
            if phys is not None:
                if cb:
                    value=phys['mass']*boundary_loss(self.model,phys['sides'])
                    loss=loss+cb*lam*5*value/b
                    totals['boundary']+=float(value.detach())
                    self.work['boundary_groups']+=1
                if ct or cp:
                    r=thermal_phase_residual(self.model,self.grid,t,phys['cells'],heat)
                    self.work['thermal_phase_groups']+=1
                    for k,c in (('thermal',ct),('phase',cp)):
                        if c:
                            value=phys['mass']*(r[k]/self.c['pde_scales'][k]).square().mean()
                            loss=loss+c*lam*value/(3*b)
                            totals[k]+=float(value.detach())
                if ce and electric is not None:
                    value=phys['mass']*self.electric_square_mean(electric,phys['cells'])
                    loss=loss+ce*self.eta*lam*value/(3*b)
                    totals['electric']+=float(value.detach())
            if not torch.isfinite(loss): raise FloatingPointError(f'nonfinite soft objective at {t}')
            if backward and loss.requires_grad: loss.backward()
            totals['objective']+=float(loss.detach())
        if cb:
            value=initial_loss(self.model,pool['initial'])
            loss=cb*lam*value/b
            if backward and loss.requires_grad: loss.backward()
            totals['initial']=float(value.detach())
            totals['objective']+=float(loss.detach())
        totals['C']=totals['observation']/a+lam*(5*totals['boundary']+totals['initial'])/b
        totals['F_Tphi']=lam*(totals['thermal']+totals['phase'])/(3*b)
        totals['E_e']=lam*totals['electric']/(3*b)
        return torch.tensor(totals['objective'],dtype=torch.float64,device=self.device),totals

    def statistics(self):
        result=super().statistics()
        result['explicit_work']=dict(self.work)
        if result['electrical']['forward_solves'] or result['electrical']['adjoint_solves']:
            raise RuntimeError('soft training unexpectedly invoked a linear solve')
        return result


def prepare(root,config,device):
    root.mkdir(parents=True,exist_ok=False)
    history=ROOT/config['historical_root']
    for name in ('calibration.json','calibration-pool.json','lbfgs-pool.json','audit-pool.json'):
        shutil.copyfile(history/name,root/name)
    shutil.copyfile(ROOT/config['parent'],root/'parent.pt')
    state=torch.load(root/'parent.pt',map_location='cpu',weights_only=False)
    data=SparseData(ROOT/config['sparse'])
    exp=SoftExperiment(config,state['model_state_dict'],data,device)
    cal=read(root/'calibration.json')
    pool=deserialize_pool(read(root/'calibration-pool.json'))
    vectors,records={},{}
    layout=[];offset=0
    for name,p in exp.model.named_parameters():
        if p.requires_grad:
            layout.append(dict(name=name,shape=list(p.shape),start=offset,stop=offset+p.numel()))
            offset+=p.numel()
    for block in BLOCKS:
        exp.model.zero_grad(set_to_none=True)
        value,components=exp.objective(exp.obs.groups(),pool,cal,.1,backward=True,blocks={block:1.})
        vectors[block]=gradient_vector(exp)
        records[block]={'weighted_objective':float(value),'norm':float(np.linalg.norm(vectors[block])),
                        'raw_components':components}
    g0=float(np.sqrt(sum(records[k]['norm']**2 for k in BLOCKS[:-1])))
    ge=records['electric']['norm']
    identifiable=bool(np.isfinite([g0,ge]).all() and min(g0,ge)>config['balance_gradient_floor'])
    eta=g0/ge if identifiable else None
    if eta is not None and not np.isfinite(eta): identifiable=False;eta=None
    equivalent=bool(identifiable and np.isclose(eta,1.,rtol=config['balance_equivalence_rtol'],atol=config['balance_equivalence_atol']))
    reason='FROZEN_DISTINCT_BALANCED_CONTROL' if identifiable and not equivalent else ('NUMERICALLY_EQUIVALENT_TO_RAW' if equivalent else 'RATIO_NOT_IDENTIFIABLE')
    config.update(roles=['F_raw']+(['F_bal'] if identifiable and not equivalent else []),eta_bal=eta,
                  balance_status=reason,reference_read=False)
    np.savez_compressed(root/'five-block-gradients.npz',**vectors)
    save_json(root/'eta-calibration.json',dict(status=reason,G0=g0,electric_gradient_norm=ge,eta_bal=eta,
        blocks=records,parameter_layout=layout,statistics=exp.statistics(),full_gradient_scans=5,
        lambda_at_calibration=.1,optimizer_updates=0,reference_read=False,created_utc=now()))
    save_json(root/'frozen-config.json',config)
    print(json.dumps(dict(event='SOFT_WEIGHTS_FROZEN',status=reason,eta_bal=eta,G0=g0,ge=ge)),flush=True)
    return config


def train(root,arm,config,device):
    folder=root/arm;folder.mkdir(exist_ok=False)
    state=torch.load(root/'parent.pt',map_location='cpu',weights_only=False)
    exp=SoftExperiment(config,state['model_state_dict'],SparseData(ROOT/config['sparse']),device,
                       1. if arm in ('F_raw','F_full') else config['eta_bal'])
    cal=read(root/'calibration.json')
    pool=deserialize_pool(read(root/'lbfgs-pool.json'))
    sampler=TimeSampler(config,exp.model.physics,exp.grid,config['sampling_seed'])
    obs_rng=np.random.default_rng(config['observation_seed'])
    optimizer=torch.optim.Adam(exp.parameters,lr=config['branch_lr'],betas=tuple(config['betas']),eps=config['eps'])
    completed=0
    try:
        with (folder/'adam-telemetry.jsonl').open('x',encoding='utf-8') as log:
            for step in range(1,config['branch_updates']+1):
                groups=exp.obs.groups(obs_rng,config['adam_observation_times'])
                batch=sampler.sample()
                optimizer.zero_grad(set_to_none=True)
                lam=config['lambda_max']*min(step/config['lambda_ramp'],1.)
                _,components=exp.objective(groups,batch,cal,lam,backward=True,counter='adam')
                norm=torch.nn.utils.clip_grad_norm_(exp.parameters,config['gradient_clip'],error_if_nonfinite=True)
                optimizer.step();completed=step;exp.calls['optimizer_updates']=step
                if not all(torch.isfinite(p).all() for p in exp.parameters): raise FloatingPointError('nonfinite Adam state')
                if step==1 or step%50==0:
                    record=dict(step=step,gradient_norm=float(norm),**components,statistics=exp.statistics())
                    log.write(json.dumps(record,allow_nan=False)+'\n');log.flush()
                    print(json.dumps(dict(role=arm,adam=step,objective=components['objective'])),flush=True)
                if step in config['checkpoint_steps']:
                    save_checkpoint(folder/f'adam-{step}.pt',exp,optimizer,config,cal,step,role=arm,
                        optimizer_phase='Adam',eta=exp.eta,observation_rng_state=obs_rng.bit_generator.state,
                        physics_rng_state=sampler.rng.bit_generator.state)
        with (folder/'lbfgs-telemetry.jsonl').open('x',encoding='utf-8') as log:
            def report(record):
                record['statistics']=exp.statistics()
                log.write(json.dumps(record,allow_nan=False)+'\n');log.flush()
                if record['accepted_steps']==1 or record['accepted_steps']%10==0:
                    print(json.dumps(dict(role=arm,lbfgs=record['evaluations'],loss=record['loss'])),flush=True)
            result,optimizer=continued_lbfgs(exp.parameters,
                lambda:exp.objective(exp.obs.groups(),pool,cal,config['lambda_max'],backward=True,counter='complete')[0],
                config['lbfgs_evaluations'],report)
        save_checkpoint(folder/'checkpoint.pt',exp,optimizer,config,cal,completed,role=arm,
                        optimizer_phase='L-BFGS',lbfgs_result=result,eta=exp.eta)
        save_json(folder/'terminal.json',dict(status='VALID_FIXED_ENDPOINT',role=arm,adam_updates=completed,
            lbfgs=result,statistics=exp.statistics(),eta=exp.eta,reference_read=False,device=device))
        print(json.dumps(dict(event='SOFT_ENDPOINT_ACCEPTED',role=arm,adam=completed,lbfgs=result['evaluations'])),flush=True)
        return True
    except Exception as error:
        save_json(folder/'failure.json',dict(status='EXECUTION_FAILED',role=arm,completed_updates=completed,
            error=str(error),traceback=traceback.format_exc(),statistics=exp.statistics(),reference_read=False))
        print(json.dumps(dict(event='SOFT_ARM_FAILED',role=arm,error=str(error))),flush=True)
        return False


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['prepare','train','predict','all'])
    p.add_argument('--root',type=Path,default=RUN);p.add_argument('--config',type=Path,default=CONFIG)
    p.add_argument('--device',default='cpu');p.add_argument('--role')
    args=p.parse_args()
    config=read(args.config if args.action in ('prepare','all') else args.root/'frozen-config.json')
    torch.set_num_threads(config['cpu_threads'])
    if args.action in ('prepare','all'): config=prepare(args.root,config,args.device)
    if args.action in ('train','all'):
        for arm in ([args.role] if args.role else config['roles']): train(args.root,arm,config,args.device)
    if args.action in ('predict','all'):
        from .phk_v23_lf11_training_coupling_predict import predict_pair
        for arm in ([args.role] if args.role else config['roles']):
            if (args.root/arm/'terminal.json').exists(): predict_pair(args.root,arm,args.device)
    if args.action=='all':
        valid=[r for r in config['roles'] if (args.root/r/'terminal.json').exists()]
        save_json(args.root/'training-and-own-inference-complete.json',dict(completed=True,
            valid_roles=valid,all_roles_valid=len(valid)==len(config['roles']),reference_read=False,created_utc=now()))


if __name__=='__main__': main()
