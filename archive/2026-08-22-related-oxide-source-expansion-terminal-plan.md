# 已归档 live plan：相关氧化物来源扩展与 KC 分层裁决

- `phase_id`: `EAF_F3_TERMINAL_NO_FRONT`
- `lifecycle_state`: `BLOCKED`
- `blocker_id`: `FINAL_FRONT_BENCHMARK_NO_GO`
- `authorization_state`: `PHASE_A_COMPLETED_2026-08-22`
- `plan_status`: `TERMINAL_EXPANDED_OXIDE_ZERO_CANDIDATE`
- `material_scope_expansion_authorized`: `false`
- `source_scan_authorized`: `false`
- `numerical_execution_authorized`: `false`
- `formal_or_gpu_authorized`: `false`
- `future_route_slots_consumed`: `0/3`
- `claim_status`: `PROPOSED_METHOD_NO_NUMERICAL_EVIDENCE`

## 计划结论

有界 VO₂ 来源扫描已经以 `BOUNDED_ZERO_CANDIDATE` 收口：六个深审对象 `0/6 PASS`。用户随后批准的相关氧化物 Phase A 也已按四个冻结查询族、八个深审对象的上限完成，结果为 `EXPANDED_OXIDE_ZERO_CANDIDATE`、`0/8 PASS`；见 [扩展扫描报告](../docs/references/2026-08-22-related-oxide-source-complete-candidate-scan.md)。

因此本计划已到终止条件：没有活动对象、fallback 或候选排序，正式路线仍为 `0/3`，Phase B–H 均关闭。当前以来源闭合二维氧化物对象承载 KC 的论文 idea 按计划停止；下一项高价值动作是另寻 idea，而不是继续材料扫描、降低来源门、跨来源拼接、启动数值研究或组合第二模块。

## 论文去向与可证伪主张

- **目标论文**：以 KC 为必选核心的 PINN 数值方法论文，服务于二维氧化物相变/忆阻器中重复脉冲诱发的空间异步、局部、部分覆盖且可恢复结构相事件。
- **核心问题**：场选择性结构动力学时钟是否在实际计算预算匹配下，相对 strong raw、identity、一般单调时钟和动力学错位负控，产生动力学特异性的结构端点增量，同时保持原物理非劣并改善独立器件端点。
- **突破定义**：只有 standalone KC 在未触碰 formal 完整案例上获得 `KC_GO` 才算路线突破；pilot、组合或部分门通过都不算。
- **禁止主张**：实验验证、真实 MHz/GHz 器件有效性、SOTA、普适 spectral-bias 解决、Q‑POP 完整真值，以及由多个 bounded 失败投票得到的一般性 PINN/KC 失败。
- **路线止损**：最多三条正式候选路线；第三条仍无 standalone formal `KC_GO` 时，在第四条启动前放弃当前 KC idea。

## Phase A：一次性扩展来源闭合扫描

**目的**：回答“相关氧化物体系中是否存在能承载 KC 科学投票的公开二维对象”。本阶段只读，不消耗三条路线。

### A0. 冻结材料与对象边界

- 纳入：具有明确结构/相态序参量、二维电—热—相态因果链、重复动力学和器件边界的相关氧化物 PCM、Mott 器件或忆阻器。
- 优先查询族：`NbO2/VOx Mott electrothermal phase-field`、`nickelate/correlated-oxide phase-field device`、`oxide memristor 2D continuum structural-phase model`、`open oxide phase-change multiphysics code/data`。
- 排除：零维/一维集总或 SPICE 模型、纯电子阈值开关、只有离子浓度而无结构相态的漂移模型、实验数据而无数值求解器、未公开专有工程、通用框架而非冻结材料对象、硫系 PCM，以及需要跨论文拼接因果量的对象。
- 预算：最多四个查询族、深入审计八个物理对象；达到三个硬门通过对象或查询族耗尽即停止，不为凑满候选降低标准。

### A1. 一手来源审计

每个对象必须在同一来源链闭合：

1. 原始论文、DOI、发布日期与物理对象身份；
2. 固定版本的公开实现与明确软件许可证；
3. 二维几何、材料、本构、接触、边界、驱动、方程、参数与状态语义；
4. 可由公开实现重新生成的完整参考输出；
5. 至少两个周期的空间异步、局部、部分覆盖且可恢复结构相事件证据；
6. 独立 evaluator、时空离散资格化及 qualification/development/formal/reserve 四角色完整案例池的可行性。

任一项缺失即硬 `FAIL`。不得克隆大型仓库、安装依赖、联系作者或运行 solver 来替来源缺口辩护；只有对象先在只读审计中通过，才进入后续批准。

### A2. 候选冻结与 Phase A 终局

- 产物：一份带查询边界、来源回链、失败矩阵和 `PASS/FAIL` 的日期化参考报告。
- 若有通过对象：冻结 `1 active + 最多 2 fallbacks`，按来源闭合、事件适配、二维多物理完整性、复现负担、raw headroom 和论文价值排序，提交用户选择。
- 若 `0 PASS`：裁决 `EXPANDED_OXIDE_ZERO_CANDIDATE`；不再扩到硫系 PCM、不降低来源门、不制造 synthetic substrate。当前 KC 论文保持不可执行，推荐另寻 idea。
- Phase A 完成后仍不得自动启动数值研究。

## Phase B：活动对象冻结与第一路线启动

**前置批准**：用户明确批准一个活动对象、一个冻结 fallback 顺序和该对象的科学合同。首次科学运行启动时，正式路线计数从 `0/3` 变为 `1/3`。

| 任务 | 工作内容 | 产物 | 通过门 / 停止条件 |
|---|---|---|---|
| B0 物理合同冻结 | 逐项核对论文、代码、输入与输出；只允许环境、格式、无量纲化和等价离散适配 | 来源 manifest、A/A′ 映射、冻结 `PhysicalContract` | 任一决定事件拓扑的量缺失即停止；不得补造物理 |
| B1 最短环境 smoke | 在隔离 Python 3.11/来源要求环境中验证入口、最小输入、输出与固定版本 | 可复现环境说明、最短 smoke 产物 | 环境外部损坏可原配置修复；隐藏依赖或不可重现行为关闭路线 |
| B2 作者参考复现 | 原样复现公开 reference case，不改几何、动力学、drive 或 seed 语义 | canonical reference artifact、差异报告 | 达到来源声明的数值/事件容差；否则路线关闭 |
| B3 独立评价链 | 用与生成器和 PINN 残差分离的实现计算守恒、事件和器件端点 | 独立 evaluator、聚焦测试、artifact adapter | evaluator 与来源语义一致；实质不一致才考虑第二 solver |

Phase B 只证明来源对象可复现，不证明 oracle 合格或 KC 有效。

## Phase C：oracle、事件与案例角色资格化

| 任务 | 工作内容 | 产物 | 通过门 / 停止条件 |
|---|---|---|---|
| C0 数值预算预检 | 以一个 qualification case 测量时空分辨率、吞吐、内存和误差量级 | throughput 记录、冻结资格化预算 | 超出一个月总目标且无可逆缩放方案即关闭路线 |
| C1 四角色案例池 | 按完整几何/器件/协议/轨迹分成 qualification、development、formal、reserve | 不可拆分 case manifest | 公开 reference 只进 qualification；时间片不得跨池 |
| C2 两周期事件门 | 检查每周期形成/恢复、空间异步性、局部性、部分覆盖和器件后果 | 事件诊断表与可视化 | 至少两个周期全部通过；整域同步翻转和单周期偶然事件失败 |
| C3 时空离散收敛 | 使用 coarse/reference/fine 的来源尺度层级检查事件拓扑、端点和守恒 | 收敛表、oracle error budget | 空间时序差高于离散分辨率，关键诊断随加密收敛 |
| C4 oracle 冻结 | 冻结字段语义、单位、阈值、端点、误差地板和数据身份 | versioned oracle contract | 合成数值 oracle 身份明确；实验数据只作外部一致性支持 |

任一 C 门失败均消耗当前路线但禁止 strong-raw/KC。只在用户批准后才切换到下一冻结 fallback。

## Phase D：两级 strong-raw 能力门

### D0. 公平预算冻结

- 先用单个 development case 和单 seed smoke 测量每次更新的实际计算与方差量级，再一次性冻结精确更新数、seed、checkpoint 和停止规则。
- 两级梯度仅包括：一个强直接 raw-time PINN，以及一个事前指定的容量或优化升级；不得根据结果同时换网络、采样、损失和预算。
- 主要公平轴为包含自动微分与额外导数代价的实际计算预算；同时报告参数量、更新数和墙钟时间。

### D1. 实现与等价 smoke

- 从现有七未知量 PINN 资产中只复用与新 `PhysicalContract` 语义一致的 artifact、ledger、checkpoint 和 evaluator 接口。
- 重新实现与 oracle 生成器独立的 PINN 残差；使用制造解/零驱动/初边值检查验证方程、单位和导数。
- raw、identity 和后续 KC 共享同一基础网络族、case、seed、checkpoint 与 evaluator。

### D2. strong-raw 裁决

- 若 strong raw 达到 oracle/离散误差地板：`NO_BOTTLENECK`，路线消耗，KC 不入场。
- 若两级 raw 都不能解析合格结构事件：`RAW_INCOMPETENT_ROUTE_NO_TEST`，路线消耗，KC 不入场。
- 只有 strong raw 能解析事件、通过物理非劣且仍留下预声明 KC headroom，才进入 Phase E。

## Phase E：KC development 与机制归因

| 任务 | 工作内容 | 产物 | 通过门 / 停止条件 |
|---|---|---|---|
| E0 KC 适配 | 仅结构序参量使用构造单调时钟；保留隔离计算图、完整一/二阶及混合导数回拉、分段强形式 | KC 实现、制造解与回拉测试 | 任一时间旁路、漏导数或静默物理修改均为 `INVALID` |
| E1 控制臂 | 冻结 raw、identity、一般单调和动力学错位负控 | 同预算配置矩阵 | 所有臂共享 case、seed、基础网络、checkpoint 和 evaluator |
| E2 开发协议 | 仅在 development 池执行已接受的 2×2 梯度/启用 pilot，并冻结 clock loss、可容许性和 checkpoint | development intent、结果报告 | 不得读取 formal/reserve，不得按结果新增第三方案 |
| E3 有序开发门 | 依次检查结构主效应、动力学特异性、原物理非劣和独立器件端点 | KC development disposition | 无判别信号则路线关闭；正向 pilot 只授权 formal 设计，不算突破 |

CPU smoke 通过且 development 预算显示高价值后，才可另行申请 GPU；GPU 不用于开放式超参数搜索。

## Phase F：条件式第二模块

本阶段默认跳过。只有 KC 已在 development 独立通过，并且未读取 formal 结果便验证出一个与 KC 不同的剩余瓶颈时才允许进入。

1. 只用 development 证据把瓶颈分类为表示、采样、约束/守恒、优化或不确定性问题；没有可归因瓶颈则保留单模块 KC。
2. 对候选模块记录来源、许可、A/A′ 适配、接口、预期增量和关键消融；允许一个活动模块、最多两个 development-only fallback。
3. 第二模块必须在同一合格 oracle、胜任 raw 和互斥 development cases 上独立通过；失败模块立即移出论文主方法，不得捆绑救援。
4. development 至少比较 raw、KC、M2、KC+M2，并按实际计算匹配；组合必须优于最佳单模块或实现预声明的不同功能增量。仅持平时保留更简单单模块。
5. 第二模块失败不取消已经通过 development 的 standalone KC；路线可按单模块进入 formal。

## Phase G：formal 冻结、执行与裁决

**前置批准**：Phase E（及可选 Phase F）完成后，提交精确案例数、seed、最小相关效应、非劣界、置信规则、实际计算额度、GPU/日历预算和停止条件，由用户另行批准。

### G0. formal intent

- 打开结果前冻结所有方法、完整案例、seed、预算、checkpoint、评价版本与处置规则。
- formal 使用未触碰完整案例；seed 只是案例内算法重复，不能冒充独立科学样本。
- 若启用 M2，formal 同时运行 raw、KC、M2 和 KC+M2；KC 或 M2 任一单独未过门，组合自动失去主方法资格。

### G1. 有序合取门

1. **结构主效应**：KC 相对 matched raw 改善周期等权结构相区时空对称差；
2. **动力学特异性**：KC 优于一般单调与动力学错位负控；
3. **原物理非劣**：守恒、残差、边界/界面与未变换物理场不劣于冻结界；
4. **独立器件后果**：改善与冻结 drive 共轭的端口/电路整段轨迹端点；
5. **完整案例稳健性**：结论跨完整案例成立，不由最佳 seed 或单一展示 case 驱动。

### G2. 互斥处置

- `KC_GO`：路线突破；进入 Phase H。
- `KC_SCIENTIFIC_NO_GO`：路线消耗；组合不得救援。PHA 只能作为另行批准、使用 untouched reserve 的诊断路线。
- `INCONCLUSIVE_BUDGET_EXHAUSTED`：路线消耗；不追加 seed、预算或事后缩窄 claim。
- 方法外执行损坏：只允许按原 intent 精确重放；算法发散属于方法表现。

## Phase H：论文与路线切换

### H1. `KC_GO` 后的论文闭合

- 主图：来源对象与事件、oracle 收敛、strong-raw 能力、KC/负控结构端点、器件端点及完整案例稳健性。
- 主表：实际计算公平、分层合取门、必要消融和单/双模块选择。
- 补充材料：方程—代码映射、A/A′ 来源表、案例角色、intent/manifest/artifact/evaluator/ledger、负面路线边界与复现步骤。
- 写作只主张限定来源对象/材料域内的动力学特异性数值增量；不升级为实验、SOTA 或普适结论。

### H2. 路线失败后的串行切换

- 每条路线终局后先形成有边界 closeout，再由用户决定是否启动冻结 fallback；不得自动切换或重排。
- 第一/第二路线失败可依次申请下一候选；第三路线仍无 standalone formal `KC_GO` 时终止 KC idea，不启动第四路线。
- 所有历史 Q‑POP、R3/R4、TAPF、ETPF、EAF 和新路线负面证据保留为问题定义、局限性与补充材料，不能累加成一般性方法失败。

## 任务依赖与高效执行顺序

| 优先级 | 任务包 | 依赖 | 预计人工/日历窗口 | 首个决策性产物 |
|---|---|---|---|---|
| P0 | Phase A 扩材料来源扫描 | 用户批准本计划与材料扩展 | 1–2 个工作日 | 合格候选或 `EXPANDED_OXIDE_ZERO_CANDIDATE` |
| P1 | Phase B 来源复现 | 用户批准活动对象 | 1–2 个工作日 | 可复现 reference artifact |
| P2 | Phase C oracle/事件资格化 | B 全部通过 | 2–3 个工作日 | 首张可信科学图：事件 + 收敛面板 |
| P3 | Phase D strong-raw | C 全部通过 | 2–3 个工作日 | `NO_BOTTLENECK`、raw 不胜任或 KC headroom |
| P4 | Phase E KC development | D 通过 | 2–4 个工作日 | 首张方法判别图；仍不是可写正面 claim |
| P5 | Phase F 第二模块（可选） | KC development 通过且存在不同瓶颈 | 0 或 2–3 个工作日 | 单模块或双模块 formal 锁定 |
| P6 | Phase G formal | 用户批准精确 formal/GPU 合同 | 3–5 个工作日 | 首条可写正面 claim 仅来自 `KC_GO` |
| P7 | Phase H 论文闭合 | `KC_GO` | 3–5 个工作日 | 论文初稿与可复现材料 |

最佳路径在找到合格对象后约需 15–24 个工作日；这是规划包络，不是完成承诺。精确计算小时、case 数和 seed 必须依据对象吞吐与 development 方差，在 formal 前一次冻结。

## 统一产物与执行纪律

- 每次真实运行继续使用 `intent → immutable manifest → canonical artifact → independent evaluator → append-only index`；计划、测试或 Git 成功不得冒充科学证据。
- 每阶段只创建其论文证据链真正消费的产物，不建立平行 dashboard、重复审计或永久版本树。
- 只在输入、实现或合同发生相关变化后重跑；达到通过、失败或阻塞条件立即收口。
- 不提交、推送、开 PR、合并或清理现有脏工作树，除非用户另行明确要求。

## 终局与下一授权边界

1. Phase A 已执行完毕并得到 `0/8 PASS`；不得追加第九个对象或自动扩大材料范围。
2. 因没有候选，Phase B–H、对象复现、solver、PINN、第二模块、formal 与 GPU 全部保持关闭。
3. 当前计划不再授权任何科研执行；下一步只能在用户另行授权后制定 oracle-first 的新 idea PLAN。
4. 历史负面证据继续用于约束新 idea 的问题定义与止损，但不得累加成 PINN/KC 的一般性失败。
