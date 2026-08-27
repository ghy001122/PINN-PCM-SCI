# PINN-PCM-SCI 当前研究总览与论文口径

本文件是“我们到底在研究什么”的当前单一来源。当前 [PLAN-PHK-V2-V1](docs/plans/NEXT_ACTIONS.md)已经按预注册在 Oracle Gate 形成终局 No-Go：透明 reduced 2D electrothermal phase-field wall-cell 的 manufactured 与 zero-drive 守卫通过，nominal 多分辨率、半时间步和 exact replay 运行保持数值硬守卫，但没有满足必需的两周期 recovery/event 合同；第 9 个 conductivity-feedback-off control 又在冻结 phase-Newton 最小线搜索步失败。因此当前研究只收口这一 benchmark/numerical-limits 证据，`PHA-MF-v2`、field-selective `KC-v2`、strong raw 和 formal 均未进入。

- `lifecycle_state`: `COMPLETED_PHK_V2_ORACLE_NO_GO`
- `claim_status`: `PHK_V2_ORACLE_NO_GO_EVENT_CONTRACT_AND_CONTROL_EXECUTION_FAILURE_NO_PINN_METHOD_EVIDENCE`
- `updated_at`: `2026-08-27`

## 当前研究问题

`VERIFIED`：[R0 一手来源审查](docs/references/2026-08-27-phk-pinn-primary-source-baseline-audit.md)已固定 Sharp/PF/jaxpi2/PirateNet/Causality-RBAR/phase-change heat/re-spacing/Miquel 的论文、代码与许可身份。Sharp paper identity 与 repo causal/RAR 长预算 recipe 必须分开；Sharp 是主 phase-field anchor 而非唯一 evidence baseline，jaxpi2 adaptive pseudo-time 是 KC 的 mandatory general strong/falsification control。

`SUPPORTED_INTERPRETATION`：PHK 的方法假设仍是“相变状态能否决定 PINN 在何处分配空间高频容量，以及相态分支在何处重分配动力学时间分辨率”，但本路线在该假设可被测试前停止。不得把未运行模块、代码存在性或文献启发写成正面方法贡献。

`VERIFIED`：上一 `GOAL-PAPER-ONE-SHOT-V1` 已完整归档；其 Q0、QN、`SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO` 和第一版论文保持原样。旧 PHA screen 的相同结构端点和 raw event failure 不能被新名字救援；新路线必须使用新的 event-verifiable 2D electrothermal phase-field substrate。

`VERIFIED`：[S0B freeze](docs/governance/2026-08-27-phk-v2-s0b-object-and-split-freeze.md)在首个 PHK 数值结果前固定透明无量纲 wall-cell、事件/守卫/收敛、12-intent 梯与 324 个 complete-case 候选。[S2 terminal summary](outputs/runs/20260827T-phk-v2-s2-q-terminal-summary/summary.json)记录 intents 1–8 完成、intent 9 失败并消费、intents 10–12 未到达；结果为 `PHK_V2_ORACLE_NO_GO_EVENT_CONTRACT_AND_CONTROL_EXECUTION_FAILURE`。[最终 V2 包](paper_v2/README.md)已在该边界内完成。

`UNKNOWN`：官方 baseline 论文指标在完整依赖和原预算下的复现性；strong raw、PHA-MF、KC、组合、OOD 与 formal 在任何未来合格对象上的表现。当前已有 PHK 数值资格化证据，但没有合格 oracle/event，也没有任何 PHK PINN 方法证据。

## 当前授权边界

- **当前状态**：`PHK_V2_COMPLETE_ORACLE_NO_GO / NO_PINN_METHOD_EVIDENCE / AUTHORIZATION_CONSUMED_CLOSED / NEXT_RESEARCH_EXECUTION_AUTHORIZED=false`。
- **当前可做动作**：只读查看已完成的本地 V2 benchmark/numerical-limits 论文包与既有运行；任何新科学路线需用户另行明确授权。
- **已关闭动作**：不再执行 baseline metric reproduction、PHK solver、strong raw、PHA-MF、KC、组合、GPU、formal 或 OOD；不救援 intent 9，不运行 intents 10–12。
- **永久禁止**：付费/云端计算、购买许可、凭据披露、作者联系、投稿、外部上传/发布、Git push/PR/merge/remote release、破坏性机器级改动、商业 `.mph` 再分发及直接并入 GPL/Penn 限制源码。
- **完成语义**：第二版以实际 Oracle No-Go 的证据边界交付最终正文/图表/表格/引用/补充/复现/claim audit；不能满足原正向稿要求，也不能把未运行的两个模块写成完成贡献。
- **历史边界**：V1、SYN-EDT、Q-POP、HFO、TaOₓ、Package A 与所有既有 No-Go/failed intents 均保持冻结；新路线不回写或改名复活它们。

## 当前规范术语

**SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO**：
预注册的 S0/S2 物理—数值合同在首个受驱动资格 intent 上无法完成，因此不能建立可供下游方法消费的 oracle。它只关闭该冻结合同与本 GOAL 的正向链。
_避免使用_：物理模型错误、Nernst–Planck 不可解、PINN 失败、所有数值方法失败

**Q0 zero-drive guard**：
零驱动时守恒、范围、端口、热平衡和不可变产物链的 bounded 实现检查；其事件检查按合同不适用。
_避免使用_：oracle qualified、event detected、source validation、experimental validation

**NOT_REACHED method evidence**：
上游 oracle/event 门未通过，因此 strong raw、PINN/CTH、development、OOD 与 formal 没有被运行或评价。
_避免使用_：negative PINN result、CTH underperformed、formal failed

## 历史冻结：HFO-NP-v1 合同边界

- **对象身份**：HFO-NP-v1 曾被选择为唯一规划对象，现以 `WAVEFORM_TIME_NO_GO / CURRENT_ROUTE_CLOSED / NOT_AUTHORIZED` 收口；它不是作者 COMSOL replay、开放 oracle 或实验真值，也不再是可进入 G1 的对象。
- **初态身份**：G0 必须在来源连续 CF 与精确、可合法使用的 finite-gap reset restart 中冻结一个分支。无来源 snapshot 时不得自造有限 gap。
- **协议与事件**：连续 CF 分支先 RESET 打开局部 gap，再由 SET 闭合；只有精确 reset restart 分支才可先 SET。第二周期连续携带内部态，只称 derived stress test，不称作者两周期 replay。
- **来源模型保真与热因果**：来源对齐单周期必须让可数字化端口轨迹和至少两个跨事件空位空间状态在联合不确定性内同时通过；决定 gap 拓扑或绝对时间的参数不得拟合。G0 还须闭合来源支持的 `T ->` vacancy transport 反馈，G1 用配对 thermal-feedback-off 消融证明它对连续事件或端口的作用高于数值不确定性。任一项不能闭合即停止当前电热方法论文路线。
- **协议轴与逐束接口**：G0 先冻结 `SOURCE_ANCHORED_DERIVED_WAVEFORM_SCALE_AXIS`；连续 CF 只缩放固定时长 RESET 段，exact restart 才可缩放固定时长 SET 段，其他波段与 physical time 不变。基础协议与 `±ε, ±ε/2` 五视图共享几何、初态和时空支撑，逐束独立初始化、完整隔离且不跨器件摊销；它是 bundle-conditioned case-specific multi-view PINN 接口，不是纯 amplitude/rate 因果轴或全局 operator。
- **side 必要性门**：一侧割线必须在两尺度上超过数值不确定性，并拒绝 smooth-quadratic null；连续 gap/通量与端口量须方向一致，hard connectivity 只作分支确认。原 `5×` 只保留为显著性成分。
- **方法边界**：fixed-slot SRPG 的 same-network target 不提供独立物理信息，latent slots 也不具唯一 basis/scale 语义。自由 TKF-v0 又因五视图光滑吸收反例不可辨识，TKF-CANON 的真实 kink 语义也已撤回。CTH 只是在固定来源锚点 `a0` 的规范基下被条件选定的 future FULL_PLAN 靶标；它只能主张有限容量/预算下的 hinge 归纳偏置。`SIDE+` 本身不准入，还须排除事件时间位移并通过 `FIELD_HINGE_RELEVANCE_PLUS`、逐系数物理可容许性、qualification/identity-development 角色分离、共同输出变换有效性、错结点/smooth4、`IND-5`/blind bundle 双轴效用与 novelty sufficiency，更不授权实现。
- **时间边界**：G1 不判时间瓶颈。只有未来 FP64 strong-raw 得到 `TEMPORAL+` 后，才可审查空间无关、保持散度/质量/no-flux 并按物理时间评价的 cKC-NP；准稳态温度不得称独立热松弛时钟。
- **证据门**：G0 来源合同、G1 局部事件/side 预资格、未来 development oracle、strong-raw、强基线/消融与 formal OOD 依次另批；事件合格但 `SIDE−` 只关闭 side 方法，不阻止另批 strong-raw 判定 `TEMPORAL`。任何对象/能力前门失败即停止，不自动切材料或方法模块。

当前唯一已成立的来源表述是“在预冻结的三个新增对象家族与 11 项一手载体范围内，未找到能通过旧单链 clean-room 来源合同的对象；筛选在求解前有界关闭”。`GOAL-PAPER-ONE-SHOT-V1` 已是获批执行合同，但其中任何具体对象、CTH、cKC、组合增量、`event-faithful`、真实物理 kink、世界首创、SOTA 或实验验证仍未获得科学证据，不能作为当前主张。

历史 HFO Q1–Q68 的决策路由见 [HFO Q1–Q68 决策总索引](docs/adr/research_decisions_HFO_Q1_Q68.md)。对象、side 门与方法路由见 [2026-08-24 HFO-NP-v1 对抗性审查整合](docs/references/2026-08-24-hfo-np-v1-srpg-kc-adversarial-integration.md)；ADR 0032–0039 和对应 notes 只保留可移植的训练、公平、控制与 CTH 诚实身份合同，不再定义当前对象或执行路线。

## R2 已关闭处置边界

R2 曾选择 source-pinned FerroX-derived HZO y-invariant MFIM 严格电热极化畴对象与温度动力学时钟主线。授权包 A 在来源身份门裁决 `R2_P0_SOURCE_IDENTITY_NO_GO`：固定 FerroX tree 内无 exact-revision 许可，论文所列 AMReX 短哈希无法从官方仓库当前解析；Zenodo 数据身份不能修复这两项。HZO 专属绝对动力学、完整热力学分解、目标 MFIM 热边界与可辨热效应也未闭合。

R2 B–D 从未授权，没有进入物理、事件、strong raw 或方法评价。该历史结论不构成 TKC、PINN 或严格热 HZO 的全局科学否定，也不得由 SRPG 改名重启。

## 当前 R1 处置边界

`r1-etac-derived-v1` 已在预声明的 P2 事件资格门终止。其派生物理合同、P1 来源范围和有界负结果继续保留，但 strong-raw、KC′、IRAC、六臂 pilot 与 formal 均未被评价，不能形成正面或负面方法结论。R1 失败不能被改名、调阈值或追加参数救援，也不能迁移为当前 SRPG 的方法 verdict。

## 已接受的研究设定

- **论文方向**：研究重复脉冲下空间异步局部结构相或守恒缺陷态事件引起的数值时间刚性；清晰移动前沿是关键诊断而非唯一准入形态，不主张真实 GHz 器件验证或普适解决 spectral bias。
- **物理工作域**：主体仍为二维及以上氧化物相变/忆阻器或神经形态器件，并至少闭合电—热—相态或电—热—缺陷态因果链。用户已接受以守恒氧空位/缺陷浓度作为器件内部序参量；采用该路线时必须明确称为“缺陷态忆阻器”，不得包装成结构晶相或铁电极化相变。允许更换材料、几何、接触、动力学和协议，也允许把不同来源模块组成透明的 `derived/synthetic` 对象；材料、本构、参数层级与来源必须逐项标明，不得冒充作者复现或实验真值。
- **方法角色**：研究逐案例重新训练的 PINN 求解器，而非冻结检查点的跨器件代理；PINN 损失必须包含明确的 PDE 或本构残差。
- **正向模块边界**：KC、界面感知空间表示、采样/优化、保守投影、协议编码、不确定性及其他 PINN 模块均可作为直接或适配模块进入有界组合。候选可以联合设计；被写成正向贡献的模块必须由关键消融证明增量，仅作为 supporting module 的组件不得冒充独立创新。旧失败不能被组合抹除，但可在前提、接口、任务或 claim 实质改变后重新评价。
- **证据身份**：合格公开模型输出只能作为合成数值 oracle；传统求解器、代码存在、运行完成和实验验证分别判定。

## 当前获批路线的最低对象与方法合同

- 每个候选 bundle 必须逐项登记 `A_anchor`、`A′`、`ENGINEERING`、`UNKNOWN_FATAL` 与 `UNKNOWN_BRANCHABLE`。主锚点必须闭合器件身份、二维拓扑、PDE/interface、IC/BC、绝对波形/history、端口与空间响应锚点和许可。
- 每个 bundle 最多两个模块来源；它们只可补与主锚点兼容的 transport 参数、热物性或主锚点已明确采用的本构子合同，不得补几何、必要 BC/interface、绝对协议、响应锚点或新机制。
- 优先零分支，最多一个二值非拓扑分支；第二个不确定轴或任何 `UNKNOWN_FATAL` 都拒绝候选。所有保留分支必须通过后续全部门，禁止事后删枝。
- 对象合同、来源响应、局部收敛事件和独立数值 oracle 必须先于 strong raw；任何 side、temporal、spatial 或 protocol-parameter 表示瓶颈只能由该对象上的后续证据建立。
- CTH 不因计划写入而获准；只有 `RAW_COMPETENT_ONE_BOTTLENECK_IDENTIFIED` 且瓶颈为 transport-side finite-budget representation、并通过非神经 relevance 与 novelty veto 后才可进入 development。
- 正向 development 必须包含 strong raw、SA/direct Jacobian、smooth6、wider raw、extra-work raw、wrong-knot、smooth-absolute 和 independent-per-view 控制；formal 只保留 CTH、strong raw 与最强非 CTH challenger。
- 完整 case 是统计单位，seed 仅为 case 内重复；qualification、development、formal-aligned 与 formal-orthogonal 角色互斥。实际计算公平、失败 intent 计票、物理守卫和 formal margin 在开封前冻结。
- 旧 No-Go 继续绑定旧对象、接口、case、预算和主张。旧来源事实可作为新模块线索，但不得让旧候选改名重开或抹去失败。

## R1 已冻结的证据合同（P2 已终止）

- **派生物理对象**：二维电导—Joule 热—Allen–Cahn 闭合；接触/几何不对称 `A` 与材料非均匀性 `H` 形成 A0H0、A1H0、A0H1、A1H1 四个因子单元。A1H1 是目标事件单元，其余用于因果对照。
- **目标事件**：至少两个 formation–recovery 周期，局部、部分覆盖、空间异步且随时空离散加密收敛；零驱动、能量/耗散、守恒和器件端点同时受独立 evaluator 审查。
- **方法准入**：strong raw 先裁决无瓶颈、raw 不胜任、仅时间、仅空间或双瓶颈。只有对应瓶颈存在时，KC′或 IRAC 才可进入方法投票。
- **六臂归因**：强 raw、generic monotone clock、KC′、IRAC、KC′+IRAC 和 IRAC-score shuffle 使用相同完整案例、嵌套 seed、调参机会与实际计算公平轴。
- **主端点与交互**：唯一结构主端点为 cycle-equal 相态/界面时空 symmetric difference；电热、PDE/守恒与器件端口是非劣守卫。组合交互由预注册 difference-in-differences 及完整案例置信下界裁决。
- **案例与失败**：oracle qualification、joint development、one-shot formal OOD、reserve 四池互斥；方法自身发散、超时、clock 不可容许或资源越界计入 intent-to-run，只有方法外执行损坏可原配置重放。

## 保留的 exact-KC 方法合同

以下条目解释旧 Q‑POP/来源闭合 KC 路线及其负面证据，不是当前候选生成的全局准入门。若 R1/R2/R3 选择 KC′，必须在 `FULL_DESIGN` 中逐项说明哪些合同直接保留、哪些适配、哪些不再适用。

- 先确认来源闭合二维相变对象，再冻结独立二维电—热—结构 `PhysicalContract`；决定事件空间拓扑的未知量不得用结果导向的 `A_PRIME` 适配补齐，实验观测不得进入主训练损失。
- 结构时钟由解析正速率基构造，在每个物理光滑段严格单调；空间相关时钟引起的全部一阶、二阶和混合导数按链式法则完整回拉。
- 非光滑物理断点采用分段强形式和一侧迹/跳跃合同，不在导数未定义点评价点值 PDE，也不静默平滑驱动波形。
- 结构时钟、结构序参量和其他物理时间场不共享可训练参数，不允许原始时间、驱动或动态场形成结构时钟旁路。
- 主训练不读取 Q-POP 瞬态内部场标签；稀疏内部场锚点只能作为单列 solver-assisted 消融。

## 保留的 exact-KC 评价与论文主张合同

以下有序门只约束以 standalone KC 为正向核心的 claim。当前重组路线若只建立组合交互、接口协同或 supporting-module 价值，应按 ADR 0026 的主张路由评价，不得倒推各模块独立优越。

- 方法、指标、预算和停止规则先在开发池锁定，再对完整留出案例分别训练与评价；完整案例是科学独立单位，seed 只是案例内算法重复。
- 唯一结构主端点为周期等权的结构相区时空对称差；唯一独立器件端点为与冻结驱动共轭的端口或电路状态整段轨迹误差。
- 正向结论必须依次通过结构主效应、动力学特异性、原始物理非劣和独立器件后果，并相对匹配 raw-time、一般单调及动力学错位对照显示增量。
- `NO_BOTTLENECK` 与 `RAW_INCOMPETENT_ROUTE_NO_TEST` 在 KC 入场前终止并消耗路线；进入有效 KC 比较后，`INCONCLUSIVE_BUDGET_EXHAUSTED`、`KC_SCIENTIFIC_NO_GO` 与 `KC_GO` 互斥。只有有效且有辨别力的 `KC_SCIENTIFIC_NO_GO` 可触发另行审批的 PHA 诊断。
- 当前只能陈述设计已接受、限定文献审查与 P2 事件资格的有界负结果。KC 的训练收益、物理有效性、相对基线增量、预算可行性和论文最终定位均未获得数值证据。

## 规范术语

本节同时保留当前通用术语与旧 exact-KC 术语。凡涉及“来源闭合二维对象”“VO₂ 优先”“KC 必选”“第二模块串行”或“standalone formal KC”的定义，只用于解释 ADR 0019–0025 及其旧证据；当前候选生成、派生对象和组合 claim 以 ADR 0026 与 live plan 为准。

**modular source-aligned clean-room object bundle**：
由一个主锚点来源、最多两个兼容模块来源及透明 `A′/ENGINEERING` 派生组成的 `derived/synthetic` 对象合同。主锚点负责器件拓扑、IC/BC/interface、绝对协议/history 和响应锚点；模块只补参数或本构子合同。
_避免使用_：作者原生重放、任意 source stitching、用模块补主锚点缺失的边界或协议

**主锚点来源（anchor source）**：
决定对象身份和可重放案例骨架的一手来源；必须自包含二维器件域、物理闭环、必要 IC/BC/interface、绝对协议/history、端口与空间/内部态响应锚点及许可。缺少其中任一对象决定项时，不能由模块来源代替。
_避免使用_：只给 I–V 的论文、只给材料参数的数据库、无固定协议的通用模型

**模块来源（module source）**：
在材料体系、量纲、温度/场强范围和许可上与主锚点兼容，只补明确列名 transport 参数、热物性或已知本构子函数的一手来源；不改变对象机制和拓扑。
_避免使用_：跨材料补核心动力学、补未知 BC、引入主锚点没有的机制

**UNKNOWN_FATAL / UNKNOWN_BRANCHABLE**：
`UNKNOWN_FATAL` 指无法给出可信有限范围，或决定拓扑、必要边界、绝对时间、主要本构、协议或来源对齐的缺项；直接拒绝 bundle。`UNKNOWN_BRANCHABLE` 指有来源支持、对象身份不变且可在求解前冻结为有限分支的单一非拓扑不确定性；当前最多一个二值轴，所有分支都必须通过。
_避免使用_：结果后验拟合、事后删掉困难分支、把自由校准参数称为不确定性

**evidence-complete manuscript draft**：
只有对象、oracle/event、strong-raw bottleneck、全部 development controls、sealed formal 统计与物理守卫均按预注册合同闭合后形成的本地论文初稿。并行 skeleton、pilot 图和负 evidence dossier 都不是该终点。
_避免使用_：把提纲称初稿、把 pilot 称 formal、用治理文档替代结果证据

**方法盲首个通过对象选择**：
只按来源身份/许可、二维物理闭环、响应锚点与事件可资格化概率、clean-room 重建、完整案例能力和预计 CPU 成本排序；深审前冻结候选，首个通过即锁定。CTH、hinge、PINN 或方法预试不得参与生成、排序或换对象。
_避免使用_：挑最像 hinge 的对象、跨对象择优、CTH 赢后回填对象理由

**source-aligned clean-room object**：
由可追溯的一手方程、本构、参数层级、单位、二维几何、IC/BC/界面、绝对协议/history 与来源响应锚点透明派生，并明确标记 `A/A′/ENGINEERING` 的 `derived/synthetic` 数值对象；不声称作者原生重放、实验真值或作者验证。
_避免使用_：author replay、experimental validation、无来源默认值拼接、隐藏派生改动

**CANDIDATE_NO_GO**：
对象锁定前，一个冻结候选在任一来源硬门上的有界失败；只关闭该候选并按预冻结顺序进入下一候选。
_避免使用_：整个材料族失败、组合终止、PINN 不可行

**PORTFOLIO_NO_GO**：
冻结候选全部失败，或预声明时间/一手载体/新家族预算耗尽且没有候选通过时，对当前论文路线的组合级关闭。
_避免使用_：首个候选失败即组合失败、为填满预算继续搜索

**blind off-grid identity**：
未来方法身份评价中，事先冻结且不参与 smooth6 构造、smooth-absolute 选择或方法调参的离网协议点；其完整案例与 qualification、development 和 formal 角色保持互斥。
_避免使用_：同一点既选 smooth 控制又验证 CTH、用 development 结果重选离网点

**快速推进**：
以最短路径获得有辨别力、可复现且会改变路线处置的科学 Go/No-Go；不以最快写出代码、得到首图或增加运行次数代替证据进展。
_避免使用_：先实现再找对象、最快首图、用更多尝试替代判别力

**守恒缺陷态序参量**：
由守恒输运方程演化、用于描述氧空位或相关缺陷空间分布及局部 filament/gap 事件的连续内部状态；它属于缺陷态忆阻器语义，不等同于结构晶相或铁电极化序参量。
_避免使用_：结构相变场、铁电极化、实验真值、非守恒 Allen–Cahn 序参量

**逐束协议条件化多视图 PINN**：
围绕一个基础完整案例，由基准协议与唯一轴的 `±ε, ±ε/2` 邻域协议组成、共享几何/初态/支撑并逐束独立训练的五视图 PINN 接口；不同 bundle 作为完整实体隔离，不跨器件摊销。
_避免使用_：全局神经算子、跨器件代理、随机轨迹片段、跨 bundle 共享测试信息

**连续协议条件化五视图**：
同一 bundle 的五个协议视图由连续轴参数 `p` 条件化同一组场网络，完整边界波形由 `t,p` 确定性生成；不为各视图训练独立 PINN，也不使用可学习的离散 view ID。
_避免使用_：五个独立求解器、瞬时电压即 history、categorical view embedding

**双极缺陷间隙事件**：
连续双极周期中，同一局部 filament 区域发生 gap 打开与闭合的拓扑事件；连续 CF 初态先 RESET opening 后 SET closing，精确 reset restart 才可先 SET。gap/连通性是结构主身份，端口电流或电导轨迹是独立守卫。
_避免使用_：固定为先 SET 后 RESET、任意缺陷面积变化、整域覆盖、只看峰值电流、单次 electroforming

**HFO-NP-v1 历史规划对象**：
曾以 HfO₂₋ₓ Nernst–Planck 缺陷输运、电流连续和准稳态 Joule 热为来源线索规划的二维轴对称透明派生对象；其 G0 因 absolute-time waveform contract 冲突以 `WAVEFORM_TIME_NO_GO` 冻结，当前候选筛选不得重开或改名复用。
_避免使用_：当前候选、来源原生 HfO₂ oracle、COMSOL 复现、动态热模型、实验真值

**HFO 来源模型保真门**：
一个来源对齐单周期案例的端口轨迹与至少两个跨事件空位空间状态必须在合并数字化、状态定位、离散、求解和 detector 不确定性后同时通过；不允许用结果导向物理参数拟合换取通过。
_避免使用_：单端口点、单张空间图、定性趋势复现、加权总分、校准 gap 或 mobility

**分支充分协议表示**：
由冻结初始缺陷场、整条双极波形、协议参数与绝对时间共同定义迟滞分支的案例表示；瞬时电压相同但历史不同的状态必须仍可区分，不额外引入学习式 history encoder。
_避免使用_：瞬时电压即完整协议、不可审计 latent history、跨分支混同

**条件式 side—temporal 方法路由**：
来源对象和局部事件先资格化，side 信息由零 PINN 的 TKB 判断，时间瓶颈只由未来另批 strong-raw 判断；事件合格后，`SIDE−` 不阻断 temporal 诊断，`SIDE+` 或 `TEMPORAL+` 也都只打开相应新方法 PLAN，二者均无则停止。
_避免使用_：预定 SRF/cKC 胜出、side 通过即训练、KC 救援无能力 raw、自动方法 fallback

**证据中立论文身份**：
在对象、strong-raw、方法 pilot 与 formal 裁决前，论文只以来源完整氧化物器件对象与 evidence-routed PINN 为工作身份；只有相应对象和方法通过后才采用材料或方法专名标题。
_避免使用_：将 CTH 条件式靶标写成既定主线、预定 SRF/cKC 主线、以候选方法名倒逼阳性结果

**来源锚定的固定时长波形缩放轴**：
G0 以资格化来源波形为 `a0`，只缩放一个固定时长事件段并保持其他波段、转折点和 physical time 不变；连续 CF 使用 RESET 段，exact restart 才可使用 SET 段。G1 在该 `SOURCE_ANCHORED_DERIVED_WAVEFORM_SCALE_AXIS` 上构造 `±ε, ±ε/2`，`side` 只表示沿同一派生轴的增减。
_避免使用_：纯 amplitude axis、纯 ramp-rate axis、source-native axis、同轮双轴、side 等同 polarity、时间归一化掩盖 history

**来源有界物理适配**：
来源固定方程、物理尺度、几何和边界，`A′` 只承担预声明的协议重复、邻域构造与等价数值表示，`ENGINEERING` 只承担数值控制；决定事件拓扑或绝对时间尺度的缺失物理量不能按结果校准。
_避免使用_：事件导向调参、宽参数扫描后回填合同、把物理缺口标成数值容差

**TKB 侧向信息预资格**：
在合格局部 gap 事件上，用唯一协议轴两侧割线的两尺度斜率跳跃、数值不确定性、smooth-quadratic null、连续 gap/通量和端口守卫共同判断是否存在超出光滑局部模型的信息；`5×`只可作显著性成分。
_避免使用_：`5×`即 kink、只看归一化斜率指数、硬阈值单独生产 side 信号、由训练收益倒推信息存在

**FIELD_HINGE_RELEVANCE_PLUS**：
在 `SIDE+` 与 strong-raw 瓶颈诊断之后，以训练外单一事件时间平移排除纯 time-shift 项，并要求三尺度、对齐后的连续 `c_v/J_v` 一侧响应超过联合不确定性、跨离散和 detector 稳定且与 gap mass、固定截面通量和端口方向一致的有限尺度 hinge 相关性门。它只准许审查显式 hinge 归纳偏置，不证明物理解映射不可微。
_避免使用_：真实 field kink 证书、固定时间 apparent kink、DTW、非线性时间扭曲、hard connectivity 或 I–V threshold 单独生产 hinge evidence

**fixed-slot SRPG**：
用同一网络自导 response target 对齐固定 pre-head latent slots 的历史 C17 候选；因 self-target、latent gauge 和 output-head nullspace 不可辨识，当前只允许作受控参数化诊断，不是默认主方法。
_避免使用_：独立物理监督、唯一物理 slots、已验证 side 方法

**分侧物理响应场 PINN（SRF-PINN）**：
仅在 `SIDE+`、raw 胜任且分块载荷定位支持 transport-primary 后才可进入候选梯级的物理输出方法；它优先在 `(c_v,J_v)` 中表达一侧响应，电热反馈仍由公共残差闭合，但当前没有被预选、实现或授权。
_避免使用_：SRPR-PINN、默认或优先赢家、全三块 side 改造、latent slots、SIDE+ 即方法成立

**Canonical Transport Hinge-Enriched PINN（CTH-PINN）**：
当前 GOAL 中唯一条件式 transport-side 方法靶标；它把 knot 固定在来源/qualification 锚点 `a0`，用同一联合系数网络产生单个 transport vector coefficient `h=(h_c,h_J)`，并经所有臂共享的来源兼容 `C1` 输出变换表达输运响应。它须在 `FIELD_HINGE_RELEVANCE_PLUS` 后相对 exact smooth P4、smooth6/spline、镜像错结点、独立逐协议与其他强基线通过角色分离 blind identity、双轴效用和新颖性门。它只是假设有限容量/预算下的归纳偏置，当前状态是 `CONDITIONALLY_AUTHORIZED_AFTER_GATES / NOT_ADMITTED / NOT_NOVELTY_CLEARED`。
_避免使用_：真实物理 kink 已证实、独立物理约束、结果后重定 knot、分裂 side heads、模型斜率差即真实导数 jump、五视图已辨识、SIDE+ 自动准入、标准 hinge 即算法创新

**CTH 系数级物理可容许性**：
CTH 与 smooth4 的参数相关系数必须分别满足所有协议共享的初态和协议不变边界；浓度系数在共同初态消失，blocking/no-flux 边界上的法向通量系数分别为零，不能靠不同协议组合值抵消。
_避免使用_：只验五个总视图、跨视图抵消、候选专属软 penalty

**CTH 诊断身份协议**：
与 method pilot 分离的 pre-pilot 协议；`FIELD_HINGE_RELEVANCE_PLUS` 只使用 qualification complete cases，冻结公共 base、CTH、smooth4、`h=0`、错结点、输出变换与判据后，identity 必须改用互斥的 identity-development complete cases，并把 `δ=±1/4` 只用于一次盲评价。通过只允许定稿 FULL_PLAN，不授权 pilot。
_避免使用_：同一 microview 既选方法又证明方法、身份 MVE 等同方法 pilot、microview 回流调参、identity-development 数据复用为 formal、通过即方法阳性

**CTH 新颖性与协议束效用门**：
在 bounded primary-source refresh、角色分离身份证据和双轴 Pareto 上，判断 canonical hinge 参数化是否仍留下超出标准 hinge、敏感度/参数化 PINN、对象复杂性和联合训练摊销的非循环、可检验窄主张。seen protocols 与 aggregate-compute-matched `IND-5` 比较事件/总成本，blind microviews 与零重训的 parameter-conditioned raw/smooth4 比较，`IND-7` 只核算新增协议成本；不得压成加权单分数。direct-near 等价、只剩“标准 hinge 用于 HFO”，或联合协议束在两轴均被支配，均否决方法论文。
_避免使用_：未发现 exact 即首创、HFO 对象代替算法创新、五点拟合或 `h` 热图作为新颖性、只报单次推理便宜、加权总分、治理流程作为 headline

**分块 side 载荷定位**：
在选择 side 方法前，分别审查输运、电学和热学物理输出的一侧斜率跳跃及其相对时序；只有证据表明载荷主要位于输运块时，transport-only 候选才获得设计资格。
_避免使用_：由因果故事预定 transport、SIDE+ 自动归因某一网络块、一次改造全部场

**side 方法候选梯级**：
未来 `SOURCE+ / SOURCE_MODEL_FIDELITY+ / THERMAL_CAUSALITY+ / EVENT+ / SIDE+ / RAW_COMPETENT` 后，先以 SA/Jacobian 式直接参数切线和物理输出割线控制定位 transport 表示瓶颈，再排除事件时间位移并建立 `FIELD_HINGE_RELEVANCE_PLUS`；只有这些前门成立，CTH 才进入独立 held-out identity、bundle utility 和 novelty sufficiency gate。fixed-slot latent 方法不进入正面梯级，任一门失败也不自动选择下一方法。
_避免使用_：直接实现 CTH、架构先于必要性、旧 TKF/SRPG 改名复活、field/identity/utility/novelty 失败后自动 fallback

**strong-raw 瓶颈诊断**：
在事件合格对象和完整 development 案例上，先判 raw 是否胜任与是否已达 oracle 地板，再以实际计算匹配的 temporal 和 fixed-support spatial 对照识别可行动瓶颈；它不是方法救援阶段。
_避免使用_：弱 raw 投票、只看训练 loss、SIDE 代替 TEMPORAL、空间欠分辨自动触发 PHA

**HFO 混合一阶 PINN backbone**：
所有比较臂共用的 supporting 物理表示，同时预测 `c_v, φ, T` 及空位、电流和热通量，并分别约束一阶守恒方程与通量本构；它降低自动微分阶数，但不作为 headline 创新。
_避免使用_：二阶 primal 强形式默认基线、混合形式即方法贡献、传统 solver 消元物理场

**HFO 三物理块场网络**：
混合一阶 backbone 分为输运 `(c_v, J_v)`、电学 `(φ, J_e)` 与热学 `(T, q_T)` 三个网络块；三块使用同一架构族与设计规则但参数独立，不共享可训练 trunk，只通过冻结的 PDE、本构与边界合同耦合。默认候选在无量纲坐标上用平滑 `tanh`，只有来源兼容时才使用选择性硬输出变换。
_避免使用_：万能共享 trunk、逐块架构搜索、六个完全孤立网络、方法干预同时污染全部物理块

**strong-raw 耦合模式资格**：
在方法投票前，只对 strong raw 有界比较全梯度 joint training 与优化同一完整 joint loss 的对称 block-coordinate/staggered training；唯一合格者冻结给所有方法臂，无唯一合格者时不强选。外部求解器闭合电学/准稳态热学只作 `QUASISTATIC_CLOSURE_DIAGNOSTIC`，不属于正面 PINN 方法。
_避免使用_：预定 monolithic 胜出、交替更新删除跨块残差、传统 solver 闭合冒充三块 PINN、资格赛扩成无界全排列

**选择性硬 IC/BC 合同**：
只有来源兼容且存在可审计解析变换的初态、Dirichlet 电极边界与浓度物理范围采用硬约束；复杂 no-flux、Robin 和界面条件保留为所有方法臂共用的残差与拒绝守卫。
_避免使用_：全部软约束、强行硬编码复杂通量边界、硬变换改变物理合同

**局部—全局空位守恒**：
局部混合守恒 PDE 与 no-flux 边界是主约束，所有方法臂另共享一个全局空位质量积分 penalty，并由训练外守恒 evaluator 独立拒绝；不以逐时刻精确投影掩盖局部通量错误。
_避免使用_：只验不训、投影遮蔽局部误差、守恒项仅给候选方法

**冻结尺度残差权重**：
先按来源合同无量纲化，再以透明特征尺度和不读取 oracle 的初始梯度审计冻结方程块权重；主归因轨所有方法臂共用同一块权重，best-method 轨最多单列一个不改变 IC/BC、质量、no-flux 或端口守卫权重的组内有界 pointwise 对照。
_避免使用_：等权默认、逐案手调、主归因中在线改变权重、动态降权物理守卫

**统一 FP64 两阶段优化**：
所有比较臂共用 FP64、嵌套低/高预算及固定更新数的 `Adam → deterministic second stage` 调度，不以 loss 平台或 oracle 指标在线改变切换；默认二阶段为 L-BFGS，若预检不可行须在生成正式 intent 前统一更换。
_避免使用_：按方法换优化器、oracle 早停、逐运行平台触发、预算后定、低精度结果充当正式证据

**固定分层 collocation support**：
主归因轨冻结同一分层低差异点集，覆盖内部域、全部边界/界面、预声明 gap ROI、波形转折区与周期均衡时间层；预测或残差驱动的点移动只可进入后续 best-method 轨。
_避免使用_：纯均匀随机遗漏事件区、主归因臂各自采样、adaptive gain 与方法机制混写

**确定性空间 Fourier 资格比较**：
在方法归因前只比较 raw-coordinate、参数量匹配的 wider raw 与来源尺度确定的 spatial Fourier 三种 strong-backbone 候选，冻结胜者供所有方法臂使用；时间和协议轴不作任意周期编码。
_避免使用_：Fourier 默认创新、随机或可学习频率、逐方法调频、只凭训练 loss 选编码

**BACKBONE_INDETERMINATE**：
公共 backbone 候选必须在全部预冻结 method-vote case×cycle 上通过主端点不确定性带、最坏案例、seed 稳健性与物理守卫；若候选互有胜负或不确定性带重叠而无单一 admissible winner，明确停止为不可判定，不按平均 loss、参数量或墙钟强造赢家。简洁性只可在预声明等价带内作 tie-break。
_避免使用_：平均指标选优、词典序掩盖难例、守卫失败后按速度胜出、无赢家仍进入方法投票

**累计 time-prefix temporal 对照**：
只在 temporal diagnosis 中使用从 `t=0` 开始、按冻结波形转折或周期边界扩展的嵌套时间前缀，并与累计 PDE/AD/closure 计算匹配的 full-horizon 控制比较；它不是公共 curriculum 或 headline 方法。
_避免使用_：系数 homotopy、伪初态、按 loss/event 选择前缀、归因轨默认课程学习

**组内有界 pointwise weighting 对照**：
在冻结方程块权重不变的前提下，只允许同一 residual group 内的有界、均值归一 pointwise 权重在 Adam 阶段按预声明规则变化，并在二阶段优化前冻结；它只属于 best-method 比较。
_避免使用_：跨块动态重权、守卫降权、L-BFGS 中继续变权、经验步数直接移植

**best-method 自适应采样对照**：
主归因轨通过后，最多单列一种来源透明的 residual/causal adaptive 方法，并把候选池评估、残差排序、点刷新与自动微分全部计入实际计算；固定背景 support 不能被完全替换。
_避免使用_：top-20%/30% 经验值直用、候选评估免费、adaptive 与目标机制混写

**只诊断训练遥测**：
分项残差、梯度、IC/BC、质量、no-flux、端口和事件守卫完整记录，但除预声明的实现有效性失败外不在线改变优化器、权重、support、预算或停止时点。
_避免使用_：total loss 单通道、oracle 控制训练、诊断触发临时救援

**HFO headline oracle 隔离**：
主训练只读取 PDE、本构、IC/BC 与守恒合同，独立 oracle 内部场只用于资格和评价；稀疏内部锚点最多作为方法锁定后的单列 solver-assisted 消融。
_避免使用_：半监督主方法、完整场蒸馏、oracle 标签改善冒充 PINN 增量

**gap soft-mask 主端点**：
在预冻结 gap 区域与映射上按周期等权聚合的缺陷耗尽 soft-mask 时空 symmetric difference，是 HFO 方法裁决的唯一结构主端点；硬连通、事件时间、gap 厚度、通量和端口量分别承担诊断或守卫。
_避免使用_：任意加权综合分数、terminal current 代替内部事件、多重可择优主端点

**HFO 双轨方法比较**：
主机制归因轨在所有方法间冻结相同 collocation/support 和实际计算口径；最小机制比较通过后，另设允许 causal/adaptive 策略的 best-method 轨评价实用竞争力。
_避免使用_：只做固定支撑却声称击败最强方法、只做各自最优而失去归因、两轨结果混写

**单一 load-bearing method headline**：
首篇论文最多允许一个经对象、事件、raw、瓶颈、归因与 formal 前门支持的 PINN 算法或网络机制承担主要方法主张；HFO 派生对象、证据路由和训练治理只作 supporting。CTH 的条件式选择不等于 headline 冻结，SRF、cKC-NP 或其组合也不作为默认替代。
_避免使用_：对象创新＋框架创新＋方法创新三重并列、未过门先命名主方法、模块拼盘 headline

**HFO 来源有效完整案例 OOD**：
formal 泛化只在 G0 来源合同认可的 HFO-NP-v1 有效域内，按完整几何、接触/热边界、协议或初态家族隔离，并对每个 case 独立训练；具体主轴须在来源和事件资格完成后冻结。
_避免使用_：轨迹片段拆分、跨材料泛化、冻结 operator、复用权重冒充逐案例求解

**事件保真—计算 Pareto**：
实际计算匹配下的完整事件主端点和物理守卫是主要裁决；只有其合格后，达到预冻结保真度所需的计算、墙钟、内存与自动微分代价才可作为次要 Pareto 证据。
_避免使用_：速度挽救失真、综合分数掩盖守卫失败、只报 loss 或单一墙钟

**首篇 forward-only 范围**：
当前论文路线只研究含明确 PDE/本构残差的 forward PINN 求解；逆问题、参数识别、UQ 和跨对象代理保留为后续独立路线。
_避免使用_：forward 证据不足时追加 inverse/UQ、以多任务数量包装贡献

**两阶段新颖性刷新**：
load-bearing primitive 冻结后、FULL_PLAN 定稿前进行第一次一手来源刷新并通过 novelty sufficiency gate，formal/论文主张冻结前再刷新一次；两次都只提供有界碰撞裁决，不提供世界首创或 FTO 保证。
_避免使用_：早期搜索永久有效、未发现 exact bundle 即 novelty cleared、标准 hinge 放入新对象即创新、只查标题不核机制

**load-bearing 因果准入链**：
方法候选必须闭合“strong-raw 诊断瓶颈→一个最小可训练干预→直接机制探针与 kill control→完整事件端点→物理守卫”；任一箭头不可执行时只留 parking lot。
_避免使用_：按新名字或 development 排名选方法、事后补机制故事、多个干预共用一个无法归因的结果

**单可训练机制 pilot**：
首轮目标候选只比冻结公共 base 多一个可训练 load-bearing 机制；若 `SIDE+ / TEMPORAL+` 同时成立，两腿仍须分别通过 standalone pilot，之后才能另审 2×2 交互。
_避免使用_：首轮捆绑 side＋clock、方法臂独占 training tricks、组合阳性倒推单腿优越

**两族 formal OOD**：
formal 只设一个与机制因果假设对齐的主要 HFO 完整案例家族和一个正交稳健家族，均在来源有效域内逐案例独立训练；具体轴在来源、事件和机制身份闭合后冻结。
_避免使用_：跨材料泛化、随机参数点、无界多轴 factorial、轨迹片段 OOD

**direct-near 碰撞否决**：
若刷新发现一手工作同时覆盖 load-bearing primitive、相同因果主张和可比完整事件证据，则在 pilot/formal 前停止、降格或实质收缩主张；组件碰撞转化为强基线和消融负担，不自动否决。
_避免使用_：任一组件相撞即放弃、只有 exact bundle 才算碰撞、未发现 exact 即宣称首创

**同 base＋方法增量公平**：
正面方法共享冻结 base，只增加其最小 load-bearing 机制，并同时面对真实参与输出的参数量匹配 wider-raw 与实际计算匹配 extra-work raw；额外参数、forward、自动微分、optimizer closure、墙钟和峰值内存全部记账。断开输出的 dummy module 只可作微基准。
_避免使用_：dummy 充当科学 kill control、候选独占更强 base、只匹配参数不匹配计算、故意缩小候选 base

**method-vote case 与 seed quorum**：
完整案例在看到 PINN 结果前冻结为 qualification、method-vote development 或 stress-only；`RAW_COMPETENT` 的全通过只约束 method-vote case×cycle，并须满足预声明 seed quorum。结果出现后不得把失败 case 改成 stress-only，也不得只保留成功 seed。
_避免使用_：事后改案例角色、单 seed 胜出、stress case 绑架 raw competence、失败 case 静默删除

**顺序式四臂方法 MVE**：
首轮方法 pilot 只比较 strong raw、最强直接近邻、目标候选和一个能够杀死核心机制的负控；只有该最小比较通过，才扩展更多强基线和消融。
_避免使用_：全排列起步、候选只对 raw、失败后增加方法臂救援

**证据式 superseding rerun**：
失败分为 implementation-invalid、method-specific numerical failure、shared-infrastructure failure 与 environment `BLOCKED`。正确实现下的发散、超时或越界计入方法；只有有定位证据的实现或共享基础设施缺陷，才允许同阶段同臂最多一次保持科学配置不变的替代重跑，原 intent 与失败记录必须保留。
_避免使用_：失败后换 seed/网络/预算、删除原 intent、把环境阻塞写成科学失败、无限工程救援

**无方法增量收口**：
对象事件合格但 raw 无可行动瓶颈，或所有获准候选均未超过强基线与关键负控时，保留有界负证据并关闭当前方法路线；不自动改投负面论文或消费剩余预算寻找 fallback。
_避免使用_：对象通过即成稿、剩余预算救援、自动 benchmark paper

**守恒全局动力学坐标 cKC-NP**：
仅在未来 `TEMPORAL+` 后可审查的端点归一、空间无关、有界正速率训练坐标；它只回拉输运块的时间累积项，电学、热学、驱动波形、视图配对和全部事件评价保持物理时间，并保持散度、总质量与 no-flux。
_避免使用_：空间/状态/温度局部时钟、`V(τ,p)`、electrothermal clock、可训练 mobility 与 clock 混淆

**透明派生对象**：
由一个或多个有来源模块经明确的材料、几何、边界、物理闭合或接口适配形成的新数值对象；每项输入必须标为 `A`、`A′` 或 `ENGINEERING`，整体必须标为 `derived/synthetic`，不得冒充作者复现或实验真值。
_避免使用_：同源作者 oracle、实验验证、隐藏工程参数

**正向贡献模块与 supporting module**：
正向贡献模块必须由强基线和关键消融证明预声明增量；supporting module 可以进入完整方法和论文故事，但只能主张其真实的支撑、接口或验证角色。
_避免使用_：组合后倒推单模块优越、支持组件冒充独立创新

**组合交互主张**：
当只有完整组合相对单模块建立增量时，只主张功能组合、接口协同或 composability；不得把组合效应拆写成各组件分别优越。
_避免使用_：双模块各自 SOTA、无消融的协同结论

### 论文范围

**抗高频（首篇论文）**：
PINN 求解器应对重复脉冲、形成—恢复时间尺度分离和空间异步局部结构相事件所引起的数值时间刚性的能力。它不等同于真实 MHz–GHz 器件物理有效性，也不表示普遍解决高空间频率问题。
_避免使用_：GHz 器件验证、普适高频鲁棒性、谱偏置解决方案

**空间异步局部结构相事件**：
在同一脉冲协议内，不同空间位置以可辨时序发生局部、部分覆盖且可恢复的结构相变化；清晰连续前沿可以出现，但不是定义该事件的必要条件。
_避免使用_：任意跨阈值事件、整域同步翻转、必须呈现锐利移动界面的相变

**来源闭合二维相变对象**：
可引用原始论文、固定版本且许可明确的公开实现、完整二维几何/材料/本构/接触/边界/驱动/状态语义及可重生成参考输出共同闭合的物理对象；任何决定事件拓扑的因果量缺失即不合格。
_避免使用_：论文启发的自由拼装 substrate、无许可代码、结果导向 A′ benchmark

**VO₂ 优先候选组合**：
一个活动 VO₂ 对象与最多两个按同一否决顺序冻结的后备对象；三者不得并行执行，只有有界 VO₂ 来源扫描无合格活动对象并另获批准后，后备范围才可扩到相近氧化物体系。
_避免使用_：多材料并行试错、结果后重排后备、降低来源门补足名额

**有界 VO₂ 来源扫描**：
以预声明查询族寻找来源闭合对象，并在得到三个合格候选或查询族耗尽时停止的只读候选审查；一个合格活动对象足以收口，后备不足不能通过降低来源门补足。
_避免使用_：无界文献搜索、凑足三个候选、零候选时自动扩材料

**冻结候选顺序**：
首次科学运行前锁定的一个活动对象与至多两个后备对象的次序；只有新的来源事实触发既定否决条件时才允许更改。
_避免使用_：根据 KC 结果重排、事后挑容易对象、动态候选池

**语义保持来源适配**：
不改变来源物理对象的环境迁移、格式适配、无量纲化或经等价性核验的离散修改；改变几何、接触、驱动、动力学或本构会产生新的派生物理对象。
_避免使用_：小幅物理修补、同一对象内调几何、未声明 A′

**热主导 VO₂ 工作域**：
首篇论文限定的二维、低至中等场 VO₂ 器件范围，其中电—热—相态因果链以可复现的 Q-POP 公开模型为物理起点。尚未闭合验证的高场缺陷输运、Poole–Frenkel 导电和完整电—力耦合不属于该工作域。
_避免使用_：通用 VO₂ 物理、高场 VO₂ oracle、实验 VO₂ 数据

**逐案 PINN 求解器**：
以含明确 PDE 或本构残差的 PINN 为核心，对每个完整案例独立求解物理场的数值方法。它不是共享冻结权重的跨器件代理或神经算子。
_避免使用_：器件代理、零样本器件预测器、算子学习研究

### 物理与方法合同

**经核对的 Q-POP 物理合同**：
在固定 Q-POP 运行模式上完成论文、模型文档与可执行代码核对后，冻结的独立未知量、方程、参数、初边值条件和外电路定义。论文描述或代码行为均不能未经核对而单独成为该合同。
_避免使用_：代码即物理真理、文档中的全部扩展物理、未经验证的三场 Q-POP

**场选择性结构动力学时钟**：
仅为结构序参量 \(\eta\) 指定局部单调时间表示，而其他独立物理状态仍以物理时间表示的动力学时钟机制。
_避免使用_：全场共享时钟、多时钟系统

**时钟旁路**：
使 \(\eta\) 能在既定结构时钟之外独立随物理时间或驱动协议变化的通路；存在该通路时，结构时钟不再是可唯一归因的时间表示。
_避免使用_：辅助时间输入、协议捷径

**构造单调结构时钟**：
在 PhysicalContract 确定的每个光滑时间段内由正速率解析积分构造、并按断点合同连续衔接的结构时间坐标；对每个固定 \(\mathbf x\)，它随物理时间严格递增，并可逆到自身的弯曲像域。零残差斜率界和有限残差偏差属于条件性机制命题，不推出普适收敛、条件数或全局误差改善。
_避免使用_：惩罚单调时钟、固定矩形时钟域、无条件斜率界、普适收敛保证

**尺度化时钟速率下限**：
无量纲结构时钟速率的严格正下限，其数值由预声明的尺度与条件性协议冻结，而不是由浮点类型或机器精度决定。它是方法参数，不是材料的最小相变速率。
_避免使用_：机器精度时钟下限、物理最小相变速率

**论文优先的可替换模块路线**：
不可约目标是取得可归因、可复现且相对强基线具有实质算法增量的 PINN 论文证据；KC′、空间模块与双模块交互都是待裁决候选，而不是预先保证的论文标题。单模块阳性可以独立路由，只有预声明交互机制和匹配消融成立时才主张组合创新。
_避免使用_：KC 必须成功、双模块预定成功、模块堆叠、失败后的组合救援

**候选研究路线**：
一个物理对象及其冻结的“对象/来源资格化 → 强 raw → 方法 pilot → 条件式 formal”证据链；它必须单独获批并在达到预声明终点时收口，但不消耗全局计数槽位。
_避免使用_：单次运行、单个 seed、同一对象重命名、无界调参分支

**逐路线证据止损**：
项目不设跨路线的固定研究次数上限；每条路线分别冻结论文去向、实际计算预算、证据门和停止条件，收口后只有在前提、接口或证据价值实质变化且再次获批时才能启动新路线。
_避免使用_：剩余路线槽位、累计失败次数自动裁决、无界救援、改名后延长旧路线

**界面—残差自适应配点（IRAC）**：
以 detached、归一化的预测界面信号和 PDE 残差信号选择空间配点的候选模块；它默认是 supporting module，只有相对 uniform/raw 与 score-shuffle 负控获得预声明增量且 prior-art 未实质碰撞时，才可成为正向方法贡献。
_避免使用_：oracle 标签采样、复杂采样天然创新、无 shuffle 的界面因果主张

**R1 六臂 development 比较**：
在同一基础网络族和实际计算公平轴下，对强 raw、generic monotone clock、KC′、IRAC、KC′+IRAC 与 IRAC-score shuffle 进行的开发期机制裁决；它不是 formal OOD，也不能单独产生最终论文结论。
_避免使用_：pilot formal、最佳 seed 比较、失败臂剔除

**收敛的两周期空间事件**：
至少两个重复周期均有形成与恢复，空间时序差高于离散分辨率，相变局部且未覆盖整域，并且核心事件诊断随离散加密收敛的结构相事件；它允许多点成核且不要求单一连续前沿。
_避免使用_：单周期偶然翻转、整域同步翻转、网格噪声前沿

**两级 strong-raw 能力门**：
在结果出现前冻结的强直接 raw 基线与一次预算匹配升级；达到误差地板时处置为 `NO_BOTTLENECK`，两级均不能解析合格事件时处置为 `RAW_INCOMPETENT_ROUTE_NO_TEST`，二者都不允许 KC 入场。
_避免使用_：无限换网络、raw 不胜任仍比较 KC、事后挖掘更难案例

**模块独立通过**：
候选模块在合格 oracle、胜任的强 raw 和互斥开发案例上，超过匹配基线与关键消融且保持原物理非劣的准入状态；它只授权组合开发，不等于论文主方法已经成立。
_避免使用_：代码已实现即通过、单指标胜出、组合后倒推单模块有效

**组合增量通过**：
在实际计算量匹配的 raw、KC、第二模块与 KC+第二模块比较中，组合超过最佳单模块，或实现预声明且可独立裁决的不同功能增量；仅持平时保留更简单的单模块。
_避免使用_：平均排名更好、事后挑选功能、复杂度本身即贡献

**standalone formal KC 突破**：
独立 KC 在未触碰 formal 完整案例上获得 `KC_GO` 的路线结果；资格化、raw 通过、正向 pilot 或组合开发均不属于突破。
_避免使用_：pilot 突破、组合救援突破、部分门通过

**实际计算匹配**：
在相同案例、seed、基础网络族和调参机会下，将 KC 的额外导数与时钟开销计入主要预算公平轴，并同时报告参数量、更新数和墙钟时间。
_避免使用_：只匹配参数量、只匹配更新数、KC 免费额外计算

**第二模块串行准入**：
KC 先在开发池独立通过并显露不同剩余瓶颈，第二模块再独立通过开发门，随后 raw、KC、第二模块与组合共同进入同一未触碰 formal 池；任一单模块失败都会取消组合资格。
_避免使用_：联合起步、formal 后补模块、失败模块捆绑

**完整回拉等价性**：
在每个光滑时间段内，将空间相关结构时钟引起的一阶、二阶及混合导数全部按链式法则回拉，使 KC 表示上的原物理残差与冻结 Q-POP 方程保持代数等价。它不表示增强后的时钟目标、有限网络函数类、优化过程、弱解或条件数等价。
_避免使用_：时钟修改 PDE、方程松弛、优化等价、已证明条件数改善

**分段强形式合同**：
以 PhysicalContract 中使方程所需导数失去光滑性的物理断点划分开区间；区间内评价强形式残差，断点处只施加由相应 PDE、ODE 或 DAE 积分平衡导出的一侧迹及连续或跳跃条件。它不静默平滑波形，也不预设所有状态连续。
_避免使用_：跳点点值 PDE、统一连续条件、未标注脉冲平滑

### 评价范围

**合格公开数值 oracle**：
来源闭合公开对象在冻结物理合同上通过独立复现、离散收敛、守恒和数量级核验后形成的合成数值参考。它不是实验真值，实验资料只能支持外部一致性判断。
_避免使用_：作者输出即 oracle、实验 ground truth、已验证器件数据

**独立 oracle 资格化**：
作者代码生成参考输出，但方程—代码核对、事件/守恒 evaluator、时空离散审计和 PINN 残差实现保持独立的资格过程；只有实质不一致才要求第二套完整 solver。
_避免使用_：作者代码自证正确、默认重写完整 solver、共享 evaluator

**案例角色四分**：
完整案例分为互斥的来源复现/资格化、方法开发、未触碰 formal 和未触碰储备角色；公开参考 case 不得进入 formal，同一实体的时间片不得跨角色。
_避免使用_：参考 case 兼任 formal、随机时空点拆分、formal 回流开发

**RAW_INCOMPETENT_ROUTE_NO_TEST**：
合格 oracle 具有目标事件，但冻结的两级 strong-raw 均不能胜任事件解析时的路线终止状态；该路线已消耗，却没有产生可裁决 KC 的有效基线。
_避免使用_：KC 失败、继续换网络、无效运行不计数

**动态电子序参量约化 oracle**：
保留二维电—热—结构因果链，并将 Q-POP 的结构序参量 η 与电子序参量 μ 都作为独立动力学状态，同时删除瞬态载流子和 Poisson 空间电荷的有界合成模型。它不是完整 Q-POP，也不因工程可运行而自动成为合格 oracle。
_避免使用_：四场 Q-POP、完整 Q-POP、实验 VO₂ 真值

**Q‑POP 热力学对齐相场 benchmark**：
保留 Q‑POP 几何、低至中等场工作域、稳定极小值自由能差和高低相本构范围，并以 φ、T、η 三个独立场闭合电—热—Allen–Cahn 因果链的二维合成数值 benchmark。它用于辨别结构时钟数值机制，不是完整 Q‑POP、实验 VO₂ 真值或真实器件替代物。
_避免使用_：三场 Q‑POP、合格 Q‑POP oracle、VO₂ 实验 benchmark

**电热倾斜相场机制 benchmark**：
以名义相标签 `m=-1`（绝缘）和 `m=+1`（金属）、有限实数结构坐标、二维电热反馈和温度倾斜双稳态 Allen–Cahn 动力学构成的合成数值 benchmark；稳定根可略超出名义标签，`m` 可显式映射到来源结构量，但不冒充 Q‑POP 原始 η，也不替代完整 VO₂ 物理。
_避免使用_：Q‑POP η、三场 VO₂ oracle、实验相变轨迹

**初值精确结构残差表示**：
把冻结结构初值写入解析基项，并令可训练结构修正显式乘以物理时间，使 raw、identity-clock 与 KC 在 `t=0` 严格满足同一 η 初值；所有附加频率修正也必须在初始时刻消失。该表示消除初值拟合自由度，但不保证事件解析、训练收敛或方法增益。
_避免使用_：硬编码结构轨迹、初值精确即全程精确、结构事件保证

**无瞬态内部场监督的主训练**：
主训练不读取 Q-POP 瞬态内部场标签，只使用物理方程、本构、初边值、界面及电路合同；稀疏内部场锚点只能构成单列的 solver-assisted 消融。
_避免使用_：data-free PINN、oracle-free PINN、Q-POP 辅助主训练

**分层正向证据合同**：
KC 只有在预算匹配下同时满足预声明的结构主效应、动力学特异性、原始物理非劣、完整案例与种子稳健性，以及独立器件后果时，才可形成正向结论。具体阈值在正式投票实验前另行冻结。
_避免使用_：平均场误差通过、墙钟时间通过、单指标胜出

**动力学错位负控**：
将当前预测产生的结构动力学速率目标经预声明、确定性且相对于实际采样测度保持边际分布的时空错位，保留可比光滑度而破坏其与局部结构事件的对齐，用于检验动力学特异性且不读取 Q-POP 瞬态内部场标签。
_避免使用_：\(K_\eta\) 变号负控、白噪声时钟、oracle 错位时钟

**NO_BOTTLENECK**：
在有效且预算冻结的基准审计中，raw-time 强基线已经达到预声明的 oracle、离散或实用误差地板，因而案例不能辨别 KC 的目标增益。它既不是 KC 成功或失败，也不触发 PHA-MF。
_避免使用_：KC 已解决、KC 无效、自动转入 PHA

**INCONCLUSIVE_BUDGET_EXHAUSTED**：
有效性门已通过，但冻结预算内的精度、样本量、方差或主指标一致性不足以裁决预声明机制条件的终止状态。它不支持正面或负面机制主张，不授权开放式调参，也不触发 PHA-MF。
_避免使用_：部分成功、默认重跑、PHA 触发

**方法锁定后求解器稳健性**：
先在开发案例上锁定方法合同，再对每个留出的完整案例独立训练并评价，且不得按测试案例重新选择方法。该概念衡量求解方法的稳健性，不表示检查点迁移。
_避免使用_：冻结检查点 zero-shot OOD、检查点泛化、跨器件迁移

**完整案例**：
不可拆分的器件级评价实体，包括其几何、材料设定、脉冲协议和整条轨迹。同一完整案例的点或相邻时间窗不得跨开发集与留出评价集拆分。
_避免使用_：随机时空点拆分、点级 OOD

**结构轨迹主端点**：
在预声明协议窗口内、按脉冲周期等权聚合的结构相区时空对称差；它是正式结构裁决的唯一主端点，事件时间、前沿距离和拓扑错误属于关键次级诊断。
_避免使用_：多重结构主指标、事后最佳结构指标、平均 \(\eta\) 场误差主端点

**共轭端口器件端点**：
与冻结驱动共轭的外部端口或电路状态整段轨迹误差；它是独立于内部结构相区的唯一器件后果端点，具体通道由冻结外电路合同决定。
_避免使用_：内部相态器件端点、事后最佳器件量、逐轨迹峰值归一化

**案例角色隔离**：
完整案例在打开正式结果前分入互斥的开发池、KC 正式池和未触碰的 PHA 储备池；方法、指标、预算和停止合同只能在开发池冻结，路线之间不得复用正式或储备信息。
_避免使用_：时间窗拆分、结果后筛选案例、KC 与 PHA 共用测试池

**科学独立案例单位**：
完整案例是跨物理条件推断的科学独立单位，随机种子是案例内嵌套的算法重复；时空点、周期和种子均不能冒充独立科学样本。
_避免使用_：case×seed 独立样本、点级样本量、最佳种子证据

**冻结预算制度**：
先冻结日历上限、阶段止损和禁止结果导向追加的规则，再依据有界吞吐与方差 pilot、于打开正式案例前冻结调参与正式运行额度；实际计算量是主要公平轴。
_避免使用_：历史预算直接继承、结果导向追加预算、点数或更新数单轴公平

**隔离的结构时钟计算图**：
结构时钟、结构序参量表示和物理时间多场表示具有互不共享的可训练参数，且不存在由共享表征、动态场或驱动协议进入结构时钟路径的前向时间旁路；物理耦合只由冻结方程合同表达。
_避免使用_：共享时间 trunk、detach 后的时间旁路、动态场捷径

**结构时钟可容许性**：
除时间纤维严格单调外，空间相关时钟还必须满足预声明的空间正则性、坐标条件和回拉放大守卫；正确实现下越过守卫属于方法失败，而不是可剔除的运行。
_避免使用_：单调即良态、结果后平滑、导数裁剪救援

**正式运行**：
方法、案例、种子、预算、停止和评价合同均已锁定并在启动前登记的确认性运行；只有可归因于方法外部的执行损坏才能按原配置精确重放。
_避免使用_：失败后换种子、只保留完成运行、测试集救援

**有序确认性裁决链**：
按结构主效应、动力学特异性、原始物理非劣和独立器件后果顺序组成的逻辑合取门；所有必要门同时通过才构成 `KC_GO`，部分通过不能降格包装为正面 KC 结论。
_避免使用_：多指标择优、部分成功主张、事后缩窄正面结论

## 决策与证据来源

- 当前 HFO Q1–Q68 决策总索引：[docs/adr/research_decisions_HFO_Q1_Q68.md](docs/adr/research_decisions_HFO_Q1_Q68.md)
- 历史 KC-PINN Q1–Q23 决策表：[docs/adr/research_decisions_Q1_Q23.md](docs/adr/research_decisions_Q1_Q23.md)
- 当前 R1 Q1–Q24 决策合同：[docs/adr/research_decisions_R1_FULL_DESIGN_GRILL_2026-08-22.md](docs/adr/research_decisions_R1_FULL_DESIGN_GRILL_2026-08-22.md)
- 当前 R1 四因子、六臂与四池证据设计：[ADR 0028](docs/adr/0028-freeze-r1-factorial-six-arm-and-four-pool-design.md)
- 当前目标事件与来源闭合要求：[ADR 0019](docs/adr/0019-target-spatially-asynchronous-events-on-a-source-complete-object.md)
- 全局路线次数上限已撤销、逐路线证据止损保留：[ADR 0027](docs/adr/0027-remove-the-fixed-count-cap-on-future-research-routes.md)
- 第二模块独立准入与组合增量：[ADR 0021](docs/adr/0021-admit-a-second-positive-module-only-after-independent-and-combination-gates.md)
- 来源闭合一票否决与 VO₂ 优先候选组合：[ADR 0022](docs/adr/0022-use-a-veto-first-vo2-source-complete-candidate-portfolio.md)
- 收敛事件与两级 strong-raw 准入：[ADR 0023](docs/adr/0023-require-a-converged-event-and-bounded-strong-raw-gate-before-kc.md)
- 来源候选冻结、oracle 独立性与案例角色：[ADR 0024](docs/adr/0024-freeze-the-source-shortlist-and-isolate-oracle-case-roles.md)
- standalone formal KC 突破与第二模块顺序：[ADR 0025](docs/adr/0025-require-standalone-formal-kc-go-before-claiming-a-breakthrough.md)
- 透明派生对象、材料/网络迁移与方法重组：[ADR 0026](docs/adr/0026-allow-transparent-derived-objects-and-bounded-method-recombination.md)
- HFO-NP-v1 规划对象与初始证据路由：[ADR 0030](docs/adr/0030-select-hfo-np-v1-and-evidence-routed-kc-srpg.md)
- HFO 来源初态、TKB 与条件式方法路由修订：[ADR 0031](docs/adr/0031-revise-hfo-source-side-gate-and-method-routing.md)
- Q30–Q36 side 方法延后选择与 PINN 训练比较边界：[ADR 0032](docs/adr/0032-defer-side-method-and-bound-hfo-pinn-training-comparators.md)
- Q37–Q43 耦合模式资格、strong-raw 公平与失败裁决：[ADR 0033](docs/adr/0033-qualify-coupling-mode-and-freeze-strong-raw-adjudication.md)
- Q44–Q48 单一方法主张、HFO 域内 forward 外推与新颖性刷新：[ADR 0034](docs/adr/0034-freeze-single-method-headline-and-hfo-scoped-forward-claim.md)
- Q49–Q53 因果单机制 pilot、两族 formal OOD 与碰撞否决：[ADR 0035](docs/adr/0035-freeze-causal-single-primitive-pilot-and-collision-veto.md)
- TKF-CANON 条件式方法靶标与 diagnostic-identity 前门：[ADR 0036](docs/adr/0036-select-canonical-tkf-as-diagnostic-gated-full-plan-target.md)
- Q54–Q58 波形轴、来源保真、field kink、身份与新颖性前门：[ADR 0037](docs/adr/0037-require-waveform-fidelity-field-kink-identity-and-novelty-gates.md)
- Q59–Q63 CTH 有限预算语义、热因果、系数可容许性、力学止损与协议束效用：[ADR 0038](docs/adr/0038-reframe-tkf-as-cth-and-require-thermal-causality-admissibility-and-utility.md)
- Q64–Q68 CTH 身份角色分离、来源锚点、联合向量、输出变换与双轴效用：[ADR 0039](docs/adr/0039-separate-cth-identity-evidence-and-freeze-anchor-vector-transform-and-utility.md)
- 决策理由：[docs/adr/](docs/adr/)
- 独立文献与公开资源审查：[docs/references/independent_literature_and_idea_collision_review_2026-08-18.md](docs/references/independent_literature_and_idea_collision_review_2026-08-18.md)
- 已执行工作流事实：[docs/experiment/2026-08-18-ideaspark-workflow-run.md](docs/experiment/2026-08-18-ideaspark-workflow-run.md)
