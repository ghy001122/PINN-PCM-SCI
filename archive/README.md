# 归档索引

`archive/` 保存已被后续文档覆盖但仍需追溯的历史报告、原始运行、缓存、失败尝试和负面证据。归档内容不再决定当前研究设定、状态、授权或下一步，且不得为了配合新解释而追溯改写。

## 已归档材料

| 归档包 | 内容 | 当前覆盖关系 |
|---|---|---|
| [`2026-08-18-ideaspark-high-frequency-pinn-pcm/`](2026-08-18-ideaspark-high-frequency-pinn-pcm/) | IdeaSpark 完整原始运行包及当时的综合审查报告 | 历史执行事实由 [`docs/experiment/2026-08-18-ideaspark-workflow-run.md`](../docs/experiment/2026-08-18-ideaspark-workflow-run.md) 索引；当前研究设定由 [`CONTEXT.md`](../CONTEXT.md) 和已接受 ADR 覆盖。 |
| [`2026-08-19-pre-execution-qpop-qualification-plan.md`](2026-08-19-pre-execution-qpop-qualification-plan.md) | 用户批准正式执行前、等待 Q-POP 资格化计划批准的旧 live plan | 由当前 [`docs/plans/NEXT_ACTIONS.md`](../docs/plans/NEXT_ACTIONS.md) 覆盖；不再决定授权或行动。 |
| [`2026-08-20-g2-quota-recovery-bounded-resume-plan.md`](2026-08-20-g2-quota-recovery-bounded-resume-plan.md) | 额度恢复后获批的一次环境集成与条件 native smoke 旧 live plan | 授权已由失败 run `20260820T142429Z-smoke-g2-env-final-001` 消耗；当前状态由 [`docs/plans/NEXT_ACTIONS.md`](../docs/plans/NEXT_ACTIONS.md) 与 [`docs/experiment/2026-08-20-g2-quota-recovery-closeout.md`](../docs/experiment/2026-08-20-g2-quota-recovery-closeout.md) 覆盖。 |
| [`2026-08-20-g2-quota-recovery-terminal-blocked-plan.md`](2026-08-20-g2-quota-recovery-terminal-blocked-plan.md) | pybind11 sdist/provider 角色错误触发后的终局阻塞旧 live plan | 用户通过 grill-with-docs 明确选择保留 Q-POP 并批准一次 provider 修正路线；当前状态由 [`docs/plans/NEXT_ACTIONS.md`](../docs/plans/NEXT_ACTIONS.md) 与 [`docs/experiment/2026-08-20-g2-provider-correction-authorization.md`](../docs/experiment/2026-08-20-g2-provider-correction-authorization.md) 覆盖。 |
| [`2026-08-21-g2-provider-correction-execution-plan.md`](2026-08-21-g2-provider-correction-execution-plan.md) | 用户 A/A/A 决策批准的 provider 修正与单次 clean integration 旧 live plan | 授权已由失败 run `20260820T160113Z-smoke-g2-env-provider-final-002` 消耗；当前状态由 [`docs/plans/NEXT_ACTIONS.md`](../docs/plans/NEXT_ACTIONS.md) 与 [`docs/experiment/2026-08-21-g2-provider-correction-closeout.md`](../docs/experiment/2026-08-21-g2-provider-correction-closeout.md) 覆盖。 |
| [`2026-08-21-strong-raw-event-capability-plan.md`](2026-08-21-strong-raw-event-capability-plan.md) | N1 强 raw 能力门及失败即关闭 Q-POP PINN 的旧 live plan | N1、N2 与预声明备用 N3B 均已执行并触发停止条件；由当前 [`docs/plans/NEXT_ACTIONS.md`](../docs/plans/NEXT_ACTIONS.md) 与 [`docs/experiment/2026-08-21-n1-n3b-terminal-closeout.md`](../docs/experiment/2026-08-21-n1-n3b-terminal-closeout.md) 覆盖。 |
| [`2026-08-21-bounded-negative-closeout-plan.md`](2026-08-21-bounded-negative-closeout-plan.md) | N1/N2/N3B 触发停止条件后的有界负面收口旧 live plan | 用户随后明确批准一条恢复独立动态电子序参量的 R4 机制修正路线；由当前 [`docs/plans/NEXT_ACTIONS.md`](../docs/plans/NEXT_ACTIONS.md) 覆盖，原负面证据继续有效。 |
| [`2026-08-21-qpop-r4-dynamic-order-signal-plan.md`](2026-08-21-qpop-r4-dynamic-order-signal-plan.md) | 恢复动态电子序参量的 R4 固定信号门旧 live plan | R4 smoke 通过，但两次固定 pilot 均数值不收敛；作者参考信号审计与 raw-v3 修复后能力门也已收口。当前状态由 [`docs/plans/NEXT_ACTIONS.md`](../docs/plans/NEXT_ACTIONS.md) 与 [`docs/experiment/2026-08-21-r4-and-raw-v3-closeout.md`](../docs/experiment/2026-08-21-r4-and-raw-v3-closeout.md) 覆盖。 |

该包中的主要入口：

- [旧综合审查报告](2026-08-18-ideaspark-high-frequency-pinn-pcm/docs/ideaspark_comprehensive_audit_report.md)
- [完整原始运行目录](2026-08-18-ideaspark-high-frequency-pinn-pcm/ideaspark_run/)

独立文献审查现位于 [`docs/references/`](../docs/references/)，当前接受决策位于 [`docs/adr/`](../docs/adr/)。未来若文档失效，应在新文档中显式声明覆盖关系，再将旧文档整体移入本目录；旧实验事实和失败证据不得删除。
