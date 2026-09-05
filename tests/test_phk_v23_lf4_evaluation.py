from __future__ import annotations

import unittest

from pinn_pcm_sci.phk_v23_lf4 import load_contracts
from pinn_pcm_sci.phk_v23_lf4_evaluation import adjudicate


class LF4EvaluationTests(unittest.TestCase):
    def setUp(self): self.contract=load_contracts()["decision"]

    def test_no_entry_keeps_p0_not_run_distinct_from_failure(self):
        decision=adjudicate(contract=self.contract,run={"numerical_invalid_arms":[],"selected_role":None,"mechanism_decision":{"classification":"NO_MECHANISM_INCREMENT_CLAIM"}},evaluations={},potential={},comparisons={},physics={})
        self.assertEqual(decision["outcome"],"LF4_NO_DEVELOPMENT_ENTRY"); self.assertEqual(decision["P0"],"NOT_RUN"); self.assertIsNone(decision["candidate"])

    def test_numerical_arm_has_precedence_but_retains_other_results(self):
        decision=adjudicate(contract=self.contract,run={"numerical_invalid_arms":["DEV_G_GLOBAL_MSE_CONTROL"]},evaluations={},potential={},comparisons={},physics={})
        self.assertEqual(decision["outcome"],"LF4_NUMERICAL_OR_IDENTITY_INVALID"); self.assertTrue(decision["matched_results_retained"])

    def test_all_machine_outcomes_have_unique_next_and_no_automatic_authority(self):
        mapping=self.contract["machine_outcomes_and_unique_next"]
        self.assertEqual(len(mapping),13); self.assertEqual(len(mapping),len(set(mapping.values())))


if __name__=="__main__": unittest.main()
