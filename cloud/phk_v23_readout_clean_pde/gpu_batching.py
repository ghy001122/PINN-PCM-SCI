"""One targeted GPU batching check; no reference or linear system is read."""
import json
import torch
from pinn_pcm_sci.phk_v23_readout_clean_pde import approved,read,load_record
from pinn_pcm_sci.phk_v23_lf11_elimination_physics import grid_for,coordinates,fields
from pinn_pcm_sci.phk_v23_lf11 import save_json

cfg,run=approved();torch.set_num_threads(4)
records=[]
for item in read(run/'input-manifest.json')['objects']:
    if item['role']=='B_E':continue
    _,model=load_record(item,'cuda:0')
    grid=grid_for(model.physics,240,120)
    q=coordinates(grid,.175,device='cuda:0')[[0,300,1500,6500,12300,20500,28799]]
    with torch.no_grad():
        a=fields(model,q);pieces=[fields(model,q[j:j+2]) for j in range(0,len(q),2)]
    errors={}
    for name in ('temperature','phase'):
        b=torch.cat([v[name] for v in pieces])
        torch.testing.assert_close(a[name],b,rtol=2e-12,atol=2e-14)
        errors[name]=float(abs(a[name]-b).max())
    records.append(dict(id=item['id'],max_difference=errors))
save_json(run/'gpu-batching-check.json',dict(status='PASS',records=records,linear_solves=0,
    optimizer_updates=0,reference_read=False,device='cuda:0'))
print(json.dumps(dict(status='GPU_BATCHING_PASS',models=len(records))))
