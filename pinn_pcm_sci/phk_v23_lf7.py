"""LF7 matched small-step and competence-filtered physics refinement.

The two arms start from the exact LF6 DEV-R checkpoint and consume the same
pre-materialized 1,200-step physics stream.  No sampler exists in this module.
P0-F audits medium fields only after a proposed 25-step physics block; medium
values never enter an autograd graph or the training objective.
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

from .phk_v22r_pinn import PhkV22RModel
from .phk_v22r_prediction import write_prediction_carrier
from .phk_v22r_training import (
    METHOD_CONTRACT_PATH as V22R_METHOD_CONTRACT_PATH,
    PROGRAM_CONTRACT_PATH as V22R_PROGRAM_CONTRACT_PATH,
    ROOT,
    _checkpoint_payload,
    load_case_physics,
)
from .phk_v23_lf0 import (
    PhysicsBatch,
    _artifact_record,
    _physics_objective,
    _read_json,
    _sha256_path,
    _write_json_exclusive,
)
from .phk_v23_lf1 import build_range_preserving_model
from .phk_v23_lf2 import _batch_sha256, load_medium_dataset
from .phk_v23_lf3 import _phase_state_sha256, build_training_config, full_medium_audit
from .phk_v23_lf4 import _field_state_sha256
from .phk_v23_lf6 import (
    LEDGER_ARRAY_NAMES,
    _decode_hashes,
    _fixed_pool_digest,
    array_sha256,
    rolling_batch_sha256,
    semantic_ledger_sha256,
)


TASK_ID = "PHK_V23_LF7_COMPETENCE_FILTERED_BLOCKWISE_BACKTRACKING_PHYSICS_REFINEMENT_PILOT_EXECUTE"
TITLE = "PHK-V2.3 LF7 competence-filtered blockwise backtracking physics refinement pilot"
P0_S = "P0_S_FIXED_SMALL_STEP_CONTROL"
P0_F = "P0_F_COMPETENCE_FILTERED_BACKTRACKING"
ARM_ORDER = (P0_S, P0_F)
ARM_DIRECTORIES = {P0_S: "p0-small", P0_F: "p0-filter"}

P0_UPDATES = 1200
PHASE_FREEZE_STEPS = 550
BLOCK_SIZE = 25
BLOCK_COUNT = 48
ETA0 = 1.25e-4
LR_SCALES = (ETA0, ETA0 / 2.0, ETA0 / 4.0, ETA0 / 8.0, ETA0 / 16.0)
MAX_FILTER_ATTEMPTED_UPDATES = 2400
EXPECTED_PHYSICS_SHA256 = "536E6706A0B68EBB1277A97F402D273AFA2EA1E0B27106F26CB4222B7EC05C53"
EXPECTED_FIXED_POOL_SHA256 = "FD285AFC67C011CE9778E36C5FEE8FA7EAECB933690AF346993B7677AF0E64CF"
EXPECTED_LEDGER_SHA256 = "29E02DAF81A07BA4AF2B95B354126E75E9419AAE094E9486589455D31D2D6801"
EXPECTED_LEDGER_MANIFEST_SHA256 = "3CFA268CFB22CF225ABB92BFD7F9F00353634AF7AFEE7AA607EC59FE4F4C8F90"
EXPECTED_LEDGER_SEMANTIC_SHA256 = "0E2F680D33C4489F6092CB5D01E87483F7ECDA8290CD3E2C24EBDD06B3DA2B7F"
EXPECTED_DEV_R_SHA256 = "7CFDD98E3A03BE29BBE587042967BD44E72D140AE7AC3396CB35E0CF5748F499"
EXPECTED_PARTITION_SHA256 = "EFD70886DD85AC467F06F38B48FB0EE6C0132471CE74817E3A4D68E752B7A515"
EXPECTED_J0 = 4.9278721846990505

PROGRAM_CONTRACT_PATH = ROOT / "configs/phk_v23/program_contract_lf7_competence_filter.json"
METHOD_CONTRACT_PATH = ROOT / "configs/phk_v23/method_contract_lf7_competence_filter.json"
DATA_CONTRACT_PATH = ROOT / "configs/phk_v23/data_contract_lf7_competence_filter.json"
DECISION_CONTRACT_PATH = ROOT / "configs/phk_v23/decision_contract_lf7_competence_filter.json"
CONTRACT_PATHS = {
    "program": PROGRAM_CONTRACT_PATH,
    "method": METHOD_CONTRACT_PATH,
    "data": DATA_CONTRACT_PATH,
    "decision": DECISION_CONTRACT_PATH,
}
EXPECTED_SCHEMAS = {
    "program": "phk-v23-lf7-program-contract-v1",
    "method": "phk-v23-lf7-method-contract-v1",
    "data": "phk-v23-lf7-data-contract-v1",
    "decision": "phk-v23-lf7-decision-contract-v1",
}


def load_contracts() -> dict[str, dict[str, Any]]:
    contracts = {name: _read_json(path) for name, path in CONTRACT_PATHS.items()}
    for name, schema in EXPECTED_SCHEMAS.items():
        if contracts[name].get("schema_id") != schema:
            raise ValueError(f"unsupported LF7 {name} contract")
    relative = {name: path.relative_to(ROOT).as_posix() for name, path in CONTRACT_PATHS.items()}
    if contracts["program"].get("phase_id") != TASK_ID:
        raise ValueError("LF7 task identity drift")
    if any(contracts[name].get("program_contract") != relative["program"] for name in ("method", "data", "decision")):
        raise ValueError("LF7 program binding drift")
    if contracts["decision"].get("method_contract") != relative["method"] or contracts["decision"].get("data_contract") != relative["data"]:
        raise ValueError("LF7 decision binding drift")
    limits = contracts["program"]["hard_limits"]
    if limits.get("maximum_scientific_gpu_trajectories") != 2 or limits.get("P0_S_optimizer_updates") != P0_UPDATES:
        raise ValueError("LF7 trajectory bound drift")
    if limits.get("P0_F_maximum_accepted_updates") != P0_UPDATES or limits.get("P0_F_maximum_attempted_updates") != MAX_FILTER_ATTEMPTED_UPDATES:
        raise ValueError("LF7 filter bound drift")
    identity = contracts["method"]["identity"]
    if identity.get("dtype") != "FLOAT64" or identity.get("seed") != 17 or float(identity.get("initial_learning_rate")) != ETA0:
        raise ValueError("LF7 method identity drift")
    if tuple(float(value) for value in contracts["method"]["P0_F"]["dyadic_learning_rates"]) != LR_SCALES:
        raise ValueError("LF7 dyadic scale drift")
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
        raise ValueError("LF7 materialized ledger binding drift")
    if data.get("partition_sha256") != EXPECTED_PARTITION_SHA256 or data["initial_DEV_R"].get("checkpoint_sha256") != EXPECTED_DEV_R_SHA256:
        raise ValueError("LF7 frozen input identity drift")
    if len(contracts["decision"].get("machine_outcomes_and_unique_next", {})) != 11:
        raise ValueError("LF7 terminal outcome map is incomplete")
    if contracts["decision"].get("stress_status") != "TWO_STRESS_REFERENCES_SEALED_UNREAD":
        raise PermissionError("LF7 stress boundary drift")
    return contracts


def contract_identity() -> dict[str, dict[str, str]]:
    return {
        name: {"path": path.relative_to(ROOT).as_posix(), "sha256": _sha256_path(path)}
        for name, path in CONTRACT_PATHS.items()
    }


def read_cpu_qualification(path: Path) -> dict[str, Any]:
    supplied = Path(path).resolve()
    payload = _read_json(supplied)
    if payload.get("schema_id") != "phk-v23-lf7-cpu-qualification-v1" or payload.get("task_id") != TASK_ID:
        raise ValueError("LF7 CPU qualification identity drift")
    if payload.get("gate_outcome") != "LF7_CPU_QUALIFICATION_PASS" or payload.get("scientific_optimizer_updates") != 0:
        raise PermissionError("LF7 CPU qualification did not pass")
    if payload.get("checks") and not all(bool(value) for value in payload["checks"].values()):
        raise PermissionError("LF7 CPU qualification contains a failed check")
    return payload


class MaterializedPhysicsLedger:
    """Strictly verify and expose the inherited LF6 arrays without sampling."""

    def __init__(self, path: Path, *, contracts: Mapping[str, Mapping[str, Any]], qualification: Mapping[str, Any]) -> None:
        binding = contracts["data"]["materialized_ledger"]
        supplied = Path(path).resolve()
        expected = (ROOT / binding["path"]).resolve()
        if supplied != expected or not supplied.is_file() or _sha256_path(supplied) != binding["file_sha256"]:
            raise ValueError("LF7 materialized ledger file binding drift")
        manifest_path = (ROOT / binding["manifest_path"]).resolve()
        if not manifest_path.is_file() or _sha256_path(manifest_path) != binding["manifest_sha256"]:
            raise ValueError("LF7 materialized ledger manifest drift")
        manifest = _read_json(manifest_path)
        if manifest.get("schema_id") != "phk-v23-lf6-materialized-ledger-manifest-v1":
            raise ValueError("LF7 inherited ledger schema drift")
        with np.load(supplied, allow_pickle=False) as archive:
            if set(archive.files) != set(LEDGER_ARRAY_NAMES):
                raise ValueError("LF7 ledger array key drift")
            self.arrays = {name: np.asarray(archive[name]) for name in LEDGER_ARRAY_NAMES}
        hashes = {name: array_sha256(name, value) for name, value in self.arrays.items()}
        for name in LEDGER_ARRAY_NAMES:
            record = manifest.get("arrays", {}).get(name, {})
            if hashes[name] != record.get("sha256") or list(self.arrays[name].shape) != record.get("shape") or self.arrays[name].dtype.str != record.get("dtype"):
                raise ValueError(f"LF7 ledger array drift: {name}")
        if semantic_ledger_sha256(hashes) != binding["semantic_sha256"] or manifest.get("semantic_sha256") != binding["semantic_sha256"]:
            raise ValueError("LF7 ledger semantic identity drift")
        self.physics_hashes = _decode_hashes(self.arrays["p0_batch_sha256"])
        if len(self.physics_hashes) != P0_UPDATES:
            raise ValueError("LF7 physics stream length drift")
        for index in range(P0_UPDATES):
            windows = int(self.arrays["p0_active_windows"][index])
            tensors = [torch.as_tensor(self.arrays[f"p0_{name}"][index], dtype=torch.float64) for name in ("interior", "left", "right", "bottom", "top", "initial")]
            actual = (
                _batch_sha256(tensors[0], metadata=f"PHYSICS_INTERIOR_WINDOWS:{windows}"),
                _batch_sha256(*tensors[1:5], metadata=f"PHYSICS_BOUNDARY_WINDOWS:{windows}"),
                _batch_sha256(tensors[5], metadata=f"PHYSICS_INITIAL_WINDOWS:{windows}"),
                _batch_sha256(*tensors, metadata=f"PHYSICS_WINDOWS:{windows}"),
            )
            expected_components = (
                _decode_hashes(self.arrays["p0_interior_sha256"][index:index + 1])[0],
                _decode_hashes(self.arrays["p0_boundary_sha256"][index:index + 1])[0],
                _decode_hashes(self.arrays["p0_initial_sha256"][index:index + 1])[0],
                self.physics_hashes[index],
            )
            if actual != expected_components:
                raise ValueError(f"LF7 materialized physics step hash drift at {index + 1}")
        self.physics_sha256 = rolling_batch_sha256("PHK_V23_LF0_PHYSICS_BATCHES", self.physics_hashes)
        if self.physics_sha256 != EXPECTED_PHYSICS_SHA256 or _fixed_pool_digest(self.arrays) != EXPECTED_FIXED_POOL_SHA256:
            raise ValueError("LF7 inherited stream aggregate drift")
        qledger = qualification.get("ledger", {})
        required_q = {
            "file_sha256": EXPECTED_LEDGER_SHA256,
            "manifest_sha256": EXPECTED_LEDGER_MANIFEST_SHA256,
            "semantic_sha256": EXPECTED_LEDGER_SEMANTIC_SHA256,
            "physics_1200_sha256": EXPECTED_PHYSICS_SHA256,
            "fixed_blind_pool_sha256": EXPECTED_FIXED_POOL_SHA256,
        }
        if any(qledger.get(key) != value for key, value in required_q.items()):
            raise ValueError("LF7 qualification ledger binding drift")

    def physics_batch(self, step: int, *, device: torch.device) -> PhysicsBatch:
        if step < 1 or step > P0_UPDATES:
            raise ValueError("LF7 physics step out of range")
        index = step - 1
        tensor = lambda name: torch.as_tensor(self.arrays[f"p0_{name}"][index], dtype=torch.float64, device=device)
        return PhysicsBatch(
            interior=tensor("interior"),
            boundary={name: tensor(name) for name in ("left", "right", "bottom", "top")},
            initial=tensor("initial"),
            active_windows=int(self.arrays["p0_active_windows"][index]),
            refreshed=bool(self.arrays["p0_refreshed"][index]),
            interior_sha256=_decode_hashes(self.arrays["p0_interior_sha256"][index:index + 1])[0],
            boundary_sha256=_decode_hashes(self.arrays["p0_boundary_sha256"][index:index + 1])[0],
            initial_sha256=_decode_hashes(self.arrays["p0_initial_sha256"][index:index + 1])[0],
            batch_sha256=self.physics_hashes[index],
        )

    def fixed_batch(self, *, device: torch.device) -> PhysicsBatch:
        tensor = lambda name: torch.as_tensor(self.arrays[f"fixed_{name}"], dtype=torch.float64, device=device).clone()
        return PhysicsBatch(
            interior=tensor("interior"),
            boundary={name: tensor(name) for name in ("left", "right", "bottom", "top")},
            initial=tensor("initial"),
            active_windows=4,
            refreshed=True,
            interior_sha256="MATERIALIZED_FIXED_INTERIOR",
            boundary_sha256="MATERIALIZED_FIXED_BOUNDARY",
            initial_sha256="MATERIALIZED_FIXED_INITIAL",
            batch_sha256=EXPECTED_FIXED_POOL_SHA256,
        )


def _structural_architecture(value: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(value)
    result.pop("trainable_parameter_count", None)
    return result


def load_dev_r_model(path: Path, *, physics: Any, config: Any, device: torch.device, contracts: Mapping[str, Mapping[str, Any]]) -> tuple[PhkV22RModel, dict[str, Any]]:
    supplied = Path(path).resolve()
    binding = contracts["data"]["initial_DEV_R"]
    expected_path = (ROOT / binding["checkpoint_path"]).resolve()
    if supplied != expected_path or not supplied.is_file() or _sha256_path(supplied) != EXPECTED_DEV_R_SHA256:
        raise ValueError("LF7 exact DEV-R checkpoint binding drift")
    payload = torch.load(supplied, map_location=device, weights_only=False)
    metadata = payload.get("lf6", {})
    if payload.get("schema_id") != "phk-v22r-checkpoint-v1-1" or payload.get("update") != 400:
        raise PermissionError("LF7 initialization is not an LF6 development checkpoint")
    if metadata.get("task_id") != "PHK_V23_LF6_EVENT_FRONTIER_RANK_BAND_AND_SAFETY_GATED_PHYSICS_PILOT_EXECUTE" or metadata.get("role") != "DEV_R_EVENT_FRONTIER_RANK_BAND":
        raise PermissionError("LF7 initialization is not exact LF6 DEV-R")
    model = build_range_preserving_model(physics=physics, config=config).to(device=device, dtype=torch.float64)
    if _structural_architecture(payload.get("architecture", {})) != _structural_architecture(model.architecture_manifest()):
        raise ValueError("LF7 DEV-R architecture drift")
    model.load_state_dict(payload["model_state_dict"], strict=True)
    for parameter in model.parameters():
        parameter.requires_grad_(True)
    model.train()
    return model, payload


def _cycle(audit: Mapping[str, Any], cycle: int) -> Mapping[str, Any]:
    return audit["event_metrics"][f"cycle_{cycle}"]


def competence_gate(audit: Mapping[str, Any], baseline: Mapping[str, Any], *, strict_timing: bool = False, physics_previous: float | None = None, physics_new: float | None = None) -> dict[str, Any]:
    global_potential = audit.get("potential_maximum_principle", {}).get("global", {})
    phase_range = audit.get("phase_range", {})
    checks: dict[str, bool] = {
        "finite": audit.get("all_values_finite") is True,
        "phase_range": float(phase_range.get("minimum", -math.inf)) >= -1.0e-10 and float(phase_range.get("maximum", math.inf)) <= 1.0000000001,
        "potential": bool(global_potential.get("passed")) and float(global_potential.get("maximum_absolute_excess", math.inf)) <= 1.0e-6 and float(global_potential.get("violation_fraction", math.inf)) == 0.0,
        "phase_maximum": float(audit.get("phase_maximum", -math.inf)) >= 0.90,
        "two_cycle_events": audit.get("two_cycle_events") is True,
    }
    ratios = {
        field: float(audit["weighted_errors"][field]) / float(baseline["weighted_errors"][field])
        for field in ("potential", "temperature", "phase")
    }
    ratios["topology"] = float(audit["topology_weighted_loss"]) / float(baseline["topology_weighted_loss"])
    maxima = {"potential": 1.20, "temperature": 1.05, "phase": 1.05, "topology": 1.05}
    for field, maximum in maxima.items():
        checks[f"relative_{field}"] = math.isfinite(ratios[field]) and ratios[field] <= maximum
    topology = audit["event_topology_hard_guard"]["cycles"]
    timing_limits = (0.005, 0.005) if strict_timing else (0.010533333334333338, 0.005000000000999893)
    for cycle in (1, 2):
        metrics = _cycle(audit, cycle)
        topo = topology[cycle - 1]
        prefix = f"cycle_{cycle}"
        recall = metrics.get("hard_recall")
        precision = metrics.get("hard_precision")
        mass = metrics.get("hard_active_mass_ratio")
        timing = metrics.get("event_time_absolute_error")
        checks[f"{prefix}_recall"] = recall is not None and float(recall) >= 0.90
        checks[f"{prefix}_precision"] = precision is not None and float(precision) >= 0.80
        checks[f"{prefix}_mass"] = mass is not None and 0.80 <= float(mass) <= 1.20
        checks[f"{prefix}_timing"] = timing is not None and float(timing) <= timing_limits[cycle - 1]
        checks[f"{prefix}_roi_peak"] = float(topo["peak_roi_fraction"]) >= 0.02
        checks[f"{prefix}_full_peak"] = float(topo["peak_full_domain_fraction"]) <= 0.45
        checks[f"{prefix}_outside_peak"] = float(topo["peak_outside_roi_fraction"]) <= 0.10
        checks[f"{prefix}_recovery"] = float(topo["recovery_fraction"]) >= 0.70
    required_decrease = None
    if physics_previous is not None and physics_new is not None:
        required_decrease = max(1.0e-12, 1.0e-8 * float(physics_previous))
        checks["fixed_blind_strict_improvement"] = math.isfinite(float(physics_new)) and float(physics_new) <= float(physics_previous) - required_decrease
    failed = sorted(name for name, passed in checks.items() if not passed)
    return {
        "passed": not failed,
        "checks": checks,
        "failed_checks": failed,
        "relative_DEV_R": ratios,
        "strict_timing": strict_timing,
        "physics_previous": physics_previous,
        "physics_new": physics_new,
        "required_decrease": required_decrease,
    }


def _set_phase_trainable(model: PhkV22RModel, trainable: bool) -> None:
    model.encoders["phase"].requires_grad_(trainable)
    model.heads["phase"].requires_grad_(trainable)


def _phase_parameters(model: PhkV22RModel) -> tuple[torch.nn.Parameter, ...]:
    return tuple(model.encoders["phase"].parameters()) + tuple(model.heads["phase"].parameters())


def _append(handle: Any, payload: Mapping[str, Any]) -> None:
    handle.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n")
    handle.flush()


def _update_digest(digest: Any, value: Any) -> None:
    if torch.is_tensor(value):
        array = value.detach().cpu().contiguous().numpy()
        digest.update(b"T"); digest.update(array.dtype.str.encode("ascii")); digest.update(str(tuple(array.shape)).encode("ascii")); digest.update(array.tobytes())
    elif isinstance(value, np.ndarray):
        array = np.ascontiguousarray(value)
        digest.update(b"N"); digest.update(array.dtype.str.encode("ascii")); digest.update(str(tuple(array.shape)).encode("ascii")); digest.update(array.tobytes())
    elif isinstance(value, Mapping):
        digest.update(b"D")
        for key in sorted(value, key=lambda item: repr(item)):
            _update_digest(digest, key); _update_digest(digest, value[key])
    elif isinstance(value, (tuple, list)):
        digest.update(b"L")
        for item in value:
            _update_digest(digest, item)
    else:
        digest.update((type(value).__name__ + ":" + repr(value)).encode("utf-8"))


def state_digest(model: PhkV22RModel, optimizer: torch.optim.Optimizer) -> str:
    digest = hashlib.sha256(b"PHK_V23_LF7_TRAINING_STATE_V1\n")
    _update_digest(digest, model.state_dict())
    _update_digest(digest, optimizer.state_dict())
    _update_digest(digest, random.getstate())
    _update_digest(digest, np.random.get_state())
    _update_digest(digest, torch.get_rng_state())
    if torch.cuda.is_available():
        _update_digest(digest, torch.cuda.get_rng_state_all())
    return digest.hexdigest().upper()


def rng_digest() -> str:
    digest = hashlib.sha256(b"PHK_V23_LF7_RNG_STATE_V1\n")
    _update_digest(digest, random.getstate())
    _update_digest(digest, np.random.get_state())
    _update_digest(digest, torch.get_rng_state())
    if torch.cuda.is_available():
        _update_digest(digest, torch.cuda.get_rng_state_all())
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
    digest: str
    rng_digest: str


def take_snapshot(model: PhkV22RModel, optimizer: torch.optim.Optimizer, *, accepted_updates: int, learning_rate: float) -> TrainingSnapshot:
    return TrainingSnapshot(
        model_state=copy.deepcopy(model.state_dict()),
        optimizer_state=copy.deepcopy(optimizer.state_dict()),
        python_rng=random.getstate(),
        numpy_rng=copy.deepcopy(np.random.get_state()),
        torch_rng=torch.get_rng_state().clone(),
        cuda_rng=[value.clone() for value in torch.cuda.get_rng_state_all()] if torch.cuda.is_available() else [],
        accepted_updates=int(accepted_updates),
        learning_rate=float(learning_rate),
        phase_trainable=any(parameter.requires_grad for parameter in _phase_parameters(model)),
        digest=state_digest(model, optimizer),
        rng_digest=rng_digest(),
    )


def restore_snapshot(snapshot: TrainingSnapshot, model: PhkV22RModel, optimizer: torch.optim.Optimizer) -> str:
    # Loading an optimizer state can retain tensor aliases when source and
    # destination already share dtype/device.  A subsequent Adam step would
    # then mutate the saved moments themselves and make rollback impossible.
    # Load from fresh deep copies so the snapshot remains an immutable value.
    model.load_state_dict(copy.deepcopy(snapshot.model_state), strict=True)
    optimizer.load_state_dict(copy.deepcopy(snapshot.optimizer_state))
    _set_phase_trainable(model, snapshot.phase_trainable)
    random.setstate(copy.deepcopy(snapshot.python_rng))
    np.random.set_state(copy.deepcopy(snapshot.numpy_rng))
    torch.set_rng_state(snapshot.torch_rng.clone())
    if torch.cuda.is_available():
        torch.cuda.set_rng_state_all([value.clone() for value in snapshot.cuda_rng])
    for group in optimizer.param_groups:
        group["lr"] = snapshot.learning_rate
    restored = state_digest(model, optimizer)
    if restored != snapshot.digest or rng_digest() != snapshot.rng_digest:
        raise RuntimeError("LF7 block rollback state identity drift")
    return restored


def _fixed_physics(model: PhkV22RModel, ledger: MaterializedPhysicsLedger, config: Any, device: torch.device) -> tuple[float, dict[str, float]]:
    batch = ledger.fixed_batch(device=device)
    with torch.enable_grad():
        _, components = _physics_objective(model, batch, config)
    return float(components["physics_total"]), components


def _audit(model: PhkV22RModel, dataset: Any, ledger: MaterializedPhysicsLedger, config: Any, device: torch.device) -> dict[str, Any]:
    medium = full_medium_audit(model, dataset, device=device)
    fixed, components = _fixed_physics(model, ledger, config, device)
    return {"medium": medium, "fixed_blind_physics": fixed, "fixed_blind_components": components}


def _make_optimizer(model: PhkV22RModel) -> torch.optim.Adam:
    return torch.optim.Adam(model.parameters(), lr=ETA0, betas=(0.9, 0.999), eps=1.0e-8, weight_decay=0.0, amsgrad=False)


def _train_one_step(model: PhkV22RModel, optimizer: torch.optim.Optimizer, *, batch: PhysicsBatch, config: Any) -> tuple[bool, dict[str, Any]]:
    optimizer.zero_grad(set_to_none=True)
    loss, components = _physics_objective(model, batch, config)
    if not bool(torch.isfinite(loss)):
        return False, {**components, "total_loss": float("inf"), "gradient_norm_before_clip": float("inf")}
    loss.backward()
    trainable = tuple(parameter for parameter in model.parameters() if parameter.requires_grad)
    per_head_gradient_norm = {}
    for field in ("potential", "temperature", "phase"):
        parameters = tuple(model.encoders[field].parameters()) + tuple(model.heads[field].parameters())
        squared = sum(
            float(torch.sum(parameter.grad.detach().square()).cpu())
            for parameter in parameters
            if parameter.requires_grad and parameter.grad is not None
        )
        per_head_gradient_norm[field] = math.sqrt(squared)
    grad_norm = float(torch.nn.utils.clip_grad_norm_(trainable, 10.0).detach().cpu())
    if not math.isfinite(grad_norm):
        return False, {**components, "total_loss": float(loss.detach().cpu()), "gradient_norm_before_clip": grad_norm}
    optimizer.step()
    return True, {
        **components,
        "total_loss": float(loss.detach().cpu()),
        "gradient_norm_before_clip": grad_norm,
        "per_head_gradient_norm_before_clip": per_head_gradient_norm,
        "clip_factor": min(1.0, 10.0 / grad_norm) if grad_norm > 0.0 else 1.0,
    }


def _block_sha256(hashes: Sequence[str]) -> str:
    digest = hashlib.sha256(b"PHK_V23_LF7_PHYSICS_BLOCK_V1\n")
    for value in hashes:
        digest.update(value.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest().upper()


def _dense_safety_pareto(arm: Mapping[str, Any], *, filtered: bool) -> bool:
    return bool(
        arm.get("numerical_valid")
        and arm.get("safety_gate", {}).get("passed")
        and float(arm.get("fixed_blind_ratio_to_DEV_R", math.inf)) <= 0.50
        and (not filtered or int(arm.get("accepted_blocks", 0)) >= 1)
    )


def _write_checkpoint(path: Path, *, model: PhkV22RModel, optimizer: torch.optim.Optimizer, config: Any, role: str, accepted: int, attempted: int, source_identity: str, parent_sha256: str, physics_program_sha256: str, physics_object_sha256: str, disposition: str) -> Path:
    payload = _checkpoint_payload(
        model=model,
        optimizer=optimizer,
        config=config,
        update=accepted,
        program_contract_sha256=_sha256_path(V22R_PROGRAM_CONTRACT_PATH),
        method_contract_sha256=_sha256_path(V22R_METHOD_CONTRACT_PATH),
        physical_program_sha256=physics_program_sha256,
        physical_object_sha256=physics_object_sha256,
    )
    payload["lf7"] = {
        "schema_id": "phk-v23-lf7-checkpoint-metadata-v1",
        "task_id": TASK_ID,
        "role": role,
        "accepted_optimizer_updates": int(accepted),
        "attempted_optimizer_updates": int(attempted),
        "source_identity": source_identity,
        "contracts": contract_identity(),
        "parent_checkpoint_sha256": parent_sha256,
        "physics_residual_used": True,
        "medium_gradient_used": False,
        "medium_acceptance_audit_used": role == P0_F,
        "runtime_sampling_used": False,
        "stress_read": False,
        "disposition": disposition,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        torch.save(payload, handle)
    return path


def _save_endpoint(directory: Path, *, model: PhkV22RModel, optimizer: torch.optim.Optimizer, config: Any, role: str, accepted: int, attempted: int, source_identity: str, parent_sha256: str, physics_program_sha256: str, physics_object_sha256: str, disposition: str, valid: bool) -> tuple[Path | None, Path | None]:
    if not valid:
        return None, None
    checkpoint = _write_checkpoint(
        directory / "checkpoint.pt", model=model, optimizer=optimizer, config=config,
        role=role, accepted=accepted, attempted=attempted, source_identity=source_identity,
        parent_sha256=parent_sha256, physics_program_sha256=physics_program_sha256,
        physics_object_sha256=physics_object_sha256, disposition=disposition,
    )
    prediction = write_prediction_carrier(checkpoint_path=checkpoint, output_path=directory / "prediction.npz", device_name=str(next(model.parameters()).device))
    return checkpoint, prediction


def _run_small(*, root: Path, dataset: Any, ledger: MaterializedPhysicsLedger, initial_checkpoint: Path, contracts: Mapping[str, Mapping[str, Any]], qualification: Mapping[str, Any], physics: Any, config: Any, device: torch.device, source_identity: str, physics_program_sha256: str, physics_object_sha256: str) -> dict[str, Any]:
    directory = root / ARM_DIRECTORIES[P0_S]
    directory.mkdir(parents=True, exist_ok=False)
    model, _ = load_dev_r_model(initial_checkpoint, physics=physics, config=config, device=device, contracts=contracts)
    baseline = qualification["dev_r_full_medium_audit"]
    optimizer = _make_optimizer(model)
    _set_phase_trainable(model, False)
    phase_initial = _phase_state_sha256(model)
    initial = _audit(model, dataset, ledger, config, device)
    if not math.isclose(initial["fixed_blind_physics"], EXPECTED_J0, rel_tol=1.0e-10, abs_tol=1.0e-12):
        raise ValueError("LF7 P0-S initial fixed-blind objective drift")
    telemetry_path = directory / "telemetry.jsonl"
    ledger_path = directory / "batch_ledger.jsonl"
    executed = 0
    numerical_valid = True
    last = initial
    step550: dict[str, Any] | None = None
    with telemetry_path.open("x", encoding="utf-8", newline="\n") as telemetry, ledger_path.open("x", encoding="utf-8", newline="\n") as batches:
        _append(telemetry, {"arm": P0_S, "step": 0, "accepted_updates": 0, "attempted_updates": 0, "stage": "PHASE_FROZEN", "learning_rate": ETA0, "phase_state_sha256": phase_initial, "optimizer_state_count": len(optimizer.state), "audit": initial})
        for step in range(1, P0_UPDATES + 1):
            if step == PHASE_FREEZE_STEPS + 1:
                state_entries = sum(parameter in optimizer.state for parameter in _phase_parameters(model))
                if _phase_state_sha256(model) != phase_initial or state_entries != 0:
                    raise RuntimeError("LF7 P0-S step550 phase identity drift")
                _set_phase_trainable(model, True)
            batch = ledger.physics_batch(step, device=device)
            ok, train = _train_one_step(model, optimizer, batch=batch, config=config)
            _append(batches, {"attempted_update": step, "accepted_update": step if ok else None, "physics_step": step, "batch_sha256": batch.batch_sha256, "interior_sha256": batch.interior_sha256, "boundary_sha256": batch.boundary_sha256, "initial_sha256": batch.initial_sha256})
            if not ok:
                numerical_valid = False
                break
            executed = step
            if step % BLOCK_SIZE == 0:
                last = _audit(model, dataset, ledger, config, device)
                _append(telemetry, {"arm": P0_S, "step": step, "accepted_updates": step, "attempted_updates": step, "stage": "PHASE_FROZEN" if step <= PHASE_FREEZE_STEPS else "JOINT", "learning_rate": ETA0, "phase_state_sha256": _phase_state_sha256(model), "optimizer_state_count": len(optimizer.state), "physics_block_sha256": _block_sha256(ledger.physics_hashes[step - BLOCK_SIZE:step]), "train": train, "audit": last})
            if step == PHASE_FREEZE_STEPS:
                state_entries = sum(parameter in optimizer.state for parameter in _phase_parameters(model))
                step550 = {"phase_before_sha256": phase_initial, "phase_after_sha256": _phase_state_sha256(model), "bitwise_preserved": _phase_state_sha256(model) == phase_initial, "phase_optimizer_state_entries": state_entries}
                if not step550["bitwise_preserved"] or state_entries != 0:
                    raise RuntimeError("LF7 P0-S step550 freeze identity drift")
                _write_checkpoint(directory / "checkpoint-step-550.pt", model=model, optimizer=optimizer, config=config, role=P0_S, accepted=550, attempted=550, source_identity=source_identity, parent_sha256=EXPECTED_DEV_R_SHA256, physics_program_sha256=physics_program_sha256, physics_object_sha256=physics_object_sha256, disposition="INTERIM_STEP_550")
    safety = competence_gate(last["medium"], baseline)
    strict = competence_gate(last["medium"], baseline, strict_timing=True)
    valid = bool(numerical_valid and executed == P0_UPDATES and last["medium"].get("all_values_finite") is True)
    checkpoint, prediction = _save_endpoint(directory, model=model, optimizer=optimizer, config=config, role=P0_S, accepted=executed, attempted=executed, source_identity=source_identity, parent_sha256=EXPECTED_DEV_R_SHA256, physics_program_sha256=physics_program_sha256, physics_object_sha256=physics_object_sha256, disposition="COMPLETE" if valid else "INVALID", valid=valid)
    gate = {"arm": P0_S, "numerical_valid": valid, "accepted_updates": executed, "attempted_updates": executed, "safety_gate": safety, "strict_gate": strict, "fixed_blind_ratio_to_DEV_R": last["fixed_blind_physics"] / EXPECTED_J0, "step550": step550, "final_audit": last}
    gate["dense_safety_pareto_pass"] = _dense_safety_pareto(gate, filtered=False)
    gate["strict_carrier_pass"] = bool(gate["dense_safety_pareto_pass"] and strict["passed"])
    _write_json_exclusive(directory / "gate.json", gate)
    _write_json_exclusive(directory / "exit.json", {"returncode": 0 if valid else 1, "accepted_updates": executed, "attempted_updates": executed, "numerical_valid": valid})
    result = {**gate, "checkpoint_sha256": _sha256_path(checkpoint) if checkpoint else None, "prediction_sha256": _sha256_path(prediction) if prediction else None, "disposition": "COMPLETE" if valid else "NUMERICAL_OR_IDENTITY_INVALID"}
    del optimizer, model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return result


def _available_scales(current: float) -> tuple[float, ...]:
    index = min(range(len(LR_SCALES)), key=lambda item: abs(LR_SCALES[item] - current))
    if not math.isclose(LR_SCALES[index], current, rel_tol=0.0, abs_tol=1.0e-16):
        raise ValueError("LF7 current learning rate left frozen dyadic ladder")
    return LR_SCALES[index:]


def _run_filter(*, root: Path, dataset: Any, ledger: MaterializedPhysicsLedger, initial_checkpoint: Path, contracts: Mapping[str, Mapping[str, Any]], qualification: Mapping[str, Any], physics: Any, config: Any, device: torch.device, source_identity: str, physics_program_sha256: str, physics_object_sha256: str) -> dict[str, Any]:
    directory = root / ARM_DIRECTORIES[P0_F]
    directory.mkdir(parents=True, exist_ok=False)
    model, _ = load_dev_r_model(initial_checkpoint, physics=physics, config=config, device=device, contracts=contracts)
    baseline = qualification["dev_r_full_medium_audit"]
    optimizer = _make_optimizer(model)
    _set_phase_trainable(model, False)
    phase_initial = _phase_state_sha256(model)
    initial = _audit(model, dataset, ledger, config, device)
    if not math.isclose(initial["fixed_blind_physics"], EXPECTED_J0, rel_tol=1.0e-10, abs_tol=1.0e-12):
        raise ValueError("LF7 P0-F initial fixed-blind objective drift")
    accepted = 0
    attempted = 0
    rejected_blocks = 0
    accepted_blocks = 0
    current_lr = ETA0
    previous_j = initial["fixed_blind_physics"]
    last = initial
    step550: dict[str, Any] | None = None
    disposition = "COMPLETE"
    numerical_valid = True
    telemetry_path = directory / "telemetry.jsonl"
    ledger_path = directory / "batch_ledger.jsonl"
    with telemetry_path.open("x", encoding="utf-8", newline="\n") as telemetry, ledger_path.open("x", encoding="utf-8", newline="\n") as batches:
        _append(telemetry, {"arm": P0_F, "accepted_updates": 0, "attempted_updates": 0, "stage": "PHASE_FROZEN", "learning_rate": current_lr, "phase_state_sha256": phase_initial, "optimizer_state_count": len(optimizer.state), "audit": initial})
        while accepted < P0_UPDATES:
            snapshot = take_snapshot(model, optimizer, accepted_updates=accepted, learning_rate=current_lr)
            block_number = accepted // BLOCK_SIZE + 1
            accepted_this_block = False
            for lr in _available_scales(current_lr):
                if attempted + BLOCK_SIZE > MAX_FILTER_ATTEMPTED_UPDATES:
                    disposition = "CFBR_STALLED_RUN_BOUND"
                    break
                restored_before = restore_snapshot(snapshot, model, optimizer)
                for group in optimizer.param_groups:
                    group["lr"] = lr
                next_step = accepted + 1
                _set_phase_trainable(model, next_step > PHASE_FREEZE_STEPS)
                if next_step == PHASE_FREEZE_STEPS + 1:
                    state_entries = sum(parameter in optimizer.state for parameter in _phase_parameters(model))
                    if _phase_state_sha256(model) != phase_initial or state_entries != 0:
                        raise RuntimeError("LF7 P0-F step550 phase identity drift")
                train: dict[str, Any] | None = None
                for local in range(BLOCK_SIZE):
                    physics_step = accepted + local + 1
                    batch = ledger.physics_batch(physics_step, device=device)
                    ok, train = _train_one_step(model, optimizer, batch=batch, config=config)
                    attempted += 1
                    _append(batches, {"block": block_number, "scale": lr, "attempted_update": attempted, "proposed_accepted_update": physics_step, "batch_sha256": batch.batch_sha256, "interior_sha256": batch.interior_sha256, "boundary_sha256": batch.boundary_sha256, "initial_sha256": batch.initial_sha256})
                    if not ok:
                        numerical_valid = False
                        disposition = "NUMERICAL_OR_IDENTITY_INVALID"
                        break
                if not numerical_valid:
                    break
                proposed = _audit(model, dataset, ledger, config, device)
                gate = competence_gate(proposed["medium"], baseline, physics_previous=previous_j, physics_new=proposed["fixed_blind_physics"])
                attempt_record = {"arm": P0_F, "block": block_number, "attempt_index": rejected_blocks + 1, "scale": lr, "lr_transition": [snapshot.learning_rate, lr], "accepted_before": accepted, "attempted_updates": attempted, "stage": "PHASE_FROZEN" if accepted < PHASE_FREEZE_STEPS else "JOINT", "state_digest_before": snapshot.digest, "rng_digest_before": snapshot.rng_digest, "restored_digest_before_attempt": restored_before, "restored_rng_digest_before_attempt": rng_digest(), "phase_state_sha256": _phase_state_sha256(model), "optimizer_state_count": len(optimizer.state), "physics_block_sha256": _block_sha256(ledger.physics_hashes[accepted:accepted + BLOCK_SIZE]), "cumulative_rejected_updates": rejected_blocks * BLOCK_SIZE, "train": train, "audit": proposed, "filter_gate": gate}
                if gate["passed"]:
                    accepted += BLOCK_SIZE
                    accepted_blocks += 1
                    current_lr = lr
                    previous_j = proposed["fixed_blind_physics"]
                    last = proposed
                    accepted_this_block = True
                    attempt_record["decision"] = "ACCEPT"
                    attempt_record["accepted_after"] = accepted
                    _append(telemetry, attempt_record)
                    if accepted == PHASE_FREEZE_STEPS:
                        state_entries = sum(parameter in optimizer.state for parameter in _phase_parameters(model))
                        step550 = {"phase_before_sha256": phase_initial, "phase_after_sha256": _phase_state_sha256(model), "bitwise_preserved": _phase_state_sha256(model) == phase_initial, "phase_optimizer_state_entries": state_entries}
                        if not step550["bitwise_preserved"] or state_entries != 0:
                            raise RuntimeError("LF7 P0-F step550 freeze identity drift")
                        _write_checkpoint(directory / "checkpoint-step-550.pt", model=model, optimizer=optimizer, config=config, role=P0_F, accepted=550, attempted=attempted, source_identity=source_identity, parent_sha256=EXPECTED_DEV_R_SHA256, physics_program_sha256=physics_program_sha256, physics_object_sha256=physics_object_sha256, disposition="INTERIM_STEP_550")
                    break
                rejected_blocks += 1
                restored_after = restore_snapshot(snapshot, model, optimizer)
                attempt_record["decision"] = "REJECT_ROLLBACK"
                attempt_record["restored_digest_after_reject"] = restored_after
                attempt_record["restored_rng_digest_after_reject"] = rng_digest()
                attempt_record["reject_reason"] = gate["failed_checks"]
                attempt_record["accepted_after"] = accepted
                attempt_record["cumulative_rejected_updates"] = rejected_blocks * BLOCK_SIZE
                _append(telemetry, attempt_record)
            if not numerical_valid or disposition == "CFBR_STALLED_RUN_BOUND":
                break
            if not accepted_this_block:
                disposition = "CFBR_STALLED"
                restore_snapshot(snapshot, model, optimizer)
                break
    safety = competence_gate(last["medium"], baseline)
    strict = competence_gate(last["medium"], baseline, strict_timing=True)
    valid = bool(numerical_valid and last["medium"].get("all_values_finite") is True)
    checkpoint, prediction = _save_endpoint(directory, model=model, optimizer=optimizer, config=config, role=P0_F, accepted=accepted, attempted=attempted, source_identity=source_identity, parent_sha256=EXPECTED_DEV_R_SHA256, physics_program_sha256=physics_program_sha256, physics_object_sha256=physics_object_sha256, disposition=disposition, valid=valid)
    gate_payload = {"arm": P0_F, "numerical_valid": valid, "accepted_updates": accepted, "attempted_updates": attempted, "accepted_blocks": accepted_blocks, "rejected_block_attempts": rejected_blocks, "final_learning_rate": current_lr, "disposition": disposition, "safety_gate": safety, "strict_gate": strict, "fixed_blind_ratio_to_DEV_R": last["fixed_blind_physics"] / EXPECTED_J0, "step550": step550, "final_audit": last}
    gate_payload["dense_safety_pareto_pass"] = _dense_safety_pareto(gate_payload, filtered=True)
    gate_payload["strict_carrier_pass"] = bool(gate_payload["dense_safety_pareto_pass"] and strict["passed"])
    _write_json_exclusive(directory / "gate.json", gate_payload)
    _write_json_exclusive(directory / "exit.json", {"returncode": 0 if valid else 1, "accepted_updates": accepted, "attempted_updates": attempted, "numerical_valid": valid, "disposition": disposition})
    result = {**gate_payload, "checkpoint_sha256": _sha256_path(checkpoint) if checkpoint else None, "prediction_sha256": _sha256_path(prediction) if prediction else None}
    del optimizer, model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return result


def mechanism_outcome(arms: Mapping[str, Mapping[str, Any]]) -> str:
    small = arms[P0_S]
    filtered = arms[P0_F]
    if not small.get("numerical_valid") or not filtered.get("numerical_valid"):
        return "MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID"
    if _dense_safety_pareto(small, filtered=False):
        return "SMALL_LR_SUFFICIENT_FILTER_NOT_LOAD_BEARING"
    if _dense_safety_pareto(filtered, filtered=True):
        return "COMPETENCE_FILTER_LOAD_BEARING"
    if str(filtered.get("disposition", "")).startswith("CFBR_STALLED"):
        return "FILTER_STALLED_NO_FEASIBLE_BLOCK_PATH"
    return "NO_PRESERVATION_COMPATIBLE_STRONG_FORM_PATH_FOUND"


def _poststep_invalid_arm(root: Path, role: str, error: BaseException) -> dict[str, Any]:
    """Preserve an affected post-step arm while allowing the fresh arm to run."""

    directory = root / ARM_DIRECTORIES[role]
    ledger_path = directory / "batch_ledger.jsonl"
    if not ledger_path.is_file():
        raise error
    batch_rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not batch_rows:
        raise error
    attempted = len(batch_rows)
    if role == P0_S:
        accepted = sum(row.get("accepted_update") is not None for row in batch_rows)
        accepted_blocks = accepted // BLOCK_SIZE
    else:
        telemetry_path = directory / "telemetry.jsonl"
        telemetry_rows = [json.loads(line) for line in telemetry_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        accepted = max((int(row.get("accepted_after", 0)) for row in telemetry_rows), default=0)
        accepted_blocks = accepted // BLOCK_SIZE
    failed_gate = {"passed": False, "checks": {}, "failed_checks": ["poststep_identity_or_runtime_failure"]}
    result = {
        "arm": role,
        "numerical_valid": False,
        "accepted_updates": accepted,
        "attempted_updates": attempted,
        "accepted_blocks": accepted_blocks,
        "disposition": "NUMERICAL_OR_IDENTITY_INVALID",
        "error_type": type(error).__name__,
        "error_message": str(error),
        "safety_gate": failed_gate,
        "strict_gate": failed_gate,
        "dense_safety_pareto_pass": False,
        "strict_carrier_pass": False,
        "fixed_blind_ratio_to_DEV_R": None,
        "checkpoint_sha256": None,
        "prediction_sha256": None,
    }
    gate_path = directory / "gate.json"
    exit_path = directory / "exit.json"
    if not gate_path.exists():
        _write_json_exclusive(gate_path, result)
    if not exit_path.exists():
        _write_json_exclusive(exit_path, {"returncode": 1, **result})
    return result


def execute_gpu_campaign(*, output_root: Path, medium_carrier: Path, initial_checkpoint: Path, materialized_ledger: Path, cpu_qualification_path: Path, device_name: str, source_identity: str) -> dict[str, Any]:
    contracts = load_contracts()
    qualification = read_cpu_qualification(cpu_qualification_path)
    if not device_name.startswith("cuda") or not torch.cuda.is_available():
        raise RuntimeError("LF7 requires CUDA")
    device = torch.device(device_name)
    gpu_name = torch.cuda.get_device_name(device)
    if gpu_name != "Tesla V100-PCIE-32GB":
        raise RuntimeError("LF7 requires Tesla V100-PCIE-32GB")
    root = Path(output_root).resolve()
    if root.exists():
        if not root.is_dir() or any(root.iterdir()):
            raise FileExistsError(f"LF7 output root must be an empty directory: {root}")
    else:
        root.mkdir(parents=True, exist_ok=False)
    config = build_training_config(device_name)
    physics, physics_program_sha256, physics_object_sha256 = load_case_physics(config.case_control)
    dataset = load_medium_dataset(Path(medium_carrier), physics=physics, contracts=contracts)
    if dataset.partition_sha256 != EXPECTED_PARTITION_SHA256 or qualification.get("partition_sha256") != EXPECTED_PARTITION_SHA256:
        raise ValueError("LF7 qualified partition drift")
    ledger = MaterializedPhysicsLedger(Path(materialized_ledger), contracts=contracts, qualification=qualification)
    random.seed(17); np.random.seed(17); torch.manual_seed(17); torch.cuda.manual_seed_all(17)
    started_at = datetime.now(timezone.utc).isoformat()
    try:
        small = _run_small(root=root, dataset=dataset, ledger=ledger, initial_checkpoint=Path(initial_checkpoint), contracts=contracts, qualification=qualification, physics=physics, config=config, device=device, source_identity=source_identity, physics_program_sha256=physics_program_sha256, physics_object_sha256=physics_object_sha256)
    except Exception as error:
        small = _poststep_invalid_arm(root, P0_S, error)
    random.seed(17); np.random.seed(17); torch.manual_seed(17); torch.cuda.manual_seed_all(17)
    try:
        filtered = _run_filter(root=root, dataset=dataset, ledger=ledger, initial_checkpoint=Path(initial_checkpoint), contracts=contracts, qualification=qualification, physics=physics, config=config, device=device, source_identity=source_identity, physics_program_sha256=physics_program_sha256, physics_object_sha256=physics_object_sha256)
    except Exception as error:
        filtered = _poststep_invalid_arm(root, P0_F, error)
    arms = {P0_S: small, P0_F: filtered}
    mechanism = mechanism_outcome(arms)
    total_attempted = int(small["attempted_updates"]) + int(filtered["attempted_updates"])
    if total_attempted > 3600:
        raise RuntimeError("LF7 campaign attempted-update bound exceeded")
    artifacts: dict[str, Any] = {}
    for role in ARM_ORDER:
        directory = root / ARM_DIRECTORIES[role]
        for name in ("telemetry.jsonl", "batch_ledger.jsonl", "checkpoint-step-550.pt", "checkpoint.pt", "prediction.npz", "gate.json", "exit.json"):
            path = directory / name
            if path.is_file():
                artifacts[f"{role}:{name}"] = _artifact_record(path, root)
    summary = {
        "schema_id": "phk-v23-lf7-reference-blind-run-summary-v1",
        "task_id": TASK_ID,
        "title": TITLE,
        "status": "LF7_REFERENCE_BLIND_GPU_CAMPAIGN_COMPLETE" if mechanism != "MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID" else "LF7_MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID",
        "started_at_utc": started_at,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_identity": source_identity,
        "gpu": gpu_name,
        "dtype": "FLOAT64",
        "seed": 17,
        "arms": arms,
        "mechanism_outcome": mechanism,
        "total_attempted_optimizer_updates": total_attempted,
        "ledger": {"path": str(Path(materialized_ledger)), "sha256": _sha256_path(Path(materialized_ledger)), "semantic_sha256": EXPECTED_LEDGER_SEMANTIC_SHA256, "physics_stream_sha256": ledger.physics_sha256, "fixed_blind_pool_sha256": EXPECTED_FIXED_POOL_SHA256},
        "artifacts": artifacts,
        "medium_gradient_used": False,
        "medium_acceptance_audit_used_by_P0_F": True,
        "prediction_reference_free": True,
        "runtime_sampling_used": False,
        "fine_extra_lf_only_evaluator_stress_read": False,
    }
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
    summary = execute_gpu_campaign(
        output_root=args.output_root,
        medium_carrier=args.medium_carrier,
        initial_checkpoint=args.initial_checkpoint,
        materialized_ledger=args.materialized_ledger,
        cpu_qualification_path=args.cpu_qualification,
        device_name=args.device,
        source_identity=args.source_identity,
    )
    print(json.dumps({"status": summary["status"], "mechanism_outcome": summary["mechanism_outcome"], "total_attempted_optimizer_updates": summary["total_attempted_optimizer_updates"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ARM_DIRECTORIES", "ARM_ORDER", "BLOCK_COUNT", "BLOCK_SIZE", "ETA0",
    "LR_SCALES", "MaterializedPhysicsLedger", "P0_F", "P0_S", "TASK_ID",
    "TrainingSnapshot", "competence_gate", "contract_identity",
    "execute_gpu_campaign", "load_contracts", "load_dev_r_model",
    "mechanism_outcome", "read_cpu_qualification", "restore_snapshot",
    "state_digest", "take_snapshot",
]
