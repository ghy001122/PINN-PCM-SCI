"""Check manuscript preservation, resolved inputs and numerical provenance."""
from pathlib import Path
from collections import Counter
import json
import re

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'paper_revision_20260929_72h'

def content(root, name):
    text = (root/'source'/f'{name}.md').read_text(encoding='utf-8')
    for token, file in [('AUXILIARY_SECTION','auxiliary-section.md'),('JOINT_RESULT_SECTION','joint-result-section.md')]:
        text = text.replace('{{'+token+'}}',(root/'source'/file).read_text(encoding='utf-8'))
    return text

def equations(text):
    return Counter(re.sub(r'\s+',' ',s).strip() for s in re.findall(r'\$\$(.*?)\$\$',text,re.S))

def images(text):
    return set(re.findall(r'!\[[^\]]*\]\(([^)]+)\)',text))

old_text = {name:content(OLD,name) for name in ('manuscript','supplement')}
new_text = {name:content(HERE,name) for name in old_text}
assert equations(old_text['manuscript']) == equations(new_text['manuscript']), 'Changed primary equations'
assert not (equations(old_text['supplement']) - equations(new_text['supplement'])), 'Lost supplementary equations'
old_images = set().union(*(images(t) for t in old_text.values()))
new_images = set().union(*(images(t) for t in new_text.values()))
assert old_images <= new_images, ('Lost scientific figures',old_images-new_images)
assert 'figures/electrical-interface-effects.png' in new_images

refs = (HERE/'references.md').read_text(encoding='utf-8')
defined = set(re.findall(r'^\[(\d+)\]',refs,re.M))
citations = set(re.findall(r'(?<!!)\[(\d+)\]', '\n'.join(new_text.values())))
assert citations <= defined, ('Missing references',citations-defined)
broken=[]
for name in new_text:
    expanded=(HERE/f'{name}.md').read_text(encoding='utf-8')
    assert not re.search(r'\{\{(?:TABLE:|REFERENCES|AUXILIARY_SECTION|JOINT_RESULT_SECTION)',expanded), ('Unexpanded source',name)
    for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',expanded):
        if re.match(r'https?://|mailto:|#',target):continue
        if not (HERE/target.split('#',1)[0]).exists():broken.append((name,target))
assert not broken, ('Broken local artifact links',broken)
result=dict(status='PASS',main_equations_unchanged=sum(equations(new_text['manuscript']).values()),
            supplementary_equations_preserved=sum(equations(old_text['supplement']).values()),
            historical_figure_inputs_preserved=len(old_images),new_figure_inputs=len(new_images-old_images),
            citations_resolve=True,local_artifact_links_resolve=True,scientific_reruns=0)
(HERE/'build/source-check.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
