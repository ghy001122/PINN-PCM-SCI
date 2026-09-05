from __future__ import annotations

import json
import unittest

from pinn_pcm_sci.phk_v22r_training import ROOT
from pinn_pcm_sci.phk_v23_lf5 import load_contracts
from pinn_pcm_sci.phk_v23_lf5_evaluation import terminal_from_cpu


class LF5EvaluationTests(unittest.TestCase):
    def test_cpu_mechanism_failure_is_terminal_with_zero_gpu(self):
        cpu=json.loads((ROOT/"docs/experiment/artifacts/20260905T150045Z-phk-v23-lf5-cpu-qualification.json").read_text(encoding="utf-8")); decision=terminal_from_cpu(cpu,contract=load_contracts()["decision"])
        self.assertEqual(decision["outcome"],"LF5_TZL_ALIGNMENT_NOT_SUPPORTED_CPU"); self.assertEqual(decision["DEV_T"],"NOT_RUN"); self.assertEqual(decision["P0"],"NOT_RUN"); self.assertEqual(decision["optimizer_updates"],0); self.assertIsNone(decision["candidate"])

    def test_outcomes_are_complete_and_no_automatic_next_authority(self):
        decision=load_contracts()["decision"]; self.assertEqual(len(decision["machine_outcomes_and_unique_next"]),15); self.assertTrue(decision["completion_does_not_authorize_next_research"])


if __name__=="__main__": unittest.main()
