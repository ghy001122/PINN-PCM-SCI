"""Turn completed fixed-array spatial scores into full tables and figures."""
from pathlib import Path
import csv
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUN = ROOT / 'outputs/runs/20260917-lf11-spatial-reference'
ARCHIVE = ROOT / 'outputs/submission-archive-20260916'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save_table(name, rows, display=None):
    path=HERE/'tables'/name
    with path.with_suffix('.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    if display is not None:
        headings,values=display
        lines=['| '+' | '.join(headings)+' |','| '+' | '.join(['---']*len(headings))+' |']
        lines += ['| '+' | '.join(str(v) for v in row)+' |' for row in values]
        path.with_suffix('.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main():
    data=read(RUN/'scoring/results.json')
    if data['status']!='COMPLETE_FIXED_ARRAY_SPATIAL_REFERENCE_CHECK':
        raise ValueError('Only complete saved spatial results can enter the paper')
    prior=read(ARCHIVE/'rescore-output/results.json')
    records={**prior['records'],'spatial':data['records']}
    decisions={**prior['decisions'],'spatial':data['decisions']}
    metrics=['S','Ephi','ET','EV','EI','bottom_current_NRMSE','power_trace_NRMSE','energy_error','local_joule_NRMSE']
    rows=[];events=[]
    for ref,objects in records.items():
        for name,obj in objects.items():
            parts=name.split('/');seed=parts[1] if len(parts)==3 else '-'
            row=dict(reference=ref,protocol=parts[0],seed=seed,role=parts[-1],
                     valid=obj['valid'],strict=obj['strict_device_pass'])
            row.update({k:obj['metrics'][k] for k in metrics})
            row.update({f'normalizer_{k}':v for k,v in obj['normalizers'].items()})
            row.update({f'fixed_old_denominator_{k}':v for k,v in obj['fixed_old_denominator'].items()})
            rows.append(row)
            for c in obj['cycles']:
                events.append(dict(reference=ref,protocol=parts[0],seed=seed,role=parts[-1],
                    cycle=c['cycle'],event_time=c['event_time'],reference_event_time=c['reference_event_time'],
                    timing=c['timing_absolute'],recall=c['recall'],precision=c['precision'],
                    mass_ratio=c['mass_ratio'],recovery=c['recovery_fraction'],
                    peak_roi=c['peak_roi_fraction'],peak_full=c['peak_full_domain_fraction'],
                    peak_outside=c['peak_outside_roi_fraction'],reference_mass=c['teacher_active_target_mass'],
                    predicted_mass=c['predicted_active_target_mass'],overlap_mass=c['true_positive_target_mass']))
    save_table('spatial-all-fixed-metrics',rows)
    save_table('spatial-all-fixed-events',events)
    short=lambda x:'O' if x=='original' else 'S'
    shown=[r for r in rows if r['reference']=='spatial']
    save_table('spatial-fixed-endpoints',shown,(
        ['Case','Seed','Method','Phase RMS','T (%)','Current (%)','Power (%)','Energy (%)','Strict'],
        [[short(r['protocol']),r['seed'],r['role'],f"{r['Ephi']:.7f}",f"{100*r['ET']:.4f}",
          f"{100*r['EI']:.4f}",f"{100*r['power_trace_NRMSE']:.4f}",f"{100*r['energy_error']:.4f}",
          'yes' if r['strict'] else 'no'] for r in shown]))

    comparisons=[]
    for protocol in ('original','shorter'):
        for seed in ('29','43'):
            for baseline,key in [('F','E_vs_soft'),('B_E','E_vs_B_E')]:
                row=dict(protocol=protocol,seed=seed,control=baseline)
                for ref in records:
                    obj=decisions[ref][protocol][seed][key]
                    row.update({f'{ref}_{layer}':obj[layer]['passed'] for layer in ('A','B')})
                c=records['spatial'][f'{protocol}/{seed}/E']['metrics']
                b=records['spatial'][f'{protocol}/{seed}/F' if baseline=='F' else f'{protocol}/B_E']['metrics']
                for metric in metrics:
                    row[f'{metric}_absolute_error_reduction']=b[metric]-c[metric]
                    row[f'{metric}_relative_error_reduction']=1-c[metric]/b[metric]
                comparisons.append(row)
    labels=['Case','Seed','Control','Old A/B','Time A/B','Space A/B','Current gain (%)','Power gain (%)']
    verdict=lambda r,ref: '/'.join('yes' if r[f'{ref}_{k}'] else 'no' for k in ('A','B'))
    save_table('spatial-historical-comparisons',comparisons,(labels,
        [[short(r['protocol']),r['seed'],r['control'],verdict(r,'old'),verdict(r,'refined'),verdict(r,'spatial'),
          f"{100*r['bottom_current_NRMSE_relative_error_reduction']:.2f}",
          f"{100*r['power_trace_NRMSE_relative_error_reduction']:.2f}"] for r in comparisons]))

    delta_rows=[dict(protocol=k,**v) for k,v in data['reference_delta_from_time_refined'].items()]
    save_table('spatial-reference-deltas',delta_rows,(
        ['Case','delta S','delta phase','delta T / 0.45','delta V','delta current','delta power','delta q'],
        [[short(r['protocol'])]+[f"{r[k]:.6g}" for k in ('S','Ephi','ET','EV','current_rms','power_rms','q_rms')]
         for r in delta_rows]))
    mapping=[];mapping_events=[]
    for name,v in data['mapping_diagnostics'].items():
        parts=name.split('/')
        row=dict(protocol=parts[0],seed=parts[1] if len(parts)==3 else '-',role=parts[-1])
        mapping.append({**row,**{k:v[k] for k in ('S_primary','S_indicator_restriction','S_absolute_difference','S_difference_bound')}})
        for c in v['cycles']:mapping_events.append({**row,**c})
    save_table('spatial-threshold-mapping',mapping,(
        ['Case','Seed','Method','S primary','S indicator','Absolute gap','Bound'],
        [[short(r['protocol']),r['seed'],r['role']]+[f"{r[k]:.7g}" for k in ('S_primary','S_indicator_restriction','S_absolute_difference','S_difference_bound')]
         for r in mapping]))
    save_table('spatial-threshold-events',mapping_events)

    execution=[]
    for protocol in ('original','shorter'):
        t=read(RUN/f'reference/{protocol}/terminal.json')
        counts=t['linear_counts']
        execution.append(dict(protocol=protocol,steps=t['solver_statistics']['time_steps_total'],
            **counts,total=sum(counts.values()),cap=200000,status=t['status'],
            phase_min=t['numerical_checks']['phase_range'][0],phase_max=t['numerical_checks']['phase_range'][1],
            thermal_residual=t['numerical_checks']['max_thermal_residual'],
            phase_residual=t['numerical_checks']['max_phase_residual'],
            current_balance=t['numerical_checks']['max_current_balance']))
    save_table('spatial-execution',execution,(
        ['Case','Main steps','Electric','Thermal','Phase','Total','Cap'],
        [[short(r['protocol'])]+[r[k] for k in ('steps','electric','thermal','phase','total','cap')] for r in execution]))
    conditional=[]
    for ref in records:
        for seed in ('29','43'):
            d=decisions[ref]['shorter'][seed]
            for role in ('E_R','E_I'):
                v=d[role]
                conditional.append(dict(reference=ref,seed=seed,role=role,A=v['matched_A'],B=v['matched_B'],
                    strict_increment=v['strict_increment'],strict_capability=records[ref][f'shorter/{seed}/{role}']['strict_device_pass']))
    save_table('spatial-continuation-decisions',conditional,(
        ['Reference','Seed','Role','Matched A','Matched B','Strict increment','Strict capability'],
        [[r['reference'],r['seed'],r['role']]+['yes' if r[k] else 'no' for k in ('A','B','strict_increment','strict_capability')] for r in conditional]))
    strict_example=[]
    for ref in records:
        obj=records[ref]['shorter/43/E_I']
        c1,c2=obj['cycles']
        strict_example.append(dict(reference=ref,cycle1_recall=c1['recall'],cycle1_timing=c1['timing_absolute'],
            cycle2_recall=c2['recall'],cycle2_timing=c2['timing_absolute'],strict=obj['strict_device_pass']))
    save_table('spatial-strict-counterexample',strict_example,(
        ['Reference','Recall 1','Timing 1','Recall 2','Timing 2','Strict'],
        [[r['reference']]+[f'{r[k]:.9f}' for k in ('cycle1_recall','cycle1_timing','cycle2_recall','cycle2_timing')]
         +['yes' if r['strict'] else 'no'] for r in strict_example]))

    pairs=[(p,s) for p in ('original','shorter') for s in ('29','43')]
    fig,axes=plt.subplots(2,2,figsize=(7.2,6.2),layout='constrained')
    components=[('bottom_current_NRMSE',100,'Bottom-current gain margin\n(percentage points)'),
                ('power_trace_NRMSE',100,'Power gain margin\n(percentage points)'),
                ('S',1e6,'S gain margin (× 10⁻⁶)'),('Ephi',1e3,'Phase RMS gain margin (× 10⁻³)')]
    x=np.arange(4)
    for ax,(metric,scale,label) in zip(axes.flat,components,strict=True):
        for j,(ref,color) in enumerate([('old','#86939e'),('refined','#316e85'),('spatial','#c07832')]):
            margins=[scale*(.9*records[ref][f'{p}/{s}/F']['metrics'][metric]-records[ref][f'{p}/{s}/E']['metrics'][metric]) for p,s in pairs]
            ax.bar(x+(j-1)*.25,margins,.24,label={'old':'Original reference','refined':'Time refined','spatial':'Space refined + restricted'}[ref],color=color)
        ax.axhline(0,color='#333333',lw=.8)
        ax.set_xticks(x,[f'{short(p)} / {s}' for p,s in pairs],fontsize=9);ax.set_ylabel(label,fontsize=10)
        ax.grid(axis='y',alpha=.16)
    axes[0,0].legend(fontsize=9)
    fig.savefig(HERE/'figures/fig12-spatial-reference-margins.png',dpi=220)
    fig.savefig(HERE/'figures/fig12-spatial-reference-margins.pdf');plt.close(fig)

    fig,axes=plt.subplots(2,2,figsize=(7.2,5.4),layout='constrained')
    for j,p in enumerate(('original','shorter')):
        with np.load(ARCHIVE/f'rescore-output/refined/{p}_29_E-traces.npz',allow_pickle=False) as before, \
             np.load(RUN/f'scoring/spatial/{p}_29_E-traces.npz',allow_pickle=False) as after:
            np.testing.assert_array_equal(before['time'],after['time'])
            for k,quantity in enumerate(('current','power')):
                ax=axes[j,k]
                ax.plot(after['time'],after[f'reference_{quantity}']-before[f'reference_{quantity}'],color='#316e85',lw=1.15)
                ax.axhline(0,color='#333333',lw=.6);ax.set_title(('Original' if p=='original' else 'Earlier pulse')+': native '+quantity)
                ax.set_ylabel('240×120 minus 160×80');ax.set_xlabel('Dimensionless time');ax.grid(alpha=.16)
    fig.savefig(HERE/'figures/fig13-spatial-native-traces.png',dpi=220)
    fig.savefig(HERE/'figures/fig13-spatial-native-traces.pdf');plt.close(fig)

    fig,axes=plt.subplots(2,1,figsize=(7.2,6.2),layout='constrained')
    xx=np.arange(len(mapping));names=[f"{short(r['protocol'])}/{r['seed']}/{r['role']}" for r in mapping]
    axes[0].plot(xx,[1e6*r['S_absolute_difference'] for r in mapping],'o',label='Observed |S change|',color='#316e85')
    axes[0].plot(xx,[1e6*r['S_difference_bound'] for r in mapping],'_',markersize=10,label='Mapping bound',color='#c07832')
    axes[0].set_ylabel('Threshold-map discrepancy (× 10⁻⁶)');axes[0].legend(fontsize=9)
    for cycle,color in [(1,'#316e85'),(2,'#c07832')]:
        vals=[100*(r['recall_indicator_restriction']-r['recall_primary']) for r in mapping_events if r['cycle']==cycle]
        axes[1].plot(xx,vals,'o',label=f'Cycle {cycle}',color=color)
    axes[1].axhline(0,color='#333333',lw=.7);axes[1].set_ylabel('Recall change (percentage points)');axes[1].legend(fontsize=9)
    axes[0].set_xticks(xx)
    axes[0].tick_params(axis='x',labelbottom=False)
    axes[1].set_xticks(xx,names,rotation=55,ha='right',fontsize=9)
    for ax in axes:ax.grid(axis='y',alpha=.16)
    fig.savefig(HERE/'figures/fig14-spatial-threshold-mapping.png',dpi=220)
    fig.savefig(HERE/'figures/fig14-spatial-threshold-mapping.pdf');plt.close(fig)

    changes=[];direction_changes=[]
    for row in comparisons:
        for layer in ('A','B'):
            if row[f'spatial_{layer}']!=row[f'refined_{layer}']:
                changes.append(dict(protocol=row['protocol'],seed=row['seed'],control=row['control'],layer=layer,
                    previous=row[f'refined_{layer}'],spatial=row[f'spatial_{layer}']))
        name=f"{row['protocol']}/{row['seed']}/E"
        control=f"{row['protocol']}/{row['seed']}/F" if row['control']=='F' else f"{row['protocol']}/B_E"
        for metric in ('S','Ephi','ET','EV','bottom_current_NRMSE','power_trace_NRMSE'):
            before=records['refined'][control]['metrics'][metric]-records['refined'][name]['metrics'][metric]
            after=records['spatial'][control]['metrics'][metric]-records['spatial'][name]['metrics'][metric]
            if np.sign(before)!=np.sign(after):
                direction_changes.append(dict(protocol=row['protocol'],seed=row['seed'],control=row['control'],
                    metric=metric,previous_error_reduction=before,spatial_error_reduction=after))
    summary=dict(status='COMPLETE',historical_rule_changes_from_time_refined=changes,
        metric_direction_changes_from_time_refined=direction_changes,
        historical_E_F_B_passes={ref:sum(decisions[ref][p][s]['E_vs_soft']['B']['passed'] for p,s in pairs) for ref in records},
        strict_objects={ref:[name for name,o in group.items() if o['strict_device_pass']] for ref,group in records.items()},
        comparisons=comparisons,reference_discrepancies=delta_rows,execution=execution,
        mapping_summary=dict(max_S_gap=max(r['S_absolute_difference'] for r in mapping),
            max_S_bound=max(r['S_difference_bound'] for r in mapping),
            max_abs_recall_change=max(abs(r['recall_indicator_restriction']-r['recall_primary']) for r in mapping_events)),
        new_training=0,new_model_evaluations=0,new_prediction_electric_solves=0,
        continuum_convergence_established=False,native_fine_grid_strict_capability_established=False)
    (HERE/'spatial-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('comparisons','reference_discrepancies')},indent=2))


if __name__=='__main__':main()
