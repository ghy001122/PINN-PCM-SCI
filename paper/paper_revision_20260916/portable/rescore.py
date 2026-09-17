"""Re-score the complete array archive: python -I portable/rescore.py --root .

Dependencies: Python >=3.11, NumPy >=2. No torch, SciPy, checkpoint loading,
model forward/backward, or PDE solves are used. All paths are archive-relative.
"""
from __future__ import annotations
import argparse
import csv
import gc
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import numpy as np

spec = importlib.util.spec_from_file_location('frozen_metrics', Path(__file__).with_name('frozen_metrics.py'))
core = importlib.util.module_from_spec(spec); spec.loader.exec_module(core)


def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))


def plain(obj):
    if isinstance(obj, dict): return {str(k):plain(v) for k,v in obj.items()}
    if isinstance(obj, (list,tuple)): return [plain(v) for v in obj]
    if isinstance(obj, np.ndarray): return obj.tolist()
    if isinstance(obj, np.generic): return obj.item()
    return obj


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plain(obj), indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def locate(root, relative):
    path = (root/relative).resolve()
    if Path(relative).is_absolute() or not path.is_relative_to(root.resolve()):
        raise ValueError('Nonportable archive path: '+relative)
    return path


class Physics(SimpleNamespace):
    def waveform(self, time):
        if self.protocol == 'original':
            local = np.remainder(time-self.time_start, self.period)
            value = np.where(local < self.ramp_up_end, self.waveform_amplitude*local/self.ramp_up_end,
                np.where(local <= self.hold_end, self.waveform_amplitude,
                np.where(local < self.ramp_down_end, self.waveform_amplitude*(self.ramp_down_end-local)/
                         (self.ramp_down_end-self.hold_end), 0.)))
        else:
            value = np.zeros_like(time)
            for start in (0., self.period):
                elapsed = time-start
                unit = np.where((elapsed >= 0)&(elapsed < self.ramp_up_end), elapsed/self.ramp_up_end,
                    np.where((elapsed >= self.ramp_up_end)&(elapsed < self.hold_end), 1.,
                    np.where((elapsed >= self.hold_end)&(elapsed < self.ramp_down_end),
                             (self.ramp_down_end-elapsed)/(self.ramp_down_end-self.hold_end), 0.)))
                value = value+self.waveform_amplitude*unit
        return np.where((time >= self.time_start)&(time < self.time_end), value, 0.)


class Grid(SimpleNamespace):
    def bottom_overlap(self, fraction):
        if fraction != self.heater_width_fraction: raise ValueError('heater mismatch')
        return self.overlap


def geometry(root, manifest):
    grid = Grid(**manifest['grid_metadata'])
    with np.load(locate(root, manifest['grid_arrays']), allow_pickle=False) as f:
        for k in f.files: setattr(grid, k, f[k])
    return grid


def arrays(path):
    with np.load(path, allow_pickle=False) as f:
        return {k:f[k] for k in ('x','z','time','potential','temperature','phase')}, (
            f['joule_density'] if 'joule_density' in f else None)


def canonical_coordinates(fields, grid):
    """Validate both stored layouts against the identical cell ordering.

    References store one x/z value per cell; projected predictions store the
    two independent axes. Only their coordinate metadata is normalized here.
    No field value is interpolated, reordered, rounded or otherwise changed.
    """
    for name, axis, cells in (('x', grid.x_centers, grid.cell_x),
                               ('z', grid.z_centers, grid.cell_z)):
        actual = fields[name]
        expected = axis if actual.shape == axis.shape else cells
        np.testing.assert_array_equal(actual, expected)
        fields[name] = axis
    expected_shape = (len(fields['time']), grid.cell_count)
    if any(fields[name].shape != expected_shape for name in ('potential', 'temperature', 'phase')):
        raise ValueError('Unexpected field layout; no automatic reshaping')


def deposition(fields, grid, physics):
    """Same half-resistance allocation, evaluated on existing V, never solved."""
    first,second = grid.internal_first,grid.internal_second
    half,area=grid.internal_half_distance,grid.internal_area
    top=np.arange((grid.nz-1)*grid.nx,grid.nz*grid.nx)
    bottom=np.flatnonzero(grid.overlap>0)
    heat=np.empty_like(fields['potential'])
    for i,(v,t,ph,u) in enumerate(zip(fields['potential'],fields['temperature'],fields['phase'],
                                      physics.waveform(fields['time']),strict=True)):
        sigma=np.exp(physics.conductivity_temperature_gain*t+
                     np.log(physics.conductivity_phase_ratio)*ph**2*(3-2*ph))
        ri=half/(sigma[first]*area);rj=half/(sigma[second]*area)
        current=(v[first]-v[second])/(ri+rj)
        cell=np.zeros(grid.cell_count)
        np.add.at(cell,first,current**2*ri);np.add.at(cell,second,current**2*rj)
        np.add.at(cell,top,2*sigma[top]*grid.dx/grid.dz*(u-v[top])**2)
        np.add.at(cell,bottom,2*sigma[bottom]*grid.overlap[bottom]/grid.dz*v[bottom]**2)
        heat[i]=cell/grid.cell_volumes
    return heat


def load_reference(root, path, grid, physics, config):
    fields,_=arrays(locate(root,path))
    with np.load(locate(root,path),allow_pickle=False) as f:
        device={k:f[k] for k in ('top_current','bottom_current','joule_power')}
    canonical_coordinates(fields,grid)
    ref=SimpleNamespace(**fields,**device,grid=grid)
    heat=deposition(fields,grid,physics)
    rs=config['qualification_event']['roi']
    roi=(abs(grid.cell_x)<=rs['abs_x_max'])&(grid.cell_z>=rs['z_min'])&(grid.cell_z<=rs['z_max'])
    ev=config['qualification_event']
    events=core._event_summary(ref.phase,time=ref.time,roi=roi,period=physics.period,
        phase_threshold=ev['phase_threshold'],event_fraction=ev['event_threshold_roi_fraction'])
    return ref,heat,events,roi


def pair(c,b,cfg):
    return {'A':core.comparison(c,b,cfg['decision']),'B':core.functional_comparison(c,b,cfg)}


def noninferior(c,b,keys,cfg):
    if not c['valid'] or not b['valid']: return {k:False for k in keys}
    atol=cfg['decision']['absolute_tolerance']
    return {k:c['metrics'][k] <= b['metrics'][k]+max(.05*b['metrics'][k],atol.get(k,1e-6)) for k in keys}


def score(root,item,reference,heat,events,roi,physics,cfg,out,refname,oldscales):
    f,q=arrays(locate(root,item['prediction']))
    canonical_coordinates(f,reference.grid)
    for k,axis in [('x',reference.x),('z',reference.z),('time',reference.time)]: np.testing.assert_array_equal(f[k],axis)
    fields={k:f[k] for k in ('potential','temperature','phase')}
    record,traces=core.metrics(fields,reference,physics,cfg)
    if not record['valid']: raise ValueError('Invalid fixed array endpoint: '+item['id'])
    core.add_power_metrics(record,traces,f['time'],reference.top_current,reference.joule_power)
    qscale=core.field_rms(heat,np.zeros_like(heat),f['time'])
    record['metrics']['local_joule_NRMSE']=core.field_rms(q,heat,f['time'])/qscale if qscale>1e-12 else None
    # Keep the old bottom-vs-top gate. Add a separately named native bottom check.
    top_scale=core.time_rms(reference.top_current,f['time'])
    bottom_scale=core.time_rms(reference.bottom_current,f['time'])
    power_scale=core.time_rms(reference.joule_power,f['time'])
    record['metrics']['top_current_rms_error']=core.time_rms(traces['top_current']-reference.top_current,f['time'])
    record['metrics']['bottom_native_NRMSE']=core.time_rms(traces['bottom_current']-reference.bottom_current,f['time'])/max(bottom_scale,1e-12)
    record['normalizers']={'top_current':top_scale,'bottom_current':bottom_scale,'power':power_scale,'local_q':qscale}
    record['fixed_old_denominator']={
        'EI':record['metrics']['top_current_rms_error']/max(oldscales['top_current'],1e-12),
        'bottom_current_NRMSE':record['metrics']['bottom_current_rms_error']/max(oldscales['top_current'],1e-12),
        'power_trace_NRMSE':record['metrics']['power_trace_rms_error']/max(oldscales['power'],1e-12),
        'local_joule_NRMSE':core.field_rms(q,heat,f['time'])/max(oldscales['local_q'],1e-12)}
    for c,rc in zip(record['cycles'],events['cycles'],strict=True):
        c['reference_event_present']=rc['event_time'] is not None
        c['false_positive_event']=rc['event_time'] is None and c['event_time'] is not None
        c['false_negative_target_mass']=c['teacher_active_target_mass']-c['true_positive_target_mass']
        c['false_positive_target_mass']=c['predicted_active_target_mass']-c['true_positive_target_mass']
    with np.load(locate(root,item['readout']),allow_pickle=False) as own:
        for k in ('top_current','bottom_current','joule_power'):
            np.testing.assert_allclose(own[k],traces[k],rtol=1e-10,atol=1e-11)
    record.update(id=item['id'],protocol=item['protocol'],seed=item['seed'],role=item['role'],
                  origin=item['origin'],training_budget_complete=True,reference=refname)
    tracefile=out/refname/(item['id'].replace('/','_')+'-traces.npz')
    tracefile.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(tracefile,time=f['time'],reference_current=reference.top_current,
        reference_power=reference.joule_power,reference_roi_fraction=events['roi_fraction'],**traces)
    # Full time histories plus four locations fixed before training; never selected by reference.
    if item['protocol']=='shorter':
        inds=[int(np.argmin(abs(f['time']-t))) for t in cfg['display_rule']['times']]
        np.testing.assert_allclose(f['time'][inds],cfg['display_rule']['times'],atol=1e-14)
        np.savez_compressed(out/refname/(item['id'].replace('/','_')+'-display.npz'),
            time=f['time'][inds],x=f['x'],z=f['z'],phase=f['phase'][inds],reference_phase=reference.phase[inds],
            false_negative=(reference.phase[inds]>=.5)&(f['phase'][inds]<.5),
            false_positive=(reference.phase[inds]<.5)&(f['phase'][inds]>=.5))
    print(json.dumps({'scored':item['id'],'reference':refname,'Ephi':record['metrics']['Ephi']}),flush=True)
    return record


def compare_saved(actual,expected,path=''):
    """Check published metrics/events/flags without hiding a changed definition."""
    checked=0
    if isinstance(expected,dict):
        for k,v in expected.items():
            if k not in actual: raise AssertionError('Missing reproduced field '+path+'/'+k)
            checked+=compare_saved(actual[k],v,path+'/'+k)
    elif isinstance(expected,list):
        if len(actual)!=len(expected): raise AssertionError(path+' length')
        for i,v in enumerate(expected):checked+=compare_saved(actual[i],v,path+'/'+str(i))
    elif isinstance(expected,(float,int)) and not isinstance(expected,bool):
        np.testing.assert_allclose(actual,expected,rtol=2e-10,atol=2e-12,err_msg=path);checked=1
    else:
        if actual!=expected: raise AssertionError((path,actual,expected))
        checked=1
    return checked


def published_tables(root,records):
    def oid(row):
        protocol={'Original':'original','Shorter gap':'shorter'}[row['protocol']]
        if row['role']=='B_E':return protocol+'/B_E'
        role={'E/projected':'E','F_raw/projected':'F'}[row['role']]
        return protocol+'/'+row['seed']+'/'+role
    count=0
    with (root/'expected/published-main-table.csv').open(encoding='utf-8',newline='') as f:
        for row in csv.DictReader(f):
            r=records[oid(row)]
            for k in ('S','Ephi','ET','EV'):count+=compare_saved(r['metrics'][k],float(row[k]),oid(row)+'/'+k)
            for col,k in [('current_percent','EI'),('power_percent','power_trace_NRMSE'),('energy_percent','energy_error')]:
                count+=compare_saved(100*r['metrics'][k],float(row[col]),oid(row)+'/'+col)
            count+=compare_saved(r['valid'],row['valid']=='True','table validity')
            count+=compare_saved(r['strict_device_pass'],row['strict']=='True','table strict')
    eventcount=0
    with (root/'expected/published-events.csv').open(encoding='utf-8',newline='') as f:
        for row in csv.DictReader(f):
            r=records[oid(row)]['cycles'][int(row['cycle'])-1]
            for key,value in row.items():
                if key in ('protocol','seed','role') or value=='':continue
                expected=(value=='True') if value in ('True','False') else float(value)
                eventcount+=compare_saved(r[key],expected,oid(row)+'/cycle/'+key)
    return dict(main_table_checked_values=count,event_table_checked_values=eventcount,passed=True)


def decisions(records,cfg,protocol):
    result={}
    baseline=records[protocol+'/B_E']
    for seed in (29,43):
        pre=protocol+f'/{seed}/'
        e,f=records[pre+'E'],records[pre+'F']
        item={'E_vs_soft':pair(e,f,cfg),'soft_vs_E':pair(f,e,cfg),
              'E_vs_B_E':pair(e,baseline,cfg),'soft_vs_B_E':pair(f,baseline,cfg)}
        if pre+'E_C' in records:
            c=records[pre+'E_C']; r=records[pre+'E_R']; i=records[pre+'E_I']
            for role,candidate in [('E_C',c),('E_R',r),('E_I',i)]:
                against=pair(candidate,c,cfg)
                # "Corresponding noninferiority" retains the exact original
                # A and B guard sets. Additional primary-metric checks must
                # not silently become new eligibility gates.
                na=noninferior(candidate,e,('ET','EI','EV'),cfg)
                nb=noninferior(candidate,e,tuple(cfg['functional_rule']['noninferior']),cfg)
                all_parent=noninferior(candidate,e,('S','Ephi','ET','EV','EI','bottom_current_NRMSE','power_trace_NRMSE'),cfg)
                ns=[noninferior(candidate,b,('S','Ephi','ET','EV','EI','power_trace_NRMSE'),cfg) for b in (c,e)]
                item[role]={'versus_E_C':against,'versus_parent':pair(candidate,e,cfg),
                    'versus_soft':pair(candidate,f,cfg),'versus_B_E':pair(candidate,baseline,cfg),
                    'parent_noninferior_A':na,'parent_noninferior_B':nb,
                    'parent_all_metric_noninferiority_report_only':all_parent,
                    'matched_A':against['A']['passed'] and all(na.values()),
                    'matched_B':against['B']['passed'] and all(nb.values()),
                    'strict_increment':candidate['strict_device_pass'] and not e['strict_device_pass'] and
                       not c['strict_device_pass'] and all(all(v.values()) for v in ns),
                    'strict_noninferiority':ns}
            gatepair=pair(i,r,cfg)
            gatestrict=(i['strict_device_pass'] and not r['strict_device_pass'] and
                        all(noninferior(i,r,('S','Ephi','ET','EV','EI','power_trace_NRMSE'),cfg).values()))
            item['gate_independence']={'versus_equal_parameter_E_R':gatepair,
                'A':item['E_I']['matched_A'] and gatepair['A']['passed'],
                'B':item['E_I']['matched_B'] and gatepair['B']['passed'],
                'strict':item['E_I']['strict_increment'] and gatestrict}
        result[str(seed)]=item
    return result


def sensitivity(old,new,oldheat,newheat,roi,time,old_events,new_events):
    delta={'S':float(np.trapezoid(np.mean((old.phase>=.5)!=(new.phase>=.5),axis=1),time)/(time[-1]-time[0])),
        'Ephi':core.field_rms(new.phase,old.phase,time,roi),
        'ET':core.field_rms(new.temperature,old.temperature,time,roi)/.45,
        'EV':core.field_rms(new.potential,old.potential,time),
        'EI_rms':core.time_rms(new.top_current-old.top_current,time),
        'power_rms':core.time_rms(new.joule_power-old.joule_power,time),
        'q_rms':core.field_rms(newheat,oldheat,time)}
    return {'delta':delta,'old_reference_events':old_events,'new_reference_events':new_events,
        'event_existence_changed':[(a['event_time'] is None) != (b['event_time'] is None)
             for a,b in zip(old_events['cycles'],new_events['cycles'],strict=True)],
        'time_only_not_space_convergence':True}


def margins(old,new,delta,protocol):
    rows=[]
    for seed in (29,43):
        pre=protocol+f'/{seed}/'
        comparisons=[(pre+'E',pre+'F'),(pre+'E',protocol+'/B_E')]
        if pre+'E_C' in old:
            comparisons += [(pre+r,pre+b) for r,b in [('E_R','E_C'),('E_I','E_C'),('E_I','E_R')]]
        for c,b in comparisons:
            for k in ('S','Ephi','ET','EV','EI','power_trace_NRMSE','bottom_current_NRMSE'):
                o=old[b]['metrics'][k]-.1*old[b]['metrics'][k]-old[c]['metrics'][k]
                n=.9*new[b]['metrics'][k]-new[c]['metrics'][k]
                d=delta.get(k)
                fixed=None
                if k in ('EI','bottom_current_NRMSE','power_trace_NRMSE'):
                    fixed=.9*new[b]['fixed_old_denominator'][k]-new[c]['fixed_old_denominator'][k]
                    scale=old[c]['normalizers']['power' if k=='power_trace_NRMSE' else 'top_current']
                    d=delta['power_rms' if k=='power_trace_NRMSE' else 'EI_rms']/scale
                tested=n if fixed is None else fixed
                if d is not None and abs(tested-o)>1.9*d+2e-12:raise AssertionError('Triangle margin bound violated')
                rows.append(dict(protocol=protocol,seed=seed,candidate=c,baseline=b,metric=k,
                    old_margin=o,new_margin=n,new_margin_fixed_old_denominator=fixed,
                    tested_margin_change=tested-o,triangle_bound=1.9*d if d is not None else None,
                    comparison_with_same_norm=True,relative_gate_only_absolute_tolerances_applied_separately=True))
    return rows


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--output',default='rescore-output');p.add_argument('--old-only',action='store_true')
    a=p.parse_args();root=a.root.resolve();manifest=read(root/'manifest.json');grid=geometry(root,manifest)
    out=locate(root,a.output)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('Scoring output is not empty; inspect rather than overwrite')
    out.mkdir(parents=True,exist_ok=True)
    records={'old':{},'refined':{}};all_decisions={};references={};old_reproduction={}
    table_reproduction={}
    for protocol,entry in manifest['protocols'].items():
        cfg=read(locate(root,entry['config']));physics=Physics(**entry['physics'],protocol=protocol)
        old,oh,oe,roi=load_reference(root,entry['references']['old'],grid,physics,cfg)
        scales={'top_current':core.time_rms(old.top_current,old.time),'power':core.time_rms(old.joule_power,old.time),
                'local_q':core.field_rms(oh,np.zeros_like(oh),old.time)}
        items=[i for i in manifest['objects'] if i['protocol']==protocol]
        for item in [i for i in items if i['origin']=='historical']:
            rec=score(root,item,old,oh,oe,roi,physics,cfg,out,'old',scales)
            expected=read(locate(root,item['expected_record']))
            keys=('metrics','cycles','valid','strict_device_pass','event_failures')
            checked=compare_saved({k:rec[k] for k in keys},{k:expected[k] for k in keys},item['id'])
            old_reproduction[item['id']]={'passed':True,'checked_values':checked}
            records['old'][item['id']]=rec
        old_decisions=decisions(records['old'],cfg,protocol)
        expected_decisions=read(locate(root,entry['expected_decisions']))
        for seed in ('29','43'):
            for k in ('E_vs_soft','soft_vs_E','E_vs_B_E','soft_vs_B_E'):
                compare_saved(old_decisions[seed][k],expected_decisions[seed][k],protocol+'/'+seed+'/'+k)
        save(out/'old-reproduction.json',{'status':'PASS','records':old_reproduction,'protocol_completed':protocol})
        if len(old_reproduction)==10:
            table_reproduction=published_tables(root,records['old'])
            save(out/'old-reproduction.json',{'status':'PASS','records':old_reproduction,'published_tables':table_reproduction})
        for item in [i for i in items if i['origin']=='new_phase_adapter']:
            records['old'][item['id']]=score(root,item,old,oh,oe,roi,physics,cfg,out,'old',scales)
        all_decisions.setdefault('old',{})[protocol]=decisions(records['old'],cfg,protocol)
        save(out/'old-results.json',{'records':records['old'],'decisions':all_decisions['old']})
        del old,oh;gc.collect()
    # All ten historical records and their decisions are checked before any
    # refined-reference score. New arrays have already received the old score.
    for protocol,entry in manifest['protocols'].items():
        if not a.old_only and 'refined' in entry['references']:
            cfg=read(locate(root,entry['config']));physics=Physics(**entry['physics'],protocol=protocol)
            old,oh,oe,roi=load_reference(root,entry['references']['old'],grid,physics,cfg)
            scales={'top_current':core.time_rms(old.top_current,old.time),'power':core.time_rms(old.joule_power,old.time),
                    'local_q':core.field_rms(oh,np.zeros_like(oh),old.time)}
            items=[i for i in manifest['objects'] if i['protocol']==protocol]
            new,nh,ne,nroi=load_reference(root,entry['references']['refined'],grid,physics,cfg)
            np.testing.assert_array_equal(old.time,new.time);np.testing.assert_array_equal(roi,nroi)
            references[protocol]=sensitivity(old,new,oh,nh,roi,old.time,oe,ne)
            for item in items:records['refined'][item['id']]=score(root,item,new,nh,ne,roi,physics,cfg,out,'refined',scales)
            all_decisions.setdefault('refined',{})[protocol]=decisions(records['refined'],cfg,protocol)
            references[protocol]['margins']=margins(records['old'],records['refined'],references[protocol]['delta'],protocol)
            del new,nh,old,oh;gc.collect()
    save(out/'results.json',{'status':'ARRAY_ONLY_RESCORING_COMPLETE','records':records,'decisions':all_decisions,
        'reference_sensitivity':references,'old_reproduction':old_reproduction,
        'published_table_reproduction':table_reproduction,
        'execution':{'python':sys.version,'numpy':np.__version__,'isolated_python':bool(sys.flags.isolated),
            'neural_models_loaded':0,'neural_forwards':0,'linear_solves':0,'private_repository_imports':False}})
    rows=[]
    for refname,rr in records.items():
        for name,r in rr.items():rows.append({'reference':refname,'id':name,**r['metrics'],
            'strict_device_pass':r['strict_device_pass']})
    with (out/'metrics.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps({'status':'COMPLETE','historical_objects_reproduced':len(old_reproduction),
        'old_reference_objects':len(records['old']),'refined_reference_objects':len(records['refined'])}),flush=True)


if __name__ == '__main__':main()
