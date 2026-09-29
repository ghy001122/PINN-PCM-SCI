"""Necessary synthetic thermal checks only; no saved scientific data is loaded."""
import unittest

import numpy as np

from scripts.conditional_thermal_tools import (
    linear_convolution, power_response, segment_grid, thermal_matrix, voltage_response,
)


class ConditionalThermalTests(unittest.TestCase):
    def setUp(self):
        self.cth = 49.62776831e-12
        self.sth = .20558726e-3
        self.cap = 145.34619293e-12

    def test_constant_power_exact_solution_and_si_units(self):
        time = np.arange(1001, dtype=np.float64) * 1e-9
        A = thermal_matrix(self.sth, self.cth, 1)
        power = 1e-3
        result = power_response(time, A, lambda t: np.full(t.size, power),
                                cth=self.cth, T_base=325., T_initial=332.)
        expected = 325. + power / self.sth + (7. - power / self.sth) * np.exp(-A[0, 0] * time)
        np.testing.assert_allclose(result.temperature_K[:, 0], expected, rtol=0., atol=3e-12)
        self.assertEqual(result.temperature_K[0, 0], 332.)
        self.assertEqual(result.evolution.forcing_evaluations, 4000)
        self.assertAlmostEqual(self.cth / self.sth / 1e-9, 241.39515410633908)

    def test_two_node_common_and_differential_modes(self):
        time = np.arange(2001, dtype=np.float64) * .5e-9
        eta = .12
        A = thermal_matrix(self.sth, self.cth, 2, eta)
        q = np.array([.8e-3, .3e-3])
        initial = np.array([329., 323.])
        result = power_response(time, A, lambda t: np.tile(q, (t.size, 1)),
                                cth=self.cth, T_base=325., T_initial=initial)
        rate = self.sth / self.cth
        plus_rate, minus_rate = rate * (1. - eta), rate * (1. + eta)
        steady_plus = np.mean(q) / self.cth / plus_rate
        steady_minus = (q[0] - q[1]) / 2. / self.cth / minus_rate
        plus = steady_plus + (np.mean(initial) - 325. - steady_plus) * np.exp(-plus_rate * time)
        minus = steady_minus + ((initial[0] - initial[1]) / 2. - steady_minus) * np.exp(-minus_rate * time)
        expected = 325. + np.column_stack((plus + minus, plus - minus))
        np.testing.assert_allclose(result.temperature_K, expected, rtol=0., atol=4e-12)

    def test_voltage_variable_transform_with_coupling_and_negative_power(self):
        time = np.arange(2001, dtype=np.float64) * 1e-9
        corner = .3375e-6
        A = thermal_matrix(self.sth, self.cth, 2, .1)
        vin = np.array([11., 9.4])
        initial = np.array([325., 327.])
        start = np.array([1.2, 2.])
        before = np.array([8e6, -2e6])
        after = np.array([-.4e6, 2e6])

        def p(t):
            return start + np.minimum(t, corner)[:, None] * before + np.maximum(t - corner, 0.)[:, None] * after

        def direct_q(t):
            value = p(t)
            dp = np.where(t[:, None] < corner, before, after)
            return value * (vin - value) / 12000. - self.cap * value * dp

        self.assertLess(np.min(direct_q(time)), 0.)
        transformed = voltage_response(time, A, p, V_in=vin, R_load=12000., C=self.cap,
                                       cth=self.cth, T_base=325., T_initial=initial,
                                       breakpoints_s=[corner])
        direct = power_response(time, A, direct_q, cth=self.cth, T_base=325., T_initial=initial,
                                breakpoints_s=[corner])
        np.testing.assert_allclose(transformed.temperature_K, direct.temperature_K, rtol=0., atol=3e-11)
        np.testing.assert_array_equal(transformed.temperature_K[0], initial)
        # E includes J, the state y includes J, and Q_ref state includes K.
        np.testing.assert_allclose(transformed.evolution.values[0],
                                   self.cth * (initial - 325.) + .5 * self.cap * start**2,
                                   rtol=0., atol=0.)
        checked = voltage_response(time, A, p, V_in=vin, R_load=12000., C=self.cap,
                                   cth=self.cth, T_base=325., T_initial=initial,
                                   breakpoints_s=[corner], gauss_order=8)
        self.assertLess(np.max(np.abs(checked.temperature_K - transformed.temperature_K)), 1e-6)

    def test_partition_union_continuity_no_history_reset(self):
        time = np.array([0., .2, .8, 1., 1.5]) * 1e-8
        breaks = np.array([.15, .2, .55, .8, 1.25]) * 1e-8
        partition = segment_grid(time, breaks)
        np.testing.assert_array_equal(partition, np.unique(np.r_[time, breaks]))
        A = np.array([[4e6]])
        force = lambda t: np.column_stack((1e7 + 2e12 * t,))
        whole = linear_convolution(time, A, [2.3], force, breakpoints_s=breaks)
        left = linear_convolution(time[:3], A, [2.3], force, breakpoints_s=breaks)
        right = linear_convolution(time[2:], A, left.values[-1], force, breakpoints_s=breaks)
        np.testing.assert_allclose(whole.values, np.vstack((left.values[:-1], right.values)), rtol=0., atol=0.)
        np.testing.assert_array_equal(whole.segment_values[np.searchsorted(partition, time)], whole.values)

    def test_fixed_quadrature_and_invalid_units_fail(self):
        for order in (2, 6, 12):
            with self.assertRaises(ValueError):
                linear_convolution([0., 1e-9], [[4e6]], [0.], lambda t: t, gauss_order=order)
        with self.assertRaises(ValueError):
            thermal_matrix(self.sth, -self.cth, 1)
        with self.assertRaises(ValueError):
            thermal_matrix(self.sth, self.cth, 2, 1.)
        with self.assertRaises(ValueError):
            segment_grid([0., 1e-9, 1e-9])


if __name__ == "__main__":
    unittest.main()
