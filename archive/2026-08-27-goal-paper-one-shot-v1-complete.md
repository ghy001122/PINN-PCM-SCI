# GOAL-PAPER-ONE-SHOT-V1：一次性自主执行到完整论文初稿

- `phase_id`: `GOAL_PAPER_ONE_SHOT_V1_COMPLETE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO_NO_ORACLE_EVENT_OR_METHOD_EVIDENCE`
- `authorization_state`: `ONE_SHOT_LOCAL_RESEARCH_EXECUTION_CONSUMED_AND_CLOSED`
- `authorization_package`: `S0_TO_S6_AND_LOCAL_MANUSCRIPT_CONSUMED`
- `plan_status`: `COMPLETED`
- `object_selection_status`: `SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO_FROZEN`
- `method_selection_status`: `NOT_REACHED_CTH_DIAGNOSTIC_ONLY_NO_TRAINING`
- `current_stage`: `GOAL_COMPLETE_LOCAL_DELIVERABLES_READY`
- `next_research_execution_authorized`: `false`
- `supersedes`: `PLAN_MSA_01`
- `preserves`: `ALL_HISTORICAL_NO_GO_AND_NEGATIVE_EVIDENCE`
- `effective_date`: `2026-08-26`

## 1. 目标与完成条件

用户已明确批准 `GOAL-PAPER-ONE-SHOT-V1`，本文件是其项目内唯一 live plan。Agent 从当前真实状态开始，按本文件的预注册门和切换表连续执行；门通过后无需逐阶段、逐包或 sealed formal 前再次申请批准。

执行已于 2026-08-26 按冻结 fallback 在 `CLEANROOM_BENCHMARK_AND_METHOD_LIMITS_MANUSCRIPT` 终点闭合。[最终本地论文包](../paper/paper_v1/README.md)与[包清单](../paper/paper_v1/package-manifest.json)满足第 10 节的完整交付条件；一次性授权已经消费并关闭。以下原始门、预算、定义与停止条件继续保留为已执行合同，不授权新研究。

优先终点是 PINN 为核心、二维电—热—守恒缺陷输运闭合、具有强控制与 sealed complete-case formal 证据的正向方法论文。若正向主张失败，继续形成以下之一，而不是把分支 No-Go 当成总目标完成：

1. `NEGATIVE_COMPARATIVE_PINN_MANUSCRIPT`；
2. `CLEANROOM_BENCHMARK_AND_METHOD_LIMITS_MANUSCRIPT`；
3. `SYNTHETIC_DEVICE_PINN_BENCHMARK_MANUSCRIPT`。

只有同时交付完整论文正文、实际结果、最终图表和主表、参考文献、补充材料、复现说明/包、claim–evidence mapping 与 reviewer-risk/主张边界自检，才可记 `GOAL_COMPLETE`。来源报告、代码、oracle、pilot、负 dossier、skeleton 或带结果占位符的稿件均不是完成。

## 2. 当前起点与保留边界

- S1 已关闭两个来源路线并按冻结切换表锁定 `SYN_EDT_2D_V1`。
- S2 生效 freeze、Q0 与首个受驱动 QN intent 已由 [S2 终局收口](../docs/experiment/2026-08-26-goal-paper-one-shot-v1-s2-terminal-closeout.md)固定：Q0 只通过零驱动守卫；QN 按冻结 Newton 迭代上限失败且已计账，没有 rescue 或生产重跑。
- 本轮有界裁决为 `SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO`。跨分辨率 oracle、双周期 event 与 thermal-effect gate 未建立；strong raw、PINN/CTH development、GPU 与 formal 均未到达且不得用“失败”替代“未评价”。
- 自动稿件终点 `CLEANROOM_BENCHMARK_AND_METHOD_LIMITS_MANUSCRIPT` 已完成第 10 节全部真实交付，现记 `GOAL_COMPLETE`。
- CTH 正向架构新颖性未清除，只保留为透明诊断/比较臂；不得承担正向新架构主张。
- HFO-NP-v1 保持 `WAVEFORM_TIME_NO_GO_FROZEN`。
- 2025 TaOₓ C1 的 `0.32/0.16 nm` 来源—模型冲突不修补。
- Package A 三候选的 `PORTFOLIO_NO_GO_PACKAGE_A_FROZEN_3_FAMILIES_11_CARRIERS` 保持原证据边界。
- 本 GOAL supersede `PLAN-MSA-01` 的当前规划/授权语义，但不追溯改写 ADR、来源报告、实验记录或归档。

## 3. 一次性授权与永久禁止项

在本 GOAL 执行期间，第 7 节总预算和阶段门内曾授权：有界一手来源研究、许可与 provenance 审查、合法本地 COMSOL 模型审计、项目隔离依赖、本地代码/配置、clean-room 对象、CPU solver/oracle、本地 GPU PINN development、sealed formal、统计、图表、本地论文与补充材料。该一次性授权现已随完整本地交付消费并关闭；本段保留历史授权范围，不授权新执行。

始终未授权：付费计算或服务、购买许可、披露凭据、联系作者、投稿、外部上传/发布、Git push/PR/merge/remote release、破坏性机器级改动。原始商业 `.mph` 不进入公开复现包；依赖只允许写入项目目录或项目虚拟环境。

## 4. 预注册路线树

路线顺序必须在任何新数值求解或 PINN 结果出现前完成 S0 冻结。

### Route 1 — COMSOL64-first

- candidate：`KNOWN_UNREVIEWED_S9_REFRESHED_TO_COMSOL_6_4`；
- application：`COMSOL_APPLICATION_ID_141181`；
- 身份上限：`COMSOL_6_4_TUTORIAL_SPECIFICATION_ALIGNED_CLEANROOM_DERIVED`；
- 只允许 tutorial-specification-aligned clean-room derived 表述，不声称实验验证或作者原生重放。

### Route 2 — source-only fallback

S0 在任何新来源审计前按方法盲规则冻结一个 fallback bundle。只有 Route 1 出现 `LEGAL_RESEARCH_ACCESS_FAILURE`、`MPH_ACCESS_FAILURE`、`SOURCE_CONTRACT_FAILURE` 或 `UNRESOLVED_VERSION_CONFLICT` 时启用。Route 1 一旦通过来源合同，Route 2 永久退出，不得因 event/raw/CTH/formal 表现换对象。

### Route 3 — SYN_EDT_2D_V1

若两个来源候选均无法形成合格对象，或来源对象在 oracle/event 门失败，自动进入预冻结 `SYN_EDT_2D_V1`。身份固定为 `FULLY_TRANSPARENT_SYNTHETIC / TWO_DIMENSIONAL_AXISYMMETRIC / ELECTROTHERMAL_DEFECT_TRANSPORT_BENCHMARK / NOT_SOURCE_ALIGNED / NOT_EXPERIMENTALLY_VALIDATED`。

Route 3 必须含电流连续、准稳态 Joule 热、动态守恒 Nernst–Planck 缺陷输运、温度对 transport 和/或 conductivity 的反馈、明确二维器件几何、完整 IC/BC/interface、绝对时间双极协议、可重复局部耗尽—恢复事件、传统 solver oracle、case generator 与 evaluator。参数、分支和协议必须在第一次求解前冻结，不得按 CTH 表现调对象。

## 5. 自动阶段链

### S0 — 合同冻结（已完成）

写入并冻结：COMSOL64 来源合同；方法盲 fallback ID/来源链/排序理由；`SYN_EDT_2D_V1` 完整物理合同；`A/A_PRIME/ENGINEERING/UNKNOWN` 账本；三种稿件终点与切换规则；互斥案例池、统计单位与预算；CTH 和全部控制的实现合同。S0 通过后自动进入 S1。

S0 机器合同与完整冻结理由见 [`s0_contract.json`](../configs/goal_paper_one_shot_v1/s0_contract.json) 和 [S0 预注册记录](../docs/governance/2026-08-26-goal-paper-one-shot-v1-s0-preregistration.md)。

### S1 — 来源、合法性与新颖性前审（已完成）

分别裁决 `COMSOL64_RESEARCH_USE_RIGHT`、`COMSOL64_MODEL_FILE_ACCESS`、`COMSOL64_RESULT_PUBLICATION_RIGHT`、`COMSOL64_MPH_REDISTRIBUTION_RIGHT` 与 `INDEPENDENT_CLEANROOM_CODE_LICENSE`；至少前三项 PASS 才可锁定 Route 1。

来源合同须闭合 domain 5 初态、全部 domain selections、EC/HT/TCC/Joule Heating、IC/BC/interface、no-flux/轴对称/绝缘/内部连续、transport/电导/热本构、表格插值/外推/单位换算、TCC formulation/stabilization、端口方向/轴对称积分、精确 COMSOL build/资产身份/模型树与机器可读 reference outputs。

CTH 新颖性前审至少覆盖 Conditional PINN、HyperPINN、P²INNs、SA/residual sensitivity、cusp-capturing PINN、Spline-PINN、PI-BSNet 与 learned/separated parameter basis；只能陈述声明范围内的检索结果。

实际裁决见 [S1 有界前审报告](../docs/references/2026-08-26-goal-paper-one-shot-v1-s1-source-legal-novelty-review.md)：本轮审阅 13 个一手载体、其中 10 个首次进入项目，使用新增预算 `10/12`。Route 1 所需权利 PASS 未建立且来源合同不完整，按预注册代码记 `LEGAL_RESEARCH_ACCESS_FAILURE + SOURCE_CONTRACT_FAILURE`；Route 2 为 `SOURCE_CONTRACT_FAILURE`，因此激活 `SYN_EDT_2D_V1`。CTH 为 `POSITIVE_ARCHITECTURE_NOVELTY_NOT_CLEARED`，只保留诊断/比较身份。

### S2–S3 — micro/full oracle、事件与案例池（已按数值合同 No-Go 终止）

依次执行 zero-drive、coarse/medium、守恒/范围/no-flux、anchor case、signed local event bracket、`DIRECT_T_TO_TRANSPORT_OFF`、`FULL_ISOTHERMAL_COUPLING_OFF` 及端口—空间联合检查；随后完成独立空间/时间收敛、current/heat/mass/no-flux/范围/端口守卫、来源联合不确定性对齐或 synthetic contract verification、同一 ROI 两个连续周期的局部部分覆盖耗尽—恢复事件、thermal effect 超越各分支数值不确定性、完整 evaluator 与误差地板。

案例池在 PINN 前互斥冻结为 `Q / D / I / F_A / F_O / R`。完整统计单位为 `GEOMETRY × CONSTITUTIVE_OR_MATERIAL_BRANCH × INITIAL_STATE × FULL_WAVEFORM × FULL_HISTORY`；mesh、time step 与 seed 不是独立 case。

实际执行只到 Q0 与首个 QN intent。Q0 为 bounded zero-drive guard；QN 在生成可评价场之前执行失败，故本节其余资格化 intent、案例池开放和误差地板均未到达。冻结合同全文保留为“原计划做什么”，不得写成“已经完成什么”。

### S4 — strong raw 与方法路由（未到达）

先资格化 parameter-conditioned mixed first-order PINN；损失必须显式包含守恒 PDE 与本构残差。裁决为 `RAW_INCOMPETENT`、`RAW_COMPETENT_NO_ACTIONABLE_BOTTLENECK`、`RAW_COMPETENT_TRANSPORT_PARAMETER_BOTTLENECK` 或 `RAW_COMPETENT_OTHER_BOTTLENECK`。

只有 raw 胜任、存在有限预算 headroom、transport-only bottleneck、一侧有限尺度响应超越 oracle 不确定性并经 event-time-shift 控制、组合新颖性与轻量分析均通过时才训练 CTH。否则保留对象并自动转 benchmark/comparative 路线，不伪造 CTH 准入。

### S5 — CTH 轻量分析与 development（未到达）

若准入，协议轴固定为 `FIXED_DURATION_RESET_WAVEFORM_SCALE_AXIS`，`lambda_R=1` 仅为 nominal anchor，不称纯幅值、纯速率或物理 knot。CTH 只称 `CONDITIONAL_APPLICATION_SPECIFIC_TRANSPORT_ARCHITECTURE_ADAPTATION`，不得称通用新 PINN 原语。

Stage 1 比较 strong parameter-conditional raw、direct residual Taylor2、训练节点 exact smooth P4 与 transport-only CTH，并报告 CTH/P4/Taylor2/spline basis 的 rank、singular values、condition number、basis norm 与 off-grid leverage。CTH 未同时优于三者即转 exact-control negative comparative 稿。

Stage 2 仅在 Stage 1 PASS 后运行：SA/direct Jacobian first order、smooth6、PI-BSNet-like spline、rank-matched learned basis、all-field/generic latent hinge、parameter-matched wider raw、compute-matched extra-work raw、mirrored wrong knots、independent-per-view raw。失败后不补 seed、不移动 knot、不增加第二 hinge，不隐藏结果。

### S6 — sealed formal 或负向确认（未到达）

formal 固定三臂：primary method、strong raw、开封前冻结的最强非 primary challenger。每个完整 configuration 独立训练，不跨 configuration warm-start；case 是独立统计单位，seed 仅为嵌套重复。

正向主张要求 `F_A` 同时相对 raw 与 challenger 达到预声明 superiority，`F_O` 同时相对二者达到 noninferiority，且全部物理守卫通过、计算—误差平面不被严格支配。失败时保留 sealed 结果并转负向稿；不得重封、补 seed、换 case、改 margin、筛失败 intent 或改 primary endpoint。授权预算内 power 不足时记 `FORMAL_POWER_BUDGET_INSUFFICIENT`，收缩为明确证据等级的 benchmark 稿，不把 pilot 冒充 formal。

## 6. 自动切换表

| 失败位置 | 自动动作 |
| --- | --- |
| COMSOL legal/source FAIL | 启用预冻结 source-only fallback |
| source fallback FAIL | 启用 `SYN_EDT_2D_V1` |
| 来源对象 oracle/event FAIL | 关闭来源分支，启用预冻结 synthetic route |
| CTH novelty/admission FAIL | 保留对象，转 diagnostic/comparative benchmark |
| CTH Stage 1 FAIL | exact-control negative comparative manuscript |
| CTH Stage 2 attribution FAIL | basis/placement/capacity failure manuscript |
| formal superiority FAIL | sealed negative method manuscript |
| orthogonal noninferiority FAIL | applicability/limits manuscript |
| formal power 不足 | 明确证据等级的 benchmark manuscript |
| GPU 不可用 | CPU 可行范围继续，否则收缩 benchmark manuscript |
| 总预算耗尽 | 停止新增运行，用全部真实证据完成稿件 |

任何单分支失败只关闭对应科学主张，不完成总 GOAL。

## 7. 冻结总预算

| 资源 | 总上限 |
| --- | ---: |
| 新增一手来源载体 | 12 |
| 深审 source candidates | COMSOL64 + 1 fallback |
| 来源阶段 | 5 日 |
| CPU solver intents | 40 |
| CPU core-hours | 256 |
| development GPU | 96 exclusive GPU-hours |
| formal GPU reserve | 128 exclusive GPU-hours |
| GPU 总上限 | 224 exclusive GPU-hours |
| 单方法正式 superseding rerun | 最多 1 次，且须有相关输入/实现/合同变化 |
| paid compute | 0 |
| Git/external publication | 0 |

未用 development 预算可在 Route 1–3 development 间转移；formal reserve 不得借给 development。所有失败运行计入预算。

## 8. 学术边界与自主规则

禁止 fabrication、hidden source stitching、seed cherry-picking、formal peeking、post-hoc margin、压制负控、实验验证/作者原生重放/真实物理 kink/通用新 PINN 原语/世界首创/普适性/SOTA/接收保证等无证据主张。

Agent 对普通实现、超参数、门后切换和阴性结果自主处理；每道门通过即继续，每个分支失败即按表切换，不因工期降低门或救援。只有需要用户专属凭据/许可动作、机器安全边界、工作区外破坏性动作、付费支出或法律伦理冲突时暂停。

## 9. 不得省略的冻结定义与计算合同

### 9.1 signed local event

对周期 (k) 的局部耗尽定义为

\[
d_k(x,t)=
\frac{c_{\mathrm{pre},k}(x)-c(x,t)}{c_{\mathrm{scale}}}.
\]

事件资格必须同时检查 localization、partial coverage、depletion/gap thickness、recovery、cycle drift、mass 与 port response；不得用端口单曲线、一次阈值穿越或整域翻转替代同一 ROI 中两个连续周期的局部耗尽—恢复事件。

### 9.2 CTH、exact smooth P4 与训练节点

若且仅若 S4 准入，固定

\[
\delta=\frac{\lambda_R-1}{\epsilon},
\qquad
q_{\mathrm{tr}}
=q_0+\delta q_1+\delta^2q_2+|\delta|h,
\qquad
(c_v,\mathbf J_v)=B(q_{\mathrm{tr}}).
\]

训练视图固定为

\[
\delta\in\{-1,-1/2,0,1/2,1\}.
\]

exact smooth kill control 固定为

\[
P_4(\delta)=\frac{7}{3}\delta^2-\frac{4}{3}\delta^4,
\qquad
q_{\mathrm{P4}}
=q_0+\delta q_1+\delta^2q_2+P_4(\delta)h.
\]

在上述五个训练节点上 (P_4(\delta)=|\delta|)。因此任何 CTH 正向身份必须依靠 sealed off-grid complete cases、轻量 basis 分析和完整强控制，而不能靠 centered training grid 上的拟合差异。

Stage 1 四臂严格为：

1. `STRONG_PARAMETER_CONDITIONAL_RAW`；
2. `DIRECT_RESIDUAL_TAYLOR2`；
3. `EXACT_SMOOTH_P4`；
4. `CTH_TRANSPORT_ONLY`。

Stage 2 严格为：`SA_DIRECT_JACOBIAN_FIRST_ORDER`、`SMOOTH6`、`PI_BSNET_LIKE_SPLINE`、`RANK_MATCHED_LEARNED_PARAMETER_BASIS`、`ALL_FIELD_OR_GENERIC_LATENT_HINGE`、`PARAMETER_MATCHED_WIDER_RAW`、`COMPUTE_MATCHED_EXTRA_WORK_RAW`、`MIRRORED_WRONG_KNOTS` 与 `INDEPENDENT_PER_VIEW_RAW`。

### 9.3 formal 统计单位与冻结量

对方法 (m)、完整 case (i)、seed (s)，两周期等权端点为

\[
Z_{m,i,s}=\frac{1}{2}\sum_{k=1}^{2}
\frac{E_{m,i,k,s}}{\tau_{\mathrm{comp},i,k}},
\qquad
\widetilde Z_{m,i}=\operatorname{median}_{s} Z_{m,i,s}.
\]

相对控制 (c) 的 paired improvement 为

\[
D_{i,c}=\widetilde Z_{c,i}-\widetilde Z_{\mathrm{primary},i}.
\]

formal 开封前冻结 primary endpoint、最小有意义效应、noninferiority margin、case/seed 数、区间方法、多重性/gatekeeping、timeout/divergence/replay 与 intent-to-run 规则、硬件吞吐和总预算。完整 case 是独立统计单位；seed 先在 case 内聚合。

### 9.4 完整计算与失败记账

每个方法和失败 intent 必须记录：参数量、forward 次数、自动微分工作、optimizer closure/更新、wall-clock、峰值内存/显存、实际硬件、gross compute、失败身份与是否允许唯一 superseding rerun。只有相关输入、实现或合同发生变化时，单方法最多允许一次正式 superseding rerun；不得把失败计算从公平比较中删除。

## 10. 完整稿件与复现交付清单

论文正文必须包含：题目、摘要、引言、相关工作、对象与来源身份、governing equations 与物理合同、PINN 与候选方法、oracle/案例划分/统计、结果、消融与计算公平、formal 或明确证据等级的负向确认、讨论、局限性和结论。

最终图表至少包括：

1. 来源、对象、许可与 clean-room 身份；
2. solver 收敛和来源或 synthetic 合同验证；
3. signed event 与两个 thermal controls；
4. strong raw competence 与瓶颈；
5. primary method、exact controls 与轻量分析；
6. 全控制漏斗与 compute Pareto；
7. sealed formal 或负向适用边界；
8. 一张主结果表。

补充与复现必须包含：全部配置和 case manifest、参数/来源账本、seed/失败 intent/gross compute、统计合同、额外场图与消融、代码和数据目录说明、复现步骤、claim–evidence mapping 与 reviewer-risk self-audit。

~~~text
NOT_COMPLETE =
    source report only
    OR code only
    OR oracle only
    OR pilot only
    OR negative dossier only
    OR manuscript skeleton
    OR manuscript with placeholder results

COMPLETE =
    FULL_MANUSCRIPT
    + ACTUAL_RESULTS
    + FINAL_FIGURES_AND_TABLES
    + REFERENCES
    + SUPPLEMENT
    + REPRODUCIBILITY_PACKAGE
    + CLAIM_BOUNDARY_AUDIT
~~~

## 11. GOAL 完成记录

- `FULL_MANUSCRIPT`：[完整英文初稿](../paper/paper_v1/manuscript.md)，包含方法、实际负向结果、证据等级、讨论、局限性与结论，无结果占位符；作者署名、机构、基金、利益冲突和致谢仍由作者在投稿前补齐。
- `ACTUAL_RESULTS`：[S2 终局收口](../docs/experiment/2026-08-26-goal-paper-one-shot-v1-s2-terminal-closeout.md)与正文只报告 Q0 零驱动守卫、首个受驱动 QN 执行失败及 `NOT_REACHED` 下游门。
- `FINAL_FIGURES_AND_TABLES`：[六幅最终图及图源](../paper/paper_v1/figures/)同时提供 PNG/PDF，主表见 [tables.md](../paper/paper_v1/tables.md)。
- `REFERENCES`：[references.bib](../paper/paper_v1/references.bib)固定 13 个已审载体的完整身份。
- `SUPPLEMENT`：[supplement.md](../paper/paper_v1/supplement.md)固定合同、资格梯、失败计账与额外边界。
- `REPRODUCIBILITY_PACKAGE`：[reproducibility.md](../paper/paper_v1/reproducibility.md)与[包索引](../paper/paper_v1/README.md)覆盖证据哈希、ledger、50 项 focused tests、Q0-only 复算、非科学诊断和图表重绘。
- `CLAIM_BOUNDARY_AUDIT`：[claim_evidence_matrix.md](../paper/paper_v1/claim_evidence_matrix.md)逐项给出载体、证据身份、禁止外推和 reviewer-risk 自检。
- [package-manifest.json](../paper/paper_v1/package-manifest.json)覆盖除自身外 34 个交付文件；其信息性 SHA256 为 `1B00038B54049B4738AB6998BF4FE4C508B1F4200BA692889066D259AFE9F7A6`。2026-08-27 的后续编辑只重构论文叙事并新增中文/通俗派生稿，不改变本 GOAL 的冻结科学结果或 claim ceiling。

最终科学边界保持 `SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO_NO_ORACLE_EVENT_OR_METHOD_EVIDENCE`。`GOAL_COMPLETE` 只表示本地制品与预注册 fallback 已完整交付，不表示 oracle、event、PINN、GPU、OOD、formal、实验验证、期刊接收或 SOTA 成立。
