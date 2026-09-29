from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import h5py
import numpy as np
from numpy.typing import NDArray


LEGACY_UNIT = "UNSPECIFIED_LEGACY_V1"
UNSPECIFIED_FIXTURE = "UNSPECIFIED_TEST_FIXTURE"
_REGISTRY_KEYS = (
    "source_name",
    "physical_symbol",
    "quantity_label",
    "unit",
    "association",
    "temporal_kind",
    "qualification_status",
)


class ArtifactContractError(ValueError):
    """An HDF5 artifact violates the canonical public disk contract."""


def _text(value: object) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def _mesh_identity(
    nodes: NDArray[np.float64],
    cells: NDArray[np.int64],
    mesh_unit: str,
) -> str:
    if mesh_unit in {LEGACY_UNIT, UNSPECIFIED_FIXTURE}:
        return mesh_unit
    digest = hashlib.sha256()
    digest.update(b"mesh-identity-v1\0")
    digest.update(mesh_unit.encode("utf-8"))
    for array in (nodes, cells):
        contiguous = np.ascontiguousarray(array)
        digest.update(str(contiguous.dtype).encode("ascii"))
        digest.update(np.asarray(contiguous.shape, dtype=np.int64).tobytes())
        digest.update(contiguous.tobytes())
    return f"sha256:{digest.hexdigest()}"


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ArtifactContractError(f"{name} must be a non-empty string")


def _require_float64(name: str, values: np.ndarray) -> None:
    if not isinstance(values, np.ndarray) or values.dtype != np.dtype(np.float64):
        raise ArtifactContractError(f"{name} must be a float64 array")
    if not np.all(np.isfinite(values)):
        raise ArtifactContractError(f"{name} contains non-finite values")


def _require_time_axis(name: str, values: np.ndarray) -> None:
    _require_float64(name, values)
    if values.ndim != 1 or values.size == 0:
        raise ArtifactContractError(f"{name} must be a non-empty one-dimensional array")
    if values.size > 1 and np.any(np.diff(values) <= 0.0):
        raise ArtifactContractError(f"{name} must be strictly increasing")


def _require_breakpoints(values: np.ndarray) -> None:
    _require_float64("breakpoints", values)
    if values.ndim != 1:
        raise ArtifactContractError("breakpoints must be one-dimensional")
    if values.size > 1 and np.any(np.diff(values) <= 0.0):
        raise ArtifactContractError("breakpoints must be strictly increasing")


def _resolve_time_axes(
    *,
    field_time: NDArray[np.float64] | None,
    circuit_time: NDArray[np.float64] | None,
    time: NDArray[np.float64] | None,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    if field_time is not None and time is not None:
        raise TypeError("provide field_time or legacy time, not both")
    resolved_field = field_time if field_time is not None else time
    if resolved_field is None:
        raise TypeError("field_time is required")
    resolved_circuit = circuit_time if circuit_time is not None else resolved_field
    return resolved_field, resolved_circuit


def _default_registry(
    field_units: dict[str, str],
    *,
    qualification_status: str = UNSPECIFIED_FIXTURE,
) -> dict[str, dict[str, str]]:
    return {
        name: {
            "source_name": name,
            "physical_symbol": name,
            "quantity_label": qualification_status,
            "unit": unit,
            "association": qualification_status,
            "temporal_kind": "dynamic",
            "qualification_status": qualification_status,
        }
        for name, unit in field_units.items()
    }


def _normalize_registry(
    field_units: dict[str, str],
    field_registry: dict[str, dict[str, str]] | None,
) -> dict[str, dict[str, str]]:
    registry = _default_registry(field_units) if field_registry is None else field_registry
    if set(registry) != set(field_units):
        raise ArtifactContractError("field_registry keys must equal field_units keys")
    normalized: dict[str, dict[str, str]] = {}
    for name, entry in registry.items():
        missing = [key for key in _REGISTRY_KEYS if key not in entry]
        if missing:
            raise ArtifactContractError(
                f"field_registry[{name!r}] missing keys: {missing}"
            )
        normalized[name] = {key: str(entry[key]) for key in _REGISTRY_KEYS}
        if normalized[name]["unit"] != field_units[name]:
            raise ArtifactContractError(f"field_registry unit mismatch for {name!r}")
    return normalized


def _read_registry(
    fields: h5py.Group,
    field_units: dict[str, str],
) -> dict[str, dict[str, str]]:
    registry: dict[str, dict[str, str]] = {}
    for name, dataset in fields.items():
        registry[name] = {key: _text(dataset.attrs[key]) for key in _REGISTRY_KEYS}
    return _normalize_registry(field_units, registry)


def _read_fields(
    fields: h5py.Group,
) -> tuple[
    dict[str, NDArray[np.float64]],
    dict[str, str],
]:
    values = {name: dataset[...] for name, dataset in fields.items()}
    units = {name: _text(dataset.attrs["unit"]) for name, dataset in fields.items()}
    return values, units


def _read_circuit(
    circuit: h5py.Group,
) -> tuple[
    dict[str, NDArray[np.float64]],
    dict[str, str],
]:
    values = {name: dataset[...] for name, dataset in circuit.items()}
    units = {name: _text(dataset.attrs["unit"]) for name, dataset in circuit.items()}
    return values, units


def _write_fields(
    handle: h5py.File,
    values: dict[str, NDArray[np.float64]],
    units: dict[str, str],
    registry: dict[str, dict[str, str]],
) -> None:
    fields = handle.create_group("fields")
    for name, array in values.items():
        dataset = fields.create_dataset(name, data=array)
        for key, value in registry[name].items():
            dataset.attrs[key] = value
        dataset.attrs["unit"] = units[name]


def _write_circuit(
    handle: h5py.File,
    values: dict[str, NDArray[np.float64]],
    units: dict[str, str],
) -> None:
    circuit = handle.create_group("circuit")
    for name, array in values.items():
        dataset = circuit.create_dataset(name, data=array)
        dataset.attrs["unit"] = units[name]


@dataclass(frozen=True, init=False)
class CaseArtifact:
    """Canonical disk contract for one complete physical case.

    ``time`` remains a read-only Python alias for ``field_time`` so the G1
    engineering fixture and its v1 artifacts remain replayable. New producers
    must use the two explicit axes.
    """

    case_id: str
    physical_contract_id: str
    evidence_identity: str
    nodes: NDArray[np.float64]
    cells: NDArray[np.int64]
    mesh_unit: str
    mesh_identity: str
    field_time: NDArray[np.float64]
    circuit_time: NDArray[np.float64]
    time_unit: str
    fields: dict[str, NDArray[np.float64]]
    field_units: dict[str, str]
    field_registry: dict[str, dict[str, str]]
    breakpoints: NDArray[np.float64]
    circuit: dict[str, NDArray[np.float64]]
    circuit_units: dict[str, str]

    SCHEMA_VERSION = "case-artifact-v2"
    LEGACY_SCHEMA_VERSION = "case-artifact-v1"

    def __init__(
        self,
        *,
        case_id: str,
        physical_contract_id: str,
        evidence_identity: str,
        nodes: NDArray[np.float64],
        cells: NDArray[np.int64],
        fields: dict[str, NDArray[np.float64]],
        field_units: dict[str, str],
        breakpoints: NDArray[np.float64],
        circuit: dict[str, NDArray[np.float64]],
        circuit_units: dict[str, str],
        field_time: NDArray[np.float64] | None = None,
        circuit_time: NDArray[np.float64] | None = None,
        time: NDArray[np.float64] | None = None,
        mesh_unit: str = UNSPECIFIED_FIXTURE,
        mesh_identity: str | None = None,
        time_unit: str = UNSPECIFIED_FIXTURE,
        field_registry: dict[str, dict[str, str]] | None = None,
    ) -> None:
        resolved_field, resolved_circuit = _resolve_time_axes(
            field_time=field_time,
            circuit_time=circuit_time,
            time=time,
        )
        computed_mesh_identity = _mesh_identity(nodes, cells, mesh_unit)
        if mesh_identity is not None and mesh_identity != computed_mesh_identity:
            raise ArtifactContractError(
                "stored mesh identity differs from nodes, cells, and mesh unit"
            )
        values: dict[str, Any] = {
            "case_id": case_id,
            "physical_contract_id": physical_contract_id,
            "evidence_identity": evidence_identity,
            "nodes": nodes,
            "cells": cells,
            "mesh_unit": mesh_unit,
            "mesh_identity": computed_mesh_identity,
            "field_time": resolved_field,
            "circuit_time": resolved_circuit,
            "time_unit": time_unit,
            "fields": fields,
            "field_units": field_units,
            "field_registry": _normalize_registry(field_units, field_registry),
            "breakpoints": breakpoints,
            "circuit": circuit,
            "circuit_units": circuit_units,
        }
        for name, value in values.items():
            object.__setattr__(self, name, value)
        self.validate()

    @property
    def time(self) -> NDArray[np.float64]:
        """Legacy alias for the field sampling axis."""

        return self.field_time

    def validate(self) -> None:
        for name in ("case_id", "physical_contract_id", "evidence_identity"):
            _require_text(name, getattr(self, name))
        _require_text("mesh_unit", self.mesh_unit)
        _require_text("mesh_identity", self.mesh_identity)
        _require_text("time_unit", self.time_unit)
        _require_float64("nodes", self.nodes)
        if self.nodes.ndim != 2 or self.nodes.shape[0] == 0 or self.nodes.shape[1] not in (2, 3):
            raise ArtifactContractError("nodes must have shape (N, 2) or (N, 3)")
        if not isinstance(self.cells, np.ndarray) or self.cells.dtype != np.dtype(np.int64):
            raise ArtifactContractError("cells must be an int64 array")
        if self.cells.ndim != 2 or self.cells.shape[0] == 0 or self.cells.shape[1] == 0:
            raise ArtifactContractError("cells must be a non-empty two-dimensional array")
        if np.any(self.cells < 0) or np.any(self.cells >= self.nodes.shape[0]):
            raise ArtifactContractError("cell index is outside the node array")
        _require_time_axis("field_time", self.field_time)
        _require_time_axis("circuit_time", self.circuit_time)
        _require_breakpoints(self.breakpoints)
        if not self.fields or set(self.fields) != set(self.field_units):
            raise ArtifactContractError("case fields and field units must be non-empty and aligned")
        if set(self.field_registry) != set(self.fields):
            raise ArtifactContractError("case field registry does not match fields")
        for name, values in self.fields.items():
            _require_text(f"field unit {name}", self.field_units[name])
            _require_float64(f"field {name}", values)
            if values.shape != (self.field_time.size, self.nodes.shape[0]):
                raise ArtifactContractError(
                    f"field {name!r} shape does not match field_time and mesh"
                )
        if not self.circuit or set(self.circuit) != set(self.circuit_units):
            raise ArtifactContractError(
                "case circuit channels and units must be non-empty and aligned"
            )
        for name, values in self.circuit.items():
            _require_text(f"circuit unit {name}", self.circuit_units[name])
            _require_float64(f"circuit {name}", values)
            if values.shape != (self.circuit_time.size,):
                raise ArtifactContractError(
                    f"circuit channel {name!r} shape does not match circuit_time"
                )
        if self.mesh_identity != _mesh_identity(self.nodes, self.cells, self.mesh_unit):
            raise ArtifactContractError("mesh identity no longer matches mesh content")

    def write(self, path: str | Path) -> None:
        self.validate()
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with h5py.File(destination, "w") as handle:
            handle.attrs["schema_version"] = self.SCHEMA_VERSION
            handle.attrs["case_id"] = self.case_id
            handle.attrs["physical_contract_id"] = self.physical_contract_id
            handle.attrs["evidence_identity"] = self.evidence_identity
            handle.attrs["mesh_identity"] = self.mesh_identity

            mesh = handle.create_group("mesh")
            mesh.attrs["unit"] = self.mesh_unit
            mesh.create_dataset("nodes", data=self.nodes)
            mesh.create_dataset("cells", data=self.cells)

            time = handle.create_group("time")
            time.attrs["unit"] = self.time_unit
            time.create_dataset("field", data=self.field_time)
            time.create_dataset("circuit", data=self.circuit_time)

            protocol = handle.create_group("protocol")
            breakpoints = protocol.create_dataset("breakpoints", data=self.breakpoints)
            breakpoints.attrs["unit"] = self.time_unit

            _write_fields(handle, self.fields, self.field_units, self.field_registry)
            _write_circuit(handle, self.circuit, self.circuit_units)

    @classmethod
    def read(cls, path: str | Path) -> "CaseArtifact":
        with h5py.File(Path(path), "r") as handle:
            schema = _text(handle.attrs.get("schema_version", "MISSING"))
            if schema not in {cls.SCHEMA_VERSION, cls.LEGACY_SCHEMA_VERSION}:
                raise ValueError(f"unsupported case artifact schema: {schema!r}")
            fields, field_units = _read_fields(handle["fields"])
            circuit, circuit_units = _read_circuit(handle["circuit"])
            if schema == cls.LEGACY_SCHEMA_VERSION:
                legacy_time = handle["time"][...]
                registry = _default_registry(
                    field_units,
                    qualification_status="LEGACY_V1_UNSPECIFIED",
                )
                return cls(
                    case_id=_text(handle.attrs["case_id"]),
                    physical_contract_id=_text(handle.attrs["physical_contract_id"]),
                    evidence_identity=_text(handle.attrs["evidence_identity"]),
                    nodes=handle["mesh/nodes"][...],
                    cells=handle["mesh/cells"][...],
                    mesh_unit=LEGACY_UNIT,
                    mesh_identity=LEGACY_UNIT,
                    field_time=legacy_time,
                    circuit_time=legacy_time.copy(),
                    time_unit=LEGACY_UNIT,
                    fields=fields,
                    field_units=field_units,
                    field_registry=registry,
                    breakpoints=handle["protocol/breakpoints"][...],
                    circuit=circuit,
                    circuit_units=circuit_units,
                )
            return cls(
                case_id=_text(handle.attrs["case_id"]),
                physical_contract_id=_text(handle.attrs["physical_contract_id"]),
                evidence_identity=_text(handle.attrs["evidence_identity"]),
                nodes=handle["mesh/nodes"][...],
                cells=handle["mesh/cells"][...],
                mesh_unit=_text(handle["mesh"].attrs["unit"]),
                mesh_identity=_text(handle.attrs["mesh_identity"]),
                field_time=handle["time/field"][...],
                circuit_time=handle["time/circuit"][...],
                time_unit=_text(handle["time"].attrs["unit"]),
                fields=fields,
                field_units=field_units,
                field_registry=_read_registry(handle["fields"], field_units),
                breakpoints=handle["protocol/breakpoints"][...],
                circuit=circuit,
                circuit_units=circuit_units,
            )


@dataclass(frozen=True, init=False)
class PredictionArtifact:
    """Canonical disk contract for model predictions at one checkpoint."""

    case_id: str
    physical_contract_id: str
    method_id: str
    checkpoint_id: str
    mesh_identity: str
    field_time: NDArray[np.float64]
    circuit_time: NDArray[np.float64]
    time_unit: str
    fields: dict[str, NDArray[np.float64]]
    field_units: dict[str, str]
    field_registry: dict[str, dict[str, str]]
    circuit: dict[str, NDArray[np.float64]]
    circuit_units: dict[str, str]

    SCHEMA_VERSION = "prediction-artifact-v2"
    LEGACY_SCHEMA_VERSION = "prediction-artifact-v1"

    def __init__(
        self,
        *,
        case_id: str,
        physical_contract_id: str,
        method_id: str,
        checkpoint_id: str,
        fields: dict[str, NDArray[np.float64]],
        field_units: dict[str, str],
        circuit: dict[str, NDArray[np.float64]],
        circuit_units: dict[str, str],
        field_time: NDArray[np.float64] | None = None,
        circuit_time: NDArray[np.float64] | None = None,
        time: NDArray[np.float64] | None = None,
        time_unit: str = UNSPECIFIED_FIXTURE,
        mesh_identity: str = UNSPECIFIED_FIXTURE,
        field_registry: dict[str, dict[str, str]] | None = None,
    ) -> None:
        resolved_field, resolved_circuit = _resolve_time_axes(
            field_time=field_time,
            circuit_time=circuit_time,
            time=time,
        )
        values: dict[str, Any] = {
            "case_id": case_id,
            "physical_contract_id": physical_contract_id,
            "method_id": method_id,
            "checkpoint_id": checkpoint_id,
            "mesh_identity": mesh_identity,
            "field_time": resolved_field,
            "circuit_time": resolved_circuit,
            "time_unit": time_unit,
            "fields": fields,
            "field_units": field_units,
            "field_registry": _normalize_registry(field_units, field_registry),
            "circuit": circuit,
            "circuit_units": circuit_units,
        }
        for name, value in values.items():
            object.__setattr__(self, name, value)
        self.validate()

    @property
    def time(self) -> NDArray[np.float64]:
        """Legacy alias for the field sampling axis."""

        return self.field_time

    def validate(self) -> None:
        for name in (
            "case_id",
            "physical_contract_id",
            "method_id",
            "checkpoint_id",
            "mesh_identity",
            "time_unit",
        ):
            _require_text(name, getattr(self, name))
        _require_time_axis("field_time", self.field_time)
        _require_time_axis("circuit_time", self.circuit_time)
        if not self.fields or set(self.fields) != set(self.field_units):
            raise ArtifactContractError(
                "prediction is missing fields or field units are not aligned"
            )
        if set(self.field_registry) != set(self.fields):
            raise ArtifactContractError("prediction field registry does not match fields")
        spatial_width: int | None = None
        for name, values in self.fields.items():
            _require_text(f"field unit {name}", self.field_units[name])
            _require_float64(f"field {name}", values)
            if values.ndim != 2 or values.shape[0] != self.field_time.size or values.shape[1] == 0:
                raise ArtifactContractError(
                    f"prediction field {name!r} shape does not match field_time"
                )
            if spatial_width is None:
                spatial_width = values.shape[1]
            elif values.shape[1] != spatial_width:
                raise ArtifactContractError("prediction fields use different mesh widths")
        if not self.circuit or set(self.circuit) != set(self.circuit_units):
            raise ArtifactContractError(
                "prediction circuit channels and units must be non-empty and aligned"
            )
        for name, values in self.circuit.items():
            _require_text(f"circuit unit {name}", self.circuit_units[name])
            _require_float64(f"circuit {name}", values)
            if values.shape != (self.circuit_time.size,):
                raise ArtifactContractError(
                    f"prediction circuit channel {name!r} shape does not match circuit_time"
                )

    def write(self, path: str | Path) -> None:
        self.validate()
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with h5py.File(destination, "w") as handle:
            handle.attrs["schema_version"] = self.SCHEMA_VERSION
            handle.attrs["case_id"] = self.case_id
            handle.attrs["physical_contract_id"] = self.physical_contract_id
            handle.attrs["method_id"] = self.method_id
            handle.attrs["checkpoint_id"] = self.checkpoint_id
            handle.attrs["mesh_identity"] = self.mesh_identity

            time = handle.create_group("time")
            time.attrs["unit"] = self.time_unit
            time.create_dataset("field", data=self.field_time)
            time.create_dataset("circuit", data=self.circuit_time)

            _write_fields(handle, self.fields, self.field_units, self.field_registry)
            _write_circuit(handle, self.circuit, self.circuit_units)

    @classmethod
    def read(cls, path: str | Path) -> "PredictionArtifact":
        with h5py.File(Path(path), "r") as handle:
            schema = _text(handle.attrs.get("schema_version", "MISSING"))
            if schema not in {cls.SCHEMA_VERSION, cls.LEGACY_SCHEMA_VERSION}:
                raise ValueError(f"unsupported prediction artifact schema: {schema!r}")
            fields, field_units = _read_fields(handle["fields"])
            circuit, circuit_units = _read_circuit(handle["circuit"])
            if schema == cls.LEGACY_SCHEMA_VERSION:
                legacy_time = handle["time"][...]
                registry = _default_registry(
                    field_units,
                    qualification_status="LEGACY_V1_UNSPECIFIED",
                )
                return cls(
                    case_id=_text(handle.attrs["case_id"]),
                    physical_contract_id=_text(handle.attrs["physical_contract_id"]),
                    method_id=_text(handle.attrs["method_id"]),
                    checkpoint_id=_text(handle.attrs["checkpoint_id"]),
                    mesh_identity=LEGACY_UNIT,
                    field_time=legacy_time,
                    circuit_time=legacy_time.copy(),
                    time_unit=LEGACY_UNIT,
                    fields=fields,
                    field_units=field_units,
                    field_registry=registry,
                    circuit=circuit,
                    circuit_units=circuit_units,
                )
            return cls(
                case_id=_text(handle.attrs["case_id"]),
                physical_contract_id=_text(handle.attrs["physical_contract_id"]),
                method_id=_text(handle.attrs["method_id"]),
                checkpoint_id=_text(handle.attrs["checkpoint_id"]),
                mesh_identity=_text(handle.attrs["mesh_identity"]),
                field_time=handle["time/field"][...],
                circuit_time=handle["time/circuit"][...],
                time_unit=_text(handle["time"].attrs["unit"]),
                fields=fields,
                field_units=field_units,
                field_registry=_read_registry(handle["fields"], field_units),
                circuit=circuit,
                circuit_units=circuit_units,
            )
