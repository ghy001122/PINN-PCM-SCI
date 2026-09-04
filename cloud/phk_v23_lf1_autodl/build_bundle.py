"""Build the exact LF1 source manifest and portable source archive locally."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tarfile
from typing import Sequence


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "cloud" / "phk_v23_lf1_autodl" / "deployed-source-manifest.json"
MEDIUM = (
    ROOT
    / "outputs"
    / "runs"
    / "20260828T-phk-v21-s1-q-04-nominal-medium"
    / "result-intent-04.npz"
)
STATIC_FILES = (
    "cloud/phk_v23_lf1_autodl/preflight.py",
    "cloud/phk_v23_lf1_autodl/README.md",
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
    "pinn_pcm_sci/phk_v23_lf1_qualification.py",
    "tests/test_phk_v21_benchmark.py",
    "tests/test_phk_v23_lf1.py",
    "tests/test_phk_v23_lf1_cloud.py",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def build(
    *, qualification_path: Path, archive_path: Path, base_commit: str
) -> dict[str, object]:
    qualification = Path(qualification_path).resolve()
    try:
        qualification_relative = qualification.relative_to(ROOT).as_posix()
    except ValueError as exc:
        raise PermissionError("LF1 qualification must be inside the repository") from exc
    files = (*STATIC_FILES, qualification_relative)
    if len(set(files)) != len(files):
        raise ValueError("LF1 source manifest contains duplicate paths")
    bindings: dict[str, str] = {}
    for relative in files:
        exact = ROOT / Path(relative)
        if not exact.is_file():
            raise FileNotFoundError(f"LF1 source file is absent: {relative}")
        bindings[relative] = _sha256(exact)
    lines = "".join(
        f"{relative}={digest}\n" for relative, digest in sorted(bindings.items())
    )
    aggregate = hashlib.sha256(lines.encode("utf-8")).hexdigest().upper()
    source_identity = f"LF1-BUNDLE-{aggregate}"
    if not MEDIUM.is_file():
        raise FileNotFoundError("LF1 medium training carrier is absent")
    qualification_payload = json.loads(qualification.read_text(encoding="utf-8"))
    if (
        qualification_payload.get("status") != "LF1_CPU_QUALIFICATION_PASS"
        or qualification_payload.get("gpu_execution_authorized_by_cpu_gate") is not True
    ):
        raise PermissionError("LF1 bundle requires a passed CPU qualification")
    manifest = {
        "schema_id": "phk-v23-lf1-deployed-source-manifest-v1",
        "source_identity": source_identity,
        "identity_definition": "SHA256_OF_SORTED_PATH_EQUALS_UPPERCASE_SHA256_LINES",
        "base_commit": str(base_commit),
        "workspace_scope": "LF1_EXACT_FILE_ALLOWLIST_UNRELATED_DIRTY_WORKTREE_CONTENT_EXCLUDED",
        "training_input": {
            "path": MEDIUM.relative_to(ROOT).as_posix(),
            "sha256": _sha256(MEDIUM),
            "size_bytes": MEDIUM.stat().st_size,
        },
        "cpu_qualification": {
            "path": qualification_relative,
            "sha256": _sha256(qualification),
            "size_bytes": qualification.stat().st_size,
        },
        "files": dict(sorted(bindings.items())),
    }
    if MANIFEST.exists():
        raise FileExistsError(f"refusing to replace LF1 source manifest: {MANIFEST}")
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    archive = Path(archive_path).resolve()
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        raise FileExistsError(f"refusing to replace LF1 archive: {archive}")
    with tarfile.open(archive, "w:gz") as handle:
        for relative in files:
            handle.add(ROOT / Path(relative), arcname=relative, recursive=False)
        handle.add(
            MANIFEST,
            arcname=MANIFEST.relative_to(ROOT).as_posix(),
            recursive=False,
        )
    return {
        "source_identity": source_identity,
        "manifest": str(MANIFEST),
        "manifest_sha256": _sha256(MANIFEST),
        "archive": str(archive),
        "archive_sha256": _sha256(archive),
        "file_count": len(files),
        "medium_separate_upload": True,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--base-commit", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    print(
        json.dumps(
            build(
                qualification_path=arguments.qualification,
                archive_path=arguments.archive,
                base_commit=arguments.base_commit,
            ),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
