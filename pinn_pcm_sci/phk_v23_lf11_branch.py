"""Execute one independent LF11 branch without repeating its common parent."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import torch
from .phk_v23_lf11 import SparseData, digest, run_role, predict, save_json
from .phk_v23_lf11_campaign import fixed_audit


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--role',choices=('D_B','P_U','P_I','P_M','P_S'),required=True)
    p.add_argument('--group',choices=('formal','conditional'),default='formal')
    p.add_argument('--device',default='cuda')
    a=p.parse_args()
    torch.set_num_threads(2)
    formal=a.root/'formal'
    config=json.loads((formal/'frozen_config.json').read_text())
    cal=json.loads((formal/'calibration.json').read_text())
    if a.role=='P_S':
        if a.group!='conditional': raise ValueError('P-S belongs to the conditional budget')
        cal.update(json.loads((formal/'conditional_calibration.json').read_text()))
        if cal['kappa0'] is None: raise ValueError('global phase calibration not identifiable')
    bundle=a.root/'input/sparse.npz'
    data=SparseData(bundle)
    result,model=run_role(a.role,data,config,a.device,a.root/a.group,digest(bundle),formal/'warm_start/checkpoint.pt',cal)
    if model is not None:
        save_json(a.root/a.group/a.role/'fixed_audit.json',fixed_audit(model,data,config,a.device))
        predict(model,config,a.root/a.group/a.role/'prediction.npz',a.device)
    print(json.dumps({'branch_complete':a.role,'status':result['status'],'updates':result['updates']}),flush=True)


if __name__=='__main__': main()
