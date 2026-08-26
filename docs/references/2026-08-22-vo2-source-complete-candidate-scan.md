# VO₂ 来源闭合二维候选有界扫描

- 扫描日期：2026-08-22
- 阶段标记：`SOURCE_SCAN_COMPLETE_AWAITING_OBJECT_APPROVAL`
- 结果：`BOUNDED_ZERO_CANDIDATE`
- 通过数：`0/6`
- 查询终止原因：四个预声明查询族在本次预算内耗尽，未发现第三方可直接复核的硬门通过对象
- 科学状态：全部候选均为 `PROPOSED_NOT_AUTHORIZED`；KC 实际增量仍为 `UNKNOWN`
- 执行边界：未运行 solver、PINN、训练、数值 pilot、GPU 或付费计算；未克隆仓库、安装依赖、联系作者或拼接来源

## 1. 结论

`VERIFIED`：本次有界扫描没有找到同时满足下列条件的 VO₂ 二维数值对象：

1. 一手论文与物理对象身份明确；
2. 同一来源链给出固定版本、公开且有明确软件许可证的实现；
3. 几何、接触、边界、驱动、方程、参数和状态语义闭合；
4. 能从该实现再生成完整参考输出；
5. 输出包含至少两个周期的空间异步、局部、部分覆盖且可恢复的结构相事件；
6. 可在不复用 PINN 残差实现的前提下独立资格化，并能形成 qualification、development、formal OOD 和 reserve 四个互斥完整案例角色。

`VERIFIED`：六个深审对象全部触发 ADR 0022/0024 的至少一项一票否决，因此没有冻结候选顺序，也没有活动对象。

`SUPPORTED_INTERPRETATION`：当前缺口不是“VO₂ 没有合适的空间结构事件”，而是两类证据没有在同一可执行来源链内相交：

- Q‑POP 最接近公开、固定版本且许可明确的可执行二维对象，但现有官方参考不能证明目标结构事件通过资格门，也不能支持四角色完整案例池；
- 2023–2026 年的若干工作给出了更接近目标的局部结构成核、传播、恢复、频率依赖或周期记忆现象，但其相应数值实现没有以固定版本和软件许可证公开，或仅存在于专有 COMSOL 工程中且工程文件未公开。

`UNKNOWN`：若把材料范围扩展到相关氧化物 PCM/忆阻器体系，能否找到硬门通过对象。本报告不授权该扩展。

## 2. 扫描合同与方法

### 2.1 固定查询族

本次只使用以下四个查询族；同义词和 DOI/仓库反查属于族内收敛，不另增查询族：

1. `QPOP official chain`：Q‑POP 论文、CPC 程序归档、作者仓库、固定提交、许可证、官方文档与随包输出；
2. `VO2 2D electrothermal/phase-field`：VO₂ 二维电—热—相场、序参量、载流子与器件动力学；
3. `VO2 spatial domain/filament/nucleation-propagation-recovery`：局部结构畴、细丝、成核—传播—恢复及重复周期；
4. `VO2 2D device/memristor multiphysics`：二维器件、忆阻器、电热网络和多物理场实现。

### 2.2 一票否决

每个“对象”是论文、实现、版本、许可证、输入合同与输出的同一来源链，不是主题相近论文的组合。以下任一项失败即为硬 `FAIL`：

- 无公开实现、无固定版本或无明确软件许可证；
- 需要从另一篇论文、通用框架或本项目旧模型补入缺失方程、参数、几何、接触或边界；
- 不能从公开实现再生成完整参考输出；
- 没有至少两个周期的合格结构事件证据；
- 无法建立独立资格化与四角色完整案例池；
- 不是二维对象，或物理语义改变后才可能满足目标。

论文开放许可只覆盖论文本身，不自动构成缺失求解器代码的软件许可证。实验数据可用于外部一致性检查，但不自动成为本项目的数值 oracle 或训练标签。

### 2.3 终止规则

预声明上限是四个查询族、六个深审对象，达到三个硬门通过对象或查询族耗尽即停止。本次深审六个对象后，各族只再出现以下非候选重复类型：无公开求解器的论文、实验数据集、通用相场框架、专有 COMSOL 示例、SPICE/集总模型或对同一 MRN 文献链的重复引用。因此按合同以“查询族在预算内耗尽”终止。该结论是有界扫描结果，不宣称对全部 VO₂ 文献作全局穷尽。

## 3. 总表

| ID | 对象 | 最强正面证据 | 首个硬否决 | 事件门 | 四角色池 | 裁决 |
|---|---|---|---|---|---|---|
| C1 | Q‑POP 2025 官方软件链 | 论文、CPC v1、固定提交、MIT、二维耦合 PDE | 官方参考输出未闭合；未证明结构序参量至少两周期合格事件 | `FAIL` | `FAIL` | `FAIL` |
| C2 | 2018 PR Materials VO₂ 相场模型 | 结构/电子序参量与载流子耦合 | 无公开固定实现、软件许可证和可再生成输出 | `FAIL` | `FAIL` | `FAIL` |
| C3 | 2023 PRB 氧空位氧化还原相场模型 | 局部缺陷成核、细丝局部切换和重复振荡 | 无公开固定实现、软件许可证和官方数值输出 | `SUPPORTED_BUT_NOT_EXECUTABLE` | `FAIL` | `FAIL` |
| C4 | 2026 Nature Communications 结构动力学 + MRN | 局部畴形成/溶解、部分恢复、二维截面 MRN | MRN 代码、固定版本、软件许可证和精确缩放合同未公开 | `SUPPORTED_EXPERIMENTALLY` | `FAIL` | `FAIL` |
| C5 | 2025 ACS Nano 结构显微 + MRN 周期记忆 | 三周期结构细丝/记忆及 MRN 重现 | MRN 代码、固定版本、软件许可证和完整参数未公开 | `OFF_TARGET_RECOVERY` | `FAIL` | `FAIL` |
| C6 | 2026 Huang 等 3D COMSOL 电热—相场 | 空间结构拓扑与倍周期动力学 | 3D、专有环境、工程/代码/数据未公开且数据需联系作者 | `SUPPORTED_BUT_WRONG_OBJECT` | `FAIL` | `FAIL` |

## 4. 深审对象

### C1. Q‑POP 2025 官方软件链

**身份与来源**

- 论文：*Q‑POP: A phase-field modeling framework for Mott memristors*，Computer Physics Communications 315 (2025) 109751，DOI [`10.1016/j.cpc.2025.109751`](https://doi.org/10.1016/j.cpc.2025.109751)。
- CPC 程序归档：Mendeley Data v1，发布于 2025-07-21，DOI [`10.17632/p3395559s6.1`](https://doi.org/10.17632/p3395559s6.1)，MIT。
- 作者仓库：[`DOE-COMMS/Q-POP-Modules`](https://github.com/DOE-COMMS/Q-POP-Modules)；CPC v1 内嵌固定提交 [`6047117bb9f40355db260aae59ec427de2050b94`](https://github.com/DOE-COMMS/Q-POP-Modules/commit/6047117bb9f40355db260aae59ec427de2050b94)，对应 [`MIT license`](https://github.com/DOE-COMMS/Q-POP-Modules/blob/6047117bb9f40355db260aae59ec427de2050b94/LICENSE)。
- 官方方程、输入与字段文档：[`Formulation`](https://q-pop.pages.dev/formulation)、[`Examples`](https://q-pop.pages.dev/examples)、[`Visualization`](https://q-pop.pages.dev/visualization)。
- 本项目既有逐文件审计：[物理合同与来源审计](qpop_physical_contract_source_audit_2026-08-21.md)、[benchmark/evaluator 审计](qpop_source_benchmark_evaluator_audit_2026-08-19.md)。

**闭合与事件审计**

`VERIFIED`：固定软件链给出二维矩形 VO₂ 器件、外部电路以及电子序参量、结构序参量、电势、温度和载流子等耦合场；随包示例明确给出 100 × 40 × 20 nm 几何、100 × 40 网格、9 V、500 kΩ、0 nF、热耗散系数、2000 ns 目标时长和局部成核设置。公开说明还展示电子序参量对应的金属细丝反复生长和收缩。

`VERIFIED`：CPC v1 随包参考只到 512.0793 ns，早于 2000 ns 目标，且缺少完成尾标；公开链没有独立官方 evaluator。

`UNKNOWN`：电子序参量细丝的重复变化是否同时构成结构序参量 `eta` 至少两个周期、空间异步、局部、部分覆盖、恢复且离散收敛的合格事件。现有随包输出不能直接证明该命题。

**四角色池与缺失因果量**

- 只有一个主要公开示例，且该参考输出本身未完成；没有来源冻结的 qualification/development/formal OOD/reserve 完整案例分组。
- 不能把参数可调等同于存在无泄漏的完整案例池；自行补造案例会形成尚未资格化的新派生对象。
- 缺少目标结构事件的收敛证据、完整多周期参考输出、独立评分合同和来源冻结的实体级拆分。

**硬裁决：`FAIL`。** 原因不是代码不可运行，而是目标结构事件、完整参考输出和四角色池未在同一官方链内闭合。历史本地 Q‑POP raw/PINN 负面结果既不修复也不制造这一来源裁决。

### C2. 2018 PR Materials 结构—电子相场模型

**身份与来源**

- Yin Shi、Long-Qing Chen，*Phase-field model of insulator-to-metal transition in VO₂ under an electric field*，Physical Review Materials 2, 053803 (2018)，DOI [`10.1103/PhysRevMaterials.2.053803`](https://doi.org/10.1103/PhysRevMaterials.2.053803)，2018-05-23；[`APS accepted manuscript`](https://link.aps.org/accepted/10.1103/PhysRevMaterials.2.053803)。

**闭合与事件审计**

`VERIFIED`：论文耦合结构与电子不稳定性及载流子，并在约 250 nm VO₂ 薄层上研究外加均匀电场下的畴状态。它是后续 Q‑POP 物理链的重要基础。

`VERIFIED`：在本次有界扫描中未发现作者或机构发布的固定代码版本、软件许可证、可再生成官方输出或独立 evaluator。

`VERIFIED`：研究对象不是带显式电极、接触、衬底热沉和外部电路的重复动态二维器件案例，未提供至少两个形成—恢复周期的目标结构事件证据。

**缺失因果量**

- 器件几何、真实接触与热边界、外部驱动/电路；
- 动态时间合同、网格/步长/求解容差和完整参数化输入；
- 固定实现、代码许可证、可再生成输出和四角色案例池。

**硬裁决：`FAIL`。** 论文物理价值不能替代可执行来源闭合。

### C3. 2023 PRB 氧空位氧化还原相场模型

**身份与来源**

- Yin Shi、Venkatraman Gopalan、Long-Qing Chen，*Phase-field model of coupled insulator-metal transitions and oxygen vacancy redox reactions*，Physical Review B 107, L201110 (2023)，DOI [`10.1103/PhysRevB.107.L201110`](https://doi.org/10.1103/PhysRevB.107.L201110)，2023-05-15；[`APS accepted manuscript`](https://link.aps.org/accepted/10.1103/PhysRevB.107.L201110)。

**闭合与事件审计**

`VERIFIED`：论文在结构序参量、电子序参量、温度、电势和载流子之外加入中性/离化氧空位场，模拟 VO₂ 薄膜与串联电阻；局部缺陷区作为成核位置，只有细丝附近发生切换，并展示重复自振荡。就事件形态而言，它比 C1/C2 更接近“局部、部分覆盖、可恢复”。

`VERIFIED`：本次有界扫描没有找到对应扩展模型的作者/机构公开实现、固定版本、软件许可证或官方可再生成数值输出。论文把部分细节指向前作；按 ADR 0022，不得用后来的基础 Q‑POP 仓库或另一论文替它补齐扩展缺陷模型。

`UNKNOWN`：论文中的结构场在至少两个完整周期是否满足本项目预注册的空间、时间和离散收敛资格门；没有公开可执行对象可独立检验。

**缺失因果量**

- 氧空位扩展模型的固定源代码、精确输入、缺陷场初/边值和数值控制；
- 许可证、官方完整输出、独立 evaluator 和四角色完整案例池；
- 可复核的结构事件离散收敛证据。

**硬裁决：`FAIL`。** 这是“事件物理相关但对象不可执行”的失败，不是对论文结果的否定。

### C4. 2026 Nature Communications 结构 Mott–Peierls 动力学 + MRN

**身份与来源**

- Pofelski 等，*Switching speed limits in electrically driven VO₂ structural Mott–Peierls transition*，Nature Communications 17, 3139 (2026)，DOI [`10.1038/s41467-026-69904-0`](https://doi.org/10.1038/s41467-026-69904-0)，2026-02-24 发布、2026-04-01 版本记录，文章为 CC BY 4.0。
- 公开实验/分析资料：UTEM 原始数据 [`Zenodo 18554592`](https://zenodo.org/records/18554592)；相图原始数据与机器学习分析代码 [`Zenodo 14767722`](https://zenodo.org/records/14767722)。
- 本项目既有来源审计：[EAF/KC 前沿来源审计](eaf_kc_front_source_audit_2026-08-21.md)。

**闭合与事件审计**

`VERIFIED`：时间分辨显微结果直接显示局部金属畴形成与溶解、占空比相关恢复，以及中等频率下部分恢复。论文的二维截面 Mott Resistor Network（MRN）在任意单位下定性重现实验结构动力学，并报告随机局部切换和频率依赖。

`VERIFIED`：公开 Zenodo 项目是实验原始数据和相图分析代码，不是 MRN 求解器。扫描未发现 MRN 的固定公共实现、软件许可证或可再生成数值输出包。论文明确用实验数据缩放空间和时间，且模型与实验仍有差异；这不足以冻结独立数值 oracle。

`VERIFIED`：文章 CC BY 4.0 不等同于未公开 MRN 代码的软件许可证。

**缺失因果量**

- MRN 固定代码、精确网格、随机分布与 seed、数值步进和完整参数；
- 从实验几何/驱动到任意单位模型的唯一缩放映射；
- 电极实际波形、寄生反射、接触与衬底热耦合的闭合数值合同；
- 可再生成多完整案例输出、独立 evaluator 和四角色池。

**硬裁决：`FAIL`。** 实验事件非常相关，但实验与分析数据不能替代缺失的数值 oracle 实现。

### C5. 2025 ACS Nano 全场结构显微 + MRN 周期记忆

**身份与来源**

- *High-Resolution Full-Field Structural Microscopy of the Voltage-Induced Filament Formation in VO₂-Based Neuromorphic Devices*，ACS Nano (2025)，DOI [`10.1021/acsnano.4c14696`](https://doi.org/10.1021/acsnano.4c14696)，2025-04-14 在线发布，文章为 CC BY 4.0。
- 公开补充材料：[`ACS Figshare 28788744`](https://acs.figshare.com/articles/journal_contribution/High-Resolution_Full-Field_Structural_Microscopy_of_the_Voltage-Induced_Filament_Formation_in_VO_sub_2_sub_Based_Neuromorphic_Devices/28788744)。

**闭合与事件审计**

`VERIFIED`：论文用全场结构显微观察电压循环中的细丝与结构记忆，并用 MRN 模拟三个循环。模型通过引入约 0.09% 的现象学低转变温度“卡住”概率，使阈值降低与实验匹配。

`VERIFIED`：公开补充材料是论文 supporting information，不是固定 MRN 源代码仓库。扫描未发现 MRN 实现、软件许可证、完整参数文件、随机状态或可再生成输出包。

`SUPPORTED_INTERPRETATION`：该对象强调跨循环累积记忆和残留低转变温度位点，不等同于本项目要求的每周期局部、部分覆盖且可恢复事件；即使代码公开，也仍需先重新资格化事件语义。

**缺失因果量**

- MRN 网格/几何、热边界、全部材料参数、收敛流程和随机 seed；
- 现象学概率的冻结依据与未调参外推行为；
- 固定实现、软件许可证、官方输出、独立 evaluator 和四角色池。

**硬裁决：`FAIL`。** 同时触发实现/许可证否决与目标恢复语义不闭合。

### C6. 2026 Huang 等 3D COMSOL 电热—相场对象

**身份与来源**

- Huang 等，*Electrically steered conduction topologies and period-doubling phase dynamics in VO₂*，arXiv:2604.19329，2026-04-21；[`摘要页`](https://arxiv.org/abs/2604.19329) 与 [`PDF`](https://arxiv.org/pdf/2604.19329)。

**闭合与事件审计**

`VERIFIED`：论文方法使用 COMSOL Multiphysics 6.0 的三维电热模型，并以 Solid Mechanics 与 Weak Form PDE 建立三维相场模型；结果包含空间结构拓扑和倍周期相动力学，物理现象与目标高度相关。

`VERIFIED`：对象是三维专有 COMSOL 模型，不是本次要求的公开二维对象。论文声明数据可向通讯作者合理请求，但没有公开数据链接、COMSOL 工程、固定代码版本或软件许可证。本次合同禁止联系作者。

`VERIFIED`：把该三维对象自行降维、重写为开源求解器或补造边界/材料函数会形成新的派生对象，不能作为本对象通过来源闭合的依据。

**缺失因果量**

- COMSOL 工程文件、材料函数、网格、步长、求解设置和完整输出；
- 可公开复用的软件许可证与无需作者介入的固定归档；
- 被证明等价的二维合同、独立 evaluator 和四角色池。

**硬裁决：`FAIL`。** 同时触发维度、公开实现、许可和免联系可获得性否决。

## 5. 仅初筛、未计入六个深审对象

以下结果在身份层即不满足目标，未占深审名额，也未用于补齐任何候选：

- Brown 等 2023 的 VO₂ 局部活动/振荡模型：是紧凑或集总动力学，不提供目标二维空间结构 oracle；论文入口 [`PubMed 36165218`](https://pubmed.ncbi.nlm.nih.gov/36165218/)。
- PRISMS-PF 等通用相场框架：框架不是经来源冻结的 VO₂ 器件物理对象。
- COMSOL 官方通用忆阻器示例：专有、材料/物理对象不匹配，且不是同一 VO₂ 来源链。
- SPICE、比较器和单节点弛豫振荡器：没有二维空间结构事件。
- “Universal Phase Dynamics” 等实验数据/分析代码：可用于外部物理参照，但不包含数值求解器；例如 [`Zenodo 4781957`](https://zenodo.org/records/4781957)。

## 6. 对 KC 论文路线的直接含义

1. `VERIFIED`：没有对象进入冻结排序，本次只读扫描没有启动科学路线；后续全局路线次数上限已由 ADR 0027 撤销。
2. `VERIFIED`：不得启动 oracle 资格化、strong-raw、KC、第二模块、formal、GPU 或任何组合实验。
3. `UNKNOWN`：KC 在合格空间异步、局部、部分覆盖且可恢复结构事件上的实际增量；本次零候选既不是 `KC_FAIL`，也不是 `RAW_INCOMPETENT_ROUTE_NO_TEST`。
4. `VERIFIED`：C1 Q‑POP 是本次最接近来源闭合的对象，但不能因“最接近”而降格硬门；C3/C4/C6 是事件物理最相关的线索，但不能因事件漂亮而忽略代码、许可与输出缺口。
5. `SUPPORTED_INTERPRETATION`：继续在同一 VO₂ 范围重复检索的预期信息增量很低；四个族的新增命中已收敛为同一批无代码论文、实验数据或重复 MRN 引用。

既有 substrate、strong-raw 与方法瓶颈的证据边界见 [多 substrate 方法就绪性负面报告](../experiment/2026-08-21-multi-substrate-method-readiness-negative-report.md)；本次来源扫描不改变其中任何科学裁决。

## 7. 终局与唯一待决策项

- 终局：`BOUNDED_ZERO_CANDIDATE`
- 阶段：`SOURCE_SCAN_COMPLETE_AWAITING_OBJECT_APPROVAL`
- 候选清单：空
- 冻结顺序：不适用
- 数值授权：`false`
- 正面方法结论：无
- 实验验证主张：无
- 下一项且仅一项用户决策：**是否把来源闭合扫描的材料范围扩展到相关氧化物 PCM/忆阻器体系。**

若未获得该扩展授权，研究保持阻塞；不得把 C1–C6 中任何对象降格准入，也不得继续更换几何、闭合、网络或 substrate 进行正式运行。

## 8. 可获得性与盲区

- APS、ACS、Nature、arXiv、Mendeley Data、GitHub、项目官方文档和 Zenodo 的可公开页面均已核验；部分网页反爬页面改用同一发布方的可索引正文、accepted manuscript、PDF 或正式归档交叉核验。
- “本次未发现公开代码”严格限定为上述四族、日期和预算；它不证明作者从未私下保存代码，也不证明未来不会公开。
- 请求作者数据、订阅/付费附件、未公开补充文件和专有 COMSOL 工程均超出授权，未尝试获取。
- 本报告只裁决候选是否满足项目来源闭合合同，不裁决各论文的学术正确性、优先权或实验可信度。
