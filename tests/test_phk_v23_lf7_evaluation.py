from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pinn_pcm_sci.phk_v23_lf1_evaluation import LF_ONLY_ROLE
from pinn_pcm_sci.phk_v23_lf7 import P0_F, P0_S, load_contracts
from pinn_pcm_sci.phk_v23_lf7_evaluation import (
    DEV_R_ROLE,
    SHUTDOWN_PROOF_SCHEMA,
    _verify_shutdown_proof,
    adjudicate,
    matched_mechanism_outcome,
)


def _evaluation(*, competent: bool = True) -> dict:
    return {
        "hard_guards": {
            "finite_values": True,
            "phase_range": True,
            "passed": competent,
        },
        "metrics": {
            "time_averaged_phase_region_symmetric_difference": 0.01,
            "phase_roi_continuous_rms": 0.01,
            "temperature_roi_nrmse_by_0_45": 0.01,
            "terminal_current_trace_nrmse": 0.01,
        },
    }


def _arm(*, safety: bool = True, strict: bool = True, valid: bool = True, disposition: str = "COMPLETE") -> dict:
    return {
        "numerical_valid": valid,
        "safety_gate": {"passed": safety},
        "strict_gate": {"passed": strict},
        "accepted_updates": 1200,
        "attempted_updates": 1200,
        "accepted_blocks": 48,
        "disposition": disposition,
    }


def _case() -> tuple[dict, dict, dict, dict, dict]:
    run = {
        "arms": {P0_S: _arm(), P0_F: _arm()},
        "mechanism_outcome": "SMALL_LR_SUFFICIENT_FILTER_NOT_LOAD_BEARING",
    }
    evaluations = {
        DEV_R_ROLE: _evaluation(),
        LF_ONLY_ROLE: _evaluation(),
        P0_S: _evaluation(),
        P0_F: _evaluation(),
    }
    potential = {role: {"passed": True} for role in evaluations}
    comparisons = {}
    for role in (P0_S, P0_F):
        comparisons[f"{role}_vs_DEV_R"] = {
            "phase_noninferiority_passed": True,
            "preservation_passed": True,
        }
        comparisons[f"{role}_vs_LF_ONLY"] = {
            "phase_noninferiority_passed": True,
            "preservation_passed": True,
        }
    physics = {
        "arms": {
            P0_S: {"passed": True, "ratio_to_DEV_R": 0.4},
            P0_F: {"passed": True, "ratio_to_DEV_R": 0.3},
        }
    }
    return run, evaluations, potential, comparisons, physics


class LF7ShutdownBoundaryTests(unittest.TestCase):
    def _proof(self) -> dict:
        return {
            "schema_id": SHUTDOWN_PROOF_SCHEMA,
            "task_id": "PHK_V23_LF7_COMPETENCE_FILTERED_BLOCKWISE_BACKTRACKING_PHYSICS_REFINEMENT_PILOT_EXECUTE",
            "pre_shutdown": {
                "training_process_count": 0,
                "gpu_compute_process_count": 0,
                "artifacts_recovered_and_hash_verified": True,
            },
            "shutdown_requested": True,
            "post_shutdown": {
                "tcp_open": False,
                "ssh_exit_code": 255,
                "ssh_terminal_evidence": "ssh: connect: Connection refused",
                "verified_closed": True,
            },
            "ordering": {"shutdown_observation_preceded_local_adjudication": True},
        }

    def test_exact_shutdown_proof_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "proof.json"
            path.write_text(json.dumps(self._proof()), encoding="utf-8")
            self.assertEqual(_verify_shutdown_proof(path)["schema_id"], SHUTDOWN_PROOF_SCHEMA)
            broken = self._proof()
            broken["post_shutdown"]["verified_closed"] = False
            path.write_text(json.dumps(broken), encoding="utf-8")
            with self.assertRaisesRegex(PermissionError, "shutdown proof"):
                _verify_shutdown_proof(path)

    def test_failed_shutdown_stops_before_contract_or_local_reference_io(self) -> None:
        from pinn_pcm_sci.phk_v23_lf7_evaluation import evaluate_lf7_campaign

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "proof.json"
            path.write_text("{}", encoding="utf-8")
            with patch("pinn_pcm_sci.phk_v23_lf7_evaluation.load_contracts") as contracts:
                with self.assertRaises(PermissionError):
                    evaluate_lf7_campaign(
                        output_directory=Path(temporary) / "local",
                        run_directory=Path(temporary) / "run",
                        cpu_qualification_path=Path(temporary) / "cpu.json",
                        shutdown_proof_path=path,
                    )
            contracts.assert_not_called()


class LF7LayeredAdjudicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_contracts()["decision"]

    def adjudicate_case(self, run, evaluations, potential, comparisons, physics):
        return adjudicate(
            contract=self.contract,
            run=run,
            evaluations=evaluations,
            potential=potential,
            comparisons=comparisons,
            physics=physics,
        )

    def test_mechanism_uses_dense_gate_not_event_safety_alone(self) -> None:
        run, evaluations, potential, comparisons, physics = _case()
        physics["arms"][P0_S]["passed"] = False
        levels = {
            P0_S: {"endpoint_valid": True, "dense_safety_pareto": False},
            P0_F: {"endpoint_valid": True, "dense_safety_pareto": True},
        }
        self.assertEqual(matched_mechanism_outcome(run, levels), "COMPETENCE_FILTER_LOAD_BEARING")

    def test_identity_invalid_has_precedence_over_a_valid_other_arm(self) -> None:
        run, evaluations, potential, comparisons, physics = _case()
        run["arms"][P0_S]["numerical_valid"] = False
        evaluations.pop(P0_S)
        potential.pop(P0_S)
        result = self.adjudicate_case(run, evaluations, potential, comparisons, physics)
        self.assertEqual(result["outcome"], "LF7_MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID")
        self.assertIsNone(result["candidate"])

    def test_filter_stall_and_complete_no_path_are_distinct(self) -> None:
        run, evaluations, potential, comparisons, physics = _case()
        for role in (P0_S, P0_F):
            physics["arms"][role]["passed"] = False
        run["arms"][P0_F]["disposition"] = "CFBR_STALLED"
        result = self.adjudicate_case(run, evaluations, potential, comparisons, physics)
        self.assertEqual(result["outcome"], "LF7_FILTER_STALLED_NO_FEASIBLE_BLOCK_PATH")

        run["arms"][P0_F]["disposition"] = "COMPLETE"
        result = self.adjudicate_case(run, evaluations, potential, comparisons, physics)
        self.assertEqual(result["outcome"], "LF7_NO_PRESERVATION_COMPATIBLE_STRONG_FORM_PATH")

    def test_dense_without_local_is_only_safety_signal(self) -> None:
        run, evaluations, potential, comparisons, physics = _case()
        for role in (P0_S, P0_F):
            comparisons[f"{role}_vs_DEV_R"]["phase_noninferiority_passed"] = False
        result = self.adjudicate_case(run, evaluations, potential, comparisons, physics)
        self.assertEqual(result["outcome"], "LF7_SAFETY_PRESERVING_PHYSICS_SIGNAL_ONLY")
        self.assertTrue(result["safety_pareto_outcome"][P0_S])
        self.assertFalse(result["local_pinn_outcome"][P0_S])

    def test_local_pinn_and_direct_paper_value_are_separate(self) -> None:
        run, evaluations, potential, comparisons, physics = _case()
        for role in (P0_S, P0_F):
            comparisons[f"{role}_vs_LF_ONLY"]["phase_noninferiority_passed"] = False
        result = self.adjudicate_case(run, evaluations, potential, comparisons, physics)
        self.assertEqual(result["outcome"], "LF7_SINGLE_SEED_PINN_PILOT_DIRECT_BASELINE_GAP")
        self.assertIsNone(result["candidate"])
        self.assertTrue(result["local_pinn_outcome"][P0_S])

    def test_provisional_candidate_prefers_simple_control_if_both_pass(self) -> None:
        run, evaluations, potential, comparisons, physics = _case()
        result = self.adjudicate_case(run, evaluations, potential, comparisons, physics)
        self.assertEqual(result["outcome"], "LF7_PROVISIONAL_SINGLE_SEED_DENSE_SIGNAL")
        self.assertEqual(result["candidate"], P0_S)
        self.assertFalse(result["next_research_execution_authorized"])

    def test_outcome_map_is_exhaustive_unique_and_never_auto_authorizes(self) -> None:
        mapping = self.contract["machine_outcomes_and_unique_next"]
        self.assertEqual(len(mapping), 11)
        self.assertEqual(len(set(mapping)), 11)
        self.assertTrue(all(isinstance(value, str) and value for value in mapping.values()))
        self.assertTrue(self.contract["completion_does_not_authorize_next_research"])


if __name__ == "__main__":
    unittest.main()
