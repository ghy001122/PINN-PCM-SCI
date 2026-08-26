# 多 substrate 方法就绪性负面报告，2026-08-21

- `report_scope`: `DEVELOPMENT_PREQUALIFICATION_SYNTHESIS`
- `report_disposition`: `METHOD_ADJUDICATION_BLOCKED_BY_SUBSTRATE_AND_BASELINE_COMPETENCE`
- `claim_status`: `BOUNDED_NEGATIVE_NO_VALID_METHOD_VERDICT`
- `new_numerical_execution`: `NONE`
- `formal_evidence`: `NONE`
- `supersedes`: `NONE`

本报告综合已经执行并保留的 Q‑POP、R3、R4、TAPF、ETPF、EAF、strong-raw、KC 与 PHA 记录。它不改写任何 intent、manifest、artifact 或原始收口文档，也不把多个 development 失败累加成一般性科学结论。

## 执行摘要

项目已经证明方法与证据工程可以运行，但尚未完成对论文核心 idea 的有效科学检验。

- `VERIFIED_IMPLEMENTATION`：原生 Q‑POP 最短 smoke、七未知量强形式 PINN、raw/identity/KC、完整一阶/二阶/混合导数回拉、初值精确结构表示、oracle-blind checkpoint、canonical HDF5、独立磁盘 evaluator 与 append-only ledger 均已实现并实际运行。
- `FINAL_BOUNDED_NEGATIVE`：所有获批的替代 substrate 都在方法投票前失败。R3 与 TAPF 没有形成结构事件；R4 执行无效；ETPF 形成整域同步翻转而非移动前沿；EAF 通过来源尺度与工程 smoke 后，冻结 drive bracket 仍没有形成主事件。
- `VERIFIED_DEVELOPMENT_NEGATIVE`：在未资格化的 Q‑POP 随包参考上，strong raw 没有解析结构事件；KC 2×2 与 PHA 四臂也没有产生结构端点增量。
- `NOT_EVALUATED`：合格移动前沿 oracle 上的 strong raw 能力、KC 动力学特异性、formal OOD、实验有效性与正面论文主张。
- `UNKNOWN`：场选择性结构动力学时钟在合格、可辨别场景中的实际增量。

当前最强结论不是“KC 失败”，而是：**项目尚未建立一个允许 KC 接受公平科学投票的方法就绪性闭环。**

## 资格链总表

| 路线 | 工程控制流 | 目标结构信号 | oracle 资格 | strong raw | KC/PHA 判别 | 终局 |
|---|---|---|---|---|---|---|
| 原生/随包 Q‑POP | 通过最短 smoke、导入、评价链 | 随包参考有结构动态，完整作者案例未闭合 | `INCONCLUSIVE_BUDGET_EXHAUSTED`；随包参考未资格化 | raw-v3 相区动态范围 `0.0` | development KC/PHA 无增量，但不投 formal 票 | 物理来源有事件，证据身份和 baseline 能力均不足 |
| QPOP‑R3 | smoke 通过；修正后 9/9 signal case 完成 | `0/9` 形成非退化周期 | 未进入离散资格化 | 未启动 | 未启动 | `REDUCED_ORACLE_NO_SIGNAL` |
| QPOP‑R4 | smoke 通过 | 两次固定 signal pilot 均未完成首个 case | 执行无效，不能判有/无信号 | 未启动 | 未启动 | `INVALID_EXECUTION` |
| QPOP‑TAPF‑v1 | P1 smoke、守恒、artifact、evaluator 通过 | 9/9 有限，但相区动态、周期与前沿位移均为 `0` | 不具备事件资格 | 未启动 | 未启动 | `TAPF_NO_SIGNAL` |
| ETPF‑KC‑v1 | K1 全链通过 | 9/9 有四次形成—恢复，但为整域同步翻转 | 五个时空层级均 `resolved_front_cycles=0` | 未启动 | 未启动 | `ETPF_QUALIFICATION_INVALID_NO_RESOLVED_FRONT` |
| EAF‑KC‑v1 | F0 来源审计、F1 尺度门、F2 smoke 通过 | 修正局部成核合同后，`0.6–2.4 V` 两端仍未达到主事件门 | 未生成可供 F4 资格化的参考 case | 未启动 | 未启动 | `FINAL_FRONT_BENCHMARK_NO_GO` |

这不是六次独立的“方法失败”。它们分别暴露了资格链中不同的断点，且后续断点不能在前置条件缺失时被解释。

## 逐层证据

### 1. 方法实现存在，但实现存在不等于方法有效

制造解和一次更新 smoke 已核对 raw、identity 与 KC 的控制流、结构时钟隔离和导数回拉；磁盘 evaluator 能在 trainer 进程外读取产物并生成冻结端点。PHA 共享 gate 也完成容量、采样与四臂归因控制流。

这些证据只支持 `VERIFIED_IMPLEMENTATION`。它们不支持训练收益、物理有效性、相对基线增量或论文创新性。

### 2. 原生 Q‑POP 同时存在“真实 development 信号”和“不合格证据身份”

随包参考包含 38 个场快照、8141 个节点与 16000 个三角单元；冻结阈值下相区占比动态范围为 `0.5534946567`。但作者 2000 ns 案例没有在冻结 CPU 预算内完成，随包参考也只覆盖至约 `512.0793 ns`，因此未冻结 oracle error budget，G3 裁决为 `INCONCLUSIVE_BUDGET_EXHAUSTED`。

这意味着随包参考可以用于开发诊断，不能作为 formal 数值真值。

### 3. strong raw 的失败是 bounded baseline-competence 失败

raw-v3 修复了初值表示和 step-0 checkpoint 偏置，选择了非初始化 step 900，并完成固定 1600 次更新。最终器件 NRMSE 为 `0.9934716030`，但相区动态范围仍为 `0.0`，结构端点为 `0.2290643041`，最大归一化物理违规为 `1.1427834250`，裁决 `RAW_EVENT_NOT_RESOLVED`。

器件轨迹发生变化而结构通道保持恒定，支持“结构表示或残差优化形成近初始吸引域”的解释；它不证明所有强形式 PINN 或所有预算都无法解析该事件。

### 4. KC/PHA development 结果没有方法裁决权

KC 冻结 2×2 协议在未资格化参考上均未改善结构端点。PHA 修正数值尺度后，global Fourier 与 shared 都选出非初始化 step 40，但 global/capacity/sampling/shared 四臂结构端点仍同为 `0.2290643041`。

由于 oracle 未资格化且共同 strong-raw 结构能力未建立，这些结果只能说明“当前 development 协议未检出信号”，不能升级为 `KC_SCIENTIFIC_NO_GO`、PHA 一般失败或论文反例。

### 5. R3、R4 与 TAPF 没有解决“可判别事件”

- R3 修正后的九案例全部有限，最大平衡违规低于 `1e-8` 量级，但相区动态范围全部为 `0.0`，裁决 `REDUCED_ORACLE_NO_SIGNAL`。
- R4 smoke 有效，但两次 signal pilot 在首个完整案例前因耦合 η–μ 局部反应不收敛而失败。正确身份是 `INVALID_EXECUTION`，不能包装为无信号。
- TAPF 的九案例全部完成且最大平衡违规约 `1e-13`，最高温度达到 `354.6909253 K`，但最佳 `eta_max=0.1377505`，未跨冻结阈值 `0.5`；结构事件为 `0/9`。

共同结论仅限于：这些冻结合同没有提供可以启动 strong raw/KC 的结构事件 substrate。

### 6. ETPF 证明“有相变”不等于“有移动前沿”

ETPF 九案例都有四次形成—恢复，相区占比范围为 `1.0`。修正 evaluator 时间语义并提高到 1 ns 采样后，五个网格/时间层级仍全部 `resolved_front_cycles=0`，且空间相区差最细两层没有收缩。

高热扩散、全域 spinodal 过驱动与快速相动力学共同造成小于 1 ns 的整域翻转。旧 5 ns 守卫把空相区到满相区误当成前沿位移，说明事件存在性、空间局部性和 evaluator 一致性必须在 PINN 训练前共同冻结。

### 7. EAF 证明“无量纲可行”不等于“非线性系统会产生前沿”

EAF 的一手来源冻结了 600 nm 深度、90 ns 脉冲、`36±10 ns` 形成、`107±21 ns` 恢复和 `4.54 nm/ns` 前沿等尺度。F1 得到 `Fo=0.5009015`、热扩散长度比例 `0.707744`、预测前沿覆盖比例 `0.681`，因此必要的尺度门通过。

但横向电极间距、接触热/电阻与去嵌入端口电压仍为 `UNKNOWN`，而它们恰好决定 Joule 热空间拓扑。局部成核合同完成唯一解析修正后，同一冻结 `0.6–2.4 V` bracket 的两端仍没有达到相区动态范围 `0.20` 的形成门，未生成参考 case。

因此 EAF 的终局是否定冻结 `A_PRIME` benchmark 的事件能力，不是否定实验尺度、相场方程或 KC idea。

## 根因审判

### 根因 A：论文主张先于可用证据对象

项目先锁定“重复脉冲下移动结构前沿的 Kinetics‑Clock PINN”，之后才持续寻找能承载该主张的 oracle。方法模块先完成、substrate 后补，导致每次 substrate 失败都会诱发新的 substrate 设计；若继续，研究将从假设检验滑向为方法寻找正例。

### 根因 B：早期事件门只问“是否转变”，没有问“是否可判别”

TAPF 检验了跨阈值事件，ETPF 初始 guard 接受了整域翻转。论文真正需要的是持续、连通、部分覆盖、时空可解析且可恢复的移动前沿。这个定义直到后期才成为硬门，前期方法工作因而建立在不足以辨别目标机制的事件语义上。

### 根因 C：把因果未知量当成普通适配量

EAF 的未知横向电极间距、接触热阻、接触电阻与端口电压不是装饰性细节；它们直接决定热点位置、温度梯度、成核位置和前沿速度。只冻结深度、脉冲和时间尺度，不能唯一闭合二维电热拓扑。

### 根因 D：尺度分析被误用为充分条件

Fourier 数、扩散长度和“速度×时间”只能排除明显不可能的区域，不能保证含反馈、势垒、成核和边界热损失的非线性系统会进入目标事件流形。F1 是廉价必要门，不是 oracle 资格证。

### 根因 E：baseline 能力与方法增量不可分

在 Q‑POP development 参考上，raw、KC 和 PHA 共享同一个结构通道失效。没有一个能够解析事件的强 raw 基线，就无法区分“KC 没有增量”与“所有比较臂都被共同表示/残差瓶颈压平”。继续添加时钟、频率或采样模块只会增加不可归因性。

### 根因 F：物理忠实度、事件可构造性与运行可行性没有同时满足

完整 Q‑POP 更接近来源物理，但资格化与训练负担过高；R3/TAPF 可运行但没有事件；R4 恢复动力学后不收敛；ETPF 有事件但空间退化；EAF 有来源尺度但关键二维拓扑未知。当前没有一条路线同时满足物理身份、事件能力、数值资格和训练可行性。

## 已被否定与仍未被否定

### 已被当前证据否定

- 冻结 QPOP‑R3 九案例作为结构事件来源；
- 冻结 QPOP‑TAPF 九案例作为结构事件来源；
- 冻结 ETPF 合同作为移动前沿 oracle；
- 冻结 EAF `A_PRIME` 合同及 `0.6–2.4 V` bracket 作为单参考前沿来源；
- 七未知量 raw-v3 在冻结网络、训练和评价预算下的事件解析能力；
- 未资格化 Q‑POP development 参考上的 KC 2×2 与 PHA 四臂信号。

### 没有被当前证据否定

- 场选择性结构动力学时钟的一般有效性；
- 在合格移动前沿 oracle 上 KC 相对 strong raw 的增量；
- 其他物理有据、事前冻结的器件几何或边界合同；
- 真实 VO₂ 器件有效性、formal OOD、实验验证或 SOTA；
- 任何超出已登记网络、预算、case 与 evaluator 的 PINN 一般能力。

## 对论文的可用价值

### 可以进入当前论文决策链

- 一套明确区分来源事实 `A`、有界适配 `A_PRIME` 与工程选择的 source map；
- “尺度可行 → 事件能力 → 离散资格 → strong raw → 方法增量”的分层门控；
- 对整域同步翻转、无事件、执行无效和 baseline 无能力四类失败的严格区分；
- 可复现的 intent/manifest/artifact/evaluator/ledger 证据链；
- 解释为何方法结果必须在合格且有辨别力的 substrate 上才有意义。

### 不能进入正面论文主张

- KC 或 PHA 的有效性、无效性或相对优势；
- Q‑POP、TAPF、ETPF 或 EAF 的实验真值身份；
- 真实器件、MHz/GHz、SOTA 或 formal OOD 结论；
- 用多个 bounded 失败投票形成一般性“PINN 不适用”结论；
- 把测试通过、代码规模或运行数量包装成科学贡献。

本报告目前最适合作为内部路线裁决、论文问题定义、局限性和可复现补充材料的证据底稿。若论文仍要求正面算法/网络创新，它本身不足以形成目标论文。

## 下一路线的不可妥协准入条件

1. 先决定论文到底要证明“结构时钟对移动前沿有增量”，还是更一般的“事件对齐时间表示对刚性相变动力学有增量”；不得在实验后缩窄或扩大。
2. 在实现新 PINN 前冻结可独立复现的二维电—热—相态 case，且所有决定空间加热拓扑的几何、接触和驱动量都有来源或明确 synthetic 身份。
3. 事件门必须同时要求局部性、连通性、部分覆盖、持续时间、恢复和时空分辨率；只发生跨阈值或整域翻转均不准入。
4. oracle 必须先通过离散收敛、守恒与事件稳定性；无资格化 reference 不进入方法投票。
5. strong raw 必须先在同一冻结 evaluator 上解析事件。raw 若达到误差地板则裁为 `NO_BOTTLENECK`；raw 若完全无能力则方法比较不具辨别力。
6. KC 仍只能是单一正向干预；identity、一般单调和动力学错位负控必须共享 case、预算、checkpoint 与 evaluator。
7. 完整案例是拆分单位，formal OOD、seed、预算、主端点和停止条件必须在打开结果前冻结。
8. 下一条路线只能有一个事前批准的物理 substrate 和一个明确 fallback；不得继续串行制造 benchmark 为既定方法寻找正例。

## 证据入口

- [Q‑POP 资格、KC/PHA development 收口](2026-08-21-kc-pha-development-closeout.md)
- [N1–N3B 终局收口](2026-08-21-n1-n3b-terminal-closeout.md)
- [R4 与 raw-v3 收口](2026-08-21-r4-and-raw-v3-closeout.md)
- [QPOP‑TAPF P2 收口](2026-08-21-qpop-tapf-p2-closeout.md)
- [ETPF K2Q 终局收口](2026-08-21-etpf-k2q-terminal-closeout.md)
- [EAF F3 终局收口](2026-08-21-eaf-f3-terminal-closeout.md)
- [EAF 来源审计](../references/eaf_kc_front_source_audit_2026-08-21.md)
- [运行索引](INDEX.md)

