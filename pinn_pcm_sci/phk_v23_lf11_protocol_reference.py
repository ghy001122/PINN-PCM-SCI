"""Local-only generation of the two explicitly authorized V32 trajectories."""
from __future__ import annotations
import argparse
from dataclasses import replace
import json
from pathlib import Path
import numpy as np
import torch
from .phk_v23_lf11 import ROOT, now, save_json, extract_sparse
from .phk_v23_lf11_protocol import CASE, validate_case, waveform, powered_count
from .phk_benchmark import PhkResolution
from .phk_v21_benchmark import (PhkV21OracleCase, PhkV21CaseSpec,
    write_phk_v21_result, read_phk_v21_result)
from .phk_v22r_evaluator import _physical_contract

RUN = ROOT/'outputs/runs/20260915-lf11-protocol-history'


class FiniteOracle(PhkV21OracleCase):
    def __init__(self, spec, resolution):
        validate_case(spec)
        self.spec = spec
        physical = _physical_contract()
        case = replace(PhkV21CaseSpec.nominal(physical), period=spec['pulse_starts'][1],
                       case_id=spec['case_id'])
        if resolution.evidence_identity != 'LF11_FINITE_PROTOCOL_AUTHORIZED_RESOLUTION':
            raise ValueError('new protocol requires its own authorized resolution identity')
        # Reuse the frozen constructor's structural checks, then record the
        # separate user-authorized experiment identity. No frozen core edits.
        super().__init__(physical=physical, case=case, resolution=replace(resolution,
                         evidence_identity='PHK_V21_FROZEN_Q_RESOLUTION'))
        self.resolution=resolution
        self.last_reported_step=-1

    def waveform(self, time_value):
        step=round(time_value/self.resolution.dt)
        if getattr(self, 'report_progress', False) and step%100==0 and step!=self.last_reported_step:
            print(json.dumps(dict(kind=self.resolution.name,step_entered=step,
                  main_steps=round(self.resolution.time_end/self.resolution.dt))),flush=True)
            self.last_reported_step=step
        return float(waveform(torch.tensor(time_value, dtype=torch.float64), self.spec))


def bounds(steps):
    # Per block: electric, phase Newton, thermal; a final electric check can
    # occur in each of 30 blocks. Each phase call has <=30 Newton solves and
    # <=31+30*21 residual evaluations (steps 1,...,2^-20 in line search).
    return dict(main_steps=steps, coupled_blocks=30*steps,
        electric_linear_solves=1+60*steps, thermal_linear_solves=30*steps,
        phase_calls=30*steps, phase_linear_solves=900*steps,
        phase_residual_evaluations=30*661*steps,
        phase_jacobian_evaluations_reported=30*31*steps,
        final_residual_evaluations=30*steps,
        thermal_factorizations=1,
        note='Phase line-search residual helper also builds Jacobians; reported Jacobian counter counts Newton bases only.')


def freeze(root=RUN):
    root.mkdir(parents=True, exist_ok=True)
    validate_case(CASE)
    result=dict(status='FROZEN_BEFORE_NEW_CASE_FIELDS', case_spec=CASE,
        recorded_utc=now(), main_trajectories={k:bounds(CASE[k]['main_steps']) for k in ('support','reference')},
        conditional_time_refinement=dict(trigger_required=True, nx=160,nz=80,dt=.0003125,save_every=8,**bounds(8000)),
        inference_nonzero_times_per_projection=powered_count(CASE),
        inference_projection_roles=5, inference_forward_cap=5*powered_count(CASE),
        training=dict(adam=10800,complete_evaluations=2400,E_forward=54000,E_adjoint=54000,
                      calibration_forward=1000,calibration_adjoint=1000,
                      audit_forward=1000,audit_adjoint=1000),
        support_mask=dict(x_indices=list(range(0,80,4))+[79],z_indices=list(range(0,40,4))+[39],
                          time_indices=list(range(0,501,4))),
        no_stress=True, old_contracts_unchanged=True)
    path=root/'case-and-budget.json'
    if path.exists():
        old=json.loads(path.read_text(encoding='utf-8'))
        if old['case_spec']!=CASE:raise ValueError('frozen case conflict')
        return old
    save_json(path,result)
    return result


def generate(kind, root=RUN):
    frozen=json.loads((root/'case-and-budget.json').read_text(encoding='utf-8'))
    spec=frozen['case_spec'];validate_case(spec)
    r=spec[kind]
    folder=root/'local-reference'/kind;folder.mkdir(parents=True,exist_ok=False)
    save_json(folder/'intent.json',dict(status='AUTHORIZED_STARTED',kind=kind,case_spec=spec,
        budget=frozen['main_trajectories'][kind], recorded_utc=now()))
    resolution=PhkResolution(name='LF11_NEW_PROTOCOL_'+kind.upper(),nx=r['nx'],nz=r['nz'],
        dt=r['dt'],time_end=spec['time_end'],save_every=r['save_every'],
        evidence_identity='LF11_FINITE_PROTOCOL_AUTHORIZED_RESOLUTION')
    runner=FiniteOracle(spec,resolution)
    runner.report_progress=True
    try:
        result=runner.solve()
        write_phk_v21_result(folder/'result.npz',result)
        if result.solver_statistics['time_steps_total']!=r['main_steps']:
            raise AssertionError('trajectory step count')
        limits=frozen['main_trajectories'][kind]
        for counter,key in [('electric_linear_solves_total','electric_linear_solves'),
            ('thermal_linear_solves_total','thermal_linear_solves'),('phase_linear_solves_total','phase_linear_solves')]:
            if result.solver_statistics[counter]>limits[key]:raise AssertionError('solver budget')
        # Causal prefix comparison is a generator check, never model selection.
        oldpath=ROOT/('outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz'
                     if kind=='support' else 'outputs/runs/20260828T-phk-v21-s1-q-06-nominal-extra-fine/result-intent-06.npz')
        with np.load(oldpath,allow_pickle=False) as old:
            np.testing.assert_array_equal(old['time'],result.time)
            prefix=result.time<spec['pulse_starts'][1]
            errors={k:float(np.max(np.abs(getattr(result,k)[prefix]-old[k][prefix])))
                    for k in ('potential','temperature','phase')}
        if any(v>1e-10 for v in errors.values()):raise AssertionError(('causal prefix mismatch',errors))
        manifest=dict(status='VALID_FIXED_REFERENCE_CARRIER',kind=kind,case_spec=spec,
            prefix_max_absolute_errors=errors,solver_statistics=dict(result.solver_statistics),
            phase_range=[float(result.phase.min()),float(result.phase.max())],
            max_thermal_residual=float(np.max(result.thermal_residual_history)),
            max_phase_residual=float(np.max(result.phase_residual_history)),
            max_current_balance=float(np.max(result.current_balance_history)),
            reference_only=kind=='reference', recorded_utc=now())
        save_json(folder/'terminal.json',manifest)
        if kind=='support':
            cfg=json.loads((ROOT/'configs/phk_v23/lf11_protocol_sprint.json').read_text(encoding='utf-8'))
            extract_sparse(folder/'result.npz',root/'input',cfg)
            with np.load(root/'input/sparse.npz') as sparse, np.load(ROOT/'paper/paper_v24/evidence/input/sparse.npz') as old:
                for axis in ('x','z','time','coordinates'):np.testing.assert_array_equal(sparse[axis],old[axis])
        print(json.dumps(manifest),flush=True)
    except BaseException as exc:
        save_json(folder/'failure.json',dict(status='STOPPED_NO_RESCUE',error=repr(exc),recorded_utc=now()))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','support','reference']);p.add_argument('--root',type=Path,default=RUN)
    a=p.parse_args()
    if a.action=='freeze':print(json.dumps(freeze(a.root)),flush=True)
    else:generate(a.action,a.root)
