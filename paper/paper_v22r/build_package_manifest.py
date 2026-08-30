"""Build a hash inventory for the PHK-V2.2R terminal paper package."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = Path(__file__).resolve().parent
OUTPUT = PACKAGE / "package-manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def record(path: Path) -> dict[str, object]:
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def main() -> None:
    package_files = sorted(
        path
        for path in PACKAGE.rglob("*")
        if path.is_file()
        and path != OUTPUT
        and "__pycache__" not in path.parts
        and path.suffix.lower() not in {".pyc", ".pyo"}
    )
    source_manifest = json.loads(
        (PACKAGE / "figures" / "source-manifest.json").read_text(encoding="utf-8")
    )
    evidence_paths = {ROOT / item["path"] for item in source_manifest["inputs"]}
    evidence_paths.update(
        {
            ROOT / "configs" / "phk_v22r" / "program_contract.json",
            ROOT / "configs" / "phk_v22r" / "method_contract.json",
            ROOT / "docs" / "experiment" / "2026-08-30-phk-v22r-v11-nominal-terminal-closeout.md",
            ROOT / "docs" / "experiment" / "2026-08-30-phk-v22r-gpu-profile-closeout.md",
            ROOT / "docs" / "experiment" / "manifests" / "20260830T112225-phk-v22r-v11-nominal-69109cd.json",
            ROOT / "outputs" / "runs" / "20260830T0122-phk-v22r-d1-gpu-profile-cf372713" / "summary.json",
            ROOT / "outputs" / "runs" / "20260830T0122-phk-v22r-d1-gpu-profile-cf372713" / "profile-local-adjudication.json",
        }
    )
    payload = {
        "schema_id": "phk-v22r-terminal-paper-package-manifest-v1",
        "status": "ADVISOR_DRAFT_COMPLETE_MVP_NO_GO_NO_BASIC_COMPETENCE",
        "run_id": "20260830T112225-phk-v22r-v11-nominal-69109cd",
        "source_commit": "69109cd324a6d5bf4690fe981086dc2f987eceed",
        "stress_references_read": False,
        "package_file_count": len(package_files),
        "package_files": [record(path) for path in package_files],
        "evidence_dependency_count": len(evidence_paths),
        "evidence_dependencies": [record(path) for path in sorted(evidence_paths)],
    }
    OUTPUT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print("PHK_V22R_PACKAGE_MANIFEST_BUILT")


if __name__ == "__main__":
    main()
