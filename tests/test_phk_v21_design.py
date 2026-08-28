from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import unittest

from pinn_pcm_sci.phk_v21_design import (
    PhkV21CandidateOutcome,
    build_stage1_cases,
    build_stage2_cases,
    rank_outcomes,
    select_medium_promotions,
    select_nominal_medium,
    select_stage1_parents,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs" / "phk_v21" / "engineering_contract.json"


def outcome(case, *, count, recovery, drift, outside, cpu, passed=False):
    return PhkV21CandidateOutcome(
        case=case,
        execution_status="COMPLETED",
        failure_identity=None,
        numerical_guard_passed=True,
        event_contract_passed=passed,
        event_and_locality_guards_passed_count=count,
        minimum_cycle_recovery=recovery,
        cycle_peak_drift=drift,
        outside_roi_peak=outside,
        process_cpu_seconds=cpu,
        cycle_records=(),
    )


class PhkV21DesignContractTest(unittest.TestCase):
    def test_stage1_is_exact_deterministic_sixteen_case_factorial(self) -> None:
        first = build_stage1_cases(CONTRACT)
        second = build_stage1_cases(CONTRACT)
        self.assertEqual(len(first), 16)
        self.assertEqual(first, second)
        self.assertEqual(len({item.physical_identity_sha256 for item in first}), 16)
        self.assertEqual({item.overrides.period for item in first}, {1.25, 1.5})
        self.assertEqual(
            {item.overrides.volumetric_cooling for item in first}, {2.5, 4.0}
        )
        self.assertEqual({item.overrides.mobility_cold for item in first}, {0.5, 1.0})
        self.assertEqual({item.overrides.thermal_drive for item in first}, {4.0, 6.0})

    def test_ranking_and_stage2_generation_are_frozen(self) -> None:
        cases = build_stage1_cases(CONTRACT)
        values = [
            outcome(
                case,
                count=index,
                recovery=0.1 + index / 100.0,
                drift=1.0,
                outside=0.2,
                cpu=10.0,
            )
            for index, case in enumerate(cases)
        ]
        parents = select_stage1_parents(values)
        self.assertEqual(
            [item.event_and_locality_guards_passed_count for item in parents],
            [15, 14],
        )
        children = build_stage2_cases(CONTRACT, parents)
        self.assertEqual(len(children), 16)
        self.assertEqual(len({item.physical_identity_sha256 for item in children}), 16)
        self.assertEqual({item.parent_case_id for item in children}, {
            parents[0].case.overrides.case_id,
            parents[1].case.overrides.case_id,
        })

    def test_ties_follow_recovery_drift_locality_cpu_then_case_id(self) -> None:
        cases = build_stage1_cases(CONTRACT)
        base = [
            outcome(case, count=10, recovery=0.5, drift=0.4, outside=0.2, cpu=10.0)
            for case in cases[:6]
        ]
        base[1] = replace(base[1], minimum_cycle_recovery=0.6)
        base[2] = replace(base[2], cycle_peak_drift=0.3)
        base[3] = replace(base[3], outside_roi_peak=0.1)
        base[4] = replace(base[4], process_cpu_seconds=9.0)
        ranked = rank_outcomes(base)
        self.assertIs(ranked[0], base[1])
        self.assertIs(ranked[1], base[2])
        self.assertIs(ranked[2], base[3])
        self.assertIs(ranked[3], base[4])

    def test_medium_selection_uses_only_three_promotions_and_first_full_pass(self) -> None:
        cases = build_stage1_cases(CONTRACT)
        stage1 = [
            outcome(case, count=index, recovery=0.5, drift=0.3, outside=0.1, cpu=1.0)
            for index, case in enumerate(cases)
        ]
        parents = select_stage1_parents(stage1)
        children = build_stage2_cases(CONTRACT, parents)
        stage2 = [
            outcome(case, count=index, recovery=0.5, drift=0.3, outside=0.1, cpu=1.0)
            for index, case in enumerate(children)
        ]
        promotions = select_medium_promotions(stage2)
        self.assertEqual([item.event_and_locality_guards_passed_count for item in promotions], [15, 14, 13])
        medium = [replace(item, event_contract_passed=False) for item in promotions]
        medium[1] = replace(medium[1], event_contract_passed=True)
        self.assertIs(select_nominal_medium(medium), medium[1])
        self.assertIsNone(
            select_nominal_medium(
                [replace(item, event_contract_passed=False) for item in promotions]
            )
        )


if __name__ == "__main__":
    unittest.main()
