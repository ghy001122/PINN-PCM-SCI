HISTORICAL_EXECUTED：本计划已完成，不构成当前授权。

# PLAN-LF11：剩余 PDE 实际影响与固定目标反事实

- `phase_id`: `PHK_V23_LF11_REMAINING_PDE_COUNTERFACTUAL_EXECUTE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `claim_status`: `REMAINING_PDE_COUNTERFACTUAL_PENDING`
- `next_research_execution_authorized`: `true`

用户当前明确授权优先于先前未授权提案；[旧提案](./2026-09-13-lf11-v28-remaining-pde-proposal.md)保留。执行依据是[完整指令](../docs/notes/2026-09-13-lf11-remaining-pde-authorized-sprint.md)，[独立报告](../docs/notes/2026-09-13-lf11-v28-independent-review-remaining-plan.md)作科学解释，不覆盖执行文件的300次上限。

1. 原固定训练池交叉评价 E0/D_E/P_E 的 C+F，复用既有独立审计；E0/D_E 进行观测、BC、热、phase完整约化梯度。只由 D_E 校准池的一阶比例冻结 kappa，弱影响规则不预设根因。
2. 同 D_E 父态、fresh L-BFGS：D_C=C，P1=C+F，符合规则时 P_kappa=C+kappa F。每臂最多300次且总正反解各30000；先一次核对实际非零时刻，统一各臂预算。不得重跑旧 V28、不加 Adam、不挑最好中途点。
3. 保存最终接受参数和优化器，在旧训练/审计池列相同 functional 和分项；新端点自身场推理后立即回收关机，本地读 nominal 参考。与 D_C、旧 D_E、B_E 按原 A/B 裁决，P_kappa 对 P1 单独归因。严格事件门不变。
4. 保留 paper_v28，在 paper_v29 整合匹配表、方程块梯度—共同目标—场/双周期事件/器件图。正面信号才规划 P_F，当前不执行；初始化、新观测和完整协议都只提出下一计划。

当前仍是同一已见 nominal 合成二维对象，未建立独立初始化、干净观测留出或 formal OOD。本轮研究要证明剩余物理的实际预测增量，不把求解、梯度检查或调权本身称创新。
