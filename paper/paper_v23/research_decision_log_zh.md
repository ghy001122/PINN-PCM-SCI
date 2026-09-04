# PHK-V2.3 LF3 研究判断与论文路线

## 一句话裁决

LF3 不是成功 carrier，也不是 PINN 方法结果；但它首次把此前的“冷态塌缩”
和 LF1 的“事件过宽”收缩成了一个很具体的剩余问题：**事件核心、时间、质量和
precision 已恢复，边界 support recall 仍不足。** 这是可写的 solver-recovery
负面证据，但不足以继续在同一 latent 路线上调参救援。

## 已验证事实

- 唯一 T0 轨迹严格完成 1200 步，P0 为 0 步；
- potential maximum-principle、phase range、finite、双周期事件、时间、
  precision、active-mass、locality 和 recovery 全部通过；
- 两周期 recall 为 `0.805842/0.768603`，均低于冻结的 `0.90`；
- 因此机器终局为 `LF3_CARRIER_NOT_ESTABLISHED`，P0 是未触发而非失败；
- 本地 extra-fine evaluator 上 LF3-T0 的 phase ROI RMS 为 `0.0390008`，
  明显好于 LF2-M0 的 `0.110564`，但仍远差于 direct `LF_ONLY` 的
  `0.00657038`；
- 云端产物已完整回收和哈希核验，实例已关机并确认 SSH 拒绝；
- 两份 stress reference 继续 sealed/unread。

## 最有论文价值的三段对照

1. **LF1：高 recall、极低 precision。** 事件被学出来，但 active mass 是
   teacher 的 5–6 倍，属于用大面积 false positive 换 recall。
2. **LF2：低连续场误差、零事件。** target measure 让整体误差下降，却被
   冷态多数类支配，证明低 weighted MSE 不能替代事件 competence。
3. **LF3：高 precision、正确质量和时间、recall 不足。** 它修复了前两类
   极端失败，却只学到较窄的事件核心，漏掉约 19%/23% 的 teacher support。

这三段比“又一次没过门”更有科研含量：它建立了 sparse-event 学习中
existence、mass、precision、recall、timing 彼此不可替代的对象特异证据。

## 为什么现在不继续跑 P0 或延长 T0

P0 的科学问题是“physics 能否在保持合格 carrier 的同时降低残差”。当前
前提不成立，强行运行会把 carrier 缺陷和 physics forgetting 混在一起。延长
T0、改 loss 或放宽 recall 都是看过结果后的新科学身份；即使偶然过门，也仍
没有解决 direct `LF_ONLY` 大幅领先的问题。因此本 campaign 的最佳止损就是
保留近门证据并结束，不追加同身份 GPU。

## 导师初稿与二区正面稿的差距

当前材料足以交付导师审阅：有完整问题、强基线、执行链、失败机理、五张图和
明确边界。若要升级为中科院二区定位的正面方法稿，最低还缺：

1. 一个能真正通过 carrier gate 的 load-bearing 核心机制；
2. 实际执行的无标签 physics refinement，并相对同架构 T0 形成 Pareto；
3. 若主张 phase latent，补同初始化/同 batch、只换 output-phase teacher 的
   matched ablation；
4. 多 seed 与完整实体级 formal OOD；
5. 面对 direct `LF_ONLY` 的预声明价值：accuracy noninferiority，或另一个在
   实验前冻结且可测的角色增量；
6. 只有候选形成后才开 stress，不能用 stress 救一个 nominal 未过门的方法。

这些是后续研究缺口，不是本次自动授权。当前唯一合法状态是
`next_research_execution_authorized=false`。

## 论文口径

允许写：在单 seed、nominal、fixed-discretization 对象中，competence-first
评价揭示了三种互不等价的失败，并将恢复路线推进到“高 precision 但 support
不完整”的近门状态。

禁止写：LF3 carrier 成功、P0/PINN 有增量、latent teacher 单独有效、优于
`LF_ONLY`、具有 OOD/stress 鲁棒性、达到 continuum truth、材料验证或投稿级
结论。
