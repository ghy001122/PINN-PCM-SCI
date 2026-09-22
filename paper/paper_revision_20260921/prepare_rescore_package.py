"""Stage 2A: portable, local-only frozen-array package. No scientific solves."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / 'outputs/submission-archive-20260918'
DEST = ROOT / 'outputs/submission-rescore-20260921'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def prepare():
    if DEST.exists():
        raise FileExistsError(f'Package already exists; do not overwrite: {DEST}')
    manifest = read(SOURCE/'manifest.json')
    core = [o for o in manifest['objects'] if o['origin'] != 'new_phase_adapter']
    extension = [o for o in manifest['objects'] if o['origin'] == 'new_phase_adapter']
    assert len(core) == 12 and len(extension) == 6
    paths = {manifest['grid_arrays'], 'primary-rescore/results.json'}
    for desc in manifest['protocols'].values():
        paths.update(desc['references'].values())
        paths.update(desc[k] for k in ('config', 'native_spatial_reference', 'sparse', 'expected_decisions'))
    for item in manifest['objects']:
        paths.update(item[k] for k in ('prediction', 'readout', 'fine_prediction', 'fine_readout', 'expected_record') if k in item)
    paths.update(p.relative_to(SOURCE).as_posix() for p in (SOURCE/'expected').glob('*') if p.is_file())
    paths.update('portable/'+name for name in ('readout_rescore.py', 'rescore.py', 'readout_metrics.py', 'frozen_metrics.py'))
    missing = sorted(p for p in paths if not (SOURCE/p).is_file())
    if missing:
        raise FileNotFoundError('Missing required saved inputs; no regeneration: '+', '.join(missing))
    DEST.mkdir(parents=True)
    integrity = []
    for name in sorted(paths):
        src, dst = SOURCE/name, DEST/name
        dst.parent.mkdir(parents=True, exist_ok=True)
        # Hard links are ordinary files on export, never symlink/private-path dependencies.
        if src.suffix == '.npz':
            os.link(src, dst)
        else:
            shutil.copy2(src, dst)
        h = hashlib.sha256()
        with dst.open('rb') as stream:
            for chunk in iter(lambda: stream.read(8*1024*1024), b''):
                h.update(chunk)
        integrity.append(dict(path=name, size=dst.stat().st_size, sha256=h.hexdigest()))
    manifest.update(package_id='PCM-20260921-FROZEN-ARRAY-RESCORE',
        review_baseline_commit='218bb66069da52b2ccfe9dd68ac519edbe4584d0',
        source_archive='outputs/submission-archive-20260918', public_upload=False,
        scopes={'core': [o['id'] for o in core], 'extension': [o['id'] for o in extension]},
        expected_record_counts={'core': 72, 'extension': 18})
    save(DEST/'manifest.json', manifest)
    save(DEST/'integrity.json', {'algorithm': 'sha256', 'scope': 'immutable copied inputs; computed once', 'files': integrity})
    shutil.copy2(HERE/'scope_rescore.py', DEST/'portable/scope_rescore.py')
    save(DEST/'extension-index.json', {'objects': extension, 'records': 18,
         'readers': ['coarse'], 'references': ['old', 'refined', 'spatial'],
         'results': 'primary-rescore/results.json', 'disposition': 'preserved negative continuations; not new independent cases'})
    print(json.dumps({'package': str(DEST), 'core_records': 72, 'extension_records': 18,
                      'required_inputs_present': True, 'input_bytes': sum(p['size'] for p in integrity)}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.parse_args()
    prepare()
