"""Select a declared object scope, reusing the frozen 18 September NumPy scorer."""
from pathlib import Path
import argparse
import gc
import importlib.util
import json
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('frozen_reader', HERE/'readout_rescore.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
s = r.s


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=HERE.parent)
    p.add_argument('--scope', choices=('original43', 'core', 'extension'), required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--validate-only', action='store_true')
    a = p.parse_args()
    root = a.root.resolve()
    m = s.read(root/'manifest.json')
    ids = ({'original/43/E', 'original/43/F', 'original/B_E'} if a.scope == 'original43'
           else set(m['scopes'][a.scope]))
    items = [i for i in m['objects'] if i['id'] in ids]
    required = {m['grid_arrays'], 'primary-rescore/results.json'}
    for item in items:
        required.update(item[k] for k in ('prediction','readout','fine_prediction','fine_readout') if k in item)
        desc = m['protocols'][item['protocol']]
        required.update(desc['references'].values())
        required.update((desc['config'], desc['native_spatial_reference']))
    missing = sorted(name for name in required if not (root/name).is_file())
    if missing:
        p.exit(2, 'Missing saved input(s); no automatic regeneration: '+', '.join(missing)+'\n')
    if a.validate_only:
        print(json.dumps({'status':'INPUTS_PRESENT', 'scope':a.scope, 'objects':len(items)}))
        return
    out = s.locate(root, a.out)
    if out.exists():
        raise FileExistsError('Output must be a new clean directory: '+str(out))
    out.mkdir(parents=True)
    expected = s.read(root/'primary-rescore/results.json')
    grid = s.geometry(root,m)
    native = r.grid_native(m['grid_metadata'])
    records = {ref:{'coarse':{}, 'fine':{}} for ref in ('old','refined','spatial')}
    decisions = {}
    checked = 0
    for case, desc in m['protocols'].items():
        selected = [i for i in items if i['protocol'] == case]
        if not selected:
            continue
        cfg = s.read(root/desc['config'])
        physics = s.Physics(protocol=case, **desc['physics'])
        caches = {i['id']:r.pred_cache(root,i,out,grid,native,physics) for i in selected}
        for refname in records:
            ref,q = r.load_ref(root,desc,refname,grid,physics)
            native_q = None
            if refname == 'spatial':
                nf,_ = s.arrays(root/desc['native_spatial_reference'])
                s.canonical_coordinates(nf,native)
                native_q = s.deposition(nf,native,physics)
                del nf
                gc.collect()
            for item in selected:
                for level in ('coarse','fine'):
                    if level == 'fine' and 'fine_prediction' not in item:
                        continue
                    result = r.score_one(root,item,level,ref,q,physics,cfg,caches[item['id']],out,
                        refname,expected['records']['old']['coarse'][case+'/29/E']['normalizers'],native_q)
                    checked += s.compare_saved(result,expected['records'][refname][level][item['id']],item['id']+'/'+refname+'/'+level)
                    records[refname][level][item['id']] = result
                    s.save(out/'partial-results.json',records)
                    print(json.dumps({'scored':item['id'],'reference':refname,'reader':level}),flush=True)
            for level in ('coarse','fine'):
                rr = records[refname][level]
                pairs = {}
                for seed in (29,43):
                    pre = f'{case}/{seed}/'
                    if pre+'E' not in rr:
                        continue
                    e,f,be = rr[pre+'E'],rr[pre+'F'],rr[case+'/B_E']
                    pair = dict(E_vs_F=s.pair(e,f,cfg), E_vs_B_E=s.pair(e,be,cfg))
                    if pre+'D_E' in rr:
                        d=rr[pre+'D_E']
                        pair.update(E_vs_D_E=s.pair(e,d,cfg), D_E_vs_E=s.pair(d,e,cfg),
                                    D_E_vs_F=s.pair(d,f,cfg), D_E_vs_B_E=s.pair(d,be,cfg))
                    checked += s.compare_saved(pair,expected['decisions'][refname][level][case][str(seed)],f'{refname}/{level}/{case}/{seed}')
                    pairs[str(seed)] = pair
                if pairs:
                    decisions.setdefault(refname,{}).setdefault(level,{})[case] = pairs
            del ref,q,native_q
            gc.collect()
    count = sum(len(rr) for levels in records.values() for rr in levels.values())
    assert count == {'original43':18, 'core':72, 'extension':18}[a.scope]
    result = dict(status='PASS_FROZEN_ARRAY_RESCORING',scope=a.scope,records=records,decisions=decisions,
        record_count=count,comparison=dict(passed=True,checked_values=checked,rtol=2e-10,atol=2e-12,booleans='exact'),
        execution=dict(isolated_python=bool(sys.flags.isolated),numpy=np.__version__,python=sys.version,
                       neural_models_loaded=0,neural_forwards=0,linear_solves=0),
        interpretation='same frozen scoring implementation; not independent implementation or retraining')
    s.save(out/'results.json',result)
    print(json.dumps({'status':result['status'],'scope':a.scope,'records':count,'checked_values':checked}),flush=True)


if __name__ == '__main__':
    main()
