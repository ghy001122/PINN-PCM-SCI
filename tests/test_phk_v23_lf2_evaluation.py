from __future__ import annotations

from pathlib import Path
import unittest

from pinn_pcm_sci.phk_v23_lf2 import load_contracts
from pinn_pcm_sci.phk_v23_lf2_evaluation import (
    LF1_B0_ROLE,
    LF_ONLY_ROLE,
    LF2_FINAL_ROLE,
    LF2_M0_ROLE,
    _component_floors,
    adjudicate,
    evaluate_lf2_campaign,
)


def _report(*, competent: bool = True):
    return {
        "hard_guards": {
            "passed": competent,
            "finite_values": True,
            "phase_range": True,
            "event_topology": {"cycles": []},
        },
        "metrics": {
            "time_averaged_phase_region_symmetric_difference": 0.10,
            "phase_roi_continuous_rms": 0.10,
            "temperature_roi_nrmse_by_0_45": 0.02,
            "terminal_current_trace_nrmse": 0.05,
        },
    }


class LF2EvaluationDecisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_contracts()["decision"]
        self.evaluations = {
            LF_ONLY_ROLE: _report(),
            LF1_B0_ROLE: _report(),
            LF2_M0_ROLE: _report(),
            LF2_FINAL_ROLE: _report(),
        }
        self.guards = {role: {"passed": True} for role in self.evaluations}
        self.comparisons = {
            role: {
                "phase_noninferiority_passed": True,
                "preservation_passed": True,
            }
            for role in (LF_ONLY_ROLE, LF2_M0_ROLE)
        }
        self.physics = {"final_to_M0": {"passed": True}}
        self.batch_identity = {"passed": True}
        self.m0_gate = {"passed": True}
        self.m1_gate = {"passed": True}

    def _decision(self, **overrides):
        arguments = {
            "contract": self.contract,
            "run_status": "LF2_REFERENCE_BLIND_GPU_TRAJECTORY_COMPLETE",
            "evaluations": self.evaluations,
            "potential_guards": self.guards,
            "comparisons": self.comparisons,
            "physics": self.physics,
            "physics_batch_identity": self.batch_identity,
            "m0_gate": self.m0_gate,
            "m1_gate": self.m1_gate,
        }
        arguments.update(overrides)
        return adjudicate(**arguments)

    def test_numerical_invalid_has_precedence_over_M0_failure(self) -> None:
        guards = dict(self.guards)
        guards[LF2_M0_ROLE] = {"passed": False}
        decision = self._decision(
            run_status="LF2_CALIBRATED_CARRIER_NOT_ESTABLISHED",
            potential_guards=guards,
            m0_gate={"passed": False},
            m1_gate=None,
        )
        self.assertEqual(decision["outcome"], "LF2_NUMERICAL_OR_IDENTITY_INVALID")
        self.assertIsNone(decision["candidate"])

    def test_M0_and_M1_gate_failures_have_distinct_terminal_outcomes(self) -> None:
        m0 = self._decision(
            run_status="LF2_CALIBRATED_CARRIER_NOT_ESTABLISHED",
            m0_gate={"passed": False},
            m1_gate=None,
        )
        self.assertEqual(m0["outcome"], "LF2_CALIBRATED_CARRIER_NOT_ESTABLISHED")
        m1 = self._decision(
            run_status="LF2_FEASIBILITY_PRESERVATION_FAILED",
            m1_gate={"passed": False},
        )
        self.assertEqual(m1["outcome"], "LF2_FEASIBILITY_PRESERVATION_FAILED")

    def test_no_gain_and_provisional_are_separated(self) -> None:
        weak = dict(self.evaluations)
        weak[LF2_FINAL_ROLE] = _report(competent=False)
        negative = self._decision(evaluations=weak)
        self.assertEqual(negative["outcome"], "LF2_NO_PINN_SPECIFIC_GAIN")
        self.assertIsNone(negative["candidate"])
        positive = self._decision()
        self.assertEqual(
            positive["outcome"],
            "LF2_MEASURE_CALIBRATED_FEASIBLE_PINN_PROVISIONAL_SIGNAL",
        )
        self.assertEqual(positive["candidate"], LF2_FINAL_ROLE)

    def test_physics_batch_identity_failure_is_numerical_invalid(self) -> None:
        decision = self._decision(physics_batch_identity={"passed": False})
        self.assertEqual(decision["outcome"], "LF2_NUMERICAL_OR_IDENTITY_INVALID")

    def test_oracle_floor_values_are_hash_bound(self) -> None:
        floors = _component_floors(self.contract)
        self.assertAlmostEqual(floors["phase_roi_continuous_rms"], 0.0045916542647892284)
        self.assertAlmostEqual(
            floors["time_averaged_phase_region_symmetric_difference"], 0.000145
        )

    def test_nominal_evaluation_refuses_before_shutdown(self) -> None:
        with self.assertRaises(PermissionError):
            evaluate_lf2_campaign(
                output_directory=Path("unused"),
                run_directory=Path("unused"),
                cpu_qualification_path=Path("unused"),
                gpu_lifecycle="RUNNING",
            )


if __name__ == "__main__":
    unittest.main()
