# ADR 0073: Activate PHK-V2.3 LF10 feasible-direction refinement and headline replication

- `status`: `ACCEPTED_ACTIVE`
- `date`: `2026-09-09`
- `phase_id`: `PHK_V23_LF10_EVENT_COMPETENCE_FEASIBLE_DIRECTION_AND_HEADLINE_EVIDENCE_REPLICATION_EXECUTE`
- `starting_head`: `06d1d2121c8d0fd6db13c12356568650083be4f3`

## Decision

Run mandatory matched `CTRL` and `PROJ` screens from exact LF6 DEV-R. Both use
the same strong-physics Adam proposal and materialized medium audit batches;
`PROJ` alone projects each trainable head onto its linearized event-competence
constraints. Every audit ratio is normalized by exact DEV-R evaluated on the
identical batch and accepted step. The medium audit never enters the physics
loss.

After the direction screen, continue a qualifying arm conditionally to the
frozen full path. Independently complete LF4 interface-exposure replications and
LF6 physics-forgetting replications on streams 23 and 29; the forgetting
medium evaluation is report-only and cannot select, stop, or alter training.
The authorized scope is
`MANDATORY_CTRL_PROJ_THEN_CONDITIONAL_FULL_PLUS_LF4_LF6_REPLICATIONS`.

The user's explicit LF10 EXECUTE instruction supersedes LF9's terminal
`NO_MORE_RESCUE` recommendation only as current authorization; it does not
rewrite LF9 evidence. LF10 does not authorize new seeds beyond the frozen
replications, sparse/OOD/stress work, architecture or optimizer sweeps, or
submission. Paper evidence remains active and pending GPU results.
