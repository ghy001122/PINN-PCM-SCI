# PLAN-PHK-V2.3-R0A：STRONG_RAW 本地 CPU 只读失效诊断

- `phase_id`: `PHK_V23_R0A_CPU_DIAGNOSTICS_AND_CONTRACT`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_TERMINAL_NO_GO_PRESERVED_R0A_INCONCLUSIVE_NO_METHOD_EVIDENCE`
- `next_research_execution_authorized`: `false`
- `authorization_state`: `R0A_CONSUMED_CLOSEOUT_AND_SELECTIVE_GIT_ONLY`
- `plan_status`: `R0A_INCONCLUSIVE_COMPLETE`
- `current_stage`: `R0A_CLOSEOUT_COMPLETE`
- `supersedes`: `PLAN_PHK_V22R_V11_TERMINAL_NO_GO`
- `preserves`: `PHK_V22R_TERMINAL_NO_GO_RUN_DECISION_CLOSEOUT_AND_PAPER`
- `program_contract`: `configs/phk_v23/program_contract.json`
- `method_contract`: `configs/phk_v23/method_contract.json`
- `diagnostic_contract`: `configs/phk_v23/r0a_diagnostic_contract.json`

## 唯一执行项

在 `HEAD=3dac71ed9197f565c470ab229b039e086615d678`、三份 R0A 合同、focused tests、legacy 回归与文档一致性门全部通过后，只允许执行一次：

1. 在本地 CPU/FP64 加载既有 seed-17 `STRONG_RAW` final checkpoint；
2. 使用不读取 reference 的 2048 点四窗均衡 Sobol pool 和 512 点梯度子集；
3. 记录 latent、解析输出 Jacobian、PDE 分项、六 loss × 三 head 梯度矩阵与状态校验；
4. 释放模型计算图后，只在本地读取 nominal development reference，做离散/代数与单场 teacher substitution；
5. 输出 `R0A_ROOT_CAUSE_IDENTIFIED` 或 `R0A_INCONCLUSIVE`，写入机器产物、实验 ledger 与 closeout；
6. 立即停止，不自动进入任何后续阶段。

## 硬边界

- GPU、AutoDL 与新增付费均为 0；CPU wall time 不得超过 4 小时。
- 不构造 optimizer、不调用 `optimizer.step`、不更新参数、不改 checkpoint、不训练。
- nominal reference 不得进入 loss、初始化、gate、sampler、collocation、阈值、超参、checkpoint selection 或 early stop。
- 两份 stress reference 继续 `SEALED_UNREAD`，在任何 R0A 数据流中均不可达。
- 不实施 R0B、R1、PJGR、recovery intervention、seed/预算/阈值搜索。
- V2.2R terminal No-Go、英文 bounded-negative 稿和全部历史证据保持原样。

## 停止条件

任何身份漂移、stress 可达、状态字节变化、测试失败、非有限值、超过 4 小时或需要 GPU/云端，均立即以相应 blocker 收口。正常完成后 `next_research_execution_authorized=false`；若 `R0A_INCONCLUSIVE`，只允许记录且不执行一个后续建议。

## 当前处置

唯一 R0A 已完成并返回 `R0A_INCONCLUSIVE`。机器 artifact、实验 manifest 与 closeout 已写入；V2.2R terminal No-Go 保持不变。当前只允许结果复核、验证与本次选择性 Git 交付。

唯一未执行建议为 `R0B_FIRST_SWITCH_175`，因为它在保持 schedule denominator `1000` 时覆盖首次 causal switch。该建议不构成授权；任何 R0B、R1、PJGR 或 GPU 动作都需要新的版本化合同和用户明确批准。
