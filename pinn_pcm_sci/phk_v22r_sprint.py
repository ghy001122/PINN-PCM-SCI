"""Frozen PHK-V2.2R v1.1 four-arm nominal GPU orchestration."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sys
import time
from typing import Any

import torch

from .phk_v22r_pinn import PhkV22RArm
from .phk_v22r_prediction import write_prediction_carrier
from .phk_v22r_training import PhkTrainingConfig, train


ROOT = Path(__file__).resolve().parents[1]
PROGRAM_CONTRACT = ROOT / "configs" / "phk_v22r" / "program_contract.json"
METHOD_CONTRACT = ROOT / "configs" / "phk_v22r" / "method_contract.json"

PRIMARY_ARMS = (
    PhkV22RArm.STRONG_RAW,
    PhkV22RArm.MF_ONLY,
    PhkV22RArm.SAMPLER_ONLY,
    PhkV22RArm.MF_PLUS_SAMPLER,
)


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid frozen contract: {path}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"frozen contract is not a JSON object: {path}")
    return payload


def validate_v11_execution_contract() -> dict[str, Any]:
    """Fail closed unless the executable and both live contracts agree exactly."""

    program = _load_json(PROGRAM_CONTRACT)
    method = _load_json(METHOD_CONTRACT)
    expected_arms = [arm.value for arm in PRIMARY_ARMS]
    if program.get("schema_id") != "phk-v22r-program-contract-v1-1":
        raise RuntimeError("PHK-V2.2R v1.1 program contract is not active")
    if method.get("schema_id") != "phk-v22r-method-contract-v1-1":
        raise RuntimeError("PHK-V2.2R v1.1 method contract is not active")
    nominal_program = program.get("nominal_matrix")
    nominal_method = method.get("nominal_training")
    if not isinstance(nominal_program, dict) or not isinstance(nominal_method, dict):
        raise RuntimeError("v1.1 contracts lack the nominal matrix")
    for nominal in (nominal_program, nominal_method):
        if nominal.get("arms_in_order") != expected_arms:
            raise RuntimeError("v1.1 contract changed the frozen four-arm order")
        required = {
            "case_control": "FULL",
            "only_advancement_arm": PhkV22RArm.MF_PLUS_SAMPLER.value,
            "seed": 17,
            "dtype": "FLOAT64",
            "frequency_band": "BAND_A",
            "initialization": "SCRATCH_START",
            "optimizer": "ADAM",
            "updates": 1000,
            "interior_points": 512,
            "boundary_points": 128,
            "initial_points": 128,
            "checkpoint_policy": "FINAL_ONLY",
        }
        for key, value in required.items():
            if nominal.get(key) != value:
                raise RuntimeError(f"v1.1 nominal contract mismatch: {key}")
    disabled = set(program.get("disabled_for_this_sprint", ()))
    mandatory_disabled = {
        "STRICT_PHA",
        "GENERIC_RAR",
        "ROUTE_B",
        "ROUTE_C",
        "FUNCTIONAL_PIVOT",
        "WARM_START",
        "EARLY_STOP",
        "LBFGS",
    }
    if not mandatory_disabled.issubset(disabled):
        raise RuntimeError("v1.1 contract did not disable every legacy rescue axis")
    return {
        "program_schema_id": program["schema_id"],
        "program_contract_sha256": _sha256_path(PROGRAM_CONTRACT),
        "method_schema_id": method["schema_id"],
        "method_contract_sha256": _sha256_path(METHOD_CONTRACT),
    }


def _omp_threads() -> int:
    raw = os.environ.get("OMP_NUM_THREADS")
    try:
        value = int(raw) if raw is not None else 0
    except ValueError as exc:
        raise RuntimeError("OMP_NUM_THREADS must be an explicit positive integer") from exc
    if value <= 0:
        raise RuntimeError("OMP_NUM_THREADS must be an explicit positive integer")
    return value


def environment_report(device_name: str) -> dict[str, Any]:
    device = torch.device(device_name)
    if device.type != "cuda" or not torch.cuda.is_available():
        raise RuntimeError("V2.2R nominal orchestration requires an available CUDA device")
    properties = torch.cuda.get_device_properties(device)
    tensor = torch.tensor([1.0], dtype=torch.float64, device=device)
    if tensor.dtype is not torch.float64:
        raise RuntimeError("CUDA float64 tensor construction failed")
    return {
        "schema_id": "phk-v22r-cloud-environment-v1-1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "torch": torch.__version__,
        "cuda_runtime": torch.version.cuda,
        "cudnn": torch.backends.cudnn.version(),
        "device_name": properties.name,
        "device_total_memory_bytes": properties.total_memory,
        "device_capability": list(torch.cuda.get_device_capability(device)),
        "float64_probe": True,
        "omp_num_threads": _omp_threads(),
    }


def _write_json_exclusive(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(serialized)
        handle.write("\n")


def _spent_cny(start: float, hourly_price_cny: float) -> float:
    return (time.perf_counter() - start) / 3600.0 * hourly_price_cny


def _ensure_budget(
    *,
    start: float,
    hourly_price_cny: float,
    budget_cny: float,
    prior_spend_cny: float,
    reserve_cny: float,
) -> None:
    projected = prior_spend_cny + _spent_cny(start, hourly_price_cny) + reserve_cny
    if projected > budget_cny:
        raise RuntimeError("cloud hard-budget guard stopped the next nominal arm")


def run_matrix(
    *,
    mode: str,
    output_root: Path,
    device: str,
    hourly_price_cny: float,
    source_identity: str,
    budget_cny: float = 150.0,
    prior_spend_cny: float = 0.0,
) -> dict[str, Any]:
    """Run exactly the frozen v1.1 nominal matrix and emit final predictions."""

    if mode != "nominal":
        raise ValueError("PHK-V2.2R v1.1 runner accepts only mode=nominal")
    if not source_identity.strip():
        raise ValueError("source identity must be non-empty")
    if not math.isfinite(hourly_price_cny) or hourly_price_cny <= 0.0:
        raise ValueError("hourly cloud price must be positive")
    if budget_cny <= 0.0 or budget_cny > 150.0:
        raise ValueError("V2.2R cloud budget must lie in (0, 150]")
    if prior_spend_cny < 0.0 or prior_spend_cny >= budget_cny:
        raise ValueError("prior cloud spend must lie in [0, budget)")

    contract_identity = validate_v11_execution_contract()
    root = Path(output_root).resolve()
    root.mkdir(parents=True, exist_ok=False)
    environment = environment_report(device)
    _write_json_exclusive(root / "environment.json", environment)
    start = time.perf_counter()
    records: list[dict[str, Any]] = []
    for index, arm in enumerate(PRIMARY_ARMS):
        remaining_runs = len(PRIMARY_ARMS) - index
        observed_seconds = [float(record["wall_seconds"]) for record in records]
        reserve_seconds = (
            max(observed_seconds) * remaining_runs
            if observed_seconds
            else 15.0 * 60.0 * remaining_runs
        )
        _ensure_budget(
            start=start,
            hourly_price_cny=hourly_price_cny,
            budget_cny=budget_cny,
            prior_spend_cny=prior_spend_cny,
            reserve_cny=reserve_seconds / 3600.0 * hourly_price_cny,
        )
        config = PhkTrainingConfig(
            arm=arm.value,
            case_control="FULL",
            updates=1000,
            seed=17,
            hidden_width=64,
            hidden_layers=4,
            frequency_band="BAND_A",
            learning_rate=1.0e-3,
            gradient_clip_norm=10.0,
            interior_points=512,
            boundary_points=128,
            initial_points=128,
            candidate_pool_multiplier=4,
            refresh_updates=250,
            log_every=25,
            checkpoint_every=1000,
            pde_weight=1.0,
            boundary_weight=5.0,
            initial_weight=1.0,
            dtype="float64",
            device=device,
        )
        outcome = train(config, run_directory=root / arm.value.lower())
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        prediction_start = time.perf_counter()
        prediction_path = outcome.run_directory / "prediction-extra-fine-axes.npz"
        write_prediction_carrier(
            checkpoint_path=outcome.checkpoint_path,
            output_path=prediction_path,
            device_name=device,
        )
        prediction_record = {
            "path": str(prediction_path),
            "sha256": _sha256_path(prediction_path),
            "size_bytes": prediction_path.stat().st_size,
            "wall_seconds": time.perf_counter() - prediction_start,
            "reference_fields_read": False,
        }
        record = {
            "arm": arm.value,
            "config": asdict(config),
            "training_config_sha256": config.identity,
            "status": outcome.status,
            "wall_seconds": outcome.wall_seconds,
            "seconds_per_update": outcome.seconds_per_update,
            "peak_gpu_memory_bytes": outcome.peak_gpu_memory_bytes,
            "final_loss": outcome.final_loss,
            "minimum_loss": outcome.minimum_loss,
            "run_directory": str(outcome.run_directory),
            "checkpoint": {
                "path": str(outcome.checkpoint_path),
                "sha256": _sha256_path(outcome.checkpoint_path),
            },
            "prediction": prediction_record,
            "estimated_phase_spend_cny_at_completion": _spent_cny(
                start, hourly_price_cny
            ),
            "estimated_cumulative_spend_cny_at_completion": prior_spend_cny
            + _spent_cny(start, hourly_price_cny),
        }
        records.append(record)
        _write_json_exclusive(root / f"ledger-{index + 1:02d}.json", record)

    summary = {
        "schema_id": "phk-v22r-cloud-nominal-matrix-v1-1",
        "status": "COMPLETE_REFERENCE_BLIND_NOMINAL",
        "mode": mode,
        "source_identity": source_identity,
        "hourly_price_cny": hourly_price_cny,
        "budget_cny": budget_cny,
        "prior_spend_cny": prior_spend_cny,
        "actual_estimated_phase_spend_cny": _spent_cny(start, hourly_price_cny),
        "actual_estimated_cumulative_spend_cny": prior_spend_cny
        + _spent_cny(start, hourly_price_cny),
        "contract_identity": contract_identity,
        "environment": environment,
        "runs": records,
        "reference_fields_read": False,
        "next_action": "DOWNLOAD_AND_ADJUDICATE_NOMINAL_LOCALLY",
    }
    _write_json_exclusive(root / "summary.json", summary)
    return summary


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["nominal"], required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--hourly-price-cny", type=float, required=True)
    parser.add_argument("--source-identity", required=True)
    parser.add_argument("--budget-cny", type=float, default=150.0)
    parser.add_argument("--prior-spend-cny", type=float, default=0.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    summary = run_matrix(
        mode=args.mode,
        output_root=args.output_root,
        device=args.device,
        hourly_price_cny=args.hourly_price_cny,
        source_identity=args.source_identity,
        budget_cny=args.budget_cny,
        prior_spend_cny=args.prior_spend_cny,
    )
    print(
        json.dumps(
            {
                "status": summary["status"],
                "mode": summary["mode"],
                "actual_estimated_phase_spend_cny": summary[
                    "actual_estimated_phase_spend_cny"
                ],
                "actual_estimated_cumulative_spend_cny": summary[
                    "actual_estimated_cumulative_spend_cny"
                ],
                "run_count": len(summary["runs"]),
                "output_root": str(Path(args.output_root).resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "PRIMARY_ARMS",
    "environment_report",
    "main",
    "run_matrix",
    "validate_v11_execution_contract",
]
