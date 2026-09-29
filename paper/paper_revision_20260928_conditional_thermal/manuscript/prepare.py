"""Derive an availability-only manuscript from the frozen 28 September source."""
from pathlib import Path
import difflib
import hashlib
import json
import os
import re
import shutil

HERE = Path(__file__).resolve().parent
OLD = HERE.parents[1] / 'paper_revision_20260928_circuit_comparison'
ROOT = HERE.parents[2]
TASK = 'PCM-20260928-CONDITIONAL-THERMAL-CLOSURE-01'
PUBLIC = 'https://github.com/ghy001122/PINN-PCM-SCI/tree/709b10fd28fc8fc80c9103acd68be02c35ac2816/paper/paper_revision_20260928_circuit_comparison/scoring-subset'

def identity(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def main():
    (HERE / 'source').mkdir(parents=True, exist_ok=True)
    (HERE / 'build').mkdir(exist_ok=True)
    original = (OLD / 'source/manuscript.md').read_text(encoding='utf-8')
    paragraphs = original.split('\n\n')
    first = next(p for p in paragraphs if p.startswith('The curated results published'))
    second = next(p for p in paragraphs if p.startswith('Full arrays have not been publicly uploaded'))
    replacement_first = (
        'Curated manuscript and evidence releases are publicly available in the project repository. '
        f'The [circuit V/I scoring subset at commit 709b10f]({PUBLIC}) includes ten saved numerical '
        'source-voltage/current records, finite voltage observations, locked PCHIP and cubic-spline '
        'predictions and polynomial coefficients, fixed scoring code and complete result tables. '
        'Its entry supports independent saved-array rescoring; the recorded isolated-directory rerun '
        'reproduced the circuit results exactly. This subset does not provide new ODE/PDE integration, '
        'checkpoint inference, neural AD residual evaluation or retraining. '
        + first[first.index('A standalone numerical package retains'):]
    )
    replacement_second = second.replace(
        'Full arrays have not been publicly uploaded or assigned a DOI. Public or controlled reviewer access, appropriate distribution permission and persistent archiving require author approval; the local package does not close this access gap.',
        'The separate full prediction/reference field arrays and checkpoints for the two-dimensional PINN study remain local and have no public dataset DOI. Public or controlled reviewer access, appropriate distribution permission and persistent archiving for that full-field package require author approval; publication of the circuit subset does not close the full-paper access gap (P03).'
    )
    replacements = {first: replacement_first, second: replacement_second}
    updated = original
    for before, after in replacements.items():
        assert updated.count(before) == 1
        updated = updated.replace(before, after)
    assert all(a == b for a,b in zip(original.split('\n\n'), updated.split('\n\n'))
               if a not in replacements)
    (HERE / 'source/manuscript.md').write_text(updated, encoding='utf-8')
    expanded = (OLD / 'manuscript.md').read_text(encoding='utf-8')
    normalize = lambda s: s.replace('\u2011', '-').replace('\u2013', '-').replace('\u2014', '-')
    manifest = json.loads((OLD / 'build/render-manifest.json').read_text(encoding='utf-8'))
    changed_blocks = []
    for before, after in replacements.items():
        before, after = normalize(before), normalize(after)
        assert expanded.count(before) == 1
        expanded = expanded.replace(before, after)
        matches = [i for i,b in enumerate(manifest['documents']['manuscript']) if b.get('text') == before]
        assert len(matches) == 1
        i = matches[0]
        manifest['documents']['manuscript'][i]['text'] = after
        changed_blocks.append(i)
    (HERE / 'manuscript.md').write_text(expanded, encoding='utf-8')
    (HERE / 'build/render-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    shutil.copyfile(OLD / 'build_docx.py', HERE / 'build_docx.py')
    assets = {OLD / 'references.md'}
    assets.update(OLD / 'tables' / (m + '.md') for m in re.findall(r'\{\{TABLE:([^}]+)\}\}', original))
    assets.update(OLD / m for m in re.findall(r'\]\((tables/[^)]+)\)', original))
    assets.update(Path(b['path']) for b in manifest['documents']['manuscript'] if b['type'] in ('image', 'equation'))
    linked = []
    # Keep Markdown references usable without duplicating unchanged scientific images.
    for source in sorted(assets):
        relative = source.relative_to(OLD)
        target = HERE / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            os.link(source, target)
        assert target.read_bytes() == source.read_bytes()
        linked.append(identity(target))
    diff = ''.join(difflib.unified_diff(original.splitlines(True), updated.splitlines(True),
                                      fromfile='frozen/source/manuscript.md', tofile='new/source/manuscript.md'))
    (HERE / 'build/access-only.diff').write_text(diff, encoding='utf-8')
    record = {'task_id': TASK, 'change_scope': 'Two paragraphs in Data, code and author declarations only',
              'changed_manifest_blocks': changed_blocks, 'scientific_text_unchanged': True,
              'source': identity(HERE / 'source/manuscript.md'), 'frozen_source': identity(OLD / 'source/manuscript.md'),
              'asset_inputs': [identity(p) for p in sorted(assets)],
              'linked_assets': linked, 'storage_note': 'Unchanged hardlinks are not independent backups; do not edit in place.',
              'formula_representation': '24 unchanged PNG formulas; editable source remains Markdown',
              'builder': identity(HERE / 'build_docx.py'),
              'render_pipeline': 'Reused verified Microsoft Word COM export and bundled Poppler; known unavailable LibreOffice was not retried',
              'supplement': '../../paper_revision_20260927_circuit_screen/supplement.pdf',
              'supplement_rebuilt': False, 'new_scientific_results_in_manuscript': False}
    (HERE / 'build/preparation.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'changed_paragraphs': len(replacements), 'changed_blocks': changed_blocks, 'assets': len(linked)}))

if __name__ == '__main__':
    main()
