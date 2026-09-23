"""Common native readout and zero-update audits, only after eight endpoints lock."""
import argparse
import json
import time
from pathlib import Path
import numpy as np
import torch
from .phk_v23_lf11 import ROOT,save_json
from .phk_v23_b1 import B1Electric,require_resource,instrument_model
from .phk_v23_b1_observations import VisibleData
from .phk_v23_lf11_elimination import deserialize_pool
from .phk_v23_lf11_elimination_physics import grid_for
from .phk_v23_lf11_elimination_predict import infer_time
from .phk_v23_lf11_electric_layer import ElectricalLayer
from .phk_v23_lf11_followup_fit import fit_model
from .phk_v23_phase_moments import ARMS,quadrature_comparison
from .phk_v23_phase_moments_run import CONFIG,read,phase_record


def readout(cfg,device):
    run=ROOT/cfg['run'];cfg=read(run/'frozen-config.json')
    assert read(run/'all-endpoints-locked.json')['status']=='ALL_EIGHT_FIXED_ENDPOINTS_LOCKED'
    items=[];total=0;times=np.linspace(0.,2.5,1001)
    for arm in ARMS:
        folder=run/'predictions'/arm
        if folder.exists():
            raise FileExistsError('Existing readout; recover only missing data after diagnosis')
        folder.mkdir(parents=True)
        state=torch.load(run/arm/'checkpoint.pt',map_location='cpu',weights_only=False)['model_state_dict']
        model=fit_model(cfg,state,adapter=True).to(device).eval();model.requires_grad_(False)
        work=instrument_model(model)
        grid=grid_for(model.physics,160,80)
        layer=ElectricalLayer(grid,model.physics.heater_width_fraction,cfg['linear_tolerance'])
        arrays={k:np.lib.format.open_memmap(folder/(k+'.npy'),mode='w+',dtype='float64',shape=(1001,12800))
                for k in ('potential','temperature','phase','joule_density')}
        traces={};start=time.perf_counter()
        for i,t in enumerate(times):
            values,diagnostics=infer_time(model,layer,float(t),device,'P_E')
            for k,v in values.items():
                if not np.isfinite(v).all():raise FloatingPointError(arm+'/'+k)
                arrays[k][i]=v
            for k,v in diagnostics.items():traces.setdefault(k,[]).append(v)
            if i%100==0:
                for v in arrays.values():v.flush()
                save_json(folder/'progress.json',dict(saved=i+1,total=1001,electrical=layer.backend.snapshot()))
                print(json.dumps(dict(readout=arm,saved=i+1)),flush=True)
        assert layer.backend.counts.forward_solves==278 and layer.backend.counts.adjoint_solves==0
        total+=278
        np.savez_compressed(folder/'prediction.npz',time=times,x=grid.x_centers,z=grid.z_centers,**arrays)
        np.savez_compressed(folder/'own-readout.npz',time=times,**{k:np.asarray(v) for k,v in traces.items()})
        save_json(folder/'prediction.json',dict(status='FIXED_ENDPOINT_PROJECTED_READER',arm=arm,
            grid=[160,80],elapsed_seconds=time.perf_counter()-start,model_work=work,
            electrical_counts=layer.backend.snapshot(),reference_read=False))
        for k,v in arrays.items():
            v._mmap.close();(folder/(k+'.npy')).unlink()
        items.append(dict(id='shorter/29/'+arm,protocol='shorter',seed=29,role=arm,
            origin='relative_phase_moments_development',prediction=(folder/'prediction.npz').relative_to(ROOT).as_posix(),
            readout=(folder/'own-readout.npz').relative_to(ROOT).as_posix()))
    assert total==2224
    save_json(run/'readout-manifest.json',dict(status='ALL_EIGHT_NATIVE_READERS_COMPLETE',objects=items,
        electrical_forward_solves=total,electrical_adjoint_solves=0,reference_read=False))


def audit(cfg,device):
    run=ROOT/cfg['run'];cfg=read(run/'frozen-config.json')
    assert read(run/'all-endpoints-locked.json')['status']=='ALL_EIGHT_FIXED_ENDPOINTS_LOCKED'
    if (run/'endpoint-audits.json').exists():raise FileExistsError('Audit already complete')
    data=VisibleData(ROOT/cfg['sparse'])
    pool=deserialize_pool(read(ROOT/cfg['source_b1']/'audit-pool.json'))
    phase_pool=read(run/'phase-calibration-pool.json');records={};total=0
    for arm in ARMS:
        state=torch.load(run/arm/'checkpoint.pt',map_location='cpu',weights_only=False)['model_state_dict']
        exp=B1Electric(cfg,state,data,device,'P_E')
        _,raw=exp.objective({},pool,dict(aE=1.,bE=1.),1.,backward=False)
        total+=exp.layer.backend.counts.forward_solves
        assert exp.layer.backend.counts.forward_solves==16 and exp.layer.backend.counts.adjoint_solves==0
        quadrature={}
        for order in (16,32):
            quadrature[order],_=phase_record(exp.model,exp.grid,phase_pool,order,cfg['phase_logit_epsilon'])
        comparisons=quadrature_comparison(quadrature[16],quadrature[32])
        records[arm]=dict(raw=raw,raw_statistics=exp.statistics(),quadrature=quadrature,
            quadrature_comparison=comparisons,quadrature_pass=all(v['passed'] for v in comparisons.values()),
            zero_updates=True,reference_read=False)
        save_json(run/arm/'endpoint-audit.json',records[arm])
        print(json.dumps(dict(endpoint_audit=arm,quadrature_pass=records[arm]['quadrature_pass'])),flush=True)
    assert total==128
    save_json(run/'endpoint-audits.json',dict(status='ALL_EIGHT_ZERO_UPDATE_AUDITS_COMPLETE',arms=records,
        audit_electrical_forward_solves=total,audit_electrical_adjoint_solves=0,reference_read=False))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('readout','audit'))
    p.add_argument('--config',type=Path,default=CONFIG);p.add_argument('--device',default='cuda:0')
    p.add_argument('--resource',type=Path,required=True);a=p.parse_args();cfg=read(a.config)
    torch.set_num_threads(cfg['cpu_threads']);require_resource(a.resource,a.device,cfg)
    (readout if a.action=='readout' else audit)(cfg,a.device)


if __name__=='__main__':main()
