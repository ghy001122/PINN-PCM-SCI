"""Build an isolated, reference-free archive from a bounded dependency closure."""
from pathlib import Path
import ast
import hashlib
import json
import tarfile

ROOT=Path(__file__).resolve().parents[2]
RUN=Path('outputs/runs/20260923-relative-phase-moments')
OLD=Path('outputs/runs/20260921-b1-second-cycle-phase-gap')
files=set();pending=[Path('pinn_pcm_sci/__init__.py'),Path('pinn_pcm_sci/phk_v23_phase_moments_run.py'),Path('pinn_pcm_sci/phk_v23_phase_moments_readout.py')]
while pending:
    p=pending.pop()
    if p in files or not (ROOT/p).is_file():continue
    files.add(p)
    for node in ast.walk(ast.parse((ROOT/p).read_text(encoding='utf-8-sig'))):
        if isinstance(node,ast.ImportFrom) and node.level==1 and node.module:
            pending.append(Path('pinn_pcm_sci')/(node.module.replace('.','/')+'.py'))
files.add(Path('pinn_pcm_sci/__init__.py'))
files.update(map(Path,['configs/phk_v21/program_contract.json','configs/phk_v21/object_numerical_contract.json',
    'configs/phk_v21/engineering_contract.json','configs/phk_v21/e1_solver_selection.json',
    'tests/test_phk_v21_benchmark.py','configs/phk_v2/program_contract.json',
    'configs/phk_v2/object_numerical_contract.json','configs/phk_v23/phase_moments_20260923.json',
    'outputs/runs/20260827T-phk-v21-e2-engineering-search-001/summary.json']))
files.add(OLD/'input/visible-fields.npz')
files.update(OLD/'seed-29'/n for n in ('parent.pt','calibration.json','lbfgs-pool.json','audit-pool.json'))
files.update(RUN/n for n in ('prepared.json','frozen-config.json','input-manifest.json','resource-approval.json',
    'calibration.json','phase-calibration.json','phase-calibration-pool.json','phase-fixed-pool.json','quadrature.json','profile.json'))
manifest=dict(task_id='PCM-20260922-RELATIVE-PHASE-MOMENTS-01',files=sorted(p.as_posix() for p in files),
    input_arrays=[(OLD/'input/visible-fields.npz').as_posix()],reference_arrays=0,
    parent_checkpoints=[(OLD/'seed-29/parent.pt').as_posix()],trained_old_endpoints=0,
    science='same physics, observations, parent, and frozen eight-arm development contract',
    source_commit='192f9551692e7b1f63add946cc8fb77295818542',local_source_changes=True)
(ROOT/RUN/'deployment-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
archive=ROOT/'outputs/staging-phase-moments-20260923.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
    for p in sorted(files):tar.add(ROOT/p,arcname=p.as_posix(),recursive=False)
    tar.add(ROOT/RUN/'deployment-manifest.json',arcname='runtime-manifest.json')
    tar.add(Path(__file__).with_name('run_cloud.py'),arcname='run_cloud.py')
with archive.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
(ROOT/RUN/'deployment-archive.json').write_text(json.dumps(dict(path=str(archive),sha256=sha,bytes=archive.stat().st_size),indent=2),encoding='utf-8')
print(json.dumps(dict(archive=str(archive),sha256=sha,bytes=archive.stat().st_size)))
