# PLAN-PHK-V2.3-LF8: authorized competence-filter completion

- `phase_id`: `PHK_V23_LF8_IDENTITY_CORRECT_COMPETENCE_FILTER_COMPLETION_AND_SCHEDULE_ATTRIBUTION_EXECUTE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `claim_status`: `CPU_QUALIFIED_GPU_FILTER_UNTESTED`
- `authorization_state`: `EXPLICIT_EXECUTE_ACTIVE`
- `current_stage`: `ACTIVATION_COMMIT_PENDING`
- `next_research_execution_authorized`: `true`
- `unique_next`: `P0_FSTAR_THEN_CONDITIONAL_ACCEPTED_SCHEDULE_CONTROL`
- `preserves`: `V22R_R0A_R0B_R0C_R1A_R1X_C0_LF0_LF1_LF2_LF3_LF4_LF5_LF6_LF7_EVIDENCE`

## Ordered execution

1. Commit the CPU-qualified, source-bound LF8 activation state.
2. Build and remotely preflight only the activation-commit bundle and frozen inputs.
3. Run mandatory P0-F* until 1,200 accepted updates or a frozen valid-prefix stall.
4. Only after a complete safe F* path with `J_final<J0`, reload exact DEV-R and
   run the accepted-schedule control without filter/audit/rollback.
5. Recover and hash artifacts, clear training/GPU processes, shut down and verify
   SSH refusal; only then run local nominal evaluation.
6. Update paper/status/evidence, close LF8 and commit the exact whitelist.

## Stop boundary

No sixth learning-rate scale, smaller block, optimizer/weighting/replay/network
rescue, extra seed, sparse/OOD/stress, weak/control-volume execution, PJGR/R2/SRPG
or submission is authorized. A valid prefix or completed path is the scientific
endpoint; every terminal result closes LF8 and sets next authorization false.
