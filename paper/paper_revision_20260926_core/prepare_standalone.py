"""Assemble the authorized local handoff; no publication or new calculation."""
from pathlib import Path
import argparse, ast, hashlib, json, os, shutil

ROOT=Path(__file__).resolve().parents[2]
ARCH=Path('outputs/submission-rescore-20260921')
RUNS=[Path('outputs/runs')/s for s in ('20260921-b1-second-cycle-phase-gap',
    '20260923-relative-phase-moments','20260924-observation-preserving-phase',
    '20260925-fixed-temperature-phase-probe')]
HERE=Path(__file__).resolve().parent

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def assemble(dest):
    dest=dest.resolve()
    if dest==ROOT or dest.is_relative_to(ROOT):raise ValueError('Handoff must be independent of the repository')
    dest.mkdir(parents=True,exist_ok=True)
    index=read(dest/'input-inventory.json') if (dest/'input-inventory.json').exists() else {}
    inode={}
    for rel,entry in index.items():
        p=ROOT/entry['source']
        if p.exists():inode[(p.stat().st_dev,p.stat().st_ino)]=dest/rel
    def copy(source,relative=None):
        p=ROOT/source;q=dest/(relative or source)
        if not p.is_file():raise FileNotFoundError(p)
        rel=q.relative_to(dest).as_posix()
        if q.exists():
            if rel not in index:raise FileExistsError(q)
            return
        q.parent.mkdir(parents=True,exist_ok=True)
        ident=(p.stat().st_dev,p.stat().st_ino)
        if ident in inode:os.link(inode[ident],q)
        else:shutil.copy2(p,q);inode[ident]=q
        index[rel]=dict(source=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size)
        if len(index)%30==0:save(dest/'input-inventory.json',index);print('INPUTS_COPIED',len(index),flush=True)
    m=read(ROOT/ARCH/'manifest.json');copy(ARCH/'manifest.json')
    needed={m['grid_arrays'],'primary-rescore/results.json','b1/first-score/results.json'}
    for item in m['objects']:
        needed.update(item[k] for k in ('prediction','readout','fine_prediction','fine_readout','expected_record') if k in item)
    for desc in m['protocols'].values():
        needed.update(desc['references'].values())
        needed.update(desc[k] for k in ('config','native_spatial_reference','sparse','expected_decisions'))
    needed.update(p.relative_to(ROOT/ARCH).as_posix() for p in (ROOT/ARCH/'portable').glob('*.py'))
    needed.update(p.relative_to(ROOT/ARCH).as_posix() for p in (ROOT/ARCH/'expected').glob('*.json'))
    for rel in sorted(needed):copy(ARCH/rel)
    for run in RUNS:
        src=ROOT/run
        # Numeric inputs and original metadata, excluding old regenerated caches,
        # recovery archives, logs of unrelated deployment and executable launchers.
        for p in src.glob('*.json'):
            if p.name in ('result.json','numerical-evaluation.json','reference-evaluation.json','common-metrics.json'):
                copy(p.relative_to(ROOT),run/'expected'/p.name)
            else:copy(p.relative_to(ROOT))
        if (src/'readout-manifest.json').exists():
            for item in read(src/'readout-manifest.json')['objects']:
                for k in ('prediction','readout','fine_prediction','fine_readout'):
                    if k in item:copy(Path(item[k]))
        if (src/'scoring/results.json').exists():copy(run/'scoring/results.json',run/'expected/results.json')
        for p in src.glob('*/checkpoint.pt'):copy(p.relative_to(ROOT))
        if 'fixed-temperature' in run.name:
            for sub in ('cache','coarse','fine'):
                for p in (src/sub).rglob('*'):
                    if p.is_file() and p.suffix in ('.npy','.npz','.json','.csv'):copy(p.relative_to(ROOT))
            for p in src.glob('*.csv'):copy(p.relative_to(ROOT),run/'expected'/p.name)
        if 'observation-preserving' in run.name:
            for p in (src/'diagnostic-20260925').iterdir():
                if p.suffix in ('.npz','.json','.csv'):copy(p.relative_to(ROOT))
            for p in src.glob('*.npz'):copy(p.relative_to(ROOT))
        if 'phase-moments' in run.name:
            for p in src.glob('*.npz'):copy(p.relative_to(ROOT))
    modules=['phk_v23_b1_evaluate','phk_v23_b1_metrics','phk_v23_phase_moments_evaluate',
        'phk_v23_observation_preserving_phase_evaluate','phk_v23_conditional_phase',
        'phk_v23_spatial_comparison','phk_benchmark','phk_contract']
    done=set()
    while modules:
        name=modules.pop()
        if name in done:continue
        done.add(name);p=Path('pinn_pcm_sci')/(name+'.py');copy(p)
        for node in ast.walk(ast.parse((ROOT/p).read_text(encoding='utf-8-sig'))):
            if isinstance(node,ast.ImportFrom) and node.level==1 and node.module:modules.append(node.module)
    (dest/'pinn_pcm_sci/__init__.py').write_text('"""Frozen array operators for a local research handoff."""\n',encoding='utf-8')
    # Replace only the dependency on the former execution/AD driver with I/O.
    src=ROOT/'pinn_pcm_sci/phk_v23_conditional_phase_evaluate.py'
    text=src.read_text(encoding='utf-8').replace('from .phk_v23_conditional_phase_run import','from .standalone_io import')
    (dest/'pinn_pcm_sci/phk_v23_conditional_phase_evaluate.py').write_text(text,encoding='utf-8')
    for p in (HERE/'portable').glob('*.py'):
        target=dest/('pinn_pcm_sci' if p.name=='standalone_io.py' else '')/p.name
        shutil.copy2(p,target)
    save(dest/'input-inventory.json',index)
    save(dest/'handoff.json',dict(task_id='PCM-20260926-CORE-REVISION-VO2-BRIDGE-01',
        baseline='90508f05a6f233a485413c7589cc74420015cbea',original_repository=str(ROOT),
        input_paths='relative to this root only',third_party_experiment_data_included=False,
        public_access=False,P03='OPEN',capabilities=dict(saved_array_rescoring=True,
        saved_residual_reaggregation=True,checkpoint_inference='checkpoints retained where available; not certified by array-only execution',
        neural_AD_recomputation=False),metric_tolerance=dict(rtol=2e-10,atol=2e-12,booleans='exact'),
        changes_to_original_science='none; dependency I/O shim and lossless storage adapter only'))
    print('HANDOFF_INPUTS_READY',dest,len(index),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();assemble(a.root)
