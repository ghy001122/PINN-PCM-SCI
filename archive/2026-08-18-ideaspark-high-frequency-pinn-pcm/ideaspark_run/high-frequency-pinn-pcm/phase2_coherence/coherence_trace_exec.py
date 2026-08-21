"""Stdlib-only execution evidence for IdeaSpark Phase 2.3 T2-T5."""

from __future__ import annotations

import math
from collections import defaultdict, deque


def legendre_nodes_weights(n: int):
    """Gauss-Legendre nodes/weights on [-1, 1], computed with stdlib math."""
    nodes = [0.0] * n
    weights = [0.0] * n
    half = (n + 1) // 2
    for i in range(half):
        z = math.cos(math.pi * (i + 0.75) / (n + 0.5))
        for _ in range(100):
            p0, p1 = 1.0, z
            for k in range(2, n + 1):
                p0, p1 = p1, ((2 * k - 1) * z * p1 - (k - 1) * p0) / k
            pn = p1 if n > 1 else z
            pnm1 = p0 if n > 1 else 1.0
            dp = n * (z * pn - pnm1) / (z * z - 1.0)
            z_next = z - pn / dp
            if abs(z_next - z) < 1e-15:
                z = z_next
                break
            z = z_next
        p0, p1 = 1.0, z
        for k in range(2, n + 1):
            p0, p1 = p1, ((2 * k - 1) * z * p1 - (k - 1) * p0) / k
        pn = p1 if n > 1 else z
        pnm1 = p0 if n > 1 else 1.0
        dp = n * (z * pn - pnm1) / (z * z - 1.0)
        w = 2.0 / ((1.0 - z * z) * dp * dp)
        nodes[i], nodes[n - 1 - i] = -z, z
        weights[i] = weights[n - 1 - i] = w
    return nodes, weights


NQ = 16
KFLOOR = 1.0e-3
NODES, WEIGHTS = legendre_nodes_weights(NQ)


def positive_rate(s: float) -> float:
    # A positive rate representable as kfloor + softplus(q(s)); the narrow peak
    # exposes non-monotonicity in independently rescaled finite quadrature.
    return KFLOOR + 80.0 * math.exp(-((s - 0.537) / 0.0028) ** 2)


def rescaled_gauss_tau(t: float) -> float:
    return 0.5 * t * sum(
        w * positive_rate(0.5 * t * (z + 1.0))
        for z, w in zip(NODES, WEIGHTS)
    )


def find_quadrature_counterexample():
    grid = [0.50 + i * (0.20 / 20000) for i in range(20001)]
    vals = [rescaled_gauss_tau(t) for t in grid]
    i = min(range(len(grid) - 1), key=lambda j: vals[j + 1] - vals[j])
    dt = grid[i + 1] - grid[i]
    slope = (vals[i + 1] - vals[i]) / dt
    return grid[i], vals[i], grid[i + 1], vals[i + 1], slope


def analytic_positive_basis_tau(t: float) -> float:
    # One local repair: exact integral of a positive Gaussian-basis rate.
    c, width, amplitude = 0.537, 0.0028, 80.0
    primitive = 0.5 * width * math.sqrt(math.pi) * (
        math.erf((t - c) / width) - math.erf(-c / width)
    )
    return KFLOOR * t + amplitude * primitive


def analytic_positive_basis_rate(t: float) -> float:
    return positive_rate(t)


def h_partial(x1: float, x2: float, tau: float, pulse: float) -> float:
    return (
        x1 * x1
        + x1 * x2 * tau
        + math.sin(tau)
        + tau * pulse
        + 0.5 * pulse * pulse
        + x2 * pulse
    )


def tau_map(x1: float, x2: float, t: float) -> float:
    return (1.0 + 0.2 * x1) * t + 0.1 * x2 * t * t + 0.05 * x1 * x2 * t


def pulse(t: float) -> float:
    return t * t + 0.1 * t


def composed_f(x1: float, x2: float, t: float) -> float:
    return h_partial(x1, x2, tau_map(x1, x2, t), pulse(t))


def pullback_check():
    x1, x2, t = 0.2, -0.1, 0.6
    tau = tau_map(x1, x2, t)
    p = pulse(t)
    tau_t = 1.0 + 0.2 * x1 + 0.2 * x2 * t + 0.05 * x1 * x2
    tau_tt = 0.2 * x2
    p_t, p_tt = 2.0 * t + 0.1, 2.0
    h_tau = x1 * x2 + math.cos(tau) + p
    h_p = tau + p + x2
    h_tautau = -math.sin(tau)
    h_taup = 1.0
    h_pp = 1.0
    formula_tt = (
        h_tautau * tau_t * tau_t
        + h_tau * tau_tt
        + 2.0 * h_taup * tau_t * p_t
        + h_pp * p_t * p_t
        + h_p * p_tt
    )
    ht = 2.0e-4
    finite_tt = (
        composed_f(x1, x2, t + ht)
        - 2.0 * composed_f(x1, x2, t)
        + composed_f(x1, x2, t - ht)
    ) / (ht * ht)

    grad_tau = [0.2 * t + 0.05 * x2 * t, 0.1 * t * t + 0.05 * x1 * t]
    hess_tau = [[0.0, 0.05 * t], [0.05 * t, 0.0]]
    grad_x_h_tau = [x2, x1]
    hess_x_h = [[2.0, tau], [tau, 0.0]]
    formula_hess = [[0.0, 0.0], [0.0, 0.0]]
    for i in range(2):
        for j in range(2):
            formula_hess[i][j] = (
                hess_x_h[i][j]
                + grad_x_h_tau[i] * grad_tau[j]
                + grad_tau[i] * grad_x_h_tau[j]
                + h_tautau * grad_tau[i] * grad_tau[j]
                + h_tau * hess_tau[i][j]
            )
    hx = 2.0e-4
    f00 = composed_f(x1, x2, t)
    fpp_x1 = composed_f(x1 + hx, x2, t)
    fmm_x1 = composed_f(x1 - hx, x2, t)
    fpp_x2 = composed_f(x1, x2 + hx, t)
    fmm_x2 = composed_f(x1, x2 - hx, t)
    fd11 = (fpp_x1 - 2.0 * f00 + fmm_x1) / (hx * hx)
    fd22 = (fpp_x2 - 2.0 * f00 + fmm_x2) / (hx * hx)
    fd12 = (
        composed_f(x1 + hx, x2 + hx, t)
        - composed_f(x1 + hx, x2 - hx, t)
        - composed_f(x1 - hx, x2 + hx, t)
        + composed_f(x1 - hx, x2 - hx, t)
    ) / (4.0 * hx * hx)
    finite_hess = [[fd11, fd12], [fd12, fd22]]
    max_hess_error = max(
        abs(formula_hess[i][j] - finite_hess[i][j])
        for i in range(2)
        for j in range(2)
    )
    return tau, p, formula_tt, finite_tt, formula_hess, finite_hess, max_hess_error


def acyclic_check():
    nodes = ["q", "tau", "pulse", "h", "fields", "K", "keff", "r_tau", "pde", "loss"]
    edges = [
        ("q", "tau"), ("tau", "h"), ("pulse", "h"), ("h", "fields"),
        ("fields", "K"), ("K", "keff"), ("tau", "r_tau"),
        ("keff", "r_tau"), ("fields", "pde"), ("r_tau", "loss"),
        ("pde", "loss"),
    ]
    indegree = {node: 0 for node in nodes}
    outgoing = defaultdict(list)
    for src, dst in edges:
        outgoing[src].append(dst)
        indegree[dst] += 1
    queue = deque(node for node in nodes if indegree[node] == 0)
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for dst in outgoing[node]:
            indegree[dst] -= 1
            if indegree[dst] == 0:
                queue.append(dst)
    return len(order) == len(nodes), order


def pulse_edge_check():
    edge = 0.5
    left_p, right_p = 0.0, 1.0
    tau = edge
    # A legal head under the written spec can return T=tau+p, hence jump.
    left_t = tau + left_p
    right_t = tau + right_p
    return left_t, right_t, right_t - left_t


def control_budget_check():
    p_head, p_clock = 120, 40
    candidate_active = p_head + p_clock
    strict_identity_same_head_active = p_head
    identity_with_nominal_frozen_clock = p_head + p_clock
    return candidate_active, strict_identity_same_head_active, identity_with_nominal_frozen_clock


def naive_comparison():
    # Same h/g parameter allocation and information; naive deletes only r_tau.
    k_value = 20.0
    naive_tau_t = 1.0
    kinetics_tau_t = math.sqrt(k_value * k_value + KFLOOR * KFLOOR)
    naive_dxi_dtau = k_value / naive_tau_t
    kinetics_dxi_dtau = k_value / kinetics_tau_t
    return k_value, naive_tau_t, kinetics_tau_t, naive_dxi_dtau, kinetics_dxi_dtau


def manufactured_residual_point():
    """One complete scalar-point pass through fields, constitutive terms, and residuals."""
    x1, x2, t = 0.2, -0.1, 0.6
    tau = tau_map(x1, x2, t)
    p = pulse(t)
    tau_t = 1.0 + 0.2 * x1 + 0.2 * x2 * t + 0.05 * x1 * x2
    tau_x1 = 0.2 * t + 0.05 * x2 * t
    tau_x2 = 0.1 * t * t + 0.05 * x1 * t
    lap_tau = 0.0
    p_t = 2.0 * t + 0.1
    v = x1 + 2.0 * x2 + 0.1 * tau
    temp = 1.0 + 0.5 * tau + p
    xi = 0.2 + 0.1 * tau
    e = (-(1.0 + 0.1 * tau_x1), -(2.0 + 0.1 * tau_x2))
    sigma, kappa, rho_c = 2.0, 1.0, 1.0
    current = (sigma * e[0], sigma * e[1])
    q_joule = current[0] * e[0] + current[1] * e[1]
    electric_residual = -sigma * 0.1 * lap_tau
    temp_t = 0.5 * tau_t + p_t
    heat_residual = rho_c * temp_t - kappa * 0.5 * lap_tau - q_joule
    xi_t = 0.1 * tau_t
    k_xi = xi_t  # manufactured constitutive value; phase residual zero is forced.
    phase_residual = xi_t - k_xi
    k_eff = math.sqrt(k_xi * k_xi + KFLOOR * KFLOOR)
    clock_residual = tau_t - k_eff
    return v, temp, xi, e, current, q_joule, electric_residual, heat_residual, phase_residual, clock_residual


def main():
    t0, v0, t1, v1, slope = find_quadrature_counterexample()
    repair_grid = [0.50 + i * (0.20 / 20000) for i in range(20001)]
    repair_slopes = [
        (analytic_positive_basis_tau(repair_grid[i + 1]) - analytic_positive_basis_tau(repair_grid[i]))
        / (repair_grid[i + 1] - repair_grid[i])
        for i in range(len(repair_grid) - 1)
    ]
    tau, p, formula_tt, finite_tt, formula_hess, finite_hess, max_hess_error = pullback_check()
    is_dag, topo = acyclic_check()
    edge_left, edge_right, edge_jump = pulse_edge_check()
    cand_p, identity_active, identity_nominal = control_budget_check()
    k_value, naive_rate, kinetics_rate, naive_slope, kinetics_slope = naive_comparison()
    manufactured = manufactured_residual_point()

    print(f"Q16_COUNTEREXAMPLE t0={t0:.5f} tau0={v0:.9f} t1={t1:.5f} tau1={v1:.9f} slope={slope:.6f}")
    print(f"Q16_POSITIVE_INTEGRAND sampled_min_lower_bound={KFLOOR:.6f}")
    print(f"ANALYTIC_POSITIVE_BASIS min_grid_slope={min(repair_slopes):.6f} min_exact_rate={min(analytic_positive_basis_rate(t) for t in repair_grid):.6f}")
    print(f"PULLBACK_POINT tau={tau:.9f} pulse={p:.9f}")
    print(f"TIME_SECOND formula={formula_tt:.9f} finite_difference={finite_tt:.9f} abs_error={abs(formula_tt-finite_tt):.3e}")
    print(f"SPACE_HESSIAN formula={formula_hess}")
    print(f"SPACE_HESSIAN finite_difference={finite_hess} max_abs_error={max_hess_error:.3e}")
    print(f"ACYCLIC is_dag={is_dag} topological_order={topo}")
    print(f"PULSE_EDGE left_T={edge_left:.6f} right_T={edge_right:.6f} unregulated_jump={edge_jump:.6f}")
    print(f"IDENTITY_CONTROL candidate_active={cand_p} same_head_identity_active={identity_active} nominal_with_frozen_clock={identity_nominal}")
    print(f"NAIVE_SAME_BUDGET K={k_value:.3f} naive_tau_t={naive_rate:.6f} kinetics_tau_t={kinetics_rate:.6f} naive_abs_dxi_dtau={naive_slope:.6f} kinetics_abs_dxi_dtau={kinetics_slope:.6f}")
    print("MANUFACTURED_POINT V={:.6f} T={:.6f} xi={:.6f} E={} J={} QJ={:.6f} r_e={:.6f} r_T={:.6f} r_xi={:.6f} r_tau={:.6f}".format(*manufactured))


if __name__ == "__main__":
    main()
