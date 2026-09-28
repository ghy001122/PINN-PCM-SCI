"""Expand saved-result tables and render equations; no scientific execution."""
from pathlib import Path
import json
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source"
BUILD = HERE / "build"
SOURCE.mkdir(exist_ok=True)
(BUILD / "equations").mkdir(parents=True, exist_ok=True)


def expand(text):
    text = text.replace("{{REFERENCES}}", (HERE / "references.md").read_text(encoding="utf-8").strip())
    def table(match):
        return (HERE / "tables" / (match.group(1) + ".md")).read_text(encoding="utf-8").strip()
    text = re.sub(r"\{\{TABLE:([^}]+)\}\}", table, text)
    # Plain ASCII dashes make line breaking and copied citations predictable.
    return text.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")


def math_image(formula, path):
    # This revision changes availability text only. Reuse a verified, identical
    # formula image instead of rendering the unchanged mathematics again.
    import shutil
    old = HERE.parent / "paper_revision_20260927_circuit_screen"
    old_manifest = json.loads((old / "build/render-manifest.json").read_text(encoding="utf-8"))
    matches = [block for block in old_manifest["documents"]["manuscript"]
               if block.get("type") == "equation" and block.get("formula") == formula]
    if len(matches) != 1:
        raise ValueError("Unchanged-formula cache identity not established")
    cached = old / "build/equations" / Path(matches[0]["path"]).name
    if not cached.is_file():
        raise FileNotFoundError(cached)
    shutil.copyfile(cached, path)


def parse(text, name):
    lines = text.splitlines()
    blocks = []
    i = 0
    equation_count = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            blocks.append({"type": "heading", "level": level, "text": line[level:].strip()})
            i += 1
        elif line.startswith("$$"):
            formula = line[2:]
            while not formula.endswith("$$"):
                i += 1
                formula += " " + lines[i].strip()
            formula = formula[:-2].strip()
            equation_count += 1
            path = BUILD / "equations" / f"{name}-{equation_count:02d}.png"
            math_image(formula, path)
            blocks.append({"type": "equation", "path": str(path), "formula": formula})
            i += 1
        elif line.startswith("!["):
            match = re.fullmatch(r"!\[(.*?)\]\((.*?)\)", line)
            if not match:
                raise ValueError(line)
            blocks.append({"type": "image", "path": str(HERE / match.group(2)), "alt": match.group(1)})
            i += 1
        elif line.startswith("|"):
            table = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [x.strip() for x in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                    table.append(cells)
                i += 1
            if len({len(r) for r in table}) != 1:
                raise ValueError("Inconsistent table width")
            blocks.append({"type": "table", "rows": table})
        else:
            paragraph = line
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].lstrip().startswith(("#", "|", "$$", "![")):
                paragraph += " " + lines[i].strip()
                i += 1
            blocks.append({"type": "paragraph", "text": paragraph})
    return blocks


manifest = {"fonts": str(Path(matplotlib.get_data_path()) / "fonts/ttf"), "documents": {}}
for name in ("manuscript",):
    template = SOURCE / f"{name}.md"
    if not template.exists():
        template.write_text((HERE / f"{name}.md").read_text(encoding="utf-8"), encoding="utf-8")
    text = expand(template.read_text(encoding="utf-8"))
    assert not re.search(r"\{\{(?:TABLE:|REFERENCES)", text), "unexpanded include"
    (HERE / f"{name}.md").write_text(text, encoding="utf-8")
    manifest["documents"][name] = parse(text, name)
(BUILD / "render-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({name: {"blocks": len(blocks), "equations": sum(b["type"] == "equation" for b in blocks)} for name, blocks in manifest["documents"].items()}))
