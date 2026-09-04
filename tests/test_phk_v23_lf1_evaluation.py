from __future__ import annotations

import unittest

from pinn_pcm_sci.phk_v23_lf1 import load_contracts
from pinn_pcm_sci.phk_v23_lf1_evaluation import (
    A_ROLE,
    B0_ROLE,
    B_FINAL_ROLE,
    C_ROLE,
    LF_ONLY_ROLE,
    adjudicate,
    compare_b_to_comparator,
)


def _report(*, competent: bool, primary: float = 0.10, co: float = 0.10):
    return {
        "hard_guards": {
            "passed": competent,
            "finite_values": True,
            "phase_range": True,
            "event_topology": {"cycles": []},
        },
        "metrics": {
            "time_averaged_phase_region_symmetric_difference": primary,
            "phase_roi_continuous_rms": co,
            "temperature_roi_nrmse_by_0_45": 0.02,
            "terminal_current_trace_nrmse": 0.05,
        },
    }


class LF1DecisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_contracts()["decision"]
        self.floors = {
            "time_averaged_phase_region_symmetric_difference": 0.01,
            "phase_roi_continuous_rms": 0.01,
        }

    def test_contract_maps_all_seven_outcomes_uniquely(self) -> None:
        mapping = self.contract["machine_outcomes_and_unique_next"]
        self.assertEqual(len(mapping), 7)
        self.assertEqual(len(set(mapping.values())), 7)

    def test_floor_noninferiority_is_distinct_from_ratio_improvement(self) -> None:
        comparison = compare_b_to_comparator(
            _report(competent=True, primary=0.105, co=0.105),
            _report(competent=True, primary=0.10, co=0.10),
            component_floors=self.floors,
        )
        self.assertTrue(comparison["floor_noninferiority_passed"])
        self.assertFalse(comparison["ratio_gate_passed"])
        self.assertTrue(comparison["phase_noninferiority_passed"])

    def test_machine_tree_distinguishes_transfer_forgetting_and_value(self) -> None:
        valid_guard = {"passed": True}
        a_only = adjudicate(
            contract=self.contract,
            evaluations={A_ROLE: _report(competent=False), LF_ONLY_ROLE: _report(competent=True)},
            potential_guards={A_ROLE: valid_guard, LF_ONLY_ROLE: valid_guard},
            b_status=None,
            comparisons={},
            physics=None,
            physics_batch_identity=None,
        )
        self.assertEqual(a_only["interim_status"], "LF1_A_VALID_RUN_B_REQUIRED")

        evaluations = {
            A_ROLE: _report(competent=False),
            LF_ONLY_ROLE: _report(competent=True),
            B0_ROLE: _report(competent=True),
            B_FINAL_ROLE: _report(competent=False),
        }
        guards = {role: valid_guard for role in evaluations}
        transfer = adjudicate(
            contract=self.contract,
            evaluations=evaluations,
            potential_guards=guards,
            b_status="LF1_DATA_TRANSFER_NO_EVENT",
            comparisons={},
            physics=None,
            physics_batch_identity=None,
        )
        self.assertEqual(transfer["outcome"], "LF1_DATA_TRANSFER_NO_EVENT")

        forgetting = adjudicate(
            contract=self.contract,
            evaluations=evaluations,
            potential_guards=guards,
            b_status="LF1_REFERENCE_BLIND_GPU_RUN_COMPLETE",
            comparisons={},
            physics={},
            physics_batch_identity={"passed": True},
        )
        self.assertEqual(forgetting["outcome"], "LF1_PHYSICS_FORGETTING_PERSISTS")

    def test_provisional_requires_conditional_data_only_control(self) -> None:
        reports = {
            A_ROLE: _report(competent=False),
            LF_ONLY_ROLE: _report(competent=True, primary=0.10, co=0.10),
            B0_ROLE: _report(competent=True, primary=0.10, co=0.10),
            B_FINAL_ROLE: _report(competent=True, primary=0.09, co=0.09),
        }
        comparisons = {
            role: compare_b_to_comparator(
                reports[B_FINAL_ROLE], reports[role], component_floors=self.floors
            )
            for role in (LF_ONLY_ROLE, B0_ROLE)
        }
        guards = {role: {"passed": True} for role in reports}
        physics = {"ratios": {"B_FINAL_TO_B0": {"passed": True}}}
        interim = adjudicate(
            contract=self.contract,
            evaluations=reports,
            potential_guards=guards,
            b_status="LF1_REFERENCE_BLIND_GPU_RUN_COMPLETE",
            comparisons=comparisons,
            physics=physics,
            physics_batch_identity={"passed": True},
        )
        self.assertEqual(interim["interim_status"], "LF1_C_TRIGGERED")

        reports[C_ROLE] = _report(competent=True, primary=0.095, co=0.095)
        comparisons[C_ROLE] = compare_b_to_comparator(
            reports[B_FINAL_ROLE], reports[C_ROLE], component_floors=self.floors
        )
        guards[C_ROLE] = {"passed": True}
        physics["ratios"]["B_FINAL_TO_C"] = {"passed": True}
        terminal = adjudicate(
            contract=self.contract,
            evaluations=reports,
            potential_guards=guards,
            b_status="LF1_REFERENCE_BLIND_GPU_RUN_COMPLETE",
            comparisons=comparisons,
            physics=physics,
            physics_batch_identity={"passed": True},
        )
        self.assertEqual(
            terminal["outcome"], "LF1_EVENT_PRESERVING_PINN_PROVISIONAL_SIGNAL"
        )


if __name__ == "__main__":
    unittest.main()
