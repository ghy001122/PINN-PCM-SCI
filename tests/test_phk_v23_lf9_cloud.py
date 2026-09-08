from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy as np

from pinn_pcm_sci import phk_v23_lf9 as core


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bundle = _load("lf9_bundle", ROOT / "cloud/phk_v23_lf9_autodl/build_bundle.py")
preflight = _load("lf9_preflight", ROOT / "cloud/phk_v23_lf9_autodl/preflight.py")


class LF9CloudTests(unittest.TestCase):
    def test_runtime_closure_is_activation_bound_and_reference_blind(self):
        required = {
            "configs/phk_v23/lf9_write_allowlist_lock.json",
            "pinn_pcm_sci/phk_v23_lf9.py",
            "pinn_pcm_sci/phk_v23_lf8.py",
            "pinn_pcm_sci/phk_v23_lf6.py",
            "cloud/phk_v23_lf9_autodl/preflight.py",
            "cloud/phk_v23_lf9_autodl/run.sh",
        }
        self.assertTrue(required.issubset(bundle.STATIC_FILES))
        self.assertTrue(required.issubset(preflight.REQUIRED_RUNTIME))
        self.assertFalse(any(
            "evaluator" in path.lower() or "evaluation" in path.lower()
            for path in bundle.STATIC_FILES
        ))
        self.assertNotIn(
            "cloud/phk_v23_lf9_autodl/deployed-source-manifest.json",
            bundle.STATIC_FILES,
        )
        deployed_path = ROOT / "cloud/phk_v23_lf9_autodl/deployed-source-manifest.json"
        if not deployed_path.exists():
            self.assertFalse(deployed_path.exists())
            return
        deployed = json.loads(deployed_path.read_text(encoding="utf-8"))
        self.assertEqual(deployed.get("schema_id"), "phk-v23-lf9-deployed-source-manifest-v1")
        self.assertEqual(deployed.get("task_id"), bundle.TASK_ID)
        base_commit = str(deployed.get("base_commit", ""))
        self.assertEqual(len(base_commit), 40)
        self.assertEqual(bundle._git("cat-file", "-t", base_commit).decode().strip(), "commit")
        self.assertEqual(
            bundle._git("show", "-s", "--format=%s",
                        "c38fa80d2fa2ceb0b1bd1fa9faf70440f2a07159").decode().strip(),
            "Activate PHK-V2.3 LF9 equation-routed thermal-CV refinement",
        )
        # A source-identity-preserving prestep engineering fix may become the
        # deployed base; it must remain descended from the authorized activation.
        bundle._git("merge-base", "--is-ancestor",
                    "c38fa80d2fa2ceb0b1bd1fa9faf70440f2a07159", base_commit)
        materialized = deployed.get("materialized_inputs", {})
        self.assertEqual(set(materialized), {
            "medium", "dev_r_checkpoint", "strong_ledger", "strong_ledger_manifest",
            "cv_ledger", "cv_ledger_manifest", "cpu_qualification",
        })
        self.assertIs(deployed.get("runtime_coordinate_generation"), False)
        self.assertIs(deployed.get("arm_local_failure_isolation"), True)
        bound_paths = [*deployed.get("files", {})]
        bound_paths.extend(str(record.get("path", "")) for record in materialized.values())
        forbidden = ("fine", "extra", "lf_only", "lf-only", "stress", "evaluation")
        self.assertFalse(any(token in path.lower() for path in bound_paths for token in forbidden))
        identity_lines = [f"base_commit={base_commit.upper()}\n"]
        identity_lines.extend(
            f"source:{path}={digest}\n" for path, digest in sorted(deployed["files"].items())
        )
        identity_lines.extend(
            f"input:{role}={record['sha256']}\n" for role, record in sorted(materialized.items())
        )
        expected_identity = "LF9-BUNDLE-" + hashlib.sha256(
            "".join(identity_lines).encode("ascii")
        ).hexdigest().upper()
        self.assertEqual(deployed.get("source_identity"), expected_identity)

    def test_frozen_inputs_and_contract_bindings(self):
        bundle._verify_frozen_inputs()
        data = json.loads((ROOT / bundle.LF9_CONTRACTS["data"]).read_text(encoding="utf-8"))
        self.assertEqual(data["training_source"]["sha256"], bundle.EXPECTED_MEDIUM_SHA256)
        self.assertEqual(data["initial_DEV_R"]["checkpoint_sha256"], bundle.EXPECTED_DEV_R_SHA256)
        self.assertEqual(data["strong_ledger"]["file_sha256"], bundle.EXPECTED_STRONG_LEDGER_SHA256)
        self.assertEqual(data["strong_ledger"]["physics_1200_sha256"],
                         bundle.EXPECTED_PHYSICS_STREAM_SHA256)
        self.assertFalse(data["cv_ledger"]["runtime_sampling"])

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

    def test_hash_algorithms_match_materialized_ledger_identity(self):
        array = np.arange(12, dtype=np.int64).reshape(3, 4)
        expected_lf6 = hashlib.sha256(
            b"PHK_V23_LF6_ARRAY_V1\nvalues\n<i8\n[3,4]\n" + array.tobytes(order="C")
        ).hexdigest().upper()
        self.assertEqual(preflight._lf6_array_sha256("values", array), expected_lf6)
        expected_cv = hashlib.sha256(
            b"values<i8(3, 4)" + array.tobytes(order="C")
        ).hexdigest().upper()
        self.assertEqual(preflight._array_sha256("values", array), expected_cv)
        expected_semantic = hashlib.sha256(
            preflight.CV_DOMAIN + b"values" + bytes.fromhex(expected_cv)
        ).hexdigest().upper()
        self.assertEqual(preflight._semantic_sha256({"values": array}), expected_semantic)

    def test_materialized_strong_ledger_verifies_all_steps_and_fixed_pool(self):
        report = preflight._verify_strong_ledger(
            ROOT,
            ROOT / preflight.STRONG_LEDGER_RELATIVE.as_posix(),
            ROOT / preflight.STRONG_MANIFEST_RELATIVE.as_posix(),
        )
        self.assertEqual(report["p0_step_count"], 1200)
        self.assertEqual(report["p0_physics_rolling_sha256"],
                         preflight.EXPECTED_PHYSICS_STREAM_SHA256)
        self.assertEqual(report["fixed_blind_pool_sha256"],
                         preflight.EXPECTED_FIXED_POOL_SHA256)

    def test_materialized_cv_ledger_verifies_when_cpu_qualification_exists(self):
        qualification, qualification_manifest = bundle._locked_qualification_paths()
        if not qualification.exists():
            self.skipTest("valid pre-qualification state")
        payload = bundle._verify_qualification(qualification, qualification_manifest)
        self.assertEqual(payload["gate_outcome"], "LF9_CPU_QUALIFICATION_PASS")
        self.assertEqual(payload["scientific_optimizer_updates"], 0)
        report = preflight._verify_cv_ledger(
            ROOT,
            ROOT / preflight.CV_LEDGER_RELATIVE.as_posix(),
            ROOT / preflight.CV_MANIFEST_RELATIVE.as_posix(),
            payload,
        )
        self.assertEqual(report["counts"]["training_steps"], 1200)
        self.assertEqual(report["counts"]["patches_per_step"], 16)
        self.assertTrue(all(report["disjoint_checks"].values()))

    def test_output_root_must_be_campaign_namespaced_existing_and_empty(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            deployment = base / "deployment"
            deployment.mkdir()
            output = base / "lf9-run-test"
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

    def test_cloud_leakage_scan_forbids_local_reference_assets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            medium = root / "medium.npz"
            medium.write_bytes(b"allowed")
            self.assertEqual(preflight._forbidden(root, {"medium.npz"}), [])
            for name in ("nominal-fine.npz", "nominal-extra-fine.npz",
                         "direct-lf-only.pt", "stress-reference.json",
                         "phk_v23_lf9_evaluation.py"):
                (root / name).write_bytes(b"forbidden")
            forbidden = preflight._forbidden(root, {"medium.npz"})
            self.assertEqual(len(forbidden), 5)

    def test_launcher_uses_one_core_process_after_preflight(self):
        launcher = (ROOT / "cloud/phk_v23_lf9_autodl/run.sh").read_text(encoding="utf-8")
        self.assertIn("LF9_OUTPUT_ROOT", launcher)
        self.assertIn("find \"${LF9_OUTPUT_ROOT}\"", launcher)
        self.assertIn(
            'PYTHON_BIN="/root/autodl-tmp/envs/pinn-pcm-sci-py311/bin/python"',
            launcher,
        )
        self.assertIn('[[ ! -x "${PYTHON_BIN}" ]]', launcher)
        self.assertLess(launcher.index("preflight.py"),
                        launcher.index('"${PYTHON_BIN}" -m pinn_pcm_sci.phk_v23_lf9'))
        self.assertEqual(launcher.count('"${PYTHON_BIN}" -m pinn_pcm_sci.phk_v23_lf9'), 1)
        for flag in ("--medium-carrier", "--dev-r-checkpoint", "--strong-ledger",
                     "--strong-ledger-manifest", "--cv-ledger",
                     "--cv-ledger-manifest", "--cpu-qualification", "--source-identity"):
            self.assertIn(flag, launcher)
        runner = launcher[launcher.index('"${PYTHON_BIN}" -m pinn_pcm_sci.phk_v23_lf9'):]
        self.assertIn("--initial-checkpoint", runner)
        self.assertNotIn("--dev-r-checkpoint", runner)
        self.assertNotIn("--strong-ledger-manifest", runner)

    def test_launcher_cli_matches_core_and_core_owns_both_screens(self):
        option_strings = {
            option for action in core._parser()._actions for option in action.option_strings
        }
        self.assertTrue({
            "--output-root", "--medium-carrier", "--initial-checkpoint",
            "--strong-ledger", "--cv-ledger", "--cv-ledger-manifest",
            "--cpu-qualification", "--device", "--source-identity",
        }.issubset(option_strings))
        source = inspect.getsource(core.execute_gpu_campaign)
        self.assertEqual(core.ARM_ORDER, (core.ER_S, core.ER_CV))
        self.assertIn("for arm in ARM_ORDER", source)
        self.assertIn("except Exception as exc", source)
        self.assertIn("adjudicate_screens(arms)", source)
        self.assertIn("screen_outcomes", source)
        self.assertIn("selected_arm", source)
        runner_source = inspect.getsource(core)
        for generator in ("SobolEngine(", "LF0PhysicsBatchStream(",
                          "PhkCollocationSampler(", "materialize_cv_ledger("):
            self.assertNotIn(generator, runner_source)

    def test_method_contract_fixes_two_screens_and_conditional_control(self):
        method = json.loads((ROOT / bundle.LF9_CONTRACTS["method"]).read_text(encoding="utf-8"))
        self.assertEqual(method["arms"], {
            "ER_S": "EQUATION_ROUTED_ALL_STRONG_FORM",
            "ER_CV": "EQUATION_ROUTED_ELECTRIC_AND_PHASE_STRONG_THERMAL_CONTROL_VOLUME",
        })
        self.assertEqual(method["filter"]["screen_accepted_updates"], 200)
        self.assertEqual(method["filter"]["full_accepted_updates"], 1200)
        self.assertEqual(method["conditional_no_filter_control"]["updates"], 1200)
        self.assertFalse(method["conditional_no_filter_control"]["medium_audit"])
        self.assertFalse(method["identity"]["runtime_sampling"])
        self.assertFalse(method["identity"]["medium_gradient"])


if __name__ == "__main__":
    unittest.main()
