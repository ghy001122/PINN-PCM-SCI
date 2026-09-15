"""Authorized same-parent DI/DB/PU comparison, with sparse-only training.

The original equations, observation measures and BC denominators are retained.
New common-parent calibration is a protocol change, not a method claim.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import time
import traceback

import numpy as np
import torch

from .phk_v23_lf11 import (
    ROOT, SparseData, PhysicsSampler, tensor, now, save_json, digest,
    pde_terms, boundary_initial_loss,
)
from .phk_v23_lf11_followup_fit import fit_model, fit_metrics
from .phk_v23_lf11_v_continue import continued_lbfgs
from .phk_v22r_pinn import boundary_residuals, initial_residuals, normalized_residual_loss
from .phk_v22r_training import BOUNDARY_SCALES, INITIAL_SCALES

RUN = ROOT / "outputs/runs/20260912-lf11-joint-bc-pde"
CONFIG = ROOT / "configs/phk_v23/lf11_joint_sprint.json"
BC_GROUPS = ("bc_insulation", "bc_heater", "bc_phase_no_flux", "bc_thermal", "bc_top_potential")


def full_observation(model, data, config, *, backward=False, coefficient=1., chunk=None):
    """Exact weighted full observation integral; chunks only limit memory."""
    chunk = chunk or config.get("full_observation_chunk", 4096)
    positive = data.coordinates[:, 2] > model.physics.time_start
    global_weight = data.prob / data.prob.sum()
    phase_weight = data.prob * positive
    phase_weight = phase_weight / phase_weight.sum()
    if data.has_interface:
        phase_weight = .5 * phase_weight + .5 * data.endpoint_prob / data.endpoint_prob.sum()
    totals = {k: 0. for k in ("obs_V", "obs_T", "obs_phase")}
    for lo in range(0, len(data.coordinates), chunk):
        sl = slice(lo, lo + chunk)
        q, target = tensor(data.coordinates[sl]), tensor(data.targets[sl])
        d = model.read_only_output_diagnostics(q)
        initial = model.physics.initial_phase(q).clamp(config["phase_logit_epsilon"], 1-config["phase_logit_epsilon"])
        desired = torch.logit(target[:, 2:3].clamp(config["phase_logit_epsilon"], 1-config["phase_logit_epsilon"])) - torch.logit(initial)
        startup = 1-torch.exp(-(q[:, 2:3]-model.physics.time_start)/model.startup_time)
        increment = model.phase_latent_scale * startup * d.latents["phase"]
        terms = {
            "obs_V": torch.dot(tensor(global_weight[sl]), ((d.output.fields[:, 0]-target[:, 0])/model.physics.waveform_amplitude).square()),
            "obs_T": torch.dot(tensor(global_weight[sl]), ((d.output.fields[:, 1]-target[:, 1])/model.physics.theta_transition).square()),
            "obs_phase": torch.dot(tensor(phase_weight[sl]), ((increment-desired)/config["phase_logit_divisor"]).square().ravel()),
        }
        if backward:
            (coefficient * sum(terms.values()) / 3).backward()
        for key, value in terms.items():
            totals[key] += float(value.detach())
    totals["observation"] = sum(totals.values()) / 3
    return totals


def boundary_components(model, batches, config):
    """Split the original soft-BC package without changing its 13-term mean."""
    result = {k: next(model.parameters()).new_zeros(()) for k in BC_GROUPS}
    for mass, sides in zip(config["window_masses"], batches, strict=True):
        residuals = [(name, value) for side, q in sides.items()
                     for name, value in boundary_residuals(model, tensor(q), side=side).items()]
        denominator = len(residuals)
        for name, value in residuals:
            if "insulating" in name:
                group = "bc_insulation"
            elif name == "bc_potential_heater":
                group = "bc_heater"
            elif name == "bc_phase_no_flux":
                group = "bc_phase_no_flux"
            elif "temperature" in name:
                group = "bc_thermal"
            else:
                group = "bc_top_potential"
            result[group] = result[group] + mass * (value/BOUNDARY_SCALES[name]).square().mean()/denominator
    return result


def initial_loss(model, coordinates):
    return normalized_residual_loss(initial_residuals(model, tensor(coordinates)), scales=INITIAL_SCALES)


def batch_components(model, data, config, cal, role, step, indices, ng, pb, bc_ic):
    obs = data.loss(model, indices, ng, config, "cpu")
    lam = config["lambda_max"] * min(step/config["lambda_ramp"], 1.)
    a, b = max(cal["a_star"], 1e-12), max(cal["b_star"], 1e-12)
    components = {"observation": obs["observation"]/a,
                  "initial": lam * initial_loss(model, bc_ic[1])/b}
    if role != "D_I":
        components.update({k: lam*5*v/b for k, v in boundary_components(model, bc_ic[0], config).items()})
    if role == "P_U":
        pde, _ = pde_terms(model, pb, "cpu")
        components.update({k: lam*v/(3*b) for k, v in pde.items()})
    return components, obs


def fixed_pools(data, config, physics, seed):
    fixed_config = copy.deepcopy(config)
    multiple = config["fixed_boundary_multiplier"]
    fixed_config["boundary_counts_per_side"] = [n*multiple for n in config["boundary_counts_per_side"]]
    sampler = PhysicsSampler(data, fixed_config, seed, physics)
    return {"pde": sampler.interior(False, multiplier=config["fixed_interior_multiplier"]),
            "bc_ic": sampler.boundary_initial(), "seed": seed}


def fixed_objective(model, data, config, cal, role, pools, *, backward=True):
    a, b = max(cal["a_star"], 1e-12), max(cal["b_star"], 1e-12)
    lam = config["lambda_max"]
    obs = full_observation(model, data, config, backward=backward, coefficient=1/a)
    total = obs["observation"]/a
    if role == "D_I":
        ic = initial_loss(model, pools["bc_ic"][1])
        boundary = ic*0
    else:
        boundary, ic = boundary_initial_loss(model, *pools["bc_ic"], config, "cpu")
    loss = lam*(5*boundary+ic)/b
    if backward:
        loss.backward()
    total += float(loss.detach())
    if role == "P_U":
        pb = pools["pde"]
        for lo in range(0, len(pb[0]), config["physics_chunk"]):
            batch = tuple(v[lo:lo+config["physics_chunk"]] for v in pb)
            terms, _ = pde_terms(model, batch, "cpu")
            loss = lam*sum(terms.values())/(3*b)
            if backward:
                loss.backward()
            total += float(loss.detach())
    return torch.tensor(total, dtype=torch.float64)


def physics_audit(model, config, pools):
    sums = {k: 0. for k in ("electric", "thermal", "phase")}
    for lo in range(0, len(pools["pde"][0]), config["physics_chunk"]):
        terms, _ = pde_terms(model, tuple(v[lo:lo+config["physics_chunk"]] for v in pools["pde"]), "cpu")
        for name, value in terms.items():
            sums[name] += float(value.detach())
    bc, ic = boundary_initial_loss(model, *pools["bc_ic"], config, "cpu")
    return {"pde": sums, "J_U": sum(sums.values())/3,
            "boundary": float(bc.detach()), "initial": float(ic.detach())}


def calibrate(model, data, config, pools):
    with torch.no_grad():
        obs = full_observation(model, data, config)
    audit = physics_audit(model, config, pools)
    result = {"a_star": obs["observation"],
              "b_star": audit["J_U"]+5*audit["boundary"]+audit["initial"],
              "observation": obs, "physics": audit, "pool_seed": pools["seed"],
              "reference_read": False, "calibrated_once_at_shared_parent": True}
    if not np.isfinite([result["a_star"], result["b_star"]]).all():
        raise FloatingPointError("nonfinite shared calibration")
    return result


def checkpoint(path, model, optimizer, config, cal, role, updates, **extra):
    torch.save({"schema_id": "lf11-joint-checkpoint-v1", "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict() if optimizer else None,
                "temperature_adapter": True, "config": config, "calibration": cal,
                "role": role, "updates": updates, **extra}, path)


def train_role(root, role, config, data, parent_state, cal, pools, audit_pool):
    folder = root/role
    folder.mkdir(exist_ok=False)
    model = fit_model(config, parent_state, adapter=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=config["branch_lr"],
                                 betas=tuple(config["betas"]), eps=config["eps"])
    rng = np.random.default_rng(config["observation_seed"])
    sampler = PhysicsSampler(data, config, config["sampling_seed"], model.physics)
    completed = 0
    start = time.perf_counter()
    try:
        with (folder/"adam-telemetry.jsonl").open("x", encoding="utf-8") as log:
            for step in range(1, config["branch_updates"]+1):
                idx, ng = data.indices(rng, config["data_points"])
                pb, bc_ic = sampler.interior(False), sampler.boundary_initial()
                optimizer.zero_grad(set_to_none=True)
                components, obs = batch_components(model, data, config, cal, role, step, idx, ng, pb, bc_ic)
                loss = sum(components.values())
                if not torch.isfinite(loss):
                    raise FloatingPointError("nonfinite pre-update objective")
                loss.backward()
                norm = torch.nn.utils.clip_grad_norm_(model.parameters(), config["gradient_clip"], error_if_nonfinite=True)
                optimizer.step()
                completed = step
                if not all(torch.isfinite(p).all() for p in model.parameters()):
                    raise FloatingPointError("nonfinite post-update parameters")
                if step == 1 or step % 100 == 0:
                    record = {"step": step, "loss": float(loss.detach()), "gradient_norm": float(norm),
                              "components": {k: float(v.detach()) for k, v in components.items()},
                              "observations": {k: float(v.detach()) for k, v in obs.items()}}
                    log.write(json.dumps(record, allow_nan=False)+"\n"); log.flush()
                    print(json.dumps({"role": role, "adam_step": step, "loss": record["loss"]}), flush=True)
                if step in config["checkpoint_steps"]:
                    checkpoint(folder/f"adam-{step}.pt", model, optimizer, config, cal, role, step,
                               observation_rng_state=copy.deepcopy(rng.bit_generator.state),
                               interior_rng_state=copy.deepcopy(sampler.rng.bit_generator.state),
                               boundary_rng_state=copy.deepcopy(sampler.bc_rng.bit_generator.state),
                               optimizer_phase="Adam", reference_read=False)
        with (folder/"lbfgs-telemetry.jsonl").open("x", encoding="utf-8") as log:
            def record_lbfgs(record):
                log.write(json.dumps(record, allow_nan=False)+"\n"); log.flush()
                if record["accepted_steps"] == 1 or record["accepted_steps"] % 20 == 0:
                    print(json.dumps({"role": role, "lbfgs": record}), flush=True)
            result, optimizer = continued_lbfgs(model.parameters(),
                lambda: fixed_objective(model, data, config, cal, role, pools),
                config["lbfgs_evaluations"], record_lbfgs)
        checkpoint(folder/"checkpoint.pt", model, optimizer, config, cal, role, completed,
                   optimizer_phase="L-BFGS", lbfgs_result=result, reference_read=False)
        visible = fit_metrics(model, data, config)
        fixed_audit = physics_audit(model, config, audit_pool)
        if not visible["finite"] or not np.isfinite([fixed_audit["J_U"], fixed_audit["boundary"], fixed_audit["initial"]]).all():
            raise FloatingPointError("nonfinite endpoint or fixed audit")
        outcome = {"role": role, "status": "VALID_FIXED_ENDPOINT", "adam_updates": completed,
                   "lbfgs": result, "visible": visible, "fixed_physics_audit": fixed_audit,
                   "completed_utc": now(), "elapsed_seconds_internal": time.perf_counter()-start,
                   "reference_read": False, "optimizer_parent_history_inherited": False}
    except Exception as exc:
        checkpoint(folder/"invalid-checkpoint.pt", model, optimizer, config, cal, role, completed,
                   validity="INVALID", exception=str(exc))
        outcome = {"role": role, "status": "INVALID", "adam_updates": completed,
                   "exception": str(exc), "traceback": traceback.format_exc(), "completed_utc": now()}
    save_json(folder/"result.json", outcome)
    print(json.dumps({"role_finished": role, "status": outcome["status"]}), flush=True)
    return outcome


def run(root=RUN):
    root = Path(root)
    if (root/"calibration.json").exists() or any((root/r).exists() for r in ("D_I", "D_B", "P_U")):
        raise FileExistsError("scientific campaign already started; no implicit rerun")
    root.mkdir(parents=True, exist_ok=True)
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    torch.set_num_threads(config["cpu_threads"])
    data = SparseData(ROOT/config["sparse"])
    parent = torch.load(ROOT/config["parent"], map_location="cpu", weights_only=False)
    if not parent.get("temperature_adapter"):
        raise ValueError("expected final temperature adapter")
    model = fit_model(config, parent["model_state_dict"], adapter=True)
    cal_pool = fixed_pools(data, config, model.physics, config["calibration_seed"])
    pools = fixed_pools(data, config, model.physics, config["lbfgs_pool_seed"])
    audit = fixed_pools(data, config, model.physics, config["audit_pool_seed"])
    cal = calibrate(model, data, config, cal_pool)
    save_json(root/"frozen-config.json", config)
    save_json(root/"calibration.json", cal)
    save_json(root/"input-identity.json", {"parent": config["parent"], "parent_sha256": digest(ROOT/config["parent"]),
              "sparse": config["sparse"], "sparse_sha256": digest(ROOT/config["sparse"]),
              "source_commit": config["source_commit"], "recorded_utc": now()})
    torch.save({"calibration": cal_pool, "lbfgs": pools, "audit": audit}, root/"fixed-pools.pt")
    checkpoint(root/"parent.pt", model, None, config, cal, "parent", 0)
    save_json(root/"parent-visible.json", fit_metrics(model, data, config))
    save_json(root/"parent-physics-audit.json", physics_audit(model, config, audit))
    print(json.dumps({"common_calibration": cal}), flush=True)
    results = {}
    for role in config["roles"]:
        results[role] = train_role(root, role, config, data, parent["model_state_dict"], cal, pools, audit)
        save_json(root/"progress.json", {"results": results, "reference_read": False})
    campaign = {"schema_id": "lf11-joint-three-arm-campaign-v1", "results": results,
                "status": "MAIN_TRAINING_COMPLETE", "recorded_utc": now(), "pid": os.getpid(),
                "adam_updates": sum(r["adam_updates"] for r in results.values()),
                "lbfgs_evaluations": sum(r.get("lbfgs", {}).get("evaluations", 0) for r in results.values()),
                "reference_read": False, "stress_read": False, "cloud_instance_started": False}
    save_json(root/"campaign.json", campaign)
    print(json.dumps({"campaign_complete": True, "adam_updates": campaign["adam_updates"],
                      "lbfgs_evaluations": campaign["lbfgs_evaluations"]}), flush=True)
    return campaign


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=RUN)
    run(parser.parse_args().root)
