from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = Path(__file__).resolve().parent
EXPECTED_SUMMARY_SHA256 = "8964ACB687F1BDB4F03C2E0D33891EE3705D4C2ABD271085D0C82A2B4469EA78"
EXPECTED_OUTCOME = "PHK_V2_ORACLE_NO_GO_EVENT_CONTRACT_AND_CONTROL_EXECUTION_FAILURE"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


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


def validate_figure_manifest() -> None:
    manifest_path = PACKAGE / "figures/source-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for group in ("sources", "derived_data", "outputs"):
        for item in manifest[group]:
            path = ROOT / item["path"]
            if not path.is_file():
                raise AssertionError(f"missing figure carrier: {item['path']}")
            if path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
                raise AssertionError(f"figure carrier mismatch: {item['path']}")
    generator = ROOT / manifest["generator"]["path"]
    if sha256(generator) != manifest["generator"]["sha256"]:
        raise AssertionError("figure generator hash mismatch")
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
    listed = set()
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
            f"package manifest inventory mismatch: missing={sorted(str(p) for p in actual-listed)}, extra={sorted(str(p) for p in listed-actual)}"
        )


def validate_terminal_identity() -> None:
    summary_path = ROOT / "outputs/runs/20260827T-phk-v2-s2-q-terminal-summary/summary.json"
    if sha256(summary_path) != EXPECTED_SUMMARY_SHA256:
        raise AssertionError("terminal summary SHA mismatch")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary["adjudication"]["outcome"] != EXPECTED_OUTCOME:
        raise AssertionError("terminal outcome mismatch")
    if summary["adjudication"]["oracle_qualified"] is not False:
        raise AssertionError("oracle qualification unexpectedly true")
    if summary["adjudication"]["method_route"] != "STOP_BEFORE_PINN_TRAINING":
        raise AssertionError("method route mismatch")


def validate_no_placeholders() -> None:
    pattern = re.compile(r"\b(?:TODO|TBD|FIXME|PLACEHOLDER|INSERT|XXX)\b", re.IGNORECASE)
    hits: list[str] = []
    for path in PACKAGE.rglob("*"):
        if path.resolve() == Path(__file__).resolve():
            continue
        if path.is_file() and path.suffix.lower() in {".md", ".bib", ".py", ".json", ".txt", ".csv"}:
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if pattern.search(line):
                    hits.append(f"{path.relative_to(ROOT)}:{number}")
    if hits:
        raise AssertionError(f"placeholder tokens found: {hits}")


def main() -> None:
    validate_markdown_links()
    validate_citations()
    validate_figure_manifest()
    validate_package_manifest()
    validate_terminal_identity()
    validate_no_placeholders()
    print("PHK_V2_PACKAGE_VALID")


if __name__ == "__main__":
    main()
