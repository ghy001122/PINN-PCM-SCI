from __future__ import annotations

import unittest

from pinn_pcm_sci.kc_protocol_adjudication import adjudicate_protocols


class KCProtocolAdjudicationTests(unittest.TestCase):
    def test_no_structural_improvement_across_four_valid_arms_is_development_no_go(self) -> None:
        decision = adjudicate_protocols(
            raw_structure_error=0.229,
            arm_structure_errors=(0.229, 0.229, 0.229, 0.229),
            all_numerically_valid=True,
            oracle_qualified=False,
            evaluator_resolution=1.0e-12,
        )
        self.assertEqual(
            decision, "DEVELOPMENT_KC_SCIENTIFIC_NO_GO_UNQUALIFIED_ORACLE"
        )


if __name__ == "__main__":
    unittest.main()
