# Experiment ledger protocol

最新：[W+A 连续成稿与条件演化收口](2026-09-25-integrated-manuscript-conditional-ivp-closeout.md)。两条轨迹数值资格通过；支持考虑原修正族证人搜索，原族可行性仍未知；实例已回收关闭。

历史2026-09-23：[相对相态残差与时间矩八臂开发收口](2026-09-23-relative-phase-moments-closeout.md)。八个有效终点与原生读出完成，未建立原A_w增量；全部数值检查通过，GPU已回收关闭。

历史2026-09-21：[B1第二周期相态缺测收口](2026-09-21-b1-phase-gap-sprint-closeout.md)。两个新父态、六终点与共同读出已完成；全部结果和代价保留，GPU已回收关闭。

历史2026-09-15：[完整新脉冲历史确认终局](2026-09-15-phk-v23-lf11-protocol-terminal-closeout.md)。新协议两组E均对F/projected及B_E通过A/B，严格双周期未过。两条参考/支持轨迹和四个固定终点已完成，实际GPU已回收关闭；paper_v32已收口。

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

The new finite two-pulse protocol is complete: both clean seeds pass A/B against the locked projected soft PINN and the same-solver interpolant. All strict event gates remain separate; no time-refinement branch was triggered. The [latest closeout](2026-09-15-phk-v23-lf11-protocol-terminal-closeout.md) and paper_v32 preserve endpoints, optimizer states, actual counts, pulse-history evidence and current-instance shutdown. The [original-protocol confirmation](2026-09-14-phk-v23-lf11-fullgrid-terminal-closeout.md) and [electrical-layer comparison](2026-09-13-phk-v23-lf11-electrical-elimination-terminal-closeout.md) remain historical evidence. Completion authorizes no new research or publication.

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
