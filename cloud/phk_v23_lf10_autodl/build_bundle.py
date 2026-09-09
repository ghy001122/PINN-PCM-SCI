"""Build the activation-commit and reference-blind LF10 cloud bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "PHK_V23_LF10_EVENT_COMPETENCE_FEASIBLE_DIRECTION_AND_HEADLINE_EVIDENCE_REPLICATION_EXECUTE"
MANIFEST = ROOT / "cloud/phk_v23_lf10_autodl/deployed-source-manifest.json"
LOCK = ROOT / "configs/phk_v23/lf10_write_allowlist_lock.json"

MEDIUM = ROOT / "outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz"
LF3_T0_CHECKPOINT = ROOT / "outputs/runs/20260904T150300Z-phk-v23-lf3-phase-latent-97a5b74/checkpoint-t0-step-1200.pt"
DEV_R_CHECKPOINT = ROOT / "outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/dev_r/checkpoint.pt"
STRONG_LEDGER = ROOT / "outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/cpu/materialized_ledger.npz"
STRONG_LEDGER_MANIFEST = ROOT / "outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/cpu/materialized_ledger_manifest.json"
LF10_RAW = ROOT / "outputs/runs/20260909T101615Z-phk-v23-lf10-feasible-direction-replication"
LF10_LEDGER = LF10_RAW / "cpu/materialized_lf10_ledger.npz"
LF10_LEDGER_MANIFEST = LF10_RAW / "cpu/materialized_lf10_ledger_manifest.json"

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

LF10_CONTRACTS = {
    role: f"configs/phk_v23/{role}_contract_lf10_feasible_direction_replication.json"
    for role in ("program", "method", "data", "decision")
}

# Deliberately excludes deployed-source-manifest.json: it is generated only
# after every source byte below is frozen by the activation commit.
STATIC_FILES = (
    "configs/phk_v23/lf10_write_allowlist_lock.json",
    *LF10_CONTRACTS.values(),
    "cloud/phk_v23_lf10_autodl/README.md",
    "cloud/phk_v23_lf10_autodl/build_bundle.py",
    "cloud/phk_v23_lf10_autodl/preflight.py",
    "cloud/phk_v23_lf10_autodl/run.sh",
    "configs/phk_v23/program_contract_lf9_equation_routed_thermal_cv.json",
    "configs/phk_v23/method_contract_lf9_equation_routed_thermal_cv.json",
    "configs/phk_v23/data_contract_lf9_equation_routed_thermal_cv.json",
    "configs/phk_v23/decision_contract_lf9_equation_routed_thermal_cv.json",
    "configs/phk_v23/program_contract_lf8_competence_filter.json",
    "configs/phk_v23/method_contract_lf8_competence_filter.json",
    "configs/phk_v23/data_contract_lf8_competence_filter.json",
    "configs/phk_v23/decision_contract_lf8_competence_filter.json",
    "configs/phk_v23/program_contract_lf6_event_frontier.json",
    "configs/phk_v23/method_contract_lf6_event_frontier.json",
    "configs/phk_v23/data_contract_lf6_event_frontier.json",
    "configs/phk_v23/decision_contract_lf6_event_frontier.json",
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
    "pinn_pcm_sci/phk_v23_lf3.py",
    "pinn_pcm_sci/phk_v23_lf4.py",
    "pinn_pcm_sci/phk_v23_lf5.py",
    "pinn_pcm_sci/phk_v23_lf6.py",
    "pinn_pcm_sci/phk_v23_lf7.py",
    "pinn_pcm_sci/phk_v23_lf8.py",
    "pinn_pcm_sci/phk_v23_lf9.py",
    "pinn_pcm_sci/phk_v23_lf10.py",
    "pinn_pcm_sci/phk_v23_lf10_qualification.py",
    "tests/test_phk_v21_benchmark.py",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _record(path: Path) -> dict[str, Any]:
    exact = path.resolve()
    return {
        "path": exact.relative_to(ROOT.resolve()).as_posix(),
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


def _verify_same_batch_audit(qualification: Mapping[str, Any]) -> None:
    manifest = _read_object(LF10_LEDGER_MANIFEST)
    identity = _ledger_identity(qualification)
    with np.load(LF10_LEDGER, allow_pickle=False) as archive:
        if "audit_baselines" not in archive.files:
            raise PermissionError("LF10 same-batch audit_baselines array is absent")
        actual = _array_record("audit_baselines", np.asarray(archive["audit_baselines"]))
    if (
        actual != EXPECTED_AUDIT_BASELINES
        or manifest.get("arrays", {}).get("audit_baselines") != EXPECTED_AUDIT_BASELINES
        or identity.get("arrays", {}).get("audit_baselines") != EXPECTED_AUDIT_BASELINES
        or manifest.get("ledger") != _record(LF10_LEDGER)
    ):
        raise PermissionError("LF10 same-batch audit baseline identity drift")


def _read_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"LF10 expected JSON object: {path}")
    return payload


def _git(*args: str) -> bytes:
    completed = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)
    if completed.returncode:
        raise RuntimeError(completed.stderr.decode(errors="replace").strip())
    return completed.stdout


def _verify_activation_commit(base_commit: str, files: Sequence[str]) -> None:
    if len(base_commit) != 40 or any(c not in "0123456789abcdefABCDEF" for c in base_commit):
        raise ValueError("LF10 base commit must be a full Git object id")
    if _git("rev-parse", "HEAD").decode().strip().lower() != base_commit.lower():
        raise PermissionError("LF10 bundle must be built at the activation commit")
    for relative in files:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"LF10 committed source absent: {relative}")
        if _git("show", f"{base_commit}:{relative}") != path.read_bytes():
            raise PermissionError(f"LF10 source is not exact activation-commit content: {relative}")


def _locked_qualification_paths() -> tuple[Path, Path]:
    allowed = _read_object(LOCK).get("allowed_paths")
    if not isinstance(allowed, list):
        raise ValueError("LF10 lock lacks allowed_paths")
    artifacts = [p for p in allowed if p.endswith("-phk-v23-lf10-cpu-qualification.json") and "/artifacts/" in p]
    manifests = [p for p in allowed if p.endswith("-phk-v23-lf10-cpu-qualification.json") and "/manifests/" in p]
    if len(artifacts) != 1 or len(manifests) != 1:
        raise ValueError("LF10 lock must contain one CPU artifact and manifest")
    return (ROOT / artifacts[0]).resolve(), (ROOT / manifests[0]).resolve()


def _ledger_identity(qualification: Mapping[str, Any]) -> Mapping[str, Any]:
    identity = qualification.get("lf10_ledger")
    if not isinstance(identity, Mapping):
        identity = qualification.get("ledger")
    if not isinstance(identity, Mapping):
        raise PermissionError("LF10 qualification lacks the materialized-ledger identity")
    return identity


def _verify_frozen_inputs(qualification: Mapping[str, Any]) -> None:
    paths = {
        "medium": MEDIUM,
        "lf3_t0_checkpoint": LF3_T0_CHECKPOINT,
        "dev_r_checkpoint": DEV_R_CHECKPOINT,
        "strong_ledger": STRONG_LEDGER,
        "strong_ledger_manifest": STRONG_LEDGER_MANIFEST,
        "lf10_ledger": LF10_LEDGER,
        "lf10_ledger_manifest": LF10_LEDGER_MANIFEST,
    }
    for role, path in paths.items():
        if not path.is_file() or _sha256(path) != EXPECTED_SHA256[role]:
            raise PermissionError(f"LF10 frozen input absent or drifted: {role}")
    data = _read_object(ROOT / LF10_CONTRACTS["data"])
    strong = data.get("strong_ledger", {})
    lf10 = data.get("LF10_ledger", {})
    if (
        data.get("medium", {}).get("path") != MEDIUM.relative_to(ROOT).as_posix()
        or str(data.get("medium", {}).get("sha256", "")).upper() != EXPECTED_SHA256["medium"]
        or data.get("LF3_T0", {}).get("checkpoint_path") != LF3_T0_CHECKPOINT.relative_to(ROOT).as_posix()
        or str(data.get("LF3_T0", {}).get("checkpoint_sha256", "")).upper() != EXPECTED_SHA256["lf3_t0_checkpoint"]
        or data.get("DEV_R", {}).get("checkpoint_path") != DEV_R_CHECKPOINT.relative_to(ROOT).as_posix()
        or str(data.get("DEV_R", {}).get("checkpoint_sha256", "")).upper() != EXPECTED_SHA256["dev_r_checkpoint"]
        or strong.get("path") != STRONG_LEDGER.relative_to(ROOT).as_posix()
        or str(strong.get("file_sha256", "")).upper() != EXPECTED_SHA256["strong_ledger"]
        or strong.get("manifest_path") != STRONG_LEDGER_MANIFEST.relative_to(ROOT).as_posix()
        or str(strong.get("manifest_sha256", "")).upper() != EXPECTED_SHA256["strong_ledger_manifest"]
        or lf10.get("path") != LF10_LEDGER.relative_to(ROOT).as_posix()
        or lf10.get("manifest_path") != LF10_LEDGER_MANIFEST.relative_to(ROOT).as_posix()
        or lf10.get("runtime_sampling") is not False
    ):
        raise PermissionError("LF10 data-contract cloud-input binding drift")
    identity = _ledger_identity(qualification)
    expected = {
        "path": LF10_LEDGER.relative_to(ROOT).as_posix(),
        "manifest_path": LF10_LEDGER_MANIFEST.relative_to(ROOT).as_posix(),
        "sha256": EXPECTED_SHA256["lf10_ledger"],
        "manifest_sha256": EXPECTED_SHA256["lf10_ledger_manifest"],
    }
    if None in expected.values() or any(str(identity.get(key, "")).upper() != str(value).upper() for key, value in expected.items()):
        raise PermissionError("LF10 materialized-ledger binding drift")
    _verify_same_batch_audit(qualification)


def _verify_qualification(path: Path, manifest_path: Path) -> dict[str, Any]:
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
        raise PermissionError("LF10 bundle requires the exact passed zero-update qualification")
    _verify_frozen_inputs(payload)
    manifest = _read_object(manifest_path)
    compact = manifest.get("artifacts", {}).get("compact_qualification")
    if (
        manifest.get("schema_version") != "run-manifest-v1"
        or manifest.get("execution_status") != "COMPLETE"
        or manifest.get("gate_outcome") != payload.get("gate_outcome")
        or compact != f"artifacts/{path.name}#sha256={_sha256(path)}"
    ):
        raise PermissionError("LF10 CPU qualification manifest drift")
    return payload


def build(*, qualification_path: Path, qualification_manifest_path: Path,
          archive_path: Path, base_commit: str) -> dict[str, Any]:
    qualification = Path(qualification_path).resolve()
    qualification_manifest = Path(qualification_manifest_path).resolve()
    if (qualification, qualification_manifest) != _locked_qualification_paths():
        raise PermissionError("LF10 qualification inputs differ from locked paths")
    qualified = _verify_qualification(qualification, qualification_manifest)
    dynamic_sources = (
        qualification.relative_to(ROOT).as_posix(),
        qualification_manifest.relative_to(ROOT).as_posix(),
    )
    committed_files = (*STATIC_FILES, *dynamic_sources)
    if len(committed_files) != len(set(committed_files)):
        raise ValueError("LF10 bundle contains duplicate committed paths")
    _verify_activation_commit(base_commit, committed_files)
    source_bindings = {relative: _sha256(ROOT / relative) for relative in committed_files}
    materialized = {
        "medium": _record(MEDIUM),
        "lf3_t0_checkpoint": _record(LF3_T0_CHECKPOINT),
        "dev_r_checkpoint": _record(DEV_R_CHECKPOINT),
        "strong_ledger": _record(STRONG_LEDGER),
        "strong_ledger_manifest": _record(STRONG_LEDGER_MANIFEST),
        "lf10_ledger": _record(LF10_LEDGER),
        "lf10_ledger_manifest": _record(LF10_LEDGER_MANIFEST),
        "cpu_qualification": _record(qualification),
    }
    lines = [f"base_commit={base_commit.upper()}\n"]
    lines.extend(f"source:{path}={digest}\n" for path, digest in sorted(source_bindings.items()))
    lines.extend(f"input:{role}={record['sha256']}\n" for role, record in sorted(materialized.items()))
    identity = "LF10-BUNDLE-" + hashlib.sha256("".join(lines).encode("ascii")).hexdigest().upper()
    ledger = _ledger_identity(qualified)
    manifest = {
        "schema_id": "phk-v23-lf10-deployed-source-manifest-v1",
        "task_id": TASK_ID,
        "source_identity": identity,
        "identity_definition": "SHA256_OF_BASE_COMMIT_AND_SORTED_SOURCE_AND_INPUT_SHA_LINES",
        "base_commit": base_commit,
        "workspace_scope": "LF10_ACTIVATION_COMMIT_PLUS_EXACT_REFERENCE_BLIND_INPUTS_UNRELATED_DIRTY_EXCLUDED",
        "scientific_order": [
            "MATCHED_CTRL_PROJ_SCREENS",
            "CONDITIONAL_SELECTED_FULL_REFINEMENT",
            "INTERFACE_REPLICATION_STREAMS_23_29",
            "FORGETTING_REPLICATION_STREAMS_23_29",
        ],
        "arm_local_failure_isolation": True,
        "files": dict(sorted(source_bindings.items())),
        "materialized_inputs": materialized,
        "lf10_ledger_semantic_sha256": str(ledger.get("semantic_sha256", "")).upper(),
        "runtime_coordinate_generation": False,
        "medium_gradient_used_for_projection": True,
        "medium_gradient_used_in_physics_loss": False,
    }
    if MANIFEST.exists():
        raise FileExistsError(f"refusing to replace LF10 deployment manifest: {MANIFEST}")
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    archive = Path(archive_path).resolve()
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        raise FileExistsError(archive)
    members = [*(ROOT / relative for relative in committed_files), MEDIUM,
               LF3_T0_CHECKPOINT, DEV_R_CHECKPOINT, STRONG_LEDGER,
               STRONG_LEDGER_MANIFEST, LF10_LEDGER, LF10_LEDGER_MANIFEST, MANIFEST]
    with tarfile.open(archive, "w:gz") as handle:
        for member in members:
            handle.add(member, arcname=member.relative_to(ROOT).as_posix(), recursive=False)
    return {
        "source_identity": identity,
        "base_commit": base_commit,
        "manifest": str(MANIFEST),
        "manifest_sha256": _sha256(MANIFEST),
        "archive": str(archive),
        "archive_sha256": _sha256(archive),
        "committed_file_count": len(committed_files),
        "materialized_input_count": len(materialized),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--qualification-manifest", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--base-commit", required=True)
    args = parser.parse_args(argv)
    print(json.dumps(build(qualification_path=args.qualification,
                           qualification_manifest_path=args.qualification_manifest,
                           archive_path=args.archive, base_commit=args.base_commit), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
