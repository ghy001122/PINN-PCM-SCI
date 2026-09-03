from __future__ import annotations

import inspect
import json
import math
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock

import numpy as np
import torch

from pinn_pcm_sci.phk_benchmark import (
    PhkGrid,
    _phase_residual_and_jacobian,
    solve_electric_field,
)
from pinn_pcm_sci.phk_v21_benchmark import PhkV21CaseSpec, load_phk_v21_physical
from pinn_pcm_sci.phk_v22r_pinn import PhkV22RPhysics
from pinn_pcm_sci.phk_v23_c0_compatibility import (
    ALLOWED_OUTCOMES,
    CONTRACT_PATH,
    ROOT,
    _assert_execution_sources_match_commit,
    _native_joule_density_from_saved_potential,
    _field_laplacian,
    _roi_mask,
    _sha256_path,
    _window_mask,
    _write_json_exclusive,
    adjudicate,
    build_readiness_pool,
    event_mechanism,
    initial_phase_analytic,
    load_contract,
    native_masks,
    output_transform_admissibility,
    phase_components,
    prediction_transform_integrity,
    refuse_reference_role,
    run_c0,
)


class PhkV23C0CompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract()
        cls.physical = load_phk_v21_physical(
            program_path=ROOT / "configs/phk_v21/program_contract.json",
            object_path=ROOT / "configs/phk_v21/object_numerical_contract.json",
            legacy_program_path=ROOT / "configs/phk_v2/program_contract.json",
            legacy_object_path=ROOT / "configs/phk_v2/object_numerical_contract.json",
        )
        cls.case = PhkV21CaseSpec.nominal(cls.physical)
        cls.physics = PhkV22RPhysics.from_contract(cls.physical, cls.case)

    def test_contract_binds_physical_object_and_source_hashes(self) -> None:
        records = self.contract["inputs"]["contracts_and_implementations"]
        self.assertGreaterEqual(len(records), 10)
        for record in records:
            self.assertEqual(_sha256_path(ROOT / record["path"]), record["sha256"])
        self.assertEqual(
            self.contract["expected_base_commit"],
            "3f86fc40d49580da86b8687611326cd85d6d0169",
        )

    def test_nominal_carrier_and_e2_hashes_are_bound_without_stress_paths(self) -> None:
        nominal = self.contract["inputs"]["nominal_development_carriers"]
        self.assertEqual(
            set(nominal),
            {"medium", "fine", "extra_fine", "medium_half_dt", "fine_exact_replay"},
        )
        for record in nominal.values():
            self.assertEqual(_sha256_path(ROOT / record["path"]), record["sha256"])
            self.assertNotIn("stress", record["path"].lower())
        e2 = self.contract["inputs"]["e2_prediction"]
        self.assertEqual(_sha256_path(ROOT / e2["path"]), e2["sha256"])

    def test_fvm_laplacian_is_the_native_solver_operator(self) -> None:
        grid = PhkGrid.build(nx=12, nz=8, x_min=-1.0, x_max=1.0, z_min=0.0, z_max=1.0)
        phase = initial_phase_analytic(grid.cell_x, grid.cell_z, self.physics)["phase"]
        old = np.full(grid.cell_count, 0.02, dtype=np.float64)
        temperature = np.full(grid.cell_count, 0.45, dtype=np.float64)
        coefficients = {
            "mobility_cold": self.physics.mobility_cold,
            "mobility_hot": self.physics.mobility_hot,
            "mobility_width": self.physics.mobility_width,
            "theta_transition": self.physics.theta_transition,
            "barrier_scale": self.physics.barrier_scale,
            "thermal_drive": self.physics.thermal_drive,
        }
        residual, _ = _phase_residual_and_jacobian(
            phase,
            phase_old=old,
            temperature=temperature,
            grid=grid,
            dt=0.01,
            coefficients=coefficients,
            interface_width=self.physics.interface_width,
        )
        terms = phase_components(
            temperature=temperature,
            phase=phase,
            laplacian=np.asarray(grid.phase_laplacian @ phase),
            physics=self.physics,
        )
        expected = phase - old - 0.01 * terms["kinetic_rhs"]
        self.assertTrue(np.allclose(residual, expected, rtol=0.0, atol=1.0e-15))

    def test_strong_laplacian_stencil_is_exact_for_quadratic_interior_and_boundary(self) -> None:
        grid = PhkGrid.build(nx=12, nz=8, x_min=-1.0, x_max=1.0, z_min=0.0, z_max=1.0)
        field = 1.5 * grid.cell_x**2 - 0.75 * grid.cell_z**2 + 0.2 * grid.cell_x
        actual = _field_laplacian(field, grid)
        self.assertTrue(np.allclose(actual, 1.5, rtol=0.0, atol=2.0e-12))

    def test_analytic_initial_phase_laplacian_matches_finite_difference_inside(self) -> None:
        point_x = np.asarray([0.08], dtype=np.float64)
        point_z = np.asarray([0.19], dtype=np.float64)
        step = 1.0e-5
        center = initial_phase_analytic(point_x, point_z, self.physics)
        plus_x = initial_phase_analytic(point_x + step, point_z, self.physics)["phase"]
        minus_x = initial_phase_analytic(point_x - step, point_z, self.physics)["phase"]
        plus_z = initial_phase_analytic(point_x, point_z + step, self.physics)["phase"]
        minus_z = initial_phase_analytic(point_x, point_z - step, self.physics)["phase"]
        numerical = (plus_x - 2.0 * center["phase"] + minus_x) / step**2 + (
            plus_z - 2.0 * center["phase"] + minus_z
        ) / step**2
        self.assertTrue(np.allclose(numerical, center["laplacian"], rtol=3.0e-6, atol=1.0e-7))

    def test_phase_rhs_formula_has_frozen_sign(self) -> None:
        temperature = np.asarray([0.40, 0.55], dtype=np.float64)
        phase = np.asarray([0.02, 0.60], dtype=np.float64)
        laplacian = np.asarray([-1.0, 2.0], dtype=np.float64)
        terms = phase_components(
            temperature=temperature,
            phase=phase,
            laplacian=laplacian,
            physics=self.physics,
        )
        expected = terms["mobility"] * (
            self.physics.interface_width**2 * laplacian
            - terms["barrier_derivative"]
            - terms["thermal_tilt_derivative"]
        )
        self.assertTrue(np.array_equal(terms["kinetic_rhs"], expected))

    def test_readiness_pool_is_exact_deterministic_r1x_pool(self) -> None:
        torch.manual_seed(999)
        first = build_readiness_pool(self.physics)
        torch.manual_seed(13)
        second = build_readiness_pool(self.physics)
        self.assertTrue(np.array_equal(first, second))
        self.assertEqual(first.shape, (2048, 3))
        for index, bounds in enumerate(((0.0, 0.35), (0.35, 1.25), (1.25, 1.60), (1.60, 2.50))):
            block = first[index * 512 : (index + 1) * 512, 2]
            self.assertTrue(np.all(block >= bounds[0]))
            self.assertTrue(np.all(block < bounds[1]))

    def test_native_roi_window_and_boundary_masks_are_strict(self) -> None:
        grid = PhkGrid.build(nx=10, nz=8, x_min=-1.0, x_max=1.0, z_min=0.0, z_max=1.0)
        masks = native_masks(grid, layers=2)
        self.assertFalse(np.any(masks["boundary_strip"] & masks["strict_interior"]))
        self.assertTrue(np.all(masks["boundary_strip"] | masks["strict_interior"]))
        self.assertEqual(int(np.count_nonzero(masks["strict_interior"])), (10 - 4) * (8 - 4))
        roi = _roi_mask(grid)
        self.assertTrue(np.array_equal(roi, (np.abs(grid.cell_x) <= 0.55) & (grid.cell_z <= 0.55)))
        time = np.asarray([0.0, 0.349, 0.35, 1.249, 1.25, 1.6, 1.601])
        self.assertTrue(np.array_equal(_window_mask(time, "W1"), np.asarray([True, True, True, False, False, False, False])))
        self.assertTrue(np.array_equal(_window_mask(time, "W3"), np.asarray([False, False, False, False, True, True, False])))

    def test_native_joule_reconstruction_matches_solver(self) -> None:
        grid = PhkGrid.build(nx=8, nz=6, x_min=-1.0, x_max=1.0, z_min=0.0, z_max=1.0)
        conductivity = np.linspace(1.0, 1.3, grid.cell_count)
        native = solve_electric_field(
            grid=grid,
            conductivity=conductivity,
            applied_voltage=0.4,
            heater_width_fraction=0.35,
        )
        reconstructed = _native_joule_density_from_saved_potential(
            native.potential,
            conductivity,
            0.4,
            grid,
            0.35,
        )
        self.assertTrue(np.allclose(reconstructed, native.joule_density, rtol=1.0e-14, atol=1.0e-14))

    def _synthetic_result(self) -> SimpleNamespace:
        grid = PhkGrid.build(nx=8, nz=6, x_min=-1.0, x_max=1.0, z_min=0.0, z_max=1.0)
        time = np.asarray([0.0, 0.1, 0.2, 0.3, 0.4, 1.3, 1.4, 1.5, 1.6, 1.7, 2.5])
        shape = (time.size, grid.cell_count)
        phase0 = initial_phase_analytic(grid.cell_x, grid.cell_z, self.physics)["phase"]
        phase = np.broadcast_to(phase0, shape).copy()
        roi = (np.abs(grid.cell_x) <= 0.55) & (grid.cell_z <= 0.55)
        selected = np.flatnonzero(roi)[:2]
        phase[2, selected] = 0.55
        phase[3, selected] = 0.80
        phase[7, selected] = 0.55
        phase[8, selected] = 0.80
        temperature = np.full(shape, 0.55, dtype=np.float64)
        potential = np.zeros(shape, dtype=np.float64)
        return SimpleNamespace(
            grid=grid,
            time=time,
            phase=phase,
            temperature=temperature,
            potential=potential,
            phase_residual_history=np.full(30, 1.0e-12),
            resolution=SimpleNamespace(dt=0.1, save_every=1),
            case=SimpleNamespace(period=1.25),
        )

    def test_saved_time_derivative_is_never_labelled_exact_internal_step(self) -> None:
        result = event_mechanism(self._synthetic_result(), self.physics)
        self.assertEqual(len(result), 8)
        for record in result.values():
            self.assertIn("NOT_EXACT_INTERNAL_STEP", record["time_derivative_identity"])

    def test_output_envelope_identifies_hard_lift_nonrepresentability(self) -> None:
        output = output_transform_admissibility(self._synthetic_result(), self.physics)
        self.assertGreater(output["e2_audited_violation_fraction_max"], 0.0)
        for window in ("W1", "W3"):
            self.assertEqual(
                output["event_support"][window]["potential_legacy"]["violation_fraction"],
                0.0,
            )
        self.assertEqual(
            output["phase_hard_transform"]["strict_bound_violation_fraction"],
            0.0,
        )

    def test_e2_prediction_transform_self_check_enforces_hard_envelopes(self) -> None:
        grid = PhkGrid.build(nx=8, nz=6, x_min=-1.0, x_max=1.0, z_min=0.0, z_max=1.0)
        time = np.asarray([0.0, 0.1], dtype=np.float64)
        waveform = np.asarray([0.0, self.physics.waveform_amplitude], dtype=np.float64)[:, None]
        z_fraction = (grid.cell_z - grid.z_min) / (grid.z_max - grid.z_min)
        potential = waveform * z_fraction[None, :]
        startup = 1.0 - np.exp(-time / 0.35)
        temperature = 0.5 * 2.5 * startup[:, None] * (1.0 - z_fraction[None, :])
        phi0 = initial_phase_analytic(grid.cell_x, grid.cell_z, self.physics)["phase"]
        phase = np.broadcast_to(phi0, potential.shape).copy()
        valid = prediction_transform_integrity(
            time_axis=time,
            potential=potential,
            temperature=temperature,
            phase=phase,
            grid=grid,
            physics=self.physics,
        )
        self.assertEqual(valid["potential_maximum_absolute_excess"], 0.0)
        invalid = potential.copy()
        invalid[1, 0] -= 0.1
        with self.assertRaises(ValueError):
            prediction_transform_integrity(
                time_axis=time,
                potential=invalid,
                temperature=temperature,
                phase=phase,
                grid=grid,
                physics=self.physics,
            )

    def _ready(self, passed: bool = True) -> dict[str, Any]:
        value = 0.03 if passed else 0.0
        item = {
            "thermal_activation_fraction": value,
            "positive_cold_kinetic_growth_fraction": value,
            "joule_q95_roi": 1.0,
        }
        return {
            "dense": {"W1": dict(item), "W3": dict(item)},
            "sobol_pool": {"W1": dict(item), "W3": dict(item)},
            "dense_pass": passed,
            "sobol_pool_pass": passed,
        }

    def _output(self, fraction: float = 0.0, excess: float = 0.0) -> dict[str, float]:
        return {
            "trigger_confirmed": fraction >= 0.001 and excess >= 0.01,
            "trigger_normalized_evidence_ratio": min(
                fraction / 0.001,
                excess / 0.01,
            ),
        }

    def test_adjudicator_covers_all_five_machine_outcomes(self) -> None:
        compatible = {"sufficient": True, "maximum_residual_to_floor_ratio": 1.0, "minimum_native_continuous_rhs_sign_agreement": 0.99}
        mismatch = {"sufficient": True, "maximum_residual_to_floor_ratio": 20.0, "minimum_native_continuous_rhs_sign_agreement": 0.5}
        cases = (
            (self._ready(), compatible, self._output(), ALLOWED_OUTCOMES[0]),
            (self._ready(False), compatible, self._output(), ALLOWED_OUTCOMES[1]),
            (self._ready(), mismatch, self._output(), ALLOWED_OUTCOMES[2]),
            (self._ready(), compatible, self._output(0.5, 0.2), ALLOWED_OUTCOMES[3]),
            (self._ready(), {"sufficient": False}, self._output(), ALLOWED_OUTCOMES[4]),
        )
        for readiness, floor, output, expected in cases:
            with self.subTest(expected=expected):
                actual = adjudicate(
                    reference_event_pass=True,
                    reference_readiness=readiness,
                    compatibility=floor,
                    output=output,
                    contract=self.contract,
                )
                self.assertEqual(actual["primary"], expected)
                self.assertEqual(
                    actual["next_recommendation"],
                    self.contract["machine_adjudication"]["next_recommendation"][expected],
                )

    def test_multiple_pathologies_have_one_primary_and_at_most_one_secondary(self) -> None:
        actual = adjudicate(
            reference_event_pass=True,
            reference_readiness=self._ready(False),
            compatibility={"sufficient": True, "maximum_residual_to_floor_ratio": 20.0, "minimum_native_continuous_rhs_sign_agreement": 0.5},
            output=self._output(0.5, 0.2),
            contract=self.contract,
        )
        self.assertIn(actual["primary"], ALLOWED_OUTCOMES)
        self.assertIn(actual["secondary"], ALLOWED_OUTCOMES)
        self.assertNotEqual(actual["primary"], actual["secondary"])

    def test_nominal_only_reference_role_refuses_stress_before_io(self) -> None:
        with mock.patch.object(Path, "open", side_effect=AssertionError("I/O reached")) as opener:
            with self.assertRaises(PermissionError):
                refuse_reference_role("STRESS_GEOMETRY")
            opener.assert_not_called()

    def test_production_runner_refuses_stress_before_identity_or_carrier_io(self) -> None:
        import pinn_pcm_sci.phk_v23_c0_compatibility as module

        with mock.patch.object(module, "assert_input_identities") as identity:
            with self.assertRaises(PermissionError):
                run_c0(
                    output_path=Path("unused.json"),
                    run_id="unused-c0",
                    source_commit="0" * 40,
                    reference_role="STRESS_REFERENCE",
                )
            identity.assert_not_called()

    def test_dirty_execution_source_mismatch_fails_closed(self) -> None:
        source = "a" * 40
        with mock.patch(
            "pinn_pcm_sci.phk_v23_c0_compatibility._current_git_head",
            return_value=source,
        ), mock.patch(
            "pinn_pcm_sci.phk_v23_c0_compatibility._git_text",
            return_value="d" * 40,
        ), mock.patch(
            "pinn_pcm_sci.phk_v23_c0_compatibility._git_blob_identity",
            return_value=("b" * 40, "c" * 40),
        ):
            with self.assertRaisesRegex(ValueError, "direct child"):
                _assert_execution_sources_match_commit(
                    source,
                    expected_base_commit="e" * 40,
                )

        with mock.patch(
            "pinn_pcm_sci.phk_v23_c0_compatibility._current_git_head",
            return_value=source,
        ), mock.patch(
            "pinn_pcm_sci.phk_v23_c0_compatibility._git_text",
            return_value="e" * 40,
        ), mock.patch(
            "pinn_pcm_sci.phk_v23_c0_compatibility._git_blob_identity",
            return_value=("b" * 40, "c" * 40),
        ):
            with self.assertRaisesRegex(ValueError, "differs from commit"):
                _assert_execution_sources_match_commit(
                    source,
                    expected_base_commit="e" * 40,
                )

    def test_module_has_no_checkpoint_model_optimizer_or_gpu_surface(self) -> None:
        import pinn_pcm_sci.phk_v23_c0_compatibility as module

        source = inspect.getsource(module)
        for forbidden in (
            "torch.load",
            "PhkV22RModel(",
            "optimizer.step",
            "cuda:0",
            "import STRESS_REFERENCES",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn('choices=("cpu",)', source)
        self.assertIn('parser.add_argument("--source-commit", required=True)', source)
        self.assertFalse(self.contract["authorization"]["gpu_use"])
        self.assertFalse(self.contract["authorization"]["neural_checkpoint_load"])

    def test_strict_json_rejects_nonfinite_and_is_exclusive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.json"
            _write_json_exclusive(path, {"finite": 1.0})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"finite": 1.0})
            with self.assertRaises(FileExistsError):
                _write_json_exclusive(path, {"finite": 2.0})
            with self.assertRaises(ValueError):
                _write_json_exclusive(Path(directory) / "bad.json", {"bad": math.nan})

    def test_contract_forbids_reference_evaluator_and_stress_mutation(self) -> None:
        authorization = self.contract["authorization"]
        self.assertFalse(authorization["benchmark_reference_or_evaluator_modification"])
        self.assertFalse(authorization["stress_read"])
        self.assertEqual(
            self.contract["reference_boundary"]["stress_status"],
            "TWO_STRESS_REFERENCES_SEALED_UNREAD",
        )


if __name__ == "__main__":
    unittest.main()
