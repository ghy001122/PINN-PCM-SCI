# ADR 0065: Activate PHK-V2.3 LF6 event-frontier rank-band pilot

- `status`: `ACCEPTED_ACTIVE`
- `date`: `2026-09-06`
- `phase_id`: `PHK_V23_LF6_EVENT_FRONTIER_RANK_BAND_AND_SAFETY_GATED_PHYSICS_PILOT_EXECUTE`
- `starting_head`: `9d3c22674dc6279846fa341433d36f603a0854f1`
- `cpu_gate`: `LF6_CPU_F_QUALIFICATION_PASS`
- `prior_art`: `NO_EXACT_FUNCTIONAL_COLLISION_FOUND_WITHIN_BOUNDED_6_ITEM_SCOPE`

## Decision

Run a matched, single-seed screen from exact LF3-T0. DEV-U and DEV-R retain the
same LF3 base and LF4 spatial-interface losses, optimizer, batches, endpoint
times, counts and 400-update budget. They differ only in whether the endpoint
cells are a frozen generic control or the teacher-side critical rank interval
that changes the two-percent ROI event functional. Sorting is deterministic
preprocessing and is not differentiated.

CPU-F found a 968-cell ROI and critical rank 20. Cycle-1 and cycle-2 frontier
intervals are respectively ranks 17--22 and 17--20, giving four pools of
`6/6/4/4` cells. It materialized all development, conditional physics and
fixed-blind batches before activation; the cloud runner must consume those
arrays directly and fail before optimizer construction on any identity drift.

After both development endpoints, select the first strict carrier by the
frozen precedence; otherwise select the best safety-qualified endpoint among
exact historical DEV-M, DEV-U and DEV-R. A selected endpoint must enter the
1200-update label-free physics continuation. This separates rank-mechanism
evidence from the later PINN-specific Pareto test.

The 2026-09-07 continuation authorization resolves the original deployment
omission: the exact hash-bound LF4 DEV-M checkpoint may be transferred only as
a read-only P0 fallback initialization. It is neither a new label source nor a
cloud evaluator input; DEV-G, DEV-C, fine, extra-fine, direct LF_ONLY, frozen
evaluators and stress remain forbidden.

The method remains an attributed, project-specific solver-recovery
composition. Only `DEV-R strict AND DEV-U not strict` supports the narrow
`EVENT_FRONTIER_SUPPORTED` interpretation. PINN value additionally requires
the conditional P0 and frozen post-shutdown gates.

Machine semantics are frozen in the LF6 [program](../../configs/phk_v23/program_contract_lf6_event_frontier.json),
[method](../../configs/phk_v23/method_contract_lf6_event_frontier.json),
[data](../../configs/phk_v23/data_contract_lf6_event_frontier.json), and
[decision](../../configs/phk_v23/decision_contract_lf6_event_frontier.json)
contracts. CPU evidence is recorded in the [qualification](../experiment/2026-09-06-phk-v23-lf6-cpu-qualification.md).
