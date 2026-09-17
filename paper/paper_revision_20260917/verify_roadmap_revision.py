"""Check the added analysis against saved results, without model/solver execution."""
from pathlib import Path
import importlib.util
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREVIOUS = HERE.parent / 'paper_revision_20260916'
ARCHIVE = ROOT / 'outputs/submission-archive-20260916'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    spec = importlib.util.spec_from_file_location('saved_metric_rules', ARCHIVE / 'portable/frozen_metrics.py')
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    evidence = read(ARCHIVE / 'rescore-output/results.json')
    analysis = read(HERE / 'reference-certificates.json')
    assert analysis['checks']['status'] == 'PASS'
    assert analysis['training'] == analysis['checkpoint_evaluations'] == analysis['new_pde_solves'] == 0
    assert len(analysis['summary']) == 16
    component_checks = bound_checks = 0
    for row in analysis['summary']:
        protocol, seed = row['protocol'], row['seed']
        candidate = f'{protocol}/{seed}/E'
        baseline = f'{protocol}/{seed}/F' if row['baseline'] == 'F' else f'{protocol}/B_E'
        cfg = read(ARCHIVE / f'definitions/{protocol}.json')
        assert cfg['decision']['relative_improvement'] == .1
        assert cfg['decision']['relative_noninferiority'] == .05
        c, b = evidence['records']['old'][candidate], evidence['records']['old'][baseline]
        rule = (core.comparison(c, b, cfg['decision']) if row['layer'] == 'A'
                else core.functional_comparison(c, b, cfg))
        category = 'E_vs_soft' if row['baseline'] == 'F' else 'E_vs_B_E'
        old_saved = evidence['decisions']['old'][protocol][str(seed)][category][row['layer']]
        new_saved = evidence['decisions']['refined'][protocol][str(seed)][category][row['layer']]
        assert row['nominal_pass'] == rule['passed'] == old_saved['passed']
        assert old_saved['passed'] == new_saved['passed']
        assert not row['full_gate_certified'] or new_saved['passed']
        parts = [p for p in analysis['components'] if p['candidate'] == candidate
                 and p['baseline'] == baseline and p['layer'] == row['layer']]
        for part in parts:
            metric = part['metric']
            assert part['nominal_pass'] == rule[part['kind']][metric]
            component_checks += 1
            for obj in (candidate, baseline):
                old, new = (evidence['records'][ref][obj] for ref in ('old', 'refined'))
                scale_key = ('top_current' if metric in ('EI', 'bottom_current_NRMSE') else
                             'power' if metric == 'power_trace_NRMSE' else None)
                n0 = old['normalizers'][scale_key] if scale_key else 1.
                n1 = new['normalizers'][scale_key] if scale_key else 1.
                delta = part['reference_delta']
                assert abs(new['metrics'][metric]*n1-old['metrics'][metric]*n0) <= delta+2e-12
                if scale_key:
                    assert abs(n1-n0) <= delta+2e-12
                bound_checks += 1
    device = [r for r in analysis['summary'] if r['baseline'] == 'F' and r['layer'] == 'B']
    assert len(device) == 4 and all(r['nominal_pass'] for r in device)
    assert all(r['all_gain_components_certified'] for r in device)
    assert [r['protocol'] for r in device if r['full_gate_certified']] == ['shorter', 'shorter']
    assert sum(r['full_gate_certified'] for r in analysis['summary']) == 9
    assert all(r['limiting_component'] == 'noninferior:ET' for r in device)

    current, previous = {}, {}
    for name in ('manuscript', 'supplement'):
        current[name] = (HERE / f'source/{name}.md').read_text(encoding='utf-8')
        previous[name] = (PREVIOUS / f'source/{name}.md').read_text(encoding='utf-8')
        eq = lambda text: re.findall(r'\$\$(.*?)\$\$', text, flags=re.S)
        assert eq(current[name])[:len(eq(previous[name]))] == eq(previous[name])
        expanded = (HERE / f'{name}.md').read_text(encoding='utf-8')
        assert '{{TABLE:' not in expanded and '{{REFERENCES}}' not in expanded
    assert len(re.findall(r'\$\$(.*?)\$\$', current['manuscript'], flags=re.S)) == 23
    assert re.findall(r'\\(?:qquad|quad) \(([^)]+)\)\s*\$\$', current['supplement']) == [
        'S1', 'S2', 'S3', 'S4a', 'S4b', 'S4c', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10', 'S11']
    assert 'does not authorize' not in current['supplement']
    assert '[author names and affiliations to be supplied]' in current['manuscript']
    refs = (HERE / 'references.md').read_text(encoding='utf-8')
    ids = [int(n) for n in re.findall(r'^\[(\d+)\]', refs, flags=re.M)]
    assert ids == list(range(1, 17))
    for name in ('references.md', 'references.bib'):
        assert (HERE / name).read_bytes() == (PREVIOUS / name).read_bytes()
    for text in current.values():
        assert all(int(n) in ids for n in re.findall(r'\[(\d+)\]', text))
        for image in re.findall(r'!\[[^\]]*\]\(([^)]+)\)', text):
            assert (HERE / image).is_file()
        for table in re.findall(r'\{\{TABLE:([^}]+)\}\}', text):
            assert (HERE / 'tables' / f'{table}.md').is_file()
    for category in ('tables', 'figures'):
        for asset in (PREVIOUS / category).iterdir():
            if asset.is_file():
                assert (HERE / category / asset.name).read_bytes() == asset.read_bytes(), asset.name

    render = read(HERE / 'build/visual-review/render-summary.json')
    for doc in render.values():
        for page in doc['pages']:
            assert not page['outside_page'] and not page['body_into_footer']
            assert not page['replacement_character'] and page['characters'] > 0
    result = dict(status='PASS', scope='Saved scalar rules, formulas, assets and rendered text; no array rescoring',
        original_rules_reproduced=16, original_component_decisions_checked=component_checks,
        observed_reference_triangle_checks=bound_checks, original_AB_outcomes_preserved=True,
        E_F_actual_device_passes=4, E_F_gain_certificates=4, E_F_complete_device_certificates=2,
        total_complete_certificates=9, core_equations_unchanged=True,
        old_tables_figures_references_preserved=True,
        pages={k:v['page_count'] for k,v in render.items()},
        new_training=0, new_model_evaluations=0, new_PDE_solves=0,
        spatial_execution_authorized=read(ROOT / 'configs/phk_v23/lf11_spatial_reference_sprint.json')['execution_authorized'])
    (HERE / 'verification.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
