# 0042：以方法盲对象组合 No-Go 关闭授权包 A

- `status`: `ACCEPTED`
- `accepted_at`: `2026-08-26`
- `decision_scope`: `PACKAGE_A_METHOD_BLIND_OBJECT_PORTFOLIO_TERMINAL`
- `evidence`: [`2026-08-26 方法盲 clean-room 对象筛选`](../references/2026-08-26-method-blind-cleanroom-object-screen.md)
- `claim_status`: `BOUNDED_SOURCE_PORTFOLIO_NO_GO_NO_METHOD_EVIDENCE`

## 背景

ADR 0041 授权在 48 小时、12 项新增一手载体和 3 个新对象家族的上限内，以方法盲、首个通过即锁定的方式筛选一个 source-aligned clean-room `derived/synthetic` 二维氧化物电—热—动态内部态对象。`CANDIDATE_NO_GO` 只关闭单个候选；冻结候选全部失败或组合预算耗尽才允许 `PORTFOLIO_NO_GO`。作者 raw 全场解或预封案例角色不是来源硬门，但决定性方程、本构、参数、BC、绝对协议或版本对齐缺口不得猜测补齐。

本轮在 2026-08-26T01:02:21+08:00 冻结 Sandia/Charon 3D TaOₓ、2026 HfO₂/Al₂O₃ baffle 和 2022 RRAM array crosstalk 三个家族。逐一深审后，三者最早决定性失败均为 Gate 3 合同不完整：候选 1 缺自包含材料/本构数值且 Charon v2.2 不能对齐早期应用；候选 2 缺 vacancy BC/interface、完整电导与热参数，并另缺绝对模拟协议且有 40/30 nm 冲突；候选 3 把决定性参数外引到当前公开链不可核验的 Ref. 29，且不足以支持重复事件与完整案例生成。

## 决定

1. 接受唯一组合级终点 `PORTFOLIO_NO_GO_PACKAGE_A_FROZEN_3_FAMILIES_11_CARRIERS`。它只覆盖本次冻结的 3 个家族、11/12 项新增一手载体和 ADR 0041 的八个来源硬门。
2. 记录 `object_selection_status=NO_OBJECT_SELECTED`、`method_selection_status=NOT_REACHED`、`novelty_status=NOT_REACHED_NO_OBJECT_LOCK`。CTH、strong raw、oracle、pilot、formal OOD 与方法论文主张均未被测试。
3. 授权包 A 已消耗并关闭。剩余 1 项来源名额不是必须填满的配额，也不得转移到新组合；排序较后的 COMSOL tutorial、PCMO 或 ceria 线索不得自动晋升为第四候选。
4. 保留三个候选各自的有界来源负证据，不将其外推为 TaOₓ、HfO₂/Al₂O₃、RRAM、氧化物器件、传统 solver 或 PINN 的一般失败。
5. 后续没有自动科研动作。新对象家族、新来源合同、授权包 B、求解、训练、GPU、formal、论文成稿或 Git/外部发布均须新的 PLAN 与明确批准。

## 被拒绝的替代方案

1. **继续使用第 12 个来源名额寻找正向对象。** 拒绝，因为 3/3 家族预算已经耗尽；预算是上限，不是必须填满的目标。
2. **把 COMSOL Application 141181 提升为第四候选。** 拒绝，因为候选名单与顺序已在深审前冻结，临时晋升会破坏方法盲选择合同。
3. **用通用材料值、软件默认 BC 或响应拟合补齐缺项。** 拒绝，因为这些量进入 vacancy 守恒、电流、Joule heating、热反馈或事件时标的因果链。
4. **把单次 reset、漂亮 I–V 或空间图直接视为 oracle/event 资格。** 拒绝，因为来源锚点不替代自包含输入合同、独立守恒求解、时空收敛和重复完整事件。
5. **将对象失败解释为 CTH 或 PINN 失败。** 拒绝，因为对象未锁定，所有神经与方法门均为 `NOT_REACHED`。

## 后果

当前论文正向路线在对象前门关闭，只交付可复核的有界来源负证据。ADR 0041 的方法盲选择、候选/组合量词和 clean-room 合同继续作为本轮解释依据，但其包 A 执行授权已由本决定消费。只有新的明确 PLAN、用户批准以及实质不同的对象/来源前提，才能启动另一轮筛选；不得把普通结果不理想当作 superseding rerun 理由。
