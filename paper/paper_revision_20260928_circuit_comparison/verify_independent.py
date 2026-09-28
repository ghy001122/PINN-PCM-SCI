"""One isolated re-score of the small transferable subset, not the old full pack."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,time
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE=HERE/'scoring-subset'
DEST=Path('C:/Users/CJ/.codex/visualizations/2026/09/20/01a0bdc5-2887-7920-bbae-fab752dd28b8/cubic-energy-independent-20260928')
if DEST.exists():raise RuntimeError('Independent run already prepared; inspect rather than repeat')
DEST.mkdir()
started=datetime.now(timezone.utc).isoformat();tic=time.perf_counter()
manifest=json.loads((SOURCE/'transfer-manifest.json').read_text(encoding='utf-8'))
for f in manifest['files']:
    target=DEST/f['path'];target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(SOURCE/f['path'],target)
    with target.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
    if actual!=f['sha256']:raise RuntimeError('Transfer integrity mismatch')
guard=r'''import json,os,pathlib,runpy,sys
root=pathlib.Path(__file__).resolve().parent
forbidden=pathlib.Path(FORBIDDEN_REPO).resolve()
runtime=forbidden/'.venv'
denied=[]
def audit(event,args):
    if event=='open' and args and isinstance(args[0],(str,bytes,os.PathLike)):
        path=pathlib.Path(os.fsdecode(args[0])).resolve()
        if path.is_relative_to(forbidden) and not path.is_relative_to(runtime):
            denied.append(str(path));raise PermissionError('Research checkout unavailable in isolated scoring')
sys.addaudithook(audit)
probe=False
try:open(forbidden/'README.md','rb')
except PermissionError:probe=True
assert probe
sys.path.insert(0,str(root/'scripts'))
sys.argv=[str(root/'scripts/run_cubic_energy_comparison.py'),'--root',str(root),'--config','config.json','--mode','score']
runpy.run_path(sys.argv[0],run_name='__main__')
# A required input is temporarily absent. No legacy-location lookup is possible.
import run_cubic_energy_comparison as api
cfg=json.loads((root/'config.json').read_text())
item=cfg['records'][0];path=root/item['source'];parked=path.with_suffix('.npz.hidden')
path.rename(parked)
missing_failed=False
try:
    try:api.loaded_record(root,item)
    except FileNotFoundError:missing_failed=True
finally:parked.rename(path)
assert missing_failed
(root/'isolation-check.json').write_text(json.dumps(dict(repository_access_probe_denied=probe,
    missing_input_failed_without_fallback=missing_failed,denied_paths=denied,
    dependency_exception='Only the pre-existing project .venv runtime; research files unavailable',
    isolated_python_flag=True)),encoding='utf-8')
'''.replace('FORBIDDEN_REPO',repr(str(ROOT)))
(DEST/'run_isolated.py').write_text(guard,encoding='utf-8')
command=[sys.executable,'-I',str(DEST/'run_isolated.py')]
proc=subprocess.run(command,cwd=DEST,text=True,capture_output=True)
(HERE/'build').mkdir(exist_ok=True)
(HERE/'build/independent-reproduction.log').write_text(proc.stdout+'\n'+proc.stderr,encoding='utf-8')
record=dict(task_id='PCM-20260928-CUBIC-ENERGY-DISCRIMINATION-01',started_utc=started,
    completed_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.perf_counter()-tic,
    original_subset=str(SOURCE),independent_directory=str(DEST),returncode=proc.returncode,
    copied_files=len(manifest['files']),copied_bytes=sum(x['bytes'] for x in manifest['files']),
    transfer_integrity='PASS',command=command,full_historical_pack_rerun=False,
    new_prediction_fits=0,new_system_steps=0,new_training_steps=0)
if proc.returncode==0:
    expected=json.loads((SOURCE/'results/results.json').read_text())
    actual=json.loads((DEST/'results/results.json').read_text())
    record['complete_results_exact_match']=expected==actual
    record['isolation']=json.loads((DEST/'isolation-check.json').read_text())
    record['status']='PASS' if expected==actual else 'RESULT_MISMATCH'
else:record['status']='EXECUTION_FAILED'
(HERE/'build/independent-reproduction.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,ensure_ascii=False,indent=2))
if record['status']!='PASS':raise SystemExit(1)
