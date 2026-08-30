# PINN-PCM-SCI 当前研究总览与论文口径

本文件是当前研究设定、规范术语与论文表述的单一来源，不承载授权、行动清单或易过期的运行结果。当前路线为 `PHK-V2.2R / RAPID METHOD-RESCUE AND POSITIVE-EVIDENCE SPRINT`；它是独立于 PHK-V2.1 Oracle No-Go 的 fixed-discretization Method-MVP，不改写任何历史证据。

- `document_role`: `CURRENT_RESEARCH_SETTING_AND_PAPER_LANGUAGE`
- `updated_at`: `2026-08-30`

## 当前研究问题

`HYPOTHESIS`：二维电—热—相态 wall-cell 的关键相区和 Joule hotspot 只占小测度区域。普通强 PINN 倾向先学习平滑背景，因 representation bandwidth 与 collocation support 分配不匹配而欠分辨局域相区。场选择性各向异性多频表示与 phase/Joule-aware sampling 可能在固定预算下改善相区形貌，同时保持温度、端电流和事件拓扑非劣。

默认候选方法为：

> **FS-PJAMF-PINN: Field-Selective Phase–Joule-Aware Anisotropic Multi-Frequency Physics-Informed Neural Network**

它包含两个同一问题驱动的主体接口：

1. (v) 采用轻量低/中频表示，θ 与 φ 使用面向 (x,z,t) 不同尺度的各向异性多频表示；
2. collocation 预算由 Sobol uniform、residual、phase indicator 和 Joule density 四池共同分配，且 uniform quota 始终大于零。

当前冲刺采用四臂固定比较：`STRONG_RAW`、`MF_ONLY`、`SAMPLER_ONLY` 与
`MF_PLUS_SAMPLER`。只有完整组合可以作为 proposed method 晋级。Strict PHA 已完成唯一
100-update profile；成本门通过但增益门失败，按预声明规则退出关键路径且不得调 gate。
generic-RAR 的 P0 截止已过且未形成稳定实现，因此本周采用四臂 fallback，不再新增该控制。

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

- **nominal extra-fine**：development-only fixed-discretization reference，可用于超参数/选路/checkpoint/图表；不得成为 A 的标签、anchor 或 sampler feature。
- **narrow-interface extra-fine**：sealed confirmation；候选冻结前不可读。
- **wide-heater extra-fine**：sealed confirmation；候选冻结前不可读；逐周期 event vector 由该 reference 开封后自动确定。
- **medium carriers**：保留为历史/稿后研究资产；本周 v1.1 不启用 Route B，不生成训练 anchors。

三个 case 只能支持 case-specific robustness 或 bounded regime evidence，不能称 formal OOD、device/material generalization。

## 当前冲刺路线

四臂训练信号只含 PDE、IC 和 BC residual，论文身份为 physics-only PINN。Route B/C 本周
停用；若 strong raw 不具基本 competence，或完整组合没有预声明的可归因增益，则按真实
No-Go 收口，不得借 sparse anchors、新架构、换 seed、延长训练或新模块继续寻找正结果。

## 评价与可写主张

- primary：time-averaged phase-region symmetric difference；
- co-primary：phase ROI continuous-field RMS；
- hard guards：finite、phase bounds、reference event vector、recovery、locality、无假全域转变；
- non-inferiority：temperature ROI RMS 与 terminal-current trace RMS；
- secondary：event time、Hausdorff、hotspot/FWHM、high-k、pulse energy、wall time、peak memory。

(U_j) 统一称 resolution-sensitivity margin。小于该敏感范围的改善只允许表述为“更好逼近固定离散参考”，不得写成超过数值不确定性或 continuum accuracy。

真实结果只可路由为三种有限正向故事：主要精度、sharp-transition regime 条件优势或
accuracy–cost Pareto。若均不成立，则保存最小 No-Go 并完成证据一致的初稿，不制造正结论。

## 规范术语与研究纪律

- **fixed-discretization numerical reference**：固定网格、时间步与输出采样下的数值参考；不得写成 continuum oracle、ground truth 或实验真值。
- **development case**：允许在冻结预算内选路、调参和做功能等价替换的 nominal case；其 reference 只参与本地评分，不进入 Route A 的训练信号或 sampler feature。
- **sealed confirmation case**：候选、阈值、损失、预算与评价口径冻结后才可开封的 stress case；开封结果只能决定 PASS、No-Go、regime-aware 或 Pareto 边界，不能反馈调参。
- **functional pivot**：仅保留为历史 v1 术语；v1.1 nominal 前不再允许 functional pivot。
- **candidate freeze**：结束开发并固定方法身份、训练合同、评价合同和确认矩阵的不可逆边界。
- **Method-MVP**：包含可运行方法主体、强 comparator、关键消融、真实有限结果和可复现入口的导师评审稿；不等于可直接投稿的完整多-seed/formal-OOD 证据包。
- **device-level QoI**：由预测场按冻结公式确定性计算的端电流、Joule energy、phase area、peak temperature、event topology 与 recovery；不是另一个可训练标签。
- **A→A′ adaptation**：透明保留底层模块来源，同时把 PCM 定向接口、场选择、轴向频带、物理采样配比和联合预算分工明确为本项目适配贡献。

P0 只允许把合同、实现、runner、评价与稿件对齐到已批准的 v1.1；P0 门禁后方法、更新数、
seed、指标、阈值、比较臂和预算立即冻结，不再结果导向调参。任何故事包装只能在已测证据
支持的预声明分支中选择，不得编造结果、隐藏不利 case、抹除来源或在开封后移动标准。

## 论文故事

普通 PINN 像平均分配清晰度的相机：大范围平滑背景很快学好，却把决定器件状态的小相区和热点拍糊。全局 Fourier 相当于全域一直开高倍镜，可能浪费容量并加重二阶 AD。FS-PJAMF-PINN 为不同物理场和方向分配不同频带，再用 phase/Joule physics 分配训练点；预测场确定性地产生端电流、Joule energy、phase area、peak temperature、event topology 与 recovery，从而检验局部场改善是否传递到器件输出。

底层 Fourier、多尺度表示、Sobol、RAR、causal/staggered/continuation 均有先例。可主张的项目贡献只能是透明的 PCM 定向 A→A′ 接口、联合预算分配、机制归因和真实固定预算增量；不得隐藏来源或声称底层模块首创。

## 权威与状态路由

当前授权只读 [active phase](active_phase.md)，已核验实现与运行状态只读 [project state](PROJECT_STATE.md)，下一步只读 [live plan](docs/plans/NEXT_ACTIONS.md)。profile 后的 v1.1 决定见 [ADR 0048](docs/adr/0048-activate-phk-v22r-v11-four-arm-sprint-after-gpu-profile.md)；旧 [program contract](configs/phk_v22r/program_contract.json) 和 [method contract](configs/phk_v22r/method_contract.json) 必须在 nominal 前完成版本化对齐。近期研究策略的受约束整合见 [2026-08-29 strategy integration](docs/notes/2026-08-29-phk-v22r-recent-research-strategy-integration.md)。历史 V2.1、V2 和 V1 证据分别由 `paper/paper_v21/`、`paper/paper_v2/` 和 `paper/paper_v1/` 路由。
