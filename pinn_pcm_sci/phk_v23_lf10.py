"""LF10 event-competence feasible directions and headline replications.

The deep seam in this module is :func:`propose_and_resolve_step`: it owns the
otherwise fragile transaction that advances exact ``torch.optim.Adam``
moments, extracts the proposed parameter delta without leaving it applied,
computes read-only competence gradients, and returns either the unmodified
CTRL delta or the nearest per-head feasible PROJ delta.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
from statistics import median
from typing import Any, Callable, Iterable, Mapping, Sequence

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
from .phk_v23_lf2 import CATEGORY_NAMES, CATEGORY_QUOTAS, MeasureBatch, load_medium_dataset, weighted_measure_terms
from .phk_v23_lf3 import _phase_state_sha256, build_training_config, full_medium_audit
from .phk_v23_lf4 import (
    ARM_G as DEV_G,
    ARM_M as DEV_M,
    BAND_POOL_NAMES,
    ExtraBatch,
    _field_state_sha256,
    _quality_preserved,
    load_lf3_t0_model,
    measure_decoupled_terms,
    normalized_logit_mse,
)
from . import phk_v23_lf7 as lf7
from . import phk_v23_lf8 as lf8


TASK_ID = "PHK_V23_LF10_EVENT_COMPETENCE_FEASIBLE_DIRECTION_AND_HEADLINE_EVIDENCE_REPLICATION_EXECUTE"
TITLE = "PHK-V2.3 LF10 event-competence feasible-direction refinement and headline-evidence replication"
CTRL = "CTRL"
PROJ = "PROJ"
DIRECTION_ARM_ORDER = (CTRL, PROJ)
STREAM_SEEDS = (23, 29)
BLOCK_SIZE = 25
SCREEN_ACCEPTED_UPDATES = 200
SCREEN_ATTEMPTED_CAP = 1000
FULL_ACCEPTED_UPDATES = 1200
FULL_ATTEMPTED_CAP = 3600
PHASE_FREEZE_STEPS = 550
ETA0 = 1.25e-4
LR_LADDER = (ETA0, ETA0 / 2.0, ETA0 / 4.0, ETA0 / 8.0, ETA0 / 16.0)
DEV_R_BASELINE = {
    "potential": 0.0000714767714198432,
    "temperature": 0.0007111887418509096,
    "phase": 0.0011832624059166495,
}
DEV_R_TOPOLOGY = 0.0046144880306589605
DEV_R_J0 = 4.9278721846990505
PROJECTION_BOUNDS = {"CV": 1.20, "CT": 1.05, "Cphase": 1.05, "Ctopology_smooth_surrogate": 1.05}
AUDIT_BASELINE_COLUMNS = ("CV", "CT", "Cphase", "Ctopology_smooth_surrogate")

PROGRAM_CONTRACT_PATH = ROOT / "configs/phk_v23/program_contract_lf10_feasible_direction_replication.json"
METHOD_CONTRACT_PATH = ROOT / "configs/phk_v23/method_contract_lf10_feasible_direction_replication.json"
DATA_CONTRACT_PATH = ROOT / "configs/phk_v23/data_contract_lf10_feasible_direction_replication.json"
DECISION_CONTRACT_PATH = ROOT / "configs/phk_v23/decision_contract_lf10_feasible_direction_replication.json"
CONTRACT_PATHS = {"program": PROGRAM_CONTRACT_PATH, "method": METHOD_CONTRACT_PATH, "data": DATA_CONTRACT_PATH, "decision": DECISION_CONTRACT_PATH}
EXPECTED_SCHEMAS = {name: f"phk-v23-lf10-{name}-contract-v1" for name in CONTRACT_PATHS}


def load_contracts() -> dict[str, dict[str, Any]]:
    contracts = {name: _read_json(path) for name, path in CONTRACT_PATHS.items()}
    for name, schema in EXPECTED_SCHEMAS.items():
        if contracts[name].get("schema_id") != schema:
            raise ValueError(f"unsupported LF10 {name} contract")
    relative = {name: path.relative_to(ROOT).as_posix() for name, path in CONTRACT_PATHS.items()}
    if contracts["program"].get("phase_id") != TASK_ID:
        raise ValueError("LF10 task identity drift")
    if any(contracts[name].get("program_contract") != relative["program"] for name in ("method", "data", "decision")):
        raise ValueError("LF10 program binding drift")
    if contracts["decision"].get("method_contract") != relative["method"] or contracts["decision"].get("data_contract") != relative["data"]:
        raise ValueError("LF10 decision binding drift")
    method = contracts["method"]
    if tuple(float(value) for value in method["direction_identity"]["optimizer"].get("betas", ())) != (0.9, 0.999):
        raise ValueError("LF10 Adam identity drift")
    if tuple(float(value) for value in method["direction_identity"].get("learning_rate_ladder", ())) != LR_LADDER:
        raise ValueError("LF10 learning-rate ladder drift")
    if int(method["direction_identity"].get("block_size", -1)) != BLOCK_SIZE:
        raise ValueError("LF10 block identity drift")
    if contracts["decision"].get("stress_status") != "TWO_STRESS_REFERENCES_SEALED_UNREAD":
        raise PermissionError("LF10 stress boundary drift")
    return contracts


def contract_identity() -> dict[str, dict[str, str]]:
    return {name: {"path": path.relative_to(ROOT).as_posix(), "sha256": _sha256_path(path)} for name, path in CONTRACT_PATHS.items()}


def read_cpu_qualification(path: Path) -> dict[str, Any]:
    payload = _read_json(Path(path).resolve())
    if payload.get("schema_id") != "phk-v23-lf10-cpu-qualification-v1" or payload.get("task_id") != TASK_ID:
        raise ValueError("LF10 CPU qualification identity drift")
    if payload.get("scientific_optimizer_updates") != 0:
        raise PermissionError("LF10 CPU qualification performed scientific updates")
    outcome = payload.get("gate_outcome", payload.get("status"))
    if outcome not in {"LF10_CPU_QUALIFICATION_PASS", "LF10_CPU_ANALYSIS_COMPLETE"}:
        raise PermissionError("LF10 CPU qualification did not pass")
    checks = payload.get("checks", {})
    if checks and not all(bool(value) for value in checks.values()):
        raise PermissionError("LF10 CPU qualification contains a failed check")
    if payload.get("contracts") != contract_identity():
        raise ValueError("LF10 CPU qualification contract identity drift")
    return payload


def array_sha256(name: str, value: np.ndarray) -> str:
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256(b"PHK_V23_LF10_ARRAY_V1\n")
    digest.update(name.encode("ascii")); digest.update(b"\n")
    digest.update(array.dtype.str.encode("ascii")); digest.update(b"\n")
    digest.update(json.dumps(list(array.shape), separators=(",", ":")).encode("ascii")); digest.update(b"\n")
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest().upper()


def semantic_ledger_sha256(array_hashes: Mapping[str, str]) -> str:
    digest = hashlib.sha256(b"PHK_V23_LF10_MATERIALIZED_LEDGER_V1\n")
    for name in sorted(array_hashes):
        digest.update(f"{name}={array_hashes[name]}\n".encode("ascii"))
    return digest.hexdigest().upper()


def _decode_hash(value: Any) -> str:
    if isinstance(value, (bytes, np.bytes_)):
        return bytes(value).decode("ascii")
    return str(value)


def ledger_array_names() -> tuple[str, ...]:
    names = ["audit_coordinates", "audit_targets", "audit_batch_sha256", "audit_baselines"]
    for seed in STREAM_SEEDS:
        for role in ("base", "global", "band"):
            names.extend((f"interface_{seed}_{role}_coordinates", f"interface_{seed}_{role}_targets", f"interface_{seed}_{role}_sha256"))
        prefix = f"physics_{seed}_"
        names.extend(prefix + name for name in (
            "interior", "left", "right", "bottom", "top", "initial",
            "active_windows", "refreshed", "interior_sha256", "boundary_sha256",
            "initial_sha256", "batch_sha256",
        ))
    return tuple(names)


class MaterializedLF10Ledger:
    """Read-only, content-addressed batches. Retries address accepted-step index."""

    def __init__(self, path: Path, manifest_path: Path, *, qualification: Mapping[str, Any]) -> None:
        self.path = Path(path).resolve()
        self.manifest_path = Path(manifest_path).resolve()
        if not self.path.is_file() or not self.manifest_path.is_file():
            raise FileNotFoundError("LF10 materialized ledger or manifest missing")
        qledger = qualification.get("ledger", qualification.get("lf10_ledger", {}))
        expected_file = qledger.get("sha256", qledger.get("file_sha256"))
        expected_manifest = qledger.get("manifest_sha256")
        if expected_file and _sha256_path(self.path) != expected_file:
            raise ValueError("LF10 ledger file binding drift")
        if expected_manifest and _sha256_path(self.manifest_path) != expected_manifest:
            raise ValueError("LF10 ledger manifest binding drift")
        manifest = _read_json(self.manifest_path)
        if manifest.get("schema_id") != "phk-v23-lf10-materialized-ledger-manifest-v1" or manifest.get("task_id") != TASK_ID:
            raise ValueError("LF10 ledger manifest identity drift")
        with np.load(self.path, allow_pickle=False) as archive:
            expected_names = set(ledger_array_names())
            if set(archive.files) != expected_names:
                missing = sorted(expected_names - set(archive.files))
                extra = sorted(set(archive.files) - expected_names)
                raise ValueError(f"LF10 ledger array key drift missing={missing} extra={extra}")
            self.arrays = {name: np.asarray(archive[name]) for name in archive.files}
        hashes = {name: array_sha256(name, value) for name, value in self.arrays.items()}
        for name, value in self.arrays.items():
            record = manifest.get("arrays", {}).get(name, {})
            if record.get("sha256") != hashes[name] or record.get("shape") != list(value.shape) or record.get("dtype") != value.dtype.str:
                raise ValueError(f"LF10 ledger array drift: {name}")
        semantic = semantic_ledger_sha256(hashes)
        if manifest.get("semantic_sha256") != semantic or (qledger.get("semantic_sha256") and qledger.get("semantic_sha256") != semantic):
            raise ValueError("LF10 ledger semantic identity drift")
        self.semantic_sha256 = semantic
        self.streams = copy.deepcopy(manifest.get("streams", qledger.get("streams", {})))
        baselines = self.arrays["audit_baselines"]
        if (
            baselines.dtype != np.dtype(np.float64)
            or baselines.shape != (self.arrays["audit_coordinates"].shape[0], len(AUDIT_BASELINE_COLUMNS))
            or not np.all(np.isfinite(baselines))
            or np.any(baselines <= 0.0)
        ):
            raise ValueError("LF10 same-batch DEV-R audit baseline identity drift")

    @staticmethod
    def _index(step: int, maximum: int, label: str) -> int:
        exact = int(step)
        if exact < 1 or exact > maximum:
            raise ValueError(f"LF10 {label} step out of range")
        return exact - 1

    def audit_batch(self, accepted_step: int, dataset: Any) -> MeasureBatch:
        index = self._index(accepted_step, FULL_ACCEPTED_UPDATES, "audit")
        return MeasureBatch(
            torch.as_tensor(self.arrays["audit_coordinates"][index], dtype=torch.float64),
            torch.as_tensor(self.arrays["audit_targets"][index], dtype=torch.float64),
            dict(zip(CATEGORY_NAMES, CATEGORY_QUOTAS, strict=True)),
            dict(dataset.category_masses),
            _decode_hash(self.arrays["audit_batch_sha256"][index]),
        )

    def audit_baselines(self, accepted_step: int) -> dict[str, float]:
        index = self._index(accepted_step, self.arrays["audit_baselines"].shape[0], "audit baseline")
        values = self.arrays["audit_baselines"][index]
        return {name: float(value) for name, value in zip(AUDIT_BASELINE_COLUMNS, values, strict=True)}

    def interface_base_batch(self, seed: int, step: int, dataset: Any) -> MeasureBatch:
        index = self._index(step, 400, "interface")
        prefix = f"interface_{int(seed)}_base"
        return MeasureBatch(
            torch.as_tensor(self.arrays[f"{prefix}_coordinates"][index], dtype=torch.float64),
            torch.as_tensor(self.arrays[f"{prefix}_targets"][index], dtype=torch.float64),
            dict(zip(CATEGORY_NAMES, CATEGORY_QUOTAS, strict=True)),
            dict(dataset.category_masses),
            _decode_hash(self.arrays[f"{prefix}_sha256"][index]),
        )

    def interface_extra_batch(self, seed: int, role: str, step: int) -> ExtraBatch:
        if role not in {"global", "band"}:
            raise KeyError(role)
        index = self._index(step, 400, "interface")
        prefix = f"interface_{int(seed)}_{role}"
        counts = {"GLOBAL_EXTRA": 256} if role == "global" else {name: 64 for name in BAND_POOL_NAMES}
        return ExtraBatch(
            torch.as_tensor(self.arrays[f"{prefix}_coordinates"][index], dtype=torch.float64),
            torch.as_tensor(self.arrays[f"{prefix}_targets"][index], dtype=torch.float64),
            counts,
            _decode_hash(self.arrays[f"{prefix}_sha256"][index]),
        )

    def physics_batch(self, seed: int, step: int, *, device: torch.device) -> PhysicsBatch:
        index = self._index(step, FULL_ACCEPTED_UPDATES, "physics replication")
        prefix = f"physics_{int(seed)}_"
        tensor = lambda name: torch.as_tensor(self.arrays[prefix + name][index], dtype=torch.float64, device=device)
        return PhysicsBatch(
            interior=tensor("interior"),
            boundary={name: tensor(name) for name in ("left", "right", "bottom", "top")},
            initial=tensor("initial"),
            active_windows=int(self.arrays[prefix + "active_windows"][index]),
            refreshed=bool(self.arrays[prefix + "refreshed"][index]),
            interior_sha256=_decode_hash(self.arrays[prefix + "interior_sha256"][index]),
            boundary_sha256=_decode_hash(self.arrays[prefix + "boundary_sha256"][index]),
            initial_sha256=_decode_hash(self.arrays[prefix + "initial_sha256"][index]),
            batch_sha256=_decode_hash(self.arrays[prefix + "batch_sha256"][index]),
        )


def field_parameter_groups(model: torch.nn.Module, *, trainable_only: bool = True) -> dict[str, tuple[torch.nn.Parameter, ...]]:
    result: dict[str, tuple[torch.nn.Parameter, ...]] = {}
    for field in ("potential", "temperature", "phase"):
        parameters = tuple(model.encoders[field].parameters()) + tuple(model.heads[field].parameters())
        selected = tuple(parameter for parameter in parameters if parameter.requires_grad) if trainable_only else parameters
        if selected or not trainable_only:
            result[field] = selected
    return result


def configure_phase_for_next_accepted_update(model: torch.nn.Module, *, accepted_updates: int) -> bool:
    trainable = int(accepted_updates) >= PHASE_FREEZE_STEPS
    model.encoders["phase"].requires_grad_(trainable)
    model.heads["phase"].requires_grad_(trainable)
    return trainable


@dataclass(frozen=True)
class AdamProposal:
    updates: Mapping[str, tuple[torch.Tensor, ...]]
    total_loss: float
    gradient_norm_before_clip: float
    clip_factor: float
    per_head_gradient_norm_before_clip: Mapping[str, float]


def extract_adam_proposed_update(
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    loss: torch.Tensor,
    *,
    parameter_groups: Mapping[str, Sequence[torch.nn.Parameter]] | None = None,
    max_grad_norm: float = 10.0,
) -> AdamProposal:
    """Advance exact Adam moments, capture its delta, and restore parameters only."""

    if not bool(torch.isfinite(loss)):
        raise FloatingPointError("LF10 physics objective is non-finite")
    groups = {}
    for name, parameters in (parameter_groups or {"all": tuple(model.parameters())}).items():
        selected = tuple(parameter for parameter in parameters if parameter.requires_grad)
        if selected:
            groups[name] = selected
    trainable: tuple[torch.nn.Parameter, ...] = tuple(dict.fromkeys(parameter for parameters in groups.values() for parameter in parameters))
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    per_head = {
        name: math.sqrt(sum(float(torch.sum(parameter.grad.detach().square()).cpu()) for parameter in parameters if parameter.grad is not None))
        for name, parameters in groups.items()
    }
    grad_norm = float(torch.nn.utils.clip_grad_norm_(trainable, float(max_grad_norm)).detach().cpu()) if trainable else 0.0
    if not math.isfinite(grad_norm):
        optimizer.zero_grad(set_to_none=True)
        raise FloatingPointError("LF10 physics gradient is non-finite")
    before = {id(parameter): parameter.detach().clone() for parameter in trainable}
    optimizer.step()
    updates = {
        name: tuple(parameter.detach().clone() - before[id(parameter)] for parameter in parameters)
        for name, parameters in groups.items()
    }
    with torch.no_grad():
        for parameter in trainable:
            parameter.copy_(before[id(parameter)])
    optimizer.zero_grad(set_to_none=True)
    return AdamProposal(
        updates=updates,
        total_loss=float(loss.detach().cpu()),
        gradient_norm_before_clip=grad_norm,
        clip_factor=min(1.0, float(max_grad_norm) / grad_norm) if grad_norm > 0.0 else 1.0,
        per_head_gradient_norm_before_clip=per_head,
    )


@dataclass(frozen=True)
class LinearConstraint:
    name: str
    row: torch.Tensor
    rhs: float
    current: float
    bound: float
    remaining_steps: int


@dataclass(frozen=True)
class ProjectionResult:
    update: torch.Tensor
    feasible: bool
    active_set: tuple[int, ...]
    distance: float
    norm_capped: bool
    reason: str
    constraint_lhs_minus_rhs: Mapping[str, float]


def _constraint_violations(update: torch.Tensor, constraints: Sequence[LinearConstraint]) -> dict[str, float]:
    return {constraint.name: float(torch.dot(constraint.row, update).detach().cpu()) - float(constraint.rhs) for constraint in constraints}


def project_update_nearest(
    proposed: torch.Tensor,
    constraints: Sequence[LinearConstraint],
    *,
    norm_cap: bool = True,
    tolerance: float = 1e-10,
) -> ProjectionResult:
    """Euclidean projection onto at most two affine halfspaces by active sets."""

    u0 = proposed.detach().reshape(-1).to(dtype=torch.float64)
    rows = tuple(constraints)
    if len(rows) > 2:
        raise ValueError("LF10 projection supports at most two constraints per head")
    if not bool(torch.all(torch.isfinite(u0))):
        return ProjectionResult(u0, False, (), math.inf, False, "NONFINITE_PROPOSAL", {})
    for constraint in rows:
        if constraint.row.numel() != u0.numel() or not bool(torch.all(torch.isfinite(constraint.row))) or not math.isfinite(float(constraint.rhs)):
            return ProjectionResult(u0, False, (), math.inf, False, "INVALID_CONSTRAINT", {})
    candidates: list[tuple[float, tuple[int, ...], torch.Tensor]] = []
    for size in range(len(rows) + 1):
        for active in itertools.combinations(range(len(rows)), size):
            if not active:
                candidate = u0.clone()
                dual = torch.empty(0, dtype=torch.float64)
            else:
                matrix = torch.stack([rows[index].row.to(dtype=torch.float64, device=u0.device) for index in active])
                rhs = torch.tensor([rows[index].rhs for index in active], dtype=torch.float64, device=u0.device)
                gram = matrix @ matrix.T
                target = matrix @ u0 - rhs
                try:
                    dual = torch.linalg.lstsq(gram, target.unsqueeze(1)).solution.reshape(-1)
                except RuntimeError:
                    continue
                if not torch.allclose(gram @ dual, target, atol=tolerance, rtol=0.0):
                    continue
                candidate = u0 - matrix.T @ dual
            if dual.numel() and bool(torch.any(dual < -tolerance)):
                continue
            violations = _constraint_violations(candidate, rows)
            if any(value > tolerance for value in violations.values()):
                continue
            distance = float(torch.sum((candidate - u0).square()).detach().cpu())
            candidates.append((distance, tuple(active), candidate))
    if not candidates:
        violations = _constraint_violations(u0, rows)
        return ProjectionResult(u0, False, (), math.inf, False, "HALFSPACE_INTERSECTION_UNSOLVED", violations)
    distance_sq, active, result = min(candidates, key=lambda item: (item[0], len(item[1]), item[1]))
    capped = False
    proposed_norm = float(torch.linalg.vector_norm(u0).detach().cpu())
    result_norm = float(torch.linalg.vector_norm(result).detach().cpu())
    if norm_cap and result_norm > proposed_norm + tolerance:
        scaled = result * (proposed_norm / result_norm) if result_norm > 0.0 else result
        violations = _constraint_violations(scaled, rows)
        if any(value > tolerance for value in violations.values()):
            return ProjectionResult(result, False, active, math.sqrt(distance_sq), False, "NORM_CAP_BREAKS_FEASIBILITY", violations)
        result = scaled
        capped = True
    violations = _constraint_violations(result, rows)
    return ProjectionResult(result, True, active, math.sqrt(distance_sq), capped, "FEASIBLE", violations)


def _flatten(values: Sequence[torch.Tensor]) -> torch.Tensor:
    if not values:
        return torch.empty(0, dtype=torch.float64)
    return torch.cat([value.detach().reshape(-1).to(dtype=torch.float64) for value in values])


def _unflatten(value: torch.Tensor, references: Sequence[torch.Tensor]) -> tuple[torch.Tensor, ...]:
    result: list[torch.Tensor] = []
    offset = 0
    for reference in references:
        count = reference.numel()
        result.append(value[offset:offset + count].reshape(reference.shape).to(dtype=reference.dtype, device=reference.device))
        offset += count
    if offset != value.numel():
        raise ValueError("LF10 projected update shape drift")
    return tuple(result)


def linearize_head_constraints(
    objectives: Mapping[str, Mapping[str, torch.Tensor]],
    baselines: Mapping[str, float],
    bounds: Mapping[str, float],
    parameter_groups: Mapping[str, Sequence[torch.nn.Parameter]],
    *,
    remaining_steps: int,
) -> tuple[dict[str, tuple[LinearConstraint, ...]], dict[str, float]]:
    """Create read-only first-order ratio constraints without touching ``.grad``."""

    if int(remaining_steps) <= 0:
        raise ValueError("LF10 remaining block steps must be positive")
    result: dict[str, tuple[LinearConstraint, ...]] = {}
    values: dict[str, float] = {}
    active_parameters = {
        head: tuple(parameter for parameter in parameter_groups.get(head, ()) if parameter.requires_grad)
        for head in objectives
    }
    total_active_objectives = sum(
        len(objectives[head]) for head, parameters in active_parameters.items() if parameters
    )
    processed_active = 0
    for head, named in objectives.items():
        parameters = active_parameters[head]
        constraints: list[LinearConstraint] = []
        for name, objective in named.items():
            baseline = float(baselines[name])
            bound = float(bounds[name])
            if not math.isfinite(baseline) or baseline <= 0.0:
                raise ValueError(f"LF10 invalid audit baseline: {name}")
            ratio = objective / baseline
            current = float(ratio.detach().cpu())
            values[name] = current
            if not parameters:
                continue
            processed_active += 1
            gradients = torch.autograd.grad(
                ratio, parameters, retain_graph=processed_active < total_active_objectives,
                create_graph=False, allow_unused=True,
            )
            row = _flatten(tuple(torch.zeros_like(parameter) if gradient is None else gradient for parameter, gradient in zip(parameters, gradients, strict=True)))
            constraints.append(LinearConstraint(name, row, (bound - current) / int(remaining_steps), current, bound, int(remaining_steps)))
        if parameters:
            result[head] = tuple(constraints)
    return result, values


@dataclass(frozen=True)
class HeadUpdateDecision:
    updates: Mapping[str, tuple[torch.Tensor, ...]]
    feasible: bool
    projections: Mapping[str, ProjectionResult]
    reason: str


def resolve_head_updates(
    arm: str,
    proposed: Mapping[str, Sequence[torch.Tensor]],
    constraints: Mapping[str, Sequence[LinearConstraint]],
) -> HeadUpdateDecision:
    if arm not in DIRECTION_ARM_ORDER:
        raise KeyError(arm)
    resolved: dict[str, tuple[torch.Tensor, ...]] = {}
    projections: dict[str, ProjectionResult] = {}
    for head, tensors in proposed.items():
        references = tuple(tensors)
        if not references:
            continue
        flat = _flatten(references)
        if arm == CTRL:
            projection = ProjectionResult(flat, True, (), 0.0, False, "CTRL_UNPROJECTED", _constraint_violations(flat, constraints.get(head, ())))
        else:
            projection = project_update_nearest(flat, constraints.get(head, ()))
        projections[head] = projection
        if not projection.feasible:
            return HeadUpdateDecision({}, False, projections, f"PROJECTION_INFEASIBLE:{head}:{projection.reason}")
        resolved[head] = _unflatten(projection.update, references)
    return HeadUpdateDecision(resolved, True, projections, "FEASIBLE")


def apply_head_updates(parameter_groups: Mapping[str, Sequence[torch.nn.Parameter]], updates: Mapping[str, Sequence[torch.Tensor]]) -> None:
    with torch.no_grad():
        for head, values in updates.items():
            parameters = tuple(parameter_groups.get(head, ()))
            if len(parameters) != len(values):
                raise ValueError(f"LF10 parameter/update count drift for {head}")
            for parameter, update in zip(parameters, values, strict=True):
                parameter.add_(update.to(dtype=parameter.dtype, device=parameter.device))


def audit_preservation_objectives(model: torch.nn.Module, batch: MeasureBatch, *, physics: Any, device: torch.device) -> dict[str, dict[str, torch.Tensor]]:
    terms = weighted_measure_terms(model, batch, physics=physics, device=device)
    components = terms["field_components"]
    return {
        "potential": {"CV": components[0]},
        "temperature": {"CT": components[1]},
        "phase": {"Cphase": components[2], "Ctopology_smooth_surrogate": terms["topology"]},
    }


def direction_geometry(proposal: Mapping[str, Sequence[torch.Tensor]], constraints: Mapping[str, Sequence[LinearConstraint]], projected: Mapping[str, ProjectionResult]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for head, values in proposal.items():
        if not values:
            continue
        u0 = _flatten(values)
        record: dict[str, Any] = {
            "proposal_norm": float(torch.linalg.vector_norm(u0).detach().cpu()),
            "proposal_changes": {constraint.name: float(torch.dot(constraint.row, u0).detach().cpu()) for constraint in constraints.get(head, ())},
        }
        if head in projected:
            record.update({
                "projected_norm": float(torch.linalg.vector_norm(projected[head].update).detach().cpu()),
                "projected_changes": {constraint.name: float(torch.dot(constraint.row, projected[head].update).detach().cpu()) for constraint in constraints.get(head, ())},
                "active_set": list(projected[head].active_set),
                "distance": projected[head].distance,
            })
        result[head] = record
    return result


def direction_screen_go(endpoint: Mapping[str, Any]) -> bool:
    return bool(
        endpoint.get("identity_valid") is not False
        and endpoint.get("numerical_valid") is True
        and int(endpoint.get("accepted_updates", 0)) == SCREEN_ACCEPTED_UPDATES
        and endpoint.get("safety_gate", {}).get("passed") is True
        and float(endpoint.get("J_ratio", math.inf)) <= 0.95
    )


def adjudicate_direction_screens(arms: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    invalid = [arm for arm in DIRECTION_ARM_ORDER if arms.get(arm, {}).get("identity_valid") is False]
    complete = {arm: int(arms.get(arm, {}).get("accepted_updates", 0)) >= SCREEN_ACCEPTED_UPDATES for arm in DIRECTION_ARM_ORDER}
    if invalid:
        outcome = "MATCHED_DIRECTION_SCREEN_IDENTITY_INVALID"
    elif complete[CTRL] and complete[PROJ]:
        outcome = "PROJECTION_NOT_LOAD_BEARING"
    elif not complete[CTRL] and complete[PROJ]:
        outcome = "FEASIBLE_DIRECTION_PROJECTION_SUPPORTED"
    elif complete[CTRL] and not complete[PROJ]:
        outcome = "PROJECTION_HARMFUL_OR_UNNECESSARY"
    else:
        outcome = "NO_EXTENDED_FEASIBLE_PATH_FOUND"
    go = {arm: direction_screen_go(arms.get(arm, {})) for arm in DIRECTION_ARM_ORDER}
    selected = CTRL if go[CTRL] else (PROJ if go[PROJ] else None)
    if invalid:
        selected = None
    return {"feasible_direction_outcome": outcome, "complete": complete, "screen_go": go, "selected_arm": selected, "identity_invalid_arms": invalid}


def interface_replication_outcome(streams: Mapping[str, Mapping[str, Any]]) -> str:
    valid = [value for value in streams.values() if value.get("valid") is True]
    if len(valid) < 3:
        return "INTERFACE_REPLICATION_INCOMPLETE"
    deltas = [float(value["delta_Rmin"]) for value in valid]
    positive = sum(value > 0.0 for value in deltas)
    quality = sum(value.get("quality_preserved") is True for value in valid)
    if positive >= 2 and median(deltas) >= 0.03 and quality >= 2:
        return "INTERFACE_EFFECT_STREAM_REPLICATED"
    return "INTERFACE_EFFECT_NOT_ROBUST_ACROSS_STREAMS"


def forgetting_replication_outcome(streams: Mapping[str, Mapping[str, Any]]) -> str:
    valid = [value for value in streams.values() if value.get("valid") is True]
    if len(valid) < 3:
        return "FORGETTING_REPLICATION_INCOMPLETE"
    residual = sum(float(value.get("J_ratio", math.inf)) <= 0.50 for value in valid)
    collapse = sum(value.get("event_missing_or_min_recall_le_half") is True for value in valid)
    no_pareto = all(value.get("field_event_pareto") is not True for value in valid)
    if residual >= 2 and collapse >= 2 and no_pareto:
        return "PHYSICS_FORGETTING_STREAM_REPLICATED"
    return "PHYSICS_FORGETTING_STREAM_DEPENDENT"


def isolate_track_results(tracks: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    completed = sorted(name for name, value in tracks.items() if value.get("valid") is True)
    failed = sorted(name for name, value in tracks.items() if value.get("valid") is not True)
    return {"completed": completed, "failed": failed, "campaign_may_continue": bool(completed) or len(failed) < len(tracks)}


def _seed_all(seed: int = 17) -> None:
    random.seed(int(seed)); np.random.seed(int(seed)); torch.manual_seed(int(seed))
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(int(seed))


def _append(handle: Any, payload: Mapping[str, Any]) -> None:
    handle.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n")
    handle.flush()


def _set_lr(optimizer: torch.optim.Optimizer, learning_rate: float) -> None:
    for group in optimizer.param_groups:
        group["lr"] = float(learning_rate)


def _available_lrs(current: float) -> tuple[float, ...]:
    index = min(range(len(LR_LADDER)), key=lambda value: abs(LR_LADDER[value] - float(current)))
    if not math.isclose(LR_LADDER[index], float(current), rel_tol=0.0, abs_tol=1e-16):
        raise ValueError("LF10 accepted learning rate left frozen ladder")
    return LR_LADDER[index:]


def _strong_runtime_bindings(contracts: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    data = contracts["data"]
    return {
        "data": {
            "initial_DEV_R": {
                "checkpoint_path": data["DEV_R"]["checkpoint_path"],
                "checkpoint_sha256": data["DEV_R"]["checkpoint_sha256"],
            },
            "materialized_ledger": copy.deepcopy(data["strong_ledger"]),
        }
    }


def _strong_qualification(qualification: Mapping[str, Any]) -> dict[str, Any]:
    source = qualification.get("inherited_strong_ledger", qualification.get("strong_ledger", {}))
    normalized = dict(source)
    if "sha256" in normalized and "file_sha256" not in normalized:
        normalized["file_sha256"] = normalized["sha256"]
    return {"ledger": normalized}


def load_dev_r_model(
    path: Path, *, physics: Any, config: Any, device: torch.device,
    contracts: Mapping[str, Mapping[str, Any]],
) -> tuple[torch.nn.Module, dict[str, Any]]:
    return lf7.load_dev_r_model(path, physics=physics, config=config, device=device, contracts=_strong_runtime_bindings(contracts))


def _make_direction_optimizer(model: torch.nn.Module) -> torch.optim.Adam:
    return torch.optim.Adam(model.parameters(), lr=ETA0, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0, amsgrad=False)


def _fixed_j(model: torch.nn.Module, ledger: lf7.MaterializedPhysicsLedger, config: Any, device: torch.device) -> tuple[float, dict[str, float]]:
    batch = ledger.fixed_batch(device=device)
    with torch.enable_grad():
        _, components = _physics_objective(model, batch, config)
    return float(components["physics_total"]), components


def _direction_audit(model: torch.nn.Module, dataset: Any, ledger: lf7.MaterializedPhysicsLedger, config: Any, device: torch.device) -> dict[str, Any]:
    medium = full_medium_audit(model, dataset, device=device)
    value, components = _fixed_j(model, ledger, config, device)
    return {"medium": medium, "fixed_blind_physics": value, "fixed_blind_components": components}


def propose_and_resolve_step(
    *,
    arm: str,
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    physics_loss: torch.Tensor,
    audit_batch: MeasureBatch,
    audit_baselines: Mapping[str, float],
    physics: Any,
    device: torch.device,
    remaining_steps: int,
) -> dict[str, Any]:
    """Execute the matched one-step direction transaction and apply its result."""

    groups = field_parameter_groups(model)
    proposal = extract_adam_proposed_update(model, optimizer, physics_loss, parameter_groups=groups)
    objectives = audit_preservation_objectives(model, audit_batch, physics=physics, device=device)
    constraints, current = linearize_head_constraints(
        objectives, audit_baselines, PROJECTION_BOUNDS, groups,
        remaining_steps=remaining_steps,
    )
    resolved = resolve_head_updates(arm, proposal.updates, constraints)
    geometry = direction_geometry(proposal.updates, constraints, resolved.projections)
    if not resolved.feasible:
        return {
            "applied": False, "reason": resolved.reason, "proposal": proposal,
            "constraints": constraints, "constraint_values": current,
            "geometry": geometry, "resolved": resolved,
        }
    apply_head_updates(groups, resolved.updates)
    if not all(bool(torch.all(torch.isfinite(parameter))) for parameter in model.parameters()):
        raise FloatingPointError("LF10 resolved update produced non-finite parameters")
    return {
        "applied": True, "reason": "APPLIED", "proposal": proposal,
        "constraints": constraints, "constraint_values": current,
        "geometry": geometry, "resolved": resolved,
    }


def audit_constraint_geometry(
    model: torch.nn.Module,
    audit_batch: MeasureBatch,
    proposed_updates: Mapping[str, Sequence[torch.Tensor]],
    *,
    audit_baselines: Mapping[str, float],
    physics: Any,
    device: torch.device,
    remaining_steps: int = BLOCK_SIZE,
) -> dict[str, Any]:
    """Qualification/public seam: read-only constraints and CTRL/PROJ geometry."""

    groups = field_parameter_groups(model)
    objectives = audit_preservation_objectives(model, audit_batch, physics=physics, device=device)
    constraints, values = linearize_head_constraints(
        objectives, audit_baselines, PROJECTION_BOUNDS, groups,
        remaining_steps=remaining_steps,
    )
    projected = resolve_head_updates(PROJ, proposed_updates, constraints)
    return {
        "feasible": projected.feasible,
        "constraint_values": values,
        "geometry": direction_geometry(proposed_updates, constraints, projected.projections),
        "projection_reason": projected.reason,
        "zero_update_feasible": all(
            all(0.0 <= constraint.rhs + 1e-10 for constraint in rows)
            for rows in constraints.values()
        ),
    }


def _make_direction_runtime(
    *, arm: str, root: Path, dataset: Any, strong_ledger: lf7.MaterializedPhysicsLedger,
    initial_checkpoint: Path, contracts: Mapping[str, Mapping[str, Any]],
    qualification: Mapping[str, Any], physics: Any, config: Any,
    device: torch.device,
) -> dict[str, Any]:
    directory = root / "direction" / arm.lower()
    directory.mkdir(parents=True, exist_ok=False)
    model, _ = load_dev_r_model(initial_checkpoint, physics=physics, config=config, device=device, contracts=contracts)
    configure_phase_for_next_accepted_update(model, accepted_updates=0)
    optimizer = _make_direction_optimizer(model)
    baseline_medium = qualification.get("dev_r_full_medium_audit")
    if not isinstance(baseline_medium, Mapping):
        baseline_medium = full_medium_audit(model, dataset, device=device)
    baseline_j, _ = _fixed_j(model, strong_ledger, config, device)
    return {
        "arm": arm, "directory": directory, "model": model, "optimizer": optimizer,
        "accepted": 0, "attempted": 0, "rejected": 0, "current_lr": ETA0,
        "accepted_lrs": [], "identity_valid": True, "numerical_valid": True,
        "disposition": "NOT_STARTED", "last_rejection": [],
        "baseline_medium": copy.deepcopy(dict(baseline_medium)), "baseline_j": baseline_j,
        "last_audit": _direction_audit(model, dataset, strong_ledger, config, device),
    }


def _projection_record(step: Mapping[str, Any]) -> dict[str, Any]:
    proposal: AdamProposal = step["proposal"]
    resolved: HeadUpdateDecision = step["resolved"]
    return {
        "physics_loss": proposal.total_loss,
        "gradient_norm_before_clip": proposal.gradient_norm_before_clip,
        "clip_factor": proposal.clip_factor,
        "per_head_gradient_norm_before_clip": dict(proposal.per_head_gradient_norm_before_clip),
        "constraint_values": dict(step["constraint_values"]),
        "geometry": step["geometry"],
        "projection_feasible": resolved.feasible,
        "projection_reason": resolved.reason,
    }


def _advance_direction(
    runtime: dict[str, Any], *, target_accepted: int, attempted_cap: int,
    dataset: Any, strong_ledger: lf7.MaterializedPhysicsLedger,
    lf10_ledger: MaterializedLF10Ledger, physics: Any, config: Any,
    device: torch.device,
) -> None:
    model, optimizer = runtime["model"], runtime["optimizer"]
    telemetry_path = runtime["directory"] / "telemetry.jsonl"
    batches_path = runtime["directory"] / "batch_ledger.jsonl"
    with telemetry_path.open("a", encoding="utf-8", newline="\n") as telemetry, batches_path.open("a", encoding="utf-8", newline="\n") as batches:
        while runtime["accepted"] < int(target_accepted):
            configure_phase_for_next_accepted_update(model, accepted_updates=runtime["accepted"])
            snapshot = lf8.take_snapshot(model, optimizer, accepted_updates=runtime["accepted"], learning_rate=runtime["current_lr"])
            snapshot_hash = lf8.snapshot_digest(snapshot)
            accepted_before = int(runtime["accepted"])
            previous_j = float(runtime["last_audit"]["fixed_blind_physics"])
            block_accepted = False
            for learning_rate in _available_lrs(runtime["current_lr"]):
                if runtime["attempted"] >= int(attempted_cap):
                    break
                lf8.restore_snapshot(snapshot, model, optimizer)
                _set_lr(optimizer, learning_rate)
                step_records: list[dict[str, Any]] = []
                batch_records: list[dict[str, Any]] = []
                rejection: list[str] = []
                for local_index in range(BLOCK_SIZE):
                    if runtime["attempted"] >= int(attempted_cap):
                        rejection = ["ATTEMPT_CAP_REACHED"]
                        break
                    accepted_step = accepted_before + local_index + 1
                    configure_phase_for_next_accepted_update(model, accepted_updates=accepted_step - 1)
                    groups = field_parameter_groups(model)
                    physics_batch = strong_ledger.physics_batch(accepted_step, device=device)
                    loss, components = _physics_objective(model, physics_batch, config)
                    audit_batch = lf10_ledger.audit_batch(accepted_step, dataset)
                    matched_baselines = lf10_ledger.audit_baselines(accepted_step)
                    step = propose_and_resolve_step(
                        arm=runtime["arm"], model=model, optimizer=optimizer,
                        physics_loss=loss, audit_batch=audit_batch,
                        audit_baselines=matched_baselines, physics=physics,
                        device=device, remaining_steps=BLOCK_SIZE - local_index,
                    )
                    runtime["attempted"] += 1
                    batch_records.append({
                        "accepted_step": accepted_step, "physics_batch_sha256": physics_batch.batch_sha256,
                        "audit_batch_sha256": audit_batch.batch_sha256,
                    })
                    step_records.append({"accepted_step": accepted_step, **components, **_projection_record(step)})
                    if not step["applied"]:
                        rejection = [step["reason"]]
                        break
                if not rejection and len(step_records) == BLOCK_SIZE:
                    proposed = _direction_audit(model, dataset, strong_ledger, config, device)
                    gate = lf7.competence_gate(
                        proposed["medium"], runtime["baseline_medium"],
                        physics_previous=previous_j, physics_new=proposed["fixed_blind_physics"],
                    )
                    if not gate["passed"]:
                        rejection = list(gate["failed_checks"])
                else:
                    proposed = runtime["last_audit"]
                    gate = {"passed": False, "failed_checks": rejection, "checks": {}}
                record = {
                    "arm": runtime["arm"], "accepted_before": accepted_before,
                    "learning_rate": learning_rate, "attempted_after": runtime["attempted"],
                    "snapshot_sha256": snapshot_hash, "steps": step_records,
                    "proposed_audit": proposed, "filter_gate": gate,
                }
                if gate["passed"]:
                    runtime["accepted"] = accepted_before + BLOCK_SIZE
                    runtime["current_lr"] = float(learning_rate)
                    runtime["accepted_lrs"].append(float(learning_rate))
                    runtime["last_audit"] = proposed
                    runtime["last_rejection"] = []
                    record.update({"decision": "ACCEPT", "accepted_after": runtime["accepted"]})
                    _append(telemetry, record)
                    for value in batch_records:
                        _append(batches, {**value, "decision": "ACCEPT", "learning_rate": learning_rate})
                    block_accepted = True
                    break
                runtime["rejected"] += 1
                runtime["last_rejection"] = rejection
                restored = lf8.restore_snapshot(snapshot, model, optimizer)
                record.update({
                    "decision": "REJECT_ROLLBACK", "accepted_after": accepted_before,
                    "reject_reason": rejection, "restored_state_sha256": restored,
                    "snapshot_still_immutable": lf8.snapshot_digest(snapshot) == snapshot_hash,
                })
                _append(telemetry, record)
                for value in batch_records:
                    _append(batches, {**value, "decision": "REJECT", "learning_rate": learning_rate})
            if not block_accepted:
                lf8.restore_snapshot(snapshot, model, optimizer)
                runtime["disposition"] = "ATTEMPT_CAP_REACHED_WITH_VALID_PREFIX" if runtime["attempted"] >= attempted_cap else "FILTER_STALLED_WITH_VALID_PREFIX"
                break
        if runtime["accepted"] == int(target_accepted):
            runtime["disposition"] = "SCREEN_COMPLETE" if int(target_accepted) == SCREEN_ACCEPTED_UPDATES else "FULL_COMPLETE"


def _direction_endpoint(runtime: Mapping[str, Any], *, target: int) -> dict[str, Any]:
    audit = runtime["last_audit"]
    safety = lf7.competence_gate(audit["medium"], runtime["baseline_medium"])
    strict = lf7.competence_gate(audit["medium"], runtime["baseline_medium"], strict_timing=True)
    ratio = float(audit["fixed_blind_physics"]) / float(runtime["baseline_j"])
    valid = bool(runtime["identity_valid"] and runtime["numerical_valid"] and audit["medium"].get("all_values_finite") is True)
    return {
        "arm": runtime["arm"], "identity_valid": bool(runtime["identity_valid"]),
        "numerical_valid": valid, "accepted_updates": int(runtime["accepted"]),
        "attempted_updates": int(runtime["attempted"]), "accepted_blocks": int(runtime["accepted"]) // BLOCK_SIZE,
        "rejected_block_attempts": int(runtime["rejected"]), "accepted_learning_rates": list(runtime["accepted_lrs"]),
        "final_learning_rate": float(runtime["current_lr"]), "disposition": runtime["disposition"],
        "safety_gate": safety, "strict_gate": strict, "J0": float(runtime["baseline_j"]),
        "J": float(audit["fixed_blind_physics"]), "J_ratio": ratio,
        "final_audit": audit, "target_accepted_updates": int(target),
        "last_rejection": list(runtime["last_rejection"]),
    }


def _write_checkpoint(
    path: Path, *, model: torch.nn.Module, optimizer: torch.optim.Optimizer,
    config: Any, role: str, update: int, source_identity: str,
    parent_sha256: str, physics_program_sha256: str, physics_object_sha256: str,
    extra: Mapping[str, Any] | None = None,
) -> Path:
    payload = _checkpoint_payload(
        model=model, optimizer=optimizer, config=config, update=int(update),
        program_contract_sha256=_sha256_path(V22R_PROGRAM_CONTRACT_PATH),
        method_contract_sha256=_sha256_path(V22R_METHOD_CONTRACT_PATH),
        physical_program_sha256=physics_program_sha256,
        physical_object_sha256=physics_object_sha256,
    )
    payload["lf10"] = {
        "schema_id": "phk-v23-lf10-checkpoint-metadata-v1", "task_id": TASK_ID,
        "role": role, "optimizer_update": int(update), "source_identity": source_identity,
        "contracts": contract_identity(), "parent_checkpoint_sha256": parent_sha256,
        "runtime_sampling_used": False, "stress_read": False, **dict(extra or {}),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        torch.save(payload, handle)
    return path


def _persist_model_endpoint(
    directory: Path, *, prefix: str, model: torch.nn.Module,
    optimizer: torch.optim.Optimizer, config: Any, role: str, update: int,
    source_identity: str, parent_sha256: str, physics_program_sha256: str,
    physics_object_sha256: str, device_name: str, extra: Mapping[str, Any] | None = None,
) -> tuple[Path, Path]:
    checkpoint = _write_checkpoint(
        directory / f"{prefix}checkpoint.pt", model=model, optimizer=optimizer,
        config=config, role=role, update=update, source_identity=source_identity,
        parent_sha256=parent_sha256, physics_program_sha256=physics_program_sha256,
        physics_object_sha256=physics_object_sha256, extra=extra,
    )
    prediction = write_prediction_carrier(
        checkpoint_path=checkpoint, output_path=directory / f"{prefix}prediction.npz",
        device_name=device_name,
    )
    return checkpoint, prediction


def _persist_direction_endpoint(
    runtime: Mapping[str, Any], result: dict[str, Any], *, prefix: str,
    config: Any, source_identity: str, initial_checkpoint: Path,
    physics_program_sha256: str, physics_object_sha256: str, device_name: str,
) -> None:
    checkpoint, prediction = _persist_model_endpoint(
        runtime["directory"], prefix=prefix, model=runtime["model"], optimizer=runtime["optimizer"],
        config=config, role=f"DIRECTION_{runtime['arm']}_{prefix.rstrip('-').upper()}",
        update=runtime["accepted"], source_identity=source_identity,
        parent_sha256=_sha256_path(initial_checkpoint), physics_program_sha256=physics_program_sha256,
        physics_object_sha256=physics_object_sha256, device_name=device_name,
        extra={"medium_audit_gradient_used_for_direction": True, "physics_residual_used": True},
    )
    result["checkpoint_sha256"] = _sha256_path(checkpoint)
    result["prediction_sha256"] = _sha256_path(prediction)
    _write_json_exclusive(runtime["directory"] / f"{prefix}gate.json", result)


def _rmin(audit: Mapping[str, Any]) -> float:
    return min(float(audit["event_metrics"][f"cycle_{cycle}"].get("hard_recall") or 0.0) for cycle in (1, 2))


def _compact_event_metrics(audit: Mapping[str, Any]) -> dict[str, Any]:
    topology = audit["event_topology_hard_guard"]["cycles"]
    cycles: dict[str, Any] = {}
    for cycle in (1, 2):
        event = audit["event_metrics"][f"cycle_{cycle}"]
        topo = topology[cycle - 1]
        cycles[f"cycle_{cycle}"] = {
            "event_exists": event.get("event_exists"), "recall": event.get("hard_recall"),
            "precision": event.get("hard_precision"), "mass": event.get("hard_active_mass_ratio"),
            "timing": event.get("event_time_absolute_error"),
            "recovery": topo.get("recovery_fraction"),
        }
    return {"Rmin": _rmin(audit), "weighted_errors": dict(audit["weighted_errors"]), "topology_weighted_loss": audit["topology_weighted_loss"], "cycles": cycles}


def _run_interface_arm(
    *, seed: int, arm: str, root: Path, dataset: Any,
    lf10_ledger: MaterializedLF10Ledger, initial_checkpoint: Path,
    contracts: Mapping[str, Mapping[str, Any]], physics: Any, config: Any,
    device: torch.device, device_name: str, source_identity: str,
    physics_program_sha256: str, physics_object_sha256: str,
) -> dict[str, Any]:
    directory = root / "interface" / f"seed-{seed}" / ("dev-g" if arm == DEV_G else "dev-m")
    directory.mkdir(parents=True, exist_ok=False)
    model, _ = load_lf3_t0_model(
        initial_checkpoint, physics=physics, config=config, device=device,
        expected_sha256=contracts["data"]["LF3_T0"]["checkpoint_sha256"],
    )
    for field in ("potential", "temperature"):
        model.encoders[field].requires_grad_(False); model.heads[field].requires_grad_(False)
    phase_parameters = tuple(model.encoders["phase"].parameters()) + tuple(model.heads["phase"].parameters())
    vt_before = {field: _field_state_sha256(model, field) for field in ("potential", "temperature")}
    optimizer = torch.optim.Adam(phase_parameters, lr=1e-3, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0, amsgrad=False)
    telemetry_path = directory / "telemetry.jsonl"
    batches_path = directory / "batch_ledger.jsonl"
    executed = 0
    with telemetry_path.open("x", encoding="utf-8", newline="\n") as telemetry, batches_path.open("x", encoding="utf-8", newline="\n") as batches:
        for step in range(1, 401):
            optimizer.zero_grad(set_to_none=True)
            base = lf10_ledger.interface_base_batch(seed, step, dataset)
            extra_role = "global" if arm == DEV_G else "band"
            extra = lf10_ledger.interface_extra_batch(seed, extra_role, step)
            base_loss = measure_decoupled_terms(model, base, physics=physics, device=device)["phase_logit"]
            extra_loss = normalized_logit_mse(model, extra, physics=physics, device=device)
            total = 0.5 * base_loss + 0.5 * extra_loss
            if not bool(torch.isfinite(total)):
                raise FloatingPointError(f"LF10 interface seed {seed} {arm} non-finite loss")
            total.backward()
            grad_norm = float(torch.nn.utils.clip_grad_norm_(phase_parameters, 10.0).detach().cpu())
            if not math.isfinite(grad_norm):
                raise FloatingPointError(f"LF10 interface seed {seed} {arm} non-finite gradient")
            optimizer.step(); executed = step
            _append(batches, {"step": step, "base_sha256": base.batch_sha256, "extra_sha256": extra.batch_sha256})
            if step == 1 or step % 50 == 0:
                _append(telemetry, {"step": step, "L_base": float(base_loss.detach().cpu()), "L_extra": float(extra_loss.detach().cpu()), "L_total": float(total.detach().cpu()), "gradient_norm_before_clip": grad_norm, "audit": full_medium_audit(model, dataset, device=device)})
    audit = full_medium_audit(model, dataset, device=device)
    vt_after = {field: _field_state_sha256(model, field) for field in ("potential", "temperature")}
    numerical_valid = bool(executed == 400 and vt_before == vt_after and audit.get("all_values_finite") is True and audit["phase_range"]["passed"] and audit["potential_maximum_principle"]["passed"])
    checkpoint, prediction = _persist_model_endpoint(
        directory, prefix="", model=model, optimizer=optimizer, config=config,
        role=f"INTERFACE_STREAM_{seed}_{arm}", update=executed, source_identity=source_identity,
        parent_sha256=_sha256_path(initial_checkpoint), physics_program_sha256=physics_program_sha256,
        physics_object_sha256=physics_object_sha256, device_name=device_name,
        extra={"stream_seed": seed, "medium_labels_used": True, "physics_residual_used": False},
    )
    result = {
        "valid": numerical_valid, "identity_valid": True, "stream_seed": seed,
        "arm": arm, "executed_updates": executed, "audit": audit,
        "metrics": _compact_event_metrics(audit), "V_T_state_sha256": {"before": vt_before, "after": vt_after},
        "checkpoint_sha256": _sha256_path(checkpoint), "prediction_sha256": _sha256_path(prediction),
    }
    _write_json_exclusive(directory / "gate.json", result)
    return result


def _run_interface_pair(
    *, seed: int, root: Path, dataset: Any, lf10_ledger: MaterializedLF10Ledger,
    initial_checkpoint: Path, contracts: Mapping[str, Mapping[str, Any]],
    physics: Any, config: Any, device: torch.device, device_name: str,
    source_identity: str, physics_program_sha256: str, physics_object_sha256: str,
) -> dict[str, Any]:
    arms: dict[str, Any] = {}
    errors: list[dict[str, str]] = []
    for arm in (DEV_G, DEV_M):
        _seed_all(17)
        try:
            arms[arm] = _run_interface_arm(
                seed=seed, arm=arm, root=root, dataset=dataset, lf10_ledger=lf10_ledger,
                initial_checkpoint=initial_checkpoint, contracts=contracts, physics=physics,
                config=config, device=device, device_name=device_name, source_identity=source_identity,
                physics_program_sha256=physics_program_sha256, physics_object_sha256=physics_object_sha256,
            )
        except Exception as exc:
            arms[arm] = {"valid": False, "identity_valid": False, "stream_seed": seed, "arm": arm, "error": {"type": type(exc).__name__, "message": str(exc)}}
            errors.append({"arm": arm, "type": type(exc).__name__, "message": str(exc)})
    pair_valid = all(arms[arm].get("valid") is True for arm in (DEV_G, DEV_M))
    if pair_valid:
        g_audit, m_audit = arms[DEV_G]["audit"], arms[DEV_M]["audit"]
        delta = _rmin(m_audit) - _rmin(g_audit)
        quality = bool(
            _quality_preserved(m_audit, g_audit)
            and float(m_audit["weighted_errors"]["phase"])
            <= 1.10 * float(g_audit["weighted_errors"]["phase"])
        )
    else:
        delta, quality = math.nan, False
    result = {"valid": pair_valid, "stream_seed": seed, "arms": arms, "delta_Rmin": delta, "quality_preserved": quality, "errors": errors}
    pair_path = root / "interface" / f"seed-{seed}" / "pair.json"
    _write_json_exclusive(pair_path, result)
    return result


def _run_forgetting_replication(
    *, seed: int, root: Path, dataset: Any, lf10_ledger: MaterializedLF10Ledger,
    strong_ledger: lf7.MaterializedPhysicsLedger, initial_checkpoint: Path,
    contracts: Mapping[str, Mapping[str, Any]], physics: Any, config: Any,
    device: torch.device, device_name: str, source_identity: str,
    physics_program_sha256: str, physics_object_sha256: str,
) -> dict[str, Any]:
    directory = root / "forgetting" / f"seed-{seed}"
    directory.mkdir(parents=True, exist_ok=False)
    model, _ = load_dev_r_model(initial_checkpoint, physics=physics, config=config, device=device, contracts=contracts)
    configure_phase_for_next_accepted_update(model, accepted_updates=0)
    phase_before = _phase_state_sha256(model)
    phase_parameters = field_parameter_groups(model, trainable_only=False)["phase"]
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0, amsgrad=False)
    baseline_medium = full_medium_audit(model, dataset, device=device)
    baseline_j, _ = _fixed_j(model, strong_ledger, config, device)
    telemetry_path = directory / "telemetry.jsonl"; batches_path = directory / "batch_ledger.jsonl"
    executed = 0; step550: dict[str, Any] | None = None
    with telemetry_path.open("x", encoding="utf-8", newline="\n") as telemetry, batches_path.open("x", encoding="utf-8", newline="\n") as batches:
        for step in range(1, 1201):
            configure_phase_for_next_accepted_update(model, accepted_updates=step - 1)
            if step == PHASE_FREEZE_STEPS + 1:
                state_entries = sum(parameter in optimizer.state for parameter in phase_parameters)
                if _phase_state_sha256(model) != phase_before or state_entries != 0:
                    raise RuntimeError("LF10 forgetting replication phase-freeze identity drift")
            optimizer.zero_grad(set_to_none=True)
            batch = lf10_ledger.physics_batch(seed, step, device=device)
            loss, components = _physics_objective(model, batch, config)
            if not bool(torch.isfinite(loss)):
                raise FloatingPointError(f"LF10 forgetting seed {seed} non-finite loss")
            loss.backward()
            trainable = tuple(parameter for parameter in model.parameters() if parameter.requires_grad)
            grad_norm = float(torch.nn.utils.clip_grad_norm_(trainable, 10.0).detach().cpu())
            if not math.isfinite(grad_norm):
                raise FloatingPointError(f"LF10 forgetting seed {seed} non-finite gradient")
            optimizer.step(); executed = step
            _append(batches, {"step": step, "batch_sha256": batch.batch_sha256})
            if step == PHASE_FREEZE_STEPS:
                step550 = {"phase_before_sha256": phase_before, "phase_after_sha256": _phase_state_sha256(model), "bitwise_preserved": phase_before == _phase_state_sha256(model), "phase_optimizer_state_entries": sum(parameter in optimizer.state for parameter in phase_parameters)}
            if step == 1 or step % 50 == 0:
                audit = full_medium_audit(model, dataset, device=device)
                blind_j, _ = _fixed_j(model, strong_ledger, config, device)
                _append(telemetry, {"step": step, **components, "total_loss": float(loss.detach().cpu()), "gradient_norm_before_clip": grad_norm, "fixed_blind_J": blind_j, "audit": audit})
    final_audit = full_medium_audit(model, dataset, device=device)
    final_j, final_components = _fixed_j(model, strong_ledger, config, device)
    j_ratio = final_j / baseline_j
    safety = lf7.competence_gate(final_audit, baseline_medium)
    recalls = [final_audit["event_metrics"][f"cycle_{cycle}"].get("hard_recall") for cycle in (1, 2)]
    events = [final_audit["event_metrics"][f"cycle_{cycle}"].get("event_exists") is True for cycle in (1, 2)]
    collapse = not all(events) or min(float(value or 0.0) for value in recalls) <= 0.50
    numerical_valid = bool(executed == 1200 and final_audit.get("all_values_finite") is True and final_audit["phase_range"]["passed"] and final_audit["potential_maximum_principle"]["passed"])
    checkpoint, prediction = _persist_model_endpoint(
        directory, prefix="", model=model, optimizer=optimizer, config=config,
        role=f"FORGETTING_STREAM_{seed}", update=executed, source_identity=source_identity,
        parent_sha256=_sha256_path(initial_checkpoint), physics_program_sha256=physics_program_sha256,
        physics_object_sha256=physics_object_sha256, device_name=device_name,
        extra={"stream_seed": seed, "medium_audit_gradient_used_for_direction": False, "physics_residual_used": True},
    )
    result = {
        "valid": numerical_valid, "identity_valid": True, "stream_seed": seed,
        "executed_updates": executed, "J0": baseline_j, "J": final_j, "J_ratio": j_ratio,
        "fixed_blind_components": final_components, "final_audit": final_audit,
        "metrics": _compact_event_metrics(final_audit), "safety_gate": safety,
        "event_missing_or_min_recall_le_half": collapse,
        "field_event_pareto": bool(j_ratio <= 0.50 and safety["passed"]),
        "step550": step550, "checkpoint_sha256": _sha256_path(checkpoint),
        "prediction_sha256": _sha256_path(prediction),
    }
    _write_json_exclusive(directory / "gate.json", result)
    return result


def _historical_interface_record(qualification: Mapping[str, Any]) -> dict[str, Any]:
    supplied = qualification.get("historical_interface_stream_17")
    if isinstance(supplied, Mapping):
        return dict(supplied)
    return {"valid": True, "stream_seed": 17, "delta_Rmin": 0.08983668354595331, "quality_preserved": True, "source": "LF4_TERMINAL"}


def _historical_forgetting_record(qualification: Mapping[str, Any]) -> dict[str, Any]:
    supplied = qualification.get("historical_forgetting_stream_17")
    if isinstance(supplied, Mapping):
        return dict(supplied)
    return {"valid": True, "stream_seed": 17, "J_ratio": 0.012814226536278206, "event_missing_or_min_recall_le_half": True, "field_event_pareto": False, "source": "LF6_TERMINAL"}


def _invalid_result(role: str, exc: BaseException) -> dict[str, Any]:
    return {
        "role": role, "valid": False, "identity_valid": False,
        "numerical_valid": False, "accepted_updates": 0,
        "error": {"type": type(exc).__name__, "message": str(exc)},
    }


def prelocal_internal_pareto(result: Mapping[str, Any]) -> bool:
    return bool(
        result.get("identity_valid") is not False
        and result.get("numerical_valid") is True
        and int(result.get("accepted_updates", 0)) == FULL_ACCEPTED_UPDATES
        and result.get("strict_gate", {}).get("passed") is True
        and float(result.get("J_ratio", math.inf)) <= 0.50
    )


def execute_gpu_campaign(
    *,
    output_root: Path,
    medium_carrier: Path,
    lf3_t0_checkpoint: Path,
    dev_r_checkpoint: Path,
    strong_ledger: Path,
    lf10_ledger: Path,
    lf10_ledger_manifest: Path,
    cpu_qualification_path: Path,
    source_identity: str,
    device_name: str,
) -> dict[str, Any]:
    """Execute all nonshared LF10 tracks and the conditional continuation."""

    contracts = load_contracts()
    qualification = read_cpu_qualification(cpu_qualification_path)
    prefix = "LF10-BUNDLE-"
    digest = source_identity[len(prefix):] if source_identity.startswith(prefix) else ""
    if len(digest) != 64 or digest != digest.upper() or any(value not in "0123456789ABCDEF" for value in digest):
        raise ValueError("LF10 source identity must be the content-addressed deployment bundle")
    if not device_name.startswith("cuda") or not torch.cuda.is_available():
        raise RuntimeError("LF10 requires CUDA")
    device = torch.device(device_name)
    gpu_name = torch.cuda.get_device_name(device)
    if gpu_name != "Tesla V100-PCIE-32GB":
        raise RuntimeError("LF10 requires Tesla V100-PCIE-32GB")
    root = Path(output_root).resolve()
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise FileExistsError(f"LF10 output root must be empty: {root}")
    root.mkdir(parents=True, exist_ok=True)
    data = contracts["data"]
    exact_inputs = (
        (Path(medium_carrier), data["medium"]["sha256"], "medium"),
        (Path(lf3_t0_checkpoint), data["LF3_T0"]["checkpoint_sha256"], "LF3-T0"),
        (Path(dev_r_checkpoint), data["DEV_R"]["checkpoint_sha256"], "DEV-R"),
        (Path(strong_ledger), data["strong_ledger"]["file_sha256"], "strong ledger"),
    )
    for path, expected, label in exact_inputs:
        if not path.is_file() or _sha256_path(path) != expected:
            raise ValueError(f"LF10 {label} input binding drift")

    config = build_training_config(device_name)
    physics, physics_program_sha256, physics_object_sha256 = load_case_physics(config.case_control)
    dataset = load_medium_dataset(Path(medium_carrier), physics=physics, contracts={"data": {"training_source": data["medium"]}})
    strong = lf7.MaterializedPhysicsLedger(
        Path(strong_ledger), contracts=_strong_runtime_bindings(contracts),
        qualification=_strong_qualification(qualification),
    )
    materialized = MaterializedLF10Ledger(Path(lf10_ledger), Path(lf10_ledger_manifest), qualification=qualification)
    started = datetime.now(timezone.utc).isoformat()
    errors: list[dict[str, str]] = []
    _write_json_exclusive(root / "manifest-start.json", {
        "schema_id": "phk-v23-lf10-run-manifest-v1", "task_id": TASK_ID,
        "status": "RUNNING_REFERENCE_BLIND_GPU_CAMPAIGN", "source_identity": source_identity,
        "contracts": contract_identity(), "gpu": gpu_name, "dtype": "FLOAT64", "seed": 17,
        "input_bindings": {label: {"sha256": expected} for _, expected, label in exact_inputs},
        "lf10_ledger_semantic_sha256": materialized.semantic_sha256,
        "fine_extra_lf_only_evaluator_stress_read": False,
    })

    direction_runtimes: dict[str, dict[str, Any]] = {}
    direction_arms: dict[str, dict[str, Any]] = {}
    for arm in DIRECTION_ARM_ORDER:
        _seed_all(17)
        runtime: dict[str, Any] | None = None
        try:
            runtime = _make_direction_runtime(
                arm=arm, root=root, dataset=dataset, strong_ledger=strong,
                initial_checkpoint=Path(dev_r_checkpoint), contracts=contracts,
                qualification=qualification, physics=physics, config=config, device=device,
            )
            _advance_direction(
                runtime, target_accepted=SCREEN_ACCEPTED_UPDATES,
                attempted_cap=SCREEN_ATTEMPTED_CAP, dataset=dataset,
                strong_ledger=strong, lf10_ledger=materialized, physics=physics,
                config=config, device=device,
            )
            result = _direction_endpoint(runtime, target=SCREEN_ACCEPTED_UPDATES)
            result["screen_go"] = direction_screen_go(result)
            _persist_direction_endpoint(
                runtime, result, prefix="screen-", config=config,
                source_identity=source_identity, initial_checkpoint=Path(dev_r_checkpoint),
                physics_program_sha256=physics_program_sha256,
                physics_object_sha256=physics_object_sha256, device_name=device_name,
            )
            direction_runtimes[arm] = runtime; direction_arms[arm] = result
        except Exception as exc:
            result = _invalid_result(f"DIRECTION_{arm}", exc)
            if runtime is not None:
                result.update({"accepted_updates": int(runtime["accepted"]), "attempted_updates": int(runtime["attempted"])})
            direction_arms[arm] = result
            errors.append({"track": f"DIRECTION_{arm}", "type": type(exc).__name__, "message": str(exc)})
    direction_decision = adjudicate_direction_screens(direction_arms)
    selected = direction_decision["selected_arm"]
    full: dict[str, Any] = {"executed": False, "reason": "NO_SCREEN_GO"}
    if selected is not None:
        runtime = direction_runtimes[selected]
        try:
            _advance_direction(
                runtime, target_accepted=FULL_ACCEPTED_UPDATES,
                attempted_cap=FULL_ATTEMPTED_CAP, dataset=dataset,
                strong_ledger=strong, lf10_ledger=materialized, physics=physics,
                config=config, device=device,
            )
            full = _direction_endpoint(runtime, target=FULL_ACCEPTED_UPDATES)
            full["executed"] = True
            full["prelocal_internal_pareto"] = prelocal_internal_pareto(full)
            full["complete_internal_pinn_pareto"] = "PENDING_POST_SHUTDOWN_LOCAL_EVALUATION" if full["prelocal_internal_pareto"] else False
            _persist_direction_endpoint(
                runtime, full, prefix="full-", config=config,
                source_identity=source_identity, initial_checkpoint=Path(dev_r_checkpoint),
                physics_program_sha256=physics_program_sha256,
                physics_object_sha256=physics_object_sha256, device_name=device_name,
            )
        except Exception as exc:
            full = {**_invalid_result(f"DIRECTION_{selected}_FULL", exc), "executed": True, "accepted_updates": int(runtime["accepted"]), "attempted_updates": int(runtime["attempted"]), "prelocal_internal_pareto": False, "complete_internal_pinn_pareto": False}
            errors.append({"track": f"DIRECTION_{selected}_FULL", "type": type(exc).__name__, "message": str(exc)})

    interface: dict[str, dict[str, Any]] = {"17": _historical_interface_record(qualification)}
    for seed in STREAM_SEEDS:
        try:
            interface[str(seed)] = _run_interface_pair(
                seed=seed, root=root, dataset=dataset, lf10_ledger=materialized,
                initial_checkpoint=Path(lf3_t0_checkpoint), contracts=contracts,
                physics=physics, config=config, device=device, device_name=device_name,
                source_identity=source_identity, physics_program_sha256=physics_program_sha256,
                physics_object_sha256=physics_object_sha256,
            )
        except Exception as exc:
            interface[str(seed)] = {"valid": False, "stream_seed": seed, "error": {"type": type(exc).__name__, "message": str(exc)}}
            errors.append({"track": f"INTERFACE_{seed}", "type": type(exc).__name__, "message": str(exc)})
    interface_outcome = interface_replication_outcome(interface)

    forgetting: dict[str, dict[str, Any]] = {"17": _historical_forgetting_record(qualification)}
    for seed in STREAM_SEEDS:
        _seed_all(17)
        try:
            forgetting[str(seed)] = _run_forgetting_replication(
                seed=seed, root=root, dataset=dataset, lf10_ledger=materialized,
                strong_ledger=strong, initial_checkpoint=Path(dev_r_checkpoint),
                contracts=contracts, physics=physics, config=config, device=device,
                device_name=device_name, source_identity=source_identity,
                physics_program_sha256=physics_program_sha256,
                physics_object_sha256=physics_object_sha256,
            )
        except Exception as exc:
            forgetting[str(seed)] = {"valid": False, "stream_seed": seed, "error": {"type": type(exc).__name__, "message": str(exc)}}
            errors.append({"track": f"FORGETTING_{seed}", "type": type(exc).__name__, "message": str(exc)})
    forgetting_outcome = forgetting_replication_outcome(forgetting)

    if full.get("prelocal_internal_pareto"):
        primary_prelocal = "PENDING_POST_SHUTDOWN_DIRECT_BASELINE_ADJUDICATION"
    elif selected is not None:
        primary_prelocal = "LF10_SAFE_PATH_EXTENDED_FULL_PARETO_NOT_REACHED"
    else:
        primary_prelocal = "LF10_FEASIBLE_DIRECTION_SCREEN_NEGATIVE_PAPER_STRENGTHENED"
    artifacts: dict[str, Any] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "run_summary.json":
            artifacts[path.relative_to(root).as_posix()] = _artifact_record(path, root)
    prediction_artifacts = {
        relative.replace("/", ":").removesuffix(":prediction.npz").removesuffix(":screen-prediction.npz").removesuffix(":full-prediction.npz"): record
        for relative, record in artifacts.items()
        if relative.endswith("prediction.npz")
    }
    track_isolation = isolate_track_results({
        "direction": {"valid": all(value.get("identity_valid") is not False for value in direction_arms.values())},
        "interface": {"valid": interface_outcome != "INTERFACE_REPLICATION_INCOMPLETE"},
        "forgetting": {"valid": forgetting_outcome != "FORGETTING_REPLICATION_INCOMPLETE"},
    })
    summary = {
        "schema_id": "phk-v23-lf10-reference-blind-run-summary-v1",
        "task_id": TASK_ID, "title": TITLE,
        "status": "LF10_REFERENCE_BLIND_GPU_CAMPAIGN_COMPLETE" if not errors else "LF10_CAMPAIGN_COMPLETE_WITH_ISOLATED_TRACK_ERRORS",
        "started_at_utc": started, "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_identity": source_identity, "gpu": gpu_name, "dtype": "FLOAT64", "seed": 17,
        "direction_arms": direction_arms,
        "feasible_direction_outcome": direction_decision["feasible_direction_outcome"],
        "direction_screen_decision": direction_decision,
        "arms": direction_arms,
        "direction_decision": direction_decision,
        "selected_direction_arm": selected, "full_refinement": full,
        "interface_replications": interface, "interface_replication_outcome": interface_outcome,
        "interface_replication": {"outcome": interface_outcome, "streams": interface},
        "forgetting_replications": forgetting, "forgetting_replication_outcome": forgetting_outcome,
        "forgetting_replication": {"outcome": forgetting_outcome, "streams": forgetting},
        "primary_outcome_prelocal": primary_prelocal, "track_isolation": track_isolation,
        "errors": errors,
        "ledger": {"file_sha256": _sha256_path(Path(lf10_ledger)), "manifest_sha256": _sha256_path(Path(lf10_ledger_manifest)), "semantic_sha256": materialized.semantic_sha256, "streams": materialized.streams},
        "strong_ledger": {"file_sha256": _sha256_path(Path(strong_ledger)), "physics_1200_sha256": strong.physics_sha256, "fixed_blind_pool_sha256": data["strong_ledger"]["fixed_blind_pool_sha256"]},
        "artifacts": artifacts, "prediction_artifacts": prediction_artifacts,
        "medium_audit_gradient_used_for_direction_only": True,
        "medium_audit_entered_physics_loss": False,
        "runtime_sampling_used": False,
        "fine_extra_lf_only_evaluator_stress_read": False,
    }
    _write_json_exclusive(root / "run_summary.json", summary)
    return summary


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--medium-carrier", type=Path, required=True)
    parser.add_argument("--lf3-t0-checkpoint", type=Path, required=True)
    parser.add_argument("--dev-r-checkpoint", type=Path, required=True)
    parser.add_argument("--strong-ledger", type=Path, required=True)
    parser.add_argument("--lf10-ledger", type=Path, required=True)
    parser.add_argument("--lf10-ledger-manifest", type=Path, required=True)
    parser.add_argument("--cpu-qualification", type=Path, required=True)
    parser.add_argument("--source-identity", required=True)
    parser.add_argument("--device", default="cuda:0")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    summary = execute_gpu_campaign(
        output_root=args.output_root, medium_carrier=args.medium_carrier,
        lf3_t0_checkpoint=args.lf3_t0_checkpoint, dev_r_checkpoint=args.dev_r_checkpoint,
        strong_ledger=args.strong_ledger, lf10_ledger=args.lf10_ledger,
        lf10_ledger_manifest=args.lf10_ledger_manifest,
        cpu_qualification_path=args.cpu_qualification, source_identity=args.source_identity,
        device_name=args.device,
    )
    print(json.dumps({
        "status": summary["status"],
        "feasible_direction_outcome": summary["feasible_direction_outcome"],
        "interface_replication_outcome": summary["interface_replication_outcome"],
        "forgetting_replication_outcome": summary["forgetting_replication_outcome"],
        "selected_direction_arm": summary["selected_direction_arm"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "AUDIT_BASELINE_COLUMNS", "AdamProposal", "BLOCK_SIZE", "CTRL", "DIRECTION_ARM_ORDER", "FULL_ACCEPTED_UPDATES",
    "HeadUpdateDecision", "LinearConstraint", "MaterializedLF10Ledger", "PROJ",
    "ProjectionResult", "SCREEN_ACCEPTED_UPDATES", "TASK_ID", "TITLE",
    "adjudicate_direction_screens", "apply_head_updates", "array_sha256",
    "audit_constraint_geometry", "audit_preservation_objectives", "configure_phase_for_next_accepted_update",
    "contract_identity", "direction_geometry", "direction_screen_go",
    "execute_gpu_campaign", "extract_adam_proposed_update", "field_parameter_groups",
    "forgetting_replication_outcome", "interface_replication_outcome", "isolate_track_results",
    "ledger_array_names", "linearize_head_constraints", "load_contracts", "main",
    "prelocal_internal_pareto", "project_update_nearest", "propose_and_resolve_step",
    "read_cpu_qualification", "resolve_head_updates", "semantic_ledger_sha256",
]
