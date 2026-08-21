from __future__ import annotations

import unittest

from pinn_pcm_sci.qpop_qualification import adjudicate_qualification


class QPopQualificationTests(unittest.TestCase):
    def test_incomplete_author_run_and_reference_cannot_be_qualified(self) -> None:
        result = adjudicate_qualification(
            environment_verified=True,
            native_smoke_passed=True,
            author_case_completed=False,
            bundled_reference_completed=False,
            convergence_passed=False,
            conservation_passed=False,
            target_event_present=True,
            source_semantics_unique=True,
        )
        self.assertEqual(result, "INCONCLUSIVE_BUDGET_EXHAUSTED")

    def test_all_required_gates_are_conjunctive(self) -> None:
        result = adjudicate_qualification(
            environment_verified=True,
            native_smoke_passed=True,
            author_case_completed=True,
            bundled_reference_completed=True,
            convergence_passed=True,
            conservation_passed=True,
            target_event_present=True,
            source_semantics_unique=True,
        )
        self.assertEqual(result, "QUALIFIED")


if __name__ == "__main__":
    unittest.main()
