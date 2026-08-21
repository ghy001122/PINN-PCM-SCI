from __future__ import annotations

from pathlib import Path
import unittest

import torch

from pinn_pcm_sci.qpop_physics import QPopParameters
from pinn_pcm_sci.qpop_pinn import QPopPINN, interior_residuals, normalized_residual_loss


class PhaseHotspotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parameters = QPopParameters.from_input(
            Path(
                "configs/qpop/cpc-v1-imt-intrinsic-voltage-osc-author-case/"
                "canonical_input.xml"
            )
        )

    def _model(self, method: str) -> QPopPINN:
        torch.manual_seed(31)
        return QPopPINN(
            parameters=self.parameters,
            horizon_ns=512.0793,
            method=method,
            hidden_width=8,
            hidden_layers=2,
        ).double()

    def test_one_physical_gate_controls_capacity_and_sampling(self) -> None:
        coordinates = torch.tensor(
            [
                [0.50, 0.02, 0.10],
                [0.10, 0.80, 0.30],
                [0.70, 0.40, 0.60],
                [0.30, 0.20, 0.90],
            ],
            dtype=torch.float64,
        )
        shared = self._model("pha_shared")
        diagnostics = shared.phase_hotspot_diagnostics(coordinates)
        self.assertEqual(diagnostics.fields.shape, (4, 7))
        self.assertEqual(diagnostics.physical_gate.shape, (4, 1))
        self.assertTrue((diagnostics.physical_gate > 0.0).all())
        self.assertTrue((diagnostics.physical_gate <= 1.0).all())
        torch.testing.assert_close(
            diagnostics.capacity_gate, diagnostics.physical_gate
        )
        torch.testing.assert_close(
            shared.collocation_weights(coordinates),
            1.0 + shared.sampling_gain * diagnostics.physical_gate,
        )
        self.assertFalse(
            any("gate" in name for name, _ in shared.named_parameters()),
            "the interpretable gate must not introduce a learned oracle proxy",
        )

        capacity_only = self._model("pha_capacity")
        capacity_only.load_state_dict(shared.state_dict())
        capacity_diagnostics = capacity_only.phase_hotspot_diagnostics(coordinates)
        torch.testing.assert_close(
            capacity_diagnostics.capacity_gate,
            capacity_diagnostics.physical_gate,
        )
        torch.testing.assert_close(
            capacity_only.collocation_weights(coordinates),
            torch.ones_like(capacity_diagnostics.physical_gate),
        )

        sampling_only = self._model("pha_sampling")
        sampling_only.load_state_dict(shared.state_dict())
        sampling_diagnostics = sampling_only.phase_hotspot_diagnostics(coordinates)
        torch.testing.assert_close(
            sampling_diagnostics.capacity_gate,
            torch.ones_like(sampling_diagnostics.physical_gate),
        )
        torch.testing.assert_close(
            sampling_only.collocation_weights(coordinates),
            1.0 + sampling_only.sampling_gain * sampling_diagnostics.physical_gate,
        )

        global_fourier = self._model("fourier_global")
        global_fourier.load_state_dict(shared.state_dict())
        global_diagnostics = global_fourier.phase_hotspot_diagnostics(coordinates)
        torch.testing.assert_close(
            global_diagnostics.capacity_gate,
            torch.ones_like(global_diagnostics.physical_gate),
        )
        torch.testing.assert_close(
            global_fourier.collocation_weights(coordinates),
            torch.ones_like(global_diagnostics.physical_gate),
        )

    def test_shared_sampling_selects_the_same_gate_hotspots(self) -> None:
        model = self._model("pha_shared")
        candidates = torch.rand((24, 3), generator=torch.Generator().manual_seed(4), dtype=torch.float64)
        weights = model.collocation_weights(candidates)
        selected = model.select_interior(candidates, count=6)
        expected_indices = torch.topk(weights[:, 0], k=6, largest=True, sorted=True).indices
        torch.testing.assert_close(selected, candidates[expected_indices])

    def test_pha_full_qpop_residual_is_finite_and_trains_frequency_branches(self) -> None:
        model = self._model("pha_shared")
        coordinates = torch.tensor(
            [[0.2, 0.3, 0.1], [0.8, 0.7, 0.4]], dtype=torch.float64
        )
        residuals = interior_residuals(model, coordinates)
        loss = normalized_residual_loss(residuals)
        self.assertTrue(torch.isfinite(loss))
        loss.backward()
        self.assertTrue(
            any(
                parameter.grad is not None and torch.isfinite(parameter.grad).all()
                for parameter in model.phase_hotspot.parameters()
            )
        )


if __name__ == "__main__":
    unittest.main()
