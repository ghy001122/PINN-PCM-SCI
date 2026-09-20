"""Portable fixed-array reproduction of reference x electrical-reader effects.

Run in an extracted package: python -I portable/readout_rescore.py --root .
Only NumPy is required. No model load/forward, training or linear solve.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse
import copy
import csv
import gc
import importlib.util
import json
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
s=module('archive_rescore','rescore.py')
core=module('readout_aware_metrics','readout_metrics.py')

def grid_native(m,nx=240,nz=120):
    dx=(m['x_max']-m['x_min'])/nx;dz=(m['z_max']-m['z_min'])/nz
    x=m['x_min']+(np.arange(nx)+.5)*dx;z=m['z_min']+(np.arange(nz)+.5)*dz
    xx,zz=np.meshgrid(x,z,indexing='xy');first=[];second=[];area=[];half=[]
    for iz in range(nz):
        for ix in range(nx-1):
            first.append(iz*nx+ix);second.append(iz*nx+ix+1);area.append(dz);half.append(dx/2)
    for iz in range(nz-1):
        for ix in range(nx):
            first.append(iz*nx+ix);second.append((iz+1)*nx+ix);area.append(dx);half.append(dz/2)
    ah=.5*(m['x_max']-m['x_min'])*m['heater_width_fraction']
    mid=.5*(m['x_min']+m['x_max'])
    overlap=np.maximum(0.,np.minimum(x+.5*dx,mid+ah)-np.maximum(x-.5*dx,mid-ah))
    return s.Grid(**{**m,'nx':nx,'nz':nz,'dx':dx,'dz':dz,'cell_count':nx*nz},
        cell_x=xx.ravel(),cell_z=zz.ravel(),x_centers=x,z_centers=z,
        cell_volumes=np.full(nx*nz,dx*dz),internal_first=np.array(first),internal_second=np.array(second),
        internal_area=np.array(area),internal_half_distance=np.array(half),overlap=overlap)

def axis_map(n,m):
    a=np.linspace(0,1,n+1);b=np.linspace(0,1,m+1)
    w=np.maximum(0,np.minimum(b[1:,None],a[None,1:])-np.maximum(b[:-1,None],a[None,:-1]))/np.diff(b)[:,None]
    np.testing.assert_allclose(w.sum(1),1,rtol=0,atol=2e-14)
    np.testing.assert_allclose(w.sum(0),m/n,rtol=0,atol=3e-14)
    width=max(np.count_nonzero(row) for row in w)
    ix=np.zeros((m,width),int);weight=np.zeros((m,width))
    for j,row in enumerate(w):
        inds=np.flatnonzero(row);ix[j,:len(inds)]=inds;weight[j,:len(inds)]=row[inds]
    return ix,weight

def restrict(v):
    ix,wx=axis_map(240,160);iz,wz=axis_map(120,80)
    out=np.empty((len(v),12800))
    for lo in range(0,len(v),16):
        a=v[lo:lo+16].reshape(-1,120,240)
        x=np.sum(a[:,:,ix]*wx[None,None,:,:],axis=-1)
        out[lo:lo+16]=np.sum(x[:,iz,:]*wz[None,:,:,None],axis=2).reshape(-1,12800)
    np.testing.assert_allclose(out.mean(1),v.mean(1),rtol=2e-12,atol=2e-14)
    return out

def load_ref(root,desc,refname,grid,physics):
    path=root/desc['references'][refname]
    fields,q=s.arrays(path);s.canonical_coordinates(fields,grid)
    with np.load(path,allow_pickle=False) as f:
        ports={k:f[k] for k in ('top_current','bottom_current','joule_power')}
    if q is None:q=s.deposition(fields,grid,physics)
    return SimpleNamespace(**fields,**ports,grid=grid),q

def pred_cache(root,item,out,grid,native,physics):
    """One native port reconstruction and conservative map per stored reader."""
    cache=out/'reader-cache'/item['id']
    cache.mkdir(parents=True,exist_ok=True)
    for level,pkey,rkey,g in [('coarse','prediction','readout',grid),('fine','fine_prediction','fine_readout',native)]:
        if pkey not in item:continue
        target=cache/(level+'.npz')
        if target.exists():continue
        fields,q=s.arrays(root/item[pkey]);s.canonical_coordinates(fields,g)
        device=core.readout(fields['potential'],fields['temperature'],fields['phase'],g,physics.waveform(fields['time']),physics)
        with np.load(root/item[rkey],allow_pickle=False) as f:
            for k in ('top_current','bottom_current','joule_power'):
                np.testing.assert_allclose(f[k],device[k],rtol=1e-10,atol=1e-11)
        np.testing.assert_allclose(q@g.cell_volumes,device['joule_power'],rtol=1e-10,atol=1e-11)
        # Cache only scalar traces. Large fixed fields are already archived;
        # duplicating them is unnecessary for this isolated reproduction.
        np.savez_compressed(target,**device)
        del fields,q,device;gc.collect()
    return cache

def mechanisms(fields,ref,cfg,physics):
    """Prespecified report-only, full-domain and ROI diagnostics."""
    t=ref.time;wt=core.axis_weights(t);measure=wt[:,None]/ref.grid.cell_count
    ph=fields['phase'];rp=ref.phase;active=ph>=.5;truth=rp>=.5
    band=abs(rp-.5)<=.05;heating=np.zeros(len(t),bool)
    for lo,hi in cfg['windows'][::2]:heating|=(t>=lo)&(t<=hi)
    result={'threshold_half_width':.05,'regions':{}}
    error=ph-rp
    for scope,tm in [('full_history',np.ones(len(t),bool)),('heating_windows',heating)]:
        for name,region in [('near_threshold',band),('outside_threshold',~band)]:
            mask=region&tm[:,None];mass=float(np.sum(measure*mask))
            dist=[]
            for low,high in zip([0,.01,.025,.05,.1,.2],[.01,.025,.05,.1,.2,1.0000001]):
                dist.append(float(np.sum(measure*mask*(abs(error)>=low)*(abs(error)<high))))
            result['regions'][scope+'/'+name]=dict(measure=mass,
                FN=float(np.sum(measure*mask*truth*~active)),FP=float(np.sum(measure*mask*~truth*active)),
                reference_active_mass=float(np.sum(measure*mask*truth)),
                predicted_active_mass=float(np.sum(measure*mask*active)),
                conditional_RMS=float(np.sqrt(np.sum(measure*mask*error**2)/mass)) if mass else None,
                abs_error_bin_edges=[0,.01,.025,.05,.1,.2,1.0000001],error_mass_by_bin=dist)
    a=physics.conductivity_temperature_gain*(fields['temperature']-ref.temperature)
    h=lambda x:x*x*(3-2*x)
    b=np.log(physics.conductivity_phase_ratio)*(h(ph)-h(rp))
    # Exact constitutive decomposition. The cross term is retained with sign.
    avg=lambda v:float(np.sum(measure*v))
    total=avg((a+b)**2);aa=avg(a*a);bb=avg(b*b);cross=2*avg(a*b)
    np.testing.assert_allclose(total,aa+bb+cross,rtol=2e-12,atol=2e-14)
    result['log_conductivity']=dict(temperature_MSE=aa,phase_MSE=bb,signed_cross=cross,
        total_MSE=total,RMS=float(np.sqrt(total)),causal_attribution=False)
    return result

def score_one(root,item,level,ref,qref,physics,cfg,cache,out,refname,oldscales,native_qref):
    fields,qp=s.arrays(root/item['prediction']);s.canonical_coordinates(fields,ref.grid)
    np.testing.assert_array_equal(fields['time'],ref.time)
    qnative=None
    if level=='fine':
        with np.load(root/item['fine_prediction'],allow_pickle=False) as f:
            fields['potential']=restrict(f['potential'])
            qnative=f['joule_density'];qp=restrict(qnative)
    with np.load(cache/(level+'.npz'),allow_pickle=False) as f:
        device={k:f[k] for k in ('top_current','bottom_current','joule_power','input_power','power_defect','electric_fv_rms')}
    # Fine ports are not recomputed from restricted V and coarse T/phase.
    record,traces=core.metrics({k:fields[k] for k in ('potential','temperature','phase')},ref,physics,cfg,device_override=device)
    if not record['valid']:raise ValueError('Invalid fixed endpoint '+item['id']+'/'+level)
    core.add_power_metrics(record,traces,ref.time,ref.top_current,ref.joule_power)
    normal=dict(top_current=core.time_rms(ref.top_current,ref.time),
        bottom_current=core.time_rms(ref.bottom_current,ref.time),power=core.time_rms(ref.joule_power,ref.time),
        local_q=core.field_rms(qref,np.zeros_like(qref),ref.time))
    qerr=core.field_rms(qp,qref,ref.time)
    record['metrics'].update(local_joule_NRMSE=qerr/max(normal['local_q'],1e-12),
        top_current_rms_error=core.time_rms(device['top_current']-ref.top_current,ref.time),
        bottom_native_NRMSE=core.time_rms(device['bottom_current']-ref.bottom_current,ref.time)/max(normal['bottom_current'],1e-12))
    record['normalizers']=normal
    record['fixed_old_denominator']={
        'EI':record['metrics']['top_current_rms_error']/max(oldscales['top_current'],1e-12),
        'bottom_current_NRMSE':record['metrics']['bottom_current_rms_error']/max(oldscales['top_current'],1e-12),
        'power_trace_NRMSE':record['metrics']['power_trace_rms_error']/max(oldscales['power'],1e-12),
        'local_joule_NRMSE':qerr/max(oldscales['local_q'],1e-12)}
    if refname=='spatial' and level=='fine':
        denom=core.field_rms(native_qref,np.zeros_like(native_qref),ref.time)
        record['native_240_local_q_NRMSE']=core.field_rms(qnative,native_qref,ref.time)/max(denom,1e-12)
    del qnative
    for c in record['cycles']:
        c['reference_event_present']=c['reference_event_time'] is not None
        c['false_positive_event']=not c['reference_event_present'] and c['event_time'] is not None
        c['false_negative_target_mass']=c['teacher_active_target_mass']-c['true_positive_target_mass']
        c['false_positive_target_mass']=c['predicted_active_target_mass']-c['true_positive_target_mass']
    record.update(id=item['id'],protocol=item['protocol'],seed=item['seed'],role=item['role'],
        origin=item['origin'],reference=refname,readout_grid=[160,80] if level=='coarse' else [240,120],
        field_event_grid=[160,80],local_q_measure='restricted 160x80 diagnostic; native fine metric separately named')
    tracepath=out/'traces'/refname/level/(item['id'].replace('/','_')+'.npz')
    tracepath.parent.mkdir(parents=True,exist_ok=True)
    err=device['joule_power']-ref.joule_power
    cumulative=np.r_[0,np.cumsum(.5*(err[1:]+err[:-1])*np.diff(ref.time))]
    np.savez_compressed(tracepath,time=ref.time,reference_current=ref.top_current,reference_power=ref.joule_power,
        signed_power_error=err,absolute_power_error=abs(err),cumulative_signed_energy_error=cumulative,**traces)
    if level=='coarse' and item['role'] in ('E','F'):
        s.save(out/'mechanisms'/refname/(item['id'].replace('/','_')+'.json'),mechanisms(fields,ref,cfg,physics))
    return record

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=HERE.parent)
    p.add_argument('--out',default='readout-rescore');p.add_argument('--compare',type=Path)
    a=p.parse_args();root=a.root.resolve();manifest=s.read(root/'manifest.json')
    out=s.locate(root,a.out)
    if (out/'results.json').exists():raise FileExistsError('Complete scores already exist; reuse or explicitly verify in another directory.')
    out.mkdir(parents=True,exist_ok=True)
    grid=s.geometry(root,manifest);native=grid_native(manifest['grid_metadata'])
    old=s.read(root/'expected/historical-time-results.json')['records']
    spatial=s.read(root/'expected/historical-spatial-results.json')['records']
    records={r:{'coarse':{},'fine':{}} for r in ('old','refined','spatial')};comparisons={};checks={}
    for case,desc in manifest['protocols'].items():
        cfg=s.read(root/desc['config']);physics=s.Physics(protocol=case,**desc['physics'])
        items=[i for i in manifest['objects'] if i['protocol']==case]
        caches={i['id']:pred_cache(root,i,out,grid,native,physics) for i in items}
        for refname in records:
            ref,q=load_ref(root,desc,refname,grid,physics)
            native_q=None
            if refname=='spatial':
                nf,_=s.arrays(root/desc['native_spatial_reference']);s.canonical_coordinates(nf,native)
                native_q=s.deposition(nf,native,physics);del nf;gc.collect()
            for item in items:
                for level in ('coarse','fine'):
                    if level=='fine' and 'fine_prediction' not in item:continue
                    result=score_one(root,item,level,ref,q,physics,cfg,caches[item['id']],out,refname,
                        old['old'][case+'/29/E']['normalizers'],native_q)
                    records[refname][level][item['id']]=result
                    if level=='coarse' and item['origin']!='clean_pde_ablation':
                        expected=spatial[item['id']] if refname=='spatial' else old[refname][item['id']]
                        keys=('metrics','cycles','valid','strict_device_pass','event_failures')
                        n=s.compare_saved({k:result[k] for k in keys},{k:expected[k] for k in keys},item['id']+'/'+refname)
                        checks[refname+'/'+item['id']]=dict(passed=True,checked_values=n)
                    if level=='fine':
                        coarse=records[refname]['coarse'][item['id']]
                        for k in ('S','Ephi','ET','phase_max'):
                            s.compare_saved(result['metrics'][k],coarse['metrics'][k],'unchanged-field/'+k)
                        s.compare_saved(result['cycles'],coarse['cycles'],'unchanged-events')
                    s.save(out/'partial-results.json',records)
                    print(json.dumps(dict(scored=item['id'],reference=refname,reader=level)),flush=True)
            for level in ('coarse','fine'):
                rr=records[refname][level];pairs={}
                for seed in (29,43):
                    pre=f'{case}/{seed}/';e=rr[pre+'E'];f=rr[pre+'F'];be=rr[case+'/B_E']
                    pairs[str(seed)]={'E_vs_F':s.pair(e,f,cfg),'E_vs_B_E':s.pair(e,be,cfg)}
                    if pre+'D_E' in rr:
                        d=rr[pre+'D_E'];pairs[str(seed)].update(E_vs_D_E=s.pair(e,d,cfg),D_E_vs_E=s.pair(d,e,cfg),
                            D_E_vs_F=s.pair(d,f,cfg),D_E_vs_B_E=s.pair(d,be,cfg))
                comparisons.setdefault(refname,{}).setdefault(level,{})[case]=pairs
            del ref,q,native_q;gc.collect()
    result=dict(status='COMPLETE_ARRAY_ONLY_REPRODUCTION',records=records,decisions=comparisons,
        historical_reproduction=checks,execution=dict(isolated_python=bool(sys.flags.isolated),
            neural_models_loaded=0,neural_forwards=0,linear_solves=0,numpy=np.__version__,python=sys.version),
        interpretation='two readers of one learned state are not independent repetitions')
    if a.compare:
        expected=s.read(a.compare)
        n=s.compare_saved({'records':records,'decisions':comparisons},
            {k:expected[k] for k in ('records','decisions')},'extended-independent-directory')
        result['independent_directory_comparison']=dict(passed=True,checked_values=n,rtol=2e-10,atol=2e-12)
    s.save(out/'results.json',result)
    print(json.dumps(dict(status=result['status'],reproduced_historical_reference_objects=len(checks))),flush=True)

if __name__=='__main__':main()
