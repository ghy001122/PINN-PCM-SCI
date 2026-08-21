from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import numpy as np

from pinn_pcm_sci.artifacts import CaseArtifact
from pinn_pcm_sci.qpop_reference import parse_historical_reference_log
from pinn_pcm_sci.qpop_signal_audit import audit_structural_signal


class QPopReferencePilotTests(unittest.TestCase):
    def test_historical_log_parser_accepts_only_the_frozen_ten_column_profile(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "log.txt"
            path.write_text(
                "#Step Time Time step Tfail Nfail Other fail Av. EOP norm Av. T (K) VO2 V drop (V) VO2 R (Ohm)\n"
                "1 1.000000e-06 1.000000e-06 0 0 0 1.2 3.0e2 5.0 8.0e5\n"
                "2 2.000000e-06 1.000000e-06 0 0 0 1.1 3.1e2 4.0 7.0e5\n",
                encoding="utf-8",
            )
            parsed = parse_historical_reference_log(path)
            self.assertEqual(parsed["step"].tolist(), [1.0, 2.0])
            self.assertEqual(parsed["time"].tolist(), [1.0e-6, 2.0e-6])
            self.assertEqual(parsed["reported_voltage_drop"].tolist(), [5.0, 4.0])

            path.write_text(path.read_text(encoding="utf-8") + "Finished computation\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "numeric rows"):
                parse_historical_reference_log(path)

    def test_signal_audit_detects_structural_drop_recovery_and_clock_heterogeneity(self) -> None:
        nodes = np.asarray([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]], dtype=np.float64)
        cells = np.asarray([[0, 1, 2]], dtype=np.int64)
        eta = np.asarray(
            [
                [1.0, 1.0, 1.0],
                [0.9, 0.2, 0.8],
                [0.1, 0.0, 0.2],
                [0.8, 0.9, 1.0],
            ],
            dtype=np.float64,
        )
        time = np.asarray([0.0, 1.0, 2.0, 4.0], dtype=np.float64)
        artifact = CaseArtifact(
            case_id="fixture",
            physical_contract_id="fixture-contract",
            evidence_identity="UNQUALIFIED_FIXTURE",
            nodes=nodes,
            cells=cells,
            mesh_unit="nm",
            field_time=time,
            circuit_time=time,
            time_unit="ns",
            fields={"eta": eta},
            field_units={"eta": "1"},
            field_registry={
                "eta": {
                    "source_name": "eta",
                    "physical_symbol": "eta",
                    "quantity_label": "structural_order_parameter",
                    "unit": "1",
                    "association": "point",
                    "temporal_kind": "dynamic",
                    "qualification_status": "UNQUALIFIED_FIXTURE",
                }
            },
            breakpoints=np.asarray([], dtype=np.float64),
            circuit={"voltage": np.asarray([5.0, 1.0, 5.0, 1.0])},
            circuit_units={"voltage": "V"},
        )
        report = audit_structural_signal(artifact)
        self.assertTrue(report["target_structure_event_present"])
        self.assertTrue(report["formation_recovery_present"])
        self.assertGreater(report["temporal_rate_dynamic_range"], 1.0)
        self.assertGreater(report["spatial_rate_heterogeneity_peak"], 0.0)


if __name__ == "__main__":
    unittest.main()
