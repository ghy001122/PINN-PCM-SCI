# PINN-PCM-SCI 当前研究总览与论文口径

本文件是当前研究设定、规范术语与论文表述的单一来源，不承载授权或行动清单。当前路线为已终局的 `PHK-V2.2R / V1.1 FOUR-ARM METHOD-MVP`；它是独立于 PHK-V2.1 Oracle No-Go 的 fixed-discretization 单-seed 负面结果，不改写任何历史证据。

- `document_role`: `CURRENT_RESEARCH_SETTING_AND_PAPER_LANGUAGE`
- `updated_at`: `2026-08-31`

在不改写 PHK-V2.2R terminal No-Go 的前提下，`PHK_V23_R0A_CPU_DIAGNOSTICS_AND_CONTRACT` 已完成一次既有 STRONG_RAW final checkpoint 的本地 CPU/FP64 只读诊断，结果为 `R0A_INCONCLUSIVE`。`PHK_V23_R0B_FIRST_SWITCH_175_MINIMAL_V2` 随后完成一次 seed-17/FP64/STRONG_RAW scratch 175-step reference-blind replay：`GRADIENT_STARVATION` 是 step 10 起、step 25 确认的最早持续 temporal precursor；gradient conflict 与 electrothermal deficit 更晚出现。`PHK_V23_R0C_EFFECTIVE_UPDATE_25_V100` 又完成一次 25-step reference-blind replay，机器裁决为 `R0C_ADAM_PRECONDITIONING_COMPENSATES_RAW_GRADIENT`：raw-gradient starvation 没有以同等量级延伸为 Adam-effective relative-update starvation。三项诊断均未实施 recovery 或 proposed method，不得写成 competence 恢复、方法增益或因果 root。两份 stress reference 继续 sealed/unread，当前无后续执行授权。

## 当前研究问题

`HYPOTHESIS_TESTED_NEGATIVE_UNDER_V11`：二维电—热—相态 wall-cell 的关键相区和 Joule hotspot 只占小测度区域。场选择性各向异性多频表示与 phase/Joule-aware sampling 原拟在固定预算下改善相区形貌；实际四臂均未产生事件，因此本合同没有建立该组合的 competence 或增益。

本轮被检验的方法为：

> **FS-PJAMF-PINN: Field-Selective Phase–Joule-Aware Anisotropic Multi-Frequency Physics-Informed Neural Network**

它包含两个同一问题驱动的主体接口：

1. (v) 采用轻量低/中频表示，θ 与 φ 使用面向 (x,z,t) 不同尺度的各向异性多频表示；
2. collocation 预算由 Sobol uniform、residual、phase indicator 和 Joule density 四池共同分配，且 uniform quota 始终大于零。

当前冲刺采用四臂固定比较：`STRONG_RAW`、`MF_ONLY`、`SAMPLER_ONLY` 与
`MF_PLUS_SAMPLER`。只有完整组合可以作为 proposed method 晋级。Strict PHA 已完成唯一
100-update profile；成本门通过但增益门失败，按预声明规则退出关键路径且不得调 gate。
generic-RAR 的 P0 截止已过且未形成稳定实现，因此本周采用四臂 fallback，不再新增该控制。

`VERIFIED`：四臂均完成 1000 updates 且 PDE loss 下降，但相场始终未超过 0.5 阈值，
两次参考事件全部缺失。冻结结论为 `MVP_NO_GO_NO_BASIC_COMPETENCE`；没有 candidate、
confirmation 或 stress 解封。

## 物理对象

对象沿用 PHK-V2.1 的透明、无量纲、literature-inspired synthetic 2D wall-cell：

\[
\nabla\cdot[\sigma(\theta,\phi)\nabla v]=0,
\]

\[
\partial_t\theta+L_r\partial_t\phi
=\alpha\nabla^2\theta-\gamma\theta
+G\sigma(\theta,\phi)|\nabla v|^2,
\]

\[
\partial_t\phi
=M(\theta)\left[\epsilon^2\nabla^2\phi-\partial_\phi W(\phi,\theta)\right].
\]

该对象闭合 `applied voltage → electric field/current → Joule heat → temperature → phase → conductivity`。它不是 GST/GGST/VO₂ 作者模型重放、材料常数校准、实验器件验证或 continuum truth。

## 参考与数据角色

- **nominal extra-fine**：既有 development-only fixed-discretization reference；R0B 中只能在云端回收关机、reference-blind machine decision 不可变写入后用于本地 non-voting appendix。R0C 完全没有读取 nominal reference fields/metrics。它不得进入 loss、初始化、gate、sampler、collocation、阈值、超参、checkpoint selection、early stop 或 intervention selection。
- **narrow-interface extra-fine**：sealed confirmation；候选冻结前不可读。
- **wide-heater extra-fine**：sealed confirmation；候选冻结前不可读；逐周期 event vector 由该 reference 开封后自动确定。
- **medium carriers**：保留为历史/稿后研究资产；本周 v1.1 不启用 Route B，不生成训练 anchors。

三个 case 只能支持 case-specific robustness 或 bounded regime evidence，不能称 formal OOD、device/material generalization。

## 当前终局路线

四臂训练信号只含 PDE、IC 和 BC residual，论文身份为 physics-only PINN。strong raw 与
其余三臂均不具基本 event competence，因此路线已按真实 No-Go 收口。不得借 sparse
anchors、新架构、换 seed、延长训练或新模块回头寻找正结果；任何新诊断必须成为独立、
重新授权的研究版本。

## 评价与可写主张

- primary：time-averaged phase-region symmetric difference；
- co-primary：phase ROI continuous-field RMS；
- hard guards：finite、phase bounds、reference event vector、recovery、locality、无假全域转变；
- non-inferiority：temperature ROI RMS 与 terminal-current trace RMS；
- secondary：event time、Hausdorff、hotspot/FWHM、high-k、pulse energy、wall time、peak memory。

(U_j) 统一称 resolution-sensitivity margin。小于该敏感范围的改善只允许表述为“更好逼近固定离散参考”，不得写成超过数值不确定性或 continuum accuracy。

当前真实结果只允许路由为 No-Go：PDE loss 收敛和相同的 0.00515 primary 不能覆盖事件
完全缺失。stress 未读，因此不存在主要精度、regime-aware、Pareto 或 sealed robustness 故事。

## 规范术语与研究纪律

- **fixed-discretization numerical reference**：固定网格、时间步与输出采样下的数值参考；不得写成 continuum oracle、ground truth 或实验真值。
- **development case**：允许在冻结预算内选路、调参和做功能等价替换的 nominal case；其 reference 只参与本地评分，不进入 Route A 的训练信号或 sampler feature。
- **sealed confirmation case**：候选、阈值、损失、预算与评价口径冻结后才可开封的 stress case；开封结果只能决定 PASS、No-Go、regime-aware 或 Pareto 边界，不能反馈调参。
- **functional pivot**：仅保留为历史 v1 术语；v1.1 nominal 及其后续确认阶段不允许 functional pivot。
- **candidate freeze**：结束开发并固定方法身份、训练合同、评价合同和确认矩阵的不可逆边界。
- **Method-MVP**：包含可运行方法主体、强 comparator、关键消融、真实有限结果和可复现入口的导师评审稿；不等于可直接投稿的完整多-seed/formal-OOD 证据包。
- **device-level QoI**：由预测场按冻结公式确定性计算的端电流、Joule energy、phase area、peak temperature、event topology 与 recovery；不是另一个可训练标签。
- **A→A′ adaptation**：透明保留底层模块来源，同时把 PCM 定向接口、场选择、轴向频带、物理采样配比和联合预算分工明确为本项目适配贡献。

P0 已把合同、实现、runner、评价与稿件对齐到批准的 v1.1；随后四臂 nominal 按冻结身份
执行并触发 terminal No-Go。R0C 进一步否决把 raw-gradient magnitude starvation 直接等同于 optimizer-effective update starvation；它不改变四臂终局。方法、更新数、seed、指标、阈值、比较臂和预算不再结果导向修改。不得编造结果、隐藏不利 metric、抹除来源或把未执行 stress 写入论文。

## 论文故事

当前论文故事不是“新方法成功”，而是“平均误差掩盖了稀疏事件完全漏检”。四臂都像只学到平滑背景的相机：PDE loss 下降，但决定器件状态的小相区始终没有出现。全域 primary 因事件占比小而只有 0.00515；event guard 先于 scalar ranking，阻止了把漏检包装成高精度。

底层 Fourier、多尺度表示、Sobol、RAR、causal/staggered/continuation 均有先例。本轮不能主张 PCM 定向组合带来增量；只可报告透明接口、预注册 competence gate 与真实固定预算负面结果。不得隐藏来源或声称底层模块首创。

## 权威与状态路由

当前授权只读 [active phase](active_phase.md)，已核验实现与运行状态只读 [project state](PROJECT_STATE.md)，下一步只读 [live plan](docs/plans/NEXT_ACTIONS.md)。终局证据见 [nominal terminal closeout](docs/experiment/2026-08-30-phk-v22r-v11-nominal-terminal-closeout.md)，R0C 诊断见 [R0C closeout](docs/experiment/2026-08-31-phk-v23-r0c-effective-update-25-closeout.md)，稿件见 [paper_v22r](paper/paper_v22r/README.md)。profile 后的 v1.1 决定见 [ADR 0048](docs/adr/0048-activate-phk-v22r-v11-four-arm-sprint-after-gpu-profile.md)；冻结机器身份由 [program contract](configs/phk_v22r/program_contract.json) 和 [method contract](configs/phk_v22r/method_contract.json) 定义。历史 V2.1、V2 和 V1 证据分别由 `paper/paper_v21/`、`paper/paper_v2/` 和 `paper/paper_v1/` 路由。
