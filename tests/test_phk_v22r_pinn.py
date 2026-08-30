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
    write_evaluation,
)
from pinn_pcm_sci.phk_v22r_decision import (
    adjudicate_nominal,
    freeze_selected_candidate,
    write_confirmation_plan,
)
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
from pinn_pcm_sci.phk_v22r_sprint import (
    PRIMARY_ARMS,
    run_matrix,
    validate_v11_execution_contract,
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
        for arm in PRIMARY_ARMS:
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

    def test_v11_contract_and_runner_expose_only_the_frozen_four_arm_nominal(self) -> None:
        program = json.loads(PROGRAM_CONTRACT.read_text(encoding="utf-8"))
        method = json.loads(METHOD_CONTRACT.read_text(encoding="utf-8"))
        expected = [arm.value for arm in PRIMARY_ARMS]
        self.assertEqual(program["schema_id"], "phk-v22r-program-contract-v1-1")
        self.assertEqual(method["schema_id"], "phk-v22r-method-contract-v1-1")
        self.assertEqual(program["nominal_matrix"]["arms_in_order"], expected)
        self.assertEqual(method["nominal_training"]["arms_in_order"], expected)
        self.assertEqual(program["nominal_matrix"]["updates"], 1000)
        self.assertEqual(method["nominal_training"]["checkpoint_policy"], "FINAL_ONLY")
        self.assertNotIn("a_to_b", program)
        self.assertNotIn("development_search", program.get("nominal_matrix", {}))
        self.assertNotIn("strict_pha_probe", method["development_decision"])
        self.assertEqual(
            validate_v11_execution_contract()["program_schema_id"],
            "phk-v22r-program-contract-v1-1",
        )
        with self.assertRaisesRegex(ValueError, "only mode=nominal"):
            run_matrix(
                mode="pilot",
                output_root=Path("unused"),
                device="cuda:0",
                hourly_price_cny=1.88,
                source_identity="TEST",
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

        role_templates = {
            "SELECTED_METHOD": {
                "arm": "MF_PLUS_SAMPLER",
                "training_config_template": {"seed": 17},
            },
            "STRONGEST_COMPARATOR": {
                "arm": "MF_ONLY",
                "training_config_template": {"seed": 17},
            },
            "PARAMETER_MATCHED_MEASURED_TIME_BUDGET_RAW_CONTROL": {
                "arm": "STRONG_RAW",
                "training_config_template": {"seed": 17},
            },
        }
        prediction_carriers = {
            control.value: {
                role: {
                    "sha256": character * 64,
                    "reference_fields_read": False,
                }
                for role, character in zip(
                    role_templates,
                    ("D", "E", "F"),
                    strict=True,
                )
            }
            for control in (
                PhkControl.INTERFACE_WIDTH_0_025,
                PhkControl.HEATER_WIDTH_0_50,
            )
        }
        payload = {
            "schema_id": "phk-v22r-candidate-freeze-v1-1",
            "status": "FROZEN_SIX_PREDICTION_IDENTITIES_VERIFIED",
            "stress_reference_access_authorized": True,
            "program_contract_sha256": sha(PROGRAM_CONTRACT),
            "method_contract_sha256": sha(METHOD_CONTRACT),
            "roles": role_templates,
            "stress_reference_seals": {
                PhkControl.INTERFACE_WIDTH_0_025.value: {
                    "carrier_sha256": "B" * 64
                },
                PhkControl.HEATER_WIDTH_0_50.value: {
                    "carrier_sha256": "C" * 64
                },
            },
            "verified_prediction_count": 6,
            "prediction_carriers": prediction_carriers,
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate-freeze.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(
                validate_candidate_freeze(path)["status"],
                "FROZEN_SIX_PREDICTION_IDENTITIES_VERIFIED",
            )

    def test_confirmation_plan_freezes_measured_time_raw_update_budget(self) -> None:
        def sha(path: Path) -> str:
            return hashlib.sha256(path.read_bytes()).hexdigest().upper()

        def config(arm: str, *, width: int, updates: int) -> dict[str, object]:
            return {
                "arm": arm,
                "case_control": "FULL",
                "updates": updates,
                "seed": 17,
                "hidden_width": width,
                "hidden_layers": 4,
                "frequency_band": "BAND_A",
                "learning_rate": 1.0e-3,
                "gradient_clip_norm": 10.0,
                "interior_points": 512,
                "boundary_points": 128,
                "initial_points": 128,
                "candidate_pool_multiplier": 4,
                "refresh_updates": 250,
                "log_every": 25,
                "checkpoint_every": updates,
                "pde_weight": 1.0,
                "boundary_weight": 5.0,
                "initial_weight": 1.0,
                "dtype": "float64",
                "device": "cuda:0",
            }

        def manifest(
            training_config: dict[str, object],
            *,
            wall_seconds: float,
            seconds_per_update: float,
            parameter_count: int,
        ) -> dict[str, object]:
            return {
                "schema_id": "phk-v22r-training-run-manifest-v1-1",
                "status": "COMPLETE",
                "reference_fields_read": False,
                "training_labels_used": False,
                "initialization": "SCRATCH_START",
                "checkpoint_policy": "FINAL_ONLY",
                "program_contract_sha256": sha(PROGRAM_CONTRACT),
                "method_contract_sha256": sha(METHOD_CONTRACT),
                "training_config": training_config,
                "training_config_sha256": "A" * 64,
                "architecture": {
                    "arm": training_config["arm"],
                    "trainable_parameter_count": parameter_count,
                },
                "wall_seconds": wall_seconds,
                "seconds_per_update": seconds_per_update,
            }

        fake_seals = {
            PhkControl.INTERFACE_WIDTH_0_025.value: {"carrier_sha256": "B" * 64},
            PhkControl.HEATER_WIDTH_0_50.value: {"carrier_sha256": "C" * 64},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            decision_path = root / "decision.json"
            selected_path = root / "selected.json"
            comparator_path = root / "comparator.json"
            raw_path = root / "raw-timing.json"
            output = root / "confirmation-plan.json"
            decision_path.write_text(
                json.dumps(
                    {
                        "status": "SELECTED_PHYSICS_ONLY_MF_PLUS_SAMPLER",
                        "confirmation_training_authorized": True,
                        "stress_unseal_authorized": False,
                        "strongest_comparator": "MF_ONLY",
                    }
                ),
                encoding="utf-8",
            )
            selected_path.write_text(
                json.dumps(
                    manifest(
                        config("MF_PLUS_SAMPLER", width=64, updates=1000),
                        wall_seconds=100.0,
                        seconds_per_update=0.1,
                        parameter_count=54915,
                    )
                ),
                encoding="utf-8",
            )
            comparator_path.write_text(
                json.dumps(
                    manifest(
                        config("MF_ONLY", width=64, updates=1000),
                        wall_seconds=90.0,
                        seconds_per_update=0.09,
                        parameter_count=54915,
                    )
                ),
                encoding="utf-8",
            )
            raw_path.write_text(
                json.dumps(
                    manifest(
                        config("STRONG_RAW", width=76, updates=100),
                        wall_seconds=20.0,
                        seconds_per_update=0.2,
                        parameter_count=55635,
                    )
                ),
                encoding="utf-8",
            )
            with mock.patch(
                "pinn_pcm_sci.phk_v22r_decision._stress_seals",
                return_value=fake_seals,
            ):
                plan = write_confirmation_plan(
                    output,
                    nominal_decision_path=decision_path,
                    selected_training_manifest_path=selected_path,
                    comparator_training_manifest_path=comparator_path,
                    raw_timing_manifest_path=raw_path,
                )
        raw_role = plan["roles"][
            "PARAMETER_MATCHED_MEASURED_TIME_BUDGET_RAW_CONTROL"
        ]
        self.assertEqual(raw_role["derived_updates"], 500)
        self.assertEqual(raw_role["training_config_template"]["updates"], 500)
        self.assertFalse(plan["stress_reference_access_authorized"])

    def test_final_freeze_requires_exactly_six_verified_prediction_identities(self) -> None:
        def sha(path: Path) -> str:
            return hashlib.sha256(path.read_bytes()).hexdigest().upper()

        fake_seals = {
            PhkControl.INTERFACE_WIDTH_0_025.value: {
                "byte_seal_path": "narrow/byte-seal.json",
                "byte_seal_sha256": "A" * 64,
                "carrier_sha256": "B" * 64,
                "carrier_size_bytes": 1,
            },
            PhkControl.HEATER_WIDTH_0_50.value: {
                "byte_seal_path": "wide/byte-seal.json",
                "byte_seal_sha256": "C" * 64,
                "carrier_sha256": "D" * 64,
                "carrier_size_bytes": 1,
            },
        }
        roles = {
            "SELECTED_METHOD": ("MF_PLUS_SAMPLER", 64, 1000, 54915),
            "STRONGEST_COMPARATOR": ("MF_ONLY", 64, 1000, 54915),
            "PARAMETER_MATCHED_MEASURED_TIME_BUDGET_RAW_CONTROL": (
                "STRONG_RAW",
                76,
                500,
                55635,
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan_path = root / "confirmation-plan.json"
            output = root / "candidate-freeze.json"
            role_payload = {}
            for role, (arm, width, updates, parameter_count) in roles.items():
                role_payload[role] = {
                    "arm": arm,
                    "trainable_parameter_count": parameter_count,
                    "training_config_template": {
                        "arm": arm,
                        "case_control": "<STRESS_CASE>",
                        "updates": updates,
                        "seed": 17,
                        "hidden_width": width,
                    },
                }
            plan_path.write_text(
                json.dumps(
                    {
                        "schema_id": "phk-v22r-confirmation-plan-v1-1",
                        "status": "IDENTITIES_FROZEN_PREDICTIONS_PENDING",
                        "stress_reference_access_authorized": False,
                        "program_contract_sha256": sha(PROGRAM_CONTRACT),
                        "method_contract_sha256": sha(METHOD_CONTRACT),
                        "roles": role_payload,
                        "confirmation_cases": [
                            PhkControl.INTERFACE_WIDTH_0_025.value,
                            PhkControl.HEATER_WIDTH_0_50.value,
                        ],
                        "stress_reference_seals": fake_seals,
                    }
                ),
                encoding="utf-8",
            )
            prediction_paths = {}
            metadata_by_path = {}
            for control in (
                PhkControl.INTERFACE_WIDTH_0_025,
                PhkControl.HEATER_WIDTH_0_50,
            ):
                for role, (arm, width, updates, parameter_count) in roles.items():
                    path = root / f"{control.value}-{role}.npz"
                    path.write_bytes(f"{control.value}-{role}".encode())
                    prediction_paths[(control.value, role)] = path
                    training_config = dict(role_payload[role]["training_config_template"])
                    training_config["case_control"] = control.value
                    metadata_by_path[path] = {
                        "reference_fields_read": False,
                        "program_contract_sha256": sha(PROGRAM_CONTRACT),
                        "method_contract_sha256": sha(METHOD_CONTRACT),
                        "training_config": training_config,
                        "training_config_sha256": "E" * 64,
                        "checkpoint_sha256": "F" * 64,
                        "checkpoint_update": updates,
                        "architecture": {
                            "arm": arm,
                            "trainable_parameter_count": parameter_count,
                        },
                    }

            def read_fake(path: Path):
                return metadata_by_path[Path(path)], {}

            incomplete = dict(prediction_paths)
            incomplete.pop(next(iter(incomplete)))
            with self.assertRaisesRegex(ValueError, "exactly two cases by three roles"):
                freeze_selected_candidate(
                    output,
                    confirmation_plan_path=plan_path,
                    prediction_paths=incomplete,
                )
            with mock.patch(
                "pinn_pcm_sci.phk_v22r_decision._stress_seals",
                return_value=fake_seals,
            ), mock.patch(
                "pinn_pcm_sci.phk_v22r_decision.read_prediction_carrier",
                side_effect=read_fake,
            ):
                freeze = freeze_selected_candidate(
                    output,
                    confirmation_plan_path=plan_path,
                    prediction_paths=prediction_paths,
                )
        self.assertEqual(freeze["verified_prediction_count"], 6)
        self.assertTrue(freeze["stress_reference_access_authorized"])

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
        self.assertTrue(decision["confirmation_training_authorized"])
        self.assertFalse(decision["stress_unseal_authorized"])
        self.assertEqual(decision["strongest_comparator"], "MF_ONLY")
        failing = dict(passing)
        failing[PhkV22RArm.MF_PLUS_SAMPLER.value] = report(
            PhkV22RArm.MF_PLUS_SAMPLER, 0.199, 0.199
        )
        decision = adjudicate_nominal(failing)
        self.assertEqual(decision["status"], "MVP_NO_GO_NO_ATTRIBUTABLE_GAIN")
        self.assertFalse(decision["stress_unseal_authorized"])
        incompetent = {
            arm: report(PhkV22RArm(arm), 0.3, 0.3, passed=False)
            for arm in passing
        }
        decision = adjudicate_nominal(incompetent)
        self.assertEqual(decision["status"], "MVP_NO_GO_NO_BASIC_COMPETENCE")
        self.assertTrue(decision["terminal_no_rescue"])

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
                serialized_in_memory = json.loads(json.dumps(report))
                output = Path(directory) / "evaluation.json"
                write_evaluation(output, report)
                serialized = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(
            report["metrics"]["time_averaged_phase_region_symmetric_difference"],
            0.0,
        )
        self.assertEqual(serialized["metrics"], report["metrics"])
        self.assertEqual(serialized, serialized_in_memory)
        self.assertEqual(report["metrics"]["phase_roi_continuous_rms"], 0.0)
        self.assertTrue(report["hard_guards"]["passed"])
        self.assertTrue(report["training_trend"]["decreasing_pde_loss"])

    def test_evaluation_write_failure_does_not_leave_partial_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "evaluation.json"
            with self.assertRaises(TypeError):
                write_evaluation(output, {"unsupported": object()})
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
