from __future__ import annotations

from pathlib import Path
import unittest

import torch

from pinn_pcm_sci.qpop_physics import QPopParameters
from pinn_pcm_sci.qpop_pinn import QPopPINN, interior_residuals, normalized_residual_loss


class QPopPINNTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parameters = QPopParameters.from_input(
            Path("configs/qpop/cpc-v1-imt-intrinsic-voltage-osc-author-case/canonical_input.xml")
        )

    def test_raw_identity_equivalence_and_kc_finite_full_physics_residual(self) -> None:
        torch.manual_seed(5)
        raw = QPopPINN(
            parameters=self.parameters,
            horizon_ns=512.0793,
            method="raw",
            hidden_width=8,
            hidden_layers=2,
        ).double()
        identity = QPopPINN(
            parameters=self.parameters,
            horizon_ns=512.0793,
            method="identity",
            hidden_width=8,
            hidden_layers=2,
        ).double()
        identity.eta_model.load_state_dict(raw.eta_model.state_dict())
        identity.physical_model.load_state_dict(raw.physical_model.state_dict())
        coordinates = torch.tensor(
            [[0.2, 0.3, 0.1], [0.8, 0.7, 0.4], [0.5, 0.2, 0.8]],
            dtype=torch.float64,
        )
        raw_residuals = interior_residuals(raw, coordinates)
        identity_residuals = interior_residuals(identity, coordinates)
        self.assertEqual(set(raw_residuals), set(identity_residuals))
        for name in raw_residuals:
            self.assertTrue(torch.isfinite(raw_residuals[name]).all(), name)
            torch.testing.assert_close(raw_residuals[name], identity_residuals[name])

        kc = QPopPINN(
            parameters=self.parameters,
            horizon_ns=512.0793,
            method="kc",
            hidden_width=8,
            hidden_layers=2,
        ).double()
        residuals = interior_residuals(kc, coordinates)
        loss = normalized_residual_loss(residuals)
        self.assertTrue(torch.isfinite(loss))
        loss.backward()
        self.assertTrue(
            any(parameter.grad is not None for parameter in kc.clock.parameters())
        )
        self.assertTrue((kc.clock.rate(coordinates) > 0.0).all())

    def test_eta_representation_satisfies_the_initial_condition_exactly(self) -> None:
        spatial = torch.tensor(
            [[0.0, 0.0, 0.0], [0.2, 0.7, 0.0], [1.0, 1.0, 0.0]],
            dtype=torch.float64,
        )
        expected = torch.full(
            (spatial.shape[0],),
            self.parameters.eta_initial,
            dtype=torch.float64,
        )
        for method in ("raw", "identity", "kc"):
            torch.manual_seed(23)
            model = QPopPINN(
                parameters=self.parameters,
                horizon_ns=512.0793,
                method=method,
                hidden_width=8,
                hidden_layers=2,
            ).double()
            actual = model(spatial)[:, 0]
            torch.testing.assert_close(actual, expected, atol=1.0e-12, rtol=0.0)


if __name__ == "__main__":
    unittest.main()
