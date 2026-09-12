# Experiment ledger protocol

最新：[同父三臂与电学归一化终局](2026-09-12-phk-v23-lf11-joint-terminal-closeout.md)。六个合法终点、6500 新增 Adam / 1500 完整评估；A/B 无预声明增量，D_N 未触发。

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

The specified-parent D_I/D_B/P_U comparison and conditional R/G/N are complete. All six fixed endpoints are valid, no declared contrast passes reconstruction A or limited function B, and D_N was not triggered. The [latest closeout](2026-09-12-phk-v23-lf11-joint-terminal-closeout.md) and paper_v27 preserve actual endpoint, event, contact and optimization evidence. This completed campaign authorizes no further research or publication.

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
