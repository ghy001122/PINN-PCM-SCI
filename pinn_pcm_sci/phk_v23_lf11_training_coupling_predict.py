"""Two readouts of each single learned state, with no reference-field access."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import torch
from .phk_v23_lf11 import save_json,now
from .phk_v23_lf11_followup_fit import fit_model
from .phk_v23_lf11_elimination_physics import grid_for
from .phk_v23_lf11_elimination_predict import infer_time
from .phk_v23_lf11_electric_layer import ElectricalLayer
from .phk_v23_lf11_training_coupling import read

FIELD_KEYS=('potential','temperature','phase','joule_density')
TRACE_KEYS=('top_current','bottom_current','joule_power','internal_power','top_power','bottom_power')


def paired_time(model,layer,time,device):
    network,dn=infer_time(model,layer,time,device,'P_F')
    fixed={k:network[k] for k in ('temperature','phase')}
    # The inherited helper adds potential to the supplied mapping. Give it an
    # owned mapping, and compare only the two physical state fields.
    projected,dp=infer_time(model,layer,time,device,'P_E',baseline_fields=dict(fixed))
    for k in ('temperature','phase'):
        np.testing.assert_array_equal(network[k],projected[k])
    return network,dn,projected,dp


def predict_pair(root,arm,device):
    cfg=read(root/'frozen-config.json')
    saved=torch.load(root/arm/'checkpoint.pt',map_location='cpu',weights_only=False)
    model=fit_model(cfg,saved['model_state_dict'],adapter=True).to(device)
    from .phk_v22r_prediction import _evaluation_axes
    from .phk_v22r_training import PhkTrainingConfig
    x,z,times=_evaluation_axes(PhkTrainingConfig(arm='STRONG_RAW',case_control='FULL'))
    assert (len(x),len(z))==tuple(cfg['inference_grid'])
    grid=grid_for(model.physics,len(x),len(z))
    np.testing.assert_array_equal(x,grid.x_centers);np.testing.assert_array_equal(z,grid.z_centers)
    layer=ElectricalLayer(grid,model.physics.heater_width_fraction,cfg['linear_tolerance'])
    arrays={mode:{k:np.empty((len(times),grid.cell_count)) for k in ('potential','temperature','phase','joule_density')}
            for mode in ('network','projected')}
    traces={mode:{} for mode in arrays}
    for j,t in enumerate(times):
        network,dn,projected,dp=paired_time(model,layer,t,device)
        for mode,f,d in (('network',network,dn),('projected',projected,dp)):
            for k in arrays[mode]: arrays[mode][k][j]=f[k]
            for k,v in d.items(): traces[mode].setdefault(k,[]).append(v)
        if layer.backend.counts.forward_solves>278: raise RuntimeError('projection solve budget')
        if j%200==0: print(json.dumps(dict(prediction_role=arm,index=j,total=len(times))),flush=True)
    for mode in arrays:
        folder=root/arm/mode;folder.mkdir(exist_ok=False)
        with (folder/'prediction.npz').open('xb') as stream:
            np.savez_compressed(stream,x=x,z=z,time=times,**arrays[mode])
        np.savez_compressed(folder/'own-readout.npz',time=times,**{k:np.asarray(v) for k,v in traces[mode].items()})
        counts=layer.backend.snapshot() if mode=='projected' else dict(forward_solves=0,adjoint_solves=0)
        save_json(folder/'prediction.json',dict(status='FIXED_OWN_PREDICTION',role=arm,readout=mode,
            grid=[len(x),len(z)],times=len(times),electrical_counts=counts,reference_read=False,
            fine_electrical_solve_used=mode=='projected',same_temperature_phase=True,device=device,created_utc=now()))
    save_json(root/arm/'paired-readout-identity.json',dict(T_phase_exactly_equal=True,
        learned_models=1,readouts=2,network_solves=0,projection_counts=layer.backend.snapshot(),
        full_thermal_phase_trajectory_solved=False,reference_read=False))


def recover_pair(root,arm,skip_projection=()):
    """Persist every own-field time point after the recovered cloud inference error.

    A skipped projection remains visibly incomplete; it cannot enter evaluation.
    This never updates parameters or accesses reference fields.
    """
    root=Path(root);cfg=read(root/'frozen-config.json')
    torch.set_num_threads(cfg['cpu_threads'])
    saved=torch.load(root/arm/'checkpoint.pt',map_location='cpu',weights_only=False)
    model=fit_model(cfg,saved['model_state_dict'],adapter=True).to('cpu')
    from .phk_v22r_prediction import _evaluation_axes
    from .phk_v22r_training import PhkTrainingConfig
    x,z,times=_evaluation_axes(PhkTrainingConfig(arm='STRONG_RAW',case_control='FULL'))
    assert (len(x),len(z))==tuple(cfg['inference_grid'])
    grid=grid_for(model.physics,len(x),len(z))
    np.testing.assert_array_equal(x,grid.x_centers);np.testing.assert_array_equal(z,grid.z_centers)
    layer=ElectricalLayer(grid,model.physics.heater_width_fraction,cfg['linear_tolerance'])
    work=root/arm/'paired-inference-work';work.mkdir(exist_ok=True)
    progress=work/'progress.json'
    state=read(progress) if progress.exists() else dict(
        network_done=[False]*len(times),projected_done=[False]*len(times),
        counts={k:0 for k in layer.backend.snapshot()},reference_read=False)
    before=dict(state['counts'])
    arrays={mode:{} for mode in ('network','projected')}
    for mode in arrays:
        for key in FIELD_KEYS:
            path=work/(mode+'-'+key+'.npy')
            arrays[mode][key]=np.lib.format.open_memmap(path,
                mode='r+' if path.exists() else 'w+',dtype=np.float64,
                shape=(len(times),grid.cell_count))
    tracepath=work/'traces.npy'
    traces=np.lib.format.open_memmap(tracepath,mode='r+' if tracepath.exists() else 'w+',
        dtype=np.float64,shape=(2,len(TRACE_KEYS),len(times)))
    lost=read(root/'prediction-interface-repair.json')['failed_projection_forward_solves'] if arm=='F_raw' else 0
    extension=root/'inference-budget-amendment.json'
    extra=read(extension).get('additional_forward_solves',0) if extension.exists() and arm=='F_raw' else 0
    cap=278+extra
    def persist():
        current=layer.backend.snapshot()
        state['counts']={k:max(before.get(k,0),v) if k.startswith('max_') else before.get(k,0)+v
                         for k,v in current.items()}
        state.update(recorded_utc=now(),device='cpu',failed_cloud_solves=lost,
                     authorized_forward_cap_including_failure=cap)
        tmp=progress.with_suffix('.tmp');save_json(tmp,state);tmp.replace(progress)
    def keep(mode,j,values,diag):
        for key in FIELD_KEYS:
            arrays[mode][key][j]=values[key];arrays[mode][key].flush()
        row=0 if mode=='network' else 1
        for k,key in enumerate(TRACE_KEYS): traces[row,k,j]=diag[key]
        traces.flush();state[mode+'_done'][j]=True;persist()
    for j,t in enumerate(times):
        if not state['network_done'][j]:
            network,dn=infer_time(model,layer,t,'cpu','P_F');keep('network',j,network,dn)
        if not state['projected_done'][j] and j not in skip_projection:
            powered=float(model.physics.waveform(torch.tensor(t,dtype=torch.float64)))!=0.
            used=before.get('forward_solves',0)+layer.backend.counts.forward_solves+lost
            if powered and used>=cap:
                raise RuntimeError('additional projected point requires explicit inference budget authorization')
            fixed={key:np.asarray(arrays['network'][key][j]) for key in ('temperature','phase')}
            projected,dp=infer_time(model,layer,t,'cpu','P_E',baseline_fields=dict(fixed))
            for key in ('temperature','phase'): np.testing.assert_array_equal(fixed[key],projected[key])
            keep('projected',j,projected,dp)
        if j%100==0:
            print(json.dumps(dict(local_prediction=arm,index=j,total=len(times),
                forward_solves=state['counts']['forward_solves'],missing=sum(not v for v in state['projected_done']))),flush=True)
    if not all(state['network_done']) or not all(state['projected_done']):
        print(json.dumps(dict(role=arm,status='OWN_PREDICTION_INCOMPLETE',missing_projection_indices=
            [j for j,v in enumerate(state['projected_done']) if not v])),flush=True)
        return False
    for row,mode in enumerate(arrays):
        folder=root/arm/mode;folder.mkdir(exist_ok=True)
        if not (folder/'prediction.npz').exists():
            with (folder/'prediction.npz').open('xb') as stream:
                np.savez_compressed(stream,x=x,z=z,time=times,**arrays[mode])
            np.savez_compressed(folder/'own-readout.npz',time=times,
                **{key:np.asarray(traces[row,k]) for k,key in enumerate(TRACE_KEYS)})
        counts=state['counts'] if mode=='projected' else dict(forward_solves=0,adjoint_solves=0)
        save_json(folder/'prediction.json',dict(status='FIXED_OWN_PREDICTION',role=arm,readout=mode,
            grid=[len(x),len(z)],times=len(times),electrical_counts=counts,reference_read=False,
            fine_electrical_solve_used=mode=='projected',same_temperature_phase=True,device='cpu',
            recovered_after_cloud_shutdown=True,created_utc=now()))
    save_json(root/arm/'paired-readout-identity.json',dict(T_phase_exactly_equal=True,
        learned_models=1,readouts=2,network_solves=0,projection_counts=state['counts'],
        failed_cloud_forward_solves=lost,total_actual_projection_forward_solves=state['counts']['forward_solves']+lost,
        full_thermal_phase_trajectory_solved=False,reference_read=False))
    return True


if __name__=='__main__':
    import argparse
    from .phk_v23_lf11_training_coupling import RUN
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=RUN)
    parser.add_argument('--arm',choices=('F_raw','F_bal'),required=True)
    parser.add_argument('--device',default='cpu')
    parser.add_argument('--recover',action='store_true')
    parser.add_argument('--skip-lost-point',action='store_true')
    args=parser.parse_args()
    if args.recover:
        recover_pair(args.root,args.arm,(1,) if args.skip_lost_point and args.arm=='F_raw' else ())
    else:
        predict_pair(args.root,args.arm,args.device)
