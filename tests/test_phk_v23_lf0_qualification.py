from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from pinn_pcm_sci.phk_v23_lf0_qualification import qualify_cpu


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs" / "phk_v23" / "decision_contract_lf0_attribution.json"


class PhkV23Lf0QualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = qualify_cpu(CONTRACT)

    def test_real_nominal_sources_pass_the_frozen_cpu_gate(self) -> None:
        report = self.report
        self.assertTrue(report["passed"])
        self.assertEqual(report["status"], "LF0_CPU_QUALIFIED")
        self.assertEqual(report["blockers"], [])
        self.assertTrue(report["medium_event_competence"]["passed"])
        self.assertTrue(report["correction_headroom"]["passed"])

        c0 = report["c0_strongform_gate"]
        self.assertAlmostEqual(c0["maximum_residual_to_floor_ratio"], 1.9140757261989731)
        self.assertAlmostEqual(c0["minimum_rhs_sign_agreement"], 1.0)
        self.assertTrue(c0["official_cross_resolution_gate_reused"])

    def test_exact_top_raw_latent_and_maximum_principle_are_admissible(self) -> None:
        for resolution in ("medium", "fine", "extra_fine"):
            record = self.report["references"][resolution]
            latent = record["required_exact_top_latent"]
            guard = record["potential_maximum_principle"]
            self.assertTrue(latent["all_finite"])
            self.assertIsNotNone(latent["q05"])
            self.assertIsNotNone(latent["q50"])
            self.assertIsNotNone(latent["q95"])
            self.assertIsNotNone(latent["q99"])
            self.assertGreater(latent["maximum_absolute"], 0.0)
            self.assertEqual(latent["zero_waveform_maximum_absolute_error"], 0.0)
            self.assertEqual(latent["top_fixed_maximum_absolute_error"], 0.0)
            self.assertLess(latent["minimum"], 0.0)
            self.assertTrue(guard["passed"])
            self.assertEqual(guard["maximum_excess"], 0.0)
            self.assertEqual(guard["violation_fraction"], 0.0)
            self.assertEqual(set(guard["by_physical_window"]), {"W1", "W2", "W3", "W4"})
            self.assertTrue(
                all(
                    item["violation_fraction_above_tolerance"] == 0.0
                    for item in guard["by_physical_window"].values()
                )
            )

    def test_headroom_uses_matching_primary_and_co_primary_units(self) -> None:
        headroom = self.report["correction_headroom"]
        self.assertAlmostEqual(headroom["D_primary"], 0.00042500000000000003)
        self.assertAlmostEqual(headroom["U_primary"], 0.000145)
        self.assertAlmostEqual(
            headroom["D_co_primary_unnormalized"], 0.006566169047747438
        )
        self.assertAlmostEqual(
            headroom["U_co_primary_unnormalized"], 0.0022958271323946142
        )
        self.assertTrue(headroom["primary_exceeds_floor"])
        self.assertTrue(headroom["co_primary_exceeds_floor"])

    def test_output_is_strict_finite_json_and_records_no_gpu_or_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "qualification.json"
            written = qualify_cpu(CONTRACT, output_path=output)
            payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(payload, written)
        self.assertEqual(payload["execution_boundary"]["device"], "CPU")
        self.assertEqual(payload["execution_boundary"]["gpu_hours"], 0)
        self.assertFalse(payload["execution_boundary"]["neural_checkpoint_loaded"])
        self.assertFalse(payload["execution_boundary"]["stress_read"])

    def test_gpu_admission_record_binds_source_contracts_and_inputs(self) -> None:
        source_identity = "LF0-BUNDLE-" + "A" * 64
        source_commit = "b" * 40
        report = qualify_cpu(
            CONTRACT,
            source_identity=source_identity,
            source_commit=source_commit,
        )
        self.assertEqual(report["qualified_source_identity"], source_identity)
        self.assertEqual(report["source_commit"], source_commit)
        self.assertEqual(
            set(report["contract_identities"]), {"program", "method", "data", "decision"}
        )
        self.assertEqual(
            set(report["input_identities"]),
            {
                "low_fidelity_training_source",
                "qualification_fine",
                "qualification_extra_fine",
                "c0_artifact",
                "c0_contract",
                "oracle_floor_contract",
                "oracle_floor_seal",
            },
        )
        self.assertEqual(
            report["input_identities"]["low_fidelity_training_source"]["sha256"],
            report["medium_source_sha256"],
        )

    def test_stress_like_contract_path_fails_before_carrier_io(self) -> None:
        payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
        payload["qualification_inputs"]["c0_artifact"]["path"] = (
            "outputs/sealed/phk_v22r/narrow_interface_extra_fine/reference.npz"
        )
        with tempfile.TemporaryDirectory() as directory:
            altered = Path(directory) / "contract.json"
            altered.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "stress or sealed input path"):
                qualify_cpu(altered)


if __name__ == "__main__":
    unittest.main()
