"""Twelve post-lock records for two F_cov endpoints; original A/B unchanged."""
from pathlib import Path
import argparse,gc,importlib.util,json,sys,time
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import recompute as isolation
RUN=ROOT/'outputs/runs/20260926-core-revision-vo2-bridge'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--expected');a=p.parse_args()
    isolation.validate();isolation.install_storage()
    out=(ROOT/a.out).resolve()
    if not out.is_relative_to(ROOT) or Path(a.out).is_absolute():raise ValueError('Output must remain below package root')
    if out.exists():raise FileExistsError(out)
    # No partial endpoint enters this comparison, even if E would look better.
    for seed in (29,43):
        t=read(RUN/f'fcov/seed-{seed}/F_cov/terminal.json')
        if t['status']!='VALID_FIXED_ENDPOINT':raise RuntimeError('Incomplete F_cov is not an E comparison')
        for grid in ('coarse','fine'):
            if read(RUN/f'fcov/seed-{seed}/F_cov/{grid}/readers-complete.json')['status']!='PASS':raise RuntimeError('Incomplete reader')
    out.mkdir(parents=True);started=time.perf_counter()
    archive=ROOT/'outputs/submission-rescore-20260921'
    spec=importlib.util.spec_from_file_location('coverage_frozen_reader',archive/'portable/readout_rescore.py')
    r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r);s=r.s
    m=read(archive/'manifest.json');desc=m['protocols']['shorter'];cfg=read(archive/desc['config'])
    physics=s.Physics(protocol='shorter',**desc['physics']);grid=s.geometry(archive,m);native=r.grid_native(m['grid_metadata'])
    old=read(archive/'primary-rescore/results.json');items=[]
    for seed in (29,43):
        prefix=(RUN/f'fcov/seed-{seed}/F_cov').relative_to(ROOT).as_posix()
        items.append(dict(id=f'shorter/{seed}/F_cov',protocol='shorter',seed=seed,role='F_cov',origin='mixed_measure_coverage_enhancement',
            prediction=prefix+'/coarse/projected/prediction.npz',readout=prefix+'/coarse/projected/own-readout.npz',
            fine_prediction=prefix+'/fine/projected/prediction.npz',fine_readout=prefix+'/fine/projected/own-readout.npz'))
    cache={i['id']:r.pred_cache(ROOT,i,out,grid,native,physics) for i in items}
    records={};comparisons={};effects={}
    for refname in ('old','refined','spatial'):
        ref,q=r.load_ref(archive,desc,refname,grid,physics);nq=None
        if refname=='spatial':
            nf,_=s.arrays(archive/desc['native_spatial_reference']);nq=s.deposition(nf,native,physics);del nf;gc.collect()
        records[refname]={};comparisons[refname]={};effects[refname]={}
        for level in ('coarse','fine'):
            records[refname][level]={};comparisons[refname][level]={};effects[refname][level]={}
            for item in items:
                seed=item['seed'];key=item['id'];prefix=f'shorter/{seed}/'
                v=r.score_one(ROOT,item,level,ref,q,physics,cfg,cache[key],out,refname,
                    old['records']['old']['coarse']['shorter/29/E']['normalizers'],nq)
                records[refname][level][key]=v
                baseline=old['records'][refname][level];e=baseline[prefix+'E'];f=baseline[prefix+'F'];be=baseline['shorter/B_E'];de=baseline[prefix+'D_E']
                pairs={};changes={}
                for label,c,d in [('E_vs_F_cov',e,v),('F_cov_vs_E',v,e),('F_cov_vs_F',v,f),('F_cov_vs_B_E',v,be),('F_cov_vs_D_E',v,de)]:
                    pairs[label]=s.pair(c,d,cfg)
                    changes[label]={k:dict(candidate=c['metrics'][k],control=d['metrics'][k],
                        signed_candidate_minus_control=c['metrics'][k]-d['metrics'][k],
                        relative_error_reduction=1-c['metrics'][k]/d['metrics'][k] if d['metrics'][k]>0 else None)
                        for k in ('S','Ephi','ET','EV','EI','bottom_current_NRMSE','power_trace_NRMSE','local_joule_NRMSE')}
                comparisons[refname][level][str(seed)]=pairs;effects[refname][level][str(seed)]=changes
                s.save(out/'partial-results.json',dict(records=records,comparisons=comparisons,effects=effects))
                print(json.dumps(dict(scored=key,reference=refname,reader=level)),flush=True)
        del ref,q,nq;gc.collect()
    result=dict(status='COMPLETE_F_COV_FIXED_ENDPOINT_SCORING',record_count=12,independent_initializations=2,
        records=records,comparisons=comparisons,effects=effects,thresholds_unchanged=True,
        original_network_readouts_retained=True,reference_used_for_training=False,
        interpretation='Mixed-measure coverage enhancement; neither a pure spatial coverage contrast nor an isolated VJP effect',
        execution=dict(seconds=time.perf_counter()-started,original_repository_access_denied=True,
            neural_inferences=0,electrical_solves=0,new_trajectories=0))
    if a.expected:
        expected=(ROOT/a.expected).resolve()
        if not expected.is_relative_to(ROOT):raise ValueError('Expected record escapes package root')
        prior=read(expected);keys=('records','comparisons','effects')
        result['verification']=dict(checked_values=s.compare_saved({k:result[k] for k in keys},{k:prior[k] for k in keys},'F_cov'),
            rtol=2e-10,atol=2e-12,booleans='exact',passed=True)
    s.save(out/'results.json',result);print(json.dumps(dict(status=result['status'],verification=result.get('verification'))),flush=True)
if __name__=='__main__':main()
