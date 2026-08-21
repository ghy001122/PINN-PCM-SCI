# Structural Kinetics-Clock PINN：有界负面研究报告

状态：`SUPPORTED_INTERPRETATION / DEVELOPMENT_ONLY`
用途：论文 Results/Discussion 的可复用负面证据底稿，不是 formal 论文结论。

## 研究问题

目标是在二维、低至中等场、热主导 VO₂ 数值工作域中，检验只作用于结构序参量的局部单调动力学时钟能否帮助逐案例 PINN 解析重复脉冲下的结构前沿、延迟与恢复。为避免把弱 baseline 的失败误认作时钟增益，研究先要求强 raw-time PINN 在不使用瞬态标签时解析结构事件。

## 方法

强 raw 能力门比较 grouped-mean / smooth-max 残差聚合与 joint / four-prefix 时间策略，四臂共享 3×24 网络、float64、seed 17、初始化、归一化尺度和计算量。checkpoint 完全按独立物理审计选择。主门失败后，仅执行一次预声明的稀疏 η 标签诊断。

在该诊断仍失败后，研究按预声明备用路线实现 QPOP-R3-v1：一个独立的二维有限体积/隐式数值 oracle。它保留 Q-POP Landau 热力学、电导—Joule 热—Allen–Cahn 闭环和串联电阻边界，同时明确约去载流子动态、Poisson 空间电荷与独立电子序参量动力学。

## 结果

强 raw 协议能够降低设备轨迹误差并保持物理审计有效，但预测结构相区始终不变：相区动态范围为 0，结构误差为 0.2290643041。加入 328 个固定 η 标签后，anchor loss 降至 0.0995450991，物理最大违规仍低于诊断上限 1.25，但结构相区动态范围仍为 0。

QPOP-R3-v1 的无驱动 smoke 数值平衡达到 `6.27e-10`。固定 3×3 信号矩阵的九个案例均完成且峰值温度覆盖约 343.95–363.24 K，说明电—热链路被激活；η 存在连续松弛，但全矩阵最小值仍为 0.98217，高于冻结相阈值 0.55950。结构相区动态范围因而在所有案例中均为 0，没有任何非退化形成—恢复循环。该备用 oracle 触发 `REDUCED_ORACLE_NO_SIGNAL`。

## 解释

`SUPPORTED_INTERPRETATION`：当前负面结果更符合“所冻结的七未知量残差表示与 QPOP-R3-v1 约化都未提供可供方法比较的结构事件”，而不是“KC 已在公平 formal 比较中失败”。N1/N2 说明继续增加优化技巧、网络规模或 KC/PHA 组合缺乏依据；N3B 说明简单删除快载流子和电子序参量动态后，即使热场跨越名义转变温区，也不能自动保留重复结构动力学。

`UNKNOWN`：一个计算上可资格化、又保留真实结构形成—恢复事件的中间复杂度 oracle 是否存在；在这样的 oracle 上 KC 是否具有可辨别增量；完整 Q-POP 494 ns 窗口是否能在不同、事先批准的复现介质上资格化。

## 可写边界

可以写：预注册门控避免了在无辨别力 substrate 上继续堆叠方法；强 raw 与一次标签诊断均未解析结构事件；冻结的简化二维 oracle 在九案例中无结构信号；路线按停止条件负面收口。

不能写：KC 一般无效、Q-POP 物理无效、真实 VO₂ 器件没有结构动力学、达到 SOTA、完成 formal 验证或得到实验支持。

## 可复现入口

- 核心训练协议：`pinn_pcm_sci/training_protocol.py`
- N1/N2 runner：`pinn_pcm_sci/qpop_raw_event.py`
- QPOP-R3-v1：`pinn_pcm_sci/reduced_oracle.py`
- reduced-oracle runner：`pinn_pcm_sci/reduced_oracle_runner.py`
- 终局事实：`docs/experiment/2026-08-21-n1-n3b-terminal-closeout.md`
- 运行索引：`docs/experiment/INDEX.md`
