# HFO-NP-v1 G0 来源与对象合同审查

- `date`: `2026-08-25`
- `report_role`: `G0_PRIMARY_SOURCE_AND_OBJECT_CONTRACT_REVIEW`
- `authorization`: `HFO_NP_V1_G0_SOURCE_REVIEW_ACTIVE / G0_SOURCE_CONTRACT_ONLY`
- `source_count`: `2`（1 篇主文及其 1 份官方 Supplement；Nature 与 DOE OSTI 只是同一主文的官方载体，不重复计数）
- `execution`: `0 solve / 0 object build / 0 training / 0 PINN / 0 GPU`
- `single_verdict`: `WAVEFORM_TIME_NO_GO`
- `downstream`: `G1_NOT_AUTHORIZED_AND_NOT_ELIGIBLE`
- `claim_status`: `NO_SCIENTIFIC_METHOD_CLAIMS`

## 1. 结论

**单一裁决：`WAVEFORM_TIME_NO_GO`。**

`VERIFIED`：Zhang 等 2020 主文与官方 Supplement 足以确认二维轴对称 HfO₂₋ₓ 对象家族、贯通连续 CF 初态、氧空位 Nernst–Planck 输运、电流连续、准稳态 Joule 热、显式 `T ->` vacancy transport 反馈、可选弹性化学势，以及一次 RESET→SET 双极事件的图像证据。

但同一主文对基准慢三角波给出互相冲突的绝对时间身份：正文和 Fig. 1 图注写 `dV/dt = 0.1 V s^-1`，而 Fig. 1b inset 的时间轴约为 `0–3.3 s`，并画出约 `0 V -> +1.1 V -> -0.6 V -> 0 V`；该图对应约 `1 V s^-1`。若文字的 `0.1 V s^-1` 为准，同一节点应约在 `0, 11, 28, 34 s`，相差约十倍。来源没有 erratum、机器可读波形或原始 deck 用来判定哪一个身份有效，也没有完整声明 dwell。

物理时间直接进入 `D(T)=D0 exp[-EA/(kBT)]` 控制的 vacancy transport。因而这一冲突不能作为排版小差异忽略，也不能由 `A′` 或 `ENGINEERING` 选择修复。来源锚点 `a0`、固定时长 RESET 段及其完整 history 均无法唯一冻结，当前 `SOURCE_ANCHORED_DERIVED_WAVEFORM_SCALE_AXIS` 不成立。按 live plan 的最早硬停止条件，G0 在此收口，不进入 G1。

侧向电/热/空位边界、力学本构参数、原始数据和输入资产许可还存在独立未闭合项；即使未来澄清波形，也必须重新通过这些门。本裁决不否定论文结果、HfO₂ vacancy 模型或 PINN 的一般可行性。

## 2. 一手来源账本

| ID | 一手来源与正式链接 | 版本与定位 | 许可/数据/资产 | 身份与状态 |
|---|---|---|---|---|
| S1 | K. Zhang, J. Wang, Y. Huang, L.-Q. Chen, P. Ganesh, Y. Cao, *High-throughput phase-field simulations and machine learning of resistive switching in resistive random-access memory*, npj Computational Materials 6, 198 (2020). [DOI](https://doi.org/10.1038/s41524-020-00455-8), [Nature 版本页](https://www.nature.com/articles/s41524-020-00455-8), [DOE OSTI 全文载体](https://www.osti.gov/biblio/1787247) | Version of Record：2020-12-18；DOI `10.1038/s41524-020-00455-8`；重点定位：Fig. 1、Fig. 2、Methods Eqs. (3)–(16)、Data availability、PDF pp. 2–3, 7–10 | 主文明确 `CC BY 4.0`。Data availability 仅称 phase-field raw data、Supplement 相关文件和 ML data 可向通讯作者合理索取；无 Code availability、公开 COMSOL 工程、输入 deck、release 或软件许可 | 来源事实为 `A`；网格/COMSOL 为来源报告的 `ENGINEERING`；`VERIFIED` |
| S2 | 同文官方 [Supplementary Information PDF](https://static-content.springer.com/esm/art%3A10.1038%2Fs41524-020-00455-8/MediaObjects/41524_2020_455_MOESM1_ESM.pdf) | 11 页；无独立 DOI/版本号；重点定位：Supplementary Note 1, Eqs. (S1)–(S4), Fig. S1；Note 2；Fig. S3–S5；Supplementary Table 1 | 官方公开下载，但 PDF 内没有独立软件/数据许可或 deck/restart；不得把主文 CC BY 自动写成 COMSOL 模型的软件许可 | 来源事实为 `A`；`VERIFIED` 载体身份，资产可重放性 `UNKNOWN` |

检索在首个决定性硬门出现后停止，没有为凑满 8 项来源继续扩张。最危险 direct/near 方法碰撞也未展开，因为本次对象合同已在方法比较之前失败；这不是 novelty clearance。

## 3. 物理对象与初态

| 合同项 | 一手证据 | A/A′/ENGINEERING | 裁决 |
|---|---|---|---|
| 几何与域 | 主文 Fig. 1a/Methods：35 nm（径向 `x`）× 20 nm（厚度 `z`）的二维等效截面，代表三维轴对称 HfO₂ 器件；连续 CF 半径约 9 nm，贯通上下电极 | `A` | `VERIFIED`；仅该轴对称有效域，不外推到任意真实几何 |
| 初态 | 主文 p. 2/Fig. 1：electroforming 已完成；CF 内 `N_V = 1.2e27 m^-3` 均匀，余域为零；CF 连接 TE/BE | `A` | `VERIFIED_CONTINUOUS_CF`；允许的初态分支只能是连续 CF，事件顺序为 RESET gap opening → SET gap closing |
| finite-gap restart | Fig. 1 给出 reset 后彩色场图，但没有机器可读字段、restart/deck、精确网格状态或许可身份 | 不能由 `A′`/`ENGINEERING` 补造 | `UNKNOWN / NOT_AVAILABLE_AS_EXACT_RESTART`；栅格图不能升格为 exact restart |
| 第二周期 | 来源只展示一次双极 sweep；连续重复为项目压力测试 | `A′` | 仅可称 derived two-cycle stress，当前未获数值执行授权 |

## 4. 方程、本构、单位与 `T -> transport` 反馈

### 4.1 来源明确给出的三场骨架

`VERIFIED`，主文 Methods Eqs. (3)–(16) 与 Supplement Note 1：

1. 氧空位数密度 `N_V [m^-3]` 是内部状态。化学、电、弹性势分别由 Eqs. (8)–(10) 给出，总势为 Eq. (11)。
2. vacancy flux 为

   `J_V = -(D/(k_B T)) N_V grad(mu_V)`，

   且 `D = D0 exp[-EA/(k_B T)]`，`D0 = 2e-3 cm^2 s^-1 = 2e-7 m^2 s^-1`，`EA = 1 eV`。守恒 Nernst–Planck 形式见主文 Eqs. (13)/(14) 与 SI Eqs. (S1)/(S2)。
3. 电流连续为 `div(sigma grad(phi)) = 0`（Eq. 15 / S3）。`sigma = sigma0(N_V) exp[-E_AC(N_V)/(k_B T)]`；SI Note 1 给出 `sigma0` 从 `1.0e3` 到 `2.86e5 S m^-1` 的线性关系，并给 `K1=2.38`。
4. 准稳态热方程为 `-div(k_th grad(T)) = sigma |grad(phi)|^2`（Eq. 16 / S4），没有 `rho c_p partial_t T`。`k_th` 依赖 `N_V`。

因此 `T -> vacancy transport` 不是推测：`T` 直接进入 `D(T)`、`1/T` mobility factor 和 `sigma(T,N_V)`，而 Joule heating 又由 `sigma|grad(phi)|^2` 产生。该电—热—缺陷反馈身份为 `VERIFIED`，但热场是准稳态而非独立热动力学状态。

### 4.2 可选力学化学势

主文 Eq. (13) 含弹性势，Eq. (14) 去除该项；Fig. 2 比较两支。`VERIFIED`：来源在恒定 `1.1 V` RESET pulse 下报告力学分支把 `R_off` 从约 `1.1 kOhm` 改为 `0.969 kOhm`，并把 `t_switch` 从约 `18 ns` 改为 `23 ns`，同时改变纵向和侧向 vacancy 分布。故力学不是可在来源模型保真中静默删除的装饰项。

但 `C_ijkl` 的完整数值/单位和机械边界没有在主文或 SI 闭合，慢三角波 Fig. 1 的具体力学分支身份也未单独声明。当前三场对象若要求复现来源空间场，力学必要性仍为 `UNKNOWN`；不得按结果开启/关闭该项。若未来确认力学为来源保真所必需，应按 live plan 另记路线 No-Go，而不是在同一计划增加第四物理块。

### 4.3 仍未闭合的本构/单位项

- `UNKNOWN`：主文 Eq. (9) 给 `mu_electric = 2 e phi`，但展开的 Eqs. (13)/(14) 写成 `eD/(k_B T)` 漂移系数；来源没有解释电荷因子约定。
- `UNKNOWN`：SI Note 1 的 `k_th` 文字公式写 `K1`，随后又定义 `K2=1.875`，Fig. S1c 标为 `K2`。同段称高 vacancy 极限等于 Hf `57.5 W m^-1 K^-1`，而 Fig. S1c 和 Supplementary Table 1 的 HfO₂ 点约为 `23 W m^-1 K^-1`。不能替来源静默纠错。
- `UNKNOWN`：`E_AC(N_V)` 只由 Fig. S1b 与端点描述，未给完整解析分段式；`C_ijkl`、外侧边界及所有接触参数也未闭合。

这些是独立的 `BOUNDARY_CONSTITUTIVE` 风险，但单一 verdict 保持最先触发且已决定绝对时间身份的 `WAVEFORM_TIME_NO_GO`。

## 5. IC、BC 与界面合同

| 场/界面 | 来源明确项 | 未明确项 | 状态 |
|---|---|---|---|
| vacancy IC | 连续贯通 CF 内 `1.2e27 m^-3`，外部为零 | 无 exact finite-gap restart | `VERIFIED` / restart `UNKNOWN` |
| vacancy BC | 两个 oxide/electrode 界面均 blocking、零 vacancy flux | 外侧径向边界 `x=35 nm` 的 vacancy BC；轴线正则条件未以方程写出 | `PARTIAL / UNKNOWN` |
| electric BC/interface | TE 施加 `V_app(t)`，BE 接地；界面假设 ohmic、忽略电子势垒和接触电阻 | 外侧径向电边界；电极域/串联电阻/电流积分定义的完整形式 | `PARTIAL / UNKNOWN` |
| thermal BC/interface | TE/BE 均作 `T=300 K` 热沉 | 外侧径向热边界、界面热阻 | `PARTIAL / UNKNOWN` |
| mechanics | 公式中设总应变 `epsilon_ij=0`，以 Vegard eigenstrain 构造局部弹性势 | 完整机械边界、`C_ijkl` 数值和慢三角波目标分支 | `PARTIAL / UNKNOWN` |

轴对称几何通常暗示 `x=0` 正则/对称条件，但来源没有把这项和外侧边界完整写出；本报告不把常规有限元默认值升格为来源事实。

## 6. 波形与绝对时间硬门

### 6.1 同源矛盾

| 证据位置 | 来源陈述 | 物理含义 | 状态 |
|---|---|---|---|
| 主文 p. 2 正文及 Fig. 1 图注 | 三角 sweep，`dV/dt=0.1 V s^-1` | `0 -> +1.1 -> -0.6 -> 0 V` 需要约 `34 s` | `VERIFIED_TEXT` |
| 主文 Fig. 1b inset | 横轴为 `Time (s)`，约 `0–3.3 s`；节点约 `0, 1.1, 2.8, 3.3 s` | 同一电压节点对应约 `1 V s^-1` | `VERIFIED_FIGURE` |
| SI Fig. S3 / 主文 Fig. 2f | 恒定 `+1.1 V` pulse，`10 ps–10 us`，用于单向 RESET 力学比较 | 独立恒压协议；不是慢双极三角波 | `VERIFIED_SEPARATE_PROTOCOL` |

来源没有给全节点表、机器可读波形、dwell、COMSOL time function 或 erratum。不能用 Fig. S3 的 ns pulse 替代慢三角波，也不能把 `0.1` 或 inset 时间轴任择其一标为 `ENGINEERING`。

### 6.2 fixed-duration waveform-scale A′

- 来源的线性三角波可作为 `A` 线索，但其绝对时间身份自相矛盾，故基准 `a0` 不能冻结。
- “只缩放固定时长 RESET 段、其余波段/转折点/physical time 不变”是 `A′`，不是 source-native axis。来源没有给这种局部协议族、允许包络或连续拼接函数。
- 在基准时间未闭合时，任何该类 `A′` 都会任意选择不同 vacancy history；不得称纯 amplitude 或纯 ramp-rate 因果轴，也不得用事件时间归一化掩盖差异。

结论：`SOURCE_ANCHORED_DERIVED_WAVEFORM_SCALE_AXIS = NOT_QUALIFIED`。

## 7. 来源模型保真变量

`VERIFIED`：主文 Fig. 1b 给出完整的一次 I–V 回线；Fig. 1c/f/i 给出至少三个带色标的 vacancy 空间状态，分别标为 `V_app=0.3 V` 初态、`+1.1 V` reset 和 `-0.57 V` set；同时给 `T` 与 `phi` 守卫场。因此“端口证据和至少两个跨事件 vacancy 空间图是否存在”的答案是肯定的。

但这些只有出版图像，没有公开原始数组、snapshot/restart、状态时间、像素/离散不确定性或作者给出的固定 ROI/gap/contour 数据。更关键的是，波形时间矛盾使 I–V 无法唯一转换为 `I(t)`/`G(t)`，也无法把空间图绑定到唯一 physical-time history。故：

- port I–V 图像存在：`VERIFIED`；可重建绝对时间端口轨迹：`UNKNOWN`；
- 跨事件 vacancy 图像存在：`VERIFIED`；精确字段和联合不确定性：`UNKNOWN`；
- 来源模型保真 G1 门：`NOT_ELIGIBLE`。

## 8. 许可与资产

- 主文及其正文图像：`CC BY 4.0`，`VERIFIED`。
- 官方 Supplement：公开可下载；文件本身未列独立软件/数据许可，`UNKNOWN` 到可复用原始资产层级。
- raw phase-field/ML data：仅“upon reasonable request”；本次未联系作者，也没有公开固定版本、校验值或许可，`UNKNOWN / NOT_PUBLICLY_REPLAYABLE`。
- COMSOL 5.4、论文专用工程、输入 deck、time function、restart、post-processing：主文/SI 没有公开仓库、release 或软件许可。此结论只覆盖本次两个一手记录，不声称作者不存在私有资产。
- 论文 CC BY 不等于专有 COMSOL、未公开 deck 或数据的软件/再分发许可。

软件 deck 缺失本可只关闭作者 replay、保留 clean-room 派生计划；但本次物理合同本身已被绝对时间矛盾和边界/本构缺口阻断，因此 clean-room 对象也不能进入 G1。

## 9. 单一裁决与边界

```text
HFO_G0_VERDICT=WAVEFORM_TIME_NO_GO
INITIAL_STATE_BRANCH=SOURCE_CONTINUOUS_CF_ONLY
SOURCE_ANCHORED_WAVEFORM_A0=UNRESOLVED_10X_TIME_CONFLICT
SOURCE_ANCHORED_DERIVED_WAVEFORM_SCALE_AXIS=NOT_QUALIFIED
SOURCE_MODEL_FIDELITY_ENTRY=NOT_ELIGIBLE
G1=NOT_AUTHORIZED_AND_MUST_NOT_START
SOLVES=0
TRAINING=0
GPU=0
```

决定性证据是同一来源内 `0.1 V s^-1` 与约 `0–3.3 s` 三角波 inset 的十倍绝对时间冲突。未闭合项包括：外侧径向三场边界、力学张量/边界和目标分支、若干本构符号/系数矛盾、机器可读端口/空间状态、COMSOL deck/restart/data 的固定版本与许可，以及 fixed-duration RESET waveform-scale A′ 的来源可容许包络。

本结果只关闭当前来源对齐的 HFO-NP-v1 G0→G1 路径；不构成 HfO₂ 物理失败、论文结果否定、PINN 失败、新颖性裁决或实验验证。
