from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import torch

from pinn_pcm_sci.phk_v22r_pinn import PhkCollocationSampler, PhkV22RArm, PhkV22RModel
from pinn_pcm_sci.phk_v22r_training import (
    PhkTrainingConfig,
    TrainingObservation,
    _active_windows,
    load_case_physics,
    train,
)
from pinn_pcm_sci.phk_v23_diagnostics import gradient_matrix_preserving_state
from pinn_pcm_sci.phk_v23_r0b import (
    R0BObserver,
    adjudicate_reference_blind,
    load_r0b_contracts,
    run_reference_blind_gpu_replay,
)


class _RecordingObserver:
    def __init__(self) -> None:
        self.events: list[tuple[str, int, int, bool]] = []

    def observe(self, observation: TrainingObservation) -> None:
        self.events.append(
            (
                observation.phase,
                observation.optimizer_step,
                observation.active_windows,
                observation.collocation_refreshed,
            )
        )


class PhkV23R0BTests(unittest.TestCase):
    @staticmethod
    def _tiny_config() -> PhkTrainingConfig:
        return PhkTrainingConfig(
            arm=PhkV22RArm.STRONG_RAW.value,
            updates=1000,
            hidden_width=4,
            hidden_layers=1,
            interior_points=4,
            boundary_points=4,
            initial_points=2,
            candidate_pool_multiplier=1,
            refresh_updates=250,
            log_every=25,
            checkpoint_every=1000,
            device="cpu",
        )

    @staticmethod
    def _model() -> PhkV22RModel:
        physics, _, _ = load_case_physics("FULL")
        torch.manual_seed(17)
        return PhkV22RModel(
            physics=physics,
            arm=PhkV22RArm.STRONG_RAW.value,
            hidden_width=4,
            hidden_layers=1,
        ).to(dtype=torch.float64)

    def test_contract_freezes_single_reference_blind_175_step_v100_run(self) -> None:
        contracts = load_r0b_contracts()
        self.assertEqual(
            contracts["method"]["execution_identity"]["scientific_schedule_denominator"],
            1000,
        )
        self.assertEqual(
            contracts["method"]["execution_identity"]["canonical_optimizer_steps"],
            175,
        )
        self.assertEqual(
            contracts["diagnostic"]["execution"]["cloud_shadow_optimizer_steps"], 0
        )
        self.assertFalse(
            contracts["diagnostic"]["reference_boundary"]["cloud_reference_fields_read"]
        )
        self.assertFalse(
            contracts["diagnostic"]["reference_boundary"][
                "stress_reference_fields_or_metrics_may_be_read"
            ]
        )

    def test_schedule_denominator_is_not_shortened_to_execution_limit(self) -> None:
        self.assertEqual(_active_windows(149, 1000), 1)
        self.assertEqual(_active_windows(150, 1000), 2)
        self.assertEqual(_active_windows(174, 1000), 2)
        self.assertEqual(_active_windows(27, 175), 2)
        self.assertEqual(_active_windows(27, 1000), 1)

    def test_diagnostic_prefix_writes_truthful_checkpoint_manifest_and_terminal_log(self) -> None:
        observer = _RecordingObserver()
        with tempfile.TemporaryDirectory() as directory:
            run_directory = Path(directory) / "run"
            outcome = train(
                self._tiny_config(),
                run_directory=run_directory,
                execution_limit=175,
                observer=observer,
                execution_metadata={"task_id": "TEST_R0B"},
            )
            checkpoint = torch.load(
                outcome.checkpoint_path, map_location="cpu", weights_only=False
            )
            manifest = json.loads(
                (run_directory / "manifest-final.json").read_text(encoding="utf-8")
            )
            log = [
                json.loads(line)
                for line in (run_directory / "training-log.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
        self.assertEqual(outcome.status, "DIAGNOSTIC_PREFIX")
        self.assertEqual(checkpoint["update"], 175)
        self.assertEqual(checkpoint["training_config"]["updates"], 1000)
        self.assertEqual(manifest["scientific_schedule_denominator"], 1000)
        self.assertEqual(manifest["canonical_optimizer_steps_executed"], 175)
        self.assertEqual(manifest["status"], "DIAGNOSTIC_PREFIX")
        self.assertEqual(log[-1]["update"], 175)
        self.assertIn(("PRE_BACKWARD", 151, 2, True), observer.events)
        self.assertNotIn(("PRE_BACKWARD", 176, 2, False), observer.events)

    def test_optional_observer_does_not_change_tiny_training_trajectory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = train(
                self._tiny_config(),
                run_directory=Path(directory) / "without",
                execution_limit=3,
            )
            observer = _RecordingObserver()
            second = train(
                self._tiny_config(),
                run_directory=Path(directory) / "with",
                execution_limit=3,
                observer=observer,
            )
            first_checkpoint = torch.load(
                first.checkpoint_path, map_location="cpu", weights_only=False
            )
            second_checkpoint = torch.load(
                second.checkpoint_path, map_location="cpu", weights_only=False
            )
        for name, tensor in first_checkpoint["model_state_dict"].items():
            self.assertTrue(torch.equal(tensor, second_checkpoint["model_state_dict"][name]))
        first_optimizer = first_checkpoint["optimizer_state_dict"]
        second_optimizer = second_checkpoint["optimizer_state_dict"]
        self.assertEqual(first_optimizer["param_groups"], second_optimizer["param_groups"])
        self.assertEqual(set(first_optimizer["state"]), set(second_optimizer["state"]))
        for parameter_id, first_state in first_optimizer["state"].items():
            second_state = second_optimizer["state"][parameter_id]
            self.assertEqual(set(first_state), set(second_state))
            for name, first_value in first_state.items():
                second_value = second_state[name]
                if isinstance(first_value, torch.Tensor):
                    self.assertTrue(torch.equal(first_value, second_value))
                else:
                    self.assertEqual(first_value, second_value)

    def test_gradient_probe_preserves_preexisting_gradients(self) -> None:
        model = self._model()
        contracts = load_r0b_contracts()
        sampler = PhkCollocationSampler(physics=model.physics, seed=23017)
        interior = sampler.interior_uniform(
            8, active_windows=1, dtype=torch.float64, device=torch.device("cpu")
        )
        boundary = sampler.boundary(
            4, active_windows=1, dtype=torch.float64, device=torch.device("cpu")
        )
        initial = sampler.initial(4, dtype=torch.float64, device=torch.device("cpu"))
        before = []
        for parameter in model.parameters():
            parameter.grad = torch.ones_like(parameter)
            before.append(parameter.grad.clone())
        result = gradient_matrix_preserving_state(
            model,
            interior,
            boundary,
            contracts,
            initial=initial,
            loss_rows=("PHASE_PDE", "TOTAL_OBJECTIVE"),
        )
        self.assertTrue(result["persistent_parameter_gradients_preserved"])
        for parameter, expected in zip(model.parameters(), before, strict=True):
            self.assertTrue(torch.equal(parameter.grad, expected))

    def test_r0b_observer_builds_balanced_reference_free_pool_and_preserves_rng(self) -> None:
        model = self._model()
        contracts = load_r0b_contracts()
        with tempfile.TemporaryDirectory() as directory:
            run_directory = Path(directory) / "run"
            run_directory.mkdir()
            observer = R0BObserver(
                run_directory=run_directory,
                contracts=contracts,
                source_identity="TEST",
                soft_stop_seconds=600.0,
            )
            cpu_rng = torch.random.get_rng_state().clone()
            observer.observe(
                TrainingObservation(
                    phase="PRE_RUN",
                    optimizer_step=0,
                    update_index=None,
                    active_windows=0,
                    collocation_refreshed=False,
                    model=model,
                    interior=None,
                    boundary=None,
                    initial=None,
                    scalars={},
                )
            )
            summary = observer.finalize()
        self.assertEqual(summary["pool_identity"]["scalar_points_total"], 1024)
        self.assertEqual(summary["pool_identity"]["scalar_points_per_window"], 512)
        self.assertTrue(torch.equal(torch.random.get_rng_state(), cpu_rng))
        self.assertFalse(summary["reference_fields_read"])

    @staticmethod
    def _synthetic_records(*, switch: bool = False, conditioned: bool = False):
        contracts = load_r0b_contracts()
        steps = sorted(
            set(contracts["method"]["observer"]["cheap_post_step_observations"])
            | set(contracts["method"]["observer"]["full_gradient_observations"])
        )
        records = []
        for step in steps:
            phase = 0.02
            jacobian = 0.2
            if switch and step >= 151:
                phase = 0.005
                jacobian = 0.05
            metrics = {
                "potential_top_sigmoid_error_rms_w1": 0.1,
                "potential_bottom_sigmoid_error_rms_w1": 0.1,
                "temperature_max_w1": 0.8,
                "positive_growth_roi_fraction_w1": 0.5,
                "phase_jacobian_below_floor_fraction_w1": 1.0 if conditioned else 0.0,
                "phase_output_capacity_0_1": 0.001 if conditioned else 1.0,
                "phase_output_capacity_1_10": 0.001 if conditioned else 1.0,
                "phase_max_w1": phase,
                "phase_jacobian_q95_w1": jacobian,
                "phase_activity_fraction_w1": 0.0 if step == 175 else 0.1,
            }
            gradient = {
                "gradient_norms": {
                    "TOTAL_OBJECTIVE": {
                        "potential": 1.0,
                        "temperature": 1.0,
                        "phase": 1.0,
                    }
                },
                "same_head_pairwise_cosines": {"phase": {}},
            }
            records.append(
                {
                    "phase": "POST_STEP_FIXED_POOL",
                    "optimizer_step": step,
                    "metrics": metrics,
                    "full_gradient": gradient if step in contracts["method"]["observer"]["full_gradient_observations"] else None,
                }
            )
        return records

    def test_machine_returns_phase_conditioning_when_two_initial_capacity_intervals_fail(self) -> None:
        result = adjudicate_reference_blind(
            self._synthetic_records(conditioned=True), load_r0b_contracts()
        )
        self.assertEqual(result["PRIMARY_PRECURSOR_CANDIDATE"], "PHASE_OUTPUT_CONDITIONING")
        self.assertFalse(result["causal_root_cause_identified"])

    def test_machine_detects_persistent_step_151_switch_shock(self) -> None:
        result = adjudicate_reference_blind(
            self._synthetic_records(switch=True), load_r0b_contracts()
        )
        self.assertEqual(result["PRIMARY_PRECURSOR_CANDIDATE"], "SWITCH_INDUCED")
        self.assertTrue(result["factorial_required"])

    def test_machine_uses_optimization_unresolved_only_after_other_classes_fail(self) -> None:
        result = adjudicate_reference_blind(
            self._synthetic_records(), load_r0b_contracts()
        )
        self.assertEqual(result["PRIMARY_PRECURSOR_CANDIDATE"], "OPTIMIZATION_UNRESOLVED")
        self.assertFalse(result["factorial_required"])

    def test_gpu_runner_rejects_cpu_before_constructing_training(self) -> None:
        with mock.patch("pinn_pcm_sci.phk_v23_r0b._git_head", return_value="TEST"):
            with self.assertRaises(PermissionError):
                run_reference_blind_gpu_replay(
                    output_root=Path("unused-r0b-output"),
                    device_name="cpu",
                    source_identity="TEST",
                    hourly_price_cny=1.88,
                )


if __name__ == "__main__":
    unittest.main()
