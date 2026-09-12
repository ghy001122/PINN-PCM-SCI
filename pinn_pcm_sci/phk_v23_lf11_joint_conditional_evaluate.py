"""Evaluate a completed conditional batch without endpoint selection or retraining."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import numpy as np
import torch

from .phk_benchmark import PhkControl
from .phk_v22r_evaluator import load_reference
from .phk_v23_lf11 import ROOT, save_json, now
from .phk_v23_lf11_joint import RUN
from .phk_v23_lf11_followup_fit import fit_model
from .phk_v23_lf11_evaluation import metrics, comparison
from .phk_v23_lf11_followup_evaluate import add_power_metrics
from .phk_v23_lf11_joint_evaluate import closure, functional_comparison


def evaluate(root):
    root=Path(root);closure(root)
    if (root/'evaluation.json').exists():raise FileExistsError('reuse fixed conditional evaluation')
    cfg=json.loads((root/'frozen-config.json').read_text())
    torch.set_num_threads(cfg['cpu_threads'])
    main=ROOT/cfg['main_root']
    preceding=main/'conditional' if cfg['roles']==['D_N'] else main
    inherited=json.loads((preceding/'evaluation.json').read_text())
    records=copy.deepcopy(inherited['records'])
    saved=torch.load(root/'parent.pt',map_location='cpu',weights_only=False)
    physical=fit_model(cfg,saved['model_state_dict'],True).physics
    reference,identity=load_reference(PhkControl.FULL)
    if identity!=inherited['reference_sha256']:raise ValueError('changed fixed nominal reference')
    campaign=json.loads((root/'campaign.json').read_text());traces={}
    for role,result in campaign['results'].items():
        if result['status']!='VALID_FIXED_ENDPOINT':
            records[role]={'valid':False,'metrics':None,'cycles':[],'status':result['status']};continue
        with np.load(root/role/'prediction.npz',allow_pickle=False) as f:
            if not (np.array_equal(f['x'],reference.grid.x_centers) and np.array_equal(f['z'],reference.grid.z_centers) and np.array_equal(f['time'],reference.time)):
                raise ValueError('conditional prediction grid changed')
            fields={k:f[k] for k in ('potential','temperature','phase')}
        record,trace=metrics(fields,reference,physical,cfg)
        add_power_metrics(record,trace,reference.time,reference.top_current,reference.joule_power)
        record.update(origin='CONDITIONAL_FIXED_BUDGET_ENDPOINT',fixed_physics_audit=result['fixed_physics_audit'])
        records[role]=record;traces[role]=trace
        with np.load(root/'electric_audit'/(role+'.npz'),allow_pickle=False) as f:
            for key in ('top_current','bottom_current','joule_power','input_power'):
                np.testing.assert_allclose(f[key],trace[key],rtol=1e-12,atol=1e-12)
        print(json.dumps({'conditional_evaluated':role,'metrics':record['metrics'],'strict':record['strict_device_pass']}),flush=True)
        del fields
    contrasts={}
    pairs=(('R','G'),('R','N'),('G','N')) if cfg['roles']!=['D_N'] else (('D_N','N'),('R','D_N'),('G','D_N'))
    for baseline,candidate in pairs:
        contrasts[baseline+'_to_'+candidate]={
            'reconstruction':comparison(records[candidate],records[baseline],cfg['decision']),
            'function':functional_comparison(records[candidate],records[baseline],cfg)}
    baselines={name:{base:{'reconstruction':comparison(records[name],records[base],cfg['decision']),
                          'function':functional_comparison(records[name],records[base],cfg)}
                     for base in cfg['strong_baselines'] if base in records}
               for name in cfg['roles']}
    if cfg['roles']==['D_N']:
        prior=inherited['followup_decision']['positive_layers_against_both_R_G']
        final={layer:bool(prior[layer] and contrasts['D_N_to_N'][layer]['passed'])
               for layer in ('reconstruction','function')}
        decision={'D_N_executed':True,'N_interior_increment_by_layer':final,
                  'claim':'Each layer still requires superiority to its no-interior counterfactual; no union success claim.'}
    else:
        layers={layer:all(contrasts[base+'_to_N'][layer]['passed'] for base in ('R','G'))
                for layer in ('reconstruction','function')}
        decision={'D_N_triggered':any(layers.values()),'positive_layers_against_both_R_G':layers,
                  'claim':'The execution trigger does not combine the two scientific claim layers.'}
    output={'schema_id':'lf11-joint-conditional-evaluation-v1','recorded_utc':now(),
            'reference_sha256':identity,'records':records,'matched_pairs':contrasts,
            'strong_baseline_comparisons':baselines,'followup_decision':decision,
            'scope':'same exposed nominal case and inherited initialization; no independent confirmation',
            'R_is_reused_Adam1000_plus_new_fixed_200_evaluations':True}
    save_json(root/'evaluation.json',output);save_json(root/'followup-decision.json',decision)
    np.savez_compressed(root/'evaluation-traces.npz',time=reference.time,reference_current=reference.top_current,
                        reference_power=reference.joule_power,
                        **{name+'__'+key:value for name,tr in traces.items() for key,value in tr.items()})
    print(json.dumps({'conditional_matched_pairs':contrasts,'followup_decision':decision}),flush=True)
    return output


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=RUN/'conditional')
    evaluate(p.parse_args().root)
