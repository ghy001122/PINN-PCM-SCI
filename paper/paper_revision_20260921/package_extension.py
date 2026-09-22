"""Make the six negative continuations separately portable; reuse input hashes."""
import json
import os
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'outputs/submission-rescore-20260921'
DEST=SOURCE/'extension'


def main():
    if DEST.exists():raise FileExistsError('Extension already packaged')
    m=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'))
    items=[o for o in m['objects'] if o['id'] in m['scopes']['extension']]
    assert len(items)==6
    desc=m['protocols']['shorter']
    paths={m['grid_arrays'],desc['config'],desc['native_spatial_reference'],
           'primary-rescore/results.json',*desc['references'].values()}
    for item in items:paths.update(item[k] for k in ('prediction','readout'))
    paths.update('portable/'+name for name in ('scope_rescore.py','readout_rescore.py','rescore.py','readout_metrics.py','frozen_metrics.py'))
    for name in sorted(paths):
        dst=DEST/name;dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.suffix=='.npz':os.link(SOURCE/name,dst)
        else:shutil.copy2(SOURCE/name,dst)
    m.update(package_id='PCM-20260921-NEGATIVE-CONTINUATIONS-EXTENSION',objects=items,
             protocols={'shorter':desc},scopes={'extension':[o['id'] for o in items]},
             expected_record_counts={'extension':18})
    (DEST/'manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
    integrity=json.loads((SOURCE/'integrity.json').read_text(encoding='utf-8'))
    integrity.update(scope='same immutable inputs as parent package; existing hashes reused, no recomputation',
                     files=[v for v in integrity['files'] if v['path'] in paths])
    (DEST/'integrity.json').write_text(json.dumps(integrity,indent=2),encoding='utf-8')
    print(json.dumps(dict(extension=str(DEST),objects=len(items),saved_records=18,new_retraining=False)))


if __name__=='__main__':main()
