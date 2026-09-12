"""Guarded, bounded R/G/N (and conditional D_N) execution.

The main comparison must finish and trigger the frozen electrical-block rule.
R reuses exactly the existing Adam1000 prefix and performs only its new 200
fixed evaluations. No scientific conditional run starts during preparation of
this source file or its isolated kernel tests.
"""
from __future__ import annotations
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

import numpy as np
import torch

from .phk_v23_lf11 import ROOT,SparseData,PhysicsSampler,save_json,now,digest
from .phk_v23_lf11_followup_fit import fit_model,fit_metrics
from .phk_v23_lf11_v_continue import continued_lbfgs
from .phk_v23_lf11_joint import RUN,checkpoint,physics_audit
from .phk_v23_lf11_joint_normalization import calibrate,batch_objective,fixed_objective


def prepare(main_root=RUN):
    main_root=Path(main_root).resolve()
    decision=json.loads((main_root/'conditional-decision.json').read_text())
    proof=json.loads((main_root/'compute-closure.json').read_text())
    if not decision['triggered'] or not proof['compute_stopped_before_reference_read']:
        raise PermissionError('both frozen conditions and real main closure are required')
    root=main_root/'conditional'
    root.mkdir(exist_ok=False)
    cfg=json.loads((main_root/'frozen-config.json').read_text())
    cfg.update(roles=['R','G','N'],branch_updates=1000,lbfgs_evaluations=200,
               checkpoint_steps=[500,1000],main_root=str(main_root.relative_to(ROOT)),
               conditional_execution_authorized=True,
               max_workers=min(3,max(1,(os.cpu_count() or 4)//cfg['cpu_threads'])),
               conditional_followup_rule='D_N only if N has the same declared positive layer against both R and G; layers stay separate')
    cal=json.loads((main_root/'calibration.json').read_text())
    saved=torch.load(main_root/'parent.pt',map_location='cpu',weights_only=False)
    torch.set_num_threads(cfg['cpu_threads'])
    model=fit_model(cfg,saved['model_state_dict'],True)
    pools=torch.load(main_root/'fixed-pools.pt',map_location='cpu',weights_only=False)
    normalization=calibrate(model,cfg,cal,pools['calibration'])
    save_json(root/'normalization.json',normalization)
    save_json(root/'frozen-config.json',cfg);save_json(root/'calibration.json',cal)
    for name in ('fixed-pools.pt','parent.pt','parent-visible.json','parent-physics-audit.json'):
        shutil.copy2(main_root/name,root/name)
    save_json(root/'trigger-provenance.json',decision)
    sources=('pinn_pcm_sci/phk_v23_lf11_joint_conditional.py',
             'pinn_pcm_sci/phk_v23_lf11_joint_normalization.py',
             'pinn_pcm_sci/phk_v23_lf11_joint.py',
             'pinn_pcm_sci/phk_v23_lf11_v_continue.py')
    save_json(root/'training-source.json',{'recorded_before_conditional_updates':True,
              'files':{name:digest(ROOT/name) for name in sources}})
    if not normalization['identifiable']:
        save_json(root/'campaign.json',{'status':'NOT_RUN_UNIDENTIFIABLE_CALIBRATION','results':{},
                  'adam_updates':0,'lbfgs_evaluations':0,'reference_read':False,'recorded_utc':now()})
    return root


def worker(root,role):
    root=Path(root);cfg=json.loads((root/'frozen-config.json').read_text())
    if not cfg.get('conditional_execution_authorized') or role not in cfg['roles']:
        raise PermissionError('role not authorized by the bounded conditional controller')
    norm=json.loads((root/'normalization.json').read_text())
    if not norm['identifiable']:raise ValueError('unidentifiable fixed normalization')
    torch.set_num_threads(cfg['cpu_threads'])
    cal=json.loads((root/'calibration.json').read_text())
    pools=torch.load(root/'fixed-pools.pt',map_location='cpu',weights_only=False)
    data=SparseData(ROOT/cfg['sparse']);main=ROOT/cfg['main_root']
    source=main/'P_U/adam-1000.pt' if role=='R' else main/'parent.pt'
    saved=torch.load(source,map_location='cpu',weights_only=False)
    if role=='R' and (saved['updates']!=1000 or saved['role']!='P_U'):
        raise ValueError('R requires the actual predeclared raw Adam1000 prefix')
    model=fit_model(cfg,saved['model_state_dict'],True)
    folder=root/role;folder.mkdir(exist_ok=False)
    optimizer=None;completed=0;began=now();start=time.perf_counter()
    try:
        if role!='R':
            optimizer=torch.optim.Adam(model.parameters(),lr=cfg['branch_lr'],betas=tuple(cfg['betas']),eps=cfg['eps'])
            rng=np.random.default_rng(cfg['observation_seed']);sampler=PhysicsSampler(data,cfg,cfg['sampling_seed'],model.physics)
            with (folder/'adam-telemetry.jsonl').open('x',encoding='utf-8') as log:
                for step in range(1,cfg['branch_updates']+1):
                    idx,ng=data.indices(rng,cfg['data_points']);pb,bc_ic=sampler.interior(False),sampler.boundary_initial()
                    optimizer.zero_grad(set_to_none=True)
                    parts,obs=batch_objective(model,data,cfg,cal,norm,role,step,idx,ng,pb,bc_ic)
                    loss=sum(parts.values())
                    if not torch.isfinite(loss):raise FloatingPointError('nonfinite conditional objective')
                    loss.backward()
                    grad_norm=torch.nn.utils.clip_grad_norm_(model.parameters(),cfg['gradient_clip'],error_if_nonfinite=True)
                    optimizer.step();completed=step
                    if not all(torch.isfinite(p).all() for p in model.parameters()):raise FloatingPointError('nonfinite conditional parameters')
                    if step==1 or step%100==0:
                        row={'step':step,'loss':float(loss.detach()),'gradient_norm':float(grad_norm),
                             'components':{k:float(v.detach()) for k,v in parts.items()}}
                        log.write(json.dumps(row,allow_nan=False)+'\n');log.flush()
                        print(json.dumps({'role':role,**row}),flush=True)
                    if step in cfg['checkpoint_steps']:
                        checkpoint(folder/f'adam-{step}.pt',model,optimizer,cfg,cal,role,step,
                            optimizer_phase='Adam',normalization=norm,
                            observation_rng_state=copy.deepcopy(rng.bit_generator.state),
                            interior_rng_state=copy.deepcopy(sampler.rng.bit_generator.state),
                            boundary_rng_state=copy.deepcopy(sampler.bc_rng.bit_generator.state),reference_read=False)
        with (folder/'lbfgs-telemetry.jsonl').open('x',encoding='utf-8') as log:
            def record(row):
                log.write(json.dumps(row,allow_nan=False)+'\n');log.flush()
                if row['accepted_steps']==1 or row['accepted_steps']%20==0:print(json.dumps({'role':role,'lbfgs':row}),flush=True)
            result,optimizer=continued_lbfgs(model.parameters(),
                lambda:fixed_objective(model,data,cfg,cal,norm,role,pools['lbfgs']),cfg['lbfgs_evaluations'],record)
        checkpoint(folder/'checkpoint.pt',model,optimizer,cfg,cal,role,1000,
                   optimizer_phase='L-BFGS',normalization=norm,lbfgs_result=result,
                   reused_Adam_prefix=role=='R',new_Adam_updates=completed,reference_read=False)
        visible=fit_metrics(model,data,cfg);audit=physics_audit(model,cfg,pools['audit'])
        if not visible['finite'] or not np.isfinite([audit['J_U'],audit['boundary'],audit['initial']]).all():
            raise FloatingPointError('nonfinite conditional endpoint')
        outcome={'role':role,'status':'VALID_FIXED_ENDPOINT','adam_updates':completed,
                 'trajectory_Adam_updates':1000,'reused_Adam_prefix':role=='R','source':str(source.relative_to(ROOT)),
                 'lbfgs':result,'visible':visible,'fixed_physics_audit':audit,
                 'started_utc':began,'completed_utc':now(),'elapsed_seconds_internal':time.perf_counter()-start,
                 'reference_read':False,'pid':os.getpid()}
    except Exception as exc:
        checkpoint(folder/'invalid-checkpoint.pt',model,optimizer,cfg,cal,role,completed,
                   normalization=norm,validity='INVALID',exception=str(exc))
        outcome={'role':role,'status':'INVALID','adam_updates':completed,'exception':str(exc),
                 'traceback':traceback.format_exc(),'completed_utc':now(),'pid':os.getpid()}
    save_json(folder/'result.json',outcome)
    return outcome


def prepare_dn(conditional_root):
    """Start a distinct later batch only after the saved R/G/N decision."""
    source=Path(conditional_root).resolve()
    decision=json.loads((source/'followup-decision.json').read_text())
    proof=json.loads((source/'compute-closure.json').read_text())
    if not decision.get('D_N_triggered') or not proof['compute_stopped_before_reference_read']:
        raise PermissionError('N must have the same positive layer against both R and G')
    root=source/'dn';root.mkdir(exist_ok=False)
    cfg=json.loads((source/'frozen-config.json').read_text())
    cfg.update(roles=['D_N'],max_workers=1)
    save_json(root/'frozen-config.json',cfg)
    for name in ('normalization.json','calibration.json','parent.pt','fixed-pools.pt',
                 'parent-visible.json','parent-physics-audit.json'):
        shutil.copy2(source/name,root/name)
    save_json(root/'trigger-provenance.json',decision)
    shutil.copy2(source/'training-source.json',root/'training-source.json')
    return root


def launch(root):
    root=Path(root);cfg=json.loads((root/'frozen-config.json').read_text())
    norm=json.loads((root/'normalization.json').read_text())
    if not norm['identifiable']:return
    if any((root/role).exists() for role in cfg['roles']):raise FileExistsError('no implicit conditional rerun')
    pending=list(cfg['roles']);running={};finished={};handles=[];worker_pids={}
    try:
        while pending or running:
            while pending and len(running)<cfg['max_workers']:
                role=pending.pop(0);out=(root/f'{role}-console.jsonl').open('x',encoding='utf-8');handles.append(out)
                flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
                p=subprocess.Popen([sys.executable,'-m','pinn_pcm_sci.phk_v23_lf11_joint_conditional','worker',
                                    '--root',str(root),'--role',role],cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,creationflags=flags)
                running[role]=p;worker_pids[role]=p.pid
                print(json.dumps({'conditional_worker_started':role,'pid':p.pid}),flush=True)
            for role,p in list(running.items()):
                code=p.poll()
                if code is None:continue
                finished[role]=code;del running[role]
                print(json.dumps({'conditional_worker_finished':role,'exit_code':code}),flush=True)
            if running:time.sleep(.5)
    finally:
        for p in running.values():
            if p.poll() is None:p.terminate()
            p.wait()
        for handle in handles:handle.close()
    results={}
    for role in cfg['roles']:
        path=root/role/'result.json'
        results[role]=json.loads(path.read_text()) if path.exists() else {
            'role':role,'status':'INVALID','adam_updates':None,'reason':'worker ended without a result','exit_code':finished[role]}
    save_json(root/'campaign.json',{'status':'CONDITIONAL_TRAINING_COMPLETE','results':results,
              'recorded_utc':now(),'adam_updates':sum(r['adam_updates'] or 0 for r in results.values()),
              'lbfgs_evaluations':sum(r.get('lbfgs',{}).get('evaluations',0) for r in results.values()),
              'reference_read':False,'stress_read':False,'cloud_instance_started':False,
              'reused_R_Adam_updates_not_counted_as_new':1000 if 'R' in results else 0})
    save_json(root/'compute-closure.json',{'training_complete':True,'compute_stopped_before_reference_read':True,
              'training_worker_pids':worker_pids,'actual_exit_codes':finished,'all_training_workers_reaped':True,
              'recorded_utc':now(),'device':'cpu','cloud_instance_started':False,'stress_read':False})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','prepare-dn','launch','worker'))
    p.add_argument('--root',type=Path,default=RUN);p.add_argument('--role',choices=('R','G','N','D_N'))
    a=p.parse_args()
    if a.action=='prepare':print(prepare(a.root))
    elif a.action=='prepare-dn':print(prepare_dn(a.root))
    elif a.action=='launch':launch(a.root)
    else:
        if a.role is None:p.error('worker requires --role')
        worker(a.root,a.role)
