"""Record inspected final manuscript; this script performs no scientific analysis."""
from pathlib import Path
import hashlib
import json
import re
from datetime import datetime, timezone
from zipfile import ZipFile
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
OLD = HERE.parents[1] / 'paper_revision_20260928_circuit_comparison'
ROOT = HERE.parents[2]

def identity(p):
    return {'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size,
            'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}

old = json.loads((OLD / 'build/render-manifest.json').read_text(encoding='utf8'))
new = json.loads((HERE / 'build/render-manifest.json').read_text(encoding='utf8'))
different = [i for i,(a,b) in enumerate(zip(old['documents']['manuscript'],new['documents']['manuscript'])) if a != b]
assert different == [161, 162]
assert len(old['documents']['manuscript']) == len(new['documents']['manuscript'])
with ZipFile(OLD / 'manuscript.docx') as a, ZipFile(HERE / 'manuscript.docx') as b:
    images = [p for p in a.namelist() if p.startswith('word/media/')]
    assert len(images) == 30
    assert all(a.read(p) == b.read(p) for p in images)
doc = PdfReader(HERE / 'manuscript.pdf')
assert len(doc.pages) == 17
assert 'scoring' in doc.pages[15].extract_text()
assert '709b10f' in doc.pages[15].extract_text()
links = re.findall(r'\]\(([^)]+)\)',(HERE / 'manuscript.md').read_text(encoding='utf8'))
assert all((HERE / p).is_file() for p in links if not p.startswith(('https://','http://')))
record = {
    'status': 'PASS', 'recorded_utc': datetime.now(timezone.utc).isoformat(),
    'pages': 17, 'pages_visually_opened': list(range(1,18)),
    'inspection': 'Every final 130 dpi page opened. No missing glyph, overlap, clipping or broken table observed; changed availability page is 16.',
    'scope': 'Source and manifest differ only in the two access paragraphs; 30 embedded images unchanged.',
    'render': 'Existing successful Word COM and bundled Poppler path reused; LibreOffice unavailable as previously documented.',
    'font_warnings': ['Symbol alias', 'ArialUnicode alias'],
    'warning_assessment': 'Warnings persisted from prior renderer; actual equations, symbols and prose readable in all final pages.',
    'outputs': [identity(HERE / ('manuscript.' + x)) for x in ('md','docx','pdf')],
    'builders': [identity(HERE / x) for x in ('prepare.py','build_docx.py','record_build.py')],
    'data_handling': 'Final files local; remote sync pending next authorized research session. Page PNGs and duplicate exported PDF are temporary; 24 formula images are build inputs.'
}
(HERE / 'build/visual-review.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'pages':len(doc.pages),'scope_blocks':different,'embedded_images_equal':len(images),'local_links_valid':True}))
