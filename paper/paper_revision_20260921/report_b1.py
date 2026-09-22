"""Export complete B1 results and work counters after frozen array scoring."""
from pathlib import Path
import csv
import json
import shutil
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
RUN=ROOT/'outputs/runs/20260921-b1-second-cycle-phase-gap'
SCORE=ROOT/'outputs/submission-rescore-20260921/b1/first-score/results.json'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2),encoding='utf-8')

def flat(value,prefix=''):
    result={}
    for key,item in value.items():
        name=prefix+str(key)
        if isinstance(item,dict):result.update(flat(item,name+'.'))
        else:result[name]=json.dumps(item) if isinstance(item,list) else item
    return result

def csv_write(name,rows):
    columns=list(dict.fromkeys(k for row in rows for k in row))
    path=HERE/'tables'/name
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns)
        writer.writeheader();writer.writerows(rows)

def md_write(name,headers,rows):
    def show(value):
        if isinstance(value,float):return f'{value:.7g}'
        return str(value)
    text='| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'
    text+=''.join('| '+' | '.join(show(v) for v in row)+' |\n' for row in rows)
    (HERE/'tables'/name).write_text(text,encoding='utf-8')

def export_port_energy(result):
    """Tabulate existing first-score traces; no model query or re-adjudication."""
    package=SCORE.parents[1]
    config=read(package/'reference-inputs/definitions/shorter.json')
    pulse_windows=config['windows'][::2]
    assert pulse_windows==[[0.0,0.35],[1.01,1.36]]
    pulse_rows=[];totals=[];index=[];display=[]
    for reference,levels in result['records'].items():
        for reader,objects in levels.items():
            for oid,record in objects.items():
                path=SCORE.parent/'traces'/reference/reader/(oid.replace('/','_')+'.npz')
                with np.load(path,allow_pickle=False) as trace:
                    t=trace['time'];error=trace['signed_power_error'];ref=trace['reference_power']
                    predicted=trace['joule_power']
                    assert len(t)==1001
                    np.testing.assert_allclose(predicted-ref,error,rtol=2e-10,atol=2e-12)
                    base=dict(reference=reference,reader=reader,object=oid)
                    signed=[]
                    for cycle,(lo,hi) in enumerate(pulse_windows,1):
                        ends=[np.flatnonzero(np.isclose(t,v,rtol=0,atol=1e-12)) for v in (lo,hi)]
                        assert all(len(v)==1 for v in ends)
                        sel=slice(int(ends[0][0]),int(ends[1][0])+1)
                        delta=float(np.trapezoid(error[sel],t[sel]));signed.append(delta)
                        pulse_rows.append(dict(**base,cycle=cycle,start=lo,end=hi,
                            reference_energy=float(np.trapezoid(ref[sel],t[sel])),
                            predicted_energy=float(np.trapezoid(predicted[sel],t[sel])),
                            signed_energy_error=delta))
                    total=float(np.trapezoid(error,t));reference_energy=float(np.trapezoid(ref,t))
                    relative=abs(total)/max(abs(reference_energy),1e-12)
                    np.testing.assert_allclose([sum(signed),trace['cumulative_signed_energy_error'][-1]],
                                               [total,total],rtol=2e-10,atol=2e-12)
                    np.testing.assert_allclose(relative,record['metrics']['energy_error'],rtol=2e-10,atol=2e-12)
                    totals.append(dict(**base,pulse_1_signed_error=signed[0],pulse_2_signed_error=signed[1],
                        full_signed_energy_error=total,full_reference_energy=reference_energy,
                        full_energy_error=relative,sum_absolute_pulse_errors=sum(abs(x) for x in signed)))
                    index.append(dict(**base,package_relative_trace=path.relative_to(package).as_posix(),
                        time_count=len(t),start=float(t[0]),end=float(t[-1]),
                        fields=';'.join(trace.files),native_ports_preserved=True))
                    if reference=='spatial' and reader=='fine':
                        parts=oid.split('/');seed=parts[1] if len(parts)==3 else '-'
                        display.append([seed,parts[-1],*signed,total,100*relative])
    assert len(pulse_rows)==84 and len(totals)==42 and len(index)==42 and len(display)==7
    csv_write('b1-signed-pulse-energy.csv',pulse_rows)
    csv_write('b1-energy-summary.csv',totals)
    csv_write('b1-port-trace-index.csv',index)
    md_write('b1-energy-spatial-fine.md',
        ['Seed','Role','Signed pulse 1','Signed pulse 2','Signed total','Energy (%)'],display)
    print(json.dumps(dict(saved_trace_exports=len(index),signed_pulse_rows=len(pulse_rows),
                          new_model_queries=0,new_electrical_solves=0,scientific_decisions_changed=False)))


def main():
    closure=read(RUN/'compute-closure.json')
    assert closure['instance_shutdown_confirmed'] and closure['recovery_verified']
    result=read(SCORE)
    assert result['status']=='COMPLETE_B1_ARRAY_SCORING' and result['record_count']==42
    (HERE/'tables').mkdir(exist_ok=True)
    export_port_energy(result)
    rows=[];windows=[];comparisons=[];primary=[];events=[]
    for ref,levels in result['records'].items():
        for reader,objects in levels.items():
            for oid,record in objects.items():
                base=dict(reference=ref,reader=reader,object=oid)
                rows.append({**base,**flat(record)})
                for cycle,item in enumerate(record['cycles'],start=1):
                    events.append({**base,'cycle_number':cycle,**flat(item),
                                   'whole_trajectory_strict':record['strict_device_pass']})
                for interval,item in result['windows'][ref][reader][oid].items():
                    windows.append({**base,'interval':interval,**flat(item)})
            for seed,pairs in result['comparisons'][ref][reader].items():
                for comparison,item in pairs.items():
                    base=dict(reference=ref,reader=reader,seed=seed,comparison=comparison)
                    comparisons.append({**base,**flat(item)})
                    if comparison=='E_vs_D_E':
                        primary.append(dict(reference=ref,reader=reader,seed=int(seed),
                            A_w=item['A_w']['passed'],full_A=item['full']['A']['passed'],
                            full_B=item['full']['B']['passed'],
                            outside_cost=any(item['outside_cost_flags'].values()),
                            outside_cost_fields=[k for k,v in item['outside_cost_flags'].items() if v],
                            effects=item['window_effects']))
    assert len(rows)==42 and len(windows)==126 and len(comparisons)==36 and len(primary)==12
    csv_write('b1-all-records.csv',rows)
    csv_write('b1-all-window-outside-full.csv',windows)
    csv_write('b1-all-comparisons.csv',comparisons)
    assert len(events)==84
    csv_write('b1-all-events.csv',events)
    support_rows=[];extent_rows=[]
    for oid,record in result['records']['spatial']['coarse'].items():
        parts=oid.split('/');seed=parts[1] if len(parts)==3 else '-';role=parts[-1]
        for cycle in record['cycles']:
            support_rows.append([seed,role,cycle['cycle'],
                cycle['event_time'] if cycle['event_time'] is not None else 'missing',
                cycle['timing_absolute'],cycle['recall'],cycle['precision'],cycle['mass_ratio']])
            extent_rows.append([seed,role,cycle['cycle'],cycle['peak_roi_fraction'],
                cycle['peak_full_domain_fraction'],cycle['peak_outside_roi_fraction'],
                cycle['recovery_fraction'],record['metrics']['phase_max'],record['strict_device_pass']])
    md_write('b1-event-support-spatial.md',
        ['Seed','Role','Cycle','Onset','Onset error','Recall','Precision','Mass ratio'],support_rows)
    md_write('b1-event-extent-spatial.md',
        ['Seed','Role','Cycle','ROI peak','Global peak','Outside peak','Recovery','Max phase','Strict'],extent_rows)
    md_write('b1-primary-decisions.md',['Reference','Reader','Seed','A_w','Full A','Full B','Outside cost'],
        [[x[k] for k in ('reference','reader','seed','A_w','full_A','full_B','outside_cost')] for x in primary])
    for scope in ('window','outside','full'):
        display=[]
        for ref in result['windows']:
            for oid,item in result['windows'][ref]['fine'].items():
                parts=oid.split('/');seed=parts[1] if len(parts)==3 else 'shared';role=parts[-1]
                m=item[scope]['metrics']
                display.append([ref,seed,role,m['S']*1000,m['Ephi'],m['ET']*100,
                                m['EV']*1000,m['bottom_current_NRMSE']*100,m['power_trace_NRMSE']*100])
        md_write('b1-'+scope+'-fine.md',['Reference','Seed','Role','1000 S','Phase RMS','T (%)','1000 V RMS','I (%)','P (%)'],display)
    locked=read(RUN/'all-endpoints-locked.json')
    work=[]
    for seed in (29,43):
        parent=read(RUN/f'seed-{seed}/common-fit/fit-summary.json')
        calibration=read(RUN/f'seed-{seed}/parent-and-calibration-work.json')
        work.append({**flat(parent),'seed':seed,'stage':'parent',
                     'elapsed_parent_and_calibration':calibration['elapsed_seconds']})
        work.append(dict(seed=seed,stage='calibration',**flat(calibration['calibration'])))
        for role in ('E','D_E','F_raw'):
            terminal=read(RUN/f'seed-{seed}/{role}/terminal.json')
            elapsed=read(RUN/f'seed-{seed}/{role}/execution-work.json')
            work.append(dict(seed=seed,stage=role,**flat(terminal),**flat(elapsed,'execution.')))
    readers=read(RUN/'readout-manifest.json')
    readout_work=[]
    for item in readers['objects']:
        for key,label in (('prediction','coarse'),('fine_prediction','fine')):
            detail=read((ROOT/item[key]).parent/'prediction.json')
            readout_work.append(dict(object=item['id'],reader=label,**flat(detail)))
    csv_write('b1-training-and-calibration-work.csv',work)
    csv_write('b1-readout-work.csv',readout_work)
    counts=locked['counts']
    assert counts['adam']==13800 and counts['complete_evaluations']<=3000
    assert readers['projected_forward_solves']==3892
    ranges={}
    for metric in primary[0]['effects']:
        values=[x['effects'][metric]['relative_error_reduction'] for x in primary]
        values=[v for v in values if v is not None]
        ranges[metric]=dict(min=min(values),max=max(values))
    summary=dict(status='COMPLETE_B1_SCORED_AND_RECOVERED',scientific_route=result['scientific_route'],
        primary_comparisons=primary,A_w_passed=sum(x['A_w'] for x in primary),A_w_total=12,
        reference_reader_repetitions_are_not_independent=True,independent_initializations=2,
        window_relative_effect_ranges=ranges,counts=counts,
        readout_forward_solves=readers['projected_forward_solves'],new_reference_steps=0,
        instance_shutdown_confirmed=True,reference_scoring_after_shutdown=True,
        cost_policy='USER_NO_COST_LIMIT',cost_not_estimated=True,
        score_source=SCORE.relative_to(ROOT).as_posix())
    summary['strict_by_reference']={ref:{oid:value['strict_device_pass'] for oid,value in levels['coarse'].items()}
                                    for ref,levels in result['records'].items()}
    summary['strict_across_all_references_and_readers']=[oid for oid in result['records']['old']['coarse']
        if all(levels[reader][oid]['strict_device_pass'] for levels in result['records'].values() for reader in ('coarse','fine'))]
    save(HERE/'evidence/b1-summary.json',summary)
    save(HERE/'evidence/b1-compute-closure.json',closure)
    save(HERE/'evidence/b1-complete-results.json',result)
    (RUN/'scoring').mkdir(exist_ok=True)
    shutil.copy2(SCORE,RUN/'scoring/results.json')
    save(RUN/'scoring/provenance.json',dict(mode='copied complete first portable score; not a second execution',source=str(SCORE)))
    package=SCORE.parents[1]
    shutil.copy2(SCORE,package/'expected-results.json')
    status=read(package/'package-status.json')
    status.update(status='COMPLETE_FIRST_PORTABLE_SCORE',actual_records=42,score_path='first-score/results.json')
    save(package/'package-status.json',status)
    print(json.dumps(dict(route=summary['scientific_route'],A_w_passed=summary['A_w_passed'],counts=counts)),flush=True)

if __name__=='__main__':
    main()
