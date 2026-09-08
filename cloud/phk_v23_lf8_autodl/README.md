# PHK-V2.3 LF8 AutoDL deployment

The LF8 bundle is built only from the activation commit plus five exact,
hash-bound inputs: the medium audit carrier, the LF6 DEV-R checkpoint, the LF6
materialized physics ledger and its manifest, and the passed LF8 zero-update CPU
qualification. Unrelated working-tree content is never archived.

Before the runner starts, the remote preflight verifies activation-commit source
bytes, the bundle identity, every materialized-ledger array, all 1200 physics
batches, the fixed-blind pool, DEV-R metadata, the exact V100 identity, the
reference-blind cloud boundary, duplicate processes, and a fresh empty output
root. Runtime Sobol/collocation generation is forbidden.

The core runner owns one ordered scientific process:

1. mandatory `P0_FSTAR_IDENTITY_CORRECT_COMPETENCE_FILTER` from exact DEV-R;
2. conditional `P0_C_ACCEPTED_SCHEDULE_NO_FILTER` only if F* completes all
   1200 accepted updates with valid safety and lower fixed-blind physics loss.

The control must restart from exact DEV-R with a fresh Adam and replay the exact
accepted F* per-block learning-rate schedule over the same materialized batches.
Medium is available only for no-gradient F* accept/reject audits. It never enters
the physics loss, and the control performs no medium audit.

Fine, extra-fine, direct LF_ONLY, local evaluators, and stress references are
forbidden on the cloud. After the process exits, recover and hash all artifacts,
verify that training and GPU compute processes are zero, shut the instance down,
and require SSH connection refusal before local adjudication.

The operator supplies `LF8_SOURCE_IDENTITY`, `LF8_DEPLOYMENT_ROOT`, and an empty
absolute `LF8_OUTPUT_ROOT` under `/root/autodl-tmp/` whose basename starts with
`lf8-run-`.
