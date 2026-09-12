"""Rebuild paper_v26 figures and tables from saved results only."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from .phk_v23_lf11 import ROOT
from .phk_v23_lf11_v_continue import RUN

def render(root=RUN,paper=ROOT/"paper/paper_v26"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    root,paper=Path(root),Path(paper)
    figdir=paper/"figures";tabdir=paper/"tables"
    figdir.mkdir(parents=True,exist_ok=True);tabdir.mkdir(exist_ok=True)
    result=json.loads((root/"evaluation.json").read_text())
    fit=json.loads((root/"v_continue/result.json").read_text())
    records=result["records"]
    history=[json.loads(s) for s in (root/"v_continue/telemetry.jsonl").read_text().splitlines()]
    traces=np.load(root/"evaluation-traces.npz",allow_pickle=False)
    audits={k:np.load(root/"electric_audit"/(k+".npz"),allow_pickle=False) for k in ("pre","post")}
    time=traces["time"]
    plt.rcParams.update({"font.size":9,"axes.spines.top":False,"axes.spines.right":False,"font.family":"DejaVu Sans","savefig.dpi":200})
    names=["S1_fixed_fit","V_continued","B_logit_waveform","B_logit_waveform_contact"]
    labels=["S1 parent","V continued","Waveform","Contact"]
    colors=["#667785","#d85a38","#8c6db0","#188979"]
    def save(fig,name):
        for ext in ("png","pdf"):fig.savefig(figdir/(name+"."+ext))
        plt.close(fig)
    fig,ax=plt.subplots(2,3,figsize=(14,8.2),layout="constrained")
    ev=[1]+[h["evaluations"] for h in history]
    loss=[fit["initial_loss"]]+[h["loss"] for h in history]
    ax[0,0].plot(ev,loss,color=colors[1],lw=1.8)
    ax[0,0].axhline(.005**2/3,color="black",ls="--",lw=1,label="0.5% fit gate")
    ax[0,0].set(xlabel="Actual complete objective / gradient evaluations",ylabel="Fixed weighted V objective",title="A   Bounded V continuation")
    ax[0,0].ticklabel_format(axis="y",style="sci",scilimits=(-5,-5))
    ax[0,0].legend(loc="upper right")
    annotation=(f'{100*fit["before"]["V_normalized_rms"]:.4f}% → '
                f'{100*fit["after"]["V_normalized_rms"]:.4f}% visible RMS\n'
                f'{fit["accepted_steps"]} accepted steps; fit gate '
                +("met" if fit["admission"]["passed"] else "not met"))
    ax[0,0].text(.05,.16,annotation,transform=ax[0,0].transAxes,fontsize=9)
    # These are integrals of signed components, not sums of RMS magnitudes.
    current_keys=["I_trace","I_drop"]
    start=np.zeros(2)
    for key,c,label in zip(current_keys,["#d85a38","#4a82a3"],["Boundary trace","Boundary-to-cell drop"]):
        vals=[np.trapezoid(audits[k][key],time) for k in ("pre","post")]
        ax[0,1].bar([0,1],vals,bottom=start,color=c,label=label,width=.5)
        start+=vals
    ad=[np.trapezoid(audits[k]["AD_bottom_current"],time) for k in ("pre","post")]
    ax[0,1].scatter([0,1],ad,color="black",marker="D",label="Own AD flux integral",zorder=4)
    ax[0,1].set(xticks=[0,1],xticklabels=["S1 parent","V continued"],ylabel="Integrated bottom current",title="B   Exact current decomposition")
    ax[0,1].legend(fontsize=7.5,loc="upper right")
    keys=["P_internal","P_top","P_trace","P_cross","P_drop"]
    cols=["#708a99","#bfbbab","#d85a38","#e9a14d","#4a82a3"]
    positive=np.zeros(2);negative=np.zeros(2)
    for key,c,label in zip(keys,cols,["Internal","Top contact","Bottom trace²","Bottom cross","Bottom drop²"]):
        vals=np.array([np.trapezoid(audits[k][key],time) for k in ("pre","post")])
        base=np.where(vals>=0,positive,negative)
        ax[0,2].bar([0,1],vals,bottom=base,color=c,label=label,width=.5)
        positive+=np.maximum(vals,0);negative+=np.minimum(vals,0)
    ax[0,2].set(xticks=[0,1],xticklabels=["S1 parent","V continued"],ylabel="Integrated Joule power",title="C   Dissipation: all signed terms")
    ax[0,2].legend(fontsize=7,loc="upper right")
    ax[0,2].set_ylim(top=.86)
    mkeys=["EV","EI","power_trace_NRMSE","energy_error","bottom_current_NRMSE"]
    for i,(n,c) in enumerate(zip(names,colors)):
        ax[1,0].bar(np.arange(5)+(i-1.5)*.19,[records[n]["metrics"][k] for k in mkeys],width=.18,color=c,label=labels[i])
    ax[1,0].set(xticks=np.arange(5),xticklabels=["Raw V RMS","Top I","Power","Energy","Bottom I"],yscale="log",
                ylabel="Frozen metric (log scale)",title="D   Neural repair and direct controls")
    ax[1,0].tick_params(axis="x",labelrotation=20)
    ax[1,0].legend(fontsize=7,ncols=2,loc="upper left")
    for n,label,c in zip(names,labels,colors):
        ax[1,1].plot(time,traces[n+"__bottom_current"],color=c,label=label,lw=1.3)
        ax[1,2].plot(time,traces[n+"__joule_power"],color=c,label=label,lw=1.3)
    ax[1,1].plot(time,traces["reference_current"],"k--",lw=1.1,label="Native reference")
    ax[1,2].plot(time,traces["reference_power"],"k--",lw=1.1,label="Native reference")
    ax[1,1].set(xlabel="Time",ylabel="FV bottom current",title="E   Bottom-current defects remain")
    ax[1,2].set(xlabel="Time",ylabel="Independent Joule power",title="F   Device benefit of known contact knots")
    ax[1,2].legend(fontsize=7.5)
    for a in ax.flat:a.grid(alpha=.18,axis="y")
    fig.suptitle("Voltage fitting, boundary trace, and device readout under fixed T / phase",fontsize=14)
    save(fig,"lf11-v-contact-main")
    fig,ax=plt.subplots(2,2,figsize=(12.8,7.6),sharex=True,layout="constrained")
    for j,(role,title) in enumerate((("pre","S1 parent"),("post","V continued"))):
        a=audits[role]
        for key,label,c,ls in [("bottom_current","Official FV","#222222","-"),("I_trace","Trace term","#d85a38","-"),
                               ("I_drop","Boundary-to-cell drop","#4a82a3","-"),("AD_bottom_current","Own AD; boundary conductivity","#188979","--"),
                               ("AD_cell_sigma_current","Own AD; cell conductivity","#8c6db0",":")]:
            ax[0,j].plot(time,a[key],label=label,color=c,ls=ls,lw=1.3)
        for key,label,c,ls in [("P_bottom","Official bottom dissipation","#222222","-"),("P_trace","Trace squared","#d85a38","-"),
                               ("P_cross","Signed cross term","#e9a14d","--"),("P_drop","Drop squared","#4a82a3",":")]:
            ax[1,j].plot(time,a[key],label=label,color=c,ls=ls,lw=1.3)
        ax[0,j].set(title=title+" | current",ylabel="Bottom current")
        ax[1,j].set(title=title+" | contact dissipation",ylabel="Bottom Joule power",xlabel="Time")
    for row in ax:
        bound=max(a.get_ylim()[1] for a in row)
        lower=min(a.get_ylim()[0] for a in row)
        for a in row:a.set_ylim(lower,bound);a.grid(alpha=.2);a.legend(fontsize=7.2)
    fig.suptitle("Exact signed decompositions; AD is a model derivative, not a reference",fontsize=13)
    save(fig,"lf11-v-electric-decomposition")
    # Tables carry all original baselines, more-information references and events.
    metrics_keys=list(records["V_continued"]["metrics"])
    with (tabdir/"all-endpoint-metrics.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.writer(f);writer.writerow(["method","identity",*metrics_keys,"valid","strict_device_pass"])
        for name,r in records.items():
            origin=r.get("origin","REUSED_LF11_OR_S1_HISTORICAL")
            writer.writerow([name,origin,*[r["metrics"].get(k) for k in metrics_keys],r["valid"],r["strict_device_pass"]])
    chosen=names+["dense_LF_ONLY","P_U"]
    table=["| Method | S | Raw Ephi | ET/.45 | Raw EV | Top-I NRMSE | Bottom-I NRMSE | Power NRMSE | Energy error |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    cols=["S","Ephi","ET","EV","EI","bottom_current_NRMSE","power_trace_NRMSE","energy_error"]
    for n in chosen:
        title=n+(" (historical LF11)" if n=="P_U" else " (more information)" if n=="dense_LF_ONLY" else "")
        table.append("| "+title+" | "+" | ".join(f'{records[n]["metrics"][k]:.9g}' for k in cols)+" |")
    (tabdir/"new-endpoints.md").write_text("\n".join(table)+"\n\nAll errors are ratios, not percentages. New D_B/P_U were not run.\n",encoding="utf-8")
    et=["| Method | Cycle | Recall | Precision | Mass ratio | Absolute timing error | Recovery |",
        "|---|---:|---:|---:|---:|---:|---:|"]
    for n in names:
        for i,c in enumerate(records[n]["cycles"]):
            recovery=c.get("recovery_fraction",c.get("recovery"))
            et.append(f'| {n} | {i+1} | {c["recall"]:.9g} | {c["precision"]:.9g} | {c["mass_ratio"]:.9g} | {c["timing_absolute"]} | {recovery} |')
    (tabdir/"new-events.md").write_text("\n".join(et)+"\n\nPhase and both cycle metrics are exactly unchanged within each V-only pair.\n",encoding="utf-8")
    print(json.dumps({"figures_and_tables_complete":True,"paper":str(paper)}))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=RUN);p.add_argument("--paper",type=Path,default=ROOT/"paper/paper_v26")
    a=p.parse_args();render(a.root,a.paper)
