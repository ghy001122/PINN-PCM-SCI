# 0035：冻结因果单机制 pilot、两族 formal OOD 与碰撞否决

- `status`: `ACCEPTED`
- `accepted_at`: `2026-08-25`
- `decision_scope`: `HFO_METHOD_PRIMITIVE_PILOT_FORMAL_AND_COLLISION_ADJUDICATION`
- `amends`: `ADR_0034`
- `supersedes_in_part`: `HFO_Q49_Q53_PRIOR_OPEN_CHOICES`
- `claim_status`: `PLANNING_CONTRACT_NO_NUMERICAL_EVIDENCE`

用户接受 grill-with-docs Q49–Q53 的全部推荐答案。未来 load-bearing 方法只能由以下完整因果链选出：已由 strong-raw 诊断定位的瓶颈，指向一个最小干预；该干预具有直接机制探针和能杀死其核心解释的负控；最后在完整事件主端点上产生计算匹配的增量，并通过全部物理守卫。方法不能因名称新颖、development 排名高或预先偏好 SRF/cKC-NP 而获得入场资格。

首轮 method pilot 只允许一个新的可训练 load-bearing 机制。backbone、物理合同、support、优化框架、评价器和 supporting training choices 必须冻结为公共合同。若未来同时得到 `SIDE+` 与 `TEMPORAL+`，side 与 clock 两条腿也必须分别通过 standalone pilot；只有两腿均合格后，才可另立计划审查 side×clock 2×2 交互，不能在首轮把两个机制捆成不可归因的方法包。

formal OOD 只允许一个与 load-bearing 机制假设直接相关的主要完整案例家族，以及一个与其正交的稳健性完整案例家族；二者都必须位于 G0 最终认可的 HFO-NP-v1 来源有效域内，并保持逐案例独立训练和完整实体隔离。具体厚度、接触/热边界、协议或初态轴只能在来源、事件和机制身份闭合后一次冻结，不采用跨材料测试、随机参数点或无界多轴 factorial 来扩大主张。

效用裁决保持事件优先：目标方法须先在实际计算匹配下超过最佳非目标臂、通过预冻结事件端点与全部物理守卫，并且在冻结计算上限下不被强基线严格支配；达到同一保真度所需成本仅作次要 Pareto 证据。速度、参数量、墙钟或综合分数不能挽救主端点或守卫失败，也不要求候选在每个成本维度都严格优于所有基线。

两次新颖性刷新采用同一碰撞否决：若 direct-near 一手工作覆盖 load-bearing primitive、相同因果主张以及可比的完整事件证据，则在 pilot 或 formal 前停止该主张、降格为 supporting module 或实质收缩范围。组件级碰撞不自动关闭路线，但必须转化为来源透明的强基线、消融和归因负担；仅有“未发现 exact bundle”仍不构成 novelty clearance。

本 ADR 不选择具体 primitive，不冻结 OOD 轴、案例数、seed、预算、统计门或效应阈值，也不授权来源检索、solver、PINN、training、formal、GPU、付费计算或 Git 发布。G0–G1 前门、当前 blocker 和 `NO_SCIENTIFIC_METHOD_CLAIMS` 保持不变。
