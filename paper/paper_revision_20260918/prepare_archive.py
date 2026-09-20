"""Build a local, portable extension; never upload or change frozen arrays."""
from pathlib import Path
import json
import os
import shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OLD=ROOT/'outputs/submission-archive-20260916'
DEST=ROOT/'outputs/submission-archive-20260918'
RUN=ROOT/'outputs/runs/20260918-lf11-readout-clean-pde'
SPATIAL=ROOT/'outputs/runs/20260917-lf11-spatial-reference'

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def link(src,dst):
    if not src.is_file():raise FileNotFoundError(src)
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():return
    os.link(src,dst)

def main():
    closure=read(RUN/'compute-closure.json')
    if not closure.get('instance_shutdown_confirmed'):raise RuntimeError('Current GPU closure required before array scoring preparation.')
    assert read(RUN/'training-and-own-inference-complete.json')['status']=='ALL_FIXED_ARTIFACTS_COMPLETE'
    DEST.mkdir(exist_ok=True)
    for part in ('data','definitions','expected','models','training','source','environment'):
        if (OLD/part).exists():
            for p in (OLD/part).rglob('*'):
                if p.is_file():link(p,DEST/p.relative_to(OLD))
    manifest=read(OLD/'manifest.json')
    save(DEST/'historical-manifest.json',manifest)
    save(DEST/'expected/historical-time-results.json',read(OLD/'rescore-output/results.json'))
    save(DEST/'expected/historical-spatial-results.json',read(SPATIAL/'scoring/results.json'))
    objects=[]
    for item in manifest['objects']:
        r=dict(item)
        if item['origin']=='historical':
            folder=RUN/'fine-readout'/item['id']
            for n in ('prediction.npz','own-readout.npz','prediction.json'):
                link(folder/n,DEST/'fine'/item['id']/n)
            r['fine_prediction']=f"fine/{item['id']}/prediction.npz"
            r['fine_readout']=f"fine/{item['id']}/own-readout.npz"
        objects.append(r)
    for seed in (29,43):
        folder=RUN/'clean-pde'/f'seed-{seed}'/'D_E'
        oid=f'shorter/{seed}/D_E'
        for level in ('coarse','fine'):
            for n in ('prediction.npz','own-readout.npz','prediction.json'):
                link(folder/level/n,DEST/level/oid/n)
        for p in (RUN/'clean-pde'/f'seed-{seed}').rglob('*'):
            if p.is_file() and p.suffix in ('.json','.jsonl','.pt'):
                link(p,DEST/'training'/p.relative_to(RUN))
        objects.append(dict(id=oid,protocol='shorter',seed=seed,role='D_E',origin='clean_pde_ablation',
            prediction=f'coarse/{oid}/prediction.npz',readout=f'coarse/{oid}/own-readout.npz',
            fine_prediction=f'fine/{oid}/prediction.npz',fine_readout=f'fine/{oid}/own-readout.npz'))
    for case,desc in manifest['protocols'].items():
        for n in ('result.npz','mapped-reference.npz','mapping.json','terminal.json','intent.json'):
            link(SPATIAL/'reference'/case/n,DEST/'spatial'/case/n)
        desc['references']['spatial']=f'spatial/{case}/mapped-reference.npz'
        desc['native_spatial_reference']=f'spatial/{case}/result.npz'
    manifest.update(schema_id='pinn-pcm-array-readout-clean-pde-20260918',objects=objects,
        public_upload=False,fine_grid=[240,120],coarse_grid=[160,80],
        source_scope='Frozen historical arrays plus one reader level and two clean D_E; no new references.',
        physics_evaluation_grid='T/phase/events:160x80; fine V volume-restricted; native ports retained',
        negative_continuations='six historical arms remain in the same scoring manifest')
    save(DEST/'manifest.json',manifest)
    portable=DEST/'portable';portable.mkdir(exist_ok=True)
    for name in ('rescore.py','frozen_metrics.py'):
        shutil.copy2(OLD/'portable'/name,portable/name)
    # Preserve the historical scope when this retained entry is invoked.
    entry=(portable/'rescore.py').read_text(encoding='utf-8')
    entry=entry.replace("manifest=read(root/'manifest.json')", "manifest=read(root/'historical-manifest.json')")
    (portable/'rescore.py').write_text(entry,encoding='utf-8')
    kernel=(portable/'frozen_metrics.py').read_text(encoding='utf-8')
    assert kernel.count('def metrics(fields, reference, physics, config):')==1
    kernel=kernel.replace('def metrics(fields, reference, physics, config):',
        'def metrics(fields, reference, physics, config, device_override=None):')
    original='device = readout(fields["potential"], fields["temperature"], fields["phase"], grid, voltage, physics)'
    assert kernel.count(original)==1
    kernel=kernel.replace(original,'device = (device_override if device_override is not None else\n        readout(fields["potential"], fields["temperature"], fields["phase"], grid, voltage, physics))')
    (portable/'readout_metrics.py').write_text(kernel,encoding='utf-8')
    shutil.copy2(HERE/'readout_rescore.py',portable/'readout_rescore.py')
    shutil.copy2(HERE/'reproduce_new_experiment.py',portable/'reproduce_new_experiment.py')
    shutil.copy2(OLD/'portable/reproduce_network.py',portable/'reproduce_network.py')
    link(ROOT/'.t/readout-clean-pde-deployment/readout-clean-pde.tar.gz',
         DEST/'training/new-execution-runtime.tar.gz')
    for n in ('execution-environment.json','gpu-batching-check.json','scoring-interface-check.json'):
        if (RUN/n).is_file():save(DEST/'execution'/n,read(RUN/n))
    save(DEST/'execution/compute-closure-summary.json',{k:closure[k] for k in
        ('recovery_verified','instance_shutdown_confirmed','training_complete','compute_stopped_before_reference_read')})
    shutil.copy2(ROOT/'pinn_pcm_sci/phk_v23_spatial_comparison.py',portable/'source_restriction.py')
    save(DEST/'execution-summary.json',read(RUN/'training-and-own-inference-complete.json'))
    save(DEST/'fixed-residual-audits.json',read(RUN/'fixed-residual-audits.json'))
    save(DEST/'interface-checks.json',read(RUN/'interface-checks.json'))
    (DEST/'README.md').write_text('''# Local submission array package

This local package has not been publicly released. All data are synthetic; no material or experimental validation is implied.

Run `python -I portable/readout_rescore.py --root . --out isolated-rescore` with Python 3.11 and NumPy. The entry reads arrays only and imports no training library. It never loads checkpoints, queries a model or solves a linear system. It retains all three references, two electrical readout grids, historical negative continuations and two clean D_E endpoints. T/phase/event comparisons use the original 160×80 measure; finer electrical ports are native, and fine V is volume-restricted only for the original field guard. Local q on 240×120 is primary only against the native spatial reference.

The historical evaluator is retained as `portable/rescore.py`, with `historical-manifest.json` identifying its unchanged scope. Its preceding isolated verification is not independent retraining. Model files and recipes are separate from array scoring. Current endpoints are in `training`; the new execution entry and source bundle accompany the manuscript delivery.

Numerical reproduction tolerance is rtol=2e-10, atol=2e-12; categorical decisions must agree exactly. Scientific effect thresholds are unchanged. No phase/reference threshold is applied after interpolating a binary prediction.
''',encoding='utf-8')
    print(json.dumps(dict(archive=str(DEST),objects=len(objects),fine_objects=12,public_upload=False)))

if __name__=='__main__':main()
