from __future__ import annotations

from unittest.mock import patch
import unittest

from pinn_pcm_sci.phk_v23_lf1_evaluation import B0_ROLE as LF1_B0_ROLE, B_FINAL_ROLE as LF1_B_FINAL_ROLE, LF_ONLY_ROLE
from pinn_pcm_sci.phk_v23_lf3_evaluation import LF2_M0_ROLE, LF3_T0_ROLE
from pinn_pcm_sci.phk_v23_lf6 import load_contracts
from pinn_pcm_sci.phk_v23_lf6_evaluation import P0_ROLE, SELECTED_ROLE, adjudicate


class LF6EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.contract=load_contracts()["decision"]

    def test_no_safety_carrier_keeps_p0_not_run_distinct_from_failure(self):
        decision=adjudicate(contract=self.contract,run={"selected_role":None,"mechanism_outcome":"NO_RANK_SPECIFIC_INCREMENT"},evaluations={},potential={},comparisons={},physics={})
        self.assertEqual(decision["outcome"],"LF6_NO_VALID_SAFETY_CARRIER"); self.assertEqual(decision["P0"],"NOT_RUN"); self.assertIsNone(decision["candidate"])

    def test_preservation_and_strict_failures_have_ordered_outcomes(self):
        evaluations={name:{} for name in (LF_ONLY_ROLE,LF1_B0_ROLE,LF1_B_FINAL_ROLE,LF2_M0_ROLE,LF3_T0_ROLE,SELECTED_ROLE,P0_ROLE)}
        potential={name:{"passed":True} for name in evaluations}
        with patch("pinn_pcm_sci.phk_v23_lf6_evaluation._evaluation_valid",return_value=True):
            run={"selected_role":"DEV_M_INTERFACE_BAND_MSE","P0":{"numerical_valid":True,"preservation_gate":{"passed":False},"strict_gate":{"passed":False}}}
            self.assertEqual(adjudicate(contract=self.contract,run=run,evaluations=evaluations,potential=potential,comparisons={},physics={})["outcome"],"LF6_P0_PRESERVATION_FAILED")
            run["P0"]["preservation_gate"]={"passed":True}
            self.assertEqual(adjudicate(contract=self.contract,run=run,evaluations=evaluations,potential=potential,comparisons={},physics={})["outcome"],"LF6_P0_FINAL_STRICT_NOT_REACHED")

    def test_level2_and_direct_baseline_are_separate(self):
        roles=(LF_ONLY_ROLE,LF1_B0_ROLE,LF1_B_FINAL_ROLE,LF2_M0_ROLE,LF3_T0_ROLE,SELECTED_ROLE,P0_ROLE); evaluations={name:{} for name in roles}; potential={name:{"passed":True} for name in roles}
        run={"selected_role":"DEV_U_GENERIC_ENDPOINT_CONTROL","mechanism_outcome":"GENERIC_TEMPORAL_ENDPOINT_SUFFICIENT","P0":{"numerical_valid":True,"preservation_gate":{"passed":True},"strict_gate":{"passed":True}}}
        within={"phase_noninferiority_passed":True,"preservation_passed":True}; direct={"phase_noninferiority_passed":False,"preservation_passed":False}
        with patch("pinn_pcm_sci.phk_v23_lf6_evaluation._evaluation_valid",return_value=True),patch("pinn_pcm_sci.phk_v23_lf6_evaluation._competent",return_value=True):
            decision=adjudicate(contract=self.contract,run=run,evaluations=evaluations,potential=potential,comparisons={"P0_vs_selected":within,"P0_vs_LF_ONLY":direct},physics={"P0_to_selected":{"passed":True}})
            self.assertEqual(decision["outcome"],"LF6_SINGLE_SEED_PINN_PILOT_DIRECT_BASELINE_GAP"); self.assertIsNone(decision["candidate"])
            direct.update(phase_noninferiority_passed=True,preservation_passed=True)
            decision=adjudicate(contract=self.contract,run=run,evaluations=evaluations,potential=potential,comparisons={"P0_vs_selected":within,"P0_vs_LF_ONLY":direct},physics={"P0_to_selected":{"passed":True}})
            self.assertEqual(decision["outcome"],"LF6_PROVISIONAL_SINGLE_SEED_SIGNAL"); self.assertEqual(decision["candidate"],P0_ROLE)

    def test_outcome_mapping_is_exhaustive_unique_and_never_auto_authorizes(self):
        mapping=self.contract["machine_outcomes_and_unique_next"]; self.assertEqual(len(mapping),13); self.assertTrue(all(isinstance(value,str) and value for value in mapping.values())); self.assertTrue(self.contract["completion_does_not_authorize_next_research"])


if __name__=="__main__": unittest.main()
