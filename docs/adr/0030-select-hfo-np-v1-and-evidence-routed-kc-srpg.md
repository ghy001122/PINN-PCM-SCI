# 0030：选择 HFO-NP-v1 规划对象与条件式 KC′/SRPG 证据路由

- `status`: `SUPERSEDED_IN_PART_BY_ADR_0031`
- `accepted_at`: `2026-08-24`
- `decision_scope`: `NEXT_G0_G1_OBJECT_AND_METHOD_ROUTING`
- `claim_status`: `PROPOSED_METHOD_NO_NUMERICAL_EVIDENCE`
- `decision_id`: `HFO_NP_V1_EVIDENCE_ROUTED_KC_SRPG_GRILL_2026-08-24`

用户把“快速推进”冻结为最短路径获得有辨别力、可复现的科学 Go/No-Go，并接受以守恒氧空位/缺陷浓度作为缺陷态忆阻器的内部序参量。下一份 G0–G1 PLAN 因此只以 `HFO-NP-v1` 为对象：从 2020 HfO₂₋ₓ Nernst–Planck、电流连续和准稳态 Joule 热方程结构建立透明 `derived/synthetic` 二维轴对称 benchmark。它不得称为作者 COMSOL 重放、开放 oracle、结构晶相或实验真值；TaOₓ、Sevic–Kobayashi、R1、Q‑POP 和 FerroX 都不自动接替。

对象采用严格 `A/A′/ENGINEERING` 分层：来源固定方程、物理尺度、几何与边界，`A′` 只允许重复来源波形、构造预声明协议邻域和等价数值表示，`ENGINEERING` 只包含容差、网格与输出控制。任何决定 gap 拓扑或绝对时间尺度的缺失物理量不得按结果校准；不能闭合即终止对象路线。

对象采用来源结构支持的预成丝与有限 gap 初态，不把 electroforming 纳入计分。合格事件是连续两个双极计分周期中同一局部 filament gap 的闭合与重新打开；gap/连通性是结构主身份，缺陷面积只作诊断，完整端口电流或电导轨迹作为独立器件守卫。完整案例身份由初始缺陷场、整条双极波形、协议参数和绝对时间共同闭合，不允许用瞬时电压单独代表迟滞 history。

SRPG 的最小训练实体改为局部协议束：一个基础协议及共享几何、初态和时空支撑的成对邻域协议共同训练一个逐束 PINN，不形成全局神经算子。资格阶段使用 SET 与 RESET 峰值幅度两个独立协议轴，每轴保留围绕基准值的正、负扰动；`side` 表示沿同一协议轴的增减，不表示电压极性。

方法不预定双模块胜出。若独立资格证据既无稳定双侧信息也无时间瓶颈，则停止方法路线；仅有双侧信息时只准入 SRPG，仅有时间瓶颈时只准入结构动力学时钟 KC′，二者同时存在时才允许实际计算匹配的 KC′×SRPG 因子归因。IRAC 保持 supporting/强基线身份，不进入主要创新标题。该架构选择不授权来源扩搜、对象实现、solver、oracle、PINN、训练、formal、GPU、付费计算或 Git 发布；执行范围仍须由完成后的 live PLAN 和 `active_phase.md` 另行授权。

SRPG 的信息准入必须独立于训练收益：基础对象先通过两周期 gap 事件与离散资格，随后至少一个协议轴在两级预冻结扰动尺度上显示超过最细两层综合数值不确定性 `5×` 的双侧非对称及事件/端口变化，且方向一致、不依赖单一网格。未通过时裁决 `NO_SIDE_RESOLVED_INFORMATION`，不得靠调扰动、损失权重或先训练 SRPG 救援。
