"""Bounded non-scientific smoke for raw-time, identity-clock, and KC training."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any, Callable, Sequence

import h5py
import numpy as np
import torch
from torch import nn

from .kinetics_clock import IdentityClock, PositiveGaussianClock, full_pullback, make_mlp
from .ledger import ExperimentLedger, RunManifest


EVALUATOR_ID = "frozen-project-method-smoke-evaluator-v1"


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _write_json_once(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _direct_derivatives(
    model: nn.Module, coordinates: torch.Tensor
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    value = model(coordinates)
    gradient = torch.autograd.grad(
        value.sum(), coordinates, create_graph=True, retain_graph=True
    )[0]
    rows = [
        torch.autograd.grad(
            gradient[:, index].sum(),
            coordinates,
            create_graph=True,
            retain_graph=True,
        )[0]
        for index in range(coordinates.shape[1])
    ]
    return value, gradient, torch.stack(rows, dim=1)


def _manufactured_target(coordinates: torch.Tensor) -> torch.Tensor:
    x, y, time_coordinate = (
        coordinates[:, 0:1],
        coordinates[:, 1:2],
        coordinates[:, 2:3],
    )
    return torch.sin(math.pi * x) * torch.sin(math.pi * y) * torch.exp(-time_coordinate)


def _forcing(coordinates: torch.Tensor) -> torch.Tensor:
    return (2.0 * math.pi * math.pi - 1.0) * _manufactured_target(coordinates)


def _loss_from_derivatives(
    value: torch.Tensor,
    gradient: torch.Tensor,
    hessian: torch.Tensor,
    coordinates: torch.Tensor,
) -> torch.Tensor:
    residual = (
        gradient[:, 2:3]
        - hessian[:, 0, 0:1]
        - hessian[:, 1, 1:2]
        - _forcing(coordinates)
    )
    fixture_anchor = value - _manufactured_target(coordinates)
    return residual.square().mean() + 0.1 * fixture_anchor.square().mean()


def _parameter_vector(parameters: Sequence[torch.Tensor]) -> torch.Tensor:
    return torch.cat([parameter.detach().reshape(-1) for parameter in parameters])


def _one_update(
    *,
    parameters: Sequence[torch.Tensor],
    closure: Callable[[], torch.Tensor],
) -> dict[str, float]:
    optimizer = torch.optim.Adam(parameters, lr=1e-3)
    before = _parameter_vector(parameters)
    optimizer.zero_grad(set_to_none=True)
    loss = closure()
    if not torch.isfinite(loss):
        raise RuntimeError("method smoke produced a non-finite training loss")
    loss.backward()
    optimizer.step()
    after = _parameter_vector(parameters)
    delta = torch.linalg.vector_norm(after - before)
    if not torch.isfinite(delta) or float(delta) <= 0.0:
        raise RuntimeError("method smoke optimizer did not update trainable parameters")
    return {"loss_before": float(loss.detach()), "parameter_delta_l2": float(delta)}


def _collocation_grid() -> torch.Tensor:
    axis = torch.linspace(0.1, 0.9, 3, dtype=torch.float64)
    time_axis = torch.linspace(0.0, 1.0, 3, dtype=torch.float64)
    return torch.cartesian_prod(axis, axis, time_axis)


def _evaluate_predictions(predictions_path: Path, metrics_path: Path) -> int:
    with h5py.File(predictions_path, "r") as handle:
        if handle.attrs.get("schema_version") != "method-smoke-predictions-v1":
            raise ValueError("unsupported method smoke prediction schema")
        values = [np.asarray(handle[f"methods/{name}/prediction"]) for name in ("raw", "identity", "kc")]
        all_finite = bool(all(np.isfinite(value).all() for value in values))
        raw_identity_initial = float(handle.attrs["raw_identity_initial_max_abs"])
    payload = {
        "schema_version": "method-smoke-metrics-v1",
        "evaluator_id": EVALUATOR_ID,
        "all_finite": all_finite,
        "raw_identity_initial_max_abs": raw_identity_initial,
    }
    _write_json_once(metrics_path, payload)
    return 0 if all_finite and raw_identity_initial <= 1e-12 else 1


def run_method_smoke(
    *,
    run_id: str,
    output_root: Path,
    experiment_root: Path,
    seed: int,
) -> int:
    started_at = _utc_now()
    started = time.monotonic()
    run_root = output_root / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    intent_path = experiment_root / "intents" / f"{run_id}.json"
    intent = {
        "schema_version": "method-smoke-intent-v1",
        "run_id": run_id,
        "tier": "smoke",
        "scientific_role": "pipeline",
        "gate": "G4",
        "seed": seed,
        "planned_optimizer_updates": 3,
        "evidence_identity": "NON_SCIENTIFIC_MANUFACTURED_PULLBACK_FIXTURE",
        "claim_status": "NO_SCIENTIFIC_CLAIMS",
        "started_at": started_at,
    }
    _write_json_once(intent_path, intent)
    torch.manual_seed(seed)
    coordinates = _collocation_grid()
    base = make_mlp(3, 1, hidden_width=8, hidden_layers=2).double()
    raw_model = make_mlp(3, 1, hidden_width=8, hidden_layers=2).double()
    identity_model = make_mlp(3, 1, hidden_width=8, hidden_layers=2).double()
    kc_model = make_mlp(3, 1, hidden_width=8, hidden_layers=2).double()
    raw_model.load_state_dict(base.state_dict())
    identity_model.load_state_dict(base.state_dict())
    kc_model.load_state_dict(base.state_dict())
    identity_clock = IdentityClock()
    kc_clock = PositiveGaussianClock(
        spatial_dim=2,
        centers=(0.25, 0.75),
        widths=(0.2, 0.2),
        kappa_floor=0.1,
        hidden_width=5,
    ).double()

    raw_coordinates = coordinates.detach().clone().requires_grad_(True)
    raw_initial = _direct_derivatives(raw_model, raw_coordinates)
    identity_coordinates = coordinates.detach().clone().requires_grad_(True)
    identity_initial_pullback = full_pullback(
        identity_model, identity_clock, identity_coordinates
    )
    initial_differences = [
        torch.max(torch.abs(raw_initial[0] - identity_initial_pullback.value)),
        torch.max(
            torch.abs(raw_initial[1] - identity_initial_pullback.physical_gradient)
        ),
        torch.max(
            torch.abs(raw_initial[2] - identity_initial_pullback.physical_hessian)
        ),
    ]
    raw_identity_initial_max_abs = float(torch.stack(initial_differences).max())
    if raw_identity_initial_max_abs > 1e-12:
        raise RuntimeError("identity clock differs from raw-time derivatives")

    def raw_closure() -> torch.Tensor:
        current = coordinates.detach().clone().requires_grad_(True)
        return _loss_from_derivatives(*_direct_derivatives(raw_model, current), current)

    def identity_closure() -> torch.Tensor:
        current = coordinates.detach().clone().requires_grad_(True)
        pullback = full_pullback(identity_model, identity_clock, current)
        return _loss_from_derivatives(
            pullback.value,
            pullback.physical_gradient,
            pullback.physical_hessian,
            current,
        )

    def kc_closure() -> torch.Tensor:
        current = coordinates.detach().clone().requires_grad_(True)
        pullback = full_pullback(kc_model, kc_clock, current)
        return _loss_from_derivatives(
            pullback.value,
            pullback.physical_gradient,
            pullback.physical_hessian,
            current,
        )

    updates = {
        "raw": _one_update(parameters=list(raw_model.parameters()), closure=raw_closure),
        "identity": _one_update(
            parameters=list(identity_model.parameters()), closure=identity_closure
        ),
        "kc": _one_update(
            parameters=[*kc_model.parameters(), *kc_clock.parameters()],
            closure=kc_closure,
        ),
    }
    checkpoint_root = run_root / "checkpoints"
    checkpoint_root.mkdir()
    torch.save(raw_model.state_dict(), checkpoint_root / "raw.pt")
    torch.save(identity_model.state_dict(), checkpoint_root / "identity.pt")
    torch.save(
        {"eta": kc_model.state_dict(), "clock": kc_clock.state_dict()},
        checkpoint_root / "kc.pt",
    )

    predictions_path = run_root / "predictions.h5"
    with torch.enable_grad():
        evaluation_coordinates = coordinates.detach().clone().requires_grad_(True)
        raw_prediction = raw_model(evaluation_coordinates).detach().cpu().numpy()
        identity_prediction = full_pullback(
            identity_model, identity_clock, evaluation_coordinates
        ).value.detach().cpu().numpy()
        kc_prediction = full_pullback(
            kc_model, kc_clock, evaluation_coordinates
        ).value.detach().cpu().numpy()
    with h5py.File(predictions_path, "x") as handle:
        handle.attrs["schema_version"] = "method-smoke-predictions-v1"
        handle.attrs["evidence_identity"] = "NON_SCIENTIFIC_MANUFACTURED_PULLBACK_FIXTURE"
        handle.attrs["raw_identity_initial_max_abs"] = raw_identity_initial_max_abs
        handle.create_dataset("coordinates", data=coordinates.cpu().numpy())
        for name, prediction in (
            ("raw", raw_prediction),
            ("identity", identity_prediction),
            ("kc", kc_prediction),
        ):
            handle.create_dataset(f"methods/{name}/prediction", data=prediction)

    metrics_path = run_root / "metrics.json"
    evaluator_stdout = run_root / "evaluator.stdout.log"
    evaluator_stderr = run_root / "evaluator.stderr.log"
    command = [
        sys.executable,
        "-m",
        "pinn_pcm_sci.method_smoke",
        "evaluate",
        "--predictions",
        str(predictions_path),
        "--metrics",
        str(metrics_path),
    ]
    with evaluator_stdout.open("wb") as stdout, evaluator_stderr.open("wb") as stderr:
        completed = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=60, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"independent method smoke evaluator returned {completed.returncode}")
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    if metrics.get("evaluator_id") != EVALUATOR_ID or metrics.get("all_finite") is not True:
        raise RuntimeError("independent method smoke evaluator output is invalid")

    ended_at = _utc_now()
    manifest = RunManifest(
        run_id=run_id,
        experiment_group_id="g4-method-engineering-smoke-v1",
        tier="smoke",
        scientific_role="pipeline",
        gate="G4",
        started_at=started_at,
        ended_at=ended_at,
        command=["python", "-m", "pinn_pcm_sci.method_smoke", "run"],
        execution_status="COMPLETED",
        numerical_validity="VALID_ENGINEERING_SMOKE",
        gate_outcome="G4_METHOD_SMOKE_PASS",
        route_disposition="CONTINUE_G3_G4",
        evidence_identity="ENGINEERING_METHOD_CONTROL_FLOW_ONLY",
        claim_status="NO_SCIENTIFIC_CLAIMS",
        code_identity={"kind": "working-tree", "dirty": True},
        environment={
            "python": platform.python_version(),
            "torch": torch.__version__,
            "dtype": "float64",
            "device": "cpu",
        },
        physical_contract_id="NON_SCIENTIFIC_MANUFACTURED_PULLBACK_FIXTURE",
        split_id="NON_SCIENTIFIC_FIXED_COLLOCATION_GRID_V1",
        method_id="raw-identity-kc-one-update-smoke-v1",
        case_id="manufactured-2d-diffusion-pullback-fixture-v1",
        seed=seed,
        planned_budget={"optimizer_updates_per_method": 1, "methods": 3},
        actual_budget={
            "optimizer_updates": 3,
            "collocation_points": int(coordinates.shape[0]),
            "wall_seconds": time.monotonic() - started,
            "updates": updates,
        },
        checkpoint={"id": "one-update-each", "selection": "NOT_APPLICABLE_SMOKE"},
        evaluator_id=EVALUATOR_ID,
        artifacts={
            "intent": str(intent_path),
            "run_root": str(run_root),
            "predictions": str(predictions_path),
            "metrics": str(metrics_path),
            "raw_checkpoint": str(checkpoint_root / "raw.pt"),
            "identity_checkpoint": str(checkpoint_root / "identity.pt"),
            "kc_checkpoint": str(checkpoint_root / "kc.pt"),
        },
        failure_class=None,
        replay_of=None,
        supersedes=None,
    )
    ExperimentLedger(experiment_root).record(manifest)
    ExperimentLedger(experiment_root).validate()
    return 0


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    evaluate_parser = subparsers.add_parser("evaluate")
    evaluate_parser.add_argument("--predictions", type=Path, required=True)
    evaluate_parser.add_argument("--metrics", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.command == "evaluate":
        return _evaluate_predictions(args.predictions, args.metrics)
    raise RuntimeError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
