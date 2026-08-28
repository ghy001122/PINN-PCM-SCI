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

from pinn_pcm_sci.phk_benchmark import PhkControl, PhkGrid, PhkResolution
from pinn_pcm_sci.phk_v21_benchmark import PhkV21CaseSpec, PhkV21OracleResult
from pinn_pcm_sci.phk_v22r_evaluator import (
    METHOD_CONTRACT,
    PROGRAM_CONTRACT,
    load_reference,
    evaluate_prediction,
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
            1.0 - torch.exp(torch.tensor(-(event_time / model.startup_time)))
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
                "training_trend": {"decreasing_pde_loss": True},
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

    def test_evaluator_returns_zero_error_for_an_identical_small_fixture(self) -> None:
        grid = PhkGrid.build(
            nx=8, nz=4, x_min=-1.0, x_max=1.0, z_min=0.0, z_max=1.0
        )
        time = np.asarray(
            [0.0, 0.10, 0.25, 0.40, 1.00, 1.25, 1.35, 1.50, 1.70, 2.50],
            dtype=np.float64,
        )
        shape = (time.size, grid.cell_count)
        potential = np.zeros(shape, dtype=np.float64)
        temperature = np.zeros(shape, dtype=np.float64)
        phase = np.full(shape, 0.02, dtype=np.float64)
        active_cell = int(np.argmin(grid.cell_x**2 + grid.cell_z**2))
        phase[2, active_cell] = 0.8
        phase[7, active_cell] = 0.8
        temperature[2, active_cell] = 0.6
        temperature[7, active_cell] = 0.6
        from pinn_pcm_sci.phk_v22r_training import ROOT
        from pinn_pcm_sci.phk_v21_benchmark import load_phk_v21_physical

        physical_contract = load_phk_v21_physical(
            program_path=ROOT / "configs/phk_v21/program_contract.json",
            object_path=ROOT / "configs/phk_v21/object_numerical_contract.json",
            legacy_program_path=ROOT / "configs/phk_v2/program_contract.json",
            legacy_object_path=ROOT / "configs/phk_v2/object_numerical_contract.json",
        )
        case = PhkV21CaseSpec.nominal(physical_contract, control=PhkControl.FULL)
        zeros = np.zeros(time.size, dtype=np.float64)
        reference = PhkV21OracleResult(
            physical_contract_id=physical_contract.contract_id,
            program_contract_sha256=physical_contract.program.sha256,
            object_contract_sha256=physical_contract.object.sha256,
            case=case,
            resolution=PhkResolution.non_scientific_fixture(
                nx=8, nz=4, dt=0.1, time_end=2.5, save_every=1
            ),
            phase_algorithm="FIXTURE",
            grid=grid,
            time=time,
            potential=potential,
            temperature=temperature,
            phase=phase,
            top_current=zeros,
            bottom_current=zeros,
            joule_power=zeros,
            current_balance_history=zeros,
            thermal_residual_history=zeros,
            phase_residual_history=zeros,
            coupled_change_history=zeros,
            linear_residual_history=zeros,
            solver_statistics={},
            evidence_identity="NON_SCIENTIFIC_TEST_FIXTURE",
        )
        prediction = {
            "x": grid.x_centers.copy(),
            "z": grid.z_centers.copy(),
            "time": time.copy(),
            "potential": potential.copy(),
            "temperature": temperature.copy(),
            "phase": phase.copy(),
            "top_current": zeros.copy(),
            "joule_power": zeros.copy(),
        }
        metadata = {
            "training_config": {"case_control": PhkControl.FULL.value},
            "training_config_sha256": "A" * 64,
            "architecture": {"arm": PhkV22RArm.STRONG_RAW.value},
        }
        with tempfile.TemporaryDirectory() as directory:
            placeholder = Path(directory) / "prediction.npz"
            placeholder.write_bytes(b"fixture")
            (placeholder.parent / "training-log.jsonl").write_text(
                json.dumps({"pde_loss": 1.0})
                + "\n"
                + json.dumps({"pde_loss": 0.5})
                + "\n",
                encoding="utf-8",
            )
            with mock.patch(
                "pinn_pcm_sci.phk_v22r_evaluator.read_prediction_carrier",
                return_value=(metadata, prediction),
            ), mock.patch(
                "pinn_pcm_sci.phk_v22r_evaluator.load_reference",
                return_value=(reference, "B" * 64),
            ):
                report = evaluate_prediction(
                    prediction_path=placeholder,
                    control=PhkControl.FULL,
                )
        self.assertEqual(
            report["metrics"]["time_averaged_phase_region_symmetric_difference"],
            0.0,
        )
        self.assertEqual(report["metrics"]["phase_roi_continuous_rms"], 0.0)
        self.assertTrue(report["hard_guards"]["passed"])
        self.assertTrue(report["training_trend"]["decreasing_pde_loss"])


if __name__ == "__main__":
    unittest.main()
