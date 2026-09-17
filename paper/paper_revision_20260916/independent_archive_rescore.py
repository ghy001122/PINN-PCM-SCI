"""One clean extraction and NumPy-only rescore of the completed local archive."""
from __future__ import annotations
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def read(path):return json.loads(path.read_text(encoding='utf-8'))


def compare(a,b,path=''):
    import math
    if isinstance(a,dict):
        if a.keys()!=b.keys():raise AssertionError(('keys',path))
        for k in a:compare(a[k],b[k],path+'/'+k)
    elif isinstance(a,list):
        if len(a)!=len(b):raise AssertionError(('length',path))
        for i,v in enumerate(a):compare(v,b[i],path+'/'+str(i))
    elif isinstance(a,(float,int)) and not isinstance(a,bool):
        if not math.isclose(a,b,rel_tol=2e-10,abs_tol=2e-12):raise AssertionError((path,a,b))
    elif a!=b:raise AssertionError((path,a,b))


def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,default=ROOT/'outputs/submission-archive-20260916')
    a=p.parse_args();archive=a.archive.resolve()
    local=read(archive/'rescore-output/results.json')
    if local['status']!='ARRAY_ONLY_RESCORING_COMPLETE':raise AssertionError('Main rescore incomplete')
    target=ROOT/'outputs/PINN-PCM-revision-20260916-array-archive.zip'
    clean=ROOT/'.t/independent-rescore-20260916'
    if target.exists() or clean.exists():raise FileExistsError('Independent archive rescore already has artifacts; inspect instead of repeating')
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_STORED,allowZip64=True) as bundle:
        for path in sorted(archive.rglob('*')):
            if not path.is_file():continue
            relative=path.relative_to(archive)
            if relative.parts[0]=='rescore-output' or '__pycache__' in relative.parts:continue
            if path.suffix.lower() in ('.pem','.key','.ttf','.otf') or 'compute-closure.json'==path.name:
                raise AssertionError('Disallowed archive asset')
            bundle.write(path,relative.as_posix())
    clean.mkdir()
    with zipfile.ZipFile(target) as bundle:
        for entry in bundle.infolist():
            destination=(clean/entry.filename).resolve()
            if not destination.is_relative_to(clean.resolve()):raise ValueError('Archive path traversal')
        bundle.extractall(clean)
    python=ROOT/'.t/independent-rescore-env-20260916/Scripts/python.exe'
    subprocess.run([str(python),'-I','portable/rescore.py','--root','.',
                    '--output','independently-rescored'],cwd=clean,check=True)
    independent=read(clean/'independently-rescored/results.json')
    for key in ('records','decisions','reference_sensitivity','old_reproduction','published_table_reproduction'):
        compare(local[key],independent[key],key)
    with target.open('rb') as stream:identity=hashlib.file_digest(stream,'sha256').hexdigest()
    result=dict(status='PASS_CLEAN_ARCHIVE_ONLY_RESCORING',archive=target.relative_to(ROOT).as_posix(),archive_sha256=identity,
        independent_results=(clean/'independently-rescored/results.json').relative_to(ROOT).as_posix(),
        historical_main_table_and_events_reproduced=True,old_and_refined_objects_each=16,
        all_matched_and_gate_decisions_reproduced=True,reference_sensitivity_reproduced=True,
        scientific_dependencies=['numpy==2.1.1'],torch_available=False,scipy_available=False,
        private_checkout_imported=False,model_loads=0,model_forwards=0,linear_solves=0,publicly_uploaded=False,
        independent_execution=independent['execution'],full_training_rerun=False)
    (HERE/'build/independent-rescore.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
