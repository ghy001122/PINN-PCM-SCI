# 0029：授权 R2 严格热耦合 FerroX 的 P0 来源门

- `status`: `ACCEPTED`
- `accepted_at`: `2026-08-22`
- `decision_scope`: `R2_STRICT_THERMAL_FERROX_FULL_DESIGN_PACKAGE_A`
- `claim_status`: `PROPOSED_METHOD_NO_NUMERICAL_EVIDENCE`
- `decision_id`: `R2_STRICT_THERMAL_FERROX_FULL_DESIGN_2026-08-22`

用户接受 R2 `FULL_DESIGN`，选择“严格热耦合 FerroX”和“PINN 方法主线”。普通批准只打开授权包 A：最多 12 项一手来源、零求解的 P0 来源与热机制准入；B–D、FerroX 重放、oracle、训练、formal、GPU、付费计算和 Git 发布均不自动授权。

R2 候选对象是 source-pinned FerroX-derived HZO 二维 y-invariant MFIM 严格电热极化畴器件，整体证据身份为 `derived/synthetic`。R2-v1 只允许以热力学推导的 TDGL 极化切换耗散为主发热机制，并要求 HZO 绝对时间、温度依赖动力学/自由能、热物性、界面热边界和可辨热反馈同时闭合；Joule/leakage 热不在本合同内，若不可忽略则路线 No-Go 而不是扩方程救援。

P0 同时冻结来源/许可身份、量纲与可辨识性、双极畴事件、创新碰撞和温度动力学时钟假设。任一关键项不闭合即以来源、热闭合、热价值或新颖性 No-Go 收口；只有 `R2_P0_PASS_STRICT_THERMAL` 可以形成下一授权包供用户审查。R3 及其他对象不自动接替。

## 执行结果

授权包 A 于 2026-08-22 在 `0 solve / 0 training intent / 11 primary-source cards` 内完成。FerroX 论文短哈希可解析为完整 commit/tree，但固定 tree 内没有许可文件；论文所列 AMReX 短哈希经官方仓库当前无法解析。按预声明的最早硬门，单一裁决为 `R2_P0_SOURCE_IDENTITY_NO_GO`。B–D 未授权、未进入；见 [P0 来源与碰撞报告](../references/2026-08-22-r2-ferrox-strict-thermal-p0-source-and-collision-review.md)。
