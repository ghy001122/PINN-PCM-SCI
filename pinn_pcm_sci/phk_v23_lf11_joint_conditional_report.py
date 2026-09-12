"""Saved-evidence figures and packaging for the optional electrical-block test."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import shutil
import numpy as np

from .phk_v23_lf11 import ROOT
from .phk_v23_lf11_joint import RUN


def render(root=RUN/'conditional',paper=ROOT/'paper/paper_v27'):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    root,paper=Path(root),Path(paper)
    first=json.loads((root/'evaluation.json').read_text())
    has_dn=(root/'dn/evaluation.json').exists()
    final=json.loads((root/'dn/evaluation.json').read_text()) if has_dn else first
    records=final['records'];names=['R','G','N']+(['D_N'] if has_dn else [])+['B_logit_waveform_contact']
    valid=[n for n in names if records[n]['valid']]
    colors={'R':'#e41a1c','G':'#ff7f00','N':'#377eb8','D_N':'#4daf4a','B_logit_waveform_contact':'#984ea3'}
    labels={'B_logit_waveform_contact':'Contact baseline'}
    destination=paper/'figures';destination.mkdir(parents=True,exist_ok=True)
    fig,axes=plt.subplots(2,3,figsize=(12,7.2),constrained_layout=True)
    pairs=(('S','Phase symmetric difference'),('Ephi','Phase RMS (raw)'),('ET','Temperature RMS / 0.45'),
           ('bottom_current_NRMSE','Bottom-current NRMSE'),('power_trace_NRMSE','Joule-power trace NRMSE'),('EI','Top-current NRMSE'))
    for ax,(key,title) in zip(axes.flat,pairs):
        ax.bar(np.arange(len(valid)),[records[n]['metrics'][key] for n in valid],color=[colors[n] for n in valid])
        ax.set_xticks(np.arange(len(valid)),[labels.get(n,n) for n in valid],rotation=25,ha='right')
        ax.set_title(title);ax.set_ylim(bottom=0);ax.grid(axis='y',alpha=.2)
        ax.ticklabel_format(axis='y',style='sci',scilimits=(-3,3))
    fig.suptitle('Conditional matched electrical-block test: raw, global scalar, normalization',fontsize=12)
    for ext in ('png','pdf'):fig.savefig(destination/('lf11-joint-normalization.'+ext),dpi=200)
    plt.close(fig)
    table=paper/'tables';table.mkdir(exist_ok=True)
    keys=sorted({k for n in names for k in (records[n].get('metrics') or {})})
    with (table/'conditional-endpoints.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['role','valid','strict_device_pass']+keys);writer.writeheader()
        for n in names:writer.writerow({'role':n,'valid':records[n]['valid'],
            'strict_device_pass':records[n].get('strict_device_pass',False),**(records[n].get('metrics') or {})})
    lines=['# Conditional electrical-block contrasts','',
           'R reuses the raw Adam1000 prefix and adds exactly its own fixed 200-evaluation endpoint. The main P_U endpoint has a different budget and is not R.',
           '', '| Contrast | Reconstruction A | Limited function B |','|---|---|---|']
    for stage in [first]+([final] if has_dn else []):
        for name,row in stage['matched_pairs'].items():
            lines.append(f'| {name} | {row["reconstruction"]["passed"]} | {row["function"]["passed"]} |')
    lines+=['','D_N execution: '+('completed under its conditional trigger.' if has_dn else 'not triggered; not a failed run.'),'',
            'The two outcome layers remain separate. A change in the normalized objective alone does not establish a phase or device increment.']
    (table/'conditional-contrasts.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    lines=['# Conditional two-cycle events','','| Role | Cycle | Recall | Precision | Mass ratio | Timing absolute |','|---|---:|---:|---:|---:|---:|']
    for name in names:
        for i,c in enumerate(records[name].get('cycles',[])):
            lines.append(f'| {name} | {i+1} | '+' | '.join('None' if c[k] is None else f'{c[k]:.9g}' for k in ('recall','precision','mass_ratio','timing_absolute'))+' |')
    (table/'conditional-events.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def package(root=RUN/'conditional',paper=ROOT/'paper/paper_v27'):
    root,paper=Path(root),Path(paper)
    target=paper/'evidence/conditional';target.mkdir(parents=True,exist_ok=True)
    stages=[(root,target)]+([(root/'dn',target/'dn')] if (root/'dn/evaluation.json').exists() else [])
    for source,dest in stages:
        dest.mkdir(exist_ok=True)
        for name in ('frozen-config.json','normalization.json','calibration.json','training-source.json',
                     'trigger-provenance.json','campaign.json','compute-closure.json','evaluation.json',
                     'evaluation-traces.npz','followup-decision.json'):
            if (source/name).exists():shutil.copy2(source/name,dest/name)
        campaign=json.loads((source/'campaign.json').read_text())
        for role in campaign['results']:
            folder=dest/role;folder.mkdir(exist_ok=True)
            for name in ('result.json','checkpoint.pt','invalid-checkpoint.pt','adam-telemetry.jsonl',
                         'lbfgs-telemetry.jsonl','boundary-subterms.json'):
                if (source/role/name).exists():shutil.copy2(source/role/name,folder/name)
            audits=dest/'electric_audit';audits.mkdir(exist_ok=True)
            for ext in ('json','npz'):
                name=role+'.'+ext
                if (source/'electric_audit'/name).exists():shutil.copy2(source/'electric_audit'/name,audits/name)
    (target/'README.md').write_text('''# Conditional electrical-block evidence

This directory records the actual conditional decision, once-only blind calibration, fixed endpoints and accepted optimizer states. The common parent and fixed pools are shared exactly with the main evidence one directory above; their duplicate binary copies are omitted here. Intermediate G/N states and full own-field predictions remain in the original run.

R reuses the exact original P_U Adam1000 state, then performs its own fresh 200 complete fixed L-BFGS evaluations. Reused Adam updates are not counted as new execution. G and N each start from the common parent, with fresh 1000-Adam/200-evaluation trajectories. A later D_N batch exists only if the saved R/G/N decision authorized it. Read the actual campaign and followup-decision files; implementation availability is not evidence that a branch ran or succeeded.

All full-reference endpoint evaluations follow termination of their training workers. No stress data, extra observations, new physics, or independent initialization are used. Results inherit the exposed nominal-case scope.

Rebuild the conditional figure and tables from this package without training or reference access:

```powershell
.\\.venv\\Scripts\\python.exe -m pinn_pcm_sci.phk_v23_lf11_joint_conditional_report --root paper/paper_v27/evidence/conditional --paper outputs/reproduction/lf11-joint-conditional-figures
```
''',encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RUN/'conditional')
    p.add_argument('--paper',type=Path,default=ROOT/'paper/paper_v27')
    a=p.parse_args();render(a.root,a.paper)
