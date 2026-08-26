# 0031：修订 HFO 来源初态、侧向信息门与方法路由

- `status`: `ACCEPTED`
- `accepted_at`: `2026-08-24`
- `decision_scope`: `HFO_NP_V1_G0_G1_PLANNING_REFINEMENT`
- `supersedes_in_part`: `ADR_0030`
- `claim_status`: `PROPOSED_METHOD_NO_NUMERICAL_EVIDENCE`

在用户提供 HFO-NP-v1、SRPG 与 KC′ 对抗性深度审查后，项目保留 ADR 0030 选择 HFO-NP-v1、守恒缺陷态、完整 history/state、`A/A′/ENGINEERING` 和 side/temporal 证据路由的决定，但撤回四个过强前提：来源已支持有限-gap初态、G1 同时资格化 SET/RESET 两轴、`5×` 数值地板足以证明 side 信息，以及 fixed-slot SRPG 可作默认主机制。原因是这些前提分别受来源身份未闭合、12-intent 预算不可辨、光滑曲率反例和 same-network/latent-gauge 不可辨识约束。

HFO-NP-v1 继续是唯一规划对象，身份为透明 `derived/synthetic`，但状态改为 `SOURCE_CONTRACT_BLOCKED`。G0 必须在来源连续 CF 与精确可用的 reset snapshot 之间冻结一个初态；无精确 snapshot 时不得自造有限 gap。连续 CF 分支的事件顺序为 `RESET gap opening → SET gap closing`，第一轮只资格化 RESET amplitude；只有精确 finite-gap restart 分支才允许先 SET 并资格化 SET amplitude。第二周期连续携带内部态，只称 derived stress test，不称作者 replay。

G1 的 side 门改为 Tangent–Kink/Branch 复合门：在唯一协议轴的 `±ε` 与 `±ε/2` 上比较一侧割线，联合两尺度未归一化斜率跳跃、数值不确定性、显式 smooth-quadratic null、连续 gap/通量指标、端口守卫和中/细分支一致性。原 `5×` 倍率只保留为显著性组成，不再是充分条件；不能拒绝光滑二次零假设即 `NO_SIDE_RESOLVED_INFORMATION`。

fixed-slot SRPG 降为 `REVISE_MAJOR_NOT_ADMITTED`，最多作为带 basis/scale/head/shuffle 负控的参数化诊断。`SIDE+` 只打开新的 side-method PLAN，不自动指定方法；直接约束物理输出响应场的 SRF-PINN 作为优先审查的 parking-lot 候选。`TEMPORAL+` 只能由未来另批 strong-raw 建立，届时 KC′必须改成空间无关、保持散度/质量/no-flux 并按物理时间评价的 `cKC-NP`，不得称 electrothermal clock。只有 SIDE+ 与 TEMPORAL+ 同时成立才允许 identity/side/clock/interaction 的 2×2；两者均为负时停止，不自动启动 PHA、IRAC 或新对象。

修订后的 G0 仍为 `0 solve / ≤8 primary sources`。G1 若未来另获批准，最多 12 个 CPU intents：三层连续两周期基础案例、一次 medium 零驱动，以及唯一轴 `±ε, ±ε/2` 的 medium/fine 八个资格案例；上限 `48 h wall / 64 CPU-core-h / 0 PINN`。G1 通过只形成 side 预资格，不形成完整 oracle、方法支持或论文主张。本 ADR 只接受规划修订，不授权来源检索、求解、实现、训练、formal、GPU、付费计算或 Git 发布。
