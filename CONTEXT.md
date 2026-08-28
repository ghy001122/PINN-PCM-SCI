# PINN-PCM-SCI 当前研究总览与论文口径

本文件是当前研究设定与论文表述的单一来源。当前路线为 `PHK-V2.2R / RAPID METHOD-RESCUE AND POSITIVE-EVIDENCE SPRINT`；它是独立于 PHK-V2.1 Oracle No-Go 的 fixed-discretization Method-MVP，不改写任何历史证据。

- `lifecycle_state`: `ACTIVE_PHK_V22_ONE_WEEK_SPRINT`
- `claim_status`: `IMPLEMENTATION_VERIFIED_NEURAL_METHOD_RESULT_NOT_YET_ESTABLISHED`
- `updated_at`: `2026-08-29`

## 当前研究问题

`HYPOTHESIS`：二维电—热—相态 wall-cell 的关键相区和 Joule hotspot 只占小测度区域。普通强 PINN 倾向先学习平滑背景，因 representation bandwidth 与 collocation support 分配不匹配而欠分辨局域相区。场选择性各向异性多频表示与 phase/Joule-aware sampling 可能在固定预算下改善相区形貌，同时保持温度、端电流和事件拓扑非劣。

默认候选方法为：

> **FS-PJAMF-PINN: Field-Selective Phase–Joule-Aware Anisotropic Multi-Frequency Physics-Informed Neural Network**

它包含两个同一问题驱动的主体接口：

1. (v) 采用轻量低/中频表示，θ 与 φ 使用面向 (x,z,t) 不同尺度的各向异性多频表示；
2. collocation 预算由 Sobol uniform、residual、phase indicator 和 Joule density 四池共同分配，且 uniform quota 始终大于零。

Strict PHA 不是必需结论，只允许一次 100-update 探针。若保留，输出 gate 使用 phase pilot 与可微 heater/pulse proxy，复合输出的 gate 导数完整进入 strong-form PDE；实际 (Q_J=\sigma|\nabla v|^2) 只用于 sampler 和评价，避免输出 gate 引入不必要的更高阶导数。

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
- **medium carriers**：只有触发 B 后，才可按固定 1% 时空坐标生成 all-field sparse anchors；同一 medium 不得兼作最终测试真值。

三个 case 只能支持 case-specific robustness 或 bounded regime evidence，不能称 formal OOD、device/material generalization。

## A→B 身份

Route A 的训练信号只含 PDE、IC 和 BC residual，论文身份为 physics-only PINN。

Route B 仅在所有 A arms 都不具基本 competence 时触发。它加入 1% medium、因果窗口与 ROI/bulk 分层 Sobol、同坐标 (v/\theta/\phi) anchors，身份必须写成 sparse-reference-assisted PINN。若 A 已具 competence但 proposed 无增量，直接 `MVP_NO_GO_NO_ATTRIBUTABLE_GAIN`；不得借 B 继续寻找正结果。

B 必须比较 same-anchor sparse raw、same-anchor data-only 和 medium interpolation。未同时建立 physics-informed increment 时停止；multi-fidelity correction C 本周禁止。

## 评价与可写主张

- primary：time-averaged phase-region symmetric difference；
- co-primary：phase ROI continuous-field RMS；
- hard guards：finite、phase bounds、reference event vector、recovery、locality、无假全域转变；
- non-inferiority：temperature ROI RMS 与 terminal-current trace RMS；
- secondary：event time、Hausdorff、hotspot/FWHM、high-k、pulse energy、wall time、peak memory。

(U_j) 统一称 resolution-sensitivity margin。小于该敏感范围的改善只允许表述为“更好逼近固定离散参考”，不得写成超过数值不确定性或 continuum accuracy。

真实结果可路由为四种有限正向故事：主要精度、sharp-transition regime 条件优势、accuracy–cost Pareto、或 sparse-data physics-informed increment。若均不成立，则保存最小 No-Go，不制造正结论或第四套大型负结果包。

## 论文故事

普通 PINN 像平均分配清晰度的相机：大范围平滑背景很快学好，却把决定器件状态的小相区和热点拍糊。全局 Fourier 相当于全域一直开高倍镜，可能浪费容量并加重二阶 AD。FS-PJAMF-PINN 为不同物理场和方向分配不同频带，再用 phase/Joule physics 分配训练点；预测场确定性地产生端电流、Joule energy、phase area、peak temperature、event topology 与 recovery，从而检验局部场改善是否传递到器件输出。

底层 Fourier、多尺度表示、Sobol、RAR、causal/staggered/continuation 均有先例。可主张的项目贡献只能是透明的 PCM 定向 A→A′ 接口、联合预算分配、机制归因和真实固定预算增量；不得隐藏来源或声称底层模块首创。

## 当前证据边界

`VERIFIED`：V2.1 已给出稳定的二维对象与 nominal extra-fine carrier，但 event-time 空间细化不单调，因此其 continuum-oracle route 为 No-Go，PINN 方法阶段未到达。

`VERIFIED`：用户已授权当前 V2.2R 代码、两份 stress extra-fine、AutoDL 150 元上限、当前仓库 commit/push 和完整 Method-MVP 稿；投稿未授权。

`VERIFIED`：V2.2R 三场 strong residual、IC/BC、所需对角 AD、四个 primary
arms、strict-PHA 全导数 probe、physics sampler、训练、prediction/evaluator、
sealed access gate 和 machine decision 已实现并通过 12 项聚焦测试；训练 API
没有 reference field 入口。该状态仅是实现证据，不是方法效果证据。

`IN PROGRESS`：两份 stress extra-fine 已各写 pre-compute intent 并执行唯一一次
solve；候选冻结前只允许生成与字节封存，禁止读取场或指标。

`UNKNOWN`：GPU profile、nominal 方法 competence、方法增量、stress confirmation
与最终论文分支尚待实际运行；不得从实现或测试预写科学结论。

当前执行细节见 [live plan](docs/plans/NEXT_ACTIONS.md)、
[program contract](configs/phk_v22r/program_contract.json) 和
[method contract](configs/phk_v22r/method_contract.json)；决定理由见
[ADR 0047](docs/adr/0047-adopt-phk-v22r-rapid-method-rescue-sprint.md)。历史
V2.1、V2 和 V1 证据分别由 `paper/paper_v21/`、`paper/paper_v2/` 和
`paper/paper_v1/` 路由。
