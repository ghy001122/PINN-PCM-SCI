# 0018：采用实验时间尺度约束的二维电热结构前沿 benchmark

- `status`: `ACCEPTED`
- `accepted_at`: `2026-08-21`
- `decision_scope`: `EAF_KC_V1_F0_F6_LOCAL_CPU_ONLY`
- `claim_status`: `PROPOSED_METHOD_NO_NUMERICAL_EVIDENCE`

## 决定

在保留 Q‑POP、R3/R4、TAPF 与 ETPF 历史负面证据的前提下，批准唯一的新科学 substrate `EAF-KC-v1`。它以公开 VO₂ 前沿实验直接报告的器件尺度、脉冲尺度、形成/恢复时间和前沿速度作为来源约束，以来源可追溯的 Q‑POP 热力学/输运形式作为材料建模起点，构造独立、确定性的二维电—热—结构数值 benchmark。

该决定只授权 F0 来源冻结、F1 无量纲可行性、F2 工程 smoke、F3 单参考前沿、F4 oracle 资格化、F5 强 raw 能力门和 F6 KC 判别 pilot。授权限于本地 CPU 和公开一手来源读取；formal、GPU、外部付费计算和论文正面主张仍未授权。

## 必要接口

- `FrontSourceMap`：逐项区分来源直接事实 `A`、有界适配 `A_PRIME` 和工程选择 `ENGINEERING`。
- `FrontFeasibilityReport`：在求解器前裁决 Fourier 数、热扩散长度、前沿传播比例、界面网格、局部阈值选择性和恢复窗口。
- 二维电热结构 case/artifact：显式电极与衬底热边界，保持电—热—相态闭环。
- `EventCompetenceReport`：拒绝整域同步翻转，只接受持续、连通且部分覆盖的空间前沿。
- 独立磁盘 evaluator：trainer 不得访问 oracle 瞬态标签或内存状态。

## 论文边界

- 实验观测只冻结尺度和外部一致性范围，不作为 PINN 训练标签或数值真值。
- benchmark 与 Q‑POP 输出均只能称为合成数值参考，不称为实验验证、完整 Q‑POP、真实器件替代或 SOTA。
- 唯一正向方法仍是结构场选择性动力学时钟；完整导数回拉、计算图隔离、强 raw 基线、一般单调与动力学错位对照继续有效。

## 止损

- 来源、许可或几何/协议不能唯一冻结：`FRONT_SOURCE_BLOCKED`。
- 无量纲窗口不存在：`FRONT_FEASIBILITY_NO_GO`，不得实现求解器。
- 单参考案例不能产生可解析前沿：`FINAL_FRONT_BENCHMARK_NO_GO`，不得再换 substrate。
- oracle 不收敛、守恒失败或事件漂移超界：`EAF_ORACLE_INVALID`。
- 强 raw 不能解析事件：`RAW_EVENT_NOT_RESOLVED`，只允许一次预登记稀疏结构锚点诊断后收口。
- KC 在有效且可辨别的 pilot 中失败：`KC_SCIENTIFIC_NO_GO`，不得换 oracle 救援。

