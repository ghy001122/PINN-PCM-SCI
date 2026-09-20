"""Stage only frozen learned states, sparse data, code and known physics."""
import ast
import hashlib
import json
from pathlib import Path
import tarfile

ROOT=Path(__file__).resolve().parents[2]
RUN=Path('outputs/runs/20260918-lf11-readout-clean-pde')

def build():
    files=set();pending=['__init__','phk_v23_readout_clean_pde']
    while pending:
        module=pending.pop();path=Path('pinn_pcm_sci')/(module+'.py')
        if path in files:continue
        files.add(path)
        for node in ast.walk(ast.parse((ROOT/path).read_text(encoding='utf-8-sig'))):
            if isinstance(node,ast.ImportFrom) and node.level==1 and node.module:pending.append(node.module)
    files|={Path('configs')/v/n for v in ('phk_v2','phk_v21') for n in ('program_contract.json','object_numerical_contract.json')}
    files|={Path(p) for p in ('configs/phk_v21/engineering_contract.json','configs/phk_v21/e1_solver_selection.json',
        'outputs/runs/20260827T-phk-v21-e2-engineering-search-001/summary.json','tests/test_phk_v21_benchmark.py',
        'configs/phk_v23/lf11_readout_clean_pde_sprint.json','cloud/phk_v23_readout_clean_pde/run.sh')}
    manifest=json.loads((ROOT/RUN/'input-manifest.json').read_text(encoding='utf-8'))
    for r in manifest['objects']:
        files|={Path(r['config']),Path(r['sparse'])}
        if r['checkpoint']:files.add(Path(r['checkpoint']))
    files|={RUN/n for n in ('input-manifest.json','frozen-config.json','interface-checks.json')}
    for seed in (29,43):
        files|={RUN/'clean-pde'/f'seed-{seed}'/n for n in ('parent.pt','frozen-config.json','calibration.json',
            'calibration-pool.json','lbfgs-pool.json','audit-pool.json')}
    assert not any('local-reference' in p.as_posix() or p.name=='prediction.npz' for p in files)
    out=ROOT/'.t/readout-clean-pde-deployment';out.mkdir(parents=True,exist_ok=True)
    listing={p.as_posix():hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(files)}
    (out/'selected-files.json').write_text(json.dumps(listing,indent=2),encoding='utf-8')
    archive=out/'readout-clean-pde.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        for path in sorted(files):tar.add(ROOT/path,arcname=path.as_posix(),recursive=False)
        tar.add(out/'selected-files.json',arcname='selected-files.json')
    print(json.dumps(dict(archive=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        no_reference_arrays=True,no_stress=True)))

if __name__=='__main__':build()
