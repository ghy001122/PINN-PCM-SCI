from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from pinn_pcm_sci.phk_benchmark import PhkConvergenceReport
from pinn_pcm_sci.phk_v21_evaluator import (
    COMPONENT_ORDER,
    adjudicate_phk_v21_q,
    build_phk_v21_oracle_floor_seal,
    load_phk_v21_oracle_contract,
    validate_phk_v21_oracle_floor_seal,
    write_phk_v21_oracle_floor_seal,
)


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "configs" / "phk_v21" / "program_contract.json"
OBJECT = ROOT / "configs" / "phk_v21" / "object_numerical_contract.json"
SPLIT = ROOT / "configs" / "phk_v21" / "case_split_manifest.json"
ORACLE = ROOT / "configs" / "phk_v21" / "oracle_and_floor_contract.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def report(values: list[float]) -> PhkConvergenceReport:
    array = np.asarray(values, dtype=np.float64)
    return PhkConvergenceReport(
        component_order=COMPONENT_ORDER,
        component_deltas=array,
        finite=bool(np.isfinite(array).all()),
    )


class PhkV21EvaluatorTest(unittest.TestCase):
    def setUp(self) -> None:
        split = json.loads(SPLIT.read_text(encoding="utf-8"))
        self.contract = load_phk_v21_oracle_contract(
            ORACLE,
            program_sha256=sha(PROGRAM),
            object_sha256=sha(OBJECT),
            split_file_sha256=sha(SPLIT),
            split_manifest_sha256=split["manifest_sha256"],
            require_final=False,
        )

    def _seal(self) -> dict[str, object]:
        return build_phk_v21_oracle_floor_seal(
            oracle_contract=self.contract,
            medium_fine=report([0.10] * 6),
            fine_extra_fine=report([0.05] * 6),
            medium_half_dt=report([0.02] * 6),
            fine_replay=report([0.0] * 6),
            medium_solver_crosscheck=report([0.03] * 6),
            source_run_ids=[f"q-{index:02d}" for index in range(1, 15)],
        )

    def test_floor_is_componentwise_max_and_self_validating(self) -> None:
        seal = self._seal()
        self.assertTrue(seal["convergence_gate_passed"])
        self.assertEqual(seal["strict_contraction_count"], 6)
        self.assertEqual(seal["component_floors_U"], [0.05] * 6)
        validate_phk_v21_oracle_floor_seal(
            seal,
            oracle_contract=self.contract,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "floor.json"
            write_phk_v21_oracle_floor_seal(path, seal)
            self.assertTrue(path.is_file())
            with self.assertRaises(FileExistsError):
                write_phk_v21_oracle_floor_seal(path, seal)

    def test_floor_tamper_and_nonmonotonic_space_fail_closed(self) -> None:
        seal = self._seal()
        tampered = copy.deepcopy(seal)
        tampered["component_floors_U"][0] = 0.04
        with self.assertRaisesRegex(ValueError, "seal hash mismatch"):
            validate_phk_v21_oracle_floor_seal(
                tampered,
                oracle_contract=self.contract,
            )
        nonmonotonic = build_phk_v21_oracle_floor_seal(
            oracle_contract=self.contract,
            medium_fine=report([0.10] * 6),
            fine_extra_fine=report([0.05, 0.05, 0.11, 0.05, 0.11, 0.05]),
            medium_half_dt=report([0.02] * 6),
            fine_replay=report([0.0] * 6),
            medium_solver_crosscheck=report([0.03] * 6),
            source_run_ids=["fixture"],
        )
        self.assertFalse(nonmonotonic["convergence_gate_passed"])

    def test_positive_q_requires_every_independent_gate(self) -> None:
        seal = self._seal()
        positive = adjudicate_phk_v21_q(
            execution_status_by_intent={index: "COMPLETED" for index in range(1, 15)},
            guard_pass_by_intent={index: True for index in range(2, 15)},
            event_pass_by_intent={index: True for index in (3, 4, 5, 6, 7, 8, 14)},
            manufactured_pass=True,
            zero_drive_no_event=True,
            joule_off_no_event=True,
            replay_max_array_difference=0.0,
            replay_limit=1.0e-12,
            floor_seal=seal,
        )
        self.assertTrue(positive["oracle_qualified"])
        self.assertEqual(positive["method_route"], "CONTINUE_TO_BASELINE_REPLICATION")
        negative = adjudicate_phk_v21_q(
            execution_status_by_intent={index: "COMPLETED" for index in range(1, 15)},
            guard_pass_by_intent={index: True for index in range(2, 15)},
            event_pass_by_intent={index: True for index in (3, 4, 5, 6, 7, 8, 14)},
            manufactured_pass=True,
            zero_drive_no_event=True,
            joule_off_no_event=False,
            replay_max_array_difference=0.0,
            replay_limit=1.0e-12,
            floor_seal=seal,
        )
        self.assertFalse(negative["oracle_qualified"])
        self.assertIn("JOULE_OFF_FALSE_EVENT", negative["reasons"])

    def test_final_loader_rejects_pending_contract_state(self) -> None:
        split = json.loads(SPLIT.read_text(encoding="utf-8"))
        payload = json.loads(ORACLE.read_text(encoding="utf-8"))
        payload["status"] = "DRAFT_PRE_VOTING_IMPLEMENTATION_BINDINGS_PENDING"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pending.json"
            path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not final"):
                load_phk_v21_oracle_contract(
                    path,
                    program_sha256=sha(PROGRAM),
                    object_sha256=sha(OBJECT),
                    split_file_sha256=sha(SPLIT),
                    split_manifest_sha256=split["manifest_sha256"],
                    require_final=True,
                )


if __name__ == "__main__":
    unittest.main()
