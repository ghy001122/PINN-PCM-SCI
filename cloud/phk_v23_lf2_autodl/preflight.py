"""Zero-update AutoDL preflight for the PHK-V2.3 LF2 deployment."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
from typing import Any

import torch


ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "PHK_V23_LF2_MEASURE_CALIBRATED_FEASIBLE_PINN_EXECUTE"
EXPECTED_GPU = "Tesla V100-PCIE-32GB"
EXPECTED_MANIFEST_SCHEMA = "phk-v23-lf2-deployed-source-manifest-v1"
IDENTITY_DEFINITION = "SHA256_OF_SORTED_PATH_EQUALS_UPPERCASE_SHA256_LINES"
MEDIUM_RELATIVE = PurePosixPath(
    "outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz"
)
CHECKPOINT_RELATIVE = PurePosixPath(
    "outputs/runs/20260903T152501Z-phk-v23-lf1-b-event-replay-dc091be-er1/checkpoint-b0-step-1200.pt"
)
CONTRACT_RELATIVES = {
    "program": PurePosixPath(
        "configs/phk_v23/program_contract_lf2_measure_calibrated_feasible_pinn.json"
    ),
    "method": PurePosixPath(
        "configs/phk_v23/method_contract_lf2_measure_calibrated_feasible_pinn.json"
    ),
    "data": PurePosixPath(
        "configs/phk_v23/data_contract_lf2_measure_calibrated_medium.json"
    ),
    "decision": PurePosixPath(
        "configs/phk_v23/decision_contract_lf2_measure_calibrated_feasible_pinn.json"
    ),
}
REQUIRED_RUNTIME = frozenset(
    {
        *(path.as_posix() for path in CONTRACT_RELATIVES.values()),
        "cloud/phk_v23_lf2_autodl/preflight.py",
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
        "pinn_pcm_sci/phk_v23_lf1.py",
        "pinn_pcm_sci/phk_v23_lf2.py",
    }
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _read(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _safe(root: Path, relative: str) -> Path:
    normalized = PurePosixPath(relative)
    if normalized.is_absolute() or ".." in normalized.parts:
        raise PermissionError("LF2 deployed path escaped its root")
    exact = (root / Path(*normalized.parts)).resolve()
    try:
        exact.relative_to(root.resolve())
    except ValueError as exc:
        raise PermissionError("LF2 deployed path escaped its root") from exc
    return exact


def _manifest(root: Path, source_identity: str) -> dict[str, Any]:
    path = root / "cloud" / "phk_v23_lf2_autodl" / "deployed-source-manifest.json"
    manifest = _read(path)
    if (
        manifest.get("schema_id") != EXPECTED_MANIFEST_SCHEMA
        or manifest.get("identity_definition") != IDENTITY_DEFINITION
        or manifest.get("source_identity") != source_identity
    ):
        raise ValueError("LF2 deployed-source manifest identity drift")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("LF2 deployed-source manifest has no files")
    missing = sorted(REQUIRED_RUNTIME.difference(files))
    if missing:
        raise ValueError(f"LF2 runtime closure is incomplete: {missing}")
    lines: list[str] = []
    for relative, expected in sorted(files.items()):
        exact = _safe(root, relative)
        actual = _sha256(exact) if exact.is_file() else None
        if actual != str(expected).upper():
            raise ValueError(f"LF2 deployed source drift: {relative}")
        lines.append(f"{relative}={actual}\n")
    digest = hashlib.sha256("".join(lines).encode("utf-8")).hexdigest().upper()
    if source_identity != f"LF2-BUNDLE-{digest}":
        raise ValueError("LF2 aggregate source identity mismatch")
    return manifest


def _contracts_and_inputs(
    root: Path,
    manifest: dict[str, Any],
    medium_carrier: Path,
    initial_checkpoint: Path,
) -> dict[str, dict[str, Any]]:
    contracts = {
        role: _read(root / Path(*relative.parts))
        for role, relative in CONTRACT_RELATIVES.items()
    }
    if contracts["program"].get("phase_id") != TASK_ID:
        raise ValueError("LF2 task identity drift")
    authorization = contracts["program"].get("authorization", {})
    if (
        authorization.get("one_gpu_trajectory_after_cpu_gate") is not True
        or authorization.get("seed_17_only") is not True
        or authorization.get("new_seed") is not False
        or authorization.get("stress_prediction_or_unseal") is not False
        or authorization.get("pjgr_or_r2") is not False
    ):
        raise PermissionError("LF2 cloud authorization boundary drift")
    identity = contracts["method"].get("common_identity", {})
    if (
        identity.get("gpu") != "TESLA_V100_PCIE_32GB_ONLY"
        or identity.get("dtype") != "FLOAT64"
        or identity.get("seed") != 17
        or identity.get("potential_transform")
        != "POTENTIAL_TRANSFORM_EXACT_TOP_RANGE_PRESERVING_LOG_RATIO"
    ):
        raise ValueError("LF2 GPU/model identity drift")
    exact_inputs = {
        "medium": (Path(medium_carrier).resolve(), MEDIUM_RELATIVE),
        "initial_checkpoint": (
            Path(initial_checkpoint).resolve(),
            CHECKPOINT_RELATIVE,
        ),
    }
    bindings = {
        "medium": contracts["data"].get("training_source", {}),
        "initial_checkpoint": contracts["data"].get("initial_checkpoint", {}),
    }
    manifest_inputs = manifest.get("training_inputs", {})
    for role, (exact, relative) in exact_inputs.items():
        required = (root / Path(*relative.parts)).resolve()
        binding = bindings[role]
        actual = _sha256(exact) if exact.is_file() else None
        expected_record = {
            "path": relative.as_posix(),
            "sha256": actual,
            "size_bytes": exact.stat().st_size if exact.is_file() else -1,
        }
        if (
            exact != required
            or not exact.is_file()
            or binding.get("path") != relative.as_posix()
            or actual != str(binding.get("sha256", "")).upper()
            or manifest_inputs.get(role) != expected_record
        ):
            raise PermissionError(f"LF2 exact {role} input drift")
    if bindings["medium"].get("only_gpu_training_label_source") is not True:
        raise PermissionError("LF2 medium-only label boundary drift")
    if (
        bindings["initial_checkpoint"].get("load_model_weights") is not True
        or bindings["initial_checkpoint"].get("load_optimizer_state") is not False
    ):
        raise PermissionError("LF2 parent checkpoint loading boundary drift")
    if contracts["decision"].get("stress_status") != "TWO_STRESS_REFERENCES_SEALED_UNREAD":
        raise PermissionError("LF2 stress boundary drift")
    return contracts


def _qualification(
    root: Path,
    manifest: dict[str, Any],
    contracts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    binding = manifest.get("cpu_qualification")
    if not isinstance(binding, dict):
        raise ValueError("LF2 CPU qualification binding is absent")
    exact = _safe(root, str(binding.get("path", "")))
    if (
        not exact.is_file()
        or exact.stat().st_size != int(binding.get("size_bytes", -1))
        or _sha256(exact) != str(binding.get("sha256", "")).upper()
    ):
        raise ValueError("LF2 CPU qualification artifact drift")
    record = _read(exact)
    expected_contracts = {
        role: {
            "path": relative.as_posix(),
            "sha256": manifest["files"][relative.as_posix()],
        }
        for role, relative in CONTRACT_RELATIVES.items()
    }
    if (
        record.get("schema_id") != "phk-v23-lf2-cpu-qualification-v1"
        or record.get("task_id") != TASK_ID
        or record.get("status") != "LF2_CPU_QUALIFICATION_PASS"
        or record.get("gpu_execution_authorized_by_cpu_gate") is not True
        or record.get("contracts") != expected_contracts
        or record.get("fine_extra_fine_reference_read") is not False
        or record.get("stress_fields_or_metrics_read") is not False
        or record.get("partition", {}).get("mutually_exclusive") is not True
        or record.get("partition", {}).get("exhaustive") is not True
    ):
        raise PermissionError("LF2 CPU qualification did not pass for this source")
    return {
        "path": binding["path"],
        "sha256": binding["sha256"],
        "size_bytes": binding["size_bytes"],
        "status": record["status"],
        "partition_sha256": record["partition"]["partition_sha256"],
    }


def _forbidden(root: Path) -> list[str]:
    allowed = {MEDIUM_RELATIVE.as_posix(), CHECKPOINT_RELATIVE.as_posix()}
    result: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.resolve().relative_to(root.resolve()).as_posix()
        if relative in allowed:
            continue
        lower = relative.lower()
        if (
            path.suffix.lower() in {".npz", ".pt"}
            or "nominal-fine" in lower
            or "nominal-extra-fine" in lower
            or any("stress" in part for part in PurePosixPath(lower).parts)
            or "evaluator" in path.name.lower()
        ):
            result.append(relative)
    return sorted(result)


def _duplicates() -> list[str]:
    if os.name != "posix" or not Path("/proc").is_dir():
        return []
    matches: list[str] = []
    for candidate in Path("/proc").iterdir():
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
        if "pinn_pcm_sci.phk_v23_lf2" in tokens:
            matches.append(f"pid:{candidate.name}")
    return sorted(matches)


def run_preflight(
    *,
    source_identity: str,
    deployment_root: Path,
    medium_carrier: Path,
    initial_checkpoint: Path,
    hourly_price_cny: float,
    cuda_probe: Any = None,
    pythonpath: str | None = None,
) -> dict[str, Any]:
    if not Path(deployment_root).is_absolute():
        raise ValueError("LF2 deployment root must be absolute")
    root = ROOT.resolve()
    if Path(deployment_root).resolve() != root:
        raise ValueError("LF2 deployment root does not match loaded source")
    entries = (
        os.environ.get("PYTHONPATH", "") if pythonpath is None else pythonpath
    ).split(os.pathsep)
    if root not in [Path(entry).resolve() for entry in entries if Path(entry).is_absolute()]:
        raise RuntimeError("LF2 absolute deployment root is missing from PYTHONPATH")
    manifest = _manifest(root, source_identity)
    contracts = _contracts_and_inputs(
        root, manifest, Path(medium_carrier), Path(initial_checkpoint)
    )
    qualification = _qualification(root, manifest, contracts)
    price = float(hourly_price_cny)
    limits = contracts["program"]["hard_limits"]
    if (
        not math.isfinite(price)
        or price <= 0.0
        or price * float(limits["maximum_v100_wall_hours"])
        > float(limits["maximum_incremental_cost_cny"])
    ):
        raise RuntimeError("LF2 live price violates the frozen cost cap")
    forbidden = _forbidden(root)
    if forbidden:
        raise PermissionError(f"LF2 forbidden cloud files: {forbidden}")
    duplicates = _duplicates()
    if duplicates:
        raise RuntimeError(f"duplicate LF2 process: {duplicates}")
    cuda = torch.cuda if cuda_probe is None else cuda_probe
    if not cuda.is_available() or cuda.get_device_name(0) != EXPECTED_GPU:
        raise RuntimeError("LF2 requires the exact Tesla V100-PCIE-32GB")
    return {
        "status": "REMOTE_LF2_PREFLIGHT_VALID",
        "task_id": TASK_ID,
        "source_identity": source_identity,
        "deployment_root": str(root),
        "medium_carrier": MEDIUM_RELATIVE.as_posix(),
        "initial_checkpoint": CHECKPOINT_RELATIVE.as_posix(),
        "cpu_qualification": qualification,
        "gpu_name": EXPECTED_GPU,
        "dtype": "FLOAT64",
        "seed": 17,
        "hourly_price_cny": price,
        "maximum_v100_wall_hours": limits["maximum_v100_wall_hours"],
        "maximum_incremental_cost_cny": limits["maximum_incremental_cost_cny"],
        "forbidden_cloud_files": [],
        "duplicate_training_processes": [],
        "optimizer_constructed": False,
        "optimizer_updates": 0,
        "fine_extra_fine_evaluator_present": False,
        "stress_fields_present": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-identity", required=True)
    parser.add_argument("--deployment-root", type=Path, required=True)
    parser.add_argument("--medium-carrier", type=Path, required=True)
    parser.add_argument("--initial-checkpoint", type=Path, required=True)
    parser.add_argument("--hourly-price-cny", type=float, required=True)
    arguments = parser.parse_args()
    print(
        json.dumps(
            run_preflight(
                source_identity=arguments.source_identity,
                deployment_root=arguments.deployment_root,
                medium_carrier=arguments.medium_carrier,
                initial_checkpoint=arguments.initial_checkpoint,
                hourly_price_cny=arguments.hourly_price_cny,
            ),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
