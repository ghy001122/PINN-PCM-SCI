"""Execute the one authorized screen, without references or automatic retries."""
from pathlib import Path
from datetime import datetime,timezone
import json
import os
import subprocess
import sys
import traceback

root=Path(__file__).resolve().parent
os.chdir(root)
run='outputs/runs/20260923-relative-phase-moments'
code=1
try:
    for module,action in [('phk_v23_phase_moments_run','train'),
                          ('phk_v23_phase_moments_readout','audit'),
                          ('phk_v23_phase_moments_readout','readout')]:
        print(json.dumps(dict(stage=action,started_utc=datetime.now(timezone.utc).isoformat())),flush=True)
        subprocess.run([sys.executable,'-u','-m','pinn_pcm_sci.'+module,action,
                        '--device','cuda:0','--resource',run+'/resource-approval.json'],check=True)
    code=0
except BaseException:
    traceback.print_exc()
finally:
    (root/'cloud-exit-status.txt').write_text(str(code)+'\n',encoding='utf-8')
    print(json.dumps(dict(gpu_sequence_exit=code,finished_utc=datetime.now(timezone.utc).isoformat())),flush=True)
sys.exit(code)
