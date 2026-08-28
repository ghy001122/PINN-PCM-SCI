from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy as np

from pinn_pcm_sci.phk_benchmark import PhkControl, PhkGrid, PhkGuardReport, PhkResolution
from pinn_pcm_sci.phk_v21_benchmark import (
    PhkV21CaseSpec,
    PhkV21OracleCase,
    PhkV21OracleResult,
    build_phk_v21_split_manifest,
    compare_phk_v21_results,
    evaluate_phk_v21_event,
    load_phk_v21_physical,
    load_phk_v21_split_manifest,
    phk_v21_resolution,
    read_phk_v21_result,
    run_phk_v21_manufactured_checks,
    write_phk_v21_split_manifest,
    write_phk_v21_result,
)
from pinn_pcm_sci.phk_v21_solver import (
    PhkV21PhaseAlgorithm,
    solve_phase_candidate,
)


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "configs" / "phk_v21" / "program_contract.json"
OBJECT = ROOT / "configs" / "phk_v21" / "object_numerical_contract.json"
LEGACY_PROGRAM = ROOT / "configs" / "phk_v2" / "program_contract.json"
LEGACY_OBJECT = ROOT / "configs" / "phk_v2" / "object_numerical_contract.json"


class PhkV21BenchmarkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.physical = load_phk_v21_physical(
            program_path=PROGRAM,
            object_path=OBJECT,
            legacy_program_path=LEGACY_PROGRAM,
            legacy_object_path=LEGACY_OBJECT,
        )

    def _zero_fixture(self) -> tuple[PhkV21CaseSpec, PhkResolution]:
        case = PhkV21CaseSpec.nominal(
            self.physical,
            control=PhkControl.ZERO_DRIVE,
        )
        resolution = PhkResolution.non_scientific_fixture(
            nx=8,
            nz=4,
            dt=0.01,
            time_end=0.02,
            save_every=1,
        )
        return case, resolution

    def _solve_zero_fixture(self) -> PhkV21OracleResult:
        case, resolution = self._zero_fixture()
        return PhkV21OracleCase(
            physical=self.physical,
            case=case,
            resolution=resolution,
            allow_non_scientific_fixture=True,
        ).solve()

    def test_loader_materializes_selected_object_without_touching_legacy(self) -> None:
        self.assertEqual(
            self.physical.contract_id,
            "PHK_V21_REPEATABLE_EVENT_2D_NUMERICAL_V1",
        )
        self.assertEqual(
            self.physical.payload["fields"]["phase_fraction"]["range_guard"],
            [0.0, 1.0],
        )
        self.assertEqual(self.physical.coordinates["time_period"], 1.25)
        self.assertEqual(self.physical.coefficients["volumetric_cooling"], 4.0)
        self.assertEqual(self.physical.coefficients["thermal_drive"], 6.0)
        self.assertEqual(set(self.physical.payload["resolutions"]), {
            "coarse",
            "medium",
            "fine",
            "extra_fine",
            "medium_half_dt",
        })

    def test_loader_fails_closed_on_inherited_byte_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tampered = Path(directory) / "legacy-object.json"
            tampered.write_bytes(LEGACY_OBJECT.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "legacy object byte identity mismatch"):
                load_phk_v21_physical(
                    program_path=PROGRAM,
                    object_path=OBJECT,
                    legacy_program_path=LEGACY_PROGRAM,
                    legacy_object_path=tampered,
                )

    def test_case_waveform_uses_its_complete_period_identity(self) -> None:
        case = PhkV21CaseSpec.nominal(self.physical)
        resolution = phk_v21_resolution(
            self.physical,
            "coarse",
            period=case.period,
        )
        oracle = PhkV21OracleCase(
            physical=self.physical,
            case=case,
            resolution=resolution,
        )
        self.assertEqual(oracle.waveform(0.0), 0.0)
        self.assertAlmostEqual(oracle.waveform(0.025), 0.36)
        self.assertAlmostEqual(oracle.waveform(0.05), 0.72)
        self.assertAlmostEqual(oracle.waveform(0.27), 0.72)
        self.assertAlmostEqual(oracle.waveform(0.31), 0.36)
        self.assertEqual(oracle.waveform(0.35), 0.0)
        self.assertAlmostEqual(oracle.waveform(1.25 + 0.025), 0.36)
        self.assertEqual(oracle.waveform(2.5), 0.0)

    def test_zero_drive_fixture_runs_selected_solver_without_clipping(self) -> None:
        result = self._solve_zero_fixture()
        guard = PhkGuardReport.from_result(result, physical=self.physical)
        self.assertTrue(guard.passed, guard.failures)
        self.assertEqual(
            result.phase_algorithm,
            PhkV21PhaseAlgorithm.LOGIT_NEWTON_ANALYTIC_JACOBIAN.value,
        )
        self.assertEqual(result.solver_statistics["time_steps_total"], 2)
        self.assertEqual(result.solver_statistics["output_clipping_count"], 0)
        self.assertGreaterEqual(float(np.min(result.phase)), 0.0)
        self.assertLessEqual(float(np.max(result.phase)), 1.0)

    def test_crosscheck_algorithm_is_fixed_for_every_phase_call(self) -> None:
        case, resolution = self._zero_fixture()
        with mock.patch(
            "pinn_pcm_sci.phk_v21_benchmark.solve_phase_candidate",
            wraps=solve_phase_candidate,
        ) as phase_solver:
            result = PhkV21OracleCase(
                physical=self.physical,
                case=case,
                resolution=resolution,
                phase_algorithm=PhkV21PhaseAlgorithm.PSEUDO_TRANSIENT_NEWTON,
                allow_non_scientific_fixture=True,
            ).solve()
        self.assertGreater(phase_solver.call_count, 0)
        self.assertTrue(
            all(
                call.kwargs["algorithm"]
                is PhkV21PhaseAlgorithm.PSEUDO_TRANSIENT_NEWTON
                for call in phase_solver.call_args_list
            )
        )
        self.assertEqual(
            result.phase_algorithm,
            PhkV21PhaseAlgorithm.PSEUDO_TRANSIENT_NEWTON.value,
        )

    def test_result_round_trip_and_identical_comparison(self) -> None:
        result = self._solve_zero_fixture()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.npz"
            write_phk_v21_result(path, result)
            loaded = read_phk_v21_result(path, physical=self.physical)
            self.assertTrue(np.array_equal(loaded.phase, result.phase))
            self.assertEqual(loaded.case, result.case)
            self.assertEqual(loaded.phase_algorithm, result.phase_algorithm)
            with self.assertRaises(FileExistsError):
                write_phk_v21_result(path, result)
        comparison = compare_phk_v21_results(
            result,
            result,
            physical=self.physical,
        )
        self.assertTrue(comparison.finite)
        self.assertTrue(np.array_equal(comparison.component_deltas, np.zeros(6)))

    def test_event_extraction_uses_case_period_not_overlay_period(self) -> None:
        case = replace(
            PhkV21CaseSpec.nominal(self.physical),
            period=1.20,
            case_id="NON_SCIENTIFIC_PERIOD_EVENT_FIXTURE",
        )
        case.validate(self.physical)
        grid = PhkGrid.build(
            nx=10,
            nz=6,
            x_min=-1.0,
            x_max=1.0,
            z_min=0.0,
            z_max=1.0,
        )
        time = np.linspace(0.0, 2.4, 241, dtype=np.float64)
        phase = np.full((time.size, grid.cell_count), 0.02, dtype=np.float64)
        roi = (
            (np.abs(grid.cell_x) <= 0.55)
            & (grid.cell_z >= 0.0)
            & (grid.cell_z <= 0.55)
        )
        for start in (0.20, 1.40):
            active = (time >= start) & (time <= start + 0.20)
            phase[np.ix_(active, roi)] = 0.80
        zeros_field = np.zeros_like(phase)
        zeros_trace = np.zeros(time.size, dtype=np.float64)
        histories = np.zeros(time.size - 1, dtype=np.float64)
        resolution = PhkResolution.non_scientific_fixture(
            nx=10,
            nz=6,
            dt=0.01,
            time_end=2.4,
            save_every=1,
        )
        result = PhkV21OracleResult(
            physical_contract_id=self.physical.contract_id,
            program_contract_sha256=self.physical.program.sha256,
            object_contract_sha256=self.physical.object.sha256,
            case=case,
            resolution=resolution,
            phase_algorithm=PhkV21PhaseAlgorithm.LOGIT_NEWTON_ANALYTIC_JACOBIAN.value,
            grid=grid,
            time=time,
            potential=zeros_field,
            temperature=zeros_field,
            phase=phase,
            top_current=zeros_trace,
            bottom_current=zeros_trace,
            joule_power=zeros_trace,
            current_balance_history=histories,
            thermal_residual_history=histories,
            phase_residual_history=histories,
            coupled_change_history=histories,
            linear_residual_history=histories,
            solver_statistics={},
            evidence_identity="NON_SCIENTIFIC_TEST_FIXTURE",
        )
        event = evaluate_phk_v21_event(result, physical=self.physical)
        self.assertTrue(event.passed, event.failures)
        self.assertEqual(len(event.cycles), 2)
        self.assertLess(event.cycles[0].event_time or 9.0, 0.20)
        self.assertLess(event.cycles[1].event_time or 9.0, 1.40)
        self.assertAlmostEqual(event.cycle_peak_relative_drift, 0.0)

    def test_manufactured_report_is_v21_labeled(self) -> None:
        report = run_phk_v21_manufactured_checks(self.physical)
        self.assertTrue(report["passed"])
        self.assertEqual(
            report["schema_id"], "phk-v21-manufactured-operator-report-v1"
        )
        self.assertEqual(
            report["program_contract_sha256"], self.physical.program.sha256
        )

    def test_split_is_exact_disjoint_and_outcome_blind(self) -> None:
        manifest = build_phk_v21_split_manifest(physical=self.physical)
        self.assertEqual(
            manifest["pool_counts"],
            {"D": 24, "I1": 12, "I2": 12, "F_A": 32, "F_O": 32, "R": 16},
        )
        self.assertEqual(len(manifest["cases"]), 128)
        self.assertEqual(
            len(manifest["candidate_universe"]["nominal_case_ids_sorted"]),
            243,
        )
        self.assertFalse(
            any("E2_STAGE" in case_id for case_id in manifest["cases"])
        )
        formal = [
            item for item in manifest["cases"].values() if item["pool"] == "F_O"
        ]
        held = {
            (item["held_out_factor"], item["held_out_value"])
            for item in formal
        }
        self.assertEqual(
            held,
            {
                ("heater_width_fraction", 0.30),
                ("heater_width_fraction", 0.40),
                ("interface_width", 0.035),
                ("interface_width", 0.045),
            },
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "split.json"
            write_phk_v21_split_manifest(path, manifest)
            loaded = load_phk_v21_split_manifest(
                path,
                physical=self.physical,
            )
            self.assertEqual(loaded, manifest)
            with self.assertRaises(FileExistsError):
                write_phk_v21_split_manifest(path, manifest)


if __name__ == "__main__":
    unittest.main()
