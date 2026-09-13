"""Build evidence figures/tables only from an actually completed evaluation."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from .phk_v23_lf11 import ROOT
from .phk_v23_lf11_elimination import RUN


def report(root=RUN, include_pf=False):
    source = root/('evaluation-with-P_F' if include_pf else 'evaluation')
    result = json.loads((source/'results.json').read_text())
    records = result['records']
    names = ['E0', 'D_E', 'P_E', 'B_E']+(['P_F'] if include_pf else [])
    if not all(records[name]['valid'] for name in names):
        raise ValueError('invalid endpoint: report its failure explicitly before drawing matched performance figures')
    directory = ROOT/'paper/paper_v28'
    tables, figures = directory/'tables', directory/'figures'
    tables.mkdir(exist_ok=True); figures.mkdir(exist_ok=True)
    keys = ['S', 'Ephi', 'ET', 'EV', 'EI', 'bottom_current_NRMSE', 'power_trace_NRMSE', 'energy_error', 'local_joule_NRMSE']
    with (tables/'fixed-endpoints.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['role', *keys, 'strict_device_pass'])
        writer.writeheader()
        for name in names:
            writer.writerow({'role': name, **{k: records[name]['metrics'][k] for k in keys},
                             'strict_device_pass': records[name]['strict_device_pass']})
    lines = ['# Actual fixed-endpoint comparison', '', '| Role | '+' | '.join(keys)+' | Strict |',
             '|---|'+'---:|'*len(keys)+'---|']
    for name in names:
        lines.append('| '+name+' | '+' | '.join(f"{records[name]['metrics'][k]:.8g}" for k in keys)+' | '+str(records[name]['strict_device_pass'])+' |')
    lines += ['', 'All values are actual fixed nominal scores. Query-grid electrical solves count as inference, and the exposed nominal reference is not independent confirmation.']
    (tables/'fixed-endpoints.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    with (tables/'cycle-events.csv').open('w', newline='', encoding='utf-8') as f:
        cols = ['role', 'cycle', 'recall', 'precision', 'mass_ratio', 'timing_absolute', 'event_time']
        writer = csv.DictWriter(f, fieldnames=cols); writer.writeheader()
        for name in names:
            for i, cycle in enumerate(records[name]['cycles'], 1):
                writer.writerow({'role': name, 'cycle': i, **{k: cycle.get(k) for k in cols[2:]}})
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False,
                         'savefig.dpi': 180, 'font.family': 'DejaVu Sans'})
    colors = dict(E0='#727780', D_E='#3274a1', P_E='#db7b24', B_E='#38895b', P_F='#8355a7')
    from matplotlib.patches import FancyBboxPatch
    fig, axis = plt.subplots(figsize=(12, 4.5), constrained_layout=True)
    axis.set(xlim=(0, 12), ylim=(0, 4.4)); axis.axis('off')
    def box(x, y, w, h, text, color):
        axis.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.07',
                                     facecolor=color, edgecolor='#405060', linewidth=1))
        axis.text(x+w/2, y+h/2, text, ha='center', va='center', fontsize=10)
    def arrow(a, b, **kw):
        axis.annotate('', xy=b, xytext=a, arrowprops=dict(arrowstyle='->', color='#405060', lw=1.6, **kw))
    box(.15, 2.25, 2.4, 1.0, 'Shared T / phase fields\nNeural D_E / P_E\nFixed E0 / interpolated B_E', '#e4edf5')
    box(3.05, 2.25, 2.05, 1.0, 'Conductivity\n' + r'$\sigma(T,\phi)$', '#e6f1ec')
    box(5.6, 2.25, 2.75, 1.0, 'Common sparse electric solve\n' + r'$A(\sigma)v=f(U,\sigma)$', '#e6f1ec')
    box(8.95, 2.25, 2.75, 1.0, 'Own voltage and local heat\nHalf-resistance deposition\nCommon current / power', '#e6f1ec')
    box(.85, .3, 4.6, 1.0, 'D_E and P_E: identical observations + BC / IC\nP_E only: thermal cell + phase PDE residuals', '#fbecdb')
    box(6.9, .3, 4.6, 1.0, 'Compare phase, events and device errors\nP_E - D_E: PDE increment\nP_E versus B_E: strong comparator', '#f0edf6')
    for a, b in [((2.62, 2.75), (2.98, 2.75)), ((5.17, 2.75), (5.53, 2.75)),
                 ((8.42, 2.75), (8.88, 2.75)), ((10.1, 2.18), (9.6, 1.38)),
                 ((1.25, 2.18), (1.6, 1.38))]: arrow(a, b)
    arrow((6.5, 2.18), (4.45, 1.38), linestyle='--')
    axis.text(5.65, 1.6, 'Own V / q in the loss\n(no added labels)', ha='center', fontsize=9,
              bbox=dict(facecolor='white', edgecolor='none', pad=2))
    axis.text(6, 4.02, 'Same electrical layer, isolated thermal / phase physics increment',
              ha='center', fontsize=13, weight='bold')
    axis.text(6, 3.6, '80 x 40 training solve; 160 x 80 query solve for every main role', ha='center', fontsize=10)
    for suffix in ('png', 'pdf'): fig.savefig(figures/f'method-interface.{suffix}')
    plt.close(fig)
    with np.load(source/'traces.npz', allow_pickle=False) as loaded:
        tr = {k: loaded[k] for k in loaded.files}
    time = tr['time']
    current_scale = np.sqrt(np.trapezoid(tr['reference_current']**2, time)/(time[-1]-time[0]))
    power_scale = np.sqrt(np.trapezoid(tr['reference_power']**2, time)/(time[-1]-time[0]))
    fig, ax = plt.subplots(2, 3, figsize=(13, 7), constrained_layout=True)
    for axis, key, label in [(ax[0, 0], 'S', 'Phase-region symmetric difference'),
                             (ax[1, 1], 'local_joule_NRMSE', 'Local Joule-deposition NRMSE'),
                             (ax[1, 2], 'ET', 'ROI temperature error / 0.45')]:
        axis.bar(names, [records[n]['metrics'][key] for n in names], color=[colors[n] for n in names])
        axis.set_title(label); axis.set_ylim(bottom=0); axis.grid(axis='y', alpha=.2)
    for name in names:
        ax[0, 1].plot([1, 2], [c['recall'] for c in records[name]['cycles']], 'o-', color=colors[name], label=name)
        ax[0, 2].plot(time, (tr[name+'__bottom_current']-tr['reference_current'])/current_scale,
                       color=colors[name], label=name)
        ax[1, 0].plot(time, (tr[name+'__joule_power']-tr['reference_power'])/power_scale,
                       color=colors[name], label=name)
    ax[0, 1].set(title='Two-cycle event-support recall', xticks=[1, 2], ylim=(0, 1.04))
    ax[0, 1].axhline(.9, color='#555555', linestyle=':', lw=1)
    ax[0, 2].axhline(0, color='black', linestyle='--', lw=1)
    ax[1, 0].axhline(0, color='black', linestyle='--', lw=1)
    ax[0, 2].set(title='Bottom-current signed error', xlabel='Time', ylabel='Error / reference RMS')
    ax[1, 0].set(title='Joule-power signed error', xlabel='Time', ylabel='Error / reference RMS')
    ax[0, 2].legend(fontsize=7, ncol=2)
    fig.suptitle('Shared electrical layer: phase, event and device consequences')
    for suffix in ('png', 'pdf'): fig.savefig(figures/f'field-event-device.{suffix}')
    plt.close(fig)
    with np.load(source/'snapshots.npz', allow_pickle=False) as loaded:
        snap = {k: loaded[k] for k in loaded.files}
    nz, nx = len(snap['z']), len(snap['x'])
    rows = ['reference']+names
    fig, ax = plt.subplots(len(rows), 2, figsize=(9, 1.8*len(rows)), constrained_layout=True)
    for i, name in enumerate(rows):
        for j in range(2):
            artist = ax[i, j].imshow(snap[name+'__phase'][j].reshape(nz, nx), origin='lower', extent=(-1, 1, 0, 1),
                                     vmin=0, vmax=1, aspect='auto', cmap='viridis')
            ax[i, j].set_title(f"{name}: phase, t={snap['phase_times'][j]:.4f}", fontsize=9)
    fig.colorbar(artist, ax=ax, shrink=.5, label='Phase fraction')
    fig.suptitle('Fixed roles at reference cycle peaks (display times only)')
    for suffix in ('png', 'pdf'): fig.savefig(figures/f'phase-fields.{suffix}')
    plt.close(fig)
    fig, ax = plt.subplots(len(rows), 4, figsize=(13, 1.75*len(rows)), constrained_layout=True)
    qmax = max(snap[name+'__joule_density'].max() for name in rows)
    tmax = max(snap[name+'__heat_temperature'].max() for name in rows)
    for i, name in enumerate(rows):
        for j in range(4):
            key = 'joule_density' if j%2 == 0 else 'heat_temperature'
            vmax = qmax if j%2 == 0 else tmax
            artist = ax[i, j].imshow(snap[name+'__'+key][j//2].reshape(nz, nx), origin='lower', extent=(-1, 1, 0, 1),
                                     vmin=0, vmax=vmax, aspect='auto', cmap='magma')
            ax[i, j].set_title(f"{name}: {'q' if j%2 == 0 else 'T'}, t={snap['heat_times'][j//2]:.4f}", fontsize=8)
            if i == 0: fig.colorbar(artist, ax=ax[:, j], shrink=.4)
    fig.suptitle('Local half-resistance Joule deposition and temperature; shared scales')
    for suffix in ('png', 'pdf'): fig.savefig(figures/f'joule-temperature.{suffix}')
    plt.close(fig)
    decision = result['conditional_decision']
    c, d = records['P_E']['metrics'], records['D_E']['metrics']
    pairs = decision['comparisons']
    text = ['# Matched remaining-PDE contrast', '',
            'VERIFIED: E0/D_E/P_E/B_E were evaluated on the fixed nominal grid. ',
            f"P_E versus D_E passes reconstruction A: **{pairs['D_E']['A']['passed']}**; function B: **{pairs['D_E']['B']['passed']}**. ",
            f"Against B_E the same full gates are A: **{pairs['B_E']['A']['passed']}** and B: **{pairs['B_E']['B']['passed']}**. ",
            f"The separately frozen same-layer prerequisite for P_F is **{decision['run_P_F']}**.", '',
            '| Metric | P_E | D_E | Relative P_E change |', '|---|---:|---:|---:|']
    for key in keys:
        tolerance = 1e-8 if key == 'S' else 1e-6
        text.append(f"| {key} | {c[key]:.8g} | {d[key]:.8g} | {(c[key]-d[key])/max(d[key],tolerance):+.3%} |")
    text += ['', '[Complete fixed-endpoint table](fixed-endpoints.md) and [cycle records](cycle-events.csv) retain every role. ',
             'Figures show the phase–event–device comparison, phase fields and local Joule/temperature maps. ',
             'Conservation identities are consequences of the solve and are not counted as independent method increments. ',
             'A failed matched gate does not erase submetric effects, and those effects do not replace the frozen gate.', '']
    if include_pf:
        text += ['P_F has been executed under the conditional budget. Its additional matched comparisons are saved in the evaluation results; its voltage remains the uncorrected network output.', '']
    elif not decision['run_P_F']:
        text += ['P_F was not triggered and was not run; it is not a failed endpoint.', '']
    (tables/'matched-pde-contrast.md').write_text('\n'.join(line.rstrip() for line in text).rstrip()+'\n', encoding='utf-8')
    print(json.dumps({'actual_figures_and_tables_written': True, 'paper': str(directory)}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=RUN); p.add_argument('--include-pf', action='store_true')
    args = p.parse_args(); report(args.root, args.include_pf)
