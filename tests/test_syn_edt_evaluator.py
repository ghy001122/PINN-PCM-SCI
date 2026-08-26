from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from pinn_pcm_sci.artifacts import CaseArtifact
from pinn_pcm_sci.syn_edt_evaluator import (
    COMPONENT_ORDER,
    SynEdtEvaluationArtifact,
    artifact_from_persisted_oracle,
    axisymmetric_cell_volumes,
    build_face_topology,
    build_floor_seal,
    component_normalizers,
    evaluate_syn_edt_files,
    hard_guard_report,
    read_floor_seal,
    six_component_errors,
    write_attempt_manifest,
    write_floor_seal,
)


ROOT = Path(__file__).resolve().parents[1]
S0_PATH = ROOT / "configs" / "goal_paper_one_shot_v1" / "s0_contract.json"
NUMERICAL_PATH = ROOT / "configs" / "goal_paper_one_shot_v1" / "s2_numerical_contract.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _contracts() -> tuple[dict[str, object], dict[str, object]]:
    s0 = json.loads(S0_PATH.read_text(encoding="utf-8"))
    numerical = json.loads(NUMERICAL_PATH.read_text(encoding="utf-8"))
    return s0["synthetic_physical_contract"], numerical


def _fixture_artifact(*, role: str = "ORACLE") -> SynEdtEvaluationArtifact:
    physical, numerical = _contracts()
    radial_faces_nm = (0.0, 25.0, 50.0, 80.0)
    axial_faces_nm = (0.0, 24.0, 27.0, 30.0)
    bounds = np.asarray(
        [
            (r0, r1, z0, z1)
            for r0, r1 in zip(radial_faces_nm[:-1], radial_faces_nm[1:])
            for z0, z1 in zip(axial_faces_nm[:-1], axial_faces_nm[1:])
        ],
        dtype=np.float64,
    ) * 1.0e-9
    volumes = axisymmetric_cell_volumes(bounds)
    field_time = np.asarray(
        [0.0, 0.10, 0.20, 0.46, 1.0, 1.10, 1.20, 1.46, 2.0],
        dtype=np.float64,
    )
    roi_top = int(
        np.flatnonzero(
            np.isclose(bounds[:, 0], 0.0, rtol=0.0, atol=1.0e-18)
            & np.isclose(bounds[:, 2], 27.0e-9, rtol=0.0, atol=1.0e-18)
            & np.isclose(bounds[:, 3], 30.0e-9, rtol=0.0, atol=1.0e-18)
        )[0]
    )
    donor = int(
        np.flatnonzero(
            np.isclose(bounds[:, 0], 50.0e-9, rtol=0.0, atol=1.0e-18)
            & np.isclose(bounds[:, 2], 0.0, rtol=0.0, atol=1.0e-18)
            & np.isclose(bounds[:, 3], 24.0e-9, rtol=0.0, atol=1.0e-18)
        )[0]
    )
    y = np.full((field_time.size, bounds.shape[0]), 0.5, dtype=np.float64)
    cycle_one_roi_depletion = np.asarray([0.0, 0.08, 0.15, 0.08, 0.03])
    cycle_two_roi_depletion = np.asarray([0.08, 0.15, 0.08, 0.03])
    y[:5, roi_top] = 0.5 - cycle_one_roi_depletion
    y[5:, roi_top] = y[4, roi_top] - cycle_two_roi_depletion
    y[:, donor] = 0.5 + (0.5 - y[:, roi_top]) * volumes[roi_top] / volumes[donor]

    circuit_time = np.asarray(
        [
            0.0, 0.02, 0.10, 0.32, 0.46, 0.48, 0.60, 0.78, 0.82,
            1.0, 1.02, 1.10, 1.32, 1.46, 1.48, 1.60, 1.78, 1.82, 2.0,
        ],
        dtype=np.float64,
    )
    voltage = np.asarray(
        [
            0.0, 0.18, 0.18, 0.18, 0.0, -0.15, -0.15, -0.15, 0.0,
            0.0, 0.18, 0.18, 0.18, 0.0, -0.15, -0.15, -0.15, 0.0, 0.0,
        ],
        dtype=np.float64,
    )
    current = np.asarray(
        [
            0.0, 1.00e-6, 0.99e-6, 0.98e-6, 0.0, -0.80e-6, -0.80e-6,
            -0.80e-6, 0.0, 0.0, 1.00e-6, 0.99e-6, 0.98e-6, 0.0,
            -0.80e-6, -0.80e-6, -0.80e-6, 0.0, 0.0,
        ],
        dtype=np.float64,
    )
    joule = voltage * current
    topology = build_face_topology(bounds)
    field_shape = (field_time.size, bounds.shape[0])
    return SynEdtEvaluationArtifact(
        role=role,
        case_id="NON_SCIENTIFIC_SYN_EDT_FIXTURE",
        physical_contract_id=str(physical["contract_id"]),
        s0_sha256=_sha256(S0_PATH),
        numerical_contract_sha256=_sha256(NUMERICAL_PATH),
        evidence_identity="NON_SCIENTIFIC_FIXTURE",
        method_id="SYN_EDT_FIXTURE_ORACLE" if role == "ORACLE" else "SYN_EDT_FIXTURE_METHOD",
        checkpoint_id="FIXTURE_CHECKPOINT_V1",
        cell_bounds_m=bounds,
        field_time_s=field_time,
        circuit_time_s=circuit_time,
        y=y,
        defect_flux_r_m2_s=np.full(field_shape, 1.0e18, dtype=np.float64),
        defect_flux_z_m2_s=np.full(field_shape, 2.0e18, dtype=np.float64),
        temperature_k=np.full(field_shape, 300.0, dtype=np.float64),
        boundary_normal_flux_m2_s=np.zeros(
            (field_time.size, topology.boundary_cells.size), dtype=np.float64
        ),
        voltage_v=voltage,
        current_top_a=current,
        current_bottom_a=-current,
        joule_power_w=joule,
        joule_power_dimensionless=joule
        / (
            float(numerical["endpoint_and_floor_contract"]["characteristic_current_a"])
            * float(physical["scales"]["thermal_voltage_v"])
        ),
        heat_sink_power_w=joule.copy(),
        non_scientific_fixture=True,
    )


class SynEdtEvaluatorTest(unittest.TestCase):
    def test_exact_axisymmetric_geometry_and_connectivity(self) -> None:
        artifact = _fixture_artifact()
        expected_total = 0.5 * (80.0e-9) ** 2 * 30.0e-9
        self.assertAlmostEqual(float(np.sum(artifact.volumes)), expected_total, places=36)
        self.assertEqual(artifact.topology.internal_face_cells.shape, (12, 2))
        self.assertEqual(artifact.topology.boundary_cells.shape, (12,))
        self.assertTrue(np.all(artifact.topology.boundary_areas_no_2pi_m2 >= 0.0))

    def test_identical_arrays_close_six_components_guards_and_floor(self) -> None:
        physical, numerical = _contracts()
        oracle = _fixture_artifact()
        prediction = replace(
            oracle,
            role="PREDICTION",
            method_id="SYN_EDT_FIXTURE_METHOD",
        )
        normalizers = component_normalizers(oracle, numerical)
        errors = six_component_errors(
            reference=oracle,
            candidate=prediction,
            physical=physical,
            numerical=numerical,
            normalizers=normalizers,
        )
        np.testing.assert_array_equal(np.asarray(errors), np.zeros((2, len(COMPONENT_ORDER))))
        self.assertTrue(
            hard_guard_report(
                prediction,
                physical=physical,
                numerical=numerical,
                normalizers=normalizers,
            )["passed"]
        )
        floor = build_floor_seal(
            reference=oracle,
            medium_space=oracle,
            medium_time=oracle,
            replay=oracle,
            physical=physical,
            numerical=numerical,
        )
        for cycle in floor["cycles"]:
            np.testing.assert_array_equal(cycle["component_floor_u"], np.full(6, 2.0e-6))
            self.assertAlmostEqual(cycle["tau_comp"], 2.0e-6)
        with tempfile.TemporaryDirectory() as temporary:
            floor_path = Path(temporary) / "floor.json"
            write_floor_seal(floor_path, floor)
            self.assertEqual(read_floor_seal(floor_path)["seal_sha256"], floor["seal_sha256"])

    def test_persisted_h5_report_pair_rehydrates_without_scale_constants(self) -> None:
        physical, numerical = _contracts()
        source = _fixture_artifact()
        concentration_scale = float(physical["scales"]["concentration_m_minus_3"])
        cell_order = np.lexsort((source.cell_bounds_m[:, 0], source.cell_bounds_m[:, 2]))
        ordered_bounds = source.cell_bounds_m[cell_order]
        centers = np.column_stack(
            (
                0.5 * (ordered_bounds[:, 0] + ordered_bounds[:, 1]),
                0.5 * (ordered_bounds[:, 2] + ordered_bounds[:, 3]),
            )
        )
        persisted = CaseArtifact(
            case_id=source.case_id,
            physical_contract_id=source.physical_contract_id,
            evidence_identity="NON_SCIENTIFIC_FIXTURE",
            nodes=centers,
            cells=np.arange(centers.shape[0], dtype=np.int64).reshape((-1, 1)),
            mesh_unit="m",
            field_time=source.field_time_s,
            circuit_time=source.circuit_time_s,
            time_unit="s",
            fields={
                "defect_fraction_y": source.y[:, cell_order],
                "electric_potential": np.zeros_like(source.y),
                "temperature": source.temperature_k[:, cell_order],
                "defect_flux_r": source.defect_flux_r_m2_s[:, cell_order]
                / concentration_scale,
                "defect_flux_z": source.defect_flux_z_m2_s[:, cell_order]
                / concentration_scale,
            },
            field_units={
                "defect_fraction_y": "1",
                "electric_potential": "V",
                "temperature": "K",
                "defect_flux_r": "m/s",
                "defect_flux_z": "m/s",
            },
            breakpoints=np.asarray([0.02, 0.32, 0.46, 0.48, 0.78, 0.82]),
            circuit={
                "voltage": source.voltage_v,
                "current_top": source.current_top_a,
                "current_bottom": source.current_bottom_a,
                "joule_power": source.joule_power_w,
                "heat_sink_power": source.heat_sink_power_w,
            },
            circuit_units={
                "voltage": "V",
                "current_top": "A",
                "current_bottom": "A",
                "joule_power": "W",
                "heat_sink_power": "W",
            },
        )
        report = {
            "case_id": source.case_id,
            "qualification_id": "FIXTURE_CHECKPOINT_V1",
            "physical_contract_id": source.physical_contract_id,
            "resolution": {"non_scientific_fixture": True},
            "active_r_faces_nm": [0.0, 25.0, 50.0, 80.0],
            "active_z_faces_nm": [0.0, 24.0, 27.0, 30.0],
            "field_time_s": source.field_time_s.tolist(),
            "guard_report": {"no_flux_residual_max": 0.0},
        }
        rehydrated = artifact_from_persisted_oracle(
            persisted,
            report,
            physical=physical,
            numerical=numerical,
            s0_sha256=source.s0_sha256,
            numerical_contract_sha256=source.numerical_contract_sha256,
        )
        np.testing.assert_array_equal(rehydrated.cell_bounds_m, ordered_bounds)
        np.testing.assert_allclose(
            rehydrated.defect_flux_r_m2_s,
            source.defect_flux_r_m2_s[:, cell_order],
            rtol=2.0e-16,
            atol=0.0,
        )
        np.testing.assert_array_equal(
            rehydrated.joule_power_dimensionless, source.joule_power_dimensionless
        )

    def test_disk_evaluator_zero_and_json_safe_positive_infinity(self) -> None:
        physical, numerical = _contracts()
        oracle = _fixture_artifact()
        prediction = replace(
            oracle,
            role="PREDICTION",
            method_id="SYN_EDT_FIXTURE_METHOD",
        )
        floor = build_floor_seal(
            reference=oracle,
            medium_space=oracle,
            medium_time=oracle,
            replay=oracle,
            physical=physical,
            numerical=numerical,
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            oracle_path = root / "oracle.npz"
            prediction_path = root / "prediction.npz"
            floor_path = root / "floor.json"
            split_path = root / "split.json"
            attempt_path = root / "attempt.json"
            metrics_path = root / "metrics.json"
            oracle.write(oracle_path)
            prediction.write(prediction_path)
            write_floor_seal(floor_path, floor)
            split_path.write_text(
                json.dumps(
                    {
                        "schema_version": "split-manifest-v1",
                        "split_id": "NON_SCIENTIFIC_FIXTURE_SPLIT",
                        "cases": {oracle.case_id: "NON_SCIENTIFIC_FIXTURE"},
                    }
                ),
                encoding="utf-8",
            )
            write_attempt_manifest(
                attempt_path,
                status="PREDICTION_AVAILABLE",
                case_id=oracle.case_id,
                physical_contract_id=oracle.physical_contract_id,
                method_id=prediction.method_id,
                checkpoint_id=prediction.checkpoint_id,
                prediction_path=prediction_path,
            )
            result = evaluate_syn_edt_files(
                attempt_path=attempt_path,
                oracle_path=oracle_path,
                split_manifest_path=split_path,
                s0_contract_path=S0_PATH,
                numerical_contract_path=NUMERICAL_PATH,
                floor_path=floor_path,
                output_path=metrics_path,
            )
            self.assertEqual(result["case_endpoint_z"], {"finite": True, "value": 0.0, "semantics": "FINITE"})
            self.assertTrue(result["hard_guards"]["passed"])

            write_attempt_manifest(
                attempt_path,
                status="OOM",
                case_id=oracle.case_id,
                physical_contract_id=oracle.physical_contract_id,
                method_id=prediction.method_id,
                checkpoint_id=prediction.checkpoint_id,
                failure_detail="NON_SCIENTIFIC_FIXTURE",
            )
            result = evaluate_syn_edt_files(
                attempt_path=attempt_path,
                oracle_path=oracle_path,
                split_manifest_path=split_path,
                s0_contract_path=S0_PATH,
                numerical_contract_path=NUMERICAL_PATH,
                floor_path=floor_path,
                output_path=metrics_path,
            )
            self.assertEqual(
                result["case_endpoint_z"],
                {"finite": False, "value": None, "semantics": "POSITIVE_INFINITY"},
            )
            self.assertNotIn("Infinity", metrics_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
