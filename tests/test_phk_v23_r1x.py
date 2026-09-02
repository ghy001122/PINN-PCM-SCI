from __future__ import annotations

import inspect
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import torch

from pinn_pcm_sci.phk_v22r_pinn import (
    FrequencyBand,
    PhkV22RModel,
    boundary_residuals,
    interior_diagnostic_terms,
    interior_residuals,
)
from pinn_pcm_sci.phk_v22r_training import (
    PhkTrainingConfig,
    campaign_weighted_loss_groups,
    load_case_physics,
    train,
)
from pinn_pcm_sci.phk_v23_r1x import (
    E1,
    E2_PHASE_NORMALIZED,
    E2_SMOOTHER_RAMP,
    E2_TOP_HARD_LIFT,
    ET_GROUPS,
    CampaignController,
    CampaignVariant,
    accelerated_active_windows,
    build_campaign_model,
    load_r1x_contracts,
    machine_action,
    readiness_gate,
    select_local_outcome,
    smoothstep_alpha,
    validate_campaign_counts,
)


def _model(*, variant: CampaignVariant = E1) -> PhkV22RModel:
    physics, _, _ = load_case_physics("FULL")
    return build_campaign_model(
        physics=physics,
        hidden_width=8,
        hidden_layers=2,
        frequency_band=FrequencyBand.band_a(),
        variant=variant,
    ).to(dtype=torch.float64)


def _coordinates() -> torch.Tensor:
    return torch.tensor(
        [
            [-0.30, 0.20, 0.10],
            [0.10, 0.45, 0.30],
            [0.45, 0.75, 1.35],
        ],
        dtype=torch.float64,
    )


def _tiny_config(updates: int = 4) -> PhkTrainingConfig:
    return PhkTrainingConfig(
        arm="STRONG_RAW",
        updates=updates,
        seed=17,
        hidden_width=8,
        hidden_layers=2,
        interior_points=8,
        boundary_points=4,
        initial_points=4,
        candidate_pool_multiplier=1,
        refresh_updates=250,
        log_every=1,
        checkpoint_every=10_000,
        dtype="float64",
        device="cpu",
    )


class _FixedPolicy:
    def __init__(self, spec) -> None:
        self.spec = spec
        self.stop_requested = False

    def step_spec(self, optimizer_step: int, total_updates: int):
        del optimizer_step, total_updates
        return self.spec


class _PhaseSnapshotObserver:
    requested_phases = frozenset({"PRE_RUN", "POST_STEP"})

    def __init__(self) -> None:
        self.before = None
        self.after = None

    def observe(self, observation) -> None:
        values = {
            name: value.detach().clone()
            for name, value in observation.model.heads["phase"].state_dict().items()
        }
        if observation.phase == "PRE_RUN":
            self.before = values
        else:
            self.after = values


class _HeadAndAdamTraceObserver:
    requested_phases = frozenset({"PRE_RUN", "POST_STEP"})
    include_optimizer_state_summary = True

    def __init__(self) -> None:
        self.heads = []
        self.optimizer_steps = []

    def observe(self, observation) -> None:
        self.heads.append(
            {
                name: torch.cat(
                    tuple(
                        parameter.detach().reshape(-1).clone()
                        for parameter in observation.model.heads[name].parameters()
                    )
                )
                for name in ("potential", "temperature", "phase")
            }
        )
        summary = observation.optimizer_state_summary or {}
        self.optimizer_steps.append(
            {
                head: max(
                    (
                        int(value["step"])
                        for name, value in summary.items()
                        if name.startswith(f"heads.{head}.")
                    ),
                    default=0,
                )
                for head in ("potential", "temperature", "phase")
            }
        )


class PhkV23R1XTests(unittest.TestCase):
    def test_01_contract_freezes_campaign_counts_and_seed(self) -> None:
        contracts = load_r1x_contracts()
        program = contracts["program"]
        method = contracts["method"]
        self.assertEqual(program["run_limits"]["maximum_non_voting_explorations"], 3)
        self.assertEqual(program["run_limits"]["maximum_frozen_confirmations"], 1)
        self.assertEqual(method["common_execution_identity"]["seed"], 17)

    def test_02_contract_keeps_stress_sealed_and_reference_out_of_cloud(self) -> None:
        contracts = load_r1x_contracts()
        roles = contracts["program"]["reference_roles"]
        self.assertEqual(roles["cloud"], "REFERENCE_BLIND")
        self.assertEqual(roles["stress"], "TWO_STRESS_REFERENCES_SEALED_UNREAD")

    def test_03_alpha_zero_uses_exact_physical_initial_phase(self) -> None:
        model = _model()
        coordinates = _coordinates().requires_grad_(True)
        residuals = interior_diagnostic_terms(model, coordinates, coupling_alpha=0.0)
        expected = model.physics.initial_phase(coordinates)
        self.assertTrue(torch.equal(residuals["coupling_phase"], expected))

    def test_04_alpha_zero_latent_derivative_is_exact_zero(self) -> None:
        model = _model()
        residuals = interior_diagnostic_terms(
            model, _coordinates().requires_grad_(True), coupling_alpha=0.0
        )
        self.assertTrue(torch.equal(residuals["coupling_phase_time"], torch.zeros_like(residuals["coupling_phase_time"])))
        self.assertTrue(torch.equal(residuals["thermal_latent"], torch.zeros_like(residuals["thermal_latent"])))

    def test_05_phase_parameters_do_not_affect_warmup_electric_or_thermal_residuals(self) -> None:
        first = _model()
        second = _model()
        second.load_state_dict(first.state_dict())
        with torch.no_grad():
            for parameter in second.heads["phase"].parameters():
                parameter.add_(3.0)
        a = interior_residuals(first, _coordinates(), coupling_alpha=0.0)
        b = interior_residuals(second, _coordinates(), coupling_alpha=0.0)
        self.assertTrue(torch.equal(a["electric"], b["electric"]))
        self.assertTrue(torch.equal(a["thermal"], b["thermal"]))

    def test_06_alpha_one_interior_residuals_match_legacy(self) -> None:
        model = _model()
        coordinates = _coordinates()
        legacy = interior_residuals(model, coordinates)
        coupled = interior_residuals(model, coordinates, coupling_alpha=1.0)
        for name in ("electric", "thermal", "phase"):
            self.assertTrue(torch.allclose(legacy[name], coupled[name], rtol=1e-12, atol=1e-14), name)

    def test_07_alpha_one_boundary_residuals_match_legacy(self) -> None:
        model = _model()
        top = torch.tensor([[-0.3, 1.0, 0.1], [0.2, 1.0, 1.3]], dtype=torch.float64)
        legacy = boundary_residuals(model, top, side="top")
        coupled = boundary_residuals(model, top, side="top", coupling_alpha=1.0)
        self.assertEqual(set(legacy), set(coupled))
        for name in legacy:
            self.assertTrue(torch.allclose(legacy[name], coupled[name], rtol=1e-12, atol=1e-14), name)

    def test_08_phase_pde_is_independent_of_coupling_alpha(self) -> None:
        model = _model()
        zero = interior_residuals(model, _coordinates(), coupling_alpha=0.0)
        half = interior_residuals(model, _coordinates(), coupling_alpha=0.5)
        self.assertTrue(torch.equal(zero["phase"], half["phase"]))

    def test_09_accelerated_windows_have_exact_boundaries(self) -> None:
        observed = [accelerated_active_windows(step) for step in (1, 50, 51, 100, 101, 150, 151, 1800)]
        self.assertEqual(observed, [1, 1, 2, 2, 3, 3, 4, 4])

    def test_10_step_151_and_later_always_have_four_windows(self) -> None:
        self.assertTrue(all(accelerated_active_windows(step) == 4 for step in range(151, 2201)))

    def test_11_readiness_requires_all_three_metrics_in_w1_and_w3(self) -> None:
        passing = {
            "W1": {"thermal_activation_fraction": 0.02, "positive_cold_kinetic_growth_fraction": 0.02, "joule_q95_roi": 1.1e-12},
            "W3": {"thermal_activation_fraction": 0.03, "positive_cold_kinetic_growth_fraction": 0.04, "joule_q95_roi": 2.0e-12},
            "finite": True,
        }
        self.assertTrue(readiness_gate(passing))
        passing["W3"]["thermal_activation_fraction"] = 0.019
        self.assertFalse(readiness_gate(passing))

    def test_12_readiness_requires_two_consecutive_checkpoints(self) -> None:
        controller = CampaignController(E1)
        metrics = {
            "W1": {"thermal_activation_fraction": 0.03, "positive_cold_kinetic_growth_fraction": 0.03, "joule_q95_roi": 2e-12},
            "W3": {"thermal_activation_fraction": 0.03, "positive_cold_kinetic_growth_fraction": 0.03, "joule_q95_roi": 2e-12},
            "finite": True,
        }
        controller.record_readiness(200, metrics)
        self.assertIsNone(controller.ready_step)
        controller.record_readiness(225, metrics)
        self.assertEqual(controller.ready_step, 225)

    def test_13_failed_readiness_at_300_requests_stop(self) -> None:
        controller = CampaignController(E1)
        failing = {
            "W1": {"thermal_activation_fraction": 0.0, "positive_cold_kinetic_growth_fraction": 0.0, "joule_q95_roi": 0.0},
            "W3": {"thermal_activation_fraction": 0.0, "positive_cold_kinetic_growth_fraction": 0.0, "joule_q95_roi": 0.0},
            "finite": True,
        }
        for step in (200, 225, 250, 275, 300):
            controller.record_readiness(step, failing)
        self.assertTrue(controller.stop_requested)
        self.assertEqual(controller.reference_blind_outcome, "ET_NOT_READY")

    def test_14_ramp_alpha_is_monotone_with_exact_endpoints(self) -> None:
        values = [smoothstep_alpha(index, 400) for index in range(400)]
        self.assertEqual(values[0], 0.0)
        self.assertEqual(values[-1], 1.0)
        self.assertTrue(all(a <= b for a, b in zip(values, values[1:])))

    def test_15_ramp_block_cycle_is_two_et_two_phase_one_joint(self) -> None:
        controller = CampaignController(E1)
        controller.ready_step = 225
        stages = [controller.step_spec(step, 1800).block_type for step in range(226, 231)]
        self.assertEqual(stages, ["ELECTROTHERMAL_BLOCK", "ELECTROTHERMAL_BLOCK", "PHASE_BLOCK", "PHASE_BLOCK", "JOINT_BLOCK"])

    def test_16_inactive_head_sets_are_exact(self) -> None:
        controller = CampaignController(E1)
        warmup = controller.step_spec(200, 1800)
        self.assertEqual(warmup.active_heads, ("potential", "temperature"))
        controller.ready_step = 225
        phase = controller.step_spec(228, 1800)
        self.assertEqual(phase.active_heads, ("phase",))

    def test_17_e1_has_at_least_1100_full_physics_steps(self) -> None:
        controller = CampaignController(E1)
        controller.ready_step = 300
        full = [step for step in range(1, 1801) if controller.step_spec(step, 1800).stage == "FULL_PHYSICS_JOINT_CLOSURE"]
        self.assertEqual(len(full), 1100)

    def test_18_smoother_ramp_keeps_at_least_half_full_physics(self) -> None:
        controller = CampaignController(E2_SMOOTHER_RAMP)
        controller.ready_step = 300
        full = [step for step in range(1, 2201) if controller.step_spec(step, 2200).stage == "FULL_PHYSICS_JOINT_CLOSURE"]
        self.assertEqual(len(full), 1100)

    def test_19_top_hard_lift_exactly_satisfies_top_dirichlet(self) -> None:
        model = _model(variant=E2_TOP_HARD_LIFT)
        coordinates = torch.tensor([[-0.4, 1.0, 0.1], [0.2, 1.0, 1.3]], dtype=torch.float64)
        potential = model(coordinates)[:, 0:1]
        self.assertTrue(torch.equal(potential, model.physics.waveform(coordinates[:, 2:3])))

    def test_20_top_hard_lift_keeps_t0_potential_zero(self) -> None:
        model = _model(variant=E2_TOP_HARD_LIFT)
        coordinates = torch.tensor([[-0.4, 0.2, 0.0], [0.2, 1.0, 0.0]], dtype=torch.float64)
        self.assertTrue(torch.equal(model(coordinates)[:, 0:1], torch.zeros((2, 1), dtype=torch.float64)))

    def test_21_phase_normalized_transform_keeps_hard_ic_and_bounds(self) -> None:
        model = _model(variant=E2_PHASE_NORMALIZED)
        coordinates = torch.tensor([[-0.2, 0.1, 0.0], [0.2, 0.8, 0.0]], dtype=torch.float64)
        phase = model(coordinates)[:, 2:3]
        self.assertTrue(torch.equal(phase, model.physics.initial_phase(coordinates)))
        later = model(_coordinates())[:, 2:3]
        self.assertTrue(bool(torch.all((later > 0.0) & (later < 1.0))))

    def test_22_phase_normalized_beta_cap_is_frozen_to_32(self) -> None:
        model = _model(variant=E2_PHASE_NORMALIZED)
        self.assertEqual(model.phase_jacobian_beta_cap, 32.0)
        manifest = model.architecture_manifest()
        self.assertEqual(manifest["phase_jacobian_beta_cap"], 32.0)

    def test_23_e2_variants_are_mutually_exclusive(self) -> None:
        self.assertEqual(len({E2_TOP_HARD_LIFT.variant_id, E2_PHASE_NORMALIZED.variant_id, E2_SMOOTHER_RAMP.variant_id}), 3)
        with self.assertRaises(ValueError):
            CampaignVariant("INVALID", "TOP_DIRICHLET_HARD_LIFT", "JACOBIAN_NORMALIZED", 400, 1800)

    def test_24_campaign_run_count_caps_fail_closed(self) -> None:
        validate_campaign_counts(explorations=3, confirmations=1)
        with self.assertRaises(PermissionError):
            validate_campaign_counts(explorations=4, confirmations=1)
        with self.assertRaises(PermissionError):
            validate_campaign_counts(explorations=3, confirmations=2)

    def test_25_local_outcome_selects_top_lift_only_after_et_not_ready(self) -> None:
        result = select_local_outcome(
            variant=E1,
            run_summary={"reference_blind_outcome": "ET_NOT_READY", "phase_signal_ever": False, "final_phase_max": 0.03},
            evaluation={"hard_guards": {"passed": False, "event_topology": {"cycles": []}}},
        )
        self.assertEqual(result, "E1_ET_NOT_READY")
        self.assertEqual(machine_action(result, explorations_completed=1), "RUN_E2_TOP_DIRICHLET_HARD_LIFT")

    def test_26_local_outcome_selects_phase_transform_only_after_no_response(self) -> None:
        result = select_local_outcome(
            variant=E1,
            run_summary={"reference_blind_outcome": "COMPLETE", "phase_signal_ever": False, "final_phase_max": 0.03},
            evaluation={"hard_guards": {"passed": False, "event_topology": {"cycles": []}}},
        )
        self.assertEqual(result, "E1_ET_READY_PHASE_NO_RESPONSE")
        self.assertEqual(machine_action(result, explorations_completed=1), "RUN_E2_PHASE_JACOBIAN_NORMALIZED_OUTPUT")

    def test_27_material_signal_selects_smoother_ramp_then_e3_extension(self) -> None:
        result = select_local_outcome(
            variant=E1,
            run_summary={"reference_blind_outcome": "COMPLETE", "phase_signal_ever": True, "final_phase_max": 0.15},
            evaluation={"hard_guards": {"passed": False, "event_topology": {"cycles": []}}},
        )
        self.assertEqual(result, "E1_PHASE_SIGNAL_INCOMPLETE_OR_COLLAPSED")
        self.assertEqual(machine_action(result, explorations_completed=1), "RUN_E2_SMOOTHER_COUPLING_RAMP")

    def test_28_competence_routes_to_exactly_one_confirmation(self) -> None:
        result = select_local_outcome(
            variant=E1,
            run_summary={"reference_blind_outcome": "COMPLETE", "phase_signal_ever": True, "final_phase_max": 0.7},
            evaluation={"hard_guards": {"passed": True, "event_topology": {"cycles": [{"event_time": 0.2}, {"event_time": 1.45}]}}},
        )
        self.assertEqual(result, "E1_COMPETENCE_SIGNAL_OBSERVED")
        self.assertEqual(machine_action(result, explorations_completed=1), "RUN_FROZEN_CONFIRMATION")

    def test_29_campaign_api_has_no_reference_or_stress_path_parameter(self) -> None:
        from pinn_pcm_sci.phk_v23_r1x import run_reference_blind_trajectory

        parameters = inspect.signature(run_reference_blind_trajectory).parameters
        self.assertNotIn("reference_path", parameters)
        self.assertNotIn("stress_path", parameters)

    def test_30_campaign_training_keeps_warmup_phase_parameters_bitwise_fixed(self) -> None:
        from pinn_pcm_sci.phk_v22r_training import TrainingStepSpec

        policy = _FixedPolicy(
            TrainingStepSpec(
                stage="CLEAN_ELECTROTHERMAL_WARMUP",
                block_type="ELECTROTHERMAL_BLOCK",
                active_windows=1,
                coupling_alpha=0.0,
                active_heads=("potential", "temperature"),
                active_loss_groups=("G1_ELECTRIC_PDE", "G2_THERMAL_PDE", "G4_ET_AUXILIARY"),
            )
        )
        observer = _PhaseSnapshotObserver()
        with tempfile.TemporaryDirectory() as directory:
            train(
                _tiny_config(1),
                run_directory=Path(directory) / "warmup",
                step_policy=policy,
                observer=observer,
            )
        self.assertIsNotNone(observer.before)
        self.assertIsNotNone(observer.after)
        for name in observer.before:
            self.assertTrue(torch.equal(observer.before[name], observer.after[name]), name)

    def test_31_single_adam_instance_is_not_rebuilt_across_stage_specs(self) -> None:
        controller = CampaignController(E1)
        controller.ready_step = 1
        with tempfile.TemporaryDirectory() as directory, mock.patch(
            "pinn_pcm_sci.phk_v22r_training.torch.optim.Adam",
            wraps=torch.optim.Adam,
        ) as adam:
            train(
                _tiny_config(1800),
                run_directory=Path(directory) / "stages",
                execution_limit=4,
                step_policy=controller,
            )
        self.assertEqual(adam.call_count, 1)

    def test_32_split_auxiliary_groups_reconstruct_full_r1a_auxiliary(self) -> None:
        values = campaign_weighted_loss_groups(
            interior={
                "electric": torch.ones((2, 1), dtype=torch.float64),
                "thermal": torch.ones((2, 1), dtype=torch.float64),
                "phase": torch.ones((2, 1), dtype=torch.float64),
            },
            boundary_by_field={"potential": torch.tensor(0.1), "temperature": torch.tensor(0.2), "phase": torch.tensor(0.3)},
            initial_by_field={"potential": torch.tensor(0.01), "temperature": torch.tensor(0.02), "phase": torch.tensor(0.03)},
            config=_tiny_config(),
        )
        self.assertTrue(torch.equal(values["G4_ET_AUXILIARY"] + values["G4_PHASE_AUXILIARY"], values["G4_BOUNDARY_INITIAL"]))

    def test_33_inactive_heads_and_adam_state_remain_frozen_across_ramp_blocks(self) -> None:
        controller = CampaignController(E1)
        controller.ready_step = 0
        observer = _HeadAndAdamTraceObserver()
        with tempfile.TemporaryDirectory() as directory:
            train(
                _tiny_config(1800),
                run_directory=Path(directory) / "five-blocks",
                execution_limit=5,
                step_policy=controller,
                observer=observer,
            )
        # PRE_RUN, then two ET, two phase, one joint updates.
        self.assertEqual(len(observer.heads), 6)
        for before, after in zip(observer.heads[0:2], observer.heads[1:3], strict=True):
            self.assertTrue(torch.equal(before["phase"], after["phase"]))
        for before, after in zip(observer.heads[2:4], observer.heads[3:5], strict=True):
            self.assertTrue(torch.equal(before["potential"], after["potential"]))
            self.assertTrue(torch.equal(before["temperature"], after["temperature"]))
        self.assertEqual(
            observer.optimizer_steps,
            [
                {"potential": 0, "temperature": 0, "phase": 0},
                {"potential": 1, "temperature": 1, "phase": 0},
                {"potential": 2, "temperature": 2, "phase": 0},
                {"potential": 2, "temperature": 2, "phase": 1},
                {"potential": 2, "temperature": 2, "phase": 2},
                {"potential": 3, "temperature": 3, "phase": 3},
            ],
        )

    def test_34_e3_changes_only_the_frozen_full_joint_extension(self) -> None:
        for base in (E2_TOP_HARD_LIFT, E2_PHASE_NORMALIZED, E2_SMOOTHER_RAMP):
            extended = base.with_e3_extension()
            self.assertEqual(extended.variant_id, base.variant_id)
            self.assertEqual(extended.potential_transform, base.potential_transform)
            self.assertEqual(extended.phase_transform, base.phase_transform)
            self.assertEqual(extended.ramp_length, base.ramp_length)
            self.assertEqual(extended.maximum_updates, base.maximum_updates)
            self.assertEqual(extended.total_updates, base.maximum_updates + 500)

    def test_35_staged_manifest_is_truthful_and_checkpoint_policy_is_final_only(self) -> None:
        from pinn_pcm_sci.phk_v22r_training import TrainingStepSpec

        policy = _FixedPolicy(
            TrainingStepSpec(
                stage="CLEAN_ELECTROTHERMAL_WARMUP",
                block_type="ELECTROTHERMAL_BLOCK",
                active_windows=1,
                coupling_alpha=0.0,
                active_heads=("potential", "temperature"),
                active_loss_groups=ET_GROUPS,
            )
        )
        with tempfile.TemporaryDirectory() as directory:
            run_directory = Path(directory) / "manifest"
            result = train(
                _tiny_config(2),
                run_directory=run_directory,
                step_policy=policy,
            )
            start = json.loads((run_directory / "manifest-start.json").read_text())
            final = json.loads((run_directory / "manifest-final.json").read_text())
            checkpoints = sorted(path.name for path in run_directory.glob("checkpoint-*.pt"))
        self.assertEqual(start["sampler_inputs"], ["SOBOL"])
        self.assertIsNone(start["causal_window_open_fractions"])
        self.assertEqual(start["checkpoint_policy"], "FINAL_ONLY")
        self.assertEqual(checkpoints, ["checkpoint-final.pt"])
        self.assertEqual(result.executed_updates, 2)
        self.assertEqual(final["canonical_optimizer_steps_executed"], 2)
        self.assertEqual(final["scientific_schedule_denominator"], 2)

    def test_36_confirmation_interface_cannot_load_an_exploration_checkpoint(self) -> None:
        from pinn_pcm_sci.phk_v23_r1x import run_reference_blind_trajectory

        parameters = inspect.signature(run_reference_blind_trajectory).parameters
        for forbidden in (
            "checkpoint",
            "checkpoint_path",
            "optimizer_state",
            "initial_state",
            "reference_path",
            "stress_path",
        ):
            self.assertNotIn(forbidden, parameters)

    def test_37_deployed_bundle_identity_binds_every_runtime_source_file(self) -> None:
        root = Path(__file__).resolve().parents[1]
        path = root / "cloud" / "phk_v23_r1x_autodl" / "deployed-source-manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(
            {
                "pinn_pcm_sci/__init__.py",
                "pinn_pcm_sci/artifacts.py",
                "configs/phk_v21/engineering_contract.json",
                "configs/phk_v21/e1_solver_selection.json",
                "outputs/runs/20260827T-phk-v21-e2-engineering-search-001/summary.json",
                "tests/test_phk_v21_benchmark.py",
            }.issubset(manifest["files"]),
        )
        lines = []
        for relative, expected in sorted(manifest["files"].items()):
            actual = hashlib.sha256((root / relative).read_bytes()).hexdigest().upper()
            self.assertEqual(actual, expected, relative)
            lines.append(f"{relative}={actual}\n")
        identity = hashlib.sha256("".join(lines).encode("utf-8")).hexdigest().upper()
        self.assertEqual(manifest["source_identity"], f"R1X-BUNDLE-{identity}")

    def test_38_deployed_bundle_loads_physics_from_an_isolated_tree(self) -> None:
        root = Path(__file__).resolve().parents[1]
        manifest_path = (
            root / "cloud" / "phk_v23_r1x_autodl" / "deployed-source-manifest.json"
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            isolated = Path(directory)
            for relative in manifest["files"]:
                destination = isolated / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((root / relative).read_bytes())
            destination = (
                isolated
                / "cloud"
                / "phk_v23_r1x_autodl"
                / "deployed-source-manifest.json"
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(manifest_path.read_bytes())
            completed = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "from pinn_pcm_sci.phk_v22r_training import load_case_physics; "
                        "load_case_physics(); print('ISOLATED_PHYSICS_LOAD_VALID')"
                    ),
                ],
                cwd=isolated,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("ISOLATED_PHYSICS_LOAD_VALID", completed.stdout)


if __name__ == "__main__":
    unittest.main()
