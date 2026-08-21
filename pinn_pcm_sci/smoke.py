from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
import h5py

from .artifacts import CaseArtifact, PredictionArtifact
from .ledger import ExperimentLedger, RunManifest


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_fixture(source: Path) -> dict[str, Any]:
    return json.loads(source.read_text(encoding="utf-8"))


def _convert_fixture(source: Path, destination: Path) -> CaseArtifact:
    raw = _load_fixture(source)
    artifact = CaseArtifact(
        case_id=str(raw["case_id"]),
        physical_contract_id=str(raw["physical_contract_id"]),
        evidence_identity=str(raw["evidence_identity"]),
        nodes=np.asarray(raw["nodes"], dtype=np.float64),
        cells=np.asarray(raw["cells"], dtype=np.int64),
        mesh_unit=str(raw["mesh_unit"]),
        field_time=np.asarray(raw["field_time"], dtype=np.float64),
        circuit_time=np.asarray(raw["circuit_time"], dtype=np.float64),
        time_unit=str(raw["time_unit"]),
        fields={
            name: np.asarray(values, dtype=np.float64)
            for name, values in raw["fields"].items()
        },
        field_units={str(name): str(unit) for name, unit in raw["field_units"].items()},
        field_registry={
            str(name): {str(key): str(value) for key, value in entry.items()}
            for name, entry in raw["field_registry"].items()
        },
        breakpoints=np.asarray(raw["breakpoints"], dtype=np.float64),
        circuit={
            name: np.asarray(values, dtype=np.float64)
            for name, values in raw["circuit"].items()
        },
        circuit_units={
            str(name): str(unit) for name, unit in raw["circuit_units"].items()
        },
    )
    artifact.write(destination)
    return artifact


def _code_identity() -> dict[str, Any]:
    revision = "UNAVAILABLE"
    dirty = True
    try:
        revision_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        revision = revision_result.stdout.strip()
        dirty = bool(status_result.stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        pass
    return {"kind": "working-tree", "revision": revision, "dirty": dirty}


def _train_one_step(case: CaseArtifact, checkpoint_path: Path, seed: int) -> np.ndarray:
    torch.manual_seed(seed)
    torch.set_default_dtype(torch.float64)
    time_grid, node_grid = np.meshgrid(
        case.field_time,
        np.arange(case.nodes.shape[0]),
        indexing="ij",
    )
    coordinates = np.column_stack(
        (
            case.nodes[node_grid.reshape(-1), 0],
            case.nodes[node_grid.reshape(-1), 1],
            time_grid.reshape(-1),
        )
    )
    inputs = torch.from_numpy(coordinates)
    targets = torch.from_numpy(case.fields["eta"].reshape(-1, 1))
    model = torch.nn.Sequential(
        torch.nn.Linear(3, 4),
        torch.nn.Tanh(),
        torch.nn.Linear(4, 1),
    )
    optimizer = torch.optim.SGD(model.parameters(), lr=1.0e-2)
    optimizer.zero_grad(set_to_none=True)
    prediction = model(inputs)
    loss = torch.mean(torch.square(prediction - targets))
    loss.backward()
    optimizer.step()
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "optimizer_steps": 1,
            "seed": seed,
            "evidence_identity": "ENGINEERING_CONTROL_FLOW_ONLY",
        },
        checkpoint_path,
    )
    with torch.no_grad():
        return model(inputs).cpu().numpy().reshape(
            case.field_time.size, case.nodes.shape[0]
        )


def _write_evaluation_contract(run_root: Path, case: CaseArtifact) -> tuple[Path, Path]:
    split_path = run_root / "split.json"
    metric_spec_path = run_root / "metric_spec.json"
    split_path.write_text(
        json.dumps(
            {
                "schema_version": "split-manifest-v1",
                "split_id": "fixture-split-v1",
                "cases": {case.case_id: "smoke_fixture"},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    boundaries = [
        float(case.field_time[0]),
        *map(float, case.breakpoints),
        float(case.field_time[-1]),
    ]
    cycle_windows = [
        [boundaries[index], boundaries[index + 1]]
        for index in range(len(boundaries) - 1)
    ]
    metric_spec_path.write_text(
        json.dumps(
            {
                "schema_version": "metric-spec-v1",
                "evaluator_id": "fixture-evaluator-v1",
                "structure_field": "eta",
                "structure_threshold": 0.5,
                "cycle_windows": cycle_windows,
                "device_channel": "voltage",
                "device_scale": 1.0,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return split_path, metric_spec_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the bounded G1 pipeline smoke.")
    parser.add_argument("--raw-fixture", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--experiment-root", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--seed", required=True, type=int)
    return parser


def run(args: argparse.Namespace) -> int:
    started_at = _utc_now()
    run_root = args.output_root / args.run_id
    run_root.mkdir(parents=True, exist_ok=False)
    ledger = ExperimentLedger(args.experiment_root)
    case_id = "UNKNOWN"
    physical_contract_id = "UNKNOWN"
    split_id = "fixture-split-v1"
    method_id = "fixture-model-v1"
    evaluator_id = "fixture-evaluator-v1"
    artifacts: dict[str, str] = {}
    try:
        case_path = run_root / "case.h5"
        checkpoint_path = run_root / "checkpoint.pt"
        prediction_path = run_root / "prediction.h5"
        metrics_path = run_root / "metrics.json"
        case = _convert_fixture(args.raw_fixture, case_path)
        case_id = case.case_id
        physical_contract_id = case.physical_contract_id
        eta_prediction = _train_one_step(case, checkpoint_path, args.seed)
        prediction = PredictionArtifact(
            case_id=case.case_id,
            physical_contract_id=case.physical_contract_id,
            method_id=method_id,
            checkpoint_id="step-0001",
            field_time=case.field_time,
            circuit_time=case.circuit_time,
            time_unit=case.time_unit,
            mesh_identity=case.mesh_identity,
            fields={"eta": eta_prediction},
            field_units={"eta": case.field_units["eta"]},
            field_registry={"eta": case.field_registry["eta"]},
            circuit={"voltage": case.circuit["voltage"].copy()},
            circuit_units={"voltage": case.circuit_units["voltage"]},
        )
        prediction.write(prediction_path)
        split_path, metric_spec_path = _write_evaluation_contract(run_root, case)
        evaluator_command = [
            sys.executable,
            "-m",
            "pinn_pcm_sci.evaluate",
            "--prediction",
            str(prediction_path),
            "--oracle",
            str(case_path),
            "--split",
            str(split_path),
            "--metric-spec",
            str(metric_spec_path),
            "--out",
            str(metrics_path),
        ]
        subprocess.run(evaluator_command, check=True, cwd=Path.cwd())
        artifacts = {
            "case": str(case_path),
            "checkpoint": str(checkpoint_path),
            "prediction": str(prediction_path),
            "metrics": str(metrics_path),
            "split": str(split_path),
            "metric_spec": str(metric_spec_path),
        }
        manifest = RunManifest(
            run_id=args.run_id,
            experiment_group_id="g1-pipeline-smoke-v1",
            tier="smoke",
            scientific_role="pipeline",
            gate="G1",
            started_at=started_at,
            ended_at=_utc_now(),
            command=list(sys.argv),
            execution_status="COMPLETED",
            numerical_validity="NOT_APPLICABLE_ENGINEERING_SMOKE",
            gate_outcome="SMOKE_PASS",
            route_disposition=None,
            evidence_identity="ENGINEERING_CONTROL_FLOW_ONLY",
            claim_status="NO_NUMERICAL_EVIDENCE",
            code_identity=_code_identity(),
            environment={
                "python": platform.python_version(),
                "torch": torch.__version__,
                "numpy": np.__version__,
                "h5py": h5py.__version__,
                "platform": platform.platform(),
                "runtime": "cpu",
            },
            physical_contract_id=physical_contract_id,
            split_id=split_id,
            method_id=method_id,
            case_id=case_id,
            seed=args.seed,
            planned_budget={"optimizer_steps": 1},
            actual_budget={"optimizer_steps": 1},
            checkpoint={"id": "step-0001", "selection": "single-step-smoke"},
            evaluator_id=evaluator_id,
            artifacts=artifacts,
            failure_class=None,
            replay_of=None,
            supersedes=None,
        )
        ledger.record(manifest)
        return 0
    except Exception as exc:
        failure_manifest = RunManifest(
            run_id=args.run_id,
            experiment_group_id="g1-pipeline-smoke-v1",
            tier="smoke",
            scientific_role="pipeline",
            gate="G1",
            started_at=started_at,
            ended_at=_utc_now(),
            command=list(sys.argv),
            execution_status="FAILED",
            numerical_validity="NOT_EVALUATED",
            gate_outcome="ENGINEERING_BLOCKED",
            route_disposition="BLOCKED",
            evidence_identity="ENGINEERING_CONTROL_FLOW_ONLY",
            claim_status="NO_NUMERICAL_EVIDENCE",
            code_identity=_code_identity(),
            environment={
                "python": platform.python_version(),
                "torch": torch.__version__,
                "numpy": np.__version__,
                "h5py": h5py.__version__,
                "platform": platform.platform(),
                "runtime": "cpu",
            },
            physical_contract_id=physical_contract_id,
            split_id=split_id,
            method_id=method_id,
            case_id=case_id,
            seed=args.seed,
            planned_budget={"optimizer_steps": 1},
            actual_budget={"optimizer_steps": 0},
            checkpoint={"id": None, "selection": "single-step-smoke"},
            evaluator_id=evaluator_id,
            artifacts=artifacts,
            failure_class=type(exc).__name__,
            replay_of=None,
            supersedes=None,
        )
        ledger.record(failure_manifest)
        print(f"G1 pipeline smoke failed: {exc}", file=sys.stderr)
        return 1


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
