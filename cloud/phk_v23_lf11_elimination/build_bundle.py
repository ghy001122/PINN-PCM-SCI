"""Selected-code deployment; no full reference, stress or unrelated dirty files."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[2]
RUN = Path('outputs/runs/20260913-lf11-electrical-elimination')


def dependency_files():
    found, pending = set(), ['__init__', 'phk_v23_lf11_elimination', 'phk_v23_lf11_elimination_predict', 'phk_v22r_prediction']
    while pending:
        module = pending.pop()
        path = Path('pinn_pcm_sci')/(module+'.py')
        if path in found: continue
        if not (ROOT/path).is_file(): raise FileNotFoundError(path)
        found.add(path)
        tree = ast.parse((ROOT/path).read_text(encoding='utf-8-sig'))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
                pending.append(node.module)
    return found | {Path('pinn_pcm_sci/__init__.py')}


def build():
    files = dependency_files()
    files |= {Path('configs')/v/n for v in ('phk_v2', 'phk_v21') for n in ('program_contract.json', 'object_numerical_contract.json')}
    files |= {Path('configs/phk_v23/lf11_elimination_sprint.json'),
              Path('configs/phk_v21/engineering_contract.json'),
              Path('configs/phk_v21/e1_solver_selection.json'),
              Path('outputs/runs/20260827T-phk-v21-e2-engineering-search-001/summary.json'),
              Path('tests/test_phk_v21_benchmark.py'),
              Path('paper/paper_v27/evidence/D_I/checkpoint.pt'), Path('paper/paper_v24/evidence/input/sparse.npz'),
              Path('cloud/phk_v23_lf11_elimination/run.sh')}
    files |= {RUN/n for n in ('parent.pt', 'frozen-config.json', 'calibration.json', 'input-manifest.json',
                              'calibration-pool.json', 'lbfgs-pool.json', 'audit-pool.json', 'zero-update-checks-cpu.json')}
    directory = ROOT/'.t/lf11-elimination-deployment'
    directory.mkdir(parents=True, exist_ok=True)
    manifest = {str(p).replace('\\','/'): hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(files)}
    (directory/'selected-files.json').write_text(json.dumps(manifest, indent=2))
    archive = directory/'lf11-elimination.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for path in sorted(files): tar.add(ROOT/path, arcname=path.as_posix(), recursive=False)
        tar.add(directory/'selected-files.json', arcname='selected-files.json')
    print(json.dumps({'archive': str(archive), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                      'no_reference_fields': True, 'no_stress_fields': True, 'no_full_medium_fields': True}))


if __name__ == '__main__': build()
