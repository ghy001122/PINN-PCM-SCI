# ETPF-KC-v1 K2Q 终局收口，2026-08-21

## 裁决

- `route_disposition`: `ETPF_QUALIFICATION_INVALID_NO_RESOLVED_FRONT`
- `lifecycle_state`: `BLOCKED`
- `claim_status`: `NO_SCIENTIFIC_METHOD_CLAIMS`
- `K1_run`: `20260821T122534Z-smoke-etpf-k1-001`
- `K2_run`: `20260821T123257Z-pilot-etpf-k2-signal-001`
- `K2Q_original_run`: `20260821T123848Z-pilot-etpf-k2q-qualification-001`
- `K2Q_superseding_run`: `20260821T124512Z-pilot-etpf-k2q-qualification-002`
- `next_route`: `NO_AUTOMATIC_RETRY_OR_THIRD_SUBSTRATE`

## 已核验事实

- `VERIFIED_IMPLEMENTATION`：局部四周期倾斜相场动力学、二维制造前沿强形式、零驱动守恒、HDF5 往返与独立磁盘 evaluator 均通过；K1 smoke 的最大离散平衡违规为 `5.590772879410198e-16`，自读结构和器件误差均为 `0.0`。
- `VERIFIED_DEVELOPMENT_SIGNAL`：K2 固定 3×3 矩阵的九个案例都完成四次整域形成—恢复，相区占比范围为 `1.0`，但该 run 的 5 ns 事件守卫会把整域翻转误判为前沿，因此不能作为 oracle 资格化证据。
- `VERIFIED_IMPLEMENTATION_CORRECTION`：K2Q 首次 run 使用逐时刻阈值占比最大差，任何小于存盘步长的事件平移都会得到离散误差 `1.0`；该实现与冻结 evaluator 的时间平均对称差不一致。修正版保留原 run，以 `supersedes` 启动 1 ns 存盘和 evaluator 一致的时间平均相区差。
- `VERIFIED_DEVELOPMENT_NEGATIVE`：修正版五个网格/时间层级均完成四周期且数值平衡有效，但全部 `resolved_front_cycles=0`；50×20、75×30、100×40 的空间相区差最细两级没有收缩，K2Q 因而仍为 `ETPF_QUALIFICATION_INVALID`。

## 失败根源

- `SUPPORTED_INTERPRETATION`：Q‑POP 来源量映射给出的热扩散率为 `2003.6064916850326 nm²/ns`，对应厚度散热率 `0.050090162292125824 ns⁻¹`；热扩散时间远短于 60 ns 脉冲，二维温度场趋向整体升温。
- `SUPPORTED_INTERPRETATION`：解析驱动为保证缺陷区每周期至少 40 ns 热 spinodal 暴露，将参考案例最高温度推至约 `382 K`，明显越过非缺陷区 spinodal；3 nm、`-5 K` 的局部转变温度偏移不足以维持可解析的空间前沿。
- `SUPPORTED_INTERPRETATION`：倾斜幅度超过 spinodal 且相动力学较快，整域在小于 1 ns 的观测间隔内完成翻转；这能产生重复事件，却不能支撑论文所需的移动结构前沿或时钟局部对齐证据。

## 边界

本裁决只否定冻结的 `ETPF-KC-v1` 作为移动前沿 benchmark 的资格，不否定倾斜相场方程、PINN 或结构动力学时钟的一般可行性。按批准计划，不启动 K3/K4，不建立第三个 substrate，不重开 TAPF/R3/R4/Q‑POP/PHA，也不产生 formal、GPU、SOTA 或实验验证主张。
