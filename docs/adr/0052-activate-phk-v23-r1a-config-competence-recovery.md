# ADR 0052：激活 PHK-V2.3 R1a ConFIG competence recovery

- `status`: `ACCEPTED_ACTIVE`
- `date`: `2026-08-31`
- `decision_id`: `ADR_0052_ACTIVATE_PHK_V23_R1A_CONFIG_COMPETENCE_RECOVERY`
- `supersedes`: `ADR_0051_FUTURE_RESEARCH_AUTHORIZATION_ONLY`
- `preserves`: `ADR_0051_R0C_RESULT_ADR_0050_R0B_PRECURSOR_R0A_AND_V22R_TERMINAL_NO_GO`

## 决策

根据用户对 `PHK_V23_R1A_CONFIG_COMPETENCE_RECOVERY_EXECUTE` 的明确授权，激活一次有界的 solver-level competence-recovery 实验。冻结科学问题是：在物理对象、STRONG_RAW 网络、seed、点集、causal schedule、Adam、学习率、裁剪、1000-update 预算与评价器全部不变时，仅把 summed-loss gradient 替换为标准 ConFIG conflict-free gradient combination，能否恢复两个周期的相变事件能力。

ConFIG 来源为 Liu、Chu、Thuerey 的 ICLR 2025 工作及其官方 MIT 代码库 `tum-pbs/ConFIG`，本项目固定上游 commit `94862437f451f175673bce9c85f3e14bd9182c21`。该模块身份为透明迁移适配的 `SHARED_SOLVER_BACKBONE`，不是本论文原创方法或优先权主张。

## 唯一变化轴

原有总目标被精确分解为四组：

1. `G1 = (1/3) * electric normalized PDE MSE`
2. `G2 = (1/3) * thermal normalized PDE MSE`
3. `G3 = (1/3) * phase normalized PDE MSE`
4. `G4 = 5 * existing BC mean + 1 * existing IC mean`

四组标量之和必须在 FP64 `rtol=1e-12, atol=1e-14` 内等于旧总目标。每步分别取四组梯度，按 standard ConFIG 的等方向权、Moore–Penrose minimum-norm target 与 projection-length rescaling 合成一个梯度，再沿用原全局 clip=10 与原 Adam step。任何非有限或退化方向均 fail closed，不切换其他算法。

## 执行和隔离

- 单次 `Tesla V100-PCIE-32GB`、FP64、seed 17、`STRONG_RAW` scratch、1000 updates。
- cloud 只允许 reference-blind training 与 contract-derived reference-free prediction；nominal/stress reference 不得上传或读取。
- 产物回收和逐文件哈希核验后必须立即关闭实例。只有关机确认后，才在本地用未改的 V2.2R nominal evaluator 评价。
- R1a GPU hard cap 1.5 h / 5 CNY；R1a 加未来另行授权的 R1b 总上限 3 h / 10 CNY；项目绝对云费用上限 150 CNY。

## 结果语义

- 全部冻结 competence guards 通过：`R1A_CONFIG_RAW_COMPETENCE_RECOVERED`，只支持 solver-level competence，不能写成 ConFIG 原创或 proposed-method superiority。
- 任一 guard 失败：`R1A_CONFIG_RAW_NO_COMPETENCE`，单次 bounded No-Go；不换 seed、不延长、不自动进入 R1b。
- 非有限：`R1A_NUMERICAL_INVALID_STOP`；预算或基础设施失败：`R1A_BUDGET_OR_INFRASTRUCTURE_BLOCKED`。

无论结果如何，本 ADR 不授权 R1b、PJGR、MultiAdam、第二次运行、stress、投稿或外部联系。
