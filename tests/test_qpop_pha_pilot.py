from __future__ import annotations

import unittest

from pathlib import Path

import torch

from pinn_pcm_sci.qpop_method_pilot import (
    PilotBatches,
    _all_residuals,
    _train_method,
)
from pinn_pcm_sci.qpop_pha_pilot import adjudicate_pha_screen
from pinn_pcm_sci.qpop_physics import QPopParameters
from pinn_pcm_sci.qpop_pinn import QPopPINN, residual_scales


class QPopPHAPilotTests(unittest.TestCase):
    def test_shared_gate_requires_attribution_wins_and_physics_noninferiority(self) -> None:
        metrics = {
            "fourier_global": {
                "structure_symmetric_difference_cycle_equal": 0.20,
                "device_trajectory_nrmse": 0.80,
            },
            "pha_capacity": {
                "structure_symmetric_difference_cycle_equal": 0.19,
                "device_trajectory_nrmse": 0.79,
            },
            "pha_sampling": {
                "structure_symmetric_difference_cycle_equal": 0.18,
                "device_trajectory_nrmse": 0.78,
            },
            "pha_shared": {
                "structure_symmetric_difference_cycle_equal": 0.15,
                "device_trajectory_nrmse": 0.75,
            },
        }
        training = {
            method: {"checkpoint_score": {"max_normalized_violation": value}}
            for method, value in {
                "fourier_global": 1.0,
                "pha_capacity": 1.01,
                "pha_sampling": 1.02,
                "pha_shared": 1.03,
            }.items()
        }
        result = adjudicate_pha_screen(
            metrics, training, min_structure_effect=1.0e-3, physics_noninferiority_ratio=1.05
        )
        self.assertEqual(result["disposition"], "DEVELOPMENT_PHA_SIGNAL_PRESENT")
        self.assertTrue(result["all_required_checks_pass"])

        tied = {method: dict(value) for method, value in metrics.items()}
        tied["pha_shared"]["structure_symmetric_difference_cycle_equal"] = 0.18
        result = adjudicate_pha_screen(
            tied, training, min_structure_effect=1.0e-3, physics_noninferiority_ratio=1.05
        )
        self.assertEqual(result["disposition"], "DEVELOPMENT_PHA_SIGNAL_NOT_DETECTED")
        self.assertFalse(result["all_required_checks_pass"])

    def test_frequency_branch_parameterization_does_not_explode_first_physics_step(self) -> None:
        parameters = QPopParameters.from_input(
            Path(
                "configs/qpop/cpc-v1-imt-intrinsic-voltage-osc-author-case/"
                "canonical_input.xml"
            )
        )
        previous_dtype = torch.get_default_dtype()
        try:
            # The command-line runner starts from PyTorch's float32 default and
            # then converts the complete model to float64.  Isolate this test
            # from another test module's process-global default-dtype change.
            torch.set_default_dtype(torch.float32)
            torch.manual_seed(17)
            model = QPopPINN(
                parameters=parameters,
                horizon_ns=512.0793,
                method="pha_shared",
                hidden_width=24,
                hidden_layers=3,
            ).double()
            audit = PilotBatches.fixed(
                seed=100017, interior=12, initial=8, boundary_per_side=5
            )
            scales = residual_scales(_all_residuals(model, audit))
            training = _train_method(
                model=model,
                seed=17,
                updates=1,
                scales=scales,
                audit_batches=audit,
            )
        finally:
            torch.set_default_dtype(previous_dtype)
        first_step = training["history"][-1]
        self.assertLess(first_step["physics_audit_max"], 10.0)


if __name__ == "__main__":
    unittest.main()
