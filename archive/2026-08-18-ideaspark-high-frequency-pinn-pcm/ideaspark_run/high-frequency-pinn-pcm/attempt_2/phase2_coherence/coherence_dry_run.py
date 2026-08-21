import json
import math


RHO = 1.0
DELTA_S = 0.02
THETA0 = [0.0, 0.0, 0.0]
TARGET = [1.0, -1.0, 0.5]
FLOOR = [0.04, 0.01, 0.0025]
LEARNING_RATE = 1.0e-5  # invented instance setting, not a candidate parameter
TOTAL_UPDATES = 70      # invented instance setting, held equal across arms


def ell(theta):
    return [(x - t) ** 2 for x, t in zip(theta, TARGET)]


ELL0 = ell(THETA0)
EPS0 = [max(x, f) for x, f in zip(ELL0, FLOOR)]


def epsilon(s):
    return [e0 ** (1.0 - s) * ef ** s for e0, ef in zip(EPS0, FLOOR)]


def loss_margin(theta, s):
    values = ell(theta)
    eps = epsilon(s)
    ratios = [x / e for x, e in zip(values, eps)]
    loss = RHO * sum(max(r - 1.0, 0.0) ** 2 for r in ratios)
    margin = 1.0 - max(ratios)
    return loss, margin, ratios


def gradient(theta, s):
    values = ell(theta)
    eps = epsilon(s)
    out = []
    for x, t, value, e in zip(theta, TARGET, values, eps):
        ratio = value / e
        if ratio <= 1.0:
            out.append(0.0)
        else:
            out.append(RHO * 4.0 * (ratio - 1.0) * (x - t) / e)
    return out


def train(theta, schedule):
    state = list(theta)
    for s, updates in schedule:
        for _ in range(updates):
            g = gradient(state, s)
            state = [x - LEARNING_RATE * dx for x, dx in zip(state, g)]
    loss, margin, ratios = loss_margin(state, schedule[-1][0])
    return {"theta": state, "loss": loss, "margin": margin, "ratios": ratios}


# Reading A: current-stage feasibility authorizes an immediate midpoint trial.
midpoint_trial = 0.5
midpoint_state = loss_margin(THETA0, midpoint_trial)

# Reading B: bisection is over coordinates already feasible at the unchanged theta.
lo, hi = 0.0, 1.0
while hi - lo > DELTA_S:
    mid = (lo + hi) / 2.0
    if loss_margin(THETA0, mid)[1] >= 0.0:
        lo = mid
    else:
        hi = mid
current_feasible = {
    "accepted_s": lo,
    "first_rejected_s": hi,
    "accepted_margin": loss_margin(THETA0, lo)[1],
    "rejected_margin": loss_margin(THETA0, hi)[1],
}

# Same-budget T5 toy: direct terminal penalty versus one defensible staged reading.
direct = train(THETA0, [(1.0, TOTAL_UPDATES)])
stages = [0.5, 0.75, 0.875, 0.9375, 0.96875, 0.984375, 1.0]
staged = train(THETA0, [(s, TOTAL_UPDATES // len(stages)) for s in stages])

zero_floor_error = None
try:
    _ = 0.0 / 0.0
except ZeroDivisionError as exc:
    zero_floor_error = type(exc).__name__ + ": " + str(exc)

report = {
    "initial": {
        "ell": ELL0,
        "epsilon_0": EPS0,
        "loss_s0": loss_margin(THETA0, 0.0)[0],
        "margin_s0": loss_margin(THETA0, 0.0)[1],
    },
    "reading_A_midpoint_before_training": {
        "next_s": midpoint_trial,
        "loss": midpoint_state[0],
        "margin": midpoint_state[1],
        "ratios": midpoint_state[2],
    },
    "reading_B_bisect_currently_feasible": current_feasible,
    "zero_floor_probe": zero_floor_error,
    "t5_same_budget": {
        "learning_rate": LEARNING_RATE,
        "updates_each": TOTAL_UPDATES,
        "direct_s1": direct,
        "staged_midpoints": staged,
        "worst_ratio_difference_staged_minus_direct": max(staged["ratios"]) - max(direct["ratios"]),
        "classification": "instance_contingent",
    },
}

print(json.dumps(report, indent=2, sort_keys=True))
