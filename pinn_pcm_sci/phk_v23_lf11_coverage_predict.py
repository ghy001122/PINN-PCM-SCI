"""Durable network and common-reader arrays for the two locked F_cov states."""
from pathlib import Path
import json
import numpy as np
import torch
from .phk_v23_lf11_coverage import read,atomic_json,check_resources
from .phk_v23_lf11_followup_fit import fit_model
from .phk_v23_lf11_elimination_physics import grid_for
from .phk_v23_lf11_elimination_predict import infer_time
from .phk_v23_lf11_electric_layer import ElectricalLayer

KEYS=('potential','temperature','phase','joule_density')
TRACE=('top_current','bottom_current','joule_power','internal_power','top_power','bottom_power')


def predict(folder,device):
    if read(folder/'F_cov/terminal.json')['status']!='VALID_FIXED_ENDPOINT':raise RuntimeError('No valid endpoint')
    cfg=read(folder/'frozen-config.json')
    state=torch.load(folder/'F_cov/checkpoint.pt',map_location='cpu',weights_only=False)
    model=fit_model(cfg,state['model_state_dict'],adapter=True).to(device).eval()
    model.requires_grad_(False);torch.set_num_threads(4)
    times=np.linspace(0,2.5,1001)
    for label,shape in [('coarse',(160,80)),('fine',(240,120))]:
        target=folder/'F_cov'/label;target.mkdir(exist_ok=True)
        if (target/'readers-complete.json').exists():continue
        grid=grid_for(model.physics,*shape)
        layer=ElectricalLayer(grid,model.physics.heater_width_fraction,cfg['linear_tolerance'])
        progress_path=target/'progress.json'
        progress=read(progress_path) if progress_path.exists() else dict(next_index=0,forward_solves=0,pending_index=None)
        prior_count=progress['forward_solves']
        # An interrupted in-flight time is recomputed only when its arrays were
        # not committed. Its possible discarded solve remains separately visible.
        discarded=int(progress.get('discarded_inflight_upper_bound',0))
        if progress.get('pending_index') is not None:
            j=progress['pending_index']
            discarded+=int(float(model.physics.waveform(torch.tensor(times[j],dtype=torch.float64,device=device)))!=0.)
        progress['discarded_inflight_upper_bound']=discarded
        arrays={}
        for mode in ('network','projected'):
            out=target/mode;out.mkdir(exist_ok=True)
            arrays[mode]={}
            for k in KEYS:
                p=out/(k+'.npy')
                arrays[mode][k]=np.lib.format.open_memmap(p,mode='r+' if p.exists() else 'w+',dtype='float64',shape=(1001,grid.cell_count))
        path=target/'traces.npy'
        trace=np.lib.format.open_memmap(path,mode='r+' if path.exists() else 'w+',dtype='float64',shape=(2,len(TRACE),1001))
        for j in range(progress['next_index'],1001):
            check_resources(device)
            progress['pending_index']=j;atomic_json(progress_path,progress)
            network,dn=infer_time(model,layer,float(times[j]),device,'P_F',chunk=1024)
            fixed={k:network[k] for k in ('temperature','phase')}
            projected,dp=infer_time(model,layer,float(times[j]),device,'P_E',baseline_fields=dict(fixed))
            for k in fixed:np.testing.assert_array_equal(network[k],projected[k])
            for row,(mode,values,diag) in enumerate([('network',network,dn),('projected',projected,dp)]):
                for k,arr in arrays[mode].items():
                    if not np.isfinite(values[k]).all():raise FloatingPointError(k)
                    arr[j]=values[k];arr.flush()
                for k,key in enumerate(TRACE):trace[row,k,j]=diag[key]
            trace.flush()
            progress.update(next_index=j+1,pending_index=None,forward_solves=prior_count+layer.backend.counts.forward_solves)
            atomic_json(progress_path,progress)
            if j%100==0:print(json.dumps(dict(event='READOUT',seed=cfg['seed'],grid=label,index=j)),flush=True)
        assert progress['forward_solves']==278
        for row,mode in enumerate(('network','projected')):
            out=target/mode
            if not (out/'prediction.npz').exists():
                np.savez_compressed(out/'prediction.npz',x=grid.x_centers,z=grid.z_centers,time=times,**arrays[mode])
                np.savez_compressed(out/'own-readout.npz',time=times,**{key:trace[row,k] for k,key in enumerate(TRACE)})
            atomic_json(out/'prediction.json',dict(status='FIXED_OWN_PREDICTION',role='F_cov',seed=cfg['seed'],
                grid=list(shape),times=1001,readout=mode,same_temperature_phase=True,reference_read=False,
                electrical_counts=dict(forward_solves=278 if mode=='projected' else 0,adjoint_solves=0),device=device))
        atomic_json(target/'readers-complete.json',dict(status='PASS',**progress,reference_read=False,
            original_network_readout_saved=True,temperature_phase_exactly_equal=True))
        for mode in arrays:
            for arr in arrays[mode].values():arr._mmap.close()
        trace._mmap.close()
    del model
    if str(device).startswith('cuda'):torch.cuda.empty_cache()
