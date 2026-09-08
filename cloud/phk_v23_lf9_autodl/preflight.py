"""Zero-update LF9 source, input, ledger, leakage, output, and V100 preflight."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
from typing import Any, Iterable, Mapping

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "PHK_V23_LF9_EQUATION_ROUTED_THERMAL_CONTROL_VOLUME_REFINEMENT_EXECUTE"
EXPECTED_GPU = "Tesla V100-PCIE-32GB"
EXPECTED_REMOTE_PARENT = "/root/autodl-tmp"

EXPECTED_MEDIUM_SHA256 = "18411D8066FACB31570774374A699ECE867981752ED9FEE25C34DF30D5D8802F"
EXPECTED_DEV_R_SHA256 = "7CFDD98E3A03BE29BBE587042967BD44E72D140AE7AC3396CB35E0CF5748F499"
EXPECTED_STRONG_LEDGER_SHA256 = "29E02DAF81A07BA4AF2B95B354126E75E9419AAE094E9486589455D31D2D6801"
EXPECTED_STRONG_MANIFEST_SHA256 = "3CFA268CFB22CF225ABB92BFD7F9F00353634AF7AFEE7AA607EC59FE4F4C8F90"
EXPECTED_STRONG_SEMANTIC_SHA256 = "0E2F680D33C4489F6092CB5D01E87483F7ECDA8290CD3E2C24EBDD06B3DA2B7F"
EXPECTED_PHYSICS_STREAM_SHA256 = "536E6706A0B68EBB1277A97F402D273AFA2EA1E0B27106F26CB4222B7EC05C53"
EXPECTED_FIXED_POOL_SHA256 = "FD285AFC67C011CE9778E36C5FEE8FA7EAECB933690AF346993B7677AF0E64CF"

MEDIUM_RELATIVE = PurePosixPath("outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz")
DEV_R_RELATIVE = PurePosixPath("outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/dev_r/checkpoint.pt")
STRONG_LEDGER_RELATIVE = PurePosixPath("outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/cpu/materialized_ledger.npz")
STRONG_MANIFEST_RELATIVE = PurePosixPath("outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/cpu/materialized_ledger_manifest.json")
CV_LEDGER_RELATIVE = PurePosixPath("outputs/runs/20260908T145333Z-phk-v23-lf9-equation-routed-thermal-cv/cpu/cv/materialized_cv_ledger.npz")
CV_MANIFEST_RELATIVE = PurePosixPath("outputs/runs/20260908T145333Z-phk-v23-lf9-equation-routed-thermal-cv/cpu/cv/materialized_cv_ledger_manifest.json")
CONTRACT_RELATIVES = {
    role: PurePosixPath(f"configs/phk_v23/{role}_contract_lf9_equation_routed_thermal_cv.json")
    for role in ("program", "method", "data", "decision")
}

REQUIRED_RUNTIME = frozenset({
    *(path.as_posix() for path in CONTRACT_RELATIVES.values()),
    "configs/phk_v23/lf9_write_allowlist_lock.json",
    "cloud/phk_v23_lf9_autodl/README.md",
    "cloud/phk_v23_lf9_autodl/preflight.py",
    "cloud/phk_v23_lf9_autodl/run.sh",
    "pinn_pcm_sci/phk_v23_lf9.py",
    "pinn_pcm_sci/phk_v23_lf8.py",
    "pinn_pcm_sci/phk_v23_lf7.py",
    "pinn_pcm_sci/phk_v23_lf6.py",
    "pinn_pcm_sci/phk_v22r_pinn.py",
    "pinn_pcm_sci/phk_v22r_prediction.py",
    "tests/test_phk_v21_benchmark.py",
})

STRONG_ARRAYS = frozenset({
    "p0_active_windows", "p0_batch_sha256", "p0_bottom", "p0_boundary_sha256",
    "p0_initial", "p0_initial_sha256", "p0_interior", "p0_interior_sha256",
    "p0_left", "p0_refreshed", "p0_right", "p0_top",
})


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _lf6_array_sha256(name: str, array: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(array)
    shape = json.dumps(list(contiguous.shape), separators=(",", ":")).encode("ascii")
    payload = (b"PHK_V23_LF6_ARRAY_V1\n" + name.encode("ascii") + b"\n"
               + contiguous.dtype.str.encode("ascii") + b"\n" + shape + b"\n"
               + contiguous.tobytes(order="C"))
    return hashlib.sha256(payload).hexdigest().upper()


def _lf6_semantic_sha256(array_hashes: Mapping[str, str]) -> str:
    digest = hashlib.sha256(b"PHK_V23_LF6_MATERIALIZED_LEDGER_V1\n")
    for name, value in sorted(array_hashes.items()):
        digest.update(f"{name}={value.upper()}\n".encode("ascii"))
    return digest.hexdigest().upper()


CV_DOMAIN = b"PHK_V23_LF9_MATERIALIZED_THERMAL_CV_LEDGER_V1"


def _array_sha256(name: str, array: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(array)
    digest = hashlib.sha256(name.encode("ascii"))
    digest.update(contiguous.dtype.str.encode("ascii"))
    digest.update(str(tuple(contiguous.shape)).encode("ascii"))
    digest.update(contiguous.tobytes(order="C"))
    return digest.hexdigest().upper()


def _semantic_sha256(arrays: Mapping[str, np.ndarray]) -> str:
    digest = hashlib.sha256(CV_DOMAIN)
    for name in sorted(arrays):
        digest.update(name.encode("ascii"))
        digest.update(bytes.fromhex(_array_sha256(name, arrays[name])))
    return digest.hexdigest().upper()


def _rolling_training_digest(bounds: np.ndarray, identity: np.ndarray) -> tuple[list[str], str]:
    hashes: list[str] = []
    rolling = hashlib.sha256(CV_DOMAIN + b"/TRAINING")
    for step in range(bounds.shape[0]):
        one = hashlib.sha256(CV_DOMAIN + b"/STEP")
        one.update(np.asarray(step + 1, dtype="<i8").tobytes())
        one.update(np.ascontiguousarray(identity[step], dtype="<i8").tobytes())
        one.update(np.ascontiguousarray(bounds[step], dtype="<f8").tobytes())
        value = one.hexdigest().upper()
        hashes.append(value)
        rolling.update(bytes.fromhex(value))
    return hashes, rolling.hexdigest().upper()


def _blind_digest(role: str, bounds: np.ndarray, identity: np.ndarray) -> str:
    digest = hashlib.sha256(CV_DOMAIN + b"/" + role.encode("ascii"))
    digest.update(np.ascontiguousarray(identity, dtype="<i8").tobytes())
    digest.update(np.ascontiguousarray(bounds, dtype="<f8").tobytes())
    return digest.hexdigest().upper()


def _fixed_pool_sha256(arrays: Mapping[str, np.ndarray]) -> str:
    digest = hashlib.sha256(b"PHK_V23_LF2_FIXED_REFERENCE_BLIND_FULL_W1_W4")
    for name in ("interior", "left", "right", "bottom", "top", "initial"):
        array = np.ascontiguousarray(arrays[f"fixed_{name}"], dtype=np.float64)
        digest.update(str(tuple(array.shape)).encode("ascii"))
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest().upper()


def _read_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"LF9 expected JSON object: {path}")
    return payload


def _safe(root: Path, relative: str) -> Path:
    normalized = PurePosixPath(relative)
    if normalized.is_absolute() or ".." in normalized.parts:
        raise PermissionError("LF9 path escaped deployment root")
    exact = (root / Path(*normalized.parts)).resolve()
    exact.relative_to(root.resolve())
    return exact


def _record(root: Path, path: Path) -> dict[str, Any]:
    exact = path.resolve()
    return {"path": exact.relative_to(root.resolve()).as_posix(),
            "sha256": _sha256(exact), "size_bytes": exact.stat().st_size}


def _decode_hashes(array: np.ndarray) -> list[str]:
    raw: Iterable[Any] = array.reshape(-1).tolist()
    result: list[str] = []
    for item in raw:
        value = (item.decode("ascii") if isinstance(item, bytes) else str(item)).upper()
        if not re.fullmatch(r"[0-9A-F]{64}", value):
            raise ValueError("LF9 invalid per-step SHA-256")
        result.append(value)
    return result


def _verify_strong_ledger(root: Path, ledger_path: Path, manifest_path: Path) -> dict[str, Any]:
    ledger, ledger_manifest = ledger_path.resolve(), manifest_path.resolve()
    if _sha256(ledger) != EXPECTED_STRONG_LEDGER_SHA256 or _sha256(ledger_manifest) != EXPECTED_STRONG_MANIFEST_SHA256:
        raise PermissionError("LF9 strong ledger file or manifest hash drift")
    manifest = _read_object(ledger_manifest)
    if (manifest.get("schema_id") != "phk-v23-lf6-materialized-ledger-manifest-v1"
            or manifest.get("runtime_sampling_permitted") is not False
            or str(manifest.get("semantic_sha256", "")).upper() != EXPECTED_STRONG_SEMANTIC_SHA256
            or manifest.get("ledger") != _record(root, ledger)):
        raise PermissionError("LF9 strong ledger identity drift")
    records, streams = manifest.get("arrays"), manifest.get("streams")
    if not isinstance(records, Mapping) or not isinstance(streams, Mapping):
        raise ValueError("LF9 strong ledger manifest lacks arrays or streams")
    with np.load(ledger, allow_pickle=False) as payload:
        if set(payload.files) != set(records):
            raise ValueError("LF9 strong ledger NPZ key set drift")
        arrays = {name: np.asarray(payload[name]) for name in payload.files}
    if STRONG_ARRAYS.difference(arrays):
        raise ValueError("LF9 strong ledger lacks required P0 arrays")
    hashes: dict[str, str] = {}
    for name, array in arrays.items():
        record = records[name]
        digest = _lf6_array_sha256(name, array)
        if (not isinstance(record, Mapping) or list(array.shape) != list(record.get("shape", []))
                or array.dtype.str != record.get("dtype") or digest != str(record.get("sha256", "")).upper()):
            raise ValueError(f"LF9 strong ledger array drift: {name}")
        hashes[name] = digest
    if _lf6_semantic_sha256(hashes) != EXPECTED_STRONG_SEMANTIC_SHA256:
        raise ValueError("LF9 strong ledger semantic aggregate drift")
    for name in STRONG_ARRAYS:
        if arrays[name].shape[0] != 1200:
            raise ValueError(f"LF9 {name} does not contain all 1200 steps")
    step_hashes = _decode_hashes(arrays["p0_batch_sha256"])
    rolling = hashlib.sha256(b"PHK_V23_LF0_PHYSICS_BATCHES")
    for value in step_hashes:
        rolling.update(bytes.fromhex(value))
    physics = rolling.hexdigest().upper()
    fixed = _fixed_pool_sha256(arrays)
    if (len(step_hashes) != 1200 or physics != EXPECTED_PHYSICS_STREAM_SHA256
            or str(streams.get("P0_physics_1200_sha256", "")).upper() != physics
            or fixed != EXPECTED_FIXED_POOL_SHA256
            or str(streams.get("fixed_blind_pool_sha256", "")).upper() != fixed):
        raise ValueError("LF9 strong physics stream or fixed-blind pool drift")
    return {"ledger": _record(root, ledger), "ledger_manifest": _record(root, ledger_manifest),
            "array_count": len(arrays), "p0_step_count": 1200,
            "p0_physics_rolling_sha256": physics, "fixed_blind_pool_sha256": fixed,
            "semantic_sha256": EXPECTED_STRONG_SEMANTIC_SHA256}


def _verify_cv_ledger(root: Path, ledger_path: Path, manifest_path: Path,
                      qualification: Mapping[str, Any]) -> dict[str, Any]:
    cv = qualification.get("cv_ledger", {})
    if not isinstance(cv, Mapping):
        raise ValueError("LF9 qualification lacks CV ledger binding")
    ledger, ledger_manifest = ledger_path.resolve(), manifest_path.resolve()
    if (_sha256(ledger) != str(cv.get("file_sha256", "")).upper()
            or _sha256(ledger_manifest) != str(cv.get("manifest_sha256", "")).upper()):
        raise PermissionError("LF9 CV ledger file or manifest hash drift")
    manifest = _read_object(ledger_manifest)
    if (manifest.get("schema_id") != "phk-v23-lf9-cv-ledger-manifest-v1"
            or manifest.get("runtime_sampling_permitted") is not False
            or str(manifest.get("semantic_sha256", "")).upper() != str(cv.get("semantic_sha256", "")).upper()
            or manifest.get("ledger") != _record(root, ledger)):
        raise PermissionError("LF9 CV ledger identity drift")
    records = manifest.get("arrays")
    if not isinstance(records, Mapping) or not records:
        raise ValueError("LF9 CV ledger manifest lacks arrays")
    with np.load(ledger, allow_pickle=False) as payload:
        if set(payload.files) != set(records):
            raise ValueError("LF9 CV ledger NPZ key set drift")
        arrays = {name: np.asarray(payload[name]) for name in payload.files}
    hashes: dict[str, str] = {}
    for name, array in arrays.items():
        record = records[name]
        digest = _array_sha256(name, array)
        if (not isinstance(record, Mapping) or list(array.shape) != list(record.get("shape", []))
                or array.dtype.str != record.get("dtype") or digest != str(record.get("sha256", "")).upper()):
            raise ValueError(f"LF9 CV ledger array drift: {name}")
        hashes[name] = digest
    expected_arrays = {
        "training_bounds", "training_identity", "training_step_sha256",
        "one_cell_blind_bounds", "one_cell_blind_identity",
        "two_by_two_blind_bounds", "two_by_two_blind_identity",
    }
    if set(arrays) != expected_arrays:
        raise ValueError("LF9 CV ledger required array set drift")
    semantic = _semantic_sha256(arrays)
    if semantic != str(cv.get("semantic_sha256", "")).upper():
        raise ValueError("LF9 CV ledger semantic aggregate drift")
    if cv.get("array_sha256") != hashes:
        raise ValueError("LF9 qualification CV array identity drift")
    step_hashes, training_rolling = _rolling_training_digest(
        arrays["training_bounds"], arrays["training_identity"]
    )
    stored_step_hashes = _decode_hashes(arrays["training_step_sha256"])
    one_cell = _blind_digest(
        "ONE_CELL_BLIND", arrays["one_cell_blind_bounds"], arrays["one_cell_blind_identity"]
    )
    two_by_two = _blind_digest(
        "TWO_BY_TWO_BLIND", arrays["two_by_two_blind_bounds"], arrays["two_by_two_blind_identity"]
    )
    if stored_step_hashes != step_hashes:
        raise ValueError("LF9 CV per-step training identity drift")
    streams = manifest.get("streams", {})
    expected_streams = {
        "training_step_sha256": step_hashes,
        "training_rolling_sha256": training_rolling,
        "one_cell_blind_sha256": one_cell,
        "two_by_two_blind_sha256": two_by_two,
    }
    if not isinstance(streams, Mapping) or streams != expected_streams:
        raise ValueError("LF9 CV stream identity drift")
    for key in ("training_rolling_sha256", "one_cell_blind_sha256", "two_by_two_blind_sha256"):
        if str(cv.get(key, "")).upper() != expected_streams[key]:
            raise ValueError(f"LF9 qualification CV stream drift: {key}")
    counts = qualification.get("counts", {})
    if manifest.get("counts") != counts:
        raise ValueError("LF9 CV ledger count binding drift")
    required_counts = {
        "training_steps": 1200,
        "patches_per_step": 16,
        "training_slabs": 19200,
        "one_cell_blind_count": 192,
        "two_by_two_blind_count": 192,
    }
    if not isinstance(counts, Mapping) or any(int(counts.get(key, -1)) != value for key, value in required_counts.items()):
        raise ValueError("LF9 CV ledger does not contain the frozen training/blind program")
    disjoint = qualification.get("disjoint_checks", {})
    if (not isinstance(disjoint, Mapping) or not disjoint
            or not all(value is True for value in disjoint.values())
            or manifest.get("disjoint_checks") != disjoint):
        raise ValueError("LF9 CV training/blind split is not disjoint")
    # The 1,200 per-step digests were recomputed and compared above.  Keep the
    # remote preflight report compact; the full list remains in the immutable
    # materialized manifest and ledger.
    compact_streams = {
        "training_rolling_sha256": training_rolling,
        "one_cell_blind_sha256": one_cell,
        "two_by_two_blind_sha256": two_by_two,
        "training_step_count": len(step_hashes),
    }
    return {"ledger": _record(root, ledger), "ledger_manifest": _record(root, ledger_manifest),
            "array_count": len(arrays), "semantic_sha256": semantic,
            "streams": compact_streams, "counts": dict(counts), "disjoint_checks": dict(disjoint)}


def _verify_output_root(deployment_root: Path, output_root: Path) -> dict[str, Any]:
    deployment, output = deployment_root.resolve(), Path(output_root)
    if not output.is_absolute():
        raise PermissionError("LF9 output root must be absolute")
    exact = output.resolve()
    if exact.parent.as_posix() != EXPECTED_REMOTE_PARENT or not exact.name.startswith("lf9-run-"):
        raise PermissionError("LF9 output root identity drift")
    if exact == deployment or deployment in exact.parents:
        raise PermissionError("LF9 output root must remain outside deployment root")
    if not exact.is_dir() or any(exact.iterdir()):
        raise RuntimeError("LF9 output root must exist and be empty")
    return {"path": exact.as_posix(), "exists": True, "empty": True}


def _forbidden(root: Path, allowed_relatives: set[str]) -> list[str]:
    result: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.resolve().relative_to(root.resolve()).as_posix()
        if relative in allowed_relatives:
            continue
        lower, parts = relative.lower(), PurePosixPath(relative.lower()).parts
        if (path.suffix.lower() in {".npz", ".pt"} or "nominal-fine" in lower
                or "nominal-extra-fine" in lower or "lf-only" in lower
                or "lf_only" in lower or any("stress" in part for part in parts)
                or "evaluator" in path.name.lower() or "evaluation" in path.name.lower()):
            result.append(relative)
    return sorted(result)


def _duplicates() -> list[str]:
    if os.name != "posix" or not Path("/proc").is_dir():
        return []
    result: list[str] = []
    for candidate in Path("/proc").iterdir():
        if not candidate.name.isdigit() or int(candidate.name) == os.getpid():
            continue
        try:
            tokens = [x.decode(errors="replace") for x in (candidate / "cmdline").read_bytes().split(b"\0") if x]
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if "pinn_pcm_sci.phk_v23_lf9" in tokens:
            result.append(f"pid:{candidate.name}")
    return sorted(result)


def _verify_gpu(cuda_probe: Any = None) -> str:
    cuda = torch.cuda if cuda_probe is None else cuda_probe
    if not cuda.is_available() or cuda.get_device_name(0) != EXPECTED_GPU:
        raise RuntimeError("LF9 exact V100 unavailable")
    return EXPECTED_GPU


def _validate_dev_r_checkpoint(path: Path) -> dict[str, Any]:
    if _sha256(path) != EXPECTED_DEV_R_SHA256:
        raise PermissionError("LF9 exact DEV-R checkpoint SHA drift")
    payload = torch.load(path, map_location="cpu", weights_only=False)
    metadata = payload.get("lf6", {})
    if (metadata.get("schema_id") != "phk-v23-lf6-checkpoint-metadata-v1"
            or metadata.get("role") != "DEV_R_EVENT_FRONTIER_RANK_BAND"
            or int(metadata.get("optimizer_update", -1)) != 400
            or metadata.get("runtime_sampling_used") is not False
            or metadata.get("stress_read") is not False
            or "model_state_dict" not in payload):
        raise PermissionError("LF9 DEV-R checkpoint metadata drift")
    return {"schema_id": metadata["schema_id"], "role": metadata["role"],
            "optimizer_update": metadata["optimizer_update"], "sha256": EXPECTED_DEV_R_SHA256}


def _manifest(root: Path, source_identity: str) -> dict[str, Any]:
    manifest = _read_object(root / "cloud/phk_v23_lf9_autodl/deployed-source-manifest.json")
    order = ["ER_S_ROUTED_STRONG_SCREEN", "ER_CV_ROUTED_THERMAL_CONTROL_VOLUME_SCREEN",
             "CONDITIONAL_SELECTED_FULL_REFINEMENT", "CONDITIONAL_MATCHED_NO_FILTER_CONTROL"]
    if (manifest.get("schema_id") != "phk-v23-lf9-deployed-source-manifest-v1"
            or manifest.get("task_id") != TASK_ID or manifest.get("source_identity") != source_identity
            or manifest.get("identity_definition") != "SHA256_OF_BASE_COMMIT_AND_SORTED_SOURCE_AND_INPUT_SHA_LINES"
            or manifest.get("scientific_order") != order
            or manifest.get("arm_local_failure_isolation") is not True
            or manifest.get("runtime_coordinate_generation") is not False):
        raise ValueError("LF9 deployment manifest identity drift")
    files, inputs = manifest.get("files"), manifest.get("materialized_inputs")
    roles = {"medium", "dev_r_checkpoint", "strong_ledger", "strong_ledger_manifest",
             "cv_ledger", "cv_ledger_manifest", "cpu_qualification"}
    if (not isinstance(files, Mapping) or not isinstance(inputs, Mapping)
            or REQUIRED_RUNTIME.difference(files) or set(inputs) != roles):
        raise ValueError("LF9 deployment closure or input boundary drift")
    source_records, input_records = [], []
    for relative, expected in sorted(files.items()):
        exact = _safe(root, relative)
        actual = _sha256(exact) if exact.is_file() else None
        if actual != str(expected).upper():
            raise ValueError(f"LF9 deployed source drift: {relative}")
        source_records.append((relative, actual))
    for role, binding in sorted(inputs.items()):
        if not isinstance(binding, Mapping):
            raise ValueError(f"LF9 malformed input binding: {role}")
        exact = _safe(root, str(binding.get("path", "")))
        if not exact.is_file() or _record(root, exact) != dict(binding):
            raise ValueError(f"LF9 deployed input drift: {role}")
        input_records.append((role, _sha256(exact)))
    lines = [f"base_commit={str(manifest['base_commit']).upper()}\n"]
    lines.extend(f"source:{path}={digest}\n" for path, digest in source_records)
    lines.extend(f"input:{role}={digest}\n" for role, digest in input_records)
    if source_identity != "LF9-BUNDLE-" + hashlib.sha256("".join(lines).encode("ascii")).hexdigest().upper():
        raise ValueError("LF9 aggregate deployment identity drift")
    return manifest


def _verify_qualification(path: Path, root: Path) -> dict[str, Any]:
    payload = _read_object(path)
    if (payload.get("schema_id") != "phk-v23-lf9-cpu-qualification-v1"
            or payload.get("task_id") != TASK_ID
            or payload.get("gate_outcome") != "LF9_CPU_QUALIFICATION_PASS"
            or payload.get("gpu_execution_authorized_by_cpu_gate") is not True
            or int(payload.get("scientific_optimizer_updates", -1)) != 0
            or not payload.get("checks")
            or not all(value is True for value in payload["checks"].values())
            or not payload.get("disjoint_checks")
            or not all(value is True for value in payload["disjoint_checks"].values())):
        raise PermissionError("LF9 CPU qualification invalid")
    contracts = {role: {"path": relative.as_posix(),
                        "sha256": _sha256(root / Path(*relative.parts))}
                 for role, relative in CONTRACT_RELATIVES.items()}
    if payload.get("contracts") != contracts:
        raise PermissionError("LF9 CPU qualification contract identity drift")
    normalization = payload.get("cv_normalization", {})
    values = [float(normalization.get(key, float("nan"))) for key in ("r_cv0_rms", "L_T_strong0", "s_cv")]
    if not all(math.isfinite(value) and value > 0.0 for value in values):
        raise PermissionError("LF9 CPU qualification CV normalization invalid")
    return payload


def run_preflight(*, source_identity: str, deployment_root: Path, output_root: Path,
                  medium_carrier: Path, dev_r_checkpoint: Path, strong_ledger: Path,
                  strong_ledger_manifest: Path, cv_ledger: Path, cv_ledger_manifest: Path,
                  cpu_qualification: Path, cuda_probe: Any = None,
                  pythonpath: str | None = None) -> dict[str, Any]:
    root = ROOT.resolve()
    if not Path(deployment_root).is_absolute() or Path(deployment_root).resolve() != root:
        raise ValueError("LF9 deployment root mismatch")
    entries = (os.environ.get("PYTHONPATH", "") if pythonpath is None else pythonpath).split(os.pathsep)
    if root not in [Path(entry).resolve() for entry in entries if Path(entry).is_absolute()]:
        raise RuntimeError("LF9 absolute deployment root absent from PYTHONPATH")
    manifest = _manifest(root, source_identity)
    expected = {
        "medium": (Path(medium_carrier).resolve(), MEDIUM_RELATIVE, EXPECTED_MEDIUM_SHA256),
        "dev_r_checkpoint": (Path(dev_r_checkpoint).resolve(), DEV_R_RELATIVE, EXPECTED_DEV_R_SHA256),
        "strong_ledger": (Path(strong_ledger).resolve(), STRONG_LEDGER_RELATIVE, EXPECTED_STRONG_LEDGER_SHA256),
        "strong_ledger_manifest": (Path(strong_ledger_manifest).resolve(), STRONG_MANIFEST_RELATIVE, EXPECTED_STRONG_MANIFEST_SHA256),
        "cv_ledger": (Path(cv_ledger).resolve(), CV_LEDGER_RELATIVE,
                      str(manifest["materialized_inputs"]["cv_ledger"]["sha256"]).upper()),
        "cv_ledger_manifest": (Path(cv_ledger_manifest).resolve(), CV_MANIFEST_RELATIVE,
                               str(manifest["materialized_inputs"]["cv_ledger_manifest"]["sha256"]).upper()),
    }
    qrel = PurePosixPath(str(manifest["materialized_inputs"]["cpu_qualification"]["path"]))
    expected["cpu_qualification"] = (Path(cpu_qualification).resolve(), qrel,
                                     str(manifest["materialized_inputs"]["cpu_qualification"]["sha256"]).upper())
    for role, (exact, relative, digest) in expected.items():
        required, binding = (root / Path(*relative.parts)).resolve(), manifest["materialized_inputs"].get(role)
        if (exact != required or not exact.is_file() or _sha256(exact) != digest
                or not isinstance(binding, Mapping) or _record(root, exact) != dict(binding)):
            raise PermissionError(f"LF9 exact deployed input drift: {role}")
    qualification = _verify_qualification(Path(cpu_qualification), root)
    strong = _verify_strong_ledger(root, Path(strong_ledger), Path(strong_ledger_manifest))
    cv = _verify_cv_ledger(root, Path(cv_ledger), Path(cv_ledger_manifest), qualification)
    if (str(manifest.get("strong_ledger_semantic_sha256", "")).upper() != strong["semantic_sha256"]
            or str(manifest.get("cv_ledger_semantic_sha256", "")).upper() != cv["semantic_sha256"]):
        raise ValueError("LF9 deployed ledger semantic identity drift")
    deployed_cv_streams = manifest.get("cv_stream_sha256", {})
    expected_deployed_streams = {
        "training": cv["streams"]["training_rolling_sha256"],
        "one_cell_blind": cv["streams"]["one_cell_blind_sha256"],
        "two_by_two_blind": cv["streams"]["two_by_two_blind_sha256"],
    }
    if deployed_cv_streams != expected_deployed_streams:
        raise ValueError("LF9 deployed CV stream identity drift")
    checkpoint = _validate_dev_r_checkpoint(Path(dev_r_checkpoint))
    runner = (root / "pinn_pcm_sci/phk_v23_lf9.py").read_text(encoding="utf-8")
    generators = [token for token in ("SobolEngine(", "LF0PhysicsBatchStream(",
                                       "PhkCollocationSampler(", "materialize_cv_ledger(") if token in runner]
    if generators:
        raise PermissionError(f"LF9 runner contains runtime coordinate generators: {generators}")
    output = _verify_output_root(root, Path(output_root))
    allowed = {relative.as_posix() for _, relative, _ in expected.values()}
    forbidden, duplicates = _forbidden(root, allowed), _duplicates()
    if forbidden:
        raise PermissionError(f"LF9 forbidden cloud files present: {forbidden}")
    if duplicates:
        raise RuntimeError(f"duplicate LF9 training process: {duplicates}")
    gpu_name = _verify_gpu(cuda_probe)
    return {"status": "REMOTE_LF9_PREFLIGHT_VALID", "task_id": TASK_ID,
            "source_identity": source_identity, "base_commit": manifest["base_commit"],
            "gpu_name": gpu_name, "dtype": "FLOAT64", "seed": 17,
            "scientific_order": manifest["scientific_order"], "mandatory_screens": 2,
            "arm_local_failure_isolation": True, "output_root": output,
            "strong_ledger": strong, "cv_ledger": cv, "checkpoint": checkpoint,
            "qualification_gate_outcome": qualification["gate_outcome"],
            "forbidden_cloud_files": [], "duplicate_training_processes": [],
            "runtime_coordinate_generation": False, "optimizer_constructed": False,
            "optimizer_updates": 0, "stress_fields_present": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-identity", required=True)
    parser.add_argument("--deployment-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--medium-carrier", type=Path, required=True)
    parser.add_argument("--dev-r-checkpoint", type=Path, required=True)
    parser.add_argument("--strong-ledger", type=Path, required=True)
    parser.add_argument("--strong-ledger-manifest", type=Path, required=True)
    parser.add_argument("--cv-ledger", type=Path, required=True)
    parser.add_argument("--cv-ledger-manifest", type=Path, required=True)
    parser.add_argument("--cpu-qualification", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run_preflight(source_identity=args.source_identity,
                                   deployment_root=args.deployment_root,
                                   output_root=args.output_root,
                                   medium_carrier=args.medium_carrier,
                                   dev_r_checkpoint=args.dev_r_checkpoint,
                                   strong_ledger=args.strong_ledger,
                                   strong_ledger_manifest=args.strong_ledger_manifest,
                                   cv_ledger=args.cv_ledger,
                                   cv_ledger_manifest=args.cv_ledger_manifest,
                                   cpu_qualification=args.cpu_qualification),
                     sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
