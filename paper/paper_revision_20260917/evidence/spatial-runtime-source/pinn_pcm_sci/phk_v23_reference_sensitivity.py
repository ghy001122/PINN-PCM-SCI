"""Two new fixed-grid reference trajectories; no neural state is consumed.

The original nonlinear algorithms and tolerances are unchanged. A local scipy
call wrapper counts actual solves and stops before exceeding the authorized cap.
"""
from __future__ import annotations
import argparse
import copy
from dataclasses import replace
import json
from pathlib import Path
import numpy as np
import torch
import scipy.sparse.linalg as sla
from .phk_v23_lf11 import ROOT, save_json, now
from .phk_v23_lf11_protocol import CASE, waveform
from .phk_benchmark import PhkResolution
from .phk_v21_benchmark import PhkV21OracleCase, PhkV21CaseSpec, write_phk_v21_result
from .phk_v22r_evaluator import _physical_contract
from . import phk_v21_benchmark as core

RUN=ROOT/'outputs/runs/20260916-lf11-phase-adapter-reference'


def reference_spec(protocol):
    spec=copy.deepcopy(CASE)
    if protocol=='original':
        spec.update(pulse_starts=[0.,1.25],recovery_cycles=[[0.,1.25],[1.25,2.5]],
            tail=[2.5,2.5],windows=[[0.,.35],[.35,1.25],[1.25,1.6],[1.6,2.5]],
            window_masses=[.14,.36,.14,.36])
    spec['case_id']='lf11-reference-sensitivity-'+protocol
    spec['reference']=dict(nx=160,nz=80,dt=.0003125,save_every=8,main_steps=8000)
    spec['changed_physics']='none; fixed spatial grid and halved reference integration time step'
    return spec


class ReferenceOracle(PhkV21OracleCase):
    def __init__(self, protocol, output):
        self.spec=reference_spec(protocol);self.output=output;self.last_step=-1
        p=_physical_contract()
        # Identical numerical core; new resolution recorded in a separate run.
        resolution=PhkResolution(name='LF11_TIME_SENSITIVITY_'+protocol.upper(),nx=160,nz=80,
            dt=.0003125,time_end=2.5,save_every=8,evidence_identity='PHK_V21_FROZEN_Q_RESOLUTION')
        case=replace(PhkV21CaseSpec.nominal(p),period=self.spec['pulse_starts'][1],case_id=self.spec['case_id'])
        super().__init__(physical=p,case=case,resolution=resolution)
        self.resolution=replace(resolution,evidence_identity='LF11_FIXED_MODEL_REFERENCE_SENSITIVITY')

    def waveform(self,t):
        step=round(t/self.resolution.dt)
        if step%100==0 and step!=self.last_step:
            self.last_step=step
            save_json(self.output/'progress.json',dict(step_entered=step,main_steps=8000,
                linear_solves=dict(self.solve_counts),created_utc=now()))
            print(json.dumps(dict(protocol=self.spec['case_id'],step_entered=step,linear_solves=sum(self.solve_counts.values()))),flush=True)
        return float(waveform(torch.tensor(t,dtype=torch.float64),self.spec))


def generate(protocol,root=RUN):
    out=root/'local-reference'/protocol;out.mkdir(parents=True,exist_ok=False)
    runner=ReferenceOracle(protocol,out);counts={'electric':0,'thermal':0,'phase':0};runner.solve_counts=counts
    kind=['phase'];limit=200000
    originals=(sla.spsolve,sla.splu,core.solve_electric_field,core.solve_phase_candidate)
    def consume(label):
        if sum(counts.values())>=limit:raise RuntimeError('authorized reference linear-solve cap reached')
        counts[label]+=1
    def direct(*args,**kwargs):
        consume(kind[0]);return originals[0](*args,**kwargs)
    class Factor:
        def __init__(self,factor):self.factor=factor
        def solve(self,*args,**kwargs):
            consume('thermal');return self.factor.solve(*args,**kwargs)
    def factor(*args,**kwargs):return Factor(originals[1](*args,**kwargs))
    def electric(*args,**kwargs):
        previous=kind[0];kind[0]='electric'
        try:return originals[2](*args,**kwargs)
        finally:kind[0]=previous
    def phase(*args,**kwargs):
        previous=kind[0];kind[0]='phase'
        try:return originals[3](*args,**kwargs)
        finally:kind[0]=previous
    save_json(out/'intent.json',dict(status='AUTHORIZED_STARTED',protocol=protocol,case_spec=runner.spec,
        grid=[160,80],dt=.0003125,save_every=8,main_steps_cap=8000,linear_solves_cap=limit,
        inherited_algorithm_tolerances=True,output_clipping_allowed=False,neural_inputs_received=False))
    try:
        sla.spsolve,sla.splu,core.solve_electric_field,core.solve_phase_candidate=direct,factor,electric,phase
        result=runner.solve()
        for name,n in counts.items():
            if result.solver_statistics[name+'_linear_solves_total']!=n:raise AssertionError(('reference count mismatch',name,n,result.solver_statistics))
        if result.solver_statistics['time_steps_total']!=8000 or len(result.time)!=1001:raise AssertionError('reference time budget')
        write_phk_v21_result(out/'result.npz',result)
        save_json(out/'terminal.json',dict(status='VALID_FIXED_TEMPORAL_REFERENCE',protocol=protocol,case_spec=runner.spec,
            solver_statistics=dict(result.solver_statistics),linear_counts=counts,new_training=0,stress_read=False,
            resolution_identity='USER_AUTHORIZED_TIME_REFINEMENT_20260916',
            old_frozen_resolution_name_not_a_new_qualification=True,created_utc=now()))
    except BaseException as exc:
        save_json(out/'failure.json',dict(status='REFERENCE_INCOMPLETE',error=repr(exc),counts=counts,created_utc=now()))
        raise
    finally:sla.spsolve,sla.splu,core.solve_electric_field,core.solve_phase_candidate=originals


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('protocol',choices=['original','shorter']);p.add_argument('--root',type=Path,default=RUN)
    a=p.parse_args();torch.set_num_threads(2);generate(a.protocol,a.root)
