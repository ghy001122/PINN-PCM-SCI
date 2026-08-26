# 相关氧化物来源闭合二维候选有界扫描

- 扫描日期：2026-08-22
- 授权：`USER_APPROVED_RELATED_OXIDE_SOURCE_SCAN_2026-08-22`
- 阶段标记：`PHASE_A_SOURCE_SCAN_COMPLETE`
- 结果：`EXPANDED_OXIDE_ZERO_CANDIDATE`
- 通过数：`0/8`
- 查询终止原因：四个冻结查询族在八个深审对象预算内耗尽，未发现六门同链闭合对象
- 科学状态：全部对象均为 `FAIL`；KC 实际增量仍为 `UNKNOWN`
- 执行边界：未运行 solver、PINN、训练、数值 pilot、GPU 或付费服务；未克隆仓库、下载大型数据、安装依赖、联系作者、跨来源拼接或扩大到硫系 PCM

## 1. 结论

`VERIFIED`：本次一次性材料扩展没有找到同时满足下列六门的相关氧化物二维数值对象：

1. 原始论文、DOI、日期与物理对象身份明确；
2. 同一来源链具有固定版本的公开实现和明确软件许可证；
3. 二维器件几何、接触、边界、驱动、完整方程参数以及电—热—结构相因果链闭合；
4. 公开实现能重新生成完整参考输出；
5. 至少两个周期出现空间异步、局部、部分覆盖且可恢复的结构相事件；
6. 可建立与生成器/PINN 残差分离的 evaluator、时空资格化，以及 qualification、development、formal、reserve 四个互斥完整案例角色。

`VERIFIED`：八个深审对象全部触发至少一项一票否决，因此没有活动对象、fallback 或候选排序；本次只读扫描没有启动科学路线。后续全局路线次数上限已由 ADR 0027 撤销，不影响本报告的来源扫描结论。

`SUPPORTED_INTERPRETATION`：扩展后仍然存在同一断裂面，而不是检索词过窄：

- V₂O₃、V₃O₅ 和 LSMO 工作给出最接近论文需求的局部形成—消失、可逆空间相事件，但数值对象没有同时公开固定实现、软件许可和结构序参量动力学；
- FerroX 给出最完整的固定开源相场代码和参考数据链，但对象是电—极化—载流子铁电器件，缺少热方程和目标电热结构事件；
- HfO₂ 与通用电形成相场模型包含二维电热耦合，但状态变量是氧空位/电荷浓度或通用金属细丝，不是目标结构相时钟，而且没有合格的两周期形成—恢复；
- NbO₂、NdNiO₃ 的器件现象与材料方向相关，但公开模型分别退化为无结构相的热失控模型、COMSOL 电势面/紧凑质子云模型，且实现不公开。

`VERIFIED`：按 live plan，零通过必须裁决为 `EXPANDED_OXIDE_ZERO_CANDIDATE`。不得再把范围扩到硫系 PCM，不得降低来源门，也不得用 synthetic substrate 补造候选。

`SUPPORTED_INTERPRETATION`：当前 KC 论文 idea 缺少能承载正式科学投票的公开对象；继续围绕该 idea 做网络、时钟或第二模块优化没有论文证据价值。下一项高价值动作应是另寻 idea，而不是启动 Phase B。

## 2. 扫描合同与查询边界

### 2.1 冻结查询族

本次只使用 live plan 冻结的四个查询族；材料同义词、DOI、作者仓库和官方归档反查属于族内收敛：

1. `NbO2/VOx Mott electrothermal phase-field`；
2. `nickelate/correlated-oxide phase-field device`；
3. `oxide memristor 2D continuum structural-phase model`；
4. `open oxide phase-change multiphysics code/data`。

### 2.2 纳入与排除

- 纳入：具有明确结构/相态/序参量、二维电—热—相态因果链、器件边界和重复动力学潜力的氧化物 PCM、Mott 器件或忆阻器对象。
- 排除：零维/一维集总与 SPICE-only 模型、纯电子阈值开关、只有离子浓度而无结构相态的漂移模型、实验数据而无数值求解器、未公开专有工程、通用框架而无冻结材料对象、硫系 PCM，以及需要跨论文拼接缺失因果量的对象。
- 预算：四个查询族、最多八个深审对象；达到三个六门通过对象或查询族耗尽即停止，不为凑候选降低标准。

### 2.3 一票否决与证据语义

一个候选必须是论文、实现、固定版本、许可证、输入合同和输出的同一来源链。论文的 CC BY 许可不自动构成求解器的软件许可证；通用 MOOSE、AMReX 或 COMSOL 的存在不等于论文专用模型公开；实验多周期证据也不能替代数值 oracle 的结构状态、离散收敛和完整输出。

本报告中的“未发现公开实现”严格限定于上述查询族、日期和预算，不主张作者没有私有代码，也不裁决论文结果真伪。

## 3. 六门总表

符号：`P` 为本门通过；`F` 为硬失败；`S` 为只有论文/实验支持但不足以通过。

| ID | 对象 | G1 论文身份 | G2 固定实现+许可 | G3 2D 电热结构闭合 | G4 完整参考输出 | G5 两周期结构事件 | G6 evaluator+四角色 | 首个硬否决 | 裁决 |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| C1 | Funck 2016 NbO₂ 多维热失控 | P | F | F | F | F | F | 无公开固定实现；模型明确不依赖温致 IMT/结构相 | `FAIL` |
| C2 | Adda 2022 V₃O₅ 二维 MRN 振荡 | P | F | F | F | S | F | 无公开固定 MRN 实现与软件许可 | `FAIL` |
| C3 | Lange 2021 V₂O₃ 应变相共存 | P | F | F | F | S | F | 模型专用实现未公开；结构只以实验转变温度图输入 | `FAIL` |
| C4 | Salev 2021 LSMO 横向绝缘势垒 | P | F | F | S | S | F | 归档代码未形成显式结构相模型；无目标动态结构序参量 | `FAIL` |
| C5 | 2026 H-NdNiO₃ 质子神经网络 | P | F | F | S | F | F | 代码仅可向作者索取；数值模型是 COMSOL 电势面/紧凑质子云 | `FAIL` |
| C6 | Sevic–Kobayashi 2023 电热相场电形成 | P | F | S | F | F | F | 只给通用 MOOSE 框架，无论文模型固定实现/许可；单次电形成 | `FAIL` |
| C7 | Zhang 2020 HfO₂ 氧空位电热相场 | P | F | F | F | F | F | COMSOL 模型和原始数据仅可向作者索取；状态为氧空位迁移 | `FAIL` |
| C8 | Kumar 2023 FerroX | P | P | F | P | F | F | 缺热方程及目标重复电热结构相事件 | `FAIL` |

## 4. 深审对象

### C1. NbO₂ 多维电场触发热失控模型

**身份与一手来源**

- Carsten Funck 等，*Multidimensional Simulation of Threshold Switching in NbO₂ Based on an Electric Field Triggered Thermal Runaway Model*，Advanced Electronic Materials 2, 1600169 (2016)，DOI [`10.1002/aelm.201600169`](https://doi.org/10.1002/aelm.201600169)；[Wiley 出版页](https://advanced.onlinelibrary.wiley.com/doi/10.1002/aelm.201600169)，[RWTH 机构记录](https://publications.rwth-aachen.de/record/679238)。

**闭合审计**

`VERIFIED`：论文给出空间分辨的 NbO₂ 阈值开关模拟，并用电场增加移动载流子后的热失控解释 I–V 跃迁。出版摘要明确说明该模型可用于“不显示温致绝缘体—金属转变”的材料，因此它不是显式结构序参量相变求解器。

`VERIFIED`：本次扫描未发现作者/机构发布的论文专用固定实现、软件许可证、可再生成输入/输出包或独立 evaluator。论文页面和机构记录只提供论文身份，不能替代实现。

`VERIFIED`：对象没有至少两个周期的局部、部分覆盖、形成—恢复结构相事件；静态/准静态阈值 I–V 也不足以建立四角色完整案例池。

**硬裁决：`FAIL`。** 即使其电热器件语义相关，缺失结构相状态和公开执行链已经一票否决。

### C2. V₃O₅ 二维 Mott resistor network 振荡对象

**身份与一手来源**

- Coline Adda 等，*Direct Observation of the Electrically Triggered Insulator–Metal Transition in V₃O₅ Far below the Transition Temperature*，Physical Review X 12, 011025 (2022)，DOI [`10.1103/PhysRevX.12.011025`](https://doi.org/10.1103/PhysRevX.12.011025)；[APS 论文页](https://journals.aps.org/prx/abstract/10.1103/PhysRevX.12.011025)，[官方补充材料](https://journals.aps.org/prx/supplemental/10.1103/PhysRevX.12.011025/SI.pdf)，[arXiv:2012.13009](https://arxiv.org/abs/2012.13009)。

**闭合审计**

`VERIFIED`：实验和官方补充材料显示 V₃O₅ 器件在振荡中周期性形成并溶解金属细丝；二维电—热 MRN 计算给出温度/电阻图，并用并联电容产生重复振荡。事件形态在八对象中与“局部、可恢复、重复”高度相关。

`VERIFIED`：MRN 单元状态由局部温度和经验电阻—温度关系切换，未演化独立结构序参量。论文及补充材料没有提供固定公共实现、软件许可证、输入包或官方完整数值输出归档。

`UNKNOWN`：论文图中的多个振荡是否在结构态上满足本项目的空间异步、部分覆盖及离散收敛门。由于没有公开求解对象，无法独立资格化。

**硬裁决：`FAIL`。** `SUPPORTED_EXPERIMENTALLY` 的漂亮事件不能补偿 G2/G3/G4/G6 缺失。

### C3. V₂O₃ 应变介导相共存与电热细丝

**身份与一手来源**

- Matthias Lange 等，*Optical imaging of strain-mediated phase coexistence during electrothermal switching in a Mott insulator*，Physical Review Applied 16, 054027 (2021)，DOI [`10.1103/PhysRevApplied.16.054027`](https://doi.org/10.1103/PhysRevApplied.16.054027)；[APS accepted manuscript](https://link.aps.org/accepted/10.1103/PhysRevApplied.16.054027)，[arXiv:2009.12536](https://arxiv.org/abs/2009.12536)。

**闭合审计**

`VERIFIED`：对象是平面 V₂O₃ 器件；V₂O₃ 的金属态为 corundum、绝缘态为 monoclinic。论文记录两个连续电流 sweep，在每个 sweep 中局部金属细丝形成、扩展/分裂并在降流时消失，器件返回高阻态；实验空间事件最接近目标。

`VERIFIED`：二维 resistor-network 同时计算电流密度和热场，并很好复现实验 I–V 与细丝方向。但它没有求解结构序参量或应变场；应变效应通过实验测得的像素级 `T_MIT/T_IMT` 图作为固定输入，论文也明确称该模型为 heuristic。

`VERIFIED`：本次扫描未发现对应模型的作者/机构固定代码版本、软件许可证、完整输入/输出归档或独立 evaluator。实验图像、transition-temperature map 与模型代码不能跨链拼接成公开 oracle。

**硬裁决：`FAIL`。** 这是事件适配最强的近失配，但“实验结构事件 + 未公开启发式模型”不满足来源闭合。

### C4. LSMO 横向绝缘势垒与开放代码归档

**身份与一手来源**

- Pavel Salev 等，*Transverse barrier formation by electrical triggering of a metal-to-insulator transition*，Nature Communications 12, 5499 (2021)，DOI [`10.1038/s41467-021-25802-1`](https://doi.org/10.1038/s41467-021-25802-1)；[出版商全文](https://www.nature.com/articles/s41467-021-25802-1)。
- 论文的数据和 simulation code 均指向固定 Zenodo 归档 [`10.5281/zenodo.5165080`](https://doi.org/10.5281/zenodo.5165080)。

**闭合审计**

`VERIFIED`：论文在 50 × 100 μm² LSMO 平面器件中观测到局部横向绝缘/顺磁势垒形成、扩展和撤除；重复开关稳定，并由二维电热 resistor network 复现实验 I–V、温度和电阻空间图。它是本次少数同时公开代码归档和空间事件数据的对象。

`VERIFIED`：Zenodo DOI 固定了归档身份，但论文的 CC BY 许可只明确覆盖文章内容；本次可达记录未给出覆盖 simulation code 的独立明确软件许可证。因此代码可获得性不能单独满足 G2 的“固定实现 + 明确软件许可”联合门。

`VERIFIED`：数值模型的核心是局部电阻—温度关系、Joule heating 和金属/绝缘单元切换；论文强调模拟不需要显式相分离、磁性或缺陷分布假设。公开链没有给出本项目要求的结构序参量动力学，也没有目标的至少两周期结构态形成—恢复及离散收敛资格化。

`VERIFIED`：论文虽报告 5×10⁶ 快速开关循环和多器件重现性，但这是实验耐久/开关证据，不是数值 oracle 中连续记录的合格结构事件案例池。归档代码存在也不自动产生 qualification/development/formal/reserve 四角色。

**硬裁决：`FAIL`。** 开放代码解决了可获得性，却没有解决论文必需的结构相状态与事件门。

### C5. H-NdNiO₃ 质子调制时空神经网络

**身份与一手来源**

- *Protonic nickelate device networks for spatiotemporal neuromorphic computing*，Nature Nanotechnology (2026)，DOI [`10.1038/s41565-026-02133-0`](https://doi.org/10.1038/s41565-026-02133-0)；[出版商全文](https://www.nature.com/articles/s41565-026-02133-0)及随文 source data。

**闭合审计**

`VERIFIED`：实验对象利用 H-NdNiO₃ 中的质子重分布产生非易失与短时记忆；论文包含 Pd–Pd 阵列的重复脉冲、二维空间相互作用和局部氢云演化。

`VERIFIED`：二维 COMSOL 部分只求 2 × 3 阵列表面的电势分布，并假定氢云均匀延伸；器件动态由 Cadence/Verilog-A 紧凑模型和 Python 氢云厚度更新描述。它不是闭合二维电—热—结构相 PDE 对象。

`VERIFIED`：出版商的 Code availability 明确写明 simulation/data-analysis code 仅可向通讯作者合理索取；当前合同禁止联系作者。随文 source data 不等于固定许可求解器。

**硬裁决：`FAIL`。** 它的时空计算价值不能替代缺失的热链、结构序参量和公开实现。

### C6. Sevic–Kobayashi 通用电热相场电形成

**身份与一手来源**

- John F. Sevic、Nobuhiko P. Kobayashi，*Resistive switching conducting filament electroformation with an electrothermal phase field method*，Applied Physics Letters 123 (2023)，DOI [`10.1063/5.0151532`](https://doi.org/10.1063/5.0151532)；[arXiv:2307.14582](https://arxiv.org/abs/2307.14582)。

**闭合审计**

`VERIFIED`：论文在 50 × 10 nm 二维薄膜中耦合 Cahn–Hilliard 电荷/相场、瞬态热方程和电荷守恒，使用 MOOSE 自适应有限元，从随机初态生成局部金属团簇和多根导电细丝。就方程形态而言，它是本次最接近可移植 PINN 残差的对象之一。

`VERIFIED`：论文明确使用的是近似“一类 resistive switching thin films”的通用自由能和参数，并称当前研究只处理单次 CF electroformation；100 ns 后达到已形成稳态。没有反向驱动、恢复，更没有至少两个形成—恢复周期。

`VERIFIED`：MOOSE 是通用框架，不是本论文模型的固定公开实现。本次扫描未发现作者发布的模型输入、定制 kernels、固定版本、软件许可证或完整参考输出包；不能用 MOOSE 的开源许可替代缺失模型代码的许可。

**硬裁决：`FAIL`。** 方程很适合另一个“电形成 PINN”idea，但不能承载当前 KC 结构时钟论文。

### C7. HfO₂ 氧空位电—热—力相场

**身份与一手来源**

- Kena Zhang 等，*High-throughput phase-field simulations and machine learning of resistive switching in resistive random-access memory*，npj Computational Materials 6, 198 (2020)，DOI [`10.1038/s41524-020-00455-8`](https://doi.org/10.1038/s41524-020-00455-8)；[出版商全文](https://www.nature.com/articles/s41524-020-00455-8)。

**闭合审计**

`VERIFIED`：对象以 35 × 20 nm² HfO₂ 为原型，耦合氧空位 Nernst–Planck、导电连续性、Joule 热传输和 Vegard 应变，并在 COMSOL 5.4 中模拟一次三角电压 sweep 的 reset/set。几何、方程与大量参数在论文中相对完整。

`VERIFIED`：状态变量是氧空位浓度，局部应变只是缺陷浓度的 Vegard 响应；论文没有结构晶相序参量或结构相形成—恢复。单次 bipolar set/reset 也不是两个合格重复结构周期。

`VERIFIED`：Data availability 明确写明 phase-field raw data、补充文件和机器学习数据仅可向通讯作者合理索取；没有单独 Code availability，也没有公开 COMSOL 工程、固定实现或软件许可证。

**硬裁决：`FAIL`。** 这是来源不公开且物理状态与当前论文主张错位的离子迁移对象。

### C8. FerroX 开源 HZO 铁电相场器件

**身份与一手来源**

- Prabhat Kumar 等，*FerroX: A GPU-accelerated, 3D Phase-Field Simulation Framework for Modeling Ferroelectric Devices*，Computer Physics Communications 290, 108757 (2023)，DOI [`10.1016/j.cpc.2023.108757`](https://doi.org/10.1016/j.cpc.2023.108757)；[机构开放稿](https://escholarship.org/uc/item/7cz0b6rq)，[arXiv:2210.15668](https://arxiv.org/abs/2210.15668)。
- 作者/机构仓库：[`AMReX-Microelectronics/FerroX`](https://github.com/AMReX-Microelectronics/FerroX)。论文固定 AMReX hash `3dda62` 与 FerroX hash `002bdd`；参考数据归档 [`10.5281/zenodo.7221895`](https://doi.org/10.5281/zenodo.7221895)。仓库给出明确的 [LBNL 三条款式许可](https://raw.githubusercontent.com/AMReX-Microelectronics/FerroX/development/license.txt)。

**闭合审计**

`VERIFIED`：FerroX 自洽求解铁电极化 TDGL、电势 Poisson 和半导体载流子方程，提供 MFIM/MFISM 器件输入、示例与参考数据；固定代码和许可是八对象中最完整的实现链。

`VERIFIED`：公开模型没有热传输/Joule heating 方程，目标是 HZO 铁电畴壁与负电容，不是氧化物电热相变/忆阻器中的局部、部分覆盖、可恢复结构相事件。仓库示例的多畴极化和 Q–V 曲线不能被重新命名为当前 KC 目标事件。

`VERIFIED`：即使允许取二维截面，补入热方程、外部电路和新事件驱动会改变物理对象，形成必须重新准入的派生模型；这违反“不得跨来源补全”的合同。

**硬裁决：`FAIL`。** 实现闭合但科学对象错位，不能作为当前论文 oracle；也不能仅因代码优质而降格录取。

## 5. 未占深审名额的身份层排除

以下命中在身份层已明确不满足目标，未占八对象预算，也未用于拼接任何候选：

- SmNiO₃/NdNiO₃ 的 DFT、实验输运或 COMSOL electrostatics 工作：没有同链二维电—热—结构动力学求解器；
- OpenPhase、MOOSE、AMReX 等通用框架：框架不是经来源冻结的氧化物器件物理对象；
- HfO₂/NiO/TiO₂ 的 SPICE、Verilog-A、compact 或 crossbar 仿真：没有二维空间结构事件；
- 固态/液态储热 PCM、熔化/凝固、沸腾和电池相分离代码：材料机理及论文主张越界；
- V₂O₃ non-thermal nanowire：准一维几何抑制细丝，且数据/代码需联系作者，不能替代 C3；
- 专有 COMSOL 工程或只声明“upon request”的数据/代码：当前合同禁止联系人介入。

## 6. 对论文 idea 与方法模块的直接含义

1. `VERIFIED`：没有对象进入 `1 active + 最多 2 fallbacks` 冻结组合；Phase B 不得启动。
2. `VERIFIED`：本次只读扫描没有启动 solver、数值研究或科学路线；它不对后续研究路线数量作出限制。
3. `UNKNOWN`：KC 对合格空间异步、局部、部分覆盖且可恢复结构事件的实际增量；零候选不是 `KC_FAIL`，也不是 `RAW_INCOMPETENT_ROUTE_NO_TEST`。
4. `VERIFIED`：第二方法模块没有入场条件。没有 standalone KC development，更没有独立剩余瓶颈，任何“魔改加排列组合”都会成为无 oracle 的方法堆叠。
5. `SUPPORTED_INTERPRETATION`：C3（V₂O₃）是事件/论文叙事最接近者，C8（FerroX）是实现/许可最接近者，C6（Sevic）是方程/PINN 适配最接近者；三者分别缺失实现、热事件、重复恢复，且不得跨链合成一个候选。
6. `SUPPORTED_INTERPRETATION`：若另寻 idea，C6/C7 可以启发“离子/电形成相场 PINN”，C8 可以启发“铁电相场 PINN”，但两者都要求重写目标物理主张、核心状态变量、事件门和方法动机；它们不是当前 KC idea 的 fallback。

## 7. 终局

- 终局：`EXPANDED_OXIDE_ZERO_CANDIDATE`
- 深审数：`8/8`
- 通过数：`0/8`
- 候选清单：空
- 冻结顺序：不适用
- Phase B 授权：`false`
- 数值/PINN/formal/GPU 授权：`false`
- 正面方法结论：无
- 实验验证主张：无
- 论文建议：终止当前来源依赖型 KC idea，另寻能先获得来源闭合 oracle 的 idea

达到 live plan 的零候选停止条件后，本次扫描立即收口。不得继续添加第九个对象、继续换材料、降格硬门、构造 synthetic substrate，或把上述互补近失配对象拼接为一个来源链。

## 8. 可获得性与盲区

- 核验渠道限于原始论文/出版商页面、官方补充材料、作者或机构仓库、Zenodo/机构归档及明确许可证文本。
- 部分 Zenodo/出版商页面存在动态页面或反爬限制；只在论文正文明确给出归档身份时引用，不据此推断未展示的文件具有软件许可。
- “未发现公开代码”是有界搜索事实，不表示作者没有私有实现或未来不会公开。
- 本报告只裁决候选是否满足本项目来源闭合合同，不裁决论文正确性、实验可信度或学术优先权。
