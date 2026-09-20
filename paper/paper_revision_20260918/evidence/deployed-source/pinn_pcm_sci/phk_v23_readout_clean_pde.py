"""Bounded frozen-reader sensitivity and two clean-parent residual ablations.

The cloud entry receives sparse observations and frozen learned states only.
It never imports a reference evaluator. Existing mathematical kernels and
accepted-state L-BFGS are reused without changing their scientific targets.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import shutil
import traceback

import numpy as np
import torch

from .phk_v23_lf11 import ROOT, SparseData, now, save_json
from .phk_v23_lf11_followup_fit import fit_model
from .phk_v23_lf11_elimination import Experiment, deserialize_pool, train_role
from .phk_v23_lf11_clean_confirmation import BoundedElectricExperiment
from .phk_v23_lf11_elimination_physics import grid_for, coordinates, fields, thermal_phase_residual
from .phk_v23_lf11_elimination_predict import baseline, infer_time
from .phk_v23_lf11_electric_layer import ElectricalLayer

CONFIG = ROOT/'configs/phk_v23/lf11_readout_clean_pde_sprint.json'
KEYS = ('potential', 'temperature', 'phase', 'joule_density')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def relative(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def approved():
    cfg = read(CONFIG)
    if cfg.get('execution_authorized') is not True:
        raise PermissionError('This bounded task is not execution-authorized.')
    assert cfg['fine_grid'] == [240, 120] and cfg['seeds'] == [29, 43]
    assert cfg['budgets']['total_forward'] == 58392
    return cfg, ROOT/cfg['run']


def gradient_vector(model):
    return torch.cat([(p.grad if p.grad is not None else torch.zeros_like(p)).reshape(-1)
                      for p in model.parameters() if p.requires_grad]).detach().cpu()


def prepare():
    cfg, run = approved()
    run.mkdir(parents=True, exist_ok=True)
    if (run/'input-manifest.json').exists():
        raise FileExistsError('Frozen inputs already prepared; reuse them.')
    records = []
    matches = []
    for case, source in cfg['historical'].items():
        for seed in cfg['seeds']:
            folder = ROOT/source/f'seed-{seed}'
            c = read(folder/'frozen-config.json')
            assert c['seed'] == seed and c['grid'] == cfg['train_grid']
            assert c['branch_updates'] == 1500 and c['lbfgs_evaluations'] == 300
            for role in cfg['historical_roles']:
                checkpoint = folder/role/'checkpoint.pt'
                if not checkpoint.is_file():
                    raise FileNotFoundError(checkpoint)
                name = f'{case}/{seed}/{"F" if role == "F_raw" else role}'
                records.append(dict(id=name,case=case,seed=seed,role=role,
                    config=relative(folder/'frozen-config.json'),checkpoint=relative(checkpoint),
                    sparse=c['sparse'],old_prediction=relative(folder/role/'projected/prediction.npz')))
            if case == 'shorter':
                # One narrowly scoped compatibility check; no scientific forward.
                parent = torch.load(folder/'parent.pt',map_location='cpu',weights_only=False)
                common = torch.load(ROOT/c['parent'],map_location='cpu',weights_only=False)
                endpoint = torch.load(folder/'E/checkpoint.pt',map_location='cpu',weights_only=False)
                state = parent['model_state_dict']
                assert state.keys() == common['model_state_dict'].keys()
                assert all(torch.equal(v,common['model_state_dict'][k]) for k,v in state.items())
                cal = read(folder/'calibration.json')
                assert endpoint['config'] == c
                assert endpoint['calibration'] == cal
                target = run/'clean-pde'/f'seed-{seed}'
                target.mkdir(parents=True,exist_ok=False)
                for name in ('parent.pt','frozen-config.json','calibration.json',
                             'lbfgs-pool.json','audit-pool.json','calibration-pool.json'):
                    shutil.copy2(folder/name,target/name)
                matches.append(dict(seed=seed,source_parent=relative(folder/'parent.pt'),
                    source_E=relative(folder/'E/checkpoint.pt'),same_common_fit_tensors=True,
                    same_config=True,same_calibration=True,pools_copied_without_regeneration=True,
                    fresh_optimizer=True,new_role='D_E'))
        folder = ROOT/source/'seed-29'
        c = read(folder/'frozen-config.json')
        records.append(dict(id=case+'/B_E',case=case,seed=None,role='B_E',
            config=relative(folder/'frozen-config.json'),checkpoint=None,sparse=c['sparse']))
    assert len(records) == 10
    save_json(run/'frozen-config.json',cfg)
    save_json(run/'input-manifest.json',dict(objects=records,parent_matches=matches,
        reference_read=False,stress_read=False,scientific_model_forwards=0,
        source_scope='eight historical endpoints, two seedless B_E, two V32 common parents'))
    print(json.dumps(dict(prepared=True,objects=10,matched_clean_parents=2)),flush=True)


def load_record(record,device):
    c = read(ROOT/record['config'])
    state = (torch.load(ROOT/record['checkpoint'],map_location='cpu',weights_only=False)
             ['model_state_dict'] if record['checkpoint'] else None)
    model = fit_model(c,state,adapter=True).to(device).eval()
    model.requires_grad_(False)
    return c,model


def predict_record(record, shape, folder, device):
    """One immutable accepted-state reader; only independent projected outputs."""
    cfg, _ = approved()
    done = folder/'prediction.json'
    if done.exists():
        evidence = read(done)
        assert evidence['id'] == record['id'] and evidence['grid'] == list(shape)
        assert (folder/'prediction.npz').is_file() and (folder/'own-readout.npz').is_file()
        return evidence
    if folder.exists():
        raise FileExistsError('Incomplete reader output requires bounded engineering recovery: '+str(folder))
    folder.mkdir(parents=True)
    c,model = load_record(record,device)
    times = np.linspace(0.,2.5,cfg['inference_times'])
    drives = model.physics.waveform(torch.tensor(times,dtype=torch.float64,device=device))
    powered = int(torch.count_nonzero(drives))
    assert powered == cfg['per_prediction_forward_limit']
    grid = grid_for(model.physics,*shape)
    layer = ElectricalLayer(grid,model.physics.heater_width_fraction,cfg['numerical_tolerance'])
    data = SparseData(ROOT/record['sparse']) if record['role']=='B_E' else None
    # Stream B_E interpolation and direct neural queries one time at a time.
    arrays = {k:np.lib.format.open_memmap(folder/(k+'.npy'),mode='w+',dtype='float64',
                shape=(len(times),grid.cell_count)) for k in KEYS}
    traces = {}
    for index,t in enumerate(times):
        supplied = ({k:v[0] for k,v in baseline(data,grid,np.asarray([t]),model.physics).items()}
                    if data is not None else None)
        values,diag = infer_time(model,layer,float(t),device,'P_E',baseline_fields=supplied)
        for k in KEYS:
            if not np.isfinite(values[k]).all():raise FloatingPointError(record['id']+'/'+k)
            arrays[k][index] = values[k]
        for k,v in diag.items():traces.setdefault(k,[]).append(v)
        assert layer.backend.counts.forward_solves <= powered
        if index % 100 == 0 or index == len(times)-1:
            for arr in arrays.values():arr.flush()
            save_json(folder/'progress.json',dict(last_saved_index=index,counts=layer.backend.snapshot(),
                id=record['id'],grid=list(shape),reference_read=False))
            print(json.dumps(dict(reader=record['id'],grid=list(shape),saved=index+1,total=len(times))),flush=True)
    assert layer.backend.counts.forward_solves == powered
    assert layer.backend.counts.adjoint_solves == 0
    np.savez_compressed(folder/'prediction.npz',x=grid.x_centers,z=grid.z_centers,time=times,**arrays)
    np.savez_compressed(folder/'own-readout.npz',time=times,**{k:np.asarray(v) for k,v in traces.items()})
    evidence=dict(status='VALID_FIXED_WEIGHT_PROJECTED_READER',id=record['id'],grid=list(shape),
        source=record,queries=len(times)*grid.cell_count,times=len(times),
        direct_network_query=data is None,baseline_rule='unchanged B_logit' if data is not None else None,
        electrical_counts=layer.backend.snapshot(),optimizer_updates=0,reference_read=False,
        stress_read=False,created_utc=now())
    save_json(done,evidence)
    for k in KEYS:
        arrays[k]._mmap.close()
        (folder/(k+'.npy')).unlink()
    del arrays,model,layer
    if device.startswith('cuda'):torch.cuda.empty_cache()
    return evidence


def checks(device):
    cfg,run=approved()
    if (run/'interface-checks.json').exists():return read(run/'interface-checks.json')
    torch.set_num_threads(4)
    records=read(run/'input-manifest.json')['objects']
    checks_out=[]
    totals=dict(forward_solves=0,adjoint_solves=0)
    for seed in cfg['seeds']:
        folder=run/'clean-pde'/f'seed-{seed}'
        c=read(folder/'frozen-config.json');cal=read(folder/'calibration.json')
        state=torch.load(folder/'parent.pt',map_location='cpu',weights_only=False)['model_state_dict']
        data=SparseData(ROOT/c['sparse'])
        pe=Experiment(c,state,data,device,'P_E');de=Experiment(c,state,data,device,'D_E')
        # Two fixed existing time nodes, including an active and an inactive one.
        pool=deserialize_pool(read(folder/'lbfgs-pool.json'))
        selected=[next(t for t in pool['times'] if .05<t<.27),
                  next(t for t in pool['times'] if .35<t<1.01)]
        pool={'times':{t:pool['times'][t] for t in selected},'initial':pool['initial']}
        groups={float(t):(i,1.) for i,t in enumerate(pe.obs.times) if i in (5,25)}
        for exp in (pe,de):exp.model.zero_grad(set_to_none=True)
        vp,parts_p=pe.objective(groups,pool,cal,.1,backward=True)
        gp=gradient_vector(pe.model)
        vd,parts_d=de.objective(groups,pool,cal,.1,backward=True)
        gd=gradient_vector(de.model)
        for key in ('observation','obs_V','obs_T','obs_phase','boundary','initial'):
            np.testing.assert_allclose(parts_p[key],parts_d[key],rtol=1e-12,atol=1e-14)
        pe.model.zero_grad(set_to_none=True)
        residual=0.
        for t,part in pool['times'].items():
            _,heat,_=pe.electric(t,True)
            r=thermal_phase_residual(pe.model,pe.grid,t,part['cells'],heat)
            f=.1*part['mass']*sum((r[k]/c['pde_scales'][k]).square().mean()
                    for k in ('thermal','phase'))/(3*max(cal['bE'],1e-12))
            f.backward();residual+=float(f.detach())
        gf=gradient_vector(pe.model)
        np.testing.assert_allclose(float(vp-vd),residual,rtol=1e-8,atol=1e-12)
        gradient_error=float(torch.linalg.vector_norm(gp-gd-gf)/max(float(torch.linalg.vector_norm(gf)),1e-12))
        assert gradient_error<1e-7
        de.model.zero_grad(set_to_none=True)
        t=next(t for t in groups if float(de.model.physics.waveform(torch.tensor(t)))>0)
        v,_,_=de.electric(t,True)
        _,pieces=de.obs.loss(de.model,groups[t],v,'D_E')
        pieces['obs_V'].backward()
        norms={head:float(torch.sqrt(sum((p.grad.square().sum() if p.grad is not None else p.new_tensor(0.))
                    for p in de.model.heads[head].parameters()))) for head in ('temperature','phase')}
        assert all(v>1e-12 for v in norms.values())
        for exp in (pe,de):
            counts=exp.layer.backend.snapshot()
            for k in totals:totals[k]+=counts[k]
        checks_out.append(dict(seed=seed,common_components_equal=True,
            full_minus_control_equals_residual=True,gradient_relative_error=gradient_error,
            voltage_observation_head_gradient_norms=norms))
    # Deterministic coordinate batching checks, no reference field access.
    for record in records:
        c,model=load_record(record,device)
        ts=np.linspace(0,2.5,1001)
        assert int(torch.count_nonzero(model.physics.waveform(torch.tensor(ts,dtype=torch.float64))))==278
        if record['role']=='B_E':continue
        grid=grid_for(model.physics,160,80)
        q=coordinates(grid,.175,device=device)[[0,153,875,2461,5670,9999,12799]]
        with torch.no_grad():
            whole=fields(model,q)
            chunks=[fields(model,q[i:i+2]) for i in range(0,len(q),2)]
        for k in ('temperature','phase'):
            torch.testing.assert_close(whole[k],torch.cat([p[k] for p in chunks]),rtol=2e-12,atol=2e-14)
    assert totals['forward_solves']<=cfg['budgets']['checks_audits_forward']
    assert totals['adjoint_solves']<=cfg['budgets']['checks_audits_adjoint']
    result=dict(status='PASS',records=checks_out,batching='same direct function',
        finite_pulse_powered_times=278,counts=totals,reference_read=False,optimizer_updates=0)
    save_json(run/'interface-checks.json',result)
    print(json.dumps(result),flush=True)
    return result


def audit_endpoints(run,device):
    """Single fixed-pool residual audit per E and D_E, no optimizer or backward."""
    dest=run/'fixed-residual-audits.json'
    if dest.exists():return read(dest)
    out={};counts=dict(forward_solves=0,adjoint_solves=0)
    for seed in (29,43):
        folder=run/'clean-pde'/f'seed-{seed}'
        c=read(folder/'frozen-config.json');cal=read(folder/'calibration.json')
        pool=deserialize_pool(read(folder/'audit-pool.json'))
        data=SparseData(ROOT/c['sparse'])
        for role in ('E','D_E'):
            source=(ROOT/read(run/'frozen-config.json')['historical']['shorter']/f'seed-{seed}'/'E/checkpoint.pt'
                    if role=='E' else folder/'D_E/checkpoint.pt')
            state=torch.load(source,map_location='cpu',weights_only=False)['model_state_dict']
            exp=Experiment(c,state,data,device,'P_E')
            _,values=exp.objective(exp.obs.groups(),pool,cal,.1)
            stat=exp.statistics()
            for k in counts:counts[k]+=stat['electrical'][k]
            out[f'{seed}/{role}']=dict(components=values,statistics=stat,source=relative(source))
    checked=read(run/'interface-checks.json')['counts']
    for k in counts:assert counts[k]+checked[k]<=500
    result=dict(records=out,counts=counts,reference_read=False,optimizer_updates=0,
                pool='same seed-specific V32 independent audit pool')
    save_json(dest,result)
    return result


def cloud(device):
    cfg,run=approved()
    if not device.startswith('cuda') or not torch.cuda.is_available():
        raise RuntimeError('The authorized long task uses a platform GPU.')
    torch.set_num_threads(4)
    if read(run/'interface-checks.json')['status']!='PASS':raise RuntimeError('interface checks pending')
    manifest=read(run/'input-manifest.json')
    historical=[]
    for record in manifest['objects']:
        historical.append(predict_record(record,cfg['fine_grid'],run/'fine-readout'/record['id'],device))
    assert sum(r['electrical_counts']['forward_solves'] for r in historical)<=2780
    failures=[]
    for seed in cfg['seeds']:
        folder=run/'clean-pde'/f'seed-{seed}';c=read(folder/'frozen-config.json')
        try:
            terminal=folder/'D_E/terminal.json'
            if not terminal.exists():
                if (folder/'D_E').exists():raise FileExistsError('Existing scientific trajectory; inspect before continuing')
                train_role(folder,'D_E',c,device,experiment_type=BoundedElectricExperiment)
            assert read(terminal)['status']=='VALID_FIXED_ENDPOINT'
            record=dict(id=f'shorter/{seed}/D_E',case='shorter',seed=seed,role='D_E',
                config=relative(folder/'frozen-config.json'),checkpoint=relative(folder/'D_E/checkpoint.pt'),
                sparse=c['sparse'])
            for shape,label in ((cfg['coarse_grid'],'coarse'),(cfg['fine_grid'],'fine')):
                predict_record(record,shape,folder/'D_E'/label,device)
        except Exception as error:
            failures.append(dict(seed=seed,error=str(error),traceback=traceback.format_exc()))
            save_json(run/'branch-failures.json',failures)
    if failures:raise RuntimeError('A branch is incomplete; other valid artifacts retained.')
    audits=audit_endpoints(run,device)
    terminals=[read(run/'clean-pde'/f'seed-{s}'/'D_E/terminal.json') for s in cfg['seeds']]
    predictions=[read(run/'clean-pde'/f'seed-{s}'/'D_E'/g/'prediction.json') for s in cfg['seeds'] for g in ('coarse','fine')]
    counts=dict(adam=sum(t['adam_updates'] for t in terminals),
        complete_evaluations=sum(t['lbfgs']['evaluations'] for t in terminals),
        train_forward=sum(t['statistics']['electrical']['forward_solves'] for t in terminals),
        train_adjoint=sum(t['statistics']['electrical']['adjoint_solves'] for t in terminals),
        historical_readout_forward=sum(t['electrical_counts']['forward_solves'] for t in historical),
        de_readout_forward=sum(t['electrical_counts']['forward_solves'] for t in predictions),
        checks_audits_forward=audits['counts']['forward_solves']+read(run/'interface-checks.json')['counts']['forward_solves'],
        checks_audits_adjoint=audits['counts']['adjoint_solves']+read(run/'interface-checks.json')['counts']['adjoint_solves'])
    assert counts['adam']<=3000 and counts['complete_evaluations']<=600
    assert counts['train_forward']<=54000 and counts['train_adjoint']<=54000
    assert counts['de_readout_forward']<=1112
    counts['total_forward']=sum(counts[k] for k in ('train_forward','historical_readout_forward','de_readout_forward','checks_audits_forward'))
    counts['total_adjoint']=counts['train_adjoint']+counts['checks_audits_adjoint']
    assert counts['total_forward']<=58392 and counts['total_adjoint']<=54500
    save_json(run/'training-and-own-inference-complete.json',dict(status='ALL_FIXED_ARTIFACTS_COMPLETE',
        counts=counts,reference_read=False,stress_read=False,completed_utc=now()))
    print(json.dumps(dict(event='ALL_FIXED_ARTIFACTS_COMPLETE',counts=counts)),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','check','cloud'))
    p.add_argument('--device',default='cpu');a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action=='check':checks(a.device)
    else:cloud(a.device)


if __name__=='__main__':main()
