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


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bundle = _load("lf6_bundle", ROOT / "cloud/phk_v23_lf6_autodl/build_bundle.py")
preflight = _load("lf6_preflight", ROOT / "cloud/phk_v23_lf6_autodl/preflight.py")


def _rolling(domain: str, values: list[str]) -> str:
    digest = hashlib.sha256(domain.encode("ascii"))
    for value in values:
        digest.update(bytes.fromhex(value))
    return digest.hexdigest().upper()


class LF6CloudTests(unittest.TestCase):
    def test_runtime_closure_is_reference_blind_and_materialized(self):
        required = {
            "pinn_pcm_sci/phk_v23_lf6.py",
            "pinn_pcm_sci/phk_v23_lf6_qualification.py",
            "pinn_pcm_sci/phk_v23_lf5.py",
            "tests/test_phk_v21_benchmark.py",
            "cloud/phk_v23_lf6_autodl/run.sh",
        }
        self.assertTrue(required.issubset(bundle.STATIC_FILES))
        self.assertTrue(required.issubset(preflight.REQUIRED_RUNTIME))
        self.assertFalse(any("evaluator" in path.lower() or "evaluation" in path.lower() for path in bundle.STATIC_FILES))
        launcher = (ROOT / "cloud/phk_v23_lf6_autodl/run.sh").read_text(encoding="utf-8")
        self.assertNotIn("Sobol", launcher)
        self.assertIn("--materialized-ledger", launcher)
        self.assertIn("--allow-dev-m-fallback-input", launcher)
        self.assertIn("LF6_ALLOW_DEV_M_FALLBACK_INPUT", launcher)

    def test_builder_requires_explicit_dev_m_authorization(self):
        signature = inspect.signature(bundle.build)
        self.assertFalse(signature.parameters["allow_dev_m_fallback_input"].default)
        with self.assertRaises(PermissionError):
            bundle.build(
                qualification_path=Path("missing"), ledger_path=Path("missing"),
                ledger_manifest_path=Path("missing"), archive_path=Path("missing"),
                base_commit="0" * 40, dev_m_checkpoint=Path("present-but-unauthorized"),
                allow_dev_m_fallback_input=False,
            )

    def test_activation_commit_byte_verifier_rejects_workspace_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "tracked.txt"
            path.write_bytes(b"activation")
            calls = [b"a" * 40 + b"\n", b"activation"]
            with mock.patch.object(bundle, "ROOT", root), mock.patch.object(bundle, "_git", side_effect=calls):
                bundle._verify_activation_commit("a" * 40, ["tracked.txt"])
            path.write_bytes(b"dirty")
            calls = [b"a" * 40 + b"\n", b"activation"]
            with mock.patch.object(bundle, "ROOT", root), mock.patch.object(bundle, "_git", side_effect=calls):
                with self.assertRaises(PermissionError):
                    bundle._verify_activation_commit("a" * 40, ["tracked.txt"])

    def test_array_and_semantic_hashes_match_frozen_algorithm(self):
        array = np.arange(12, dtype=np.int64).reshape(3, 4)
        expected = hashlib.sha256(
            b"PHK_V23_LF6_ARRAY_V1\nvalues\n<i8\n[3,4]\n" + array.tobytes(order="C")
        ).hexdigest().upper()
        self.assertEqual(preflight._array_sha256("values", array), expected)
        digest = hashlib.sha256(b"PHK_V23_LF6_MATERIALIZED_LEDGER_V1\n")
        digest.update(f"values={expected}\n".encode("ascii"))
        self.assertEqual(preflight._semantic_sha256({"values": expected}), digest.hexdigest().upper())

    def test_full_ledger_verification_reads_arrays_and_step_hashes(self):
        domains = list(preflight.STREAM_IDENTITIES)
        step_values = {
            domains[0]: ["00" * 32] * 400,
            domains[1]: ["11" * 32] * 400,
            domains[2]: ["22" * 32] * 1200,
        }
        arrays = {
            "base_batch_sha256": np.asarray(step_values[domains[0]], dtype="S64"),
            "spatial_batch_sha256": np.asarray(step_values[domains[1]], dtype="S64"),
            "p0_batch_sha256": np.asarray(step_values[domains[2]], dtype="S64"),
            "coordinates": np.arange(30, dtype=np.float64).reshape(10, 3),
        }
        for name in ("interior", "left", "right", "bottom", "top", "initial"):
            arrays[f"fixed_{name}"] = np.arange(6, dtype=np.float64).reshape(2, 3)
        expected_streams = {domain: _rolling(domain, values) for domain, values in step_values.items()}
        fixed_sha256 = preflight._fixed_pool_sha256(arrays)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            ledger = root / "ledger.npz"
            np.savez(ledger, **arrays)
            array_records = {
                name: {"shape": list(value.shape), "dtype": value.dtype.str, "sha256": preflight._array_sha256(name, value)}
                for name, value in arrays.items()
            }
            semantic = preflight._semantic_sha256({name: record["sha256"] for name, record in array_records.items()})
            streams = {
                "base_400_sha256": expected_streams[domains[0]],
                "spatial_400_sha256": expected_streams[domains[1]],
                "P0_physics_1200_sha256": expected_streams[domains[2]],
                "fixed_blind_pool_sha256": fixed_sha256,
            }
            manifest = root / "ledger_manifest.json"
            manifest_payload = {
                "schema_id": "phk-v23-lf6-materialized-ledger-manifest-v1",
                "task_id": preflight.TASK_ID,
                "runtime_sampling_permitted": False,
                "ledger": preflight._record(root, ledger),
                "semantic_sha256": semantic,
                "arrays": array_records,
                "streams": streams,
            }
            manifest.write_text(json.dumps(manifest_payload), encoding="utf-8")
            qualification = {
                "ledger": {
                    **preflight._record(root, ledger),
                    "manifest_path": manifest.relative_to(root).as_posix(),
                    "manifest_sha256": preflight._sha256(manifest),
                    "semantic_sha256": semantic,
                    "arrays": array_records,
                    "streams": streams,
                }
            }
            with mock.patch.dict(preflight.STREAM_IDENTITIES, expected_streams, clear=True), mock.patch.object(preflight, "EXPECTED_FIXED_POOL_SHA256", fixed_sha256):
                report = preflight._verify_ledger(root=root, ledger_path=ledger, ledger_manifest_path=manifest, qualification=qualification)
            self.assertEqual(report["array_count"], len(arrays))
            self.assertEqual(report["semantic_sha256"], semantic)

    def test_safe_path_and_leakage_scan(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            with self.assertRaises(PermissionError):
                preflight._safe(root, "../escape")
            allowed = root / "medium.npz"
            allowed.write_bytes(b"ok")
            self.assertEqual(preflight._forbidden(root, {"medium.npz"}), [])
            (root / "extra-fine.npz").write_bytes(b"bad")
            self.assertEqual(preflight._forbidden(root, {"medium.npz"}), ["extra-fine.npz"])


if __name__ == "__main__":
    unittest.main()
