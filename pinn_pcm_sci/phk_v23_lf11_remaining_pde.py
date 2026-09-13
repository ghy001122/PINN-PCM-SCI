"""One bounded, fixed-objective remaining-PDE counterfactual from V28 D_E.

The only new scientific coefficient multiplies the complete remaining PDE.
First-order blocks retain the original implicit electrical VJP. No reference
reader or parameter Hessian is used in this module.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import numpy as np
import torch

from .phk_v23_lf11 import ROOT, SparseData, save_json, now
from .phk_v23_lf11_elimination import Experiment, deserialize_pool, save_checkpoint
from .phk_v23_lf11_elimination_physics import thermal_phase_residual, boundary_loss, initial_loss
from .phk_v23_lf11_v_continue import continued_lbfgs

RUN = ROOT/'outputs/runs/20260913-lf11-remaining-pde'
CONFIG = ROOT/'configs/phk_v23/lf11_remaining_pde_sprint.json'
BLOCKS = ('observation', 'boundary', 'thermal', 'phase')


class FixedExperiment(Experiment):
    def fixed(self, pool, calibration, coefficients, *, backward=False, counter='audit'):
        """Exact inherited sums, with separately selectable weighted blocks.

        Each time has one aggregated backward. A phase-only scan need not solve
        electricity because the phase equation has no V/q dependency.
        """
        if backward:
            key = 'complete_objective_gradient_evaluations' if counter == 'complete' else 'audit_objective_gradient_evaluations'
            self.calls[key] += 1
        else:
            self.calls['audit_objective_evaluations'] += 1
        a, b = max(calibration['aE'], 1e-12), max(calibration['bE'], 1e-12)
        co, cb, ct, cp = [coefficients.get(k, 0.) for k in BLOCKS]
        groups = self.obs.groups() if co else {}
        physics_times = pool['times'] if cb or ct or cp else {}
        totals = {k: 0. for k in ('observation','obs_V','obs_T','obs_phase','boundary','initial','thermal','phase','objective')}
        for t in sorted(set(groups) | set(physics_times)):
            obs_group, phys = groups.get(t), physics_times.get(t)
            v, heat, _ = self.electric(t, obs_group is not None or (phys is not None and bool(ct)))
            loss = torch.zeros((), dtype=torch.float64, device=self.device)
            if obs_group is not None:
                observed, pieces = self.obs.loss(self.model, obs_group, v, 'D_E')
                loss = loss+co*observed/a
                totals['observation'] += float(observed.detach())
                for k,value in pieces.items(): totals[k] += float(value.detach())
            if phys is not None:
                if cb:
                    bc = phys['mass']*boundary_loss(self.model, phys['sides'])
                    loss = loss+cb*.1*5*bc/b
                    totals['boundary'] += float(bc.detach())
                if ct or cp:
                    residual = thermal_phase_residual(self.model, self.grid, t, phys['cells'], heat)
                    for key, coefficient in (('thermal', ct), ('phase', cp)):
                        if coefficient:
                            value = phys['mass']*(residual[key]/self.c['pde_scales'][key]).square().mean()
                            loss = loss+coefficient*.1*value/(3*b)
                            totals[key] += float(value.detach())
            if not torch.isfinite(loss): raise FloatingPointError('nonfinite fixed block objective')
            if backward and loss.requires_grad: loss.backward()
            totals['objective'] += float(loss.detach())
        if cb:
            ic = initial_loss(self.model, pool['initial'])
            loss = cb*.1*ic/b
            if backward and loss.requires_grad: loss.backward()
            totals['initial'] = float(ic.detach())
            totals['objective'] += float(loss.detach())
        totals['J_Tphi'] = (totals['thermal']+totals['phase'])/3
        totals['C'] = totals['observation']/a+.1*(5*totals['boundary']+totals['initial'])/b
        totals['F'] = .1*totals['J_Tphi']/b
        totals['common_C_plus_F'] = totals['C']+totals['F']
        return torch.tensor(totals['objective'], dtype=torch.float64, device=self.device), totals


def coefficients(kappa):
    return dict(observation=1., boundary=1., thermal=kappa, phase=kappa)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def vector(exp):
    return torch.cat([(p.grad if p.grad is not None else torch.zeros_like(p)).detach().reshape(-1).cpu() for p in exp.parameters]).numpy()


def vector_summary(vectors, slices):
    result = {}
    full = dict(vectors)
    full['C'] = vectors['observation']+vectors['boundary']
    full['F'] = vectors['thermal']+vectors['phase']
    full['C_plus_F'] = full['C']+full['F']
    for head, mask in slices.items():
        vecs = {k:v[mask] for k,v in full.items()}
        norms = {k:float(np.linalg.norm(v)) for k,v in vecs.items()}
        cosine, slopes = {}, {}
        for k,g in vecs.items():
            cosine[k], slopes[k] = {}, {}
            for name,direction in vecs.items():
                den = norms[k]*norms[name]
                cosine[k][name] = float(np.dot(g,direction)/den) if den > 1e-24 else None
                slopes[k][name] = float(-np.dot(g,direction)/norms[name]) if norms[name] > 1e-12 else None
        result[head] = {'norms':norms, 'cosines':cosine,
                        'local_slopes_along_negative_unit_block_gradient':slopes}
    return result


def add_counts(total, statistics):
    s = statistics['electrical']
    for key in ('forward_solves','adjoint_solves'):
        total[key] += s[key]


def make_exp(config, path, data, device):
    state = torch.load(path, map_location='cpu', weights_only=False)
    return FixedExperiment(config, state['model_state_dict'], data, device, 'D_E')


def diagnose(root, config, device):
    root.mkdir(parents=True, exist_ok=True)
    if (root/'diagnosis.json').exists(): raise FileExistsError('reuse completed diagnosis')
    hist = ROOT/config['historical_root']
    for name in ('calibration.json','calibration-pool.json','lbfgs-pool.json','audit-pool.json'):
        shutil.copyfile(hist/name, root/name)
    cal = read(root/'calibration.json')
    pools = {name:deserialize_pool(read(root/(name+'-pool.json'))) for name in ('calibration','lbfgs','audit')}
    data = SparseData(ROOT/config['sparse'])
    paths = {'E0':hist/'parent.pt', 'D_E':ROOT/config['parent'], 'P_E':hist/'P_E/checkpoint.pt'}
    records, grad_records, arrays = {}, {}, {}
    counts = {'forward_solves':0, 'adjoint_solves':0}
    for role,path in paths.items():
        exp = make_exp(config, path, data, device)
        _, values = exp.fixed(pools['lbfgs'],cal,coefficients(1.))
        records[role] = {'values':values,'statistics':exp.statistics()}
        add_counts(counts,exp.statistics())
        print(json.dumps({'event':'FIXED_TRAIN_POOL_COMPARISON','role':role,'values':values}),flush=True)
    for role in ('E0','D_E'):
        exp = make_exp(config, paths[role], data, device)
        names, tmask, pmask = [], [], []
        for name,p in exp.model.named_parameters():
            if p.requires_grad:
                names.append({'name':name,'shape':list(p.shape),'numel':p.numel()})
                tmask.extend([name.startswith('heads.temperature.')]*p.numel())
                pmask.extend([name.startswith('heads.phase.')]*p.numel())
        masks = {'all':np.ones(sum(p.numel() for p in exp.parameters),dtype=bool),
                 'T_including_adapter':np.array(tmask), 'phase':np.array(pmask)}
        vectors, blocks = {}, {}
        for block in BLOCKS:
            exp.model.zero_grad(set_to_none=True)
            _, values = exp.fixed(pools['calibration'],cal,{block:1.},backward=True)
            v = vector(exp)
            if not np.isfinite(v).all(): raise FloatingPointError('nonfinite reduced block gradient')
            vectors[block] = v
            arrays[role+'__'+block] = v
            blocks[block] = values
        grad_records[role] = {'blocks':blocks,'parameter_layout':names,
            'by_head':vector_summary(vectors,masks),'statistics':exp.statistics()}
        add_counts(counts,exp.statistics())
        print(json.dumps({'event':'COMPLETE_FIRST_ORDER_BLOCKS','role':role,
                         'norms':grad_records[role]['by_head']['all']['norms']}),flush=True)
    go,gb = arrays['D_E__observation'], arrays['D_E__boundary']
    gf = arrays['D_E__thermal']+arrays['D_E__phase']
    G = float(np.hypot(np.linalg.norm(go),np.linalg.norm(gb)))
    nf = float(np.linalg.norm(gf))
    identifiable = bool(np.isfinite([G,nf]).all() and min(G,nf)>config['gradient_identifiability_floor'])
    ratio = nf/G if identifiable else None
    raw = config['kappa_target']/ratio if identifiable and ratio<config['kappa_target'] else 1.
    kappa = min(config['kappa_max'],raw)
    enabled = bool(identifiable and ratio<config['kappa_target'] and kappa>1.+1e-8)
    selection = {'identifiable':identifiable,'G':G,'norm_gF':nf,'ratio':ratio,
                 'unclipped_kappa':raw,'kappa':kappa,'cap_hit':raw>config['kappa_max'],
                 'run_P_kappa':enabled,'selection_information':'original calibration pool only; no reference',
                 'local_gradient_is_not_trajectory_causality':True}
    exp = make_exp(config,paths['D_E'],data,device)
    def nonzero(ts):
        return sum(float(exp.model.physics.waveform(torch.tensor(t,dtype=torch.float64)))!=0. for t in ts)
    obs_times=set(exp.obs.groups())
    p_times=obs_times|set(pools['lbfgs']['times'])
    per_eval = {'D_C':nonzero(obs_times),'P1':nonzero(p_times)}
    if enabled: per_eval['P_kappa']=per_eval['P1']
    common_limit=min(config['lbfgs_evaluations'],config['training_solve_cap']//sum(per_eval.values()))
    config.update(roles=list(per_eval),resolved_lbfgs_evaluations=common_limit,kappa=kappa,
                  solve_budget_resolution={'per_evaluation_nonzero_solves':per_eval,
                    'common_evaluation_limit':common_limit,
                    'maximum_forward_and_adjoint_each':common_limit*sum(per_eval.values()),
                    'reason':'simultaneous per-arm 300 and total 30000 caps; equal evaluation caps, not equal compute'})
    if max(counts.values())>config['diagnosis_solve_cap']: raise RuntimeError('diagnostic solve cap')
    save_json(root/'frozen-config.json',config)
    shutil.copyfile(ROOT/config['parent'],root/'parent.pt')
    oldaudit=read(hist/'fixed-endpoint-unlabeled-audit.json')
    result={'status':'ONE_PASS_REFERENCE_BLIND_DIAGNOSIS','created_utc':now(),
            'fixed_train_pool':records,'inherited_audit':oldaudit,
            'block_gradients':grad_records,'selection':selection,'counts':counts,
            'gradient_scans':8,'optimizer_updates':0,'reference_read':False,
            'solve_budget_resolution':config['solve_budget_resolution']}
    np.savez_compressed(root/'full-block-gradients.npz',**arrays)
    save_json(root/'diagnosis.json',result)
    print(json.dumps({'event':'DIAGNOSIS_FROZEN','selection':selection,'budget':config['solve_budget_resolution'],'counts':counts}),flush=True)
    return config


def train(root, role, config, device):
    folder=root/role
    folder.mkdir(exist_ok=False)
    data=SparseData(ROOT/config['sparse'])
    exp=make_exp(config,root/'parent.pt',data,device)
    cal=read(root/'calibration.json')
    pool=deserialize_pool(read(root/'lbfgs-pool.json'))
    kappa={'D_C':0.,'P1':1.,'P_kappa':config['kappa']}[role]
    cap=config['resolved_lbfgs_evaluations']
    cost=config['solve_budget_resolution']['per_evaluation_nonzero_solves'][role]
    with (folder/'lbfgs-telemetry.jsonl').open('x',encoding='utf-8') as log:
        def record(item):
            item['statistics']=exp.statistics()
            log.write(json.dumps(item,allow_nan=False)+'\n');log.flush()
            if item['accepted_steps']==1 or item['accepted_steps']%10==0:
                print(json.dumps({'role':role,'evaluations':item['evaluations'],'loss':item['loss']}),flush=True)
        def objective():
            if exp.layer.backend.counts.forward_solves+cost>cap*cost:
                raise RuntimeError('frozen per-arm solve budget would be exceeded')
            return exp.fixed(pool,cal,coefficients(kappa),backward=True,counter='complete')[0]
        result,optimizer=continued_lbfgs(exp.parameters,objective,cap,record)
    exp.role=role
    save_checkpoint(folder/'checkpoint.pt',exp,optimizer,config,cal,0,
                    optimizer_phase='fresh L-BFGS',lbfgs_result=result,remaining_pde_multiplier=kappa)
    terminal={'status':'VALID_FIXED_ENDPOINT','role':role,'adam_updates':0,'lbfgs':result,
              'statistics':exp.statistics(),'kappa':kappa,'reference_read':False,'device':device}
    save_json(folder/'terminal.json',terminal)
    print(json.dumps({'event':'FIXED_ENDPOINT','role':role,'lbfgs':result,'solves':exp.statistics()['electrical']}),flush=True)


def endpoint_audit(root,config,device):
    counts=dict(read(root/'diagnosis.json')['counts'])
    data=SparseData(ROOT/config['sparse'])
    cal=read(root/'calibration.json')
    records={}
    for role in config['roles']:
        exp=make_exp(config,root/role/'checkpoint.pt',data,device)
        records[role]={}
        for name in ('lbfgs','audit'):
            pool=deserialize_pool(read(root/(name+'-pool.json')))
            _,values=exp.fixed(pool,cal,coefficients(1.))
            kappa={'D_C':0.,'P1':1.,'P_kappa':config['kappa']}[role]
            values['actual_role_functional']=values['C']+kappa*values['F']
            records[role][name]=values
        records[role]['statistics']=exp.statistics()
        add_counts(counts,exp.statistics())
    if max(counts.values())>config['diagnosis_solve_cap']: raise RuntimeError('diagnostic solve cap exceeded')
    save_json(root/'fixed-endpoint-common-audit.json',{'records':records,'diagnostic_counts_including_pretraining':counts,
              'optimizer_updates':0,'parameter_gradient_scans':0,'reference_read':False})
    print(json.dumps({'event':'ENDPOINT_COMMON_AUDIT','counts':counts}),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['diagnose','train','audit','predict','all'])
    parser.add_argument('--root',type=Path,default=RUN)
    parser.add_argument('--config',type=Path,default=CONFIG)
    parser.add_argument('--device',default='cpu')
    parser.add_argument('--role')
    args=parser.parse_args()
    config=read(args.config if args.action in ('diagnose','all') else args.root/'frozen-config.json')
    torch.set_num_threads(config['cpu_threads'])
    if args.action in ('diagnose','all'): config=diagnose(args.root,config,args.device)
    if args.action in ('train','all'):
        for role in ([args.role] if args.role else config['roles']): train(args.root,role,config,args.device)
    if args.action in ('audit','all'): endpoint_audit(args.root,config,args.device)
    if args.action in ('predict','all'):
        from .phk_v23_lf11_elimination_predict import predict
        for role in ([args.role] if args.role else config['roles']): predict(args.root,role,args.device)
    if args.action=='all':
        save_json(args.root/'training-and-own-inference-complete.json',{'completed':True,'reference_read':False,'created_utc':now()})


if __name__=='__main__': main()
