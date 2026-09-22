"""Stage a source/visible-data-only runtime; no reference arrays or old weights."""
import ast
import argparse
import json
from pathlib import Path
import shutil
import tarfile

ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'outputs/b1-runtime-20260921'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh-preparation',action='store_true')
    args=parser.parse_args()
    if DEST.exists():
        previous=json.loads((DEST/'runtime-manifest.json').read_text(encoding='utf-8'))
        if not args.refresh_preparation or previous['status']!='STAGED_NOT_EXECUTED' or list(DEST.rglob('*.pt')):
            raise FileExistsError('Only this unexecuted preparation package may be refreshed')
    pending=['__init__','phk_v23_b1'];modules=set()
    while pending:
        name=pending.pop()
        if name in modules:continue
        path=ROOT/'pinn_pcm_sci'/(name+'.py')
        if not path.is_file():continue
        modules.add(name)
        tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):
                if node.level==1 and node.module:pending.append(node.module.split('.')[0])
                elif node.module and node.module.startswith('pinn_pcm_sci.'):
                    pending.append(node.module.split('.')[1])
            elif isinstance(node,ast.Import):
                pending.extend(n.name.split('.')[1] for n in node.names if n.name.startswith('pinn_pcm_sci.'))
    paths=['pinn_pcm_sci/'+m+'.py' for m in sorted(modules)]
    paths+=['configs/phk_v21/program_contract.json','configs/phk_v21/object_numerical_contract.json',
            'configs/phk_v21/engineering_contract.json','configs/phk_v21/e1_solver_selection.json',
            'tests/test_phk_v21_benchmark.py',
            'configs/phk_v2/program_contract.json','configs/phk_v2/object_numerical_contract.json',
            'configs/phk_v23/lf11_b1_sprint.json']
    physical=json.loads((ROOT/'configs/phk_v21/object_numerical_contract.json').read_text(encoding='utf-8'))
    paths.append('outputs/runs/'+physical['engineering_bindings']['e2_run_id']+'/summary.json')
    paths.extend([physical['base_identity']['legacy_operator_implementation_path'],'pinn_pcm_sci/phk_v21_solver.py'])
    paths=list(dict.fromkeys(paths))
    run='outputs/runs/20260921-b1-second-cycle-phase-gap/'
    paths += [run+n for n in ('frozen-config.json','prepared.json','visible-statistics.json','input/visible-fields.npz')]
    for name in paths:
        src=ROOT/name;dst=DEST/name
        if not src.is_file():raise FileNotFoundError(src)
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    assert not list(DEST.rglob('*.pt')) and len(list(DEST.rglob('*.npz')))==1
    manifest=dict(task_id='PCM-20260921-FINAL-SPRINT-B1-01',status='STAGED_NOT_EXECUTED',files=paths,
        input_arrays=[run+'input/visible-fields.npz'],old_checkpoints=0,reference_arrays=0,
        authority='stage 2 local staging only; stage 3 resource approval remains required',
        dependencies=['Python 3.11','NumPy','SciPy','PyTorch; platform-specific GPU build only after resource confirmation'])
    (DEST/'runtime-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    target=ROOT/'outputs/b1-runtime-20260921.tar.gz'
    with tarfile.open(target,'w:gz' if args.refresh_preparation else 'x:gz') as tar:
        for name in sorted(paths+['runtime-manifest.json']):
            tar.add(DEST/name,arcname=name,recursive=False)
    print(json.dumps(dict(staged=str(DEST),archive=str(target),bytes=target.stat().st_size,
                          old_checkpoints=0,reference_arrays=0,visible_data_only=True)))


if __name__=='__main__':main()
