from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = Path(__file__).resolve().parent
EXPECTED_SUMMARY_SHA256 = "5E6343D3E8DFE63C1C3F2F031FCF04B455E8C53B5BF454F8AFA013D33C33A9C9"
EXPECTED_OUTCOME = "PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def validate_required_deliverables() -> None:
    required = {
        "README.md",
        "manuscript.md",
        "manuscript_zh.md",
        "plain_language_story_zh.md",
        "supplement.md",
        "reproducibility.md",
        "tables.md",
        "references.bib",
        "baseline_anatomy_cards.md",
        "claim_evidence_matrix.md",
        "reviewer_risk_self_check.md",
        "build_package_manifest.py",
        "validate_package.py",
        "figures/captions.md",
        "figures/source-manifest.json",
    }
    missing = sorted(path for path in required if not (PACKAGE / path).is_file())
    if missing:
        raise AssertionError(f"missing required deliverables: {missing}")


def validate_markdown_links() -> None:
    missing: list[str] = []
    link_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    for markdown in PACKAGE.rglob("*.md"):
        text = markdown.read_text(encoding="utf-8")
        for raw_target in link_pattern.findall(text):
            target = raw_target.strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (markdown.parent / target).resolve()
            if not resolved.exists():
                missing.append(f"{markdown.relative_to(ROOT)} -> {raw_target}")
    if missing:
        raise AssertionError(f"missing local Markdown links: {missing}")


def validate_citations() -> None:
    manuscript = (PACKAGE / "manuscript.md").read_text(encoding="utf-8")
    cited = set(re.findall(r"@([A-Za-z0-9_:-]+)", manuscript))
    bibliography = (PACKAGE / "references.bib").read_text(encoding="utf-8")
    available = set(re.findall(r"@[A-Za-z]+\{([^,]+),", bibliography))
    missing = cited - available
    if missing:
        raise AssertionError(f"citation keys missing from BibTeX: {sorted(missing)}")
    if not cited:
        raise AssertionError("English manuscript contains no citation keys")


def validate_figure_manifest() -> None:
    manifest_path = PACKAGE / "figures/source-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for group in ("inputs", "outputs"):
        for item in manifest[group]:
            path = ROOT / item["path"]
            if not path.is_file():
                raise AssertionError(f"missing figure carrier: {item['path']}")
            if path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
                raise AssertionError(f"figure carrier mismatch: {item['path']}")
    generator = PACKAGE / "figures/generate_figures.py"
    if sha256(generator) != manifest["generator_sha256"]:
        raise AssertionError("figure generator hash mismatch")
    if manifest["terminal_outcome"] != EXPECTED_OUTCOME:
        raise AssertionError("figure terminal outcome mismatch")
    if manifest["solver_or_training_executed"] is not False:
        raise AssertionError("figure generator unexpectedly executed science")
    png = list((PACKAGE / "figures").glob("figure-*.png"))
    pdf = list((PACKAGE / "figures").glob("figure-*.pdf"))
    csv = list((PACKAGE / "figures/data").glob("*.csv"))
    if (len(png), len(pdf), len(csv)) != (6, 6, 6):
        raise AssertionError(f"unexpected figure package counts: {(len(png), len(pdf), len(csv))}")


def validate_package_manifest() -> None:
    manifest = json.loads((PACKAGE / "package-manifest.json").read_text(encoding="utf-8"))
    if manifest["package_file_count"] != len(manifest["package_files"]):
        raise AssertionError("package file count mismatch")
    if manifest["evidence_dependency_count"] != len(manifest["evidence_dependencies"]):
        raise AssertionError("evidence dependency count mismatch")
    listed: set[Path] = set()
    for group in ("package_files", "evidence_dependencies"):
        for item in manifest[group]:
            path = ROOT / item["path"]
            if not path.is_file():
                raise AssertionError(f"missing manifest carrier: {item['path']}")
            if path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
                raise AssertionError(f"package carrier mismatch: {item['path']}")
            if group == "package_files":
                listed.add(path.resolve())
    actual = {
        path.resolve()
        for path in PACKAGE.rglob("*")
        if path.is_file()
        and path.name != "package-manifest.json"
        and "__pycache__" not in path.parts
        and path.suffix.lower() not in {".pyc", ".pyo"}
    }
    if listed != actual:
        raise AssertionError(
            "package manifest inventory mismatch: "
            f"missing={sorted(str(path) for path in actual - listed)}, "
            f"extra={sorted(str(path) for path in listed - actual)}"
        )


def validate_terminal_identity() -> None:
    summary_path = ROOT / "outputs/runs/20260828T-phk-v21-s1-q-terminal-summary-001/summary.json"
    if sha256(summary_path) != EXPECTED_SUMMARY_SHA256:
        raise AssertionError("terminal summary SHA mismatch")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    adjudication = summary["adjudication"]
    if adjudication["outcome"] != EXPECTED_OUTCOME:
        raise AssertionError("terminal outcome mismatch")
    if adjudication["oracle_qualified"] is not False:
        raise AssertionError("oracle qualification unexpectedly true")
    if adjudication["floor_sealed_and_converged"] is not False:
        raise AssertionError("neural floor unexpectedly qualified")
    if adjudication["method_route"] != "STOP_BEFORE_PINN_TRAINING":
        raise AssertionError("method route mismatch")
    if adjudication["reasons"] != ["CONVERGENCE_OR_FLOOR_GATE_FAILED"]:
        raise AssertionError("unexpected terminal reason")
    if summary["not_reached_intents"]:
        raise AssertionError("S1 qualification intent unexpectedly not reached")
    if summary["gross_compute"].get("gpu_hours", 0) != 0:
        raise AssertionError("unexpected GPU accounting")


def validate_no_result_placeholders() -> None:
    pattern = re.compile(r"\b(?:TODO|TBD|FIXME|PLACEHOLDER|INSERT|XXX)\b", re.IGNORECASE)
    allowed_author_metadata = {
        "**Funding:** To be completed by the authors before submission.",
        "**Competing interests:** To be completed by the authors before submission.",
        "**Author contributions:** To be completed by the authors before submission.",
        "**Acknowledgements:** To be completed by the authors before submission.",
    }
    hits: list[str] = []
    for path in PACKAGE.rglob("*"):
        if path.resolve() == Path(__file__).resolve():
            continue
        if path.is_file() and path.suffix.lower() in {".md", ".bib", ".py", ".json", ".txt", ".csv"}:
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if pattern.search(line) and line not in allowed_author_metadata:
                    hits.append(f"{path.relative_to(ROOT)}:{number}")
    if hits:
        raise AssertionError(f"unfinished result placeholders found: {hits}")


def main() -> None:
    validate_required_deliverables()
    validate_markdown_links()
    validate_citations()
    validate_figure_manifest()
    validate_package_manifest()
    validate_terminal_identity()
    validate_no_result_placeholders()
    print("PHK_V21_PACKAGE_VALID")


if __name__ == "__main__":
    main()
