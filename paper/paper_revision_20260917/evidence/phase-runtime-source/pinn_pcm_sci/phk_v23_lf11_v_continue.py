"""One authorized V-only continuation; existing T/phase and sparse data stay fixed.

L-BFGS is the PyTorch 2.5.1 implementation (BSD-3-Clause); the budget/rollback
wrapper extends the repository's LF11 follow-up wrapper with history resumption
and an accepted-state fit gate. This is fitting, not a new PINN method.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import numpy as np
import torch
from .phk_v23_lf11 import ROOT, SparseData, save_json, now
from .phk_v23_lf11_followup import predict_visible
from .phk_v23_lf11_followup_fit import (
    EvaluationLimit, fit_model, full_head_objective, fit_metrics, admission,
)

RUN = ROOT/"outputs/runs/20260912-lf11-v-pde-increment"
CONFIG = ROOT/"configs/phk_v23/lf11_v_pde_sprint.json"

def continued_lbfgs(parameters, objective, limit, log=None, *, optimizer_state=None, accepted_loss_gate=None):
    """objective(backward=True) returns the fixed complete loss and derivatives.

    max_iter=1 exposes every accepted step. Explicit closure accounting handles
    the fact that PyTorch's max_eval does not cap strong-Wolfe evaluations.
    """
    parameters = list(parameters)
    optimizer = torch.optim.LBFGS(parameters, lr=1., max_iter=1, max_eval=32,
                                  tolerance_grad=1e-10, tolerance_change=1e-14,
                                  history_size=50, line_search_fn="strong_wolfe")
    if optimizer_state is not None:
        optimizer.load_state_dict(copy.deepcopy(optimizer_state))
    initial_loss = None
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
            nonlocal used, initial_loss
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
            if initial_loss is None:
                initial_loss = float(loss.detach())
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
        if accepted_loss_gate is not None and new_loss <= accepted_loss_gate:
            terminal = "FIRST_ACCEPTED_V_FIT_GATE"
            break
        if float(gradient.abs().max()) <= 1e-10:
            terminal = "GRADIENT_CONVERGED"
            break
    return {"evaluations": used, "accepted_steps": accepted, "termination": terminal,
            "last_accepted_loss": last_loss if last_loss is not None else initial_loss,
            "initial_loss": initial_loss, "history_resumed": optimizer_state is not None,
            "first_gate_accepted_evaluation": used if terminal == "FIRST_ACCEPTED_V_FIT_GATE" else None}, optimizer



def history_compatibility(model, endpoint, stage):
    names = ["heads.potential."+n for n, _ in model.heads["potential"].named_parameters()]
    a, b = endpoint["model_state_dict"], stage["model_state_dict"]
    state = stage.get("optimizer_state_dict")
    checks = {
        "V_parameters_exact": all(n in b and torch.equal(a[n], b[n]) for n in names),
        "V_parameter_order": [n for n in b if n in names] == names,
        "same_sparse_identity": endpoint["sparse_sha256"] == stage["sparse_sha256"],
        "optimizer_type": stage.get("optimizer_type") == "LBFGS",
    }
    groups = state["param_groups"] if state else []
    checks["parameter_group"] = len(groups) == 1 and len(groups[0]["params"]) == len(names)
    expected = dict(lr=1., max_iter=1, max_eval=32, tolerance_grad=1e-10,
                    tolerance_change=1e-14, history_size=50, line_search_fn="strong_wolfe")
    checks["optimizer_recipe"] = bool(groups) and all(groups[0].get(k) == v for k,v in expected.items())
    vectors = sum(p.numel() for p in model.heads["potential"].parameters())
    tensors = []
    def collect(x):
        if torch.is_tensor(x): tensors.append(x)
        elif isinstance(x, dict):
            for v in x.values(): collect(v)
        elif isinstance(x, (list, tuple)):
            for v in x: collect(v)
    if state: collect(state["state"])
    checks["finite_FP64_history"] = bool(tensors) and all(t.dtype == torch.float64 and torch.isfinite(t).all().item() for t in tensors)
    checks["history_shapes"] = bool(tensors) and all(t.numel() in (1, vectors) for t in tensors)
    return {"checks": checks, "compatible": all(checks.values()),
            "parameter_names": names, "V_parameter_count": vectors}

def run(root=RUN):
    root = Path(root)
    folder = root/"v_continue"
    folder.mkdir(exist_ok=False)
    contract = json.loads(CONFIG.read_text(encoding="utf-8"))
    config = json.loads((ROOT/contract["base_config"]).read_text(encoding="utf-8"))
    torch.set_num_threads(4)
    data = SparseData(ROOT/contract["sparse"])
    endpoint = torch.load(ROOT/contract["parent"], map_location="cpu", weights_only=False)
    stage = torch.load(ROOT/contract["V_optimizer"], map_location="cpu", weights_only=False)
    model = fit_model(config, endpoint["model_state_dict"], endpoint["temperature_adapter"])
    compatibility = history_compatibility(model, endpoint, stage)
    save_json(folder/"compatibility.json", compatibility)
    before = fit_metrics(model, data, config)
    for n,p in model.named_parameters(): p.requires_grad_(n.startswith("heads.potential."))
    with (folder/"telemetry.jsonl").open("x", encoding="utf-8") as f:
        def record(item):
            f.write(json.dumps(item, allow_nan=False)+"\n"); f.flush()
            if item["accepted_steps"] == 1 or item["accepted_steps"] % 10 == 0:
                print(json.dumps(item), flush=True)
        result, optimizer = continued_lbfgs(
            model.heads["potential"].parameters(),
            lambda: full_head_objective(model, data, "potential"),
            contract["V_evaluations"], record,
            optimizer_state=stage["optimizer_state_dict"] if compatibility["compatible"] else None,
            accepted_loss_gate=contract["visible_V_gate"]**2/3)
    after = fit_metrics(model, data, config)
    same = all(torch.equal(endpoint["model_state_dict"][n],v)
               for n,v in model.state_dict().items() if not n.startswith("heads.potential."))
    if not same: raise RuntimeError("V-only continuation changed a non-V state")
    old_s0 = json.loads((ROOT/contract["original_s0"]).read_text(encoding="utf-8"))
    thresholds = dict(V=.005,T_all=.02,T_heating=.05,T_off=.05,phase_relative_noninferiority=.05)
    gate = admission(after, old_s0["parent_visible_metrics"], thresholds)
    for p in model.parameters(): p.requires_grad_(True)
    payload = dict(schema_id="lf11-v-continued-checkpoint-v1", role="repaired_parent" if gate["passed"] else "V_fixed_endpoint",
                   model_state_dict=model.state_dict(), config=config,
                   temperature_adapter=endpoint["temperature_adapter"],
                   sparse_sha256=endpoint["sparse_sha256"], optimizer_state_dict=optimizer.state_dict(),
                   optimizer_type="LBFGS_V_ONLY", counters=dict(Adam_updates=0,fixed_objective_gradient_evaluations=result["evaluations"]))
    torch.save(payload, folder/"checkpoint.pt")
    fields, increment, envelope = predict_visible(model, data)
    np.savez_compressed(folder/"visible.npz", fields=fields, phase_increment=increment, envelope=envelope)
    result.update(schema_id="lf11-v-continuation-result-v1", recorded_utc=now(),
                  before=before, after=after, admission=gate, non_V_state_exactly_preserved=same,
                  compatibility=compatibility, reference_read=False, cloud_instance_started=False,
                  outcome="V_ADMITTED_TO_MATCHED_PHYSICS" if gate["passed"] else "V_BOUNDED_CONTINUATION_NOT_ADMITTED")
    save_json(folder/"result.json",result)
    print(json.dumps({"V_CONTINUATION_COMPLETE": result},allow_nan=False),flush=True)
    return result

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,default=RUN)
    run(p.parse_args().root)
