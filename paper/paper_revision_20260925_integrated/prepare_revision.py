"""Prepare one continuous manuscript from existing, closed evidence only."""
from pathlib import Path
import csv
import json
import re
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = HERE.parent / 'paper_revision_20260921'
MOM = HERE.parent / 'phase_moments_20260923'
OBS = HERE.parent / 'observation_preserving_phase_20260924'


def write(name, text):
    p = HERE/name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')


def main():
    if (HERE/'source/manuscript.md').exists():
        raise FileExistsError('Prepared source exists; edit that source, do not regenerate it.')
    for folder in ('tables', 'figures'):
        shutil.copytree(OLD/folder, HERE/folder)
    for name in ('references.md', 'references.bib', 'prepare_document.py', 'build_pdf.py'):
        shutil.copy2(OLD/name, HERE/name)
    text = (OLD/'source/manuscript.md').read_text(encoding='utf-8')
    abstract = '''A final electrical solve can repair terminal outputs while leaving inaccurate internal states unchanged. We examine how this constraint should participate in learning temperature and phase in a synthetic two-dimensional electrothermal device. A partially eliminated PINN solves the grounded electrical problem during training and uses the same face resistances for local Joule deposition. Soft PINN and interpolation controls receive the same final electrical solve. Four paired full-label fits on two separately reconstructed protocols retain the complete device-advantage criterion under three numerical references and two readers; current and power error reductions over the soft controls are 47.03-76.52% and 47.86-77.50% with the spatial reference and finer reader. Strong interpolation supplies a ranking counterexample, and matched controls do not establish added reconstruction value from the thermal/phase interior residual package. A complete second-cycle phase gap and subsequent bounded phase-correction tests retain this limitation. In a common-measure diagnostic, an observation-preserving neural correction lowers its scalar physical objective by 89.91% while increasing the raw phase-residual square 10.32-fold. Thus objective reduction and repaired ports cannot substitute for separately evaluated dynamic consistency. The results support a tested electrical-interface configuration and delimit its attribution; they do not establish neural-specific phase completion, strict two-cycle usability, formal out-of-distribution generalization or material validation.'''
    text = re.sub(r'(## Abstract\n\n).*?(\n\nKeywords:)', lambda m:m[1]+abstract+m[2], text, flags=re.S)
    text = text.replace('Dense support fields, reference fields, reference currents or heating, and sealed stress cases do not enter training or model selection.', 'Dense support fields, reference fields, reference currents or heating, and sealed stress cases do not enter these training losses or within-run endpoint selection. Published reference evaluations informed subsequent research questions and interpretation; the overall development process is not claimed to be reference-blind.')
    text = text.replace('the S and phase-RMS improvements must meet the inherited 10% or absolute-floor requirements', 'each of the S and phase-RMS improvements must satisfy E_control - E_candidate >= max(0.1 E_control, absolute_tolerance)')
    text = text.replace('## 5. Additional dynamic residuals: full-label and phase-gap tests', '## 5. Dynamic residual increments and failure diagnostics')
    insert = '''### 5.4 Bounded corrections and equation-wise diagnostics

Two later development questions retain the same synthetic physical object but have distinct parents and budgets. An eight-arm relative-residual/time-moment study does not establish its prescribed phase-gap increment; its eight arms share one parent and are not eight independent initializations. The combined RIM candidate improves phase RMS by 1.918% and set error by 2.202% over its matched D control, below the inherited practical requirements. These effects must not be pooled with the earlier B1 comparisons or interpreted as a cross-round learning curve. Supplement S21 retains every arm, raw audit and event record.

A separate fixed-parent study restricts neural N and spline S corrections to the dark interval D=[1.36,2.02], preserving the base temperature and port predictions and leaving phase unchanged outside D. General correction G is the direct unrestricted-support control. None establishes the prescribed completion increment or independent equation-wise qualification. N reduces the window set error by 34.21% while increasing phase RMS by 7.95%; unchanged ports therefore do not identify the hidden phase trajectory. These are changes in predictions, not new evidence of their accuracy.

For B0, the accepted N-Adam checkpoint, N-final and S-final, a subsequent zero-update diagnostic compares the same time nodes, spatial cells and boundary samples. At common 256-node temporal quadrature, N-final lowers H by 89.9073% while its raw phase-residual square becomes 10.3157 times B0. On a second spatial support these values are 80.7961% and 13.4327 times, respectively. The decomposition H=J_phi/75+J_T/48+5 B_phi shows compensation between boundary and dynamic terms. The tested 128-to-256 temporal refinement changes each integrated component by less than 0.029%, whereas the spline boundary term depends strongly on spatial coverage. This is a directly observed objective/qualification mismatch, not an isolated proof of the complete optimization failure mechanism or a general claim about L-BFGS.

The temperature-implied phase trajectory under exact thermal balance violates phase-range and endpoint conditions on the checked support. Its thermal-square lower bound is about 21.615% of the same-support base value, which does not exclude improvement within the allowed 105% thermal budget. The base itself belongs to that tolerance set. What remains unresolved is an attainable improvement satisfying the original support, range, endpoint and equation-wise conditions, followed separately by improved reference reconstruction and a neural-specific benefit. Supplement S22 preserves all controls and component records.

![Scalar objective and separate physical components](figures/physics-objective-diagnostic.png)

Figure 6. Saved-checkpoint diagnostic of scalar-objective reduction and separate physical components. Temporal refinement and spatial-support changes are distinct checks; values are not mixed across supports. This figure uses the completed zero-update diagnostic, not a new training run.

'''
    text = text.replace('## 6. Physical interpretation', insert+'## 6. Physical interpretation') if '## 6. Physical interpretation' in text else text.replace('## 6.', insert+'## 6.',1)
    start = text.index('The full-label E/D_E evidence does not establish', text.index('## 7.'))
    end = text.index('### Data, code and author declarations', start)
    text = text[:start]+'''Matched full-label and phase-gap controls do not establish the expected additional dynamic-residual increment. The bounded relative-residual and observation-preserving studies retain this limitation; lower scalar loss and unchanged electrical ports do not establish a qualified internal phase reconstruction. Strict two-cycle usability remains unestablished. The evidence separates a configuration-level benefit from unresolved algorithmic, generalization and material claims.

'''+text[end:]
    start = text.index('The curated repository at',text.index('### Data, code'))
    end = text.index('Full arrays have not', start)
    text = text[:start]+'''The curated repository through [commit e2e14b5](https://github.com/ghy001122/PINN-PCM-SCI/tree/e2e14b5ce390de930646e1cba9a606a8191cff80) includes selected manuscript, B1, bounded-correction and diagnostic evidence. This integrated review version and its new conditional diagnostic are a subsequent local delivery. The full prediction/reference arrays remain local. The portable packages retain 72 core, 18 historical continuation and 42 B1 reference/reader records; these counts are not independent replications. The completed core arithmetic reproduction checked 8,868 scalar, identity and Boolean entries at rtol=2e-10 and atol=2e-12 with exact categorical agreement. Array rescoring, figure rebuilding, new model inference and retraining are distinct reproduction levels. No independent external retraining is claimed. The accompanying evidence map identifies the actual source records and figure inputs.

'''+text[end:]
    write('source/manuscript.md',text)
    supp = (OLD/'source/supplement.md').read_text(encoding='utf-8')
    extras = '''## S21. Complete relative-residual and time-moment development

All eight arms share one declared parent. None establishes the predeclared A_w increment; all strict two-cycle tests fail. Numerical quadrature checks passed. These results are bounded development evidence, not independent confirmations. Tables S21a-S21c retain continuous metrics, event records and actual work. Full pairwise, endpoint-moment, quadrature and raw-physics records remain linked in the evidence map.

{{TABLE:moments-metrics}}

{{TABLE:moments-events}}

{{TABLE:moments-cost}}

## S22. Observation-preserving controls and saved-checkpoint diagnosis

The base is old B1 E/29. G, N and S each use 600 Adam updates and 200 complete L-BFGS evaluations. They do not establish completion or independent physical qualification. N/S preserve temperature and electrical predictions by construction; this is not an accuracy or acceleration claim. All three training branches actually ran on CPU; subsequent audits/readouts used GPU. Failed engineering attempts and effective work remain in the original execution report. The objective diagnostic later used zero optimizer updates and zero electrical solves.

{{TABLE:completion-metrics}}

{{TABLE:completion-events}}

{{TABLE:completion-cost}}

{{TABLE:diagnostic-components}}

For full-precision records, full-history/reader metrics, all pairwise decisions, raw physics, phase-error decomposition, work deviations and source identities, see the accompanying evidence map. No favorable checkpoint replaces an accepted endpoint. The diagnostic separates the two spatial supports and temporal quadrature orders; a change of measure is not a new independent replicate.

## S23. Fixed-temperature conditional phase evolution

This section is reserved for the authorized, bounded two-step-size conditional evolution and will be completed from its accepted output or explicit numerical stop. No result is asserted during manuscript preparation.

'''
    supp=supp.replace('## References\n\n{{REFERENCES}}',extras+'## References\n\n{{REFERENCES}}')
    write('source/supplement.md',supp)
    shutil.copy2(OBS/'figures/physics-objective-diagnostic.png',HERE/'figures/physics-objective-diagnostic.png')
    assets={}
    for prefix,folder in [('moments',MOM),('completion',OBS)]:
        for suffix,file in [('metrics','all-metrics.csv'),('events','both-cycle-events.csv'),('cost','actual-training-cost.csv')]:
            rows=list(csv.reader((folder/file).open(encoding='utf-8-sig',newline='')))
            # Display a compact projection; complete unchanged CSV remains alongside it.
            shutil.copy2(folder/file,HERE/'tables'/f'{prefix}-{suffix}.csv')
            if suffix=='metrics':
                keys=[x for x in ['arm','role','scope','S','Ephi','ET','EV','EI','bottom_current_NRMSE','power_trace_NRMSE'] if x in rows[0]]
            elif suffix=='events':
                keys=[x for x in rows[0] if any(y in x.lower() for y in ['arm','role','cycle','onset','recall','precision','strict','passed'])][:9]
            else:keys=rows[0][:8]
            if not keys:keys=rows[0][:8]
            ix=[rows[0].index(k) for k in keys]
            tab=[keys]+[[r[i] for i in ix] for r in rows[1:]]
            write(f'tables/{prefix}-{suffix}.md','| '+' | '.join(tab[0])+' |\n|'+'---|'*len(keys)+'\n'+'\n'.join('| '+' | '.join(r)+' |' for r in tab[1:])+'\n')
            assets[f'{prefix}-{suffix}']={'source':str((folder/file).relative_to(ROOT)),'columns':keys,'complete_csv':f'tables/{prefix}-{suffix}.csv'}
    shutil.copy2(OBS/'physics-objective-components.csv',HERE/'tables/diagnostic-components.csv')
    rows=list(csv.DictReader((OBS/'physics-objective-components.csv').open(encoding='utf-8-sig')))
    keys=[k for k in ['pool','state','n_times','phase_raw','thermal_raw','phase_BC','H'] if k in rows[0]]
    write('tables/diagnostic-components.md','| '+' | '.join(keys)+' |\n|'+'---|'*len(keys)+'\n'+'\n'.join('| '+' | '.join(str(r[k]) for k in keys)+' |' for r in rows)+'\n')
    write('table-source-map.json',json.dumps(assets,indent=2))
    write('claim_evidence_matrix.md','''# Claim and evidence map

| Manuscript use | Comparison and measure | Source and complete evidence |
|---|---|---|
| Four full-label E/F device benefits | Two protocols, two reused seeds, three references, two readers; paired fixed endpoints | [original complete map](../paper_revision_20260921/claim_evidence_matrix.md); inherited full-label and sensitivity tables |
| B_E counterexample and D_E boundary | Same reference/reader per row; B_E does not use V labels, D_E retains electrical physics | inherited P04 table, clean-PDE tables and S17 |
| B1 phase gap and both events | W=[1.01,2.02], two initializations; 12 conditions are not 12 independent runs | inherited S20 and B1 complete comparison/event tables; [port-trace index](../paper_revision_20260921/tables/b1-port-trace-index.csv) |
| Eight-arm bounded development | Shared parent, original A_w and strict rules | [all metrics](../phase_moments_20260923/all-metrics.csv), [all pairwise decisions](../phase_moments_20260923/all-pairwise-decisions.csv), [raw audit](../phase_moments_20260923/raw-physics-audit.csv), [quadrature](../phase_moments_20260923/endpoint-quadrature.csv), [complete report](../phase_moments_20260923/results.md) |
| N/G/S prediction invariance and failure | Old B1 E/29; retain endpoint, window/full scope and original reference | [complete metrics](../observation_preserving_phase_20260924/all-metrics.csv), [pairwise](../observation_preserving_phase_20260924/all-pairwise-decisions.csv), [events](../observation_preserving_phase_20260924/both-cycle-events.csv), [deviations](../observation_preserving_phase_20260924/validation-and-deviations.md) |
| Scalar objective versus equation-wise qualification | B0/N-Adam/N-final/S-final on each separately named common support; 128/256 temporal nodes | [full-precision components](../observation_preserving_phase_20260924/physics-objective-components.csv), [per-time rows](../observation_preserving_phase_20260924/physics-objective-time-components.csv), [source figure builder](../observation_preserving_phase_20260924/build_diagnostic_report.py) |
| Historical continuation and all adverse outcomes | Six fixed historical states, no pooling with new parents | inherited S10-S13, complete 18-record extension; not re-executed |
| Conditional IVP | B0/coarse/fine, full 80x40, D only, paired thermal conventions | pending actual bounded run; no claim during preparation |

VERIFIED describes saved numerical facts. SUPPORTED_INTERPRETATION describes bounded explanations and research recommendations. Feasibility of the original C2 family, neural-specific value and material validation remain UNKNOWN. Historical sources and this new manuscript remain separately identifiable.
''')
    write('revision-response.md','''# Implemented manuscript integration

W uses one Markdown source per document and derives review formats from it. The abstract and conclusions now distinguish the positive electrical-configuration evidence, strong counterexamples and bounded failure diagnostics. Section 3.7 states the max rule explicitly. Section 5 integrates the distinct later development questions without a cross-round performance curve. Complete adverse tables and source links are retained. Reference use in training is distinguished from development use. Current public condensed evidence is distinguished from local full arrays. Physical phase and Joule panels are retained. A is supplementary by default and cannot block W.
''')
    write('README.md','''# Integrated manuscript and conditional evolution

Task PCM-20260925-INTEGRATED-MANUSCRIPT-FEASIBILITY-02 is authorized for W+A. Manuscript sources and the evidence map are prepared before conditional evolution. Review formats and the actual conditional outcome will be finalized after bounded execution. Prior frozen directories remain unchanged. This task authorizes no Git/data publication or submission.
''')
    print('CONTINUOUS_W_SOURCES_PREPARED')


if __name__=='__main__':main()
