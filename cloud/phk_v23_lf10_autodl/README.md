# PHK-V2.3 LF10 AutoDL deployment

LF10 deploys only the activation commit and the reference-blind inputs needed
by the three independent scientific tracks: the medium carrier, exact LF3-T0
and LF6 DEV-R checkpoints, the inherited materialized strong-physics ledger,
the LF10 materialized audit/replication ledger, and the passed zero-update LF10
CPU qualification. The bundle is built from committed bytes and never archives
the surrounding dirty worktree.

One process owns the frozen work order while isolating arm-local failures:

1. matched CTRL and PROJ feasible-direction screens;
2. conditional continuation of the selected screen endpoint when a screen passes;
3. LF4 DEV-G/DEV-M paired replications for sampling streams 23 and 29;
4. LF6 physics-forgetting replications for streams 23 and 29.

The runner must continue every unaffected mandatory track after an arm-local
scientific failure. All coordinates and batch identities are materialized before
deployment; runtime sampling is forbidden. Medium data may supply the common
audit gradients and acceptance checks, but never the physics loss. Fine,
extra-fine, direct `LF_ONLY`, frozen local evaluators, stress, and OOD assets are
forbidden on the cloud.

The operator supplies `LF10_SOURCE_IDENTITY`, `LF10_DEPLOYMENT_ROOT`,
`LF10_CPU_QUALIFICATION`, and an empty absolute `LF10_OUTPUT_ROOT` below
`/root/autodl-tmp/` whose basename begins with `lf10-run-`. After the process
exits, recover the declared artifacts once, verify their content manifest and
that training/GPU compute processes are zero, then shut down the instance before
local threshold and strong-baseline adjudication.
