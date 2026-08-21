from __future__ import annotations

from pathlib import Path
import unittest

import torch

from pinn_pcm_sci.qpop_physics import QPopParameters, dfermi, fermi


class QPopPhysicsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.input_path = Path(
            "configs/qpop/cpc-v1-imt-intrinsic-voltage-osc-author-case/canonical_input.xml"
        )

    def test_canonical_input_is_resolved_in_qpop_dimensionless_units(self) -> None:
        parameters = QPopParameters.from_input(self.input_path)
        self.assertEqual(parameters.lx, 100.0)
        self.assertEqual(parameters.ly, 40.0)
        self.assertEqual(parameters.lz, 20.0)
        self.assertEqual(parameters.terminal_time, 2000.0)
        self.assertEqual(parameters.drive_voltage, 9000.0)
        self.assertAlmostEqual(parameters.substrate_temperature, 300.0 / 338.0)
        self.assertAlmostEqual(parameters.eta_initial, 1.119)
        self.assertAlmostEqual(parameters.mu_initial, -1.293)
        self.assertGreater(parameters.electron_density_of_states, 0.0)
        self.assertGreater(parameters.structural_mobility, 0.0)

    def test_frozen_nucleus_and_fermi_relations_are_finite_and_monotone(self) -> None:
        parameters = QPopParameters.from_input(self.input_path)
        coordinates = torch.tensor(
            [[parameters.lx / 2.0, 0.0], [0.0, parameters.ly]],
            dtype=torch.float64,
        )
        variation = parameters.tc_variance(coordinates)
        self.assertLess(float(variation[0]), -0.01)
        self.assertAlmostEqual(float(variation[1]), 0.0, places=4)

        gamma = torch.linspace(-20.0, 20.0, 17, dtype=torch.float64)
        values = fermi(gamma)
        derivatives = dfermi(gamma)
        self.assertTrue(torch.isfinite(values).all())
        self.assertTrue(torch.isfinite(derivatives).all())
        self.assertTrue((derivatives > 0.0).all())
        self.assertTrue((torch.diff(values) > 0.0).all())


if __name__ == "__main__":
    unittest.main()
