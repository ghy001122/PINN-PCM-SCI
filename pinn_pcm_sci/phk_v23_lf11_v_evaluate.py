"""Post-training nominal evaluation for the single accepted V endpoint."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import torch
from .phk_benchmark import PhkControl
from .phk_v22r_evaluator import load_reference
from .phk_v23_lf11 import ROOT,SparseData,save_json,now
from .phk_v23_lf11_evaluation import metrics,comparison
from .phk_v23_lf11_followup_evaluate import add_power_metrics
from .phk_v23_lf11_followup_fit import fit_model
from .phk_v23_lf11_readout import interpolate_sparse
from .phk_v23_lf11_electric_trace_audit import normalized_voltage_contact
from .phk_v23_lf11_v_continue import RUN,CONFIG

def evaluate(root=RUN):
    root=Path(root)
    if (root/"evaluation.json").exists():raise FileExistsError("reuse fixed endpoint evaluation")
    proof=json.loads((root/"compute-closure.json").read_text())
    if not proof["training_complete"] or not proof["compute_stopped_before_reference_read"]:raise ValueError("training not closed")
    contract=json.loads(CONFIG.read_text())
    ckpt=torch.load(root/"v_continue/checkpoint.pt",map_location="cpu",weights_only=False)
    model=fit_model(ckpt["config"],ckpt["model_state_dict"],ckpt["temperature_adapter"]);torch.set_num_threads(4)
    config=ckpt["config"]
    with np.load(root/"v_continue/prediction.npz",allow_pickle=False) as f:
        x,z,time=[f[k] for k in ("x","z","time")]
        fields={k:f[k] for k in ("potential","temperature","phase")}
    reference,identity=load_reference(PhkControl.FULL)
    if not (np.array_equal(x,reference.grid.x_centers) and np.array_equal(z,reference.grid.z_centers) and np.array_equal(time,reference.time)):
        raise ValueError("prediction axes differ from frozen reference")
    old_root=ROOT/"outputs/runs/20260911-lf11-followup-fit-electric-block"
    previous=json.loads((old_root/"evaluation.json").read_text())
    if identity!=previous["reference_sha256"]:raise ValueError("different nominal reference")
    records=previous["records"]
    traces={}
    with np.load(old_root/"evaluation-traces.npz",allow_pickle=False) as f:
        for name in records:
            prefix=name+"__";traces[name]={k[len(prefix):]:f[k] for k in f.files if k.startswith(prefix)}
    record,trace=metrics(fields,reference,model.physics,config)
    add_power_metrics(record,trace,time,reference.top_current,reference.joule_power)
    record["origin"]="NEW_V_ONLY_FIXED_ENDPOINT"
    records["V_continued"]=record;traces["V_continued"]=trace
    for key in ("S","Ephi","ET","phase_max"):
        if record["metrics"][key]!=records["S1_fixed_fit"]["metrics"][key]:raise ValueError("non-V metric changed")
    if record["cycles"]!=records["S1_fixed_fit"]["cycles"]:raise ValueError("phase events changed")
    # The new baseline was frozen and its observation preservation checked before
    # reference fields were opened. Its independent T/phase interpolation is old.
    data=SparseData(ROOT/contract["sparse"])
    direct=interpolate_sparse(data,x,z,time,model.physics,"B_logit")
    direct["potential"]=normalized_voltage_contact(data,x,z,time,model.physics)
    r,tr=metrics(direct,reference,model.physics,config)
    add_power_metrics(r,tr,time,reference.top_current,reference.joule_power)
    r["origin"]="PREDECLARED_SAME_OBSERVATION_CONTACT_COMPLETE_BASELINE"
    for key in ("S","Ephi","ET","phase_max"):
        if r["metrics"][key]!=records["B_logit_waveform"]["metrics"][key]:raise ValueError("contact control changed T/phase metric")
    records["B_logit_waveform_contact"]=r;traces["B_logit_waveform_contact"]=tr
    np.savez_compressed(root/"contact-prediction.npz",x=x,z=z,time=time,**direct)
    # Check that the exact diagnostic decomposition is the official readout,
    # including the previously saved parent. No diagnostic subtraction is scored.
    for label,name in (("pre","S1_fixed_fit"),("post","V_continued")):
        with np.load(root/"electric_audit"/(label+".npz"),allow_pickle=False) as a:
            for key in ("top_current","bottom_current","joule_power","input_power"):
                np.testing.assert_allclose(a[key],traces[name][key],rtol=1e-13,atol=1e-13)
    evidence=json.loads((root/"electric_audit/summary.json").read_text())
    pre=evidence["pre"]["summaries"];post=evidence["post"]["summaries"]
    def integral(s,k):return s[k]["signed_integral"]
    current_drop=integral(pre,"bottom_current")-integral(post,"bottom_current")
    derived={"integrated_bottom_current_decrease":current_drop,
             "signed_trace_fraction_of_integrated_current_decrease":(integral(pre,"I_trace")-integral(post,"I_trace"))/current_drop,
             "post_trace_fraction_of_integrated_current":integral(post,"I_trace")/integral(post,"bottom_current"),
             "pre_trace_fraction_of_integrated_current":integral(pre,"I_trace")/integral(pre,"bottom_current"),
             "internal_Joule_integral_change":integral(post,"P_internal")-integral(pre,"P_internal"),
             "bottom_Joule_integral_change":integral(post,"P_bottom")-integral(pre,"P_bottom"),
             "total_Joule_integral_change":integral(post,"joule_power")-integral(pre,"joule_power"),
             "interpretation":"signed algebraic integrated quantities; not independent RMS shares or a universal mechanism"}
    result={"schema_id":"lf11-v-continuation-evaluation-v1","recorded_utc":now(),
            "reference_sha256":identity,"records":records,"derived_electric_attribution":derived,
            "unrun_branches":proof["unrun_branches"],"new_PINN_matched_comparison_executed":False,
            "T_phase_and_cycle_metrics_exactly_preserved":True,
            "contact_control_T_phase_metrics_exactly_preserved":True,
            "scope":"single nominal development endpoint; no new PINN comparison or independent-seed/OOD evidence"}
    save_json(root/"evaluation.json",result)
    np.savez_compressed(root/"evaluation-traces.npz",time=time,reference_current=reference.top_current,reference_power=reference.joule_power,
                        **{name+"__"+key:value for name,tr in traces.items() for key,value in tr.items()})
    print(json.dumps({"evaluation_complete":True,"new_metrics":{n:records[n]["metrics"] for n in ("S1_fixed_fit","V_continued","B_logit_waveform","B_logit_waveform_contact")},
                      "derived":derived},indent=2),flush=True)
    return result

if __name__=="__main__": evaluate()

