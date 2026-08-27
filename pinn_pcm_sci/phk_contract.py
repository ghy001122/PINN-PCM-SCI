"""Fail-closed PHK-V2 contracts and complete-case split identities.

This module deliberately contains no solver or training code.  Its only job is
to turn pre-result JSON bytes into typed identities and to enumerate the case
universe without consulting numerical or neural outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Any, Mapping


JsonObject = dict[str, Any]


_PROGRAM_KEYS = {
    "schema_id",
    "contract_id",
    "effective_date",
    "status",
    "source_plan",
    "preserves",
    "authorization",
    "baseline_identities",
    "physical_object",
    "case_identity_fields",
    "case_pools",
    "primary_endpoint",
    "important_secondary_endpoints",
    "hard_guards",
    "method_arms",
    "formal_statistics",
    "budgets",
    "stage_order",
    "failure_semantics",
    "completion_requires",
}

_OBJECT_KEYS = {
    "schema_id",
    "contract_id",
    "status",
    "effective_date",
    "evidence_identity",
    "source_roles",
    "coordinates",
    "geometry",
    "fields",
    "governing_equations",
    "coefficients",
    "waveform",
    "discretization",
    "resolutions",
    "nonlinear_solver",
    "qualification_event",
    "hard_guard_thresholds",
    "convergence",
    "qualification_intents",
    "factor_supports",
    "split_rules",
    "prohibitions",
}


def _read_exact_json(path: Path, expected_keys: set[str]) -> tuple[bytes, JsonObject]:
    raw = path.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid UTF-8 JSON contract: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("contract root must be a JSON object")
    actual = set(payload)
    unknown = actual - expected_keys
    missing = expected_keys - actual
    if unknown:
        raise ValueError(f"unknown contract keys: {sorted(unknown)}")
    if missing:
        raise ValueError(f"missing contract keys: {sorted(missing)}")
    return raw, payload


def _require_mapping(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def _finite_positive(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(number) or number <= 0.0:
        raise ValueError(f"{name} must be finite and positive")
    return number


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


@dataclass(frozen=True)
class PhkProgramContract:
    path: Path
    payload: Mapping[str, Any]
    sha256: str

    @property
    def contract_id(self) -> str:
        return str(self.payload["contract_id"])

    @classmethod
    def load(cls, path: Path) -> "PhkProgramContract":
        exact = Path(path).resolve()
        raw, payload = _read_exact_json(exact, _PROGRAM_KEYS)
        if payload["schema_id"] != "phk-v2-program-contract-v1":
            raise ValueError("unsupported PHK program schema_id")
        if payload["contract_id"] != "PLAN_PHK_V2_V1":
            raise ValueError("unexpected PHK program contract_id")
        budgets = _require_mapping(payload, "budgets")
        for name in (
            "cpu_core_hours",
            "development_gpu_exclusive_hours",
            "formal_gpu_exclusive_hours",
            "total_gpu_exclusive_hours",
        ):
            _finite_positive(budgets.get(name), f"budgets.{name}")
        if float(budgets["paid_compute"]) != 0.0:
            raise ValueError("paid_compute must remain zero")
        if float(budgets["external_publication_or_git_remote"]) != 0.0:
            raise ValueError("external publication/Git budget must remain zero")
        return cls(exact, payload, hashlib.sha256(raw).hexdigest().upper())


@dataclass(frozen=True)
class PhkObjectContract:
    path: Path
    payload: Mapping[str, Any]
    sha256: str
    program_sha256: str

    @property
    def contract_id(self) -> str:
        return str(self.payload["contract_id"])

    @property
    def pulse_cycles(self) -> int:
        return int(_require_mapping(self.payload, "coordinates")["pulse_cycles"])

    @property
    def dtype(self) -> str:
        return str(_require_mapping(self.payload, "discretization")["float_dtype"])

    @property
    def coefficients(self) -> Mapping[str, Any]:
        return _require_mapping(self.payload, "coefficients")

    @property
    def factor_supports(self) -> Mapping[str, Any]:
        return _require_mapping(self.payload, "factor_supports")

    def waveform(self, time_value: float, *, amplitude: float | None = None) -> float:
        time_number = float(time_value)
        coordinates = _require_mapping(self.payload, "coordinates")
        waveform = _require_mapping(self.payload, "waveform")
        start = float(coordinates["time_start"])
        end = float(coordinates["time_end"])
        period = float(coordinates["time_period"])
        if time_number < start or time_number >= end:
            return 0.0
        phase = (time_number - start) % period
        peak = float(waveform["amplitude"] if amplitude is None else amplitude)
        rise = float(waveform["ramp_up_end"])
        hold = float(waveform["hold_end"])
        fall = float(waveform["ramp_down_end"])
        if phase < rise:
            return peak * phase / rise
        if phase <= hold:
            return peak
        if phase < fall:
            return peak * (fall - phase) / (fall - hold)
        return 0.0

    @classmethod
    def load(
        cls,
        path: Path,
        *,
        program: PhkProgramContract,
    ) -> "PhkObjectContract":
        exact = Path(path).resolve()
        raw, payload = _read_exact_json(exact, _OBJECT_KEYS)
        if payload["schema_id"] != "phk-v2-object-numerical-contract-v1":
            raise ValueError("unsupported PHK object schema_id")
        if payload["contract_id"] != "PHK_REDUCED_WALL_CELL_2D_V1_NUMERICAL_V1":
            raise ValueError("unexpected PHK object contract_id")
        if payload["status"] != "PRE_FIRST_PHK_SOLVE_FREEZE":
            raise ValueError("PHK object contract is not a pre-first-solve freeze")

        coordinates = _require_mapping(payload, "coordinates")
        if int(coordinates.get("pulse_cycles", 0)) != 2:
            raise ValueError("pulse_cycles must equal two")
        if float(coordinates["time_end"]) != 2.0 * float(coordinates["time_period"]):
            raise ValueError("time_end must contain exactly two periods")

        coefficients = _require_mapping(payload, "coefficients")
        for name in (
            "thermal_diffusivity",
            "volumetric_cooling",
            "joule_gain",
            "conductivity_phase_ratio",
            "interface_width",
            "barrier_scale",
            "thermal_drive",
            "mobility_cold",
            "mobility_hot",
            "mobility_width",
            "initial_phase_background",
        ):
            _finite_positive(coefficients.get(name), f"coefficients.{name}")
        if float(coefficients["mobility_hot"]) < float(coefficients["mobility_cold"]):
            raise ValueError("mobility_hot cannot be below mobility_cold")
        if not 0.0 < float(coefficients["initial_phase_background"]) < 0.5:
            raise ValueError("initial_phase_background must be in the cold basin")

        discretization = _require_mapping(payload, "discretization")
        if discretization.get("float_dtype") != "float64":
            raise ValueError("PHK scientific object requires float64")
        if discretization.get("clipping_as_acceptance") is not False:
            raise ValueError("clipping_as_acceptance must be false")

        resolutions = _require_mapping(payload, "resolutions")
        if set(resolutions) != {"coarse", "medium", "fine", "medium_half_dt"}:
            raise ValueError("resolution identities are incomplete or unknown")
        for name, item in resolutions.items():
            if not isinstance(item, dict):
                raise ValueError(f"resolution {name} must be an object")
            if int(item.get("nx", 0)) <= 0 or int(item.get("nz", 0)) <= 0:
                raise ValueError(f"resolution {name} grid is invalid")
            _finite_positive(item.get("dt"), f"resolutions.{name}.dt")

        intents = payload["qualification_intents"]
        if not isinstance(intents, list) or [item.get("order") for item in intents] != list(
            range(1, 13)
        ):
            raise ValueError("qualification intents must be the frozen ordered 1..12 ladder")

        return cls(
            exact,
            payload,
            hashlib.sha256(raw).hexdigest().upper(),
            program.sha256,
        )


@dataclass(frozen=True)
class PhkSplitManifest:
    """Exact, outcome-blind binding of a split file to both contract bytes."""

    path: Path
    payload: Mapping[str, Any]
    file_sha256: str

    @property
    def manifest_sha256(self) -> str:
        return str(self.payload["manifest_sha256"])

    @classmethod
    def load(
        cls,
        path: Path,
        *,
        program: PhkProgramContract,
        physical: PhkObjectContract,
    ) -> "PhkSplitManifest":
        exact = Path(path).resolve()
        raw = exact.read_bytes()
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid UTF-8 JSON split manifest: {exact}") from exc
        if not isinstance(payload, dict):
            raise ValueError("split manifest root must be a JSON object")
        expected = build_phk_split_manifest(program=program, physical=physical)
        if payload != expected:
            raise ValueError(
                "split manifest does not exactly match the current frozen contracts"
            )
        return cls(
            path=exact,
            payload=payload,
            file_sha256=hashlib.sha256(raw).hexdigest().upper(),
        )


def _case_pool(factors: Mapping[str, Any], digest: str) -> str:
    if (
        factors["constitutive_branch"] == "LOWER_PHASE_CONDUCTIVITY_FEEDBACK"
        and factors["waveform_amplitude"] == 0.85
    ):
        return "R"
    if factors["heater_width_fraction"] == 0.20 or factors["interface_width"] == 0.025:
        return "F_O"
    bucket = int(digest[:8], 16) % 100
    if bucket <= 39:
        return "D"
    if bucket <= 54:
        return "I1"
    if bucket <= 69:
        return "I2"
    if bucket <= 89:
        return "F_A"
    return "R"


def build_phk_split_manifest(
    *,
    program: PhkProgramContract,
    physical: PhkObjectContract,
) -> JsonObject:
    """Enumerate and hash-split the full pre-result complete-case universe."""

    if physical.program_sha256 != program.sha256:
        raise ValueError("object contract was not loaded against this program contract")
    supports = physical.factor_supports
    expected = (
        "heater_width_fraction",
        "interface_width",
        "waveform_amplitude",
        "pulse_hold_end",
        "initial_phase_background",
        "constitutive_branch",
    )
    if set(supports) != set(expected):
        raise ValueError("factor_supports contain missing or unknown axes")

    cases: dict[str, JsonObject] = {}
    counts = {pool: 0 for pool in ("D", "I1", "I2", "F_A", "F_O", "R")}
    for values in itertools.product(*(supports[name] for name in expected)):
        factors = dict(zip(expected, values, strict=True))
        identity = {
            "physical_contract_id": physical.contract_id,
            "geometry": {
                "heater_width_fraction": factors["heater_width_fraction"],
                "wall_cell": "TWO_DIMENSIONAL_CARTESIAN",
            },
            "material_or_synthetic_constitutive_branch": factors[
                "constitutive_branch"
            ],
            "initial_state": {
                "phase_background": factors["initial_phase_background"]
            },
            "full_waveform": {
                "amplitude": factors["waveform_amplitude"],
                "hold_end": factors["pulse_hold_end"],
                "periods": physical.pulse_cycles,
            },
            "full_history": "CONTINUOUS_TWO_CYCLE_NO_RESET",
            "interface_width": factors["interface_width"],
        }
        digest = hashlib.sha256(_canonical_json(identity)).hexdigest().upper()
        pool = _case_pool(factors, digest)
        if digest in cases:
            raise RuntimeError("complete-case SHA256 collision")
        cases[digest] = {
            "pool": pool,
            "factors": factors,
            "identity": identity,
        }
        counts[pool] += 1

    manifest: JsonObject = {
        "schema_id": "phk-v2-split-manifest-v1",
        "program_contract_id": program.contract_id,
        "program_contract_sha256": program.sha256,
        "object_contract_id": physical.contract_id,
        "object_contract_sha256": physical.sha256,
        "partition_semantics": "PRE_RESULT_COMPLETE_CASE_HASH_SPLIT",
        "pool_counts": counts,
        "cases": dict(sorted(cases.items())),
    }
    manifest["manifest_sha256"] = hashlib.sha256(
        _canonical_json(manifest)
    ).hexdigest().upper()
    return manifest
