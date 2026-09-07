# PHK-V2.3 LF7 AutoDL deployment

This deployment is built only from the LF7 activation commit and the exact,
hash-bound inputs admitted by the LF7 data contract: the medium carrier, the
LF6 DEV-R checkpoint, the LF6 CPU-F materialized ledger and manifest, and the
LF7 CPU qualification. Unrelated working-tree files are never archived.

Before any optimizer is constructed, the remote preflight verifies the source
identity, every materialized-ledger array, all 1200 per-step physics hashes,
the fixed-blind pool, the exact V100 identity, the absence of duplicate LF7
processes, the reference-blind cloud boundary, and a fresh empty output root.
The LF7 runtime consumes the materialized arrays directly and must not invoke
Sobol or regenerate collocation coordinates.

The scientific order is fixed:

1. `P0-S`: exact DEV-R, fresh Adam, fixed small learning rate, 1200 updates;
2. `P0-F`: reload exact DEV-R, create a second fresh Adam, then run the
   competence-filtered blockwise-backtracking arm on the same 1200 batches.

`P0-F` must never inherit weights, optimizer state, RNG state, accepted-step
state, or learning rate from `P0-S`. Medium is available only for no-gradient
full-medium audits and filter decisions; it is not part of the physics loss.

Fine, extra-fine, direct LF_ONLY, frozen evaluators, stress references, and
formal OOD material are forbidden on the cloud. Local adjudication may begin
only after all cloud artifacts are recovered and verified, training and GPU
processes are zero, the instance is shut down, and SSH returns connection
refused.

The operator supplies:

- `LF7_SOURCE_IDENTITY`, exactly as emitted by `build_bundle.py`;
- `LF7_DEPLOYMENT_ROOT`, the absolute extracted activation bundle root; and
- `LF7_OUTPUT_ROOT=/root/autodl-tmp/lf7-run-20260907T144634Z`.

`run.sh` rejects any other output identity or a nonempty output root.
