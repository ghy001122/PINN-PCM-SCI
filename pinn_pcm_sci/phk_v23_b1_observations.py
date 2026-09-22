"""B1 field-visible observations; no hidden phase labels enter the training bundle.

The original coordinate measure is restricted, never re-trapezoided over a gap.
No reference data, learned initializer or model evaluation is used by export.
"""
from pathlib import Path
import numpy as np
import torch
from scipy.interpolate import PchipInterpolator, RegularGridInterpolator
from scipy.special import expit, logit

from .phk_v23_lf11_elimination import ObservationTimes
from .phk_v23_lf11_elimination_physics import fields

SCHEMA = 'lf11-b1-visible-fields-v1'
WINDOW = (1.01, 2.02)


def visible_bundle(arrays, window=WINDOW):
    """Select field values BEFORE phase statistics or interface identification."""
    x,z,t = (np.array(arrays[k], copy=True) for k in ('x','z','time'))
    q = np.array(arrays['coordinates'], copy=True)
    original = arrays['targets']
    base = np.array(arrays['global_probability'], copy=True)
    ns = len(x)*len(z)
    assert len(q) == len(t)*ns
    hidden = np.zeros(len(q), bool) if window is None else (q[:,2] >= window[0]) & (q[:,2] <= window[1])
    visible = ~hidden
    phi_indices = np.flatnonzero(visible)
    phi_values = np.array(original[visible,2], copy=True)
    # NaN denotes absence in temporary coordinate-aligned storage, never a label.
    ph = np.full(len(q), np.nan)
    ph[visible] = phi_values
    ph = ph.reshape(len(t),len(z),len(x))
    mask = visible.reshape(ph.shape)
    corners = [(slice(dt,len(t)-1+dt),slice(dz,len(z)-1+dz),slice(dx,len(x)-1+dx))
               for dt in (0,1) for dz in (0,1) for dx in (0,1)]
    all_visible = np.logical_and.reduce([mask[c] for c in corners])
    straddles = np.zeros(all_visible.shape, bool)
    # Compute min/max only AFTER rejecting cells with any missing corner.
    vals = [ph[c][all_visible] for c in corners]
    straddles[all_visible] = (np.minimum.reduce(vals) < .5) & (np.maximum.reduce(vals) >= .5)
    it,iz,ix = np.where(straddles)
    lower = np.column_stack([x[ix],z[iz],t[it]])
    upper = np.column_stack([x[ix+1],z[iz+1],t[it+1]])
    volume = np.prod(upper-lower,axis=1)
    endpoints = np.zeros(ph.shape)
    for dt in (0,1):
        for dz in (0,1):
            for dx in (0,1):
                np.add.at(endpoints,(it+dt,iz+dz,ix+dx),volume/8)
    endpoints[0] = 0
    if endpoints.sum():
        endpoints /= endpoints.sum()
    phase_global = base*visible*(q[:,2] > t[0])
    phase_global /= phase_global.sum()
    phase_weight = phase_global.copy()
    if endpoints.sum():
        phase_weight = .5*phase_global+.5*endpoints.ravel()
    global_weight = base/base.sum()
    return dict(schema_id=np.asarray(SCHEMA),x=x,z=z,time=t,coordinates=q,
        potential=np.array(original[:,0],copy=True),temperature=np.array(original[:,1],copy=True),
        phase_indices=phi_indices,phase_values=phi_values,global_probability=global_weight,
        phase_global_probability=phase_global,phase_probability=phase_weight,
        interface_probability=endpoints.ravel(),cell_lower=lower,cell_upper=upper,
        straddles=straddles.astype(np.uint8),phase_visible=visible,
        window=np.asarray([] if window is None else window,dtype=float))


def export(source, destination):
    # Do not read or inherit old full-label interface fields/statistics.
    with np.load(source,allow_pickle=False) as f:
        arrays={k:f[k] for k in ('x','z','time','coordinates','targets','global_probability')}
    bundle=visible_bundle(arrays)
    destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('xb') as stream:
        np.savez_compressed(stream,**bundle)
    return statistics(bundle)


def statistics(a):
    q=a['coordinates'];positive=q[:,2]>a['time'][0];vis=a['phase_visible']
    ns=len(a['x'])*len(a['z'])
    vt=a['time'][vis.reshape(len(a['time']),ns).all(1)]
    hidden_times=a['time'][~vis.reshape(len(a['time']),ns).all(1)]
    before=vt[vt<WINDOW[0]];after=vt[vt>WINDOW[1]]
    return dict(schema_id=SCHEMA,phase_missing_window=list(WINDOW),
        field_positive_labels={'potential':int(positive.sum()),'temperature':int(positive.sum()),
                               'phase':int((positive&vis).sum())},
        missing_positive_phase=int((positive&~vis).sum()),
        observation_times=len(a['time']),spatial_nodes=ns,spatial_shape=[len(a['x']),len(a['z'])],
        phase_visible_times=len(vt),phase_hidden_times=hidden_times.tolist(),
        last_visible_before=float(before[-1]),first_visible_after=float(after[0]),
        endpoint_present={str(v):bool(np.any(a['time']==v)) for v in WINDOW},
        analytic_ic_positions=ns,analytic_ic_scalar_values=3*ns,
        phase_ic_observation_weight=float(a['phase_probability'][~positive].sum()),
        interface_cells=len(a['cell_lower']),interface_endpoints=int(np.count_nonzero(a['interface_probability'])),
        teacher_current_power_exported=False,hidden_phase_exported=False,
        interpolation_uses_post_window_phase=True,claim='offline reconstruction of one developed protocol')


class VisibleData:
    def __init__(self,path=None,*,arrays=None):
        if arrays is None:
            with np.load(path,allow_pickle=False) as f:
                arrays={k:f[k] for k in f.files}
        self.arrays=arrays
        if str(arrays['schema_id']) != SCHEMA or 'targets' in arrays:
            raise ValueError('B1 requires a field-grouped visible-only bundle')
        self.coordinates=arrays['coordinates']
        self.prob=arrays['global_probability']
        self.endpoint_prob=arrays['interface_probability']
        self.has_interface=bool(self.endpoint_prob.sum())
        self.targets=np.full((len(self.coordinates),3),np.nan)
        self.targets[:,:2]=np.column_stack([arrays['potential'],arrays['temperature']])
        self.targets[arrays['phase_indices'],2]=arrays['phase_values']
        self.visible=arrays['phase_visible'].astype(bool)
        np.testing.assert_array_equal(np.flatnonzero(self.visible),arrays['phase_indices'])
        if not np.isfinite(self.targets[:,:2]).all() or not np.isfinite(arrays['phase_values']).all():
            raise ValueError('nonfinite visible label')


class VisibleTimes(ObservationTimes):
    def __init__(self,data,grid,physics,config,device):
        self.data,self.config,self.device=data,config,device
        self.times=data.arrays['time'];self.nt=len(self.times)
        self.ns=len(data.coordinates)//self.nt
        self.q=data.coordinates.reshape(self.nt,self.ns,3)
        self.target=data.targets.reshape(self.nt,self.ns,3)
        self.visible=data.visible.reshape(self.nt,self.ns)
        self.global_weight=data.prob.reshape(self.nt,self.ns)
        self.phase_weight=data.arrays['phase_probability'].reshape(self.nt,self.ns)
        self.proposal=.5*(self.global_weight.sum(1)+self.phase_weight.sum(1))
        self.proposal/=self.proposal.sum()
        ix=np.rint((self.q[0,:,0]-grid.x_min)/grid.dx-.5).astype(int)
        iz=np.rint((self.q[0,:,1]-grid.z_min)/grid.dz-.5).astype(int)
        if np.any(ix<0) or np.any(ix>=grid.nx) or np.any(iz<0) or np.any(iz>=grid.nz):
            raise ValueError('sparse coordinates outside training grid')
        self.cell=iz*grid.nx+ix
        np.testing.assert_allclose(self.q[0,:,:2],np.column_stack([grid.cell_x[self.cell],grid.cell_z[self.cell]]),rtol=0,atol=1e-12)

    def loss(self,model,group,voltage,role):
        i,coefficient=group
        q=self.tensor(self.q[i]);target=self.tensor(self.target[i,:,:2])
        f=fields(model,q,potential=role=='P_F')
        v=f['potential'] if role=='P_F' else voltage[torch.as_tensor(self.cell,device=self.device)]
        weight=self.tensor(self.global_weight[i])
        pieces=dict(obs_V=coefficient*torch.dot(weight,((v-target[:,0])/model.physics.waveform_amplitude).square()),
                    obs_T=coefficient*torch.dot(weight,((f['temperature']-target[:,1])/model.physics.theta_transition).square()))
        use=self.visible[i] & (self.phase_weight[i]>0)
        if np.any(use):
            ix=torch.as_tensor(np.flatnonzero(use),device=self.device)
            initial=model.physics.initial_phase(q[ix]).reshape(-1).clamp(self.config['phase_logit_epsilon'],1-self.config['phase_logit_epsilon'])
            desired=torch.logit(self.tensor(self.target[i,use,2]).clamp(self.config['phase_logit_epsilon'],1-self.config['phase_logit_epsilon']))-torch.logit(initial)
            pieces['obs_phase']=coefficient*torch.dot(self.tensor(self.phase_weight[i,use]),
                ((f['delta_logit'][ix]-desired)/self.config['phase_logit_divisor']).square())
        else:
            pieces['obs_phase']=f['delta_logit'].sum()*0.
        return sum(pieces.values())/3,pieces

    def head_observations(self,head):
        q=self.q.reshape(-1,3);target=self.target.reshape(-1,3)
        if head=='phase':
            weight=self.phase_weight.ravel();use=self.data.visible & (weight>0)
        else:
            weight=self.global_weight.ravel();use=np.ones(len(q),bool)
        return q[use],target[use],weight[use]


def visible_baseline(data,grid,times,physics):
    """Frozen PCHIP-time/linear-space B_logit, independently visible field nodes."""
    a=data.arrays;x,z,t=a['x'],a['z'],a['time'];times=np.asarray(times)
    ns=len(x)*len(z)
    visible=data.visible.reshape(len(t),ns)
    if not np.all(visible == visible[:,:1]):
        raise ValueError('Frozen B1 masks complete spatial slices only')
    phase_times=visible[:,0]
    q0=data.coordinates[:ns]
    initial=physics.initial_phase(torch.tensor(q0,dtype=torch.float64)).numpy().reshape(len(z),len(x))
    # Only selected rows are transformed. Missing entries never reach logit.
    phase=data.targets.reshape(len(t),len(z),len(x),3)[phase_times,...,2]
    delta=logit(np.clip(phase,1e-8,1-1e-8))-logit(np.clip(initial,1e-8,1-1e-8))[None]
    delta[0]=0
    values={'temperature':PchipInterpolator(t,a['temperature'].reshape(len(t),len(z),len(x)),axis=0)(times),
            'phase':PchipInterpolator(t[phase_times],delta,axis=0)(times)}
    sx=np.r_[physics.x_min,x,physics.x_max];sz=np.r_[physics.z_min,z,physics.z_max]
    xx,zz=np.meshgrid(grid.x_centers,grid.z_centers,indexing='xy')
    query=np.column_stack([zz.ravel(),xx.ravel()]);out={}
    for name,temporal in values.items():
        padded=np.pad(temporal,((0,0),(1,1),(1,1)),mode='edge')
        if name=='temperature':
            padded[:,:,0]/=1+physics.thermal_robin_biot*(x[0]-physics.x_min)
            padded[:,:,-1]/=1+physics.thermal_robin_biot*(physics.x_max-x[-1])
            padded[:,0,:]/=1+physics.thermal_robin_biot*(z[0]-physics.z_min)
            padded[:,-1,:]=0
        predicted=np.stack([RegularGridInterpolator((sz,sx),row,method='linear',bounds_error=True)(query) for row in padded])
        if name=='phase':
            q=np.column_stack([xx.ravel(),zz.ravel(),np.zeros(xx.size)])
            initial_out=physics.initial_phase(torch.tensor(q,dtype=torch.float64)).numpy().ravel()
            predicted=expit(predicted+logit(np.clip(initial_out,1e-8,1-1e-8))[None])
        zero=times==physics.time_start
        predicted[zero]=initial_out if name=='phase' else 0.
        out[name]=predicted
    return out
