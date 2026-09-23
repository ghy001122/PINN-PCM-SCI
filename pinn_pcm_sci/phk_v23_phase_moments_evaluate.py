"""Array-only original-reference evaluation of all eight locked development arms.

Uses the existing frozen metric implementation and thresholds. No models,
training utilities or electrical linear solves are imported here.
"""
import argparse
import csv
import gc
import importlib.util
import json
from pathlib import Path
import numpy as np
from .phk_v23_b1_metrics import window_records,outside_cost,interval_weights

ROOT=Path(__file__).resolve().parents[1]
ARMS=('D','P','L','R','I','RI','RIM','G')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,default=ROOT/'outputs/runs/20260923-relative-phase-moments')
    p.add_argument('--archive',type=Path,default=ROOT/'outputs/submission-rescore-20260921')
    a=p.parse_args();run=a.run.resolve();archive=a.archive.resolve()
    assert read(run/'all-endpoints-locked.json')['status']=='ALL_EIGHT_FIXED_ENDPOINTS_LOCKED'
    manifest=read(run/'readout-manifest.json')
    assert manifest['status']=='ALL_EIGHT_NATIVE_READERS_COMPLETE'
    assert [v['role'] for v in manifest['objects']]==list(ARMS)
    out=run/'scoring'
    if (out/'results.json').exists():raise FileExistsError('Completed scores exist; reuse them')
    out.mkdir(exist_ok=True)
    spec=importlib.util.spec_from_file_location('phase_moments_frozen_reader',archive/'portable/readout_rescore.py')
    r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r);s=r.s
    m=read(archive/'manifest.json');desc=m['protocols']['shorter'];cfg=read(archive/desc['config'])
    physics=s.Physics(protocol='shorter',**desc['physics'])
    grid=s.geometry(archive,m);native=r.grid_native(m['grid_metadata'])
    old=read(archive/'b1/first-score/results.json')['records']['old']['coarse']['shorter/29/E']['normalizers']
    ref,qref=r.load_ref(archive,desc,'old',grid,physics)
    records={};windows={};decomposition=[];active_traces={'time':ref.time,'reference_active':(ref.phase>=.5).mean(1)}
    weights={name:interval_weights(ref.time,[pair]) for name,pair in
             [('heating',(1.01,1.36)),('subsequent',(1.36,2.02)),('W',(1.01,2.02))]}
    truth=ref.phase>=.5
    for item in manifest['objects']:
        arm=item['role'];cache=r.pred_cache(ROOT,item,out,grid,native,physics)
        record=r.score_one(ROOT,item,'coarse',ref,qref,physics,cfg,cache,out,'old',old,None)
        fields,_=s.arrays(ROOT/item['prediction'])
        with np.load(cache/'coarse.npz',allow_pickle=False) as f:device={k:f[k] for k in f.files}
        windows[arm]=window_records(fields,ref,device,cfg);records[arm]=record
        for k,v in windows[arm]['full']['metrics'].items():
            np.testing.assert_allclose(v,record['metrics'][k],rtol=2e-10,atol=2e-12)
        active=fields['phase']>=.5;fn=np.mean(truth&~active,axis=1);fp=np.mean(~truth&active,axis=1)
        active_traces.update({arm+'/active':active.mean(1),arm+'/FN':fn,arm+'/FP':fp})
        row=dict(arm=arm)
        for name,w in weights.items():
            row.update({name+'_FN_integral':float(w@fn),name+'_FP_integral':float(w@fp)})
        np.testing.assert_allclose(row['W_FN_integral']+row['W_FP_integral'],
                                   windows[arm]['window']['metrics']['S']*1.01,rtol=1e-12,atol=1e-14)
        decomposition.append(row)
        s.save(out/'partial-results.json',dict(records=records,windows=windows))
        del fields,device,active;gc.collect()
        print(json.dumps(dict(scored=arm,reference='old',reader='160x80')),flush=True)
    pairs={}
    for candidate in ARMS:
        for control in ARMS:
            if candidate==control:continue
            cw,dw=windows[candidate],windows[control]
            pairs[candidate+'_vs_'+control]=dict(full=s.pair(records[candidate],records[control],cfg),
                A_w=r.core.comparison(cw['window'],dw['window'],cfg['decision']),
                outside_cost_flags=outside_cost(cw['outside'],dw['outside'],cfg),
                continuous_effects={scope:{k:dict(candidate_error=v,control_error=dw[scope]['metrics'][k],
                    signed_difference=v-dw[scope]['metrics'][k],
                    relative_error_reduction=1-v/dw[scope]['metrics'][k] if dw[scope]['metrics'][k]>0 else None)
                    for k,v in cw[scope]['metrics'].items()} for scope in ('window','outside','full')})
    np.savez_compressed(out/'active-error-traces.npz',**active_traces)
    with (out/'phase-error-decomposition.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(decomposition[0]));w.writeheader();w.writerows(decomposition)
    s.save(out/'results.json',dict(status='COMPLETE_EIGHT_ARM_DEVELOPMENT_SCORING',records=records,windows=windows,
        comparisons=pairs,independent_initializations=1,reference='old',reader=[160,80],
        original_thresholds_unchanged=True,reference_used_for_training=False,new_reference_solves=0,
        claim_status='VERIFIED_METRICS_NOT_CONFIRMATION',raw_audits='../endpoint-audits.json'))
    print(json.dumps(dict(status='COMPLETE_EIGHT_ARM_DEVELOPMENT_SCORING',records=8)))


if __name__=='__main__':main()
