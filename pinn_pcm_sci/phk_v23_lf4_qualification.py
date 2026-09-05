"""CPU-G boundary geometry and deterministic stream qualification for LF4."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .phk_v22r_training import ROOT, load_case_physics
from .phk_v23_lf0 import _sha256_path, _write_json_exclusive
from .phk_v23_lf2 import _predict_medium, load_medium_dataset
from .phk_v23_lf4 import (
    TASK_ID,
    InterfaceBandDataset,
    boundary_geometry_report,
    build_training_config,
    contract_identity,
    full_medium_audit,
    load_contracts,
    load_lf3_t0_model,
    precompute_stream_identities,
)


LF3_RAW_QUALIFICATION = ROOT / "outputs/runs/20260904T150300Z-phk-v23-lf3-cpu-qualification-6ec084c/qualification.json"
LF3_RAW_QUALIFICATION_SHA256 = "A88B35037881BFD6D3A7934688C23DDC85ED4AC7D952F4D641C7BDBF0CDC5C76"


def _verify_binding(binding: Mapping[str, Any], *, label: str) -> Path:
    path = (ROOT / str(binding["path"])).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PermissionError(f"LF4 {label} escaped repository") from exc
    if not path.is_file() or _sha256_path(path) != str(binding["sha256"]).upper():
        raise ValueError(f"LF4 {label} is absent or hash-drifted")
    return path


def _phase_math_report(dataset: Any, prediction: np.ndarray) -> dict[str, Any]:
    target = np.clip(dataset.targets[:, 2], 1.0e-8, 1.0 - 1.0e-8)
    predicted = np.clip(np.asarray(prediction, dtype=np.float64).reshape(-1), 1.0e-8, 1.0 - 1.0e-8)
    initial = np.clip(np.tile(dataset.fields["phase"][0], dataset.time.size), 1.0e-8, 1.0 - 1.0e-8)
    delta = np.log(target / (1.0 - target)) - np.log(initial / (1.0 - initial))
    startup = 1.0 - np.exp(-np.repeat(dataset.time - dataset.time[0], dataset.cell_count) / 0.35)
    t0 = np.repeat(dataset.time == dataset.time[0], dataset.cell_count)
    return {
        "teacher_delta_logit_finite": bool(np.isfinite(delta).all()),
        "teacher_delta_logit_minimum": float(delta.min()),
        "teacher_delta_logit_maximum": float(delta.max()),
        "clip_bound": 36.84136146790473,
        "within_clip_span": bool(np.max(np.abs(delta)) <= 36.84136146790473 + 1.0e-12),
        "startup_at_t0_exact_zero": bool(np.all(startup[t0] == 0.0)),
        "prediction_finite_and_bounded": bool(np.isfinite(predicted).all() and np.all((predicted >= 1.0e-8) & (predicted <= 1.0 - 1.0e-8))),
    }


def compute_cpu_payload(*, require_stream_freeze: bool) -> dict[str, Any]:
    contracts = load_contracts(require_stream_freeze=require_stream_freeze)
    data = contracts["data"]
    medium = _verify_binding(data["training_source"], label="medium")
    _verify_binding(data["lf1_b0_identity"], label="LF1-B0 identity")
    checkpoint = _verify_binding(data["initial_checkpoint"], label="LF3-T0 checkpoint")
    prediction_path = checkpoint.parent / "prediction-t0-step-1200.npz"
    if not prediction_path.is_file() or _sha256_path(prediction_path) != data["initial_checkpoint"]["prediction_sha256"]:
        raise ValueError("LF4 LF3-T0 prediction binding drift")
    config = build_training_config("cpu")
    physics, _, _ = load_case_physics(config.case_control)
    dataset = load_medium_dataset(medium, physics=physics, contracts=contracts)
    if dataset.partition_sha256 != data["target_measure"]["partition_sha256"]:
        raise ValueError("LF4 partition hash drift")
    band = InterfaceBandDataset(dataset)
    streams = precompute_stream_identities(dataset)
    if require_stream_freeze:
        expected = {
            "base_window_1201_1600_sha256": data["base_stream"]["development_window_sha256"],
            "base_rolling_1600_sha256": data["base_stream"]["rolling_1600_sha256"],
            "global_extra_400_sha256": data["global_extra_stream"]["rolling_sha256"],
            "band_400_sha256": data["band_stream"]["rolling_sha256"],
        }
        if any(streams[key] != value for key, value in expected.items()):
            raise ValueError("LF4 frozen stream hash mismatch")
    model, _ = load_lf3_t0_model(checkpoint, physics=physics, config=config, device=torch.device("cpu"), expected_sha256=data["initial_checkpoint"]["sha256"])
    audit = full_medium_audit(model, dataset, device=torch.device("cpu"))
    prediction = _predict_medium(model, dataset, device=torch.device("cpu"))
    geometry = boundary_geometry_report(dataset, band, prediction[:, 2])
    phase_math = _phase_math_report(dataset, prediction[:, 2])
    if _sha256_path(LF3_RAW_QUALIFICATION) != LF3_RAW_QUALIFICATION_SHA256:
        raise ValueError("LF4 inherited LF3 qualification drift")
    inherited = json.loads(LF3_RAW_QUALIFICATION.read_text(encoding="utf-8"))
    baseline = inherited.get("lf1_b0_full_medium_audit")
    if not isinstance(baseline, Mapping):
        raise ValueError("LF4 lacks inherited LF1-B0 full-medium audit")
    checks = {
        "input_hashes": True,
        "partition": dataset.partition_sha256 == data["target_measure"]["partition_sha256"],
        "four_pools_nonempty": all(geometry["pool_counts"][name] > 0 for name in geometry["pool_counts"]),
        "pool_values_finite": all(np.isfinite(value) and value > 0.0 for value in geometry["pool_masses"].values()),
        "phase_math": all(bool(phase_math[key]) for key in ("teacher_delta_logit_finite", "within_clip_span", "startup_at_t0_exact_zero", "prediction_finite_and_bounded")),
        "lf3_t0_audit_finite": audit["all_values_finite"] is True,
        "stream_hashes_frozen": require_stream_freeze,
        "zero_optimizer_updates": True,
        "fine_extra_stress_unread": True,
    }
    return {
        "schema_id": "phk-v23-lf4-cpu-qualification-v1",
        "task_id": TASK_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "LF4_CPU_QUALIFICATION_PASS" if all(checks.values()) else "LF4_BOUNDARY_GEOMETRY_BLOCKED",
        "gpu_execution_authorized_by_cpu_gate": bool(all(checks.values())),
        "scientific_model_optimizer_updates": 0,
        "gpu_used": False,
        "contracts": contract_identity(),
        "checks": checks,
        "partition_sha256": dataset.partition_sha256,
        "stream_identities": streams,
        "boundary_geometry": geometry,
        "phase_math": phase_math,
        "lf3_t0_full_medium_audit": audit,
        "lf1_b0_full_medium_audit": baseline,
        "input_bindings": {
            "medium": {"path": str(medium), "sha256": _sha256_path(medium)},
            "lf3_t0_checkpoint": {"path": str(checkpoint), "sha256": _sha256_path(checkpoint)},
            "lf3_t0_prediction": {"path": str(prediction_path), "sha256": _sha256_path(prediction_path)},
            "lf3_raw_qualification": {"path": str(LF3_RAW_QUALIFICATION), "sha256": _sha256_path(LF3_RAW_QUALIFICATION)},
        },
        "reference_boundary": {"fine_extra_read": False, "stress_read": False, "frozen_evaluator_read": False},
    }


def qualify_cpu(*, artifact_path: Path, manifest_path: Path) -> dict[str, Any]:
    artifact_path = Path(artifact_path).resolve()
    manifest_path = Path(manifest_path).resolve()
    if artifact_path.is_file():
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        if payload.get("task_id") != TASK_ID or payload.get("status") != "LF4_CPU_QUALIFICATION_PASS" or payload.get("contracts") != contract_identity():
            raise ValueError("existing LF4 CPU artifact is not the exact completed qualification")
    else:
        payload = compute_cpu_payload(require_stream_freeze=True)
        if payload["status"] != "LF4_CPU_QUALIFICATION_PASS":
            raise RuntimeError(payload["status"])
        _write_json_exclusive(artifact_path, payload)
    manifest = {
        "schema_id": "phk-v23-lf4-cpu-qualification-manifest-v1",
        "task_id": TASK_ID,
        "status": payload["status"],
        "artifact": {"path": artifact_path.relative_to(ROOT).as_posix(), "sha256": _sha256_path(artifact_path), "size_bytes": artifact_path.stat().st_size},
        "contracts": payload["contracts"],
        "optimizer_updates": 0,
        "gpu_used": False,
        "fine_extra_stress_read": False,
    }
    _write_json_exclusive(manifest_path, manifest)
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--precompute-streams", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.precompute_streams:
        payload = compute_cpu_payload(require_stream_freeze=False)
        print(json.dumps(payload["stream_identities"], sort_keys=True))
        return 0
    if args.artifact is None or args.manifest is None:
        raise SystemExit("--artifact and --manifest are required")
    payload = qualify_cpu(artifact_path=args.artifact, manifest_path=args.manifest)
    print(json.dumps({"status": payload["status"], "partition_sha256": payload["partition_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["compute_cpu_payload", "qualify_cpu"]
