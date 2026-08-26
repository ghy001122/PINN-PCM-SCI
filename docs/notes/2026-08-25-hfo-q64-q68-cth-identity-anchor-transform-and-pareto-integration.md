# HFO-NP-v1 Q64–Q68：CTH 身份分离、固定锚点、向量原语、输出变换与 Pareto 效用整合

- `date`: `2026-08-25`
- `document_role`: `ACCEPTED_PLANNING_REVISION_DETAIL_NOT_LIVE_PLAN`
- `status`: `REVISE_BEFORE_FULL_PLAN_FINALIZATION`
- `method_target`: `CTH_PINN`
- `method_admission`: `NOT_ADMITTED`
- `implementation_authorization`: `NOT_AUTHORIZED`
- `claim_status`: `NO_NEW_SCIENTIFIC_EVIDENCE`
- `authority_relation`: 细化 ADR 0039；服从 `CONTEXT.md`、`active_phase.md` 与唯一 live plan
- `execution_in_this_task`: `0 source search / 0 solve / 0 PINN implementation / 0 training / 0 formal / 0 GPU`

## 1. 用户接受的最终处置

| 问题 | 答案 | 当前约束 |
|---|---|---|
| Q64 身份证据复用 | `A` | field-hinge qualification 与 blind identity-development 使用互斥完整案例；同一 microview 不能既选方法又证明方法 |
| Q65 hinge 结点 | `A` | 永久固定来源锚点 `a0`；错位即停止，不重定中心、不学习 knot、不加第二 hinge |
| Q66 transport 原语 | `A` | `h=(h_c,h_J)` 是一个联合向量系数，由同一网络产生；禁止独立 heads、loss weights 或分量级主张 |
| Q67 输出变换 | `A` | 所有臂共用冻结的来源兼容 `C1` 变换 `B`；Jacobian 作用量退化即身份无效 |
| Q68 协议束效用 | `A` | 使用 seen-protocol `IND-5` 与 blind-microview smooth bundle 的双轴 Pareto；`IND-7` 只核算新增协议成本 |

## 2. 证据角色分离

未来 `FIELD_HINGE_RELEVANCE_PLUS` 只使用 qualification complete cases 和训练外连续 solver fields，回答固定来源锚点附近是否仍有值得审查的有限尺度 hinge relevance。只有该门通过，才能冻结 CTH、smooth4、`h=0`、错结点、公共 base、输出变换、配置及判据。

冻结后，`CTH_DIAGNOSTIC_IDENTITY_PROTOCOL` 必须改用互斥的 identity-development complete cases。每个案例仍只训练 `delta in {-1,-1/2,0,1/2,1}`；`delta=+/-1/4` 在所有选择完成后一次打开，不得回流模型、阈值、配置、pilot 或 formal。案例数或预算不足以分离角色时，输出是 `IDENTITY_EVIDENCE_ROLE_INSUFFICIENT`，不是阳性或阴性身份结果。

## 3. 固定结点与单一向量原语

CTH 保留

\[
q_{tr}=q_0+\delta q_1+\delta^2q_2+|\delta|h,
\qquad h=(h_c,h_J),
\]

其中 `delta=(a-a0)/epsilon`，`a0` 只能是 G0 冻结的来源波形锚点。资格证据若把有限尺度尖锐区定位到其他协议值，当前方法假设即失败；不得用该证据重新定义 `a0` 或 knot。

`q0/q1/q2/h` 由一个联合 coefficient-field network 产生，`h_c/h_J` 只是同一 transport representation 的两个物理输出坐标。CTH 与 smooth4 使用相同向量维度、容量、硬 IC/BC 变换、support、forward、自动微分和调参机会；不把任一系数分量解释成唯一真实导数场。

## 4. 共同输出变换有效性

所有比较臂共用事前冻结的 `B`。`B` 必须来源兼容、`C1`、不显含 `delta`、side ID 或 `|delta|`，并保持浓度范围和通量边界的公共合同。identity evaluator 在固定事件 ROI 中检查 `D_qB(q0)h` 的方向、幅值和可观测性；明显饱和、退化或 nullspace 吸收记 `CTH_TRANSFORM_NULLSPACE_INVALID`。该状态表示表示身份无效，不能通过放大 `h`、改 `B` 或展示 latent 热图救援。

## 5. 双轴协议束效用

效用不使用加权总分：

1. **seen-protocol 轴**：CTH 与五个独立、aggregate-compute-matched strong raw PINNs（`IND-5`）比较完整事件保真、守卫和总训练成本；
2. **blind-microview 轴**：CTH 与同样不新增训练的 parameter-conditioned strong raw、smooth4 比较 `delta=+/-1/4` 的场、gap、固定截面通量和端口响应；
3. **新增协议成本**：`IND-7` 只用于报告独立方法补算两个 microviews 的增量成本，不作为零重训预测基线。

CTH 若在 seen protocols 被 `IND-5` 严格支配，且 blind microviews 不优于强平滑 bundle，裁决 `CTH_BUNDLE_UTILITY_NO_GO`。单次推理便宜、参数共享或 coefficient 可视化都不能挽救该失败。

## 6. 当前边界

本整合没有产生 SOURCE、模型保真、热因果、EVENT、SIDE、RAW、TEMPORAL/SPATIAL、FIELD_HINGE、CTH identity、bundle utility 或 novelty 阳性证据。它只收紧 future FULL_PLAN 的设计；所有科研执行权限保持 `false`。
