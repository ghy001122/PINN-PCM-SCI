# PHK-V2.3 LF6 live execution plan

- `phase_id`: `PHK_V23_LF6_EVENT_FRONTIER_RANK_BAND_AND_SAFETY_GATED_PHYSICS_PILOT_EXECUTE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `claim_status`: `CPU_F_QUALIFIED_MATCHED_EVENT_FRONTIER_AND_CONDITIONAL_PHYSICS_EXECUTION_PENDING`
- `next_research_execution_authorized`: `true`

1. Freeze the activation commit and build a content-addressed, reference-blind
   bundle containing the full CPU-F ledger.
2. Pass isolated local and remote zero-step preflight before any optimizer is
   created.
3. Run DEV-U and DEV-R for exactly 400 updates each; both endpoints vote.
4. Apply the deterministic strict/safety selection over DEV-M/U/R and run the
   selected endpoint through exactly 1200 label-free physics updates.
5. Recover and hash all artifacts, clear processes/GPU, shut down the instance,
   and verify closed TCP plus explicit SSH refusal.
6. Only then run nominal local frozen evaluation, update the single paper_v23
   package, terminalize the unique machine outcome, and push the exact whitelist.

No matched confirmation, new seed, sparse/OOD/stress task, kinetic teacher,
PJGR/R2 or submission is authorized by this live plan.
