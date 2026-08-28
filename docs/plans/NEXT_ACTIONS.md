# PLAN-PHK-V2.1-V1：可恢复二维 benchmark、强基线与 PHK 归因

- `phase_id`: `PHK_V21_COMPLETE_ORACLE_NO_GO`
- `lifecycle_state`: `COMPLETED`
- `blocker_id`: `NONE`
- `claim_status`: `PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN_NO_BASELINE_OR_METHOD_EVIDENCE`
- `authorization_state`: `PHK_V21_LOCAL_EXECUTION_CONSUMED_AND_CLOSED`
- `authorization_package`: `E0_TO_S7_BOUNDED_LOCAL_ENGINEERING_SCIENCE_AND_MANUSCRIPT`
- `plan_status`: `COMPLETED_AT_S1_ORACLE_NO_GO`
- `object_selection_status`: `ORACLE_QUALIFICATION_NO_GO_FROZEN`
- `method_selection_status`: `NOT_REACHED_ORACLE_GATE_NO_GO`
- `current_stage`: `COMPLETE`
- `next_research_execution_authorized`: `false`
- `supersedes`: `PLAN_PHK_V2_V1_COMPLETE_NO_FURTHER_EXECUTION_AUTHORIZATION_SEMANTICS_ONLY`
- `preserves`: `PHK_V2_ORACLE_NO_GO_FAILED_INTENTS_PAPER_AND_ALL_PRIOR_EVIDENCE`
- `source_review_sha256`: `EDA89F42F357C5CA156F702D4343D8097B02A8590B80F0D6E8A5EB4ACE0E34BD`
- `s0_scientific_freeze`: `docs/governance/2026-08-28-phk-v21-s0-scientific-contract-freeze.md`
- `effective_date`: `2026-08-28`

## 1. 获批 GOAL 与完成语义

执行独立的 `PHK_V21_REPEATABLE_EVENT`：先修复 control branch 并资格化一个二维、局域、两周期形成—恢复的透明电热—相态 benchmark；完成 Sharp/PF 固定身份的论文指标复现与 neural floor 封存；随后执行四臂瓶颈诊断、等预算 PHA-MF × field-selective KC 2×2、容量/计算与机制挑战者以及 complete-case formal OOD。

正向路线只有在以下链条全部闭合时成立：

```text
qualified object
  -> oracle/event/controls/floor
  -> Sharp/PF metric replication
  -> strong raw competent
  -> four-arm bottleneck diagnosis
  -> PHA standalone + KC standalone + PHK interaction
  -> device consequence
  -> formal OOD
```

至少一个预声明结构或器件 co-primary 必须显著优于最强合格 baseline，另一个 co-primary 与全部关键物理端点必须非劣。若任一上游门失败，按本计划的冻结停止表交付对应的有边界终局论文与复现包；不靠移动对象、阈值、case、seed、预算或统计 margin 制造正面结论。

## 2. 不可改写的历史边界

- PHK‑V2 保持 `PHK_V2_COMPLETE_ORACLE_NO_GO`；旧对象、12-intent ladder、intent 9 失败、intents 10–12 未到达、terminal summary、`paper/paper_v2/` 与 claim ceiling 原样有效。
- 当前新路线不重跑旧 intent，不复用旧 324-case split，不把新 solver 或新对象结果回填到 PHK‑V2。
- `GOAL-PAPER-ONE-SHOT-V1`、SYN‑EDT、Q‑POP、HFO、TaOₓ、Package A、R1/R2 与所有旧 No-Go/failed intents 原样保留。
- 路线 A“重复、局域、可恢复事件”是唯一对象任务。累积 programming、SRPG、history encoder 和第三个 headline 模块不进入本 GOAL。
- 新对象始终称透明、无量纲、literature-inspired synthetic benchmark；不称作者模型复现、材料校准、实验器件验证或真实 PCM 预测。

## 3. 授权范围

本授权覆盖：有界一手来源核验、开放代码固定身份审计与合法隔离复现、项目内 clean-room 实现、非投票工程诊断、CPU oracle、本地可用 GPU development/formal、统计图表与本地英文/中文正文、补充和复现包。达到门后自动推进，无需逐阶段再次批准。

不授权：付费或云端计算、凭据披露、作者联系、投稿、外部上传、Git push/PR/release、购买许可、破坏性机器改动或把 GPL/Penn 限制源码并入主库。

## 4. E0–E2：非投票工程阶段

机器边界见 [program contract](../../configs/phk_v21/program_contract.json)与 [engineering contract](../../configs/phk_v21/engineering_contract.json)。工程输出只能决定后续 scientific contract，不能作为论文方法结果。

### E1 控制分支求解

1. 用固定 2×2 snapshot 复现旧 phase-Newton line-search failure。
2. 逐一检验 legacy damped Newton、trust-region reflective、logit analytic Newton、pseudo-transient Newton、smaller-step diagnostic 与 Anderson outer coupling。
3. 每个 probe 记录 residual、step、phase range、temperature、state change、Jacobian directional error/condition proxy、linear solves、CPU 与失败身份。
4. 只有同时通过最小 red fixture、full-duration conductivity-off、nominal/Joule-off sentinels、physical bounds、residual 与 exact replay 的一个固定方案可进入新 scientific freeze。
5. scientific ladder 中禁止动态 solver switching；smaller-step 只作诊断，不可冒充同一 numerical contract 的修复。

### E2 有界对象设计图

1. Stage 1 固定 16 个 coarse factorial：period × cooling × cold mobility × thermal drive。
2. 按预登记的 event/locality/rank 选 2 个 parent；每个 parent 固定生成 amplitude × hold × latent 的 8 个 refinement，共 16 个。
3. coarse 总数最多 32；最多 3 个 promotion 进入 medium；唯一最终候选运行 zero/Joule-off/conductivity-off/latent-off/wide-heater/narrow-interface controls。
4. 候选必须同时满足：两周期各有新 upward event且持续至少 3 saved steps；每周期 recovery ≥0.70；cycle peak drift ≤0.20；full-domain peak ≤0.45；outside-ROI peak ≤0.10；Joule-off 无 event；全部 controls 可执行；全部数值守卫通过。
5. 没有候选通过时终止为 `PHK_V21_ENGINEERING_NO_ADMISSIBLE_REPEATABLE_EVENT_OBJECT`，不得进入 PINN。

## 5. S0：正式科学 freeze

工程候选通过后、任何 voting oracle 或 neural 运行前，必须写入并哈希：

- `configs/phk_v21/object_numerical_contract.json`；
- `configs/phk_v21/case_split_manifest.json`；
- `configs/phk_v21/oracle_and_floor_contract.json`；
- `configs/phk_v21/baseline_replication_contract.json`；
- `configs/phk_v21/method_contract.json`；
- Q/D/I1/I2/F_A/F_O/R complete-case identities、seed、公共训练协议、端点、normalizer、budget、formal margin 与停止规则。

工程 cases 与正式 Q/D/I/formal cases 身份隔离。正式 split 基于新对象重新生成；完整 history 属于 case identity；同一 case 不跨 pool。

## 6. S1：Oracle、controls 与 neural floor

正式 qualification 至少包括 manufactured、zero-drive、coarse/medium/fine/extra-fine、medium half-dt、independent replay、Joule-off、conductivity-off、latent-off、wide-heater、narrow-interface 与 fixed-solver cross-check。

要求：

- medium→fine→extra-fine 的承重分量单调收缩；
- medium vs half-dt finite；
- independent replay 通过冻结 tolerance；
- 两周期 event/recovery/locality 与全部 numerical guards 通过；
- 所有 controls 完成并仅形成其合同允许的 causal claim；
- 对每个 component 在 neural work 前封存
  `U_j=max(space_delta,time_delta,replay_delta,solver_delta)`。

任一 event/control/convergence/floor 门失败即 `STOP_BEFORE_PINN_TRAINING`。

## 7. S2：Sharp/PF 固定身份论文指标复现

- Sharp paper identity 与 repo recipe 分开；在隔离 GPL 环境至少复现一个 2D case、一张主图或主指标、paper-spec/repo-recipe ordering，并报告至少 3 seeds 的缩小版稳定性。
- PF 在隔离 GPL 环境复现一个 1D activation 和一个 2D phase-field case，核对 NTK weighting 与 RAR 的作者趋势。
- jaxpi2/adaptive pseudo-time 作为 general-strong/KC falsification control；若官方完整环境仍不可运行，只能按 Apache-2.0 代码和论文公式 clean-room 适配并明确不是官方复现。
- baseline replication contract 必须在首次作者代码 metric run 前固定 exact case、commit、environment、metric extraction、tolerance、seed 与失败语义。
- 若不能建立至少 Sharp 与 PF 的规定复现身份，停止方法 headline，不把 module smoke 改称论文复现。

## 8. S3：strong raw 与四臂瓶颈诊断

公共参数、collocation support、optimizer updates、AD work 与 gross compute 在 arm 开始前固定。四臂为：

1. strong raw；
2. global multi-frequency；
3. phase-aware sampling；
4. global MF + phase-aware sampling。

只在 strong raw 能解析 event/phase/device endpoints 且 hard guards 通过时评价瓶颈。sampling 显著领先表示 support scarcity；Fourier 显著领先表示 representation；组合超加和才准入 PHA routing；四臂均差且 loss/gradient 失衡则优先裁决 stiffness/optimization，不启动 PHA headline。

## 9. S4–S5：等预算 PHA×KC 归因与挑战者

核心 2×2：

| arm | PHA | KC |
| --- | ---: | ---: |
| strong raw | 0 | 0 |
| PHA-only | 1 | 0 |
| KC-only | 0 | 1 |
| PHK-full | 1 | 1 |

PHA 必须优于 global MF、wider raw、extra-work raw、phase-only/Joule-only/generic/shuffled gates；否则不得主张 physics-routed frequency allocation。

KC 只作用于 phase branch，完整保留物理时间 pullback。它必须在 stiff cases 上优于 identity、parameter-matched generic monotone、random fixed、all-field warp、wrong-segment 与 adaptive pseudo-time，并在 smooth control 上不表现为普遍坐标变换收益；否则不得主张 kinetics specificity。

单模块失败不能由 full 隐藏。full 必须相对最强 standalone 建立预声明增量或交互；参数量、更新数、wall time、forward/AD work、失败 seed 与 gross compute 全量报告。

## 10. S6：sealed complete-case formal OOD

formal 只在 D/I 完成、候选与阈值锁定、功效和预算可行后开封。两类 whole-factor OOD：

- 几何/热边界轴：heater width、active-layer thickness、thermal boundary strength；
- 动力学/协议轴：mobility ratio、interface width、pulse rise/hold/recovery。

科学单位是完整 case，seed 为 case 内重复。paired error 定义为 baseline minus proposed；两个 co-primary 为时空 phase-region symmetric difference 与 terminal-current trace error。至少一个 co-primary 的 simultaneous one-sided lower CI 必须超过 `max(2U_oracle,2U_seed,0.5 floor units)`，另一个与关键物理端点必须通过 0.5 floor-unit noninferiority；至少一个 F_O family 方向一致。失败 case/seed 不替换。

## 11. 预算

- 总 CPU process core-hours：128；
- E1–E2 engineering：24；oracle：32；官方 baseline：24；方法、统计与制品：48；
- 本地 development GPU：最多 64 exclusive hours；本地 formal GPU：最多 64 exclusive hours；设备不可用不授权云端替代；
- 外部新增一手载体最多 6；付费/云端、外部发布与 Git remote 均为 0；
- 每个失败 intent 计入预算，无 replacement seed/case。

## 12. 停止表

| 最早失败门 | terminal route |
| --- | --- |
| 无工程候选 | `PHK_V21_ENGINEERING_NO_ADMISSIBLE_REPEATABLE_EVENT_OBJECT` |
| oracle/event/control/floor | `PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN` |
| Sharp/PF 指标复现 | `PHK_V21_BASELINE_REPLICATION_NO_GO_STOP_BEFORE_METHOD_CLAIM` |
| strong raw 不胜任 | `PHK_V21_RAW_INCOMPETENT_METHOD_NOT_ESTIMABLE` |
| 无表示/support/stiffness瓶颈 | `PHK_V21_NO_BOTTLENECK_HEADLINE_NO_GO` |
| PHA/KC/组合或挑战者门失败 | 对应 `PHK_V21_METHOD_NO_GO` |
| formal 功效/预算不足 | `PHK_V21_FORMAL_POWER_BUDGET_INSUFFICIENT` |
| formal superiority/NI 失败 | `PHK_V21_FORMAL_NO_GO` |

每个 terminal 都必须交付 terminal machine summary、失败/未到达计账、英文/中文正文、图表、参考文献、补充、复现、claim matrix、reviewer-risk audit 与 package manifest。只有实际 formal 正面门通过时，制品才可称“正向 PHK-PINN 第二版”；否则标题和结论必须反映真实终点。

## 13. 实际终点与完成交付

`VERIFIED`：本计划在最早冻结停止门 S1 完成。14/14 qualification intents 均完成、0 solver execution failures、0 hard-guard failures；nominal 两周期 event、zero/Joule-off no-event、exact replay 与独立 fixed-solver cross-check 均可评价。但是 event-time 空间差由 medium→fine 的 `0.0012067679515502204` 增至 fine→extra-fine 的 `0.0016486829760616161`，违反逐分量单调收敛规则。

因此终点固定为：

~~~text
PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN
PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN_NO_BASELINE_OR_METHOD_EVIDENCE
~~~

[S1 terminal closeout](../experiment/2026-08-28-phk-v21-s1-terminal-closeout.md)和 [terminal summary](../../outputs/runs/20260828T-phk-v21-s1-q-terminal-summary-001/summary.json)固定科学结果；[S7 package closeout](../experiment/2026-08-28-phk-v21-s7-terminal-package-closeout.md)和[最终 paper_v21 包](../../paper/paper_v21/README.md)完成英文/中文正文、通俗故事、六图、图源、表格、参考文献、补充、复现、baseline anatomy、claim matrix、reviewer-risk audit 与 package manifest。

Sharp/PF、合格 neural floor、strong raw、四臂 bottleneck、PHA-MF、field-selective KC、2×2、GPU 与 formal/OOD 均为 `NOT_REACHED`，不是负面方法结果。本地 E0-S7 授权已经消费并关闭；任何新的研究执行必须获得新的明确用户授权，并保持本 No-Go 不回写。
