from __future__ import annotations

from types import SimpleNamespace
import unittest

import numpy as np
import torch

from pinn_pcm_sci.phk_v22r_training import load_case_physics
from pinn_pcm_sci.phk_v23_lf2 import CATEGORY_NAMES, MeasureBatch, MediumMeasureDataset
from pinn_pcm_sci.phk_v23_lf3 import (
    LOGIT_SPAN,
    Q_ABSOLUTE_BOUND,
    carrier_gate,
    load_contracts,
    measure_decoupled_terms,
    p0_preservation_gate,
    phase_logit_targets,
)


def _synthetic_result(physics):
    time = np.asarray([0.0, 0.1, 0.2, 0.3, 0.35, 0.4, 0.8, 1.25, 1.35, 1.45, 1.55, 1.6, 1.7, 2.0, 2.5])
    x = np.asarray([-0.25, 0.25, 0.8, -0.8])
    z = np.asarray([0.2, 0.5, 0.8, 0.8])
    phase_line = np.asarray([0.03,0.2,0.6,0.9,0.8,0.7,0.1,0.03,0.2,0.6,0.9,0.8,0.7,0.1,0.03])
    phase = np.full((time.size, x.size), 0.03)
    phase[:, 0] = phase_line
    temperature = 0.2 + 0.4 * phase
    waveform = physics.waveform(torch.as_tensor(time, dtype=torch.float64).reshape(-1, 1)).numpy()
    zeta = (z - physics.z_min) / (physics.z_max - physics.z_min)
    potential = waveform * (0.25 + 0.75 * zeta[None, :])
    return SimpleNamespace(
        time=time, grid=SimpleNamespace(cell_x=x, cell_z=z, cell_volumes=np.asarray([1.0,2.0,1.5,0.5])),
        case=SimpleNamespace(period=1.25), potential=potential, temperature=temperature, phase=phase,
    )


class _DiagnosticsModel(torch.nn.Module):
    def read_only_output_diagnostics(self, coordinates):
        fields = torch.stack((coordinates[:, 0], coordinates[:, 1], torch.full_like(coordinates[:, 0], 0.25)), dim=1)
        latent = torch.zeros((coordinates.shape[0], 1), dtype=coordinates.dtype)
        return SimpleNamespace(output=SimpleNamespace(fields=fields), latents={"phase": latent})


def _audit(error=0.4):
    cycle = {"hard_recall": 0.95, "hard_precision": 0.9, "hard_active_mass_ratio": 1.0, "event_time_absolute_error": 0.001}
    topology_cycle = {"peak_roi_fraction": 0.2, "peak_full_domain_fraction": 0.2, "peak_outside_roi_fraction": 0.05, "recovery_fraction": 0.8}
    return {
        "all_values_finite": True, "phase_range": {"passed": True},
        "potential_maximum_principle": {"passed": True}, "phase_maximum": 0.95,
        "two_cycle_events": True, "event_metrics": {"cycle_1": dict(cycle), "cycle_2": dict(cycle)},
        "event_topology_hard_guard": {"passed": True, "cycles": [dict(topology_cycle), dict(topology_cycle)]},
        "weighted_errors": {"potential": error, "temperature": error, "phase": error},
        "topology_weighted_loss": error,
    }


class LF3MathAndMeasureTests(unittest.TestCase):
    def setUp(self):
        self.physics, _, _ = load_case_physics("FULL")
        self.dataset = MediumMeasureDataset(_synthetic_result(self.physics), physics=self.physics)

    def test_phase_logit_teacher_is_exact_and_masks_t0(self):
        coordinates = torch.tensor([[0.0,0.2,0.0],[0.0,0.2,0.1]], dtype=torch.float64)
        target = torch.tensor([[0.99999999],[0.9]], dtype=torch.float64)
        delta, startup, mask = phase_logit_targets(coordinates, target, physics=self.physics)
        initial = self.physics.initial_phase(coordinates).clamp(1e-8, 1-1e-8)
        reconstructed = torch.sigmoid(torch.logit(initial) + delta)
        self.assertTrue(torch.allclose(reconstructed, target.clamp(1e-8,1-1e-8), atol=1e-12, rtol=0.0))
        self.assertEqual(mask.reshape(-1).tolist(), [False, True])
        self.assertEqual(float(startup[0]), 0.0)
        self.assertLessEqual(float(torch.max(torch.abs(delta / 8.0))), Q_ABSOLUTE_BOUND + 1e-12)

    def test_phase_loss_is_equal_category_while_v_t_use_target_mass(self):
        coordinates = torch.tensor([[1.0,2.0,0.25]] * len(CATEGORY_NAMES), dtype=torch.float64)
        targets = torch.zeros_like(coordinates)
        masses = {name: (index + 1) / sum(range(1, len(CATEGORY_NAMES)+1)) for index, name in enumerate(CATEGORY_NAMES)}
        batch = MeasureBatch(coordinates, targets, {name: 1 for name in CATEGORY_NAMES}, masses, "A" * 64)
        terms = measure_decoupled_terms(_DiagnosticsModel(), batch, physics=self.physics, device=torch.device("cpu"))
        self.assertAlmostEqual(float(terms["potential"]), (1.0 / self.physics.waveform_amplitude) ** 2)
        self.assertAlmostEqual(float(terms["temperature"]), (2.0 / self.physics.theta_transition) ** 2)
        self.assertEqual(len(terms["category_phase_logit"]), 14)
        self.assertAlmostEqual(LOGIT_SPAN, 2.0 * np.log((1.0 - 1e-8) / 1e-8))


class LF3GateAndContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = load_contracts()["decision"]

    def test_contract_freezes_one_combination_pilot_without_d0_or_stress(self):
        contracts = load_contracts()
        self.assertEqual(contracts["program"]["hard_limits"]["maximum_scientific_gpu_trajectories"], 1)
        self.assertEqual(contracts["program"]["hard_limits"]["maximum_optimizer_updates"], 2400)
        self.assertFalse(contracts["program"]["authorization"]["d0_diagnostic_campaign"])
        self.assertFalse(contracts["program"]["authorization"]["stress_prediction_or_unseal"])
        mapping = self.contract["machine_outcomes_and_unique_next"]
        self.assertEqual(len(mapping), 15)
        self.assertEqual(len(mapping), len(set(mapping.values())))

    def test_temporal_only_failure_is_distinct(self):
        baseline = _audit(1.0)
        candidate = _audit(0.4)
        candidate["event_metrics"]["cycle_1"]["event_time_absolute_error"] = 0.01
        gate = carrier_gate(candidate, baseline, contract=self.contract)
        self.assertFalse(gate["passed"])
        self.assertTrue(gate["temporal_only_failure"])
        self.assertEqual(gate["failure_outcome"], "LF3_TEMPORAL_CARRIER_FAILURE")

    def test_p0_preservation_requires_exact_physics_stream(self):
        baseline, t0, p0 = _audit(1.0), _audit(0.4), _audit(0.41)
        passed = p0_preservation_gate(p0, t0, baseline, contract=self.contract, physics_stream_sha256="536E6706A0B68EBB1277A97F402D273AFA2EA1E0B27106F26CB4222B7EC05C53")
        self.assertTrue(passed["passed"])
        failed = p0_preservation_gate(p0, t0, baseline, contract=self.contract, physics_stream_sha256="0" * 64)
        self.assertFalse(failed["passed"])


if __name__ == "__main__":
    unittest.main()
