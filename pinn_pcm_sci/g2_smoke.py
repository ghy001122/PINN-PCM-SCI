from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, BinaryIO

import h5py
import numpy as np

from .artifacts import CaseArtifact, PredictionArtifact
from .ledger import ExperimentLedger, RunManifest
from .qpop_conversion import (
    QPopConversionError,
    QPopConversionRequest,
    convert_qpop_run,
)


_ORPHAN_RECOVERY_GRACE_SECONDS = 2


@dataclass(frozen=True)
class G2SmokeRequest:
    run_id: str
    source_root: Path
    config_root: Path
    output_root: Path
    experiment_root: Path
    environment_facts: dict[str, Any]
    replay_of: str | None = None
    supersedes: str | None = None


class G2SmokeError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class _IntentLease:
    """Process-lifetime ownership for one durable G2 run intent."""

    def __init__(self, path: Path, handle: BinaryIO) -> None:
        self.path = path
        self._handle = handle

    @classmethod
    def try_acquire(cls, path: Path, *, create: bool) -> _IntentLease | None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not create and not path.is_file():
            return None
        handle = path.open("a+b")
        try:
            if path.stat().st_size == 0:
                handle.write(b"\0")
                handle.flush()
                os.fsync(handle.fileno())
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            handle.close()
            if exc.errno in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                return None
            raise
        return cls(path, handle)

    def release(self) -> None:
        try:
            self._handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        finally:
            self._handle.close()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("UTC timestamp must include an offset")
    return parsed.astimezone(timezone.utc)


def _recover_not_before(started_at: str, runtime_spec_path: Path) -> str:
    wall_seconds = 0
    evaluator_seconds = 0
    try:
        runtime = _load_json(runtime_spec_path)
        wall_value = runtime.get("wall_timeout_seconds")
        evaluator_value = runtime.get("evaluator_timeout_seconds")
        if isinstance(wall_value, int) and not isinstance(wall_value, bool) and wall_value > 0:
            wall_seconds = wall_value
        if (
            isinstance(evaluator_value, int)
            and not isinstance(evaluator_value, bool)
            and evaluator_value > 0
        ):
            evaluator_seconds = evaluator_value
    except (OSError, json.JSONDecodeError, G2SmokeError):
        pass
    deadline = _parse_utc(started_at) + timedelta(
        seconds=wall_seconds
        + evaluator_seconds
        + _ORPHAN_RECOVERY_GRACE_SECONDS
    )
    return deadline.isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise G2SmokeError("PREPARATION_CONTRACT_INVALID", f"not a JSON object: {path}")
    return value


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _positive_int(value: Any, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise G2SmokeError(
            "PREPARATION_CONTRACT_INVALID",
            f"{label} must be a strictly positive integer",
        )
    return value


def _expected_wsl_runtime_environment() -> dict[str, str]:
    prefix = "/opt/qpop-cpc-v1-env-g2-final-002"
    petsc_arch = "arch-linux-qpop-opt"
    mpi_prefix = f"{prefix}/openmpi-3.1.6"
    petsc_dir = f"{prefix}/src/petsc"
    dolfin_dir = f"{prefix}/fenics/dolfin"
    provider = f"{prefix}/providers/pybind11-2.2.4"
    return {
        "CC": "/usr/bin/gcc-9",
        "CXX": "/usr/bin/g++-9",
        "FC": "/usr/bin/gfortran-9",
        "MPI_DIR": mpi_prefix,
        "PETSC_DIR": petsc_dir,
        "PETSC_ARCH": petsc_arch,
        "PATH": (
            f"{prefix}/py38/bin:{mpi_prefix}/bin:"
            "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
        ),
        "LD_LIBRARY_PATH": (
            f"{dolfin_dir}/lib:{petsc_dir}/{petsc_arch}/lib:{mpi_prefix}/lib"
        ),
        "PYTHONPATH": f"{petsc_dir}/{petsc_arch}/lib",
        "CMAKE_PREFIX_PATH": (
            f"{provider}:{dolfin_dir}:{petsc_dir}/{petsc_arch}:{mpi_prefix}"
        ),
        "PKG_CONFIG_PATH": f"{dolfin_dir}/lib/pkgconfig",
        "pybind11_DIR": f"{provider}/share/cmake/pybind11",
        "DOLFIN_DIR": f"{dolfin_dir}/share/dolfin/cmake",
        "MPICC": f"{mpi_prefix}/bin/mpicc",
        "OMPI_ALLOW_RUN_AS_ROOT": "1",
        "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
        "PYTHONNOUSERSITE": "1",
    }


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _validate_wsl_environment_facts(
    runtime: dict[str, Any], environment_facts: dict[str, Any]
) -> None:
    if runtime.get("launcher_profile") != "WSL2_QPOP_CPC_V1":
        return
    expected = {
        "schema_version": "qpop-legacy-verification-v1",
        "status": "ENVIRONMENT_VERIFIED",
        "evidence_identity": "ENGINEERING_ABI_AND_FEATURE_QUALIFICATION_ONLY",
        "scientific_claim_status": "NO_SCIENTIFIC_CLAIMS",
        "qpop_started": False,
        "g2_gate_outcome": "NOT_EVALUATED",
        "environment_id": runtime["environment_id"],
        "spec_sha256": runtime["environment_spec_sha256"],
        "resolution_lock_sha256": runtime["resolution_lock_sha256"],
        "build_manifest_sha256": runtime["build_manifest_sha256"],
        "two_rank_import_barrier": "PASS",
    }
    mismatched = [
        key for key, value in expected.items() if environment_facts.get(key) != value
    ]
    if mismatched:
        raise G2SmokeError(
            "PREPARATION_CONTRACT_INVALID",
            "native smoke requires the matching verified environment facts: "
            + ", ".join(mismatched),
        )


def _load_runtime_spec(config_root: Path, conversion_spec: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    path = config_root / "native_runtime.json"
    runtime = _load_json(path)
    if runtime.get("schema_version") != "qpop-native-runtime-v1":
        raise G2SmokeError(
            "PREPARATION_CONTRACT_INVALID",
            "unsupported native runtime schema",
        )
    profile = runtime.get("launcher_profile")
    ranks = _positive_int(runtime.get("mpi_ranks"), label="mpi_ranks")
    _positive_int(runtime.get("wall_timeout_seconds"), label="wall_timeout_seconds")
    _positive_int(
        runtime.get("evaluator_timeout_seconds"),
        label="evaluator_timeout_seconds",
    )
    if profile == "NON_SCIENTIFIC_LOCAL_FIXTURE":
        if conversion_spec.get("evidence_identity") != "NON_SCIENTIFIC_FIXTURE":
            raise G2SmokeError(
                "PREPARATION_CONTRACT_INVALID",
                "local fixture launcher is forbidden for Q-POP evidence",
            )
        if ranks != 1:
            raise G2SmokeError(
                "PREPARATION_CONTRACT_INVALID",
                "local fixture launcher requires exactly one recorded rank",
            )
    elif profile == "WSL2_QPOP_CPC_V1":
        required_strings = (
            "wsl_executable",
            "distribution",
            "wsl_user",
            "mpirun_path",
            "python_path",
            "environment_id",
            "environment_spec_sha256",
            "resolution_lock_sha256",
            "build_manifest_sha256",
        )
        for key in required_strings:
            if not isinstance(runtime.get(key), str) or not runtime[key]:
                raise G2SmokeError(
                    "PREPARATION_CONTRACT_INVALID",
                    f"WSL runtime requires non-empty {key}",
                )
        if runtime["distribution"] != "PINN-PCM-SCI-Ubuntu-20.04":
            raise G2SmokeError(
                "PREPARATION_CONTRACT_INVALID",
                "WSL distribution differs from the qualified project distribution",
            )
        if runtime["environment_id"] != "qpop-cpc-v1-ubuntu-20.04-source-stack-v3":
            raise G2SmokeError(
                "PREPARATION_CONTRACT_INVALID",
                "WSL environment identity differs from the verified G2 stack",
            )
        for key in (
            "environment_spec_sha256",
            "resolution_lock_sha256",
            "build_manifest_sha256",
        ):
            if not _is_sha256(runtime[key]):
                raise G2SmokeError(
                    "PREPARATION_CONTRACT_INVALID",
                    f"{key} must be a SHA256 identity",
                )
        if runtime["wsl_user"] != "root":
            raise G2SmokeError(
                "PREPARATION_CONTRACT_INVALID",
                "G2 runtime currently freezes the imported root identity",
            )
        if ranks != 2:
            raise G2SmokeError(
                "PREPARATION_CONTRACT_INVALID",
                "Q-POP CPC v1 smoke requires exactly two MPI ranks",
            )
        for key in ("mpirun_path", "python_path"):
            if not str(runtime[key]).startswith("/"):
                raise G2SmokeError(
                    "PREPARATION_CONTRACT_INVALID",
                    f"{key} must be an absolute WSL path",
                )
        expected_environment = _expected_wsl_runtime_environment()
        if runtime.get("runtime_environment") != expected_environment:
            raise G2SmokeError(
                "PREPARATION_CONTRACT_INVALID",
                "WSL runtime environment differs from the verified G2 stack",
            )
        prefix = "/opt/qpop-cpc-v1-env-g2-final-002"
        if runtime["mpirun_path"] != f"{prefix}/openmpi-3.1.6/bin/mpirun":
            raise G2SmokeError(
                "PREPARATION_CONTRACT_INVALID",
                "WSL mpirun path differs from the verified G2 stack",
            )
        if runtime["python_path"] != f"{prefix}/py38/bin/python":
            raise G2SmokeError(
                "PREPARATION_CONTRACT_INVALID",
                "WSL Python path differs from the verified G2 stack",
            )
    else:
        raise G2SmokeError(
            "PREPARATION_CONTRACT_INVALID",
            f"unsupported native launcher profile: {profile!r}",
        )
    return path, runtime


def _windows_to_wsl_path(path: Path) -> str:
    resolved = path.resolve()
    drive = resolved.drive.rstrip(":").lower()
    if not drive or len(drive) != 1:
        raise G2SmokeError(
            "PREPARATION_CONTRACT_INVALID",
            f"cannot map native run path into WSL: {resolved}",
        )
    relative = resolved.as_posix().split(":", maxsplit=1)[1].lstrip("/")
    return f"/mnt/{drive}/{relative}"


def _build_native_command(
    *,
    native_root: Path,
    runtime: dict[str, Any],
) -> list[str]:
    entrypoint = native_root / "source" / "qpop-imt.py"
    if runtime["launcher_profile"] == "NON_SCIENTIFIC_LOCAL_FIXTURE":
        return [sys.executable, str(entrypoint)]
    wsl_native_root = _windows_to_wsl_path(native_root)
    wall_timeout = int(runtime["wall_timeout_seconds"])
    return [
        str(runtime["wsl_executable"]),
        "--distribution",
        str(runtime["distribution"]),
        "--user",
        str(runtime["wsl_user"]),
        "--cd",
        wsl_native_root,
        "--",
        "/usr/bin/timeout",
        "--signal=TERM",
        "--kill-after=10s",
        f"{wall_timeout}s",
        "/usr/bin/env",
        *[
            f"{key}={runtime['runtime_environment'][key]}"
            for key in sorted(runtime["runtime_environment"])
        ],
        str(runtime["mpirun_path"]),
        "--allow-run-as-root",
        "-np",
        str(runtime["mpi_ranks"]),
        str(runtime["python_path"]),
        f"{wsl_native_root}/source/qpop-imt.py",
    ]


def _terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            check=False,
        )
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=5)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def _launch_native_process(
    *,
    command: list[str],
    cwd: Path,
    stdout_path: Path,
    stderr_path: Path,
    timeout_seconds: int,
    state: dict[str, bool],
) -> int:
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=stdout,
                stderr=stderr,
                creationflags=creationflags,
                start_new_session=os.name != "nt",
            )
        except OSError as exc:
            raise G2SmokeError("NATIVE_LAUNCH_FAILED", str(exc)) from exc
        state["native_started"] = True
        try:
            process.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            _terminate_process_group(process)
            raise G2SmokeError(
                "NATIVE_TIMEOUT",
                f"native process exceeded {timeout_seconds} seconds",
            ) from exc
        except BaseException:
            _terminate_process_group(process)
            raise
    return int(process.returncode)


def _code_identity() -> dict[str, Any]:
    revision = "UNAVAILABLE"
    dirty = True
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        )
    except (OSError, subprocess.CalledProcessError):
        pass
    return {"kind": "working-tree", "revision": revision, "dirty": dirty}


def _prepare_native(
    *,
    request: G2SmokeRequest,
    native_root: Path,
    spec_path: Path,
    spec: dict[str, Any],
) -> dict[str, Any]:
    source_dir = native_root / "source"
    solution_dir = native_root / "solution"
    source_dir.mkdir(parents=True)
    solution_dir.mkdir()
    smoke_input = request.config_root / "smoke_input.xml"
    if _sha256(smoke_input) != str(spec.get("expected_input_sha256", "")):
        raise G2SmokeError(
            "PREPARATION_CONTRACT_INVALID",
            "smoke_input.xml differs from the frozen conversion spec",
        )
    shutil.copyfile(smoke_input, native_root / "input.xml")
    required_sources = spec.get("required_source_files")
    if not isinstance(required_sources, dict) or not required_sources:
        raise G2SmokeError(
            "PREPARATION_CONTRACT_INVALID",
            "conversion spec has no required source files",
        )
    copied_source_hashes: dict[str, str] = {}
    for relative, expected_hash in required_sources.items():
        relative_path = Path(str(relative))
        if relative_path.parts[:1] != ("source",) or len(relative_path.parts) != 2:
            raise G2SmokeError(
                "PREPARATION_CONTRACT_INVALID",
                f"unsupported source layout in conversion spec: {relative}",
            )
        source = request.source_root / relative_path.name
        destination = native_root / relative_path
        if not source.is_file() or _sha256(source) != str(expected_hash):
            raise G2SmokeError(
                "PREPARATION_SOURCE_MISMATCH",
                f"frozen source hash mismatch: {source}",
            )
        shutil.copyfile(source, destination)
        copied_source_hashes[relative_path.as_posix()] = _sha256(destination)
    metadata = {
        "schema_version": "qpop-native-run-metadata-v1",
        "run_id": request.run_id,
        "source_identity": spec["source_identity"],
        "source_files": copied_source_hashes,
        "input_sha256": _sha256(native_root / "input.xml"),
        "canonical_input_sha256": spec["canonical_input_sha256"],
        "allowed_input_differences": spec["allowed_input_differences"],
        "conversion_spec_sha256": _sha256(spec_path),
        "prepared_at": _utc_now(),
    }
    (native_root / "qpop_run_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metadata


def _assert_immutable_native_inputs(native_root: Path, metadata: dict[str, Any]) -> None:
    if _sha256(native_root / "input.xml") != metadata["input_sha256"]:
        raise G2SmokeError("POSTRUN_INPUT_CHANGED", "input.xml changed during native run")
    for relative, expected_hash in metadata["source_files"].items():
        if _sha256(native_root / relative) != expected_hash:
            raise G2SmokeError(
                "POSTRUN_SOURCE_CHANGED",
                f"executed source changed during native run: {relative}",
            )


def _postrun_identity(native_root: Path, metadata: dict[str, Any] | None) -> dict[str, Any]:
    if metadata is None:
        return {
            "schema_version": "qpop-postrun-identity-v1",
            "status": "NOT_PREPARED",
        }
    expected: dict[str, str] = {"input.xml": str(metadata["input_sha256"])}
    expected.update(
        {str(relative): str(value) for relative, value in metadata["source_files"].items()}
    )
    entries: dict[str, Any] = {"schema_version": "qpop-postrun-identity-v1"}
    for relative, expected_hash in expected.items():
        path = native_root / relative
        actual_hash = _sha256(path) if path.is_file() else None
        entries[relative] = {
            "expected_sha256": expected_hash,
            "actual_sha256": actual_hash,
            "status": (
                "MATCH"
                if actual_hash == expected_hash
                else "MISSING"
                if actual_hash is None
                else "CHANGED"
            ),
        }
    return entries


def _identity_violation(identity: dict[str, Any]) -> G2SmokeError | None:
    for relative, entry in identity.items():
        if relative == "schema_version" or not isinstance(entry, dict):
            continue
        status = entry.get("status")
        if status == "MATCH":
            continue
        code = "POSTRUN_INPUT_CHANGED" if relative == "input.xml" else "POSTRUN_SOURCE_CHANGED"
        return G2SmokeError(code, f"post-run identity for {relative} is {status}")
    return None


def _write_attempt_intent(
    *,
    request: G2SmokeRequest,
    started_at: str,
    runtime_spec_path: Path,
    lease_path: Path,
) -> Path:
    path = request.experiment_root / "intents" / f"{request.run_id}.json"
    if path.exists():
        raise G2SmokeError("RUN_ID_ALREADY_EXISTS", f"intent already exists: {request.run_id}")
    owner_host = platform.node()
    if not owner_host:
        raise G2SmokeError(
            "PREPARATION_CONTRACT_INVALID",
            "cannot establish the local host identity for intent recovery",
        )
    runtime_sha256 = _sha256(runtime_spec_path) if runtime_spec_path.is_file() else None
    _write_json_atomic(
        path,
        {
            "schema_version": "run-intent-v2",
            "run_id": request.run_id,
            "tier": "smoke",
            "scientific_role": "oracle_qualification",
            "gate": "G2",
            "started_at": started_at,
            "recover_not_before": _recover_not_before(
                started_at,
                runtime_spec_path,
            ),
            "recovery_grace_seconds": _ORPHAN_RECOVERY_GRACE_SECONDS,
            "owner": {
                "host": owner_host,
                "pid": os.getpid(),
                "lease": lease_path.relative_to(request.experiment_root).as_posix(),
            },
            "request": {
                "source_root": str(request.source_root),
                "config_root": str(request.config_root),
                "output_root": str(request.output_root),
                "environment_facts": request.environment_facts,
            },
            "runtime_spec": str(runtime_spec_path),
            "runtime_spec_sha256": runtime_sha256,
            "command": [],
            "code_identity": {
                "kind": "working-tree",
                "revision": "UNAVAILABLE",
                "dirty": True,
            },
            "physical_contract_id": "PROVISIONAL_G2_QPOP_CONTRACT_UNKNOWN",
            "case_id": "UNKNOWN",
            "planned_budget": {},
            "replay_of": request.replay_of,
            "supersedes": request.supersedes,
            "claim_status": "NO_SCIENTIFIC_CLAIM",
        },
    )
    return path


def _update_attempt_intent(path: Path, updates: dict[str, Any]) -> None:
    intent = _load_json(path)
    intent.update(updates)
    _write_json_atomic(path, intent)


def _intent_lease_path(experiment_root: Path, run_id: str) -> Path:
    return experiment_root / "leases" / f"{run_id}.lock"


def _manifest_from_orphan_intent(
    *,
    intent_path: Path,
    intent: dict[str, Any],
    lease_path: Path,
) -> RunManifest:
    request = intent.get("request")
    request = request if isinstance(request, dict) else {}
    environment_facts = request.get("environment_facts")
    environment_facts = environment_facts if isinstance(environment_facts, dict) else {}
    owner = intent.get("owner")
    owner = owner if isinstance(owner, dict) else {}
    command = intent.get("command")
    command = command if isinstance(command, list) else []
    code_identity = intent.get("code_identity")
    code_identity = (
        code_identity
        if isinstance(code_identity, dict)
        else {"kind": "working-tree", "revision": "UNAVAILABLE", "dirty": True}
    )
    planned_budget = intent.get("planned_budget")
    planned_budget = planned_budget if isinstance(planned_budget, dict) else {}
    run_id = str(intent["run_id"])
    output_root = request.get("output_root")
    artifacts = {
        "intent": str(intent_path),
        "lease": str(lease_path),
    }
    if isinstance(output_root, str) and output_root:
        artifacts["run_root"] = str(Path(output_root) / run_id)
    return RunManifest(
        run_id=run_id,
        experiment_group_id="g2-qpop-native-smoke-v1",
        tier="smoke",
        scientific_role="oracle_qualification",
        gate="G2",
        started_at=str(intent["started_at"]),
        ended_at=_utc_now(),
        command=[str(part) for part in command],
        execution_status="INTERRUPTED",
        numerical_validity="NOT_VALIDATED",
        gate_outcome="G2_SMOKE_BLOCKED",
        route_disposition="BLOCKED",
        evidence_identity="QPOP_NATIVE_NUMERICAL_SMOKE_ONLY",
        claim_status="NO_SCIENTIFIC_CLAIM",
        code_identity=code_identity,
        environment={
            **environment_facts,
            "orphan_recovery": {
                "status": "OWNER_LEASE_RELEASED",
                "owner_host": owner.get("host"),
                "owner_pid": owner.get("pid"),
            },
        },
        physical_contract_id=str(
            intent.get(
                "physical_contract_id",
                "PROVISIONAL_G2_QPOP_CONTRACT_UNKNOWN",
            )
        ),
        split_id="g2-qpop-artifact-self-read-v1",
        method_id="qpop-native-cpc-v1-smoke",
        case_id=str(intent.get("case_id", "UNKNOWN")),
        seed=0,
        planned_budget=planned_budget,
        actual_budget={
            "wall_seconds": None,
            "native_exit_code": None,
            "native_launch_attempted": None,
            "native_started": None,
            "recovered_from_orphan_intent": True,
        },
        checkpoint={
            "id": None,
            "selection": "not_available_interrupted_unknown",
        },
        evaluator_id="frozen-project-evaluator-g2-artifact-self-read-v1",
        artifacts=artifacts,
        failure_class="INTERRUPTED_UNKNOWN",
        replay_of=intent.get("replay_of"),
        supersedes=intent.get("supersedes"),
    )


def _index_has_exact_row(index_path: Path, expected: dict[str, Any]) -> bool:
    if not index_path.is_file():
        return False
    try:
        rows = [
            json.loads(line)
            for line in index_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (OSError, json.JSONDecodeError):
        return False
    return any(row == expected for row in rows)


def recover_orphaned_g2_intents(experiment_root: str | Path) -> list[Path]:
    """Record terminal evidence for same-host intents whose owner lease is released."""

    experiment_root = Path(experiment_root)
    intent_dir = experiment_root / "intents"
    if not intent_dir.is_dir():
        return []
    ledger = ExperimentLedger(experiment_root)
    recovered: list[Path] = []
    local_host = platform.node()
    for intent_path in sorted(intent_dir.glob("*.json")):
        try:
            intent = _load_json(intent_path)
        except (OSError, json.JSONDecodeError, G2SmokeError):
            continue
        run_id = intent.get("run_id")
        owner = intent.get("owner")
        if (
            intent.get("schema_version") != "run-intent-v2"
            or not isinstance(run_id, str)
            or run_id != intent_path.stem
            or not isinstance(owner, dict)
            or owner.get("host") != local_host
        ):
            continue
        recover_not_before = intent.get("recover_not_before")
        try:
            if not isinstance(recover_not_before, str) or datetime.now(
                timezone.utc
            ) < _parse_utc(recover_not_before):
                continue
        except ValueError:
            continue
        manifest_path = ledger.manifest_dir / f"{run_id}.json"
        expected_lease = _intent_lease_path(experiment_root, run_id)
        if owner.get("lease") != expected_lease.relative_to(experiment_root).as_posix():
            continue
        lease = _IntentLease.try_acquire(expected_lease, create=False)
        if lease is None:
            continue
        try:
            if manifest_path.exists():
                try:
                    stored_manifest = RunManifest(
                        **json.loads(manifest_path.read_text(encoding="utf-8"))
                    )
                except (OSError, json.JSONDecodeError, TypeError):
                    continue
                if _index_has_exact_row(
                    ledger.index_path,
                    stored_manifest.index_row(),
                ):
                    continue
                recovered.append(ledger.record(stored_manifest))
                continue
            manifest = _manifest_from_orphan_intent(
                intent_path=intent_path,
                intent=intent,
                lease_path=expected_lease,
            )
            recovered.append(ledger.record(manifest))
        finally:
            lease.release()
    return recovered


def _write_self_evaluation_contract(
    *,
    run_root: Path,
    case: CaseArtifact,
    spec: dict[str, Any],
) -> tuple[Path, Path, Path]:
    prediction_path = run_root / "prediction-self-read.h5"
    split_path = run_root / "split.json"
    metric_spec_path = run_root / "metric_spec.json"
    structure_field = "eta"
    device_channel = "qpop_cpc_v1_reported_voltage_drop"
    if device_channel not in case.circuit:
        raise G2SmokeError(
            "EVALUATOR_CONTRACT_INVALID",
            f"frozen device channel is missing: {device_channel}",
        )
    prediction = PredictionArtifact(
        case_id=case.case_id,
        physical_contract_id=case.physical_contract_id,
        method_id="qpop-native-artifact-self-read",
        checkpoint_id="native-final",
        mesh_identity=case.mesh_identity,
        field_time=case.field_time.copy(),
        circuit_time=case.circuit_time.copy(),
        time_unit=case.time_unit,
        fields={structure_field: case.fields[structure_field].copy()},
        field_units={structure_field: case.field_units[structure_field]},
        field_registry={structure_field: case.field_registry[structure_field]},
        circuit={device_channel: case.circuit[device_channel].copy()},
        circuit_units={device_channel: case.circuit_units[device_channel]},
    )
    prediction.write(prediction_path)
    split_path.write_text(
        json.dumps(
            {
                "schema_version": "split-manifest-v1",
                "split_id": "g2-qpop-artifact-self-read-v1",
                "cases": {case.case_id: "g2_smoke"},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    metric_spec_path.write_text(
        json.dumps(
            {
                "schema_version": "metric-spec-v1",
                "evaluator_id": "frozen-project-evaluator-g2-artifact-self-read-v1",
                "evidence_identity": "ENGINEERING_DISK_READ_CHECK_ONLY",
                "official_evaluator": spec["evaluator_audit"],
                "structure_field": structure_field,
                "structure_threshold": 0.5,
                "cycle_windows": [
                    [float(case.field_time[0]), float(case.field_time[-1])]
                ],
                "device_channel": device_channel,
                "device_scale": 1.0,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return prediction_path, split_path, metric_spec_path


def _run_evaluator_process(
    *,
    evaluator_command: list[str],
    evaluator_timeout_seconds: int,
    metrics_path: Path,
) -> subprocess.CompletedProcess[str]:
    del metrics_path
    try:
        return subprocess.run(
            evaluator_command,
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            timeout=evaluator_timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise G2SmokeError(
            "EVALUATOR_TIMEOUT",
            f"evaluator exceeded {evaluator_timeout_seconds} seconds",
        ) from exc


def _validate_self_evaluation_metrics(metrics_path: Path, case: CaseArtifact) -> dict[str, Any]:
    try:
        metrics = _load_json(metrics_path)
    except (OSError, json.JSONDecodeError, G2SmokeError) as exc:
        raise G2SmokeError(
            "EVALUATOR_OUTPUT_INVALID",
            f"metrics artifact is missing or invalid: {exc}",
        ) from exc
    expected_identity = {
        "schema_version": "metrics-v1",
        "evaluator_id": "frozen-project-evaluator-g2-artifact-self-read-v1",
        "case_id": case.case_id,
        "split_id": "g2-qpop-artifact-self-read-v1",
        "method_id": "qpop-native-artifact-self-read",
        "checkpoint_id": "native-final",
    }
    for key, expected in expected_identity.items():
        if metrics.get(key) != expected:
            raise G2SmokeError(
                "EVALUATOR_OUTPUT_INVALID",
                f"metrics {key} differs from frozen identity",
            )
    for key in (
        "structure_symmetric_difference_cycle_equal",
        "device_trajectory_nrmse",
    ):
        value = metrics.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise G2SmokeError(
                "EVALUATOR_OUTPUT_INVALID",
                f"metrics {key} is not numeric",
            )
        if not np.isfinite(float(value)) or float(value) != 0.0:
            raise G2SmokeError(
                "EVALUATOR_OUTPUT_INVALID",
                f"self-read metric {key} must be finite and exactly zero",
            )
    return metrics


def _summarize_native_log(log_path: Path) -> dict[str, int]:
    rows: list[list[str]] = []
    for line in log_path.read_text(encoding="utf-8").splitlines()[1:]:
        parts = line.split()
        if len(parts) == 11:
            rows.append(parts)
    if not rows:
        return {"accepted_steps": 0, "tfail": 0, "nfail": 0, "otherfail": 0}
    final = rows[-1]
    return {
        "accepted_steps": int(final[0]),
        "tfail": int(final[3]),
        "nfail": int(final[4]),
        "otherfail": int(final[5]),
    }


def _write_inventory(run_root: Path) -> Path:
    inventory_path = run_root / "artifact_inventory.json"
    inventory: dict[str, dict[str, Any]] = {}
    for path in sorted(run_root.rglob("*")):
        if path.is_file() and path != inventory_path:
            relative = path.relative_to(run_root).as_posix()
            inventory[relative] = {"bytes": path.stat().st_size, "sha256": _sha256(path)}
    inventory_path.write_text(
        json.dumps(
            {"schema_version": "artifact-inventory-v1", "files": inventory},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return inventory_path


def run_g2_smoke(request: G2SmokeRequest) -> int:
    recover_orphaned_g2_intents(request.experiment_root)
    lease_path = _intent_lease_path(request.experiment_root, request.run_id)
    lease = _IntentLease.try_acquire(lease_path, create=True)
    if lease is None:
        raise G2SmokeError(
            "RUN_ID_ALREADY_ACTIVE",
            f"another runner owns the intent lease: {request.run_id}",
        )
    try:
        return _run_g2_smoke_owned(request, lease_path=lease_path)
    finally:
        lease.release()


def _run_g2_smoke_owned(request: G2SmokeRequest, *, lease_path: Path) -> int:
    started_at = _utc_now()
    started_clock = time.monotonic()
    run_root = request.output_root / request.run_id
    native_root = run_root / "native"
    stdout_path = run_root / "stdout.log"
    stderr_path = run_root / "stderr.log"
    conversion_bundle = run_root / "conversion"
    spec_path = request.config_root / "conversion_spec.json"
    runtime_spec_path = request.config_root / "native_runtime.json"
    ledger = ExperimentLedger(request.experiment_root)
    command: list[str] = []
    native_exit_code: int | None = None
    native_launch_attempted = False
    native_state = {"native_started": False}
    metadata: dict[str, Any] | None = None
    runtime: dict[str, Any] = {}
    code_identity: dict[str, Any] = {
        "kind": "working-tree",
        "revision": "UNAVAILABLE",
        "dirty": True,
    }
    case: CaseArtifact | None = None
    log_summary = {"accepted_steps": 0, "tfail": 0, "nfail": 0, "otherfail": 0}
    artifacts: dict[str, str] = {
        "run_root": str(run_root),
        "native": str(native_root),
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "conversion_spec": str(spec_path),
        "native_runtime_spec": str(runtime_spec_path),
    }
    spec: dict[str, Any] = {}
    caught: BaseException | None = None
    try:
        intent_path = _write_attempt_intent(
            request=request,
            started_at=started_at,
            runtime_spec_path=runtime_spec_path,
            lease_path=lease_path,
        )
        artifacts["intent"] = str(intent_path)
        code_identity = _code_identity()
        _update_attempt_intent(intent_path, {"code_identity": code_identity})
        run_root.mkdir(parents=True, exist_ok=False)
        native_root.mkdir()
        spec = _load_json(spec_path)
        runtime_spec_path, runtime = _load_runtime_spec(request.config_root, spec)
        _validate_wsl_environment_facts(runtime, request.environment_facts)
        metadata = _prepare_native(
            request=request,
            native_root=native_root,
            spec_path=spec_path,
            spec=spec,
        )
        artifacts["native_metadata"] = str(native_root / "qpop_run_metadata.json")
        _assert_immutable_native_inputs(native_root, metadata)
        command = _build_native_command(native_root=native_root, runtime=runtime)
        _update_attempt_intent(
            intent_path,
            {
                "command": command,
                "physical_contract_id": str(
                    spec.get(
                        "physical_contract_id",
                        "PROVISIONAL_G2_QPOP_CONTRACT_UNKNOWN",
                    )
                ),
                "case_id": str(spec.get("case_id", "UNKNOWN")),
                "planned_budget": {
                    "wall_timeout_seconds": runtime.get("wall_timeout_seconds"),
                    "evaluator_timeout_seconds": runtime.get(
                        "evaluator_timeout_seconds"
                    ),
                    "mpi_ranks": runtime.get("mpi_ranks"),
                    "minimum_accepted_steps": 1,
                },
                "native_runtime": runtime,
            },
        )
        native_launch_attempted = True
        native_exit_code = _launch_native_process(
            command=command,
            cwd=native_root,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            timeout_seconds=int(runtime["wall_timeout_seconds"]) + (
                15 if runtime["launcher_profile"] == "WSL2_QPOP_CPC_V1" else 0
            ),
            state=native_state,
        )
        _assert_immutable_native_inputs(native_root, metadata)
        if (
            runtime["launcher_profile"] == "WSL2_QPOP_CPC_V1"
            and native_exit_code == 124
        ):
            raise G2SmokeError(
                "NATIVE_TIMEOUT",
                f"native process exceeded the frozen GNU timeout ({native_exit_code})",
            )
        if (
            runtime["launcher_profile"] == "WSL2_QPOP_CPC_V1"
            and native_exit_code == 137
        ):
            raise G2SmokeError(
                "NATIVE_PROCESS_KILLED_AMBIGUOUS",
                "native process returned 137 without an independent timeout sentinel",
            )
        if native_exit_code != 0:
            raise G2SmokeError(
                "NATIVE_PROCESS_EXIT",
                f"native process returned {native_exit_code}",
            )
        try:
            convert_qpop_run(
                QPopConversionRequest(
                    native_run_dir=native_root,
                    conversion_spec_path=spec_path,
                    bundle_dir=conversion_bundle,
                )
            )
        except QPopConversionError as exc:
            artifacts["conversion_report"] = str(
                conversion_bundle / "conversion_report.json"
            )
            raise G2SmokeError(exc.code, exc.detail) from exc
        case_path = conversion_bundle / "case.h5"
        case = CaseArtifact.read(case_path)
        prediction_path, split_path, metric_spec_path = _write_self_evaluation_contract(
            run_root=run_root,
            case=case,
            spec=spec,
        )
        metrics_path = run_root / "metrics.json"
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
        evaluator = _run_evaluator_process(
            evaluator_command=evaluator_command,
            evaluator_timeout_seconds=int(runtime["evaluator_timeout_seconds"]),
            metrics_path=metrics_path,
        )
        if evaluator.returncode != 0:
            with stderr_path.open("a", encoding="utf-8") as handle:
                handle.write(str(evaluator.stderr))
            raise G2SmokeError(
                "EVALUATOR_PROCESS_FAILED",
                str(evaluator.stderr).strip(),
            )
        _validate_self_evaluation_metrics(metrics_path, case)
        log_summary = _summarize_native_log(native_root / "log.txt")
        if log_summary["accepted_steps"] < 1:
            raise G2SmokeError(
                "NATIVE_RUN_INCOMPLETE",
                "native log contains no accepted nonlinear step",
            )
        artifacts.update(
            {
                "conversion_bundle": str(conversion_bundle),
                "case": str(case_path),
                "prediction": str(prediction_path),
                "split": str(split_path),
                "metric_spec": str(metric_spec_path),
                "metrics": str(metrics_path),
            }
        )
    except BaseException as exc:
        caught = exc
    finally:
        if run_root.exists():
            try:
                identity = _postrun_identity(native_root, metadata)
                identity_path = run_root / "postrun_identity.json"
                _write_json_atomic(identity_path, identity)
                artifacts["postrun_identity"] = str(identity_path)
                violation = _identity_violation(identity)
                if caught is None and violation is not None:
                    caught = violation
            except BaseException as identity_exc:
                if caught is None:
                    caught = G2SmokeError(
                        "POSTRUN_IDENTITY_AUDIT_FAILED",
                        str(identity_exc),
                    )
        if conversion_bundle.exists():
            artifacts["conversion_bundle"] = str(conversion_bundle)
            report_path = conversion_bundle / "conversion_report.json"
            if report_path.exists():
                artifacts["conversion_report"] = str(report_path)
        if (native_root / "log.txt").is_file():
            try:
                log_summary = _summarize_native_log(native_root / "log.txt")
            except (OSError, UnicodeDecodeError, ValueError):
                pass
        if run_root.exists():
            try:
                inventory_path = _write_inventory(run_root)
                artifacts["inventory"] = str(inventory_path)
            except BaseException as inventory_exc:
                if caught is None:
                    caught = G2SmokeError(
                        "ARTIFACT_INVENTORY_FAILED",
                        str(inventory_exc),
                    )

    successful = caught is None
    interrupted = isinstance(caught, (KeyboardInterrupt, SystemExit))
    failure_class = (
        None
        if successful
        else "INTERRUPTED"
        if interrupted
        else caught.code
        if isinstance(caught, G2SmokeError)
        else type(caught).__name__
    )
    actual_budget: dict[str, Any] = {
        "wall_seconds": time.monotonic() - started_clock,
        "native_exit_code": native_exit_code,
        "mpi_ranks": runtime.get("mpi_ranks"),
        "native_launch_attempted": native_launch_attempted,
        "native_started": native_state["native_started"],
        **log_summary,
    }
    if case is not None:
        actual_budget.update(
            {
                "first_time_ns": float(case.circuit_time[0]),
                "last_time_ns": float(case.circuit_time[-1]),
            }
        )
    planned_budget: dict[str, Any] = {
        "wall_timeout_seconds": runtime.get("wall_timeout_seconds"),
        "evaluator_timeout_seconds": runtime.get("evaluator_timeout_seconds"),
        "mpi_ranks": runtime.get("mpi_ranks"),
        "minimum_accepted_steps": 1,
    }
    differences = spec.get("allowed_input_differences")
    if isinstance(differences, list) and differences and isinstance(differences[0], dict):
        planned_budget["endtime_ns"] = differences[0].get("smoke_value")
    manifest = RunManifest(
        run_id=request.run_id,
        experiment_group_id="g2-qpop-native-smoke-v1",
        tier="smoke",
        scientific_role="oracle_qualification",
        gate="G2",
        started_at=started_at,
        ended_at=_utc_now(),
        command=command,
        execution_status=(
            "COMPLETED" if successful else "INTERRUPTED" if interrupted else "FAILED"
        ),
        numerical_validity="VALID_ENGINEERING_SMOKE" if successful else "NOT_VALIDATED",
        gate_outcome="G2_SMOKE_PASS" if successful else "G2_SMOKE_BLOCKED",
        route_disposition="CONTINUE_G3" if successful else "BLOCKED",
        evidence_identity="QPOP_NATIVE_NUMERICAL_SMOKE_ONLY",
        claim_status="NO_SCIENTIFIC_CLAIM",
        code_identity=code_identity,
        environment={
            **request.environment_facts,
            "python": platform.python_version(),
            "numpy": np.__version__,
            "h5py": h5py.__version__,
            "qpop_source_identity": spec.get("source_identity", {}),
            "conversion_spec_sha256": _sha256(spec_path) if spec_path.is_file() else None,
            "native_runtime_spec_sha256": (
                _sha256(runtime_spec_path) if runtime_spec_path.is_file() else None
            ),
            "native_runtime": runtime,
        },
        physical_contract_id=str(
            spec.get("physical_contract_id", "PROVISIONAL_G2_QPOP_CONTRACT_UNKNOWN")
        ),
        split_id="g2-qpop-artifact-self-read-v1",
        method_id="qpop-native-cpc-v1-smoke",
        case_id=str(spec.get("case_id", "UNKNOWN")),
        seed=0,
        planned_budget=planned_budget,
        actual_budget=actual_budget,
        checkpoint={
            "id": "native-final" if successful else None,
            "selection": "not_applicable_native_smoke",
        },
        evaluator_id="frozen-project-evaluator-g2-artifact-self-read-v1",
        artifacts=artifacts,
        failure_class=failure_class,
        replay_of=request.replay_of,
        supersedes=request.supersedes,
    )
    ledger.record(manifest)
    if interrupted:
        raise caught
    if caught is not None:
        print(f"G2 Q-POP smoke failed: {caught}", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one bounded G2 native Q-POP smoke.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--config-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--experiment-root", required=True, type=Path)
    parser.add_argument("--environment-facts", type=Path)
    parser.add_argument("--replay-of")
    parser.add_argument("--supersedes")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    environment_facts = (
        _load_json(args.environment_facts) if args.environment_facts else {}
    )
    return run_g2_smoke(
        G2SmokeRequest(
            run_id=args.run_id,
            source_root=args.source_root,
            config_root=args.config_root,
            output_root=args.output_root,
            experiment_root=args.experiment_root,
            environment_facts=environment_facts,
            replay_of=args.replay_of,
            supersedes=args.supersedes,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
