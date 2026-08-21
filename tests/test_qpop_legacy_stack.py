from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from pinn_pcm_sci.qpop_legacy_stack import (
    LegacyStackContractError,
    LegacyStackExecutionError,
    build_stack_environment,
    build_execution_plan,
    classify_cpp_build_state,
    inspect_clean_source_checkout,
    load_stack_spec,
    lock_petsc_external_sources,
    parse_petsc_configuration,
    validate_dolfin_python_contract,
    validate_petsc_check_log,
    validate_preflight_report,
    validate_python_resolution_transition,
    validate_resolution_lock,
)


class QPopLegacyStackContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.spec_path = (
            self.root
            / "configs"
            / "qpop"
            / "legacy-stack-ubuntu-20.04"
            / "stack_spec.json"
        )

    def test_frozen_spec_produces_a_non_qpop_resolve_build_verify_plan(self) -> None:
        spec = load_stack_spec(self.spec_path)
        plan = build_execution_plan(spec)

        self.assertEqual(spec["os"], {"id": "ubuntu", "version_id": "20.04"})
        self.assertEqual(spec["wsl_distro_name"], "PINN-PCM-SCI-Ubuntu-20.04")
        self.assertEqual(spec["build_jobs"], 2)
        self.assertEqual(spec["toolchain"]["gnu_major"], 9)
        self.assertEqual(spec["sources"]["openmpi"]["version"], "3.1.6")
        self.assertEqual(spec["sources"]["petsc"]["commit"], "09da24df01e50defd94bc4f7396f866a808ecea5")
        self.assertEqual(spec["sources"]["dolfin"]["ref"], "2019.1.0.post0")
        self.assertIn(
            "-download-sowing-cc=/usr/bin/gcc-9",
            spec["petsc"]["configure_options"],
        )
        self.assertIn(
            "-download-sowing-cxx=/usr/bin/g++-9",
            spec["petsc"]["configure_options"],
        )
        self.assertEqual(
            [stage["id"] for stage in plan],
            ["resolve", "preflight", "build", "verify"],
        )
        build_stage = next(stage for stage in plan if stage["id"] == "build")
        resolve_stage = next(stage for stage in plan if stage["id"] == "resolve")
        self.assertEqual(
            resolve_stage["required_mpi_executables"],
            ["mpirun", "mpiexec", "ompi_info", "mpicc", "mpicxx", "mpifort"],
        )
        self.assertEqual(
            build_stage["requires"],
            ["resolution.lock.json", "preflight.json"],
        )
        rendered = json.dumps(plan, sort_keys=True).lower()
        self.assertNotIn("qpop-imt.py", rendered)
        self.assertNotIn("canonical_input", rendered)
        self.assertIn("openmpi-3.1.6", rendered)
        self.assertIn("arch-linux-qpop-opt", rendered)
        self.assertIn("resolution.lock.json", rendered)

    def test_frozen_ptscotch_plan_declares_bison(self) -> None:
        spec = load_stack_spec(self.spec_path)

        self.assertIn("bison", spec["system_packages"]["install"])

    def test_final_integration_contract_uses_a_new_clean_prefix(self) -> None:
        spec = load_stack_spec(self.spec_path)

        self.assertEqual(
            spec["environment_id"],
            "qpop-cpc-v1-ubuntu-20.04-source-stack-v3",
        )
        self.assertEqual(
            spec["install_prefix"],
            "/opt/qpop-cpc-v1-env-g2-final-002",
        )

        reused = copy.deepcopy(spec)
        reused["install_prefix"] = "/opt/qpop-cpc-v1-env"
        with self.assertRaisesRegex(LegacyStackContractError, "clean G2 final prefix"):
            build_execution_plan(reused)

    def test_frozen_ptscotch_plan_declares_flex(self) -> None:
        spec = load_stack_spec(self.spec_path)

        self.assertIn("flex", spec["system_packages"]["install"])

    def test_frozen_python_contract_uses_the_dolfin_pybind11_source_release(self) -> None:
        spec = load_stack_spec(self.spec_path)

        self.assertIn("pybind11==2.2.4", spec["python_resolution"]["requirements"])
        self.assertNotIn("pybind11==2.2.3", spec["python_resolution"]["requirements"])
        self.assertEqual(
            spec["sources"]["pybind11"],
            {
                "version": "2.2.4",
                "url": "https://files.pythonhosted.org/packages/source/p/pybind11/pybind11-2.2.4.tar.gz",
                "filename": "pybind11-2.2.4.tar.gz",
                "sha256": "642abbbd2948ed5af28e69adfae1535347c7aa9eb0cdab130e20e1f198f8e1cf",
            },
        )
        self.assertIn(
            {
                "filename": "pybind11-2.2.4.tar.gz",
                "sha256": "642abbbd2948ed5af28e69adfae1535347c7aa9eb0cdab130e20e1f198f8e1cf",
            },
            spec["python_resolution"]["known_artifacts"],
        )

        stale = copy.deepcopy(spec)
        stale["python_resolution"]["requirements"] = [
            "pybind11==2.2.3" if item == "pybind11==2.2.4" else item
            for item in stale["python_resolution"]["requirements"]
        ]
        with self.assertRaisesRegex(LegacyStackContractError, "pybind11 2.2.4"):
            build_execution_plan(stale)

        missing_artifact = copy.deepcopy(spec)
        missing_artifact["python_resolution"]["known_artifacts"] = [
            item
            for item in missing_artifact["python_resolution"]["known_artifacts"]
            if item["filename"] != "pybind11-2.2.4.tar.gz"
        ]
        with self.assertRaisesRegex(LegacyStackContractError, "pybind11 source artifact"):
            build_execution_plan(missing_artifact)

    def test_resolution_plan_separates_python_sdist_from_git_cmake_provider(self) -> None:
        spec = load_stack_spec(self.spec_path)
        plan = build_execution_plan(spec)
        resolve = next(stage for stage in plan if stage["id"] == "resolve")

        self.assertEqual(
            spec["sources"]["pybind11_cmake_provider"],
            {
                "version": "2.2.4",
                "repository": "https://github.com/pybind/pybind11.git",
                "tag": "v2.2.4",
                "tag_object": "e4637eb508aa3e41233875f6ce3891d96fbc5d33",
                "commit": "9a19306fbf30642ca331d0ec88e7da54a96860f9",
                "archive_url": (
                    "https://codeload.github.com/pybind/pybind11/tar.gz/"
                    "9a19306fbf30642ca331d0ec88e7da54a96860f9"
                ),
                "filename": "pybind11-v2.2.4-git-9a19306.tar.gz",
                "archive_root": "pybind11-9a19306fbf30642ca331d0ec88e7da54a96860f9",
                "sha256": "29b2cafb4c15ceb452d6ca2fc13221640738b1bf0f17d9a49f7c14833bd8a6f8",
            },
        )
        self.assertEqual(
            resolve["pybind11_provider"]["source"]["filename"],
            "pybind11-v2.2.4-git-9a19306.tar.gz",
        )
        self.assertNotEqual(
            resolve["pybind11_provider"]["source"]["sha256"],
            spec["sources"]["pybind11"]["sha256"],
        )

    def test_dolfin_source_requirement_must_match_the_frozen_pybind11_version(self) -> None:
        spec = load_stack_spec(self.spec_path)
        with tempfile.TemporaryDirectory() as raw:
            setup_path = Path(raw) / "setup.py"
            setup_path.write_text(
                'REQUIREMENTS = ["numpy", "pybind11==2.2.4"]\n',
                encoding="utf-8",
            )
            self.assertEqual(
                validate_dolfin_python_contract(spec, setup_path),
                "pybind11==2.2.4",
            )

            setup_path.write_text(
                'REQUIREMENTS = ["numpy", "pybind11==2.2.3"]\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                LegacyStackContractError,
                "DOLFIN requires pybind11==2.2.3.*frozen pybind11==2.2.4",
            ):
                validate_dolfin_python_contract(spec, setup_path)

    def test_frozen_mumps_archive_is_retained_and_explicitly_consumed(self) -> None:
        spec = load_stack_spec(self.spec_path)
        mumps = spec["sources"]["mumps"]

        self.assertEqual(mumps["version"], "5.3.5")
        self.assertEqual(
            mumps["url"],
            "https://ftp.mcs.anl.gov/pub/petsc/externalpackages/MUMPS_5.3.5.tar.gz",
        )
        self.assertEqual(mumps["filename"], "MUMPS_5.3.5.tar.gz")
        self.assertEqual(mumps["sha256_policy"], "FIRST_RESOLUTION_LOCK")
        self.assertEqual(
            mumps["retained_relative_path"],
            "downloads/petsc/MUMPS_5.3.5.tar.gz",
        )
        self.assertIn(
            f'--download-mumps={spec["install_prefix"]}/'
            "downloads/petsc/MUMPS_5.3.5.tar.gz",
            spec["petsc"]["configure_options"],
        )

    def test_ptscotch_download_rejects_a_spec_without_bison(self) -> None:
        spec = load_stack_spec(self.spec_path)
        missing_bison = copy.deepcopy(spec)
        missing_bison["system_packages"]["install"].remove("bison")

        with self.assertRaisesRegex(LegacyStackContractError, "PTScotch requires bison"):
            build_execution_plan(missing_bison)

    def test_ptscotch_download_rejects_a_spec_without_flex(self) -> None:
        spec = load_stack_spec(self.spec_path)
        missing_flex = copy.deepcopy(spec)
        missing_flex["system_packages"]["install"].remove("flex")

        with self.assertRaisesRegex(LegacyStackContractError, "PTScotch requires flex"):
            build_execution_plan(missing_flex)

    def test_spec_rejects_an_apt_openmpi_or_unfrozen_known_source(self) -> None:
        spec = load_stack_spec(self.spec_path)
        bad_apt = copy.deepcopy(spec)
        bad_apt["system_packages"]["install"].append("openmpi-bin")
        with self.assertRaisesRegex(LegacyStackContractError, "forbidden system package"):
            build_execution_plan(bad_apt)

        missing_sowing_cxx = copy.deepcopy(spec)
        missing_sowing_cxx["petsc"]["configure_options"] = [
            option
            for option in missing_sowing_cxx["petsc"]["configure_options"]
            if not option.startswith("-download-sowing-cxx=")
        ]
        with self.assertRaisesRegex(LegacyStackContractError, "SOWING compiler binding"):
            build_execution_plan(missing_sowing_cxx)

        bad_petsc = copy.deepcopy(spec)
        bad_petsc["sources"]["petsc"]["commit"] = None
        with self.assertRaisesRegex(LegacyStackContractError, "PETSc commit"):
            build_execution_plan(bad_petsc)

    def test_root_execution_environment_explicitly_allows_only_frozen_openmpi(self) -> None:
        spec = load_stack_spec(self.spec_path)
        env = build_stack_environment(
            spec,
            inherited_environment={
                "PATH": "/usr/bin",
                "LD_LIBRARY_PATH": "",
                "CMAKE_PREFIX_PATH": "",
            },
        )

        self.assertEqual(env["OMPI_ALLOW_RUN_AS_ROOT"], "1")
        self.assertEqual(env["OMPI_ALLOW_RUN_AS_ROOT_CONFIRM"], "1")
        self.assertTrue(
            env["PATH"].startswith(
                f'{spec["install_prefix"]}/py38/bin:'
                f'{spec["install_prefix"]}/openmpi-3.1.6/bin:'
            )
        )
        self.assertNotIn("/usr/lib/x86_64-linux-gnu/openmpi", env["PATH"])

    def test_build_environment_excludes_host_anaconda_from_hdf5_search(self) -> None:
        spec = load_stack_spec(self.spec_path)
        env = build_stack_environment(
            spec,
            inherited_environment={
                "PATH": "/mnt/d/anaconda/Library/bin:/usr/bin",
                "LD_LIBRARY_PATH": "/mnt/d/anaconda/Library/bin",
                "CMAKE_PREFIX_PATH": "/mnt/d/anaconda/Library",
                "PKG_CONFIG_PATH": "/mnt/d/anaconda/Library/lib/pkgconfig",
                "HDF5_DIR": "/mnt/d/anaconda/Library/share/cmake/hdf5",
                "HDF5_ROOT": "/mnt/d/anaconda/Library",
                "UNRELATED_FROZEN_INPUT": "preserved",
            },
        )

        self.assertEqual(
            env["PATH"],
            f'{spec["install_prefix"]}/py38/bin:'
            f'{spec["install_prefix"]}/openmpi-3.1.6/bin:'
            "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        )
        self.assertNotIn("/mnt/", env["LD_LIBRARY_PATH"])
        self.assertNotIn("/mnt/", env["CMAKE_PREFIX_PATH"])
        self.assertEqual(
            env["PKG_CONFIG_PATH"],
            f'{spec["install_prefix"]}/fenics/dolfin/lib/pkgconfig',
        )
        self.assertTrue(
            env["CMAKE_PREFIX_PATH"].startswith(
                f'{spec["install_prefix"]}/providers/pybind11-2.2.4:'
            )
        )
        self.assertEqual(
            env["pybind11_DIR"],
            f'{spec["install_prefix"]}/providers/pybind11-2.2.4/'
            "share/cmake/pybind11",
        )
        self.assertNotIn("HDF5_DIR", env)
        self.assertNotIn("HDF5_ROOT", env)
        self.assertEqual(env["UNRELATED_FROZEN_INPUT"], "preserved")

    def test_offline_build_environment_rejects_python_and_network_resolution_injection(self) -> None:
        spec = load_stack_spec(self.spec_path)
        env = build_stack_environment(
            spec,
            inherited_environment={
                "PIP_INDEX_URL": "https://mirror.invalid/simple",
                "PIP_EXTRA_INDEX_URL": "https://extra.invalid/simple",
                "PIP_FIND_LINKS": "https://links.invalid/",
                "PIP_TRUSTED_HOST": "mirror.invalid",
                "PYTHONPATH": "/tmp/injected-python",
                "PYTHONHOME": "/tmp/injected-home",
                "CMAKE_ARGS": "-DUNFROZEN=ON",
                "HTTP_PROXY": "http://proxy.invalid",
                "HTTPS_PROXY": "http://proxy.invalid",
                "ALL_PROXY": "socks5://proxy.invalid",
            },
            offline_build=True,
        )

        for key in (
            "PIP_INDEX_URL",
            "PIP_EXTRA_INDEX_URL",
            "PIP_FIND_LINKS",
            "PIP_TRUSTED_HOST",
            "PYTHONHOME",
            "CMAKE_ARGS",
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "ALL_PROXY",
        ):
            self.assertNotIn(key, env)
        self.assertEqual(
            env["PYTHONPATH"],
            f'{spec["install_prefix"]}/src/petsc/'
            f'{spec["petsc"]["arch"]}/lib',
        )
        self.assertNotEqual(env["PYTHONPATH"], "/tmp/injected-python")
        self.assertEqual(env["PIP_NO_INDEX"], "1")
        self.assertEqual(env["PIP_NO_DEPS"], "1")
        self.assertEqual(env["PIP_DISABLE_PIP_VERSION_CHECK"], "1")
        self.assertEqual(env["PIP_CONFIG_FILE"], "/dev/null")
        self.assertEqual(env["PYTHONNOUSERSITE"], "1")

    def test_build_plan_installs_dolfin_python_from_the_local_environment_without_resolution(self) -> None:
        spec = load_stack_spec(self.spec_path)
        build_stage = next(
            stage for stage in build_execution_plan(spec) if stage["id"] == "build"
        )

        self.assertEqual(
            build_stage["dolfin_python_install_command"],
            [
                "/usr/bin/env",
                "CIRCLECI=1",
                f'{spec["install_prefix"]}/py38/bin/python',
                "-m",
                "pip",
                "install",
                "--no-index",
                "--no-deps",
                "--no-build-isolation",
                f'{spec["install_prefix"]}/src/dolfin/python',
            ],
        )

    def test_resolution_plan_installs_the_frozen_pybind11_cmake_provider(self) -> None:
        spec = load_stack_spec(self.spec_path)
        resolve_stage = next(
            stage for stage in build_execution_plan(spec) if stage["id"] == "resolve"
        )
        prefix = spec["install_prefix"]
        provider = resolve_stage["pybind11_provider"]

        self.assertEqual(
            provider["source"],
            {
                "url": spec["sources"]["pybind11_cmake_provider"]["archive_url"],
                "path": (
                    f"{prefix}/downloads/pybind11/"
                    "pybind11-v2.2.4-git-9a19306.tar.gz"
                ),
                "filename": "pybind11-v2.2.4-git-9a19306.tar.gz",
                "archive_root": (
                    "pybind11-9a19306fbf30642ca331d0ec88e7da54a96860f9"
                ),
                "sha256": spec["sources"]["pybind11_cmake_provider"]["sha256"],
                "repository": "https://github.com/pybind/pybind11.git",
                "tag": "v2.2.4",
                "tag_object": "e4637eb508aa3e41233875f6ce3891d96fbc5d33",
                "commit": "9a19306fbf30642ca331d0ec88e7da54a96860f9",
            },
        )
        self.assertEqual(
            provider["configure_command"],
            [
                "cmake",
                "-S",
                (
                    f"{prefix}/src/"
                    "pybind11-9a19306fbf30642ca331d0ec88e7da54a96860f9"
                ),
                "-B",
                (
                    f"{prefix}/src/"
                    "pybind11-9a19306fbf30642ca331d0ec88e7da54a96860f9/"
                    "build-g2-provider"
                ),
                "-DPYBIND11_TEST=OFF",
                "-DPYBIND11_INSTALL=ON",
                f"-DCMAKE_INSTALL_PREFIX={prefix}/providers/pybind11-2.2.4",
            ],
        )
        self.assertEqual(
            provider["install_command"],
            [
                "cmake",
                "--install",
                (
                    f"{prefix}/src/"
                    "pybind11-9a19306fbf30642ca331d0ec88e7da54a96860f9/"
                    "build-g2-provider"
                ),
            ],
        )
        self.assertEqual(
            provider["cmake_config_path"],
            f"{prefix}/providers/pybind11-2.2.4/"
            "share/cmake/pybind11/pybind11Config.cmake",
        )

    def test_source_checkout_identity_rejects_tracked_worktree_drift(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            checkout = Path(raw) / "source"
            checkout.mkdir()
            for command in (
                ["git", "init", "--quiet"],
                ["git", "config", "user.name", "Legacy Stack Test"],
                ["git", "config", "user.email", "legacy-stack@example.invalid"],
            ):
                subprocess.run(command, cwd=checkout, check=True, capture_output=True)
            tracked = checkout / "tracked.txt"
            tracked.write_text("frozen\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=checkout, check=True)
            subprocess.run(
                ["git", "commit", "--quiet", "-m", "frozen source"],
                cwd=checkout,
                check=True,
                capture_output=True,
            )

            identity = inspect_clean_source_checkout(checkout)
            self.assertRegex(identity["commit"], r"^[0-9a-f]{40}$")
            self.assertRegex(identity["tree"], r"^[0-9a-f]{40}$")
            self.assertRegex(identity["archive_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(identity["archive_format"], "git-archive-tar")

            tracked.write_text("drifted\n", encoding="utf-8")
            with self.assertRaisesRegex(LegacyStackContractError, "tracked worktree drift"):
                inspect_clean_source_checkout(checkout)

    def test_cached_git_external_is_locked_from_checkout_without_a_repeated_log_url(self) -> None:
        spec = load_stack_spec(self.spec_path)
        one_external = copy.deepcopy(spec)
        one_external["petsc"]["required_external_packages"] = ["fblaslapack"]

        with tempfile.TemporaryDirectory() as raw:
            petsc_root = Path(raw) / "petsc"
            checkout = (
                petsc_root
                / spec["petsc"]["arch"]
                / "externalpackages"
                / "git.fblaslapack"
            )
            checkout.mkdir(parents=True)
            for command in (
                ["git", "init", "--quiet"],
                ["git", "config", "user.name", "Legacy Stack Test"],
                ["git", "config", "user.email", "legacy-stack@example.invalid"],
            ):
                subprocess.run(command, cwd=checkout, check=True, capture_output=True)
            (checkout / "source.f").write_text("      END\n", encoding="utf-8")
            subprocess.run(["git", "add", "source.f"], cwd=checkout, check=True)
            subprocess.run(
                ["git", "commit", "--quiet", "-m", "frozen external"],
                cwd=checkout,
                check=True,
                capture_output=True,
            )
            origin = "https://bitbucket.org/petsc/pkg-fblaslapack"
            subprocess.run(
                ["git", "remote", "add", "origin", origin],
                cwd=checkout,
                check=True,
            )
            commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=checkout,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            tree = subprocess.run(
                ["git", "rev-parse", "HEAD^{tree}"],
                cwd=checkout,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            configure_log = petsc_root / "configure.log"
            configure_log.write_text("fblaslapack: cached checkout reused\n", encoding="utf-8")

            locked = lock_petsc_external_sources(
                one_external, petsc_root, configure_log
            )["fblaslapack"]

        self.assertEqual(locked["source_kind"], "git-checkout")
        self.assertEqual(locked["urls"], [origin])
        self.assertEqual(locked["filename"], "git.fblaslapack")
        self.assertEqual(
            locked["relative_path"],
            f'{spec["petsc"]["arch"]}/externalpackages/git.fblaslapack',
        )
        self.assertEqual(locked["commit"], commit)
        self.assertEqual(locked["tree"], tree)
        self.assertEqual(locked["archive_format"], "git-archive-tar")
        self.assertRegex(locked["archive_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(locked["sha256"], locked["archive_sha256"])

    def test_retained_mumps_archive_is_locked_without_a_repeated_log_url(self) -> None:
        spec = load_stack_spec(self.spec_path)
        one_external = copy.deepcopy(spec)
        one_external["petsc"]["required_external_packages"] = ["mumps"]

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            petsc_root = root / "petsc"
            petsc_root.mkdir()
            configure_log = petsc_root / "configure.log"
            configure_log.write_text(
                "MUMPS: consumed explicit local archive\n", encoding="utf-8"
            )
            retained_archive = root / "MUMPS_5.3.5.tar.gz"
            retained_archive.write_bytes(b"abc")

            locked = lock_petsc_external_sources(
                one_external,
                petsc_root,
                configure_log,
                retained_archives={"mumps": retained_archive},
            )["mumps"]

        self.assertEqual(locked["source_kind"], "retained-archive")
        self.assertEqual(locked["urls"], [spec["sources"]["mumps"]["url"]])
        self.assertEqual(locked["filename"], "MUMPS_5.3.5.tar.gz")
        self.assertEqual(locked["retained_path"], retained_archive.as_posix())
        self.assertEqual(
            locked["sha256"],
            "ba7816bf8f01cfea414140de5dae2223"
            "b00361a396177a9cb410ff61f20015ad",
        )

    def test_consumed_ptscotch_archive_is_locked_from_its_extracted_source_tree(self) -> None:
        spec = load_stack_spec(self.spec_path)
        one_external = copy.deepcopy(spec)
        one_external["petsc"]["required_external_packages"] = ["ptscotch"]
        source_url = (
            "https://gitlab.inria.fr/scotch/scotch/-/archive/v6.1.0/"
            "scotch-v6.1.0.tar.gz"
        )

        with tempfile.TemporaryDirectory() as raw:
            petsc_root = Path(raw) / "petsc"
            source_tree = (
                petsc_root
                / spec["petsc"]["arch"]
                / "externalpackages"
                / "scotch-v6.1.0"
            )
            (source_tree / "src").mkdir(parents=True)
            (source_tree / "LICENSE_en.txt").write_text("license\n", encoding="utf-8")
            (source_tree / "src" / "solver.c").write_text(
                "int solver(void) { return 0; }\n", encoding="utf-8"
            )
            configure_log = petsc_root / "configure.log"
            configure_log.write_text(f"Downloading {source_url}\n", encoding="utf-8")

            first = lock_petsc_external_sources(
                one_external, petsc_root, configure_log
            )["ptscotch"]
            second = lock_petsc_external_sources(
                one_external, petsc_root, configure_log
            )["ptscotch"]

        self.assertEqual(first, second)
        self.assertEqual(first["source_kind"], "extracted-source-tree")
        self.assertEqual(first["urls"], [source_url])
        self.assertEqual(first["filename"], "scotch-v6.1.0")
        self.assertEqual(
            first["relative_path"],
            f'{spec["petsc"]["arch"]}/externalpackages/scotch-v6.1.0',
        )
        self.assertEqual(first["tree_hash_algorithm"], "sha256-path-mode-content-v1")
        self.assertEqual(first["file_count"], 2)
        self.assertRegex(first["sha256"], r"^[0-9a-f]{64}$")

    def test_petsc_configuration_is_parsed_from_generated_header(self) -> None:
        header_bytes = (
            b"#define PETSC_USE_REAL_DOUBLE 1\n"
            b"#define PETSC_USE_64BIT_INDICES 1\n"
        )
        with tempfile.TemporaryDirectory() as raw:
            header = Path(raw) / "petscconf.h"
            header.write_bytes(header_bytes)
            configuration = parse_petsc_configuration(header)

        self.assertEqual(
            configuration,
            {
                "evidence_source": "petscconf.h",
                "petscconf_sha256": hashlib.sha256(header_bytes).hexdigest(),
                "scalar_type": "real",
                "precision": "double",
                "index_size_bits": 64,
                "debugging": False,
            },
        )

    def test_petsc_check_rejects_zero_exit_false_green_records(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            log_path = Path(raw) / "petsc-check.log"
            log_path.write_text(
                "Running PETSc check examples\nAll examples completed\n",
                encoding="utf-8",
            )
            self.assertEqual(
                validate_petsc_check_log(log_path),
                {"status": "PASS", "forbidden_records": []},
            )

            for record in (
                "Possible error running C/C++ src/snes/tutorials/ex19 with 1 MPI process",
                "Possible problem with ex19 running with mumps, diffs above",
                "mpiexec has detected an attempt to run as root.",
            ):
                log_path.write_text(
                    f"Running PETSc check examples\n{record}\n",
                    encoding="utf-8",
                )
                with self.subTest(record=record), self.assertRaisesRegex(
                    LegacyStackExecutionError,
                    "PETSc check log contains forbidden false-green records",
                ):
                    validate_petsc_check_log(log_path)

    def test_build_plan_runs_petsc_check_with_the_frozen_root_launcher(self) -> None:
        spec = load_stack_spec(self.spec_path)
        build_stage = next(
            stage for stage in build_execution_plan(spec) if stage["id"] == "build"
        )
        prefix = spec["install_prefix"]

        self.assertEqual(
            build_stage["petsc_check_command"],
            [
                "make",
                f"PETSC_DIR={prefix}/src/petsc",
                f'PETSC_ARCH={spec["petsc"]["arch"]}',
                f"MPIEXEC={prefix}/openmpi-3.1.6/bin/mpiexec --allow-run-as-root",
                "check",
            ],
        )

    def test_dolfin_python_build_uses_upstream_two_job_compatibility_branch(self) -> None:
        spec = load_stack_spec(self.spec_path)
        build_stage = next(
            stage for stage in build_execution_plan(spec) if stage["id"] == "build"
        )

        self.assertEqual(spec["build_jobs"], 2)
        self.assertEqual(
            build_stage["dolfin_python_install_command"][:2],
            ["/usr/bin/env", "CIRCLECI=1"],
        )
        self.assertEqual(
            build_stage["dolfin_python_parallelism"],
            {
                "effective_jobs": 2,
                "mechanism": "upstream-circleci-two-job-branch",
            },
        )

    def test_cpp_complete_python_pending_is_the_only_resumable_partial_build(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            petsc_lib = root / "petsc-lib"
            dolfin_build = root / "dolfin-build"
            dolfin_install = root / "dolfin-install"
            build_manifest = root / "build.manifest.json"

            self.assertEqual(
                classify_cpp_build_state(
                    petsc_library_dir=petsc_lib,
                    dolfin_build_dir=dolfin_build,
                    dolfin_install_dir=dolfin_install,
                    build_manifest=build_manifest,
                ),
                "CLEAN",
            )

            petsc_lib.mkdir()
            (petsc_lib / "libpetsc.so").write_bytes(b"petsc")
            dolfin_build.mkdir()
            (dolfin_build / "CMakeCache.txt").write_text("cache\n", encoding="utf-8")
            (dolfin_install / "lib").mkdir(parents=True)
            (dolfin_install / "lib" / "libdolfin.so").write_bytes(b"dolfin")
            self.assertEqual(
                classify_cpp_build_state(
                    petsc_library_dir=petsc_lib,
                    dolfin_build_dir=dolfin_build,
                    dolfin_install_dir=dolfin_install,
                    build_manifest=build_manifest,
                ),
                "CPP_COMPLETE_PYTHON_PENDING",
            )

            (dolfin_install / "lib" / "libdolfin.so").unlink()
            with self.assertRaisesRegex(
                LegacyStackContractError, "incomplete partial environment build"
            ):
                classify_cpp_build_state(
                    petsc_library_dir=petsc_lib,
                    dolfin_build_dir=dolfin_build,
                    dolfin_install_dir=dolfin_install,
                    build_manifest=build_manifest,
                )

    def test_cpp_complete_resume_accepts_only_the_frozen_petsc4py_build_addition(self) -> None:
        resolved = ["mpi4py==3.1.6", "pip==23.0.1"]

        validate_python_resolution_transition(
            resolved,
            [*resolved, "petsc4py==3.15.1"],
            allowed_build_additions=["petsc4py==3.15.1"],
        )
        with self.assertRaisesRegex(
            LegacyStackExecutionError, "Python environment drifted"
        ):
            validate_python_resolution_transition(
                resolved,
                [*resolved, "petsc4py==3.15.1", "unexpected==1.0"],
                allowed_build_additions=["petsc4py==3.15.1"],
            )

    def test_resolution_lock_must_bind_first_resolution_and_single_mpi_prefix(self) -> None:
        spec = load_stack_spec(self.spec_path)
        spec_sha256 = hashlib.sha256(self.spec_path.read_bytes()).hexdigest()
        lock = {
            "schema_version": "qpop-legacy-resolution-lock-v1",
            "status": "RESOLVED",
            "spec_sha256": spec_sha256,
            "install_prefix": spec["install_prefix"],
            "mpi_prefix": f'{spec["install_prefix"]}/openmpi-3.1.6',
            "os_release": {"ID": "ubuntu", "VERSION_ID": "20.04"},
            "apt_packages": {
                name: f"{index}.0-test"
                for index, name in enumerate(spec["system_packages"]["install"], start=1)
            },
            "compiler_identities": {
                key: {
                    "path": spec["toolchain"][key],
                    "version_line": "GNU 9 test" if key != "python" else "Python 3.8 test",
                    "sha256": "1" * 64,
                }
                for key in ("cc", "cxx", "fc", "python")
            },
            "python_freeze": ["numpy==1.23.5", "pybind11==2.2.4"],
            "python_artifacts": [
                {"filename": item["filename"], "sha256": item["sha256"]}
                for item in spec["python_resolution"]["known_artifacts"]
            ],
            "pybind11_provider": {
                "version": "2.2.4",
                "source_filename": "pybind11-v2.2.4-git-9a19306.tar.gz",
                "source_sha256": spec["sources"]["pybind11_cmake_provider"]["sha256"],
                "source_repository": spec["sources"]["pybind11_cmake_provider"]["repository"],
                "source_tag": spec["sources"]["pybind11_cmake_provider"]["tag"],
                "source_tag_object": spec["sources"]["pybind11_cmake_provider"]["tag_object"],
                "source_commit": spec["sources"]["pybind11_cmake_provider"]["commit"],
                "source_archive_root": spec["sources"]["pybind11_cmake_provider"]["archive_root"],
                "install_prefix": f'{spec["install_prefix"]}/providers/pybind11-2.2.4',
                "cmake_config_path": (
                    f'{spec["install_prefix"]}/providers/pybind11-2.2.4/'
                    "share/cmake/pybind11/pybind11Config.cmake"
                ),
                "cmake_config_sha256": "7" * 64,
            },
            "sources": {
                "openmpi": {
                    "version": spec["sources"]["openmpi"]["version"],
                    "url": spec["sources"]["openmpi"]["url"],
                    "sha1": spec["sources"]["openmpi"]["sha1"],
                    "sha256": "b" * 64,
                },
                "petsc": {
                    "repository": spec["sources"]["petsc"]["repository"],
                    "ref": spec["sources"]["petsc"]["ref"],
                    "commit": spec["sources"]["petsc"]["commit"],
                    "tree": "c" * 40,
                    "archive_format": "git-archive-tar",
                    "archive_sha256": "4" * 64,
                },
                "dolfin": {
                    "repository": spec["sources"]["dolfin"]["repository"],
                    "ref": spec["sources"]["dolfin"]["ref"],
                    "commit": "d" * 40,
                    "tree": "e" * 40,
                    "archive_format": "git-archive-tar",
                    "archive_sha256": "5" * 64,
                },
            },
            "petsc_external_packages": {
                **{
                    name: {
                        "urls": [f"https://example.invalid/{name}.tar.gz"],
                        "sha256": "f" * 64,
                    }
                    for name in spec["petsc"]["required_external_packages"]
                    if name != "mumps"
                },
                "mumps": {
                    "source_kind": "retained-archive",
                    "urls": [spec["sources"]["mumps"]["url"]],
                    "filename": spec["sources"]["mumps"]["filename"],
                    "retained_path": (
                        f'{spec["install_prefix"]}/'
                        f'{spec["sources"]["mumps"]["retained_relative_path"]}'
                    ),
                    "sha256": "f" * 64,
                },
            },
            "petsc_arch": spec["petsc"]["arch"],
            "petsc_configure_command": [
                f'{spec["install_prefix"]}/py38/bin/python',
                f'{spec["install_prefix"]}/src/petsc/configure',
                f'--with-mpi-dir={spec["install_prefix"]}/openmpi-3.1.6',
                *spec["petsc"]["configure_options"],
            ],
            "petsc_configure_log_sha256": "2" * 64,
            "petsc_reconfigure_script_sha256": "3" * 64,
            "petsc_configuration": {
                "evidence_source": "petscconf.h",
                "petscconf_sha256": "6" * 64,
                "scalar_type": "real",
                "precision": "double",
                "index_size_bits": 32,
                "debugging": False,
            },
        }
        validate_resolution_lock(spec, lock, expected_spec_sha256=spec_sha256)

        stale_pybind_install = copy.deepcopy(lock)
        stale_pybind_install["python_freeze"] = [
            "numpy==1.23.5",
            "pybind11==2.2.3",
        ]
        with self.assertRaisesRegex(LegacyStackContractError, "installed pybind11 2.2.4"):
            validate_resolution_lock(
                spec,
                stale_pybind_install,
                expected_spec_sha256=spec_sha256,
            )

        missing_pybind_provider = copy.deepcopy(lock)
        del missing_pybind_provider["pybind11_provider"]
        with self.assertRaisesRegex(LegacyStackContractError, "pybind11 CMake provider"):
            validate_resolution_lock(
                spec,
                missing_pybind_provider,
                expected_spec_sha256=spec_sha256,
            )

        missing = copy.deepcopy(lock)
        del missing["petsc_external_packages"]["mumps"]
        with self.assertRaisesRegex(LegacyStackContractError, "mumps"):
            validate_resolution_lock(spec, missing, expected_spec_sha256=spec_sha256)

        unretained_mumps = copy.deepcopy(lock)
        unretained_mumps["petsc_external_packages"]["mumps"][
            "source_kind"
        ] = "archive"
        with self.assertRaisesRegex(LegacyStackContractError, "retained MUMPS"):
            validate_resolution_lock(
                spec, unretained_mumps, expected_spec_sha256=spec_sha256
            )

        mixed = copy.deepcopy(lock)
        mixed["mpi_prefix"] = "/usr/lib/x86_64-linux-gnu/openmpi"
        with self.assertRaisesRegex(LegacyStackContractError, "MPI prefix"):
            validate_resolution_lock(spec, mixed, expected_spec_sha256=spec_sha256)

        unhashed_source = copy.deepcopy(lock)
        del unhashed_source["sources"]["petsc"]["archive_sha256"]
        with self.assertRaisesRegex(LegacyStackContractError, "PETSc source archive SHA256"):
            validate_resolution_lock(
                spec, unhashed_source, expected_spec_sha256=spec_sha256
            )

        incomplete_configuration = copy.deepcopy(lock)
        del incomplete_configuration["petsc_configuration"]["precision"]
        with self.assertRaisesRegex(LegacyStackContractError, "PETSc resolved configuration"):
            validate_resolution_lock(
                spec, incomplete_configuration, expected_spec_sha256=spec_sha256
            )

        incomplete_apt = copy.deepcopy(lock)
        del incomplete_apt["apt_packages"]["cmake"]
        with self.assertRaisesRegex(LegacyStackContractError, "apt package cmake"):
            validate_resolution_lock(spec, incomplete_apt, expected_spec_sha256=spec_sha256)

        wrong_configure_python = copy.deepcopy(lock)
        wrong_configure_python["petsc_configure_command"][0] = "/usr/bin/python3"
        with self.assertRaisesRegex(LegacyStackContractError, "configure command"):
            validate_resolution_lock(
                spec, wrong_configure_python, expected_spec_sha256=spec_sha256
            )

    def test_preflight_report_is_the_single_build_admission_contract(self) -> None:
        spec = load_stack_spec(self.spec_path)
        spec_sha256 = hashlib.sha256(self.spec_path.read_bytes()).hexdigest()
        lock_sha256 = "8" * 64
        prefix = spec["install_prefix"]
        report = {
            "schema_version": "qpop-legacy-preflight-v1",
            "status": "PREFLIGHT_PASS",
            "environment_id": spec["environment_id"],
            "spec_sha256": spec_sha256,
            "resolution_lock_sha256": lock_sha256,
            "resolution_state_revalidated": True,
            "clean_prefix": True,
            "dolfin_pybind11_requirement": "pybind11==2.2.4",
            "pybind11_provider": {
                "version": "2.2.4",
                "source_sha256": spec["sources"]["pybind11_cmake_provider"]["sha256"],
                "source_commit": spec["sources"]["pybind11_cmake_provider"]["commit"],
                "cmake_config_path": (
                    f"{prefix}/providers/pybind11-2.2.4/"
                    "share/cmake/pybind11/pybind11Config.cmake"
                ),
                "cmake_config_sha256": "9" * 64,
                "cmake_find_package": "PASS",
            },
            "offline_build": {
                "pip_no_index": True,
                "pip_no_deps": True,
                "pip_no_build_isolation": True,
                "environment_sanitized": True,
            },
            "mpi": {
                "version": "Open MPI v3.1.6",
                "wrapper_prefix": f"{prefix}/openmpi-3.1.6",
                "executables": {
                    name: f"{prefix}/openmpi-3.1.6/bin/{name}"
                    for name in (
                        "mpirun",
                        "mpiexec",
                        "ompi_info",
                        "mpicc",
                        "mpicxx",
                        "mpifort",
                    )
                },
                "compiler_commands": {
                    "mpicc": spec["toolchain"]["cc"],
                    "mpicxx": spec["toolchain"]["cxx"],
                    "mpifort": spec["toolchain"]["fc"],
                },
                "probes": {
                    "1": {"status": "PASS", "ranks": [0]},
                    "2": {"status": "PASS", "ranks": [0, 1]},
                },
                "mpi4py_libmpi": [
                    f"{prefix}/openmpi-3.1.6/lib/libmpi.so.40"
                ],
            },
        }

        validate_preflight_report(
            spec,
            report,
            expected_spec_sha256=spec_sha256,
            expected_resolution_lock_sha256=lock_sha256,
        )

        missing_rank = copy.deepcopy(report)
        missing_rank["mpi"]["probes"]["2"]["ranks"] = [0]
        with self.assertRaisesRegex(LegacyStackContractError, "two-rank MPI probe"):
            validate_preflight_report(
                spec,
                missing_rank,
                expected_spec_sha256=spec_sha256,
                expected_resolution_lock_sha256=lock_sha256,
            )

        missing_dolfin_wrapper = copy.deepcopy(report)
        del missing_dolfin_wrapper["mpi"]["executables"]["mpifort"]
        with self.assertRaisesRegex(
            LegacyStackContractError,
            "MPI executable contract",
        ):
            validate_preflight_report(
                spec,
                missing_dolfin_wrapper,
                expected_spec_sha256=spec_sha256,
                expected_resolution_lock_sha256=lock_sha256,
            )

        wrong_wrapper_compiler = copy.deepcopy(report)
        wrong_wrapper_compiler["mpi"]["compiler_commands"]["mpicxx"] = "/usr/bin/g++"
        with self.assertRaisesRegex(
            LegacyStackContractError,
            "MPI compiler wrapper contract",
        ):
            validate_preflight_report(
                spec,
                wrong_wrapper_compiler,
                expected_spec_sha256=spec_sha256,
                expected_resolution_lock_sha256=lock_sha256,
            )

        network_open = copy.deepcopy(report)
        network_open["offline_build"]["pip_no_deps"] = False
        with self.assertRaisesRegex(LegacyStackContractError, "offline build contract"):
            validate_preflight_report(
                spec,
                network_open,
                expected_spec_sha256=spec_sha256,
                expected_resolution_lock_sha256=lock_sha256,
            )

    def test_check_spec_cli_is_read_only(self) -> None:
        # The public static seam must not need a WSL distribution or create a lock.
        with tempfile.TemporaryDirectory() as raw:
            copied = Path(raw) / "spec.json"
            copied.write_bytes(self.spec_path.read_bytes())
            spec = load_stack_spec(copied)
            build_execution_plan(spec)
            self.assertEqual(list(Path(raw).iterdir()), [copied])


if __name__ == "__main__":
    unittest.main()
