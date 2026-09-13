# V28：电学消元、同层强基线增益与剩余 PDE 的独立价值

**本轮已完成。VERIFIED：D_E、P_E 均超过共享电学求解的强插值 B_E；P_E 对同父 D_E 未达到冻结 A/B 增量，P_F 未触发、未运行。** GPU 产物已回收，实际实例已关闭并确认，随后完成本地参考评价。用户随后明确授权发布新稿与重要证据，并交付独立复评；本包属于本文件所在提交，原始未发布字段保留为科研收口快照。

P_E 相对 B_E 的 S / raw Ephi / 电流 / 功率误差降低 41.85% / 32.69% / 59.85% / 61.18%；D_E 也通过同样两层门。相对 D_E，P_E 的 S / Ephi 上升 4.07% / 2.68%，电流 / 功率仅改善 4.20% / 5.49%。其固定无标签内部残差总量还高 0.58%，不能复述为本轮“物理残差下降却事件变差”。所有角色仍未通过严格双周期器件门。

- [完整论文正文](manuscript.md)：问题、方法、原始来源、实际结果、讨论和保留历史证据。
- [主张与证据](claim_evidence_matrix.md)、[最小复现入口](reproducibility.md)、[精简证据包](evidence/README.md)。
- [四角色完整数表](tables/fixed-endpoints.md)、[PDE 匹配差分](tables/matched-pde-contrast.md)、[双周期事件](tables/cycle-events.csv)。
- [终局报告](../../docs/experiment/2026-09-13-phk-v23-lf11-electrical-elimination-terminal-closeout.md)、[冻结配置](../../configs/phk_v23/lf11_elimination_sprint.json)、[执行指令](../../docs/notes/2026-09-13-lf11-elimination-authorized-sprint.md)。
- [保留的 V27](../paper_v27/README.md)；下一方案只列于[唯一计划](../../docs/plans/NEXT_ACTIONS.md)，没有新数值研究执行授权；发布及评估请求见[V28 交接](../../docs/notes/2026-09-13-lf11-v28-results-cloud-review-handoff.md)。

| 图件 | 内容 | 导出 |
|---|---|---|
| [方法接口](figures/method-interface.png) | 同层对照、隐式电学、局部焦耳耦合、归因关系 | [PDF](figures/method-interface.pdf) |
| [场—事件—器件主图](figures/field-event-device.png) | 四角色相态、召回、电流/功率误差、局部热与温度误差 | [PDF](figures/field-event-device.pdf) |
| [双周期相态](figures/phase-fields.png) | 固定终点、共同色标；参考峰值仅用于展示时刻 | [PDF](figures/phase-fields.pdf) |
| [局部焦耳沉积和温度](figures/joule-temperature.png) | 两个预定平台末时刻、共享尺度 | [PDF](figures/joule-temperature.pdf) |

原始运行在 `outputs/runs/20260913-lf11-electrical-elimination`，包含共同父态、固定池、D_E/P_E 的 Adam 节点、最终模型及接受优化状态、完整自身预测、实际算量和关机回执。正式训练合计 3000 Adam / 600 次完整评估；没有新增初始化、观测、完整案例或 stress。

SUPPORTED_INTERPRETATION：已经补上同信息强基线上的重建与功能增益，且分开了电压接口修复与训练收益。当前最优先的问题是证明剩余热/相态 PDE 的独立价值，而非把通用求解、隐式梯度或机器精度守恒分别包装成创新。论文仍是合成无量纲二维对象的有界研究稿，尚不是经过独立确认的正面 PINN 方法论文。