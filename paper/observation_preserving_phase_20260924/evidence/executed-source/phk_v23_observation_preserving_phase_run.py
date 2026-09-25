"""Frozen G/N/S preparation and finite-budget execution; no references imported."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import platform
import time
import traceback
import numpy as np
import torch
from .phk_v23_lf11 import ROOT,save_json,now,digest
from .phk_v23_b1 import require_resource
from .phk_v23_b1_observations import VisibleData
from .phk_v23_lf11_elimination import serialize_pool,deserialize_pool
from .phk_v23_lf11_v_continue import continued_lbfgs
from .phk_v23_observation_preserving_phase import CompletionExperiment,CompletionSampler,A,B,SEGMENTS

RUN=ROOT/'outputs/runs/20260924-observation-preserving-phase'
OLD=ROOT/'outputs/runs/20260921-b1-second-cycle-phase-gap/seed-29'
CONFIG=ROOT/'configs/phk_v23/observation_preserving_phase_20260924.json'
ARMS=('G','N','S')


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))


def inputs(cfg,arm,device='cpu'):
    endpoint=torch.load(ROOT/cfg['parent'],map_location='cpu',weights_only=False)
    if not endpoint['temperature_adapter']:raise ValueError('Base temperature adapter missing')
    exp=CompletionExperiment(cfg,endpoint['model_state_dict'],VisibleData(ROOT/cfg['sparse']),arm,device)
    return exp,read(ROOT/cfg['base_calibration'])


def prepare():
    if (RUN/'prepared.json').exists():raise FileExistsError('Preparation already frozen')
    if read(RUN/'fixed-support-bound.json')['status']!='FIXED_SUPPORT_NECESSARY_CONDITION_PASSED':
        raise ValueError('FIXED_SUPPORT_CANNOT_MEET_PRIMARY_TARGET')
    cfg=read(OLD/'frozen-config.json')
    cfg.update(task_id='PCM-20260924-OBSERVATION-PRESERVING-PHASE-01',
        run=RUN.relative_to(ROOT).as_posix(),parent=(OLD/'E/checkpoint.pt').relative_to(ROOT).as_posix(),
        base_calibration=(OLD/'calibration.json').relative_to(ROOT).as_posix(),
        base_config=(OLD/'frozen-config.json').relative_to(ROOT).as_posix(),
        source_commit='a96303c2110ae1a79984ed7dcddf0c01ab07bec1',
        execution_order=list(ARMS),branch_updates=600,lbfgs_evaluations=200,branch_lr=1e-4,
        betas=[.9,.999],eps=1e-8,gradient_clip=10.,lambda_max=.1,lambda_ramp=None,
        correction_seed=2901,d_sampling_seed=740129,complement_sampling_seed=740229,
        fixed_pool_seed=750129,independent_D_audit_seed=760129,support=[A,B],
        correction_parameters=dict(N=1217,G=1217,S=7749),
        base_identity='old B1 E/29 endpoint; all base parameters frozen',
        source_b1=OLD.relative_to(ROOT).as_posix(),checkpoint_steps=[600],
        windows=[list(v) for v in SEGMENTS],window_masses=[(hi-lo)/2.5 for lo,hi in SEGMENTS],
        core_physics='unchanged raw phase, original cell thermal including latent heat and phase BC',
        formal_ood=False,confirmation_authorized=False)
    exp,cal=inputs(cfg,'G')
    fixed_sampler=CompletionSampler(cfg,exp.model.physics,exp.grid,750129,750129)
    fixed_sampler.outside.rng=fixed_sampler.inside.rng
    fixed=fixed_sampler.sample(fixed=True)
    audit=CompletionSampler(cfg,exp.model.physics,exp.grid,760129,760229).sample(audit=True)
    save_json(RUN/'fixed-pool.json',serialize_pool(fixed));save_json(RUN/'D-audit-pool.json',serialize_pool(audit))
    # Dry sampling determines the exact powered-query cap before optimization.
    sampler=CompletionSampler(cfg,exp.model.physics,exp.grid)
    rng=np.random.default_rng(cfg['observation_seed']);adam_queries=0;zero_queries=0
    def count(groups,pool):
        ts=sorted(set(groups)|set(pool['times']))
        powered=sum(float(exp.model.physics.waveform(torch.tensor(t,dtype=torch.float64)))!=0 for t in ts)
        return int(powered),len(ts)-powered
    for _ in range(600):
        power,zero=count(exp.obs.groups(rng,4),sampler.sample());adam_queries+=power;zero_queries+=zero
    per_fixed,zfixed=count(exp.obs.groups(),fixed)
    cfg['budgets']=dict(adam_updates=1800,complete_evaluations=600,
        training_forward_solves_G=adam_queries+200*per_fixed,
        training_adjoint_solves_G=adam_queries+200*per_fixed,
        G_adam_powered_queries=adam_queries,G_complete_powered_queries=per_fixed,
        G_zero_drive_queries_at_full_budget=zero_queries+200*zfixed,
        training_forward_solves_N=0,training_forward_solves_S=0,
        native_readout_forward=282,native_readout_adjoint=0)
    save_json(CONFIG,cfg);save_json(RUN/'frozen-config.json',cfg);save_json(RUN/'calibration.json',cal)
    save_json(RUN/'input-manifest.json',dict(task_id=cfg['task_id'],parent=cfg['parent'],
        parent_sha256=digest(ROOT/cfg['parent']),visible_data=cfg['sparse'],visible_sha256=digest(ROOT/cfg['sparse']),
        base_config=cfg['base_config'],base_calibration=cfg['base_calibration'],
        source_commit=cfg['source_commit'],scientific_optimizer_updates=0,new_parents=0,
        new_support_or_reference_solves=0,created_utc=now(),
        runtime=dict(python=platform.python_version(),torch=torch.__version__)))
    save_json(RUN/'prepared.json',dict(status='FROZEN_INPUTS_AWAITING_NUMERICAL_QUALIFICATION',
        task_id=cfg['task_id'],reference_used_only_by_separate_feasibility_diagnostic=True,
        training_reference_read=False,counts=cfg['budgets']))
    print(json.dumps(cfg['budgets']),flush=True)


def memory_snapshot():
    import os
    if os.name=='nt':
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(k,ctypes.c_size_t) for k in
                ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage',
                 'QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage','PrivateUsage')]
        c=Counters();c.cb=ctypes.sizeof(c)
        kernel=ctypes.WinDLL('kernel32');kernel.GetCurrentProcess.restype=wintypes.HANDLE
        query=ctypes.WinDLL('psapi').GetProcessMemoryInfo
        query.argtypes=[wintypes.HANDLE,ctypes.c_void_p,wintypes.DWORD]
        query.restype=wintypes.BOOL
        if not query(kernel.GetCurrentProcess(),ctypes.byref(c),c.cb):
            raise ctypes.WinError()
        return dict(peak_working_set_bytes=int(c.PeakWorkingSetSize),private_bytes=int(c.PrivateUsage))
    import resource
    return dict(peak_rss_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)*1024)


def profile(cfg,arm,perturbed=False):
    if perturbed and arm=='S':raise ValueError('Only the predeclared N/G perturbation is used')
    label=('perturbed-' if perturbed else '')+arm
    path=RUN/f'profile-{label}.json'
    if path.exists():raise FileExistsError('Profile already complete; do not repeat')
    exp,cal=inputs(cfg,arm);pool=deserialize_pool(read(RUN/'fixed-pool.json'))
    if perturbed:
        with torch.no_grad():exp.model.correction.net[-1].bias.fill_(.125)
    t=time.perf_counter()
    _,parts=exp.objective(exp.obs.groups(),pool,cal,backward=True)
    grad=torch.cat([p.grad.reshape(-1) for p in exp.parameters])
    record=dict(arm=arm,parameters=grad.numel(),objective=parts,gradient_norm=float(torch.linalg.vector_norm(grad)),
        elapsed_seconds=time.perf_counter()-t,statistics=exp.statistics(),
        optimizer_updates=0,full_objective=arm=='G',reference_read=False,passes=1,
        correction_output_bias=.125 if perturbed else 0.)
    if not torch.isfinite(grad).all():raise FloatingPointError('Invalid profile gradient')
    if arm!='G' and exp.layer.backend.counts.forward_solves!=0:raise ValueError('Unneeded N/S electric solves')
    np.save(RUN/f'profile-gradient-{label}.npy',grad.detach().numpy())
    save_json(RUN/f'profile-{label}-objective.json',record)
    record['memory']=memory_snapshot()
    save_json(path,record);print(json.dumps(record),flush=True)


def save_endpoint(path,exp,optimizer,cfg,updates,**extra):
    # Frozen base is referenced by its immutable input record, not recopied as a trainable head.
    torch.save(dict(schema_id='observation-preserving-phase-v1',arm=exp.arm,
        correction_state_dict=exp.model.correction.state_dict(),base_checkpoint=cfg['parent'],
        base_sha256=read(RUN/'input-manifest.json')['parent_sha256'],
        config=cfg,optimizer_state_dict=optimizer.state_dict(),adam_updates=updates,
        statistics=exp.statistics(),reference_read=False,**extra),path)


def train(cfg,device):
    if read(RUN/'qualification.json')['status']!='READY_FOR_FIXED_THREE_ARM_DEVELOPMENT':
        raise ValueError('Numerical preparation not qualified')
    endpoints=[]
    for arm in ARMS:
        folder=RUN/arm;folder.mkdir(exist_ok=False)
        exp,cal=inputs(cfg,arm)
        base_state={k:v.detach().cpu().clone() for k,v in exp.model.base.state_dict().items()}
        sampler=CompletionSampler(cfg,exp.model.physics,exp.grid)
        rng=np.random.default_rng(cfg['observation_seed'])
        optimizer=torch.optim.Adam(exp.parameters,lr=1e-4,betas=(.9,.999),eps=1e-8)
        started=time.perf_counter();completed=0
        try:
            with (folder/'adam-telemetry.jsonl').open('x',encoding='utf-8') as log:
                for step in range(1,601):
                    groups=exp.obs.groups(rng,4);pool=sampler.sample()
                    optimizer.zero_grad(set_to_none=True)
                    _,parts=exp.objective(groups,pool,cal,backward=True,counter='adam')
                    norm=torch.nn.utils.clip_grad_norm_(exp.parameters,10.,error_if_nonfinite=True)
                    optimizer.step();completed=step;exp.calls['optimizer_updates']=step
                    if not all(torch.isfinite(p).all() for p in exp.parameters):raise FloatingPointError('Nonfinite accepted Adam state')
                    if step==1 or step%50==0:
                        record=dict(arm=arm,adam=step,gradient_norm=float(norm),components=parts,statistics=exp.statistics())
                        log.write(json.dumps(record,allow_nan=False)+'\n');log.flush()
                        print(json.dumps(dict(arm=arm,adam=step,objective=parts['objective'])),flush=True)
            save_endpoint(folder/'adam-600.pt',exp,optimizer,cfg,600)
            fixed=deserialize_pool(read(RUN/'fixed-pool.json'))
            with (folder/'lbfgs-telemetry.jsonl').open('x',encoding='utf-8') as log:
                def record(item):
                    log.write(json.dumps(item,allow_nan=False)+'\n');log.flush()
                    if item['accepted_steps']==1 or item['accepted_steps']%10==0:print(json.dumps(dict(arm=arm,**item)),flush=True)
                result,optimizer=continued_lbfgs(exp.parameters,
                    lambda:exp.objective(exp.obs.groups(),fixed,cal,backward=True,counter='complete')[0],200,record)
            if result['termination'].startswith(('NONFINITE','LINE_SEARCH_FAILED')):
                raise FloatingPointError(result['termination'])
            if not all(torch.equal(base_state[k],v.detach().cpu()) for k,v in exp.model.base.state_dict().items()):
                raise RuntimeError('Frozen base identity changed')
            stats=exp.statistics();count=stats['electrical']
            if arm in ('N','S'):
                assert count['forward_solves']==count['adjoint_solves']==0
            else:
                assert count['forward_solves']<=cfg['budgets']['training_forward_solves_G']
                assert count['adjoint_solves']<=cfg['budgets']['training_adjoint_solves_G']
            save_endpoint(folder/'checkpoint.pt',exp,optimizer,cfg,600,lbfgs=result)
            terminal=dict(status='VALID_FIXED_ENDPOINT',arm=arm,adam_updates=600,lbfgs=result,
                elapsed_seconds=time.perf_counter()-started,statistics=stats,base_exactly_preserved=True,reference_read=False)
            save_json(folder/'terminal.json',terminal);endpoints.append(terminal)
            print(json.dumps(dict(completed=arm,seconds=terminal['elapsed_seconds'])),flush=True)
        except BaseException as error:
            save_json(folder/'failure.json',dict(status='INVALID_OR_INCOMPLETE',completed_updates=completed,
                error=str(error),traceback=traceback.format_exc(),statistics=exp.statistics()))
            raise
    save_json(RUN/'all-endpoints-locked.json',dict(status='ALL_THREE_FIXED_ENDPOINTS_LOCKED',
        objects=endpoints,created_utc=now(),reference_read=False))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['prepare','profile','train']);p.add_argument('--arm',choices=ARMS)
    p.add_argument('--device',default='cpu');p.add_argument('--resource',type=Path)
    p.add_argument('--perturbed',action='store_true')
    a=p.parse_args();torch.set_num_threads(4)
    if a.action=='prepare':prepare();return
    cfg=read(RUN/'frozen-config.json')
    if a.action=='profile':profile(cfg,a.arm,a.perturbed)
    else:require_resource(a.resource,a.device,cfg);train(cfg,a.device)


if __name__=='__main__':main()
