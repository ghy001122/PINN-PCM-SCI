"""Auditable Ubuntu 20.04 source-stack builder for the G2 Q-POP route.

The module deliberately stops at environment qualification.  It never imports or
launches Q-POP.  ``check-spec`` and ``print-plan`` are read-only on every host;
the mutating ``resolve``, ``build`` and ``verify`` commands are Linux-only and
require an explicit ``--execute`` acknowledgement.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SPEC_SCHEMA = "qpop-legacy-stack-spec-v1"
LOCK_SCHEMA = "qpop-legacy-resolution-lock-v1"
PREFLIGHT_SCHEMA = "qpop-legacy-preflight-v1"
BUILD_SCHEMA = "qpop-legacy-build-manifest-v1"
VERIFY_SCHEMA = "qpop-legacy-verification-v1"
MPI_EXECUTABLES = (
    "mpirun",
    "mpiexec",
    "ompi_info",
    "mpicc",
    "mpicxx",
    "mpifort",
)
MPI_COMPILER_WRAPPERS = {
    "mpicc": "cc",
    "mpicxx": "cxx",
    "mpifort": "fc",
}


class LegacyStackContractError(RuntimeError):
    """A frozen environment contract or its resolved evidence is invalid."""


class LegacyStackExecutionError(RuntimeError):
    """An external environment preparation or verification action failed."""


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LegacyStackContractError(f"{label} must be a JSON object")
    return value


def _require_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LegacyStackContractError(f"{label} must be a non-empty string")
    return value


def _is_hex(value: Any, length: int) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(rf"[0-9a-f]{{{length}}}", value))


def load_stack_spec(path: Path) -> dict[str, Any]:
    """Load and validate the frozen legacy-stack spec without side effects."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LegacyStackContractError(f"cannot read stack spec {path}: {exc}") from exc
    spec = _require_mapping(value, "stack spec")
    validate_stack_spec(spec)
    return spec


def validate_stack_spec(spec: Mapping[str, Any]) -> None:
    if spec.get("schema_version") != SPEC_SCHEMA:
        raise LegacyStackContractError(f"unsupported stack spec schema: {spec.get('schema_version')!r}")
    if spec.get("purpose") != "G2_QPOP_ENVIRONMENT_QUALIFICATION_ONLY":
        raise LegacyStackContractError("stack purpose must remain G2 environment qualification only")
    if spec.get("environment_id") != "qpop-cpc-v1-ubuntu-20.04-source-stack-v3":
        raise LegacyStackContractError("environment identity must remain on the G2 provider-corrected v3 contract")
    if spec.get("wsl_distro_name") != "PINN-PCM-SCI-Ubuntu-20.04":
        raise LegacyStackContractError("legacy stack must remain bound to the dedicated WSL distro")
    if spec.get("os") != {"id": "ubuntu", "version_id": "20.04"}:
        raise LegacyStackContractError("legacy stack requires exact Ubuntu 20.04")
    prefix = _require_nonempty_string(spec.get("install_prefix"), "install_prefix")
    if prefix != "/opt/qpop-cpc-v1-env-g2-final-002":
        raise LegacyStackContractError("install_prefix must remain the new clean G2 final prefix")
    build_jobs = spec.get("build_jobs")
    if build_jobs != 2:
        raise LegacyStackContractError(
            "build_jobs must remain 2 for the qualified 4 GiB WSL2 environment"
        )

    toolchain = _require_mapping(spec.get("toolchain"), "toolchain")
    if toolchain.get("gnu_major") != 9:
        raise LegacyStackContractError("GNU compiler major must remain 9")
    if toolchain.get("python_major_minor") != "3.8":
        raise LegacyStackContractError("Ubuntu legacy Python must remain 3.8")
    expected_tools = {
        "cc": "/usr/bin/gcc-9",
        "cxx": "/usr/bin/g++-9",
        "fc": "/usr/bin/gfortran-9",
        "python": "/usr/bin/python3",
    }
    for key, expected in expected_tools.items():
        if toolchain.get(key) != expected:
            raise LegacyStackContractError(f"toolchain {key} must be {expected}")

    system = _require_mapping(spec.get("system_packages"), "system_packages")
    install = system.get("install")
    forbidden = system.get("forbidden")
    if not isinstance(install, list) or not all(isinstance(item, str) for item in install):
        raise LegacyStackContractError("system_packages.install must be a string list")
    if not isinstance(forbidden, list) or not all(isinstance(item, str) for item in forbidden):
        raise LegacyStackContractError("system_packages.forbidden must be a string list")
    overlap = sorted(set(install).intersection(forbidden))
    if overlap:
        raise LegacyStackContractError(f"forbidden system package requested: {', '.join(overlap)}")

    sources = _require_mapping(spec.get("sources"), "sources")
    openmpi = _require_mapping(sources.get("openmpi"), "sources.openmpi")
    if openmpi.get("version") != "3.1.6" or openmpi.get("sha1") != "5c220f8f0c5070cbb43bc8af6200b91339cdccd5":
        raise LegacyStackContractError("OpenMPI must be official 3.1.6 with the frozen SHA1")
    if openmpi.get("sha256_policy") != "FIRST_RESOLUTION_LOCK":
        raise LegacyStackContractError("OpenMPI SHA256 must be captured in the first resolution lock")
    petsc = _require_mapping(sources.get("petsc"), "sources.petsc")
    if petsc.get("version") != "3.15.1" or not _is_hex(petsc.get("commit"), 40):
        raise LegacyStackContractError("PETSc commit must be the frozen 3.15.1 commit")
    if petsc.get("commit") != "09da24df01e50defd94bc4f7396f866a808ecea5":
        raise LegacyStackContractError("PETSc commit differs from official v3.15.1")
    dolfin = _require_mapping(sources.get("dolfin"), "sources.dolfin")
    if dolfin.get("ref") != "2019.1.0.post0" or dolfin.get("commit_policy") != "FIRST_RESOLUTION_LOCK":
        raise LegacyStackContractError("DOLFIN must resolve and lock tag 2019.1.0.post0")
    pybind11 = _require_mapping(sources.get("pybind11"), "sources.pybind11")
    expected_pybind11 = {
        "version": "2.2.4",
        "url": "https://files.pythonhosted.org/packages/source/p/pybind11/pybind11-2.2.4.tar.gz",
        "filename": "pybind11-2.2.4.tar.gz",
        "sha256": "642abbbd2948ed5af28e69adfae1535347c7aa9eb0cdab130e20e1f198f8e1cf",
    }
    if pybind11 != expected_pybind11:
        raise LegacyStackContractError("pybind11 2.2.4 source release identity is not frozen")
    pybind11_provider = _require_mapping(
        sources.get("pybind11_cmake_provider"),
        "sources.pybind11_cmake_provider",
    )
    expected_pybind11_provider = {
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
    }
    if pybind11_provider != expected_pybind11_provider:
        raise LegacyStackContractError(
            "pybind11 2.2.4 CMake provider Git identity is not frozen"
        )
    mumps = _require_mapping(sources.get("mumps"), "sources.mumps")
    expected_mumps_path = "downloads/petsc/MUMPS_5.3.5.tar.gz"
    if (
        mumps.get("version") != "5.3.5"
        or mumps.get("url")
        != "https://ftp.mcs.anl.gov/pub/petsc/externalpackages/MUMPS_5.3.5.tar.gz"
        or mumps.get("filename") != "MUMPS_5.3.5.tar.gz"
        or mumps.get("sha256_policy") != "FIRST_RESOLUTION_LOCK"
        or mumps.get("retained_relative_path") != expected_mumps_path
    ):
        raise LegacyStackContractError(
            "MUMPS 5.3.5 must use the retained first-resolution archive contract"
        )

    python = _require_mapping(spec.get("python_resolution"), "python_resolution")
    requirements = python.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        raise LegacyStackContractError("python requirements cannot be empty")
    if python.get("first_resolution_lock_required") is not True:
        raise LegacyStackContractError("Python transitive dependencies must be locked on first resolution")
    required_requirements = {
        "numpy<1.24",
        "Cython<3",
        "pybind11==2.2.4",
        "ply==3.11",
        "pkgconfig",
        "wheel",
        "mpi4py==3.0.3",
        "fenics-fiat==2019.1.0",
        "fenics-ufl==2019.1.0",
        "fenics-dijitso==2019.1.0",
        "fenics-ffc==2019.1.0.post0",
    }
    if set(requirements) != required_requirements or len(requirements) != len(required_requirements):
        if "pybind11==2.2.4" not in requirements:
            raise LegacyStackContractError("Python resolution must require pybind11 2.2.4")
        raise LegacyStackContractError("Python resolution input differs from the frozen bounded set")
    known_artifacts = python.get("known_artifacts")
    if not isinstance(known_artifacts, list) or not known_artifacts:
        raise LegacyStackContractError("known Python artifact hashes are required")
    for artifact in known_artifacts:
        item = _require_mapping(artifact, "known Python artifact")
        _require_nonempty_string(item.get("filename"), "known artifact filename")
        if not _is_hex(item.get("sha256"), 64):
            raise LegacyStackContractError("known Python artifact SHA256 must be 64 lowercase hex characters")
    expected_pybind_artifact = {
        "filename": pybind11["filename"],
        "sha256": pybind11["sha256"],
    }
    if expected_pybind_artifact not in known_artifacts:
        raise LegacyStackContractError("pybind11 source artifact hash is not frozen")

    petsc_config = _require_mapping(spec.get("petsc"), "petsc")
    if petsc_config.get("arch") != "arch-linux-qpop-opt":
        raise LegacyStackContractError("PETSc arch must remain arch-linux-qpop-opt")
    options = petsc_config.get("configure_options")
    if not isinstance(options, list):
        raise LegacyStackContractError("PETSc configure options must be a list")
    if "--download-ptscotch" in options and "bison" not in install:
        raise LegacyStackContractError("PTScotch requires bison in system_packages.install")
    if "--download-ptscotch" in options and "flex" not in install:
        raise LegacyStackContractError("PTScotch requires flex in system_packages.install")
    expected_petsc_options = {
        "--with-debugging=0",
        "--download-fblaslapack",
        "--download-metis",
        "--download-parmetis",
        "--download-ptscotch",
        "--download-suitesparse",
        f"--download-mumps={prefix}/{expected_mumps_path}",
        "--download-scalapack",
        "--download-hypre",
        "--with-petsc4py",
        "-download-sowing-cc=/usr/bin/gcc-9",
        "-download-sowing-cxx=/usr/bin/g++-9",
    }
    if not {
        "-download-sowing-cc=/usr/bin/gcc-9",
        "-download-sowing-cxx=/usr/bin/g++-9",
    }.issubset(options):
        raise LegacyStackContractError("PETSc SOWING compiler binding must remain on GNU 9")
    if set(options) != expected_petsc_options or len(options) != len(expected_petsc_options):
        raise LegacyStackContractError("PETSc configure options differ from the frozen feature set")
    required_downloads = petsc_config.get("required_external_packages")
    if not isinstance(required_downloads, list) or not required_downloads:
        raise LegacyStackContractError("PETSc external package list cannot be empty")
    for name in required_downloads:
        option_prefix = f"--download-{name}"
        if not any(
            option == option_prefix or option.startswith(f"{option_prefix}=")
            for option in options
        ):
            raise LegacyStackContractError(f"PETSc configure option missing --download-{name}")

    dolfin_config = _require_mapping(spec.get("dolfin"), "dolfin")
    expected_dolfin_options = {
        "-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_INSTALL_PREFIX={prefix}/fenics/dolfin",
        f"-DCMAKE_C_COMPILER={prefix}/openmpi-3.1.6/bin/mpicc",
        f"-DCMAKE_CXX_COMPILER={prefix}/openmpi-3.1.6/bin/mpicxx",
        f"-DCMAKE_Fortran_COMPILER={prefix}/openmpi-3.1.6/bin/mpifort",
    }
    actual_dolfin_options = dolfin_config.get("cmake_options")
    if not isinstance(actual_dolfin_options, list) or set(actual_dolfin_options) != expected_dolfin_options:
        raise LegacyStackContractError("DOLFIN CMake options must bind Release and the single OpenMPI prefix")

    rendered = json.dumps(spec, sort_keys=True).lower()
    if "qpop-imt.py" in rendered or "canonical_input" in rendered:
        raise LegacyStackContractError("environment stack spec must not launch or select a Q-POP case")


def build_execution_plan(spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return the three-stage plan consumed by callers and static tests."""

    validate_stack_spec(spec)
    prefix = str(spec["install_prefix"])
    mpi_prefix = f"{prefix}/openmpi-3.1.6"
    provider_source = spec["sources"]["pybind11_cmake_provider"]
    pybind_source = f"{prefix}/src/{provider_source['archive_root']}"
    pybind_build = f"{pybind_source}/build-g2-provider"
    pybind_provider = f"{prefix}/providers/pybind11-2.2.4"
    return [
        {
            "id": "resolve",
            "mutates_environment": True,
            "inputs": ["stack_spec.json", "Ubuntu 20.04 package repositories", "primary source archives"],
            "actions": [
                "resolve exact apt versions and record installed dpkg state",
                "resolve Python 3.8 artifacts and record every artifact SHA256",
                f"build openmpi-3.1.6 into {mpi_prefix}",
                "retain the MUMPS 5.3.5 tarball and bind PETSc to that local file",
                "resolve PETSc external package URLs and archive SHA256 values",
                "resolve the DOLFIN 2019.1.0.post0 tag commit and tree",
            ],
            "required_mpi_executables": list(MPI_EXECUTABLES),
            "pybind11_provider": {
                "source": {
                    "url": provider_source["archive_url"],
                    "path": f"{prefix}/downloads/pybind11/{provider_source['filename']}",
                    "filename": provider_source["filename"],
                    "archive_root": provider_source["archive_root"],
                    "sha256": provider_source["sha256"],
                    "repository": provider_source["repository"],
                    "tag": provider_source["tag"],
                    "tag_object": provider_source["tag_object"],
                    "commit": provider_source["commit"],
                },
                "configure_command": [
                    "cmake",
                    "-S",
                    pybind_source,
                    "-B",
                    pybind_build,
                    "-DPYBIND11_TEST=OFF",
                    "-DPYBIND11_INSTALL=ON",
                    f"-DCMAKE_INSTALL_PREFIX={pybind_provider}",
                ],
                "install_command": ["cmake", "--install", pybind_build],
                "cmake_config_path": (
                    f"{pybind_provider}/share/cmake/pybind11/pybind11Config.cmake"
                ),
            },
            "output": "resolution.lock.json",
        },
        {
            "id": "preflight",
            "mutates_environment": False,
            "requires": "resolution.lock.json",
            "actions": [
                "match DOLFIN's source requirement to frozen pybind11 2.2.4",
                "prove the source-built pybind11 CMake provider is discoverable",
                "reject Python cache, source, spec, MPI ABI or clean-prefix drift",
                "run one-rank and two-rank OpenMPI import barriers",
            ],
            "output": "preflight.json",
        },
        {
            "id": "build",
            "mutates_environment": True,
            "requires": ["resolution.lock.json", "preflight.json"],
            "actions": [
                "reject spec, source or resolution drift",
                "build PETSc arch-linux-qpop-opt with the frozen external feature set",
                "build and install DOLFIN/FEniCS 2019.1.0.post0",
            ],
            "dolfin_python_install_command": [
                "/usr/bin/env",
                "CIRCLECI=1",
                f"{prefix}/py38/bin/python",
                "-m",
                "pip",
                "install",
                "--no-index",
                "--no-deps",
                "--no-build-isolation",
                f"{prefix}/src/dolfin/python",
            ],
            "dolfin_python_parallelism": {
                "effective_jobs": 2,
                "mechanism": "upstream-circleci-two-job-branch",
            },
            "petsc_check_command": [
                "make",
                f"PETSC_DIR={prefix}/src/petsc",
                f"PETSC_ARCH={spec['petsc']['arch']}",
                f"MPIEXEC={mpi_prefix}/bin/mpiexec --allow-run-as-root",
                "check",
            ],
            "output": "build.manifest.json",
        },
        {
            "id": "verify",
            "mutates_environment": False,
            "requires": [
                "resolution.lock.json",
                "preflight.json",
                "build.manifest.json",
            ],
            "actions": [
                "verify Ubuntu 20.04, GNU 9, PETSc 3.15.1, MUMPS and ParMETIS",
                f"require all Python and solver modules to resolve libmpi below {mpi_prefix}",
                "run a two-rank import and communicator barrier only",
            ],
            "output": "verification.json",
        },
    ]


def validate_dolfin_python_contract(
    spec: Mapping[str, Any], setup_path: Path
) -> str:
    """Return DOLFIN's pybind11 requirement after matching it to the frozen spec."""

    validate_stack_spec(spec)
    try:
        tree = ast.parse(setup_path.read_text(encoding="utf-8"), filename=str(setup_path))
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        raise LegacyStackContractError(
            f"cannot inspect DOLFIN Python requirements at {setup_path}: {exc}"
        ) from exc
    requirements: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value.startswith("pybind11"):
                requirements.append(node.value)
    unique = sorted(set(requirements))
    if len(unique) != 1:
        raise LegacyStackContractError(
            f"DOLFIN setup.py must declare exactly one pybind11 requirement, found {unique}"
        )
    actual = unique[0]
    expected = f"pybind11=={spec['sources']['pybind11']['version']}"
    if actual != expected:
        raise LegacyStackContractError(
            f"DOLFIN requires {actual}, but the frozen {expected} contract is required"
        )
    return actual


def validate_resolution_lock(
    spec: Mapping[str, Any],
    lock: Mapping[str, Any],
    *,
    expected_spec_sha256: str,
) -> None:
    """Validate that first-resolution evidence is complete and spec-bound."""

    validate_stack_spec(spec)
    if lock.get("schema_version") != LOCK_SCHEMA or lock.get("status") != "RESOLVED":
        raise LegacyStackContractError("resolution lock is not a completed v1 lock")
    if lock.get("spec_sha256") != expected_spec_sha256:
        raise LegacyStackContractError("resolution lock does not bind the current spec SHA256")
    if lock.get("install_prefix") != spec["install_prefix"]:
        raise LegacyStackContractError("resolution lock install prefix differs from the spec")
    expected_mpi = f"{spec['install_prefix']}/openmpi-3.1.6"
    if lock.get("mpi_prefix") != expected_mpi:
        raise LegacyStackContractError(f"resolution lock MPI prefix must be {expected_mpi}")
    os_release = _require_mapping(lock.get("os_release"), "resolution OS identity")
    if os_release.get("ID") != "ubuntu" or os_release.get("VERSION_ID") != "20.04":
        raise LegacyStackContractError("resolution lock OS identity is not Ubuntu 20.04")
    apt_packages = lock.get("apt_packages")
    python_freeze = lock.get("python_freeze")
    python_artifacts = lock.get("python_artifacts")
    if not isinstance(apt_packages, dict) or not apt_packages:
        raise LegacyStackContractError("resolution lock has no exact apt package versions")
    apt_versions_by_name = {
        str(name).split(":", 1)[0]: version for name, version in apt_packages.items()
    }
    for package in spec["system_packages"]["install"]:
        version = apt_versions_by_name.get(package)
        if not isinstance(version, str) or not version:
            raise LegacyStackContractError(
                f"resolution lock lacks exact apt package {package}"
            )
    locked_forbidden = sorted(
        set(apt_versions_by_name).intersection(spec["system_packages"]["forbidden"])
    )
    if locked_forbidden:
        raise LegacyStackContractError(
            "resolution lock contains forbidden apt packages: "
            + ", ".join(locked_forbidden)
        )
    if not isinstance(python_freeze, list) or not python_freeze:
        raise LegacyStackContractError("resolution lock has no Python freeze")
    frozen_pybind = [
        item for item in python_freeze if str(item).lower().startswith("pybind11==")
    ]
    if frozen_pybind != ["pybind11==2.2.4"]:
        raise LegacyStackContractError(
            "resolution lock must prove installed pybind11 2.2.4"
        )
    if not isinstance(python_artifacts, list) or not python_artifacts:
        raise LegacyStackContractError("resolution lock has no Python artifact hashes")
    for artifact in python_artifacts:
        item = _require_mapping(artifact, "locked Python artifact")
        if not _is_hex(item.get("sha256"), 64):
            raise LegacyStackContractError("locked Python artifact has an invalid SHA256")
    artifact_by_name = {str(item.get("filename")): item for item in python_artifacts}
    for known in spec["python_resolution"]["known_artifacts"]:
        if artifact_by_name.get(known["filename"], {}).get("sha256") != known["sha256"]:
            raise LegacyStackContractError(
                f"resolution lock lost known Python artifact {known['filename']}"
            )
    try:
        provider = _require_mapping(
            lock.get("pybind11_provider"), "pybind11 CMake provider"
        )
    except LegacyStackContractError as exc:
        raise LegacyStackContractError("resolution lock has no pybind11 CMake provider") from exc
    pybind_source = spec["sources"]["pybind11_cmake_provider"]
    provider_prefix = f"{spec['install_prefix']}/providers/pybind11-2.2.4"
    provider_config = f"{provider_prefix}/share/cmake/pybind11/pybind11Config.cmake"
    if (
        provider.get("version") != pybind_source["version"]
        or provider.get("source_filename") != pybind_source["filename"]
        or provider.get("source_sha256") != pybind_source["sha256"]
        or provider.get("source_repository") != pybind_source["repository"]
        or provider.get("source_tag") != pybind_source["tag"]
        or provider.get("source_tag_object") != pybind_source["tag_object"]
        or provider.get("source_commit") != pybind_source["commit"]
        or provider.get("source_archive_root") != pybind_source["archive_root"]
        or provider.get("install_prefix") != provider_prefix
        or provider.get("cmake_config_path") != provider_config
        or not _is_hex(provider.get("cmake_config_sha256"), 64)
    ):
        raise LegacyStackContractError("pybind11 CMake provider identity is incomplete or drifted")

    compilers = _require_mapping(lock.get("compiler_identities"), "compiler identities")
    for key in ("cc", "cxx", "fc", "python"):
        identity = _require_mapping(compilers.get(key), f"compiler identity {key}")
        if identity.get("path") != spec["toolchain"][key] or not _is_hex(identity.get("sha256"), 64):
            raise LegacyStackContractError(f"compiler identity {key} is incomplete or drifted")

    sources = _require_mapping(lock.get("sources"), "resolution sources")
    openmpi = _require_mapping(sources.get("openmpi"), "locked OpenMPI")
    expected_openmpi = spec["sources"]["openmpi"]
    if (
        openmpi.get("version") != expected_openmpi["version"]
        or openmpi.get("url") != expected_openmpi["url"]
        or openmpi.get("sha1") != expected_openmpi["sha1"]
    ):
        raise LegacyStackContractError("OpenMPI source identity differs from the frozen release")
    if not _is_hex(openmpi.get("sha256"), 64):
        raise LegacyStackContractError("OpenMPI first-resolution SHA256 is missing")
    petsc = _require_mapping(sources.get("petsc"), "locked PETSc")
    expected_petsc = spec["sources"]["petsc"]
    if (
        petsc.get("repository") != expected_petsc["repository"]
        or petsc.get("ref") != expected_petsc["ref"]
        or petsc.get("commit") != expected_petsc["commit"]
        or not _is_hex(petsc.get("tree"), 40)
    ):
        raise LegacyStackContractError("PETSc source identity differs from the frozen commit")
    if (
        petsc.get("archive_format") != "git-archive-tar"
        or not _is_hex(petsc.get("archive_sha256"), 64)
    ):
        raise LegacyStackContractError("resolution lock lacks the PETSc source archive SHA256")
    dolfin = _require_mapping(sources.get("dolfin"), "locked DOLFIN")
    expected_dolfin = spec["sources"]["dolfin"]
    if (
        dolfin.get("repository") != expected_dolfin["repository"]
        or dolfin.get("ref") != expected_dolfin["ref"]
        or not _is_hex(dolfin.get("commit"), 40)
        or not _is_hex(dolfin.get("tree"), 40)
    ):
        raise LegacyStackContractError("DOLFIN tag commit and tree must be locked on first resolution")
    if (
        dolfin.get("archive_format") != "git-archive-tar"
        or not _is_hex(dolfin.get("archive_sha256"), 64)
    ):
        raise LegacyStackContractError("resolution lock lacks the DOLFIN source archive SHA256")

    external = _require_mapping(lock.get("petsc_external_packages"), "PETSc external package lock")
    for name in spec["petsc"]["required_external_packages"]:
        item = _require_mapping(external.get(name), f"PETSc external package {name}")
        urls = item.get("urls")
        if not isinstance(urls, list) or not urls or not all(
            isinstance(url, str) and re.match(r"^(?:https?|ftp)://", url) for url in urls
        ):
            raise LegacyStackContractError(f"PETSc external package {name} lacks its resolved URL")
        if not _is_hex(item.get("sha256"), 64):
            raise LegacyStackContractError(f"PETSc external package {name} lacks its resolved SHA256")
        if item.get("source_kind") == "extracted-source-tree":
            if (
                item.get("tree_hash_algorithm") != "sha256-path-mode-content-v1"
                or item.get("tree_sha256") != item.get("sha256")
                or not isinstance(item.get("file_count"), int)
                or item.get("file_count", 0) <= 0
                or not str(item.get("relative_path", "")).startswith(
                    f"{spec['petsc']['arch']}/externalpackages/"
                )
            ):
                raise LegacyStackContractError(
                    f"PETSc external package {name} has an incomplete extracted-tree identity"
                )
    mumps_lock = _require_mapping(
        external.get("mumps"), "PETSc retained MUMPS archive"
    )
    expected_mumps = spec["sources"]["mumps"]
    expected_mumps_path = (
        f"{spec['install_prefix']}/{expected_mumps['retained_relative_path']}"
    )
    if (
        mumps_lock.get("source_kind") != "retained-archive"
        or mumps_lock.get("urls") != [expected_mumps["url"]]
        or mumps_lock.get("filename") != expected_mumps["filename"]
        or mumps_lock.get("retained_path") != expected_mumps_path
    ):
        raise LegacyStackContractError(
            "resolution lock does not bind the retained MUMPS archive contract"
        )
    if lock.get("petsc_arch") != spec["petsc"]["arch"]:
        raise LegacyStackContractError("resolution lock PETSc arch differs from the spec")
    configure_command = lock.get("petsc_configure_command")
    expected_configure_command = [
        f"{spec['install_prefix']}/py38/bin/python",
        f"{spec['install_prefix']}/src/petsc/configure",
        f"--with-mpi-dir={expected_mpi}",
        *spec["petsc"]["configure_options"],
    ]
    if configure_command != expected_configure_command:
        raise LegacyStackContractError("resolution lock PETSc configure command drifted")
    for hash_field in ("petsc_configure_log_sha256", "petsc_reconfigure_script_sha256"):
        if not _is_hex(lock.get(hash_field), 64):
            raise LegacyStackContractError(f"resolution lock lacks {hash_field}")
    configuration = _require_mapping(
        lock.get("petsc_configuration"), "PETSc resolved configuration"
    )
    if (
        configuration.get("evidence_source") != "petscconf.h"
        or not _is_hex(configuration.get("petscconf_sha256"), 64)
        or configuration.get("scalar_type") not in {"real", "complex"}
        or configuration.get("precision")
        not in {"single", "double", "__float128", "__fp16"}
        or configuration.get("index_size_bits") not in {32, 64}
        or not isinstance(configuration.get("debugging"), bool)
    ):
        raise LegacyStackContractError("PETSc resolved configuration is incomplete or invalid")
    if configuration["debugging"] is not False:
        raise LegacyStackContractError(
            "PETSc resolved configuration contradicts --with-debugging=0"
        )


def validate_preflight_report(
    spec: Mapping[str, Any],
    report: Mapping[str, Any],
    *,
    expected_spec_sha256: str,
    expected_resolution_lock_sha256: str,
) -> None:
    """Validate the single machine-readable admission record for a long build."""

    validate_stack_spec(spec)
    if report.get("schema_version") != PREFLIGHT_SCHEMA or report.get("status") != "PREFLIGHT_PASS":
        raise LegacyStackContractError("preflight report is not a completed pass record")
    if report.get("environment_id") != spec["environment_id"]:
        raise LegacyStackContractError("preflight report environment identity drifted")
    if report.get("spec_sha256") != expected_spec_sha256:
        raise LegacyStackContractError("preflight report does not bind the current spec")
    if report.get("resolution_lock_sha256") != expected_resolution_lock_sha256:
        raise LegacyStackContractError("preflight report does not bind the resolution lock")
    if report.get("resolution_state_revalidated") is not True:
        raise LegacyStackContractError("preflight did not revalidate the resolution state")
    if report.get("clean_prefix") is not True:
        raise LegacyStackContractError("preflight did not prove a clean build prefix")
    if report.get("dolfin_pybind11_requirement") != "pybind11==2.2.4":
        raise LegacyStackContractError("preflight DOLFIN pybind11 requirement drifted")

    provider = _require_mapping(report.get("pybind11_provider"), "preflight pybind11 provider")
    provider_prefix = f"{spec['install_prefix']}/providers/pybind11-2.2.4"
    expected_config = f"{provider_prefix}/share/cmake/pybind11/pybind11Config.cmake"
    if (
        provider.get("version") != "2.2.4"
        or provider.get("source_sha256")
        != spec["sources"]["pybind11_cmake_provider"]["sha256"]
        or provider.get("source_commit")
        != spec["sources"]["pybind11_cmake_provider"]["commit"]
        or provider.get("cmake_config_path") != expected_config
        or not _is_hex(provider.get("cmake_config_sha256"), 64)
        or provider.get("cmake_find_package") != "PASS"
    ):
        raise LegacyStackContractError("preflight pybind11 CMake provider is incomplete or drifted")

    offline = _require_mapping(report.get("offline_build"), "offline build contract")
    if offline != {
        "pip_no_index": True,
        "pip_no_deps": True,
        "pip_no_build_isolation": True,
        "environment_sanitized": True,
    }:
        raise LegacyStackContractError("preflight offline build contract is incomplete")

    mpi = _require_mapping(report.get("mpi"), "preflight MPI evidence")
    mpi_prefix = f"{spec['install_prefix']}/openmpi-3.1.6"
    if "3.1.6" not in str(mpi.get("version", "")) or mpi.get("wrapper_prefix") != mpi_prefix:
        raise LegacyStackContractError("preflight MPI identity drifted")
    expected_executables = {
        name: f"{mpi_prefix}/bin/{name}" for name in MPI_EXECUTABLES
    }
    if mpi.get("executables") != expected_executables:
        raise LegacyStackContractError(
            "preflight MPI executable contract is incomplete or drifted"
        )
    expected_compiler_commands = {
        wrapper: str(spec["toolchain"][toolchain_key])
        for wrapper, toolchain_key in MPI_COMPILER_WRAPPERS.items()
    }
    if mpi.get("compiler_commands") != expected_compiler_commands:
        raise LegacyStackContractError(
            "preflight MPI compiler wrapper contract is incomplete or drifted"
        )
    probes = _require_mapping(mpi.get("probes"), "preflight MPI probes")
    one_rank = _require_mapping(probes.get("1"), "one-rank MPI probe")
    two_rank = _require_mapping(probes.get("2"), "two-rank MPI probe")
    if one_rank != {"status": "PASS", "ranks": [0]}:
        raise LegacyStackContractError("preflight one-rank MPI probe did not pass exactly")
    if two_rank != {"status": "PASS", "ranks": [0, 1]}:
        raise LegacyStackContractError("preflight two-rank MPI probe did not pass exactly")
    libmpi = mpi.get("mpi4py_libmpi")
    if not isinstance(libmpi, list) or not libmpi or not all(
        isinstance(path, str) and path.startswith(mpi_prefix + "/") for path in libmpi
    ):
        raise LegacyStackContractError("preflight mpi4py ABI escaped the frozen MPI prefix")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha1(path: Path) -> str:
    digest = hashlib.sha1()  # noqa: S324 - required upstream release identity
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json_atomic(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, sort_keys=True) + "\n"
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_json_once(path: Path, value: Mapping[str, Any]) -> None:
    if path.exists():
        raise LegacyStackContractError(f"refusing to overwrite immutable evidence: {path}")
    _write_json_atomic(path, value)


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LegacyStackContractError(f"cannot read {label} {path}: {exc}") from exc
    return _require_mapping(value, label)


def _run_logged(
    command: Sequence[str],
    *,
    log_path: Path,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    display = subprocess.list2cmdline([str(item) for item in command])
    print(f"[{_utc_now()}] start: {display}", flush=True)
    with log_path.open("a", encoding="utf-8", newline="\n") as log:
        log.write(f"\n[{_utc_now()}] COMMAND {display}\n")
        log.flush()
        try:
            process = subprocess.Popen(
                [str(item) for item in command],
                cwd=str(cwd) if cwd is not None else None,
                env=dict(env) if env is not None else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as exc:
            raise LegacyStackExecutionError(f"cannot start {command[0]}: {exc}") from exc
        assert process.stdout is not None
        for line in process.stdout:
            log.write(line)
            log.flush()
            print(line, end="", flush=True)
        returncode = process.wait()
    if returncode != 0:
        raise LegacyStackExecutionError(
            f"command exited {returncode}; see {log_path}: {display}"
        )
    print(f"[{_utc_now()}] complete: {command[0]}", flush=True)


def _capture(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> str:
    try:
        result = subprocess.run(
            [str(item) for item in command],
            cwd=str(cwd) if cwd is not None else None,
            env=dict(env) if env is not None else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        stderr = getattr(exc, "stderr", "") or ""
        raise LegacyStackExecutionError(
            f"command failed: {subprocess.list2cmdline([str(item) for item in command])}; {stderr.strip()}"
        ) from exc
    return result.stdout


def _read_os_release() -> dict[str, str]:
    path = Path("/etc/os-release")
    if not path.is_file():
        raise LegacyStackExecutionError("/etc/os-release is missing; expected Ubuntu 20.04")
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"')
    return values


def _require_execution_host(spec: Mapping[str, Any]) -> dict[str, str]:
    if sys.platform != "linux":
        raise LegacyStackExecutionError("legacy stack execution is Linux-only")
    values = _read_os_release()
    if values.get("ID") != spec["os"]["id"] or values.get("VERSION_ID") != spec["os"]["version_id"]:
        raise LegacyStackExecutionError(
            f"expected Ubuntu 20.04, found {values.get('ID')} {values.get('VERSION_ID')}"
        )
    distro_name = os.environ.get("WSL_DISTRO_NAME")
    if distro_name != spec["wsl_distro_name"]:
        raise LegacyStackExecutionError(
            f"expected dedicated WSL distro {spec['wsl_distro_name']}, found {distro_name!r}"
        )
    if not hasattr(os, "geteuid") or os.geteuid() != 0:
        raise LegacyStackExecutionError("resolve/build must run as root inside the dedicated WSL distro")
    return values


def _stack_paths(spec: Mapping[str, Any]) -> dict[str, Path]:
    prefix = Path(str(spec["install_prefix"]))
    return {
        "prefix": prefix,
        "state": prefix / "state",
        "sources": prefix / "src",
        "downloads": prefix / "downloads",
        "petsc_downloads": prefix / "downloads" / "petsc",
        "mumps_archive": (
            prefix / str(spec["sources"]["mumps"]["retained_relative_path"])
        ),
        "python_cache": prefix / "downloads" / "python",
        "pybind_provider": prefix / "providers" / "pybind11-2.2.4",
        "venv": prefix / "py38",
        "mpi": prefix / "openmpi-3.1.6",
        "petsc": prefix / "src" / "petsc",
        "dolfin": prefix / "src" / "dolfin",
        "dolfin_install": prefix / "fenics" / "dolfin",
        "lock": prefix / "state" / "resolution.lock.json",
        "preflight": prefix / "state" / "preflight.json",
        "build_manifest": prefix / "state" / "build.manifest.json",
    }


def build_stack_environment(
    spec: Mapping[str, Any],
    *,
    inherited_environment: Mapping[str, str] | None = None,
    offline_build: bool = False,
) -> dict[str, str]:
    """Return the single-MPI build environment required by the frozen stack.

    All mutating stages run as root in the dedicated disposable WSL distro.
    OpenMPI otherwise refuses launcher use by PETSc's checks, so both of its
    explicit root acknowledgements are part of this environment contract.
    """

    validate_stack_spec(spec)
    paths = _stack_paths(spec)
    toolchain = spec["toolchain"]
    env = dict(os.environ if inherited_environment is None else inherited_environment)
    petsc_arch_root = paths["petsc"] / str(spec["petsc"]["arch"])
    posix = {key: path.as_posix() for key, path in paths.items()}
    petsc_arch_posix = petsc_arch_root.as_posix()
    for host_package_hint in ("HDF5_DIR", "HDF5_ROOT"):
        env.pop(host_package_hint, None)
    if offline_build:
        for untrusted_resolution_input in (
            "PIP_INDEX_URL",
            "PIP_EXTRA_INDEX_URL",
            "PIP_FIND_LINKS",
            "PIP_TRUSTED_HOST",
            "PYTHONPATH",
            "PYTHONHOME",
            "CMAKE_ARGS",
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "ALL_PROXY",
            "http_proxy",
            "https_proxy",
            "all_proxy",
        ):
            env.pop(untrusted_resolution_input, None)
    env.update(
        {
            "CC": str(toolchain["cc"]),
            "CXX": str(toolchain["cxx"]),
            "FC": str(toolchain["fc"]),
            "MPI_DIR": posix["mpi"],
            "PETSC_DIR": posix["petsc"],
            "PETSC_ARCH": str(spec["petsc"]["arch"]),
            "PATH": (
                f"{posix['venv']}/bin:{posix['mpi']}/bin:"
                "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
            ),
            "LD_LIBRARY_PATH": (
                f"{posix['dolfin_install']}/lib:{petsc_arch_posix}/lib:"
                f"{posix['mpi']}/lib"
            ),
            "PYTHONPATH": f"{petsc_arch_posix}/lib",
            "CMAKE_PREFIX_PATH": (
                f"{posix['pybind_provider']}:{posix['dolfin_install']}:"
                f"{petsc_arch_posix}:{posix['mpi']}"
            ),
            "PKG_CONFIG_PATH": f"{posix['dolfin_install']}/lib/pkgconfig",
            "pybind11_DIR": f"{posix['pybind_provider']}/share/cmake/pybind11",
            "DOLFIN_DIR": f"{posix['dolfin_install']}/share/dolfin/cmake",
            "MPICC": f"{posix['mpi']}/bin/mpicc",
            "OMPI_ALLOW_RUN_AS_ROOT": "1",
            "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
        }
    )
    if offline_build:
        env.update(
            {
                "PIP_NO_INDEX": "1",
                "PIP_NO_DEPS": "1",
                "PIP_DISABLE_PIP_VERSION_CHECK": "1",
                "PIP_CONFIG_FILE": "/dev/null",
                "PYTHONNOUSERSITE": "1",
            }
        )
    return env


def _download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.is_file() and destination.stat().st_size > 0:
            return
        raise LegacyStackExecutionError(f"download target exists but is not a usable file: {destination}")
    temporary = destination.with_name(f".{destination.name}.download")
    if temporary.exists():
        raise LegacyStackExecutionError(f"partial download requires an explicit new attempt: {temporary}")
    print(f"[{_utc_now()}] download: {url}", flush=True)
    try:
        with urllib.request.urlopen(url, timeout=120) as response, temporary.open("xb") as output:
            shutil.copyfileobj(response, output, length=1024 * 1024)
        os.replace(temporary, destination)
    except Exception as exc:
        raise LegacyStackExecutionError(f"download failed for {url}: {exc}") from exc


def _safe_extract_tar(archive: Path, destination: Path) -> None:
    expected_root = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, mode="r:gz") as handle:
        for member in handle.getmembers():
            candidate = (destination / member.name).resolve()
            if os.path.commonpath((str(expected_root), str(candidate))) != str(expected_root):
                raise LegacyStackExecutionError(f"archive member escapes destination: {member.name}")
            if member.ischr() or member.isblk() or member.isfifo():
                raise LegacyStackExecutionError(f"archive contains a special device: {member.name}")
            if member.issym() or member.islnk():
                link_target = (candidate.parent / member.linkname).resolve()
                if os.path.commonpath((str(expected_root), str(link_target))) != str(expected_root):
                    raise LegacyStackExecutionError(f"archive link escapes destination: {member.name}")
        handle.extractall(destination)


def _clone_tag(
    *,
    repository: str,
    ref: str,
    destination: Path,
    log_path: Path,
    expected_commit: str | None,
) -> dict[str, str]:
    if not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        _run_logged(
            ["git", "clone", "--depth", "1", "--branch", ref, repository, str(destination)],
            log_path=log_path,
        )
    if not (destination / ".git").is_dir():
        raise LegacyStackExecutionError(f"source destination is not a Git checkout: {destination}")
    remote = _capture(["git", "remote", "get-url", "origin"], cwd=destination).strip()
    identity = inspect_clean_source_checkout(destination)
    commit = identity["commit"]
    tags = set(_capture(["git", "tag", "--points-at", "HEAD"], cwd=destination).splitlines())
    if remote.rstrip("/") != repository.rstrip("/"):
        raise LegacyStackExecutionError(f"source remote drift at {destination}: {remote}")
    if ref not in tags:
        raise LegacyStackExecutionError(f"source checkout is not exactly tag {ref}: {destination}")
    if expected_commit is not None and commit != expected_commit:
        raise LegacyStackExecutionError(
            f"tag {ref} resolved to {commit}, expected {expected_commit}"
        )
    return {"repository": remote, "ref": ref, **identity}


def _dpkg_versions() -> dict[str, str]:
    output = _capture(["dpkg-query", "-W", "-f=${binary:Package}\t${Version}\n"])
    result: dict[str, str] = {}
    for line in output.splitlines():
        if "\t" in line:
            package, version = line.split("\t", 1)
            result[package] = version
    if not result:
        raise LegacyStackExecutionError("dpkg-query returned no installed packages")
    return dict(sorted(result.items()))


def _assert_forbidden_packages_absent(spec: Mapping[str, Any], packages: Mapping[str, str]) -> None:
    installed_names = {name.split(":", 1)[0] for name in packages}
    forbidden = sorted(installed_names.intersection(spec["system_packages"]["forbidden"]))
    if forbidden:
        raise LegacyStackExecutionError(
            f"forbidden alternate MPI/FEniCS packages are installed: {', '.join(forbidden)}"
        )


def _compiler_identities(spec: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    identities: dict[str, dict[str, str]] = {}
    for key in ("cc", "cxx", "fc", "python"):
        path = Path(str(spec["toolchain"][key]))
        if not path.is_file():
            raise LegacyStackExecutionError(f"required toolchain executable is missing: {path}")
        flag = "--version"
        first_line = _capture([str(path), flag]).splitlines()[0]
        identities[key] = {
            "path": str(path),
            "sha256": _sha256(path),
            "version_line": first_line,
        }
    for key in ("cc", "cxx", "fc"):
        if not re.search(r"\b9(?:\.|\b)", identities[key]["version_line"]):
            raise LegacyStackExecutionError(
                f"{key} is not GNU 9: {identities[key]['version_line']}"
            )
    python_version = _capture([str(spec["toolchain"]["python"]), "-c", "import sys; print('%d.%d' % sys.version_info[:2])"]).strip()
    if python_version != spec["toolchain"]["python_major_minor"]:
        raise LegacyStackExecutionError(f"expected Python 3.8, found {python_version}")
    return identities


def _inventory_files(root: Path) -> list[dict[str, Any]]:
    return [
        {
            "filename": path.name,
            "relative_path": path.relative_to(root).as_posix(),
            "size": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]


def _verify_known_python_artifacts(
    spec: Mapping[str, Any], artifacts: Sequence[Mapping[str, Any]]
) -> None:
    by_name = {str(item["filename"]): item for item in artifacts}
    for expected in spec["python_resolution"]["known_artifacts"]:
        actual = by_name.get(expected["filename"])
        if actual is None:
            raise LegacyStackExecutionError(
                f"pip resolution did not select known artifact {expected['filename']}"
            )
        if actual.get("sha256") != expected["sha256"]:
            raise LegacyStackExecutionError(
                f"known Python artifact hash mismatch: {expected['filename']}"
            )


def inspect_clean_source_checkout(path: Path) -> dict[str, str]:
    """Return immutable Git source identity, rejecting tracked checkout drift."""

    if not (path / ".git").is_dir():
        raise LegacyStackContractError(f"source checkout has no Git metadata: {path}")
    try:
        commit = _capture(["git", "rev-parse", "HEAD"], cwd=path).strip()
        tree = _capture(["git", "rev-parse", "HEAD^{tree}"], cwd=path).strip()
        tracked_status = _capture(
            ["git", "status", "--porcelain=v1", "--untracked-files=no"], cwd=path
        ).strip()
    except LegacyStackExecutionError as exc:
        raise LegacyStackContractError(f"cannot inspect source checkout {path}: {exc}") from exc
    if not _is_hex(commit, 40) or not _is_hex(tree, 40):
        raise LegacyStackContractError(f"source checkout has an invalid Git identity: {path}")
    if tracked_status:
        raise LegacyStackContractError(f"tracked worktree drift at {path}: {tracked_status}")

    command = ["git", "archive", "--format=tar", commit]
    digest = hashlib.sha256()
    try:
        process = subprocess.Popen(
            command,
            cwd=str(path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        raise LegacyStackContractError(f"cannot archive source checkout {path}: {exc}") from exc
    assert process.stdout is not None
    for chunk in iter(lambda: process.stdout.read(1024 * 1024), b""):
        digest.update(chunk)
    process.stdout.close()
    stderr = process.stderr.read() if process.stderr is not None else b""
    if process.stderr is not None:
        process.stderr.close()
    returncode = process.wait()
    if returncode != 0:
        detail = stderr.decode("utf-8", errors="replace").strip()
        raise LegacyStackContractError(
            f"cannot hash source checkout {path}: git archive exited {returncode}; {detail}"
        )
    return {
        "commit": commit,
        "tree": tree,
        "archive_format": "git-archive-tar",
        "archive_sha256": digest.hexdigest(),
    }


_EXTERNAL_ALIASES = {
    "fblaslapack": ("fblaslapack",),
    "metis": ("metis",),
    "parmetis": ("parmetis",),
    "ptscotch": ("scotch", "ptscotch"),
    "suitesparse": ("suitesparse", "suite-sparse"),
    "mumps": ("mumps",),
    "scalapack": ("scalapack",),
    "hypre": ("hypre",),
}


def _name_matches_external(text: str, name: str) -> bool:
    lowered = text.lower()
    if name == "metis" and "parmetis" in lowered:
        return False
    return any(alias in lowered for alias in _EXTERNAL_ALIASES[name])


def _hash_extracted_source_tree(path: Path) -> dict[str, Any]:
    """Hash a non-Git extracted source tree without volatile timestamps."""

    if not path.is_dir() or (path / ".git").exists():
        raise LegacyStackContractError(
            f"extracted PETSc external source is not a non-Git directory: {path}"
        )
    root = path.resolve()
    digest = hashlib.sha256()
    file_count = 0
    total_size = 0
    for entry in sorted(path.rglob("*"), key=lambda item: item.relative_to(path).as_posix()):
        relative_path = entry.relative_to(path).as_posix()
        metadata = entry.lstat()
        mode = metadata.st_mode & 0o777
        if entry.is_symlink():
            target = os.readlink(entry)
            resolved_target = (entry.parent / target).resolve()
            if os.path.commonpath((str(root), str(resolved_target))) != str(root):
                raise LegacyStackContractError(
                    f"extracted PETSc external symlink escapes its source tree: {entry}"
                )
            record = {
                "kind": "symlink",
                "mode": mode,
                "path": relative_path,
                "target": target,
            }
            file_count += 1
        elif entry.is_dir():
            record = {"kind": "directory", "mode": mode, "path": relative_path}
        elif entry.is_file():
            size = metadata.st_size
            record = {
                "content_sha256": _sha256(entry),
                "kind": "file",
                "mode": mode,
                "path": relative_path,
                "size": size,
            }
            file_count += 1
            total_size += size
        else:
            raise LegacyStackContractError(
                f"extracted PETSc external source contains a special file: {entry}"
            )
        digest.update(
            json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
        )
        digest.update(b"\n")
    if file_count == 0:
        raise LegacyStackContractError(
            f"extracted PETSc external source tree is empty: {path}"
        )
    return {
        "tree_hash_algorithm": "sha256-path-mode-content-v1",
        "tree_sha256": digest.hexdigest(),
        "file_count": file_count,
        "total_file_bytes": total_size,
    }


def lock_petsc_external_sources(
    spec: Mapping[str, Any],
    petsc_root: Path,
    configure_log: Path,
    *,
    retained_archives: Mapping[str, Path] | None = None,
) -> dict[str, Any]:
    """Lock each PETSc external from its checkout, archive, or extracted tree.

    PETSc reuses prior Git checkouts without repeating their download URLs in a
    later configure log.  The checkout origin and immutable Git identity are
    therefore the authoritative evidence for Git-backed externals; archive
    downloads continue to use the configure log plus the downloaded bytes.  A
    few PETSc packages consume and delete their archive; their remaining
    non-Git extracted tree is hashed with a path/mode/content manifest.
    """

    retained_archives = {} if retained_archives is None else retained_archives
    log_text = configure_log.read_text(encoding="utf-8", errors="replace")
    urls = sorted(
        set(
            match.rstrip(".,);]")
            for match in re.findall(r"(?:https?|ftp)://[^\s'\"<>]+", log_text)
        )
    )
    archive_suffixes = (".tar.gz", ".tgz", ".tar.bz2", ".tar.xz", ".zip")
    archives = [
        path
        for path in petsc_root.rglob("*")
        if path.is_file() and path.name.lower().endswith(archive_suffixes)
    ]
    git_checkouts = [
        metadata.parent
        for metadata in petsc_root.rglob(".git")
        if metadata.is_dir()
    ]
    external_root = petsc_root / str(spec["petsc"]["arch"]) / "externalpackages"
    extracted_trees = (
        [
            path
            for path in external_root.iterdir()
            if path.is_dir() and not (path / ".git").exists()
        ]
        if external_root.is_dir()
        else []
    )
    locked: dict[str, Any] = {}
    for name in spec["petsc"]["required_external_packages"]:
        if name in retained_archives:
            archive = retained_archives[name]
            source = _require_mapping(
                spec["sources"].get(name), f"sources.{name}"
            )
            if (
                not archive.is_file()
                or archive.stat().st_size <= 0
                or archive.name != source.get("filename")
            ):
                raise LegacyStackExecutionError(
                    f"retained PETSc external archive for {name} is missing or drifted"
                )
            locked[name] = {
                "source_kind": "retained-archive",
                "urls": [source["url"]],
                "filename": archive.name,
                "retained_path": archive.as_posix(),
                "sha256": _sha256(archive),
            }
            continue
        matching_urls = [url for url in urls if _name_matches_external(url, name)]
        matching_checkouts = [
            path for path in git_checkouts if _name_matches_external(path.name, name)
        ]
        if len(matching_checkouts) > 1:
            raise LegacyStackExecutionError(
                f"PETSc external source for {name} has multiple Git checkouts"
            )
        if matching_checkouts:
            checkout = matching_checkouts[0]
            identity = inspect_clean_source_checkout(checkout)
            origin = _capture(["git", "remote", "get-url", "origin"], cwd=checkout).strip()
            if not re.match(r"^(?:https?|ftp)://", origin):
                raise LegacyStackExecutionError(
                    f"PETSc external Git source for {name} has no supported origin URL"
                )
            locked[name] = {
                "source_kind": "git-checkout",
                "urls": [origin],
                "filename": checkout.name,
                "relative_path": checkout.relative_to(petsc_root).as_posix(),
                "sha256": identity["archive_sha256"],
                **identity,
            }
            continue
        basenames = {
            Path(urllib.parse.urlparse(url).path).name.lower() for url in matching_urls
        }
        matching_archives = [
            path
            for path in archives
            if path.name.lower() in basenames or _name_matches_external(path.name, name)
        ]
        unique_by_hash: dict[str, Path] = {}
        for path in matching_archives:
            unique_by_hash.setdefault(_sha256(path), path)
        if not matching_urls:
            raise LegacyStackExecutionError(
                f"PETSc configure log did not expose a resolved URL for {name}"
            )
        if not unique_by_hash:
            matching_trees = [
                path for path in extracted_trees if _name_matches_external(path.name, name)
            ]
            if len(matching_trees) != 1:
                raise LegacyStackExecutionError(
                    f"PETSc external source for {name} is not uniquely hashable: "
                    f"0 archives and {len(matching_trees)} extracted trees"
                )
            source_tree = matching_trees[0]
            identity = _hash_extracted_source_tree(source_tree)
            locked[name] = {
                "source_kind": "extracted-source-tree",
                "urls": matching_urls,
                "filename": source_tree.name,
                "relative_path": source_tree.relative_to(petsc_root).as_posix(),
                "sha256": identity["tree_sha256"],
                **identity,
            }
            continue
        if len(unique_by_hash) != 1:
            raise LegacyStackExecutionError(
                f"PETSc external source for {name} is not uniquely hashable: {len(unique_by_hash)} archives"
            )
        digest, archive = next(iter(unique_by_hash.items()))
        locked[name] = {
            "source_kind": "archive",
            "urls": matching_urls,
            "filename": archive.name,
            "relative_path": archive.relative_to(petsc_root).as_posix(),
            "sha256": digest,
        }
    return locked


def _find_petsc_configure_log(petsc_root: Path, arch: str) -> Path:
    preferred = petsc_root / arch / "lib" / "petsc" / "conf" / "configure.log"
    if preferred.is_file():
        return preferred
    candidates = [path for path in petsc_root.rglob("configure.log") if path.is_file()]
    if len(candidates) != 1:
        raise LegacyStackExecutionError(
            f"PETSc configure log is not unique: {[str(path) for path in candidates]}"
        )
    return candidates[0]


def _find_petsc_reconfigure_script(petsc_root: Path, arch: str) -> Path:
    conf_root = petsc_root / arch / "lib" / "petsc" / "conf"
    candidates = [
        path
        for path in conf_root.glob("reconfigure*.py")
        if path.is_file()
    ]
    if len(candidates) != 1:
        raise LegacyStackExecutionError(
            f"PETSc reconfigure script is not unique: {[str(path) for path in candidates]}"
        )
    return candidates[0]


def parse_petsc_configuration(header_path: Path) -> dict[str, Any]:
    """Parse the resolved scalar, precision, index and debug modes from PETSc."""

    if not header_path.is_file():
        raise LegacyStackContractError(f"PETSc generated configuration header is missing: {header_path}")
    try:
        header_bytes = header_path.read_bytes()
        text = header_bytes.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise LegacyStackContractError(
            f"cannot read PETSc generated configuration header {header_path}: {exc}"
        ) from exc
    defines = {
        match.group(1)
        for line in text.splitlines()
        if (match := re.match(r"^\s*#\s*define\s+(PETSC_[A-Z0-9_]+)(?:\s+.*)?$", line))
    }
    precision_macros = {
        "PETSC_USE_REAL_SINGLE": "single",
        "PETSC_USE_REAL_DOUBLE": "double",
        "PETSC_USE_REAL___FLOAT128": "__float128",
        "PETSC_USE_REAL___FP16": "__fp16",
    }
    selected_precisions = [
        precision for macro, precision in precision_macros.items() if macro in defines
    ]
    if len(selected_precisions) != 1:
        raise LegacyStackContractError(
            "PETSc generated configuration does not identify exactly one precision"
        )
    return {
        "evidence_source": "petscconf.h",
        "petscconf_sha256": hashlib.sha256(header_bytes).hexdigest(),
        "scalar_type": "complex" if "PETSC_USE_COMPLEX" in defines else "real",
        "precision": selected_precisions[0],
        "index_size_bits": 64 if "PETSC_USE_64BIT_INDICES" in defines else 32,
        "debugging": "PETSC_USE_DEBUG" in defines,
    }


def validate_petsc_check_log(log_path: Path) -> dict[str, Any]:
    """Reject PETSc's documented exit-zero false-green records."""

    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        raise LegacyStackExecutionError(f"cannot read PETSc check log {log_path}: {exc}") from exc
    forbidden_patterns = (
        re.compile(r"^\s*Possible (?:error|problem)\b", re.IGNORECASE),
        re.compile(
            r"^\s*(?:mpiexec|mpirun|orterun) has detected an attempt to run as root\.\s*$",
            re.IGNORECASE,
        ),
    )
    forbidden = [
        line.strip()
        for line in lines
        if any(pattern.search(line) for pattern in forbidden_patterns)
    ]
    if forbidden:
        raise LegacyStackExecutionError(
            "PETSc check log contains forbidden false-green records: "
            + " | ".join(forbidden)
        )
    return {"status": "PASS", "forbidden_records": []}


def _resolve_stage(
    spec: Mapping[str, Any], *, spec_path: Path, evidence_root: Path
) -> dict[str, Any]:
    os_release = _require_execution_host(spec)
    paths = _stack_paths(spec)
    evidence_root.mkdir(parents=True, exist_ok=True)
    for key in (
        "prefix",
        "state",
        "sources",
        "downloads",
        "petsc_downloads",
        "python_cache",
    ):
        paths[key].mkdir(parents=True, exist_ok=True)
    spec_sha256 = _sha256(spec_path)
    evidence_lock = evidence_root / "resolution.lock.json"
    if paths["lock"].exists():
        lock = _load_json_object(paths["lock"], "resolution lock")
        validate_resolution_lock(spec, lock, expected_spec_sha256=spec_sha256)
        if evidence_lock.exists() and _sha256(evidence_lock) != _sha256(paths["lock"]):
            raise LegacyStackContractError("state and evidence resolution locks differ")
        if not evidence_lock.exists():
            shutil.copyfile(paths["lock"], evidence_lock)
        return lock

    log_root = evidence_root / "logs"
    _run_logged(["apt-get", "update"], log_path=log_root / "apt.log")
    _run_logged(
        ["apt-get", "install", "-y", "--no-install-recommends", *spec["system_packages"]["install"]],
        log_path=log_root / "apt.log",
    )
    apt_packages = _dpkg_versions()
    _assert_forbidden_packages_absent(spec, apt_packages)
    compiler_identities = _compiler_identities(spec)

    openmpi_spec = spec["sources"]["openmpi"]
    openmpi_archive = paths["downloads"] / openmpi_spec["filename"]
    _download(openmpi_spec["url"], openmpi_archive)
    if _sha1(openmpi_archive) != openmpi_spec["sha1"]:
        raise LegacyStackExecutionError("OpenMPI official SHA1 mismatch")
    openmpi_source = paths["sources"] / f"openmpi-{openmpi_spec['version']}"
    if not openmpi_source.is_dir():
        _safe_extract_tar(openmpi_archive, paths["sources"])
    if not (openmpi_source / "configure").is_file():
        raise LegacyStackExecutionError("OpenMPI release archive has an unexpected layout")
    env = build_stack_environment(spec)
    mpi_bin = paths["mpi"] / "bin"
    mpi_presence = {
        name: (mpi_bin / name).is_file() for name in MPI_EXECUTABLES
    }
    if any(mpi_presence.values()) and not all(mpi_presence.values()):
        missing = sorted(name for name, present in mpi_presence.items() if not present)
        raise LegacyStackExecutionError(
            f"partial OpenMPI installation is not a valid resolution state: {missing}"
        )
    if not all(mpi_presence.values()):
        _run_logged(
            [
                str(openmpi_source / "configure"),
                f"--prefix={paths['mpi']}",
            ],
            cwd=openmpi_source,
            env=env,
            log_path=log_root / "openmpi-configure.log",
        )
        _run_logged(
            ["make", f"-j{spec['build_jobs']}", "all"],
            cwd=openmpi_source,
            env=env,
            log_path=log_root / "openmpi-build.log",
        )
        _run_logged(
            ["make", "install"],
            cwd=openmpi_source,
            env=env,
            log_path=log_root / "openmpi-build.log",
        )
    _collect_mpi_wrapper_evidence(
        spec,
        mpi_bin=mpi_bin,
        env=env,
    )
    ompi_version = _capture([str(paths["mpi"] / "bin" / "ompi_info"), "--version"], env=env)
    if "3.1.6" not in ompi_version:
        raise LegacyStackExecutionError(f"built OpenMPI is not 3.1.6: {ompi_version.splitlines()[:1]}")

    python_executable = paths["venv"] / "bin" / "python"
    if not python_executable.is_file():
        _run_logged(
            [str(spec["toolchain"]["python"]), "-m", "venv", str(paths["venv"])],
            log_path=log_root / "python-resolution.log",
            env=env,
        )
    requirements_in = paths["state"] / "python-requirements.in"
    expected_requirements_text = "\n".join(spec["python_resolution"]["requirements"]) + "\n"
    if requirements_in.exists() and requirements_in.read_text(encoding="utf-8") != expected_requirements_text:
        raise LegacyStackExecutionError("Python resolution input drifted within the same prefix")
    requirements_in.write_text(expected_requirements_text, encoding="utf-8")
    resolve_plan = next(stage for stage in build_execution_plan(spec) if stage["id"] == "resolve")
    pybind_plan = resolve_plan["pybind11_provider"]
    pybind_archive = Path(str(pybind_plan["source"]["path"]))
    _download(str(pybind_plan["source"]["url"]), pybind_archive)
    if _sha256(pybind_archive) != pybind_plan["source"]["sha256"]:
        raise LegacyStackExecutionError("pybind11 2.2.4 source artifact SHA256 mismatch")
    _run_logged(
        [
            str(python_executable),
            "-m",
            "pip",
            "download",
            "--dest",
            str(paths["python_cache"]),
            "--find-links",
            str(paths["python_cache"]),
            "--no-binary=mpi4py,pybind11",
            "--requirement",
            str(requirements_in),
        ],
        log_path=log_root / "python-resolution.log",
        env=env,
    )
    python_artifacts = _inventory_files(paths["python_cache"])
    _verify_known_python_artifacts(spec, python_artifacts)
    _run_logged(
        [
            str(python_executable),
            "-m",
            "pip",
            "install",
            "--no-index",
            "--find-links",
            str(paths["python_cache"]),
            "--no-binary=mpi4py,pybind11",
            "--requirement",
            str(requirements_in),
        ],
        log_path=log_root / "python-install.log",
        env=env,
    )

    pybind_source = paths["sources"] / str(pybind_plan["source"]["archive_root"])
    if not pybind_source.is_dir():
        _safe_extract_tar(pybind_archive, paths["sources"])
    if not (pybind_source / "CMakeLists.txt").is_file():
        raise LegacyStackExecutionError("pybind11 source artifact has an unexpected layout")
    pybind_config = Path(str(pybind_plan["cmake_config_path"]))
    if not pybind_config.is_file():
        _run_logged(
            pybind_plan["configure_command"],
            env=env,
            log_path=log_root / "pybind11-provider.log",
        )
        _run_logged(
            pybind_plan["install_command"],
            env=env,
            log_path=log_root / "pybind11-provider.log",
        )
    if not pybind_config.is_file():
        raise LegacyStackExecutionError(
            f"pybind11 CMake provider did not install {pybind_config}"
        )
    pybind_provider = {
        "version": spec["sources"]["pybind11_cmake_provider"]["version"],
        "source_filename": pybind_archive.name,
        "source_sha256": _sha256(pybind_archive),
        "source_repository": pybind_plan["source"]["repository"],
        "source_tag": pybind_plan["source"]["tag"],
        "source_tag_object": pybind_plan["source"]["tag_object"],
        "source_commit": pybind_plan["source"]["commit"],
        "source_archive_root": pybind_plan["source"]["archive_root"],
        "install_prefix": str(paths["pybind_provider"]),
        "cmake_config_path": str(pybind_config),
        "cmake_config_sha256": _sha256(pybind_config),
    }

    petsc_identity = _clone_tag(
        repository=spec["sources"]["petsc"]["repository"],
        ref=spec["sources"]["petsc"]["ref"],
        destination=paths["petsc"],
        log_path=log_root / "source-resolution.log",
        expected_commit=spec["sources"]["petsc"]["commit"],
    )
    dolfin_identity = _clone_tag(
        repository=spec["sources"]["dolfin"]["repository"],
        ref=spec["sources"]["dolfin"]["ref"],
        destination=paths["dolfin"],
        log_path=log_root / "source-resolution.log",
        expected_commit=None,
    )
    mumps_source = spec["sources"]["mumps"]
    _download(mumps_source["url"], paths["mumps_archive"])
    mumps_sha256_before_configure = _sha256(paths["mumps_archive"])
    petsc_configure = [
        str(python_executable),
        str(paths["petsc"] / "configure"),
        f"--with-mpi-dir={paths['mpi']}",
        *spec["petsc"]["configure_options"],
    ]
    petsc_env = dict(env)
    for compiler_variable in ("CC", "CXX", "FC"):
        petsc_env.pop(compiler_variable, None)
    _run_logged(
        petsc_configure,
        cwd=paths["petsc"],
        env=petsc_env,
        log_path=log_root / "petsc-configure-console.log",
    )
    configure_log = _find_petsc_configure_log(paths["petsc"], spec["petsc"]["arch"])
    reconfigure_script = _find_petsc_reconfigure_script(
        paths["petsc"], spec["petsc"]["arch"]
    )
    petscconf_header = (
        paths["petsc"] / str(spec["petsc"]["arch"]) / "include" / "petscconf.h"
    )
    petsc_configuration = parse_petsc_configuration(petscconf_header)
    if _sha256(paths["mumps_archive"]) != mumps_sha256_before_configure:
        raise LegacyStackExecutionError(
            "retained MUMPS archive changed while PETSc consumed it"
        )
    external_packages = lock_petsc_external_sources(
        spec,
        paths["petsc"],
        configure_log,
        retained_archives={"mumps": paths["mumps_archive"]},
    )
    shutil.copyfile(configure_log, evidence_root / "petsc-configure.log")
    shutil.copyfile(reconfigure_script, evidence_root / "petsc-reconfigure.py")
    shutil.copyfile(petscconf_header, evidence_root / "petscconf.h")
    python_freeze = sorted(
        line.strip()
        for line in _capture([str(python_executable), "-m", "pip", "freeze", "--all"], env=env).splitlines()
        if line.strip()
    )
    lock = {
        "schema_version": LOCK_SCHEMA,
        "status": "RESOLVED",
        "evidence_identity": "ENGINEERING_ENVIRONMENT_RESOLUTION_ONLY",
        "scientific_claim_status": "NO_SCIENTIFIC_CLAIMS",
        "g2_gate_outcome": "NOT_EVALUATED",
        "environment_id": spec["environment_id"],
        "created_at": _utc_now(),
        "spec_sha256": spec_sha256,
        "install_prefix": str(paths["prefix"]),
        "mpi_prefix": str(paths["mpi"]),
        "os_release": os_release,
        "apt_packages": apt_packages,
        "compiler_identities": compiler_identities,
        "python_freeze": python_freeze,
        "python_artifacts": python_artifacts,
        "pybind11_provider": pybind_provider,
        "sources": {
            "openmpi": {
                "version": openmpi_spec["version"],
                "url": openmpi_spec["url"],
                "sha1": _sha1(openmpi_archive),
                "sha256": _sha256(openmpi_archive),
            },
            "petsc": petsc_identity,
            "dolfin": dolfin_identity,
        },
        "petsc_arch": spec["petsc"]["arch"],
        "petsc_configure_command": petsc_configure,
        "petsc_configure_log_sha256": _sha256(configure_log),
        "petsc_reconfigure_script_sha256": _sha256(reconfigure_script),
        "petsc_configuration": petsc_configuration,
        "petsc_external_packages": external_packages,
    }
    validate_resolution_lock(spec, lock, expected_spec_sha256=spec_sha256)
    _write_json_once(paths["lock"], lock)
    try:
        paths["lock"].chmod(0o444)
    except OSError:
        pass
    _write_json_once(evidence_lock, lock)
    return lock


def validate_python_resolution_transition(
    resolution_freeze: Sequence[str],
    current_freeze: Sequence[str],
    *,
    allowed_build_additions: Sequence[str] = (),
) -> None:
    expected = sorted([*resolution_freeze, *allowed_build_additions])
    if sorted(current_freeze) != expected:
        raise LegacyStackExecutionError(
            "Python environment drifted after first resolution"
        )


def _assert_resolution_state(
    spec: Mapping[str, Any],
    paths: Mapping[str, Path],
    lock: Mapping[str, Any],
    *,
    allowed_python_build_additions: Sequence[str] = (),
) -> None:
    packages = _dpkg_versions()
    _assert_forbidden_packages_absent(spec, packages)
    for name, version in lock["apt_packages"].items():
        if packages.get(name) != version:
            raise LegacyStackExecutionError(f"apt package drift: {name}")
    for source_name, path_key in (("petsc", "petsc"), ("dolfin", "dolfin")):
        identity = inspect_clean_source_checkout(paths[path_key])
        expected = lock["sources"][source_name]
        if any(identity[key] != expected.get(key) for key in identity):
            raise LegacyStackExecutionError(f"{source_name} source drifted after resolution")
    petscconf_header = (
        paths["petsc"] / str(spec["petsc"]["arch"]) / "include" / "petscconf.h"
    )
    if parse_petsc_configuration(petscconf_header) != lock["petsc_configuration"]:
        raise LegacyStackExecutionError("PETSc resolved configuration drifted after resolution")
    archive = paths["downloads"] / spec["sources"]["openmpi"]["filename"]
    if _sha256(archive) != lock["sources"]["openmpi"]["sha256"]:
        raise LegacyStackExecutionError("OpenMPI archive drifted after resolution")
    if (
        not paths["mumps_archive"].is_file()
        or _sha256(paths["mumps_archive"])
        != lock["petsc_external_packages"]["mumps"]["sha256"]
    ):
        raise LegacyStackExecutionError("retained MUMPS archive drifted after resolution")
    env = build_stack_environment(spec)
    python_freeze = sorted(
        line.strip()
        for line in _capture([str(paths["venv"] / "bin" / "python"), "-m", "pip", "freeze", "--all"], env=env).splitlines()
        if line.strip()
    )
    validate_python_resolution_transition(
        lock["python_freeze"],
        python_freeze,
        allowed_build_additions=allowed_python_build_additions,
    )
    locked_artifacts = {
        str(item["filename"]): str(item["sha256"])
        for item in lock["python_artifacts"]
    }
    current_artifacts = {
        str(item["filename"]): str(item["sha256"])
        for item in _inventory_files(paths["python_cache"])
    }
    if current_artifacts != locked_artifacts:
        raise LegacyStackExecutionError("Python artifact cache drifted after first resolution")
    provider = lock["pybind11_provider"]
    provider_plan = next(
        stage for stage in build_execution_plan(spec) if stage["id"] == "resolve"
    )["pybind11_provider"]
    provider_archive = Path(str(provider_plan["source"]["path"]))
    provider_config = Path(str(provider["cmake_config_path"]))
    if (
        not provider_archive.is_file()
        or _sha256(provider_archive) != provider["source_sha256"]
        or not provider_config.is_file()
        or _sha256(provider_config) != provider["cmake_config_sha256"]
    ):
        raise LegacyStackExecutionError("pybind11 CMake provider drifted after resolution")
    validate_dolfin_python_contract(spec, paths["dolfin"] / "python" / "setup.py")


def _assert_clean_build_prefix(spec: Mapping[str, Any], paths: Mapping[str, Path]) -> None:
    """Reject remnants that would make the single integration build non-clean."""

    forbidden_paths = [
        paths["build_manifest"],
        paths["dolfin"] / "build",
        paths["dolfin_install"],
    ]
    present = [str(path) for path in forbidden_paths if path.exists()]
    petsc_arch_lib = paths["petsc"] / str(spec["petsc"]["arch"]) / "lib"
    present.extend(str(path) for path in petsc_arch_lib.glob("libpetsc.*"))
    if present:
        raise LegacyStackExecutionError(
            "clean G2 final prefix contains prior build outputs: " + ", ".join(present)
        )
    env = build_stack_environment(spec, offline_build=True)
    python_freeze = _capture(
        [str(paths["venv"] / "bin" / "python"), "-m", "pip", "freeze", "--all"],
        env=env,
    )
    if any(line.lower().startswith("fenics-dolfin==") for line in python_freeze.splitlines()):
        raise LegacyStackExecutionError(
            "clean G2 final prefix already contains a DOLFIN Python binding"
        )


def classify_cpp_build_state(
    *,
    petsc_library_dir: Path,
    dolfin_build_dir: Path,
    dolfin_install_dir: Path,
    build_manifest: Path,
) -> str:
    """Classify the only safe partial-build resume point."""

    if build_manifest.is_file():
        return "COMPLETE"
    markers = {
        "petsc_library": any(
            path.is_file() for path in petsc_library_dir.glob("libpetsc.so*")
        ),
        "dolfin_cache": (dolfin_build_dir / "CMakeCache.txt").is_file(),
        "dolfin_library": (
            dolfin_install_dir / "lib" / "libdolfin.so"
        ).is_file(),
    }
    if all(markers.values()):
        return "CPP_COMPLETE_PYTHON_PENDING"
    if not any(markers.values()):
        return "CLEAN"
    present = sorted(name for name, found in markers.items() if found)
    missing = sorted(name for name, found in markers.items() if not found)
    raise LegacyStackContractError(
        "incomplete partial environment build; "
        f"present={present}, missing={missing}"
    )


def _build_stage(
    spec: Mapping[str, Any], *, spec_path: Path, evidence_root: Path
) -> dict[str, Any]:
    _require_execution_host(spec)
    paths = _stack_paths(spec)
    spec_sha256 = _sha256(spec_path)
    if not paths["lock"].is_file():
        raise LegacyStackContractError("build requires resolution.lock.json")
    lock = _load_json_object(paths["lock"], "resolution lock")
    validate_resolution_lock(spec, lock, expected_spec_sha256=spec_sha256)
    if not paths["preflight"].is_file():
        raise LegacyStackContractError("build requires a completed preflight.json")
    preflight = _load_json_object(paths["preflight"], "preflight report")
    validate_preflight_report(
        spec,
        preflight,
        expected_spec_sha256=spec_sha256,
        expected_resolution_lock_sha256=_sha256(paths["lock"]),
    )
    evidence_lock = evidence_root / "resolution.lock.json"
    if not evidence_lock.is_file() or _sha256(evidence_lock) != _sha256(paths["lock"]):
        raise LegacyStackContractError("build evidence root must contain the identical resolution lock")
    evidence_preflight = evidence_root / "preflight.json"
    if (
        not evidence_preflight.is_file()
        or _sha256(evidence_preflight) != _sha256(paths["preflight"])
    ):
        raise LegacyStackContractError(
            "build evidence root must contain the identical preflight report"
        )
    if paths["build_manifest"].is_file():
        manifest = _load_json_object(paths["build_manifest"], "build manifest")
        if (
            manifest.get("schema_version") != BUILD_SCHEMA
            or manifest.get("status") != "BUILT_NOT_YET_VERIFIED"
            or manifest.get("spec_sha256") != spec_sha256
            or manifest.get("resolution_lock_sha256") != _sha256(paths["lock"])
            or manifest.get("preflight_sha256") != _sha256(paths["preflight"])
        ):
            raise LegacyStackContractError("existing build manifest binds a different resolution lock")
        evidence_build = evidence_root / "build.manifest.json"
        if evidence_build.exists() and _sha256(evidence_build) != _sha256(paths["build_manifest"]):
            raise LegacyStackContractError("state and evidence build manifests differ")
        if not evidence_build.exists():
            shutil.copyfile(paths["build_manifest"], evidence_build)
        return manifest
    dolfin_build = paths["dolfin"] / "build"
    cpp_build_state = classify_cpp_build_state(
        petsc_library_dir=paths["petsc"] / str(spec["petsc"]["arch"]) / "lib",
        dolfin_build_dir=dolfin_build,
        dolfin_install_dir=paths["dolfin_install"],
        build_manifest=paths["build_manifest"],
    )
    allowed_python_build_additions: list[str] = []
    if cpp_build_state == "CPP_COMPLETE_PYTHON_PENDING":
        allowed_python_build_additions.append(
            f"petsc4py=={spec['sources']['petsc']['version']}"
        )
    _assert_resolution_state(
        spec,
        paths,
        lock,
        allowed_python_build_additions=allowed_python_build_additions,
    )
    if cpp_build_state == "CLEAN":
        _assert_clean_build_prefix(spec, paths)
    env = build_stack_environment(spec, offline_build=True)
    log_root = evidence_root / "logs"
    build_plan = next(stage for stage in build_execution_plan(spec) if stage["id"] == "build")
    make_variables = [f"PETSC_DIR={paths['petsc']}", f"PETSC_ARCH={spec['petsc']['arch']}"]
    if cpp_build_state == "CLEAN":
        _run_logged(
            ["make", f"-j{spec['build_jobs']}", *make_variables, "all"],
            cwd=paths["petsc"],
            env=env,
            log_path=log_root / "petsc-build.log",
        )
    _run_logged(
        build_plan["petsc_check_command"],
        cwd=paths["petsc"],
        env=env,
        log_path=log_root / "petsc-check.log",
    )
    petsc_check_evidence = validate_petsc_check_log(log_root / "petsc-check.log")
    if cpp_build_state == "CLEAN":
        _run_logged(
            ["cmake", "-S", str(paths["dolfin"]), "-B", str(dolfin_build), *spec["dolfin"]["cmake_options"]],
            env=env,
            log_path=log_root / "dolfin-configure.log",
        )
        _run_logged(
            ["cmake", "--build", str(dolfin_build), "--parallel", str(spec["build_jobs"])],
            env=env,
            log_path=log_root / "dolfin-build.log",
        )
        _run_logged(
            ["cmake", "--install", str(dolfin_build)],
            env=env,
            log_path=log_root / "dolfin-install.log",
        )
    python_executable = paths["venv"] / "bin" / "python"
    _run_logged(
        build_plan["dolfin_python_install_command"],
        env=env,
        log_path=log_root / "dolfin-python-install.log",
    )
    cache = dolfin_build / "CMakeCache.txt"
    if not cache.is_file():
        raise LegacyStackExecutionError("DOLFIN CMakeCache.txt is missing after build")
    shutil.copyfile(cache, evidence_root / "dolfin-CMakeCache.txt")
    final_freeze = sorted(
        line.strip()
        for line in _capture([str(python_executable), "-m", "pip", "freeze", "--all"], env=env).splitlines()
        if line.strip()
    )
    manifest = {
        "schema_version": BUILD_SCHEMA,
        "status": "BUILT_NOT_YET_VERIFIED",
        "evidence_identity": "ENGINEERING_ENVIRONMENT_BUILD_ONLY",
        "scientific_claim_status": "NO_SCIENTIFIC_CLAIMS",
        "g2_gate_outcome": "NOT_EVALUATED",
        "environment_id": spec["environment_id"],
        "completed_at": _utc_now(),
        "spec_sha256": spec_sha256,
        "resolution_lock_sha256": _sha256(paths["lock"]),
        "preflight_sha256": _sha256(paths["preflight"]),
        "petsc_arch": spec["petsc"]["arch"],
        "build_mode": cpp_build_state,
        "dolfin_python_parallelism": build_plan["dolfin_python_parallelism"],
        "dolfin_cmake_cache_sha256": _sha256(cache),
        "python_freeze": final_freeze,
        "petsc_check": petsc_check_evidence,
    }
    _write_json_once(paths["build_manifest"], manifest)
    try:
        paths["build_manifest"].chmod(0o444)
    except OSError:
        pass
    _write_json_once(evidence_root / "build.manifest.json", manifest)
    return manifest


def _ldd_paths(binary: Path, *, env: Mapping[str, str]) -> tuple[str, list[str]]:
    output = _capture(["ldd", str(binary)], env=env)
    paths: list[str] = []
    for line in output.splitlines():
        match = re.search(r"=>\s+(/[^\s]+)", line)
        if match:
            paths.append(str(Path(match.group(1)).resolve()))
    return output, paths


def _run_mpi_preflight_probe(
    *,
    ranks: int,
    mpi_bin: Path,
    python_executable: Path,
    env: Mapping[str, str],
    log_path: Path,
) -> dict[str, Any]:
    probe_code = (
        "import json; from mpi4py import MPI; "
        "MPI.COMM_WORLD.Barrier(); "
        "print(json.dumps({'rank': MPI.COMM_WORLD.rank, 'size': MPI.COMM_WORLD.size}, sort_keys=True))"
    )
    command = [
        str(mpi_bin / "mpiexec"),
        "--allow-run-as-root",
        "-np",
        str(ranks),
        str(python_executable),
        "-c",
        probe_code,
    ]
    output = _capture(command, env=env)
    if log_path.exists():
        raise LegacyStackContractError(f"refusing to overwrite MPI preflight evidence: {log_path}")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        f"COMMAND {subprocess.list2cmdline(command)}\n{output}",
        encoding="utf-8",
    )
    records: list[dict[str, Any]] = []
    for line in output.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and {"rank", "size"}.issubset(value):
            records.append(value)
    observed_ranks = sorted(
        int(item["rank"]) for item in records if int(item["size"]) == ranks
    )
    if observed_ranks != list(range(ranks)):
        raise LegacyStackExecutionError(
            f"{ranks}-rank MPI preflight probe returned ranks {observed_ranks}"
        )
    return {"status": "PASS", "ranks": observed_ranks}


def _collect_mpi_wrapper_evidence(
    spec: Mapping[str, Any],
    *,
    mpi_bin: Path,
    env: Mapping[str, str],
) -> dict[str, dict[str, str]]:
    """Prove every launcher/compiler wrapper used downstream is frozen."""

    executables: dict[str, str] = {}
    for name in MPI_EXECUTABLES:
        expected = mpi_bin / name
        resolved = shutil.which(name, path=env["PATH"])
        if not expected.is_file() or resolved != str(expected):
            raise LegacyStackExecutionError(
                f"MPI executable {name} is missing or escaped the frozen prefix"
            )
        executables[name] = resolved

    compiler_commands: dict[str, str] = {}
    for wrapper, toolchain_key in MPI_COMPILER_WRAPPERS.items():
        expected_compiler = str(spec["toolchain"][toolchain_key])
        raw_command = _capture(
            [str(mpi_bin / wrapper), "--showme:command"],
            env=env,
        ).strip()
        try:
            tokens = shlex.split(raw_command)
        except ValueError as exc:
            raise LegacyStackExecutionError(
                f"MPI compiler wrapper {wrapper} returned an invalid command"
            ) from exc
        if tokens != [expected_compiler]:
            raise LegacyStackExecutionError(
                f"MPI compiler wrapper {wrapper} does not bind {expected_compiler}: "
                f"{raw_command!r}"
            )
        compiler_commands[wrapper] = tokens[0]
    return {
        "executables": executables,
        "compiler_commands": compiler_commands,
    }


def _preflight_stage(
    spec: Mapping[str, Any], *, spec_path: Path, evidence_root: Path
) -> dict[str, Any]:
    _require_execution_host(spec)
    paths = _stack_paths(spec)
    spec_sha256 = _sha256(spec_path)
    if not paths["lock"].is_file():
        raise LegacyStackContractError("preflight requires resolution.lock.json")
    lock = _load_json_object(paths["lock"], "resolution lock")
    validate_resolution_lock(spec, lock, expected_spec_sha256=spec_sha256)
    evidence_lock = evidence_root / "resolution.lock.json"
    if not evidence_lock.is_file() or _sha256(evidence_lock) != _sha256(paths["lock"]):
        raise LegacyStackContractError(
            "preflight evidence root must contain the identical resolution lock"
        )
    evidence_preflight = evidence_root / "preflight.json"
    if paths["preflight"].is_file():
        report = _load_json_object(paths["preflight"], "preflight report")
        validate_preflight_report(
            spec,
            report,
            expected_spec_sha256=spec_sha256,
            expected_resolution_lock_sha256=_sha256(paths["lock"]),
        )
        if evidence_preflight.is_file() and _sha256(evidence_preflight) != _sha256(
            paths["preflight"]
        ):
            raise LegacyStackContractError(
                "state and evidence preflight reports differ"
            )
        if not evidence_preflight.is_file():
            shutil.copyfile(paths["preflight"], evidence_preflight)
        return report

    _assert_resolution_state(spec, paths, lock)
    _assert_clean_build_prefix(spec, paths)
    env = build_stack_environment(spec, offline_build=True)
    python_executable = paths["venv"] / "bin" / "python"
    mpi_bin = paths["mpi"] / "bin"
    mpi_wrapper_evidence = _collect_mpi_wrapper_evidence(
        spec,
        mpi_bin=mpi_bin,
        env=env,
    )
    ompi_version = _capture([str(mpi_bin / "ompi_info"), "--version"], env=env)
    if "3.1.6" not in ompi_version:
        raise LegacyStackExecutionError("preflight did not find OpenMPI 3.1.6")

    provider = lock["pybind11_provider"]
    provider_config = Path(str(provider["cmake_config_path"]))
    with tempfile.TemporaryDirectory(prefix="qpop-pybind-preflight-") as raw:
        cmake_probe = Path(raw)
        (cmake_probe / "CMakeLists.txt").write_text(
            "cmake_minimum_required(VERSION 3.1)\n"
            "project(qpop_pybind_preflight LANGUAGES CXX)\n"
            "find_package(pybind11 2.2.4 EXACT CONFIG REQUIRED)\n",
            encoding="utf-8",
        )
        _run_logged(
            [
                "cmake",
                "-S",
                str(cmake_probe),
                "-B",
                str(cmake_probe / "build"),
                f"-Dpybind11_DIR={provider_config.parent}",
            ],
            env=env,
            log_path=evidence_root / "logs" / "pybind11-find-package.log",
        )

    mpi_extension_text = _capture(
        [
            str(python_executable),
            "-c",
            "from mpi4py import MPI; print(MPI.__file__)",
        ],
        env=env,
    ).strip()
    mpi_extension = Path(mpi_extension_text)
    if not mpi_extension.is_file():
        raise LegacyStackExecutionError(
            f"preflight mpi4py extension is missing: {mpi_extension}"
        )
    ldd_output, libraries = _ldd_paths(mpi_extension, env=env)
    (evidence_root / "ldd-mpi4py-preflight.txt").write_text(
        ldd_output,
        encoding="utf-8",
    )
    libmpi = sorted(
        path for path in libraries if re.search(r"/libmpi(?:_[^/]*)?\.so", path)
    )
    mpi_prefix_real = str(paths["mpi"].resolve()) + os.sep
    if not libmpi or any(not path.startswith(mpi_prefix_real) for path in libmpi):
        raise LegacyStackExecutionError(
            f"preflight mpi4py ABI escaped the frozen prefix: {libmpi}"
        )

    probes = {
        str(ranks): _run_mpi_preflight_probe(
            ranks=ranks,
            mpi_bin=mpi_bin,
            python_executable=python_executable,
            env=env,
            log_path=evidence_root / "logs" / f"mpi-{ranks}-rank-preflight.log",
        )
        for ranks in (1, 2)
    }
    report = {
        "schema_version": PREFLIGHT_SCHEMA,
        "status": "PREFLIGHT_PASS",
        "evidence_identity": "ENGINEERING_BUILD_ADMISSION_ONLY",
        "scientific_claim_status": "NO_SCIENTIFIC_CLAIMS",
        "g2_gate_outcome": "NOT_EVALUATED",
        "checked_at": _utc_now(),
        "environment_id": spec["environment_id"],
        "spec_sha256": spec_sha256,
        "resolution_lock_sha256": _sha256(paths["lock"]),
        "resolution_state_revalidated": True,
        "clean_prefix": True,
        "dolfin_pybind11_requirement": validate_dolfin_python_contract(
            spec, paths["dolfin"] / "python" / "setup.py"
        ),
        "pybind11_provider": {
            "version": provider["version"],
            "source_sha256": provider["source_sha256"],
            "source_commit": provider["source_commit"],
            "cmake_config_path": provider["cmake_config_path"],
            "cmake_config_sha256": provider["cmake_config_sha256"],
            "cmake_find_package": "PASS",
        },
        "offline_build": {
            "pip_no_index": env.get("PIP_NO_INDEX") == "1",
            "pip_no_deps": env.get("PIP_NO_DEPS") == "1",
            "pip_no_build_isolation": True,
            "environment_sanitized": all(
                key not in env
                for key in (
                    "PIP_INDEX_URL",
                    "PIP_EXTRA_INDEX_URL",
                    "PIP_FIND_LINKS",
                    "PYTHONHOME",
                    "CMAKE_ARGS",
                )
            )
            and env.get("PYTHONPATH")
            == f"{paths['petsc']}/{spec['petsc']['arch']}/lib",
        },
        "mpi": {
            "version": ompi_version.splitlines()[0],
            "wrapper_prefix": str(paths["mpi"]),
            **mpi_wrapper_evidence,
            "probes": probes,
            "mpi4py_libmpi": libmpi,
        },
    }
    validate_preflight_report(
        spec,
        report,
        expected_spec_sha256=spec_sha256,
        expected_resolution_lock_sha256=_sha256(paths["lock"]),
    )
    _write_json_once(paths["preflight"], report)
    try:
        paths["preflight"].chmod(0o444)
    except OSError:
        pass
    _write_json_once(evidence_preflight, report)
    return report


def _verify_stage(
    spec: Mapping[str, Any], *, spec_path: Path, evidence_root: Path
) -> dict[str, Any]:
    os_release = _require_execution_host(spec)
    paths = _stack_paths(spec)
    spec_sha256 = _sha256(spec_path)
    lock = _load_json_object(paths["lock"], "resolution lock")
    validate_resolution_lock(spec, lock, expected_spec_sha256=spec_sha256)
    if not paths["preflight"].is_file():
        raise LegacyStackContractError("verify requires the build preflight report")
    preflight = _load_json_object(paths["preflight"], "preflight report")
    validate_preflight_report(
        spec,
        preflight,
        expected_spec_sha256=spec_sha256,
        expected_resolution_lock_sha256=_sha256(paths["lock"]),
    )
    manifest = _load_json_object(paths["build_manifest"], "build manifest")
    if (
        manifest.get("schema_version") != BUILD_SCHEMA
        or manifest.get("status") != "BUILT_NOT_YET_VERIFIED"
        or manifest.get("spec_sha256") != spec_sha256
        or manifest.get("resolution_lock_sha256") != _sha256(paths["lock"])
        or manifest.get("preflight_sha256") != _sha256(paths["preflight"])
    ):
        raise LegacyStackContractError("build manifest does not bind the active resolution lock")
    evidence_lock = evidence_root / "resolution.lock.json"
    evidence_preflight = evidence_root / "preflight.json"
    evidence_build = evidence_root / "build.manifest.json"
    if (
        not evidence_lock.is_file()
        or _sha256(evidence_lock) != _sha256(paths["lock"])
        or not evidence_preflight.is_file()
        or _sha256(evidence_preflight) != _sha256(paths["preflight"])
        or not evidence_build.is_file()
        or _sha256(evidence_build) != _sha256(paths["build_manifest"])
    ):
        raise LegacyStackContractError(
            "verify evidence root must contain the identical resolution, preflight and build records"
        )
    env = build_stack_environment(spec)
    python_executable = paths["venv"] / "bin" / "python"
    mpi_bin = paths["mpi"] / "bin"
    _collect_mpi_wrapper_evidence(spec, mpi_bin=mpi_bin, env=env)
    ompi_version = _capture([str(mpi_bin / "ompi_info"), "--version"], env=env)
    if "3.1.6" not in ompi_version:
        raise LegacyStackExecutionError("ompi_info did not report OpenMPI 3.1.6")

    probe_code = (
        "import json, dolfin; import dolfin.cpp; "
        "from mpi4py import MPI; from petsc4py import PETSc; "
        "print(json.dumps({'mpi4py': MPI.__file__, 'petsc4py': PETSc.__file__, "
        "'dolfin_cpp': dolfin.cpp.__file__, 'petsc_version': list(PETSc.Sys.getVersion()), "
        "'dolfin_version': dolfin.__version__, 'mumps': bool(dolfin.has_lu_solver_method('mumps')), "
        "'petsc_external': {n: bool(PETSc.Sys.hasExternalPackage(n)) for n in "
        "['mumps','parmetis','ptscotch','scalapack','hypre']}}))"
    )
    probe = json.loads(_capture([str(python_executable), "-c", probe_code], env=env))
    if probe.get("petsc_version") != spec["verification"]["required_petsc_version"]:
        raise LegacyStackExecutionError(f"unexpected PETSc version: {probe.get('petsc_version')}")
    if not str(probe.get("dolfin_version", "")).startswith(spec["verification"]["required_dolfin_version_prefix"]):
        raise LegacyStackExecutionError(f"unexpected DOLFIN version: {probe.get('dolfin_version')}")
    if probe.get("mumps") is not True:
        raise LegacyStackExecutionError("DOLFIN does not expose the required MUMPS solver")
    missing_external = sorted(
        name for name, present in probe.get("petsc_external", {}).items() if not present
    )
    if missing_external:
        raise LegacyStackExecutionError(f"PETSc lacks required external packages: {missing_external}")

    cache = paths["dolfin"] / "build" / "CMakeCache.txt"
    cache_text = cache.read_text(encoding="utf-8", errors="replace")
    parmetis_lines = [
        line for line in cache_text.splitlines() if "parmetis" in line.lower()
    ]
    parmetis_enabled = any(
        re.search(
            r"PARMETIS_FOUND(?::[^=]+)?=(?:TRUE|ON|1)$",
            line,
            re.IGNORECASE,
        )
        or re.search(
            r"PARMETIS_LIBRAR(?:Y|IES)(?::[^=]+)?=.*(?:^|/)libparmetis(?:\.so|\.a)",
            line,
            re.IGNORECASE,
        )
        for line in parmetis_lines
    )
    if not parmetis_enabled:
        raise LegacyStackExecutionError(
            "DOLFIN CMake cache does not prove ParMETIS availability"
        )

    library_evidence: dict[str, Any] = {}
    mpi_libraries: set[str] = set()
    for label in ("mpi4py", "petsc4py", "dolfin_cpp"):
        binary = Path(str(probe[label]))
        if not binary.is_file():
            raise LegacyStackExecutionError(f"{label} extension path is missing: {binary}")
        output, libraries = _ldd_paths(binary, env=env)
        (evidence_root / f"ldd-{label}.txt").write_text(output, encoding="utf-8")
        libmpi = [path for path in libraries if re.search(r"/libmpi(?:_[^/]*)?\.so", path)]
        if not libmpi:
            raise LegacyStackExecutionError(f"{label} does not expose a linked libmpi")
        mpi_libraries.update(libmpi)
        library_evidence[label] = {"binary": str(binary), "libmpi": libmpi}
    mpi_prefix_real = str(paths["mpi"].resolve()) + os.sep
    bad_mpi = sorted(path for path in mpi_libraries if not path.startswith(mpi_prefix_real))
    if bad_mpi:
        raise LegacyStackExecutionError(f"mixed MPI ABI detected outside the frozen prefix: {bad_mpi}")
    rejected = str(spec["verification"]["reject_system_openmpi_path"])
    if any(path.startswith(rejected) for path in mpi_libraries):
        raise LegacyStackExecutionError("system OpenMPI ABI leaked into the source stack")

    barrier_code = (
        "import dolfin; from mpi4py import MPI; from petsc4py import PETSc; "
        "MPI.COMM_WORLD.Barrier(); "
        "assert PETSc.Sys.getVersion() == (3, 15, 1); "
        "print('rank=%d imports=ok' % MPI.COMM_WORLD.rank)"
    )
    _run_logged(
        [
            str(mpi_bin / "mpirun"),
            "--allow-run-as-root",
            "-np",
            str(spec["verification"]["mpi_ranks"]),
            str(python_executable),
            "-c",
            barrier_code,
        ],
        env=env,
        log_path=evidence_root / "logs" / "mpi-two-rank-import.log",
    )

    dpkg_text = _capture(["dpkg-query", "-W", "-f=${binary:Package}\t${Version}\n"])
    pip_text = _capture([str(python_executable), "-m", "pip", "freeze", "--all"], env=env)
    ompi_all = _capture([str(mpi_bin / "ompi_info"), "--all"], env=env)
    (evidence_root / "dpkg-query.txt").write_text(dpkg_text, encoding="utf-8")
    (evidence_root / "pip-freeze-all.txt").write_text(pip_text, encoding="utf-8")
    (evidence_root / "ompi-info-all.txt").write_text(ompi_all, encoding="utf-8")
    verification = {
        "schema_version": VERIFY_SCHEMA,
        "status": "ENVIRONMENT_VERIFIED",
        "evidence_identity": "ENGINEERING_ABI_AND_FEATURE_QUALIFICATION_ONLY",
        "scientific_claim_status": "NO_SCIENTIFIC_CLAIMS",
        "qpop_started": False,
        "g2_gate_outcome": "NOT_EVALUATED",
        "environment_id": spec["environment_id"],
        "verified_at": _utc_now(),
        "spec_sha256": spec_sha256,
        "resolution_lock_sha256": _sha256(paths["lock"]),
        "build_manifest_sha256": _sha256(paths["build_manifest"]),
        "os_release": os_release,
        "ompi_version": ompi_version.splitlines()[0] if ompi_version.splitlines() else "",
        "runtime_probe": probe,
        "mpi_library_evidence": library_evidence,
        "unique_mpi_library_paths": sorted(mpi_libraries),
        "dolfin_parmetis_cache_lines": parmetis_lines,
        "two_rank_import_barrier": "PASS",
    }
    _write_json_once(evidence_root / "verification.json", verification)
    return verification


def _record_stage_failure(
    *, command: str, evidence_root: Path | None, error: Exception
) -> None:
    if evidence_root is None or not evidence_root.is_absolute():
        return
    try:
        evidence_root.mkdir(parents=True, exist_ok=True)
        path = evidence_root / f"{command}.failure.json"
        if path.exists():
            return
        _write_json_once(
            path,
            {
                "schema_version": "qpop-legacy-stage-failure-v1",
                "stage": command,
                "status": "FAILED",
                "failed_at": _utc_now(),
                "failure_type": type(error).__name__,
                "message": str(error),
                "scientific_claim_status": "NO_SCIENTIFIC_CLAIMS",
                "g2_gate_outcome": "NOT_EVALUATED",
            },
        )
    except Exception:
        pass


def _default_spec_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "configs"
        / "qpop"
        / "legacy-stack-ubuntu-20.04"
        / "stack_spec.json"
    )


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("check-spec", "print-plan", "resolve", "preflight", "build", "verify"),
    )
    parser.add_argument("--spec", type=Path, default=_default_spec_path())
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        spec = load_stack_spec(args.spec)
        if args.command == "check-spec":
            print(
                json.dumps(
                    {"status": "VALID", "environment_id": spec["environment_id"]},
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "print-plan":
            print(json.dumps(build_execution_plan(spec), indent=2, sort_keys=True))
            return 0
        if not args.execute:
            raise LegacyStackContractError(f"{args.command} requires explicit --execute")
        if args.evidence_root is None or not args.evidence_root.is_absolute():
            raise LegacyStackContractError("mutating stages require an absolute --evidence-root")
        if args.command == "resolve":
            result = _resolve_stage(spec, spec_path=args.spec, evidence_root=args.evidence_root)
        elif args.command == "preflight":
            result = _preflight_stage(
                spec,
                spec_path=args.spec,
                evidence_root=args.evidence_root,
            )
        elif args.command == "build":
            result = _build_stage(spec, spec_path=args.spec, evidence_root=args.evidence_root)
        elif args.command == "verify":
            result = _verify_stage(spec, spec_path=args.spec, evidence_root=args.evidence_root)
        else:  # pragma: no cover - argparse owns the command vocabulary
            raise LegacyStackContractError(f"unsupported command: {args.command}")
        print(json.dumps({"stage": args.command, "status": result["status"]}, sort_keys=True))
        return 0
    except (LegacyStackContractError, LegacyStackExecutionError) as exc:
        _record_stage_failure(command=args.command, evidence_root=args.evidence_root, error=exc)
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (LegacyStackContractError, LegacyStackExecutionError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
