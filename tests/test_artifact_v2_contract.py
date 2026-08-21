from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import h5py
import numpy as np

from pinn_pcm_sci.artifacts import ArtifactContractError, CaseArtifact, PredictionArtifact
from pinn_pcm_sci.evaluator import ArtifactValidationError, evaluate_files


FIELD_REGISTRY = {
    "eta": {
        "source_name": "eta",
        "physical_symbol": "eta",
        "quantity_label": "structural_order_parameter",
        "unit": "1",
        "association": "point",
        "temporal_kind": "dynamic",
        "qualification_status": "NON_SCIENTIFIC_FIXTURE",
    }
}


class ArtifactV2ContractTest(unittest.TestCase):
    def test_case_round_trip_preserves_independent_time_axes_units_and_registry(self) -> None:
        artifact = CaseArtifact(
            case_id="fixture-case-v2",
            physical_contract_id="fixture-contract-v2",
            evidence_identity="NON_SCIENTIFIC_FIXTURE",
            nodes=np.array([[0.0, 0.0], [1.0, 0.0]], dtype=np.float64),
            cells=np.array([[0, 1]], dtype=np.int64),
            mesh_unit="nm",
            field_time=np.array([0.0, 1.0], dtype=np.float64),
            circuit_time=np.array([0.0, 0.25, 1.0], dtype=np.float64),
            time_unit="ns",
            fields={"eta": np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.float64)},
            field_units={"eta": "1"},
            field_registry=FIELD_REGISTRY,
            breakpoints=np.array([0.5], dtype=np.float64),
            circuit={"voltage": np.array([0.0, 0.5, 1.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "case.h5"
            artifact.write(path)
            loaded = CaseArtifact.read(path)
            with h5py.File(path, "r") as handle:
                schema_version = str(handle.attrs["schema_version"])

        self.assertEqual(schema_version, "case-artifact-v2")
        self.assertEqual(loaded.mesh_unit, "nm")
        self.assertEqual(loaded.time_unit, "ns")
        np.testing.assert_array_equal(loaded.field_time, artifact.field_time)
        np.testing.assert_array_equal(loaded.circuit_time, artifact.circuit_time)
        self.assertEqual(loaded.field_registry, FIELD_REGISTRY)

    def test_prediction_round_trip_preserves_independent_time_axes(self) -> None:
        artifact = PredictionArtifact(
            case_id="fixture-case-v2",
            physical_contract_id="fixture-contract-v2",
            method_id="fixture-method",
            checkpoint_id="step-1",
            field_time=np.array([0.0, 1.0], dtype=np.float64),
            circuit_time=np.array([0.0, 0.5, 1.0], dtype=np.float64),
            time_unit="ns",
            mesh_identity="fixture-mesh-identity",
            fields={"eta": np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.float64)},
            field_units={"eta": "1"},
            field_registry=FIELD_REGISTRY,
            circuit={"voltage": np.array([0.0, 0.5, 1.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prediction.h5"
            artifact.write(path)
            loaded = PredictionArtifact.read(path)

        np.testing.assert_array_equal(loaded.field_time, artifact.field_time)
        np.testing.assert_array_equal(loaded.circuit_time, artifact.circuit_time)
        self.assertEqual(loaded.time_unit, "ns")
        self.assertEqual(loaded.field_registry, FIELD_REGISTRY)

    def test_v1_case_remains_readable_with_explicit_legacy_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy-case.h5"
            with h5py.File(path, "w") as handle:
                handle.attrs["schema_version"] = "case-artifact-v1"
                handle.attrs["case_id"] = "legacy-case"
                handle.attrs["physical_contract_id"] = "legacy-contract"
                handle.attrs["evidence_identity"] = "ENGINEERING_CONTROL_FLOW_ONLY"
                mesh = handle.create_group("mesh")
                mesh.create_dataset("nodes", data=np.array([[0.0, 0.0]], dtype=np.float64))
                mesh.create_dataset("cells", data=np.array([[0]], dtype=np.int64))
                handle.create_dataset("time", data=np.array([0.0], dtype=np.float64))
                protocol = handle.create_group("protocol")
                protocol.create_dataset("breakpoints", data=np.array([], dtype=np.float64))
                fields = handle.create_group("fields")
                eta = fields.create_dataset("eta", data=np.array([[0.0]], dtype=np.float64))
                eta.attrs["unit"] = "1"
                circuit = handle.create_group("circuit")
                voltage = circuit.create_dataset("voltage", data=np.array([0.0], dtype=np.float64))
                voltage.attrs["unit"] = "V"

            loaded = CaseArtifact.read(path)

        self.assertEqual(loaded.mesh_unit, "UNSPECIFIED_LEGACY_V1")
        self.assertEqual(loaded.time_unit, "UNSPECIFIED_LEGACY_V1")
        np.testing.assert_array_equal(loaded.field_time, loaded.circuit_time)
        self.assertEqual(
            loaded.field_registry["eta"]["qualification_status"],
            "LEGACY_V1_UNSPECIFIED",
        )

    def test_unknown_schema_version_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "unknown.h5"
            with h5py.File(path, "w") as handle:
                handle.attrs["schema_version"] = "case-artifact-v999"

            with self.assertRaisesRegex(ValueError, "unsupported case artifact schema"):
                CaseArtifact.read(path)

    def test_evaluator_uses_both_time_axes_and_their_unit(self) -> None:
        oracle = CaseArtifact(
            case_id="fixture-case-v2",
            physical_contract_id="fixture-contract-v2",
            evidence_identity="NON_SCIENTIFIC_FIXTURE",
            nodes=np.array([[0.0, 0.0]], dtype=np.float64),
            cells=np.array([[0]], dtype=np.int64),
            mesh_unit="nm",
            field_time=np.array([0.0, 1.0], dtype=np.float64),
            circuit_time=np.array([0.0, 0.25, 1.0], dtype=np.float64),
            time_unit="ns",
            fields={"eta": np.array([[0.0], [1.0]], dtype=np.float64)},
            field_units={"eta": "1"},
            field_registry=FIELD_REGISTRY,
            breakpoints=np.array([], dtype=np.float64),
            circuit={"voltage": np.array([0.0, 0.5, 1.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )

        def prediction(*, circuit_time: np.ndarray, time_unit: str) -> PredictionArtifact:
            return PredictionArtifact(
                case_id=oracle.case_id,
                physical_contract_id=oracle.physical_contract_id,
                method_id="fixture-method",
                checkpoint_id="step-1",
                field_time=oracle.field_time.copy(),
                circuit_time=circuit_time,
                time_unit=time_unit,
                mesh_identity=oracle.mesh_identity,
                fields={"eta": oracle.fields["eta"].copy()},
                field_units={"eta": "1"},
                field_registry=FIELD_REGISTRY,
                circuit={"voltage": oracle.circuit["voltage"].copy()},
                circuit_units={"voltage": "V"},
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            oracle_path = root / "oracle.h5"
            prediction_path = root / "prediction.h5"
            split_path = root / "split.json"
            spec_path = root / "spec.json"
            oracle.write(oracle_path)
            split_path.write_text(
                '{"schema_version":"split-manifest-v1","split_id":"fixture-split",'
                '"cases":{"fixture-case-v2":"fixture"}}',
                encoding="utf-8",
            )
            spec_path.write_text(
                '{"schema_version":"metric-spec-v1","evaluator_id":"fixture-evaluator",'
                '"structure_field":"eta",'
                '"structure_threshold":0.5,"cycle_windows":[[0.0,1.0]],'
                '"device_channel":"voltage","device_scale":1.0}',
                encoding="utf-8",
            )

            prediction(
                circuit_time=np.array([0.0, 0.5, 1.0], dtype=np.float64),
                time_unit="ns",
            ).write(prediction_path)
            with self.assertRaisesRegex(ArtifactValidationError, "circuit time grids"):
                evaluate_files(
                    prediction_path=prediction_path,
                    oracle_path=oracle_path,
                    split_manifest_path=split_path,
                    metric_spec_path=spec_path,
                    output_path=root / "metrics.json",
                )

            prediction(
                circuit_time=oracle.circuit_time.copy(),
                time_unit="s",
            ).write(prediction_path)
            with self.assertRaisesRegex(ArtifactValidationError, "time unit"):
                evaluate_files(
                    prediction_path=prediction_path,
                    oracle_path=oracle_path,
                    split_manifest_path=split_path,
                    metric_spec_path=spec_path,
                    output_path=root / "metrics.json",
                )

    def test_case_contract_rejects_nonmonotone_time_and_invalid_connectivity(self) -> None:
        common = {
            "case_id": "invalid-case",
            "physical_contract_id": "fixture-contract-v2",
            "evidence_identity": "NON_SCIENTIFIC_FIXTURE",
            "nodes": np.array([[0.0, 0.0]], dtype=np.float64),
            "mesh_unit": "nm",
            "circuit_time": np.array([0.0], dtype=np.float64),
            "time_unit": "ns",
            "fields": {"eta": np.array([[0.0], [1.0]], dtype=np.float64)},
            "field_units": {"eta": "1"},
            "field_registry": FIELD_REGISTRY,
            "breakpoints": np.array([], dtype=np.float64),
            "circuit": {"voltage": np.array([0.0], dtype=np.float64)},
            "circuit_units": {"voltage": "V"},
        }
        with self.assertRaisesRegex(ArtifactContractError, "field_time"):
            CaseArtifact(
                **common,
                cells=np.array([[0]], dtype=np.int64),
                field_time=np.array([1.0, 0.0], dtype=np.float64),
            )
        with self.assertRaisesRegex(ArtifactContractError, "cell index"):
            CaseArtifact(
                **common,
                cells=np.array([[1]], dtype=np.int64),
                field_time=np.array([0.0, 1.0], dtype=np.float64),
            )

    def test_evaluator_rejects_prediction_for_a_different_mesh_identity(self) -> None:
        oracle = CaseArtifact(
            case_id="fixture-case-v2",
            physical_contract_id="fixture-contract-v2",
            evidence_identity="NON_SCIENTIFIC_FIXTURE",
            nodes=np.array([[0.0, 0.0]], dtype=np.float64),
            cells=np.array([[0]], dtype=np.int64),
            mesh_unit="nm",
            field_time=np.array([0.0], dtype=np.float64),
            circuit_time=np.array([0.0], dtype=np.float64),
            time_unit="ns",
            fields={"eta": np.array([[0.0]], dtype=np.float64)},
            field_units={"eta": "1"},
            field_registry=FIELD_REGISTRY,
            breakpoints=np.array([], dtype=np.float64),
            circuit={"voltage": np.array([0.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )
        prediction = PredictionArtifact(
            case_id=oracle.case_id,
            physical_contract_id=oracle.physical_contract_id,
            method_id="fixture-method",
            checkpoint_id="step-1",
            field_time=oracle.field_time.copy(),
            circuit_time=oracle.circuit_time.copy(),
            time_unit="ns",
            mesh_identity="different-mesh",
            fields={"eta": oracle.fields["eta"].copy()},
            field_units={"eta": "1"},
            field_registry=FIELD_REGISTRY,
            circuit={"voltage": oracle.circuit["voltage"].copy()},
            circuit_units={"voltage": "V"},
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            oracle_path = root / "oracle.h5"
            prediction_path = root / "prediction.h5"
            split_path = root / "split.json"
            spec_path = root / "spec.json"
            oracle.write(oracle_path)
            prediction.write(prediction_path)
            split_path.write_text(
                '{"schema_version":"split-manifest-v1","split_id":"fixture-split",'
                '"cases":{"fixture-case-v2":"fixture"}}',
                encoding="utf-8",
            )
            spec_path.write_text(
                '{"schema_version":"metric-spec-v1","evaluator_id":"fixture-evaluator",'
                '"structure_field":"eta",'
                '"structure_threshold":0.5,"cycle_windows":[[0.0,0.0]],'
                '"device_channel":"voltage","device_scale":1.0}',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ArtifactValidationError, "mesh identity"):
                evaluate_files(
                    prediction_path=prediction_path,
                    oracle_path=oracle_path,
                    split_manifest_path=split_path,
                    metric_spec_path=spec_path,
                    output_path=root / "metrics.json",
                )


if __name__ == "__main__":
    unittest.main()
