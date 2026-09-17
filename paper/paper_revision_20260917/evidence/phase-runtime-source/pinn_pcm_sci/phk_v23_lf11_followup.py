"""LF11 follow-up: sparse-only representation feasibility before optimization.

The pointwise interval projection is a mathematical lower bound, never a
replacement observation or a trained/reconstructed field.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from .phk_v23_lf11 import ROOT, SparseData, build_model, digest, now, save_json, tensor


RUN = ROOT / "outputs/runs/20260911-lf11-followup-fit-electric-block"


def weighted_rms(error, weight, mask=None):
    weight = np.asarray(weight, dtype=np.float64)
    if mask is not None:
        weight = weight * mask
    total = float(weight.sum())
    if total <= 0:
        return None
    return float(np.sqrt(np.dot(weight, np.asarray(error) ** 2) / total))


def temperature_envelope(coordinates, scale=2.5, startup_time=.35,
                         time_start=0., z_min=0., z_max=1.):
    q = np.asarray(coordinates)
    return scale * (-np.expm1(-(q[:, 2] - time_start) / startup_time)) * (
        1 - (q[:, 1] - z_min) / (z_max - z_min))


def interval_distance(values, upper):
    """Distance to [0, upper]; valid even at zero-envelope IC/top points."""
    values, upper = np.asarray(values), np.asarray(upper)
    if np.any(upper < 0):
        raise ValueError("negative envelope at supported coordinates")
    return np.maximum(-values, 0) + np.maximum(values - upper, 0)


def strata(data, physics):
    t = data.coordinates[:, 2]
    drive = physics.waveform(tensor(t[:, None])).detach().numpy().ravel()
    return {"all": np.ones(len(t), dtype=bool),
            "heating": (t > physics.time_start) & (drive > 0),
            "off": (t > physics.time_start) & (drive == 0)}


def predict_visible(model, data, chunk=4096):
    fields, phase_increment, envelopes = [], [], []
    with torch.no_grad():
        for lo in range(0, len(data.coordinates), chunk):
            q = tensor(data.coordinates[lo:lo+chunk])
            d = model.read_only_output_diagnostics(q)
            fields.append(d.output.fields.numpy())
            startup = 1-torch.exp(-(q[:, 2:3]-model.physics.time_start)/model.startup_time)
            phase_increment.append((model.phase_latent_scale*startup*d.latents["phase"]).numpy().ravel())
            envelopes.append((model.temperature_scale*startup*(
                1-(q[:, 1:2]-model.physics.z_min)/(model.physics.z_max-model.physics.z_min))).numpy().ravel())
    return np.concatenate(fields), np.concatenate(phase_increment), np.concatenate(envelopes)


def visible_metrics(fields, increment, data, physics, config, groups):
    error = fields-data.targets
    positive = data.coordinates[:, 2] > physics.time_start
    initial = physics.initial_phase(tensor(data.coordinates)).numpy().ravel()
    eps = config["phase_logit_epsilon"]
    def logit(value):
        value = np.clip(value, eps, 1-eps)
        return np.log(value)-np.log1p(-value)
    desired = logit(data.targets[:, 2])-logit(initial)
    squared = ((increment-desired)/config["phase_logit_divisor"])**2
    gp = data.prob*positive
    phase_logit = float(np.dot(gp, squared)/gp.sum())
    if data.has_interface:
        phase_logit = .5*phase_logit+.5*float(np.dot(data.endpoint_prob, squared)/data.endpoint_prob.sum())
    return {"V_normalized_rms": weighted_rms(error[:, 0], data.prob)/physics.waveform_amplitude,
            "T_normalized_rms": {name: weighted_rms(error[:, 1], data.prob, mask)/physics.theta_transition
                                 for name, mask in groups.items()},
            "phase_raw_visible_rms": weighted_rms(error[:, 2], data.prob, positive),
            "phase_logit_objective": phase_logit,
            "finite": bool(np.isfinite(fields).all())}


def s0(root=RUN):
    root = Path(root)
    if (root/"s0.json").exists():
        raise FileExistsError("S0 already exists; reuse its evidence")
    root.mkdir(parents=True, exist_ok=True)
    local = ROOT/"outputs/runs/20260910-lf11-sparse-metric-sprint"
    public = ROOT/"paper/paper_v24/evidence"
    bundle = local/"input/sparse.npz"
    parent = local/"formal/warm_start/checkpoint.pt"
    if not bundle.is_file():
        bundle = public/"input/sparse.npz"
    if not parent.is_file():
        parent = public/"formal/warm_start/checkpoint.pt"
    config = json.loads((ROOT/"configs/phk_v23/lf11_sprint.json").read_text(encoding="utf-8"))
    # Freeze the strata and admission thresholds before opening target fields.
    contract = {"schema_id": "lf11-followup-s0-v1", "recorded_utc": now(),
                "source_commit": "6412dbf3c766207dfb5f586a94bac8eaa0f247d5",
                "sparse": str(bundle.relative_to(ROOT)), "parent": str(parent.relative_to(ROOT)),
                "strata": {"all": "original full global observation measure including analytic IC",
                           "heating": "t>0 and known U(t)>0; conditional global measure",
                           "off": "t>0 and known U(t)=0; conditional global measure"},
                "thresholds": {"T_all": .02, "T_heating": .05, "T_off": .05, "V": .005,
                               "phase_relative_noninferiority": .05},
                "budget": {"S1_Adam": 1200, "S1_fixed_evaluations": 400,
                           "main_Adam": 3200, "main_fixed_evaluations": 800,
                           "all_Adam": 6200, "all_fixed_evaluations": 1400},
                "information_role": "previously exposed nominal training/development observations",
                "stop_if": "any temperature lower bound exceeds its frozen admission threshold"}
    save_json(root/"frozen_contract.json", contract)
    torch.set_num_threads(4)
    model = build_model(config)
    state = torch.load(parent, map_location="cpu", weights_only=False)
    model.load_state_dict(state["model_state_dict"])
    model.eval()
    data = SparseData(bundle)
    groups = strata(data, model.physics)
    q = data.coordinates
    upper = temperature_envelope(q, model.temperature_scale, model.startup_time,
                                 model.physics.time_start, model.physics.z_min, model.physics.z_max)
    gap = interval_distance(data.targets[:, 1], upper)
    lower = {name: weighted_rms(gap, data.prob, mask)/model.physics.theta_transition
             for name, mask in groups.items()}
    fields, increment, actual_upper = predict_visible(model, data)
    parent_metrics = visible_metrics(fields, increment, data, model.physics, config, groups)
    largest = int(np.argmax(gap))
    counts = {name: {"points": int(mask.sum()),
                     "outside_envelope": int(np.count_nonzero((gap > 0)&mask)),
                     "global_measure_mass": float(data.prob[mask].sum())}
              for name, mask in groups.items()}
    fails = [name for name in groups if lower[name] > contract["thresholds"]["T_"+name]]
    result = {"schema_id": "lf11-followup-s0-result-v1", "recorded_utc": now(),
              "evidence_status": "VERIFIED", "outcome": "S0_REPRESENTATION_INFEASIBLE" if fails else "S0_RANGE_BOUND_DOES_NOT_PRECLUDE_S1",
              "failed_strata": fails, "temperature_normalized_rms_lower_bound": lower,
              "parent_visible_metrics": parent_metrics, "stratum_counts": counts,
              "maximum_temperature_gap": float(gap[largest]),
              "maximum_gap_witness": {"coordinate_xzt": q[largest].tolist(),
                                      "observed_T": float(data.targets[largest, 1]),
                                      "envelope": float(upper[largest])},
              "analytic_vs_actual_envelope_max_difference": float(np.max(np.abs(actual_upper-upper))),
              "input_identity": {"sparse_sha256": digest(bundle), "parent_sha256": digest(parent)},
              "optimizer_updates": 0, "fixed_optimization_evaluations": 0,
              "reference_read": False, "cloud_instance_started": False,
              "scope": "Pointwise function-class lower bound on existing visible observations; not a trained endpoint or continuum claim"}
    save_json(root/"s0.json", result)
    np.savez_compressed(root/"s0-visible.npz", coordinates=q, targets=data.targets,
                        weights=data.prob, envelope=upper, interval_distance=gap,
                        parent_fields=fields, parent_phase_increment=increment)
    print(json.dumps(result, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=RUN)
    parser.add_argument("--stage", choices=["s0"], default="s0")
    args = parser.parse_args()
    s0(args.root)


if __name__ == "__main__":
    main()
