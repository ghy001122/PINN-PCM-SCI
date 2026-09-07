from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock

from pinn_pcm_sci import phk_v23_lf7 as lf7


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bundle = _load("lf7_bundle", ROOT / "cloud/phk_v23_lf7_autodl/build_bundle.py")
preflight = _load("lf7_preflight", ROOT / "cloud/phk_v23_lf7_autodl/preflight.py")


class LF7CloudTests(unittest.TestCase):
    @staticmethod
    def _qualification_payload():
        return {
            "schema_id": "phk-v23-lf7-cpu-qualification-v1",
            "task_id": bundle.TASK_ID,
            "gate_outcome": "LF7_CPU_QUALIFICATION_PASS",
            "gpu_execution_authorized_by_cpu_gate": True,
            "scientific_optimizer_updates": 0,
            "contracts": {
                role: {"path": relative, "sha256": bundle._sha256(ROOT / relative)}
                for role, relative in bundle.LF7_CONTRACTS.items()
            },
            "ledger": {
                "file_sha256": preflight.EXPECTED_LEDGER_SHA256,
                "manifest_sha256": preflight.EXPECTED_LEDGER_MANIFEST_SHA256,
                "semantic_sha256": preflight.EXPECTED_LEDGER_SEMANTIC_SHA256,
                "physics_1200_sha256": preflight.EXPECTED_PHYSICS_STREAM_SHA256,
                "fixed_blind_pool_sha256": preflight.EXPECTED_FIXED_POOL_SHA256,
            },
            "checks": {"identity": True},
        }

    def test_runtime_closure_is_activation_bound_and_reference_blind(self):
        required = {
            "pinn_pcm_sci/phk_v23_lf7.py",
            "pinn_pcm_sci/phk_v23_lf6.py",
            "tests/test_phk_v21_benchmark.py",
            "cloud/phk_v23_lf7_autodl/preflight.py",
            "cloud/phk_v23_lf7_autodl/run.sh",
        }
        self.assertTrue(required.issubset(bundle.STATIC_FILES))
        self.assertTrue(required.issubset(preflight.REQUIRED_RUNTIME))
        self.assertFalse(any(
            "evaluator" in path.lower() or "evaluation" in path.lower()
            for path in bundle.STATIC_FILES
        ))
        self.assertNotIn(
            "cloud/phk_v23_lf7_autodl/deployed-source-manifest.json",
            bundle.STATIC_FILES,
        )
        self.assertEqual(
            set(inspect.signature(bundle.build).parameters),
            {"qualification_path", "qualification_manifest_path", "archive_path", "base_commit"},
        )

    def test_frozen_cloud_inputs_match_data_contract_and_hashes(self):
        bundle._verify_frozen_inputs()
        self.assertEqual(bundle.EXPECTED_MEDIUM_SHA256, preflight.EXPECTED_MEDIUM_SHA256)
        self.assertEqual(bundle.EXPECTED_DEV_R_SHA256, preflight.EXPECTED_DEV_R_SHA256)
        self.assertEqual(bundle.EXPECTED_LEDGER_SHA256, preflight.EXPECTED_LEDGER_SHA256)
        self.assertEqual(
            bundle.EXPECTED_LEDGER_MANIFEST_SHA256,
            preflight.EXPECTED_LEDGER_MANIFEST_SHA256,
        )

    def test_activation_commit_byte_verifier_rejects_workspace_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "tracked.txt"
            path.write_bytes(b"activation")
            calls = [b"a" * 40 + b"\n", b"activation"]
            with mock.patch.object(bundle, "ROOT", root), mock.patch.object(
                bundle, "_git", side_effect=calls
            ):
                bundle._verify_activation_commit("a" * 40, ["tracked.txt"])
            path.write_bytes(b"dirty")
            calls = [b"a" * 40 + b"\n", b"activation"]
            with mock.patch.object(bundle, "ROOT", root), mock.patch.object(
                bundle, "_git", side_effect=calls
            ):
                with self.assertRaises(PermissionError):
                    bundle._verify_activation_commit("a" * 40, ["tracked.txt"])

    def test_cpu_qualification_schema_is_closed_across_builder_and_preflight(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact = root / "20260907T144634Z-phk-v23-lf7-cpu-qualification.json"
            payload = self._qualification_payload()
            artifact.write_text(json.dumps(payload), encoding="utf-8")
            preflight._verify_qualification(artifact, ROOT)

            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "schema_version": "run-manifest-v1",
                "run_id": bundle.EXPECTED_CPU_RUN_ID,
                "experiment_group_id": bundle.EXPECTED_CPU_EXPERIMENT_GROUP,
                "gate": bundle.EXPECTED_CPU_GATE,
                "execution_status": "COMPLETE",
                "gate_outcome": "LF7_CPU_QUALIFICATION_PASS",
                "artifacts": {
                    "compact_qualification": (
                        f"artifacts/{artifact.name}#sha256={bundle._sha256(artifact)}"
                    ),
                },
            }), encoding="utf-8")
            bundle._verify_qualification(artifact, manifest)

            payload["scientific_optimizer_updates"] = 1
            artifact.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(PermissionError):
                preflight._verify_qualification(artifact, ROOT)

    def test_lf6_materialized_ledger_verifies_all_steps_and_fixed_pool(self):
        report = preflight._verify_ledger(
            ROOT,
            ROOT / preflight.LEDGER_RELATIVE.as_posix(),
            ROOT / preflight.LEDGER_MANIFEST_RELATIVE.as_posix(),
        )
        self.assertEqual(report["p0_step_count"], 1200)
        self.assertEqual(
            report["p0_physics_rolling_sha256"],
            preflight.EXPECTED_PHYSICS_STREAM_SHA256,
        )
        self.assertEqual(
            report["fixed_blind_pool_sha256"],
            preflight.EXPECTED_FIXED_POOL_SHA256,
        )
        self.assertEqual(
            report["semantic_sha256"],
            preflight.EXPECTED_LEDGER_SEMANTIC_SHA256,
        )

    def test_hash_algorithms_preserve_lf6_ledger_identity(self):
        import numpy as np

        array = np.arange(12, dtype=np.int64).reshape(3, 4)
        expected = hashlib.sha256(
            b"PHK_V23_LF6_ARRAY_V1\nvalues\n<i8\n[3,4]\n"
            + array.tobytes(order="C")
        ).hexdigest().upper()
        self.assertEqual(preflight._array_sha256("values", array), expected)
        semantic = hashlib.sha256(b"PHK_V23_LF6_MATERIALIZED_LEDGER_V1\n")
        semantic.update(f"values={expected}\n".encode("ascii"))
        self.assertEqual(
            preflight._semantic_sha256({"values": expected}),
            semantic.hexdigest().upper(),
        )

    def test_exact_dev_r_metadata_is_phase_only_endpoint_not_optimizer_resume(self):
        report = preflight._validate_dev_r_checkpoint(ROOT / preflight.DEV_R_RELATIVE.as_posix())
        self.assertEqual(report["role"], "DEV_R_EVENT_FRONTIER_RANK_BAND")
        self.assertEqual(report["optimizer_update"], 400)
        self.assertEqual(report["sha256"], preflight.EXPECTED_DEV_R_SHA256)

    def test_output_root_must_be_exact_existing_and_empty(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            deployment = base / "deployment"
            deployment.mkdir()
            output = base / preflight.EXPECTED_OUTPUT_BASENAME
            output.mkdir()
            with mock.patch.object(
                preflight, "EXPECTED_REMOTE_OUTPUT_IDENTITY", output.as_posix()
            ):
                report = preflight._verify_output_root(deployment, output)
                self.assertTrue(report["empty"])
                (output / "partial.txt").write_text("partial", encoding="utf-8")
                with self.assertRaises(RuntimeError):
                    preflight._verify_output_root(deployment, output)

    def test_safe_path_and_reference_leakage_scan(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            with self.assertRaises(PermissionError):
                preflight._safe(root, "../escape")
            medium = root / "medium.npz"
            medium.write_bytes(b"allowed")
            self.assertEqual(preflight._forbidden(root, {"medium.npz"}), [])
            (root / "direct-lf-only.pt").write_bytes(b"forbidden")
            (root / "nominal-extra-fine.npz").write_bytes(b"forbidden")
            self.assertEqual(
                preflight._forbidden(root, {"medium.npz"}),
                ["direct-lf-only.pt", "nominal-extra-fine.npz"],
            )

    def test_launcher_enforces_empty_root_preflight_and_single_ordered_runner(self):
        launcher = (ROOT / "cloud/phk_v23_lf7_autodl/run.sh").read_text(encoding="utf-8")
        self.assertNotIn("Sobol", launcher)
        self.assertIn("LF7_OUTPUT_ROOT", launcher)
        self.assertIn("find \"${LF7_OUTPUT_ROOT}\"", launcher)
        self.assertLess(launcher.index("preflight.py"), launcher.index("python -m pinn_pcm_sci.phk_v23_lf7"))
        self.assertEqual(launcher.count("python -m pinn_pcm_sci.phk_v23_lf7"), 1)
        self.assertIn("complete P0-S", launcher)
        self.assertIn("reload exact DEV-R", launcher)
        self.assertIn("fresh optimizer before P0-F", launcher)
        for flag in (
            "--medium-carrier", "--dev-r-checkpoint", "--materialized-ledger",
            "--ledger-manifest", "--cpu-qualification", "--source-identity",
        ):
            self.assertIn(flag, launcher)
        runner = launcher[launcher.index("python -m pinn_pcm_sci.phk_v23_lf7"):]
        self.assertIn("--initial-checkpoint", runner)
        self.assertNotIn("--dev-r-checkpoint", runner)
        self.assertNotIn("--ledger-manifest", runner)

    def test_runner_parser_matches_launcher_and_campaign_orders_fresh_arms(self):
        args = lf7._parser().parse_args([
            "--output-root", "out",
            "--medium-carrier", "medium.npz",
            "--initial-checkpoint", "dev-r.pt",
            "--materialized-ledger", "ledger.npz",
            "--cpu-qualification", "qualification.json",
            "--source-identity", "LF7-BUNDLE-TEST",
            "--device", "cuda:0",
        ])
        self.assertEqual(args.initial_checkpoint, Path("dev-r.pt"))
        self.assertEqual(args.materialized_ledger, Path("ledger.npz"))

        small_source = inspect.getsource(lf7._run_small)
        filter_source = inspect.getsource(lf7._run_filter)
        self.assertIn("load_dev_r_model", small_source)
        self.assertIn("_make_optimizer", small_source)
        self.assertIn("load_dev_r_model", filter_source)
        self.assertIn("_make_optimizer", filter_source)

        arm_calls = []
        small = {
            "numerical_valid": True,
            "attempted_updates": 1200,
            "safety_gate": {"passed": True},
        }
        filtered = {
            "numerical_valid": True,
            "attempted_updates": 1200,
            "safety_gate": {"passed": True},
            "disposition": "COMPLETE",
        }

        def fake_small(**kwargs):
            arm_calls.append((lf7.P0_S, kwargs["initial_checkpoint"]))
            return small

        def fake_filter(**kwargs):
            arm_calls.append((lf7.P0_F, kwargs["initial_checkpoint"]))
            return filtered

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "empty-existing-output"
            output.mkdir()
            ledger_path = Path(temporary) / "ledger.npz"
            ledger_path.write_bytes(b"test-ledger")
            ledger = SimpleNamespace(physics_sha256=lf7.EXPECTED_PHYSICS_SHA256)
            with mock.patch.multiple(
                lf7,
                load_contracts=mock.DEFAULT,
                read_cpu_qualification=mock.DEFAULT,
                build_training_config=mock.DEFAULT,
                load_case_physics=mock.DEFAULT,
                load_medium_dataset=mock.DEFAULT,
                MaterializedPhysicsLedger=mock.DEFAULT,
                _run_small=mock.DEFAULT,
                _run_filter=mock.DEFAULT,
                _write_json_exclusive=mock.DEFAULT,
            ) as patched, mock.patch.object(lf7.torch.cuda, "is_available", return_value=True), mock.patch.object(
                lf7.torch.cuda, "get_device_name", return_value="Tesla V100-PCIE-32GB"
            ), mock.patch.object(lf7.torch.cuda, "manual_seed_all"):
                patched["load_contracts"].return_value = {}
                patched["read_cpu_qualification"].return_value = {
                    "partition_sha256": lf7.EXPECTED_PARTITION_SHA256,
                }
                patched["build_training_config"].return_value = SimpleNamespace(case_control="FULL")
                patched["load_case_physics"].return_value = (object(), "program", "object")
                patched["load_medium_dataset"].return_value = SimpleNamespace(
                    partition_sha256=lf7.EXPECTED_PARTITION_SHA256,
                )
                patched["MaterializedPhysicsLedger"].return_value = ledger
                patched["_run_small"].side_effect = fake_small
                patched["_run_filter"].side_effect = fake_filter
                lf7.execute_gpu_campaign(
                    output_root=output,
                    medium_carrier=Path("medium.npz"),
                    initial_checkpoint=Path("dev-r.pt"),
                    materialized_ledger=ledger_path,
                    cpu_qualification_path=Path("qualification.json"),
                    device_name="cuda:0",
                    source_identity="LF7-BUNDLE-TEST",
                )
        self.assertEqual(
            arm_calls,
            [(lf7.P0_S, Path("dev-r.pt")), (lf7.P0_F, Path("dev-r.pt"))],
        )


if __name__ == "__main__":
    unittest.main()
