# GOAL-PAPER-ONE-SHOT-V1 S2 数值与 evaluator 预注册

- `contract_id`: `GOAL_PAPER_ONE_SHOT_V1_S2_NUMERICS_V1`
- `physical_contract_id`: `SYN_EDT_2D_V1_PHYSICS_V1`
- `machine_contract_sha256`: `D059AA2261CC227C3B16B7965A75C461AD64110C2A20C3700B62E54FDE25E8E6`
- `frozen_before`: `FIRST_SYN_EDT_2D_NUMERICAL_RESULT`
- `claim_status`: `NUMERICAL_PREREGISTRATION_ONLY_NO_ORACLE_EVENT_OR_METHOD_EVIDENCE`

本记录在首个 `SYN_EDT_2D_V1` 数值结果出现前，补齐 S0 未逐字定义的离散、evaluator 与资格化顺序；机器可读合同为 [`s2_numerical_contract.json`](../../configs/goal_paper_one_shot_v1/s2_numerical_contract.json)。它只实现 S0，不改变物理参数、几何、波形、事件阈值、预算或失败路线，也不允许以数值结果反向救援对象。

## 首次求解前的一致性修正

在任何生产数值结果或 ledger intent 出现前，派生电流尺度由不一致的 `2.436017492242105e-6 A` 修正为 `2.4363051028588846e-6 A`。后者严格使用同一冻结合同的公式 `2π σ0 L0 VT` 与 `σ0=500 S/m`、`L0=3e-8 m`、`VT=0.02585 V`；该修正不改变任何独立物理参数、阈值或观察结果。合同 loader 必须重新计算并核对该派生量，运行产物只绑定修正后的机器合同哈希。

同样在首个生产数值结果、intent 或 claim 出现前，预生产审计把三项原先只由实现隐含的有限体积语义写入机器合同：异质内部面的总焦耳热按两个半面电阻 `d_i/σ_i` 与 `d_j/σ_j` 的比例分配；保存的 cell-centered 缺陷通量把所有外部 active 边界面以严格零法向通量计入面积平均分母；每个时间步只在返回的松弛后 `y, ψ, θ` 状态上重新计算电势与输运残差且残差不超过 `1e-9` 时才接受。三项均为结果出现前的离散一致性闭合，不改变 S0 物理参数、几何、波形、阈值或失败路线；运行产物只允许绑定上述更新后的机器合同哈希。

## 冻结裁决

1. 使用非均匀 cell-centered 轴对称有限体积；径向体积和面权重显式保留，`r=0` 面面积严格为零。材料掩膜包含 active、bottom electrode 与 top contact，电/热界面连续由共享 face conductance 强制；异质内部面的焦耳热按半面电阻分配。
2. 电流连续与准稳态热用稀疏直接解；热矩阵只分解一次。缺陷输运使用 logit 变量、lattice-gas mobility 的 logarithmic mean 与 backward Euler，内部面通量成对写入，外边界严格 no-flux；保存的 cell-centered vector flux 在边界面积平均中显式包含零法向外部面；不得 clip `y`。
3. 每个时间步最多 12 次电—热—输运 block iteration，缺陷 Newton 最多 20 次；tolerance、阻尼和 line-search 下限已经固定。候选状态经 block relaxation 后，必须在实际返回状态上重算一致电势与输运残差并满足 `1e-9` 门槛。失败记 execution invalidity 或冻结对象 hard-gate failure；不减小时间步、不改参数、不重启救援。
4. evaluator 现在固定 adjacent annulus、首个 `D_k=0.12` crossing、top-connected depleted component、厚度、partial coverage、port sign/response、zero-Joule heat residual、recovery/annulus evaluation time、cycle drift、trapezoid time weighting 和 field-L2 归一化。所有轴对称平均使用真实 cell volume。
5. `DIRECT_T_TO_TRANSPORT_OFF` 只关闭 transport 中的直接温度因子；`FULL_ISOTHERMAL_COUPLING_OFF` 设 `T=T0` 并关闭全部温度依赖。两者不改变电压、几何、初态或其他参数。
6. 资格化使用 13 个顺序 intent：Q0 一个，QN 独立空间/时间五点交叉，QL/QH 两个非投票 bracket，两个 thermal controls 各用 medium/fine 两层，最后一个独立进程 QN fine/fine exact replay 用于 oracle floor。QN 是唯一事件投票 case；任一分支失败不允许用 QL/QH 替代。第 13 个 intent 是预注册不确定度审计，不是 replacement 或 superseding rerun。
7. 六个 cycle endpoint 逐式冻结：ROI concentration field、vector defect flux、first-crossing event time、top-connected gap thickness、unclipped recovery 与 top-current trace。Flux/current normalizer 由 oracle RMS 与固定 characteristic floor 的较大者定义；space/time/replay delta 必须用相同分量公式计算，synthetic `source_joint_uncertainty=0`，逐分量 solver tolerance 为 `1e-6`。全部 `u_j`、`tau_comp` 与 normalizer 在 neural work 前 write-once/hash-seal。
8. Thermal-effect gate 比较 intent 6 的 nominal fine/fine 与 intents 10/12 的两个 fine/fine controls。对每个 control，peak depletion、event time 与 normalized port-current trace 三个 effect 分量中，至少一个共同分量必须在两个 cycle 都超过 nominal space/time/replay 与该 control medium/fine 的对应不确定度，且有方向的 passing effect 在两周期同号。若 nominal 事件通过、control 的非事件硬守卫全部通过且两个周期均不再 crossing，则记有界 censored-effect PASS；单周期或混合 censoring 失败。单独温度差不能通过此门。

## 主张边界

- `VERIFIED`：本记录与机器合同在首个合成对象求解前存在，并把离散/evaluator 歧义固定为工程选择。
- `UNKNOWN`：该离散能否收敛、QN 是否形成合格双周期局部耗尽—恢复事件、thermal effect 是否超过数值不确定性。
- 禁止表述：来源对齐、实验验证、真实材料参数、COMSOL replay、oracle PASS、事件 PASS 或 PINN/CTH 增量。
