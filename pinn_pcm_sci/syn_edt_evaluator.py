"""Frozen evaluator seam for the synthetic electrothermal-defect benchmark.

The generic project artifacts are nodal and intentionally remain unchanged.
This module owns the cell-centred SYN-EDT disk contract, exact axisymmetric
geometry, event extraction, six-component endpoint, hard guards, and sealed
oracle floors.  The public helpers are pure array computations so the oracle
can reuse them without depending on evaluator file I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]

ARTIFACT_SCHEMA = "syn-edt-eval-artifact-v1"
ATTEMPT_SCHEMA = "syn-edt-attempt-v1"
FLOOR_SCHEMA = "syn-edt-floor-seal-v1"
METRICS_SCHEMA = "syn-edt-metrics-v1"
COMPONENT_ORDER = (
    "roi_concentration_field_error",
    "defect_flux_error",
    "event_time_error",
    "depletion_gap_thickness_error",
    "recovery_error",
    "port_current_trace_error",
)
FAILURE_ATTEMPT_STATUSES = frozenset({"NAN", "OOM", "TIMEOUT", "DIVERGENCE"})


class SynEdtEvaluatorError(ValueError):
    """A frozen SYN-EDT artifact or evaluator contract is invalid."""


class NonestimableComponentError(SynEdtEvaluatorError):
    """A required event or endpoint component cannot be estimated."""


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _sha256_file(path: str | Path) -> str:
    return _sha256_bytes(Path(path).read_bytes())


def _read_object(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise SynEdtEvaluatorError(f"JSON root must be an object: {path}")
    return value


def _write_object(path: str | Path, value: Mapping[str, Any], *, overwrite: bool) -> None:
    destination = Path(path)
    if destination.exists() and not overwrite:
        raise SynEdtEvaluatorError(f"write-once artifact already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _require_finite(name: str, value: NDArray[Any], *, ndim: int | None = None) -> None:
    if not isinstance(value, np.ndarray) or value.dtype != np.dtype(np.float64):
        raise SynEdtEvaluatorError(f"{name} must be a float64 array")
    if ndim is not None and value.ndim != ndim:
        raise SynEdtEvaluatorError(f"{name} must have {ndim} dimensions")
    if not np.all(np.isfinite(value)):
        raise SynEdtEvaluatorError(f"{name} contains non-finite values")


def _require_time(name: str, value: FloatArray) -> None:
    _require_finite(name, value, ndim=1)
    if value.size < 2 or np.any(np.diff(value) <= 0.0):
        raise SynEdtEvaluatorError(f"{name} must be strictly increasing")


def axisymmetric_cell_volumes(cell_bounds_m: FloatArray) -> FloatArray:
    """Return exact cell volumes with the common ``2*pi`` factor omitted."""

    _require_finite("cell_bounds_m", cell_bounds_m, ndim=2)
    if cell_bounds_m.shape[1] != 4 or cell_bounds_m.shape[0] == 0:
        raise SynEdtEvaluatorError("cell_bounds_m must have shape (N, 4)")
    r0, r1, z0, z1 = cell_bounds_m.T
    if np.any(r0 < 0.0) or np.any(r1 <= r0) or np.any(z1 <= z0):
        raise SynEdtEvaluatorError("cell bounds must have positive extent and r >= 0")
    return np.asarray(0.5 * (r1 * r1 - r0 * r0) * (z1 - z0), dtype=np.float64)


def _face_key(axis: str, coordinate: float, low: float, high: float) -> tuple[str, str, str, str]:
    return axis, float(coordinate).hex(), float(low).hex(), float(high).hex()


@dataclass(frozen=True)
class FaceTopology:
    internal_face_cells: IntArray
    boundary_cells: IntArray
    boundary_normals_rz: FloatArray
    boundary_areas_no_2pi_m2: FloatArray


def build_face_topology(cell_bounds_m: FloatArray) -> FaceTopology:
    """Build deterministic full-face connectivity for conforming rectangles."""

    axisymmetric_cell_volumes(cell_bounds_m)
    pending: dict[tuple[str, str, str, str], tuple[int, tuple[float, float], float]] = {}
    internal: list[tuple[int, int]] = []
    for index, (r0, r1, z0, z1) in enumerate(cell_bounds_m):
        faces = (
            (_face_key("r", r0, z0, z1), (-1.0, 0.0), r0 * (z1 - z0)),
            (_face_key("r", r1, z0, z1), (1.0, 0.0), r1 * (z1 - z0)),
            (_face_key("z", z0, r0, r1), (0.0, -1.0), 0.5 * (r1 * r1 - r0 * r0)),
            (_face_key("z", z1, r0, r1), (0.0, 1.0), 0.5 * (r1 * r1 - r0 * r0)),
        )
        for key, normal, area in faces:
            previous = pending.pop(key, None)
            if previous is None:
                pending[key] = (index, normal, area)
                continue
            other, other_normal, other_area = previous
            if not np.allclose(np.asarray(normal) + np.asarray(other_normal), 0.0, atol=0.0):
                raise SynEdtEvaluatorError("matched faces do not have opposite normals")
            if not math.isclose(area, other_area, rel_tol=0.0, abs_tol=0.0):
                raise SynEdtEvaluatorError("matched faces have different exact areas")
            internal.append((min(index, other), max(index, other)))
    internal.sort()
    boundary_rows = sorted(
        pending.values(),
        key=lambda item: (item[0], item[1][0], item[1][1], item[2]),
    )
    return FaceTopology(
        internal_face_cells=np.asarray(internal, dtype=np.int64).reshape((-1, 2)),
        boundary_cells=np.asarray([row[0] for row in boundary_rows], dtype=np.int64),
        boundary_normals_rz=np.asarray([row[1] for row in boundary_rows], dtype=np.float64).reshape((-1, 2)),
        boundary_areas_no_2pi_m2=np.asarray([row[2] for row in boundary_rows], dtype=np.float64),
    )


def conservative_project_cells(
    source_values: FloatArray,
    source_bounds_m: FloatArray,
    target_bounds_m: FloatArray,
) -> FloatArray:
    """Conservatively project cell averages using exact axisymmetric overlaps."""

    _require_finite("source_values", source_values)
    source_volumes = axisymmetric_cell_volumes(source_bounds_m)
    target_volumes = axisymmetric_cell_volumes(target_bounds_m)
    if source_values.shape[-1] != source_bounds_m.shape[0]:
        raise SynEdtEvaluatorError("source value width differs from source cell count")
    flat = source_values.reshape((-1, source_values.shape[-1]))
    output = np.zeros((flat.shape[0], target_bounds_m.shape[0]), dtype=np.float64)
    sr0, sr1, sz0, sz1 = source_bounds_m.T
    for target_index, (tr0, tr1, tz0, tz1) in enumerate(target_bounds_m):
        radial0 = np.maximum(sr0, tr0)
        radial1 = np.minimum(sr1, tr1)
        axial0 = np.maximum(sz0, tz0)
        axial1 = np.minimum(sz1, tz1)
        overlap = 0.5 * np.maximum(radial1 * radial1 - radial0 * radial0, 0.0) * np.maximum(axial1 - axial0, 0.0)
        total = float(np.sum(overlap))
        if not math.isclose(total, float(target_volumes[target_index]), rel_tol=1.0e-10, abs_tol=1.0e-30):
            raise SynEdtEvaluatorError("source mesh does not exactly cover a target cell")
        output[:, target_index] = (flat @ overlap) / target_volumes[target_index]
    # Exercise the source volume calculation as a coverage/shape validation.
    if np.any(source_volumes <= 0.0):
        raise SynEdtEvaluatorError("source mesh has non-positive volume")
    return output.reshape(source_values.shape[:-1] + (target_bounds_m.shape[0],))


def interpolate_time(time: FloatArray, values: FloatArray, target: FloatArray) -> FloatArray:
    """Linearly interpolate a leading time dimension without extrapolation."""

    _require_time("time", time)
    _require_time("target", target)
    _require_finite("values", values)
    if values.shape[0] != time.size:
        raise SynEdtEvaluatorError("value time dimension differs from its time axis")
    if target[0] < time[0] - 1.0e-14 or target[-1] > time[-1] + 1.0e-14:
        raise SynEdtEvaluatorError("time interpolation would extrapolate")
    flat = values.reshape((time.size, -1))
    out = np.empty((target.size, flat.shape[1]), dtype=np.float64)
    for column in range(flat.shape[1]):
        out[:, column] = np.interp(target, time, flat[:, column])
    return out.reshape((target.size,) + values.shape[1:])


def _window(time: FloatArray, values: FloatArray, start: float, end: float) -> tuple[FloatArray, FloatArray]:
    if not start < end or start < time[0] - 1.0e-14 or end > time[-1] + 1.0e-14:
        raise SynEdtEvaluatorError("invalid integration window")
    interior = time[(time > start) & (time < end)]
    target = np.concatenate((np.asarray([start]), interior, np.asarray([end]))).astype(np.float64)
    return target, interpolate_time(time, values, target)


def _space_time_rms(
    time: FloatArray,
    values: FloatArray,
    volumes: FloatArray,
    start: float,
    end: float,
) -> float:
    selected_time, selected = _window(time, values, start, end)
    if selected.shape[-1] != volumes.size:
        raise SynEdtEvaluatorError("spatial values and volume weights differ")
    squared = np.square(selected)
    if squared.ndim == 3:  # vector component axis before cell axis
        squared = np.sum(squared, axis=1)
    space_mean = np.sum(squared * volumes, axis=-1) / np.sum(volumes)
    return float(np.sqrt(np.trapezoid(space_mean, selected_time) / (end - start)))


def _time_rms(time: FloatArray, values: FloatArray, start: float, end: float) -> float:
    selected_time, selected = _window(time, values, start, end)
    return float(np.sqrt(np.trapezoid(np.square(selected), selected_time) / (end - start)))


def _mask_for_bounds(cell_bounds_m: FloatArray, bounds_nm: Sequence[Sequence[float]]) -> NDArray[np.bool_]:
    (r0_nm, r1_nm), (z0_nm, z1_nm) = bounds_nm
    scale = 1.0e-9
    tolerance = 1.0e-18
    return (
        (cell_bounds_m[:, 0] >= r0_nm * scale - tolerance)
        & (cell_bounds_m[:, 1] <= r1_nm * scale + tolerance)
        & (cell_bounds_m[:, 2] >= z0_nm * scale - tolerance)
        & (cell_bounds_m[:, 3] <= z1_nm * scale + tolerance)
    )


def _sample_at(time: FloatArray, values: FloatArray, sample: float) -> FloatArray:
    _require_time("time", time)
    _require_finite("values", values)
    if values.shape[0] != time.size:
        raise SynEdtEvaluatorError("value time dimension differs from its time axis")
    if sample < time[0] - 1.0e-14 or sample > time[-1] + 1.0e-14:
        raise SynEdtEvaluatorError("time interpolation would extrapolate")
    flat = values.reshape((time.size, -1))
    output = np.empty(flat.shape[1], dtype=np.float64)
    for column in range(flat.shape[1]):
        output[column] = np.interp(sample, time, flat[:, column])
    return output.reshape(values.shape[1:])


@dataclass(frozen=True)
class CycleEvent:
    peak_roi_depletion: float
    event_time_s: float
    recovery_fraction: float
    adjacent_annulus_relative_depletion: float
    depleted_thickness_fraction: float
    partial_coverage_fraction: float


def extract_cycle_event(
    *,
    field_time_s: FloatArray,
    y: FloatArray,
    cell_bounds_m: FloatArray,
    topology: FaceTopology,
    cycle_index: int,
    roi_mask: NDArray[np.bool_],
    annulus_mask: NDArray[np.bool_],
    volumes: FloatArray,
    search_end_relative_s: float = 0.46,
    crossing: float = 0.12,
) -> CycleEvent:
    """Extract the frozen first-crossing and top-connected event for one cycle."""

    start = float(cycle_index)
    end = start + 1.0
    if not np.any(roi_mask) or not np.any(annulus_mask):
        raise NonestimableComponentError("ROI or adjacent annulus contains no cells")
    pre = _sample_at(field_time_s, y, start)
    depletion = (pre[None, :] - y) / 0.5
    roi_mean = np.sum(depletion[:, roi_mask] * volumes[roi_mask], axis=1) / np.sum(volumes[roi_mask])
    search = (field_time_s >= start - 1.0e-14) & (field_time_s <= start + search_end_relative_s + 1.0e-14)
    indices = np.flatnonzero(search)
    if indices.size < 2:
        raise NonestimableComponentError("cycle peak search has fewer than two samples")
    peak_local = int(np.argmax(roi_mean[indices]))
    peak_index = int(indices[peak_local])
    peak = float(roi_mean[peak_index])
    event_time: float | None = None
    for left, right in zip(indices[:-1], indices[1:]):
        y0 = float(roi_mean[left])
        y1 = float(roi_mean[right])
        if y0 < crossing <= y1 and y1 > y0:
            fraction = (crossing - y0) / (y1 - y0)
            event_time = float(field_time_s[left] + fraction * (field_time_s[right] - field_time_s[left]))
            break
    if event_time is None or peak <= 0.0:
        raise NonestimableComponentError("cycle has no upward D=0.12 crossing")
    annulus_mean = float(
        np.sum(depletion[peak_index, annulus_mask] * volumes[annulus_mask])
        / np.sum(volumes[annulus_mask])
    )
    eligible = depletion[peak_index] >= 0.5 * peak
    top = np.isclose(cell_bounds_m[:, 3], 30.0e-9, rtol=0.0, atol=1.0e-18)
    connected = np.zeros(y.shape[1], dtype=bool)
    stack = list(np.flatnonzero(eligible & top))
    adjacency: list[list[int]] = [[] for _ in range(y.shape[1])]
    for left, right in topology.internal_face_cells:
        adjacency[int(left)].append(int(right))
        adjacency[int(right)].append(int(left))
    while stack:
        cell = stack.pop()
        if connected[cell] or not eligible[cell]:
            continue
        connected[cell] = True
        stack.extend(adjacency[cell])
    if not np.any(connected):
        raise NonestimableComponentError("no depleted component is connected to z=30 nm")
    thickness = float((30.0e-9 - np.min(cell_bounds_m[connected, 2])) / 30.0e-9)
    coverage = float(np.sum(volumes[connected]) / np.sum(volumes))
    end_state = _sample_at(field_time_s, y, end)
    end_depletion = float(
        np.sum(((pre - end_state) / 0.5)[roi_mask] * volumes[roi_mask])
        / np.sum(volumes[roi_mask])
    )
    return CycleEvent(
        peak_roi_depletion=peak,
        event_time_s=event_time,
        recovery_fraction=float((peak - end_depletion) / peak),
        adjacent_annulus_relative_depletion=float(annulus_mean / peak),
        depleted_thickness_fraction=thickness,
        partial_coverage_fraction=coverage,
    )


def _mesh_identity(bounds: FloatArray, topology: FaceTopology) -> str:
    digest = hashlib.sha256(b"syn-edt-cell-mesh-v1\0")
    for value in (
        bounds,
        topology.internal_face_cells,
        topology.boundary_cells,
        topology.boundary_normals_rz,
        topology.boundary_areas_no_2pi_m2,
    ):
        contiguous = np.ascontiguousarray(value)
        digest.update(str(contiguous.dtype).encode("ascii"))
        digest.update(np.asarray(contiguous.shape, dtype=np.int64).tobytes())
        digest.update(contiguous.tobytes())
    return f"sha256:{digest.hexdigest()}"


@dataclass(frozen=True)
class SynEdtEvaluationArtifact:
    role: str
    case_id: str
    physical_contract_id: str
    s0_sha256: str
    numerical_contract_sha256: str
    evidence_identity: str
    method_id: str
    checkpoint_id: str
    cell_bounds_m: FloatArray
    field_time_s: FloatArray
    circuit_time_s: FloatArray
    y: FloatArray
    defect_flux_r_m2_s: FloatArray
    defect_flux_z_m2_s: FloatArray
    temperature_k: FloatArray
    boundary_normal_flux_m2_s: FloatArray
    voltage_v: FloatArray
    current_top_a: FloatArray
    current_bottom_a: FloatArray
    joule_power_w: FloatArray
    joule_power_dimensionless: FloatArray
    heat_sink_power_w: FloatArray
    non_scientific_fixture: bool = False

    def validate(self) -> None:
        if self.role not in {"ORACLE", "PREDICTION"}:
            raise SynEdtEvaluatorError("artifact role must be ORACLE or PREDICTION")
        for name in (
            "case_id", "physical_contract_id", "s0_sha256",
            "numerical_contract_sha256", "evidence_identity", "method_id", "checkpoint_id",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise SynEdtEvaluatorError(f"{name} must be non-empty")
        volumes = axisymmetric_cell_volumes(self.cell_bounds_m)
        topology = build_face_topology(self.cell_bounds_m)
        _require_time("field_time_s", self.field_time_s)
        _require_time("circuit_time_s", self.circuit_time_s)
        for name in ("y", "defect_flux_r_m2_s", "defect_flux_z_m2_s", "temperature_k"):
            value = getattr(self, name)
            _require_finite(name, value, ndim=2)
            if value.shape != (self.field_time_s.size, volumes.size):
                raise SynEdtEvaluatorError(f"{name} shape differs from field time and cells")
        _require_finite("boundary_normal_flux_m2_s", self.boundary_normal_flux_m2_s, ndim=2)
        if self.boundary_normal_flux_m2_s.shape != (self.field_time_s.size, topology.boundary_cells.size):
            raise SynEdtEvaluatorError("boundary flux shape differs from field time and boundary topology")
        for name in (
            "voltage_v", "current_top_a", "current_bottom_a", "joule_power_w",
            "joule_power_dimensionless", "heat_sink_power_w",
        ):
            value = getattr(self, name)
            _require_finite(name, value, ndim=1)
            if value.shape != self.circuit_time_s.shape:
                raise SynEdtEvaluatorError(f"{name} shape differs from circuit time")

    @property
    def topology(self) -> FaceTopology:
        return build_face_topology(self.cell_bounds_m)

    @property
    def volumes(self) -> FloatArray:
        return axisymmetric_cell_volumes(self.cell_bounds_m)

    @property
    def mesh_identity(self) -> str:
        return _mesh_identity(self.cell_bounds_m, self.topology)

    def write(self, path: str | Path) -> None:
        self.validate()
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        topology = self.topology
        metadata = {
            "schema_version": ARTIFACT_SCHEMA,
            "role": self.role,
            "case_id": self.case_id,
            "physical_contract_id": self.physical_contract_id,
            "s0_sha256": self.s0_sha256,
            "numerical_contract_sha256": self.numerical_contract_sha256,
            "evidence_identity": self.evidence_identity,
            "method_id": self.method_id,
            "checkpoint_id": self.checkpoint_id,
            "mesh_identity": self.mesh_identity,
            "non_scientific_fixture": self.non_scientific_fixture,
        }
        np.savez_compressed(
            destination,
            metadata=np.asarray(json.dumps(metadata, sort_keys=True, allow_nan=False)),
            cell_bounds_m=self.cell_bounds_m,
            cell_volumes_no_2pi_m3=self.volumes,
            internal_face_cells=topology.internal_face_cells,
            boundary_cells=topology.boundary_cells,
            boundary_normals_rz=topology.boundary_normals_rz,
            boundary_areas_no_2pi_m2=topology.boundary_areas_no_2pi_m2,
            field_time_s=self.field_time_s,
            circuit_time_s=self.circuit_time_s,
            y=self.y,
            defect_flux_r_m2_s=self.defect_flux_r_m2_s,
            defect_flux_z_m2_s=self.defect_flux_z_m2_s,
            temperature_k=self.temperature_k,
            boundary_normal_flux_m2_s=self.boundary_normal_flux_m2_s,
            voltage_v=self.voltage_v,
            current_top_a=self.current_top_a,
            current_bottom_a=self.current_bottom_a,
            joule_power_w=self.joule_power_w,
            joule_power_dimensionless=self.joule_power_dimensionless,
            heat_sink_power_w=self.heat_sink_power_w,
        )

    @classmethod
    def read(cls, path: str | Path) -> "SynEdtEvaluationArtifact":
        with np.load(Path(path), allow_pickle=False) as payload:
            metadata = json.loads(str(payload["metadata"].item()))
            if metadata.get("schema_version") != ARTIFACT_SCHEMA:
                raise SynEdtEvaluatorError("unsupported SYN-EDT artifact schema")
            value = cls(
                role=str(metadata["role"]),
                case_id=str(metadata["case_id"]),
                physical_contract_id=str(metadata["physical_contract_id"]),
                s0_sha256=str(metadata["s0_sha256"]),
                numerical_contract_sha256=str(metadata["numerical_contract_sha256"]),
                evidence_identity=str(metadata["evidence_identity"]),
                method_id=str(metadata["method_id"]),
                checkpoint_id=str(metadata["checkpoint_id"]),
                cell_bounds_m=np.asarray(payload["cell_bounds_m"], dtype=np.float64),
                field_time_s=np.asarray(payload["field_time_s"], dtype=np.float64),
                circuit_time_s=np.asarray(payload["circuit_time_s"], dtype=np.float64),
                y=np.asarray(payload["y"], dtype=np.float64),
                defect_flux_r_m2_s=np.asarray(payload["defect_flux_r_m2_s"], dtype=np.float64),
                defect_flux_z_m2_s=np.asarray(payload["defect_flux_z_m2_s"], dtype=np.float64),
                temperature_k=np.asarray(payload["temperature_k"], dtype=np.float64),
                boundary_normal_flux_m2_s=np.asarray(payload["boundary_normal_flux_m2_s"], dtype=np.float64),
                voltage_v=np.asarray(payload["voltage_v"], dtype=np.float64),
                current_top_a=np.asarray(payload["current_top_a"], dtype=np.float64),
                current_bottom_a=np.asarray(payload["current_bottom_a"], dtype=np.float64),
                joule_power_w=np.asarray(payload["joule_power_w"], dtype=np.float64),
                joule_power_dimensionless=np.asarray(payload["joule_power_dimensionless"], dtype=np.float64),
                heat_sink_power_w=np.asarray(payload["heat_sink_power_w"], dtype=np.float64),
                non_scientific_fixture=bool(metadata["non_scientific_fixture"]),
            )
            value.validate()
            topology = value.topology
            checks = {
                "cell_volumes_no_2pi_m3": value.volumes,
                "internal_face_cells": topology.internal_face_cells,
                "boundary_cells": topology.boundary_cells,
                "boundary_normals_rz": topology.boundary_normals_rz,
                "boundary_areas_no_2pi_m2": topology.boundary_areas_no_2pi_m2,
            }
            for name, expected in checks.items():
                if not np.array_equal(payload[name], expected):
                    raise SynEdtEvaluatorError(f"stored {name} differs from exact cell geometry")
            if metadata.get("mesh_identity") != value.mesh_identity:
                raise SynEdtEvaluatorError("stored mesh identity differs from exact geometry")
            return value


def _contract_parts(
    s0_contract_path: str | Path,
    numerical_contract_path: str | Path,
) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    s0 = _read_object(s0_contract_path)
    numerical = _read_object(numerical_contract_path)
    s0_sha = _sha256_file(s0_contract_path)
    numerical_sha = _sha256_file(numerical_contract_path)
    if str(numerical.get("derived_from_s0_sha256", "")).upper() != s0_sha:
        raise SynEdtEvaluatorError("S2 contract does not bind the exact S0 bytes")
    physical = s0.get("synthetic_physical_contract")
    if not isinstance(physical, dict) or numerical.get("physical_contract_id") != physical.get("contract_id"):
        raise SynEdtEvaluatorError("S0/S2 physical contract identity mismatch")
    return physical, numerical, s0_sha, numerical_sha


def _event_masks(artifact: SynEdtEvaluationArtifact, physical: Mapping[str, Any], numerical: Mapping[str, Any]) -> tuple[NDArray[np.bool_], NDArray[np.bool_]]:
    roi = physical["event_contract"]["roi_nm"]
    annulus = numerical["event_evaluator"]["adjacent_annulus_nm"]
    roi_mask = _mask_for_bounds(artifact.cell_bounds_m, (roi["r"], roi["z"]))
    annulus_mask = _mask_for_bounds(
        artifact.cell_bounds_m,
        (annulus["r_open_closed"], annulus["z_closed"]),
    )
    return roi_mask, annulus_mask


def _events(artifact: SynEdtEvaluationArtifact, physical: Mapping[str, Any], numerical: Mapping[str, Any]) -> tuple[CycleEvent, CycleEvent]:
    roi_mask, annulus_mask = _event_masks(artifact, physical, numerical)
    return tuple(
        extract_cycle_event(
            field_time_s=artifact.field_time_s,
            y=artifact.y,
            cell_bounds_m=artifact.cell_bounds_m,
            topology=artifact.topology,
            cycle_index=cycle,
            roi_mask=roi_mask,
            annulus_mask=annulus_mask,
            volumes=artifact.volumes,
        )
        for cycle in (0, 1)
    )  # type: ignore[return-value]


def component_normalizers(artifact: SynEdtEvaluationArtifact, numerical: Mapping[str, Any]) -> list[dict[str, float]]:
    endpoint = numerical["endpoint_and_floor_contract"]
    flux_floor = 0.01 * float(endpoint["characteristic_particle_flux_m_minus_2_s_minus_1"])
    current_floor = 1.0e-6 * float(endpoint["characteristic_current_a"])
    vector = np.stack((artifact.defect_flux_r_m2_s, artifact.defect_flux_z_m2_s), axis=1)
    result: list[dict[str, float]] = []
    for cycle in (0, 1):
        flux = _space_time_rms(
            artifact.field_time_s,
            vector,
            artifact.volumes,
            float(cycle),
            float(cycle + 1),
        )
        current = _time_rms(
            artifact.circuit_time_s,
            artifact.current_top_a,
            float(cycle),
            float(cycle + 1),
        )
        result.append({
            "defect_flux": max(flux, flux_floor),
            "port_current": max(current, current_floor),
        })
    return result


def _aligned_reference(reference: SynEdtEvaluationArtifact, target: SynEdtEvaluationArtifact) -> SynEdtEvaluationArtifact:
    def field(values: FloatArray) -> FloatArray:
        projected = conservative_project_cells(values, reference.cell_bounds_m, target.cell_bounds_m)
        return interpolate_time(reference.field_time_s, projected, target.field_time_s)

    def circuit(values: FloatArray) -> FloatArray:
        return interpolate_time(reference.circuit_time_s, values, target.circuit_time_s)

    return SynEdtEvaluationArtifact(
        role="ORACLE",
        case_id=reference.case_id,
        physical_contract_id=reference.physical_contract_id,
        s0_sha256=reference.s0_sha256,
        numerical_contract_sha256=reference.numerical_contract_sha256,
        evidence_identity=reference.evidence_identity,
        method_id=reference.method_id,
        checkpoint_id=reference.checkpoint_id,
        cell_bounds_m=target.cell_bounds_m,
        field_time_s=target.field_time_s,
        circuit_time_s=target.circuit_time_s,
        y=field(reference.y),
        defect_flux_r_m2_s=field(reference.defect_flux_r_m2_s),
        defect_flux_z_m2_s=field(reference.defect_flux_z_m2_s),
        temperature_k=field(reference.temperature_k),
        boundary_normal_flux_m2_s=np.zeros_like(target.boundary_normal_flux_m2_s),
        voltage_v=circuit(reference.voltage_v),
        current_top_a=circuit(reference.current_top_a),
        current_bottom_a=circuit(reference.current_bottom_a),
        joule_power_w=circuit(reference.joule_power_w),
        joule_power_dimensionless=circuit(reference.joule_power_dimensionless),
        heat_sink_power_w=circuit(reference.heat_sink_power_w),
        non_scientific_fixture=reference.non_scientific_fixture,
    )


def six_component_errors(
    *,
    reference: SynEdtEvaluationArtifact,
    candidate: SynEdtEvaluationArtifact,
    physical: Mapping[str, Any],
    numerical: Mapping[str, Any],
    normalizers: Sequence[Mapping[str, float]],
    align_reference: bool = False,
) -> list[list[float]]:
    """Return the six frozen dimensionless errors for both cycles."""

    if len(normalizers) != 2:
        raise SynEdtEvaluatorError("two cycles of normalizers are required")
    comparable = _aligned_reference(reference, candidate) if align_reference else reference
    if not align_reference:
        if comparable.mesh_identity != candidate.mesh_identity:
            raise SynEdtEvaluatorError("method prediction mesh differs from its oracle")
        if not np.array_equal(comparable.field_time_s, candidate.field_time_s):
            raise SynEdtEvaluatorError("method field time differs from its oracle")
        if not np.array_equal(comparable.circuit_time_s, candidate.circuit_time_s):
            raise SynEdtEvaluatorError("method circuit time differs from its oracle")
    reference_events = _events(comparable, physical, numerical)
    candidate_events = _events(candidate, physical, numerical)
    roi_mask, _ = _event_masks(candidate, physical, numerical)
    volumes = candidate.volumes
    output: list[list[float]] = []
    for cycle in (0, 1):
        start, end = float(cycle), float(cycle + 1)
        y_error = _space_time_rms(
            candidate.field_time_s,
            ((candidate.y - comparable.y) / 0.5)[:, roi_mask],
            volumes[roi_mask],
            start,
            end,
        )
        flux_difference = np.stack(
            (
                candidate.defect_flux_r_m2_s - comparable.defect_flux_r_m2_s,
                candidate.defect_flux_z_m2_s - comparable.defect_flux_z_m2_s,
            ),
            axis=1,
        )
        flux_error = _space_time_rms(
            candidate.field_time_s,
            flux_difference,
            volumes,
            start,
            end,
        ) / float(normalizers[cycle]["defect_flux"])
        current_error = _time_rms(
            candidate.circuit_time_s,
            candidate.current_top_a - comparable.current_top_a,
            start,
            end,
        ) / float(normalizers[cycle]["port_current"])
        output.append([
            y_error,
            flux_error,
            abs(candidate_events[cycle].event_time_s - reference_events[cycle].event_time_s) / 1.0,
            abs(candidate_events[cycle].depleted_thickness_fraction - reference_events[cycle].depleted_thickness_fraction),
            abs(candidate_events[cycle].recovery_fraction - reference_events[cycle].recovery_fraction),
            current_error,
        ])
    return output


def hard_guard_report(
    artifact: SynEdtEvaluationArtifact,
    *,
    physical: Mapping[str, Any],
    numerical: Mapping[str, Any],
    normalizers: Sequence[Mapping[str, float]],
) -> dict[str, Any]:
    failures: list[str] = []
    guards = physical["physical_guards"]
    event_contract = physical["event_contract"]
    volumes = artifact.volumes
    mass = artifact.y @ volumes
    mass_drift = float(np.max(np.abs(mass - mass[0])) / max(abs(float(mass[0])), 1.0e-300))
    if mass_drift > float(guards["relative_mass_drift_max"]):
        failures.append("MASS")
    terminal_magnitude = np.maximum(
        np.abs(artifact.current_top_a), np.abs(artifact.current_bottom_a)
    )
    zero_current = 1.0e-24 * float(
        numerical["endpoint_and_floor_contract"]["characteristic_current_a"]
    )
    mismatch_trace = np.where(
        terminal_magnitude <= zero_current,
        0.0,
        np.abs(artifact.current_top_a + artifact.current_bottom_a)
        / np.maximum(terminal_magnitude, 1.0e-300),
    )
    current_mismatch = float(np.max(mismatch_trace))
    if current_mismatch > float(guards["relative_terminal_current_mismatch_max"]):
        failures.append("CURRENT")
    y_min, y_max = float(np.min(artifact.y)), float(np.max(artifact.y))
    if y_min < float(guards["y_bounds"][0]) or y_max > float(guards["y_bounds"][1]):
        failures.append("STATE_BOUNDS")
    temperature_min, temperature_max = float(np.min(artifact.temperature_k)), float(np.max(artifact.temperature_k))
    if temperature_min < float(guards["temperature_k_bounds"][0]) or temperature_max > float(guards["temperature_k_bounds"][1]):
        failures.append("TEMPERATURE_BOUNDS")
    temperature_scale = float(numerical["nondimensionalization"]["temperature_k"])
    temperature_deviation = np.max(
        np.abs(artifact.temperature_k / temperature_scale - 1.0), axis=1
    )
    temperature_deviation = interpolate_time(
        artifact.field_time_s,
        temperature_deviation,
        artifact.circuit_time_s,
    )
    driven = np.abs(artifact.joule_power_dimensionless) > 1.0e-24
    heat_residual_trace = np.zeros_like(artifact.joule_power_w)
    heat_residual_trace[driven] = (
        np.abs(artifact.joule_power_w[driven] - artifact.heat_sink_power_w[driven])
        / np.maximum(np.abs(artifact.joule_power_w[driven]), 1.0e-300)
    )
    heat_residual_trace[~driven] = np.where(
        temperature_deviation[~driven] <= 1.0e-12,
        0.0,
        math.inf,
    )
    heat_residual = float(np.max(heat_residual_trace))
    if heat_residual > float(guards["relative_heat_balance_residual_max"]):
        failures.append("HEAT")
    flux_scale = max(float(item["defect_flux"]) for item in normalizers)
    no_flux = float(np.max(np.abs(artifact.boundary_normal_flux_m2_s)) / flux_scale)
    no_flux_limit = 2.0 * float(
        numerical["endpoint_and_floor_contract"]["declared_solver_tolerance_each_dimensionless_component"]
    )
    if no_flux > no_flux_limit:
        failures.append("NO_FLUX")
    try:
        events = _events(artifact, physical, numerical)
    except NonestimableComponentError as exc:
        failures.append(f"EVENT_NONESTIMABLE:{exc}")
        events = None
    if events is not None:
        for cycle, event in enumerate(events, start=1):
            if not (float(event_contract["peak_roi_depletion_range"][0]) <= event.peak_roi_depletion <= float(event_contract["peak_roi_depletion_range"][1])):
                failures.append(f"EVENT_AMPLITUDE_C{cycle}")
            if event.adjacent_annulus_relative_depletion > float(event_contract["adjacent_annulus_relative_depletion_max"]):
                failures.append(f"EVENT_LOCALIZATION_C{cycle}")
            if not (float(event_contract["connected_depleted_thickness_fraction_range"][0]) <= event.depleted_thickness_fraction <= float(event_contract["connected_depleted_thickness_fraction_range"][1])):
                failures.append(f"DEPLETED_THICKNESS_C{cycle}")
            coverage_range = numerical["event_evaluator"]["partial_coverage_fraction_range"]
            if not (float(coverage_range[0]) <= event.partial_coverage_fraction <= float(coverage_range[1])):
                failures.append(f"PARTIAL_COVERAGE_C{cycle}")
            if event.recovery_fraction < float(event_contract["recovery_fraction_min"]):
                failures.append(f"RECOVERY_C{cycle}")
        drift = abs(events[0].peak_roi_depletion - events[1].peak_roi_depletion) / max(events[0].peak_roi_depletion, events[1].peak_roi_depletion)
        if drift > float(event_contract["cycle_relative_drift_max"]):
            failures.append("CYCLE_DRIFT")
    else:
        drift = None
    port_failures: list[str] = []
    for cycle in (0, 1):
        hold_start, hold_end = cycle + 0.02, cycle + 0.32
        hold_time, hold_current = _window(artifact.circuit_time_s, artifact.current_top_a, hold_start, hold_end)
        _, hold_voltage = _window(artifact.circuit_time_s, artifact.voltage_v, hold_start, hold_end)
        if np.any(hold_current <= 0.0):
            port_failures.append(f"POSITIVE_HOLD_SIGN_C{cycle + 1}")
        conductance = hold_current / np.maximum(hold_voltage, 1.0e-300)
        relative_drop = float((conductance[0] - conductance[-1]) / max(abs(float(conductance[0])), 1.0e-300))
        if relative_drop < 0.01:
            port_failures.append(f"PORT_RESPONSE_C{cycle + 1}")
    negative = artifact.voltage_v < -1.0e-14
    if np.any(negative & (artifact.current_top_a >= 0.0)):
        port_failures.append("NEGATIVE_PULSE_PORT_SIGN")
    if port_failures:
        failures.extend(port_failures)
    return {
        "passed": not failures,
        "failures": failures,
        "relative_mass_drift_max": mass_drift,
        "relative_terminal_current_mismatch_max": current_mismatch,
        "y_min": y_min,
        "y_max": y_max,
        "temperature_min_k": temperature_min,
        "temperature_max_k": temperature_max,
        "relative_heat_balance_residual_max": heat_residual,
        "no_flux_residual_max": no_flux,
        "cycle_relative_drift": drift,
    }


def build_floor_seal(
    *,
    reference: SynEdtEvaluationArtifact,
    medium_space: SynEdtEvaluationArtifact,
    medium_time: SynEdtEvaluationArtifact,
    replay: SynEdtEvaluationArtifact,
    physical: Mapping[str, Any],
    numerical: Mapping[str, Any],
    normalizer_cases: Mapping[str, SynEdtEvaluationArtifact] | None = None,
) -> dict[str, Any]:
    """Build, but do not write, the frozen global QN component-floor seal."""

    declared_order = numerical["endpoint_and_floor_contract"].get(
        "components_in_fixed_order"
    )
    if tuple(declared_order or ()) != COMPONENT_ORDER:
        raise SynEdtEvaluatorError("S2 endpoint component order differs from evaluator v1")
    reference.validate()
    if reference.role != "ORACLE":
        raise SynEdtEvaluatorError("floor reference must be an oracle artifact")
    for label, artifact in (
        ("medium_space", medium_space),
        ("medium_time", medium_time),
        ("replay", replay),
    ):
        artifact.validate()
        if artifact.role != "ORACLE":
            raise SynEdtEvaluatorError(f"{label} floor source is not an oracle artifact")
        for identity in (
            "case_id",
            "physical_contract_id",
            "s0_sha256",
            "numerical_contract_sha256",
        ):
            if getattr(artifact, identity) != getattr(reference, identity):
                raise SynEdtEvaluatorError(f"{label} {identity} differs from the floor reference")
    normalizers = component_normalizers(reference, numerical)
    space = six_component_errors(
        reference=reference, candidate=medium_space, physical=physical,
        numerical=numerical, normalizers=normalizers, align_reference=True,
    )
    time_delta = six_component_errors(
        reference=reference, candidate=medium_time, physical=physical,
        numerical=numerical, normalizers=normalizers, align_reference=True,
    )
    replay_delta = six_component_errors(
        reference=reference, candidate=replay, physical=physical,
        numerical=numerical, normalizers=normalizers, align_reference=True,
    )
    solver_tolerance = float(
        numerical["endpoint_and_floor_contract"]["declared_solver_tolerance_each_dimensionless_component"]
    )
    source_uncertainty = float(numerical["endpoint_and_floor_contract"]["source_joint_uncertainty"])
    cycles: list[dict[str, Any]] = []
    for cycle in (0, 1):
        u = [
            max(space[cycle][item], time_delta[cycle][item], replay_delta[cycle][item], source_uncertainty, 2.0 * solver_tolerance)
            for item in range(len(COMPONENT_ORDER))
        ]
        tau = float(np.sqrt(np.mean(np.square(u))))
        cycles.append({
            "cycle": cycle + 1,
            "space_delta": space[cycle],
            "time_delta": time_delta[cycle],
            "replay_delta": replay_delta[cycle],
            "source_joint_uncertainty": [source_uncertainty] * len(COMPONENT_ORDER),
            "twice_declared_solver_tolerance": [2.0 * solver_tolerance] * len(COMPONENT_ORDER),
            "component_floor_u": u,
            "tau_comp": tau,
        })
    cases = normalizer_cases or {reference.case_id: reference}
    for case_id, artifact in cases.items():
        artifact.validate()
        if artifact.role != "ORACLE" or artifact.case_id != case_id:
            raise SynEdtEvaluatorError("normalizer case key/role differs from its oracle artifact")
        for identity in (
            "physical_contract_id",
            "s0_sha256",
            "numerical_contract_sha256",
        ):
            if getattr(artifact, identity) != getattr(reference, identity):
                raise SynEdtEvaluatorError(f"normalizer case {identity} differs from the floor reference")
    payload: dict[str, Any] = {
        "schema_version": FLOOR_SCHEMA,
        "physical_contract_id": reference.physical_contract_id,
        "s0_sha256": reference.s0_sha256,
        "numerical_contract_sha256": reference.numerical_contract_sha256,
        "source_case_id": reference.case_id,
        "component_order": list(COMPONENT_ORDER),
        "cycles": cycles,
        "normalizers_by_case": {
            case_id: component_normalizers(artifact, numerical)
            for case_id, artifact in sorted(cases.items())
        },
        "sealed_before_neural_work": True,
    }
    payload["seal_sha256"] = _sha256_bytes(_canonical_bytes(payload))
    return payload


def _validate_floor_seal(payload: Mapping[str, Any]) -> None:
    if payload.get("schema_version") != FLOOR_SCHEMA:
        raise SynEdtEvaluatorError("unsupported floor seal schema")
    expected = dict(payload)
    stored_hash = str(expected.pop("seal_sha256", ""))
    if stored_hash != _sha256_bytes(_canonical_bytes(expected)):
        raise SynEdtEvaluatorError("floor seal hash is invalid")
    if payload.get("sealed_before_neural_work") is not True:
        raise SynEdtEvaluatorError("floor seal lacks its pre-neural write-once assertion")
    if tuple(payload.get("component_order", ())) != COMPONENT_ORDER:
        raise SynEdtEvaluatorError("floor seal component order is invalid")
    cycles = payload.get("cycles")
    if not isinstance(cycles, list) or len(cycles) != 2:
        raise SynEdtEvaluatorError("floor seal must contain exactly two cycles")
    for cycle_index, cycle in enumerate(cycles, start=1):
        if not isinstance(cycle, Mapping) or cycle.get("cycle") != cycle_index:
            raise SynEdtEvaluatorError("floor seal cycle identity is invalid")
        source_rows: list[list[float]] = []
        for name in (
            "space_delta",
            "time_delta",
            "replay_delta",
            "source_joint_uncertainty",
            "twice_declared_solver_tolerance",
        ):
            raw = cycle.get(name)
            if not isinstance(raw, list) or len(raw) != len(COMPONENT_ORDER):
                raise SynEdtEvaluatorError(f"floor seal {name} has invalid shape")
            row = [float(item) for item in raw]
            if any(not math.isfinite(item) or item < 0.0 for item in row):
                raise SynEdtEvaluatorError(f"floor seal {name} is not finite nonnegative")
            source_rows.append(row)
        declared_floor = cycle.get("component_floor_u")
        if not isinstance(declared_floor, list) or len(declared_floor) != len(COMPONENT_ORDER):
            raise SynEdtEvaluatorError("floor seal component floor has invalid shape")
        recomputed = [max(row[item] for row in source_rows) for item in range(len(COMPONENT_ORDER))]
        if not np.array_equal(
            np.asarray(declared_floor, dtype=np.float64),
            np.asarray(recomputed, dtype=np.float64),
        ):
            raise SynEdtEvaluatorError("floor seal component floor differs from its sources")
        tau = float(cycle.get("tau_comp", math.nan))
        recomputed_tau = float(np.sqrt(np.mean(np.square(recomputed))))
        if not math.isclose(tau, recomputed_tau, rel_tol=1.0e-15, abs_tol=0.0):
            raise SynEdtEvaluatorError("floor seal tau_comp differs from its components")
    normalizers = payload.get("normalizers_by_case")
    source_case = str(payload.get("source_case_id", ""))
    if not isinstance(normalizers, Mapping) or source_case not in normalizers:
        raise SynEdtEvaluatorError("floor seal lacks its source-case normalizers")
    for case_id, rows in normalizers.items():
        if not isinstance(case_id, str) or not case_id or not isinstance(rows, list) or len(rows) != 2:
            raise SynEdtEvaluatorError("floor seal normalizer case has invalid identity or cycles")
        for row in rows:
            if not isinstance(row, Mapping):
                raise SynEdtEvaluatorError("floor seal normalizer row is invalid")
            for name in ("defect_flux", "port_current"):
                value = float(row.get(name, math.nan))
                if not math.isfinite(value) or value <= 0.0:
                    raise SynEdtEvaluatorError("floor seal normalizer is not finite positive")


def write_floor_seal(path: str | Path, payload: Mapping[str, Any]) -> None:
    _validate_floor_seal(payload)
    _write_object(path, payload, overwrite=False)


def read_floor_seal(path: str | Path) -> dict[str, Any]:
    payload = _read_object(path)
    _validate_floor_seal(payload)
    return payload


def write_attempt_manifest(
    path: str | Path,
    *,
    status: str,
    case_id: str,
    physical_contract_id: str,
    method_id: str,
    checkpoint_id: str,
    prediction_path: str | Path | None = None,
    failure_detail: str | None = None,
) -> None:
    if status not in FAILURE_ATTEMPT_STATUSES | {"PREDICTION_AVAILABLE"}:
        raise SynEdtEvaluatorError("unsupported attempt status")
    if (status == "PREDICTION_AVAILABLE") != (prediction_path is not None):
        raise SynEdtEvaluatorError("prediction path must exist exactly for PREDICTION_AVAILABLE")
    payload: dict[str, Any] = {
        "schema_version": ATTEMPT_SCHEMA,
        "status": status,
        "case_id": case_id,
        "physical_contract_id": physical_contract_id,
        "method_id": method_id,
        "checkpoint_id": checkpoint_id,
    }
    if prediction_path is not None:
        payload["prediction_path"] = str(prediction_path)
    if failure_detail is not None:
        payload["failure_detail"] = failure_detail
    _write_object(path, payload, overwrite=True)


def _infinity_score() -> dict[str, Any]:
    return {"finite": False, "value": None, "semantics": "POSITIVE_INFINITY"}


def _finite_score(value: float) -> dict[str, Any]:
    if not math.isfinite(value):
        raise SynEdtEvaluatorError("finite score is not finite")
    return {"finite": True, "value": value, "semantics": "FINITE"}


def evaluate_syn_edt_files(
    *,
    attempt_path: str | Path,
    oracle_path: str | Path,
    split_manifest_path: str | Path,
    s0_contract_path: str | Path,
    numerical_contract_path: str | Path,
    floor_path: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    """Evaluate one complete attempt using only frozen disk artifacts."""

    physical, numerical, s0_sha, numerical_sha = _contract_parts(
        s0_contract_path, numerical_contract_path
    )
    oracle = SynEdtEvaluationArtifact.read(oracle_path)
    if oracle.role != "ORACLE":
        raise SynEdtEvaluatorError("oracle artifact role is not ORACLE")
    if oracle.s0_sha256 != s0_sha or oracle.numerical_contract_sha256 != numerical_sha:
        raise SynEdtEvaluatorError("oracle artifact contract hash mismatch")
    floor = read_floor_seal(floor_path)
    if (
        floor.get("physical_contract_id") != oracle.physical_contract_id
        or floor.get("s0_sha256") != s0_sha
        or floor.get("numerical_contract_sha256") != numerical_sha
    ):
        raise SynEdtEvaluatorError("floor seal identity mismatch")
    normalizers = floor.get("normalizers_by_case", {}).get(oracle.case_id)
    if not isinstance(normalizers, list) or len(normalizers) != 2:
        raise SynEdtEvaluatorError("floor seal lacks case-specific normalizers")
    oracle_guards = hard_guard_report(
        oracle, physical=physical, numerical=numerical, normalizers=normalizers
    )
    if not oracle_guards["passed"]:
        raise SynEdtEvaluatorError("oracle hard guard failed; object must close before method scoring")
    split = _read_object(split_manifest_path)
    if split.get("schema_version") != "split-manifest-v1" or oracle.case_id not in split.get("cases", {}):
        raise SynEdtEvaluatorError("oracle case is absent from the frozen split")
    attempt = _read_object(attempt_path)
    if attempt.get("schema_version") != ATTEMPT_SCHEMA:
        raise SynEdtEvaluatorError("unsupported attempt schema")
    for key, expected in (
        ("case_id", oracle.case_id),
        ("physical_contract_id", oracle.physical_contract_id),
    ):
        if attempt.get(key) != expected:
            raise SynEdtEvaluatorError(f"attempt {key} mismatch")
    base: dict[str, Any] = {
        "schema_version": METRICS_SCHEMA,
        "evaluator_id": "SYN_EDT_2D_V1_EVALUATOR_V1",
        "case_id": oracle.case_id,
        "split_id": str(split.get("split_id", "")),
        "method_id": str(attempt.get("method_id", "")),
        "checkpoint_id": str(attempt.get("checkpoint_id", "")),
        "attempt_status": str(attempt.get("status", "")),
        "component_order": list(COMPONENT_ORDER),
        "floor_seal_sha256": str(floor["seal_sha256"]),
    }
    status = str(attempt.get("status", ""))
    if status in FAILURE_ATTEMPT_STATUSES:
        result = {
            **base,
            "cycles": [],
            "hard_guards": {"passed": False, "failures": [status]},
            "case_endpoint_z": _infinity_score(),
            "failure_detail": attempt.get("failure_detail"),
        }
        _write_object(output_path, result, overwrite=True)
        return result
    if status != "PREDICTION_AVAILABLE":
        raise SynEdtEvaluatorError("unsupported attempt status")
    prediction_file = Path(str(attempt["prediction_path"]))
    if not prediction_file.is_absolute():
        prediction_file = Path(attempt_path).resolve().parent / prediction_file
    prediction = SynEdtEvaluationArtifact.read(prediction_file)
    if prediction.role != "PREDICTION":
        raise SynEdtEvaluatorError("prediction artifact role is not PREDICTION")
    for name in ("case_id", "physical_contract_id", "s0_sha256", "numerical_contract_sha256"):
        if getattr(prediction, name) != getattr(oracle, name):
            raise SynEdtEvaluatorError(f"prediction {name} mismatch")
    if prediction.method_id != attempt.get("method_id") or prediction.checkpoint_id != attempt.get("checkpoint_id"):
        raise SynEdtEvaluatorError("prediction method/checkpoint identity mismatch")
    try:
        errors = six_component_errors(
            reference=oracle,
            candidate=prediction,
            physical=physical,
            numerical=numerical,
            normalizers=normalizers,
        )
        prediction_guards = hard_guard_report(
            prediction,
            physical=physical,
            numerical=numerical,
            normalizers=normalizers,
        )
    except NonestimableComponentError as exc:
        result = {
            **base,
            "cycles": [],
            "hard_guards": {"passed": False, "failures": [f"METHOD_NONESTIMABLE:{exc}"]},
            "case_endpoint_z": _infinity_score(),
        }
        _write_object(output_path, result, overwrite=True)
        return result
    cycles: list[dict[str, Any]] = []
    z_terms: list[float] = []
    for cycle in (0, 1):
        e_value = float(np.sqrt(np.mean(np.square(errors[cycle]))))
        tau = float(floor["cycles"][cycle]["tau_comp"])
        if not tau > 0.0 or not math.isfinite(tau):
            raise SynEdtEvaluatorError("floor tau_comp must be finite and positive")
        z_terms.append(e_value / tau)
        cycles.append({
            "cycle": cycle + 1,
            "components": dict(zip(COMPONENT_ORDER, errors[cycle])),
            "e_unclipped_rms": e_value,
            "tau_comp": tau,
        })
    endpoint = float(0.5 * sum(z_terms))
    result = {
        **base,
        "cycles": cycles,
        "hard_guards": prediction_guards,
        "case_endpoint_z": _finite_score(endpoint) if prediction_guards["passed"] else _infinity_score(),
    }
    _write_object(output_path, result, overwrite=True)
    return result


def _artifact_scales(
    physical: Mapping[str, Any], numerical: Mapping[str, Any]
) -> tuple[float, float]:
    scales = physical["scales"]
    constitutive = physical["constitutive_laws"]
    nondimensional = numerical["nondimensionalization"]
    endpoint = numerical["endpoint_and_floor_contract"]
    concentration = float(scales["concentration_m_minus_3"])
    length = float(scales["length_m"])
    thermal_voltage = float(scales["thermal_voltage_v"])
    active_sigma = float(nondimensional["active_sigma_scale_s_m"])
    characteristic_current = 2.0 * math.pi * active_sigma * length * thermal_voltage
    characteristic_flux = concentration * float(constitutive["D0_m2_s"]) / length
    if not math.isclose(
        characteristic_current,
        float(endpoint["characteristic_current_a"]),
        rel_tol=1.0e-14,
        abs_tol=0.0,
    ):
        raise SynEdtEvaluatorError("derived current scale differs from the frozen endpoint")
    if not math.isclose(
        characteristic_flux,
        float(endpoint["characteristic_particle_flux_m_minus_2_s_minus_1"]),
        rel_tol=1.0e-14,
        abs_tol=0.0,
    ):
        raise SynEdtEvaluatorError("derived particle-flux scale differs from the frozen endpoint")
    if not math.isclose(
        thermal_voltage,
        float(nondimensional["thermal_voltage_v"]),
        rel_tol=0.0,
        abs_tol=0.0,
    ):
        raise SynEdtEvaluatorError("S0 and S2 thermal-voltage scales differ")
    return concentration, characteristic_current * thermal_voltage


def artifact_from_oracle_result(
    result: Any,
    *,
    physical: Mapping[str, Any],
    numerical: Mapping[str, Any],
    s0_sha256: str,
    numerical_contract_sha256: str,
) -> SynEdtEvaluationArtifact:
    """Adapt stable ``SynEdtOracleResult`` fields without duplicated constants."""

    concentration_scale_m3, characteristic_power = _artifact_scales(
        physical, numerical
    )
    if result.physical_contract_id != physical.get("contract_id"):
        raise SynEdtEvaluatorError("oracle result and physical contract identities differ")
    if float(result.guard_report.no_flux_residual_max) != 0.0:
        raise SynEdtEvaluatorError("oracle result does not prove its structural no-flux boundary")
    bounds_m = np.asarray(result.active_cell_bounds_nm, dtype=np.float64) * 1.0e-9
    topology = build_face_topology(bounds_m)
    return SynEdtEvaluationArtifact(
        role="ORACLE",
        case_id=str(result.case_id),
        physical_contract_id=str(result.physical_contract_id),
        s0_sha256=s0_sha256,
        numerical_contract_sha256=numerical_contract_sha256,
        evidence_identity=(
            "NON_SCIENTIFIC_FIXTURE"
            if bool(result.resolution.non_scientific_fixture)
            else "SYNTHETIC_NUMERICAL_ORACLE"
        ),
        method_id="SYN_EDT_CPU_ORACLE",
        checkpoint_id=str(result.qualification_id),
        cell_bounds_m=bounds_m,
        field_time_s=np.asarray(result.field_time_s, dtype=np.float64),
        circuit_time_s=np.asarray(result.time_s, dtype=np.float64),
        y=np.asarray(result.y, dtype=np.float64),
        defect_flux_r_m2_s=np.asarray(result.defect_flux_r_m_s, dtype=np.float64) * concentration_scale_m3,
        defect_flux_z_m2_s=np.asarray(result.defect_flux_z_m_s, dtype=np.float64) * concentration_scale_m3,
        temperature_k=np.asarray(result.temperature_k, dtype=np.float64),
        boundary_normal_flux_m2_s=np.zeros((len(result.field_time_s), topology.boundary_cells.size), dtype=np.float64),
        voltage_v=np.asarray(result.voltage_v, dtype=np.float64),
        current_top_a=np.asarray(result.current_top_a, dtype=np.float64),
        current_bottom_a=np.asarray(result.current_bottom_a, dtype=np.float64),
        joule_power_w=np.asarray(result.joule_power_w, dtype=np.float64),
        joule_power_dimensionless=np.asarray(result.joule_power_w, dtype=np.float64) / characteristic_power,
        heat_sink_power_w=np.asarray(result.heat_sink_power_w, dtype=np.float64),
        non_scientific_fixture=bool(result.resolution.non_scientific_fixture),
    )


def artifact_from_persisted_oracle(
    case_artifact: Any,
    report: Mapping[str, Any],
    *,
    physical: Mapping[str, Any],
    numerical: Mapping[str, Any],
    s0_sha256: str,
    numerical_contract_sha256: str,
    method_id: str = "SYN_EDT_CPU_ORACLE",
) -> SynEdtEvaluationArtifact:
    """Rehydrate the deep evaluator artifact from the runner's H5/report pair.

    The generic H5 intentionally stores cell-centred arrays but not cell bounds.
    The companion immutable report supplies the exact active face arrays.  Both
    carriers are therefore required and cross-checked; this function never
    guesses geometry or physical scales.
    """

    concentration_scale_m3, characteristic_power = _artifact_scales(
        physical, numerical
    )
    if getattr(case_artifact, "physical_contract_id", None) != physical.get("contract_id"):
        raise SynEdtEvaluatorError("persisted artifact and physical contract identities differ")
    if report.get("physical_contract_id") != physical.get("contract_id"):
        raise SynEdtEvaluatorError("persisted report and physical contract identities differ")
    if report.get("case_id") != getattr(case_artifact, "case_id", None):
        raise SynEdtEvaluatorError("persisted H5/report case identities differ")
    if getattr(case_artifact, "mesh_unit", None) != "m" or getattr(
        case_artifact, "time_unit", None
    ) != "s":
        raise SynEdtEvaluatorError("persisted oracle must use metre and second axes")
    r_faces = np.asarray(report.get("active_r_faces_nm"), dtype=np.float64)
    z_faces = np.asarray(report.get("active_z_faces_nm"), dtype=np.float64)
    _require_time("active_r_faces_nm", r_faces)
    _require_time("active_z_faces_nm", z_faces)
    bounds_nm = np.asarray(
        [
            (r_faces[ir], r_faces[ir + 1], z_faces[iz], z_faces[iz + 1])
            for iz in range(z_faces.size - 1)
            for ir in range(r_faces.size - 1)
        ],
        dtype=np.float64,
    )
    bounds_m = bounds_nm * 1.0e-9
    centers_m = np.column_stack(
        (
            0.5 * (bounds_m[:, 0] + bounds_m[:, 1]),
            0.5 * (bounds_m[:, 2] + bounds_m[:, 3]),
        )
    )
    nodes = np.asarray(getattr(case_artifact, "nodes"), dtype=np.float64)
    if nodes.shape != centers_m.shape or not np.allclose(
        nodes, centers_m, rtol=0.0, atol=1.0e-18
    ):
        raise SynEdtEvaluatorError("persisted report geometry differs from H5 cell centres")
    required_field_units = {
        "defect_fraction_y": "1",
        "temperature": "K",
        "defect_flux_r": "m/s",
        "defect_flux_z": "m/s",
    }
    required_circuit_units = {
        "voltage": "V",
        "current_top": "A",
        "current_bottom": "A",
        "joule_power": "W",
        "heat_sink_power": "W",
    }
    if any(
        getattr(case_artifact, "field_units", {}).get(name) != unit
        for name, unit in required_field_units.items()
    ):
        raise SynEdtEvaluatorError("persisted oracle field units differ from the SYN contract")
    if any(
        getattr(case_artifact, "circuit_units", {}).get(name) != unit
        for name, unit in required_circuit_units.items()
    ):
        raise SynEdtEvaluatorError("persisted oracle circuit units differ from the SYN contract")
    guard = report.get("guard_report")
    if not isinstance(guard, Mapping) or float(guard.get("no_flux_residual_max", math.inf)) != 0.0:
        raise SynEdtEvaluatorError("persisted report does not prove structural no-flux closure")
    fields = getattr(case_artifact, "fields")
    circuit = getattr(case_artifact, "circuit")
    topology = build_face_topology(bounds_m)
    field_time = np.asarray(getattr(case_artifact, "field_time"), dtype=np.float64)
    circuit_time = np.asarray(getattr(case_artifact, "circuit_time"), dtype=np.float64)
    reported_field_time = np.asarray(report.get("field_time_s"), dtype=np.float64)
    if not np.array_equal(field_time, reported_field_time):
        raise SynEdtEvaluatorError("persisted report and H5 field-time axes differ")
    evidence_identity = str(getattr(case_artifact, "evidence_identity"))
    resolution = report.get("resolution")
    non_scientific = bool(
        isinstance(resolution, Mapping) and resolution.get("non_scientific_fixture")
    )
    if non_scientific != ("FIXTURE" in evidence_identity.upper()):
        raise SynEdtEvaluatorError("fixture identity differs between persisted H5 and report")
    value = SynEdtEvaluationArtifact(
        role="ORACLE",
        case_id=str(case_artifact.case_id),
        physical_contract_id=str(case_artifact.physical_contract_id),
        s0_sha256=s0_sha256,
        numerical_contract_sha256=numerical_contract_sha256,
        evidence_identity=evidence_identity,
        method_id=method_id,
        checkpoint_id=str(report.get("qualification_id", "")),
        cell_bounds_m=bounds_m,
        field_time_s=field_time,
        circuit_time_s=circuit_time,
        y=np.asarray(fields["defect_fraction_y"], dtype=np.float64),
        defect_flux_r_m2_s=np.asarray(fields["defect_flux_r"], dtype=np.float64)
        * concentration_scale_m3,
        defect_flux_z_m2_s=np.asarray(fields["defect_flux_z"], dtype=np.float64)
        * concentration_scale_m3,
        temperature_k=np.asarray(fields["temperature"], dtype=np.float64),
        boundary_normal_flux_m2_s=np.zeros(
            (field_time.size, topology.boundary_cells.size), dtype=np.float64
        ),
        voltage_v=np.asarray(circuit["voltage"], dtype=np.float64),
        current_top_a=np.asarray(circuit["current_top"], dtype=np.float64),
        current_bottom_a=np.asarray(circuit["current_bottom"], dtype=np.float64),
        joule_power_w=np.asarray(circuit["joule_power"], dtype=np.float64),
        joule_power_dimensionless=np.asarray(
            circuit["joule_power"], dtype=np.float64
        )
        / characteristic_power,
        heat_sink_power_w=np.asarray(circuit["heat_sink_power"], dtype=np.float64),
        non_scientific_fixture=non_scientific,
    )
    value.validate()
    return value
