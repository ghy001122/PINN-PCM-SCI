# ADR 0071: Activate PHK-V2.3 LF9 equation-routed thermal-CV refinement

- `status`: `ACCEPTED_ACTIVE`
- `date`: `2026-09-08`
- `phase_id`: `PHK_V23_LF9_EQUATION_ROUTED_THERMAL_CONTROL_VOLUME_REFINEMENT_EXECUTE`
- `starting_head`: `f16ca9db66843c04d420c077679604dd553ac036`

## Decision

Run two mandatory matched screens from exact LF6 DEV-R. `ER-S` routes each
strong-form equation, BC and IC only to its owning field head; `ER-CV` keeps the
same routing and replaces only the thermal pointwise residual with the direct
space-time control-volume energy balance. Both use the same materialized strong
stream, frozen CV ledger, competence filter and phase-frozen schedule.

Only a screen that completes 200 accepted updates with field/event preservation
and blind strong/CV improvement may continue to a filtered 1,200-update path.
The cloud trigger is `PRELOCAL_INTERNAL_PARETO`: it may authorize the matched
no-filter control but is not the complete result. `COMPLETE_INTERNAL_PINN_PARETO`
additionally requires shutdown-before-local frozen evaluation; direct `LF_ONLY`
remains the paper-value baseline.

This decision tests whether thermal drift comes from cross-equation parameter
gradients or the pointwise thermal functional. It does not alter the physical
object, coefficients, network, event gates or sealed stress references, and it
does not authorize later sparse, seed, OOD/stress or phase-weak-form work.
