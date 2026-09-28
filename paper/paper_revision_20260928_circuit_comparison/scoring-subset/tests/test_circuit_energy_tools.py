"""Synthetic mathematical checks only; no scientific trajectories are loaded."""
import unittest

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.interpolate import CubicSpline, PchipInterpolator, PPoly

from scripts.circuit_energy_tools import prediction_energy, reference_energy, euler_energy_check


def saved_polynomial(pp, origin=0., scale=1e-6):
    return {"polynomial_coefficients": pp.c, "polynomial_breakpoints": pp.x,
            "time_origin": np.asarray(origin), "time_scale": np.asarray(scale)}


def gauss_energy(pred, left, right, vin, rl, c):
    """Independent four-point quadrature of p*I, split at every polynomial break."""
    pp = PPoly(pred["polynomial_coefficients"], pred["polynomial_breakpoints"], extrapolate=False)
    origin, scale = float(pred["time_origin"]), float(pred["time_scale"])
    a, b = (left - origin) / scale, (right - origin) / scale
    x, w = leggauss(4)
    result = np.zeros(pp.c.shape[-1])
    for lo, hi in zip(pp.x[:-1], pp.x[1:]):
        lo, hi = max(lo, a), min(hi, b)
        if hi <= lo:
            continue
        tau = (lo + hi) / 2 + (hi - lo) / 2 * x
        voltage = pp(tau)
        current = (np.asarray(vin) - voltage) / rl - c * pp.derivative()(tau) / scale
        result += scale * (hi - lo) / 2 * (w @ (voltage * current))
    return result


class CircuitEnergyTests(unittest.TestCase):
    def test_constant_and_linear_energy_units(self):
        t = np.array([0., 0.1, 0.4, 1., 2.]) * 1e-6
        values = np.column_stack((np.full(len(t), 2.), 1. + 5e5 * t))
        vin, rl, c = np.array([9., 11.]), 12000., 1.4534619293e-10
        a, b = .17e-6, 1.63e-6
        for scale in (1e-6, 1.):
            pred = saved_polynomial(CubicSpline(t / scale, values), scale=scale)
            got = prediction_energy(pred, a, b, vin, rl, c)
            slope = 5e5
            int_p = (b - a) + slope / 2 * (b*b - a*a)
            int_p2 = (b - a) + slope * (b*b - a*a) + slope*slope / 3 * (b**3 - a**3)
            expected = np.array([(9.*2. - 4.) * (b - a) / rl,
                                 (11.*int_p - int_p2) / rl - c / 2 * ((1.+slope*b)**2 - (1.+slope*a)**2)])
            np.testing.assert_allclose(got, expected, rtol=2e-14, atol=1e-24)
            np.testing.assert_allclose(got, gauss_energy(pred, a, b, vin, rl, c), rtol=2e-14, atol=1e-24)

    def test_cubic_nonuniform_last_interval_partition_and_gauss(self):
        obs = np.r_[np.arange(196) * 102.4e-9, 20e-6]
        self.assertAlmostEqual((obs[-1] - obs[-2]) * 1e9, 32., places=9)
        tau = obs / 1e-6
        values = np.column_stack((1. + .1*tau - .004*tau**2 + .00012*tau**3,
                                  2. - .08*tau + .009*tau**2 - .00013*tau**3))
        vin, rl, c = [9., 12.5], 12000., 1.4534619293e-10
        for interpolate in (CubicSpline, PchipInterpolator):
            pred = saved_polynomial(interpolate(tau, values, extrapolate=False))
            full = prediction_energy(pred, obs[0], obs[-1], vin, rl, c)
            intervals = np.array([prediction_energy(pred, a, b, vin, rl, c) for a,b in zip(obs[:-1], obs[1:])])
            np.testing.assert_allclose(full, np.sum(intervals, axis=0), rtol=2e-14, atol=1e-23)
            for a,b in ((obs[0],obs[-1]), (.153e-6,17.392e-6), (obs[-2],obs[-1])):
                np.testing.assert_allclose(prediction_energy(pred,a,b,vin,rl,c),
                                           gauss_energy(pred,a,b,vin,rl,c), rtol=4e-14, atol=1e-23)

    def test_reference_offgrid_and_partition(self):
        t = np.array([0., 1., 3., 4.]) * 1e-6
        power = np.column_stack(([0., 2., 2., 0.], [1., -1., 3., 5.])) * 1e-3
        got = reference_energy(t,power,.5e-6,3.5e-6)
        # Linear POWER: first column pieces area .75+4+.75 mW*us.
        # Second column: -.25+2+1.75 mW*us = 3.5 nJ.
        np.testing.assert_allclose(got, [5.5e-9,3.5e-9], rtol=2e-15, atol=1e-24)
        pieces = [.0e-6,.5e-6,1.8e-6,3.5e-6,4.e-6]
        total = np.sum([reference_energy(t,power,a,b) for a,b in zip(pieces[:-1],pieces[1:])],axis=0)
        np.testing.assert_allclose(total,np.trapezoid(power,t,axis=0),rtol=2e-15,atol=1e-24)
        np.testing.assert_array_equal(reference_energy(t,power,2e-6,2e-6),[0.,0.])

    def test_euler_identity_signs_and_cancellation(self):
        t = np.array([0., 1., 2.7, 4.2, 6.]) * 1e-9
        v = np.column_stack(([2.,2.001,1.999,2.003,2.002], [0.,.001,.002,.003,.004]))
        vin, rl, c = np.array([9., 1.2]), 12000., 1e-10
        h = np.diff(t)[:,None]
        chosen_kappa = np.column_stack((np.full(len(t)-1,1e-7),np.full(len(t)-1,-2e-7)))
        device = np.empty_like(v)
        device[:-1] = (vin-v[:-1])/rl-c*np.diff(v,axis=0)/h-chosen_kappa
        device[-1] = [2e-4,-1e-5]
        rows = euler_energy_check(t,v,device,vin,rl,c)
        for j,row in enumerate(rows):
            self.assertTrue(row['valid'])
            self.assertGreater(row['discrete_correction_J'],0)
            expected_kappa = np.sum(h[:,0]*v[:-1,j]*chosen_kappa[:,j])
            self.assertAlmostEqual(row['kappa_term_J'],expected_kappa,delta=1e-28)
            expected = row['voltage_input_J']-row['capacitor_change_J']+row['discrete_correction_J']-row['kappa_term_J']
            self.assertEqual(row['rhs_J'],expected)
            self.assertGreater(abs(row['left_J']-(expected-2*row['discrete_correction_J'])),row['tolerance_J'])
            self.assertAlmostEqual(row['trapezoid_J'],reference_energy(t,v*device,t[0],t[-1])[j],delta=1e-28)
        # Nearly zero Id is cancellation of load/capacitive terms, not zero
        # arithmetic scale. No large relative-to-small-error tolerance is fitted.
        linear_t=np.arange(1001)*1e-9
        linear_v=(1e6*linear_t)[:,None]
        linear_device=(1.2-linear_v)/rl-c*1e6
        self.assertTrue(euler_energy_check(linear_t,linear_v,linear_device,1.2,rl,c)[0]['valid'])

    def test_domain_validation_and_scalar_shape(self):
        pp=CubicSpline([0.,1.,2.,3.],[2.,2.,2.,2.])
        pred=saved_polynomial(pp)
        self.assertEqual(prediction_energy(pred,0.,3e-6,9.,12000.,1e-10).shape,(1,))
        np.testing.assert_array_equal(prediction_energy(pred,1e-6,1e-6,9.,12000.,1e-10),[0.])
        for a,b in ((-1e-15,1e-6),(0.,3.1e-6),(2e-6,1e-6)):
            with self.assertRaises(ValueError):prediction_energy(pred,a,b,9.,12000.,1e-10)
        with self.assertRaises(ValueError):reference_energy([0.,1.],[1.,2.],-.1,.5)
        with self.assertRaises(ValueError):euler_energy_check([0.,0.],[1.,1.],[0.,0.],9.,12000.,1e-10)


if __name__ == '__main__':
    unittest.main()
