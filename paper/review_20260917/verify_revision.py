"""Check revised claims against preserved evidence; no scientific execution."""
from pathlib import Path
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PAPER = ROOT/'paper/paper_revision_20260916'


def main():
    new = {n:(PAPER/'source'/f'{n}.md').read_text(encoding='utf-8') for n in ('manuscript','supplement')}
    old = {n:(HERE/'baseline/source'/f'{n}.md').read_text(encoding='utf-8') for n in new}
    refs = (PAPER/'references.md').read_text(encoding='utf-8')
    ids = [int(n) for n in re.findall(r'^\[(\d+)\]', refs, flags=re.M)]
    assert ids == list(range(1,17))
    for text in new.values():
        assert all(int(n) in ids for n in re.findall(r'\[(\d+)\]', text))
    images = lambda docs:set(re.findall(r'!\[[^\]]*\]\(([^)]+)\)', '\n'.join(docs.values())))
    tables = lambda docs:set(re.findall(r'\{\{TABLE:([^}]+)\}\}', '\n'.join(docs.values())))
    assert images(old) == images(new), 'A predeclared visual was lost or added'
    assert tables(old) == tables(new), 'An evidence-table include was lost or added'
    assert all((PAPER/p).is_file() for p in images(new))
    assert all((PAPER/'tables'/f'{n}.md').is_file() for n in tables(new))
    eqs = lambda s:re.findall(r'\$\$(.*?)\$\$', s, flags=re.S)
    assert eqs(old['manuscript'])[:20] == eqs(new['manuscript'])[:20], 'Core method equation changed'
    assert re.findall(r'\\(?:qquad|quad) \(([^)]+)\)\$\$',new['manuscript']) == [str(n) for n in range(1,24)]
    assert re.findall(r'\\(?:qquad|quad) \(([^)]+)\)\$\$',new['supplement']) == ['S1','S2','S3','S4a','S4b','S4c','S5','S6','S7','S8']
    assert re.findall(r'^Figure (\d+)\.',new['manuscript'],flags=re.M) == [str(n) for n in range(1,8)]
    assert re.findall(r'^Figure (S\d+)\.',new['supplement'],flags=re.M) == [f'S{n}' for n in range(1,5)]
    assert re.findall(r'^Table (S\d+)\.',new['supplement'],flags=re.M) == [f'S{n}' for n in range(1,17)]
    for name in new:
        expanded=(PAPER/f'{name}.md').read_text(encoding='utf-8')
        assert '{{TABLE:' not in expanded and '{{REFERENCES}}' not in expanded

    data=json.loads((ROOT/'outputs/submission-archive-20260916/rescore-output/results.json').read_text(encoding='utf-8'))
    assert len(data['records']['old']) == len(data['records']['refined']) == 16
    assert sum('/B_E' in name for name in data['records']['old']) == 2
    decisions=0
    for protocol in ('original','shorter'):
        for seed in ('29','43'):
            before=data['decisions']['old'][protocol][seed]
            after=data['decisions']['refined'][protocol][seed]
            assert before['E_vs_soft']['B']['passed'] and after['E_vs_soft']['B']['passed']
            for comparator in ('E_vs_soft','E_vs_B_E'):
                for criterion in ('A','B'):
                    assert before[comparator][criterion]['passed'] == after[comparator][criterion]['passed']
                    decisions+=1
    assert decisions==16
    for reference in ('old','refined'):
        for seed in ('29','43'):
            for arm in ('E_R','E_I'):
                decision=data['decisions'][reference]['shorter'][seed][arm]
                assert not decision['matched_A'] and not decision['matched_B']
    strict={ref:[n for n,v in data['records'][ref].items() if v['strict_device_pass']] for ref in ('old','refined')}
    assert strict == {'old':[], 'refined':['shorter/43/E_I']}
    row=data['records']['old']['shorter/43/E_I']['cycles'][0]
    rerow=data['records']['refined']['shorter/43/E_I']['cycles'][0]
    assert f"{row['recall']:.9f}" in new['manuscript']
    assert f"{rerow['recall']:.9f}" in new['manuscript']
    assert row['predicted_active_target_mass']==rerow['predicted_active_target_mass']
    assert rerow['true_positive_target_mass'] < row['true_positive_target_mass']
    numeric=[]
    records=data['records']['old']
    for seed in ('29','43'):
        parent=records[f'shorter/{seed}/E']['metrics']
        ctrl=records[f'shorter/{seed}/E_C']['metrics']
        cand=records[f'shorter/{seed}/E_I']['metrics']
        claims={'continued_phase_reduction':100*(1-ctrl['Ephi']/parent['Ephi']),
                'gated_power_reduction':100*(1-cand['power_trace_NRMSE']/ctrl['power_trace_NRMSE']),
                'gated_phase_change':100*(cand['Ephi']/ctrl['Ephi']-1)}
        for val in claims.values():
            assert f'{abs(val):.2f}%' in new['manuscript']
        numeric.append(dict(seed=seed,**claims))
    result=dict(status='PASS',scientific_execution=False,
        core_equations_unchanged=True,all_baseline_figures_and_table_includes_preserved=True,
        manuscript_figure_count=7,supplement_figure_count=4,
        evidence_objects=dict(historical_learned=8,interpolants=2,continuations=6),
        historical_comparisons=8,unchanged_historical_AB_decisions=decisions,
        strict_reference_specific_outcomes=strict,numeric_claim_checks=numeric,
        scope='Source/artifact consistency and arithmetic against saved JSON; no models, solver or rescoring of arrays')
    (HERE/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
