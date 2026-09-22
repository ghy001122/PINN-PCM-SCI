"""B1 preparation and separately resource-authorized fixed-endpoint execution.

Training reads only the physically field-filtered package and known physics.
References are used by a separate array-only scorer after all endpoints lock.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import time
import traceback
import numpy as np
import torch

from .phk_v23_lf11 import ROOT,save_json,now
from .phk_v23_b1_observations import VisibleData,VisibleTimes,visible_baseline,export,WINDOW
from .phk_v23_lf11_clean_confirmation import BoundedElectricExperiment,prepare_seed
from .phk_v23_lf11_training_coupling import SoftExperiment,train as train_soft
from .phk_v23_lf11_elimination import train_role
from .phk_v23_lf11_elimination_predict import infer_time
from .phk_v23_lf11_elimination_physics import grid_for
from .phk_v23_lf11_followup_fit import fit_model
from .phk_v23_lf11_electric_layer import ElectricalLayer

CONFIG=ROOT/'configs/phk_v23/lf11_b1_sprint.json'
DEADLINE=None


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def deadline_check():
    if DEADLINE is not None and time.time()>=DEADLINE:
        raise TimeoutError('BUDGET_INCOMPLETE: approved wall-clock allocation exhausted')


def instrument_model(model):
    counts=dict(head_forward_calls=0,head_coordinate_queries=0,head_output_derivative_calls=0)
    def forward(module,args,output):
        deadline_check()
        counts['head_forward_calls']+=1
        counts['head_coordinate_queries']+=len(args[0])
        if output.requires_grad:
            def differentiated(gradient):
                counts['head_output_derivative_calls']+=1
                return gradient
            output.register_hook(differentiated)
    for head in model.heads.values():
        head.register_forward_hook(forward)
    return counts


class B1Electric(BoundedElectricExperiment):
    observation_type=VisibleTimes

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.model_work=instrument_model(self.model)

    def statistics(self):
        return {**super().statistics(),'model_work':dict(self.model_work)}


class B1Soft(SoftExperiment):
    observation_type=VisibleTimes

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.model_work=instrument_model(self.model)

    def statistics(self):
        return {**super().statistics(),'model_work':dict(self.model_work)}


def validate(cfg):
    assert cfg['task_id']=='PCM-20260921-FINAL-SPRINT-B1-01'
    assert cfg['phase_missing_window']==list(WINDOW)
    assert cfg['confirmation']['seeds']==[29,43] and cfg['paired_roles']==['E','D_E','F_raw']
    assert cfg['case_spec']['pulse_starts']==[0.,1.01]
    assert cfg['branch_updates']==1500 and cfg['lbfgs_evaluations']==300
    assert cfg['confirmation']['parent_adam']==2400
    assert cfg['confirmation']['parent_lbfgs_by_head']==dict(potential=200,temperature=200,phase=200)
    assert cfg['electric_spatial_reduction']=='sampled' and cfg['eta_bal']==1.
    assert cfg['source_parent']=='fresh observation-only fit'
    assert cfg['parent']=='FRESH_B1_PARENT_PER_SEED'
    return cfg


def prepare(cfg):
    """No untrained neural forward or electric solve; only data and coordinates."""
    run=ROOT/cfg['run'];run.mkdir(parents=True,exist_ok=True)
    if (run/'prepared.json').exists():
        raise FileExistsError('B1 inputs already frozen; reuse them')
    stats=export(ROOT/cfg['source_sparse'],ROOT/cfg['sparse'])
    from .phk_v23_lf11_protocol import powered_count
    powered=powered_count(cfg['case_spec'])
    assert powered==278
    cfg['budgets']['readout_forward']=7*2*powered
    # Existence-only check: reference values never enter training preparation.
    missing=[p for p in cfg['evaluation_reference_files'] if not (ROOT/p).is_file()]
    if missing:
        raise FileNotFoundError('B1 evaluation asset missing; no reference generation: '+', '.join(missing))
    save_json(run/'frozen-config.json',cfg)
    save_json(run/'visible-statistics.json',stats)
    save_json(run/'prepared.json',dict(status='PREPARED_NOT_TRAINED',task_id=cfg['task_id'],
        training_input=cfg['sparse'],reference_arrays_read=False,all_required_reference_paths_present=True,
        scientific_optimizer_updates=0,scientific_electric_solves=0,
        actual_nonzero_readout_times=powered,readout_forward_limit=7*2*powered,
        figure_times=cfg['figure_times'],created_utc=now()))
    print(json.dumps(stats),flush=True)


def require_resource(approval,device,cfg):
    global DEADLINE
    if approval is None:
        raise PermissionError('Stage 3 requires this task\'s enabled GPU instance and resource approval')
    a=read(approval)
    required=('instance_id','gpu_model','staging_path','recovery_path','shutdown_policy','approval_record')
    if a.get('task_id')!=cfg['task_id'] or a.get('authorized') is not True or a.get('instance_enabled') is not True:
        raise PermissionError('No task-specific enabled-instance approval')
    if any(not a.get(k) for k in required):
        raise ValueError('Resource identity and recovery/shutdown fields required')
    if a.get('cost_policy')!='USER_NO_COST_LIMIT' and (a.get('max_cost') is None or a['max_cost']<0):
        raise ValueError('Approved cost cap or explicit user no-cost-limit instruction required')
    if not device.startswith('cuda') or not torch.cuda.is_available():
        raise RuntimeError('Authorized long execution requires the confirmed platform GPU')
    # The 2026-09-21 user approved completion with no cost budget. Fixed
    # scientific counts still bound execution; do not invent a paid-time cap.
    if a.get('wallclock_policy')=='FROZEN_WORK_ONLY':
        if a.get('cost_policy')!='USER_NO_COST_LIMIT':
            raise ValueError('Frozen-work-only execution requires explicit no-cost-limit approval')
        DEADLINE=None
    else:
        if not a.get('deadline_epoch') or not a.get('max_wallclock_hours',0)>0:
            raise ValueError('Set one approved absolute deadline for train and readout together')
        DEADLINE=float(a['deadline_epoch']);deadline_check()
    return a


def train(cfg,device):
    run=ROOT/cfg['run']
    if list(run.glob('seed-*')):
        raise FileExistsError('Existing scientific trajectory; no automatic restart or best-checkpoint selection')
    if read(run/'prepared.json')['status']!='PREPARED_NOT_TRAINED':
        raise ValueError('visible inputs not prepared')
    configs={}
    try:
        # Establish BOTH fresh parents/calibrations before the six branches.
        for seed in cfg['confirmation']['seeds']:
            started=time.perf_counter()
            configs[seed]=prepare_seed(run/f'seed-{seed}',cfg,seed,'F_raw',device,
                data_type=VisibleData,observation_type=VisibleTimes,electric_type=B1Electric,
                model_observer=instrument_model)
            save_json(run/f'seed-{seed}/parent-and-calibration-work.json',dict(
                elapsed_seconds=time.perf_counter()-started,parent_forward_solves=0,parent_adjoint_solves=0,
                calibration=read(run/f'seed-{seed}/calibration.json')['statistics']))
        for seed,role in cfg['execution_order']:
            c=configs[seed];folder=run/f'seed-{seed}'
            deadline_check()
            started=time.perf_counter()
            if role=='F_raw':
                if not train_soft(folder,role,c,device,experiment_type=B1Soft,data_type=VisibleData):
                    raise RuntimeError('Invalid soft endpoint; scientific comparison is incomplete')
            else:
                train_role(folder,'P_E' if role=='E' else 'D_E',c,device,output_role=role,
                           experiment_type=B1Electric,data_type=VisibleData)
            endpoint=read(folder/role/'terminal.json')
            save_json(folder/role/'execution-work.json',dict(elapsed_seconds=time.perf_counter()-started,
                model_work=endpoint['statistics']['model_work'],electrical=endpoint['statistics']['electrical'],
                objectives=endpoint['statistics']['objectives']))
            if endpoint['lbfgs']['termination'].startswith(('NONFINITE','LINE_SEARCH_FAILED')):
                raise FloatingPointError('Invalid branch line search; stop affected campaign')
        terminal=[]
        for seed,role in cfg['execution_order']:
            item=read(run/f'seed-{seed}'/role/'terminal.json')
            if item['status']!='VALID_FIXED_ENDPOINT' or item['adam_updates']!=1500:
                raise ValueError('Not all fixed endpoints completed')
            # Numeric line-search failures do not become legitimate convergence.
            if item['lbfgs']['termination'].startswith(('NONFINITE','LINE_SEARCH_FAILED')):
                raise ValueError('Numerically invalid L-BFGS endpoint: '+role)
            terminal.append(dict(seed=seed,role=role,terminal=item))
        parents=[read(run/f'seed-{s}/common-fit/fit-summary.json') for s in cfg['confirmation']['seeds']]
        for p in parents:
            if any(v['termination'].startswith(('NONFINITE','LINE_SEARCH_FAILED')) for v in p['lbfgs'].values()):
                raise ValueError('Numerically invalid parent')
        counts=dict(adam=sum(v['adam_updates'] for v in parents)+sum(v['terminal']['adam_updates'] for v in terminal),
            complete_evaluations=sum(v['complete_evaluations'] for v in parents)+sum(v['terminal']['lbfgs']['evaluations'] for v in terminal))
        for name in ('forward_solves','adjoint_solves','zero_drive_queries'):
            counts['training_'+name]=sum(v['terminal']['statistics']['electrical'][name] for v in terminal)
            counts['calibration_'+name]=sum(read(run/f'seed-{s}/calibration.json')['statistics']['electrical'][name] for s in (29,43))
        assert counts['adam']==13800 and counts['complete_evaluations']<=3000
        assert counts['training_forward_solves']<=108000 and counts['training_adjoint_solves']<=108000
        assert counts['calibration_forward_solves']<=1000 and counts['calibration_adjoint_solves']==0
        save_json(run/'all-endpoints-locked.json',dict(status='ALL_SIX_FIXED_ENDPOINTS_LOCKED',
            objects=terminal,parents=parents,counts=counts,reference_read=False,created_utc=now()))
    except Exception as error:
        save_json(run/'execution-failure.json',dict(status='BUDGET_INCOMPLETE' if isinstance(error,TimeoutError) else 'INVALID_OR_INCOMPLETE',
            error=str(error),traceback=traceback.format_exc(),reference_read=False))
        raise


def readout(cfg,device):
    run=ROOT/cfg['run']
    locked=read(run/'all-endpoints-locked.json')
    assert locked['status']=='ALL_SIX_FIXED_ENDPOINTS_LOCKED'
    times=np.linspace(0.,2.5,1001);data=VisibleData(ROOT/cfg['sparse'])
    objects=[(s,r) for s,r in cfg['execution_order']]+[(None,'B_E')]
    manifest=[];counts=0
    for seed,role in objects:
        oid=f'shorter/{seed}/{"F" if role=="F_raw" else role}' if seed else 'shorter/B_E'
        c=read(run/f'seed-{seed}/frozen-config.json') if seed else cfg
        state=torch.load(run/f'seed-{seed}'/role/'checkpoint.pt',map_location='cpu',weights_only=False)['model_state_dict'] if seed else None
        model=fit_model(c,state,adapter=True).to(device).eval();model.requires_grad_(False)
        work=instrument_model(model)
        record=dict(id=oid,protocol='shorter',seed=seed,role='F' if role=='F_raw' else role,origin='b1_missing_phase')
        for shape,label in (([160,80],'coarse'),([240,120],'fine')):
            work_start=dict(work);started=time.perf_counter()
            folder=run/'predictions'/oid/label
            if folder.exists():
                raise FileExistsError('Existing reader arrays; inspect recovery instead of recomputing')
            folder.mkdir(parents=True)
            grid=grid_for(model.physics,*shape);layer=ElectricalLayer(grid,model.physics.heater_width_fraction,c['linear_tolerance'])
            arrays={k:np.lib.format.open_memmap(folder/(k+'.npy'),mode='w+',dtype='float64',shape=(len(times),grid.cell_count))
                    for k in ('potential','temperature','phase','joule_density')}
            traces={}
            for i,t in enumerate(times):
                deadline_check()
                supplied={k:v[0] for k,v in visible_baseline(data,grid,np.array([t]),model.physics).items()} if role=='B_E' else None
                values,diag=infer_time(model,layer,float(t),device,'P_E',baseline_fields=supplied)
                for k,v in values.items():
                    if not np.isfinite(v).all():raise FloatingPointError(oid+'/'+k)
                    arrays[k][i]=v
                for k,v in diag.items():traces.setdefault(k,[]).append(v)
                if i%100==0:
                    for v in arrays.values():v.flush()
                    save_json(folder/'progress.json',dict(saved=i+1,total=1001,counts=layer.backend.snapshot()))
                    print(json.dumps(dict(readout=oid,grid=shape,saved=i+1)),flush=True)
            assert layer.backend.counts.forward_solves==278 and layer.backend.counts.adjoint_solves==0
            counts+=layer.backend.counts.forward_solves
            np.savez_compressed(folder/'prediction.npz',x=grid.x_centers,z=grid.z_centers,time=times,**arrays)
            np.savez_compressed(folder/'own-readout.npz',time=times,**{k:np.asarray(v) for k,v in traces.items()})
            save_json(folder/'prediction.json',dict(status='FIXED_ENDPOINT_PROJECTED_READER',id=oid,grid=shape,
                model_work={k:work[k]-work_start[k] for k in work},elapsed_seconds=time.perf_counter()-started,
                electrical_counts=layer.backend.snapshot(),reference_read=False))
            for k,v in arrays.items():
                v._mmap.close();(folder/(k+'.npy')).unlink()
            prefix='' if label=='coarse' else 'fine_'
            record[prefix+'prediction']=(folder/'prediction.npz').relative_to(ROOT).as_posix()
            record[prefix+'readout']=(folder/'own-readout.npz').relative_to(ROOT).as_posix()
        manifest.append(record)
        del model
        if device.startswith('cuda'):torch.cuda.empty_cache()
    assert counts==cfg['budgets']['readout_forward']==3892
    save_json(run/'readout-manifest.json',dict(status='ALL_FIXED_READERS_COMPLETE',objects=manifest,
        projected_forward_solves=counts,adjoint_solves=0,expected_score_records=42,reference_read=False))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('prepare','train','readout','validate'))
    p.add_argument('--config',type=Path,default=CONFIG)
    p.add_argument('--device',default='cpu')
    p.add_argument('--approval',type=Path)
    p.add_argument('--dry-run',action='store_true')
    a=p.parse_args();cfg=validate(read(a.config));torch.set_num_threads(cfg['cpu_threads'])
    if a.dry_run or a.action=='validate':
        print(json.dumps(dict(status='PARSED_NOT_EXECUTED',action=a.action,task=cfg['task_id'],
            run=cfg['run'],budgets=cfg['budgets'],resource_authorized=False)))
        return
    if a.action=='prepare':prepare(cfg);return
    require_resource(a.approval,a.device,cfg)
    if read(ROOT/cfg['run']/'frozen-config.json')!=cfg:
        raise ValueError('Prepared configuration changed')
    if a.action=='train':train(cfg,a.device)
    else:readout(cfg,a.device)


if __name__=='__main__':main()
