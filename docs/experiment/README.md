# Experiment ledger protocol

This directory stores compact, reviewable facts for every attempted run. Raw
checkpoints and arrays stay under `outputs/runs/<run_id>/` and are not evidence
unless a finalized manifest points to them.

## Required lifecycle

1. Assign a globally unique `run_id` and, for formal work, write the frozen
   intent before execution.
2. Run only the registered tier and scientific role.
3. Finalize exactly one immutable manifest in `manifests/<run_id>.json`, even
   when the attempt fails or is interrupted.
4. Append exactly one matching row to `index.jsonl` and regenerate `INDEX.md`.
5. Preserve failed attempts. A permitted infrastructure replay receives a new
   run ID and records `replay_of`; corrections use `supersedes` rather than
   rewriting history.

The machine ledger is `index.jsonl`; `INDEX.md` is only its generated human
view. Smoke and pilot entries never vote in formal adjudication. A run's
`evidence_identity` and `claim_status` define what it may support.

## Current bounded campaign

LF10 is ACTIVE after `LF10_CPU_QUALIFICATION_PASS` with zero scientific updates.
The frozen campaign runs matched CTRL/PROJ feasible-direction screens, a
conditional selected full path, and mandatory LF4/LF6 streams 23/29 headline
replications. Cloud execution remains reference-blind; local direct/frozen
evaluation follows recovery and shutdown. No LF10 scientific result exists yet.

## G1 fixture boundary

The G1 fixture is deliberately tagged `NON_SCIENTIFIC_FIXTURE`. Its one-step
model update tests conversion, model startup, serialization, independent
evaluation, and bookkeeping only. It is neither a PINN result nor evidence
about VO2, Q-POP, or the kinetics-clock hypothesis.
