# 架构与研究决策索引

- [0058：激活 PHK-V2.3 LF2 measure-calibrated feasible PINN](0058-activate-phk-v23-lf2-measure-calibrated-feasible-pinn.md) — 唯一 seed-17 trajectory 先做评价测度校准 M0，再条件式做可行性约束 full-physics M1；CPU 资格已通过，stress/PJGR/R2/额外轨迹保持关闭。
- [0057：激活并收口 PHK-V2.3 LF1 event-preserving multi-fidelity pilot](0057-activate-phk-v23-lf1-event-preserving-multifidelity-pilot.md) — B0/B final 均恢复两周期 competence且 physics objective 显著下降，但冻结 phase/temperature 增量门失败，故以 `LF1_DATA_ONLY_VALUE_NO_PINN_GAIN` 收口；C 未触发，继续禁止 PJGR/R2/stress。
- [0056：激活并收口 PHK-V2.3 LF0 exact-top warm-start attribution campaign](0056-activate-phk-v23-lf0-exact-top-warmstart-attribution.md) — A 无 competence；B 的 step-800 data-only checkpoint 违反 potential validity，故以 `LF0_NUMERICAL_OR_IDENTITY_INVALID` 收口且不执行条件 C；stress 继续 sealed/unread。
- [0055：激活并收口 PHK-V2.3 C0 reference/discrete/strong-form compatibility audit](0055-activate-phk-v23-c0-reference-discrete-strongform-compatibility-audit.md) — 一次本地 CPU/FP64 nominal development diagnostic 识别 E2 hard-lift output inadmissibility；不训练、不使用 GPU、不读取 stress，完成后不自动授权下一路线。
- [0054：在已验证工程修复后恢复 R1X 原科学任务](0054-resume-r1x-after-verified-engineering-repair.md) — 覆盖旧的一次 engineering-retry 限制；仅当首步前纯工程故障根因已明确且隔离回归证明修复时，重执行相同冻结任务且不消耗科学 run 配额。
- [0053：激活 PHK-V2.3 R1X 有界 clean-coupling campaign](0053-activate-phk-v23-r1x-bounded-clean-coupling-campaign.md) — 最多三条 non-voting exploration 与一条条件性 frozen confirmation；每条云端运行回收后立即关机，nominal 仅在本地关机验证后评价，stress 始终 sealed。
- [0052：激活 PHK-V2.3 R1a ConFIG competence recovery](0052-activate-phk-v23-r1a-config-competence-recovery.md) — 只授权一次 reference-blind STRONG_RAW/seed-17/FP64/V100 1000-update ConFIG solver-backbone 恢复实验；关机后本地 nominal 裁决，stress 继续 sealed。

本目录只解释“为什么接受某项决定”。当前能否执行由 [`active_phase.md`](../../active_phase.md) 决定，已运行事实由 [`docs/experiment/`](../experiment/) 保存。

## 冻结的 Kinetics-Clock 政策合同

- [Q1–Q23 决策总表](research_decisions_Q1_Q23.md)
- [0001：限定高频主张](0001-bound-high-frequency-claim-to-thermal-vo2-time-stiffness.md)
- [0002：采用逐案例 PINN 求解评价](0002-use-post-lock-per-case-pinn-solver-evaluation.md)
- [0003：冻结经核对的 Q‑POP PhysicalContract](0003-freeze-a-reconciled-qpop-physical-contract.md)
- [0004：采用场选择性的结构动力学时钟](0004-use-a-field-selective-structural-kinetics-clock.md)
- [0005：唯一正向干预为构造单调时钟](0005-use-a-constructively-monotone-clock-as-the-sole-positive-intervention.md)
- [0006：主训练不读取 Q‑POP 内部场标签](0006-separate-qpop-labels-from-primary-training-and-use-layered-adjudication.md)
- [0007：物理断点采用分段强形式](0007-use-piecewise-strong-form-at-physical-breakpoints.md)
- [0008：显式治理 KC 止损与 PHA 转换](0008-govern-kc-stop-and-pha-transition-with-explicit-dispositions.md)
- [0009：使用两个独立端点和角色隔离 case pool](0009-use-two-independent-endpoints-and-role-isolated-case-pools.md)
- [0010：完整 case 是统计单位并冻结预算政策](0010-treat-complete-cases-as-units-and-freeze-budget-policy.md)
- [0011：隔离结构时钟计算图](0011-isolate-the-structural-clock-computation-graph.md)
- [0012：用有界 pilot 冻结时钟优化与可容许性](0012-freeze-clock-optimization-and-admissibility-by-bounded-pilot.md)
- [0013：intent-to-run 与有序 KC 裁决](0013-use-intent-to-run-and-ordered-kc-adjudication.md)

## 后续有界实现与路线决定

- [当前 HFO-NP-v1 Q1–Q68 决策总索引](research_decisions_HFO_Q1_Q68.md) — 路由当前 HFO 编号空间的有效处置；不覆盖历史 KC Q1–Q23 或 R1 Q1–Q24，也不授权执行。

ADR 0019–0025 保留旧 exact-KC、同源对象扫描及其证据合同；ADR 0026 已允许透明派生对象，ADR 0027 已撤销固定研究路线次数上限。ADR 0028–0040 保存 R1、R2、HFO 与 TaOₓ C1 的设计史和有界 No-Go。ADR 0041 冻结方法盲单链对象筛选，ADR 0042 记录该包在 3/3 家族、11/12 载体处组合级有界关闭。ADR 0043 提出的模块化主锚点路线保持历史 `PROPOSED` 身份；ADR 0044 已采纳并完成 `GOAL-PAPER-ONE-SHOT-V1`。ADR 0045 采纳的 `PHK-V2` 已由 Oracle Gate No-Go 与 V2 完成包消费关闭。ADR 0046 新建且完成不回写旧终局的 `PHK-V2.1` 工程—科学双阶段合同。ADR 0047 以前瞻数据角色、预算和止损边界启动独立的 `PHK-V2.2R` 一周 Method-MVP；ADR 0048 在 GPU profile 后激活 v1.1 四臂 fallback；ADR 0049 完成一次本地 CPU R0A；ADR 0050 完成一次 R0B 175-step reference-blind temporal-precursor replay；ADR 0051 完成一次 R0C 25-step Adam-effective update materiality replay。所有旧扫描事实、失败 intent、论文和 No-Go 原样有效。

- [R1 FULL_DESIGN Q1–Q24 决策合同](research_decisions_R1_FULL_DESIGN_GRILL_2026-08-22.md) — 独立于历史 KC-PINN Q1–Q23 的当前 R1 决策身份。

- [0014：在 reduced oracle 中恢复动态电子序参量](0014-restore-dynamic-electronic-order-in-the-bounded-reduced-oracle.md) — 历史 R4 路线决定；执行结果已由 [R4/raw-v3 收口](../experiment/2026-08-21-r4-and-raw-v3-closeout.md) 关闭。
- [0015：初值精确结构残差与非初始 checkpoint](0015-use-initial-condition-exact-structural-residuals-and-noninitial-checkpoints.md) — 当前保留的实现合同。
- [0016：采用 Q‑POP 热力学对齐的三场二维相场 benchmark](0016-use-a-qpop-thermodynamics-aligned-phase-field-benchmark.md) — 历史 TAPF 科学核心与证据边界；P2 已由 [TAPF 收口](../experiment/2026-08-21-qpop-tapf-p2-closeout.md) 关闭。
- [0017：先用电热倾斜相场 benchmark 裁决结构动力学时钟机制](0017-use-a-mechanism-first-electrothermal-tilted-phase-field-benchmark.md) — 历史 ETPF 路线；K2Q 已由终局记录关闭。
- [0018：采用实验时间尺度约束的二维电热结构前沿 benchmark](0018-adopt-an-experiment-timescale-constrained-electrothermal-front-benchmark.md) — 历史 `EAF-KC-v1` 路线；F3 已由终局记录关闭。
- [0019：以来源闭合对象研究空间异步局部结构相事件](0019-target-spatially-asynchronous-events-on-a-source-complete-object.md) — 旧 exact-KC 路线的事件语义与同源对象边界；当前筛选由 ADR 0026 细化。
- [0020：未来 KC 正向研究最多消耗三条候选路线](0020-cap-future-kc-research-at-three-candidate-routes.md) — 历史计数决定，已由 ADR 0027 覆盖，不再约束后续研究。
- [0021：第二正向模块必须同时通过独立门与组合增量门](0021-admit-a-second-positive-module-only-after-independent-and-combination-gates.md) — 旧 exact-KC 的独立正向 claim 门；当前允许联合候选设计，但主要贡献模块仍须新证据。
- [0022：采用来源闭合一票否决的 VO₂ 优先候选组合](0022-use-a-veto-first-vo2-source-complete-candidate-portfolio.md) — 已执行并关闭的同源对象扫描合同；当前不再全局禁止派生对象或材料扩张。
- [0023：KC 入场前必须通过收敛事件门与两级 strong-raw 门](0023-require-a-converged-event-and-bounded-strong-raw-gate-before-kc.md) — 两周期空间事件、`NO_BOTTLENECK` 与 raw 不胜任处置继续有效；全局路线槽位语义已由 ADR 0027 覆盖。
- [0024：科学运行前冻结来源候选顺序并隔离 oracle 案例角色](0024-freeze-the-source-shortlist-and-isolate-oracle-case-roles.md) — 有界扫描、独立资格化与四类完整案例；不授权检索或执行。
- [0025：只有 standalone formal KC_GO 才算路线突破](0025-require-standalone-formal-kc-go-before-claiming-a-breakthrough.md) — 只约束独立 KC 突破 claim；组合交互与 supporting-module 路由由 ADR 0026 细化。
- [0026：允许透明派生对象与有界方法重组继续新 idea 筛选](0026-allow-transparent-derived-objects-and-bounded-method-recombination.md) — 用户纠正后的材料/网络/模块迁移、A/A′ 透明派生对象、组合贡献与论文故事边界；只授权 FAST_SCAN/计划，不授权科学执行。
- [0027：撤销未来研究路线的固定次数上限](0027-remove-the-fixed-count-cap-on-future-research-routes.md) — 取消全局路线计数与剩余槽位语义；保留逐路线计划、预算、证据门和停止条件，不授权科学执行。
- [0028：冻结 R1 四因子、六臂与四池证据设计](0028-freeze-r1-factorial-six-arm-and-four-pool-design.md) — 固定当前派生 benchmark、瓶颈准入、方法归因、案例隔离与失败计票；formal/GPU 仍不授权。
- [0029：授权 R2 严格热耦合 FerroX 的 P0 来源门](0029-authorize-r2-strict-thermal-ferrox-p0-source-gate.md) — 接受 R2 `FULL_DESIGN`，普通批准只打开最多 12 项一手来源、零求解的 P0；该包现以 `R2_P0_SOURCE_IDENTITY_NO_GO` 终止，B–D、solver、training、formal/GPU 均未授权。
- [0030：选择 HFO-NP-v1 规划对象与条件式 KC′/SRPG 证据路由](0030-select-hfo-np-v1-and-evidence-routed-kc-srpg.md) — 冻结下一份 G0–G1 PLAN 的透明缺陷态对象、局部协议束、双极 gap 事件和证据路由；只记录计划架构，不授权科研执行。
- [0031：修订 HFO 来源初态、侧向信息门与方法路由](0031-revise-hfo-source-side-gate-and-method-routing.md) — 部分覆盖 ADR 0030：初态待 G0 回源、G1 单轴 TKB、fixed-slot SRPG 降级、守恒 cKC-NP 仅在未来 temporal 门后候选；不授权科研执行。
- [0032：延后 side 方法选择并约束 HFO PINN 训练比较](0032-defer-side-method-and-bound-hfo-pinn-training-comparators.md) — 修订 Q30–Q36：side 方法不预选，cKC 只在 TEMPORAL+ 后按物理时间守恒回拉，Fourier/curriculum/weighting/sampling/optimizer 均进入分轨有界比较；不授权科研执行。
- [0033：资格化耦合训练模式并冻结 strong-raw 裁决边界](0033-qualify-coupling-mode-and-freeze-strong-raw-adjudication.md) — 修订 Q37–Q43：不默认 monolithic joint training，允许 backbone 不可判定，要求 wider-raw/extra-work raw 双控制、预冻结 method-vote case×cycle、seed quorum 与证据式单次 supersede；不授权科研执行。
- [0034：冻结单一方法主张与 HFO 域内 forward 论文边界](0034-freeze-single-method-headline-and-hfo-scoped-forward-claim.md) — 接受 Q44–Q48：单一 load-bearing PINN headline、HFO 来源有效完整案例 OOD、事件保真优先的计算 Pareto、forward-only 及 pilot/formal 前两次新颖性刷新；不选择方法或授权科研执行。
- [0035：冻结因果单机制 pilot、两族 formal OOD 与碰撞否决](0035-freeze-causal-single-primitive-pilot-and-collision-veto.md) — 接受 Q49–Q53：方法必须闭合瓶颈—干预—探针/负控—事件—守卫链，首轮只含一个新可训练机制，formal 采用一个机制对齐家族加一个正交稳健家族，并以 direct-near 覆盖触发停止/收缩；不授权科研执行。
- [0036：选择 canonical TKF 作为待身份诊断的 FULL_PLAN 靶标](0036-select-canonical-tkf-as-diagnostic-gated-full-plan-target.md) — 否决五视图不可辨识的自由 TKF-v0，只把 TKF-CANON-PINN 选为 future FULL_PLAN 条件式靶标，并要求 smooth-quartic control 与 held-out microviews 先通过身份门；不准入或授权方法。
- [0037：在 TKF FULL_PLAN 前增加波形、保真、场身份与新颖性门](0037-require-waveform-fidelity-field-kink-identity-and-novelty-gates.md) — 接受 Q54–Q58：唯一轴改为来源锚定 fixed-duration waveform-scale A′，增加来源模型保真、`FIELD_KINK_PLUS`、独立 identity protocol 与 novelty sufficiency；FULL_PLAN 仍未定稿，方法未准入或授权。
- [0038：将 TKF 重构为有限预算 CTH 并增加热因果、可容许性与效用门](0038-reframe-tkf-as-cth-and-require-thermal-causality-admissibility-and-utility.md) — 接受 Q59–Q63：撤回真实 kink 语义，把 CTH-PINN 仅作为有限预算 hinge 条件靶标，并要求逐系数 IC/BC、thermal-feedback-off、力学必要即止损及 independent-per-view utility kill；不授权科研执行。
- [0039：分离 CTH 身份证据并冻结锚点、向量原语、输出变换与效用裁决](0039-separate-cth-identity-evidence-and-freeze-anchor-vector-transform-and-utility.md) — 接受 Q64–Q68：qualification 与 blind identity-development 分池，固定来源 `a0`、联合 `h=(h_c,h_J)`、共同 `C1` 变换及 `IND-5`/blind bundle/`IND-7` 双轴 Pareto；不授权科研执行。
- [0040：新对象来源筛选后接受有界不选择对象](0040-select-new-source-complete-object.md) — 2025 Pd/Ta₂O₅/TaOₓ/Pd 论文与固定作者模型的 `a=0.32/0.16 nm` 冲突触发最早 source–model alignment 否决；记录 `NO_OBJECT_SELECTED / METHOD_NOT_REACHED`，不授权扩搜、实现或历史路线重开。
- [0041：采用“一对象—一瓶颈—一论文”目标并授权方法盲筛选包 A](0041-adopt-one-object-one-bottleneck-goal-and-authorize-package-a.md) — 冻结首个通过即锁定、候选/组合停止量词、clean-room 来源合同、历史 No-Go 排除和 48 小时/12 载体/3 家族边界；只授权静态来源审查与治理，不授权构建、求解、训练、GPU、formal 或 Git 发布。
- [0042：以方法盲对象组合 No-Go 关闭授权包 A](0042-close-package-a-with-method-blind-object-portfolio-no-go.md) — 三个冻结候选均在 Gate 3 合同完整性最早失败后，以 11/12 新增一手载体触发组合级有界收口；无对象锁定，CTH 与所有方法门均未到达，后续科研动作须新 PLAN 与批准。
- [0043：提出模块化来源对齐对象到论文初稿的最短关键路径](0043-propose-modular-source-aligned-object-to-manuscript-critical-path.md) — 以一个强主锚点、最多两个兼容模块来源和最多一个二值非拓扑分支替代旧单链完整性合同；冻结 object→oracle/event→raw→CTH→formal→manuscript 路径，但保持 `PROPOSED_NOT_AUTHORIZED`。
- [0044：采纳 GOAL-PAPER-ONE-SHOT-V1 一次性本地研究执行授权](0044-adopt-goal-paper-one-shot-v1.md) — 批准 S0–S6 与本地完整稿件连续执行、预注册 Route 1/2/3 自动切换及冻结总预算；继续禁止付费资源、凭据披露、作者联系、外部上传/投稿和 Git 远程操作。
- [0045：采纳 PHK-V2 强基线复现与双模块正向研究执行](0045-adopt-phk-v2-strong-baseline-and-two-module-execution.md) — 固定 Sharp paper/repo 双身份、general strong controls、transparent reduced wall-cell、PHA/KC 独立门、complete-case formal 与本地有界预算；实际在 Oracle Gate 以 event/control No-Go 收口，方法阶段未到达，授权已消费关闭。
- [0046：采纳 PHK-V2.1 独立工程—科学双阶段合同](0046-adopt-phk-v21-independent-engineering-science-contract.md) — 先在非投票沙盒固定 control solver 与可恢复两周期对象，再另行冻结新 oracle/baseline/method/formal；只覆盖旧完成态的授权语义，不改写 PHK-V2 No-Go。
- [0047：采纳 PHK-V2.2R 极速方法抢救冲刺](0047-adopt-phk-v22r-rapid-method-rescue-sprint.md) — 保留 V2.1 No-Go，以 nominal fixed-discretization reference 开发 S-first 方法并密封两个 stress case，授权一周内的代码、AutoDL 150 元上限、单-seed有限证据、稿件与当前仓库推送；不授权投稿。
- [0048：在 GPU profile 后激活 PHK-V2.2R v1.1 四臂冲刺](0048-activate-phk-v22r-v11-four-arm-sprint-after-gpu-profile.md) — strict PHA 增益门失败后删除 routing，generic-RAR 截止后采用四臂 fallback；授权先完成 v1.1 对齐，再连续执行 nominal、条件性 sealed confirmation 与论文初稿，继续禁止投稿和结果导向救援。
- [0049：激活 PHK-V2.3 R0A 本地 CPU 只读失效诊断](0049-activate-phk-v23-r0a-cpu-diagnostics.md) — 只允许一次既有 STRONG_RAW checkpoint 的 CPU/FP64 诊断与本地 nominal teacher probes；不训练、不更新参数、不读 stress，也不授权 R0B/R1/PJGR。
- [0050：激活并收口 PHK-V2.3 R0B 首次窗口切换 175-step 最小诊断](0050-activate-phk-v23-r0b-first-switch-175-minimal-v2.md) — 一次 V100 reference-blind STRONG_RAW scratch replay 已识别 `GRADIENT_STARVATION` 为最早持续前兆并完成回收关机；结果不是因果 root 或方法证据，不授权 recovery、R1、PJGR、stress 或第二次 run。
- [0051：激活并收口 PHK-V2.3 R0C 25-step 有效更新诊断](0051-activate-phk-v23-r0c-effective-update-25-v100.md) — 唯一 V100 reference-blind STRONG_RAW 25-step replay 发现 Adam 对 phase raw-gradient starvation 形成物质有效更新补偿；不恢复 competence，不授权 recovery、R1、PJGR、reference 或 stress。
