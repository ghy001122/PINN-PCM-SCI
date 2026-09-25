"""Editorial adjustments and display tables from unchanged historical records."""
from pathlib import Path
import csv,json
HERE=Path(__file__).resolve().parent
def readcsv(name):return list(csv.DictReader((HERE/'tables'/name).open(encoding='utf-8-sig',newline='')))
def table(name,keys,labels,rows):
    def fmt(v):
        try:return f'{float(v):.6g}'
        except (ValueError,TypeError):return str(v)
    (HERE/'tables'/f'{name}.md').write_text('| '+' | '.join(labels)+' |\n|'+'---|'*len(keys)+'\n'+'\n'.join('| '+' | '.join(fmt(r.get(k,'')) for k in keys)+' |' for r in rows)+'\n',encoding='utf-8')
mapping=json.loads((HERE/'table-source-map.json').read_text())
for prefix in ('moments','completion'):
    for suffix,keys,labels in [
        ('metrics',['arm','scope','S','Ephi','ET','bottom_current_NRMSE','power_trace_NRMSE'],['Arm','Scope','S','Phase RMS','T NRMSE','I NRMSE','P NRMSE']),
        ('events',['arm','cycle','event_time','timing_absolute','recall','precision','mass_ratio'],['Arm','Cycle','Onset','Time error','Recall','Precision','Mass ratio']),
        ('cost',['arm','adam_updates','lbfgs_evaluations','training_seconds','forward_solves','adjoint_solves'],['Arm','Adam','L-BFGS eval.','Train s','Forward solves','Adjoint solves'])]:
        rows=readcsv(f'{prefix}-{suffix}.csv');table(f'{prefix}-{suffix}',keys,labels,rows)
        mapping[f'{prefix}-{suffix}'].update(columns=keys,display_headers=labels)
(HERE/'table-source-map.json').write_text(json.dumps(mapping,indent=2),encoding='utf-8')
p=HERE/'source/manuscript.md';s=p.read_text(encoding='utf-8')
s=s.replace('each of the S and phase-RMS improvements must satisfy E_control - E_candidate >= max(0.1 E_control, absolute_tolerance), while T, top-current and potential retain their original 5% noninferiority guards.', 'each of the S and phase-RMS improvements must satisfy\n\n$$ E_{\\mathrm{control}}-E_{\\mathrm{candidate}}\\geq\\max(0.1E_{\\mathrm{control}},\\epsilon_{\\mathrm{abs}}). $$\n\nThe absolute floor is the corresponding inherited tolerance. T, top-current and potential retain their original 5% noninferiority guards.')
rows=readcsv('b1-all-comparisons.csv');effects=[]
for comparison in ('E_vs_D_E','E_vs_F','E_vs_B_E'):
    for seed in ('29','43'):
        subset=[r for r in rows if r['comparison']==comparison and r['seed']==seed]
        assert len(subset)==6,(comparison,seed,len(subset))
        row={'comparison':comparison.replace('E_vs_','E / '),'seed':seed}
        for field in ('Ephi','S','bottom_current_NRMSE','power_trace_NRMSE'):
            values=[100*float(r[f'window_effects.{field}.relative_error_reduction']) for r in subset]
            row[field]=f'{min(values):.2f} to {max(values):.2f}'
        effects.append(row)
table('b1-continuous-ranges',['comparison','seed','Ephi','S','bottom_current_NRMSE','power_trace_NRMSE'],['Comparison','Seed','Phase reduction %','Set reduction %','Current reduction %','Power reduction %'],effects)
anchor='All E/F and E/B_E comparisons, complete cycle metrics'
if 'TABLE:b1-continuous-ranges' not in s:
    start=s.index(anchor)
    s=s[:start]+'''Table 5. Continuous B1 window effects across the three references and two readers. Each range summarizes six sensitivity conditions for one initialization; positive reduction means smaller E error. It does not establish the full window criterion.

{{TABLE:b1-continuous-ranges}}

The spatial-reference event records separate port and support behavior. Both E and D_E recover a second event, whereas both repaired F states and the shared B_E miss it. Second-cycle ROI recall is 0.7799/0.7738 for E/D_E at seed 29 and 0.8061/0.8010 at seed 43, below the 0.9 requirement. E second-event timing errors are 0.00450 and 0.00771, respectively. Thus substantially improved window ports and recovery of an event can coexist with failure of the phase and strict two-cycle criteria. The complete first/second-event records, including support extent, precision and recovery, are retained in Supplement S20.

'''+s[start:]
p.write_text(s,encoding='utf-8')
p=HERE/'source/supplement.md';s=p.read_text(encoding='utf-8').replace('Tables S20a-S20c','Tables S21a-S21c')
captions={'moments-metrics':'Table S21a. All eight arms and both scoring ranges. Full electrical fields remain in the unchanged CSV. Errors are dimensionless, not percentages.',
 'moments-events':'Table S21b. Both event cycles for every arm. These arms share one parent.',
 'moments-cost':'Table S21c. Actual training work. Optimizer evaluations and electrical solves are separate work units.',
 'completion-metrics':'Table S22a. B0 and all N/G/S accepted endpoints, with both scoring ranges. Errors are dimensionless.',
 'completion-events':'Table S22b. Both event cycles, including missing events and support errors.',
 'completion-cost':'Table S22c. Actual training work for all three branches; these historical runs used CPU.',
 'diagnostic-components':'Table S22d. Every saved checkpoint, spatial pool and temporal quadrature in the zero-update diagnostic. Phase and thermal columns are raw mean-square residuals; H is the original composite objective.'}
for name,caption in captions.items():
    token='{{TABLE:'+name+'}}'
    if caption not in s:s=s.replace(token,caption+'\n\n'+token)
s=s.replace('Historical words such as', 'S21-S22 integrate the complete later bounded corrections and saved-checkpoint diagnostic. S23 reports the fixed-temperature conditional evolution. Historical words such as')
p.write_text(s,encoding='utf-8')
p=HERE/'claim_evidence_matrix.md';s=p.read_text(encoding='utf-8').replace('inherited S18/S19 and B1','inherited S20 and B1');p.write_text(s,encoding='utf-8')
p=HERE/'prepare_revision.py';s=p.read_text(encoding='utf-8').replace('Its best combined neural candidate','The combined RIM candidate').replace('Supplement S20 retains every arm','Supplement S21 retains every arm').replace('Supplement S21 preserves all controls','Supplement S22 preserves all controls').replace('## S20. Complete relative-residual','## S21. Complete relative-residual').replace('Tables S20a-S20c','Tables S21a-S21c').replace('## S21. Observation-preserving','## S22. Observation-preserving').replace('## S22. Fixed-temperature','## S23. Fixed-temperature').replace('inherited S18/S19 and B1','inherited S20 and B1');p.write_text(s,encoding='utf-8')
p=HERE/'build_pdf.py';s=p.read_text(encoding='utf-8').replace('Phase-gap revision, 21 September 2026','Integrated revision, 25 September 2026');p.write_text(s,encoding='utf-8')
print('Editorial tables and continuous B1 effects updated from saved records.')
