"""Recover N/S composite arrays and score locked endpoints using old metrics."""
from pathlib import Path
import argparse
import csv
import gc
import hashlib
import importlib.util
import json
import shutil
import zipfile
import numpy as np
from .phk_v23_b1_metrics import interval_weights,window_records,outside_cost

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'outputs/runs/20260924-observation-preserving-phase'
OLD=ROOT/'outputs/runs/20260921-b1-second-cycle-phase-gap'


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,v):Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def mapped_arrays(path):
    """Storage adapter: stream original NPY members to read-only memory maps.

    There is no field transformation, changed metric, or model evaluation.
    Only the newly imported isolated reader uses this adapter.
    """
    path=Path(path).resolve()
    key=hashlib.sha256(str(path).encode()).hexdigest()[:16]
    folder=RUN/'scoring/array-cache'/key;folder.mkdir(parents=True,exist_ok=True)
    stamp=dict(path=str(path),bytes=path.stat().st_size,mtime_ns=path.stat().st_mtime_ns)
    if (folder/'source.json').exists():assert read(folder/'source.json')==stamp
    else:save(folder/'source.json',stamp)
    values={}
    with zipfile.ZipFile(path) as source:
        names=set(source.namelist())
        for name in ('x','z','time','potential','temperature','phase','joule_density'):
            member=name+'.npy'
            if member not in names:
                if name=='joule_density':continue
                raise ValueError('Missing original array '+name)
            target=folder/member
            if not target.exists():
                temporary=target.with_suffix('.npy.partial')
                with source.open(member) as src,temporary.open('wb') as dst:shutil.copyfileobj(src,dst,4*1024*1024)
                temporary.replace(target)
            values[name]=np.load(target,mmap_mode='r',allow_pickle=False)
    return {k:values[k] for k in ('x','z','time','potential','temperature','phase')},values.get('joule_density')


def compose():
    if (RUN/'readout-manifest.json').exists():raise FileExistsError('Composite arrays already complete')
    assert read(RUN/'all-endpoints-locked.json')['status']=='ALL_THREE_FIXED_ENDPOINTS_LOCKED'
    cloud=read(RUN/'cloud-readout-manifest.json');base=next(v for v in read(OLD/'readout-manifest.json')['objects'] if v['id']=='shorter/29/E')
    with np.load(ROOT/base['prediction'],allow_pickle=False) as z:
        fields={k:z[k] for k in z.files}
    with np.load(ROOT/base['readout'],allow_pickle=False) as z:
        ports={k:z[k] for k in z.files}
    times=fields['time'];mutable=(times>1.36)&(times<2.02)
    checks={}
    for item in cloud['objects']:
        arm=item['role']
        if arm=='G':continue
        folder=RUN/'predictions'/arm
        with np.load(folder/'dark-phase.npz',allow_pickle=False) as z:
            np.testing.assert_array_equal(z['time'],times[mutable])
            np.testing.assert_array_equal(z['x'],fields['x']);np.testing.assert_array_equal(z['z'],fields['z'])
            corrected=fields['phase'].copy();corrected[mutable]=z['phase']
        differences={};spot_ports=read(folder/'own-field-spot-ports.json')
        with np.load(folder/'own-field-spot-checks.npz',allow_pickle=False) as z:
            for t in (.27,1.28,1.55,1.8):
                i=int(np.argmin(abs(times-t)));assert abs(times[i]-t)<1e-12
                for name in ('temperature','potential','joule_density'):
                    actual=z[str(t)+'/'+name];expected=fields[name][i]
                    np.testing.assert_allclose(actual,expected,rtol=2e-10,atol=2e-12)
                    differences[str(t)+'/'+name]=float(np.max(abs(actual-expected)))
                expected=corrected[i] if mutable[i] else fields['phase'][i]
                np.testing.assert_allclose(z[str(t)+'/phase'],expected,rtol=2e-10,atol=2e-12)
                for name,value in spot_ports[str(t)].items():
                    np.testing.assert_allclose(value,ports[name][i],rtol=2e-10,atol=2e-12)
                    differences[str(t)+'/'+name]=abs(value-float(ports[name][i]))
        np.testing.assert_array_equal(corrected[~mutable],fields['phase'][~mutable])
        target=ROOT/item['prediction']
        if target.exists():raise FileExistsError('Existing composite prediction requires specific recovery, not overwrite')
        np.savez_compressed(target,**{**fields,'phase':corrected})
        shutil.copyfile(ROOT/base['readout'],ROOT/item['readout'])
        checks[arm]=dict(passed=True,base_id=base['id'],base_prediction=base['prediction'],base_ports=base['readout'],
            reused_fields=['temperature','potential','joule_density'],phase_outside_D_exact=True,
            ports_reused=True,spot_differences=differences,
            reason='same T; same phase at every powered time; zero-drive V and q are identically zero; independent own-field spot checks passed',
            not_independent_electrical_evidence=True)
        save(folder/'composition-provenance.json',checks[arm])
        item['local_base_array_composition_required']=False
        del corrected;gc.collect()
    save(RUN/'invariance-array-checks.json',checks)
    save(RUN/'readout-manifest.json',dict(status='ALL_THREE_COMPLETE_NATIVE_COMPOSITE_READERS',objects=cloud['objects'],
        electrical_forward_solves=282,electrical_adjoint_solves=0,reference_read=False))
    print('NATIVE_COMPOSITE_ARRAYS_VERIFIED',flush=True)


def score():
    if (RUN/'scoring/results.json').exists():raise FileExistsError('Scores already complete')
    assert read(RUN/'readout-manifest.json')['status']=='ALL_THREE_COMPLETE_NATIVE_COMPOSITE_READERS'
    archive=ROOT/'outputs/submission-rescore-20260921';out=RUN/'scoring';out.mkdir(exist_ok=True)
    spec=importlib.util.spec_from_file_location('frozen_completion_reader',archive/'portable/readout_rescore.py')
    r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r);s=r.s
    # Bind a storage adapter in this isolated imported reader, leaving all
    # archived scientific functions and their arithmetic unchanged.
    s.arrays=mapped_arrays
    m=read(archive/'manifest.json');desc=m['protocols']['shorter'];cfg=read(archive/desc['config'])
    physics=s.Physics(protocol='shorter',**desc['physics']);grid=s.geometry(archive,m);native=r.grid_native(m['grid_metadata'])
    normal=read(archive/'b1/first-score/results.json')['records']['old']['coarse']['shorter/29/E']['normalizers']
    ref,qref=r.load_ref(archive,desc,'old',grid,physics)
    old=read(OLD/'readout-manifest.json')['objects'];items=[]
    for role,label in [('E','B0'),('D_E','D_E')]:
        # This development authorizes the existing common 160x80 reader only.
        item={k:v for k,v in next(v for v in old if v['id']=='shorter/29/'+role).items()
              if k not in ('fine_prediction','fine_readout')}
        item['role']=label;item['id']='shorter/29/'+label;items.append(item)
    items+=read(RUN/'readout-manifest.json')['objects']
    partial=read(out/'partial-results.json') if (out/'partial-results.json').exists() else {}
    records=partial.get('records',{});windows=partial.get('windows',{});parts=[];traces=dict(time=ref.time,reference=(ref.phase>=.5).mean(1))
    w=interval_weights(ref.time,[(1.01,2.02)]);dark=(ref.time>1.36)&(ref.time<2.02)
    rcfg=cfg['qualification_event']['roi'];g=ref.grid
    roi=(abs(g.cell_x)<=rcfg['abs_x_max'])&(g.cell_z>=rcfg['z_min'])&(g.cell_z<=rcfg['z_max'])
    truth=ref.phase>=cfg['qualification_event']['phase_threshold']
    for item in items:
        arm=item['role'];cache=r.pred_cache(ROOT,item,out,grid,native,physics)
        if arm not in records:
            records[arm]=r.score_one(ROOT,item,'coarse',ref,qref,physics,cfg,cache,out,'old',normal,None)
        fields,unused_q=s.arrays(ROOT/item['prediction']);del unused_q
        with np.load(cache/'coarse.npz',allow_pickle=False) as z:device={k:z[k] for k in z.files}
        if arm not in windows:windows[arm]=window_records(fields,ref,device,cfg)
        for k,v in windows[arm]['full']['metrics'].items():
            np.testing.assert_allclose(v,records[arm]['metrics'][k],rtol=2e-10,atol=2e-12)
        pred=fields['phase']>=.5;fn=np.mean(truth&~pred,1);fp=np.mean(~truth&pred,1)
        mse=np.mean((fields['phase'][:,roi]-ref.phase[:,roi])**2,axis=1)
        traces[arm]=pred.mean(1)
        row=dict(arm=arm,W_FN=float(w@fn),W_FP=float(w@fp),D_FN=float((w*dark)@fn),D_FP=float((w*dark)@fp),
            D_phase_square=float((w*dark)@mse),fixed_phase_square=float((w*~dark)@mse),
            phase_min=float(fields['phase'].min()),phase_max=float(fields['phase'].max()),
            fraction_exact_zero=float(np.mean(fields['phase']==0.)),fraction_exact_one=float(np.mean(fields['phase']==1.)))
        np.testing.assert_allclose(row['W_FN']+row['W_FP'],windows[arm]['window']['metrics']['S']*1.01,rtol=1e-12,atol=1e-14)
        parts.append(row)
        save(out/'partial-results.json',dict(records=records,windows=windows))
        del fields,device,pred;gc.collect();print(json.dumps(dict(scored=arm)),flush=True)
    pairs={}
    for candidate in records:
        for control in records:
            if candidate==control:continue
            c,d=windows[candidate],windows[control]
            pairs[candidate+'_vs_'+control]=dict(A_w=r.core.comparison(c['window'],d['window'],cfg['decision']),
                full=s.pair(records[candidate],records[control],cfg),outside_cost=outside_cost(c['outside'],d['outside'],cfg),
                relative_reduction={scope:{k:1-v/max(d[scope]['metrics'][k],1e-12) for k,v in c[scope]['metrics'].items()}
                    for scope in ('window','outside','full')})
    # Construction-invariant numerical fields and heated event entries are
    # checked separately from favorable metric comparisons.
    invariance=read(RUN/'invariance-array-checks.json')
    for arm in ('N','S'):
        for scope in windows[arm]:
            for key in ('ET','EI','EV','bottom_current_NRMSE','power_trace_NRMSE'):
                np.testing.assert_allclose(windows[arm][scope]['metrics'][key],windows['B0'][scope]['metrics'][key],rtol=0,atol=0)
        for key in ('S','Ephi'):
            np.testing.assert_allclose(windows[arm]['outside']['metrics'][key],windows['B0']['outside']['metrics'][key],rtol=0,atol=0)
        heated_keys=('event_time','reference_event_time','timing_absolute','recall','precision','mass_ratio',
            'support_window','teacher_active_target_mass','predicted_active_target_mass',
            'true_positive_target_mass','false_negative_target_mass','false_positive_target_mass')
        assert len(records[arm]['cycles'])==len(records['B0']['cycles'])
        for actual,expected in zip(records[arm]['cycles'],records['B0']['cycles']):
            for key in heated_keys:
                if actual[key] is None or expected[key] is None:
                    assert actual[key] is expected[key]
                else:
                    np.testing.assert_allclose(actual[key],expected[key],rtol=0,atol=1e-12)
        assert not records['B0']['strict_device_pass']
        assert not records[arm]['strict_device_pass']
        invariance[arm]['heated_event_fields_verified']=list(heated_keys)
        invariance[arm]['strict_failure_preserved']=True
    with (out/'phase-error-decomposition.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(parts[0]));writer.writeheader();writer.writerows(parts)
    np.savez_compressed(out/'active-traces.npz',**traces)
    save(out/'results.json',dict(status='COMPLETE_THREE_ARM_DEVELOPMENT_SCORING',records=records,windows=windows,pairs=pairs,
        decomposition=parts,invariance=invariance,independent_base_initializations=1,
        reference='original only',native_readout=[160,80],strict_event_definition_unchanged=True))
    print('COMPLETE_THREE_ARM_DEVELOPMENT_SCORING',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['compose','score']);a=p.parse_args()
    (compose if a.action=='compose' else score)()
