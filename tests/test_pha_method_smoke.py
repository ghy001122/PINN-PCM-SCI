from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from pinn_pcm_sci.ledger import ExperimentLedger
from pinn_pcm_sci.pha_method_smoke import run_pha_method_smoke


class PHAMethodSmokeTests(unittest.TestCase):
    def test_four_pha_attribution_arms_complete_one_update_and_disk_audit(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            run_id = "20260821T040000Z-smoke-g6-pha-method-001"
            exit_code = run_pha_method_smoke(
                run_id=run_id,
                input_path=Path(
                    "configs/qpop/cpc-v1-imt-intrinsic-voltage-osc-author-case/"
                    "canonical_input.xml"
                ),
                output_root=root / "outputs" / "runs",
                experiment_root=root / "experiment",
                seed=13,
            )
            manifest = json.loads(
                (root / "experiment" / "manifests" / f"{run_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            metrics = json.loads(
                (root / "outputs" / "runs" / run_id / "metrics.json").read_text(
                    encoding="utf-8"
                )
            )
            ExperimentLedger(root / "experiment").validate()
            self.assertEqual(exit_code, 0)
            self.assertEqual(manifest["tier"], "smoke")
            self.assertEqual(manifest["gate_outcome"], "G6_PHA_METHOD_SMOKE_PASS")
            self.assertEqual(manifest["actual_budget"]["optimizer_updates"], 4)
            self.assertEqual(manifest["claim_status"], "NO_SCIENTIFIC_CLAIMS")
            self.assertTrue(metrics["all_finite"])
            self.assertLessEqual(metrics["shared_gate_max_abs_delta"], 1.0e-12)
            self.assertTrue(metrics["shared_sampling_concentrated"])


if __name__ == "__main__":
    unittest.main()
