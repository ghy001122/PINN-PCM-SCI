from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = Path(__file__).resolve().parent
OUTPUT = PACKAGE_ROOT / "package-manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def entry(path: Path) -> dict[str, object]:
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def main() -> None:
    package_files = sorted(
        path
        for path in PACKAGE_ROOT.rglob("*")
        if path.is_file()
        and path != OUTPUT
        and "__pycache__" not in path.parts
        and path.suffix.lower() not in {".pyc", ".pyo"}
    )
    evidence_paths = [
        ROOT / "configs/phk_v2/program_contract.json",
        ROOT / "configs/phk_v2/object_numerical_contract.json",
        ROOT / "configs/phk_v2/case_split_manifest.json",
        ROOT / "docs/references/2026-08-27-phk-pinn-primary-source-baseline-audit.md",
        ROOT / "docs/experiment/2026-08-27-phk-v2-s1-baseline-acquisition-and-cpu-smoke.md",
        ROOT / "docs/experiment/2026-08-27-phk-v2-s2-terminal-closeout.md",
        ROOT / "outputs/runs/20260827T-phk-v2-s2-q-terminal-summary/summary.json",
        ROOT / "pinn_pcm_sci/phk_contract.py",
        ROOT / "pinn_pcm_sci/phk_benchmark.py",
        ROOT / "pinn_pcm_sci/phk_evaluator.py",
        ROOT / "pinn_pcm_sci/phk_runner.py",
        ROOT / "tests/test_phk_contract.py",
        ROOT / "tests/test_phk_benchmark.py",
        ROOT / "tests/test_phk_evaluator.py",
        ROOT / "tests/test_phk_runner.py",
    ]
    missing = [str(path) for path in evidence_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing evidence dependency: {missing}")
    manifest = {
        "schema_id": "phk-v2-paper-package-manifest-v1",
        "status": "COMPLETE_LOCAL_NEGATIVE_LIMITS_V2_PACKAGE",
        "self_reference_policy": "package-manifest.json excluded from its own entries",
        "claim_status": "PHK_V2_ORACLE_NO_GO_EVENT_CONTRACT_AND_CONTROL_EXECUTION_FAILURE_NO_PINN_METHOD_EVIDENCE",
        "package_file_count": len(package_files),
        "package_files": [entry(path) for path in package_files],
        "evidence_dependency_count": len(evidence_paths),
        "evidence_dependencies": [entry(path) for path in evidence_paths],
    }
    OUTPUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"package_file_count": len(package_files), "evidence_dependency_count": len(evidence_paths), "manifest_sha256": sha256(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()

