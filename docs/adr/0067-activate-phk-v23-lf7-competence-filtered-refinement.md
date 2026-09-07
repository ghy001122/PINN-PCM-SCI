# ADR 0067: Activate PHK-V2.3 LF7 competence-filtered refinement pilot

- `status`: `ACCEPTED_ACTIVE`
- `date`: `2026-09-07`
- `phase_id`: `PHK_V23_LF7_COMPETENCE_FILTERED_BLOCKWISE_BACKTRACKING_PHYSICS_REFINEMENT_PILOT_EXECUTE`
- `starting_head`: `e00f8767fc1d611b4cadcd0057720d1dd507f51c`
- `prior_art`: `NO_EXACT_FUNCTIONAL_COLLISION_FOUND_WITHIN_BOUNDED_6_ITEM_SCOPE`

## Decision

Run two matched physics refinements from the exact LF6 DEV-R endpoint. P0-S is
the fixed small-step pure-physics control. P0-F uses the same start, first
learning rate, materialized physics batches and optimizer family, but accepts a
25-step block only when the blind physics objective strictly decreases and the
full-medium event/field competence conjunction remains valid; rejection restores
model, optimizer and random states before retrying the same block at the next of
five dyadic learning rates.

The comparison asks whether a smaller step alone is sufficient or whether a
function-space competence filter is load-bearing near DEV-R. Medium is read only
for block acceptance, never differentiated, so P0-F is a
`MULTIFIDELITY_COMPETENCE_FILTERED_PINN_REFINEMENT`, not a label-free method.
Its filter, rollback and backtracking primitives are attributed constrained-
optimization components; only the project-specific event-competence composition
is screened here, without claiming classical filter or trust-region convergence.

Both arms must run within the frozen bounds unless P0-F exhausts all five scales
at one block or reaches the attempted-update cap. A negative arm cannot suppress
the other. Fine, extra-fine, direct LF_ONLY and frozen evaluators remain local and
unread until all cloud outputs are recovered and the V100 instance is shut down;
stress remains sealed. Multi-seed, sparse/OOD/stress work and any weak-form or
control-volume backup require a new EXECUTE authorization.

Machine semantics are frozen in the LF7 program, method, data and decision
contracts; the CPU qualification must pass before the activation commit.
