# 0028：冻结 R1 四因子、六臂与四池证据设计

- `status`: `ACCEPTED`
- `accepted_at`: `2026-08-22`
- `decision_scope`: `R1_DERIVED_DUAL_STIFFNESS_FULL_DESIGN`
- `claim_status`: `PROPOSED_METHOD_NO_NUMERICAL_EVIDENCE`
- `decision_id`: `R1_FULL_DESIGN_GRILL_2026-08-22`

在两次同源对象扫描零候选及透明派生对象获准后，R1 选择材料类别级 `derived/synthetic` 二维电—热—Allen–Cahn benchmark，以接触/几何不对称和材料非均匀性构成 2×2 物理因子块。目标事件必须具备至少两个局部、部分覆盖、空间异步且离散收敛的 formation–recovery 周期；合成 oracle、传统求解器和实验验证继续保持不同证据身份。

方法不得由标题预先准入。strong raw 先独立判断 `NO_BOTTLENECK`、`RAW_INCOMPETENT_ROUTE_NO_TEST`、`TEMPORAL_ONLY`、`SPATIAL_ONLY` 或 `DUAL_BOTTLENECK`；KC′只重参数化相态时间并完整回拉，IRAC 只使用 detached 的界面与 PDE 残差信号。development 比较固定为强 raw、generic monotone clock、KC′、IRAC、KC′+IRAC 和 IRAC-score shuffle 六臂，以实际计算量匹配，并用预注册 difference-in-differences 裁决组合交互。

完整案例分为 oracle qualification、joint development、one-shot formal OOD 和 reserve 四个互斥角色。开发期允许 benchmark–method 联合迭代并完整留痕，但冻结后不得读取 formal 或 reserve 结果调参；方法自身失败进入 intent-to-run。任一 oracle、瓶颈、raw、方法增量或预算停止门触发即关闭当前路线，单模块阳性主动缩减论文，失败模块不得被组合包装成主要创新。完整 Q1–Q24 合同见 [R1 FULL_DESIGN 决策记录](research_decisions_R1_FULL_DESIGN_GRILL_2026-08-22.md)。本 ADR 记录设计取舍，不单独授予执行；formal OOD 与 GPU 仍需后续授权包 B。

