"""Bounded read-only CPU diagnostics for the PHK-V2.3 R0A contract."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import time
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .phk_benchmark import PhkControl
from .phk_v21_benchmark import load_phk_v21_physical, read_phk_v21_result
from .phk_v22r_pinn import (
    FIELD_NAMES,
    FrequencyBand,
    PhkCollocationSampler,
    PhkV22RArm,
    PhkV22RModel,
    boundary_residuals,
    evaluate_fields,
    initial_residuals,
    interior_diagnostic_terms,
    normalized_residual_loss,
)
from .phk_v22r_prediction import _load_model
from .phk_v22r_training import BOUNDARY_SCALES, INITIAL_SCALES, PDE_SCALES


ROOT = Path(__file__).resolve().parents[1]
PROGRAM_CONTRACT_PATH = ROOT / "configs" / "phk_v23" / "program_contract.json"
METHOD_CONTRACT_PATH = ROOT / "configs" / "phk_v23" / "method_contract.json"
DIAGNOSTIC_CONTRACT_PATH = (
    ROOT / "configs" / "phk_v23" / "r0a_diagnostic_contract.json"
)
R0A_ARTIFACT_PATH = (
    ROOT
    / "docs"
    / "experiment"
    / "artifacts"
    / "20260830T-phk-v23-r0a-cpu-001.json"
)
PHYSICAL_PROGRAM_PATH = ROOT / "configs" / "phk_v21" / "program_contract.json"
PHYSICAL_OBJECT_PATH = ROOT / "configs" / "phk_v21" / "object_numerical_contract.json"
LEGACY_PROGRAM_PATH = ROOT / "configs" / "phk_v2" / "program_contract.json"
LEGACY_OBJECT_PATH = ROOT / "configs" / "phk_v2" / "object_numerical_contract.json"


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"contract must contain one JSON object: {path}")
    return payload


def load_contract_bundle() -> dict[str, dict[str, Any]]:
    """Load and fail-close the three versioned R0A contracts."""

    program = _read_json(PROGRAM_CONTRACT_PATH)
    method = _read_json(METHOD_CONTRACT_PATH)
    diagnostic = _read_json(DIAGNOSTIC_CONTRACT_PATH)
    if program.get("schema_id") != "phk-v23-program-contract-r0a-v1":
        raise ValueError("unsupported PHK-V2.3 R0A program contract")
    if method.get("schema_id") != "phk-v23-method-contract-r0a-v1":
        raise ValueError("unsupported PHK-V2.3 R0A method contract")
    if diagnostic.get("schema_id") != "phk-v23-r0a-diagnostic-contract-v1":
        raise ValueError("unsupported PHK-V2.3 R0A diagnostic contract")
    authorization = program["authorization"]
    required_true = {
        "r0a_cpu_diagnostic_authorized",
        "selective_commit_and_push_authorized",
    }
    required_false = {
        "optimizer_or_parameter_update_authorized",
        "gpu_or_cloud_authorized",
        "r0b_authorized",
        "r1_authorized",
        "r2_or_pjgr_authorized",
        "stress_reference_access_authorized",
        "submission_or_external_contact_authorized",
    }
    if any(authorization.get(name) is not True for name in required_true):
        raise PermissionError("R0A program authorization is incomplete")
    if any(authorization.get(name) is not False for name in required_false):
        raise PermissionError("R0A program contains an out-of-scope authorization")
    execution = diagnostic["execution"]
    if execution != {
        "device": "CPU",
        "dtype": "FLOAT64",
        "cuda_visible_devices": "",
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "parameter_updates": 0,
        "checkpoint_selection": False,
        "maximum_wall_seconds": 14400,
        "maximum_runs": 1,
    }:
        raise ValueError("R0A execution contract drift")
    if diagnostic["stress_reference"]["fields_or_metrics_may_be_read"] is not False:
        raise PermissionError("stress reference contract is not fail-closed")
    return {"program": program, "method": method, "diagnostic": diagnostic}


def assert_cpu_only_environment() -> str:
    """Normalize PowerShell's unset representation of an empty CUDA mask."""

    visible_devices = os.environ.get("CUDA_VISIBLE_DEVICES")
    if visible_devices not in {None, ""}:
        raise PermissionError("R0A requires CUDA_VISIBLE_DEVICES to be empty")
    return ""


def assert_one_time_r0a_target(output_path: Path) -> None:
    """Fail before checkpoint I/O when the one authorized artifact is not creatable."""

    if Path(output_path).resolve() != R0A_ARTIFACT_PATH.resolve():
        raise PermissionError("R0A output path differs from the frozen one-time artifact")
    if R0A_ARTIFACT_PATH.exists():
        raise FileExistsError(f"R0A artifact already exists: {R0A_ARTIFACT_PATH}")


def _absolute_contract_path(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PermissionError("R0A source path escaped the repository") from exc
    return path


def reject_non_nominal_reference_access(path: Path) -> None:
    """Refuse any reference path other than the one frozen nominal carrier."""

    contract = load_contract_bundle()["diagnostic"]
    nominal = _absolute_contract_path(contract["nominal_reference"]["path"])
    if Path(path).resolve() != nominal:
        raise PermissionError("R0A can access only the frozen nominal development reference")


def load_nominal_development_reference():
    """Open the frozen FULL nominal reference; no path or control is user-selectable."""

    bundle = load_contract_bundle()
    reference_contract = bundle["diagnostic"]["nominal_reference"]
    path = _absolute_contract_path(reference_contract["path"])
    reject_non_nominal_reference_access(path)
    if _sha256_path(path) != reference_contract["sha256"]:
        raise ValueError("nominal development reference hash mismatch")
    physical = load_phk_v21_physical(
        program_path=PHYSICAL_PROGRAM_PATH,
        object_path=PHYSICAL_OBJECT_PATH,
        legacy_program_path=LEGACY_PROGRAM_PATH,
        legacy_object_path=LEGACY_OBJECT_PATH,
    )
    result = read_phk_v21_result(path, physical=physical)
    if result.case.control is not PhkControl.FULL:
        raise ValueError("R0A nominal reference is not the FULL case")
    return result


def _tensor_bytes(tensor: torch.Tensor) -> bytes:
    return tensor.detach().cpu().contiguous().numpy().tobytes(order="C")


def _digest_named_tensors(items: Sequence[tuple[str, torch.Tensor]]) -> str:
    digest = hashlib.sha256()
    for name, tensor in sorted(items, key=lambda item: item[0]):
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(b"\0")
        digest.update(json.dumps(list(tensor.shape), separators=(",", ":")).encode("ascii"))
        digest.update(b"\0")
        digest.update(_tensor_bytes(tensor))
    return digest.hexdigest().upper()


def state_identity(model: PhkV22RModel) -> dict[str, str]:
    parameters = list(model.named_parameters())
    buffers = list(model.named_buffers())
    combined = list(model.state_dict().items())
    return {
        "parameters_sha256": _digest_named_tensors(parameters),
        "buffers_sha256": _digest_named_tensors(buffers),
        "combined_state_sha256": _digest_named_tensors(combined),
    }


def snapshot_state(model: PhkV22RModel) -> dict[str, torch.Tensor]:
    return {
        name: tensor.detach().cpu().clone()
        for name, tensor in model.state_dict().items()
    }


def assert_state_unchanged(
    model: PhkV22RModel,
    before: Mapping[str, torch.Tensor],
    before_identity: Mapping[str, str],
) -> dict[str, str]:
    after = model.state_dict()
    if set(after) != set(before):
        raise RuntimeError("R0A changed model state keys")
    for name, tensor in after.items():
        if not torch.equal(tensor.detach().cpu(), before[name]):
            raise RuntimeError(f"R0A changed model state tensor: {name}")
    identity = state_identity(model)
    if identity != dict(before_identity):
        raise RuntimeError("R0A changed parameter or buffer bytes")
    if any(parameter.grad is not None for parameter in model.parameters()):
        raise RuntimeError("R0A left a persistent parameter gradient")
    return identity


def build_r0a_pool(
    model: PhkV22RModel,
    contracts: Mapping[str, Mapping[str, Any]],
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, dict[str, Any]]:
    """Build the reference-independent frozen scalar and gradient pools."""

    pool_contract = contracts["method"]["diagnostic_pool"]
    sampler = PhkCollocationSampler(
        physics=model.physics,
        windows=tuple(tuple(item) for item in pool_contract["windows"]),
        seed=int(pool_contract["seed"]),
    )
    total = int(pool_contract["scalar_points_total"])
    pool = sampler.interior_uniform(
        total,
        active_windows=int(pool_contract["active_windows"]),
        dtype=torch.float64,
        device=torch.device("cpu"),
    ).detach()
    per_window = int(pool_contract["scalar_points_per_window"])
    gradient_per_window = int(pool_contract["gradient_points_per_window"])
    indices = torch.cat(
        [
            torch.arange(
                window * per_window,
                window * per_window + gradient_per_window,
                dtype=torch.int64,
            )
            for window in range(int(pool_contract["active_windows"]))
        ]
    )
    gradient_pool = pool.index_select(0, indices).detach()
    observed = {
        "pool_sha256_float64_bytes": _sha256_bytes(_tensor_bytes(pool)),
        "gradient_indices_sha256_int64_bytes": _sha256_bytes(_tensor_bytes(indices)),
        "gradient_subset_sha256_float64_bytes": _sha256_bytes(
            _tensor_bytes(gradient_pool)
        ),
    }
    for name, value in observed.items():
        if value != pool_contract[name]:
            raise ValueError(f"frozen R0A diagnostic pool identity mismatch: {name}")
    boundary_sampler = PhkCollocationSampler(
        physics=model.physics,
        windows=tuple(tuple(item) for item in pool_contract["windows"]),
        seed=int(pool_contract["boundary_pool_seed"]),
    )
    boundary = boundary_sampler.boundary(
        int(pool_contract["boundary_points_per_side"]),
        active_windows=int(pool_contract["active_windows"]),
        dtype=torch.float64,
        device=torch.device("cpu"),
    )
    identity = {
        "algorithm": pool_contract["algorithm"],
        "seed": int(pool_contract["seed"]),
        "scalar_points_total": int(pool.shape[0]),
        "scalar_points_per_window": per_window,
        "gradient_points_total": int(gradient_pool.shape[0]),
        "gradient_points_per_window": gradient_per_window,
        "window_counts": [
            int(
                torch.count_nonzero(
                    (pool[:, 2] >= start) & (pool[:, 2] < end)
                )
            )
            for start, end in pool_contract["windows"]
        ],
        "gradient_window_counts": [
            int(
                torch.count_nonzero(
                    (gradient_pool[:, 2] >= start)
                    & (gradient_pool[:, 2] < end)
                )
            )
            for start, end in pool_contract["windows"]
        ],
        **observed,
    }
    return pool, gradient_pool, indices, {"batches": boundary, "identity": identity}


def _finite_float(value: torch.Tensor | float) -> float:
    number = float(value.detach().cpu()) if isinstance(value, torch.Tensor) else float(value)
    if not math.isfinite(number):
        raise FloatingPointError("R0A diagnostic produced a non-finite scalar")
    return number


def summarize_tensor(tensor: torch.Tensor, quantiles: Sequence[float]) -> dict[str, Any]:
    flat = tensor.detach().reshape(-1).to(device="cpu", dtype=torch.float64)
    if flat.numel() == 0:
        return {"count": 0}
    if not bool(torch.isfinite(flat).all()):
        raise FloatingPointError("R0A diagnostic tensor contains non-finite values")
    result: dict[str, Any] = {
        "count": int(flat.numel()),
        "min": _finite_float(torch.min(flat)),
        "max": _finite_float(torch.max(flat)),
        "mean": _finite_float(torch.mean(flat)),
        "rms": _finite_float(torch.sqrt(torch.mean(flat.square()))),
    }
    result["quantiles"] = {
        f"q{int(round(100 * quantile)):02d}": _finite_float(
            torch.quantile(flat, float(quantile))
        )
        for quantile in quantiles
    }
    return result


def _roi_mask(coordinates: torch.Tensor, diagnostic: Mapping[str, Any]) -> torch.Tensor:
    roi = diagnostic["measurements"]["roi"]
    return (
        (coordinates[:, 0].abs() <= float(roi["abs_x_max"]))
        & (coordinates[:, 1] >= float(roi["z_min"]))
        & (coordinates[:, 1] <= float(roi["z_max"]))
    )


def summarize_model_mapping(
    model: PhkV22RModel,
    pool: torch.Tensor,
    boundary: Mapping[str, torch.Tensor],
    contracts: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, torch.Tensor]]:
    """Measure A-C and retain only detached values needed by teacher probes."""

    diagnostic = contracts["diagnostic"]
    method = contracts["method"]
    quantiles = tuple(float(item) for item in diagnostic["measurements"]["quantiles"])
    activity_threshold = float(
        diagnostic["measurements"]["phase_activity_threshold"]
    )
    windows = method["diagnostic_pool"]["windows"]
    per_window = int(method["diagnostic_pool"]["scalar_points_per_window"])
    field_mapping: dict[str, Any] = {"per_window": []}
    phase_terms: dict[str, Any] = {"per_window": []}
    electrothermal: dict[str, Any] = {"per_window": []}
    teacher_parts: dict[str, list[torch.Tensor]] = {
        name: []
        for name in (
            "coordinates",
            "temperature",
            "phase",
            "grad_potential_x",
            "grad_potential_z",
            "lap_phase",
            "phase_time",
            "thermal_nonjoule",
            "base_phase_residual",
            "base_thermal_residual",
            "base_joule",
        )
    }
    for window_index, (start, end) in enumerate(windows):
        window_pool = pool[
            window_index * per_window : (window_index + 1) * per_window
        ].detach()
        output = model.read_only_output_diagnostics(window_pool)
        fields = {
            name: output.output.fields[:, index : index + 1]
            for index, name in enumerate(FIELD_NAMES)
        }
        terms = interior_diagnostic_terms(model, window_pool)
        bundle = evaluate_fields(model, window_pool)
        roi = _roi_mask(window_pool, diagnostic)
        field_record: dict[str, Any] = {
            "window_index": window_index,
            "time_bounds": [float(start), float(end)],
            "fields": {
                name: summarize_tensor(value, quantiles)
                for name, value in fields.items()
            },
            "latents": {
                name: summarize_tensor(value, quantiles)
                for name, value in output.latents.items()
            },
            "raw_latent_sigmoid_derivatives": {
                name: summarize_tensor(value, quantiles)
                for name, value in output.raw_latent_sigmoid_derivatives.items()
            },
            "analytic_output_jacobians": {
                name: summarize_tensor(value, quantiles)
                for name, value in output.analytic_output_jacobians.items()
            },
            "phase_activity_fraction": _finite_float(
                torch.mean((fields["phase"] >= activity_threshold).to(torch.float64))
            ),
            "phase_activity_roi_fraction": _finite_float(
                torch.mean(
                    (fields["phase"][roi] >= activity_threshold).to(torch.float64)
                )
            )
            if bool(torch.any(roi))
            else None,
            "joule_density": summarize_tensor(terms["joule_density"], quantiles),
        }
        field_mapping["per_window"].append(field_record)
        phase_record = {
            "window_index": window_index,
            "time_bounds": [float(start), float(end)],
            "terms": {
                name: summarize_tensor(terms[name], quantiles)
                for name in (
                    "phase_time",
                    "phase_diffusion",
                    "phase_reaction",
                    "phase_kinetic_rhs",
                    "phase_residual",
                )
            },
            "roi_terms": {
                name: summarize_tensor(terms[name][roi], quantiles)
                for name in (
                    "phase_time",
                    "phase_diffusion",
                    "phase_reaction",
                    "phase_kinetic_rhs",
                    "phase_residual",
                )
            },
            "positive_growth_roi_fraction": _finite_float(
                torch.mean((terms["phase_kinetic_rhs"][roi] > 0.0).to(torch.float64))
            )
            if bool(torch.any(roi))
            else None,
        }
        phase_terms["per_window"].append(phase_record)
        margin = fields["temperature"] - model.physics.theta_transition
        electro_record = {
            "window_index": window_index,
            "time_bounds": [float(start), float(end)],
            "electric_terms": {
                name: summarize_tensor(terms[name], quantiles)
                for name in (
                    "electric_conductivity_laplacian",
                    "electric_conductivity_gradient_x",
                    "electric_conductivity_gradient_z",
                    "electric_residual",
                )
            },
            "thermal_terms": {
                name: summarize_tensor(terms[name], quantiles)
                for name in (
                    "thermal_time",
                    "thermal_latent",
                    "thermal_diffusion",
                    "thermal_cooling",
                    "thermal_joule",
                    "thermal_residual",
                )
            },
            "conductivity": summarize_tensor(terms["conductivity"], quantiles),
            "mobility": summarize_tensor(terms["mobility"], quantiles),
            "joule_density": summarize_tensor(terms["joule_density"], quantiles),
            "joule_density_roi": summarize_tensor(
                terms["joule_density"][roi], quantiles
            )
            if bool(torch.any(roi))
            else None,
            "temperature_margin_to_transition": summarize_tensor(margin, quantiles),
            "temperature_above_transition_fraction": _finite_float(
                torch.mean((margin >= 0.0).to(torch.float64))
            ),
        }
        electrothermal["per_window"].append(electro_record)
        teacher_parts["coordinates"].append(window_pool.detach().cpu())
        teacher_parts["temperature"].append(fields["temperature"].detach().cpu())
        teacher_parts["phase"].append(fields["phase"].detach().cpu())
        teacher_parts["grad_potential_x"].append(
            bundle.gradients["potential"][:, 0:1].detach().cpu()
        )
        teacher_parts["grad_potential_z"].append(
            bundle.gradients["potential"][:, 1:2].detach().cpu()
        )
        teacher_parts["lap_phase"].append(
            (
                bundle.diagonal_second["phase"]["xx"]
                + bundle.diagonal_second["phase"]["zz"]
            ).detach().cpu()
        )
        teacher_parts["phase_time"].append(
            bundle.gradients["phase"][:, 2:3].detach().cpu()
        )
        teacher_parts["thermal_nonjoule"].append(
            (
                terms["thermal_time"]
                + terms["thermal_latent"]
                + terms["thermal_diffusion"]
                + terms["thermal_cooling"]
            ).detach().cpu()
        )
        teacher_parts["base_phase_residual"].append(
            terms["phase_residual"].detach().cpu()
        )
        teacher_parts["base_thermal_residual"].append(
            terms["thermal_residual"].detach().cpu()
        )
        teacher_parts["base_joule"].append(terms["joule_density"].detach().cpu())
        del output, fields, terms, bundle
        gc.collect()
    boundary_record: dict[str, Any] = {}
    for side, coordinates in boundary.items():
        output = model.read_only_output_diagnostics(coordinates)
        waveform = model.physics.waveform(coordinates[:, 2:3])
        active = waveform[:, 0].abs() > 1.0e-12
        if side == "bottom":
            active = active & (
                coordinates[:, 0].abs() <= model.physics.heater_half_width
            )
        raw_sigmoid = torch.sigmoid(output.latents["potential"])
        derivative = output.raw_latent_sigmoid_derivatives["potential"]
        record: dict[str, Any] = {
            "active_pulse_points": int(torch.count_nonzero(active)),
            "temperature_top_is_structural_hard_zero": side == "top",
        }
        if bool(torch.any(active)):
            desired = 1.0 if side == "top" else 0.0 if side == "bottom" else None
            record.update(
                {
                    "potential_latent": summarize_tensor(
                        output.latents["potential"][active], quantiles
                    ),
                    "potential_sigmoid": summarize_tensor(raw_sigmoid[active], quantiles),
                    "potential_sigmoid_derivative": summarize_tensor(
                        derivative[active], quantiles
                    ),
                    "sigmoid_derivative_below_0_01_fraction": _finite_float(
                        torch.mean((derivative[active] < 0.01).to(torch.float64))
                    ),
                    "dirichlet_target": desired,
                    "dirichlet_sigmoid_error": summarize_tensor(
                        raw_sigmoid[active] - float(desired), quantiles
                    )
                    if desired is not None
                    else None,
                }
            )
        boundary_record[side] = record
    field_mapping["potential_boundary_saturation"] = boundary_record
    detached_teacher = {
        name: torch.cat(values, dim=0) for name, values in teacher_parts.items()
    }
    return field_mapping, phase_terms, electrothermal, detached_teacher


def _merged_boundary_items(
    model: PhkV22RModel, batches: Mapping[str, torch.Tensor]
) -> list[tuple[str, torch.Tensor]]:
    items: list[tuple[str, torch.Tensor]] = []
    for side, coordinates in batches.items():
        for name, value in boundary_residuals(model, coordinates, side=side).items():
            items.append((f"{side}:{name}", value))
    return items


def _loss_for_row(
    model: PhkV22RModel,
    row: str,
    gradient_pool: torch.Tensor,
    boundary: Mapping[str, torch.Tensor],
) -> torch.Tensor:
    if row.endswith("_PDE"):
        name = row.removesuffix("_PDE").lower()
        terms = interior_diagnostic_terms(model, gradient_pool)
        residual = terms[f"{name}_residual"]
        return torch.mean((residual / PDE_SCALES[name]).square()) / 3.0
    items = _merged_boundary_items(model, boundary)
    total_items = len(items)
    if total_items == 0:
        raise RuntimeError("R0A boundary pool produced no residual items")
    prefix = {
        "ELECTRIC_BC": ("bc_potential", "bc_electric"),
        "THERMAL_BC": ("bc_temperature",),
        "PHASE_BC": ("bc_phase",),
    }[row]
    selected = []
    for qualified_name, value in items:
        base_name = qualified_name.split(":", 1)[1]
        if base_name.startswith(prefix):
            selected.append(torch.mean((value / BOUNDARY_SCALES[base_name]).square()))
    if not selected:
        raise RuntimeError(f"R0A boundary group has no residual item: {row}")
    return 5.0 * torch.stack(selected).sum() / float(total_items)


def _flatten_gradients(
    gradients: Sequence[torch.Tensor | None],
    parameters: Sequence[torch.nn.Parameter],
) -> torch.Tensor:
    pieces = []
    for gradient, parameter in zip(gradients, parameters, strict=True):
        pieces.append(
            torch.zeros_like(parameter).reshape(-1)
            if gradient is None
            else gradient.detach().reshape(-1)
        )
    return torch.cat(pieces) if pieces else torch.empty(0, dtype=torch.float64)


def gradient_matrix(
    model: PhkV22RModel,
    gradient_pool: torch.Tensor,
    boundary: Mapping[str, torch.Tensor],
    contracts: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """R0A compatibility wrapper around the observer-safe gradient probe."""

    return gradient_matrix_preserving_state(
        model,
        gradient_pool,
        boundary,
        contracts,
    )


def gradient_matrix_preserving_state(
    model: PhkV22RModel,
    gradient_pool: torch.Tensor,
    boundary: Mapping[str, torch.Tensor],
    contracts: Mapping[str, Mapping[str, Any]],
    *,
    initial: torch.Tensor | None = None,
    loss_rows: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Measure loss-by-head gradients without touching persistent ``.grad`` state."""

    matrix_contract = contracts["method"]["loss_head_gradient_matrix"]
    rows = tuple(loss_rows or matrix_contract["loss_rows"])
    heads = tuple(matrix_contract["head_columns"])
    parameter_groups = {
        head: tuple(model.heads[head].parameters()) for head in heads
    }
    all_parameters = tuple(
        parameter for head in heads for parameter in parameter_groups[head]
    )
    slices: dict[str, slice] = {}
    cursor = 0
    for head in heads:
        count = len(parameter_groups[head])
        slices[head] = slice(cursor, cursor + count)
        cursor += count
    vectors: dict[str, dict[str, torch.Tensor]] = {head: {} for head in heads}
    norms: dict[str, dict[str, float]] = {}
    losses: dict[str, float] = {}
    saved_grads = [
        None if parameter.grad is None else parameter.grad.detach().clone()
        for parameter in all_parameters
    ]
    try:
        for row in rows:
            if row == "INITIAL":
                if initial is None:
                    raise ValueError("INITIAL diagnostic row requires a fixed initial pool")
                loss = normalized_residual_loss(
                    initial_residuals(model, initial), scales=INITIAL_SCALES
                )
            elif row == "TOTAL_OBJECTIVE":
                if initial is None:
                    raise ValueError(
                        "TOTAL_OBJECTIVE diagnostic row requires a fixed initial pool"
                    )
                base_rows = (
                    "ELECTRIC_PDE",
                    "THERMAL_PDE",
                    "PHASE_PDE",
                    "ELECTRIC_BC",
                    "THERMAL_BC",
                    "PHASE_BC",
                )
                loss = sum(
                    (_loss_for_row(model, item, gradient_pool, boundary) for item in base_rows),
                    torch.zeros((), dtype=gradient_pool.dtype, device=gradient_pool.device),
                ) + normalized_residual_loss(
                    initial_residuals(model, initial), scales=INITIAL_SCALES
                )
            else:
                loss = _loss_for_row(model, row, gradient_pool, boundary)
            if not bool(torch.isfinite(loss)):
                raise FloatingPointError(f"non-finite diagnostic loss: {row}")
            gradients = torch.autograd.grad(
                loss,
                all_parameters,
                create_graph=False,
                retain_graph=False,
                allow_unused=True,
            )
            losses[row] = _finite_float(loss)
            norms[row] = {}
            for head in heads:
                head_slice = slices[head]
                vector = _flatten_gradients(
                    gradients[head_slice], parameter_groups[head]
                ).to(device="cpu", dtype=torch.float64)
                vectors[head][row] = vector
                norms[row][head] = _finite_float(torch.linalg.vector_norm(vector))
            del loss, gradients
            gc.collect()
    finally:
        for parameter, saved in zip(all_parameters, saved_grads, strict=True):
            parameter.grad = None if saved is None else saved
    diagnostic_contract = contracts["diagnostic"]
    if "root_cause" in diagnostic_contract:
        epsilon = float(
            diagnostic_contract["root_cause"]["zero_gradient_norm_epsilon"]
        )
    else:
        epsilon = float(diagnostic_contract["decision"]["thresholds"]["epsilon"])
    cosines: dict[str, dict[str, Any]] = {}
    for head in heads:
        head_cosines: dict[str, Any] = {}
        for first_index, first in enumerate(rows):
            for second in rows[first_index + 1 :]:
                first_vector = vectors[head][first]
                second_vector = vectors[head][second]
                first_norm = torch.linalg.vector_norm(first_vector)
                second_norm = torch.linalg.vector_norm(second_vector)
                key = f"{first}__{second}"
                if float(first_norm) <= epsilon or float(second_norm) <= epsilon:
                    head_cosines[key] = {"cosine": None, "reason": "ZERO_NORM"}
                else:
                    value = torch.dot(first_vector, second_vector) / (
                        first_norm * second_norm
                    )
                    head_cosines[key] = {
                        "cosine": _finite_float(value),
                        "reason": None,
                    }
        cosines[head] = head_cosines
    return {
        "loss_values_with_existing_effective_weights": losses,
        "gradient_norms": norms,
        "same_head_pairwise_cosines": cosines,
        "persistent_parameter_gradients_after_probe": False,
        "persistent_parameter_gradients_preserved": True,
    }


def deterministic_phase_initialization_displacement(
    model: PhkV22RModel,
    config,
) -> dict[str, Any]:
    """Compare final phase parameters to a deterministic reconstruction, not a snapshot."""

    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(int(config.seed))
        reconstructed = PhkV22RModel(
            physics=model.physics,
            arm=config.arm,
            hidden_width=config.hidden_width,
            hidden_layers=config.hidden_layers,
            frequency_band=FrequencyBand.band_a(),
        ).to(device=torch.device("cpu"), dtype=torch.float64)
    current = torch.cat(
        [parameter.detach().reshape(-1) for parameter in model.heads["phase"].parameters()]
    )
    initial = torch.cat(
        [
            parameter.detach().reshape(-1)
            for parameter in reconstructed.heads["phase"].parameters()
        ]
    )
    difference = current - initial
    initial_norm = torch.linalg.vector_norm(initial)
    current_norm = torch.linalg.vector_norm(current)
    cosine = torch.dot(current, initial) / (current_norm * initial_norm)
    return {
        "evidence_identity": "DETERMINISTIC_INITIALIZATION_RECONSTRUCTION_NOT_HISTORICAL_SNAPSHOT",
        "l2_displacement": _finite_float(torch.linalg.vector_norm(difference)),
        "maximum_absolute_displacement": _finite_float(torch.max(torch.abs(difference))),
        "relative_l2_to_reconstructed_initial": _finite_float(
            torch.linalg.vector_norm(difference) / initial_norm
        ),
        "cosine_to_reconstructed_initial": _finite_float(cosine),
        "torch_version": torch.__version__,
    }


def _nearest_reference_indices(reference, coordinates: np.ndarray):
    grid = reference.grid
    x_index = np.clip(
        np.floor((coordinates[:, 0] - grid.x_min) / grid.dx).astype(np.int64),
        0,
        grid.nx - 1,
    )
    z_index = np.clip(
        np.floor((coordinates[:, 1] - grid.z_min) / grid.dz).astype(np.int64),
        0,
        grid.nz - 1,
    )
    right = np.searchsorted(reference.time, coordinates[:, 2], side="left")
    right = np.clip(right, 0, reference.time.size - 1)
    left = np.clip(right - 1, 0, reference.time.size - 1)
    choose_left = np.abs(reference.time[left] - coordinates[:, 2]) <= np.abs(
        reference.time[right] - coordinates[:, 2]
    )
    time_index = np.where(choose_left, left, right).astype(np.int64)
    cell_index = z_index * grid.nx + x_index
    return time_index, cell_index


def _reference_discrete_phase_parts(reference, time_index, cell_index):
    laplacian = np.empty(time_index.size, dtype=np.float64)
    phase_time = np.empty(time_index.size, dtype=np.float64)
    for index in np.unique(time_index):
        selected = np.flatnonzero(time_index == index)
        lap = reference.grid.phase_laplacian @ reference.phase[index]
        if index == 0:
            derivative = (reference.phase[1] - reference.phase[0]) / (
                reference.time[1] - reference.time[0]
            )
        elif index + 1 == reference.time.size:
            derivative = (reference.phase[-1] - reference.phase[-2]) / (
                reference.time[-1] - reference.time[-2]
            )
        else:
            derivative = (reference.phase[index + 1] - reference.phase[index - 1]) / (
                reference.time[index + 1] - reference.time[index - 1]
            )
        laplacian[selected] = np.asarray(lap)[cell_index[selected]]
        phase_time[selected] = derivative[cell_index[selected]]
    return laplacian[:, None], phase_time[:, None]


def _trace_summary(values: np.ndarray) -> dict[str, float]:
    finite = np.asarray(values, dtype=np.float64)
    if not np.isfinite(finite).all():
        raise FloatingPointError("reference or prediction trace is non-finite")
    return {
        "min": float(np.min(finite)),
        "max": float(np.max(finite)),
        "q50": float(np.quantile(finite, 0.50)),
        "q95": float(np.quantile(finite, 0.95)),
        "q99": float(np.quantile(finite, 0.99)),
        "rms": float(np.sqrt(np.mean(np.square(finite)))),
    }


def _reference_event_stats(reference, activity_threshold: float, roi_contract):
    roi = (
        (np.abs(reference.grid.cell_x) <= float(roi_contract["abs_x_max"]))
        & (reference.grid.cell_z >= float(roi_contract["z_min"]))
        & (reference.grid.cell_z <= float(roi_contract["z_max"]))
    )
    result = []
    for cycle, (start, end) in enumerate(((0.0, 1.25), (1.25, 2.5)), start=1):
        time_mask = (reference.time >= start) & (
            (reference.time < end) if cycle == 1 else (reference.time <= end)
        )
        time_indices = np.flatnonzero(time_mask)
        phase = reference.phase[time_indices][:, roi]
        activity = np.mean(phase >= activity_threshold, axis=1)
        local_peak = int(np.argmax(activity))
        peak_index = int(time_indices[local_peak])
        result.append(
            {
                "cycle": cycle,
                "time_bounds": [start, end],
                "peak_activity_time": float(reference.time[peak_index]),
                "peak_activity_fraction": float(activity[local_peak]),
                "peak_phase_max": float(np.max(reference.phase[peak_index, roi])),
                "peak_temperature_max": float(
                    np.max(reference.temperature[peak_index, roi])
                ),
                "peak_temperature_q95": float(
                    np.quantile(reference.temperature[peak_index, roi], 0.95)
                ),
            }
        )
    return result


def nominal_teacher_probes(
    model: PhkV22RModel,
    teacher: Mapping[str, torch.Tensor],
    contracts: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Run local evaluation-only nominal substitutions after model graphs are freed."""

    reference = load_nominal_development_reference()
    coordinates = teacher["coordinates"].numpy()
    time_index, cell_index = _nearest_reference_indices(reference, coordinates)
    reference_temperature = torch.as_tensor(
        reference.temperature[time_index, cell_index, None], dtype=torch.float64
    )
    reference_phase = torch.as_tensor(
        reference.phase[time_index, cell_index, None], dtype=torch.float64
    )
    reference_lap, reference_phase_time = _reference_discrete_phase_parts(
        reference, time_index, cell_index
    )
    reference_lap_t = torch.as_tensor(reference_lap, dtype=torch.float64)
    reference_phase_time_t = torch.as_tensor(reference_phase_time, dtype=torch.float64)
    predicted_temperature = teacher["temperature"]
    predicted_phase = teacher["phase"]
    grad_v_square = teacher["grad_potential_x"].square() + teacher[
        "grad_potential_z"
    ].square()
    sigma_predicted = model.physics.conductivity(
        predicted_temperature, predicted_phase
    )
    sigma_t_reference = model.physics.conductivity(
        reference_temperature, predicted_phase
    )
    sigma_phase_reference = model.physics.conductivity(
        predicted_temperature, reference_phase
    )
    sigma_both_reference = model.physics.conductivity(
        reference_temperature, reference_phase
    )
    mixed_joule = {
        "predicted_temperature_predicted_phase": sigma_predicted * grad_v_square,
        "reference_temperature_predicted_phase": sigma_t_reference * grad_v_square,
        "predicted_temperature_reference_phase": sigma_phase_reference * grad_v_square,
        "reference_temperature_reference_phase": sigma_both_reference * grad_v_square,
    }
    phase_diffusion_predicted = (
        model.physics.interface_width**2 * teacher["lap_phase"]
    )
    t_teacher_rhs = model.physics.mobility(reference_temperature) * (
        phase_diffusion_predicted
        - model.physics.potential_derivative(reference_temperature, predicted_phase)
    )
    t_teacher_residual = teacher["phase_time"] - t_teacher_rhs
    phase_reference_rhs = model.physics.mobility(predicted_temperature) * (
        model.physics.interface_width**2 * reference_lap_t
        - model.physics.potential_derivative(predicted_temperature, reference_phase)
    )
    phase_reference_residual = reference_phase_time_t - phase_reference_rhs
    both_reference_rhs = model.physics.mobility(reference_temperature) * (
        model.physics.interface_width**2 * reference_lap_t
        - model.physics.potential_derivative(reference_temperature, reference_phase)
    )
    both_reference_residual = reference_phase_time_t - both_reference_rhs
    qj_teacher_thermal_residual = teacher["thermal_nonjoule"] - (
        model.physics.joule_gain
        * mixed_joule["reference_temperature_reference_phase"]
    )
    quantiles = tuple(
        float(item)
        for item in contracts["diagnostic"]["measurements"]["quantiles"]
    )
    base_phase_rms = summarize_tensor(
        teacher["base_phase_residual"], quantiles
    )["rms"]
    t_teacher_phase_rms = summarize_tensor(t_teacher_residual, quantiles)["rms"]
    base_thermal_rms = summarize_tensor(
        teacher["base_thermal_residual"], quantiles
    )["rms"]
    qj_teacher_thermal_rms = summarize_tensor(
        qj_teacher_thermal_residual, quantiles
    )["rms"]
    prediction_path = _absolute_contract_path(
        contracts["method"]["legacy_source"]["prediction_carrier"]
    )
    if _sha256_path(prediction_path) != contracts["method"]["legacy_source"][
        "prediction_carrier_sha256"
    ]:
        raise ValueError("legacy STRONG_RAW prediction carrier hash mismatch")
    with np.load(prediction_path, allow_pickle=False) as archive:
        predicted_joule_trace = np.asarray(archive["joule_power"], dtype=np.float64)
    diagnostic = contracts["diagnostic"]
    event_stats = _reference_event_stats(
        reference,
        float(diagnostic["measurements"]["phase_activity_threshold"]),
        diagnostic["measurements"]["roi"],
    )
    result = {
        "reference_access_role": "NOMINAL_LOCAL_DIAGNOSTIC_ONLY",
        "reference_identity": {
            "sha256": diagnostic["nominal_reference"]["sha256"],
            "case_control": reference.case.control.value,
            "evidence_identity": reference.evidence_identity,
            "interpolated_ad_residual_used": False,
            "discrete_or_algebraic_only": True,
        },
        "reference_event_windows": event_stats,
        "reference_pool_temperature": summarize_tensor(
            reference_temperature, quantiles
        ),
        "reference_pool_phase": summarize_tensor(reference_phase, quantiles),
        "reference_algebraic_phase_reaction": summarize_tensor(
            -model.physics.potential_derivative(reference_temperature, reference_phase),
            quantiles,
        ),
        "mixed_joule_density": {
            name: summarize_tensor(value, quantiles)
            for name, value in mixed_joule.items()
        },
        "phase_teacher_substitutions": {
            "base_predicted_residual": summarize_tensor(
                teacher["base_phase_residual"], quantiles
            ),
            "reference_temperature_only_residual": summarize_tensor(
                t_teacher_residual, quantiles
            ),
            "reference_phase_discrete_residual_with_predicted_temperature": summarize_tensor(
                phase_reference_residual, quantiles
            ),
            "both_reference_discrete_residual": summarize_tensor(
                both_reference_residual, quantiles
            ),
            "base_to_reference_temperature_residual_improvement_ratio": (
                base_phase_rms / max(t_teacher_phase_rms, 1.0e-300)
            ),
        },
        "thermal_teacher_substitution": {
            "base_predicted_residual": summarize_tensor(
                teacher["base_thermal_residual"], quantiles
            ),
            "reference_constitutive_qj_residual_with_predicted_grad_v": summarize_tensor(
                qj_teacher_thermal_residual, quantiles
            ),
            "base_to_reference_constitutive_qj_residual_improvement_ratio": (
                base_thermal_rms / max(qj_teacher_thermal_rms, 1.0e-300)
            ),
        },
        "joule_power_trace_scale": {
            "reference": _trace_summary(reference.joule_power),
            "strong_raw_prediction": _trace_summary(predicted_joule_trace),
        },
    }
    del reference
    gc.collect()
    return result


def adjudicate_root_cause(
    gradient: Mapping[str, Any],
    teacher: Mapping[str, Any],
    contracts: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Apply only predeclared order-of-magnitude and teacher-contrast gates."""

    root_contract = contracts["diagnostic"]["root_cause"]
    threshold = float(root_contract["teacher_residual_improvement_ratio"])
    phase_teacher = float(
        teacher["phase_teacher_substitutions"][
            "base_to_reference_temperature_residual_improvement_ratio"
        ]
    )
    thermal_teacher = float(
        teacher["thermal_teacher_substitution"][
            "base_to_reference_constitutive_qj_residual_improvement_ratio"
        ]
    )
    reference_q95 = abs(
        float(teacher["joule_power_trace_scale"]["reference"]["q95"])
    )
    predicted_q95 = abs(
        float(teacher["joule_power_trace_scale"]["strong_raw_prediction"]["q95"])
    )
    trace_ratio = reference_q95 / max(predicted_q95, 1.0e-300)
    observations = {
        "phase_temperature_teacher_improvement_ratio": phase_teacher,
        "thermal_qj_teacher_improvement_ratio": thermal_teacher,
        "reference_to_prediction_joule_q95_ratio": trace_ratio,
    }
    if thermal_teacher >= threshold and trace_ratio >= threshold:
        return {
            "status": "R0A_ROOT_CAUSE_IDENTIFIED",
            "primary": "ELECTROTHERMAL_DRIVE_DEFICIT",
            "secondary": [],
            "hypotheses": ["ELECTROTHERMAL_DRIVE_DEFICIT"],
            "basis": observations,
            "next_recommendation": None,
        }
    hypotheses: list[str] = []
    phase_norms = {
        row: float(values["phase"])
        for row, values in gradient["gradient_norms"].items()
    }
    positive_norms = [value for value in phase_norms.values() if value > 0.0]
    if positive_norms and max(positive_norms) / max(min(positive_norms), 1.0e-300) >= 10.0:
        hypotheses.append("LOSS_OR_HEAD_GRADIENT_STARVATION")
    conflict_threshold = float(root_contract["gradient_conflict_cosine_threshold"])
    if any(
        item["cosine"] is not None and float(item["cosine"]) <= conflict_threshold
        for item in gradient["same_head_pairwise_cosines"]["phase"].values()
    ):
        hypotheses.append("LOSS_OR_HEAD_GRADIENT_CONFLICT")
    hypotheses.append("CAUSAL_OR_EARLY_TRAINING_DYNAMICS_UNRESOLVED")
    hypotheses = list(dict.fromkeys(hypotheses))[:3]
    return {
        "status": "R0A_INCONCLUSIVE",
        "primary": None,
        "secondary": [],
        "hypotheses": hypotheses,
        "basis": observations,
        "reason": "NO_CLEAR_ORDER_OF_MAGNITUDE_AND_TEACHER_SUBSTITUTION_CONTRAST",
        "next_recommendation": "R0B_FIRST_SWITCH_175",
    }


def assert_legacy_source_identity(
    checkpoint_path: Path,
    contracts: Mapping[str, Mapping[str, Any]],
) -> tuple[PhkV22RModel, Any, dict[str, Any]]:
    source = contracts["method"]["legacy_source"]
    expected = _absolute_contract_path(source["checkpoint"])
    if Path(checkpoint_path).resolve() != expected:
        raise ValueError("R0A checkpoint path differs from the frozen STRONG_RAW source")
    if _sha256_path(expected) != source["checkpoint_sha256"]:
        raise ValueError("R0A STRONG_RAW checkpoint hash mismatch")
    model, config, checkpoint = _load_model(expected, device=torch.device("cpu"))
    identity = contracts["method"]["legacy_training_identity"]
    assertions = {
        "checkpoint_schema": checkpoint.get("schema_id"),
        "checkpoint_update": int(checkpoint.get("update", -1)),
        "arm": config.arm,
        "case_control": config.case_control,
        "seed": int(config.seed),
        "hidden_width": int(config.hidden_width),
        "hidden_layers": int(config.hidden_layers),
        "frequency_band": config.frequency_band,
        "temperature_scale": model.temperature_scale,
        "phase_latent_scale": model.phase_latent_scale,
        "hard_ic_startup_time": model.startup_time,
        "model_device": str(next(model.parameters()).device),
        "model_dtype": str(next(model.parameters()).dtype),
        "optimizer_state_loaded": False,
    }
    expected_values = {
        "checkpoint_schema": "phk-v22r-checkpoint-v1-1",
        "checkpoint_update": int(identity["updates"]),
        "arm": PhkV22RArm.STRONG_RAW.value,
        "case_control": identity["case_control"],
        "seed": int(identity["seed"]),
        "hidden_width": int(identity["hidden_width"]),
        "hidden_layers": int(identity["hidden_layers"]),
        "frequency_band": identity["frequency_band"],
        "temperature_scale": float(identity["temperature_scale"]),
        "phase_latent_scale": float(identity["phase_latent_scale"]),
        "hard_ic_startup_time": float(identity["hard_ic_startup_time"]),
        "model_device": "cpu",
        "model_dtype": "torch.float64",
        "optimizer_state_loaded": False,
    }
    if assertions != expected_values:
        raise ValueError(f"legacy STRONG_RAW identity mismatch: {assertions}")
    checkpoint_summary = {
        "training_config_sha256": checkpoint["training_config_sha256"],
        "v22r_program_contract_sha256": checkpoint["program_contract_sha256"],
        "v22r_method_contract_sha256": checkpoint["method_contract_sha256"],
        "physical_program_sha256": checkpoint["physical_program_sha256"],
        "physical_object_sha256": checkpoint["physical_object_sha256"],
    }
    for checkpoint_name, source_name in (
        ("v22r_program_contract_sha256", "v22r_program_contract_sha256"),
        ("v22r_method_contract_sha256", "v22r_method_contract_sha256"),
        ("physical_program_sha256", "physical_program_sha256"),
        ("physical_object_sha256", "physical_object_sha256"),
    ):
        if checkpoint_summary[checkpoint_name] != source[source_name]:
            raise ValueError(f"legacy checkpoint identity mismatch: {checkpoint_name}")
    del checkpoint
    gc.collect()
    return model, config, {**assertions, **checkpoint_summary}


def load_legacy_source_preserving_rng(
    checkpoint_path: Path,
    contracts: Mapping[str, Mapping[str, Any]],
) -> tuple[PhkV22RModel, Any, dict[str, Any]]:
    """Construct and load the legacy model without consuming ambient CPU RNG."""

    before = torch.random.get_rng_state().clone()
    with torch.random.fork_rng(devices=[]):
        loaded = assert_legacy_source_identity(checkpoint_path, contracts)
    if not torch.equal(torch.random.get_rng_state(), before):
        raise RuntimeError("legacy checkpoint loading changed ambient torch CPU RNG")
    return loaded


def _training_log_summary(path: Path) -> dict[str, Any]:
    records = [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not records:
        raise ValueError("legacy STRONG_RAW training log is empty")
    return {
        "record_count": len(records),
        "first_update": int(records[0]["update"]),
        "last_update": int(records[-1]["update"]),
        "first_pde_loss": float(records[0]["pde_loss"]),
        "final_pde_loss": float(records[-1]["pde_loss"]),
        "first_component_rms": {
            name: float(records[0][f"{name}_rms"])
            for name in ("electric", "thermal", "phase")
        },
        "final_component_rms": {
            name: float(records[-1][f"{name}_rms"])
            for name in ("electric", "thermal", "phase")
        },
    }


def write_json_exclusive_atomic(path: Path, payload: Mapping[str, Any]) -> Path:
    """Atomically create one JSON artifact and refuse overwrite."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    ) + "\n"
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, target)
        return target
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def run_r0a(
    *,
    checkpoint_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Execute exactly one bounded CPU-only read-only R0A diagnostic."""

    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    assert_cpu_only_environment()
    assert_one_time_r0a_target(output_path)
    rng_before = torch.random.get_rng_state().clone()
    contracts = load_contract_bundle()
    model, config, legacy_assertions = load_legacy_source_preserving_rng(
        checkpoint_path, contracts
    )
    if next(model.parameters()).device.type != "cpu":
        raise PermissionError("R0A model is not on CPU")
    mode_before = model.training
    state_before = snapshot_state(model)
    identity_before = state_identity(model)
    pool, gradient_pool, _, boundary_bundle = build_r0a_pool(model, contracts)
    field_mapping, phase_terms, electrothermal, teacher_parts = summarize_model_mapping(
        model,
        pool,
        boundary_bundle["batches"],
        contracts,
    )
    gradient = gradient_matrix(
        model,
        gradient_pool,
        boundary_bundle["batches"],
        contracts,
    )
    gradient["phase_parameter_displacement_identity"] = (
        deterministic_phase_initialization_displacement(model, config)
    )
    model.zero_grad(set_to_none=True)
    gc.collect()
    teacher = nominal_teacher_probes(model, teacher_parts, contracts)
    root_cause = adjudicate_root_cause(gradient, teacher, contracts)
    identity_after = assert_state_unchanged(model, state_before, identity_before)
    if model.training != mode_before:
        raise RuntimeError("R0A changed model training mode")
    if not torch.equal(torch.random.get_rng_state(), rng_before):
        raise RuntimeError("R0A changed the ambient torch CPU RNG state")
    elapsed = time.perf_counter() - started
    maximum = float(contracts["diagnostic"]["execution"]["maximum_wall_seconds"])
    if elapsed > maximum:
        raise TimeoutError("R0A CPU wall-time hard cap exceeded")
    source = contracts["method"]["legacy_source"]
    training_log = _absolute_contract_path(source["training_log"])
    artifact: dict[str, Any] = {
        "schema_id": "phk-v23-r0a-diagnostic-artifact-v1",
        "task_id": "PHK_V23_R0A_CPU_DIAGNOSTICS_AND_CONTRACT",
        "status": root_cause["status"],
        "started_at_utc": started_at,
        "ended_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_identity": {
            "run_id": source["run_id"],
            "source_commit": source["source_commit"],
            "checkpoint_path": source["checkpoint"],
            "checkpoint_sha256": source["checkpoint_sha256"],
            "prediction_carrier_path": source["prediction_carrier"],
            "prediction_carrier_sha256": source["prediction_carrier_sha256"],
            "training_log_path": source["training_log"],
            "training_log_sha256": _sha256_path(training_log),
            "contracts": {
                "program": {
                    "path": str(PROGRAM_CONTRACT_PATH.relative_to(ROOT)).replace("\\", "/"),
                    "sha256": _sha256_path(PROGRAM_CONTRACT_PATH),
                },
                "method": {
                    "path": str(METHOD_CONTRACT_PATH.relative_to(ROOT)).replace("\\", "/"),
                    "sha256": _sha256_path(METHOD_CONTRACT_PATH),
                },
                "diagnostic": {
                    "path": str(DIAGNOSTIC_CONTRACT_PATH.relative_to(ROOT)).replace("\\", "/"),
                    "sha256": _sha256_path(DIAGNOSTIC_CONTRACT_PATH),
                },
            },
        },
        "execution": {
            "device": "CPU",
            "dtype": "FLOAT64",
            "cuda_visible_devices": "",
            "gpu_used": False,
            "cloud_used": False,
            "incremental_cloud_cost_cny": 0.0,
            "optimizer_constructed": False,
            "optimizer_steps": 0,
            "parameter_updates": 0,
            "checkpoint_selection": False,
            "training_semantics_changed": False,
            "reference_access_role": "NOMINAL_LOCAL_DIAGNOSTIC_ONLY",
            "stress_fields_read": False,
            "wall_seconds": elapsed,
            "wall_seconds_hard_cap": maximum,
            "torch_version": torch.__version__,
            "numpy_version": np.__version__,
        },
        "legacy_assertions": legacy_assertions,
        "legacy_training_log": _training_log_summary(training_log),
        "pool": boundary_bundle["identity"],
        "state_identity": {
            "before": identity_before,
            "after": identity_after,
            "all_state_tensors_equal": True,
            "model_training_mode_unchanged": True,
            "entry_to_exit_torch_rng_unchanged": True,
            "persistent_parameter_gradients": False,
        },
        "A_field_mapping": field_mapping,
        "B_phase_terms": phase_terms,
        "C_electrothermal": electrothermal,
        "D_gradient_matrix": gradient,
        "E_nominal_teacher": teacher,
        "root_cause": root_cause,
        "refusals": {
            "r0b_executed": False,
            "r1_executed": False,
            "pjgr_implemented": False,
            "stress_reference_accessed": False,
            "gpu_or_cloud_used": False,
            "optimizer_step_called": False,
            "old_evidence_rewritten": False,
        },
    }
    required = set(contracts["diagnostic"]["output_required_sections"])
    missing = required - set(artifact)
    if missing:
        raise RuntimeError(f"R0A artifact lacks required sections: {sorted(missing)}")
    write_json_exclusive_atomic(output_path, artifact)
    return artifact


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args(argv)
    artifact = run_r0a(
        checkpoint_path=arguments.checkpoint,
        output_path=arguments.output,
    )
    print(
        json.dumps(
            {
                "status": artifact["status"],
                "wall_seconds": artifact["execution"]["wall_seconds"],
                "output": str(arguments.output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DIAGNOSTIC_CONTRACT_PATH",
    "METHOD_CONTRACT_PATH",
    "PROGRAM_CONTRACT_PATH",
    "adjudicate_root_cause",
    "assert_cpu_only_environment",
    "assert_one_time_r0a_target",
    "assert_legacy_source_identity",
    "assert_state_unchanged",
    "build_r0a_pool",
    "gradient_matrix",
    "gradient_matrix_preserving_state",
    "load_contract_bundle",
    "load_legacy_source_preserving_rng",
    "load_nominal_development_reference",
    "nominal_teacher_probes",
    "reject_non_nominal_reference_access",
    "run_r0a",
    "snapshot_state",
    "state_identity",
    "summarize_model_mapping",
    "summarize_tensor",
    "write_json_exclusive_atomic",
]
