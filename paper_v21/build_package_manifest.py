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
        ROOT / "configs/phk_v21/program_contract.json",
        ROOT / "configs/phk_v21/engineering_contract.json",
        ROOT / "configs/phk_v21/e1_solver_selection.json",
        ROOT / "configs/phk_v21/object_numerical_contract.json",
        ROOT / "configs/phk_v21/case_split_manifest.json",
        ROOT / "configs/phk_v21/oracle_and_floor_contract.json",
        ROOT / "configs/phk_v21/baseline_replication_contract.json",
        ROOT / "configs/phk_v21/method_contract.json",
        ROOT / "configs/phk_v21/s1_implementation_amendment_001.json",
        ROOT / "configs/phk_v21/s1_adjudication_amendment_002.json",
        ROOT / "docs/references/2026-08-27-phk-v2-1-baseline-reproduction-identity-audit.md",
        ROOT / "docs/governance/2026-08-27-phk-v21-s0-program-and-engineering-preregistration.md",
        ROOT / "docs/governance/2026-08-28-phk-v21-s0-scientific-contract-freeze.md",
        ROOT / "docs/experiment/2026-08-27-phk-v21-e1-control-solver-selection.md",
        ROOT / "docs/experiment/2026-08-27-phk-v21-e2-engineering-object-selection.md",
        ROOT / "docs/experiment/2026-08-28-phk-v21-s1-intent-02-carrier-reconciliation.md",
        ROOT / "docs/experiment/2026-08-28-phk-v21-s1-adjudication-label-reconciliation.md",
        ROOT / "docs/experiment/2026-08-28-phk-v21-s1-terminal-closeout.md",
        ROOT / "outputs/runs/20260828T-phk-v21-s1-q-terminal-summary-001/summary.json",
        ROOT / "outputs/runs/20260828T-phk-v21-s1-q-terminal-summary-001/oracle-floor-seal.json",
        ROOT / "docs/experiment/manifests/20260828T-phk-v21-s1-q-terminal-summary-001.json",
        ROOT / "pinn_pcm_sci/phk_v21_solver.py",
        ROOT / "pinn_pcm_sci/phk_v21_engineering.py",
        ROOT / "pinn_pcm_sci/phk_v21_design.py",
        ROOT / "pinn_pcm_sci/phk_v21_design_runner.py",
        ROOT / "pinn_pcm_sci/phk_v21_benchmark.py",
        ROOT / "pinn_pcm_sci/phk_v21_evaluator.py",
        ROOT / "pinn_pcm_sci/phk_v21_runner.py",
        ROOT / "tests/test_phk_v21_solver.py",
        ROOT / "tests/test_phk_v21_engineering.py",
        ROOT / "tests/test_phk_v21_design.py",
        ROOT / "tests/test_phk_v21_design_runner.py",
        ROOT / "tests/test_phk_v21_benchmark.py",
        ROOT / "tests/test_phk_v21_evaluator.py",
        ROOT / "tests/test_phk_v21_runner.py",
    ]
    missing = [str(path) for path in evidence_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing evidence dependency: {missing}")
    manifest = {
        "schema_id": "phk-v21-paper-package-manifest-v1",
        "status": "COMPLETE_LOCAL_ORACLE_NO_GO_PACKAGE",
        "self_reference_policy": "package-manifest.json excluded from its own entries",
        "claim_status": "PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN_NO_BASELINE_OR_METHOD_EVIDENCE",
        "package_file_count": len(package_files),
        "package_files": [entry(path) for path in package_files],
        "evidence_dependency_count": len(evidence_paths),
        "evidence_dependencies": [entry(path) for path in evidence_paths],
    }
    OUTPUT.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "package_file_count": len(package_files),
                "evidence_dependency_count": len(evidence_paths),
                "manifest_sha256": sha256(OUTPUT),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
