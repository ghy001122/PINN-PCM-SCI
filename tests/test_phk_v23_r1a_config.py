from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import torch

from pinn_pcm_sci.phk_v22r_pinn import normalized_residual_loss
from pinn_pcm_sci.phk_v22r_training import (
    INITIAL_SCALES,
    PDE_SCALES,
    PhkTrainingConfig,
    canonical_weighted_loss_groups,
    train,
)
from pinn_pcm_sci.phk_v23_r1a_config import (
    ConFIGGradientCombiner,
    GROUP_NAMES,
    MECHANISM_STEPS,
    adjudicate_local_nominal,
    load_r1a_contracts,
)


class _TinyModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.alpha = torch.nn.Parameter(torch.tensor(0.4, dtype=torch.float64))
        self.beta = torch.nn.Parameter(torch.tensor(-0.3, dtype=torch.float64))


class _SummedLossCombiner:
    def __init__(self) -> None:
        self.calls = 0

    def manifest(self):
        return {"method": "TEST_SUMMED_LOSS_EQUIVALENT"}

    def combine(self, *, model, loss_groups, legacy_total):
        del model, loss_groups
        legacy_total.backward()
        self.calls += 1
        return {}


def _tiny_config() -> PhkTrainingConfig:
    return PhkTrainingConfig(
        arm="STRONG_RAW",
        updates=1000,
        seed=17,
        hidden_width=8,
        hidden_layers=2,
        interior_points=8,
        boundary_points=4,
        initial_points=4,
        candidate_pool_multiplier=1,
        refresh_updates=250,
        log_every=1,
        checkpoint_every=1000,
        device="cpu",
    )


class PhkV23R1AConFIGTests(unittest.TestCase):
    def test_contract_freezes_one_run_and_only_config_axis(self) -> None:
        contracts = load_r1a_contracts()
        program = contracts["program"]
        method = contracts["method"]
        self.assertTrue(
            program["authorization"]["one_r1a_reference_blind_v100_run_authorized"]
        )
        self.assertFalse(program["authorization"]["second_r1a_run_or_seed_change_authorized"])
        self.assertFalse(program["authorization"]["stress_prediction_or_unseal_authorized"])
        self.assertEqual(method["execution_identity"]["optimizer_updates"], 1000)
        self.assertEqual(tuple(method["config_gradient_groups"]), GROUP_NAMES)
        self.assertEqual(
            sorted(method["mechanism_observation_steps"]), sorted(MECHANISM_STEPS)
        )

    def test_four_groups_reconstruct_frozen_total(self) -> None:
        config = _tiny_config()
        interior = {
            "electric": torch.tensor([[2.0], [3.0]], dtype=torch.float64),
            "thermal": torch.tensor([[4.0], [5.0]], dtype=torch.float64),
            "phase": torch.tensor([[1.0], [6.0]], dtype=torch.float64),
        }
        boundary = torch.tensor(0.125, dtype=torch.float64)
        initial = torch.tensor(0.25, dtype=torch.float64)
        pde = normalized_residual_loss(interior, scales=PDE_SCALES)
        total = config.pde_weight * pde + config.boundary_weight * boundary + initial
        groups = canonical_weighted_loss_groups(
            interior=interior,
            boundary_loss=boundary,
            initial_loss=initial,
            config=config,
        )
        self.assertEqual(tuple(groups), GROUP_NAMES)
        self.assertTrue(
            torch.allclose(
                torch.stack(tuple(groups.values())).sum(),
                total,
                rtol=1.0e-12,
                atol=1.0e-14,
            )
        )

    def test_config_conflict_case_is_finite_and_positive_for_material_groups(self) -> None:
        model = _TinyModel()
        groups = {
            GROUP_NAMES[0]: model.alpha,
            GROUP_NAMES[1]: model.beta,
            GROUP_NAMES[2]: -0.2 * model.alpha + model.beta,
            GROUP_NAMES[3]: model.alpha + 0.2 * model.beta,
        }
        result = ConFIGGradientCombiner().combine(
            model=model,
            loss_groups=groups,
            legacy_total=torch.stack(tuple(groups.values())).sum(),
        )
        self.assertTrue(all(torch.isfinite(p.grad).all() for p in model.parameters()))
        self.assertTrue(all(value > 0.0 for value in result["combined_dot_by_group"].values()))
        self.assertTrue(
            all(value is not None and value > 0.0 for value in result["combined_cosine_by_group"].values())
        )

    def test_config_zero_group_and_none_gradients_do_not_produce_nan(self) -> None:
        model = _TinyModel()
        groups = {
            GROUP_NAMES[0]: model.alpha,
            GROUP_NAMES[1]: model.beta,
            GROUP_NAMES[2]: model.alpha + model.beta,
            GROUP_NAMES[3]: model.beta * 0.0,
        }
        combiner = ConFIGGradientCombiner()
        result = combiner.combine(
            model=model,
            loss_groups=groups,
            legacy_total=torch.stack(tuple(groups.values())).sum(),
        )
        self.assertEqual(result["zero_norm_groups"], [GROUP_NAMES[3]])
        self.assertIsNone(result["combined_cosine_by_group"][GROUP_NAMES[3]])
        self.assertTrue(all(torch.isfinite(p.grad).all() for p in model.parameters()))
        self.assertEqual(combiner.manifest()["trainable_parameters"], 0)
        self.assertEqual(len(tuple(combiner.__dict__)), 4)

    def test_legacy_default_and_equivalent_seam_are_exact_for_one_update(self) -> None:
        config = _tiny_config()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = train(config, run_directory=root / "legacy", execution_limit=1)
            adapter = _SummedLossCombiner()
            equivalent = train(
                config,
                run_directory=root / "equivalent",
                execution_limit=1,
                gradient_combiner=adapter,
            )
            first = torch.load(legacy.checkpoint_path, map_location="cpu", weights_only=False)
            second = torch.load(equivalent.checkpoint_path, map_location="cpu", weights_only=False)
            self.assertEqual(adapter.calls, 1)
            self.assertEqual(first["training_config_sha256"], second["training_config_sha256"])
            for name, tensor in first["model_state_dict"].items():
                self.assertTrue(torch.equal(tensor, second["model_state_dict"][name]), name)
            self.assertEqual(legacy.final_loss, equivalent.final_loss)

    def test_config_adapter_executes_one_real_pinn_update_reference_blind(self) -> None:
        config = _tiny_config()
        combiner = ConFIGGradientCombiner()
        with tempfile.TemporaryDirectory() as directory:
            outcome = train(
                config,
                run_directory=Path(directory) / "config",
                execution_limit=1,
                gradient_combiner=combiner,
            )
            checkpoint = torch.load(
                outcome.checkpoint_path, map_location="cpu", weights_only=False
            )
            manifest = json.loads(
                (outcome.run_directory / "manifest-final.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(combiner.calls, 1)
            self.assertEqual(checkpoint["update"], 1)
            self.assertEqual(manifest["status"], "DIAGNOSTIC_PREFIX")
            self.assertFalse(manifest["reference_fields_read"])
            self.assertEqual(
                manifest["gradient_combiner"]["method"],
                "STANDARD_CONFIG_EQUAL_DIRECTION_WEIGHTS",
            )

    def test_adam_defaults_and_fp64_are_unchanged(self) -> None:
        parameter = torch.nn.Parameter(torch.tensor(1.0, dtype=torch.float64))
        optimizer = torch.optim.Adam([parameter], lr=1.0e-3)
        self.assertEqual(optimizer.defaults["betas"], (0.9, 0.999))
        self.assertEqual(optimizer.defaults["eps"], 1.0e-8)
        self.assertEqual(optimizer.defaults["weight_decay"], 0)
        self.assertFalse(optimizer.defaults["amsgrad"])
        self.assertEqual(_tiny_config().dtype, "float64")

    def test_local_adjudication_uses_only_existing_hard_guard_boolean(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            summary = root / "summary.json"
            evaluation = root / "evaluation.json"
            output = root / "decision.json"
            summary.write_text(
                json.dumps({"status": "R1A_REFERENCE_BLIND_GPU_RUN_COMPLETE"}),
                encoding="utf-8",
            )
            evaluation.write_text(
                json.dumps(
                    {
                        "status": "EVALUATED_LOCAL_REFERENCE_ONLY",
                        "case_control": "FULL",
                        "hard_guards": {
                            "passed": False,
                            "failures": ["cycle_1_event_missing"],
                            "event_topology": {"cycles": []},
                        },
                        "metrics": {"primary": 1.0},
                    }
                ),
                encoding="utf-8",
            )
            result = adjudicate_local_nominal(
                run_summary_path=summary,
                evaluation_path=evaluation,
                output_path=output,
            )
            self.assertEqual(result["status"], "R1A_CONFIG_RAW_NO_COMPETENCE")
            self.assertFalse(result["stress_unseal_authorized"])
            self.assertFalse(result["next_research_execution_authorized"])


if __name__ == "__main__":
    unittest.main()
