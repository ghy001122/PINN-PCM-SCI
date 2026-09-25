"""Observation-preserving phase completion on a frozen B1 E endpoint.

Only the correction is trainable. Cached coordinate derivatives are evaluated
before detaching; complete phase derivatives are composed analytically. The
original modules and checkpoints are not modified or monkeypatched.
"""
from __future__ import annotations
import numpy as np
import torch
from torch import nn
from scipy.interpolate import BSpline
from .phk_v22r_pinn import _gradient
from .phk_v23_lf11_followup_fit import fit_model, head_field
from .phk_v23_lf11_elimination_physics import fields as base_fields, coordinates, face_quadrature, grid_for
from .phk_v23_lf11_elimination import TimeSampler
from .phk_v23_b1_observations import VisibleTimes
from .phk_v23_lf11_electric_layer import ElectricalLayer

A, B = 1.36, 2.02
SEGMENTS = ((0.,.35),(.35,1.01),(1.01,1.36),(A,B),(2.02,2.5))


def dark_gate(t):
    s = (t-A)/(B-A)
    return torch.where((t>A)&(t<B), 64*s**3*(1-s)**3, torch.zeros_like(t))


def gate_derivatives(t):
    s=(t-A)/(B-A); active=(t>A)&(t<B)
    g=64*s**3*(1-s)**3
    d=192*s**2*(1-s)**2*(1-2*s)/(B-A)
    d2=384*s*(1-s)*(1-5*s+5*s*s)/(B-A)**2
    return tuple(torch.where(active,x,torch.zeros_like(t)) for x in (g,d,d2))


class NeuralCorrection(nn.Module):
    def __init__(self):
        super().__init__()
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(2901)
            self.net=nn.Sequential(nn.Linear(3,32),nn.Tanh(),nn.Linear(32,32),nn.Tanh(),nn.Linear(32,1)).double()
        nn.init.zeros_(self.net[-1].weight); nn.init.zeros_(self.net[-1].bias)
        assert sum(p.numel() for p in self.parameters())==1217

    def forward(self, normalized):
        return self.net(normalized).ravel()


def axis_basis(values, n, lo, hi):
    """Only the four active cubic bases and their physical-coordinate jets."""
    knots=np.r_[np.repeat(lo,4),np.linspace(lo,hi,n-2)[1:-1],np.repeat(hi,4)]
    spline=BSpline(knots,np.eye(n),3,extrapolate=False)
    span=np.clip(np.searchsorted(knots,values,side='right')-1,3,n-1)
    idx=span[:,None]-3+np.arange(4)[None,:]
    jet=[spline(values,nu=k)[np.arange(len(values))[:,None],idx] for k in range(3)]
    return idx,jet


class SplineCorrection(nn.Module):
    def __init__(self):
        super().__init__(); self.coefficients=nn.Parameter(torch.zeros(41*21*9,dtype=torch.float64))

    @staticmethod
    def prepare(q):
        v=q.detach().cpu().numpy(); use=(v[:,2]>A)&(v[:,2]<B)
        rows=np.flatnonzero(use); v=v[use]
        # Outside-support queries never reach the time spline.
        ix,bx=axis_basis(v[:,0],41,-1.,1.)
        iz,bz=axis_basis(v[:,1],21,0.,1.)
        it,bt=axis_basis((v[:,2]-A)/(B-A),9,0.,1.)
        index=((ix[:,:,None,None]*21+iz[:,None,:,None])*9+it[:,None,None,:]).reshape(len(v),64)
        weights={}
        for name,dx,dz,dt in [('v',0,0,0),('x',1,0,0),('z',0,1,0),('t',0,0,1),('xx',2,0,0),('zz',0,2,0)]:
            weights[name]=torch.as_tensor((bx[dx][:,:,None,None]*bz[dz][:,None,:,None]*bt[dt][:,None,None,:]).reshape(len(v),64)/(B-A)**dt,
                                         device=q.device,dtype=q.dtype)
        return dict(rows=torch.as_tensor(rows,device=q.device),index=torch.as_tensor(index,device=q.device),weights=weights)

    def jet(self,q,prepared=None):
        p=self.prepare(q) if prepared is None else prepared
        values=self.coefficients[p['index']]
        out={name:torch.zeros(len(q),dtype=q.dtype,device=q.device).index_add(0,p['rows'],(values*w).sum(1))
             for name,w in p['weights'].items()}
        g,dg,_=gate_derivatives(q[:,2])
        delta=8*g*out['v']
        grad=8*torch.stack([g*out['x'],g*out['z'],dg*out['v']+g*out['t']],1)
        lap=8*g*(out['xx']+out['zz'])
        return delta,grad,lap


class Completion(nn.Module):
    def __init__(self, config, state, arm, device='cpu'):
        super().__init__(); self.arm=arm
        self.base=fit_model(config,state,adapter=True).to(device).eval()
        self.base.requires_grad_(False)
        self.correction=(SplineCorrection() if arm=='S' else NeuralCorrection()).to(device)
        self.physics=self.base.physics
        self.work=dict(base_value_positions=0,base_first_derivative_positions=0,base_second_derivative_components=0,
                       correction_value_positions=0,correction_first_derivative_positions=0,correction_second_derivative_components=0,
                       thermal_face_first_derivative_positions=0,cache_builds=0)

    def base_cache(self,q,order=0):
        q=q.detach().clone().requires_grad_(order>0)
        f=base_fields(self.base,q,phase_latent=True)
        result={k:f[k] for k in ('temperature','phase','phase_latent','delta_logit')}
        self.work['base_value_positions']+=len(q)
        if order:
            result['psi_grad']=_gradient(f['phase_latent'],q)
            result['temperature_grad']=_gradient(f['temperature'],q)
            self.work['base_first_derivative_positions']+=len(q)
        if order>=2:
            dp=result['psi_grad']
            result['psi_lap']=_gradient(dp[:,0],q)[:,0]+_gradient(dp[:,1],q)[:,1]
            self.work['base_second_derivative_components']+=2*len(q)
        self.work['cache_builds']+=1
        return {k:v.detach() for k,v in result.items()}

    def delta(self,q,order=0,spline=None):
        self.work['correction_value_positions']+=len(q)
        if order:self.work['correction_first_derivative_positions']+=len(q)
        if order>=2:self.work['correction_second_derivative_components']+=2*len(q)
        if self.arm=='S':
            d,g,l=self.correction.jet(q,spline)
            return d,g if order else None,l if order>=2 else None
        gate=1-torch.exp(-(q[:,2]-self.physics.time_start)/self.base.startup_time) if self.arm=='G' else dark_gate(q[:,2])
        d=8*gate*self.correction(self.physics.normalize(q))
        g=_gradient(d,q) if order else None
        l=_gradient(g[:,0],q)[:,0]+_gradient(g[:,1],q)[:,1] if order>=2 else None
        return d,g,l

    def fields(self,q,*,order=0,cache=None,spline=None):
        if order and not q.requires_grad:q=q.detach().clone().requires_grad_(True)
        c=self.base_cache(q,order) if cache is None else cache
        delta,dd,lapd=self.delta(q,order,spline)
        psi=c['phase_latent']+delta; phase=torch.sigmoid(psi); s=phase*(1-phase)
        out=dict(temperature=c['temperature'],phase=phase,phase_latent=psi,delta_logit=c['delta_logit']+delta)
        if order:
            dp=c['psi_grad']+dd
            out.update(phase_grad=s[:,None]*dp,temperature_grad=c['temperature_grad'])
        if order>=2:
            out['phase_lap']=s*(c['psi_lap']+lapd+(1-2*phase)*(dp[:,:2]**2).sum(1))
        return out

    def complete_graph(self,q):
        """Independent noncached neural path, used for interface checks only."""
        if self.arm=='S':raise ValueError('Spline jets are checked against independent spline differences')
        f=base_fields(self.base,q,phase_latent=True)
        d,_,_=self.delta(q)
        return {**f,'phase_latent':f['phase_latent']+d,'phase':torch.sigmoid(f['phase_latent']+d),
                'delta_logit':f['delta_logit']+d}


class CompletionSampler:
    def __init__(self,config,physics,grid,d_seed=740129,out_seed=740229):
        self.grid=grid
        self.inside=TimeSampler(config,physics,grid,d_seed)
        self.outside=TimeSampler(config,physics,grid,out_seed)

    def sample(self,*,fixed=False,audit=False):
        result={}
        nD=64 if audit else (32 if fixed else 8)
        ncell=256 if audit else (128 if fixed else 64)
        nbc=16 if fixed or audit else 4
        for j,(lo,hi) in enumerate(SEGMENTS):
            sampler=self.inside if j==3 else self.outside
            n=nD if j==3 else (8 if fixed else 2)
            if audit and j!=3:continue
            times=lo+(np.arange(n)+sampler.rng.random(n))*(hi-lo)/n
            for t in times:
                sides={}
                for side in ('left','right','bottom','top'):
                    q=np.column_stack([sampler.rng.uniform(-1,1,nbc),sampler.rng.uniform(0,1,nbc),np.full(nbc,t)])
                    if side in ('left','right'):q[:,0]=-1 if side=='left' else 1
                    else:q[:,1]=0 if side=='bottom' else 1
                    sides[side]=q
                result[float(t)]=dict(mass=(hi-lo)/2.5/n,cells=sampler.rng.integers(self.grid.cell_count,size=ncell),sides=sides)
        # IC is identically constant, but retained for full-objective checks.
        xy=np.column_stack([self.grid.cell_x[:64],self.grid.cell_z[:64]])
        return dict(times=result,initial=xy)


class CompletionExperiment:
    def __init__(self,config,state,data,arm,device='cpu'):
        self.c,self.arm,self.device=config,arm,device
        self.model=Completion(config,state,arm,device)
        self.parameters=list(self.model.correction.parameters())
        self.grid=grid_for(self.model.physics,*config['grid'])
        self.layer=ElectricalLayer(self.grid,self.model.physics.heater_width_fraction,config['linear_tolerance'])
        self.obs=VisibleTimes(data,self.grid,self.model.physics,config,device)
        self.cache={}; self.pool=None
        self.calls=dict(adam_objective_gradient_evaluations=0,complete_objective_gradient_evaluations=0,
                        audit_objective_gradient_evaluations=0,audit_objective_evaluations=0,optimizer_updates=0)

    def cached(self,key,q,order):
        if key not in self.cache:
            c=self.model.base_cache(q,order)
            if self.arm=='S':c['spline']=self.model.correction.prepare(q)
            self.cache[key]=c
        return self.cache[key]

    def field(self,key,q,order=0):
        c=self.cached(key,q,order)
        return self.model.fields(q,order=order,cache=c,spline=c.get('spline'))

    def electric(self,t):
        p=self.model.physics
        u=float(p.waveform(torch.tensor(t,dtype=torch.float64,device=self.device)))
        if u==0:
            self.layer.backend.counts.forward_queries+=1;self.layer.backend.counts.zero_drive_queries+=1
            z=torch.zeros(self.grid.cell_count,device=self.device,dtype=torch.float64)
            return z,z
        q=coordinates(self.grid,t,device=self.device)
        f=self.field(('electric',t),q)
        return self.layer(p.conductivity(f['temperature'],f['phase']),u)

    def observation(self,group,voltage):
        i,coefficient=group;o=self.obs;p=self.model.physics
        q=o.tensor(o.q[i]);target=o.tensor(o.target[i,:,:2]);f=self.field(('obs',i),q)
        v=voltage[torch.as_tensor(o.cell,device=self.device)];weight=o.tensor(o.global_weight[i])
        pieces=dict(obs_V=coefficient*torch.dot(weight,((v-target[:,0])/p.waveform_amplitude).square()),
                    obs_T=coefficient*torch.dot(weight,((f['temperature']-target[:,1])/p.theta_transition).square()))
        use=o.visible[i]&(o.phase_weight[i]>0)
        if np.any(use):
            ix=torch.as_tensor(np.flatnonzero(use),device=self.device)
            initial=p.initial_phase(q[ix]).reshape(-1).clamp(self.c['phase_logit_epsilon'],1-self.c['phase_logit_epsilon'])
            desired=torch.logit(o.tensor(o.target[i,use,2]).clamp(self.c['phase_logit_epsilon'],1-self.c['phase_logit_epsilon']))-torch.logit(initial)
            pieces['obs_phase']=coefficient*torch.dot(o.tensor(o.phase_weight[i,use]),((f['delta_logit'][ix]-desired)/self.c['phase_logit_divisor']).square())
        else:pieces['obs_phase']=f['delta_logit'].sum()*0
        return sum(pieces.values())/3,pieces

    def residual(self,t,phys,heat):
        q=coordinates(self.grid,t,cells=phys['cells'],device=self.device,requires_grad=True)
        f=self.field(('cells',t),q,2);p=self.model.physics
        key=('flux',t)
        if key not in self.cache:
            xy,incidence=face_quadrature(self.grid,phys['cells'])
            face=torch.tensor(np.column_stack([xy,np.full(len(xy),t)]),dtype=torch.float64,device=self.device,requires_grad=True)
            grad=_gradient(head_field(self.model.base,'temperature',face),face)
            idx=torch.as_tensor(incidence,device=self.device)
            flux=self.grid.dz*(grad[idx[:,1],0]-grad[idx[:,0],0])+self.grid.dx*(grad[idx[:,3],1]-grad[idx[:,2],1])
            self.cache[key]=flux.detach()
            self.model.work['thermal_face_first_derivative_positions']+=len(xy)
        phase=f['phase'];s=phase*(1-phase)
        thermal=(f['temperature_grad'][:,2]+p.latent_ratio*f['phase_grad'][:,2]+p.volumetric_cooling*f['temperature']
                 -p.thermal_diffusivity*self.cache[key]/(self.grid.dx*self.grid.dz)
                 -p.joule_gain*heat[torch.as_tensor(phys['cells'],device=self.device)])
        phase_r=f['phase_grad'][:,2]-p.mobility(f['temperature'])*(p.interface_width**2*f['phase_lap']
                -2*p.barrier_scale*s*(1-2*phase)-6*p.thermal_drive*(p.theta_transition-f['temperature'])*s)
        return dict(thermal=thermal,phase=phase_r)

    def boundary(self,t,sides,include_constants):
        phase=thermal=torch.zeros((),dtype=torch.float64,device=self.device)
        normal={'left':(-1,0),'right':(1,0),'bottom':(0,-1),'top':(0,1)}
        for side,values in sides.items():
            q=torch.tensor(values,dtype=torch.float64,device=self.device,requires_grad=True)
            f=self.field(('bc',t,side),q,1);nx,nz=normal[side]
            phase=phase+(nx*f['phase_grad'][:,0]+nz*f['phase_grad'][:,1]).square().mean()
            if include_constants:
                bt=f['temperature'] if side=='top' else nx*f['temperature_grad'][:,0]+nz*f['temperature_grad'][:,1]+self.model.physics.thermal_robin_biot*f['temperature']
                thermal=thermal+bt.square().mean()
        return (phase+thermal)/13,phase/13,thermal/13

    def objective(self,groups,pool,calibration,*,backward=False,counter='audit',full=False):
        if self.pool is not pool:self.cache={};self.pool=pool
        key=(counter+'_objective_gradient_evaluations') if backward else 'audit_objective_evaluations'
        self.calls[key]+=1
        include_constants=full or self.arm=='G'
        a,b=calibration['aE'],calibration['bE'];lam=.1
        totals=dict.fromkeys(('observation','obs_V','obs_T','obs_phase','boundary','phase_boundary','thermal_boundary','initial','thermal','phase','objective'),0.)
        use_groups=groups if include_constants else {}
        for t in sorted(set(use_groups)|set(pool['times'])):
            phys=pool['times'].get(t);group=use_groups.get(t)
            if not include_constants and not A<t<B:continue
            voltage,heat=self.electric(t) if include_constants else (None,torch.zeros(self.grid.cell_count,dtype=torch.float64,device=self.device))
            loss=torch.zeros((),dtype=torch.float64,device=self.device)
            if group is not None:
                obs,pieces=self.observation(group,voltage);loss=loss+obs/a
                totals['observation']+=float(obs.detach())
                for k,v in pieces.items():totals[k]+=float(v.detach())
            if phys is not None:
                bc,bp,bt=self.boundary(t,phys['sides'],include_constants)
                for k,v in [('boundary',bc),('phase_boundary',bp),('thermal_boundary',bt)]:totals[k]+=phys['mass']*float(v.detach())
                loss=loss+lam*5*phys['mass']*bc/b
                residual=self.residual(t,phys,heat)
                for k,scale in [('thermal',4),('phase',5)]:
                    v=phys['mass']*(residual[k]/scale).square().mean()
                    totals[k]+=float(v.detach());loss=loss+lam*v/(3*b)
            if not torch.isfinite(loss):raise FloatingPointError('Nonfinite correction objective')
            if backward and loss.requires_grad:loss.backward()
            totals['objective']+=float(loss.detach())
        if include_constants:
            q=torch.tensor(np.column_stack([pool['initial'],np.zeros(len(pool['initial']))]),dtype=torch.float64,device=self.device)
            f=self.field(('ic',),q)
            ic=(f['temperature'].square().mean()+((f['phase']-self.model.physics.initial_phase(q).ravel())/.03).square().mean())/3
            totals['initial']=float(ic.detach());totals['objective']+=lam*float(ic.detach())/b
            if backward and ic.requires_grad:(lam*ic/b).backward()
        return torch.tensor(totals['objective'],dtype=torch.float64,device=self.device),totals

    def statistics(self):
        return dict(objectives=dict(self.calls),electrical=self.layer.backend.snapshot(),coordinate_work=dict(self.model.work))
