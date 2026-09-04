# PHK-V2.3 LF3 快速 prior-art 闭包

- `date`: `2026-09-04`
- `scope`: `PHK_V23_LF3_MEASURE_DECOUPLED_STARTUP_SCALED_PHASE_LATENT_CARRIER_PILOT_EXECUTE`
- `search_cap`: `12_PRIMARY_SOURCES_OR_AUTHOR_REPOSITORIES`
- `verdict`: `NO_EXACT_COLLISION_FOUND_WITHIN_FROZEN_SEARCH_SCOPE`
- `method_identity`: `ATTRIBUTED_SOLVER_RECOVERY_COMBINATION_PILOT`

## 冻结检索问题

是否已经存在与 LF3 完整功能组合相同的公开方法：对电—热—相态耦合 PINN 使用初值精确的 startup-scaled inverse-link phase 表示；以 target-measure 监督 V/T、以互斥事件类等权监督完整 phase-logit 增量；再以无标签 full-physics continuation 检验事件 carrier 的 Pareto 保留？

停止条件为先到者：找到完整功能同构实现；或核验 12 项最邻近一手论文/作者仓库。检索不决定是否恢复 backbone；若发生完整碰撞，只禁止原创 headline，并把实现作为有来源 baseline。

## 一手来源矩阵

| # | 一手来源 | 与 LF3 的重合 | 边界 |
|---:|---|---|---|
| 1 | [Lagaris et al., 1997](https://arxiv.org/abs/physics/9705023) | 用输出变换精确满足初边值条件 | 无事件稀有测度、phase-logit teacher 或两阶段 Pareto 合同 |
| 2 | [Sukumar & Srivastava, 2021](https://arxiv.org/abs/2104.08426) | exact boundary construction | 不包含本项目的耦合对象与 teacher/continuation 组合 |
| 3 | [Manav et al., 2024](https://arxiv.org/abs/2404.13154) | phase-field PINN、sigmoid/bounded phase 表示 | 不等同于 startup-scaled logit-increment distillation |
| 4 | [Sharp-PINNs paper](https://arxiv.org/abs/2502.11942) / [authors' code](https://github.com/NanxiiChen/sharp-pinns) | phase-field 的 staggered/curriculum solver recovery | 不采用 LF3 的监督测度和 matched carrier-to-physics 归因 |
| 5 | [PF-PINNs paper](https://doi.org/10.1016/j.jcp.2025.113843) / [authors' code](https://github.com/NanxiiChen/PF-PINNs) | 专门的 phase-field PINN 求解策略 | 未发现完整 LF3 组合 |
| 6 | [Causal PINNs](https://arxiv.org/abs/2203.07404) / [authors' code](https://github.com/PredictiveIntelligenceLab/CausalPINNs) | 时间因果加权与困难动力学训练 | startup 因子不是其因果权重，也无本项目 carrier 门 |
| 7 | [Wu et al., 2022](https://arxiv.org/abs/2207.10289) / [authors' code](https://github.com/lu-group/pinn-sampling) | PINN 采样策略比较 | 与等类别 teacher 测度只有一般采样层面的邻近性 |
| 8 | [Hinton et al., 2015](https://arxiv.org/abs/1503.02531) | logit/soft-target distillation 的一般先例 | 不支持将 inverse-link teacher 单独主张为原创 |
| 9 | [Cui et al., 2019](https://arxiv.org/abs/1901.05555) | 类别重平衡的一般先例 | 不支持将等类别损失单独主张为原创 |
| 10 | [Balanced Knowledge Distillation](https://arxiv.org/abs/2104.10510) / [authors' code](https://github.com/EricZsy/SingleKD) | 类别不均衡下的蒸馏 | 对象、表示和物理 closure 均不同 |
| 11 | [Goswami et al., 2019](https://arxiv.org/abs/1907.02531) | transfer learning 与 phase-field fracture PINN | 不包含 LF3 的 phase latent 与强基线三层门 |
| 12 | [Fine-Tuning DeepONets for PINNs, 2024](https://arxiv.org/abs/2410.14134) | 预训练到 physics-informed fine-tuning | 架构、监督对象与稀有事件归因不同 |

## 裁决与论文边界

`VERIFIED`：在上述冻结范围内未发现完整功能同构碰撞；各组成件均有明确先例。

`SUPPORTED_INTERPRETATION`：LF3 最多是一次有来源的 solver-recovery 组合 pilot。单条 T0→P0 轨迹若为正，只能证明 nominal、single-seed、fixed-discretization 下的组合可行性和同架构 PINN-specific Pareto 信号。

`UNKNOWN`：更广检索是否存在未命中的完整同构方法；LF3 是否能建立 carrier；相对 direct `LF_ONLY` 是否有可测 paper-value；跨 seed、OOD 与 stress 是否成立。

禁止把 startup scaling、logit teacher、类别平衡任一单件写成独立原创。只有后续新授权的 matched output-phase ablation、重复 seed、formal OOD/stress 与强基线增量闭合后，才能重新裁决正面论文主体身份。
