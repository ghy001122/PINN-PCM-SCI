from __future__ import annotations

import errno
import json
import os
import tempfile
import threading
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, BinaryIO, Iterator

if os.name == "nt":
    import msvcrt
else:  # pragma: no cover - exercised on POSIX CI
    import fcntl


class LedgerValidationError(ValueError):
    """The experiment index and finalized manifests disagree."""


_THREAD_LOCKS_GUARD = threading.Lock()
_THREAD_LOCKS: dict[str, threading.Lock] = {}


def _thread_lock_for(path: Path) -> threading.Lock:
    key = os.path.normcase(str(path.resolve()))
    with _THREAD_LOCKS_GUARD:
        return _THREAD_LOCKS.setdefault(key, threading.Lock())


def _acquire_process_lock(handle: BinaryIO) -> None:
    if os.name == "nt":
        retryable = {
            errno.EACCES,
            errno.EAGAIN,
            getattr(errno, "EDEADLOCK", errno.EACCES),
        }
        while True:
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                return
            except OSError as exc:
                if exc.errno not in retryable:
                    raise
                time.sleep(0.01)
    else:  # pragma: no cover - exercised on POSIX CI
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)


def _release_process_lock(handle: BinaryIO) -> None:
    handle.seek(0)
    if os.name == "nt":
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:  # pragma: no cover - exercised on POSIX CI
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def _exclusive_ledger_lock(path: Path) -> Iterator[None]:
    thread_lock = _thread_lock_for(path)
    with thread_lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a+b") as handle:
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
                os.fsync(handle.fileno())
            _acquire_process_lock(handle)
            try:
                yield
            finally:
                _release_process_lock(handle)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        temporary_path.replace(path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    experiment_group_id: str
    tier: str
    scientific_role: str
    gate: str
    started_at: str
    ended_at: str
    command: list[str]
    execution_status: str
    numerical_validity: str
    gate_outcome: str
    route_disposition: str | None
    evidence_identity: str
    claim_status: str
    code_identity: dict[str, Any]
    environment: dict[str, Any]
    physical_contract_id: str
    split_id: str
    method_id: str
    case_id: str
    seed: int
    planned_budget: dict[str, Any]
    actual_budget: dict[str, Any]
    checkpoint: dict[str, Any]
    evaluator_id: str
    artifacts: dict[str, str]
    failure_class: str | None
    replay_of: str | None
    supersedes: str | None
    schema_version: str = "run-manifest-v1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def index_row(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "tier": self.tier,
            "scientific_role": self.scientific_role,
            "gate": self.gate,
            "method_id": self.method_id,
            "case_id": self.case_id,
            "split_id": self.split_id,
            "seed": self.seed,
            "manifest": f"manifests/{self.run_id}.json",
            "execution_status": self.execution_status,
            "numerical_validity": self.numerical_validity,
            "gate_outcome": self.gate_outcome,
            "route_disposition": self.route_disposition,
            "claim_status": self.claim_status,
            "replay_of": self.replay_of,
        }


class ExperimentLedger:
    """Append-only index and immutable finalized manifest store."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.manifest_dir = self.root / "manifests"
        self.index_path = self.root / "index.jsonl"
        self.human_index_path = self.root / "INDEX.md"
        self.lock_path = self.root / ".ledger.lock"

    def record(self, manifest: RunManifest) -> Path:
        with _exclusive_ledger_lock(self.lock_path):
            return self._record_locked(manifest)

    def _record_locked(self, manifest: RunManifest) -> Path:
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
        index_rows = self._read_index_rows(repair_truncated_tail=True)
        manifest_path = self.manifest_dir / f"{manifest.run_id}.json"
        indexed_manifest_paths: set[str] = set()
        for row in index_rows:
            indexed_path = row.get("manifest")
            if not isinstance(indexed_path, str):
                raise LedgerValidationError(
                    "append-only index row has no string manifest path"
                )
            indexed_manifest_paths.add(indexed_path)
        on_disk_manifest_paths = {
            f"manifests/{path.name}" for path in self.manifest_dir.glob("*.json")
        }
        requested_manifest_path = f"manifests/{manifest_path.name}"
        unrelated_unindexed = (
            on_disk_manifest_paths
            - indexed_manifest_paths
            - {requested_manifest_path}
        )
        if unrelated_unindexed:
            raise LedgerValidationError(
                "unindexed manifest requires idempotent replay before a new run: "
                + ", ".join(sorted(unrelated_unindexed))
            )
        manifest_payload = manifest.to_dict()
        if manifest_path.exists():
            try:
                existing_payload = json.loads(
                    manifest_path.read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError(
                    f"run_id already recorded with unreadable manifest: {manifest.run_id}"
                ) from exc
            if existing_payload != manifest_payload:
                raise ValueError(
                    f"run_id already recorded with different manifest content: "
                    f"{manifest.run_id}"
                )
        else:
            _atomic_write_text(
                manifest_path,
                json.dumps(manifest_payload, indent=2, sort_keys=True) + "\n",
            )
        index_row = manifest.index_row()
        matching_rows = [
            row
            for row in index_rows
            if row.get("run_id") == manifest.run_id
        ]
        if len(matching_rows) > 1:
            raise LedgerValidationError(
                f"duplicate run_id in append-only index: {manifest.run_id}"
            )
        if matching_rows and matching_rows[0] != index_row:
            raise LedgerValidationError(
                f"indexed content differs from manifest request: {manifest.run_id}"
            )
        if not matching_rows:
            with self.index_path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(index_row, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
        self._write_human_index()
        return manifest_path

    def _read_index_rows(
        self, *, repair_truncated_tail: bool = False
    ) -> list[dict[str, Any]]:
        if not self.index_path.exists():
            return []
        data = self.index_path.read_bytes()
        if not data:
            return []

        final_line_terminated = data.endswith(b"\n")
        encoded_lines = data.split(b"\n")
        if final_line_terminated:
            encoded_lines.pop()

        rows: list[dict[str, Any]] = []
        line_start = 0
        for line_number, encoded_line in enumerate(encoded_lines, start=1):
            is_final_line = line_number == len(encoded_lines)
            try:
                line = encoded_line.decode("utf-8")
            except UnicodeDecodeError as exc:
                if repair_truncated_tail and is_final_line and not final_line_terminated:
                    self._truncate_uncommitted_index_tail(line_start)
                    return rows
                raise LedgerValidationError(
                    f"invalid UTF-8 in append-only index row at line {line_number}"
                ) from exc
            if not line.strip():
                line_start += len(encoded_line) + 1
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                if repair_truncated_tail and is_final_line and not final_line_terminated:
                    self._truncate_uncommitted_index_tail(line_start)
                    return rows
                raise LedgerValidationError(
                    f"invalid append-only index row at line {line_number}"
                ) from exc
            if not isinstance(row, dict):
                raise LedgerValidationError(
                    f"append-only index row at line {line_number} is not an object"
                )
            rows.append(row)
            line_start += len(encoded_line) + 1

        if repair_truncated_tail and not final_line_terminated:
            with self.index_path.open("ab") as handle:
                handle.write(b"\n")
                handle.flush()
                os.fsync(handle.fileno())
        return rows

    def _truncate_uncommitted_index_tail(self, committed_size: int) -> None:
        with self.index_path.open("r+b") as handle:
            handle.truncate(committed_size)
            handle.flush()
            os.fsync(handle.fileno())

    def _write_human_index(self) -> None:
        rows = self._read_index_rows()
        lines = [
            "# Experiment index",
            "",
            "This is a generated view of the append-only `index.jsonl` ledger.",
            "",
            "| Run | Tier | Role | Gate | Method | Case | Seed | Status | Outcome | Manifest |",
            "|---|---|---|---|---|---|---:|---|---|---|",
        ]
        for row in rows:
            lines.append(
                "| {run_id} | {tier} | {scientific_role} | {gate} | {method_id} | "
                "{case_id} | {seed} | {execution_status} | {gate_outcome} | "
                "[{manifest}]({manifest}) |".format(**row)
            )
        self.human_index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def validate(self) -> None:
        with _exclusive_ledger_lock(self.lock_path):
            self._validate_locked()

    def _validate_locked(self) -> None:
        if not self.index_path.exists():
            manifests = (
                list(self.manifest_dir.glob("*.json"))
                if self.manifest_dir.exists()
                else []
            )
            if manifests:
                raise LedgerValidationError("manifest exists without append-only index")
            return

        rows = self._read_index_rows()
        run_ids = [str(row["run_id"]) for row in rows]
        if len(run_ids) != len(set(run_ids)):
            raise LedgerValidationError("duplicate run_id in append-only index")
        for row in rows:
            manifest_path = self.root / str(row["manifest"])
            if not manifest_path.exists():
                raise LedgerValidationError(
                    f"missing manifest for indexed run {row['run_id']}"
                )
            try:
                payload = json.loads(manifest_path.read_text(encoding="utf-8"))
                stored_manifest = RunManifest(**payload)
            except (OSError, json.JSONDecodeError, TypeError) as exc:
                raise LedgerValidationError(
                    f"invalid manifest for indexed run {row['run_id']}"
                ) from exc
            if payload.get("run_id") != row["run_id"]:
                raise LedgerValidationError(
                    f"manifest run_id mismatch for indexed run {row['run_id']}"
                )
            if stored_manifest.index_row() != row:
                raise LedgerValidationError(
                    f"index row does not match manifest for indexed run {row['run_id']}"
                )
        indexed_paths = {str(row["manifest"]) for row in rows}
        on_disk_paths = {
            f"manifests/{path.name}"
            for path in self.manifest_dir.glob("*.json")
        }
        if indexed_paths != on_disk_paths:
            raise LedgerValidationError("manifest/index one-to-one correspondence failed")
