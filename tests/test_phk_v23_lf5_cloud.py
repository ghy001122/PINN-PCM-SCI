from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT=Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec=importlib.util.spec_from_file_location(name,path); assert spec and spec.loader; module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


bundle=_load("lf5_bundle",ROOT/"cloud/phk_v23_lf5_autodl/build_bundle.py")
preflight=_load("lf5_preflight",ROOT/"cloud/phk_v23_lf5_autodl/preflight.py")


class LF5CloudTests(unittest.TestCase):
    def test_runtime_contains_lf5_runner_and_no_evaluator(self):
        required={"pinn_pcm_sci/phk_v23_lf5.py","pinn_pcm_sci/phk_v23_lf4.py","cloud/phk_v23_lf5_autodl/run.sh"}; self.assertTrue(required.issubset(bundle.STATIC_FILES)); self.assertTrue(required.issubset(preflight.REQUIRED_RUNTIME)); self.assertFalse(any("evaluator" in path.lower() for path in bundle.STATIC_FILES))
        launcher=(ROOT/"cloud/phk_v23_lf5_autodl/run.sh").read_text(encoding="utf-8")
        self.assertEqual(launcher.count("--user-override-cpu-gate"),2)

    def test_failed_cpu_gate_prevents_bundle_before_cloud(self):
        artifact=ROOT/"docs/experiment/artifacts/20260905T150045Z-phk-v23-lf5-cpu-qualification.json"
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(PermissionError): bundle.build(qualification_path=artifact,archive_path=Path(temporary)/"lf5.tar.gz",base_commit="test")

    def test_safe_path_and_forbidden_carrier_scan(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            with self.assertRaises(PermissionError): preflight._safe(root,"../escape")
            for relative in (preflight.MEDIUM_RELATIVE,preflight.CHECKPOINT_RELATIVE):
                path=root/Path(*relative.parts); path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(b"ok")
            self.assertEqual(preflight._forbidden(root),[]); bad=root/"extra-fine.npz"; bad.write_bytes(b"bad"); self.assertEqual(preflight._forbidden(root),["extra-fine.npz"])


if __name__=="__main__": unittest.main()
