# 2026-08-25 新对象 source-complete 审查

## 1. 结论先行

- **唯一阶段判决：`NEW_OBJECT_SOURCE_COMPLETE_BOUNDED_NO_GO`。** 本轮只深审 1 个二维及以上氧化物器件对象家族，新增核验 3 项一手来源载体；没有对象通过全部 source-complete 硬门，因此不指定 PASS 对象。
- 被审对象是 2025 年 Pd/Ta₂O₅/TaOₓ/Pd 作者 COMSOL 对象。其固定作者模型自身的二维器件边界、电—热—vacancy 内部态链、IC/BC/界面、本构、单位和绝对时间协议可以闭合，记为 **boundary-integrity PASS**。
- **最早且决定性的失败是 source–model parameter alignment。** 固定作者模型中的 vacancy hopping distance 为 `a = 0.16 nm`，论文正文明确为 `a = 0.32 nm`。`a` 同时进入扩散系数和场驱动跃迁速度，不能靠解释、猜测或结果拟合修补，故该对象在任何求解前即失去 canonical oracle 资格。
- 两项独立次级失败进一步阻止提升：固定 `.mph` 没有嵌入可读取的全场时空解/轨迹；六个 `.mph` 只有五个唯一内容，且均为同一对象的 `K1/K2` 变体，不能闭合完整实体拆分。
- 该 No-Go 只覆盖本轮这个对象和三项固定载体；它不证明 TaOₓ、其他氧化物、传统求解器或 PINN 普遍失败，也不授权重开 HFO-NP-v1、历史 Q-POP/R1/R2/R3 路线，或自动选择任何方法。

状态词：直接由固定一手载体核对得到的事实记为 `VERIFIED`；由这些事实推得、但不是来源原句的门禁解释记为 `SUPPORTED_INTERPRETATION`。本报告没有把假设写成对象事实。

## 2. 授权边界与查询范围

本审查仅执行只读一手来源研究和固定资产静态检查：**0 object build、0 solve、0 training、0 PINN、0 GPU、0 paid compute、0 Git 操作**。没有执行 `.mph`，没有生成数值结果。

查询日期为 2026-08-25。先复用并排除既有 [VO₂ source-complete candidate scan](./2026-08-22-vo2-source-complete-candidate-scan.md) 与 [related-oxide source-complete candidate scan](./2026-08-22-related-oxide-source-complete-candidate-scan.md)，不重复计算其中已审家族。本轮仅把具备论文、作者固定模型包和明确许可证的 Pd/Ta₂O₅/TaOₓ/Pd 对象提升到 deep review；在最早决定性硬失败成立后停止扩展，不为凑满“最多 4 家族”继续搜索。

检索面限于 DOI/出版社正式页面、作者机构公开模型仓库和软件供应商官方技术文档；概念组合包括 `oxide memristor`、`RRAM`、`2D/3D`、`electrothermal`、`oxygen vacancy`、`full model`、`raw solution`、`data/code` 和 `license`。搜索摘要、二手综述、博客和模型回忆没有参与判决，也没有用跨材料参数拼接修补对象。

## 3. 新增一手来源账本（3/20）

| ID | 固定一手载体 | 本轮用途 | 可用性与许可判断 |
|---|---|---|---|
| S1 | Gooran-Shoorakchaly, Sharif & Banad, *Scientific Reports* 15, 18646 (2025), [version of record / DOI](https://doi.org/10.1038/s41598-025-02909-9) | 方程、参数、几何、加载、边界、图示输出和 data-availability 声明 | 论文为 CC BY-NC-ND 4.0；可核对，但不得把改编图文当作自由许可资产 |
| S2 | 作者公开模型仓库，固定于 commit [`5944e6f187b2e78700ff515dba742952ba03c759`](https://github.com/INQUIRELAB/TaOx-RRAM-Simulation-and-Analysis/tree/5944e6f187b2e78700ff515dba742952ba03c759) | 六个 `.mph`、`dmodel.xml`、内部数据集元数据、README、Git tree/blob 身份和许可证静态审查 | 仓库声明 [MIT License](https://github.com/INQUIRELAB/TaOx-RRAM-Simulation-and-Analysis/blob/5944e6f187b2e78700ff515dba742952ba03c759/LICENSE)；运行仍需另行具备合法 COMSOL 6.1 环境 |
| S3 | COMSOL 6.3 API, [`model.sol()` official documentation](https://doc.comsol.com/6.3/doc/com.comsol.help.comsol/comsol_api_general.47.58.html) | 核对 solver sequence/features 与 computed solution data 的区别；官方文档说明 `clearSolutionData()` 可清除计算解而不改变 solver features | 只作文件语义解释，不把 COMSOL 文档当作该对象的物理来源 |

S1–S3 均为作者、出版社或软件供应商的一手载体。没有使用论文补充包形成额外独立事实，因此不把它另计为来源。

## 4. 统一硬门与审查顺序

对象按下列顺序判定，任何硬门失败即停止把它提升为论文对象：

1. 二维及以上、器件级空间对象；
2. 电—热—内部态闭环，内部态由可记录的演化方程推进；
3. 几何、材料区域、IC、BC、界面条件、本构、参数和单位闭合；
4. 绝对时间、完整加载波形、历史/初始化顺序闭合；
5. 论文与固定作者模型逐项对齐，不允许猜测修补；
6. 固定且合法的作者实现，或足以独立 clean-room 重建的完整合同；
7. 可机器读取的端口量和至少一个空间量，可支持独立 oracle 核验；
8. 可按完整器件、几何、协议或轨迹形成互斥资格、开发、formal 与 reserve 实体角色。

## 5. 唯一深审家族：2025 Pd/Ta₂O₅/TaOₓ/Pd 作者 COMSOL 对象

### 5.1 对象身份

对象只称为 **source-pinned 2025 Pd/Ta₂O₅/TaOₓ/Pd COMSOL numerical model**。它不是实验验证对象，不是作者原生结果重放，也不是 clean-room HFO-NP-v1 的继续或替代。

`VERIFIED`：[S1 version of record](https://www.nature.com/articles/s41598-025-02909-9) 给出二维 Pd/Ta₂O₅/TaOₓ/Pd 双层器件：宽 40 nm、深 20 nm，BE/TaOₓ/Ta₂O₅/TE 厚度分别为 35/30/5/50 nm；TaOₓ 初始 vacancy density 为 `1e22 cm^-3`，Ta₂O₅ 为 `1e16 cm^-3`。模型自洽求解 vacancy drift–diffusion–Soret 连续方程、电流连续方程和带 Joule heating 的 Fourier 热方程，并使电导率和热导率依赖 vacancy density/温度。S1 还给出 forming `-2.1 V × 10 ms`、RESET `+1 V × 10 ms`，以及 300 K 电极/CML 热边界、BE 接地和 CML 顶面加载。

### 5.2 boundary integrity：PASS，与纸模对齐判决分离

`VERIFIED`：对 [S2 固定作者模型树](https://github.com/INQUIRELAB/TaOx-RRAM-Simulation-and-Analysis/tree/5944e6f187b2e78700ff515dba742952ba03c759) 做不执行的只读容器检查，以下内容都可在 canonical 模型树中定位：

- 二维器件几何及材料域；
- 13,841-node 二维 vacancy-density 初值资产与温度初值；
- 电边界 13 的 `Vin2(t)+0.5 mV·sin(2πt/PT)`、电边界 2 的 ground；热边界 2/10/12/13 的 `293.15 K`，其余外边界为 thermal insulation；
- vacancy 默认外边界为 zero flux，边界 6 由 Dirichlet 条件固定为 `nD0`；
- vacancy drift、Fick diffusion、Soret flux、电流连续和 Joule-heated heat equation；
- 材料本构、参数单位、周期 SET/RESET 函数、当前 study 的符号时间范围及多物理耦合节点。

因此，**固定模型自身**在二维器件、电—热—内部态链、IC/BC/界面、本构、单位和绝对时间/历史定义上记为 `PASS`。该 PASS 只说明模型树内部完整；它不意味着模型与论文一致，更不意味着保存了解或具备 oracle 资格。

### 5.3 最早决定性失败：source–model parameter alignment

`VERIFIED`：S1 的 vacancy transport 定义为

\[
D=\tfrac12 a^2 f\exp(-E_a/kT),\qquad
\nu=a f\exp(-E_a/kT)\sinh(-qaE/kT),
\]

并在正文明确使用 `a = 0.32 nm`。固定 S2 canonical reference [`Figure5_Reference_Kth=5.75-sigma=9.4.mph`](https://github.com/INQUIRELAB/TaOx-RRAM-Simulation-and-Analysis/blob/5944e6f187b2e78700ff515dba742952ba03c759/Figure5_Reference_Kth%3D5.75-sigma%3D9.4.mph) 的只读下载 SHA-256 为 `045370FDC7F5A8D9E98CF8A17C43A50B96551AC6E68E1B6A15774F780C43057A`；其 `dmodel.xml` 定义 `a = 0.16[nm]`，并直接使用 `D_new=0.5*a^2*f*exp(-Ea/(k_B_const*T))`、`v_x=a*f*exp(-Ea/(k_B_const*T))*sinh(e_const*a*Vx/(k_B_const*T))`，`v_y` 同理。场方向的符号约定不影响 `a` 在扩散与非线性漂移两处的直接耦合。

`SUPPORTED_INTERPRETATION`：这不是只影响标签的差异。固定温度下，零场扩散前因子因 `a^2` 相差 4 倍；场驱动速度的线性前因子和 `sinh` 自变量也同时改变。S1–S2 没有给出双版本、换算或勘误，因此不能选择其中一个冒充 canonical 物理合同，也不能用未来结果拟合决定采用哪个值。

同一静态核验还读到 S1 纸面定温边界为 `300 K`、S2 固定模型树为 `293.15 K`。这不改变“边界位置与类型可唯一读取”的 boundary-integrity PASS，却是另一项未获作者说明的纸模数值差异；最早判决仍只需上面的 `a` 冲突。

**硬门 5 = FAIL。** 这是最早决定性失败；按预声明顺序，到此已足以判定对象 No-Go。以下两项作为独立次级失败保留，不用于“叠加理由”延长路线。

### 5.4 独立次级失败 A：没有嵌入可读取的 oracle 轨迹

`VERIFIED`：canonical `.mph` 的 `Dataset SolutionNative` 元数据列出 5,881 个时间标签，但同时记录 `totalSize = 0`；配套 `solution1.mphbin` 仅 77,070 B，模型容器中没有保存全场时空 solution payload。固定仓库树也没有 CSV、HDF5、VTK 或其他 raw 数值导出。

[S3 官方文档](https://doc.comsol.com/6.3/doc/com.comsol.help.comsol/comsol_api_general.47.58.html) 明确区分 solver sequence/features 与 computed solution data，并说明计算解可以被清除而 solver/results settings 保持不变。因而，模型中仍有求解节点、结果节点、时间标签或 solver log，不能推出数值解数组仍嵌入文件。

`SUPPORTED_INTERPRETATION`：S1 的论文图和 S2 的 Results 节点可以规定“应看什么”，却不能充当可复算的端口/空间 oracle。任何未来重新求解得到的数组都将是新执行结果，而且仍会遇到 `a` 的版本歧义。**硬门 7 = FAIL。**

### 5.5 独立次级失败 B：完整实体拆分不成立

`VERIFIED`：[S2 固定树](https://github.com/INQUIRELAB/TaOx-RRAM-Simulation-and-Analysis/tree/5944e6f187b2e78700ff515dba742952ba03c759) 有六个 `.mph` 名称，但 `Fig6_Refere_Kth=5.75-sigma=9.4.mph` 与 `Figure5_Reference_Kth=5.75-sigma=9.4.mph` 指向同一 Git blob，故只有五个唯一模型内容。其余四个唯一文件是：

- `Figure5_consKth_sigma=18.8.mph`
- `Figure5_constKth_sigma=6.2.mph`
- `Figure6_ConstSigma_Kth=11.5.mph`
- `Figure6_ConstSigma_Kth=2.5.mph`

它们均为同一器件、同一协议附近的 `K1` 或 `K2` 单轴变体。固定资产没有预封存 qualification/development/formal/reserve 分工，也没有与每个实体配套的 raw 端口量和空间真值。

`SUPPORTED_INTERPRETATION`：不能把同一 reference 的重复文件当成两个独立实体，也不能在缺少 raw truth 的情况下事后把五个稀疏变体包装成完整互斥证据角色。**硬门 8 = FAIL。**

### 5.6 门禁矩阵

| 硬门 | 判决 | 直接依据 |
|---|---:|---|
| 2D+ 器件 | PASS | S1 几何；S2 固定模型树 |
| 电—热—内部态闭环 | PASS | S1 三方程；S2 耦合物理节点 |
| IC/BC/界面/本构/单位 | PASS | S2 `dmodel.xml` 静态检查 |
| 绝对时间/完整历史 | PASS | S1 脉冲；S2 周期函数与 current-study 符号时间范围 |
| source–model alignment | **FAIL** | `a = 0.32 nm`（S1）vs `0.16 nm`（S2） |
| 合法固定资产 | CONDITIONAL | S2 为 MIT；运行依赖另行合法 COMSOL 6.1 环境 |
| 机器可读端口 + 空间真值 | **FAIL** | `totalSize = 0`，无保存全场解或 raw export |
| 完整实体拆分 | **FAIL** | 6 个名称、5 个唯一内容，仅 `K1/K2` 稀疏变体 |

### 5.7 家族判决

**`C1_NO_GO_SOURCE_MODEL_ALIGNMENT`。** 无嵌入解与 entity split 失败是相互独立的次级否决项；即使未来补回解文件，也不能自动修复论文—模型的 `a` 冲突。

## 6. 正式收口与保留价值

1. 本轮没有 source-complete PASS 对象，因此不产生方法、网络结构、loss、训练日程、GPU 建议、bottleneck hypothesis、强 raw 设计或消融/OOD 方案。
2. C1 仅保留为有界的 **source–model inconsistency negative evidence**：它说明“论文 + `.mph` + 开源仓库”的外观不能替代逐项 paper–model alignment 与 solution-payload 核验。
3. 任何未来重启必须由新的明确 PLAN 与用户批准触发，并至少带来能改变最早失败的新一手资产，例如作者勘误或固定模型版本说明。仅补 CSV、补算结果或增加 case，不能解决 `a` 冲突。
4. 没有输入变化时，不重复审计、不追加机制、不自动换路线。

**最终状态：`NEW_OBJECT_SOURCE_COMPLETE_BOUNDED_NO_GO`。**
