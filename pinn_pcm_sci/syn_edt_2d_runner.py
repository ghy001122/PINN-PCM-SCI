"""Immutable S2 orchestration for the frozen SYN_EDT_2D_V1 oracle.

The runner is deliberately thin.  Physics, case identity, artifacts, and
cross-resolution comparison live in :mod:`pinn_pcm_sci.syn_edt_2d`; this
module owns only process boundaries, intent ordering, accounting, and the
append-only experiment ledger.
"""

from __future__ import annotations

import argparse
import ctypes
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

import h5py
import numpy as np
import scipy

from .artifacts import CaseArtifact
from .ledger import ExperimentLedger, RunManifest
from . import syn_edt_2d as syn_core
from . import syn_edt_evaluator as syn_eval


DEFAULT_S0_CONTRACT = Path("configs/goal_paper_one_shot_v1/s0_contract.json")
DEFAULT_S2_CONTRACT = Path(
    "configs/goal_paper_one_shot_v1/s2_numerical_contract.json"
)
DEFAULT_OUTPUT_ROOT = Path("outputs/runs")
DEFAULT_EXPERIMENT_ROOT = Path("docs/experiment")

EXPERIMENT_GROUP_ID = "goal-paper-one-shot-v1-syn-edt-2d"
PHYSICAL_CONTRACT_ID = "SYN_EDT_2D_V1_PHYSICS_V1"
SPLIT_ID = "syn-edt-2d-v1-s2-q-only-v1"
ORACLE_METHOD_ID = "syn-edt-2d-v1-independent-axisymmetric-fv"
CASE_GENERATOR_METHOD_ID = "syn-edt-2d-v1-q-case-generator"
SUMMARY_METHOD_ID = "syn-edt-2d-v1-s2-adjudicator"
EVALUATOR_ID = "syn-edt-2d-v1-s2-event-guard-convergence-v1"
EVIDENCE_IDENTITY = "FULLY_TRANSPARENT_SYNTHETIC_BENCHMARK"
Q_CASES = frozenset({"Q0", "QL", "QN", "QH"})
LEVELS = frozenset({"coarse", "medium", "fine"})
SOLVER_COUNT_FIELDS = (
    "timesteps",
    "block_iterations_total",
    "block_iterations_max",
    "transport_newton_iterations_total",
    "transport_newton_iterations_max",
    "final_consistency_evaluations_total",
    "electric_linear_solves_total",
    "thermal_linear_solves_total",
    "transport_linear_solves_total",
    "linear_solves_total",
)
SOLVER_RESIDUAL_FIELD = "final_transport_scaled_residual_max"
CONTROL_NAMES = frozenset(
    {
        "FULL",
        "DIRECT_T_TO_TRANSPORT_OFF",
        "FULL_ISOTHERMAL_COUPLING_OFF",
    }
)


class RunnerContractError(ValueError):
    """The frozen S2 runner contract is incomplete or inconsistent."""


@dataclass(frozen=True)
class S2Intent:
    number: int
    qualification_case: str
    space_level: str
    time_level: str
    control_name: str
    role: str | None = None

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "S2Intent":
        try:
            intent = cls(
                number=int(payload["intent"]),
                qualification_case=str(payload["case"]),
                space_level=str(payload["space"]),
                time_level=str(payload["time"]),
                control_name=str(payload["control"]),
                role=None if payload.get("role") is None else str(payload["role"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise RunnerContractError("invalid S2 qualification-ladder row") from exc
        if intent.qualification_case not in Q_CASES:
            raise RunnerContractError("S2 may not access a case outside pool Q")
        if intent.space_level not in LEVELS or intent.time_level not in LEVELS:
            raise RunnerContractError("S2 ladder uses an unsupported resolution level")
        if intent.control_name not in CONTROL_NAMES:
            raise RunnerContractError("S2 ladder uses an unsupported control")
        return intent

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "intent": self.number,
            "case": self.qualification_case,
            "space": self.space_level,
            "time": self.time_level,
            "control": self.control_name,
        }
        if self.role is not None:
            payload["role"] = self.role
        return payload


@dataclass(frozen=True)
class ContractBundle:
    s0_payload: dict[str, Any]
    s2_payload: dict[str, Any]
    physical_contract: Any
    ladder: tuple[S2Intent, ...]


@dataclass(frozen=True)
class S2FreezeBinding:
    run_id: str
    case_manifest_path: Path
    case_manifest_sha256: str
    s0_sha256: str
    s2_sha256: str

    def manifest_fields(self) -> dict[str, str]:
        return {
            "freeze_run_id": self.run_id,
            "case_manifest_sha256": self.case_manifest_sha256,
            "s0_sha256": self.s0_sha256,
            "s2_sha256": self.s2_sha256,
        }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RunnerContractError(f"cannot read JSON contract: {path}") from exc
    if not isinstance(payload, dict):
        raise RunnerContractError(f"JSON contract is not an object: {path}")
    return payload


def _load_contract_bundle(s0_path: Path, s2_path: Path) -> ContractBundle:
    s0 = _read_json_object(s0_path)
    s2 = _read_json_object(s2_path)
    if s2.get("schema_version") != "goal-paper-one-shot-v1-s2-numerics-v1":
        raise RunnerContractError("unsupported S2 numerical-contract schema")
    if s2.get("physical_contract_id") != PHYSICAL_CONTRACT_ID:
        raise RunnerContractError("S2 physical-contract identity mismatch")
    declared_hash = str(s2.get("derived_from_s0_sha256", "")).upper()
    actual_hash = hashlib.sha256(s0_path.read_bytes()).hexdigest().upper()
    if not declared_hash or declared_hash != actual_hash:
        raise RunnerContractError("S2 numerical contract does not match the frozen S0 bytes")
    rows = s2.get("qualification_ladder")
    if not isinstance(rows, list) or not rows:
        raise RunnerContractError("S2 requires a non-empty qualification ladder")
    ladder = tuple(S2Intent.from_payload(row) for row in rows if isinstance(row, dict))
    expected_numbers = tuple(range(1, len(rows) + 1))
    if len(ladder) != len(rows) or tuple(item.number for item in ladder) != expected_numbers:
        raise RunnerContractError("S2 intent numbers must be contiguous from one")
    if len({item.to_dict().__repr__() for item in ladder}) != len(ladder):
        raise RunnerContractError("S2 qualification ladder contains a duplicate row")
    replay_rows = [item for item in ladder if item.role is not None]
    if replay_rows and any(
        item.role != "INDEPENDENT_PROCESS_EXACT_REPLAY_FOR_ORACLE_FLOOR"
        for item in replay_rows
    ):
        raise RunnerContractError("S2 ladder contains an unsupported intent role")
    contract = syn_core.SynEdtPhysicalContract.from_s0(
        s0_path, numerical_path=s2_path
    )
    return ContractBundle(s0, s2, contract, ladder)


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _write_json_once(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"immutable JSON already exists: {path}")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(_jsonable(payload), handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _code_identity() -> dict[str, Any]:
    revision = "UNAVAILABLE"
    dirty = True
    try:
        revision_run = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        status_run = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        revision = revision_run.stdout.strip()
        dirty = bool(status_run.stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        pass
    return {"kind": "working-tree", "revision": revision, "dirty": dirty}


def _environment() -> dict[str, Any]:
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "h5py": h5py.__version__,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "device": "cpu",
        "dtype": "float64",
    }


def _peak_process_rss_bytes() -> int | None:
    try:
        if os.name == "nt":
            from ctypes import wintypes

            class ProcessMemoryCounters(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            counters = ProcessMemoryCounters()
            counters.cb = ctypes.sizeof(counters)
            process = ctypes.windll.kernel32.GetCurrentProcess()
            ok = ctypes.windll.psapi.GetProcessMemoryInfo(
                process, ctypes.byref(counters), counters.cb
            )
            return int(counters.PeakWorkingSetSize) if ok else None
        import resource

        maximum = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        return maximum if sys.platform == "darwin" else maximum * 1024
    except (AttributeError, ImportError, OSError, ValueError):
        return None


def _exact_solver_statistics(result: Any) -> dict[str, int | float]:
    raw = getattr(result, "solver_statistics", None)
    if not isinstance(raw, Mapping):
        raise RunnerContractError("oracle result lacks exact solver_statistics")
    statistics: dict[str, int | float] = {}
    for field in SOLVER_COUNT_FIELDS:
        value = raw.get(field)
        try:
            count = int(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise RunnerContractError(
                f"oracle solver_statistics lacks integer {field}"
            ) from exc
        if isinstance(value, bool) or count < 0 or value != count:
            raise RunnerContractError(
                f"oracle solver_statistics has invalid count {field}"
            )
        statistics[field] = count
    try:
        residual = float(raw[SOLVER_RESIDUAL_FIELD])
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise RunnerContractError(
            f"oracle solver_statistics lacks {SOLVER_RESIDUAL_FIELD}"
        ) from exc
    if not np.isfinite(residual) or residual < 0.0:
        raise RunnerContractError(
            f"oracle solver_statistics has invalid {SOLVER_RESIDUAL_FIELD}"
        )
    statistics[SOLVER_RESIDUAL_FIELD] = residual
    component_total = sum(
        int(statistics[field])
        for field in (
            "electric_linear_solves_total",
            "thermal_linear_solves_total",
            "transport_linear_solves_total",
        )
    )
    if statistics["linear_solves_total"] != component_total:
        raise RunnerContractError(
            "oracle linear_solves_total differs from exact component sum"
        )
    return statistics


def _accounting(
    *,
    intent_id: str,
    method_id: str,
    case_id: str,
    wall_start: float,
    cpu_start: float,
    solver_intents: int,
    failed_intents: int,
    failure: BaseException | None,
    intent: S2Intent | None = None,
    solver_statistics: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    wall_seconds = max(0.0, time.perf_counter() - wall_start)
    process_cpu_seconds = max(0.0, time.process_time() - cpu_start)
    cpu_core_hours = process_cpu_seconds / 3600.0
    internal = {} if solver_statistics is None else dict(solver_statistics)
    failure_identity = {
        "status": "NO_FAILURE" if failure is None else "FAILED_INTENT",
        "failure_class": None if failure is None else type(failure).__name__,
        "message": None if failure is None else str(failure),
    }
    payload: dict[str, Any] = {
        "intent_id": intent_id,
        "method_id": method_id,
        "case_id": case_id,
        "seed": 0,
        "solver_intents": solver_intents,
        "failed_intents": failed_intents,
        "wall_seconds": wall_seconds,
        "wall_clock_seconds": wall_seconds,
        "process_cpu_seconds": process_cpu_seconds,
        "cpu_core_hours": cpu_core_hours,
        "cpu_threads_declared": 1,
        "peak_ram_bytes": _peak_process_rss_bytes(),
        "peak_ram_scope": "PROCESS_LIFETIME_HIGH_WATER_MARK",
        "peak_vram_bytes": 0,
        "parameter_count": 0,
        "forward_calls": 0,
        "automatic_differentiation_work": 0,
        "optimizer_closures_or_updates": 0,
        "rescue_attempts": 0,
        "hardware_identity": {
            "machine": platform.machine(),
            "processor": platform.processor(),
            "logical_cpu_count": os.cpu_count(),
        },
        "gross_compute": cpu_core_hours,
        "gross_compute_unit": "CPU_PROCESS_CORE_HOURS",
        "failure_identity": failure_identity,
        "failed_intent_consumed": bool(failed_intents),
        "superseding_rerun_eligibility": False,
        "superseding_rerun_disposition": (
            "NOT_APPLICABLE_SUCCESSFUL_INTENT"
            if failure is None
            else "REQUIRES_RELEVANT_INPUT_IMPLEMENTATION_OR_CONTRACT_CHANGE_"
            "AND_EXPLICIT_RECONCILIATION"
        ),
        "solver_statistics": _jsonable(internal),
        "solver_counters": _jsonable(internal),
    }
    if intent is not None:
        payload.update(
            {
                "s2_intent": intent.number,
                "qualification_case": intent.qualification_case,
                "case_pool": "Q",
                "space_level": intent.space_level,
                "time_level": intent.time_level,
                "control": intent.control_name,
                "intent_role": intent.role,
            }
        )
    return payload


def _planned_budget(bundle: ContractBundle, intent: S2Intent | None) -> dict[str, Any]:
    budgets = bundle.s0_payload.get("budgets", {})
    planned: dict[str, Any] = {
        "cpu_solver_intents_goal_cap": budgets.get("cpu_solver_intents"),
        "cpu_core_hours_goal_cap": budgets.get("cpu_core_hours"),
        "failed_intents_count_against_budget": True,
        "timestep_rescue": False,
        "parameter_rescue": False,
        "pool_scope": "Q_ONLY",
    }
    if intent is not None:
        planned["solver_intents"] = 1
        planned["qualification_ladder_row"] = intent.to_dict()
        planned["planned_oracle_floor_replay"] = bool(intent.role)
    else:
        planned["solver_intents"] = 0
    return planned


def _validate_run_id(run_id: str) -> None:
    if not run_id or run_id in {".", ".."} or Path(run_id).name != run_id:
        raise RunnerContractError("run_id must be one non-empty path segment")


def _new_run_root(output_root: Path, run_id: str) -> Path:
    _validate_run_id(run_id)
    root = output_root / run_id
    root.mkdir(parents=True, exist_ok=False)
    return root


def _record_manifest(
    *,
    experiment_root: Path,
    run_id: str,
    tier: str,
    scientific_role: str,
    gate: str,
    started_at: str,
    command: list[str],
    execution_status: str,
    numerical_validity: str,
    gate_outcome: str,
    route_disposition: str | None,
    claim_status: str,
    method_id: str,
    case_id: str,
    planned_budget: dict[str, Any],
    actual_budget: dict[str, Any],
    artifacts: dict[str, str],
    failure: BaseException | None,
    supersedes: str | None = None,
) -> Path:
    manifest = RunManifest(
        run_id=run_id,
        experiment_group_id=EXPERIMENT_GROUP_ID,
        tier=tier,
        scientific_role=scientific_role,
        gate=gate,
        started_at=started_at,
        ended_at=_utc_now(),
        command=command,
        execution_status=execution_status,
        numerical_validity=numerical_validity,
        gate_outcome=gate_outcome,
        route_disposition=route_disposition,
        evidence_identity=EVIDENCE_IDENTITY,
        claim_status=claim_status,
        code_identity=_code_identity(),
        environment=_environment(),
        physical_contract_id=PHYSICAL_CONTRACT_ID,
        split_id=SPLIT_ID,
        method_id=method_id,
        case_id=case_id,
        seed=0,
        planned_budget=planned_budget,
        actual_budget=actual_budget,
        checkpoint={"id": "NOT_APPLICABLE", "selection": "INDEPENDENT_CPU_ORACLE"},
        evaluator_id=EVALUATOR_ID,
        artifacts=artifacts,
        failure_class=None if failure is None else type(failure).__name__,
        replay_of=None,
        supersedes=supersedes,
    )
    ledger = ExperimentLedger(experiment_root)
    path = ledger.record(manifest)
    ledger.validate()
    return path


def _case_entries(manifest: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    raw = manifest.get("cases")
    if isinstance(raw, Mapping):
        entries = {
            str(case_id): value
            for case_id, value in raw.items()
            if isinstance(value, Mapping)
        }
    elif isinstance(raw, list):
        entries = {}
        for value in raw:
            if not isinstance(value, Mapping):
                raise RunnerContractError("case manifest contains an invalid list entry")
            identity = value.get(
                "case_id",
                value.get("qualification_case", value.get("qualification_id")),
            )
            if not identity:
                raise RunnerContractError("case manifest list entry lacks case identity")
            key = str(identity)
            if key in entries:
                raise RunnerContractError("case manifest contains a duplicate case identity")
            entries[key] = value
    else:
        raise RunnerContractError("case manifest requires a cases map or list")
    if not entries:
        raise RunnerContractError("case manifest contains no cases")
    return entries


def _q_only_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    selected: dict[str, Mapping[str, Any]] = {}
    seen_qualifications: set[str] = set()
    for case_id, entry in _case_entries(manifest).items():
        qualification = str(
            entry.get("qualification_case", entry.get("qualification_id", ""))
        )
        pool = str(entry.get("pool", entry.get("case_pool", "Q")))
        if pool != "Q":
            continue
        if qualification not in Q_CASES:
            raise RunnerContractError("pool Q contains an unknown qualification case")
        selected[case_id] = dict(entry)
        seen_qualifications.add(qualification)
    if seen_qualifications != Q_CASES:
        raise RunnerContractError("S2 Q manifest must contain Q0, QL, QN, and QH")
    return {
        "schema_version": "split-manifest-v1",
        "split_id": SPLIT_ID,
        "physical_contract_id": PHYSICAL_CONTRACT_ID,
        "scope": "S2_Q_ONLY",
        "cases": selected,
    }


def _existing_case_manifests(experiment_root: Path) -> list[dict[str, Any]]:
    manifest_root = experiment_root / "manifests"
    manifests: list[dict[str, Any]] = []
    if not manifest_root.exists():
        return manifests
    for path in sorted(manifest_root.glob("*.json")):
        payload = _read_json_object(path)
        if (
            payload.get("experiment_group_id") == EXPERIMENT_GROUP_ID
            and payload.get("gate") == "S2_CASE"
        ):
            manifests.append(payload)
    return manifests


def _load_completed_freeze_manifest(
    experiment_root: Path, freeze_run_id: str
) -> dict[str, Any]:
    _validate_run_id(freeze_run_id)
    path = experiment_root / "manifests" / f"{freeze_run_id}.json"
    if not path.is_file():
        raise RunnerContractError(f"S2 freeze manifest does not exist: {freeze_run_id}")
    payload = _read_json_object(path)
    if (
        payload.get("run_id") != freeze_run_id
        or payload.get("experiment_group_id") != EXPERIMENT_GROUP_ID
        or payload.get("gate") != "S2_CASE_FREEZE"
        or payload.get("execution_status") != "COMPLETED"
        or payload.get("physical_contract_id") != PHYSICAL_CONTRACT_ID
        or payload.get("split_id") != SPLIT_ID
    ):
        raise RunnerContractError(
            f"S2 freeze manifest is not a completed compatible freeze: {freeze_run_id}"
        )
    return payload


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        _jsonable(payload),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _validate_freeze_binding(
    experiment_root: Path,
    freeze_run_id: str,
    *,
    contract: Any | None = None,
    s2_contract_path: Path | None = None,
    expected_q_manifest: Mapping[str, Any] | None = None,
    expected_s0_sha256: str,
    expected_s2_sha256: str,
) -> S2FreezeBinding:
    manifest = _load_completed_freeze_manifest(experiment_root, freeze_run_id)
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, Mapping):
        raise RunnerContractError(f"S2 freeze lacks artifacts: {freeze_run_id}")
    declared: dict[str, str] = {}
    for key in ("case_manifest_sha256", "s0_sha256", "s2_sha256"):
        value = artifacts.get(key)
        if not isinstance(value, str) or not value or value != value.upper():
            raise RunnerContractError(
                f"S2 freeze lacks uppercase {key}: {freeze_run_id}"
            )
        declared[key] = value
    if declared["s0_sha256"] != expected_s0_sha256.upper():
        raise RunnerContractError(f"S2 freeze S0 hash mismatch: {freeze_run_id}")
    if declared["s2_sha256"] != expected_s2_sha256.upper():
        raise RunnerContractError(f"S2 freeze S2 hash mismatch: {freeze_run_id}")
    case_manifest_value = artifacts.get("case_manifest")
    if not isinstance(case_manifest_value, str) or not case_manifest_value:
        raise RunnerContractError(f"S2 freeze lacks case manifest: {freeze_run_id}")
    case_manifest_path = Path(case_manifest_value)
    if not case_manifest_path.is_absolute():
        case_manifest_path = Path.cwd() / case_manifest_path
    if not case_manifest_path.is_file():
        raise RunnerContractError(
            f"S2 freeze case manifest does not exist: {freeze_run_id}"
        )
    actual_case_sha256 = hashlib.sha256(
        case_manifest_path.read_bytes()
    ).hexdigest().upper()
    if actual_case_sha256 != declared["case_manifest_sha256"]:
        raise RunnerContractError(
            f"S2 freeze case manifest hash mismatch: {freeze_run_id}"
        )
    frozen_q_manifest = _read_json_object(case_manifest_path)
    if expected_q_manifest is None:
        if contract is None or s2_contract_path is None:
            raise RunnerContractError("exact contract is required for freeze validation")
        generated = syn_core.build_syn_edt_case_manifest(contract, s2_contract_path)
        if not isinstance(generated, Mapping):
            raise RunnerContractError("case generator did not return a mapping")
        expected_q_manifest = _q_only_manifest(generated)
    if _canonical_json_bytes(frozen_q_manifest) != _canonical_json_bytes(
        expected_q_manifest
    ):
        raise RunnerContractError(
            f"S2 freeze case manifest differs from exact contracts: {freeze_run_id}"
        )
    return S2FreezeBinding(
        run_id=freeze_run_id,
        case_manifest_path=case_manifest_path,
        case_manifest_sha256=declared["case_manifest_sha256"],
        s0_sha256=declared["s0_sha256"],
        s2_sha256=declared["s2_sha256"],
    )


def _assert_no_orphan_s2_intents(experiment_root: Path) -> None:
    """Fail closed when an S2 intent/claim has no finalized manifest.

    A process interruption after intent persistence is evidence that the frozen
    solver intent was consumed.  Automatic replay would silently change the
    failure accounting, so only an explicit reconciliation may clear the gate.
    """

    finalized_run_ids = {
        str(manifest.get("run_id", ""))
        for manifest in _existing_case_manifests(experiment_root)
    }
    candidates = (
        (
            experiment_root / "intents",
            frozenset({"syn-edt-s2-case-intent-v1"}),
        ),
        (
            experiment_root / "intent_claims",
            frozenset({"syn-edt-s2-intent-claim-v1"}),
        ),
    )
    for root, schemas in candidates:
        if not root.exists():
            continue
        for path in sorted(root.glob("*.json")):
            try:
                payload = _read_json_object(path)
            except RunnerContractError as exc:
                raise RunnerContractError(
                    "ORPHAN_S2_INTENT_RECONCILIATION_REQUIRED: "
                    f"unreadable immutable intent evidence {path}"
                ) from exc
            if payload.get("schema_version") not in schemas:
                continue
            run_id = payload.get("run_id")
            if (
                not isinstance(run_id, str)
                or not run_id
                or payload.get("physical_contract_id") != PHYSICAL_CONTRACT_ID
                or payload.get("split_id") != SPLIT_ID
                or run_id not in finalized_run_ids
            ):
                raise RunnerContractError(
                    "ORPHAN_S2_INTENT_RECONCILIATION_REQUIRED: "
                    f"{path}; do not auto-replay or replace the consumed intent"
                )


def _claim_s2_intent(
    experiment_root: Path,
    *,
    run_id: str,
    intent: S2Intent,
    started_at: str,
    s0_sha256: str,
    s2_sha256: str,
) -> Path:
    """Atomically and immutably claim one frozen ladder row across processes."""

    claim_path = (
        experiment_root
        / "intent_claims"
        / f"s2-intent-{intent.number:02d}.json"
    )
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "syn-edt-s2-intent-claim-v1",
        "run_id": run_id,
        "started_at": started_at,
        "physical_contract_id": PHYSICAL_CONTRACT_ID,
        "split_id": SPLIT_ID,
        "ladder": intent.to_dict(),
        "s0_sha256": s0_sha256,
        "s2_sha256": s2_sha256,
        "disposition_if_unfinalized": (
            "ORPHAN_S2_INTENT_RECONCILIATION_REQUIRED_NO_AUTOMATIC_REPLAY"
        ),
    }
    encoded = (
        json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    try:
        descriptor = os.open(claim_path, flags, 0o644)
    except FileExistsError as exc:
        raise RunnerContractError(
            "S2_INTENT_CLAIM_RECONCILIATION_REQUIRED: "
            f"frozen intent {intent.number} already has immutable claim evidence"
        ) from exc
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        # The exclusive file is intentionally retained.  A partial claim is an
        # orphan requiring reconciliation, never permission for an auto-retry.
        raise
    return claim_path


def _assert_intent_order(experiment_root: Path, intent: S2Intent) -> None:
    prior = _existing_case_manifests(experiment_root)
    by_number: dict[int, dict[str, Any]] = {}
    for manifest in prior:
        actual = manifest.get("actual_budget")
        if not isinstance(actual, Mapping):
            raise RunnerContractError("prior S2 case manifest lacks actual_budget")
        try:
            number = int(actual["s2_intent"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RunnerContractError("prior S2 case manifest lacks intent identity") from exc
        if number in by_number:
            raise RunnerContractError("duplicate S2 intent already exists in the ledger")
        by_number[number] = manifest
    if intent.number in by_number:
        raise RunnerContractError(f"S2 intent {intent.number} is already finalized")
    expected = set(range(1, intent.number))
    if set(by_number) != expected:
        raise RunnerContractError(
            f"S2 intent {intent.number} requires finalized intents 1..{intent.number - 1}"
        )
    if any(item.get("execution_status") != "COMPLETED" for item in by_number.values()):
        raise RunnerContractError("S2 must stop after an execution-invalid intent")


def _result_report(result: Any, intent: S2Intent) -> dict[str, Any]:
    method = getattr(result, "to_report_dict", None)
    if callable(method):
        report = method()
    else:
        report = {
            "event_report": _jsonable(getattr(result, "event_report", None)),
            "guard_report": _jsonable(getattr(result, "guard_report", None)),
        }
    if not isinstance(report, Mapping):
        raise RunnerContractError("oracle result report is not a mapping")
    event = report.get("event_report")
    guards = report.get("guard_report")
    if not isinstance(event, Mapping) or not isinstance(guards, Mapping):
        raise RunnerContractError("oracle result lacks explicit event or guard report")
    return {
        "schema_version": "syn-edt-s2-case-report-v1",
        "physical_contract_id": PHYSICAL_CONTRACT_ID,
        "split_id": SPLIT_ID,
        "ladder": intent.to_dict(),
        **_jsonable(report),
    }


def run_freeze_cases(
    *,
    run_id: str,
    supersedes_freeze_run_id: str | None = None,
    s0_contract_path: Path,
    s2_contract_path: Path,
    output_root: Path,
    experiment_root: Path,
) -> int:
    bundle = _load_contract_bundle(s0_contract_path, s2_contract_path)
    ExperimentLedger(experiment_root).validate()
    _validate_run_id(run_id)
    if supersedes_freeze_run_id is not None:
        if supersedes_freeze_run_id == run_id:
            raise RunnerContractError("an S2 freeze cannot supersede itself")
        _load_completed_freeze_manifest(experiment_root, supersedes_freeze_run_id)
    s0_sha256 = hashlib.sha256(s0_contract_path.read_bytes()).hexdigest().upper()
    s2_sha256 = hashlib.sha256(s2_contract_path.read_bytes()).hexdigest().upper()
    started_at = _utc_now()
    wall_start, cpu_start = time.perf_counter(), time.process_time()
    run_root = _new_run_root(output_root, run_id)
    intent_path = experiment_root / "intents" / f"{run_id}.json"
    command = [
        "python",
        "-m",
        "pinn_pcm_sci.syn_edt_2d_runner",
        "freeze-cases",
        "--run-id",
        run_id,
    ]
    if supersedes_freeze_run_id is not None:
        command.extend(
            ["--supersedes-freeze-run-id", supersedes_freeze_run_id]
        )
    intent_payload: dict[str, Any] = {
        "schema_version": "syn-edt-s2-freeze-intent-v1",
        "run_id": run_id,
        "started_at": started_at,
        "physical_contract_id": PHYSICAL_CONTRACT_ID,
        "scope": "S2_Q_ONLY",
        "formal_or_reserve_access": False,
        "s0_sha256": s0_sha256,
        "s2_sha256": s2_sha256,
    }
    if supersedes_freeze_run_id is not None:
        intent_payload["supersedes_freeze_run_id"] = supersedes_freeze_run_id
    _write_json_once(
        intent_path,
        intent_payload,
    )
    artifacts = {
        "intent": str(intent_path),
        "run_root": str(run_root),
        "s0_sha256": s0_sha256,
        "s2_sha256": s2_sha256,
    }
    failure: BaseException | None = None
    outcome = "SYN_EDT_S2_Q_CASE_MANIFEST_FREEZE_FAILED"
    try:
        generated = syn_core.build_syn_edt_case_manifest(
            bundle.physical_contract, s2_contract_path
        )
        if not isinstance(generated, Mapping):
            raise RunnerContractError("case generator did not return a mapping")
        q_manifest = _q_only_manifest(generated)
        manifest_path = run_root / "case-manifest-q-only.json"
        _write_json_once(manifest_path, q_manifest)
        artifacts["case_manifest"] = str(manifest_path)
        artifacts["case_manifest_sha256"] = hashlib.sha256(
            manifest_path.read_bytes()
        ).hexdigest().upper()
        outcome = "SYN_EDT_S2_Q_CASE_MANIFEST_FROZEN"
    except Exception as exc:
        failure = exc
    actual = _accounting(
        intent_id=run_id,
        method_id=CASE_GENERATOR_METHOD_ID,
        case_id="syn-edt-2d-v1-s2-q-pool",
        wall_start=wall_start,
        cpu_start=cpu_start,
        solver_intents=0,
        failed_intents=0,
        failure=failure,
    )
    _record_manifest(
        experiment_root=experiment_root,
        run_id=run_id,
        tier="smoke",
        scientific_role="contract_freeze",
        gate="S2_CASE_FREEZE",
        started_at=started_at,
        command=command,
        execution_status="FAILED" if failure else "COMPLETED",
        numerical_validity="NOT_APPLICABLE_PREREGISTRATION",
        gate_outcome=outcome,
        route_disposition=(
            "S2_CASE_FREEZE_EXECUTION_INVALID" if failure else "CONTINUE_S2"
        ),
        claim_status="NO_NUMERICAL_EVIDENCE_CASE_MANIFEST_ONLY",
        method_id=CASE_GENERATOR_METHOD_ID,
        case_id="syn-edt-2d-v1-s2-q-pool",
        planned_budget=_planned_budget(bundle, None),
        actual_budget=actual,
        artifacts=artifacts,
        failure=failure,
        supersedes=supersedes_freeze_run_id,
    )
    return 1 if failure else 0


def run_case(
    *,
    run_id: str,
    intent_number: int,
    freeze_run_id: str,
    s0_contract_path: Path,
    s2_contract_path: Path,
    output_root: Path,
    experiment_root: Path,
) -> int:
    bundle = _load_contract_bundle(s0_contract_path, s2_contract_path)
    if not 1 <= intent_number <= len(bundle.ladder):
        raise RunnerContractError(
            f"run-case intent must be in 1..{len(bundle.ladder)}"
        )
    intent = bundle.ladder[intent_number - 1]
    _validate_run_id(run_id)
    ledger = ExperimentLedger(experiment_root)
    ledger.validate()
    s0_sha256 = hashlib.sha256(s0_contract_path.read_bytes()).hexdigest().upper()
    s2_sha256 = hashlib.sha256(s2_contract_path.read_bytes()).hexdigest().upper()
    freeze_binding = _validate_freeze_binding(
        experiment_root,
        freeze_run_id,
        contract=bundle.physical_contract,
        s2_contract_path=s2_contract_path,
        expected_s0_sha256=s0_sha256,
        expected_s2_sha256=s2_sha256,
    )
    _assert_no_orphan_s2_intents(experiment_root)
    _assert_intent_order(experiment_root, intent)
    started_at = _utc_now()
    wall_start, cpu_start = time.perf_counter(), time.process_time()
    claim_path = _claim_s2_intent(
        experiment_root,
        run_id=run_id,
        intent=intent,
        started_at=started_at,
        s0_sha256=s0_sha256,
        s2_sha256=s2_sha256,
    )
    run_root = _new_run_root(output_root, run_id)
    intent_path = experiment_root / "intents" / f"{run_id}.json"
    command = [
        "python",
        "-m",
        "pinn_pcm_sci.syn_edt_2d_runner",
        "run-case",
        "--run-id",
        run_id,
        "--intent",
        str(intent.number),
        "--freeze-run-id",
        freeze_run_id,
    ]
    case_intent_payload = {
            "schema_version": "syn-edt-s2-case-intent-v1",
            "run_id": run_id,
            "started_at": started_at,
            "physical_contract_id": PHYSICAL_CONTRACT_ID,
            "split_id": SPLIT_ID,
            "ladder": intent.to_dict(),
            "case_pool": "Q",
            "formal_or_reserve_access": False,
            "freeze_run_id": freeze_run_id,
            "claim_path": str(claim_path),
            "s0_sha256": s0_sha256,
            "s2_sha256": s2_sha256,
            "planned_budget": _planned_budget(bundle, intent),
    }
    case_intent_payload.update(freeze_binding.manifest_fields())
    _write_json_once(intent_path, case_intent_payload)
    artifacts = {
        "intent_claim": str(claim_path),
        "intent": str(intent_path),
        "run_root": str(run_root),
    }
    artifacts.update(freeze_binding.manifest_fields())
    failure: BaseException | None = None
    result: Any | None = None
    solver_statistics: dict[str, int | float] = {}
    case_identity = f"syn-edt-2d-v1-{intent.qualification_case.lower()}"
    outcome = "SYN_EDT_S2_EXECUTION_FAILED"
    numerical_validity = "NOT_EVALUATED"
    try:
        case = syn_core.SynEdtCaseSpec.qualification(
            intent.qualification_case, bundle.physical_contract
        )
        resolution = syn_core.SynEdtResolution.from_levels(
            intent.space_level, intent.time_level, bundle.physical_contract
        )
        control = syn_core.SynEdtControl[intent.control_name]
        result = syn_core.SynEdtOracleCase(
            contract=bundle.physical_contract,
            case=case,
            resolution=resolution,
            control=control,
        ).solve()
        solver_statistics = _exact_solver_statistics(result)
        report = _result_report(result, intent)
        case_identity = str(
            report.get("case_id", getattr(case, "case_id", case_identity))
        )
        artifact = syn_core.syn_edt_result_to_artifact(
            result,
            bundle.physical_contract,
            case_identity,
            "SYN_EDT_2D_V1_S2_NOT_YET_QUALIFIED",
        )
        if not isinstance(artifact, CaseArtifact):
            raise RunnerContractError("oracle did not produce a CaseArtifact")
        suffix = (
            f"{intent.space_level}-{intent.time_level}-"
            f"{intent.control_name.lower()}"
        )
        artifact_path = run_root / (
            f"case-{intent.qualification_case.lower()}-intent-{intent.number:02d}-"
            f"{suffix}.h5"
        )
        artifact.write(artifact_path)
        artifact_sha256 = hashlib.sha256(
            artifact_path.read_bytes()
        ).hexdigest().upper()
        evaluation = syn_eval.artifact_from_oracle_result(
            result,
            physical=bundle.physical_contract.physical,
            numerical=bundle.s2_payload,
            s0_sha256=s0_sha256,
            numerical_contract_sha256=s2_sha256,
        )
        evaluation_path = run_root / (
            f"evaluation-{intent.qualification_case.lower()}-"
            f"intent-{intent.number:02d}.npz"
        )
        evaluation.write(evaluation_path)
        evaluation_sha256 = hashlib.sha256(
            evaluation_path.read_bytes()
        ).hexdigest().upper()
        report_path = run_root / "report.json"
        _write_json_once(report_path, report)
        report_sha256 = hashlib.sha256(report_path.read_bytes()).hexdigest().upper()
        artifacts.update(
            {
                "case": str(artifact_path),
                "case_sha256": artifact_sha256,
                "evaluation": str(evaluation_path),
                "evaluation_sha256": evaluation_sha256,
                "report": str(report_path),
                "report_sha256": report_sha256,
            }
        )
        outcome = "SYN_EDT_S2_CASE_COMPLETED"
        numerical_validity = "PENDING_S2_CROSS_RUN_ADJUDICATION"
    except Exception as exc:
        failure = exc
    actual = _accounting(
        intent_id=run_id,
        method_id=ORACLE_METHOD_ID,
        case_id=case_identity,
        wall_start=wall_start,
        cpu_start=cpu_start,
        solver_intents=1,
        failed_intents=1 if failure else 0,
        failure=failure,
        intent=intent,
        solver_statistics=solver_statistics,
    )
    _record_manifest(
        experiment_root=experiment_root,
        run_id=run_id,
        tier="pilot",
        scientific_role="oracle_qualification",
        gate="S2_CASE",
        started_at=started_at,
        command=command,
        execution_status="FAILED" if failure else "COMPLETED",
        numerical_validity=numerical_validity,
        gate_outcome=outcome,
        route_disposition=(
            "SYN_EDT_S2_EXECUTION_INVALID_STOP" if failure else "AWAIT_S2_SUMMARY"
        ),
        claim_status="NO_ORACLE_EVENT_OR_METHOD_CLAIM_SINGLE_CASE_ONLY",
        method_id=ORACLE_METHOD_ID,
        case_id=case_identity,
        planned_budget=_planned_budget(bundle, intent),
        actual_budget=actual,
        artifacts=artifacts,
        failure=failure,
    )
    return 1 if failure else 0


def _load_selected_case_runs(
    experiment_root: Path,
    run_ids: Sequence[str],
    ladder: tuple[S2Intent, ...],
    *,
    expected_s0_sha256: str,
    expected_numerical_sha256: str,
    expected_q_manifest: Mapping[str, Any],
) -> tuple[
    dict[int, dict[str, Any]],
    dict[int, dict[str, Any]],
    dict[int, CaseArtifact],
    dict[int, Any],
]:
    if len(run_ids) != len(ladder) or len(set(run_ids)) != len(ladder):
        raise RunnerContractError(
            "summarize-s2 requires one unique case run ID per frozen intent"
        )
    manifests: dict[int, dict[str, Any]] = {}
    reports: dict[int, dict[str, Any]] = {}
    artifacts: dict[int, CaseArtifact] = {}
    evaluation_artifacts: dict[int, Any] = {}
    common_freeze_binding: tuple[str, str, str, str] | None = None
    for run_id in run_ids:
        manifest_path = experiment_root / "manifests" / f"{run_id}.json"
        manifest = _read_json_object(manifest_path)
        if (
            manifest.get("experiment_group_id") != EXPERIMENT_GROUP_ID
            or manifest.get("gate") != "S2_CASE"
            or manifest.get("physical_contract_id") != PHYSICAL_CONTRACT_ID
        ):
            raise RunnerContractError(f"run is not an S2 SYN_EDT case: {run_id}")
        actual = manifest.get("actual_budget")
        if not isinstance(actual, Mapping):
            raise RunnerContractError(f"run lacks accounting: {run_id}")
        try:
            number = int(actual["s2_intent"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RunnerContractError(f"run lacks intent identity: {run_id}") from exc
        if number in manifests or not 1 <= number <= len(ladder):
            raise RunnerContractError("selected runs duplicate or exceed the S2 ladder")
        expected = ladder[number - 1]
        observed = {
            "intent": number,
            "case": actual.get("qualification_case"),
            "space": actual.get("space_level"),
            "time": actual.get("time_level"),
            "control": actual.get("control"),
        }
        if expected.role is not None:
            observed["role"] = actual.get("intent_role")
        if observed != expected.to_dict() or actual.get("case_pool") != "Q":
            raise RunnerContractError(f"run differs from frozen ladder row {number}")
        artifact_map = manifest.get("artifacts")
        if not isinstance(artifact_map, Mapping):
            raise RunnerContractError(f"run lacks artifacts: {run_id}")
        observed_freeze_binding = tuple(
            str(artifact_map.get(key, ""))
            for key in (
                "freeze_run_id",
                "case_manifest_sha256",
                "s0_sha256",
                "s2_sha256",
            )
        )
        if (
            any(not value for value in observed_freeze_binding)
            or observed_freeze_binding[1] != observed_freeze_binding[1].upper()
            or observed_freeze_binding[2] != expected_s0_sha256.upper()
            or observed_freeze_binding[3] != expected_numerical_sha256.upper()
        ):
            raise RunnerContractError(
                f"case run lacks current S2 freeze binding: {run_id}"
            )
        if common_freeze_binding is None:
            common_freeze_binding = observed_freeze_binding
        elif observed_freeze_binding != common_freeze_binding:
            raise RunnerContractError(
                "selected case runs must share the same S2 freeze binding"
            )
        report_path = Path(str(artifact_map.get("report", "")))
        artifact_path = Path(str(artifact_map.get("case", "")))
        evaluation_path = Path(str(artifact_map.get("evaluation", "")))
        if not report_path.is_absolute():
            report_path = Path.cwd() / report_path
        if not artifact_path.is_absolute():
            artifact_path = Path.cwd() / artifact_path
        if not evaluation_path.is_absolute():
            evaluation_path = Path.cwd() / evaluation_path
        for key, path in (
            ("case", artifact_path),
            ("report", report_path),
            ("evaluation", evaluation_path),
        ):
            _verify_artifact_sha256(
                artifact_map,
                key=key,
                path=path,
                run_id=run_id,
            )
        report = _read_json_object(report_path)
        if report.get("ladder") != expected.to_dict():
            raise RunnerContractError(f"report differs from ladder row {number}")
        if not isinstance(report.get("event_report"), Mapping) or not isinstance(
            report.get("guard_report"), Mapping
        ):
            raise RunnerContractError(f"run lacks event or guard record: {run_id}")
        report_case_manifest = report.get("case_manifest")
        if not isinstance(report_case_manifest, Mapping) or any(
            observed != expected_identity
            for observed, expected_identity in (
                (report.get("case_id"), manifest.get("case_id")),
                (report.get("physical_contract_id"), PHYSICAL_CONTRACT_ID),
                (
                    report_case_manifest.get("physical_contract_id"),
                    PHYSICAL_CONTRACT_ID,
                ),
                (report_case_manifest.get("s0_sha256"), expected_s0_sha256),
                (
                    report_case_manifest.get("s2_numerical_sha256"),
                    expected_numerical_sha256,
                ),
            )
        ):
            raise RunnerContractError(f"report artifact contract mismatch: {run_id}")
        case_artifact = CaseArtifact.read(artifact_path)
        if (
            case_artifact.case_id != str(manifest.get("case_id"))
            or case_artifact.physical_contract_id != PHYSICAL_CONTRACT_ID
        ):
            raise RunnerContractError(f"case artifact identity mismatch: {run_id}")
        manifests[number] = manifest
        reports[number] = report
        artifacts[number] = case_artifact
        evaluation = syn_eval.SynEdtEvaluationArtifact.read(evaluation_path)
        if (
            evaluation.physical_contract_id != PHYSICAL_CONTRACT_ID
            or evaluation.case_id != str(manifest.get("case_id"))
            or evaluation.s0_sha256.upper() != expected_s0_sha256.upper()
            or evaluation.numerical_contract_sha256.upper()
            != expected_numerical_sha256.upper()
        ):
            raise RunnerContractError(f"evaluator artifact contract mismatch: {run_id}")
        evaluation_artifacts[number] = evaluation
    if set(manifests) != set(range(1, len(ladder) + 1)):
        raise RunnerContractError("selected runs do not cover the complete frozen ladder")
    if common_freeze_binding is None:
        raise RunnerContractError("selected case runs lack an S2 freeze binding")
    validated_freeze = _validate_freeze_binding(
        experiment_root,
        common_freeze_binding[0],
        expected_q_manifest=expected_q_manifest,
        expected_s0_sha256=expected_s0_sha256,
        expected_s2_sha256=expected_numerical_sha256,
    )
    if (
        validated_freeze.case_manifest_sha256,
        validated_freeze.s0_sha256,
        validated_freeze.s2_sha256,
    ) != common_freeze_binding[1:]:
        raise RunnerContractError(
            "selected case runs differ from their validated S2 freeze binding"
        )
    return manifests, reports, artifacts, evaluation_artifacts


def _comparison_payload(value: Any) -> dict[str, Any]:
    payload = _jsonable(value)
    if not isinstance(payload, dict):
        raise RunnerContractError("cross-run comparison did not return a mapping")
    return payload


def _verify_artifact_sha256(
    artifact_map: Mapping[str, Any],
    *,
    key: str,
    path: Path,
    run_id: str,
) -> None:
    declared = str(artifact_map.get(f"{key}_sha256", "")).upper()
    if not declared or not path.is_file():
        raise RunnerContractError(f"run lacks {key} artifact identity: {run_id}")
    actual = hashlib.sha256(path.read_bytes()).hexdigest().upper()
    if actual != declared:
        raise RunnerContractError(f"{key} artifact hash mismatch: {run_id}")


def _numeric_matrix(
    record: Mapping[str, Any],
    key: str,
    *,
    rows: int,
    columns: int,
    allow_none: bool,
) -> list[list[float | None]] | None:
    raw = record.get(key)
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return None
    if len(raw) != rows:
        return None
    matrix: list[list[float | None]] = []
    for raw_row in raw:
        if not isinstance(raw_row, Sequence) or isinstance(raw_row, (str, bytes)):
            return None
        if len(raw_row) != columns:
            return None
        row: list[float | None] = []
        for raw_value in raw_row:
            if raw_value is None:
                if not allow_none:
                    return None
                row.append(None)
                continue
            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                return None
            if not np.isfinite(value):
                return None
            row.append(value)
        matrix.append(row)
    return matrix


def _not_ready_record(reason: str) -> dict[str, Any]:
    return {"sealed": False, "finite": False, "ready": False, "reason": reason}


def _numeric_series(
    record: Mapping[str, Any],
    key: str,
    *,
    length: int,
    allow_none: bool,
) -> list[float | None] | None:
    raw = record.get(key)
    if (
        not isinstance(raw, Sequence)
        or isinstance(raw, (str, bytes))
        or len(raw) != length
    ):
        return None
    values: list[float | None] = []
    for raw_value in raw:
        if raw_value is None:
            if not allow_none:
                return None
            values.append(None)
            continue
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            return None
        if not np.isfinite(value):
            return None
        values.append(value)
    return values


def _floor_current_normalizers(
    floor_record: Mapping[str, Any], *, cycles: int
) -> list[float] | None:
    if (
        floor_record.get("schema_version") != syn_eval.FLOOR_SCHEMA
        or floor_record.get("sealed_before_neural_work") is not True
        or not isinstance(floor_record.get("seal_sha256"), str)
        or not floor_record.get("seal_sha256")
    ):
        return None
    source_case_id = floor_record.get("source_case_id")
    normalizers_by_case = floor_record.get("normalizers_by_case")
    if not isinstance(source_case_id, str) or not isinstance(
        normalizers_by_case, Mapping
    ):
        return None
    raw = normalizers_by_case.get(source_case_id)
    if (
        not isinstance(raw, Sequence)
        or isinstance(raw, (str, bytes))
        or len(raw) != cycles
    ):
        return None
    normalizers: list[float] = []
    for item in raw:
        if not isinstance(item, Mapping):
            return None
        try:
            value = float(item["port_current"])
        except (KeyError, TypeError, ValueError):
            return None
        if not np.isfinite(value) or value <= 0.0:
            return None
        normalizers.append(value)
    return normalizers


def _normalized_thermal_deltas(
    record: Mapping[str, Any],
    *,
    current_normalizers: Sequence[float],
    cycles: int,
) -> list[list[float | None]] | None:
    deltas = _numeric_matrix(
        record,
        "thermal_component_deltas_by_cycle",
        rows=cycles,
        columns=3,
        allow_none=True,
    )
    current = _numeric_series(
        record,
        "thermal_current_rms_difference_a_by_cycle",
        length=cycles,
        allow_none=True,
    )
    if deltas is None or current is None or len(current_normalizers) != cycles:
        return None
    normalized: list[list[float | None]] = []
    for cycle in range(cycles):
        peak, event, placeholder = deltas[cycle]
        raw_current = current[cycle]
        if placeholder is not None:
            return None
        if any(value is not None and value < 0.0 for value in (peak, event, raw_current)):
            return None
        normalized.append(
            [
                peak,
                event,
                None
                if raw_current is None
                else float(raw_current) / float(current_normalizers[cycle]),
            ]
        )
    return normalized


def _event_time_state(report: Mapping[str, Any], *, cycles: int) -> str:
    event = report.get("event_report")
    if not isinstance(event, Mapping):
        return "INVALID"
    raw = event.get("event_time_s")
    if (
        not isinstance(raw, Sequence)
        or isinstance(raw, (str, bytes))
        or len(raw) != cycles
    ):
        return "INVALID"
    finite: list[bool] = []
    for value in raw:
        if value is None:
            finite.append(False)
            continue
        try:
            finite.append(bool(np.isfinite(float(value))))
        except (TypeError, ValueError):
            return "INVALID"
    if all(finite):
        return "FINITE"
    if not any(finite) and all(value is None for value in raw):
        return "ALL_MISSING"
    return "MIXED_OR_INVALID"


def _signed_series(
    record: Mapping[str, Any], key: str, *, cycles: int
) -> list[float] | None:
    raw_mapping = record.get("thermal_effect_signed_by_cycle")
    if not isinstance(raw_mapping, Mapping):
        return None
    raw = raw_mapping.get(key)
    if (
        not isinstance(raw, Sequence)
        or isinstance(raw, (str, bytes))
        or len(raw) != cycles
    ):
        return None
    values: list[float] = []
    for item in raw:
        if item is None:
            return None
        try:
            value = float(item)
        except (TypeError, ValueError):
            return None
        if not np.isfinite(value):
            return None
        values.append(value)
    return values


def _same_nonzero_sign(values: Sequence[float] | None) -> bool:
    if values is None or not values or any(value == 0.0 for value in values):
        return False
    return all(value > 0.0 for value in values) or all(value < 0.0 for value in values)


def _thermal_effect_record(
    *,
    comparisons: Mapping[str, Mapping[str, Any]],
    reports: Mapping[int, Mapping[str, Any]],
    floor_record: Mapping[str, Any],
    effect_name: str,
    control_uncertainty_name: str,
    control_intent: int,
    numerical_contract: Mapping[str, Any],
    cycles: int,
) -> dict[str, Any]:
    current_normalizers = _floor_current_normalizers(floor_record, cycles=cycles)
    if current_normalizers is None:
        return {"ready": False, "reason": "CANONICAL_CURRENT_NORMALIZERS_NOT_READY"}
    source_names = (
        "space_medium_fine",
        "time_medium_fine",
        "independent_process_replay",
        control_uncertainty_name,
    )
    if any(not isinstance(comparisons.get(name), Mapping) for name in (*source_names, effect_name)):
        return {"ready": False, "reason": "THERMAL_COMPARISON_MISSING"}
    uncertainty_sources: dict[str, list[list[float | None]]] = {}
    for name in source_names:
        converted = _normalized_thermal_deltas(
            comparisons[name],
            current_normalizers=current_normalizers,
            cycles=cycles,
        )
        if converted is None:
            return {"ready": False, "reason": f"{name.upper()}_THERMAL_DELTAS_MISSING"}
        uncertainty_sources[name] = converted
    effect = _normalized_thermal_deltas(
        comparisons[effect_name],
        current_normalizers=current_normalizers,
        cycles=cycles,
    )
    if effect is None:
        return {"ready": False, "reason": "THERMAL_EFFECT_DELTAS_MISSING"}
    endpoint = numerical_contract.get("endpoint_and_floor_contract")
    if not isinstance(endpoint, Mapping):
        return {"ready": False, "reason": "THERMAL_FLOOR_CONTRACT_MISSING"}
    try:
        solver_floor = 2.0 * float(
            endpoint["declared_solver_tolerance_each_dimensionless_component"]
        )
    except (KeyError, TypeError, ValueError):
        return {"ready": False, "reason": "THERMAL_SOLVER_FLOOR_INVALID"}
    uncertainty: list[list[float | None]] = []
    for cycle in range(cycles):
        row: list[float | None] = []
        for component in range(3):
            values = [
                uncertainty_sources[name][cycle][component] for name in source_names
            ]
            row.append(
                None
                if any(value is None for value in values)
                else max(solver_floor, *(float(value) for value in values))
            )
        uncertainty.append(row)
    signed_peak = _signed_series(comparisons[effect_name], "peak_depletion", cycles=cycles)
    signed_event = _signed_series(comparisons[effect_name], "event_time", cycles=cycles)
    sign_consistent = {
        "peak_depletion": _same_nonzero_sign(signed_peak),
        "event_time": _same_nonzero_sign(signed_event),
        "current_trace_rms": True,
    }
    component_names = ("peak_depletion", "event_time", "current_trace_rms")
    passes: dict[str, bool] = {}
    for component, name in enumerate(component_names):
        finite_pair = all(
            effect[cycle][component] is not None
            and uncertainty[cycle][component] is not None
            for cycle in range(cycles)
        )
        exceeds = finite_pair and all(
            float(effect[cycle][component]) > float(uncertainty[cycle][component])
            for cycle in range(cycles)
        )
        passes[name] = bool(exceeds and sign_consistent[name])
    nominal_event = reports.get(6, {}).get("event_report")
    control_guard = reports.get(control_intent, {}).get("guard_report")
    nominal_state = _event_time_state(reports.get(6, {}), cycles=cycles)
    control_state = _event_time_state(reports.get(control_intent, {}), cycles=cycles)
    if nominal_state == "INVALID" or control_state == "INVALID":
        return {"ready": False, "reason": "THERMAL_EVENT_STATE_INVALID"}
    if nominal_state == "MIXED_OR_INVALID" or control_state == "MIXED_OR_INVALID":
        return {
            "ready": True,
            "effect_exceeds_numerical_uncertainty": False,
            "reason": "MIXED_OR_SINGLE_CYCLE_CENSORING",
            "nominal_event_state": nominal_state,
            "control_event_state": control_state,
        }
    censored = bool(
        isinstance(nominal_event, Mapping)
        and nominal_event.get("passed") is True
        and isinstance(control_guard, Mapping)
        and control_guard.get("passed") is True
        and nominal_state == "FINITE"
        and control_state == "ALL_MISSING"
    )
    structurally_ready = all(
        effect[cycle][component] is not None
        and uncertainty[cycle][component] is not None
        for cycle in range(cycles)
        for component in (0, 2)
    )
    if not structurally_ready:
        return {"ready": False, "reason": "THERMAL_EFFECT_INPUT_NOT_EVALUABLE"}
    passed = bool(censored or any(passes.values()))
    return {
        "ready": True,
        "effect_exceeds_numerical_uncertainty": passed,
        "effect_components": list(component_names),
        "effect_by_cycle": effect,
        "uncertainty_by_cycle": uncertainty,
        "uncertainty_sources_by_cycle": uncertainty_sources,
        "current_normalizers_by_cycle_a": current_normalizers,
        "component_passes_both_cycles": passes,
        "sign_consistent": sign_consistent,
        "signed_effect_by_cycle": {
            "peak_depletion": signed_peak,
            "event_time": signed_event,
        },
        "censored_event_pass": censored,
        "nominal_event_state": nominal_state,
        "control_event_state": control_state,
    }


def _build_s2_summary(
    *,
    contract: Any,
    numerical_contract: Mapping[str, Any],
    manifests: Mapping[int, Mapping[str, Any]],
    reports: Mapping[int, Mapping[str, Any]],
    artifacts: Mapping[int, CaseArtifact],
    floor_seal: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if any(item.get("execution_status") != "COMPLETED" for item in manifests.values()):
        return {
            "schema_version": "syn-edt-s2-summary-v1",
            "adjudicated": False,
            "passed": False,
            "outcome": "S2_NOT_ADJUDICATED",
            "reason": "ONE_OR_MORE_CASE_RUNS_EXECUTION_INVALID",
        }
    comparator = getattr(syn_core, "compare_syn_edt_artifacts", None)
    if not callable(comparator):
        return {
            "schema_version": "syn-edt-s2-summary-v1",
            "adjudicated": False,
            "passed": False,
            "outcome": "S2_NOT_ADJUDICATED",
            "reason": "ARTIFACT_LEVEL_COMPARATOR_UNAVAILABLE",
        }
    pairs = {
        "space_coarse_medium": (2, 3),
        "space_medium_fine": (3, 6),
        "time_coarse_medium": (4, 5),
        "time_medium_fine": (5, 6),
        "direct_transport_medium_fine": (9, 10),
        "isothermal_medium_fine": (11, 12),
        "independent_process_replay": (6, 13),
        "full_vs_direct_thermal_effect": (6, 10),
        "full_vs_isothermal_thermal_effect": (6, 12),
    }
    comparisons: dict[str, Any] = {}
    try:
        for name, (left, right) in pairs.items():
            comparisons[name] = _comparison_payload(
                comparator(
                    artifacts[left],
                    artifacts[right],
                    reports[left],
                    reports[right],
                    contract,
                )
            )
    except Exception as exc:
        return {
            "schema_version": "syn-edt-s2-summary-v1",
            "adjudicated": False,
            "passed": False,
            "outcome": "S2_NOT_ADJUDICATED",
            "reason": "CROSS_RUN_COMPARISON_FAILED",
            "failure_class": type(exc).__name__,
            "failure": str(exc),
            "comparisons": comparisons,
        }
    try:
        cycles = int(contract.physical["absolute_waveform"]["cycles"])
    except (AttributeError, KeyError, TypeError, ValueError):
        cycles = 0
    if cycles <= 0:
        return {
            "schema_version": "syn-edt-s2-summary-v1",
            "adjudicated": False,
            "passed": False,
            "outcome": "S2_NOT_ADJUDICATED",
            "reason": "FROZEN_CYCLE_COUNT_UNAVAILABLE",
            "comparisons": comparisons,
        }
    floor_record: Mapping[str, Any] = (
        floor_seal
        if isinstance(floor_seal, Mapping)
        else _not_ready_record("EVALUATOR_FLOOR_SEAL_UNAVAILABLE")
    )
    comparisons["endpoint_component_floors"] = floor_record
    direct_thermal_gate = _thermal_effect_record(
        comparisons=comparisons,
        reports=reports,
        floor_record=floor_record,
        effect_name="full_vs_direct_thermal_effect",
        control_uncertainty_name="direct_transport_medium_fine",
        control_intent=10,
        numerical_contract=numerical_contract,
        cycles=cycles,
    )
    isothermal_thermal_gate = _thermal_effect_record(
        comparisons=comparisons,
        reports=reports,
        floor_record=floor_record,
        effect_name="full_vs_isothermal_thermal_effect",
        control_uncertainty_name="isothermal_medium_fine",
        control_intent=12,
        numerical_contract=numerical_contract,
        cycles=cycles,
    )
    comparisons["full_vs_direct_thermal_effect"] = {
        **comparisons["full_vs_direct_thermal_effect"],
        "thermal_gate": direct_thermal_gate,
    }
    comparisons["full_vs_isothermal_thermal_effect"] = {
        **comparisons["full_vs_isothermal_thermal_effect"],
        "thermal_gate": isothermal_thermal_gate,
    }
    required = (
        "space_medium_fine",
        "time_medium_fine",
        "independent_process_replay",
    )
    comparison_records_complete = all(
        isinstance(comparisons[name].get("passed"), bool) for name in required
    )
    event = reports[6]["event_report"]
    intent_numbers = sorted(reports)
    guards = [reports[number]["guard_report"] for number in intent_numbers]
    explicit_event = isinstance(event.get("passed"), bool)
    explicit_guards = all(isinstance(item.get("passed"), bool) for item in guards)
    if not (comparison_records_complete and explicit_event and explicit_guards):
        return {
            "schema_version": "syn-edt-s2-summary-v1",
            "adjudicated": False,
            "passed": False,
            "outcome": "S2_NOT_ADJUDICATED",
            "reason": "MISSING_EXPLICIT_CONVERGENCE_EVENT_OR_GUARD_VERDICT",
            "comparisons": comparisons,
        }
    adjudicator = getattr(syn_core, "adjudicate_syn_edt_s2", None)
    if not callable(adjudicator):
        return {
            "schema_version": "syn-edt-s2-summary-v1",
            "adjudicated": False,
            "passed": False,
            "outcome": "S2_NOT_ADJUDICATED",
            "reason": "FULL_S2_ADJUDICATOR_UNAVAILABLE",
            "event_report": event,
            "guard_reports": {
                str(number): reports[number]["guard_report"]
                for number in intent_numbers
            },
            "comparisons": comparisons,
        }
    adjudication = _comparison_payload(
        adjudicator(reports, comparisons, numerical_contract)
    )
    if not isinstance(adjudication.get("passed"), bool) or not isinstance(
        adjudication.get("adjudicated"), bool
    ):
        raise RunnerContractError("full S2 adjudicator omitted an explicit verdict")
    adjudicated = bool(adjudication["adjudicated"])
    passed = bool(adjudicated and adjudication["passed"])
    return {
        "schema_version": "syn-edt-s2-summary-v1",
        "adjudicated": adjudicated,
        "passed": passed,
        "outcome": (
            "SYN_EDT_S2_PASS_TO_S3"
            if passed
            else (
                "SYN_EDT_S2_HARD_GATE_FAIL_NO_RESCUE"
                if adjudicated
                else "S2_NOT_ADJUDICATED"
            )
        ),
        "reason": adjudication.get("reason"),
        "event_vote_intent": 6,
        "event_report": event,
        "guard_reports": {
            str(number): reports[number]["guard_report"] for number in intent_numbers
        },
        "comparisons": comparisons,
        "adjudication": adjudication,
    }


def run_summarize_s2(
    *,
    run_id: str,
    case_run_ids: Sequence[str],
    s0_contract_path: Path,
    s2_contract_path: Path,
    output_root: Path,
    experiment_root: Path,
) -> int:
    bundle = _load_contract_bundle(s0_contract_path, s2_contract_path)
    ExperimentLedger(experiment_root).validate()
    started_at = _utc_now()
    wall_start, cpu_start = time.perf_counter(), time.process_time()
    run_root = _new_run_root(output_root, run_id)
    intent_path = experiment_root / "intents" / f"{run_id}.json"
    command = [
        "python",
        "-m",
        "pinn_pcm_sci.syn_edt_2d_runner",
        "summarize-s2",
        "--run-id",
        run_id,
    ]
    _write_json_once(
        intent_path,
        {
            "schema_version": "syn-edt-s2-summary-intent-v1",
            "run_id": run_id,
            "started_at": started_at,
            "physical_contract_id": PHYSICAL_CONTRACT_ID,
            "selected_case_run_ids": list(case_run_ids),
            "expected_intents": [item.to_dict() for item in bundle.ladder],
            "formal_or_reserve_access": False,
        },
    )
    artifacts_out = {"intent": str(intent_path), "run_root": str(run_root)}
    failure: BaseException | None = None
    summary: dict[str, Any]
    selected_manifests: dict[int, dict[str, Any]] = {}
    try:
        generated_case_manifest = syn_core.build_syn_edt_case_manifest(
            bundle.physical_contract, s2_contract_path
        )
        if not isinstance(generated_case_manifest, Mapping):
            raise RunnerContractError("case generator did not return a mapping")
        expected_q_manifest = _q_only_manifest(generated_case_manifest)
        current_s0_sha256 = hashlib.sha256(
            s0_contract_path.read_bytes()
        ).hexdigest().upper()
        current_s2_sha256 = hashlib.sha256(
            s2_contract_path.read_bytes()
        ).hexdigest().upper()
        (
            selected_manifests,
            reports,
            case_artifacts,
            evaluation_artifacts,
        ) = _load_selected_case_runs(
            experiment_root,
            case_run_ids,
            bundle.ladder,
            expected_s0_sha256=current_s0_sha256,
            expected_numerical_sha256=current_s2_sha256,
            expected_q_manifest=expected_q_manifest,
        )
        normalizer_cases = {
            evaluation_artifacts[number].case_id: evaluation_artifacts[number]
            for number in (6, 7, 8)
        }
        floor_seal = syn_eval.build_floor_seal(
            reference=evaluation_artifacts[6],
            medium_space=evaluation_artifacts[3],
            medium_time=evaluation_artifacts[5],
            replay=evaluation_artifacts[13],
            physical=bundle.physical_contract.physical,
            numerical=bundle.s2_payload,
            normalizer_cases=normalizer_cases,
        )
        floor_path = run_root / "endpoint-floor-seal.json"
        syn_eval.write_floor_seal(floor_path, floor_seal)
        artifacts_out["floor_seal"] = str(floor_path)
        artifacts_out["floor_seal_sha256"] = hashlib.sha256(
            floor_path.read_bytes()
        ).hexdigest().upper()
        summary = _build_s2_summary(
            contract=bundle.physical_contract,
            numerical_contract=bundle.s2_payload,
            manifests=selected_manifests,
            reports=reports,
            artifacts=case_artifacts,
            floor_seal=floor_seal,
        )
    except syn_eval.NonestimableComponentError as exc:
        summary = {
            "schema_version": "syn-edt-s2-summary-v1",
            "adjudicated": True,
            "passed": False,
            "outcome": "SYN_EDT_S2_HARD_GATE_FAIL_NO_RESCUE",
            "reason": "ORACLE_COMPONENT_NONESTIMABLE",
            "failure_class": type(exc).__name__,
            "failure": str(exc),
        }
    except Exception as exc:
        failure = exc
        summary = {
            "schema_version": "syn-edt-s2-summary-v1",
            "adjudicated": False,
            "passed": False,
            "outcome": "S2_NOT_ADJUDICATED",
            "reason": "SUMMARY_INPUT_INVALID",
            "failure_class": type(exc).__name__,
            "failure": str(exc),
        }
    summary_path = run_root / "summary.json"
    _write_json_once(summary_path, summary)
    artifacts_out["summary"] = str(summary_path)
    aggregate_solver_intents = sum(
        int(item.get("actual_budget", {}).get("solver_intents", 0))
        for item in selected_manifests.values()
    )
    aggregate_failed_intents = sum(
        int(item.get("actual_budget", {}).get("failed_intents", 0))
        for item in selected_manifests.values()
    )
    aggregate_core_hours = sum(
        float(item.get("actual_budget", {}).get("cpu_core_hours", 0.0))
        for item in selected_manifests.values()
    )
    actual = _accounting(
        intent_id=run_id,
        method_id=SUMMARY_METHOD_ID,
        case_id="syn-edt-2d-v1-s2-summary",
        wall_start=wall_start,
        cpu_start=cpu_start,
        solver_intents=0,
        failed_intents=0,
        failure=failure,
    )
    actual.update(
        {
            "aggregated_solver_intents": aggregate_solver_intents,
            "aggregated_failed_intents": aggregate_failed_intents,
            "aggregated_cpu_core_hours": aggregate_core_hours,
            "selected_case_run_count": len(selected_manifests),
        }
    )
    adjudicated = bool(summary.get("adjudicated"))
    passed = bool(summary.get("passed"))
    if failure:
        outcome = "S2_NOT_ADJUDICATED"
        execution_status = "FAILED"
        numerical_validity = "NOT_EVALUATED"
        route = "SYN_EDT_S2_SUMMARY_EXECUTION_INVALID"
    elif not adjudicated:
        outcome = "S2_NOT_ADJUDICATED"
        execution_status = "COMPLETED"
        numerical_validity = "NOT_EVALUATED"
        route = "SYN_EDT_S2_REMAINS_OPEN_NO_PASS_INFERRED"
    elif passed:
        outcome = "SYN_EDT_S2_PASS_TO_S3"
        execution_status = "COMPLETED"
        numerical_validity = "VALID_SYN_EDT_S2_ORACLE_QUALIFICATION"
        route = "CONTINUE_S3"
    else:
        outcome = "SYN_EDT_S2_HARD_GATE_FAIL_NO_RESCUE"
        execution_status = "COMPLETED"
        numerical_validity = "VALID_SYN_EDT_S2_BOUNDED_NEGATIVE"
        route = "CLOSE_SYN_EDT_2D_V1_NO_PARAMETER_OR_TIMESTEP_RESCUE"
    _record_manifest(
        experiment_root=experiment_root,
        run_id=run_id,
        tier="pilot",
        scientific_role="oracle_qualification",
        gate="S2_SUMMARY",
        started_at=started_at,
        command=command,
        execution_status=execution_status,
        numerical_validity=numerical_validity,
        gate_outcome=outcome,
        route_disposition=route,
        claim_status="SYNTHETIC_NUMERICAL_ONLY_NO_METHOD_OR_EXPERIMENTAL_CLAIM",
        method_id=SUMMARY_METHOD_ID,
        case_id="syn-edt-2d-v1-s2-complete-ladder-bundle",
        planned_budget=_planned_budget(bundle, None),
        actual_budget=actual,
        artifacts=artifacts_out,
        failure=failure,
    )
    return 1 if failure else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--s0-contract", type=Path, default=DEFAULT_S0_CONTRACT)
    parser.add_argument("--s2-contract", type=Path, default=DEFAULT_S2_CONTRACT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--experiment-root", type=Path, default=DEFAULT_EXPERIMENT_ROOT
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    freeze = subparsers.add_parser("freeze-cases")
    freeze.add_argument("--run-id", required=True)
    freeze.add_argument("--supersedes-freeze-run-id")

    case = subparsers.add_parser("run-case")
    case.add_argument("--run-id", required=True)
    case.add_argument("--intent", required=True, type=int)
    case.add_argument("--freeze-run-id", required=True)

    summary = subparsers.add_parser("summarize-s2")
    summary.add_argument("--run-id", required=True)
    summary.add_argument(
        "--case-run-id", action="append", required=True, dest="case_run_ids"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    common = {
        "run_id": args.run_id,
        "s0_contract_path": args.s0_contract,
        "s2_contract_path": args.s2_contract,
        "output_root": args.output_root,
        "experiment_root": args.experiment_root,
    }
    if args.command == "freeze-cases":
        return run_freeze_cases(
            supersedes_freeze_run_id=args.supersedes_freeze_run_id, **common
        )
    if args.command == "run-case":
        return run_case(
            intent_number=args.intent,
            freeze_run_id=args.freeze_run_id,
            **common,
        )
    if args.command == "summarize-s2":
        return run_summarize_s2(case_run_ids=args.case_run_ids, **common)
    raise RunnerContractError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
