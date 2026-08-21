# IdeaSpark 研究产物全面综合审查报告

- 审查日期：2026-08-18
- 审查对象：`ideaspark_run/high-frequency-pinn-pcm/`
- 研究主题：面向相变材料/器件的抗高频 PINN
- 当前候选：**Kinetics-Clock PINNs for Endogenous High-Frequency VO₂ Switching Fronts**
- 总体处置：**REVISE_BEFORE_IMPLEMENTATION（修订后方可实施）**
- 科学状态：**PROPOSED_NOT_AUTHORIZED**

## 1. 执行摘要

本次 IdeaSpark 运行不是空洞的头脑风暴。它形成了从文献检索、瓶颈定位、三轮候选筛选、独立一致性追踪、碰撞审查到 Phase 4 卡片包装的完整产物链；两条失败路线及其反例被保留，最终候选也修复了有限求积时钟不保持单调性的真实错误。现有 71 个 JSON 均可解析，IdeaSpark 自带验证器重跑结果为 `7 pass / 0 warn / 0 fail`。

但是，**流程完整不等于科学闭合**。当前候选仍有两项机制级阻塞：

1. **formal OOD 任务与模型输入不一致。** 方案要求冻结检查点后预测未见几何和材料组合，但模型只读取空间坐标、局部动力学时钟与脉冲，没有几何/材料参数或域表示；当前写法既不是可执行的跨器件零样本代理，也没有明确改成“每个新器件重新训练的 PINN 求解器”。
2. **条件斜率公式遗漏显式脉冲输入项。** 方案一方面规定解头读取 `p(t)` 并在链式法则中保留 `f_p·p_dot`，另一方面又从 `r_tau=0` 与相态残差为零直接推出 `|xi_tau|=|K_xi|/sqrt(K_xi^2+k_floor^2)<1`。一般情况下应额外包含 `-xi_p·p_dot`；除非明确限定分段常值脉冲、去掉该显式输入路径，或改写主张，否则核心机制解释不成立。

此外，仓库中尚无被方案反复引用的 FEniCSx 器件模型、网格、参数、轨迹或收敛证据；VO₂ 电—热—相态物理闭合未冻结；新颖性检索对“学习坐标/内禀时间/反应进度变量”的历史近邻覆盖不足；最终三张卡还遗漏核心主张、证伪预测、预算与可行性结论，并存在数学标记损坏。

因此本报告的结论不是放弃该 idea，而是：

> **保留 Kinetics-Clock PINN 作为有潜力、可证伪的研究候选；在修复脉冲项与 OOD 定义、闭合物理模型和新颖性之前，不进入训练或论文主张阶段。**

## 2. 审查范围、证据等级与限制

### 2.1 审查范围

本次审查覆盖：

- 项目权威链及 IdeaSpark 项目绑定；
- Phase 0 文献池、相关性分区、全文缓存和 host recall；
- Phase 1 瓶颈与最近邻；
- 三轮 Phase 2/3 候选、执行型 coherence 证据与 abandon/advance 决策；
- 最终候选的数学数据流、物理含义、负对照、formal OOD、预算和停止条件；
- Phase 4 skeleton、fill、derive、method view、implementability、渲染卡片；
- 产物完整性、可追溯性、新鲜度、渲染质量和治理状态一致性。

本次没有新增文献检索、没有建立或运行物理求解器、没有训练 PINN、没有生成实验结果，也没有修改项目阶段文件。因而本报告是**对既有产物的静态与有限执行证据审查**，不是研究验证报告。

### 2.2 证据等级

- `VERIFIED`：可由仓库文件、结构化数据或本次重跑直接确认。
- `SUPPORTED_INTERPRETATION`：由多项已核实证据支持，但仍包含专业判断。
- `HYPOTHESIS`：候选提出、尚待实验检验的机制或性能判断。
- `UNKNOWN`：现有产物不足以判断。

### 2.3 关键限制

- 文献审查以已有 Phase 0/3 检索产物为边界；未把“无命中”当成“不存在”。
- coherence 脚本验证的是小型代数/数值例，不验证 VO₂ 物理正确性或训练收益。
- 没有可执行 FEniCSx 基准、训练代码或数据，因此无法审查数值收敛、泄漏、性能、稳定性或复现性。
- 当前用户指令允许本次审查与报告；项目状态文件仍记录旧的治理阶段，详见第 9 节。

## 3. 产物盘点与规范路径

### 3.1 总体盘点

`VERIFIED`：

- 运行目录共有 **121 个文件**，约 **10.4 MB**。
- 共有 **71 个 JSON**，均可严格解析。
- Phase 0 原始相关性分区为 **151** 条：32 core、41 adjacent、78 off-topic。
- 最终文献池为 **75** 条：34 core、41 adjacent；无重复 paper ID 或精确题名。
- 全文层选入 21 条，只有 9 条取得方法级文本，12 条退化为摘要且 `method_chars=0`。
- 最终 Phase 3 原始碰撞池 485 条，审计池 229 条。
- 两次被否决候选均完整归档；第三轮候选进入 Phase 4。
- Phase 4 没有未填普通 TODO；implementability 文件诚实保留 7 个 `open` 作者决策。
- 三张 Markdown 卡和两张 TeX 卡存在；本机无 XeLaTeX/Tectonic，未生成 PDF，也没有 PDF 视觉 QA。

### 3.2 候选演化

```mermaid
flowchart LR
    P0["Phase 0<br/>75-paper grounded pool"] --> P1["Phase 1<br/>high-frequency multiphysics bottleneck"]
    P1 --> A1["Attempt 1<br/>Impact-Partitioned Local-Operator"]
    A1 -->|"mixed-coordinate bound fails"| X1["Abandon"]
    X1 --> A2["Attempt 2<br/>Solver-Floor Continuation"]
    A2 -->|"generic curriculum / recipe bypass"| X2["Abandon"]
    X2 --> A3["Attempt 3<br/>Kinetics-Clock PINN"]
    A3 --> C["Coherence patch<br/>analytic monotone clock"]
    C --> P3["Phase 3<br/>Advance, soft judgment"]
    P3 --> P4["Phase 4<br/>proposal cards"]
```

这条演化链的主要价值是：每轮失败都产生了新约束，而不是简单重复生成。Attempt 1 暴露 gate-coordinate 与 response-coordinate 混用；Attempt 2 暴露固定目标连续化缺乏真正新机制；最终方案转向 C12 表示/算子替换。

### 3.3 当前规范候选与歧义

当前应以 [refined_candidate.json](../ideaspark_run/high-frequency-pinn-pcm/phase2_coherence/refined_candidate.json) 为 Phase 2 规范候选，再结合 [phase3_critique_output.json](../ideaspark_run/high-frequency-pinn-pcm/phase3_critique/phase3_critique_output.json) 和 [phase4_expansion.json](../ideaspark_run/high-frequency-pinn-pcm/phase4/phase4_expansion.json) 阅读。

但是 [phase2_generate_output.json](../ideaspark_run/high-frequency-pinn-pcm/phase2_generate/phase2_generate_output.json) 仍保留已被 coherence 反例推翻的有限求积时钟表述。若人工只读取该文件，会恢复错误机制。运行目录缺少一个顶层 canonical manifest 来声明：

- 当前规范候选文件；
- 每阶段实际输入及 SHA-256；
- Skill 和生成器版本；
- 被废弃/被修补的前身；
- 最新验证状态与时间。

因此当前是“导航器知道规范路径”，不是“产物自身可独立判定规范路径”。

## 4. 当前候选的技术内容

### 4.1 核心机制

候选拟在二维 VO₂ 电—焦耳热—相态 PINN 中，用空间局部、严格单调的动力学时钟替代解网络的原始时间输入槽：

$$
\tau_\psi(x,t)
=k_{\mathrm{floor}}t
+\sum_{j=1}^{J}\operatorname{softplus}(a_{\psi,j}(x))B_j(t),
$$

其中 `B_j(t)` 是高斯正率基函数的解析累积，`k_ref>0`，`k_floor>0`，因而按构造有 `partial_t tau>0`。解头写成

$$
(T,E,\xi,\ldots)=h_\theta(x,\tau_\psi(x,t),p(t)),
$$

并通过完整一阶/二阶时空链式法则把原始电—热—相态 PDE 残差拉回物理坐标。时钟残差为

$$
r_\tau
=\partial_t\tau
-\sqrt{K_\xi(T,E,\xi,\nabla\xi,\Delta\xi)^2+k_{\mathrm{floor}}^2}.
$$

预期作用是：在相变动力学快的区域增加时钟速度，使前沿在 `tau` 坐标中变宽，同时保持原始物理目标不变。

### 4.2 已设计的关键对照

`VERIFIED`：候选已提出以下必要对照：

- 原始时间 PINN；
- 恒等时钟 `tau=t`，并关闭 `r_tau`；
- 同架构解析坐标变换，但移除 `k_eff` 与 `r_tau` 的动力学时钟耦合，同时保留完整 pullback 和含 `K_xi` 的原相态 PDE；
- 加宽的原始时间网络；
- 高频/谱特征、因果/时间推进、采样或坐标类强基线；
- 同预算、同参数量或显式报告活动/冻结参数量；
- 在方法锁定后才进行整实体 OOD 评估。

这些对照使“只是多参数”“只是一般坐标变换”“只是训练预算更大”等替代解释原则上可被隔离，是最终候选最强的部分之一。

## 5. 已确认的优点

### 5.1 负面证据被保留

`VERIFIED`：Attempt 1 和 Attempt 2 的候选、碰撞结果、coherence 证据与 abandon 审查均未被覆盖。尤其 Attempt 1 的合法反例表明书面 Taylor 界错误，随后路线被放弃，而不是通过措辞弱化继续包装。

### 5.2 单调时钟的数值实现错误被真实发现并修复

`VERIFIED`：现有 coherence 脚本复跑得到：

- 对正 integrand 使用独立缩放的 16 点 Gauss 求积时，数值时钟仍可局部下降；实测有限差分斜率为 `-984.389906`。
- 改为解析 Gaussian/erf 累积后，最小解析/网格斜率为 `0.001`。
- 二阶时间 pullback 最大误差约 `3.903e-08`。
- 二维空间 Hessian pullback 最大误差约 `9.337e-09`。
- 计算图为 DAG。
- 脉冲跳变探针、恒等分支参数计数和同预算 naive 坐标比较均有执行输出。

这支持“当前解析时钟与局部 pullback 在小型例子上代数一致”，但不支持“训练更快”或“VO₂ 预测更准”。

### 5.3 主张边界总体克制

`VERIFIED`：卡片没有伪造训练结果或实验验证；把主要收益写成可证伪预测，并保留 synthetic solver 与真实实验之间的界限。Phase 3 也承认“学习自适应坐标改善尖锐解”的宽泛主张已被既有工作占据，候选只能主张更窄的 `K_xi` 驱动局部时间表示。

### 5.4 流程结构检查通过

本次重跑 IdeaSpark 验证器得到：

| 检查 | 结果 |
|---|---:|
| kill-switch integrity | pass |
| sub-pattern citation consistency | pass |
| alias collateral coverage | pass |
| expansion completeness | pass |
| implementability completeness | pass |
| implementability readability | pass |
| user direction | pass |

必须强调：这些检查只证明指定字段、引用关系和结构约束满足 Skill 合同，不证明数学主张正确、模型可运行、文献完整或方法有效。

## 6. 阻断性科学问题

### F-01 — formal OOD 目标与模型数据流矛盾

- 严重度：**BLOCKER**
- 状态：`VERIFIED`
- 证据：[phase4_expansion.json](../ideaspark_run/high-frequency-pinn-pcm/phase4/phase4_expansion.json)、[method_view.json](../ideaspark_run/high-frequency-pinn-pcm/phase4/method_view.json)

S10 要求在锁定方法和检查点后，对完整未见几何、材料刚度或脉冲谱进行评估且不更新参数。但当前时钟网络只读 `x`，解头只读 `(x,tau,p(t))`；没有几何描述、材料参数、域编码或跨域映射。一个在几何 A 上训练的坐标 `x` 并不自动定义几何 B 上的函数，更不能把未见材料常数隐式传给冻结网络。

必须二选一：

1. **参数化跨器件代理。** 给模型增加明确的几何、材料、边界/协议条件与域表示；训练按完整器件分组，formal OOD 才是冻结模型的零样本泛化。
2. **逐案例 PINN 求解器。** 对每个新器件重新训练，但锁定算法、超参数选择规则和预算；这评估的是算法/求解器稳健性，不应称为冻结检查点的实体级零样本 OOD。

当前文本混合两种任务定义，formal OOD 合同不可执行。此问题必须在架构、数据拆分和论文主张之前解决。

### F-02 — 条件斜率公式遗漏脉冲路径

- 严重度：**BLOCKER**
- 状态：`VERIFIED`
- 证据：[phase4_expansion.json](../ideaspark_run/high-frequency-pinn-pcm/phase4/phase4_expansion.json)、[idea.detail.en.md](../ideaspark_run/high-frequency-pinn-pcm/phase4/idea.detail.en.md)

候选已明确采用

$$
\partial_t f=f_\tau\,\partial_t\tau+f_p\cdot\dot p.
$$

因此当相态 PDE 为 `partial_t xi=K_xi` 且 `r_tau=0` 时，一般应有

$$
\xi_\tau
=\frac{K_\xi-\xi_p\cdot\dot p}
{\sqrt{K_\xi^2+k_{\mathrm{floor}}^2}},
$$

而不是当前主张的

$$
|\xi_\tau|
=\frac{|K_\xi|}{\sqrt{K_\xi^2+k_{\mathrm{floor}}^2}}<1.
$$

后一个等式只有在 `p_dot=0`、`xi_p=0` 或存在另一条等价约束时成立。候选又允许光滑脉冲段并显式使用 `p_dot/p_ddot`，所以不能默认忽略该项。

可接受修复只有三类：

- 将协议限定为分段常值，明确不等式只在脉冲间开区间成立，并单独处理跳变界面；
- 从相态解头去掉 `p(t)` 的显式路径，让协议只通过物理场/边界条件进入；
- 保留显式协议输入，但改写核心公式、机制解释和证伪指标。

这会改变核心 claim 或模型数据流。修复后应重新执行 coherence、Phase 3 审查和完整 Phase 4 生成，不能只手改卡片。

### F-03 — 被引用的 FEniCSx 物理基准并不存在于仓库

- 严重度：**BLOCKER FOR EXECUTION**
- 状态：`VERIFIED`

产物多次引用“已命名的 FEniCSx oracle/model”，但仓库中没有对应求解器、网格、参数表、边界条件、配置、依赖锁、轨迹、收敛研究或数据清单。除 `.agents/`、`ideaspark_run/` 与虚拟环境外，也未发现可执行科学模型文件。

因此当前“oracle”只是拟议资源，不是现有可复现实物。正式实施前至少需要：

- 权威模型快照与唯一版本标识；
- 方程、本构、初边值条件、单位与无量纲化；
- 几何、网格和时间步定义；
- 材料参数来源、适用温区和不确定性；
- 网格/时间收敛、能量/电荷闭合和失败判据；
- 数据生成清单、实体级 ID 与 split manifest。

### F-04 — VO₂ 电—热—相态物理闭合尚未冻结

- 严重度：**HIGH**
- 状态：`UNKNOWN`

当前文本以 `sigma`、`kappa`、`rho c` 和 `K_xi(T,E,xi,grad xi,Delta xi)` 等符号描述系统，但没有确定具体 VO₂ 模型。至少以下选择仍会改变研究结论：

- 电输运采用欧姆、Poole–Frenkel、场致或混合机制；
- 相变采用哪种自由能、动力学、滞回和成核规则；
- 潜热/焓、弹性或结构自由度是否进入热/相态闭合；
- 电极接触、串联电路、电容/电感和器件寄生是否进入“高频”问题；
- 材料界面、热边界、电流边界与相态边界条件；
- 光滑脉冲和阶跃脉冲下状态连续性、通量连续性与界面条件。

在这些条件未冻结前，无法判断 `K_xi` 时钟是否跟随真正的主导刚性，也无法构造可信 FEniCSx oracle。

### F-05 — 时钟可能只把刚性从时间方向转移到空间方向

- 严重度：**HIGH**
- 状态：`SUPPORTED_INTERPRETATION`

当 `tau= tau(x,t)` 随空间变化时，完整 pullback 会引入 `grad tau`、`D^2 tau` 以及与解头 `tau` 导数的交叉项。即使时间方向的相态斜率在某些条件下被归一化，空间残差、残差 Jacobian 或优化几何仍可能更差。

因此只报告 switching time、前沿拓扑和编程能量误差，不能证明“抗高频”来自时钟机制。最小机制诊断还应包括：

- `tau` 动态范围、`min/max partial_t tau`；
- `norm(grad tau)` 与 `norm(D^2 tau)`；
- 原/变换坐标下解与残差的频谱；
- 各 PDE 残差梯度范数与梯度冲突；
- 残差 Jacobian、经验 NTK 或可负担的条件性代理；
- 同预算下收敛速度、失败率和内存/时间开销。

若候选只改善 `|xi_tau|`，却放大空间交叉项或总体条件数，则核心解释被证伪。

## 7. 文献与新颖性审查

### 7.1 已有文献基础

`VERIFIED`：最终 75 条记录来自 40 条 OpenAlex、20 条 arXiv 和 15 条 Semantic Scholar；51 条带 DOI，7 条缺 venue，23 条以 arXiv 为 venue，39 条引用数为零或空。时间只覆盖 2024–2026，其中 40 条来自 2026。

最近邻中的以下事实有本地文本支持：

- NeuSA：高频/因果表征与带限初态等假设；
- adaptive spectral PINN：在 stiff ODE 上的门控和谱表示；
- 静态 phase-field PINN：通过静态化规避动态相场；
- VO₂ 多物理论文：Poole–Frenkel、电热机械耦合和动态拓扑的物理动机。

这些材料足以支持“动态多场相变前沿对 PINN 构成困难”这一研究动机，但不足以闭合最终坐标机制的新颖性。

### 7.2 新颖性未闭合

- 严重度：**HIGH**
- 状态：`SUPPORTED_INTERPRETATION`

候选生成后，真正最近的技术家族已从“高频/因果 PINN”转为“学习坐标、移动网格、内禀时间与反应进度”。最终卡片仍把 NeuSA 称为最近架构先例，这不准确：NeuSA 是重要的高频—因果基线，但不是最终表示替换的总体最近邻。

已有碰撞池至少暴露以下更近的方法家族/条目：

- `openalex:W4403443387`：R-adaptive DeepONet；
- `semanticscholar:10e53930fef24588789b135a8031237e1231ed61`：PAS-Net，arXiv:2511.14925；
- `arxiv:2605.06203v1`：Adaptive Coordinate Transforms for Neural Operators；
- `arxiv:2508.19561v1`：EEMS-PINN；
- `semanticscholar:509282c42d55d4041f034bc4d8f9ef9a58496c0f`：coordinate-transformed PINN fine-tuning，DOI 10.1016/j.compfluid.2025.106957。

此外，Phase 0 完全没有 2024 年以前文献，Phase 3 只回溯到 2022；而 material time、intrinsic time、reaction-progress coordinate、time equidistribution 和 moving mesh 的机制祖先可能更早。现有专属查询对这些词的命中大多是跨领域噪声，不能用“未检索到 exact hit”支持首次性。

建议把相关工作重构为三条轴：

1. 高频与因果 PINN：NeuSA、adaptive spectral/causal 方法；
2. 学习或解析坐标：R-adaptive DeepONet、PAS-Net、adaptive coordinate transform、coordinate-transformed PINN；
3. 移动网格与采样：EEMS-PINN 等。

KC-PINN 的可守窄差异只能是：**空间局部、严格单调、由相态动力学速率约束的时间坐标，并对原电—热—相态 PDE 做完整 pullback**。在 targeted scoop check 完成前，该差异仍是 retrieval-bounded hypothesis，不得写“首次”。

### 7.3 六项承重 host reference 未解析

`VERIFIED`：[host_refs_unresolved.md](../ideaspark_run/high-frequency-pinn-pcm/phase0/host_refs_unresolved.md) 保留以下未被验证并纳入语料的候选：

| ID 提示 | 预期承重方向 | 当前状态 |
|---|---|---|
| 10.1016/j.neunet.2025.108247 | Fourier/high-frequency PINN | UNKNOWN |
| arXiv:2508.00628 | 空间自适应 Fourier 特征 | UNKNOWN |
| 10.1016/j.neunet.2024.106886 | Fourier-feature/频谱偏置 | UNKNOWN |
| 10.1016/j.cma.2021.113938 | 基础方法/数值机制 | UNKNOWN |
| 10.1016/j.nxmate.2026.102138 | PCM thermal memory | UNKNOWN |
| 10.1016/j.sse.2022.108542 | electrothermal phase-field PCM solver | UNKNOWN |

无论这些条目最终被证实、纠正或判为不存在，都必须逐条留下解析结果。它们正好位于强基线与目标物理两侧，未解析时不能称文献调研全面。

### 7.4 全文覆盖被顶层布尔值掩盖

`VERIFIED`：21 个全文目标只有 9 个取得方法文本，12 个明确失败并退化为摘要；anchor NeuSA 取得约 11,916 个 method chars，因此 anchor 足够，但总体全文覆盖明显退化。[phase1_output.json](../ideaspark_run/high-frequency-pinn-pcm/phase1/phase1_output.json) 仍写 `fulltext_degraded=false`，容易被误解为整个语料全文正常。

建议拆成结构化字段：

- `anchor_fulltext_sufficient=true`；
- `corpus_fulltext_degraded=true`；
- `selected=21`、`method_level_success=9`、`abstract_only=12`；
- 每条来源、失败原因与最后核验时间。

### 7.5 “高频”概念混用

`SUPPORTED_INTERPRETATION`：现有 core/adjacent 分区混合了三类不同现象：网络的高频表示、器件的运行频率、材料的超快事件时间尺度。GHz/kHz 电路频率、ps 相变时长和解谱高频并不等价。

建议后续语料采用至少六类标签：

- `HF_representation`
- `stiff_fast_transient`
- `device_operating_frequency`
- `target_phase_physics`
- `multiphysics_solver`
- `off_topic`

只有前两类能直接支撑“抗高频 PINN”的方法学瓶颈。

### 7.6 材料范围需收窄

最终候选已从泛“相变材料/器件”收窄为 VO₂。VO₂ Mott/结构相变与 GST、GeTe 等硫系相变存储并非同一物理体系。当前 VO₂ 支撑主要来自一项特定器件预印本和若干通用 PCM/相场论文，不能把 VO₂ 结论外推为所有 PCM。

论文应明确：VO₂ 是首个研究实例；若要主张“面向 PCM”，需要跨材料族实验或至少给出适用条件与失效边界。

## 8. 实施、预算与证伪设计审查

### 8.1 预算是紧约束，不是普通可行

候选预算为 `9.5 80GB-class GPU-days`，Phase 1 包络为最多 10 GPU-days，即使用率约 95%。但 Phase 4 的预算解析器没有识别中间的 `80GB-class`，只解析了“零付费 API”，因此 compute 分项被错误标为 `feasible`；按其自身阈值应为 `tight`。

同时，方案列出十余类基线、三随机种子、FEniCSx 数据生成、二阶时间和空间 Hessian pullback，以及 OOD 评估。全部塞入 9.5 GPU-days 风险很高。

建议采用分级 MVE：

1. 首轮只运行 raw-time、identity、naive analytic/no-`r_tau`、KC-PINN、一个最强高频/因果基线；
2. 先看机制诊断与三个下游指标是否出现一致信号；
3. 若无信号立即停止，不扩展完整基线矩阵；
4. 只有通过首轮门槛后再增加坐标/采样/谱基线与三种子确认；
5. formal OOD 只能在方法完全锁定后执行。

### 8.2 证伪结构总体合理，但需在修复后重写

`SUPPORTED_INTERPRETATION`：当前证伪计划包含最小比较、明确下游指标、单一负控和 matched-budget 设计，结构优于一般“看 loss 是否下降”。然而 F-01 与 F-02 会改变任务与主张，修复后必须重新定义：

- 负控究竟移除哪一个承重变量；
- 预测回归到哪个 baseline；
- OOD 是冻结代理还是锁定算法后重训；
- 事件时序、拓扑、能量和场误差的操作定义；
- 成功/失败方向与停止条件。

### 8.3 FEniCSx oracle 不是独立真值

即使补齐代码，FEniCSx 仍是同一物理模型下的数值 oracle，不是实验真值。至少需要网格/时间收敛、守恒检查和独立实现或独立离散交叉核验。论文必须使用“合成数值基准”措辞，不能表述为器件实验验证。

## 9. 流程、渲染、复现与治理审查

### 9.1 最终卡片遗漏承重内容

- 严重度：**HIGH**
- 状态：`VERIFIED`

[phase4_expansion.json](../ideaspark_run/high-frequency-pinn-pcm/phase4/phase4_expansion.json) 包含 `core_claim`、`sub_claims`、`falsification_prediction`、`compute_budget`、五项 `feasibility_validation`、`differentiation_from_lit` 和 `literature_breakdown`，但三张 Markdown 卡没有呈现其中大部分内容；Reviewer 卡基本只保留 Motivation、Method 和 Reviewer concerns。

这意味着“Phase 4 expansion 完整”没有转化成“用户可见卡片完整”。Reviewer 卡至少应包含：主张边界、完整证伪预测、预算/可行性、新颖性差异、检索限制、标准参考文献和 `PROPOSED_NOT_AUTHORIZED` 状态。

### 9.2 卡片数学格式和自动摘要损坏

- 严重度：**HIGH FOR DELIVERY**
- 状态：`VERIFIED`

[idea.std.en.md](../ideaspark_run/high-frequency-pinn-pcm/phase4/idea.std.en.md)、[idea.std.zh.md](../ideaspark_run/high-frequency-pinn-pcm/phase4/idea.std.zh.md) 和 TeX 文件存在：

- 行内数学定界符与 Markdown 代码定界符发生交叉嵌套；
- `\(a\dots\)`、`\(existing\dots\)` 一类被截断的步骤引用；
- `M0_background`、`M1_analytic_clock` 等内部模块 ID 泄漏到正文；
- 无 PDF 输出，因而未做视觉 QA。

现有 readability validator 和 Markdown lint 均未捕获这些问题。三张卡当前不宜视为论文级或评审级交付物。

### 9.3 Phase 4 缺少依赖新鲜度检查

- 严重度：**MEDIUM**
- 状态：`VERIFIED`

文件时间显示 `derive_map.json` 与 `phase4_implementability.json` 早于最后一次 `fill_map.json` 修订；之后 expansion 与 method view 被重建。人工语义复核认为当前文本基本一致，但没有输入哈希证明 derive 和 implementability 审查的是当前版本。

导航器只依据文件存在性报告 `DONE`，也不检查卡片是否晚于 expansion/implementability。故 `7 pass` 不能证明派生产物新鲜。

建议所有派生产物记录：

- `input_sha256`；
- Skill 本地树哈希与上游固定版本；
- 生成器/模型身份；
- UTC 和本地生成时间；
- 依赖文件列表；
- validator 版本与结果。

上游任何变化都应使 derive、method view、implementability 和 cards 失效并强制重建。

### 9.4 缺少运行清单和持久验证报告

运行目录没有统一的 `run_manifest.json` 或 `validation_report.json`；没有持久记录命令、环境、连接器版本、检索 `as_of`、模型/agent 身份、输入/输出哈希和验证器输出。`.agents/` 与 `ideaspark_run/` 当前也未形成 Git 中可引用的不可变身份。

这不会否定 idea，但阻止他人证明“哪一版输入生成了哪一版结论”。

### 9.5 引用不可独立追溯

最终卡片只使用裸 arXiv/OpenAlex/Semantic Scholar ID，没有标准参考文献表、链接、DOI、证据层级或全文状态。文件一旦脱离运行目录，引用便不可读。`lit_table.md` 还存在编码乱码，75 个 `resolves_problem` 单元全部为空。

建议生成 canonical bibliography：优先 DOI/arXiv ID，保留 OpenAlex/S2 作为检索 provenance，并标注 abstract/method/full-text 证据层级。

### 9.6 治理状态与实际运行记录冲突

- 严重度：**HIGH PROCESS RISK**
- 状态：`VERIFIED`

用户已明确授权本次文献调研、idea 筛选和审查，并说明最新任务指令优先于 `active_phase.md` 的旧记录。因此本次运行不是“未经用户授权”。

但以下文件仍记录相反的旧状态：

- `active_phase.md`：`PRE_RESEARCH_INITIALIZED / GOVERNANCE_ONLY`；
- `PROJECT_STATE.md`：当前只有治理产物，idea 筛选尚未开始；
- `NEXT_ACTIONS.md`：等待 Phase 0 授权，不开展检索；
- `docs/governance/EXTERNAL_SKILLS.md`：未调用论文数据库、未生成 idea。

实际目录已经有 121 个研究工作流文件。这是**状态记录失真**，不是对用户授权的否定。后续若继续依赖这些文件自动路由，可能再次发生错误暂停或错误宣称“尚未开始”。

本报告不擅自修改阶段文件。建议另行更新为：已授权并完成一次 IdeaSpark 文献筛选与候选生成；候选仍为 `PROPOSED_NOT_AUTHORIZED`；尚未授权求解、训练、长时间计算或论文科学主张。

### 9.7 低优先级状态噪声

- `phase0/.pattern_summary_pending` 在 `lit_table.md` 完成后仍存在；
- `.retry_used` 不能独立表达两次 abandon 和第三候选 advance；
- `DONE` 只表示三张 Markdown 文件存在，不表示新鲜、科学有效、作者决策已关闭或 PDF QA 完成。

建议使用更精确终态，例如 `CARDS_RENDERED_WITH_OPEN_SCIENTIFIC_BLOCKERS`。

## 10. 主张—证据矩阵

| 主张 | 当前状态 | 现有证据 | 尚缺什么 |
|---|---|---|---|
| 解析 Gaussian/erf 时钟严格单调 | VERIFIED（给定正率构造） | 解析结构与小型数值探针 | 实现级 AD/精度测试、极端尺度稳定性 |
| 一/二阶时空 pullback 公式可实现 | SUPPORTED_INTERPRETATION | 小型时间二阶与二维 Hessian 对照 | 完整多场残差、边界/界面和批处理测试 |
| `|xi_tau|<1` | 当前不成立为一般陈述 | 无脉冲显式项时的条件推导 | 解决 F-02 并重审 claim |
| 时钟改善高频/刚性 PINN 训练 | HYPOTHESIS | 机制直觉、naive toy | 同预算强基线、机制诊断、种子统计 |
| 时钟不会把刚性转移到空间项 | UNKNOWN | 无 | `grad tau`、`D²tau`、Jacobian/NTK/梯度诊断 |
| 提升 switching time、拓扑和能量精度 | HYPOTHESIS | 证伪计划 | 冻结 oracle、数据、训练结果 |
| 对未见几何/材料 formal OOD 有效 | 当前任务定义不可执行 | 无 | 选择参数化代理或逐案例求解器 |
| 方法对 VO₂ 物理有效 | UNKNOWN | 文献动机 | 冻结、来源明确、收敛验证的 VO₂ 模型 |
| 方法具有可发表的新颖性 | UNKNOWN / retrieval-bounded | 近期碰撞审查 | 历史机制检索、六项 unresolved、全文 prior matrix |
| 可在 9.5 GPU-days 内完成全部计划 | UNKNOWN，预算 tight | 文本预算 | 分级 MVE、实测吞吐和停止门 |
| 达到中科院二区论文定位 | UNKNOWN | 无实验或论文证据 | 完整科学闭环；不构成接收承诺 |

## 11. 实施前必须通过的门槛

### G0 — 规范化与状态对齐

- 建立 canonical manifest，明确 `refined_candidate.json` 为当前 Phase 2 规范候选；
- 标记有限求积版本为 superseded，不删除负面证据；
- 写入运行/验证 manifest 与输入哈希；
- 在单独授权下更新阶段状态，保留“未授权训练/实验”。

**通过条件：** 任意读者无需依赖聊天记录即可确定规范路径、版本、授权边界和未决项。

### G1 — 修复两个机制级阻塞

- 决定脉冲输入语义并修正 F-02；
- 决定 formal OOD 是参数化冻结代理还是逐案例重训求解器；
- 按变化重新运行 coherence、Phase 3 和完整 Phase 4，而不是局部改文案。

**停止条件：** 若修复后核心斜率归一化不再成立，或 OOD 任务要求改变研究主体且无合理表示，则退回瓶颈重诊断。

### G2 — 新颖性硬门

- 解析六项 unresolved host refs；
- 围绕 adaptive temporal coordinate、intrinsic/material time、reaction-progress coordinate、time equidistribution、moving-time mesh、VO₂/PCM multiphysics PINN 做定向检索；
- 对 R-adaptive DeepONet、PAS-Net、ACT、EEMS-PINN 和 coordinate-transform PINN 建方法级 prior matrix；
- 把 NeuSA 正确定位为高频—因果强基线，而非总体最近架构先例；
- 生成标准参考文献并升级承重威胁到全文证据。

**停止条件：** 若发现既有工作已实现同一局部动力学时钟、完整 PDE pullback 和同等目标物理，且无可守差异，则停止该 novelty claim 或放弃路线。

### G3 — 冻结物理与数据合同

- 选择并引用 VO₂ 电—热—相态模型；
- 冻结方程、本构、单位、无量纲化、几何、初边值和接口条件；
- 明确 `K_xi`、潜热/焓、电路与接触模型；
- 建立 FEniCSx 实现、收敛检查、守恒检查和数据 manifest；
- 明确整实体 split 与泄漏防护。

**停止条件：** oracle 未收敛、守恒不闭合、不同离散不一致，或目标事件在冻结模型中不存在。

### G4 — 低成本代数与实现 MVE

- 对解析时钟、正率、极端尺度和可逆性做自动测试；
- 对完整一/二阶时空 pullback 做制造解或高精度差分检查；
- 验证脉冲边界、材料界面、恒等分支和参数公平性；
- 记录 `tau` 导数、残差和计算图的数值稳定性。

**通过条件：** 所有原始 PDE 残差在变换前后对制造解一致，且无隐藏的有限求积或断点错误。

### G5 — 有界比较 MVE

首轮只比较：

1. raw-time PINN；
2. identity clock；
3. naive analytic transform，无 `k_eff/r_tau`；
4. KC-PINN；
5. 一个最强高频/因果或坐标基线。

报告物理时间下的 switching time、前沿拓扑、能量闭合、场误差，以及第 6.5 节的机制诊断；统一预算并记录活动/冻结参数。

**停止条件：**

- KC-PINN 在多个案例上不优于最强统一基线；
- 负控没有把下游指标拉回基线，说明机制归因不成立；
- 时间方向改善被空间交叉项、条件性或计算成本抵消；
- 首轮预算消耗后仍无稳定信号；
- 结果只在泄漏拆分或单一器件上成立。

formal OOD 仅在 G5 内部方法、指标和超参数选择完全锁定后执行。

## 12. Phase 4 尚未关闭的作者决策

[phase4_implementability.json](../ideaspark_run/high-frequency-pinn-pcm/phase4/phase4_implementability.json) 保留 7 个 `open` 项，主要聚合为：

- 权威 FEniCSx 模型快照、组成方程/边界合同及其来源；
- `k_ref` 和无量纲尺度的实际取值规则；
- 解头架构与匹配参数量的具体再分配；
- 优化器及训练控制值；
- switching、topology、energy-balance、场误差和残差指标的操作定义与阈值。

这些不是文案空缺，而是会改变实现或证据含义的作者决策。应在执行配置中预声明，不应由代码运行时临时选择。

## 13. 最终评级

| 维度 | 评级 | 结论 |
|---|---|---|
| 问题重要性 | 中高 | 动态多场相变前沿与 PINN 高频/刚性困难有研究价值 |
| idea 区分度 | 中 | `K_xi` 驱动局部时间时钟是可守窄差异，但历史近邻未闭合 |
| 内部程序一致性 | 中 | 解析时钟/pullback 有正面证据，但脉冲项公式仍有阻塞 |
| 物理可信度 | 低至中 | 目标物理尚未冻结，FEniCSx oracle 不存在于仓库 |
| 证伪性 | 中高 | 对照结构较好，需在任务/公式修复后重写 |
| 复现性 | 低 | 无实现、数据、manifest、输入哈希或持久验证报告 |
| 文献完整性 | 中低 | 足以支撑 ideation，不足以闭合 novelty |
| 交付质量 | 低 | 卡片内容遗漏且格式损坏，无 PDF QA |
| 当前实施准备度 | **不通过** | 必须先通过 G0–G3，随后才做低成本 G4/G5 |

## 14. 最短合理下一步

当前最有价值的下一步不是启动训练，而是形成一个**机制与任务修订包**，只包含三项：

1. 一页决策：选择脉冲语义，并给出修正后的 `xi_tau` 公式与 claim；
2. 一页决策：选择参数化跨器件代理或逐案例 PINN 求解器，重写 formal OOD；
3. 一份证据表：冻结 VO₂/FEniCSx 物理合同，并完成坐标/内禀时间/反应进度近邻的 targeted scoop check。

三项完成后，重新执行 IdeaSpark coherence → Phase 3 → Phase 4，修复 renderer 并生成带标准引用、证伪、预算和状态边界的卡片。只有新一轮审查不再出现机制级阻塞，才进入有界实现 MVE。

## 15. 审查结论

`SUPPORTED_INTERPRETATION`：IdeaSpark 本轮最有价值的产物不是“已经成熟的抗高频 PINN”，而是一个经过两次失败学习后形成、边界较窄且可以被真正证伪的 Kinetics-Clock PINN 假说。它值得保留和修订。

`VERIFIED`：当前结构验证通过，但存在 OOD 数据流矛盾、脉冲项公式缺口、物理基准缺失、文献新颖性未闭合、预算解析错误、派生新鲜度不可证和卡片交付损坏。

`HYPOTHESIS`：局部动力学时钟能够缓解 VO₂ 高频相变前沿的 PINN 训练困难。

`UNKNOWN`：该机制是否优于强谱/因果/坐标基线、是否在空间项中转移刚性、是否有可发表的新颖性、是否满足 formal OOD，以及是否能在预算内形成中科院二区定位的证据闭环。

**最终处置：保留 idea；修订后复审；当前不授权实施、训练或科学正面主张。**
