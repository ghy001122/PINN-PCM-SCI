from __future__ import annotations

from pathlib import Path
import unittest

from pinn_pcm_sci.phk_v23_lf3 import load_contracts
from pinn_pcm_sci.phk_v23_lf3_evaluation import (
    LF2_M0_ROLE, LF3_P0_ROLE, LF3_T0_ROLE, _lf3_fixed_physics_values,
    adjudicate, evaluate_lf3_campaign,
)
from pinn_pcm_sci.phk_v23_lf1_evaluation import B0_ROLE, B_FINAL_ROLE, LF_ONLY_ROLE


def _report(competent=True):
    return {"hard_guards": {"passed": competent, "finite_values": True, "phase_range": True}, "metrics": {"time_averaged_phase_region_symmetric_difference": 0.1, "phase_roi_continuous_rms": 0.1, "temperature_roi_nrmse_by_0_45": 0.02, "terminal_current_trace_nrmse": 0.05}}


class LF3AdjudicationTests(unittest.TestCase):
    def setUp(self):
        self.contract = load_contracts()["decision"]
        roles = (LF_ONLY_ROLE, B0_ROLE, B_FINAL_ROLE, LF2_M0_ROLE, LF3_T0_ROLE, LF3_P0_ROLE)
        self.evaluations = {role: _report() for role in roles}
        self.guards = {role: {"passed": True} for role in roles}
        self.comparisons = {name: {"phase_noninferiority_passed": True, "preservation_passed": True} for name in ("P0_vs_T0", "P0_vs_LF_ONLY")}

    def decide(self, **overrides):
        args = {"contract": self.contract, "run_status": "LF3_REFERENCE_BLIND_GPU_TRAJECTORY_COMPLETE", "evaluations": self.evaluations, "potential_guards": self.guards, "comparisons": self.comparisons, "physics": {"P0_to_T0": {"passed": True}}, "t0_gate": {"passed": True, "temporal_only_failure": False}, "p0_gate": {"passed": True}}
        args.update(overrides)
        return adjudicate(**args)

    def test_candidate_signal_requires_all_three_levels(self):
        result = self.decide()
        self.assertEqual(result["outcome"], "LF3_PROVISIONAL_CANDIDATE_SIGNAL")
        self.assertEqual(result["candidate"], LF3_P0_ROLE)

    def test_no_pareto_and_direct_gap_are_distinct(self):
        physics = {"P0_to_T0": {"passed": False}}
        self.assertEqual(self.decide(physics=physics)["outcome"], "LF3_NO_PINN_PARETO")
        comparisons = dict(self.comparisons)
        comparisons["P0_vs_LF_ONLY"] = {"phase_noninferiority_passed": False, "preservation_passed": True}
        self.assertEqual(self.decide(comparisons=comparisons)["outcome"], "LF3_DIRECT_BASELINE_GAP")

    def test_temporal_carrier_failure_precedes_generic_failure(self):
        result = self.decide(run_status="LF3_TEMPORAL_CARRIER_FAILURE", t0_gate={"passed": False, "temporal_only_failure": True}, p0_gate=None)
        self.assertEqual(result["outcome"], "LF3_TEMPORAL_CARRIER_FAILURE")

    def test_local_evaluation_refuses_before_shutdown(self):
        with self.assertRaises(PermissionError):
            evaluate_lf3_campaign(output_directory=Path("unused"), run_directory=Path("unused"), cpu_qualification_path=Path("unused"), gpu_lifecycle="RUNNING")

    def test_fixed_physics_report_uses_lf3_roles(self):
        from unittest.mock import patch

        legacy = {
            "values": {"LF2_M0_CALIBRATED_CARRIER": 2.0, "LF2_M1_FINAL": 0.5},
            "components": {"LF2_M0_CALIBRATED_CARRIER": {"physics_total": 2.0}, "LF2_M1_FINAL": {"physics_total": 0.5}},
            "final_to_M0": {"ratio": 0.25, "defined": True, "maximum": 0.5, "passed": True},
            "fixed_pool_sha256": "POOL",
        }
        with patch("pinn_pcm_sci.phk_v23_lf3_evaluation._fixed_physics_values", return_value=legacy):
            report = _lf3_fixed_physics_values(
                {LF3_T0_ROLE: Path("t0.pt"), LF3_P0_ROLE: Path("p0.pt")},
                contract={},
            )
        self.assertEqual(set(report["values"]), {LF3_T0_ROLE, LF3_P0_ROLE})
        self.assertEqual(set(report["components"]), {LF3_T0_ROLE, LF3_P0_ROLE})
        self.assertEqual(report["P0_to_T0"]["ratio"], 0.25)
        self.assertNotIn("final_to_M0", report)


if __name__ == "__main__":
    unittest.main()
