"""Apply the next Roadmap revision to the preserved, reviewed source draft."""
from pathlib import Path
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent
PREVIOUS=HERE.parent/'paper_revision_20260916'


def main():
    data=json.loads((HERE/'reference-certificates.json').read_text(encoding='utf-8'))
    manuscript=(PREVIOUS/'source/manuscript.md').read_text(encoding='utf-8')
    supplement=(PREVIOUS/'source/supplement.md').read_text(encoding='utf-8')
    addition='''A conservative perturbation calculation further separates empirical retention from a uniform guarantee. At a perturbation budget equal to the observed time-reference discrepancy, the current and power gain components are certified in all four E/F pairs, but the complete device rule is certified only in the two earlier-pulse pairs; the original pairs are limited by the temperature noninferiority guard. This is a sufficient-bound limitation, not an observed reversal: all four complete rules retain their outcomes under the actual refined reference. Supplement S14 gives the derivation, absolute-tolerance treatment and all comparisons. The observed discrepancy is not an estimate or upper bound for unknown continuum error.

'''
    anchor='### 5.7 Added phase capacity gives mixed, reference-dependent effects'
    if manuscript.count(anchor)!=1:raise ValueError('main insertion anchor')
    manuscript=manuscript.replace(anchor,addition+anchor)
    section=r'''## S14. Complete-rule reference perturbation bounds

### S14.1 Assumptions and sufficient conditions

The original margin plot separates individual error gains. A complete A/B rule also contains noninferiority guards and absolute floors. We now evaluate sufficient conditions for the whole rule from the already saved metrics and time-reference discrepancies; this analysis runs no neural model, reference solver or array rescoring. It neither changes the historical decisions nor supplies new spatial evidence.

For a candidate and comparator with fixed predictions, let e_c and e_b be their errors in the same unnormalized norm, and d > 0 their shared normalization. For S, the reference perturbation is measured by the symmetric-difference distance between reference active sets; for temperature absorb the fixed 0.45 divisor into the norm. Assume a changed reference changes either error by at most r δ, and d by at most r δ_d. The normalizer bound δ_d is zero for fixed normalizers; for current and power, it is set to the corresponding reference RMS discrepancy, which bounds the normalizer change by the reverse triangle inequality. The argument concerns a blockwise reference-distance bound, not a probability distribution. In particular, the bound on active-set distance is separate from the phase RMS bound: an RMS perturbation alone need not control threshold crossings.

$$ |e'_c-e_c|,\ |e'_b-e_b|\leq r\delta,\qquad |d'-d|\leq r\delta_d,\qquad d'>0.\qquad (S9) $$

A relative gain η together with an absolute normalized floor τ requires both inequalities below. Substitution of the worst allowed error changes gives a sufficient condition that retains the original max rule:

$$ (1-\eta)e_b-e_c\geq r(2-\eta)\delta,\qquad e_b-e_c-\tau d\geq r(2\delta+\tau\delta_d).\qquad (S10) $$

For a relative noninferiority allowance ν, either of the following inequalities is sufficient, because the permitted deterioration is the larger of the relative and absolute allowances:

$$ (1+\nu)e_b-e_c\geq r(2+\nu)\delta\quad\mathrm{or}\quad e_b-e_c+\tau d\geq r(2\delta+\tau\delta_d).\qquad (S11) $$

We use η = 0.1, ν = 0.05 and the unchanged metric-specific τ. For each gain the sufficient radius is the smaller branch radius from (S10); for each guard it is the larger branch radius from (S11). The minimum across all required components gives the reported whole-rule sufficient radius, with negative values reported as zero and an originally failed rule still marked failed. Positive-normalizer conditions are retained. This is a conservative guarantee from the chosen inequalities, not the largest true radius permitted by correlated reference errors.

### S14.2 What the saved evidence can and cannot certify

The reference distance at r = 1 is exactly the measured old-to-time-refined discrepancy for each metric block. Using its value to define a perturbation budget does not imply that an unknown spatial reference, the continuum solution or an experiment lies inside that budget. Empirical comparison against the actual refined reference remains the direct evidence.

Table S17. All eight historical comparisons and both rules. “Gain bound” covers the required gain components; “full bound” also requires every noninferiority guard and the absolute floors. Earlier denotes the earlier-pulse protocol; T guard is temperature noninferiority. A radius below one is not a failed empirical comparison or proof of instability.

{{TABLE:reference-certificates}}

All four E/F current-and-power gain pairs admit a certificate at r = 1. The full device rule admits one for the earlier-pulse pairs only. The original-protocol radii are 0.9546 (seed29) and 0.6950 (seed43), both limited by temperature noninferiority; the earlier-pulse radii are 1.5317 and 1.2435. The narrow earlier-pulse seed43 phase rule has radius 0.1399, limited by S, although that rule passes for both references actually evaluated. Across all controls, nine of the sixteen rule instances have a sufficient certificate at r = 1; these are algebraic checks on shared data, not sixteen independent validations.

![Complete device-rule perturbation bounds](figures/fig11-complete-reference-certificates.png)

Figure S5. Sufficient perturbation radii for E against F/projected. The dashed line is the observed temporal-reference distance used as a budget, not a confidence threshold. Current and power gain conditions alone allow larger radii than the complete device rule. The complete empirical rule passes under both actual references in all four pairs, including those whose conservative radius is below one. No new reference or learned prediction enters this figure.

The expanded calculation identifies the limiting criterion without selecting a new checkpoint, threshold or comparator. It motivates measuring spatial-reference differences directly and cannot substitute for that experiment. `reference_certificates.py` reproduces this table and the component CSV from the saved scalar records. The small synthetic interval-corner check tests the algebra against the original max rules, not the physical model or empirical success rates.

'''
    if supplement.count('## References')!=1:raise ValueError('supplement insertion anchor')
    supplement=supplement.replace('## References',section+'## References')
    for name,text in [('manuscript',manuscript),('supplement',supplement)]:
        (HERE/'source'/f'{name}.md').write_text(text,encoding='utf-8')
    selected=[r for r in data['summary'] if r['baseline']=='F' and r['layer']=='B']
    gain=[]
    for r in selected:
        parts=[p for p in data['components'] if p['candidate']==f"{r['protocol']}/{r['seed']}/E" and
               p['baseline'].endswith('/F') and p['layer']=='B' and p['kind']=='gain']
        gain.append(min(p['sufficient_radius'] for p in parts))
    labels=[('Original' if r['protocol']=='original' else 'Earlier pulse')+' / '+str(r['seed']) for r in selected]
    x=np.arange(4)
    fig,ax=plt.subplots(figsize=(8.1,4.2),layout='constrained')
    ax.bar(x-.18,gain,.36,label='Current + power gain conditions',color='#316e85')
    whole=[r['sufficient_radius'] for r in selected]
    ax.bar(x+.18,whole,.36,label='Complete device rule',color='#c07832')
    ax.axhline(1,color='#333333',ls='--',lw=1)
    for xx,values in [(x-.18,gain),(x+.18,whole)]:
        for xpos,y in zip(xx,values):ax.text(xpos,y*1.07,f'{y:.3g}',ha='center',fontsize=9)
    ax.set_yscale('log');ax.set_ylim(.45,max(gain)*2.3)
    ax.set_xticks(x,labels);ax.set_ylabel('Sufficient perturbation radius r')
    ax.grid(axis='y',alpha=.18);ax.legend(loc='upper left',fontsize=9)
    fig.savefig(HERE/'figures/fig11-complete-reference-certificates.png',dpi=220)
    fig.savefig(HERE/'figures/fig11-complete-reference-certificates.pdf')
    plt.close(fig)
    print('Updated manuscript and supplement from preserved review; added complete-rule reference analysis.')


if __name__=='__main__':main()
