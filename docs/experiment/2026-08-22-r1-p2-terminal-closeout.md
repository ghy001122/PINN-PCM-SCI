# R1 派生电—热—Allen–Cahn P2 终局收口，2026-08-22

## 裁决

- `route_disposition`: `R1_P2_NO_CREDIBLE_EVENT`
- `lifecycle_state`: `BLOCKED`
- `claim_status`: `NO_SCIENTIFIC_METHOD_CLAIMS`
- `source_review`: `P1_PASS_WITH_SCOPE_REDUCTION`
- `P2_run`: `20260822T142511Z-pilot-r1-p2-event-001`
- `execution_status`: `COMPLETED`
- `numerical_validity`: `VALID_R1_P2_BOUNDED_NEGATIVE_EVENT_SCREEN`
- `next_route`: `R2_FULL_DESIGN_PROPOSAL_ONLY_NOT_AUTHORIZED`

## 已核验事实

- `VERIFIED_IMPLEMENTATION`：新的 `R1PhysicalContract`、A×H 四个因子单元、独立 SciPy CPU oracle、预结果事件/收敛阈值、零驱动耗散检查、canonical HDF5 adapter 和 P2 外部裁决器已实现；新增 5 项单元测试通过。旧 TAPF/ETPF/EAF 对象未被修改、重命名或复活。
- `VERIFIED_SOURCE_REVIEW`：11 项定向一手来源支持透明 `derived/synthetic` 电—热—Allen–Cahn 类别；IRAC 因直接先例高度碰撞降为支撑性适配，KC′只保留 `eta` 场局部单调时钟与完整回拉的窄假设。没有 VO2 定量、优先权或首创主张。
- `VERIFIED_ZERO_DRIVE`：A1H1 medium 零驱动检查通过；最大温升 `0.0 K`、最大电流 `0.0 A`、跨阈值相区占比 `0.0`、最大自由能增量 `-5.954319192643809e-19`、最大平衡违规 `2.7155769284996245e-13`。
- `VERIFIED_EXECUTION`：四个预冻结升序电压 `0.65/0.80/0.95/1.10 V` 全部完成；共 5 个 CPU solve，声明单线程，墙钟 `79.656 s`，远低于 `48 h` 或 `64 CPU-core-hours` 上限。全部场有限，最大平衡违规介于 `2.92e-13` 与 `4.14e-10`，没有 phase clipping。
- `VERIFIED_DEVELOPMENT_NEGATIVE`：`0/4` 电压通过双周期合取事件门，因此选择规则没有产生参考电压，粗/中/细收敛运行未启动，P3 资格化 intent 为 `0/12`。

## 固定电压结果

| Drive | 最大相区占比 | 异步 | 局部/部分 | 周期 1 | 周期 2 | 失败边界 |
|---:|---:|---|---|---|---|---|
| `0.65 V` | `0.0000` | 否 | 否 | 未形成 | 未形成 | 温升最高 `342.73 K`，但无跨阈值相态事件。 |
| `0.80 V` | `0.0444` | 是 | 是 | gain `0.0444`、drop `0.0267` | gain `0.0267`、drop `0.0333` | 首周期恢复降幅和第二周期形成增量低于冻结门槛。 |
| `0.95 V` | `0.3244` | 是 | 是 | peak/recovery `0.1067/0.0622` | peak/recovery `0.2756/0.0978` | 周期间残留累积，两个 recovery 均未回到各自冻结基线带。 |
| `1.10 V` | `0.5289` | 是 | 否 | peak/recovery `0.3911/0.3600` | peak/recovery `0.3933/0.1000` | 首周期几乎不恢复，峰值包围盒覆盖全域，违反局部事件门。 |

## 失败根源

- `SUPPORTED_INTERPRETATION`：冻结电压轴呈现清晰的形成—残留权衡，而不是数值崩溃。弱驱动不足以形成两个周期；增强驱动后，第一周期残余相区成为第二周期基线，最终转为跨周期累积或近全域覆盖。
- `SUPPORTED_INTERPRETATION`：该 v1 合同的冷态 phase mobility、`50 ns` off-window、热/导电正反馈与初始成核场组合，不能同时满足“足够形成”和“每周期回到冻结基线带”。这是当前派生对象的事件资格失败，不是阈值实现错误。
- `SUPPORTED_INTERPRETATION`：由于没有任何 medium 事件通过完整合取门，继续做网格加密只会资格化一个已不合格对象；按预声明停止规则不运行收敛、四单元资格化、raw PINN 或六臂方法 pilot。

## 边界

本裁决只关闭 `r1-etac-derived-v1` 在冻结参数、A1H1 目标、四电压轴和事件门下的 R1 路线。它不证明 Allen–Cahn、电热相场、PINN、KC′或自适应采样一般无效，也不评价 P4/P5 方法增量。授权包 A 在 P2 停止；P3–P5、P6–P8、formal/reserve、GPU 和付费计算均未启动。下一步至多形成新的 R2 `FULL_DESIGN` 计划，必须另获用户批准后才能执行。

