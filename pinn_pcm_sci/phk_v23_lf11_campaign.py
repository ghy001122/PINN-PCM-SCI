"""Continue the authorized LF11 screen from its completed, sparse-only parent."""
from __future__ import annotations
import argparse
import json
import platform
from pathlib import Path

import numpy as np
import torch

from .phk_v23_lf11 import (
    SparseData, PhysicsSampler, build_model, boundary_initial_loss, pde_terms,
    run_role, predict, save_json, digest, now, PDE_SCALES,
)


def fixed_audit(model, data, config, device):
    """Identical reference-free integration for each fixed neural endpoint."""
    sampler = PhysicsSampler(data, config, 70217, model.physics)
    sums = {k: 0. for k in ("electric", "thermal", "phase")}
    repetitions = config["calibration_points"]//sum(config["interior_counts"])
    for _ in range(repetitions):
        terms, _ = pde_terms(model, sampler.interior(False), device)
        for name in sums:
            sums[name] += float(terms[name].detach())/repetitions
    bc, ic = boundary_initial_loss(model, *sampler.boundary_initial(), config, device)
    idx, ng = data.indices(np.random.default_rng(70117), 8192)
    with torch.no_grad():
        obs = data.loss(model, idx, ng, config, device)
    return {"measure": "fixed independent uniform space-time integration",
            "points": repetitions*sum(config["interior_counts"]),
            "scaled_pde_mse": sums,
            "raw_pde_rms": {k: float(np.sqrt(v)*PDE_SCALES[k]) for k,v in sums.items()},
            "boundary": float(bc.detach()), "initial": float(ic.detach()),
            "observation": {k: float(v) for k,v in obs.items()},
            "no_reference_read": True, "optimizer_updates": 0}


def scalar_calibration(model, data, config, cal, device):
    """P-S matches the full phase-loss parameter gradient at the common parent."""
    sampler = PhysicsSampler(data, config, 70317, model.physics)
    params = list(model.parameters())
    accum = [torch.zeros(sum(p.numel() for p in params), dtype=torch.float64, device=device) for _ in range(2)]
    repetitions = config["calibration_points"]//sum(config["interior_counts"])
    for _ in range(repetitions):
        uniform, phase_q = pde_terms(model, sampler.interior(True), device)
        for i, loss in enumerate((uniform["phase"], cal["c0"]*phase_q)):
            gradients = torch.autograd.grad(loss, params, allow_unused=True, retain_graph=i==0)
            flat = torch.cat([(g if g is not None else torch.zeros_like(p)).reshape(-1) for p,g in zip(params, gradients)])
            accum[i] += flat.detach()/repetitions
    norms = [float(g.norm()) for g in accum]
    return {"schema_id": "lf11-fixed-global-phase-attribution-v1", "recorded_utc": now(),
            "kappa0": norms[1]/norms[0] if norms[0] > 1e-24 else None,
            "full_parameter_gradient_norm_uniform": norms[0],
            "full_parameter_gradient_norm_metric": norms[1],
            "gradient_cosine": float(torch.dot(*accum)/(accum[0].norm()*accum[1].norm()).clamp_min(1e-24)),
            "calibration_seed": 70317, "points": repetitions*sum(config["interior_counts"]),
            "reference_blind": True, "parent": "formal/warm_start/checkpoint.pt", "optimizer_updates": 0}


def campaign(root, device):
    root = Path(root)
    formal = root/"formal"
    config = json.loads((formal/"frozen_config.json").read_text(encoding="utf-8"))
    cal = json.loads((formal/"calibration.json").read_text(encoding="utf-8"))
    parent = formal/"warm_start/checkpoint.pt"
    previous = json.loads((formal/"warm_start/result.json").read_text(encoding="utf-8"))
    source_sha = digest(root/"input/sparse.npz")
    cp = torch.load(parent, map_location="cpu", weights_only=False)
    if previous["status"] != "VALID_FIXED_ENDPOINT" or cp["updates"] != 1200 or cp["sparse_sha256"] != source_sha or cp["config"] != config:
        raise ValueError("the already completed common parent does not match this frozen screen")
    if (formal/"campaign.json").exists():
        raise FileExistsError("completed screen exists; no implicit rerun")
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("requested GPU is unavailable; zero branch updates")
    data = SparseData(root/"input/sparse.npz")
    model = build_model(config, device)
    model.load_state_dict(cp["model_state_dict"])
    del cp
    save_json(formal/"execution_environment.json", {
        "recorded_utc": now(), "python": platform.python_version(), "torch": torch.__version__,
        "numpy": np.__version__, "device": device, "threads": torch.get_num_threads(),
        "device_name": torch.cuda.get_device_name() if device == "cuda" else platform.processor(),
        "all_formal_branches_same_environment": True, "warm_start_reused": True,
        "parent_sha256": digest(parent), "sparse_sha256": source_sha,
        "source_identity": json.loads((root/"source_identity.json").read_text())})
    if cal["P_M_identifiable"]:
        save_json(formal/"conditional_calibration.json", scalar_calibration(model, data, config, cal, device))
    save_json(formal/"warm_start/fixed_audit.json", fixed_audit(model, data, config, device))
    if not (formal/"warm_start/prediction.npz").exists():
        predict(model, config, formal/"warm_start/prediction.npz", device)
    results = {"warm_start": previous}
    for role in config["roles"]:
        if role in {"P_I", "P_M"} and all(p <= 0 or p >= 1-1e-14 for p in cal["pB"]):
            results[role] = {"status": "NOT_TESTABLE", "updates": 0, "reason": "proposal equals uniform in every window"}
            continue
        if role == "P_M" and not cal["P_M_identifiable"]:
            results[role] = {"status": "NOT_TESTABLE", "updates": 0, "reason": "phase calibration not identifiable"}
            continue
        result, model = run_role(role, data, config, device, formal, source_sha, parent, cal)
        results[role] = result
        save_json(formal/"progress.json", {"results": results})
        if model is not None:
            save_json(formal/role/"fixed_audit.json", fixed_audit(model, data, config, device))
            predict(model, config, formal/role/"prediction.npz", device)
    save_json(formal/"campaign.json", {
        "schema_id": "lf11-four-arm-screen-v1", "status": "FIXED_SCREEN_COMPLETE",
        "results": results, "optimizer_updates": sum(v["updates"] for v in results.values()),
        "sparse_sha256": source_sha, "completed_utc": now(),
        "high_fidelity_read": False, "stress_read": False})
    print("LF11_FIXED_SCREEN_COMPLETE", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    torch.set_num_threads(2)
    campaign(args.root, args.device)


if __name__ == "__main__":
    main()
