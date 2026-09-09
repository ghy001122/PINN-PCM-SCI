# ADR 0074: Close PHK-V2.3 LF10 with replicated headline evidence and no extended feasible direction

- `status`: `ACCEPTED_COMPLETE`
- `date`: `2026-09-09`
- `phase_id`: `PHK_V23_LF10_EVENT_COMPETENCE_FEASIBLE_DIRECTION_AND_HEADLINE_EVIDENCE_REPLICATION_EXECUTE`
- `starting_head`: `06d1d2121c8d0fd6db13c12356568650083be4f3`
- `activation_commit`: `f5e05f4dec416df2a3598e433d4edcb9f7ba299c`
- `machine_outcome`: `LF10_FEASIBLE_DIRECTION_SCREEN_NEGATIVE_PAPER_STRENGTHENED`
- `mechanism_outcome`: `NO_EXTENDED_FEASIBLE_PATH_FOUND`
- `interface_replication_outcome`: `INTERFACE_EFFECT_STREAM_REPLICATED`
- `forgetting_replication_outcome`: `PHYSICS_FORGETTING_STREAM_REPLICATED`
- `candidate`: `none`

## Decision

Close LF10 after both identity-valid direction screens retained one safe
25-update prefix but failed to reach the frozen 200-update screen requirement.
CTRL attempted 150 updates and stopped on temperature preservation; PROJ
attempted 147 and stopped when its temperature projection became infeasible
under the frozen norm cap. Both endpoints had the same blind-physics ratio
`0.9891315882`. Thus LF10 found local safe descent, but no extended feasible
path and no load-bearing increment from event-competence projection. The
conditional full path and its control were not run because no screen qualified;
they are not failed trajectories.

The independent evidence tracks did close two paper-level uncertainties. Across
streams 17/23/29, the interface-band effect met its predeclared replication
rule, and pure strong-physics forgetting also met its replication rule. The
threshold grid preserved the formal machine outcome and direct `LF_ONLY` led
the mean-symmetric-difference predicate in all 375 evaluated role-grid
comparisons. These results strengthen the
bounded interface-exposure and physics-forgetting narrative, not a positive
PINN-refinement claim.

## Consequence and authority boundary

The terminal route name is
`FINALIZE_REPLICATED_INTERFACE_AND_FORGETTING_PAPER_NO_MORE_REFINEMENT_RESCUE`;
it is a closeout routing label inferred from the frozen outcomes, not a field
that existed in the LF10 decision contract. No full PINN Pareto,
direct-`LF_ONLY` gain, candidate, SOTA, sparse/OOD/stress result or experimental
validation exists. Stress remains `TWO_STRESS_REFERENCES_SEALED_UNREAD`, and
`next_research_execution_authorized=false`.

See the LF10 [terminal closeout](../experiment/2026-09-09-phk-v23-lf10-terminal-closeout.md),
[artifact](../experiment/artifacts/20260909T101615Z-phk-v23-lf10-terminal.json),
and [manifest](../experiment/manifests/20260909T101615Z-phk-v23-lf10-terminal.json).
