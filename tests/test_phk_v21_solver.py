from __future__ import annotations

import json
from pathlib import Path
import unittest

import numpy as np

from pinn_pcm_sci.phk_benchmark import (
    PhkGrid,
    PhkPhysicalContract,
    _phase_residual_and_jacobian,
    _solve_phase_newton,
)
from pinn_pcm_sci.phk_v21_solver import (
    PhkV21PhaseAlgorithm,
    solve_phase_candidate,
)


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "configs" / "phk_v2" / "program_contract.json"
OBJECT = ROOT / "configs" / "phk_v2" / "object_numerical_contract.json"
ENGINEERING = ROOT / "configs" / "phk_v21" / "engineering_contract.json"


class PhkV21PhaseSolverRegressionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.physical = PhkPhysicalContract.from_files(
            program_path=PROGRAM,
            object_path=OBJECT,
        )
        payload = json.loads(ENGINEERING.read_text(encoding="utf-8"))
        fixture = payload["p0_red_fixture"]
        grid = fixture["grid"]
        self.grid = PhkGrid.build(
            nx=int(grid["nx"]),
            nz=int(grid["nz"]),
            x_min=float(grid["x_min"]),
            x_max=float(grid["x_max"]),
            z_min=float(grid["z_min"]),
            z_max=float(grid["z_max"]),
        )
        self.phase_old = np.asarray(fixture["phase_old"], dtype=np.float64)
        self.initial_guess = np.asarray(fixture["initial_guess"], dtype=np.float64)
        self.temperature = np.asarray(fixture["temperature"], dtype=np.float64)
        self.dt = float(fixture["dt"])

    def _kwargs(self) -> dict[str, object]:
        return {
            "phase_old": self.phase_old,
            "initial_guess": self.initial_guess,
            "temperature": self.temperature,
            "grid": self.grid,
            "dt": self.dt,
            "coefficients": dict(self.physical.coefficients),
            "interface_width": 0.04,
            "solver": self.physical.nonlinear_solver,
        }

    def test_frozen_legacy_inner_guard_reproduces_exact_failure(self) -> None:
        with self.assertRaisesRegex(
            RuntimeError,
            "PHK phase Newton line search reached its frozen minimum step",
        ):
            _solve_phase_newton(
                **self._kwargs(),
                lower_bound=1.0e-8,
                upper_bound=0.99999999,
            )

    def test_analytic_jacobian_is_accurate_at_the_failure_state(self) -> None:
        residual, jacobian = _phase_residual_and_jacobian(
            self.initial_guess,
            phase_old=self.phase_old,
            temperature=self.temperature,
            grid=self.grid,
            dt=self.dt,
            coefficients=dict(self.physical.coefficients),
            interface_width=0.04,
        )
        direction = np.asarray((0.5, -0.2, 0.3, -0.4), dtype=np.float64)
        direction /= np.linalg.norm(direction)
        step = 1.0e-7
        plus, _ = _phase_residual_and_jacobian(
            self.initial_guess + step * direction,
            phase_old=self.phase_old,
            temperature=self.temperature,
            grid=self.grid,
            dt=self.dt,
            coefficients=dict(self.physical.coefficients),
            interface_width=0.04,
        )
        minus, _ = _phase_residual_and_jacobian(
            self.initial_guess - step * direction,
            phase_old=self.phase_old,
            temperature=self.temperature,
            grid=self.grid,
            dt=self.dt,
            coefficients=dict(self.physical.coefficients),
            interface_width=0.04,
        )
        finite_difference = (plus - minus) / (2.0 * step)
        relative = np.linalg.norm(finite_difference - jacobian @ direction) / np.linalg.norm(
            finite_difference
        )
        self.assertLess(relative, 2.0e-7)
        self.assertGreater(float(np.max(np.abs(residual))), 1.0e-10)

    def test_all_eligible_phase_candidates_resolve_the_minimized_failure(self) -> None:
        for algorithm in (
            PhkV21PhaseAlgorithm.TRUST_REGION_REFLECTIVE_PHASE,
            PhkV21PhaseAlgorithm.LOGIT_NEWTON_ANALYTIC_JACOBIAN,
            PhkV21PhaseAlgorithm.PSEUDO_TRANSIENT_NEWTON,
        ):
            with self.subTest(algorithm=algorithm.value):
                solved = solve_phase_candidate(
                    algorithm=algorithm,
                    **self._kwargs(),
                    lower_bound=0.0,
                    upper_bound=1.0,
                )
                self.assertTrue(solved.converged)
                self.assertLessEqual(solved.final_residual_inf, 1.0e-10)
                self.assertGreaterEqual(float(np.min(solved.phase)), 0.0)
                self.assertLessEqual(float(np.max(solved.phase)), 1.0)
                self.assertEqual(solved.output_clipping_count, 0)


if __name__ == "__main__":
    unittest.main()
