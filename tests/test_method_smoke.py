from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pinn_pcm_sci.ledger import ExperimentLedger
from pinn_pcm_sci.method_smoke import run_method_smoke


class MethodSmokeTest(unittest.TestCase):
    def test_raw_identity_and_kc_complete_one_update_and_disk_evaluation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            run_id = "20260821T030000Z-smoke-g4-method-fixture-001"
            exit_code = run_method_smoke(
                run_id=run_id,
                output_root=root / "outputs" / "runs",
                experiment_root=root / "experiment",
                seed=7,
            )
            manifest = json.loads(
                (root / "experiment" / "manifests" / f"{run_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            metrics = json.loads(
                (
                    root
                    / "outputs"
                    / "runs"
                    / run_id
                    / "metrics.json"
                ).read_text(encoding="utf-8")
            )

            ExperimentLedger(root / "experiment").validate()
            self.assertEqual(exit_code, 0)
            self.assertEqual(manifest["tier"], "smoke")
            self.assertEqual(manifest["gate_outcome"], "G4_METHOD_SMOKE_PASS")
            self.assertEqual(manifest["claim_status"], "NO_SCIENTIFIC_CLAIMS")
            self.assertEqual(manifest["actual_budget"]["optimizer_updates"], 3)
            self.assertTrue(metrics["all_finite"])
            self.assertLess(metrics["raw_identity_initial_max_abs"], 1e-12)


if __name__ == "__main__":
    unittest.main()
