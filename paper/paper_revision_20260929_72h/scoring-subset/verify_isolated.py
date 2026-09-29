"""Execute the scorer once with the research checkout explicitly unavailable.

Run this only from the independent copied package; --forbid-root is a denied
location, never an input fallback.  The existing .venv may supply NumPy.
"""
from pathlib import Path
import argparse
import json
import os
import runpy
import sys

parser=argparse.ArgumentParser()
parser.add_argument('--forbid-root', required=True, type=Path)
args=parser.parse_args()
root=Path(__file__).resolve().parent
forbidden=args.forbid_root.resolve()
if root.is_relative_to(forbidden):
    raise RuntimeError('The verification copy must be outside the research checkout')
runtime=forbidden/'.venv'
denied=[]
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name]='4'


def audit(event, arguments):
    if event == 'open' and arguments and isinstance(arguments[0], (str, bytes, os.PathLike)):
        path=Path(os.fsdecode(arguments[0])).resolve()
        if path.is_relative_to(forbidden) and not path.is_relative_to(runtime):
            denied.append(str(path))
            raise PermissionError('Research checkout unavailable during independent scoring')


sys.addaudithook(audit)
probe=False
try:
    open(forbidden/'README.md', 'rb')
except PermissionError:
    probe=True
if not probe:
    raise RuntimeError('Repository-read denial was not enforced')
sys.argv=[str(root/'score.py'), '--root', str(root)]
namespace=runpy.run_path(str(root/'score.py'), run_name='__main__')
configuration=json.loads((root/'config.json').read_text(encoding='utf-8'))
source=root/configuration['source']
parked=source.with_suffix('.npz.absent-for-check')
source.rename(parked)
missing_failed=False
try:
    try:
        namespace['arrays'](root, configuration['source'], ['time'])
    except FileNotFoundError:
        missing_failed=True
finally:
    parked.rename(source)
if not missing_failed:
    raise RuntimeError('Missing input did not fail immediately')
(root/'isolation-check.json').write_text(json.dumps(dict(
    repository_access_probe_denied=probe,
    missing_input_failed_without_fallback=missing_failed,
    denied_paths=denied,
    dependency_exception='Existing project .venv Python/NumPy only; scientific repository files denied',
    isolated_python_flag=True), indent=2)+'\n', encoding='utf-8')
