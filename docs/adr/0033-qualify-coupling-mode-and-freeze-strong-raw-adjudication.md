# 0033：资格化耦合训练模式并冻结 strong-raw 裁决边界

- `status`: `ACCEPTED`
- `accepted_at`: `2026-08-25`
- `decision_scope`: `HFO_POST_G1_STRONG_RAW_TRAINING_FAIRNESS_AND_FAILURE_ACCOUNTING`
- `amends`: `ADR_0032`
- `supersedes_in_part`: `HFO_Q37_Q43_PRIOR_DEFAULT_RECOMMENDATIONS`
- `claim_status`: `PLANNING_CONTRACT_NO_NUMERICAL_EVIDENCE`

用户接受引用会话“深度论文审查”对 Q37–Q43 的 `REVISE_WITH_CONDITIONAL_ACCEPTANCE` 裁决。未来 strong-raw 不默认使用 monolithic joint training：在任何方法投票前，只允许对 strong raw 进行一次有界耦合模式资格比较，比较全梯度联合优化与对称 block-coordinate/staggered 优化。二者必须优化同一完整 joint loss；后者每个子步仍保留全部 PDE、本构、IC/BC、守恒与端口项，并重新计算耦合场。唯一合格者随后冻结给所有方法臂；没有唯一合格者时不得强行选择。

三物理块继续使用同一架构族、独立参数且无共享 trunk 的 mixed first-order backbone；默认候选使用无量纲坐标、平滑 `tanh` 与来源兼容的选择性硬输出变换。传统求解器或外部闭合电学/热学只可作为 `QUASISTATIC_CLOSURE_DIAGNOSTIC` 定位耦合瓶颈，不能成为正面 PINN 方法、替代完整 joint residual 或参与 headline 方法投票。

backbone 资格不能只按平均误差或简单词典序强选。所有事前冻结的 method-vote development case×cycle 都必须进入非劣/优效不确定性带、最坏案例与物理守卫；只有在这些条件下存在单一可接受候选时才冻结。候选互有胜负或不确定性带重叠时记 `BACKBONE_INDETERMINATE`，不以参数量、墙钟或简洁性制造科学赢家；这些量只可在统计等价带内作简洁性 tie-break。

方法公平以“同一冻结 base＋最小方法增量”为主，同时要求两个有效 kill control：参数量匹配且真实参与输出的 wider-raw，以及按实际 residual-point、自动微分、forward/closure 与墙钟匹配的 extra-work raw。断开输出的 dummy module 最多用于工程微基准，不能替代科学公平控制。各方法可有同等数量的 method-specific development 配置，但还必须服从同一实际计算上限；具体配置数、seed、预算与不确定性门留待 G2/G3 吞吐量后另立 PLAN。

完整案例在看到任何 PINN 结果前分为 qualification、method-vote development 与 stress-only；raw competence 的“全部通过”只约束预冻结的 method-vote case×cycle，并须满足预声明 seed quorum。结果出现后不得把失败 case 降格为 stress-only。`NO_BOTTLENECK`、`RAW_INCOMPETENT_ROUTE_NO_TEST` 与后续 temporal/spatial diagnosis 继续按现有顺序裁决。

失败统一分为 implementation-invalid、method-specific numerical failure、shared-infrastructure failure 与 environment `BLOCKED`。公共 preflight 只检查实现、单位、有限性、梯度、IC/BC 与 identity，不读取 formal oracle 或调优科学超参数。生成 intent 后，正确实现下的发散、超时或越界计入该方法；只有有证据的实现或共享基础设施缺陷，才允许同阶段同臂最多一次保持科学配置不变的 superseding rerun，且原 intent 与失败记录必须保留。

本 ADR 只冻结 future-stage 规划边界，不冻结网络宽深、耦合交替顺序、配置数、seed quorum、预算、效应阈值或统计规则，也不授权来源检索、solver、PINN、training、formal、GPU、付费计算或 Git 发布。G0–G1 的来源、事件与 TKB 前门以及当前阻塞状态保持不变。
