from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from pinn_pcm_sci import g2_smoke
from pinn_pcm_sci.g2_smoke import G2SmokeRequest, run_g2_smoke
from tests.test_qpop_conversion import _write_native_fixture, _write_spec


def _fixture_inputs(
    root: Path,
    *,
    entrypoint_body: str | None = None,
    wall_timeout_seconds: int = 30,
    evaluator_timeout_seconds: int = 30,
) -> tuple[Path, Path]:
    template_native = _write_native_fixture(root)
    if entrypoint_body is None:
        entrypoint_body = """from pathlib import Path
import shutil

template = Path({template!r})
cwd = Path.cwd()
shutil.copyfile(template / "log.txt", cwd / "log.txt")
shutil.copytree(template / "solution", cwd / "solution", dirs_exist_ok=True)
""".format(template=str(template_native))
    (template_native / "source" / "qpop-imt.py").write_text(
        entrypoint_body,
        encoding="utf-8",
    )
    config_root = root / "config"
    config_root.mkdir()
    _write_spec(config_root, template_native)
    shutil.copyfile(template_native / "input.xml", config_root / "smoke_input.xml")
    (config_root / "native_runtime.json").write_text(
        json.dumps(
            {
                "schema_version": "qpop-native-runtime-v1",
                "launcher_profile": "NON_SCIENTIFIC_LOCAL_FIXTURE",
                "mpi_ranks": 1,
                "wall_timeout_seconds": wall_timeout_seconds,
                "evaluator_timeout_seconds": evaluator_timeout_seconds,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return template_native, config_root


def _hard_kill_runner(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.kill()
    process.wait(timeout=10)


def _wsl_runtime_contract() -> dict[str, object]:
    prefix = "/opt/qpop-cpc-v1-env-g2-final-002"
    petsc_arch = "arch-linux-qpop-opt"
    mpi_prefix = f"{prefix}/openmpi-3.1.6"
    petsc_dir = f"{prefix}/src/petsc"
    dolfin_dir = f"{prefix}/fenics/dolfin"
    provider = f"{prefix}/providers/pybind11-2.2.4"
    return {
        "schema_version": "qpop-native-runtime-v1",
        "launcher_profile": "WSL2_QPOP_CPC_V1",
        "environment_id": "qpop-cpc-v1-ubuntu-20.04-source-stack-v3",
        "environment_spec_sha256": "a" * 64,
        "resolution_lock_sha256": "b" * 64,
        "build_manifest_sha256": "c" * 64,
        "mpi_ranks": 2,
        "wall_timeout_seconds": 30,
        "evaluator_timeout_seconds": 30,
        "wsl_executable": "fixture-wsl.exe",
        "distribution": "PINN-PCM-SCI-Ubuntu-20.04",
        "wsl_user": "root",
        "mpirun_path": f"{mpi_prefix}/bin/mpirun",
        "python_path": f"{prefix}/py38/bin/python",
        "runtime_environment": {
            "CC": "/usr/bin/gcc-9",
            "CXX": "/usr/bin/g++-9",
            "FC": "/usr/bin/gfortran-9",
            "MPI_DIR": mpi_prefix,
            "PETSC_DIR": petsc_dir,
            "PETSC_ARCH": petsc_arch,
            "PATH": (
                f"{prefix}/py38/bin:{mpi_prefix}/bin:"
                "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
            ),
            "LD_LIBRARY_PATH": (
                f"{dolfin_dir}/lib:{petsc_dir}/{petsc_arch}/lib:{mpi_prefix}/lib"
            ),
            "PYTHONPATH": f"{petsc_dir}/{petsc_arch}/lib",
            "CMAKE_PREFIX_PATH": (
                f"{provider}:{dolfin_dir}:{petsc_dir}/{petsc_arch}:{mpi_prefix}"
            ),
            "PKG_CONFIG_PATH": f"{dolfin_dir}/lib/pkgconfig",
            "pybind11_DIR": f"{provider}/share/cmake/pybind11",
            "DOLFIN_DIR": f"{dolfin_dir}/share/dolfin/cmake",
            "MPICC": f"{mpi_prefix}/bin/mpicc",
            "OMPI_ALLOW_RUN_AS_ROOT": "1",
            "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
            "PYTHONNOUSERSITE": "1",
        },
    }


def _verified_environment_facts(runtime: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "qpop-legacy-verification-v1",
        "status": "ENVIRONMENT_VERIFIED",
        "evidence_identity": "ENGINEERING_ABI_AND_FEATURE_QUALIFICATION_ONLY",
        "g2_gate_outcome": "NOT_EVALUATED",
        "environment_id": runtime["environment_id"],
        "spec_sha256": runtime["environment_spec_sha256"],
        "resolution_lock_sha256": runtime["resolution_lock_sha256"],
        "build_manifest_sha256": runtime["build_manifest_sha256"],
        "qpop_started": False,
        "two_rank_import_barrier": "PASS",
        "scientific_claim_status": "NO_SCIENTIFIC_CLAIMS",
    }


class G2SmokeRunnerContractTest(unittest.TestCase):
    def test_native_process_conversion_disk_evaluator_and_ledger_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template, config_root = _fixture_inputs(root)
            output_root = root / "outputs" / "runs"
            experiment_root = root / "experiment"
            run_id = "20260819T020304Z-smoke-qpop-fixture-001"

            exit_code = run_g2_smoke(
                G2SmokeRequest(
                    run_id=run_id,
                    source_root=template / "source",
                    config_root=config_root,
                    output_root=output_root,
                    experiment_root=experiment_root,
                    environment_facts={"runtime": "NON_SCIENTIFIC_FIXTURE"},
                )
            )
            manifest = json.loads(
                (experiment_root / "manifests" / f"{run_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            metrics = json.loads(
                (output_root / run_id / "metrics.json").read_text(encoding="utf-8")
            )
            index_rows = (experiment_root / "index.jsonl").read_text(
                encoding="utf-8"
            ).splitlines()

        self.assertEqual(exit_code, 0)
        self.assertEqual(manifest["tier"], "smoke")
        self.assertEqual(manifest["scientific_role"], "oracle_qualification")
        self.assertEqual(manifest["gate_outcome"], "G2_SMOKE_PASS")
        self.assertEqual(manifest["claim_status"], "NO_SCIENTIFIC_CLAIM")
        self.assertEqual(manifest["actual_budget"]["accepted_steps"], 3)
        self.assertEqual(manifest["actual_budget"]["mpi_ranks"], 1)
        self.assertEqual(
            manifest["command"],
            [
                sys.executable,
                str(output_root / run_id / "native" / "source" / "qpop-imt.py"),
            ],
        )
        self.assertEqual(metrics["structure_symmetric_difference_cycle_equal"], 0.0)
        self.assertEqual(metrics["device_trajectory_nrmse"], 0.0)
        self.assertEqual(len(index_rows), 1)

    def test_native_failure_still_records_manifest_and_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template, config_root = _fixture_inputs(
                root,
                entrypoint_body="raise SystemExit(3)\n",
            )
            output_root = root / "outputs" / "runs"
            experiment_root = root / "experiment"
            run_id = "20260819T020305Z-smoke-qpop-fixture-failed"

            exit_code = run_g2_smoke(
                G2SmokeRequest(
                    run_id=run_id,
                    source_root=template / "source",
                    config_root=config_root,
                    output_root=output_root,
                    experiment_root=experiment_root,
                    environment_facts={"runtime": "NON_SCIENTIFIC_FIXTURE"},
                )
            )
            manifest = json.loads(
                (experiment_root / "manifests" / f"{run_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            index_rows = (experiment_root / "index.jsonl").read_text(
                encoding="utf-8"
            ).splitlines()

        self.assertEqual(exit_code, 1)
        self.assertEqual(manifest["execution_status"], "FAILED")
        self.assertEqual(manifest["gate_outcome"], "G2_SMOKE_BLOCKED")
        self.assertEqual(manifest["actual_budget"]["native_exit_code"], 3)
        self.assertEqual(manifest["failure_class"], "NATIVE_PROCESS_EXIT")
        self.assertEqual(len(index_rows), 1)

    @unittest.skipUnless(os.name == "nt", "WSL launcher contract is Windows-only")
    def test_wsl_native_command_reuses_the_verified_runtime_environment(self) -> None:
        class CompletedNativeProcess:
            returncode = 3

            def communicate(self, timeout: int) -> tuple[bytes, bytes]:
                return b"", b""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template, config_root = _fixture_inputs(root)
            runtime = _wsl_runtime_contract()
            (config_root / "native_runtime.json").write_text(
                json.dumps(runtime, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            observed_commands: list[list[str]] = []
            real_popen = subprocess.Popen

            def launch(command: list[str], *args: object, **kwargs: object):
                if command[0] == "fixture-wsl.exe":
                    observed_commands.append(command)
                    return CompletedNativeProcess()
                return real_popen(command, *args, **kwargs)

            with mock.patch(
                "pinn_pcm_sci.g2_smoke.subprocess.Popen",
                side_effect=launch,
            ):
                run_g2_smoke(
                    G2SmokeRequest(
                        run_id="20260820T000001Z-smoke-qpop-wsl-runtime-environment",
                        source_root=template / "source",
                        config_root=config_root,
                        output_root=root / "outputs" / "runs",
                        experiment_root=root / "experiment",
                        environment_facts=_verified_environment_facts(runtime),
                    )
                )

        self.assertEqual(len(observed_commands), 1)
        command = observed_commands[0]
        env_index = command.index("/usr/bin/env")
        mpirun_index = command.index(str(runtime["mpirun_path"]))
        self.assertLess(env_index, mpirun_index)
        self.assertEqual(
            command[env_index + 1 : mpirun_index],
            [
                f"{key}={runtime['runtime_environment'][key]}"
                for key in sorted(runtime["runtime_environment"])
            ],
        )

    @unittest.skipUnless(os.name == "nt", "WSL launcher contract is Windows-only")
    def test_wsl_runtime_rejects_unverified_environment_before_native_launch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template, config_root = _fixture_inputs(root)
            runtime = _wsl_runtime_contract()
            (config_root / "native_runtime.json").write_text(
                json.dumps(runtime, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            facts = _verified_environment_facts(runtime)
            facts["status"] = "BUILT_NOT_YET_VERIFIED"
            run_id = "20260820T000002Z-smoke-qpop-wsl-unverified-environment"
            experiment_root = root / "experiment"

            exit_code = run_g2_smoke(
                G2SmokeRequest(
                    run_id=run_id,
                    source_root=template / "source",
                    config_root=config_root,
                    output_root=root / "outputs" / "runs",
                    experiment_root=experiment_root,
                    environment_facts=facts,
                )
            )
            manifest = json.loads(
                (experiment_root / "manifests" / f"{run_id}.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(manifest["failure_class"], "PREPARATION_CONTRACT_INVALID")
        self.assertFalse(manifest["actual_budget"]["native_started"])

    @unittest.skipUnless(os.name == "nt", "WSL launcher contract is Windows-only")
    def test_wsl_timeout_statuses_are_distinguished_from_ordinary_failure(self) -> None:
        class CompletedNativeProcess:
            def __init__(self, returncode: int) -> None:
                self.returncode = returncode

            def communicate(self, timeout: int) -> tuple[bytes, bytes]:
                return b"", b""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template, config_root = _fixture_inputs(root)
            runtime_path = config_root / "native_runtime.json"
            runtime_path.write_text(
                json.dumps(_wsl_runtime_contract(), indent=2, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )
            output_root = root / "outputs" / "runs"
            experiment_root = root / "experiment"
            real_popen = subprocess.Popen
            observed: list[str | None] = []

            for exit_status in (124, 137, 3):
                run_id = f"20260819T020305Z-smoke-qpop-wsl-timeout-{exit_status}"

                def launch(command: list[str], *args: object, **kwargs: object):
                    if command[0] == "fixture-wsl.exe":
                        return CompletedNativeProcess(exit_status)
                    return real_popen(command, *args, **kwargs)

                with mock.patch(
                    "pinn_pcm_sci.g2_smoke.subprocess.Popen",
                    side_effect=launch,
                ):
                    run_g2_smoke(
                        G2SmokeRequest(
                            run_id=run_id,
                            source_root=template / "source",
                            config_root=config_root,
                            output_root=output_root,
                            experiment_root=experiment_root,
                            environment_facts=_verified_environment_facts(
                                _wsl_runtime_contract()
                            ),
                        )
                    )
                manifest = json.loads(
                    (experiment_root / "manifests" / f"{run_id}.json").read_text(
                        encoding="utf-8"
                    )
                )
                observed.append(manifest["failure_class"])

        self.assertEqual(
            observed,
            [
                "NATIVE_TIMEOUT",
                "NATIVE_PROCESS_KILLED_AMBIGUOUS",
                "NATIVE_PROCESS_EXIT",
            ],
        )

    def test_runtime_rank_tampering_is_rejected_before_native_launch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template, config_root = _fixture_inputs(root)
            runtime_path = config_root / "native_runtime.json"
            runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
            runtime["mpi_ranks"] = 2
            runtime_path.write_text(json.dumps(runtime), encoding="utf-8")
            run_id = "20260819T020306Z-smoke-qpop-runtime-tampered"
            experiment_root = root / "experiment"

            exit_code = run_g2_smoke(
                G2SmokeRequest(
                    run_id=run_id,
                    source_root=template / "source",
                    config_root=config_root,
                    output_root=root / "outputs" / "runs",
                    experiment_root=experiment_root,
                    environment_facts={"runtime": "NON_SCIENTIFIC_FIXTURE"},
                )
            )
            manifest = json.loads(
                (experiment_root / "manifests" / f"{run_id}.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(manifest["failure_class"], "PREPARATION_CONTRACT_INVALID")
        self.assertFalse(manifest["actual_budget"]["native_started"])

    def test_timeout_records_postrun_input_mutation_and_started_state(self) -> None:
        body = """from pathlib import Path
import time

Path("input.xml").write_text("changed during timeout\\n", encoding="utf-8")
time.sleep(30)
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template, config_root = _fixture_inputs(
                root,
                entrypoint_body=body,
                wall_timeout_seconds=1,
            )
            run_id = "20260819T020307Z-smoke-qpop-timeout-mutation"
            experiment_root = root / "experiment"
            output_root = root / "outputs" / "runs"

            exit_code = run_g2_smoke(
                G2SmokeRequest(
                    run_id=run_id,
                    source_root=template / "source",
                    config_root=config_root,
                    output_root=output_root,
                    experiment_root=experiment_root,
                    environment_facts={"runtime": "NON_SCIENTIFIC_FIXTURE"},
                )
            )
            manifest = json.loads(
                (experiment_root / "manifests" / f"{run_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            identity = json.loads(
                (output_root / run_id / "postrun_identity.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(manifest["failure_class"], "NATIVE_TIMEOUT")
        self.assertTrue(manifest["actual_budget"]["native_started"])
        self.assertEqual(identity["input.xml"]["status"], "CHANGED")

    def test_keyboard_interrupt_is_recorded_before_it_is_reraised(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template, config_root = _fixture_inputs(root)
            run_id = "20260819T020308Z-smoke-qpop-interrupted"
            experiment_root = root / "experiment"

            with mock.patch(
                "pinn_pcm_sci.g2_smoke._launch_native_process",
                side_effect=KeyboardInterrupt(),
            ):
                with self.assertRaises(KeyboardInterrupt):
                    run_g2_smoke(
                        G2SmokeRequest(
                            run_id=run_id,
                            source_root=template / "source",
                            config_root=config_root,
                            output_root=root / "outputs" / "runs",
                            experiment_root=experiment_root,
                            environment_facts={"runtime": "NON_SCIENTIFIC_FIXTURE"},
                        )
                    )
            manifest = json.loads(
                (experiment_root / "manifests" / f"{run_id}.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(manifest["execution_status"], "INTERRUPTED")
        self.assertEqual(manifest["failure_class"], "INTERRUPTED")

    def test_hard_terminated_runner_is_recovered_only_after_its_lease_is_released(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template, config_root = _fixture_inputs(
                root,
                entrypoint_body="""from pathlib import Path
import time

Path("native-started").write_text("started\\n", encoding="utf-8")
time.sleep(1)
""",
                wall_timeout_seconds=1,
                evaluator_timeout_seconds=1,
            )
            run_id = "20260819T020308Z-smoke-qpop-hard-terminated"
            output_root = root / "outputs" / "runs"
            experiment_root = root / "experiment"
            command = [
                sys.executable,
                "-m",
                "pinn_pcm_sci.g2_smoke",
                "--run-id",
                run_id,
                "--source-root",
                str(template / "source"),
                "--config-root",
                str(config_root),
                "--output-root",
                str(output_root),
                "--experiment-root",
                str(experiment_root),
            ]
            process = subprocess.Popen(
                command,
                cwd=Path(__file__).resolve().parents[1],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
                ),
                start_new_session=os.name != "nt",
            )
            intent_path = experiment_root / "intents" / f"{run_id}.json"
            manifest_path = experiment_root / "manifests" / f"{run_id}.json"
            native_started_path = output_root / run_id / "native" / "native-started"
            try:
                deadline = time.monotonic() + 10
                while not native_started_path.exists() and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertTrue(intent_path.exists(), "runner did not publish its intent")
                self.assertTrue(native_started_path.exists(), "native fixture did not start")
                self.assertIsNone(process.poll(), "runner exited before hard-termination test")

                self.assertEqual(
                    g2_smoke.recover_orphaned_g2_intents(experiment_root),
                    [],
                )
                self.assertFalse(manifest_path.exists())

                _hard_kill_runner(process)
                self.assertEqual(
                    g2_smoke.recover_orphaned_g2_intents(experiment_root),
                    [],
                    "released lease must not bypass the recovery deadline",
                )
                intent = json.loads(intent_path.read_text(encoding="utf-8"))
                recover_not_before = datetime.fromisoformat(
                    intent["recover_not_before"].replace("Z", "+00:00")
                )
                while datetime.now(timezone.utc) < recover_not_before:
                    time.sleep(0.05)
                recovered = g2_smoke.recover_orphaned_g2_intents(experiment_root)
            finally:
                _hard_kill_runner(process)

            self.assertEqual(
                recovered,
                [manifest_path],
                intent_path.read_text(encoding="utf-8"),
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            index_rows = [
                json.loads(line)
                for line in (experiment_root / "index.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]

        self.assertEqual(
            (
                manifest["execution_status"],
                manifest["failure_class"],
                [(row["run_id"], row["execution_status"]) for row in index_rows],
            ),
            (
                "INTERRUPTED",
                "INTERRUPTED_UNKNOWN",
                [(run_id, "INTERRUPTED")],
            ),
        )

    def test_recovery_reconciles_a_published_manifest_missing_from_the_index(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template, config_root = _fixture_inputs(root)
            output_root = root / "outputs" / "runs"
            experiment_root = root / "experiment"
            run_id = "20260819T020308Z-smoke-qpop-manifest-index-gap"
            run_g2_smoke(
                G2SmokeRequest(
                    run_id=run_id,
                    source_root=template / "source",
                    config_root=config_root,
                    output_root=output_root,
                    experiment_root=experiment_root,
                    environment_facts={"runtime": "NON_SCIENTIFIC_FIXTURE"},
                )
            )
            manifest_path = experiment_root / "manifests" / f"{run_id}.json"
            intent_path = experiment_root / "intents" / f"{run_id}.json"
            intent = json.loads(intent_path.read_text(encoding="utf-8"))
            intent["recover_not_before"] = "2000-01-01T00:00:00Z"
            intent_path.write_text(
                json.dumps(intent, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (experiment_root / "index.jsonl").unlink()
            (experiment_root / "INDEX.md").unlink()

            recovered = g2_smoke.recover_orphaned_g2_intents(experiment_root)
            index_rows = [
                json.loads(line)
                for line in (experiment_root / "index.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]

        self.assertEqual(recovered, [manifest_path])
        self.assertEqual([row["run_id"] for row in index_rows], [run_id])

    def test_native_launch_failure_is_recorded_without_started_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template, config_root = _fixture_inputs(root)
            run_id = "20260819T020308Z-smoke-qpop-launch-failed"
            experiment_root = root / "experiment"

            with mock.patch(
                "pinn_pcm_sci.g2_smoke.subprocess.Popen",
                side_effect=OSError("fixture launch failure"),
            ):
                exit_code = run_g2_smoke(
                    G2SmokeRequest(
                        run_id=run_id,
                        source_root=template / "source",
                        config_root=config_root,
                        output_root=root / "outputs" / "runs",
                        experiment_root=experiment_root,
                        environment_facts={"runtime": "NON_SCIENTIFIC_FIXTURE"},
                    )
                )
            manifest = json.loads(
                (experiment_root / "manifests" / f"{run_id}.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(manifest["failure_class"], "NATIVE_LAUNCH_FAILED")
        self.assertFalse(manifest["actual_budget"]["native_started"])

    def test_zero_exit_evaluator_without_metrics_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template, config_root = _fixture_inputs(root)
            run_id = "20260819T020309Z-smoke-qpop-missing-metrics"
            experiment_root = root / "experiment"

            with mock.patch(
                "pinn_pcm_sci.g2_smoke._run_evaluator_process",
                return_value=mock.Mock(returncode=0, stderr=""),
            ):
                exit_code = run_g2_smoke(
                    G2SmokeRequest(
                        run_id=run_id,
                        source_root=template / "source",
                        config_root=config_root,
                        output_root=root / "outputs" / "runs",
                        experiment_root=experiment_root,
                        environment_facts={"runtime": "NON_SCIENTIFIC_FIXTURE"},
                    )
                )
            manifest = json.loads(
                (experiment_root / "manifests" / f"{run_id}.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(manifest["failure_class"], "EVALUATOR_OUTPUT_INVALID")

    def test_zero_exit_evaluator_with_wrong_identity_is_rejected(self) -> None:
        def write_wrong_metrics(*, metrics_path: Path, **_: object) -> object:
            metrics_path.write_text(
                json.dumps(
                    {
                        "schema_version": "metrics-v1",
                        "evaluator_id": "wrong",
                        "case_id": "wrong",
                        "split_id": "wrong",
                        "method_id": "wrong",
                        "checkpoint_id": "wrong",
                        "structure_symmetric_difference_cycle_equal": 0.0,
                        "device_trajectory_nrmse": 0.0,
                    }
                ),
                encoding="utf-8",
            )
            return mock.Mock(returncode=0, stderr="")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template, config_root = _fixture_inputs(root)
            run_id = "20260819T020310Z-smoke-qpop-wrong-metrics"
            experiment_root = root / "experiment"

            with mock.patch(
                "pinn_pcm_sci.g2_smoke._run_evaluator_process",
                side_effect=write_wrong_metrics,
            ):
                exit_code = run_g2_smoke(
                    G2SmokeRequest(
                        run_id=run_id,
                        source_root=template / "source",
                        config_root=config_root,
                        output_root=root / "outputs" / "runs",
                        experiment_root=experiment_root,
                        environment_facts={"runtime": "NON_SCIENTIFIC_FIXTURE"},
                    )
                )
            manifest = json.loads(
                (experiment_root / "manifests" / f"{run_id}.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(manifest["failure_class"], "EVALUATOR_OUTPUT_INVALID")


if __name__ == "__main__":
    unittest.main()
