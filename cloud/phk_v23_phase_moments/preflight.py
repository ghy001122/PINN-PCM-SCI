"""Confirm the staged dependency closure and four-point CUDA phase identity."""
import json
from pathlib import Path
import platform
import torch
import scipy
import numpy as np
from pinn_pcm_sci.phk_v23_phase_moments_run import parent_model,read,CONFIG
from pinn_pcm_sci.phk_v23_phase_moments import phase_quantities
from pinn_pcm_sci.phk_v23_lf11 import save_json,ROOT
from pinn_pcm_sci.phk_v23_b1_observations import VisibleData

cfg=read(CONFIG);torch.set_num_threads(cfg['cpu_threads'])
assert platform.python_version_tuple()[:2]==('3','11') and torch.cuda.is_available()
model,_=parent_model(cfg);model=model.to('cuda:0')
data=VisibleData(ROOT/cfg['sparse'])
assert len(data.arrays['phase_values'])<len(data.coordinates)
q=torch.tensor([[-.2,.12,.1],[.1,.18,.3],[.3,.2,1.2],[0.,.3,1.6]],dtype=torch.float64,device='cuda:0',requires_grad=True)
r=phase_quantities(model,q)
torch.testing.assert_close(r['rphi'],r['s']*r['rpsi'],rtol=2e-10,atol=1e-12)
result=dict(status='ISOLATED_GPU_PREFLIGHT_VALID',python=platform.python_version(),torch=torch.__version__,
    scipy=scipy.__version__,numpy=np.__version__,gpu=torch.cuda.get_device_name(0),reference_arrays=0,
    optimizer_updates=0,electrical_solves=0,phase_probe_positions=4)
save_json(ROOT/cfg['run']/'gpu-preflight.json',result)
print(json.dumps(result))
