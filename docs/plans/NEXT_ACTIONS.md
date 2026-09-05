# PLAN-PHK-V2.3-LF4: executing

- `phase_id`: `PHK_V23_LF4_THRESHOLD_ALIGNED_INTERFACE_BAND_MECHANISM_AND_CONDITIONAL_PHYSICS_PILOT_EXECUTE`
- `lifecycle_state`: `EXECUTING_GPU_PENDING_ACTIVATION_COMMIT`
- `blocker_id`: `NONE`
- `claim_status`: `LF4_CPU_GEOMETRY_SUPPORT_ONLY_GPU_MECHANISM_UNTESTED`
- `authorization_state`: `CURRENT_USER_EXPLICIT_EXECUTE`
- `current_stage`: `ACTIVATION_COMMIT_AND_REFERENCE_BLIND_DEPLOYMENT`
- `next_research_execution_authorized`: `true`
- `supersedes`: `PLAN_PHK_V23_LF3_TERMINAL_DISPOSITION`
- `preserves`: `V22R_R0A_R0B_R0C_R1A_R1X_C0_LF0_LF1_LF2_LF3_EVIDENCE`

## Exact sequence

1. Commit and push the passed CPU-G, frozen contracts, implementation, tests,
   prior-art closure, and activation state from the exact LF4 whitelist.
2. Build a bundle only from committed activation sources; remote zero-step
   preflight must verify V100, input hashes, source aggregate, no duplicate
   process, and absence of forbidden references.
3. Run DEV-G, DEV-M, and DEV-C to exactly 400 updates each. Complete all three.
4. Select by strict-pass, Rmin, simplicity, then phase-error precedence. If any
   arm passes entry, run P0 exactly 1200 physics updates; otherwise record P0
   `NOT_RUN` rather than failed.
5. Recover and hash all artifacts, clear processes/GPU, shut down, and verify
   connection refusal. Only then run local nominal fine/extra/LF_ONLY evaluation.
6. Update paper_v23, figures, evidence matrix, terminal closeout/state, then
   selectively commit and push the terminal result.

## Stop boundary

No post-first-step scientific retry. A pre-step engineering retry is legal only
after isolated root-cause repair with unchanged scientific identity. LF4
completion authorizes no seed, OOD, stress, confirmation arm, PJGR/R2, alternate
architecture, kinetic teacher, or submission.
