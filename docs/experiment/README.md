# Experiment ledger protocol

最新：[电学消元与同层强基线终局](2026-09-13-phk-v23-lf11-electrical-elimination-terminal-closeout.md)。四角色合法，3000 Adam / 600 完整评估；D_E/P_E 对 B_E A/B 通过，P_E−D_E 未达，P_F 未触发。实际 GPU 已回收关机，paper_v28 已收口。

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

## Latest bounded campaign

The shared electrical-layer E0/D_E/P_E/B_E comparison is complete. Both trained roles pass A/B against the equally solved B_E, but P_E−D_E does not; P_F was not triggered. The [latest closeout](2026-09-13-phk-v23-lf11-electrical-elimination-terminal-closeout.md) and paper_v28 preserve actual endpoints, accepted optimizers, function/phase evidence, counts and current-instance shutdown. The [V27 closeout](2026-09-12-phk-v23-lf11-joint-terminal-closeout.md) retains its six-endpoint negative comparisons and unrun D_N. Completion authorizes no new research or publication.

## Historical LF10 campaign

LF10 is complete as
`LF10_FEASIBLE_DIRECTION_SCREEN_NEGATIVE_PAPER_STRENGTHENED`. CTRL and PROJ
each retained one identity-valid 25-update safety prefix, but neither completed
the frozen 200-update screen; full/control were not run because their
prerequisite was unmet. The independent tracks established
`INTERFACE_EFFECT_STREAM_REPLICATED` and
`PHYSICS_FORGETTING_STREAM_REPLICATED`. No complete PINN Pareto or candidate
exists, stress remains sealed/unread, and no new research execution is authorized.

## G1 fixture boundary

The G1 fixture is deliberately tagged `NON_SCIENTIFIC_FIXTURE`. Its one-step
model update tests conversion, model startup, serialization, independent
evaluation, and bookkeeping only. It is neither a PINN result nor evidence
about VO2, Q-POP, or the kinetics-clock hypothesis.
