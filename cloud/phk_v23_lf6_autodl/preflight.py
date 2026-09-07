"""Zero-update remote identity, ledger, leakage, process, and V100 preflight for LF6."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
from typing import Any, Iterable, Mapping

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "PHK_V23_LF6_EVENT_FRONTIER_RANK_BAND_AND_SAFETY_GATED_PHYSICS_PILOT_EXECUTE"
EXPECTED_GPU = "Tesla V100-PCIE-32GB"
EXPECTED_DEV_M_SHA256 = "16EEE20C6B1A2510ACB387E83894ADD64061D631422FAB4DAA9EC1F7194018B5"
EXPECTED_INITIAL_SHA256 = "4A679E54A4819A9D30CF55C6396C37129B9801BC635A8BD7EB3883F8F3B66EDA"
EXPECTED_FIXED_POOL_SHA256 = "FD285AFC67C011CE9778E36C5FEE8FA7EAECB933690AF346993B7677AF0E64CF"
MEDIUM_RELATIVE = PurePosixPath("outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz")
CHECKPOINT_RELATIVE = PurePosixPath("outputs/runs/20260904T150300Z-phk-v23-lf3-phase-latent-97a5b74/checkpoint-t0-step-1200.pt")
DEV_M_RELATIVE = PurePosixPath("outputs/runs/20260905T102817Z-phk-v23-lf4-interface-band-5dbde1d/checkpoint-dev-m-interface-band-mse-step-400.pt")
CONTRACT_RELATIVES = {
    role: PurePosixPath(f"configs/phk_v23/{role}_contract_lf6_event_frontier.json")
    for role in ("program", "method", "data", "decision")
}
REQUIRED_RUNTIME = frozenset({
    *(path.as_posix() for path in CONTRACT_RELATIVES.values()),
    "configs/phk_v23/lf6_write_allowlist_lock.json",
    "cloud/phk_v23_lf6_autodl/README.md",
    "cloud/phk_v23_lf6_autodl/preflight.py",
    "cloud/phk_v23_lf6_autodl/run.sh",
    "pinn_pcm_sci/phk_v23_lf6.py",
    "pinn_pcm_sci/phk_v23_lf6_qualification.py",
    "pinn_pcm_sci/phk_v23_lf5.py",
    "pinn_pcm_sci/phk_v23_lf4.py",
    "pinn_pcm_sci/phk_v23_lf3.py",
    "pinn_pcm_sci/phk_v23_lf2.py",
    "pinn_pcm_sci/phk_v23_lf1.py",
    "pinn_pcm_sci/phk_v23_lf0.py",
    "pinn_pcm_sci/phk_v22r_training.py",
    "tests/test_phk_v21_benchmark.py",
})
STREAM_IDENTITIES = {
    "PHK_V23_LF4_BASE_DRAWS_1201_1600": "3870D0C1411B3DF6E04C5BA316B3F0F77233D94A73A19E84523D81B62F692E4A",
    "PHK_V23_LF4_INTERFACE_BAND": "4DB1728CC543B1AB18BD3F74B83B29EBFE5F95624D98DAFEA615B0ECDC69DEC4",
    "PHK_V23_LF0_PHYSICS_BATCHES": "536E6706A0B68EBB1277A97F402D273AFA2EA1E0B27106F26CB4222B7EC05C53",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _array_sha256(name: str, array: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(array)
    shape = json.dumps(list(contiguous.shape), separators=(",", ":")).encode("ascii")
    payload = b"PHK_V23_LF6_ARRAY_V1\n" + name.encode("ascii") + b"\n" + contiguous.dtype.str.encode("ascii") + b"\n" + shape + b"\n" + contiguous.tobytes(order="C")
    return hashlib.sha256(payload).hexdigest().upper()


def _semantic_sha256(array_hashes: Mapping[str, str]) -> str:
    digest = hashlib.sha256(b"PHK_V23_LF6_MATERIALIZED_LEDGER_V1\n")
    for name, value in sorted(array_hashes.items()):
        digest.update(f"{name}={value.upper()}\n".encode("ascii"))
    return digest.hexdigest().upper()


def _read_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"LF6 expected JSON object: {path}")
    return payload


def _safe(root: Path, relative: str) -> Path:
    normalized = PurePosixPath(relative)
    if normalized.is_absolute() or ".." in normalized.parts:
        raise PermissionError("LF6 path escaped deployment root")
    exact = (root / Path(*normalized.parts)).resolve()
    exact.relative_to(root.resolve())
    return exact


def _record(root: Path, path: Path) -> dict[str, Any]:
    exact = path.resolve()
    return {"path": exact.relative_to(root.resolve()).as_posix(), "sha256": _sha256(exact), "size_bytes": exact.stat().st_size}


def _decode_step_hashes(array: np.ndarray) -> list[str]:
    raw: Iterable[Any] = array.reshape(-1).tolist()
    result: list[str] = []
    for item in raw:
        if isinstance(item, bytes):
            item = item.decode("ascii")
        value = str(item).upper()
        if not re.fullmatch(r"[0-9A-F]{64}", value):
            raise ValueError("LF6 invalid per-step SHA-256")
        result.append(value)
    if not result:
        raise ValueError("LF6 empty stream hash sequence")
    return result


def _fixed_pool_sha256(arrays: Mapping[str, np.ndarray]) -> str:
    digest = hashlib.sha256(b"PHK_V23_LF2_FIXED_REFERENCE_BLIND_FULL_W1_W4")
    for name in ("interior", "left", "right", "bottom", "top", "initial"):
        array = np.ascontiguousarray(arrays[f"fixed_{name}"], dtype=np.float64)
        digest.update(str(tuple(array.shape)).encode("ascii"))
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest().upper()


def _verify_streams(streams: Mapping[str, Any], arrays: Mapping[str, np.ndarray]) -> dict[str, Any]:
    definitions = (
        ("base_400_sha256", "PHK_V23_LF4_BASE_DRAWS_1201_1600", "base_batch_sha256", 400),
        ("spatial_400_sha256", "PHK_V23_LF4_INTERFACE_BAND", "spatial_batch_sha256", 400),
        ("P0_physics_1200_sha256", "PHK_V23_LF0_PHYSICS_BATCHES", "p0_batch_sha256", 1200),
    )
    verified: dict[str, Any] = {}
    for key, domain, array_name, expected_count in definitions:
        if array_name not in arrays:
            raise ValueError(f"LF6 missing per-step hash array: {array_name}")
        hashes = _decode_step_hashes(arrays[array_name])
        if len(hashes) != expected_count:
            raise ValueError(f"LF6 {domain} step count drift")
        rolling = hashlib.sha256(domain.encode("ascii"))
        for step_hash in hashes:
            rolling.update(bytes.fromhex(step_hash))
        actual = rolling.hexdigest().upper()
        recorded = str(streams.get(key, "")).upper()
        expected = STREAM_IDENTITIES[domain]
        if actual != recorded or actual != expected:
            raise ValueError(f"LF6 {domain} aggregate drift")
        verified[key] = {"domain_tag": domain, "step_count": len(hashes), "rolling_sha256": actual}
    fixed = _fixed_pool_sha256(arrays)
    if fixed != str(streams.get("fixed_blind_pool_sha256", "")).upper() or fixed != EXPECTED_FIXED_POOL_SHA256:
        raise ValueError("LF6 fixed blind pool aggregate drift")
    verified["fixed_blind_pool_sha256"] = fixed
    return verified


def _verify_ledger(*, root: Path, ledger_path: Path, ledger_manifest_path: Path, qualification: Mapping[str, Any]) -> dict[str, Any]:
    ledger = Path(ledger_path).resolve()
    ledger_manifest = Path(ledger_manifest_path).resolve()
    manifest = _read_object(ledger_manifest)
    if manifest.get("schema_id") != "phk-v23-lf6-materialized-ledger-manifest-v1" or manifest.get("task_id") != TASK_ID:
        raise ValueError("LF6 materialized ledger manifest identity drift")
    if manifest.get("runtime_sampling_permitted") is not False:
        raise PermissionError("LF6 materialized ledger permits remote sampling")
    ledger_record = manifest.get("ledger")
    if not isinstance(ledger_record, Mapping) or dict(ledger_record) != _record(root, ledger):
        raise ValueError("LF6 ledger file binding drift")
    qualification_record = qualification.get("ledger")
    if not isinstance(qualification_record, Mapping):
        raise ValueError("LF6 qualification lacks ledger binding")
    for key, actual in (
        ("path", ledger.relative_to(root.resolve()).as_posix()),
        ("sha256", _sha256(ledger)),
        ("size_bytes", ledger.stat().st_size),
        ("manifest_path", ledger_manifest.relative_to(root.resolve()).as_posix()),
        ("manifest_sha256", _sha256(ledger_manifest)),
        ("semantic_sha256", str(manifest.get("semantic_sha256", "")).upper()),
    ):
        if qualification_record.get(key) != actual:
            raise ValueError(f"LF6 qualification ledger drift: {key}")

    array_records = manifest.get("arrays")
    streams = manifest.get("streams")
    if not isinstance(array_records, Mapping) or not isinstance(streams, Mapping):
        raise ValueError("LF6 ledger manifest lacks arrays or streams")
    with np.load(ledger, allow_pickle=False) as payload:
        if set(payload.files) != set(array_records):
            raise ValueError("LF6 ledger NPZ key set drift")
        arrays = {name: np.asarray(payload[name]) for name in payload.files}
    array_hashes: dict[str, str] = {}
    for name, array in arrays.items():
        record = array_records[name]
        if not isinstance(record, Mapping):
            raise ValueError(f"LF6 malformed array record: {name}")
        digest = _array_sha256(name, array)
        if list(array.shape) != list(record.get("shape", [])) or array.dtype.str != record.get("dtype") or digest != str(record.get("sha256", "")).upper():
            raise ValueError(f"LF6 ledger array drift: {name}")
        array_hashes[name] = digest
    semantic = _semantic_sha256(array_hashes)
    if semantic != str(manifest.get("semantic_sha256", "")).upper():
        raise ValueError("LF6 ledger semantic aggregate drift")
    if qualification_record.get("arrays") != array_records or qualification_record.get("streams") != streams:
        raise ValueError("LF6 qualification per-array or stream binding drift")
    verified_streams = _verify_streams(streams, arrays)
    return {"ledger": _record(root, ledger), "ledger_manifest": _record(root, ledger_manifest), "semantic_sha256": semantic, "array_count": len(arrays), "streams": verified_streams}


def _forbidden(root: Path, allowed_relatives: set[str]) -> list[str]:
    result: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.resolve().relative_to(root.resolve()).as_posix()
        if relative in allowed_relatives:
            continue
        lower = relative.lower()
        parts = PurePosixPath(lower).parts
        if (
            path.suffix.lower() in {".npz", ".pt"}
            or "nominal-fine" in lower
            or "nominal-extra-fine" in lower
            or "lf-only" in lower
            or any("stress" in part for part in parts)
            or "evaluator" in path.name.lower()
            or "evaluation" in path.name.lower()
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
            tokens = [item.decode(errors="replace") for item in (candidate / "cmdline").read_bytes().split(b"\0") if item]
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if "pinn_pcm_sci.phk_v23_lf6" in tokens:
            matches.append(f"pid:{candidate.name}")
    return sorted(matches)


def _validate_checkpoint_metadata(path: Path, *, role: str) -> dict[str, Any]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if role == "initial_checkpoint":
        metadata = payload.get("lf3", {})
        valid = metadata.get("schema_id") == "phk-v23-lf3-checkpoint-metadata-v1" and int(metadata.get("global_optimizer_step", -1)) == 1200
    else:
        metadata = payload.get("lf4", {})
        valid = (
            metadata.get("schema_id") == "phk-v23-lf4-checkpoint-metadata-v1"
            and metadata.get("role") == "DEV_M_INTERFACE_BAND_MSE"
            and int(metadata.get("optimizer_update", -1)) == 400
            and str(metadata.get("parent_checkpoint_sha256", "")).upper() == EXPECTED_INITIAL_SHA256
            and metadata.get("stress_read") is False
        )
    if not valid or "model_state_dict" not in payload:
        raise PermissionError(f"LF6 {role} checkpoint metadata drift")
    return {"schema_id": metadata.get("schema_id"), "role": metadata.get("role", metadata.get("stage")), "optimizer_update": metadata.get("optimizer_update", metadata.get("global_optimizer_step"))}


def _manifest(root: Path, source_identity: str) -> dict[str, Any]:
    manifest = _read_object(root / "cloud/phk_v23_lf6_autodl/deployed-source-manifest.json")
    if (
        manifest.get("schema_id") != "phk-v23-lf6-deployed-source-manifest-v1"
        or manifest.get("task_id") != TASK_ID
        or manifest.get("identity_definition") != "SHA256_OF_BASE_COMMIT_AND_SORTED_SOURCE_AND_INPUT_SHA_LINES"
        or manifest.get("source_identity") != source_identity
    ):
        raise ValueError("LF6 deployment manifest identity drift")
    files = manifest.get("files")
    inputs = manifest.get("materialized_inputs")
    if not isinstance(files, Mapping) or not isinstance(inputs, Mapping) or REQUIRED_RUNTIME.difference(files):
        raise ValueError("LF6 runtime closure incomplete")
    source_records: list[tuple[str, str]] = []
    for relative, expected in sorted(files.items()):
        exact = _safe(root, relative)
        actual = _sha256(exact) if exact.is_file() else None
        if actual != str(expected).upper():
            raise ValueError(f"LF6 deployed source drift: {relative}")
        source_records.append((relative, actual))
    input_records: list[tuple[str, str]] = []
    for role, binding in sorted(inputs.items()):
        if not isinstance(binding, Mapping):
            raise ValueError(f"LF6 malformed input binding: {role}")
        exact = _safe(root, str(binding.get("path", "")))
        if not exact.is_file() or _record(root, exact) != dict(binding):
            raise ValueError(f"LF6 deployed input drift: {role}")
        input_records.append((role, _sha256(exact)))
    lines = [f"base_commit={str(manifest['base_commit']).upper()}\n"]
    lines.extend(f"source:{path}={digest}\n" for path, digest in source_records)
    lines.extend(f"input:{role}={digest}\n" for role, digest in input_records)
    aggregate = hashlib.sha256("".join(lines).encode("ascii")).hexdigest().upper()
    if source_identity != "LF6-BUNDLE-" + aggregate:
        raise ValueError("LF6 aggregate deployment identity drift")
    return manifest


def run_preflight(
    *,
    source_identity: str,
    deployment_root: Path,
    medium_carrier: Path,
    initial_checkpoint: Path,
    materialized_ledger: Path,
    ledger_manifest: Path,
    cpu_qualification: Path,
    dev_m_checkpoint: Path | None,
    allow_dev_m_fallback_input: bool,
    cuda_probe: Any = None,
    pythonpath: str | None = None,
) -> dict[str, Any]:
    root = ROOT.resolve()
    if not Path(deployment_root).is_absolute() or Path(deployment_root).resolve() != root:
        raise ValueError("LF6 deployment root mismatch")
    entries = (os.environ.get("PYTHONPATH", "") if pythonpath is None else pythonpath).split(os.pathsep)
    if root not in [Path(entry).resolve() for entry in entries if Path(entry).is_absolute()]:
        raise RuntimeError("LF6 absolute deployment root absent from PYTHONPATH")
    manifest = _manifest(root, source_identity)
    dev_record = manifest.get("dev_m_fallback_input", {})
    if bool(dev_record.get("included")) != bool(allow_dev_m_fallback_input) or bool(dev_record.get("operator_asserted_authorized")) != bool(allow_dev_m_fallback_input):
        raise PermissionError("LF6 DEV-M fallback authorization identity drift")
    supplied = {
        "medium": (Path(medium_carrier).resolve(), MEDIUM_RELATIVE),
        "initial_checkpoint": (Path(initial_checkpoint).resolve(), CHECKPOINT_RELATIVE),
        "cpu_qualification": (Path(cpu_qualification).resolve(), PurePosixPath(str(manifest["materialized_inputs"]["cpu_qualification"]["path"]))),
        "ledger": (Path(materialized_ledger).resolve(), PurePosixPath(str(manifest["materialized_inputs"]["ledger"]["path"]))),
        "ledger_manifest": (Path(ledger_manifest).resolve(), PurePosixPath(str(manifest["materialized_inputs"]["ledger_manifest"]["path"]))),
    }
    if allow_dev_m_fallback_input:
        if dev_m_checkpoint is None:
            raise PermissionError("LF6 authorized DEV-M fallback checkpoint absent")
        supplied["dev_m_fallback_checkpoint"] = (Path(dev_m_checkpoint).resolve(), DEV_M_RELATIVE)
    elif dev_m_checkpoint is not None:
        raise PermissionError("LF6 unauthorized DEV-M fallback checkpoint supplied")
    for role, (exact, relative) in supplied.items():
        required = (root / Path(*relative.parts)).resolve()
        binding = manifest["materialized_inputs"].get(role)
        if exact != required or not exact.is_file() or not isinstance(binding, Mapping) or _record(root, exact) != dict(binding):
            raise PermissionError(f"LF6 exact deployed input drift: {role}")

    qualification = _read_object(Path(cpu_qualification))
    if (
        qualification.get("schema_id") != "phk-v23-lf6-cpu-qualification-v1"
        or qualification.get("task_id") != TASK_ID
        or qualification.get("status") != "LF6_CPU_F_QUALIFICATION_PASS"
        or qualification.get("gpu_execution_authorized_by_cpu_gate") is not True
    ):
        raise PermissionError("LF6 CPU-F qualification invalid")
    ledger_report = _verify_ledger(root=root, ledger_path=Path(materialized_ledger), ledger_manifest_path=Path(ledger_manifest), qualification=qualification)
    if ledger_report["semantic_sha256"] != str(manifest.get("ledger_semantic_sha256", "")).upper():
        raise ValueError("LF6 deployment ledger semantic identity drift")
    data = _read_object(root / Path(*CONTRACT_RELATIVES["data"].parts))
    if _sha256(Path(medium_carrier)) != str(data["training_source"]["sha256"]).upper() or _sha256(Path(initial_checkpoint)) != str(data["initial_checkpoint"]["sha256"]).upper():
        raise PermissionError("LF6 data-contract source drift")
    contract_identity = {
        role: {"path": relative.as_posix(), "sha256": _sha256(root / Path(*relative.parts))}
        for role, relative in CONTRACT_RELATIVES.items()
    }
    if qualification.get("contracts") != contract_identity:
        raise PermissionError("LF6 qualification contract identity drift")
    ledger_binding = data.get("materialized_ledger", {})
    ledger_manifest_payload = _read_object(Path(ledger_manifest))
    expected_ledger_binding = {
        "path": Path(materialized_ledger).resolve().relative_to(root).as_posix(),
        "manifest_path": Path(ledger_manifest).resolve().relative_to(root).as_posix(),
        "file_sha256": _sha256(Path(materialized_ledger)),
        "manifest_sha256": _sha256(Path(ledger_manifest)),
        "semantic_sha256": ledger_report["semantic_sha256"],
        "frontier_endpoint_sha256": str(ledger_manifest_payload.get("frontier_endpoint_sha256", "")).upper(),
        "uniform_endpoint_sha256": str(ledger_manifest_payload.get("uniform_endpoint_sha256", "")).upper(),
    }
    if any(str(ledger_binding.get(key, "")).upper() != str(value).upper() for key, value in expected_ledger_binding.items()):
        raise PermissionError("LF6 materialized ledger data-contract binding drift")
    checkpoint_metadata = {"initial_checkpoint": _validate_checkpoint_metadata(Path(initial_checkpoint), role="initial_checkpoint")}
    if allow_dev_m_fallback_input:
        if _sha256(Path(dev_m_checkpoint)) != EXPECTED_DEV_M_SHA256:
            raise PermissionError("LF6 exact DEV-M SHA drift")
        dev_binding = data.get("LF4_DEV_M", {})
        if str(dev_binding.get("path")) != DEV_M_RELATIVE.as_posix() or str(dev_binding.get("sha256", "")).upper() != EXPECTED_DEV_M_SHA256:
            raise PermissionError("LF6 exact DEV-M data-contract binding drift")
        checkpoint_metadata["dev_m_fallback_checkpoint"] = _validate_checkpoint_metadata(Path(dev_m_checkpoint), role="dev_m_fallback_checkpoint")

    lf6_source = (root / "pinn_pcm_sci/phk_v23_lf6.py").read_text(encoding="utf-8")
    forbidden_generators = [token for token in ("SobolEngine(", "BaseDevelopmentStream(", "BandStream(", "LF0PhysicsBatchStream(") if token in lf6_source]
    if forbidden_generators:
        raise PermissionError(f"LF6 remote runner contains runtime generator calls: {forbidden_generators}")
    allowed = {relative.as_posix() for _, relative in supplied.values()}
    forbidden = _forbidden(root, allowed)
    duplicates = _duplicates()
    if forbidden:
        raise PermissionError(f"LF6 forbidden cloud files present: {forbidden}")
    if duplicates:
        raise RuntimeError(f"duplicate LF6 training process: {duplicates}")
    cuda = torch.cuda if cuda_probe is None else cuda_probe
    if not cuda.is_available() or cuda.get_device_name(0) != EXPECTED_GPU:
        raise RuntimeError("LF6 exact V100 unavailable")
    return {
        "status": "REMOTE_LF6_PREFLIGHT_VALID",
        "task_id": TASK_ID,
        "source_identity": source_identity,
        "base_commit": manifest["base_commit"],
        "gpu_name": EXPECTED_GPU,
        "dtype": "FLOAT64",
        "seed": 17,
        "maximum_optimizer_updates": 2000,
        "maximum_scientific_trajectories": 3,
        "dev_m_fallback_input_authorized": bool(allow_dev_m_fallback_input),
        "ledger": ledger_report,
        "checkpoint_metadata": checkpoint_metadata,
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
    parser.add_argument("--medium-carrier", type=Path, required=True)
    parser.add_argument("--initial-checkpoint", type=Path, required=True)
    parser.add_argument("--materialized-ledger", type=Path, required=True)
    parser.add_argument("--ledger-manifest", type=Path, required=True)
    parser.add_argument("--cpu-qualification", type=Path, required=True)
    parser.add_argument("--dev-m-checkpoint", type=Path)
    parser.add_argument("--allow-dev-m-fallback-input", action="store_true")
    args = parser.parse_args()
    report = run_preflight(source_identity=args.source_identity, deployment_root=args.deployment_root, medium_carrier=args.medium_carrier, initial_checkpoint=args.initial_checkpoint, materialized_ledger=args.materialized_ledger, ledger_manifest=args.ledger_manifest, cpu_qualification=args.cpu_qualification, dev_m_checkpoint=args.dev_m_checkpoint, allow_dev_m_fallback_input=args.allow_dev_m_fallback_input)
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
