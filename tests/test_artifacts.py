from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from pinn_pcm_sci.artifacts import CaseArtifact, PredictionArtifact


class CaseArtifactContractTest(unittest.TestCase):
    def test_round_trip_preserves_public_case_contract(self) -> None:
        artifact = CaseArtifact(
            case_id="fixture-case-001",
            physical_contract_id="fixture-contract-v1",
            evidence_identity="NON_SCIENTIFIC_FIXTURE",
            nodes=np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]], dtype=np.float64),
            cells=np.array([[0, 1, 2]], dtype=np.int64),
            time=np.array([0.0, 0.5, 1.0], dtype=np.float64),
            fields={
                "eta": np.array(
                    [[0.0, 0.0, 0.0], [0.2, 0.4, 0.6], [0.8, 0.9, 1.0]],
                    dtype=np.float64,
                )
            },
            field_units={"eta": "1"},
            breakpoints=np.array([0.5], dtype=np.float64),
            circuit={"voltage": np.array([0.0, 1.0, 0.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "case.h5"
            artifact.write(path)
            loaded = CaseArtifact.read(path)

        self.assertEqual(loaded.case_id, "fixture-case-001")
        self.assertEqual(loaded.physical_contract_id, "fixture-contract-v1")
        self.assertEqual(loaded.evidence_identity, "NON_SCIENTIFIC_FIXTURE")
        np.testing.assert_array_equal(loaded.nodes, artifact.nodes)
        np.testing.assert_array_equal(loaded.cells, artifact.cells)
        np.testing.assert_array_equal(loaded.time, artifact.time)
        np.testing.assert_array_equal(loaded.breakpoints, artifact.breakpoints)
        np.testing.assert_array_equal(loaded.fields["eta"], artifact.fields["eta"])
        np.testing.assert_array_equal(loaded.circuit["voltage"], artifact.circuit["voltage"])
        self.assertEqual(loaded.field_units, {"eta": "1"})
        self.assertEqual(loaded.circuit_units, {"voltage": "V"})


class PredictionArtifactContractTest(unittest.TestCase):
    def test_round_trip_preserves_prediction_identity_and_values(self) -> None:
        prediction = PredictionArtifact(
            case_id="fixture-case-001",
            physical_contract_id="fixture-contract-v1",
            method_id="fixture-model-v1",
            checkpoint_id="step-0001",
            time=np.array([0.0, 1.0], dtype=np.float64),
            fields={"eta": np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.float64)},
            field_units={"eta": "1"},
            circuit={"voltage": np.array([0.0, 1.0], dtype=np.float64)},
            circuit_units={"voltage": "V"},
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prediction.h5"
            prediction.write(path)
            loaded = PredictionArtifact.read(path)

        self.assertEqual(
            (
                loaded.case_id,
                loaded.physical_contract_id,
                loaded.method_id,
                loaded.checkpoint_id,
                loaded.field_units,
                loaded.circuit_units,
                loaded.time.tolist(),
                loaded.fields["eta"].tolist(),
                loaded.circuit["voltage"].tolist(),
            ),
            (
                "fixture-case-001",
                "fixture-contract-v1",
                "fixture-model-v1",
                "step-0001",
                {"eta": "1"},
                {"voltage": "V"},
                [0.0, 1.0],
                [[0.0, 1.0], [1.0, 0.0]],
                [0.0, 1.0],
            ),
        )


if __name__ == "__main__":
    unittest.main()
