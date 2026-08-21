from __future__ import annotations

import json
import multiprocessing
import os
import tempfile
import threading
import time
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from unittest.mock import patch

if os.name == "nt":
    import msvcrt
else:  # pragma: no cover - exercised on POSIX CI
    import fcntl

from pinn_pcm_sci.ledger import ExperimentLedger, LedgerValidationError, RunManifest


@contextmanager
def _hold_platform_file_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
            os.fsync(handle.fileno())
        handle.seek(0)
        if os.name == "nt":
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:  # pragma: no cover - exercised on POSIX CI
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:  # pragma: no cover - exercised on POSIX CI
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _record_in_child_process(
    root: str,
    manifest: RunManifest,
    ready: object,
    finished: object,
) -> None:
    ready.set()  # type: ignore[attr-defined]
    try:
        ExperimentLedger(root).record(manifest)
    finally:
        finished.set()  # type: ignore[attr-defined]


def _record_after_process_start(
    root: str,
    manifest: RunManifest,
    start: object,
) -> None:
    start.wait()  # type: ignore[attr-defined]
    ExperimentLedger(root).record(manifest)


def _manifest(
    *,
    run_id: str = "20260819T010203Z-smoke-pipeline-fixture-001",
    execution_status: str = "COMPLETED",
) -> RunManifest:
    return RunManifest(
        run_id=run_id,
        experiment_group_id="g1-pipeline-smoke-v1",
        tier="smoke",
        scientific_role="pipeline",
        gate="G1",
        started_at="2026-08-19T01:02:03Z",
        ended_at="2026-08-19T01:02:04Z",
        command=["python", "-m", "pinn_pcm_sci.smoke"],
        execution_status=execution_status,
        numerical_validity="NOT_APPLICABLE_ENGINEERING_SMOKE",
        gate_outcome="SMOKE_PASS",
        route_disposition=None,
        evidence_identity="ENGINEERING_CONTROL_FLOW_ONLY",
        claim_status="NO_NUMERICAL_EVIDENCE",
        code_identity={"kind": "working-tree", "revision": "fixture"},
        environment={"python": "3.11.9", "runtime": "cpu"},
        physical_contract_id="fixture-contract-v1",
        split_id="fixture-split-v1",
        method_id="fixture-model-v1",
        case_id="fixture-case-001",
        seed=7,
        planned_budget={"optimizer_steps": 1},
        actual_budget={"optimizer_steps": 1},
        checkpoint={"id": "step-0001", "selection": "single-step-smoke"},
        evaluator_id="fixture-evaluator-v1",
        artifacts={"metrics": "outputs/runs/example/metrics.json"},
        failure_class=None,
        replay_of=None,
        supersedes=None,
    )


class ExperimentLedgerContractTest(unittest.TestCase):
    def test_record_honors_the_same_lock_across_processes(self) -> None:
        manifest = _manifest(run_id="run-process-001")

        with tempfile.TemporaryDirectory() as tmp:
            ledger = ExperimentLedger(Path(tmp) / "experiment")
            context = multiprocessing.get_context("spawn")
            ready = context.Event()
            finished = context.Event()
            process = context.Process(
                target=_record_in_child_process,
                args=(str(ledger.root), manifest, ready, finished),
            )

            with _hold_platform_file_lock(ledger.lock_path):
                process.start()
                self.assertTrue(ready.wait(timeout=5.0))
                self.assertFalse(finished.wait(timeout=0.5))

            self.assertTrue(finished.wait(timeout=10.0))
            process.join(timeout=5.0)
            self.assertEqual(process.exitcode, 0)
            ledger.validate()

    def test_retry_repairs_only_a_truncated_final_jsonl_row(self) -> None:
        first = _manifest(run_id="run-before-crash")
        interrupted = _manifest(run_id="run-interrupted")

        with tempfile.TemporaryDirectory() as tmp:
            ledger = ExperimentLedger(Path(tmp) / "experiment")
            ledger.record(first)
            committed_prefix = ledger.index_path.read_bytes()
            interrupted_manifest_path = (
                ledger.manifest_dir / f"{interrupted.run_id}.json"
            )
            interrupted_manifest_path.write_text(
                json.dumps(interrupted.to_dict(), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            torn_row = json.dumps(interrupted.index_row(), sort_keys=True).encode(
                "utf-8"
            )[:47]
            with ledger.index_path.open("ab") as handle:
                handle.write(torn_row)

            recovered_path = ledger.record(interrupted)
            ledger.validate()
            recovered_bytes = ledger.index_path.read_bytes()
            rows = [
                json.loads(line)
                for line in recovered_bytes.decode("utf-8").splitlines()
            ]

        self.assertEqual(recovered_path, interrupted_manifest_path)
        self.assertTrue(recovered_bytes.startswith(committed_prefix))
        self.assertEqual(
            [row["run_id"] for row in rows],
            [first.run_id, interrupted.run_id],
        )

    def test_a_new_run_cannot_skip_the_manifest_owned_by_a_truncated_tail(self) -> None:
        first = _manifest(run_id="run-before-other-crash")
        interrupted = _manifest(run_id="run-other-interrupted")
        unrelated = _manifest(run_id="run-unrelated-new")

        with tempfile.TemporaryDirectory() as tmp:
            ledger = ExperimentLedger(Path(tmp) / "experiment")
            ledger.record(first)
            committed_prefix = ledger.index_path.read_bytes()
            (ledger.manifest_dir / f"{interrupted.run_id}.json").write_text(
                json.dumps(interrupted.to_dict(), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with ledger.index_path.open("ab") as handle:
                handle.write(b'{"run_id":"run-other-interrupted"')

            with self.assertRaisesRegex(
                LedgerValidationError, "unindexed manifest requires idempotent replay"
            ):
                ledger.record(unrelated)

            self.assertEqual(ledger.index_path.read_bytes(), committed_prefix)
            self.assertFalse(
                (ledger.manifest_dir / f"{unrelated.run_id}.json").exists()
            )

            ledger.record(interrupted)
            ledger.record(unrelated)
            ledger.validate()

    def test_record_never_repairs_or_masks_a_damaged_middle_jsonl_row(self) -> None:
        manifests = [
            _manifest(run_id="run-middle-001"),
            _manifest(run_id="run-middle-002"),
            _manifest(run_id="run-middle-003"),
        ]
        next_manifest = _manifest(run_id="run-middle-004")

        with tempfile.TemporaryDirectory() as tmp:
            ledger = ExperimentLedger(Path(tmp) / "experiment")
            for manifest in manifests:
                ledger.record(manifest)
            committed_lines = ledger.index_path.read_bytes().splitlines()
            damaged_bytes = b"\n".join(
                [committed_lines[0], b'{"broken":', committed_lines[2]]
            ) + b"\n"
            ledger.index_path.write_bytes(damaged_bytes)

            with self.assertRaisesRegex(
                LedgerValidationError, "invalid append-only index row at line 2"
            ):
                ledger.record(next_manifest)

            self.assertEqual(ledger.index_path.read_bytes(), damaged_bytes)
            self.assertFalse(
                (ledger.manifest_dir / f"{next_manifest.run_id}.json").exists()
            )

    def test_record_does_not_repair_an_invalid_but_terminated_final_row(self) -> None:
        first = _manifest(run_id="run-terminated-001")
        next_manifest = _manifest(run_id="run-terminated-002")

        with tempfile.TemporaryDirectory() as tmp:
            ledger = ExperimentLedger(Path(tmp) / "experiment")
            ledger.record(first)
            with ledger.index_path.open("ab") as handle:
                handle.write(b'{"broken":\n')
            damaged_bytes = ledger.index_path.read_bytes()

            with self.assertRaisesRegex(
                LedgerValidationError, "invalid append-only index row at line 2"
            ):
                ledger.record(next_manifest)

            self.assertEqual(ledger.index_path.read_bytes(), damaged_bytes)
            self.assertFalse(
                (ledger.manifest_dir / f"{next_manifest.run_id}.json").exists()
            )

    def test_concurrent_process_records_do_not_lose_or_duplicate_runs(self) -> None:
        manifests = [
            _manifest(run_id=f"run-process-concurrent-{number:03d}")
            for number in range(4)
        ]

        with tempfile.TemporaryDirectory() as tmp:
            ledger = ExperimentLedger(Path(tmp) / "experiment")
            context = multiprocessing.get_context("spawn")
            start = context.Event()
            processes = [
                context.Process(
                    target=_record_after_process_start,
                    args=(str(ledger.root), manifest, start),
                )
                for manifest in manifests
            ]
            for process in processes:
                process.start()
            start.set()
            for process in processes:
                process.join(timeout=15.0)

            self.assertEqual([process.exitcode for process in processes], [0] * 4)
            ledger.validate()
            rows = [
                json.loads(line)
                for line in ledger.index_path.read_text(encoding="utf-8").splitlines()
            ]
            human_index = ledger.human_index_path.read_text(encoding="utf-8")

        self.assertEqual(len(rows), len(manifests))
        self.assertEqual(
            {row["run_id"] for row in rows},
            {manifest.run_id for manifest in manifests},
        )
        for manifest in manifests:
            self.assertIn(manifest.run_id, human_index)

    def test_threaded_records_share_one_ledger_lock_and_preserve_both_rows(self) -> None:
        first = _manifest(run_id="run-thread-001")
        second = _manifest(run_id="run-thread-002")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "experiment"
            ledgers = [ExperimentLedger(root), ExperimentLedger(root)]
            start = threading.Barrier(3)
            state_lock = threading.Lock()
            active_publishers = 0
            max_active_publishers = 0
            errors: list[BaseException] = []
            original_replace = Path.replace

            def slow_manifest_publish(path: Path, target: Path) -> Path:
                nonlocal active_publishers, max_active_publishers
                if path.parent == ledgers[0].manifest_dir:
                    with state_lock:
                        active_publishers += 1
                        max_active_publishers = max(
                            max_active_publishers, active_publishers
                        )
                    time.sleep(0.05)
                    try:
                        return original_replace(path, target)
                    finally:
                        with state_lock:
                            active_publishers -= 1
                return original_replace(path, target)

            def record(ledger: ExperimentLedger, manifest: RunManifest) -> None:
                try:
                    start.wait()
                    ledger.record(manifest)
                except BaseException as exc:  # pragma: no cover - asserted below
                    errors.append(exc)

            with patch.object(Path, "replace", new=slow_manifest_publish):
                threads = [
                    threading.Thread(target=record, args=(ledgers[0], first)),
                    threading.Thread(target=record, args=(ledgers[1], second)),
                ]
                for thread in threads:
                    thread.start()
                start.wait()
                for thread in threads:
                    thread.join(timeout=5.0)

            ledgers[0].validate()
            rows = [
                json.loads(line)
                for line in ledgers[0]
                .index_path.read_text(encoding="utf-8")
                .splitlines()
            ]

        self.assertEqual(errors, [])
        self.assertEqual(max_active_publishers, 1)
        self.assertEqual({row["run_id"] for row in rows}, {first.run_id, second.run_id})
        self.assertEqual(len(rows), 2)

    def test_manifest_publish_failure_never_exposes_a_partial_manifest(self) -> None:
        manifest = _manifest()

        with tempfile.TemporaryDirectory() as tmp:
            ledger = ExperimentLedger(Path(tmp) / "experiment")
            with patch.object(Path, "replace", side_effect=OSError("publish failed")):
                with self.assertRaisesRegex(OSError, "publish failed"):
                    ledger.record(manifest)

            self.assertFalse(
                (ledger.manifest_dir / f"{manifest.run_id}.json").exists()
            )
            self.assertFalse(ledger.index_path.exists())
            self.assertFalse(ledger.human_index_path.exists())

    def test_identical_manifest_recovers_a_missing_index_and_human_view(self) -> None:
        manifest = _manifest()

        with tempfile.TemporaryDirectory() as tmp:
            ledger = ExperimentLedger(Path(tmp) / "experiment")
            manifest_path = ledger.record(manifest)
            ledger.index_path.unlink()
            ledger.human_index_path.unlink()

            recovered_path = ledger.record(manifest)
            ledger.validate()
            index_rows = [
                json.loads(line)
                for line in ledger.index_path.read_text(encoding="utf-8").splitlines()
            ]
            human_index = ledger.human_index_path.read_text(encoding="utf-8")

        self.assertEqual(recovered_path, manifest_path)
        self.assertEqual(index_rows, [manifest.index_row()])
        self.assertIn(manifest.run_id, human_index)

    def test_retry_after_index_append_failure_recovers_from_manifest(self) -> None:
        manifest = _manifest()

        with tempfile.TemporaryDirectory() as tmp:
            ledger = ExperimentLedger(Path(tmp) / "experiment")
            original_open = Path.open

            def fail_index_append(path: Path, *args: object, **kwargs: object):
                mode = args[0] if args else kwargs.get("mode", "r")
                if path == ledger.index_path and mode == "a":
                    raise OSError("index append failed")
                return original_open(path, *args, **kwargs)

            with patch.object(Path, "open", new=fail_index_append):
                with self.assertRaisesRegex(OSError, "index append failed"):
                    ledger.record(manifest)

            self.assertTrue(
                (ledger.manifest_dir / f"{manifest.run_id}.json").exists()
            )
            self.assertFalse(ledger.index_path.exists())
            self.assertFalse(ledger.human_index_path.exists())

            ledger.record(manifest)
            ledger.validate()
            index_rows = [
                json.loads(line)
                for line in ledger.index_path.read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(index_rows, [manifest.index_row()])

    def test_existing_manifest_with_different_content_is_rejected(self) -> None:
        manifest = _manifest()
        conflicting_manifest = _manifest(execution_status="FAILED")

        with tempfile.TemporaryDirectory() as tmp:
            ledger = ExperimentLedger(Path(tmp) / "experiment")
            manifest_path = ledger.record(manifest)

            with self.assertRaisesRegex(ValueError, "different manifest content"):
                ledger.record(conflicting_manifest)

            saved_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            index_rows = ledger.index_path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(saved_manifest, manifest.to_dict())
        self.assertEqual(len(index_rows), 1)

    def test_retry_after_human_view_failure_rebuilds_without_duplicate_row(self) -> None:
        manifest = _manifest()

        with tempfile.TemporaryDirectory() as tmp:
            ledger = ExperimentLedger(Path(tmp) / "experiment")
            original_write_text = Path.write_text

            def fail_human_view(path: Path, *args: object, **kwargs: object) -> int:
                if path == ledger.human_index_path:
                    raise OSError("human index failed")
                return original_write_text(path, *args, **kwargs)

            with patch.object(Path, "write_text", new=fail_human_view):
                with self.assertRaisesRegex(OSError, "human index failed"):
                    ledger.record(manifest)

            self.assertTrue(
                (ledger.manifest_dir / f"{manifest.run_id}.json").exists()
            )
            self.assertEqual(
                len(ledger.index_path.read_text(encoding="utf-8").splitlines()),
                1,
            )
            self.assertFalse(ledger.human_index_path.exists())

            ledger.record(manifest)
            ledger.validate()
            index_rows = [
                json.loads(line)
                for line in ledger.index_path.read_text(encoding="utf-8").splitlines()
            ]
            human_index = ledger.human_index_path.read_text(encoding="utf-8")

        self.assertEqual(index_rows, [manifest.index_row()])
        self.assertIn(manifest.run_id, human_index)

    def test_successful_smoke_is_written_to_manifest_and_append_only_index(self) -> None:
        manifest = RunManifest(
            run_id="20260819T010203Z-smoke-pipeline-fixture-001",
            experiment_group_id="g1-pipeline-smoke-v1",
            tier="smoke",
            scientific_role="pipeline",
            gate="G1",
            started_at="2026-08-19T01:02:03Z",
            ended_at="2026-08-19T01:02:04Z",
            command=["python", "-m", "pinn_pcm_sci.smoke"],
            execution_status="COMPLETED",
            numerical_validity="NOT_APPLICABLE_ENGINEERING_SMOKE",
            gate_outcome="SMOKE_PASS",
            route_disposition=None,
            evidence_identity="ENGINEERING_CONTROL_FLOW_ONLY",
            claim_status="NO_NUMERICAL_EVIDENCE",
            code_identity={"kind": "working-tree", "revision": "fixture"},
            environment={"python": "3.11.9", "runtime": "cpu"},
            physical_contract_id="fixture-contract-v1",
            split_id="fixture-split-v1",
            method_id="fixture-model-v1",
            case_id="fixture-case-001",
            seed=7,
            planned_budget={"optimizer_steps": 1},
            actual_budget={"optimizer_steps": 1},
            checkpoint={"id": "step-0001", "selection": "single-step-smoke"},
            evaluator_id="fixture-evaluator-v1",
            artifacts={"metrics": "outputs/runs/example/metrics.json"},
            failure_class=None,
            replay_of=None,
            supersedes=None,
        )

        with tempfile.TemporaryDirectory() as tmp:
            ledger = ExperimentLedger(Path(tmp) / "experiment")
            manifest_path = ledger.record(manifest)
            saved_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            index_rows = [
                json.loads(line)
                for line in ledger.index_path.read_text(encoding="utf-8").splitlines()
            ]
            human_index = ledger.human_index_path.read_text(encoding="utf-8")

        self.assertEqual(
            (
                saved_manifest["run_id"],
                saved_manifest["execution_status"],
                index_rows,
                "20260819T010203Z-smoke-pipeline-fixture-001" in human_index,
            ),
            (
                "20260819T010203Z-smoke-pipeline-fixture-001",
                "COMPLETED",
                [
                    {
                        "case_id": "fixture-case-001",
                        "claim_status": "NO_NUMERICAL_EVIDENCE",
                        "execution_status": "COMPLETED",
                        "gate": "G1",
                        "gate_outcome": "SMOKE_PASS",
                        "manifest": "manifests/20260819T010203Z-smoke-pipeline-fixture-001.json",
                        "method_id": "fixture-model-v1",
                        "numerical_validity": "NOT_APPLICABLE_ENGINEERING_SMOKE",
                        "replay_of": None,
                        "route_disposition": None,
                        "run_id": "20260819T010203Z-smoke-pipeline-fixture-001",
                        "scientific_role": "pipeline",
                        "seed": 7,
                        "split_id": "fixture-split-v1",
                        "tier": "smoke",
                    }
                ],
                True,
            ),
        )

    def test_validation_detects_an_index_row_without_its_manifest(self) -> None:
        manifest = RunManifest(
            run_id="20260819T010203Z-smoke-pipeline-fixture-001",
            experiment_group_id="g1-pipeline-smoke-v1",
            tier="smoke",
            scientific_role="pipeline",
            gate="G1",
            started_at="2026-08-19T01:02:03Z",
            ended_at="2026-08-19T01:02:04Z",
            command=["python", "-m", "pinn_pcm_sci.smoke"],
            execution_status="COMPLETED",
            numerical_validity="NOT_APPLICABLE_ENGINEERING_SMOKE",
            gate_outcome="SMOKE_PASS",
            route_disposition=None,
            evidence_identity="ENGINEERING_CONTROL_FLOW_ONLY",
            claim_status="NO_NUMERICAL_EVIDENCE",
            code_identity={"kind": "working-tree", "revision": "fixture"},
            environment={"python": "3.11.9", "runtime": "cpu"},
            physical_contract_id="fixture-contract-v1",
            split_id="fixture-split-v1",
            method_id="fixture-model-v1",
            case_id="fixture-case-001",
            seed=7,
            planned_budget={"optimizer_steps": 1},
            actual_budget={"optimizer_steps": 1},
            checkpoint={"id": "step-0001", "selection": "single-step-smoke"},
            evaluator_id="fixture-evaluator-v1",
            artifacts={"metrics": "outputs/runs/example/metrics.json"},
            failure_class=None,
            replay_of=None,
            supersedes=None,
        )

        with tempfile.TemporaryDirectory() as tmp:
            ledger = ExperimentLedger(Path(tmp) / "experiment")
            manifest_path = ledger.record(manifest)
            manifest_path.unlink()
            with self.assertRaisesRegex(LedgerValidationError, "missing manifest"):
                ledger.validate()

    def test_validation_detects_index_content_that_differs_from_manifest(self) -> None:
        manifest = _manifest()

        with tempfile.TemporaryDirectory() as tmp:
            ledger = ExperimentLedger(Path(tmp) / "experiment")
            ledger.record(manifest)
            mismatched_row = manifest.index_row()
            mismatched_row["case_id"] = "different-case"
            ledger.index_path.write_text(
                json.dumps(mismatched_row, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                LedgerValidationError, "index row does not match manifest"
            ):
                ledger.validate()


if __name__ == "__main__":
    unittest.main()
