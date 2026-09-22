"""Package completed B1 arrays before their first unified NumPy-only scoring."""
from pathlib import Path
import copy
import hashlib
import json
import os
import shutil

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT/'outputs/runs/20260921-b1-second-cycle-phase-gap'
CORE = ROOT/'outputs/submission-rescore-20260921'
DEST = CORE/'b1'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')

def link(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix=='.npz':
        os.link(src, dst)
    else:
        shutil.copy2(src, dst)

def main():
    closure = read(RUN/'compute-closure.json')
    assert closure['recovery_verified'] and closure['instance_shutdown_confirmed']
    assert read(RUN/'all-endpoints-locked.json')['status']=='ALL_SIX_FIXED_ENDPOINTS_LOCKED'
    readers = read(RUN/'readout-manifest.json')
    assert readers['status']=='ALL_FIXED_READERS_COMPLETE' and len(readers['objects'])==7
    if DEST.exists():
        raise FileExistsError('B1 package already exists; inspect its status, do not overwrite')
    DEST.mkdir()
    original = read(CORE/'manifest.json')
    reference = copy.deepcopy(original)
    desc = reference['protocols']['shorter']
    for key in ('sparse', 'expected_decisions'):
        desc.pop(key, None)
    reference['protocols'] = {'shorter':desc}
    reference['objects'] = []
    reference['scope'] = 'Fixed reference definitions for B1; predictors are in run/readout-manifest.json'
    archive = DEST/'reference-inputs'
    paths = [original['grid_arrays'], desc['config'], *desc['references'].values(),
             desc['native_spatial_reference'], 'primary-rescore/results.json']
    old_integrity = {r['path']:r for r in read(CORE/'integrity.json')['files']}
    integrity = []
    for name in paths:
        link(CORE/name, archive/name)
        if name in old_integrity:
            integrity.append({**old_integrity[name], 'path':'reference-inputs/'+name,
                              'hash_origin':'reused frozen core input digest; no rehash'})
    save(archive/'manifest.json', reference)
    for src in (CORE/'portable').glob('*.py'):
        link(src, archive/'portable'/src.name)
    for item in readers['objects']:
        for key in ('prediction','readout','fine_prediction','fine_readout'):
            src = ROOT/item[key]
            target = DEST/'run'/src.relative_to(RUN)
            link(src,target)
            with src.open('rb') as stream:
                digest = hashlib.file_digest(stream,'sha256').hexdigest()
            integrity.append(dict(path=target.relative_to(DEST).as_posix(),size=src.stat().st_size,
                                  sha256=digest,hash_origin='new B1 fixed input; computed once'))
            item[key] = target.relative_to(DEST).as_posix()
    save(DEST/'run/readout-manifest.json',readers)
    for name in ('all-endpoints-locked.json','frozen-config.json','visible-statistics.json','compute-closure.json','deployment.json'):
        link(RUN/name,DEST/'run'/name)
    package = DEST/'pinn_pcm_sci'
    package.mkdir()
    (package/'__init__.py').write_text('"""Array-only B1 scorer; no training imports."""\n',encoding='utf-8')
    for name in ('phk_v23_b1_evaluate.py','phk_v23_b1_metrics.py'):
        link(ROOT/'pinn_pcm_sci'/name, package/name)
    entry = DEST/'portable/score_b1.py'
    entry.parent.mkdir()
    entry.write_text('''"""Score all 42 B1 records from this directory alone; NumPy only."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from pinn_pcm_sci.phk_v23_b1_evaluate import main
sys.argv.extend(['--run',str(root/'run'),'--archive',str(root/'reference-inputs')])
main()
''',encoding='utf-8')
    save(DEST/'integrity.json',dict(algorithm='sha256',files=integrity,
                                  scope='new predictor digests once; reference digests reused'))
    (DEST/'README.md').write_text('''# B1 saved-array package

Local, portable array-only package; not a public release. Seven scientific
objects (two seeds times E/D_E/F plus one B_E), two electrical readers and
three numerical references yield 42 records, not 42 independent samples.

From this directory with Python 3.11 and NumPy 2.1.1:

```text
python -I portable/score_b1.py --out first-score
```

The existing full-history kernels and frozen B1 window kernels are copied
unchanged. Only relative input locations are adapted. No Torch, network
evaluation, linear solve, trajectory generation or checkpoint is required.
All endpoints/readers must be complete; missing inputs raise errors and are
never regenerated. An existing score output directory cannot be overwritten.
Window, outside and full measures retain their separate normalizers; old
A/B/strict rules and the separately named A_w are reported without retuning.

Large arrays use ordinary local hard links. Copying the complete directory
materializes normal files and needs neither the original run directory nor
the parent core package. The local training runtime and weights are separate
reproduction assets. Dataset access/redistribution permissions remain pending.
''',encoding='utf-8')
    save(DEST/'package-status.json',dict(status='INPUTS_PACKAGED_NOT_YET_SCORED',objects=7,
        expected_records=42,neural_queries=0,electrical_solves=0,reference_steps=0,
        source_recovery_sha256=closure['recovery_sha256']))
    print(json.dumps(dict(status='B1_ARRAY_PACKAGE_READY',root=str(DEST),expected_records=42)),flush=True)

if __name__=='__main__':
    main()
