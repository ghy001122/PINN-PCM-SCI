"""Collect the authorized submission archive locally; never execute a model.

Preparation serializes known constants and expected saved scores. Collection
requires the current GPU shutdown receipt and copies existing files only.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
RUN=ROOT/'outputs/runs/20260916-lf11-phase-adapter-reference'
ARCHIVE=ROOT/'outputs/submission-archive-20260916'


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')


def copy(source,destination):
    destination.parent.mkdir(parents=True,exist_ok=True)
    if not source.is_file():raise FileNotFoundError(source.relative_to(ROOT))
    if destination.exists():
        if destination.stat().st_size!=source.stat().st_size:raise FileExistsError(destination)
        return
    shutil.copy2(source,destination)


def prepare(archive):
    from pinn_pcm_sci.phk_v22r_training import load_case_physics
    from pinn_pcm_sci.phk_v22r_evaluator import _physical_contract
    from pinn_pcm_sci.phk_benchmark import PhkGrid
    physics=load_case_physics()[0];p=asdict(physics)
    grid=PhkGrid.build(nx=160,nz=80,x_min=p['x_min'],x_max=p['x_max'],z_min=p['z_min'],z_max=p['z_max'])
    archive.mkdir(parents=True,exist_ok=True)
    (archive/'definitions').mkdir(exist_ok=True)
    names=('cell_x','cell_z','cell_volumes','internal_first','internal_second','internal_area','internal_half_distance','x_centers','z_centers')
    np.savez_compressed(archive/'definitions/grid.npz',**{k:getattr(grid,k) for k in names},
                        overlap=grid.bottom_overlap(p['heater_width_fraction']))
    meta={k:getattr(grid,k) for k in ('nx','nz','dx','dz','x_min','x_max','z_min','z_max','cell_count')}
    meta['heater_width_fraction']=p['heater_width_fraction']
    manifest=dict(schema_id='pinn-pcm-array-rescore-20260916',source_commit='4081ba09b8a6aefa2141b10c707fdf4b327898eb',
        grid_metadata=meta,grid_arrays='definitions/grid.npz',protocols={},objects=[],
        scope='fixed array rescore and time-reference perturbation; not continuum validation or new training',
        paths='all relative to archive root',publicly_uploaded=False,reference_read_in_preparation=False)
    sources={}
    basecfg=read(ROOT/'configs/phk_v23/lf11_phase_adapter_sprint.json')
    roots={'original':ROOT/'outputs/runs/20260914-lf11-clean-confirmation',
           'shorter':ROOT/'outputs/runs/20260915-lf11-protocol-history'}
    def register(source,dest):sources[dest]=source.relative_to(ROOT).as_posix();return dest
    for protocol,folder in roots.items():
        cfg=read(folder/'seed-29/frozen-config.json')
        cfg['qualification_event']=_physical_contract().payload['qualification_event']
        cfg['evaluation']={'readout':'COMMON_FV_FACE_FLUX_EDGE_DISSIPATION_V1'}
        cfg['display_rule']=basecfg['display_rule']
        # Evaluation-only definitions. Omit unrelated runtime and historical paths.
        scoring={k:cfg[k] for k in ('windows','decision','functional_rule','qualification_event','evaluation','display_rule')}
        save(archive/f'definitions/{protocol}.json',scoring)
        pp=dict(p);pp['period']=1.25 if protocol=='original' else 1.01
        refold=(ROOT/'outputs/runs/20260828T-phk-v21-s1-q-06-nominal-extra-fine/result-intent-06.npz'
                if protocol=='original' else folder/'local-reference/reference/result.npz')
        refs={name:register(source,f'data/{protocol}/reference-{name}.npz') for name,source in
              [('old',refold),('refined',RUN/f'local-reference/{protocol}/result.npz')]}
        sparse=(ROOT/'paper/paper_v24/evidence/input/sparse.npz' if protocol=='original' else folder/'input/sparse.npz')
        register(sparse,f'data/{protocol}/sparse.npz')
        manifest['protocols'][protocol]=dict(physics=pp,config=f'definitions/{protocol}.json',references=refs,
            sparse=f'data/{protocol}/sparse.npz',expected_decisions=f'expected/{protocol}-decisions.json')
        expected_decisions={}
        for seed in (29,43):
            results=read(ROOT/f'paper/paper_v31/evidence/confirmation/seed-{seed}/evaluation/results.json') if protocol=='original' else read(folder/'evaluation/results.json')
            expected_decisions[str(seed)]=results['decision'] if protocol=='original' else results['decisions'][str(seed)]
            for role,dirname,recordname in [('E','E','E/projected'),('F','F_raw','F_raw/projected')]:
                oid=f'{protocol}/{seed}/{role}';dest=f'data/{oid}'
                rec=results['records'][recordname if protocol=='original' else f'{seed}/{recordname}']
                save(archive/f'expected/{protocol}-{seed}-{role}.json',rec)
                item=dict(id=oid,protocol=protocol,seed=seed,role=role,origin='historical',
                    prediction=register(folder/f'seed-{seed}/{dirname}/projected/prediction.npz',dest+'/prediction.npz'),
                    readout=register(folder/f'seed-{seed}/{dirname}/projected/own-readout.npz',dest+'/readout.npz'),
                    expected_record=f'expected/{protocol}-{seed}-{role}.json')
                register(folder/f'seed-{seed}/{dirname}/checkpoint.pt',f'models/{oid}/checkpoint.pt')
                register(folder/f'seed-{seed}/{dirname}/terminal.json',f'models/{oid}/terminal.json')
                register(folder/f'seed-{seed}/{dirname}/projected/prediction.json',f'models/{oid}/prediction.json')
                manifest['objects'].append(item)
            for fn in ('frozen-config.json','calibration.json','calibration-pool.json','lbfgs-pool.json','audit-pool.json'):
                register(folder/f'seed-{seed}/{fn}',f'models/{protocol}/{seed}/{fn}')
        save(archive/f'expected/{protocol}-decisions.json',expected_decisions)
        baseline=(ROOT/'outputs/runs/20260913-lf11-electrical-elimination/B_E' if protocol=='original' else folder/'B_E/projected')
        save(archive/f'expected/{protocol}-B_E.json',results['records']['B_E'])
        manifest['objects'].append(dict(id=protocol+'/B_E',protocol=protocol,seed=None,role='B_E',origin='historical',
            prediction=register(baseline/'prediction.npz',f'data/{protocol}/B_E/prediction.npz'),
            readout=register(baseline/'own-readout.npz',f'data/{protocol}/B_E/readout.npz'),expected_record=f'expected/{protocol}-B_E.json'))
    for seed in (29,43):
        folder=RUN/f'seed-{seed}'
        for fn in ('parent.pt','frozen-config.json','calibration.json','calibration-pool.json','lbfgs-pool.json','audit-pool.json','gate-calibration.json','adapter-initial.pt'):
            register(folder/fn,f'models/phase-adapter/{seed}/{fn}')
        for role in ('E_C','E_R','E_I'):
            oid=f'shorter/{seed}/{role}';dest=f'data/{oid}'
            item=dict(id=oid,protocol='shorter',seed=seed,role=role,origin='new_phase_adapter',
                prediction=register(folder/role/'projected/prediction.npz',dest+'/prediction.npz'),
                readout=register(folder/role/'projected/own-readout.npz',dest+'/readout.npz'),
                display=register(folder/role/'projected/fixed-display.npz',dest+'/fixed-display.npz'))
            manifest['objects'].append(item)
            for fn in ('checkpoint.pt','adam-300.pt','adam-600.pt','terminal.json','adam-telemetry.jsonl','lbfgs-telemetry.jsonl'):
                register(folder/role/fn,f'models/phase-adapter/{seed}/{role}/{fn}')
            register(folder/role/'projected/prediction.json',f'models/phase-adapter/{seed}/{role}/prediction.json')
    save(archive/'manifest.json',manifest)
    # This build map stays outside the portable archive. No private absolute paths in the archive.
    save(HERE/'build/archive-source-map.json',sources)
    if list(archive.glob('*/results.json')):
        raise FileExistsError('Do not replace a scorer after results have consumed it')
    (archive/'portable').mkdir(exist_ok=True)
    for path in (HERE/'portable').glob('*.py'):shutil.copy2(path,archive/'portable'/path.name)
    shutil.copy2(HERE/'portable/README.md',archive/'README.md')
    copy(ROOT/'paper/paper_submission/tables/unified-results.csv',archive/'expected/published-main-table.csv')
    copy(ROOT/'paper/paper_submission/tables/complete-events.csv',archive/'expected/published-events.csv')
    copy(ROOT/'docs/notes/2026-09-16-phase-adapter-authorized-sprint.md',archive/'definitions/authorized-protocol.md')
    deployed=read(ROOT/'.t/phase-adapter-deployment/selected-files.json')
    for rel in deployed:
        if rel.startswith(('pinn_pcm_sci/','configs/','tests/','outputs/runs/20260827T-phk-v21-e2-engineering-search-001/')):
            copy(ROOT/rel,archive/'training/runtime-source'/rel)
    copy(HERE/'portable/reproduce_network.py',archive/'portable/reproduce_network.py')
    print(json.dumps(dict(status='ARCHIVE_MANIFEST_PREPARED',objects=len(manifest['objects']),reference_fields_read=False)))


def collect(archive,allow_pending_references=False):
    proof=read(RUN/'compute-closure.json')
    if not all(proof.get(k) for k in ('training_complete','recovery_verified','shutdown_requested','instance_shutdown_confirmed','compute_stopped_before_reference_read')):
        raise ValueError('Current GPU recovery and shutdown must be complete before collection/scoring')
    sources=read(HERE/'build/archive-source-map.json');pending=[]
    for dest,source in sources.items():
        path=ROOT/source
        if not path.exists() and allow_pending_references and dest.endswith('reference-refined.npz'):
            pending.append(dest);continue
        copy(path,archive/dest)
    for protocol in ('original','shorter'):
        terminal=RUN/f'local-reference/{protocol}/terminal.json'
        if terminal.exists():copy(terminal,archive/f'definitions/{protocol}-refined-terminal.json')
        correction=RUN/f'local-reference/{protocol}/metadata-clarification.json'
        if correction.exists():copy(correction,archive/f'definitions/{protocol}-metadata-clarification.json')
    for name in ('execution-summary.json','actual-parent-interface-checks.json','focused-checks.json'):
        copy(RUN/name,archive/'definitions'/name)
    save(archive/'definitions/effective-phase-head-protocol.json',dict(
        parents={str(seed):read(RUN/f'seed-{seed}/frozen-config.json')['parent'] for seed in (29,43)},
        parent_role='Final V32 short-gap E per seed; not an observation-only or V28 parent',
        calibrations='The corresponding original seed aE/bE and original pools are reused, not recalibrated',
        only_scientific_change='Original phase head versus ordinary residual versus fixed parent-interface gated residual',
        lambda_from_first_update=0.1,adam_per_arm=600,full_evaluations_per_arm=100,
        legacy_template_labels='Unused historical description fields remain in the frozen configs; effective seed config, source and this role map identify execution',
        no_settings_changed_after_first_update=True))
    public_compute={k:proof[k] for k in ('mode','training_complete','recovery_verified','shutdown_requested',
        'instance_shutdown_confirmed','compute_stopped_before_reference_read')}
    save(archive/'definitions/compute-closure-summary.json',public_compute)
    import importlib.metadata
    save(archive/'definitions/scoring-environment.json',dict(python=sys.version,numpy=np.__version__,
        scope='array-only evaluation environment',training_environment=dict(python='3.11.9',torch='2.5.1+cu118',
        numpy='2.1.1',scipy='1.14.1',dtype='float64',cuda_device='Tesla V100-PCIE-32GB'),
        environment_is_not_a_speed_comparison=True))
    save(archive/'collection.json',dict(status='PENDING_REFINED_REFERENCES' if pending else 'COMPLETE',pending=pending,
         neural_execution_during_collection=0,linear_solves_during_collection=0,public_upload=False))
    print(json.dumps(dict(status='LOCAL_ARCHIVE_COLLECTED',pending=pending)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','collect'])
    p.add_argument('--archive',type=Path,default=ARCHIVE);p.add_argument('--allow-pending-references',action='store_true')
    a=p.parse_args()
    if a.action=='prepare':prepare(a.archive)
    else:collect(a.archive,a.allow_pending_references)
