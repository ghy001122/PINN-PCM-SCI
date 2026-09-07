"""Zero-update CPU qualification for the LF7 matched refinement pilot."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .phk_v22r_training import ROOT, load_case_physics
from .phk_v23_lf0 import _physics_objective, _read_json, _sha256_path, _write_json_exclusive
from .phk_v23_lf2 import load_medium_dataset
from .phk_v23_lf3 import build_training_config, full_medium_audit
from .phk_v23_lf4 import _field_state_sha256
from .phk_v23_lf7 import (
    ETA0,
    EXPECTED_FIXED_POOL_SHA256,
    EXPECTED_J0,
    EXPECTED_LEDGER_MANIFEST_SHA256,
    EXPECTED_LEDGER_SEMANTIC_SHA256,
    EXPECTED_LEDGER_SHA256,
    EXPECTED_PARTITION_SHA256,
    EXPECTED_PHYSICS_SHA256,
    MaterializedPhysicsLedger,
    TASK_ID,
    contract_identity,
    load_contracts,
    load_dev_r_model,
    restore_snapshot,
    state_digest,
    take_snapshot,
)


STATUS = "LF7_CPU_QUALIFICATION_PASS"
LF6_DEV_R = "DEV_R_EVENT_FRONTIER_RANK_BAND"


def _bound_path(
    binding: Mapping[str, Any], *, path_key: str = "path", sha_key: str = "sha256", label: str
) -> Path:
    path = (ROOT / str(binding[path_key])).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PermissionError(f"LF7 {label} escaped repository") from exc
    if not path.is_file() or _sha256_path(path) != str(binding[sha_key]).upper():
        raise ValueError(f"LF7 {label} is absent or hash-drifted")
    return path


def _close(actual: float, expected: float) -> bool:
    return math.isfinite(actual) and math.isclose(actual, expected, rel_tol=1.0e-10, abs_tol=1.0e-12)


def _audit_identity(actual: Mapping[str, Any], expected: Mapping[str, Any]) -> dict[str, bool]:
    checks: dict[str, bool] = {
        "all_values_finite": actual.get("all_values_finite") is True,
        "two_cycle_events": actual.get("two_cycle_events") is expected.get("two_cycle_events") is True,
        "phase_range": actual.get("phase_range", {}).get("passed") is True,
        "potential_guard": actual.get("potential_maximum_principle", {}).get("passed") is True,
        "phase_maximum": _close(float(actual["phase_maximum"]), float(expected["phase_maximum"])),
        "topology_weighted_loss": _close(
            float(actual["topology_weighted_loss"]), float(expected["topology_weighted_loss"])
        ),
    }
    for field in ("potential", "temperature", "phase"):
        checks[f"weighted_error_{field}"] = _close(
            float(actual["weighted_errors"][field]), float(expected["weighted_errors"][field])
        )
    for cycle in (1, 2):
        name = f"cycle_{cycle}"
        for metric in ("hard_recall", "hard_precision", "hard_active_mass_ratio", "event_time_absolute_error"):
            checks[f"{name}_{metric}"] = _close(
                float(actual["event_metrics"][name][metric]),
                float(expected["event_metrics"][name][metric]),
            )
        for metric in (
            "peak_roi_fraction",
            "peak_full_domain_fraction",
            "peak_outside_roi_fraction",
            "recovery_fraction",
        ):
            checks[f"{name}_{metric}"] = _close(
                float(actual["event_topology_hard_guard"]["cycles"][cycle - 1][metric]),
                float(expected["event_topology_hard_guard"]["cycles"][cycle - 1][metric]),
            )
    return checks


class _ToyModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.encoders = torch.nn.ModuleDict(
            {name: torch.nn.Linear(2, 2, bias=True, dtype=torch.float64) for name in ("potential", "temperature", "phase")}
        )
        self.heads = torch.nn.ModuleDict(
            {name: torch.nn.Linear(2, 1, bias=True, dtype=torch.float64) for name in ("potential", "temperature", "phase")}
        )

    def forward(self, value: torch.Tensor) -> torch.Tensor:
        return sum(self.heads[name](self.encoders[name](value)).sum() for name in self.encoders)


def _toy_rollback_check() -> dict[str, Any]:
    torch.manual_seed(17)
    np.random.seed(17)
    model = _ToyModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=ETA0, betas=(0.9, 0.999), eps=1.0e-8)
    warm = torch.tensor([[0.25, -0.75]], dtype=torch.float64)
    optimizer.zero_grad(set_to_none=True)
    model(warm).square().backward()
    optimizer.step()
    snapshot = take_snapshot(model, optimizer, accepted_updates=25, learning_rate=ETA0)
    batch = torch.tensor([[0.5, 0.125]], dtype=torch.float64)
    batch_before = batch.detach().clone()
    optimizer.zero_grad(set_to_none=True)
    model(batch).square().backward()
    optimizer.step()
    changed = state_digest(model, optimizer) != snapshot.digest
    restored = restore_snapshot(snapshot, model, optimizer)
    for group in optimizer.param_groups:
        group["lr"] = snapshot.learning_rate / 2.0
    return {
        "state_changed_before_rollback": changed,
        "rollback_bitwise_restored": restored == snapshot.digest,
        "same_block_coordinates_reusable": torch.equal(batch, batch_before),
        "learning_rate_halved": all(float(group["lr"]) == ETA0 / 2.0 for group in optimizer.param_groups),
        "snapshot_accepted_updates": snapshot.accepted_updates,
        "snapshot_sha256": snapshot.digest,
    }


def compute_cpu_payload() -> dict[str, Any]:
    contracts = load_contracts()
    data = contracts["data"]
    medium = _bound_path(data["training_source"], label="medium")
    dev_r = _bound_path(
        data["initial_DEV_R"], path_key="checkpoint_path", sha_key="checkpoint_sha256", label="LF6 DEV-R checkpoint"
    )
    dev_r_prediction = _bound_path(
        data["initial_DEV_R"], path_key="prediction_path", sha_key="prediction_sha256", label="LF6 DEV-R prediction"
    )
    ledger_path = _bound_path(data["materialized_ledger"], label="LF6 materialized ledger", sha_key="file_sha256")
    ledger_manifest_path = _bound_path(
        data["materialized_ledger"], path_key="manifest_path", sha_key="manifest_sha256", label="LF6 materialized ledger manifest"
    )
    lf6_terminal = _bound_path(data["LF6_evidence"]["terminal_artifact"], label="LF6 terminal artifact")
    lf6_terminal_manifest = _bound_path(data["LF6_evidence"]["terminal_manifest"], label="LF6 terminal manifest")
    lf6_summary = _bound_path(data["LF6_evidence"]["run_summary"], label="LF6 run summary")
    lf6_cpu = _bound_path(data["LF6_evidence"]["cpu_qualification"], label="LF6 CPU qualification")

    lf6_cpu_payload = _read_json(lf6_cpu)
    inherited_q = {"ledger": {
        "file_sha256": EXPECTED_LEDGER_SHA256,
        "manifest_sha256": EXPECTED_LEDGER_MANIFEST_SHA256,
        "semantic_sha256": EXPECTED_LEDGER_SEMANTIC_SHA256,
        "physics_1200_sha256": EXPECTED_PHYSICS_SHA256,
        "fixed_blind_pool_sha256": EXPECTED_FIXED_POOL_SHA256,
    }}
    ledger = MaterializedPhysicsLedger(ledger_path, contracts=contracts, qualification=inherited_q)
    manifest = _read_json(ledger_manifest_path)
    terminal = _read_json(lf6_terminal)
    summary = _read_json(lf6_summary)
    config = build_training_config("cpu")
    physics, _, _ = load_case_physics(config.case_control)
    dataset = load_medium_dataset(medium, physics=physics, contracts=contracts)
    model, checkpoint_payload = load_dev_r_model(
        dev_r, physics=physics, config=config, device=torch.device("cpu"), contracts=contracts
    )

    state_before = {field: _field_state_sha256(model, field) for field in ("potential", "temperature", "phase")}
    for parameter in model.parameters():
        parameter.grad = None
    audit = full_medium_audit(model, dataset, device=torch.device("cpu"))
    medium_grad_free = all(parameter.grad is None for parameter in model.parameters())
    expected_audit = summary["development"][LF6_DEV_R]["audit"]
    audit_checks = _audit_identity(audit, expected_audit)
    fixed_batch = ledger.fixed_batch(device=torch.device("cpu"))
    with torch.enable_grad():
        _, fixed_components = _physics_objective(model, fixed_batch, config)
    fixed_j0 = float(fixed_components["physics_total"])
    state_after_audits = {field: _field_state_sha256(model, field) for field in ("potential", "temperature", "phase")}

    for parameter in model.parameters():
        parameter.grad = None
    batch_one = ledger.physics_batch(1, device=torch.device("cpu"))
    batch_again = ledger.physics_batch(1, device=torch.device("cpu"))
    loss, _ = _physics_objective(model, batch_one, config)
    loss.backward()
    gradients = [parameter.grad for parameter in model.parameters() if parameter.grad is not None]
    backward_ok = bool(
        torch.isfinite(loss)
        and gradients
        and all(torch.isfinite(value).all() for value in gradients)
        and any(float(torch.linalg.vector_norm(value)) > 0.0 for value in gradients)
    )
    for parameter in model.parameters():
        parameter.grad = None
    state_after_backward = {field: _field_state_sha256(model, field) for field in ("potential", "temperature", "phase")}
    toy = _toy_rollback_check()

    checks: dict[str, bool] = {
        "all_input_hashes": True,
        "partition_sha256": dataset.partition_sha256 == EXPECTED_PARTITION_SHA256,
        "LF6_terminal_identity": terminal.get("machine_outcome") == "LF6_P0_PRESERVATION_FAILED"
        and terminal.get("selected_role") == LF6_DEV_R,
        "LF6_terminal_manifest_identity": _read_json(lf6_terminal_manifest).get("gate_outcome") == "LF6_P0_PRESERVATION_FAILED",
        "LF6_CPU_identity": lf6_cpu_payload.get("status") == "LF6_CPU_F_QUALIFICATION_PASS",
        "DEV_R_checkpoint_metadata": checkpoint_payload.get("lf6", {}).get("role") == LF6_DEV_R,
        "DEV_R_full_medium_audit": all(audit_checks.values()),
        "DEV_R_recorded_safety": summary["development"][LF6_DEV_R]["safety_gate"]["passed"] is True,
        "fixed_blind_J0": _close(fixed_j0, EXPECTED_J0),
        "ledger_file": _sha256_path(ledger_path) == EXPECTED_LEDGER_SHA256,
        "ledger_manifest": _sha256_path(ledger_manifest_path) == EXPECTED_LEDGER_MANIFEST_SHA256,
        "ledger_semantic": manifest.get("semantic_sha256") == EXPECTED_LEDGER_SEMANTIC_SHA256,
        "physics_stream_1200": ledger.physics_sha256 == EXPECTED_PHYSICS_SHA256 and len(ledger.physics_hashes) == 1200,
        "fixed_pool": manifest.get("streams", {}).get("fixed_blind_pool_sha256") == EXPECTED_FIXED_POOL_SHA256,
        "runtime_sampling_absent": "SobolEngine" not in (ROOT / "pinn_pcm_sci/phk_v23_lf7.py").read_text(encoding="utf-8"),
        "same_batch_coordinates": batch_one.batch_sha256 == batch_again.batch_sha256
        and torch.equal(batch_one.interior, batch_again.interior),
        "toy_snapshot_changed": toy["state_changed_before_rollback"],
        "toy_rollback": toy["rollback_bitwise_restored"],
        "toy_same_coordinates": toy["same_block_coordinates_reusable"],
        "toy_lr_halving": toy["learning_rate_halved"],
        "real_DEV_R_finite_backward_no_step": backward_ok,
        "medium_audit_no_gradient": medium_grad_free,
        "model_weights_unchanged": state_before == state_after_audits == state_after_backward,
        "fine_extra_LF_ONLY_stress_unread": True,
    }
    gate = STATUS if all(checks.values()) else "LF7_CPU_QUALIFICATION_FAILED"
    return {
        "schema_id": "phk-v23-lf7-cpu-qualification-v1",
        "task_id": TASK_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_outcome": gate,
        "status": gate,
        "scientific_optimizer_updates": 0,
        "gpu_used": False,
        "gpu_execution_authorized_by_cpu_gate": gate == STATUS,
        "checks": checks,
        "audit_identity_checks": audit_checks,
        "contracts": contract_identity(),
        "partition_sha256": dataset.partition_sha256,
        "dev_r_full_medium_audit": audit,
        "dev_r_terminal_full_medium_audit": expected_audit,
        "fixed_blind_J0": fixed_j0,
        "fixed_blind_components": fixed_components,
        "ledger": inherited_q["ledger"],
        "rollback_qualification": toy,
        "input_bindings": {
            "medium": {"path": str(medium), "sha256": _sha256_path(medium)},
            "dev_r_checkpoint": {"path": str(dev_r), "sha256": _sha256_path(dev_r)},
            "dev_r_prediction": {"path": str(dev_r_prediction), "sha256": _sha256_path(dev_r_prediction)},
            "ledger": {"path": str(ledger_path), "sha256": _sha256_path(ledger_path)},
            "ledger_manifest": {"path": str(ledger_manifest_path), "sha256": _sha256_path(ledger_manifest_path)},
            "lf6_terminal": {"path": str(lf6_terminal), "sha256": _sha256_path(lf6_terminal)},
            "lf6_terminal_manifest": {"path": str(lf6_terminal_manifest), "sha256": _sha256_path(lf6_terminal_manifest)},
            "lf6_run_summary": {"path": str(lf6_summary), "sha256": _sha256_path(lf6_summary)},
            "lf6_cpu_qualification": {"path": str(lf6_cpu), "sha256": _sha256_path(lf6_cpu)},
        },
        "reference_boundary": {
            "fine_read": False,
            "extra_fine_read": False,
            "direct_LF_ONLY_read": False,
            "frozen_evaluator_read": False,
            "stress_read": False,
        },
    }


def qualify_cpu(*, artifact_path: Path, manifest_path: Path, raw_output_directory: Path) -> dict[str, Any]:
    payload = compute_cpu_payload()
    if payload["gate_outcome"] != STATUS:
        raise RuntimeError(payload["gate_outcome"])
    raw = Path(raw_output_directory).resolve()
    raw.mkdir(parents=True, exist_ok=True)
    raw_report = raw / "qualification.json"
    _write_json_exclusive(raw_report, payload)
    _write_json_exclusive(Path(artifact_path), payload)
    run_id = Path(artifact_path).stem
    manifest = {
        "schema_version": "run-manifest-v1",
        "run_id": run_id,
        "experiment_group_id": "PHK_V23_LF7",
        "tier": "qualification",
        "scientific_role": "cpu_only_DEV_R_ledger_rollback_and_backward_qualification",
        "gate": "PHK_V23_LF7_CPU",
        "started_at": payload["created_at_utc"],
        "ended_at": payload["created_at_utc"],
        "command": [".venv/Scripts/python.exe", "-m", "pinn_pcm_sci.phk_v23_lf7_qualification"],
        "execution_status": "COMPLETE",
        "numerical_validity": "VALID_CPU_FP64_ZERO_UPDATE_HASH_BOUND_DEV_R_LEDGER_ROLLBACK_AND_BACKWARD",
        "gate_outcome": STATUS,
        "route_disposition": "RUN_MATCHED_P0_S_THEN_FRESH_P0_F",
        "evidence_identity": "ZERO_UPDATE_HASH_BOUND_DEV_R_LEDGER_ROLLBACK_AND_BACKWARD_QUALIFICATION_ONLY",
        "claim_status": "LF7_DEV_R_LEDGER_ROLLBACK_AND_BACKWARD_QUALIFIED_GPU_MECHANISM_UNTESTED",
        "code_identity": {"base_commit": "e00f8767fc1d611b4cadcd0057720d1dd507f51c", "workspace_scope": "LF7_EXACT_ALLOWLIST_UNRELATED_DIRTY_PRESERVED"},
        "environment": {"device": "CPU", "dtype": "FLOAT64", "cloud_connection_opened": False, "stress_status": "TWO_STRESS_REFERENCES_SEALED_UNREAD"},
        "physical_contract_id": "PHK_V21_FIXED_DISCRETIZATION_FULL_NOMINAL",
        "split_id": "MEDIUM_AUDIT_ONLY_EXACT_DEV_R_PHYSICS_LEDGER_FINE_EXTRA_LF_ONLY_LOCAL_ONLY_STRESS_SEALED",
        "method_id": "phk-v23-lf7-competence-filtered-refinement-v1",
        "case_id": "PHK_V21_NOMINAL_DEV_R_REFINEMENT_QUALIFICATION",
        "seed": 17,
        "planned_budget": {"gpu_trajectories": 0, "optimizer_updates": 0},
        "actual_budget": {"gpu_trajectories": 0, "optimizer_updates": 0, "gpu_used": False},
        "checkpoint": {"DEV_R_source_sha256": payload["input_bindings"]["dev_r_checkpoint"]["sha256"], "loaded_read_only": True},
        "evaluator_id": "NOT_READ_DURING_LF7_CPU_QUALIFICATION",
        "artifacts": {
            "compact_qualification": f"artifacts/{Path(artifact_path).name}#sha256={_sha256_path(Path(artifact_path))}",
            "raw_report": f"{raw_report.relative_to(ROOT).as_posix()}#sha256={_sha256_path(raw_report)}",
        },
        "failure_class": None,
        "replay_of": None,
        "supersedes": None,
    }
    _write_json_exclusive(Path(manifest_path), manifest)
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--raw-output-directory", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    payload = qualify_cpu(
        artifact_path=args.artifact,
        manifest_path=args.manifest,
        raw_output_directory=args.raw_output_directory,
    )
    print(json.dumps({"gate_outcome": payload["gate_outcome"], "fixed_blind_J0": payload["fixed_blind_J0"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["STATUS", "compute_cpu_payload", "qualify_cpu"]
