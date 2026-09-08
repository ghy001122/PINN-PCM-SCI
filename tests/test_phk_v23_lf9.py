from __future__ import annotations

import json
import math
from pathlib import Path
import tempfile
import unittest

import numpy as np
import torch

from pinn_pcm_sci import phk_v23_lf9 as lf9
from pinn_pcm_sci import phk_v23_lf9_qualification as qualification


def _audit(*, temperature_ratio: float = 1.0, timing_1: float = 0.004) -> dict:
    return {
        "all_values_finite": True,
        "phase_minimum": 0.0,
        "phase_maximum": 0.95,
        "potential_guard": {
            "passed": True,
            "global": {
                "maximum_absolute_excess": 0.0,
                "violation_fraction": 0.0,
            },
        },
        "cycles": {
            "cycle_1": {
                "event_exists": True,
                "hard_recall": 0.92,
                "hard_precision": 0.90,
                "hard_active_mass_ratio": 1.0,
                "event_time_absolute_error": timing_1,
                "roi_peak_fraction": 0.1,
                "full_domain_peak_fraction": 0.2,
                "outside_roi_peak_fraction": 0.05,
                "recovery_fraction": 0.9,
            },
            "cycle_2": {
                "event_exists": True,
                "hard_recall": 0.93,
                "hard_precision": 0.91,
                "hard_active_mass_ratio": 1.0,
                "event_time_absolute_error": 0.004,
                "roi_peak_fraction": 0.1,
                "full_domain_peak_fraction": 0.2,
                "outside_roi_peak_fraction": 0.05,
                "recovery_fraction": 0.9,
            },
        },
        "weighted_errors": {
            "potential": lf9.DEV_R_BASELINE["potential"],
            "temperature": lf9.DEV_R_BASELINE["temperature"] * temperature_ratio,
            "phase": lf9.DEV_R_BASELINE["phase"],
        },
        "topology_weighted_loss": lf9.DEV_R_TOPOLOGY,
    }


class _Physics:
    latent_ratio = 2.0
    thermal_diffusivity = 1.0
    volumetric_cooling = 0.0
    joule_gain = 0.0

    @staticmethod
    def conductivity(temperature: torch.Tensor, phase: torch.Tensor) -> torch.Tensor:
        return torch.ones_like(temperature)


class _AnalyticModel(torch.nn.Module):
    def __init__(self, mode: str) -> None:
        super().__init__()
        self.mode = mode
        self.physics = _Physics()

    def forward(self, q: torch.Tensor) -> torch.Tensor:
        x, z, t = q[:, 0:1], q[:, 1:2], q[:, 2:3]
        zero = 0.0 * x
        if self.mode == "linear_time":
            return torch.cat((zero, t, zero), dim=1)
        if self.mode == "quadratic_space":
            return torch.cat((zero, x.square() + z.square(), zero), dim=1)
        raise AssertionError(self.mode)


class _ThreeHead(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.encoders = torch.nn.ModuleDict(
            {name: torch.nn.Linear(1, 1, bias=False) for name in ("potential", "temperature", "phase")}
        )
        self.heads = torch.nn.ModuleDict(
            {name: torch.nn.Linear(1, 1, bias=False) for name in ("potential", "temperature", "phase")}
        )


class LF9ContractAndRoutingTests(unittest.TestCase):
    def test_contracts_freeze_two_screens_and_original_denominators(self) -> None:
        contracts = lf9.load_contracts()
        self.assertEqual(tuple(contracts["method"]["filter"]["learning_rate_ladder"]), lf9.LR_LADDER)
        self.assertEqual(contracts["method"]["equation_routing"]["pde_denominator"], 3)
        self.assertEqual(set(contracts["method"]["arms"]), {lf9.ER_S, lf9.ER_CV})
        self.assertEqual(contracts["program"]["hard_limits"]["required_screen_arms"], 2)

    def test_equation_gradients_are_routed_to_owned_head_from_one_pre_step_graph(self) -> None:
        model = _ThreeHead().double()
        params = lf9.field_parameter_groups(model)
        p = next(iter(params["potential"]))
        t = next(iter(params["temperature"]))
        f = next(iter(params["phase"]))
        losses = {
            "potential": p.sum() + 10.0 * t.sum() + 100.0 * f.sum(),
            "temperature": 2.0 * p.sum() + 3.0 * t.sum() + 5.0 * f.sum(),
            "phase": 7.0 * p.sum() + 11.0 * t.sum() + 13.0 * f.sum(),
        }
        gradients = lf9.routed_field_gradients(losses, params)
        self.assertEqual(float(gradients["potential"][0]), 1.0)
        self.assertEqual(float(gradients["temperature"][0]), 3.0)
        self.assertEqual(float(gradients["phase"][0]), 13.0)


class LF9ControlVolumeTests(unittest.TestCase):
    def test_two_point_gauss_is_exact_for_constant_linear_and_quadratic(self) -> None:
        nodes, weights = lf9.gauss_legendre_2(-2.0, 3.0, dtype=torch.float64, device=torch.device("cpu"))
        self.assertAlmostEqual(float(torch.sum(weights)), 5.0, places=14)
        self.assertAlmostEqual(float(torch.sum(weights * nodes)), 2.5, places=14)
        self.assertAlmostEqual(float(torch.sum(weights * nodes.square())), 35.0 / 3.0, places=13)

    def test_cv_residual_matches_strong_identity_for_time_and_diffusion_examples(self) -> None:
        bounds = torch.tensor([[0.0, 1.0, 0.0, 1.0, 0.2, 0.4]], dtype=torch.float64)
        linear = lf9.thermal_control_volume_residual(_AnalyticModel("linear_time"), bounds)
        quadratic = lf9.thermal_control_volume_residual(_AnalyticModel("quadratic_space"), bounds)
        self.assertTrue(torch.allclose(linear, torch.ones_like(linear), atol=1e-12, rtol=0.0))
        self.assertTrue(torch.allclose(quadratic, torch.full_like(quadratic, -4.0), atol=1e-12, rtol=0.0))


class LF9LedgerAndDecisionTests(unittest.TestCase):
    def test_materialized_training_and_blind_cell_time_supports_are_disjoint(self) -> None:
        x = np.linspace(-0.875, 0.875, 8)
        z = np.linspace(0.125, 0.875, 4)
        time = np.array([0.0, 0.175, 0.35, 0.8, 1.25, 1.425, 1.6, 2.05, 2.5])
        arrays, report = qualification.materialize_cv_arrays(
            cell_x=np.tile(x, z.size),
            cell_z=np.repeat(z, x.size),
            time=time,
            steps=8,
            patches_per_step=4,
            blind_per_window=1,
            seed=17,
        )
        self.assertEqual(arrays["training_bounds"].shape, (8, 4, 6))
        self.assertEqual(arrays["one_cell_blind_bounds"].shape, (4, 6))
        self.assertEqual(arrays["two_by_two_blind_bounds"].shape, (4, 6))
        self.assertTrue(all(report["disjoint_checks"].values()))

    def test_training_patches_follow_the_accepted_step_causal_window_schedule(self) -> None:
        x = np.linspace(-0.875, 0.875, 8)
        z = np.linspace(0.125, 0.875, 4)
        time = np.arange(0.0, 2.5000001, 0.05)
        arrays, report = qualification.materialize_cv_arrays(
            cell_x=np.tile(x, z.size), cell_z=np.repeat(z, x.size), time=time,
            steps=551, patches_per_step=4, blind_per_window=1, seed=17,
        )
        midpoint = arrays["training_bounds"][:, :, 4:6].mean(axis=2)
        self.assertTrue(np.all(midpoint[0] <= 0.35))
        self.assertEqual(sum(midpoint[150] <= 0.35), 2)
        self.assertEqual(sum((midpoint[150] > 0.35) & (midpoint[150] < 1.25)), 2)
        self.assertEqual(sum(midpoint[350] <= 0.35), 2)
        self.assertEqual(sum((midpoint[350] > 0.35) & (midpoint[350] < 1.25)), 1)
        self.assertEqual(sum((midpoint[350] >= 1.25) & (midpoint[350] <= 1.60)), 1)
        self.assertEqual(len(set(np.round(midpoint[550], 12))), 4)
        self.assertTrue(report["ordered_remainder"])

    def test_filter_gate_screen_and_mechanism_are_strictly_conjunctive(self) -> None:
        passed = lf9.competence_gate(_audit(), physics_previous=10.0, physics_new=9.0)
        failed = lf9.competence_gate(_audit(temperature_ratio=1.051), physics_previous=10.0, physics_new=9.0)
        self.assertTrue(passed["passed"])
        self.assertIn("relative_temperature", failed["failed_checks"])
        endpoint = {
            "numerical_valid": True,
            "accepted_updates": 200,
            "safety_gate": passed,
            "own_ratio": 0.94,
            "cv1_ratio": 0.94,
            "cv4_ratio": 0.94,
        }
        self.assertTrue(lf9.screen_go(endpoint))
        arms = {lf9.ER_S: endpoint, lf9.ER_CV: {**endpoint, "cv4_ratio": 0.84}}
        decision = lf9.adjudicate_screens(arms)
        self.assertEqual(decision["mechanism_outcome"], "THERMAL_CONTROL_VOLUME_ADDS_MEANINGFUL_CONSERVATION_GAIN")
        self.assertEqual(decision["selected_arm"], lf9.ER_CV)

    def test_cpu_artifact_schema_is_zero_update_and_gpu_authorizing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cpu.json"
            path.write_text(json.dumps({
                "schema_id": "phk-v23-lf9-cpu-qualification-v1",
                "task_id": lf9.TASK_ID,
                "gate_outcome": "LF9_CPU_QUALIFICATION_PASS",
                "scientific_optimizer_updates": 0,
                "gpu_execution_authorized_by_cpu_gate": True,
                "checks": {"a": True},
                "cv_ledger": {"file_sha256": "A", "manifest_sha256": "B", "semantic_sha256": "C"},
            }), encoding="utf-8")
            payload = lf9.read_cpu_qualification(path)
            self.assertTrue(payload["gpu_execution_authorized_by_cpu_gate"])


if __name__ == "__main__":
    unittest.main()
