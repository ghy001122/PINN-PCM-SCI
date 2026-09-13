"""Selected unchanged inputs plus new fixed-objective code; no reference arrays."""
import ast
import hashlib
import json
from pathlib import Path
import tarfile

ROOT=Path(__file__).resolve().parents[2]


def build():
    files=set()
    pending=['__init__','phk_v23_lf11_remaining_pde','phk_v23_lf11_elimination_predict','phk_v22r_prediction']
    while pending:
        module=pending.pop()
        path=Path('pinn_pcm_sci')/(module+'.py')
        if path in files: continue
        files.add(path)
        tree=ast.parse((ROOT/path).read_text(encoding='utf-8-sig'))
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom) and node.level==1 and node.module: pending.append(node.module)
    files|={Path('configs')/v/n for v in ('phk_v2','phk_v21') for n in ('program_contract.json','object_numerical_contract.json')}
    files|={Path(p) for p in ('configs/phk_v21/engineering_contract.json','configs/phk_v21/e1_solver_selection.json',
        'outputs/runs/20260827T-phk-v21-e2-engineering-search-001/summary.json','tests/test_phk_v21_benchmark.py',
        'configs/phk_v23/lf11_remaining_pde_sprint.json','paper/paper_v24/evidence/input/sparse.npz',
        'cloud/phk_v23_lf11_remaining_pde/run.sh')}
    files|={Path('paper/paper_v28/evidence')/p for p in ('parent.pt','D_E/checkpoint.pt','P_E/checkpoint.pt',
        'calibration.json','calibration-pool.json','lbfgs-pool.json','audit-pool.json','fixed-endpoint-unlabeled-audit.json')}
    directory=ROOT/'.t/lf11-remaining-deployment'
    directory.mkdir(parents=True,exist_ok=True)
    manifest={p.as_posix():hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(files)}
    (directory/'selected-files.json').write_text(json.dumps(manifest,indent=2))
    archive=directory/'lf11-remaining.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        for path in sorted(files): tar.add(ROOT/path,arcname=path.as_posix(),recursive=False)
        tar.add(directory/'selected-files.json',arcname='selected-files.json')
    print(json.dumps({'archive':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'no_reference_or_stress':True}))


if __name__=='__main__': build()
