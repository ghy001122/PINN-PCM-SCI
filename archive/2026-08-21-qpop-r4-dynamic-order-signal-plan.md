# Live plan：QPOP-R4-v1 动态电子序参量信号门

- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `authorization_state`: `USER_AUTHORIZED_NEW_BOUNDED_SCIENTIFIC_ROUTE_2026-08-21`
- `execution_authorized`: `true`
- `claim_status`: `PROPOSED_ROUTE_NO_R4_NUMERICAL_EVIDENCE`

## 论文去向与核心假设

论文仍检验“仅结构序参量 η 使用局部严格单调动力学时钟”是否改善重复脉冲二维 VO₂ PINN。R3 的全局稳定 μ 代数闭合删除了 Q-POP 原生 μ 动力学、历史和扩散；本路线只恢复这一项，检验它是否是缺失结构事件的主因。

## R4 固定物理边界

- 独立未知量为电势 `φ`、温度 `T`、结构序参量 `η` 和电子序参量 `μ`；
- `η` 与 `μ` 分别保留 Q-POP 的 Allen–Cahn 动力学、梯度项和 Robin 环境边界；
- 载流子使用冻结 Q-POP Fermi 本构的局部平衡闭合；仍删除瞬态载流子方程和 Poisson 空间电荷；
- 电路、几何、材料参数、四个 60 ns 开/60 ns 关脉冲、5 ns 边沿及结构阈值保持不变；
- R3 产物不改写，R4 使用新的 PhysicalContract/evidence identity。

## 可执行任务与门

1. `R4-S0`：测试先行实现动态 μ 的四场 oracle；完成初值保持、制造解/有限性、η/μ 扩散与积分平衡、HDF5 往返及失败落账。smoke 墙钟上限 10 分钟。
2. `R4-S1`：固定顺序运行 `(9 V, 500 kΩ)`、`(10.5 V, 300 kΩ)`、`(7.5 V, 700 kΩ)`，共同使用 `50×20`、`dt=0.1 ns`、`0–494 ns`。总墙钟上限 30 分钟。`dt=1 ns` 的原始失败永久保留；`0.1 ns` 是一次由 `0.01 ns` 原生电子时间尺度和小网格单变量诊断触发的欠分辨修正，不开放进一步步长搜索。
3. `R4_SIGNAL_PRESENT`：至少 2/3 案例同时满足相区占比范围 `≥0.05`、非退化形成—恢复周期 `≥2`、最大平衡违规 `≤1%`，且所有场有限。
4. 若信号门失败，裁决 `R4_NO_SIGNAL` 并收口，不搜索新电压、阈值、脉冲、网络或积分协议。
5. 仅在信号门通过后，建立四场 raw/identity/KC 最短训练链；先证明强 raw 能解析事件，再进行 `1 case × 1 seed × 200 updates` 的 raw/identity/KC 判别 smoke。KC 仍只作用于 η。

## 当前禁止

- 修改或重跑 R3 以寻找正结果；
- 恢复瞬态载流子、Poisson、高场缺陷、Poole–Frenkel、完整力学、PHA 或双时钟；
- 电压/阈值/网络宽深/优化器/进一步积分步长搜索，或 KC 与 Fourier、采样等组合救援；
- 在 R4 信号与 strong-raw 门前启动 formal、GPU 或外部付费计算；
- 将任何 smoke/pilot 或合成 oracle 表述为实验验证、SOTA 或正式方法证据。

## 停止与归档

每个真实 run 启动前写 intent，结束后生成 immutable manifest 并进入 append-only index。达到 `R4_SIGNAL_PRESENT` 或 `R4_NO_SIGNAL` 后只更新一次阶段状态；只有前者开放四场 PINN smoke，formal 仍需后续独立冻结。
