"""Run the single approved B1 training/readout sequence, without references."""
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parent
RUN = 'outputs/runs/20260921-b1-second-cycle-phase-gap'
os.chdir(ROOT)
env = dict(os.environ, OMP_NUM_THREADS='4', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', PYTHONUNBUFFERED='1')
code = 1
try:
    for action in ('train', 'readout'):
        print(json.dumps({'stage': action, 'started_utc': datetime.now(timezone.utc).isoformat()}), flush=True)
        subprocess.run([sys.executable, '-u', '-m', 'pinn_pcm_sci.phk_v23_b1', action,
                        '--device', 'cuda:0', '--approval', RUN+'/resource-approval.json'],
                       check=True, env=env)
    code = 0
except BaseException:
    traceback.print_exc()
finally:
    (ROOT/'cloud-exit-status.txt').write_text(str(code), encoding='utf-8')
    print(json.dumps({'gpu_sequence_exit': code, 'finished_utc': datetime.now(timezone.utc).isoformat()}), flush=True)
sys.exit(code)
