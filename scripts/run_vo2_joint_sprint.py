"""Prepare legal inputs, qualify true gradients, then run the fixed three arms."""
import os
for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='4'
from pathlib import Path
import argparse,hashlib,json,sys,time
from datetime import datetime,timezone
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from pinn_pcm_sci.vo2_joint_reconstruction import RUN,PAPER,P,JointObjective,save,read,trap,train,stamp,check_resources
from pinn_pcm_sci.vo2_joint_history import replay_with_history,resistance_from_temperature,selected_event_signature
from pinn_pcm_sci.vo2_joint_rc import rc_forward,rc_voltage
torch.set_num_threads(4)

def prepare():
    RUN.mkdir(parents=True,exist_ok=True)
    if (RUN/'input.npz').exists():raise RuntimeError('Frozen legal input already exists')
    cfg=read(PAPER/'config.json')
    with np.load(ROOT/'paper/paper_revision_20260928_conditional_thermal/arrays/pair_excitation-0p5ns/thermal.npz') as x:
        t=x['time'];T0=x['T_P']
    with np.load(ROOT/'paper/paper_revision_20260928_circuit_comparison/scoring-subset/inputs/pair_excitation-0p5ns.npz') as x:
        ot=x['observation_time'];ov=x['observation_voltage']
    assert len(t)==40001 and len(ot)==197 and np.array_equal(T0[0],[325.,325.])
    history=replay_with_history(T0);v0=rc_forward(history['resistance'],cfg['dt_s'],P.C,P.RL,np.array(cfg['Vin_V']),0.)
    np.savez_compressed(RUN/'input.npz',time=t,T0=T0,v0=v0,observation_time=ot,observation_voltage=ov,observation_weights=trap(ot))
    save(RUN/'config.json',cfg)
    save(RUN/'input-provenance.json',dict(task_id=cfg['task_id'],created_utc=stamp(),
        fields=['time','T0','v0','observation_time','observation_voltage','observation_weights'],
        source_T_R_g_H_read=False,full_source_current_read=False,common_RC_initialization_calls=1,
        T0_source=cfg['shared_temperature'],T0_representation='exact same saved native array for all three',
        file_sha256=hashlib.sha256((RUN/'input.npz').read_bytes()).hexdigest(),
        no_new_conditional_heat_response=True))
    print('Legal shared inputs locked; source truth fields not loaded')

def admission(device):
    cfg=read(RUN/'config.json');began=time.perf_counter();results=[];fields=[]
    if (RUN/'admission.json').exists():raise RuntimeError('Admission already recorded; no repeated diagnostic sweep')
    for role in ['N_dyn','F_dyn','S_dyn']:
        exp=JointObjective(role,29,device);check_resources(device)
        start=time.perf_counter();exp.model.zero_grad(set_to_none=True)
        loss,parts=exp.loss();duration=time.perf_counter()-start
        grads=torch.cat([p.grad.detach().flatten() for p in exp.model.parameters()])
        with torch.no_grad():T,R,v=exp.fields()
        fields.append((T.cpu().numpy(),v.cpu().numpy()))
        # Direction tests use the full physical objective with a native T
        # perturbation. F also perturbs v; neural chain is checked separately.
        Tbase=T.detach().clone().requires_grad_(True);vbase=v.detach().clone()
        Rbase=resistance_from_temperature(Tbase)
        if role=='F_dyn':vbase=vbase.requires_grad_(True);vr=vbase
        else:vr=rc_voltage(Rbase,exp.h,P.C,P.RL,exp.Vin,0.)
        val=exp.components(Tbase,Rbase,vr)[0];val.backward()
        t=exp.data['time']/exp.data['time'][-1]
        direction=np.column_stack((t*np.sin(2*np.pi*t),t*np.cos(3*np.pi*t)))
        d=torch.tensor(direction,dtype=torch.float64,device=device)
        direction_v=.1*d if role=='F_dyn' else None
        analytic=float((Tbase.grad*d).sum())
        if role=='F_dyn':analytic+=float((vbase.grad*direction_v).sum())
        signature=selected_event_signature(Tbase.detach().cpu().numpy())
        derivatives=[]
        for eps in cfg['gradient_admission']['finite_steps_K']:
            values=[];same=True
            for sign in [-1.,1.]:
                Tp=Tbase.detach()+sign*eps*d
                same=bool(same and selected_event_signature(Tp.cpu().numpy())==signature)
                Rp=resistance_from_temperature(Tp)
                vp=vbase.detach()+sign*eps*direction_v if role=='F_dyn' else rc_voltage(Rp,exp.h,P.C,P.RL,exp.Vin,0.)
                values.append(float(exp.components(Tp,Rp,vp)[0]))
            fd=(values[1]-values[0])/(2*eps);err=abs(fd-analytic)
            tol=cfg['gradient_admission']['absolute_tolerance']+cfg['gradient_admission']['relative_tolerance']*abs(analytic)
            derivatives.append(dict(eps_K=eps,same_full_event_signature=same,analytic=analytic,finite_difference=fd,absolute_error=err,tolerance=tol,passed=bool(same and err<=tol)))
        fixed=[x for x in derivatives if x['same_full_event_signature']]
        derivative_pass=len(fixed)>=2 and all(x['passed'] for x in fixed[-2:])
        # The network/spline path must receive nonzero finite gradients.
        result=dict(role=role,zero_loss=float(loss),parts={k:float(v) for k,v in parts.items()},
            full_objective_gradient_seconds=duration,parameter_count=sum(p.numel() for p in exp.model.parameters()),
            gradient_l2=float(torch.linalg.vector_norm(grads)),gradients_finite=bool(torch.isfinite(grads).all()),
            initial_T_max_difference_K=float(np.max(abs(fields[-1][0]-exp.data['T0']))),
            initial_v_max_difference_V=float(np.max(abs(fields[-1][1]-exp.data['v0']))),
            directional_derivatives=derivatives,derivative_pass=derivative_pass,
            GPU_peak_allocated_bytes=torch.cuda.max_memory_allocated(device) if str(device).startswith('cuda') else 0)
        result['passed']=bool(derivative_pass and result['gradients_finite'] and result['initial_T_max_difference_K']==0 and result['initial_v_max_difference_V']<1e-12)
        results.append(result);print(json.dumps(result),flush=True)
        del exp,T,R,v,Tbase,Rbase,vr,val
    identical=all(np.array_equal(fields[0][0],x[0]) and np.array_equal(fields[0][1],x[1]) for x in fields[1:])
    allowed=datetime.now(timezone.utc)<datetime.fromisoformat(cfg['admission_deadline_utc'])
    report=dict(task_id=cfg['task_id'],passed=all(x['passed'] for x in results) and identical and allowed,
        full_zero_fields_identical=identical,within_8h=allowed,roles=results,seconds=time.perf_counter()-began,
        fixed_event_tolerance=cfg['gradient_admission'],absolute_noninferiority_floors=cfg['increment']['absolute_floors'],
        cross_reversal='Separate synthetic test records discontinuous event change; not counted as fixed-event derivative accuracy',
        device=device,created_utc=stamp(),reference_fields_read=False)
    save(RUN/'admission.json',report);return report

def run_seed(seed,device):
    if seed==43:
        if not read(RUN/'seed-29-gate.json')['trigger_seed43']:raise RuntimeError('Second seed not triggered')
    records=[]
    for role in ['N_dyn','F_dyn','S_dyn'] if seed==29 else ['N_dyn','F_dyn']:
        records.append(train(role,seed,device))
    save(RUN/f'seed-{seed}-locked.json',dict(records=records,locked_utc=stamp(),all_valid=all(x['status']=='VALID_COMPLETE' for x in records)))
    return records
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','admission','train']);parser.add_argument('--device',default='cuda:0');parser.add_argument('--seed',type=int,default=29);args=parser.parse_args()
    if args.mode=='prepare':prepare()
    elif args.mode=='admission':admission(args.device)
    else:run_seed(args.seed,args.device)
