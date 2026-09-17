"""LF11 sparse-observation, matched-boundary physics metric experiment.

Training opens only an extracted sparse bundle and known physical contracts.
Reference evaluation is a separate local module. No old model is an initializer.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import traceback

import numpy as np
import torch

from .phk_v22r_pinn import (
    PhkV22RModel, POTENTIAL_TRANSFORM_EXACT_TOP_RANGE_PRESERVING,
    interior_residuals, boundary_residuals, initial_residuals,
    normalized_residual_loss,
)
from .phk_v22r_training import (
    load_case_physics, PDE_SCALES, BOUNDARY_SCALES, INITIAL_SCALES,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs/phk_v23/lf11_sprint.json"
FIELDS = ("potential", "temperature", "phase")


def now():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def tensor(value, device="cpu"):
    return torch.as_tensor(value, dtype=torch.float64, device=device)


def build_model(config, device="cpu"):
    torch.manual_seed(config["seed"])
    physics, _, _ = load_case_physics()
    if "case_spec" in config:
        from .phk_v23_lf11_protocol import case_physics
        physics = case_physics(physics, config["case_spec"])
    return PhkV22RModel(
        physics=physics, arm="STRONG_RAW", hidden_width=config["width"],
        hidden_layers=config["layers"], phase_latent_scale=8.0,
        potential_output_transform=POTENTIAL_TRANSFORM_EXACT_TOP_RANGE_PRESERVING,
    ).to(device=device, dtype=torch.float64)


def axis_weights(axis, lower=None, upper=None):
    edges = np.concatenate(([axis[0] if lower is None else lower],
                            .5 * (axis[:-1] + axis[1:]),
                            [axis[-1] if upper is None else upper]))
    weights = np.diff(edges)
    if np.any(weights <= 0):
        raise ValueError("nonpositive quadrature weights")
    return weights / weights.sum()


def extract_sparse(source, output, config):
    """Record coordinate-only mask before selecting any field values."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if (output / "sparse.npz").exists():
        raise FileExistsError("sparse input already exists; reuse it")
    physics, _, _ = load_case_physics()
    if "case_spec" in config:
        from .phk_v23_lf11_protocol import case_physics
        physics = case_physics(physics, config["case_spec"])
    with np.load(source, allow_pickle=False) as f:
        xfull, zfull, times = np.unique(f["x"]), np.unique(f["z"]), f["time"]
        mask = [np.unique(np.r_[np.arange(0, len(a), 4), len(a)-1]) for a in (xfull, zfull, times)]
        xi, zi, ti = mask
        save_json(output / "observation_mask.json", {
            "status": "FROZEN_BEFORE_FIELD_SELECTION", "recorded_utc": now(),
            "source": config["medium"], "source_axes": [len(xfull), len(zfull), len(times)],
            "x_indices": xi.tolist(), "z_indices": zi.tolist(), "time_indices": ti.tolist(),
            "rule": "0,4,8,... plus last; unique; values never used for placement",
        })
        x, z, t = xfull[xi], zfull[zi], times[ti]
        xx, zz = np.meshgrid(xfull, zfull, indexing="xy")
        if not (np.array_equal(xx.ravel(), f["x"]) and np.array_equal(zz.ravel(), f["z"])):
            raise ValueError("unexpected medium grid ordering")
        selected = []
        for name in FIELDS:
            # The extractor may decompress a source field, but exports and uses
            # only the coordinate-frozen selected observations.
            values = f[name].reshape(len(times), len(zfull), len(xfull))
            selected.append(values[np.ix_(ti, zi, xi)].copy())
            del values
        values = np.stack(selected, axis=-1)
    tt, zz, xx = np.meshgrid(t, z, x, indexing="ij")
    coords = np.stack([xx, zz, tt], axis=-1).reshape(-1, 3)
    initial = physics.initial_phase(tensor(coords)).numpy().reshape(len(t), len(z), len(x))
    values[0, ..., :2] = 0.0
    values[0, ..., 2] = initial[0]
    probability = (axis_weights(t)[:, None, None] *
                   axis_weights(z, physics.z_min, physics.z_max)[None, :, None] *
                   axis_weights(x, physics.x_min, physics.x_max)[None, None, :])
    ph = values[..., 2]
    corners = [ph[dt:len(t)-1+dt, dz:len(z)-1+dz, dx:len(x)-1+dx]
               for dt in (0, 1) for dz in (0, 1) for dx in (0, 1)]
    straddles = (np.minimum.reduce(corners) < .5) & (np.maximum.reduce(corners) >= .5)
    it, iz, ix = np.where(straddles)
    lower = np.column_stack([x[ix], z[iz], t[it]])
    upper = np.column_stack([x[ix+1], z[iz+1], t[it+1]])
    volumes = np.prod(upper-lower, axis=1)
    endpoints = np.zeros(ph.shape, dtype=np.float64)
    for dt in (0, 1):
        for dz in (0, 1):
            for dx in (0, 1):
                np.add.at(endpoints, (it+dt, iz+dz, ix+dx), volumes / 8)
    endpoints[0] = 0
    if endpoints.sum() > 0:
        endpoints /= endpoints.sum()
    with (output / "sparse.npz").open("xb") as f:
        np.savez_compressed(f, x=x, z=z, time=t, coordinates=coords,
                            targets=values.reshape(-1, 3), global_probability=probability.ravel(),
                            interface_probability=endpoints.ravel(), cell_lower=lower,
                            cell_upper=upper, straddles=straddles.astype(np.uint8))
    record = {
        "schema_id": "lf11-sparse-observations-v1", "status": "SPARSE_ONLY_EXPORTED",
        "source_sha256": digest(source), "bundle_sha256": digest(output / "sparse.npz"),
        "shape_tzx": list(ph.shape), "selected_positions_including_ic": int(ph.size),
        "analytic_ic_positions": int(len(x)*len(z)),
        "observed_positions_t_positive": int((len(t)-1)*len(x)*len(z)),
        "observed_scalar_values_t_positive": int(3*(len(t)-1)*len(x)*len(z)),
        "interface_cells": int(len(lower)), "interface_endpoints": int(np.count_nonzero(endpoints)),
        "exported_keys": ["x", "z", "time", "coordinates", "targets", "global_probability",
                          "interface_probability", "cell_lower", "cell_upper", "straddles"],
        "teacher_current_power_exported": False, "dense_weights_exported": False,
    }
    save_json(output / "sparse_manifest.json", record)
    return record


class SparseData:
    def __init__(self, path):
        with np.load(path, allow_pickle=False) as f:
            self.arrays = {key: f[key] for key in f.files}
        expected = {"x", "z", "time", "coordinates", "targets", "global_probability",
                    "interface_probability", "cell_lower", "cell_upper", "straddles"}
        if set(self.arrays) != expected:
            raise ValueError("sparse bundle contains unexpected fields")
        self.coordinates = self.arrays["coordinates"]
        self.targets = self.arrays["targets"]
        self.prob = self.arrays["global_probability"]
        self.endpoint_prob = self.arrays["interface_probability"]
        self.has_interface = bool(np.any(self.endpoint_prob > 0))

    def indices(self, rng, count):
        ng = count // 2 if self.has_interface else count
        global_idx = rng.choice(len(self.prob), ng, p=self.prob)
        if not self.has_interface:
            return global_idx, ng
        extra = rng.choice(len(self.prob), count-ng, p=self.endpoint_prob)
        return np.r_[global_idx, extra], ng

    def loss(self, model, indices, ng, config, device):
        q, target = tensor(self.coordinates[indices], device), tensor(self.targets[indices], device)
        d = model.read_only_output_diagnostics(q)
        pred, physics = d.output.fields, model.physics
        v = ((pred[:ng, 0]-target[:ng, 0]) / physics.waveform_amplitude).square().mean()
        t = ((pred[:ng, 1]-target[:ng, 1]) / physics.theta_transition).square().mean()
        initial = physics.initial_phase(q).clamp(1e-8, 1-1e-8)
        desired = torch.logit(target[:, 2:3].clamp(1e-8, 1-1e-8))-torch.logit(initial)
        startup = 1-torch.exp(-(q[:, 2:3]-physics.time_start)/.35)
        latent = 8*startup*d.latents["phase"]
        err = ((latent-desired)/config["phase_logit_divisor"]).square().ravel()
        valid = q[:ng, 2] > physics.time_start
        phase = err[:ng][valid].mean()
        if len(indices) > ng:
            phase = .5*phase + .5*err[ng:].mean()
        return {"observation": (v+t+phase)/3, "obs_V": v, "obs_T": t, "obs_phase": phase}


class PhysicsSampler:
    def __init__(self, data, config, seed, physics):
        self.data, self.config, self.physics = data, config, physics
        self.rng = np.random.default_rng(seed)
        self.bc_rng = np.random.default_rng(seed+123456)
        self.bounds = []
        self.pB = []
        for lo, hi in config["windows"]:
            low = data.arrays["cell_lower"].copy()
            high = data.arrays["cell_upper"].copy()
            low[:, 2] = np.maximum(low[:, 2], lo)
            high[:, 2] = np.minimum(high[:, 2], hi)
            keep = np.all(high > low, axis=1)
            low, high = low[keep], high[keep]
            vol = np.prod(high-low, axis=1)
            self.bounds.append((low, high, vol))
            self.pB.append(float(vol.sum()/((physics.x_max-physics.x_min)*(physics.z_max-physics.z_min)*(hi-lo))))

    def in_B(self, q):
        a = self.data.arrays
        idx = [np.searchsorted(a[name], q[:, col], side="right")-1
               for col, name in enumerate(("x", "z", "time"))]
        valid = np.ones(len(q), dtype=bool)
        for i, name in zip(idx, ("x", "z", "time")):
            valid &= (i >= 0) & (i < len(a[name])-1)
        inside = np.zeros(len(q), dtype=bool)
        inside[valid] = a["straddles"][idx[2][valid], idx[1][valid], idx[0][valid]].astype(bool)
        return inside

    def interior(self, proposal=False, multiplier=1):
        coords, weights, masses = [], [], []
        p = self.physics
        for widx, ((lo, hi), n, mass) in enumerate(zip(self.config["windows"], self.config["interior_counts"], self.config["window_masses"])):
            n *= multiplier
            q = self.rng.uniform([p.x_min, p.z_min, lo], [p.x_max, p.z_max, hi], (n, 3))
            density = np.ones(n)
            if proposal and 0 < self.pB[widx] < 1-1e-14:
                low, high, vol = self.bounds[widx]
                count = n//4
                cells = self.rng.choice(len(vol), count, p=vol/vol.sum())
                q[-count:] = low[cells]+self.rng.random((count, 3))*(high[cells]-low[cells])
                density = .75+.25*self.in_B(q)/self.pB[widx]
            coords.append(q)
            weights.append(1/density)
            masses.append(np.full(n, mass/n))
        return np.concatenate(coords), np.concatenate(weights), np.concatenate(masses)

    def boundary_initial(self):
        p, r = self.physics, self.bc_rng
        windows = []
        for (lo, hi), n in zip(self.config["windows"], self.config["boundary_counts_per_side"]):
            sides = {}
            for side in ("left", "right", "bottom", "top"):
                q = r.uniform([p.x_min, p.z_min, lo], [p.x_max, p.z_max, hi], (n, 3))
                if side == "left": q[:, 0] = p.x_min
                if side == "right": q[:, 0] = p.x_max
                if side == "top": q[:, 1] = p.z_max
                if side == "bottom":
                    q[:, 1] = p.z_min
                    # Both mixed-boundary families are present in every window.
                    q[:n//2, 0] = r.uniform(-p.heater_half_width, p.heater_half_width, n//2)
                    u = r.random(n-n//2)
                    q[n//2:, 0] = np.where(u < .5, p.x_min+2*u*(p.heater_half_width+p.x_min)*(-1),
                                           p.heater_half_width+2*(u-.5)*(p.x_max-p.heater_half_width))
                sides[side] = q
            windows.append(sides)
        initial = r.uniform([p.x_min, p.z_min], [p.x_max, p.z_max], (self.config["initial_points"], 2))
        return windows, initial


def boundary_initial_loss(model, batches, initial, config, device):
    total = next(model.parameters()).new_zeros(())
    for mass, sides in zip(config["window_masses"], batches):
        terms = []
        for side, q in sides.items():
            for name, value in boundary_residuals(model, tensor(q, device), side=side).items():
                terms.append((value/BOUNDARY_SCALES[name]).square().mean())
        total = total+mass*torch.stack(terms).mean()
    ic = normalized_residual_loss(initial_residuals(model, tensor(initial, device)), scales=INITIAL_SCALES)
    return total, ic


def pde_terms(model, batch, device):
    q, w, mass = batch
    residuals = interior_residuals(model, tensor(q, device))
    mass, w = tensor(mass, device), tensor(w, device)
    losses = {name: (residuals[name].ravel()/PDE_SCALES[name]).square()
              for name in ("electric", "thermal", "phase")}
    uniform = {name: torch.sum(mass*w*value) for name, value in losses.items()}
    phase_q = torch.sum(mass*losses["phase"])
    return uniform, phase_q


def calibration(model, data, config, device):
    rng = np.random.default_rng(50117)
    idx, ng = data.indices(rng, 8192)
    with torch.no_grad():
        a0 = float(data.loss(model, idx, ng, config, device)["observation"])
    us = PhysicsSampler(data, config, 50217, model.physics)
    qs = PhysicsSampler(data, config, 50317, model.physics)
    sums = {"electric": 0., "thermal": 0., "phase": 0.}
    phase_q = 0.
    repeats = max(1, config["calibration_points"]//sum(config["interior_counts"]))
    for _ in range(repeats):
        terms, _ = pde_terms(model, us.interior(False), device)
        for name in sums: sums[name] += float(terms[name].detach())/repeats
        _, pq = pde_terms(model, qs.interior(True), device)
        phase_q += float(pq.detach())/repeats
    bc, ic = boundary_initial_loss(model, *us.boundary_initial(), config, device)
    b0 = sum(sums.values())/3+5*float(bc.detach())+float(ic.detach())
    finite = np.isfinite([a0, b0, phase_q, *sums.values()]).all()
    if not finite:
        raise ValueError("nonfinite common calibration")
    identifiable = phase_q > config["calibration_denominator_min"] and sums["phase"] > config["calibration_denominator_min"]
    return {"a0": a0, "b0": b0, "c0": sums["phase"]/phase_q if identifiable else None,
            "P_M_identifiable": bool(identifiable), "uniform_pde": sums, "proposal_phase": phase_q,
            "boundary": float(bc.detach()), "initial": float(ic.detach()), "pB": us.pB,
            "calibration_points_per_measure": repeats*sum(config["interior_counts"]),
            "fixed_calibration_seeds": [50117, 50217, 50317]}


def objective(model, data, config, device, obs_indices, ng, physics_batch, bc_ic,
              role, step, cal):
    terms = data.loss(model, obs_indices, ng, config, device)
    if role == "warm_start":
        return terms["observation"], terms
    bc, ic = boundary_initial_loss(model, *bc_ic, config, device)
    lam = config["lambda_max"]*min(step/config["lambda_ramp"], 1)
    total = terms["observation"]/max(cal["a0"], 1e-12)+lam*(5*bc+ic)/max(cal["b0"], 1e-12)
    terms.update(boundary=bc, initial=ic)
    if role != "D_B":
        pde, pq = pde_terms(model, physics_batch, device)
        phase = cal["c0"]*pq if role == "P_M" else pde["phase"]
        if role == "P_S": phase = cal["kappa0"]*pde["phase"]
        value = (pde["electric"]+pde["thermal"]+phase)/3
        total = total+lam*value/max(cal["b0"], 1e-12)
        terms.update({"pde_"+k: v for k, v in pde.items()})
        terms["phase_proposal"] = pq
        terms["pde_objective"] = value
    terms["total"] = total
    return total, terms


def write_checkpoint(path, model, optimizer, config, role, steps, input_sha, cal):
    torch.save({"schema_id": "lf11-checkpoint-v1", "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(), "config": config,
                "role": role, "updates": steps, "sparse_sha256": input_sha,
                "calibration": cal, "physics": asdict(model.physics)}, path)


def run_role(role, data, config, device, output, input_sha, parent=None, cal=None):
    root = Path(output)/role
    root.mkdir(parents=True, exist_ok=False)
    model = build_model(config, device)
    if parent is not None:
        model.load_state_dict(torch.load(parent, map_location=device, weights_only=False)["model_state_dict"])
    warm = role == "warm_start"
    opt = torch.optim.Adam(model.parameters(), lr=config["warmup_lr" if warm else "branch_lr"],
                           betas=tuple(config["betas"]), eps=config["eps"])
    rng = np.random.default_rng(60117)
    sampler = PhysicsSampler(data, config, 60217, model.physics)
    count = config["warmup_updates" if warm else "branch_updates"]
    completed = 0
    start = time.monotonic()
    try:
        with (root/"telemetry.jsonl").open("x", encoding="utf-8") as log:
            for step in range(1, count+1):
                idx, ng = data.indices(rng, config["data_points"])
                pb = sampler.interior(role in {"P_I", "P_M", "P_S"}) if not warm and role != "D_B" else None
                bc_ic = sampler.boundary_initial() if not warm else None
                opt.zero_grad(set_to_none=True)
                loss, terms = objective(model, data, config, device, idx, ng, pb, bc_ic, role, step, cal)
                if not torch.isfinite(loss): raise FloatingPointError("nonfinite loss before update")
                loss.backward()
                norm = torch.nn.utils.clip_grad_norm_(model.parameters(), config["gradient_clip"], error_if_nonfinite=True)
                opt.step()
                completed = step
                if step == 1 or step % 50 == 0 or step == count:
                    record = {"step": step, "gradient_norm_before_clip": float(norm),
                              **{k: float(v.detach()) for k, v in terms.items()}}
                    log.write(json.dumps(record, allow_nan=False)+"\n"); log.flush()
                    print(json.dumps({"role": role, "step": step, "loss": float(loss.detach())}), flush=True)
                if step % 600 == 0:
                    write_checkpoint(root/f"checkpoint-step-{step}.pt", model, opt, config, role, step, input_sha, cal)
        write_checkpoint(root/"checkpoint.pt", model, opt, config, role, completed, input_sha, cal)
        result = {"role": role, "status": "VALID_FIXED_ENDPOINT", "updates": completed,
                  "sparse_sha256": input_sha, "parameter_count": sum(p.numel() for p in model.parameters()),
                  "checkpoint": str((root/"checkpoint.pt").relative_to(output)), "completed_utc": now()}
        save_json(root/"result.json", result)
        return result, model
    except Exception as exc:
        result = {"role": role, "status": "INVALID", "updates": completed,
                  "exception": str(exc), "traceback": traceback.format_exc()}
        save_json(root/"result.json", result)
        if completed:
            write_checkpoint(root/"invalid-checkpoint.pt", model, opt, config, role, completed, input_sha, cal)
        return result, None


def predict(model, config, path, device):
    """Use public coordinate rules, without opening any reference arrays."""
    from .phk_v22r_prediction import _evaluation_axes
    from .phk_v22r_training import PhkTrainingConfig
    x, z, times = _evaluation_axes(PhkTrainingConfig(arm="STRONG_RAW", case_control="FULL"))
    xx, zz = np.meshgrid(x, z, indexing="xy")
    space = np.column_stack([xx.ravel(), zz.ravel()])
    fields = np.empty((len(times), len(space), 3), dtype=np.float64)
    with torch.no_grad():
        for it, tv in enumerate(times):
            q = np.column_stack([space, np.full(len(space), tv)])
            for start in range(0, len(q), 8192):
                fields[it, start:start+8192] = model(tensor(q[start:start+8192], device)).cpu().numpy()
    with Path(path).open("xb") as f:
        np.savez_compressed(f, x=x, z=z, time=times,
                            **{name: fields[..., i] for i, name in enumerate(FIELDS)})


def train_campaign(bundle, config, output, device, predictions=True):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if (output/"campaign.json").exists() or (output/"warm_start").exists():
        raise FileExistsError("existing scientific output; no implicit rerun")
    data = SparseData(bundle)
    source_sha = digest(bundle)
    save_json(output/"frozen_config.json", config)
    results = {}
    result, model = run_role("warm_start", data, config, device, output, source_sha)
    results["warm_start"] = result
    if model is None:
        save_json(output/"campaign.json", {"status": "WARM_START_INVALID", "results": results})
        return
    cal = calibration(model, data, config, device)
    save_json(output/"calibration.json", cal)
    if predictions: predict(model, config, output/"warm_start/prediction.npz", device)
    parent = output/"warm_start/checkpoint.pt"
    for role in config["roles"]:
        if role in {"P_I", "P_M"} and all(p <= 0 or p >= 1-1e-14 for p in cal["pB"]):
            results[role] = {"status": "NOT_TESTABLE", "updates": 0, "reason": "proposal equals uniform in every window"}
            continue
        if role == "P_M" and not cal["P_M_identifiable"]:
            results[role] = {"status": "NOT_TESTABLE", "updates": 0, "reason": "initial phase calibration not identifiable"}
            continue
        result, model = run_role(role, data, config, device, output, source_sha, parent, cal)
        results[role] = result
        save_json(output/"progress.json", {"results": results})
        if model is not None and predictions:
            predict(model, config, output/role/"prediction.npz", device)
    save_json(output/"campaign.json", {"schema_id": "lf11-four-arm-screen-v1", "status": "FIXED_SCREEN_COMPLETE",
                                       "results": results, "optimizer_updates": sum(v["updates"] for v in results.values()),
                                       "sparse_sha256": source_sha, "completed_utc": now(),
                                       "high_fidelity_read": False, "stress_read": False})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("extract", "train"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--no-predictions", action="store_true")
    args = parser.parse_args()
    torch.set_num_threads(args.threads)
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if args.action == "extract":
        print(json.dumps(extract_sparse(args.source or ROOT/config["medium"], args.output, config)))
    else:
        train_campaign(args.bundle, config, args.output, args.device, not args.no_predictions)


if __name__ == "__main__":
    main()
