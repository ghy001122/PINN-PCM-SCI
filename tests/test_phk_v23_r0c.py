from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import torch

from pinn_pcm_sci.phk_v22r_pinn import PhkV22RArm, PhkV22RModel
from pinn_pcm_sci.phk_v22r_training import PhkTrainingConfig, TrainingObservation, load_case_physics, train
from pinn_pcm_sci.phk_v23_r0c import R0CObserver, adjudicate_reference_blind, load_r0c_contracts


class _UpdateObserver:
    requested_phases = frozenset(
        {
            "PRE_BACKWARD",
            "POST_BACKWARD_PRE_CLIP",
            "POST_CLIP_PRE_STEP",
            "POST_STEP",
        }
    )
    include_optimizer_state_summary = True

    def __init__(self) -> None:
        self.events: list[str] = []
        self.summary = None

    def observe(self, observation: TrainingObservation) -> None:
        self.events.append(observation.phase)
        if observation.phase == "POST_STEP":
            self.summary = observation.optimizer_state_summary


class PhkV23R0CTests(unittest.TestCase):
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

    def test_contract_freezes_one_reference_blind_25_step_v100_run(self) -> None:
        contracts = load_r0c_contracts()
        identity = contracts["method"]["execution_identity"]
        self.assertEqual(identity["scientific_schedule_denominator"], 1000)
        self.assertEqual(identity["canonical_optimizer_steps"], 25)
        self.assertEqual(identity["cloud_shadow_optimizer_steps"], 0)
        self.assertEqual(contracts["program"]["execution_budget"]["maximum_scientific_gpu_runs"], 1)
        self.assertFalse(contracts["program"]["authorization"]["selective_commit_and_push_authorized"])
        self.assertTrue(all(value is False for value in contracts["diagnostic"]["reference_boundary"].values()))

    def test_training_observer_seam_exposes_update_phases_without_optimizer(self) -> None:
        observer = _UpdateObserver()
        with tempfile.TemporaryDirectory() as directory:
            outcome = train(
                self._tiny_config(),
                run_directory=Path(directory) / "run",
                execution_limit=1,
                observer=observer,
            )
        self.assertEqual(outcome.status, "DIAGNOSTIC_PREFIX")
        self.assertEqual(
            observer.events,
            [
                "PRE_BACKWARD",
                "POST_BACKWARD_PRE_CLIP",
                "POST_CLIP_PRE_STEP",
                "POST_STEP",
            ],
        )
        self.assertIsNotNone(observer.summary)
        assert observer.summary is not None
        self.assertTrue(all(set(item) == {"step", "exp_avg_l2", "exp_avg_sq_l2"} for item in observer.summary.values()))
        self.assertTrue(all(int(item["step"]) in {0, 1} for item in observer.summary.values()))
        self.assertTrue(any(int(item["step"]) == 1 for item in observer.summary.values()))

    def test_strong_raw_parameter_ownership_is_exactly_three_heads(self) -> None:
        model = self._model()
        contracts = load_r0c_contracts()
        with tempfile.TemporaryDirectory() as directory:
            observer = R0CObserver(
                run_directory=Path(directory),
                contracts=contracts,
                source_identity="TEST",
                soft_stop_seconds=600.0,
            )
            observer._assert_groups(model)
        assigned = {
            name
            for group in observer.groups.values()
            for name, _ in group
        }
        self.assertEqual(assigned, {name for name, parameter in model.named_parameters() if parameter.requires_grad})
        self.assertEqual(set(observer.groups), {"potential", "temperature", "phase"})

    def test_pre_run_fixed_probe_matches_frozen_pool_and_preserves_rng(self) -> None:
        model = self._model()
        contracts = load_r0c_contracts()
        cpu_rng = torch.random.get_rng_state().clone()
        with tempfile.TemporaryDirectory() as directory:
            observer = R0CObserver(
                run_directory=Path(directory),
                contracts=contracts,
                source_identity="TEST",
                soft_stop_seconds=600.0,
            )
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
        self.assertEqual(
            observer.pool_identity["pool_sha256"],
            contracts["method"]["diagnostic_pool"]["expected_pool_sha256"],
        )
        self.assertTrue(torch.equal(torch.random.get_rng_state(), cpu_rng))

    @staticmethod
    def _records(*, update_ratio: float, raw_ratio: float = 0.01, output_confound: bool = False):
        records = []
        for step in range(1, 26):
            metrics = {
                "temperature_max_w1": 0.7,
                "positive_growth_roi_fraction_w1": 0.1,
                "phase_jacobian_below_floor_fraction_w1": 0.99 if output_confound else 0.05,
                "phase_jacobian_q95_w1": 0.005 if output_confound else 0.05,
            }
            if step == 10:
                metrics["phase_output_capacity_0_1"] = 0.001 if output_confound else 0.1
                metrics["phase_output_capacity_1_10"] = 0.001 if output_confound else 0.1
            records.append(
                {
                    "optimizer_step": step,
                    "trajectory_identity": {"passed": True} if step in {1, 10, 20, 25} else None,
                    "raw_gradient_ratio": raw_ratio,
                    "effective_update_ratio": update_ratio,
                    "head_updates": {
                        "potential": {"relative_l2": 1.0e-3},
                        "temperature": {"relative_l2": 2.0e-3},
                        "phase": {"relative_l2": update_ratio * 2.0e-3},
                    },
                    "fixed_pool_metrics": metrics,
                }
            )
        return records

    def test_machine_supports_effective_update_starvation(self) -> None:
        result = adjudicate_reference_blind(self._records(update_ratio=0.05), load_r0c_contracts())
        self.assertEqual(result["status"], "R0C_EFFECTIVE_UPDATE_STARVATION_SUPPORTED")
        self.assertEqual(result["qualifying_block"], {"start": 10, "end": 19})
        self.assertFalse(result["next_stage_authorized"])

    def test_machine_detects_adam_compensation(self) -> None:
        result = adjudicate_reference_blind(self._records(update_ratio=0.75), load_r0c_contracts())
        self.assertEqual(result["status"], "R0C_ADAM_PRECONDITIONING_COMPENSATES_RAW_GRADIENT")

    def test_machine_stops_when_update_ratio_is_between_frozen_gates(self) -> None:
        result = adjudicate_reference_blind(self._records(update_ratio=0.25), load_r0c_contracts())
        self.assertEqual(result["status"], "R0C_INCONCLUSIVE_STOP")

    def test_output_conditioning_confound_blocks_both_positive_optimizer_outcomes(self) -> None:
        result = adjudicate_reference_blind(
            self._records(update_ratio=0.05, output_confound=True), load_r0c_contracts()
        )
        self.assertEqual(result["status"], "R0C_INCONCLUSIVE_STOP")
        self.assertTrue(result["output_conditioning_confound"])

    def test_trajectory_identity_failure_is_invalid_not_inconclusive(self) -> None:
        records = self._records(update_ratio=0.05)
        records[9]["trajectory_identity"] = {"passed": False}
        with self.assertRaisesRegex(ValueError, "trajectory identity"):
            adjudicate_reference_blind(records, load_r0c_contracts())

    def test_r0c_module_has_no_reference_or_evaluator_import(self) -> None:
        source = (Path(__file__).parents[1] / "pinn_pcm_sci" / "phk_v23_r0c.py").read_text(encoding="utf-8")
        self.assertNotIn("phk_v22r_evaluator", source)
        self.assertNotIn("load_reference", source)
        self.assertNotIn("STRESS_REFERENCES", source)


if __name__ == "__main__":
    unittest.main()
