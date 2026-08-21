from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class PipelineSmokeContractTest(unittest.TestCase):
    def test_fixture_conversion_model_update_and_disk_evaluation_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_fixture = root / "raw_fixture.json"
            output_root = root / "outputs" / "runs"
            experiment_root = root / "experiment"
            run_id = "20260819T010203Z-smoke-pipeline-fixture-001"
            raw_fixture.write_text(
                json.dumps(
                    {
                        "case_id": "fixture-case-001",
                        "physical_contract_id": "fixture-contract-v1",
                        "evidence_identity": "NON_SCIENTIFIC_FIXTURE",
                        "mesh_unit": "arbitrary_fixture_length",
                        "nodes": [[0.0, 0.0], [1.0, 0.0]],
                        "cells": [[0, 1]],
                        "field_time": [0.0, 0.5, 1.0],
                        "circuit_time": [0.0, 0.5, 1.0],
                        "time_unit": "arbitrary_fixture_time",
                        "fields": {"eta": [[0.0, 1.0], [0.5, 1.0], [1.0, 0.0]]},
                        "field_units": {"eta": "1"},
                        "field_registry": {
                            "eta": {
                                "source_name": "eta",
                                "physical_symbol": "eta",
                                "quantity_label": "non_scientific_fixture_order_parameter",
                                "unit": "1",
                                "association": "point",
                                "temporal_kind": "dynamic",
                                "qualification_status": "NON_SCIENTIFIC_FIXTURE",
                            }
                        },
                        "breakpoints": [0.5],
                        "circuit": {"voltage": [0.0, 1.0, 0.0]},
                        "circuit_units": {"voltage": "V"},
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pinn_pcm_sci.smoke",
                    "--raw-fixture",
                    str(raw_fixture),
                    "--output-root",
                    str(output_root),
                    "--experiment-root",
                    str(experiment_root),
                    "--run-id",
                    run_id,
                    "--seed",
                    "7",
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                check=False,
            )
            run_root = output_root / run_id
            manifest = json.loads(
                (experiment_root / "manifests" / f"{run_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            metrics = json.loads((run_root / "metrics.json").read_text(encoding="utf-8"))
            index_lines = (experiment_root / "index.jsonl").read_text(
                encoding="utf-8"
            ).splitlines()

        self.assertEqual(
            (
                completed.returncode,
                (run_root / "case.h5").name,
                (run_root / "checkpoint.pt").name,
                (run_root / "prediction.h5").name,
                manifest["gate_outcome"],
                manifest["actual_budget"],
                metrics["evaluator_id"],
                len(index_lines),
            ),
            (
                0,
                "case.h5",
                "checkpoint.pt",
                "prediction.h5",
                "SMOKE_PASS",
                {"optimizer_steps": 1},
                "fixture-evaluator-v1",
                1,
            ),
            msg=completed.stderr,
        )

    def test_failed_attempt_still_records_a_manifest_and_index_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_fixture = root / "invalid_raw_fixture.json"
            output_root = root / "outputs" / "runs"
            experiment_root = root / "experiment"
            run_id = "20260819T010204Z-smoke-pipeline-fixture-invalid"
            raw_fixture.write_text(
                json.dumps(
                    {
                        "case_id": "fixture-case-invalid",
                        "physical_contract_id": "fixture-contract-v1",
                        "evidence_identity": "NON_SCIENTIFIC_FIXTURE",
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pinn_pcm_sci.smoke",
                    "--raw-fixture",
                    str(raw_fixture),
                    "--output-root",
                    str(output_root),
                    "--experiment-root",
                    str(experiment_root),
                    "--run-id",
                    run_id,
                    "--seed",
                    "7",
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                check=False,
            )
            manifest = json.loads(
                (experiment_root / "manifests" / f"{run_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            index_rows = [
                json.loads(line)
                for line in (experiment_root / "index.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]

        self.assertEqual(
            (
                completed.returncode,
                manifest["execution_status"],
                manifest["gate_outcome"],
                manifest["route_disposition"],
                manifest["failure_class"],
                len(index_rows),
            ),
            (1, "FAILED", "ENGINEERING_BLOCKED", "BLOCKED", "KeyError", 1),
        )


if __name__ == "__main__":
    unittest.main()
