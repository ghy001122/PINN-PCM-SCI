from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import h5py
import numpy as np

from pinn_pcm_sci.artifacts import CaseArtifact, PredictionArtifact
from pinn_pcm_sci.evaluator import ArtifactValidationError, evaluate_files


def _write_minimal_evaluation_contract(
    root: Path,
    oracle: CaseArtifact,
    prediction: PredictionArtifact,
) -> tuple[Path, Path, Path, Path]:
    oracle_path = root / "oracle.h5"
    prediction_path = root / "prediction.h5"
    split_path = root / "split.json"
    spec_path = root / "metric_spec.json"
    oracle.write(oracle_path)
    prediction.write(prediction_path)
    split_path.write_text(
        json.dumps(
            {
                "schema_version": "split-manifest-v1",
                "split_id": "fixture-split-v1",
                "cases": {oracle.case_id: "smoke_fixture"},
            }
        ),
        encoding="utf-8",
    )
    spec_path.write_text(
        json.dumps(
            {
                "schema_version": "metric-spec-v1",
                "evaluator_id": "fixture-evaluator-v1",
                "structure_field": "eta",
                "structure_threshold": 0.5,
                "cycle_windows": [[0.0, 1.0]],
                "device_channel": "voltage",
                "device_scale": 1.0,
            }
        ),
        encoding="utf-8",
    )
    return oracle_path, prediction_path, split_path, spec_path


class FrozenEvaluatorContractTest(unittest.TestCase):
    def test_identical_prediction_has_zero_primary_and_device_error(self) -> None:
        oracle = CaseArtifact(
            case_id="fixture-case-001",
            physical_contract_id="fixture-contract-v1",
            evidence_identity="NON_SCIENTIFIC_FIXTURE",
            nodes=np.array([[0.0, 0.0], [1.0, 0.0]], dtype=np.float64),
            cells=np.array([[0, 1]], dtype=np.int64),
            time=np.array([0.0, 0.5, 1.0], dtype=np.float64),
            fields={"eta": np.array([[0.0, 1.0], [1.0, 1.0], [1.0, 0.0]])},
            field_units={"eta": "1"},
            breakpoints=np.array([0.5], dtype=np.float64),
            circuit={"voltage": np.array([0.0, 1.0, 0.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )
        prediction = PredictionArtifact(
            case_id="fixture-case-001",
            physical_contract_id="fixture-contract-v1",
            method_id="fixture-model-v1",
            checkpoint_id="step-0001",
            time=oracle.time,
            fields={"eta": oracle.fields["eta"].copy()},
            field_units={"eta": "1"},
            circuit={"voltage": oracle.circuit["voltage"].copy()},
            circuit_units={"voltage": "V"},
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            oracle_path = root / "oracle.h5"
            prediction_path = root / "prediction.h5"
            split_path = root / "split.json"
            spec_path = root / "metric_spec.json"
            metrics_path = root / "metrics.json"
            oracle.write(oracle_path)
            prediction.write(prediction_path)
            split_path.write_text(
                json.dumps(
                    {
                        "schema_version": "split-manifest-v1",
                        "split_id": "fixture-split-v1",
                        "cases": {"fixture-case-001": "smoke_fixture"},
                    }
                ),
                encoding="utf-8",
            )
            spec_path.write_text(
                json.dumps(
                    {
                        "schema_version": "metric-spec-v1",
                        "evaluator_id": "fixture-evaluator-v1",
                        "structure_field": "eta",
                        "structure_threshold": 0.5,
                        "cycle_windows": [[0.0, 0.5], [0.5, 1.0]],
                        "device_channel": "voltage",
                        "device_scale": 1.0,
                    }
                ),
                encoding="utf-8",
            )

            metrics = evaluate_files(
                prediction_path=prediction_path,
                oracle_path=oracle_path,
                split_manifest_path=split_path,
                metric_spec_path=spec_path,
                output_path=metrics_path,
            )

        self.assertEqual(
            metrics,
            {
                "schema_version": "metrics-v1",
                "evaluator_id": "fixture-evaluator-v1",
                "case_id": "fixture-case-001",
                "split_id": "fixture-split-v1",
                "method_id": "fixture-model-v1",
                "checkpoint_id": "step-0001",
                "structure_symmetric_difference_cycle_equal": 0.0,
                "device_trajectory_nrmse": 0.0,
            },
        )

    def test_rejects_prediction_for_a_different_complete_case(self) -> None:
        oracle = CaseArtifact(
            case_id="fixture-case-001",
            physical_contract_id="fixture-contract-v1",
            evidence_identity="NON_SCIENTIFIC_FIXTURE",
            nodes=np.array([[0.0, 0.0]], dtype=np.float64),
            cells=np.array([[0]], dtype=np.int64),
            time=np.array([0.0], dtype=np.float64),
            fields={"eta": np.array([[0.0]], dtype=np.float64)},
            field_units={"eta": "1"},
            breakpoints=np.array([], dtype=np.float64),
            circuit={"voltage": np.array([0.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )
        prediction = PredictionArtifact(
            case_id="fixture-case-999",
            physical_contract_id="fixture-contract-v1",
            method_id="fixture-model-v1",
            checkpoint_id="step-0001",
            time=np.array([0.0], dtype=np.float64),
            fields={"eta": np.array([[0.0]], dtype=np.float64)},
            field_units={"eta": "1"},
            circuit={"voltage": np.array([0.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            oracle_path = root / "oracle.h5"
            prediction_path = root / "prediction.h5"
            split_path = root / "split.json"
            spec_path = root / "metric_spec.json"
            oracle.write(oracle_path)
            prediction.write(prediction_path)
            split_path.write_text(
                json.dumps(
                    {
                        "schema_version": "split-manifest-v1",
                        "split_id": "fixture-split-v1",
                        "cases": {"fixture-case-001": "smoke_fixture"},
                    }
                ),
                encoding="utf-8",
            )
            spec_path.write_text(
                json.dumps(
                    {
                        "schema_version": "metric-spec-v1",
                        "evaluator_id": "fixture-evaluator-v1",
                        "structure_field": "eta",
                        "structure_threshold": 0.5,
                        "cycle_windows": [[0.0, 1.0]],
                        "device_channel": "voltage",
                        "device_scale": 1.0,
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ArtifactValidationError, "case_id"):
                evaluate_files(
                    prediction_path=prediction_path,
                    oracle_path=oracle_path,
                    split_manifest_path=split_path,
                    metric_spec_path=spec_path,
                    output_path=root / "metrics.json",
                )

    def test_rejects_prediction_with_wrong_physical_units(self) -> None:
        oracle = CaseArtifact(
            case_id="fixture-case-001",
            physical_contract_id="fixture-contract-v1",
            evidence_identity="NON_SCIENTIFIC_FIXTURE",
            nodes=np.array([[0.0, 0.0]], dtype=np.float64),
            cells=np.array([[0]], dtype=np.int64),
            time=np.array([0.0], dtype=np.float64),
            fields={"eta": np.array([[0.0]], dtype=np.float64)},
            field_units={"eta": "1"},
            breakpoints=np.array([], dtype=np.float64),
            circuit={"voltage": np.array([0.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )
        prediction = PredictionArtifact(
            case_id="fixture-case-001",
            physical_contract_id="fixture-contract-v1",
            method_id="fixture-model-v1",
            checkpoint_id="step-0001",
            time=np.array([0.0], dtype=np.float64),
            fields={"eta": np.array([[0.0]], dtype=np.float64)},
            field_units={"eta": "K"},
            circuit={"voltage": np.array([0.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            oracle_path = root / "oracle.h5"
            prediction_path = root / "prediction.h5"
            split_path = root / "split.json"
            spec_path = root / "metric_spec.json"
            oracle.write(oracle_path)
            prediction.write(prediction_path)
            split_path.write_text(
                json.dumps(
                    {
                        "schema_version": "split-manifest-v1",
                        "split_id": "fixture-split-v1",
                        "cases": {"fixture-case-001": "smoke_fixture"},
                    }
                ),
                encoding="utf-8",
            )
            spec_path.write_text(
                json.dumps(
                    {
                        "schema_version": "metric-spec-v1",
                        "evaluator_id": "fixture-evaluator-v1",
                        "structure_field": "eta",
                        "structure_threshold": 0.5,
                        "cycle_windows": [[0.0, 1.0]],
                        "device_channel": "voltage",
                        "device_scale": 1.0,
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ArtifactValidationError, "unit"):
                evaluate_files(
                    prediction_path=prediction_path,
                    oracle_path=oracle_path,
                    split_manifest_path=split_path,
                    metric_spec_path=spec_path,
                    output_path=root / "metrics.json",
                )

    def test_rejects_prediction_missing_the_frozen_structure_field(self) -> None:
        oracle = CaseArtifact(
            case_id="fixture-case-001",
            physical_contract_id="fixture-contract-v1",
            evidence_identity="NON_SCIENTIFIC_FIXTURE",
            nodes=np.array([[0.0, 0.0]], dtype=np.float64),
            cells=np.array([[0]], dtype=np.int64),
            time=np.array([0.0], dtype=np.float64),
            fields={"eta": np.array([[0.0]], dtype=np.float64)},
            field_units={"eta": "1"},
            breakpoints=np.array([], dtype=np.float64),
            circuit={"voltage": np.array([0.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )
        prediction = PredictionArtifact(
            case_id="fixture-case-001",
            physical_contract_id="fixture-contract-v1",
            method_id="fixture-model-v1",
            checkpoint_id="step-0001",
            time=np.array([0.0], dtype=np.float64),
            fields={"eta": np.array([[0.0]], dtype=np.float64)},
            field_units={"eta": "1"},
            circuit={"voltage": np.array([0.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            oracle_path, prediction_path, split_path, spec_path = (
                _write_minimal_evaluation_contract(root, oracle, prediction)
            )
            with h5py.File(prediction_path, "a") as handle:
                del handle["fields/eta"]
            with self.assertRaisesRegex(ArtifactValidationError, "missing field"):
                evaluate_files(
                    prediction_path=prediction_path,
                    oracle_path=oracle_path,
                    split_manifest_path=split_path,
                    metric_spec_path=spec_path,
                    output_path=root / "metrics.json",
                )

    def test_rejects_non_finite_prediction_values(self) -> None:
        oracle = CaseArtifact(
            case_id="fixture-case-001",
            physical_contract_id="fixture-contract-v1",
            evidence_identity="NON_SCIENTIFIC_FIXTURE",
            nodes=np.array([[0.0, 0.0]], dtype=np.float64),
            cells=np.array([[0]], dtype=np.int64),
            time=np.array([0.0], dtype=np.float64),
            fields={"eta": np.array([[0.0]], dtype=np.float64)},
            field_units={"eta": "1"},
            breakpoints=np.array([], dtype=np.float64),
            circuit={"voltage": np.array([0.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )
        prediction = PredictionArtifact(
            case_id="fixture-case-001",
            physical_contract_id="fixture-contract-v1",
            method_id="fixture-model-v1",
            checkpoint_id="step-0001",
            time=np.array([0.0], dtype=np.float64),
            fields={"eta": np.array([[0.0]], dtype=np.float64)},
            field_units={"eta": "1"},
            circuit={"voltage": np.array([0.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            oracle_path, prediction_path, split_path, spec_path = (
                _write_minimal_evaluation_contract(root, oracle, prediction)
            )
            with h5py.File(prediction_path, "a") as handle:
                handle["fields/eta"][0, 0] = np.nan
            with self.assertRaisesRegex(ArtifactValidationError, "non-finite"):
                evaluate_files(
                    prediction_path=prediction_path,
                    oracle_path=oracle_path,
                    split_manifest_path=split_path,
                    metric_spec_path=spec_path,
                    output_path=root / "metrics.json",
                )

    def test_rejects_case_missing_from_the_frozen_split(self) -> None:
        oracle = CaseArtifact(
            case_id="fixture-case-001",
            physical_contract_id="fixture-contract-v1",
            evidence_identity="NON_SCIENTIFIC_FIXTURE",
            nodes=np.array([[0.0, 0.0]], dtype=np.float64),
            cells=np.array([[0]], dtype=np.int64),
            time=np.array([0.0], dtype=np.float64),
            fields={"eta": np.array([[0.0]], dtype=np.float64)},
            field_units={"eta": "1"},
            breakpoints=np.array([], dtype=np.float64),
            circuit={"voltage": np.array([0.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )
        prediction = PredictionArtifact(
            case_id=oracle.case_id,
            physical_contract_id=oracle.physical_contract_id,
            method_id="fixture-model-v1",
            checkpoint_id="step-0001",
            time=oracle.time.copy(),
            fields={"eta": oracle.fields["eta"].copy()},
            field_units={"eta": "1"},
            circuit={"voltage": oracle.circuit["voltage"].copy()},
            circuit_units={"voltage": "V"},
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            oracle_path, prediction_path, split_path, spec_path = (
                _write_minimal_evaluation_contract(root, oracle, prediction)
            )
            split_path.write_text(
                json.dumps(
                    {
                        "schema_version": "split-manifest-v1",
                        "split_id": "fixture-split-v1",
                        "cases": {"different-case": "smoke_fixture"},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ArtifactValidationError, "split"):
                evaluate_files(
                    prediction_path=prediction_path,
                    oracle_path=oracle_path,
                    split_manifest_path=split_path,
                    metric_spec_path=spec_path,
                    output_path=root / "metrics.json",
                )

    def test_rejects_a_cycle_window_without_samples(self) -> None:
        oracle = CaseArtifact(
            case_id="fixture-case-001",
            physical_contract_id="fixture-contract-v1",
            evidence_identity="NON_SCIENTIFIC_FIXTURE",
            nodes=np.array([[0.0, 0.0]], dtype=np.float64),
            cells=np.array([[0]], dtype=np.int64),
            time=np.array([0.0, 1.0], dtype=np.float64),
            fields={"eta": np.array([[0.0], [1.0]], dtype=np.float64)},
            field_units={"eta": "1"},
            breakpoints=np.array([], dtype=np.float64),
            circuit={"voltage": np.array([0.0, 1.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )
        prediction = PredictionArtifact(
            case_id=oracle.case_id,
            physical_contract_id=oracle.physical_contract_id,
            method_id="fixture-model-v1",
            checkpoint_id="step-0001",
            time=oracle.time.copy(),
            fields={"eta": oracle.fields["eta"].copy()},
            field_units={"eta": "1"},
            circuit={"voltage": oracle.circuit["voltage"].copy()},
            circuit_units={"voltage": "V"},
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            oracle_path, prediction_path, split_path, spec_path = (
                _write_minimal_evaluation_contract(root, oracle, prediction)
            )
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["cycle_windows"] = [[0.25, 0.75]]
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            with self.assertRaisesRegex(ArtifactValidationError, "cycle window"):
                evaluate_files(
                    prediction_path=prediction_path,
                    oracle_path=oracle_path,
                    split_manifest_path=split_path,
                    metric_spec_path=spec_path,
                    output_path=root / "metrics.json",
                )

    def test_rejects_a_different_physical_contract(self) -> None:
        oracle = CaseArtifact(
            case_id="fixture-case-001",
            physical_contract_id="fixture-contract-v1",
            evidence_identity="NON_SCIENTIFIC_FIXTURE",
            nodes=np.array([[0.0, 0.0]], dtype=np.float64),
            cells=np.array([[0]], dtype=np.int64),
            time=np.array([0.0], dtype=np.float64),
            fields={"eta": np.array([[0.0]], dtype=np.float64)},
            field_units={"eta": "1"},
            breakpoints=np.array([], dtype=np.float64),
            circuit={"voltage": np.array([0.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )
        prediction = PredictionArtifact(
            case_id=oracle.case_id,
            physical_contract_id="different-contract-v1",
            method_id="fixture-model-v1",
            checkpoint_id="step-0001",
            time=oracle.time.copy(),
            fields={"eta": oracle.fields["eta"].copy()},
            field_units={"eta": "1"},
            circuit={"voltage": oracle.circuit["voltage"].copy()},
            circuit_units={"voltage": "V"},
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            oracle_path, prediction_path, split_path, spec_path = (
                _write_minimal_evaluation_contract(root, oracle, prediction)
            )
            with self.assertRaisesRegex(ArtifactValidationError, "physical_contract_id"):
                evaluate_files(
                    prediction_path=prediction_path,
                    oracle_path=oracle_path,
                    split_manifest_path=split_path,
                    metric_spec_path=spec_path,
                    output_path=root / "metrics.json",
                )

    def test_rejects_a_prediction_on_a_different_time_grid(self) -> None:
        oracle = CaseArtifact(
            case_id="fixture-case-001",
            physical_contract_id="fixture-contract-v1",
            evidence_identity="NON_SCIENTIFIC_FIXTURE",
            nodes=np.array([[0.0, 0.0]], dtype=np.float64),
            cells=np.array([[0]], dtype=np.int64),
            time=np.array([0.0, 1.0], dtype=np.float64),
            fields={"eta": np.array([[0.0], [1.0]], dtype=np.float64)},
            field_units={"eta": "1"},
            breakpoints=np.array([], dtype=np.float64),
            circuit={"voltage": np.array([0.0, 1.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )
        prediction = PredictionArtifact(
            case_id=oracle.case_id,
            physical_contract_id=oracle.physical_contract_id,
            method_id="fixture-model-v1",
            checkpoint_id="step-0001",
            time=np.array([0.0, 0.5], dtype=np.float64),
            fields={"eta": oracle.fields["eta"].copy()},
            field_units={"eta": "1"},
            circuit={"voltage": oracle.circuit["voltage"].copy()},
            circuit_units={"voltage": "V"},
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            oracle_path, prediction_path, split_path, spec_path = (
                _write_minimal_evaluation_contract(root, oracle, prediction)
            )
            with self.assertRaisesRegex(ArtifactValidationError, "time grid"):
                evaluate_files(
                    prediction_path=prediction_path,
                    oracle_path=oracle_path,
                    split_manifest_path=split_path,
                    metric_spec_path=spec_path,
                    output_path=root / "metrics.json",
                )

    def test_hand_worked_nonzero_metric_is_deterministic(self) -> None:
        oracle = CaseArtifact(
            case_id="fixture-case-001",
            physical_contract_id="fixture-contract-v1",
            evidence_identity="NON_SCIENTIFIC_FIXTURE",
            nodes=np.array([[0.0, 0.0], [1.0, 0.0]], dtype=np.float64),
            cells=np.array([[0, 1]], dtype=np.int64),
            time=np.array([0.0, 0.5, 1.0], dtype=np.float64),
            fields={"eta": np.array([[0.0, 1.0], [1.0, 1.0], [1.0, 0.0]])},
            field_units={"eta": "1"},
            breakpoints=np.array([0.5], dtype=np.float64),
            circuit={"voltage": np.array([0.0, 1.0, 0.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )
        prediction = PredictionArtifact(
            case_id="fixture-case-001",
            physical_contract_id="fixture-contract-v1",
            method_id="fixture-model-v1",
            checkpoint_id="step-0001",
            time=oracle.time.copy(),
            fields={"eta": np.array([[1.0, 1.0], [0.0, 1.0], [1.0, 1.0]])},
            field_units={"eta": "1"},
            circuit={"voltage": np.array([1.0, 1.0, 0.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            oracle_path, prediction_path, split_path, spec_path = (
                _write_minimal_evaluation_contract(root, oracle, prediction)
            )
            first_path = root / "metrics_first.json"
            second_path = root / "metrics_second.json"
            first = evaluate_files(
                prediction_path=prediction_path,
                oracle_path=oracle_path,
                split_manifest_path=split_path,
                metric_spec_path=spec_path,
                output_path=first_path,
            )
            second = evaluate_files(
                prediction_path=prediction_path,
                oracle_path=oracle_path,
                split_manifest_path=split_path,
                metric_spec_path=spec_path,
                output_path=second_path,
            )

        self.assertEqual(
            (
                first["structure_symmetric_difference_cycle_equal"],
                first["device_trajectory_nrmse"],
                first,
            ),
            (0.5, 0.5773502691896257, second),
        )

    def test_rejects_unfrozen_schema_and_invalid_metric_scale(self) -> None:
        oracle = CaseArtifact(
            case_id="fixture-case-001",
            physical_contract_id="fixture-contract-v1",
            evidence_identity="NON_SCIENTIFIC_FIXTURE",
            nodes=np.array([[0.0, 0.0]], dtype=np.float64),
            cells=np.array([[0]], dtype=np.int64),
            time=np.array([0.0], dtype=np.float64),
            fields={"eta": np.array([[0.0]], dtype=np.float64)},
            field_units={"eta": "1"},
            breakpoints=np.array([], dtype=np.float64),
            circuit={"voltage": np.array([0.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )
        prediction = PredictionArtifact(
            case_id=oracle.case_id,
            physical_contract_id=oracle.physical_contract_id,
            method_id="fixture-model-v1",
            checkpoint_id="step-0001",
            time=oracle.time.copy(),
            fields={"eta": oracle.fields["eta"].copy()},
            field_units={"eta": "1"},
            circuit={"voltage": oracle.circuit["voltage"].copy()},
            circuit_units={"voltage": "V"},
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            oracle_path, prediction_path, split_path, spec_path = (
                _write_minimal_evaluation_contract(root, oracle, prediction)
            )
            split = json.loads(split_path.read_text(encoding="utf-8"))
            split["schema_version"] = "split-manifest-v999"
            split_path.write_text(json.dumps(split), encoding="utf-8")
            with self.assertRaisesRegex(ArtifactValidationError, "split manifest schema"):
                evaluate_files(
                    prediction_path=prediction_path,
                    oracle_path=oracle_path,
                    split_manifest_path=split_path,
                    metric_spec_path=spec_path,
                    output_path=root / "invalid-split-metrics.json",
                )

            split["schema_version"] = "split-manifest-v1"
            split_path.write_text(json.dumps(split), encoding="utf-8")
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["device_scale"] = 0.0
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            with self.assertRaisesRegex(ArtifactValidationError, "device_scale"):
                evaluate_files(
                    prediction_path=prediction_path,
                    oracle_path=oracle_path,
                    split_manifest_path=split_path,
                    metric_spec_path=spec_path,
                    output_path=root / "invalid-scale-metrics.json",
                )


if __name__ == "__main__":
    unittest.main()
