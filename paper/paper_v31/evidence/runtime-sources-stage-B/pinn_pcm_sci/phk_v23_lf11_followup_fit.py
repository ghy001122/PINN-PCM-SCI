"""Budgeted sparse-only fitting for the authorized LF11 follow-up.

Uses PyTorch Adam/L-BFGS. L-BFGS evaluations see the complete fixed weighted
observation component. Interrupted line searches restore the last accepted
parameters AND optimizer state; trial parameters never become endpoints.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn

from .phk_v22r_pinn import ModifiedMLP, range_preserving_exact_top_fraction
from .phk_v23_lf11 import ROOT, SparseData, build_model, now, save_json, tensor
from .phk_v23_lf11_followup import RUN, predict_visible, strata, visible_metrics


class TemperatureAdapter(nn.Module):
    """One optional smooth additive latent adapter; zero at insertion."""
    def __init__(self, base):
        super().__init__()
        self.base = base
        self.register_buffer("frequencies", torch.tensor([
            [.5, 0, 0], [1, 0, 0], [2, 0, 0], [0, .5, 0], [0, 1, 0],
            [0, 0, .5], [0, 0, 1], [0, 0, 2], [0, 0, 4]], dtype=torch.float64))
        self.residual = ModifiedMLP(21, hidden_width=32, hidden_layers=2).double()
        nn.init.zeros_(self.residual.output.weight)
        nn.init.zeros_(self.residual.output.bias)

    def forward(self, normalized):
        angles = 2*torch.pi*(normalized@self.frequencies.T)
        return self.base(normalized)+self.residual(torch.cat(
            [normalized, torch.sin(angles), torch.cos(angles)], dim=1))


def fit_model(config, state=None, adapter=False):
    model = build_model(config)
    if adapter:
        model.heads["temperature"] = TemperatureAdapter(model.heads["temperature"])
    if state is not None:
        model.load_state_dict(state)
    return model


def head_field(model, name, q):
    normalized = model.physics.normalize(q)
    latent = model.heads[name](model.encoders[name](normalized))
    zf = (q[:, 1:2]-model.physics.z_min)/(model.physics.z_max-model.physics.z_min)
    if name == "potential":
        return (model.physics.waveform(q[:, 2:3]) *
                range_preserving_exact_top_fraction(latent, zf)).ravel()
    if name == "temperature":
        return (model.temperature_scale*(1-torch.exp(
            -(q[:, 2:3]-model.physics.time_start)/model.startup_time)) *
                (1-zf)*torch.sigmoid(latent)).ravel()
    raise ValueError(name)


class EvaluationLimit(Exception):
    pass


def bounded_lbfgs(parameters, objective, limit, log=None):
    """objective(backward=True) returns the fixed complete loss and derivatives.

    max_iter=1 exposes every accepted step. Explicit closure accounting handles
    the fact that PyTorch's max_eval does not cap strong-Wolfe evaluations.
    """
    parameters = list(parameters)
    optimizer = torch.optim.LBFGS(parameters, lr=1., max_iter=1, max_eval=32,
                                  tolerance_grad=1e-10, tolerance_change=1e-14,
                                  history_size=50, line_search_fn="strong_wolfe")
    used, accepted = 0, 0
    terminal = "EVALUATION_BUDGET_EXHAUSTED"
    last_loss = None
    def flatten(items):
        return torch.cat([p.detach().reshape(-1) for p in items])
    while used < limit:
        snapshot = [p.detach().clone() for p in parameters]
        optimizer_snapshot = copy.deepcopy(optimizer.state_dict())
        evaluations = []
        def closure():
            nonlocal used
            if used >= limit:
                raise EvaluationLimit()
            used += 1
            optimizer.zero_grad(set_to_none=True)
            loss = objective()
            if not torch.isfinite(loss):
                raise FloatingPointError("nonfinite fixed objective")
            gradient = flatten([p.grad if p.grad is not None else torch.zeros_like(p)
                                for p in parameters])
            if not torch.isfinite(gradient).all():
                raise FloatingPointError("nonfinite fixed gradient")
            evaluations.append((flatten(parameters).clone(), float(loss.detach()), gradient.clone()))
            return loss
        def restore():
            with torch.no_grad():
                for p, previous in zip(parameters, snapshot):
                    p.copy_(previous)
            optimizer.load_state_dict(optimizer_snapshot)
            optimizer.zero_grad(set_to_none=True)
        try:
            optimizer.step(closure)
        except EvaluationLimit:
            restore()
            terminal = "EVALUATION_BUDGET_EXHAUSTED_TRIAL_ROLLED_BACK"
            break
        except FloatingPointError:
            restore()
            terminal = "NONFINITE_LINE_SEARCH_TRIAL_ROLLED_BACK"
            break
        current = flatten(parameters)
        matches = [item for item in evaluations if torch.equal(item[0], current)]
        if not matches:
            restore()
            raise RuntimeError("accepted parameters have no evaluated objective")
        _, new_loss, gradient = matches[-1]
        start, start_loss, start_grad = evaluations[0]
        state = optimizer.state[parameters[0]]
        if torch.equal(start, current):
            terminal = "GRADIENT_CONVERGED" if float(gradient.abs().max()) <= 1e-10 else "NO_ACCEPTED_PROGRESS"
            last_loss = new_loss
            break
        direction, step = state["d"], float(state["t"])
        gtd = float(start_grad@direction)
        armijo = new_loss <= start_loss+1e-4*step*gtd+1e-15
        curvature = abs(float(gradient@direction)) <= -.9*gtd+1e-15
        if not (armijo and curvature):
            restore()
            terminal = "LINE_SEARCH_FAILED_WOLFE_TRIAL_ROLLED_BACK"
            break
        accepted += 1
        last_loss = new_loss
        if log is not None:
            log({"evaluations": used, "accepted_steps": accepted, "loss": new_loss,
                 "gradient_max": float(gradient.abs().max()), "wolfe_verified": True})
        if float(gradient.abs().max()) <= 1e-10:
            terminal = "GRADIENT_CONVERGED"
            break
    return {"evaluations": used, "accepted_steps": accepted, "termination": terminal,
            "last_accepted_loss": last_loss}, optimizer


def full_head_objective(model, data, name, chunk=4096):
    col = {"potential": 0, "temperature": 1}[name]
    scale = model.physics.waveform_amplitude if col == 0 else model.physics.theta_transition
    total = torch.zeros((), dtype=torch.float64)
    for lo in range(0, len(data.coordinates), chunk):
        q = tensor(data.coordinates[lo:lo+chunk])
        target = tensor(data.targets[lo:lo+chunk, col])
        weight = tensor(data.prob[lo:lo+chunk]/data.prob.sum())
        value = torch.dot(weight, ((head_field(model, name, q)-target)/scale).square())/3
        value.backward()
        total += value.detach()
    return total


def fit_metrics(model, data, config):
    fields, increment, _ = predict_visible(model, data)
    return visible_metrics(fields, increment, data, model.physics, config, strata(data, model.physics))


def admission(metrics, original, thresholds):
    predicates = {"finite": metrics["finite"],
                  "V": metrics["V_normalized_rms"] <= thresholds["V"]}
    for name in ("all", "heating", "off"):
        predicates["T_"+name] = metrics["T_normalized_rms"][name] <= thresholds["T_"+name]
    for name in ("phase_raw_visible_rms", "phase_logit_objective"):
        predicates[name] = metrics[name] <= original[name]*(1+thresholds["phase_relative_noninferiority"])
    return {"passed": all(predicates.values()), "predicates": predicates}


def s1(root=RUN):
    root = Path(root)
    folder = root/"s1"
    folder.mkdir(exist_ok=False)
    contract = json.loads((root/"frozen_contract.json").read_text(encoding="utf-8"))
    s0_result = json.loads((root/"s0.json").read_text(encoding="utf-8"))
    if s0_result["outcome"] != "S0_RANGE_BOUND_DOES_NOT_PRECLUDE_S1":
        raise ValueError("S0 forbids fitting")
    config = json.loads((ROOT/"configs/phk_v23/lf11_sprint.json").read_text(encoding="utf-8"))
    plan = {"recorded_utc": now(), "base": "600 Adam V/T then potential 80 and temperature 120 fixed L-BFGS evaluations",
            "conditional": "If not admitted: at most 600 more Adam V/T; one zero-initialized T latent Fourier residual if T fails; potential up to 40 then T remainder to cumulative 400 fixed evaluations",
            "phase": "unchanged during pure observation fitting; restore joint trainability before any S2 PDE",
            "Adam": {"lr": .001, "betas": [.9, .999], "eps": 1e-8, "clip": 10., "batch": 1024},
            "LBFGS": {"fixed_full_weighted_component": True, "weight": "global_probability / sum / 3",
                       "history_size": 50, "line_search": "strong_wolfe_verified", "no_gradient_clipping": True},
            "adapter": {"type": "additive temperature latent only", "width": 32, "layers": 2,
                        "normalized_coordinate_frequencies": {"x": [.5, 1, 2], "z": [.5, 1], "t": [.5, 1, 2, 4]},
                        "initial_function": "exactly unchanged through zero final layer"},
            "source": "PyTorch Adam/LBFGS; smooth Fourier-feature additive adaptation of the existing ModifiedMLP, not claimed novel"}
    save_json(folder/"frozen_fit_plan.json", plan)
    torch.set_num_threads(4)
    data = SparseData(ROOT/contract["sparse"])
    inherited = torch.load(ROOT/contract["parent"], map_location="cpu", weights_only=False)
    model = fit_model(config, inherited["model_state_dict"])
    for p in model.heads["phase"].parameters():
        p.requires_grad_(False)
    rng = np.random.default_rng(61117)
    counters = {"Adam_updates": 0, "fixed_objective_gradient_evaluations": 0}
    history = []
    adapter_used = False
    stream = (folder/"telemetry.jsonl").open("x", encoding="utf-8")
    def record(item):
        item = {"recorded_utc": now(), **counters, **item}
        stream.write(json.dumps(item, allow_nan=False)+"\n")
        stream.flush()
        print(json.dumps(item, allow_nan=False), flush=True)
    def checkpoint(role, optimizer=None):
        torch.save({"schema_id": "lf11-followup-fit-checkpoint-v1", "role": role,
                    "model_state_dict": model.state_dict(), "config": config,
                    "temperature_adapter": adapter_used, "counters": dict(counters),
                    "optimizer_state_dict": optimizer.state_dict() if optimizer else None,
                    "optimizer_type": type(optimizer).__name__ if optimizer else None,
                    "sparse_sha256": s0_result["input_identity"]["sparse_sha256"]}, folder/f"{role}.pt")
    def adam(count, role):
        params = [p for p in model.parameters() if p.requires_grad]
        optimizer = torch.optim.Adam(params, lr=.001, betas=(.9, .999), eps=1e-8)
        for step in range(1, count+1):
            indices = rng.choice(len(data.prob), 1024, p=data.prob)
            q = tensor(data.coordinates[indices])
            optimizer.zero_grad(set_to_none=True)
            loss = torch.zeros((), dtype=torch.float64)
            for name, col, scale in (("potential", 0, .72), ("temperature", 1, .45)):
                loss = loss+((head_field(model, name, q)-tensor(data.targets[indices, col]))/scale).square().mean()/3
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 10., error_if_nonfinite=True)
            optimizer.step()
            counters["Adam_updates"] += 1
            if step % 100 == 0 or step == 1:
                record({"stage": role, "stage_step": step, "sample_loss": float(loss.detach())})
        checkpoint(role, optimizer)
    def lbfgs(name, limit, role):
        start = counters["fixed_objective_gradient_evaluations"]
        def log(item):
            if item["accepted_steps"] % 10 == 0 or item["accepted_steps"] == 1:
                record({"stage": role, "head": name, "local_evaluation": item["evaluations"],
                        "cumulative_evaluation": start+item["evaluations"], **item})
        result, optimizer = bounded_lbfgs(model.heads[name].parameters(),
            lambda: full_head_objective(model, data, name), limit, log)
        counters["fixed_objective_gradient_evaluations"] += result["evaluations"]
        history.append({"stage": role, "head": name, **result})
        checkpoint(role, optimizer)
        record({"stage": role, "head": name, "completion": result})
    adam(600, "base_adam")
    lbfgs("potential", 80, "base_lbfgs_V")
    lbfgs("temperature", 120, "base_lbfgs_T")
    first = fit_metrics(model, data, config)
    first_gate = admission(first, s0_result["parent_visible_metrics"], contract["thresholds"])
    save_json(folder/"base_fit_metrics.json", {"metrics": first, "admission": first_gate})
    record({"stage": "base_fit_assessment", "metrics": first, "admission": first_gate})
    if not first_gate["passed"]:
        if any(not first_gate["predicates"]["T_"+name] for name in ("all", "heating", "off")):
            torch.manual_seed(61117)
            before = predict_visible(model, data)[0]
            model.heads["temperature"] = TemperatureAdapter(model.heads["temperature"])
            adapter_used = True
            after = predict_visible(model, data)[0]
            if not np.array_equal(before, after):
                raise RuntimeError("adapter changed initial represented function")
            save_json(folder/"adapter-insertion.json", {"exact_function_preserved": True,
                       "max_difference": float(np.max(np.abs(after-before))), "recorded_utc": now()})
        adam(600, "refinement_adam")
        if not first_gate["predicates"]["V"]:
            lbfgs("potential", min(40, 400-counters["fixed_objective_gradient_evaluations"]), "refinement_lbfgs_V")
        lbfgs("temperature", 400-counters["fixed_objective_gradient_evaluations"], "refinement_lbfgs_T")
    final = fit_metrics(model, data, config)
    gate = admission(final, s0_result["parent_visible_metrics"], contract["thresholds"])
    for p in model.parameters():
        p.requires_grad_(True)
    checkpoint("fixed_fit_endpoint")
    fields, increment, upper = predict_visible(model, data)
    np.savez_compressed(folder/"fixed-visible.npz", fields=fields, phase_increment=increment, envelope=upper)
    repeated = fit_metrics(model, data, config)
    result = {"schema_id": "lf11-followup-s1-v1", "recorded_utc": now(),
              "outcome": "S1_ADMITTED_TO_MATCHED_PHYSICS" if gate["passed"] else "S1_BOUNDED_FIT_NOT_ADMITTED",
              "metrics": final, "admission": gate, "counters": counters,
              "fixed_full_metrics_exactly_repeatable": repeated == final,
              "temperature_adapter_used": adapter_used, "optimizer_terminations": history,
              "reference_read": False, "cloud_instance_started": False,
              "phase_unchanged": all(torch.equal(inherited["model_state_dict"][k], v) for k,v in model.state_dict().items() if k.startswith("heads.phase.")),
              "checkpoint": "s1/fixed_fit_endpoint.pt"}
    save_json(folder/"result.json", result)
    record({"stage": "S1_COMPLETE", **result})
    stream.close()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=RUN)
    args = parser.parse_args()
    s1(args.root)


if __name__ == "__main__":
    main()
