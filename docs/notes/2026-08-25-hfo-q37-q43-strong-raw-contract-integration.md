# HFO-NP-v1 Q37–Q43 strong-raw 与公平裁决合同整合

- `date`: `2026-08-25`
- `document_role`: `FUTURE_STRONG_RAW_CONTRACT_INTEGRATION_NOT_LIVE_PLAN`
- `status`: `ACCEPTED_PLANNING_REFINEMENT_NOT_AUTHORIZED`
- `claim_status`: `NO_NEW_SCIENTIFIC_EVIDENCE`
- `input`: ChatGPT 会话“深度论文审查”对 Q37–Q43 的对抗性回答
- `authority_relation`: 服从 `CONTEXT.md`、ADR 0031–0033、`active_phase.md` 与唯一 live plan
- `supersedes_in_part`: 先前关于 monolithic joint training、backbone 强制选优、dummy 容量匹配及 raw case 处置的默认建议
- `extends`: `2026-08-25-hfo-q30-q36-pinn-training-contract-integration.md`
- `extended_by`: `2026-08-25-hfo-q44-q48-paper-claim-and-novelty-boundary-integration.md`
- `execution_in_this_task`: `0 source search / 0 solve / 0 implementation / 0 training / 0 formal / 0 GPU`

## 1. 整合裁决

外部回答只作为规划与对抗分析输入；其中出现的论文、代码、release、许可与新颖性判断没有在本轮回源，不能升格为一手 `VERIFIED`。用户接受的是 Q37–Q43 的训练治理、计算公平与失败裁决边界：

| 问题 | 当前决定 | 对先前默认建议的影响 |
|---|---|---|
| Q37 三块耦合训练 | `REVISE_ONE_BOUNDED_QUALIFICATION` | 不默认 monolithic；一次比较 full-gradient joint 与 symmetric block-coordinate/staggered |
| Q38 最小 backbone | `ACCEPT_WITH_COMMON_FAMILY` | 三块独立参数、同一架构族、平滑激活与来源兼容的输出变换 |
| Q39 backbone 赢家 | `REVISE_ALLOW_INDETERMINATE` | 加 case×cycle 不确定性带、最坏案例、守卫与不可判定出口 |
| Q40 容量/计算公平 | `REVISE_TWO_ACTIVE_KILL_CONTROLS` | dummy 不充分；同时需要 wider-raw 与 extra-work raw |
| Q41 development 调优 | `ACCEPT_EQUAL_OPPORTUNITY_AND_COMPUTE` | 同配置机会还须服从同一实际计算上限 |
| Q42 raw competence | `REVISE_PREFROZEN_ROLES_AND_SEED_QUORUM` | 只对预冻结 method-vote case×cycle 要求全通过，禁止事后改角色 |
| Q43 失败与重跑 | `ACCEPT_TYPED_FAILURE_AND_ONE_SUPERSEDE` | 正确实现下失败计票；只有有证据的实现/共享缺陷可一次替代重跑 |

这些决定不改变证据顺序：

```text
SOURCE → EVENT → SIDE → RAW_COMPETENCE
       → TEMPORAL/SPATIAL diagnosis → ONE_METHOD_PILOT
```

也不把任何训练技巧、backbone 或耦合模式变成论文创新。

## 2. Q37：一次性 strong-raw 耦合模式资格

未来另批 strong-raw PLAN 必须在方法投票前对以下两种训练模式做一次有界比较：

1. `JOINT_FULL_GRADIENT`：输运、电学和热学三块在每个更新中同时接收完整 joint loss 的梯度；
2. `SYMMETRIC_BLOCK_COORDINATE`：按事前冻结的对称或正反向 block schedule 更新单块参数，但每个子步仍评价完整 joint loss，保留跨块 PDE、本构、IC/BC、质量、no-flux、热学与端口项，并在子步间重算耦合场。

第二种模式不是把三块拆成互不相干的 solver，也不能通过停止某块梯度来删除其物理违规。比较必须使用相同 case、support、初始化族、FP64 优化框架和实际计算账本。若只有一个模式同时通过 event 主端点、全部物理守卫、case×cycle 稳健性和预声明不确定性门，则冻结它供全部后续方法臂使用；若二者均失败或无法区分，不强选赢家，也不进入方法投票。

把给定 `c_v` 下的电学/准稳态热学交给传统求解器闭合，只能记为 `QUASISTATIC_CLOSURE_DIAGNOSTIC`。它可以回答困难主要来自 coupled optimization 还是 transport 表示，但因为不再是完整三块 PINN，不能作为正面方法或以较低误差支持 PINN claim。

本轮不冻结交替次序、子步数、资格案例数或预算。这些量必须在 G2 吞吐量已知后、生成任何 G3 intent 前一次冻结，禁止形成 2×3×多配置的无界网格搜索。

## 3. Q38：公共最小 backbone

三块继续采用：

- 同一 architecture family 和相同设计规则，但参数完全独立、无共享可训练 trunk；
- 无量纲连续坐标和协议条件；默认候选为平滑 `tanh` MLP；
- 只有来源合同允许且存在可审计解析变换时，才硬编码初态、Dirichlet 电极、浓度范围或电势 gauge；no-flux、Robin 和界面条件仍保留为公共残差与拒绝守卫；
- 若 Q32 的三臂资格比较选择 deterministic spatial Fourier，它只替换公共输入编码，不改变三块、PDE 或方法身份；
- 不为不同物理块分别搜索激活、频率或网络族，不把 SIREN、per-block architecture search 或共享 trunk 作为默认救援。

## 4. Q39：允许 `BACKBONE_INDETERMINATE`

Q32 的 raw-coordinate、有效 wider-raw 与 deterministic spatial Fourier 候选不能只按平均 loss 或平均结构误差词典序选胜者。未来资格规则至少同时要求：

1. 在全部预冻结 method-vote development case×cycle 上计算主端点和物理守卫；
2. 为非劣/优效差异给出由 development 设计冻结的不确定性带；
3. 检查最坏案例、seed 稳健性以及质量、no-flux、端口、温度与 PDE 违规；
4. 只有一个候选在上述条件下保持可接受时才冻结；
5. 候选互有胜负或不确定性带重叠且没有单一 admissible winner 时，裁决 `BACKBONE_INDETERMINATE`，不为后续方法实验强造赢家。

参数量、墙钟与简洁性只可在性能处于预声明等价带时作 tie-break，不能覆盖最坏案例或物理守卫失败。具体置信规则、实用差异带与聚合方式仍为 `UNKNOWN`。

## 5. Q40：公平控制必须真实参与计算

主要比较保持“同一冻结 base＋最小方法增量”：目标方法不得获得更好的基础编码、support、优化器或额外 development 数据。所有增量参数、额外 forward、PDE 自动微分阶次与次数、optimizer closure、峰值内存和墙钟均进入账本。

每个正面候选还必须面对两个有效 kill control：

- `PARAMETER_MATCHED_WIDER_RAW`：增加的参数真实连接到 raw 输出并参与训练，检验收益是否只是容量增加；
- `COMPUTE_MATCHED_EXTRA_WORK_RAW`：保持 raw 方法身份，用额外更新、collocation/closure 或其他预声明工作匹配候选的实际计算，检验收益是否只是更多计算。

断开输出的 dummy module 可用于测量参数存储或局部 kernel 开销，但因为不能改变函数族或优化轨迹，不能作为科学容量/计算公平控制。也不得故意缩小候选 base 来制造参数相等。

## 6. Q41：development 调优的双上限

所有臂共享冻结的物理合同、无量纲化、case/support、守卫、preflight、优化框架和评价器。每个方法允许同等数量的 method-specific development 配置，同时必须满足同一实际计算上限；只满足“配置数相同”但某臂每次贵得多，不算公平。

具体配置数、seed 数、低/高预算和吞吐量目前保持 `UNKNOWN`。它们只能在 G2/G3 计划中根据公共 pilot 的成本与方差一次冻结。选出的唯一配置在 formal 前锁定；formal case 不得参与配置筛选、权重选择或停止规则调整。

## 7. Q42：案例角色与 seed quorum 先于结果

在读取任何 PINN 结果前，将完整案例冻结为：

- `qualification`：验证实现、尺度、离散或公共训练合同，不参与方法投票；
- `method-vote development`：用于 raw competence、瓶颈诊断和 development 方法比较；
- `stress-only`：只解释已知极端行为，不进入 raw competence 全通过条件。

`RAW_COMPETENT` 要求每个预冻结 method-vote case×cycle 在预声明 seed quorum 下解析事件并通过全部守卫。结果出现后不得把失败的 method-vote case 改为 stress-only，也不得只保留成功 seed。具体 quorum 数值须依据 development 方差另行冻结；当前不写 `2/2`、`2/3` 等经验数字。

若低预算已经达到 oracle/数值不确定性地板，记 `NO_BOTTLENECK`；若高预算仍不胜任，记 `RAW_INCOMPETENT_ROUTE_NO_TEST`。只有 raw competent 且未达地板后，才允许 temporal/spatial diagnosis；SIDE 结果不能替代这一步。

## 8. Q43：失败分类与唯一替代重跑

| 类型 | 身份 | 处置 |
|---|---|---|
| `IMPLEMENTATION_INVALID` | 单位、符号、IC/BC、梯度、identity、NaN/Inf 等实现证据失败 | intent 无科学投票权；保留记录，修复须有定位证据 |
| `METHOD_SPECIFIC_NUMERICAL_FAILURE` | 正确实现下的发散、超时、不可容许状态或预算越界 | 计入该方法，不允许换 seed/网络/预算救援 |
| `SHARED_INFRASTRUCTURE_FAILURE` | evaluator、公共数据、运行环境封装或共享训练路径故障 | 影响全部相关臂；修复后保持科学配置重放 |
| `ENVIRONMENT_BLOCKED` | 依赖、硬件或外部环境使 intent 无法开始/完成 | 记 `BLOCKED`，不冒充科学失败或成功 |

公共 preflight 只验证实现、单位、有限性、梯度、IC/BC、identity 和预算可执行性；不得读取 formal oracle、筛选正式案例或调优科学超参数。生成 intent 后，只有有证据的 implementation/shared-infrastructure 缺陷，才允许同阶段同臂最多一次 superseding rerun；原 manifest、intent、日志和失败处置保持可追溯。正确实现下的 method-specific failure 不得通过加 seed、换网络、提高预算、修改阈值/support 或追加训练技巧重放。

## 9. 对未来 G3–G4 的影响

> Q44–Q48 已由 [论文主张与新颖性边界整合](2026-08-25-hfo-q44-q48-paper-claim-and-novelty-boundary-integration.md)和 [ADR 0034](../adr/0034-freeze-single-method-headline-and-hfo-scoped-forward-claim.md)继续约束；本节不单独决定 headline、formal 外推域或新颖性刷新时点。

- G3 在方法投票前增加一次耦合模式资格，并保留 Q32 的公共 backbone 资格；具体先后和最小设计必须在未来 G3 PLAN 中冻结，禁止把两者扩成无界全排列；
- backbone 可以正式裁决为 `BACKBONE_INDETERMINATE`，此时不进入方法投票；
- raw competence 的全通过规则只作用于事前冻结的 method-vote case×cycle，并增加 seed quorum；
- 所有方法候选都必须面对有效 wider-raw 与 extra-work raw，而不再使用 disconnected dummy 作为主要 kill control；
- method-specific failure 计入 intent-to-run；只有证据充分的实现或共享基础设施缺陷可有一次 superseding rerun；
- Q37–Q43 不改变 side 方法延后选择、cKC 的 `TEMPORAL+` 前门、固定-support attribution 与 best-method 分轨。

## 10. 当前状态与下一动作

本整合只更新 future roadmap，不改变实时阶段：`HFO_NP_V1_G0_G1_PLAN_REVISED_BLOCKED / HFO_SOURCE_CONTRACT_NOT_CLOSED / NO_SCIENTIFIC_METHOD_CLAIMS`。当前没有 SOURCE+、EVENT+、SIDE+、RAW_COMPETENT、TEMPORAL+、backbone 或耦合模式赢家。

当前唯一可申请的科学执行动作仍是 live plan 的授权包 A：G0。未经明确批准，不运行来源检索、solver、PINN、training、formal、GPU 或付费计算。
