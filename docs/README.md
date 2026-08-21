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
8. [`plans/NEXT_ACTIONS.md`](plans/NEXT_ACTIONS.md)：唯一仍生效的 live plan。

随后才按任务需要读取研究总览、ADR、实验记录、参考审查、笔记或归档。

## 文档角色与权威边界

| 文档或目录 | 回答的问题 | 权威性与变更规则 |
|---|---|---|
| [`CONTEXT.md`](../CONTEXT.md) | 我们当前到底研究什么，论文如何表述？ | 当前研究设定与论文口径的单一来源；不放行动清单、授权或运行结果。 |
| [`adr/README.md`](adr/README.md) | 为什么接受某项研究决定？ | 保存已接受决定及理由；计划和笔记不能覆盖 ADR。编号 ADR 必须进入该索引。 |
| [`plans/NEXT_ACTIONS.md`](plans/NEXT_ACTIONS.md) | 现在下一项有界工作是什么？ | 唯一 live plan；只描述下一步、准入、产物和停止条件，不能产生授权或重新定义研究。 |
| [`experiment/`](experiment/) | 某次运行实际上做了什么、得到什么？ | 只记已执行事实。记录按日期新增，不追溯改写；新解释用新记录的 `supersedes` 指向旧记录。 |
| [`references/`](references/) | 哪些文献或公开数据在何时、何范围内被审查？ | 只支撑其声明的来源、查询与时间范围；刷新时新增带日期文档并说明覆盖关系。 |
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
