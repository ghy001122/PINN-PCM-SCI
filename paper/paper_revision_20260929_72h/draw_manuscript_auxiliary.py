"""Redraw the already fixed 12.5 V display from saved arrays only."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
(HERE/'build').mkdir(exist_ok=True)
THERMAL=HERE.parent/'paper_revision_20260928_conditional_thermal'
SUBSET=HERE.parent/'paper_revision_20260928_circuit_comparison/scoring-subset'
record='single_12p5V-0p5ns'
with np.load(SUBSET/'inputs'/(record+'.npz')) as z:source={k:z[k] for k in z.files}
with np.load(THERMAL/'arrays'/record/'thermal.npz') as z:temperature={k:z[k] for k in z.files}
source_path=HERE.parents[1]/'outputs/runs/20260926-core-revision-vo2-bridge/vo2'/ (record+'.npz')
with np.load(source_path) as z:saved_T=z['temperature']
histories={};predictions={}
for key,method in [('P','PCHIP'),('CS','CS')]:
    with np.load(THERMAL/'arrays'/record/('history-'+key+'.npz')) as z:histories[key]=z['r_close']
    with np.load(SUBSET/'predictions'/method/(record+'.npz')) as z:predictions[key]=z['voltage']
t=source['time']*1e6
mask=(t>=2.362)&(t<=2.862)
fig,axs=plt.subplots(3,1,figsize=(8.8,7),sharex=True,constrained_layout=True)
colors={'P':'#2464ad','CS':'#d47915'}
axs[0].plot(t[mask],source['voltage'][mask,0],color='black',lw=1.5,label='Saved numerical source')
obs=source['observation_time']*1e6;sel=(obs>=2.362)&(obs<=2.862)
axs[0].scatter(obs[sel],source['observation_voltage'][sel,0],c='black',s=20,zorder=5,label='Finite voltage observations')
axs[1].plot(t[mask],saved_T[mask,0],color='black',lw=1.5,label='Saved numerical source')
axs[1].plot(t[mask],temperature['T_V_ref'][mask,0],color='#2b9157',ls=':',lw=1.6,label='Native voltage control')
for key in ('P','CS'):
    label='PCHIP' if key=='P' else 'Cubic spline'
    axs[0].plot(t[mask],predictions[key][mask,0],color=colors[key],label=label)
    axs[1].plot(t[mask],temperature['T_'+key][mask,0],color=colors[key],label=label)
    axs[2].plot(t[mask],histories[key][mask,0]*1e3,color=colors[key],label=label)
for ax,label in zip(axs,['Voltage (V)','Temperature (K)','Closure current (mA)']):
    ax.set_ylabel(label);ax.grid(alpha=.18);ax.legend(fontsize=8,ncol=2,loc='best')
axs[2].axhline(0,color='.45',lw=.7)
axs[2].set_xlabel('Time (microseconds)')
axs[0].set_title('12.5 V  |  Prespecified 2.362-2.862 microsecond window',fontsize=11)
for ext in ('png','pdf'):fig.savefig(HERE/'figures'/('neuristor-fixed-voltage-temperature-closure.'+ext),dpi=200)
plt.close(fig)
(HERE/'build/auxiliary-figure-source.json').write_text(json.dumps({'source':str(source_path),'temperature':str(THERMAL/'arrays'/record/'thermal.npz'),'voltage_predictions':str(SUBSET/'predictions'),'history':str(THERMAL/'arrays'/record),'window_us':[2.362,2.862],'new_integrations':0,'new_history_replays':0,'alignment':'none'},indent=2),encoding='utf8')
