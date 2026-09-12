"""Fixed-function electric audit and contact-complete, zero-training baseline.

No reference fields or PDE solve are used. FV current is never replaced by an
AD flux or by a trace-subtracted quantity.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import torch
from scipy.interpolate import PchipInterpolator, RegularGridInterpolator, interp1d
from .phk_v23_lf11 import ROOT, SparseData, tensor, now, save_json
from .phk_v23_lf11_followup_fit import fit_model, head_field
from .phk_v23_lf11_readout import make_grid
from .phk_v23_lf11_v_continue import RUN, CONFIG

def normalized_voltage_contact(data, x, z, times, physics):
    """Same waveform interpolation; add known contact endpoints only."""
    a=data.arrays
    source_t=a["time"]; source_u=physics.waveform(tensor(source_t)).numpy()
    target_u=physics.waveform(tensor(times)).numpy()
    source=data.targets[:,0].reshape(len(source_t),len(a["z"]),len(a["x"]))
    response=np.zeros((len(times),len(a["z"]),len(a["x"])))
    for cycle in range(2):
        visible=(source_u>1e-12)&(source_t>=cycle*physics.period)&(source_t<(cycle+1)*physics.period)
        target=(target_u>1e-12)&(times>=cycle*physics.period)&(times<(cycle+1)*physics.period)
        ts=source_t[visible]
        if len(ts)<2: raise ValueError("insufficient positive-voltage samples")
        beta=source[visible]/source_u[visible,None,None]
        response[target]=PchipInterpolator(ts,beta,axis=0)(np.clip(times[target],ts[0],ts[-1]))
    response=np.pad(response,((0,0),(1,1),(1,1)),mode="edge")
    sx=np.r_[physics.x_min,a["x"],physics.x_max]
    sz=np.r_[physics.z_min,a["z"],physics.z_max]
    response[:,-1,:]=1
    response[:,0,np.abs(sx)<=physics.heater_half_width]=0
    new_x=np.unique(np.r_[sx,-physics.heater_half_width,physics.heater_half_width])
    response=interp1d(sx,response,axis=2,kind="linear",bounds_error=True)(new_x)
    response[:,0,np.abs(new_x)<=physics.heater_half_width]=0
    xx,zz=np.meshgrid(x,z,indexing="xy")
    query=np.column_stack([zz.ravel(),xx.ravel()])
    beta=np.stack([RegularGridInterpolator((sz,new_x),v,bounds_error=True)(query) for v in response])
    return target_u[:,None]*np.clip(beta,0,1)

def conductivity(t, phase, physics):
    return np.exp(physics.conductivity_temperature_gain*t+
                  np.log(physics.conductivity_phase_ratio)*phase**2*(3-2*phase))

def bottom_decomposition(v, boundary, sigma, grid, voltage, overlap):
    """Exact signed decomposition, using the identical FV conductances."""
    bottom=np.flatnonzero(overlap>0)
    top=np.arange((grid.nz-1)*grid.nx,grid.cell_count)
    c=2*sigma[:,bottom]*overlap[bottom]/grid.dz
    value=v[:,bottom]; drop=value-boundary
    trace_current=np.sum(c*boundary,axis=1)
    drop_current=np.sum(c*drop,axis=1)
    pb_trace=np.sum(c*boundary**2,axis=1)
    pb_cross=2*np.sum(c*boundary*drop,axis=1)
    pb_drop=np.sum(c*drop**2,axis=1)
    first,second=grid.internal_first,grid.internal_second
    half,area=grid.internal_half_distance,grid.internal_area
    internal=[]
    for vi,si in zip(v,sigma,strict=True):
        g=1/(half/(si[first]*area)+half/(si[second]*area))
        internal.append(np.sum(g*(vi[first]-vi[second])**2))
    gt=2*sigma[:,top]*grid.dx/grid.dz
    top_drop=voltage[:,None]-v[:,top]
    ptop=np.sum(gt*top_drop**2,axis=1)
    pbottom=np.sum(c*value**2,axis=1)
    itop=np.sum(gt*top_drop,axis=1)
    ibottom=np.sum(c*value,axis=1)
    pint=np.asarray(internal)
    return dict(bottom_current=ibottom,I_trace=trace_current,I_drop=drop_current,
                P_bottom=pbottom,P_trace=pb_trace,P_cross=pb_cross,P_drop=pb_drop,
                P_internal=pint,P_top=ptop,joule_power=pint+ptop+pbottom,
                top_current=itop,input_power=voltage*itop,
                current_identity_error=ibottom-trace_current-drop_current,
                power_identity_error=pbottom-pb_trace-pb_cross-pb_drop)

def audit_one(model, fields, x, z, times, folder, label):
    grid=make_grid(x,z,model.physics)
    overlap=grid.bottom_overlap(model.physics.heater_width_fraction)
    bottom=np.flatnonzero(overlap>0); bx=grid.cell_x[bottom]
    tt,xx=np.meshgrid(times,bx,indexing="ij")
    coords=np.column_stack([xx.ravel(),np.zeros(xx.size),tt.ravel()])
    boundary=[]; derivatives=[]
    for lo in range(0,len(coords),4096):
        q=tensor(coords[lo:lo+4096]).requires_grad_(True)
        f=model(q)
        derivative=torch.autograd.grad(f[:,0].sum(),q)[0][:,1]
        boundary.append(f.detach().numpy()); derivatives.append(derivative.detach().numpy())
    f=np.concatenate(boundary).reshape(len(times),len(bx),3)
    dz=np.concatenate(derivatives).reshape(len(times),len(bx))
    sigma=conductivity(fields["temperature"],fields["phase"],model.physics)
    sig_b=conductivity(f[:,:,1],f[:,:,2],model.physics)
    u=model.physics.waveform(tensor(times)).numpy()
    arrays=bottom_decomposition(fields["potential"],f[:,:,0],sigma,grid,u,overlap)
    arrays.update(heater_trace=f[:,:,0],boundary_dV_dn=-dz,
                  boundary_sigma=sig_b,cell_sigma=sigma[:,bottom],
                  AD_bottom_current=np.sum(sig_b*dz*overlap[bottom],axis=1),
                  AD_cell_sigma_current=np.sum(sigma[:,bottom]*dz*overlap[bottom],axis=1))
    edge=np.zeros(len(bottom),dtype=bool);edge[:2]=True;edge[-2:]=True
    for role,mask in (("edge",edge),("interior",~edge)):
        c=2*sigma[:,bottom][:,mask]*overlap[bottom][mask]/grid.dz
        arrays["I_trace_"+role]=np.sum(c*f[:,mask,0],axis=1)
        arrays["I_drop_"+role]=np.sum(c*(fields["potential"][:,bottom][:,mask]-f[:,mask,0]),axis=1)
        arrays["AD_bottom_"+role]=np.sum(sig_b[:,mask]*dz[:,mask]*overlap[bottom][mask],axis=1)
    def rms(y): return float(np.sqrt(np.trapezoid(y*y,times)/(times[-1]-times[0])))
    summaries={k:{"signed_integral":float(np.trapezoid(v,times)),"rms":rms(v)}
               for k,v in arrays.items() if v.ndim==1}
    if max(np.max(np.abs(arrays[k])) for k in ("current_identity_error","power_identity_error"))>1e-10:
        raise ValueError("electric decomposition identity failed")
    np.savez_compressed(folder/(label+".npz"),time=times,heater_x=bx,contact_edge=edge,**arrays)
    result={"role":label,"recorded_utc":now(),"reference_read":False,"PDE_solve":False,
            "summaries":summaries,"heater_trace_rms":rms(np.sqrt(np.average(f[:,:,0]**2,axis=1,weights=overlap[bottom]))),
            "interpretation":"signed identities; RMS components are not additive shares; AD is own-model flux, not truth",
            "boundary_trace_from_own_model":True,"contact_edge_rule":"first/last two positive-overlap faces"}
    save_json(folder/(label+".json"),result)
    return result

def run(root=RUN):
    folder=root/"electric_audit";folder.mkdir(exist_ok=False)
    contract=json.loads(CONFIG.read_text(encoding="utf-8"))
    result=json.loads((root/"v_continue/result.json").read_text(encoding="utf-8"))
    if not result["non_V_state_exactly_preserved"]: raise ValueError("cannot reuse non-V fields")
    torch.set_num_threads(4)
    data=SparseData(ROOT/contract["sparse"])
    endpoint=torch.load(ROOT/contract["parent"],map_location="cpu",weights_only=False)
    after=torch.load(root/"v_continue/checkpoint.pt",map_location="cpu",weights_only=False)
    models=[fit_model(e["config"],e["model_state_dict"],e["temperature_adapter"]) for e in (endpoint,after)]
    with np.load(ROOT/"outputs/runs/20260911-lf11-followup-fit-electric-block/s1/fixed-prediction.npz",allow_pickle=False) as f:
        x,z,times=[f[k] for k in ("x","z","time")]
        fields={k:f[k] for k in ("potential","temperature","phase")}
    # Reuse predictions of the identical, frozen S1 function, never teacher fields.
    pre=audit_one(models[0],fields,x,z,times,folder,"pre")
    xx,zz=np.meshgrid(x,z,indexing="xy"); space=np.column_stack([xx.ravel(),zz.ravel()])
    potential=np.empty_like(fields["potential"])
    with torch.no_grad():
        for i,t in enumerate(times):
            q=np.column_stack([space,np.full(len(space),t)])
            for lo in range(0,len(q),8192):
                potential[i,lo:lo+8192]=head_field(models[1],"potential",tensor(q[lo:lo+8192])).numpy()
            if i%200==0: print(json.dumps({"own_V_prediction_index":i}),flush=True)
    fields["potential"]=potential
    np.savez_compressed(root/"v_continue/prediction.npz",x=x,z=z,time=times,**fields)
    post=audit_one(models[1],fields,x,z,times,folder,"post")
    predicted=normalized_voltage_contact(data,data.arrays["x"],data.arrays["z"],data.arrays["time"],models[1].physics)
    preservation=float(np.max(np.abs(predicted-data.targets[:,0].reshape(predicted.shape))))
    h=models[1].physics.heater_half_width
    test_x=np.linspace(-h,h,73)
    boundary=normalized_voltage_contact(data,test_x,np.array([0.]),data.arrays["time"],models[1].physics)
    if preservation>1e-12 or np.max(np.abs(boundary))>1e-14: raise ValueError("contact baseline invariance failed")
    save_json(root/"contact-baseline-check.json",dict(rule="B_logit_waveform_contact",
        visible_max_abs=preservation,entire_heater_check_max_abs=float(np.max(np.abs(boundary))),
        new_labels=0,training_updates=0,PDE_solve=False,insulation_exact=False,temperature_phase_changed=False))
    save_json(folder/"summary.json",dict(pre=pre,post=post,fixed_T_phase_conductivity=True))
    print(json.dumps({"electric_audit_complete":True,"pre":pre["summaries"],"post":post["summaries"]}),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=RUN)
    run(p.parse_args().root)
