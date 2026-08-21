from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

from pinn_pcm_sci.artifacts import CaseArtifact, PredictionArtifact


class EvaluatorProcessContractTest(unittest.TestCase):
    def test_evaluator_process_reads_only_disk_artifacts(self) -> None:
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
                        "cycle_windows": [[0.0, 1.0]],
                        "device_channel": "voltage",
                        "device_scale": 1.0,
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pinn_pcm_sci.evaluate",
                    "--prediction",
                    str(prediction_path),
                    "--oracle",
                    str(oracle_path),
                    "--split",
                    str(split_path),
                    "--metric-spec",
                    str(spec_path),
                    "--out",
                    str(metrics_path),
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                check=False,
            )
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

        self.assertEqual(
            (
                completed.returncode,
                metrics["structure_symmetric_difference_cycle_equal"],
                metrics["device_trajectory_nrmse"],
            ),
            (0, 0.0, 0.0),
            msg=completed.stderr,
        )


if __name__ == "__main__":
    unittest.main()
