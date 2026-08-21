from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from .artifacts import ArtifactContractError, CaseArtifact


@dataclass(frozen=True)
class QPopConversionRequest:
    native_run_dir: Path
    conversion_spec_path: Path
    bundle_dir: Path


@dataclass(frozen=True)
class QPopConversionReport:
    status: str
    conversion_spec_id: str
    case_id: str
    error_code: str | None
    error_message: str | None
    artifact_sha256: str | None
    conversion_spec_sha256: str | None
    field_snapshot_count: int
    circuit_sample_count: int
    node_count: int
    cell_count: int
    source_files: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    schema_version: str = "qpop-conversion-report-v1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class QPopConversionError(RuntimeError):
    """A native Q-POP package violated the frozen conversion contract."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.detail = message


@dataclass
class _ConversionState:
    native_root: Path
    consumed: dict[str, str] = field(default_factory=dict)

    def consume(self, path: Path) -> None:
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(self.native_root)
        except ValueError as exc:
            raise QPopConversionError(
                "SOURCE_IDENTITY_MISMATCH",
                f"input path escapes native run directory: {resolved}",
            ) from exc
        self.consumed[relative.as_posix()] = _sha256(resolved)


@dataclass(frozen=True)
class _NativeLog:
    columns: dict[str, np.ndarray]
    row_count: int


@dataclass(frozen=True)
class _MeshField:
    nodes: np.ndarray
    cells: np.ndarray
    values: np.ndarray


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise QPopConversionError(
            "SOURCE_IDENTITY_MISMATCH",
            f"cannot read JSON contract {path}: {exc}",
        ) from exc
    if not isinstance(loaded, dict):
        raise QPopConversionError(
            "SOURCE_IDENTITY_MISMATCH",
            f"JSON contract is not an object: {path}",
        )
    return loaded


def _resolve_within(root: Path, relative: str, *, error_code: str) -> Path:
    root_resolved = root.resolve()
    candidate = (root_resolved / relative).resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise QPopConversionError(
            error_code,
            f"referenced path escapes native directory: {relative!r}",
        ) from exc
    return candidate


def _normalized_header(value: str) -> str:
    return " ".join(value.strip().split())


def _xml_snapshot(path: Path) -> dict[str, dict[str, Any]]:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise QPopConversionError(
            "INPUT_DELTA_NOT_ALLOWED",
            f"cannot parse frozen input XML {path}: {exc}",
        ) from exc
    snapshot: dict[str, dict[str, Any]] = {}

    def visit(element: ET.Element, element_path: str) -> None:
        children = list(element)
        snapshot[element_path] = {
            "attributes": dict(sorted(element.attrib.items())),
            "text": (element.text or "").strip(),
            "children": [child.tag for child in children],
        }
        totals: dict[str, int] = {}
        for child in children:
            totals[child.tag] = totals.get(child.tag, 0) + 1
        seen: dict[str, int] = {}
        for child in children:
            seen[child.tag] = seen.get(child.tag, 0) + 1
            suffix = f"[{seen[child.tag]}]" if totals[child.tag] > 1 else ""
            visit(child, f"{element_path}/{child.tag}{suffix}")

    visit(root, f"/{root.tag}")
    return snapshot


def _validate_allowed_input_delta(
    *,
    spec: dict[str, Any],
    spec_path: Path,
    native_input_path: Path,
) -> None:
    canonical_relative = spec.get("canonical_input_path")
    if not isinstance(canonical_relative, str) or not canonical_relative:
        raise QPopConversionError(
            "INPUT_DELTA_NOT_ALLOWED",
            "canonical_input_path is absent from conversion spec",
        )
    canonical_path = _resolve_within(
        spec_path.parent,
        canonical_relative,
        error_code="INPUT_DELTA_NOT_ALLOWED",
    )
    if not canonical_path.is_file():
        raise QPopConversionError(
            "INPUT_DELTA_NOT_ALLOWED",
            "canonical input file is missing",
        )
    if _sha256(canonical_path) != str(spec.get("canonical_input_sha256", "")):
        raise QPopConversionError(
            "INPUT_DELTA_NOT_ALLOWED",
            "canonical input hash differs from conversion spec",
        )
    canonical = _xml_snapshot(canonical_path)
    native = _xml_snapshot(native_input_path)
    if set(canonical) != set(native):
        raise QPopConversionError(
            "INPUT_DELTA_NOT_ALLOWED",
            "native input XML topology differs from canonical input",
        )
    differences = {
        path for path in canonical if canonical[path] != native[path]
    }
    allowed_entries = spec.get("allowed_input_differences")
    if not isinstance(allowed_entries, list) or not allowed_entries:
        raise QPopConversionError(
            "INPUT_DELTA_NOT_ALLOWED",
            "allowed_input_differences is absent",
        )
    allowed: dict[str, dict[str, Any]] = {}
    for entry in allowed_entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("xpath"), str):
            raise QPopConversionError(
                "INPUT_DELTA_NOT_ALLOWED",
                "allowed input difference entry is invalid",
            )
        path = str(entry["xpath"])
        if path in allowed:
            raise QPopConversionError(
                "INPUT_DELTA_NOT_ALLOWED",
                f"duplicate allowed input XPath: {path}",
            )
        allowed[path] = entry
    if differences != set(allowed):
        raise QPopConversionError(
            "INPUT_DELTA_NOT_ALLOWED",
            "native input changes are not exactly the frozen allowed XPath set",
        )
    for path, entry in allowed.items():
        canonical_node = canonical[path]
        native_node = native[path]
        if canonical_node["children"] or native_node["children"]:
            raise QPopConversionError(
                "INPUT_DELTA_NOT_ALLOWED",
                f"allowed input XPath must identify a leaf: {path}",
            )
        if canonical_node["attributes"] != native_node["attributes"]:
            raise QPopConversionError(
                "INPUT_DELTA_NOT_ALLOWED",
                f"attributes changed at allowed input XPath: {path}",
            )
        if canonical_node["text"] != str(entry.get("canonical_value", "")):
            raise QPopConversionError(
                "INPUT_DELTA_NOT_ALLOWED",
                f"canonical value differs at {path}",
            )
        if native_node["text"] != str(entry.get("smoke_value", "")):
            raise QPopConversionError(
                "INPUT_DELTA_NOT_ALLOWED",
                f"native smoke value differs at {path}",
            )
        expected_unit = entry.get("unit")
        if expected_unit is not None and canonical_node["attributes"].get("unit") != str(
            expected_unit
        ):
            raise QPopConversionError(
                "INPUT_DELTA_NOT_ALLOWED",
                f"unit differs at {path}",
            )


def _validate_source_and_input(
    spec: dict[str, Any],
    spec_path: Path,
    state: _ConversionState,
) -> None:
    metadata_path = state.native_root / "qpop_run_metadata.json"
    input_path = state.native_root / "input.xml"
    if not metadata_path.is_file() or not input_path.is_file():
        raise QPopConversionError(
            "SOURCE_IDENTITY_MISMATCH",
            "native run requires qpop_run_metadata.json and input.xml",
        )
    metadata = _load_json(metadata_path)
    if metadata.get("conversion_spec_sha256") != _sha256(spec_path):
        raise QPopConversionError(
            "SOURCE_IDENTITY_MISMATCH",
            "native intent metadata is not bound to the exact conversion spec",
        )
    expected_source = spec.get("source_identity")
    if metadata.get("source_identity") != expected_source:
        raise QPopConversionError(
            "SOURCE_IDENTITY_MISMATCH",
            "native source identity differs from conversion spec",
        )
    required_source_files = spec.get("required_source_files")
    if not isinstance(required_source_files, dict) or not required_source_files:
        raise QPopConversionError(
            "SOURCE_IDENTITY_MISMATCH",
            "required_source_files is absent from conversion spec",
        )
    for relative, expected_hash in required_source_files.items():
        source_path = _resolve_within(
            state.native_root,
            str(relative),
            error_code="SOURCE_IDENTITY_MISMATCH",
        )
        if not source_path.is_file() or _sha256(source_path) != str(expected_hash):
            raise QPopConversionError(
                "SOURCE_IDENTITY_MISMATCH",
                f"executed source file differs from frozen hash: {relative}",
            )
        state.consume(source_path)
    actual_input_sha = _sha256(input_path)
    if metadata.get("input_sha256") != actual_input_sha:
        raise QPopConversionError(
            "INPUT_DELTA_NOT_ALLOWED",
            "native input hash differs from its run metadata",
        )
    if spec.get("expected_input_sha256") != actual_input_sha:
        raise QPopConversionError(
            "INPUT_DELTA_NOT_ALLOWED",
            "native input hash differs from the frozen conversion spec",
        )
    _validate_allowed_input_delta(
        spec=spec,
        spec_path=spec_path,
        native_input_path=input_path,
    )
    state.consume(metadata_path)
    state.consume(input_path)


def _parse_log(
    spec: dict[str, Any],
    state: _ConversionState,
) -> _NativeLog:
    log_path = state.native_root / "log.txt"
    if not log_path.is_file():
        raise QPopConversionError("NATIVE_RUN_INCOMPLETE", "log.txt is missing")
    state.consume(log_path)
    try:
        lines = log_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise QPopConversionError("LOG_PROFILE_MISMATCH", "log.txt is not UTF-8") from exc
    if not lines:
        raise QPopConversionError("NATIVE_RUN_INCOMPLETE", "log.txt is empty")

    profile = spec.get("log_profile")
    if not isinstance(profile, dict):
        raise QPopConversionError("LOG_PROFILE_MISMATCH", "log_profile is absent")
    expected_header = _normalized_header(str(profile.get("normalized_header", "")))
    if _normalized_header(lines[0]) != expected_header:
        raise QPopConversionError(
            "LOG_PROFILE_MISMATCH",
            "native log header differs from the frozen profile",
        )
    column_keys = profile.get("column_keys")
    if not isinstance(column_keys, list) or len(column_keys) != 11:
        raise QPopConversionError(
            "LOG_PROFILE_MISMATCH",
            "frozen Q-POP log profile must define exactly 11 columns",
        )

    rows: list[list[float]] = []
    finished = False
    previous_step = 0
    previous_time = -math.inf
    previous_failures = (0, 0, 0)
    output_marker = re.compile(r"^-\s+\d+\s+[-+0-9.eE]+\s+-\s+out$")
    success_trailer = re.compile(
        r"^Finished computation, computation time:\s+[0-9]+\.[0-9]{3}\s+s\.$"
    )
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        if finished and not stripped.startswith("Finished computation"):
            raise QPopConversionError(
                "LOG_PROFILE_MISMATCH",
                "native log success trailer is not the last nonempty record",
            )
        if "Solving process diverged" in stripped:
            raise QPopConversionError(
                "NATIVE_RUN_DIVERGED",
                "native log reports solver divergence",
            )
        if stripped.startswith("Finished computation"):
            if success_trailer.fullmatch(stripped) is None:
                raise QPopConversionError(
                    "LOG_PROFILE_MISMATCH",
                    "native log success trailer differs from the frozen profile",
                )
            if finished:
                raise QPopConversionError(
                    "LOG_PROFILE_MISMATCH",
                    "native log contains more than one success trailer",
                )
            if not rows:
                raise QPopConversionError(
                    "LOG_PROFILE_MISMATCH",
                    "native log success trailer precedes every accepted step",
                )
            finished = True
            continue
        if output_marker.fullmatch(stripped):
            continue
        parts = stripped.split()
        if len(parts) != len(column_keys):
            raise QPopConversionError(
                "LOG_ROW_INVALID",
                f"accepted-step row has {len(parts)} values; expected {len(column_keys)}",
            )
        try:
            row = [float(value) for value in parts]
        except ValueError as exc:
            raise QPopConversionError(
                "LOG_ROW_INVALID",
                f"accepted-step row is not numeric: {stripped}",
            ) from exc
        if not np.all(np.isfinite(row)):
            raise QPopConversionError("NONFINITE_NATIVE_VALUE", "non-finite value in log row")
        step = int(row[0])
        failures = (int(row[3]), int(row[4]), int(row[5]))
        if row[0] != step or step != previous_step + 1:
            raise QPopConversionError("LOG_ROW_INVALID", "step column is not contiguous integer")
        if row[1] <= previous_time or row[2] <= 0.0:
            raise QPopConversionError(
                "LOG_ROW_INVALID",
                "time must be strictly increasing and time step must be positive",
            )
        if any(row[index] != failures[index - 3] for index in (3, 4, 5)):
            raise QPopConversionError("LOG_ROW_INVALID", "failure counters must be integers")
        if any(current < prior for current, prior in zip(failures, previous_failures)):
            raise QPopConversionError("LOG_ROW_INVALID", "failure counters decreased")
        rows.append(row)
        previous_step = step
        previous_time = row[1]
        previous_failures = failures
    if not rows or not finished:
        raise QPopConversionError(
            "NATIVE_RUN_INCOMPLETE",
            "native run requires at least one accepted step and a success trailer",
        )
    matrix = np.asarray(rows, dtype=np.float64)
    return _NativeLog(
        columns={str(key): matrix[:, index] for index, key in enumerate(column_keys)},
        row_count=matrix.shape[0],
    )


def _parse_xml(path: Path, state: _ConversionState, *, code: str) -> ET.Element:
    if not path.is_file():
        raise QPopConversionError(code, f"required native file is missing: {path.name}")
    state.consume(path)
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise QPopConversionError(code, f"invalid XML in {path.name}: {exc}") from exc


def _numeric_array(element: ET.Element, *, dtype: Any, label: str) -> np.ndarray:
    if element.attrib.get("format") != "ascii":
        raise QPopConversionError(
            "UNSUPPORTED_VTK_ENCODING",
            f"{label} is not VTK ASCII encoding",
        )
    values = np.fromstring(element.text or "", sep=" ", dtype=dtype)
    if values.size == 0:
        raise QPopConversionError("ARTIFACT_VALIDATION_FAILED", f"{label} is empty")
    if np.issubdtype(values.dtype, np.floating) and not np.all(np.isfinite(values)):
        raise QPopConversionError("NONFINITE_NATIVE_VALUE", f"non-finite value in {label}")
    return values


def _named_data_array(parent: ET.Element, name: str, *, code: str) -> ET.Element:
    for element in parent.findall("DataArray"):
        if element.attrib.get("Name") == name:
            return element
    raise QPopConversionError(code, f"VTK array {name!r} is missing")


def _parse_vtu_piece(
    path: Path,
    *,
    source_name: str,
    mesh_spec: dict[str, Any],
    state: _ConversionState,
) -> _MeshField:
    root = _parse_xml(path, state, code="FIELD_SET_MISMATCH")
    if root.attrib.get("type") != "UnstructuredGrid":
        raise QPopConversionError(
            "UNSUPPORTED_VTK_ENCODING",
            f"{path.name} is not an UnstructuredGrid",
        )
    piece = root.find("./UnstructuredGrid/Piece")
    if piece is None:
        raise QPopConversionError("MESH_TOPOLOGY_MISMATCH", f"{path.name} has no Piece")
    points_array = piece.find("./Points/DataArray")
    if points_array is None:
        raise QPopConversionError("MESH_TOPOLOGY_MISMATCH", f"{path.name} has no points")
    components = int(points_array.attrib.get("NumberOfComponents", "0"))
    points_flat = _numeric_array(points_array, dtype=np.float64, label="points")
    if components != 3 or points_flat.size % components:
        raise QPopConversionError(
            "MESH_TOPOLOGY_MISMATCH",
            "Q-POP point coordinates must have three components",
        )
    points = points_flat.reshape(-1, components)
    dimension = int(mesh_spec.get("dimension", 0))
    drop_axis = int(mesh_spec.get("drop_axis", -1))
    drop_tolerance = float(mesh_spec.get("drop_tolerance", 0.0))
    if dimension != 2 or drop_axis not in (0, 1, 2):
        raise QPopConversionError(
            "MESH_TOPOLOGY_MISMATCH",
            "G2 converter supports only a frozen planar two-dimensional mesh",
        )
    if np.any(np.abs(points[:, drop_axis]) > drop_tolerance):
        raise QPopConversionError(
            "MESH_TOPOLOGY_MISMATCH",
            "coordinate on the frozen planar drop axis exceeds tolerance",
        )
    points = np.delete(points, drop_axis, axis=1).astype(np.float64, copy=False)

    cells_parent = piece.find("./Cells")
    if cells_parent is None:
        raise QPopConversionError("MESH_TOPOLOGY_MISMATCH", f"{path.name} has no cells")
    connectivity = _numeric_array(
        _named_data_array(cells_parent, "connectivity", code="MESH_TOPOLOGY_MISMATCH"),
        dtype=np.int64,
        label="connectivity",
    )
    offsets = _numeric_array(
        _named_data_array(cells_parent, "offsets", code="MESH_TOPOLOGY_MISMATCH"),
        dtype=np.int64,
        label="offsets",
    )
    cell_types = _numeric_array(
        _named_data_array(cells_parent, "types", code="MESH_TOPOLOGY_MISMATCH"),
        dtype=np.int64,
        label="cell types",
    )
    if offsets.size != cell_types.size or offsets[-1] != connectivity.size:
        raise QPopConversionError("MESH_TOPOLOGY_MISMATCH", "invalid VTK cell offsets")
    allowed_types = {int(value) for value in mesh_spec.get("allowed_cell_types", [])}
    if not allowed_types or any(int(value) not in allowed_types for value in cell_types):
        raise QPopConversionError("MESH_TOPOLOGY_MISMATCH", "unexpected VTK cell type")
    starts = np.concatenate((np.array([0], dtype=np.int64), offsets[:-1]))
    widths = offsets - starts
    if np.any(widths <= 0) or not np.all(widths == widths[0]):
        raise QPopConversionError(
            "MESH_TOPOLOGY_MISMATCH",
            "mixed or empty cell arity is not supported",
        )
    cells = np.vstack(
        [connectivity[start:end] for start, end in zip(starts.tolist(), offsets.tolist())]
    ).astype(np.int64, copy=False)
    if np.any(cells < 0) or np.any(cells >= points.shape[0]):
        raise QPopConversionError("MESH_TOPOLOGY_MISMATCH", "cell index is out of bounds")

    point_data = piece.find("./PointData")
    if point_data is None:
        raise QPopConversionError("FIELD_SET_MISMATCH", f"{path.name} has no PointData")
    values = _numeric_array(
        _named_data_array(point_data, source_name, code="FIELD_SET_MISMATCH"),
        dtype=np.float64,
        label=source_name,
    )
    if values.shape != (points.shape[0],):
        raise QPopConversionError(
            "FIELD_SET_MISMATCH",
            f"field {source_name!r} does not have one value per point",
        )
    return _MeshField(nodes=points, cells=cells, values=values)


def _merge_pieces(pieces: list[_MeshField]) -> _MeshField:
    if not pieces:
        raise QPopConversionError("FIELD_SET_MISMATCH", "PVTU contains no pieces")
    global_nodes: list[np.ndarray] = []
    global_values: list[float] = []
    global_cells: list[np.ndarray] = []
    node_index: dict[tuple[float, ...], int] = {}
    cell_width: int | None = None
    for piece in pieces:
        local_to_global = np.empty(piece.nodes.shape[0], dtype=np.int64)
        for local, node in enumerate(piece.nodes):
            key = tuple(float(value) for value in node)
            existing = node_index.get(key)
            if existing is None:
                existing = len(global_nodes)
                node_index[key] = existing
                global_nodes.append(node.copy())
                global_values.append(float(piece.values[local]))
            elif global_values[existing] != float(piece.values[local]):
                raise QPopConversionError(
                    "MESH_TOPOLOGY_MISMATCH",
                    "shared point carries inconsistent field values across pieces",
                )
            local_to_global[local] = existing
        remapped = local_to_global[piece.cells]
        if cell_width is None:
            cell_width = remapped.shape[1]
        if remapped.shape[1] != cell_width:
            raise QPopConversionError("MESH_TOPOLOGY_MISMATCH", "piece cell arity differs")
        global_cells.extend(row.copy() for row in remapped)
    return _MeshField(
        nodes=np.asarray(global_nodes, dtype=np.float64),
        cells=np.asarray(global_cells, dtype=np.int64),
        values=np.asarray(global_values, dtype=np.float64),
    )


def _parse_pvtu(
    path: Path,
    *,
    source_name: str,
    mesh_spec: dict[str, Any],
    state: _ConversionState,
    solution_root: Path,
) -> _MeshField:
    root = _parse_xml(path, state, code="FIELD_SET_MISMATCH")
    if root.attrib.get("type") != "PUnstructuredGrid":
        raise QPopConversionError(
            "UNSUPPORTED_VTK_ENCODING",
            f"{path.name} is not a PUnstructuredGrid",
        )
    grid = root.find("./PUnstructuredGrid")
    if grid is None:
        raise QPopConversionError("FIELD_SET_MISMATCH", f"{path.name} has no grid")
    advertised = grid.find("./PPointData/PDataArray")
    if advertised is None or advertised.attrib.get("Name") != source_name:
        raise QPopConversionError(
            "FIELD_SET_MISMATCH",
            f"PVTU does not advertise required point field {source_name!r}",
        )
    pieces: list[_MeshField] = []
    for piece in grid.findall("Piece"):
        source = piece.attrib.get("Source")
        if not source:
            raise QPopConversionError("FIELD_SET_MISMATCH", "PVTU piece has no Source")
        piece_path = _resolve_within(solution_root, source, error_code="FIELD_SET_MISMATCH")
        pieces.append(
            _parse_vtu_piece(
                piece_path,
                source_name=source_name,
                mesh_spec=mesh_spec,
                state=state,
            )
        )
    return _merge_pieces(pieces)


def _parse_dynamic_field(
    *,
    pvd_path: Path,
    source_name: str,
    mesh_spec: dict[str, Any],
    state: _ConversionState,
    solution_root: Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    root = _parse_xml(pvd_path, state, code="FIELD_SET_MISMATCH")
    if root.attrib.get("type") != "Collection":
        raise QPopConversionError("FIELD_SET_MISMATCH", f"{pvd_path.name} is not a Collection")
    datasets = root.findall("./Collection/DataSet")
    if not datasets:
        raise QPopConversionError("FIELD_SET_MISMATCH", f"{pvd_path.name} has no snapshots")
    times: list[float] = []
    snapshots: list[np.ndarray] = []
    canonical_nodes: np.ndarray | None = None
    canonical_cells: np.ndarray | None = None
    for dataset in datasets:
        try:
            time = float(dataset.attrib["timestep"])
            relative = dataset.attrib["file"]
        except (KeyError, ValueError) as exc:
            raise QPopConversionError(
                "FIELD_TIME_MISMATCH",
                "PVD snapshot lacks a finite timestep or file",
            ) from exc
        if not math.isfinite(time) or (times and time <= times[-1]):
            raise QPopConversionError(
                "FIELD_TIME_MISMATCH",
                "field time must be finite and strictly increasing",
            )
        pvtu_path = _resolve_within(solution_root, relative, error_code="FIELD_SET_MISMATCH")
        merged = _parse_pvtu(
            pvtu_path,
            source_name=source_name,
            mesh_spec=mesh_spec,
            state=state,
            solution_root=solution_root,
        )
        if canonical_nodes is None:
            canonical_nodes = merged.nodes
            canonical_cells = merged.cells
        elif not np.array_equal(merged.nodes, canonical_nodes) or not np.array_equal(
            merged.cells, canonical_cells
        ):
            raise QPopConversionError(
                "MESH_TOPOLOGY_MISMATCH",
                f"mesh changed across snapshots in {pvd_path.name}",
            )
        times.append(time)
        snapshots.append(merged.values)
    assert canonical_nodes is not None and canonical_cells is not None
    return (
        np.asarray(times, dtype=np.float64),
        canonical_nodes,
        canonical_cells,
        np.vstack(snapshots).astype(np.float64, copy=False),
    )


def _parse_fields(
    spec: dict[str, Any],
    state: _ConversionState,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    dict[str, np.ndarray],
    dict[str, str],
    dict[str, dict[str, str]],
]:
    solution_name = str(spec.get("solution_directory", ""))
    solution_root = _resolve_within(
        state.native_root,
        solution_name,
        error_code="FIELD_SET_MISMATCH",
    )
    if not solution_root.is_dir():
        raise QPopConversionError("FIELD_SET_MISMATCH", "solution directory is missing")
    mesh_spec = spec.get("mesh")
    registry_spec = spec.get("field_registry")
    if not isinstance(mesh_spec, dict) or not isinstance(registry_spec, dict) or not registry_spec:
        raise QPopConversionError("FIELD_SET_MISMATCH", "mesh or field registry is absent")

    field_time: np.ndarray | None = None
    nodes: np.ndarray | None = None
    cells: np.ndarray | None = None
    fields: dict[str, np.ndarray] = {}
    units: dict[str, str] = {}
    registry: dict[str, dict[str, str]] = {}
    registry_keys = (
        "source_name",
        "physical_symbol",
        "quantity_label",
        "unit",
        "association",
        "temporal_kind",
        "qualification_status",
    )
    for canonical_name, entry_value in registry_spec.items():
        if not isinstance(entry_value, dict):
            raise QPopConversionError("FIELD_SET_MISMATCH", "field registry entry is invalid")
        try:
            pvd_name = str(entry_value["pvd"])
            source_name = str(entry_value["source_name"])
            entry = {key: str(entry_value[key]) for key in registry_keys}
        except KeyError as exc:
            raise QPopConversionError(
                "FIELD_SET_MISMATCH",
                f"field registry entry {canonical_name!r} is incomplete",
            ) from exc
        if entry["association"] != "point" or entry["temporal_kind"] != "dynamic":
            raise QPopConversionError(
                "FIELD_SET_MISMATCH",
                "G2 converter accepts only dynamic point fields",
            )
        pvd_path = _resolve_within(solution_root, pvd_name, error_code="FIELD_SET_MISMATCH")
        parsed_time, parsed_nodes, parsed_cells, values = _parse_dynamic_field(
            pvd_path=pvd_path,
            source_name=source_name,
            mesh_spec=mesh_spec,
            state=state,
            solution_root=solution_root,
        )
        if field_time is None:
            field_time = parsed_time
            nodes = parsed_nodes
            cells = parsed_cells
        elif not np.array_equal(parsed_time, field_time):
            raise QPopConversionError("FIELD_TIME_MISMATCH", "dynamic field times differ")
        elif not np.array_equal(parsed_nodes, nodes) or not np.array_equal(parsed_cells, cells):
            raise QPopConversionError(
                "MESH_TOPOLOGY_MISMATCH",
                "dynamic field meshes or topology differ",
            )
        fields[str(canonical_name)] = values
        units[str(canonical_name)] = entry["unit"]
        registry[str(canonical_name)] = entry
    assert field_time is not None and nodes is not None and cells is not None
    return field_time, nodes, cells, fields, units, registry


def _build_circuit(
    spec: dict[str, Any],
    native_log: _NativeLog,
) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, str]]:
    try:
        circuit_time = native_log.columns["time"].copy()
    except KeyError as exc:
        raise QPopConversionError("LOG_PROFILE_MISMATCH", "log profile has no time column") from exc
    registry = spec.get("circuit_registry")
    if not isinstance(registry, dict) or not registry:
        raise QPopConversionError("LOG_PROFILE_MISMATCH", "circuit registry is absent")
    circuit: dict[str, np.ndarray] = {}
    units: dict[str, str] = {}
    for canonical_name, entry_value in registry.items():
        if not isinstance(entry_value, dict):
            raise QPopConversionError("LOG_PROFILE_MISMATCH", "circuit registry entry is invalid")
        source_column = str(entry_value.get("source_column", ""))
        if source_column not in native_log.columns:
            raise QPopConversionError(
                "LOG_PROFILE_MISMATCH",
                f"circuit source column {source_column!r} is absent",
            )
        circuit[str(canonical_name)] = native_log.columns[source_column].copy()
        units[str(canonical_name)] = str(entry_value.get("unit", ""))
    return circuit_time, circuit, units


def _check_field_times_are_logged(
    field_time: np.ndarray,
    native_log: _NativeLog,
    spec: dict[str, Any],
) -> None:
    alignment = spec.get("field_log_alignment")
    if not isinstance(alignment, dict):
        raise QPopConversionError(
            "FIELD_TIME_MISMATCH",
            "field_log_alignment is absent from conversion spec",
        )
    rtol = float(alignment.get("rtol", -1.0))
    atol = float(alignment.get("atol", -1.0))
    saveperiod = int(alignment.get("auto_saveperiod", 0))
    if not (0.0 <= rtol <= 1.0e-5) or not (0.0 <= atol <= 1.0e-9) or saveperiod <= 0:
        raise QPopConversionError(
            "FIELD_TIME_MISMATCH",
            "invalid frozen field/log alignment tolerances or saveperiod",
        )
    circuit_time = native_log.columns["time"]
    steps = native_log.columns["step"]
    for value in field_time:
        matches = np.flatnonzero(np.isclose(circuit_time, value, rtol=rtol, atol=atol))
        if matches.size != 1:
            raise QPopConversionError(
                "FIELD_TIME_MISMATCH",
                f"field snapshot time {value!r} does not match exactly one log row",
            )
        step = int(steps[matches[0]])
        if (step - 1) % saveperiod != 0:
            raise QPopConversionError(
                "FIELD_TIME_MISMATCH",
                f"field snapshot at accepted step {step} violates frozen auto saveperiod",
            )


def _report_for_error(
    *,
    spec: dict[str, Any],
    error: QPopConversionError,
    consumed: dict[str, str],
    conversion_spec_sha256: str | None,
) -> QPopConversionReport:
    return QPopConversionReport(
        status="REJECTED",
        conversion_spec_id=str(spec.get("conversion_spec_id", "UNKNOWN")),
        case_id=str(spec.get("case_id", "UNKNOWN")),
        error_code=error.code,
        error_message=error.detail,
        artifact_sha256=None,
        conversion_spec_sha256=conversion_spec_sha256,
        field_snapshot_count=0,
        circuit_sample_count=0,
        node_count=0,
        cell_count=0,
        source_files=dict(sorted(consumed.items())),
    )


def _write_report(path: Path, report: QPopConversionReport) -> None:
    path.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _publish_rejection(
    *,
    working: Path,
    bundle: Path,
    report: QPopConversionReport,
) -> None:
    shutil.rmtree(working)
    working.mkdir()
    _write_report(working / "conversion_report.json", report)
    working.rename(bundle)


def convert_qpop_run(request: QPopConversionRequest) -> QPopConversionReport:
    """Convert one completed native Q-POP run into the canonical disk bundle."""

    native_root = Path(request.native_run_dir).resolve()
    spec_path = Path(request.conversion_spec_path).resolve()
    bundle = Path(request.bundle_dir).resolve()
    if bundle.exists():
        raise QPopConversionError("DESTINATION_EXISTS", f"bundle already exists: {bundle}")
    bundle.parent.mkdir(parents=True, exist_ok=True)
    spec: dict[str, Any] = {}
    conversion_spec_sha256: str | None = None
    state = _ConversionState(native_root=native_root)
    working = Path(tempfile.mkdtemp(prefix=f".{bundle.name}-", dir=bundle.parent))
    try:
        conversion_spec_sha256 = _sha256(spec_path)
        spec = _load_json(spec_path)
        if spec.get("schema_version") != "qpop-conversion-spec-v1":
            raise QPopConversionError(
                "SOURCE_IDENTITY_MISMATCH",
                "unsupported Q-POP conversion spec schema",
            )
        _validate_source_and_input(spec, spec_path, state)
        native_log = _parse_log(spec, state)
        field_time, nodes, cells, fields, field_units, field_registry = _parse_fields(
            spec,
            state,
        )
        circuit_time, circuit, circuit_units = _build_circuit(spec, native_log)
        _check_field_times_are_logged(field_time, native_log, spec)
        artifact = CaseArtifact(
            case_id=str(spec["case_id"]),
            physical_contract_id=str(spec["physical_contract_id"]),
            evidence_identity=str(spec["evidence_identity"]),
            nodes=nodes.astype(np.float64, copy=False),
            cells=cells.astype(np.int64, copy=False),
            mesh_unit=str(spec["mesh"]["coordinate_unit"]),
            field_time=field_time,
            circuit_time=circuit_time,
            time_unit=str(spec["time_unit"]),
            fields=fields,
            field_units=field_units,
            field_registry=field_registry,
            breakpoints=np.asarray(spec.get("protocol_breakpoints", []), dtype=np.float64),
            circuit=circuit,
            circuit_units=circuit_units,
        )
        artifact_path = working / "case.h5"
        artifact.write(artifact_path)
        CaseArtifact.read(artifact_path)
        artifact_sha256 = _sha256(artifact_path)
        report = QPopConversionReport(
            status="CONVERTED",
            conversion_spec_id=str(spec["conversion_spec_id"]),
            case_id=str(spec["case_id"]),
            error_code=None,
            error_message=None,
            artifact_sha256=artifact_sha256,
            conversion_spec_sha256=conversion_spec_sha256,
            field_snapshot_count=int(field_time.size),
            circuit_sample_count=int(circuit_time.size),
            node_count=int(nodes.shape[0]),
            cell_count=int(cells.shape[0]),
            source_files=dict(sorted(state.consumed.items())),
        )
        _write_report(working / "conversion_report.json", report)
        working.rename(bundle)
        return report
    except QPopConversionError as error:
        _publish_rejection(
            working=working,
            bundle=bundle,
            report=_report_for_error(
                spec=spec,
                error=error,
                consumed=state.consumed,
                conversion_spec_sha256=conversion_spec_sha256,
            ),
        )
        raise
    except ArtifactContractError as exc:
        error = QPopConversionError("ARTIFACT_VALIDATION_FAILED", str(exc))
        _publish_rejection(
            working=working,
            bundle=bundle,
            report=_report_for_error(
                spec=spec,
                error=error,
                consumed=state.consumed,
                conversion_spec_sha256=conversion_spec_sha256,
            ),
        )
        raise error from exc
    except OSError as exc:
        error = QPopConversionError("CONVERSION_INFRASTRUCTURE_ERROR", str(exc))
        _publish_rejection(
            working=working,
            bundle=bundle,
            report=_report_for_error(
                spec=spec,
                error=error,
                consumed=state.consumed,
                conversion_spec_sha256=conversion_spec_sha256,
            ),
        )
        raise error from exc
    except Exception as exc:
        error = QPopConversionError("INTERNAL_CONVERSION_ERROR", str(exc))
        _publish_rejection(
            working=working,
            bundle=bundle,
            report=_report_for_error(
                spec=spec,
                error=error,
                consumed=state.consumed,
                conversion_spec_sha256=conversion_spec_sha256,
            ),
        )
        raise error from exc
