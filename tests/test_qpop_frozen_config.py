from __future__ import annotations

import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


class QPopFrozenConfigTest(unittest.TestCase):
    def test_g2_input_is_the_single_registered_endtime_delta(self) -> None:
        root = (
            Path(__file__).resolve().parents[1]
            / "configs"
            / "qpop"
            / "cpc-v1-imt-intrinsic-voltage-osc"
        )
        spec = json.loads((root / "conversion_spec.json").read_text(encoding="utf-8"))
        canonical_path = root / "canonical_input.xml"
        smoke_path = root / "smoke_input.xml"

        self.assertEqual(
            hashlib.sha256(canonical_path.read_bytes()).hexdigest(),
            spec["canonical_input_sha256"],
        )
        self.assertEqual(
            hashlib.sha256(smoke_path.read_bytes()).hexdigest(),
            spec["expected_input_sha256"],
        )
        canonical_root = ET.parse(canonical_path).getroot()
        smoke_root = ET.parse(smoke_path).getroot()
        canonical_endtime = canonical_root.find("./time/endtime")
        smoke_endtime = smoke_root.find("./time/endtime")
        assert canonical_endtime is not None and smoke_endtime is not None
        self.assertEqual(
            (
                canonical_endtime.text,
                smoke_endtime.text,
                canonical_endtime.attrib,
                smoke_endtime.attrib,
                spec["allowed_input_differences"],
            ),
            (
                "2e3",
                "1e-6",
                {"unit": "ns"},
                {"unit": "ns"},
                [
                    {
                        "xpath": "/input/time/endtime",
                        "canonical_value": "2e3",
                        "smoke_value": "1e-6",
                        "unit": "ns",
                    }
                ],
            ),
        )
        canonical_endtime.text = smoke_endtime.text
        self.assertEqual(
            ET.tostring(canonical_root, encoding="unicode"),
            ET.tostring(smoke_root, encoding="unicode"),
        )

    def test_g2_registry_freezes_all_six_dynamic_fields_without_si_density_claim(self) -> None:
        spec_path = (
            Path(__file__).resolve().parents[1]
            / "configs"
            / "qpop"
            / "cpc-v1-imt-intrinsic-voltage-osc"
            / "conversion_spec.json"
        )
        spec = json.loads(spec_path.read_text(encoding="utf-8"))

        self.assertEqual(
            set(spec["field_registry"]),
            {
                "eta",
                "psi",
                "electron_occupancy",
                "hole_occupancy",
                "electric_potential",
                "temperature",
            },
        )
        self.assertEqual(spec["field_registry"]["psi"]["source_name"], "mu")
        self.assertEqual(spec["field_registry"]["electron_occupancy"]["unit"], "1")
        self.assertIn(
            "qpop_native",
            spec["field_registry"]["electron_occupancy"]["quantity_label"],
        )
        self.assertEqual(
            spec["evaluator_audit"],
            {
                "status": "ABSENT",
                "disposition": "OFFICIAL_EVALUATOR_NOT_PROVIDED",
            },
        )


if __name__ == "__main__":
    unittest.main()
