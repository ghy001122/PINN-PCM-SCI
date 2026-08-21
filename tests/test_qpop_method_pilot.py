from __future__ import annotations

from pathlib import Path
import unittest

import torch

from pinn_pcm_sci.qpop_method_pilot import PilotBatches, pilot_loss, training_batches
from pinn_pcm_sci.qpop_physics import QPopParameters
from pinn_pcm_sci.qpop_pinn import QPopPINN


class QPopMethodPilotTests(unittest.TestCase):
    def test_pilot_loss_uses_physics_ic_boundary_and_clock_without_oracle_labels(self) -> None:
        parameters = QPopParameters.from_input(
            Path("configs/qpop/cpc-v1-imt-intrinsic-voltage-osc-author-case/canonical_input.xml")
        )
        model = QPopPINN(
            parameters=parameters,
            horizon_ns=512.0793,
            method="kc",
            hidden_width=8,
            hidden_layers=2,
        ).double()
        batches = PilotBatches.fixed(seed=7, interior=3, initial=2, boundary_per_side=2)
        loss, components = pilot_loss(model, batches, stop_gradient_clock_target=True)
        self.assertTrue(torch.isfinite(loss))
        self.assertIn("interior", components)
        self.assertIn("initial", components)
        self.assertIn("boundary", components)
        self.assertIn("clock_alignment", components)
        loss.backward()
        self.assertTrue(any(p.grad is not None for p in model.clock.parameters()))

    def test_pha_training_batches_use_the_model_gate_only_for_sampling_arms(self) -> None:
        parameters = QPopParameters.from_input(
            Path("configs/qpop/cpc-v1-imt-intrinsic-voltage-osc-author-case/canonical_input.xml")
        )
        shared = QPopPINN(
            parameters=parameters,
            horizon_ns=512.0793,
            method="pha_shared",
            hidden_width=8,
            hidden_layers=2,
        ).double()
        batches, audit = training_batches(
            shared,
            seed=23,
            interior=4,
            initial=2,
            boundary_per_side=2,
            candidate_multiplier=4,
        )
        self.assertEqual(batches.interior.shape, (4, 3))
        self.assertEqual(audit["candidate_count"], 16)
        self.assertTrue(audit["gate_adaptive"])
        self.assertGreaterEqual(
            audit["selected_gate_mean"], audit["candidate_gate_mean"]
        )

        capacity = QPopPINN(
            parameters=parameters,
            horizon_ns=512.0793,
            method="pha_capacity",
            hidden_width=8,
            hidden_layers=2,
        ).double()
        capacity.load_state_dict(shared.state_dict())
        _, capacity_audit = training_batches(
            capacity,
            seed=23,
            interior=4,
            initial=2,
            boundary_per_side=2,
            candidate_multiplier=4,
        )
        self.assertFalse(capacity_audit["gate_adaptive"])
        self.assertEqual(capacity_audit["candidate_count"], 16)


if __name__ == "__main__":
    unittest.main()
