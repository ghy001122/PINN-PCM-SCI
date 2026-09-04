from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import unittest

import numpy as np
import torch

from pinn_pcm_sci.phk_v22r_training import load_case_physics
from pinn_pcm_sci.phk_v23_lf0 import LF0PhysicsBatchStream
from pinn_pcm_sci.phk_v23_lf2 import (
    CATEGORY_NAMES,
    CATEGORY_QUOTAS,
    M0_STAGE,
    M1_STAGE,
    MeasureBatch,
    MeasureCalibratedBatchStream,
    MediumMeasureDataset,
    augmented_lagrangian_inequality,
    augmented_lagrangian_sum,
    build_training_config,
    load_contracts,
    load_lf1_b0_initialization,
    m0_full_medium_gate,
    m1_full_medium_feasibility_gate,
    stage_stream_policy,
    trapezoid_node_weights,
    update_multipliers,
    weighted_measure_terms,
)


def _synthetic_result(physics):
    time = np.asarray(
        [
            0.0,
            0.1,
            0.2,
            0.3,
            0.35,
            0.4,
            0.8,
            1.25,
            1.35,
            1.45,
            1.55,
            1.6,
            1.7,
            2.0,
            2.5,
        ],
        dtype=np.float64,
    )
    cell_x = np.asarray([-0.25, 0.25, 0.8, -0.8], dtype=np.float64)
    cell_z = np.asarray([0.2, 0.5, 0.8, 0.8], dtype=np.float64)
    volumes = np.asarray([1.0, 2.0, 1.5, 0.5], dtype=np.float64)
    event_line = np.asarray(
        [
            0.03,
            0.20,
            0.60,
            0.90,
            0.80,
            0.70,
            0.10,
            0.03,
            0.20,
            0.60,
            0.90,
            0.80,
            0.70,
            0.10,
            0.03,
        ],
        dtype=np.float64,
    )
    phase = np.full((time.size, cell_x.size), 0.03, dtype=np.float64)
    phase[:, 0] = event_line
    temperature = 0.2 + 0.4 * phase
    waveform = (
        physics.waveform(torch.as_tensor(time, dtype=torch.float64).reshape(-1, 1))
        .detach()
        .numpy()
    )
    zeta = (cell_z - physics.z_min) / (physics.z_max - physics.z_min)
    potential = waveform * (0.25 + 0.75 * zeta[None, :])
    return SimpleNamespace(
        time=time,
        grid=SimpleNamespace(
            cell_x=cell_x, cell_z=cell_z, cell_volumes=volumes
        ),
        case=SimpleNamespace(period=1.25),
        potential=potential,
        temperature=temperature,
        phase=phase,
    )


def _audit(*, error: float = 0.4):
    cycle = {
        "hard_recall": 0.95,
        "hard_precision": 0.90,
        "hard_active_mass_ratio": 1.0,
        "event_time_absolute_error": 0.001,
        "predicted_event_time": 0.2,
    }
    return {
        "all_values_finite": True,
        "weighted_errors": {
            "potential": error,
            "temperature": error,
            "phase": error,
        },
        "topology_weighted_loss": error,
        "phase_maximum": 0.95,
        "potential_maximum_principle": {"passed": True},
        "event_metrics": {"cycle_1": dict(cycle), "cycle_2": dict(cycle)},
        "two_cycle_events": True,
    }


class _CoordinateModel(torch.nn.Module):
    def forward(self, coordinates: torch.Tensor) -> torch.Tensor:
        return coordinates[:, :3]


class LF2MeasureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.physics, _, _ = load_case_physics("FULL")
        self.dataset = MediumMeasureDataset(
            _synthetic_result(self.physics), physics=self.physics
        )

    def test_trapezoid_weights_are_normalized_and_endpoint_halved(self) -> None:
        weights = trapezoid_node_weights(np.asarray([0.0, 1.0, 3.0]))
        np.testing.assert_allclose(weights, [1.0 / 6.0, 0.5, 1.0 / 3.0])
        self.assertAlmostEqual(float(weights.sum()), 1.0)

    def test_fourteen_categories_are_mutually_exclusive_and_exhaustive(self) -> None:
        self.assertEqual(set(self.dataset.category_counts), set(CATEGORY_NAMES))
        self.assertTrue(all(self.dataset.category_counts[name] for name in CATEGORY_NAMES))
        self.assertEqual(
            sum(self.dataset.category_counts.values()), self.dataset.node_count
        )
        self.assertEqual(self.dataset.assignment.size, self.dataset.node_count)
        self.assertAlmostEqual(sum(self.dataset.category_masses.values()), 1.0)

    def test_sobol_stream_has_exact_quotas_call_order_and_role_separation(self) -> None:
        first = MeasureCalibratedBatchStream(self.dataset, role="M0")
        second = MeasureCalibratedBatchStream(self.dataset, role="M0")
        batch_a = first.draw(1)
        batch_b = second.draw(1)
        self.assertEqual(batch_a.coordinates.shape, (1024, 3))
        self.assertEqual(tuple(batch_a.category_counts.values()), CATEGORY_QUOTAS)
        self.assertEqual(batch_a.batch_sha256, batch_b.batch_sha256)
        self.assertTrue(torch.equal(batch_a.coordinates, batch_b.coordinates))
        independent = MeasureCalibratedBatchStream(
            self.dataset, role="M1_CONSTRAINT"
        ).draw(1)
        self.assertNotEqual(batch_a.batch_sha256, independent.batch_sha256)
        with self.assertRaises(ValueError):
            first.draw(3)

    def test_weighted_estimator_recovers_category_independent_loss(self) -> None:
        masses = {name: 1.0 / len(CATEGORY_NAMES) for name in CATEGORY_NAMES}
        coordinates = torch.tensor(
            [[1.0, 2.0, 0.25]] * len(CATEGORY_NAMES), dtype=torch.float64
        )
        batch = MeasureBatch(
            coordinates=coordinates,
            targets=torch.zeros_like(coordinates),
            category_counts={name: 1 for name in CATEGORY_NAMES},
            category_masses=masses,
            batch_sha256="A" * 64,
        )
        terms = weighted_measure_terms(
            _CoordinateModel(),
            batch,
            physics=self.physics,
            device=torch.device("cpu"),
        )
        expected = torch.tensor(
            [
                (1.0 / self.physics.waveform_amplitude) ** 2,
                (2.0 / self.physics.theta_transition) ** 2,
                (0.25 / 0.5) ** 2,
            ],
            dtype=torch.float64,
        )
        self.assertTrue(torch.allclose(terms["field_components"], expected))
        self.assertAlmostEqual(float(terms["field"]), float(torch.mean(expected)))

    def test_stage_policy_keeps_physics_rng_out_of_M0(self) -> None:
        self.assertEqual(
            stage_stream_policy(M0_STAGE),
            {
                "measure_stream_role": "M0",
                "physics_stream_constructed": False,
                "physics_stream_draws": 0,
            },
        )
        self.assertTrue(stage_stream_policy(M1_STAGE)["physics_stream_constructed"])


class LF2ConstraintAndIdentityTests(unittest.TestCase):
    def test_augmented_lagrangian_formula_and_multiplier_update(self) -> None:
        g = torch.tensor(0.4, dtype=torch.float64)
        value = augmented_lagrangian_inequality(g, 0.3, rho=2.0)
        expected = ((0.3 + 2.0 * 0.4) ** 2 - 0.3**2) / 4.0
        self.assertAlmostEqual(float(value), expected)
        total = augmented_lagrangian_sum({"g": g}, {"g": 0.3}, rho=2.0)
        self.assertAlmostEqual(float(total), expected)
        self.assertEqual(update_multipliers({"g": g}, {"g": 0.3}, rho=2.0), {"g": 1.1})

    def test_full_medium_gates_apply_frozen_ratios(self) -> None:
        contract = load_contracts()["decision"]
        baseline = _audit(error=1.0)
        m0 = _audit(error=0.4)
        self.assertTrue(m0_full_medium_gate(m0, baseline, contract=contract)["passed"])
        final = _audit(error=0.41)
        self.assertTrue(
            m1_full_medium_feasibility_gate(final, m0, contract=contract)["passed"]
        )
        final["weighted_errors"]["phase"] = 0.5
        result = m1_full_medium_feasibility_gate(final, m0, contract=contract)
        self.assertFalse(result["passed"])
        self.assertEqual(result["failure_outcome"], "LF2_FEASIBILITY_PRESERVATION_FAILED")

    def test_exact_parent_checkpoint_is_float64_and_physics_batch_identity_matches_LF1(self) -> None:
        contracts = load_contracts()
        physics, _, _ = load_case_physics("FULL")
        config = build_training_config("cpu")
        checkpoint = Path(contracts["data"]["initial_checkpoint"]["path"])
        model, payload = load_lf1_b0_initialization(
            checkpoint,
            physics=physics,
            config=config,
            contracts=contracts,
            device=torch.device("cpu"),
        )
        self.assertEqual(payload["lf1"]["stage"], "B0_EVENT_DATA_ONLY")
        self.assertEqual({parameter.dtype for parameter in model.parameters()}, {torch.float64})
        stream = LF0PhysicsBatchStream(
            physics=physics,
            interior_points=config.interior_points,
            boundary_points=config.boundary_points,
            initial_points=config.initial_points,
            refresh_updates=config.refresh_updates,
            seed=config.seed,
        )
        batch = stream.draw(
            model, 1, dtype=torch.float64, device=torch.device("cpu")
        )
        self.assertEqual(
            batch.batch_sha256,
            "5DEBCD1C96A8A2CD63E11DE5DD3D7C5077CDDAE4DC59F4527ABFABC6FDBC2433",
        )


class LF2ContractTests(unittest.TestCase):
    def test_contract_freezes_one_seed_one_trajectory_and_seven_unique_outcomes(self) -> None:
        contracts = load_contracts()
        limits = contracts["program"]["hard_limits"]
        self.assertEqual(limits["maximum_scientific_gpu_trajectories"], 1)
        self.assertEqual(limits["maximum_optimizer_updates"], 2400)
        self.assertEqual(contracts["method"]["common_identity"]["seed"], 17)
        mapping = contracts["decision"]["machine_outcomes_and_unique_next"]
        self.assertEqual(len(mapping), 7)
        self.assertEqual(len(set(mapping.values())), 7)
        self.assertFalse(
            contracts["program"]["authorization"]["stress_prediction_or_unseal"]
        )


if __name__ == "__main__":
    unittest.main()
