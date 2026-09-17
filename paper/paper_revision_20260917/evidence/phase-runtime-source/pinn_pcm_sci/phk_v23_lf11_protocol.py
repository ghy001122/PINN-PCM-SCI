"""One finite-pulse case specification shared by V32 generation and learning."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import numpy as np
import torch
from .phk_v22r_pinn import PhkV22RPhysics


CASE = dict(
    schema_id="lf11-finite-pulse-case-v1", case_id="lf11-history-gap-1p01",
    pulse_starts=[0.0, 1.01], amplitude=0.72, rise_end=0.05,
    hold_end=0.27, fall_end=0.35, time_end=2.5,
    recovery_cycles=[[0.0, 1.01], [1.01, 2.02]], tail=[2.02, 2.5],
    windows=[[0.0, 0.35], [0.35, 1.01], [1.01, 1.36], [1.36, 2.5]],
    window_masses=[0.14, 0.264, 0.14, 0.456],
    support=dict(nx=80, nz=40, dt=0.0025, save_every=2, main_steps=1000),
    reference=dict(nx=160, nz=80, dt=0.000625, save_every=4, main_steps=4000),
    sampling_rule="indices 0,4,8,... plus last on each support axis",
    changed_physics="second pulse start only; finite two-pulse experiment",
)


def validate_case(spec):
    if spec != CASE:
        raise ValueError("case differs from the explicitly authorized finite-pulse case")
    lengths = np.diff(np.asarray(spec['windows']), axis=1).ravel()
    np.testing.assert_allclose(lengths/spec['time_end'], spec['window_masses'], atol=1e-15)


def waveform(time, spec):
    """Exactly two trapezoids; no modulo continuation into the final tail."""
    result = torch.zeros_like(time)
    for start in spec['pulse_starts']:
        elapsed = time-start
        up, hold, down = spec['rise_end'], spec['hold_end'], spec['fall_end']
        unit = torch.where((elapsed >= 0) & (elapsed < up), elapsed/up,
            torch.where((elapsed >= up) & (elapsed < hold), torch.ones_like(time),
            torch.where((elapsed >= hold) & (elapsed < down),
                        (down-elapsed)/(down-hold), torch.zeros_like(time))))
        result = result + spec['amplitude']*unit
    return torch.where((time >= 0) & (time < spec['time_end']), result, torch.zeros_like(time))


@dataclass(frozen=True)
class FinitePulsePhysics(PhkV22RPhysics):
    pulse_starts: tuple[float, ...] = (0.0, 1.01)

    def waveform(self, time):
        return waveform(time, dict(pulse_starts=self.pulse_starts,
            amplitude=self.waveform_amplitude, rise_end=self.ramp_up_end,
            hold_end=self.hold_end, fall_end=self.ramp_down_end, time_end=self.time_end))


def case_physics(base, spec):
    validate_case(spec)
    values = asdict(base)
    values.update(period=spec['pulse_starts'][1], time_end=spec['time_end'])
    for key, expected in [('waveform_amplitude', spec['amplitude']),
                          ('ramp_up_end', spec['rise_end']), ('hold_end', spec['hold_end']),
                          ('ramp_down_end', spec['fall_end'])]:
        if values[key] != expected:
            raise ValueError('inherited pulse shape differs: '+key)
    return FinitePulsePhysics(**values, pulse_starts=tuple(spec['pulse_starts']))


def inference_times(spec):
    validate_case(spec)
    return np.linspace(0.0, spec['time_end'], 1001)


def powered_count(spec):
    return int(torch.count_nonzero(waveform(torch.tensor(inference_times(spec), dtype=torch.float64), spec)))
