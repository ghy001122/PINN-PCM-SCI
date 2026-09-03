from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy as np

from pinn_pcm_sci.phk_v23_lf0_evaluation import (
    A_ROLE,
    B_FINAL_ROLE,
    C_ROLE,
    GPU_LIFECYCLE_RETAINED_BY_USER,
    LF_DATA_ONLY_ROLE,
    LF_ONLY_ROLE,
    adjudicate_campaign,
    compare_b_to_comparator,
    compare_physics_batch_logs,
    interpolate_low_fidelity_arrays,
    load_decision_contract,
    reference_role_for_gpu_lifecycle,
    safe_error_ratio,
    write_c_trigger,
    write_strict_json,
    evaluate_lf0_campaign,
    _run_files,
)


def _evaluation(
    *,
    primary: float,
    phase_rms: float,
    competent: bool,
    temperature: float = 0.1,
    current: float = 0.1,
) -> dict:
    return {
        "status": "EVALUATED_LOCAL_REFERENCE_ONLY",
        "metrics": {
            "time_averaged_phase_region_symmetric_difference": primary,
            "phase_roi_continuous_rms": phase_rms,
            "temperature_roi_nrmse_by_0_45": temperature,
            "terminal_current_trace_nrmse": current,
        },
        "hard_guards": {
            "passed": competent,
            "finite_values": True,
            "phase_range": True,
            "event_topology": {
                "passed": competent,
                "cycles": [
                    {
                        "event_time": 0.2 if competent else None,
                        "peak_roi_fraction": 0.1 if competent else 0.0,
                        "peak_full_domain_fraction": 0.1 if competent else 0.0,
                        "peak_outside_roi_fraction": 0.01 if competent else 0.0,
                        "recovery_fraction": 0.8 if competent else 0.0,
                    },
                    {
                        "event_time": 1.4 if competent else None,
                        "peak_roi_fraction": 0.1 if competent else 0.0,
                        "peak_full_domain_fraction": 0.1 if competent else 0.0,
                        "peak_outside_roi_fraction": 0.01 if competent else 0.0,
                        "recovery_fraction": 0.8 if competent else 0.0,
                    },
                ],
            },
        },
    }


def _guards(*roles: str, passed: bool = True) -> dict[str, dict]:
    return {role: {"passed": passed} for role in roles}


class LF0DecisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.floors = {
            "phase_roi_continuous_rms": 0.004,
            "time_averaged_phase_region_symmetric_difference": 0.001,
        }

    def test_explicit_instance_retention_has_truthful_local_reference_role(self) -> None:
        self.assertEqual(
            reference_role_for_gpu_lifecycle(GPU_LIFECYCLE_RETAINED_BY_USER),
            (
                "NOMINAL_LOCAL_DEVELOPMENT_ONLY_AFTER_RECOVERY_"
                "INSTANCE_RETAINED_BY_EXPLICIT_USER_OVERRIDE"
            ),
        )
        with self.assertRaisesRegex(ValueError, "unsupported LF0 GPU lifecycle"):
            reference_role_for_gpu_lifecycle("RUNNING_TRAINING")

    def test_contract_freezes_reference_blind_full_objective_pool(self) -> None:
        contract = load_decision_contract()
        pool = contract["reference_blind_physics_diagnostic_pool"]
        self.assertEqual(pool["seed"], 17031)
        self.assertEqual(pool["active_windows"], 4)
        self.assertEqual(pool["interior_points"], 512)
        self.assertEqual(pool["boundary_points_total"], 128)
        self.assertEqual(pool["initial_points"], 128)
        self.assertFalse(pool["reference_or_low_fidelity_values_read"])
        self.assertEqual(
            pool["objective"],
            "NORMALIZED_PDE_PLUS_5_TIMES_BOUNDARY_PLUS_INITIAL",
        )

    def test_safe_error_ratio_has_frozen_zero_denominator_semantics(self) -> None:
        self.assertEqual(safe_error_ratio(0.0, 0.0), (1.0, True))
        self.assertEqual(safe_error_ratio(0.2, 0.0), (None, False))
        ratio, valid = safe_error_ratio(0.2, 0.4)
        self.assertTrue(valid)
        self.assertAlmostEqual(ratio or 0.0, 0.5)

    def test_noncompetent_comparator_uses_category_upgrade_and_floor(self) -> None:
        comparison = compare_b_to_comparator(
            _evaluation(primary=0.01, phase_rms=0.01, competent=True),
            _evaluation(primary=0.03, phase_rms=0.03, competent=False),
            component_floors=self.floors,
        )
        self.assertTrue(comparison["category_upgrade"])
        self.assertTrue(comparison["component_floor_improvement_passed"])
        self.assertTrue(comparison["increment_passed"])
        self.assertTrue(comparison["preservation_passed"])

    def test_competent_comparator_requires_all_three_ratio_gates(self) -> None:
        passed = compare_b_to_comparator(
            _evaluation(primary=0.09, phase_rms=0.09, competent=True),
            _evaluation(primary=0.10, phase_rms=0.10, competent=True),
            component_floors=self.floors,
        )
        self.assertTrue(passed["continuous_ratio_gate_passed"])
        self.assertTrue(passed["increment_passed"])
        failed = compare_b_to_comparator(
            _evaluation(primary=0.097, phase_rms=0.097, competent=True),
            _evaluation(primary=0.10, phase_rms=0.10, competent=True),
            component_floors=self.floors,
        )
        self.assertFalse(failed["geometric_mean_ratio_passed"])
        self.assertFalse(failed["increment_passed"])

    def test_all_seven_terminal_outcomes_and_two_interim_actions_are_exhaustive(self) -> None:
        noncompetent = _evaluation(primary=0.4, phase_rms=0.4, competent=False)
        competent = _evaluation(primary=0.01, phase_rms=0.01, competent=True)
        roles_ab = {
            A_ROLE: noncompetent,
            B_FINAL_ROLE: competent,
            LF_ONLY_ROLE: noncompetent,
            LF_DATA_ONLY_ROLE: noncompetent,
        }
        guards_ab = _guards(*roles_ab)
        batch = {"passed": True}
        objective = {"passed": True, "ratio": 0.5}

        engineering = adjudicate_campaign(
            cpu_qualification_passed=True,
            evaluations={},
            potential_guards={},
            component_floors=self.floors,
            engineering_blocked_reason="missing recovered file",
        )
        self.assertEqual(engineering["outcome"], "LF0_ENGINEERING_BLOCKED")

        cpu = adjudicate_campaign(
            cpu_qualification_passed=False,
            evaluations={},
            potential_guards={},
            component_floors=self.floors,
        )
        self.assertEqual(cpu["outcome"], "LF0_CPU_QUALIFICATION_BLOCKED")

        invalid = adjudicate_campaign(
            cpu_qualification_passed=True,
            evaluations={A_ROLE: noncompetent, LF_ONLY_ROLE: noncompetent},
            potential_guards=_guards(A_ROLE, LF_ONLY_ROLE, passed=False),
            component_floors=self.floors,
        )
        self.assertEqual(invalid["outcome"], "LF0_NUMERICAL_OR_IDENTITY_INVALID")

        after_a = adjudicate_campaign(
            cpu_qualification_passed=True,
            evaluations={A_ROLE: noncompetent, LF_ONLY_ROLE: noncompetent},
            potential_guards=_guards(A_ROLE, LF_ONLY_ROLE),
            component_floors=self.floors,
        )
        self.assertEqual(after_a["interim_status"], "LF0_A_VALID_RUN_B_REQUIRED")

        trigger = adjudicate_campaign(
            cpu_qualification_passed=True,
            evaluations=roles_ab,
            potential_guards=guards_ab,
            component_floors=self.floors,
            physics_batch_identity=batch,
            physics_objective_ratio=objective,
        )
        self.assertEqual(trigger["interim_status"], "LF0_C_TRIGGERED")
        self.assertTrue(trigger["c_trigger"]["b_competent"])

        provisional = adjudicate_campaign(
            cpu_qualification_passed=True,
            evaluations={**roles_ab, C_ROLE: noncompetent},
            potential_guards=_guards(*roles_ab, C_ROLE),
            component_floors=self.floors,
            physics_batch_identity=batch,
            physics_objective_ratio=objective,
        )
        self.assertEqual(
            provisional["outcome"], "LF0_WARMSTART_PINN_PROVISIONAL_METHOD_SIGNAL"
        )

        exact_top = adjudicate_campaign(
            cpu_qualification_passed=True,
            evaluations={
                A_ROLE: competent,
                B_FINAL_ROLE: noncompetent,
                LF_ONLY_ROLE: noncompetent,
                LF_DATA_ONLY_ROLE: noncompetent,
            },
            potential_guards=_guards(
                A_ROLE, B_FINAL_ROLE, LF_ONLY_ROLE, LF_DATA_ONLY_ROLE
            ),
            component_floors=self.floors,
            physics_batch_identity=batch,
            physics_objective_ratio={"passed": False, "ratio": 1.0},
        )
        self.assertEqual(
            exact_top["outcome"], "LF0_EXACT_TOP_SCRATCH_COMPETENCE_ONLY"
        )

        guided = adjudicate_campaign(
            cpu_qualification_passed=True,
            evaluations=roles_ab,
            potential_guards=guards_ab,
            component_floors={key: 1.0 for key in self.floors},
            physics_batch_identity=batch,
            physics_objective_ratio=objective,
        )
        self.assertEqual(
            guided["outcome"], "LF0_GUIDED_SOLVER_RESCUE_NO_METHOD_GAIN"
        )

        no_competence_roles = {
            A_ROLE: noncompetent,
            B_FINAL_ROLE: noncompetent,
            LF_ONLY_ROLE: noncompetent,
            LF_DATA_ONLY_ROLE: noncompetent,
        }
        no_competence = adjudicate_campaign(
            cpu_qualification_passed=True,
            evaluations=no_competence_roles,
            potential_guards=_guards(*no_competence_roles),
            component_floors=self.floors,
            physics_batch_identity=batch,
            physics_objective_ratio=objective,
        )
        self.assertEqual(
            no_competence["outcome"], "LF0_LOW_FIDELITY_ROUTE_NO_COMPETENCE"
        )


class LF0EvidenceTests(unittest.TestCase):
    def test_physics_hash_logs_compare_local_steps_and_c_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = [root / name for name in ("a.jsonl", "b.jsonl", "c.jsonl")]
            rows = [
                {
                    "global_step": step,
                    "physics_local_step": step,
                    "active_windows": (
                        1
                        if step <= 150
                        else (2 if step <= 350 else (3 if step <= 550 else 4))
                    ),
                    "batch_sha256": f"{step:064X}",
                }
                for step in range(1, 1201)
            ]
            c_rows = rows + [
                {
                    "global_step": step,
                    "physics_local_step": step,
                    "active_windows": 4,
                    "batch_sha256": f"{step:064X}",
                }
                for step in range(1201, 2001)
            ]
            for path, payload in zip(paths, (rows, rows, c_rows), strict=True):
                path.write_text(
                    "".join(json.dumps(row) + "\n" for row in payload),
                    encoding="utf-8",
                )
            report = compare_physics_batch_logs(paths[0], paths[1], paths[2])
            self.assertTrue(report["passed"])
            changed = list(rows)
            changed[1] = {**changed[1], "batch_sha256": "F" * 64}
            paths[1].write_text(
                "".join(json.dumps(row) + "\n" for row in changed),
                encoding="utf-8",
            )
            report = compare_physics_batch_logs(paths[0], paths[1])
            self.assertFalse(report["passed"])
            self.assertEqual(report["first_mismatch_physics_local_step"], 2)

    def test_low_fidelity_interpolation_maps_fields_and_scalar_traces(self) -> None:
        source_axes = (
            np.array([0.0, 1.0]),
            np.array([0.0, 1.0]),
            np.array([0.0, 1.0]),
        )
        target_axes = (
            np.array([0.0, 0.5, 1.0]),
            np.array([0.0, 0.5, 1.0]),
            np.array([0.0, 0.5, 1.0]),
        )
        t, z, x = np.meshgrid(*source_axes, indexing="ij")
        base = t + 2.0 * z + 3.0 * x
        result = interpolate_low_fidelity_arrays(
            source_axes=source_axes,
            target_axes=target_axes,
            fields={"potential": base, "temperature": 2 * base, "phase": 3 * base},
            scalar_traces={"top_current": np.array([0.0, 2.0]), "joule_power": np.array([1.0, 3.0])},
        )
        center = np.ravel_multi_index((1, 1), (3, 3))
        self.assertAlmostEqual(result["potential"][1, center], 3.0)
        np.testing.assert_allclose(result["top_current"], [0.0, 1.0, 2.0])
        np.testing.assert_allclose(result["joule_power"], [1.0, 2.0, 3.0])

    def test_trigger_binds_inputs_and_strict_json_rejects_nonfinite(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            inputs = {}
            for name in ("a", "b", "lf_data", "lf_only", "a_hash", "b_hash"):
                path = root / name
                path.write_bytes(name.encode("ascii"))
                inputs[name] = path
            target = root / "trigger.json"
            trigger = write_c_trigger(
                target,
                conditions={
                    "b_competent": True,
                    "b_provisional_increment_vs_all_comparators": True,
                    "pde_ratio_pass": True,
                    "preservation_pass": True,
                    "potential_validity_pass": True,
                },
                bound_inputs=inputs,
            )
            self.assertEqual(trigger["schema_id"], "phk-v23-lf0-c-trigger-v1")
            self.assertEqual(set(trigger["input_bindings"]), set(inputs))
            with self.assertRaises(ValueError):
                write_strict_json(root / "bad.json", {"bad": math.inf})

    def test_stress_is_rejected_before_contract_or_path_io(self) -> None:
        with mock.patch(
            "pinn_pcm_sci.phk_v23_lf0_evaluation.load_decision_contract"
        ) as load_contract:
            with self.assertRaises(PermissionError):
                evaluate_lf0_campaign(
                    output_directory=Path("not-opened"),
                    a_run_directory=Path("not-opened-a"),
                    case_control="INTERFACE_WIDTH_0_025",
                )
            load_contract.assert_not_called()

    def test_recovered_machine_invalid_run_reaches_campaign_adjudication(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            names = {
                "prediction_final": "prediction-final.npz",
                "checkpoint_final": "checkpoint-final.pt",
                "physics_batch_hashes": "physics-batch-hashes.jsonl",
                "prediction_lf_data_only": "prediction-lf-data-only-step-800.npz",
                "checkpoint_lf_data_only": "checkpoint-lf-data-only-step-800.pt",
            }
            artifacts = {}
            for key, name in names.items():
                path = root / name
                path.write_bytes(key.encode("ascii"))
                artifacts[key] = {
                    "path": name,
                    "size_bytes": path.stat().st_size,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
                }
            (root / "summary.json").write_text(
                json.dumps(
                    {
                        "status": "LF0_NUMERICAL_OR_IDENTITY_INVALID",
                        "run_arm": "B_MEDIUM_WARMSTART",
                        "prediction_reference_free": True,
                        "stress_fields_or_metrics_read": False,
                        "artifacts": artifacts,
                    }
                ),
                encoding="utf-8",
            )

            recovered = _run_files(root, arm="B_MEDIUM_WARMSTART")

            self.assertEqual(
                recovered["summary_payload"]["status"],
                "LF0_NUMERICAL_OR_IDENTITY_INVALID",
            )


if __name__ == "__main__":
    unittest.main()
