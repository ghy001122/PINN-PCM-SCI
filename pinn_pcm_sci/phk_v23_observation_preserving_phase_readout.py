"""Locked-endpoint raw audits and native reads, with no reference access."""
from pathlib import Path
import argparse
import json
import time
import numpy as np
import torch
from .phk_v23_lf11 import ROOT,save_json
from .phk_v23_b1 import require_resource
from .phk_v23_lf11_elimination import deserialize_pool
from .phk_v23_lf11_elimination_physics import coordinates,grid_for
from .phk_v23_lf11_elimination_predict import infer_time
from .phk_v23_lf11_electric_layer import ElectricalLayer
from .phk_v23_observation_preserving_phase import A,B
from .phk_v23_observation_preserving_phase_run import RUN,ARMS,read,inputs


def endpoint(cfg,arm,device):
    exp,cal=inputs(cfg,'N' if arm=='B0' else arm,device)
    if arm!='B0':
        ck=torch.load(RUN/arm/'checkpoint.pt',map_location=device,weights_only=False)
        assert ck['base_sha256']==read(RUN/'input-manifest.json')['parent_sha256']
        exp.model.correction.load_state_dict(ck['correction_state_dict'])
    return exp,cal


def audit(cfg,device):
    if (RUN/'endpoint-audits.json').exists():raise FileExistsError('Audits complete')
    old_pool=deserialize_pool(read(ROOT/cfg['source_b1']/'audit-pool.json'))
    dpool=deserialize_pool(read(RUN/'D-audit-pool.json'));rows={};count=0
    for arm in ('B0',*ARMS):
        exp,_=endpoint(cfg,arm,device)
        _,raw=exp.objective({},old_pool,dict(aE=1.,bE=1.),full=True)
        _,local=exp.objective({},dpool,dict(aE=1.,bE=1.),full=True)
        mass=sum(v['mass'] for v in dpool['times'].values())
        local_physics=dict(phase_raw_mean_square=local['phase']*25/mass,
            thermal_raw_mean_square=local['thermal']*16/mass,
            phase_BC_mean_square_original_denominator=local['phase_boundary']/mass,
            scaled_phase=local['phase']/mass,scaled_thermal=local['thermal']/mass)
        rows[arm]=dict(full_raw=raw,D=local_physics,statistics=exp.statistics(),reference_read=False)
        assert exp.layer.backend.counts.forward_solves==16 and exp.layer.backend.counts.adjoint_solves==0
        count+=16;save_json(RUN/f'audit-{arm}.json',rows[arm])
        print(json.dumps(dict(audit=arm,D=local_physics)),flush=True)
    base=rows['B0']['D']
    for arm in ARMS:
        v=rows[arm]['D']
        rows[arm]['physical_completion']={
            'phase_10_percent':v['phase_raw_mean_square']<=.9*base['phase_raw_mean_square'],
            'thermal_noninferior':v['thermal_raw_mean_square']<=max(1.05*base['thermal_raw_mean_square'],base['thermal_raw_mean_square']+1e-12),
            'phase_BC_noninferior':v['phase_BC_mean_square_original_denominator']<=max(1.05*base['phase_BC_mean_square_original_denominator'],base['phase_BC_mean_square_original_denominator']+1e-12)}
        rows[arm]['physical_completion']['passed']=all(rows[arm]['physical_completion'].values())
    save_json(RUN/'endpoint-audits.json',dict(status='ALL_THREE_AND_BASE_RAW_AUDITS_COMPLETE',
        arms=rows,electrical_forward_solves=count,electrical_adjoint_solves=0,D_time_mass=.264,
        D_pool_time_count=64,D_pool_cells_per_time=256,reference_read=False))


def network_fields(model,grid,t,device):
    q=coordinates(grid,t,device=device);out={'temperature':[],'phase':[]}
    with torch.no_grad():
        for lo in range(0,len(q),4096):
            f=model.fields(q[lo:lo+4096])
            for k in out:out[k].append(f[k].cpu().numpy())
    return {k:np.concatenate(v) for k,v in out.items()}


def readout(cfg,device):
    times=np.linspace(0,2.5,1001);items=[];total=0
    for arm in ARMS:
        folder=RUN/'predictions'/arm;folder.mkdir(parents=True,exist_ok=False)
        exp,_=endpoint(cfg,arm,device);model=exp.model.eval();model.requires_grad_(False)
        grid=grid_for(model.physics,160,80);layer=ElectricalLayer(grid,model.physics.heater_width_fraction,cfg['linear_tolerance'])
        start=time.perf_counter()
        if arm=='G':
            arrays={k:np.lib.format.open_memmap(folder/(k+'.npy'),mode='w+',dtype='float64',shape=(1001,12800))
                    for k in ('temperature','phase','potential','joule_density')}
            traces={}
            for i,t in enumerate(times):
                f=network_fields(model,grid,float(t),device)
                values,d=infer_time(model,layer,float(t),device,'P_E',baseline_fields=f)
                for k,v in values.items():
                    if not np.isfinite(v).all():raise FloatingPointError('G native field nonfinite')
                    arrays[k][i]=v
                for k,v in d.items():traces.setdefault(k,[]).append(v)
                if i%100==0:
                    for v in arrays.values():v.flush()
                    save_json(folder/'progress.json',dict(saved=i+1,total=1001))
                    print(json.dumps(dict(readout=arm,saved=i+1)),flush=True)
            np.savez_compressed(folder/'prediction.npz',time=times,x=grid.x_centers,z=grid.z_centers,**arrays)
            np.savez_compressed(folder/'own-readout.npz',time=times,**{k:np.asarray(v) for k,v in traces.items()})
            for k,v in arrays.items():v._mmap.close();(folder/(k+'.npy')).unlink()
            assert layer.backend.counts.forward_solves==278
        else:
            dark=(times>A)&(times<B);frames=[]
            for i,t in enumerate(times[dark]):
                f=network_fields(model,grid,float(t),device)
                if not np.isfinite(f['phase']).all():raise FloatingPointError('Nonfinite dark phase')
                frames.append(f['phase'])
                if i%100==0:print(json.dumps(dict(readout=arm,dark_frames=i+1)),flush=True)
            np.savez_compressed(folder/'dark-phase.npz',time=times[dark],phase=np.array(frames),x=grid.x_centers,z=grid.z_centers)
            checks={};ports={}
            for t in (.27,1.28,1.55,1.8):
                f=network_fields(model,grid,t,device)
                values,d=infer_time(model,layer,t,device,'P_E',baseline_fields=f)
                for k,v in values.items():checks[str(t)+'/'+k]=v
                ports[str(t)]=d
            np.savez_compressed(folder/'own-field-spot-checks.npz',**checks)
            save_json(folder/'own-field-spot-ports.json',ports)
            assert layer.backend.counts.forward_solves==2
        total+=layer.backend.counts.forward_solves
        assert layer.backend.counts.adjoint_solves==0
        item=dict(id='shorter/29/'+arm,role=arm,protocol='shorter',seed=29,
            origin='observation_preserving_phase_completion',
            prediction=(folder/'prediction.npz').relative_to(ROOT).as_posix(),
            readout=(folder/'own-readout.npz').relative_to(ROOT).as_posix(),
            local_base_array_composition_required=arm!='G')
        save_json(folder/'prediction.json',dict(status='NATIVE_OWN_G' if arm=='G' else 'DARK_PHASE_AND_SPOTS_AWAITING_BASE_COMPOSITION',
            elapsed_seconds=time.perf_counter()-start,electrical_counts=layer.backend.snapshot(),
            coordinate_work=model.work,reference_read=False))
        items.append(item)
    assert total==282
    save_json(RUN/'cloud-readout-manifest.json',dict(status='ALL_THREE_GPU_READERS_COMPLETE',objects=items,
        electrical_forward_solves=total,electrical_adjoint_solves=0,reference_read=False,
        N_S_reuse_requires_local_exact_base_and_spot_verification=True))


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['audit','readout'])
    p.add_argument('--device',default='cuda:0');p.add_argument('--resource',type=Path,required=True)
    a=p.parse_args();torch.set_num_threads(4);cfg=read(RUN/'frozen-config.json')
    require_resource(a.resource,a.device,cfg)
    assert read(RUN/'all-endpoints-locked.json')['status']=='ALL_THREE_FIXED_ENDPOINTS_LOCKED'
    (audit if a.action=='audit' else readout)(cfg,a.device)


if __name__=='__main__':main()
