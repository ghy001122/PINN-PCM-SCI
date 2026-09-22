"""Assemble one final revision only after B1 scoring and GPU closure."""
from pathlib import Path
import json
import re
import shutil
from report_b1 import md_write

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'paper_revision_20260918'
RUN=ROOT/'outputs/runs/20260921-b1-second-cycle-phase-gap'

def read(path):return json.loads(path.read_text(encoding='utf-8'))
def table(name):return '{{TABLE:'+name+'}}'
def figure(number,path,caption):
    return f'![Figure {number}. {caption}](figures/{path}.png)\n\nFigure {number}. {caption}\n'

def main():
    summary=read(HERE/'evidence/b1-summary.json')
    assert summary['status']=='COMPLETE_B1_SCORED_AND_RECOVERED'
    assert read(RUN/'compute-closure.json')['instance_shutdown_confirmed']
    results=read(RUN/'scoring/results.json')
    original=read(ROOT/'outputs/submission-rescore-20260921/core-rescore/results.json')
    text=(OLD/'source/manuscript.md').read_text(encoding='utf-8')
    blocks=(HERE/'manuscript-revision-blocks.md').read_text(encoding='utf-8')
    def between(start,end):return text.split(start,1)[1].split(end,1)[0].strip()
    def newblock(start,end):return blocks.split(start,1)[1].split(end,1)[0].strip()
    for folder in ('tables','figures'):
        shutil.copytree(OLD/folder,HERE/folder,dirs_exist_ok=True)
    (HERE/'source').mkdir(exist_ok=True)
    rows=[]
    for oid,value in original['records']['spatial']['fine'].items():
        parts=oid.split('/');case=parts[0];seed=parts[1] if len(parts)==3 else 'shared';role=parts[-1]
        m=value['metrics']
        rows.append([case,seed,role,m['Ephi'],100*m['bottom_current_NRMSE'],100*m['power_trace_NRMSE']])
    md_write('full-label-main.md',['Protocol','Seed','Role','Phase RMS','Current (%)','Power (%)'],rows)
    rows=[]
    for oid,value in results['windows']['spatial']['fine'].items():
        parts=oid.split('/');seed=parts[1] if len(parts)==3 else '-';role=parts[-1]
        m=value['window']['metrics']
        rows.append([seed,role,1000*m['S'],m['Ephi'],100*m['ET'],100*m['bottom_current_NRMSE'],100*m['power_trace_NRMSE']])
    md_write('b1-main.md',['Seed','Role','1000 S','Phase RMS','T (%)','Current (%)','Power (%)'],rows)
    n=summary['A_w_passed'];route=summary['scientific_route'];ranges=summary['window_relative_effect_ranges']
    outside=sum(x['outside_cost'] for x in summary['primary_comparisons'])
    costs=sorted({k for x in summary['primary_comparisons'] for k in x['outside_cost_fields']})
    secondary=[]
    for label,display in (('E_vs_F','the repaired soft PINN F'),('E_vs_B_E','the shared interpolant B_E')):
        comparisons=[pairs[str(seed)][label] for levels in results['comparisons'].values()
                     for pairs in levels.values() for seed in (29,43)]
        assert len(comparisons)==12
        window_pass=sum(x['A_w']['passed'] for x in comparisons)
        full_a=sum(x['full']['A']['passed'] for x in comparisons)
        full_b=sum(x['full']['B']['passed'] for x in comparisons)
        secondary.append(f'Against {display}, B1 E satisfies the same window reconstruction formula in {window_pass}/12 conditions and the original whole-history A/B rules in {full_a}/12 and {full_b}/12, respectively.')
    secondary_text=' '.join(secondary)+' These are reference/reader checks on the same two initializations. Their continuous effects and all failures remain in the complete tables; the primary attribution of the additional interior package still uses E versus D_E.'
    seed_detail=[]
    device_detail=[]
    guard_passes=0
    for seed in (29,43):
        paired=[pairs[str(seed)]['E_vs_D_E'] for levels in results['comparisons'].values() for pairs in levels.values()]
        guard_passes+=sum(all(v['A_w']['noninferior'].values()) for v in paired)
        def interval(metric):
            values=[100*v['window_effects'][metric]['relative_error_reduction'] for v in paired]
            return f'{min(values):.2f}% to {max(values):.2f}%'
        seed_detail.append(f'Seed {seed} has phase-RMS error reductions of {interval("Ephi")} and active-set error reductions of {interval("S")}.')
        counts_by_control={name:sum(pairs[str(seed)][name]['full']['B']['passed'] for levels in results['comparisons'].values() for pairs in levels.values()) for name in ('E_vs_F','E_vs_B_E')}
        device_detail.append(f'For seed {seed}, the full device rule passes {counts_by_control["E_vs_F"]}/6 checks against F and {counts_by_control["E_vs_B_E"]}/6 against B_E.')
    phase_detail=' '.join(seed_detail)+f' All three window guards jointly pass in {guard_passes}/12 conditions. The phase-gain requirements still determine the complete A_w outcome; negative reductions indicate larger E errors.'
    secondary_text+=' '+' '.join(device_detail)
    ph=ranges['Ephi'];pmin=100*ph['min'];pmax=100*ph['max']
    if n==12:
        outcome='Both initializations satisfy the complete phase-gap criterion against D_E under all three references and both readers.'
        interpretation='This establishes a conditional contribution from the retained thermal/phase residual package in the prescribed phase-gap observation regime.'
        if outside:interpretation+=' The contribution has the outside-window costs reported below and is not an unqualified whole-history improvement.'
    elif n:
        outcome=f'The phase-gap criterion against D_E passes in {n} of the twelve initialization/reference/reader conditions; the complete advantage is not stable across the declared conditions.'
        interpretation='The result provides mixed conditional evidence, without establishing a reference- and reader-stable residual increment.'
    else:
        outcome='Neither initialization establishes the complete phase-gap criterion against D_E under the three references and two readers.'
        interpretation='The prescribed phase-gap experiment does not establish the claimed additional residual increment; individual favorable errors do not replace the complete criterion.'
    outcomes=f'{outcome} Across those conditions, relative phase-RMS reductions of E against D_E range from {pmin:.2f}% to {pmax:.2f}%; negative reduction means larger E error.'
    costsentence=f'Outside-window noninferiority costs occur in {outside} of the twelve primary comparison conditions.'
    metric_names={'S':'active-set difference','Ephi':'phase RMS','ET':'temperature error','EI':'top-current NRMSE','EV':'potential RMS','bottom_current_NRMSE':'bottom-current NRMSE','power_trace_NRMSE':'power-trace NRMSE'}
    if costs:costsentence+=' The affected quantities are '+', '.join(metric_names[k] for k in costs)+', with every condition retained in the comparison table.'
    robust=summary['strict_across_all_references_and_readers']
    strictsentence=('No B1 object satisfies the complete strict two-cycle rule across all tested references and readers.' if not robust else
                    'The B1 objects satisfying the complete strict rule across all tested references and readers are '+', '.join(robust)+'.')
    if not any(flag for values in summary['strict_by_reference'].values() for flag in values.values()):
        strictsentence='All seven B1 objects fail the complete strict two-cycle rule under every tested reference and reader.'
    title='Training-time electrical elimination in physics-informed neural networks for electrothermal phase reconstruction'
    manuscript=f'''# {title}

Authors: [author names and affiliations to be supplied]

Corresponding author: [name and email to be supplied]

## Abstract

A final electrical solve can repair terminal outputs while leaving inaccurate temperature and phase unchanged. We study how this constraint should participate in learning a transient electrothermal state from prescribed field observations. A partially eliminated PINN retains neural temperature and phase, solves a grounded finite-volume electrical problem during training, and uses its face resistances for consistent local Joule deposition. The soft PINN and interpolation controls receive the same final electrical solve. Four paired fits on two separately reconstructed finite-pulse protocols retain the complete device-advantage criterion under three numerical references and two electrical readers. With the finer reader and spatial reference, current and power error reductions over the soft controls are 47.03-76.52% and 47.86-77.50%. Strong interpolation gives a continuous-ranking counterexample. Clean full-label controls without the thermal/phase interior residuals have lower phase, current and power errors. A further frozen experiment removes phase labels throughout the second cycle while retaining potential, temperature and post-window phase observations. {outcome} {costsentence} The evidence distinguishes the tested electrical-constraint configuration from the conditional contribution of additional dynamic residuals. It concerns a synthetic, known-model offline reconstruction problem; strict-event, numerical-discretization and material-validation limits remain explicit.

Keywords: physics-informed neural network; electrothermal coupling; electrical elimination; missing phase observations; phase-field reconstruction

## 1. Problem and information conditions

Small potential errors can produce large contact-current and local-heating errors in a coupled phase-transition calculation. Electrical repair can restore terminal consistency without repairing the learned evolving state. We therefore ask two separate questions: whether training with the electrical constraint improves reconstruction after every method receives the same final solve, and whether the additional thermal/phase interior residuals contribute under complete and phase-gap observation conditions.

'''
    manuscript+='PINNs combine observations with explicit differential-equation residuals [1]. '
    introduction=newblock('## Problem and supported contribution','## Initial and boundary interpretation')
    introduction=introduction.replace(' The method and information differences are documented in [the source verification](source-verification.md).','')
    manuscript+=introduction
    manuscript+='\n\nReduced and all-at-once PDE formulations provide the broader setting for eliminating a constrained variable versus jointly optimizing all fields [13]. Here only quasi-static potential is eliminated; the transient states remain neural.'
    manuscript+='\n\nThe field network follows the smooth modified-MLP construction of Wang et al. [2]. The spatial cell-balance thermal residual is related to control-volume learning [6], while the nonconserved phase dynamics use an Allen-Cahn-type potential [7]. The device layout and electrothermal feedback are inspired by wall-cell phase-change-memory modeling [8]; its Ge-rich GST material formulation is distinct from the present dimensionless single-phase variable. The parameters below define the synthetic benchmark and are not an oxide calibration.\n\n'
    manuscript+='## 2. Two-dimensional physical object\n\n'
    manuscript+='### 2.1 Equations, geometry and known coefficients\n\n'+between('### 2.1 Governing equations','### 2.2 Complete pulse protocols and information boundary')
    initial_boundary=newblock('## Initial and boundary interpretation','## Matched E/F/D_E/B_E design')
    initial_boundary='For the initial phase in Eq. (7), at x=0'+initial_boundary.split('At x=0',1)[1]
    manuscript+='\n\n### 2.2 Initial-boundary interpretation\n\n'+initial_boundary
    manuscript+='\n\n### 2.3 Pulse histories and observations\n\n'+between('### 2.2 Complete pulse protocols and information boundary','## 3. Partially eliminated hybrid PINN')
    manuscript+='\n\n'+figure(1,'fig01-object-information','Actual geometry, fixed spatial sampling and finite pulse protocols. The shaded interval W=[1.01,2.02] removes only phase labels in B1; potential and temperature remain observed. Phase observations after W remain available. Dashed vertical lines mark the predeclared display times 0.27 and 1.28. The dashed spatial box is the fixed state-error ROI.')
    manuscript+='\n## 3. Method and matched controls\n\n### 3.1 Neural states and electrical elimination\n\n'
    method=between('### 3.1 Neural states and electrical elimination','### 3.4 Fixed-prediction reference perturbation')
    method=method.split('![Figure 1.',1)[0].strip()
    manuscript+=method
    manuscript+='\n\n### 3.4 The D_E ablation and strong interpolant\n\n'+newblock('## Matched E/F/D_E/B_E design','## Existing main result and adjacent counterexamples')
    manuscript+=r'''

The precise ablation objective is

$$\mathcal{L}_{D_E}=L_{{\rm obs},E}/a+\lambda(5L_{\rm BC}+L_{\rm IC})/b. \qquad (21)$$

The scale b is still calibrated from the complete parent physical package. Thus E minus D_E removes exactly the interior term rather than renormalizing the shared boundary or observation contribution. Targeted value/gradient checks and full-visible compatibility checks precede the new execution.
'''
    parents=between('### 4.1 Shared parents, fixed endpoints and strong controls','### 4.2 Common inference and distinct outcome measures').split('B_E interpolates',1)[0]
    manuscript+='\n### 3.5 Common parents, fixed endpoints and readouts\n\n'+parents
    manuscript+='\nThe shorter-protocol D_E controls share the corresponding full-label parents. B1 instead establishes two entirely new observation-only parents with only its visible phase labels, then runs E, D_E and F in each seed without selecting a favorable checkpoint or skipping an arm based on performance. All fixed endpoints are locked before reference scoring. The common 160 by 80 and 240 by 120 electrical readers evaluate every model at the same 1001 times. Fine-grid T/phase are direct queries of the same locked function. T/phase and event scores remain on 160 by 80; only fine potential is conservatively restricted for the inherited field guard, while native currents, power and Joule deposition stay native.\n'
    measures=between('### 4.2 Common inference and distinct outcome measures','### 4.3 Bounded phase-head development')
    measures=measures.replace('The separately declared 240 × 120 reader below','The 240 × 120 reader')
    manuscript+='\n### 3.6 Distinct error and event measures\n\n'+measures
    gap=newblock('## Frozen B1 question — results not yet available','## Data and code availability')
    gap=gap.split('No B1 improvement',1)[0].strip()
    gap=gap.replace('will each initialize','each initialize')
    manuscript+='\n\n### 3.7 Frozen second-cycle phase-gap experiment\n\n'+gap
    manuscript+='\n\nA_w applies the original phase-advantage formula to W with its own time weights and normalizers: the S and phase-RMS improvements must meet the inherited 10% or absolute-floor requirements, while T, top-current and potential retain their original 5% noninferiority guards. The bottom-current convention remains separately reported. The outside measure integrates [0,1.01] and [2.02,2.5] separately, without bridging W. Its unnormalized integrals plus those of W reproduce the full-history integrals. Outside costs include all seven named state/device quantities. Original full-history A/B and strict-event rules remain unchanged. This is a complete withheld time window for phase, with V/T still observed inside it; it is not a formal out-of-distribution or forecasting test.\n'
    manuscript+='\n## 4. Reconstruction after common electrical repair\n\n### 4.1 Four paired full-label comparisons\n\n'
    manuscript+='All four clean E/F pairs retain the complete device criterion under every existing reference and both readers. Under the spatial reference with the finer reader, current-error reductions are 47.03-76.52% (0.78-2.28 percentage points) and power-error reductions are 47.86-77.50% (0.82-2.39 points). The comparison therefore survives giving F the same final electrical solve. Four pairs on two related protocols are the comparison units; reference, reader and saved-time counts do not increase that sample size.\n\n'
    manuscript+='Table 1. Complete full-label objects under the spatial reference and fine reader. Phase uses the original 160 by 80 ROI; native device NRMSE values are percentages. B_E is one deterministic object per protocol. D_E is shown alongside the learned controls rather than introduced only after the main results.\n\n'+table('full-label-main')+'\n\n'
    manuscript+=figure(2,'fig02-full-label-physics-seed29','Native 240 by 120 physical states and signed errors for the full-label shorter protocol. The first two columns show spatial-reference T, phase and Joule density at the two predeclared plateau endpoints. The remaining columns show E, repaired F and B_E minus reference at t=1.28 for seed 29. Error color scales are shared with the seed-43 companion in the supplement. These physical panels are descriptive native-grid views; the primary T/phase/event measure stays on 160 by 80.')
    manuscript+='\n'+figure(3,'fig15-common-reader','All four historical E/F pairs under the same native spatial reference and the two electrical readers. Solid and dashed curves show current and power NRMSE. B_E is repeated visually across seeds but is one baseline per protocol. Signed E-F differences use percentage points. The complete criterion also includes all field guards.')
    manuscript+='\nThe development controls illustrate why repair is a necessary comparison: with T/phase fixed, projection reduces F_raw current NRMSE from 279.30% to 1.071% and power NRMSE from 20.118% to 1.065%, while E gives 0.694% and 0.682%. A full-spatial finite-penalty control does not remove that development difference, but its integrated energy error is better. These controls delimit the tested package; they are retained in Supplement S4 and are not pooled as clean replications.\n'
    reversal=newblock('## Existing main result and adjacent counterexamples','## Frozen B1 question — results not yet available')
    reversal=reversal.split('This robustness does not extend uniformly to B_E.',1)[1].split('In the two clean full-label',1)[0]
    # Display rounding never supplies the decision input; complete precision is in CSV.
    reversal=re.sub(r'(?<![\w])([+-]?\d+\.\d{7,})',lambda m:f'{float(m.group(1)):.6f}',reversal)
    reversal=reversal.replace('\n\n| Reference |','\n\nTable 2. Continuous interpolation counterexample for original-protocol seed 43 with the fine reader. Negative relative error reduction means larger E error; full-precision records determine the unchanged A/B decisions.\n\n| Reference |',1)
    manuscript+='\n### 4.2 The strong interpolation counterexample\n\nThis robustness does not extend uniformly to B_E.'+reversal
    manuscript+='\n## 5. Additional dynamic residuals: full-label and phase-gap tests\n\n### 5.1 Full-label matched D_E evidence\n\n'
    manuscript+='In both clean shorter-protocol pairs, D_E has lower phase, current and power RMS errors than E under all three references and both readers. Neither pair establishes the prescribed added-residual phase or device increment. With the spatial reference and finer reader, E exceeds D_E in phase/current/power error by 2.404%/5.997%/6.061% for seed 29 and 0.277%/8.945%/11.239% for seed 43. Other outcomes are mixed. Because the electrical solve and voltage feedback remain active in D_E, this result concerns the additional thermal/phase interior package. It does not test physics against a data-only network. Complete independent audit components remain in Supplement S17.\n'
    manuscript+='\n### 5.2 Second-cycle phase-gap reconstruction\n\n'+outcomes+' '+interpretation+'\n\n'+phase_detail+'\n\n'
    manuscript+='Table 3. B1 errors inside W under the spatial reference and fine reader. All seven objects are included. Full-precision values for all references/readers, including their own denominators, remain in the complete tables.\n\n'+table('b1-main')+'\n\n'
    manuscript+=figure(4,'b1-phase-t2','B1 phase at t=1.28, inside the withheld second cycle. Reference and shared B_E accompany E, D_E and F for both seeds. All panels use the same [0,1] color range. Native fine-grid fields provide a physical view, while the primary state and event criteria use the original coarse measure. T, local q, both predeclared times and signed-error companions are retained in the supplementary physical atlas.')
    manuscript+='\n'+figure(5,'fig05-b1-matched-effects','Window effects of E against same-parent D_E in all twelve seed/reference/reader conditions. Positive numbers mean smaller E error. Colors are capped at plus/minus 100% for legibility; annotations retain the actual values. The row label gives the complete A_w outcome, which also uses absolute floors and noninferiority. The rows are sensitivity checks on two independent initializations, not twelve independent experiments.')
    manuscript+='\n### 5.3 Whole-history costs and strict events\n\n'+costsentence+' '+strictsentence+'\n\n'
    manuscript+='Table 4. Primary B1 decisions in every reference/reader condition. Full A/B retain their original definitions; outside cost denotes at least one separately reported noninferiority violation. A favorable window result does not erase an outside or strict-event cost.\n\n'+table('b1-primary-decisions')+'\n\n'
    manuscript+=secondary_text+'\n\n'
    manuscript+='All E/F and E/B_E comparisons, complete cycle metrics, signed device effects and separate full/outside normalizers are retained with the primary comparison. Phase observations after 2.02 support both the networks and the legal interpolant, so even a favorable result is offline reconstruction rather than online second-pulse prediction. The outcome has not changed the full-label D_E finding, historical E/F decisions, seeds, thresholds or reference definitions.\n'
    manuscript+='\n## 6. Physical interpretation and numerical scope\n\n'
    manuscript+='### 6.1 Pulse history and functional quantities\n\nThe references agree before the changed pulse to roundoff at matching resolution. Immediately before the second pulse, advancing it from 1.25 to 1.01 increases the reference ROI mean T from 0.006525 to 0.018746 and mean phase from 0.0004829 to 0.0039725. The second-event latency decreases from 0.2484 to 0.2168. These observations support history dependence in this numerical object but do not isolate thermal from phase mediation. Complete per-pulse states and event values remain in Supplement S5.\n\n'
    manuscript+='Device and event rankings differ. Historical shorter-protocol E passes both onset-timing tolerances under the original reference, but first-cycle recalls 0.866607 and 0.875507 remain below 0.9. F29 has the smaller second-cycle timing error. F43 has opposite signed pulse-energy errors, +0.00511674 and -0.00400099, yielding 0.25736% total energy error despite 3.09469% power-trajectory NRMSE. E also exhibits cancellation. Since projected current and power obey P=UI, their errors are related drive-weighted views; neither low energy error nor electrical balance certifies local heating or strict event reconstruction.\n'
    manuscript+='\n### 6.2 Reference and reader sensitivity\n\nThe original reference uses 160 by 80 cells and dt=0.000625; temporal refinement halves dt; spatial refinement uses 240 by 120 at the halved step. All save the same 1001 times and keep the learned states fixed. Spatial fields are conservatively restricted for the primary state/event measure while ports remain native. Predictions have two separately tested electrical readers. These are finite perturbation tests, not a demonstrated convergence order or continuum-error estimate.\n\n'
    manuscript+='Across the historical coarse-reader comparisons, temporal refinement changes no A/B decision; spatial refinement changes three: original/29 E/B_E loses A, shorter/43 E/F loses A, and original/43 E/B_E gains B. The latter B crossing disappears with the finer reader. Section 4.2 additionally retains the continuous B_E reversals under original/time references. The complete E/F device criterion remains retained in every tested condition. Supplement S9 and S14-S16 give the complete margins, sufficient perturbation bounds and restriction conventions.\n\n'
    manuscript+='A later gated continuation crosses the strict rule only under the time-refined reference and loses it under spatial refinement as first-cycle recall changes from 0.902063024 to 0.897526906. Ordinary and gated phase-head extensions do not establish a stable matched increment over unchanged continuation. All six negative continuation states are retained in Supplement S10-S13 and the separately indexed array extension. These limits prevent attributing the core effect to a demonstrated new gate, extra capacity or arbitrary-grid robustness.\n'
    manuscript+='\n### 6.3 What the experiment identifies\n\nThe E/F contrast identifies the tested constraint-training configuration. Initial V, active parameters, exact versus finite enforcement, enforcement times and gradient maps differ; the experiment does not isolate one implicit-gradient pathway. E/D_E controls that distinction more tightly for the additional interior residuals, but its conclusion is conditional on the information regime and frozen optimization recipe. Each information regime rebuilds its own parents and calibration scales. The comparison between regimes therefore describes the observed pattern of increments without holding every training mediator fixed. Equal update limits do not give equal numerical work, and no acceleration over a conventional forward solver is claimed.\n\n'
    manuscript+='The domain has a localized electrode and a closed electric-thermal-phase feedback chain. Its dimensionless coefficients, single phase variable and idealized geometry still require a separate material-consistent calibration and independent validation before a device-material claim. The initial-boundary incompatibility and shared numerical discretization likewise remain limitations. A stronger algorithmic or material claim would need a separately designed experiment rather than relabeling the present controls.\n'
    manuscript+='\n## 7. Conclusions and availability\n\nTraining-time electrical elimination with consistent local Joule deposition produces a matched device-reconstruction benefit over the tested soft PINN after both receive the same final electrical repair. All four full-label pairs retain the complete device criterion under the declared reference and reader changes. Strong interpolation supplies a continuous reversal and a reader-sensitive advantage decision, limiting the scope of that benefit.\n\n'
    manuscript+='The full-label E/D_E evidence does not establish added predictive value from the interior thermal/phase residuals. '+outcome+' '+interpretation+' '+costsentence+' '+strictsentence+' The work separates configuration-level evidence, conditional residual contributions and unresolved material or generalization claims.\n\n'
    manuscript+='### Data, code and author declarations\n\nThe curated repository at [commit 218bb66069da52b2ccfe9dd68ac519edbe4584d0](https://github.com/ghy001122/PINN-PCM-SCI/tree/218bb66069da52b2ccfe9dd68ac519edbe4584d0) contains the 18 September scientific revision and selected evidence, published separately on 20 September 2026. The present B1 revision remains local. Its portable array package contains 72 full-label core records, a separately preserved 18-record negative continuation extension and 42 B1 reference/reader records. Those record counts are not independent-repetition counts. The core reproduced 8,868 saved scalar/identity/Boolean entries at rtol=2e-10 and atol=2e-12, with exact categorical agreement. B1 was first scored from its separately portable NumPy-only inputs after endpoints and readers were locked and GPU recovery/shutdown completed. Array arithmetic, figure/PDF rebuilding, new model inference and retraining are distinct reproduction levels. No independent external retraining is claimed.\n\n'
    manuscript+='Full arrays have not been publicly uploaded or assigned a DOI. Public or controlled reviewer access, appropriate distribution permission and persistent archiving require author approval. AI-assisted preparation: OpenAI Codex assisted with research-code preparation, numerical execution, source checking, analysis, figures and drafting. Human authors must verify the content and take responsibility for interpretation, disclosures and submission. Funding, author contributions, competing interests, affiliations and final author approval remain to be supplied truthfully. This numerical study contains no experimental or human-subject data.\n\n## References\n\n{{REFERENCES}}\n'
    manuscript=manuscript.replace('from the conditional contribution of additional dynamic residuals',
                                  'from the test of added dynamic-residual value')
    manuscript=manuscript.replace('configuration-level evidence, conditional residual contributions',
                                  'configuration-level evidence, tests of additional residual value')
    (HERE/'source/manuscript.md').write_text(manuscript,encoding='utf-8')
    make_supplement(title,summary,results,outcomes,costsentence,strictsentence)
    for name in ('prepare_document.py','build_pdf.py'):
        if (HERE/name).exists():
            continue  # Preserve the current revision's verified typesetting fixes.
        source=(OLD/name).read_text(encoding='utf-8')
        source=source.replace('Readout and residual revision, 18 September 2026','Phase-gap revision, 21 September 2026')
        if name=='build_pdf.py':
            source=source.replace('symbols = ("u_θ",', 'symbols = ("A_w", "S_w", "u_θ",')
        (HERE/name).write_text(source,encoding='utf-8')
    print(json.dumps(dict(status='FINAL_SOURCES_ASSEMBLED_FROM_COMPLETED_B1',route=route)),flush=True)


def make_supplement(title,summary,results,outcomes,costsentence,strictsentence):
    """Keep historical evidence accessible, with an explicit map and B1 block."""
    source=(OLD/'source/supplement.md').read_text(encoding='utf-8')
    source=source.replace(source.splitlines()[2],'## '+title,1)
    navigation='''
## Navigation and version scope

S1-S3 specify the numerical object, learning interface and frozen metrics. S4-S6 retain the development controls, full historical events and work. S9 and S14-S16 collect reference/reader sensitivity and complete bounds. S10-S13 retain all six representation continuations and their adverse outcomes. S17 gives the full-label E/D_E controls; S18 gives descriptive diagnostics. S20 states the new B1 design, complete decisions, costs and physical atlas. Historical words such as "new protocol" in S1-S19 refer to their original dated experiments, not additional work in B1.

All primary decisions use full-precision records. Tables may round display values. The machine-readable table index in S20 identifies every B1 event, noninferiority component, normalization and signed effect, including unfavorable values.

'''
    source=source.replace('## S1. Numerical object and data construction',navigation+'## S1. Numerical object and data construction',1)
    source=source.replace('The main figures instead use directly paired F network/projected readouts',
                          'The historical repair figures use directly paired F network/projected readouts')
    source=source.replace('Figures 2–3 use the development table; Figure 4 uses four clean pairs; Figure 5 uses the saved event/reference/power data; Figure 6 retains adverse event and energy outcomes.',
                          'The preserved historical fig02/fig03 assets use the development table; fig04 uses four clean pairs; fig05 uses saved event/reference/power data; fig06 retains adverse event and energy outcomes. These filenames retain their historical identities and do not assign the main-text numbering in this revision.')
    source=source.replace('Necessity remains UNKNOWN; the clean matched increment is adjudicated in S17',
                          'The full-label clean matched increment is adjudicated in S17; B1 adds the conditional S20 test without establishing universal necessity')
    source=source.replace('For the present reader/residual revision, report_results.py regenerates the new tables and figures from the expanded array scores; prepare_document.py/build_pdf.py rebuild the complete documents from their included assets. The current data-and-reproduction.md gives the distinct commands. Earlier snapshots and numerical values are preserved.',
                          'For the 18 September reader/residual revision, report_results.py regenerated that snapshot from its expanded array scores. These commands describe preserved historical packages. For the present 21 September revision, use paper/paper_revision_20260921/prepare_document.py followed by build_pdf.py to rebuild the supplied source/templates, tables, figures and references with the project Python and ReportLab. Its plot_physics.py regenerates physical panels from locked arrays, with zero model queries or electrical solves. Its report_b1.py exports the completed B1 score, rather than scoring or training again. The current data-and-reproduction.md gives the distinct actually executed commands and the portable scoring entrypoints. Earlier snapshots and numerical values are preserved.')
    source=source.replace('## S8. Claim-to-evidence matrix',
                          '## S8. Historical claim-to-evidence matrix')
    source=source.replace('VERIFIED denotes saved evidence checked against its source, not independent retraining or external peer review.',
                          'This section preserves the historical full-label matrix; the complete current matrix is claim_evidence_matrix.md, and S20 supplies the B1 evidence and limits. VERIFIED denotes saved evidence checked against its source, not independent retraining or external peer review.',1)
    source=source.replace('## S19. Expanded reproduction and submission boundary',
                          '## S19. The 18 September reproduction package and submission boundary')
    source=source.replace('The current revision executes two clean-parent thermal/phase-residual ablations',
                          'The 18 September revision executed two clean-parent full-label thermal/phase-residual ablations')
    before=source.split('## References',1)[0]
    counts=summary['counts']
    b1=f'''## S20. Second-cycle phase-gap experiment

### S20.1 Visible data, matching and frozen selection rules

The sole protocol is the existing shorter pulse history. W=[1.01,2.02] removes 11,781 positive-time phase labels; 17,094 remain. V/T each keep 28,875 labels. There are 126 original observation times and 231 spatial sites. Phase has 75 visible times including the analytic initial map; the last preceding and first following observed times are 1.00 and 2.04. There is no original observation at 1.01; the observation at 2.02 is withheld. Post-window phase remains visible, making this offline reconstruction.

The physically exported package separates V, T and visible phase indices/values. Hidden phase is removed before logit conversion, statistics, parent fitting, interface selection, calibration and baseline construction. The original coordinate quadrature is restricted and normalized per field; time weights are not recomputed across a gap. A straddling cell is retained only when all its original adjacent corners are visible. There are 173 retained cells and 476 endpoints. Phase keeps the half-global/half-interface measure. The common four-time proposal retains all V/T temporal support and uses exact inverse-probability correction for each field. Complete-objective closures evaluate the fixed target. Known initial phase has zero observation mass and remains exact in the output map.

Each seed, 29 then 43, creates a fresh observation-only parent, new calibration and new fixed pools. Both parents are established before branches run in order 29/E, 29/D_E, 29/F, 43/E, 43/D_E, 43/F. No complete-label trained state, calibration, interface pool or hidden-label statistic is imported. Within a seed, branches share the parent, architecture, observation boundary, calibration and fixed physical pools; only the named objective/method difference changes. B_E uses field-specific visible-time PCHIP and the inherited spatial/initial/boundary rules, allowing legal interpolation across the missing phase segment. B_E uses no interior V labels and is one shared object.

Parents use 2400 Adam updates at learning rate 0.001 and at most 200 complete evaluations per head. Each branch uses 1500 Adam updates at 0.0001, followed by at most 300 complete evaluations. Adam betas are (0.9,0.999), epsilon is 1e-8, and clipping is 10. Lambda rises linearly to 0.1 over 200 steps. Four observation times, 128 physical cells per window, four physical windows, and eight fixed times per window retain the preceding recipe. L-BFGS uses learning rate 1, history 50, max_iter=1 per continued step, max_eval=32, strong-Wolfe search, gradient tolerance 1e-10 and change tolerance 1e-14. Every trial/repeated closure counts; cap interruption rolls back to the last accepted state. No reference metric chooses a checkpoint, seed or extra run.

The primary A_w is the original phase-comparison rule applied to W with its own normalization. Outside weights integrate the two remaining segments separately. Window plus outside unnormalized integrals exactly reconstruct the full-history integrals. The full A/B, strict-event and E/F/B_E comparisons retain all original rules. Two initializations are the independent optimization units; three references and two readers are repeated sensitivity evaluations of those states.

### S20.2 Complete outcomes and outside costs

{outcomes} {costsentence} {strictsentence}

Table S29. Every primary A_w, original full A/B and outside-cost decision.

{table('b1-primary-decisions')}

Table S30. All seven B1 objects in W for each reference with the fine reader. S and V RMS are multiplied by 1000; phase RMS is raw; T and device errors are percentages. Coarse-reader counterparts and all normalization denominators are in the complete CSV/JSON records.

{table('b1-window-fine')}

Table S31. Outside-window errors with their own normalization and disjoint integration intervals.

{table('b1-outside-fine')}

Table S32. Full-history B1 errors under the unchanged primary measures.

{table('b1-full-fine')}

Table S33. B1 onset and support in both cycles for every object, using the spatial reference and the primary 160 by 80 state/event measure. Errors are absolute time errors; recall, precision and mass ratio retain their original definitions. Missing onset and any infinite missing-event error are reported without replacement by zero. The shared baseline has no seed.

{table('b1-event-support-spatial')}

Table S34. B1 event extent and recovery for the same complete object/cycle set. Peak and recovery values are fractions, not percentages. Maximum phase and Strict refer to the entire object history and are repeated beside both cycles; Strict also requires the support and timing conditions. Other references and exact cycle values remain in the complete 84-row event CSV; whole-history phase maxima are in b1-all-records.csv.

{table('b1-event-extent-spatial')}

Table S35. Signed per-pulse Joule-energy errors for all seven B1 objects under the spatial reference and fine reader. Each error integrates predicted minus reference power over the unchanged powered intervals [0,0.35] and [1.01,1.36]. Zero drive gives zero power outside those intervals, so their signed sum equals the full-history error. The last column is 100 times the absolute total divided by reference energy; it is not the sum of absolute pulse errors. These are dimensionless quantities. All 84 pulse rows, 42 full-history summaries and 42 complete native-port traces are indexed below.

{table('b1-energy-spatial-fine')}

| File | Complete scope |
| --- | --- |
| b1-all-records.csv | All 42 reference/reader/object records, full metrics and original strict states |
| b1-all-events.csv | Every cycle of all records: 84 rows; duplicate readers are not independent events |
| b1-all-window-outside-full.csv | 126 records: all window/outside/full errors, denominators and unnormalized integrals |
| b1-all-comparisons.csv | All 36 E/D_E, E/F and E/B_E comparisons with each subpredicate, signed effect and outside flag |
| b1-signed-pulse-energy.csv / b1-energy-summary.csv | All 84 signed pulse integrals and 42 whole-history energy summaries; pulse sums match stored cumulative errors and original energy scores |
| b1-port-trace-index.csv | All 42 saved 1001-time native-port/power/error traces; paths are relative to the portable B1 package |
| b1-training-and-calibration-work.csv | Both parents, calibrations and all six branches, including complete trial counts and model-work instrumentation |
| b1-readout-work.csv | All fourteen readers, native electrical counts, model-head queries and elapsed times |

All tables are under tables/. Original metric, cycle and comparison records are also in evidence/b1-complete-results.json; energy exports use the indexed traces. No failed method, cycle or reference is filtered out.

### S20.3 Actual work, recovery and reproducibility

Actual optimizer work is {counts['adam']} Adam updates and {counts['complete_evaluations']} complete evaluations, within the frozen limits 13,800 and 3,000. Training electrical forward/adjoint counts are {counts['training_forward_solves']}/{counts['training_adjoint_solves']}; calibration counts are {counts['calibration_forward_solves']}/{counts['calibration_adjoint_solves']}. Common readout adds 3,892 forward solves and no adjoints: seven objects times two grids times 278 powered times. All 1001 times are retained; zero-drive solutions use the established analytic branch. No support or reference trajectory is generated.

Head-forward calls, coordinate queries and head-output derivative calls are instrumented separately; derivative-hook counts are not claimed to be universal framework backward-operation counts. Parent, calibration, optimizer, complete-objective and reader costs remain distinct. Equal optimizer caps do not imply equal wall time. The verified platform is Tesla V100-PCIE-32GB, Python 3.11.9, PyTorch 2.5.1+cu118, NumPy 2.1.1 and SciPy 1.14.1. Outputs were recovered and the actual instance shut down before reference scoring.

The separate B1 array package uses only NumPy and complete saved inputs. Its first actual scoring command is documented in data-and-reproduction.md. Predictors and references have portable paths; the same full-history and frozen window kernels are retained. Twelve targeted synthetic CPU checks preceded the campaign. Source preparation, actual execution, same-code array arithmetic and independent scientific replication are different evidence levels.

### S20.4 Physical atlas at predeclared times

The display times 0.27 and 1.28 were frozen from the waveform before B1 outcomes. Native 240 by 120 states are shown without a favorable crop. Each physical quantity uses a shared range across times and all objects; signed-error companions use a common symmetric range. T/phase/event adjudication stays on the original 160 by 80 measure. Joule density uses saved values or the same algebraic deposition from saved native V/T/phase; this plotting introduces zero model queries and zero electrical solves.

![Full-label seed-43 physical companion](figures/fig02-full-label-physics-seed43.png)

Figure S11. Full-label seed-43 companion to main Figure 2, with the same reference fields, times and signed-error color ranges.

'''
    number=12
    for field,label in (('temperature','temperature'),('phase','phase'),('joule_density','local Joule density')):
        for j,time in enumerate((.27,1.28),start=1):
            for suffix,kind in (('','state'),('-error','signed prediction-minus-reference error')):
                zero=' The reference error panel is zero by definition.' if suffix else ''
                b1+=f'![B1 {label} {kind}](figures/b1-{field}{suffix}-t{j}.png)\n\nFigure S{number}. B1 {label} {kind} at t={time:.2f}. Reference, shared B_E and all E/D_E/F states for both seeds are retained.{zero}\n\n'
                number+=1
    (HERE/'source/supplement.md').write_text(before+b1+'## References\n\n{{REFERENCES}}\n',encoding='utf-8')

if __name__=='__main__':main()
