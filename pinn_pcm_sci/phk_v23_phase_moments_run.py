"""Bounded eight-arm phase-moment development; training never reads references."""
from __future__ import annotations
import argparse
import json
import platform
import time
import traceback
from pathlib import Path

import numpy as np
import torch

from .phk_v23_lf11 import ROOT, save_json, now, digest
from .phk_v23_b1 import B1Electric, require_resource
from .phk_v23_b1_observations import VisibleData
from .phk_v23_lf11_elimination import TimeSampler, deserialize_pool
from .phk_v23_lf11_elimination_physics import thermal_phase_residual, boundary_loss, initial_loss, grid_for
from .phk_v23_lf11_followup_fit import fit_model
from .phk_v23_lf11_v_continue import continued_lbfgs
from .phk_v23_phase_moments import (
    ARMS, ARM_KIND, KINDS, PanelSampler, panel_values, phase_value_gradient, calibrate, select_order,
)

CONFIG = ROOT/'configs/phk_v23/phase_moments_20260923.json'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


class PhaseExperiment(B1Electric):
    def __init__(self, config, state, data, device='cpu', arm='D'):
        if arm not in ARMS:
            raise ValueError(arm)
        super().__init__(config, state, data, device, 'D_E' if arm=='D' else 'P_E')
        self.arm = arm
        self.phase_work = dict(phase_derivative_positions=0, phase_spatial_second_ad_components=0,
                               phase_endpoint_queries=0)

    def objective(self, groups, pool, calibration, lam, *, backward=False, counter='audit'):
        if backward:
            key = {'complete':'complete_objective_gradient_evaluations',
                   'adam':'adam_objective_gradient_evaluations'}.get(counter, 'audit_objective_gradient_evaluations')
            self.calls[key] += 1
        else:
            self.calls['audit_objective_evaluations'] += 1
        a, b = max(calibration['aE'], 1e-12), max(calibration['bE'], 1e-12)
        totals = dict.fromkeys(('observation','obs_V','obs_T','obs_phase','boundary','initial','thermal','phase','objective'),0.)
        for t in sorted(set(groups) | set(pool['times'])):
            group, phys = groups.get(t), pool['times'].get(t)
            interior = phys is not None and self.arm != 'D'
            v, heat, _ = self.electric(t, group is not None or interior)
            loss = torch.zeros((), dtype=torch.float64, device=self.device)
            if group is not None:
                observed, pieces = self.obs.loss(self.model, group, v, self.role)
                loss = loss+observed/a
                totals['observation'] += float(observed.detach())
                for k, value in pieces.items():
                    totals[k] += float(value.detach())
            if phys is not None:
                boundary = phys['mass']*boundary_loss(self.model, phys['sides'])
                loss = loss+lam*5*boundary/b
                totals['boundary'] += float(boundary.detach())
                if interior:
                    r = thermal_phase_residual(self.model, self.grid, t, phys['cells'], heat, include_phase=False)
                    value = phys['mass']*(r['thermal']/self.c['pde_scales']['thermal']).square().mean()
                    loss = loss+lam*value/(3*b)
                    totals['thermal'] += float(value.detach())
            if not torch.isfinite(loss):
                raise FloatingPointError(f'nonfinite {self.arm} common objective')
            if backward and loss.requires_grad:
                loss.backward()
            totals['objective'] += float(loss.detach())
        ic = initial_loss(self.model, pool['initial'])
        loss = lam*ic/b
        if backward:
            loss.backward()
        totals['initial'] = float(ic.detach())
        totals['objective'] += float(loss.detach())
        if self.arm != 'D':
            kind = ARM_KIND[self.arm]
            panels = pool['phase_panels']
            for start in range(0, len(panels), self.c['phase_panels']['chunk_panels']):
                value = panel_values(self.model, self.grid,
                    panels[start:start+self.c['phase_panels']['chunk_panels']],
                    self.c['phase_panels']['order'], self.c['phase_logit_epsilon'], kind, self.phase_work)[kind]
                value = value*calibration['phase']['factors'][self.arm]
                loss = lam*value/(3*b)
                if not torch.isfinite(loss):
                    raise FloatingPointError(f'nonfinite {self.arm} phase objective')
                if backward:
                    loss.backward()
                totals['phase'] += float(value.detach())
                totals['objective'] += float(loss.detach())
        return torch.tensor(totals['objective'], dtype=torch.float64, device=self.device), totals

    def statistics(self):
        return {**super().statistics(), 'phase_work':dict(self.phase_work)}


def parent_model(cfg):
    parent = torch.load(ROOT/cfg['parent'], map_location='cpu', weights_only=False)
    if not parent.get('temperature_adapter'):
        raise ValueError('The B1 parent must retain its temperature adapter')
    model = fit_model(cfg, parent['model_state_dict'], adapter=True)
    for p in model.heads['potential'].parameters():
        p.requires_grad_(False)
    return model, parent


def phase_record(model, grid, panels, order, delta):
    start = time.perf_counter()
    values, gradients = phase_value_gradient(model, grid, panels, order, delta)
    return dict(values=values, gradient_norms={k:float(torch.linalg.vector_norm(v)) for k,v in gradients.items()},
                elapsed_seconds=time.perf_counter()-start), gradients


def prepare(cfg):
    """One reference-blind numerical qualification; no optimizer creation."""
    run = ROOT/cfg['run']
    if (run/'quadrature.json').exists():
        raise FileExistsError('Qualification already exists; do not resample for a favorable result')
    run.mkdir(parents=True, exist_ok=True)
    model, parent = parent_model(cfg)
    grid = grid_for(model.physics, *cfg['grid'])
    calpool = PanelSampler(cfg, grid, cfg['phase_panels']['calibration_seed']).sample(True)
    fixed = PanelSampler(cfg, grid, cfg['phase_panels']['fixed_seed']).sample(True)
    save_json(run/'phase-calibration-pool.json', calpool)
    save_json(run/'phase-fixed-pool.json', fixed)
    save_json(run/'input-manifest.json', dict(parent=cfg['parent'], parent_sha256=digest(ROOT/cfg['parent']),
        sparse=cfg['sparse'], sparse_sha256=digest(ROOT/cfg['sparse']), source_commit=cfg['source_commit'],
        source_b1=cfg['source_b1'], runtime=dict(python=platform.python_version(),torch=torch.__version__),
        reference_read=False, optimizer_updates=0, created_utc=now()))
    records, gradients = {}, {}
    for order in (8,16,32):
        existing=run/f'parent-quadrature-{order}.json'
        if existing.exists():
            records[order]=read(existing)
            continue
        records[order], gradients[order] = phase_record(model, grid, calpool, order, cfg['phase_logit_epsilon'])
        save_json(run/f'parent-quadrature-{order}.json', records[order])
        print(json.dumps(dict(stage='parent_quadrature',order=order,**records[order])),flush=True)
    decision = select_order(records)
    # Fixed manufactured field: same IC/startup and smooth analytic head functions.
    class SmoothHead(torch.nn.Module):
        def __init__(self):
            super().__init__();self.amplitude=torch.nn.Parameter(torch.tensor(.4,dtype=torch.float64))
        def forward(self, q):
            return self.amplitude*(q[:,0:1]**2+.3*q[:,1:2]**2+torch.sin(torch.pi*q[:,2:3]))
    synthetic = fit_model(dict(cfg,width=8,layers=2))
    for name in ('temperature','phase','potential'):
        synthetic.heads[name]=SmoothHead();synthetic.encoders[name]=torch.nn.Identity()
    synthetic_records = {}
    for order in (8,16,32):
        synthetic_records[order], _ = phase_record(synthetic, grid, calpool, order, cfg['phase_logit_epsilon'])
    synthetic_decision = select_order(synthetic_records)
    if decision['selected_order'] is None or synthetic_decision['selected_order'] is None:
        decision.update(status='QUADRATURE_UNRESOLVED',selected_order=None)
    else:
        decision['selected_order']=max(decision['selected_order'],synthetic_decision['selected_order'])
    save_json(run/'quadrature.json',dict(**decision,parent=records,manufactured=synthetic_records,
        manufactured_decision=synthetic_decision,reference_read=False,optimizer_updates=0))
    if decision['selected_order'] is None:
        return decision
    order=decision['selected_order']
    if order not in gradients:
        repeated, gradients[order]=phase_record(model,grid,calpool,order,cfg['phase_logit_epsilon'])
        for key in ('values','gradient_norms'):
            np.testing.assert_allclose(list(repeated[key].values()),list(records[order][key].values()),rtol=2e-11,atol=1e-13)
        save_json(run/'calibration-engineering-recovery.json',dict(
            reason='local process exited during order32 without Python traceback; low available host memory',
            fix='at most 512 coordinate positions per shared AD graph',
            original_results_reused=[8,16],missing_order_completed=32,
            selected_order_gradient_recomputed=order,blockwise_values_and_gradient_norms_agree=True,
            optimizer_updates=0,scientific_identity_changed=False))
    phase_cal=calibrate(records[order]['values'],gradients[order])
    save_json(run/'phase-calibration.json',phase_cal)
    cfg['phase_panels']['order']=order
    common=read(ROOT/cfg['source_b1']/'calibration.json')
    common['phase']=phase_cal
    save_json(run/'calibration.json',common)
    # Simulate only known time RNGs to freeze tighter solve ceilings before training.
    data=VisibleData(ROOT/cfg['sparse'])
    exp=PhaseExperiment(cfg,parent['model_state_dict'],data,'cpu','D')
    sampler=TimeSampler(cfg,model.physics,grid,cfg['sampling_seed'])
    rng=np.random.default_rng(cfg['observation_seed'])
    limits=dict(D=0,P=0)
    def powered(times):
        return sum(float(model.physics.waveform(torch.tensor(t,dtype=torch.float64)))!=0. for t in times)
    for _ in range(cfg['branch_updates']):
        groups=exp.obs.groups(rng,cfg['adam_observation_times']);pool=sampler.sample()
        limits['D']+=powered(groups);limits['P']+=powered(set(groups)|set(pool['times']))
    pool=deserialize_pool(read(ROOT/cfg['source_b1']/'lbfgs-pool.json'))
    fixed_count={'D':powered(exp.obs.groups()),'P':powered(set(exp.obs.groups())|set(pool['times']))}
    cfg['training_solve_caps']={arm:limits['D' if arm=='D' else 'P']+
        cfg['lbfgs_evaluations']*fixed_count['D' if arm=='D' else 'P'] for arm in ARMS}
    cfg['per_E_forward_limit']=max(cfg['training_solve_caps'].values())
    save_json(run/'frozen-config.json',cfg)
    return decision


def full_pool(cfg):
    pool=deserialize_pool(read(ROOT/cfg['source_b1']/'lbfgs-pool.json'))
    pool['phase_panels']=read(ROOT/cfg['run']/'phase-fixed-pool.json')
    return pool


def profile(cfg):
    run=ROOT/cfg['run'];cfg=read(run/'frozen-config.json')
    if (run/'profile.json').exists():
        raise FileExistsError('Bounded profile already complete')
    _,parent=parent_model(cfg);data=VisibleData(ROOT/cfg['sparse']);pool=full_pool(cfg)
    cal=read(run/'calibration.json');result={}
    try:
        import psutil
    except ImportError:
        psutil=None
    for arm in ARMS:
        exp=PhaseExperiment(cfg,parent['model_state_dict'],data,'cpu',arm)
        start=time.perf_counter()
        value,parts=exp.objective(exp.obs.groups(),pool,cal,.1,backward=True)
        gradient=torch.cat([(p.grad if p.grad is not None else torch.zeros_like(p)).reshape(-1) for p in exp.parameters])
        if not torch.isfinite(gradient).all():
            raise FloatingPointError('Invalid profile gradient')
        memory=psutil.Process().memory_info()._asdict() if psutil else {'unavailable':'psutil not installed'}
        result[arm]=dict(objective=float(value),components=parts,gradient_norm=float(torch.linalg.vector_norm(gradient)),
            elapsed_seconds=time.perf_counter()-start,memory=memory,statistics=exp.statistics(),optimizer_updates=0)
        save_json(run/f'profile-{arm}.json',result[arm])
        print(json.dumps(dict(stage='profile',arm=arm,seconds=result[arm]['elapsed_seconds'])),flush=True)
    save_json(run/'profile.json',dict(status='ZERO_UPDATE_PROFILE_COMPLETE',passes_per_arm=1,arms=result))
    save_json(run/'prepared.json',dict(status='LOCAL_QUALIFICATION_PASSED',optimizer_updates=0,reference_read=False,
                                      selected_order=cfg['phase_panels']['order']))


def train(cfg, device):
    run=ROOT/cfg['run'];cfg=read(run/'frozen-config.json')
    if read(run/'prepared.json')['status']!='LOCAL_QUALIFICATION_PASSED':
        raise ValueError('Local qualification incomplete')
    parent=torch.load(ROOT/cfg['parent'],map_location='cpu',weights_only=False)
    data=VisibleData(ROOT/cfg['sparse']);cal=read(run/'calibration.json');fixed=full_pool(cfg)
    terminals={}
    for arm in ARMS:
        folder=run/arm;folder.mkdir(exist_ok=False)
        exp=PhaseExperiment(cfg,parent['model_state_dict'],data,device,arm)
        sampler=TimeSampler(cfg,exp.model.physics,exp.grid,cfg['sampling_seed'])
        panels=PanelSampler(cfg,exp.grid,cfg['phase_panels']['adam_seed'])
        rng=np.random.default_rng(cfg['observation_seed'])
        optimizer=torch.optim.Adam(exp.parameters,lr=cfg['branch_lr'],betas=tuple(cfg['betas']),eps=cfg['eps'])
        completed=0;start=time.perf_counter()
        try:
            with (folder/'adam-telemetry.jsonl').open('x',encoding='utf-8') as log:
                for step in range(1,cfg['branch_updates']+1):
                    pool=sampler.sample();pool['phase_panels']=panels.sample()
                    optimizer.zero_grad(set_to_none=True)
                    _,parts=exp.objective(exp.obs.groups(rng,cfg['adam_observation_times']),pool,cal,
                        cfg['lambda_max']*min(step/cfg['lambda_ramp'],1.),backward=True,counter='adam')
                    norm=torch.nn.utils.clip_grad_norm_(exp.parameters,cfg['gradient_clip'],error_if_nonfinite=True)
                    optimizer.step();completed=step;exp.calls['optimizer_updates']=step
                    if not all(torch.isfinite(p).all() for p in exp.parameters):
                        raise FloatingPointError('nonfinite accepted Adam state')
                    if step==1 or step%50==0:
                        record=dict(step=step,gradient_norm=float(norm),**parts,statistics=exp.statistics())
                        log.write(json.dumps(record,allow_nan=False)+'\n');log.flush()
                        print(json.dumps(dict(arm=arm,adam=step,objective=parts['objective'])),flush=True)
                    if step in cfg['checkpoint_steps']:
                        torch.save(dict(model_state_dict=exp.model.state_dict(),optimizer_state_dict=optimizer.state_dict(),
                            config=cfg,arm=arm,updates=step,temperature_adapter=True,reference_read=False),folder/f'adam-{step}.pt')
            with (folder/'lbfgs-telemetry.jsonl').open('x',encoding='utf-8') as log:
                def log_step(record):
                    log.write(json.dumps(dict(**record,statistics=exp.statistics()))+'\n');log.flush()
                    if record['accepted_steps']==1 or record['accepted_steps']%10==0:
                        print(json.dumps(dict(arm=arm,lbfgs=record['evaluations'],loss=record['loss'])),flush=True)
                result,optimizer=continued_lbfgs(exp.parameters,
                    lambda:exp.objective(exp.obs.groups(),fixed,cal,.1,backward=True,counter='complete')[0],
                    cfg['lbfgs_evaluations'],log_step)
            if result['termination'] in ('NONFINITE_LINE_SEARCH_TRIAL_ROLLED_BACK','LINE_SEARCH_FAILED_WOLFE_TRIAL_ROLLED_BACK'):
                raise FloatingPointError('Invalid line search: '+result['termination'])
            if exp.layer.backend.counts.forward_solves>cfg['training_solve_caps'][arm]:
                raise RuntimeError('Frozen electrical cap exceeded')
            torch.save(dict(model_state_dict=exp.model.state_dict(),optimizer_state_dict=optimizer.state_dict(),
                config=cfg,arm=arm,updates=completed,temperature_adapter=True,reference_read=False,
                calibration=cal,lbfgs_result=result,statistics=exp.statistics()),folder/'checkpoint.pt')
            terminal=dict(status='VALID_FIXED_ENDPOINT',arm=arm,adam_updates=completed,lbfgs=result,
                statistics=exp.statistics(),elapsed_seconds=time.perf_counter()-start,reference_read=False)
            save_json(folder/'terminal.json',terminal);terminals[arm]=terminal
        except Exception as error:
            save_json(folder/'failure.json',dict(status='INVALID_OR_INCOMPLETE',completed_updates=completed,
                error=str(error),traceback=traceback.format_exc(),statistics=exp.statistics()))
            raise
    save_json(run/'all-endpoints-locked.json',dict(status='ALL_EIGHT_FIXED_ENDPOINTS_LOCKED',arms=terminals,
                                                reference_read=False,created_utc=now()))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('prepare','profile','train'))
    p.add_argument('--config',type=Path,default=CONFIG)
    p.add_argument('--device',default='cpu');p.add_argument('--resource',type=Path)
    a=p.parse_args();cfg=read(a.config);torch.set_num_threads(cfg['cpu_threads'])
    if a.action=='prepare':
        print(json.dumps(prepare(cfg)))
    elif a.action=='profile':
        profile(cfg)
    else:
        require_resource(a.resource,a.device,cfg);train(cfg,a.device)


if __name__=='__main__':
    main()
