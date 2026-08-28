from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy as np

import torch
from torch import nn

from pinn_pcm_sci.phk_benchmark import PhkControl
from pinn_pcm_sci.phk_v22r_evaluator import (
    METHOD_CONTRACT,
    PROGRAM_CONTRACT,
    load_reference,
    validate_candidate_freeze,
)
from pinn_pcm_sci.phk_v22r_decision import adjudicate_nominal
from pinn_pcm_sci.phk_v22r_pinn import (
    CollocationMixture,
    FrequencyBand,
    PhkCollocationSampler,
    PhkV22RArm,
    PhkV22RModel,
    boundary_residuals,
    evaluate_fields,
    initial_residuals,
    interior_residuals,
    normalized_residual_loss,
)
from pinn_pcm_sci.phk_v22r_prediction import (
    read_prediction_carrier,
    write_prediction_carrier,
)
from pinn_pcm_sci.phk_v22r_training import (
    PhkTrainingConfig,
    load_case_physics,
    train,
)


class _AnalyticFields(nn.Module):
    def forward(self, coordinates: torch.Tensor) -> torch.Tensor:
        x = coordinates[:, 0:1]
        z = coordinates[:, 1:2]
        t = coordinates[:, 2:3]
        return torch.cat(
            (
                x**3 + z**2 + t,
                x**2 + z**3 + t**2,
                x**4 + z**4 + t**3,
            ),
            dim=1,
        )


class PhkV22RPinnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.physics, _, _ = load_case_physics(PhkControl.FULL)

    def _model(self, arm: PhkV22RArm) -> PhkV22RModel:
        torch.manual_seed(17)
        return PhkV22RModel(
            physics=self.physics,
            arm=arm,
            hidden_width=8,
            hidden_layers=2,
            frequency_band=FrequencyBand.conservative(),
        ).double()

    def test_diagonal_derivatives_are_physical_coordinate_derivatives(self) -> None:
        coordinates = torch.tensor(
            [[0.2, 0.3, 0.4], [-0.4, 0.6, 1.2]], dtype=torch.float64
        )
        bundle = evaluate_fields(_AnalyticFields(), coordinates)  # type: ignore[arg-type]
        x = bundle.coordinates[:, 0:1]
        z = bundle.coordinates[:, 1:2]
        self.assertTrue(
            torch.allclose(bundle.diagonal_second["potential"]["xx"], 6.0 * x)
        )
        self.assertTrue(
            torch.allclose(
                bundle.diagonal_second["potential"]["zz"],
                torch.full_like(z, 2.0),
            )
        )
        self.assertTrue(
            torch.allclose(
                bundle.diagonal_second["temperature"]["zz"], 6.0 * z
            )
        )
        self.assertTrue(
            torch.allclose(bundle.diagonal_second["phase"]["xx"], 12.0 * x.square())
        )

    def test_all_primary_arms_have_truthful_representation_and_sampler_identity(self) -> None:
        expected = {
            PhkV22RArm.STRONG_RAW: (False, False),
            PhkV22RArm.MF_ONLY: (True, False),
            PhkV22RArm.SAMPLER_ONLY: (False, True),
            PhkV22RArm.MF_PLUS_SAMPLER: (True, True),
        }
        for arm, flags in expected.items():
            manifest = self._model(arm).architecture_manifest()
            self.assertEqual(
                (manifest["field_selective"], manifest["physics_sampler"]), flags
            )

    def test_hard_initial_conditions_and_phase_range_hold(self) -> None:
        model = self._model(PhkV22RArm.MF_PLUS_SAMPLER)
        space = torch.tensor(
            [[-0.8, 0.1], [0.0, 0.12], [0.7, 0.8]], dtype=torch.float64
        )
        residuals = initial_residuals(model, space)
        for residual in residuals.values():
            self.assertLessEqual(float(torch.max(torch.abs(residual))), 1.0e-14)
        coordinates = torch.tensor(
            [[0.0, 0.2, 0.3], [0.5, 0.9, 2.0]], dtype=torch.float64
        )
        phase = model(coordinates)[:, 2]
        self.assertTrue(bool(torch.all((phase > 0.0) & (phase < 1.0))))
        event_time = 0.2378
        event_z = 0.12
        temperature_envelope = model.temperature_scale * (
            1.0
            - torch.exp(torch.tensor(-((event_time / model.startup_time) ** 2)))
        ) * (1.0 - event_z)
        self.assertGreater(
            float(temperature_envelope), self.physics.theta_transition
        )

    def test_one_backward_step_is_finite_for_each_arm(self) -> None:
        coordinates = torch.tensor(
            [[-0.4, 0.2, 0.1], [0.3, 0.5, 0.8], [0.0, 0.7, 1.4]],
            dtype=torch.float64,
        )
        for arm in PhkV22RArm:
            model = self._model(arm)
            residuals = interior_residuals(model, coordinates)
            loss = normalized_residual_loss(residuals)
            self.assertTrue(bool(torch.isfinite(loss)))
            loss.backward()
            gradients = [
                parameter.grad
                for parameter in model.parameters()
                if parameter.requires_grad and parameter.grad is not None
            ]
            self.assertTrue(gradients)
            self.assertTrue(all(bool(torch.isfinite(value).all()) for value in gradients))

    def test_strict_routing_gate_remains_in_coordinate_and_parameter_graph(self) -> None:
        model = self._model(PhkV22RArm.STRICT_PHA_PROBE)
        coordinates = torch.tensor(
            [[0.1, 0.2, 0.2], [0.3, 0.4, 1.4]],
            dtype=torch.float64,
            requires_grad=True,
        )
        diagnostics = model.diagnostics(coordinates)
        self.assertIsNotNone(diagnostics.gate)
        assert diagnostics.gate is not None
        coordinate_gradient = torch.autograd.grad(
            diagnostics.gate.sum(), coordinates, create_graph=True
        )[0]
        self.assertGreater(float(torch.max(torch.abs(coordinate_gradient))), 0.0)
        loss = normalized_residual_loss(interior_residuals(model, coordinates))
        loss.backward()
        assert model.high_phase is not None
        self.assertTrue(
            any(
                parameter.grad is not None
                and float(torch.max(torch.abs(parameter.grad))) > 0.0
                for parameter in model.high_phase.parameters()
            )
        )

    def test_sampler_retains_uniform_floor_and_equal_causal_replay(self) -> None:
        mixture = CollocationMixture(candidate_pool_multiplier=1)
        sampler = PhkCollocationSampler(physics=self.physics, mixture=mixture, seed=17)
        points = sampler.interior_uniform(
            40,
            active_windows=4,
            dtype=torch.float64,
            device=torch.device("cpu"),
        )
        counts = [
            int(torch.count_nonzero((points[:, 2] >= start) & (points[:, 2] < end)))
            for start, end in sampler.windows
        ]
        self.assertEqual(counts, [10, 10, 10, 10])
        selected = sampler.select_interior(
            self._model(PhkV22RArm.SAMPLER_ONLY),
            count=8,
            active_windows=2,
            physics_aware=True,
            dtype=torch.float64,
            device=torch.device("cpu"),
        )
        self.assertEqual(selected.shape, (8, 3))
        self.assertTrue(bool(torch.isfinite(selected).all()))

    def test_boundary_contract_contains_every_field(self) -> None:
        model = self._model(PhkV22RArm.STRONG_RAW)
        sampler = PhkCollocationSampler(physics=self.physics, seed=17)
        batches = sampler.boundary(
            4,
            active_windows=4,
            dtype=torch.float64,
            device=torch.device("cpu"),
        )
        top = boundary_residuals(model, batches["top"], side="top")
        bottom = boundary_residuals(model, batches["bottom"], side="bottom")
        self.assertIn("bc_potential_top", top)
        self.assertIn("bc_temperature_top", top)
        self.assertIn("bc_phase_no_flux", top)
        self.assertIn("bc_temperature_robin", bottom)
        self.assertIn("bc_phase_no_flux", bottom)
        self.assertTrue(
            "bc_potential_heater" in bottom
            or "bc_electric_insulating_bottom" in bottom
        )

    def test_one_update_training_writes_reference_blind_manifest(self) -> None:
        config = PhkTrainingConfig(
            arm=PhkV22RArm.STRONG_RAW.value,
            updates=1,
            hidden_width=8,
            hidden_layers=2,
            interior_points=4,
            boundary_points=8,
            initial_points=4,
            refresh_updates=1,
            log_every=1,
            checkpoint_every=1,
        )
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory) / "run"
            outcome = train(config, run_directory=run)
            self.assertEqual(outcome.status, "COMPLETE")
            manifest = json.loads((run / "manifest-final.json").read_text())
            self.assertFalse(manifest["reference_fields_read"])
            self.assertFalse(manifest["training_labels_used"])
            self.assertTrue(outcome.checkpoint_path.is_file())

    def test_prediction_carrier_is_generated_from_checkpoint_without_reference(self) -> None:
        config = PhkTrainingConfig(
            arm=PhkV22RArm.STRONG_RAW.value,
            updates=1,
            hidden_width=8,
            hidden_layers=2,
            interior_points=4,
            boundary_points=8,
            initial_points=4,
            refresh_updates=1,
            log_every=1,
            checkpoint_every=1,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outcome = train(config, run_directory=root / "run")
            target = root / "prediction.npz"
            with mock.patch(
                "pinn_pcm_sci.phk_v22r_prediction._evaluation_axes",
                return_value=(
                    np.asarray([-0.5, 0.5], dtype=np.float64),
                    np.asarray([0.25, 0.75], dtype=np.float64),
                    np.asarray([0.1, 0.2], dtype=np.float64),
                ),
            ):
                write_prediction_carrier(
                    checkpoint_path=outcome.checkpoint_path,
                    output_path=target,
                    chunk_points=4,
                )
            metadata, arrays = read_prediction_carrier(target)
            self.assertFalse(metadata["reference_fields_read"])
            self.assertEqual(arrays["phase"].shape, (2, 4))
            self.assertTrue(np.isfinite(arrays["top_current"]).all())

    def test_stress_reference_fails_closed_before_candidate_freeze(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "candidate-freeze.json"
            with self.assertRaises(PermissionError):
                load_reference(
                    PhkControl.INTERFACE_WIDTH_0_025,
                    candidate_freeze_path=missing,
                )

    def test_candidate_freeze_schema_can_be_validated_without_opening_stress(self) -> None:
        def sha(path: Path) -> str:
            return hashlib.sha256(path.read_bytes()).hexdigest().upper()

        payload = {
            "schema_id": "phk-v22r-candidate-freeze-v1",
            "status": "FROZEN",
            "program_contract_sha256": sha(PROGRAM_CONTRACT),
            "method_contract_sha256": sha(METHOD_CONTRACT),
            "selected_candidate": {
                "arm": "MF_PLUS_SAMPLER",
                "training_config_sha256": "A" * 64,
                "seed": 17,
                "updates": 1500,
                "architecture": {},
                "training_config": {
                    "arm": "MF_PLUS_SAMPLER",
                    "case_control": "FULL",
                    "updates": 1500,
                    "seed": 17,
                },
                "decision_status": "SELECTED",
            },
            "stress_reference_seals": {
                PhkControl.INTERFACE_WIDTH_0_025.value: {
                    "carrier_sha256": "B" * 64
                },
                PhkControl.HEATER_WIDTH_0_50.value: {
                    "carrier_sha256": "C" * 64
                },
            },
            "strongest_component": "MF_ONLY",
            "equal_compute_raw_identity": {
                "arm": "STRONG_RAW",
                "hidden_width": 76,
                "hidden_layers": 4,
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate-freeze.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(validate_candidate_freeze(path)["status"], "FROZEN")

    def test_nominal_decision_requires_attributable_combined_gain(self) -> None:
        def report(
            arm: PhkV22RArm,
            primary: float,
            co_primary: float,
            *,
            passed: bool = True,
        ) -> dict[str, object]:
            return {
                "case_control": PhkControl.FULL.value,
                "architecture": {"arm": arm.value},
                "hard_guards": {"passed": passed},
                "metrics": {
                    "time_averaged_phase_region_symmetric_difference": primary,
                    "phase_roi_continuous_rms": co_primary,
                    "temperature_roi_nrmse_by_0_45": 0.04,
                    "terminal_current_trace_nrmse": 0.10,
                },
            }

        passing = {
            PhkV22RArm.STRONG_RAW.value: report(
                PhkV22RArm.STRONG_RAW, 0.30, 0.30
            ),
            PhkV22RArm.MF_ONLY.value: report(PhkV22RArm.MF_ONLY, 0.20, 0.20),
            PhkV22RArm.SAMPLER_ONLY.value: report(
                PhkV22RArm.SAMPLER_ONLY, 0.24, 0.24
            ),
            PhkV22RArm.MF_PLUS_SAMPLER.value: report(
                PhkV22RArm.MF_PLUS_SAMPLER, 0.18, 0.18
            ),
        }
        decision = adjudicate_nominal(passing)
        self.assertEqual(decision["status"], "SELECTED_PHYSICS_ONLY_MF_PLUS_SAMPLER")
        failing = dict(passing)
        failing[PhkV22RArm.MF_PLUS_SAMPLER.value] = report(
            PhkV22RArm.MF_PLUS_SAMPLER, 0.199, 0.199
        )
        decision = adjudicate_nominal(failing)
        self.assertEqual(decision["status"], "MVP_NO_GO_NO_ATTRIBUTABLE_GAIN")
        self.assertFalse(decision["stress_unseal_authorized"])


if __name__ == "__main__":
    unittest.main()
