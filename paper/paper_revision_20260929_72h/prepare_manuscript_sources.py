"""Assemble existing evidence and manuscript sources without scientific execution."""
from pathlib import Path
import csv
import hashlib
import json
import os
import re
import shutil

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
BASE = PAPER / 'paper_revision_20260927_circuit_screen'
THERMAL = PAPER / 'paper_revision_20260928_conditional_thermal'

def link(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        os.link(source, target)
    if target.read_bytes() != source.read_bytes():
        raise ValueError(f'Unchanged asset differs: {target}')

def main():
    (HERE/'source').mkdir(parents=True, exist_ok=True)
    (HERE/'tables').mkdir(exist_ok=True)
    main = (THERMAL/'manuscript/source/manuscript.md').read_text(encoding='utf8')
    supplement = (BASE/'source/supplement.md').read_text(encoding='utf8')
    old = next(p for p in main.split('\n\n') if p.startswith('For example, the VO2 thermal neuristors'))
    new = ('An auxiliary test on the distinct, fitted lumped VO2 neuristor model of Qiu et al. [19] '
           'shows why port accuracy and state consistency require separate checks (Supplement S25). '
           'From the same 197 finite voltage observations, PCHIP and cubic-spline reconstructions '
           'at 12.5 V give temperature RMS errors of 0.654 and 0.761 K against the frozen numerical '
           'source, while a native-voltage control gives 0.0189 K. Replaying the constitutive history '
           'leaves circuit-closure RMS errors of 223.27 and 243.73 μA; a closer constitutive current '
           'in another role does not remove that closure defect. The storage partition and closure '
           'identities in S25 explain these quantities without assigning causal percentages. '
           'This auxiliary numerical model is neither a calibration of the two-dimensional object '
           'nor experimental temperature validation; its joint-reconstruction comparison is reported '
           'with the same-information traditional control in S25.')
    assert main.count(old) == 1
    main = main.replace(old, new)
    access = (' The published conditional-thermal package at commit d068bdf additionally retains '
              'the forty locked thermal responses, history replays and their scoring inputs; its '
              'saved-array entry is separate from the original conditional integrations. The present '
              'revision and any new joint-reconstruction outputs are supplied locally for review '
              'and are not claimed to be publicly deposited.')
    main = main.replace('A standalone numerical package retains', access.strip()+' A standalone numerical package retains', 1)
    supplement = supplement.replace('S24 gives the mixed-measure coverage control.',
        'S24 gives the mixed-measure coverage control. S25 consolidates the separate lumped neuristor voltage, energy, conditional-temperature and history evidence, and states the joint-reconstruction experiment.')
    supplement = supplement.replace('## References\n\n{{REFERENCES}}',
        '{{AUXILIARY_SECTION}}\n\n## References\n\n{{REFERENCES}}')
    (HERE/'source/manuscript.md').write_text(main,encoding='utf8')
    (HERE/'source/supplement.md').write_text(supplement,encoding='utf8')
    for filename in ('references.md','build_docx.py'):
        shutil.copyfile(BASE/filename,HERE/filename)
    builder=(HERE/'build_docx.py').read_text(encoding='utf8')
    builder=builder.replace('Circuit screen revision 28 September 2026', 'Joint reconstruction revision 29 September 2026')
    (HERE/'build_docx.py').write_text(builder,encoding='utf8')
    for text in (main,supplement):
        for name in re.findall(r'\{\{TABLE:([^}]+)\}\}',text):
            link(BASE/'tables'/(name+'.md'), HERE/'tables'/(name+'.md'))
        for path in re.findall(r'\]\(((?:figures|tables)/[^)]+)\)',text):
            link(BASE/path,HERE/path)
    # Copy existing numerical summaries only; no new rescore or conditional solve.
    temperatures=list(csv.DictReader((THERMAL/'results/temperature.csv').open(encoding='utf8',newline='')))
    closure=list(csv.DictReader((THERMAL/'results/closure.csv').open(encoding='utf8',newline='')))
    selected=[r for r in closure if r['window']=='full' and float(r['dt_s'])==5e-10]
    rows=[]
    names={'single_9V':'9 V','single_12p5V':'12.5 V','single_15p8V':'15.8 V','pair_excitation':'Excitation','pair_inhibition':'Inhibition'}
    for r in selected:
        t=next(x for x in temperatures if x['id']==r['id'] and x['device']==r['device'] and x['window']=='full' and x['method']==r['method'])
        v=next(x for x in temperatures if x['id']==r['id'] and x['device']==r['device'] and x['window']=='full' and x['method']=='V_ref')
        rows.append({'role':names[r['case']]+'/'+r['device'],'method':r['method'],'T_RMS_K':float(t['rms_K']),
                     'Vref_T_RMS_K':float(v['rms_K']),'IKCL_RMS_uA':float(r['I_KCL_rms_A'])*1e6,
                     'IR_RMS_uA':float(r['I_R_rms_A'])*1e6,'closure_RMS_uA':float(r['closure_rms_A'])*1e6,
                     'IKCL_min_uA':float(r['I_KCL_min_A'])*1e6})
    with (HERE/'tables/neuristor-all-roles.csv').open('w',encoding='utf8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    header=['Role','Method','T RMS K','V ref T RMS K','KCL RMS μA','R law RMS μA','Closure RMS μA','Min KCL μA']
    lines=['| '+' | '.join(header)+' |','|'+'---|'*len(header)]
    for r in rows:
        vals=[r['role'],r['method']]+[f'{v:.6g}' for v in list(r.values())[2:]]
        lines.append('| '+' | '.join(vals)+' |')
    (HERE/'tables/neuristor-all-roles.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    for name in ('single_12p5V-fixed-first-peak.png','conditional-single_12p5V-A.png'):
        link(THERMAL/'figures'/name,HERE/'figures'/name)
    print(json.dumps({'main':str(HERE/'source/manuscript.md'),'supplement':str(HERE/'source/supplement.md'),'all_role_rows':len(rows),'historical_reruns':0}))

if __name__=='__main__':main()
