from __future__ import annotations

import hashlib
import inspect
import random
from pathlib import Path
import tempfile
import unittest

import numpy as np
import torch

import pinn_pcm_sci.phk_v23_lf7 as lf7
from pinn_pcm_sci.phk_v23_lf7 import (
    BLOCK_COUNT,
    BLOCK_SIZE,
    ETA0,
    LR_SCALES,
    MAX_FILTER_ATTEMPTED_UPDATES,
    P0_F,
    P0_S,
    P0_UPDATES,
    PHASE_FREEZE_STEPS,
    competence_gate,
    load_contracts,
    mechanism_outcome,
    restore_snapshot,
    take_snapshot,
)


def _audit(*, timing1: float = 0.004, timing2: float = 0.004) -> dict:
    metric = lambda timing: {
        "hard_recall": 0.95,
        "hard_precision": 0.90,
        "hard_active_mass_ratio": 1.0,
        "event_time_absolute_error": timing,
    }
    topology = {
        "peak_roi_fraction": 0.05,
        "peak_full_domain_fraction": 0.03,
        "peak_outside_roi_fraction": 0.0,
        "recovery_fraction": 1.0,
    }
    return {
        "all_values_finite": True,
        "phase_range": {"minimum": 0.0, "maximum": 0.99},
        "potential_maximum_principle": {
            "global": {
                "passed": True,
                "maximum_absolute_excess": 0.0,
                "violation_fraction": 0.0,
            }
        },
        "phase_maximum": 0.99,
        "two_cycle_events": True,
        "event_metrics": {"cycle_1": metric(timing1), "cycle_2": metric(timing2)},
        "event_topology_hard_guard": {"cycles": [dict(topology), dict(topology)]},
        "weighted_errors": {"potential": 1.0, "temperature": 1.0, "phase": 1.0},
        "topology_weighted_loss": 1.0,
    }


class _ToyThreeHead(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.encoders = torch.nn.ModuleDict(
            {name: torch.nn.Linear(1, 2, dtype=torch.float64) for name in ("potential", "temperature", "phase")}
        )
        self.heads = torch.nn.ModuleDict(
            {name: torch.nn.Linear(2, 1, dtype=torch.float64) for name in ("potential", "temperature", "phase")}
        )


class LF7FrozenIdentityTests(unittest.TestCase):
    def test_contract_and_schedule_are_exact(self) -> None:
        contracts = load_contracts()
        self.assertEqual(contracts["program"]["hard_limits"]["maximum_scientific_gpu_trajectories"], 2)
        self.assertEqual(contracts["program"]["hard_limits"]["campaign_maximum_attempted_optimizer_updates"], 3600)
        self.assertEqual((P0_UPDATES, PHASE_FREEZE_STEPS, BLOCK_SIZE, BLOCK_COUNT), (1200, 550, 25, 48))
        self.assertEqual(MAX_FILTER_ATTEMPTED_UPDATES, 2400)
        self.assertEqual(ETA0, 1.25e-4)
        self.assertEqual(LR_SCALES, (1.25e-4, 6.25e-5, 3.125e-5, 1.5625e-5, 7.8125e-6))
        self.assertEqual(len(contracts["decision"]["machine_outcomes_and_unique_next"]), 11)

    def test_runtime_has_no_sampler_and_physics_step_is_reused_on_retry(self) -> None:
        source = Path(inspect.getsourcefile(lf7) or "").read_text(encoding="utf-8")
        self.assertNotIn("SobolEngine", source)
        filter_source = inspect.getsource(lf7._run_filter)
        self.assertIn("physics_step = accepted + local + 1", filter_source)
        self.assertIn("ledger.physics_batch(physics_step", filter_source)
        self.assertNotIn("dataset.targets", inspect.getsource(lf7._train_one_step))
        self.assertNotIn("full_medium_audit", inspect.getsource(lf7._train_one_step))


class LF7GateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = _audit()

    def test_A_through_D_are_conjunctive_and_timing_levels_are_distinct(self) -> None:
        safety = competence_gate(
            _audit(timing1=0.010, timing2=0.005), self.baseline,
            physics_previous=4.0, physics_new=3.0,
        )
        strict = competence_gate(
            _audit(timing1=0.010, timing2=0.005), self.baseline,
            strict_timing=True,
        )
        self.assertTrue(safety["passed"])
        self.assertFalse(strict["passed"])
        self.assertIn("cycle_1_timing", strict["failed_checks"])

        failed = _audit()
        failed["event_metrics"]["cycle_2"]["hard_recall"] = 0.899
        gate = competence_gate(failed, self.baseline, physics_previous=4.0, physics_new=4.0)
        self.assertFalse(gate["passed"])
        self.assertIn("cycle_2_recall", gate["failed_checks"])
        self.assertIn("fixed_blind_strict_improvement", gate["failed_checks"])

    def test_mechanism_uses_dense_physics_ratio_and_filtered_acceptance(self) -> None:
        good = {
            "numerical_valid": True,
            "safety_gate": {"passed": True},
            "fixed_blind_ratio_to_DEV_R": 0.40,
            "disposition": "COMPLETE",
        }
        arms = {P0_S: dict(good), P0_F: {**good, "accepted_blocks": 48}}
        self.assertEqual(mechanism_outcome(arms), "SMALL_LR_SUFFICIENT_FILTER_NOT_LOAD_BEARING")
        arms[P0_S]["fixed_blind_ratio_to_DEV_R"] = 0.51
        self.assertEqual(mechanism_outcome(arms), "COMPETENCE_FILTER_LOAD_BEARING")
        arms[P0_F]["accepted_blocks"] = 0
        arms[P0_F]["disposition"] = "CFBR_STALLED"
        self.assertEqual(mechanism_outcome(arms), "FILTER_STALLED_NO_FEASIBLE_BLOCK_PATH")


class LF7RollbackTests(unittest.TestCase):
    @staticmethod
    def _payload_digest(value: object) -> str:
        digest = hashlib.sha256()
        lf7._update_digest(digest, value)
        return digest.hexdigest()

    def test_nonempty_adam_retry_does_not_mutate_snapshot_and_reject_rollback_is_exact(self) -> None:
        random.seed(17)
        np.random.seed(17)
        torch.manual_seed(17)
        model = _ToyThreeHead()
        optimizer = torch.optim.Adam(model.parameters(), lr=ETA0)
        loss = sum(parameter.square().sum() for parameter in model.parameters())
        loss.backward()
        optimizer.step()
        lf7._set_phase_trainable(model, False)
        snapshot = take_snapshot(model, optimizer, accepted_updates=525, learning_rate=ETA0)

        python_probe = random.Random()
        python_probe.setstate(snapshot.python_rng)
        expected_python = python_probe.random()
        numpy_probe = np.random.RandomState()
        numpy_probe.set_state(snapshot.numpy_rng)
        expected_numpy = float(numpy_probe.random_sample())
        torch_probe = torch.Generator()
        torch_probe.set_state(snapshot.torch_rng)
        expected_torch = float(torch.rand((), generator=torch_probe))
        model_snapshot_digest = self._payload_digest(snapshot.model_state)
        optimizer_snapshot_digest = self._payload_digest(snapshot.optimizer_state)
        rng_snapshot_digest = self._payload_digest(
            (snapshot.python_rng, snapshot.numpy_rng, snapshot.torch_rng, snapshot.cuda_rng)
        )

        # Match the filtered runtime: restore the accepted snapshot before the
        # next block, run Adam with non-empty moments, then reject and restore.
        self.assertEqual(restore_snapshot(snapshot, model, optimizer), snapshot.digest)
        live_optimizer_state = optimizer.state_dict()["state"]
        for state_id, saved_state in snapshot.optimizer_state["state"].items():
            for key, saved_value in saved_state.items():
                if torch.is_tensor(saved_value):
                    self.assertNotEqual(live_optimizer_state[state_id][key].data_ptr(), saved_value.data_ptr())
        for group in optimizer.param_groups:
            group["lr"] = ETA0 / 16.0
        optimizer.zero_grad(set_to_none=True)
        attempt_loss = sum(parameter.square().sum() for parameter in model.parameters() if parameter.requires_grad)
        attempt_loss.backward()
        optimizer.step()
        random.random()
        np.random.random()
        torch.rand(())

        self.assertEqual(self._payload_digest(snapshot.model_state), model_snapshot_digest)
        self.assertEqual(self._payload_digest(snapshot.optimizer_state), optimizer_snapshot_digest)
        self.assertEqual(
            self._payload_digest((snapshot.python_rng, snapshot.numpy_rng, snapshot.torch_rng, snapshot.cuda_rng)),
            rng_snapshot_digest,
        )

        restored = restore_snapshot(snapshot, model, optimizer)
        self.assertEqual(restored, snapshot.digest)
        self.assertEqual(optimizer.param_groups[0]["lr"], ETA0)
        self.assertFalse(any(parameter.requires_grad for parameter in lf7._phase_parameters(model)))
        self.assertEqual(random.random(), expected_python)
        self.assertEqual(float(np.random.random()), expected_numpy)
        self.assertEqual(float(torch.rand(())), expected_torch)
        for name, value in model.state_dict().items():
            self.assertTrue(torch.equal(value, snapshot.model_state[name]))

    def test_true_snapshot_optimizer_drift_is_rejected(self) -> None:
        random.seed(17)
        np.random.seed(17)
        torch.manual_seed(17)
        model = _ToyThreeHead()
        optimizer = torch.optim.Adam(model.parameters(), lr=ETA0)
        loss = sum(parameter.square().sum() for parameter in model.parameters())
        loss.backward()
        optimizer.step()
        snapshot = take_snapshot(model, optimizer, accepted_updates=25, learning_rate=ETA0)

        mutated = False
        for state in snapshot.optimizer_state["state"].values():
            for value in state.values():
                if torch.is_tensor(value):
                    value.add_(1.0)
                    mutated = True
                    break
            if mutated:
                break
        self.assertTrue(mutated)

        with self.assertRaisesRegex(RuntimeError, "rollback state identity drift"):
            restore_snapshot(snapshot, model, optimizer)

    def test_phase_boundary_is_accepted_step_550_then_same_optimizer_joint(self) -> None:
        small = inspect.getsource(lf7._run_small)
        filtered = inspect.getsource(lf7._run_filter)
        self.assertIn("step == PHASE_FREEZE_STEPS + 1", small)
        self.assertIn("next_step > PHASE_FREEZE_STEPS", filtered)
        self.assertNotIn("_make_optimizer(model)", filtered.split("while accepted < P0_UPDATES:", 1)[1])
        self.assertNotIn("restore_snapshot", small)

    def test_dyadic_retry_never_increases_accepted_learning_rate(self) -> None:
        self.assertEqual(lf7._available_scales(ETA0), LR_SCALES)
        self.assertEqual(lf7._available_scales(ETA0 / 4), LR_SCALES[2:])
        self.assertTrue(all(after < before for before, after in zip(LR_SCALES, LR_SCALES[1:])))


if __name__ == "__main__":
    unittest.main()
