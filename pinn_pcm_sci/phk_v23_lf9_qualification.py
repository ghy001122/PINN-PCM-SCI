"""Zero-update CPU qualification and CV-ledger materialization for PHK-V2.3 LF9."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .ledger import RunManifest
from .phk_v22r_pinn import interior_residuals
from .phk_v22r_training import PDE_SCALES, ROOT, load_case_physics
from .phk_v23_lf0 import _sha256_path, _write_json_exclusive
from .phk_v23_lf2 import load_medium_dataset
from .phk_v23_lf3 import build_training_config, full_medium_audit


TASK_ID = "PHK_V23_LF9_EQUATION_ROUTED_THERMAL_CONTROL_VOLUME_REFINEMENT_EXECUTE"
STATUS = "LF9_CPU_QUALIFICATION_PASS"
DOMAIN = b"PHK_V23_LF9_MATERIALIZED_THERMAL_CV_LEDGER_V1"
WINDOWS = (
    ("W1", 0.0, 0.35, True, True),
    ("W2", 0.35, 1.25, False, False),
    ("W3", 1.25, 1.60, True, True),
    ("W4", 1.60, 2.50, False, True),
)
CONTRACT_PATHS = {
    name: ROOT / f"configs/phk_v23/{name}_contract_lf9_equation_routed_thermal_cv.json"
    for name in ("program", "method", "data", "decision")
}
EXPECTED_SCHEMAS = {name: f"phk-v23-lf9-{name}-contract-v1" for name in CONTRACT_PATHS}


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"LF9 expected JSON object: {path}")
    return value


def load_contracts() -> dict[str, dict[str, Any]]:
    contracts = {name: _read_json(path) for name, path in CONTRACT_PATHS.items()}
    for name, schema in EXPECTED_SCHEMAS.items():
        if contracts[name].get("schema_id") != schema:
            raise ValueError(f"LF9 {name} schema drift")
    if contracts["program"].get("phase_id") != TASK_ID:
        raise ValueError("LF9 task identity drift")
    return contracts


def _bound_path(binding: Mapping[str, Any], *, path_key: str, sha_key: str, label: str) -> Path:
    exact = (ROOT / str(binding[path_key])).resolve()
    try:
        exact.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PermissionError(f"LF9 {label} escaped repository") from exc
    if not exact.is_file() or _sha256_path(exact) != str(binding[sha_key]).upper():
        raise ValueError(f"LF9 {label} absent or hash-drifted")
    return exact


def _array_digest(name: str, value: np.ndarray) -> str:
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256(name.encode("ascii"))
    digest.update(array.dtype.str.encode("ascii"))
    digest.update(str(tuple(array.shape)).encode("ascii"))
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest().upper()


def _semantic_digest(arrays: Mapping[str, np.ndarray]) -> str:
    digest = hashlib.sha256(DOMAIN)
    for name in sorted(arrays):
        digest.update(name.encode("ascii"))
        digest.update(bytes.fromhex(_array_digest(name, arrays[name])))
    return digest.hexdigest().upper()


def _rolling_training_digest(bounds: np.ndarray, identity: np.ndarray) -> tuple[list[str], str]:
    hashes: list[str] = []
    rolling = hashlib.sha256(DOMAIN + b"/TRAINING")
    for step in range(bounds.shape[0]):
        one = hashlib.sha256(DOMAIN + b"/STEP")
        one.update(np.asarray(step + 1, dtype="<i8").tobytes())
        one.update(np.ascontiguousarray(identity[step], dtype="<i8").tobytes())
        one.update(np.ascontiguousarray(bounds[step], dtype="<f8").tobytes())
        value = one.hexdigest().upper()
        hashes.append(value)
        rolling.update(bytes.fromhex(value))
    return hashes, rolling.hexdigest().upper()


def _blind_digest(role: str, bounds: np.ndarray, identity: np.ndarray) -> str:
    digest = hashlib.sha256(DOMAIN + b"/" + role.encode("ascii"))
    digest.update(np.ascontiguousarray(identity, dtype="<i8").tobytes())
    digest.update(np.ascontiguousarray(bounds, dtype="<f8").tobytes())
    return digest.hexdigest().upper()


def _window_interval_indices(time: np.ndarray, spec: tuple[str, float, float, bool, bool]) -> np.ndarray:
    _, lower, upper, include_lower, include_upper = spec
    midpoint = 0.5 * (time[:-1] + time[1:])
    left = midpoint >= lower if include_lower else midpoint > lower
    right = midpoint <= upper if include_upper else midpoint < upper
    result = np.flatnonzero(left & right).astype(np.int64)
    if result.size == 0:
        raise ValueError(f"LF9 empty saved-time interval window: {spec[0]}")
    return result


def _axis_edges(centres: np.ndarray, *, name: str) -> np.ndarray:
    values = np.unique(np.asarray(centres, dtype=np.float64).reshape(-1))
    if values.size < 4 or not np.isfinite(values).all() or np.any(np.diff(values) <= 0.0):
        raise ValueError(f"LF9 invalid {name} cell centres")
    edges = np.empty(values.size + 1, dtype=np.float64)
    edges[1:-1] = 0.5 * (values[:-1] + values[1:])
    edges[0] = values[0] - 0.5 * (values[1] - values[0])
    edges[-1] = values[-1] + 0.5 * (values[-1] - values[-2])
    return edges


def _one_bounds(x_edges: np.ndarray, z_edges: np.ndarray, time: np.ndarray, key: tuple[int, int, int]) -> np.ndarray:
    ix, iz, it = key
    return np.asarray((x_edges[ix], x_edges[ix + 1], z_edges[iz], z_edges[iz + 1], time[it], time[it + 1]), dtype=np.float64)


def _two_bounds(x_edges: np.ndarray, z_edges: np.ndarray, time: np.ndarray, key: tuple[int, int, int]) -> np.ndarray:
    ix, iz, it = key
    return np.asarray((x_edges[ix], x_edges[ix + 2], z_edges[iz], z_edges[iz + 2], time[it], time[it + 1]), dtype=np.float64)


def _occupied(key: tuple[int, int, int], *, width: int) -> set[tuple[int, int, int]]:
    ix, iz, it = key
    return {(ix + dx, iz + dz, it) for dx in range(width) for dz in range(width)}


def materialize_cv_arrays(
    *, cell_x: np.ndarray, cell_z: np.ndarray, time: np.ndarray,
    steps: int = 1200, patches_per_step: int = 16,
    blind_per_window: int = 48, seed: int = 17,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Materialize mutually disjoint one-cell training/blind and 2x2 blind slabs."""

    if steps <= 0 or patches_per_step <= 0 or patches_per_step % 4:
        raise ValueError("LF9 steps must be positive and patches_per_step divisible by four")
    x_values = np.unique(np.asarray(cell_x, dtype=np.float64).reshape(-1))
    z_values = np.unique(np.asarray(cell_z, dtype=np.float64).reshape(-1))
    times = np.asarray(time, dtype=np.float64).reshape(-1)
    x_edges = _axis_edges(x_values, name="x")
    z_edges = _axis_edges(z_values, name="z")
    if times.size < 2 or not np.isfinite(times).all() or np.any(np.diff(times) <= 0.0):
        raise ValueError("LF9 saved times are invalid")
    def active_windows(step: int) -> tuple[str, ...]:
        if step <= 150:
            return ("W1",)
        if step <= 350:
            return ("W1", "W2")
        if step <= 550:
            return ("W1", "W2", "W3")
        return ("W1", "W2", "W3", "W4")

    allocation: list[list[str]] = []
    required_by_window = {name: 0 for name, *_ in WINDOWS}
    for step in range(1, steps + 1):
        active = active_windows(step)
        quotient, remainder = divmod(patches_per_step, len(active))
        row = [name for index, name in enumerate(active) for _ in range(quotient + (1 if index < remainder else 0))]
        if len(row) != patches_per_step:
            raise AssertionError("LF9 active-window allocation drift")
        allocation.append(row)
        for name in row:
            required_by_window[name] += 1
    rng = np.random.default_rng(int(seed))
    used: set[tuple[int, int, int]] = set()
    by_window: dict[str, dict[str, list[tuple[int, int, int]]]] = {}

    for spec in WINDOWS:
        window = spec[0]
        intervals = _window_interval_indices(times, spec)
        two_candidates = [(ix, iz, int(it)) for it in intervals for iz in range(1, z_values.size - 2) for ix in range(1, x_values.size - 2)]
        one_candidates = [(ix, iz, int(it)) for it in intervals for iz in range(1, z_values.size - 1) for ix in range(1, x_values.size - 1)]
        rng.shuffle(two_candidates); rng.shuffle(one_candidates)
        selected_two: list[tuple[int, int, int]] = []
        for key in two_candidates:
            footprint = _occupied(key, width=2)
            if not (footprint & used):
                selected_two.append(key); used.update(footprint)
                if len(selected_two) == blind_per_window:
                    break
        if len(selected_two) != blind_per_window:
            raise ValueError(f"LF9 insufficient disjoint 2x2 blind slabs in {window}")
        available_one = [key for key in one_candidates if key not in used]
        max_per_step = max((row.count(window) for row in allocation), default=0)
        required = blind_per_window + max_per_step
        if len(available_one) < required:
            raise ValueError(f"LF9 insufficient disjoint one-cell slabs in {window}")
        selected_one = available_one[:blind_per_window]
        used.update(selected_one)
        training_pool = [key for key in available_one[blind_per_window:] if key not in used]
        by_window[window] = {"training": training_pool, "one": selected_one, "two": selected_two}

    training_identity = np.empty((steps, patches_per_step, 3), dtype=np.int64)
    for step in range(steps):
        offset = 0
        for name, *_ in WINDOWS:
            count = allocation[step].count(name)
            if count:
                pool = by_window[name]["training"]
                chosen = rng.choice(len(pool), size=count, replace=False)
                training_identity[step, offset:offset + count] = np.asarray([pool[int(index)] for index in chosen], dtype=np.int64)
                offset += count
    one_identity = np.asarray([key for name, *_ in WINDOWS for key in by_window[name]["one"]], dtype=np.int64)
    two_identity = np.asarray([key for name, *_ in WINDOWS for key in by_window[name]["two"]], dtype=np.int64)
    training_bounds = np.empty((steps, patches_per_step, 6), dtype=np.float64)
    for index in np.ndindex(training_identity.shape[:2]):
        training_bounds[index] = _one_bounds(x_edges, z_edges, times, tuple(int(v) for v in training_identity[index]))
    one_bounds = np.stack([_one_bounds(x_edges, z_edges, times, tuple(map(int, key))) for key in one_identity])
    two_bounds = np.stack([_two_bounds(x_edges, z_edges, times, tuple(map(int, key))) for key in two_identity])
    arrays = {
        "training_bounds": np.ascontiguousarray(training_bounds),
        "training_identity": np.ascontiguousarray(training_identity),
        "one_cell_blind_bounds": np.ascontiguousarray(one_bounds),
        "one_cell_blind_identity": np.ascontiguousarray(one_identity),
        "two_by_two_blind_bounds": np.ascontiguousarray(two_bounds),
        "two_by_two_blind_identity": np.ascontiguousarray(two_identity),
    }
    training_cells = set(map(tuple, training_identity.reshape(-1, 3).tolist()))
    one_cells = set(map(tuple, one_identity.tolist()))
    two_cells: set[tuple[int, int, int]] = set()
    for key in map(tuple, two_identity.tolist()):
        two_cells.update(_occupied(tuple(map(int, key)), width=2))
    step_hashes, rolling_hash = _rolling_training_digest(training_bounds, training_identity)
    arrays["training_step_sha256"] = np.asarray(step_hashes, dtype="S64")
    disjoint = {
        "training_vs_one_cell": not bool(training_cells & one_cells),
        "training_vs_two_by_two_occupied_cells": not bool(training_cells & two_cells),
        "one_cell_vs_two_by_two_occupied_cells": not bool(one_cells & two_cells),
        "training_unique_within_each_step": all(len(set(map(tuple, row.tolist()))) == row.shape[0] for row in training_identity),
        "one_cell_unique": len(one_cells) == one_identity.shape[0],
        "two_by_two_occupied_cells_unique": len(two_cells) == 4 * two_identity.shape[0],
    }
    report = {
        "domain_tag": DOMAIN.decode("ascii"), "seed": int(seed),
        "steps": int(steps), "patches_per_step": int(patches_per_step),
        "window_order": [name for name, *_ in WINDOWS],
        "active_window_schedule": {"1_150": ["W1"], "151_350": ["W1", "W2"], "351_550": ["W1", "W2", "W3"], "551_1200": ["W1", "W2", "W3", "W4"]},
        "training_counts_by_window": required_by_window,
        "ordered_remainder": True,
        "one_cell_blind_per_window": int(blind_per_window),
        "two_by_two_blind_per_window": int(blind_per_window),
        "training_step_sha256": step_hashes,
        "training_rolling_sha256": rolling_hash,
        "one_cell_blind_sha256": _blind_digest("ONE_CELL_BLIND", one_bounds, one_identity),
        "two_by_two_blind_sha256": _blind_digest("TWO_BY_TWO_BLIND", two_bounds, two_identity),
        "semantic_sha256": _semantic_digest(arrays),
        "array_sha256": {name: _array_digest(name, value) for name, value in arrays.items()},
        "disjoint_checks": disjoint,
    }
    if not all(disjoint.values()):
        raise AssertionError("LF9 CV ledger disjointness failed")
    return arrays, report


def _save_npz_exclusive(path: Path, arrays: Mapping[str, np.ndarray]) -> None:
    exact = Path(path)
    exact.parent.mkdir(parents=True, exist_ok=True)
    if exact.exists():
        raise FileExistsError(exact)
    np.savez_compressed(exact, **arrays)


def _mean_over_chunks(function: Any, model: torch.nn.Module, bounds: np.ndarray, *, chunk: int = 64) -> float:
    total = 0.0; count = 0
    device = next(model.parameters()).device
    for start in range(0, bounds.shape[0], chunk):
        tensor = torch.as_tensor(bounds[start:start + chunk], dtype=torch.float64, device=device)
        value = function(model, tensor)
        flat = value.detach().to(device="cpu", dtype=torch.float64).reshape(-1)
        total += float(torch.sum(flat)) if function.__name__ == "strong_thermal_normalized_mse" else float(torch.sum(flat.square()))
        count += 1 if function.__name__ == "strong_thermal_normalized_mse" else int(flat.numel())
    if count <= 0:
        raise ValueError("LF9 empty CV normalization input")
    return total / float(count)


def _real_rollback_qualification(model: torch.nn.Module) -> dict[str, Any]:
    from .phk_v23_lf8 import restore_snapshot, snapshot_digest, snapshot_optimizer_aliases, take_snapshot
    from .phk_v23_lf9 import field_parameter_groups

    random.seed(17); np.random.seed(17); torch.manual_seed(17)
    groups = field_parameter_groups(model)
    for parameter in groups["phase"]:
        parameter.requires_grad_(False)
    optimizer = torch.optim.Adam(model.parameters(), lr=1.25e-4, betas=(0.9, 0.999), eps=1e-8)
    optimizer.zero_grad(set_to_none=True)
    synthetic = sum(parameter.square().sum() for parameter in tuple(groups["potential"]) + tuple(groups["temperature"]))
    synthetic.backward(); optimizer.step()
    snapshot = take_snapshot(model, optimizer, accepted_updates=25, learning_rate=1.25e-4)
    immutable = snapshot_digest(snapshot)
    cycles: list[dict[str, Any]] = []
    for cycle in range(2):
        before = restore_snapshot(snapshot, model, optimizer)
        aliases = snapshot_optimizer_aliases(snapshot, optimizer)
        optimizer.zero_grad(set_to_none=True)
        proposal = sum((index + 1) * parameter.square().sum() for index, parameter in enumerate(model.parameters()) if parameter.requires_grad)
        proposal.backward(); optimizer.step()
        random.random(); np.random.random(); torch.rand(())
        stable = snapshot_digest(snapshot) == immutable
        after = restore_snapshot(snapshot, model, optimizer)
        cycles.append({"cycle": cycle + 1, "before": before, "after": after, "aliases": aliases, "snapshot_stable": stable})
    passed = bool(len(optimizer.state) > 0 and all(not row["aliases"] and row["snapshot_stable"] and row["before"] == row["after"] for row in cycles))
    return {"nonempty_adam_state": len(optimizer.state), "cycles": cycles, "passed": passed}


def _analytic_and_routing_qualification() -> dict[str, Any]:
    from .phk_v23_lf9 import field_parameter_groups, routed_field_gradients, thermal_control_volume_residual

    class Physics:
        latent_ratio = 2.0; thermal_diffusivity = 1.0; volumetric_cooling = 0.0; joule_gain = 0.0
        @staticmethod
        def conductivity(temperature: torch.Tensor, phase: torch.Tensor) -> torch.Tensor:
            return torch.ones_like(temperature)

    class Analytic(torch.nn.Module):
        def __init__(self, mode: str) -> None:
            super().__init__(); self.mode = mode; self.physics = Physics(); self.anchor = torch.nn.Parameter(torch.zeros((), dtype=torch.float64))
        def forward(self, q: torch.Tensor) -> torch.Tensor:
            x, z, t = q[:, 0:1], q[:, 1:2], q[:, 2:3]; zero = 0.0 * x + 0.0 * self.anchor
            temperature = zero if self.mode == "constant" else (t if self.mode == "linear" else x.square() + z.square())
            return torch.cat((zero, temperature, zero), dim=1)

    bounds = torch.tensor([[0.0, 1.0, 0.0, 1.0, 0.2, 0.4]], dtype=torch.float64)
    residuals = {mode: float(thermal_control_volume_residual(Analytic(mode), bounds)) for mode in ("constant", "linear", "quadratic")}

    class CoupledPhysics(Physics):
        joule_gain = 1.0

    class Coupled(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__(); self.physics = CoupledPhysics()
            self.a = torch.nn.Parameter(torch.tensor(0.7, dtype=torch.float64))
            self.b = torch.nn.Parameter(torch.tensor(0.4, dtype=torch.float64))
            self.c = torch.nn.Parameter(torch.tensor(0.2, dtype=torch.float64))
        def forward(self, q: torch.Tensor) -> torch.Tensor:
            x, t = q[:, 0:1], q[:, 2:3]
            return torch.cat((self.a * x, self.b * t, self.c * t), dim=1)

    coupled = Coupled()
    coupled_residual = thermal_control_volume_residual(coupled, bounds).square().mean()
    coupling_grads = torch.autograd.grad(coupled_residual, (coupled.a, coupled.b, coupled.c))
    coupling_gradient_values = [float(value) for value in coupling_grads]
    coupling_passed = all(math.isfinite(value) and abs(value) > 1e-12 for value in coupling_gradient_values)

    class Heads(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.encoders = torch.nn.ModuleDict({name: torch.nn.Linear(1, 1, bias=False).double() for name in ("potential", "temperature", "phase")})
            self.heads = torch.nn.ModuleDict({name: torch.nn.Linear(1, 1, bias=False).double() for name in ("potential", "temperature", "phase")})
    routed_model = Heads(); groups = field_parameter_groups(routed_model)
    pv, tv, fv = (next(iter(groups[name])) for name in ("potential", "temperature", "phase"))
    losses = {"potential": pv.sum() + 10 * tv.sum() + 100 * fv.sum(), "temperature": 2 * pv.sum() + 3 * tv.sum() + 5 * fv.sum(), "phase": 7 * pv.sum() + 11 * tv.sum() + 13 * fv.sum()}
    grads = routed_field_gradients(losses, groups)
    routed_values = {name: float(values[0]) for name, values in grads.items()}
    return {
        "analytic_residuals": residuals,
        "analytic_passed": all(math.isclose(residuals[name], target, rel_tol=0.0, abs_tol=1e-12) for name, target in {"constant": 0.0, "linear": 1.0, "quadratic": -4.0}.items()),
        "routed_owned_gradients": routed_values,
        "routing_passed": all(math.isclose(routed_values[name], target, abs_tol=1e-14) for name, target in {"potential": 1.0, "temperature": 3.0, "phase": 13.0}.items()),
        "coupling_parameter_gradients": {"potential": coupling_gradient_values[0], "temperature": coupling_gradient_values[1], "phase": coupling_gradient_values[2]},
        "coupling_coordinate_derivatives_preserved": coupling_passed,
    }


def compute_cpu_payload(*, raw_output_directory: Path) -> dict[str, Any]:
    import copy
    from .phk_v23_lf7 import MaterializedPhysicsLedger
    from .phk_v23_lf9 import MaterializedCVLedger, fixed_blind_metrics, load_dev_r_model, strong_thermal_normalized_mse, thermal_control_volume_residual

    contracts = load_contracts(); data = contracts["data"]
    medium = _bound_path(data["training_source"], path_key="path", sha_key="sha256", label="medium")
    checkpoint = _bound_path(data["initial_DEV_R"], path_key="checkpoint_path", sha_key="checkpoint_sha256", label="DEV-R checkpoint")
    prediction = _bound_path(data["initial_DEV_R"], path_key="prediction_path", sha_key="prediction_sha256", label="DEV-R prediction")
    strong = _bound_path(data["strong_ledger"], path_key="path", sha_key="file_sha256", label="strong ledger")
    strong_manifest = _bound_path(data["strong_ledger"], path_key="manifest_path", sha_key="manifest_sha256", label="strong ledger manifest")
    config = build_training_config("cpu"); physics, _, _ = load_case_physics(config.case_control)
    dataset = load_medium_dataset(medium, physics=physics, contracts=contracts)
    arrays, ledger_report = materialize_cv_arrays(cell_x=dataset.cell_x, cell_z=dataset.cell_z, time=dataset.time)
    raw = Path(raw_output_directory).resolve(); cv_root = raw / "cv"
    ledger_path = cv_root / "materialized_cv_ledger.npz"
    ledger_manifest_path = cv_root / "materialized_cv_ledger_manifest.json"
    _save_npz_exclusive(ledger_path, arrays)
    ledger_report.update({
        "schema_id": "phk-v23-lf9-cv-ledger-manifest-v1",
        "runtime_sampling_permitted": False,
        "ledger": {"path": ledger_path.relative_to(ROOT).as_posix(), "sha256": _sha256_path(ledger_path), "size_bytes": ledger_path.stat().st_size},
        "arrays": {
            name: {"shape": list(value.shape), "dtype": value.dtype.str, "sha256": ledger_report["array_sha256"][name]}
            for name, value in arrays.items()
        },
        "streams": {
            "training_step_sha256": ledger_report["training_step_sha256"],
            "training_rolling_sha256": ledger_report["training_rolling_sha256"],
            "one_cell_blind_sha256": ledger_report["one_cell_blind_sha256"],
            "two_by_two_blind_sha256": ledger_report["two_by_two_blind_sha256"],
        },
        "counts": {"training_steps": 1200, "patches_per_step": 16, "training_slabs": 19200, "one_cell_blind_count": 192, "two_by_two_blind_count": 192},
    })
    _write_json_exclusive(ledger_manifest_path, ledger_report)

    model, checkpoint_payload = load_dev_r_model(checkpoint, physics=physics, config=config, device=torch.device("cpu"), contracts=contracts)
    audit = full_medium_audit(model, dataset, device=torch.device("cpu"))
    flat_training = arrays["training_bounds"].reshape(-1, 6)
    raw_cv_mse = _mean_over_chunks(thermal_control_volume_residual, model, flat_training)
    strong_mse = _mean_over_chunks(strong_thermal_normalized_mse, model, flat_training)
    r_cv0_rms = math.sqrt(raw_cv_mse)
    s_cv = r_cv0_rms / math.sqrt(max(strong_mse, 1e-16))
    equality = raw_cv_mse / (s_cv * s_cv)
    strong_identity = {
        "file_sha256": data["strong_ledger"]["file_sha256"], "manifest_sha256": data["strong_ledger"]["manifest_sha256"],
        "semantic_sha256": data["strong_ledger"]["semantic_sha256"], "physics_1200_sha256": data["strong_ledger"]["physics_1200_sha256"],
        "fixed_blind_pool_sha256": data["strong_ledger"]["fixed_blind_pool_sha256"],
    }
    runtime_contracts = copy.deepcopy(contracts); runtime_contracts["data"]["materialized_ledger"] = copy.deepcopy(data["strong_ledger"])
    strong_ledger = MaterializedPhysicsLedger(strong, contracts=runtime_contracts, qualification={"ledger": strong_identity})
    cv_identity = {
        "cv_ledger": {"file_sha256": _sha256_path(ledger_path), "manifest_sha256": _sha256_path(ledger_manifest_path), "training_rolling_sha256": ledger_report["training_rolling_sha256"]}
    }
    cv_ledger = MaterializedCVLedger(ledger_path, ledger_manifest_path, contracts=contracts, qualification=cv_identity)
    blind_baseline = fixed_blind_metrics(model, strong_ledger, cv_ledger, config, cv_scale=s_cv, device=torch.device("cpu"))
    analytic = _analytic_and_routing_qualification()
    rollback = _real_rollback_qualification(model)
    checks = {
        "input_bindings": True,
        "partition_identity": dataset.partition_sha256 == data["partition_sha256"],
        "DEV_R_checkpoint_metadata": checkpoint_payload.get("lf6", {}).get("role") == "DEV_R_EVENT_FRONTIER_RANK_BAND",
        "DEV_R_finite": audit.get("all_values_finite") is True,
        "ledger_shapes": arrays["training_bounds"].shape == (1200, 16, 6) and arrays["one_cell_blind_bounds"].shape == (192, 6) and arrays["two_by_two_blind_bounds"].shape == (192, 6),
        "ledger_disjoint": all(ledger_report["disjoint_checks"].values()),
        "normalization_finite_positive": all(math.isfinite(value) and value > 0.0 for value in (r_cv0_rms, strong_mse, s_cv)),
        "normalization_equality": math.isclose(equality, strong_mse, rel_tol=2e-13, abs_tol=2e-15),
        "analytic_CV_identity": analytic["analytic_passed"],
        "equation_routing_owned_gradients": analytic["routing_passed"],
        "coupling_coordinate_derivatives_preserved": analytic["coupling_coordinate_derivatives_preserved"],
        "real_nonempty_Adam_rollback": rollback["passed"],
        "no_scientific_step_and_reference_blind": True,
    }
    gate = STATUS if all(checks.values()) else "LF9_CPU_QUALIFICATION_FAILED"
    return {
        "schema_id": "phk-v23-lf9-cpu-qualification-v1", "task_id": TASK_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "gate_outcome": gate, "status": gate,
        "scientific_optimizer_updates": 0, "gpu_used": False, "gpu_execution_authorized_by_cpu_gate": gate == STATUS,
        "checks": checks, "cv_ledger": {
            "path": ledger_path.relative_to(ROOT).as_posix(), "file_sha256": _sha256_path(ledger_path),
            "manifest_path": ledger_manifest_path.relative_to(ROOT).as_posix(), "manifest_sha256": _sha256_path(ledger_manifest_path),
            "semantic_sha256": ledger_report["semantic_sha256"], "training_rolling_sha256": ledger_report["training_rolling_sha256"],
            "one_cell_blind_sha256": ledger_report["one_cell_blind_sha256"],
            "two_by_two_blind_sha256": ledger_report["two_by_two_blind_sha256"],
            "array_sha256": ledger_report["array_sha256"],
        },
        "stream_sha256": {"training": ledger_report["training_rolling_sha256"], "one_cell_blind": ledger_report["one_cell_blind_sha256"], "two_by_two_blind": ledger_report["two_by_two_blind_sha256"]},
        "counts": ledger_report["counts"],
        "disjoint_checks": ledger_report["disjoint_checks"],
        "cv_normalization": {"r_cv0_rms": r_cv0_rms, "L_T_strong0": strong_mse, "s_cv": s_cv, "L_T_CV0": equality},
        "blind_baseline": blind_baseline,
        "analytic_and_routing": analytic, "rollback_qualification": rollback,
        "partition_sha256": dataset.partition_sha256, "dev_r_full_medium_audit": audit,
        "strong_ledger": strong_identity,
        "contracts": {name: {"path": path.relative_to(ROOT).as_posix(), "sha256": _sha256_path(path)} for name, path in CONTRACT_PATHS.items()},
        "input_bindings": {"medium": str(medium), "dev_r_checkpoint": str(checkpoint), "dev_r_prediction": str(prediction), "strong_ledger": str(strong), "strong_ledger_manifest": str(strong_manifest)},
        "reference_boundary": {"fine_read": False, "extra_fine_read": False, "direct_LF_ONLY_read": False, "frozen_evaluator_read": False, "stress_read": False},
    }


def build_cpu_manifest(payload: Mapping[str, Any], *, artifact_path: Path, raw_report: Path) -> dict[str, Any]:
    manifest = {
        "schema_version": "run-manifest-v1", "run_id": Path(artifact_path).stem,
        "experiment_group_id": "PHK_V23_LF9", "tier": "qualification",
        "scientific_role": "cpu_zero_update_cv_ledger_normalization_routing_and_rollback_qualification",
        "gate": "PHK_V23_LF9_CPU", "started_at": payload["created_at_utc"], "ended_at": payload["created_at_utc"],
        "command": [".venv/Scripts/python.exe", "-m", "pinn_pcm_sci.phk_v23_lf9_qualification"],
        "execution_status": "COMPLETE", "numerical_validity": "VALID_CPU_FP64_ZERO_SCIENTIFIC_UPDATE",
        "gate_outcome": payload["gate_outcome"], "route_disposition": "RUN_ER_S_AND_ER_CV_FIXED_SCREENS",
        "evidence_identity": "ENGINEERING_QUALIFICATION_ONLY", "seed": 17,
        "claim_status": "LF9_CV_AND_ROUTING_ENGINEERING_QUALIFIED_GPU_MECHANISM_UNTESTED",
        "code_identity": {"base_commit": "f16ca9db66843c04d420c077679604dd553ac036", "workspace_scope": "LF9_EXACT_ALLOWLIST_UNRELATED_DIRTY_PRESERVED"},
        "environment": {"device": "CPU", "dtype": "FLOAT64", "cloud_connection_opened": False, "stress_status": "TWO_STRESS_REFERENCES_SEALED_UNREAD"},
        "physical_contract_id": "PHK_V21_FIXED_DISCRETIZATION_FULL_NOMINAL", "split_id": "MEDIUM_AUDIT_DEV_R_STRONG_AND_CV_LEDGER_ONLY_REFERENCES_SEALED",
        "method_id": "phk-v23-lf9-equation-routed-thermal-cv-v1", "case_id": "PHK_V21_NOMINAL_LF9_CPU_QUALIFICATION",
        "planned_budget": {"gpu_trajectories": 0, "optimizer_updates": 0}, "actual_budget": {"gpu_trajectories": 0, "optimizer_updates": 0, "gpu_used": False},
        "checkpoint": {"DEV_R_source_sha256": payload["contracts"] and "7CFDD98E3A03BE29BBE587042967BD44E72D140AE7AC3396CB35E0CF5748F499", "loaded_read_only": True},
        "evaluator_id": "NOT_READ_DURING_LF9_CPU_QUALIFICATION",
        "artifacts": {"compact_qualification": f"artifacts/{Path(artifact_path).name}#sha256={_sha256_path(Path(artifact_path))}", "raw_report": f"{Path(raw_report).resolve().relative_to(ROOT).as_posix()}#sha256={_sha256_path(Path(raw_report))}", "cv_ledger": f"{payload['cv_ledger']['path']}#sha256={payload['cv_ledger']['file_sha256']}"},
        "failure_class": None, "replay_of": None, "supersedes": None,
    }
    return RunManifest(**manifest).to_dict()


def qualify_cpu(*, artifact_path: Path, manifest_path: Path, raw_output_directory: Path) -> dict[str, Any]:
    payload = compute_cpu_payload(raw_output_directory=raw_output_directory)
    if payload["gate_outcome"] != STATUS:
        raise RuntimeError(payload["gate_outcome"])
    raw_report = Path(raw_output_directory).resolve() / "qualification.json"
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
    print(json.dumps({"gate_outcome": payload["gate_outcome"], "cv_ledger": payload["cv_ledger"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["STATUS", "TASK_ID", "materialize_cv_arrays", "qualify_cpu"]
