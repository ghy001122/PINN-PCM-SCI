# 项目状态

更新时间：2026-08-26

- `phase_id`: `GOAL_PAPER_ONE_SHOT_V1_COMPLETE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO_NO_ORACLE_EVENT_OR_METHOD_EVIDENCE`
- `authorization_scope`: `ONE_SHOT_LOCAL_RESEARCH_EXECUTION_CONSUMED_AND_CLOSED`
- `authorization_package`: `S0_TO_S6_AND_LOCAL_MANUSCRIPT_CONSUMED`
- `plan_status`: `COMPLETED`
- `candidate_status`: `SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO_FROZEN`
- `idea_research_status`: `GOAL_PAPER_ONE_SHOT_V1_COMPLETE`
- `object_selection_status`: `SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO_FROZEN`
- `method_selection_status`: `NOT_REACHED_CTH_DIAGNOSTIC_ONLY_NO_TRAINING`
- `source_scan_status`: `S1_COMPLETE_ROUTE_1_NOT_ADMITTED_ROUTE_2_SOURCE_CONTRACT_FAIL_SYNTHETIC_ACTIVATED`
- `fresh_primary_source_budget`: `12_NEW_PRIMARY_CARRIERS_TOTAL`
- `deep_review_object_family_budget`: `COMSOL64_PLUS_ONE_FALLBACK`
- `screen_timebox`: `FIVE_DAYS_AFTER_S0_FREEZE`
- `last_completed_science_terminal`: `SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO`
- `prior_package_a_status`: `CONSUMED_AND_CLOSED`
- `compute_authorization`: `CLOSED_GOAL_COMPLETE_READ_ONLY_REPRO_AUDIT_ONLY`
- `implementation_authorization`: `CLOSED_GOAL_COMPLETE_MAINTENANCE_ONLY`
- `formal_or_gpu_authorization`: `NOT_REACHED_CLOSED_BY_S2_GATE`
- `next_research_execution_authorized`: `false`
- `next_authorizable_package`: `NONE_GOAL_COMPLETE_NEW_USER_AUTHORIZATION_REQUIRED`
- `prior_hfo_route_status`: `WAVEFORM_TIME_NO_GO_FROZEN`
- `novelty_status`: `CTH_POSITIVE_ARCHITECTURE_NOVELTY_NOT_CLEARED_BOUNDED_REVIEW`

## 当前已核验事实

- `VERIFIED_GOAL_PAPER_ONE_SHOT_V1_LOCAL_DELIVERABLES_COMPLETE`：[最终本地论文包](paper/README.md)已经交付完整正文、实际结果、六幅最终图的 PNG/PDF、主表、13 项参考文献、补充材料、复现说明、claim–evidence mapping 与 reviewer-risk 自检。[包清单](paper/package-manifest.json)覆盖除自身外 32 个文件，其信息性 SHA256 为 `1EA96E3B9019F3D7F5419805E0C4E7CBE999F5E270B2340C54CD695ED26AA36A`。一次性执行授权因此消费并关闭；该交付事实不建立 oracle、event、PINN、GPU、OOD、formal 或实验主张。
- `VERIFIED_SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO`：[S2 终局收口](docs/experiment/2026-08-26-goal-paper-one-shot-v1-s2-terminal-closeout.md)固定 `SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO`。生效 freeze `20260826T113537Z-goal-paper-one-shot-v1-s2-freeze-002` 绑定 S0 SHA256 `947E737A255D27A7BB2553286809ADB98219FD4E48B932B170CB06608A2E3A75`、S2 SHA256 `D059AA2261CC227C3B16B7965A75C461AD64110C2A20C3700B62E54FDE25E8E6` 与 Q-only case-manifest SHA256 `EF093A5C2F2E798FF05E768C3D0837CF08C3E10FD6AE79B432F26585F0FCD09C`，并显式 supersede `freeze-001`。
- `VERIFIED_SYN_EDT_Q0_ZERO_DRIVE_GUARD_ONLY`：intent `20260826T113638Z-goal-paper-one-shot-v1-s2-intent-01-q0` 完成 400 个时间步；质量漂移、无通量残差、热平衡残差和端口电流不匹配均为 `0.0`，`y_min=y_max=0.5`，全部 hard guards 通过。其 manifest 保持 `PENDING_S2_CROSS_RUN_ADJUDICATION / NO_ORACLE_EVENT_OR_METHOD_CLAIM_SINGLE_CASE_ONLY`；这是零驱动实现与产物链守卫，不是 oracle 或 event evidence。
- `VERIFIED_SYN_EDT_QN_EXECUTION_FAILURE_CONSUMED`：首个受驱动 QN intent `20260826T113752Z-goal-paper-one-shot-v1-s2-intent-02-qn-coarse-fine` 在 `0.0984956999309361 s` 后抛出 `transport Newton exceeded its frozen iteration limit`。失败 manifest 记录 `failed_intent_consumed=true`、`rescue_attempts=0`；Q0 与该失败共消费 2 个 solver intents 和 `0.002326388888888889 CPU_PROCESS_CORE_HOURS`，intent `3–13` 未启动。
- `VERIFIED_SYN_EDT_NUMERICAL_DIAGNOSIS_BOUNDARY`：显式 `NON_SCIENTIFIC_DIAGNOSTIC` 在最小 QN 首步 fixture 上确认 half-step Newton 近似每轮减半，冻结 inner `initial_step=0.5 / max_iterations=20 / tolerance=1e-10` 无法在预算内收敛；所测状态和方向未发现大的解析 Jacobian—有限差分 mismatch，但不排除未测试方向或状态的实现错误。latent outer `relaxation=0.5 / max_blocks=12 / relative_change=1e-8` 亦存在结构性预算风险，但 production intent 在 inner 阶段即终止，未观测 outer failure。诊断不是生产 oracle，也不证明改合同后会成功。
- `VERIFIED_SYN_EDT_DOWNSTREAM_NOT_REACHED`：S2 未建立跨分辨率 oracle、双周期 event 或 thermal-effect gate；因此 strong raw、PINN/CTH、development GPU 与 sealed formal 均为 `NOT_REACHED`，没有正面或负面方法证据。获批 fallback 的 `CLEANROOM_BENCHMARK_AND_METHOD_LIMITS_MANUSCRIPT` 已按该边界完成本地交付。
- `VERIFIED_GOAL_PAPER_ONE_SHOT_V1_AUTHORIZATION`：用户于 2026-08-26 明确批准并执行 `GOAL-PAPER-ONE-SHOT-V1`，一次性授权 S0–S6、有界来源与许可研究、合法本地 COMSOL 审计、项目内实现、CPU oracle、本地 GPU development、sealed formal、统计图表和本地完整稿件；不授权付费计算、凭据披露、作者联系、投稿、外部上传/发布或 Git 远程操作。授权事实已由 [ADR 0044](docs/adr/0044-adopt-goal-paper-one-shot-v1.md) 接受；授权本身不是科学证据，实际 S2 证据边界由上述终局收口定义。
- `VERIFIED_GOAL_PAPER_ONE_SHOT_V1_S0_FREEZE`：[S0 机器合同](configs/goal_paper_one_shot_v1/s0_contract.json)与[预注册记录](docs/governance/2026-08-26-goal-paper-one-shot-v1-s0-preregistration.md)已在任何新来源审计或数值求解前冻结路线顺序、synthetic 物理、案例池、方法/控制、预算、formal 统计、失败计账和稿件终点；文档一致性门通过。该项只证明执行合同固定，不构成来源 PASS、对象锁定或科学证据。
- `VERIFIED_GOAL_PAPER_ONE_SHOT_V1_S2_NUMERICAL_FREEZE`：[S2 数值机器合同](configs/goal_paper_one_shot_v1/s2_numerical_contract.json)与[预注册记录](docs/governance/2026-08-26-goal-paper-one-shot-v1-s2-numerical-preregistration.md)已在首个 `SYN_EDT_2D_V1` 数值结果前冻结轴对称有限体积、logit backward-Euler 守恒输运、非线性容差、六端点/normalizer/oracle-floor 公式、thermal-control 语义和含 independent exact replay 的 13-intent 资格化顺序。该项是工程预注册，不证明 solver 收敛、事件成立或任何方法有效。
- `VERIFIED_GOAL_PAPER_ONE_SHOT_V1_S1_ROUTE_VERDICT`：[S1 来源、合法性与新颖性前审](docs/references/2026-08-26-goal-paper-one-shot-v1-s1-source-legal-novelty-review.md)实际审阅 13 个一手载体，其中 10 个首次进入项目、使用冻结新增预算 `10/12`，并完成 `2/2` 深审对象。COMSOL Route 1 因可用证据未建立所需研究使用/结果发表 PASS 且完整可独立复现合同未闭合，按预注册代码裁决 `LEGAL_RESEARCH_ACCESS_FAILURE + SOURCE_CONTRACT_FAILURE`；该代码不证明用户或机构没有许可证。PCMO Route 2 因原文为均匀 point-device MATLAB ODE、依赖未公开 Sentaurus LUT 且无二维守恒场合同，裁决 `SOURCE_CONTRACT_FAILURE`。按冻结切换表锁定 `SYN_EDT_2D_V1`；该对象是完全透明合成 benchmark，不是来源对齐或实验验证对象。
- `VERIFIED_COMSOL_TEMP_ASSET_AUDIT_BOUNDARY`：公开 Gallery 6.4 `.mph` 仅在系统临时目录作只读 manifest/entry 审计，闭合长度 `59,463,566` bytes、SHA256 `14A1A8356B6FDA3C2B2CCBC2F4458C0F610CD47C4EE924602D4DBD49C8983FA3`、build `6.4.0.257` 与 solved payload 存在性；未启动 COMSOL、未读取 solution 数组、未把商业原始资产写入仓库或复现包，审计后临时文件已删除。该事实不赋予许可、不形成 oracle，也不证明作者模型重放。
- `VERIFIED_CTH_BOUNDED_NOVELTY_ADMISSION_FAIL`：S1 有界先验集未发现 `q0 + δq1 + δ²q2 + |δ|h` transport-only 完整 bundle 的 exact collision，但 conditional/parameterized PINN、parameter encoder/hypernetwork、absolute-value cusp、spline 和 learned/fixed parameter basis 均有直接先例。故 `POSITIVE_ARCHITECTURE_NOVELTY_NOT_CLEARED`，CTH 不得承担正向新架构主张，只可在后续真实数值证据允许时作为透明诊断/比较臂。
- `VERIFIED_WORKSPACE_DOCUMENT_ALIGNMENT`：[2026-08-26 工作区文档状态对齐](docs/governance/2026-08-26-workspace-document-state-alignment.md)完成当前权威面逐项语义审查与全库文档机器巡检。它修正已结束 Package A 仍被写成“当前筛选”的状态漂移，归档完成版旧 live plan，修复归档相对链接，并确认历史 snapshot 保持非权威身份。本项只证明文档治理状态，不构成科学证据或科研执行授权。
- `VERIFIED_PLAN_MSA_01_SUPERSEDED_HISTORY`：先前唯一 live plan `PLAN-MSA-01` 曾提出“主锚点来源 + 最多两个兼容模块来源 + 最多一个二值非拓扑分支”的模块化 source-aligned clean-room 对象合同，状态为 `DRAFT_FOR_EXPLICIT_APPROVAL_NOT_AUTHORIZED`；其原文现已[归档](archive/2026-08-26-plan-msa-01-review-superseded.md)。[ADR 0044](docs/adr/0044-adopt-goal-paper-one-shot-v1.md)随后覆盖其逐包批准与无自动 fallback 语义，但保留可移植科学门和全部历史证据。
- `VERIFIED_PACKAGE_A_PORTFOLIO_NO_GO`：[方法盲对象筛选报告](docs/references/2026-08-26-method-blind-cleanroom-object-screen.md)在 2026-08-26T01:02:21+08:00 冻结 Sandia/Charon 3D TaOₓ、2026 HfO₂/Al₂O₃ baffle 与 2022 RRAM array crosstalk 三个家族，并按顺序完成八门审查。三者最早决定性失败均为 Gate 3 合同完整性；11/12 项新增一手载体、3/3 家族后，严格按 ADR 0041 的组合量词记 `PORTFOLIO_NO_GO_PACKAGE_A_FROZEN_3_FAMILIES_11_CARRIERS`。该结论只覆盖冻结组合；见 [ADR 0042](docs/adr/0042-close-package-a-with-method-blind-object-portfolio-no-go.md)。
- `VERIFIED_PACKAGE_A_AUTHORIZATION_CONSUMED`：用户于 2026-08-26 明确批准最终 GOAL 的授权包 A；该授权现已按预声明终点消费并关闭。全程为 `0 object build / 0 solve / 0 smoke / 0 training / 0 PINN / 0 GPU / 0 formal / 0 paid compute / 0 Git publication`；`object_selection_status=NO_OBJECT_SELECTED`，CTH、strong raw、novelty 与全部方法门均为 `NOT_REACHED`。见 [ADR 0041](docs/adr/0041-adopt-one-object-one-bottleneck-goal-and-authorize-package-a.md)。
- `ACCEPTED_ONE_OBJECT_GOAL`：当前采用 `ONE OBJECT → ONE BOTTLENECK → ONE PAPER`。对象按来源身份、二维物理闭环、响应锚点/事件可资格化概率、clean-room 重建、完整案例能力和预计 CPU 成本方法盲排序；`CANDIDATE_NO_GO` 只关闭候选，`PORTFOLIO_NO_GO` 才关闭组合，首个 PASS 后锁定唯一对象且不得为方法结果换对象。作者 raw 全场解与作者预封案例角色不是 clean-room 来源硬门；因果参数冲突仍不得猜测修补。
- `VERIFIED_NEW_OBJECT_SCREEN_TERMINAL`：[新对象 source-complete 审查](docs/references/2026-08-25-new-object-source-complete-review.md)在新增 3 项一手载体、深审 1 个家族后以 `NEW_OBJECT_SOURCE_COMPLETE_BOUNDED_NO_GO` 收口。2025 Pd/Ta₂O₅/TaOₓ/Pd 论文使用 vacancy hopping distance `a=0.32 nm`，固定作者模型使用 `a=0.16 nm`，且该量直接进入扩散与漂移速度；无同源勘误或换算，因此对象选择为 `NO_OBJECT_SELECTED`，方法阶段 `NOT_REACHED`。固定模型 `SolutionNative totalSize=0`、没有 raw 全场解，以及六个文件名只有五个唯一 `K1/K2` 变体，是独立次级失败。见 [ADR 0040](docs/adr/0040-select-new-source-complete-object.md)。
- `VERIFIED_NEW_OBJECT_AUTHORIZATION_CONSUMED`：用户于 2026-08-25 明确选择“来源完整新对象优先、由实际 bottleneck 决定唯一 PINN 方法”的修订 GOAL，并授权最多新增 20 项一手来源、深审最多 4 个对象家族的阶段 1A。该授权已在第 1 个家族出现决定性硬失败后按停止条件消耗并终止；全程保持 `0 solve / 0 object build / 0 training / 0 PINN / 0 GPU`。
- `VERIFIED_HFO_G0_WAVEFORM_TIME_NO_GO`：[G0 来源与对象合同审查](docs/references/2026-08-25-hfo-g0-source-and-object-contract-review.md)使用 2 项一手记录确认：正文/图注的 `0.1 V/s` 与 Fig. 1b 约 `0–3.3 s` 的三角波时间轴相差约十倍，且无 erratum、机器可读波形或公开输入 deck 可唯一冻结 physical time。裁决为 `WAVEFORM_TIME_NO_GO`；G1 `NOT_AUTHORIZED_AND_NOT_ELIGIBLE`，执行保持 `0 solve / 0 object build / 0 training / 0 PINN / 0 GPU`。
- `VERIFIED_IDEASPARK_HISTORY`：IdeaSpark 的 ESD-PINN 与 susceptibility-scout/routing 两个候选分别以 `abandon` 收口；C17/fixed-slot SRPG 曾以 `CONDITIONAL_RETAIN / REVISE_BEFORE_IMPLEMENTATION / PROPOSED_NOT_AUTHORIZED` 保留。本轮没有改写该历史，也没有运行 solver、training 或 formal OOD。
- `VERIFIED_PRIMARY_SOURCE_REVIEW`：截至 2026-08-23 的一手审查覆盖 48 项论文记录与 26 个官方代码/数据/归档载体；未发现完整机制束 exact collision，但参数敏感 PINN、PDE 导数正则、stop-gradient 物理自目标、潜空间结构化和相场 causal/adaptive 训练均已出现，裁决仍为 `NO_EXACT_BUNDLE_COLLISION_FOUND_IN_BOUNDED_SEARCH / BROAD_CLAIM_COLLISION_CONFIRMED / NOT_NOVELTY_CLEARED`。
- `VERIFIED_OPEN_ORACLE_NO_GO`：10 个对象/框架家族、19 个一手载体中，没有单一来源原生对象同时闭合开放许可、固定实现、动态电—热—内部态、绝对时间和可重放完整局域器件事件，裁决 `OPEN_INDEPENDENT_ORACLE_NO_GO`。该结果不禁止 ADR 0026 下的透明 clean-room 派生对象。
- `VERIFIED_HFO_PLANNING_DECISION`：用户已通过 Q1–Q12 与 ADR 0030 选择 HFO-NP-v1 为唯一下一规划对象，接受守恒氧空位缺陷态、完整 history/state 和 side/temporal 证据路由；这只是治理事实，不证明来源合同或事件成立。
- `VERIFIED_ADVERSARIAL_DOCUMENT_INTEGRATION`：用户提供的 `E:\PINN-PCM\HFO-NP-v1、SRPG 与 KC′ 对抗性深度审查报告.md` 已作为内部调研输入整合到 [当前对抗性审查](docs/references/2026-08-24-hfo-np-v1-srpg-kc-adversarial-integration.md)。本轮只采纳可由既有一手账本或本地方程分析支持的结论；未回源内容统一保留为待 G0 核验。
- `VERIFIED_FUTURE_ROADMAP_INTEGRATION`：引用 ChatGPT 会话“深度论文审查”的后续路线已按实时权威链筛选并写入 [后 G1 PINN 研究路线整合](docs/notes/2026-08-24-hfo-post-g1-pinn-roadmap-integration.md)。吸收了“对象→事件→side→strong raw→唯一方法→pilot→formal”的顺序，拒绝了初态提前锁定、双轴首轮五视图、SRF 预定胜出、PHA 自动 fallback 与无证据预算阈值；该项是文档事实，不是科学证据或执行授权。
- `VERIFIED_Q30_Q36_PLANNING_INTEGRATION`：用户接受同一引用会话对 Q30–Q36 的对抗性修订，并以 [Q30–Q36 PINN 训练合同整合](docs/notes/2026-08-25-hfo-q30-q36-pinn-training-contract-integration.md)与 [ADR 0032](docs/adr/0032-defer-side-method-and-bound-hfo-pinn-training-comparators.md)记录。Q30 改为 side 方法延后选择，Q33 改为 attribution 无 curriculum；Q31、Q32、Q34–Q36 仅按守恒、物理时间、实际计算和分轨边界条件接受。该项是已接受规划事实，不是方法证据或执行授权。
- `VERIFIED_Q37_Q43_PLANNING_INTEGRATION`：用户继续接受同一引用会话对 Q37–Q43 的 `REVISE_WITH_CONDITIONAL_ACCEPTANCE`，并以 [Q37–Q43 strong-raw 合同整合](docs/notes/2026-08-25-hfo-q37-q43-strong-raw-contract-integration.md)与 [ADR 0033](docs/adr/0033-qualify-coupling-mode-and-freeze-strong-raw-adjudication.md)记录。未来不默认 monolithic joint training；backbone 允许 `BACKBONE_INDETERMINATE`，方法公平须含有效 wider-raw 与 extra-work raw，raw competence 使用预冻结 method-vote case×cycle 与 seed quorum，失败只按有证据的实现/共享缺陷允许一次 superseding rerun。该项只证明规划已接受，没有产生 SOURCE、EVENT、SIDE、RAW、TEMPORAL、PINN 或方法证据，也没有执行授权。
- `VERIFIED_Q44_Q48_PLANNING_INTEGRATION`：用户接受 grill-with-docs 对 Q44–Q48 的推荐，并以 [Q44–Q48 论文主张与新颖性边界整合](docs/notes/2026-08-25-hfo-q44-q48-paper-claim-and-novelty-boundary-integration.md)与 [ADR 0034](docs/adr/0034-freeze-single-method-headline-and-hfo-scoped-forward-claim.md)记录。未来首篇论文仅允许一个证据合格的 load-bearing PINN 机制进入 headline，formal 仅在来源有效 HFO 完整案例家族内逐案例训练，事件保真为主要裁决、计算成本为次要 Pareto 证据，范围保持 forward-only，并在 pilot 前与 formal/主张冻结前各刷新一次新颖性。该项是规划治理事实，不选择具体方法、不构成 novelty clearance，也不产生任何科研执行授权。
- `VERIFIED_Q49_Q53_PLANNING_INTEGRATION`：用户继续接受 grill-with-docs 对 Q49–Q53 的推荐，并以 [Q49–Q53 因果 pilot、formal 与碰撞合同整合](docs/notes/2026-08-25-hfo-q49-q53-causal-pilot-formal-and-collision-contract-integration.md)与 [ADR 0035](docs/adr/0035-freeze-causal-single-primitive-pilot-and-collision-veto.md)记录。未来方法必须闭合瓶颈→单一干预→直接探针/kill control→完整事件→守卫因果链；首轮只准一个新可训练机制，formal 只用一个机制对齐家族加一个正交稳健家族，direct-near 工作若覆盖 primitive、因果主张与可比完整事件证据即触发停止/收缩。该项不选择方法、不冻结 OOD 轴或数值门，也没有产生 SOURCE、EVENT、SIDE、RAW、TEMPORAL、PINN、novelty 或 formal 证据。
- `VERIFIED_TKF_CANON_CONDITIONAL_METHOD_SELECTION`：用户要求选择具体方法并交给引用会话“深度论文审查”复核。原自由 `q_s+|δ|k` 的 TKF-v0 因五视图光滑四次吸收反例被审查为 `DEFER_PENDING_DIAGNOSTIC_IDENTITY`，不得进入 FULL_PLAN；[ADR 0036](docs/adr/0036-select-canonical-tkf-as-diagnostic-gated-full-plan-target.md)据此只选择固定规范基 TKF-CANON-PINN 作为 future FULL_PLAN 条件式靶标。其信息身份为 `REDUNDANT_BUT_POTENTIALLY_USEFUL_CONDITIONING`，必须先以 held-out protocol microview 对 smooth-quartic control 通过身份门；当前仍为 `NOT_ADMITTED / NOT_AUTHORIZED / NOT_NOVELTY_CLEARED`。
- `VERIFIED_Q54_Q58_PLANNING_INTEGRATION`：用户接受引用会话对 Q54–Q58 的 `REVISE A` 调整，并以 [前置门修订整合](docs/notes/2026-08-25-hfo-q54-q58-pre-full-plan-adversarial-revision-integration.md)与 [ADR 0037](docs/adr/0037-require-waveform-fidelity-field-kink-identity-and-novelty-gates.md)记录。唯一轴改为待 G0 回源的 `SOURCE_ANCHORED_DERIVED_WAVEFORM_SCALE_AXIS`；FULL_PLAN 前须依次关闭来源模型保真、`FIELD_KINK_PLUS`、独立身份协议与新颖性充分性。该项是规划治理事实，不把引用会话中的波形、图像、许可或同期工作陈述升格为一手证据，也没有产生 SOURCE、EVENT、SIDE、FIELD_KINK、PINN、novelty 或执行阳性。
- `VERIFIED_Q59_Q63_PLANNING_INTEGRATION`：用户接受 grill-with-docs Q59–Q63，并以 [CTH/热因果/效用整合](docs/notes/2026-08-25-hfo-q59-q63-hinge-causality-admissibility-and-utility-integration.md)与 [ADR 0038](docs/adr/0038-reframe-tkf-as-cth-and-require-thermal-causality-admissibility-and-utility.md)记录。当前方法靶标改名 CTH-PINN，只允许有限容量/预算下的 hinge 归纳偏置主张；新增系数级 IC/BC 可容许性、一个 thermal-feedback-off 因果 intent、力学必要即停止和 independent-per-view strong-raw 效用 kill。该项只证明规划已接受，不证明热因果、有限尺度 hinge relevance、方法效用或新颖性成立。
- `VERIFIED_Q64_Q68_PLANNING_INTEGRATION`：用户接受 grill-with-docs Q64–Q68，并以 [身份/锚点/效用整合](docs/notes/2026-08-25-hfo-q64-q68-cth-identity-anchor-transform-and-pareto-integration.md)与 [ADR 0039](docs/adr/0039-separate-cth-identity-evidence-and-freeze-anchor-vector-transform-and-utility.md)记录。field-hinge qualification 与 blind identity-development 完整案例必须互斥；hinge knot 固定来源 `a0`；`h=(h_c,h_J)` 为一个联合向量原语；公共 `C1` 输出变换须通过 Jacobian-action guard；协议束效用采用 `IND-5`、blind bundle 与 `IND-7` 的双轴 Pareto。该项只证明规划已接受，不证明 CTH 身份、效用或新颖性成立。
- `VERIFIED_HFO_Q1_Q68_DECISION_INDEX`：[HFO Q1–Q68 决策总索引](docs/adr/research_decisions_HFO_Q1_Q68.md)已把当前 HFO 编号空间与历史 KC Q1–Q23、R1 Q1–Q24 分开，并路由到 ADR 0030–0039。Q13–Q29 没有可逐字恢复的单一原始问答表，索引只汇总已进入权威链的有效合同，不补造原问题。
- `VERIFIED_Q1_Q68_DOCUMENT_CLOSEOUT`：本轮按 `neat-freak` 六面审查同步了 `README / CONTEXT / active phase / project state / unique live plan / ADR与notes索引`，修正旧 12-intent、SRF 优先级和 qualification-case 身份证据复用等非阻塞漂移；本次未修改科研代码、运行时、项目规则、记忆或既有实验资产，也未清理工作区中的用户改动。文档一致性门通过后，本项只证明状态闭合，不构成科学证据或执行授权。
- `VERIFIED_NONBLOCKING_WARNING_CLOSEOUT`：Git sandbox 对用户级 ignore 的权限 warning 已通过仓库内部 `.git/info/codex-global-ignore` 精确镜像和 repo-local `core.excludesfile` 路由消除，未修改用户 ACL 或全局 Git 配置；`docs/experiment/INDEX.md` 已保留内容并统一为 LF，`ExperimentLedger` 现显式以 LF 写 human index，相关 16 项 `unittest` 通过。这是工程状态，不是科研证据。
- `VERIFIED_ANALYTICAL_REVISION`：原 `5×` 门只能排除数值地板，不能排除光滑二次曲率或驻点；归一化斜率指数也不能单独裁决。same-network detached target 不增加独立物理信息，固定 latent slots 受 basis/scale/output-head nullspace 影响。因此 fixed-slot SRPG 改为 `REVISE_MAJOR_NOT_ADMITTED`，side 门改为含 smooth-quadratic null 的复合 TKB。
- `UNVERIFIED_HFO_SOURCE_DETAILS`：连续 CF 与 finite-gap restart 的精确身份、完整三角波/绝对时间、侧向边界、全本构参数、力学分支、Supplement/data/deck 与许可仍为 `UNVERIFIED_PENDING_PRIMARY_SOURCE`。这些是 `HFO_SOURCE_CONTRACT_NOT_CLOSED` 的内容，不得跨材料补齐。
- `ACCEPTED_REVISED_METHOD_ROUTING`：[ADR 0031](docs/adr/0031-revise-hfo-source-side-gate-and-method-routing.md)部分覆盖 ADR 0030：G1 只冻结一个协议轴并只判 side；只要来源与局部事件合格，`SIDE+` 或 `SIDE−` 都可另立 strong-raw 诊断 PLAN，side 结果只决定 side 方法资格；SRF-PINN 仍只是 parking-lot 候选，cKC-NP 仅在 future strong-raw 得到 `TEMPORAL+` 后可审查，`SIDE−/TEMPORAL−` 后停止且无自动 fallback。
- `VERIFIED_HFO_G0_AUTHORIZATION_HISTORICAL`：用户曾批准 HFO 授权包 A / G0 的最多 8 项一手来源、零求解审查；该授权已由 `WAVEFORM_TIME_NO_GO` 消耗并终止，不延伸到当前新对象筛选或任何数值执行。

- `VERIFIED_R2_AUTHORIZATION`：用户于 2026-08-22 接受 R2 严格热耦合 FerroX + PINN 方法路线 `FULL_DESIGN`；按计划的授权分层，普通批准只打开授权包 A，即最多 12 项一手来源、零求解的 P0 来源与热机制准入。授权包 B–D、FerroX replay、oracle、training、formal、GPU、付费计算和 Git 发布均未授权；见 [ADR 0029](docs/adr/0029-authorize-r2-strict-thermal-ferrox-p0-source-gate.md)。
- `VERIFIED_R2_P0_ENTRY_STATE_HISTORICAL`：进入 P0 时，固定 FerroX 的 TDGL–Poisson–平衡载流子底座及公开参考入口只作为来源线索；旧提交许可、HZO 绝对时间、极化耗散热、温度反馈参数、热效应量级和 TKC 新颖性尚未闭合，因此当时状态为 `R2_STRICT_THERMAL_NOT_YET_ADMITTED`，没有先实现或求解。
- `VERIFIED_R2_P0_TERMINAL`：授权包 A 已在 0 solve、0 training intent 与 11 项一手来源内完成。FerroX `002bdd` 可解析为完整 commit/tree，但固定 tree 内无许可文件；AMReX `3dda62` 经官方仓库当前无法解析为完整 commit/tree。按最早硬门裁决 `R2_P0_SOURCE_IDENTITY_NO_GO`；见 [P0 报告](docs/references/2026-08-22-r2-ferrox-strict-thermal-p0-source-and-collision-review.md)。
- `VERIFIED_R2_DATA_IDENTITY_PARTIAL_PASS`：Zenodo DOI `10.5281/zenodo.7221895` 的 CC-BY-4.0、四个 tar 包、文件大小与 MD5 已冻结；该数据身份不能修复 exact-revision 代码许可和依赖身份。
- `UNKNOWN_R2_THERMAL_CLOSURE`：HZO 专属绝对动力学、`L(T)`/`Gamma(T)`、完整耗散/可逆热分解、目标 MFIM 热边界及热效应相对离散地板没有在同一链闭合；这些发现不覆盖最早的来源身份单一 verdict。

- `VERIFIED_SOURCE_SCAN`：有界 VO₂ 来源闭合扫描已完成；四个预声明查询族在预算内耗尽，六个深审对象全部触发至少一项硬否决，结果为 `BOUNDED_ZERO_CANDIDATE`；见 [扫描报告](docs/references/2026-08-22-vo2-source-complete-candidate-scan.md)。
- `VERIFIED_SOURCE_SCAN`：用户批准的相关氧化物扩展扫描已完成；四个冻结查询族和八个深审对象全部触发至少一项硬否决，结果为 `EXPANDED_OXIDE_ZERO_CANDIDATE`，`0/8 PASS`；见 [扩展扫描报告](docs/references/2026-08-22-related-oxide-source-complete-candidate-scan.md)。
- `VERIFIED_PRIOR_SCAN_SCOPE`：前述两次来源扫描本身只做一手来源审计，没有运行 solver、PINN、训练、数值 pilot、GPU 或付费计算，也没有产生活动同源对象；该事实不覆盖随后另行获批的 R1 派生路线。
- `VERIFIED_AUTHORIZATION`：用户于 2026-08-22 明确批准最新 PLAN 的授权包 A。该授权已按阶段门在 P2 消耗并终止；P3–P5 没有越过停止门，P6–P8、formal OOD、GPU、付费计算和 Git 发布始终未授权。
- `VERIFIED_R1_P1_SOURCE_REVIEW`：11 项定向一手来源完成物理合同与创新碰撞审查，裁决 `P1_PASS_WITH_SCOPE_REDUCTION`；IRAC 降为已有残差/界面自适应思路的透明适配，KC′只保留“η 场局部单调时钟＋完整链式回拉”的窄假设，不作首创或具名材料定量主张。见 [P1 审查报告](docs/references/2026-08-22-r1-electrothermal-kc-irac-source-and-collision-review.md)。
- `VERIFIED_R1_P2_IMPLEMENTATION`：新的 `R1PhysicalContract`、A×H 四因子单元、独立 SciPy CPU oracle、预冻结事件/收敛门、零驱动检查、canonical adapter 和外部裁决器已实现；新增 5 项单元测试通过，旧 TAPF/ETPF/EAF 对象未被修改或复活。
- `VERIFIED_R1_P2_ZERO_DRIVE`：目标 A1H1 medium 零驱动通过；最大温升与电流均为零，跨阈值相区占比为零，最大平衡违规为 `2.7155769284996245e-13`。
- `VERIFIED_R1_P2_BOUNDED_NEGATIVE`：run `20260822T142511Z-pilot-r1-p2-event-001` 在四个预冻结升序电压上 `0/4` 通过完整双周期事件门，数值场均有限且无 phase clipping；选择规则未产生参考电压，因此没有运行粗/细收敛或 P3 资格化。裁决 `R1_P2_NO_CREDIBLE_EVENT`；见 [P2 收口](docs/experiment/2026-08-22-r1-p2-terminal-closeout.md)。
- `ACCEPTED_DESIGN_DECISION`：用户随后明确纠正，允许继续更换材料、物理闭合与网络，并允许透明迁移、适配和捆绑方法模块；零候选只关闭冻结同源对象合同。跨来源系统必须标为派生/合成对象，正向模块或组合仍须由基线、消融和完整证据支持；见 [ADR 0026](docs/adr/0026-allow-transparent-derived-objects-and-bounded-method-recombination.md)。
- `VERIFIED_FAST_SCAN`：按 `research-module-recombination FAST_SCAN` 已从六个来源/资产模块形成六个有界组合；`R1` 派生事件 benchmark + KC′ + 界面感知空间模块为 provisional active，热耦合 FerroX 与可恢复电形成相场为两个 fallback。该结果是设计排序，不是科学证据或执行授权。
- `ACCEPTED_DESIGN_DECISION`：论文级可归因 PINN 增量优先于保住指定模块；R1 仅承担材料类别级 `derived/synthetic` benchmark 身份，KC′、空间模块或二者交互按证据路由。组合创新须先通过 prior-art 碰撞否决并由预声明机制与 2×2 消融支持；48 小时只承诺路线裁决，不承诺阳性或 formal 结果。
- `ACCEPTED_DESIGN_DECISION`：`R1_FULL_DESIGN_GRILL_2026-08-22` 已冻结 Q1–Q24：A×H 四因子物理块、四个互斥案例池、strong-raw 瓶颈准入、六臂方法归因、cycle-equal 相态/界面主端点、difference-in-differences 交互、实际计算公平、intent-to-run 失败计票和预先路由的稿件故事。见 [ADR 0028](docs/adr/0028-freeze-r1-factorial-six-arm-and-four-pool-design.md) 与 [完整决策记录](docs/adr/research_decisions_R1_FULL_DESIGN_GRILL_2026-08-22.md)。
- `ACCEPTED_DESIGN_DECISION_SCOPED_BY_ADR_0026`：ADR 0019 为旧 exact-KC 路线冻结“空间异步、局部、部分覆盖且可恢复”的事件语义及同源二维对象门；事件语义继续可复用，但同源对象不再是当前重组筛选的全局必要条件。见 [ADR 0019](docs/adr/0019-target-spatially-asynchronous-events-on-a-source-complete-object.md)。
- `ACCEPTED_DESIGN_DECISION`：用户已撤销后续研究的固定全局次数上限；不再维护路线槽位或以累计次数自动放弃 idea。每条新路线仍须独立冻结论文去向、预算、证据门和停止条件，达到该路线的预声明终点后收口；见 [ADR 0027](docs/adr/0027-remove-the-fixed-count-cap-on-future-research-routes.md)。
- `ACCEPTED_DESIGN_DECISION_SCOPED_BY_ADR_0026`：ADR 0021 的“KC 必选、第二模块串行”只保留为旧 exact-KC claim 合同；当前候选允许联合设计。任何模块若要成为论文主要正向贡献，仍须在新对象/接口下通过强基线和关键消融；未通过者只能降为透明 supporting module，不能捆绑成主要方法创新。
- `ACCEPTED_DESIGN_DECISION_SUPERSEDED_FOR_CURRENT_SCREEN`：ADR 0022 的来源闭合一票否决、VO₂ 优先和材料扩张审批已完成其两次扫描用途，不再禁止当前透明派生对象、换材料/网络或跨来源模块重组；扫描事实与来源身份边界继续有效。
- `ACCEPTED_DESIGN_DECISION`：KC 只有在至少两个周期的空间事件通过离散资格化、且预登记两级 strong-raw 既未到达误差地板又能胜任事件解析后才可入场；`NO_BOTTLENECK` 与 `RAW_INCOMPETENT_ROUTE_NO_TEST` 均关闭当前合同内的 KC 测试，但不再消耗全局路线槽位；见 [ADR 0023](docs/adr/0023-require-a-converged-event-and-bounded-strong-raw-gate-before-kc.md) 与 [ADR 0027](docs/adr/0027-remove-the-fixed-count-cap-on-future-research-routes.md)。
- `ACCEPTED_DESIGN_DECISION_SCOPED_BY_ADR_0026`：ADR 0024 的冻结查询族与候选顺序已用于并关闭两次同源对象扫描；独立 oracle 资格化、PINN 残差独立性和完整案例角色隔离继续适用于后续派生对象。
- `ACCEPTED_DESIGN_DECISION_SCOPED_BY_ADR_0026`：standalone KC 只有在未触碰 formal 池获得 `KC_GO` 才能主张独立 KC 突破；当前路线也允许由预声明消融支持的组合交互或接口协同 claim，但不得倒推 KC 或空间模块各自优越。实际计算公平继续适用。
- `VERIFIED_DOCUMENTATION`：已形成 [多 substrate 方法就绪性负面报告](docs/experiment/2026-08-21-multi-substrate-method-readiness-negative-report.md)，综合既有 Q‑POP、R3/R4、TAPF、ETPF、EAF、strong-raw、KC 与 PHA 证据；没有新增数值运行，也没有形成方法科学 verdict。
- `FINAL_CURRENT`：用户批准的 `EAF-KC-v1` F0–F6 授权已在 F3 消耗；单次成核合同修正后的固定 drive bracket 仍无满足主事件门的结构前沿，裁决 `FINAL_FRONT_BENCHMARK_NO_GO`。
- `VERIFIED_IMPLEMENTATION`：F0 来源/许可、F1 无量纲门、F2 显式电极/衬底热沉、制造前沿、canonical artifact、独立 evaluator 及 raw/identity/KC 一次更新均已通过。
- `VERIFIED_DEVELOPMENT_NEGATIVE`：superseding F3 run `20260821T141230Z-pilot-eaf-f3-front-nucleation-correction-002` 在 `0.6–2.4 V` 冻结 bracket 内没有达到相区动态范围 0.20 的校准事件；没有生成可供资格化或 PINN 投票的参考 case。
- `FINAL_CURRENT`：用户批准的 `ETPF-KC-v1` K0–K4 授权已在 K2Q 消耗；K1 smoke 通过，但修正版 K2Q 的五个层级均没有 1 ns 可解析空间前沿，裁决 `ETPF_QUALIFICATION_INVALID_NO_RESOLVED_FRONT`。
- `VERIFIED_IMPLEMENTATION`：局部四周期动力学、制造前沿强形式、二维零驱动守恒、HDF5 和独立 evaluator 通过；K1 run `20260821T122534Z-smoke-etpf-k1-001` 为 `ETPF_SMOKE_PASS`。
- `VERIFIED_DEVELOPMENT_NEGATIVE`：K2 的九个案例都有四次整域形成—恢复，但 K2Q run `20260821T124512Z-pilot-etpf-k2q-qualification-002` 在 1 ns 采样下全部 `resolved_front_cycles=0`，空间相区差最细两层未收缩，不能作为移动前沿 oracle。
- `FINAL_CURRENT`：用户批准的 `QPOP-TAPF-v1` P0–P2 与条件式 P3/P4 授权已由 P2 终局裁决消耗；在该历史 QPOP-TAPF-v1 合同内只允许收口，且其 formal/GPU 从未打开。当前 GOAL 的条件式 GPU/formal 授权由 ADR 0044 独立建立，付费计算仍关闭。
- `VERIFIED_IMPLEMENTATION`：`ThermodynamicPhaseFieldContract`、独立 SciPy 三场 oracle、canonical HDF5 adapter、事件诊断和跨进程磁盘 evaluator 已实现；P1 run `20260821T104436Z-smoke-tapf-p1-001` 为 `TAPF_SMOKE_PASS`。
- `VERIFIED_DEVELOPMENT_NEGATIVE`：P2 run `20260821T104534Z-pilot-tapf-p2-signal-001` 的九个固定案例全部数值完成且平衡违规约为 `1e-13`，但 `0/9` 通过事件门；最高温度 `354.6909252920972 K`，最佳 `eta_max=0.1377504669746865`，裁决 `TAPF_NO_SIGNAL`。
- `VERIFIED_IMPLEMENTATION`：专用 Ubuntu 20.04 WSL2 环境与原生 Q‑POP 最短 smoke 已通过；字段转换和独立磁盘 evaluator 可运行。
- `VERIFIED_IMPLEMENTATION`：artifact/evaluator/ledger、七未知量 raw/identity/KC PINN、完整导数回拉、训练协议、R3/R4 独立 oracle 和跨进程评分链已经实现。
- `VERIFIED_SIGNAL`：CPC v1 随包参考 artifact 含 38 个场快照、8141 节点和 16000 三角单元；冻结 η 阈值下相区占比动态范围为 `0.5534946567`。
- `INVALID_EXECUTION`：R4 smoke 有效，但两个固定信号 pilot 均在首个完整案例前因耦合 η–μ 反应不收敛而失败；R4 信号没有被科学评价。
- `VERIFIED_DEVELOPMENT_NEGATIVE`：初值表示与 step-0 checkpoint 缺陷已经修复；raw-v3 完成固定 1600 次更新后相区动态范围仍为 `0.0`，裁决 `RAW_EVENT_NOT_RESOLVED`。
- `FINAL_CURRENT`：R3、R4、旧七未知量 Q‑POP PINN、QPOP-TAPF-v1、ETPF-KC-v1、EAF-KC-v1 与 `r1-etac-derived-v1` 当前合同均已关闭；R1 P3–P5、P6–P8、formal 与 GPU 未打开。
- `CURRENT_SCOPE`：`GOAL-PAPER-ONE-SHOT-V1` 已在 `SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO` 与无 oracle/event/method evidence 的边界内完成全部本地论文交付。当前不授权新科学执行；HFO-NP-v1、TaOₓ C1、Package A 三候选及所有历史 No-Go 保持冻结，CTH 只保留为未运行的诊断/比较身份。

## 科学状态

- `SUPPORTED_INTERPRETATION`：若 HFO 来源合同和局部 gap 事件成立，只有在一侧割线的两尺度跳跃显著、拒绝 smooth-quadratic null 且 gap/flux/port 同向时，才有理由认为一阶敏感度不足；当前 TKB 未运行，该判断也不能排除纯事件时间平移。
- `HYPOTHESIS`：只有在 `SIDE+`、`RAW_COMPETENT`、transport-side representation bottleneck、`FIELD_HINGE_RELEVANCE_PLUS`、角色分离 diagnostic identity、双轴 bundle utility 与 novelty sufficiency 前门全部通过后，CTH 的 canonical hinge 归纳偏置才可能在有限容量/预算下相对 smooth-quartic、错结点和独立逐协议等强基线改善 held-out 协议响应和完整事件保真；这不等于真实物理解映射不可微。`TEMPORAL+` 后，全局守恒 cKC-NP 仍只是另一条件候选。二者均未实现或获得数值支持，CTH 也未准入。
- `VERIFIED`：当前来源对齐的 HFO-NP-v1 不能闭合唯一 absolute-time waveform contract，因而不能进入来源模型保真、热反馈因果、事件、SIDE、strong-raw、`FIELD_HINGE_RELEVANCE_PLUS` 或 CTH 方法评价；这些下游问题在当前路线均为 `NOT_REACHED`，不是负面方法结果。
- `SUPPORTED_INTERPRETATION`：当前七未知量强形式残差与有限网络/冻结预算形成近初始结构吸引域；器件轨迹变化而结构相区不变，不能用整体优化停滞解释。
- `SUPPORTED_INTERPRETATION`：TAPF P2 失败不是数值崩溃或守恒失败；冻结脉冲与冻结 Allen–Cahn 动力学未在预算窗口内形成跨阈值结构事件。
- `SUPPORTED_INTERPRETATION`：高热扩散、全域 spinodal 过驱动与快速相动力学共同造成小于 1 ns 的整域翻转；3 nm、`-5 K` 缺陷不足以维持可解析前沿。
- `SUPPORTED_INTERPRETATION`：实验深度/脉冲尺度满足前沿无量纲窗口，但当前冻结的 `A_PRIME` 横向/接触几何与确定性闭合不能在允许 drive 范围内产生主端点所需的空间事件；这不构成 KC 方法失败。
- `SUPPORTED_INTERPRETATION`：公开实现最完整的 Q‑POP 缺合格结构事件与完整参考/案例角色闭合；结构事件最相关的后续工作又缺公开固定且许可明确的对应求解器，两类证据未在同一来源链内相交。
- `SUPPORTED_INTERPRETATION`：V₂O₃ 的事件、通用电热相场的方程和 FerroX 的实现分别最接近旧同源对象需求，但没有在同一来源链相交；它们不能拼成“作者复现”，却可在来源、许可和改动透明时成为新派生 idea 的不同模块。
- `SUPPORTED_INTERPRETATION`：R1 P2 的冻结电压轴呈现“弱驱动不足形成，强驱动跨周期残留或近全域覆盖”的形成—恢复权衡；这是 `r1-etac-derived-v1` 的事件资格失败，不是数值崩溃或阈值实现错误。
- `HYPOTHESIS`：一个同时针对时间刚性与空间局域界面的双模块 PINN，若配合未来另行资格化的事件可辨二维器件 benchmark，仍可能形成可裁决论文证据；R1 P2 没有检验该方法假设。
- `UNKNOWN`：结构动力学时钟、IRAC 或二者组合在任何未来合格对象上的实际增量；R1 P2 的有界负结果不是 PINN、Allen–Cahn、KC′或自适应采样的一般性科学失败。
- Q‑POP 与所有 reduced oracle 都是合成数值参考，不是实验真值。
- 当前没有正面方法结论、formal OOD 证据、实验验证、SOTA 或期刊接收前景主张。

## 工程与治理状态

- 每次真实 run 均保留 intent、immutable manifest 和 append-only index；当前 ledger 一一对应关系有效。
- 当前权威链为 `AGENTS.md → CODEX_CONTEXT.md → docs/README.md → 研究规范 → rules.md → active_phase.md → PROJECT_STATE.md → docs/plans/NEXT_ACTIONS.md`。
- 2026-08-24 的 `neat-freak` 收尾曾把候选入口路由到 SRPG 综合审查；本轮又显式路由到 HFO-NP-v1 对抗性整合并归档旧 SRPG 等待计划。两次动作都只证明文档同步，不构成科学证据。
- 文档一致性门禁为 `.venv\Scripts\python.exe -m pinn_pcm_sci.document_consistency --root .`；权威状态、唯一 live plan、文档角色、ADR 索引、本地链接、ledger 和运行锁 ignore 必须同时通过。
- 外部 Skill 中本轮实际使用的 `research` 与 `domain-modeling` 已完成固定上游提交、MIT 许可和 prompt-only 运行边界的最小对账；其余 lockfile 管理 Skill 仍为 `UNRECONCILED`。该状态只影响治理可追溯性，不构成科学证据。
- 当前未推送、未开 PR；GPU/formal 虽曾在一次性 GOAL 中获得条件授权，但未到达科学前门、从未启动，且该授权现已随 GOAL 完成而消费关闭。

## 历史事实入口

环境 attempts 001–007、provider 修正、Q‑POP smoke、N1/N2、R3/R4、PHA/KC development 和所有失败记录不在本文件重复。权威历史入口为：

- [实验索引](docs/experiment/INDEX.md)
- [G2 provider 修正收口](docs/experiment/2026-08-21-g2-provider-correction-closeout.md)
- [N1–N3B 收口](docs/experiment/2026-08-21-n1-n3b-terminal-closeout.md)
- [R4 与 raw-v3 收口](docs/experiment/2026-08-21-r4-and-raw-v3-closeout.md)
- [QPOP-TAPF-v1 P2 收口](docs/experiment/2026-08-21-qpop-tapf-p2-closeout.md)
- [ETPF-KC-v1 K2Q 收口](docs/experiment/2026-08-21-etpf-k2q-terminal-closeout.md)
- [历史计划归档](archive/README.md)

## 有意保留的未知项

- 是否会出现足以改变 `a=0.32/0.16 nm` 最早硬失败的作者勘误或固定模型版本说明；没有该类新证据时当前 Ta₂O₅/TaOₓ 家族不重开；
- protocol/history/state 表示能否区分迟滞分支，唯一协议轴是否通过含 smooth-quadratic null 的 TKB；
- FP64 strong raw、SA-PINN、Jacobian/tangent 与相场 causal/adaptive 强基线是否已经解释目标增益；
- 来源锚定固定时长 waveform-scale A′ 是否被 G0 一手合同允许，来源对齐端口轨迹与跨事件空位空间状态能否在联合不确定性内同时闭合；
- 对齐后的连续输运场是否在三尺度上通过 `FIELD_HINGE_RELEVANCE_PLUS`，并排除纯事件时间平移、detector、smooth curvature 与镜像错结点解释；该门不能证明数学不可微；
- CTH 的来源锚点 `a0` 是否位于有限尺度 hinge-relevant 邻域、共同 `B` 是否避免 Jacobian nullspace，以及联合向量 `h=(h_c,h_J)` 能否在互斥 identity-development cases 的 `δ=±1/4` 盲 microviews 上相对 smooth4/错结点/parameter-conditioned raw 显示增量，并在 seen protocols 上不被 `IND-5` 与总成本严格支配；任一门失败均按 ADR 0037–0039 收口，不自动重定 knot 或选择另一候选；
- 一个实质改变 exact-revision 许可/依赖身份合同的未来 R2 是否还能闭合来源、事件、strong raw 与方法可归因门；
- 在新的合格对象上，界面感知空间模块最终属于独立正向贡献、组合交互贡献还是 supporting module；
- 结构动力学时钟在合格空间异步局部结构相事件 oracle 上的实际增量仍为 `UNKNOWN`；
- formal 预算、统计规则和可写 claim 的最终门槛。
