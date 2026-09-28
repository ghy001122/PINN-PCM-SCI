"""Record the inputs actually consumed by this revision's document build."""
from pathlib import Path
import hashlib,json,re,sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def identity(path):
    return dict(path=path.relative_to(ROOT).as_posix(),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size)

def main():
    old=json.loads((HERE.parent/'paper_revision_20260926_core/build-dependencies.json').read_text(encoding='utf-8'))
    historical={Path(x['path']).name:x.get('immediate_source') for x in old['review_build_inputs']}
    sources=[HERE/'source'/f'{n}.md' for n in ('manuscript','supplement')]
    inputs=set(sources+[HERE/'references.md'])
    for source in sources:
        text=source.read_text(encoding='utf-8')
        inputs.update(HERE/'tables'/f'{n}.md' for n in re.findall(r'\{\{TABLE:([^}]+)\}\}',text))
        inputs.update(HERE/p for p in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',text))
    records=[]
    for path in sorted(inputs):
        value=identity(path)
        if path.name in historical:value['historical_asset_source']=historical[path.name]
        records.append(value)
    builders=[HERE/'prepare_document.py',HERE/'build_docx.py',HERE.parent/'advisor_review_20260924/render_with_word.ps1']
    value=dict(authoritative_text=['source/manuscript.md','source/supplement.md'],
        review_build_inputs=records,builders=[identity(p) for p in builders],
        equations='Regenerated from the same Markdown formulas by prepare_document.py; DOCX equations are embedded images, with editable formula source in Markdown.',
        pdf_derivation='Installed Microsoft Word exports the final DOCX. No separately authored PDF text.',
        runtime=dict(numeric_and_markdown_preparation='Project Python 3.11 with NumPy, SciPy and Matplotlib',
            docx='Bundled Python 3.12.14 with python-docx 1.2.0 and Pillow',
            pdf='Installed Microsoft Word COM; bundled Poppler at 130 dpi',
            visual_QA='Rendered page PNGs, project PyMuPDF and Pillow; see build/visual-review.json'),
        renderer_fallback='The unchanged Windows environment previously failed bundled render_docx.py because LibreOffice was absent (paper/paper_revision_20260926_core/build/packaged-render.log). This revision directly reused the working Microsoft Word/Poppler renderer; no new LibreOffice claim or dependency installation.',
        scientific_regeneration=dict(
            historical=old['scientific_regeneration'],
            this_revision='No historical scientific regeneration. Manuscript display rows verified from existing CSV. source/supplement.md is byte-identical to the prior revision.',
            circuit_screen='Separate report: fixed saved-array PCHIP analysis; see circuit-screen/execution-score.json and scoring-source.py. No new trajectory or network evaluation.'),
        outputs={})
    for name in ('manuscript','supplement'):
        for ext in ('md','docx','pdf'):
            path=HERE/f'{name}.{ext}'
            if not path.is_file():raise FileNotFoundError(path)
            value['outputs'][path.name]=identity(path)
    (HERE/'build-dependencies.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print('RECORDED_ACTUAL_DOCUMENT_INPUTS',len(records),flush=True)

if __name__=='__main__':main()
