# 2026-08-26 方法盲 clean-room 对象筛选

## 1. 结论先行

- **唯一组合级判决：`PORTFOLIO_NO_GO`。** 该量词只覆盖 2026-08-26T01:02:21+08:00 冻结的三个新增对象家族、下列 11/12 项新增一手载体和授权包 A 的八个来源硬门；它不证明其他对象不存在，也不把任何历史 No-Go 改名重开。
- 冻结候选顺序为：**(1) Sandia/Charon 3D TaOₓ 应用链；(2) 2026 HfO₂/Al₂O₃ memristive-baffle 链；(3) 2022 graphene/Pt-electrode RRAM array crosstalk 链。** 三者均为 `CANDIDATE_NO_GO`，且最早决定性失败均在 **Gate 3：合同完整性**。
- 候选 1 的两个问题必须分开：**SAND2016-2238J 论文及 SAND2016-11186 报告本身不能闭合自包含 clean-room 合同；Charon v2.2 虽为 GPLv3 官方源码，但不能声称与 2015/2016 应用实现对齐。** 用户手册明确说明相对早期应用所用模型，Poisson formulation 后来已重构，而公开固定仓库中没有该应用的历史 deck/commit。
- 候选 2 的更新 SI 提供二维轴对称几何、方程、部分迁移参数及端口/空间响应，但缺 vacancy 外边界/界面条件、完整电导本构和热参数；此外，模拟的绝对 sweep/pulse 时间协议缺失，且同一模拟堆栈出现 `40 nm` 与 `30 nm` 电极厚度冲突。
- 候选 3 给出器件阵列、多物理方程、主要材料表、`1 V/s` 的绝对 reset 协议以及端口和空间锚点；但它把“other parameters”外引到 Ref. 29，而本轮只能固定该 IEEE 载体的 DOI/摘要元数据，无法核验被引参数、vacancy 边界/界面和完整合同。它也只有单次 reset 事件，set 仅作定性陈述，不能建立重复事件与完整案例生成能力。
- 因候选名单已按预声明规则冻结，三家族预算在第三项失败时耗尽。本轮不将排序较后的 COMSOL proprietary tutorial 临时提升为第四候选，也不为得到正向对象追加家族、补默认参数或跨来源拼接。

状态词：由固定一手载体直接核对的事实记为 `VERIFIED`；由这些事实触发的门禁判断记为 `SUPPORTED_INTERPRETATION`；一手载体未给出且无法合法唯一化的内容记为 `UNKNOWN`。`UNKNOWN` 不以默认值或结果拟合修补。

## 2. 授权边界、方法盲查询与计数规则

本轮仅执行静态一手来源审查并写出本报告：**0 object build、0 solve、0 smoke、0 training、0 PINN、0 GPU、0 formal、0 paid compute、0 dependency install、0 author contact、0 Git 操作**。未运行任何作者程序、模型文件或数值求解器，也未生成新的物理结果；`CTH = NOT_REACHED`。

Pass 1 只使用 live plan 冻结的四个方法中立查询族：

1. `oxide memristor electrothermal oxygen vacancy 2D code data`
2. `RRAM drift diffusion heat equation open source simulation`
3. `oxide phase-field device Joule heating code data`
4. `ferroelectric oxide electrothermal phase-field device open source`

查询、候选生成、排序和逐门判断均未加入拟议学习方法、表示形状或预期方法表现。搜索摘要、综述和聚合页面只用于发现线索；只有论文 version of record、期刊 supplement、作者/机构官方仓库、机构档案或软件供应商正式载体参与门禁事实。

计数以“可独立固定身份的一手载体”为单位；同一论文的 DOI、PMC/OSTI 镜像和 HTML/PDF 不重复计数。候选冻结时已计 9/12 项；深审候选 1 时增加 SAND2016-11186，深审候选 3 时增加其决定性 Ref. 29，最终为 **11/12**。没有为了用满预算继续发现。

## 3. 新增一手来源账本（11/12）

| ID | 固定一手载体 | 日期/版本与许可状态 | 本轮角色 |
|---|---|---|---|
| S1 | Sandia, *TaOx Bipolar Memristor Simulation and Discussion*, SAND2016-2238J；[OSTI 固定 PDF](https://www.osti.gov/servlets/purl/1257786)，[DOI](https://doi.org/10.1149/07203.0049ecst) | 2016；Sandia/OSTI public-release 载体，未把它解释为代码许可证 | 候选 1 的短论文、3D 对象、方程、协议和图示响应 |
| S2 | Charon 官方 [source-code 页面](https://charon.sandia.gov/downloads/source-code/)；GitHub 固定镜像 commit [`c18975483fdf1529e2ce8f7e954e166cccadd90a`](https://github.com/tcadsoftware/charon/tree/c18975483fdf1529e2ce8f7e954e166cccadd90a) | Charon `v2.2.0`，页面/仓库声明 GPLv3；固定镜像最后提交 2022-07-29 | 候选 1 的可用代码身份；不据此推断早期应用 deck |
| S3 | Sandia, [*Charon User Manual: v. 2.2*](https://www.sandia.gov/app/uploads/sites/106/2022/06/Charon_UserManual.pdf), SAND2022-7653 | printed 2022-06-07；Sandia public-release manual | 候选 1 的当前方程身份与“later reformulated”边界 |
| S4 | Kim et al., [*Memristive Baffle Systems: Design, Simulation, and Applications*](https://doi.org/10.1002/advs.202523273), *Advanced Science* 13 (2026)；[PMC VOR](https://pmc.ncbi.nlm.nih.gov/articles/PMC13104148/) | online 2026-03-03，issue 2026-04-23；CC BY 4.0 | 候选 2 的正文、模型叙述、响应锚点与 data-availability |
| S5 | S4 的 [updated Supporting Information](https://pmc-oa-opendata.s3.amazonaws.com/PMC13104148.1/ADVS-13-e23273-s001.pdf) | OA 载体更新 2026-03-12；MD5 `712dfe778d9d160f1e7549c4c4e014ab`，1,883,129 B；随 S4 的 OA 许可链 | 候选 2 的几何、方程、参数、图示和冲突核验 |
| S6 | Saraswat et al., [*Reaction-Drift Model for Switching Transients in Pr0.7Ca0.3MnO3-Based Resistive RAM*](https://doi.org/10.1109/TED.2020.3011387), *IEEE TED* 67 (2020) 3610–3617；[作者稿](https://arxiv.org/abs/2005.07398) | arXiv v1 2020-05-15；IEEE VOR 权利保留，作者稿许可按 arXiv 记录 | Pass 1 发现载体；未进入冻结三家族 |
| S7 | Khot et al., [*Device simulation of ceria-based interfacial switching memristor*](https://doi.org/10.1007/s43207-026-00621-6), *Journal of the Korean Ceramic Society* | published 2026-04-29；本轮未找到可固定的开放模型/代码许可 | Pass 1 发现载体；未进入冻结三家族 |
| S8 | Xie et al., [*Multiphysics Simulation of Crosstalk Effect in Resistive Random Access Memory with Different Metal Oxides*](https://doi.org/10.3390/mi13020266), *Micromachines* 13, 266 (2022)；[PMC VOR](https://pmc.ncbi.nlm.nih.gov/articles/PMC8880066/) | published 2022-02-06；CC BY 4.0 | 候选 3 的正文、材料表、协议与响应锚点 |
| S9 | COMSOL, [*Memristor*, Application ID 141181](https://www.comsol.com/model/memristor-141181)；[6.3 manual](https://doc.comsol.com/6.3/doc/com.comsol.help.models.semicond.memristor/memristor.html) | COMSOL 6.3 tutorial；受 COMSOL Software License Agreement 约束，不是开放源码许可 | Pass 1 高相关但 proprietary 的较后排序载体；未进入冻结三家族 |
| S10 | Sandia, [*Multiphysics Simulation of Memristive Devices with Charon*](https://www.osti.gov/servlets/purl/1331433), SAND2016-11186 | 2016，80 pp；`Unlimited Release` / approved for public release | 深审候选 1 时用于检查完整应用合同 |
| S11 | Xie et al., [*Modeling and Simulation of Resistive Random Access Memory With Graphene Electrode*](https://doi.org/10.1109/TED.2020.2965182), *IEEE TED* 67 (2020) 915–921 | IEEE VOR；本轮公开一手链只固定 DOI/摘要元数据，未发现可读 SI、代码或作者全文 | 候选 3 明确外引的 Ref. 29；只用于记录依赖，不据摘要补参数 |

S6、S7、S9 是合格的一手发现载体，但不是被深审的候选家族；未逐八门判 No-Go。S11 的全文不可达不是“论文不存在”，而是本次固定公开来源链无法核对决定性被引内容。

## 4. Pass 1：冻结候选、顺序与排除边界

### 4.1 冻结时点、名单和排序

候选名单于 **2026-08-26T01:02:21+08:00** 冻结，当时为 9/12 项载体、3/3 个新对象家族。排序严格按 live plan 的优先级，而非按任何预期学习方法表现：

1. **Sandia/Charon 3D TaOₓ application chain**：Sandia 机构论文/报告、官方版本化源码、GPLv3 与手册身份最强；3D 器件、电—热—vacancy 链和端口/空间图示同时存在，故排第一。
2. **2026 HfO₂/Al₂O₃ memristive-baffle chain**：CC BY VOR 与 updated SI、二维轴对称器件、multi-cycle vacancy maps 和 I–V/P–D 锚点较强；但没有作者模型代码，数据需按需索取，故排第二。
3. **2022 graphene/Pt-electrode RRAM array crosstalk chain**：CC BY VOR、二维器件阵列、多材料对照和端口/空间锚点明确；但正文已显露 Ref. 29 参数依赖，主要是单次 reset case，故排第三。

三者不构成同层平手，因此预声明的发布日期/DOI 字典序 tie-break 未被调用。冻结后没有因深审结果或潜在方法适配改变顺序。

### 4.2 与历史家族的实体边界

- 候选 1 虽同属 TaOₓ，但来源、年代、3D Pt/TaOₓ/Ta₂O₅/CF/Pt 拓扑、Charon 代码链和参数合同均不同于已冻结的 2025 Pd/Ta₂O₅/TaOₓ/Pd COMSOL `TaOₓ C1`。因此它是可审的新家族，不是对历史 C1 改名；本报告也不借它重开 C1。
- 候选 2 是 HfO₂/Al₂O₃ multilayer baffle 与 current-regulator stack，来源合同不同于 HFO-NP-v1；它是新家族，不继承 HFO-NP-v1 的任何 PASS/FAIL。
- 候选 3 是 array-level crosstalk 对象，包含 graphene/Pt electrode 与 HfOₓ/TiOₓ/ZrOₓ/NiOₓ 材料轴；它不是历史 VO₂/related-oxide、Q-POP、R1 或 R2/FerroX 的重命名。

### 4.3 未进入冻结三家族的发现线索

- **S6 PCMO reaction-drift**：摘要支持电荷 drift–diffusion、自热和 reaction–drift 内部态，但本轮一手公开链未给出足以优先于前三项的二维及以上器件合同/开放代码身份，故未提升；这不是对 PCMO 全家族的硬门裁决。
- **S7 ceria interfacial model**：发现载体支持界面切换建模，但当前公开链未显示与前三项相当的 Joule-heated 二维闭环和固定代码/数据身份，故未提升；这不是 ceria 全家族 No-Go。
- **S9 COMSOL Application 141181**：官方 6.3 tutorial 实际具有二维轴对称、电—热—vacancy drift–diffusion 和端口/空间输出，相关性很高；但来源身份受 proprietary COMSOL 许可和产品依赖约束，在“来源身份与许可”这一首要排序轴上低于冻结三项。3 家族名单冻结后不允许把它临时升级为第四项。

## 5. Pass 2 统一八门

| Gate | 冻结问题 |
|---|---|
| G1 二维器件 | 是否为二维及以上真实器件基，而非抽象方域、一维或单节点 |
| G2 物理闭环 | 是否闭合电/电流、Joule heating/温度与动态内部态，并有明确反馈 |
| G3 合同完整 | 几何、材料域、IC、BC、界面、单位和关键本构是否可追溯冻结；未知项不得决定核心拓扑或靠结果拟合 |
| G4 绝对协议 | 驱动、持续时间、顺序、history/state carryover 和观测窗是否定义可重放物理时间案例 |
| G5 参数对齐 | 进入因果链的 paper–code–supplement 参数是否无未解释冲突；有限分支必须透明列出 |
| G6 来源响应锚点 | 是否至少同时有一个端口响应与一个空间/内部态响应 |
| G7 身份与许可 | 论文、代码/数据、版本、固定标识、许可及未来 `A/A’-ENGINEERING` 层是否可追溯；对象只称 clean-room `derived/synthetic` |
| G8 可重建与案例能力 | 是否可在不依赖作者私有 raw 的条件下建立独立守恒 oracle、时空收敛、互斥完整 case generator 及 qualification/development/formal OOD 实体隔离 |

作者未发布 raw 全场解或预封案例角色不单独导致 G3/G6 失败；但方程、BC、决定性参数、绝对协议或两类响应锚点缺失仍是硬失败。

## 6. 候选 1：Sandia/Charon 3D TaOₓ application chain

### 6.1 `VERIFIED` 来源对象

S1/S10 描述 3D filamentary Pt/TaOₓ/Ta₂O₅/CF/Pt 器件。S10 给出约 `20 nm` Pt / `50 nm` TaOₓ / `10 nm` Ta₂O₅ / `20 nm` Pt 的层厚、约 `20 nm` device diameter 和 `10 nm` CF diameter。活性 TaOₓ/CF 解 Poisson、electron、oxygen-vacancy transport 与 heat equation，Pt/Ta₂O₅ 解相应电子/热子集；温度 top/bottom 固定 `300 K`、其他外表面 homogeneous Neumann，底端接地、顶端加压，电子/电势在上下端采用 ohmic-contact 处理。

S10 还给出 TaOₓ/CF 初始 vacancy/electron density `1e21 cm^-3`、Pt electron density `1e21 cm^-3` 与 `300 K` 初温；RESET 例包括 `−1` 至 `−1.5 V`、最长约 `1 s`，SET 与三角扫例含 `1`、`1.5`、`2 V/s`。来源响应同时包含端口电流/电阻/I–V 与 vacancy/electron/temperature 的空间截面或三维图。

### 6.2 决定性区分 A：论文/报告能否独立闭合合同

`VERIFIED`：S1 是短 proceedings paper；S10 虽增加几何、IC/BC、波形和响应图，但没有列出独立重建所需的完整材料/本构数值集。S10 对早期结果明确说明没有进行实验 calibration，后续主要改变 filament radius、mobility 和 maximum vacancy density；其 vacancy-density 上限被描述为带有任意性。图示电流/时间响应不能反向唯一确定这些缺失量。

`SUPPORTED_INTERPRETATION`：**S1 单独不完整，S1+S10 仍不构成自包含 clean-room contract。** 缺失项进入电流、热源、迁移和饱和行为的因果链，不能作为无关 nuisance parameter 留待任意选择。因此 **G3 = FAIL**，这是最早决定性失败。

### 6.3 决定性区分 B：Charon v2.2 能否声称对齐早期应用

`VERIFIED`：S2/S3 固定了 Charon v2.2 的官方代码/手册身份。S3 说明当前 non-isothermal memristor capability 包含 Poisson、electron/hole、oxygen vacancy 与 heat equations，但同时明确记载该模型的 Poisson equation 相对 2015/2016 引用应用后来经过 reformulation。S2 的固定公开镜像只有当前少量提交；本轮未发现 S1/S10 对应的历史 input deck、application commit 或逐项 paper-to-code 参数表。

`SUPPORTED_INTERPRETATION`：Charon v2.2 可证明“后来版本有相近能力”，不能证明“当前实现就是 2015/2016 论文所运行的 canonical application”。若把 S2/S3 强接到 S1/S10，会引入未封存的实现分支。故 **G5 = FAIL（未建立对齐，不声称已发现数值冲突）**。这是一项独立次级失败，不改变最早的 G3。

### 6.4 八门矩阵与判决

| Gate | 判决 | 直接依据与边界 |
|---|---:|---|
| G1 | PASS | S1/S10 的 3D filamentary real-device stack |
| G2 | PASS | Poisson/electron/vacancy/heat coupling；Joule/self-heating 与 T-dependent transport |
| G3 | **FAIL（最早）** | S1+S10 缺完整材料/本构数值与可唯一化 calibration；arbitrary vacancy cap 进入因果链 |
| G4 | **FAIL / PARTIAL** | 可定位 RESET/SET 和三角扫的绝对电压、时间/速率示例，但没有冻结从初始化到各阶段的唯一顺序与 state carryover；分配初态的分离算例不能自动拼成完整 canonical history |
| G5 | **FAIL** | v2.2 手册声明模型后来重构；无早期 application deck/commit，不能声称版本对齐 |
| G6 | PASS | 端口 I–V/R(t) + 空间 vacancy/electron/T 图 |
| G7 | PASS / CONDITIONAL | Sandia 固定报告、GPLv3 Charon v2.2 可追溯；未来对象只能是 clean-room `derived/synthetic`，不能称作者原生重放 |
| G8 | **FAIL** | G3/G5 阻止独立 canonical oracle；3D 计算负担、缺 case generator/实体角色也是现实限制 |

**候选级判决：`CANDIDATE_NO_GO_C1_GATE3_INCOMPLETE_SELF_CONTAINED_CONTRACT`。** 该判决只关闭这条 S1+S10+v2.2 公开链，不覆盖其他 TaOₓ 家族。

## 7. 候选 2：2026 HfO₂/Al₂O₃ memristive-baffle chain

### 7.1 `VERIFIED` 来源对象与锚点

S4/S5 描述 HfO₂/Al₂O₃ multilayer VCM baffle system。S5 Figure S1 给出二维轴对称模型，包括约 `10 nm` current regulator、`40 nm` TiN、`40 nm` Pt、`14 nm` switching layer、约 `7 nm` CF radius，并将电极外端固定为 `293.15 K`。方程包括 oxygen-vacancy transport、current continuity 和带 Joule heating 的 Fourier heat equation。

S5 列出的明确扩散参数主要对应 monoclinic HfO₂：`D0 = 2.86e−7 m²/s`、`Ea = 0.70 eV`、correlation factor `0.32`、attempt frequency `5.24 THz`、hopping distance `2.67 Å`、effective charge `4.58`。S4/S5 同时提供 I–V、potentiation/depression、cycles 1/5/10 的二维 vacancy maps 以及温度/电场分布，故两类来源响应锚点存在。S4 的 data-availability 是按合理请求提供，不是公开固定 raw。

### 7.2 最早失败 G3：合同缺口

`VERIFIED`：S4/S5 未给出 oxygen-vacancy 在所有外边界、金属/oxide 和 multilayer interface 的完整 BC/continuity/flux 规则；没有给出可复算的完整 conductivity function/数据（包括决定幅值的 `sigma0` 链）；也没有列出各域热传导所需的完整 `rho`、`Cp`、`k` 数值集。

`SUPPORTED_INTERPRETATION`：这些量分别决定 vacancy 守恒、层间输运、电流与 Joule source、热扩散和温度反馈，不能靠图像拟合或通用材料手册拼接。因此 **G3 = FAIL**，是最早决定性失败。作者 raw 或预封 case 缺失没有被当作本门失败理由。

### 7.3 独立失败 G4：模拟绝对协议缺失

`VERIFIED`：S4/S5 的模拟图给出电压范围、cycle number 与 P/D 序列，但未给出动态模拟的绝对 sweep rate、每段 duration/time step、完整 history/state carryover 或模拟 P/D pulse width。文中可见的 `1 ms`、`0.8 μs` 等脉宽属于实验测量协议，来源没有把它们指定为模拟加载。

`SUPPORTED_INTERPRETATION`：实验脉宽不能自动复制为模拟协议；缺绝对时间时，T-dependent vacancy transport 与 Joule feedback 的同一曲线并非唯一物理案例。故 **G4 = FAIL**。

### 7.4 独立失败 G5：同一堆栈几何冲突

`VERIFIED`：S4 主文/Figure 1 与 S5 Figure S1 给出上下电极 `40 nm`；S5 p.15 / Figure S7 的模拟说明却把相同 TiN/Pt 电极写为 `30 nm`。更新 SI 没有给出二者分别对应不同模型版本的解释。

`SUPPORTED_INTERPRETATION`：这是有限但未标注的几何分支。不能选择 `30 nm` 或 `40 nm` 冒充唯一 canonical 合同，故 **G5 = FAIL**；最早失败仍为 G3。

### 7.5 八门矩阵与判决

| Gate | 判决 | 直接依据与边界 |
|---|---:|---|
| G1 | PASS | 2D-axisymmetric real multilayer device stack |
| G2 | PASS | current continuity + Joule-heated heat equation + vacancy transport/feedback |
| G3 | **FAIL（最早）** | vacancy BC/interface、完整 conductivity 与 `rho/Cp/k` 缺失 |
| G4 | **FAIL** | 无模拟绝对 sweep/pulse 时间、完整顺序/history；实验脉宽不替代模拟合同 |
| G5 | **FAIL** | 同一模拟电极 `40 nm` vs `30 nm`，无版本解释 |
| G6 | PASS | I–V/P–D 端口 + vacancy/T/E 空间图和多 cycle state maps |
| G7 | PASS / CONDITIONAL | S4/S5 为可固定 CC BY 链；无公开作者模型代码/固定 raw，未来只能称 clean-room `derived/synthetic` |
| G8 | **FAIL** | G3/G4/G5 阻止独立 oracle/case generator；来源还明确提示单 cycle simulation 计算耗时 |

**候选级判决：`CANDIDATE_NO_GO_C2_GATE3_INCOMPLETE_BOUNDARY_CONSTITUTIVE_THERMAL_CONTRACT`。** 该判决只关闭 S4/S5 公开链，不覆盖 HfO₂/Al₂O₃ 或 baffle 设计的一切可能版本。

## 8. 候选 3：2022 graphene/Pt-electrode RRAM array crosstalk chain

### 8.1 `VERIFIED` 来源对象、协议与锚点

S8 建模包含 graphene-electrode (GE-RRAM) 与 Pt-RRAM 的器件阵列 crosstalk。模型用 finite-difference 形式耦合 current continuity、oxygen-vacancy drift–diffusion 和 heat conduction；diffusivity 采用 Arrhenius T dependence，电/热导率依赖 vacancy density 与 temperature。

S8 Table 1 对 HfOₓ/TiOₓ/ZrOₓ/NiOₓ 给出 oxide/electrode thermal conductivity、oxide/electrode electrical conductivity、相应 activation energy、`D0` 与 vacancy migration `Ea`。它还给出 `6 nm` CF diameter、`6 nm` oxide thickness、CF initial vacancy density `1.2e27 m⁻³`、reset depletion threshold `0.6e27 m⁻³`。

绝对 bad-case reset 协议可定位：pillar voltage 从 `0 V` 以 `1 V/s` 上升；上下 active planar electrodes 接地，中间 inactive electrode 跟随 pillar；上下表面 `300 K`，侧边 Neumann/adiabatic；结果窗口到 `0.2 s / 0.2 V`。来源给出材料别 reset voltage、victim-cell temperature、spacing threshold，以及 temperature/vacancy maps 和 inactive-cell 轴向 vacancy profiles。

### 8.2 最早失败 G3：决定性参数外引而公开链不可闭合

`VERIFIED`：S8 在列出部分条件后明确声明其余参数与 Ref. 29 相同。Ref. 29 即 S11。S11 是同一团队的 GE-RRAM electrothermal/vacancy 模型论文，但本轮公开一手链只能固定 DOI/摘要元数据；未发现可读的 author manuscript、supplement、model code 或参数表。

因此，S8 没有在自身载体内完整给出被外引的其余几何、边界/界面、本构与数值参数，尤其无法从公开链唯一核对 vacancy boundary/interface rules 及所有进入 crosstalk 因果链的值。

`SUPPORTED_INTERPRETATION`：**S11 被计为来源载体，不代表其未读正文可以被模型回忆或二手摘要代填。** 对公开可复核的 clean-room 合同，决定性外引仍未闭合，故 **G3 = FAIL**，是最早决定性失败。

### 8.3 其余门的独立判断

- **G4 = PASS（仅限文中冻结的单一 bad-case reset）**：`0→0.2 V`、`1 V/s`、`0→0.2 s`、初态、电/热边界和观测窗足以定义该单次 reset。该 PASS 不扩展到 set；S8 只说 set crosstalk trend 类似，没有给出等价的完整 set 仿真协议/结果。
- **G5 = FAIL / alignment unavailable**：没有发现与 S8 同时固定的代码/SI，且 S11 的被引参数正文不可核对。这里不声称发现具体 paper–paper 数值冲突，只记录预声明的参数对齐无法建立。
- **G6 = PASS**：reset voltage/temperature/spacing response 是端口或 case-level 响应；vacancy/temperature maps 与轴向 vacancy profile 是空间/内部态锚点。
- **G8 = FAIL**：来源没有公开生成器、mesh/time-step convergence 或 solver-accuracy 证据；只有单次 reset threshold crossing，set 未完整模拟，没有局部重复事件，也没有 qualification/development/formal OOD 的完整实体角色。缺 author raw 本身不是失败理由；失败来自合同与案例能力无法建立。

### 8.4 八门矩阵与判决

| Gate | 判决 | 直接依据与边界 |
|---|---:|---|
| G1 | PASS | device-array cross-section / 2D finite-difference spatial model，不是单节点 |
| G2 | PASS | current + Joule/heat + vacancy transport，且系数有 T/state feedback |
| G3 | **FAIL（最早）** | “other parameters”外引 S11；公开固定链无法核验决定性参数、vacancy BC/interface 与完整合同 |
| G4 | PASS / LIMITED | 唯一 bad-case reset 的 `1 V/s`、`0–0.2 s` 与 BC/观测窗可重放；不覆盖 set |
| G5 | **FAIL** | S11 参数链与任何代码/SI 均不可核验；alignment unavailable，不编造具体冲突 |
| G6 | PASS | reset/temperature/spacing responses + vacancy/T maps/profiles |
| G7 | PASS / CONDITIONAL | S8 为固定 CC BY VOR；S11 权利保留且仅元数据可达；未来对象只能称 clean-room `derived/synthetic` |
| G8 | **FAIL** | 无公开 generator/convergence；单次 reset、set 不完整、无重复事件和完整 case/OOD 实体能力 |

**候选级判决：`CANDIDATE_NO_GO_C3_GATE3_UNCLOSED_REF29_PARAMETER_CHAIN`。** 该判决只关闭 S8+当前可达 S11 的公开链，不证明 GE-RRAM、Pt-RRAM 或四种 oxide 材料普遍失败。

## 9. 组合级收口

| 冻结顺序 | 对象家族 | 最早硬失败 | 独立次级失败 | 候选 verdict |
|---:|---|---|---|---|
| 1 | Sandia/Charon 3D TaOₓ | G3：paper/report 非自包含合同 | G4：完整 history/carryover 未冻结；G5：Charon v2.2 与早期应用未对齐；G8 | `CANDIDATE_NO_GO` |
| 2 | 2026 HfO₂/Al₂O₃ baffle | G3：BC/interface/电导/热参数缺失 | G4：绝对模拟协议；G5：40/30 nm 冲突；G8 | `CANDIDATE_NO_GO` |
| 3 | 2022 RRAM array crosstalk | G3：Ref. 29 决定性参数链未闭合 | G5：alignment unavailable；G8：单次 reset/无生成器 | `CANDIDATE_NO_GO` |

**`VERIFIED` 计数：3/3 个冻结家族均未通过全部八门；11/12 个新增一手载体已计；没有 `OBJECT_SOURCE_PASS_AND_LOCKED`。** 根据预冻结停止规则，三家族 deep-review 预算已耗尽，故本次唯一组合级状态为：

> **`PORTFOLIO_NO_GO_PACKAGE_A_FROZEN_3_FAMILIES_11_CARRIERS`**

其证据边界如下：

1. 它只关闭本次冻结组合和当前论文路线，不把 `CANDIDATE_NO_GO` 外推为材料、数值 PDE、神经方法或整个文献空间的普遍失败。
2. 排序较后的 S9 不自动晋升；S6/S7 也不自动变为新候选。任何新家族都需要新的明确 PLAN 与授权，不得在本包中救援式追加。
3. 没有对象通过，故对象后 novelty 前门、oracle、事件资格、strong-raw、`CTH`、任何方法比较、pilot、formal OOD 与论文性能主张均保持 `NOT_REACHED` / `NOT_AUTHORIZED`。
4. 本报告保留的是有界来源负证据：三条看似具备电—热—内部态与空间响应的来源链，均在任何求解之前因决定性合同不可唯一化而失去 clean-room oracle 前提。

## 10. 可独立复核的决定性链接

- 候选 1：[SAND2016-2238J / OSTI](https://www.osti.gov/servlets/purl/1257786)、[SAND2016-11186 / OSTI](https://www.osti.gov/servlets/purl/1331433)、[Charon v2.2 source](https://charon.sandia.gov/downloads/source-code/)、[Charon v2.2 manual](https://www.sandia.gov/app/uploads/sites/106/2022/06/Charon_UserManual.pdf)。
- 候选 2：[Advanced Science VOR](https://pmc.ncbi.nlm.nih.gov/articles/PMC13104148/)、[updated Supporting Information](https://pmc-oa-opendata.s3.amazonaws.com/PMC13104148.1/ADVS-13-e23273-s001.pdf)。
- 候选 3：[Micromachines VOR](https://pmc.ncbi.nlm.nih.gov/articles/PMC8880066/)、[explicit Ref. 29 DOI](https://doi.org/10.1109/TED.2020.2965182)。

本报告没有实施任何对象，也没有开展对象后方法特异的新颖性审查。
