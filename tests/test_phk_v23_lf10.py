from __future__ import annotations

import copy
import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from pinn_pcm_sci import phk_v23_lf10 as lf10


def _adam_pair() -> tuple[torch.nn.Linear, torch.optim.Adam]:
    model = torch.nn.Linear(2, 1, bias=True, dtype=torch.float64)
    with torch.no_grad():
        model.weight.copy_(torch.tensor([[0.4, -0.2]], dtype=torch.float64))
        model.bias.copy_(torch.tensor([0.1], dtype=torch.float64))
    optimizer = torch.optim.Adam(
        model.parameters(), lr=1.25e-4, betas=(0.9, 0.999), eps=1e-8,
        weight_decay=0.0, amsgrad=False,
    )
    return model, optimizer


def test_extract_adam_proposal_matches_real_step_but_leaves_parameters_pre_step() -> None:
    model, optimizer = _adam_pair()
    control = copy.deepcopy(model)
    control_optimizer = torch.optim.Adam(
        control.parameters(), lr=1.25e-4, betas=(0.9, 0.999), eps=1e-8,
        weight_decay=0.0, amsgrad=False,
    )
    x = torch.tensor([[0.3, -0.7], [0.2, 0.5]], dtype=torch.float64)
    y = torch.tensor([[0.8], [-0.1]], dtype=torch.float64)
    before = tuple(parameter.detach().clone() for parameter in model.parameters())

    proposal = lf10.extract_adam_proposed_update(
        model, optimizer, torch.mean((model(x) - y).square()),
        parameter_groups={"all": tuple(model.parameters())},
    )
    control_optimizer.zero_grad(set_to_none=True)
    torch.mean((control(x) - y).square()).backward()
    torch.nn.utils.clip_grad_norm_(tuple(control.parameters()), 10.0)
    control_optimizer.step()

    expected = tuple(
        actual.detach() - initial
        for actual, initial in zip(control.parameters(), before, strict=True)
    )
    assert all(torch.equal(actual, initial) for actual, initial in zip(model.parameters(), before, strict=True))
    assert all(torch.equal(actual, wanted) for actual, wanted in zip(proposal.updates["all"], expected, strict=True))
    assert all(int(optimizer.state[p]["step"].item()) == 1 for p in model.parameters())
    assert all(p.grad is None for p in model.parameters())


@pytest.mark.parametrize(
    ("u0", "constraints", "expected"),
    [
        ([0.2, -0.1], [], [0.2, -0.1]),
        ([2.0, 0.0], [([1.0, 0.0], 0.5)], [0.5, 0.0]),
        ([2.0, 2.0], [([1.0, 0.0], 0.5), ([0.0, 1.0], 0.25)], [0.5, 0.25]),
    ],
)
def test_qp_projection_is_nearest_feasible_update(u0, constraints, expected) -> None:
    proposal = torch.tensor(u0, dtype=torch.float64)
    rows = tuple(
        lf10.LinearConstraint(
            name=f"c{index}", row=torch.tensor(row, dtype=torch.float64), rhs=rhs,
            current=1.0, bound=1.0, remaining_steps=1,
        )
        for index, (row, rhs) in enumerate(constraints)
    )
    result = lf10.project_update_nearest(proposal, rows)
    assert result.feasible
    assert torch.allclose(result.update, torch.tensor(expected, dtype=torch.float64), atol=1e-12, rtol=0.0)
    assert float(torch.linalg.vector_norm(result.update)) <= float(torch.linalg.vector_norm(proposal)) + 1e-12
    assert all(value <= 1e-10 for value in result.constraint_lhs_minus_rhs.values())


def test_qp_reports_norm_cap_infeasible_instead_of_changing_identity() -> None:
    result = lf10.project_update_nearest(
        torch.tensor([0.1], dtype=torch.float64),
        (lf10.LinearConstraint("repair", torch.tensor([1.0], dtype=torch.float64), -1.0, 1.2, 1.0, 1),),
    )
    assert not result.feasible
    assert result.reason == "NORM_CAP_BREAKS_FEASIBILITY"


def test_ctrl_and_proj_share_adam_proposal_and_audit_gradients_do_not_touch_grad_slots() -> None:
    model, optimizer = _adam_pair()
    parameters = tuple(model.parameters())
    x = torch.tensor([[0.5, -0.3]], dtype=torch.float64)
    proposal = lf10.extract_adam_proposed_update(
        model, optimizer, model(x).square().mean(), parameter_groups={"potential": parameters},
    )
    audit = (model(x) - 0.2).square().mean()
    constraints, values = lf10.linearize_head_constraints(
        {"potential": {"CV": audit}},
        {"CV": 1.0}, {"CV": 1.20}, {"potential": parameters}, remaining_steps=25,
    )
    assert all(parameter.grad is None for parameter in parameters)
    ctrl = lf10.resolve_head_updates(lf10.CTRL, proposal.updates, constraints)
    proj = lf10.resolve_head_updates(lf10.PROJ, proposal.updates, constraints)
    assert all(torch.equal(a, b) for a, b in zip(ctrl.updates["potential"], proposal.updates["potential"], strict=True))
    assert values["CV"] >= 0.0
    assert proj.feasible


def test_batch_matched_dev_r_baselines_make_all_ratios_one_and_zero_feasible() -> None:
    parameter = torch.nn.Parameter(torch.tensor([0.3], dtype=torch.float64))
    baselines = {"CV": 2.0, "CT": 3.0, "Cphase": 4.0, "Ctopology_smooth_surrogate": 5.0}
    objectives = {
        "potential": {"CV": parameter.sum() * 0.0 + baselines["CV"]},
        "temperature": {"CT": parameter.sum() * 0.0 + baselines["CT"]},
        "phase": {
            "Cphase": parameter.sum() * 0.0 + baselines["Cphase"],
            "Ctopology_smooth_surrogate": parameter.sum() * 0.0 + baselines["Ctopology_smooth_surrogate"],
        },
    }
    constraints, ratios = lf10.linearize_head_constraints(
        objectives, baselines, lf10.PROJECTION_BOUNDS,
        {"potential": (parameter,), "temperature": (parameter,), "phase": (parameter,)},
        remaining_steps=25,
    )
    assert ratios == {name: 1.0 for name in baselines}
    assert all(constraint.rhs >= 0.0 for rows in constraints.values() for constraint in rows)
    assert all(
        lf10.project_update_nearest(torch.zeros(1, dtype=torch.float64), rows).feasible
        for rows in constraints.values()
    )


def test_materialized_ledger_binds_and_returns_step_matched_audit_baselines(tmp_path: Path) -> None:
    arrays: dict[str, np.ndarray] = {}
    for name in lf10.ledger_array_names():
        if name == "audit_baselines":
            value = np.asarray([[2.0, 3.0, 4.0, 5.0]], dtype=np.float64)
        elif name.endswith("sha256"):
            value = np.asarray([b"A" * 64], dtype="S64")
        elif name.endswith("active_windows"):
            value = np.asarray([4], dtype=np.int16)
        elif name.endswith("refreshed"):
            value = np.asarray([True], dtype=np.bool_)
        else:
            value = np.zeros((1, 1, 3), dtype=np.float64)
        arrays[name] = value
    ledger_path = tmp_path / "ledger.npz"
    manifest_path = tmp_path / "manifest.json"
    np.savez_compressed(ledger_path, **arrays)
    records = {
        name: {"shape": list(value.shape), "dtype": value.dtype.str, "sha256": lf10.array_sha256(name, value)}
        for name, value in arrays.items()
    }
    semantic = lf10.semantic_ledger_sha256({name: value["sha256"] for name, value in records.items()})
    manifest_path.write_text(json.dumps({
        "schema_id": "phk-v23-lf10-materialized-ledger-manifest-v1",
        "task_id": lf10.TASK_ID, "arrays": records, "semantic_sha256": semantic,
        "streams": {},
    }), encoding="utf-8")
    ledger = lf10.MaterializedLF10Ledger(
        ledger_path, manifest_path,
        qualification={"ledger": {"semantic_sha256": semantic}},
    )
    assert ledger.audit_baselines(1) == {
        "CV": 2.0, "CT": 3.0, "Cphase": 4.0,
        "Ctopology_smooth_surrogate": 5.0,
    }


def test_phase_schedule_freezes_through_550_then_unfreezes_without_optimizer_reset() -> None:
    class TinyHeads(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.encoders = torch.nn.ModuleDict({name: torch.nn.Linear(1, 1) for name in ("potential", "temperature", "phase")})
            self.heads = torch.nn.ModuleDict({name: torch.nn.Linear(1, 1) for name in ("potential", "temperature", "phase")})

    model = TinyHeads()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    optimizer_id = id(optimizer)
    lf10.configure_phase_for_next_accepted_update(model, accepted_updates=0)
    assert not any(p.requires_grad for p in lf10.field_parameter_groups(model, trainable_only=False)["phase"])
    lf10.configure_phase_for_next_accepted_update(model, accepted_updates=550)
    assert all(p.requires_grad for p in lf10.field_parameter_groups(model, trainable_only=False)["phase"])
    assert id(optimizer) == optimizer_id


def test_frozen_phase_is_audited_but_absent_from_projection_and_update_telemetry() -> None:
    potential = torch.nn.Parameter(torch.tensor([1.0], dtype=torch.float64))
    temperature = torch.nn.Parameter(torch.tensor([1.0], dtype=torch.float64))
    phase = torch.nn.Parameter(torch.tensor([1.0], dtype=torch.float64), requires_grad=False)
    baselines = {"CV": 1.0, "CT": 1.0, "Cphase": 1.0, "Ctopology_smooth_surrogate": 1.0}
    constraints, ratios = lf10.linearize_head_constraints(
        {
            "potential": {"CV": potential.square().sum()},
            "temperature": {"CT": temperature.square().sum()},
            "phase": {
                "Cphase": phase.square().sum(),
                "Ctopology_smooth_surrogate": phase.square().sum(),
            },
        },
        baselines,
        lf10.PROJECTION_BOUNDS,
        {"potential": (potential,), "temperature": (temperature,), "phase": ()},
        remaining_steps=25,
    )
    proposed = {
        "potential": (torch.tensor([0.01], dtype=torch.float64),),
        "temperature": (torch.tensor([0.01], dtype=torch.float64),),
        "phase": (),
    }
    resolved = lf10.resolve_head_updates(lf10.PROJ, proposed, constraints)
    geometry = lf10.direction_geometry(proposed, constraints, resolved.projections)

    assert set(ratios) == set(baselines)
    assert set(constraints) == {"potential", "temperature"}
    assert "phase" not in resolved.updates
    assert "phase" not in resolved.projections
    assert "phase" not in geometry


@pytest.mark.parametrize(
    ("ctrl", "proj", "outcome"),
    [
        (200, 200, "PROJECTION_NOT_LOAD_BEARING"),
        (175, 200, "FEASIBLE_DIRECTION_PROJECTION_SUPPORTED"),
        (200, 175, "PROJECTION_HARMFUL_OR_UNNECESSARY"),
        (175, 175, "NO_EXTENDED_FEASIBLE_PATH_FOUND"),
    ],
)
def test_direction_screen_adjudication_is_literal(ctrl: int, proj: int, outcome: str) -> None:
    arms = {
        lf10.CTRL: {"identity_valid": True, "accepted_updates": ctrl, "numerical_valid": True, "safety_gate": {"passed": True}, "J_ratio": 0.90},
        lf10.PROJ: {"identity_valid": True, "accepted_updates": proj, "numerical_valid": True, "safety_gate": {"passed": True}, "J_ratio": 0.90},
    }
    result = lf10.adjudicate_direction_screens(arms)
    assert result["feasible_direction_outcome"] == outcome
    if ctrl == 200:
        assert result["selected_arm"] == lf10.CTRL
    elif proj == 200:
        assert result["selected_arm"] == lf10.PROJ
    else:
        assert result["selected_arm"] is None


def test_stream_replication_aggregates_require_two_of_three_and_effect_size() -> None:
    interface = {
        "17": {"valid": True, "delta_Rmin": 0.089, "quality_preserved": True},
        "23": {"valid": True, "delta_Rmin": 0.040, "quality_preserved": True},
        "29": {"valid": True, "delta_Rmin": -0.005, "quality_preserved": False},
    }
    assert lf10.interface_replication_outcome(interface) == "INTERFACE_EFFECT_STREAM_REPLICATED"
    forgetting = {
        "17": {"valid": True, "J_ratio": 0.012, "event_missing_or_min_recall_le_half": True, "field_event_pareto": False},
        "23": {"valid": True, "J_ratio": 0.20, "event_missing_or_min_recall_le_half": True, "field_event_pareto": False},
        "29": {"valid": True, "J_ratio": 0.80, "event_missing_or_min_recall_le_half": False, "field_event_pareto": False},
    }
    assert lf10.forgetting_replication_outcome(forgetting) == "PHYSICS_FORGETTING_STREAM_REPLICATED"


def test_nonshared_track_failure_isolated_in_summary_status() -> None:
    tracks = lf10.isolate_track_results(
        {"direction": {"valid": False}, "interface": {"valid": True}, "forgetting": {"valid": True}}
    )
    assert tracks["completed"] == ["forgetting", "interface"]
    assert tracks["failed"] == ["direction"]
    assert tracks["campaign_may_continue"]


def test_mock_campaign_keeps_nonshared_replication_after_one_track_failure(monkeypatch, tmp_path: Path) -> None:
    inputs = {name: tmp_path / name for name in ("medium.npz", "lf3.pt", "devr.pt", "strong.npz", "lf10.npz", "lf10.json", "cpu.json")}
    for path in inputs.values():
        path.write_bytes(b"x")
    contracts = {
        "data": {
            "medium": {"sha256": "MEDIUM"},
            "LF3_T0": {"checkpoint_sha256": "LF3"},
            "DEV_R": {"checkpoint_path": "devr.pt", "checkpoint_sha256": "DEVR"},
            "strong_ledger": {"path": "strong.npz", "file_sha256": "STRONG", "fixed_blind_pool_sha256": "FIXED"},
        }
    }
    hashes = {inputs["medium.npz"]: "MEDIUM", inputs["lf3.pt"]: "LF3", inputs["devr.pt"]: "DEVR", inputs["strong.npz"]: "STRONG"}
    monkeypatch.setattr(lf10, "load_contracts", lambda: contracts)
    monkeypatch.setattr(lf10, "read_cpu_qualification", lambda path: {})
    monkeypatch.setattr(lf10, "_sha256_path", lambda path: hashes.get(Path(path), "A" * 64))
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "get_device_name", lambda device: "Tesla V100-PCIE-32GB")
    monkeypatch.setattr(lf10, "build_training_config", lambda device: SimpleNamespace(case_control="FULL"))
    monkeypatch.setattr(lf10, "load_case_physics", lambda control: (object(), "P" * 64, "O" * 64))
    monkeypatch.setattr(lf10, "load_medium_dataset", lambda *args, **kwargs: object())

    class Strong:
        physics_sha256 = "PHYSICS"

    class Ledger:
        semantic_sha256 = "SEMANTIC"
        streams = {"all": "STREAM"}

    monkeypatch.setattr(lf10.lf7, "MaterializedPhysicsLedger", lambda *args, **kwargs: Strong())
    monkeypatch.setattr(lf10, "MaterializedLF10Ledger", lambda *args, **kwargs: Ledger())
    monkeypatch.setattr(lf10, "_make_direction_runtime", lambda arm, **kwargs: {"arm": arm, "accepted": 0, "attempted": 0})

    def advance(runtime, *, target_accepted, **kwargs):
        runtime["accepted"] = target_accepted
        runtime["attempted"] = target_accepted

    monkeypatch.setattr(lf10, "_advance_direction", advance)
    monkeypatch.setattr(lf10, "_direction_endpoint", lambda runtime, target: {"arm": runtime["arm"], "identity_valid": True, "numerical_valid": True, "accepted_updates": runtime["accepted"], "attempted_updates": runtime["attempted"], "safety_gate": {"passed": True}, "strict_gate": {"passed": False}, "J_ratio": 0.9})
    monkeypatch.setattr(lf10, "_persist_direction_endpoint", lambda *args, **kwargs: None)
    monkeypatch.setattr(lf10, "_run_interface_pair", lambda seed, **kwargs: {"valid": True, "stream_seed": seed, "delta_Rmin": 0.04, "quality_preserved": True})

    def forgetting(seed, **kwargs):
        if seed == 23:
            raise RuntimeError("isolated")
        return {"valid": True, "stream_seed": seed, "J_ratio": 0.2, "event_missing_or_min_recall_le_half": True, "field_event_pareto": False}

    monkeypatch.setattr(lf10, "_run_forgetting_replication", forgetting)
    summary = lf10.execute_gpu_campaign(
        output_root=tmp_path / "run", medium_carrier=inputs["medium.npz"],
        lf3_t0_checkpoint=inputs["lf3.pt"], dev_r_checkpoint=inputs["devr.pt"],
        strong_ledger=inputs["strong.npz"], lf10_ledger=inputs["lf10.npz"],
        lf10_ledger_manifest=inputs["lf10.json"], cpu_qualification_path=inputs["cpu.json"],
        source_identity="LF10-BUNDLE-" + "A" * 64, device_name="cuda:0",
    )
    assert summary["direction_arms"][lf10.CTRL]["accepted_updates"] == 200
    assert set(summary["interface_replications"]) == {"17", "23", "29"}
    assert summary["forgetting_replications"]["23"]["valid"] is False
    assert summary["forgetting_replications"]["29"]["valid"] is True
    assert summary["status"] == "LF10_CAMPAIGN_COMPLETE_WITH_ISOLATED_TRACK_ERRORS"
    assert (tmp_path / "run" / "run_summary.json").is_file()
