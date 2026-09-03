from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from cloud.phk_v23_lf0_autodl import preflight


CONTRACTS = {
    "program": Path("configs/phk_v23/program_contract_lf0_exact_top_warmstart.json"),
    "method": Path("configs/phk_v23/method_contract_lf0_exact_top_warmstart.json"),
    "data": Path("configs/phk_v23/data_contract_lf0_medium_only.json"),
    "decision": Path("configs/phk_v23/decision_contract_lf0_attribution.json"),
}
MEDIUM = Path(
    "outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz"
)
MANIFEST = Path("cloud/phk_v23_lf0_autodl/deployed-source-manifest.json")
QUALIFICATION = Path("docs/experiment/artifacts/lf0-cpu-qualification.json")
SOURCE_COMMIT = "1" * 40


class _CudaProbe:
    def __init__(self, *, available: bool = True, name: str = "Tesla V100-PCIE-32GB"):
        self.available = available
        self.name = name

    def is_available(self) -> bool:
        return self.available

    def get_device_name(self, index: int) -> str:
        if index != 0:
            raise AssertionError("LF0 preflight must inspect cuda:0 only")
        return self.name


class Lf0CloudPreflightTests(unittest.TestCase):
    def test_runtime_manifest_closure_imports_lf0_in_isolated_tree(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            deployment_root = Path(temporary).resolve()
            for relative in sorted(preflight.REQUIRED_RUNTIME_RELATIVE_PATHS):
                source = repository_root / relative
                self.assertTrue(source.is_file(), relative)
                destination = deployment_root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)

            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(deployment_root)
            completed = subprocess.run(
                [sys.executable, "-c", "import pinn_pcm_sci.phk_v23_lf0"],
                cwd=deployment_root,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)

    def _tree(self) -> tuple[tempfile.TemporaryDirectory[str], Path, str]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name).resolve()
        medium = root / MEDIUM
        medium.parent.mkdir(parents=True)
        medium.write_bytes(b"synthetic-medium-carrier-for-preflight")
        medium_sha = hashlib.sha256(medium.read_bytes()).hexdigest().upper()

        contracts = {
            "program": {
                "schema_id": "phk-v23-lf0-program-contract-v1",
                "phase_id": "PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE",
                "authorization": {
                    "gpu_run_a": True,
                    "gpu_run_b_after_valid_a": True,
                    "conditional_gpu_run_c": True,
                    "new_seed": False,
                    "stress_prediction_or_unseal": False,
                    "benchmark_physics_reference_evaluator_change": False,
                },
            },
            "method": {
                "schema_id": "phk-v23-lf0-method-contract-v1",
                "program_contract": CONTRACTS["program"].as_posix(),
                "common_gpu_identity": {
                    "gpu": "TESLA_V100_PCIE_32GB_ONLY",
                    "dtype": "FLOAT64",
                    "seed": 17,
                    "arm": "STRONG_RAW",
                },
            },
            "data": {
                "schema_id": "phk-v23-lf0-data-contract-v1",
                "program_contract": CONTRACTS["program"].as_posix(),
                "training_source": {
                    "path": MEDIUM.as_posix(),
                    "sha256": medium_sha,
                    "resolution": "medium",
                    "only_gpu_training_label_source": True,
                },
                "qualification_only": {
                    "fine": {
                        "path": "outputs/local/nominal-fine.npz",
                        "sha256": "2" * 64,
                    },
                    "extra_fine": {
                        "path": "outputs/local/nominal-extra-fine.npz",
                        "sha256": "3" * 64,
                    },
                },
                "cloud_boundary": {
                    "medium_allowed_as_declared_method_input": True,
                    "fine_extra_fine_evaluator_and_stress_carriers_inaccessible": True,
                    "stress_fail_closed_before_io": True,
                }
            },
            "decision": {
                "schema_id": "phk-v23-lf0-decision-contract-v1",
                "program_contract": CONTRACTS["program"].as_posix(),
                "method_contract": CONTRACTS["method"].as_posix(),
                "data_contract": CONTRACTS["data"].as_posix(),
                "stress_status": "TWO_STRESS_REFERENCES_SEALED_UNREAD",
                "qualification_inputs": {
                    "c0_artifact": {
                        "path": "docs/experiment/artifacts/c0.json",
                        "sha256": "4" * 64,
                    },
                    "c0_contract": {
                        "path": "configs/phk_v23/c0.json",
                        "sha256": "5" * 64,
                    },
                    "oracle_floor_contract": {
                        "path": "configs/phk_v21/oracle-floor.json",
                        "sha256": "6" * 64,
                    },
                    "oracle_floor_seal": {
                        "path": "outputs/local/oracle-floor-seal.json",
                        "sha256": "7" * 64,
                    },
                },
            },
        }
        file_hashes = {}
        for role, relative in CONTRACTS.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(contracts[role]), encoding="utf-8")
            file_hashes[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        for relative in sorted(preflight.REQUIRED_RUNTIME_RELATIVE_PATHS):
            if relative in file_hashes:
                continue
            path = root / Path(relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f"runtime:{relative}".encode("utf-8"))
            file_hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        identity_lines = "".join(
            f"{relative}={digest}\n" for relative, digest in sorted(file_hashes.items())
        )
        identity = "LF0-BUNDLE-" + hashlib.sha256(identity_lines.encode()).hexdigest().upper()

        contract_identities = {
            role: {
                "path": relative.as_posix(),
                "sha256": file_hashes[relative.as_posix()],
            }
            for role, relative in CONTRACTS.items()
        }
        input_identities = {
            "low_fidelity_training_source": {
                "path": MEDIUM.as_posix(),
                "sha256": medium_sha,
                "size_bytes": medium.stat().st_size,
            },
            "qualification_fine": contracts["data"]["qualification_only"]["fine"],
            "qualification_extra_fine": contracts["data"]["qualification_only"]["extra_fine"],
            **contracts["decision"]["qualification_inputs"],
        }
        qualification_path = root / QUALIFICATION
        qualification_path.parent.mkdir(parents=True, exist_ok=True)
        qualification_path.write_text(
            json.dumps(
                {
                    "schema_id": "phk-v23-lf0-cpu-qualification-v1",
                    "task_id": "PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE",
                    "status": "LF0_CPU_QUALIFIED",
                    "passed": True,
                    "blockers": [],
                    "qualified_source_identity": identity,
                    "source_commit": SOURCE_COMMIT,
                    "contract_identities": contract_identities,
                    "input_identities": input_identities,
                }
            ),
            encoding="utf-8",
        )
        qualification_sha = hashlib.sha256(qualification_path.read_bytes()).hexdigest().upper()

        manifest_path = root / MANIFEST
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(
                {
                    "schema_id": "phk-v23-lf0-deployed-source-manifest-v1",
                    "source_identity": identity,
                    "source_commit": SOURCE_COMMIT,
                    "identity_definition": (
                        "SHA256_OF_SORTED_PATH_EQUALS_UPPERCASE_SHA256_LINES"
                    ),
                    "files": file_hashes,
                    "training_input": {
                        "path": MEDIUM.as_posix(),
                        "sha256": medium_sha,
                        "size_bytes": medium.stat().st_size,
                    },
                    "cpu_qualification": {
                        "path": QUALIFICATION.as_posix(),
                        "sha256": qualification_sha,
                        "size_bytes": qualification_path.stat().st_size,
                    },
                }
            ),
            encoding="utf-8",
        )
        return temporary, root, identity

    def _run(self, root: Path, identity: str) -> dict[str, object]:
        with mock.patch.object(preflight, "_running_lf0_training_processes", return_value=[]):
            return preflight.run_preflight(
                source_identity=identity,
                deployment_root=root,
                medium_carrier=root / MEDIUM,
                project_root=root,
                cuda_probe=_CudaProbe(),
                pythonpath=str(root),
            )

    def test_valid_bundle_allows_only_the_exact_medium_training_carrier(self) -> None:
        temporary, root, identity = self._tree()
        self.addCleanup(temporary.cleanup)
        result = self._run(root, identity)
        self.assertEqual(result["status"], "REMOTE_LF0_PREFLIGHT_VALID")
        self.assertEqual(result["gpu_name"], "Tesla V100-PCIE-32GB")
        self.assertEqual(result["dtype"], "FLOAT64")
        self.assertEqual(result["medium_carrier"], MEDIUM.as_posix())
        self.assertEqual(result["cpu_qualification"]["status"], "LF0_CPU_QUALIFIED")
        self.assertEqual(result["forbidden_cloud_files"], [])
        self.assertEqual(result["duplicate_training_processes"], [])
        self.assertFalse(result["optimizer_constructed"])
        self.assertEqual(result["optimizer_updates"], 0)

    def test_four_contract_bundle_is_not_a_complete_runtime_deployment(self) -> None:
        temporary, root, identity = self._tree()
        self.addCleanup(temporary.cleanup)
        manifest_path = root / MANIFEST
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"] = {
            relative.as_posix(): manifest["files"][relative.as_posix()]
            for relative in CONTRACTS.values()
        }
        lines = "".join(
            f"{relative}={digest}\n"
            for relative, digest in sorted(manifest["files"].items())
        )
        identity = "LF0-BUNDLE-" + hashlib.sha256(lines.encode()).hexdigest().upper()
        manifest["source_identity"] = identity
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "runtime closure"):
            self._run(root, identity)

    def test_cpu_qualification_record_is_required_before_gpu_admission(self) -> None:
        temporary, root, identity = self._tree()
        self.addCleanup(temporary.cleanup)
        manifest_path = root / MANIFEST
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        del manifest["cpu_qualification"]
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "CPU qualification"):
            self._run(root, identity)

    def test_failed_or_source_mismatched_cpu_qualification_is_rejected(self) -> None:
        for field, value, message in (
            ("passed", False, "did not pass"),
            ("qualified_source_identity", "LF0-BUNDLE-" + "0" * 64, "source identity"),
        ):
            with self.subTest(field=field):
                temporary, root, identity = self._tree()
                self.addCleanup(temporary.cleanup)
                manifest_path = root / MANIFEST
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                qualification_path = root / QUALIFICATION
                qualification = json.loads(qualification_path.read_text(encoding="utf-8"))
                qualification[field] = value
                qualification_path.write_text(json.dumps(qualification), encoding="utf-8")
                manifest["cpu_qualification"]["sha256"] = hashlib.sha256(
                    qualification_path.read_bytes()
                ).hexdigest().upper()
                manifest["cpu_qualification"]["size_bytes"] = qualification_path.stat().st_size
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                with self.assertRaisesRegex((PermissionError, ValueError), message):
                    self._run(root, identity)

    def test_stale_required_runtime_file_is_rejected(self) -> None:
        temporary, root, identity = self._tree()
        self.addCleanup(temporary.cleanup)
        (root / "pinn_pcm_sci/phk_v22r_pinn.py").write_bytes(b"stale model seam")
        with self.assertRaisesRegex(ValueError, "deployed-source drift"):
            self._run(root, identity)

    def test_deployment_root_must_be_absolute_and_match_the_loaded_tree(self) -> None:
        temporary, root, identity = self._tree()
        self.addCleanup(temporary.cleanup)
        with self.assertRaisesRegex(ValueError, "absolute"):
            preflight.run_preflight(
                source_identity=identity,
                deployment_root=Path("relative-deploy-root"),
                medium_carrier=root / MEDIUM,
                project_root=root,
                cuda_probe=_CudaProbe(),
            )

    def test_fine_or_extra_carrier_is_rejected_before_training(self) -> None:
        temporary, root, identity = self._tree()
        self.addCleanup(temporary.cleanup)
        extra = (
            root
            / "outputs/runs/20260828T-phk-v21-s1-q-06-nominal-extra-fine/result-intent-06.npz"
        )
        extra.parent.mkdir(parents=True)
        extra.write_bytes(b"forbidden")
        with self.assertRaisesRegex(PermissionError, "forbidden cloud files"):
            self._run(root, identity)

    def test_stress_and_evaluator_files_are_rejected(self) -> None:
        for relative in (
            "outputs/stress-reference-secret.npz",
            "pinn_pcm_sci/phk_v22r_evaluator.py",
        ):
            with self.subTest(relative=relative):
                temporary, root, identity = self._tree()
                self.addCleanup(temporary.cleanup)
                forbidden = root / relative
                forbidden.parent.mkdir(parents=True, exist_ok=True)
                forbidden.write_text("forbidden", encoding="utf-8")
                with self.assertRaisesRegex(PermissionError, "forbidden cloud files"):
                    self._run(root, identity)

    def test_duplicate_lf0_training_process_is_rejected(self) -> None:
        temporary, root, identity = self._tree()
        self.addCleanup(temporary.cleanup)
        with mock.patch.object(
            preflight,
            "_running_lf0_training_processes",
            return_value=["4242 python -m pinn_pcm_sci.phk_v23_lf0 run"],
        ):
            with self.assertRaisesRegex(RuntimeError, "duplicate LF0 training"):
                preflight.run_preflight(
                    source_identity=identity,
                    deployment_root=root,
                    medium_carrier=root / MEDIUM,
                    project_root=root,
                    cuda_probe=_CudaProbe(),
                    pythonpath=str(root),
                )

    def test_source_or_contract_drift_is_rejected(self) -> None:
        temporary, root, identity = self._tree()
        self.addCleanup(temporary.cleanup)
        (root / CONTRACTS["program"]).write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "deployed-source drift"):
            self._run(root, identity)

    def test_wrong_gpu_is_rejected(self) -> None:
        temporary, root, identity = self._tree()
        self.addCleanup(temporary.cleanup)
        with mock.patch.object(preflight, "_running_lf0_training_processes", return_value=[]):
            with self.assertRaisesRegex(RuntimeError, "unexpected GPU"):
                preflight.run_preflight(
                    source_identity=identity,
                    deployment_root=root,
                    medium_carrier=root / MEDIUM,
                    project_root=root,
                    cuda_probe=_CudaProbe(name="NVIDIA A100-SXM4-40GB"),
                    pythonpath=str(root),
                )


if __name__ == "__main__":
    unittest.main()
