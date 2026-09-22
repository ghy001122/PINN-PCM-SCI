"""Physical panels from locked saved arrays; no neural inference or solve."""
from pathlib import Path
import importlib.util
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import Normalize

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
RUN=ROOT/'outputs/runs/20260921-b1-second-cycle-phase-gap'
CORE=ROOT/'outputs/submission-rescore-20260921'
TIMES=np.array([.27,1.28])

def read(path):return json.loads(path.read_text(encoding='utf-8'))

def savefig(fig,name):
    fig.savefig(HERE/'figures'/(name+'.png'),dpi=320,bbox_inches='tight',facecolor='white')
    fig.savefig(HERE/'figures'/(name+'.svg'),bbox_inches='tight',facecolor='white')
    plt.close(fig)

def select(path,reader,grid,physics):
    with np.load(path,allow_pickle=False) as f:
        t=f['time'];ix=[int(np.argmin(abs(t-v))) for v in TIMES]
        np.testing.assert_allclose(t[ix],TIMES,rtol=0,atol=1e-12)
        result={k:f[k][ix].copy() for k in ('temperature','phase')}
        if 'joule_density' in f:
            result['joule_density']=f['joule_density'][ix].copy()
        else:
            fields={**result,'potential':f['potential'][ix].copy(),'time':t[ix].copy()}
            result['joule_density']=reader.s.deposition(fields,grid,physics)
    return result

def image(ax,values,shape,cmap,norm,title):
    im=ax.imshow(values.reshape(shape),origin='lower',extent=(-1,1,0,1),
        cmap=cmap,norm=norm,interpolation='nearest',aspect='equal')
    ax.plot([-.35,.35],[0,0],color='#142d40',lw=2.5,clip_on=False)
    ax.set_title(title,fontsize=8)
    ax.set_xticks([-1,0,1]);ax.set_yticks([0,.5,1]);ax.tick_params(labelsize=7,length=2)
    return im

def object_information(cfg):
    fig=plt.figure(figsize=(7.1,4.1),layout='constrained')
    gs=fig.add_gridspec(2,2,width_ratios=(1,1.6),height_ratios=(1,.8))
    ax=fig.add_subplot(gs[:,0]);ax.add_patch(Rectangle((-1,0),2,1,facecolor='#eef4f6',edgecolor='#234354'))
    with np.load(RUN/'input/visible-fields.npz',allow_pickle=False) as f:
        x,z=np.meshgrid(f['x'],f['z']);times=f['time'].copy()
        ax.scatter(x.ravel(),z.ravel(),s=2,color='#70949f',alpha=.7)
    ax.plot([-1,1],[1,1],lw=4,color='#bc612c');ax.plot([-.35,.35],[0,0],lw=4,color='#162c3c')
    ax.add_patch(Rectangle((-.55,0),1.1,.55,fill=False,linestyle='--',edgecolor='#8a6559'))
    ax.text(0,1.09,'Driven top electrode: U(t); T=0',ha='center',fontsize=8)
    ax.text(0,-.18,'Grounded bottom segment',ha='center',fontsize=8)
    ax.text(0,.68,'V -> Joule heat -> T -> phase\nConductivity feeds back to V',ha='center',fontsize=8)
    ax.set(xlim=(-1.2,1.2),ylim=(-.25,1.2),xlabel='x',ylabel='z',aspect='equal')
    ax.set_title('(a) Synthetic 2D cell\nand fixed observation sites',fontsize=9)
    pulse=fig.add_subplot(gs[0,1]);t=np.linspace(0,2.5,1001)
    for starts,label,color,style in (([0,1.25],'Original','#71818a','--'),([0,1.01],'Shorter / B1','#166a83','-')):
        u=np.zeros_like(t)
        for start in starts:
            a=t-start
            u+=.72*np.where((a>=0)&(a<.05),a/.05,
                 np.where((a>=.05)&(a<=.27),1,np.where((a>.27)&(a<.35),(.35-a)/.08,0)))
        pulse.plot(t,u,label=label,color=color,ls=style)
    pulse.axvspan(1.01,2.02,color='#edbe85',alpha=.3)
    for time in TIMES:pulse.axvline(time,color='#8b6460',ls=':',lw=.8)
    pulse.set(xlim=(0,2.5),ylim=(-.02,.84),ylabel='U(t)')
    pulse.set_title('(b) Two finite pulses; fixed display times',fontsize=9)
    pulse.legend(frameon=False,fontsize=7,loc='upper right')
    mask=fig.add_subplot(gs[1,1],sharex=pulse)
    visible=(times<1.01)|(times>2.02)
    for y,label,keep in ((2,'V',np.ones(len(times),bool)),(1,'T',np.ones(len(times),bool)),(0,'phase',visible)):
        mask.scatter(times[keep],np.full(keep.sum(),y),s=7,c='#176c82',marker='|')
    mask.axvspan(1.01,2.02,color='#edbe85',alpha=.3)
    mask.text(1.515,.45,'phase labels withheld',ha='center',fontsize=8)
    mask.set(yticks=[0,1,2],yticklabels=['phase','T','V'],xlabel='t',ylim=(-.55,2.5))
    mask.set_title('(c) B1 time visibility; post-window phase retained',fontsize=9)
    savefig(fig,'fig01-object-information')

def main():
    assert read(RUN/'compute-closure.json')['instance_shutdown_confirmed']
    assert (RUN/'scoring/results.json').is_file()
    (HERE/'figures').mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.spines.top':False,
                         'axes.spines.right':False,'svg.fonttype':'none'})
    spec=importlib.util.spec_from_file_location('figure_frozen_reader',CORE/'portable/readout_rescore.py')
    reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    manifest=read(CORE/'manifest.json');desc=manifest['protocols']['shorter']
    physics=reader.s.Physics(protocol='shorter',**desc['physics'])
    grid=reader.grid_native(manifest['grid_metadata']);shape=(grid.nz,grid.nx)
    reference=select(CORE/desc['native_spatial_reference'],reader,grid,physics)
    cfg=read(RUN/'frozen-config.json');assert cfg['figure_times']==TIMES.tolist()
    object_information(cfg)
    old={x['id']:x for x in manifest['objects']}
    old_selected={key:select(CORE/old[key]['fine_prediction'],reader,grid,physics)
                  for key in ('shorter/29/E','shorter/29/F','shorter/43/E','shorter/43/F','shorter/B_E')}
    # Reference fields plus signed errors at the second plateau; both seeds get
    # the same panel recipe. The main text uses seed 29; seed 43 is retained.
    for seed in (29,43):
        fig,axs=plt.subplots(3,5,figsize=(7.1,5.2),layout='constrained')
        for row,(key,label) in enumerate((('temperature','T'),('phase','phase'),('joule_density','q'))):
            vals=reference[key]
            norm=Normalize(0,1 if key=='phase' else max(float(vals.max()),1e-12))
            for col,j in enumerate((0,1)):
                im=image(axs[row,col],vals[j],shape,'viridis',norm,f'{label} ref, t={TIMES[j]:.2f}')
            fig.colorbar(im,ax=list(axs[row,:2]),shrink=.75,pad=.02)
            keys=[f'shorter/{seed}/E',f'shorter/{seed}/F','shorter/B_E']
            errors=[old_selected[k][key][1]-vals[1] for k in keys]
            limit=max(max(float(np.max(abs(old_selected[k][key][1]-vals[1]))) for k in old_selected),1e-12)
            for col,(role,error) in enumerate(zip(('E','F','B_E'),errors),start=2):
                im=image(axs[row,col],error,shape,'RdBu_r',Normalize(-limit,limit),f'{role} - ref')
            fig.colorbar(im,ax=list(axs[row,2:]),shrink=.75,pad=.02)
        savefig(fig,f'fig02-full-label-physics-seed{seed}')
    items=read(RUN/'readout-manifest.json')['objects']
    selected={item['id']:select(ROOT/item['fine_prediction'],reader,grid,physics) for item in items}
    ordering=[('Reference',reference),('B_E',selected['shorter/B_E'])]
    ordering += [(f'{role}, seed {seed}',selected[f'shorter/{seed}/{role}'])
                 for seed in (29,43) for role in ('E','D_E','F')]
    for key,label in (('temperature','T'),('phase','phase'),('joule_density','q')):
        for j,t in enumerate(TIMES):
            norm=Normalize(0,1 if key=='phase' else max(float(v[key].max()) for _,v in ordering))
            fig,axs=plt.subplots(3,3,figsize=(7.1,4.7),layout='constrained')
            panels=[axs.flat[i] for i in (0,1,3,4,5,6,7,8)]
            axs.flat[2].axis('off')
            gap_label='Inside phase-label gap' if 1.01<=t<=2.02 else 'Outside phase-label gap'
            axs.flat[2].text(.5,.5,'Shared reference and baseline\nSeed 29: second row\nSeed 43: third row\nV/T samples retained\n'+gap_label,ha='center',va='center',fontsize=8)
            for ax,(name,values) in zip(panels,ordering):
                im=image(ax,values[key][j],shape,'viridis',norm,name)
            fig.colorbar(im,ax=panels,shrink=.82,pad=.02,label=label+' (dimensionless)')
            fig.suptitle(f'B1: {label} at fixed t={t:.2f}; native 240 x 120 fields',fontsize=10)
            savefig(fig,f'b1-{key}-t{j+1}')
            errors=[(name,v[key][j]-reference[key][j]) for name,v in ordering]
            limit=max(max(float(np.max(abs(v[key]-reference[key]))) for _,v in ordering),1e-12)
            fig,axs=plt.subplots(3,3,figsize=(7.1,4.7),layout='constrained')
            panels=[axs.flat[i] for i in (0,1,3,4,5,6,7,8)]
            axs.flat[2].axis('off')
            axs.flat[2].text(.5,.5,'Signed error, common scale\nSeed 29: second row\nSeed 43: third row\nNo spatial crop',ha='center',va='center',fontsize=8)
            for ax,(name,values) in zip(panels,errors):
                im=image(ax,values,shape,'RdBu_r',Normalize(-limit,limit),name)
            fig.colorbar(im,ax=panels,shrink=.82,pad=.02,label='prediction - reference')
            fig.suptitle(f'B1: signed {label} error at fixed t={t:.2f}',fontsize=10)
            savefig(fig,f'b1-{key}-error-t{j+1}')
    summary=read(HERE/'evidence/b1-summary.json')
    metrics=['S','Ephi','ET','EV','EI','bottom_current_NRMSE','power_trace_NRMSE']
    primary=summary['primary_comparisons']
    values=np.array([[100*x['effects'][k]['relative_error_reduction']
                      if x['effects'][k]['relative_error_reduction'] is not None else np.nan for k in metrics] for x in primary])
    fig,ax=plt.subplots(figsize=(7.1,4.8),layout='constrained')
    im=ax.imshow(values,cmap='RdBu',vmin=-100,vmax=100,aspect='auto')
    for i in range(len(primary)):
        for j in range(len(metrics)):
            v=values[i,j];ax.text(j,i,'n/a' if not np.isfinite(v) else f'{v:.1f}',ha='center',va='center',fontsize=7,
                                 color='white' if abs(v)>60 else '#172a37')
    ax.set_xticks(range(7),['S','phase','T','V','top I','bottom I','power'])
    ax.set_yticks(range(len(primary)),[f"{x['seed']} / {x['reference']} / {'160' if x['reader']=='coarse' else '240'} / {'pass' if x['A_w'] else 'fail'}" for x in primary])
    ax.set_title('B1: E versus D_E in W; reference / reader / complete A_w',fontsize=10)
    fig.colorbar(im,ax=ax,label='Error reduction (%) = 100(1 - E / D_E); color capped at +/-100')
    savefig(fig,'fig05-b1-matched-effects')
    assets={}
    for name,state in [('reference',reference),*old_selected.items(),*[(f'b1/{k}',v) for k,v in selected.items()]]:
        for field,value in state.items():assets[name.replace('/','_')+'__'+field]=value
    (HERE/'figure-data').mkdir(exist_ok=True)
    np.savez_compressed(HERE/'figure-data/physical-panels.npz',time=TIMES,x=grid.x_centers,z=grid.z_centers,**assets)
    provenance=dict(times=TIMES.tolist(),selection='frozen waveform plateau endpoints before B1 outcomes',
        reference=desc['native_spatial_reference'],grid=[240,120],new_neural_queries=0,new_linear_solves=0,
        new_reference_steps=0,q_source='saved Joule density when present; otherwise algebraic deposition from saved native V/T/phase at the two display times',
        primary_T_phase_event_measure_unchanged=[160,80],all_B1_seeds_and_controls_included=True)
    (HERE/'figure-data/provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    print(json.dumps(dict(status='PHYSICAL_PANELS_FROM_FIXED_ARRAYS',**provenance)),flush=True)

if __name__=='__main__':main()
