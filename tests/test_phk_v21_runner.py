from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy as np

from pinn_pcm_sci import phk_v21_runner
from pinn_pcm_sci.phk_benchmark import PhkConvergenceReport
from pinn_pcm_sci.phk_v21_evaluator import COMPONENT_ORDER
from pinn_pcm_sci.phk_v21_runner import (
    PhkV21RunnerContractError,
    run_qualification_intent,
    run_summarize_q,
)


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "configs" / "phk_v21" / "program_contract.json"
OBJECT = ROOT / "configs" / "phk_v21" / "object_numerical_contract.json"
LEGACY_PROGRAM = ROOT / "configs" / "phk_v2" / "program_contract.json"
LEGACY_OBJECT = ROOT / "configs" / "phk_v2" / "object_numerical_contract.json"
SPLIT = ROOT / "configs" / "phk_v21" / "case_split_manifest.json"
ORACLE = ROOT / "configs" / "phk_v21" / "oracle_and_floor_contract.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class PhkV21RunnerTest(unittest.TestCase):
    def _roots(self, directory: str) -> tuple[Path, Path]:
        output = Path(directory) / "runs"
        experiment = Path(directory) / "experiment"
        output.mkdir()
        experiment.mkdir()
        return output, experiment

    def _final_oracle(self, directory: str) -> Path:
        payload = json.loads(ORACLE.read_text(encoding="utf-8"))
        payload["status"] = "PRE_FIRST_VOTING_SOLVE_FREEZE"
        payload["bindings"]["evaluator_implementation_sha256"] = sha(
            ROOT / "pinn_pcm_sci" / "phk_v21_evaluator.py"
        )
        payload["bindings"]["runner_implementation_sha256"] = sha(
            ROOT / "pinn_pcm_sci" / "phk_v21_runner.py"
        )
        payload["bindings"]["qualification_tests_sha256"] = "A" * 64
        path = Path(directory) / "oracle.json"
        path.write_text(
            json.dumps(payload, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def _kwargs(
        self,
        *,
        output: Path,
        experiment: Path,
        oracle: Path,
    ) -> dict[str, Path]:
        return {
            "program_path": PROGRAM,
            "object_path": OBJECT,
            "legacy_program_path": LEGACY_PROGRAM,
            "legacy_object_path": LEGACY_OBJECT,
            "split_path": SPLIT,
            "oracle_contract_path": oracle,
            "output_root": output,
            "experiment_root": experiment,
        }

    def test_no_event_accepts_the_tuple_carrier_emitted_by_dataclass_asdict(self) -> None:
        event_payload = {
            "cycles": (
                {"event_time": None, "peak_roi_fraction": 0.0},
                {"event_time": None, "peak_roi_fraction": 0.0},
            )
        }
        self.assertTrue(phk_v21_runner._no_event(event_payload))

    def test_reconciliation_consumes_immutable_no_event_carriers_without_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            experiment = root / "experiment"
            manifests = experiment / "manifests"
            manifests.mkdir(parents=True)
            report_path = root / "report.json"
            result_path = root / "result.npz"
            report = {
                "expected_no_event_passed": False,
                "event": {
                    "cycles": [
                        {"event_time": None, "peak_roi_fraction": 0.0},
                        {"event_time": None, "peak_roi_fraction": 0.0},
                    ]
                },
            }
            report_path.write_text(json.dumps(report), encoding="utf-8")
            result_path.write_bytes(b"immutable-result-carrier")
            original_runner = "1" * 64
            manifest = {
                "run_id": "v21-q-002",
                "execution_status": "COMPLETED",
                "gate_outcome": "PHK_V21_Q_CASE_NO_GO",
                "route_disposition": "STOP_PHK_V21_ORACLE_ROUTE",
                "code_identity": {"phk_v21_runner_sha256": original_runner},
                "artifacts": {
                    "report": str(report_path),
                    "report_sha256": sha(report_path),
                    "result": str(result_path),
                    "result_sha256": sha(result_path),
                },
            }
            manifest_path = manifests / "v21-q-002.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            amendment = {
                "original_runner_sha256": original_runner,
                "correction": {
                    "qualification_intent": 2,
                    "run_id": "v21-q-002",
                    "manifest_sha256": sha(manifest_path),
                    "report_sha256": sha(report_path),
                    "result_sha256": sha(result_path),
                },
            }
            self.assertTrue(
                phk_v21_runner._is_reconciled_false_no_event(
                    experiment, manifest, 2, amendment
                )
            )

    def test_legacy_comparator_labels_are_canonicalized_without_reordering_values(self) -> None:
        legacy = PhkConvergenceReport(
            component_order=(
                "PHASE_FIELD_ROI_RMS",
                "TEMPERATURE_FIELD_ROI_RMS",
                "CURRENT_TRACE_RMS",
                "EVENT_TIME",
                "PHASE_REGION_SYMMETRIC_DIFFERENCE",
                "RECOVERY",
            ),
            component_deltas=np.arange(6, dtype=np.float64),
            finite=True,
        )
        canonical = phk_v21_runner._canonicalize_comparison_labels(legacy)
        self.assertEqual(canonical.component_order, COMPONENT_ORDER)
        np.testing.assert_array_equal(canonical.component_deltas, legacy.component_deltas)

    def test_manufactured_intent_and_claim_exist_before_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output, experiment = self._roots(directory)
            oracle = self._final_oracle(directory)
            original = phk_v21_runner.run_phk_v21_manufactured_checks

            def inspect(physical):
                self.assertTrue((experiment / "intents" / "v21-q-001.json").is_file())
                self.assertTrue(
                    (
                        experiment
                        / "intent_claims"
                        / "phk-v21-q-intent-01.json"
                    ).is_file()
                )
                return original(physical)

            with mock.patch.object(
                phk_v21_runner,
                "run_phk_v21_manufactured_checks",
                side_effect=inspect,
            ):
                status = run_qualification_intent(
                    run_id="v21-q-001",
                    intent_number=1,
                    **self._kwargs(output=output, experiment=experiment, oracle=oracle),
                )
            self.assertEqual(status, 0)
            manifest = json.loads(
                (experiment / "manifests" / "v21-q-001.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(manifest["gate_outcome"], "PHK_V21_Q_MANUFACTURED_PASS")
            self.assertEqual(manifest["actual_budget"]["qualification_intent"], 1)
            self.assertEqual(
                manifest["artifacts"]["oracle_contract_sha256"], sha(oracle)
            )

    def test_intent_order_is_checked_before_atomic_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output, experiment = self._roots(directory)
            oracle = self._final_oracle(directory)
            with self.assertRaisesRegex(PhkV21RunnerContractError, "prior"):
                run_qualification_intent(
                    run_id="v21-q-002",
                    intent_number=2,
                    **self._kwargs(output=output, experiment=experiment, oracle=oracle),
                )
            self.assertFalse(
                (experiment / "intent_claims" / "phk-v21-q-intent-02.json").exists()
            )

    def test_solver_failure_is_consumed_and_terminal_summary_accounts_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output, experiment = self._roots(directory)
            oracle = self._final_oracle(directory)
            kwargs = self._kwargs(output=output, experiment=experiment, oracle=oracle)
            self.assertEqual(
                run_qualification_intent(
                    run_id="v21-q-001", intent_number=1, **kwargs
                ),
                0,
            )

            def fail_after_intent(_self):
                self.assertTrue((experiment / "intents" / "v21-q-002.json").is_file())
                raise RuntimeError("fixture solver failure")

            with mock.patch.object(
                phk_v21_runner.PhkV21OracleCase,
                "solve",
                autospec=True,
                side_effect=fail_after_intent,
            ):
                status = run_qualification_intent(
                    run_id="v21-q-002", intent_number=2, **kwargs
                )
            self.assertEqual(status, 1)
            manifest = json.loads(
                (experiment / "manifests" / "v21-q-002.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(manifest["execution_status"], "FAILED")
            self.assertEqual(manifest["numerical_validity"], "NOT_EVALUATED")
            self.assertEqual(manifest["actual_budget"]["failed_intents"], 1)
            self.assertEqual(
                manifest["actual_budget"]["failure_identity"],
                "RuntimeError: fixture solver failure",
            )
            with self.assertRaisesRegex(PhkV21RunnerContractError, "failed"):
                run_qualification_intent(
                    run_id="v21-q-003", intent_number=3, **kwargs
                )
            self.assertEqual(
                run_summarize_q(run_id="v21-q-summary", **kwargs),
                0,
            )
            summary = json.loads(
                (output / "v21-q-summary" / "summary.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(summary["not_reached_intents"], list(range(3, 15)))
            self.assertEqual(
                summary["adjudication"]["outcome"],
                "PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN",
            )
            self.assertIsNone(summary["floor_seal"])

    def test_manufactured_no_go_blocks_later_intent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output, experiment = self._roots(directory)
            oracle = self._final_oracle(directory)
            kwargs = self._kwargs(output=output, experiment=experiment, oracle=oracle)
            report = {
                "schema_id": "phk-v21-manufactured-operator-report-v1",
                "passed": False,
            }
            with mock.patch.object(
                phk_v21_runner,
                "run_phk_v21_manufactured_checks",
                return_value=report,
            ):
                self.assertEqual(
                    run_qualification_intent(
                        run_id="v21-q-001", intent_number=1, **kwargs
                    ),
                    0,
                )
            with self.assertRaisesRegex(PhkV21RunnerContractError, "closed the route"):
                run_qualification_intent(
                    run_id="v21-q-002", intent_number=2, **kwargs
                )


if __name__ == "__main__":
    unittest.main()
