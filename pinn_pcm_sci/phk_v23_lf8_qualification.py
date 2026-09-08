"""Zero-update CPU qualification for LF8's reachable rollback path."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import random
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .ledger import RunManifest
from .phk_v22r_training import ROOT, load_case_physics
from .phk_v23_lf0 import _physics_objective, _sha256_path, _write_json_exclusive
from .phk_v23_lf2 import load_medium_dataset
from .phk_v23_lf3 import build_training_config, full_medium_audit
from .phk_v23_lf8 import (
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
    _load_dev_r_model,
    _make_optimizer,
    contract_identity,
    load_contracts,
    phase_parameters,
    restore_snapshot,
    set_phase_trainable,
    snapshot_digest,
    snapshot_optimizer_aliases,
    take_snapshot,
)


STATUS = "LF8_CPU_QUALIFICATION_PASS"


def _bound_path(binding: Mapping[str, Any], *, path_key: str, sha_key: str, label: str) -> Path:
    path = (ROOT / str(binding[path_key])).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PermissionError(f"LF8 {label} escaped repository") from exc
    if not path.is_file() or _sha256_path(path) != str(binding[sha_key]).upper():
        raise ValueError(f"LF8 {label} is absent or hash-drifted")
    return path


def _real_nonempty_adam_rollback(model: torch.nn.Module) -> dict[str, Any]:
    random.seed(17); np.random.seed(17); torch.manual_seed(17)
    optimizer = _make_optimizer(model)
    set_phase_trainable(model, False)
    optimizer.zero_grad(set_to_none=True)
    synthetic = sum(parameter.square().sum() for parameter in model.parameters() if parameter.requires_grad)
    synthetic.backward()
    optimizer.step()
    state_count = len(optimizer.state)
    snapshot = take_snapshot(model, optimizer, accepted_updates=25, learning_rate=ETA0)
    immutable = snapshot.immutable_digest
    cycles: list[dict[str, Any]] = []
    for cycle in range(2):
        restored_before = restore_snapshot(snapshot, model, optimizer)
        aliases_before = snapshot_optimizer_aliases(snapshot, optimizer)
        for group in optimizer.param_groups:
            group["lr"] = ETA0 / 16.0
        optimizer.zero_grad(set_to_none=True)
        proposal = sum((index + 1) * parameter.square().sum() for index, parameter in enumerate(model.parameters()) if parameter.requires_grad)
        proposal.backward()
        optimizer.step()
        random.random(); np.random.random(); torch.rand(())
        snapshot_stable_after_step = snapshot_digest(snapshot) == immutable
        restored_after = restore_snapshot(snapshot, model, optimizer)
        cycles.append({
            "cycle": cycle + 1,
            "restored_before_sha256": restored_before,
            "restored_after_sha256": restored_after,
            "optimizer_snapshot_aliases": aliases_before,
            "snapshot_stable_after_step": snapshot_stable_after_step,
        })
    return {
        "real_model": True,
        "nonempty_adam_state_count": state_count,
        "phase_frozen_in_snapshot": not snapshot.phase_trainable,
        "phase_optimizer_state_entries": sum(parameter in optimizer.state for parameter in phase_parameters(model)),
        "continuous_reject_restore_cycles": cycles,
        "snapshot_sha256": immutable,
        "passed": bool(
            state_count > 0
            and not snapshot.phase_trainable
            and all(not row["optimizer_snapshot_aliases"] and row["snapshot_stable_after_step"] and row["restored_before_sha256"] == snapshot.state_digest and row["restored_after_sha256"] == snapshot.state_digest for row in cycles)
        ),
    }


def compute_cpu_payload() -> dict[str, Any]:
    contracts = load_contracts()
    data = contracts["data"]
    medium = _bound_path(data["training_source"], path_key="path", sha_key="sha256", label="medium audit source")
    dev_r = _bound_path(data["initial_DEV_R"], path_key="checkpoint_path", sha_key="checkpoint_sha256", label="DEV-R checkpoint")
    dev_r_prediction = _bound_path(data["initial_DEV_R"], path_key="prediction_path", sha_key="prediction_sha256", label="DEV-R prediction")
    ledger_path = _bound_path(data["materialized_ledger"], path_key="path", sha_key="file_sha256", label="materialized ledger")
    manifest_path = _bound_path(data["materialized_ledger"], path_key="manifest_path", sha_key="manifest_sha256", label="ledger manifest")
    inherited = {"ledger": {
        "file_sha256": EXPECTED_LEDGER_SHA256,
        "manifest_sha256": EXPECTED_LEDGER_MANIFEST_SHA256,
        "semantic_sha256": EXPECTED_LEDGER_SEMANTIC_SHA256,
        "physics_1200_sha256": EXPECTED_PHYSICS_SHA256,
        "fixed_blind_pool_sha256": EXPECTED_FIXED_POOL_SHA256,
    }}
    ledger = MaterializedPhysicsLedger(ledger_path, contracts=contracts, qualification=inherited)
    config = build_training_config("cpu")
    physics, _, _ = load_case_physics(config.case_control)
    dataset = load_medium_dataset(medium, physics=physics, contracts=contracts)
    model, checkpoint_payload = _load_dev_r_model(dev_r, physics=physics, config=config, device=torch.device("cpu"), contracts=contracts)
    dev_r_audit = full_medium_audit(model, dataset, device=torch.device("cpu"))
    fixed_batch = ledger.fixed_batch(device=torch.device("cpu"))
    with torch.enable_grad():
        _, fixed_components = _physics_objective(model, fixed_batch, config)
    fixed_j0 = float(fixed_components["physics_total"])
    rollback = _real_nonempty_adam_rollback(model)
    restore_model, _ = _load_dev_r_model(dev_r, physics=physics, config=config, device=torch.device("cpu"), contracts=contracts)
    for parameter in restore_model.parameters(): parameter.grad = None
    batch = ledger.physics_batch(1, device=torch.device("cpu"))
    loss, _ = _physics_objective(restore_model, batch, config)
    loss.backward()
    gradients = [parameter.grad for parameter in restore_model.parameters() if parameter.grad is not None]
    backward_ok = bool(torch.isfinite(loss) and gradients and all(torch.isfinite(value).all() for value in gradients) and any(float(torch.linalg.vector_norm(value)) > 0.0 for value in gradients))
    checks = {
        "all_input_hashes": True,
        "partition_sha256": dataset.partition_sha256 == EXPECTED_PARTITION_SHA256,
        "DEV_R_checkpoint_metadata": checkpoint_payload.get("lf6", {}).get("role") == "DEV_R_EVENT_FRONTIER_RANK_BAND",
        "DEV_R_full_medium_finite": dev_r_audit.get("all_values_finite") is True,
        "fixed_blind_J0": math.isclose(fixed_j0, EXPECTED_J0, rel_tol=1e-10, abs_tol=1e-12),
        "physics_stream_1200": ledger.physics_sha256 == EXPECTED_PHYSICS_SHA256 and len(ledger.physics_hashes) == 1200,
        "real_nonempty_Adam_two_rollbacks": rollback["passed"],
        "real_physics_finite_backward_no_step": backward_ok,
        "fine_extra_LF_ONLY_stress_unread": True,
    }
    gate = STATUS if all(checks.values()) else "LF8_ENGINEERING_QUALIFICATION_FAILED"
    return {
        "schema_id": "phk-v23-lf8-cpu-qualification-v1",
        "task_id": TASK_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_outcome": gate,
        "status": gate,
        "scientific_optimizer_updates": 0,
        "gpu_used": False,
        "gpu_execution_authorized_by_cpu_gate": gate == STATUS,
        "checks": checks,
        "contracts": contract_identity(),
        "partition_sha256": dataset.partition_sha256,
        "dev_r_full_medium_audit": dev_r_audit,
        "fixed_blind_J0": fixed_j0,
        "fixed_blind_components": fixed_components,
        "ledger": inherited["ledger"],
        "rollback_qualification": rollback,
        "input_bindings": {
            "medium": {"path": str(medium), "sha256": _sha256_path(medium)},
            "dev_r_checkpoint": {"path": str(dev_r), "sha256": _sha256_path(dev_r)},
            "dev_r_prediction": {"path": str(dev_r_prediction), "sha256": _sha256_path(dev_r_prediction)},
            "ledger": {"path": str(ledger_path), "sha256": _sha256_path(ledger_path)},
            "ledger_manifest": {"path": str(manifest_path), "sha256": _sha256_path(manifest_path)},
        },
        "reference_boundary": {"fine_read": False, "extra_fine_read": False, "direct_LF_ONLY_read": False, "frozen_evaluator_read": False, "stress_read": False},
    }


def build_cpu_manifest(
    payload: Mapping[str, Any], *, artifact_path: Path, raw_report: Path
) -> dict[str, Any]:
    """Build a complete repository RunManifest v1 for the LF8 CPU gate."""

    artifact_path = Path(artifact_path).resolve()
    raw_report = Path(raw_report).resolve()
    manifest = {
        "schema_version": "run-manifest-v1", "run_id": Path(artifact_path).stem,
        "experiment_group_id": "PHK_V23_LF8", "tier": "qualification",
        "scientific_role": "cpu_only_real_model_nonempty_adam_continuous_rollback_and_physics_backward",
        "gate": "PHK_V23_LF8_CPU", "started_at": payload["created_at_utc"], "ended_at": payload["created_at_utc"],
        "command": [".venv/Scripts/python.exe", "-m", "pinn_pcm_sci.phk_v23_lf8_qualification"],
        "execution_status": "COMPLETE", "numerical_validity": "VALID_CPU_FP64_ZERO_SCIENTIFIC_UPDATE_REAL_ROLLBACK_QUALIFICATION",
        "gate_outcome": STATUS, "route_disposition": "RUN_MANDATORY_P0_FSTAR_THEN_CONDITIONAL_P0_C",
        "evidence_identity": "ENGINEERING_QUALIFICATION_ONLY", "seed": 17,
        "claim_status": "LF8_REAL_NONEMPTY_ADAM_ROLLBACK_QUALIFIED_GPU_FILTER_UNTESTED",
        "code_identity": {
            "base_commit": "95e448e36a659ac266b670667543b80ce467da53",
            "workspace_scope": "LF8_EXACT_ALLOWLIST_UNRELATED_DIRTY_PRESERVED",
        },
        "environment": {
            "device": "CPU", "dtype": "FLOAT64",
            "cloud_connection_opened": False,
            "stress_status": "TWO_STRESS_REFERENCES_SEALED_UNREAD",
        },
        "physical_contract_id": "PHK_V21_FIXED_DISCRETIZATION_FULL_NOMINAL",
        "split_id": "MEDIUM_AUDIT_ONLY_EXACT_DEV_R_PHYSICS_LEDGER_FINE_EXTRA_LF_ONLY_LOCAL_ONLY_STRESS_SEALED",
        "method_id": "phk-v23-lf8-identity-correct-competence-filter-v1",
        "case_id": "PHK_V21_NOMINAL_DEV_R_FILTER_COMPLETION_QUALIFICATION",
        "planned_budget": {"gpu_trajectories": 0, "optimizer_updates": 0},
        "actual_budget": {"gpu_trajectories": 0, "optimizer_updates": 0, "gpu_used": False},
        "checkpoint": {
            "DEV_R_source_sha256": payload["input_bindings"]["dev_r_checkpoint"]["sha256"],
            "loaded_read_only": True,
        },
        "evaluator_id": "NOT_READ_DURING_LF8_CPU_QUALIFICATION",
        "artifacts": {"compact_qualification": f"artifacts/{Path(artifact_path).name}#sha256={_sha256_path(Path(artifact_path))}", "raw_report": f"{raw_report.relative_to(ROOT).as_posix()}#sha256={_sha256_path(raw_report)}"},
        "failure_class": None, "replay_of": None, "supersedes": None,
    }
    validated = RunManifest(**manifest)
    index = validated.index_row()
    if (
        index["run_id"] != manifest["run_id"]
        or index["gate_outcome"] != STATUS
        or index["execution_status"] != "COMPLETE"
        or index["claim_status"] != manifest["claim_status"]
    ):
        raise ValueError("LF8 qualification manifest/index identity drift")
    return validated.to_dict()


def qualify_cpu(*, artifact_path: Path, manifest_path: Path, raw_output_directory: Path) -> dict[str, Any]:
    payload = compute_cpu_payload()
    if payload["gate_outcome"] != STATUS:
        raise RuntimeError(payload["gate_outcome"])
    raw = Path(raw_output_directory).resolve(); raw.mkdir(parents=True, exist_ok=True)
    raw_report = raw / "qualification.json"
    _write_json_exclusive(raw_report, payload)
    _write_json_exclusive(Path(artifact_path), payload)
    manifest = build_cpu_manifest(payload, artifact_path=Path(artifact_path), raw_report=raw_report)
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
    payload = qualify_cpu(artifact_path=args.artifact, manifest_path=args.manifest, raw_output_directory=args.raw_output_directory)
    print(json.dumps({"gate_outcome": payload["gate_outcome"], "fixed_blind_J0": payload["fixed_blind_J0"], "rollback_passed": payload["rollback_qualification"]["passed"]}, sort_keys=True))
    return 0


if __name__ == "__main__": raise SystemExit(main())


__all__ = ["STATUS", "build_cpu_manifest", "compute_cpu_payload", "qualify_cpu"]
