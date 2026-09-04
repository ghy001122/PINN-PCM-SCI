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


ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT_PATH = ROOT / "cloud" / "phk_v23_lf3_autodl" / "preflight.py"
BUILD_PATH = PREFLIGHT_PATH.with_name("build_bundle.py")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


preflight = _load("lf3_preflight", PREFLIGHT_PATH)
build_bundle = _load("lf3_bundle", BUILD_PATH)


class LF3CloudTests(unittest.TestCase):
    def test_runtime_closure_has_lf3_and_no_evaluator(self):
        required = {"pinn_pcm_sci/phk_v23_lf3.py", "pinn_pcm_sci/phk_v23_lf2.py", "tests/test_phk_v21_benchmark.py"}
        self.assertTrue(required.issubset(build_bundle.STATIC_FILES))
        self.assertTrue(required.issubset(preflight.REQUIRED_RUNTIME))
        self.assertFalse(any("evaluator" in path.lower() for path in build_bundle.STATIC_FILES))

    def test_safe_path_rejects_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(PermissionError): preflight._safe(Path(temporary), "../escape")

    def test_isolated_runtime_closure_imports_lf3_and_loads_physics(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in build_bundle.STATIC_FILES:
                source = ROOT / relative
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(root)
            completed = subprocess.run(
                [sys.executable, "-c", "from pinn_pcm_sci.phk_v23_lf3 import load_contracts; from pinn_pcm_sci.phk_v22r_training import load_case_physics; load_contracts(); load_case_physics('FULL'); print('LF3_RUNTIME_OK')"],
                cwd=root, env=environment, capture_output=True, text=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, msg=f"stdout={completed.stdout}\nstderr={completed.stderr}")
            self.assertIn("LF3_RUNTIME_OK", completed.stdout)

    def test_forbidden_scan_allows_only_exact_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in (preflight.MEDIUM_RELATIVE, preflight.CHECKPOINT_RELATIVE):
                path = root / Path(*relative.parts); path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b"ok")
            self.assertEqual(preflight._forbidden(root), [])
            bad = root / "outputs" / "nominal-extra-fine.npz"; bad.write_bytes(b"bad")
            self.assertEqual(preflight._forbidden(root), ["outputs/nominal-extra-fine.npz"])

    def test_manifest_aggregate_binds_all_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            one = root / "one"; two = root / "two"; one.write_text("1"); two.write_text("2")
            files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest().upper() for p in (one,two)}
            lines = "".join(f"{name}={digest}\n" for name,digest in sorted(files.items()))
            identity = "LF3-BUNDLE-" + hashlib.sha256(lines.encode()).hexdigest().upper()
            path = root / "cloud" / "phk_v23_lf3_autodl" / "deployed-source-manifest.json"; path.parent.mkdir(parents=True)
            path.write_text(json.dumps({"schema_id": preflight.EXPECTED_MANIFEST_SCHEMA, "identity_definition": preflight.IDENTITY_DEFINITION, "source_identity": identity, "files": files}))
            original_root, original_required = preflight.ROOT, preflight.REQUIRED_RUNTIME
            try:
                preflight.ROOT = root; preflight.REQUIRED_RUNTIME = frozenset(files)
                self.assertEqual(preflight._manifest(root, identity)["source_identity"], identity)
                two.write_text("changed")
                with self.assertRaises(ValueError): preflight._manifest(root, identity)
            finally:
                preflight.ROOT, preflight.REQUIRED_RUNTIME = original_root, original_required


if __name__ == "__main__": unittest.main()
