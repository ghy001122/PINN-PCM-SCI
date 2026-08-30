# ADR 0049：激活 PHK-V2.3 R0A 本地 CPU 只读失效诊断

- `status`: `ACCEPTED_COMPLETE`
- `date`: `2026-08-30`
- `phase_id`: `PHK_V23_R0A_CPU_DIAGNOSTICS_AND_CONTRACT`
- `supersedes`: `ADR_0048_FUTURE_RESEARCH_AUTHORIZATION_ONLY`
- `preserves`: `ADR_0048_AND_PHK_V22R_TERMINAL_NO_GO_RUN_DECISION_CLOSEOUT_AND_PAPER`
- `decision_source`: 当前用户明确批准 `EXECUTE PHK_V23_R0A_CPU_DIAGNOSTICS_AND_CONTRACT`

## 决定

接受 PHK-V2.3 的第一项有界科研动作：对既有 nominal `STRONG_RAW` final checkpoint 执行一次本地 CPU/FP64 只读诊断。它只定位共享 competence failure；不训练、不更新参数、不构造 optimizer、不选择 checkpoint，也不建立新方法或正向主张。

三份版本化合同分别固定授权/预算、legacy 方法身份与诊断 schema。诊断采用 2048 个四窗均衡 Sobol 点，梯度子集为每窗冻结顺序的前 128 点；参数、缓冲、模型模式和 CPU RNG 在诊断前后必须保持一致。输出只能是 `R0A_ROOT_CAUSE_IDENTIFIED` 或 `R0A_INCONCLUSIVE`。

## Reference 边界

nominal extra-fine reference 只允许在模型侧测量和梯度 probe 完成、计算图释放、身份守卫通过后，以 `NOMINAL_LOCAL_DIAGNOSTIC_ONLY` 角色本地读取。它不得进入 loss、初始化、gate、sampler、collocation、阈值、超参、checkpoint selection、early stop 或云端。两份 stress reference 继续 sealed/unread，R0A 入口在任何 candidate freeze 状态下都不可达它们。

## 计算与停止

- 设备：本地 CPU；dtype：FP64；`CUDA_VISIBLE_DEVICES=""`。
- 单次 R0A；CPU wall time 硬上限 4 小时；GPU 0 小时；新增云成本 0 元。
- 身份漂移、state bytes 改变、stress 可达、测试失败、非有限值、超时或需要 GPU/云端时立即停止。
- 正常完成后不自动授权 R0B、R1、R2、PJGR、low-fidelity pivot 或投稿。

## 保留的科学结论

PHK-V2.2R 的 `MVP_NO_GO_NO_BASIC_COMPETENCE`、四臂运行、裁决、终局 closeout 和 bounded-negative advisor draft 全部保持原样。R0A 工程或诊断完成不等于恢复 strong-raw competence，也不构成方法增益。
