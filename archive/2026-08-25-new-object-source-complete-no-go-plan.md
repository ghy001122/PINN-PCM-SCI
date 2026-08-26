# Archived plan：来源完整新对象与 PINN idea 筛选

- `phase_id`: `NEW_SOURCE_COMPLETE_OBJECT_IDEA_RESEARCH_ACTIVE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `authorization_state`: `BOUNDED_IDEA_RESEARCH_ONLY`
- `plan_status`: `SOURCE_COMPLETE_OBJECT_SCREEN_ACTIVE`
- `candidate_status`: `SOURCE_COMPLETE_OBJECT_SCREEN_ACTIVE`
- `idea_research_status`: `AUTHORIZED_ACTIVE`
- `object_selection_status`: `NOT_SELECTED`
- `method_selection_status`: `NOT_SELECTED_PENDING_OBJECT_AND_BOTTLENECK`
- `fresh_primary_source_budget`: `UP_TO_20`
- `deep_review_object_family_budget`: `UP_TO_4`
- `compute_authorization`: `ZERO_SOLVE_ZERO_TRAINING_ZERO_GPU`
- `implementation_authorization`: `NOT_AUTHORIZED`
- `formal_or_gpu_authorization`: `NOT_AUTHORIZED`
- `prior_hfo_route_status`: `WAVEFORM_TIME_NO_GO_FROZEN`
- `novelty_status`: `NOT_NOVELTY_CLEARED`
- `claim_status`: `NO_SCIENTIFIC_METHOD_CLAIMS`

## 单一目标

在最多新增 20 项一手来源、深审最多 4 个对象家族的范围内，筛选并裁决一个来源完整的二维及以上氧化物器件对象；随后只依据该对象上可审计的预期瓶颈提出一个 load-bearing PINN 方法 idea。若没有对象通过，则以有界 No-Go 结束当前总目标，不扩大来源、材料或方法范围。

本阶段服务于一篇 evidence-routed scientific machine learning / computational physics 论文的对象与方法准入。当前不预写方法阳性，不把治理、对象复杂度或传统求解器替代 PINN 的算法增量。

## 当前授权与时间盒

- 时间盒：10 天，必要时最多延长 3 天；
- 新增一手来源：最多 20 项；
- 深审对象家族：最多 4 个；
- 允许：原始论文、官方 Supplement、官方代码/数据仓库、固定 release/commit、权威数据库的只读检索与证据整合；
- 允许：形成来源报告、对象选择/否决 ADR、论文证据合同及最小权威文档同步；
- 禁止：object build、solver、smoke、training intent、PINN、pilot、formal OOD、GPU、付费计算、联系作者、安装依赖或 Git 发布。

## 对象硬门

一个对象家族只有同时闭合以下条目才可进入唯一选择：

1. 二维及以上氧化物器件域、材料分区与接触结构；
2. 电—热—内部态因果链，以及各场的方程、本构、单位和有效域；
3. 初态、全部 IC/BC、界面条件与分支身份；
4. 可恢复的绝对物理时间、完整波形/脉冲节点、dwell 与连续 history；
5. 固定且合法的作者实现，或足以支持独立 clean-room 重建的完整物理合同；
6. 机器可读端口轨迹和至少一种能够裁决局部内部态事件的空间验证量；
7. 论文、代码、数据、模型资产和依赖的来源与许可；
8. 可按完整器件、几何、协议或轨迹形成互斥资格/开发/formal 案例角色。

任一决定对象身份、物理拓扑、绝对时间、事件极性、输运速度、合法重建或验证量的缺口，均不得用跨材料参数、常规数值默认值或目标结果校准补齐。

## 四家族深审规则

- 先复用既有 48 项论文/26 个官方载体账本和历史 source No-Go，避免以新名字重复同一已关闭合同；
- 每个家族以最早硬否决优先，出现决定性失败后停止为该家族追加来源；
- HFO-NP-v1 保持 `WAVEFORM_TIME_NO_GO_FROZEN`；不得修补、自动 synthetic 降级或继续其 CTH 路线；
- Q-POP、R1、R2/FerroX、R3/R4、TAPF、ETPF、EAF 的历史 No-Go 保持原边界，不自动重启；
- 不因“没有找到 exact collision”宣称 novelty，不因代码存在宣称对象或事件合格。

## 单一对象选择规则

候选按以下优先级裁决：

1. 来源合同完整性与合法可重建性；
2. 局部、可重复、可离散资格化的内部态事件；
3. 电—热反馈对事件具有可直接检验的因果接口；
4. 机器可读验证量和完整案例拆分能力；
5. 在有界计算下获得首个判别性 Go/No-Go 的可行性；
6. 对 PINN 方法研究存在尚未预押的、可由 strong raw 验证的潜在瓶颈。

只有一个家族可被选为下一对象。若多个家族同时通过，选择来源合同更完整、验证量更强且最早可裁决者；不得同时保留多个最终对象。

## 方法中立证据合同

对象通过后，本阶段只提出待后续验证的瓶颈假设和一个条件式方法 idea，并预冻结：

- 最强直接基线；
- 能隔离唯一 load-bearing primitive 的关键消融；
- 完整案例与泄漏边界；
- 一个 mechanism-aligned OOD 家族和一个 orthogonal OOD 家族；
- 事件/场/守恒/端口主次端点；
- future smoke → pilot → formal 的预算生成规则和停止条件；
- bounded direct/near prior-art collision review。

CTH、cKC、PHA、IRAC、采样或空间表示模块均不能在对象及 bottleneck 证据前被预选。CTH 只在未来证据明确指向输运协议参数的有限预算表示瓶颈时，才可按 smooth6、direct residual-Jacobian、wider/extra-work raw、wrong-knot 与 sealed protocol utility 合同重新审查。

## 当前产物

1. `docs/references/2026-08-25-new-object-source-complete-review.md`
   - 查询范围与时间窗；
   - 不超过 20 项的一手来源账本；
   - 不超过 4 个家族的逐门证据与单一 verdict；
   - 唯一对象或有界 No-Go；
   - 若通过，给出方法中立 bottleneck hypotheses、强基线、消融与 OOD 候选。
2. `docs/adr/0040-select-new-source-complete-object.md`
   - 仅在来源报告形成可接受决定后记录唯一对象选择或有界不选择决定；
   - 不授权对象实现或数值执行。
3. 最小同步 `README / CONTEXT / active phase / PROJECT_STATE / docs map / live plan / ADR index`，并运行文档一致性门。

## 停止条件

任一对象家族出现下列情况即拒绝该家族：

- 关键 IC/BC、本构、绝对时间或 history 无法由同一可追溯来源家族闭合；
- 需要跨材料移植决定性参数或按目标事件调参；
- 只有定性图片而没有可裁决、可数字化或机器可读验证量；
- 代码、数据、模型资产或依赖许可不足，且 clean-room 物理合同也不完整；
- 事件依赖未闭合的额外物理块，或只能通过改变研究对象救援；
- 对象虽完整，但不能支持实体级案例隔离或 PINN 核心方法评价。

4 个家族全部失败或新增 20 项一手来源预算耗尽时，记：

```text
NEW_OBJECT_SOURCE_COMPLETE_BOUNDED_NO_GO
OBJECT_SELECTION_STATUS=NO_OBJECT_SELECTED
METHOD_SELECTION_STATUS=NOT_REACHED
```

不自动扩大搜索、重启历史路线或降级成无来源保真主张的 synthetic benchmark。

## 后续授权门

只有来源报告与 ADR 形成唯一对象、论文证据合同和单一条件式方法 idea 后，才能提交阶段 1B/2 的实现计划供实时授权链审查。即使阶段 1A 通过，object build、CPU oracle、PINN、training、pilot、formal、GPU 和付费计算仍保持关闭。

## 当前下一动作

立即执行上述有界一手来源筛选，优先寻找最早硬否决并形成单一对象或有界 No-Go；同时保持 HFO 和所有历史方法路线冻结。
