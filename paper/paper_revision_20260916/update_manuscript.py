"""Integrate actual completed results into the complete original manuscript."""
from pathlib import Path
import argparse
import json
import re
from editorial_revision import revise

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OLD=ROOT/'paper/paper_submission'
RUN=ROOT/'outputs/runs/20260916-lf11-phase-adapter-reference'


def read(path):return json.loads(path.read_text(encoding='utf-8'))


def main():
    p=argparse.ArgumentParser();p.add_argument('--scores',type=Path,default=ROOT/'outputs/submission-archive-20260916/rescore-output/results.json')
    a=p.parse_args();d=read(a.scores);exe=read(RUN/'execution-summary.json')
    r=d['records']['old'];ref=d['records']['refined'];ds=d['decisions'];tot=exe['totals']
    if len(r)!=16 or len(ref)!=16:raise ValueError('Complete old/new array results required')
    strict_old=[k for k,v in r.items() if v['strict_device_pass']]
    strict_new=[k for k,v in ref.items() if v['strict_device_pass']]
    verdict=[];details=[]
    for seed in (29,43):
        s=ds['old']['shorter'][str(seed)];n=ds['refined']['shorter'][str(seed)]
        parent=r[f'shorter/{seed}/E'];control=r[f'shorter/{seed}/E_C']
        details.append(f"For seed {seed}, unchanged continuation changes raw phase RMS from {parent['metrics']['Ephi']:.8f} to {control['metrics']['Ephi']:.8f}. This control is necessary because the new heads receive additional optimization.")
        for role in ('E_R','E_I'):
            candidate=r[f'shorter/{seed}/{role}'];m=candidate['metrics'];c=control['metrics']
            gain=100*(1-m['Ephi']/c['Ephi']);power=100*(m['power_trace_NRMSE']/c['power_trace_NRMSE']-1)
            timing=['not defined' if v['timing_absolute'] is None else f"{v['timing_absolute']:.6f}" for v in candidate['cycles']]
            kinds=[k for k,flag in [('phase',s[role]['matched_A']),('device',s[role]['matched_B']),('strict',s[role]['strict_increment'])] if flag]
            nextk=[k for k,flag in [('phase',n[role]['matched_A']),('device',n[role]['matched_B']),('strict',n[role]['strict_increment'])] if flag]
            verdict.append(f"Seed {seed}, {role}: original-reference increment = {', '.join(kinds) or 'none'}; refined-reference increment = {', '.join(nextk) or 'none'}.")
            details.append(f"{role} changes phase RMS by {-gain:+.2f}% and power NRMSE by {power:+.2f}% relative to E_C (negative is improvement). Its cycle recalls are {candidate['cycles'][0]['recall']:.6f}/{candidate['cycles'][1]['recall']:.6f}, with onset errors {timing[0]}/{timing[1]}.")
    gate_seeds=[seed for seed in (29,43) if any(ds['old']['shorter'][str(seed)]['gate_independence'][k] for k in ('A','B','strict'))]
    gate_ref=[seed for seed in (29,43) if any(ds['refined']['shorter'][str(seed)]['gate_independence'][k] for k in ('A','B','strict'))]
    adapter_seeds={role:[seed for seed in (29,43) if any(ds['old']['shorter'][str(seed)][role][k] for k in ('matched_A','matched_B','strict_increment'))] for role in ('E_R','E_I')}
    seed_names=lambda values: ', '.join(map(str,values)) if values else 'neither parent'
    interpretation=(
        'Neither added head satisfies a predefined phase, device or strict increment against E_C in either parent under the original reference. '
        if not any(adapter_seeds.values()) else
        f"The ordinary/gated heads satisfy a predefined increment in {seed_names(adapter_seeds['E_R'])} and {seed_names(adapter_seeds['E_I'])}, respectively, under the original reference. ")
    interpretation+=(f"The additional equal-parameter gate criterion is met in {seed_names(gate_seeds)} under the original reference and in {seed_names(gate_ref)} under the refined reference. "
        "A result in only one parent or under only one reference is a bounded development signal. It is not a clean initialization confirmation or a reason to pool different categories across seeds.")
    if not gate_seeds:
        interpretation += " No independent gate contribution is established under the original reference. The gate is retained as a tested counterfactual rather than added to the main contribution list."
    if not any(adapter_seeds.values()):
        interpretation += " The absence of an original-reference increment limits the proposed representation-efficiency explanation without proving that phase representation never matters. The reference-specific strict result is examined separately below."
    # Keep the ten historical objects' decisions separate from new-head development.
    flips=[];oldB=[];newB=[]
    for protocol in ('original','shorter'):
        for seed in ('29','43'):
            oo=ds['old'][protocol][seed];nn=ds['refined'][protocol][seed]
            oldB.append(oo['E_vs_soft']['B']['passed']);newB.append(nn['E_vs_soft']['B']['passed'])
            for comparison in ('E_vs_soft','E_vs_B_E'):
                for layer in ('A','B'):
                    if oo[comparison][layer]['passed']!=nn[comparison][layer]['passed']:
                        flips.append(f"{protocol} seed {seed} {comparison} {layer}")
    sensitivity=(f"With fixed historical predictions, the device criterion against the projected soft control passes in {sum(oldB)}/4 pairs under the original references and {sum(newB)}/4 under the refined references. "
        f"The changed historical A/B decisions are: {'; '.join(flips) if flips else 'none across eight comparisons (four E/soft and four E/interpolant), or sixteen A/B decisions per reference'}. "
        "A changed gate limits that specific threshold claim; a retained direction or gate supports only the tested temporal perturbation. Full errors, each reference denominator and fixed-old-denominator diagnostics are retained in the scoring records.")
    for protocol,v in d['reference_sensitivity'].items():
        dd=v['delta'];sensitivity += f" The {protocol} reference discrepancy is δ_S = {dd['S']:.8g} and ROI phase RMS δ = {dd['Ephi']:.8g}."
    narrow=next(v for v in d['reference_sensitivity']['shorter']['margins']
        if v['candidate']=='shorter/43/E' and v['baseline']=='shorter/43/F' and v['metric']=='S')
    sensitivity+=(f" The historically narrow seed-43 S margin changes from {narrow['old_margin']:.10g} to {narrow['new_margin']:.10g}. "
        "The sufficient triangle-bound condition alone cannot certify this narrow margin; its retention follows from actual rescoring of these two references, not from a continuum argument.")
    strict_text=(f"Strict two-cycle success holds for {len(strict_old)} of the sixteen objects under the original references and {len(strict_new)} under the refined references. "
        f"Original-reference successes: {', '.join(strict_old) or 'none'}. Refined-reference successes: {', '.join(strict_new) or 'none'}. "
        "Historical and newly developed objects are not pooled to estimate a success probability, and a reference-induced status change is not new model capability.")
    crossing=[]
    for name in sorted(set(strict_old)^set(strict_new)):
        for cycle,(co,cn) in enumerate(zip(r[name]['cycles'],ref[name]['cycles'],strict=True),1):
            if (co['recall']>=.9)!=(cn['recall']>=.9):
                crossing.append(f"For {name}, cycle {cycle} recall moves from {co['recall']:.9f} to {cn['recall']:.9f}, "
                    f"although predicted active mass remains {co['predicted_active_target_mass']:.11g}. "
                    f"Reference active mass changes from {co['teacher_active_target_mass']:.11g} to {cn['teacher_active_target_mass']:.11g}, "
                    f"and overlap from {co['true_positive_target_mass']:.11g} to {cn['true_positive_target_mass']:.11g}. "
                    f"The same cycle's onset error changes from {co['timing_absolute']:.9f} to {cn['timing_absolute']:.9f}. "
                    "This is a reference-specific crossing of the predefined strict criterion; it does not establish a gate contribution that survives both reference choices.")
    result_section="\n\n".join([
        '### 5.6 Phase representation: continuation, capacity and the frozen interface gate',
        'The six prescribed coupled PINN continuations and their own electrical projections were completed. Table 3 and Figure 7 retain the parent and continued control alongside both residual heads, which add the same number of trainable parameters. E_I additionally stores a frozen copy of the parent phase head. No new reference enters optimization or checkpoint selection.',
        'Table 3. New-head decisions under the original and refined references. A strict capability gain is separate from the phase/device criteria. Gate independence additionally compares E_I with E_R, with equal trainable counts and the extra frozen-gate cost disclosed.',
        '{{TABLE:phase-adapter-decisions}}',
        '\n\n'.join(details),interpretation,
        '![Figure 7. Fixed-budget phase-head comparison.](figures/fig07-phase-adapter.png)',
        'Figure 7. Both parents are displayed separately. All metrics use the original reference; the two curves in the bottom rows show the two cycles. Dashed horizontal lines retain the original criteria. Update and complete-evaluation caps are matched. E_C retains the original trainable count; E_R/E_I each add 1217 trainable parameters, and E_I additionally evaluates and differentiates a frozen gate. Supplement S10 lists actual counts and both-reference tables.',
        '![Figure 8. Fixed-time false-negative/false-positive maps and parent gate, seed 29.](figures/fig08-support-gate-seed29.png)',
        'Figure 8. The four display times were fixed before training (0.20, 0.30, 1.21, 1.31); the complete domain is shown. Blue marks missed activity, rust marks false activity and white marks agreement. The final column is the frozen normalized gate. It is not selected from reference errors. The same complete plot for seed 43 appears in Supplement S10. These maps explain localization descriptively; they do not create an additional training or selection criterion.',
        '### 5.7 Fixed-model reference sensitivity and array-only reproduction',sensitivity,strict_text,
        'Table 4. Reference discrepancies in the exact scoring measures. These are changes between numerical references, not model errors against a continuum truth.',
        '{{TABLE:reference-deltas}}',
        '![Figure 9. Reference sensitivity of historical advantage margins.](figures/fig09-reference-margins.png)',
        'Figure 9. Original and refined relative-gain margins for the same historical E/F and E/B_E arrays, including both primary device quantities. Positive margins satisfy the relative component only; original absolute tolerances and noninferiority still enter the full decision. Phase and symmetric-difference bounds use the same fixed measure. Device bars use each reference denominator; the fixed-original-denominator version for the triangle bound is supplied separately. No new network is selected from these plots.',
        '\n\n'.join(crossing),
        '![Figure 10. Both-reference event metrics for all new endpoints.](figures/fig10-event-reference-sensitivity.png)',
        'Figure 10. Both cycles of all six fixed new endpoints are displayed. Paired points change the reference only, preserving the predicted fields, event times and active masses. Dotted lines are the original recall and timing requirements; passing these two quantities alone does not replace the complete strict rule. The trace for seed 43, gated head, cycle 1 shows the reference-sensitive crossing without suppressing the other endpoints.',
        'The clean-directory NumPy evaluation reproduces all ten old objects\' saved metrics, complete event summaries and A/B decisions, and then evaluates all six new objects against both references. This establishes array-level reproducibility of the submitted results. It neither retrains the models nor proves independence of the original solver implementation. The local archive contains the full scoring inputs; public release is still an author-controlled step.'
    ])
    manuscript=(OLD/'source/manuscript.md').read_text(encoding='utf-8')
    manuscript=manuscript.replace(r'\qquad (21)$$',r'\qquad (24)$$')
    manuscript=manuscript.replace('while absolute current errors are','while current NRMSE values are')
    manuscript=manuscript.replace('and power errors are 0.673','and power NRMSE values are 0.673')
    manuscript=manuscript.replace('It is computed once per protocol and reused across seeds.',
        'It is computed once per protocol and reused across seeds. B_E has access to the same three-field sparse carrier, but its state interpolation actually uses only T and phase; it does not assimilate interior V observations. This is a comparison with the same available data, not equal utilization of every observed field.',1)
    manuscript=manuscript.replace('### 5.5 Event and energy counterexamples remain consequential','### 5.5 Historical event and energy counterexamples')
    manuscript=manuscript.replace('neither model achieves strict two-cycle usability',
        'neither model meets all project-defined two-cycle event requirements')
    manuscript=manuscript.replace('Our setting differs in three respects.',
        'Reduced and all-at-once PDE formulations distinguish eliminating a constrained variable from optimizing the full state jointly [13]. Integral projection methods enforce prescribed global quantities [12]; our electrical layer instead solves a local quasi-static boundary problem, retaining the evolving thermal and phase fields as neural unknowns. These neighboring approaches delimit the contribution, rather than establish novelty for constrained learning itself.\n\nOur setting differs in three respects.')
    manuscript=manuscript.replace('$$E_I=', '$$\\mathcal{E}_I=').replace(',\\quad E_P=', ',\\quad \\mathcal{E}_P=').replace(',\\quad E_W=', ',\\quad \\mathcal{E}_W=')
    network_abstract=(
        'Six additional matched phase-head continuations separate continued optimization, ordinary added capacity and a frozen interface gate; neither added head establishes the predefined increment under the original reference. '
        if not any(adapter_seeds.values()) else
        f'Six matched phase-head continuations give predefined ordinary/gated increments in {len(adapter_seeds["E_R"])}/2 and {len(adapter_seeds["E_I"])}/2 parents under the original reference. ')
    abstract=(
        'Electrical repair at inference can restore balance without correcting a learned evolving state. We compare training-time quasi-static electrical elimination with a soft electrical PINN receiving the same final solve. A hybrid network represents temperature and phase, differentiates the electrical solution implicitly, and deposits Joule heat through the same finite-volume half-cell resistances. Explicit thermal/phase residuals and a same-solver interpolant support the comparison. '
        'In a synthetic, dimensionless two-dimensional wall cell, two initialization pairs under each of two pulse protocols favor elimination. Under the original numerical references, current/power NRMSE reductions are 48.8-78.3%, with current NRMSE 0.682-1.572% and power NRMSE 0.673-1.593%. Earlier-pulse phase RMS decreases by 20.22% and 20.31% against projected soft controls. '
        +network_abstract+
        f'Halving the reference integration step preserves {sum(newB)}/4 historical device advantages. '+
        ('One gated endpoint crosses the strict two-cycle criterion only under the refined reference, showing threshold sensitivity rather than a reference-stable capability gain. ' if len(strict_old)==0 and len(strict_new)==1 else strict_text+' ')+
        'All sixteen fixed objects are independently rescored from a portable array archive. The evidence supports the specified coupling method while leaving isolated implicit-gradient causality, independent necessity of the remaining PDE terms, spatial convergence and material-calibrated performance unestablished.')
    manuscript=re.sub(r'(?s)(## Abstract\n\n).*?(\n\nKeywords:)',lambda m:m.group(1)+abstract+m.group(2),manuscript,count=1)
    manuscript=manuscript.replace('## 4. Matched experiment and evaluation',
        (HERE/'source/phase-adapter-method.md').read_text(encoding='utf-8')+'\n\n## 4. Matched experiment and evaluation')
    manuscript=manuscript.replace('## 5. Results',(HERE/'source/phase-adapter-protocol.md').read_text(encoding='utf-8')+'\n\n## 5. Results')
    support_identity=('For the same heating-window measure, let M_pred, M_ref and M_TP be predicted, reference and overlapping active masses. When both masses exceed the numerical denominator floor, the definitions give\n\n'
        '$$\\operatorname{recall}=\\operatorname{precision}\\,\\frac{M_{\\rm pred}}{M_{\\rm ref}}\\leq\\min\\left(1,\\frac{M_{\\rm pred}}{M_{\\rm ref}}\\right). \\qquad (25)$$\n\n'
        'This identity separates an insufficient predicted active mass from mismatch in space and time at a fixed mass. It is a descriptive support diagnostic, not a new loss or evidence that a particular neural mechanism caused the error. The original near-zero floors remain in the scorer. The strict gates are project-defined evaluation requirements, not experimental device-reliability standards or estimates of a success probability.\n\n')
    manuscript=manuscript.replace('Predeclared phase-reconstruction and device-function criteria',support_identity+'Predeclared phase-reconstruction and device-function criteria',1)
    manuscript=manuscript.replace('## 5. Results\n','## 5. Results\n\nSections 5.1-5.5 retain the historical results against the original fixed references. Section 5.6 adds the matched phase-head development, and Section 5.7 separately reports the new reference perturbation. No historical endpoint or decision is overwritten.\n',1)
    manuscript=manuscript.replace('## 6. Discussion',result_section+'\n\n## 6. Discussion')
    manuscript=manuscript.replace('A bounded future sensitivity check could retain every learned state and compare both protocols with a temporally refined reference; no such result is included here. The present paper remains complete as a fixed-reference method study.',
        'The new fixed-prediction comparison quantifies one temporal-reference perturbation and its actual decision changes in Section 5.7. It remains a fixed-spatial-discretization study; unchanged rankings cannot be promoted to continuum accuracy. The new phase-head controls address one representation hypothesis without establishing the independent necessity of the retained PDE terms.')
    manuscript=manuscript.replace('## 7. Conclusions',
        'The added phase heads yield small and mixed changes beyond continuation. This constrains the tested capacity explanation while preserving the reference-specific strict crossing as a numerical sensitivity result. It does not justify escalating the gate into the core method or declaring phase capacity irrelevant.\n\nThe explicit material mapping in Supplement S12 separates state, geometry, transport, latent heat and kinetics assumptions from validation. It also retains a theoretical oxide counterpoint rather than treating Joule heating as the sole possible transition mechanism [14].\n\n## 7. Conclusions')
    manuscript=manuscript.replace('strict event reliability, independent necessity of the remaining PDE terms, isolated implicit-gradient causality and material-calibrated performance remain unestablished.',
        ('the original eight learned states do not meet the complete strict two-cycle requirements. '+
         strict_text+' Independent necessity of the remaining PDE terms, isolated implicit-gradient causality and material-calibrated performance remain unestablished.'))
    manuscript=manuscript.replace('The present manuscript package adds only local writing, saved-result arithmetic and figure generation; it has not been published automatically. Full dense reference and prediction arrays are retained locally and are not all included in the public curated package.',
        'The present revision adds six phase-head PINN continuations, their projected outputs, two time-refined numerical references and array-only rescoring. These new results and their complete local scoring archive have not been publicly uploaded. The earlier curated public package remains distinct from this complete local revision.')
    manuscript=manuscript.replace('including source, configurations, checkpoints, curated result tables and selected traces.',
        'including source, configurations, checkpoints, curated result tables and selected traces. The preceding manuscript-only version is separately identified by [commit 4081ba09](https://github.com/ghy001122/PINN-PCM-SCI/tree/4081ba09b8a6aefa2141b10c707fdf4b327898eb/paper/paper_submission). This is the local experimental revision dated 16 September 2026; it does not reuse either published version identifier as its own.')
    manuscript=manuscript.replace('Complete dataset archival remains a submission preparation item.',
        'The local submission archive now contains the four references, sixteen fixed prediction/readout objects, two sparse observation bundles, accepted neural/optimizer states and portable evaluator. A clean-directory isolated-Python rescore is recorded separately; public release and a persistent dataset identifier remain submission preparation items.')
    manuscript=manuscript.replace('and no learned state passes all strict two-cycle event requirements.',
        'and none of the eight historical learned states passes all strict two-cycle event requirements under the original references.')
    manuscript=manuscript.replace('The comparison includes a same-solver interpolant and development counterfactuals that limit explanations based solely on readout repair or electrical spatial sampling.',
        'The comparison includes a same-solver interpolant and development counterfactuals that limit explanations based solely on readout repair or electrical spatial sampling. Additional matched phase-head continuations and a fixed-model time-reference perturbation delimit capacity, gate and numerical-sensitivity claims rather than silently expanding the method.')
    supplement=(OLD/'source/supplement.md').read_text(encoding='utf-8')
    start=supplement.index('## S9. Single bounded future numerical item')
    supplement=supplement[:start]+'''## S9. Executed reference sensitivity and portable array reproduction

The formerly proposed fixed-model temporal refinement is executed in this revision. Both references use 160 by 80 cells, time step 0.0003125, saving every eight steps and 8000 main steps. Original references and all original decisions remain separate. The actual algorithms, tolerances and no-clipping policy are unchanged. A descriptive metadata clarification corrects inherited window/reference labels; the executing trajectories used the correct pulse starts and step sizes, and the full 8001-point drive is unchanged by that correction. No reference trajectory is rerun for this documentation correction.

'''+sensitivity+'''

Table S11. Reference event changes, including both cycles and protocols.

{{TABLE:reference-events}}

The principal original/refined metrics and event measures for all sixteen objects are in tables/all-fixed-metrics.csv and tables/all-fixed-events.csv. The paired-effect-sizes.csv table separately reports each compared error, signed difference, percentage-point difference where the error is normalized, and relative error reduction; it distinguishes continuation from matched representation and historical method comparisons. The all-strict-failures.csv table names each failed original requirement, including any peak-phase failure. The complete portable results.json additionally retains all cycle peak/locality fields, validity checks and event-failure lists; the compact printed tables do not replace those records. The reference-margins table includes the same-norm triangle bounds; the JSON records distinguish reference-specific and fixed-original normalization. Old bottom-current scoring against the reference top current is preserved, while bottom-native errors are also supplied. A changed reference onset, event correspondence or threshold flag is a numerical sensitivity result, not retraining or a new physical event in a fixed predictor.

The local portable archive contains all scoring arrays and serialized geometry/ROI/rules. Python isolated mode runs portable/rescore.py in a clean extracted directory with NumPy only. It imports neither Torch nor SciPy, does not load checkpoints and performs zero linear solves. Its kernels preserve the original definitions; numerical metrics are compared at relative tolerance 2e-10 and absolute tolerance 2e-12, while categorical decisions must agree exactly. This tolerance concerns reproducibility arithmetic, not relaxed scientific effect gates.

The archive also supplies portable/reproduce_network.py as a separate opt-in entry. Its prepare action stages only the existing parent states, sparse observations and known-physics sources. Train repeats the specified six continuations; infer regenerates one selected fixed endpoint. Neither is invoked by the scoring or figure commands. Historical clean-parent retraining is a further, separate reproduction level.

## S10. Phase-head experiment, actual cost and complete outcomes

'''+interpretation+f'''

All six arms together used {tot['adam']} Adam updates, {tot['complete_evaluations']} complete fixed-target evaluations, {tot['training_forward']} training forward solves and {tot['training_adjoint']} adjoint solves, followed by {tot['inference_forward']} fine-grid projection solves. These quantities are not assumed to have equal unit cost. Trainable counts are 29827 for E_C and 31044 for E_R/E_I; each residual adds 1217. Total stored model counts, including the unused frozen V head, are 43140, 44357 and 57670, respectively. E_I additionally stores and evaluates 13313 frozen parent-phase parameters and differentiates that gate with respect to coordinates through second spatial derivatives. Its RMS amplitude normalization does not cancel this extra cost or match all gradients. No runtime acceleration claim is made.

Table S12. Actual matched work. Accepted L-BFGS steps and objective/gradient evaluation counts are different quantities.

{{{{TABLE:revision-execution}}}}

Table S13. All short-gap parent/control/candidate and soft metrics under both references. Percentages are normalized RMS errors times 100.

{{{{TABLE:phase-adapter-metrics}}}}

Table S14. All new-development support, timing, recovery and support masses. FN/FP masses are reporting diagnostics derived from fixed arrays.

{{{{TABLE:phase-adapter-events}}}}

Table S15. Potential, bottom current, energy and local Joule deposition for the same objects. A smaller integrated-energy error may coexist with a larger power-trajectory error; local q is a spatially resolved error, not an algebraic conservation check.

{{{{TABLE:phase-adapter-secondary}}}}

![Figure S1. All predeclared display times for seed 43.](figures/fig08-support-gate-seed43.png)

Figure S1. Same complete-domain times, colors and normalization as main Figure 8. The gate depends only on the frozen parent, never on reference error. Complete time traces accompany the portable scores; no favorable crop or time was selected from dense truth.

## S11. Updated evidence limits

'''+strict_text+'\n\n'+ '\n\n'.join(verdict)+'\n\n'+(HERE/'source/material-mapping.md').read_text(encoding='utf-8')+'\n\n## References\n\n{{REFERENCES}}\n'
    supplement=supplement.replace('The manuscript sprint itself reads only saved CSV/JSON/NPZ evidence. It performs zero optimizer updates, zero checkpoint loads or model evaluations, zero new electrical/reference solves and no stress access. No GPU instance is started for it.',
        'The original manuscript-only sprint read saved evidence and performed no new scientific execution. This revision is a separately authorized scientific experiment described in S9-S10, with six new coupled PINN endpoints and two new references. All GPU outputs were recovered and the current instance was shut down before local reference scoring. Stress was not read.')
    supplement=supplement.replace('The model increment is δ_θ = 8a(t)h_φ and is not divided by startup a(t).',
        'The base-model increment is δ_θ = 8a(t)h_φ and is not divided by startup a(t). For the new heads, the same interface includes R_ξ or normalized gR_ξ in h_φ, so the observation and PDE paths both use the composed phase.')
    supplement=supplement.replace('Reference first-onset time is 0.2406 in both cases.',
        'For these historical tables using the original references, first-onset time is 0.2406 in both cases; S9 reports the refined-reference onsets separately.')
    supplement=supplement.replace('No temporal refinement executed for this claim','Updated by the executed time-reference comparison in S9; not a spatial convergence result')
    supplement=supplement.replace('| Performance transfers to experimental oxide devices or arbitrary geometry |',
        f'| A frozen interface gate adds a matched benefit over the ordinary residual | {"VERIFIED bounded signal" if gate_seeds else "Not supported in this trial"} | Original-reference qualifying parent seeds: {gate_seeds or "none"}; refined: {gate_ref or "none"} | These are trained-parent developments, not new clean confirmations |\n'
        f'| Historical device advantages survive the tested time-step refinement | VERIFIED in {sum(newB)}/4 paired comparisons | Fixed arrays, both reference trajectories; Figure 9 | Does not establish spatial convergence |\n'
        '| Performance transfers to experimental oxide devices or arbitrary geometry |')
    supplement=supplement.replace('Strict two-cycle reliability has been achieved','The eight historical states meet the strict two-cycle requirements')
    supplement=supplement.replace('in strict usability','in the project-defined strict event requirements')
    supplement=supplement.replace('not a new independent rerun during manuscript preparation.',
        'with the array-only reproduction in this revision identified separately from the original training and the six new continuations.')
    supplement=supplement.replace('### S7.1 Rebuild this manuscript from saved evidence',
        '### S7.1 Rebuild the historical figures from saved evidence')
    supplement=supplement.replace('The existing snapshots are preserved. This package is a new local writing product,',
        'The original manuscript-only snapshot is preserved. That earlier package was a local writing product,')
    supplement=supplement.replace('### S7.2 Reproduce the numerical experiments separately',
        'For this revision, build_revision_analysis.py consumes the completed portable scoring results; update_manuscript.py integrates those results into the complete sources, and prepare_document.py/build_pdf.py rebuild the final documents. The revision README gives the commands. The old snapshot and its numerical values are preserved.\n\n### S7.2 Reproduce the historical numerical experiments separately')
    supplement=supplement.replace('| The narrow S threshold remains stable under refined references | UNKNOWN | Fixed-reference margin 4.4453125 × 10⁻⁶ | Updated',
        '| The narrow S threshold remains stable under refined references | '+
        ('VERIFIED for the tested reference pair' if ds['refined']['shorter']['43']['E_vs_soft']['A']['gain']['S'] else 'Contradicted by VERIFIED sensitivity')+
        ' | Historical margin 4.4453125 × 10⁻⁶; actual new margin in S9 | Updated')
    manuscript, supplement = revise(manuscript, supplement)
    (HERE/'source/manuscript.md').write_text(manuscript,encoding='utf-8')
    (HERE/'source/supplement.md').write_text(supplement,encoding='utf-8')
    summary=dict(adapter_increment_seeds=adapter_seeds,gate_original=gate_seeds,gate_refined=gate_ref,
        strict_original=strict_old,strict_refined=strict_new,historical_decision_flips=flips,
        historical_B_original=sum(oldB),historical_B_refined=sum(newB),interpretation=interpretation,reference_summary=sensitivity)
    (HERE/'build/scientific-conclusions.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
