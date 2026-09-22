"""Bounded, time-grouped D_E/P_E experiment; sparse observations only.

No reference module is imported here. A fixed physical pool and the complete
observation integral define each L-BFGS objective. Each time group's losses are
aggregated before its single backward call through the electrical solve.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import platform
import time
import traceback
import numpy as np
import scipy
import torch

from .phk_v23_lf11 import ROOT, SparseData, save_json, digest, now
from .phk_v23_lf11_followup_fit import fit_model
from .phk_v23_lf11_v_continue import continued_lbfgs
from .phk_v23_lf11_electric_layer import ElectricalLayer
from .phk_v23_lf11_elimination_physics import (
    grid_for, fields, coordinates, thermal_phase_residual, boundary_loss, initial_loss,
)

RUN = ROOT/'outputs/runs/20260913-lf11-electrical-elimination'
CONFIG = ROOT/'configs/phk_v23/lf11_elimination_sprint.json'


class ObservationTimes:
    def __init__(self, data, grid, physics, config, device):
        self.data, self.config, self.device = data, config, device
        self.times = data.arrays['time']
        self.nt = len(self.times)
        self.ns = len(data.coordinates)//self.nt
        self.q = data.coordinates.reshape(self.nt, self.ns, 3)
        self.target = data.targets.reshape(self.nt, self.ns, 3)
        self.global_weight = (data.prob/data.prob.sum()).reshape(self.nt, self.ns)
        phase = data.prob*(data.coordinates[:, 2] > physics.time_start)
        phase /= phase.sum()
        if data.has_interface:
            phase = .5*phase+.5*data.endpoint_prob/data.endpoint_prob.sum()
        self.phase_weight = phase.reshape(self.nt, self.ns)
        self.proposal = .5*(self.global_weight.sum(1)+self.phase_weight.sum(1))
        self.proposal /= self.proposal.sum()
        ix = np.rint((self.q[0, :, 0]-grid.x_min)/grid.dx-.5).astype(int)
        iz = np.rint((self.q[0, :, 1]-grid.z_min)/grid.dz-.5).astype(int)
        if np.any(ix < 0) or np.any(ix >= grid.nx) or np.any(iz < 0) or np.any(iz >= grid.nz):
            raise ValueError('sparse coordinates outside training grid')
        self.cell = iz*grid.nx+ix
        np.testing.assert_allclose(self.q[0, :, :2], np.column_stack([grid.cell_x[self.cell], grid.cell_z[self.cell]]), atol=1e-12, rtol=0)

    def tensor(self, value):
        return torch.as_tensor(value, dtype=torch.float64, device=self.device)

    def groups(self, rng=None, count=4):
        if rng is None:
            return {float(t): (i, 1.) for i, t in enumerate(self.times)}
        indices, counts = np.unique(rng.choice(self.nt, count, p=self.proposal), return_counts=True)
        return {float(self.times[i]): (int(i), float(n/(count*self.proposal[i]))) for i, n in zip(indices, counts)}

    def loss(self, model, group, voltage, role):
        i, coefficient = group
        q, target = self.tensor(self.q[i]), self.tensor(self.target[i])
        f = fields(model, q, potential=role == 'P_F')
        v = f['potential'] if role == 'P_F' else voltage[torch.as_tensor(self.cell, device=self.device)]
        initial = model.physics.initial_phase(q).clamp(self.config['phase_logit_epsilon'], 1-self.config['phase_logit_epsilon']).reshape(-1)
        desired = torch.logit(target[:, 2].clamp(self.config['phase_logit_epsilon'], 1-self.config['phase_logit_epsilon']))-torch.logit(initial)
        weight, pw = self.tensor(self.global_weight[i]), self.tensor(self.phase_weight[i])
        pieces = {'obs_V': coefficient*torch.dot(weight, ((v-target[:, 0])/model.physics.waveform_amplitude).square()),
                  'obs_T': coefficient*torch.dot(weight, ((f['temperature']-target[:, 1])/model.physics.theta_transition).square()),
                  'obs_phase': coefficient*torch.dot(pw, ((f['delta_logit']-desired)/self.config['phase_logit_divisor']).square())}
        return sum(pieces.values())/3, pieces


class TimeSampler:
    def __init__(self, config, physics, grid, seed):
        self.c, self.p, self.grid = config, physics, grid
        self.rng = np.random.default_rng(seed)

    def boundaries(self, when, count):
        p, r = self.p, self.rng
        sides = {}
        for side in ('left', 'right', 'bottom', 'top'):
            q = np.column_stack([r.uniform(p.x_min, p.x_max, count), r.uniform(p.z_min, p.z_max, count), np.full(count, when)])
            if side == 'left': q[:, 0] = p.x_min
            if side == 'right': q[:, 0] = p.x_max
            if side == 'top': q[:, 1] = p.z_max
            if side == 'bottom':
                q[:, 1] = p.z_min
                q[:count//2, 0] = r.uniform(-p.heater_half_width, p.heater_half_width, count//2)
                u = r.random(count-count//2)
                q[count//2:, 0] = np.where(u < .5,
                    p.x_min+2*u*(-p.heater_half_width-p.x_min),
                    p.heater_half_width+2*(u-.5)*(p.x_max-p.heater_half_width))
            sides[side] = q
        return sides

    def sample(self, fixed=False):
        result = {}
        per_window = self.c['fixed_times_per_window'] if fixed else 1
        ncell = self.c['fixed_physics_cells'] if fixed else self.c['adam_physics_cells']
        for (lo, hi), mass, nbc in zip(self.c['windows'], self.c['window_masses'], self.c['boundary_counts_per_side']):
            # Stratified time samples for the fixed integral; uniform within each stratum.
            ts = lo+(hi-lo)*(np.arange(per_window)+self.rng.random(per_window))/per_window
            for t in ts:
                result[float(t)] = {'mass': mass/per_window,
                    'cells': self.rng.choice(self.grid.cell_count, ncell, replace=False),
                    'sides': self.boundaries(t, nbc)}
        p = self.p
        initial = self.rng.uniform([p.x_min, p.z_min], [p.x_max, p.z_max], (self.c['initial_points'], 2))
        return {'times': result, 'initial': initial}


def serialize_pool(pool):
    return {'initial': pool['initial'].tolist(), 'times': [
        {'time': t, 'mass': v['mass'], 'cells': v['cells'].tolist(),
         'sides': {k: q.tolist() for k, q in v['sides'].items()}} for t, v in pool['times'].items()]}


def deserialize_pool(value):
    return {'initial': np.asarray(value['initial']), 'times': {
        float(v['time']): {'mass': v['mass'], 'cells': np.asarray(v['cells'], dtype=np.int64),
                          'sides': {k: np.asarray(q) for k, q in v['sides'].items()}}
        for v in value['times']}}


class Experiment:
    observation_type = ObservationTimes

    def __init__(self, config, state, data, device='cpu', role='D_E'):
        self.c, self.role, self.device = config, role, device
        self.model = fit_model(config, state, adapter=True).to(device)
        for p in self.model.heads['potential'].parameters():
            p.requires_grad_(role == 'P_F')
        self.parameters = [p for p in self.model.parameters() if p.requires_grad]
        self.grid = grid_for(self.model.physics, *config['grid'])
        self.layer = ElectricalLayer(self.grid, self.model.physics.heater_width_fraction, config['linear_tolerance'])
        self.obs = self.observation_type(data, self.grid, self.model.physics, config, device)
        self.calls = {'complete_objective_gradient_evaluations': 0, 'adam_objective_gradient_evaluations': 0,
                      'audit_objective_evaluations': 0, 'audit_objective_gradient_evaluations': 0, 'optimizer_updates': 0}

    def electric(self, t, needed):
        n = self.grid.cell_count
        u = float(self.model.physics.waveform(torch.tensor(t, dtype=torch.float64, device=self.device)))
        if not needed or u == 0.:
            if needed:
                self.layer.backend.counts.forward_queries += 1
                self.layer.backend.counts.zero_drive_queries += 1
            zero = torch.zeros(n, dtype=torch.float64, device=self.device)
            return zero, zero, None
        q = coordinates(self.grid, t, device=self.device)
        f = fields(self.model, q, potential=self.role == 'P_F')
        sigma = self.model.physics.conductivity(f['temperature'], f['phase'])
        if self.role == 'P_F':
            v = f['potential']
            return v, self.layer.deposition(v, sigma, u)['density'], self.layer.balance(v, sigma, u)
        v, heat = self.layer(sigma, u)
        return v, heat, None

    def objective(self, groups, pool, calibration, lam, *, backward=False, counter='audit'):
        if backward:
            key = {'complete': 'complete_objective_gradient_evaluations',
                   'adam': 'adam_objective_gradient_evaluations'}.get(counter, 'audit_objective_gradient_evaluations')
            self.calls[key] += 1
        else:
            self.calls['audit_objective_evaluations'] += 1
        a, b = max(calibration['aE'], 1e-12), max(calibration['bE'], 1e-12)
        totals = {k: 0. for k in ('observation', 'obs_V', 'obs_T', 'obs_phase', 'boundary', 'initial', 'thermal', 'phase', 'electric', 'objective')}
        times = sorted(set(groups) | set(pool['times']))
        for t in times:
            obs_group, phys = groups.get(t), pool['times'].get(t)
            interior = phys is not None and self.role in {'P_E', 'P_F'}
            v, heat, electric = self.electric(t, obs_group is not None or interior)
            loss = torch.zeros((), dtype=torch.float64, device=self.device)
            if obs_group is not None:
                observed, pieces = self.obs.loss(self.model, obs_group, v, self.role)
                loss = loss+observed/a
                totals['observation'] += float(observed.detach())
                for k, value in pieces.items(): totals[k] += float(value.detach())
            if phys is not None:
                boundary = phys['mass']*boundary_loss(self.model, phys['sides'])
                loss = loss+lam*5*boundary/b
                totals['boundary'] += float(boundary.detach())
                if interior:
                    r = thermal_phase_residual(self.model, self.grid, t, phys['cells'], heat)
                    for k in ('thermal', 'phase'):
                        value = phys['mass']*(r[k]/self.c['pde_scales'][k]).square().mean()
                        loss = loss+lam*value/(3*b)
                        totals[k] += float(value.detach())
                    if self.role == 'P_F' and electric is not None:
                        value = phys['mass']*(electric[torch.as_tensor(phys['cells'], device=self.device)]/self.c['pde_scales']['electric']).square().mean()
                        loss = loss+lam*value/(3*b)
                        totals['electric'] += float(value.detach())
            if not torch.isfinite(loss):
                raise FloatingPointError(f'nonfinite {self.role} objective at t={t}')
            if backward and loss.requires_grad:
                loss.backward()
            totals['objective'] += float(loss.detach())
        ic = initial_loss(self.model, pool['initial'])
        loss = lam*ic/b
        if backward: loss.backward()
        totals['initial'] = float(ic.detach())
        totals['objective'] += float(loss.detach())
        return torch.tensor(totals['objective'], dtype=torch.float64, device=self.device), totals

    def statistics(self):
        return {'objectives': dict(self.calls), 'electrical': self.layer.backend.snapshot()}


def load_inputs(config, device):
    state = torch.load(ROOT/config['parent'], map_location='cpu', weights_only=False)
    if not state.get('temperature_adapter'):
        raise ValueError('specified parent lacks the retained T adapter')
    data = SparseData(ROOT/config['sparse'])
    return state['model_state_dict'], data


def prepare(root, config, device):
    """Freeze pools and calibrate once at E0; no optimizer is constructed."""
    root.mkdir(parents=True, exist_ok=True)
    if (root/'calibration.json').exists():
        raise FileExistsError('calibration exists; reuse the frozen result')
    state, data = load_inputs(config, device)
    exp = Experiment(config, state, data, device, 'P_E')
    pools = {}
    for label, seed in [('calibration', config['calibration_seed']), ('lbfgs', config['lbfgs_pool_seed']), ('audit', config['audit_pool_seed'])]:
        pools[label] = TimeSampler(config, exp.model.physics, exp.grid, seed).sample(fixed=True)
        save_json(root/f'{label}-pool.json', serialize_pool(pools[label]))
    _, values = exp.objective(exp.obs.groups(), pools['calibration'], {'aE': 1., 'bE': 1.}, 1.)
    cal = {'aE': values['observation'], 'bE': (values['thermal']+values['phase'])/3+5*values['boundary']+values['initial'],
           'components': values, 'status': 'FROZEN_ONCE_AT_E0', 'reference_read': False,
           'statistics': exp.statistics()}
    if not np.isfinite([cal['aE'], cal['bE']]).all():
        raise FloatingPointError('nonfinite E0 calibration')
    save_json(root/'calibration.json', cal)
    save_json(root/'frozen-config.json', config)
    save_json(root/'input-manifest.json', {'parent': config['parent'], 'parent_sha256': digest(ROOT/config['parent']),
        'sparse': config['sparse'], 'sparse_sha256': digest(ROOT/config['sparse']), 'source_commit': config['source_commit'],
        'runtime': {'torch': torch.__version__, 'scipy': scipy.__version__, 'python': platform.python_version()},
        'reference_read': False, 'created_utc': now()})
    torch.save({'model_state_dict': state, 'temperature_adapter': True, 'role': 'E0', 'updates': 0,
                'config': config, 'calibration': cal}, root/'parent.pt')
    print(json.dumps({'event': 'E0_CALIBRATED', **cal}), flush=True)
    return cal


def save_checkpoint(path, exp, optimizer, config, cal, updates, **extra):
    torch.save({'schema_id': 'lf11-elimination-checkpoint-v1', 'model_state_dict': exp.model.state_dict(),
                'temperature_adapter': True, 'role': exp.role, 'updates': updates,
                'optimizer_state_dict': optimizer.state_dict(), 'config': config, 'calibration': cal,
                'statistics': exp.statistics(), 'reference_read': False, **extra}, path)


def train_role(root, role, config, device, *, output_role=None, experiment_type=Experiment, data_type=SparseData):
    if role not in {'D_E', 'P_E', 'P_F'}:
        raise ValueError('invalid training role')
    if role == 'P_F':
        decision = json.loads((root/'evaluation/conditional-decision.json').read_text())
        if decision.get('run_P_F') is not True:
            raise ValueError('P_F scientific prerequisite not satisfied')
    folder = root/(output_role or role)
    folder.mkdir(exist_ok=False)
    frozen = json.loads((root/'frozen-config.json').read_text())
    if frozen != config:
        raise ValueError('configuration changed after E0 calibration')
    cal = json.loads((root/'calibration.json').read_text())
    parent = torch.load(root/'parent.pt', map_location='cpu', weights_only=False)
    data = data_type(ROOT/config['sparse'])
    exp = experiment_type(config, parent['model_state_dict'], data, device, role)
    sampler = TimeSampler(config, exp.model.physics, exp.grid, config['sampling_seed'])
    obs_rng = np.random.default_rng(config['observation_seed'])
    pool = deserialize_pool(json.loads((root/'lbfgs-pool.json').read_text()))
    optimizer = torch.optim.Adam(exp.parameters, lr=config['branch_lr'], betas=tuple(config['betas']), eps=config['eps'])
    completed = 0
    start = time.perf_counter()
    try:
        with (folder/'adam-telemetry.jsonl').open('x', encoding='utf-8') as log:
            for step in range(1, config['branch_updates']+1):
                groups = exp.obs.groups(obs_rng, config['adam_observation_times'])
                batch = sampler.sample()
                optimizer.zero_grad(set_to_none=True)
                lam = config['lambda_max']*min(step/config['lambda_ramp'], 1.)
                _, components = exp.objective(groups, batch, cal, lam, backward=True, counter='adam')
                norm = torch.nn.utils.clip_grad_norm_(exp.parameters, config['gradient_clip'], error_if_nonfinite=True)
                optimizer.step()
                completed = step
                exp.calls['optimizer_updates'] = step
                if not all(torch.isfinite(p).all() for p in exp.parameters):
                    raise FloatingPointError('nonfinite accepted Adam parameters')
                if step == 1 or step % 50 == 0:
                    record = {'step': step, 'gradient_norm': float(norm), **components, 'statistics': exp.statistics()}
                    log.write(json.dumps(record, allow_nan=False)+'\n'); log.flush()
                    print(json.dumps({'role': role, 'adam': step, 'objective': components['objective']}), flush=True)
                if step in config['checkpoint_steps']:
                    save_checkpoint(folder/f'adam-{step}.pt', exp, optimizer, config, cal, step,
                                    optimizer_phase='Adam', observation_rng_state=obs_rng.bit_generator.state,
                                    physics_rng_state=sampler.rng.bit_generator.state)
        with (folder/'lbfgs-telemetry.jsonl').open('x', encoding='utf-8') as log:
            def log_step(record):
                record['statistics'] = exp.statistics()
                log.write(json.dumps(record, allow_nan=False)+'\n'); log.flush()
                if record['accepted_steps'] == 1 or record['accepted_steps'] % 10 == 0:
                    print(json.dumps({'role': role, 'lbfgs': record['evaluations'], 'loss': record['loss']}), flush=True)
            result, optimizer = continued_lbfgs(exp.parameters,
                lambda: exp.objective(exp.obs.groups(), pool, cal, config['lambda_max'], backward=True, counter='complete')[0],
                config['lbfgs_evaluations'], log_step)
        save_checkpoint(folder/'checkpoint.pt', exp, optimizer, config, cal, completed,
                        optimizer_phase='L-BFGS', lbfgs_result=result)
        terminal = {'status': 'VALID_FIXED_ENDPOINT', 'role': role, 'adam_updates': completed,
                    'lbfgs': result, 'statistics': exp.statistics(), 'reference_read': False,
                    'elapsed_seconds_internal': time.perf_counter()-start, 'device': device}
        save_json(folder/'terminal.json', terminal)
        print(json.dumps({'role': role, 'status': terminal['status'], 'adam_updates': completed,
                          'full_evaluations': result['evaluations']}), flush=True)
    except Exception as error:
        save_json(folder/'failure.json', {'status': 'EXECUTION_FAILED', 'role': role, 'completed_updates': completed,
            'error': str(error), 'traceback': traceback.format_exc(), 'statistics': exp.statistics(),
            'reference_read': False})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'train'])
    parser.add_argument('--root', type=Path, default=RUN)
    parser.add_argument('--config', type=Path, default=CONFIG)
    parser.add_argument('--device', default='cpu')
    parser.add_argument('--role', choices=['D_E', 'P_E', 'P_F'])
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8'))
    torch.set_num_threads(config['cpu_threads'])
    if args.action == 'prepare': prepare(args.root, config, args.device)
    elif args.role: train_role(args.root, args.role, config, args.device)
    else: parser.error('--role is required for training')


if __name__ == '__main__':
    main()
