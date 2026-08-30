"""Validate the PHK-V2.2R terminal paper package and evidence bindings."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = Path(__file__).resolve().parent
RUN = ROOT / "outputs" / "runs" / "20260830T112225-phk-v22r-v11-nominal-69109cd"
EXPECTED = {
    "summary": "721D0ADC537F42622F66CFF7266A287D02A626967E8D9A95F1CFC906C26F03FA",
    "decision": "15F4D2B1BF53200872E4D05BDBEB832FB8AB7B04D7189C1B7B8286976C7A2943",
    "program": "A413F56A2317CEFF15FFF2D3BD183C11D990F2E47E8BA33F7316F11567275272",
    "method": "FEEFB36A4D86CACFA6CBAA8C263E7071421415CE88B4F7FBF6BA5F31B9B71D4F",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def validate_required_files() -> None:
    required = {
        "README.md", "manuscript.md", "tables.md", "supplement.md",
        "reproducibility.md", "claim_evidence_matrix.md", "results_registry.md",
        "research_decision_log_zh.md", "reviewer_risk_self_check.md",
        "references.bib", "build_package_manifest.py", "validate_package.py",
        "package-manifest.json", "figures/captions.md",
        "figures/generate_figures.py", "figures/source-manifest.json",
    }
    missing = sorted(name for name in required if not (PACKAGE / name).is_file())
    if missing:
        raise AssertionError(f"missing required deliverables: {missing}")


def validate_terminal_identity() -> None:
    paths = {
        "summary": RUN / "summary.json",
        "decision": RUN / "nominal-decision.json",
        "program": ROOT / "configs" / "phk_v22r" / "program_contract.json",
        "method": ROOT / "configs" / "phk_v22r" / "method_contract.json",
    }
    for name, path in paths.items():
        if sha256(path) != EXPECTED[name]:
            raise AssertionError(f"terminal evidence drift: {name}")
    decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
    if decision["status"] != "MVP_NO_GO_NO_BASIC_COMPETENCE":
        raise AssertionError("terminal outcome mismatch")
    if decision["selected_arm"] is not None:
        raise AssertionError("candidate unexpectedly selected")
    if decision["confirmation_training_authorized"] is not False:
        raise AssertionError("confirmation unexpectedly authorized")
    if decision["stress_unseal_authorized"] is not False:
        raise AssertionError("stress access unexpectedly authorized")


def validate_figures() -> None:
    manifest = json.loads(
        (PACKAGE / "figures" / "source-manifest.json").read_text(encoding="utf-8")
    )
    if manifest["terminal_outcome"] != "MVP_NO_GO_NO_BASIC_COMPETENCE":
        raise AssertionError("figure terminal outcome mismatch")
    if manifest["stress_references_read"] is not False:
        raise AssertionError("figure package claims stress access")
    if sha256(PACKAGE / "figures" / "generate_figures.py") != manifest["generator_sha256"]:
        raise AssertionError("figure generator drift")
    for group in ("inputs", "outputs"):
        for item in manifest[group]:
            path = ROOT / item["path"]
            if not path.is_file():
                raise AssertionError(f"missing figure {group[:-1]}: {item['path']}")
            if path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
                raise AssertionError(f"figure carrier drift: {item['path']}")
    png = list((PACKAGE / "figures").glob("figure-*.png"))
    pdf = list((PACKAGE / "figures").glob("figure-*.pdf"))
    csv = list((PACKAGE / "figures" / "data").glob("figure-*.csv"))
    if (len(png), len(pdf), len(csv)) != (5, 5, 5):
        raise AssertionError(f"unexpected figure counts: {(len(png), len(pdf), len(csv))}")


def validate_markdown_links() -> None:
    missing: list[str] = []
    pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    for markdown in PACKAGE.rglob("*.md"):
        for target in pattern.findall(markdown.read_text(encoding="utf-8")):
            clean = target.strip().split("#", 1)[0]
            if not clean or clean.startswith(("http://", "https://", "mailto:")):
                continue
            if not (markdown.parent / clean).resolve().exists():
                missing.append(f"{markdown.relative_to(ROOT)} -> {target}")
    if missing:
        raise AssertionError(f"missing Markdown links: {missing}")


def validate_no_placeholders_or_overclaims() -> None:
    placeholder = re.compile(
        r"\[(?:RESULT|NOMINAL|SEALED|STRESS|ABLATION|ATTRIBUTION|DISCUSSION|CONCLUSION)_[A-Z_]+\]"
        r"|\b(?:TODO|TBD|FIXME|PLACEHOLDER|INSERT|XXX)\b",
        re.IGNORECASE,
    )
    hits: list[str] = []
    for path in PACKAGE.rglob("*"):
        if path.resolve() == Path(__file__).resolve():
            continue
        if path.is_file() and path.suffix.lower() in {".md", ".bib", ".py", ".json", ".csv", ".txt"}:
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if placeholder.search(line):
                    hits.append(f"{path.relative_to(ROOT)}:{number}")
    if hits:
        raise AssertionError(f"unfinished placeholders found: {hits}")
    manuscript = (PACKAGE / "manuscript.md").read_text(encoding="utf-8")
    required = [
        "MVP_NO_GO_NO_BASIC_COMPETENCE",
        "remain sealed and unread",
        "does not establish a global limitation of PINNs",
        "no positive method claim",
    ]
    for phrase in required:
        if phrase not in manuscript:
            raise AssertionError(f"manuscript lacks claim boundary: {phrase}")


def validate_package_manifest() -> None:
    manifest = json.loads((PACKAGE / "package-manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "ADVISOR_DRAFT_COMPLETE_MVP_NO_GO_NO_BASIC_COMPETENCE":
        raise AssertionError("package status mismatch")
    if manifest["stress_references_read"] is not False:
        raise AssertionError("package claims stress access")
    if manifest["package_file_count"] != len(manifest["package_files"]):
        raise AssertionError("package file count mismatch")
    if manifest["evidence_dependency_count"] != len(manifest["evidence_dependencies"]):
        raise AssertionError("evidence dependency count mismatch")
    listed: set[Path] = set()
    for group in ("package_files", "evidence_dependencies"):
        for item in manifest[group]:
            path = ROOT / item["path"]
            if not path.is_file():
                raise AssertionError(f"missing manifest path: {item['path']}")
            if path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
                raise AssertionError(f"package manifest drift: {item['path']}")
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
        raise AssertionError("package manifest inventory mismatch")


def main() -> None:
    validate_required_files()
    validate_terminal_identity()
    validate_figures()
    validate_markdown_links()
    validate_no_placeholders_or_overclaims()
    validate_package_manifest()
    print("PHK_V22R_TERMINAL_PACKAGE_VALID")


if __name__ == "__main__":
    main()
