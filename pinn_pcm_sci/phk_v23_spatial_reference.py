"""Bounded spatial-reference perturbation of fixed archived predictions.

This wrapper changes resolution only. The inherited numerical core, physical
object, nonlinear tolerances and no-rescue policy remain unchanged.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import scipy.sparse.linalg as sla
import torch

from . import phk_v21_benchmark as core
from .phk_benchmark import PhkResolution
from .phk_v21_benchmark import PhkV21CaseSpec, PhkV21OracleCase, write_phk_v21_result
from .phk_v22r_evaluator import _physical_contract
from .phk_v23_lf11 import ROOT, now, save_json
from .phk_v23_lf11_protocol import waveform
from .phk_v23_reference_sensitivity import reference_spec

RUN = ROOT / "outputs/runs/20260917-lf11-spatial-reference"
CONFIG = ROOT / "configs/phk_v23/lf11_spatial_reference_sprint.json"


class SpatialOracle(PhkV21OracleCase):
    def __init__(self, protocol: str, output: Path, config: dict):
        self.spec = reference_spec(protocol)
        self.spec["case_id"] = "lf11-spatial-reference-" + protocol
        self.spec["reference"] = config["reference"].copy()
        self.spec["changed_physics"] = "none; spatial reference only"
        self.output, self.last_step = output, -1
        self.solve_counts = {"electric": 0, "thermal": 0, "phase": 0}
        physical = _physical_contract()
        r = config["reference"]
        resolution = PhkResolution(
            name="LF11_SPATIAL_REFERENCE_" + protocol.upper(),
            nx=r["nx"], nz=r["nz"], dt=r["dt"], time_end=r["time_end"],
            save_every=r["save_every"], evidence_identity="PHK_V21_FROZEN_Q_RESOLUTION",
        )
        case = replace(PhkV21CaseSpec.nominal(physical),
                       period=self.spec["pulse_starts"][1], case_id=self.spec["case_id"])
        # Reuse structural validation, then retain this experiment's own identity.
        super().__init__(physical=physical, case=case, resolution=resolution)
        self.resolution = replace(resolution,
            evidence_identity="USER_AUTHORIZED_SPATIAL_REFERENCE_20260917")

    def waveform(self, value):
        step = round(value / self.resolution.dt)
        if step % 100 == 0 and step != self.last_step:
            self.last_step = step
            record = dict(step_entered=step, linear_solves=dict(self.solve_counts),
                          created_utc=now())
            save_json(self.output / "progress.json", record)
            print(json.dumps(dict(case=self.spec["case_id"], **record)), flush=True)
        return float(waveform(torch.tensor(value, dtype=torch.float64), self.spec))


def generate(protocol: str, root: Path = RUN):
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if config.get("execution_authorized") is not True:
        raise RuntimeError("Spatial-reference execution awaits explicit approval; no solve started")
    if protocol not in config["protocols"]:
        raise ValueError("not a frozen protocol")
    out = root / "reference" / protocol
    out.mkdir(parents=True, exist_ok=False)
    runner = SpatialOracle(protocol, out, config)
    counts = runner.solve_counts
    label = ["phase"]
    limit = config["per_trajectory_linear_solve_cap"]
    originals = (sla.spsolve, sla.splu, core.solve_electric_field, core.solve_phase_candidate)

    def consume(kind):
        if sum(counts.values()) >= limit:
            raise RuntimeError("frozen spatial-reference linear-solve budget exhausted")
        counts[kind] += 1

    def direct(*args, **kwargs):
        consume(label[0])
        return originals[0](*args, **kwargs)

    class ThermalFactor:
        def __init__(self, factor):
            self.factor = factor

        def solve(self, *args, **kwargs):
            consume("thermal")
            return self.factor.solve(*args, **kwargs)

    def factor(*args, **kwargs):
        return ThermalFactor(originals[1](*args, **kwargs))

    def electric(*args, **kwargs):
        previous, label[0] = label[0], "electric"
        try:
            return originals[2](*args, **kwargs)
        finally:
            label[0] = previous

    def phase(*args, **kwargs):
        previous, label[0] = label[0], "phase"
        try:
            return originals[3](*args, **kwargs)
        finally:
            label[0] = previous

    save_json(out / "intent.json", dict(status="AUTHORIZED_STARTED", config=config,
        protocol=protocol, case_spec=runner.spec, inherited_algorithms=True,
        neural_inputs_received=False, created_utc=now()))
    try:
        sla.spsolve, sla.splu = direct, factor
        core.solve_electric_field, core.solve_phase_candidate = electric, phase
        result = runner.solve()
        if result.solver_statistics["time_steps_total"] != config["reference"]["main_steps"]:
            raise AssertionError("unexpected main step count")
        if len(result.time) != 1001:
            raise AssertionError("unexpected saved time grid")
        for key, count in counts.items():
            if result.solver_statistics[key + "_linear_solves_total"] != count:
                raise AssertionError((key, count, result.solver_statistics))
        write_phk_v21_result(out / "result.npz", result)
        save_json(out / "terminal.json", dict(status="VALID_FIXED_SPATIAL_REFERENCE",
            protocol=protocol, case_spec=runner.spec, solver_statistics=dict(result.solver_statistics),
            linear_counts=counts, numerical_checks=dict(
                phase_range=[float(result.phase.min()), float(result.phase.max())],
                max_thermal_residual=float(np.max(result.thermal_residual_history)),
                max_phase_residual=float(np.max(result.phase_residual_history)),
                max_current_balance=float(np.max(result.current_balance_history))),
            output_clipping_allowed=False, stress_read=False, new_training=0,
            created_utc=now()))
    except BaseException as exc:
        save_json(out / "failure.json", dict(status="REFERENCE_INCOMPLETE_NO_RESCUE",
            error=repr(exc), counts=counts, created_utc=now()))
        raise
    finally:
        sla.spsolve, sla.splu, core.solve_electric_field, core.solve_phase_candidate = originals


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("protocol", choices=["original", "shorter"])
    parser.add_argument("--root", type=Path, default=RUN)
    args = parser.parse_args()
    torch.set_num_threads(2)
    generate(args.protocol, args.root)
