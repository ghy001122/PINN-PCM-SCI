"""Build the activation-commit and materialized-input LF9 cloud bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import subprocess
import tarfile
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "PHK_V23_LF9_EQUATION_ROUTED_THERMAL_CONTROL_VOLUME_REFINEMENT_EXECUTE"
MANIFEST = ROOT / "cloud/phk_v23_lf9_autodl/deployed-source-manifest.json"
LOCK = ROOT / "configs/phk_v23/lf9_write_allowlist_lock.json"

MEDIUM = ROOT / "outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz"
DEV_R_CHECKPOINT = ROOT / "outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/dev_r/checkpoint.pt"
STRONG_LEDGER = ROOT / "outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/cpu/materialized_ledger.npz"
STRONG_LEDGER_MANIFEST = ROOT / "outputs/runs/20260906T065434Z-phk-v23-lf6-event-frontier-pilot/cpu/materialized_ledger_manifest.json"
CV_LEDGER = ROOT / "outputs/runs/20260908T145333Z-phk-v23-lf9-equation-routed-thermal-cv/cpu/cv/materialized_cv_ledger.npz"
CV_LEDGER_MANIFEST = ROOT / "outputs/runs/20260908T145333Z-phk-v23-lf9-equation-routed-thermal-cv/cpu/cv/materialized_cv_ledger_manifest.json"

EXPECTED_MEDIUM_SHA256 = "18411D8066FACB31570774374A699ECE867981752ED9FEE25C34DF30D5D8802F"
EXPECTED_DEV_R_SHA256 = "7CFDD98E3A03BE29BBE587042967BD44E72D140AE7AC3396CB35E0CF5748F499"
EXPECTED_STRONG_LEDGER_SHA256 = "29E02DAF81A07BA4AF2B95B354126E75E9419AAE094E9486589455D31D2D6801"
EXPECTED_STRONG_MANIFEST_SHA256 = "3CFA268CFB22CF225ABB92BFD7F9F00353634AF7AFEE7AA607EC59FE4F4C8F90"
EXPECTED_STRONG_SEMANTIC_SHA256 = "0E2F680D33C4489F6092CB5D01E87483F7ECDA8290CD3E2C24EBDD06B3DA2B7F"
EXPECTED_PHYSICS_STREAM_SHA256 = "536E6706A0B68EBB1277A97F402D273AFA2EA1E0B27106F26CB4222B7EC05C53"
EXPECTED_FIXED_POOL_SHA256 = "FD285AFC67C011CE9778E36C5FEE8FA7EAECB933690AF346993B7677AF0E64CF"

LF9_CONTRACTS = {
    role: f"configs/phk_v23/{role}_contract_lf9_equation_routed_thermal_cv.json"
    for role in ("program", "method", "data", "decision")
}

# The deployment manifest is deliberately absent: it is generated only after
# the activation commit has frozen every source byte below.
STATIC_FILES = (
    "configs/phk_v23/lf9_write_allowlist_lock.json",
    "cloud/phk_v23_lf9_autodl/README.md",
    "cloud/phk_v23_lf9_autodl/build_bundle.py",
    "cloud/phk_v23_lf9_autodl/preflight.py",
    "cloud/phk_v23_lf9_autodl/run.sh",
    *LF9_CONTRACTS.values(),
    "configs/phk_v23/program_contract_lf8_competence_filter.json",
    "configs/phk_v23/method_contract_lf8_competence_filter.json",
    "configs/phk_v23/data_contract_lf8_competence_filter.json",
    "configs/phk_v23/decision_contract_lf8_competence_filter.json",
    "configs/phk_v23/program_contract_lf7_competence_filter.json",
    "configs/phk_v23/method_contract_lf7_competence_filter.json",
    "configs/phk_v23/data_contract_lf7_competence_filter.json",
    "configs/phk_v23/decision_contract_lf7_competence_filter.json",
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


def _read_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"LF9 expected JSON object: {path}")
    return payload


def _git(*args: str) -> bytes:
    completed = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)
    if completed.returncode:
        raise RuntimeError(completed.stderr.decode(errors="replace").strip())
    return completed.stdout


def _verify_activation_commit(base_commit: str, files: Sequence[str]) -> None:
    if len(base_commit) != 40 or any(c not in "0123456789abcdefABCDEF" for c in base_commit):
        raise ValueError("LF9 base commit must be a full Git object id")
    if _git("rev-parse", "HEAD").decode().strip().lower() != base_commit.lower():
        raise PermissionError("LF9 bundle must be built at the activation commit")
    for relative in files:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"LF9 committed source absent: {relative}")
        if _git("show", f"{base_commit}:{relative}") != path.read_bytes():
            raise PermissionError(f"LF9 source is not exact activation-commit content: {relative}")


def _locked_qualification_paths() -> tuple[Path, Path]:
    lock = _read_object(LOCK)
    allowed = lock.get("allowed_paths")
    if not isinstance(allowed, list):
        raise ValueError("LF9 lock lacks allowed_paths")
    artifacts = [p for p in allowed if p.endswith("-phk-v23-lf9-cpu-qualification.json") and "/artifacts/" in p]
    manifests = [p for p in allowed if p.endswith("-phk-v23-lf9-cpu-qualification.json") and "/manifests/" in p]
    if len(artifacts) != 1 or len(manifests) != 1:
        raise ValueError("LF9 lock must contain one CPU artifact and manifest")
    result = ((ROOT / artifacts[0]).resolve(), (ROOT / manifests[0]).resolve())
    for path in result:
        path.relative_to(ROOT.resolve())
    return result


def _verify_frozen_inputs() -> None:
    expected = {
        MEDIUM: EXPECTED_MEDIUM_SHA256,
        DEV_R_CHECKPOINT: EXPECTED_DEV_R_SHA256,
        STRONG_LEDGER: EXPECTED_STRONG_LEDGER_SHA256,
        STRONG_LEDGER_MANIFEST: EXPECTED_STRONG_MANIFEST_SHA256,
    }
    for path, digest in expected.items():
        if not path.is_file() or _sha256(path) != digest:
            raise PermissionError(f"LF9 frozen input absent or hash-drifted: {path}")
    manifest = _read_object(STRONG_LEDGER_MANIFEST)
    if (
        manifest.get("schema_id") != "phk-v23-lf6-materialized-ledger-manifest-v1"
        or manifest.get("runtime_sampling_permitted") is not False
        or str(manifest.get("semantic_sha256", "")).upper() != EXPECTED_STRONG_SEMANTIC_SHA256
        or manifest.get("ledger") != _record(STRONG_LEDGER)
    ):
        raise PermissionError("LF9 strong-ledger identity drift")
    data = _read_object(ROOT / LF9_CONTRACTS["data"])
    source = data.get("training_source", {})
    dev_r = data.get("initial_DEV_R", {})
    strong = data.get("strong_ledger", {})
    cv = data.get("cv_ledger", {})
    if (
        source.get("path") != MEDIUM.relative_to(ROOT).as_posix()
        or str(source.get("sha256", "")).upper() != EXPECTED_MEDIUM_SHA256
        or dev_r.get("checkpoint_path") != DEV_R_CHECKPOINT.relative_to(ROOT).as_posix()
        or str(dev_r.get("checkpoint_sha256", "")).upper() != EXPECTED_DEV_R_SHA256
        or dev_r.get("load_optimizer_state") is not False
        or strong.get("path") != STRONG_LEDGER.relative_to(ROOT).as_posix()
        or str(strong.get("file_sha256", "")).upper() != EXPECTED_STRONG_LEDGER_SHA256
        or strong.get("manifest_path") != STRONG_LEDGER_MANIFEST.relative_to(ROOT).as_posix()
        or str(strong.get("manifest_sha256", "")).upper() != EXPECTED_STRONG_MANIFEST_SHA256
        or str(strong.get("semantic_sha256", "")).upper() != EXPECTED_STRONG_SEMANTIC_SHA256
        or cv.get("path") != CV_LEDGER.relative_to(ROOT).as_posix()
        or cv.get("manifest_path") != CV_LEDGER_MANIFEST.relative_to(ROOT).as_posix()
        or cv.get("runtime_sampling") is not False
    ):
        raise PermissionError("LF9 data-contract cloud-input binding drift")


def _verify_qualification(path: Path, manifest_path: Path) -> dict[str, Any]:
    qualification = _read_object(path)
    if (
        qualification.get("schema_id") != "phk-v23-lf9-cpu-qualification-v1"
        or qualification.get("task_id") != TASK_ID
        or qualification.get("gate_outcome") != "LF9_CPU_QUALIFICATION_PASS"
        or qualification.get("gpu_execution_authorized_by_cpu_gate") is not True
        or int(qualification.get("scientific_optimizer_updates", -1)) != 0
        or not qualification.get("checks")
        or not all(value is True for value in qualification["checks"].values())
        or not qualification.get("disjoint_checks")
        or not all(value is True for value in qualification["disjoint_checks"].values())
    ):
        raise PermissionError("LF9 bundle requires the exact passed zero-update CPU qualification")
    contracts = {
        role: {"path": relative, "sha256": _sha256(ROOT / relative)}
        for role, relative in LF9_CONTRACTS.items()
    }
    if qualification.get("contracts") != contracts:
        raise PermissionError("LF9 CPU qualification contract identity drift")
    strong = qualification.get("strong_ledger", {})
    required_strong = {
        "file_sha256": EXPECTED_STRONG_LEDGER_SHA256,
        "manifest_sha256": EXPECTED_STRONG_MANIFEST_SHA256,
        "semantic_sha256": EXPECTED_STRONG_SEMANTIC_SHA256,
        "physics_1200_sha256": EXPECTED_PHYSICS_STREAM_SHA256,
        "fixed_blind_pool_sha256": EXPECTED_FIXED_POOL_SHA256,
    }
    if any(str(strong.get(key, "")).upper() != value for key, value in required_strong.items()):
        raise PermissionError("LF9 CPU qualification strong-ledger identity drift")
    cv = qualification.get("cv_ledger", {})
    expected_paths = {
        "path": CV_LEDGER.relative_to(ROOT).as_posix(),
        "manifest_path": CV_LEDGER_MANIFEST.relative_to(ROOT).as_posix(),
    }
    if any(str(cv.get(key, "")) != value for key, value in expected_paths.items()):
        raise PermissionError("LF9 CPU qualification CV-ledger path drift")
    for key in ("file_sha256", "manifest_sha256", "semantic_sha256", "training_rolling_sha256", "one_cell_blind_sha256", "two_by_two_blind_sha256"):
        value = str(cv.get(key, "")).upper()
        if len(value) != 64 or any(c not in "0123456789ABCDEF" for c in value):
            raise PermissionError(f"LF9 CPU qualification lacks valid CV identity: {key}")
    if not CV_LEDGER.is_file() or not CV_LEDGER_MANIFEST.is_file():
        raise FileNotFoundError("LF9 materialized CV ledger or manifest absent")
    if _sha256(CV_LEDGER) != str(cv["file_sha256"]).upper() or _sha256(CV_LEDGER_MANIFEST) != str(cv["manifest_sha256"]).upper():
        raise PermissionError("LF9 materialized CV file binding drift")
    counts = qualification.get("counts", {})
    if not isinstance(counts, Mapping) or not counts:
        raise PermissionError("LF9 CPU qualification lacks CV counts")
    normalization = qualification.get("cv_normalization", {})
    values = [float(normalization.get(key, float("nan"))) for key in ("r_cv0_rms", "L_T_strong0", "s_cv")]
    if not all(math.isfinite(value) and value > 0.0 for value in values):
        raise PermissionError("LF9 CV normalization is invalid")
    manifest = _read_object(manifest_path)
    compact = manifest.get("artifacts", {}).get("compact_qualification")
    if (
        manifest.get("schema_version") != "run-manifest-v1"
        or manifest.get("execution_status") != "COMPLETE"
        or manifest.get("gate_outcome") != qualification.get("gate_outcome")
        or compact != f"artifacts/{path.name}#sha256={_sha256(path)}"
    ):
        raise PermissionError("LF9 CPU qualification manifest drift")
    return qualification


def build(*, qualification_path: Path, qualification_manifest_path: Path,
          archive_path: Path, base_commit: str) -> dict[str, Any]:
    qualification = Path(qualification_path).resolve()
    qualification_manifest = Path(qualification_manifest_path).resolve()
    if (qualification, qualification_manifest) != _locked_qualification_paths():
        raise PermissionError("LF9 qualification inputs differ from locked paths")
    if not qualification.is_file() or not qualification_manifest.is_file():
        raise FileNotFoundError("LF9 qualification artifact or manifest absent")
    _verify_frozen_inputs()
    qualified = _verify_qualification(qualification, qualification_manifest)
    dynamic_sources = (
        qualification.relative_to(ROOT).as_posix(),
        qualification_manifest.relative_to(ROOT).as_posix(),
    )
    committed_files = (*STATIC_FILES, *dynamic_sources)
    if len(committed_files) != len(set(committed_files)):
        raise ValueError("LF9 bundle contains duplicate committed paths")
    _verify_activation_commit(base_commit, committed_files)
    source_bindings = {relative: _sha256(ROOT / relative) for relative in committed_files}
    materialized = {
        "medium": _record(MEDIUM),
        "dev_r_checkpoint": _record(DEV_R_CHECKPOINT),
        "strong_ledger": _record(STRONG_LEDGER),
        "strong_ledger_manifest": _record(STRONG_LEDGER_MANIFEST),
        "cv_ledger": _record(CV_LEDGER),
        "cv_ledger_manifest": _record(CV_LEDGER_MANIFEST),
        "cpu_qualification": _record(qualification),
    }
    cv = qualified["cv_ledger"]
    lines = [f"base_commit={base_commit.upper()}\n"]
    lines.extend(f"source:{path}={digest}\n" for path, digest in sorted(source_bindings.items()))
    lines.extend(f"input:{role}={record['sha256']}\n" for role, record in sorted(materialized.items()))
    identity = "LF9-BUNDLE-" + hashlib.sha256("".join(lines).encode("ascii")).hexdigest().upper()
    manifest = {
        "schema_id": "phk-v23-lf9-deployed-source-manifest-v1",
        "task_id": TASK_ID,
        "source_identity": identity,
        "identity_definition": "SHA256_OF_BASE_COMMIT_AND_SORTED_SOURCE_AND_INPUT_SHA_LINES",
        "base_commit": base_commit,
        "workspace_scope": "LF9_ACTIVATION_COMMIT_PLUS_EXACT_HASH_BOUND_INPUTS_UNRELATED_DIRTY_EXCLUDED",
        "scientific_order": [
            "ER_S_ROUTED_STRONG_SCREEN",
            "ER_CV_ROUTED_THERMAL_CONTROL_VOLUME_SCREEN",
            "CONDITIONAL_SELECTED_FULL_REFINEMENT",
            "CONDITIONAL_MATCHED_NO_FILTER_CONTROL",
        ],
        "arm_local_failure_isolation": True,
        "files": dict(sorted(source_bindings.items())),
        "materialized_inputs": materialized,
        "strong_ledger_semantic_sha256": EXPECTED_STRONG_SEMANTIC_SHA256,
        "cv_ledger_semantic_sha256": str(cv["semantic_sha256"]).upper(),
        "cv_stream_sha256": {
            "training": str(cv["training_rolling_sha256"]).upper(),
            "one_cell_blind": str(cv["one_cell_blind_sha256"]).upper(),
            "two_by_two_blind": str(cv["two_by_two_blind_sha256"]).upper(),
        },
        "runtime_coordinate_generation": False,
    }
    if MANIFEST.exists():
        raise FileExistsError(f"refusing to replace LF9 deployment manifest: {MANIFEST}")
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    archive = Path(archive_path).resolve()
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        raise FileExistsError(archive)
    members = [*(ROOT / relative for relative in committed_files), MEDIUM, DEV_R_CHECKPOINT,
               STRONG_LEDGER, STRONG_LEDGER_MANIFEST, CV_LEDGER, CV_LEDGER_MANIFEST, MANIFEST]
    with tarfile.open(archive, "w:gz") as handle:
        for path in members:
            handle.add(path, arcname=path.relative_to(ROOT).as_posix(), recursive=False)
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
