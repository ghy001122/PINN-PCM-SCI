# GOAL-PAPER-ONE-SHOT-V1 S1 来源、合法性与 CTH 新颖性前审

- `report_id`: `GOAL_PAPER_ONE_SHOT_V1_S1_SOURCE_LEGAL_NOVELTY_V1`
- `review_date`: `2026-08-26`
- `review_scope`: `COMSOL_APPLICATION_141181_6_4 + PCMO_REACTION_DRIFT_FALLBACK + BOUNDED_CTH_PRIOR_ART`
- `deep_review_candidates_used`: `2 / 2`
- `reviewed_primary_carriers`: `13`
- `new_to_project_primary_carriers_used`: `10 / 12`
- `preexisting_reused_primary_carriers`: `3`
- `claim_status`: `BOUNDED_PRIMARY_SOURCE_REVIEW_NO_NUMERICAL_OR_METHOD_EVIDENCE`
- `route_verdict`: `ROUTE_1_FAIL + ROUTE_2_FAIL + ACTIVATE_SYN_EDT_2D_V1`
- `cth_verdict`: `NO_EXACT_BUNDLE_COLLISION_IN_THIS_BOUNDED_SET / POSITIVE_ARCHITECTURE_NOVELTY_NOT_CLEARED`

本报告是 S0 冻结合同下的一次有界来源裁决，不是法律意见，也不证明任何数值、PINN 或方法主张。预注册代码 `LEGAL_RESEARCH_ACCESS_FAILURE` 在本报告中只表示“可用证据未建立当前路线要求的研究使用 PASS”，不表示已经证明用户或其机构没有许可证、公开临时下载违法，或任何司法辖区下一概禁止自主 PDE 实现。本报告不评价任何机构或个人在其他许可证、司法辖区或书面协议下的权利。

## 1. 结论优先

| 审查对象 | 最早决定性结果 | 有界裁决 | 自动动作 |
| --- | --- | --- | --- |
| Route 1：COMSOL Application 141181，6.4 | COMSOL 6.4 官方 SLA 把 Example 使用绑定到有效授权使用，并对利用 Programs 开发竞争/替代软件设限；当前可用证据没有建立冻结路线所需的研究使用与结果发表 PASS。临时资产审计闭合了 exact build 与 solved-payload 存在性，但仍未闭合 domain 5 初态、完整默认树、TCC 稳定化和可独立提取的机器可读参考输出 | `LEGAL_RESEARCH_ACCESS_FAILURE`（PASS 未建立）` + SOURCE_CONTRACT_FAILURE` | 关闭 Route 1，启用预冻结 Route 2 |
| Route 2：PCMO reaction–drift | 原文明确把最终模型称为 simple point-device model；陷阱密度和温度均匀，电流来自未公开的 Sentaurus TCAD LUT，动态由 MATLAB 中的 lumped ODE 更新 | `SOURCE_CONTRACT_FAILURE` | 关闭 Route 2，启用 `SYN_EDT_2D_V1` |
| CTH 正向方法身份 | 本轮未找到相同的 `q0 + δq1 + δ²q2 + |δ|h` transport-only 完整束，但 conditional/parameterized PINN、parameter encoder、hypernetwork、绝对值 cusp feature、spline 与 learned/fixed basis 均有直接先例 | `NOT_NOVELTY_CLEARED_FOR_POSITIVE_ARCHITECTURE_CLAIM` | CTH 最多保留为预注册诊断/比较臂；对象路线转 synthetic benchmark/comparative，不以 CTH 作为已清除的新架构 |

因此，S1 的无凭据、无付费、无作者联系路线推荐是：**按预注册表立即激活 `SYN_EDT_2D_V1`；不再为 COMSOL 或 PCMO 补来源，不把 CTH 写成通用新 PINN 原语。**

## 2. 搜索范围、停止条件与载体记账

### 2.1 固定载体清单

同一论文的 DOI 与其作者稿版本按一个学术载体计；COMSOL Application Gallery 页面及该页面调用的同一 `Application ID` 官方文件列表端点按一个资产记录计。没有把搜索摘要、内部聊天、二手综述或 AI 内容计为来源。

| ID | 一手载体 | 本轮角色 | 固定链接/标识 |
| --- | --- | --- | --- |
| C01 | COMSOL Application Gallery：Memristor，Application ID 141181；含同记录官方文件列表 | Route 1 资产身份 | [Application 141181](https://www.comsol.com/model/memristor-141181)；文件列表由该页官方 `/models/get-the-files` 端点按 `id=141181` 返回 |
| C02 | COMSOL 6.4 Application Library PDF，`models.semicond.memristor.pdf`，asset `1585101` | Route 1 物理/模型树深审 | [COMSOL 6.4 model PDF](https://www.comsol.com/model/download/1585101/models.semicond.memristor.pdf) |
| C03 | COMSOL Software License Agreement 6.4 | Route 1 使用、输出、Example 与独立实现权利 | [COMSOL 6.4 SLA](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/comsol_la_license.04.1.html) |
| C04 | COMSOL Notice of Academic Licensed Rights | Route 1 学术研究资格边界 | [Academic licensed rights](https://www.comsol.com/legal/academic-licensed-rights) |
| C05 | Saraswat et al., *Reaction-Drift Model for Switching Transients in PCMO-Based Resistive RAM*, arXiv:2005.07398v1 / DOI 10.1109/TED.2020.3011387 | Route 2 对象深审 | [arXiv record](https://arxiv.org/abs/2005.07398)，[author manuscript](https://arxiv.org/pdf/2005.07398)，[DOI](https://doi.org/10.1109/TED.2020.3011387) |
| C06 | Kovacs et al., *Conditional physics informed neural networks*, arXiv:2104.02741v1 / DOI 10.1016/j.cnsns.2021.106041 | CTH prior art | [arXiv record](https://arxiv.org/abs/2104.02741) |
| C07 | Belbute-Peres et al., *HyperPINN*, arXiv:2111.01008v1 | CTH prior art | [paper](https://arxiv.org/pdf/2111.01008) |
| C08 | Cho et al., *Parameterized Physics-informed Neural Networks for Parameterized PDEs*, arXiv:2408.09446 / ICML 2024 | CTH prior art | [arXiv record](https://arxiv.org/abs/2408.09446)，[ICML/OpenReview paper](https://openreview.net/pdf?id=n3yYrtt9U7) |
| C09 | McClenny and Braga-Neto, *Self-Adaptive PINNs using a Soft Attention Mechanism*, arXiv:2009.04544 | CTH prior art | [arXiv record](https://arxiv.org/abs/2009.04544) |
| C10 | Tseng et al., *A cusp-capturing PINN for elliptic interface problems*, arXiv:2210.08424 | CTH prior art | [arXiv record](https://arxiv.org/abs/2210.08424) |
| C11 | Wandel et al., *Spline-PINN*, arXiv:2109.07143v2 / AAAI 2022 | CTH prior art | [arXiv record](https://arxiv.org/abs/2109.07143) |
| C12 | Wang et al., *Physics-Informed Deep B-Spline Networks (PI-BSNet)*, OpenReview `x1TWOnfTX8`, ICLR 2026 | CTH prior art与 learned/fixed basis | [OpenReview record](https://openreview.net/forum?id=x1TWOnfTX8)，[paper PDF](https://openreview.net/pdf?id=x1TWOnfTX8) |
| C13 | COMSOL `memristor.mph` vendor binary，asset `1471921`；临时只读 archive-metadata 审计后删除 | Route 1 exact build、asset hash 与 solved-payload 存在性 | [official asset endpoint](https://www.comsol.com/model/download/1471921/memristor.mph)；SHA256 `14A1A8356B6FDA3C2B2CCBC2F4458C0F610CD47C4EE924602D4DBD49C8983FA3` |

载体账本区分“本轮实际审阅”与“首次进入项目”：C01、C05、C08 在本轮前已有项目记录，属于复用载体；C02、C03、C04、C06、C07、C09、C10、C11、C12、C13 为本轮首次进入项目的十个一手载体。因此本轮实际审阅 `13` 个载体，使用新增预算 `10 / 12`，深审对象 `2 / 2`；未把独立承载 build/hash/payload 事实的 C13 静默并入 C01。精确式检索还使用了 `q0 delta q1 delta^2 q2 PINN`、`|delta| physics-informed parameter`、`PINN absolute-value parameter cusp` 与对应 OpenReview/arXiv 限域查询；没有把这些查询返回的其他作品纳入事实链，也没有据此宣称全局无碰撞。

### 2.2 合规动作边界

- 读取公开 HTML/PDF、同一 Gallery 记录的文件元数据；主线程随后把公开 6.4 `.mph` 下载到系统临时目录，核对字节数、SHA256、公开 manifest/build 与 archive entry 清单后删除。原始资产从未进入项目目录、复现包或外部上传。
- 没有使用 COMSOL 凭据、许可证、试用许可或商业运行时，没有启动模型、读取求解场数组、联系作者或再分发原始 `.mph`。
- 没有求解、训练、创建外部账户、上传、发布或访问付费全文。

## 3. Route 1：COMSOL Application 141181（6.4）

### 3.1 官方资产身份

`VERIFIED`（C01–C02、C13）：

- Gallery 名称为 **Memristor**，Application ID 为 `141181`。官方页面只承诺氧化物忆阻器、氧空位 drift–diffusion、current continuity 与 heat transfer 的 fully coupled model，并引用 Kim、Choi 与 Lu 2014。
- 同一 Gallery 记录的官方文件列表给出 6.4 两个资产：
  - `memristor.mph`：`/model/download/1471921/memristor.mph`，页面标称 `56.71 MB`；headers-only 检查为 HTTP 200、`Content-Type: application/vnd.comsol`、`Content-Length: 59,463,566`、`Last-Modified: 2026-03-19`。
  - `models.semicond.memristor.pdf`：`/model/download/1585101/models.semicond.memristor.pdf`，页面标称 `0.58 MB`。
- C02 首页面只写 `Model created in COMSOL Multiphysics 6.4`。对 C13 vendor binary 的临时只读 archive-metadata 审计进一步固定：`Content-Length=59,463,566`，SHA256 `14A1A8356B6FDA3C2B2CCBC2F4458C0F610CD47C4EE924602D4DBD49C8983FA3`，`fileversion/modelinfo.xml=COMSOL 6.4.0.257`，`createdIn=COMSOL Multiphysics 6.4 (Build: 257)`，`lastComputationVersion=COMSOL 6.4.0.257`。Application Library path 为 `Semiconductor_Module/Device_Building_Blocks/memristor`。
- C13 archive metadata entries 标记 `nodeType=solved`，entry 清单含 `solution1.mphbin`、`solutionstatic1.mphbin` 与五个 `solutionblock*.mphbin`；这只证明 vendor payload 存在，不证明本项目在无授权运行时下可合法、独立、机器可读地提取参考场。
- C02 给出 2D-axisymmetric 四个主矩形及一个由 layer 操作生成的导电细丝域：上下 Pd 电极各 30 nm；氧化层 30 nm 与 5 nm；半径 20 nm；CF 半径 5 nm。
- 固定参数为 `T0=300 K`、`n0=1e21 cm^-3`、hopping distance `a=0.1 nm`、escape frequency `f=1e12 Hz`、barrier `Ea=0.85 eV`。
- 电压表为 `(t[s],V)=(0,0),(0.6,1.2),(1.2,0),(1.7,-1),(2.2,0)`；文档另称 ramp rate 为 `2 V/s`。输出时间为 `range(0,0.01,2.2)`。
- 电流定义为 `I=-intop1(ec.JZ)`，积分边界为 boundary 9；结果图使用 `V0(t)` 为横轴。

### 3.2 物理与本构事实

`VERIFIED`（C02）：

- Electric Currents 与 Heat Transfer in Solids 均设置为 stationary equation form，但整体 study 为 time dependent；Joule Heating 提供电热耦合。
- TCC 选中 domains 2、3、5；内置 electric-field drift 被关闭，convection 被开启，速度由文档变量给定：Mott–Gurney 电场漂移减 Soret 速度；扩散系数为 `D_n=0.5 a^2 f exp(-Ea/(k_B T))`。
- `sigma=sigma0(k) exp(-E_AC(k)/(k_B T))`，`k=n/n0`；`k_th=k_th0(k)[1+0.1 K^-1(T-T0)]`。
- 插值节点为：`sigma0(0)=10 S/cm, sigma0(1)=940 S/cm`；`E_AC(0)=0.05 eV, E_AC(0.5)=E_AC(1)=-0.006 eV`；`k_th0(0)=0.12 W/(m K), k_th0(1)=57.5 W/(m K)`。
- Pd 赋给 domains 1、4；TaₓOᵧ 赋给 domains 2、3、5。电势 ground 为 boundary 2，`V0(t)` 为 boundary 9；温度 `T0` 施加于 boundaries 2、9；TCC No Flux 选择 All boundaries。
- TCC 的显式 `Initial Values 2` 只选 domains 2、3 并设 `nn=n0`；文档未显示 domain 5 继承的默认 `Initial Values 1` 数值。

### 3.3 权利裁决

| 冻结权利项 | 官方条款事实 | 当前项目裁决 |
| --- | --- | --- |
| `COMSOL64_RESEARCH_USE_RIGHT` | C03 §2 只在协议期限内授予 Programs、Documentation 与 Examples 的有限、不可转让使用权；§2(c) 把 Example 使用绑定到 authorized use。C04 又限定下载和软件只能由对应机构协议下的 eligible users 使用，CKL 不得用于 academic research。 | `RESEARCH_USE_RIGHT_NOT_ESTABLISHED / FAIL_CURRENT_ROUTE`。当前可用证据没有闭合许可证类型、有效期、机构协议与 authorized-user 身份；公开 URL 本身不能建立研究使用 PASS。该状态不是“证明许可证不存在”。 |
| `COMSOL64_MODEL_FILE_ACCESS` | C01 的 6.4 `.mph` URL 技术上公开可达，C13 临时文件的长度、哈希和 archive metadata entries 已核对。C03/C04 仍把 Example/download 使用绑定到有效授权。 | `TECHNICAL_ASSET_ACCESS_PASS / LAWFUL_EXECUTABLE_ACCESS_NOT_PASS`。本地没有已核验 6.4 运行时或有效 license identity；临时 archive-metadata 审计不等于可执行研究访问。 |
| `COMSOL64_RESULT_PUBLICATION_RIGHT` | C03 §3 允许用户拥有不复制 Program 或 COMSOL-published Model 实质元素的计算数据；用户创建的 Models 可按协议使用/发表。C03 §2(m) 明确禁止发表 trial-license 结果。 | `CONDITIONAL_ONLY_NOT_CURRENT_PASS`。有效非试用许可证下的独立结果存在条件式发表路径；当前许可身份未闭合，且不得把 COMSOL 发布模型的实质元素当作自有输出。 |
| `COMSOL64_MPH_REDISTRIBUTION_RIGHT` | C03 §2(c) 只明确允许在 authorized use 下以 Example 为起点；只有修改/新增足够实质时才授予 modified Example 的使用、修改、发表与分发权，第三方作者 notice 另有限制。 | `UNKNOWN / RAW_VENDOR_MPH_NOT_AUTHORIZED_FOR_REPRO_PACKAGE`。没有依据允许再分发原始 `1471921` `.mph`；本项虽非 Route 1 前三项之一，仍保持关闭。 |
| `INDEPENDENT_CLEANROOM_CODE_LICENSE` | C03 §2(h)(xi) 对利用 Programs 开发功能相同、实质相近、竞争或可替代 Programs 的独立软件设限；C02 没有另附独立求解器许可。条款本身不足以裁决所有基于公开科学方程的自主 PDE 实现。 | `NOT_ESTABLISHED_FOR_COMSOL_SPECIFICATION_ALIGNED_IDENTITY`。可用证据不能给 `COMSOL_6_4_TUTORIAL_SPECIFICATION_ALIGNED` 独立 solver 身份形成许可 PASS；这不是对所有 bespoke PDE 实现的 blanket prohibition。当前 synthetic route 明确脱离该身份。 |

上述裁决不声称公开阅读 C01/C02 本身违法；它只说明冻结路线要求的研究使用、可执行模型和独立代码权利没有形成 PASS。

### 3.4 S0 完整来源合同矩阵

| 必需字段 | C02 中直接事实 | 状态 |
| --- | --- | --- |
| `domain_5_initial_state` | TCC 包含 domains 2、3、5；显式 `Initial Values 2` 仅覆盖 2、3。domain 5 默认值未列。 | `FAIL_UNKNOWN` |
| `all_domain_selections` | 材料和 TCC 域有列；EC/HT 的完整 feature selections、layer 产生域的全部继承关系未逐项列。 | `PARTIAL` |
| `electric_currents` | Stationary EC、ground 2、potential 9、线性离散明确。 | `PASS` |
| `heat_transfer` | Stationary HT、`Tref=T0`、boundaries 2/9 温度明确。 | `PASS` |
| `transport_of_concentrated_species` | 实际接口名为 Transport of Charge Carriers；domains 2/3/5、diffusion 与 convection 明确。 | `PASS_IDENTITY_SCOPED` |
| `joule_heating_coupling` | Model Wizard 明确添加 Joule Heating。 | `PASS` |
| `all_initial_boundary_interface_conditions` | 主要外边界有列；domain 5 TCC 初态、所有默认边界 feature、内部 interface 的逐 feature 数值未闭合。 | `FAIL_PARTIAL` |
| `no_flux_axisymmetry_insulation_internal_continuity` | 2D axisymmetric 与 TCC all-boundary No Flux 明确；EC insulation、HT 默认边界、内部电/热 continuity 未显式冻结。 | `FAIL_PARTIAL` |
| `transport_electrical_thermal_constitutive_laws` | `D_n`、Mott–Gurney/Soret 速度、`sigma(k,T)`、`k_th(k,T)` 和 Pd 常数均给出。 | `PASS` |
| `tables_interpolation_extrapolation_units` | 三张表的节点和单位给出；interpolation method、extrapolation rule 与超范围行为未给出。 | `FAIL_PARTIAL` |
| `tcc_formulation_and_stabilization` | drift checkbox off、convection on、diffusion `D_n` 给出；space/time formulation、consistent/inconsistent stabilization 与默认版本值未给出。 | `FAIL_UNKNOWN` |
| `port_current_sign_and_axisymmetric_integration` | `I=-intop1(ec.JZ)` 与 boundary 9 给出；轴对称积分的精确权重/设置未在文档中展开。 | `FAIL_PARTIAL` |
| `exact_build_asset_identity_and_model_tree` | C13 vendor binary 的 archive metadata entries 固定 build `6.4.0.257`、asset hash、solved identity 和 entry 清单；PDF 给出手工树。完整默认/自动 feature 取值仍未闭合为可独立使用的 clean-room 合同。 | `BUILD_AND_ASSET_PASS / FULL_DEFAULT_TREE_FAIL_PARTIAL` |
| `machine_readable_reference_outputs` | `.mph` 清单证明 vendor binary solution payload 存在；没有 CSV/XLSX/TXT/reference table，本项目也没有已核验 COMSOL 运行时/许可来合法导出场。 | `VENDOR_PAYLOAD_EXISTS / INDEPENDENT_REFERENCE_OUTPUT_FAIL` |

即使暂不考虑许可，`domain_5_initial_state`、TCC stabilization、完整默认 feature 取值与可独立使用的 machine-readable reference outputs 已足够触发 `SOURCE_CONTRACT_FAILURE`。不能从 COMSOL 默认值、图像读数或 6.3 资产补造 6.4 合同。

## 4. Route 2：PCMO reaction–drift fallback

### 4.1 原文直接事实

`VERIFIED`（C05）：

- 实验器件为 W/PCMO/Pt，文首称 PCMO film 约 60 nm、top contact 约 1 μm；simulation section 的 current LUT 使用 `L=65 nm`、area `1 μm²`。
- 动态程序在 MATLAB 中执行。状态变量是输入电压 `V(t)`、电流 `I(t)`、uniform trap density `N_T(t)` 与 uniform device temperature `T(t)`。
- 原文明确列出三个近似：trap density 无空间依赖、temperature 无空间依赖、hole current response 比热和离子 reaction–drift 快。
- Hole current 不是由公开方程/网格实时求解，而是来自 Sentaurus TCAD 的 quasi-static LUT；LUT 以 fixed uniform `N_T` 与 isothermal `T` 为轴。TCAD 解 Poisson、carrier continuity 与 statistics，但 deck、材料文件和 LUT 没有在论文中给出。
- Trap density 由 Mott–Gurney drift 与 first-order reaction equilibrium 推出的 ODE 更新；温度由 lumped balance `(T-Tamb)/Rth + cs dT/dt = I V` 更新。
- 初始条件为 `V=I=0`；LRS `N_T0≈10^18 cm^-3` 或 HRS `N_T0≈10^20 cm^-3`；`T=Tamb`。
- 输入先在 20 ns 从 0 ramp 到固定 `Vapp`，随后固定 bias。Table I 给出 `Vapp=±[1.3,2.5] V`、`Tamb=300–475 K`、`a=0.5 nm`、`f=1e13 Hz`、`Em=0.8 eV`、`cv=2e7 J m^-3 K^-1`、`λ≈6 W m^-1 K^-1`。
- Set 使用约 10 mA compliance；原文明确说明 compliance 后实际电压会降低，但仪器输出不显示实际值，simulation 仍显示 setpoint 而非实际电压。
- 结论把模型称为 `simple point device model`，不是二维空间离子输运模型。

### 4.2 完整来源合同裁决

| 合同维度 | 原文闭合度 | 状态 |
| --- | --- | --- |
| 二维及以上器件几何 | 只用 thickness 与 contact area 的 point/lumped model；没有二维场域、网格或空间离子态。 | `FAIL` |
| 电—热—守恒缺陷输运 | 有 DD+SH+RD 物理故事，但最终动态是 TCAD LUT + lumped thermal ODE + uniform trap ODE；没有公开守恒 Nernst–Planck/continuity defect field。 | `FAIL_FOR_REQUIRED_TOPOLOGY` |
| 完整 IC | 两个起始 trap-density 量级和 `Tamb` 给出；没有完整 TCAD carrier/Poisson 初态、LUT initialization 或 case-by-case exact values。 | `PARTIAL` |
| 完整 BC/interface | reactive W interface 只作机理叙述；空间 BC/interface 不存在于公开 point model，TCAD deck 未公开。 | `FAIL` |
| 绝对协议 | 20 ns ramp 和 fixed bias 范围给出；Set compliance 后实际施加电压明确未知/未输出。 | `FAIL_FOR_EXACT_WAVEFORM` |
| 输出与 reference data | 论文给出 figures 与定性/量级比较；没有机器可读 transient、LUT 或完整场输出。 | `FAIL` |
| solver/code identity | 只说明 MATLAB + Sentaurus TCAD；没有 commit、archive、source tree、deck、LUT 或 executable manifest。 | `FAIL` |
| code/data/license | arXiv 作者稿可公开阅读，但没有为 MATLAB、TCAD files、LUT 或数据给出独立下载与许可证。 | `UNKNOWN_NOT_PASS` |
| 可重建性 | 关键 current map `I(N_T,T;V)` 和 TCAD/material parameter files 缺失，不能由论文表格唯一重建。 | `FAIL` |

`SUPPORTED_INTERPRETATION`：C05 是 reaction–drift、自热与电子 transport 耦合的有效科学先例，但不满足本 GOAL 的二维守恒 defect-transport 对象合同。把它扩展为 2D Nernst–Planck 对象将是新的 `A_PRIME/ENGINEERING` 研究对象，不是该论文的 source-aligned replay；S0 已禁止用来源拼接救援 fallback，因此 Route 2 在 S1 收口。

## 5. CTH 有界新颖性/碰撞矩阵

本节审查的冻结身份是 transport-only

\[
q_{\mathrm{tr}}=q_0+\delta q_1+\delta^2q_2+|\delta|h,
\qquad (c_v,\mathbf J_v)=B(q_{\mathrm{tr}}),
\]

及其 parameter-conditioned PINN、exact smooth `P4` kill control 与 off-grid complete-case 证据。检索问题不是“是否存在同名 CTH”，而是 load-bearing mechanism 是否已有直接先例。

| 先例 | 直接事实 | 与 CTH 的碰撞 | 本轮未见的部分 | 裁决 |
| --- | --- | --- | --- | --- |
| Conditional PINN（C06） | 把 PDE/缺陷参数作为 tag，与空间点一同输入单个网络；一个网络学习整类 PDE/eigenvalue problems。 | “一个 parameter-conditioned PINN 学习完整参数族”不是新机制。 | 没有 transport-only `|δ|` basis、P4 identity control 或 memristor event endpoint。 | `BROAD_CONDITIONAL_COLLISION` |
| HyperPINN（C07） | Hypernetwork 以 PDE 参数为输入，生成每个参数化对应的 main PINN weights。 | 参数到 solver representation/weights 的 learned map 已有直接先例。 | 不是显式 Taylor2+hinge transport basis。 | `BROAD_META_CONDITIONING_COLLISION` |
| P²INNs（C08） | Separate parameter encoder `g(μ)` 构造 latent parameter manifold，再 parameterize solution network；另报告 SVD-based modulation。 | learned parameter representation、separate encoder 与低维/SVD modulation 已直接覆盖 CTH 的“参数轴表示”广义贡献。 | 没有固定 `|δ|` kink 与 exact `P4` kill。 | `LEARNED_PARAMETER_BASIS_COLLISION` |
| SA-PINN（C09） | 每个 training point 有可训练权重；对应 loss 越大权重越大，形成 residual/IC/BC soft-attention map。 | residual-sensitive/self-adaptive training 不能归入 CTH 独创，也必须作为不同机制控制。 | 不生成参数 kink basis，不是 direct parameter Jacobian。 | `TRAINING_CONTROL_COLLISION_ONLY` |
| Cusp-capturing PINN（C10） | 把 level-set 的绝对值 `|φ(x)|` 作为 non-differentiable augmented feature，使平滑网络可表达 interface 上的一阶导数 cusp。 | “向 PINN 输入显式绝对值 cusp feature 来表达导数折点”是对 `|δ|` load-bearing idea 最直接的结构先例。 | C10 的 cusp 是已知空间界面，不是 learned protocol-parameter transport hinge；没有完整器件事件或 P4 control。 | `DIRECT_ABSOLUTE_VALUE_CUSP_FEATURE_COLLISION` |
| Spline-PINN（C11） | Hermite-spline kernels 连续插值 grid state，并由 CNN 处理；仅用 physics-informed loss，无预计算训练数据。 | spline/structured basis 与物理残差结合已有先例。 | 不是 parameter-family hinge placement，也不学习 CTH 的 q-basis。 | `SPLINE_REPRESENTATION_COLLISION` |
| PI-BSNet（C12） | 以 B-spline basis 表示 parameterized PDE family，由网络学习 compact control points；解析求导，并通过 control points 严格施加 IC/Dirichlet BC。论文还明确讨论 fixed basis 与 learned basis 的取舍。 | parameterized family + fixed structured basis + learned coefficients/control points 已直接覆盖 CTH 的 basis-family 广义主张，也支持强 `PI_BSNET_LIKE_SPLINE` 与 learned-basis controls 的必要性。 | 没有 transport-only绝对值 hinge、P4 identity 或 memristor event。 | `FIXED_AND_LEARNED_BASIS_COLLISION` |

### 5.1 新颖性裁决

- `VERIFIED`：在上述七个预注册类别、固定版本和精确式查询中，没有找到相同的 CTH 完整式、相同五个训练节点/P4 恒等控制、相同 transport-only placement 与相同两周期局部事件端点。
- `SUPPORTED_INTERPRETATION`：未见 exact bundle 不能清除新颖性。CTH 的全部 load-bearing 组件——conditional family learning、learned parameter encoding/modulation、绝对值 cusp feature、structured spline basis、learned/fixed basis 与 residual-adaptive controls——均已有一手先例。
- `SUPPORTED_INTERPRETATION`：在项目规范要求“算法或网络架构具有可测实质创新”的门下，当前最强可守措辞仍是 S0 已冻结的 `CONDITIONAL_APPLICATION_SPECIFIC_TRANSPORT_ARCHITECTURE_ADAPTATION`。仅凭把这些组件放到 memristor transport 上，不能在 S1 升格为正向架构创新。
- `UNKNOWN`：更广数据库、全文专利、2026-08-26 后论文或不同术语下是否存在 exact bundle；本轮不作全球优先权、世界首创或 SOTA 结论。

因此，本报告给出 `CTH_POSITIVE_NOVELTY_ADMISSION_FAIL`。若后续 benchmark 仍实现 CTH，它只能作为预注册诊断/比较 arm，实际结果可以支持“该 application-specific adaptation 在冻结 benchmark 上有效/无效”的窄主张，不能倒推通用原语新颖性。

## 6. 自动路线推荐

```text
ROUTE_1 = FAIL(
  LEGAL_RESEARCH_ACCESS_FAILURE,
  SOURCE_CONTRACT_FAILURE
)

ROUTE_2 = FAIL(
  SOURCE_CONTRACT_FAILURE:
  POINT_DEVICE + UNPUBLISHED_TCAD_LUT + NO_2D_CONSERVATIVE_DEFECT_FIELD
)

NEXT_OBJECT_ROUTE = SYN_EDT_2D_V1
METHOD_ROUTE = DIAGNOSTIC_OR_COMPARATIVE_BENCHMARK
CTH_POSITIVE_ARCHITECTURE_ADMISSION = NOT_CLEARED_UNDER_THIS_GOAL
```

`SYN_EDT_2D_V1` 必须保持 S0 身份：`FULLY_TRANSPARENT_SYNTHETIC / TWO_DIMENSIONAL_AXISYMMETRIC / ELECTROTHERMAL_DEFECT_TRANSPORT_BENCHMARK / NOT_SOURCE_ALIGNED / NOT_EXPERIMENTALLY_VALIDATED`。C02 和 C05 可在论文 related work/physics motivation 中被透明引用，但其参数、默认值、LUT、曲线或许可不得被隐藏拼接进 synthetic contract。

## 7. 主张边界自检

### `VERIFIED`

- C01/C02 的公开页面/文档资产身份、文档明示模型结构、方程设置、参数、边界和输出定义；C13 vendor binary archive metadata 明示的 build、hash 与 solved-payload 存在性。
- C03/C04 明示的授权前提、Example、trial result、Program output、redistribution 与 independent-program restrictions。
- C05 明示的 point-device、uniform-state、MATLAB + Sentaurus LUT、lumped thermal/RD ODE、20 ns ramp 与 compliance 后实际电压缺失。
- C06–C12 各自明示的 conditional、hypernetwork、parameter encoder、self-adaptive weight、absolute-value cusp、Hermite spline 和 B-spline/learned-control-point 机制。

### `SUPPORTED_INTERPRETATION`

- 当前项目不能把公开 `.mph` URL 当作已获得合法研究使用权或独立 clean-room solver 许可。
- 两个来源对象都不满足 S0 完整来源合同，故应自动切换到 synthetic route。
- CTH 没有获得正向架构新颖性 clearance，但可在窄 benchmark 中作为透明比较臂。

### `UNKNOWN`

- `memristor.mph` 内完整默认 feature 取值、domain 5 initial value、stabilization 与 solution 数组内容；exact build 和 payload 存在性已由临时 manifest/entry 审计闭合。
- 用户或其机构在仓库外是否另有有效、非试用 COMSOL 许可证或 negotiated agreement；本轮未请求凭据，也不需要该动作来继续 fallback。
- 原始 COMSOL `.mph` 的无修改再分发权，以及独立司法辖区对 clean-room interoperability 的适用例外。
- C05 的 MATLAB、Sentaurus deck、LUT、实验 transient 数据和许可证身份。
- CTH 的全球新颖性、普适性、SOTA、真实物理 kink 或任何实验验证。

本报告没有把公开教程、作者稿、内部合同或搜索未命中转换成数值真值，也没有把 route failure 扩大为 COMSOL、PCMO、PINN、cusp feature、spline 或 parameterized PDE learning 的一般性失败。
