"""Bounded SI adaptation of Qiu SI and the pinned Zhang author hysteresis code.

Provenance: Qiu et al., Adv. Mater. 36, 2306818; arXiv:2307.11256v2 SI S1-S9;
Zhang author code 217d4f0ed6bfc680240021b07142a121cb4963d1 (MIT, copyright
2024 Yuanhang Zhang). This implementation retains that code's hysteresis rules.
It uses the SI's two-node thermal topology, not the later array-neighbour rule.
"""
from dataclasses import dataclass,asdict
from pathlib import Path
import argparse,json,time
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'outputs/runs/20260926-core-revision-vo2-bridge/vo2'


@dataclass(frozen=True)
class Parameters:
    R0:float=5.35882879e-3
    Ea:float=5220.47417
    beta:float=.252796285
    w:float=7.19357064
    Tc:float=332.805839
    gamma:float=.956269682
    Rm0:float=262.5
    k:float=4.90025335
    C:float=145.34619293e-12
    Cth:float=49.62776831e-12
    Sth:float=.20558726e-3
    RL:float=12000.
    Tbase:float=325.


P=Parameters()
CASES=[dict(id='single_9V',Vin=[9.],eta=0.,figure='Fig.2A',evidence='experiment_and_author_fitted_simulation'),
       dict(id='single_12p5V',Vin=[12.5],eta=0.,figure='Fig.2B',evidence='experiment_and_author_fitted_simulation'),
       dict(id='single_15p8V',Vin=[15.8],eta=0.,figure='Fig.2C',evidence='experiment_and_author_fitted_simulation'),
       dict(id='pair_excitation',Vin=[11.,9.4],eta=.12,figure='Fig.S11D',evidence='author_simulation'),
       dict(id='pair_inhibition',Vin=[11.,14.],eta=.1,figure='Fig.S13D',evidence='author_simulation')]
HKEYS=('delta','reversed','Tr','gr','Tpr','T_last')


class Hysteresis:
    def __init__(self,n,parameters=P):
        self.p=parameters
        self.delta=np.ones(n,dtype=np.float64)
        self.reversed=np.zeros(n,dtype=np.float64)
        T=np.full(n,parameters.Tbase-.1,dtype=np.float64)
        self.gr=self.g_major(T);self.Tr=T.copy();self.Tpr=self.tpr();self.T_last=T.copy()
    def g_major(self,T):
        p=self.p
        return .5+.5*np.tanh(p.beta*(self.delta*p.w/2+p.Tc-T))
    def tpr(self):
        p=self.p
        return self.delta*p.w/2+p.Tc-np.arctanh(2*self.gr-1)/p.beta-self.Tr
    def g(self,T):
        p=self.p;x=(T-self.Tr)/(self.Tpr+1e-6)
        proximity=.5*(1-np.sin(p.gamma*x))*(1+np.tanh(np.pi**2-2*np.pi*x))
        tp=self.Tpr*proximity*self.reversed
        return .5+.5*np.tanh(p.beta*(self.delta*p.w/2+p.Tc-(T+tp)))
    def reversal(self,T):
        clipped=np.clip(T,305.,370.)
        change=clipped-self.T_last
        if np.max(abs(change))>.01:
            delta=np.sign(change);mask=(delta!=self.delta)&(delta!=0)
            if np.any(mask):
                self.gr[mask]=self.g(clipped)[mask]
                self.delta[mask]=delta[mask];self.reversed[mask]=1.
                self.Tr[mask]=clipped[mask];self.Tpr[mask]=self.tpr()[mask]
            self.T_last=clipped.copy()
    def resistance(self,T,dynamic=True):
        p=self.p;clipped=np.clip(T,305.,370.)
        return p.R0*np.exp(p.Ea/clipped)*self.g(clipped)+p.Rm0*(p.k if dynamic else 1.)


def rhs(voltage,temperature,resistance,Vin,eta,p=P):
    device_current=voltage/resistance
    load_current=(Vin-voltage)/p.RL
    dv=(load_current-device_current)/p.C
    environment=p.Sth*(1-eta)
    exchange=np.zeros_like(temperature)
    if len(temperature)==2:exchange=eta*p.Sth*(temperature[::-1]-temperature)
    dt=(voltage*device_current-environment*(temperature-p.Tbase)+exchange)/p.Cth
    return dv,dt,device_current,load_current,exchange


def frozen_contract():
    return dict(task_id='PCM-20260926-CORE-REVISION-VO2-BRIDGE-01',parameters_SI=asdict(P),
        units=dict(R0='ohm',Ea='K',beta='1/K',w='K',Tc='K',gamma='dimensionless',Rm0='ohm',
                   k='dimensionless',C='F',Cth='J/K',Sth='W/K',RL='ohm',Tbase='K'),
        author_unit_conversion=dict(time_ns_to_s=1e-9,resistance_kohm_to_ohm=1e3,
            capacitance_pF_to_F=1e-12,thermal_capacity_mW_ns_per_K_to_J_per_K=1e-12,
            conductance_mW_per_K_to_W_per_K=1e-3,current_mA_to_A=1e-3),
        author_commit='217d4f0ed6bfc680240021b07142a121cb4963d1',cases=CASES,
        dt_seconds=[1e-9,.5e-9],end_seconds=20e-6,maximum_system_steps=300000,dtype='float64',
        initial=dict(V=0.,T=325.,hysteresis_initial_T=324.9,delta=1.,reversed=0.,other_history='author initialization formulas'),
        width_factor=1.,Cth_factor=1.,noise_strength=0.,
        clamp=dict(lower_K=305.,upper_K=370.,scope='resistance and reversal; state T is not clipped'),
        reversal_trigger=dict(max_vector_abs_dT_K=.01,strict_greater=True,comparison='last trigger state'),
        denominator_regularizer_K=1e-6,S3_choice='author code atanh; preprint equation discrepancy retained',
        scheme='explicit Euler, history then same-level R/I/RHS and record, then simultaneous state update',
        topology='single S_env=Sth; pair S_env=(1-eta)Sth, mutual=eta Sth',
        peak_rule=dict(current='device current',threshold_A=.0015,minimum_interval_s=.5e-6,
            near_peak_choice='higher, ties earlier',smoothing=False,alignment=False),
        analysis_windows_s=dict(full=[0.,20e-6],transient=[0.,10e-6],tail=[10e-6,20e-6]),
        branch_description='all tail g>0.5 insulating; all g<0.5 metallic; otherwise unresolved; no equilibrium certification',
        quantitative_reproduction_tolerance=None,refitting=False,extra_cases=False)


def simulate(case,dt,out):
    n=len(case['Vin']);steps=round(20e-6/dt);Vin=np.asarray(case['Vin'],dtype=np.float64)
    voltage=np.zeros(n);temperature=np.full(n,P.Tbase);history=Hysteresis(n)
    keys=('voltage','temperature','resistance','device_current','load_current','capacitor_current','g',*HKEYS)
    arrays={k:np.empty((steps+1,n),dtype=np.float64) for k in keys}
    energy=np.zeros(steps);euler_defect=np.zeros(steps);balance_defect=np.zeros(steps)
    peak_exchange=peak_kcl=0.
    for i in range(steps+1):
        history.reversal(temperature)
        resistance=history.resistance(temperature)
        dv,dT,Id,Il,exchange=rhs(voltage,temperature,resistance,Vin,case['eta'])
        row=dict(voltage=voltage,temperature=temperature,resistance=resistance,device_current=Id,
                 load_current=Il,capacitor_current=P.C*dv,g=history.g(np.clip(temperature,305.,370.)))
        row.update({k:getattr(history,k) for k in HKEYS})
        for k in keys:arrays[k][i]=row[k]
        if not all(np.isfinite(v).all() for v in row.values()):raise FloatingPointError((case['id'],i))
        peak_exchange=max(peak_exchange,abs(float(sum(exchange))))
        peak_kcl=max(peak_kcl,float(np.max(abs(Il-Id-P.C*dv))))
        if i==steps:break
        next_v=voltage+dt*dv;next_T=temperature+dt*dT
        source=np.sum(Vin*Il-P.RL*Il**2-(1-case['eta'])*P.Sth*(temperature-P.Tbase))
        change=np.sum(.5*P.C*(next_v**2-voltage**2)+P.Cth*(next_T-temperature))
        correction=float(np.sum(.5*P.C*dt**2*dv**2))
        energy[i]=dt*source;euler_defect[i]=correction;balance_defect[i]=change-dt*source-correction
        voltage,temperature=next_v,next_T
    np.savez_compressed(out,time=np.arange(steps+1)*dt,**arrays,
        net_external_energy_step_J=energy,euler_capacitive_energy_defect_J=euler_defect,
        discrete_energy_balance_defect_J=balance_defect)
    return dict(case=case['id'],dt=dt,system_steps=steps,states=steps+1,
        max_KCL_defect_A=peak_kcl,max_mutual_heat_sum_W=peak_exchange,
        total_Euler_energy_defect_J=float(sum(euler_defect)),max_corrected_energy_defect_J=float(max(abs(balance_defect))),
        temperature_range_K=[float(arrays['temperature'].min()),float(arrays['temperature'].max())],
        clipping_of_evolved_state=False,initialization_shared=False)


def detect_peaks(times,current):
    candidates=np.flatnonzero((current[1:-1]>current[:-2])&(current[1:-1]>=current[2:])&(current[1:-1]>.0015))+1
    chosen=[]
    for i in sorted(candidates,key=lambda j:(-current[j],times[j])):
        if all(abs(times[i]-times[j])>=.5e-6-1e-18 for j in chosen):chosen.append(int(i))
    return np.array(sorted(chosen),dtype=int)


def events(data,j,window):
    t=data['time'];I=data['device_current'][:,j]
    idx=detect_peaks(t,I);idx=idx[(t[idx]>=window[0])&(t[idx]<=window[1])]
    ts=t[idx];isi=np.diff(ts)
    mask=(t>=window[0])&(t<=window[1]);g=data['g'][mask,j]
    if len(idx):label='DETECTED_SPIKING'
    elif np.all(g>.5):label='NO_DETECTED_PEAKS_INSULATING_BRANCH'
    elif np.all(g<.5):label='NO_DETECTED_PEAKS_METALLIC_BRANCH'
    else:label='TRANSITION_OR_UNRESOLVED'
    return dict(count=len(idx),times_s=ts.tolist(),heights_A=I[idx].tolist(),
        first_peak_s=float(ts[0]) if len(ts) else None,intervals_s=isi.tolist(),
        frequency_Hz=float(1/np.mean(isi)) if len(isi) else None,functional_description=label,
        g_range=[float(g.min()),float(g.max())],
        temperature_range_K=[float(data['temperature'][mask,j].min()),float(data['temperature'][mask,j].max())],
        resistance_range_ohm=[float(data['resistance'][mask,j].min()),float(data['resistance'][mask,j].max())],
        temperature_change_K=float(data['temperature'][mask,j][-1]-data['temperature'][mask,j][0]),
        equilibrium_certified=False)


def compare(case,out):
    a=np.load(out/(case['id']+'-1ns.npz'));b=np.load(out/(case['id']+'-0p5ns.npz'))
    np.testing.assert_allclose(a['time'],b['time'][::2],rtol=0,atol=1e-20)
    records=[]
    for j in range(len(case['Vin'])):
        waves={}
        for k in ('voltage','device_current','temperature','resistance'):
            x=a[k][:,j];y=b[k][::2,j];d=x-y;rms=float(np.sqrt(np.mean(d*d)))
            scale=float(np.sqrt(np.mean(y*y)))
            waves[k]=dict(unaligned_rms=rms,max_abs=float(np.max(abs(d))),relative_rms=rms/scale if scale else None)
        windows={}
        for label,w in dict(full=(0,20e-6),transient=(0,10e-6),tail=(10e-6,20e-6)).items():
            ea,eb=events(a,j,w),events(b,j,w);m=min(ea['count'],eb['count'])
            windows[label]=dict(coarse=ea,fine=eb,
                paired_peak_time_differences_s=(np.array(ea['times_s'][:m])-np.array(eb['times_s'][:m])).tolist(),
                paired_peak_height_differences_A=(np.array(ea['heights_A'][:m])-np.array(eb['heights_A'][:m])).tolist(),
                unmatched_coarse=ea['times_s'][m:],unmatched_fine=eb['times_s'][m:],
                count_equal=ea['count']==eb['count'],labels_equal=ea['functional_description']==eb['functional_description'])
        end={k:dict(coarse=float(a[k][-1,j]),fine=float(b[k][-1,j]),difference=float(a[k][-1,j]-b[k][-1,j]))
             for k in ('voltage','temperature','resistance','g',*HKEYS)}
        records.append(dict(device=j,waveforms=waves,events=windows,end_state=end))
    return dict(case=case,devices=records,numerical_claim='TWO_STEP_SENSITIVITY_ONLY',
                quantitative_reproduction_certified=False,experimental_fit_performed=False)


def run(out=RUN):
    out.mkdir(parents=True,exist_ok=True)
    contract=frozen_contract();path=out/'frozen-config.json'
    if path.exists():assert json.loads(path.read_text())==contract
    else:path.write_text(json.dumps(contract,indent=2),encoding='utf-8')
    started=time.perf_counter();cost=[]
    for case in CASES:
        for label,dt in [('1ns',1e-9),('0p5ns',.5e-9)]:
            target=out/(case['id']+'-'+label+'.npz');meta=target.with_suffix('.json')
            if target.exists():
                if not meta.exists():raise RuntimeError('Existing trajectory without completion metadata; inspect first')
                record=json.loads(meta.read_text())
            else:
                record=simulate(case,dt,target);meta.write_text(json.dumps(record,indent=2),encoding='utf-8')
            cost.append(record);print(json.dumps(record),flush=True)
    results=[compare(case,out) for case in CASES]
    report=dict(status='COMPLETE',claim_status='VERIFIED',step_records=cost,cases=results,
        total_system_steps=sum(x['system_steps'] for x in cost),seconds=time.perf_counter()-started,
        interpretation='Author-model reproduction and sensitivity; not validation of the old synthetic PINN material')
    assert report['total_system_steps']==300000
    (out/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=RUN);run(p.parse_args().out)
