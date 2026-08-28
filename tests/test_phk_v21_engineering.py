from __future__ import annotations

from pathlib import Path
import unittest

from pinn_pcm_sci.phk_benchmark import (
    PhkControl,
    PhkPhysicalContract,
    PhkResolution,
)
from pinn_pcm_sci.phk_v21_engineering import (
    PhkV21EngineeringOverrides,
    build_engineering_physical,
    run_engineering_case,
)
from pinn_pcm_sci.phk_v21_solver import PhkV21PhaseAlgorithm


ROOT = Path(__file__).resolve().parents[1]
PROGRAM_V2 = ROOT / "configs" / "phk_v2" / "program_contract.json"
OBJECT_V2 = ROOT / "configs" / "phk_v2" / "object_numerical_contract.json"
PROGRAM_V21 = ROOT / "configs" / "phk_v21" / "program_contract.json"


class PhkV21EngineeringHarnessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.legacy = PhkPhysicalContract.from_files(
            program_path=PROGRAM_V2,
            object_path=OBJECT_V2,
        )

    def test_engineering_view_changes_only_the_in_memory_identity(self) -> None:
        overrides = PhkV21EngineeringOverrides(
            case_id="TEST_VIEW",
            period=1.5,
            volumetric_cooling=4.0,
            mobility_cold=1.0,
            thermal_drive=6.0,
        )
        view = build_engineering_physical(
            legacy=self.legacy,
            phk_v21_program_path=PROGRAM_V21,
            overrides=overrides,
        )
        self.assertEqual(float(view.coordinates["time_end"]), 3.0)
        self.assertEqual(float(view.coefficients["volumetric_cooling"]), 4.0)
        self.assertEqual(view.payload["fields"]["phase_fraction"]["range_guard"], [0.0, 1.0])
        self.assertEqual(
            self.legacy.payload["fields"]["phase_fraction"]["range_guard"],
            [1.0e-8, 0.99999999],
        )

    def test_small_zero_drive_engineering_case_is_non_voting_and_guarded(self) -> None:
        resolution = PhkResolution.non_scientific_fixture(
            nx=12,
            nz=6,
            dt=0.01,
            time_end=0.05,
            save_every=1,
        )
        run = run_engineering_case(
            legacy=self.legacy,
            phk_v21_program_path=PROGRAM_V21,
            overrides=PhkV21EngineeringOverrides(case_id="TEST_ZERO"),
            control=PhkControl.ZERO_DRIVE,
            resolution=resolution,
            algorithm=PhkV21PhaseAlgorithm.LOGIT_NEWTON_ANALYTIC_JACOBIAN,
        )
        self.assertEqual(run.evidence_identity, "NON_VOTING_ENGINEERING_ONLY")
        self.assertTrue(run.guard.passed)
        self.assertEqual(run.phase_solver_statistics["phase_output_clipping_total"], 0)


if __name__ == "__main__":
    unittest.main()
