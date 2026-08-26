from __future__ import annotations

import copy
from dataclasses import asdict, replace
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from pinn_pcm_sci.syn_edt_2d import (
    SynEdtCaseSpec,
    SynEdtControl,
    SynEdtOracleCase,
    SynEdtPhysicalContract,
    SynEdtResolution,
    _OracleEngine,
    adjudicate_syn_edt_s2,
    build_syn_edt_case_manifest,
    canonical_syn_edt_case_identity,
    compare_syn_edt_artifacts,
    compare_syn_edt_resolutions,
    reconstruct_syn_edt_cell_flux_from_faces,
    split_syn_edt_face_joule_power,
    syn_edt_result_to_artifact,
)


ROOT = Path(__file__).resolve().parents[1]
S0 = ROOT / "configs" / "goal_paper_one_shot_v1" / "s0_contract.json"
S2 = ROOT / "configs" / "goal_paper_one_shot_v1" / "s2_numerical_contract.json"


class SynEdtContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = SynEdtPhysicalContract.from_s0(S0, S2)

    def test_frozen_contract_and_manifest_expose_all_qualification_cases(self) -> None:
        self.assertEqual(self.contract.physical_contract_id, "SYN_EDT_2D_V1_PHYSICS_V1")
        manifest = build_syn_edt_case_manifest(self.contract, S2)
        self.assertEqual(
            {entry["qualification_case"] for entry in manifest["cases"]},
            {"Q0", "QL", "QN", "QH"},
        )
        self.assertTrue(all(entry["pool"] == "Q" for entry in manifest["cases"]))

    def test_case_identity_excludes_resolution_but_includes_control(self) -> None:
        case = SynEdtCaseSpec.qualification("QN", self.contract)
        coarse = SynEdtResolution.from_levels("coarse", "coarse", self.contract)
        fine = SynEdtResolution.from_levels("fine", "fine", self.contract)
        full_coarse = canonical_syn_edt_case_identity(
            self.contract, case, SynEdtControl.FULL, coarse
        )
        full_fine = canonical_syn_edt_case_identity(
            self.contract, case, SynEdtControl.FULL, fine
        )
        direct_off = canonical_syn_edt_case_identity(
            self.contract,
            case,
            SynEdtControl.DIRECT_T_TO_TRANSPORT_OFF,
            fine,
        )
        self.assertEqual(full_coarse, full_fine)
        self.assertNotEqual(full_fine, direct_off)

    def test_characteristic_current_is_a_derived_fail_closed_invariant(self) -> None:
        payload = json.loads(S2.read_text(encoding="utf-8"))
        payload["endpoint_and_floor_contract"]["characteristic_current_a"] *= 1.01
        with tempfile.TemporaryDirectory() as temporary:
            altered = Path(temporary) / "s2.json"
            altered.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "characteristic current"):
                SynEdtPhysicalContract.from_s0(S0, altered)

    def test_two_material_face_joule_follows_half_face_resistance(self) -> None:
        left, right = split_syn_edt_face_joule_power(
            total_power=2.0,
            left_distance=0.5,
            right_distance=0.5,
            left_conductivity=1.0,
            right_conductivity=10_000.0,
        )
        self.assertAlmostEqual(left + right, 2.0, places=15)
        self.assertAlmostEqual(left / right, 10_000.0, places=6)
        self.assertGreater(left / 2.0, 0.9999)

    def test_cell_flux_reconstruction_includes_zero_flux_boundary_faces(self) -> None:
        radial, axial = reconstruct_syn_edt_cell_flux_from_faces(
            cell_bounds=np.asarray(
                [[0.0, 1.0, 0.0, 1.0], [1.0, 2.0, 0.0, 1.0]],
                dtype=np.float64,
            ),
            internal_face_left=np.asarray([0], dtype=np.int64),
            internal_face_right=np.asarray([1], dtype=np.int64),
            internal_face_area=np.asarray([1.0], dtype=np.float64),
            internal_face_orientation=("r",),
            internal_face_flux_density=np.asarray([3.0], dtype=np.float64),
        )
        np.testing.assert_allclose(radial, np.asarray([3.0, 1.0]))
        np.testing.assert_allclose(axial, np.zeros(2))


class SynEdtNonScientificFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = SynEdtPhysicalContract.from_s0(S0, S2)

    def _solve_fixture(self, spacing_nm: float):
        case = SynEdtCaseSpec.qualification("Q0", self.contract).as_fixture(
            total_duration_s=0.01
        )
        resolution = SynEdtResolution.fixture(
            active_h_max_nm=spacing_nm,
            corner_h_max_nm=min(10.0, spacing_nm),
            dt_max_s=0.005,
            saved_field_interval_s=0.005,
        )
        return SynEdtOracleCase(
            contract=self.contract,
            case=case,
            resolution=resolution,
            control=SynEdtControl.FULL,
        ).solve()

    def test_non_scientific_diagnostic_freezes_qn_first_step_newton_no_go(
        self,
    ) -> None:
        # NON_SCIENTIFIC_DIAGNOSTIC: this smallest ROI/annulus-resolving fixture
        # preserves the frozen numerical No-Go and must never be used as oracle
        # evidence. Its one timestep is the first QN ramp step (V_end=0.01125 V).
        case = replace(
            SynEdtCaseSpec.qualification("QN", self.contract).as_fixture(
                total_duration_s=0.00125
            ),
            active_radius_nm=50.0,
        )
        resolution = SynEdtResolution.fixture(
            active_h_max_nm=100.0,
            corner_h_max_nm=100.0,
            dt_max_s=0.00125,
            saved_field_interval_s=0.00125,
        )
        engine = _OracleEngine(
            self.contract,
            case,
            resolution,
            SynEdtControl.FULL,
        )
        y_old = np.full(
            engine.mesh.active_full.size,
            case.initial_y,
            dtype=np.float64,
        )
        theta = np.ones(engine.mesh.domain.size, dtype=np.float64)
        psi, joule, *_ = engine._electric(y_old, theta, 0.01125)
        theta_target, *_ = engine._thermal(joule)
        relaxation = float(engine.numerics["block_relaxation"])
        theta_relaxed = (
            (1.0 - relaxation) * theta + relaxation * theta_target
        )
        with self.assertRaisesRegex(
            RuntimeError,
            "^transport Newton exceeded its frozen iteration limit$",
        ):
            engine._transport_newton(
                y_old,
                y_old,
                psi,
                theta_relaxed,
                0.00125 / self.contract.time_s,
            )

    def test_zero_drive_fixture_is_exactly_conservative_and_artifact_valid(self) -> None:
        result = self._solve_fixture(20.0)
        self.assertTrue(result.guard_report.passed, result.guard_report.failures)
        self.assertFalse(result.event_report.applicable)
        np.testing.assert_allclose(result.y, 0.5, atol=2.0e-13, rtol=0.0)
        np.testing.assert_allclose(result.temperature_k, 300.0, atol=2.0e-10, rtol=0.0)
        np.testing.assert_allclose(result.current_top_a, 0.0, atol=1.0e-30, rtol=0.0)
        self.assertLessEqual(result.guard_report.relative_mass_drift_max, 1.0e-13)
        json.dumps(result.to_report_dict(), allow_nan=False)
        artifact = syn_edt_result_to_artifact(
            result,
            self.contract,
            qualification_status="NON_SCIENTIFIC_FIXTURE",
        )
        artifact.validate()
        self.assertEqual(artifact.fields["defect_fraction_y"].shape, result.y.shape)
        self.assertEqual(artifact.circuit_time.size, result.time_s.size)

    def test_identical_zero_drive_fixtures_compare_at_zero_error(self) -> None:
        coarse = self._solve_fixture(20.0)
        fine = self._solve_fixture(15.0)
        report = compare_syn_edt_resolutions(coarse, fine, self.contract)
        self.assertTrue(report.passed, report.failures)
        self.assertLessEqual(report.field_l2, 1.0e-12)
        self.assertEqual(report.event_magnitude_relative, 0.0)

    def test_persisted_comparison_thermal_payload_is_json_finite(self) -> None:
        coarse = self._solve_fixture(20.0)
        fine = self._solve_fixture(15.0)
        coarse_artifact = syn_edt_result_to_artifact(
            coarse,
            self.contract,
            qualification_status="NON_SCIENTIFIC_FIXTURE",
        )
        fine_artifact = syn_edt_result_to_artifact(
            fine,
            self.contract,
            qualification_status="NON_SCIENTIFIC_FIXTURE",
        )
        comparison = compare_syn_edt_artifacts(
            coarse_artifact,
            fine_artifact,
            coarse.to_report_dict(),
            fine.to_report_dict(),
            self.contract,
        )
        payload = asdict(comparison)
        json.dumps(payload, allow_nan=False)
        self.assertEqual(len(comparison.thermal_component_deltas_by_cycle), 2)
        self.assertEqual(
            len(comparison.thermal_current_rms_difference_a_by_cycle), 2
        )

    def test_persisted_convergence_uses_frozen_s2_field_scales(self) -> None:
        result = self._solve_fixture(20.0)
        reference = syn_edt_result_to_artifact(
            result,
            self.contract,
            qualification_status="NON_SCIENTIFIC_FIXTURE",
        )
        fields = dict(reference.fields)
        fields["electric_potential"] = fields["electric_potential"] + 0.18
        candidate = replace(reference, fields=fields)
        report = result.to_report_dict()
        baseline = compare_syn_edt_artifacts(
            candidate, reference, report, report, self.contract
        )
        numerical = copy.deepcopy(self.contract.numerical)
        numerical["field_convergence_metric"]["fixed_scales"][
            "electric_potential_v"
        ] = 0.36
        rescaled_contract = replace(self.contract, numerical=numerical)
        rescaled = compare_syn_edt_artifacts(
            candidate, reference, report, report, rescaled_contract
        )
        self.assertAlmostEqual(
            float(baseline.field_l2),
            2.0 * float(rescaled.field_l2),
            places=12,
        )

    def test_isothermal_driven_fixture_marks_heat_balance_not_applicable(self) -> None:
        case = SynEdtCaseSpec.qualification("QN", self.contract).as_fixture(
            total_duration_s=0.00005
        )
        resolution = SynEdtResolution.fixture(
            active_h_max_nm=20.0,
            corner_h_max_nm=10.0,
            dt_max_s=0.00005,
            saved_field_interval_s=0.00005,
        )
        result = SynEdtOracleCase(
            contract=self.contract,
            case=case,
            resolution=resolution,
            control=SynEdtControl.FULL_ISOTHERMAL_COUPLING_OFF,
        ).solve()
        self.assertFalse(result.guard_report.heat_balance_applicable)
        self.assertNotIn("heat", result.guard_report.failures)
        self.assertTrue(result.guard_report.port_sign_pass)
        np.testing.assert_allclose(result.temperature_k, 300.0, atol=1.0e-12, rtol=0.0)
        full = SynEdtOracleCase(
            contract=self.contract,
            case=case,
            resolution=resolution,
            control=SynEdtControl.FULL,
        ).solve()
        self.assertTrue(full.guard_report.heat_balance_applicable)
        self.assertTrue(full.guard_report.passed, full.guard_report.failures)
        self.assertTrue(full.guard_report.port_sign_pass)
        self.assertNotIn("mass", full.guard_report.failures)
        self.assertGreater(float(np.max(full.temperature_k)), 300.0)
        self.assertTrue(np.all(np.isfinite(full.y)))
        self.assertGreater(
            float(np.max(np.abs(full.y[-1] - full.y[0]))),
            1.0e-8,
        )
        self.assertGreaterEqual(float(np.min(full.y)), 1.0e-8)
        self.assertLessEqual(float(np.max(full.y)), 1.0 - 1.0e-8)
        self.assertLessEqual(full.guard_report.relative_mass_drift_max, 1.0e-10)
        statistics = full.solver_statistics
        self.assertLessEqual(
            statistics["final_transport_scaled_residual_max"],
            self.contract.numerical["nonlinear_scheme"][
                "block_scaled_residual_tolerance"
            ],
        )
        self.assertEqual(statistics["timesteps"], 1)
        self.assertGreaterEqual(
            statistics["block_iterations_total"],
            statistics["block_iterations_max"],
        )
        self.assertGreaterEqual(
            statistics["transport_newton_iterations_total"],
            statistics["transport_newton_iterations_max"],
        )
        self.assertEqual(
            statistics["electric_linear_solves_total"],
            1
            + statistics["block_iterations_total"]
            + statistics["final_consistency_evaluations_total"],
        )
        self.assertGreaterEqual(
            statistics["final_consistency_evaluations_total"],
            statistics["timesteps"],
        )
        self.assertEqual(
            statistics["thermal_linear_solves_total"],
            1 + statistics["block_iterations_total"],
        )
        self.assertEqual(
            statistics["transport_linear_solves_total"],
            statistics["transport_newton_iterations_total"],
        )
        self.assertEqual(
            statistics["linear_solves_total"],
            statistics["electric_linear_solves_total"]
            + statistics["thermal_linear_solves_total"]
            + statistics["transport_linear_solves_total"],
        )
        json.dumps(full.to_report_dict(), allow_nan=False)


class SynEdtS2AdjudicatorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = SynEdtPhysicalContract.from_s0(S0, S2)

    @staticmethod
    def _seal_hash(payload: dict) -> str:
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
        return hashlib.sha256(encoded).hexdigest().upper()

    def _evidence(self):
        ladder = self.contract.numerical["qualification_ladder"]
        reports = {}
        for row in ladder:
            intent = int(row["intent"])
            reports[intent] = {
                "physical_contract_id": self.contract.physical_contract_id,
                "case_id": "case-nominal" if intent == 6 else f"case-{intent}",
                "case_manifest": {
                    "s0_sha256": self.contract.s0_sha256,
                    "s2_numerical_sha256": self.contract.numerical_sha256,
                },
                "guard_report": {"passed": True},
                "event_report": {
                    "passed": intent == 6,
                    "event_time_s": [0.10, 1.10],
                    "peak_roi_depletion": [0.20, 0.21],
                },
            }
        # Exercise the explicitly frozen both-cycle censoring semantics.
        reports[10]["event_report"]["event_time_s"] = [None, None]

        delta = [[1.0e-5, 1.0e-5, None], [1.0e-5, 1.0e-5, None]]
        raw_current = [1.0e-11, 1.0e-11]

        def comparison(rows=delta, current=raw_current):
            return {
                "passed": True,
                "thermal_component_deltas_by_cycle": rows,
                "thermal_current_rms_difference_a_by_cycle": current,
                "thermal_effect_signed_by_cycle": {
                    "peak_depletion": [1.0e-5, 1.0e-5],
                    "event_time": [1.0e-5, 1.0e-5],
                    "current_trace_rms": current,
                },
            }

        comparisons = {
            "space_medium_fine": comparison(),
            "time_medium_fine": comparison(),
            "independent_process_replay": comparison(),
            "direct_transport_medium_fine": comparison(
                [[1.0e-5, None, None], [1.0e-5, None, None]]
            ),
            "isothermal_medium_fine": comparison(),
            "full_vs_direct_thermal_effect": comparison(
                [[0.10, None, None], [0.11, None, None]],
                [1.0e-7, 1.1e-7],
            ),
            "full_vs_isothermal_thermal_effect": comparison(
                [[0.10, 0.02, None], [0.11, 0.02, None]],
                [1.0e-7, 1.1e-7],
            ),
        }
        comparisons["full_vs_direct_thermal_effect"][
            "thermal_effect_signed_by_cycle"
        ] = {
            "peak_depletion": [0.10, 0.11],
            "event_time": [None, None],
            "current_trace_rms": [1.0e-7, 1.1e-7],
        }
        comparisons["full_vs_isothermal_thermal_effect"][
            "thermal_effect_signed_by_cycle"
        ] = {
            "peak_depletion": [0.10, 0.11],
            "event_time": [0.02, 0.02],
            "current_trace_rms": [1.0e-7, 1.1e-7],
        }

        endpoint = self.contract.numerical["endpoint_and_floor_contract"]
        width = len(endpoint["components_in_fixed_order"])
        source = float(endpoint["source_joint_uncertainty"])
        twice_solver = 2.0 * float(
            endpoint["declared_solver_tolerance_each_dimensionless_component"]
        )
        floor_value = 1.0e-5
        cycles = []
        for cycle in (1, 2):
            cycles.append(
                {
                    "cycle": cycle,
                    "space_delta": [floor_value] * width,
                    "time_delta": [floor_value] * width,
                    "replay_delta": [floor_value] * width,
                    "source_joint_uncertainty": [source] * width,
                    "twice_declared_solver_tolerance": [twice_solver] * width,
                    "component_floor_u": [floor_value] * width,
                    "tau_comp": floor_value,
                }
            )
        seal = {
            "schema_version": "syn-edt-floor-seal-v1",
            "physical_contract_id": self.contract.physical_contract_id,
            "s0_sha256": self.contract.s0_sha256,
            "numerical_contract_sha256": self.contract.numerical_sha256,
            "source_case_id": "case-nominal",
            "component_order": list(endpoint["components_in_fixed_order"]),
            "cycles": cycles,
            "normalizers_by_case": {
                "case-nominal": [
                    {"defect_flux": 1.0e18, "port_current": 1.0e-6},
                    {"defect_flux": 1.0e18, "port_current": 1.0e-6},
                ]
            },
            "sealed_before_neural_work": True,
        }
        seal["seal_sha256"] = self._seal_hash(seal)
        comparisons["endpoint_component_floors"] = seal
        return reports, comparisons

    def test_exact_floor_and_two_thermal_controls_can_adjudicate(self) -> None:
        reports, comparisons = self._evidence()
        result = adjudicate_syn_edt_s2(
            reports, comparisons, self.contract.numerical
        )
        json.dumps(result, allow_nan=False)
        self.assertTrue(result["adjudicated"], result)
        self.assertTrue(result["passed"], result)
        self.assertTrue(
            result["thermal_controls"]["direct"][
                "event_censored_both_cycles"
            ]
        )

    def test_missing_cross_control_record_remains_not_adjudicated(self) -> None:
        reports, comparisons = self._evidence()
        del comparisons["full_vs_isothermal_thermal_effect"]
        result = adjudicate_syn_edt_s2(
            reports, comparisons, self.contract.numerical
        )
        json.dumps(result, allow_nan=False)
        self.assertFalse(result["adjudicated"])
        self.assertFalse(result["passed"])


if __name__ == "__main__":
    unittest.main()
