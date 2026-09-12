"""Fixed-endpoint joint-protocol evaluation after the training process ends."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import numpy as np
import torch

from .phk_benchmark import PhkControl
from .phk_v22r_evaluator import load_reference
from .phk_v23_lf11 import ROOT, save_json, now, predict
from .phk_v23_lf11_joint import RUN, boundary_components
from .phk_v23_lf11_followup_fit import fit_model
from .phk_v23_lf11_evaluation import metrics, comparison
from .phk_v23_lf11_followup_evaluate import add_power_metrics
from .phk_v23_lf11_electric_trace_audit import audit_one

OLD = ROOT/'outputs/runs/20260912-lf11-v-pde-increment'


def closure(root):
    proof=json.loads((root/'compute-closure.json').read_text())
    if not proof['training_complete'] or not proof['compute_stopped_before_reference_read']:
        raise ValueError('real training closure required')
    return proof


def prepare(root=RUN,roles=None):
    root=Path(root)
    cfg=json.loads((root/'frozen-config.json').read_text())
    torch.set_num_threads(cfg['cpu_threads'])
    if roles is None:
        closure(root)
        campaign=json.loads((root/'campaign.json').read_text())
        results=campaign['results']
    else:
        # An already fixed arm can generate its own fields while another arm
        # trains. This path never loads a reference or changes either model.
        results={role:json.loads((root/role/'result.json').read_text()) for role in roles}
    audits=root/'electric_audit'; audits.mkdir(exist_ok=True)
    for role,result in results.items():
        if result['status']!='VALID_FIXED_ENDPOINT': continue
        saved=torch.load(root/role/'checkpoint.pt',map_location='cpu',weights_only=False)
        model=fit_model(saved['config'],saved['model_state_dict'],saved['temperature_adapter'])
        destination=root/role/'prediction.npz'
        if not destination.exists():
            print(json.dumps({'prediction_started':role}),flush=True)
            predict(model,cfg,destination,'cpu')
        if not (audits/(role+'.json')).exists():
            with np.load(destination,allow_pickle=False) as p:
                x,z,times=[p[k] for k in ('x','z','time')]
                fields={k:p[k] for k in ('potential','temperature','phase')}
            audit_one(model,fields,x,z,times,audits,role)
            del fields
        subterms_path=root/role/'boundary-subterms.json'
        if not subterms_path.exists():
            pool=torch.load(root/'fixed-pools.pt',map_location='cpu',weights_only=False)['audit']
            parts={key:float(value.detach()) for key,value in boundary_components(model,pool['bc_ic'][0],cfg).items()}
            total=sum(parts.values())
            np.testing.assert_allclose(total,result['fixed_physics_audit']['boundary'],rtol=1e-12,atol=1e-12)
            save_json(subterms_path,{'role':role,'components':parts,'sum':total,'pool_seed':pool['seed'],
                      'reference_read':False,'optimizer_updates':0,'new_sampling_pool':False,
                      'scope':'Scalar split of the already frozen endpoint BC audit; no additional equation-by-head gradient node.'})
        print(json.dumps({'own_field_and_contact_audit_ready':role}),flush=True)


def functional_comparison(candidate,base,cfg):
    if not candidate['valid'] or not base['valid']:
        return {'passed':False,'reason':'numerical_validity_failure'}
    c,b=candidate['metrics'],base['metrics']; rule=cfg['functional_rule']
    keys=rule['gain']+rule['noninferior']
    if any(c.get(k) is None or b.get(k) is None for k in keys):
        return {'passed':False,'reason':'required_metric_not_identifiable'}
    atol=cfg['decision']['absolute_tolerance']
    gain={k:b[k]-c[k]>=max(.1*b[k],rule['extra_normalized_absolute_tolerance']) for k in rule['gain']}
    noninferior={k:c[k]<=b[k]+max(.05*b[k],atol[k]) for k in rule['noninferior']}
    return {'passed':all(gain.values()) and all(noninferior.values()),'gain':gain,'noninferior':noninferior,
            'relative_changes':{k:(c[k]-b[k])/max(b[k],atol.get(k,1e-6)) for k in keys},
            'claim_layer':'limited device-function signal; separate from phase reconstruction and strict usability'}


def conditional_decision(records,diagnosis,cfg):
    if not all(k in records and records[k]['valid'] for k in ('P_U','D_B')):
        return {'triggered':False,'reason':'required_matched_endpoints_missing_or_invalid'}
    c,b=records['P_U']['metrics'],records['D_B']['metrics']; cond=cfg['conditional']; damage={}
    for key in cond['damage_metrics']:
        tolerance=cfg['decision']['absolute_tolerance'].get(key,
            cond['dimensional_defect_tolerance'] if key in ('current_balance_rms','power_defect_rms') else cond['normalized_tolerance'])
        damage[key]=bool(c[key] is not None and b[key] is not None and
                         c[key]>b[key]+max(cond['damage_relative']*abs(b[key]),tolerance))
    direction=bool(diagnosis.get('all_three_nodes_supported',False))
    return {'triggered':bool(any(damage.values()) and direction),'matched_damage':damage,
            'all_three_nodes_direction_supported':direction,
            'consistent_channels':diagnosis.get('consistent_supported_channels',[]),
            'reason':'Both endpoint damage and a consistent material amplitude channel at all three frozen nodes are required.',
            'large_bottom_error_is_not_a_trigger':True}


def evaluate(root=RUN):
    root=Path(root); proof=closure(root)
    if (root/'evaluation.json').exists(): raise FileExistsError('reuse completed fixed evaluation')
    cfg=json.loads((root/'frozen-config.json').read_text()); torch.set_num_threads(cfg['cpu_threads'])
    parent=torch.load(root/'parent.pt',map_location='cpu',weights_only=False)
    physical=fit_model(cfg,parent['model_state_dict'],parent['temperature_adapter']).physics
    reference,identity=load_reference(PhkControl.FULL)
    old=json.loads((OLD/'evaluation.json').read_text())
    if identity!=old['reference_sha256']: raise ValueError('changed nominal reference')
    rename={name:'LF11_'+name for name in ('D_B','P_U','P_I','P_M','warm_start')}
    records={rename.get(k,k):copy.deepcopy(v) for k,v in old['records'].items()}
    records['parent']=copy.deepcopy(records['V_continued'])
    records['parent']['origin']='EXACT_V26_COMMON_PARENT_REUSED'
    traces={}
    with np.load(OLD/'evaluation-traces.npz',allow_pickle=False) as source:
        for name in old['records']:
            prefix=name+'__'
            traces[rename.get(name,name)]={k[len(prefix):]:source[k] for k in source.files if k.startswith(prefix)}
    traces['parent']=traces['V_continued']
    rs=physical
    # Reference peaks determine display times only, never endpoints or training.
    from .phk_v22r_evaluator import _physical_contract, _event_summary
    ev=_physical_contract().payload['qualification_event']; region=ev['roi']
    roi=(np.abs(reference.grid.cell_x)<=region['abs_x_max']) & (reference.grid.cell_z>=region['z_min']) & (reference.grid.cell_z<=region['z_max'])
    events=_event_summary(reference.phase,time=reference.time,roi=roi,period=physical.period,
                          phase_threshold=ev['phase_threshold'],event_fraction=ev['event_threshold_roi_fraction'])
    peaks=[c['peak_time_index'] for c in events['cycles']]
    snapshots={'reference__'+k:getattr(reference,k)[peaks].copy() for k in ('potential','temperature','phase')}
    campaign=json.loads((root/'campaign.json').read_text())
    for role,result in campaign['results'].items():
        if result['status']!='VALID_FIXED_ENDPOINT':
            records[role]={'valid':False,'metrics':None,'cycles':[],'status':result['status']}
            continue
        with np.load(root/role/'prediction.npz',allow_pickle=False) as p:
            if not (np.array_equal(p['x'],reference.grid.x_centers) and np.array_equal(p['z'],reference.grid.z_centers) and np.array_equal(p['time'],reference.time)):
                raise ValueError('prediction axes differ from reference')
            fields={k:p[k] for k in ('potential','temperature','phase')}
        record,trace=metrics(fields,reference,physical,cfg)
        add_power_metrics(record,trace,reference.time,reference.top_current,reference.joule_power)
        record.update(origin='NEW_JOINT_PROTOCOL_FIXED_ENDPOINT',fixed_physics_audit=result['fixed_physics_audit'])
        records[role]=record; traces[role]=trace
        snapshots.update({role+'__'+k:v[peaks].copy() for k,v in fields.items()})
        with np.load(root/'electric_audit'/(role+'.npz'),allow_pickle=False) as a:
            for key in ('top_current','bottom_current','joule_power','input_power'):
                np.testing.assert_allclose(a[key],trace[key],rtol=1e-12,atol=1e-12)
        print(json.dumps({'evaluated':role,'metrics':record['metrics'],'strict':record['strict_device_pass']}),flush=True)
        del fields
    for role,path in (('parent',OLD/'v_continue/prediction.npz'),('B_logit_waveform_contact',OLD/'contact-prediction.npz')):
        with np.load(path,allow_pickle=False) as source:
            for key in ('potential','temperature','phase'):
                snapshots[role+'__'+key]=source[key][peaks].copy()
    pairs={}
    for baseline,candidate in (('D_I','D_B'),('D_B','P_U')):
        pairs[baseline+'_to_'+candidate]={
            'reconstruction':comparison(records[candidate],records[baseline],cfg['decision']),
            'function':functional_comparison(records[candidate],records[baseline],cfg)}
    baselines={candidate:{baseline:{'reconstruction':comparison(records[candidate],records[baseline],cfg['decision']),
                                    'function':functional_comparison(records[candidate],records[baseline],cfg)}
                           for baseline in cfg['strong_baselines'] if baseline in records}
               for candidate in cfg['roles'] if candidate in records}
    diagnosis=json.loads((root/'equation-head-diagnosis.json').read_text())
    decision=conditional_decision(records,diagnosis,cfg)
    result={'schema_id':'lf11-joint-three-arm-evaluation-v1','recorded_utc':now(),'reference_sha256':identity,
            'records':records,'matched_pairs':pairs,'strong_baseline_comparisons':baselines,
            'conditional_decision':decision,'strict_device_gate_separate':True,
            'old_V_fit_gate_unmet_preserved':True,
            'scope':'specified-parent single-initialization nominal protocol; no independent confirmation, formal OOD or experimental validation'}
    save_json(root/'evaluation.json',result); save_json(root/'conditional-decision.json',decision)
    np.savez_compressed(root/'evaluation-traces.npz',time=reference.time,reference_current=reference.top_current,
                        reference_power=reference.joule_power,
                        **{name+'__'+key:value for name,tr in traces.items() for key,value in tr.items()})
    np.savez_compressed(root/'field-snapshots.npz',x=reference.grid.x_centers,z=reference.grid.z_centers,
                        times=reference.time[peaks],**snapshots)
    print(json.dumps({'matched_pairs':pairs,'conditional_decision':decision}),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','evaluate'))
    p.add_argument('--root',type=Path,default=RUN)
    p.add_argument('--roles',nargs='+',choices=('D_I','D_B','P_U'))
    args=p.parse_args()
    if args.action=='prepare':prepare(args.root,args.roles)
    else:
        if args.roles:p.error('reference evaluation requires the complete fixed campaign')
        evaluate(args.root)
