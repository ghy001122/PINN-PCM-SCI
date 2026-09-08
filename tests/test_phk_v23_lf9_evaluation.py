from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pinn_pcm_sci import phk_v23_lf9 as lf9
from pinn_pcm_sci import phk_v23_lf9_evaluation as evaluation


class LF9EvaluationTests(unittest.TestCase):
    def test_not_run_conditional_endpoints_are_strict_json_serializable(self) -> None:
        level = evaluation._level_for_endpoint(
            raw={"executed": False, "endpoint_valid": False},
            evaluation=None,
            potential=None,
            medium=None,
            baseline_medium={},
            comparison_dev_r=None,
            comparison_direct=None,
            blind=None,
            blind_baseline={"J_S": 1.0, "J_M": 1.0, "CV1": 1.0, "CV4": 1.0},
            selected_arm=None,
        )
        self.assertEqual(
            level["blind_ratios_to_DEV_R"],
            {"J_S": None, "J_M": None, "CV1": None, "CV4": None},
        )
        with TemporaryDirectory() as tmp:
            evaluation.write_strict_json(Path(tmp) / "report.json", {"level": level})

    def test_two_screen_failures_close_solver_rescue(self) -> None:
        result = evaluation.terminal_outcome(
            run={
                "arms": {
                    lf9.ER_S: {"screen_go": False, "identity_valid": True},
                    lf9.ER_CV: {"screen_go": False, "identity_valid": True},
                },
                "mechanism_outcome": "NO_SAFE_MIXED_FORM_SCREEN",
                "selected_arm": None,
                "full_refinement": {"executed": False},
                "control": {"executed": False},
            },
            local={},
        )
        self.assertEqual(result["machine_outcome"], "LF9_NO_SAFE_MIXED_FORM_SCREEN")
        self.assertEqual(result["unique_next"], "FINALIZE_NEGATIVE_SOLVER_DIAGNOSTIC_NO_MORE_RESCUE")

    def test_internal_pareto_and_control_separate_filter_attribution(self) -> None:
        base = {
            "complete_internal_pareto": True,
            "direct_paper_value": False,
        }
        no_filter_pass = evaluation.terminal_outcome(
            run={
                "arms": {lf9.ER_S: {"screen_go": True, "identity_valid": True}, lf9.ER_CV: {"screen_go": False, "identity_valid": True}},
                "mechanism_outcome": "EQUATION_ROUTING_SUFFICIENT",
                "selected_arm": lf9.ER_S,
                "full_refinement": {"executed": True, **base},
                "control": {"executed": True, "complete_internal_pareto": True},
            },
            local={},
        )
        self.assertEqual(no_filter_pass["machine_outcome"], "LF9_SCHEDULE_AND_ROUTING_SUFFICIENT")
        filtered_only = evaluation.terminal_outcome(
            run={
                "arms": {lf9.ER_S: {"screen_go": True, "identity_valid": True}, lf9.ER_CV: {"screen_go": False, "identity_valid": True}},
                "mechanism_outcome": "EQUATION_ROUTING_SUFFICIENT",
                "selected_arm": lf9.ER_S,
                "full_refinement": {"executed": True, **base},
                "control": {"executed": True, "complete_internal_pareto": False},
            },
            local={},
        )
        self.assertEqual(filtered_only["machine_outcome"], "LF9_FILTER_LOAD_BEARING_DIRECT_BASELINE_GAP")

    def test_phase_frozen_stall_has_priority_over_generic_full_stall(self) -> None:
        result = evaluation.terminal_outcome(
            run={
                "arms": {lf9.ER_S: {"screen_go": True, "identity_valid": True}, lf9.ER_CV: {"screen_go": False, "identity_valid": True}},
                "mechanism_outcome": "EQUATION_ROUTING_SUFFICIENT",
                "selected_arm": lf9.ER_S,
                "full_refinement": {"executed": True, "disposition": "PHASE_FROZEN_THERMAL_ROUTE_FAILED", "complete_internal_pareto": False},
                "control": {"executed": False},
            },
            local={},
        )
        self.assertEqual(result["machine_outcome"], "LF9_PHASE_FROZEN_THERMAL_ROUTE_FAILED")


if __name__ == "__main__":
    unittest.main()
