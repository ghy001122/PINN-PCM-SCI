from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from pinn_pcm_sci import phk_v23_lf8 as core


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bundle = _load("lf8_bundle", ROOT / "cloud/phk_v23_lf8_autodl/build_bundle.py")
preflight = _load("lf8_preflight", ROOT / "cloud/phk_v23_lf8_autodl/preflight.py")


class LF8CloudTests(unittest.TestCase):
    @staticmethod
    def _qualification_payload() -> dict:
        return {
            "schema_id": "phk-v23-lf8-cpu-qualification-v1",
            "task_id": bundle.TASK_ID,
            "gate_outcome": "LF8_CPU_QUALIFICATION_PASS",
            "gpu_execution_authorized_by_cpu_gate": True,
            "scientific_optimizer_updates": 0,
            "checks": {"all_input_hashes": True, "fine_extra_LF_ONLY_stress_unread": True},
            "contracts": {
                role: {"path": relative, "sha256": bundle._sha256(ROOT / relative)}
                for role, relative in bundle.LF8_CONTRACTS.items()
            },
            "ledger": {
                "file_sha256": preflight.EXPECTED_LEDGER_SHA256,
                "manifest_sha256": preflight.EXPECTED_LEDGER_MANIFEST_SHA256,
                "semantic_sha256": preflight.EXPECTED_LEDGER_SEMANTIC_SHA256,
                "physics_1200_sha256": preflight.EXPECTED_PHYSICS_STREAM_SHA256,
                "fixed_blind_pool_sha256": preflight.EXPECTED_FIXED_POOL_SHA256,
            },
        }

    def test_runtime_closure_is_activation_bound_and_reference_blind(self):
        required = {
            "configs/phk_v23/lf8_competence_filter_write_allowlist_lock.json",
            "pinn_pcm_sci/phk_v23_lf8.py",
            "pinn_pcm_sci/phk_v23_lf7.py",
            "pinn_pcm_sci/phk_v23_lf6.py",
            "cloud/phk_v23_lf8_autodl/preflight.py",
            "cloud/phk_v23_lf8_autodl/run.sh",
        }
        self.assertTrue(required.issubset(bundle.STATIC_FILES))
        self.assertTrue(required.issubset(preflight.REQUIRED_RUNTIME))
        self.assertFalse(any(
            "evaluator" in path.lower() or "evaluation" in path.lower()
            for path in bundle.STATIC_FILES
        ))
        self.assertNotIn(
            "cloud/phk_v23_lf8_autodl/deployed-source-manifest.json",
            bundle.STATIC_FILES,
        )
        self.assertFalse((ROOT / "cloud/phk_v23_lf8_autodl/deployed-source-manifest.json").exists())
        self.assertEqual(
            set(inspect.signature(bundle.build).parameters),
            {"qualification_path", "qualification_manifest_path", "archive_path", "base_commit"},
        )

    def test_frozen_inputs_and_same_materialized_stream_match_contract(self):
        bundle._verify_frozen_inputs()
        self.assertEqual(bundle.EXPECTED_MEDIUM_SHA256, preflight.EXPECTED_MEDIUM_SHA256)
        self.assertEqual(bundle.EXPECTED_DEV_R_SHA256, preflight.EXPECTED_DEV_R_SHA256)
        self.assertEqual(bundle.EXPECTED_LEDGER_SHA256, preflight.EXPECTED_LEDGER_SHA256)
        self.assertEqual(bundle.EXPECTED_LEDGER_MANIFEST_SHA256,
                         preflight.EXPECTED_LEDGER_MANIFEST_SHA256)
        data = json.loads((ROOT / bundle.LF8_CONTRACTS["data"]).read_text(encoding="utf-8"))
        self.assertEqual(data["materialized_ledger"]["physics_1200_sha256"],
                         preflight.EXPECTED_PHYSICS_STREAM_SHA256)
        self.assertFalse(json.loads(
            (ROOT / bundle.LF8_CONTRACTS["method"]).read_text(encoding="utf-8")
        )["identity"]["runtime_sampling"])

    def test_activation_commit_byte_verifier_rejects_workspace_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "tracked.txt"
            path.write_bytes(b"activation")
            with mock.patch.object(bundle, "ROOT", root), mock.patch.object(
                bundle, "_git", side_effect=[b"a" * 40 + b"\n", b"activation"]
            ):
                bundle._verify_activation_commit("a" * 40, ["tracked.txt"])
            path.write_bytes(b"dirty")
            with mock.patch.object(bundle, "ROOT", root), mock.patch.object(
                bundle, "_git", side_effect=[b"a" * 40 + b"\n", b"activation"]
            ):
                with self.assertRaises(PermissionError):
                    bundle._verify_activation_commit("a" * 40, ["tracked.txt"])

    def test_cpu_qualification_requires_zero_updates_and_exact_contracts(self):
        with tempfile.TemporaryDirectory() as temporary:
            artifact = Path(temporary) / "qualification.json"
            payload = self._qualification_payload()
            artifact.write_text(json.dumps(payload), encoding="utf-8")
            preflight._verify_qualification(artifact, ROOT)
            payload["scientific_optimizer_updates"] = 1
            artifact.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(PermissionError):
                preflight._verify_qualification(artifact, ROOT)

    def test_cpu_qualification_has_one_exact_pass_identity(self):
        source = (ROOT / "cloud/phk_v23_lf8_autodl/build_bundle.py").read_text(encoding="utf-8")
        remote = (ROOT / "cloud/phk_v23_lf8_autodl/preflight.py").read_text(encoding="utf-8")
        self.assertIn('"LF8_CPU_QUALIFICATION_PASS"', source)
        self.assertIn('"LF8_CPU_QUALIFICATION_PASS"', remote)
        self.assertNotIn("LF8_CPU_PASS", source + remote)
        self.assertNotIn("cpu_qualification_artifact", source)
        self.assertNotIn("cpu_qualification_manifest", source)

    def test_materialized_ledger_verifies_all_steps_and_fixed_pool(self):
        report = preflight._verify_ledger(
            ROOT,
            ROOT / preflight.LEDGER_RELATIVE.as_posix(),
            ROOT / preflight.LEDGER_MANIFEST_RELATIVE.as_posix(),
        )
        self.assertEqual(report["p0_step_count"], 1200)
        self.assertEqual(report["p0_physics_rolling_sha256"],
                         preflight.EXPECTED_PHYSICS_STREAM_SHA256)
        self.assertEqual(report["fixed_blind_pool_sha256"],
                         preflight.EXPECTED_FIXED_POOL_SHA256)

    def test_hash_algorithms_preserve_lf6_ledger_identity(self):
        import numpy as np

        array = np.arange(12, dtype=np.int64).reshape(3, 4)
        expected = hashlib.sha256(
            b"PHK_V23_LF6_ARRAY_V1\nvalues\n<i8\n[3,4]\n" + array.tobytes(order="C")
        ).hexdigest().upper()
        self.assertEqual(preflight._array_sha256("values", array), expected)

    def test_output_root_must_be_campaign_namespaced_existing_and_empty(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            deployment = base / "deployment"
            deployment.mkdir()
            output = base / "lf8-run-test"
            output.mkdir()
            with mock.patch.object(preflight, "EXPECTED_REMOTE_PARENT", base.as_posix()):
                self.assertTrue(preflight._verify_output_root(deployment, output)["empty"])
                (output / "partial.txt").write_text("partial", encoding="utf-8")
                with self.assertRaises(RuntimeError):
                    preflight._verify_output_root(deployment, output)

    def test_preflight_requires_exact_v100(self):
        good = mock.Mock()
        good.is_available.return_value = True
        good.get_device_name.return_value = "Tesla V100-PCIE-32GB"
        self.assertEqual(preflight._verify_gpu(good), "Tesla V100-PCIE-32GB")
        for available, name in ((False, "Tesla V100-PCIE-32GB"),
                                (True, "NVIDIA A100-SXM4-40GB")):
            probe = mock.Mock()
            probe.is_available.return_value = available
            probe.get_device_name.return_value = name
            with self.assertRaises(RuntimeError):
                preflight._verify_gpu(probe)

    def test_cloud_leakage_scan_forbids_fine_extra_lf_only_stress(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            medium = root / "medium.npz"
            medium.write_bytes(b"allowed")
            self.assertEqual(preflight._forbidden(root, {"medium.npz"}), [])
            for name in ("nominal-fine.npz", "nominal-extra-fine.npz",
                         "direct-lf-only.pt", "stress-reference.json"):
                (root / name).write_bytes(b"forbidden")
            forbidden = preflight._forbidden(root, {"medium.npz"})
            self.assertEqual(len(forbidden), 4)
            self.assertTrue(any("lf-only" in path for path in forbidden))
            self.assertTrue(any("stress" in path for path in forbidden))

    def test_launcher_runs_one_order_owning_process_after_preflight(self):
        launcher = (ROOT / "cloud/phk_v23_lf8_autodl/run.sh").read_text(encoding="utf-8")
        self.assertNotIn("Sobol", launcher)
        self.assertIn("LF8_OUTPUT_ROOT", launcher)
        self.assertIn("find \"${LF8_OUTPUT_ROOT}\"", launcher)
        self.assertLess(launcher.index("preflight.py"),
                        launcher.index("python -m pinn_pcm_sci.phk_v23_lf8"))
        self.assertEqual(launcher.count("python -m pinn_pcm_sci.phk_v23_lf8"), 1)
        self.assertIn("mandatory F*", launcher)
        self.assertIn("conditional", launcher)
        for flag in ("--medium-carrier", "--dev-r-checkpoint", "--materialized-ledger",
                     "--ledger-manifest", "--cpu-qualification", "--source-identity"):
            self.assertIn(flag, launcher)
        runner = launcher[launcher.index("python -m pinn_pcm_sci.phk_v23_lf8"):]
        self.assertIn("--initial-checkpoint", runner)
        self.assertNotIn("--dev-r-checkpoint", runner)
        self.assertNotIn("--ledger-manifest", runner)

    def test_launcher_cli_matches_core_and_core_owns_conditional_order(self):
        option_strings = {
            option
            for action in core._parser()._actions
            for option in action.option_strings
        }
        self.assertTrue({
            "--output-root", "--medium-carrier", "--initial-checkpoint",
            "--materialized-ledger", "--cpu-qualification", "--device",
            "--source-identity",
        }.issubset(option_strings))
        source = inspect.getsource(core.execute_gpu_campaign)
        self.assertLess(source.index("_run_fstar("),
                        source.index("if schedule_control_required(fstar):"))
        self.assertLess(source.index("if schedule_control_required(fstar):"),
                        source.index("_run_schedule_control("))
        self.assertEqual(source.count("_run_fstar("), 1)
        self.assertEqual(source.count("_run_schedule_control("), 1)
        self.assertIn("ledger=ledger", source)
        self.assertIn("initial_checkpoint=Path(initial_checkpoint)", source)
        runner_source = inspect.getsource(core)
        for generator in ("SobolEngine(", "LF0PhysicsBatchStream(",
                          "PhkCollocationSampler("):
            self.assertNotIn(generator, runner_source)

    def test_method_contract_fixes_fstar_then_conditional_control_without_medium(self):
        method = json.loads((ROOT / bundle.LF8_CONTRACTS["method"]).read_text(encoding="utf-8"))
        self.assertEqual(method["P0_FSTAR"]["role"],
                         "P0_FSTAR_IDENTITY_CORRECT_COMPETENCE_FILTER")
        self.assertEqual(method["P0_C"]["role"], "P0_C_ACCEPTED_SCHEDULE_NO_FILTER")
        self.assertEqual(method["P0_C"]["trigger"],
                         "FSTAR_1200_VALID_SAFETY_AND_J_FINAL_LT_J0")
        self.assertFalse(method["P0_C"]["medium_audit_during_training"])
        self.assertFalse(method["P0_C"]["rollback"])
        self.assertFalse(method["P0_C"]["filter"])
        self.assertFalse(method["identity"]["medium_or_label_gradient"])

    def test_schedule_control_has_no_medium_audit_interface(self):
        self.assertNotIn("dataset", inspect.signature(core._run_schedule_control).parameters)
        source = inspect.getsource(core._run_schedule_control)
        self.assertNotIn("_audit(", source)
        self.assertNotIn("full_medium_audit", source)
        self.assertNotIn('["medium"]', source)
        campaign = inspect.getsource(core.execute_gpu_campaign)
        invocation = campaign[campaign.index("_run_schedule_control("):]
        self.assertNotIn("dataset=dataset", invocation)


if __name__ == "__main__":
    unittest.main()
