"""Prepare a NEW LF11 sparse run and its CPU parent; never overwrite a run."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import torch
from .phk_v23_lf11 import (ROOT, DEFAULT_CONFIG, extract_sparse, SparseData, run_role,
                          calibration, digest, save_json, now)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True,help='new output directory')
    p.add_argument('--config',type=Path,default=DEFAULT_CONFIG)
    a=p.parse_args()
    if a.root.exists(): raise FileExistsError('a new run directory is required')
    config=json.loads(a.config.read_text(encoding='utf-8'))
    if config['warmup_updates']!=1200 or config['branch_updates']!=1200:
        raise ValueError('this entry reproduces the fixed LF11 design')
    torch.set_num_threads(2)
    extract_sparse(ROOT/config['medium'],a.root/'input',config)
    save_json(a.root/'formal/frozen_config.json',config)
    names=['pinn_pcm_sci/phk_v23_lf11.py','pinn_pcm_sci/phk_v23_lf11_readout.py',
           'pinn_pcm_sci/phk_v22r_pinn.py','pinn_pcm_sci/phk_v22r_training.py']
    save_json(a.root/'source_identity.json',{'recorded_utc':now(),'base_commit':config['source_commit'],
              'files':{name:digest(ROOT/name) for name in names}})
    bundle=a.root/'input/sparse.npz'
    data=SparseData(bundle)
    result,model=run_role('warm_start',data,config,'cpu',a.root/'formal',digest(bundle))
    if model is None: raise RuntimeError('common parent invalid; no branches authorized by this entry')
    save_json(a.root/'formal/calibration.json',calibration(model,data,config,'cpu'))
    print(json.dumps({'status':'SPARSE_CPU_PARENT_COMPLETE','updates':result['updates'],
                      'next_entry':'pinn_pcm_sci.phk_v23_lf11_campaign'}))


if __name__=='__main__': main()
