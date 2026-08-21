# Live plan：选择新的事件可验证二维 substrate

- `phase_id`: `BOUNDED_METHOD_IMPLEMENTATION_NEGATIVE_CLOSEOUT`
- `lifecycle_state`: `AWAITING_NEW_SCIENTIFIC_ROUTE`
- `blocker_id`: `RAW_EVENT_NOT_RESOLVED_AFTER_BOUNDED_IMPLEMENTATION_REPAIRS`
- `authorization_state`: `NEW_SCIENTIFIC_CORE_NOT_YET_APPROVED`
- `execution_authorized`: `false`
- `claim_status`: `BOUNDED_NEGATIVE_DEVELOPMENT_RESULT_NO_FORMAL_EVIDENCE`

## 唯一下一步

形成并由用户确认一个新的、事件先验可验证的二维电—热—相态 substrate 合同。推荐候选是受控的二维电—热—Allen–Cahn phase-field benchmark；本阶段只允许冻结科学边界，不允许实现或运行。

## 准入条件

- 说明它与 Q‑POP 热力学和低/中场工作域的可追溯关系；
- 独立数值 oracle 与 PINN 残差不得复用同一实现；
- 预注册单案例 raw 事件能力门、最大实际计算预算和一次性停止条件；
- 保留当前 R3、R4、N1/N2、PHA/KC 的全部负面证据，不通过更换 substrate 寻找 KC 正结果；
- 只有新的 strong-raw 门通过后才允许 KC 判别 pilot；formal、GPU 和外部费用继续关闭。

## 预期产物

- 一份明确标注科学核心变化的 ADR；
- 一份可直接执行的 bounded smoke/pilot plan；
- 论文主张、强 raw 基线、KC 消融、完整 case 拆分和停止条件的映射。

## 停止条件

若候选不能同时满足二维电—热—相态闭环、独立 oracle、可构造结构事件和有界计算预算，则不进入实现；不得退回 R3/R4 或追加旧路线救援。

历史执行事实见 [R4 与 raw-v3 收口记录](../experiment/2026-08-21-r4-and-raw-v3-closeout.md)。
