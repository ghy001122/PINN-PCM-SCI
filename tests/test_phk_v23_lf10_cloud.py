from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bundle = _load("lf10_bundle", ROOT / "cloud/phk_v23_lf10_autodl/build_bundle.py")
preflight = _load("lf10_preflight", ROOT / "cloud/phk_v23_lf10_autodl/preflight.py")


class LF10CloudTests(unittest.TestCase):
    def test_runtime_closure_is_activation_bound_and_reference_blind(self):
        required = {
            "configs/phk_v23/lf10_write_allowlist_lock.json",
            "pinn_pcm_sci/phk_v23_lf10.py",
            "pinn_pcm_sci/phk_v23_lf10_qualification.py",
            "pinn_pcm_sci/phk_v23_lf9.py",
            "pinn_pcm_sci/phk_v23_lf8.py",
            "pinn_pcm_sci/phk_v23_lf6.py",
            "pinn_pcm_sci/phk_v23_lf4.py",
            "pinn_pcm_sci/phk_v23_lf3.py",
            "cloud/phk_v23_lf10_autodl/preflight.py",
            "cloud/phk_v23_lf10_autodl/run.sh",
            "tests/test_phk_v21_benchmark.py",
        }
        self.assertTrue(required.issubset(bundle.STATIC_FILES))
        self.assertTrue(required.issubset(preflight.REQUIRED_RUNTIME))
        self.assertFalse(any("evaluation" in path.lower() for path in bundle.STATIC_FILES))
        self.assertNotIn("cloud/phk_v23_lf10_autodl/deployed-source-manifest.json",
                         bundle.STATIC_FILES)
        self.assertEqual(preflight.EXPECTED_INPUT_ROLES, {
            "medium", "lf3_t0_checkpoint", "dev_r_checkpoint", "strong_ledger",
            "strong_ledger_manifest", "lf10_ledger", "lf10_ledger_manifest",
            "cpu_qualification",
        })

    def test_locked_cpu_paths_and_frozen_inputs_are_exact(self):
        qualification, manifest = bundle._locked_qualification_paths()
        self.assertEqual(
            qualification.relative_to(ROOT).as_posix(),
            "docs/experiment/artifacts/20260909T101615Z-phk-v23-lf10-cpu-qualification.json",
        )
        self.assertEqual(
            manifest.relative_to(ROOT).as_posix(),
            "docs/experiment/manifests/20260909T101615Z-phk-v23-lf10-cpu-qualification.json",
        )
        for role, path in {
            "medium": bundle.MEDIUM,
            "lf3_t0_checkpoint": bundle.LF3_T0_CHECKPOINT,
            "dev_r_checkpoint": bundle.DEV_R_CHECKPOINT,
            "strong_ledger": bundle.STRONG_LEDGER,
            "strong_ledger_manifest": bundle.STRONG_LEDGER_MANIFEST,
            "lf10_ledger": bundle.LF10_LEDGER,
            "lf10_ledger_manifest": bundle.LF10_LEDGER_MANIFEST,
        }.items():
            self.assertTrue(path.is_file())
            self.assertEqual(bundle._sha256(path), bundle.EXPECTED_SHA256[role])
        data = json.loads((ROOT / bundle.LF10_CONTRACTS["data"]).read_text(encoding="utf-8"))
        self.assertEqual(data["medium"]["path"], bundle.MEDIUM.relative_to(ROOT).as_posix())
        self.assertEqual(data["LF3_T0"]["checkpoint_path"], bundle.LF3_T0_CHECKPOINT.relative_to(ROOT).as_posix())
        self.assertEqual(data["DEV_R"]["checkpoint_path"], bundle.DEV_R_CHECKPOINT.relative_to(ROOT).as_posix())
        self.assertFalse(data["LF10_ledger"]["runtime_sampling"])

    def test_same_batch_audit_array_is_exactly_bound(self):
        qualification_path, _ = bundle._locked_qualification_paths()
        qualification = json.loads(qualification_path.read_text(encoding="utf-8"))
        bundle._verify_same_batch_audit(qualification)
        identity = qualification["ledger"]
        manifest = json.loads(bundle.LF10_LEDGER_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(identity["sha256"], bundle.EXPECTED_SHA256["lf10_ledger"])
        self.assertEqual(identity["manifest_sha256"], bundle.EXPECTED_SHA256["lf10_ledger_manifest"])
        self.assertEqual(identity["arrays"]["audit_baselines"], bundle.EXPECTED_AUDIT_BASELINES)
        self.assertEqual(manifest["arrays"]["audit_baselines"], bundle.EXPECTED_AUDIT_BASELINES)
        self.assertEqual(preflight.EXPECTED_SCIENTIFIC_ORDER, [
            "MATCHED_CTRL_PROJ_SCREENS",
            "CONDITIONAL_SELECTED_FULL_REFINEMENT",
            "INTERFACE_REPLICATION_STREAMS_23_29",
            "FORGETTING_REPLICATION_STREAMS_23_29",
        ])

    def test_activation_byte_verifier_rejects_workspace_drift(self):
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

    def test_deployment_identity_definition_is_deterministic(self):
        base_commit = "a" * 40
        files = {"b.py": "B" * 64, "a.py": "A" * 64}
        inputs = {"z": {"sha256": "D" * 64}, "m": {"sha256": "C" * 64}}
        lines = [f"base_commit={base_commit.upper()}\n"]
        lines.extend(f"source:{path}={digest}\n" for path, digest in sorted(files.items()))
        lines.extend(f"input:{role}={record['sha256']}\n" for role, record in sorted(inputs.items()))
        expected = "LF10-BUNDLE-" + hashlib.sha256("".join(lines).encode("ascii")).hexdigest().upper()
        self.assertRegex(expected, r"^LF10-BUNDLE-[0-9A-F]{64}$")

    def test_exact_cpu_qualification_shape_is_accepted(self):
        payload = {
            "schema_id": "phk-v23-lf10-cpu-qualification-v1",
            "task_id": preflight.TASK_ID,
            "gate_outcome": "LF10_CPU_QUALIFICATION_PASS",
            "scientific_optimizer_updates": 0,
            "gpu_execution_authorized_by_cpu_gate": True,
            "gpu_used": False,
            "checks": {"qualified": True},
            "ledger": {"sha256": "A" * 64},
            "reference_boundary": {
                "fine_read": False,
                "extra_fine_read": False,
                "direct_LF_ONLY_read": False,
                "frozen_evaluator_read": False,
                "stress_read": False,
            },
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "qualification.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(preflight._verify_qualification(path, Path(temporary)), payload)
        self.assertEqual(bundle._ledger_identity(payload)["sha256"], "A" * 64)

    def test_output_root_must_be_namespaced_existing_and_empty(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary).resolve()
            deployment = parent / "deployment"
            deployment.mkdir()
            output = parent / "lf10-run-test"
            output.mkdir()
            with mock.patch.object(preflight, "EXPECTED_REMOTE_PARENT", parent.as_posix()):
                self.assertTrue(preflight._verify_output_root(deployment, output)["empty"])
                (output / "partial.txt").write_text("partial", encoding="utf-8")
                with self.assertRaises(RuntimeError):
                    preflight._verify_output_root(deployment, output)

    def test_preflight_requires_exact_v100(self):
        good = mock.Mock()
        good.is_available.return_value = True
        good.get_device_name.return_value = "Tesla V100-PCIE-32GB"
        self.assertEqual(preflight._verify_gpu(good), "Tesla V100-PCIE-32GB")
        bad = mock.Mock()
        bad.is_available.return_value = True
        bad.get_device_name.return_value = "NVIDIA A100-SXM4-40GB"
        with self.assertRaises(RuntimeError):
            preflight._verify_gpu(bad)

    def test_cloud_leakage_scan_forbids_local_reference_assets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            medium = root / "medium.npz"
            medium.write_bytes(b"allowed")
            self.assertEqual(preflight._forbidden(root, {"medium.npz"}), [])
            for name in ("nominal-fine.npz", "nominal-extra-fine.npz",
                         "direct-lf-only.pt", "stress-reference.json",
                         "phk_v23_lf10_evaluation.py"):
                (root / name).write_bytes(b"forbidden")
            self.assertEqual(len(preflight._forbidden(root, {"medium.npz"})), 5)

    def test_launcher_matches_frozen_cli_and_uses_one_core_process(self):
        launcher = (ROOT / "cloud/phk_v23_lf10_autodl/run.sh").read_text(encoding="utf-8")
        self.assertIn('PYTHON_BIN="/root/autodl-tmp/envs/pinn-pcm-sci-py311/bin/python"', launcher)
        self.assertLess(launcher.index("preflight.py"),
                        launcher.index('"${PYTHON_BIN}" -m pinn_pcm_sci.phk_v23_lf10'))
        self.assertEqual(launcher.count('"${PYTHON_BIN}" -m pinn_pcm_sci.phk_v23_lf10'), 1)
        for flag in (
            "--output-root", "--medium-carrier", "--lf3-t0-checkpoint",
            "--dev-r-checkpoint", "--strong-ledger", "--lf10-ledger",
            "--lf10-ledger-manifest", "--cpu-qualification",
            "--source-identity", "--device",
        ):
            self.assertIn(flag, launcher)

    def test_core_cli_and_summary_schema_match_cloud_contract(self):
        runner = (ROOT / "pinn_pcm_sci/phk_v23_lf10.py").read_text(encoding="utf-8")
        for flag in (
            "--output-root", "--medium-carrier", "--lf3-t0-checkpoint",
            "--dev-r-checkpoint", "--strong-ledger", "--lf10-ledger",
            "--lf10-ledger-manifest", "--cpu-qualification",
            "--source-identity", "--device",
        ):
            self.assertIn(f'parser.add_argument("{flag}"', runner)
        self.assertIn('"schema_id": "phk-v23-lf10-reference-blind-run-summary-v1"', runner)
        for key in (
            "direction_arms", "feasible_direction_outcome", "full_refinement",
            "interface_replications", "interface_replication_outcome",
            "forgetting_replications", "forgetting_replication_outcome",
            "primary_outcome_prelocal", "track_isolation", "errors",
        ):
            self.assertIn(f'"{key}"', runner)

    def test_active_paper_data_cannot_generate_terminal_figures(self):
        payload = json.loads((ROOT / "paper/paper_v23/figures/data/lf10_terminal_metrics.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["campaign_state"], "ACTIVE")
        self.assertIsNone(payload["terminal_outcome"])
        self.assertEqual(payload["claim_boundary"], "ACTIVE_NULL_SCAFFOLD_NO_LF10_SCIENTIFIC_RESULT")


if __name__ == "__main__":
    unittest.main()
