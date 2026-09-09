from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from pinn_pcm_sci import phk_v23_lf10_evaluation as evaluation


class LF10ThresholdRobustnessTests(unittest.TestCase):
    def _case(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        time = np.linspace(0.0, 2.0, 9)
        cell_x = np.array([-0.5, 0.0, 0.5, 0.9])
        cell_z = np.array([0.2, 0.2, 0.2, 0.2])
        reference = np.zeros((time.size, cell_x.size))
        reference[1:3, :2] = 0.8
        reference[5:7, :2] = 0.8
        prediction = reference.copy()
        return prediction, reference, time, cell_x, cell_z

    def test_threshold_grid_is_5_by_5_and_keeps_formal_threshold(self) -> None:
        prediction, reference, time, x, z = self._case()
        result = evaluation.threshold_grid_metrics(
            prediction, reference, time=time, cell_x=x, cell_z=z, period=1.0
        )
        self.assertEqual(result["grid_size"], 25)
        self.assertEqual(result["formal_machine_threshold"], {"phase": 0.5, "active_fraction": 0.02})
        self.assertTrue(all(row["both_events_exist"] for row in result["rows"]))
        self.assertTrue(all(row["minimum_recall"] == 1.0 for row in result["rows"]))
        self.assertTrue(all(row["mean_iou"] == 1.0 for row in result["rows"]))

    def test_comparison_counts_matched_grid_directions(self) -> None:
        rows_good = [{"minimum_recall": 0.9, "both_events_exist": True, "mean_symmetric_difference": 0.01} for _ in range(25)]
        rows_bad = [{"minimum_recall": 0.4, "both_events_exist": False, "mean_symmetric_difference": 0.2} for _ in range(25)]
        rows_direct = [{"minimum_recall": 1.0, "both_events_exist": True, "mean_symmetric_difference": 0.001} for _ in range(25)]
        result = evaluation.robustness_comparison({
            "LF6_DEV_R": {"rows": rows_good},
            "LF6_P0": {"rows": rows_bad},
            "DIRECT_LF_ONLY": {"rows": rows_direct},
            "LF3_T0": {"rows": rows_bad},
        })
        self.assertEqual(result["interface_support_same_sign"]["status"], "SKIPPED_MISSING_PREDICTION")
        self.assertEqual(result["physics_forgetting_persists"]["fraction"], 1.0)
        self.assertEqual(result["direct_lf_only_lead"]["fraction"], 1.0)

    def test_primary_outcomes_separate_path_extension_pareto_and_direct_value(self) -> None:
        self.assertEqual(
            evaluation.primary_terminal_outcome(
                feasible_direction_outcome="NO_EXTENDED_FEASIBLE_PATH_FOUND",
                safe_path_updates=25,
                within_architecture_pareto=False,
                direct_noninferiority=False,
            ),
            "LF10_FEASIBLE_DIRECTION_SCREEN_NEGATIVE_PAPER_STRENGTHENED",
        )
        self.assertEqual(
            evaluation.primary_terminal_outcome(
                feasible_direction_outcome="FEASIBLE_DIRECTION_PROJECTION_SUPPORTED",
                safe_path_updates=200,
                within_architecture_pareto=False,
                direct_noninferiority=False,
            ),
            "LF10_SAFE_PATH_EXTENDED_FULL_PARETO_NOT_REACHED",
        )
        self.assertEqual(
            evaluation.primary_terminal_outcome(
                feasible_direction_outcome="FEASIBLE_DIRECTION_PROJECTION_SUPPORTED",
                safe_path_updates=1200,
                within_architecture_pareto=True,
                direct_noninferiority=False,
            ),
            "LF10_WITHIN_ARCHITECTURE_PINN_PARETO_DIRECT_BASELINE_GAP",
        )
        self.assertEqual(
            evaluation.primary_terminal_outcome(
                feasible_direction_outcome="FEASIBLE_DIRECTION_PROJECTION_SUPPORTED",
                safe_path_updates=1200,
                within_architecture_pareto=True,
                direct_noninferiority=True,
            ),
            "LF10_PROVISIONAL_SINGLE_SEED_DENSE_SIGNAL",
        )

    def test_canonical_real_runner_summary_schema_is_consumed(self) -> None:
        run = {
            "schema_id": "phk-v23-lf10-reference-blind-run-summary-v1",
            "task_id": evaluation.TASK_ID,
            "direction_arms": {
                "CTRL": {"accepted_updates": 0, "attempted_updates": 25},
                "PROJ": {"accepted_updates": 200, "attempted_updates": 225},
            },
            "feasible_direction_outcome": "FEASIBLE_DIRECTION_PROJECTION_SUPPORTED",
            "direction_screen_decision": {
                "feasible_direction_outcome": "FEASIBLE_DIRECTION_PROJECTION_SUPPORTED",
                "selected_arm": "PROJ",
            },
            "selected_direction_arm": "PROJ",
            "full_refinement": {"executed": True, "accepted_updates": 1200, "attempted_updates": 1275},
            "interface_replication_outcome": "INTERFACE_EFFECT_STREAM_REPLICATED",
            "forgetting_replication_outcome": "PHYSICS_FORGETTING_STREAM_REPLICATED",
            "medium_audit_gradient_used_for_direction_only": True,
            "medium_audit_entered_physics_loss": False,
            "runtime_sampling_used": False,
            "fine_extra_lf_only_evaluator_stress_read": False,
        }
        view = evaluation.canonical_run_view(run)
        self.assertEqual(view["selected_arm"], "PROJ")
        self.assertEqual(view["full"]["accepted_updates"], 1200)
        self.assertEqual(view["interface_outcome"], "INTERFACE_EFFECT_STREAM_REPLICATED")
        self.assertEqual(
            evaluation._prediction_role("direction/proj/full-prediction.npz"),
            evaluation.SELECTED_FULL_ROLE,
        )
        self.assertEqual(
            evaluation._prediction_role("interface/seed-23/dev-m/prediction.npz"),
            "LF10_INTERFACE_23_DEV_M",
        )

    def test_shutdown_proof_requires_shutdown_before_local_adjudication(self) -> None:
        proof = {
            "schema_id": evaluation.SHUTDOWN_PROOF_SCHEMA,
            "task_id": evaluation.TASK_ID,
            "pre_shutdown": {
                "artifacts_recovered_and_hash_verified": True,
                "training_process_count": 0,
                "gpu_compute_process_count": 0,
            },
            "shutdown_requested": True,
            "post_shutdown": {
                "tcp_open": False,
                "verified_closed": True,
                "ssh_exit_code": 255,
                "ssh_terminal_evidence": "ssh: connect: Connection refused",
            },
            "ordering": {"shutdown_observation_preceded_local_adjudication": False},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "proof.json"
            path.write_text(json.dumps(proof), encoding="utf-8")
            with self.assertRaises(PermissionError):
                evaluation._verify_shutdown_proof(path)


if __name__ == "__main__":
    unittest.main()
