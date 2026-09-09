# PLAN-PHK-V2.3-LF10: execute feasible-direction and headline replications

- `phase_id`: `PHK_V23_LF10_EVENT_COMPETENCE_FEASIBLE_DIRECTION_AND_HEADLINE_EVIDENCE_REPLICATION_EXECUTE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `claim_status`: `CPU_QUALIFIED_GPU_RESULTS_PENDING`
- `authorization_state`: `EXPLICITLY_AUTHORIZED`
- `current_stage`: `ACTIVATION`
- `next_research_execution_authorized`: `true`
- `authorization_scope`: `MANDATORY_CTRL_PROJ_THEN_CONDITIONAL_FULL_PLUS_LF4_LF6_REPLICATIONS`
- `unique_next`: `ACTIVATE_DEPLOY_AND_EXECUTE_FROZEN_LF10`
- `preserves`: `V22R_R0A_R0B_R0C_R1A_R1X_C0_LF0_LF1_LF2_LF3_LF4_LF5_LF6_LF7_LF8_LF9_EVIDENCE`

## Execution order

1. Commit the CPU-qualified activation identity and build the committed bundle.
2. Run mandatory matched CTRL and PROJ screens.
3. If eligible, continue the selected arm to the frozen full endpoint.
4. Run LF4 interface and LF6 forgetting replications on streams 23 and 29.
5. Recover and verify artifacts, stop compute, shut down, then perform local
   frozen/direct evaluation and close LF10.

The forgetting medium audit is report-only and cannot affect optimization,
selection, stopping or checkpoint choice. Nonshared tracks continue after
another track fails. No additional seed, sparse/OOD/stress, sweep or submission
is authorized.
