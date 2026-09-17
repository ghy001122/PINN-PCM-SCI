"""Integrate completed spatial evidence; never infer an uncomputed outcome."""
from pathlib import Path
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
RUN=ROOT/'outputs/runs/20260917-lf11-spatial-reference'


def main():
    summary=json.loads((HERE/'spatial-summary.json').read_text(encoding='utf-8'))
    results=json.loads((RUN/'scoring/results.json').read_text(encoding='utf-8'))
    if summary['status']!='COMPLETE':raise ValueError('No completed spatial analysis')
    n=summary['historical_E_F_B_passes']['spatial']
    changed=summary['historical_rule_changes_from_time_refined']
    strict=summary['strict_objects']['spatial']
    object_label=lambda v: v.replace('original/','original ').replace('shorter/','earlier-pulse ').replace('/',' / ')
    strict_text=', '.join(object_label(v) for v in strict) if strict else 'none'
    changes_text='none' if not changed else '; '.join(
        f"{r['protocol']} seed {r['seed']}, E/{r['control']}, {r['layer']}: {r['previous']} to {r['spatial']}" for r in changed)
    total=sum(r['total'] for r in summary['execution'])
    soft=[r for r in summary['comparisons'] if r['control']=='F']
    percent_range=lambda key: f"{100*min(r[key] for r in soft):.2f}–{100*max(r[key] for r in soft):.2f}"
    old=json.loads((ROOT/'outputs/submission-archive-20260916/rescore-output/results.json').read_text(encoding='utf-8'))
    d=results['decisions'];objects=results['records']
    phase_be=-100*d['original']['29']['E_vs_B_E']['A']['relative_changes']['Ephi']
    phase_s=-100*d['shorter']['43']['E_vs_soft']['A']['relative_changes']['S']
    new_be=d['original']['43']['E_vs_B_E']['B']['relative_changes']
    old_recall=old['records']['refined']['shorter/43/E_I']['cycles'][0]['recall']
    new_recall=objects['shorter/43/E_I']['cycles'][0]['recall']
    new_timings=[objects[f'shorter/{seed}/E']['cycles'][1]['timing_absolute'] for seed in ('29','43')]
    block=f'''### 5.8 Spatial-reference sensitivity with fixed predictions

A further reference changes the grid from 160 × 80 to 240 × 120 at the already refined time step 0.0003125, separately for each protocol. Every learned prediction and electrical readout is held fixed. Reference fields are conservatively restricted to the original scoring cells; reference terminal current and power retain their native fine-grid values. This tests the specified reference perturbation, including its mapping, rather than model-inference grid independence.

The complete device criterion against projected F passes in {n}/4 historical pairs under this spatial reference, compared with 4/4 under each temporal reference. Across both controls and both rules, {len(changed)} of the sixteen historical decisions change relative to the time-refined reference. Supplement S15 lists every comparison and the full endpoint measures; Figure 8 shows the relative-gain margins, which do not by themselves replace the complete rules.

Relative current and power error reductions against projected F are {percent_range('bottom_current_NRMSE_relative_error_reduction')}% and {percent_range('power_trace_NRMSE_relative_error_reduction')}%, respectively. Their absolute NRMSE reductions are {percent_range('bottom_current_NRMSE_absolute_error_reduction')} and {percent_range('power_trace_NRMSE_absolute_error_reduction')} percentage points. Across the eight historical comparisons, the directions of the S, phase, temperature, potential, current and power error differences do not reverse. Threshold conclusions are more sensitive: original seed 29 improves phase RMS over B_E by {phase_be:.2f}%, and earlier-pulse seed 43 improves S over F by {phase_s:.2f}%, each below the prescribed 10% requirement. Conversely, original seed 43 now crosses the device criterion against B_E, with current/power gains of {-100*new_be['bottom_current_NRMSE']:.2f}%/{-100*new_be['power_trace_NRMSE']:.2f}%. That crossing remains specific to the spatial reference.

![Spatial-reference margins for fixed predictions](figures/fig12-spatial-reference-margins.png)

Figure 8. Reference-only comparison of the four fixed E/F pairs. O and S denote the original and earlier-pulse cases. The spatial reference supplies native terminal quantities and volume-restricted fields. Positive bars satisfy the relative-gain component; absolute floors and noninferiority guards remain in the complete comparisons. Changing reference never selects or retrains a network.

Across the sixteen fixed objects, the spatial-reference strict outcomes are {strict_text}. The historical absence of strict capability under the original reference is unchanged; passing a later reference cannot establish robustness across all tested references. Thresholding the restricted phase is also different from restricting the fine active indicator. The largest resulting S discrepancy is {summary['mapping_summary']['max_S_gap']:.7g}; the largest absolute recall change is {100*summary['mapping_summary']['max_abs_recall_change']:.5g} percentage points. These alternative mapping quantities are diagnostics only, not substitute scores used to choose a favorable decision.

The previously passing gated seed-43 continuation loses strict status: its first-cycle recall changes from {old_recall:.9f} under temporal refinement to {new_recall:.9f} under spatial refinement, with the prediction unchanged (Table S23). Historical earlier-pulse E also has second-cycle timing errors of {new_timings[0]:.6f} and {new_timings[1]:.6f}, both above 0.005. Thus the spatial check adds a timing limitation to the previously reported recall limitation; it does not merely repeat the earlier strict verdict.

Two spatial resolutions, one refinement ratio and a shared numerical algorithm do not establish a convergence order or continuum accuracy. The complete state, event and device results therefore support only the numerical comparisons actually made. Native fine-grid event capability and prediction-readout grid independence remain untested.

'''
    p=HERE/'source/manuscript.md'
    text=p.read_text(encoding='utf-8')
    if '### 5.8 ' in text:raise ValueError('Rebuild base revision before applying spatial update again')
    text=text.replace('## 6. Discussion',block+'## 6. Discussion',1)
    original='With predictions fixed, halving the reference time step preserves all four paired device advantages.'
    assert original in text
    text=text.replace(original,original+f' A separate spatial-reference perturbation with conservative field restriction retains the complete device criterion in {n}/4 pairs, while changing phase-threshold and strict-event conclusions.',1)
    old='The new fixed-prediction comparison quantifies one temporal-reference perturbation and its actual decision changes in Section 5.6. It remains a fixed-spatial-discretization study; unchanged rankings cannot be promoted to continuum accuracy.'
    assert old in text
    text=text.replace(old,'The fixed-prediction comparisons quantify temporal refinement and a spatial perturbation with a declared conservative mapping in Sections 5.6 and 5.8. They do not establish convergence order, model-inference grid independence or continuum accuracy.',1)
    text=text.replace('All formal comparisons use the fixed reference discretization and previously fixed selection rules.',
        'Primary results use the original reference discretization; the temporal and spatial checks change only the declared reference and retain the original comparison rules.',1)
    old='The present evidence therefore supports a bounded computational reconstruction method, with spatial-reference sensitivity and material-specific validation remaining distinct next questions.'
    assert old in text
    text=text.replace(old,f'The further spatial-reference check retains the complete device criterion against soft in {n}/4 pairs under its declared mapping. The evidence supports a bounded computational reconstruction method; continuum accuracy, prediction-readout grid independence and material-specific validation remain unestablished.',1)
    old='The experiment was completed on 16 September 2026 and this manuscript was editorially revised on 17 September 2026 without new scientific execution; it does not reuse either published version identifier as its own.'
    assert old in text
    text=text.replace(old,'The phase-head and temporal-reference experiment was completed on 16 September 2026. Editorial revision on 17 September 2026 was followed by the separate fixed-prediction spatial-reference experiment reported in Section 5.8. This revision does not reuse either published version identifier as its own.',1)
    text=text.replace('The present revision adds six phase-head PINN continuations, their projected outputs, two time-refined numerical references and array-only rescoring.',
        'The phase-head experiment added six PINN continuations, their projected outputs and two time-refined references. The later spatial check adds two reference trajectories and array-only rescoring of all sixteen saved objects.',1)
    text=text.replace('The local submission archive now contains the four references, sixteen fixed prediction/readout objects, two sparse observation bundles, accepted neural/optimizer states and portable evaluator.',
        'The original local submission archive contains the four temporal-reference trajectories, sixteen fixed prediction/readout objects, two sparse observation bundles, accepted neural/optimizer states and portable evaluator. The spatial extension is separate: two native reference trajectories, their declared field mappings, all new scores and the executed numerical sources are retained without changing that archive.',1)
    p.write_text(text,encoding='utf-8')

    section=r'''## S15. Fixed-prediction spatial-reference experiment

### S15.1 Numerical change and common comparison space

Both protocols are solved on 240 × 120 cells with dt = 0.0003125 over [0, 2.5], saving every eighth step. The reference numerical algorithm, coefficients, initial-state formula, contact geometry, tolerances and finite pulse histories are inherited unchanged. Each trajectory takes 8000 main steps with a separate limit of 200000 internal linear solves. These are new numerical references, not new neural training or new physical cases.

All sixteen predicted field arrays and their original 160 × 80 electrical readouts are unchanged. For fine cells c_i and scoring cells C_j, use the exact intersection-volume restriction W. If v_i and V_j denote cell volumes, the following identities preserve constants and domain integrals:

$$ W_{ji}=|C_j\cap c_i|/V_j,\qquad W_{ji}\geq0,\qquad\sum_iW_{ji}=1,\qquad\sum_jV_jW_{ji}=v_i.\qquad(S12) $$

The fine V, T, phase and local Joule density are restricted by W. Their integral consistency is checked on the saved arrays. Terminal current and total power remain the native fine-reference outputs; recomputing them from restricted V would introduce another readout and is not done. The projected neural readouts also are not recomputed on a new grid. Thus the new comparison cannot establish neural electrical-readout grid independence or claim that the mapped fields solve the coarse discrete equations.

The physical heater edges align with faces at both resolutions. The two fine references are compared over the identical physical prefix before the earlier second pulse. Numerical validity and the actual solve counters are retained separately from prediction accuracy. Local deposition and total dissipation identities remain operator-consistency checks, not independent physical validation.

Table S18. Actual work in the two spatial references. O and S denote the original and earlier-pulse protocols. Counts are actual electric, thermal and phase linear solves; a main time step can contain multiple nonlinear blocks and solves. No model evaluation or new prediction projection is included.

{{TABLE:spatial-execution}}

Table S19. Spatial-reference differences from the time-refined 160 × 80 reference. Field discrepancies use the fixed scoring measure after restriction; terminal discrepancies use native reference traces. They are numerical differences, not bounds on continuum error.

{{TABLE:spatial-reference-deltas}}

### S15.2 Full endpoint comparisons and counterexamples

Table S20. Every fixed endpoint under the spatial reference, including both deterministic interpolants and all six continuations. Percentages multiply the corresponding normalized RMS errors by 100. Strict refers to the original rule evaluated with the mapped phase reference. It is not a native fine-grid qualification. Full S, voltage, bottom-current, local-heat errors and normalization data are in spatial-all-fixed-metrics.csv, which retains all three references and the separately reported errors using the original fixed denominators. Complete two-cycle records are in spatial-all-fixed-events.csv.

{{TABLE:spatial-fixed-endpoints}}

Table S21. All eight historical comparisons, both rules and all three references. The gain columns are relative error reductions under the spatial reference. The complete A/B flags include the original absolute floors and noninferiority tests. Rows are related comparisons, not independent statistical samples.

{{TABLE:spatial-historical-comparisons}}

Table S22. All phase-head continuation decisions under all three references. Matched A/B include the continued E_C control and the required parent noninferiority checks. A reference-specific strict crossing is kept separate from a reproducible matched phase or device gain. No threshold, endpoint or architecture is changed.

{{TABLE:spatial-continuation-decisions}}

Table S23. The previously reference-sensitive gated seed-43 continuation, with identical predicted fields and event times in all rows. The first-cycle recall requirement is 0.9 and the timing requirement is 0.005 for each cycle; these displayed components alone do not replace the complete strict rule. All other endpoint/cycle records remain in spatial-all-fixed-events.csv and their complete decisions in Table S22. The spatial result removes the earlier reference-specific strict crossing.

{{TABLE:spatial-strict-counterexample}}

![Native spatial-reference terminal trace differences](figures/fig13-spatial-native-traces.png)

Figure S6. Native fine-reference current and power minus the time-refined reference traces, with the original two protocols shown separately. Fields used for scoring are restricted, but the terminal quantities plotted here are not recomputed from those restricted fields. These traces contain no new model prediction.

### S15.3 Thresholding and restriction do not commute

The primary score thresholds W phi_h at 0.5. A separately named diagnostic restricts the fine active indicator instead. For the fixed coarse binary prediction P, define a = W 1(phi_h >= 0.5) and b = 1(W phi_h >= 0.5). The alternative support and symmetric difference integrate the fractional overlap with the same predicted set. The reverse triangle inequality gives the following bound in the fixed space-time measure mu:

$$ |S(P,a)-S(P,b)|\leq\int|a-b|\,d\mu.\qquad(S13) $$

This diagnostic interprets P as constant within each scoring cell. It does not evaluate the network on native fine points. The primary diagnostic reproduces the frozen scorer's S, overlap, predicted/reference support masses and recall before the alternative mapping is compared. Both mappings retain the original global trapezoidal time weights and heating-window selection. The alternative scores cannot replace a less favorable primary decision.

Table S24. Threshold-map discrepancy for every fixed object. S primary uses thresholded restricted phase; S indicator uses restricted fine active fraction. The common bound depends on the reference mapping, whereas the realized score change also depends on the fixed prediction. Full per-cycle masses and recall differences are retained in spatial-threshold-events.csv.

{{TABLE:spatial-threshold-mapping}}

![Threshold-map discrepancy and all cycle recall shifts](figures/fig14-spatial-threshold-mapping.png)

Figure S7. Report-only consequences of exchanging thresholding and restriction. All sixteen fixed objects are retained. Upper panel: observed S changes and the mapping bound. Lower panel: alternative-minus-primary recall changes in both cycles. These are not additional model results or new gate outcomes.

### S15.4 Reproduction and evidence boundary

The spatial extension is kept separately in outputs/runs/20260917-lf11-spatial-reference: native result files, mapped references, the restricted indicators, source snapshots, intents, terminal counters and complete scores. The original array archive remains unchanged. phk_v23_spatial_reference.py generates the two trajectories; spatial_analysis.py consumes only completed references and archived prediction arrays; spatial_report.py produces the tables and figures. No scientific execution occurs in the document build.

Two space resolutions at one fixed time step do not identify a reliable convergence order. Both use the same numerical algorithm, and field comparisons include a specified restriction. The experiment therefore extends the tested numerical-reference range without supplying an independent solver, continuum truth, zero-shot transfer or material validation. Stable strict capability, independent remaining-PDE necessity and isolated VJP causality remain separate claims.

'''
    outcome=f'''The saved-data outcome is {n}/4 complete historical E/F device passes under the spatial reference. Historical decision changes from the time-refined reference are: {changes_text}. Spatial-reference strict objects are: {strict_text}. Actual reference work totals {total} internal linear solves across the two fixed trajectories. These statements are generated from the complete saved result tables, without selecting a favorable model or case.

'''
    p=HERE/'source/supplement.md';text=p.read_text(encoding='utf-8')
    if '## S15.' in text:raise ValueError('Rebuild base revision before applying spatial update again')
    text=text.replace('This revision is a separately authorized scientific experiment described in S9-S10, with six new coupled PINN endpoints and two new references. All GPU outputs were recovered and the current instance was shut down before local reference scoring.',
        'The phase-head and temporal-reference experiment in S9-S10 added six coupled PINN endpoints and two time-refined references. Its GPU outputs were recovered and the instance was shut down before local reference scoring. The separate spatial study in S15 adds two CPU reference trajectories, with all neural predictions fixed and no GPU use.',1)
    text=text.replace('## References',section+outcome+'## References',1)
    p.write_text(text,encoding='utf-8')
    print('Integrated completed spatial evidence with all comparisons and limitations.')


if __name__=='__main__':main()
