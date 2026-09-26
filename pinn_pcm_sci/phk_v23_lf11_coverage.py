"""Two authorized mixed-measure electrical coverage continuations, 2026-09-26.

No reference evaluator is imported. Non-electrical losses are delegated to the
unchanged historical SoftExperiment. The new term replaces its electric term.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import traceback

import numpy as np
import torch

from .phk_v23_lf11 import ROOT, SparseData, now, save_json
from .phk_v23_lf11_elimination import TimeSampler, deserialize_pool
from .phk_v23_lf11_training_coupling import SoftExperiment, BLOCKS, read, gradient_vector

RUN = ROOT / 'outputs/runs/20260926-core-revision-vo2-bridge/fcov'


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    save_json(temporary, value)
    temporary.replace(path)


def atomic_checkpoint(path, payload):
    path = Path(path)
    temporary = path.with_suffix('.tmp')
    torch.save(payload, temporary)
    temporary.replace(path)


class ResourceStop(RuntimeError):
    pass


def resource_status(device):
    if Path('/proc/self/status').is_file():
        # Linux exposes the two required measurements without another package.
        def kib_fields(path):
            return {line.split(':',1)[0]:int(line.split()[1])*1024
                    for line in Path(path).read_text().splitlines()
                    if len(line.split())==3 and line.split()[-1]=='kB'}
        status=dict(rss=kib_fields('/proc/self/status')['VmRSS'],
                    host_available=kib_fields('/proc/meminfo')['MemAvailable'])
    else:
        import ctypes
        from ctypes import wintypes
        class MemoryStatus(ctypes.Structure):
            _fields_=[('length',wintypes.DWORD),('load',wintypes.DWORD)]+[
                (name,ctypes.c_ulonglong) for name in ('total_phys','avail_phys','total_page',
                    'avail_page','total_virtual','avail_virtual','avail_extended')]
        class ProcessMemory(ctypes.Structure):
            _fields_=[('cb',wintypes.DWORD),('faults',wintypes.DWORD)]+[
                (name,ctypes.c_size_t) for name in ('peak_ws','ws','peak_pool','pool',
                    'peak_nonpaged','nonpaged','pagefile','peak_pagefile')]
        ms=MemoryStatus();ms.length=ctypes.sizeof(ms)
        pm=ProcessMemory();pm.cb=ctypes.sizeof(pm)
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.GetCurrentProcess.restype=wintypes.HANDLE
        psapi=ctypes.WinDLL('psapi',use_last_error=True)
        psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(ProcessMemory),wintypes.DWORD]
        if not kernel.GlobalMemoryStatusEx(ctypes.byref(ms)) or not psapi.GetProcessMemoryInfo(
                kernel.GetCurrentProcess(),ctypes.byref(pm),pm.cb):
            raise OSError(ctypes.get_last_error(),'Native memory measurement failed')
        status=dict(rss=pm.ws,host_available=ms.avail_phys)
    cgroup = Path('/sys/fs/cgroup')
    for limit_name, used_name in [('memory.max', 'memory.current'),
                                 ('memory/memory.limit_in_bytes', 'memory/memory.usage_in_bytes')]:
        if (cgroup/limit_name).exists():
            limit = (cgroup/limit_name).read_text().strip()
            if limit.isdigit():
                status['host_available'] = min(status['host_available'],
                    int(limit)-int((cgroup/used_name).read_text()))
            break
    if str(device).startswith('cuda'):
        status.update(gpu_allocated=torch.cuda.memory_allocated(device),
                      gpu_free=torch.cuda.mem_get_info(device)[0])
    return status


def check_resources(device):
    status = resource_status(device)
    gib = 1024**3
    if (status['rss'] >= 12*gib or status['host_available'] < 4*gib or
        status.get('gpu_allocated', 0) >= 16*gib or status.get('gpu_free', 32*gib) < 4*gib):
        raise ResourceStop(json.dumps(status))
    return status


def merge_measure(physics, observed):
    weights = {}
    for t, weight in physics.items():
        weights[float(t)] = weights.get(float(t), 0.) + .5*float(weight)
    for t, weight in observed.items():
        weights[float(t)] = weights.get(float(t), 0.) + .5*float(weight)
    return weights


class CoverageExperiment(SoftExperiment):
    def __init__(self, config, state, data, device='cpu'):
        super().__init__(config, state, data, device, eta=1.)
        self.c = dict(self.c, electric_spatial_reduction='full')
        self.coverage_rng = np.random.default_rng(960000+int(config['seed']))
        marginal = self.obs.global_weight.sum(axis=1)
        mask = np.array([float(self.model.physics.waveform(torch.tensor(
            float(t), dtype=torch.float64, device=device))) != 0. for t in self.obs.times])
        self.powered_times = self.obs.times[mask]
        self.powered_probability = marginal[mask]/marginal[mask].sum()

    def observed_measure(self, sampled=False):
        if not sampled:
            return dict(zip(map(float, self.powered_times), map(float, self.powered_probability)))
        indices, counts = np.unique(self.coverage_rng.choice(len(self.powered_times),
            size=4, replace=True, p=self.powered_probability), return_counts=True)
        return {float(self.powered_times[i]): float(n/4) for i, n in zip(indices, counts)}

    def objective(self, groups, pool, calibration, lam, *, backward=False,
                  counter='audit', observed_measure=None, include_electric=True):
        # The old observation, boundary, IC, thermal, and phase terms (and the
        # soft-network Joule source) are evaluated by their original routine.
        _, totals = super().objective(groups, pool, calibration, lam,
            backward=backward, counter=counter,
            blocks={key: 1. for key in BLOCKS if key != 'electric'})
        if include_electric:
            obs = self.observed_measure() if observed_measure is None else observed_measure
            weights = merge_measure({t: v['mass'] for t, v in pool['times'].items()}, obs)
            b = max(calibration['bE'], 1e-12)
            electric_value = 0.
            for t, weight in sorted(weights.items()):
                _, _, residual = self.electric(t, True)
                if residual is None:
                    continue
                value = weight*self.electric_square_mean(residual, None)
                loss = lam*value/(3*b)
                if not torch.isfinite(loss):
                    raise FloatingPointError('nonfinite coverage term')
                if backward:
                    loss.backward()
                electric_value += float(value.detach())
                totals['objective'] += float(loss.detach())
            totals['electric'] = electric_value
            totals['E_e'] = lam*electric_value/(3*b)
        return torch.tensor(totals['objective'], dtype=torch.float64, device=self.device), totals


def load_experiment(folder, device):
    cfg = read(folder/'frozen-config.json')
    parent = torch.load(folder/'parent.pt', map_location='cpu', weights_only=False)
    return cfg, CoverageExperiment(cfg, parent['model_state_dict'], SparseData(ROOT/cfg['sparse']), device)


def profile(folder, device):
    check_resources(device)
    cfg, exp = load_experiment(folder, device)
    torch.set_num_threads(4)
    cal = read(folder/'calibration.json')
    pool = deserialize_pool(read(folder/'lbfgs-pool.json'))
    before = {k: v.detach().clone() for k, v in exp.model.state_dict().items()}
    if str(device).startswith('cuda'):
        torch.cuda.reset_peak_memory_stats(device)
    started = time.perf_counter()
    exp.model.zero_grad(set_to_none=True)
    _, components = exp.objective(exp.obs.groups(), pool, cal, cfg['lambda_max'], backward=True)
    grad = gradient_vector(exp)
    assert np.isfinite(grad).all() and all(torch.equal(before[k], v) for k, v in exp.model.state_dict().items())
    record = dict(status='PASS', optimizer_updates=0, seconds=time.perf_counter()-started,
        gradient_norm=float(np.linalg.norm(grad)), components=components,
        resources=check_resources(device), device=device,
        gpu_peak_allocated=torch.cuda.max_memory_allocated(device) if str(device).startswith('cuda') else None,
        statistics=exp.statistics(), reference_read=False, created_utc=now(),
        powered_observation_times=len(exp.powered_times), physical_times=len(pool['times']),
        electric_union_size=len(merge_measure({t:v['mass'] for t,v in pool['times'].items()},exp.observed_measure())))
    atomic_json(folder/'zero-update-profile.json', record)
    print(json.dumps(dict(event='PROFILE_PASS',seed=cfg['seed'],seconds=record['seconds'],resources=record['resources'])),flush=True)


def _cpu(value):
    if torch.is_tensor(value): return value.detach().cpu().clone()
    if isinstance(value, dict): return {k:_cpu(v) for k,v in value.items()}
    if isinstance(value, list): return [_cpu(v) for v in value]
    if isinstance(value, tuple): return tuple(_cpu(v) for v in value)
    return copy.deepcopy(value)


def accepted_lbfgs(parameters, objective, remaining, *, optimizer_state=None,
                   report=None, charge=None, resource_check=None):
    """Historical continued_lbfgs recipe plus durable accepted-state hooks.

    The strong-Wolfe recipe and acceptance checks are unchanged. All exceptions
    restore parameters AND optimizer history before returning control to caller.
    PyTorch LBFGS is BSD-3-Clause; the wrapper derives from phk_v23_lf11_v_continue.
    """
    parameters = list(parameters)
    opt = torch.optim.LBFGS(parameters, lr=1., max_iter=1, max_eval=32,
        tolerance_grad=1e-10, tolerance_change=1e-14, history_size=50, line_search_fn='strong_wolfe')
    if optimizer_state is not None: opt.load_state_dict(copy.deepcopy(optimizer_state))
    used = accepted = 0
    terminal = 'EVALUATION_BUDGET_EXHAUSTED'
    last_loss = initial_loss = None
    def flat(items): return torch.cat([p.detach().reshape(-1) for p in items])
    class Limit(Exception): pass
    while used < remaining:
        if resource_check: resource_check()
        snapshot = [p.detach().clone() for p in parameters]
        old_opt = copy.deepcopy(opt.state_dict())
        evaluations = []
        def closure():
            nonlocal used, initial_loss
            if used >= remaining: raise Limit()
            if resource_check: resource_check()
            used += 1
            if charge: charge()
            opt.zero_grad(set_to_none=True)
            loss = objective()
            gradient = flat([p.grad if p.grad is not None else torch.zeros_like(p) for p in parameters])
            if not torch.isfinite(loss) or not torch.isfinite(gradient).all():
                raise FloatingPointError('nonfinite complete objective or gradient')
            if initial_loss is None: initial_loss=float(loss.detach())
            evaluations.append((flat(parameters).clone(),float(loss.detach()),gradient.clone()))
            return loss
        def restore():
            with torch.no_grad():
                for p, old in zip(parameters,snapshot): p.copy_(old)
            opt.load_state_dict(old_opt)
            opt.zero_grad(set_to_none=True)
        try:
            opt.step(closure)
        except Limit:
            restore(); terminal='EVALUATION_BUDGET_EXHAUSTED_TRIAL_ROLLED_BACK'; break
        except BaseException:
            restore()
            if report: report(dict(event='interrupted',evaluations=used,accepted_steps=accepted), opt)
            raise
        current=flat(parameters)
        matches=[x for x in evaluations if torch.equal(x[0],current)]
        if not matches:
            restore(); raise RuntimeError('accepted parameters lack evaluated objective')
        _,new_loss,gradient=matches[-1]
        start,start_loss,start_grad=evaluations[0]
        state=opt.state[parameters[0]]
        if torch.equal(start,current):
            terminal='GRADIENT_CONVERGED' if float(gradient.abs().max())<=1e-10 else 'NO_ACCEPTED_PROGRESS'
            last_loss=new_loss; break
        direction,step=state['d'],float(state['t']);gtd=float(start_grad@direction)
        if not (new_loss<=start_loss+1e-4*step*gtd+1e-15 and abs(float(gradient@direction))<=-.9*gtd+1e-15):
            restore(); terminal='LINE_SEARCH_FAILED_WOLFE_TRIAL_ROLLED_BACK'; break
        accepted+=1;last_loss=new_loss
        if report: report(dict(event='accepted',evaluations=used,accepted_steps=accepted,
                              loss=new_loss,gradient_max=float(gradient.abs().max()),wolfe_verified=True),opt)
        if float(gradient.abs().max())<=1e-10:
            terminal='GRADIENT_CONVERGED';break
    return dict(evaluations=used,accepted_steps=accepted,termination=terminal,
                last_accepted_loss=last_loss if last_loss is not None else initial_loss),opt


def train(folder, device):
    if not (folder/'zero-update-profile.json').is_file(): raise RuntimeError('profile required')
    target=folder/'F_cov';target.mkdir(exist_ok=True)
    if (target/'terminal.json').exists(): return read(target/'terminal.json')
    cfg,exp=load_experiment(folder,device);torch.set_num_threads(4)
    cal=read(folder/'calibration.json');pool=deserialize_pool(read(folder/'lbfgs-pool.json'))
    sampler=TimeSampler(cfg,exp.model.physics,exp.grid,cfg['sampling_seed'])
    obs_rng=np.random.default_rng(cfg['observation_seed'])
    support_id=hashlib.sha256((folder/'lbfgs-pool.json').read_bytes()).hexdigest()
    progress=dict(phase='Adam',adam_updates=0,lbfgs_charged=0,lbfgs_complete=0,
                  lbfgs_accepted=0,interruptions=0)
    optimizer=torch.optim.Adam(exp.parameters,lr=cfg['branch_lr'],betas=tuple(cfg['betas']),eps=cfg['eps'])
    resume=target/'accepted-state.pt';journal=target/'cost-journal.json'
    if resume.exists():
        saved=torch.load(resume,map_location=device,weights_only=False)
        assert saved['support_id']==support_id
        exp.model.load_state_dict(saved['model_state_dict']);progress=saved['progress']
        obs_rng.bit_generator.state=saved['observation_rng_state']
        sampler.rng.bit_generator.state=saved['physics_rng_state']
        exp.coverage_rng.bit_generator.state=saved['coverage_rng_state']
        torch.set_rng_state(saved['torch_rng_state'].cpu())
        exp.calls.update(saved['statistics']['objectives'])
        exp.work.update(saved['statistics']['explicit_work'])
        if journal.exists():
            cost=read(journal)
            for key in ('lbfgs_charged','lbfgs_complete'):progress[key]=max(progress[key],cost[key])
        if progress['phase']=='Adam': optimizer.load_state_dict(saved['optimizer_state_dict'])
    else: saved=None
    accepted_payload=None
    def persist(opt, event):
        nonlocal accepted_payload
        accepted_payload=dict(model_state_dict=_cpu(exp.model.state_dict()),
            optimizer_state_dict=_cpu(opt.state_dict()),optimizer_type=type(opt).__name__,
            config=cfg,calibration=cal,temperature_adapter=True,role='F_cov',
            progress=copy.deepcopy(progress),support_id=support_id,
            observation_rng_state=copy.deepcopy(obs_rng.bit_generator.state),
            physics_rng_state=copy.deepcopy(sampler.rng.bit_generator.state),
            coverage_rng_state=copy.deepcopy(exp.coverage_rng.bit_generator.state),
            torch_rng_state=torch.get_rng_state(),statistics=exp.statistics(),
            reference_read=False,accepted_state=True,event=event,created_utc=now())
        atomic_checkpoint(resume,accepted_payload)
        atomic_json(journal,progress)
    if saved is not None: accepted_payload=_cpu(saved)
    else: persist(optimizer,'initial_parent')
    started=time.perf_counter()
    try:
        if progress['phase']=='Adam':
            for step in range(progress['adam_updates']+1,cfg['branch_updates']+1):
                check_resources(device)
                groups=exp.obs.groups(obs_rng,cfg['adam_observation_times']);batch=sampler.sample()
                measure=exp.observed_measure(sampled=True)
                optimizer.zero_grad(set_to_none=True)
                lam=cfg['lambda_max']*min(step/cfg['lambda_ramp'],1.)
                _,components=exp.objective(groups,batch,cal,lam,backward=True,counter='adam',observed_measure=measure)
                check_resources(device)
                norm=torch.nn.utils.clip_grad_norm_(exp.parameters,cfg['gradient_clip'],error_if_nonfinite=True)
                optimizer.step()
                if not all(torch.isfinite(p).all() for p in exp.parameters): raise FloatingPointError('nonfinite Adam update')
                progress['adam_updates']=step;exp.calls['optimizer_updates']=step
                persist(optimizer,'accepted_adam')
                if step==1 or step%50==0:
                    record=dict(seed=cfg['seed'],step=step,gradient_norm=float(norm),**components)
                    with (target/'adam-telemetry.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record)+'\n')
                    print(json.dumps(dict(event='ADAM',seed=cfg['seed'],step=step,objective=components['objective'])),flush=True)
            progress['phase']='L-BFGS'
            # Fresh LBFGS, preserving the completed Adam state as an archive.
            atomic_checkpoint(target/'adam-complete.pt',accepted_payload)
            optimizer=torch.optim.LBFGS(exp.parameters,lr=1.,max_iter=1,max_eval=32,tolerance_grad=1e-10,
                tolerance_change=1e-14,history_size=50,line_search_fn='strong_wolfe')
            persist(optimizer,'lbfgs_initial');saved=accepted_payload
        base_accepted=progress['lbfgs_accepted']
        def charge():
            progress['lbfgs_charged']+=1;atomic_json(journal,progress)
        def objective():
            value=exp.objective(exp.obs.groups(),pool,cal,cfg['lambda_max'],backward=True,counter='complete')[0]
            progress['lbfgs_complete']+=1;atomic_json(journal,progress)
            return value
        def report(record,opt):
            progress['lbfgs_accepted']=base_accepted+record['accepted_steps']
            persist(opt,record['event'])
            with (target/'lbfgs-telemetry.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(dict(record,charged_total=progress['lbfgs_charged']))+'\n')
            if record['accepted_steps']==1 or record['accepted_steps']%10==0:
                print(json.dumps(dict(event='LBFGS',seed=cfg['seed'],**progress)),flush=True)
        result,optimizer=accepted_lbfgs(exp.parameters,objective,cfg['lbfgs_evaluations']-progress['lbfgs_charged'],
            optimizer_state=accepted_payload['optimizer_state_dict'],report=report,charge=charge,
            resource_check=lambda:check_resources(device))
        progress['lbfgs_accepted']=base_accepted+result['accepted_steps']
        if result['termination'].startswith('LINE_SEARCH_FAILED'): raise FloatingPointError(result['termination'])
        persist(optimizer,'valid_fixed_endpoint')
        atomic_checkpoint(target/'checkpoint.pt',accepted_payload)
        terminal=dict(status='VALID_FIXED_ENDPOINT',seed=cfg['seed'],role='F_cov',
            progress=progress,lbfgs=result,statistics=exp.statistics(),reference_read=False,device=device,
            current_session_seconds=time.perf_counter()-started,created_utc=now())
        atomic_json(target/'terminal.json',terminal)
        return terminal
    except BaseException as error:
        # Reuse the last durable accepted state; never serialize trial parameters.
        if accepted_payload is not None:
            accepted_payload['progress']['lbfgs_charged']=progress['lbfgs_charged']
            accepted_payload['progress']['lbfgs_complete']=progress['lbfgs_complete']
            accepted_payload['progress']['interruptions']+=1
            atomic_checkpoint(resume,accepted_payload)
        resource=isinstance(error,(ResourceStop,MemoryError,torch.OutOfMemoryError,KeyboardInterrupt))
        failure=dict(status='RESOURCE_INTERRUPTED' if resource else 'NUMERICAL_OR_ENGINEERING_FAILURE',
            error=str(error),progress=progress,traceback=traceback.format_exc(),
            accepted_parameters_and_optimizer_preserved=True,reference_read=False,
            current_session_seconds=time.perf_counter()-started,created_utc=now())
        atomic_json(target/'interruption.json',failure)
        print(json.dumps(failure),flush=True)
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['profile','train'])
    parser.add_argument('--folder',type=Path,required=True)
    parser.add_argument('--device',default='cpu')
    args=parser.parse_args()
    signal.signal(signal.SIGTERM,lambda *_: (_ for _ in ()).throw(KeyboardInterrupt('SIGTERM')))
    (profile if args.action=='profile' else train)(args.folder,args.device)


if __name__=='__main__':main()
