# R2 严格热耦合 FerroX：P0 来源、热机制与创新碰撞审查

- `review_date`: `2026-08-22`
- `phase_id`: `R2_P0_AUTHORIZED_SOURCE_ONLY`
- `scope`: `PACKAGE_A_A1_TO_A5`
- `budget_used`: `0 solve / 0 training intent / 11 primary-source cards`
- `object_identity`: `source-pinned FerroX-derived/synthetic HZO y-invariant MFIM candidate`
- `single_verdict`: `R2_P0_SOURCE_IDENTITY_NO_GO`
- `downstream_authorization`: `NONE`

## 1. 单一裁决

`VERIFIED`：R2 在最早的来源身份硬门终止。FerroX 论文所指短哈希 `002bdd` 可解析为完整 commit `002bddf6368d4de94a3b623c6a16e1f0d597e82b` 和 tree `da2e4a8725cfed389da970a749c17b72b76086ff`，但该固定 tree 内没有 `LICENSE`、`license.txt` 或其他许可文件；当前 `development` 分支的 2024 许可不能替代计划要求的“论文提交时实际存在的许可”。论文所指 AMReX 短哈希 `3dda62` 经官方 GitHub commit API 当前返回 `422 No commit found`，官方 commit search 也没有匹配，因而不能冻结为完整 commit/tree。Zenodo 数据身份可以闭合，但不能修复代码和依赖身份。

因此按预声明停止顺序裁决：

> `R2_P0_SOURCE_IDENTITY_NO_GO`

该裁决关闭当前 R2 `FULL_DESIGN` 的授权包 A，并禁止进入 B、C、D。它不表示 FerroX 代码从未获得过许可，也不表示严格热耦合 HZO 模型在全局不存在；它只表示当前计划要求的论文固定代码/依赖/许可链无法由现有官方记录闭合。

另有独立但不覆盖首个停止门的发现：`THERMAL_CLOSURE` 未闭合，`THERMAL_VALUE` 不可判定为通过，TKC 的精确创新空间仍为 `UNKNOWN`。这些发现仅用于解释为什么不得绕过来源门实施，不形成第二个并列 verdict。

## 2. 一手来源卡（11 项）

| # | 一手来源 | 本次固定内容 | 证据状态与用途 |
|---|---|---|---|
| S1 | [FerroX 论文](https://doi.org/10.1016/j.cpc.2023.108757)；[作者版 v2](https://arxiv.org/html/2210.15668v2) | TDGL–Poisson–平衡载流子方程，y-invariant MFIM、三角波畴切换、FerroX `002bdd`、AMReX `3dda62`、Zenodo DOI | `VERIFIED` 原生底座与论文身份；原模型无热方程、无动态电流连续方程 |
| S2 | [FerroX 官方 commit API](https://api.github.com/repos/AMReX-Microelectronics/FerroX/commits/002bdd) 与 [固定 tree](https://api.github.com/repos/AMReX-Microelectronics/FerroX/git/trees/da2e4a8725cfed389da970a749c17b72b76086ff?recursive=1) | 完整 commit/tree；固定 tree 文件集合 | `VERIFIED` 可解析；`VERIFIED` 固定 tree 内无许可文件 |
| S3 | [FerroX 当前许可](https://raw.githubusercontent.com/AMReX-Microelectronics/FerroX/development/license.txt) | 当前开发分支的宽松三条款文本，版权年份 2024 | `VERIFIED` 当前许可存在；不能倒填为 2022 固定提交的实际许可 |
| S4 | [AMReX 官方 commit API](https://api.github.com/repos/AMReX-Codes/amrex/commits/3dda62) | 论文短哈希 `3dda62` 的解析尝试 | `VERIFIED` 截至审查日官方 API 为 422；完整 commit/tree `UNKNOWN` |
| S5 | [Zenodo 版本记录](https://doi.org/10.5281/zenodo.7221895) | version DOI、CC-BY-4.0、四个 tar 包、文件大小与 MD5 | `VERIFIED` 数据入口可冻结；不含代码许可补丁 |
| S6 | [Wang et al. 2018](https://doi.org/10.1088/1361-665X/aab92e) | 热力学一致 TDGL–热方程、极化黏滞耗散与可逆热项的结构 | `VERIFIED` 方程结构来源；材料是 BaTiO3，参数不得移植到 HZO |
| S7 | [Scott et al. 2018](https://doi.org/10.1063/1.5052244) | 20 nm Hf1-xZrxO2 有效热阻、界面贡献、HZO 体积热容 | `VERIFIED` HZO 热物性部件；堆栈和厚度不等同 FerroX MFIM |
| S8 | [HZO 薄膜热导率实验](https://doi.org/10.1016/j.jeurceramsoc.2020.12.053) | 未掺杂/掺杂 HZO 有效热导率约 0.75/0.67 W m-1 K-1 | `VERIFIED` 热扩散量级；不提供极化耗散热源或温度动力学 |
| S9 | [4–300 K HZO 开关实验](https://doi.org/10.1002/aelm.202300879) | 温度改变 P–V/PUND 与切换行为 | `VERIFIED` 温度相关性存在；不能替代局域 `T→P` 参数闭合 |
| S10 | [能量耗散约束铁电相场 PINN](https://arxiv.org/abs/2409.02959) | 铁电相场、能量耗散约束与 PINN 的已有组合 | `VERIFIED` 阻断“FerroX + PINN”宽泛首创主张 |
| S11 | [3D 铁电 TDGL 动态监督代理](https://doi.org/10.1038/s41524-024-01375-7) | 动态铁电畴演化的机器学习代理 | `VERIFIED` 动态代理已有先例；与本计划的 PINN/TKC 评价合同不等同 |

### Zenodo 固定清单

| 文件 | 字节数 | MD5 |
|---|---:|---|
| `Fig3_3D.tar.gz` | 266137069 | `93292545ffd717453203d8bbd09559b8` |
| `Fig4.tar.gz` | 680901979 | `fe2b64e65b23312591725a3e70dcece5` |
| `Fig3_Supp.tar.gz` | 926509406 | `d924c736d2eff6b9e5a3e8410b388a14` |
| `Fig3_2D.tar.gz` | 20339878 | `664d752ea346cdf1357bff1402eb4023` |

本次只读取官方元数据，没有下载、解包或运行这些文件。

## 3. 来源与许可/版本表

| 对象 | 计划要求 | 本次结果 | 门状态 |
|---|---|---|---|
| FerroX code | 论文短哈希解析为 full commit/tree | `002bddf6368d4de94a3b623c6a16e1f0d597e82b` / `da2e4a8725cfed389da970a749c17b72b76086ff` | PASS |
| FerroX exact-revision license | 固定提交时存在且允许修改/再分发 | 固定 tree 无许可文件；当前许可为 2024 development 资产 | **FAIL** |
| AMReX dependency | `3dda62` 解析为 full commit/tree | 官方 API 当前无法解析 | **FAIL** |
| Reference data | version DOI、许可、文件、校验值 | DOI 与 CC-BY-4.0、四文件 MD5 已闭合 | PASS |
| Drift control | 禁用 development/main 替代论文版本 | 已冻结为规则；本次没有 clone 或移植 | PASS |

`SUPPORTED_INTERPRETATION`：即使未来能证明当前许可对历史版本具有追溯适用性，也仍需一个新的、明确授权的来源身份审查来替代本次记录；不得在本次 P0 内静默作此法律推断。

## 4. 唯一热机制合同审查

计划允许的 R2-v1 热闭环应满足：

\[
\dot P=-L(T)\,\frac{\delta F(P,T,\phi)}{\delta P},
\qquad
C_v\dot T-\nabla\!\cdot(k\nabla T)=q_{\rm irr}(P,T)+q_{\rm rev}(P,T),
\]

其中不可逆极化黏滞耗散的符号和量纲由完整能量恒等式决定，可逆项不能被省略后仍称“严格热力学闭合”。温度至少反馈一个 HZO 自由能系数和 `L(T)`/`Gamma(T)`；`J·E`、泄漏和电流连续不属于 R2-v1。

| 合同项 | FerroX/来源提供情况 | P0 状态 |
|---|---|---|
| TDGL、Poisson、平衡载流子 | FerroX 提供 | `VERIFIED` |
| 动态热方程 | FerroX 不提供；Wang 提供跨材料方程结构 | `VERIFIED_ABSENT_IN_FERROX` |
| 不可逆极化耗散与可逆热项 | 可由 Wang 的 BaTiO3 热力学框架规定结构 | `SUPPORTED_STRUCTURE_ONLY` |
| HZO 绝对时间与维度化 `L(T)`/`Gamma(T)` | FerroX `Gamma=100` 未形成可审计的 HZO 温度标定链 | `UNKNOWN_NOT_CLOSED` |
| HZO 温度依赖自由能系数 | 温度影响开关有实验支持，但局域系数/有效温区未在同一链闭合 | `UNKNOWN_NOT_CLOSED` |
| HZO `C_v`、`k`、界面热阻 | 有薄膜测量部件，但几何/堆栈不等同目标 MFIM | `PARTIAL_NOT_A_DEVICE_CONTRACT` |
| MFIM 热边界与接触 | 原生 FerroX 协议未定义 | `UNKNOWN_NOT_CLOSED` |
| Joule/leakage | FerroX 无动态电流连续和 HZO 导电律 | `EXCLUDED_BY_CONTRACT` |

`VERIFIED`：不能把 `sigma|E|^2` 直接附加在 FerroX 的 Poisson 场上；这样既没有 `J` 的守恒闭合，也违反本次不扩方程的授权边界。若后续证据表明泄漏不可忽略，按冻结规则应关闭 R2-v1，而不是补造 Joule 路线。

## 5. 零求解量纲与可辨识性

以下只是不运行求解器的尺度计算，不是 oracle 或 HZO 定量验证。

1. 由 FerroX 的 Landau 系数可得候选自发极化量级 `P_s ≈ 0.195 C m-2`、零场势垒量级约 `24.5 MJ m-3`。若把该势垒全部、瞬时、局部且不可逆地转成热，并用 Scott 的 HZO 名义体积热容 `2.18 MJ m-3 K-1`，绝热温升上界约 `11.2 K`。这只是极宽上界；现有链没有给出外功、可逆热、储能与耗散的 HZO 分解，不能把它当可信温升。
2. 取 `k = 0.75 W m-1 K-1` 与 `C_v = 2.18 MJ m-3 K-1`，名义热扩散率约 `3.44e-7 m2 s-1`，5 nm 膜厚扩散时间 `L^2/alpha ≈ 73 ps`。
3. 将 Scott 的晶化薄膜有效热阻 `15.81 m2 K GW-1` 与 5 nm HZO 面热容相乘，名义 lumped 时间约 `172 ps`。该映射跨厚度/堆栈，只可作为数量级警示。
4. FerroX 的数值时间步和三角波调度可从代码/论文读取，但在缺少 HZO 维度化 `L(T)`/`Gamma(T)` 与同器件热边界时，不能把数值扫描率解释为已校准的物理驱动时间。

`SUPPORTED_INTERPRETATION`：现有热物性更支持“纳米厚度方向温度快速均匀化”的风险，而不是自动支持一个可辨空间局域温度时钟。由于可信耗散份额、目标 MFIM 热边界、切换时间温敏度和 oracle 误差地板都未闭合，无法证明热效应达到 `5 ×` 数值不确定性；热源强度仍保留不可允许的自由尺度。因此 `THERMAL_VALUE` 不能判 PASS。

## 6. 创新碰撞矩阵

| 候选主张 | 一手碰撞 | P0 结论 |
|---|---|---|
| “FerroX + PINN” | S10 已有铁电相场 PINN 与能量耗散约束 | `NOVELTY_CLAIM_REJECTED` |
| 动态铁电畴 ML | S11 已有 3D TDGL 动态监督代理 | 不能把“动态代理”作为首创 |
| 能量耗散作为 PINN 约束 | S10 | 只能作为透明强基线/约束，不是标题创新 |
| 单调时间重参数化 | 跨 PDE/PINN 已有广义时间变换先例；本次未发现与 R2 完全同构的 HZO 局域温度时钟 | 精确 TKC 碰撞为 `UNKNOWN`，不得提前宣称首创 |
| 残差/界面自适应采样 | 已有 PINN 自适应采样家族 | 只能作来源透明强基线，不进入主要创新标题 |
| 只作用于极化网络的局域温度动力学时钟及完整混合导数回拉 | 本次 11 项有界来源中未发现精确同构 | `HYPOTHESIS_ONLY`；须先有合格物理对象、strong raw 时间瓶颈和 shuffle 负控才可评价 |

新颖性没有触发本次单一 No-Go：宽泛主张已被否决，窄 TKC 假设仍未获得正向证据。来源身份门已先终止路线，故不继续扩充检索或形成 formal novelty claim。

## 7. 冻结事件合同的 P0 处置

`VERIFIED`：官方 y-invariant MFIM 截面与多次双极三角波下的多畴/单畴转换可以由 S1 固定为未来重放线索。`UNKNOWN`：该数值协议的 HZO 绝对时间、与热扩散/热边界的匹配及可作为严格热 oracle 的身份没有闭合。来源中没有在相同严格热模型上提供第二个原生备用协议，因此本次没有自行创造 fallback。

授权包 B 的事件阈值、网格收敛和 Q–V 标准均未运行、未评价。官方等温畴图不能被升格为 R2 热耦合研究图。

## 8. 终止与允许的后续动作

- 当前 R2 终止于 `R2_P0_SOURCE_IDENTITY_NO_GO`；授权包 B–D 保持 `NOT_AUTHORIZED`。
- 不 clone/build/run FerroX 或 AMReX，不下载参考数据，不写 `ThermoFerroXContract`、oracle、PINN 或训练协议。
- 不以 current development 替代论文版本，不把 BaTiO3 参数或跨堆栈 HZO 热参数拼接成定量验证。
- 不自动启动 R3、HFO-NP-v1 或其他对象。
- 如用户未来希望重新打开 R2，必须先给出实质改变来源身份合同的新方案，例如可审计的许可适用链和可解析依赖身份；本报告本身不构成该授权。

## 9. 证据边界

- `VERIFIED`：官方元数据、固定 tree 内容、Zenodo 文件元数据、论文明确方程/参数/事件与已发表热物性。
- `SUPPORTED_INTERPRETATION`：快速热扩散使局域温度时钟面临可辨识性风险；这是数量级解释，不是数值求解结论。
- `HYPOTHESIS`：严格闭合且可辨的局域温度动力学可能为 TKC 提供时间瓶颈；本次未测试。
- `UNKNOWN`：HZO 专属耗散份额、绝对 `L(T)`/`Gamma(T)`、目标 MFIM 热边界、热效应相对离散地板、TKC 对 strong raw 的增量。

本报告不是实验验证、FerroX 作者热模型、HZO 定量预测、PINN 结果、SOTA 或期刊可接收性证明。
