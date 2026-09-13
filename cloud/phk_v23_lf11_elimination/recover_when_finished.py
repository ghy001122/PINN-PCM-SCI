"""Watch this exact authorized job, recover its artifacts, then shut it down.

This local lifecycle helper never reads reference fields or changes training.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT/'outputs/runs/20260913-lf11-electrical-elimination'
DEST = 'root@region-46.seetacloud.com'
REMOTE = '/root/autodl-tmp/lf11-elimination-20260913'
KEY = str(Path.home()/'.ssh/codex_autodl_pinn_v22r')
SSH = ['ssh', '-i', KEY, '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes',
       '-o', 'ConnectTimeout=10', '-p', '28355', DEST]
SCP = ['scp', '-i', KEY, '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes',
       '-o', 'ConnectTimeout=10', '-P', '28355']


def now():
    return datetime.now(timezone.utc).isoformat()


def remote(command, timeout=30, check=True):
    p = subprocess.run(SSH+[command], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=timeout)
    if check and p.returncode:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip())
    return p


def main():
    record = {'mode': 'cloud', 'started_utc': now(), 'destination': DEST,
              'remote_directory': REMOTE, 'reference_read': False,
              'recovery_verified': False, 'shutdown_requested': False,
              'instance_shutdown_confirmed': False, 'training_complete': False,
              'compute_stopped_before_reference_read': False}
    def save():
        (RUN/'compute-closure.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    seen = ''
    while True:
        p = remote(f'cd {REMOTE} && if test -f cloud-exit-status.txt; then cat cloud-exit-status.txt; else echo RUNNING; fi; tail -n 1 cloud-run.log')
        lines = p.stdout.strip().splitlines()
        status = lines[0]
        if p.stdout != seen:
            print(json.dumps({'job_status': status, 'progress': lines[1:]}, ensure_ascii=False), flush=True)
            seen = p.stdout
        if status != 'RUNNING':
            record['job_exit_code'] = int(status)
            break
        time.sleep(30)
    relative = 'outputs/runs/20260913-lf11-electrical-elimination'
    manifest = remote(f'cd {REMOTE} && tar -czf recovery.tar.gz {relative} selected-files.json cloud-run.log cloud-exit-status.txt && sha256sum recovery.tar.gz', timeout=600)
    expected = manifest.stdout.split()[0]
    archive = ROOT/'.t/lf11-elimination-deployment/recovery.tar.gz'
    print(json.dumps({'event': 'RECOVERING_FIXED_ARTIFACTS'}), flush=True)
    subprocess.run(SCP+[DEST+':'+REMOTE+'/recovery.tar.gz', str(archive)], check=True, timeout=1800)
    actual = hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest()
    if actual != expected:
        raise RuntimeError('recovery archive mismatch; shutdown not yet requested')
    record.update(recovery_verified=True, recovery_archive=str(archive.relative_to(ROOT)),
                  recovery_sha256=actual, recovered_utc=now())
    save()
    # Current authenticated command, not a historical shutdown receipt.
    stopped = remote('/usr/bin/shutdown -h now', timeout=45, check=False)
    record.update(shutdown_requested=True, shutdown_requested_utc=now(),
                  shutdown_returncode=stopped.returncode,
                  shutdown_stdout=stopped.stdout.strip(), shutdown_stderr=stopped.stderr.strip())
    save()
    probes = []
    for _ in range(12):
        time.sleep(5)
        try:
            p = remote('true', timeout=15, check=False)
            probes.append({'returncode': p.returncode, 'stderr': p.stderr.strip()})
            if p.returncode != 0 and 'Connection refused' in p.stderr:
                record['instance_shutdown_confirmed'] = True
                record['shutdown_confirmation'] = 'CURRENT_AUTHENTICATED_SHUTDOWN_THEN_CONNECTION_REFUSED'
                break
        except subprocess.TimeoutExpired:
            probes.append({'timeout': True})
    record.update(shutdown_probes=probes, completed_utc=now(),
                  training_complete=record['job_exit_code'] == 0,
                  compute_stopped_before_reference_read=record['instance_shutdown_confirmed'])
    save()
    print(json.dumps({'event': 'RECOVERY_AND_SHUTDOWN_RESULT', **record}, ensure_ascii=False), flush=True)
    if not record['instance_shutdown_confirmed']:
        raise RuntimeError('shutdown confirmation still required; do not read reference')


if __name__ == '__main__':
    main()
