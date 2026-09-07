"""Build the activation-commit and materialized-ledger LF6 cloud bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "PHK_V23_LF6_EVENT_FRONTIER_RANK_BAND_AND_SAFETY_GATED_PHYSICS_PILOT_EXECUTE"
MANIFEST = ROOT / "cloud/phk_v23_lf6_autodl/deployed-source-manifest.json"
LOCK = ROOT / "configs/phk_v23/lf6_write_allowlist_lock.json"
MEDIUM = ROOT / "outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz"
INITIAL_CHECKPOINT = ROOT / "outputs/runs/20260904T150300Z-phk-v23-lf3-phase-latent-97a5b74/checkpoint-t0-step-1200.pt"
DEV_M_CHECKPOINT = ROOT / "outputs/runs/20260905T102817Z-phk-v23-lf4-interface-band-5dbde1d/checkpoint-dev-m-interface-band-mse-step-400.pt"
EXPECTED_DEV_M_SHA256 = "16EEE20C6B1A2510ACB387E83894ADD64061D631422FAB4DAA9EC1F7194018B5"
EXPECTED_MEDIUM_SHA256 = "18411D8066FACB31570774374A699ECE867981752ED9FEE25C34DF30D5D8802F"
EXPECTED_INITIAL_SHA256 = "4A679E54A4819A9D30CF55C6396C37129B9801BC635A8BD7EB3883F8F3B66EDA"

STATIC_FILES = (
    "configs/phk_v23/lf6_write_allowlist_lock.json",
    "cloud/phk_v23_lf6_autodl/README.md",
    "cloud/phk_v23_lf6_autodl/build_bundle.py",
    "cloud/phk_v23_lf6_autodl/preflight.py",
    "cloud/phk_v23_lf6_autodl/run.sh",
    "configs/phk_v23/program_contract_lf6_event_frontier.json",
    "configs/phk_v23/method_contract_lf6_event_frontier.json",
    "configs/phk_v23/data_contract_lf6_event_frontier.json",
    "configs/phk_v23/decision_contract_lf6_event_frontier.json",
    "configs/phk_v23/program_contract_lf5_temporal_zero_level.json",
    "configs/phk_v23/method_contract_lf5_temporal_zero_level.json",
    "configs/phk_v23/data_contract_lf5_temporal_zero_level.json",
    "configs/phk_v23/decision_contract_lf5_temporal_zero_level.json",
    "configs/phk_v23/program_contract_lf4_interface_band.json",
    "configs/phk_v23/method_contract_lf4_interface_band.json",
    "configs/phk_v23/data_contract_lf4_interface_band.json",
    "configs/phk_v23/decision_contract_lf4_interface_band.json",
    "configs/phk_v23/program_contract_lf3_phase_latent_carrier.json",
    "configs/phk_v23/method_contract_lf3_phase_latent_carrier.json",
    "configs/phk_v23/data_contract_lf3_phase_latent_carrier.json",
    "configs/phk_v23/decision_contract_lf3_phase_latent_carrier.json",
    "configs/phk_v23/program_contract_lf2_measure_calibrated_feasible_pinn.json",
    "configs/phk_v23/method_contract_lf2_measure_calibrated_feasible_pinn.json",
    "configs/phk_v23/data_contract_lf2_measure_calibrated_medium.json",
    "configs/phk_v23/decision_contract_lf2_measure_calibrated_feasible_pinn.json",
    "configs/phk_v23/program_contract_lf1_event_preserving_multifidelity.json",
    "configs/phk_v23/method_contract_lf1_event_preserving_multifidelity.json",
    "configs/phk_v23/data_contract_lf1_medium_event_replay.json",
    "configs/phk_v23/decision_contract_lf1_event_preserving.json",
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
    "pinn_pcm_sci/phk_v23_lf6_qualification.py",
    "tests/test_phk_v21_benchmark.py",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _record(path: Path) -> dict[str, Any]:
    return {"path": path.resolve().relative_to(ROOT.resolve()).as_posix(), "sha256": _sha256(path), "size_bytes": path.stat().st_size}


def _read_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"LF6 expected JSON object: {path}")
    return payload


def _git(*args: str) -> bytes:
    completed = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.decode(errors="replace").strip())
    return completed.stdout


def _verify_activation_commit(base_commit: str, files: Sequence[str]) -> None:
    if len(base_commit) != 40 or any(character not in "0123456789abcdefABCDEF" for character in base_commit):
        raise ValueError("LF6 base commit must be a full Git object id")
    head = _git("rev-parse", "HEAD").decode().strip()
    if head.lower() != base_commit.lower():
        raise PermissionError("LF6 bundle must be built at the activation commit")
    for relative in files:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"LF6 committed source absent: {relative}")
        committed = _git("show", f"{base_commit}:{relative}")
        if committed != path.read_bytes():
            raise PermissionError(f"LF6 source is not exact activation-commit content: {relative}")


def _contract_dev_m_binding() -> Mapping[str, Any]:
    data = _read_object(ROOT / "configs/phk_v23/data_contract_lf6_event_frontier.json")
    candidates = (
        data.get("LF4_DEV_M"),
        data.get("LF4_fixed_inputs", {}).get("DEV_M"),
        data.get("lf4_fixed_inputs", {}).get("DEV_M"),
        data.get("fixed_inputs", {}).get("DEV_M"),
    )
    for candidate in candidates:
        if isinstance(candidate, Mapping):
            return candidate
    raise KeyError("LF6 data contract lacks exact DEV-M binding")


def _qualification_ledger_binding(qualification: Mapping[str, Any]) -> Mapping[str, Any]:
    binding = qualification.get("ledger")
    if not isinstance(binding, Mapping):
        raise ValueError("LF6 CPU-F qualification lacks materialized ledger binding")
    return binding


def build(
    *,
    qualification_path: Path,
    ledger_path: Path,
    ledger_manifest_path: Path,
    archive_path: Path,
    base_commit: str,
    dev_m_checkpoint: Path | None = None,
    allow_dev_m_fallback_input: bool = False,
) -> dict[str, Any]:
    if dev_m_checkpoint is not None and not allow_dev_m_fallback_input:
        raise PermissionError("LF6 DEV-M fallback input needs explicit authorization")
    qualification = Path(qualification_path).resolve()
    ledger = Path(ledger_path).resolve()
    ledger_manifest = Path(ledger_manifest_path).resolve()
    lock = _read_object(LOCK)
    expected_qualification = (ROOT / lock["timestamped_paths"]["cpu_artifact"]).resolve()
    expected_ledger = (ROOT / lock["raw_paths"]["cpu_ledger"]).resolve()
    expected_ledger_manifest = (ROOT / lock["raw_paths"]["cpu_ledger_manifest"]).resolve()
    if (qualification, ledger, ledger_manifest) != (expected_qualification, expected_ledger, expected_ledger_manifest):
        raise PermissionError("LF6 bundle inputs differ from locked paths")
    for path in (qualification, ledger, ledger_manifest, MEDIUM, INITIAL_CHECKPOINT):
        if not path.is_file():
            raise FileNotFoundError(path)
    if _sha256(MEDIUM) != EXPECTED_MEDIUM_SHA256 or _sha256(INITIAL_CHECKPOINT) != EXPECTED_INITIAL_SHA256:
        raise PermissionError("LF6 medium or LF3-T0 input drift")

    qualification_payload = _read_object(qualification)
    if (
        qualification_payload.get("schema_id") != "phk-v23-lf6-cpu-qualification-v1"
        or qualification_payload.get("task_id") != TASK_ID
        or qualification_payload.get("status") != "LF6_CPU_F_QUALIFICATION_PASS"
        or qualification_payload.get("gpu_execution_authorized_by_cpu_gate") is not True
    ):
        raise PermissionError("LF6 bundle requires a passed exact CPU-F qualification")
    ledger_payload = _read_object(ledger_manifest)
    if ledger_payload.get("schema_id") != "phk-v23-lf6-materialized-ledger-manifest-v1" or ledger_payload.get("task_id") != TASK_ID:
        raise ValueError("LF6 materialized ledger manifest identity drift")
    binding = _qualification_ledger_binding(qualification_payload)
    for key, actual in (("path", ledger.relative_to(ROOT).as_posix()), ("sha256", _sha256(ledger)), ("size_bytes", ledger.stat().st_size), ("manifest_path", ledger_manifest.relative_to(ROOT).as_posix()), ("manifest_sha256", _sha256(ledger_manifest))):
        if binding.get(key) != actual:
            raise ValueError(f"LF6 qualification ledger binding drift: {key}")
    if binding.get("arrays") != ledger_payload.get("arrays") or binding.get("streams") != ledger_payload.get("streams"):
        raise ValueError("LF6 qualification does not bind the complete ledger manifest")

    contract_records = {
        role: {"path": f"configs/phk_v23/{role}_contract_lf6_event_frontier.json", "sha256": _sha256(ROOT / f"configs/phk_v23/{role}_contract_lf6_event_frontier.json")}
        for role in ("program", "method", "data", "decision")
    }
    if qualification_payload.get("contracts") != contract_records:
        raise PermissionError("LF6 CPU-F qualification contract identity drift")

    dev_m: Path | None = None
    if allow_dev_m_fallback_input:
        if dev_m_checkpoint is None:
            raise PermissionError("LF6 authorized DEV-M fallback requires its exact checkpoint")
        dev_m = Path(dev_m_checkpoint).resolve()
        contract_binding = _contract_dev_m_binding()
        if (
            dev_m != DEV_M_CHECKPOINT.resolve()
            or not dev_m.is_file()
            or _sha256(dev_m) != EXPECTED_DEV_M_SHA256
            or str(contract_binding.get("path")) != DEV_M_CHECKPOINT.relative_to(ROOT).as_posix()
            or str(contract_binding.get("sha256", "")).upper() != EXPECTED_DEV_M_SHA256
        ):
            raise PermissionError("LF6 exact DEV-M fallback checkpoint drift")

    qualification_relative = qualification.relative_to(ROOT).as_posix()
    qualification_manifest_relative = str(lock["timestamped_paths"]["cpu_manifest"])
    qualification_manifest_payload = _read_object(ROOT / qualification_manifest_relative)
    compact_reference = qualification_manifest_payload.get("artifacts", {}).get("compact_qualification")
    if (
        qualification_manifest_payload.get("schema_version") != "run-manifest-v1"
        or qualification_manifest_payload.get("run_id") != "20260906T065434Z-phk-v23-lf6-cpu-qualification"
        or qualification_manifest_payload.get("gate") != "PHK_V23_LF6_CPU_F"
        or qualification_manifest_payload.get("gate_outcome") != "LF6_CPU_F_QUALIFICATION_PASS"
        or qualification_manifest_payload.get("execution_status") != "COMPLETE"
        or compact_reference != f"artifacts/{qualification.name}#sha256={_sha256(qualification)}"
    ):
        raise PermissionError("LF6 CPU-F qualification manifest drift")
    committed_files = (*STATIC_FILES, qualification_relative, qualification_manifest_relative)
    if len(committed_files) != len(set(committed_files)):
        raise ValueError("LF6 bundle contains duplicate committed paths")
    _verify_activation_commit(base_commit, committed_files)
    source_bindings = {relative: _sha256(ROOT / relative) for relative in committed_files}
    materialized = {
        "medium": _record(MEDIUM),
        "initial_checkpoint": _record(INITIAL_CHECKPOINT),
        "cpu_qualification": _record(qualification),
        "ledger": _record(ledger),
        "ledger_manifest": _record(ledger_manifest),
    }
    if dev_m is not None:
        materialized["dev_m_fallback_checkpoint"] = _record(dev_m)
    identity_lines = [f"base_commit={base_commit.upper()}\n"]
    identity_lines.extend(f"source:{path}={digest}\n" for path, digest in sorted(source_bindings.items()))
    identity_lines.extend(f"input:{role}={record['sha256']}\n" for role, record in sorted(materialized.items()))
    source_identity = "LF6-BUNDLE-" + hashlib.sha256("".join(identity_lines).encode("ascii")).hexdigest().upper()
    manifest = {
        "schema_id": "phk-v23-lf6-deployed-source-manifest-v1",
        "task_id": TASK_ID,
        "source_identity": source_identity,
        "identity_definition": "SHA256_OF_BASE_COMMIT_AND_SORTED_SOURCE_AND_INPUT_SHA_LINES",
        "base_commit": base_commit,
        "workspace_scope": "LF6_ACTIVATION_COMMIT_PLUS_HASH_BOUND_MATERIALIZED_INPUTS_UNRELATED_DIRTY_EXCLUDED",
        "dev_m_fallback_input": {
            "included": dev_m is not None,
            "requires_explicit_user_authorization": True,
            "operator_asserted_authorized": bool(allow_dev_m_fallback_input),
        },
        "files": dict(sorted(source_bindings.items())),
        "materialized_inputs": materialized,
        "ledger_semantic_sha256": str(ledger_payload.get("semantic_sha256", "")).upper(),
    }
    if MANIFEST.exists():
        raise FileExistsError(f"refusing to replace LF6 deployment manifest: {MANIFEST}")
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")

    archive = Path(archive_path).resolve()
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        raise FileExistsError(archive)
    archive_members = [*(ROOT / relative for relative in committed_files), MEDIUM, INITIAL_CHECKPOINT, ledger, ledger_manifest]
    if dev_m is not None:
        archive_members.append(dev_m)
    with tarfile.open(archive, "w:gz") as handle:
        for path in archive_members:
            handle.add(path, arcname=path.relative_to(ROOT).as_posix(), recursive=False)
        handle.add(MANIFEST, arcname=MANIFEST.relative_to(ROOT).as_posix(), recursive=False)
    return {
        "source_identity": source_identity,
        "base_commit": base_commit,
        "manifest": str(MANIFEST),
        "manifest_sha256": _sha256(MANIFEST),
        "archive": str(archive),
        "archive_sha256": _sha256(archive),
        "dev_m_fallback_included": dev_m is not None,
        "committed_file_count": len(committed_files),
        "materialized_input_count": len(materialized),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--ledger-manifest", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--base-commit", required=True)
    parser.add_argument("--dev-m-checkpoint", type=Path)
    parser.add_argument("--allow-dev-m-fallback-input", action="store_true")
    args = parser.parse_args(argv)
    print(json.dumps(build(qualification_path=args.qualification, ledger_path=args.ledger, ledger_manifest_path=args.ledger_manifest, archive_path=args.archive, base_commit=args.base_commit, dev_m_checkpoint=args.dev_m_checkpoint, allow_dev_m_fallback_input=args.allow_dev_m_fallback_input), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
