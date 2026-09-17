"""Prepared fixed-array scoring of two spatial reference trajectories.

Uses native reference terminal quantities and volume-restricted reference
fields. All predictor arrays and electrical readouts remain unchanged.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse
import gc
import importlib.util
import json
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ARCHIVE = ROOT / "outputs/submission-archive-20260916"
RUN = ROOT / "outputs/runs/20260917-lf11-spatial-reference"
sys.path.insert(0,str(ROOT))
from pinn_pcm_sci.phk_benchmark import PhkGrid
from pinn_pcm_sci.phk_v23_spatial_comparison import CellRestriction, threshold_diagnostic

spec=importlib.util.spec_from_file_location("fixed_array_scoring", ARCHIVE/"portable/rescore.py")
scorer=importlib.util.module_from_spec(spec);spec.loader.exec_module(scorer)


def native_grid(nx,nz,metadata):
    grid=PhkGrid.build(nx=nx,nz=nz,**{k:metadata[k] for k in ('x_min','x_max','z_min','z_max')})
    values=dict(grid.__dict__)
    values.update(cell_count=grid.cell_count,x_centers=grid.x_centers,z_centers=grid.z_centers,
                  overlap=grid.bottom_overlap(metadata['heater_width_fraction']),
                  heater_width_fraction=metadata['heater_width_fraction'])
    return scorer.Grid(**values)


def prepare_reference(protocol,manifest,grid,physics,cfg,out):
    folder=RUN/'reference'/protocol
    terminal=scorer.read(folder/'terminal.json')
    if terminal['status']!='VALID_FIXED_SPATIAL_REFERENCE':
        raise ValueError('only a valid saved reference can enter scoring')
    fields,_=scorer.arrays(folder/'result.npz')
    r=terminal['case_spec']['reference']
    native=native_grid(r['nx'],r['nz'],manifest['grid_metadata'])
    scorer.canonical_coordinates(fields,native)
    restriction=CellRestriction(r['nx'],r['nz'],grid.nx,grid.nz)
    qnative=scorer.deposition(fields,native,physics)
    with np.load(folder/'result.npz',allow_pickle=False) as f:
        device={k:f[k] for k in ('top_current','bottom_current','joule_power')}
    qpower=qnative@native.cell_volumes
    np.testing.assert_allclose(qpower,device['joule_power'],rtol=1e-10,atol=1e-11)
    mapped={key:restriction(fields[key]) for key in ('potential','temperature','phase')}
    mapped.update(time=fields['time'],x=grid.x_centers,z=grid.z_centers)
    q=restriction(qnative)
    np.testing.assert_allclose(q@grid.cell_volumes,qpower,rtol=1e-11,atol=1e-12)
    conservation={key:float(np.max(abs(mapped[key]@grid.cell_volumes-fields[key]@native.cell_volumes)))
                  for key in ('potential','temperature','phase')}
    active=restriction((fields['phase']>=cfg['qualification_event']['phase_threshold']).astype(float))
    np.savez_compressed(folder/'mapped-reference.npz',**mapped,**device,joule_density=q)
    np.save(folder/'restricted-active.npy',active,allow_pickle=False)
    scorer.save(folder/'mapping.json',dict(method='nonnegative cell-overlap volume restriction',
        source_grid=[native.nx,native.nz],target_grid=[grid.nx,grid.nz],
        max_integral_discrepancy=conservation,native_q_power_max_error=float(np.max(abs(qpower-device['joule_power']))),
        model_arrays_changed=False,new_electrical_solves=0,
        terminal_reference='native fine grid, not recomputed from restricted V'))
    ref=SimpleNamespace(**mapped,**device,grid=grid)
    ev=cfg['qualification_event'];rs=ev['roi']
    roi=(abs(grid.cell_x)<=rs['abs_x_max'])&(grid.cell_z>=rs['z_min'])&(grid.cell_z<=rs['z_max'])
    events=scorer.core._event_summary(ref.phase,time=ref.time,roi=roi,period=physics.period,
        phase_threshold=ev['phase_threshold'],event_fraction=ev['event_threshold_roi_fraction'])
    del fields,qnative
    gc.collect()
    return ref,q,active,events,roi


def causal_prefix():
    errors={}
    with np.load(RUN/'reference/original/result.npz',allow_pickle=False) as a, \
         np.load(RUN/'reference/shorter/result.npz',allow_pickle=False) as b:
        np.testing.assert_array_equal(a['time'],b['time'])
        prefix=a['time']<1.01
        for key in ('potential','temperature','phase'):
            aa=a[key];bb=b[key]
            errors[key]=float(np.max(abs(aa[prefix]-bb[prefix])))
            del aa,bb
    if any(v>1e-10 for v in errors.values()):
        raise AssertionError(('new-reference causal-prefix mismatch',errors))
    return errors


def main():
    manifest=scorer.read(ARCHIVE/'manifest.json')
    previous=scorer.read(ARCHIVE/'rescore-output/results.json')
    grid=scorer.geometry(ARCHIVE,manifest)
    out=RUN/'scoring';out.mkdir(exist_ok=False)
    prefix=causal_prefix()
    records={};mapping_checks={};deltas={};reference_events={};comparison={}
    for protocol in ('original','shorter'):
        desc=manifest['protocols'][protocol]
        cfg=scorer.read(ARCHIVE/desc['config'])
        physics=scorer.Physics(protocol=protocol,**desc['physics'])
        ref,q,active,events,roi=prepare_reference(protocol,manifest,grid,physics,cfg,out)
        baseline,bq,bevents,_=scorer.load_reference(ARCHIVE,desc['references']['refined'],grid,physics,cfg)
        np.testing.assert_array_equal(baseline.time,ref.time)
        deltas[protocol]={
            'S':float(np.trapezoid(np.mean((ref.phase>=.5)!=(baseline.phase>=.5),axis=1),ref.time)/2.5),
            'Ephi':scorer.core.field_rms(ref.phase,baseline.phase,ref.time,roi),
            'ET':scorer.core.field_rms(ref.temperature,baseline.temperature,ref.time,roi)/.45,
            'EV':scorer.core.field_rms(ref.potential,baseline.potential,ref.time),
            'current_rms':scorer.core.time_rms(ref.top_current-baseline.top_current,ref.time),
            'power_rms':scorer.core.time_rms(ref.joule_power-baseline.joule_power,ref.time),
            'q_rms':scorer.core.field_rms(q,bq,ref.time)}
        reference_events[protocol]=dict(baseline=bevents,spatial=events)
        scorer.save(out/f'{protocol}-reference-events.json',reference_events[protocol])
        del baseline,bq;gc.collect()
        oldscales=previous['records']['old'][f'{protocol}/29/E']['normalizers']
        for item in (i for i in manifest['objects'] if i['protocol']==protocol):
            record=scorer.score(ARCHIVE,item,ref,q,events,roi,physics,cfg,out,'spatial',oldscales)
            records[item['id']]=record
            with np.load(ARCHIVE/item['prediction'],allow_pickle=False) as f:
                mapping_checks[item['id']]=threshold_diagnostic(f['phase'],ref.phase,active,
                    ref.time,cfg['windows'],cfg['qualification_event']['phase_threshold'])
            diagnostic=mapping_checks[item['id']]
            np.testing.assert_allclose(diagnostic['S_primary'],record['metrics']['S'],rtol=0,atol=2e-14)
            for actual,check in zip(record['cycles'],diagnostic['cycles'],strict=True):
                for original_key,diagnostic_key in (
                    ('teacher_active_target_mass','reference_mass_primary'),
                    ('true_positive_target_mass','overlap_primary'),
                    ('predicted_active_target_mass','predicted_mass'),
                    ('recall','recall_primary')):
                    np.testing.assert_allclose(actual[original_key],check[diagnostic_key],rtol=1e-12,atol=2e-14)
            scorer.save(out/'partial-results.json',records)
        comparison[protocol]=scorer.decisions(records,cfg,protocol)
        del ref,q,active;gc.collect()
    scorer.save(out/'results.json',dict(status='COMPLETE_FIXED_ARRAY_SPATIAL_REFERENCE_CHECK',
        records=records,decisions=comparison,reference_delta_from_time_refined=deltas,
        mapping_diagnostics=mapping_checks,causal_prefix_max_error=prefix,
        model_predictions_unchanged=True,new_training=0,new_checkpoint_evaluations=0,
        new_prediction_electric_solves=0,scope='Native reference device readout; fields and threshold gates restricted to the fixed 160x80 scoring grid'))
    print(json.dumps(dict(status='COMPLETE',objects=len(records),deltas=deltas)),flush=True)


if __name__=='__main__':main()
