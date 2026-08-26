# 已归档计划：R1 授权包 A（在 P2 终止）

> `superseded_by`: [`docs/plans/NEXT_ACTIONS.md`](../docs/plans/NEXT_ACTIONS.md)
>
> 本文件完整保留用户批准的授权包 A 及其 P0–P8 门设计；授权已在 P2 的预声明停止条件消耗，不再授予当前行动。

- `phase_id`: `R1_P2_TERMINAL_NO_CREDIBLE_EVENT`
- `lifecycle_state`: `BLOCKED`
- `blocker_id`: `R1_P2_NO_CREDIBLE_EVENT`
- `authorization_state`: `USER_APPROVED_LATEST_PLAN_PACKAGE_A_2026-08-22`
- `plan_status`: `PACKAGE_A_STOPPED_AT_P2_TERMINAL_CLOSEOUT`
- `source_review_authorized`: `false`
- `cpu_oracle_authorized`: `false`
- `cpu_pinn_development_authorized`: `false`
- `formal_or_gpu_authorized`: `false`
- `next_route_execution_authorized`: `false`
- `claim_status`: `NO_SCIENTIFIC_METHOD_CLAIMS`

## 当前门状态与剩余授权

- P0：`DOCUMENT_CONSISTENCY_VALID`，已允许进入 P1。
- P1：`P1_PASS_WITH_SCOPE_REDUCTION`；IRAC 只保留为透明适配，KC′只保留窄机制假设，已允许进入 P2。
- P2：`R1_P2_NO_CREDIBLE_EVENT`；冻结 A1H1 对象在四个预声明电压上没有通过完整双周期事件门，触发终止。
- P3–P5：未进入；qualification 与 training intents 均为零。
- 当前只允许完成有界收口、复核证据或提出 R2 `FULL_DESIGN` 供用户审查。R2/R3 执行、P6–P8、formal/reserve、GPU 和付费计算均未授权。

## 当前结论与论文去向

用户批准了 [R1 FULL_DESIGN 决策合同](../docs/adr/research_decisions_R1_FULL_DESIGN_GRILL_2026-08-22.md) 所定义的授权包 A。该路线原拟先证明合格事件与可辨时间/空间瓶颈，再分别检验 KC′ 和 IRAC；实际授权已在 P2 的预声明事件门终止，因此当前论文路由只能是 R1 有界 benchmark/负结果收口，不能进入方法投票。

P0–P2 的授权已执行并按门槛收口；P3–P5 不再开放。P6–P8、one-shot formal OOD、GPU、付费计算、提交、推送、PR 与论文正面结论均未授权。不得以换材料、移动阈值、追加 seed 或扩大预算救援当前 R1。

## 冻结的论文主问题

> 在具有接触/几何不对称性与材料非均匀性的派生二维电—热—相场器件族中，结构化相态时间重参数化与界面—残差自适应配点，能否分别缓解时间刚性和空间局部误差，并在完整族 OOD 上形成可归因的协同增量？

R1 只能支撑材料类别级 `derived/synthetic` benchmark、数值机制和 PINN 方法主张；不得表述为 VO₂、V₂O₃ 或其他具名材料的定量/半定量验证，也不得把传统 solver 输出写成实验真值。

## 冻结的物理与方法合同

R1 的最低三场闭合为：

\[
\nabla\cdot[\sigma(\eta,T)\nabla\phi]=0,
\]

\[
\rho c_p\partial_tT=\nabla\cdot(k\nabla T)+\sigma|\nabla\phi|^2-q_{\mathrm{loss}},
\]

\[
\partial_t\eta=-L(T)\left[\partial_\eta f(\eta,T)-\kappa\nabla^2\eta\right].
\]

- 物理因子：接触/几何不对称 `A` × 材料非均匀性 `H`，形成 A0H0、A1H0、A0H1、A1H1 四个预声明单元。
- 时间模块：KC′只改变 \(\eta\) 的时间坐标并执行完整链式回拉；\(\phi,T\) 保留物理时间，不改变 PDE、自由能或动力学系数。
- 空间模块：IRAC 只使用 detached、归一化的界面与 PDE 残差信号；uniform、IRAC 与 shuffle 共享候选池及实际计算预算。
- 证据角色：oracle qualification、joint development、one-shot formal OOD、reserve 四个完整案例池互斥；formal 与 reserve 不得回流开发。

## P0——同步决策与授权链（已通过）

任务：

1. 建立唯一决策身份 `R1_FULL_DESIGN_GRILL_2026-08-22`，固化 Q1–Q24，不覆盖历史 KC-PINN Q1–Q23。
2. 将上一份 FAST_SCAN 计划移入 `archive/`，本文件成为唯一 live plan。
3. 确认现行文档不再以“最多三次正式研究”、`0/3` 或剩余路线槽位决定研究去留；历史证据不回写。
4. 将 `active_phase.md`、`PROJECT_STATE.md`、`README.md` 与 `CONTEXT.md` 同步为授权包 A 的有条件执行状态。
5. 运行文档一致性门禁与差异空白检查。

进入 P1 的门槛：`DOCUMENT_CONSISTENCY_VALID`；失败时只修复权威逻辑链，不启动科研执行。

## P1——定向来源与创新碰撞审查（缩减范围后通过）

任务：

1. 为电导—Joule 热—Allen–Cahn 方程、边界条件、无量纲尺度与参数区间建立来源卡；每项标为 `A`、`A′` 或 `ENGINEERING`。
2. 核验接触/几何不对称与材料非均匀性作为两个独立物理因子的依据。
3. 定向检查结构化时间重参数化、generic monotone clock、RAR/残差采样、界面采样及其组合的直接先例。
4. 记录论文、固定代码、数据、许可和适用边界；不得跨来源拼成虚假的作者 oracle。
5. 形成 claim–collision 矩阵，区分已知模块、实际适配、可主张贡献与禁止措辞。
6. 用约 8–12 个高相关一手来源闭合 FULL_DESIGN，不开展新的无界材料扫描。

P1 停止条件：物理合同无可追溯依据；KC′或 IRAC 与直接先例实质完全碰撞且没有真实机制差异；论文贡献只能依赖工作流包装。触发后关闭 R1，不进入 P2。

## P2——R1 物理合同与独立 CPU oracle（终止门）

任务：

1. 建立新的 `R1PhysicalContract`，冻结派生身份、参数谱系、几何、边界、驱动、可变范围和单位/无量纲映射。
2. 建立独立于 PINN 的 CPU oracle；不修改、重命名或复活旧 TAPF/ETPF/EAF 冻结对象。
3. 实现 A0H0、A1H0、A0H1、A1H1 四因子单元；A1H1 是预声明目标单元，其余为机制对照。
4. development pool 内允许 benchmark–method 联合迭代，但每次变化必须留痕；不得只保留最好单元或读取 formal/reserve。
5. 首个可信事件裁决预算不超过 48 小时墙钟或 64 CPU-core-hours，以先到者为准。

目标事件同时满足：

- 至少两个 formation–recovery 周期；
- 局部且只覆盖部分区域；
- 空间异步程度高于时空离散分辨率；
- 事件位置、面积、时序与端口响应随网格/时间步加密收敛；
- 通过零驱动、能量/耗散、守恒和数量级检查。

P2 停止条件：目标 A1H1 不合格、事件只在单一分辨率出现、守恒/零驱动失败，或必须根据结果移动阈值才能通过。触发后形成有界 closeout，只可提出 R2 FULL_DESIGN，不自动执行。

## P3——oracle 资格化、冻结与四池拆分（未进入）

任务：

1. 对四个因子单元执行预冻结的粗—中—细联合空间/时间离散资格化，总计不超过 12 个 qualification intents。
2. 由训练器外部 evaluator 判断事件、界面几何、PDE/守恒、端口和离散收敛。
3. 资格通过后冻结 generator、阈值、指标、案例定义和代码身份。
4. 生成四个互斥案例池并检查完整几何、协议、非均匀性家族的角色隔离。
5. formal OOD 与 reserve 在授权包 B 前保持封闭，不得用于调参、阈值或模块选择。
6. 只在保护冻结案例身份和重放资格时记录必要 manifest/hash；不扩散为日常重复审计。

P3 停止条件：目标事件资格失败、两个最细离散层不收敛、守恒失败、案例角色泄漏，或冻结后需要修改结果相关门槛。

## P4——强 raw PINN 与瓶颈诊断（未进入）

任务：

1. 实现新的三场强形式 PINN；raw、generic clock 与 KC′共享同一基础网络族和物理残差。
2. 依据 P1 选择一个强 raw 架构；development 阶段允许一次预算内选择，但所有选择消耗同一固定预算。
3. 在四个开发案例、两个实际计算预算、两个嵌套 seeds 上检验 raw，总计不超过 16 个 training intents。
4. 记录墙钟、参数量、更新数、导数成本、采样评分成本、失败与方法外损坏。
5. 由训练器外部诊断裁决：`NO_BOTTLENECK`、`RAW_INCOMPETENT_ROUTE_NO_TEST`、`TEMPORAL_ONLY`、`SPATIAL_ONLY` 或 `DUAL_BOTTLENECK`。

只有 `TEMPORAL_ONLY`、`SPATIAL_ONLY` 或 `DUAL_BOTTLENECK` 才允许对应模块进入 P5。`NO_BOTTLENECK` 表示对象不能辨别目标增量；`RAW_INCOMPETENT_ROUTE_NO_TEST` 表示没有合法共同基线。二者均关闭当前 R1 方法投票，不得用模块堆叠救援。

## P5——KC′/IRAC 实现与六臂 development pilot（未进入）

固定六臂：

1. 强 raw 基线 B；
2. generic monotone clock；
3. KC′；
4. IRAC；
5. KC′+IRAC；
6. IRAC-score shuffle。

任务：

1. 实现 KC′完整回拉、计算图隔离和 clock 可容许性守卫。
2. 实现 detached/归一化 IRAC，以及候选池和实际计算公平的 shuffle 负控。
3. 先运行 manufactured/unit tests 与 CPU smoke；这些只证明实现/执行，不形成科学主张。
4. 在一个预声明代表性 development case、两个嵌套 seeds 上执行六臂 pilot，总计不超过 12 个 training intents。
5. 唯一结构主端点为 cycle-equal 相态/界面时空 symmetric difference；电场、温度、PDE/守恒与器件端口是非劣守卫。
6. 按实际计算量匹配案例、seed 和调参机会，并报告墙钟、参数量、更新数及额外导数/采样成本。
7. 计算预注册交互量：

\[
I=(E_B-E_{TS})-(E_B-E_T)-(E_B-E_S).
\]

P5 裁决：

- KC′须优于 B，并与 generic monotone clock 拉开差异；
- IRAC 须优于 B，并与 score shuffle 拉开差异；
- TS 须通过全部守卫，且交互置信下界超过零及 development 阶段冻结的实用裕量；
- 单模块通过则主动缩减论文；任一失败模块不得捆绑为主要创新；
- 所有失败运行按 intent-to-run 计票，只有明确的方法外执行损坏可按完全相同配置重放。

P5 完成即停止授权包 A，形成 `PACKAGE_A_COMPLETE_AWAITING_PACKAGE_B_DECISION` 或相应有界 No-Go；不得自动进入 formal。

## P6–P8——仅保留设计，当前未授权

- P6：只在 P5 出现合格信号后，用 development 结果冻结 formal 样本量、seed、预算、非劣界、实用效应阈值和统计分析计划；若预算内功效不足，裁决 `FORMAL_DESIGN_UNDERPOWERED`。
- P7：用户另行批准授权包 B 后，才可一次性打开 formal OOD 池；不得调参或用 reserve 补救方法失败。
- P8：按预冻结结果路由双模块、KC′单模块、IRAC 单模块或 benchmark/负结果稿件，并交付代码、配置、数据、图表与证据映射。

## 论文结果路由与停止语义

| 证据结果 | 允许路由 |
|---|---|
| T、S 与交互均通过 | 申请双模块 formal；仍只主张派生计算 benchmark |
| 仅 KC′通过 | 时间重参数化单模块论文候选 |
| 仅 IRAC 通过 | 仅在 prior-art 审查支持时成为空间方法论文候选 |
| 方法均无增量 | benchmark/evaluator、支撑性负结果或关闭路线 |
| oracle、raw 或瓶颈门失败 | 有界 closeout；只提出下一路线 PLAN |

所有科学表述继续区分 `VERIFIED`、`SUPPORTED_INTERPRETATION`、`HYPOTHESIS` 与 `UNKNOWN`。代码存在、测试通过、运行完成、数值资格、方法增量、formal OOD 和实验验证是不同证据层。
