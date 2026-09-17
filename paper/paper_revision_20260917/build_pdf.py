"""Typeset the prepared manuscript with the bundled ReportLab runtime."""
from pathlib import Path
import html
import json
import re
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                               LongTable, TableStyle, KeepTogether, CondPageBreak, PageBreak)
from reportlab.lib.utils import ImageReader

HERE = Path(__file__).resolve().parent
manifest = json.loads((HERE / "build/render-manifest.json").read_text(encoding="utf-8"))
fontdir = Path(manifest["fonts"])
for face, filename in (("Body", "DejaVuSerif.ttf"), ("BodyBold", "DejaVuSerif-Bold.ttf"),
                       ("BodyItalic", "DejaVuSerif-Italic.ttf"), ("Sans", "DejaVuSans.ttf"),
                       ("SansBold", "DejaVuSans-Bold.ttf"), ("Mono", "DejaVuSansMono.ttf")):
    pdfmetrics.registerFont(TTFont(face, str(fontdir / filename)))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyBold", italic="BodyItalic", boldItalic="BodyBold")
pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="SansBold", italic="Sans", boldItalic="SansBold")
WIDTH = A4[0] - 104
INK = colors.HexColor("#182A3A")
ACCENT = colors.HexColor("#176B87")
styles = {
    "title": ParagraphStyle("title", fontName="SansBold", fontSize=20, leading=25, textColor=INK, spaceAfter=18, keepWithNext=True),
    "h2": ParagraphStyle("h2", fontName="SansBold", fontSize=13.3, leading=17, textColor=INK, spaceBefore=14, spaceAfter=8, keepWithNext=True),
    "h3": ParagraphStyle("h3", fontName="SansBold", fontSize=11, leading=15, textColor=INK, spaceBefore=10, spaceAfter=6, keepWithNext=True),
    "body": ParagraphStyle("body", fontName="Body", fontSize=10.3, leading=14.3, spaceAfter=7.5, allowWidows=0, allowOrphans=0, splitLongWords=True),
    "caption": ParagraphStyle("caption", fontName="Sans", fontSize=8.3, leading=11.2, spaceBefore=5, spaceAfter=10),
    "tablecaption": ParagraphStyle("tablecaption", fontName="Sans", fontSize=8.6, leading=11.4, spaceBefore=6, spaceAfter=6),
    "ref": ParagraphStyle("ref", fontName="Body", fontSize=8.6, leading=11.4, spaceAfter=5.5, splitLongWords=True),
    "suppref": ParagraphStyle("suppref", fontName="Body", fontSize=8.6, leading=11.4, spaceAfter=5.5, splitLongWords=True),
    "cell": ParagraphStyle("cell", fontName="Sans", fontSize=7.6, leading=10, spaceAfter=0, splitLongWords=True),
    "headcell": ParagraphStyle("headcell", fontName="SansBold", fontSize=7.4, leading=9.6, textColor=colors.white, splitLongWords=True),
}


def inline(text):
    # Escape user-independent scientific prose, then preserve simple inline links.
    codes = []
    def protect_code(match):
        codes.append(match.group(1))
        return "@@CODE"+str(len(codes)-1)+"@@"
    text = re.sub(r"`([^`]+)`", protect_code, text)
    text = html.escape(text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: '<link href="'+m.group(2)+'" color="#176B87">'+m.group(1)+'</link>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    symbols = ("u_θ", "T_θ", "φ_θ", "σ_θ", "V_θ", "h_T", "h_φ", "h_V", "A_e", "ω_i", "q_i", "P_J", "L_obs", "L_BC", "L_IC", "J_Tφ", "E_φ", "E_T", "E_V", "E_I", "E_P", "E_W", "B_E", "D_E", "P_E", "F_raw", "F_full", "F_bal", "D_C", "P_kappa", "ε_logit", "d_scale", "T_c", "m_c", "m_h", "w_M")
    for symbol in symbols:
        base, sub = symbol.split("_", 1)
        text = re.sub(r"(?<![\w/])"+re.escape(symbol)+r"(?![\w/])", base+"<sub>"+sub+"</sub>", text)
    for symbol in ("E_C", "E_R", "R_ξ", "c_g", "ell_θ", "e_c", "e_b", "δ_d"):
        base, sub = symbol.split("_", 1)
        if base == "ell": base = "ℓ"
        text = re.sub(r"(?<![\w/])"+re.escape(symbol)+r"(?![\w/])", base+"<sub>"+sub+"</sub>", text)
    for i, code in enumerate(codes):
        text = text.replace("@@CODE"+str(i)+"@@", '<font face="Mono" size="7.2">'+html.escape(code)+'</font>')
    return text


def cell_number(text):
    if re.fullmatch(r"[-+]?\d*\.?\d+(?:e[-+]?\d+)?", text, flags=re.I):
        val = float(text)
        if val == int(val) and abs(val) < 100000:
            return str(int(val))
        return f"{val:.6g}"
    return text


def make_table(rows):
    n = len(rows[0])
    numeric_revision = rows[0][:3] == ["Reference", "Seed", "Role"] and n in (9, 11)
    if numeric_revision and n == 9:
        widths = [43, 37, 35, 59, 70, 69, 70, 70, 38]
        widths = [w*WIDTH/sum(widths) for w in widths]
    elif numeric_revision and n == 11:
        widths = [43, 33, 29, 33, 45, 46, 42, 55, 46, 59.5, 59.5]
        widths = [w*WIDTH/sum(widths) for w in widths]
    elif rows[0][:2] == ["Seed", "Role"]:
        widths = [35, 40] + [(WIDTH-75)/(n-2)]*(n-2)
    elif rows[0][:4] == ["Case", "Seed", "Method", "Cycle"]:
        widths = [30, 33, 48, 34] + [(WIDTH-145)/(n-4)]*(n-4)
    elif rows[0][:3] == ["Case", "Seed", "Method"]:
        widths = [69, 36, 66] + [(WIDTH-171)/(n-3)]*(n-3)
    elif rows[0][:4] == ["Case", "Seed", "Control", "Rule"]:
        widths = [60, 33, 48, 32, 55, 57, 57, 54, 67]
        widths = [w*WIDTH/sum(widths) for w in widths]
    elif n == 4 and rows[0][0] == "Statement":
        ratios = [1.6, 1.15, 1.35, 1.6]
        widths = [WIDTH*r/sum(ratios) for r in ratios]
    elif n == 2:
        widths = [WIDTH*.31, WIDTH*.69]
    elif rows[0][0] in ("Role", "Method"):
        widths = [107] + [(WIDTH-107)/(n-1)]*(n-1)
    else:
        widths = [WIDTH/n]*n
    padding = 4 if numeric_revision else 5
    cells = []
    for j, row in enumerate(rows):
        rendered = []
        for col, raw in enumerate(row):
            value = cell_number(raw) if j else raw
            if numeric_revision and not j:
                value = {'Reference': 'Ref.', 'Precision': 'Prec.', 'Recovery': 'Recov.'}.get(value, value)
            if numeric_revision and j and col == 1 and value == 'shared':
                value = '-'
            style = styles["headcell" if j == 0 else "cell"]
            if numeric_revision and j and re.fullmatch(r"[-+]?\d*\.?\d+(?:e[-+]?\d+)?", value, flags=re.I):
                measured = pdfmetrics.stringWidth(value, "Sans", style.fontSize)
                size = min(style.fontSize, style.fontSize*(widths[col]-2*padding-1)/max(measured, 1))
                if size < 6.5:
                    raise ValueError(f"Numeric column needs more width: {value}")
                style = ParagraphStyle("numeric", parent=style, fontSize=size, splitLongWords=False)
            rendered.append(Paragraph(inline(value), style))
        cells.append(rendered)
    table = LongTable(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
    commands = [("BACKGROUND", (0, 0), (-1, 0), INK), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), padding), ("RIGHTPADDING", (0, 0), (-1, -1), padding),
                ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LINEBELOW", (0, -1), (-1, -1), .5, colors.HexColor("#9EAAB5"))]
    for i in range(1, len(rows)):
        if i % 2:
            commands.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F0F4F7")))
    table.setStyle(TableStyle(commands))
    return table


class Document(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in ("h2", "h3"):
            self.section_count = getattr(self, "section_count", 0) + 1
            key = "section-" + str(self.section_count)
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(flowable.getPlainText(), key, level=0, closed=False)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D2DCE3")); canvas.setLineWidth(.5)
    canvas.line(52, 39, A4[0]-52, 39)
    canvas.setFont("Sans", 7.2); canvas.setFillColor(colors.HexColor("#637483"))
    label = "Supplementary material" if doc.is_supplement else "Training-time electrical elimination"
    canvas.drawString(52, 27, label + "  |  Review revision, 17 September 2026")
    canvas.drawRightString(A4[0]-52, 27, str(doc.page))
    if doc.page > 1:
        canvas.setFont("Sans", 7.4)
        canvas.drawString(52, A4[1]-32, "PINN electrothermal phase-change reconstruction")
    canvas.restoreState()


summary = {}
for name, blocks in manifest["documents"].items():
    doc = Document(str(HERE / f"{name}.pdf"), pagesize=A4, rightMargin=52, leftMargin=52,
                   topMargin=49, bottomMargin=53, title=blocks[0]["text"], author="Author information pending",
                   subject="Matched electrothermal reconstruction, fixed-prediction reference sensitivity and complete supplementary controls")
    doc.is_supplement = name == "supplement"
    story = []
    i = 0
    while i < len(blocks):
        b = blocks[i]
        if b["type"] == "heading":
            sty = "title" if b["level"] == 1 else ("h2" if b["level"] == 2 else "h3")
            story.append(Paragraph(inline(b["text"]), styles[sty]))
        elif b["type"] == "paragraph":
            text = b["text"]
            sty = "ref" if re.match(r"^\[\d+\]", text) else ("caption" if text.startswith("Figure ") else ("tablecaption" if text.startswith("Table ") else "body"))
            if sty == 'ref' and doc.is_supplement:
                sty = 'suppref'
            if sty == "tablecaption":
                story.append(CondPageBreak(100))
            story.append(Paragraph(inline(text), styles[sty]))
        elif b["type"] == "table":
            if b['rows'][0][:4] == ['Reference', 'Seed', 'Role', 'Cycle']:
                # Keep the complete event table in readable, bounded page panels.
                # The table's CSV/Markdown source retains full-precision numbers.
                for start in range(1, len(b['rows']), 22):
                    if start > 1:
                        story.append(PageBreak())
                        story.append(Paragraph('Table S14 (continued). Complete support and timing measures.', styles['tablecaption']))
                    story.extend([make_table([b['rows'][0]] + b['rows'][start:start+22]), Spacer(1, 8)])
            else:
                story.extend([make_table(b["rows"]), Spacer(1, 8)])
        elif b["type"] in ("image", "equation"):
            w, h = ImageReader(b["path"]).getSize()
            if b["type"] == "equation":
                # Rendered at 220 dpi with a 14-point math font, capped to page width.
                width = min(WIDTH, w*72/220)
                height = h*width/w
                picture = Image(b["path"], width=width, height=height, hAlign="LEFT")
                story.extend([Spacer(1, 2), picture, Spacer(1, 7)])
            else:
                width = WIDTH
                height = h*width/w
                picture = Image(b["path"], width=width, height=height)
                if i+1 < len(blocks) and blocks[i+1]["type"] == "paragraph" and blocks[i+1]["text"].startswith("Figure "):
                    caption = Paragraph(inline(blocks[i+1]["text"]), styles["caption"])
                    story.append(KeepTogether([Spacer(1, 5), picture, caption])); i += 1
                else:
                    story.append(picture)
        i += 1
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    summary[name] = {"pages": doc.page, "output": str(HERE / f"{name}.pdf")}
(HERE / "build/pdf-build-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
