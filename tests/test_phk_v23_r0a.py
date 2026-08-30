from __future__ import annotations

import inspect
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import torch

from pinn_pcm_sci.phk_v22r_pinn import (
    PhkV22RArm,
    PhkV22RModel,
    interior_diagnostic_terms,
    interior_residuals,
)
from pinn_pcm_sci.phk_v22r_training import load_case_physics
from pinn_pcm_sci.phk_v23_diagnostics import (
    ROOT,
    adjudicate_root_cause,
    assert_cpu_only_environment,
    assert_one_time_r0a_target,
    assert_state_unchanged,
    build_r0a_pool,
    gradient_matrix,
    load_contract_bundle,
    load_legacy_source_preserving_rng,
    reject_non_nominal_reference_access,
    snapshot_state,
    state_identity,
    write_json_exclusive_atomic,
)


class PhkV23R0ADiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contracts = load_contract_bundle()
        cls.physics, _, _ = load_case_physics("FULL")

    def _model(self) -> PhkV22RModel:
        torch.manual_seed(17)
        return PhkV22RModel(
            physics=self.physics,
            arm=PhkV22RArm.STRONG_RAW,
            hidden_width=8,
            hidden_layers=2,
        ).to(dtype=torch.float64, device=torch.device("cpu"))

    def test_contract_is_cpu_only_diagnostic_and_authorizes_no_next_stage(self) -> None:
        program = self.contracts["program"]
        method = self.contracts["method"]
        diagnostic = self.contracts["diagnostic"]
        self.assertTrue(program["authorization"]["r0a_cpu_diagnostic_authorized"])
        for name in (
            "optimizer_or_parameter_update_authorized",
            "gpu_or_cloud_authorized",
            "r0b_authorized",
            "r1_authorized",
            "r2_or_pjgr_authorized",
            "stress_reference_access_authorized",
        ):
            self.assertFalse(program["authorization"][name])
        self.assertEqual(program["execution_budget"]["gpu_hours"], 0.0)
        self.assertEqual(program["execution_budget"]["incremental_cloud_cost_cny"], 0.0)
        self.assertEqual(diagnostic["execution"]["device"], "CPU")
        self.assertEqual(diagnostic["execution"]["optimizer_steps"], 0)
        self.assertEqual(method["diagnostic_pool"]["scalar_points_total"], 2048)
        self.assertEqual(method["diagnostic_pool"]["gradient_points_total"], 512)
        self.assertEqual(method["legacy_training_identity"]["temperature_scale"], 2.5)
        self.assertEqual(method["legacy_training_identity"]["phase_latent_scale"], 8.0)
        self.assertEqual(method["legacy_training_identity"]["hard_ic_startup_time"], 0.35)
        self.assertTrue(program["completion_does_not_authorize_any_next_stage"])

    def test_windows_empty_cuda_mask_normalizes_without_gpu_access(self) -> None:
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertEqual(assert_cpu_only_environment(), "")
        with mock.patch.dict("os.environ", {"CUDA_VISIBLE_DEVICES": ""}, clear=True):
            self.assertEqual(assert_cpu_only_environment(), "")
        with mock.patch.dict(
            "os.environ", {"CUDA_VISIBLE_DEVICES": "0"}, clear=True
        ), self.assertRaises(PermissionError):
            assert_cpu_only_environment()

    def test_one_time_target_and_checkpoint_load_are_fail_closed_and_rng_neutral(self) -> None:
        with self.assertRaisesRegex(PermissionError, "frozen one-time artifact"):
            assert_one_time_r0a_target(ROOT / "other-r0a-output.json")
        ambient = torch.random.get_rng_state().clone()

        def fake_loader(checkpoint_path, contracts):
            torch.rand(5)
            return self._model(), object(), {"fixture": True}

        with mock.patch(
            "pinn_pcm_sci.phk_v23_diagnostics.assert_legacy_source_identity",
            side_effect=fake_loader,
        ):
            _, _, assertions = load_legacy_source_preserving_rng(
                ROOT / "fixture.pt", self.contracts
            )
        self.assertEqual(assertions, {"fixture": True})
        self.assertTrue(torch.equal(torch.random.get_rng_state(), ambient))

    def test_frozen_sobol_pool_and_first_128_per_window_subset(self) -> None:
        model = self._model()
        ambient = torch.random.get_rng_state().clone()
        pool, subset, indices, boundary = build_r0a_pool(model, self.contracts)
        self.assertEqual(pool.shape, (2048, 3))
        self.assertEqual(subset.shape, (512, 3))
        expected = torch.cat(
            [torch.arange(start, start + 128) for start in (0, 512, 1024, 1536)]
        )
        self.assertTrue(torch.equal(indices, expected))
        self.assertEqual(boundary["identity"]["window_counts"], [512] * 4)
        self.assertEqual(boundary["identity"]["gradient_window_counts"], [128] * 4)
        self.assertEqual(
            boundary["identity"]["pool_sha256_float64_bytes"],
            "4AF7927C2C577EFA2AFABC26C3A31EE139D2D9C572C2C3F22EA51A51021B2F8F",
        )
        self.assertEqual(
            boundary["identity"]["gradient_indices_sha256_int64_bytes"],
            "28A31A9BEA9F98FA43AB596EB1F56FEB72A2D3F46E5AB18E7154882D66DF84F5",
        )
        self.assertEqual(
            boundary["identity"]["gradient_subset_sha256_float64_bytes"],
            "F3E092406B41074F1CCCD1515686788CC56C20394AB59082CF58B9FD4B99335E",
        )
        self.assertTrue(torch.equal(torch.random.get_rng_state(), ambient))

    def test_read_only_observer_matches_legacy_transforms_and_residuals(self) -> None:
        model = self._model()
        coordinates = torch.tensor(
            [[-0.25, 0.20, 0.10], [0.05, 0.45, 0.80], [0.30, 0.70, 1.80]],
            dtype=torch.float64,
        )
        observed = model.read_only_output_diagnostics(coordinates)
        self.assertTrue(torch.equal(observed.output.fields, model(coordinates)))
        normalized = model.physics.normalize(coordinates)
        latent, _, _, _ = model._latent_fields(normalized)
        startup = 1.0 - torch.exp(-coordinates[:, 2:3] / 0.35)
        z_fraction = coordinates[:, 1:2]
        initial = model.physics.initial_phase(coordinates).clamp(1.0e-8, 1.0 - 1.0e-8)
        legacy = torch.cat(
            (
                model.physics.waveform(coordinates[:, 2:3])
                * torch.sigmoid(latent["potential"]),
                2.5
                * startup
                * (1.0 - z_fraction)
                * torch.sigmoid(latent["temperature"]),
                torch.sigmoid(
                    torch.logit(initial) + 8.0 * startup * latent["phase"]
                ),
            ),
            dim=1,
        )
        self.assertTrue(torch.equal(observed.output.fields, legacy))
        self.assertTrue(
            torch.equal(
                observed.analytic_output_jacobians["phase"],
                8.0
                * startup
                * observed.output.fields[:, 2:3]
                * (1.0 - observed.output.fields[:, 2:3]),
            )
        )
        for tensor in (
            *observed.latents.values(),
            *observed.analytic_output_jacobians.values(),
        ):
            self.assertTrue(bool(torch.isfinite(tensor).all()))
        legacy_residuals = interior_residuals(model, coordinates)
        terms = interior_diagnostic_terms(model, coordinates)
        for old_name, new_name in (
            ("electric", "electric_residual"),
            ("thermal", "thermal_residual"),
            ("phase", "phase_residual"),
            ("joule_density", "joule_density"),
            ("phase_indicator", "phase_indicator"),
        ):
            self.assertTrue(torch.equal(legacy_residuals[old_name], terms[new_name]))

    def test_gradient_probe_uses_no_optimizer_and_leaves_state_and_grads_unchanged(self) -> None:
        model = self._model()
        state = snapshot_state(model)
        identity = state_identity(model)
        _, subset, _, boundary = build_r0a_pool(model, self.contracts)
        with mock.patch.object(
            torch.optim.Optimizer,
            "step",
            side_effect=AssertionError("optimizer step is forbidden in R0A"),
        ):
            result = gradient_matrix(
                model,
                subset,
                boundary["batches"],
                self.contracts,
            )
        self.assertEqual(len(result["gradient_norms"]), 6)
        for row in result["gradient_norms"].values():
            self.assertEqual(set(row), {"potential", "temperature", "phase"})
        self.assertTrue(all(parameter.grad is None for parameter in model.parameters()))
        self.assertEqual(assert_state_unchanged(model, state, identity), identity)

    def test_prediction_core_has_no_reference_argument_and_stress_fails_before_open(self) -> None:
        for callable_object in (
            PhkV22RModel.forward,
            interior_residuals,
            interior_diagnostic_terms,
            build_r0a_pool,
            gradient_matrix,
        ):
            names = set(inspect.signature(callable_object).parameters)
            self.assertTrue(names.isdisjoint({"reference", "label", "oracle"}))
        stress = ROOT / "outputs" / "sealed" / "phk_v22r" / "narrow_interface_extra_fine" / "reference.npz"
        with self.assertRaisesRegex(PermissionError, "only the frozen nominal"):
            reject_non_nominal_reference_access(stress)

    def test_atomic_artifact_write_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.json"
            write_json_exclusive_atomic(path, {"schema_id": "fixture", "value": 1})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["value"], 1)
            with self.assertRaises(FileExistsError):
                write_json_exclusive_atomic(path, {"schema_id": "fixture", "value": 2})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["value"], 1)

    def test_inconclusive_adjudication_recommends_exactly_first_switch_175(self) -> None:
        gradient = {
            "gradient_norms": {
                name: {"phase": 1.0}
                for name in (
                    "ELECTRIC_PDE",
                    "THERMAL_PDE",
                    "PHASE_PDE",
                    "ELECTRIC_BC",
                    "THERMAL_BC",
                    "PHASE_BC",
                )
            },
            "same_head_pairwise_cosines": {
                "phase": {"A__B": {"cosine": 0.0, "reason": None}}
            },
        }
        teacher = {
            "phase_teacher_substitutions": {
                "base_to_reference_temperature_residual_improvement_ratio": 1.0
            },
            "thermal_teacher_substitution": {
                "base_to_reference_constitutive_qj_residual_improvement_ratio": 1.0
            },
            "joule_power_trace_scale": {
                "reference": {"q95": 1.0},
                "strong_raw_prediction": {"q95": 1.0},
            },
        }
        result = adjudicate_root_cause(gradient, teacher, self.contracts)
        self.assertEqual(result["status"], "R0A_INCONCLUSIVE")
        self.assertIsNone(result["primary"])
        self.assertEqual(result["next_recommendation"], "R0B_FIRST_SWITCH_175")

    def test_versioned_r0a_artifact_binds_state_reference_and_refusals(self) -> None:
        path = (
            ROOT
            / "docs"
            / "experiment"
            / "artifacts"
            / "20260830T-phk-v23-r0a-cpu-001.json"
        )
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_id"], "phk-v23-r0a-diagnostic-artifact-v1")
        self.assertEqual(payload["status"], "R0A_INCONCLUSIVE")
        self.assertEqual(payload["execution"]["device"], "CPU")
        self.assertFalse(payload["execution"]["gpu_used"])
        self.assertEqual(payload["execution"]["optimizer_steps"], 0)
        self.assertTrue(payload["state_identity"]["all_state_tensors_equal"])
        self.assertEqual(
            payload["state_identity"]["before"]["combined_state_sha256"],
            payload["state_identity"]["after"]["combined_state_sha256"],
        )
        self.assertEqual(
            payload["execution"]["reference_access_role"],
            "NOMINAL_LOCAL_DIAGNOSTIC_ONLY",
        )
        self.assertFalse(payload["execution"]["stress_fields_read"])
        self.assertFalse(payload["state_identity"]["entry_to_exit_torch_rng_unchanged"])
        self.assertTrue(
            payload["state_identity"][
                "post_checkpoint_load_to_exit_torch_rng_unchanged"
            ]
        )
        self.assertFalse(payload["refusals"]["r0b_executed"])
        self.assertEqual(
            hashlib.sha256(path.read_bytes()).hexdigest().upper(),
            "5B767A6E2FB1C64C6EE0FE5B5552DD3546C586944B55DDADF07D4B0277F31843",
        )


if __name__ == "__main__":
    unittest.main()
