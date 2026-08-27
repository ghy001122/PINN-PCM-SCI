from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from pinn_pcm_sci import phk_runner
from pinn_pcm_sci.phk_runner import (
    PhkRunnerContractError,
    run_freeze_splits,
    run_qualification_intent,
)


ROOT = Path(__file__).resolve().parents[1]
PROGRAM_PATH = ROOT / "configs" / "phk_v2" / "program_contract.json"
OBJECT_PATH = ROOT / "configs" / "phk_v2" / "object_numerical_contract.json"
SPLIT_PATH = ROOT / "configs" / "phk_v2" / "case_split_manifest.json"


class PhkRunnerTest(unittest.TestCase):
    def test_freeze_splits_is_write_once_and_self_hashing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "split_manifest.json"
            manifest = run_freeze_splits(
                program_path=PROGRAM_PATH,
                object_path=OBJECT_PATH,
                output_path=output,
            )
            disk = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(disk, manifest)
            self.assertEqual(len(disk["manifest_sha256"]), 64)
            with self.assertRaises(FileExistsError):
                run_freeze_splits(
                    program_path=PROGRAM_PATH,
                    object_path=OBJECT_PATH,
                    output_path=output,
                )

    def test_freeze_splits_does_not_create_parent_implicitly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "missing" / "split_manifest.json"
            with self.assertRaises(FileNotFoundError):
                run_freeze_splits(
                    program_path=PROGRAM_PATH,
                    object_path=OBJECT_PATH,
                    output_path=output,
                )

    def _roots(self, temp_dir: str) -> tuple[Path, Path]:
        output = Path(temp_dir) / "runs"
        experiment = Path(temp_dir) / "experiment"
        output.mkdir()
        experiment.mkdir()
        return output, experiment

    def test_manufactured_intent_is_persisted_before_check_and_ledgered(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output, experiment = self._roots(temp_dir)
            original = phk_runner.run_phk_manufactured_checks

            def check_after_intent(physical):
                self.assertTrue((experiment / "intents" / "phk-q-001.json").is_file())
                self.assertTrue(
                    (experiment / "intent_claims" / "phk-v2-q-intent-01.json").is_file()
                )
                return original(physical)

            with mock.patch.object(
                phk_runner,
                "run_phk_manufactured_checks",
                side_effect=check_after_intent,
            ):
                status = run_qualification_intent(
                    run_id="phk-q-001",
                    intent_number=1,
                    program_path=PROGRAM_PATH,
                    object_path=OBJECT_PATH,
                    split_path=SPLIT_PATH,
                    output_root=output,
                    experiment_root=experiment,
                )
            self.assertEqual(status, 0)
            manifest = json.loads(
                (experiment / "manifests" / "phk-q-001.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["execution_status"], "COMPLETED")
            self.assertEqual(manifest["gate_outcome"], "PHK_V2_Q_MANUFACTURED_PASS")
            self.assertEqual(manifest["actual_budget"]["qualification_intent"], 1)
            self.assertGreater(
                manifest["actual_budget"]["gross_compute"][
                    "single_thread_wall_upper_bound_core_hours"
                ],
                0.0,
            )
            self.assertEqual(len(manifest["artifacts"]["split_manifest_sha256"]), 64)

    def test_intent_order_is_enforced_before_atomic_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output, experiment = self._roots(temp_dir)
            with self.assertRaisesRegex(PhkRunnerContractError, "prior qualification intent"):
                run_qualification_intent(
                    run_id="phk-q-002",
                    intent_number=2,
                    program_path=PROGRAM_PATH,
                    object_path=OBJECT_PATH,
                    split_path=SPLIT_PATH,
                    output_root=output,
                    experiment_root=experiment,
                )
            self.assertFalse(
                (experiment / "intent_claims" / "phk-v2-q-intent-02.json").exists()
            )

    def test_solver_failure_is_consumed_and_not_relabelled_scientific_no_go(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output, experiment = self._roots(temp_dir)
            self.assertEqual(
                run_qualification_intent(
                    run_id="phk-q-001",
                    intent_number=1,
                    program_path=PROGRAM_PATH,
                    object_path=OBJECT_PATH,
                    split_path=SPLIT_PATH,
                    output_root=output,
                    experiment_root=experiment,
                ),
                0,
            )
            with mock.patch.object(
                phk_runner.PhkOracleCase,
                "solve",
                side_effect=RuntimeError("fixture failure"),
            ):
                status = run_qualification_intent(
                    run_id="phk-q-002",
                    intent_number=2,
                    program_path=PROGRAM_PATH,
                    object_path=OBJECT_PATH,
                    split_path=SPLIT_PATH,
                    output_root=output,
                    experiment_root=experiment,
                )
            self.assertEqual(status, 1)
            manifest = json.loads(
                (experiment / "manifests" / "phk-q-002.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["execution_status"], "FAILED")
            self.assertEqual(manifest["numerical_validity"], "NOT_EVALUATED")
            self.assertEqual(manifest["gate_outcome"], "PHK_V2_Q_EXECUTION_FAILED")
            self.assertEqual(manifest["failure_class"], "RuntimeError")
            self.assertEqual(
                manifest["actual_budget"]["failure_identity"],
                "RuntimeError: fixture failure",
            )
            self.assertNotIn("ORACLE_NO_GO", manifest["claim_status"])


if __name__ == "__main__":
    unittest.main()
