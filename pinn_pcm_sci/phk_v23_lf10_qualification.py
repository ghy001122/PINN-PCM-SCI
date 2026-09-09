"""Zero-update CPU qualification and stream materialisation for LF10."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .ledger import RunManifest
from .phk_v22r_prediction import _load_model
from .phk_v22r_training import ROOT, load_case_physics
from .phk_v23_lf0 import LF0PhysicsBatchStream, PhysicsBatch, _batch_sha256, _physics_objective, _sha256_path, _write_json_exclusive
from .phk_v23_lf2 import CATEGORY_NAMES, CATEGORY_QUOTAS, MeasureBatch, load_medium_dataset
from .phk_v23_lf3 import build_training_config, full_medium_audit
from .phk_v23_lf4 import BAND_POOL_NAMES, InterfaceBandDataset
from .phk_v23_lf10 import (
    BLOCK_SIZE,
    CTRL,
    DEV_R_BASELINE,
    DEV_R_TOPOLOGY,
    FULL_ACCEPTED_UPDATES,
    LR_LADDER,
    PROJ,
    PROJECTION_BOUNDS,
    STREAM_SEEDS,
    TASK_ID,
    LinearConstraint,
    MaterializedLF10Ledger,
    array_sha256,
    audit_preservation_objectives,
    contract_identity,
    direction_geometry,
    extract_adam_proposed_update,
    field_parameter_groups,
    ledger_array_names,
    linearize_head_constraints,
    load_contracts,
    project_update_nearest,
    resolve_head_updates,
    semantic_ledger_sha256,
)


STATUS = "LF10_CPU_QUALIFICATION_PASS"
LEDGER_SCHEMA = "phk-v23-lf10-materialized-ledger-manifest-v1"
AUDIT_SEEDS = tuple(range(17701, 17715))
INTERFACE_STEPS = 400
PHYSICS_STEPS = 1200

PREFIX_BINDINGS = {
    "DEV_R": (
        "outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/dev_r/checkpoint.pt",
        "7CFDD98E3A03BE29BBE587042967BD44E72D140AE7AC3396CB35E0CF5748F499",
    ),
    "LF8_PREFIX": (
        "outputs/runs/20260908T050343Z-phk-v23-lf8-competence-filter-completion-pilot/p0-fstar/valid-prefix.pt",
        "765BA83BE9E1CB22B7E5B32C61551575D8FBE58EE05AD6BF5EB583AE53A7ABCD",
    ),
    "LF9_ER_S_PREFIX": (
        "outputs/runs/20260908T145333Z-phk-v23-lf9-equation-routed-thermal-cv/gpu/lf9-run-bc3950a/er-s/valid-prefix.pt",
        "C3F993E66D1A2898A31C90C09DA944F3DD6D34C044B0604C7BE147F8FEEE7F6F",
    ),
    "LF9_ER_CV_PREFIX": (
        "outputs/runs/20260908T145333Z-phk-v23-lf9-equation-routed-thermal-cv/gpu/lf9-run-bc3950a/er-cv/valid-prefix.pt",
        "4890CE3B7D9BEE24E990B54C308AF2B98E9B98AC50226BB35FA724D2134DBFB1",
    ),
}


def _bound(path: str, sha256: str, label: str) -> Path:
    candidate = (ROOT / path).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PermissionError(f"LF10 {label} escaped repository") from exc
    if not candidate.is_file() or _sha256_path(candidate) != str(sha256).upper():
        raise ValueError(f"LF10 {label} absent or hash-drifted")
    return candidate


def _rolling(domain: str, hashes: Sequence[str]) -> str:
    digest = hashlib.sha256(domain.encode("ascii"))
    for value in hashes:
        digest.update(bytes.fromhex(str(value)))
    return digest.hexdigest().upper()


def _measure_stream(dataset: Any, *, seeds: Sequence[int], steps: int, domain: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    if len(seeds) != len(CATEGORY_NAMES):
        raise ValueError("LF10 measure seed count drift")
    engines = tuple(torch.quasirandom.SobolEngine(1, scramble=True, seed=int(seed)) for seed in seeds)
    coordinates: list[np.ndarray] = []
    targets: list[np.ndarray] = []
    hashes: list[str] = []
    for step in range(1, int(steps) + 1):
        q: list[torch.Tensor] = []
        y: list[torch.Tensor] = []
        for name, quota, engine in zip(CATEGORY_NAMES, CATEGORY_QUOTAS, engines, strict=True):
            selected_q, selected_y = dataset.category_sample(name, engine.draw(quota, dtype=torch.float64).reshape(-1))
            q.append(selected_q); y.append(selected_y)
        joined_q, joined_y = torch.cat(q), torch.cat(y)
        batch_hash = _batch_sha256(joined_q, joined_y, metadata=f"{domain}:{step}:{dataset.partition_sha256}")
        coordinates.append(joined_q.numpy()); targets.append(joined_y.numpy()); hashes.append(batch_hash)
    return (
        np.ascontiguousarray(np.stack(coordinates), dtype=np.float64),
        np.ascontiguousarray(np.stack(targets), dtype=np.float64),
        np.asarray(hashes, dtype="S64"),
        _rolling(domain, hashes),
    )


def _global_stream(dataset: Any, *, seed: int, steps: int, domain: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    cdf = np.cumsum(dataset.node_weights); cdf[-1] = 1.0
    cdf_tensor = torch.as_tensor(cdf, dtype=torch.float64)
    engine = torch.quasirandom.SobolEngine(1, scramble=True, seed=int(seed))
    coordinates: list[np.ndarray] = []; targets: list[np.ndarray] = []; hashes: list[str] = []
    for step in range(1, int(steps) + 1):
        unit = engine.draw(256, dtype=torch.float64).reshape(-1)
        selected = torch.searchsorted(cdf_tensor, unit, right=True).clamp_max(dataset.node_count - 1).numpy()
        q = torch.as_tensor(dataset.coordinates[selected], dtype=torch.float64)
        y = torch.as_tensor(dataset.targets[selected], dtype=torch.float64)
        digest = _batch_sha256(q, y, metadata=f"{domain}:{step}:{dataset.partition_sha256}")
        coordinates.append(q.numpy()); targets.append(y.numpy()); hashes.append(digest)
    return np.ascontiguousarray(np.stack(coordinates)), np.ascontiguousarray(np.stack(targets)), np.asarray(hashes, dtype="S64"), _rolling(domain, hashes)


def _band_stream(dataset: Any, *, seeds: Sequence[int], steps: int, domain: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    band = InterfaceBandDataset(dataset)
    engines = tuple(torch.quasirandom.SobolEngine(1, scramble=True, seed=int(seed)) for seed in seeds)
    coordinates: list[np.ndarray] = []; targets: list[np.ndarray] = []; hashes: list[str] = []
    for step in range(1, int(steps) + 1):
        q: list[torch.Tensor] = []; y: list[torch.Tensor] = []
        for name, engine in zip(BAND_POOL_NAMES, engines, strict=True):
            one_q, one_y = band.sample(name, engine.draw(64, dtype=torch.float64).reshape(-1))
            q.append(one_q); y.append(one_y)
        joined_q, joined_y = torch.cat(q), torch.cat(y)
        digest = _batch_sha256(joined_q, joined_y, metadata=f"{domain}:{step}:{dataset.partition_sha256}")
        coordinates.append(joined_q.numpy()); targets.append(joined_y.numpy()); hashes.append(digest)
    return np.ascontiguousarray(np.stack(coordinates)), np.ascontiguousarray(np.stack(targets)), np.asarray(hashes, dtype="S64"), _rolling(domain, hashes)


def _physics_stream(model: torch.nn.Module, physics: Any, *, seed: int, steps: int) -> tuple[dict[str, np.ndarray], str]:
    stream = LF0PhysicsBatchStream(
        physics=physics, interior_points=512, boundary_points=128,
        initial_points=128, refresh_updates=250, seed=int(seed),
    )
    values: dict[str, list[Any]] = {name: [] for name in (
        "interior", "left", "right", "bottom", "top", "initial",
        "active_windows", "refreshed", "interior_sha256", "boundary_sha256",
        "initial_sha256", "batch_sha256",
    )}
    for step in range(1, int(steps) + 1):
        batch = stream.draw(model, step, dtype=torch.float64, device=torch.device("cpu"))
        values["interior"].append(batch.interior.numpy())
        for name in ("left", "right", "bottom", "top"):
            values[name].append(batch.boundary[name].numpy())
        values["initial"].append(batch.initial.numpy())
        values["active_windows"].append(batch.active_windows); values["refreshed"].append(batch.refreshed)
        for name in ("interior_sha256", "boundary_sha256", "initial_sha256", "batch_sha256"):
            values[name].append(getattr(batch, name))
    arrays: dict[str, np.ndarray] = {}
    for name in ("interior", "left", "right", "bottom", "top", "initial"):
        arrays[name] = np.ascontiguousarray(np.stack(values[name]), dtype=np.float64)
    arrays["active_windows"] = np.asarray(values["active_windows"], dtype=np.int16)
    arrays["refreshed"] = np.asarray(values["refreshed"], dtype=np.bool_)
    for name in ("interior_sha256", "boundary_sha256", "initial_sha256", "batch_sha256"):
        arrays[name] = np.asarray(values[name], dtype="S64")
    return arrays, stream.rolling_sha256


def _materialize_audit_baselines(
    model: torch.nn.Module,
    dataset: Any,
    physics: Any,
    coordinates: np.ndarray,
    targets: np.ndarray,
    *,
    chunk_steps: int = 64,
) -> np.ndarray:
    """Evaluate exact DEV-R same-batch denominators without 1200 Python forwards."""

    if coordinates.shape[:2] != targets.shape[:2] or coordinates.shape[0] == 0:
        raise ValueError("LF10 audit baseline inputs are malformed")
    model.eval()
    masses = [float(dataset.category_masses[name]) for name in CATEGORY_NAMES]
    scales = torch.tensor(
        [physics.waveform_amplitude, physics.theta_transition, 0.5], dtype=torch.float64
    )
    rows: list[torch.Tensor] = []
    with torch.no_grad():
        for start in range(0, coordinates.shape[0], int(chunk_steps)):
            stop = min(start + int(chunk_steps), coordinates.shape[0])
            count = stop - start
            q = torch.as_tensor(coordinates[start:stop], dtype=torch.float64)
            target = torch.as_tensor(targets[start:stop], dtype=torch.float64)
            prediction = model(q.reshape(-1, q.shape[-1])).reshape(count, q.shape[1], -1)
            squared = ((prediction - target) / scales).square()
            topology_target = (target[..., 2] >= 0.5).to(dtype=torch.float64)
            topology_logits = (prediction[..., 2] - 0.5) / 0.05
            topology_pointwise = torch.nn.functional.binary_cross_entropy_with_logits(
                topology_logits, topology_target, reduction="none"
            )
            components = torch.zeros((count, 3), dtype=torch.float64)
            topology = torch.zeros(count, dtype=torch.float64)
            offset = 0
            for quota, mass in zip(CATEGORY_QUOTAS, masses, strict=True):
                end = offset + int(quota)
                components += mass * squared[:, offset:end].mean(dim=1)
                topology += mass * topology_pointwise[:, offset:end].mean(dim=1)
                offset = end
            if offset != q.shape[1]:
                raise ValueError("LF10 audit baseline category slices drift")
            rows.append(torch.cat((components, topology[:, None]), dim=1))
    result = torch.cat(rows, dim=0).numpy()
    if result.shape != (coordinates.shape[0], 4) or not np.isfinite(result).all() or np.any(result <= 0.0):
        raise FloatingPointError("LF10 audit baseline materialization is invalid")
    return np.ascontiguousarray(result, dtype=np.float64)


def materialize_lf10_arrays(dataset: Any, model: torch.nn.Module, physics: Any, *, audit_steps: int = FULL_ACCEPTED_UPDATES, interface_steps: int = INTERFACE_STEPS, physics_steps: int = PHYSICS_STEPS) -> tuple[dict[str, np.ndarray], dict[str, str]]:
    """Materialise every runtime-random LF10 batch on CPU."""

    arrays: dict[str, np.ndarray] = {}; streams: dict[str, str] = {}
    q, y, h, rolling = _measure_stream(dataset, seeds=AUDIT_SEEDS, steps=audit_steps, domain="PHK_V23_LF10_MEDIUM_AUDIT_GRADIENTS_17")
    audit_baselines = _materialize_audit_baselines(model, dataset, physics, q, y)
    arrays.update(
        audit_coordinates=q,
        audit_targets=y,
        audit_batch_sha256=h,
        audit_baselines=audit_baselines,
    )
    streams["audit_1200_sha256"] = rolling
    for seed in STREAM_SEEDS:
        base_seeds = tuple(seed * 1000 + value for value in range(101, 115))
        q, y, h, rolling = _measure_stream(dataset, seeds=base_seeds, steps=interface_steps, domain=f"PHK_V23_LF10_INTERFACE_{seed}_BASE")
        arrays.update({f"interface_{seed}_base_coordinates": q, f"interface_{seed}_base_targets": y, f"interface_{seed}_base_sha256": h}); streams[f"interface_{seed}_base_400_sha256"] = rolling
        q, y, h, rolling = _global_stream(dataset, seed=seed * 1000 + 401, steps=interface_steps, domain=f"PHK_V23_LF10_INTERFACE_{seed}_GLOBAL")
        arrays.update({f"interface_{seed}_global_coordinates": q, f"interface_{seed}_global_targets": y, f"interface_{seed}_global_sha256": h}); streams[f"interface_{seed}_global_400_sha256"] = rolling
        q, y, h, rolling = _band_stream(dataset, seeds=tuple(seed * 1000 + value for value in range(411, 415)), steps=interface_steps, domain=f"PHK_V23_LF10_INTERFACE_{seed}_BAND")
        arrays.update({f"interface_{seed}_band_coordinates": q, f"interface_{seed}_band_targets": y, f"interface_{seed}_band_sha256": h}); streams[f"interface_{seed}_band_400_sha256"] = rolling
        physics_arrays, rolling = _physics_stream(model, physics, seed=seed, steps=physics_steps)
        arrays.update({f"physics_{seed}_{name}": value for name, value in physics_arrays.items()}); streams[f"physics_{seed}_1200_sha256"] = rolling
    if audit_steps == FULL_ACCEPTED_UPDATES and interface_steps == INTERFACE_STEPS and physics_steps == PHYSICS_STEPS and set(arrays) != set(ledger_array_names()):
        raise AssertionError("LF10 materialized array set drift")
    return arrays, streams


def materialize_ledger(*, output_directory: Path) -> dict[str, Any]:
    contracts = load_contracts(); data = contracts["data"]
    medium = _bound(data["medium"]["path"], data["medium"]["sha256"], "medium")
    dev_r = _bound(data["DEV_R"]["checkpoint_path"], data["DEV_R"]["checkpoint_sha256"], "DEV-R")
    physics, _, _ = load_case_physics("FULL")
    dataset = load_medium_dataset(medium, physics=physics, contracts=contracts)
    if dataset.partition_sha256 != data["medium"]["partition_sha256"]:
        raise ValueError("LF10 medium partition drift")
    model, _, _ = _load_model(dev_r, device=torch.device("cpu"))
    arrays, streams = materialize_lf10_arrays(dataset, model, physics)
    output = Path(output_directory).resolve(); output.mkdir(parents=True, exist_ok=True)
    ledger_path, manifest_path = output / "materialized_lf10_ledger.npz", output / "materialized_lf10_ledger_manifest.json"
    if ledger_path.exists() or manifest_path.exists():
        raise FileExistsError("LF10 materialized ledger already exists")
    np.savez_compressed(ledger_path, **arrays)
    records = {name: {"shape": list(value.shape), "dtype": value.dtype.str, "sha256": array_sha256(name, value)} for name, value in arrays.items()}
    semantic = semantic_ledger_sha256({name: record["sha256"] for name, record in records.items()})
    manifest = {
        "schema_id": LEDGER_SCHEMA, "task_id": TASK_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "ledger": {"path": ledger_path.relative_to(ROOT).as_posix(), "sha256": _sha256_path(ledger_path), "size_bytes": ledger_path.stat().st_size},
        "semantic_sha256": semantic, "arrays": records, "streams": streams,
        "seed_domain_mapping": data["LF10_ledger"]["seed_domain_mapping"], "runtime_sampling_permitted": False,
    }
    _write_json_exclusive(manifest_path, manifest)
    return {"path": ledger_path.relative_to(ROOT).as_posix(), "sha256": _sha256_path(ledger_path), "size_bytes": ledger_path.stat().st_size, "manifest_path": manifest_path.relative_to(ROOT).as_posix(), "manifest_sha256": _sha256_path(manifest_path), "semantic_sha256": semantic, "streams": streams, "arrays": records}


def _strong_batch(path: Path, *, step: int = 1) -> PhysicsBatch:
    index = int(step) - 1
    with np.load(path, allow_pickle=False) as archive:
        tensor = lambda name: torch.as_tensor(np.asarray(archive[name][index]), dtype=torch.float64)
        decode = lambda name: bytes(archive[name][index]).decode("ascii")
        return PhysicsBatch(
            interior=tensor("p0_interior"),
            boundary={name: tensor(f"p0_{name}") for name in ("left", "right", "bottom", "top")},
            initial=tensor("p0_initial"), active_windows=int(archive["p0_active_windows"][index]), refreshed=bool(archive["p0_refreshed"][index]),
            interior_sha256=decode("p0_interior_sha256"), boundary_sha256=decode("p0_boundary_sha256"), initial_sha256=decode("p0_initial_sha256"), batch_sha256=decode("p0_batch_sha256"),
        )


def _cosine(left: torch.Tensor, right: torch.Tensor) -> float | None:
    denominator = float(torch.linalg.vector_norm(left) * torch.linalg.vector_norm(right))
    return float(torch.dot(left, right) / denominator) if denominator > 0.0 else None


def _load_qualified_prefix(path: Path, *, device: torch.device) -> tuple[torch.nn.Module, Mapping[str, Any], Mapping[str, Any]]:
    """Load standard or LF8/LF9 recovery-prefix checkpoints on the DEV-R architecture."""

    payload = torch.load(path, map_location="cpu", weights_only=False)
    schema = str(payload.get("schema_id", ""))
    if schema.startswith("phk-v22r-checkpoint-"):
        return _load_model(path, device=device)

    dev_r_path, dev_r_sha256 = PREFIX_BINDINGS["DEV_R"]
    model, config, _ = _load_model(
        _bound(dev_r_path, dev_r_sha256, "DEV-R architecture source"),
        device=device,
    )
    if schema == "phk-v23-lf8-valid-prefix-recovery-v1":
        state = payload.get("training_snapshot", {}).get("model_state_dict")
    elif schema == "phk-v23-lf9-valid-prefix-v1":
        snapshot = payload.get("snapshot")
        state = getattr(snapshot, "model_state", None)
        if state is None and isinstance(snapshot, Mapping):
            state = snapshot.get("model_state")
    else:
        raise ValueError(f"unsupported LF10 prefix checkpoint schema: {schema}")
    if not isinstance(state, Mapping):
        raise ValueError(f"LF10 prefix checkpoint lacks model state: {schema}")
    model.load_state_dict(state, strict=True)
    model.train()
    return model, config, payload


def _geometry_at_checkpoint(path: Path, *, audit_batch: MeasureBatch, audit_baselines: Mapping[str, float], strong_batch: PhysicsBatch) -> dict[str, Any]:
    device = torch.device("cpu")
    model, config, _ = _load_qualified_prefix(path, device=device)
    for parameter in model.encoders["phase"].parameters(): parameter.requires_grad_(False)
    for parameter in model.heads["phase"].parameters(): parameter.requires_grad_(False)
    groups = field_parameter_groups(model)
    optimizer = torch.optim.Adam(tuple(p for values in groups.values() for p in values), lr=LR_LADDER[0], betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0, amsgrad=False)
    physics_loss, physics_components = _physics_objective(model, strong_batch, config)
    proposal = extract_adam_proposed_update(model, optimizer, physics_loss, parameter_groups=groups, max_grad_norm=10.0)
    objectives = audit_preservation_objectives(model, audit_batch, physics=model.physics, device=device)
    constraints, current = linearize_head_constraints(objectives, audit_baselines, PROJECTION_BOUNDS, groups, remaining_steps=BLOCK_SIZE)
    projected_decision = resolve_head_updates(PROJ, proposal.updates, constraints)
    projected = projected_decision.projections
    geometry = direction_geometry(proposal.updates, constraints, projected)
    physics_loss_again, _ = _physics_objective(model, strong_batch, config)
    trainable = tuple(p for values in groups.values() for p in values)
    gradients = torch.autograd.grad(physics_loss_again, trainable, create_graph=False, allow_unused=True)
    by_parameter = {id(p): (torch.zeros_like(p) if g is None else g.detach()) for p, g in zip(trainable, gradients, strict=True)}
    for head, parameters in groups.items():
        if not parameters:
            geometry.setdefault(head, {})["physics_gradient_norm"] = 0.0
            geometry[head]["physics_constraint_cosine"] = {}
            geometry[head]["constraint_rhs"] = {}
            continue
        gphysics = torch.cat([by_parameter[id(parameter)].reshape(-1) for parameter in parameters])
        geometry.setdefault(head, {})["physics_gradient_norm"] = float(torch.linalg.vector_norm(gphysics))
        geometry[head]["physics_constraint_cosine"] = {constraint.name: _cosine(gphysics, constraint.row) for constraint in constraints.get(head, ())}
        geometry[head]["constraint_rhs"] = {constraint.name: constraint.rhs for constraint in constraints.get(head, ())}
    return {
        "physics_components": physics_components,
        "current_ratios": current,
        "zero_update_feasible": all(constraint.rhs >= -1e-12 for values in constraints.values() for constraint in values),
        "projected_feasible": projected_decision.feasible,
        "geometry": geometry,
    }


def _analytic_qp_check() -> dict[str, Any]:
    proposed = torch.tensor([2.0, 2.0], dtype=torch.float64)
    constraints = (
        LinearConstraint("x", torch.tensor([1.0, 0.0], dtype=torch.float64), 0.5, 1.0, 1.2, 1),
        LinearConstraint("y", torch.tensor([0.0, 1.0], dtype=torch.float64), 0.25, 1.0, 1.2, 1),
    )
    result = project_update_nearest(proposed, constraints)
    expected = torch.tensor([0.5, 0.25], dtype=torch.float64)
    return {
        "zero_update_feasible": all(constraint.rhs >= 0.0 for constraint in constraints),
        "projection_feasible": result.feasible,
        "expected_projection": expected.tolist(),
        "actual_projection": result.update.tolist(),
        "matches_expected": bool(torch.allclose(result.update, expected, atol=1e-12, rtol=0.0)),
    }


def _validate_materialized_ledger(ledger_path: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest.get("schema_id") != LEDGER_SCHEMA or manifest.get("task_id") != TASK_ID:
        raise ValueError("LF10 ledger manifest identity drift")
    if not Path(ledger_path).is_file() or _sha256_path(ledger_path) != manifest.get("ledger", {}).get("sha256"):
        raise ValueError("LF10 ledger byte identity drift")
    with np.load(ledger_path, allow_pickle=False) as archive:
        if set(archive.files) != set(ledger_array_names()):
            raise ValueError("LF10 ledger array set drift")
        hashes = {name: array_sha256(name, np.asarray(archive[name])) for name in archive.files}
        if any(hashes[name] != manifest["arrays"][name]["sha256"] for name in archive.files):
            raise ValueError("LF10 ledger array hash drift")
    semantic = semantic_ledger_sha256(hashes)
    if semantic != manifest.get("semantic_sha256"):
        raise ValueError("LF10 ledger semantic drift")
    return {"path": Path(ledger_path).relative_to(ROOT).as_posix(), "sha256": _sha256_path(ledger_path), "size_bytes": Path(ledger_path).stat().st_size, "manifest_path": Path(manifest_path).relative_to(ROOT).as_posix(), "manifest_sha256": _sha256_path(manifest_path), "semantic_sha256": semantic, "streams": manifest["streams"], "arrays": manifest["arrays"]}


def compute_cpu_payload(*, ledger_path: Path, ledger_manifest_path: Path) -> dict[str, Any]:
    contracts = load_contracts(); data = contracts["data"]
    medium = _bound(data["medium"]["path"], data["medium"]["sha256"], "medium")
    lf3 = _bound(data["LF3_T0"]["checkpoint_path"], data["LF3_T0"]["checkpoint_sha256"], "LF3-T0")
    dev_r = _bound(data["DEV_R"]["checkpoint_path"], data["DEV_R"]["checkpoint_sha256"], "DEV-R")
    strong = _bound(data["strong_ledger"]["path"], data["strong_ledger"]["file_sha256"], "strong ledger")
    strong_manifest = strong.with_name("materialized_ledger_manifest.json")
    if _sha256_path(strong_manifest) != data["strong_ledger"]["manifest_sha256"]:
        raise ValueError("LF10 inherited strong ledger manifest drift")
    prefixes = {role: _bound(path, sha, role) for role, (path, sha) in PREFIX_BINDINGS.items()}
    ledger = _validate_materialized_ledger(Path(ledger_path).resolve(), Path(ledger_manifest_path).resolve())
    physics, _, _ = load_case_physics("FULL")
    dataset = load_medium_dataset(medium, physics=physics, contracts=contracts)
    if dataset.partition_sha256 != data["medium"]["partition_sha256"]:
        raise ValueError("LF10 partition drift")
    qledger = MaterializedLF10Ledger(ledger_path, ledger_manifest_path, qualification={"ledger": ledger})
    audit_batch = qledger.audit_batch(1, dataset)
    fixed = _strong_batch(strong, step=1)
    geometries: dict[str, Any] = {}
    same_batch_baselines = qledger.audit_baselines(1)
    for role, path in prefixes.items():
        geometries[role] = _geometry_at_checkpoint(path, audit_batch=audit_batch, audit_baselines=same_batch_baselines, strong_batch=fixed)
    dev_r_model, _, _ = _load_qualified_prefix(prefixes["DEV_R"], device=torch.device("cpu"))
    dev_r_audit = full_medium_audit(dev_r_model, dataset, device=torch.device("cpu"))
    analytic_qp = _analytic_qp_check()
    checks = {
        "input_hashes": True,
        "partition": dataset.partition_sha256 == data["medium"]["partition_sha256"],
        "ledger_arrays_and_hashes": True,
        "audit_stream_1200": len(qledger.arrays["audit_batch_sha256"]) == FULL_ACCEPTED_UPDATES,
        "interface_streams_23_29": all(qledger.arrays[f"interface_{seed}_base_coordinates"].shape[0] == INTERFACE_STEPS for seed in STREAM_SEEDS),
        "physics_streams_23_29": all(qledger.arrays[f"physics_{seed}_batch_sha256"].shape[0] == PHYSICS_STEPS for seed in STREAM_SEEDS),
        "actual_direction_geometry_recorded": all(math.isfinite(float(record["physics_components"]["physics_total"])) for record in geometries.values()),
        "dev_r_same_batch_zero_update_feasible": geometries["DEV_R"]["zero_update_feasible"],
        "analytic_qp_zero_update_feasible": analytic_qp["zero_update_feasible"],
        "analytic_qp_projection_correct": analytic_qp["projection_feasible"] and analytic_qp["matches_expected"],
        "scientific_optimizer_updates_zero": True,
        "fine_extra_direct_stress_unread": True,
    }
    gate = STATUS if all(checks.values()) else "LF10_INPUT_OR_ENGINEERING_BLOCKED"
    return {
        "schema_id": "phk-v23-lf10-cpu-qualification-v1", "task_id": TASK_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "gate_outcome": gate, "status": gate,
        "scientific_optimizer_updates": 0, "gpu_used": False, "gpu_execution_authorized_by_cpu_gate": gate == STATUS,
        "checks": checks, "contracts": contract_identity(), "partition_sha256": dataset.partition_sha256,
        "ledger": ledger,
        "strong_ledger": {"path": strong.relative_to(ROOT).as_posix(), "sha256": _sha256_path(strong), "manifest_path": strong_manifest.relative_to(ROOT).as_posix(), "manifest_sha256": _sha256_path(strong_manifest), "semantic_sha256": data["strong_ledger"]["semantic_sha256"], "physics_1200_sha256": data["strong_ledger"]["physics_1200_sha256"], "fixed_blind_pool_sha256": data["strong_ledger"]["fixed_blind_pool_sha256"]},
        "audit_baselines": {"semantics": "EXACT_DEV_R_SAME_PREMATERIALIZED_AUDIT_BATCH", "columns": ["CV", "CT", "Cphase", "Ctopology_smooth_surrogate"]},
        "dev_r_full_medium_audit": dev_r_audit,
        "gradient_geometry": geometries, "analytic_qp": analytic_qp,
        "input_bindings": {"medium": {"path": str(medium), "sha256": _sha256_path(medium)}, "lf3_t0": {"path": str(lf3), "sha256": _sha256_path(lf3)}, "dev_r": {"path": str(dev_r), "sha256": _sha256_path(dev_r)}, **{role.lower(): {"path": str(path), "sha256": _sha256_path(path)} for role, path in prefixes.items()}},
        "reference_boundary": {"fine_read": False, "extra_fine_read": False, "direct_LF_ONLY_read": False, "frozen_evaluator_read": False, "stress_read": False},
    }


def build_cpu_manifest(payload: Mapping[str, Any], *, artifact_path: Path, raw_report: Path) -> dict[str, Any]:
    manifest = {
        "schema_version": "run-manifest-v1", "run_id": Path(artifact_path).stem,
        "experiment_group_id": "PHK_V23_LF10", "tier": "qualification",
        "scientific_role": "cpu_only_gradient_geometry_and_materialized_audit_replication_stream_qualification",
        "gate": "PHK_V23_LF10_CPU", "started_at": payload["created_at_utc"], "ended_at": payload["created_at_utc"],
        "command": [".venv/Scripts/python.exe", "-m", "pinn_pcm_sci.phk_v23_lf10_qualification"],
        "execution_status": "COMPLETE", "numerical_validity": "VALID_CPU_FP64_ZERO_SCIENTIFIC_UPDATE_HASH_BOUND_GEOMETRY_AND_STREAMS",
        "gate_outcome": payload["gate_outcome"], "route_disposition": "RUN_ALL_NONSHARED_LF10_TRACKS",
        "evidence_identity": "ENGINEERING_AND_GEOMETRY_QUALIFICATION_ONLY", "seed": 17,
        "claim_status": "LF10_STREAMS_AND_FEASIBLE_DIRECTION_IMPLEMENTATION_QUALIFIED_GPU_RESULTS_UNTESTED",
        "code_identity": {"base_commit": "06d1d2121c8d0fd6db13c12356568650083be4f3", "workspace_scope": "LF10_EXACT_ALLOWLIST_UNRELATED_DIRTY_PRESERVED"},
        "environment": {"device": "CPU", "dtype": "FLOAT64", "cloud_connection_opened": False, "stress_status": "TWO_STRESS_REFERENCES_SEALED_UNREAD"},
        "physical_contract_id": "PHK_V21_FIXED_DISCRETIZATION_FULL_NOMINAL", "split_id": "MEDIUM_AUDIT_AND_REPLICATION_STREAMS_FINE_EXTRA_DIRECT_LOCAL_POST_SHUTDOWN_STRESS_SEALED",
        "method_id": "phk-v23-lf10-event-competence-feasible-direction-v1", "case_id": "PHK_V21_NOMINAL_LF10_QUALIFICATION",
        "planned_budget": {"gpu_trajectories": 0, "optimizer_updates": 0}, "actual_budget": {"gpu_trajectories": 0, "optimizer_updates": 0, "gpu_used": False},
        "checkpoint": {"DEV_R_source_sha256": payload["input_bindings"]["dev_r"]["sha256"], "loaded_read_only": True},
        "evaluator_id": "NOT_READ_DURING_LF10_CPU_QUALIFICATION",
        "artifacts": {"compact_qualification": f"artifacts/{Path(artifact_path).name}#sha256={_sha256_path(Path(artifact_path))}", "raw_report": f"{raw_report.relative_to(ROOT).as_posix()}#sha256={_sha256_path(raw_report)}", "materialized_ledger": f"{payload['ledger']['path']}#sha256={payload['ledger']['sha256']}"},
        "failure_class": None, "replay_of": None, "supersedes": None,
    }
    return RunManifest(**manifest).to_dict()


def qualify_cpu(*, artifact_path: Path, manifest_path: Path, raw_output_directory: Path) -> dict[str, Any]:
    raw = Path(raw_output_directory).resolve(); raw.mkdir(parents=True, exist_ok=True)
    ledger_path, ledger_manifest = raw / "materialized_lf10_ledger.npz", raw / "materialized_lf10_ledger_manifest.json"
    if not ledger_path.exists() and not ledger_manifest.exists():
        materialize_ledger(output_directory=raw)
    payload = compute_cpu_payload(ledger_path=ledger_path, ledger_manifest_path=ledger_manifest)
    if payload["gate_outcome"] != STATUS:
        failed = sorted(name for name, passed in payload.get("checks", {}).items() if not passed)
        raise RuntimeError(f"{payload['gate_outcome']}: failed_checks={failed}")
    raw_report = raw / "qualification.json"
    _write_json_exclusive(raw_report, payload); _write_json_exclusive(Path(artifact_path), payload)
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
    print(json.dumps({"gate_outcome": payload["gate_outcome"], "ledger_sha256": payload["ledger"]["sha256"], "gradient_roles": sorted(payload["gradient_geometry"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["AUDIT_SEEDS", "LEDGER_SCHEMA", "STATUS", "build_cpu_manifest", "compute_cpu_payload", "materialize_ledger", "materialize_lf10_arrays", "qualify_cpu"]
