# PLAN-PHK-V2.3-LF9: equation-routed strong versus thermal-CV refinement

- `phase_id`: `PHK_V23_LF9_EQUATION_ROUTED_THERMAL_CONTROL_VOLUME_REFINEMENT_EXECUTE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `claim_status`: `CPU_QUALIFIED_GPU_MECHANISM_UNTESTED`
- `authorization_state`: `EXPLICIT_EXECUTE_ACTIVE`
- `current_stage`: `ACTIVATION_READY`
- `next_research_execution_authorized`: `true`
- `unique_next`: `RUN_ER_S_AND_ER_CV_FIXED_SCREENS`
- `preserves`: `V22R_R0A_R0B_R0C_R1A_R1X_C0_LF0_LF1_LF2_LF3_LF4_LF5_LF6_LF7_LF8_EVIDENCE`

## Execute now

1. Commit the qualified LF9 implementation and frozen inputs.
2. Deploy only that activation identity and execute both mandatory matched screens.
3. Complete both screen endpoints before mechanism adjudication.
4. If either passes, continue the selected filtered arm to 1,200 accepted updates or
   its preregistered valid stall.
5. Run the no-filter control only if the selected filtered endpoint reaches
   `PRELOCAL_INTERNAL_PARETO` on cloud-allowed evidence.
6. Recover all artifacts, clear compute processes and shut down the instance before
   frozen local evaluation and direct-`LF_ONLY` comparison.

## Decision boundary

The local evaluator converts a cloud trigger into
`COMPLETE_INTERNAL_PINN_PARETO`; the two terms are not interchangeable. Negative
screens or a valid stall are scientific outcomes and close the corresponding route.
No unregistered rescue, sparse task, seed, OOD/stress or submission is authorized.
