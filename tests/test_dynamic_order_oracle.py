from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

import numpy as np

from pinn_pcm_sci.dynamic_order_oracle import (
    DynamicOrderOracleCase,
    dynamic_result_to_artifact,
)
from pinn_pcm_sci.qpop_physics import QPopParameters
from pinn_pcm_sci.reduced_oracle import ReducedOracleGrid


ROOT = Path(__file__).resolve().parents[1]
INPUT = (
    ROOT
    / "configs"
    / "qpop"
    / "cpc-v1-imt-intrinsic-voltage-osc"
    / "canonical_input.xml"
)


class DynamicOrderOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parameters = QPopParameters.from_input(INPUT)

    def test_zero_mobility_manufactured_state_is_preserved(self) -> None:
        parameters = replace(
            self.parameters,
            structural_mobility=0.0,
            electronic_mobility=0.0,
        )
        result = DynamicOrderOracleCase(
            parameters=parameters,
            grid=ReducedOracleGrid(6, 4),
            end_time_ns=2.0,
            time_step_ns=1.0,
            drive_voltage_v=0.0,
            series_resistance_ohm=5.0e5,
            save_every=1,
        ).solve()

        np.testing.assert_allclose(result.eta, parameters.eta_initial, atol=1.0e-12)
        np.testing.assert_allclose(result.mu, parameters.mu_initial, atol=1.0e-12)
        np.testing.assert_allclose(
            result.temperature, parameters.temperature_initial * 338.0, atol=1.0e-9
        )
        self.assertLessEqual(result.max_balance_violation, 1.0e-10)

    def test_dynamic_mu_is_an_independent_state_and_smoke_is_finite(self) -> None:
        result = DynamicOrderOracleCase(
            parameters=self.parameters,
            grid=ReducedOracleGrid(6, 4),
            end_time_ns=2.0,
            time_step_ns=1.0,
            drive_voltage_v=0.0,
            series_resistance_ohm=5.0e5,
            save_every=1,
        ).solve()

        np.testing.assert_allclose(result.mu[0], self.parameters.mu_initial, atol=0.0)
        self.assertTrue(np.all(np.isfinite(result.eta)))
        self.assertTrue(np.all(np.isfinite(result.mu)))
        self.assertTrue(np.all(np.isfinite(result.temperature)))
        self.assertLessEqual(result.max_balance_violation, 0.01)

    def test_driven_stiff_branch_uses_the_frozen_tenth_ns_step(self) -> None:
        result = DynamicOrderOracleCase(
            parameters=self.parameters,
            grid=ReducedOracleGrid(6, 4),
            end_time_ns=1.0,
            time_step_ns=0.1,
            drive_voltage_v=9.0,
            series_resistance_ohm=5.0e5,
            save_every=10,
        ).solve()

        self.assertTrue(np.all(np.isfinite(result.eta)))
        self.assertTrue(np.all(np.isfinite(result.mu)))
        self.assertLessEqual(result.max_balance_violation, 0.01)

    def test_artifact_names_dynamic_mu_and_r4_contract(self) -> None:
        grid = ReducedOracleGrid(6, 4)
        result = DynamicOrderOracleCase(
            parameters=replace(
                self.parameters,
                structural_mobility=0.0,
                electronic_mobility=0.0,
            ),
            grid=grid,
            end_time_ns=1.0,
            time_step_ns=1.0,
            drive_voltage_v=0.0,
            series_resistance_ohm=5.0e5,
            save_every=1,
        ).solve()
        artifact = dynamic_result_to_artifact(
            result, grid=grid, case_id="qpop-r4-v1-test"
        )

        self.assertEqual(artifact.physical_contract_id, "qpop-r4-v1")
        self.assertEqual(
            artifact.evidence_identity,
            "QPOP_R4_V1_DYNAMIC_ORDER_REDUCED_SYNTHETIC_ORACLE",
        )
        self.assertIn("mu", artifact.fields)
        self.assertNotIn("mu_equilibrium", artifact.fields)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "case.h5"
            artifact.write(path)
            loaded = artifact.read(path)
        self.assertEqual(loaded.case_id, "qpop-r4-v1-test")


if __name__ == "__main__":
    unittest.main()
