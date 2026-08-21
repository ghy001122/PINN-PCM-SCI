from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest
from unittest import mock

from pinn_pcm_sci.dynamic_order_oracle_runner import (
    R4_SIGNAL_CASES,
    R4_SIGNAL_TIME_STEP_NS,
    R4_SMOKE_TIME_STEP_NS,
    classify_r4_signal,
    run_signal_screen,
    run_smoke,
)
from pinn_pcm_sci.ledger import ExperimentLedger


ROOT = Path(__file__).resolve().parents[1]
INPUT = (
    ROOT
    / "configs"
    / "qpop"
    / "cpc-v1-imt-intrinsic-voltage-osc"
    / "canonical_input.xml"
)


class DynamicOrderOracleRunnerTests(unittest.TestCase):
    def test_signal_case_order_and_conjunctive_gate_are_frozen(self) -> None:
        self.assertEqual(
            R4_SIGNAL_CASES,
            ((9.0, 5.0e5), (10.5, 3.0e5), (7.5, 7.0e5)),
        )
        self.assertEqual(R4_SIGNAL_TIME_STEP_NS, 0.1)
        passing = {
            "finite": True,
            "phase_fraction_range": 0.05,
            "nondegenerate_cycle_count": 2,
            "max_balance_violation": 0.01,
        }
        failing = {**passing, "phase_fraction_range": 0.049999}

        outcome = classify_r4_signal([passing, passing, failing])
        self.assertEqual(outcome["signal_case_count"], 2)
        self.assertEqual(outcome["gate_outcome"], "R4_SIGNAL_PRESENT")
        self.assertEqual(
            classify_r4_signal([passing, failing, failing])["gate_outcome"],
            "R4_NO_SIGNAL",
        )

    def test_smoke_records_one_manifest_and_index_row(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            experiment_root = root / "experiment"
            run_id = "20260821T000000Z-smoke-r4-test-001"
            self.assertEqual(
                run_smoke(
                    run_id=run_id,
                    input_path=INPUT,
                    output_root=root / "runs",
                    experiment_root=experiment_root,
                ),
                0,
            )
            ledger = ExperimentLedger(experiment_root)
            ledger.validate()
            rows = (experiment_root / "index.jsonl").read_text(
                encoding="utf-8"
            ).splitlines()
            self.assertEqual(len(rows), 1)
            self.assertTrue(
                (experiment_root / "manifests" / f"{run_id}.json").is_file()
            )
            intent = json.loads(
                (experiment_root / "intents" / f"{run_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(intent["time_step_ns"], R4_SMOKE_TIME_STEP_NS)

    def test_execution_failure_is_not_recorded_as_a_scientific_no_signal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            experiment_root = root / "experiment"
            run_id = "20260821T000100Z-pilot-r4-failure-test-001"
            with mock.patch(
                "pinn_pcm_sci.dynamic_order_oracle_runner.DynamicOrderOracleCase.solve",
                side_effect=RuntimeError("forced integration failure"),
            ):
                with self.assertRaisesRegex(RuntimeError, "forced integration failure"):
                    run_signal_screen(
                        run_id=run_id,
                        input_path=INPUT,
                        output_root=root / "runs",
                        experiment_root=experiment_root,
                    )

            intent = json.loads(
                (experiment_root / "intents" / f"{run_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            manifest = json.loads(
                (experiment_root / "manifests" / f"{run_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(intent["time_step_ns"], R4_SIGNAL_TIME_STEP_NS)
            self.assertEqual(manifest["gate_outcome"], "R4_EXECUTION_FAILED")
            self.assertEqual(
                manifest["route_disposition"], "R4_EXECUTION_INVALID"
            )


if __name__ == "__main__":
    unittest.main()
