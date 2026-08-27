# 文档库地图

本文件是项目文档的唯一导航入口。它只说明去哪里读、各文档能决定什么以及冲突时如何处理；它本身不授予研究执行权限，也不重述研究结论。

## 固定入口顺序

每次任务依次读取：

1. [`AGENTS.md`](../AGENTS.md)：仓库级工作规则与硬约束。
2. [`CODEX_CONTEXT.md`](../CODEX_CONTEXT.md)：精简上下文入口与按需路由。
3. 本文件：定位当前任务所需的权威文档。
4. [`governance/PINN_PCM_Norms_2026-08-14.md`](governance/PINN_PCM_Norms_2026-08-14.md)：完整项目规范。
5. [`rules.md`](../rules.md)：执行规则摘要。
6. [`active_phase.md`](../active_phase.md)：当前阶段及授权边界。
7. [`PROJECT_STATE.md`](../PROJECT_STATE.md)：当前已核验状态。
8. [`plans/NEXT_ACTIONS.md`](plans/NEXT_ACTIONS.md)：唯一 current/most-recent plan；完成态不产生新授权。

随后才按任务需要读取研究总览、ADR、实验记录、参考审查、笔记或归档。

## 当前执行入口

- 当前唯一 current plan：[PLAN-PHK-V2-V1](plans/NEXT_ACTIONS.md)。状态为 `COMPLETED_BOUNDARY_PRESERVING_ORACLE_NO_GO`；S2 已按预注册在 Oracle Gate 形成 `PHK_V2_ORACLE_NO_GO_EVENT_CONTRACT_AND_CONTROL_EXECUTION_FAILURE`，S7 完整负结果论文与复现包已交付。
- 当前阶段与授权：[active_phase.md](../active_phase.md)。PHK-V2 执行与收口授权已经消费并关闭；不再授权 solver、PINN、PHA/KC、GPU、formal、OOD 或论文扩展。付费/云端计算、凭据披露、作者联系、投稿、外部上传和 Git 远程操作仍未授权。
- 当前证据入口：[PHK-PINN R0 一手来源与 baseline 审查](references/2026-08-27-phk-pinn-primary-source-baseline-audit.md)、[baseline CPU smoke](experiment/2026-08-27-phk-v2-s1-baseline-acquisition-and-cpu-smoke.md)、[S0 program 预注册](governance/2026-08-27-phk-v2-s0-program-preregistration.md)、[S0B 对象/split freeze](governance/2026-08-27-phk-v2-s0b-object-and-split-freeze.md)与 [S2 terminal summary](../outputs/runs/20260827T-phk-v2-s2-q-terminal-summary/summary.json)。这些建立来源身份、模块 smoke 和冻结对象的 Oracle No-Go，不建立官方 baseline 论文指标复现或任何 PINN 方法证据。
- 当前 PHK-V2 制品入口：[完整论文与复现包](../paper_v2/README.md)与 [S2 终局收口](experiment/2026-08-27-phk-v2-s2-terminal-closeout.md)。包内清单、图源、链接、引用键和 claim boundary 已验证，不改变科学证据上限。
- 上一科研终点：[S2 终局收口](experiment/2026-08-26-goal-paper-one-shot-v1-s2-terminal-closeout.md)与[归档 GOAL](../archive/2026-08-27-goal-paper-one-shot-v1-complete.md)。Q0 只通过零驱动守卫；首个受驱动 QN intent 失败且已计账。该 No-Go、V1 论文和全部历史证据保持原样。
- 上一对象组合终点：[方法盲对象筛选报告](references/2026-08-26-method-blind-cleanroom-object-screen.md)与 [ADR 0042](adr/0042-close-package-a-with-method-blind-object-portfolio-no-go.md)。3/3 冻结家族在 Gate 3 最早失败，11/12 新载体后形成 `PORTFOLIO_NO_GO_PACKAGE_A_FROZEN_3_FAMILIES_11_CARRIERS`。
- 本轮已消费授权的理由与边界：[ADR 0045](adr/0045-adopt-phk-v2-strong-baseline-and-two-module-execution.md)。它曾覆盖上一完成 GOAL 的当时授权语义，现已由 Oracle No-Go 和完成包消费关闭；不撤销或改写任何旧 No-Go、失败 intent 或论文。
- 本轮全库文档状态审计：[2026-08-26 工作区文档状态对齐](governance/2026-08-26-workspace-document-state-alignment.md)。它记录全量机器巡检、当前权威面逐项审查、状态漂移和链接修复，不构成科学证据。
- 本轮论文润色整合：[2026-08-27 外部会话论文润色整合记录](notes/2026-08-27-manuscript-polish-integration.md)。它记录可读会话结论的逐项核对、接纳/拒绝边界和派生稿件身份，不构成新的科学 evidence。
- 当前论文口径与规范术语：[CONTEXT.md](../CONTEXT.md)；当前已核验事实：[PROJECT_STATE.md](../PROJECT_STATE.md)。

历史 HFO/TaOₓ/R1/R2/KC/CTH 设计与 No-Go 不再逐项列作“当前入口”。需要追溯时依次读 [ADR 索引](adr/README.md)、[研究笔记索引](notes/README.md)、[实验索引](experiment/INDEX.md)、[来源审查索引](references/README.md)和[归档索引](../archive/README.md)。其中 [HFO Q1–Q68 索引](adr/research_decisions_HFO_Q1_Q68.md)只保存历史方法形成与可移植控制合同，不定义当前对象或授权。

上述入口均不授权科研执行；能否执行只读 `active_phase.md`。

## 文档角色与权威边界

| 文档或目录 | 回答的问题 | 权威性与变更规则 |
|---|---|---|
| [`CONTEXT.md`](../CONTEXT.md) | 我们当前到底研究什么，论文如何表述？ | 当前研究设定与论文口径的单一来源；不放行动清单、授权或运行结果。 |
| [`../paper/`](../paper/README.md) | 本轮完整论文、图表、补充和复现材料在哪里？ | 本地交付制品与其哈希索引；制品完成不建立新科学主张，也不授权投稿或上传。 |
| [`../paper_v2/`](../paper_v2/README.md) | PHK-V2 的 Oracle No-Go 第二版论文与复现包在哪里？ | 英文/中文正文、图表、表格、引用、补充、复现、方法剖析和 claim audit；保持无 PINN 方法证据边界。 |
| [`adr/README.md`](adr/README.md) | 为什么接受某项研究决定？ | 保存已接受决定及理由；计划和笔记不能覆盖 ADR。编号 ADR 必须进入该索引。 |
| [`plans/NEXT_ACTIONS.md`](plans/NEXT_ACTIONS.md) | 当前或最近一次 GOAL 合同是什么状态？ | 唯一 current plan；当前记录本轮完成与原冻结合同，不能产生新授权或重新定义研究。 |
| [`experiment/`](experiment/) | 某次运行实际上做了什么、得到什么？ | 只记已执行事实。记录按日期新增，不追溯改写；新解释用新记录的 `supersedes` 指向旧记录。 |
| [`references/README.md`](references/README.md) | 哪些文献或公开数据在何时、何范围内被审查？ | 只支撑其声明的来源、查询与时间范围；刷新时新增带日期文档并说明覆盖关系。 |
| [`notes/`](notes/) | 哪些数据、方法、评价协议或想法仍未接受？ | 非权威工作笔记；不能覆盖 `CONTEXT.md`、ADR、阶段、状态、计划或实验事实。 |
| [`governance/`](governance/) | 项目规范、外部 Skill、来源和许可证如何治理？ | 管理规范与来源登记；外部 Skill 以 [`EXTERNAL_SKILLS.md`](governance/EXTERNAL_SKILLS.md) 为单一登记，不得冒充科学证据。 |
| [`../archive/`](../archive/) | 哪些历史材料被后续文件覆盖？ | 历史证据与原始产物；不再决定当前研究或行动，内容保持不回写。索引见 [`archive/README.md`](../archive/README.md)。 |

## 按任务读取

- 判断当前能否执行：读 `active_phase.md`；live plan 不能代替授权。
- 理解当前研究与论文口径：读 `CONTEXT.md`；需要决策理由时再读对应 ADR。
- 核对已运行事实：读带日期的 `experiment/` 记录，再按链接进入原始产物。
- 核对文献或公开数据：读 `references/` 中与日期和范围匹配的审查。
- 继续未接受的研究想法：只在任务明确相关时读 `notes/`。
- 追溯被覆盖的解释、失败路线或完整原始运行包：读 `archive/`，但不得把历史文件当成当前授权。

`.agents/` 中的 Skill、`.venv/`、缓存和归档运行产物不是主动文档入口；只有任务明确需要时才按项目规则读取。

## 覆盖与冲突规则

- `active_phase.md` 决定当前能否执行；live plan 只说明批准后或当前应做什么。
- `CONTEXT.md` 决定当前研究设定；ADR 记录决定形成的理由，两者不能被计划、笔记或历史报告静默改写。
- 实验记录和归档材料保持历史原貌。后续结果改变解释时，新建文档并显式写出 `supersedes` 或覆盖关系。
- `docs/plans/` 始终只保留一份 live plan；替换时将旧计划移入 `archive/`。
- 若总览、ADR、阶段、状态、计划或实验事实互相冲突，必须指出具体冲突并停止受影响动作，不得自行调和。

## 文档一致性门禁

修改 `README.md`、`active_phase.md`、`PROJECT_STATE.md`、live plan、ADR、实验索引或它们引用的路径后，运行：

```powershell
.\.venv\Scripts\python.exe -m pinn_pcm_sci.document_consistency --root .
```

门禁核对权威状态字段、唯一 live plan、文档角色、ADR 完整索引、本地链接、实验 ledger 和运行锁 ignore。失败时先修复文档逻辑链，不得以手工声明绕过。
