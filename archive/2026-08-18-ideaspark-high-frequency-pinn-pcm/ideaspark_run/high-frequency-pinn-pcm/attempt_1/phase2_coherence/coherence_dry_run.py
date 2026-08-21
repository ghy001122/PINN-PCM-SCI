"""Stdlib-only numeric trace for IdeaSpark Phase 2.3."""

from __future__ import annotations

import json
import math
import statistics
import sys


def iqr(values: list[float]) -> float:
    ordered = sorted(values)
    half = len(ordered) // 2
    return statistics.median(ordered[half:]) - statistics.median(ordered[:half])


def residual_norm(vector: list[float], basis: list[list[float]]) -> float:
    projected = [0.0] * len(vector)
    for axis in basis:
        coefficient = sum(x * y for x, y in zip(vector, axis))
        projected = [p + coefficient * a for p, a in zip(projected, axis)]
    return math.sqrt(sum((x - p) ** 2 for x, p in zip(vector, projected)))


term_samples = {
    "R_V": [1.0, 2.0, 3.0, 4.0],
    "R_q": [2.0, 2.0, 2.0, 2.0],
    "R_T": [10.0, 12.0, 14.0, 16.0],
    "R_phi": [0.1, 0.2, 0.4, 0.8],
}
scales = {name: (raw if (raw := iqr(xs)) else sys.float_info.epsilon) for name, xs in term_samples.items()}

validation = {
    "switch": [0.2, 0.4],
    "topology": [0.1, 0.3],
    "energy": [0.3, 0.5],
    "event_order": [0.0, 1.0],
}
means = {name: statistics.fmean(xs) for name, xs in validation.items()}
j_val = statistics.fmean(means[name] for name in ("switch", "topology", "energy"))

responses = {
    "b1": [3.0, 0.0, 0.0],
    "b2": [0.0, 2.0, 0.0],
    "b3": [0.0, 0.0, 1.0],
    "b4": [1.0, 1.0, 0.0],
}
sensitivities = {"b1": 0.4, "b2": 0.3, "b3": 0.2, "b4": 0.5}
basis_r1 = [[1.0, 0.0, 0.0]]
basis_r2 = basis_r1 + [[0.0, 1.0, 0.0]]
deltas_r1 = {b: residual_norm(v, basis_r1) for b, v in responses.items()}
deltas_r2 = {b: residual_norm(v, basis_r2) for b, v in responses.items()}
scores_r1 = {b: sensitivities[b] * deltas_r1[b] for b in responses}
scores_r2 = {b: sensitivities[b] * deltas_r2[b] for b in responses}

# Structural counterexample to the written bound.  The Hessian assumption holds
# with L_g=0 for J(g)=g, but the formula mixes gate and response coordinates.
delta = 0.25
gradient_gate = 1.0
l_gate = 0.0
actual_removal_change = abs(1.0 - 0.0)
written_bound = abs(gradient_gate) * delta + (l_gate / 2.0) * delta**2
gate_coordinate_bound = abs(gradient_gate) + (l_gate / 2.0)

# Same one-head capacity and same packet information; uniform allocation has no
# projection, sensitivity, knee, or routing stage.
packet_benefits = [0.00, 0.60, 0.20, 0.50]
mechanism_error = 1.0 - packet_benefits[1]  # r_bulk=1 score order selects b2
naive_error = 1.0 - sum(0.25 * benefit for benefit in packet_benefits)
mechanism_error_r2 = 1.0 - packet_benefits[2]  # r_bulk=2 order selects b3

result = {
    "scales": scales,
    "validation_component_means": means,
    "J_val_three_component_scalar": j_val,
    "delta_if_r_bulk_1": deltas_r1,
    "delta_if_r_bulk_2": deltas_r2,
    "I_if_r_bulk_1": scores_r1,
    "I_if_r_bulk_2": scores_r2,
    "rank_dependent_order_r1": sorted(scores_r1, key=scores_r1.get, reverse=True),
    "rank_dependent_order_r2": sorted(scores_r2, key=scores_r2.get, reverse=True),
    "bound_counterexample": {
        "J(g)": "g",
        "delta_b": delta,
        "gradient_wrt_gate": gradient_gate,
        "L_g": l_gate,
        "actual_removal_change": actual_removal_change,
        "written_B_R": written_bound,
        "gate_coordinate_Taylor_bound": gate_coordinate_bound,
        "written_bound_violated": actual_removal_change > written_bound,
    },
    "degenerate_probes": {
        "empty_packets": "no cumulative curve; no knee; declared stop branch",
        "k_zero_local_heads": "hybrid collapses to f_bulk; no routed minority can be tested",
        "all_identical_scores": "cumulative curve is linear; no minority-forming curvature",
        "tied_max_curvature": "selection is non-unique without a stated tie rule",
        "single_packet": "no interior curvature point; declared no-knee stop",
    },
    "naive_same_budget": {
        "head_capacity": 1.0,
        "mechanism_allocation_r1": [0.0, 1.0, 0.0, 0.0],
        "mechanism_allocation_r2": [0.0, 0.0, 1.0, 0.0],
        "uniform_naive_allocation": [0.25, 0.25, 0.25, 0.25],
        "mechanism_error_r1": mechanism_error,
        "mechanism_error_r2": mechanism_error_r2,
        "naive_error": naive_error,
        "error_difference_naive_minus_mechanism_r1": naive_error - mechanism_error,
        "error_difference_naive_minus_mechanism_r2": naive_error - mechanism_error_r2,
    },
}

print(json.dumps(result, indent=2, sort_keys=True))
