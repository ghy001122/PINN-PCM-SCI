from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from pinn_pcm_sci.phk_contract import (
    PhkProgramContract,
    PhkObjectContract,
    PhkSplitManifest,
    build_phk_split_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
PROGRAM_PATH = ROOT / "configs" / "phk_v2" / "program_contract.json"
OBJECT_PATH = ROOT / "configs" / "phk_v2" / "object_numerical_contract.json"
SPLIT_PATH = ROOT / "configs" / "phk_v2" / "case_split_manifest.json"


class PhkContractTest(unittest.TestCase):
    def test_live_contracts_load_fail_closed(self) -> None:
        program = PhkProgramContract.load(PROGRAM_PATH)
        physical = PhkObjectContract.load(OBJECT_PATH, program=program)

        self.assertEqual(program.contract_id, "PLAN_PHK_V2_V1")
        self.assertEqual(
            physical.contract_id,
            "PHK_REDUCED_WALL_CELL_2D_V1_NUMERICAL_V1",
        )
        self.assertEqual(physical.pulse_cycles, 2)
        self.assertEqual(physical.dtype, "float64")

    def test_contract_rejects_unknown_or_invalid_values(self) -> None:
        payload = json.loads(OBJECT_PATH.read_text(encoding="utf-8"))
        payload["unexpected"] = "silent drift"
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unknown"):
                PhkObjectContract.load(
                    path,
                    program=PhkProgramContract.load(PROGRAM_PATH),
                )

        payload = json.loads(OBJECT_PATH.read_text(encoding="utf-8"))
        payload["coefficients"]["interface_width"] = -0.04
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "interface_width"):
                PhkObjectContract.load(
                    path,
                    program=PhkProgramContract.load(PROGRAM_PATH),
                )

    def test_waveform_has_exact_declared_boundaries(self) -> None:
        contract = PhkObjectContract.load(
            OBJECT_PATH,
            program=PhkProgramContract.load(PROGRAM_PATH),
        )
        values = {
            0.0: 0.0,
            0.025: 0.375,
            0.05: 0.75,
            0.30: 0.75,
            0.325: 0.375,
            0.35: 0.0,
            0.90: 0.0,
            1.05: 0.75,
            2.0: 0.0,
        }
        for time_value, expected in values.items():
            with self.subTest(time=time_value):
                self.assertAlmostEqual(contract.waveform(time_value), expected)

    def test_split_manifest_is_deterministic_exclusive_and_complete(self) -> None:
        program = PhkProgramContract.load(PROGRAM_PATH)
        contract = PhkObjectContract.load(OBJECT_PATH, program=program)
        first = build_phk_split_manifest(program=program, physical=contract)
        second = build_phk_split_manifest(program=program, physical=contract)

        self.assertEqual(first, second)
        self.assertEqual(first["schema_id"], "phk-v2-split-manifest-v1")
        self.assertEqual(first["program_contract_sha256"], program.sha256)
        self.assertEqual(first["object_contract_sha256"], contract.sha256)
        self.assertEqual(
            len(first["cases"]),
            3 * 3 * 3 * 2 * 3 * 2,
        )
        self.assertEqual(
            set(first["pool_counts"]),
            {"D", "I1", "I2", "F_A", "F_O", "R"},
        )
        self.assertEqual(
            sum(first["pool_counts"].values()),
            len(first["cases"]),
        )
        self.assertEqual(len(first["cases"]), len(set(first["cases"])))

    def test_orthogonal_and_reserve_rules_precede_hash_partition(self) -> None:
        program = PhkProgramContract.load(PROGRAM_PATH)
        contract = PhkObjectContract.load(OBJECT_PATH, program=program)
        manifest = build_phk_split_manifest(program=program, physical=contract)

        for case_id, case in manifest["cases"].items():
            factors = case["factors"]
            if factors["constitutive_branch"] == "LOWER_PHASE_CONDUCTIVITY_FEEDBACK" and factors["waveform_amplitude"] == 0.85:
                self.assertEqual(case["pool"], "R", case_id)
            elif factors["heater_width_fraction"] == 0.20 or factors["interface_width"] == 0.025:
                self.assertEqual(case["pool"], "F_O", case_id)

    def test_live_split_binding_rebuilds_exactly_and_rejects_tamper(self) -> None:
        program = PhkProgramContract.load(PROGRAM_PATH)
        physical = PhkObjectContract.load(OBJECT_PATH, program=program)
        split = PhkSplitManifest.load(
            SPLIT_PATH,
            program=program,
            physical=physical,
        )
        self.assertEqual(len(split.payload["cases"]), 324)
        self.assertEqual(len(split.file_sha256), 64)

        payload = json.loads(SPLIT_PATH.read_text(encoding="utf-8"))
        payload["pool_counts"]["D"] += 1
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "tampered.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "does not exactly match"):
                PhkSplitManifest.load(
                    path,
                    program=program,
                    physical=physical,
                )


if __name__ == "__main__":
    unittest.main()
