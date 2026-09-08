"""LF9 equation-routed strong/CV competence-filtered refinement campaign."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .phk_v22r_pinn import initial_residuals, interior_residuals
from .phk_v22r_prediction import write_prediction_carrier
from .phk_v22r_training import (
    INITIAL_SCALES,
    PDE_SCALES,
    METHOD_CONTRACT_PATH as V22R_METHOD_CONTRACT_PATH,
    PROGRAM_CONTRACT_PATH as V22R_PROGRAM_CONTRACT_PATH,
    ROOT,
    _boundary_loss_by_field,
    _checkpoint_payload,
    _initial_loss_by_field,
    load_case_physics,
)
from .phk_v23_lf0 import PhysicsBatch, _artifact_record, _read_json, _sha256_path, _write_json_exclusive
from .phk_v23_lf2 import load_medium_dataset
from .phk_v23_lf3 import _phase_state_sha256, build_training_config, full_medium_audit
from . import phk_v23_lf7 as lf7
from . import phk_v23_lf8 as lf8


TASK_ID = "PHK_V23_LF9_EQUATION_ROUTED_THERMAL_CONTROL_VOLUME_REFINEMENT_EXECUTE"
TITLE = "PHK-V2.3 LF9 equation-routed thermal control-volume competence-filtered refinement"
ER_S = "ER_S"
ER_CV = "ER_CV"
ARM_ORDER = (ER_S, ER_CV)
ARM_DIRECTORIES = {ER_S: "er-s", ER_CV: "er-cv"}
CONTROL_DIRECTORY = "no-filter-control"
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
EXPECTED_DEV_R_SHA256 = lf7.EXPECTED_DEV_R_SHA256
EXPECTED_PARTITION_SHA256 = lf7.EXPECTED_PARTITION_SHA256
EXPECTED_STRONG_LEDGER_SHA256 = lf7.EXPECTED_LEDGER_SHA256
EXPECTED_STRONG_SEMANTIC_SHA256 = lf7.EXPECTED_LEDGER_SEMANTIC_SHA256
EXPECTED_PHYSICS_SHA256 = lf7.EXPECTED_PHYSICS_SHA256
EXPECTED_FIXED_POOL_SHA256 = lf7.EXPECTED_FIXED_POOL_SHA256
EXPECTED_STRONG_J0 = lf7.EXPECTED_J0

PROGRAM_CONTRACT_PATH = ROOT / "configs/phk_v23/program_contract_lf9_equation_routed_thermal_cv.json"
METHOD_CONTRACT_PATH = ROOT / "configs/phk_v23/method_contract_lf9_equation_routed_thermal_cv.json"
DATA_CONTRACT_PATH = ROOT / "configs/phk_v23/data_contract_lf9_equation_routed_thermal_cv.json"
DECISION_CONTRACT_PATH = ROOT / "configs/phk_v23/decision_contract_lf9_equation_routed_thermal_cv.json"
CONTRACT_PATHS = {"program": PROGRAM_CONTRACT_PATH, "method": METHOD_CONTRACT_PATH, "data": DATA_CONTRACT_PATH, "decision": DECISION_CONTRACT_PATH}
EXPECTED_SCHEMAS = {name: f"phk-v23-lf9-{name}-contract-v1" for name in CONTRACT_PATHS}


def load_contracts() -> dict[str, dict[str, Any]]:
    contracts = {name: _read_json(path) for name, path in CONTRACT_PATHS.items()}
    for name, schema in EXPECTED_SCHEMAS.items():
        if contracts[name].get("schema_id") != schema:
            raise ValueError(f"unsupported LF9 {name} contract")
    relative = {name: path.relative_to(ROOT).as_posix() for name, path in CONTRACT_PATHS.items()}
    if contracts["program"].get("phase_id") != TASK_ID:
        raise ValueError("LF9 task identity drift")
    if any(contracts[name].get("program_contract") != relative["program"] for name in ("method", "data", "decision")):
        raise ValueError("LF9 program contract binding drift")
    if contracts["decision"].get("method_contract") != relative["method"] or contracts["decision"].get("data_contract") != relative["data"]:
        raise ValueError("LF9 decision contract binding drift")
    method = contracts["method"]
    if tuple(float(v) for v in method["filter"]["learning_rate_ladder"]) != LR_LADDER:
        raise ValueError("LF9 learning-rate ladder drift")
    if int(method["filter"]["block_size"]) != BLOCK_SIZE or int(method["thermal_cv"]["patches_per_step"]) != 16:
        raise ValueError("LF9 block or CV batch identity drift")
    data = contracts["data"]
    if data.get("partition_sha256") != EXPECTED_PARTITION_SHA256 or data["initial_DEV_R"].get("checkpoint_sha256") != EXPECTED_DEV_R_SHA256:
        raise ValueError("LF9 inherited input identity drift")
    strong = data["strong_ledger"]
    if strong.get("file_sha256") != EXPECTED_STRONG_LEDGER_SHA256 or strong.get("semantic_sha256") != EXPECTED_STRONG_SEMANTIC_SHA256:
        raise ValueError("LF9 strong ledger binding drift")
    if strong.get("physics_1200_sha256") != EXPECTED_PHYSICS_SHA256 or strong.get("fixed_blind_pool_sha256") != EXPECTED_FIXED_POOL_SHA256:
        raise ValueError("LF9 strong stream identity drift")
    if contracts["decision"].get("stress_status") != "TWO_STRESS_REFERENCES_SEALED_UNREAD":
        raise PermissionError("LF9 stress boundary drift")
    return contracts


def contract_identity() -> dict[str, dict[str, str]]:
    return {name: {"path": path.relative_to(ROOT).as_posix(), "sha256": _sha256_path(path)} for name, path in CONTRACT_PATHS.items()}


def read_cpu_qualification(path: Path) -> dict[str, Any]:
    payload = _read_json(Path(path).resolve())
    if payload.get("schema_id") != "phk-v23-lf9-cpu-qualification-v1" or payload.get("task_id") != TASK_ID:
        raise ValueError("LF9 CPU qualification identity drift")
    if payload.get("gate_outcome") != "LF9_CPU_QUALIFICATION_PASS" or payload.get("scientific_optimizer_updates") != 0:
        raise PermissionError("LF9 CPU qualification did not pass")
    if payload.get("gpu_execution_authorized_by_cpu_gate") is not True or not all(bool(v) for v in payload.get("checks", {}).values()):
        raise PermissionError("LF9 CPU qualification contains a failed check")
    return payload


def _runtime_contracts(contracts: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    value = copy.deepcopy(dict(contracts))
    value["data"]["materialized_ledger"] = copy.deepcopy(value["data"]["strong_ledger"])
    return value


def load_dev_r_model(path: Path, *, physics: Any, config: Any, device: torch.device, contracts: Mapping[str, Mapping[str, Any]]) -> tuple[torch.nn.Module, dict[str, Any]]:
    return lf7.load_dev_r_model(path, physics=physics, config=config, device=device, contracts=_runtime_contracts(contracts))


def field_parameter_groups(model: torch.nn.Module, *, trainable_only: bool = True) -> dict[str, tuple[torch.nn.Parameter, ...]]:
    result: dict[str, tuple[torch.nn.Parameter, ...]] = {}
    for field in ("potential", "temperature", "phase"):
        parameters = tuple(model.encoders[field].parameters()) + tuple(model.heads[field].parameters())
        result[field] = tuple(p for p in parameters if p.requires_grad) if trainable_only else parameters
    return result


def set_phase_trainable(model: torch.nn.Module, trainable: bool) -> None:
    model.encoders["phase"].requires_grad_(trainable)
    model.heads["phase"].requires_grad_(trainable)


def gauss_legendre_2(lower: float, upper: float, *, dtype: torch.dtype, device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
    lo, hi = float(lower), float(upper)
    if not math.isfinite(lo) or not math.isfinite(hi) or hi <= lo:
        raise ValueError("LF9 Gauss interval must be finite and increasing")
    root = 1.0 / math.sqrt(3.0)
    midpoint, half = 0.5 * (lo + hi), 0.5 * (hi - lo)
    nodes = torch.tensor((midpoint - half * root, midpoint + half * root), dtype=dtype, device=device)
    weights = torch.full((2,), half, dtype=dtype, device=device)
    return nodes, weights


def _gradient(value: torch.Tensor, coordinates: torch.Tensor) -> torch.Tensor:
    return torch.autograd.grad(value, coordinates, grad_outputs=torch.ones_like(value), create_graph=True, retain_graph=True)[0]


def _tensor_product_coordinates(bounds: torch.Tensor, *, mode: str) -> tuple[torch.Tensor, torch.Tensor]:
    if bounds.ndim != 2 or bounds.shape[1] != 6:
        raise ValueError("LF9 CV bounds must have shape (N, 6)")
    device, dtype = bounds.device, bounds.dtype
    rows: list[torch.Tensor] = []
    weights: list[torch.Tensor] = []
    for row in bounds:
        x0, x1, z0, z1, t0, t1 = (float(v) for v in row.detach().cpu())
        xn, xw = gauss_legendre_2(x0, x1, dtype=dtype, device=device)
        zn, zw = gauss_legendre_2(z0, z1, dtype=dtype, device=device)
        tn, tw = gauss_legendre_2(t0, t1, dtype=dtype, device=device)
        if mode == "volume":
            q = torch.cartesian_prod(xn, zn, tn).reshape(-1, 3)
            w = torch.cartesian_prod(xw, zw, tw).prod(dim=1)
        elif mode in {"time_a", "time_b"}:
            q = torch.cartesian_prod(xn, zn).reshape(-1, 2)
            q = torch.cat((q, q.new_full((q.shape[0], 1), t0 if mode == "time_a" else t1)), dim=1)
            w = torch.cartesian_prod(xw, zw).prod(dim=1)
        else:
            raise ValueError(mode)
        rows.append(q); weights.append(w)
    return torch.stack(rows), torch.stack(weights)


def thermal_control_volume_residual(model: torch.nn.Module, bounds: torch.Tensor) -> torch.Tensor:
    """Evaluate the direct space-time integral of the frozen thermal equation."""

    bounds = bounds.to(dtype=torch.float64)
    if not bool(torch.isfinite(bounds).all()):
        raise ValueError("LF9 CV bounds are non-finite")
    volume, vw = _tensor_product_coordinates(bounds, mode="volume")
    qa, aw = _tensor_product_coordinates(bounds, mode="time_a")
    qb, bw = _tensor_product_coordinates(bounds, mode="time_b")
    n = bounds.shape[0]
    volume_flat = volume.reshape(-1, 3).detach().clone().requires_grad_(True)
    fields = model(volume_flat)
    potential, temperature, phase = (fields[:, i : i + 1] for i in range(3))
    grad_v = _gradient(potential, volume_flat)
    conductivity = model.physics.conductivity(temperature, phase)
    joule = conductivity * (grad_v[:, 0:1].square() + grad_v[:, 1:2].square())
    volume_t = temperature.reshape(n, -1)
    volume_joule = joule.reshape(n, -1)
    volume_integral_t = torch.sum(volume_t * vw, dim=1)
    volume_integral_joule = torch.sum(volume_joule * vw, dim=1)
    fa = model(qa.reshape(-1, 3)); fb = model(qb.reshape(-1, 3))
    ha = (fa[:, 1] + model.physics.latent_ratio * fa[:, 2]).reshape(n, -1)
    hb = (fb[:, 1] + model.physics.latent_ratio * fb[:, 2]).reshape(n, -1)
    enthalpy_change = torch.sum(hb * bw - ha * aw, dim=1)

    root = bounds.new_tensor(1.0 / math.sqrt(3.0))
    def nodes_weights(lo: torch.Tensor, hi: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        mid, half = 0.5 * (lo + hi), 0.5 * (hi - lo)
        return torch.stack((mid - half * root, mid + half * root), dim=1), half[:, None].expand(-1, 2)
    xn, xw = nodes_weights(bounds[:, 0], bounds[:, 1])
    zn, zw = nodes_weights(bounds[:, 2], bounds[:, 3])
    tn, tw = nodes_weights(bounds[:, 4], bounds[:, 5])
    flux_terms: list[torch.Tensor] = []
    for axis, fixed, tangential, spatial_weights, sign in (
        (0, bounds[:, 0], zn, zw, -1.0),
        (0, bounds[:, 1], zn, zw, 1.0),
        (1, bounds[:, 2], xn, xw, -1.0),
        (1, bounds[:, 3], xn, xw, 1.0),
    ):
        tangential_grid = tangential[:, :, None].expand(-1, 2, 2)
        time_grid = tn[:, None, :].expand(-1, 2, 2)
        fixed_grid = fixed[:, None, None].expand(-1, 2, 2)
        q = (
            torch.stack((fixed_grid, tangential_grid, time_grid), dim=-1)
            if axis == 0
            else torch.stack((tangential_grid, fixed_grid, time_grid), dim=-1)
        ).reshape(-1, 3).detach().clone().requires_grad_(True)
        tface = model(q)[:, 1:2]
        normal = sign * _gradient(tface, q)[:, axis].reshape(n, 2, 2)
        weights = spatial_weights[:, :, None] * tw[:, None, :]
        flux_terms.append(torch.sum(normal * weights, dim=(1, 2)))
    flux_integral = torch.stack(flux_terms, dim=0).sum(dim=0)
    volume_measure = (bounds[:, 1] - bounds[:, 0]) * (bounds[:, 3] - bounds[:, 2]) * (bounds[:, 5] - bounds[:, 4])
    raw = (
        enthalpy_change
        - model.physics.thermal_diffusivity * flux_integral
        + model.physics.volumetric_cooling * volume_integral_t
        - model.physics.joule_gain * volume_integral_joule
    ) / volume_measure
    return raw.reshape(-1, 1)


def strong_thermal_normalized_mse(model: torch.nn.Module, bounds: torch.Tensor) -> torch.Tensor:
    volume, _ = _tensor_product_coordinates(bounds.to(dtype=torch.float64), mode="volume")
    q = volume.reshape(-1, 3)
    residual = interior_residuals(model, q)["thermal"]
    return torch.mean((residual / float(PDE_SCALES["thermal"])).square())


TrainingSnapshot = lf8.TrainingSnapshot
take_snapshot = lf8.take_snapshot
restore_snapshot = lf8.restore_snapshot
snapshot_digest = lf8.snapshot_digest


class MaterializedCVLedger:
    ARRAY_NAMES = (
        "training_bounds", "training_identity", "one_cell_blind_bounds",
        "one_cell_blind_identity", "two_by_two_blind_bounds", "two_by_two_blind_identity",
        "training_step_sha256",
    )

    def __init__(self, path: Path, manifest_path: Path, *, contracts: Mapping[str, Mapping[str, Any]], qualification: Mapping[str, Any]) -> None:
        binding = contracts["data"]["cv_ledger"]
        supplied, supplied_manifest = Path(path).resolve(), Path(manifest_path).resolve()
        expected = (ROOT / binding["path"]).resolve()
        expected_manifest = (ROOT / binding["manifest_path"]).resolve()
        if supplied != expected or supplied_manifest != expected_manifest:
            raise PermissionError("LF9 CV ledger path binding drift")
        qbinding = qualification.get("cv_ledger", {})
        if not supplied.is_file() or _sha256_path(supplied) != str(qbinding.get("file_sha256", "")).upper():
            raise ValueError("LF9 CV ledger file identity drift")
        if not supplied_manifest.is_file() or _sha256_path(supplied_manifest) != str(qbinding.get("manifest_sha256", "")).upper():
            raise ValueError("LF9 CV ledger manifest identity drift")
        manifest = _read_json(supplied_manifest)
        if manifest.get("schema_id") != "phk-v23-lf9-cv-ledger-manifest-v1" or manifest.get("runtime_sampling_permitted") is not False:
            raise ValueError("LF9 CV ledger manifest schema drift")
        with np.load(supplied, allow_pickle=False) as archive:
            if set(archive.files) != set(self.ARRAY_NAMES):
                raise ValueError("LF9 CV ledger array key drift")
            self.arrays = {name: np.asarray(archive[name]) for name in self.ARRAY_NAMES}
        arrays = manifest.get("arrays", {})
        for name, value in self.arrays.items():
            record = arrays.get(name, {})
            if list(value.shape) != record.get("shape") or value.dtype.str != record.get("dtype"):
                raise ValueError(f"LF9 CV ledger array metadata drift: {name}")
            recorded = str(record.get("sha256", "")).upper()
            if recorded and recorded != _qualification_array_digest(name, value):
                raise ValueError(f"LF9 CV ledger array content drift: {name}")
        if self.arrays["training_bounds"].shape != (1200, 16, 6):
            raise ValueError("LF9 CV training ledger shape drift")
        if self.arrays["one_cell_blind_bounds"].shape != (192, 6) or self.arrays["two_by_two_blind_bounds"].shape != (192, 6):
            raise ValueError("LF9 CV blind ledger shape drift")
        encoded = self.arrays["training_step_sha256"].reshape(-1)
        self.training_step_sha256 = tuple(v.decode("ascii") if isinstance(v, bytes) else str(v) for v in encoded)
        if len(self.training_step_sha256) != 1200:
            raise ValueError("LF9 CV training stream length drift")
        recomputed: list[str] = []
        for index in range(1200):
            one = hashlib.sha256(b"PHK_V23_LF9_MATERIALIZED_THERMAL_CV_LEDGER_V1/STEP")
            one.update(np.asarray(index + 1, dtype="<i8").tobytes())
            one.update(np.ascontiguousarray(self.arrays["training_identity"][index], dtype="<i8").tobytes())
            one.update(np.ascontiguousarray(self.arrays["training_bounds"][index], dtype="<f8").tobytes())
            recomputed.append(one.hexdigest().upper())
        if tuple(recomputed) != self.training_step_sha256:
            raise ValueError("LF9 CV per-step stream identity drift")
        rolling = hashlib.sha256(b"PHK_V23_LF9_MATERIALIZED_THERMAL_CV_LEDGER_V1/TRAINING")
        for value in recomputed: rolling.update(bytes.fromhex(value))
        self.training_rolling_sha256 = str(manifest.get("streams", {}).get("training_rolling_sha256", "")).upper()
        if rolling.hexdigest().upper() != self.training_rolling_sha256:
            raise ValueError("LF9 CV recomputed rolling identity drift")
        if self.training_rolling_sha256 != str(qbinding.get("training_rolling_sha256", self.training_rolling_sha256)).upper():
            raise ValueError("LF9 CV training rolling identity drift")

    def training_bounds(self, step: int, *, device: torch.device) -> torch.Tensor:
        if step < 1 or step > 1200:
            raise ValueError("LF9 CV training step out of range")
        return torch.as_tensor(self.arrays["training_bounds"][step - 1], dtype=torch.float64, device=device)

    def one_cell_blind_bounds(self, *, device: torch.device) -> torch.Tensor:
        return torch.as_tensor(self.arrays["one_cell_blind_bounds"], dtype=torch.float64, device=device)

    def two_by_two_blind_bounds(self, *, device: torch.device) -> torch.Tensor:
        return torch.as_tensor(self.arrays["two_by_two_blind_bounds"], dtype=torch.float64, device=device)


def _qualification_array_digest(name: str, value: np.ndarray) -> str:
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256(name.encode("ascii"))
    digest.update(array.dtype.str.encode("ascii")); digest.update(str(tuple(array.shape)).encode("ascii")); digest.update(array.tobytes(order="C"))
    return digest.hexdigest().upper()


def routed_field_gradients(losses: Mapping[str, torch.Tensor], groups: Mapping[str, Sequence[torch.nn.Parameter]]) -> dict[str, tuple[torch.Tensor, ...]]:
    result: dict[str, tuple[torch.Tensor, ...]] = {}
    for field in ("potential", "temperature", "phase"):
        parameters = tuple(p for p in groups[field] if p.requires_grad)
        if not parameters:
            result[field] = ()
            continue
        gradients = torch.autograd.grad(losses[field], parameters, retain_graph=True, create_graph=False, allow_unused=True)
        result[field] = tuple(torch.zeros_like(parameter) if gradient is None else gradient for parameter, gradient in zip(parameters, gradients, strict=True))
    return result


def routed_physics_objectives(
    model: torch.nn.Module,
    batch: PhysicsBatch,
    config: Any,
    *,
    thermal_mode: str,
    cv_bounds: torch.Tensor | None = None,
    cv_scale: float | None = None,
) -> tuple[dict[str, torch.Tensor], dict[str, float]]:
    if thermal_mode not in {ER_S, ER_CV}:
        raise ValueError("LF9 unknown thermal mode")
    interior = interior_residuals(model, batch.interior)
    pde = {
        name: torch.mean((interior[name] / float(PDE_SCALES[name])).square())
        for name in ("electric", "thermal", "phase")
    }
    if thermal_mode == ER_CV:
        if cv_bounds is None or cv_scale is None or not math.isfinite(float(cv_scale)) or float(cv_scale) <= 0.0:
            raise ValueError("LF9 ER-CV requires finite frozen CV scale and bounds")
        raw = thermal_control_volume_residual(model, cv_bounds)
        pde["thermal"] = torch.mean((raw / float(cv_scale)).square())
    _, boundary_diagnostics, boundary_by_field = _boundary_loss_by_field(model, batch.boundary)
    _, initial_by_field = _initial_loss_by_field(initial_residuals(model, batch.initial))
    objectives = {
        "potential": config.pde_weight * pde["electric"] / 3.0 + config.boundary_weight * boundary_by_field["potential"] + config.initial_weight * initial_by_field["potential"],
        "temperature": config.pde_weight * pde["thermal"] / 3.0 + config.boundary_weight * boundary_by_field["temperature"] + config.initial_weight * initial_by_field["temperature"],
        "phase": config.pde_weight * pde["phase"] / 3.0 + config.boundary_weight * boundary_by_field["phase"] + config.initial_weight * initial_by_field["phase"],
    }
    components = {
        "physics_total": float(sum(objectives.values()).detach().cpu()),
        "electric_normalized_mse": float(pde["electric"].detach().cpu()),
        "thermal_normalized_mse": float(pde["thermal"].detach().cpu()),
        "phase_normalized_mse": float(pde["phase"].detach().cpu()),
        **{f"field_objective:{name}": float(value.detach().cpu()) for name, value in objectives.items()},
        **{f"boundary:{name}": value for name, value in boundary_diagnostics.items()},
    }
    return objectives, components


def routed_optimizer_step(model: torch.nn.Module, optimizer: torch.optim.Optimizer, *, batch: PhysicsBatch, config: Any, thermal_mode: str, cv_bounds: torch.Tensor | None = None, cv_scale: float | None = None) -> tuple[bool, dict[str, Any]]:
    optimizer.zero_grad(set_to_none=True)
    objectives, components = routed_physics_objectives(model, batch, config, thermal_mode=thermal_mode, cv_bounds=cv_bounds, cv_scale=cv_scale)
    total = sum(objectives.values())
    if not bool(torch.isfinite(total)):
        return False, {**components, "gradient_norm_before_clip": math.inf}
    groups = field_parameter_groups(model)
    gradients = routed_field_gradients(objectives, groups)
    per_head: dict[str, float] = {}
    for field, values in gradients.items():
        per_head[field] = math.sqrt(sum(float(torch.sum(g.detach().square()).cpu()) for g in values))
        for parameter, gradient in zip(groups[field], values, strict=True):
            parameter.grad = gradient
    trainable = tuple(p for p in model.parameters() if p.requires_grad)
    grad_norm = float(torch.nn.utils.clip_grad_norm_(trainable, 10.0).detach().cpu())
    if not math.isfinite(grad_norm):
        return False, {**components, "gradient_norm_before_clip": grad_norm, "per_head_gradient_norm_before_clip": per_head}
    optimizer.step()
    return True, {**components, "gradient_norm_before_clip": grad_norm, "per_head_gradient_norm_before_clip": per_head, "clip_factor": min(1.0, 10.0 / grad_norm) if grad_norm else 1.0}


def competence_gate(audit: Mapping[str, Any], baseline: Mapping[str, Any] | None = None, *, strict_timing: bool = False, physics_previous: float | None = None, physics_new: float | None = None) -> dict[str, Any]:
    baseline = baseline or {"weighted_errors": DEV_R_BASELINE, "topology_weighted_loss": DEV_R_TOPOLOGY}
    if "event_metrics" in audit:
        return lf7.competence_gate(audit, baseline, strict_timing=strict_timing, physics_previous=physics_previous, physics_new=physics_new)
    potential = audit.get("potential_guard", {}).get("global", {})
    checks = {
        "finite": audit.get("all_values_finite") is True,
        "phase_range": float(audit.get("phase_minimum", -math.inf)) >= -1e-10 and float(audit.get("phase_maximum", math.inf)) <= 1.0000000001,
        "potential": bool(audit.get("potential_guard", {}).get("passed")) and float(potential.get("maximum_absolute_excess", math.inf)) <= 1e-6 and float(potential.get("violation_fraction", math.inf)) == 0.0,
        "phase_maximum": float(audit.get("phase_maximum", -math.inf)) >= 0.90,
    }
    maxima = {"potential": 1.20, "temperature": 1.05, "phase": 1.05}
    ratios = {name: float(audit["weighted_errors"][name]) / float(baseline["weighted_errors"][name]) for name in maxima}
    ratios["topology"] = float(audit["topology_weighted_loss"]) / float(baseline["topology_weighted_loss"])
    for name, maximum in {**maxima, "topology": 1.05}.items(): checks[f"relative_{name}"] = math.isfinite(ratios[name]) and ratios[name] <= maximum
    for cycle in (1, 2):
        value = audit["cycles"][f"cycle_{cycle}"]; prefix = f"cycle_{cycle}"
        checks[f"{prefix}_event"] = value.get("event_exists") is True
        checks[f"{prefix}_recall"] = float(value.get("hard_recall", -math.inf)) >= 0.90
        checks[f"{prefix}_precision"] = float(value.get("hard_precision", -math.inf)) >= 0.80
        checks[f"{prefix}_mass"] = 0.80 <= float(value.get("hard_active_mass_ratio", math.inf)) <= 1.20
        limit = 0.005 if strict_timing else ((0.010533333334333338, 0.005000000000999893)[cycle - 1])
        checks[f"{prefix}_timing"] = float(value.get("event_time_absolute_error", math.inf)) <= limit
        checks[f"{prefix}_roi_peak"] = float(value.get("roi_peak_fraction", -math.inf)) >= 0.02
        checks[f"{prefix}_full_peak"] = float(value.get("full_domain_peak_fraction", math.inf)) <= 0.45
        checks[f"{prefix}_outside_peak"] = float(value.get("outside_roi_peak_fraction", math.inf)) <= 0.10
        checks[f"{prefix}_recovery"] = float(value.get("recovery_fraction", -math.inf)) >= 0.70
    if physics_previous is not None and physics_new is not None:
        decrease = max(1e-12, 1e-8 * float(physics_previous))
        checks["fixed_blind_strict_improvement"] = math.isfinite(float(physics_new)) and float(physics_new) <= float(physics_previous) - decrease
    failed = sorted(name for name, passed in checks.items() if not passed)
    return {"passed": not failed, "checks": checks, "failed_checks": failed, "relative_DEV_R": ratios, "strict_timing": strict_timing, "physics_previous": physics_previous, "physics_new": physics_new}


def screen_go(endpoint: Mapping[str, Any]) -> bool:
    return bool(endpoint.get("numerical_valid") and int(endpoint.get("accepted_updates", 0)) == SCREEN_ACCEPTED_UPDATES and endpoint.get("safety_gate", {}).get("passed") and float(endpoint.get("own_ratio", math.inf)) <= 0.95 and float(endpoint.get("cv1_ratio", math.inf)) <= 0.95 and float(endpoint.get("cv4_ratio", math.inf)) <= 0.95)


def adjudicate_screens(arms: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    invalid = [name for name in ARM_ORDER if arms.get(name, {}).get("identity_valid") is False]
    s_go, cv_go = screen_go(arms.get(ER_S, {})), screen_go(arms.get(ER_CV, {}))
    if s_go and not cv_go: outcome, selected = "EQUATION_ROUTING_SUFFICIENT", ER_S
    elif cv_go and not s_go: outcome, selected = "THERMAL_CONTROL_VOLUME_SUPPORTED", ER_CV
    elif s_go and cv_go:
        cv_gain = float(arms[ER_CV]["cv4_ratio"]) <= 0.90 * float(arms[ER_S]["cv4_ratio"])
        if cv_gain and arms[ER_CV].get("safety_gate", {}).get("passed"):
            outcome, selected = "THERMAL_CONTROL_VOLUME_ADDS_MEANINGFUL_CONSERVATION_GAIN", ER_CV
        else: outcome, selected = "ROUTING_SUFFICIENT_CV_NOT_LOAD_BEARING", ER_S
    else: outcome, selected = "NO_SAFE_MIXED_FORM_SCREEN", None
    if invalid:
        outcome = "MATCHED_ATTRIBUTION_UNAVAILABLE_VALID_ARM" if selected else "MATCHED_ATTRIBUTION_UNAVAILABLE"
    return {"screen_outcomes": {ER_S: s_go, ER_CV: cv_go}, "mechanism_outcome": outcome, "selected_arm": selected, "identity_invalid_arms": invalid}


def fixed_blind_metrics(model: torch.nn.Module, strong_ledger: Any, cv_ledger: MaterializedCVLedger, config: Any, *, cv_scale: float, device: torch.device) -> dict[str, float]:
    """Evaluate both blind objectives and both conservation scales at one state."""

    batch = strong_ledger.fixed_batch(device=device)
    one = cv_ledger.one_cell_blind_bounds(device=device)
    four = cv_ledger.two_by_two_blind_bounds(device=device)
    with torch.enable_grad():
        strong_objectives, _ = routed_physics_objectives(model, batch, config, thermal_mode=ER_S)
        mixed_objectives, _ = routed_physics_objectives(model, batch, config, thermal_mode=ER_CV, cv_bounds=one, cv_scale=cv_scale)
        cv1 = torch.mean((thermal_control_volume_residual(model, one) / float(cv_scale)).square())
        cv4 = torch.mean((thermal_control_volume_residual(model, four) / float(cv_scale)).square())
    return {
        "J_S": float(sum(strong_objectives.values()).detach().cpu()),
        "J_M": float(sum(mixed_objectives.values()).detach().cpu()),
        "CV1": float(cv1.detach().cpu()),
        "CV4": float(cv4.detach().cpu()),
    }


def _ratios(metrics: Mapping[str, float], baseline: Mapping[str, float]) -> dict[str, float]:
    return {name: float(metrics[name]) / float(baseline[name]) for name in ("J_S", "J_M", "CV1", "CV4")}


def _arm_audit(model: torch.nn.Module, dataset: Any, strong_ledger: Any, cv_ledger: MaterializedCVLedger, config: Any, *, cv_scale: float, device: torch.device) -> dict[str, Any]:
    return {
        "medium": full_medium_audit(model, dataset, device=device),
        "blind": fixed_blind_metrics(model, strong_ledger, cv_ledger, config, cv_scale=cv_scale, device=device),
    }


def _own_key(arm: str) -> str:
    if arm == ER_S: return "J_S"
    if arm == ER_CV: return "J_M"
    raise KeyError(arm)


def _make_optimizer(model: torch.nn.Module) -> torch.optim.Adam:
    return torch.optim.Adam(model.parameters(), lr=ETA0, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0, amsgrad=False)


def _available_lrs(current: float) -> tuple[float, ...]:
    index = min(range(len(LR_LADDER)), key=lambda i: abs(LR_LADDER[i] - float(current)))
    if not math.isclose(LR_LADDER[index], float(current), rel_tol=0.0, abs_tol=1e-16):
        raise ValueError("LF9 accepted learning rate left frozen ladder")
    return LR_LADDER[index:]


def _append(handle: Any, payload: Mapping[str, Any]) -> None:
    handle.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n"); handle.flush()


def _block_sha256(strong_hashes: Sequence[str], cv_hashes: Sequence[str]) -> str:
    digest = hashlib.sha256(b"PHK_V23_LF9_MATCHED_BLOCK_V1\n")
    for value in (*strong_hashes, *cv_hashes): digest.update(value.encode("ascii") + b"\n")
    return digest.hexdigest().upper()


def _checkpoint(
    path: Path, *, model: torch.nn.Module, optimizer: torch.optim.Optimizer, config: Any,
    role: str, accepted: int, attempted: int, source_identity: str,
    physics_program_sha256: str, physics_object_sha256: str, disposition: str,
    accepted_learning_rates: Sequence[float],
) -> Path:
    payload = _checkpoint_payload(
        model=model, optimizer=optimizer, config=config, update=accepted,
        program_contract_sha256=_sha256_path(V22R_PROGRAM_CONTRACT_PATH),
        method_contract_sha256=_sha256_path(V22R_METHOD_CONTRACT_PATH),
        physical_program_sha256=physics_program_sha256,
        physical_object_sha256=physics_object_sha256,
    )
    payload["lf9"] = {
        "schema_id": "phk-v23-lf9-checkpoint-metadata-v1", "task_id": TASK_ID,
        "role": role, "accepted_optimizer_updates": accepted,
        "attempted_optimizer_updates": attempted, "source_identity": source_identity,
        "contracts": contract_identity(), "parent_checkpoint_sha256": EXPECTED_DEV_R_SHA256,
        "equation_routing_used": True, "thermal_control_volume_used": role.startswith(ER_CV),
        "medium_gradient_used": False, "runtime_sampling_used": False,
        "stress_read": False, "disposition": disposition,
        "accepted_learning_rates": list(accepted_learning_rates),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle: torch.save(payload, handle)
    return path


def _save_model_artifacts(directory: Path, *, prefix: str, model: torch.nn.Module, optimizer: torch.optim.Optimizer, config: Any, role: str, accepted: int, attempted: int, source_identity: str, physics_program_sha256: str, physics_object_sha256: str, disposition: str, accepted_learning_rates: Sequence[float]) -> tuple[Path, Path]:
    checkpoint = _checkpoint(directory / f"{prefix}checkpoint.pt", model=model, optimizer=optimizer, config=config, role=role, accepted=accepted, attempted=attempted, source_identity=source_identity, physics_program_sha256=physics_program_sha256, physics_object_sha256=physics_object_sha256, disposition=disposition, accepted_learning_rates=accepted_learning_rates)
    prediction = write_prediction_carrier(checkpoint_path=checkpoint, output_path=directory / f"{prefix}prediction.npz", device_name=str(next(model.parameters()).device))
    return checkpoint, prediction


def prelocal_internal_pareto(result: Mapping[str, Any]) -> bool:
    return bool(
        result.get("numerical_valid") and int(result.get("accepted_updates", 0)) == FULL_ACCEPTED_UPDATES
        and result.get("safety_gate", {}).get("passed") and result.get("strict_gate", {}).get("passed")
        and float(result.get("own_ratio", math.inf)) <= 0.50
        and float(result.get("cv1_ratio", math.inf)) <= 0.75
        and float(result.get("cv4_ratio", math.inf)) <= 0.75
    )


def _seed_all(seed: int = 17) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _phase_optimizer_state_entries(model: torch.nn.Module, optimizer: torch.optim.Optimizer) -> int:
    phase = set(field_parameter_groups(model, trainable_only=False)["phase"])
    return sum(parameter in optimizer.state for parameter in phase)


def _write_recovery_state(
    path: Path,
    *,
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    accepted: int,
    attempted: int,
    current_lr: float,
    accepted_learning_rates: Sequence[float],
    arm: str,
) -> None:
    payload = {
        "schema_id": "phk-v23-lf9-valid-prefix-v1",
        "task_id": TASK_ID,
        "arm": arm,
        "accepted_updates": int(accepted),
        "attempted_updates": int(attempted),
        "current_learning_rate": float(current_lr),
        "accepted_learning_rates": list(accepted_learning_rates),
        "snapshot": take_snapshot(
            model, optimizer, accepted_updates=accepted, learning_rate=current_lr
        ),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    torch.save(payload, temporary)
    temporary.replace(path)


def _invalid_arm_result(arm: str, exc: Exception) -> dict[str, Any]:
    return {
        "arm": arm,
        "identity_valid": False,
        "numerical_valid": False,
        "endpoint_valid": False,
        "accepted_updates": 0,
        "attempted_updates": 0,
        "accepted_blocks": 0,
        "rejected_block_attempts": 0,
        "accepted_learning_rates": [],
        "disposition": "POSTSTEP_IDENTITY_INVALID",
        "safety_gate": {"passed": False, "failed_checks": ["poststep_exception"]},
        "strict_gate": {"passed": False, "failed_checks": ["poststep_exception"]},
        "error": {"type": type(exc).__name__, "message": str(exc)},
    }


def _make_runtime(
    *,
    arm: str,
    root: Path,
    dataset: Any,
    strong_ledger: Any,
    cv_ledger: MaterializedCVLedger,
    initial_checkpoint: Path,
    contracts: Mapping[str, Mapping[str, Any]],
    qualification: Mapping[str, Any],
    physics: Any,
    config: Any,
    device: torch.device,
    cv_scale: float,
) -> dict[str, Any]:
    directory = root / ARM_DIRECTORIES[arm]
    directory.mkdir(parents=True, exist_ok=False)
    model, _ = load_dev_r_model(
        initial_checkpoint, physics=physics, config=config, device=device, contracts=contracts
    )
    set_phase_trainable(model, False)
    optimizer = _make_optimizer(model)
    audit = _arm_audit(
        model, dataset, strong_ledger, cv_ledger, config,
        cv_scale=cv_scale, device=device,
    )
    expected = qualification["blind_baseline"]
    for key in ("J_S", "J_M", "CV1", "CV4"):
        if not math.isclose(float(audit["blind"][key]), float(expected[key]), rel_tol=1e-9, abs_tol=1e-12):
            raise RuntimeError(f"LF9 DEV-R GPU baseline drift: {key}")
    baseline_medium = qualification["dev_r_full_medium_audit"]
    baseline_gate = competence_gate(audit["medium"], baseline_medium)
    if not baseline_gate["passed"]:
        raise RuntimeError("LF9 DEV-R GPU competence identity drift")
    return {
        "arm": arm,
        "directory": directory,
        "model": model,
        "optimizer": optimizer,
        "accepted": 0,
        "attempted": 0,
        "rejected": 0,
        "current_lr": ETA0,
        "accepted_lrs": [],
        "last_audit": audit,
        "baseline_medium": baseline_medium,
        "baseline_blind": {key: float(expected[key]) for key in ("J_S", "J_M", "CV1", "CV4")},
        "phase_initial": _phase_state_sha256(model),
        "identity_valid": True,
        "numerical_valid": True,
        "disposition": "ACTIVE",
        "last_rejection": [],
    }


def _train_proposed_block(
    runtime: dict[str, Any],
    *,
    strong_ledger: Any,
    cv_ledger: MaterializedCVLedger,
    config: Any,
    cv_scale: float,
    device: torch.device,
    learning_rate: float,
    telemetry: Any,
    batches: Any,
) -> tuple[bool, dict[str, Any] | None, list[str], list[str]]:
    model, optimizer = runtime["model"], runtime["optimizer"]
    accepted = int(runtime["accepted"])
    for group in optimizer.param_groups:
        group["lr"] = float(learning_rate)
    next_step = accepted + 1
    set_phase_trainable(model, next_step > PHASE_FREEZE_STEPS)
    if next_step == PHASE_FREEZE_STEPS + 1:
        if _phase_state_sha256(model) != runtime["phase_initial"] or _phase_optimizer_state_entries(model, optimizer) != 0:
            raise RuntimeError("LF9 phase-freeze identity drift at accepted step 550")
    train: dict[str, Any] | None = None
    strong_hashes: list[str] = []
    cv_hashes: list[str] = []
    for local in range(BLOCK_SIZE):
        step = accepted + local + 1
        strong_batch = strong_ledger.physics_batch(step, device=device)
        cv_bounds = cv_ledger.training_bounds(step, device=device)
        ok, train = routed_optimizer_step(
            model,
            optimizer,
            batch=strong_batch,
            config=config,
            thermal_mode=runtime["arm"],
            cv_bounds=cv_bounds if runtime["arm"] == ER_CV else None,
            cv_scale=cv_scale if runtime["arm"] == ER_CV else None,
        )
        runtime["attempted"] += 1
        strong_hashes.append(strong_batch.batch_sha256)
        cv_hashes.append(cv_ledger.training_step_sha256[step - 1])
        _append(batches, {
            "arm": runtime["arm"],
            "attempted_update": runtime["attempted"],
            "proposed_accepted_update": step,
            "learning_rate": float(learning_rate),
            "strong_batch_sha256": strong_batch.batch_sha256,
            "cv_batch_sha256": cv_ledger.training_step_sha256[step - 1],
        })
        if not ok:
            _append(telemetry, {
                "arm": runtime["arm"], "decision": "NUMERICAL_REJECT",
                "accepted_before": accepted, "learning_rate": float(learning_rate),
                "train": train,
            })
            return False, train, strong_hashes, cv_hashes
    return True, train, strong_hashes, cv_hashes


def _advance_filtered(
    runtime: dict[str, Any],
    *,
    target_accepted: int,
    attempted_cap: int,
    dataset: Any,
    strong_ledger: Any,
    cv_ledger: MaterializedCVLedger,
    config: Any,
    cv_scale: float,
    device: torch.device,
) -> None:
    """Advance one arm through immutable block proposals until target or stall."""

    directory = runtime["directory"]
    telemetry_path, batches_path = directory / "telemetry.jsonl", directory / "batch_ledger.jsonl"
    mode = "a" if telemetry_path.exists() else "x"
    with telemetry_path.open(mode, encoding="utf-8", newline="\n") as telemetry, batches_path.open(mode, encoding="utf-8", newline="\n") as batches:
        while runtime["accepted"] < target_accepted:
            if runtime["attempted"] + BLOCK_SIZE > attempted_cap:
                runtime["disposition"] = "ATTEMPT_CAP_REACHED_WITH_VALID_PREFIX"
                break
            accepted_before = int(runtime["accepted"])
            snapshot = take_snapshot(
                runtime["model"], runtime["optimizer"],
                accepted_updates=accepted_before, learning_rate=runtime["current_lr"],
            )
            snapshot_hash = snapshot_digest(snapshot)
            accepted_block = False
            for learning_rate in _available_lrs(runtime["current_lr"]):
                if runtime["attempted"] + BLOCK_SIZE > attempted_cap:
                    break
                if runtime["accepted"] != accepted_before:
                    raise RuntimeError("LF9 accepted-step identity changed within proposal ladder")
                ok, train, strong_hashes, cv_hashes = _train_proposed_block(
                    runtime,
                    strong_ledger=strong_ledger,
                    cv_ledger=cv_ledger,
                    config=config,
                    cv_scale=cv_scale,
                    device=device,
                    learning_rate=learning_rate,
                    telemetry=telemetry,
                    batches=batches,
                )
                gate: dict[str, Any]
                proposed: dict[str, Any] | None = None
                if ok:
                    proposed = _arm_audit(
                        runtime["model"], dataset, strong_ledger, cv_ledger, config,
                        cv_scale=cv_scale, device=device,
                    )
                    own = _own_key(runtime["arm"])
                    gate = competence_gate(
                        proposed["medium"], runtime["baseline_medium"],
                        physics_previous=float(runtime["last_audit"]["blind"][own]),
                        physics_new=float(proposed["blind"][own]),
                    )
                else:
                    gate = {"passed": False, "failed_checks": ["finite_gradient_or_objective"]}
                record = {
                    "arm": runtime["arm"],
                    "block": accepted_before // BLOCK_SIZE + 1,
                    "stage": "PHASE_FROZEN" if accepted_before < PHASE_FREEZE_STEPS else "JOINT",
                    "learning_rate": float(learning_rate),
                    "accepted_before": accepted_before,
                    "attempted_updates": runtime["attempted"],
                    "strong_cv_block_sha256": _block_sha256(strong_hashes, cv_hashes),
                    "snapshot_sha256": snapshot_hash,
                    "train": train,
                    "audit": proposed,
                    "filter_gate": gate,
                }
                if gate["passed"]:
                    runtime["accepted"] += BLOCK_SIZE
                    runtime["current_lr"] = float(learning_rate)
                    runtime["accepted_lrs"].append(float(learning_rate))
                    runtime["last_audit"] = proposed
                    runtime["last_rejection"] = []
                    record.update({"decision": "ACCEPT", "accepted_after": runtime["accepted"]})
                    _append(telemetry, record)
                    _write_recovery_state(
                        directory / "valid-prefix.pt",
                        model=runtime["model"], optimizer=runtime["optimizer"],
                        accepted=runtime["accepted"], attempted=runtime["attempted"],
                        current_lr=runtime["current_lr"],
                        accepted_learning_rates=runtime["accepted_lrs"], arm=runtime["arm"],
                    )
                    accepted_block = True
                    break
                runtime["rejected"] += 1
                runtime["last_rejection"] = list(gate["failed_checks"])
                restored = restore_snapshot(snapshot, runtime["model"], runtime["optimizer"])
                record.update({
                    "decision": "REJECT_ROLLBACK", "accepted_after": accepted_before,
                    "reject_reason": gate["failed_checks"], "restored_state_sha256": restored,
                    "snapshot_still_immutable": snapshot_digest(snapshot) == snapshot_hash,
                })
                _append(telemetry, record)
            if not accepted_block:
                runtime["disposition"] = (
                    "ATTEMPT_CAP_REACHED_WITH_VALID_PREFIX"
                    if runtime["attempted"] + BLOCK_SIZE > attempted_cap
                    else "FILTER_STALLED_WITH_VALID_PREFIX"
                )
                restore_snapshot(snapshot, runtime["model"], runtime["optimizer"])
                break
        if runtime["accepted"] == target_accepted:
            runtime["disposition"] = "SCREEN_COMPLETE" if target_accepted == SCREEN_ACCEPTED_UPDATES else "FULL_COMPLETE"


def _endpoint_result(runtime: Mapping[str, Any], *, target: int) -> dict[str, Any]:
    audit = runtime["last_audit"]
    baseline = runtime["baseline_blind"]
    ratios = _ratios(audit["blind"], baseline)
    safety = competence_gate(audit["medium"], runtime["baseline_medium"])
    strict = competence_gate(audit["medium"], runtime["baseline_medium"], strict_timing=True)
    own = _own_key(runtime["arm"])
    valid = bool(runtime["identity_valid"] and runtime["numerical_valid"] and audit["medium"].get("all_values_finite") is True)
    return {
        "arm": runtime["arm"],
        "identity_valid": bool(runtime["identity_valid"]),
        "numerical_valid": valid,
        "endpoint_valid": valid,
        "accepted_updates": int(runtime["accepted"]),
        "attempted_updates": int(runtime["attempted"]),
        "accepted_blocks": int(runtime["accepted"]) // BLOCK_SIZE,
        "rejected_block_attempts": int(runtime["rejected"]),
        "accepted_learning_rates": list(runtime["accepted_lrs"]),
        "final_learning_rate": float(runtime["current_lr"]),
        "disposition": runtime["disposition"],
        "safety_gate": safety,
        "strict_gate": strict,
        "blind": audit["blind"],
        "blind_ratios_to_DEV_R": ratios,
        "own_ratio": ratios[own],
        "cv1_ratio": ratios["CV1"],
        "cv4_ratio": ratios["CV4"],
        "final_audit": audit,
        "target_accepted_updates": int(target),
        "last_rejection": list(runtime["last_rejection"]),
    }


def _persist_endpoint(
    runtime: Mapping[str, Any], result: dict[str, Any], *, prefix: str,
    config: Any, source_identity: str,
    physics_program_sha256: str, physics_object_sha256: str,
) -> None:
    checkpoint, prediction = _save_model_artifacts(
        runtime["directory"], prefix=prefix, model=runtime["model"],
        optimizer=runtime["optimizer"], config=config,
        role=f"{runtime['arm']}:{'SCREEN' if prefix.startswith('screen') else 'FULL'}",
        accepted=runtime["accepted"], attempted=runtime["attempted"],
        source_identity=source_identity,
        physics_program_sha256=physics_program_sha256,
        physics_object_sha256=physics_object_sha256,
        disposition=runtime["disposition"],
        accepted_learning_rates=runtime["accepted_lrs"],
    )
    result["checkpoint_sha256"] = _sha256_path(checkpoint)
    result["prediction_sha256"] = _sha256_path(prediction)
    gate_path = runtime["directory"] / f"{prefix}gate.json"
    _write_json_exclusive(gate_path, result)


def _full_path_disposition(result: Mapping[str, Any]) -> str:
    if int(result.get("accepted_updates", 0)) <= PHASE_FREEZE_STEPS:
        failed = set(result.get("last_rejection", ()))
        if "relative_temperature" in failed:
            return "PHASE_FROZEN_THERMAL_ROUTE_FAILED"
    if int(result.get("accepted_updates", 0)) > PHASE_FREEZE_STEPS:
        failed = set(result.get("last_rejection", ()))
        if any("cycle_" in value or value in {"relative_phase", "relative_topology"} for value in failed):
            return "PHASE_KINETIC_PRIMARY_BLOCKER"
    return "FULL_PATH_STALLED_OR_PHYSICS_GATE_MISSED"


def _run_no_filter_control(
    *,
    selected_arm: str,
    schedule: Sequence[float],
    root: Path,
    strong_ledger: Any,
    cv_ledger: MaterializedCVLedger,
    initial_checkpoint: Path,
    contracts: Mapping[str, Mapping[str, Any]],
    qualification: Mapping[str, Any],
    physics: Any,
    config: Any,
    device: torch.device,
    cv_scale: float,
    source_identity: str,
    physics_program_sha256: str,
    physics_object_sha256: str,
) -> dict[str, Any]:
    if len(schedule) != FULL_ACCEPTED_UPDATES // BLOCK_SIZE:
        raise ValueError("LF9 no-filter schedule length drift")
    directory = root / CONTROL_DIRECTORY
    directory.mkdir(parents=True, exist_ok=False)
    model, _ = load_dev_r_model(
        initial_checkpoint, physics=physics, config=config, device=device, contracts=contracts
    )
    set_phase_trainable(model, False)
    optimizer = _make_optimizer(model)
    phase_initial = _phase_state_sha256(model)
    accepted = 0
    numerical_valid = True
    last_train: dict[str, Any] | None = None
    with (directory / "telemetry.jsonl").open("x", encoding="utf-8", newline="\n") as telemetry, (directory / "batch_ledger.jsonl").open("x", encoding="utf-8", newline="\n") as batches:
        for block, learning_rate in enumerate(schedule, start=1):
            for group in optimizer.param_groups:
                group["lr"] = float(learning_rate)
            start = accepted + 1
            if start == PHASE_FREEZE_STEPS + 1:
                if _phase_state_sha256(model) != phase_initial or _phase_optimizer_state_entries(model, optimizer) != 0:
                    raise RuntimeError("LF9 no-filter phase-freeze identity drift")
            set_phase_trainable(model, start > PHASE_FREEZE_STEPS)
            strong_hashes: list[str] = []
            cv_hashes: list[str] = []
            for step in range(start, start + BLOCK_SIZE):
                strong_batch = strong_ledger.physics_batch(step, device=device)
                cv_bounds = cv_ledger.training_bounds(step, device=device)
                ok, last_train = routed_optimizer_step(
                    model, optimizer, batch=strong_batch, config=config,
                    thermal_mode=selected_arm,
                    cv_bounds=cv_bounds if selected_arm == ER_CV else None,
                    cv_scale=cv_scale if selected_arm == ER_CV else None,
                )
                strong_hashes.append(strong_batch.batch_sha256)
                cv_hashes.append(cv_ledger.training_step_sha256[step - 1])
                _append(batches, {
                    "arm": "NO_FILTER_CONTROL", "selected_physics_arm": selected_arm,
                    "accepted_update": step, "learning_rate": float(learning_rate),
                    "strong_batch_sha256": strong_batch.batch_sha256,
                    "cv_batch_sha256": cv_ledger.training_step_sha256[step - 1],
                })
                if not ok:
                    numerical_valid = False
                    break
            if not numerical_valid:
                break
            accepted += BLOCK_SIZE
            _append(telemetry, {
                "arm": "NO_FILTER_CONTROL", "selected_physics_arm": selected_arm,
                "block": block, "accepted_updates": accepted,
                "learning_rate": float(learning_rate), "train": last_train,
                "strong_cv_block_sha256": _block_sha256(strong_hashes, cv_hashes),
                "competence_audit_performed": False,
            })
    endpoint_blind = fixed_blind_metrics(
        model, strong_ledger, cv_ledger, config,
        cv_scale=cv_scale, device=device,
    )
    baseline_blind = qualification["blind_baseline"]
    ratios = _ratios(endpoint_blind, baseline_blind)
    own = _own_key(selected_arm)
    valid = bool(
        numerical_valid and accepted == FULL_ACCEPTED_UPDATES
        and all(math.isfinite(float(value)) for value in endpoint_blind.values())
    )
    result = {
        "arm": "NO_FILTER_CONTROL", "selected_physics_arm": selected_arm,
        "identity_valid": valid, "numerical_valid": valid, "endpoint_valid": valid,
        "accepted_updates": accepted, "attempted_updates": accepted,
        "accepted_blocks": accepted // BLOCK_SIZE,
        "accepted_learning_rates": list(schedule),
        "disposition": "COMPLETE" if valid else "POSTSTEP_IDENTITY_INVALID",
        "safety_gate": {"status": "PENDING_POST_SHUTDOWN_LOCAL_ADJUDICATION"},
        "strict_gate": {"status": "PENDING_POST_SHUTDOWN_LOCAL_ADJUDICATION"},
        "blind": endpoint_blind, "blind_ratios_to_DEV_R": ratios,
        "own_ratio": ratios[own], "cv1_ratio": ratios["CV1"], "cv4_ratio": ratios["CV4"],
        "final_audit": {"blind": endpoint_blind, "medium": "NOT_READ_ON_CLOUD"},
        "intermediate_medium_audit_used": False,
        "endpoint_medium_audit_used": False,
        "filter_used": False, "rollback_used": False,
    }
    checkpoint, prediction = _save_model_artifacts(
        directory, prefix="", model=model, optimizer=optimizer, config=config,
        role=f"NO_FILTER_CONTROL:{selected_arm}", accepted=accepted, attempted=accepted,
        source_identity=source_identity,
        physics_program_sha256=physics_program_sha256,
        physics_object_sha256=physics_object_sha256,
        disposition=result["disposition"], accepted_learning_rates=schedule,
    )
    result["checkpoint_sha256"] = _sha256_path(checkpoint)
    result["prediction_sha256"] = _sha256_path(prediction)
    _write_json_exclusive(directory / "gate.json", result)
    _write_json_exclusive(directory / "exit.json", {
        "returncode": 0 if valid else 1, "accepted_updates": accepted,
        "numerical_valid": valid,
    })
    del optimizer, model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return result


def execute_gpu_campaign(
    *,
    output_root: Path,
    medium_carrier: Path,
    initial_checkpoint: Path,
    strong_ledger: Path,
    cv_ledger: Path,
    cv_ledger_manifest: Path,
    cpu_qualification_path: Path,
    source_identity: str,
    device_name: str,
) -> dict[str, Any]:
    """Execute both matched screens and the frozen conditional continuations."""

    contracts = load_contracts()
    qualification = read_cpu_qualification(cpu_qualification_path)
    bundle_prefix = "LF9-BUNDLE-"
    bundle_digest = source_identity[len(bundle_prefix):] if source_identity.startswith(bundle_prefix) else ""
    if len(bundle_digest) != 64 or bundle_digest != bundle_digest.upper() or any(value not in "0123456789ABCDEF" for value in bundle_digest):
        raise ValueError("LF9 source identity must be the content-addressed deployment bundle")
    expected_contracts = contract_identity()
    if qualification.get("contracts") != expected_contracts:
        raise ValueError("LF9 CPU qualification contract identity drift")
    if not device_name.startswith("cuda") or not torch.cuda.is_available():
        raise RuntimeError("LF9 requires CUDA")
    device = torch.device(device_name)
    gpu_name = torch.cuda.get_device_name(device)
    if gpu_name != "Tesla V100-PCIE-32GB":
        raise RuntimeError("LF9 requires Tesla V100-PCIE-32GB")
    root = Path(output_root).resolve()
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise FileExistsError(f"LF9 output root must be empty: {root}")
    root.mkdir(parents=True, exist_ok=True)

    config = build_training_config(device_name)
    physics, physics_program_sha256, physics_object_sha256 = load_case_physics(config.case_control)
    dataset = load_medium_dataset(Path(medium_carrier), physics=physics, contracts=contracts)
    if dataset.partition_sha256 != EXPECTED_PARTITION_SHA256:
        raise ValueError("LF9 medium partition drift")
    strong = lf7.MaterializedPhysicsLedger(
        Path(strong_ledger), contracts=_runtime_contracts(contracts),
        qualification={"ledger": qualification["strong_ledger"]},
    )
    cv = MaterializedCVLedger(
        Path(cv_ledger), Path(cv_ledger_manifest),
        contracts=contracts, qualification=qualification,
    )
    cv_scale = float(qualification["cv_normalization"]["s_cv"])
    if not math.isfinite(cv_scale) or cv_scale <= 0.0:
        raise ValueError("LF9 frozen CV scale is invalid")

    started = datetime.now(timezone.utc).isoformat()
    runtimes: dict[str, dict[str, Any]] = {}
    arms: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, str]] = []
    for arm in ARM_ORDER:
        _seed_all(17)
        runtime: dict[str, Any] | None = None
        try:
            runtime = _make_runtime(
                arm=arm, root=root, dataset=dataset, strong_ledger=strong,
                cv_ledger=cv, initial_checkpoint=Path(initial_checkpoint),
                contracts=contracts, qualification=qualification,
                physics=physics, config=config, device=device, cv_scale=cv_scale,
            )
            _advance_filtered(
                runtime, target_accepted=SCREEN_ACCEPTED_UPDATES,
                attempted_cap=SCREEN_ATTEMPTED_CAP, dataset=dataset,
                strong_ledger=strong, cv_ledger=cv, config=config,
                cv_scale=cv_scale, device=device,
            )
            result = _endpoint_result(runtime, target=SCREEN_ACCEPTED_UPDATES)
            result["screen_go"] = screen_go(result)
            _persist_endpoint(
                runtime, result, prefix="screen-", config=config,
                source_identity=source_identity,
                physics_program_sha256=physics_program_sha256,
                physics_object_sha256=physics_object_sha256,
            )
            _write_json_exclusive(runtime["directory"] / "screen-exit.json", {
                "returncode": 0, "accepted_updates": result["accepted_updates"],
                "screen_go": result["screen_go"], "identity_valid": True,
            })
            runtimes[arm] = runtime
            arms[arm] = result
        except Exception as exc:
            result = _invalid_arm_result(arm, exc)
            if runtime is not None:
                result["accepted_updates"] = int(runtime["accepted"])
                result["attempted_updates"] = int(runtime["attempted"])
                result["accepted_blocks"] = int(runtime["accepted"]) // BLOCK_SIZE
                result["accepted_learning_rates"] = list(runtime["accepted_lrs"])
            directory = root / ARM_DIRECTORIES[arm]
            directory.mkdir(parents=True, exist_ok=True)
            if not (directory / "screen-gate.json").exists():
                _write_json_exclusive(directory / "screen-gate.json", result)
            if not (directory / "screen-exit.json").exists():
                _write_json_exclusive(directory / "screen-exit.json", {
                    "returncode": 1, "identity_valid": False,
                    "error_type": type(exc).__name__,
                })
            arms[arm] = result
            errors.append({"arm": arm, "type": type(exc).__name__, "message": str(exc)})

    decision = adjudicate_screens(arms)
    selected = decision["selected_arm"] if not decision["identity_invalid_arms"] else None
    full: dict[str, Any] = {"executed": False, "reason": "NO_VALID_MATCHED_SCREEN_SELECTION"}
    control: dict[str, Any] = {"executed": False, "reason": "PRELOCAL_INTERNAL_PARETO_NOT_REACHED"}
    if selected is not None:
        runtime = runtimes[selected]
        try:
            _advance_filtered(
                runtime, target_accepted=FULL_ACCEPTED_UPDATES,
                attempted_cap=FULL_ATTEMPTED_CAP, dataset=dataset,
                strong_ledger=strong, cv_ledger=cv, config=config,
                cv_scale=cv_scale, device=device,
            )
            full = _endpoint_result(runtime, target=FULL_ACCEPTED_UPDATES)
            full["executed"] = True
            full["prelocal_internal_pareto"] = prelocal_internal_pareto(full)
            full["complete_internal_pinn_pareto"] = "PENDING_POST_SHUTDOWN_LOCAL_EVALUATION"
            if runtime["accepted"] < FULL_ACCEPTED_UPDATES:
                full["scientific_disposition"] = _full_path_disposition(full)
            else:
                full["scientific_disposition"] = (
                    "PRELOCAL_INTERNAL_PARETO" if full["prelocal_internal_pareto"]
                    else "FULL_PATH_PHYSICS_OR_COMPETENCE_GATE_MISSED"
                )
            _persist_endpoint(
                runtime, full, prefix="full-", config=config,
                source_identity=source_identity,
                physics_program_sha256=physics_program_sha256,
                physics_object_sha256=physics_object_sha256,
            )
            _write_json_exclusive(runtime["directory"] / "full-exit.json", {
                "returncode": 0, "accepted_updates": full["accepted_updates"],
                "prelocal_internal_pareto": full["prelocal_internal_pareto"],
            })
            if full["prelocal_internal_pareto"]:
                _seed_all(17)
                control = _run_no_filter_control(
                    selected_arm=selected, schedule=full["accepted_learning_rates"],
                    root=root, strong_ledger=strong, cv_ledger=cv,
                    initial_checkpoint=Path(initial_checkpoint), contracts=contracts,
                    qualification=qualification, physics=physics, config=config,
                    device=device, cv_scale=cv_scale, source_identity=source_identity,
                    physics_program_sha256=physics_program_sha256,
                    physics_object_sha256=physics_object_sha256,
                )
                control["executed"] = True
        except Exception as exc:
            full = {
                "executed": True, "identity_valid": False,
                "numerical_valid": False, "endpoint_valid": False,
                "accepted_updates": int(runtime["accepted"]),
                "attempted_updates": int(runtime["attempted"]),
                "accepted_learning_rates": list(runtime["accepted_lrs"]),
                "disposition": "POSTSTEP_IDENTITY_INVALID",
                "prelocal_internal_pareto": False,
                "complete_internal_pinn_pareto": False,
                "error": {"type": type(exc).__name__, "message": str(exc)},
            }
            errors.append({"arm": f"{selected}:FULL", "type": type(exc).__name__, "message": str(exc)})

    schedule_attribution = "NOT_TRIGGERED"
    if control.get("executed"):
        schedule_attribution = "PENDING_POST_SHUTDOWN_LOCAL_ADJUDICATION"
    artifacts: dict[str, Any] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "run_summary.json":
            artifacts[path.relative_to(root).as_posix()] = _artifact_record(path, root)
    summary = {
        "schema_id": "phk-v23-lf9-reference-blind-run-summary-v1",
        "task_id": TASK_ID, "title": TITLE,
        "status": "LF9_POSTSTEP_IDENTITY_INVALID" if errors else "LF9_REFERENCE_BLIND_GPU_CAMPAIGN_COMPLETE",
        "started_at_utc": started,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_identity": source_identity, "gpu": gpu_name,
        "dtype": "FLOAT64", "seed": 17,
        "arms": arms,
        "screen_outcomes": decision["screen_outcomes"],
        "mechanism_outcome": decision["mechanism_outcome"],
        "selected_arm": selected,
        "full_refinement": full,
        "control": control,
        "schedule_attribution_prelocal": schedule_attribution,
        "complete_internal_pinn_pareto": "PENDING_POST_SHUTDOWN_LOCAL_EVALUATION" if full.get("prelocal_internal_pareto") else False,
        "errors": errors,
        "strong_ledger": {
            "file_sha256": _sha256_path(Path(strong_ledger)),
            "semantic_sha256": EXPECTED_STRONG_SEMANTIC_SHA256,
            "physics_1200_sha256": strong.physics_sha256,
            "fixed_blind_pool_sha256": EXPECTED_FIXED_POOL_SHA256,
        },
        "cv_ledger": {
            "file_sha256": _sha256_path(Path(cv_ledger)),
            "manifest_sha256": _sha256_path(Path(cv_ledger_manifest)),
            "training_rolling_sha256": cv.training_rolling_sha256,
        },
        "cv_normalization": qualification["cv_normalization"],
        "artifacts": artifacts,
        "medium_gradient_used": False, "runtime_sampling_used": False,
        "fine_extra_lf_only_evaluator_stress_read": False,
    }
    _write_json_exclusive(root / "run_summary.json", summary)
    return summary


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--medium-carrier", type=Path, required=True)
    parser.add_argument("--initial-checkpoint", type=Path, required=True)
    parser.add_argument("--strong-ledger", type=Path, required=True)
    parser.add_argument("--cv-ledger", type=Path, required=True)
    parser.add_argument("--cv-ledger-manifest", type=Path, required=True)
    parser.add_argument("--cpu-qualification", type=Path, required=True)
    parser.add_argument("--source-identity", required=True)
    parser.add_argument("--device", default="cuda:0")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    summary = execute_gpu_campaign(
        output_root=args.output_root, medium_carrier=args.medium_carrier,
        initial_checkpoint=args.initial_checkpoint, strong_ledger=args.strong_ledger,
        cv_ledger=args.cv_ledger, cv_ledger_manifest=args.cv_ledger_manifest,
        cpu_qualification_path=args.cpu_qualification,
        source_identity=args.source_identity, device_name=args.device,
    )
    print(json.dumps({
        "status": summary["status"],
        "mechanism_outcome": summary["mechanism_outcome"],
        "selected_arm": summary["selected_arm"],
        "control_executed": bool(summary["control"].get("executed")),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ARM_ORDER", "BLOCK_SIZE", "CONTROL_DIRECTORY", "ER_CV", "ER_S",
    "ETA0", "FULL_ACCEPTED_UPDATES", "LR_LADDER", "MaterializedCVLedger",
    "PHASE_FREEZE_STEPS", "SCREEN_ACCEPTED_UPDATES", "TASK_ID", "TITLE",
    "TrainingSnapshot", "adjudicate_screens", "competence_gate",
    "contract_identity", "execute_gpu_campaign", "field_parameter_groups",
    "fixed_blind_metrics", "gauss_legendre_2", "load_contracts",
    "load_dev_r_model", "main", "prelocal_internal_pareto",
    "read_cpu_qualification", "restore_snapshot", "routed_field_gradients",
    "routed_optimizer_step", "routed_physics_objectives", "screen_go",
    "set_phase_trainable", "snapshot_digest", "strong_thermal_normalized_mse",
    "take_snapshot", "thermal_control_volume_residual",
]
