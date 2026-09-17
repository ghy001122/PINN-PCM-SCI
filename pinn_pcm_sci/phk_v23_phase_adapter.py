"""Authorized phase-head residual development on fixed V32 E parents.

All existing consumers see the same composed phase head. The gate's weights
are frozen; its coordinate derivatives remain in the autograd graph.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import shutil
import traceback
import numpy as np
import torch
from torch import nn
from .phk_v23_lf11 import ROOT, SparseData, save_json, now
from .phk_v23_lf11_followup_fit import fit_model
from .phk_v23_lf11_elimination import Experiment, deserialize_pool, train_role
from .phk_v23_lf11_elimination_physics import fields, coordinates, grid_for, thermal_phase_residual
from .phk_v23_lf11_electric_layer import ElectricalLayer
from .phk_v23_lf11_elimination_predict import infer_time
from .phk_v23_lf11_protocol import inference_times, powered_count

RUN = ROOT/'outputs/runs/20260916-lf11-phase-adapter-reference'
CONFIG = ROOT/'configs/phk_v23/lf11_phase_adapter_sprint.json'
ROLES = ('E_C', 'E_R', 'E_I')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


class PhaseResidualHead(nn.Module):
    def __init__(self, base, physics, startup_time, latent_scale, seed, gated, cg):
        super().__init__()
        self.base = base
        self.physics, self.startup_time, self.latent_scale = physics, startup_time, latent_scale
        self.gated = gated
        self.frozen_parent = copy.deepcopy(base) if gated else None
        if self.frozen_parent is not None:
            self.frozen_parent.requires_grad_(False)
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(seed)
            self.residual = nn.Sequential(nn.Linear(3, 32), nn.Tanh(),
                                          nn.Linear(32, 32), nn.Tanh(), nn.Linear(32, 1)).double()
        nn.init.zeros_(self.residual[-1].weight)
        nn.init.zeros_(self.residual[-1].bias)
        self.register_buffer('cg', torch.tensor(float(cg), dtype=torch.float64))

    def gate(self, normalized):
        if self.frozen_parent is None:
            return torch.ones_like(normalized[:, :1])
        p = self.physics
        lower = normalized.new_tensor([p.x_min, p.z_min, p.time_start])
        upper = normalized.new_tensor([p.x_max, p.z_max, p.time_end])
        q = lower + .5*(normalized+1)*(upper-lower)
        initial = p.initial_phase(q).clamp(1e-8, 1-1e-8)
        startup = 1-torch.exp(-(q[:, 2:3]-p.time_start)/self.startup_time)
        parent_phase = torch.sigmoid(torch.logit(initial)+self.latent_scale*startup*self.frozen_parent(normalized))
        return (.25+.75*4*parent_phase*(1-parent_phase))/self.cg

    def forward(self, normalized):
        return self.base(normalized)+self.gate(normalized)*self.residual(normalized)


def install(model, role, cfg):
    if role not in ROLES:
        raise ValueError(role)
    if role != 'E_C':
        model.heads['phase'] = PhaseResidualHead(model.heads['phase'], model.physics,
            model.startup_time, model.phase_latent_scale, 916000+cfg['seed'],
            role == 'E_I', cfg['phase_gate_cg'])
    for p in model.heads['potential'].parameters():
        p.requires_grad_(False)
    return model


def load_model(cfg, state, role, device):
    model = install(fit_model(cfg, adapter=True), role, cfg)
    model.load_state_dict(state)
    return model.to(device)


class AdapterExperiment(Experiment):
    def __init__(self, cfg, state, data, device, role, adapter_role):
        super().__init__(cfg, state, data, device, role)
        # Install after loading the exact parent; do not load an old model over T.
        self.model = install(self.model, adapter_role, cfg).to(device)
        self.parameters = [p for p in self.model.parameters() if p.requires_grad]
        self.adapter_role = adapter_role

    def electric(self, t, needed):
        u = float(self.model.physics.waveform(torch.tensor(t, dtype=torch.float64, device=self.device)))
        counts = self.layer.backend.counts
        if needed and u != 0. and (counts.forward_solves >= self.c['per_E_forward_limit'] or
                                    counts.adjoint_solves >= self.c['per_E_adjoint_limit']):
            raise RuntimeError('phase-adapter electrical budget reached before next solve')
        return super().electric(t, needed)


def prepare_seed(root, cfg, seed):
    old = ROOT/cfg['parent_root']/f'seed-{seed}'
    folder = root/f'seed-{seed}'
    folder.mkdir(parents=True, exist_ok=False)
    c = read(old/'frozen-config.json')
    c.update({k: cfg[k] for k in ('branch_updates', 'lbfgs_evaluations', 'lambda_ramp',
        'checkpoint_steps', 'roles', 'per_E_forward_limit', 'per_E_adjoint_limit')})
    c.update(schema_id=cfg['schema_id'], seed=seed, adapter=cfg['adapter'], adapter_seed=916000+seed,
             display_rule=cfg['display_rule'], parent=(old/'E/checkpoint.pt').relative_to(ROOT).as_posix(),
             source_commit=cfg['source_commit'], lambda_max=.1)
    state = torch.load(old/'E/checkpoint.pt', map_location='cpu', weights_only=False)
    model = fit_model(c, state['model_state_dict'], adapter=True)
    pool = deserialize_pool(read(old/'calibration-pool.json'))
    grid = grid_for(model.physics, *c['grid'])
    square = 0.; mass = 0.; gate_min = 1.; gate_max = 0.
    with torch.no_grad():
        for t, item in pool['times'].items():
            q = coordinates(grid, t, cells=item['cells'])
            ph = fields(model, q)['phase']
            gate = .25+.75*4*ph*(1-ph)
            square += item['mass']*float(gate.square().mean()); mass += item['mass']
            gate_min = min(gate_min, float(gate.min())); gate_max = max(gate_max, float(gate.max()))
    if abs(mass-1.) > 1e-12:
        raise ValueError('gate calibration is not the inherited uniform time integral')
    c['phase_gate_cg'] = float(np.sqrt(square))
    obs_times = np.load(ROOT/c['sparse'], allow_pickle=False)['time']
    fixed = deserialize_pool(read(old/'lbfgs-pool.json'))
    n_obs = int(torch.count_nonzero(model.physics.waveform(torch.tensor(obs_times))))
    n_phys = len(fixed['times'])
    if len(obs_times) != 126 or n_obs > 34 or n_phys != 32:
        raise ValueError(('unexpected inherited objective time counts', len(obs_times), n_obs, n_phys))
    if 600*8+100*(n_obs+n_phys) > 11400:
        raise ValueError('objective schedule exceeds declared upper bound')
    for label in ('calibration', 'lbfgs', 'audit'):
        shutil.copyfile(old/f'{label}-pool.json', folder/f'{label}-pool.json')
    shutil.copyfile(old/'calibration.json', folder/'calibration.json')
    shutil.copyfile(old/'E/checkpoint.pt', folder/'parent.pt')
    save_json(folder/'frozen-config.json', c)
    save_json(folder/'gate-calibration.json', dict(c_g=c['phase_gate_cg'], gate_range=[gate_min, gate_max],
        measure='inherited calibration-pool uniform time masses and sampled equal-volume cells',
        adapter_seed=c['adapter_seed'], fixed_observation_times=len(obs_times),
        powered_observation_times=n_obs, fixed_physics_times=n_phys, reference_read=False,
        parent_role='V32 short-gap final E', derivative_freezing='weights only; coordinates remain differentiable'))
    return c


def predict(folder, role, cfg, device):
    state = torch.load(folder/role/'checkpoint.pt', map_location='cpu', weights_only=False)
    model = load_model(cfg, state['model_state_dict'], role, device)
    grid = grid_for(model.physics, *cfg['inference_grid'])
    layer = ElectricalLayer(grid, model.physics.heater_width_fraction, cfg['linear_tolerance'])
    times = inference_times(cfg['case_spec'])
    arrays = {k: np.empty((len(times), grid.cell_count)) for k in ('potential','temperature','phase','joule_density')}
    traces = {}
    for i,t in enumerate(times):
        if layer.backend.counts.forward_solves >= 278 and float(model.physics.waveform(torch.tensor(t))) != 0:
            raise RuntimeError('projection cap before next solve')
        f,d = infer_time(model, layer, t, device, 'P_E')
        for k in arrays: arrays[k][i] = f[k]
        for k,v in d.items(): traces.setdefault(k, []).append(v)
        if i % 200 == 0: print(json.dumps(dict(seed=cfg['seed'], role=role, prediction_index=i)), flush=True)
    out = folder/role/'projected'; out.mkdir(exist_ok=False)
    np.savez_compressed(out/'prediction.npz', x=grid.x_centers,z=grid.z_centers,time=times,**arrays)
    np.savez_compressed(out/'own-readout.npz', time=times,**{k:np.asarray(v) for k,v in traces.items()})
    save_json(out/'prediction.json',dict(status='FIXED_OWN_PREDICTION',role=role,readout='projected',
        electrical_counts=layer.backend.snapshot(),reference_read=False,times=len(times),case_spec=cfg['case_spec']))
    # Display gate and state at times fixed before training; no true field used.
    display = {}
    with torch.no_grad():
        for index,t in enumerate(cfg['display_rule']['times']):
            q = coordinates(grid,t,device=device)
            display[f'phase_{index}'] = fields(model,q)['phase'].cpu().numpy()
            if role=='E_I':
                display[f'gate_{index}'] = model.heads['phase'].gate(model.physics.normalize(q)).ravel().cpu().numpy()
    np.savez_compressed(out/'fixed-display.npz',time=cfg['display_rule']['times'],x=grid.x_centers,z=grid.z_centers,**display)


def check_prepared(root, device):
    records=[]
    for seed in (29,43):
        folder=root/f'seed-{seed}';cfg=read(folder/'frozen-config.json')
        state=torch.load(folder/'parent.pt',map_location='cpu',weights_only=False)
        data=SparseData(ROOT/cfg['sparse']);pool=deserialize_pool(read(folder/'calibration-pool.json'))
        t,item=next(iter(pool['times'].items()))
        small={'times':{t:dict(item,cells=item['cells'][:8])},'initial':pool['initial'][:8]}
        base=fit_model(cfg,state['model_state_dict'],adapter=True).to(device)
        q=coordinates(grid_for(base.physics),t,cells=item['cells'][:8],device=device)
        expected=fields(base,q,potential=True)
        initial_residuals=[]
        for role in ROLES:
            exp=AdapterExperiment(cfg,state['model_state_dict'],data,device,'P_E',role)
            got=fields(exp.model,q,potential=True)
            for k in expected:torch.testing.assert_close(expected[k],got[k],rtol=0,atol=0)
            if role!='E_C':initial_residuals.append(copy.deepcopy(exp.model.heads['phase'].residual.state_dict()))
            groups={float(exp.obs.times[8]):(8,1.)}
            exp.model.zero_grad(set_to_none=True)
            value,_=exp.objective(groups,small,read(folder/'calibration.json'),.1,backward=True)
            if not all(p.grad is None or torch.isfinite(p.grad).all() for p in exp.parameters):raise AssertionError('actual parent nonfinite gradient')
            records.append(dict(seed=seed,role=role,objective=float(value),trainable_parameters=sum(p.numel() for p in exp.parameters),
                total_parameters=sum(p.numel() for p in exp.model.parameters()),statistics=exp.statistics()))
        if not all(torch.equal(initial_residuals[0][k],initial_residuals[1][k]) for k in initial_residuals[0]):raise AssertionError('unequal adapter initial weights')
    counts={k:sum(r['statistics']['electrical'][k+'_solves'] for r in records) for k in ('forward','adjoint')}
    if any(v>600 for v in counts.values()):raise AssertionError('check budget')
    save_json(root/'actual-parent-interface-checks.json',dict(status='PASS',device=device,records=records,counts=counts,optimizer_updates=0,reference_read=False))


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RUN)
    p.add_argument('--config',type=Path,default=CONFIG);p.add_argument('--device',default='cuda:0')
    p.add_argument('--prepare-only',action='store_true')
    p.add_argument('--check-only',action='store_true')
    a=p.parse_args();cfg=read(a.config);torch.set_num_threads(cfg['cpu_threads'])
    a.root.mkdir(parents=True,exist_ok=True)
    if a.check_only:
        check_prepared(a.root,a.device);return
    failures=[]
    for seed in (29,43):
        folder=a.root/f'seed-{seed}'
        c=read(folder/'frozen-config.json') if folder.exists() else prepare_seed(a.root,cfg,seed)
        if a.prepare_only:continue
        for role in ROLES:
            if (folder/role).exists():raise FileExistsError('scientific arm exists; no implicit restart')
            try:
                train_role(folder,'P_E',c,a.device,output_role=role,
                    experiment_type=lambda cc,ss,dd,dev,rr:AdapterExperiment(cc,ss,dd,dev,rr,role))
                predict(folder,role,c,a.device)
            except Exception as exc:
                failures.append(dict(seed=seed,role=role,error=repr(exc)))
                save_json(folder/(role+'-execution-error.json'),dict(error=repr(exc),traceback=traceback.format_exc()))
                print(json.dumps(dict(seed=seed,role=role,status='ARM_INVALID_CONTINUE_OTHER_PREDECLARED_ARMS')),flush=True)
    if not a.prepare_only:
        save_json(a.root/'training-and-own-inference-complete.json',dict(completed=not failures,
            failures=failures,valid_roles=[r for r in ROLES],reference_read=False,created_utc=now()))
        if failures:raise RuntimeError('bounded campaign has missing endpoints; see individual failures')


if __name__=='__main__':main()
