"""B1 array-only scoring after all six endpoints and fourteen readers lock.

Uses the existing portable full-history scorer, adds separately named A_w,
and never imports a training or electrical-solver module.
"""
import argparse
import gc
import importlib.util
import json
from pathlib import Path
import numpy as np
from .phk_v23_b1_metrics import window_records,outside_cost

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,default=ROOT/'outputs/runs/20260921-b1-second-cycle-phase-gap')
    p.add_argument('--archive',type=Path,default=ROOT/'outputs/submission-rescore-20260921')
    p.add_argument('--out',type=Path)
    p.add_argument('--dry-run',action='store_true')
    a=p.parse_args();run=a.run.resolve();archive=a.archive.resolve()
    if a.dry_run:
        print(json.dumps(dict(status='PARSED_NOT_EXECUTED',run=str(run),archive=str(archive),expected_records=42,
                              endpoints_present=(run/'all-endpoints-locked.json').is_file())))
        return
    read=lambda q:json.loads(q.read_text(encoding='utf-8'))
    if read(run/'all-endpoints-locked.json')['status']!='ALL_SIX_FIXED_ENDPOINTS_LOCKED':
        raise ValueError('All endpoints must lock before reference scoring')
    manifest=read(run/'readout-manifest.json')
    if manifest['status']!='ALL_FIXED_READERS_COMPLETE' or len(manifest['objects'])!=7:
        raise ValueError('Fourteen fixed readers required')
    # The original script resolves its sibling frozen metric modules itself.
    spec=importlib.util.spec_from_file_location('b1_frozen_reader',archive/'portable/readout_rescore.py')
    r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r);s=r.s
    out=(a.out or run/'scoring').resolve()
    if out.exists():raise FileExistsError('Score destination must be new')
    out.mkdir(parents=True)
    m=read(archive/'manifest.json');desc=m['protocols']['shorter'];cfg=read(archive/desc['config'])
    physics=s.Physics(protocol='shorter',**desc['physics'])
    grid=s.geometry(archive,m);native=r.grid_native(m['grid_metadata'])
    old=read(archive/'primary-rescore/results.json')['records']['old']['coarse']['shorter/29/E']['normalizers']
    items=manifest['objects'];caches={i['id']:r.pred_cache(ROOT,i,out,grid,native,physics) for i in items}
    records={};comparisons={};window_scores={}
    for refname in ('old','refined','spatial'):
        ref,q=r.load_ref(archive,desc,refname,grid,physics);nq=None
        if refname=='spatial':
            nf,_=s.arrays(archive/desc['native_spatial_reference']);nq=s.deposition(nf,native,physics);del nf;gc.collect()
        records[refname]={};window_scores[refname]={};comparisons[refname]={}
        for level in ('coarse','fine'):
            rr={};ww={}
            for item in items:
                rr[item['id']]=r.score_one(ROOT,item,level,ref,q,physics,cfg,caches[item['id']],out,refname,old,nq)
                fields,_=s.arrays(ROOT/item['prediction'])
                if level=='fine':
                    with np.load(ROOT/item['fine_prediction'],allow_pickle=False) as f:fields['potential']=r.restrict(f['potential'])
                with np.load(caches[item['id']]/(level+'.npz'),allow_pickle=False) as f:device={k:f[k] for k in f.files}
                ww[item['id']]=window_records(fields,ref,device,cfg)
                for k,v in ww[item['id']]['full']['metrics'].items():
                    np.testing.assert_allclose(v,rr[item['id']]['metrics'][k],rtol=2e-10,atol=2e-12)
                del fields,device;gc.collect()
                print(json.dumps(dict(scored=item['id'],reference=refname,reader=level)),flush=True)
            pairs={}
            for seed in (29,43):
                pre=f'shorter/{seed}/';e=pre+'E';pairs[str(seed)]={}
                for label,control in (('E_vs_D_E',pre+'D_E'),('E_vs_F',pre+'F'),('E_vs_B_E','shorter/B_E')):
                    pairs[str(seed)][label]=dict(full=s.pair(rr[e],rr[control],cfg),
                        A_w=r.core.comparison(ww[e]['window'],ww[control]['window'],cfg['decision']),
                        window_effects={k:dict(candidate_error=ww[e]['window']['metrics'][k],control_error=ww[control]['window']['metrics'][k],
                            signed_candidate_minus_control=ww[e]['window']['metrics'][k]-ww[control]['window']['metrics'][k],
                            relative_error_reduction=(1-ww[e]['window']['metrics'][k]/ww[control]['window']['metrics'][k])
                                if ww[control]['window']['metrics'][k]>0 else None,
                            candidate_minus_control_percentage_points=100*(ww[e]['window']['metrics'][k]-ww[control]['window']['metrics'][k])
                                if k in ('EI','bottom_current_NRMSE','power_trace_NRMSE') else None)
                            for k in ww[e]['window']['metrics']},
                        outside_cost_flags=outside_cost(ww[e]['outside'],ww[control]['outside'],cfg))
            records[refname][level]=rr;window_scores[refname][level]=ww;comparisons[refname][level]=pairs
            s.save(out/'partial-results.json',dict(records=records,windows=window_scores,comparisons=comparisons))
        del ref,q,nq;gc.collect()
    primary=[comparisons[ref][level][str(seed)]['E_vs_D_E'] for ref in comparisons for level in comparisons[ref] for seed in (29,43)]
    passes=[v['A_w']['passed'] for v in primary]
    if all(passes):
        route='ROBUST_CONDITIONAL_INCREMENT_WITH_OUTSIDE_COST' if any(any(v['outside_cost_flags'].values()) for v in primary) else 'ROBUST_CONDITIONAL_INCREMENT'
    elif any(passes) or any(any(v['A_w'].get('gain',{}).values()) for v in primary):route='MIXED_CONDITIONAL_EVIDENCE'
    else:route='PREDECLARED_INCREMENT_NOT_ESTABLISHED'
    count=sum(len(v) for levels in records.values() for v in levels.values());assert count==42
    s.save(out/'results.json',dict(status='COMPLETE_B1_ARRAY_SCORING',record_count=count,records=records,
        windows=window_scores,comparisons=comparisons,scientific_route=route,
        claim_status='SUPPORTED_INTERPRETATION',independent_initializations=2,new_observation_conditions=1,
        original_thresholds_unchanged=True,reference_used_for_training=False,publication_goal_achieved=False))
    print(json.dumps(dict(status='COMPLETE_B1_ARRAY_SCORING',records=count,route=route)),flush=True)


if __name__=='__main__':main()
