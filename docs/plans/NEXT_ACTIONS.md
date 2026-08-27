# PLAN-PHK-V2-V1：强基线复现、二维相变对象与 PHK-PINN 第二版论文

- `phase_id`: `PHK_V2_COMPLETE_ORACLE_NO_GO`
- `lifecycle_state`: `COMPLETED`
- `blocker_id`: `NONE`
- `claim_status`: `PHK_V2_ORACLE_NO_GO_EVENT_CONTRACT_AND_CONTROL_EXECUTION_FAILURE_NO_PINN_METHOD_EVIDENCE`
- `authorization_state`: `PHK_V2_EXECUTION_AND_CLOSEOUT_CONSUMED_CLOSED`
- `authorization_package`: `S0_TO_S7_LOCAL_RESEARCH_AND_V2_MANUSCRIPT_CONSUMED`
- `plan_status`: `COMPLETED_BOUNDARY_PRESERVING_ORACLE_NO_GO`
- `object_selection_status`: `PHK_REDUCED_WALL_CELL_2D_V1_FROZEN_ORACLE_NO_GO`
- `method_selection_status`: `NOT_ENTERED_ORACLE_GATE_NO_GO`
- `current_stage`: `COMPLETE`
- `next_research_execution_authorized`: `false`
- `supersedes`: `GOAL_PAPER_ONE_SHOT_V1_COMPLETE_AUTHORIZATION_SEMANTICS_ONLY`
- `preserves`: `ALL_PRIOR_NO_GO_FAILED_INTENTS_AND_V1_MANUSCRIPT`
- `source_plan_sha256`: `3A178D7F98D4333B1AB76AC226A7816209053525D6477A37AF2DAD47A85F3C70`
- `effective_date`: `2026-08-27`

## 0. S2 终局裁决与当前唯一剩余工作

本计划的 S2 Oracle Gate 已按预注册停止条件终止正向方法路线。terminal run `20260827T-phk-v2-s2-q-terminal-summary` 固定 `PHK_V2_ORACLE_NO_GO_EVENT_CONTRACT_AND_CONTROL_EXECUTION_FAILURE`：intents 1–8 完成，intent 9 以 `PHK phase Newton line search reached its frozen minimum step` 失败并消费，intents 10–12 `NOT_REACHED`。nominal coarse/medium/fine/half-dt/replay 运行通过数值 hard guards，exact replay 六分量全为零，但第一周期 recovery 仅约 `0.22–0.24`，第二周期没有新的阈值上穿，cycle-peak drift 约 `1.41–1.59`，不满足两周期 event/recovery 合同。

因此没有 neural floor，S3–S6 的 strong raw、PHA-MF、KC、组合、GPU、formal 和 OOD 均未进入。S7 已交付 [benchmark/numerical-limits V2 完整包](../../paper_v2/README.md)：英文/中文正文、通俗故事、六幅双格式图、图源 CSV、最终表格/参考文献、baseline anatomy cards、补充材料、复现说明与 claim–evidence 自检。下文第 1–10 节保留为预结果冻结合同和历史执行边界，不再授权任何新科学计算。

## 1. 用户目标与授权解释

用户要求沿用《后续研究总规划》，全面剖析并复现相关 PINN 工作，提取真实创新与方法模块，识别局限和可改空间，迁移到相变器件领域，从可行性开始分层验证，在强 baseline 上进行有界、可归因的组合与改进，最终交付重要指标不劣于最强合格 baseline、至少一个预声明主指标实质改善的 PHK-PINN 组合和第二版论文初稿。

本文件将该要求作为新的独立研究执行合同。S0 通过后，Agent 可在本文件预算与门禁内自动继续 S1–S7，不需逐阶段再次申请；普通复现失败、数值失败、训练失败或方法 No-Go 按第 8 节切换，不以降低门槛或结果导向救援换取正面结论。

本授权仅覆盖项目内有界来源研究、开放代码的固定版本审计与隔离复现、clean-room 实现、CPU 求解、本地可用 GPU 训练、sealed formal、本地图表统计和第二版论文/补充/复现材料。它不授权付费或云端计算、凭据披露、作者联系、投稿、外部上传、Git push/PR/release 或破坏性机器改动。

## 2. 不可改写的既有边界

- [GOAL-PAPER-ONE-SHOT-V1](../../archive/2026-08-27-goal-paper-one-shot-v1-complete.md)保持完成态；其 `SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO`、Q0 守卫、QN 失败、论文和复现包不回写。
- Q-POP/KC/PHA、HFO、TaOₓ、Package A 与其他历史 No-Go 均保留原作用域。新路线不得把旧实现烟测、旧 event、旧 PHA/KC 代码存在性或旧负面结果当成 PHK-V2 的 oracle、event 或方法证据。
- 第一版论文继续作为 reference-solver qualification / failure-preserving stop 稿。第二版是独立正向路线；若正向门失败，只能交付对应证据等级的限制/负向 V2 稿，不能把未运行模块拼接到 V1 结果中。
- 新对象固定为透明、literature-inspired 的 reduced 2D electrothermal phase-field benchmark；不得称为 Miquel/GGST 作者模型重放、实验校准材料、真实器件验证或开放作者 oracle。

## 3. R0 已固定的一手来源与 baseline 身份

R0 结论以[一手来源与 baseline 审查](../references/2026-08-27-phk-pinn-primary-source-baseline-audit.md)为准。它是来源证据，不是复现或方法结果。

### 3.1 必须分开的身份

1. `SHARP_PINNS_PAPER_REPLICATION_V1`
   - phase-field domain anchor；
   - 只包含论文明确声明的 staggered AC/CH、RFF、modified MLP、hard output constraint 与 gradient-norm weighting；
   - 不把 causal weighting、RAR 或当前仓库长预算静默并入论文身份。
2. `SHARP_PINNS_REPO_RECIPE_4B7029E`
   - 官方仓库固定 SHA `4b7029e3e1e0b82482d245ba12e3ec0945d87ed9`；
   - causal/RAR/长 epoch 配置作为独立 best-method recipe；
   - GPL-3.0，只能隔离运行或按论文公式 clean-room 重实现，不能把源码直接并入主库。
3. `PF_PINNS_SUPPORT_COMPARATOR_A25F75B`
   - 用于 random-batch NTK、界面采样与 RAR；
   - GPL-3.0，固定支持型 comparator 身份，不与固定 support 的架构归因混用。
4. `JAXPI2_ADAPTIVE_PSEUDOTIME_77A5C13`
   - Apache-2.0 仓库固定 SHA `77a5c1315a056388271822c35ad512a5a192b60d`；
   - 作为 mandatory general strong control，检验 KC 是否只是通用 continuation/优化替代品。
5. `PIRATENET_PAPER_SPEC_CONTROL`
   - 只采用公开论文公式与报告身份；原 jaxpi 代码为 Penn 定制非营利研究许可且限制再分发，不进入公开主库。
6. `CAUSALITY_RBAR_PAPER_SPEC_ONLY`
   - 作者代码链接在 R0 核验时为 404；只做论文规格的 clean-room 控制或背景，不声称官方代码复现。
7. `MIQUEL_GGST_TOPOLOGY_INSPIRATION_ONLY`
   - 仅提供 wall-cell、电—热—相态因果链与多尺度困难的来源启发；保密成分、未公开物性和无代码关闭 exact reproduction/oracle 身份。

Sharp-PINNs 是唯一主 phase-field domain anchor，但不是唯一证据 baseline。最终方法必须与最强合格的 domain anchor、general strong anchor、容量/计算控制和机制负控比较。

## 4. 论文问题与方法身份

工作名称为 `PHK-PINN`：

> Physics-routed spatial-frequency and kinetics-time allocation for localized electrothermal phase-change dynamics.

只允许两个 load-bearing 主模块：

1. `PHA_MF_V2`：相变—热点感知的局部多频表示，回答局域界面、Joule hotspot 与窄尺度结构的空间欠分辨；
2. `FIELD_SELECTIVE_KC_V2`：只作用于相态分支的严格单调动力学时钟，使用完整一阶、二阶与混合导数 pullback，回答脉冲相变的时间刚性与快慢尺度分离。

staggered scheduling、sampling/RAR、causal training、loss balancing、continuation/pseudo-time 和 optimizer recipe 是公共强协议或控制，不与 PHA/KC 并列包装为额外创新。

### 4.1 PHA 必须防止的自确认

- 高频容量首版只投向 `T` 与 `phi`；`V` 使用共同 low/mid 表示。
- gate 只能读取训练期可得量；不得读取 oracle 或 formal 标签。
- prediction-derived phase/Joule gate 必须有 `g_min>0`，并分别比较 detach/no-detach。
- 必须包含 global MF、phase-only、Joule-only、generic learned、shuffled/wrong-location、gate-off parameter-matched、wider raw 与 extra-work raw。
- 若 PHA 只胜过 Vanilla，或收益可被 support、参数量、AD 工作或 wall time解释，则 `PHA_NO_GO`。

### 4.2 KC 必须防止的宽泛坐标变换叙事

- 仅 `phi(x,t)=phi_hat(x,tau(x,t))` 使用时钟；电势和温度保持物理时间。
- clock 严格正速率，centers 在结果前由 pulse ramp/hold/cooling 区段固定；不得根据 event time 移动。
- 所有评价回到物理时间；Laplacian 存在时必须保留完整空间二阶 pullback。
- 必须比较 identity、参数匹配 generic monotone、random fixed、all-field warp、wrong-segment、smooth-dynamics、RS-like mapping 与 adaptive pseudo-time。
- 若 adaptive pseudo-time 或 generic monotone 已解释全部收益，或 smooth/stiff case 无机制交互，则不允许 kinetics-specific 正面主张。

## 5. 深模块公共接口与 TDD 边界

首次实现前固定以下项目内接口；测试先于实现。避免复制 GPL/Penn 源码，也不把历史 Q-POP PHA 模块改名冒充 V2。

1. `pinn_pcm_sci/phk_contract.py`
   - `PhkProgramContract.load(path)`：fail-closed 读取机器合同；
   - `PhkCaseSpec`、`PhkSplitManifest` 与完整 case SHA256；
   - 只负责身份、单位、池和冻结常数，不求解、不训练。
2. `pinn_pcm_sci/phk_benchmark.py`
   - `PhkPhysicalContract`、`PhkOracleCase.solve()`、event/guard/convergence reports；
   - 闭合 `V–T–phi` 电流连续、Joule/latent heat 与 reduced phase-field；
   - 传统数值 solver 与 PINN 实现不共享残差 evaluator。
3. `pinn_pcm_sci/phk_method.py`
   - `MethodSpec` 和唯一 `build_phk_method(spec, contract)`；
   - clean-room strong raw、PHA-MF、KC、full 与匹配控制均经同一入口；
   - 复用现有 `PositiveGaussianClock`/pullback 只能通过新合同适配，不复活旧对象结论。
4. `pinn_pcm_sci/phk_evaluator.py`
   - disk-only oracle/prediction evaluator；
   - 结构主端点、界面/热点/event/device 指标、物理硬守卫和 JSON-safe 失败语义。
5. `pinn_pcm_sci/phk_runner.py`
   - intent-first、immutable run root、预算/失败计账、ledger 与 sealed pool access；
   - 只编排，不复制 solver、模型或评价逻辑。

任何现有未跟踪的 phase-field/R1 文件先视为用户资产和历史线索；只有通过来源、测试、物理身份与接口审查后才能选择性迁移，不能静默覆盖。

## 6. 对象、case 与评价的预结果冻结

### 6.1 对象身份

`PHK_REDUCED_WALL_CELL_2D_V1` 至少闭合：

\[
\nabla\!\cdot[\sigma(T,\phi)\nabla V]=0,
\]

\[
\rho c_p(T,\phi)\partial_tT+\rho L\partial_t\phi
=\nabla\!\cdot[k(T,\phi)\nabla T]+\sigma(T,\phi)|\nabla V|^2,
\]

\[
\tau_\phi(T)\partial_t\phi
=\epsilon_\phi^2\nabla^2\phi-\partial_\phi W(\phi,T).
\]

S0B 必须在第一次该对象求解前另行写入机器可读物理/数值合同，固定几何、单位、公开参数及其来源/工程身份、IC/BC/interface、波形、solver、离散、保存间隔、事件、守卫、qualification intents 和无救援规则。对象工程只可使用 manufactured、zero-drive、单步和 Q 池；看到 D/I/F 结果后不得改物理制造方法优势。

### 6.2 case pool

完整 case 身份为：

`geometry × public/synthetic material branch × initial state × full waveform × full history`。

mesh、time step、collocation point、checkpoint 和 seed 不是独立科学 case。所有 case 在方法结果前互斥冻结为：

- `Q`：oracle/守卫/事件资格化；
- `D`：backbone、超参数、checkpoint 与低预算筛选；
- `I1`：单模块 identity/attribution；
- `I2`：组合与 best-method development confirmation；
- `F_A`：完整 waveform/protocol 轴 formal；
- `F_O`：至少整族 geometry/material/initial-history 正交 holdout；
- `R`：本 GOAL 不打开的储备池。

同一器件或轨迹的相邻时空点不得跨池。formal 开封后禁止调参、换 case、补 seed、移动 margin 或重封。

### 6.3 唯一结构主端点与硬守卫

唯一结构主端点为相区时空对称差：

\[
E_\Gamma=\frac1T\int
\frac{|\Omega_{\phi,\theta}(t)\triangle\Omega_{\phi,\mathrm{ref}}(t)|}
{|\Omega_{\phi,\mathrm{ref}}(t)|+\varepsilon}\,dt,
\quad \Omega_\phi(t)=\{x:\phi(x,t)\ge0.5\}.
\]

预结果 normalizer/floor 把各误差写成 oracle-floor units。关键次级量为 interface Hausdorff、event/switching delay、recovery、hotspot peak/centroid/FWHM、terminal current trace、programmed resistance、phase volume、pulse energy 和 peak temperature。PDE、本构、latent/thermal balance、`phi` 范围、terminal-current balance、IC/BC/interface、非有限值和 event coverage 是分别计票的硬守卫，不能平均掩盖。

## 7. 分层执行链

### S0 — 来源与机器合同

- R0 一手来源审查已完成；不构成可运行性或方法证据。
- 完成本文件、ADR、机器 program contract 和对象 numerical contract。
- 记录本机环境；本地 GPU 不存在时只启动 CPU 可行阶段，不转付费/云端。

### S1 — 原域 reproduction

- `SHARP_PINNS_PAPER_REPLICATION_V1`：至少一个低成本 2D 原域 case，分离 paper identity 与 repo recipe；
- PF-PINNs 至少一个低成本官方 case；
- jaxpi2 至少一个 CPU 可行 smoke；
- 每项记录 source SHA、license、environment、oracle、seed、预算、失败与差异。

官方 smoke 只证明可执行；R2 至少复现一个预声明主图、主指标或方法排序。若固定环境不兼容，保留失败并进入 paper-spec clean-room 路线，不无界修依赖。

### S2 — 机制 benchmark 与 oracle engineering

- 1D Stefan/stiff Allen–Cahn：分离 frequency、sampling 与 stiffness；
- 2D localized-heater difficulty map：预冻结 `hotspot width × interface width`；
- wall-cell 只在 Q 池完成 manufactured、zero-drive、守恒、空间/时间收敛、independent replay、event stability 与 thermal/Joule effect。

Oracle Gate 要求局域、可解析、可重复事件；空间/时间/replay floors 可估；Joule/thermal coupling 效应超越联合不确定性。整域瞬时翻转、事件低于保存分辨率、收敛失败或 event 对网格/阈值不稳定均为 `ORACLE_NO_GO`。

### S3 — strong raw

先对不超过 12 个公共候选做 fractional search：低预算 3 seeds、successive halving、最多 2 个高预算候选。候选只来自有界层数/宽度、modified MLP 或 clean-room PirateNet-style、raw/RFF/anisotropic RFF、固定/gradient-norm/mini-NTK、full/causal、fixed/RAR 与 Adam→deterministic L-BFGS。

Sharp-domain raw 与 jaxpi2/general strong raw 均进入候选。baseline 获得与 proposed 相同或更多调参预算。Strong Raw Gate 要求在合格 event case 上形成正确事件、全部硬守卫通过，并留有稳定非地板误差；事件都无法形成时不允许直接比较 PHA/KC。

### S4 — 单模块 attribution

固定 support、精度、loss、seed schedule、参数/计算预算，依次比较：

- `A0` 最强合格 raw；
- `A1` global MF；
- `A2` PHA-MF；
- `A3` KC；
- `A5` wider raw；
- `A6` extra-work raw；
- PHA/KC 第 4 节全部 kill controls。

只打开 `I1` 一次。单模块必须在预声明困难 case 上相对每个承重 control 有稳定增量，且重要次级端点非劣；失败即冻结该模块 No-Go，不用组合掩盖 standalone 失败。

### S5 — 组合与 best-method

只有两个 standalone 均通过才运行 `A4=A0+PHA+KC`。打开 `I2` 前冻结 full、best standalone、adaptive pseudo-time、PF/RBAR-style sampling 和 common-sampling 身份。

full 必须优于最强 standalone，或通过预声明的正交交互检验；wider/extra-work、adaptive pseudo-time、generic clock、global MF 与 sampling 不能解释全部收益。

### S6 — sealed formal

formal 每个完整 case 独立训练，seed 在 case 内聚合，不跨 case warm-start。方法臂为：PHK full、最强 domain/general baseline、开封前冻结的最强非 primary challenger。

以 paired case-level studentized bootstrap 形成区间。主端点以 oracle-floor units 计，正向 superiority margin 固定为 `+0.5 floor units`；关键次级端点 noninferiority margin 固定为 `0.5 floor units`，硬守卫必须全部通过。formal case 数从 `{8,12,16,20,24,32}` 中按 D/I 控制的最大 paired SD、至少 80% power 与剩余预算预先选择；若无可行样本量，记 `FORMAL_POWER_BUDGET_INSUFFICIENT`，不把较小运行改称 formal。

`F_A` 要求相对两条控制的主端点一侧区间下界均超过 superiority margin；`F_O` 要求相对两条控制的主端点和全部关键次级量满足 noninferiority。任何 primary formal fail 关闭正面 PHK 主张。

### S7 — V2 论文与复现包

只有实际证据决定稿件身份。交付英文/中文第二版正文、最终图表/表格、参考文献、anatomy cards、A/A′ 表、全部配置/失败运行、oracle convergence、case/seed split、gross compute、补充材料、复现说明、claim–evidence matrix 与 reviewer-risk 自检；无结果占位符。

## 8. 自动裁决与失败切换

| 失败位置 | 自动动作 |
| --- | --- |
| 官方仓库环境/代码失败 | 固定失败；转 paper-spec clean-room reproduction，不声称官方复现 |
| 开放物理合同不闭合 | 缩减为透明 synthetic reduced contract；不 source-stitch 未公开参数 |
| Oracle Gate 失败 | 停止 PINN 方法路线；交付 benchmark/numerical-limits V2 |
| Strong Raw Gate 失败 | 先关闭方法比较；交付 strong-baseline capability/limits 稿，不用 PHA/KC 救援 |
| PHA standalone 失败 | 冻结 `PHA_NO_GO`；KC 可独立继续，不允许 full 正面双模块主张 |
| KC standalone 失败 | 冻结 `KC_NO_GO`；PHA 可独立继续，不允许 full 正面双模块主张 |
| full 不优于最强 standalone | 保留最佳 standalone，第二模块只作负向消融 |
| formal superiority 失败 | sealed negative/limits manuscript |
| formal OOD noninferiority 失败 | applicability-boundary manuscript |
| GPU 不可用 | 完成 CPU R0–S2 和可行小规模训练；不得转付费/云端，GPU 阶段保持资源阻塞 |
| 预算耗尽 | 停止新增运行，以全部真实证据完成相应等级 V2 稿 |

任何失败 seed、timeout、OOM、NaN、divergence 或 hard-guard fail 均保留并计入 intent；不允许结果后换 seed/case、删失败、改 margin 或追加 open-ended rescue。

## 9. 冻结预算与计算公平

| 资源 | 上限 |
| --- | ---: |
| 新增一手来源载体 | R0 已审 8 个对象；S1 仅允许补 4 个决定性载体 |
| CPU oracle 与 reproduction | 128 core-hours |
| development GPU | 64 exclusive GPU-hours |
| sealed formal GPU | 64 exclusive GPU-hours |
| GPU 总上限 | 128 exclusive GPU-hours，仅本地实际可用设备 |
| paid/cloud compute | 0 |
| 同一正式方法 superseding rerun | 最多 1 次，仅限外部执行损坏或相关输入/实现已改变 |
| Git/external publication | 0 |

每个方法和失败 intent 记录参数量、collocation、forward、AD 工作、optimizer closure/update、wall time、CPU/GPU 型号、峰值内存/显存、gross compute、失败身份和 rerun disposition。参数量、更新数或 wall time 任一单轴都不能单独证明公平。

## 10. 正面主张的充分条件

“关键指标不低于 baseline”只是必要条件，不是论文完成条件。PHK 正面主张必须同时满足：

1. 合格 oracle、事件和 floors 已在方法训练前固定；
2. 最强 raw 能解析事件，且 baseline 调参与 proposed 公平；
3. PHA 相对 global MF、容量/计算和 wrong-gate controls 在局域高频/热点困难 case 上通过；
4. KC 相对 generic monotone、RS-like 与 adaptive pseudo-time 在 stiff case 上通过，并在 smooth control 上显示机制差异；
5. full 相对最强 standalone 有增量或预声明交互；
6. `F_A` 主端点 superiority 与 `F_O` noninferiority 同时通过；
7. 全部物理/器件硬守卫通过，增益超过 oracle floor、seed variability 与实际意义阈值；
8. 失败 case/seed 和 gross compute 全量报告；
9. claim 仅限透明 synthetic reduced electrothermal phase-field benchmark 和实际测试的 complete-case/OOD 轴，不外推到实验材料、真实器件、普适 PINN 或 SOTA。

## 11. 当前终局状态

R0 与 S0B 在任何 PHK 数值结果前完成；S1 只建立固定源码身份和模块级 CPU smoke，不建立论文指标复现。S2 已形成上述 Oracle No-Go 并关闭方法路线。S7 有边界的负结果论文与复现包已经完成；原执行授权全部消费并关闭，当前无 solver、PINN、GPU、formal 或论文扩展授权。

~~~text
CURRENT_EVIDENCE =
    R0_PRIMARY_SOURCE_AUDIT_COMPLETE
    + FIXED_SOURCE_MODULE_SMOKES_ONLY_NO_PAPER_METRIC_REPRODUCTION
    + PHK_V2_ORACLE_NO_GO_EVENT_CONTRACT_AND_CONTROL_EXECUTION_FAILURE
    + NO_STRONG_RAW_OR_PHA_OR_KC_EVIDENCE

COMPLETE =
    BOUNDARY_PRESERVING_ORACLE_NO_GO
    + V2_BENCHMARK_NUMERICAL_LIMITS_MANUSCRIPT
    + FINAL_FIGURES_TABLES_REFERENCES_SUPPLEMENT_REPRO_AND_CLAIM_AUDIT
~~~
