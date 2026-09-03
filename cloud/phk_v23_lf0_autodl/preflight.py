"""Zero-update AutoDL preflight for the PHK-V2.3 LF0 deployment."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from typing import Any

import torch


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE_PATHS = {
    "program": PurePosixPath(
        "configs/phk_v23/program_contract_lf0_exact_top_warmstart.json"
    ),
    "method": PurePosixPath(
        "configs/phk_v23/method_contract_lf0_exact_top_warmstart.json"
    ),
    "data": PurePosixPath("configs/phk_v23/data_contract_lf0_medium_only.json"),
    "decision": PurePosixPath("configs/phk_v23/decision_contract_lf0_attribution.json"),
}
MANIFEST_RELATIVE_PATH = PurePosixPath(
    "cloud/phk_v23_lf0_autodl/deployed-source-manifest.json"
)
MEDIUM_RELATIVE_PATH = PurePosixPath(
    "outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz"
)
EXPECTED_TASK_ID = "PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE"
EXPECTED_GPU = "Tesla V100-PCIE-32GB"
EXPECTED_DTYPE = "FLOAT64"
EXPECTED_MANIFEST_SCHEMA = "phk-v23-lf0-deployed-source-manifest-v1"
EXPECTED_CONTRACT_SCHEMAS = {
    "program": "phk-v23-lf0-program-contract-v1",
    "method": "phk-v23-lf0-method-contract-v1",
    "data": "phk-v23-lf0-data-contract-v1",
    "decision": "phk-v23-lf0-decision-contract-v1",
}
IDENTITY_DEFINITION = "SHA256_OF_SORTED_PATH_EQUALS_UPPERCASE_SHA256_LINES"
EXPECTED_CPU_QUALIFICATION_SCHEMA = "phk-v23-lf0-cpu-qualification-v1"
REQUIRED_RUNTIME_RELATIVE_PATHS = frozenset(
    {
        *(relative.as_posix() for relative in CONTRACT_RELATIVE_PATHS.values()),
        "cloud/phk_v23_lf0_autodl/preflight.py",
        "configs/phk_v22r/program_contract.json",
        "configs/phk_v22r/method_contract.json",
        "configs/phk_v21/program_contract.json",
        "configs/phk_v21/object_numerical_contract.json",
        "configs/phk_v21/engineering_contract.json",
        "configs/phk_v21/e1_solver_selection.json",
        "configs/phk_v2/program_contract.json",
        "configs/phk_v2/object_numerical_contract.json",
        "outputs/runs/20260827T-phk-v21-e2-engineering-search-001/summary.json",
        "pinn_pcm_sci/__init__.py",
        "pinn_pcm_sci/artifacts.py",
        "pinn_pcm_sci/phk_contract.py",
        "pinn_pcm_sci/phk_benchmark.py",
        "pinn_pcm_sci/phk_v21_benchmark.py",
        "pinn_pcm_sci/phk_v21_solver.py",
        "pinn_pcm_sci/phk_v22r_pinn.py",
        "pinn_pcm_sci/phk_v22r_training.py",
        "pinn_pcm_sci/phk_v22r_prediction.py",
        "pinn_pcm_sci/phk_v23_lf0.py",
        "tests/test_phk_v21_benchmark.py",
    }
)


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _safe_deployed_path(root: Path, relative: str) -> Path:
    normalized = PurePosixPath(relative)
    if normalized.is_absolute() or ".." in normalized.parts:
        raise PermissionError(f"deployed-source path escaped project: {relative}")
    exact = (root / Path(*normalized.parts)).resolve()
    try:
        exact.relative_to(root)
    except ValueError as exc:
        raise PermissionError(f"deployed-source path escaped project: {relative}") from exc
    return exact


def _load_and_validate_manifest(root: Path, source_identity: str) -> dict[str, Any]:
    manifest_path = root / Path(*MANIFEST_RELATIVE_PATH.parts)
    manifest = _read_json(manifest_path)
    if manifest.get("schema_id") != EXPECTED_MANIFEST_SCHEMA:
        raise ValueError("unsupported LF0 deployed-source manifest")
    if manifest.get("identity_definition") != IDENTITY_DEFINITION:
        raise ValueError("unsupported LF0 source-identity definition")
    if manifest.get("source_identity") != source_identity:
        raise ValueError("LF0 deployed-source identity mismatch")

    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("LF0 deployed-source manifest has no files")
    missing_runtime = sorted(REQUIRED_RUNTIME_RELATIVE_PATHS.difference(files))
    if missing_runtime:
        raise ValueError(f"LF0 deployed-source runtime closure is incomplete: {missing_runtime}")

    identity_lines: list[str] = []
    for relative, expected in sorted(files.items()):
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise ValueError("invalid LF0 deployed-source file entry")
        exact = _safe_deployed_path(root, relative)
        actual = _sha256_path(exact) if exact.is_file() else None
        if actual != expected.upper():
            raise ValueError(f"LF0 deployed-source drift: {relative}")
        identity_lines.append(f"{relative}={actual}\n")
    calculated = hashlib.sha256("".join(identity_lines).encode("utf-8")).hexdigest().upper()
    if source_identity != f"LF0-BUNDLE-{calculated}":
        raise ValueError("LF0 aggregate source identity mismatch")
    return manifest


def _is_upper_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and value == value.upper()
        and all(character in "0123456789ABCDEF" for character in value)
    )


def _validate_cpu_qualification(
    *,
    root: Path,
    manifest: dict[str, Any],
    contracts: dict[str, dict[str, Any]],
    source_identity: str,
) -> dict[str, Any]:
    binding = manifest.get("cpu_qualification")
    if not isinstance(binding, dict):
        raise ValueError("LF0 CPU qualification binding is missing")
    relative = binding.get("path")
    expected_sha = binding.get("sha256")
    expected_size = binding.get("size_bytes")
    if (
        not isinstance(relative, str)
        or not _is_upper_sha256(expected_sha)
        or not isinstance(expected_size, int)
        or isinstance(expected_size, bool)
        or expected_size <= 0
    ):
        raise ValueError("LF0 CPU qualification binding is malformed")
    exact = _safe_deployed_path(root, relative)
    if (
        not exact.is_file()
        or exact.stat().st_size != expected_size
        or _sha256_path(exact) != expected_sha
    ):
        raise ValueError("LF0 CPU qualification artifact drift")
    record = _read_json(exact)
    if (
        record.get("schema_id") != EXPECTED_CPU_QUALIFICATION_SCHEMA
        or record.get("task_id") != EXPECTED_TASK_ID
        or record.get("status") != "LF0_CPU_QUALIFIED"
        or record.get("passed") is not True
        or record.get("blockers") != []
    ):
        raise PermissionError("LF0 CPU qualification did not pass")
    if record.get("qualified_source_identity") != source_identity:
        raise ValueError("LF0 CPU qualification source identity mismatch")
    source_commit = manifest.get("source_commit")
    if (
        not isinstance(source_commit, str)
        or len(source_commit) != 40
        or any(character not in "0123456789abcdefABCDEF" for character in source_commit)
        or record.get("source_commit") != source_commit
    ):
        raise ValueError("LF0 CPU qualification source commit mismatch")

    files = manifest["files"]
    contract_identities = record.get("contract_identities")
    if not isinstance(contract_identities, dict) or set(contract_identities) != set(
        CONTRACT_RELATIVE_PATHS
    ):
        raise ValueError("LF0 CPU qualification contract identities are incomplete")
    for role, contract_path in CONTRACT_RELATIVE_PATHS.items():
        identity = contract_identities.get(role)
        relative_contract = contract_path.as_posix()
        if not isinstance(identity, dict) or identity != {
            "path": relative_contract,
            "sha256": files[relative_contract],
        }:
            raise ValueError(f"LF0 CPU qualification {role} contract mismatch")

    expected_inputs: dict[str, Any] = {
        "low_fidelity_training_source": contracts["data"].get("training_source"),
        "qualification_fine": contracts["data"].get("qualification_only", {}).get("fine"),
        "qualification_extra_fine": contracts["data"].get("qualification_only", {}).get(
            "extra_fine"
        ),
        **contracts["decision"].get("qualification_inputs", {}),
    }
    input_identities = record.get("input_identities")
    if not isinstance(input_identities, dict) or set(input_identities) != set(expected_inputs):
        raise ValueError("LF0 CPU qualification input identities are incomplete")
    for label, expected in expected_inputs.items():
        actual = input_identities.get(label)
        if not isinstance(expected, dict) or not isinstance(actual, dict):
            raise ValueError(f"LF0 CPU qualification {label} identity is malformed")
        if actual.get("path") != expected.get("path") or actual.get("sha256") != str(
            expected.get("sha256", "")
        ).upper():
            raise ValueError(f"LF0 CPU qualification {label} identity mismatch")
    medium = input_identities["low_fidelity_training_source"]
    training_input = manifest["training_input"]
    if medium.get("size_bytes") != training_input.get("size_bytes"):
        raise ValueError("LF0 CPU qualification medium input size mismatch")
    return {
        "path": relative,
        "sha256": expected_sha,
        "size_bytes": expected_size,
        "status": record["status"],
        "source_commit": source_commit,
    }


def _validate_contracts_and_medium(
    *, root: Path, manifest: dict[str, Any], medium_carrier: Path
) -> dict[str, dict[str, Any]]:
    contracts = {
        role: _read_json(root / Path(*relative.parts))
        for role, relative in CONTRACT_RELATIVE_PATHS.items()
    }
    for role, expected_schema in EXPECTED_CONTRACT_SCHEMAS.items():
        if contracts[role].get("schema_id") != expected_schema:
            raise ValueError(f"unsupported LF0 {role} contract")

    program = contracts["program"]
    method = contracts["method"]
    data = contracts["data"]
    decision = contracts["decision"]
    if program.get("phase_id") != EXPECTED_TASK_ID:
        raise ValueError("LF0 task identity mismatch")

    program_path = CONTRACT_RELATIVE_PATHS["program"].as_posix()
    if (
        method.get("program_contract") != program_path
        or data.get("program_contract") != program_path
        or decision.get("program_contract") != program_path
        or decision.get("method_contract")
        != CONTRACT_RELATIVE_PATHS["method"].as_posix()
        or decision.get("data_contract") != CONTRACT_RELATIVE_PATHS["data"].as_posix()
    ):
        raise ValueError("LF0 cross-contract identity drift")

    authorization = program.get("authorization", {})
    if (
        authorization.get("gpu_run_a") is not True
        or authorization.get("gpu_run_b_after_valid_a") is not True
        or authorization.get("conditional_gpu_run_c") is not True
        or authorization.get("new_seed") is not False
        or authorization.get("stress_prediction_or_unseal") is not False
        or authorization.get("benchmark_physics_reference_evaluator_change") is not False
    ):
        raise PermissionError("LF0 cloud authorization boundary is not frozen")

    gpu = method.get("common_gpu_identity", {})
    if (
        gpu.get("gpu") != "TESLA_V100_PCIE_32GB_ONLY"
        or gpu.get("dtype") != EXPECTED_DTYPE
        or gpu.get("seed") != 17
        or gpu.get("arm") != "STRONG_RAW"
    ):
        raise ValueError("LF0 V100/FP64/seed/arm identity drift")

    source = data.get("training_source", {})
    if source.get("path") != MEDIUM_RELATIVE_PATH.as_posix():
        raise PermissionError("LF0 medium training-source path drift")
    if source.get("only_gpu_training_label_source") is not True:
        raise PermissionError("LF0 medium source is not frozen as the only GPU label source")
    expected_sha = source.get("sha256")
    if not isinstance(expected_sha, str):
        raise ValueError("LF0 medium training-source hash missing")
    cloud_boundary = data.get("cloud_boundary", {})
    if (
        cloud_boundary.get("medium_allowed_as_declared_method_input") is not True
        or cloud_boundary.get(
            "fine_extra_fine_evaluator_and_stress_carriers_inaccessible"
        )
        is not True
        or cloud_boundary.get("stress_fail_closed_before_io") is not True
        or decision.get("stress_status") != "TWO_STRESS_REFERENCES_SEALED_UNREAD"
    ):
        raise PermissionError("LF0 data or stress boundary drift")

    exact_medium = medium_carrier.resolve()
    required_medium = (root / Path(*MEDIUM_RELATIVE_PATH.parts)).resolve()
    if exact_medium != required_medium or not exact_medium.is_file():
        raise PermissionError("only the exact LF0 medium carrier is permitted")
    actual_sha = _sha256_path(exact_medium)
    if actual_sha != expected_sha.upper():
        raise ValueError("LF0 medium carrier drift")

    training_input = manifest.get("training_input")
    if not isinstance(training_input, dict):
        raise ValueError("LF0 deployed-source manifest has no training_input binding")
    if (
        training_input.get("path") != MEDIUM_RELATIVE_PATH.as_posix()
        or training_input.get("sha256") != actual_sha
        or training_input.get("size_bytes") != exact_medium.stat().st_size
    ):
        raise ValueError("LF0 manifest medium-carrier identity mismatch")
    return contracts


def _forbidden_cloud_files(root: Path) -> list[str]:
    forbidden: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            relative = path.resolve().relative_to(root).as_posix()
        except ValueError:
            forbidden.append(str(path))
            continue
        if relative == MEDIUM_RELATIVE_PATH.as_posix():
            continue
        lower = relative.lower()
        name = path.name.lower()
        if (
            path.suffix.lower() == ".npz"
            or "result-intent" in name
            or "nominal-fine" in lower
            or "nominal-extra-fine" in lower
            or "stress-reference" in lower
            or any("stress" in part for part in PurePosixPath(lower).parts)
            or "evaluator" in name
        ):
            forbidden.append(relative)
    return sorted(forbidden)


def _running_lf0_training_processes() -> list[str]:
    """Return only process identifiers, never full command lines or credentials."""

    proc = Path("/proc")
    if os.name != "posix" or not proc.is_dir():
        return []
    matches: list[str] = []
    for candidate in proc.iterdir():
        if not candidate.name.isdigit() or int(candidate.name) == os.getpid():
            continue
        try:
            tokens = [
                item.decode("utf-8", errors="replace")
                for item in (candidate / "cmdline").read_bytes().split(b"\0")
                if item
            ]
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if "pinn_pcm_sci.phk_v23_lf0" in tokens and "run" in tokens:
            matches.append(f"pid:{candidate.name}")
    return sorted(matches)


def _validate_absolute_pythonpath(root: Path, pythonpath: str | None) -> None:
    entries = [] if not pythonpath else pythonpath.split(os.pathsep)
    resolved: list[Path] = []
    for entry in entries:
        candidate = Path(entry)
        if candidate.is_absolute():
            resolved.append(candidate.resolve())
    if root not in resolved:
        raise RuntimeError("LF0 absolute deployment root is missing from PYTHONPATH")


def run_preflight(
    *,
    source_identity: str,
    deployment_root: Path,
    medium_carrier: Path,
    project_root: Path = ROOT,
    cuda_probe: Any = None,
    pythonpath: str | None = None,
) -> dict[str, object]:
    supplied_root = Path(deployment_root)
    if not supplied_root.is_absolute():
        raise ValueError("LF0 deployment root must be absolute")
    root = Path(project_root).resolve()
    if supplied_root.resolve() != root:
        raise ValueError("LF0 deployment root does not match the loaded source tree")
    _validate_absolute_pythonpath(
        root, os.environ.get("PYTHONPATH") if pythonpath is None else pythonpath
    )

    manifest = _load_and_validate_manifest(root, source_identity)
    contracts = _validate_contracts_and_medium(
        root=root, manifest=manifest, medium_carrier=Path(medium_carrier)
    )
    qualification = _validate_cpu_qualification(
        root=root,
        manifest=manifest,
        contracts=contracts,
        source_identity=source_identity,
    )
    forbidden = _forbidden_cloud_files(root)
    if forbidden:
        raise PermissionError(f"LF0 forbidden cloud files: {forbidden}")
    duplicates = _running_lf0_training_processes()
    if duplicates:
        raise RuntimeError(f"duplicate LF0 training process detected: {duplicates}")

    cuda = torch.cuda if cuda_probe is None else cuda_probe
    if not cuda.is_available():
        raise RuntimeError("CUDA is unavailable")
    gpu_name = cuda.get_device_name(0)
    if gpu_name != EXPECTED_GPU:
        raise RuntimeError(f"unexpected GPU: {gpu_name}")

    return {
        "status": "REMOTE_LF0_PREFLIGHT_VALID",
        "task_id": EXPECTED_TASK_ID,
        "source_identity": source_identity,
        "deployment_root": str(root),
        "medium_carrier": MEDIUM_RELATIVE_PATH.as_posix(),
        "cpu_qualification": qualification,
        "gpu_name": gpu_name,
        "dtype": EXPECTED_DTYPE,
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "forbidden_cloud_files": forbidden,
        "duplicate_training_processes": duplicates,
        "fine_or_extra_training_source_present": False,
        "stress_or_reference_evaluator_present": False,
        "optimizer_constructed": False,
        "optimizer_updates": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-identity", required=True)
    parser.add_argument("--deployment-root", type=Path, required=True)
    parser.add_argument("--medium-carrier", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            run_preflight(
                source_identity=args.source_identity,
                deployment_root=args.deployment_root,
                medium_carrier=args.medium_carrier,
            ),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
