"""One manuscript consistency/layout pass; reads evidence and PDFs only."""
from pathlib import Path
import csv
import json
import re
import fitz
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "build/preview"
OUT.mkdir(parents=True, exist_ok=True)
results = {}
for name in ("manuscript", "supplement"):
    doc = fitz.open(HERE / f"{name}.pdf")
    images = []
    overflows, replacements = [], []
    text_all = ""
    for i, page in enumerate(doc):
        text = page.get_text()
        text_all += text
        if "\ufffd" in text or "\x00" in text:
            replacements.append(i+1)
        for block in page.get_text("dict")["blocks"]:
            if block["type"] != 0:
                continue
            x0, y0, x1, y1 = block["bbox"]
            if x0 < 40 or x1 > page.rect.width-40 or y0 < 15 or y1 > page.rect.height-15:
                overflows.append({"page": i+1, "bounds": block["bbox"]})
        pix = page.get_pixmap(matrix=fitz.Matrix(1.25, 1.25), alpha=False)
        path = OUT / f"{name}-{i+1:02d}.png"
        pix.save(path)
        im = Image.open(path).convert("RGB")
        im.thumbnail((248, 350))
        tile = Image.new("RGB", (268, 380), "#E7EDF1")
        tile.paste(im, ((268-im.width)//2, 20))
        ImageDraw.Draw(tile).text((12, 365), f"{name} | {i+1}", fill="black")
        images.append(tile)
    cols = 4
    sheet = Image.new("RGB", (cols*268, ((len(images)+cols-1)//cols)*380), "white")
    for i, im in enumerate(images):
        sheet.paste(im, ((i % cols)*268, (i//cols)*380))
    sheet.save(OUT / f"{name}-overview.png")
    (OUT / f"{name}-extracted.txt").write_text(text_all, encoding="utf-8")
    results[name] = {"pages": len(doc), "out_of_page_text_blocks": overflows,
                     "replacement_glyph_pages": replacements,
                     "unexpanded_includes": bool(re.search(r"\{\{(?:TABLE:|REFERENCES)", text_all))}

text = (HERE / "manuscript.md").read_text(encoding="utf-8")
assert len(re.findall(r"!\[Figure", text)) == 6
assert all(f"[{i}]" in text for i in range(1, 11))
assert not re.search(r"\{\{(?:TABLE:|REFERENCES)", text)
with (HERE / "tables/unified-results.csv").open(encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))
assert len(rows) == 10
assert sum(r["role"] == "B_E" for r in rows) == 2
with (HERE / "tables/paired-effects.csv").open(encoding="utf-8", newline="") as f:
    effects = list(csv.DictReader(f))
device = [float(r["relative_reduction_percent"]) for r in effects if r["comparator"] == "F_raw/projected" and r["metric"] in ("current_percent", "power_percent")]
new43 = [r for r in rows if r["protocol"] == "Shorter gap" and r["seed"] == "43"]
e = next(r for r in new43 if r["role"] == "E/projected")
f = next(r for r in new43 if r["role"] == "F_raw/projected")
margin = .9*float(f["S"])-float(e["S"])
assert abs(margin-4.4453125e-6) < 1e-15
paths = re.findall(r"`(pinn_pcm_sci/[^`]+\.py)`", (HERE / "supplement.md").read_text(encoding="utf-8"))
assert all((REPO/p).is_file() for p in paths), paths
results["scientific_consistency"] = {
    "source": "saved tables plus direct source/formula review; not independent numerical reproduction",
    "unique_result_rows": len(rows), "shared_baselines": 2, "main_figures": 6,
    "relative_device_reduction_percent_range": [min(device), max(device)],
    "new_seed43_S_margin": margin, "all_references_present": True,
    "mapped_implementation_paths_exist": True,
    "new_scientific_execution": False,
    "visual_inspection": "pending human-model inspection of generated page images"}
(HERE / "build/review-summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
print(json.dumps(results, indent=2))
