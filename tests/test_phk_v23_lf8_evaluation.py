from __future__ import annotations

import unittest

from pinn_pcm_sci.phk_v23_lf8 import P0_C, P0_FSTAR, load_contracts
from pinn_pcm_sci.phk_v23_lf8_evaluation import evidence_levels, matched_schedule_outcome, terminal_outcome


class LF8LayeredDecisionSeamTests(unittest.TestCase):
    def test_three_levels_do_not_collapse_into_each_other(self) -> None:
        levels = evidence_levels(
            accepted_updates=1200,
            endpoint_valid=True,
            safety_passed=True,
            strict_passed=True,
            fixed_blind_ratio=0.40,
            local_noninferiority=True,
            direct_noninferiority=False,
        )
        self.assertEqual(
            levels,
            {"complete_safety_path": True, "single_seed_pinn_pareto": True, "dense_paper_value": False},
        )

    def test_schedule_attribution_uses_only_complete_valid_endpoints(self) -> None:
        fstar = {"endpoint_valid": True, "safety_gate": {"passed": True}, "accepted_updates": 1200}
        control = {"endpoint_valid": True, "safety_gate": {"passed": False}, "accepted_updates": 1200}
        self.assertEqual(
            matched_schedule_outcome({P0_FSTAR: fstar, P0_C: control}),
            "COMPETENCE_FILTER_LOAD_BEARING_FOR_PRESERVATION",
        )
        control["safety_gate"]["passed"] = True
        self.assertEqual(
            matched_schedule_outcome({P0_FSTAR: fstar, P0_C: control}),
            "SCHEDULE_SUFFICIENT_FILTER_NOT_LOAD_BEARING",
        )
        control["endpoint_valid"] = False
        self.assertEqual(matched_schedule_outcome({P0_FSTAR: fstar, P0_C: control}), "MATCHED_ATTRIBUTION_UNAVAILABLE")

    def test_terminal_tree_separates_stall_physics_strict_and_direct_levels(self) -> None:
        decision = load_contracts()["decision"]
        self.assertEqual(terminal_outcome(decision, fstar_disposition="NO_FEASIBLE_FIRST_BLOCK"), "LF8_NO_FEASIBLE_FIRST_BLOCK")
        self.assertEqual(terminal_outcome(decision, fstar_disposition="FILTER_STALLED_WITH_VALID_PREFIX"), "LF8_FILTER_STALLED_WITH_VALID_PREFIX")
        self.assertEqual(
            terminal_outcome(decision, fstar_disposition="COMPLETE", safety=True, physics=False),
            "LF8_FULL_SAFETY_PATH_PHYSICS_GATE_MISSED",
        )
        self.assertEqual(
            terminal_outcome(decision, fstar_disposition="COMPLETE", safety=True, physics=True, strict=False),
            "LF8_SAFETY_PATH_STRICT_OR_LOCAL_FAILED",
        )
        self.assertEqual(
            terminal_outcome(
                decision,
                fstar_disposition="COMPLETE",
                safety=True,
                physics=True,
                strict=True,
                local=True,
                direct=False,
                mechanism="COMPETENCE_FILTER_LOAD_BEARING_FOR_PRESERVATION",
            ),
            "LF8_FILTER_LOAD_BEARING_DIRECT_BASELINE_GAP",
        )
        self.assertEqual(
            terminal_outcome(
                decision,
                fstar_disposition="COMPLETE",
                identity_valid=False,
                safety=True,
                physics=True,
                strict=True,
                local=True,
                direct=True,
            ),
            "LF8_POSTSTEP_IDENTITY_INVALID",
        )

    def test_outcome_map_is_exhaustive_unique_and_closed(self) -> None:
        decision = load_contracts()["decision"]
        mapping = decision["machine_outcomes_and_unique_next"]
        self.assertEqual(len(mapping), 11)
        self.assertEqual(len(set(mapping.values())), 11)
        self.assertTrue(decision["completion_does_not_authorize_next_research"])


if __name__ == "__main__":
    unittest.main()
