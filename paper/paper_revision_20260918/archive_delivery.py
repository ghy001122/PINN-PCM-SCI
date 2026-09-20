"""Stage the single isolated rescore and package the resulting local archive."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
ARCH=ROOT/'outputs/submission-archive-20260918'
ISOLATED=ROOT/'outputs/isolated-array-reproduction-20260918'
PARTS=ROOT/'outputs/submission-archive-20260918-parts'

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
def stage():
    assert read(ARCH/'primary-rescore/results.json')['status']=='COMPLETE_ARRAY_ONLY_REPRODUCTION'
    if ISOLATED.exists():raise FileExistsError(ISOLATED)
    ISOLATED.mkdir()
    for p in ARCH.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(ARCH)
        if rel.parts[0] in ('primary-rescore','isolated-rescore'):continue
        target=ISOLATED/rel;target.parent.mkdir(parents=True,exist_ok=True)
        if p.suffix in ('.npz','.npy','.pt','.gz'):
            os.link(p,target)
        else:shutil.copy2(p,target)
    shutil.copy2(ARCH/'primary-rescore/results.json',ISOLATED/'expected/new-primary-results.json')
    print(json.dumps({'prepared_isolated_directory':str(ISOLATED),'large_inputs':'read-only use of hardlinks','scientific_compute':0}))

def adopt():
    result=read(ISOLATED/'isolated-rescore/results.json')
    assert result['independent_directory_comparison']['passed']
    target=ARCH/'isolated-rescore'
    if target.exists():raise FileExistsError(target)
    for p in (ISOLATED/'isolated-rescore').rglob('*'):
        if p.is_file():
            q=target/p.relative_to(ISOLATED/'isolated-rescore');q.parent.mkdir(parents=True,exist_ok=True);os.link(p,q)
    print(json.dumps(result['independent_directory_comparison']))

def pack():
    assert read(ARCH/'isolated-rescore/results.json')['independent_directory_comparison']['passed']
    # The manuscript is self-contained and can be built independently of arrays.
    for part in ('source','tables','figures','evidence'):
        shutil.copytree(HERE/part,ARCH/'manuscript'/part,dirs_exist_ok=True)
    for name in ('references.md','references.bib','prepare_document.py','build_pdf.py','report_results.py','README.md','data-and-reproduction.md',
                 'revision-response.md','cover-letter-draft.md','claim_evidence_matrix.md',
                 'adjudication.json','manuscript.pdf','supplement.pdf'):
        shutil.copy2(HERE/name,ARCH/'manuscript'/name)
    shutil.copy2(HERE/'build/visual-review/visual-acceptance.json',ARCH/'manuscript/pdf-review.json')
    shutil.copy2(HERE/'build/content-verification.json',ARCH/'manuscript/content-verification.json')
    readme=ARCH/'README.md'
    text=readme.read_text(encoding='utf-8').replace('--out isolated-rescore','--out my-rescore')
    text+='\nSee `manuscript/data-and-reproduction.md` for the separate document, fixed-array and opt-in training reproduction levels, environment requirements and author/public-release boundaries. The included `isolated-rescore` is completed evidence; choose a new output directory for a fresh reproduction. Upstream license notices are in `provenance`; the authors still need to select and confirm repository/data redistribution terms before public release.\n'
    readme.write_text(text,encoding='utf-8')
    if PARTS.exists():raise FileExistsError(PARTS)
    PARTS.mkdir()
    # Each part is independently readable; extract all parts into one directory.
    # Stored NPZ/PT files avoid an unnecessary compression pass and a giant
    # intermediate archive. No existing evidence file is removed.
    limit=1_500_000_000
    files=sorted(p for p in ARCH.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    batches=[];batch=[];size=0
    for p in files:
        n=p.stat().st_size
        if batch and size+n>limit:batches.append(batch);batch=[];size=0
        batch.append(p);size+=n
    if batch:batches.append(batch)
    rows=[]
    for i,batch in enumerate(batches,1):
        path=PARTS/f'pinn-pcm-revision-part-{i:02d}.zip'
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
            for p in batch:z.write(p,p.relative_to(ARCH).as_posix())
        with path.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
        with zipfile.ZipFile(path) as z:
            assert len(z.infolist())==len(batch)
            assert sum(n.file_size for n in z.infolist())==sum(p.stat().st_size for p in batch)
        row={'name':path.name,'bytes':path.stat().st_size,'sha256':digest,'members':len(batch)}
        rows.append(row);print(json.dumps(row),flush=True)
    save(PARTS/'parts.json',{'status':'LOCAL_ONLY_NOT_UPLOADED','parts':rows,
        'instructions':'Extract every independent zip part into the same new directory, then follow README.md.',
        'integrity':'Per-part SHA256 for transfer; scientific arithmetic validated by the isolated rescore.'})
    (PARTS/'README.md').write_text('# Local split archive\n\nExtract all ZIP files into the same new directory. No part depends on ZIP concatenation. Verify the SHA256 values in parts.json after transfer. The full array package has not been publicly uploaded. Follow README.md in the extracted root for the array-only scorer.\n',encoding='utf-8')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['stage','adopt','pack']);a=p.parse_args()
    {'stage':stage,'adopt':adopt,'pack':pack}[a.action]()
