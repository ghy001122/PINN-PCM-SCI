from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .artifacts import ArtifactContractError, CaseArtifact, PredictionArtifact


class ArtifactValidationError(ValueError):
    """A prediction cannot be scored against the frozen artifact contract."""


def _load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        raise ArtifactValidationError(f"JSON contract is not an object: {path}")
    return loaded


def _validate_split_manifest(split: dict[str, Any]) -> None:
    if split.get("schema_version") != "split-manifest-v1":
        raise ArtifactValidationError("unsupported split manifest schema")
    split_id = split.get("split_id")
    if not isinstance(split_id, str) or not split_id:
        raise ArtifactValidationError("split manifest requires a non-empty split_id")
    cases = split.get("cases")
    if not isinstance(cases, dict) or not cases:
        raise ArtifactValidationError("split manifest requires a non-empty cases map")
    if any(not isinstance(case_id, str) or not case_id for case_id in cases):
        raise ArtifactValidationError("split manifest contains an invalid case_id")


def _validate_metric_spec(spec: dict[str, Any]) -> None:
    if spec.get("schema_version") != "metric-spec-v1":
        raise ArtifactValidationError("unsupported metric spec schema")
    for key in ("evaluator_id", "structure_field", "device_channel"):
        if not isinstance(spec.get(key), str) or not spec[key]:
            raise ArtifactValidationError(f"metric spec requires non-empty {key}")
    try:
        threshold = float(spec["structure_threshold"])
        device_scale = float(spec["device_scale"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ArtifactValidationError("metric spec contains a non-numeric scalar") from exc
    if not np.isfinite(threshold):
        raise ArtifactValidationError("structure_threshold must be finite")
    if not np.isfinite(device_scale) or device_scale <= 0.0:
        raise ArtifactValidationError("device_scale must be finite and strictly positive")
    windows = spec.get("cycle_windows")
    if not isinstance(windows, list) or not windows:
        raise ArtifactValidationError("cycle_windows must be a non-empty list")
    previous_end = -np.inf
    for index, window in enumerate(windows):
        if not isinstance(window, list) or len(window) != 2:
            raise ArtifactValidationError(f"cycle window {index} must contain two bounds")
        try:
            start, end = float(window[0]), float(window[1])
        except (TypeError, ValueError) as exc:
            raise ArtifactValidationError(f"cycle window {index} is not numeric") from exc
        if not np.isfinite(start) or not np.isfinite(end) or start > end:
            raise ArtifactValidationError(f"cycle window {index} has invalid bounds")
        if start < previous_end:
            raise ArtifactValidationError("cycle windows overlap or are not ordered")
        previous_end = end


def _cycle_equal_symmetric_difference(
    reference: np.ndarray,
    prediction: np.ndarray,
    time: np.ndarray,
    threshold: float,
    cycle_windows: list[list[float]],
) -> float:
    values: list[float] = []
    for index, (start, end) in enumerate(cycle_windows):
        if index == len(cycle_windows) - 1:
            selected = (time >= start) & (time <= end)
        else:
            selected = (time >= start) & (time < end)
        if not np.any(selected):
            raise ArtifactValidationError(
                f"cycle window {index} contains no oracle time samples"
            )
        values.append(
            float(
                np.mean(
                    np.logical_xor(
                        reference[selected] >= threshold,
                        prediction[selected] >= threshold,
                    )
                )
            )
        )
    return float(np.mean(values))


def evaluate_files(
    *,
    prediction_path: str | Path,
    oracle_path: str | Path,
    split_manifest_path: str | Path,
    metric_spec_path: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    """Evaluate one prediction using disk artifacts only."""

    try:
        oracle = CaseArtifact.read(oracle_path)
        prediction = PredictionArtifact.read(prediction_path)
    except ArtifactContractError as exc:
        raise ArtifactValidationError(f"invalid artifact contract: {exc}") from exc
    split = _load_json(split_manifest_path)
    spec = _load_json(metric_spec_path)
    _validate_split_manifest(split)
    _validate_metric_spec(spec)

    if prediction.case_id != oracle.case_id:
        raise ArtifactValidationError(
            f"case_id mismatch: prediction={prediction.case_id!r}, oracle={oracle.case_id!r}"
        )
    if prediction.physical_contract_id != oracle.physical_contract_id:
        raise ArtifactValidationError(
            "physical_contract_id mismatch: "
            f"prediction={prediction.physical_contract_id!r}, "
            f"oracle={oracle.physical_contract_id!r}"
        )
    if prediction.mesh_identity != oracle.mesh_identity:
        raise ArtifactValidationError(
            "prediction and oracle mesh identity differ: "
            f"prediction={prediction.mesh_identity!r}, oracle={oracle.mesh_identity!r}"
        )
    if prediction.field_time.shape != oracle.field_time.shape or not np.array_equal(
        prediction.field_time, oracle.field_time
    ):
        raise ArtifactValidationError("prediction and oracle field time grids differ")
    if prediction.circuit_time.shape != oracle.circuit_time.shape or not np.array_equal(
        prediction.circuit_time, oracle.circuit_time
    ):
        raise ArtifactValidationError("prediction and oracle circuit time grids differ")
    if prediction.time_unit != oracle.time_unit:
        raise ArtifactValidationError(
            "prediction and oracle time unit mismatch: "
            f"prediction={prediction.time_unit!r}, oracle={oracle.time_unit!r}"
        )
    split_cases = split.get("cases")
    if not isinstance(split_cases, dict) or oracle.case_id not in split_cases:
        raise ArtifactValidationError(
            f"case_id {oracle.case_id!r} is absent from frozen split"
        )

    structure_field = str(spec["structure_field"])
    device_channel = str(spec["device_channel"])
    if structure_field not in oracle.fields or structure_field not in prediction.fields:
        raise ArtifactValidationError(
            f"missing field {structure_field!r} in oracle or prediction"
        )
    if device_channel not in oracle.circuit or device_channel not in prediction.circuit:
        raise ArtifactValidationError(
            f"missing circuit channel {device_channel!r} in oracle or prediction"
        )
    if prediction.field_units.get(structure_field) != oracle.field_units.get(
        structure_field
    ):
        raise ArtifactValidationError(
            f"unit mismatch for field {structure_field!r}: "
            f"prediction={prediction.field_units.get(structure_field)!r}, "
            f"oracle={oracle.field_units.get(structure_field)!r}"
        )
    if prediction.circuit_units.get(device_channel) != oracle.circuit_units.get(
        device_channel
    ):
        raise ArtifactValidationError(
            f"unit mismatch for circuit channel {device_channel!r}"
        )
    expected_field_shape = (oracle.field_time.size, oracle.nodes.shape[0])
    if oracle.fields[structure_field].shape != expected_field_shape:
        raise ArtifactValidationError(
            f"oracle field {structure_field!r} shape does not match field time and mesh"
        )
    if prediction.fields[structure_field].shape != oracle.fields[structure_field].shape:
        raise ArtifactValidationError(
            f"prediction field {structure_field!r} shape differs from oracle"
        )
    expected_circuit_shape = (oracle.circuit_time.size,)
    if oracle.circuit[device_channel].shape != expected_circuit_shape:
        raise ArtifactValidationError(
            f"oracle circuit channel {device_channel!r} shape does not match circuit time"
        )
    if prediction.circuit[device_channel].shape != oracle.circuit[device_channel].shape:
        raise ArtifactValidationError(
            f"prediction circuit channel {device_channel!r} shape differs from oracle"
        )
    arrays_to_check = {
        "oracle field time": oracle.field_time,
        "prediction field time": prediction.field_time,
        "oracle circuit time": oracle.circuit_time,
        "prediction circuit time": prediction.circuit_time,
        f"oracle field {structure_field}": oracle.fields[structure_field],
        f"prediction field {structure_field}": prediction.fields[structure_field],
        f"oracle circuit {device_channel}": oracle.circuit[device_channel],
        f"prediction circuit {device_channel}": prediction.circuit[device_channel],
    }
    for label, values in arrays_to_check.items():
        if not np.all(np.isfinite(values)):
            raise ArtifactValidationError(f"non-finite values in {label}")
    structure_error = _cycle_equal_symmetric_difference(
        oracle.fields[structure_field],
        prediction.fields[structure_field],
        oracle.field_time,
        float(spec["structure_threshold"]),
        spec["cycle_windows"],
    )
    device_difference = (
        prediction.circuit[device_channel] - oracle.circuit[device_channel]
    )
    device_error = float(
        np.sqrt(np.mean(np.square(device_difference))) / float(spec["device_scale"])
    )

    metrics: dict[str, Any] = {
        "schema_version": "metrics-v1",
        "evaluator_id": str(spec["evaluator_id"]),
        "case_id": oracle.case_id,
        "split_id": str(split["split_id"]),
        "method_id": prediction.method_id,
        "checkpoint_id": prediction.checkpoint_id,
        "structure_symmetric_difference_cycle_equal": structure_error,
        "device_trajectory_nrmse": device_error,
    }
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metrics
