# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料/器件”的纯软件研究项目。目标是以可复现、证据闭合的方式推进到中科院二区 SCI 定位的论文初稿；该定位不是接收承诺，合成数值证据也不等同于实验验证。

## 当前状态

- `phase_id`: `PHK_V2_COMPLETE_ORACLE_NO_GO`
- `lifecycle_state`: `COMPLETED`
- `blocker_id`: `NONE`
- `authorization_scope`: `PHK_V2_EXECUTION_AND_CLOSEOUT_CONSUMED_CLOSED`
- `claim_status`: `PHK_V2_ORACLE_NO_GO_EVENT_CONTRACT_AND_CONTROL_EXECUTION_FAILURE_NO_PINN_METHOD_EVIDENCE`

PHK-V2 is complete at its preregistered Oracle No-Go. Manufactured operators and the zero-drive guard passed; coarse, medium, fine, half-time-step and exact-replay nominal runs remained numerically guarded but failed the required two-cycle recovery/event contract, and qualification intent 9 ended in the frozen phase-Newton line-search failure. Intents 10–12 and every PINN/PHA/KC/GPU/formal stage are therefore not reached. The evidence-bounded V2 negative/limits manuscript and reproducibility package are complete; the execution authorization is consumed and closed.

当前 [PLAN-PHK-V2-V1](docs/plans/NEXT_ACTIONS.md)已按预注册切换表完成。R0 [一手来源与 baseline 审查](docs/references/2026-08-27-phk-pinn-primary-source-baseline-audit.md)固定了 Sharp/PF/jaxpi2/PirateNet 等来源、许可和可复现身份；隔离模块 smoke 通过，但未复现论文指标。S2 [terminal summary](outputs/runs/20260827T-phk-v2-s2-q-terminal-summary/summary.json)记录 manufactured/zero-drive 通过、nominal 数值硬守卫与 exact replay 通过、两周期 recovery/event 合同失败，以及 intent 9 的冻结 phase-Newton line-search 失败。

新路线在任何 PHK 数值结果前写入 [program contract](configs/phk_v2/program_contract.json)、[S0 预注册记录](docs/governance/2026-08-27-phk-v2-s0-program-preregistration.md)、[S0B 对象/split freeze](docs/governance/2026-08-27-phk-v2-s0b-object-and-split-freeze.md)与 [ADR 0045](docs/adr/0045-adopt-phk-v2-strong-baseline-and-two-module-execution.md)。冻结的 12-intent 梯在 intent 9 消费失败后停止，intents 10–12 未到达；没有 neural floor，也没有 strong raw、PHA-MF、KC、组合、GPU、formal 或 OOD 方法证据。完整本地 [PHK-V2 论文与复现包](paper_v2/README.md)已经交付并通过清单、链接、引用键、图源与 claim-boundary 自检。

上一 [GOAL-PAPER-ONE-SHOT-V1 完成合同](archive/2026-08-27-goal-paper-one-shot-v1-complete.md)、`SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO`、完整第一版[论文包](paper/README.md)、精选 GitHub 同步记录和所有历史 No-Go 保持原样。PHK-V2 不授权投稿、外部上传、额外 Git 远程操作、付费/云端计算或直接并入 GPL/Penn 限制源码。

当前授权读 [active_phase.md](active_phase.md)，已核验事实读 [PROJECT_STATE.md](PROJECT_STATE.md)，研究与论文口径读 [CONTEXT.md](CONTEXT.md)，完整文档路由读 [docs/README.md](docs/README.md)。
