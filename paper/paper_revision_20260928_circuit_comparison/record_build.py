"""Record only inputs consumed by the availability-only manuscript update."""
from pathlib import Path
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = HERE.parent / "paper_revision_20260927_circuit_screen"


def identity(path):
    path = path.resolve()
    return {"path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    source = HERE / "source/manuscript.md"
    content = source.read_text(encoding="utf-8")
    manifest_path = HERE / "build/render-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    inputs = {source, HERE / "references.md", manifest_path}
    inputs.update(HERE / "tables" / (n + ".md")
                  for n in re.findall(r"\{\{TABLE:([^}]+)\}\}", content))
    for block in manifest["documents"]["manuscript"]:
        if block["type"] in ("image", "equation"):
            inputs.add(Path(block["path"]))
    inherited = json.loads((HERE / "build/manuscript-preparation.json").read_text(encoding="utf-8"))
    record = {
        "task": "PCM-20260928-CUBIC-ENERGY-DISCRIMINATION-01",
        "authoritative_text": "source/manuscript.md",
        "source_change": "Published release identity and actual access status only",
        "build_inputs": [identity(p) for p in sorted(inputs)],
        "builders": [identity(p) for p in [HERE / "prepare_document.py", HERE / "build_docx.py",
                     HERE.parent / "advisor_review_20260924/render_with_word.ps1"]],
        "unchanged_formula_cache": {
            "source_manifest": identity(OLD / "build/render-manifest.json"),
            "count": 24,
            "qualification": "Each formula string matched exactly before copying the saved PNG",
            "representation": "Embedded PNG; editable mathematics remain in Markdown"},
        "inherited_assets": inherited["inherited_assets"],
        "storage": "Inherited figure/table/reference hardlinks are not independent backups",
        "runtime": {"preparation": "Project Python 3.11; cached equation PNG reuse",
                    "docx": "Bundled documents-runtime Python 3.12.14; python-docx 1.2.0 and Pillow",
                    "pdf": "Installed Microsoft Word COM exports the final DOCX",
                    "page_images": "Bundled Poppler at 130 dpi"},
        "render_fallback": "Existing Windows LibreOffice absence documented in the prior build; reused successful Word/Poppler path",
        "successful_manuscript_build_count": 1,
        "engineering_record": "build/preparation-engineering-record.json",
        "review": "build/visual-review-manuscript.json",
        "supplement": {"rebuilt": False, "pages": 58,
                       "pdf": "../paper_revision_20260927_circuit_screen/supplement.pdf",
                       "docx": "../paper_revision_20260927_circuit_screen/supplement.docx",
                       "source": "../paper_revision_20260927_circuit_screen/source/supplement.md"},
        "scientific_regeneration": "None for manuscript. New circuit comparison is a separate report.",
        "outputs": [identity(HERE / ("manuscript." + ext)) for ext in ("md", "docx", "pdf")],
    }
    (HERE / "build-dependencies.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("RECORDED_MANUSCRIPT_INPUTS", len(inputs))


if __name__ == "__main__":
    main()
