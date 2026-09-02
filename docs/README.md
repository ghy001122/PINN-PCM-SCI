# 文档库地图

本文件是项目文档的唯一导航入口。它只说明去哪里读、各文档能决定什么以及冲突时如何处理；它本身不授予研究执行权限，也不重述研究结论。

当前阶段为 PHK-V2.3 R1X 有界 clean-coupling campaign。E1 已完成并裁决为 `E1_ET_NOT_READY`，冻结机器树选择 `E2_TOP_DIRICHLET_HARD_LIFT`；AutoDL 已关机，campaign 授权保持有效并等待用户重启实例。权威入口见 [active phase](../active_phase.md)、[live plan](plans/NEXT_ACTIONS.md)、[E1 closeout](experiment/2026-09-03-phk-v23-r1x-e1-et-not-ready-closeout.md)、[ADR 0054](adr/0054-resume-r1x-after-verified-engineering-repair.md) 与原 [ADR 0053](adr/0053-activate-phk-v23-r1x-bounded-clean-coupling-campaign.md)；V2.2R/R0A/R0B/R0C/R1a 历史证据保持不变，stress 继续 sealed/unread。

R1X E1 两次历史工程启动都在模型构造前因隔离部署传递依赖缺失而终止，均不计 scientific trajectory；该历史见 [R1X engineering-blocked closeout](experiment/2026-09-02-phk-v23-r1x-engineering-blocked-closeout.md)。传递依赖闭合后，修复的 E1 有效运行 300 updates 并按 readiness policy 停止，现已计入 1/3 条 exploration。

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

- 当前唯一 current/most-recent plan：[PLAN-PHK-V2.3-R1X](plans/NEXT_ACTIONS.md)。E1 已形成 1/3 条 exploration 并裁决为 `E1_ET_NOT_READY`；下一条仅可执行 E2 top hard lift，当前等待 AutoDL 重启。
- 当前阶段与授权：[active_phase.md](../active_phase.md)。V2.2R 四臂 nominal 的
  `MVP_NO_GO_NO_BASIC_COMPETENCE` 与 R0A/R0B/R0C/R1a 证据保持冻结；R1X 已授权恢复 E1 及冻结机器树，PJGR、R2、low-fidelity、其他 seed、stress 和投稿仍未授权。
- 历史 PHK-V2.3 R1X 工程阻塞记录：[2026-09-02 R1X engineering-blocked closeout](experiment/2026-09-02-phk-v23-r1x-engineering-blocked-closeout.md)。它记录两次 pre-update 部署失败、日志哈希、0 科学轨迹、关机验证和 post-blocker isolation 回归修复；不得解释为 clean-coupling 方法失败。
- 当前 PHK-V2.3 R1X E1 结果入口：[2026-09-03 R1X E1 ET-not-ready closeout](experiment/2026-09-03-phk-v23-r1x-e1-et-not-ready-closeout.md)。它记录 300-step reference-blind warm-up、readiness 失败、产物回收/关机、本地 nominal 评价和 E2 top-hard-lift 路由；它是 non-voting development evidence。
- 当前研究身份与论文口径：[CONTEXT.md](../CONTEXT.md)。V2.2R 是 fixed-discretization
  单 seed 负面 Method-MVP；PDE loss 下降没有建立局域事件 competence，不能外推为 PINN
  全局失败、continuum truth、formal OOD 或实验结论。
- 当前证据入口：[PHK-V2.1 terminal summary](../outputs/runs/20260828T-phk-v21-s1-q-terminal-summary-001/summary.json)、[S1 terminal closeout](experiment/2026-08-28-phk-v21-s1-terminal-closeout.md)、[S7 package closeout](experiment/2026-08-28-phk-v21-s7-terminal-package-closeout.md)、[最终 paper_v21 包](../paper/paper_v21/README.md)、[S0 scientific freeze](governance/2026-08-28-phk-v21-s0-scientific-contract-freeze.md)、[baseline identity audit](references/2026-08-27-phk-v2-1-baseline-reproduction-identity-audit.md)、[E1 solver selection](experiment/2026-08-27-phk-v21-e1-control-solver-selection.md)与 [E2 object selection](experiment/2026-08-27-phk-v21-e2-engineering-object-selection.md)。它们固定 Oracle No-Go、完整终局包与 neural 下游未到达。
- 当前 V2.2R 决定入口：[ADR 0048](adr/0048-activate-phk-v22r-v11-four-arm-sprint-after-gpu-profile.md)。它在 profile 后激活 v1.1 四臂冲刺并只覆盖 [ADR 0047](adr/0047-adopt-phk-v22r-rapid-method-rescue-sprint.md) 的后续执行语义，不改写 V2.1 terminal evidence 或既有 profile 事实。
- 当前 PHK-V2.3 R0A 决定入口：[ADR 0049](adr/0049-activate-phk-v23-r0a-cpu-diagnostics.md)。它只激活一次 CPU 诊断，保留 V2.2R terminal No-Go，并明确禁止 GPU、训练、stress、R0B、R1 与 PJGR。
- 当前 PHK-V2.3 R0A 结果入口：[2026-08-30 R0A CPU diagnostics closeout](experiment/2026-08-30-phk-v23-r0a-cpu-diagnostics-closeout.md)。机器裁决为 `R0A_INCONCLUSIVE`；artifact 和 manifest 分别固定完整诊断量与运行身份。
- 当前 PHK-V2.3 R0B 决定入口：[ADR 0050](adr/0050-activate-phk-v23-r0b-first-switch-175-minimal-v2.md)。它只激活一次 175-step reference-blind temporal-precursor replay，要求产物回收后立即关机，并禁止把结果写成因果 root 或方法增益。
- 当前 PHK-V2.3 R0B 结果入口：[2026-08-31 R0B first-switch closeout](experiment/2026-08-31-phk-v23-r0b-first-switch-175-closeout.md)。机器裁决识别 `GRADIENT_STARVATION` 为最早持续前兆；AutoDL 已关闭，factorial 未触发，nominal appendix 为 non-voting，两份 stress references 继续 sealed/unread。
- 当前 PHK-V2.3 R0C 决定入口：[ADR 0051](adr/0051-activate-phk-v23-r0c-effective-update-25-v100.md)。它只激活并已消费一次 25-step reference-blind effective-update materiality replay；禁止 reference、recovery、R1、PJGR、第二次 run 与 stress。
- 当前 PHK-V2.3 R1a 决定入口：[ADR 0052](adr/0052-activate-phk-v23-r1a-config-competence-recovery.md)。它只激活一次 standard-ConFIG shared-solver-backbone competence-recovery run；不授权第二次 run、R1b、PJGR 或 stress。
- 当前 PHK-V2.3 R1a 结果入口：[2026-08-31 R1a ConFIG closeout](experiment/2026-08-31-phk-v23-r1a-config-closeout.md)。ConFIG 在全部冻结机制节点产生 conflict-free direction，但两周期事件仍完全缺失，机器裁决为 `R1A_CONFIG_RAW_NO_COMPETENCE`。
- 当前 PHK-V2.3 R0C 结果入口：[2026-08-31 R0C effective-update closeout](experiment/2026-08-31-phk-v23-r0c-effective-update-25-closeout.md)。机器裁决为 `R0C_ADAM_PRECONDITIONING_COMPENSATES_RAW_GRADIENT`；AutoDL 已关闭，nominal/stress reference 均未读取，结果不恢复 competence 或证明方法增益。
- 当前 V2.2R 近期研究策略入口：[2026-08-29 研究策略整合](notes/2026-08-29-phk-v22r-recent-research-strategy-integration.md)。它把实时会话中的模块组合、结果故事和止损思路映射到冻结合同，只提供解释和稿后路由，不新增授权或证据。
- 当前 V2.2R stress reference 字节封存记录：
  [2026-08-29 PHK-V2.2R stress extra-fine seal](experiment/2026-08-29-phk-v22r-stress-reference-byte-seal.md)。
  它只记录生成身份、大小和 SHA256；候选冻结前没有读取场或指标。
- 当前 V2.2R 全形状工程预检：
  [2026-08-29 PHK-V2.2R full-shape CPU preflight](experiment/2026-08-29-phk-v22r-fullshape-cpu-preflight.md)。
  五臂均有限并写出完整训练产物，但该一步并发运行不参与排序或成本裁决。
- 当前 V2.2R GPU profile 收口：
  [2026-08-30 PHK-V2.2R GPU profile closeout](experiment/2026-08-30-phk-v22r-gpu-profile-closeout.md)。
  五臂均有限；strict PHA 成本门通过但增益门失败，按冻结规则退出关键路径。该 profile
  不建立四臂排序、candidate freeze 或正向方法结果。
- 当前 V2.2R P0 v1.1 对齐收口：
  [2026-08-30 PHK-V2.2R v1.1 alignment closeout](experiment/2026-08-30-phk-v22r-v11-alignment-closeout.md)。
  它记录机器合同、四臂 runner、decision/freeze、云端 run card 和验证门禁已经闭合；不把
  工程通过表述为 nominal 结果。
- 当前 V2.2R nominal 终局收口：
  [2026-08-30 PHK-V2.2R v1.1 nominal terminal closeout](experiment/2026-08-30-phk-v22r-v11-nominal-terminal-closeout.md)。
  它记录四臂完整运行、本地评价、`MVP_NO_GO_NO_BASIC_COMPETENCE`、预算和关机事实；
  [paper_v22r](../paper/paper_v22r/README.md) 保存英文导师初稿、五图与复现包。
- 当前冲刺跨工具协作与数据路由：
  [2026-08-30 sprint collaboration and data routing](governance/2026-08-30-sprint-collaboration-and-data-routing.md)。
  它规定本地、AutoDL、GitHub、Codex、ChatGPT、VSCode 与 PowerShell 的职责和文件去向，
  不产生科研授权或科学证据。
- 当前 PHK-V2 制品入口：[完整论文与复现包](../paper/paper_v2/README.md)与 [S2 终局收口](experiment/2026-08-27-phk-v2-s2-terminal-closeout.md)。包内清单、图源、链接、引用键和 claim boundary 已验证，不改变科学证据上限。
- 上一科研终点：[S2 终局收口](experiment/2026-08-26-goal-paper-one-shot-v1-s2-terminal-closeout.md)与[归档 GOAL](../archive/2026-08-27-goal-paper-one-shot-v1-complete.md)。Q0 只通过零驱动守卫；首个受驱动 QN intent 失败且已计账。该 No-Go、V1 论文和全部历史证据保持原样。
- 上一对象组合终点：[方法盲对象筛选报告](references/2026-08-26-method-blind-cleanroom-object-screen.md)与 [ADR 0042](adr/0042-close-package-a-with-method-blind-object-portfolio-no-go.md)。3/3 冻结家族在 Gate 3 最早失败，11/12 新载体后形成 `PORTFOLIO_NO_GO_PACKAGE_A_FROZEN_3_FAMILIES_11_CARRIERS`。
- 当前授权理由与边界：[ADR 0046](adr/0046-adopt-phk-v21-independent-engineering-science-contract.md)。它建立独立工程—科学双阶段合同，只覆盖旧完成态的不再执行语义；[ADR 0045](adr/0045-adopt-phk-v2-strong-baseline-and-two-module-execution.md)、PHK-V2 No-Go、失败 intent 与论文保持原样。
- 当前全库文档与研究策略审计：[2026-08-29 工作区文档与研究策略对齐](governance/2026-08-29-workspace-document-and-strategy-alignment.md)。它记录当前权威面、近期实时会话整合、角色漂移和归档链接修复，不构成科学证据。
- 上一轮全库文档状态审计：[2026-08-26 工作区文档状态对齐](governance/2026-08-26-workspace-document-state-alignment.md)。它保存当时的状态漂移、链接修复和机器巡检快照，不再代表当前 phase。
- 本轮论文润色整合：[2026-08-27 外部会话论文润色整合记录](notes/2026-08-27-manuscript-polish-integration.md)。它记录可读会话结论的逐项核对、接纳/拒绝边界和派生稿件身份，不构成新的科学 evidence。
- 当前论文目录规范与一次性云端同步边界：[2026-08-28 paper version layout GitHub sync](governance/2026-08-28-paper-version-layout-github-sync.md)。它固定 `paper/paper_vxx/` 为后续版本路径，只改变工程组织，不改变科学主张。
- 当前论文口径与规范术语：[CONTEXT.md](../CONTEXT.md)；当前已核验事实：[PROJECT_STATE.md](../PROJECT_STATE.md)。
- 本次云端精选同步边界：[2026-08-28 PHK-V2.1 GitHub 同步边界](governance/2026-08-28-phk-v21-selected-github-sync-boundary.md)。它只记录用户授权、纳入/排除范围与披露边界，不改变科学 claim。

历史 HFO/TaOₓ/R1/R2/KC/CTH 设计与 No-Go 不再逐项列作“当前入口”。需要追溯时依次读 [ADR 索引](adr/README.md)、[研究笔记索引](notes/README.md)、[实验索引](experiment/INDEX.md)、[来源审查索引](references/README.md)和[归档索引](../archive/README.md)。其中 [HFO Q1–Q68 索引](adr/research_decisions_HFO_Q1_Q68.md)只保存历史方法形成与可移植控制合同，不定义当前对象或授权。

上述入口均不授权科研执行；能否执行只读 `active_phase.md`。

## 文档角色与权威边界

| 文档或目录 | 回答的问题 | 权威性与变更规则 |
|---|---|---|
| [`CONTEXT.md`](../CONTEXT.md) | 我们当前到底研究什么，论文如何表述？ | 当前研究设定与论文口径的单一来源；不放行动清单、授权或运行结果。 |
| [`../paper/`](../paper/README.md) | 各论文版本及后续 `paper_vxx` 制品在哪里？ | 唯一论文版本根与版本路由；所有版本包统一存放在 `paper/paper_vxx/`。 |
| [`../paper/paper_v1/`](../paper/paper_v1/README.md) | GOAL-PAPER-ONE-SHOT-V1 第一版论文包在哪里？ | 英文/中文正文、图表、补充和复现材料；保持原 numerical-contract No-Go 边界。 |
| [`../paper/paper_v2/`](../paper/paper_v2/README.md) | PHK-V2 的 Oracle No-Go 第二版论文与复现包在哪里？ | 英文/中文正文、图表、表格、引用、补充、复现、方法剖析和 claim audit；保持无 PINN 方法证据边界。 |
| [`../paper/paper_v21/`](../paper/paper_v21/README.md) | PHK-V2.1 的 Oracle convergence No-Go 终局论文与复现包在哪里？ | 英文/中文正文、通俗故事、六图、表格、引用、补充、复现、baseline anatomy、claim audit 和 package manifest；保持 Sharp/PF/PINN/PHA/KC/formal 未到达边界。 |
| [`../paper/paper_v22r/`](../paper/paper_v22r/README.md) | PHK-V2.2R 四臂 nominal 负面 Method-MVP 初稿在哪里？ | 英文正文、五图、表格、补充、复现、claim audit 与研究决策记录；保持 no candidate、no confirmation、stress sealed/unread 边界。 |
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
