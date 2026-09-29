"""Package only locked, already-scored joint endpoints; never run training.

No source arrays are read until --locked-results-ready is explicitly supplied
and all requested seed result/lock files exist.  This builder is workspace-only;
the produced score.py resolves every runtime input from the supplied pack root.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUN = ROOT/'outputs/runs/20260929-joint-reconstruction'
PACK = HERE/'scoring-subset'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')


def subset(source, destination, fields):
    with np.load(source, allow_pickle=False) as archive:
        missing = set(fields)-set(archive.files)
        if missing:
            raise KeyError(f'{source.name}: missing fields {sorted(missing)}')
        data = {key: archive[key] for key in fields}
    destination.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(destination, **data)


def build(seeds):
    config = read(RUN/'config.json')
    records = []
    for seed in seeds:
        lock = read(RUN/f'seed-{seed}-locked.json')
        results = read(RUN/f'seed-{seed}-results.json')
        if results['all_valid'] != lock['all_valid']:
            raise ValueError('Lock and scored endpoint qualification disagree')
        records.append((seed, lock, results))
    # Every current-seed terminal result is confirmed before any source field
    # is opened. This package never selects endpoints or changes their status.
    source_path = ROOT/config['original_source_for_scoring_only']
    subset(source_path, PACK/'arrays/source.npz',
           ['time', 'voltage', 'device_current', 'temperature', 'resistance', 'delta'])
    subset(RUN/'input.npz', PACK/'arrays/observations.npz',
           ['observation_time', 'observation_voltage', 'observation_weights'])
    settings = {key: config[key] for key in ['task_id', 'dt_s', 'Vin_V', 'eta', 'parameters_SI',
                                              'initial_voltage_V', 'increment']}
    packaged = dict(task_id=config['task_id'], source='arrays/source.npz', observations='arrays/observations.npz',
                    settings=settings, seeds=[])
    provenance = dict(source=str(source_path.relative_to(ROOT)),
                      observations='outputs/runs/20260929-joint-reconstruction/input.npz',
                      expected_results='outputs/runs/20260929-joint-reconstruction/seed-*-results.json',
                      checkpoint_location='outputs/runs/20260929-joint-reconstruction/seed-<seed>/<role>/checkpoint.pt',
                      checkpoint_included=False, provenance_paths_are_not_runtime_fallbacks=True,
                      source_kind='Project numerical arrays from the fixed published-author model; not experimental observations',
                      upstream_model_commit='217d4f0ed6bfc680240021b07142a121cb4963d1',
                      upstream_model_url='https://github.com/yuanhangzhang98/collective_dynamics_neuristor',
                      scoring_source='scripts/score_vo2_joint_sprint.py',
                      peak_source='scripts/circuit_screen_metrics.py',
                      history_event_source='scripts/conditional_history_tools.py:reversal_events',
                      external_access='NOT_PUBLISHED; local independent-score delivery only; full-paper P03 remains open',
                      candidates=[])
    for seed, lock, expected in records:
        expected_name=f'expected/seed-{seed}.json'
        save(PACK/expected_name, expected)
        item=dict(seed=seed, all_valid=expected['all_valid'], methods=[], expected=expected_name)
        roles=['N_dyn', 'F_dyn', 'S_dyn'] if seed == 29 else ['N_dyn', 'F_dyn']
        for role in roles:
            run=RUN/f'seed-{seed}'/role
            terminal=read(run/'termination.json')
            save(PACK/f'provenance/seed-{seed}-{role}-termination.json', terminal)
            if terminal['status'] != 'VALID_COMPLETE':
                provenance['candidates'].append(dict(seed=seed, method=role, status=terminal['status'], included=False))
                continue
            path=f'arrays/seed-{seed}-{role}.npz'
            with np.load(run/'endpoint.npz', allow_pickle=False) as a:
                values={key:a[key] for key in ['T', 'R', 'common_voltage', 'delta']}
                equal=np.array_equal(a['v'],a['common_voltage'])
                if not equal:
                    values['native_voltage']=a['v']
            np.savez_compressed(PACK/path, **values)
            item['methods'].append(dict(method=role, path=path, native_equals_common=equal))
            provenance['candidates'].append(dict(seed=seed, method=role, status=terminal['status'], included=True,
                                                source=str((run/'endpoint.npz').relative_to(ROOT)),
                                                native_voltage_reuses_common_only_if_bitwise_equal=equal))
        packaged['seeds'].append(item)
    save(PACK/'config.json', packaged)
    save(PACK/'provenance.json', provenance)
    # Preserve the actual upstream license, without calling all project files
    # or third-party experimental/publisher assets MIT licensed.
    license_source=ROOT/'paper/paper_revision_20260926_core/literature/LICENSE'
    shutil.copy2(license_source, PACK/'UPSTREAM_AUTHOR_MODEL_LICENSE.txt')
    files=[]
    for path in sorted(PACK.rglob('*')):
        if path.is_file() and 'recomputed' not in path.parts and path.name != 'manifest.json':
            files.append(dict(path=path.relative_to(PACK).as_posix(), bytes=path.stat().st_size,
                              sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    save(PACK/'manifest.json', dict(task_id=config['task_id'], files=files,
                                  array_precision='Preserved native FP64; no time-node removal',
                                  copied_neural_checkpoints=False, total_input_bytes=sum(x['bytes'] for x in files),
                                  scientific_replay='No training, thermal integration or hysteresis replay',
                                  publication='Not authorized in this task'))
    print(json.dumps(dict(package=str(PACK), files=len(files), bytes=sum(x['bytes'] for x in files)),ensure_ascii=False))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--locked-results-ready', action='store_true')
    parser.add_argument('--seeds', type=int, nargs='+', default=[29])
    args=parser.parse_args()
    if not args.locked_results_ready:
        parser.error('Only run after root confirms endpoints recovered, locked and scored')
    if args.seeds not in ([29], [29,43]):
        parser.error('Only the authorized ordered seed subsets [29] or [29,43] are supported')
    build(args.seeds)
