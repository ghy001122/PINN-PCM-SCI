from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT=Path(__file__).resolve().parents[1]


def _load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); assert spec and spec.loader; module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


preflight=_load("lf4_preflight",ROOT/"cloud/phk_v23_lf4_autodl/preflight.py")
bundle=_load("lf4_bundle",ROOT/"cloud/phk_v23_lf4_autodl/build_bundle.py")


class LF4CloudTests(unittest.TestCase):
    def test_runtime_has_lf4_run_script_and_no_evaluator(self):
        required={"pinn_pcm_sci/phk_v23_lf4.py","pinn_pcm_sci/phk_v23_lf3.py","cloud/phk_v23_lf4_autodl/run.sh"}
        self.assertTrue(required.issubset(bundle.STATIC_FILES)); self.assertTrue(required.issubset(preflight.REQUIRED_RUNTIME)); self.assertFalse(any("evaluator" in path.lower() for path in bundle.STATIC_FILES))

    def test_safe_path_and_forbidden_carrier_scan(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            with self.assertRaises(PermissionError): preflight._safe(root,"../escape")
            for relative in (preflight.MEDIUM_RELATIVE,preflight.CHECKPOINT_RELATIVE):
                path=root/Path(*relative.parts); path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(b"ok")
            self.assertEqual(preflight._forbidden(root),[]); bad=root/"extra-fine.npz"; bad.write_bytes(b"bad"); self.assertEqual(preflight._forbidden(root),["extra-fine.npz"])

    def test_manifest_aggregate_detects_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); one=root/"one"; two=root/"two"; one.write_text("1"); two.write_text("2")
            files={p.name:hashlib.sha256(p.read_bytes()).hexdigest().upper() for p in (one,two)}; lines="".join(f"{name}={digest}\n" for name,digest in sorted(files.items())); identity="LF4-BUNDLE-"+hashlib.sha256(lines.encode()).hexdigest().upper()
            path=root/"cloud/phk_v23_lf4_autodl/deployed-source-manifest.json"; path.parent.mkdir(parents=True); path.write_text(json.dumps({"schema_id":"phk-v23-lf4-deployed-source-manifest-v1","identity_definition":"SHA256_OF_SORTED_PATH_EQUALS_UPPERCASE_SHA256_LINES","source_identity":identity,"files":files}))
            original_root,original_required=preflight.ROOT,preflight.REQUIRED_RUNTIME
            try:
                preflight.ROOT=root; preflight.REQUIRED_RUNTIME=frozenset(files); self.assertEqual(preflight._manifest(root,identity)["source_identity"],identity); two.write_text("changed")
                with self.assertRaises(ValueError): preflight._manifest(root,identity)
            finally: preflight.ROOT,preflight.REQUIRED_RUNTIME=original_root,original_required


if __name__=="__main__": unittest.main()
