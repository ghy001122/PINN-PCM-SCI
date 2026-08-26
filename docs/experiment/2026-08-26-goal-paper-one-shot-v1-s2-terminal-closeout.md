# GOAL-PAPER-ONE-SHOT-V1 S2 终局收口（2026-08-26）

## 裁决

- `route_disposition`: `SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO`
- `scope`: 仅限 `SYN_EDT_2D_V1` 在下列冻结 `S0/S2` 合同及资格化梯度下的 S2 CPU 数值执行。
- `claim_status`: `NO_ORACLE_EVENT_OR_PINN_EVIDENCE`
- `numerical_disposition`: `Q0_ZERO_DRIVE_GUARD_VERIFIED; FIRST_DRIVEN_QN_INTENT_EXECUTION_FAILED; CROSS_RUN_ADJUDICATION_NOT_REACHED`
- `rerun_disposition`: `NO_PRODUCTION_RERUN_NO_RESCUE`

这是一项数值合同终止裁决，不是物理对象、缺陷输运方程、PINN 或任何方法类别的一般性失败结论。

## 冻结身份与实际证据载体

| 载体 | 实际路径 | SHA256 / 绑定 |
|---|---|---|
| 生效 S2 freeze manifest | `docs/experiment/manifests/20260826T113537Z-goal-paper-one-shot-v1-s2-freeze-002.json` | `74B5CD92A5271FD481A134DD52A80DD22FC65DC6784F761C5B8B74B880AB2F35` |
| Q-only case manifest | `outputs/runs/20260826T113537Z-goal-paper-one-shot-v1-s2-freeze-002/case-manifest-q-only.json` | `EF093A5C2F2E798FF05E768C3D0837CF08C3E10FD6AE79B432F26585F0FCD09C` |
| S0 contract | `configs/goal_paper_one_shot_v1/s0_contract.json` | `947E737A255D27A7BB2553286809ADB98219FD4E48B932B170CB06608A2E3A75` |
| S2 numerical contract | `configs/goal_paper_one_shot_v1/s2_numerical_contract.json` | `D059AA2261CC227C3B16B7965A75C461AD64110C2A20C3700B62E54FDE25E8E6` |
| Q0 intent-01 manifest | `docs/experiment/manifests/20260826T113638Z-goal-paper-one-shot-v1-s2-intent-01-q0.json` | `6451DFC6C1E331A0AF86997FDCC74083CD4C8C781C96C2C2A156EB149504205E` |
| Q0 case / evaluation / report | `outputs/runs/20260826T113638Z-goal-paper-one-shot-v1-s2-intent-01-q0/` | `01F5DCF28E25A75E74C5EDBE612456A542ECA36EFFCB8CAFEC196AE4994F7A01` / `F24439F92CBC70FDED7A24DE1D0B6272E59D14A169CCB86A1FAA888E21BDAE6B` / `0964E3B55431AA49CDE158FFF7F98F3478288865A6DE670CC88ABD9B7BF3D1A8` |
| QN intent-02 manifest | `docs/experiment/manifests/20260826T113752Z-goal-paper-one-shot-v1-s2-intent-02-qn-coarse-fine.json` | `A1806D03A1D5F8687FCE252F66BA2CCE921DA78902EADA149B5A84C42CE0ECB8` |
| QN intent / atomic claim | `docs/experiment/intents/20260826T113752Z-goal-paper-one-shot-v1-s2-intent-02-qn-coarse-fine.json`; `docs/experiment/intent_claims/s2-intent-02.json` | `DC2A38B5BF9F560A2A64D78733647C02906CF225C8392699614E5DAC778D4AE5`; `CF7FB0E8C8F5DF05C16F1E13F88C75C68FEE9F3D23F93427FA952A161C2A8B7C` |

`freeze-002` 明确 `supersedes` `20260826T110938Z-goal-paper-one-shot-v1-s2-freeze-001`，并把 S0、S2 和 case-manifest 哈希写入 manifest；因此本收口只以 `freeze-002` 为生效 freeze。

## VERIFIED — Q0 零驱动守卫

- `run_id`: `20260826T113638Z-goal-paper-one-shot-v1-s2-intent-01-q0`
- `execution_status`: `COMPLETED`
- `ladder`: intent `1`, `Q0`, `coarse/coarse`, `FULL`
- 400 个时间步全部完成；`block_iterations_total/max=400/1`，`final_transport_scaled_residual_max=0.0`。
- 零驱动下 `y_min=y_max=0.5`，温度仅有浮点舍入范围 `299.9999999999985–300.00000000000034 K`；质量漂移、无通量残差、热平衡残差及端口电流不匹配均为 `0.0`，全部 hard guards 通过。
- 事件检查按合同为 `applicable=false`；这验证的是零驱动守恒与产物链，不是 driven event、oracle 资格化或跨分辨率收敛。
- manifest 保持 `numerical_validity=PENDING_S2_CROSS_RUN_ADJUDICATION` 和 `claim_status=NO_ORACLE_EVENT_OR_METHOD_CLAIM_SINGLE_CASE_ONLY`，不得提升为 oracle/event 证据。

## VERIFIED — driven 执行失败

- `run_id`: `20260826T113752Z-goal-paper-one-shot-v1-s2-intent-02-qn-coarse-fine`
- `ladder`: intent `2`, `QN`, `coarse/fine`, `FULL`；这是 Q0 后首个 driven 资格化 intent。
- `execution_status=FAILED`，`gate_outcome=SYN_EDT_S2_EXECUTION_FAILED`，`route_disposition=SYN_EDT_S2_EXECUTION_INVALID_STOP`，`numerical_validity=NOT_EVALUATED`。
- 冻结执行在生成 case、evaluation 或 report 产物前抛出 `RuntimeError: transport Newton exceeded its frozen iteration limit`；对应 run root 为空。
- 失败 manifest 记录 `solver_intents=1`、`failed_intents=1`、`failed_intent_consumed=true`、`rescue_attempts=0`。该失败 intent 计入 40 个 CPU solver-intent 总上限；连同 Q0，本 S2 已消费 2 个 solver intent，其中 1 个失败。Q0 与失败 intent 的记录 CPU 量合计为 `0.002326388888888889 CPU_PROCESS_CORE_HOURS`。
- 冻结合同禁止 timestep rescue、parameter rescue 和 post-result solver-threshold change。失败后没有生产重跑、替代阈值运行或自动 replay；intent `3–13` 未启动。

## NON_SCIENTIFIC_DIAGNOSTIC — 数学相容性定位

以下诊断来自 `tests/test_syn_edt_2d.py` 中显式标记的最小 QN fixture：12 个 active cells、单个 `0.00125 s` 时间步和首个 QN ramp 端点 `0.01125 V`。它只复现失败类别，不是生产网格、oracle 或论文科学结果。

### Inner transport Newton：`0.5 / 20 / 1e-10`

- 冻结 inner Newton 的初始线搜索步长为 `0.5`，只允许继续二分而不允许增至全步；最大迭代数为 `20`，scaled-residual 阈值为 `1e-10`。
- 在上述 fixture 中，初始 scaled residual 为 `1.5106745331996967e-3`；20 次被接受的步长全部为 `0.5`，第 20 次后的 residual 为 `1.4406930175716191e-9`，仍高于 `1e-10`。实测比值 `9.536753191437917e-7` 与 `2^-20=9.5367431640625e-7` 一致。
- 对近线性 Newton 局部模型，固定半步给出 `r_(k+1)≈0.5 r_k`。20 次半步要达到 `1e-10`，初始 residual 必须不高于 `1e-10 × 2^20 = 1.048576e-4`；fixture 的初值约为该上限的 `14.41` 倍。因此 `initial_step=0.5`、`max_iterations=20` 与 `tolerance=1e-10` 对这个已到达状态在数学上不相容，触发的是预注册 solver contract 的确定性停止条件。
- 同一 fixture 上，解析 Jacobian 与中心有限差分方向导数的相对无穷范数误差为 `1.7339861280712171e-10`。这在该状态下排除了“Jacobian 装配明显错误”作为近因；它不证明所有网格和状态的 Jacobian 都无误。

### Latent outer block：`0.5 / 12 / 1e-8`

- outer electrothermal-transport block 同样冻结 relaxation `0.5`、最多 `12` 次和 relative-change 阈值 `1e-8`。
- 即使按理想一阶半衰减，12 次后也只缩小到 `2^-12=2.44140625e-4`；要在 12 次内达到 `1e-8`，初始归一化 mismatch 必须不高于 `4.096e-5`。
- intent-02 先在 inner Newton 终止，因而 production run 从未到达 outer 判定。本项是合同结构的 latent 数学风险，不是已观测 outer failure，也不能作为修改阈值后会成功的证据。

## UNKNOWN

- `UNKNOWN`: 冻结 driven QN 案例是否存在满足全部数值门槛的成功离散解；当前合同在首个 driven intent 即停止，未产生可裁决场。
- `UNKNOWN`: spatial/time/replay floor、QN 双周期事件、QL/QH bracket、两个热控制及 thermal-effect gate；相应 intent 均未执行。
- `UNKNOWN`: 若改变 relaxation、迭代上限、容差、时间步或求解算法，driven 路线会成功还是暴露新的 outer/物理/数值失败。任何此类改变都会定义新合同，不能回写本次冻结结果。
- `UNKNOWN`: PINN、raw baseline、CTH/KC、OOD、formal 或 reserve 表现；S2 没有产生可供其消费的 oracle/event 证据。

## 主张边界与停止动作

最终固定裁决为 `SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO`。可主张的只有：Q0 零驱动守卫在冻结产物链上通过；首个 driven QN intent 按冻结 inner-Newton 限制执行失败；非科学 fixture 将近因定位为 solver 阈值组合的数学不相容，并在该 fixture 状态下未发现 Jacobian 差分冲突。

不得主张 `SYN_EDT_2D_V1` 已形成合格 oracle，不得主张存在双周期 event，不得主张 PINN 或任何方法有效/无效，也不得把 fixture 数字写成科学结果。按预注册停止规则，本合同下不做生产重跑，失败 intent 保留并计入预算；S2 不授权下游 raw/PINN/development/formal 以此对象产生正面方法证据。
