"""Budget-aware orchestration for V2.2R GPU profiles and nominal pilots."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import time
from typing import Any, Iterable

import torch

from .phk_v22r_pinn import PhkV22RArm
from .phk_v22r_prediction import write_prediction_carrier
from .phk_v22r_training import PhkTrainingConfig, train


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


def environment_report(device_name: str) -> dict[str, Any]:
    device = torch.device(device_name)
    if device.type != "cuda" or not torch.cuda.is_available():
        raise RuntimeError("V2.2R GPU orchestration requires an available CUDA device")
    properties = torch.cuda.get_device_properties(device)
    tensor = torch.tensor([1.0], dtype=torch.float64, device=device)
    if tensor.dtype is not torch.float64:
        raise RuntimeError("CUDA float64 tensor construction failed")
    return {
        "schema_id": "phk-v22r-cloud-environment-v1",
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
    }


def _write_json_exclusive(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _spent_cny(start: float, hourly_price_cny: float) -> float:
    return (time.perf_counter() - start) / 3600.0 * hourly_price_cny


def _ensure_budget(
    *,
    start: float,
    hourly_price_cny: float,
    budget_cny: float,
    phase_budget_cny: float,
    prior_spend_cny: float,
    reserve_cny: float,
) -> None:
    projected_phase = _spent_cny(start, hourly_price_cny) + reserve_cny
    if projected_phase > phase_budget_cny:
        raise RuntimeError("cloud phase-allocation guard stopped the next run")
    if prior_spend_cny + projected_phase > budget_cny:
        raise RuntimeError("cloud budget guard stopped the next run")


def run_matrix(
    *,
    mode: str,
    output_root: Path,
    device: str,
    hourly_price_cny: float,
    budget_cny: float = 150.0,
    prior_spend_cny: float = 0.0,
    arms: Iterable[PhkV22RArm] | None = None,
) -> dict[str, Any]:
    if mode not in {"profile", "pilot"}:
        raise ValueError("sprint mode must be profile or pilot")
    if not math.isfinite(hourly_price_cny) or hourly_price_cny <= 0.0:
        raise ValueError("hourly cloud price must be positive")
    if budget_cny <= 0.0 or budget_cny > 150.0:
        raise ValueError("V2.2R cloud budget must lie in (0, 150]")
    if prior_spend_cny < 0.0 or prior_spend_cny >= budget_cny:
        raise ValueError("prior cloud spend must lie in [0, budget)")
    phase_budget_cny = budget_cny * (0.20 if mode == "profile" else 0.30)
    root = Path(output_root).resolve()
    root.mkdir(parents=True, exist_ok=False)
    environment = environment_report(device)
    _write_json_exclusive(root / "environment.json", environment)
    selected_arms = tuple(arms or PRIMARY_ARMS)
    if mode == "profile" and PhkV22RArm.STRICT_PHA_PROBE not in selected_arms:
        selected_arms = (*selected_arms, PhkV22RArm.STRICT_PHA_PROBE)
    updates = 100 if mode == "profile" else 1500
    start = time.perf_counter()
    records = []
    for index, arm in enumerate(selected_arms):
        spent = _spent_cny(start, hourly_price_cny)
        remaining_runs = len(selected_arms) - index
        observed_seconds = [record["wall_seconds"] for record in records]
        reserve_seconds = (
            max(observed_seconds) * remaining_runs
            if observed_seconds
            else 15.0 * 60.0
        )
        reserve_cny = reserve_seconds / 3600.0 * hourly_price_cny
        _ensure_budget(
            start=start,
            hourly_price_cny=hourly_price_cny,
            budget_cny=budget_cny,
            phase_budget_cny=phase_budget_cny,
            prior_spend_cny=prior_spend_cny,
            reserve_cny=reserve_cny,
        )
        config = PhkTrainingConfig(
            arm=arm.value,
            updates=updates,
            device=device,
            log_every=10 if mode == "profile" else 25,
            checkpoint_every=updates,
        )
        outcome = train(config, run_directory=root / arm.value.lower())
        prediction_record = None
        if mode == "pilot":
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
        records.append(
            {
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
                "checkpoint": str(outcome.checkpoint_path),
                "prediction": prediction_record,
                "estimated_phase_spend_cny_at_completion": _spent_cny(
                    start, hourly_price_cny
                ),
                "estimated_cumulative_spend_cny_at_completion": prior_spend_cny
                + _spent_cny(start, hourly_price_cny),
            }
        )
        _write_json_exclusive(root / f"ledger-{index + 1:02d}.json", records[-1])
    profile_adjudication = None
    if mode == "profile":
        by_arm = {record["arm"]: record for record in records}
        mf_cost = by_arm[PhkV22RArm.MF_ONLY.value]["seconds_per_update"]
        strict_cost = by_arm[PhkV22RArm.STRICT_PHA_PROBE.value][
            "seconds_per_update"
        ]
        cost_ratio = strict_cost / max(mf_cost, 1.0e-15)
        profile_adjudication = {
            "strict_pha_cost_ratio_to_mf": cost_ratio,
            "cost_gate_maximum": 1.8,
            "cost_gate_passed": cost_ratio <= 1.8,
            "routing_status": (
                "REQUIRES_NOMINAL_GAIN_GATE"
                if cost_ratio <= 1.8
                else "DELETE_STRICT_PHA_WITHOUT_GATE_TUNING"
            ),
        }
    summary = {
        "schema_id": "phk-v22r-cloud-matrix-v1",
        "status": "COMPLETE",
        "mode": mode,
        "hourly_price_cny": hourly_price_cny,
        "budget_cny": budget_cny,
        "phase_budget_cny": phase_budget_cny,
        "prior_spend_cny": prior_spend_cny,
        "actual_estimated_phase_spend_cny": _spent_cny(start, hourly_price_cny),
        "actual_estimated_cumulative_spend_cny": prior_spend_cny
        + _spent_cny(start, hourly_price_cny),
        "environment": environment,
        "runs": records,
        "profile_adjudication": profile_adjudication,
    }
    _write_json_exclusive(root / "summary.json", summary)
    return summary


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["profile", "pilot"], required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--hourly-price-cny", type=float, required=True)
    parser.add_argument("--budget-cny", type=float, default=150.0)
    parser.add_argument("--prior-spend-cny", type=float, default=0.0)
    parser.add_argument(
        "--arms",
        nargs="+",
        choices=[arm.value for arm in PhkV22RArm],
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    summary = run_matrix(
        mode=args.mode,
        output_root=args.output_root,
        device=args.device,
        hourly_price_cny=args.hourly_price_cny,
        budget_cny=args.budget_cny,
        prior_spend_cny=args.prior_spend_cny,
        arms=None if args.arms is None else tuple(PhkV22RArm(item) for item in args.arms),
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


__all__ = ["PRIMARY_ARMS", "environment_report", "main", "run_matrix"]
