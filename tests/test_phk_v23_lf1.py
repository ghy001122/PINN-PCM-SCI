from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path
import tempfile
import unittest

import numpy as np
import torch

from pinn_pcm_sci.phk_v22r_pinn import (
    POTENTIAL_TRANSFORM_EXACT_TOP_RANGE_PRESERVING,
    range_preserving_exact_top_fraction,
)
from pinn_pcm_sci.phk_v22r_training import load_case_physics
from pinn_pcm_sci.phk_v22r_prediction import _load_model
from pinn_pcm_sci.phk_v23_lf1 import (
    ARM_A,
    ARM_B,
    ARM_C,
    DISTILLATION_COUNTS,
    MediumEventBatchStream,
    MediumEventDataset,
    REPLAY_COUNTS,
    build_range_preserving_model,
    build_training_config,
    event_distillation_loss,
    contract_identity,
    load_contracts,
    _write_checkpoint,
    LF0PhysicsBatchStream,
    _physics_objective,
)


def _synthetic_result(physics):
    time = np.asarray(
        [0.0, 0.2, 0.35, 0.4, 0.8, 1.25, 1.4, 1.6, 1.7, 2.0, 2.5],
        dtype=np.float64,
    )
    x = np.asarray([-0.25, 0.25], dtype=np.float64)
    z = np.asarray([0.2, 0.5], dtype=np.float64)
    phase_line = np.asarray(
        [0.03, 0.40, 0.80, 0.70, 0.10, 0.03, 0.40, 0.80, 0.70, 0.10, 0.03],
        dtype=np.float64,
    )
    shape = (time.size, z.size, x.size)
    phase = np.broadcast_to(phase_line[:, None, None], shape).copy()
    temperature = 0.2 + 0.4 * phase
    waveform = physics.waveform(torch.as_tensor(time).reshape(-1, 1)).numpy()
    zeta = (z - physics.z_min) / (physics.z_max - physics.z_min)
    potential = np.broadcast_to(
        waveform[:, None, :] * (0.25 + 0.75 * zeta[None, :, None]), shape
    ).copy()
    return SimpleNamespace(
        time=time,
        grid=SimpleNamespace(x_centers=x, z_centers=z, nx=x.size, nz=z.size),
        potential=potential.reshape(-1),
        temperature=temperature.reshape(-1),
        phase=phase.reshape(-1),
    )


class RangePreservingTransformTests(unittest.TestCase):
    def test_exact_range_and_derivatives(self) -> None:
        h = torch.tensor(
            [[-1000.0], [-100.0], [-10.0], [0.0], [10.0], [100.0], [1000.0]],
            dtype=torch.float64,
            requires_grad=True,
        )
        zeta = torch.tensor(
            [[0.0], [0.2], [0.5], [0.9], [1.0], [0.3], [1.0]],
            dtype=torch.float64,
            requires_grad=True,
        )
        fraction = range_preserving_exact_top_fraction(h, zeta)
        self.assertTrue(bool(torch.isfinite(fraction).all()))
        self.assertTrue(bool(torch.all((fraction >= 0.0) & (fraction <= 1.0))))
        self.assertEqual(float(fraction[4]), 1.0)
        self.assertEqual(float(fraction[6]), 1.0)
        derivative_h = torch.autograd.grad(
            fraction, h, torch.ones_like(fraction), retain_graph=True
        )[0]
        self.assertTrue(
            torch.allclose(derivative_h, fraction * (1.0 - fraction), atol=1e-12)
        )

        moderate = torch.tensor([[-10.0], [0.0], [10.0]], dtype=torch.float64)
        top = torch.ones_like(moderate, requires_grad=True)
        top_fraction = range_preserving_exact_top_fraction(moderate, top)
        derivative_zeta = torch.autograd.grad(
            top_fraction, top, torch.ones_like(top_fraction)
        )[0]
        self.assertTrue(
            torch.allclose(derivative_zeta, torch.exp(-moderate), rtol=1e-12)
        )

    def test_model_materializes_exact_top_and_zero_waveform(self) -> None:
        physics, _, _ = load_case_physics("FULL")
        torch.manual_seed(17)
        config = build_training_config(ARM_A, "cpu")
        model = build_range_preserving_model(physics=physics, config=config).to(
            dtype=torch.float64
        )
        top = torch.tensor(
            [[physics.x_min, physics.z_max, 0.20], [physics.x_max, physics.z_max, 1.40]],
            dtype=torch.float64,
        )
        prediction = model(top)
        waveform = physics.waveform(top[:, 2:3])
        self.assertTrue(torch.equal(prediction[:, 0:1], waveform))
        zero = torch.tensor(
            [[0.0, 0.5 * (physics.z_min + physics.z_max), physics.time_start]],
            dtype=torch.float64,
        )
        self.assertEqual(float(model(zero)[0, 0]), 0.0)
        self.assertEqual(
            model.architecture_manifest()["potential_output_transform"],
            POTENTIAL_TRANSFORM_EXACT_TOP_RANGE_PRESERVING,
        )

    def test_range_preserving_model_has_finite_strong_form_backward(self) -> None:
        physics, _, _ = load_case_physics("FULL")
        config = build_training_config(ARM_A, "cpu")
        torch.manual_seed(17)
        model = build_range_preserving_model(physics=physics, config=config).to(
            dtype=torch.float64
        )
        stream = LF0PhysicsBatchStream(
            physics=physics,
            interior_points=16,
            boundary_points=16,
            initial_points=16,
            refresh_updates=250,
            seed=17,
        )
        batch = stream.draw(
            model, 1, dtype=torch.float64, device=torch.device("cpu")
        )
        loss, _ = _physics_objective(model, batch, config)
        self.assertTrue(bool(torch.isfinite(loss)))
        loss.backward()
        self.assertTrue(
            all(
                parameter.grad is None or bool(torch.isfinite(parameter.grad).all())
                for parameter in model.parameters()
            )
        )


class EventStreamTests(unittest.TestCase):
    def setUp(self) -> None:
        self.physics, _, _ = load_case_physics("FULL")

    def _dataset(self) -> MediumEventDataset:
        return MediumEventDataset(_synthetic_result(self.physics), physics=self.physics)

    def test_required_pools_are_nonempty_and_batches_match_contract(self) -> None:
        dataset = self._dataset()
        self.assertTrue(all(count > 0 for count in dataset.pool_counts.values()))
        distillation = MediumEventBatchStream(dataset, role="DISTILLATION").draw(1)
        self.assertEqual(distillation.coordinates.shape, (1024, 3))
        self.assertEqual(
            sum(
                count
                for name, count in distillation.category_counts.items()
                if name != "background_original_eight_strata"
            ),
            sum(DISTILLATION_COUNTS),
        )
        replay = MediumEventBatchStream(self._dataset(), role="REPLAY").draw(1)
        self.assertEqual(replay.coordinates.shape, (512, 3))
        self.assertEqual(sum(replay.category_counts.values()), sum(REPLAY_COUNTS))

    def test_fast_forward_reproduces_continuation_batch(self) -> None:
        direct = MediumEventBatchStream(self._dataset(), role="DISTILLATION")
        direct.draw(1)
        direct.draw(2)
        expected = direct.draw(3)
        continued = MediumEventBatchStream(self._dataset(), role="DISTILLATION")
        continued.fast_forward(2)
        actual = continued.draw(3)
        self.assertEqual(actual.batch_sha256, expected.batch_sha256)
        self.assertTrue(torch.equal(actual.coordinates, expected.coordinates))
        self.assertTrue(torch.equal(actual.targets, expected.targets))

    def test_event_loss_is_finite_and_topology_is_present(self) -> None:
        dataset = self._dataset()
        batch = MediumEventBatchStream(dataset, role="DISTILLATION").draw(1)
        torch.manual_seed(17)
        model = build_range_preserving_model(
            physics=self.physics, config=build_training_config(ARM_B, "cpu")
        ).to(dtype=torch.float64)
        total, components = event_distillation_loss(
            model, batch, physics=self.physics, device=torch.device("cpu")
        )
        self.assertTrue(bool(torch.isfinite(total)))
        self.assertGreater(components["topology"], 0.0)
        total.backward()
        self.assertTrue(
            all(
                parameter.grad is None or bool(torch.isfinite(parameter.grad).all())
                for parameter in model.parameters()
            )
        )


class ContractTests(unittest.TestCase):
    def test_contracts_freeze_run_order_and_budgets(self) -> None:
        contracts = load_contracts()
        self.assertEqual(
            contracts["program"]["run_limits"]["fixed_order"],
            [ARM_A, ARM_B, ARM_C],
        )
        self.assertEqual(
            contracts["method"]["runs"]["B"]["B1"]["replay_weight"], 0.1
        )
        self.assertFalse(
            contracts["program"]["authorization"]["stress_prediction_or_unseal"]
        )

    def test_lf1_checkpoint_is_prediction_loader_compatible(self) -> None:
        physics, program_sha, object_sha = load_case_physics("FULL")
        config = build_training_config(ARM_A, "cpu")
        model = build_range_preserving_model(physics=physics, config=config).to(
            dtype=torch.float64
        )
        optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = _write_checkpoint(
                path=Path(temporary) / "checkpoint.pt",
                model=model,
                optimizer=optimizer,
                config=config,
                global_step=1200,
                physics_program_sha256=program_sha,
                physics_object_sha256=object_sha,
                arm=ARM_A,
                stage="A_PURE_PHYSICS",
                source_identity="LF1-BUNDLE-" + "A" * 64,
                contracts=contract_identity(),
            )
            loaded, loaded_config, payload = _load_model(
                checkpoint, device=torch.device("cpu")
            )
        self.assertEqual(loaded_config, config)
        self.assertEqual(payload["lf1"]["task_id"], load_contracts()["program"]["phase_id"])
        self.assertEqual(
            loaded.architecture_manifest()["potential_output_transform"],
            POTENTIAL_TRANSFORM_EXACT_TOP_RANGE_PRESERVING,
        )


if __name__ == "__main__":
    unittest.main()
