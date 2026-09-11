"""Render saved LF11 adjudication; never repeat training or metric estimation."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from .phk_benchmark import PhkControl
from .phk_v22r_evaluator import load_reference
from .phk_v23_lf11 import SparseData, build_model
from .phk_v23_lf11_readout import interpolate_sparse
from .phk_v23_lf11_evaluation import figures,field_figure


def waveform_figure(traces, time, reference, waveform, directory):
    fig,axes=plt.subplots(2,2,figsize=(12,7),constrained_layout=True)
    values={'B_logit (frozen)':traces['B_logit'],'B_logit + known waveform (posthoc)':waveform,
            'P_U':traces['P_U']}
    styles=[('tab:red','--'),('tab:green','-'),('tab:blue','-')]
    for (name,trace),(color,style) in zip(values.items(),styles):
        energy=np.r_[0,np.cumsum(.5*(trace['joule_power'][1:]+trace['joule_power'][:-1])*np.diff(time))]
        axes[0,0].plot(time,trace['top_current'],style,color=color,label=name)
        axes[0,1].plot(time,energy,style,color=color)
        axes[1,0].plot(time,trace['top_current']-trace['bottom_current'],style,color=color)
        axes[1,1].plot(time,trace['power_defect'],style,color=color)
    axes[0,0].plot(time,reference.top_current,'k',lw=1.8,label='native reference')
    axes[0,1].plot(time,np.r_[0,np.cumsum(.5*(reference.joule_power[1:]+reference.joule_power[:-1])*np.diff(time))],'k',lw=1.8)
    for ax,title in zip(axes.flat,('Top-electrode current','Cumulative Joule energy','Current balance: top minus bottom','Power defect: Joule minus supplied')):
        ax.set_title(title);ax.set_xlabel('Dimensionless time');ax.grid(alpha=.2)
    axes[0,0].legend(fontsize=7)
    fig.suptitle('Known-waveform diagnostic: identical observations, phase and temperature; no training',fontsize=11)
    for ext in ('png','pdf'):fig.savefig(directory/f'lf11-waveform-and-conservation.{ext}')
    plt.close(fig)


def direction_figure(diagnosis,directory):
    sources=['observation','boundary','electric','thermal','phase','historical_momentum']
    heads=['potential','temperature','phase']
    metrics={'potential':'EV_squared','temperature':'ET_squared','phase':'Ephi_squared'}
    arrays=[]
    for role in ('P_U','P_M'):
        record=next(r for r in diagnosis['records'] if r['role']==role)
        array=np.zeros((len(sources),3))
        for i,source in enumerate(sources):
            for j,head in enumerate(heads):
                row=next(r for r in record['rows'] if r['equation']==source and r['head']==head)
                array[i,j]=1e4*row['relative_first_order_rms_effect'][metrics[head]]
        arrays.append(array)
    limit=max(float(np.max(np.abs(a))) for a in arrays)
    fig,axes=plt.subplots(1,2,figsize=(11,5),constrained_layout=True)
    for ax,array,role in zip(axes,arrays,('P_U','P_M')):
        artist=ax.imshow(array,cmap='coolwarm',vmin=-limit,vmax=limit,aspect='auto')
        ax.set_xticks(range(3),['V head / V error','T head / T error','Phase head / phase error'],rotation=20,ha='right')
        ax.set_yticks(range(len(sources)),sources)
        for i in range(array.shape[0]):
            for j in range(array.shape[1]):
                ax.text(j,i,f'{array[i,j]:.3g}',ha='center',va='center',fontsize=8,
                        color='white' if abs(array[i,j])>.65*limit else 'black')
        ax.set_title(role+' endpoint: prospective update 1201')
    fig.colorbar(artist,ax=axes,shrink=.8,label='Relative first-order RMS change x 10,000')
    fig.suptitle('Actual Adam moments, shared denominator; red increases error, blue decreases error',fontsize=11)
    for ext in ('png','pdf'):fig.savefig(directory/f'lf11-equation-head-directions.{ext}')
    plt.close(fig)


def render(root):
    output=root/'local'
    result=json.loads((output/'results.json').read_text())
    records=result['records']
    with np.load(output/'traces.npz',allow_pickle=False) as f:
        time=f['time']
        reference_traces=SimpleNamespace(top_current=f['reference_current'],joule_power=f['reference_power'])
        traces={}
        for key in f.files:
            if '__' in key:
                role,name=key.split('__',1)
                traces.setdefault(role,{})[name]=f[key]
    figures(records,traces,time,reference_traces,output)
    # Only image snapshots need field access. Saved official metrics are reused.
    reference,_=load_reference(PhkControl.FULL)
    peaks=[c['peak_time_index'] for c in records['native_reference_readout_check']['cycles']]
    snapshots={'native_reference_readout_check':{'phase':reference.phase[peaks].copy()}}
    best_sparse=min(('B_L','B_P','B_logit'),key=lambda n:records[n]['metrics']['S'])
    best_physics=min(('P_U','P_I','P_M'),key=lambda n:records[n]['metrics']['S'])
    for role in ('D_B',best_physics):
        with np.load(root/'formal'/role/'prediction.npz',allow_pickle=False) as f:
            snapshots[role]={'phase':f['phase'][peaks]}
    config=json.loads((root/'formal/frozen_config.json').read_text())
    physics=build_model(config).physics
    sparse_fields=interpolate_sparse(SparseData(root/'input/sparse.npz'),reference.grid.x_centers,
                     reference.grid.z_centers,reference.time[peaks],physics,best_sparse)
    snapshots[best_sparse]={'phase':sparse_fields['phase']}
    field_figure(snapshots,records,reference.grid,reference.time[peaks],output)
    if (output/'waveform-diagnostic.json').exists():
        with np.load(output/'waveform-traces.npz',allow_pickle=False) as f:
            waveform={k:f[k] for k in f.files if k!='time'}
        waveform_figure(traces,time,reference_traces,waveform,output)
    if (output/'equation-head-diagnosis.json').exists():
        direction_figure(json.loads((output/'equation-head-diagnosis.json').read_text()),output)
    names=['B_L','B_P','B_logit','D_B','P_U','P_I','P_M','dense_LF_ONLY','warm_start','native_reference_readout_check']
    keys=['S','Ephi','ET','EI','EV','energy_error']
    lines=['# LF11 fixed-endpoint results','',
           'Nominal sparse reconstruction; strict event/device checks are separate.','',
           '| Role | S | Raw Ephi | ET/0.45 | EI | EV | Energy error | Strict device |',
           '|---|---:|---:|---:|---:|---:|---:|---|']
    with (output/'metrics.csv').open('w',encoding='utf-8',newline='') as handle:
        writer=csv.writer(handle);writer.writerow(['role',*keys,'strict_device_pass'])
        for name in names:
            r=records[name];m=r['metrics']
            writer.writerow([name,*[m[k] for k in keys],r['strict_device_pass']])
            lines.append('| '+name+' | '+' | '.join(f'{m[k]:.8g}' for k in keys)+f" | {r['strict_device_pass']} |")
    (output/'results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'status':'FIGURES_AND_TABLES_COMPLETE','figure_stems':[p.stem for p in output.glob('*.png')],
                      'saved_adjudication_reused':True,'optimizer_updates':0}),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    a=p.parse_args();torch.set_num_threads(2);render(a.root)


if __name__=='__main__':main()
