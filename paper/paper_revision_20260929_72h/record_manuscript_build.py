"""Record the completed visual checks after final rendering; no science runs."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import shutil
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
BUILD=HERE/'build'
ROOT=HERE.parents[1]

def identity(path):
    return {'path':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def main():
    old=json.loads((BUILD/'supplement-pre-final-text.json').read_text(encoding='utf8'))
    reader=PdfReader(BUILD/'render-supplement-final/supplement.pdf')
    new=[page.extract_text() for page in reader.pages]
    changed=[i+1 for i,(a,b) in enumerate(zip(old,new)) if a!=b]
    assert len(new)==64 and changed==[63,64], (len(new),changed)
    same_png=[]
    for n in range(1,63):
        filename=f'page-{n:02}.png'
        a=BUILD/'render-supplement'/filename
        b=BUILD/'render-supplement-final'/filename
        assert a.read_bytes()==b.read_bytes(), filename
        same_png.append(n)
    for name,folder in [('manuscript','render-manuscript'),('supplement','render-supplement-final')]:
        source=BUILD/folder/(name+'.pdf')
        shutil.copyfile(source,HERE/(name+'.pdf'))
    manifest=json.loads((BUILD/'render-manifest.json').read_text(encoding='utf8'))
    outputs=[identity(HERE/(name+'.'+ext)) for name in ('manuscript','supplement') for ext in ('md','docx','pdf')]
    assert len(PdfReader(HERE/'manuscript.pdf').pages)==17
    assert 'in progress' not in (HERE/'source/joint-result-section.md').read_text(encoding='utf8')
    record={
        'status':'PASS','recorded_utc':datetime.now(timezone.utc).isoformat(),
        'manuscript':{'pages':17,'pages_opened_individually':list(range(1,18)),
                      'reviewer':'root','findings':'No clipped text, overlap, black glyph blocks or missing content; new result paragraph on page15 and accurate access statement on page16 checked. Larger figure-page whitespace is intentional.'},
        'supplement':{'pages':64,'pages_opened_individually':list(range(1,65)),
                      'reviewers':{'thermal_kernel':list(range(1,33)),'sprint_manuscript':list(range(33,65))},
                      'findings':'All figures, equations, 62 tables and repeated headers readable; S25 all-role table, fixed 12.5V display, actual joint gates and optimizer stop retained. No clipping, overlap or missing glyphs.',
                      'final_text_patch_changed_pages':changed,'final_PNGs_bitwise_equal_to_inspected_first_render':same_png,
                      'final_changed_pages_opened_again':[63,64]},
        'render':'Existing Microsoft Word COM exporter and bundled Poppler at130dpi; LibreOffice unavailable as recorded by earlier successful pipeline',
        'font_alias_warnings':['Symbol','ArialUnicode'],
        'warning_assessment':'Visible equation images and Unicode body text checked and readable despite inherited Poppler alias warnings.',
        'outputs':outputs,
        'new_training_claim':'Fixed seed29 gate failed; seed43 not triggered; S Wolfe failure and accepted-state rollback not described as convergence.',
        'source_authority':'source/manuscript.md plus source/supplement.md and its explicit auxiliary/joint includes',
        'scientific_reruns_by_build':0,
        'data_handling':'Final artifacts local; final formatting produced after GPU shutdown and awaits later authorized remote sync. No publication.'
    }
    (BUILD/'visual-review.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
    inputs=[]
    for p in sorted((HERE/'source').glob('*.md')):inputs.append(identity(p))
    inputs.append(identity(HERE/'references.md'))
    deps={'status':'BUILT_AND_VISUALLY_VERIFIED','python_executable':'C:/Users/CJ/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
          'python_packages':{k:importlib.metadata.version(k) for k in ('python-docx','Pillow','pypdf')},
          'renderer':'Microsoft Word COM via paper/advisor_review_20260924/render_with_word.ps1',
          'pdftoppm':'C:/Users/CJ/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe',
          'sources':inputs,
          'builders':[identity(HERE/x) for x in ('prepare_document.py','build_docx.py','draw_manuscript_auxiliary.py','record_manuscript_build.py')],
          'counts':{k:{'blocks':len(v),'equations':sum(b['type']=='equation' for b in v),'scientific_figures':sum(b['type']=='image' for b in v),'tables':sum(b['type']=='table' for b in v)} for k,v in manifest['documents'].items()},
          'formula_cache':'Unchanged formulas linked by exact canonical formula; six new equations rendered once; no old formula regeneration',
          'license':'Build tools and upstream assets retain their own licenses; this record grants no new blanket publication license'}
    (BUILD/'dependencies.json').write_text(json.dumps(deps,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'status':'PASS','main_pages':17,'supplement_pages':64,'changed_final_pages':changed,'same_previously_inspected_PNGs':len(same_png)},ensure_ascii=False))

if __name__=='__main__':main()
