"""Complete-gate sufficient bounds using only previously saved scalar results.

The radius is relative to an observed numerical-reference discrepancy. It is
not an estimated continuum-error bound, confidence interval or new experiment.
"""
from pathlib import Path
import csv
import itertools
import json

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ARCHIVE = ROOT / "outputs/submission-archive-20260916"


def radius(c, b, delta, normalizer, delta_normalizer, kind, relative, absolute):
    if kind == "gain":
        rel = ((1-relative)*b-c)/((2-relative)*delta)
        ab = (b-c-absolute*normalizer)/(2*delta+absolute*delta_normalizer)
        raw = min(rel, ab)
        nominal = b-c >= max(relative*b, absolute*normalizer)
    else:
        rel = ((1+relative)*b-c)/((2+relative)*delta)
        ab = (b-c+absolute*normalizer)/(2*delta+absolute*delta_normalizer)
        raw = max(rel, ab)
        nominal = c-b <= max(relative*b, absolute*normalizer)
    # Stay in the positive-normalizer regime; no zero-denominator conclusion.
    if delta_normalizer:
        raw = min(raw, .999999*normalizer/delta_normalizer)
    return dict(relative_radius=rel, absolute_radius=ab, sufficient_radius=max(0., raw),
                nominal_pass=bool(nominal), certified_at_observed_radius=bool(nominal and raw>=1.))


def check_bounds():
    rng = np.random.default_rng(170917)
    verified = 0
    for _ in range(500):
        n = rng.uniform(.5, 3.)
        c, b = rng.uniform(.0001, .15, 2)*n
        delta = rng.uniform(.00001,.01)*n
        dn = delta if rng.random() < .5 else 0.
        atol = rng.choice([1e-6, .01, .1])
        for kind, rel in (("gain",.1),("noninferior",.05)):
            result = radius(c,b,delta,n,dn,kind,rel,atol)
            r = .999*result["sufficient_radius"]
            if not result["nominal_pass"] or r<=0: continue
            # Verify the original max rule at every interval corner, rather
            # than repeating the certificate formula as the expected value.
            for ec,eb,en in itertools.product((-1,1),repeat=3):
                cc=max(0.,c+ec*r*delta);bb=max(0.,b+eb*r*delta);nn=n+en*r*dn
                assert nn>0
                passed=(bb-cc>=max(rel*bb,atol*nn)-1e-13 if kind=="gain" else
                        cc-bb<=max(rel*bb,atol*nn)+1e-13)
                if not passed: raise AssertionError((c,b,delta,n,dn,kind,result,cc,bb,nn))
                verified+=1
    return dict(status="PASS", interval_corner_checks=verified, new_solves=0,
                scope="algebraic sufficient bounds, not empirical research repeats")


def main():
    checks = check_bounds()
    data = json.loads((ARCHIVE/"rescore-output/results.json").read_text(encoding="utf-8"))
    details, summaries = [], []
    for protocol in ("original","shorter"):
        cfg=json.loads((ARCHIVE/f"definitions/{protocol}.json").read_text(encoding="utf-8"))
        delta=data["reference_sensitivity"][protocol]["delta"]
        old=data["records"]["old"]
        for seed in (29,43):
            candidate=f"{protocol}/{seed}/E"
            for baseline in (f"{protocol}/{seed}/F",f"{protocol}/B_E"):
                c,b=old[candidate],old[baseline]
                n=c["normalizers"]
                for layer in ("A","B"):
                    gains=(['S','Ephi'] if layer=='A' else cfg['functional_rule']['gain'])
                    guards=(['ET','EI','EV'] if layer=='A' else cfg['functional_rule']['noninferior'])
                    components=[]
                    for kind,keys in (("gain",gains),("noninferior",guards)):
                        for key in keys:
                            scale = n['top_current'] if key in ('EI','bottom_current_NRMSE') else n['power'] if key=='power_trace_NRMSE' else 1.
                            dd = delta['EI_rms'] if key in ('EI','bottom_current_NRMSE') else delta['power_rms'] if key=='power_trace_NRMSE' else delta[key]
                            dn = dd if key in ('EI','bottom_current_NRMSE','power_trace_NRMSE') else 0.
                            atol=(cfg['functional_rule']['extra_normalized_absolute_tolerance'] if layer=='B' and kind=='gain' else cfg['decision']['absolute_tolerance'][key])
                            result=radius(c['metrics'][key]*scale,b['metrics'][key]*scale,dd,scale,dn,
                                          kind,.1 if kind=='gain' else .05,atol)
                            row=dict(protocol=protocol,seed=seed,candidate=candidate,baseline=baseline,
                                layer=layer,kind=kind,metric=key,reference_delta=dd,
                                base_normalizer=scale,**result)
                            details.append(row);components.append(row)
                    limiting=min(components,key=lambda r:r['sufficient_radius'])
                    summaries.append(dict(protocol=protocol,seed=seed,baseline='F' if baseline.endswith('/F') else 'B_E',
                        layer=layer,nominal_pass=all(r['nominal_pass'] for r in components),
                        all_gain_components_certified=all(r['certified_at_observed_radius'] for r in components if r['kind']=='gain'),
                        full_gate_certified=all(r['certified_at_observed_radius'] for r in components),
                        sufficient_radius=limiting['sufficient_radius'],limiting_component=limiting['kind']+':'+limiting['metric']))
    result=dict(status='COMPLETE_SAVED_DATA_ANALYSIS',checks=checks,summary=summaries,components=details,
        interpretation='Sufficient certificates for an assumed blockwise reference-error ball scaled by the observed time-step discrepancy; not a continuum uncertainty estimate',
        training=0,checkpoint_evaluations=0,new_pde_solves=0)
    (HERE/'reference-certificates.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    out=HERE/'tables';out.mkdir(exist_ok=True)
    for name,rows in [('reference-certificates',summaries),('reference-certificate-components',details)]:
        with (out/f'{name}.csv').open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    headings=['Case','Seed','Control','Rule','Original pass','Gain bound','Full bound','Radius r','Limiting test']
    lines=['| '+' | '.join(headings)+' |','| '+' | '.join(['---']*len(headings))+' |']
    labels={'noninferior:ET':'T guard','gain:Ephi':'Phase gain','gain:S':'S gain',
            'gain:bottom_current_NRMSE':'Bottom I gain'}
    for r in summaries:
        yes=lambda key:'yes' if r[key] else 'no'
        lines.append('| '+' | '.join(['Original' if r['protocol']=='original' else 'Earlier',str(r['seed']),r['baseline'],r['layer'],
            yes('nominal_pass'),yes('all_gain_components_certified'),yes('full_gate_certified'),
            f"{r['sufficient_radius']:.4g}",labels[r['limiting_component']]])+' |')
    (out/'reference-certificates.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(dict(checks=checks,summary=summaries),ensure_ascii=False))


if __name__=='__main__':main()
