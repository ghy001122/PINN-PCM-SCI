"""Reference-blind prediction carrier generation for PHK-V2.2R checkpoints."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

import numpy as np
import torch

from .phk_benchmark import PhkControl, PhkGrid
from .phk_v21_benchmark import phk_v21_resolution
from .phk_v22r_pinn import FrequencyBand, PhkV22RModel
from .phk_v22r_training import (
    PROGRAM_CONTRACT_PATH,
    METHOD_CONTRACT_PATH,
    ROOT,
    PhkTrainingConfig,
    load_case_physics,
)


PREDICTION_ARRAYS = {
    "metadata_json",
    "x",
    "z",
    "time",
    "potential",
    "temperature",
    "phase",
    "top_current",
    "joule_power",
}


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _band(name: str) -> FrequencyBand:
    return (
        FrequencyBand.band_a()
        if name == "BAND_A"
        else FrequencyBand.conservative()
    )


def _load_model(
    checkpoint_path: Path,
    *,
    device: torch.device,
) -> tuple[PhkV22RModel, PhkTrainingConfig, dict[str, Any]]:
    checkpoint = torch.load(
        Path(checkpoint_path), map_location=device, weights_only=False
    )
    if checkpoint.get("schema_id") != "phk-v22r-checkpoint-v1":
        raise ValueError("unsupported PHK-V2.2R checkpoint schema")
    config = PhkTrainingConfig(**checkpoint["training_config"])
    config.validate()
    if checkpoint.get("training_config_sha256") != config.identity:
        raise ValueError("checkpoint training configuration hash mismatch")
    if checkpoint.get("program_contract_sha256") != _sha256_path(
        PROGRAM_CONTRACT_PATH
    ):
        raise ValueError("checkpoint V2.2R program contract drift")
    if checkpoint.get("method_contract_sha256") != _sha256_path(
        METHOD_CONTRACT_PATH
    ):
        raise ValueError("checkpoint V2.2R method contract drift")
    physics, program_sha, object_sha = load_case_physics(config.case_control)
    if checkpoint.get("physical_program_sha256") != program_sha:
        raise ValueError("checkpoint physical program hash mismatch")
    if checkpoint.get("physical_object_sha256") != object_sha:
        raise ValueError("checkpoint physical object hash mismatch")
    model = PhkV22RModel(
        physics=physics,
        arm=config.arm,
        hidden_width=config.hidden_width,
        hidden_layers=config.hidden_layers,
        frequency_band=_band(config.frequency_band),
    ).to(device=device, dtype=torch.float64)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.eval()
    return model, config, checkpoint


def _evaluation_axes(config: PhkTrainingConfig) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    physical_contract = __import__(
        "pinn_pcm_sci.phk_v21_benchmark", fromlist=["load_phk_v21_physical"]
    ).load_phk_v21_physical(
        program_path=ROOT / "configs" / "phk_v21" / "program_contract.json",
        object_path=ROOT / "configs" / "phk_v21" / "object_numerical_contract.json",
        legacy_program_path=ROOT / "configs" / "phk_v2" / "program_contract.json",
        legacy_object_path=ROOT / "configs" / "phk_v2" / "object_numerical_contract.json",
    )
    case = __import__(
        "pinn_pcm_sci.phk_v21_benchmark", fromlist=["PhkV21CaseSpec"]
    ).PhkV21CaseSpec.nominal(
        physical_contract, control=PhkControl(config.case_control)
    )
    resolution = phk_v21_resolution(
        physical_contract, "extra_fine", period=case.period
    )
    grid = PhkGrid.build(
        nx=resolution.nx,
        nz=resolution.nz,
        x_min=float(physical_contract.coordinates["x_min"]),
        x_max=float(physical_contract.coordinates["x_max"]),
        z_min=float(physical_contract.coordinates["z_min"]),
        z_max=float(physical_contract.coordinates["z_max"]),
    )
    step_count = int(round(resolution.time_end / resolution.dt))
    saved = list(range(0, step_count + 1, resolution.save_every))
    if saved[-1] != step_count:
        saved.append(step_count)
    time = np.asarray(saved, dtype=np.float64) * resolution.dt
    return grid.x_centers, grid.z_centers, time


def write_prediction_carrier(
    *,
    checkpoint_path: Path,
    output_path: Path,
    device_name: str = "cpu",
    chunk_points: int = 65536,
) -> Path:
    """Evaluate a checkpoint on contract-derived axes without opening references."""

    if chunk_points <= 0:
        raise ValueError("prediction chunk size must be positive")
    device = torch.device(device_name)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA prediction requested but CUDA is unavailable")
    model, config, checkpoint = _load_model(Path(checkpoint_path), device=device)
    x_axis, z_axis, time_axis = _evaluation_axes(config)
    x_mesh, z_mesh = np.meshgrid(x_axis, z_axis, indexing="xy")
    spatial_x = x_mesh.reshape(-1)
    spatial_z = z_mesh.reshape(-1)
    cell_count = spatial_x.size
    shape = (time_axis.size, cell_count)
    potential = np.empty(shape, dtype=np.float64)
    temperature = np.empty(shape, dtype=np.float64)
    phase = np.empty(shape, dtype=np.float64)
    top_current = np.empty(time_axis.size, dtype=np.float64)
    joule_power = np.empty(time_axis.size, dtype=np.float64)
    dx = float(x_axis[1] - x_axis[0])
    dz = float(z_axis[1] - z_axis[0])

    for time_index, time_value in enumerate(time_axis):
        joule_sum = 0.0
        for start in range(0, cell_count, chunk_points):
            end = min(start + chunk_points, cell_count)
            coordinates = torch.as_tensor(
                np.column_stack(
                    (
                        spatial_x[start:end],
                        spatial_z[start:end],
                        np.full(end - start, time_value, dtype=np.float64),
                    )
                ),
                dtype=torch.float64,
                device=device,
            ).requires_grad_(True)
            fields = model(coordinates)
            potential_gradient = torch.autograd.grad(
                fields[:, 0:1],
                coordinates,
                grad_outputs=torch.ones_like(fields[:, 0:1]),
                create_graph=False,
                retain_graph=False,
            )[0]
            conductivity = model.physics.conductivity(
                fields[:, 1:2], fields[:, 2:3]
            )
            local_joule = conductivity * (
                potential_gradient[:, 0:1].square()
                + potential_gradient[:, 1:2].square()
            )
            values = fields.detach().cpu().numpy()
            potential[time_index, start:end] = values[:, 0]
            temperature[time_index, start:end] = values[:, 1]
            phase[time_index, start:end] = values[:, 2]
            joule_sum += float(local_joule.detach().sum().cpu()) * dx * dz
        joule_power[time_index] = joule_sum

        top_coordinates = torch.as_tensor(
            np.column_stack(
                (
                    x_axis,
                    np.full(x_axis.size, model.physics.z_max, dtype=np.float64),
                    np.full(x_axis.size, time_value, dtype=np.float64),
                )
            ),
            dtype=torch.float64,
            device=device,
        ).requires_grad_(True)
        top_fields = model(top_coordinates)
        top_gradient = torch.autograd.grad(
            top_fields[:, 0:1],
            top_coordinates,
            grad_outputs=torch.ones_like(top_fields[:, 0:1]),
            create_graph=False,
            retain_graph=False,
        )[0]
        top_sigma = model.physics.conductivity(
            top_fields[:, 1:2], top_fields[:, 2:3]
        )
        top_current[time_index] = float(
            torch.sum(top_sigma * top_gradient[:, 1:2]).detach().cpu()
        ) * dx

    metadata = {
        "schema_id": "phk-v22r-prediction-carrier-v1",
        "checkpoint_sha256": _sha256_path(Path(checkpoint_path)),
        "checkpoint_update": int(checkpoint["update"]),
        "training_config": asdict(config),
        "training_config_sha256": config.identity,
        "architecture": model.architecture_manifest(),
        "program_contract_sha256": checkpoint["program_contract_sha256"],
        "method_contract_sha256": checkpoint["method_contract_sha256"],
        "physical_program_sha256": checkpoint["physical_program_sha256"],
        "physical_object_sha256": checkpoint["physical_object_sha256"],
        "reference_fields_read": False,
        "evaluation_grid_identity": "CONTRACT_DERIVED_EXTRA_FINE_AXES_WITHOUT_REFERENCE_VALUES",
        "top_current_definition": "INTEGRAL_TOP_SIGMA_DV_DZ",
        "joule_power_definition": "CELL_QUADRATURE_SIGMA_GRAD_V_SQUARED",
    }
    exact = Path(output_path)
    exact.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    descriptor = os.open(exact, flags, 0o644)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            np.savez_compressed(
                handle,
                metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
                x=x_axis,
                z=z_axis,
                time=time_axis,
                potential=potential,
                temperature=temperature,
                phase=phase,
                top_current=top_current,
                joule_power=joule_power,
            )
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        exact.unlink(missing_ok=True)
        raise
    return exact


def read_prediction_carrier(path: Path) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    exact = Path(path)
    try:
        with np.load(exact, allow_pickle=False) as archive:
            if set(archive.files) != PREDICTION_ARRAYS:
                raise ValueError("prediction carrier contains missing or unknown arrays")
            metadata = json.loads(str(archive["metadata_json"].item()))
            arrays = {
                name: np.asarray(archive[name], dtype=np.float64).copy()
                for name in PREDICTION_ARRAYS - {"metadata_json"}
            }
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid PHK-V2.2R prediction carrier: {exact}") from exc
    if metadata.get("schema_id") != "phk-v22r-prediction-carrier-v1":
        raise ValueError("unsupported PHK-V2.2R prediction carrier schema")
    if metadata.get("reference_fields_read") is not False:
        raise ValueError("prediction carrier does not preserve reference blindness")
    nt = arrays["time"].size
    cells = arrays["x"].size * arrays["z"].size
    for name in ("potential", "temperature", "phase"):
        if arrays[name].shape != (nt, cells):
            raise ValueError(f"prediction {name} shape mismatch")
    for name in ("top_current", "joule_power"):
        if arrays[name].shape != (nt,):
            raise ValueError(f"prediction {name} trace shape mismatch")
    if not all(np.isfinite(value).all() for value in arrays.values()):
        raise ValueError("prediction carrier contains nonfinite values")
    return metadata, arrays


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--chunk-points", type=int, default=65536)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    path = write_prediction_carrier(
        checkpoint_path=args.checkpoint,
        output_path=args.output,
        device_name=args.device,
        chunk_points=args.chunk_points,
    )
    print(
        json.dumps(
            {
                "status": "PREDICTION_COMPLETE",
                "path": str(path.resolve()),
                "sha256": _sha256_path(path),
                "size_bytes": path.stat().st_size,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "PREDICTION_ARRAYS",
    "main",
    "read_prediction_carrier",
    "write_prediction_carrier",
]
