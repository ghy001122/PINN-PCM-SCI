"""One-update engineering smoke for the four PHA attribution arms."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any, Sequence

import h5py
import numpy as np
import torch

from .ledger import ExperimentLedger, RunManifest
from .qpop_method_pilot import PilotBatches, pilot_loss
from .qpop_physics import QPopParameters
from .qpop_pinn import PHA_METHODS, QPopPINN


EVALUATOR_ID = "frozen-project-pha-method-smoke-evaluator-v1"


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _write_json_once(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _candidate_pool(seed: int) -> torch.Tensor:
    return torch.rand(
        (24, 3), generator=torch.Generator().manual_seed(seed), dtype=torch.float64
    )


def _selection_indices(model: QPopPINN, candidates: torch.Tensor, count: int) -> torch.Tensor:
    if model.method in {"pha_sampling", "pha_shared"}:
        weights = model.collocation_weights(candidates)[:, 0]
        return torch.topk(weights, k=count, largest=True, sorted=True).indices
    return torch.arange(count)


def _evaluate(predictions_path: Path, metrics_path: Path) -> int:
    with h5py.File(predictions_path, "r") as handle:
        if handle.attrs.get("schema_version") != "pha-method-smoke-predictions-v1":
            raise ValueError("unsupported PHA smoke prediction schema")
        all_finite = True
        for method in PHA_METHODS:
            group = handle[f"methods/{method}"]
            for name in (
                "fields",
                "physical_gate",
                "capacity_gate",
                "collocation_weights",
            ):
                all_finite = all_finite and bool(np.isfinite(group[name][...]).all())

        shared = handle["methods/pha_shared"]
        shared_gate = np.asarray(shared["physical_gate"])
        shared_delta = max(
            float(np.max(np.abs(np.asarray(shared["capacity_gate"]) - shared_gate))),
            float(
                np.max(
                    np.abs(
                        np.asarray(shared["collocation_weights"])
                        - (1.0 + float(handle.attrs["sampling_gain"]) * shared_gate)
                    )
                )
            ),
        )
        selected = np.asarray(shared["selected_indices"], dtype=np.int64)
        concentrated = bool(
            np.mean(shared_gate[selected]) + 1.0e-15 >= np.mean(shared_gate)
        )
        parameter_updates = {
            method: float(handle[f"methods/{method}"].attrs["parameter_delta_l2"])
            for method in PHA_METHODS
        }
        all_updated = all(delta > 0.0 for delta in parameter_updates.values())
    payload = {
        "schema_version": "pha-method-smoke-metrics-v1",
        "evaluator_id": EVALUATOR_ID,
        "all_finite": all_finite,
        "all_arms_updated": all_updated,
        "parameter_delta_l2": parameter_updates,
        "shared_gate_max_abs_delta": shared_delta,
        "shared_sampling_concentrated": concentrated,
    }
    _write_json_once(metrics_path, payload)
    return 0 if all_finite and all_updated and shared_delta <= 1.0e-12 and concentrated else 1


def run_pha_method_smoke(
    *,
    run_id: str,
    input_path: Path,
    output_root: Path,
    experiment_root: Path,
    seed: int,
    supersedes: str | None = None,
) -> int:
    started_at = _utc_now()
    started = time.monotonic()
    run_root = output_root / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    intent_path = experiment_root / "intents" / f"{run_id}.json"
    _write_json_once(
        intent_path,
        {
            "schema_version": "pha-method-smoke-intent-v1",
            "run_id": run_id,
            "tier": "smoke",
            "scientific_role": "pipeline",
            "gate": "G6_PHA",
            "methods": list(PHA_METHODS),
            "planned_optimizer_updates": len(PHA_METHODS),
            "training_uses_qpop_transient_labels": False,
            "claim_status": "NO_SCIENTIFIC_CLAIMS",
            "supersedes": supersedes,
            "started_at": started_at,
        },
    )

    failure: Exception | None = None
    updates: dict[str, dict[str, float]] = {}
    artifacts: dict[str, str] = {"intent": str(intent_path), "run_root": str(run_root)}
    predictions_path = run_root / "predictions.h5"
    metrics_path = run_root / "metrics.json"
    try:
        parameters = QPopParameters.from_input(input_path)
        candidates = _candidate_pool(seed)
        fixed = PilotBatches.fixed(
            seed=seed + 1, interior=4, initial=3, boundary_per_side=2
        )
        models: dict[str, QPopPINN] = {}
        common_state: dict[str, torch.Tensor] | None = None
        for method in PHA_METHODS:
            torch.manual_seed(seed)
            model = QPopPINN(
                parameters=parameters,
                horizon_ns=512.0793,
                method=method,
                hidden_width=8,
                hidden_layers=2,
            ).double()
            if common_state is None:
                common_state = {
                    name: value.detach().clone() for name, value in model.state_dict().items()
                }
            else:
                model.load_state_dict(common_state)
            models[method] = model

        checkpoint_root = run_root / "checkpoints"
        checkpoint_root.mkdir()
        with h5py.File(predictions_path, "x") as handle:
            handle.attrs["schema_version"] = "pha-method-smoke-predictions-v1"
            handle.attrs["evidence_identity"] = "QPOP_PHYSICS_CONTROL_FLOW_ONLY"
            handle.attrs["sampling_gain"] = models["pha_shared"].sampling_gain
            handle.create_dataset("candidates", data=candidates.numpy())
            for method, model in models.items():
                indices = _selection_indices(model, candidates, 4)
                batches = PilotBatches(
                    interior=candidates[indices],
                    initial=fixed.initial,
                    boundaries=fixed.boundaries,
                )
                optimizer = torch.optim.Adam(model.parameters(), lr=1.0e-4)
                before = torch.cat(
                    [parameter.detach().reshape(-1) for parameter in model.parameters()]
                )
                optimizer.zero_grad(set_to_none=True)
                loss, _ = pilot_loss(
                    model, batches, stop_gradient_clock_target=True
                )
                if not torch.isfinite(loss):
                    raise RuntimeError(f"{method} produced a non-finite smoke loss")
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 10.0)
                optimizer.step()
                after = torch.cat(
                    [parameter.detach().reshape(-1) for parameter in model.parameters()]
                )
                delta = float(torch.linalg.vector_norm(after - before))
                if not np.isfinite(delta) or delta <= 0.0:
                    raise RuntimeError(f"{method} did not update parameters")
                updates[method] = {
                    "loss_before": float(loss.detach()),
                    "parameter_delta_l2": delta,
                }
                checkpoint_path = checkpoint_root / f"{method}.pt"
                torch.save(model.state_dict(), checkpoint_path)
                artifacts[f"checkpoint_{method}"] = str(checkpoint_path)
                with torch.no_grad():
                    diagnostics = model.phase_hotspot_diagnostics(candidates)
                    weights = model.collocation_weights(candidates)
                group = handle.create_group(f"methods/{method}")
                group.attrs["parameter_delta_l2"] = delta
                group.create_dataset("fields", data=diagnostics.fields.numpy())
                group.create_dataset(
                    "physical_gate", data=diagnostics.physical_gate.numpy()
                )
                group.create_dataset(
                    "capacity_gate", data=diagnostics.capacity_gate.numpy()
                )
                group.create_dataset("collocation_weights", data=weights.numpy())
                group.create_dataset("selected_indices", data=indices.numpy())

        evaluator_stdout = run_root / "evaluator.stdout.log"
        evaluator_stderr = run_root / "evaluator.stderr.log"
        command = [
            sys.executable,
            "-m",
            "pinn_pcm_sci.pha_method_smoke",
            "evaluate",
            "--predictions",
            str(predictions_path),
            "--metrics",
            str(metrics_path),
        ]
        with evaluator_stdout.open("wb") as stdout, evaluator_stderr.open("wb") as stderr:
            completed = subprocess.run(
                command, stdout=stdout, stderr=stderr, timeout=60, check=False
            )
        if completed.returncode != 0:
            raise RuntimeError(
                f"independent PHA smoke evaluator returned {completed.returncode}"
            )
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        if metrics.get("evaluator_id") != EVALUATOR_ID:
            raise RuntimeError("independent PHA smoke evaluator identity mismatch")
        artifacts.update(
            {
                "predictions": str(predictions_path),
                "metrics": str(metrics_path),
                "evaluator_stdout": str(evaluator_stdout),
                "evaluator_stderr": str(evaluator_stderr),
            }
        )
    except Exception as exc:
        failure = exc

    manifest = RunManifest(
        run_id=run_id,
        experiment_group_id="g6-pha-method-engineering-smoke-v1",
        tier="smoke",
        scientific_role="pipeline",
        gate="G6_PHA",
        started_at=started_at,
        ended_at=_utc_now(),
        command=["python", "-m", "pinn_pcm_sci.pha_method_smoke", "run"],
        execution_status="FAILED" if failure else "COMPLETED",
        numerical_validity="NOT_EVALUATED" if failure else "VALID_ENGINEERING_SMOKE",
        gate_outcome="G6_PHA_METHOD_SMOKE_FAILED" if failure else "G6_PHA_METHOD_SMOKE_PASS",
        route_disposition="BLOCKED_ENGINEERING" if failure else "CONTINUE_PHA_DEVELOPMENT_ONLY",
        evidence_identity="QPOP_PHYSICS_METHOD_CONTROL_FLOW_ONLY",
        claim_status="NO_SCIENTIFIC_CLAIMS",
        code_identity={"kind": "working-tree", "dirty": True},
        environment={
            "python": platform.python_version(),
            "torch": torch.__version__,
            "dtype": "float64",
            "device": "cpu",
        },
        physical_contract_id="PROVISIONAL_G3_QPOP_CPC_V1_IMT_CONTRACT",
        split_id="NON_SCIENTIFIC_FIXED_PHA_SMOKE_COORDINATES_V1",
        method_id="fourier-pha-capacity-sampling-shared-one-update-smoke-v1",
        case_id="qpop-cpc-v1-equations-non-oracle-smoke-v1",
        seed=seed,
        planned_budget={"methods": len(PHA_METHODS), "optimizer_updates_per_method": 1},
        actual_budget={
            "optimizer_updates": len(updates),
            "candidate_points": 24,
            "selected_points_per_method": 4,
            "wall_seconds": time.monotonic() - started,
            "updates": updates,
        },
        checkpoint={"id": "one-update-each", "selection": "NOT_APPLICABLE_SMOKE"},
        evaluator_id=EVALUATOR_ID,
        artifacts=artifacts,
        failure_class=None if failure is None else type(failure).__name__,
        replay_of=None,
        supersedes=supersedes,
    )
    ledger = ExperimentLedger(experiment_root)
    ledger.record(manifest)
    ledger.validate()
    if failure is not None:
        raise failure
    return 0


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--run-id", required=True)
    run_parser.add_argument("--input", type=Path, required=True)
    run_parser.add_argument("--output-root", type=Path, default=Path("outputs/runs"))
    run_parser.add_argument(
        "--experiment-root", type=Path, default=Path("docs/experiment")
    )
    run_parser.add_argument("--seed", type=int, default=13)
    run_parser.add_argument("--supersedes")
    evaluate_parser = subparsers.add_parser("evaluate")
    evaluate_parser.add_argument("--predictions", type=Path, required=True)
    evaluate_parser.add_argument("--metrics", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.command == "evaluate":
        return _evaluate(args.predictions, args.metrics)
    return run_pha_method_smoke(
        run_id=args.run_id,
        input_path=args.input,
        output_root=args.output_root,
        experiment_root=args.experiment_root,
        seed=args.seed,
        supersedes=args.supersedes,
    )


if __name__ == "__main__":
    raise SystemExit(main())
