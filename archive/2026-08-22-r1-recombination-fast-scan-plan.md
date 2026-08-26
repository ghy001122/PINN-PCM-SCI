# 已归档计划：模块迁移重组 FAST_SCAN 与新论文路线选择

- `status`: `SUPERSEDED`
- `superseded_by`: `docs/plans/NEXT_ACTIONS.md`
- `superseded_at`: `2026-08-22`

- `phase_id`: `POST_SCAN_RECOMBINATION_FAST_SCAN`
- `lifecycle_state`: `PLANNING`
- `blocker_id`: `ACTIVE_COMBINATION_FULL_DESIGN_NOT_APPROVED`
- `authorization_state`: `USER_AUTHORIZED_RECOMBINATION_POLICY_2026-08-22`
- `plan_status`: `FAST_SCAN_COMPLETE_AWAITING_FULL_DESIGN_APPROVAL`
- `source_card_refresh_authorized`: `true`
- `scientific_execution_authorized`: `false`
- `formal_or_gpu_authorized`: `false`
- `global_route_count_cap`: `NONE_USER_REVOKED_2026-08-22`
- `claim_status`: `PROPOSED_METHOD_NO_NUMERICAL_EVIDENCE`

## 结论

用户于 2026-08-22 明确纠正：材料、物理闭合、网络、损失、训练控制流、评价协议及方法模块均可迁移、适配和组合；不得把此前 `0/8 PASS` 解释成对后续换材料、调网络或模块重组的永久禁令。

用户随后撤销后续研究的固定全局次数上限。路线不再共享计数槽位；每条路线仍必须有自己的批准、预算、证据门和停止条件，取消全局计数不授权无界搜索或结果导向救援。

VO₂ 与相关氧化物扫描结果保持有效，但只关闭其冻结的“同一来源链直接提供完整二维 oracle”路线。跨来源模块可以构成新的透明派生研究对象，前提是逐项记录 A/A′、来源、许可、工程选择与证据身份，且不得把派生对象冒充作者复现、实验真值或同源 source-complete oracle。

本轮按 `research-module-recombination FAST_SCAN` 完成有界筛选：六个核心模块、六个组合、三个深评对象；冻结一个 provisional active 和两个 genuine fallbacks。这里只完成设计与论文故事路由，不授权 solver、PINN、训练、formal 或 GPU。

## 目标论文与故事主线

### 已接受的根决策

1. 不可约目标是取得可归因、可复现且具有实质算法增量的 PINN 论文证据；KC′、E_S′ 与双模块标题均可按证据替换，不能预定组合成功。
2. R1 只作为材料类别级 `derived/synthetic` benchmark；不作 VO₂、V₂O₃ 或其他具名材料的定量/半定量验证主张。
3. 组合创新必须先通过定向 prior-art 碰撞否决，并由预声明交互机制和 2×2 消融支持；benchmark/workflow 完整性不能替代算法或网络增量。
4. 48 小时只承诺冻结协议下的路线裁决或首个可信事件里程碑，不承诺阳性 pilot，更不承诺 formal 证据。
5. 后续研究没有固定全局次数上限；每条路线仍使用独立批准、预算、证据门和停止条件。

`HYPOTHESIS`：可以围绕“二维氧化物相变/忆阻器中的时间刚性与空间局域界面同时压垮 raw-time PINN”构造一篇以 PINN 为核心的数值方法论文。候选主方法将透明组合：

1. 一个具备局部、部分覆盖、可恢复事件的派生二维电—热—相态器件 benchmark；
2. 一个处理结构动力学时间刚性的场选择性时间表示；
3. 一个处理局域界面/多尺度空间结构的网络或采样模块；
4. 一个与生成器及 PINN 残差分离的事件—守恒—器件评价链。

允许的故事包装是“问题 → 已证实瓶颈 → 来源模块 → 精确适配 → 新接口/能力 → 最小证据 → claim”。禁止的包装包括隐藏来源、抹去负结果、事后移动阈值、把工程选择写成材料事实、把已有模块冒充原创、编造数据或把合成 benchmark 写成实验验证。

## Source Module Genealogy

| ID | 来源与现有资产 | 原始角色 | 可迁移角色 | 当前边界 |
|---|---|---|---|---|
| A | EAF/ETPF/TAPF 电热相场生成器、Q‑POP 来源尺度及现有 artifact/evaluator 接口 | 产生二维电—热—结构轨迹 | `adapted_module`：构造透明派生事件 benchmark | 既有冻结合同分别 No-Go；新对象必须改变前提/接口并重新命名 |
| B | V₂O₃/LSMO 一手工作中的局部形成—消失、部分覆盖和重复事件 | 实验事件与器件叙事 | `supporting_module`：冻结事件语义和外部一致性尺度 | 不能作为数值 oracle、训练标签或未公开代码替代物 |
| C | Sevic–Kobayashi 电热 Cahn–Hilliard/电形成方程 | 通用单次导电细丝电形成 | `adapted_module`：扩展为可恢复/双极协议 | 无论文专用公开实现；需要自行形成派生 solver 并明确身份 |
| D | FerroX 的 TDGL–Poisson–载流子代码、许可与参考数据 | HZO 铁电相场器件 | `directly_transferred_module` + 热耦合 A′ 候选 | 原模型无热方程，不得称热耦合扩展为原始 FerroX |
| E | 已实现的 raw/identity/KC/PHA、完整导数回拉、初值精确表示和 checkpoint | PINN 表示与训练模块 | `adapted_module`/`functional_composition` | 既有 development 无正向增量；只可在新任务/接口下重新裁决 |
| F | intent/manifest/artifact/独立 evaluator/完整 case 角色与防泄漏链 | 证据与复现工作流 | `validation_contribution`/`workflow_contribution` | 工程闭环不是科学结果，必须绑定真实数值证据 |

## Adaptation Ledger

| 适配 | 原行为 | 精确变化 | 预期能力 | 必需消融 | 禁止措辞 |
|---|---|---|---|---|---|
| A → A′ | 冻结 EAF/ETPF 几何与动力学 | 在来源范围内显式选择新的材料、接触、异质性和脉冲协议；完整标为 derived/synthetic | 稳定产生局部、部分覆盖、可恢复事件 | 原冻结对象 vs A′ 事件资格；不得只展示最好 case | 作者器件复现、实验 oracle |
| E_KC → E_KC′ | KC 只服务旧 VO₂ 结构序参量 | 按新状态变量和 PDE 完整重写速率、回拉与可容许性 | 缓解事件时间尺度分离 | raw-time 或一般单调时间表示 | 已证明普适抗高频 |
| E_S → E_S′ | 既有 PHA/Fourier/采样臂绑定未资格化 Q‑POP | 仅选择一个来源可核验的界面感知空间表示或采样模块，并适配到新对象 | 解析局域界面和部分覆盖结构 | KC-only 或 spatial-only 关键消融 | 更复杂网络天然更优 |
| D → D′ | FerroX 无热传输 | 加入有来源参数或明确工程参数的 Joule/热传输闭合 | 脉冲自热下 HZO 畴演化 | 等温 FerroX vs 热耦合 D′ | 原始 FerroX 已含自热 |
| C → C′ | 单次电形成至稳态 | 增加来源支持或明确派生的反向驱动/溶解动力学 | 可恢复 set/reset 事件 | 单次形成 C vs 可恢复 C′ | 原论文已证明循环恢复 |

## Candidate Combination Matrix

| 路线 | 模块 | 新能力与论文故事 | 主要风险 | 处置 |
|---|---|---|---|---|
| R1 | A′ + B(support) + E_KC′ + E_S′ + F | **双刚性 PINN**：派生器件先闭合可辨局部事件，再以动力学时间表示 + 界面感知空间表示共同解决时间/空间瓶颈 | benchmark 可能被质疑为为方法造题；必须做材料/几何/协议完整 OOD 与强基线 | `PROVISIONAL_ACTIVE` |
| R2 | D + D′ + E_KC′/E_S′ + F | **热耦合 FerroX PINN**：在固定开源 HZO 相场底座上研究脉冲自热、畴壁和 PINN 多尺度求解 | 热参数、事件协议和派生 solver 工作量较高 | `FALLBACK_1` |
| R3 | C + C′ + E_KC′ + F | **可恢复电形成 PINN**：围绕电热 Cahn–Hilliard 高阶刚性与细丝形成/溶解 | 无专用公开实现；四阶 PDE、参数与恢复动力学风险最高 | `FALLBACK_2` |
| P1 | 旧 Q‑POP reference + 继续无界换网络 | 只调网络而不修复 oracle/baseline 身份 | 重复既有不可归因失败 | `PRUNED` |
| P2 | V₂O₃/LSMO 实验图 + 未公开模型拼成“作者 oracle” | 事件叙事漂亮 | 违反证据身份和来源透明性 | `PRUNED` |
| P3 | 仅汇总负结果形成正向方法论文 | 快速写作 | 没有正面 PINN 增量，不能满足目标论文 | `PRUNED_AS_HEADLINE`；可作动机/局限性 |

## Utility Ranking

分数仅为路线选择辅助，`1–5`；成本/风险分数越高越差。

| 排名 | 路线 | 论文价值 | 可用证据概率 | 就绪度 | 资产复用 | 审稿防御 | 负结果回收 | 计算成本 | 集成风险 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | R1 | 4 | 4 | 5 | 5 | 3 | 5 | 2 | 3 |
| 2 | R2 | 5 | 3 | 3 | 3 | 5 | 3 | 5 | 4 |
| 3 | R3 | 4 | 2 | 2 | 3 | 3 | 3 | 5 | 5 |

| 路线 | 48 小时内的判别里程碑 | 分数 | 预计新增运行 | 低运行负担分数 |
|---|---|---:|---|---:|
| R1 | 完成 source cards 与 `FULL_DESIGN`；获批后争取首张可信事件图 | 4 | 最多 3 个 oracle 变体；方法 MVE 不超过 12 个训练臂 | 3 |
| R2 | 只裁决来源、热耦合接口与最小复用链能否进入 `FULL_DESIGN` | 2 | reference/热耦合/方法运行约 20–50 | 3 |
| R3 | 只裁决四阶 PDE、恢复动力学与许可缺口是否构成启动阻断 | 1 | 新 solver 与参数基础设施，规模未知 | 1 |

所有日历承诺只写 48 小时内可验证动作；后续里程碑按新证据另行冻结。

R1 胜出来自现有生成器、PINN 和 evaluator 的复用及最短判别路径；R2 的来源/许可与审稿防御更强，保留为第一 fallback；R3 只在前两路均被物理或证据门关闭时考虑。

## Selected Minimum Evidence Contract

### S0：R1 来源卡与 FULL_DESIGN（当前唯一下一步）

1. 将 A′ 的材料、几何、接触、驱动、方程、参数和 synthetic 身份逐项冻结；每个量标为 `A`、`A′` 或 `ENGINEERING`。
2. 只为 E_S′ 的唯一候选网络/采样模块及仍缺失的材料参数做定向一手来源卡，不做宽泛文献库存。
3. 冻结 paper claim、完整 case 拆分、formal OOD 轴、实际计算预算、最多三个事前变体和停止条件。
4. 输出 `FULL_DESIGN` 八节合同并等待用户批准；S0 不运行 solver 或训练。

### S1：事件 oracle MVE（未授权）

- 本次 R1 批准包内最多三个事前冻结 A′ 变体；不得根据结果连续换材料/几何。该路线内预算不是全局正式研究次数上限。
- 必须通过二维电—热—相态闭合、至少两周期形成/恢复、局部/部分覆盖、时空离散收敛、守恒与器件端点门。
- 三个变体均失败则关闭 R1，提交 R2 是否启动的最小决策，不追加第四个救援变体。

### S2：方法 MVE（未授权）

- 最小三件套：最强 raw-time/interface-capable PINN、一个关键模块消融、完整双模块组合。
- 若要同时把 KC′ 与 E_S′列为正向贡献，formal 前补全 raw、KC′、E_S′、KC′+E_S′ 四臂实际计算匹配比较。
- 单模块旧 No-Go 不被抹除；新结果只绑定新对象、接口、case、预算与 claim。
- 完整组合若没有性能、功能、界面、稳健性、守恒、泛化或可组合性中的预声明增量，则裁决 `COMBINATION_INCREMENT_NOT_SUPPORTED`，不得仅靠叙事升级。

## Pass/Fail Manuscript Routing

| 结果 | 允许写法 | 路由 |
|---|---|---|
| R1 oracle + 组合均通过 | 在透明派生二维氧化物 benchmark 上，双刚性 PINN 相对强基线实现预声明增量 | 申请 formal/GPU；仍不称实验验证 |
| oracle 通过、KC′ only 通过 | 保留单模块时间表示论文；E_S′降为消融/支持模块 | 不强行双模块 headline |
| oracle 通过、仅组合通过且交互消融成立 | 主张功能组合或接口协同，不主张两个模块各自独立优越 | 进入匹配 formal 设计 |
| oracle 失败 | 当前三个派生闭合不能承载该事件 | 关闭 R1，申请 R2 |
| 方法无增量 | 当前组合在冻结对象/预算上无增量 | benchmark/evaluator 可作 supporting asset；申请 fallback 或停止 |

## 授权边界

当前只授权读取既有证据、完成 R1 的定向 source cards 与 `FULL_DESIGN` 计划。未授权修改科学代码、生成数据、运行 solver/PINN、训练、formal、GPU、提交、推送或 PR。任何执行必须在 FULL_DESIGN 明确列出科学核心、强基线、关键消融、完整 case/OOD、预算与停止条件后由用户另行批准。
