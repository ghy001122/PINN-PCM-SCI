# R1 FULL_DESIGN 决策合同（Q1–Q24）

- `decision_id`: `R1_FULL_DESIGN_GRILL_2026-08-22`
- `status`: `ACCEPTED`
- `accepted_at`: `2026-08-22`
- `claim_status`: `PROPOSED_METHOD_NO_NUMERICAL_EVIDENCE`
- `user_basis`: 用户逐轮接受推荐；Q5 由用户明确撤销全局次数上限；Q6 由 Q6a=A 收紧为可审计的开发期联合设计

本文件只冻结当前 R1 的论文目标、物理对象、方法归因、案例隔离、预算公平和停止语义。它不覆盖历史 [KC-PINN Q1–Q23 决策总表](research_decisions_Q1_Q23.md)，也不把计划、实现或运行状态写成科学事实。当前能否执行仍由仓库根目录的 `active_phase.md` 决定。

| 编号 | 已接受选择 | 冻结内容 |
|---|---|---|
| Q1 | A | 不可约目标是可归因、可复现且具有实质算法增量的 PINN 论文；KC′、IRAC 和双模块标题均可按证据缩减或替换。 |
| Q2 | A | R1 是材料类别级 `derived/synthetic` 二维 benchmark，只支持机制与计算方法主张，不作 VO₂、V₂O₃ 或其他具名材料的定量/半定量验证。 |
| Q3 | A | 允许组合创新，但须先做定向 prior-art 碰撞审查，并以预声明机制和因子/方法消融证明可归因增量；工作流完整性不能替代算法增量。 |
| Q4 | A | 48 小时只承诺冻结协议下的路线裁决或首个可信事件里程碑，不承诺阳性 pilot、formal 或论文结论。 |
| Q5 | 用户覆盖 | 不设跨路线的固定研究次数上限；每条路线仍须独立批准、冻结预算与停止条件，并在终点立即收口。见 [ADR 0027](0027-remove-the-fixed-count-cap-on-future-research-routes.md)。 |
| Q6 / Q6a | B，经 A 收紧 | 允许在互斥 development pool 内联合迭代 benchmark 与方法并完整留痕；随后同时冻结生成器、方法、指标和阈值，只在完全未触碰的 formal 家族一次裁决。 |
| Q7 | A | 物理机制采用接触/几何不对称 `A` × 材料非均匀性 `H` 的 2×2 因子块：A0H0、A1H0、A0H1、A1H1。 |
| Q8 | A | 最低物理闭合为电导方程、Joule 热方程和热力学一致的 Allen–Cahn 相态方程；关键本构依赖相态，并检查零驱动、能量/耗散和守恒。 |
| Q9 | A | 合格目标事件须至少含两个 formation–recovery 周期，局部、部分覆盖、空间异步且随时空离散加密收敛。 |
| Q10 | A | 方法模块由独立瓶颈诊断准入：时间瓶颈才允许 KC′，空间瓶颈才允许 IRAC；只有双瓶颈及交互门成立才保留双模块标题。 |
| Q11 | A | formal OOD 必须留出完整几何—协议—非均匀性家族；同一实体的时空点、轨迹片段或窗口不得跨角色。 |
| Q12 | A | KC′只重参数化相态变量的时间坐标，执行完整链式回拉；不修改自由能、动力学系数或 PDE 解空间，也不允许物理时间旁路。 |
| Q13 | A | 首个空间模块采用界面感知残差自适应配点 IRAC；默认是 supporting module，只有 prior-art 与增量证据同时支持时才升级为主要创新。 |
| Q14 | A | development 方法比较固定六臂：强 raw 基线 B、generic monotone clock、KC′、IRAC、KC′+IRAC、IRAC-score shuffle。 |
| Q15 | A | 唯一结构主端点为按周期等权、完整案例聚合的相态/界面时空 symmetric difference；电热误差、PDE/守恒与器件端口是非劣守卫。 |
| Q16 | A | 双模块交互采用预注册 difference-in-differences；完整案例上的置信下界必须超过零及预声明实用裕量。 |
| Q17 | A | 以实际计算量为公平主轴，并同时报告相同案例/seed/调参机会下的墙钟、参数量、更新数和额外导数/采样成本。 |
| Q18 | A | 完整案例预先分为四个互斥角色：oracle qualification、joint development、one-shot formal OOD、reserve。 |
| Q19 | A | 事件与通过阈值根据来源尺度、离散误差、守恒裕量和 development 噪声冻结；打开 formal 后不得移动。 |
| Q20 | A | 只用 development 结果估计吞吐量、方差和效应范围；在打开 formal 前一次冻结案例数、seed 数、预算和统计规则。 |
| Q21 | A | 完整几何—协议—非均匀性 case 或完整留出家族是科学独立单位；seed 仅为案例内嵌套重复，方法间采用配对分析。 |
| Q22 | A | 方法自身导致的发散、超时、clock 不可容许或资源超限均进入 intent-to-run；只有明确的方法外执行损坏可按原配置重放。 |
| Q23 | A | 稿件故事预先路由：双模块、KC′单模块、IRAC 单模块或 benchmark/负结果资产；失败模块不得进入主要创新标题。 |
| Q24 | A | oracle 不合格、无可辨瓶颈、raw 不胜任、方法无增量或冻结预算耗尽均立即关闭 R1；下一路线须有实质不同对象、接口或假设并重新批准。 |

## 授权分层

- 授权包 A：P0–P5，限文档同步、定向一手来源审查、CPU oracle、strong-raw 诊断和六臂 development pilot；阶段门顺序生效。
- 授权包 B：P6–P8、formal OOD、必要 GPU 与论文结果收口；当前未授权。

