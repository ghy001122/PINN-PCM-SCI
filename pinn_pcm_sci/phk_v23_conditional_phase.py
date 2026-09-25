"""Array-only operators for the approved fixed-temperature conditional IVP.

No reference reader, learned model, optimizer, electrical solver or new PDE.
"""
from __future__ import annotations
import numpy as np
from .phk_benchmark import _mobility, _phase_free_energy_derivatives


def phase_rhs(phase, temperature, grid, physics):
    first, _ = _phase_free_energy_derivatives(
        phase, temperature, barrier=physics['barrier_scale'],
        thermal_drive=physics['thermal_drive'], transition_temperature=physics['theta_transition'])
    return _mobility(temperature, physics)*(physics['interface_width']**2*(grid.phase_laplacian@phase)-first)


def phase_jet(phase, temperature, temperature_t, grid, physics):
    """Partial time derivative plus analytic sparse Jacobian-vector product."""
    p=physics
    first, second = _phase_free_energy_derivatives(
        phase, temperature, barrier=p['barrier_scale'], thermal_drive=p['thermal_drive'],
        transition_temperature=p['theta_transition'])
    mobility=_mobility(temperature,p)
    bracket=p['interface_width']**2*(grid.phase_laplacian@phase)-first
    velocity=mobility*bracket
    raw=(temperature-p['theta_transition'])/p['mobility_width']
    logistic=1/(1+np.exp(-np.clip(raw,-50,50)))
    mobility_T=(p['mobility_hot']-p['mobility_cold'])/p['mobility_width']*logistic*(1-logistic)*(np.abs(raw)<50)
    partial_time=mobility_T*temperature_t*bracket+mobility*6*p['thermal_drive']*temperature_t*phase*(1-phase)
    jacobian_velocity=mobility*(p['interface_width']**2*(grid.phase_laplacian@velocity)-second*velocity)
    return velocity,partial_time+jacobian_velocity


def common_derivative(values, step=0.000625):
    values=np.asarray(values,dtype=np.float64)
    if values.shape[0]<3:raise ValueError('At least three shared time nodes are required')
    out=np.empty_like(values)
    out[1:-1]=(values[2:]-values[:-2])/(2*step)
    out[0]=(-3*values[0]+4*values[1]-values[2])/(2*step)
    out[-1]=(3*values[-1]-4*values[-2]+values[-3])/(2*step)
    return out


def time_weights(times):
    times=np.asarray(times,dtype=np.float64)
    d=np.diff(times)
    if not np.all(d>0):raise ValueError('Time nodes must be strictly increasing')
    w=np.r_[d[0]/2,(d[:-1]+d[1:])/2,d[-1]/2]
    return w/w.sum()


def mean_square(values,times,volumes):
    v=np.asarray(volumes,dtype=np.float64);v=v/v.sum()
    x=np.asarray(values,dtype=np.float64)
    return float(time_weights(times)@(x*x@v))


def thermal_decision(base,coarse,fine):
    upper=max(1.05*base,base+1e-12)
    margins={'coarse':upper-coarse,'fine':upper-fine}
    delta=abs(coarse-fine)
    unresolved=((margins['coarse']>=0)!=(margins['fine']>=0) or abs(margins['fine'])<=delta)
    direction='UNRESOLVED' if unresolved else ('WITHIN_BUDGET' if margins['fine']>0 else 'EXCEEDS_BUDGET')
    return dict(base=base,coarse=coarse,fine=fine,upper=upper,margins=margins,
                observed_step_difference=delta,direction=direction,
                interpretation='step difference is sensitivity, not an error bound or confidence interval')


def reference_direction(base,coarse,fine):
    gains={'coarse':base-coarse,'fine':base-fine};delta=abs(coarse-fine)
    if min(gains.values())>delta:direction='IMPROVES'
    elif max(gains.values()) < -delta:direction='WORSENS'
    else:direction='UNRESOLVED'
    return dict(Ephi_D_80_B0=base,Ephi_D_80_coarse=coarse,Ephi_D_80_fine=fine,
                gains=gains,observed_step_difference=delta,direction=direction)
