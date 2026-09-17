"""Validate completed spatial-reference evidence and its manuscript integration.

Consumes saved scalars, tables and rendered text. It does not run a model,
generate a reference or repeat a scientific experiment.
"""
from pathlib import Path
import csv
import importlib.util
import json
import re

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUN = ROOT / 'outputs/runs/20260917-lf11-spatial-reference'
ARCHIVE = ROOT / 'outputs/submission-archive-20260916'
BASE = ROOT / 'paper/review_20260917/pre-spatial-revision'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def csv_rows(name):
    with (HERE/'tables'/name).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def main():
    spec = importlib.util.spec_from_file_location('spatial_saved_rules', ARCHIVE/'portable/rescore.py')
    scoring = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scoring)
    data = read(RUN/'scoring/results.json')
    prior = read(ARCHIVE/'rescore-output/results.json')
    summary = read(HERE/'spatial-summary.json')
    manifest = read(ARCHIVE/'manifest.json')
    assert data['status'] == 'COMPLETE_FIXED_ARRAY_SPATIAL_REFERENCE_CHECK'
    assert summary['status'] == 'COMPLETE'
    assert data['new_training'] == data['new_checkpoint_evaluations'] == data['new_prediction_electric_solves'] == 0
    assert data['model_predictions_unchanged']
    names = {obj['id'] for obj in manifest['objects']}
    assert len(names) == 16
    assert names == set(data['records']) == set(data['mapping_diagnostics'])
    assert all(v <= 1e-10 for v in data['causal_prefix_max_error'].values())
    counts = {}
    for protocol in ('original', 'shorter'):
        folder = RUN/'reference'/protocol
        intent = read(folder/'intent.json')
        terminal = read(folder/'terminal.json')
        assert intent['config']['execution_authorized'] is True
        assert terminal['status'] == 'VALID_FIXED_SPATIAL_REFERENCE'
        assert terminal['new_training'] == 0 and not terminal['stress_read']
        r = terminal['case_spec']['reference']
        assert (r['nx'], r['nz'], r['dt'], r['time_end'], r['save_every']) == (240, 120, .0003125, 2.5, 8)
        assert terminal['solver_statistics']['time_steps_total'] == 8000
        counts[protocol] = dict(terminal['linear_counts'])
        assert 0 < sum(counts[protocol].values()) <= 200000
        for kind, value in counts[protocol].items():
            assert value == terminal['solver_statistics'][kind+'_linear_solves_total']
        assert 0 <= terminal['numerical_checks']['phase_range'][0] <= terminal['numerical_checks']['phase_range'][1] <= 1
        mapping = read(folder/'mapping.json')
        assert not mapping['model_arrays_changed'] and mapping['new_electrical_solves'] == 0
        assert all(v < 1e-10 for v in mapping['max_integral_discrepancy'].values())
        assert mapping['native_q_power_max_error'] < 1e-9
        cfg = read(ARCHIVE/manifest['protocols'][protocol]['config'])
        reproduced = scoring.decisions(data['records'], cfg, protocol)
        scoring.compare_saved(reproduced, data['decisions'][protocol])

    invariant_checks = 0
    for name, record in data['records'].items():
        old = prior['records']['old'][name]
        diag = data['mapping_diagnostics'][name]
        assert record['valid'] == old['valid']
        np.testing.assert_allclose(diag['S_primary'], record['metrics']['S'], rtol=0, atol=2e-14)
        assert diag['S_absolute_difference'] <= diag['S_difference_bound'] + 2e-14
        for new_cycle, old_cycle in zip(record['cycles'], old['cycles'], strict=True):
            for key in ('event_time', 'recovery_fraction', 'peak_roi_fraction',
                        'peak_full_domain_fraction', 'peak_outside_roi_fraction',
                        'predicted_active_target_mass'):
                a, b = new_cycle[key], old_cycle[key]
                if a is None or b is None:
                    assert a is b, (name, key, a, b)
                else:
                    np.testing.assert_allclose(a, b, rtol=1e-12, atol=2e-14, err_msg=name+'/'+key)
                invariant_checks += 1
        assert all(np.isfinite(v) and v > 0 for v in record['normalizers'].values())
        assert record['strict_device_pass'] == (name in summary['strict_objects']['spatial'])

    metrics = csv_rows('spatial-all-fixed-metrics.csv')
    events = csv_rows('spatial-all-fixed-events.csv')
    assert len(metrics) == 48 and len(events) == 96
    assert len(csv_rows('spatial-historical-comparisons.csv')) == 8
    assert len(csv_rows('spatial-continuation-decisions.csv')) == 12
    assert len(csv_rows('spatial-threshold-events.csv')) == 32
    strict_rows = csv_rows('spatial-strict-counterexample.csv')
    assert len(strict_rows) == 3
    for row in strict_rows:
        records = data['records'] if row['reference'] == 'spatial' else prior['records'][row['reference']]
        obj = records['shorter/43/E_I']
        for i, cycle in enumerate(obj['cycles'], 1):
            for key, source in [('recall', 'recall'), ('timing', 'timing_absolute')]:
                np.testing.assert_allclose(float(row[f'cycle{i}_{key}']), cycle[source], rtol=0, atol=0)
        assert row['strict'] == str(obj['strict_device_pass'])
    for row in metrics:
        name = row['protocol']+'/' + (row['seed']+'/' if row['seed'] != '-' else '') + row['role']
        record = (data['records'] if row['reference'] == 'spatial' else prior['records'][row['reference']])[name]
        for key in ('S', 'Ephi', 'ET', 'EV', 'EI', 'bottom_current_NRMSE',
                    'power_trace_NRMSE', 'energy_error', 'local_joule_NRMSE'):
            np.testing.assert_allclose(float(row[key]), record['metrics'][key], rtol=0, atol=0)
        assert row['strict'] == str(record['strict_device_pass'])

    docs = {}
    equations = lambda text: re.findall(r'\$\$(.*?)\$\$', text, flags=re.S)
    for name in ('manuscript', 'supplement'):
        docs[name] = (HERE/f'source/{name}.md').read_text(encoding='utf-8')
        previous = (BASE/f'source/{name}.md').read_text(encoding='utf-8')
        assert equations(docs[name])[:len(equations(previous))] == equations(previous)
        expanded = (HERE/f'{name}.md').read_text(encoding='utf-8')
        assert '{{TABLE:' not in expanded and '{{REFERENCES}}' not in expanded
        for image in re.findall(r'!\[[^\]]*\]\(([^)]+)\)', docs[name]):
            assert (HERE/image).is_file(), image
        for table in re.findall(r'\{\{TABLE:([^}]+)\}\}', docs[name]):
            assert (HERE/'tables'/f'{table}.md').is_file(), table
    assert len(equations(docs['manuscript'])) == 23
    assert len(equations(docs['supplement'])) == 15
    assert '### 5.8 Spatial-reference' in docs['manuscript']
    assert '## S15. Fixed-prediction spatial-reference experiment' in docs['supplement']
    n = summary['historical_E_F_B_passes']['spatial']
    assert f'in {n}/4 historical pairs' in docs['manuscript']
    assert f'{len(summary["historical_rule_changes_from_time_refined"])} of the sixteen historical decisions' in docs['manuscript']
    assert '[author names and affiliations to be supplied]' in docs['manuscript']
    for filename in ('references.md', 'references.bib'):
        assert (HERE/filename).read_bytes() == (HERE.parent/'paper_revision_20260916'/filename).read_bytes()
    render = read(HERE/'build/visual-review/render-summary.json')
    for doc in render.values():
        for page in doc['pages']:
            assert not page['outside_page'] and not page['body_into_footer']
            assert not page['replacement_character'] and page['characters'] > 0
    result = dict(status='PASS', scope='Saved spatial scores, original rules, prediction invariants, manuscript and rendered text',
        reference_trajectories=2, main_steps=16000, linear_solves=counts,
        full_objects=16, three_reference_metric_rows=48, event_rows=96,
        reference_independent_event_scalars_checked=invariant_checks,
        primary_threshold_scores_verified=True, complete_rules_reproduced=True,
        complete_E_F_device_passes=n, historical_rule_changes=summary['historical_rule_changes_from_time_refined'],
        strict_objects=summary['strict_objects']['spatial'],
        pre_spatial_equations_preserved=True,
        pages={k:v['page_count'] for k,v in render.items()},
        new_training=0, new_model_evaluations=0, new_prediction_electric_solves=0)
    (HERE/'spatial-verification.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
