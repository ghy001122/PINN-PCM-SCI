from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


PREFLIGHT_PATH = (
    Path(__file__).resolve().parents[1]
    / "cloud"
    / "phk_v23_lf2_autodl"
    / "preflight.py"
)
BUILD_BUNDLE_PATH = PREFLIGHT_PATH.with_name("build_bundle.py")
SPEC = importlib.util.spec_from_file_location("phk_v23_lf2_cloud_preflight", PREFLIGHT_PATH)
assert SPEC is not None and SPEC.loader is not None
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)
BUILD_SPEC = importlib.util.spec_from_file_location(
    "phk_v23_lf2_cloud_build_bundle", BUILD_BUNDLE_PATH
)
assert BUILD_SPEC is not None and BUILD_SPEC.loader is not None
build_bundle = importlib.util.module_from_spec(BUILD_SPEC)
BUILD_SPEC.loader.exec_module(build_bundle)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class LF2CloudPreflightTests(unittest.TestCase):
    def test_runtime_closure_contains_LF2_without_evaluator(self) -> None:
        required = {
            "pinn_pcm_sci/phk_v23_lf2.py",
            "pinn_pcm_sci/phk_v23_lf0.py",
            "pinn_pcm_sci/phk_v23_lf1.py",
            "tests/test_phk_v21_benchmark.py",
        }
        self.assertTrue(required.issubset(set(build_bundle.STATIC_FILES)))
        self.assertTrue(required.issubset(preflight.REQUIRED_RUNTIME))
        self.assertFalse(
            any("evaluator" in name.lower() for name in build_bundle.STATIC_FILES)
        )

    def test_isolated_runtime_closure_loads_physics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            repository = PREFLIGHT_PATH.parents[2]
            for relative in build_bundle.STATIC_FILES:
                source = repository / relative
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(root)
            completed = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "from pinn_pcm_sci.phk_v22r_training import "
                        "load_case_physics; load_case_physics('FULL'); "
                        "print('ISOLATED_PHYSICS_LOAD_VALID')"
                    ),
                ],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                completed.returncode,
                0,
                msg=f"stdout={completed.stdout}\nstderr={completed.stderr}",
            )
            self.assertIn("ISOLATED_PHYSICS_LOAD_VALID", completed.stdout)

    def test_safe_deployed_path_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(PermissionError):
                preflight._safe(Path(temporary).resolve(), "../outside.py")

    def test_forbidden_scan_allows_only_medium_and_exact_parent_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            for relative in (preflight.MEDIUM_RELATIVE, preflight.CHECKPOINT_RELATIVE):
                exact = root / Path(*relative.parts)
                exact.parent.mkdir(parents=True, exist_ok=True)
                exact.write_bytes(b"allowed")
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
            lines = "".join(
                f"{name}={digest}\n" for name, digest in sorted(files.items())
            )
            identity = (
                "LF2-BUNDLE-"
                + hashlib.sha256(lines.encode("utf-8")).hexdigest().upper()
            )
            manifest_path = (
                root
                / "cloud"
                / "phk_v23_lf2_autodl"
                / "deployed-source-manifest.json"
            )
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
                self.assertEqual(loaded["source_identity"], identity)
                second.write_text("changed", encoding="utf-8")
                with self.assertRaises(ValueError):
                    preflight._manifest(root, identity)
            finally:
                preflight.REQUIRED_RUNTIME = original_required


if __name__ == "__main__":
    unittest.main()
