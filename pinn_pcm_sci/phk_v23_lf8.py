"""LF8 identity-correct competence-filter completion and schedule attribution.

F* is mandatory.  It proposes 25-update strong-form blocks from the exact LF6
DEV-R endpoint, accepts only function-space-safe strict physics decreases, and
retains the last accepted prefix on stall.  The matched schedule-only control is
run only after a complete 1,200-update F* safety path.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .phk_v22r_prediction import write_prediction_carrier
from .phk_v22r_training import (
    METHOD_CONTRACT_PATH as V22R_METHOD_CONTRACT_PATH,
    PROGRAM_CONTRACT_PATH as V22R_PROGRAM_CONTRACT_PATH,
    ROOT,
    _checkpoint_payload,
    load_case_physics,
)
from .phk_v23_lf0 import PhysicsBatch, _artifact_record, _physics_objective, _read_json, _sha256_path, _write_json_exclusive
from .phk_v23_lf2 import load_medium_dataset
from .phk_v23_lf3 import _phase_state_sha256, build_training_config, full_medium_audit
from . import phk_v23_lf7 as lf7


TASK_ID = "PHK_V23_LF8_IDENTITY_CORRECT_COMPETENCE_FILTER_COMPLETION_AND_SCHEDULE_ATTRIBUTION_EXECUTE"
TITLE = "PHK-V2.3 LF8 identity-correct competence-filter completion and conditional schedule attribution"
P0_FSTAR = "P0_FSTAR_IDENTITY_CORRECT_COMPETENCE_FILTER"
P0_C = "P0_C_ACCEPTED_SCHEDULE_NO_FILTER"
ARM_ORDER = (P0_FSTAR, P0_C)
ARM_DIRECTORIES = {P0_FSTAR: "p0-fstar", P0_C: "p0-schedule-control"}

P0_UPDATES = 1200
PHASE_FREEZE_STEPS = 550
BLOCK_SIZE = 25
BLOCK_COUNT = 48
ETA0 = 1.25e-4
LR_SCALES = (ETA0, ETA0 / 2.0, ETA0 / 4.0, ETA0 / 8.0, ETA0 / 16.0)
MAX_FILTER_ATTEMPTED_UPDATES = 2400
EXPECTED_PHYSICS_SHA256 = lf7.EXPECTED_PHYSICS_SHA256
EXPECTED_FIXED_POOL_SHA256 = lf7.EXPECTED_FIXED_POOL_SHA256
EXPECTED_LEDGER_SHA256 = lf7.EXPECTED_LEDGER_SHA256
EXPECTED_LEDGER_MANIFEST_SHA256 = lf7.EXPECTED_LEDGER_MANIFEST_SHA256
EXPECTED_LEDGER_SEMANTIC_SHA256 = lf7.EXPECTED_LEDGER_SEMANTIC_SHA256
EXPECTED_DEV_R_SHA256 = lf7.EXPECTED_DEV_R_SHA256
EXPECTED_PARTITION_SHA256 = lf7.EXPECTED_PARTITION_SHA256
EXPECTED_J0 = lf7.EXPECTED_J0

PROGRAM_CONTRACT_PATH = ROOT / "configs/phk_v23/program_contract_lf8_competence_filter.json"
METHOD_CONTRACT_PATH = ROOT / "configs/phk_v23/method_contract_lf8_competence_filter.json"
DATA_CONTRACT_PATH = ROOT / "configs/phk_v23/data_contract_lf8_competence_filter.json"
DECISION_CONTRACT_PATH = ROOT / "configs/phk_v23/decision_contract_lf8_competence_filter.json"
CONTRACT_PATHS = {"program": PROGRAM_CONTRACT_PATH, "method": METHOD_CONTRACT_PATH, "data": DATA_CONTRACT_PATH, "decision": DECISION_CONTRACT_PATH}
EXPECTED_SCHEMAS = {name: f"phk-v23-lf8-{name}-contract-v1" for name in CONTRACT_PATHS}


def load_contracts() -> dict[str, dict[str, Any]]:
    contracts = {name: _read_json(path) for name, path in CONTRACT_PATHS.items()}
    for name, schema in EXPECTED_SCHEMAS.items():
        if contracts[name].get("schema_id") != schema:
            raise ValueError(f"unsupported LF8 {name} contract")
    relative = {name: path.relative_to(ROOT).as_posix() for name, path in CONTRACT_PATHS.items()}
    if contracts["program"].get("phase_id") != TASK_ID:
        raise ValueError("LF8 task identity drift")
    if any(contracts[name].get("program_contract") != relative["program"] for name in ("method", "data", "decision")):
        raise ValueError("LF8 program binding drift")
    if contracts["decision"].get("method_contract") != relative["method"] or contracts["decision"].get("data_contract") != relative["data"]:
        raise ValueError("LF8 decision binding drift")
    limits = contracts["program"]["hard_limits"]
    if limits.get("maximum_scientific_gpu_trajectories") != 2 or limits.get("P0_FSTAR_maximum_accepted_updates") != P0_UPDATES:
        raise ValueError("LF8 trajectory bound drift")
    if limits.get("P0_FSTAR_maximum_attempted_updates") != MAX_FILTER_ATTEMPTED_UPDATES or limits.get("P0_C_updates") != P0_UPDATES:
        raise ValueError("LF8 update bound drift")
    method = contracts["method"]
    if tuple(float(value) for value in method["P0_FSTAR"]["dyadic_learning_rates"]) != LR_SCALES:
        raise ValueError("LF8 dyadic scale drift")
    data = contracts["data"]
    ledger = data["materialized_ledger"]
    expected = {
        "file_sha256": EXPECTED_LEDGER_SHA256,
        "manifest_sha256": EXPECTED_LEDGER_MANIFEST_SHA256,
        "semantic_sha256": EXPECTED_LEDGER_SEMANTIC_SHA256,
        "physics_1200_sha256": EXPECTED_PHYSICS_SHA256,
        "fixed_blind_pool_sha256": EXPECTED_FIXED_POOL_SHA256,
    }
    if any(ledger.get(key) != value for key, value in expected.items()):
        raise ValueError("LF8 materialized ledger binding drift")
    if data.get("partition_sha256") != EXPECTED_PARTITION_SHA256 or data["initial_DEV_R"].get("checkpoint_sha256") != EXPECTED_DEV_R_SHA256:
        raise ValueError("LF8 frozen input identity drift")
    if len(contracts["decision"].get("machine_outcomes_and_unique_next", {})) != 11:
        raise ValueError("LF8 terminal outcome map is incomplete")
    if contracts["decision"].get("stress_status") != "TWO_STRESS_REFERENCES_SEALED_UNREAD":
        raise PermissionError("LF8 stress boundary drift")
    return contracts


def contract_identity() -> dict[str, dict[str, str]]:
    return {name: {"path": path.relative_to(ROOT).as_posix(), "sha256": _sha256_path(path)} for name, path in CONTRACT_PATHS.items()}


def read_cpu_qualification(path: Path) -> dict[str, Any]:
    payload = _read_json(Path(path).resolve())
    if payload.get("schema_id") != "phk-v23-lf8-cpu-qualification-v1" or payload.get("task_id") != TASK_ID:
        raise ValueError("LF8 CPU qualification identity drift")
    if payload.get("gate_outcome") != "LF8_CPU_QUALIFICATION_PASS" or payload.get("scientific_optimizer_updates") != 0:
        raise PermissionError("LF8 CPU qualification did not pass")
    if not all(bool(value) for value in payload.get("checks", {}).values()):
        raise PermissionError("LF8 CPU qualification contains a failed check")
    return payload


MaterializedPhysicsLedger = lf7.MaterializedPhysicsLedger


def update_digest(digest: Any, value: Any) -> None:
    lf7._update_digest(digest, value)


def phase_parameters(model: torch.nn.Module) -> tuple[torch.nn.Parameter, ...]:
    return tuple(model.encoders["phase"].parameters()) + tuple(model.heads["phase"].parameters())


def set_phase_trainable(model: torch.nn.Module, trainable: bool) -> None:
    model.encoders["phase"].requires_grad_(trainable)
    model.heads["phase"].requires_grad_(trainable)


def _rng_state() -> tuple[Any, ...]:
    return (
        random.getstate(),
        copy.deepcopy(np.random.get_state()),
        torch.get_rng_state().clone(),
        [value.clone() for value in torch.cuda.get_rng_state_all()] if torch.cuda.is_available() else [],
    )


def _state_digest(model: torch.nn.Module, optimizer: torch.optim.Optimizer) -> str:
    digest = hashlib.sha256(b"PHK_V23_LF8_LIVE_STATE_V1\n")
    update_digest(digest, model.state_dict())
    update_digest(digest, optimizer.state_dict())
    update_digest(digest, _rng_state())
    return digest.hexdigest().upper()


@dataclass
class TrainingSnapshot:
    model_state: dict[str, Any]
    optimizer_state: dict[str, Any]
    python_rng: object
    numpy_rng: tuple[Any, ...]
    torch_rng: torch.Tensor
    cuda_rng: list[torch.Tensor]
    accepted_updates: int
    learning_rate: float
    phase_trainable: bool
    state_digest: str
    immutable_digest: str = ""


def snapshot_digest(snapshot: TrainingSnapshot) -> str:
    digest = hashlib.sha256(b"PHK_V23_LF8_IMMUTABLE_SNAPSHOT_V1\n")
    update_digest(digest, snapshot.model_state)
    update_digest(digest, snapshot.optimizer_state)
    update_digest(digest, snapshot.python_rng)
    update_digest(digest, snapshot.numpy_rng)
    update_digest(digest, snapshot.torch_rng)
    update_digest(digest, snapshot.cuda_rng)
    update_digest(digest, snapshot.accepted_updates)
    update_digest(digest, snapshot.learning_rate)
    update_digest(digest, snapshot.phase_trainable)
    update_digest(digest, snapshot.state_digest)
    return digest.hexdigest().upper()


def take_snapshot(model: torch.nn.Module, optimizer: torch.optim.Optimizer, *, accepted_updates: int, learning_rate: float) -> TrainingSnapshot:
    python_rng, numpy_rng, torch_rng, cuda_rng = _rng_state()
    snapshot = TrainingSnapshot(
        model_state=copy.deepcopy(model.state_dict()),
        optimizer_state=copy.deepcopy(optimizer.state_dict()),
        python_rng=copy.deepcopy(python_rng),
        numpy_rng=copy.deepcopy(numpy_rng),
        torch_rng=torch_rng.clone(),
        cuda_rng=[value.clone() for value in cuda_rng],
        accepted_updates=int(accepted_updates),
        learning_rate=float(learning_rate),
        phase_trainable=any(parameter.requires_grad for parameter in phase_parameters(model)),
        state_digest=_state_digest(model, optimizer),
    )
    snapshot.immutable_digest = snapshot_digest(snapshot)
    return snapshot


def snapshot_optimizer_aliases(snapshot: TrainingSnapshot, optimizer: torch.optim.Optimizer) -> list[str]:
    aliases: list[str] = []
    live = optimizer.state_dict().get("state", {})
    saved = snapshot.optimizer_state.get("state", {})
    for state_id, saved_state in saved.items():
        live_state = live.get(state_id, {})
        for key, saved_value in saved_state.items():
            live_value = live_state.get(key)
            if torch.is_tensor(saved_value) and torch.is_tensor(live_value) and saved_value.data_ptr() == live_value.data_ptr():
                aliases.append(f"{state_id}:{key}")
    return aliases


def restore_snapshot(snapshot: TrainingSnapshot, model: torch.nn.Module, optimizer: torch.optim.Optimizer) -> str:
    if snapshot_digest(snapshot) != snapshot.immutable_digest:
        raise RuntimeError("LF8 immutable snapshot drift before rollback")
    model.load_state_dict(copy.deepcopy(snapshot.model_state), strict=True)
    optimizer.load_state_dict(copy.deepcopy(snapshot.optimizer_state))
    set_phase_trainable(model, snapshot.phase_trainable)
    random.setstate(copy.deepcopy(snapshot.python_rng))
    np.random.set_state(copy.deepcopy(snapshot.numpy_rng))
    torch.set_rng_state(snapshot.torch_rng.clone())
    if torch.cuda.is_available():
        torch.cuda.set_rng_state_all([value.clone() for value in snapshot.cuda_rng])
    for group in optimizer.param_groups:
        group["lr"] = snapshot.learning_rate
    aliases = snapshot_optimizer_aliases(snapshot, optimizer)
    restored = _state_digest(model, optimizer)
    if aliases or restored != snapshot.state_digest or snapshot_digest(snapshot) != snapshot.immutable_digest:
        raise RuntimeError("LF8 block rollback state identity drift")
    return restored


def available_scales(current: float) -> tuple[float, ...]:
    index = min(range(len(LR_SCALES)), key=lambda item: abs(LR_SCALES[item] - current))
    if not math.isclose(LR_SCALES[index], current, rel_tol=0.0, abs_tol=1.0e-16):
        raise ValueError("LF8 current learning rate left frozen dyadic ladder")
    return LR_SCALES[index:]


def filter_path_disposition(*, accepted_updates: int, identity_valid: bool) -> str:
    if not identity_valid:
        return "POSTSTEP_IDENTITY_INVALID"
    if accepted_updates == P0_UPDATES:
        return "COMPLETE"
    if accepted_updates == 0:
        return "NO_FEASIBLE_FIRST_BLOCK"
    if 0 < accepted_updates < P0_UPDATES and accepted_updates % BLOCK_SIZE == 0:
        return "FILTER_STALLED_WITH_VALID_PREFIX"
    raise ValueError("LF8 invalid accepted prefix length")


def schedule_control_required(fstar: Mapping[str, Any]) -> bool:
    return bool(
        fstar.get("numerical_valid") is True
        and int(fstar.get("accepted_updates", -1)) == P0_UPDATES
        and fstar.get("safety_gate", {}).get("passed") is True
        and float(fstar.get("fixed_blind_physics", math.inf)) < EXPECTED_J0
        and len(fstar.get("accepted_learning_rates", ())) == BLOCK_COUNT
    )


def replay_schedule(fstar: Mapping[str, Any]) -> tuple[float, ...]:
    if not schedule_control_required(fstar):
        raise PermissionError("LF8 schedule control trigger not satisfied")
    schedule = tuple(float(value) for value in fstar["accepted_learning_rates"])
    if any(value not in LR_SCALES for value in schedule) or any(after > before for before, after in zip(schedule, schedule[1:])):
        raise ValueError("LF8 accepted schedule identity drift")
    return schedule


def competence_gate(audit: Mapping[str, Any], baseline: Mapping[str, Any], *, strict_timing: bool = False, physics_previous: float | None = None, physics_new: float | None = None) -> dict[str, Any]:
    return lf7.competence_gate(audit, baseline, strict_timing=strict_timing, physics_previous=physics_previous, physics_new=physics_new)


def _make_optimizer(model: torch.nn.Module) -> torch.optim.Adam:
    return torch.optim.Adam(model.parameters(), lr=ETA0, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0, amsgrad=False)


def _train_one_step(model: torch.nn.Module, optimizer: torch.optim.Optimizer, *, batch: PhysicsBatch, config: Any) -> tuple[bool, dict[str, Any]]:
    return lf7._train_one_step(model, optimizer, batch=batch, config=config)


def _fixed_physics(model: torch.nn.Module, ledger: MaterializedPhysicsLedger, config: Any, device: torch.device) -> tuple[float, dict[str, float]]:
    return lf7._fixed_physics(model, ledger, config, device)


def _audit(model: torch.nn.Module, dataset: Any, ledger: MaterializedPhysicsLedger, config: Any, device: torch.device) -> dict[str, Any]:
    medium = full_medium_audit(model, dataset, device=device)
    fixed, components = _fixed_physics(model, ledger, config, device)
    return {"medium": medium, "fixed_blind_physics": fixed, "fixed_blind_components": components}


def _load_dev_r_model(path: Path, *, physics: Any, config: Any, device: torch.device, contracts: Mapping[str, Mapping[str, Any]]) -> tuple[torch.nn.Module, dict[str, Any]]:
    return lf7.load_dev_r_model(path, physics=physics, config=config, device=device, contracts=contracts)


def _append(handle: Any, payload: Mapping[str, Any]) -> None:
    handle.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n")
    handle.flush()


def _block_sha256(hashes: Sequence[str]) -> str:
    digest = hashlib.sha256(b"PHK_V23_LF8_PHYSICS_BLOCK_V1\n")
    for value in hashes:
        digest.update(value.encode("ascii")); digest.update(b"\n")
    return digest.hexdigest().upper()


def _write_checkpoint(path: Path, *, model: torch.nn.Module, optimizer: torch.optim.Optimizer, config: Any, role: str, accepted: int, attempted: int, source_identity: str, physics_program_sha256: str, physics_object_sha256: str, disposition: str, accepted_learning_rates: Sequence[float]) -> Path:
    payload = _checkpoint_payload(
        model=model, optimizer=optimizer, config=config, update=accepted,
        program_contract_sha256=_sha256_path(V22R_PROGRAM_CONTRACT_PATH),
        method_contract_sha256=_sha256_path(V22R_METHOD_CONTRACT_PATH),
        physical_program_sha256=physics_program_sha256,
        physical_object_sha256=physics_object_sha256,
    )
    payload["lf8"] = {
        "schema_id": "phk-v23-lf8-checkpoint-metadata-v1", "task_id": TASK_ID,
        "role": role, "accepted_optimizer_updates": accepted, "attempted_optimizer_updates": attempted,
        "source_identity": source_identity, "contracts": contract_identity(),
        "parent_checkpoint_sha256": EXPECTED_DEV_R_SHA256, "physics_residual_used": True,
        "medium_gradient_used": False, "medium_acceptance_audit_used": role == P0_FSTAR,
        "runtime_sampling_used": False, "stress_read": False, "disposition": disposition,
        "accepted_learning_rates": list(accepted_learning_rates),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        torch.save(payload, handle)
    return path


def _write_recovery_state(
    path: Path,
    *,
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    accepted: int,
    attempted: int,
    learning_rate: float,
    accepted_learning_rates: Sequence[float],
    source_identity: str,
    physics_program_sha256: str,
    physics_object_sha256: str,
) -> None:
    snapshot = take_snapshot(
        model, optimizer, accepted_updates=accepted, learning_rate=learning_rate
    )
    payload = {
        "schema_id": "phk-v23-lf8-valid-prefix-recovery-v1", "task_id": TASK_ID,
        "accepted_updates": accepted, "attempted_updates": attempted, "learning_rate": learning_rate,
        "accepted_learning_rates": list(accepted_learning_rates), "phase_trainable": any(p.requires_grad for p in phase_parameters(model)),
        "training_snapshot": {
            "model_state_dict": snapshot.model_state,
            "optimizer_state_dict": snapshot.optimizer_state,
            "python_rng_state": snapshot.python_rng,
            "numpy_rng_state": snapshot.numpy_rng,
            "torch_cpu_rng_state": snapshot.torch_rng,
            "torch_cuda_rng_states": snapshot.cuda_rng,
            "accepted_updates": snapshot.accepted_updates,
            "learning_rate": snapshot.learning_rate,
            "phase_trainable": snapshot.phase_trainable,
            "live_state_sha256": snapshot.state_digest,
            "immutable_snapshot_sha256": snapshot.immutable_digest,
        },
        "provenance": {
            "source_identity": source_identity,
            "contracts": contract_identity(),
            "parent_checkpoint_sha256": EXPECTED_DEV_R_SHA256,
            "materialized_ledger_sha256": EXPECTED_LEDGER_SHA256,
            "materialized_ledger_semantic_sha256": EXPECTED_LEDGER_SEMANTIC_SHA256,
            "physics_stream_sha256": EXPECTED_PHYSICS_SHA256,
            "physics_program_sha256": physics_program_sha256,
            "physics_object_sha256": physics_object_sha256,
        },
    }
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        torch.save(payload, handle)
    temporary.replace(path)


def _save_endpoint(directory: Path, *, model: torch.nn.Module, optimizer: torch.optim.Optimizer, config: Any, role: str, accepted: int, attempted: int, source_identity: str, physics_program_sha256: str, physics_object_sha256: str, disposition: str, accepted_learning_rates: Sequence[float], valid: bool) -> tuple[Path | None, Path | None]:
    if not valid:
        return None, None
    checkpoint = _write_checkpoint(
        directory / "checkpoint.pt", model=model, optimizer=optimizer, config=config, role=role,
        accepted=accepted, attempted=attempted, source_identity=source_identity,
        physics_program_sha256=physics_program_sha256, physics_object_sha256=physics_object_sha256,
        disposition=disposition, accepted_learning_rates=accepted_learning_rates,
    )
    prediction = write_prediction_carrier(checkpoint_path=checkpoint, output_path=directory / "prediction.npz", device_name=str(next(model.parameters()).device))
    return checkpoint, prediction


def _run_fstar(*, root: Path, dataset: Any, ledger: MaterializedPhysicsLedger, initial_checkpoint: Path, contracts: Mapping[str, Mapping[str, Any]], qualification: Mapping[str, Any], physics: Any, config: Any, device: torch.device, source_identity: str, physics_program_sha256: str, physics_object_sha256: str) -> dict[str, Any]:
    directory = root / ARM_DIRECTORIES[P0_FSTAR]
    directory.mkdir(parents=True, exist_ok=False)
    model, _ = _load_dev_r_model(initial_checkpoint, physics=physics, config=config, device=device, contracts=contracts)
    baseline = qualification["dev_r_full_medium_audit"]
    optimizer = _make_optimizer(model)
    set_phase_trainable(model, False)
    initial = _audit(model, dataset, ledger, config, device)
    if not math.isclose(initial["fixed_blind_physics"], EXPECTED_J0, rel_tol=1e-10, abs_tol=1e-12):
        raise ValueError("LF8 F* initial fixed-blind objective drift")
    accepted = attempted = accepted_blocks = rejected_attempts = 0
    current_lr = ETA0
    previous_j = float(initial["fixed_blind_physics"])
    last = initial
    accepted_lrs: list[float] = []
    phase_initial = _phase_state_sha256(model)
    numerical_valid = True
    disposition = "COMPLETE"
    with (directory / "telemetry.jsonl").open("x", encoding="utf-8", newline="\n") as telemetry, (directory / "batch_ledger.jsonl").open("x", encoding="utf-8", newline="\n") as batches:
        _append(telemetry, {"arm": P0_FSTAR, "accepted_updates": 0, "attempted_updates": 0, "stage": "PHASE_FROZEN", "learning_rate": current_lr, "audit": initial})
        while accepted < P0_UPDATES:
            snapshot = take_snapshot(model, optimizer, accepted_updates=accepted, learning_rate=current_lr)
            snapshot_hash = snapshot.immutable_digest
            block_number = accepted // BLOCK_SIZE + 1
            accepted_this_block = False
            for lr in available_scales(current_lr):
                if attempted + BLOCK_SIZE > MAX_FILTER_ATTEMPTED_UPDATES:
                    break
                restore_snapshot(snapshot, model, optimizer)
                for group in optimizer.param_groups:
                    group["lr"] = lr
                next_step = accepted + 1
                set_phase_trainable(model, next_step > PHASE_FREEZE_STEPS)
                if next_step == PHASE_FREEZE_STEPS + 1:
                    state_entries = sum(parameter in optimizer.state for parameter in phase_parameters(model))
                    if _phase_state_sha256(model) != phase_initial or state_entries != 0:
                        raise RuntimeError("LF8 F* phase-freeze identity drift")
                train: dict[str, Any] | None = None
                for local in range(BLOCK_SIZE):
                    physics_step = accepted + local + 1
                    batch = ledger.physics_batch(physics_step, device=device)
                    ok, train = _train_one_step(model, optimizer, batch=batch, config=config)
                    attempted += 1
                    _append(batches, {"block": block_number, "scale": lr, "attempted_update": attempted, "proposed_accepted_update": physics_step, "batch_sha256": batch.batch_sha256})
                    if not ok:
                        numerical_valid = False
                        break
                if not numerical_valid:
                    disposition = "POSTSTEP_IDENTITY_INVALID"
                    break
                proposed = _audit(model, dataset, ledger, config, device)
                gate = competence_gate(proposed["medium"], baseline, physics_previous=previous_j, physics_new=proposed["fixed_blind_physics"])
                record = {"arm": P0_FSTAR, "block": block_number, "scale": lr, "accepted_before": accepted, "attempted_updates": attempted, "stage": "PHASE_FROZEN" if accepted < PHASE_FREEZE_STEPS else "JOINT", "physics_block_sha256": _block_sha256(ledger.physics_hashes[accepted:accepted + BLOCK_SIZE]), "train": train, "audit": proposed, "filter_gate": gate, "snapshot_sha256": snapshot_hash}
                if gate["passed"]:
                    accepted += BLOCK_SIZE
                    accepted_blocks += 1
                    current_lr = lr
                    previous_j = float(proposed["fixed_blind_physics"])
                    last = proposed
                    accepted_lrs.append(lr)
                    record.update({"decision": "ACCEPT", "accepted_after": accepted})
                    _append(telemetry, record)
                    _write_recovery_state(
                        directory / "valid-prefix.pt", model=model,
                        optimizer=optimizer, accepted=accepted, attempted=attempted,
                        learning_rate=current_lr,
                        accepted_learning_rates=accepted_lrs,
                        source_identity=source_identity,
                        physics_program_sha256=physics_program_sha256,
                        physics_object_sha256=physics_object_sha256,
                    )
                    accepted_this_block = True
                    break
                rejected_attempts += 1
                restored = restore_snapshot(snapshot, model, optimizer)
                record.update({"decision": "REJECT_ROLLBACK", "accepted_after": accepted, "reject_reason": gate["failed_checks"], "restored_state_sha256": restored, "snapshot_still_immutable": snapshot_digest(snapshot) == snapshot_hash})
                _append(telemetry, record)
            if not numerical_valid:
                break
            if not accepted_this_block:
                disposition = filter_path_disposition(accepted_updates=accepted, identity_valid=True)
                restore_snapshot(snapshot, model, optimizer)
                break
        if accepted == P0_UPDATES:
            disposition = "COMPLETE"
    safety = competence_gate(last["medium"], baseline)
    strict = competence_gate(last["medium"], baseline, strict_timing=True)
    valid = bool(numerical_valid and last["medium"].get("all_values_finite") is True)
    checkpoint, prediction = _save_endpoint(directory, model=model, optimizer=optimizer, config=config, role=P0_FSTAR, accepted=accepted, attempted=attempted, source_identity=source_identity, physics_program_sha256=physics_program_sha256, physics_object_sha256=physics_object_sha256, disposition=disposition, accepted_learning_rates=accepted_lrs, valid=valid)
    result = {
        "arm": P0_FSTAR, "numerical_valid": valid, "endpoint_valid": valid,
        "accepted_updates": accepted, "attempted_updates": attempted,
        "accepted_blocks": accepted_blocks, "rejected_block_attempts": rejected_attempts,
        "accepted_learning_rates": accepted_lrs, "final_learning_rate": current_lr,
        "disposition": disposition, "safety_gate": safety, "strict_gate": strict,
        "fixed_blind_physics": float(last["fixed_blind_physics"]),
        "fixed_blind_ratio_to_DEV_R": float(last["fixed_blind_physics"]) / EXPECTED_J0,
        "final_audit": last,
        "checkpoint_sha256": _sha256_path(checkpoint) if checkpoint else None,
        "prediction_sha256": _sha256_path(prediction) if prediction else None,
    }
    _write_json_exclusive(directory / "gate.json", result)
    _write_json_exclusive(directory / "exit.json", {"returncode": 0 if valid else 1, **{key: result[key] for key in ("accepted_updates", "attempted_updates", "disposition", "numerical_valid")}})
    del optimizer, model
    if torch.cuda.is_available(): torch.cuda.empty_cache()
    return result


def _run_schedule_control(*, schedule: Sequence[float], root: Path, ledger: MaterializedPhysicsLedger, initial_checkpoint: Path, contracts: Mapping[str, Mapping[str, Any]], physics: Any, config: Any, device: torch.device, source_identity: str, physics_program_sha256: str, physics_object_sha256: str) -> dict[str, Any]:
    if len(schedule) != BLOCK_COUNT:
        raise ValueError("LF8 control schedule length drift")
    directory = root / ARM_DIRECTORIES[P0_C]
    directory.mkdir(parents=True, exist_ok=False)
    model, _ = _load_dev_r_model(initial_checkpoint, physics=physics, config=config, device=device, contracts=contracts)
    optimizer = _make_optimizer(model)
    set_phase_trainable(model, False)
    phase_initial = _phase_state_sha256(model)
    numerical_valid = True
    with (directory / "telemetry.jsonl").open("x", encoding="utf-8", newline="\n") as telemetry, (directory / "batch_ledger.jsonl").open("x", encoding="utf-8", newline="\n") as batches:
        for block, lr in enumerate(schedule, start=1):
            for group in optimizer.param_groups: group["lr"] = float(lr)
            start = (block - 1) * BLOCK_SIZE + 1
            if start == PHASE_FREEZE_STEPS + 1:
                if _phase_state_sha256(model) != phase_initial or sum(p in optimizer.state for p in phase_parameters(model)) != 0:
                    raise RuntimeError("LF8 control phase-freeze identity drift")
                set_phase_trainable(model, True)
            train: dict[str, Any] | None = None
            for step in range(start, start + BLOCK_SIZE):
                batch = ledger.physics_batch(step, device=device)
                ok, train = _train_one_step(model, optimizer, batch=batch, config=config)
                _append(batches, {"block": block, "accepted_update": step, "learning_rate": lr, "batch_sha256": batch.batch_sha256})
                if not ok:
                    numerical_valid = False
                    break
            if not numerical_valid: break
            fixed_j, fixed_components = _fixed_physics(model, ledger, config, device)
            _append(telemetry, {"arm": P0_C, "block": block, "accepted_updates": block * BLOCK_SIZE, "learning_rate": lr, "fixed_blind_physics": fixed_j, "fixed_blind_components": fixed_components, "train": train})
    accepted = P0_UPDATES if numerical_valid else (block - 1) * BLOCK_SIZE
    fixed_j, fixed_components = _fixed_physics(model, ledger, config, device) if numerical_valid else (None, None)
    valid = bool(numerical_valid and accepted == P0_UPDATES and fixed_j is not None and math.isfinite(fixed_j))
    checkpoint, prediction = _save_endpoint(directory, model=model, optimizer=optimizer, config=config, role=P0_C, accepted=accepted, attempted=accepted, source_identity=source_identity, physics_program_sha256=physics_program_sha256, physics_object_sha256=physics_object_sha256, disposition="COMPLETE" if valid else "POSTSTEP_IDENTITY_INVALID", accepted_learning_rates=schedule, valid=valid)
    result = {"arm": P0_C, "numerical_valid": valid, "endpoint_valid": valid, "accepted_updates": accepted, "attempted_updates": accepted, "accepted_blocks": accepted // BLOCK_SIZE, "accepted_learning_rates": list(schedule), "disposition": "COMPLETE" if valid else "POSTSTEP_IDENTITY_INVALID", "safety_gate": {"status": "PENDING_POST_SHUTDOWN_LOCAL_ADJUDICATION"}, "strict_gate": {"status": "PENDING_POST_SHUTDOWN_LOCAL_ADJUDICATION"}, "fixed_blind_physics": float(fixed_j) if fixed_j is not None else None, "fixed_blind_components": fixed_components, "fixed_blind_ratio_to_DEV_R": float(fixed_j) / EXPECTED_J0 if fixed_j is not None else None, "medium_audit_performed": False, "checkpoint_sha256": _sha256_path(checkpoint) if checkpoint else None, "prediction_sha256": _sha256_path(prediction) if prediction else None}
    _write_json_exclusive(directory / "gate.json", result)
    _write_json_exclusive(directory / "exit.json", {"returncode": 0 if valid else 1, "accepted_updates": accepted, "numerical_valid": valid})
    del optimizer, model
    if torch.cuda.is_available(): torch.cuda.empty_cache()
    return result


def matched_schedule_outcome(arms: Mapping[str, Mapping[str, Any]]) -> str:
    fstar = arms[P0_FSTAR]
    if not fstar.get("endpoint_valid"):
        return "MATCHED_ATTRIBUTION_UNAVAILABLE"
    if int(fstar.get("accepted_updates", 0)) < P0_UPDATES:
        return "FILTER_PATH_STALLED_OR_INSUFFICIENT"
    control = arms.get(P0_C)
    if not control or not control.get("endpoint_valid"):
        return "MATCHED_ATTRIBUTION_UNAVAILABLE"
    if fstar.get("safety_gate", {}).get("passed") and control.get("safety_gate", {}).get("passed"):
        return "SCHEDULE_SUFFICIENT_FILTER_NOT_LOAD_BEARING"
    if fstar.get("safety_gate", {}).get("passed") and not control.get("safety_gate", {}).get("passed"):
        return "COMPETENCE_FILTER_LOAD_BEARING_FOR_PRESERVATION"
    return "MATCHED_ATTRIBUTION_UNAVAILABLE"


def _partial_failure_arm(root: Path, role: str, exc: Exception) -> dict[str, Any]:
    """Persist enough post-step evidence for recovery and terminal classification."""

    directory = root / ARM_DIRECTORIES[role]
    directory.mkdir(parents=True, exist_ok=True)
    accepted = attempted = 0
    recovery = directory / "valid-prefix.pt"
    if recovery.is_file():
        payload = torch.load(recovery, map_location="cpu", weights_only=False)
        accepted = int(payload.get("accepted_updates", 0))
        attempted = int(payload.get("attempted_updates", 0))
    result = {
        "arm": role,
        "numerical_valid": False,
        "endpoint_valid": False,
        "accepted_updates": accepted,
        "attempted_updates": attempted,
        "accepted_blocks": accepted // BLOCK_SIZE,
        "accepted_learning_rates": [],
        "disposition": "POSTSTEP_IDENTITY_INVALID",
        "safety_gate": {"passed": False, "failed_checks": ["poststep_exception"]},
        "strict_gate": {"passed": False, "failed_checks": ["poststep_exception"]},
        "error": {"type": type(exc).__name__, "message": str(exc)},
    }
    if not (directory / "gate.json").exists():
        _write_json_exclusive(directory / "gate.json", result)
    if not (directory / "exit.json").exists():
        _write_json_exclusive(
            directory / "exit.json",
            {
                "returncode": 1,
                "accepted_updates": accepted,
                "attempted_updates": attempted,
                "disposition": "POSTSTEP_IDENTITY_INVALID",
                "error_type": type(exc).__name__,
            },
        )
    return result


def execute_gpu_campaign(*, output_root: Path, medium_carrier: Path, initial_checkpoint: Path, materialized_ledger: Path, cpu_qualification_path: Path, device_name: str, source_identity: str) -> dict[str, Any]:
    contracts = load_contracts()
    qualification = read_cpu_qualification(cpu_qualification_path)
    if not device_name.startswith("cuda") or not torch.cuda.is_available(): raise RuntimeError("LF8 requires CUDA")
    device = torch.device(device_name)
    if torch.cuda.get_device_name(device) != "Tesla V100-PCIE-32GB": raise RuntimeError("LF8 requires Tesla V100-PCIE-32GB")
    root = Path(output_root).resolve()
    if root.exists() and (not root.is_dir() or any(root.iterdir())): raise FileExistsError(f"LF8 output root must be empty: {root}")
    root.mkdir(parents=True, exist_ok=True)
    config = build_training_config(device_name)
    physics, physics_program_sha256, physics_object_sha256 = load_case_physics(config.case_control)
    dataset = load_medium_dataset(Path(medium_carrier), physics=physics, contracts=contracts)
    if dataset.partition_sha256 != EXPECTED_PARTITION_SHA256: raise ValueError("LF8 partition drift")
    ledger = MaterializedPhysicsLedger(Path(materialized_ledger), contracts=contracts, qualification=qualification)
    random.seed(17); np.random.seed(17); torch.manual_seed(17); torch.cuda.manual_seed_all(17)
    started = datetime.now(timezone.utc).isoformat()
    arms: dict[str, Any] = {}
    poststep_error: dict[str, str] | None = None
    try:
        fstar = _run_fstar(root=root, dataset=dataset, ledger=ledger, initial_checkpoint=Path(initial_checkpoint), contracts=contracts, qualification=qualification, physics=physics, config=config, device=device, source_identity=source_identity, physics_program_sha256=physics_program_sha256, physics_object_sha256=physics_object_sha256)
        arms[P0_FSTAR] = fstar
        if schedule_control_required(fstar):
            random.seed(17); np.random.seed(17); torch.manual_seed(17); torch.cuda.manual_seed_all(17)
            arms[P0_C] = _run_schedule_control(schedule=replay_schedule(fstar), root=root, ledger=ledger, initial_checkpoint=Path(initial_checkpoint), contracts=contracts, physics=physics, config=config, device=device, source_identity=source_identity, physics_program_sha256=physics_program_sha256, physics_object_sha256=physics_object_sha256)
    except Exception as exc:
        failed_role = P0_C if P0_FSTAR in arms else P0_FSTAR
        arms[failed_role] = _partial_failure_arm(root, failed_role, exc)
        poststep_error = {"arm": failed_role, "type": type(exc).__name__, "message": str(exc)}
    mechanism = (
        "PENDING_POST_SHUTDOWN_LOCAL_ADJUDICATION"
        if P0_C in arms
        else (
            "MATCHED_ATTRIBUTION_UNAVAILABLE"
            if poststep_error is not None
            else "FILTER_PATH_STALLED_OR_INSUFFICIENT"
        )
    )
    artifacts: dict[str, Any] = {}
    for role in arms:
        directory = root / ARM_DIRECTORIES[role]
        for name in ("telemetry.jsonl", "batch_ledger.jsonl", "valid-prefix.pt", "checkpoint.pt", "prediction.npz", "gate.json", "exit.json"):
            path = directory / name
            if path.is_file(): artifacts[f"{role}:{name}"] = _artifact_record(path, root)
    summary = {"schema_id": "phk-v23-lf8-reference-blind-run-summary-v1", "task_id": TASK_ID, "title": TITLE, "status": "LF8_POSTSTEP_IDENTITY_INVALID" if poststep_error else "LF8_REFERENCE_BLIND_GPU_CAMPAIGN_COMPLETE", "started_at_utc": started, "finished_at_utc": datetime.now(timezone.utc).isoformat(), "source_identity": source_identity, "gpu": torch.cuda.get_device_name(device), "dtype": "FLOAT64", "seed": 17, "arms": arms, "schedule_control_executed": P0_C in arms, "mechanism_outcome": mechanism, "poststep_error": poststep_error, "ledger": {"sha256": _sha256_path(Path(materialized_ledger)), "semantic_sha256": EXPECTED_LEDGER_SEMANTIC_SHA256, "physics_stream_sha256": ledger.physics_sha256, "fixed_blind_pool_sha256": EXPECTED_FIXED_POOL_SHA256}, "artifacts": artifacts, "medium_gradient_used": False, "runtime_sampling_used": False, "fine_extra_lf_only_evaluator_stress_read": False}
    _write_json_exclusive(root / "run_summary.json", summary)
    return summary


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--medium-carrier", type=Path, required=True)
    parser.add_argument("--initial-checkpoint", type=Path, required=True)
    parser.add_argument("--materialized-ledger", type=Path, required=True)
    parser.add_argument("--cpu-qualification", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--source-identity", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    summary = execute_gpu_campaign(output_root=args.output_root, medium_carrier=args.medium_carrier, initial_checkpoint=args.initial_checkpoint, materialized_ledger=args.materialized_ledger, cpu_qualification_path=args.cpu_qualification, device_name=args.device, source_identity=args.source_identity)
    print(json.dumps({"status": summary["status"], "mechanism_outcome": summary["mechanism_outcome"], "schedule_control_executed": summary["schedule_control_executed"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ARM_ORDER", "BLOCK_COUNT", "BLOCK_SIZE", "ETA0", "LR_SCALES", "MAX_FILTER_ATTEMPTED_UPDATES",
    "P0_C", "P0_FSTAR", "P0_UPDATES", "PHASE_FREEZE_STEPS", "TASK_ID", "TrainingSnapshot",
    "available_scales", "competence_gate", "contract_identity", "execute_gpu_campaign",
    "filter_path_disposition", "load_contracts", "matched_schedule_outcome", "phase_parameters",
    "read_cpu_qualification", "replay_schedule", "restore_snapshot", "schedule_control_required",
    "set_phase_trainable", "snapshot_digest", "snapshot_optimizer_aliases", "take_snapshot", "update_digest",
]
