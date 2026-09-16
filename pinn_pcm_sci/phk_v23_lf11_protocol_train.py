"""V32 paired new-case adaptation; this process receives sparse observations only."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import torch
from .phk_v23_lf11 import ROOT, SparseData, save_json, now
from .phk_v23_lf11_protocol import validate_case, inference_times, powered_count
from .phk_v23_lf11_clean_confirmation import prepare_seed, BoundedElectricExperiment
from .phk_v23_lf11_elimination import train_role
from .phk_v23_lf11_training_coupling import train, read
from .phk_v23_lf11_followup_fit import fit_model
from .phk_v23_lf11_elimination_physics import grid_for
from .phk_v23_lf11_elimination_predict import infer_time, baseline
from .phk_v23_lf11_training_coupling_predict import paired_time
from .phk_v23_lf11_electric_layer import ElectricalLayer

RUN=ROOT/'outputs/runs/20260915-lf11-protocol-history'
CONFIG=ROOT/'configs/phk_v23/lf11_protocol_sprint.json'


def predict(directory, role, cfg, device, baseline_data=None):
    """One projected solve per powered time; optional soft network readout shares T/phase."""
    if role=='B_E':
        model=fit_model(cfg,adapter=True).to(device)
    else:
        state=torch.load(directory/role/'checkpoint.pt',map_location='cpu',weights_only=False)
        model=fit_model(cfg,state['model_state_dict'],adapter=True).to(device)
    times=inference_times(cfg['case_spec'])
    grid=grid_for(model.physics,*cfg['inference_grid'])
    layer=ElectricalLayer(grid,model.physics.heater_width_fraction,cfg['linear_tolerance'])
    projection_cap=powered_count(cfg['case_spec'])
    modes=['network','projected'] if role=='F_raw' else ['projected']
    keys=('potential','temperature','phase','joule_density')
    arrays={mode:{k:np.empty((len(times),grid.cell_count)) for k in keys} for mode in modes}
    traces={mode:{} for mode in modes}
    bfields=baseline(baseline_data,grid,times,model.physics) if role=='B_E' else None
    for i,t in enumerate(times):
        if role=='F_raw':
            n,dn,p,dp=paired_time(model,layer,t,device)
            parts={'network':(n,dn),'projected':(p,dp)}
        else:
            supplied={k:v[i] for k,v in bfields.items()} if bfields is not None else None
            p,dp=infer_time(model,layer,t,device,'P_E',baseline_fields=supplied)
            parts={'projected':(p,dp)}
        for mode,(fields,diag) in parts.items():
            for k in keys:arrays[mode][k][i]=fields[k]
            for k,v in diag.items():traces[mode].setdefault(k,[]).append(v)
        if layer.backend.counts.forward_solves>projection_cap:
            raise RuntimeError('new-protocol projection solve cap')
        if i%200==0:print(json.dumps(dict(seed=cfg['seed'],prediction=role,index=i)),flush=True)
    for mode in modes:
        folder=directory/role/mode;folder.mkdir(parents=True,exist_ok=False)
        np.savez_compressed(folder/'prediction.npz',x=grid.x_centers,z=grid.z_centers,time=times,**arrays[mode])
        np.savez_compressed(folder/'own-readout.npz',time=times,**{k:np.asarray(v) for k,v in traces[mode].items()})
        counts=layer.backend.snapshot() if mode=='projected' else dict(forward_solves=0,adjoint_solves=0)
        save_json(folder/'prediction.json',dict(status='FIXED_OWN_PREDICTION',role=role,readout=mode,
            case_spec=cfg['case_spec'],grid=cfg['inference_grid'],times=len(times),
            electrical_counts=counts,reference_read=False,created_utc=now()))
    if role=='F_raw':
        save_json(directory/role/'paired-readout-identity.json',dict(T_phase_exactly_equal=True,
            learned_models=1,readouts=2,network_solves=0,projection_counts=layer.backend.snapshot(),
            reference_read=False))


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RUN)
    p.add_argument('--config',type=Path,default=CONFIG);p.add_argument('--device',default='cuda:0')
    a=p.parse_args();cfg=read(a.config);validate_case(cfg['case_spec'])
    torch.set_num_threads(cfg['cpu_threads'])
    a.root.mkdir(parents=True,exist_ok=True)
    if list(a.root.glob('seed-*')):raise FileExistsError('existing scientific trajectory; no automatic restart')
    save_json(a.root/'frozen-config.json',cfg)
    save_json(a.root/'training-isolation.json',dict(reference_read=False,
        training_input=cfg['sparse'],initialization='fresh paired seeds29/43, zero-output T adapter',
        full_reference_or_support_received=False,old_trained_weights_received=False,
        inference_times=1001,inference_nonzero_times=powered_count(cfg['case_spec']),
        case_spec=cfg['case_spec']))
    for seed in cfg['confirmation']['seeds']:
        directory=a.root/f'seed-{seed}'
        c=prepare_seed(directory,cfg,seed,'F_raw',a.device)
        train_role(directory,'P_E',c,a.device,output_role='E',experiment_type=BoundedElectricExperiment)
        if not train(directory,'F_raw',c,a.device):raise RuntimeError('new-case soft endpoint invalid')
        predict(directory,'E',c,a.device)
        predict(directory,'F_raw',c,a.device)
        save_json(directory/'training-and-own-inference-complete.json',dict(completed=True,
            valid_roles=c['roles'],case_id=cfg['case_spec']['case_id'],reference_read=False,created_utc=now()))
    # One seedless same-information strong baseline, computed once for both pairs.
    predict(a.root,'B_E',cfg,a.device,baseline_data=SparseData(ROOT/cfg['sparse']))
    save_json(a.root/'training-and-own-inference-complete.json',dict(completed=True,
        clean_seeds=cfg['confirmation']['seeds'],case_id=cfg['case_spec']['case_id'],
        B_E_computed_once=True,reference_read=False,created_utc=now()))


if __name__=='__main__':main()
