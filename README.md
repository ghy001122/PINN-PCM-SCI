# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料/器件”的纯软件研究项目。目标是以可复现、证据闭合的方式推进到中科院二区 SCI 定位的论文初稿；该定位不是接收承诺，合成数值证据也不等同于实验验证。

## 当前状态

- `phase_id`: `PHK_V21_COMPLETE_ORACLE_NO_GO`
- `lifecycle_state`: `COMPLETED`
- `blocker_id`: `NONE`
- `authorization_scope`: `PHK_V21_EXECUTION_CONSUMED_AND_CLOSED`
- `claim_status`: `PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN_NO_BASELINE_OR_METHOD_EVIDENCE`

PHK-V2 remains complete at its preregistered Oracle No-Go. In the independent PHK-V2.1 route, E1 repaired the control solver, E2 selected a repeatable-event engineering candidate, and S1 completed all 14 frozen qualification intents. Nominal event, hard guards, controls and exact replay were valid, but the event-time component did not contract monotonically from fine to extra-fine. The route therefore stopped before Sharp/PF replication or any PINN training. The complete bounded terminal package is now fixed without rewriting PHK-V2.

当前 [PLAN-PHK-V2.1-V1](docs/plans/NEXT_ACTIONS.md)已按最早停止门完成。[S1 terminal closeout](docs/experiment/2026-08-28-phk-v21-s1-terminal-closeout.md)与 [terminal summary](outputs/runs/20260828T-phk-v21-s1-q-terminal-summary-001/summary.json)固定 `PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN`；[S7 closeout](docs/experiment/2026-08-28-phk-v21-s7-terminal-package-closeout.md)和[最终 paper_v21 包](paper/paper_v21/README.md)固定完整英文/中文论文、图表、补充、复现和主张边界。当前没有新的 research execution 授权。

[ADR 0046](docs/adr/0046-adopt-phk-v21-independent-engineering-science-contract.md)只覆盖旧完成态“不得开始新执行”的授权语义。[PHK-V2 terminal summary](outputs/runs/20260827T-phk-v2-s2-q-terminal-summary/summary.json)、[旧 S0B freeze](docs/governance/2026-08-27-phk-v2-s0b-object-and-split-freeze.md)和[PHK-V2 论文包](paper/paper_v2/README.md)继续证明旧路线没有 neural floor、strong raw、PHA-MF、KC、组合、GPU、formal 或 OOD 方法证据。

上一 [GOAL-PAPER-ONE-SHOT-V1 完成合同](archive/2026-08-27-goal-paper-one-shot-v1-complete.md)、`SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO`、完整第一版[论文包](paper/paper_v1/README.md)、精选 GitHub 同步记录和所有历史 No-Go 保持原样。所有论文版本统一由 [paper 版本索引](paper/README.md)路由；PHK-V2.1 完成态不授权新求解/训练、投稿、外部上传、额外 Git 远程操作、付费/云端计算或直接并入 GPL/Penn 限制源码。

当前授权读 [active_phase.md](active_phase.md)，已核验事实读 [PROJECT_STATE.md](PROJECT_STATE.md)，研究与论文口径读 [CONTEXT.md](CONTEXT.md)，完整文档路由读 [docs/README.md](docs/README.md)。
