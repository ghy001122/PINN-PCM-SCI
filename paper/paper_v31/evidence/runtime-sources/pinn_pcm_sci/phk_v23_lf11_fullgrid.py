"""V31 spatial electric counterfactual. Training and diagnostics are label blind."""
from __future__ import annotations
import argparse
import json
import shutil
from pathlib import Path
import numpy as np
import torch
from .phk_v23_lf11 import ROOT,SparseData,save_json,now
from .phk_v23_lf11_training_coupling import SoftExperiment,read,train
from .phk_v23_lf11_elimination import deserialize_pool

RUN=ROOT/'outputs/runs/20260914-lf11-fullgrid'
CONFIG=ROOT/'configs/phk_v23/lf11_fullgrid_sprint.json'


def prepare(root,config):
    root.mkdir(parents=True,exist_ok=False)
    for name in ('calibration.json','calibration-pool.json','lbfgs-pool.json','audit-pool.json'):
        shutil.copyfile(ROOT/config['historical_root']/name,root/name)
    shutil.copyfile(ROOT/config['parent'],root/'parent.pt')
    save_json(root/'frozen-config.json',config)
    save_json(root/'input-identity.json',dict(parent=config['parent'],sparse=config['sparse'],
        reference_read=False,calibration_reused=True,eta=1.,
        only_change='electric spatial volume mean over all 3200 cells at original physics times',
        thermal_phase_samples_and_rng_unchanged=True,created_utc=now()))


def diagnose(root,role,device):
    config=read(root/'frozen-config.json')
    state=torch.load(root/role/'checkpoint.pt',map_location='cpu',weights_only=False)
    exp=SoftExperiment(config,state['model_state_dict'],SparseData(ROOT/config['sparse']),device,1.)
    grid=exp.grid
    # Adjacent to an actual heater-overlap face, with other boundary cells disjoint.
    overlap=np.maximum(0.,np.minimum(grid.cell_x+grid.dx/2,exp.model.physics.heater_half_width)
                       -np.maximum(grid.cell_x-grid.dx/2,-exp.model.physics.heater_half_width))
    bottom=np.repeat(np.arange(grid.nz),grid.nx)==0
    heater=bottom&(overlap>0)
    ix=np.tile(np.arange(grid.nx),grid.nz);iz=np.repeat(np.arange(grid.nz),grid.nx)
    edge=(ix==0)|(ix==grid.nx-1)|(iz==0)|(iz==grid.nz-1)
    bins=dict(heater_adjacent=heater,other_boundary=edge&~heater,interior=~edge)
    pool=deserialize_pool(read(root/'lbfgs-pool.json'))
    rows=[]
    with torch.no_grad():
        for t,phys in pool['times'].items():
            _,_,residual=exp.electric(t,True)
            residual=np.zeros(grid.cell_count) if residual is None else residual.cpu().numpy()
            squared=(residual/config['pde_scales']['electric'])**2
            rows.append(dict(time=t,mass=phys['mass'],sampled=float(squared[phys['cells']].mean()),
                full=float(squared.mean()),bins={k:dict(cells=int(m.sum()),mean=float(squared[m].mean()),
                    full_volume_contribution=float(squared[m].sum()/grid.cell_count)) for k,m in bins.items()}))
    save_json(root/role/'spatial-electric-diagnostic.json',dict(status='REPORTING_ONLY',
        pool='original lbfgs physics times',rows=rows,
        sampled_integral=sum(r['mass']*r['sampled'] for r in rows),
        full_integral=sum(r['mass']*r['full'] for r in rows),
        statistics=exp.statistics(),optimizer_updates=0,reference_read=False))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','train','diagnose','predict','all'])
    parser.add_argument('--root',type=Path,default=RUN)
    parser.add_argument('--config',type=Path,default=CONFIG)
    parser.add_argument('--device',default='cpu')
    args=parser.parse_args();root=args.root
    cfg=read(args.config if args.action in ('prepare','all') else root/'frozen-config.json')
    torch.set_num_threads(cfg['cpu_threads'])
    if args.action in ('prepare','all'): prepare(root,cfg)
    if args.action in ('train','all'):
        if not train(root,'F_full',cfg,args.device): raise RuntimeError('F_full training invalid')
    if args.action in ('diagnose','all'): diagnose(root,'F_full',args.device)
    if args.action in ('predict','all'):
        from .phk_v23_lf11_training_coupling_predict import predict_pair
        predict_pair(root,'F_full',args.device)
        save_json(root/'training-and-own-inference-complete.json',dict(completed=True,
            valid_roles=['F_full'],all_roles_valid=True,reference_read=False,created_utc=now()))


if __name__=='__main__': main()
