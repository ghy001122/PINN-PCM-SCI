"""Conservative CPU oracle for the frozen ``SYN_EDT_2D_V1`` benchmark.

This module is the in-process seam for the synthetic axisymmetric
electrothermal defect-transport object.  It deliberately keeps mesh
construction, sparse assembly, nonlinear coupling, event evaluation, and
artifact conversion behind a small public interface.  Loading a frozen
contract or solving a non-scientific fixture is not scientific evidence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from enum import Enum
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from numpy.typing import NDArray
from scipy import sparse
from scipy.sparse.linalg import factorized, spsolve
from scipy.special import expit

from .artifacts import CaseArtifact


FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]

_ELECTRONVOLT_PER_KB_K = 8.617333262145e-5
_TWO_PI = 2.0 * math.pi
_LEVELS = ("coarse", "medium", "fine")


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"contract root must be an object: {path}")
    return value


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _json_finite_value(value: Any) -> Any:
    """Convert arrays/scalars recursively without emitting JSON NaN/Infinity."""

    if isinstance(value, Mapping):
        return {str(key): _json_finite_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_finite_value(item) for item in value]
    if isinstance(value, np.ndarray):
        return _json_finite_value(value.tolist())
    if isinstance(value, np.generic):
        return _json_finite_value(value.item())
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value


class SynEdtControl(str, Enum):
    """Frozen electrothermal ablation branch."""

    FULL = "FULL"
    DIRECT_T_TO_TRANSPORT_OFF = "DIRECT_T_TO_TRANSPORT_OFF"
    FULL_ISOTHERMAL_COUPLING_OFF = "FULL_ISOTHERMAL_COUPLING_OFF"


@dataclass(frozen=True)
class SynEdtPhysicalContract:
    """Validated frozen S0 physics and S2 numerical contracts."""

    s0_path: Path
    numerical_path: Path
    s0_sha256: str
    numerical_sha256: str
    s0: Mapping[str, Any]
    numerical: Mapping[str, Any]

    @classmethod
    def from_s0(
        cls,
        path: str | Path,
        numerical_path: str | Path | None = None,
    ) -> "SynEdtPhysicalContract":
        s0_path = Path(path).resolve()
        resolved_numerical = (
            Path(numerical_path).resolve()
            if numerical_path is not None
            else s0_path.with_name("s2_numerical_contract.json")
        )
        s0_bytes = s0_path.read_bytes()
        numerical_bytes = resolved_numerical.read_bytes()
        s0 = _read_json(s0_path)
        numerical = _read_json(resolved_numerical)
        s0_sha = _sha256_bytes(s0_bytes)
        numerical_sha = _sha256_bytes(numerical_bytes)

        physical = s0.get("synthetic_physical_contract", {})
        if physical.get("contract_id") != "SYN_EDT_2D_V1_PHYSICS_V1":
            raise ValueError("S0 does not contain the frozen SYN_EDT_2D_V1 physics contract")
        if numerical.get("physical_contract_id") != physical.get("contract_id"):
            raise ValueError("S0 and S2 physical contract identities differ")
        expected_sha = str(numerical.get("derived_from_s0_sha256", "")).upper()
        if expected_sha != s0_sha:
            raise ValueError(
                "S2 numerical contract was not derived from the supplied exact S0 bytes"
            )
        if numerical.get("discretization", {}).get("method") != (
            "CELL_CENTERED_MASKED_NONUNIFORM_FINITE_VOLUME"
        ):
            raise ValueError("unsupported SYN_EDT discretization")
        nondimensional = numerical.get("nondimensionalization", {})
        endpoint = numerical.get("endpoint_and_floor_contract", {})
        derived_current = (
            _TWO_PI
            * float(nondimensional.get("active_sigma_scale_s_m", math.nan))
            * float(nondimensional.get("length_m", math.nan))
            * float(nondimensional.get("thermal_voltage_v", math.nan))
        )
        declared_current = float(endpoint.get("characteristic_current_a", math.nan))
        if not (
            math.isfinite(derived_current)
            and math.isfinite(declared_current)
            and math.isclose(
                declared_current,
                derived_current,
                rel_tol=5.0e-14,
                abs_tol=0.0,
            )
        ):
            raise ValueError(
                "S2 characteristic current must equal "
                "2*pi*active_sigma_scale*length*thermal_voltage"
            )
        return cls(
            s0_path=s0_path,
            numerical_path=resolved_numerical,
            s0_sha256=s0_sha,
            numerical_sha256=numerical_sha,
            s0=s0,
            numerical=numerical,
        )

    @classmethod
    def from_files(
        cls,
        s0_path: str | Path,
        numerical_path: str | Path,
    ) -> "SynEdtPhysicalContract":
        """Compatibility alias for callers that name both frozen files."""

        return cls.from_s0(s0_path, numerical_path)

    @property
    def physical(self) -> Mapping[str, Any]:
        return self.s0["synthetic_physical_contract"]

    @property
    def physical_contract_id(self) -> str:
        return str(self.physical["contract_id"])

    @property
    def length_m(self) -> float:
        return float(self.numerical["nondimensionalization"]["length_m"])

    @property
    def time_s(self) -> float:
        return float(self.numerical["nondimensionalization"]["time_s"])

    @property
    def temperature_k(self) -> float:
        return float(self.numerical["nondimensionalization"]["temperature_k"])

    @property
    def thermal_voltage_v(self) -> float:
        return float(self.numerical["nondimensionalization"]["thermal_voltage_v"])


@dataclass(frozen=True)
class SynEdtResolution:
    """Frozen space/time level or an explicitly non-scientific fixture level."""

    space_level: str
    time_level: str
    active_h_max_nm: float
    corner_h_max_nm: float
    dt_max_s: float
    saved_field_interval_s: float
    non_scientific_fixture: bool = False

    @classmethod
    def from_levels(
        cls,
        space: str,
        time: str,
        contract: SynEdtPhysicalContract | None = None,
    ) -> "SynEdtResolution":
        if space not in _LEVELS or time not in _LEVELS:
            raise ValueError(f"space and time levels must be one of {_LEVELS}")
        if contract is None:
            spacing = {
                "coarse": {"active": 4.0, "contact_corner": 1.0},
                "medium": {"active": 2.0, "contact_corner": 0.5},
                "fine": {"active": 1.0, "contact_corner": 0.25},
            }
            dt = {"coarse": 0.005, "medium": 0.0025, "fine": 0.00125}
            saved = 0.0025
        else:
            disc = contract.numerical["discretization"]
            spacing = disc["level_max_spacing_nm"]
            dt = disc["level_dt_max_s"]
            saved = float(contract.numerical["saved_field_interval_s"])
        return cls(
            space_level=space,
            time_level=time,
            active_h_max_nm=float(spacing[space]["active"]),
            corner_h_max_nm=float(spacing[space]["contact_corner"]),
            dt_max_s=float(dt[time]),
            saved_field_interval_s=saved,
        )

    @classmethod
    def fixture(
        cls,
        *,
        active_h_max_nm: float = 20.0,
        corner_h_max_nm: float = 10.0,
        dt_max_s: float = 0.005,
        saved_field_interval_s: float | None = None,
    ) -> "SynEdtResolution":
        if min(active_h_max_nm, corner_h_max_nm, dt_max_s) <= 0.0:
            raise ValueError("fixture spacings and timestep must be positive")
        return cls(
            space_level="fixture",
            time_level="fixture",
            active_h_max_nm=float(active_h_max_nm),
            corner_h_max_nm=float(corner_h_max_nm),
            dt_max_s=float(dt_max_s),
            saved_field_interval_s=float(saved_field_interval_s or dt_max_s),
            non_scientific_fixture=True,
        )


@dataclass(frozen=True)
class SynEdtCaseSpec:
    """One complete waveform/history case; mesh and timestep are excluded."""

    qualification_id: str
    reset_v: float
    set_v: float
    cycles: int
    cycle_duration_s: float
    total_duration_s: float
    initial_y: float
    active_radius_nm: float
    active_height_nm: float
    contact_radius_nm: float
    history: str
    non_scientific_fixture: bool = False

    @classmethod
    def qualification(
        cls,
        case_id: str,
        contract: SynEdtPhysicalContract,
    ) -> "SynEdtCaseSpec":
        qualification = contract.physical["qualification_cases"]
        if case_id not in qualification:
            raise KeyError(f"unknown qualification case: {case_id}")
        entry = qualification[case_id]
        waveform = contract.physical["absolute_waveform"]
        geometry = contract.physical["domains_nm"]
        active = geometry["active_mixed_conductor"]
        contact = geometry["top_contact"]
        return cls(
            qualification_id=case_id,
            reset_v=float(entry["reset_v"]),
            set_v=float(entry["set_v"]),
            cycles=int(waveform["cycles"]),
            cycle_duration_s=float(waveform["cycle_duration_s"]),
            total_duration_s=float(waveform["total_duration_s"]),
            initial_y=float(contract.physical["initial_conditions"]["y"]),
            active_radius_nm=float(active["r"][1]),
            active_height_nm=float(active["z"][1] - active["z"][0]),
            contact_radius_nm=float(contact["r"][1]),
            history=str(contract.physical["initial_conditions"]["history"]),
        )

    @classmethod
    def from_qualification_id(
        cls,
        contract: SynEdtPhysicalContract,
        case_id: str,
    ) -> "SynEdtCaseSpec":
        return cls.qualification(case_id, contract)

    def as_fixture(self, *, total_duration_s: float) -> "SynEdtCaseSpec":
        if total_duration_s <= 0.0 or total_duration_s > self.total_duration_s:
            raise ValueError("fixture duration must be positive and no longer than the case")
        return replace(
            self,
            total_duration_s=float(total_duration_s),
            cycles=max(1, int(math.ceil(total_duration_s / self.cycle_duration_s))),
            history="NON_SCIENTIFIC_SHORT_FIXTURE_FRESH_STATE",
            non_scientific_fixture=True,
        )


def _case_definition(
    contract: SynEdtPhysicalContract,
    case: SynEdtCaseSpec,
    control: SynEdtControl,
) -> dict[str, Any]:
    return {
        "object": "SYN_EDT_2D_V1",
        "physical_contract_id": contract.physical_contract_id,
        "geometry_nm": {
            "active_radius": case.active_radius_nm,
            "active_height": case.active_height_nm,
            "top_contact_radius": case.contact_radius_nm,
            "bottom_electrode": contract.physical["domains_nm"]["bottom_electrode"],
            "top_contact": contract.physical["domains_nm"]["top_contact"],
        },
        "constitutive_branch": control.value,
        "initial_state": {"y": case.initial_y},
        "waveform": {
            "qualification_id": case.qualification_id,
            "reset_v": case.reset_v,
            "set_v": case.set_v,
            "cycles": case.cycles,
            "cycle_duration_s": case.cycle_duration_s,
            "total_duration_s": case.total_duration_s,
            "segments": contract.physical["absolute_waveform"]["segments_per_cycle"],
        },
        "history": case.history,
        "identity": (
            "NON_SCIENTIFIC_FIXTURE"
            if case.non_scientific_fixture
            else "FULLY_TRANSPARENT_SYNTHETIC"
        ),
    }


def canonical_syn_edt_case_identity(
    contract: SynEdtPhysicalContract,
    case: SynEdtCaseSpec,
    control: SynEdtControl = SynEdtControl.FULL,
    resolution: SynEdtResolution | None = None,
) -> str:
    """Return the immutable complete-case identity.

    ``resolution`` is accepted for caller compatibility but intentionally does
    not enter the hash: mesh and timestep are convergence levels, not cases.
    """

    del resolution
    digest = hashlib.sha256(_canonical_json(_case_definition(contract, case, control)))
    return f"sha256:{digest.hexdigest()}"


canonical_case_identity = canonical_syn_edt_case_identity


def build_syn_edt_case_manifest(
    contract: SynEdtPhysicalContract,
    numerical_contract_path: str | Path | None = None,
    *,
    case: SynEdtCaseSpec | None = None,
    resolution: SynEdtResolution | None = None,
    control: SynEdtControl = SynEdtControl.FULL,
) -> dict[str, Any]:
    if numerical_contract_path is not None:
        supplied = Path(numerical_contract_path).resolve()
        if _sha256_bytes(supplied.read_bytes()) != contract.numerical_sha256:
            raise ValueError("manifest numerical contract differs from the loaded contract")
    manifest: dict[str, Any] = {
        "schema_version": "syn-edt-case-manifest-v1",
        "goal_id": str(contract.s0["goal_id"]),
        "physical_contract_id": contract.physical_contract_id,
        "s0_sha256": contract.s0_sha256,
        "s2_numerical_sha256": contract.numerical_sha256,
        "claim_status": "IMPLEMENTATION_OR_EXECUTION_IDENTITY_NOT_SCIENTIFIC_EVIDENCE",
        "cases": [
            {
                "qualification_case": qualification_id,
                "qualification_id": qualification_id,
                "pool": "Q",
                "role": entry["role"],
            }
            for qualification_id, entry in contract.physical["qualification_cases"].items()
        ],
    }
    if case is not None:
        manifest["case_definition"] = _case_definition(contract, case, control)
        manifest["case_id"] = canonical_syn_edt_case_identity(contract, case, control)
    if resolution is not None:
        manifest["resolution"] = asdict(resolution)
    return manifest


@dataclass(frozen=True)
class SynEdtEventReport:
    applicable: bool
    passed: bool
    peak_roi_depletion: tuple[float, ...] = ()
    event_time_s: tuple[float | None, ...] = ()
    recovery_fraction: tuple[float, ...] = ()
    adjacent_annulus_relative_depletion: tuple[float, ...] = ()
    depleted_thickness_fraction: tuple[float, ...] = ()
    partial_coverage_fraction: tuple[float, ...] = ()
    cycle_relative_drift: float = 0.0
    port_response_pass: bool = True
    failures: tuple[str, ...] = ()


@dataclass(frozen=True)
class SynEdtGuardReport:
    passed: bool
    relative_mass_drift_max: float
    relative_terminal_current_mismatch_max: float
    y_min: float
    y_max: float
    temperature_min_k: float
    temperature_max_k: float
    relative_heat_balance_residual_max: float
    no_flux_residual_max: float
    port_sign_pass: bool
    heat_balance_applicable: bool = True
    failures: tuple[str, ...] = ()


@dataclass(frozen=True)
class SynEdtConvergenceReport:
    passed: bool
    field_l2: float | None
    event_magnitude_relative: float | None
    event_time_absolute_s: float | None
    peak_current_relative: float | None
    peak_temperature_relative: float | None
    failures: tuple[str, ...] = ()
    component_deltas_by_cycle: tuple[tuple[float | None, ...], ...] = ()
    thermal_component_deltas_by_cycle: tuple[tuple[float | None, ...], ...] = ()
    thermal_effect_signed_by_cycle: Mapping[str, tuple[float | None, ...]] = field(
        default_factory=dict
    )
    thermal_current_rms_difference_a_by_cycle: tuple[float | None, ...] = ()


def split_syn_edt_face_joule_power(
    *,
    total_power: float,
    left_distance: float,
    right_distance: float,
    left_conductivity: float,
    right_conductivity: float,
) -> tuple[float, float]:
    """Split internal-face Joule heat by the two half-face resistances."""

    values = (
        total_power,
        left_distance,
        right_distance,
        left_conductivity,
        right_conductivity,
    )
    if not all(math.isfinite(float(value)) for value in values):
        raise ValueError("Joule partition inputs must be finite")
    if total_power < 0.0 or min(
        left_distance,
        right_distance,
        left_conductivity,
        right_conductivity,
    ) <= 0.0:
        raise ValueError("Joule power must be nonnegative and half-face data positive")
    left_resistance = left_distance / left_conductivity
    right_resistance = right_distance / right_conductivity
    total_resistance = left_resistance + right_resistance
    left = total_power * left_resistance / total_resistance
    return left, total_power - left


def reconstruct_syn_edt_cell_flux_from_faces(
    *,
    cell_bounds: FloatArray,
    internal_face_left: IntArray,
    internal_face_right: IntArray,
    internal_face_area: FloatArray,
    internal_face_orientation: Sequence[str],
    internal_face_flux_density: FloatArray,
) -> tuple[FloatArray, FloatArray]:
    """Area-weight face-normal samples into cell-centred ``(r, z)`` flux.

    Internal flux densities use the global positive coordinate direction for
    both incident cells.  The reconstruction denominator contains *all* four
    faces of every axisymmetric cell.  Omitted exterior faces therefore enter
    as the frozen zero-normal-flux boundary condition instead of disappearing
    from a boundary cell's average.
    """

    bounds = np.asarray(cell_bounds, dtype=np.float64)
    left = np.asarray(internal_face_left, dtype=np.int64)
    right = np.asarray(internal_face_right, dtype=np.int64)
    area = np.asarray(internal_face_area, dtype=np.float64)
    density = np.asarray(internal_face_flux_density, dtype=np.float64)
    orientations = tuple(str(value) for value in internal_face_orientation)
    if bounds.ndim != 2 or bounds.shape[1] != 4 or bounds.shape[0] == 0:
        raise ValueError("cell_bounds must have shape (n_cells, 4)")
    face_count = left.size
    if not (
        left.ndim == right.ndim == area.ndim == density.ndim == 1
        and right.size == area.size == density.size == len(orientations) == face_count
    ):
        raise ValueError("internal face arrays must be one-dimensional and equal length")
    if not np.all(np.isfinite(bounds)):
        raise ValueError("cell bounds must be finite")
    r0, r1, z0, z1 = bounds.T
    if np.any(r0 < 0.0) or np.any(r1 <= r0) or np.any(z1 <= z0):
        raise ValueError("cell bounds must define positive axisymmetric cells")
    if face_count:
        if np.any(left < 0) or np.any(right < 0):
            raise ValueError("internal face cell indices must be nonnegative")
        if np.any(left >= bounds.shape[0]) or np.any(right >= bounds.shape[0]):
            raise ValueError("internal face cell index is out of range")
        if np.any(left == right):
            raise ValueError("an internal face must join distinct cells")
        if not np.all(np.isfinite(area)) or np.any(area <= 0.0):
            raise ValueError("internal face areas must be finite and positive")
        if not np.all(np.isfinite(density)):
            raise ValueError("internal face flux densities must be finite")
        if any(value not in {"r", "z"} for value in orientations):
            raise ValueError("internal face orientation must be 'r' or 'z'")

    radial_numerator = np.zeros(bounds.shape[0], dtype=np.float64)
    axial_numerator = np.zeros(bounds.shape[0], dtype=np.float64)
    for index, orientation in enumerate(orientations):
        target = radial_numerator if orientation == "r" else axial_numerator
        contribution = density[index] * area[index]
        target[left[index]] += contribution
        target[right[index]] += contribution

    # Two radial faces have areas r0*dz and r1*dz.  Two axial faces each
    # have area 0.5*(r1**2-r0**2); the common 2*pi factor cancels.
    radial_area = (r0 + r1) * (z1 - z0)
    axial_area = r1**2 - r0**2
    return radial_numerator / radial_area, axial_numerator / axial_area


@dataclass(frozen=True)
class SynEdtOracleResult:
    case_id: str
    qualification_id: str
    physical_contract_id: str
    control: SynEdtControl
    resolution: SynEdtResolution
    case_manifest: Mapping[str, Any]
    time_s: FloatArray
    field_time_s: FloatArray
    active_cell_centers_m: FloatArray
    active_cell_bounds_nm: FloatArray
    active_cell_volume_hat: FloatArray
    active_r_faces_nm: FloatArray
    active_z_faces_nm: FloatArray
    y: FloatArray
    potential_v: FloatArray
    temperature_k: FloatArray
    defect_flux_r_m_s: FloatArray
    defect_flux_z_m_s: FloatArray
    voltage_v: FloatArray
    current_top_a: FloatArray
    current_bottom_a: FloatArray
    joule_power_w: FloatArray
    heat_sink_power_w: FloatArray
    active_mass_hat: FloatArray
    roi_depletion: FloatArray
    annulus_depletion: FloatArray
    full_temperature_min_k: FloatArray
    full_temperature_max_k: FloatArray
    event_report: SynEdtEventReport
    guard_report: SynEdtGuardReport
    solver_statistics: Mapping[str, Any] = field(default_factory=dict)

    def to_report_dict(self) -> dict[str, Any]:
        payload = {
            "schema_version": "syn-edt-oracle-report-v1",
            "case_id": self.case_id,
            "qualification_id": self.qualification_id,
            "physical_contract_id": self.physical_contract_id,
            "control": self.control.value,
            "resolution": asdict(self.resolution),
            "case_manifest": dict(self.case_manifest),
            "event_report": asdict(self.event_report),
            "guard_report": asdict(self.guard_report),
            "solver_statistics": dict(self.solver_statistics),
            "active_r_faces_nm": self.active_r_faces_nm.tolist(),
            "active_z_faces_nm": self.active_z_faces_nm.tolist(),
            "field_time_s": self.field_time_s.tolist(),
            "aggregation_status": (
                "NON_SCIENTIFIC_FIXTURE"
                if self.resolution.non_scientific_fixture
                else "EXECUTED_NOT_YET_CONVERGENCE_ADJUDICATED"
            ),
        }
        return _json_finite_value(payload)


@dataclass(frozen=True)
class _Face:
    left: int
    right: int
    area_hat: float
    left_distance_hat: float
    right_distance_hat: float
    orientation: str


@dataclass(frozen=True)
class _BoundaryFace:
    cell: int
    area_hat: float
    distance_hat: float
    terminal: str


@dataclass(frozen=True)
class _StepStatistics:
    block_iterations: int
    transport_newton_iterations_total: int
    transport_newton_iterations_max: int
    final_consistency_evaluations: int
    final_transport_scaled_residual: float


@dataclass
class _Mesh:
    r_faces_nm: FloatArray
    z_faces_nm: FloatArray
    cell_id: IntArray
    domain: IntArray
    centers_hat: FloatArray
    bounds_nm: FloatArray
    volumes_hat: FloatArray
    internal_faces: tuple[_Face, ...]
    electrical_boundaries: tuple[_BoundaryFace, ...]
    thermal_boundaries: tuple[_BoundaryFace, ...]
    active_full: IntArray
    active_lookup: IntArray
    active_faces: tuple[_Face, ...]
    active_neighbors: tuple[tuple[int, ...], ...]
    active_top: IntArray
    active_r_faces_nm: FloatArray
    active_z_faces_nm: FloatArray


def _partition(a: float, b: float, maximum: float) -> list[float]:
    if b <= a:
        return [a]
    count = max(1, int(math.ceil((b - a) / maximum - 1.0e-12)))
    return np.linspace(a, b, count + 1, dtype=np.float64).tolist()


def _axis_faces(
    minimum: float,
    maximum: float,
    exact: Sequence[float],
    patch: tuple[float, float],
    base_h: float,
    patch_h: float,
) -> FloatArray:
    points = sorted(
        {
            float(minimum),
            float(maximum),
            *[float(x) for x in exact if minimum <= float(x) <= maximum],
            max(minimum, float(patch[0])),
            min(maximum, float(patch[1])),
        }
    )
    values: list[float] = [points[0]]
    for left, right in zip(points[:-1], points[1:]):
        midpoint = 0.5 * (left + right)
        spacing = patch_h if patch[0] <= midpoint <= patch[1] else base_h
        values.extend(_partition(left, right, spacing)[1:])
    result = np.asarray(values, dtype=np.float64)
    if np.any(np.diff(result) <= 0.0):
        raise RuntimeError("generated mesh faces are not strictly increasing")
    return result


def _build_mesh(
    contract: SynEdtPhysicalContract,
    case: SynEdtCaseSpec,
    resolution: SynEdtResolution,
) -> _Mesh:
    disc = contract.numerical["discretization"]
    exact = disc["exact_mesh_faces_nm"]
    patch = disc["contact_corner_refinement_patch_nm"]
    domains = contract.physical["domains_nm"]
    bottom = domains["bottom_electrode"]
    top = domains["top_contact"]
    z_min = float(bottom["z"][0])
    z_max = float(top["z"][1])
    r_faces = _axis_faces(
        0.0,
        case.active_radius_nm,
        exact["r"],
        (float(patch["r"][0]), float(patch["r"][1])),
        resolution.active_h_max_nm,
        resolution.corner_h_max_nm,
    )
    z_faces = _axis_faces(
        z_min,
        z_max,
        exact["z"],
        (float(patch["z"][0]), float(patch["z"][1])),
        resolution.active_h_max_nm,
        resolution.corner_h_max_nm,
    )
    nr = r_faces.size - 1
    nz = z_faces.size - 1
    domain_grid = np.zeros((nz, nr), dtype=np.int64)
    cell_id = np.full((nz, nr), -1, dtype=np.int64)
    centers: list[tuple[float, float]] = []
    bounds: list[tuple[float, float, float, float]] = []
    volumes: list[float] = []
    length_nm = contract.length_m * 1.0e9
    tolerance = 1.0e-10

    for iz in range(nz):
        z0, z1 = float(z_faces[iz]), float(z_faces[iz + 1])
        zc = 0.5 * (z0 + z1)
        for ir in range(nr):
            r0, r1 = float(r_faces[ir]), float(r_faces[ir + 1])
            rc = 0.5 * (r0 + r1)
            domain = 0
            if 0.0 - tolerance <= zc <= case.active_height_nm + tolerance:
                domain = 1
            elif float(bottom["z"][0]) - tolerance <= zc <= float(bottom["z"][1]) + tolerance:
                domain = 2
            elif (
                rc <= case.contact_radius_nm + tolerance
                and float(top["z"][0]) - tolerance <= zc <= float(top["z"][1]) + tolerance
            ):
                domain = 3
            if domain == 0:
                continue
            index = len(centers)
            domain_grid[iz, ir] = domain
            cell_id[iz, ir] = index
            centers.append((rc / length_nm, zc / length_nm))
            bounds.append((r0, r1, z0, z1))
            volumes.append(
                0.5
                * ((r1 / length_nm) ** 2 - (r0 / length_nm) ** 2)
                * ((z1 - z0) / length_nm)
            )

    internal: list[_Face] = []
    electrical_boundaries: list[_BoundaryFace] = []
    thermal_boundaries: list[_BoundaryFace] = []
    for iz in range(nz):
        for ir in range(nr):
            left_index = int(cell_id[iz, ir])
            if left_index < 0:
                continue
            r0, r1 = r_faces[ir] / length_nm, r_faces[ir + 1] / length_nm
            z0, z1 = z_faces[iz] / length_nm, z_faces[iz + 1] / length_nm
            if ir + 1 < nr:
                right_index = int(cell_id[iz, ir + 1])
                if right_index >= 0:
                    internal.append(
                        _Face(
                            left=left_index,
                            right=right_index,
                            area_hat=float(r1 * (z1 - z0)),
                            left_distance_hat=float(0.5 * (r1 - r0)),
                            right_distance_hat=float(
                                0.5
                                * (
                                    r_faces[ir + 2] / length_nm
                                    - r_faces[ir + 1] / length_nm
                                )
                            ),
                            orientation="r",
                        )
                    )
            if iz + 1 < nz:
                upper_index = int(cell_id[iz + 1, ir])
                if upper_index >= 0:
                    internal.append(
                        _Face(
                            left=left_index,
                            right=upper_index,
                            area_hat=float(0.5 * (r1**2 - r0**2)),
                            left_distance_hat=float(0.5 * (z1 - z0)),
                            right_distance_hat=float(
                                0.5
                                * (
                                    z_faces[iz + 2] / length_nm
                                    - z_faces[iz + 1] / length_nm
                                )
                            ),
                            orientation="z",
                        )
                    )

            domain = int(domain_grid[iz, ir])
            z0_nm, z1_nm = float(z_faces[iz]), float(z_faces[iz + 1])
            axial_area = float(0.5 * (r1**2 - r0**2))
            if domain == 2 and abs(z0_nm - z_min) <= tolerance:
                boundary = _BoundaryFace(
                    cell=left_index,
                    area_hat=axial_area,
                    distance_hat=float(0.5 * (z1 - z0)),
                    terminal="bottom",
                )
                electrical_boundaries.append(boundary)
                thermal_boundaries.append(boundary)
            if domain == 3 and abs(z1_nm - z_max) <= tolerance:
                boundary = _BoundaryFace(
                    cell=left_index,
                    area_hat=axial_area,
                    distance_hat=float(0.5 * (z1 - z0)),
                    terminal="top",
                )
                electrical_boundaries.append(boundary)
                thermal_boundaries.append(boundary)

    domain_flat = np.asarray(
        [domain_grid[iz, ir] for iz in range(nz) for ir in range(nr) if cell_id[iz, ir] >= 0],
        dtype=np.int64,
    )
    active_full = np.flatnonzero(domain_flat == 1).astype(np.int64)
    active_lookup = np.full(domain_flat.size, -1, dtype=np.int64)
    active_lookup[active_full] = np.arange(active_full.size, dtype=np.int64)
    active_faces: list[_Face] = []
    neighbors: list[list[int]] = [[] for _ in range(active_full.size)]
    for face in internal:
        ai = int(active_lookup[face.left])
        aj = int(active_lookup[face.right])
        if ai < 0 or aj < 0:
            continue
        active_face = replace(face, left=ai, right=aj)
        active_faces.append(active_face)
        neighbors[ai].append(aj)
        neighbors[aj].append(ai)
    bounds_array = np.asarray(bounds, dtype=np.float64)
    active_bounds = bounds_array[active_full]
    active_top = np.flatnonzero(
        np.isclose(active_bounds[:, 3], case.active_height_nm, atol=1.0e-10)
    ).astype(np.int64)
    active_z_faces = z_faces[(z_faces >= -tolerance) & (z_faces <= case.active_height_nm + tolerance)]

    return _Mesh(
        r_faces_nm=r_faces,
        z_faces_nm=z_faces,
        cell_id=cell_id,
        domain=domain_flat,
        centers_hat=np.asarray(centers, dtype=np.float64),
        bounds_nm=bounds_array,
        volumes_hat=np.asarray(volumes, dtype=np.float64),
        internal_faces=tuple(internal),
        electrical_boundaries=tuple(electrical_boundaries),
        thermal_boundaries=tuple(thermal_boundaries),
        active_full=active_full,
        active_lookup=active_lookup,
        active_faces=tuple(active_faces),
        active_neighbors=tuple(tuple(entry) for entry in neighbors),
        active_top=active_top,
        active_r_faces_nm=r_faces.copy(),
        active_z_faces_nm=active_z_faces.copy(),
    )


def _piecewise_voltage(case: SynEdtCaseSpec, time_s: float) -> float:
    if case.qualification_id == "Q0" or (case.reset_v == 0.0 and case.set_v == 0.0):
        return 0.0
    cycle = case.cycle_duration_s
    relative = time_s % cycle
    if time_s > 0.0 and math.isclose(relative, 0.0, abs_tol=1.0e-13):
        relative = 0.0
    if relative < 0.02:
        return case.reset_v * relative / 0.02
    if relative <= 0.32:
        return case.reset_v
    if relative < 0.36:
        return case.reset_v * (0.36 - relative) / 0.04
    if relative < 0.46:
        return 0.0
    if relative < 0.48:
        return case.set_v * (relative - 0.46) / 0.02
    if relative <= 0.78:
        return case.set_v
    if relative < 0.82:
        return case.set_v * (0.82 - relative) / 0.04
    return 0.0


def _waveform_breakpoints(case: SynEdtCaseSpec) -> FloatArray:
    relative = (0.02, 0.32, 0.36, 0.46, 0.48, 0.78, 0.82)
    values = [
        cycle * case.cycle_duration_s + point
        for cycle in range(case.cycles)
        for point in relative
        if cycle * case.cycle_duration_s + point < case.total_duration_s - 1.0e-13
    ]
    return np.asarray(values, dtype=np.float64)


def _time_axis(case: SynEdtCaseSpec, resolution: SynEdtResolution) -> FloatArray:
    knots = [0.0, case.total_duration_s]
    knots.extend(_waveform_breakpoints(case).tolist())
    for cycle in range(1, case.cycles):
        value = cycle * case.cycle_duration_s
        if value < case.total_duration_s:
            knots.append(value)
    knots = sorted(set(knots))
    values: list[float] = [0.0]
    for left, right in zip(knots[:-1], knots[1:]):
        count = max(1, int(math.ceil((right - left) / resolution.dt_max_s - 1.0e-12)))
        values.extend(np.linspace(left, right, count + 1, dtype=np.float64)[1:].tolist())
    return np.asarray(values, dtype=np.float64)


def _field_time_axis(case: SynEdtCaseSpec, resolution: SynEdtResolution) -> FloatArray:
    interval = resolution.saved_field_interval_s
    count = int(math.floor(case.total_duration_s / interval + 1.0e-12))
    values = np.arange(count + 1, dtype=np.float64) * interval
    if values[-1] < case.total_duration_s - 1.0e-12:
        values = np.append(values, case.total_duration_s)
    else:
        values[-1] = case.total_duration_s
    return values


def _stable_logit(y: FloatArray) -> FloatArray:
    if np.any((y <= 0.0) | (y >= 1.0)):
        raise RuntimeError("logit state left the open lattice-gas interval")
    return np.log(y) - np.log1p(-y)


def _mobility_mean_and_derivatives(
    wi: FloatArray,
    wj: FloatArray,
) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray, FloatArray]:
    yi = expit(wi)
    yj = expit(wj)
    dw = wj - wi
    dy = yj - yi
    regular = np.abs(dw) >= 1.0e-6
    mobility = np.empty_like(dw)
    derivative_i = np.empty_like(dw)
    derivative_j = np.empty_like(dw)
    mobility[regular] = dy[regular] / dw[regular]
    mi = yi * (1.0 - yi)
    mj = yj * (1.0 - yj)
    derivative_i[regular] = (
        -mi[regular] * dw[regular] + dy[regular]
    ) / dw[regular] ** 2
    derivative_j[regular] = (
        mj[regular] * dw[regular] - dy[regular]
    ) / dw[regular] ** 2
    if np.any(~regular):
        wbar = 0.5 * (wi[~regular] + wj[~regular])
        ybar = expit(wbar)
        mbar = ybar * (1.0 - ybar)
        mobility[~regular] = mbar
        derivative = 0.5 * mbar * (1.0 - 2.0 * ybar)
        derivative_i[~regular] = derivative
        derivative_j[~regular] = derivative
    return yi, yj, mobility, derivative_i, derivative_j


class _OracleEngine:
    def __init__(
        self,
        contract: SynEdtPhysicalContract,
        case: SynEdtCaseSpec,
        resolution: SynEdtResolution,
        control: SynEdtControl,
    ) -> None:
        self.contract = contract
        self.case = case
        self.resolution = resolution
        self.control = control
        self.mesh = _build_mesh(contract, case, resolution)
        self.numerics = contract.numerical["nonlinear_scheme"]
        self.beta = float(contract.numerical["nondimensionalization"]["joule_heat_beta"])
        self.sigma_scale = float(
            contract.numerical["nondimensionalization"]["active_sigma_scale_s_m"]
        )
        self.k_scale = float(
            contract.numerical["nondimensionalization"][
                "active_thermal_conductivity_scale_w_m_k"
            ]
        )
        self.electrode_sigma_star = float(
            contract.physical["constitutive_laws"]["electrode_sigma_s_m"]
        ) / self.sigma_scale
        self.electrode_k_star = float(
            contract.physical["constitutive_laws"]["electrode_thermal_conductivity_w_m_k"]
        ) / self.k_scale
        kb_t0_ev = _ELECTRONVOLT_PER_KB_K * contract.temperature_k
        self.a_d = 0.18 / kb_t0_ev
        self.a_sigma = 0.04 / kb_t0_ev
        self.active_volumes = self.mesh.volumes_hat[self.mesh.active_full]
        self._face_i = np.asarray([f.left for f in self.mesh.active_faces], dtype=np.int64)
        self._face_j = np.asarray([f.right for f in self.mesh.active_faces], dtype=np.int64)
        self._face_area = np.asarray([f.area_hat for f in self.mesh.active_faces], dtype=np.float64)
        self._face_di = np.asarray(
            [f.left_distance_hat for f in self.mesh.active_faces], dtype=np.float64
        )
        self._face_dj = np.asarray(
            [f.right_distance_hat for f in self.mesh.active_faces], dtype=np.float64
        )
        self._face_orientation = tuple(f.orientation for f in self.mesh.active_faces)
        self._linear_solve_counts = {
            "electric": 0,
            "thermal": 0,
            "transport": 0,
        }
        self._thermal_matrix, self._thermal_rhs_base = self._assemble_thermal_matrix()
        self._thermal_solve = (
            None
            if self.control is SynEdtControl.FULL_ISOTHERMAL_COUPLING_OFF
            else factorized(self._thermal_matrix)
        )
        active_bounds = self.mesh.bounds_nm[self.mesh.active_full]
        roi = contract.physical["event_contract"]["roi_nm"]
        annulus = contract.numerical["event_evaluator"]["adjacent_annulus_nm"]
        self.roi_mask = (
            (active_bounds[:, 0] >= float(roi["r"][0]) - 1.0e-10)
            & (active_bounds[:, 1] <= float(roi["r"][1]) + 1.0e-10)
            & (active_bounds[:, 2] >= float(roi["z"][0]) - 1.0e-10)
            & (active_bounds[:, 3] <= float(roi["z"][1]) + 1.0e-10)
        )
        self.annulus_mask = (
            (active_bounds[:, 0] >= float(annulus["r_open_closed"][0]) - 1.0e-10)
            & (active_bounds[:, 1] <= float(annulus["r_open_closed"][1]) + 1.0e-10)
            & (active_bounds[:, 2] >= float(annulus["z_closed"][0]) - 1.0e-10)
            & (active_bounds[:, 3] <= float(annulus["z_closed"][1]) + 1.0e-10)
        )
        if not np.any(self.roi_mask) or not np.any(self.annulus_mask):
            raise RuntimeError("mesh does not resolve the frozen event ROI and annulus")

    @staticmethod
    def _conductance(face: _Face, coefficient: FloatArray) -> float:
        left = max(float(coefficient[face.left]), 1.0e-300)
        right = max(float(coefficient[face.right]), 1.0e-300)
        return face.area_hat / (
            face.left_distance_hat / left + face.right_distance_hat / right
        )

    def _conductivity(self, y: FloatArray, theta: FloatArray) -> FloatArray:
        coefficient = np.full(self.mesh.domain.size, self.electrode_sigma_star, dtype=np.float64)
        active_theta = theta[self.mesh.active_full]
        if self.control is SynEdtControl.FULL_ISOTHERMAL_COUPLING_OFF:
            active_theta = np.ones_like(active_theta)
        exponent = 2.0 * (y - 0.5) - self.a_sigma * (1.0 / active_theta - 1.0)
        coefficient[self.mesh.active_full] = np.exp(np.clip(exponent, -100.0, 100.0))
        return coefficient

    def _electric(
        self,
        y: FloatArray,
        theta: FloatArray,
        voltage_v: float,
    ) -> tuple[FloatArray, FloatArray, float, float, float, float]:
        coefficient = self._conductivity(y, theta)
        size = coefficient.size
        rows: list[int] = []
        columns: list[int] = []
        values: list[float] = []
        diagonal = np.zeros(size, dtype=np.float64)
        rhs = np.zeros(size, dtype=np.float64)
        conductances: list[float] = []
        for face in self.mesh.internal_faces:
            conductance = self._conductance(face, coefficient)
            conductances.append(conductance)
            diagonal[face.left] += conductance
            diagonal[face.right] += conductance
            rows.extend((face.left, face.right))
            columns.extend((face.right, face.left))
            values.extend((-conductance, -conductance))
        terminal_data: list[tuple[_BoundaryFace, float, float]] = []
        top_psi = voltage_v / self.contract.thermal_voltage_v
        for boundary in self.mesh.electrical_boundaries:
            value = top_psi if boundary.terminal == "top" else 0.0
            conductance = (
                boundary.area_hat
                * coefficient[boundary.cell]
                / boundary.distance_hat
            )
            diagonal[boundary.cell] += conductance
            rhs[boundary.cell] += conductance * value
            terminal_data.append((boundary, conductance, value))
        rows.extend(range(size))
        columns.extend(range(size))
        values.extend(diagonal.tolist())
        matrix = sparse.csc_matrix((values, (rows, columns)), shape=(size, size))
        self._linear_solve_counts["electric"] += 1
        psi = np.asarray(spsolve(matrix, rhs), dtype=np.float64)
        if not np.all(np.isfinite(psi)):
            raise RuntimeError("electric sparse solve returned non-finite values")
        residual = matrix @ psi - rhs
        residual_scale = max(float(np.max(np.abs(rhs))), 1.0)
        if float(np.max(np.abs(residual))) / residual_scale > float(
            self.numerics["linear_relative_residual_tolerance"]
        ):
            raise RuntimeError("electric sparse solve exceeded its frozen residual tolerance")

        joule_cell = np.zeros(size, dtype=np.float64)
        for face, conductance in zip(self.mesh.internal_faces, conductances):
            power = conductance * (psi[face.left] - psi[face.right]) ** 2
            left_power, right_power = split_syn_edt_face_joule_power(
                total_power=float(power),
                left_distance=face.left_distance_hat,
                right_distance=face.right_distance_hat,
                left_conductivity=float(coefficient[face.left]),
                right_conductivity=float(coefficient[face.right]),
            )
            joule_cell[face.left] += left_power
            joule_cell[face.right] += right_power
        current_top_hat = 0.0
        current_bottom_hat = 0.0
        for boundary, conductance, value in terminal_data:
            entering = conductance * (value - psi[boundary.cell])
            power = conductance * (value - psi[boundary.cell]) ** 2
            joule_cell[boundary.cell] += power
            if boundary.terminal == "top":
                current_top_hat += entering
            else:
                current_bottom_hat += entering
        return (
            psi,
            joule_cell,
            current_top_hat,
            current_bottom_hat,
            float(np.sum(joule_cell)),
            float(np.max(np.abs(residual)) / residual_scale),
        )

    def _assemble_thermal_matrix(self) -> tuple[sparse.csc_matrix, FloatArray]:
        coefficient = np.where(self.mesh.domain == 1, 1.0, self.electrode_k_star)
        size = coefficient.size
        rows: list[int] = []
        columns: list[int] = []
        values: list[float] = []
        diagonal = np.zeros(size, dtype=np.float64)
        rhs = np.zeros(size, dtype=np.float64)
        for face in self.mesh.internal_faces:
            conductance = self._conductance(face, coefficient)
            diagonal[face.left] += conductance
            diagonal[face.right] += conductance
            rows.extend((face.left, face.right))
            columns.extend((face.right, face.left))
            values.extend((-conductance, -conductance))
        for boundary in self.mesh.thermal_boundaries:
            conductance = (
                boundary.area_hat
                * coefficient[boundary.cell]
                / boundary.distance_hat
            )
            diagonal[boundary.cell] += conductance
            rhs[boundary.cell] += conductance
        rows.extend(range(size))
        columns.extend(range(size))
        values.extend(diagonal.tolist())
        return sparse.csc_matrix((values, (rows, columns)), shape=(size, size)), rhs

    def _thermal(self, joule_cell: FloatArray) -> tuple[FloatArray, float, float]:
        if self.control is SynEdtControl.FULL_ISOTHERMAL_COUPLING_OFF:
            return np.ones(self.mesh.domain.size, dtype=np.float64), 0.0, 0.0
        rhs = self._thermal_rhs_base + self.beta * joule_cell
        if self._thermal_solve is None:
            raise RuntimeError("thermal factorization is unavailable")
        self._linear_solve_counts["thermal"] += 1
        theta = np.asarray(self._thermal_solve(rhs), dtype=np.float64)
        if not np.all(np.isfinite(theta)):
            raise RuntimeError("thermal sparse solve returned non-finite values")
        residual = self._thermal_matrix @ theta - rhs
        residual_scale = max(float(np.max(np.abs(rhs))), 1.0)
        relative = float(np.max(np.abs(residual)) / residual_scale)
        if relative > float(self.numerics["linear_relative_residual_tolerance"]):
            raise RuntimeError("thermal sparse solve exceeded its frozen residual tolerance")
        sink_hat = self._thermal_sink(theta)
        return theta, sink_hat, relative

    def _thermal_sink(self, theta: FloatArray) -> float:
        if self.control is SynEdtControl.FULL_ISOTHERMAL_COUPLING_OFF:
            return 0.0
        coefficient = np.where(self.mesh.domain == 1, 1.0, self.electrode_k_star)
        sink_hat = 0.0
        for boundary in self.mesh.thermal_boundaries:
            conductance = (
                boundary.area_hat
                * coefficient[boundary.cell]
                / boundary.distance_hat
            )
            sink_hat += conductance * (theta[boundary.cell] - 1.0)
        return float(sink_hat)

    def _transport_coefficients(
        self,
        psi: FloatArray,
        theta: FloatArray,
    ) -> tuple[FloatArray, FloatArray]:
        active_theta = theta[self.mesh.active_full]
        if self.control is SynEdtControl.FULL:
            diffusion = np.exp(
                np.clip(-self.a_d * (1.0 / active_theta - 1.0), -100.0, 100.0)
            )
            theta_transport = active_theta
        else:
            diffusion = np.ones_like(active_theta)
            theta_transport = np.ones_like(active_theta)
        active_psi = psi[self.mesh.active_full]
        conductance = 1.0 / (
            self._face_di / diffusion[self._face_i]
            + self._face_dj / diffusion[self._face_j]
        )
        theta_face = 0.5 * (
            theta_transport[self._face_i] + theta_transport[self._face_j]
        )
        drive = (active_psi[self._face_j] - active_psi[self._face_i]) / theta_face
        return conductance, drive

    def _transport_system(
        self,
        w: FloatArray,
        y_old: FloatArray,
        dt_hat: float,
        conductance: FloatArray,
        drive: FloatArray,
        *,
        jacobian: bool,
    ) -> tuple[FloatArray, sparse.csc_matrix | None, float]:
        wi = w[self._face_i]
        wj = w[self._face_j]
        yi, yj, mobility, derivative_i, derivative_j = _mobility_mean_and_derivatives(
            wi, wj
        )
        y = expit(w)
        integrated_flux = -self._face_area * conductance * (
            (yj - yi) + mobility * drive
        )
        residual = self.active_volumes * (y - y_old) / dt_hat
        np.add.at(residual, self._face_i, integrated_flux)
        np.add.at(residual, self._face_j, -integrated_flux)
        scale = self.active_volumes / dt_hat
        face_scale = self._face_area * conductance * (1.0 + np.abs(drive))
        np.add.at(scale, self._face_i, face_scale)
        np.add.at(scale, self._face_j, face_scale)
        scaled = float(np.max(np.abs(residual) / np.maximum(scale, 1.0e-300)))
        if not jacobian:
            return residual, None, scaled

        mi = yi * (1.0 - yi)
        mj = yj * (1.0 - yj)
        derivative_flux_i = -self._face_area * conductance * (
            -mi + derivative_i * drive
        )
        derivative_flux_j = -self._face_area * conductance * (
            mj + derivative_j * drive
        )
        diagonal = self.active_volumes * y * (1.0 - y) / dt_hat
        rows = np.concatenate(
            (
                np.arange(y.size, dtype=np.int64),
                self._face_i,
                self._face_i,
                self._face_j,
                self._face_j,
            )
        )
        columns = np.concatenate(
            (
                np.arange(y.size, dtype=np.int64),
                self._face_i,
                self._face_j,
                self._face_i,
                self._face_j,
            )
        )
        values = np.concatenate(
            (
                diagonal,
                derivative_flux_i,
                derivative_flux_j,
                -derivative_flux_i,
                -derivative_flux_j,
            )
        )
        matrix = sparse.csc_matrix((values, (rows, columns)), shape=(y.size, y.size))
        return residual, matrix, scaled

    def _transport_newton(
        self,
        y_old: FloatArray,
        y_initial: FloatArray,
        psi: FloatArray,
        theta: FloatArray,
        dt_hat: float,
    ) -> tuple[FloatArray, int, float]:
        conductance, drive = self._transport_coefficients(psi, theta)
        w = _stable_logit(y_initial)
        tolerance = float(self.numerics["transport_scaled_residual_tolerance"])
        maximum = int(self.numerics["transport_newton_max_iterations"])
        initial_step = float(self.numerics["transport_newton_initial_step"])
        minimum_step = float(self.numerics["transport_newton_min_step"])
        for iteration in range(maximum + 1):
            residual, matrix, scaled = self._transport_system(
                w, y_old, dt_hat, conductance, drive, jacobian=True
            )
            if scaled <= tolerance:
                return expit(w), iteration, scaled
            if iteration == maximum or matrix is None:
                break
            self._linear_solve_counts["transport"] += 1
            delta = np.asarray(spsolve(matrix, -residual), dtype=np.float64)
            if not np.all(np.isfinite(delta)):
                raise RuntimeError("transport Newton direction is non-finite")
            step = initial_step
            accepted = False
            while step >= minimum_step - 1.0e-15:
                candidate = w + step * delta
                _, _, candidate_scaled = self._transport_system(
                    candidate,
                    y_old,
                    dt_hat,
                    conductance,
                    drive,
                    jacobian=False,
                )
                if candidate_scaled < scaled or candidate_scaled <= tolerance:
                    w = candidate
                    accepted = True
                    break
                step *= 0.5
            if not accepted:
                raise RuntimeError("transport Newton line search reached its frozen minimum step")
        raise RuntimeError("transport Newton exceeded its frozen iteration limit")

    def _transport_flux_cells(
        self,
        y: FloatArray,
        psi: FloatArray,
        theta: FloatArray,
    ) -> tuple[FloatArray, FloatArray]:
        conductance, drive = self._transport_coefficients(psi, theta)
        w = _stable_logit(y)
        yi, yj, mobility, _, _ = _mobility_mean_and_derivatives(
            w[self._face_i], w[self._face_j]
        )
        density = -conductance * ((yj - yi) + mobility * drive)
        length_nm = self.contract.length_m * 1.0e9
        active_bounds_hat = (
            self.mesh.bounds_nm[self.mesh.active_full] / length_nm
        )
        radial, axial = reconstruct_syn_edt_cell_flux_from_faces(
            cell_bounds=active_bounds_hat,
            internal_face_left=self._face_i,
            internal_face_right=self._face_j,
            internal_face_area=self._face_area,
            internal_face_orientation=self._face_orientation,
            internal_face_flux_density=density,
        )
        physical_scale = float(
            self.contract.physical["constitutive_laws"]["D0_m2_s"]
        ) / self.contract.length_m
        return radial * physical_scale, axial * physical_scale

    def coupled_step(
        self,
        y_old: FloatArray,
        theta_previous: FloatArray,
        voltage_v: float,
        dt_s: float,
    ) -> tuple[
        FloatArray,
        FloatArray,
        FloatArray,
        float,
        float,
        float,
        float,
        _StepStatistics,
    ]:
        relaxation = float(self.numerics["block_relaxation"])
        maximum = int(self.numerics["block_max_iterations"])
        change_tolerance = float(self.numerics["block_relative_change_tolerance"])
        residual_tolerance = float(self.numerics["block_scaled_residual_tolerance"])
        y_iter = y_old.copy()
        theta_iter = (
            np.ones_like(theta_previous)
            if self.control is SynEdtControl.FULL_ISOTHERMAL_COUPLING_OFF
            else theta_previous.copy()
        )
        psi_iter = np.zeros_like(theta_iter)
        last_newton = 0
        last_residual = math.inf
        newton_total = 0
        newton_max = 0
        consistency_evaluations = 0
        final_residual = math.inf
        final_electric: tuple[FloatArray, float, float, float] | None = None
        dt_hat = dt_s / self.contract.time_s
        for block in range(1, maximum + 1):
            psi_target, joule, _, _, _, _ = self._electric(
                y_iter, theta_iter, voltage_v
            )
            theta_target, _, _ = self._thermal(joule)
            theta_new = (
                theta_target
                if self.control is SynEdtControl.FULL_ISOTHERMAL_COUPLING_OFF
                else (1.0 - relaxation) * theta_iter + relaxation * theta_target
            )
            y_target, last_newton, last_residual = self._transport_newton(
                y_old, y_iter, psi_target, theta_new, dt_hat
            )
            newton_total += last_newton
            newton_max = max(newton_max, last_newton)
            w_new = (1.0 - relaxation) * _stable_logit(y_iter) + relaxation * _stable_logit(
                y_target
            )
            y_new = expit(w_new)
            change = max(
                float(np.max(np.abs(y_new - y_iter)) / 0.5),
                float(
                    np.max(np.abs(theta_new - theta_iter))
                    / max(float(np.max(np.abs(theta_new))), 1.0)
                ),
                float(
                    np.max(np.abs(psi_target - psi_iter))
                    / max(float(np.max(np.abs(psi_target))), 1.0)
                ),
            )
            y_iter = y_new
            theta_iter = theta_new
            psi_iter = psi_target
            if change <= change_tolerance and last_residual <= residual_tolerance:
                (
                    psi_check,
                    _,
                    current_top_check,
                    current_bottom_check,
                    joule_hat_check,
                    _,
                ) = self._electric(y_iter, theta_iter, voltage_v)
                consistency_evaluations += 1
                conductance, drive = self._transport_coefficients(
                    psi_check, theta_iter
                )
                _, _, final_residual = self._transport_system(
                    _stable_logit(y_iter),
                    y_old,
                    dt_hat,
                    conductance,
                    drive,
                    jacobian=False,
                )
                if final_residual <= residual_tolerance:
                    final_electric = (
                        psi_check,
                        current_top_check,
                        current_bottom_check,
                        joule_hat_check,
                    )
                    break
                psi_iter = psi_check
        else:
            if math.isfinite(final_residual):
                raise RuntimeError(
                    "final relaxed transport residual exceeded the frozen block "
                    f"tolerance: {final_residual:.17g} > {residual_tolerance:.17g}"
                )
            raise RuntimeError(
                "electrothermal-transport block exceeded its frozen iteration limit"
            )

        if final_electric is None or final_residual > residual_tolerance:
            raise RuntimeError("final relaxed transport state was not accepted")
        psi, current_top, current_bottom, joule_hat = final_electric
        sink_hat = self._thermal_sink(theta_iter)
        return (
            y_iter,
            psi,
            theta_iter,
            current_top,
            current_bottom,
            joule_hat,
            sink_hat,
            _StepStatistics(
                block_iterations=block,
                transport_newton_iterations_total=newton_total,
                transport_newton_iterations_max=newton_max,
                final_consistency_evaluations=consistency_evaluations,
                final_transport_scaled_residual=final_residual,
            ),
        )


def _weighted_mean(values: FloatArray, weights: FloatArray, mask: NDArray[np.bool_]) -> float:
    selected = weights[mask]
    return float(np.sum(values[mask] * selected) / np.sum(selected))


def _connected_component_metrics(
    engine: _OracleEngine,
    depletion: FloatArray,
    peak_mean: float,
) -> tuple[float, float]:
    if peak_mean <= 0.0:
        return 0.0, 0.0
    mask = depletion >= 0.5 * peak_mean
    seeds = [int(index) for index in engine.mesh.active_top if mask[int(index)]]
    if not seeds:
        return 0.0, 0.0
    visited: set[int] = set(seeds)
    stack = seeds.copy()
    while stack:
        current = stack.pop()
        for neighbor in engine.mesh.active_neighbors[current]:
            if mask[neighbor] and neighbor not in visited:
                visited.add(neighbor)
                stack.append(neighbor)
    indices = np.asarray(sorted(visited), dtype=np.int64)
    coverage = float(
        np.sum(engine.active_volumes[indices]) / np.sum(engine.active_volumes)
    )
    active_bounds = engine.mesh.bounds_nm[engine.mesh.active_full]
    minimum_z = float(np.min(active_bounds[indices, 2]))
    thickness = (engine.case.active_height_nm - minimum_z) / engine.case.active_height_nm
    return thickness, coverage


def _first_upward_crossing(
    time: FloatArray,
    value: FloatArray,
    threshold: float,
) -> float | None:
    for index in range(1, time.size):
        if value[index - 1] < threshold <= value[index]:
            denominator = value[index] - value[index - 1]
            if abs(denominator) <= 1.0e-30:
                return float(time[index])
            fraction = (threshold - value[index - 1]) / denominator
            return float(time[index - 1] + fraction * (time[index] - time[index - 1]))
    return None


def _event_report(
    engine: _OracleEngine,
    field_time_s: FloatArray,
    field_y: FloatArray,
    circuit_time_s: FloatArray,
    voltage_v: FloatArray,
    current_top_a: FloatArray,
) -> SynEdtEventReport:
    case = engine.case
    is_fixture = case.non_scientific_fixture or engine.resolution.non_scientific_fixture
    if case.qualification_id == "Q0" or is_fixture:
        return SynEdtEventReport(applicable=False, passed=True)
    frozen = engine.contract.physical["event_contract"]
    coverage_range = engine.contract.numerical["event_evaluator"][
        "partial_coverage_fraction_range"
    ]
    peak_range = frozen["peak_roi_depletion_range"]
    thickness_range = frozen["connected_depleted_thickness_fraction_range"]
    recovery_min = float(frozen["recovery_fraction_min"])
    annulus_max = float(frozen["adjacent_annulus_relative_depletion_max"])
    failures: list[str] = []
    peaks: list[float] = []
    event_times: list[float | None] = []
    recovery: list[float] = []
    annulus_relative: list[float] = []
    thicknesses: list[float] = []
    coverage: list[float] = []
    port_pass = True
    tolerance = 1.0e-11

    for cycle in range(case.cycles):
        start = cycle * case.cycle_duration_s
        end = min(start + case.cycle_duration_s, case.total_duration_s)
        if end < start + case.cycle_duration_s - tolerance:
            failures.append(f"cycle_{cycle + 1}_incomplete")
            continue
        pre_index = int(np.argmin(np.abs(field_time_s - start)))
        pre = field_y[pre_index]
        all_selector = (field_time_s >= start - tolerance) & (
            field_time_s <= end + tolerance
        )
        all_time = field_time_s[all_selector]
        all_y = field_y[all_selector]
        all_roi = np.asarray(
            [
                _weighted_mean((pre - state) / 0.5, engine.active_volumes, engine.roi_mask)
                for state in all_y
            ],
            dtype=np.float64,
        )
        search_selector = all_time <= start + 0.46 + tolerance
        search_time = all_time[search_selector]
        search_roi = all_roi[search_selector]
        search_y = all_y[search_selector]
        peak_index = int(np.argmax(search_roi))
        peak = float(search_roi[peak_index])
        peak_state = search_y[peak_index]
        peaks.append(peak)
        event_times.append(_first_upward_crossing(search_time, search_roi, 0.12))
        end_depletion = float(np.interp(end, all_time, all_roi))
        recovery_value = (
            (peak - end_depletion) / peak if peak > 1.0e-30 else -math.inf
        )
        recovery.append(recovery_value)
        local = (pre - peak_state) / 0.5
        annulus = _weighted_mean(local, engine.active_volumes, engine.annulus_mask)
        annulus_relative.append(annulus / peak if peak > 1.0e-30 else math.inf)
        thickness, fraction = _connected_component_metrics(engine, local, peak)
        thicknesses.append(thickness)
        coverage.append(fraction)

        if not (float(peak_range[0]) <= peak <= float(peak_range[1])):
            failures.append(f"cycle_{cycle + 1}_peak_depletion")
        if event_times[-1] is None:
            failures.append(f"cycle_{cycle + 1}_event_time")
        if recovery[-1] < recovery_min:
            failures.append(f"cycle_{cycle + 1}_recovery")
        if annulus_relative[-1] > annulus_max:
            failures.append(f"cycle_{cycle + 1}_localization")
        if not (float(thickness_range[0]) <= thicknesses[-1] <= float(thickness_range[1])):
            failures.append(f"cycle_{cycle + 1}_depleted_thickness")
        if not (float(coverage_range[0]) <= coverage[-1] <= float(coverage_range[1])):
            failures.append(f"cycle_{cycle + 1}_partial_coverage")

        positive = (
            (circuit_time_s >= start + 0.02 - tolerance)
            & (circuit_time_s <= start + 0.32 + tolerance)
        )
        negative = (
            (circuit_time_s >= start + 0.48 - tolerance)
            & (circuit_time_s <= start + 0.78 + tolerance)
        )
        if not np.any(positive) or np.any(current_top_a[positive] <= 0.0):
            port_pass = False
        if not np.any(negative) or np.any(current_top_a[negative] >= 0.0):
            port_pass = False
        start_index = int(np.argmin(np.abs(circuit_time_s - (start + 0.02))))
        hold_end_index = int(np.argmin(np.abs(circuit_time_s - (start + 0.32))))
        g_start = current_top_a[start_index] / max(abs(voltage_v[start_index]), 1.0e-300)
        g_end = current_top_a[hold_end_index] / max(abs(voltage_v[hold_end_index]), 1.0e-300)
        relative_drop = (g_start - g_end) / max(abs(g_start), 1.0e-300)
        if relative_drop < 0.01:
            port_pass = False

    drift = 0.0
    if len(peaks) >= 2:
        drift = abs(peaks[1] - peaks[0]) / max(abs(peaks[0]), abs(peaks[1]), 1.0e-300)
        if drift > float(frozen["cycle_relative_drift_max"]):
            failures.append("cycle_relative_drift")
    if not port_pass:
        failures.append("port_response")
    return SynEdtEventReport(
        applicable=True,
        passed=not failures,
        peak_roi_depletion=tuple(peaks),
        event_time_s=tuple(event_times),
        recovery_fraction=tuple(recovery),
        adjacent_annulus_relative_depletion=tuple(annulus_relative),
        depleted_thickness_fraction=tuple(thicknesses),
        partial_coverage_fraction=tuple(coverage),
        cycle_relative_drift=drift,
        port_response_pass=port_pass,
        failures=tuple(failures),
    )


def _guard_report(
    contract: SynEdtPhysicalContract,
    *,
    control: SynEdtControl,
    mass: FloatArray,
    current_top_hat: FloatArray,
    current_bottom_hat: FloatArray,
    y_minimum: FloatArray,
    y_maximum: FloatArray,
    temperature_minimum_k: FloatArray,
    temperature_maximum_k: FloatArray,
    joule_hat: FloatArray,
    sink_hat: FloatArray,
    theta_deviation: FloatArray,
    port_sign_pass: bool,
) -> SynEdtGuardReport:
    limits = contract.physical["physical_guards"]
    relative_mass = float(np.max(np.abs(mass - mass[0])) / max(abs(float(mass[0])), 1.0e-300))
    mismatch = np.abs(current_top_hat + current_bottom_hat)
    current_scale = np.maximum(np.maximum(np.abs(current_top_hat), np.abs(current_bottom_hat)), 1.0e-300)
    mismatch = np.where(
        np.maximum(np.abs(current_top_hat), np.abs(current_bottom_hat)) <= 1.0e-24,
        0.0,
        mismatch / current_scale,
    )
    heat_applicable = control is not SynEdtControl.FULL_ISOTHERMAL_COUPLING_OFF
    heat_residual = np.zeros_like(joule_hat)
    if heat_applicable:
        driven = joule_hat > 1.0e-24
        heat_residual[driven] = np.abs(contract.numerical["nondimensionalization"]["joule_heat_beta"] * joule_hat[driven] - sink_hat[driven]) / np.maximum(
            contract.numerical["nondimensionalization"]["joule_heat_beta"] * joule_hat[driven],
            1.0e-300,
        )
        heat_residual[~driven] = np.where(
            theta_deviation[~driven] <= 1.0e-12,
            0.0,
            math.inf,
        )
    y_min = float(np.min(y_minimum))
    y_max = float(np.max(y_maximum))
    t_min = float(np.min(temperature_minimum_k))
    t_max = float(np.max(temperature_maximum_k))
    failures: list[str] = []
    if relative_mass > float(limits["relative_mass_drift_max"]):
        failures.append("mass")
    if float(np.max(mismatch)) > float(limits["relative_terminal_current_mismatch_max"]):
        failures.append("current")
    if y_min < float(limits["y_bounds"][0]) or y_max > float(limits["y_bounds"][1]):
        failures.append("state_bounds")
    if t_min < float(limits["temperature_k_bounds"][0]) or t_max > float(
        limits["temperature_k_bounds"][1]
    ):
        failures.append("temperature_bounds")
    if heat_applicable and float(np.max(heat_residual)) > float(
        limits["relative_heat_balance_residual_max"]
    ):
        failures.append("heat")
    if not port_sign_pass:
        failures.append("port_sign")
    return SynEdtGuardReport(
        passed=not failures,
        relative_mass_drift_max=relative_mass,
        relative_terminal_current_mismatch_max=float(np.max(mismatch)),
        y_min=y_min,
        y_max=y_max,
        temperature_min_k=t_min,
        temperature_max_k=t_max,
        relative_heat_balance_residual_max=float(np.max(heat_residual)),
        no_flux_residual_max=0.0,
        port_sign_pass=port_sign_pass,
        heat_balance_applicable=heat_applicable,
        failures=tuple(failures),
    )


class SynEdtOracleCase:
    """Deep in-process finite-volume oracle for one complete case."""

    def __init__(
        self,
        *,
        contract: SynEdtPhysicalContract,
        case: SynEdtCaseSpec,
        resolution: SynEdtResolution,
        control: SynEdtControl = SynEdtControl.FULL,
    ) -> None:
        if case.non_scientific_fixture != resolution.non_scientific_fixture:
            raise ValueError(
                "fixture case and fixture resolution must be paired so they cannot enter science"
            )
        self.contract = contract
        self.case = case
        self.resolution = resolution
        self.control = SynEdtControl(control)

    def solve(self) -> SynEdtOracleResult:
        engine = _OracleEngine(self.contract, self.case, self.resolution, self.control)
        time = _time_axis(self.case, self.resolution)
        field_time = _field_time_axis(self.case, self.resolution)
        active_size = engine.mesh.active_full.size
        y = np.full(active_size, self.case.initial_y, dtype=np.float64)
        theta = np.ones(engine.mesh.domain.size, dtype=np.float64)
        voltage = np.asarray([_piecewise_voltage(self.case, value) for value in time], dtype=np.float64)
        current_top_hat = np.zeros(time.size, dtype=np.float64)
        current_bottom_hat = np.zeros(time.size, dtype=np.float64)
        joule_hat = np.zeros(time.size, dtype=np.float64)
        sink_hat = np.zeros(time.size, dtype=np.float64)
        mass = np.zeros(time.size, dtype=np.float64)
        roi_trace = np.zeros(time.size, dtype=np.float64)
        annulus_trace = np.zeros(time.size, dtype=np.float64)
        temperature_minimum = np.zeros(time.size, dtype=np.float64)
        temperature_maximum = np.zeros(time.size, dtype=np.float64)
        theta_deviation = np.zeros(time.size, dtype=np.float64)
        y_minimum = np.zeros(time.size, dtype=np.float64)
        y_maximum = np.zeros(time.size, dtype=np.float64)
        pre_states: list[FloatArray | None] = [None] * self.case.cycles
        peak_states: list[FloatArray | None] = [None] * self.case.cycles
        peak_values = [-math.inf] * self.case.cycles
        solver_steps: list[_StepStatistics] = []

        psi, joule_cell, top_hat, bottom_hat, q_hat, _ = engine._electric(
            y, theta, float(voltage[0])
        )
        theta, h_hat, _ = engine._thermal(joule_cell)
        flux_r, flux_z = engine._transport_flux_cells(y, psi, theta)

        saved_y: list[FloatArray] = [y.copy()]
        saved_psi: list[FloatArray] = [psi[engine.mesh.active_full].copy()]
        saved_theta: list[FloatArray] = [theta[engine.mesh.active_full].copy()]
        saved_flux_r: list[FloatArray] = [flux_r.copy()]
        saved_flux_z: list[FloatArray] = [flux_z.copy()]
        next_field = 1

        def record(index: int, state: FloatArray, state_theta: FloatArray, top: float, bottom: float, q: float, h: float) -> None:
            current_top_hat[index] = top
            current_bottom_hat[index] = bottom
            joule_hat[index] = q
            sink_hat[index] = h
            mass[index] = float(np.sum(engine.active_volumes * state))
            y_minimum[index] = float(np.min(state))
            y_maximum[index] = float(np.max(state))
            temperature_minimum[index] = float(np.min(state_theta) * self.contract.temperature_k)
            temperature_maximum[index] = float(np.max(state_theta) * self.contract.temperature_k)
            theta_deviation[index] = float(np.max(np.abs(state_theta - 1.0)))
            if time[index] >= self.case.total_duration_s - 1.0e-12:
                cycle = self.case.cycles - 1
            else:
                cycle = min(
                    int(math.floor((time[index] + 1.0e-12) / self.case.cycle_duration_s)),
                    self.case.cycles - 1,
                )
            if pre_states[cycle] is None:
                pre_states[cycle] = state.copy()
            pre = pre_states[cycle]
            assert pre is not None
            local = (pre - state) / 0.5
            roi_trace[index] = _weighted_mean(local, engine.active_volumes, engine.roi_mask)
            annulus_trace[index] = _weighted_mean(
                local, engine.active_volumes, engine.annulus_mask
            )
            relative = time[index] - cycle * self.case.cycle_duration_s
            if relative <= 0.46 + 1.0e-12 and roi_trace[index] > peak_values[cycle]:
                peak_values[cycle] = float(roi_trace[index])
                peak_states[cycle] = state.copy()

        record(0, y, theta, top_hat, bottom_hat, q_hat, h_hat)
        previous_y = y.copy()
        previous_psi = psi.copy()
        previous_theta = theta.copy()
        previous_flux_r = flux_r.copy()
        previous_flux_z = flux_z.copy()

        for index in range(1, time.size):
            dt = float(time[index] - time[index - 1])
            y, psi, theta, top_hat, bottom_hat, q_hat, h_hat, step_statistics = engine.coupled_step(
                previous_y,
                previous_theta,
                float(voltage[index]),
                dt,
            )
            solver_steps.append(step_statistics)
            flux_r, flux_z = engine._transport_flux_cells(y, psi, theta)
            record(index, y, theta, top_hat, bottom_hat, q_hat, h_hat)
            while next_field < field_time.size and field_time[next_field] <= time[index] + 1.0e-12:
                fraction = (field_time[next_field] - time[index - 1]) / dt
                fraction = min(max(float(fraction), 0.0), 1.0)
                saved_y.append(previous_y + fraction * (y - previous_y))
                saved_psi.append(
                    previous_psi[engine.mesh.active_full]
                    + fraction
                    * (psi[engine.mesh.active_full] - previous_psi[engine.mesh.active_full])
                )
                saved_theta.append(
                    previous_theta[engine.mesh.active_full]
                    + fraction
                    * (theta[engine.mesh.active_full] - previous_theta[engine.mesh.active_full])
                )
                saved_flux_r.append(previous_flux_r + fraction * (flux_r - previous_flux_r))
                saved_flux_z.append(previous_flux_z + fraction * (flux_z - previous_flux_z))
                next_field += 1
            previous_y = y.copy()
            previous_psi = psi.copy()
            previous_theta = theta.copy()
            previous_flux_r = flux_r.copy()
            previous_flux_z = flux_z.copy()

        if next_field != field_time.size:
            raise RuntimeError("field output interpolation did not fill the frozen saved axis")
        event = _event_report(
            engine,
            field_time,
            np.asarray(saved_y, dtype=np.float64),
            time,
            voltage,
            current_top_hat
            * (_TWO_PI * engine.sigma_scale * self.contract.thermal_voltage_v * self.contract.length_m),
        )
        guard = _guard_report(
            self.contract,
            control=self.control,
            mass=mass,
            current_top_hat=current_top_hat,
            current_bottom_hat=current_bottom_hat,
            y_minimum=y_minimum,
            y_maximum=y_maximum,
            temperature_minimum_k=temperature_minimum,
            temperature_maximum_k=temperature_maximum,
            joule_hat=joule_hat,
            sink_hat=sink_hat,
            theta_deviation=theta_deviation,
            port_sign_pass=bool(
                np.all(
                    (
                        np.abs(voltage) <= 1.0e-15
                    )
                    | (current_top_hat * voltage > 0.0)
                )
            ),
        )
        current_scale = (
            _TWO_PI
            * engine.sigma_scale
            * self.contract.thermal_voltage_v
            * self.contract.length_m
        )
        joule_scale = (
            _TWO_PI
            * engine.sigma_scale
            * self.contract.thermal_voltage_v**2
            * self.contract.length_m
        )
        heat_scale = (
            _TWO_PI
            * engine.k_scale
            * self.contract.temperature_k
            * self.contract.length_m
        )
        active_bounds = engine.mesh.bounds_nm[engine.mesh.active_full]
        active_centers_m = engine.mesh.centers_hat[engine.mesh.active_full] * self.contract.length_m
        manifest = build_syn_edt_case_manifest(
            self.contract,
            case=self.case,
            resolution=self.resolution,
            control=self.control,
        )
        return SynEdtOracleResult(
            case_id=str(manifest["case_id"]),
            qualification_id=self.case.qualification_id,
            physical_contract_id=self.contract.physical_contract_id,
            control=self.control,
            resolution=self.resolution,
            case_manifest=manifest,
            time_s=time,
            field_time_s=field_time,
            active_cell_centers_m=active_centers_m,
            active_cell_bounds_nm=active_bounds,
            active_cell_volume_hat=engine.active_volumes.copy(),
            active_r_faces_nm=engine.mesh.active_r_faces_nm.copy(),
            active_z_faces_nm=engine.mesh.active_z_faces_nm.copy(),
            y=np.asarray(saved_y, dtype=np.float64),
            potential_v=np.asarray(saved_psi, dtype=np.float64)
            * self.contract.thermal_voltage_v,
            temperature_k=np.asarray(saved_theta, dtype=np.float64)
            * self.contract.temperature_k,
            defect_flux_r_m_s=np.asarray(saved_flux_r, dtype=np.float64),
            defect_flux_z_m_s=np.asarray(saved_flux_z, dtype=np.float64),
            voltage_v=voltage,
            current_top_a=current_top_hat * current_scale,
            current_bottom_a=current_bottom_hat * current_scale,
            joule_power_w=joule_hat * joule_scale,
            heat_sink_power_w=sink_hat * heat_scale,
            active_mass_hat=mass,
            roi_depletion=roi_trace,
            annulus_depletion=annulus_trace,
            full_temperature_min_k=temperature_minimum,
            full_temperature_max_k=temperature_maximum,
            event_report=event,
            guard_report=guard,
            solver_statistics={
                "timesteps": int(time.size - 1),
                "block_iterations_total": sum(
                    item.block_iterations for item in solver_steps
                ),
                "block_iterations_max": max(
                    (item.block_iterations for item in solver_steps), default=0
                ),
                "transport_newton_iterations_total": sum(
                    item.transport_newton_iterations_total for item in solver_steps
                ),
                "transport_newton_iterations_max": max(
                    (
                        item.transport_newton_iterations_max
                        for item in solver_steps
                    ),
                    default=0,
                ),
                "final_consistency_evaluations_total": sum(
                    item.final_consistency_evaluations for item in solver_steps
                ),
                "electric_linear_solves_total": engine._linear_solve_counts[
                    "electric"
                ],
                "thermal_linear_solves_total": engine._linear_solve_counts[
                    "thermal"
                ],
                "transport_linear_solves_total": engine._linear_solve_counts[
                    "transport"
                ],
                "linear_solves_total": sum(engine._linear_solve_counts.values()),
                "final_transport_scaled_residual_max": max(
                    (
                        item.final_transport_scaled_residual
                        for item in solver_steps
                    ),
                    default=0.0,
                ),
                "non_scientific_fixture": self.resolution.non_scientific_fixture,
            },
        )


def _field_registry(
    units: Mapping[str, str],
    qualification_status: str,
) -> dict[str, dict[str, str]]:
    symbols = {
        "defect_fraction_y": "y",
        "electric_potential": "phi",
        "temperature": "T",
        "defect_flux_r": "j_y_r",
        "defect_flux_z": "j_y_z",
    }
    return {
        name: {
            "source_name": name,
            "physical_symbol": symbols[name],
            "quantity_label": "SYN_EDT_2D_V1_ORACLE_FIELD",
            "unit": unit,
            "association": "axisymmetric_finite_volume_cell_center",
            "temporal_kind": "dynamic",
            "qualification_status": qualification_status,
        }
        for name, unit in units.items()
    }


def syn_edt_result_to_artifact(
    result: SynEdtOracleResult,
    contract: SynEdtPhysicalContract,
    case_id: str | None = None,
    qualification_status: str = "EXECUTED_NOT_YET_QUALIFIED",
) -> CaseArtifact:
    """Convert an in-memory oracle result to the canonical case artifact."""

    if result.physical_contract_id != contract.physical_contract_id:
        raise ValueError("result and contract physical identities differ")
    if result.resolution.non_scientific_fixture and "FIXTURE" not in qualification_status:
        raise ValueError("non-scientific fixture artifacts must be labelled as fixtures")
    units = {
        "defect_fraction_y": "1",
        "electric_potential": "V",
        "temperature": "K",
        "defect_flux_r": "m/s",
        "defect_flux_z": "m/s",
    }
    fields = {
        "defect_fraction_y": np.asarray(result.y, dtype=np.float64),
        "electric_potential": np.asarray(result.potential_v, dtype=np.float64),
        "temperature": np.asarray(result.temperature_k, dtype=np.float64),
        "defect_flux_r": np.asarray(result.defect_flux_r_m_s, dtype=np.float64),
        "defect_flux_z": np.asarray(result.defect_flux_z_m_s, dtype=np.float64),
    }
    circuit = {
        "voltage": np.asarray(result.voltage_v, dtype=np.float64),
        "current_top": np.asarray(result.current_top_a, dtype=np.float64),
        "current_bottom": np.asarray(result.current_bottom_a, dtype=np.float64),
        "joule_power": np.asarray(result.joule_power_w, dtype=np.float64),
        "heat_sink_power": np.asarray(result.heat_sink_power_w, dtype=np.float64),
        "active_mass_hat": np.asarray(result.active_mass_hat, dtype=np.float64),
        "roi_depletion": np.asarray(result.roi_depletion, dtype=np.float64),
        "annulus_depletion": np.asarray(result.annulus_depletion, dtype=np.float64),
        "temperature_min": np.asarray(result.full_temperature_min_k, dtype=np.float64),
        "temperature_max": np.asarray(result.full_temperature_max_k, dtype=np.float64),
    }
    circuit_units = {
        "voltage": "V",
        "current_top": "A",
        "current_bottom": "A",
        "joule_power": "W",
        "heat_sink_power": "W",
        "active_mass_hat": "1",
        "roi_depletion": "1",
        "annulus_depletion": "1",
        "temperature_min": "K",
        "temperature_max": "K",
    }
    waveform = result.case_manifest["case_definition"]["waveform"]
    breakpoints = [
        cycle * float(waveform["cycle_duration_s"]) + float(segment[1])
        for cycle in range(int(waveform["cycles"]))
        for segment in waveform["segments"][:-1]
        if cycle * float(waveform["cycle_duration_s"]) + float(segment[1])
        < float(waveform["total_duration_s"]) - 1.0e-13
    ]
    nodes = np.asarray(result.active_cell_centers_m, dtype=np.float64)
    cells = np.arange(nodes.shape[0], dtype=np.int64).reshape((-1, 1))
    return CaseArtifact(
        case_id=case_id or result.case_id,
        physical_contract_id=result.physical_contract_id,
        evidence_identity=qualification_status,
        nodes=nodes,
        cells=cells,
        mesh_unit="m",
        field_time=np.asarray(result.field_time_s, dtype=np.float64),
        circuit_time=np.asarray(result.time_s, dtype=np.float64),
        time_unit="s",
        fields=fields,
        field_units=units,
        field_registry=_field_registry(units, qualification_status),
        breakpoints=np.asarray(sorted(set(breakpoints)), dtype=np.float64),
        circuit=circuit,
        circuit_units=circuit_units,
    )


def _overlap_projection(
    coarse_bounds: FloatArray,
    fine_bounds: FloatArray,
) -> sparse.csr_matrix:
    rows: list[int] = []
    columns: list[int] = []
    values: list[float] = []
    for row, coarse in enumerate(coarse_bounds):
        radial_low = np.maximum(coarse[0], fine_bounds[:, 0])
        radial_high = np.minimum(coarse[1], fine_bounds[:, 1])
        axial_low = np.maximum(coarse[2], fine_bounds[:, 2])
        axial_high = np.minimum(coarse[3], fine_bounds[:, 3])
        overlap = (
            0.5
            * np.maximum(radial_high**2 - radial_low**2, 0.0)
            * np.maximum(axial_high - axial_low, 0.0)
        )
        indices = np.flatnonzero(overlap > 0.0)
        total = float(np.sum(overlap[indices]))
        if total <= 0.0:
            raise ValueError("fine mesh does not cover a coarse active cell")
        rows.extend([row] * indices.size)
        columns.extend(indices.tolist())
        values.extend((overlap[indices] / total).tolist())
    return sparse.csr_matrix(
        (values, (rows, columns)),
        shape=(coarse_bounds.shape[0], fine_bounds.shape[0]),
    )


def _interpolate_time(values: FloatArray, source: FloatArray, target: FloatArray) -> FloatArray:
    if target[0] < source[0] - 1.0e-12 or target[-1] > source[-1] + 1.0e-12:
        raise ValueError("reference time axis does not cover comparison times")
    right = np.searchsorted(source, target, side="left")
    right = np.clip(right, 0, source.size - 1)
    left = np.maximum(right - 1, 0)
    exact = np.isclose(source[right], target, atol=1.0e-13, rtol=0.0)
    left = np.where(exact, right, left)
    denominator = source[right] - source[left]
    weight = np.divide(
        target - source[left],
        denominator,
        out=np.zeros_like(target),
        where=np.abs(denominator) > 0.0,
    )
    return values[left] + weight[:, None] * (values[right] - values[left])


def _trapezoid_weights(time: FloatArray) -> FloatArray:
    if time.size == 1:
        return np.ones(1, dtype=np.float64)
    weights = np.zeros_like(time)
    increments = np.diff(time)
    weights[:-1] += 0.5 * increments
    weights[1:] += 0.5 * increments
    return weights


def _event_difference(
    coarse: SynEdtEventReport,
    fine: SynEdtEventReport,
) -> tuple[float, float]:
    if not coarse.applicable and not fine.applicable:
        return 0.0, 0.0
    if len(coarse.peak_roi_depletion) != len(fine.peak_roi_depletion):
        return math.inf, math.inf
    magnitude = max(
        (
            abs(left - right) / max(abs(right), 1.0e-300)
            for left, right in zip(coarse.peak_roi_depletion, fine.peak_roi_depletion)
        ),
        default=0.0,
    )
    event_time = 0.0
    for left, right in zip(coarse.event_time_s, fine.event_time_s):
        if left is None and right is None:
            continue
        if left is None or right is None:
            return magnitude, math.inf
        event_time = max(event_time, abs(left - right))
    return magnitude, event_time


def compare_syn_edt_resolutions(
    coarse: SynEdtOracleResult,
    fine: SynEdtOracleResult,
    contract: SynEdtPhysicalContract | None = None,
) -> SynEdtConvergenceReport:
    if coarse.physical_contract_id != fine.physical_contract_id:
        raise ValueError("cannot compare different physical contracts")
    if coarse.qualification_id != fine.qualification_id or coarse.control != fine.control:
        raise ValueError("convergence comparison requires the same complete case and control")
    projection = _overlap_projection(coarse.active_cell_bounds_nm, fine.active_cell_bounds_nm)
    fine_fields = (
        _interpolate_time(fine.y, fine.field_time_s, coarse.field_time_s),
        _interpolate_time(fine.potential_v, fine.field_time_s, coarse.field_time_s),
        _interpolate_time(fine.temperature_k, fine.field_time_s, coarse.field_time_s),
    )
    coarse_fields = (coarse.y, coarse.potential_v, coarse.temperature_k)
    scales = (
        _field_convergence_scales(contract)
        if contract is not None
        else (0.5, 0.18, 50.0)
    )
    volume = coarse.active_cell_volume_hat
    time_weight = _trapezoid_weights(coarse.field_time_s)
    mean_square: list[float] = []
    for coarse_field, fine_field, scale in zip(coarse_fields, fine_fields, scales):
        projected = np.asarray((projection @ fine_field.T).T, dtype=np.float64)
        error = (coarse_field - projected) / scale
        spatial = np.sum(error**2 * volume[None, :], axis=1) / np.sum(volume)
        mean_square.append(float(np.sum(spatial * time_weight) / np.sum(time_weight)))
    field_l2 = math.sqrt(float(np.mean(mean_square)))
    event_magnitude, event_time = _event_difference(coarse.event_report, fine.event_report)
    coarse_current = float(np.max(np.abs(coarse.current_top_a)))
    fine_current = float(np.max(np.abs(fine.current_top_a)))
    current_relative = abs(coarse_current - fine_current) / max(fine_current, 1.0e-300)
    coarse_rise = float(np.max(coarse.full_temperature_max_k) - 300.0)
    fine_rise = float(np.max(fine.full_temperature_max_k) - 300.0)
    temperature_relative = abs(coarse_rise - fine_rise) / max(abs(fine_rise), 1.0)
    loaded = contract
    convergence = (
        loaded.physical["convergence"]
        if loaded is not None
        else {
            "medium_fine_field_l2_max": 0.02,
            "medium_fine_event_magnitude_max": 0.03,
            "medium_fine_event_time_s_max": 0.0025,
            "medium_fine_peak_current_temperature_max": 0.02,
        }
    )
    failures: list[str] = []
    if field_l2 > float(convergence["medium_fine_field_l2_max"]):
        failures.append("field_l2")
    if event_magnitude > float(convergence["medium_fine_event_magnitude_max"]):
        failures.append("event_magnitude")
    if event_time > float(convergence["medium_fine_event_time_s_max"]):
        failures.append("event_time")
    peak_limit = float(convergence["medium_fine_peak_current_temperature_max"])
    if current_relative > peak_limit:
        failures.append("peak_current")
    if temperature_relative > peak_limit:
        failures.append("peak_temperature")
    return SynEdtConvergenceReport(
        passed=not failures,
        field_l2=field_l2,
        event_magnitude_relative=event_magnitude,
        event_time_absolute_s=event_time,
        peak_current_relative=current_relative,
        peak_temperature_relative=temperature_relative,
        failures=tuple(failures),
    )


def _bounds_from_report(report: Mapping[str, Any]) -> tuple[FloatArray, FloatArray]:
    r = np.asarray(report["active_r_faces_nm"], dtype=np.float64)
    z = np.asarray(report["active_z_faces_nm"], dtype=np.float64)
    bounds = np.asarray(
        [
            (r[ir], r[ir + 1], z[iz], z[iz + 1])
            for iz in range(z.size - 1)
            for ir in range(r.size - 1)
        ],
        dtype=np.float64,
    )
    volume = 0.5 * (bounds[:, 1] ** 2 - bounds[:, 0] ** 2) * (
        bounds[:, 3] - bounds[:, 2]
    )
    return bounds, volume


def _field_convergence_scales(
    contract: SynEdtPhysicalContract,
) -> tuple[float, float, float]:
    """Return the three frozen S2 field normalizers, failing closed."""

    try:
        fixed = contract.numerical["field_convergence_metric"]["fixed_scales"]
        scales = (
            float(fixed["defect_fraction"]),
            float(fixed["electric_potential_v"]),
            float(fixed["temperature_k"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("S2 lacks the frozen field convergence scales") from exc
    if not all(math.isfinite(value) and value > 0.0 for value in scales):
        raise ValueError("S2 field convergence scales must be finite and positive")
    return scales


def _time_space_rms(
    error: FloatArray,
    time: FloatArray,
    volume: FloatArray,
    mask: NDArray[np.bool_] | None = None,
) -> float:
    selected = np.ones(volume.size, dtype=bool) if mask is None else mask
    weights = volume[selected]
    spatial = np.sum(error[:, selected] ** 2 * weights[None, :], axis=1) / np.sum(weights)
    time_weight = _trapezoid_weights(time)
    return math.sqrt(float(np.sum(spatial * time_weight) / np.sum(time_weight)))


def _time_rms(error: FloatArray, time: FloatArray) -> float:
    weight = _trapezoid_weights(time)
    return math.sqrt(float(np.sum(error**2 * weight) / np.sum(weight)))


def _event_sequence(
    report: Mapping[str, Any],
    key: str,
    cycles: int,
) -> tuple[float | None, ...]:
    event = report.get("event_report")
    if not isinstance(event, Mapping):
        return tuple(None for _ in range(cycles))
    raw = event.get(key, ())
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return tuple(None for _ in range(cycles))
    values: list[float | None] = []
    for index in range(cycles):
        if index >= len(raw) or raw[index] is None:
            values.append(None)
        else:
            value = float(raw[index])
            values.append(value if math.isfinite(value) else None)
    return tuple(values)


def _persisted_component_deltas(
    coarse_artifact: CaseArtifact,
    fine_artifact: CaseArtifact,
    coarse_report: Mapping[str, Any],
    fine_report: Mapping[str, Any],
    contract: SynEdtPhysicalContract,
    coarse_bounds: FloatArray,
    coarse_volume: FloatArray,
    projection: sparse.csr_matrix,
) -> tuple[
    tuple[tuple[float | None, ...], ...],
    tuple[tuple[float | None, ...], ...],
    Mapping[str, tuple[float | None, ...]],
]:
    raise RuntimeError(
        "endpoint deltas are exclusively produced by "
        "syn_edt_evaluator.build_floor_seal"
    )
    cycles = int(contract.physical["absolute_waveform"]["cycles"])
    fine_y = _interpolate_time(
        fine_artifact.fields["defect_fraction_y"],
        fine_artifact.field_time,
        coarse_artifact.field_time,
    )
    fine_y = np.asarray((projection @ fine_y.T).T, dtype=np.float64)
    fine_flux_r = _interpolate_time(
        fine_artifact.fields["defect_flux_r"],
        fine_artifact.field_time,
        coarse_artifact.field_time,
    )
    fine_flux_z = _interpolate_time(
        fine_artifact.fields["defect_flux_z"],
        fine_artifact.field_time,
        coarse_artifact.field_time,
    )
    fine_flux_r = np.asarray((projection @ fine_flux_r.T).T, dtype=np.float64)
    fine_flux_z = np.asarray((projection @ fine_flux_z.T).T, dtype=np.float64)
    current_fine = _interpolate_time(
        fine_artifact.circuit["current_top"][:, None],
        fine_artifact.circuit_time,
        coarse_artifact.circuit_time,
    )[:, 0]
    peak_coarse = _event_sequence(coarse_report, "peak_roi_depletion", cycles)
    peak_fine = _event_sequence(fine_report, "peak_roi_depletion", cycles)
    event_coarse = _event_sequence(coarse_report, "event_time_s", cycles)
    event_fine = _event_sequence(fine_report, "event_time_s", cycles)
    thickness_coarse = _event_sequence(
        coarse_report, "depleted_thickness_fraction", cycles
    )
    thickness_fine = _event_sequence(fine_report, "depleted_thickness_fraction", cycles)
    recovery_coarse = _event_sequence(coarse_report, "recovery_fraction", cycles)
    recovery_fine = _event_sequence(fine_report, "recovery_fraction", cycles)
    roi = contract.physical["event_contract"]["roi_nm"]
    roi_mask = (
        (coarse_bounds[:, 0] >= float(roi["r"][0]) - 1.0e-10)
        & (coarse_bounds[:, 1] <= float(roi["r"][1]) + 1.0e-10)
        & (coarse_bounds[:, 2] >= float(roi["z"][0]) - 1.0e-10)
        & (coarse_bounds[:, 3] <= float(roi["z"][1]) + 1.0e-10)
    )
    endpoint = contract.numerical["endpoint_and_floor_contract"]
    current_floor = 1.0e-6 * float(endpoint["characteristic_current_a"])
    fraction_flux_floor = 0.01 * (
        float(contract.physical["constitutive_laws"]["D0_m2_s"])
        / contract.length_m
    )
    component_rows: list[tuple[float | None, ...]] = []
    thermal_rows: list[tuple[float | None, ...]] = []
    signed_peak: list[float | None] = []
    signed_event: list[float | None] = []
    current_effect: list[float | None] = []
    for cycle in range(cycles):
        start = cycle * float(contract.physical["absolute_waveform"]["cycle_duration_s"])
        end = start + float(contract.physical["absolute_waveform"]["cycle_duration_s"])
        field_selector = (
            (coarse_artifact.field_time >= start - 1.0e-12)
            & (coarse_artifact.field_time <= end + 1.0e-12)
        )
        circuit_selector = (
            (coarse_artifact.circuit_time >= start - 1.0e-12)
            & (coarse_artifact.circuit_time <= end + 1.0e-12)
        )
        field_axis = coarse_artifact.field_time[field_selector]
        circuit_axis = coarse_artifact.circuit_time[circuit_selector]
        roi_error = _time_space_rms(
            (
                coarse_artifact.fields["defect_fraction_y"][field_selector]
                - fine_y[field_selector]
            )
            / 0.5,
            field_axis,
            coarse_volume,
            roi_mask,
        )
        flux_difference = np.sqrt(
            (
                coarse_artifact.fields["defect_flux_r"][field_selector]
                - fine_flux_r[field_selector]
            )
            ** 2
            + (
                coarse_artifact.fields["defect_flux_z"][field_selector]
                - fine_flux_z[field_selector]
            )
            ** 2
        )
        oracle_flux = np.sqrt(
            fine_flux_r[field_selector] ** 2 + fine_flux_z[field_selector] ** 2
        )
        flux_normalizer = max(
            _time_space_rms(oracle_flux, field_axis, coarse_volume),
            fraction_flux_floor,
        )
        flux_error = _time_space_rms(
            flux_difference, field_axis, coarse_volume
        ) / flux_normalizer
        event_delta = (
            None
            if event_coarse[cycle] is None or event_fine[cycle] is None
            else abs(float(event_coarse[cycle]) - float(event_fine[cycle]))
        )
        thickness_delta = (
            None
            if thickness_coarse[cycle] is None or thickness_fine[cycle] is None
            else abs(float(thickness_coarse[cycle]) - float(thickness_fine[cycle]))
        )
        recovery_delta = (
            None
            if recovery_coarse[cycle] is None or recovery_fine[cycle] is None
            else abs(float(recovery_coarse[cycle]) - float(recovery_fine[cycle]))
        )
        fine_current_cycle = current_fine[circuit_selector]
        current_normalizer = max(_time_rms(fine_current_cycle, circuit_axis), current_floor)
        current_delta = _time_rms(
            coarse_artifact.circuit["current_top"][circuit_selector]
            - fine_current_cycle,
            circuit_axis,
        ) / current_normalizer
        component_rows.append(
            (
                roi_error,
                flux_error,
                event_delta,
                thickness_delta,
                recovery_delta,
                current_delta,
            )
        )
        peak_delta = (
            None
            if peak_coarse[cycle] is None or peak_fine[cycle] is None
            else abs(float(peak_coarse[cycle]) - float(peak_fine[cycle]))
        )
        thermal_rows.append((peak_delta, event_delta, current_delta))
        signed_peak.append(
            None
            if peak_coarse[cycle] is None or peak_fine[cycle] is None
            else float(peak_coarse[cycle]) - float(peak_fine[cycle])
        )
        signed_event.append(
            None
            if event_coarse[cycle] is None or event_fine[cycle] is None
            else float(event_coarse[cycle]) - float(event_fine[cycle])
        )
        current_effect.append(current_delta)
    return (
        tuple(component_rows),
        tuple(thermal_rows),
        {
            "peak_depletion": tuple(signed_peak),
            "event_time": tuple(signed_event),
            "current_trace_rms": tuple(current_effect),
        },
    )


def _persisted_thermal_deltas(
    coarse_artifact: CaseArtifact,
    fine_artifact: CaseArtifact,
    coarse_report: Mapping[str, Any],
    fine_report: Mapping[str, Any],
    contract: SynEdtPhysicalContract,
) -> tuple[
    tuple[tuple[float | None, ...], ...],
    Mapping[str, tuple[float | None, ...]],
    tuple[float | None, ...],
]:
    """Extract only the three frozen thermal-effect quantities.

    Endpoint component deltas and normalizers are deliberately *not* produced
    here.  Their sole implementation and sealing authority is
    ``syn_edt_evaluator.build_floor_seal``.  Current-trace differences remain
    in amperes so every comparison can later use the same nominal current
    normalizer from that seal.
    """

    cycles = int(contract.physical["absolute_waveform"]["cycles"])
    current_fine = _interpolate_time(
        fine_artifact.circuit["current_top"][:, None],
        fine_artifact.circuit_time,
        coarse_artifact.circuit_time,
    )[:, 0]
    peak_coarse = _event_sequence(coarse_report, "peak_roi_depletion", cycles)
    peak_fine = _event_sequence(fine_report, "peak_roi_depletion", cycles)
    event_coarse = _event_sequence(coarse_report, "event_time_s", cycles)
    event_fine = _event_sequence(fine_report, "event_time_s", cycles)
    rows: list[tuple[float | None, ...]] = []
    signed_peak: list[float | None] = []
    signed_event: list[float | None] = []
    raw_current: list[float | None] = []
    cycle_duration = float(
        contract.physical["absolute_waveform"]["cycle_duration_s"]
    )
    for cycle in range(cycles):
        start = cycle * cycle_duration
        end = start + cycle_duration
        selector = (
            (coarse_artifact.circuit_time >= start - 1.0e-12)
            & (coarse_artifact.circuit_time <= end + 1.0e-12)
        )
        time = coarse_artifact.circuit_time[selector]
        if not np.any(selector) or time.size == 0:
            current_delta: float | None = None
        else:
            measured = _time_rms(
                coarse_artifact.circuit["current_top"][selector]
                - current_fine[selector],
                time,
            )
            current_delta = measured if math.isfinite(measured) else None
        peak_delta = (
            None
            if peak_coarse[cycle] is None or peak_fine[cycle] is None
            else abs(float(peak_coarse[cycle]) - float(peak_fine[cycle]))
        )
        event_delta = (
            None
            if event_coarse[cycle] is None or event_fine[cycle] is None
            else abs(float(event_coarse[cycle]) - float(event_fine[cycle]))
        )
        rows.append((peak_delta, event_delta, None))
        signed_peak.append(
            None
            if peak_coarse[cycle] is None or peak_fine[cycle] is None
            else float(peak_coarse[cycle]) - float(peak_fine[cycle])
        )
        signed_event.append(
            None
            if event_coarse[cycle] is None or event_fine[cycle] is None
            else float(event_coarse[cycle]) - float(event_fine[cycle])
        )
        raw_current.append(current_delta)
    return (
        tuple(rows),
        {
            "peak_depletion": tuple(signed_peak),
            "event_time": tuple(signed_event),
            "current_trace_rms": tuple(raw_current),
        },
        tuple(raw_current),
    )


def compare_syn_edt_artifacts(
    coarse_artifact: CaseArtifact,
    fine_artifact: CaseArtifact,
    coarse_report: Mapping[str, Any],
    fine_report: Mapping[str, Any],
    contract: SynEdtPhysicalContract,
) -> SynEdtConvergenceReport:
    """Fail-closed persisted equivalent of :func:`compare_syn_edt_resolutions`."""

    required = {"event_report", "guard_report", "active_r_faces_nm", "active_z_faces_nm"}
    if not required.issubset(coarse_report) or not required.issubset(fine_report):
        raise ValueError("persisted SYN_EDT reports lack comparison-required keys")
    coarse_bounds, coarse_volume = _bounds_from_report(coarse_report)
    fine_bounds, _ = _bounds_from_report(fine_report)
    if coarse_bounds.shape[0] != coarse_artifact.nodes.shape[0]:
        raise ValueError("coarse report geometry does not match its artifact")
    if fine_bounds.shape[0] != fine_artifact.nodes.shape[0]:
        raise ValueError("fine report geometry does not match its artifact")
    projection = _overlap_projection(coarse_bounds, fine_bounds)
    names = ("defect_fraction_y", "electric_potential", "temperature")
    scales = _field_convergence_scales(contract)
    time_weight = _trapezoid_weights(coarse_artifact.field_time)
    mean_square: list[float] = []
    for name, scale in zip(names, scales):
        fine_values = _interpolate_time(
            fine_artifact.fields[name],
            fine_artifact.field_time,
            coarse_artifact.field_time,
        )
        projected = np.asarray((projection @ fine_values.T).T, dtype=np.float64)
        error = (coarse_artifact.fields[name] - projected) / scale
        spatial = np.sum(error**2 * coarse_volume[None, :], axis=1) / np.sum(
            coarse_volume
        )
        mean_square.append(float(np.sum(spatial * time_weight) / np.sum(time_weight)))
    field_l2 = math.sqrt(float(np.mean(mean_square)))

    def event_from(value: Mapping[str, Any]) -> SynEdtEventReport:
        return SynEdtEventReport(
            applicable=bool(value["applicable"]),
            passed=bool(value["passed"]),
            peak_roi_depletion=tuple(float(x) for x in value.get("peak_roi_depletion", ())),
            event_time_s=tuple(
                None if x is None else float(x) for x in value.get("event_time_s", ())
            ),
        )

    event_magnitude, event_time = _event_difference(
        event_from(coarse_report["event_report"]),
        event_from(fine_report["event_report"]),
    )
    coarse_current = float(np.max(np.abs(coarse_artifact.circuit["current_top"])))
    fine_current = float(np.max(np.abs(fine_artifact.circuit["current_top"])))
    current_relative = abs(coarse_current - fine_current) / max(fine_current, 1.0e-300)
    coarse_rise = float(np.max(coarse_artifact.circuit["temperature_max"]) - 300.0)
    fine_rise = float(np.max(fine_artifact.circuit["temperature_max"]) - 300.0)
    temperature_relative = abs(coarse_rise - fine_rise) / max(abs(fine_rise), 1.0)
    limits = contract.physical["convergence"]
    failures: list[str] = []
    if field_l2 > float(limits["medium_fine_field_l2_max"]):
        failures.append("field_l2")
    if event_magnitude > float(limits["medium_fine_event_magnitude_max"]):
        failures.append("event_magnitude")
    if event_time > float(limits["medium_fine_event_time_s_max"]):
        failures.append("event_time")
    peak_limit = float(limits["medium_fine_peak_current_temperature_max"])
    if current_relative > peak_limit:
        failures.append("peak_current")
    if temperature_relative > peak_limit:
        failures.append("peak_temperature")
    thermal_rows, signed_effects, raw_current = _persisted_thermal_deltas(
        coarse_artifact,
        fine_artifact,
        coarse_report,
        fine_report,
        contract,
    )

    def json_finite(value: float) -> float | None:
        return float(value) if math.isfinite(value) else None

    return SynEdtConvergenceReport(
        passed=not failures,
        field_l2=json_finite(field_l2),
        event_magnitude_relative=json_finite(event_magnitude),
        event_time_absolute_s=json_finite(event_time),
        peak_current_relative=json_finite(current_relative),
        peak_temperature_relative=json_finite(temperature_relative),
        failures=tuple(failures),
        thermal_component_deltas_by_cycle=thermal_rows,
        thermal_effect_signed_by_cycle=signed_effects,
        thermal_current_rms_difference_a_by_cycle=raw_current,
    )


def _legacy_adjudicate_syn_edt_s2(
    reports: Mapping[int, Mapping[str, Any]],
    comparisons: Mapping[str, Mapping[str, Any]],
    numerical_contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Adjudicate S2 only when every frozen evidence item is explicit.

    The function is intentionally fail-closed: ordinary failed gates are an
    adjudicated FAIL, while absent endpoint floors or thermal-effect
    attribution remain NOT_ADJUDICATED and can never become an inferred PASS.
    """

    ladder = numerical_contract.get("qualification_ladder", ())
    expected = {int(row["intent"]) for row in ladder if isinstance(row, Mapping)}
    if not expected or set(reports) != expected:
        return {
            "adjudicated": False,
            "passed": False,
            "reason": "INCOMPLETE_FROZEN_LADDER_REPORTS",
            "floors": {"ready": False},
            "thermal_controls": {"ready": False},
        }
    guard_failures: list[int] = []
    for intent in sorted(expected):
        guard = reports[intent].get("guard_report")
        if not isinstance(guard, Mapping) or not isinstance(guard.get("passed"), bool):
            return {
                "adjudicated": False,
                "passed": False,
                "reason": "MISSING_EXPLICIT_GUARD_VERDICT",
                "intent": intent,
                "floors": {"ready": False},
                "thermal_controls": {"ready": False},
            }
        if not bool(guard["passed"]):
            guard_failures.append(intent)
    event = reports.get(6, {}).get("event_report")
    if not isinstance(event, Mapping) or not isinstance(event.get("passed"), bool):
        return {
            "adjudicated": False,
            "passed": False,
            "reason": "MISSING_INTENT_6_EVENT_VERDICT",
            "floors": {"ready": False},
            "thermal_controls": {"ready": False},
        }
    required_comparisons = (
        "space_medium_fine",
        "time_medium_fine",
        "independent_process_replay",
        "direct_transport_medium_fine",
        "isothermal_medium_fine",
    )
    for name in required_comparisons:
        record = comparisons.get(name)
        if not isinstance(record, Mapping) or not isinstance(record.get("passed"), bool):
            return {
                "adjudicated": False,
                "passed": False,
                "reason": "MISSING_EXPLICIT_COMPARISON_VERDICT",
                "comparison": name,
                "floors": {"ready": False},
                "thermal_controls": {"ready": False},
            }
    ordinary_failures = {
        "guard_intents": guard_failures,
        "intent_6_event": not bool(event["passed"]),
        "space_medium_fine": not bool(comparisons["space_medium_fine"]["passed"]),
        "time_medium_fine": not bool(comparisons["time_medium_fine"]["passed"]),
        "replay": not bool(comparisons["independent_process_replay"]["passed"]),
        "direct_control_convergence": not bool(
            comparisons["direct_transport_medium_fine"]["passed"]
        ),
        "isothermal_control_convergence": not bool(
            comparisons["isothermal_medium_fine"]["passed"]
        ),
    }
    if guard_failures or any(
        value for key, value in ordinary_failures.items() if key != "guard_intents"
    ):
        return {
            "adjudicated": True,
            "passed": False,
            "reason": "ONE_OR_MORE_FROZEN_S2_HARD_GATES_FAILED",
            "failures": ordinary_failures,
            "floors": {"ready": False},
            "thermal_controls": {"ready": False},
        }

    floor_record = comparisons.get("endpoint_component_floors")
    thermal_direct = comparisons.get("full_vs_direct_thermal_effect")
    thermal_isothermal = comparisons.get("full_vs_isothermal_thermal_effect")
    floors_ready = bool(
        isinstance(floor_record, Mapping)
        and floor_record.get("sealed") is True
        and floor_record.get("finite") is True
    )
    thermal_ready = bool(
        isinstance(thermal_direct, Mapping)
        and isinstance(thermal_isothermal, Mapping)
        and isinstance(thermal_direct.get("effect_exceeds_numerical_uncertainty"), bool)
        and isinstance(
            thermal_isothermal.get("effect_exceeds_numerical_uncertainty"), bool
        )
    )
    if not floors_ready or not thermal_ready:
        return {
            "adjudicated": False,
            "passed": False,
            "reason": "ENDPOINT_FLOORS_OR_THERMAL_EFFECT_NOT_COMPARISON_READY",
            "floors": {"ready": floors_ready, "record": floor_record},
            "thermal_controls": {
                "ready": thermal_ready,
                "direct": thermal_direct,
                "isothermal": thermal_isothermal,
            },
            "completed_prerequisites": ordinary_failures,
        }
    thermal_pass = bool(
        thermal_direct["effect_exceeds_numerical_uncertainty"]
        and thermal_isothermal["effect_exceeds_numerical_uncertainty"]
    )
    return {
        "adjudicated": True,
        "passed": thermal_pass,
        "reason": (
            "ALL_FROZEN_S2_GATES_AND_THERMAL_EFFECT_PASS"
            if thermal_pass
            else "THERMAL_EFFECT_DOES_NOT_EXCEED_NUMERICAL_UNCERTAINTY"
        ),
        "floors": {"ready": True, "record": floor_record},
        "thermal_controls": {
            "ready": True,
            "direct": thermal_direct,
            "isothermal": thermal_isothermal,
        },
    }


def _finite_nonnegative(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0.0:
        return None
    return number


def _two_cycle_rows(
    record: Mapping[str, Any], key: str, width: int
) -> tuple[tuple[float | None, ...], tuple[float | None, ...]] | None:
    raw = record.get(key)
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)) or len(raw) != 2:
        return None
    rows: list[tuple[float | None, ...]] = []
    for row in raw:
        if (
            not isinstance(row, Sequence)
            or isinstance(row, (str, bytes))
            or len(row) != width
        ):
            return None
        values: list[float | None] = []
        for value in row:
            if value is None:
                values.append(None)
            else:
                values.append(_finite_nonnegative(value))
        rows.append(tuple(values))
    return rows[0], rows[1]


def _two_cycle_values(
    record: Mapping[str, Any], key: str
) -> tuple[float | None, float | None] | None:
    raw = record.get(key)
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)) or len(raw) != 2:
        return None
    values: list[float | None] = []
    for value in raw:
        values.append(None if value is None else _finite_nonnegative(value))
    return values[0], values[1]


def _validated_evaluator_floor_seal(
    record: Any,
    *,
    reports: Mapping[int, Mapping[str, Any]],
    nominal_intent: int,
    numerical_contract: Mapping[str, Any],
) -> tuple[Mapping[str, Any] | None, str]:
    if not isinstance(record, Mapping):
        return None, "MISSING_EVALUATOR_FLOOR_SEAL"
    candidate: Any = record.get("seal", record)
    if not isinstance(candidate, Mapping):
        return None, "MALFORMED_EVALUATOR_FLOOR_SEAL"
    floor = dict(candidate)
    if floor.get("schema_version") != "syn-edt-floor-seal-v1":
        return None, "UNSUPPORTED_EVALUATOR_FLOOR_SEAL"
    if floor.get("sealed_before_neural_work") is not True:
        return None, "FLOOR_NOT_SEALED_BEFORE_NEURAL_WORK"
    stored_hash = str(floor.get("seal_sha256", "")).upper()
    unsigned = dict(floor)
    unsigned.pop("seal_sha256", None)
    try:
        calculated_hash = _sha256_bytes(_canonical_json(unsigned))
    except (TypeError, ValueError):
        return None, "FLOOR_SEAL_IS_NOT_JSON_FINITE"
    if not stored_hash or stored_hash != calculated_hash:
        return None, "FLOOR_SEAL_HASH_MISMATCH"

    nominal_report = reports[nominal_intent]
    case_manifest = nominal_report.get("case_manifest")
    if not isinstance(case_manifest, Mapping):
        return None, "NOMINAL_REPORT_LACKS_CONTRACT_IDENTITY"
    identities = (
        ("physical_contract_id", nominal_report.get("physical_contract_id")),
        ("s0_sha256", case_manifest.get("s0_sha256")),
        ("numerical_contract_sha256", case_manifest.get("s2_numerical_sha256")),
        ("source_case_id", nominal_report.get("case_id")),
    )
    for key, expected in identities:
        if not isinstance(expected, str) or not expected or floor.get(key) != expected:
            return None, f"FLOOR_SEAL_{key.upper()}_MISMATCH"

    endpoint = numerical_contract.get("endpoint_and_floor_contract")
    if not isinstance(endpoint, Mapping):
        return None, "MISSING_ENDPOINT_AND_FLOOR_CONTRACT"
    component_order = endpoint.get("components_in_fixed_order")
    if not isinstance(component_order, Sequence) or isinstance(
        component_order, (str, bytes)
    ):
        return None, "MISSING_FROZEN_COMPONENT_ORDER"
    component_order = tuple(str(item) for item in component_order)
    if tuple(floor.get("component_order", ())) != component_order:
        return None, "FLOOR_COMPONENT_ORDER_MISMATCH"
    width = len(component_order)
    cycles = floor.get("cycles")
    if not isinstance(cycles, Sequence) or isinstance(cycles, (str, bytes)) or len(cycles) != 2:
        return None, "FLOOR_SEAL_REQUIRES_TWO_CYCLES"
    source = _finite_nonnegative(endpoint.get("source_joint_uncertainty"))
    tolerance = _finite_nonnegative(
        endpoint.get("declared_solver_tolerance_each_dimensionless_component")
    )
    if source is None or tolerance is None:
        return None, "NONFINITE_FROZEN_FLOOR_CONSTANT"
    for index, raw_cycle in enumerate(cycles):
        if not isinstance(raw_cycle, Mapping) or raw_cycle.get("cycle") != index + 1:
            return None, "FLOOR_CYCLE_IDENTITY_MISMATCH"
        parsed: dict[str, tuple[float, ...]] = {}
        for key in (
            "space_delta",
            "time_delta",
            "replay_delta",
            "source_joint_uncertainty",
            "twice_declared_solver_tolerance",
            "component_floor_u",
        ):
            raw_values = raw_cycle.get(key)
            if (
                not isinstance(raw_values, Sequence)
                or isinstance(raw_values, (str, bytes))
                or len(raw_values) != width
            ):
                return None, f"FLOOR_{key.upper()}_SHAPE_MISMATCH"
            values = tuple(_finite_nonnegative(item) for item in raw_values)
            if any(item is None for item in values):
                return None, f"FLOOR_{key.upper()}_NONESTIMABLE"
            parsed[key] = tuple(float(item) for item in values if item is not None)
        expected_source = tuple(source for _ in range(width))
        expected_solver = tuple(2.0 * tolerance for _ in range(width))
        if parsed["source_joint_uncertainty"] != expected_source:
            return None, "FLOOR_SOURCE_UNCERTAINTY_MISMATCH"
        if parsed["twice_declared_solver_tolerance"] != expected_solver:
            return None, "FLOOR_SOLVER_TOLERANCE_MISMATCH"
        expected_u = tuple(
            max(
                parsed["space_delta"][item],
                parsed["time_delta"][item],
                parsed["replay_delta"][item],
                source,
                2.0 * tolerance,
            )
            for item in range(width)
        )
        if any(
            not math.isclose(left, right, rel_tol=1.0e-12, abs_tol=1.0e-15)
            for left, right in zip(parsed["component_floor_u"], expected_u)
        ):
            return None, "FLOOR_COMPONENT_U_MISMATCH"
        tau = _finite_nonnegative(raw_cycle.get("tau_comp"))
        expected_tau = math.sqrt(sum(value * value for value in expected_u) / width)
        if tau is None or tau <= 0.0 or not math.isclose(
            tau, expected_tau, rel_tol=1.0e-12, abs_tol=1.0e-15
        ):
            return None, "FLOOR_TAU_COMP_MISMATCH"

    normalizers_by_case = floor.get("normalizers_by_case")
    source_case = str(floor["source_case_id"])
    if not isinstance(normalizers_by_case, Mapping):
        return None, "FLOOR_LACKS_CASE_NORMALIZERS"
    normalizers = normalizers_by_case.get(source_case)
    if (
        not isinstance(normalizers, Sequence)
        or isinstance(normalizers, (str, bytes))
        or len(normalizers) != 2
    ):
        return None, "FLOOR_LACKS_NOMINAL_NORMALIZERS"
    for item in normalizers:
        if not isinstance(item, Mapping):
            return None, "MALFORMED_NOMINAL_NORMALIZER"
        flux = _finite_nonnegative(item.get("defect_flux"))
        current = _finite_nonnegative(item.get("port_current"))
        if flux is None or current is None or flux <= 0.0 or current <= 0.0:
            return None, "NONPOSITIVE_NOMINAL_NORMALIZER"
    return floor, "READY"


def _nominal_current_normalizers(
    floor: Mapping[str, Any],
) -> tuple[float, float]:
    rows = floor["normalizers_by_case"][floor["source_case_id"]]
    return float(rows[0]["port_current"]), float(rows[1]["port_current"])


def _thermal_control_adjudication(
    *,
    label: str,
    control_intent: int,
    control_uncertainty_name: str,
    cross_name: str,
    reports: Mapping[int, Mapping[str, Any]],
    comparisons: Mapping[str, Mapping[str, Any]],
    nominal_intent: int,
    nominal_uncertainty_names: Sequence[str],
    current_normalizers: tuple[float, float],
    floor_minimum: float,
) -> tuple[bool, bool, dict[str, Any]]:
    needed = tuple(nominal_uncertainty_names) + (
        control_uncertainty_name,
        cross_name,
    )
    if any(not isinstance(comparisons.get(name), Mapping) for name in needed):
        return False, False, {
            "label": label,
            "reason": "MISSING_THERMAL_COMPARISON_RECORD",
        }
    parsed_rows: dict[str, tuple[tuple[float | None, ...], ...]] = {}
    parsed_current: dict[str, tuple[float | None, float | None]] = {}
    for name in needed:
        record = comparisons[name]
        rows = _two_cycle_rows(record, "thermal_component_deltas_by_cycle", 3)
        current = _two_cycle_values(
            record, "thermal_current_rms_difference_a_by_cycle"
        )
        if rows is None or current is None:
            return False, False, {
                "label": label,
                "reason": "MALFORMED_THERMAL_COMPARISON_RECORD",
                "comparison": name,
            }
        parsed_rows[name] = rows
        parsed_current[name] = current

    nominal_event = reports[nominal_intent].get("event_report")
    control_event = reports[control_intent].get("event_report")
    control_guard = reports[control_intent].get("guard_report")
    if not all(isinstance(item, Mapping) for item in (nominal_event, control_event, control_guard)):
        return False, False, {
            "label": label,
            "reason": "MISSING_THERMAL_EVENT_OR_GUARD_RECORD",
        }
    nominal_times = _event_sequence(reports[nominal_intent], "event_time_s", 2)
    control_times = _event_sequence(reports[control_intent], "event_time_s", 2)
    if any(value is None for value in nominal_times):
        return False, False, {
            "label": label,
            "reason": "NOMINAL_EVENT_TIME_NONESTIMABLE",
        }
    missing_control = tuple(value is None for value in control_times)
    if any(missing_control) and not all(missing_control):
        return True, False, {
            "label": label,
            "reason": "MIXED_OR_SINGLE_CYCLE_EVENT_CENSORING",
            "event_censoring": list(missing_control),
        }
    censored = bool(
        all(missing_control)
        and nominal_event.get("passed") is True
        and control_guard.get("passed") is True
    )

    effect_rows = parsed_rows[cross_name]
    effect_current = parsed_current[cross_name]
    uncertainty: list[list[float | None]] = []
    effects: list[list[float | None]] = []
    for cycle in range(2):
        peak_sources = [
            parsed_rows[name][cycle][0]
            for name in tuple(nominal_uncertainty_names)
            + (control_uncertainty_name,)
        ]
        current_sources = [
            parsed_current[name][cycle]
            for name in tuple(nominal_uncertainty_names)
            + (control_uncertainty_name,)
        ]
        if any(value is None for value in peak_sources + current_sources):
            return False, False, {
                "label": label,
                "reason": "THERMAL_PEAK_OR_CURRENT_UNCERTAINTY_NONESTIMABLE",
                "cycle": cycle + 1,
            }
        peak_uncertainty = max(
            *(float(value) for value in peak_sources if value is not None),
            floor_minimum,
        )
        current_uncertainty = max(
            *(
                float(value) / current_normalizers[cycle]
                for value in current_sources
                if value is not None
            ),
            floor_minimum,
        )
        event_uncertainty: float | None = None
        event_effect: float | None = None
        if not censored:
            event_sources = [
                parsed_rows[name][cycle][1]
                for name in tuple(nominal_uncertainty_names)
                + (control_uncertainty_name,)
            ]
            event_effect = effect_rows[cycle][1]
            if event_effect is None or any(value is None for value in event_sources):
                return False, False, {
                    "label": label,
                    "reason": "THERMAL_EVENT_UNCERTAINTY_NONESTIMABLE",
                    "cycle": cycle + 1,
                }
            event_uncertainty = max(
                *(float(value) for value in event_sources if value is not None),
                floor_minimum,
            )
        peak_effect = effect_rows[cycle][0]
        current_effect_a = effect_current[cycle]
        if peak_effect is None or current_effect_a is None:
            return False, False, {
                "label": label,
                "reason": "THERMAL_EFFECT_NONESTIMABLE",
                "cycle": cycle + 1,
            }
        effects.append(
            [
                float(peak_effect),
                event_effect,
                float(current_effect_a) / current_normalizers[cycle],
            ]
        )
        uncertainty.append(
            [peak_uncertainty, event_uncertainty, current_uncertainty]
        )

    signed = comparisons[cross_name].get("thermal_effect_signed_by_cycle")
    if not isinstance(signed, Mapping):
        return False, False, {
            "label": label,
            "reason": "MISSING_SIGNED_THERMAL_EFFECT",
        }
    # Signed peak/event values may be negative, so parse them separately.
    def signed_pair(key: str) -> tuple[float | None, float | None] | None:
        raw = signed.get(key)
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)) or len(raw) != 2:
            return None
        output: list[float | None] = []
        for value in raw:
            if value is None:
                output.append(None)
                continue
            try:
                number = float(value)
            except (TypeError, ValueError):
                return None
            output.append(number if math.isfinite(number) else None)
        return output[0], output[1]

    signed_peak = signed_pair("peak_depletion")
    signed_event = signed_pair("event_time")
    if signed_peak is None or (not censored and signed_event is None):
        return False, False, {
            "label": label,
            "reason": "MALFORMED_SIGNED_THERMAL_EFFECT",
        }

    exceed_by_cycle = [
        [
            effects[cycle][component] is not None
            and uncertainty[cycle][component] is not None
            and float(effects[cycle][component])
            > float(uncertainty[cycle][component])
            for component in range(3)
        ]
        for cycle in range(2)
    ]
    peak_sign_consistent = bool(
        signed_peak[0] is not None
        and signed_peak[1] is not None
        and signed_peak[0] != 0.0
        and signed_peak[1] != 0.0
        and signed_peak[0] * signed_peak[1] > 0.0
    )
    event_sign_consistent = bool(
        not censored
        and signed_event is not None
        and signed_event[0] is not None
        and signed_event[1] is not None
        and signed_event[0] != 0.0
        and signed_event[1] != 0.0
        and signed_event[0] * signed_event[1] > 0.0
    )
    shared = {
        "peak_depletion": bool(
            exceed_by_cycle[0][0]
            and exceed_by_cycle[1][0]
            and peak_sign_consistent
        ),
        "event_time": bool(
            censored
            or (
                exceed_by_cycle[0][1]
                and exceed_by_cycle[1][1]
                and event_sign_consistent
            )
        ),
        "current_trace_rms": bool(
            exceed_by_cycle[0][2] and exceed_by_cycle[1][2]
        ),
    }
    passed = any(shared.values())
    return True, passed, {
        "label": label,
        "passed": passed,
        "reason": (
            "THERMAL_EFFECT_EXCEEDS_NUMERICAL_UNCERTAINTY"
            if passed
            else "NO_SHARED_TWO_CYCLE_THERMAL_EFFECT_EXCEEDS_UNCERTAINTY"
        ),
        "effect_components": [
            "cycle_peak_roi_depletion_absolute_difference",
            "cycle_event_time_absolute_difference_divided_by_1_second",
            "cycle_top_current_trace_rms_difference_divided_by_the_frozen_current_normalizer",
        ],
        "effects_by_cycle": effects,
        "uncertainty_by_cycle": uncertainty,
        "exceeds_by_cycle": exceed_by_cycle,
        "shared_component_pass": shared,
        "signed_full_minus_control": {
            "peak_depletion": list(signed_peak),
            "event_time": None if signed_event is None else list(signed_event),
        },
        "sign_consistency": {
            "peak_depletion": peak_sign_consistent,
            "event_time": event_sign_consistent,
        },
        "event_censored_both_cycles": censored,
    }


def adjudicate_syn_edt_s2(
    reports: Mapping[int, Mapping[str, Any]],
    comparisons: Mapping[str, Mapping[str, Any]],
    numerical_contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Fail-closed adjudication of the complete frozen S2 evidence bundle."""

    ladder = numerical_contract.get("qualification_ladder", ())
    expected = {
        int(row["intent"])
        for row in ladder
        if isinstance(row, Mapping) and "intent" in row
    }
    base_not_ready = {
        "adjudicated": False,
        "passed": False,
        "floors": {"ready": False},
        "thermal_controls": {"ready": False},
    }
    if not expected or set(reports) != expected:
        return {
            **base_not_ready,
            "reason": "INCOMPLETE_FROZEN_LADDER_REPORTS",
        }
    thermal_gate = numerical_contract.get("thermal_effect_gate")
    if not isinstance(thermal_gate, Mapping):
        return {**base_not_ready, "reason": "MISSING_THERMAL_EFFECT_GATE"}
    try:
        nominal_intent = int(thermal_gate["nominal_reference_intent"])
        direct_intent = int(thermal_gate["direct_transport_off_intent"])
        isothermal_intent = int(thermal_gate["full_isothermal_off_intent"])
        nominal_uncertainty_names = tuple(
            str(item) for item in thermal_gate["nominal_uncertainty_comparisons"]
        )
        direct_uncertainty = str(
            thermal_gate["direct_control_uncertainty_comparison"]
        )
        isothermal_uncertainty = str(
            thermal_gate["isothermal_control_uncertainty_comparison"]
        )
    except (KeyError, TypeError, ValueError):
        return {**base_not_ready, "reason": "MALFORMED_THERMAL_EFFECT_GATE"}

    guard_failures: list[int] = []
    for intent in sorted(expected):
        guard = reports[intent].get("guard_report")
        if not isinstance(guard, Mapping) or not isinstance(guard.get("passed"), bool):
            return {
                **base_not_ready,
                "reason": "MISSING_EXPLICIT_GUARD_VERDICT",
                "intent": intent,
            }
        if not bool(guard["passed"]):
            guard_failures.append(intent)
    event = reports[nominal_intent].get("event_report")
    if not isinstance(event, Mapping) or not isinstance(event.get("passed"), bool):
        return {
            **base_not_ready,
            "reason": "MISSING_NOMINAL_EVENT_VERDICT",
            "intent": nominal_intent,
        }
    required_convergence = nominal_uncertainty_names + (
        direct_uncertainty,
        isothermal_uncertainty,
    )
    for name in required_convergence:
        record = comparisons.get(name)
        if not isinstance(record, Mapping) or not isinstance(record.get("passed"), bool):
            return {
                **base_not_ready,
                "reason": "MISSING_EXPLICIT_COMPARISON_VERDICT",
                "comparison": name,
            }
    ordinary_failures = {
        "guard_intents": guard_failures,
        "nominal_event": not bool(event["passed"]),
        "comparisons": {
            name: not bool(comparisons[name]["passed"])
            for name in required_convergence
        },
    }
    if (
        guard_failures
        or ordinary_failures["nominal_event"]
        or any(ordinary_failures["comparisons"].values())
    ):
        return {
            "adjudicated": True,
            "passed": False,
            "reason": "ONE_OR_MORE_FROZEN_S2_HARD_GATES_FAILED",
            "failures": ordinary_failures,
            "floors": {"ready": False},
            "thermal_controls": {"ready": False},
        }

    floor, floor_reason = _validated_evaluator_floor_seal(
        comparisons.get("endpoint_component_floors"),
        reports=reports,
        nominal_intent=nominal_intent,
        numerical_contract=numerical_contract,
    )
    if floor is None:
        return {
            **base_not_ready,
            "reason": floor_reason,
            "completed_prerequisites": ordinary_failures,
        }
    current_normalizers = _nominal_current_normalizers(floor)
    endpoint = numerical_contract["endpoint_and_floor_contract"]
    solver_tolerance = float(
        endpoint["declared_solver_tolerance_each_dimensionless_component"]
    )
    floor_minimum = 2.0 * solver_tolerance
    direct_ready, direct_passed, direct = _thermal_control_adjudication(
        label="DIRECT_T_TO_TRANSPORT_OFF",
        control_intent=direct_intent,
        control_uncertainty_name=direct_uncertainty,
        cross_name="full_vs_direct_thermal_effect",
        reports=reports,
        comparisons=comparisons,
        nominal_intent=nominal_intent,
        nominal_uncertainty_names=nominal_uncertainty_names,
        current_normalizers=current_normalizers,
        floor_minimum=floor_minimum,
    )
    isothermal_ready, isothermal_passed, isothermal = _thermal_control_adjudication(
        label="FULL_ISOTHERMAL_COUPLING_OFF",
        control_intent=isothermal_intent,
        control_uncertainty_name=isothermal_uncertainty,
        cross_name="full_vs_isothermal_thermal_effect",
        reports=reports,
        comparisons=comparisons,
        nominal_intent=nominal_intent,
        nominal_uncertainty_names=nominal_uncertainty_names,
        current_normalizers=current_normalizers,
        floor_minimum=floor_minimum,
    )
    floors = {
        "ready": True,
        "schema_version": floor["schema_version"],
        "seal_sha256": floor["seal_sha256"],
        "source_case_id": floor["source_case_id"],
        "cycles": floor["cycles"],
        "normalizers_by_case": floor["normalizers_by_case"],
    }
    if not direct_ready or not isothermal_ready:
        return {
            "adjudicated": False,
            "passed": False,
            "reason": "THERMAL_EFFECT_NOT_COMPARISON_READY",
            "floors": floors,
            "thermal_controls": {
                "ready": False,
                "direct": direct,
                "isothermal": isothermal,
            },
            "completed_prerequisites": ordinary_failures,
        }
    passed = direct_passed and isothermal_passed
    return {
        "adjudicated": True,
        "passed": passed,
        "reason": (
            "ALL_FROZEN_S2_GATES_AND_THERMAL_EFFECT_PASS"
            if passed
            else "THERMAL_EFFECT_DOES_NOT_EXCEED_NUMERICAL_UNCERTAINTY"
        ),
        "floors": floors,
        "thermal_controls": {
            "ready": True,
            "direct": direct,
            "isothermal": isothermal,
        },
    }
