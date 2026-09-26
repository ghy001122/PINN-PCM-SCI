"""Resume only committed fixed-endpoint inference after an unrecorded exit."""
from pathlib import Path
import hashlib,json,time,traceback
from pinn_pcm_sci.phk_v23_lf11_coverage import RUN,read,atomic_json,now,check_resources
from pinn_pcm_sci.phk_v23_lf11_coverage_predict import predict

out=RUN.parent
assert read(out/'endpoints-locked.json')['seeds']==[29,43]
def identities():
    return {str(seed):hashlib.sha256((RUN/f'seed-{seed}/F_cov/checkpoint.pt').read_bytes()).hexdigest() for seed in (29,43)}
before=identities();started=time.perf_counter()
record=read(out/'readout-recovery.json')
record.update(resume_started_utc=now(),checkpoint_sha256=before,resources_before=check_resources('cuda:0'))
atomic_json(out/'readout-recovery.json',record)
try:
    for seed in (29,43):
        assert read(RUN/f'seed-{seed}/F_cov/terminal.json')['status']=='VALID_FIXED_ENDPOINT'
        predict(RUN/f'seed-{seed}','cuda:0')
    assert identities()==before
    result=dict(status='COMPLETE',reference_read=False,training_resumed=False,checkpoint_weights_unchanged=True)
except BaseException as exc:
    result=dict(status='STOPPED',error=str(exc),traceback=traceback.format_exc(),reference_read=False,training_resumed=False)
finally:
    record.update(resume_result=result,readout_resume_seconds=time.perf_counter()-started,resume_finished_utc=now())
    atomic_json(out/'readout-recovery.json',record)
    result.update(seconds=record['readout_resume_seconds'],duration_scope='readout_resumption_only',created_utc=now())
    atomic_json(out/'cloud-finished.json',result)
    print(json.dumps(result),flush=True)
