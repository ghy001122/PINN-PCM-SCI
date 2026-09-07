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

## LF7 终局：小步长负对照有效，filter 机制因身份故障未完成

1. `VERIFIED`：P0-S 从 exact DEV-R 出发完成 1200 步，固定 blind objective
   `4.927872 -> 2.971883`，ratio=0.603076，未过 0.50 门。
2. `VERIFIED`：P0-S 的 cycle 1 事件消失；cycle 2 recall/recovery 仅
   `0.0762/0.0282`；V/T/phase/topology 相对误差为
   `39.47/48.11/22.46/17.41`。所以单纯把 Adam 步长缩小 8 倍仍不能保留事件。
3. `VERIFIED_PARTIAL`：P0-F 对第一个 25-step block 的前四档学习率均因 V/T
   preservation 拒绝并成功回滚；第五档 `eta0/16` 通过全部 block gates，blind
   objective 降到 4.874314，且四个相对误差为 `0.995/1.018/1/1`。
4. `VERIFIED_ENGINEERING`：接受该 block 后，非空 Adam state 的 snapshot aliasing
   导致后续 rollback identity drift。事后修复与回归不能追溯恢复科学轨迹；未重跑。
5. 因此终局为 `LF7_MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID`，candidate=none。
   不能说 filter 成功，也不能据此说 filter 科学失败；只能保留 P0-S 负对照和
   P0-F 的局部筛选行为。

论文当前可写的新增结论是：降低步长不足以解决 physics forgetting；强式
competence filter 会在较大学习率下直接拒绝 V/T 漂移，但其长期有效性尚未获得
身份有效的 matched endpoint。direct `LF_ONLY` 仍远强于 P0-S；不得写 PINN
Pareto、强基线增益、SOTA 或候选方法。stress 保持 sealed/unread。
