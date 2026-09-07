# ADR 0068: Close PHK-V2.3 LF7 with an incomplete matched screen

- `status`: `ACCEPTED_COMPLETE`
- `date`: `2026-09-08`
- `phase_id`: `PHK_V23_LF7_COMPETENCE_FILTERED_BLOCKWISE_BACKTRACKING_PHYSICS_REFINEMENT_PILOT_EXECUTE`
- `starting_head`: `e00f8767fc1d611b4cadcd0057720d1dd507f51c`
- `activation_commit`: `1dbee129d8b958accc71b97bf2ade3201587b441`
- `machine_outcome`: `LF7_MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID`
- `mechanism_outcome`: `MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID`
- `candidate`: `none`

## Decision

Close LF7 after both preregistered arms were attempted from exact LF6 DEV-R.
P0-S completed all 1,200 fixed-small-step physics updates and is a valid arm.
Its fixed-blind objective ratio was `0.6030763369`, which missed the frozen
`0.50` decrease gate, while event competence and field accuracy collapsed.
It therefore supplies bounded negative small-step-refinement evidence, not a
PINN Pareto or candidate.

P0-F attempted 150 optimizer updates and accepted its first 25-update block,
then raised a post-step rollback identity error. Forensic review found that
PyTorch Adam state loading had aliased nonempty snapshot tensors, which a later
optimizer step mutated. The initial empty-state toy test could not expose that
failure. Because it occurred after scientific updates, the arm was consumed and
was not retried. P0-F has no valid endpoint, so LF7 cannot compare filtered and
unfiltered refinement or attribute a mechanism increment.

## Engineering provenance

Two zero-update launch incidents preceded the scientific run: the launcher first
found no `python` on PATH, then passed the remote zero-step preflight but failed
to import missing `h5py`. An isolated system-site-packages environment with
pinned `h5py 3.12.1` and `scipy 1.14.1` resolved the dependency without changing
the activation bundle, scientific inputs, method or global environment.

The rollback alias fix and regression added after the run are unexecuted,
engineering-only terminal-tree changes. Executed evidence remains bound to the
activation commit and source identity; no result is reassigned to the fix.

## Evidence and authority boundary

The valid P0-S arm may support only a bounded negative result: smaller fixed
steps reduced the blind physics objective by about 39.7% but did not preserve
the event-bearing carrier. P0-F supports an identity-failure record only. Direct
`LF_ONLY` remains substantially stronger on the frozen nominal metrics. No
filter benefit, PINN Pareto, direct-baseline gain, candidate, multi-seed,
sparse/OOD/stress, SOTA or experimental claim is established.

The unique recommendation is `RETAIN_VALID_ARM_NO_MECHANISM_ATTRIBUTION`; it is
not execution authorization. `next_research_execution_authorized` is false and
stress remains `TWO_STRESS_REFERENCES_SEALED_UNREAD`.

See the LF7 [terminal closeout](../experiment/2026-09-07-phk-v23-lf7-terminal-closeout.md),
[artifact](../experiment/artifacts/20260907T144634Z-phk-v23-lf7-terminal.json)
and [manifest](../experiment/manifests/20260907T144634Z-phk-v23-lf7-terminal.json).
