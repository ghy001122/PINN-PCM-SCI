from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from pinn_pcm_sci.qpop_physics import QPopParameters
from pinn_pcm_sci.reduced_oracle import (
    ReducedOracleCase,
    ReducedOracleGrid,
    bulk_free_energy,
    pulse_train_voltage,
    reduced_result_to_artifact,
    stable_mu_equilibrium,
)
import pinn_pcm_sci.reduced_oracle as reduced_oracle


INPUT = Path(
    "configs/qpop/cpc-v1-imt-intrinsic-voltage-osc-author-case/canonical_input.xml"
)


class ReducedOracleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parameters = QPopParameters.from_input(INPUT)

    def test_stable_mu_is_a_stable_local_minimum_of_frozen_qpop_free_energy(self) -> None:
        eta = np.asarray([[0.2, 0.8], [1.0, 1.2]])
        temperature = np.asarray([[0.89, 0.95], [1.0, 1.05]])
        tc_variance = np.zeros_like(eta)

        mu = stable_mu_equilibrium(self.parameters, eta, temperature, tc_variance)
        epsilon = 1.0e-5
        left = bulk_free_energy(
            self.parameters, eta, mu - epsilon, temperature, tc_variance
        )
        center = bulk_free_energy(
            self.parameters, eta, mu, temperature, tc_variance
        )
        right = bulk_free_energy(
            self.parameters, eta, mu + epsilon, temperature, tc_variance
        )

        self.assertTrue(np.all(np.isfinite(mu)))
        self.assertTrue(np.all(center <= left + 1.0e-9))
        self.assertTrue(np.all(center <= right + 1.0e-9))

    def test_four_pulse_drive_has_five_ns_edges_and_sixty_ns_on_off_windows(self) -> None:
        amplitude = 9.0
        values = pulse_train_voltage(
            np.asarray([0.0, 2.5, 5.0, 60.0, 62.5, 65.0, 120.0, 125.0, 480.0]),
            amplitude=amplitude,
        )

        np.testing.assert_allclose(
            values,
            [0.0, 4.5, 9.0, 9.0, 4.5, 0.0, 0.0, 9.0, 0.0],
        )

    def test_one_allen_cahn_step_does_not_repeat_the_full_mu_search(self) -> None:
        eta = np.full(24, self.parameters.eta_initial)
        temperature = np.full(24, self.parameters.temperature_initial)
        tc_variance = np.zeros(24)

        with patch(
            "pinn_pcm_sci.reduced_oracle.stable_mu_equilibrium",
            wraps=reduced_oracle.stable_mu_equilibrium,
        ) as equilibrium:
            reduced_oracle._reaction_step(
                self.parameters, eta, temperature, tc_variance, 1.0
            )

        self.assertLessEqual(equilibrium.call_count, 2)

    def test_tiny_independent_oracle_smoke_is_finite_and_records_balances(self) -> None:
        result = ReducedOracleCase(
            parameters=self.parameters,
            grid=ReducedOracleGrid(nx=6, ny=4),
            end_time_ns=2.0,
            time_step_ns=1.0,
            drive_voltage_v=0.0,
            series_resistance_ohm=5.0e5,
            save_every=1,
        ).solve()

        self.assertEqual(result.eta.shape, (3, 24))
        self.assertTrue(np.all(np.isfinite(result.eta)))
        self.assertTrue(np.all(np.isfinite(result.temperature)))
        self.assertLessEqual(result.max_balance_violation, 0.01)

        artifact = reduced_result_to_artifact(
            result,
            grid=ReducedOracleGrid(nx=6, ny=4),
            case_id="tiny-reduced-oracle",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "case.h5"
            artifact.write(path)
            self.assertEqual(artifact.read(path).case_id, "tiny-reduced-oracle")


if __name__ == "__main__":
    unittest.main()
