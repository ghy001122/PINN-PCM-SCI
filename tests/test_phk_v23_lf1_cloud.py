from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


PREFLIGHT_PATH = (
    Path(__file__).resolve().parents[1]
    / "cloud"
    / "phk_v23_lf1_autodl"
    / "preflight.py"
)
BUILD_BUNDLE_PATH = PREFLIGHT_PATH.with_name("build_bundle.py")
SPEC = importlib.util.spec_from_file_location("phk_v23_lf1_cloud_preflight", PREFLIGHT_PATH)
assert SPEC is not None and SPEC.loader is not None
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)
BUILD_SPEC = importlib.util.spec_from_file_location(
    "phk_v23_lf1_cloud_build_bundle", BUILD_BUNDLE_PATH
)
assert BUILD_SPEC is not None and BUILD_SPEC.loader is not None
build_bundle = importlib.util.module_from_spec(BUILD_SPEC)
BUILD_SPEC.loader.exec_module(build_bundle)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class LF1CloudPreflightTests(unittest.TestCase):
    def test_runtime_closure_includes_v21_hash_bound_test_dependency(self) -> None:
        relative = "tests/test_phk_v21_benchmark.py"
        self.assertIn(relative, build_bundle.STATIC_FILES)
        self.assertIn(relative, preflight.REQUIRED_RUNTIME)

    def test_safe_deployed_path_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            with self.assertRaises(PermissionError):
                preflight._safe(root, "../outside.py")

    def test_forbidden_scan_allows_only_declared_medium_carrier(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            medium = root / Path(*preflight.MEDIUM_RELATIVE.parts)
            medium.parent.mkdir(parents=True)
            medium.write_bytes(b"medium")
            self.assertEqual(preflight._forbidden(root), [])
            forbidden = root / "outputs" / "nominal-extra-fine-result.npz"
            forbidden.write_bytes(b"reference")
            self.assertEqual(
                preflight._forbidden(root),
                ["outputs/nominal-extra-fine-result.npz"],
            )

    def test_manifest_aggregate_binds_every_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            first = root / "one.txt"
            second = root / "nested" / "two.txt"
            second.parent.mkdir()
            first.write_text("one", encoding="utf-8")
            second.write_text("two", encoding="utf-8")
            files = {"one.txt": _sha(first), "nested/two.txt": _sha(second)}
            lines = "".join(f"{name}={digest}\n" for name, digest in sorted(files.items()))
            identity = "LF1-BUNDLE-" + hashlib.sha256(lines.encode("utf-8")).hexdigest().upper()
            manifest_path = root / "cloud" / "phk_v23_lf1_autodl" / "deployed-source-manifest.json"
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_id": preflight.EXPECTED_MANIFEST_SCHEMA,
                        "identity_definition": preflight.IDENTITY_DEFINITION,
                        "source_identity": identity,
                        "files": files,
                    }
                ),
                encoding="utf-8",
            )
            original_required = preflight.REQUIRED_RUNTIME
            try:
                preflight.REQUIRED_RUNTIME = frozenset(files)
                loaded = preflight._manifest(root, identity)
            finally:
                preflight.REQUIRED_RUNTIME = original_required
            self.assertEqual(loaded["source_identity"], identity)
            second.write_text("changed", encoding="utf-8")
            with self.assertRaises(ValueError):
                original_required = preflight.REQUIRED_RUNTIME
                try:
                    preflight.REQUIRED_RUNTIME = frozenset(files)
                    preflight._manifest(root, identity)
                finally:
                    preflight.REQUIRED_RUNTIME = original_required


if __name__ == "__main__":
    unittest.main()
