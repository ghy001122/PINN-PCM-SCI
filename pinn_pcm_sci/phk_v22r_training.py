"""Bounded training and profiling runner for PHK-V2.2R method arms."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import time
from typing import Any, Mapping

import numpy as np
import torch

from .phk_benchmark import PhkControl
from .phk_v21_benchmark import PhkV21CaseSpec, load_phk_v21_physical
from .phk_v22r_pinn import (
    CollocationMixture,
    FrequencyBand,
    PhkCollocationSampler,
    PhkV22RArm,
    PhkV22RModel,
    PhkV22RPhysics,
    boundary_residuals,
    initial_residuals,
    interior_residuals,
    normalized_residual_loss,
)


ROOT = Path(__file__).resolve().parents[1]
PROGRAM_CONTRACT_PATH = ROOT / "configs" / "phk_v22r" / "program_contract.json"
METHOD_CONTRACT_PATH = ROOT / "configs" / "phk_v22r" / "method_contract.json"


PDE_SCALES: Mapping[str, float] = {
    "electric": 1.0,
    "thermal": 4.0,
    "phase": 5.0,
}

BOUNDARY_SCALES: Mapping[str, float] = {
    "bc_potential_top": 0.72,
    "bc_potential_heater": 0.72,
    "bc_electric_insulating_bottom": 1.0,
    "bc_electric_insulating_side": 1.0,
    "bc_temperature_top": 1.0,
    "bc_temperature_robin": 1.0,
    "bc_phase_no_flux": 1.0,
}

INITIAL_SCALES: Mapping[str, float] = {
    "ic_potential": 0.72,
    "ic_temperature": 1.0,
    "ic_phase": 0.03,
}


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _write_json_exclusive(path: Path, payload: Mapping[str, Any]) -> None:
    exact = Path(path)
    exact.parent.mkdir(parents=True, exist_ok=True)
    with exact.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


@dataclass(frozen=True)
class PhkTrainingConfig:
    arm: str
    case_control: str = "FULL"
    updates: int = 1000
    seed: int = 17
    hidden_width: int = 64
    hidden_layers: int = 4
    frequency_band: str = "BAND_A"
    learning_rate: float = 1.0e-3
    gradient_clip_norm: float = 10.0
    interior_points: int = 512
    boundary_points: int = 128
    initial_points: int = 128
    candidate_pool_multiplier: int = 4
    refresh_updates: int = 250
    log_every: int = 25
    checkpoint_every: int = 1000
    pde_weight: float = 1.0
    boundary_weight: float = 5.0
    initial_weight: float = 1.0
    dtype: str = "float64"
    device: str = "cpu"

    def validate(self) -> None:
        PhkV22RArm(self.arm)
        control = PhkControl(self.case_control)
        if control not in {
            PhkControl.FULL,
            PhkControl.INTERFACE_WIDTH_0_025,
            PhkControl.HEATER_WIDTH_0_50,
        }:
            raise ValueError("training case is outside the V2.2R matrix")
        positive_ints = {
            "updates": self.updates,
            "hidden_width": self.hidden_width,
            "hidden_layers": self.hidden_layers,
            "interior_points": self.interior_points,
            "boundary_points": self.boundary_points,
            "initial_points": self.initial_points,
            "candidate_pool_multiplier": self.candidate_pool_multiplier,
            "refresh_updates": self.refresh_updates,
            "log_every": self.log_every,
            "checkpoint_every": self.checkpoint_every,
        }
        for name, value in positive_ints.items():
            if int(value) <= 0:
                raise ValueError(f"{name} must be positive")
        if self.boundary_points % 4:
            raise ValueError("boundary_points must be divisible by four")
        for name in (
            "learning_rate",
            "gradient_clip_norm",
            "pde_weight",
            "boundary_weight",
            "initial_weight",
        ):
            value = float(getattr(self, name))
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be positive and finite")
        if self.dtype != "float64":
            raise ValueError("PHK-V2.2R training is frozen to float64")
        if self.frequency_band not in {"BAND_A", "BAND_B_CONSERVATIVE"}:
            raise ValueError("unknown frozen frequency band")
        if self.device != "cpu" and not self.device.startswith("cuda"):
            raise ValueError("device must be cpu or a CUDA device")

    @property
    def identity(self) -> str:
        return hashlib.sha256(_canonical_json(asdict(self))).hexdigest().upper()


@dataclass(frozen=True)
class TrainingOutcome:
    run_directory: Path
    status: str
    final_loss: float
    minimum_loss: float
    wall_seconds: float
    seconds_per_update: float
    peak_gpu_memory_bytes: int
    checkpoint_path: Path


def load_case_physics(
    control: PhkControl | str = PhkControl.FULL,
) -> tuple[PhkV22RPhysics, str, str]:
    """Load only contracts; this function never opens a reference carrier."""

    physical = load_phk_v21_physical(
        program_path=ROOT / "configs" / "phk_v21" / "program_contract.json",
        object_path=ROOT / "configs" / "phk_v21" / "object_numerical_contract.json",
        legacy_program_path=ROOT / "configs" / "phk_v2" / "program_contract.json",
        legacy_object_path=ROOT / "configs" / "phk_v2" / "object_numerical_contract.json",
    )
    selected = PhkControl(control)
    if selected not in {
        PhkControl.FULL,
        PhkControl.INTERFACE_WIDTH_0_025,
        PhkControl.HEATER_WIDTH_0_50,
    }:
        raise ValueError("training case is outside the V2.2R matrix")
    case = PhkV21CaseSpec.nominal(physical, control=selected)
    physics = PhkV22RPhysics.from_contract(physical, case)
    return physics, physical.program.sha256, physical.object.sha256


def _frequency_band(name: str) -> FrequencyBand:
    if name == "BAND_A":
        return FrequencyBand.band_a()
    if name == "BAND_B_CONSERVATIVE":
        return FrequencyBand.conservative()
    raise ValueError(f"unknown frequency band: {name}")


def _active_windows(update: int, total_updates: int) -> int:
    """Open windows at frozen fractions 0, 0.15, 0.35, and 0.55."""

    fraction = update / max(total_updates, 1)
    if fraction < 0.15:
        return 1
    if fraction < 0.35:
        return 2
    if fraction < 0.55:
        return 3
    return 4


def _merge_residuals(
    groups: Mapping[str, Mapping[str, torch.Tensor]],
) -> dict[str, torch.Tensor]:
    merged: dict[str, list[torch.Tensor]] = {}
    for prefix, residuals in groups.items():
        for name, value in residuals.items():
            merged.setdefault(f"{prefix}:{name}", []).append(value.reshape(-1, 1))
    return {name: torch.cat(values, dim=0) for name, values in merged.items()}


def _boundary_loss(
    model: PhkV22RModel,
    batches: Mapping[str, torch.Tensor],
) -> tuple[torch.Tensor, dict[str, float]]:
    residuals = _merge_residuals(
        {
            side: boundary_residuals(model, coordinates, side=side)
            for side, coordinates in batches.items()
        }
    )
    losses = []
    diagnostics = {}
    for qualified_name, value in residuals.items():
        base_name = qualified_name.split(":", 1)[1]
        scale = BOUNDARY_SCALES[base_name]
        item = torch.mean((value / scale).square())
        losses.append(item)
        diagnostics[qualified_name] = float(item.detach().cpu())
    return torch.stack(losses).mean(), diagnostics


def _checkpoint_payload(
    *,
    model: PhkV22RModel,
    optimizer: torch.optim.Optimizer,
    config: PhkTrainingConfig,
    update: int,
    program_contract_sha256: str,
    method_contract_sha256: str,
    physical_program_sha256: str,
    physical_object_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_id": "phk-v22r-checkpoint-v1-1",
        "update": int(update),
        "training_config": asdict(config),
        "training_config_sha256": config.identity,
        "architecture": model.architecture_manifest(),
        "program_contract_sha256": program_contract_sha256,
        "method_contract_sha256": method_contract_sha256,
        "physical_program_sha256": physical_program_sha256,
        "physical_object_sha256": physical_object_sha256,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "torch_version": torch.__version__,
    }


def train(
    config: PhkTrainingConfig,
    *,
    run_directory: Path,
) -> TrainingOutcome:
    """Run one bounded arm from scratch and emit an immutable evidence directory."""

    config.validate()
    output = Path(run_directory).resolve()
    output.mkdir(parents=True, exist_ok=False)
    program_contract_sha256 = _sha256_path(PROGRAM_CONTRACT_PATH)
    method_contract_sha256 = _sha256_path(METHOD_CONTRACT_PATH)
    physics, physical_program_sha256, physical_object_sha256 = load_case_physics(
        config.case_control
    )
    device = torch.device(config.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA training requested but CUDA is unavailable")
    dtype = torch.float64
    random.seed(config.seed)
    np.random.seed(config.seed)
    torch.manual_seed(config.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(config.seed)
        torch.cuda.reset_peak_memory_stats(device)

    model = PhkV22RModel(
        physics=physics,
        arm=config.arm,
        hidden_width=config.hidden_width,
        hidden_layers=config.hidden_layers,
        frequency_band=_frequency_band(config.frequency_band),
    ).to(device=device, dtype=dtype)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    mixture = CollocationMixture(
        candidate_pool_multiplier=config.candidate_pool_multiplier
    )
    sampler = PhkCollocationSampler(
        physics=physics,
        mixture=mixture,
        seed=config.seed,
    )
    manifest = {
        "schema_id": "phk-v22r-training-run-manifest-v1-1",
        "status": "RUNNING",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "training_config": asdict(config),
        "training_config_sha256": config.identity,
        "architecture": model.architecture_manifest(),
        "program_contract": str(PROGRAM_CONTRACT_PATH.relative_to(ROOT)),
        "program_contract_sha256": program_contract_sha256,
        "method_contract": str(METHOD_CONTRACT_PATH.relative_to(ROOT)),
        "method_contract_sha256": method_contract_sha256,
        "physical_program_sha256": physical_program_sha256,
        "physical_object_sha256": physical_object_sha256,
        "reference_fields_read": False,
        "training_labels_used": False,
        "anchor_fields_used": False,
        "initialization": "SCRATCH_START",
        "checkpoint_policy": (
            "FINAL_ONLY"
            if config.checkpoint_every >= config.updates
            else "PERIODIC_PLUS_FINAL"
        ),
        "sampler_inputs": ["SOBOL", "PDE_RESIDUAL", "PREDICTED_PHASE", "PREDICTED_JOULE"],
        "pde_scales": dict(PDE_SCALES),
        "boundary_scales": dict(BOUNDARY_SCALES),
        "initial_scales": dict(INITIAL_SCALES),
        "loss_weights": {
            "pde": config.pde_weight,
            "boundary": config.boundary_weight,
            "initial": config.initial_weight,
        },
        "causal_window_open_fractions": [0.0, 0.15, 0.35, 0.55],
    }
    _write_json_exclusive(output / "manifest-start.json", manifest)

    log_path = output / "training-log.jsonl"
    checkpoint_path = output / "checkpoint-final.pt"
    cached_interior: torch.Tensor | None = None
    cached_boundary: dict[str, torch.Tensor] | None = None
    cached_initial: torch.Tensor | None = None
    cached_windows = 0
    minimum_loss = math.inf
    final_loss = math.inf
    start = time.perf_counter()
    status = "COMPLETE"
    try:
        with log_path.open("x", encoding="utf-8", newline="\n") as log_handle:
            for update in range(config.updates):
                active_windows = _active_windows(update, config.updates)
                needs_refresh = (
                    cached_interior is None
                    or update % config.refresh_updates == 0
                    or active_windows != cached_windows
                )
                if needs_refresh:
                    cached_interior = sampler.select_interior(
                        model,
                        count=config.interior_points,
                        active_windows=active_windows,
                        physics_aware=PhkV22RArm(config.arm).uses_physics_sampler,
                        dtype=dtype,
                        device=device,
                    ).detach()
                    cached_boundary = sampler.boundary(
                        config.boundary_points // 4,
                        active_windows=active_windows,
                        dtype=dtype,
                        device=device,
                    )
                    cached_initial = sampler.initial(
                        config.initial_points,
                        dtype=dtype,
                        device=device,
                    )
                    cached_windows = active_windows
                assert cached_interior is not None
                assert cached_boundary is not None
                assert cached_initial is not None

                optimizer.zero_grad(set_to_none=True)
                interior = interior_residuals(model, cached_interior)
                pde_loss = normalized_residual_loss(interior, scales=PDE_SCALES)
                bc_loss, bc_diagnostics = _boundary_loss(model, cached_boundary)
                ic = initial_residuals(model, cached_initial)
                ic_loss = normalized_residual_loss(ic, scales=INITIAL_SCALES)
                total = (
                    config.pde_weight * pde_loss
                    + config.boundary_weight * bc_loss
                    + config.initial_weight * ic_loss
                )
                if not bool(torch.isfinite(total)):
                    raise FloatingPointError(f"nonfinite loss at update {update + 1}")
                total.backward()
                gradient_norm = torch.nn.utils.clip_grad_norm_(
                    model.parameters(), config.gradient_clip_norm
                )
                if not bool(torch.isfinite(gradient_norm)):
                    raise FloatingPointError(
                        f"nonfinite gradient norm at update {update + 1}"
                    )
                optimizer.step()
                final_loss = float(total.detach().cpu())
                minimum_loss = min(minimum_loss, final_loss)

                should_log = (
                    update == 0
                    or (update + 1) % config.log_every == 0
                    or update + 1 == config.updates
                )
                if should_log:
                    record = {
                        "update": update + 1,
                        "active_windows": active_windows,
                        "collocation_refreshed": needs_refresh,
                        "loss": final_loss,
                        "pde_loss": float(pde_loss.detach().cpu()),
                        "boundary_loss": float(bc_loss.detach().cpu()),
                        "initial_loss": float(ic_loss.detach().cpu()),
                        "gradient_norm_before_clip": float(gradient_norm.detach().cpu()),
                        "electric_rms": float(
                            torch.sqrt(torch.mean(interior["electric"].detach().square())).cpu()
                        ),
                        "thermal_rms": float(
                            torch.sqrt(torch.mean(interior["thermal"].detach().square())).cpu()
                        ),
                        "phase_rms": float(
                            torch.sqrt(torch.mean(interior["phase"].detach().square())).cpu()
                        ),
                        "boundary_components": bc_diagnostics,
                        "elapsed_seconds": time.perf_counter() - start,
                    }
                    log_handle.write(json.dumps(record, sort_keys=True) + "\n")
                    log_handle.flush()
                if (update + 1) % config.checkpoint_every == 0 and (
                    update + 1 < config.updates
                ):
                    torch.save(
                        _checkpoint_payload(
                            model=model,
                            optimizer=optimizer,
                            config=config,
                            update=update + 1,
                            program_contract_sha256=program_contract_sha256,
                            method_contract_sha256=method_contract_sha256,
                            physical_program_sha256=physical_program_sha256,
                            physical_object_sha256=physical_object_sha256,
                        ),
                        output / f"checkpoint-{update + 1:06d}.pt",
                    )
        torch.save(
            _checkpoint_payload(
                model=model,
                optimizer=optimizer,
                config=config,
                update=config.updates,
                program_contract_sha256=program_contract_sha256,
                method_contract_sha256=method_contract_sha256,
                physical_program_sha256=physical_program_sha256,
                physical_object_sha256=physical_object_sha256,
            ),
            checkpoint_path,
        )
    except BaseException:
        status = "FAILED"
        raise
    finally:
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        wall_seconds = time.perf_counter() - start
        peak_memory = (
            int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else 0
        )
        final_manifest = {
            **manifest,
            "status": status,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "wall_seconds": wall_seconds,
            "seconds_per_update": wall_seconds / max(config.updates, 1),
            "peak_gpu_memory_bytes": peak_memory,
            "final_loss": final_loss,
            "minimum_loss": minimum_loss,
        }
        _write_json_exclusive(output / "manifest-final.json", final_manifest)
    return TrainingOutcome(
        run_directory=output,
        status=status,
        final_loss=final_loss,
        minimum_loss=minimum_loss,
        wall_seconds=wall_seconds,
        seconds_per_update=wall_seconds / config.updates,
        peak_gpu_memory_bytes=peak_memory,
        checkpoint_path=checkpoint_path,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=[arm.value for arm in PhkV22RArm], required=True)
    parser.add_argument(
        "--case-control",
        choices=[
            PhkControl.FULL.value,
            PhkControl.INTERFACE_WIDTH_0_025.value,
            PhkControl.HEATER_WIDTH_0_50.value,
        ],
        default=PhkControl.FULL.value,
    )
    parser.add_argument("--run-directory", type=Path, required=True)
    parser.add_argument("--updates", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--hidden-width", type=int, default=64)
    parser.add_argument("--hidden-layers", type=int, default=4)
    parser.add_argument(
        "--frequency-band",
        choices=["BAND_A", "BAND_B_CONSERVATIVE"],
        default="BAND_A",
    )
    parser.add_argument("--learning-rate", type=float, default=1.0e-3)
    parser.add_argument("--interior-points", type=int, default=512)
    parser.add_argument("--boundary-points", type=int, default=128)
    parser.add_argument("--initial-points", type=int, default=128)
    parser.add_argument("--candidate-pool-multiplier", type=int, default=4)
    parser.add_argument("--refresh-updates", type=int, default=250)
    parser.add_argument("--log-every", type=int, default=25)
    parser.add_argument("--checkpoint-every", type=int, default=1000)
    parser.add_argument("--device", default="cpu")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    config = PhkTrainingConfig(
        arm=args.arm,
        case_control=args.case_control,
        updates=args.updates,
        seed=args.seed,
        hidden_width=args.hidden_width,
        hidden_layers=args.hidden_layers,
        frequency_band=args.frequency_band,
        learning_rate=args.learning_rate,
        interior_points=args.interior_points,
        boundary_points=args.boundary_points,
        initial_points=args.initial_points,
        candidate_pool_multiplier=args.candidate_pool_multiplier,
        refresh_updates=args.refresh_updates,
        log_every=args.log_every,
        checkpoint_every=args.checkpoint_every,
        device=args.device,
    )
    outcome = train(config, run_directory=args.run_directory)
    print(
        json.dumps(
            {
                "status": outcome.status,
                "run_directory": str(outcome.run_directory),
                "final_loss": outcome.final_loss,
                "minimum_loss": outcome.minimum_loss,
                "wall_seconds": outcome.wall_seconds,
                "seconds_per_update": outcome.seconds_per_update,
                "peak_gpu_memory_bytes": outcome.peak_gpu_memory_bytes,
                "checkpoint": str(outcome.checkpoint_path),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "BOUNDARY_SCALES",
    "INITIAL_SCALES",
    "METHOD_CONTRACT_PATH",
    "PDE_SCALES",
    "PhkTrainingConfig",
    "TrainingOutcome",
    "load_case_physics",
    "main",
    "train",
]
