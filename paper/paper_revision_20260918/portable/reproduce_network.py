"""Explicit reproduction entry; not invoked by array rescore or paper build.

Requires the archived original Python/Torch/SciPy environment and a new empty
workspace. This repeats the phase-head continuation, not the whole historical
research campaign. Use --action prepare to stage without running a model.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--action',choices=['prepare','train','infer'],default='prepare')
    p.add_argument('--device',default='cuda:0')
    p.add_argument('--seed',type=int,choices=[29,43],default=29)
    p.add_argument('--role',choices=['E_C','E_R','E_I'],default='E_C')
    a=p.parse_args();archive=a.archive.resolve();work=a.workspace.resolve()
    if work.exists():raise FileExistsError('Use a new empty workspace; no implicit restart or overwrite')
    shutil.copytree(archive/'training/runtime-source',work)
    run=work/'outputs/runs/20260916-lf11-phase-adapter-reference';run.mkdir(parents=True)
    sparse=work/'outputs/runs/20260915-lf11-protocol-history/input/sparse.npz'
    sparse.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(archive/'data/shorter/sparse.npz',sparse)
    shutil.copy2(work/'configs/phk_v23/lf11_phase_adapter_sprint.json',run/'frozen-config.json')
    for seed in (29,43):
        src=archive/f'models/phase-adapter/{seed}';dest=run/f'seed-{seed}';dest.mkdir()
        for fn in ('parent.pt','frozen-config.json','calibration.json','calibration-pool.json','lbfgs-pool.json','audit-pool.json','gate-calibration.json'):
            shutil.copy2(src/fn,dest/fn)
    print(json.dumps({'status':'PREPARED','reference_arrays_staged':False,'action':a.action}))
    if a.action=='prepare':return
    if a.action=='train':
        subprocess.run([sys.executable,'-m','pinn_pcm_sci.phk_v23_phase_adapter','--root',str(run),'--device',a.device],cwd=work,check=True)
    else:
        destination=run/f'seed-{a.seed}/{a.role}';destination.mkdir()
        shutil.copy2(archive/f'models/phase-adapter/{a.seed}/{a.role}/checkpoint.pt',destination/'checkpoint.pt')
        script=work/'infer_selected.py'
        script.write_text('''import json,sys
from pathlib import Path
from pinn_pcm_sci.phk_v23_phase_adapter import predict
folder=Path(sys.argv[1]);role=sys.argv[2];device=sys.argv[3]
config=json.loads((folder/'frozen-config.json').read_text())
predict(folder,role,config,device)
''',encoding='utf-8')
        subprocess.run([sys.executable,str(script),str(run/f'seed-{a.seed}'),a.role,a.device],cwd=work,check=True)


if __name__=='__main__':main()
