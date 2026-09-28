import json,os,pathlib,runpy,sys
root=pathlib.Path(__file__).resolve().parent
forbidden=pathlib.Path('E:\\Python demo\\PINN-PCM-SCI').resolve()
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
