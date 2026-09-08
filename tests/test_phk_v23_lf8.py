from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest import mock

import numpy as np
import torch

import pinn_pcm_sci.phk_v23_lf8 as lf8
import pinn_pcm_sci.phk_v23_lf8_qualification as lf8q
from pinn_pcm_sci.ledger import ExperimentLedger, RunManifest


class _ThreeHead(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.encoders = torch.nn.ModuleDict(
            {name: torch.nn.Linear(2, 2, dtype=torch.float64) for name in ("potential", "temperature", "phase")}
        )
        self.heads = torch.nn.ModuleDict(
            {name: torch.nn.Linear(2, 1, dtype=torch.float64) for name in ("potential", "temperature", "phase")}
        )

    def forward(self, value: torch.Tensor) -> torch.Tensor:
        return sum(self.heads[name](self.encoders[name](value)).sum() for name in self.encoders)


class LF8RollbackSeamTests(unittest.TestCase):
    @staticmethod
    def _digest(value: object) -> str:
        digest = hashlib.sha256()
        lf8.update_digest(digest, value)
        return digest.hexdigest()

    def test_real_nonempty_adam_survives_two_reject_restore_cycles_without_alias(self) -> None:
        random.seed(17)
        np.random.seed(17)
        torch.manual_seed(17)
        model = _ThreeHead()
        optimizer = torch.optim.Adam(model.parameters(), lr=lf8.ETA0)
        warm = torch.tensor([[0.25, -0.75]], dtype=torch.float64)
        optimizer.zero_grad(set_to_none=True)
        model(warm).square().backward()
        optimizer.step()
        lf8.set_phase_trainable(model, False)
        snapshot = lf8.take_snapshot(model, optimizer, accepted_updates=25, learning_rate=lf8.ETA0)
        immutable = lf8.snapshot_digest(snapshot)

        for _ in range(2):
            restored = lf8.restore_snapshot(snapshot, model, optimizer)
            self.assertEqual(restored, snapshot.state_digest)
            self.assertEqual(lf8.snapshot_optimizer_aliases(snapshot, optimizer), [])
            for group in optimizer.param_groups:
                group["lr"] = lf8.LR_SCALES[-1]
            optimizer.zero_grad(set_to_none=True)
            model(torch.tensor([[0.5, 0.125]], dtype=torch.float64)).square().backward()
            optimizer.step()
            random.random(); np.random.random(); torch.rand(())
            self.assertEqual(lf8.snapshot_digest(snapshot), immutable)

        lf8.restore_snapshot(snapshot, model, optimizer)
        self.assertFalse(any(p.requires_grad for p in lf8.phase_parameters(model)))
        self.assertEqual(lf8.snapshot_digest(snapshot), immutable)


class LF8FilterPathSeamTests(unittest.TestCase):
    def test_frozen_ladder_and_valid_prefix_stall_are_distinct(self) -> None:
        self.assertEqual(lf8.LR_SCALES, (1.25e-4, 6.25e-5, 3.125e-5, 1.5625e-5, 7.8125e-6))
        self.assertEqual(lf8.available_scales(lf8.ETA0 / 4), lf8.LR_SCALES[2:])
        self.assertEqual(
            lf8.filter_path_disposition(accepted_updates=0, identity_valid=True),
            "NO_FEASIBLE_FIRST_BLOCK",
        )
        self.assertEqual(
            lf8.filter_path_disposition(accepted_updates=25, identity_valid=True),
            "FILTER_STALLED_WITH_VALID_PREFIX",
        )
        self.assertEqual(
            lf8.filter_path_disposition(accepted_updates=1200, identity_valid=True),
            "COMPLETE",
        )
        self.assertEqual(
            lf8.filter_path_disposition(accepted_updates=25, identity_valid=False),
            "POSTSTEP_IDENTITY_INVALID",
        )

    def test_schedule_replay_is_conditional_and_exact(self) -> None:
        accepted_schedule = [lf8.ETA0 / 16] * lf8.BLOCK_COUNT
        fstar = {
            "accepted_updates": 1200,
            "numerical_valid": True,
            "safety_gate": {"passed": True},
            "fixed_blind_physics": 4.0,
            "accepted_learning_rates": accepted_schedule,
        }
        self.assertTrue(lf8.schedule_control_required(fstar))
        self.assertEqual(lf8.replay_schedule(fstar), tuple(accepted_schedule))
        fstar["accepted_updates"] = 1175
        self.assertFalse(lf8.schedule_control_required(fstar))


class LF8QualificationManifestTests(unittest.TestCase):
    def test_manifest_is_complete_runmanifest_and_index_consistent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact = root / "docs/experiment/artifacts/lf8-cpu.json"
            raw = root / "outputs/runs/lf8-cpu/qualification.json"
            artifact.parent.mkdir(parents=True)
            raw.parent.mkdir(parents=True)
            artifact.write_text("{}\n", encoding="utf-8")
            raw.write_text("{}\n", encoding="utf-8")
            payload = {
                "created_at_utc": "2026-09-08T00:00:00+00:00",
                "input_bindings": {
                    "dev_r_checkpoint": {"sha256": lf8.EXPECTED_DEV_R_SHA256}
                },
            }
            with mock.patch.object(lf8q, "ROOT", root):
                manifest = lf8q.build_cpu_manifest(
                    payload, artifact_path=artifact, raw_report=raw
                )
            parsed = RunManifest(**manifest)
            self.assertEqual(parsed.to_dict(), manifest)
            self.assertEqual(parsed.index_row()["gate_outcome"], lf8q.STATUS)
            self.assertEqual(parsed.index_row()["method_id"], manifest["method_id"])
            ledger = ExperimentLedger(root / "ledger")
            ledger.record(parsed)
            ledger.validate()
            recorded = json.loads(
                (root / "ledger/index.jsonl").read_text(encoding="utf-8")
            )
            self.assertEqual(recorded, parsed.index_row())
            versioned = json.loads(
                (
                    Path(__file__).parents[1]
                    / "docs/experiment/manifests/20260908T050343Z-phk-v23-lf8-cpu-qualification.json"
                ).read_text(encoding="utf-8")
            )
            for key in (
                "experiment_group_id", "tier", "scientific_role", "gate",
                "execution_status", "numerical_validity", "gate_outcome",
                "route_disposition", "evidence_identity", "claim_status",
                "code_identity", "environment", "physical_contract_id",
                "split_id", "method_id", "case_id", "seed",
                "planned_budget", "actual_budget", "checkpoint",
                "evaluator_id", "failure_class", "replay_of", "supersedes",
                "schema_version", "command",
            ):
                self.assertEqual(manifest[key], versioned[key], key)


if __name__ == "__main__":
    unittest.main()
