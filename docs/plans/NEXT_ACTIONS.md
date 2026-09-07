# PLAN-PHK-V2.3-LF7: authorized matched constrained refinement

- `phase_id`: `PHK_V23_LF7_COMPETENCE_FILTERED_BLOCKWISE_BACKTRACKING_PHYSICS_REFINEMENT_PILOT_EXECUTE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `claim_status`: `CPU_QUALIFIED_GPU_MECHANISM_UNTESTED`
- `authorization_state`: `EXPLICIT_EXECUTE_ACTIVE`
- `current_stage`: `GPU_DEPLOYMENT_PENDING`
- `next_research_execution_authorized`: `true`
- `unique_next`: `P0_S_1200_THEN_FRESH_P0_F`
- `preserves`: `V22R_R0A_R0B_R0C_R1A_R1X_C0_LF0_LF1_LF2_LF3_LF4_LF5_LF6_EVIDENCE`

## Ordered execution

1. Commit the CPU-qualified, source-bound activation state.
2. Build and remotely preflight the activation-commit bundle on the exact V100.
3. Run P0-S for 1,200 fixed small-step physics updates.
4. Reload exact DEV-R and run P0-F to 1,200 accepted updates or its frozen
   backtracking/attempt bound. An independent post-step arm failure must not
   suppress the other arm.
5. Recover and hash all artifacts, clear processes/GPU, shut down and verify SSH
   refusal; only then run local nominal evaluation.
6. Close paper/status/evidence, commit and push the exact whitelist.

## Stop boundary

No hyperparameter rescue, extra trajectory, seed, sparse/OOD/stress task,
weak-form/control-volume method, PJGR/R2 or submission is authorized. A terminal
result—positive or negative—must close LF7 and set next authorization false.
