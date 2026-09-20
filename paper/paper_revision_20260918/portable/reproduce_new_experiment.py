"""Opt-in reproduction; default action only stages the frozen runtime.

This is separate from the NumPy rescore and manuscript build. Executing the
experiment requires an appropriate GPU environment and substantial compute.
"""
from pathlib import Path
import argparse
import subprocess
import sys
import tarfile

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--action',choices=['prepare','execute'],default='prepare')
    p.add_argument('--device',default='cuda:0');a=p.parse_args()
    work=a.workspace.resolve()
    if work.exists():raise FileExistsError('Use a new empty workspace; no implicit restart.')
    work.mkdir(parents=True)
    with tarfile.open(a.archive/'training/new-execution-runtime.tar.gz','r:gz') as t:
        for member in t.getmembers():
            target=(work/member.name).resolve()
            if not target.is_relative_to(work) or member.issym() or member.islnk():
                raise ValueError('Unexpected archive path or link')
        t.extractall(work,filter='data')
    print('FROZEN_INPUTS_PREPARED_WITHOUT_REFERENCES')
    if a.action=='execute':
        subprocess.run([sys.executable,'-m','pinn_pcm_sci.phk_v23_readout_clean_pde','cloud','--device',a.device],
            cwd=work,check=True)

if __name__=='__main__':main()
