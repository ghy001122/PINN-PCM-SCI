"""Copy the new task's completed numeric artifacts into the local handoff."""
from pathlib import Path
import json,shutil,argparse
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
REL=Path('outputs/runs/20260926-core-revision-vo2-bridge')
def update(dest,include_fcov=False):
    dest=dest.resolve();inventory=json.loads((dest/'input-inventory.json').read_text())
    files=[Path('pinn_pcm_sci/vo2_author_reproduction.py')]
    files += [HERE.relative_to(ROOT)/'literature'/name for name in
              ('LICENSE','model.py','main.py','utils.py','README.md','source-manifest.json','data-assets.json')]
    files += [p.relative_to(ROOT) for p in (ROOT/REL/'vo2').iterdir() if p.suffix in ('.npz','.json')]
    if include_fcov:
        files += [Path('cloud/phk_v23_coverage')/name for name in ('controller.py','run_cloud.py','resume_readout.py')]
        for seed in (29,43):
            folder=ROOT/REL/f'fcov/seed-{seed}'
            for p in folder.rglob('*'):
                if p.is_file() and p.suffix in ('.pt','.json','.jsonl','.npz'):files.append(p.relative_to(ROOT))
        files += [REL/p for p in ('runtime.tar.gz','runtime-manifest.json','environment.json','compute-closure.json','engineering-recovery.json','monitoring-recovery.json','monitor-transport.jsonl','readout-recovery.json','readout-recovery-launch.json','readout-cache-release.json','remote-engineering-tests.log','cloud-finished.json','endpoints-locked.json','fcov-scoring/results.json') if (ROOT/REL/p).exists()]
    for rel in files:
        source=ROOT/rel;target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():
            if rel.as_posix() not in inventory:raise FileExistsError(target)
            continue
        shutil.copy2(source,target);inventory[rel.as_posix()]=dict(source=rel.as_posix(),bytes=source.stat().st_size)
    for p in (HERE/'portable').glob('*.py'):
        q=dest/('pinn_pcm_sci' if p.name=='standalone_io.py' else '')/p.name;shutil.copy2(p,q)
    (dest/'input-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
    print('UPDATED_COMPLETED_HANDOFF_INPUTS',len(files),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--fcov',action='store_true');a=p.parse_args();update(a.root,a.fcov)
