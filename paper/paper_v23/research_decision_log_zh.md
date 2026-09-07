# PHK-V2.3 LF6 研究判断与论文路线

## 一句话裁决

LF6 首次真正执行了无标签 physics refinement，并得到清晰的负结果：
**固定 blind physics objective 降至原来的 1.28%，但 V/T 先在 phase 冻结期漂移，
phase 解冻后两周期事件迅速消失。** 终局为
`LF6_P0_PRESERVATION_FAILED`，candidate=none。

## 实质进展

1. `VERIFIED`：CPU-F 合法构造了 2% active-count 的 teacher rank frontier，
   cycle 1/2 分别为 ranks 17--22 和 17--20。
2. `VERIFIED`：DEV-U 与 DEV-R 同起点、同预算、同 base/spatial stream，仅
   endpoint cells 不同，各完成 400 步。
3. `VERIFIED`：DEV-U recall=0.897/0.899，未过 safety；DEV-R
   recall=0.918/0.923，过 safety，但 cycle-1 timing=0.01053，未过 strict。
4. `VERIFIED`：两臂都未过 strict，因此机制结果只能是
   `NO_RANK_SPECIFIC_INCREMENT`，不能把 DEV-R 的 safety 选择冒充 rank 机制。
5. `VERIFIED`：DEV-R 触发 P0；1200 步纯 physics、无 label/replay/anchor，
   blind objective `4.927872 -> 0.063147`，ratio=0.012814。
6. `VERIFIED`：step550 phase bitwise 不变且无 optimizer state，但 V/T MSE 已从
   `8.25e-5/0.00246` 漂到 `0.00206/0.04316`；step600 recall 降到
   0.343/0.216；step1200 为 0/0。
7. `SUPPORTED_INTERPRETATION`：这是“两阶段 physics forgetting”：先是固定
   phase 条件下 V/T 偏离 carrier，再是 joint 更新直接抹除事件。尚不能唯一归因于
   PDE mismatch、优化冲突或缺少 replay。

## 强基线与论文边界

extra-fine evaluator 上，DEV-R 的 phase/T/current 为
`0.03237/0.01736/0.13730`，P0 为
`0.15750/0.15147/0.07540`；direct `LF_ONLY` 为
`0.00657/0.00180/0.00352`。所以：

- 可以写：single-seed、fixed-discretization 的界面暴露机制证据与 physics
  forgetting 负结果；
- 不可以写：rank-band 增量、strict carrier、PINN Pareto、强基线增益、实用
  优越、SOTA、OOD/stress、实验验证或投稿就绪。

## 最高价值的后续方向（仅研究判断，不构成授权）

不要继续微调 rank band、延长 P0 或更换 optimizer。下一条最小可证伪路线应
直接针对已观测的 preservation 缺口：从同一 DEV-R safety endpoint 出发，做一条
预冻结的 carrier-preserving physics continuation，并与本次 pure-physics P0 严格
matched。机制必须在训练中承担事件保持，而不是只在 entry gate 检查；例如固定
小权重 replay/functional constraint 只能二选一，不能堆模块。若 matched arm 仍不能
同时保持事件并降低 blind objective，则停止正面 solver-recovery 路线，收口负面稿。
若成功，再补最少多 seed 和 sparse/equal-information task；candidate 前不解封 stress。

## LF7 ACTIVE：将 preservation 提升为更新接受规则

LF7 已预注册从同一 exact DEV-R 起点、同一 physics stream 与 blind pool 出发的
matched screen。P0-S 用固定小步长回答“仅缩小步长是否足够”；P0-F 每 25 步审计
事件 competence 与 blind physics，失败时完整回滚 model/optimizer/RNG 并作有限
dyadic backtracking。medium teacher 不进梯度，但参与接受裁决，因此 P0-F 不是
label-free。只有 S 不过 safety 而 F 通过时，才支持 competence filter 的 pilot
信号；S 也通过表示小步长已足够，F 也失败则支持该强式路径下的有界负结论。
当前仅为 ACTIVE 设计身份，结果、candidate 与论文正面结论均为未知。
