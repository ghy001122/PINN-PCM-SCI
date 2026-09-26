"""Bounded GPU sequence; failures preserve accepted-state files for recovery."""
from pathlib import Path
import json,traceback,time,subprocess,sys
import torch
from pinn_pcm_sci.phk_v23_lf11_coverage import RUN,profile,train,atomic_json,now
from pinn_pcm_sci.phk_v23_lf11_coverage_predict import predict

started=time.perf_counter();out=RUN.parent
try:
    import platform,numpy,scipy
    atomic_json(out/'environment.json',dict(python=platform.python_version(),torch=torch.__version__,numpy=numpy.__version__,
        scipy=scipy.__version__,device=torch.cuda.get_device_name(),cpu_threads=4,created_utc=now()))
    # Both zero-update complete gradients precede any scientific update.
    for seed in (29,43):
        folder=RUN/f'seed-{seed}'
        if not (folder/'zero-update-profile.json').exists():profile(folder,'cuda:0')
        torch.cuda.empty_cache()
    for seed in (29,43):
        train(RUN/f'seed-{seed}','cuda:0');torch.cuda.empty_cache()
    atomic_json(out/'endpoints-locked.json',dict(seeds=[29,43],reference_read=False,created_utc=now()))
    for seed in (29,43):predict(RUN/f'seed-{seed}','cuda:0')
    result=dict(status='COMPLETE',reference_read=False)
except BaseException as e:
    result=dict(status='STOPPED',error=str(e),traceback=traceback.format_exc(),reference_read=False)
finally:
    result.update(seconds=time.perf_counter()-started,created_utc=now())
    atomic_json(out/'cloud-finished.json',result)
    print(json.dumps(result),flush=True)
