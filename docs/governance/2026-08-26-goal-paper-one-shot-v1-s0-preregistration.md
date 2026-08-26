# GOAL-PAPER-ONE-SHOT-V1 S0 预注册与冻结记录

- `contract_id`: `GOAL_PAPER_ONE_SHOT_V1_S0_V1`
- `frozen_at`: `2026-08-26T16:46:25+08:00`
- `lifecycle_state`: `FROZEN_BEFORE_FIRST_NEW_SOURCE_AUDIT_OR_SOLVE`
- `claim_status`: `PREREGISTRATION_ONLY_NO_NEW_SCIENTIFIC_EVIDENCE`
- `machine_contract`: [`configs/goal_paper_one_shot_v1/s0_contract.json`](../../configs/goal_paper_one_shot_v1/s0_contract.json)
- `live_plan`: [`GOAL-PAPER-ONE-SHOT-V1`](../plans/NEXT_ACTIONS.md)

本记录只冻结执行合同，不是来源 PASS、对象锁定、数值结果或科学证据。机器可读 JSON 是参数、案例、方法、预算和停止规则的逐字段执行入口；本页说明其研究身份与关键理由。

## 1. 路线顺序

1. `KNOWN_UNREVIEWED_S9_REFRESHED_TO_COMSOL_6_4 / Application 141181`；
2. `PCMO_REACTION_DRIFT_S6_SOURCE_ONLY_V1`；
3. `SYN_EDT_2D_V1`。

Route 1 目前只是 6.3 官方 tutorial 的既有 Pass-1 线索；本地未发现 `.mph`、机器可读输出或标准路径 COMSOL 安装，因此当前是 `MODEL_FILE_ACCESS_UNKNOWN`，不是预先宣告 access failure。S1 必须独立裁决精确 6.4 build、合法研究访问、结果发表权、模型树、domain 5 初态、EC/HT/TCC/Joule、IC/BC/interface、表格/单位、稳定化、端口符号与 reference outputs。

Route 2 在新审查前方法盲冻结为 Saraswat 等人的 PCMO reaction–drift 线索（DOI `10.1109/TED.2020.3011387`，arXiv `2005.07398v1`）。它在既有本地报告中明确包含 drift–diffusion、自热和 reaction–drift，且有可达作者稿，因此高于现有 ceria 线索；但二维器件闭环、开放代码身份和完整合同尚未闭合，身份严格为 `DISCOVERY_ONLY / NOT_SOURCE_PASS`。

HFO-NP-v1、TaOₓ C1、Package A 三家族、R1/TAPF/ETPF/EAF 均不进入 fallback；其冻结终点原样保留。

## 2. SYN_EDT_2D_V1 物理合同

Route 3 是全新、透明、二维轴对称 synthetic mixed-conductor benchmark，不继承任何冻结对象的材料身份、参数或 PASS。活动域为半径 80 nm、厚度 30 nm 的混合导体，配 15 nm 底电极与半径 25 nm 的居中顶接触。

场方程为：

\[
\nabla\!\cdot\mathbf J_e=0,
\qquad
\mathbf J_e=-\sigma(y,T)\nabla\phi,
\]

\[
\partial_t y+\nabla\!\cdot\mathbf j_y=0,
\qquad
\mathbf j_y=-D(T)\left[\nabla y+\frac{e}{k_BT}y(1-y)\nabla\phi\right],
\]

\[
-\nabla\!\cdot(k\nabla T)=\sigma(y,T)|\nabla\phi|^2.
\]

这里 (y\in[0,1]) 是守恒 lattice-gas defect fraction；热场采用准稳态 Joule source，不建立独立热时钟。(D(T)) 与 \(\sigma(y,T)\) 的全部系数、几何、边界和两周期绝对波形都是 `ENGINEERING` synthetic choices，不是材料本征常数或实验拟合。

初态为 (y=0.50,T=300\,\mathrm K)。顶接触施加固定时长 bipolar waveform：每个 1 s 周期先正 reset、再固定 (-0.15\,\mathrm V) set；两周期连续携带状态。方法轴只缩放正 reset 幅值，nominal 为 (0.18\,\mathrm V)，

\[
\lambda_R=1+0.20\delta.
\]

零驱动 Q0、非投票 QL/QH 与唯一 event-voting QN 的幅值在 JSON 中冻结。第一次数值求解后不得改参数、波形、阈值、分支或事件 ROI；任何硬门失败都关闭 `SYN_EDT_2D_V1_V1`，不救援。

## 3. 事件、守卫和收敛

事件场使用

\[
d_k(x,t)=\frac{y_{\mathrm{pre},k}(x)-y(x,t)}{0.50}.
\]

投票 ROI 为顶接触下 (r\le25\,\mathrm{nm},24\le z\le30\,\mathrm{nm})。两个周期必须同时满足局部耗尽幅度、恢复、邻近环带对照、部分覆盖厚度、cycle drift、质量与端口响应门。质量、端口电流闭合、状态范围、温度范围和热平衡均为独立硬守卫。

空间与时间采用三套独立层级；medium–fine field、事件幅值/时间、峰值电流/温度阈值均在 JSON 中冻结。`DIRECT_T_TO_TRANSPORT_OFF` 与 `FULL_ISOTHERMAL_COUPLING_OFF` 分别裁决直接温度输运反馈和完整电热反馈；效应必须超过两支的联合数值不确定性。

## 4. 案例、防泄漏与 CTH 身份

完整统计 case 是对象、几何、constitutive/material branch、初态、完整 waveform bundle 与完整 history 的不可分割组合。case ID 的 SHA256 只保护这个不可变身份；mesh、time step 与 seed 都不是新 case。每个 case 只能属于 `Q/D/I/F_A/F_O/R` 之一。

- Q：oracle、事件、thermal controls、evaluator floor 与 strong-raw 资格；
- D：唯一允许调参、早停和选择控制的池；
- I：求解前 hash-split 为 `I_S1/I_S2`，分别在 Stage 1/2 臂冻结后只开一次；
- F_A：sealed waveform-axis formal，其他因素在 development support 内；
- F_O：至少整轴留出一个 geometry/branch/initial/history 因素；
- R：本 GOAL 永不打开。

训练节点固定为 (delta\in\{-1,-1/2,0,1/2,1\})。

\[
P_4(\delta)=\frac73\delta^2-\frac43\delta^4
\]

在五个训练节点精确等于 (|\delta|)；identity 点固定为 (pm1/4,pm3/4)，其 (|\delta|-P_4) 的符号翻转是预注册的 exact-smooth kill。CTH 只允许称 `CONDITIONAL_APPLICATION_SPECIFIC_TRANSPORT_ARCHITECTURE_ADAPTATION`。

## 5. raw、development 与 formal

strong raw 只有在 Q 上全部物理守卫通过、有限 seed/intent 比例、标准化 endpoint 阈值和事件方向/定位同时达标时才称 `COMPETENT`。transport bottleneck 还须在多数完整 cases 中成为最大子系统误差、超越电/热与 oracle floor，并通过 (delta=\pm1/4) 的响应和 event-time-shift 控制。

Stage 1 严格比较 raw、Taylor2、exact P4 与 CTH；Stage 2 严格加入 direct Jacobian、smooth6、spline、learned basis、generic hinge、wider raw、extra-work raw、wrong-knot 和 independent-per-view raw。任一强控制吸收收益即按 live plan 转负向/benchmark 稿，不增 seed、移 knot 或补第二 hinge。

formal 固定 primary、strong raw 和最强 non-primary challenger 三臂；每 case 三个嵌套 seed，不跨 configuration warm-start。四个 superiority/noninferiority 门各用 one-sided alpha `0.0125`，margin 均为 `0.5` oracle-floor units。case 数只由开封前冻结的 power 规则从 `8/12/16/20/24/32` 选择，并保留 20% formal failure reserve；预算不足记 `FORMAL_POWER_BUDGET_INSUFFICIENT`。

NaN、OOM、timeout、divergence 或物理守卫失败统一计 (Z=+\infty)，保留全部 gross compute。只有在任何指标被读取前可对已核验的外部中断做一次 exact replay；不替换 case/seed，不 formal peeking 或重封。

## 6. 完成与主张边界

正向、负向比较、clean-room limits 或 synthetic benchmark 四种稿件身份均由实际证据选择。S0 只证明合同已冻结；它不证明 source、object、event、raw、CTH、formal 或论文主张成立。总 GOAL 仍只有在正文、实际结果、最终图表/主表、参考文献、补充材料、复现包与 claim-boundary audit 全部完成后收口。
