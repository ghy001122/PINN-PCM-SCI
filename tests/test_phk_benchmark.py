from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import numpy as np

from pinn_pcm_sci.phk_benchmark import (
    PhkCaseSpec,
    PhkControl,
    PhkEventReport,
    PhkGrid,
    PhkOracleCase,
    PhkOracleResult,
    PhkPhysicalContract,
    PhkResolution,
    compare_phk_results,
    read_phk_result,
    run_phk_manufactured_checks,
    solve_electric_field,
    write_phk_result,
)


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "configs" / "phk_v2" / "program_contract.json"
OBJECT = ROOT / "configs" / "phk_v2" / "object_numerical_contract.json"


class PhkBenchmarkContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.physical = PhkPhysicalContract.from_files(
            program_path=PROGRAM,
            object_path=OBJECT,
        )

    def test_resolution_and_nominal_case_are_contract_derived(self) -> None:
        resolution = PhkResolution.from_contract(self.physical, "medium")
        case = PhkCaseSpec.qualification(self.physical, PhkControl.FULL)
        self.assertEqual((resolution.nx, resolution.nz), (80, 40))
        self.assertAlmostEqual(resolution.dt, 0.0025)
        self.assertAlmostEqual(case.heater_width_fraction, 0.35)
        self.assertAlmostEqual(case.waveform_amplitude, 0.75)
        self.assertEqual(case.control, PhkControl.FULL)

    def test_cartesian_grid_has_exact_cell_volumes_and_neumann_constant(self) -> None:
        grid = PhkGrid.build(nx=8, nz=4, x_min=-1.0, x_max=1.0, z_min=0.0, z_max=1.0)
        self.assertEqual(grid.cell_count, 32)
        self.assertAlmostEqual(float(np.sum(grid.cell_volumes)), 2.0)
        np.testing.assert_allclose(grid.phase_laplacian @ np.ones(grid.cell_count), 0.0)

    def test_uniform_full_electrode_electric_solution_is_linear_and_conservative(self) -> None:
        grid = PhkGrid.build(nx=10, nz=8, x_min=-1.0, x_max=1.0, z_min=0.0, z_max=1.0)
        sigma = np.ones(grid.cell_count)
        solved = solve_electric_field(
            grid=grid,
            conductivity=sigma,
            applied_voltage=0.75,
            heater_width_fraction=1.0,
        )
        expected = 0.75 * grid.cell_z
        np.testing.assert_allclose(solved.potential, expected, rtol=0.0, atol=2.0e-13)
        self.assertLess(solved.current_balance_relative, 2.0e-13)
        self.assertAlmostEqual(
            solved.joule_power_total,
            solved.top_current * 0.75,
            delta=2.0e-12,
        )

    def test_manufactured_operator_bundle_passes_without_scientific_field_claim(self) -> None:
        report = run_phk_manufactured_checks(self.physical)
        self.assertEqual(report["evidence_identity"], "NO_SCIENTIFIC_FIELD_RESULT")
        self.assertTrue(report["passed"])
        self.assertLess(report["checks"]["phase_jacobian_directional_relative_l2"], 2.0e-7)
        self.assertLess(report["checks"]["electric_linear_max_abs_error"], 5.0e-12)


class PhkBenchmarkFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        self.physical = PhkPhysicalContract.from_files(
            program_path=PROGRAM,
            object_path=OBJECT,
        )

    def test_explicit_non_scientific_zero_drive_fixture_is_finite(self) -> None:
        fixture = PhkResolution.non_scientific_fixture(
            nx=12,
            nz=6,
            dt=0.01,
            time_end=0.02,
            save_every=1,
        )
        result = PhkOracleCase(
            physical=self.physical,
            case=PhkCaseSpec.qualification(self.physical, PhkControl.ZERO_DRIVE),
            resolution=fixture,
            allow_non_scientific_fixture=True,
        ).solve()
        self.assertEqual(result.evidence_identity, "NON_SCIENTIFIC_TEST_FIXTURE")
        self.assertTrue(np.isfinite(result.phase).all())
        self.assertTrue(np.isfinite(result.temperature).all())
        np.testing.assert_allclose(result.top_current, 0.0, atol=1.0e-14)
        self.assertGreaterEqual(float(np.min(result.phase)), 1.0e-8)
        self.assertLessEqual(float(np.max(result.phase)), 0.99999999)

    def test_event_report_extracts_two_localized_recovering_cycles(self) -> None:
        grid = PhkGrid.build(nx=10, nz=5, x_min=-1.0, x_max=1.0, z_min=0.0, z_max=1.0)
        time = np.linspace(0.0, 2.0, 21)
        phase = np.full((time.size, grid.cell_count), 0.02)
        roi = (np.abs(grid.cell_x) <= 0.55) & (grid.cell_z <= 0.55)
        roi_cells = np.flatnonzero(roi)
        selected = roi_cells[: max(1, int(np.ceil(0.15 * roi_cells.size)))]
        for start in (0, 10):
            phase[start + 2 : start + 6, selected] = 0.8
            phase[start + 6, selected] = 0.35
        zeros = np.zeros_like(phase)
        result = PhkOracleResult.synthetic_for_test(
            physical=self.physical,
            grid=grid,
            time=time,
            potential=zeros,
            temperature=zeros,
            phase=phase,
        )
        report = PhkEventReport.from_result(result, physical=self.physical)
        self.assertEqual(len(report.cycles), 2)
        self.assertTrue(report.passed)
        self.assertTrue(all(cycle.event_time is not None for cycle in report.cycles))
        self.assertTrue(all(cycle.recovery_fraction >= 0.70 for cycle in report.cycles))

    def test_identical_result_comparison_is_exact_zero(self) -> None:
        grid = PhkGrid.build(nx=4, nz=2, x_min=-1.0, x_max=1.0, z_min=0.0, z_max=1.0)
        time = np.array([0.0, 1.0, 2.0])
        zeros = np.zeros((time.size, grid.cell_count))
        phase = np.full_like(zeros, 0.02)
        result = PhkOracleResult.synthetic_for_test(
            physical=self.physical,
            grid=grid,
            time=time,
            potential=zeros,
            temperature=zeros,
            phase=phase,
        )
        comparison = compare_phk_results(
            result,
            result,
            physical=self.physical,
        )
        self.assertTrue(comparison.finite)
        np.testing.assert_allclose(comparison.component_deltas, 0.0, atol=0.0)

    def test_result_npz_round_trip_binds_contract_grid_and_arrays(self) -> None:
        grid = PhkGrid.build(nx=4, nz=2, x_min=-1.0, x_max=1.0, z_min=0.0, z_max=1.0)
        time = np.array([0.0, 1.0, 2.0])
        zeros = np.zeros((time.size, grid.cell_count))
        result = PhkOracleResult.synthetic_for_test(
            physical=self.physical,
            grid=grid,
            time=time,
            potential=zeros,
            temperature=zeros,
            phase=np.full_like(zeros, 0.02),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "result.npz"
            write_phk_result(path, result)
            loaded = read_phk_result(path, physical=self.physical)
            np.testing.assert_array_equal(loaded.time, result.time)
            np.testing.assert_array_equal(loaded.phase, result.phase)
            self.assertEqual(loaded.object_contract_sha256, self.physical.object.sha256)
            with self.assertRaises(FileExistsError):
                write_phk_result(path, result)


if __name__ == "__main__":
    unittest.main()
