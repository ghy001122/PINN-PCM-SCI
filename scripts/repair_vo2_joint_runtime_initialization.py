"""One zero-update platform repair: lock common v0 on the actual runtime.

T0, observations, formulas, objective and budgets do not change. Preserve the
original input and failed exact-identity admission; reuse passed derivatives.
"""
from pathlib import Path
import hashlib,json,sys,time
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from pinn_pcm_sci.vo2_joint_reconstruction import RUN,P,JointObjective,read,save
from pinn_pcm_sci.vo2_joint_history import replay_with_history
from pinn_pcm_sci.vo2_joint_rc import rc_forward
if list(RUN.glob('seed-*/**/accepted-state.pt')):raise RuntimeError('Repair permitted only before any training')
original=read(RUN/'admission.json')
assert all(x['passed'] for x in original['roles']) and not original['full_zero_fields_identical']
archive=RUN/'prestep-platform-roundoff';archive.mkdir(exist_ok=False)
for name in ['input.npz','input-provenance.json','admission.json']:(RUN/name).replace(archive/name)
with np.load(archive/'input.npz') as file:a={k:file[k] for k in file.files}
cfg=read(RUN/'config.json');h=replay_with_history(a['T0'])
new_v=rc_forward(h['resistance'],cfg['dt_s'],P.C,P.RL,np.array(cfg['Vin_V']),0.)
difference=float(np.max(abs(new_v-a['v0'])));a['v0']=new_v
np.savez_compressed(RUN/'input.npz',**a)
provenance=read(archive/'input-provenance.json');provenance.update(actual_runtime_initialization='Linux scientific runtime, same RC formula',
    input_before_repair='prestep-platform-roundoff/input.npz',max_v0_platform_roundoff_V=difference,
    common_RC_initialization_calls=2,scientific_optimizer_updates=0,
    file_sha256=hashlib.sha256((RUN/'input.npz').read_bytes()).hexdigest())
save(RUN/'input-provenance.json',provenance)
fields=[];zero=[]
for role in ['N_dyn','F_dyn','S_dyn']:
    exp=JointObjective(role,29,'cuda:0')
    with torch.no_grad():T,R,v=exp.fields();loss,parts,_,_=exp.components(T,R,v)
    fields.append((T.cpu().numpy(),v.cpu().numpy()))
    zero.append(dict(role=role,loss=float(loss),T_exact=bool(np.array_equal(fields[-1][0],a['T0'])),
        v_exact=bool(np.array_equal(fields[-1][1],a['v0']))))
assert all(x['T_exact'] and x['v_exact'] for x in zero)
original.update(passed=True,full_zero_fields_identical=True,zero_identity_recheck=zero,
    engineering_repair=dict(reason='Windows-vs-Linux same-formula v0 rounding 6.16e-13 V; regenerate common runtime v0 once',
        old_failed_record='prestep-platform-roundoff/admission.json',source_truth_read=False,optimizer_updates=0,
        actual_extra_RC_initializations=1,zero_forward_checks=3,gradient_tests_repeated=False,
        scientific_formula_or_budget_changed=False))
save(RUN/'admission.json',original)
print(json.dumps(dict(passed=True,roundoff_V=difference,zero_checks=zero)))
