"""Build render manifests from the authoritative Markdown and saved evidence."""
from pathlib import Path
import hashlib
import json
import os
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
BUILD=HERE/'build'
(BUILD/'equations').mkdir(parents=True,exist_ok=True)

def canonical(formula):
    return re.sub(r'\s+',' ',formula).strip()

cache={}
for prior in ('paper_revision_20260927_circuit_screen','paper_revision_20260928_conditional_thermal/manuscript'):
    record=json.loads((HERE.parent/prior/'build/render-manifest.json').read_text(encoding='utf8'))
    for blocks in record['documents'].values():
        for block in blocks:
            if block['type']=='equation' and Path(block['path']).is_file():
                cache[canonical(block['formula'])]=Path(block['path'])

def expand(text):
    for token,file in [('AUXILIARY_SECTION','auxiliary-section.md'),('JOINT_RESULT_SECTION','joint-result-section.md')]:
        text=text.replace('{{'+token+'}}',(HERE/'source'/file).read_text(encoding='utf8').strip())
    text=text.replace('{{REFERENCES}}',(HERE/'references.md').read_text(encoding='utf8').strip())
    text=re.sub(r'\{\{TABLE:([^}]+)\}\}',lambda m:(HERE/'tables'/(m[1]+'.md')).read_text(encoding='utf8').strip(),text)
    return text.replace('\u2011','-').replace('\u2013','-').replace('\u2014','-')

def equation(formula):
    key=canonical(formula)
    path=BUILD/'equations'/(hashlib.sha256(key.encode()).hexdigest()[:16]+'.png')
    if path.exists():return path
    if key in cache:
        os.link(cache[key],path)
        return path
    rendered=re.sub(r'\\(mathsf|mathcal|mathbb|bar)\s+([A-Za-z])',lambda m:'\\'+m[1]+'{'+m[2]+'}',formula)
    fig=plt.figure(figsize=(12,.62),dpi=220)
    fig.patch.set_alpha(0)
    text=fig.text(.015,.45,'$'+rendered+'$',fontsize=14,ha='left',va='center')
    fig.canvas.draw()
    box=text.get_window_extent().expanded(1.02,1.25)
    fig.savefig(path,bbox_inches=box.transformed(fig.dpi_scale_trans.inverted()),pad_inches=.04,transparent=True)
    plt.close(fig)
    return path

def parse(text):
    lines=text.splitlines();blocks=[];i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line.startswith('#'):
            n=len(line)-len(line.lstrip('#'));blocks.append(dict(type='heading',level=n,text=line[n:].strip()));i+=1
        elif line.startswith('$$'):
            formula=line[2:]
            while not formula.endswith('$$'):
                i+=1;formula+=' '+lines[i].strip()
            formula=formula[:-2].strip();blocks.append(dict(type='equation',path=str(equation(formula)),formula=formula));i+=1
        elif line.startswith('!['):
            m=re.fullmatch(r'!\[(.*?)\]\((.*?)\)',line)
            if not m:raise ValueError(line)
            path=(HERE/m[2]).resolve()
            if not path.is_file():raise FileNotFoundError(path)
            blocks.append(dict(type='image',path=str(path),alt=m[1]));i+=1
        elif line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',c) for c in cells):rows.append(cells)
                i+=1
            if len({len(r) for r in rows})!=1:raise ValueError(rows)
            blocks.append(dict(type='table',rows=rows))
        else:
            para=line;i+=1
            while i<len(lines) and lines[i].strip() and not lines[i].lstrip().startswith(('#','|','$$','![')):
                para+=' '+lines[i].strip();i+=1
            blocks.append(dict(type='paragraph',text=para))
    return blocks

manifest={'documents':{},'source_authority':'source/*.md with tables and references expanded; other Markdown is derived'}
for name in ('manuscript','supplement'):
    text=expand((HERE/'source'/(name+'.md')).read_text(encoding='utf8'))
    if re.search(r'\{\{(?:TABLE:|REFERENCES|AUXILIARY_SECTION|JOINT_RESULT_SECTION)',text):raise ValueError('Unexpanded include')
    (HERE/(name+'.md')).write_text(text,encoding='utf8')
    manifest['documents'][name]=parse(text)
(BUILD/'render-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:len(v) for k,v in manifest['documents'].items()}))
