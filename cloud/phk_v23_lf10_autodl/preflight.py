"""Zero-update LF10 source, input, leakage, GPU, and output preflight."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
from typing import Any, Mapping

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "PHK_V23_LF10_EVENT_COMPETENCE_FEASIBLE_DIRECTION_AND_HEADLINE_EVIDENCE_REPLICATION_EXECUTE"
EXPECTED_REMOTE_PARENT = "/root/autodl-tmp"
EXPECTED_GPU = "Tesla V100-PCIE-32GB"

MEDIUM_RELATIVE = PurePosixPath("outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz")
LF3_T0_RELATIVE = PurePosixPath("outputs/runs/20260904T150300Z-phk-v23-lf3-phase-latent-97a5b74/checkpoint-t0-step-1200.pt")
DEV_R_RELATIVE = PurePosixPath("outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/dev_r/checkpoint.pt")
STRONG_LEDGER_RELATIVE = PurePosixPath("outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/cpu/materialized_ledger.npz")
STRONG_MANIFEST_RELATIVE = PurePosixPath("outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/cpu/materialized_ledger_manifest.json")
LF10_LEDGER_RELATIVE = PurePosixPath("outputs/runs/20260909T101615Z-phk-v23-lf10-feasible-direction-replication/cpu/materialized_lf10_ledger.npz")
LF10_MANIFEST_RELATIVE = PurePosixPath("outputs/runs/20260909T101615Z-phk-v23-lf10-feasible-direction-replication/cpu/materialized_lf10_ledger_manifest.json")

EXPECTED_SHA256 = {
    "medium": "18411D8066FACB31570774374A699ECE867981752ED9FEE25C34DF30D5D8802F",
    "lf3_t0_checkpoint": "4A679E54A4819A9D30CF55C6396C37129B9801BC635A8BD7EB3883F8F3B66EDA",
    "dev_r_checkpoint": "7CFDD98E3A03BE29BBE587042967BD44E72D140AE7AC3396CB35E0CF5748F499",
    "strong_ledger": "29E02DAF81A07BA4AF2B95B354126E75E9419AAE094E9486589455D31D2D6801",
    "strong_ledger_manifest": "3CFA268CFB22CF225ABB92BFD7F9F00353634AF7AFEE7AA607EC59FE4F4C8F90",
    "lf10_ledger": "90BA299A37EFB6F01EA6B0AE28472182D89A2428F685D70819E97B4966B975A5",
    "lf10_ledger_manifest": "4917BE4A245D678E9FBE76AAD9121ED4E326527A04A97634A6F78E552F6F3271",
}
EXPECTED_AUDIT_BASELINES = {
    "shape": [1200, 4],
    "dtype": "<f8",
    "sha256": "B49D0D5CF98A4A62472DB461674B23A0FE33B2FB8E5278B35351B3FDF5BA01CB",
}
EXPECTED_STRONG_SEMANTIC = "0E2F680D33C4489F6092CB5D01E87483F7ECDA8290CD3E2C24EBDD06B3DA2B7F"
EXPECTED_PHYSICS_STREAM = "536E6706A0B68EBB1277A97F402D273AFA2EA1E0B27106F26CB4222B7EC05C53"
EXPECTED_FIXED_POOL = "FD285AFC67C011CE9778E36C5FEE8FA7EAECB933690AF346993B7677AF0E64CF"

REQUIRED_RUNTIME = {
    "configs/phk_v23/lf10_write_allowlist_lock.json",
    "configs/phk_v23/program_contract_lf10_feasible_direction_replication.json",
    "configs/phk_v23/method_contract_lf10_feasible_direction_replication.json",
    "configs/phk_v23/data_contract_lf10_feasible_direction_replication.json",
    "configs/phk_v23/decision_contract_lf10_feasible_direction_replication.json",
    "cloud/phk_v23_lf10_autodl/README.md",
    "cloud/phk_v23_lf10_autodl/build_bundle.py",
    "cloud/phk_v23_lf10_autodl/preflight.py",
    "cloud/phk_v23_lf10_autodl/run.sh",
    "pinn_pcm_sci/phk_v23_lf10.py",
    "pinn_pcm_sci/phk_v23_lf10_qualification.py",
    "pinn_pcm_sci/phk_v23_lf9.py",
    "pinn_pcm_sci/phk_v23_lf8.py",
    "pinn_pcm_sci/phk_v23_lf6.py",
    "pinn_pcm_sci/phk_v23_lf4.py",
    "pinn_pcm_sci/phk_v23_lf3.py",
    "tests/test_phk_v21_benchmark.py",
}
EXPECTED_INPUT_ROLES = {
    "medium", "lf3_t0_checkpoint", "dev_r_checkpoint", "strong_ledger",
    "strong_ledger_manifest", "lf10_ledger", "lf10_ledger_manifest",
    "cpu_qualification",
}
EXPECTED_SCIENTIFIC_ORDER = [
    "MATCHED_CTRL_PROJ_SCREENS",
    "CONDITIONAL_SELECTED_FULL_REFINEMENT",
    "INTERFACE_REPLICATION_STREAMS_23_29",
    "FORGETTING_REPLICATION_STREAMS_23_29",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _record(root: Path, path: Path) -> dict[str, Any]:
    exact = path.resolve()
    return {
        "path": exact.relative_to(root.resolve()).as_posix(),
        "sha256": _sha256(exact),
        "size_bytes": exact.stat().st_size,
    }


def _array_record(name: str, value: np.ndarray) -> dict[str, Any]:
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256(b"PHK_V23_LF10_ARRAY_V1\n")
    digest.update(name.encode("ascii")); digest.update(b"\n")
    digest.update(array.dtype.str.encode("ascii")); digest.update(b"\n")
    digest.update(json.dumps(list(array.shape), separators=(",", ":")).encode("ascii")); digest.update(b"\n")
    digest.update(array.tobytes(order="C"))
    return {"shape": list(array.shape), "dtype": array.dtype.str, "sha256": digest.hexdigest().upper()}


def _read_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"LF10 expected JSON object: {path}")
    return payload


def _verify_output_root(deployment_root: Path, output_root: Path) -> dict[str, Any]:
    output = output_root.resolve()
    parent = Path(EXPECTED_REMOTE_PARENT).resolve()
    if not output_root.is_absolute() or output.parent != parent or not output.name.startswith("lf10-run-"):
        raise ValueError("LF10 output root is outside the frozen campaign namespace")
    if output == deployment_root.resolve() or deployment_root.resolve() in output.parents:
        raise ValueError("LF10 output root overlaps the deployment")
    if not output.is_dir():
        raise FileNotFoundError("LF10 output root must exist before preflight")
    if any(output.iterdir()):
        raise RuntimeError("LF10 output root is not empty")
    return {"path": output.as_posix(), "empty": True}


def _verify_gpu(cuda_probe: Any = None) -> str:
    if cuda_probe is None:
        import torch
        cuda_probe = torch.cuda
    if not cuda_probe.is_available():
        raise RuntimeError("LF10 CUDA unavailable")
    name = str(cuda_probe.get_device_name(0))
    if name != EXPECTED_GPU:
        raise RuntimeError(f"LF10 requires {EXPECTED_GPU}, got {name}")
    return name


def _forbidden(root: Path, allowed: set[str]) -> list[str]:
    tokens = (
        "nominal-fine", "extra-fine", "lf_only", "lf-only", "stress",
        "phk_v23_lf10_evaluation.py", "local_adjudication",
    )
    result: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative not in allowed and any(token in relative.lower() for token in tokens):
            result.append(relative)
    return sorted(result)


def _duplicates() -> list[str]:
    completed = subprocess.run(
        ["ps", "-eo", "pid,args"], capture_output=True, text=True, check=False
    )
    if completed.returncode:
        return []
    own_pid = os.getpid()
    return [
        line.strip() for line in completed.stdout.splitlines()
        if "pinn_pcm_sci.phk_v23_lf10" in line and not line.lstrip().startswith(str(own_pid))
    ]


def _manifest(root: Path, source_identity: str) -> dict[str, Any]:
    path = root / "cloud/phk_v23_lf10_autodl/deployed-source-manifest.json"
    manifest = _read_object(path)
    if (
        manifest.get("schema_id") != "phk-v23-lf10-deployed-source-manifest-v1"
        or manifest.get("task_id") != TASK_ID
        or manifest.get("source_identity") != source_identity
        or manifest.get("runtime_coordinate_generation") is not False
        or manifest.get("arm_local_failure_isolation") is not True
        or manifest.get("scientific_order") != EXPECTED_SCIENTIFIC_ORDER
        or manifest.get("medium_gradient_used_for_projection") is not True
        or manifest.get("medium_gradient_used_in_physics_loss") is not False
    ):
        raise PermissionError("LF10 deployed source identity drift")
    files = manifest.get("files")
    if not isinstance(files, Mapping) or not REQUIRED_RUNTIME.issubset(files):
        raise PermissionError("LF10 deployed runtime closure is incomplete")
    for relative, digest in files.items():
        exact = root / str(relative)
        if not exact.is_file() or _sha256(exact) != str(digest).upper():
            raise PermissionError(f"LF10 deployed source drift: {relative}")
    return manifest


def _ledger_identity(qualification: Mapping[str, Any]) -> Mapping[str, Any]:
    identity = qualification.get("lf10_ledger")
    if not isinstance(identity, Mapping):
        identity = qualification.get("ledger")
    if not isinstance(identity, Mapping):
        raise PermissionError("LF10 qualification lacks materialized-ledger identity")
    return identity


def _verify_qualification(path: Path, root: Path) -> dict[str, Any]:
    payload = _read_object(path)
    reference_boundary = payload.get("reference_boundary", {})
    if (
        payload.get("schema_id") != "phk-v23-lf10-cpu-qualification-v1"
        or payload.get("task_id") != TASK_ID
        or payload.get("gate_outcome") != "LF10_CPU_QUALIFICATION_PASS"
        or int(payload.get("scientific_optimizer_updates", -1)) != 0
        or payload.get("gpu_execution_authorized_by_cpu_gate") is not True
        or not isinstance(payload.get("checks"), Mapping)
        or not payload["checks"]
        or not all(value is True for value in payload["checks"].values())
        or payload.get("gpu_used") is not False
        or not isinstance(reference_boundary, Mapping)
        or any(reference_boundary.get(key) is not False for key in (
            "fine_read", "extra_fine_read", "direct_LF_ONLY_read",
            "frozen_evaluator_read", "stress_read",
        ))
    ):
        raise PermissionError("LF10 CPU qualification invalid")
    return payload


def _verify_strong_manifest(path: Path) -> dict[str, Any]:
    payload = _read_object(path)
    streams = payload.get("streams", {})
    if (
        payload.get("schema_id") != "phk-v23-lf6-materialized-ledger-manifest-v1"
        or payload.get("runtime_sampling_permitted") is not False
        or str(payload.get("semantic_sha256", "")).upper() != EXPECTED_STRONG_SEMANTIC
        or str(streams.get("P0_physics_1200_sha256", "")).upper() != EXPECTED_PHYSICS_STREAM
        or str(streams.get("fixed_blind_pool_sha256", "")).upper() != EXPECTED_FIXED_POOL
    ):
        raise PermissionError("LF10 inherited strong-ledger identity drift")
    return payload


def _verify_lf10_manifest(ledger: Path, manifest_path: Path,
                          qualification: Mapping[str, Any]) -> dict[str, Any]:
    payload = _read_object(manifest_path)
    identity = _ledger_identity(qualification)
    with np.load(ledger, allow_pickle=False) as archive:
        if "audit_baselines" not in archive.files:
            raise PermissionError("LF10 same-batch audit_baselines array is absent")
        audit_baselines = _array_record("audit_baselines", np.asarray(archive["audit_baselines"]))
    if (
        payload.get("schema_id") != "phk-v23-lf10-materialized-ledger-manifest-v1"
        or payload.get("runtime_sampling_permitted") is not False
        or payload.get("task_id") != TASK_ID
        or str(identity.get("path", "")) != LF10_LEDGER_RELATIVE.as_posix()
        or str(identity.get("manifest_path", "")) != LF10_MANIFEST_RELATIVE.as_posix()
        or str(identity.get("sha256", "")).upper() != _sha256(ledger)
        or str(identity.get("manifest_sha256", "")).upper() != _sha256(manifest_path)
        or str(identity.get("semantic_sha256", "")).upper() != str(payload.get("semantic_sha256", "")).upper()
        or audit_baselines != EXPECTED_AUDIT_BASELINES
        or payload.get("arrays", {}).get("audit_baselines") != EXPECTED_AUDIT_BASELINES
        or identity.get("arrays", {}).get("audit_baselines") != EXPECTED_AUDIT_BASELINES
    ):
        raise PermissionError("LF10 materialized-ledger identity drift")
    return payload


def run_preflight(*, source_identity: str, deployment_root: Path, output_root: Path,
                  medium_carrier: Path, lf3_t0_checkpoint: Path,
                  dev_r_checkpoint: Path, strong_ledger: Path,
                  lf10_ledger: Path, lf10_ledger_manifest: Path,
                  cpu_qualification: Path, cuda_probe: Any = None,
                  pythonpath: str | None = None) -> dict[str, Any]:
    root = ROOT.resolve()
    if not Path(deployment_root).is_absolute() or Path(deployment_root).resolve() != root:
        raise ValueError("LF10 deployment root mismatch")
    entries = (os.environ.get("PYTHONPATH", "") if pythonpath is None else pythonpath).split(os.pathsep)
    if root not in [Path(entry).resolve() for entry in entries if Path(entry).is_absolute()]:
        raise RuntimeError("LF10 absolute deployment root absent from PYTHONPATH")
    deployed = _manifest(root, source_identity)
    if set(deployed.get("materialized_inputs", {})) != EXPECTED_INPUT_ROLES:
        raise PermissionError("LF10 deployed input boundary drift")
    paths = {
        "medium": (Path(medium_carrier).resolve(), MEDIUM_RELATIVE, EXPECTED_SHA256["medium"]),
        "lf3_t0_checkpoint": (Path(lf3_t0_checkpoint).resolve(), LF3_T0_RELATIVE, EXPECTED_SHA256["lf3_t0_checkpoint"]),
        "dev_r_checkpoint": (Path(dev_r_checkpoint).resolve(), DEV_R_RELATIVE, EXPECTED_SHA256["dev_r_checkpoint"]),
        "strong_ledger": (Path(strong_ledger).resolve(), STRONG_LEDGER_RELATIVE, EXPECTED_SHA256["strong_ledger"]),
        "strong_ledger_manifest": ((root / Path(*STRONG_MANIFEST_RELATIVE.parts)).resolve(), STRONG_MANIFEST_RELATIVE, EXPECTED_SHA256["strong_ledger_manifest"]),
        "lf10_ledger": (Path(lf10_ledger).resolve(), LF10_LEDGER_RELATIVE, EXPECTED_SHA256["lf10_ledger"]),
        "lf10_ledger_manifest": (Path(lf10_ledger_manifest).resolve(), LF10_MANIFEST_RELATIVE, EXPECTED_SHA256["lf10_ledger_manifest"]),
    }
    qrel = PurePosixPath(str(deployed["materialized_inputs"]["cpu_qualification"]["path"]))
    paths["cpu_qualification"] = (Path(cpu_qualification).resolve(), qrel,
                                  str(deployed["materialized_inputs"]["cpu_qualification"]["sha256"]).upper())
    for role, (exact, relative, digest) in paths.items():
        required = (root / Path(*relative.parts)).resolve()
        binding = deployed.get("materialized_inputs", {}).get(role)
        if (
            exact != required or not exact.is_file() or _sha256(exact) != digest
            or not isinstance(binding, Mapping) or _record(root, exact) != dict(binding)
        ):
            raise PermissionError(f"LF10 exact deployed input drift: {role}")
    source_lines = [
        f"source:{path}={str(digest).upper()}\n"
        for path, digest in sorted(deployed["files"].items())
    ]
    input_lines = [
        f"input:{role}={str(record['sha256']).upper()}\n"
        for role, record in sorted(deployed["materialized_inputs"].items())
    ]
    aggregate = "LF10-BUNDLE-" + hashlib.sha256(
        (f"base_commit={str(deployed['base_commit']).upper()}\n" + "".join(source_lines) + "".join(input_lines)).encode("ascii")
    ).hexdigest().upper()
    if source_identity != aggregate:
        raise PermissionError("LF10 aggregate deployment identity drift")
    qualification = _verify_qualification(Path(cpu_qualification), root)
    strong = _verify_strong_manifest(paths["strong_ledger_manifest"][0])
    qstrong = qualification.get("strong_ledger", {})
    if (
        not isinstance(qstrong, Mapping)
        or str(qstrong.get("sha256", "")).upper() != EXPECTED_SHA256["strong_ledger"]
        or str(qstrong.get("manifest_sha256", "")).upper() != EXPECTED_SHA256["strong_ledger_manifest"]
        or str(qstrong.get("semantic_sha256", "")).upper() != EXPECTED_STRONG_SEMANTIC
        or str(qstrong.get("physics_1200_sha256", "")).upper() != EXPECTED_PHYSICS_STREAM
        or str(qstrong.get("fixed_blind_pool_sha256", "")).upper() != EXPECTED_FIXED_POOL
    ):
        raise PermissionError("LF10 inherited strong qualification binding drift")
    ledger = _verify_lf10_manifest(Path(lf10_ledger), Path(lf10_ledger_manifest), qualification)
    runner = (root / "pinn_pcm_sci/phk_v23_lf10.py").read_text(encoding="utf-8")
    generators = [token for token in ("SobolEngine(", "LF0PhysicsBatchStream(", "PhkCollocationSampler(") if token in runner]
    if generators:
        raise PermissionError(f"LF10 runner contains runtime coordinate generators: {generators}")
    output = _verify_output_root(root, Path(output_root))
    allowed = {relative.as_posix() for _, relative, _ in paths.values()}
    forbidden, duplicates = _forbidden(root, allowed), _duplicates()
    if forbidden:
        raise PermissionError(f"LF10 forbidden cloud files present: {forbidden}")
    if duplicates:
        raise RuntimeError(f"duplicate LF10 training process: {duplicates}")
    gpu_name = _verify_gpu(cuda_probe)
    return {
        "status": "REMOTE_LF10_PREFLIGHT_VALID",
        "task_id": TASK_ID,
        "source_identity": source_identity,
        "base_commit": deployed["base_commit"],
        "gpu_name": gpu_name,
        "dtype": "FLOAT64",
        "seed": 17,
        "scientific_order": deployed["scientific_order"],
        "arm_local_failure_isolation": True,
        "output_root": output,
        "strong_ledger_semantic_sha256": strong["semantic_sha256"],
        "lf10_ledger_semantic_sha256": ledger["semantic_sha256"],
        "qualification_gate_outcome": qualification["gate_outcome"],
        "forbidden_cloud_files": [],
        "duplicate_training_processes": [],
        "runtime_coordinate_generation": False,
        "optimizer_constructed": False,
        "optimizer_updates": 0,
        "stress_fields_present": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-identity", required=True)
    parser.add_argument("--deployment-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--medium-carrier", type=Path, required=True)
    parser.add_argument("--lf3-t0-checkpoint", type=Path, required=True)
    parser.add_argument("--dev-r-checkpoint", type=Path, required=True)
    parser.add_argument("--strong-ledger", type=Path, required=True)
    parser.add_argument("--lf10-ledger", type=Path, required=True)
    parser.add_argument("--lf10-ledger-manifest", type=Path, required=True)
    parser.add_argument("--cpu-qualification", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run_preflight(source_identity=args.source_identity,
                                   deployment_root=args.deployment_root,
                                   output_root=args.output_root,
                                   medium_carrier=args.medium_carrier,
                                   lf3_t0_checkpoint=args.lf3_t0_checkpoint,
                                   dev_r_checkpoint=args.dev_r_checkpoint,
                                   strong_ledger=args.strong_ledger,
                                   lf10_ledger=args.lf10_ledger,
                                   lf10_ledger_manifest=args.lf10_ledger_manifest,
                                   cpu_qualification=args.cpu_qualification),
                     sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
