from __future__ import annotations

import unittest

from pinn_pcm_sci.phk_evaluator import adjudicate_phk_q


class PhkQAdjudicationTest(unittest.TestCase):
    def test_complete_positive_bundle_requires_every_event_and_no_execution_failure(self) -> None:
        decision = adjudicate_phk_q(
            execution_status_by_intent={number: "COMPLETED" for number in range(1, 13)},
            guard_pass_by_intent={number: True for number in range(2, 13)},
            event_pass_by_intent={number: True for number in range(3, 13)},
            manufactured_pass=True,
            replay_max_component_difference=0.0,
            replay_limit=1.0e-12,
            thermal_effect_established=True,
        )
        self.assertEqual(decision["outcome"], "PHK_V2_ORACLE_GATE_PASS")
        self.assertEqual(decision["method_route"], "CONTINUE_TO_STRONG_RAW")

    def test_failed_control_after_stable_event_failure_closes_method_route(self) -> None:
        decision = adjudicate_phk_q(
            execution_status_by_intent={
                **{number: "COMPLETED" for number in range(1, 9)},
                9: "FAILED",
            },
            guard_pass_by_intent={number: True for number in range(2, 9)},
            event_pass_by_intent={
                3: False,
                4: False,
                5: False,
                6: False,
                7: False,
                8: False,
            },
            manufactured_pass=True,
            replay_max_component_difference=0.0,
            replay_limit=1.0e-12,
            thermal_effect_established=True,
        )
        self.assertEqual(
            decision["outcome"],
            "PHK_V2_ORACLE_NO_GO_EVENT_CONTRACT_AND_CONTROL_EXECUTION_FAILURE",
        )
        self.assertEqual(decision["not_reached_intents"], [10, 11, 12])
        self.assertEqual(decision["method_route"], "STOP_BEFORE_PINN_TRAINING")
        self.assertFalse(decision["oracle_qualified"])

    def test_missing_intent_without_prior_consumed_failure_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing qualification intent"):
            adjudicate_phk_q(
                execution_status_by_intent={1: "COMPLETED", 2: "COMPLETED"},
                guard_pass_by_intent={2: True},
                event_pass_by_intent={},
                manufactured_pass=True,
                replay_max_component_difference=0.0,
                replay_limit=1.0e-12,
                thermal_effect_established=False,
            )


if __name__ == "__main__":
    unittest.main()
