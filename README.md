# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料/器件”的纯软件研究项目。目标是以可复现、证据闭合的方式推进到中科院二区 SCI 定位的论文初稿；该定位不是接收承诺，合成数值证据也不等同于实验验证。

## 当前状态

- `phase_id`: `GOAL_PAPER_ONE_SHOT_V1_COMPLETE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `authorization_scope`: `ONE_SHOT_LOCAL_RESEARCH_EXECUTION_CONSUMED_AND_CLOSED`
- `claim_status`: `SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO_NO_ORACLE_EVENT_OR_METHOD_EVIDENCE`

用户批准的 [GOAL-PAPER-ONE-SHOT-V1](docs/plans/NEXT_ACTIONS.md) 一次性本地研究执行授权已经消费并关闭。S0/S2 均在新结果前冻结；S1 实际审阅 13 个一手载体（其中 10 个首次进入项目，使用新增预算 `10/12`）并完成 `2/2` 深审，两个来源对象路线均按预注册硬门关闭。透明合成路线的 Q0 零驱动守卫随后通过，但首个受驱动 QN intent 按冻结 Newton 上限执行失败且已计账；没有 rescue、生产重跑或阈值改动。最终有界裁决为 `SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO`，并已按自动 fallback 完成 `CLEANROOM_BENCHMARK_AND_METHOD_LIMITS_MANUSCRIPT` 的[全套本地交付](paper/README.md)。

S1 的来源与新颖性结论见[有界前审报告](docs/references/2026-08-26-goal-paper-one-shot-v1-s1-source-legal-novelty-review.md)，实际数值边界见 [S2 终局收口](docs/experiment/2026-08-26-goal-paper-one-shot-v1-s2-terminal-closeout.md)。Q0 只证明零驱动实现与产物链守卫；没有跨分辨率 oracle、双周期事件、strong raw、PINN/CTH、GPU 或 formal 证据。该 No-Go 只约束本次冻结数值合同，不是缺陷输运物理或 PINN 的一般失败。历史 No-Go 均保持冻结。

完整论文初稿、实际结果、六幅最终图的 PNG/PDF、主表、13 项参考文献、补充材料、复现说明和主张边界自检均已交付；[包清单](paper/package-manifest.json)覆盖除自身外 32 个文件。该制品完成不改变科学证据边界。2026-08-27 经用户另行明确授权，182 个精选变更文件已同步至本仓库 `main`；[同步记录](docs/governance/2026-08-27-selected-github-sync.md)列明范围与排除项。该一次性同步授权已消费，不授权投稿、额外上传、PR、release 或后续 Git 远程动作。

当前授权读 [active_phase.md](active_phase.md)，已核验事实读 [PROJECT_STATE.md](PROJECT_STATE.md)，研究与论文口径读 [CONTEXT.md](CONTEXT.md)，完整文档路由读 [docs/README.md](docs/README.md)。旧包证据见[方法盲对象筛选报告](docs/references/2026-08-26-method-blind-cleanroom-object-screen.md)与 [ADR 0042](docs/adr/0042-close-package-a-with-method-blind-object-portfolio-no-go.md)；一次性目标采纳理由见 [ADR 0044](docs/adr/0044-adopt-goal-paper-one-shot-v1.md)。
