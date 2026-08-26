# 0038：将 TKF 重构为有限预算 CTH 并增加热因果、可容许性与效用门

- `status`: `ACCEPTED`
- `accepted_at`: `2026-08-25`
- `decision_scope`: `HFO_CTH_FINITE_BUDGET_HINGE_THERMAL_CAUSALITY_ADMISSIBILITY_AND_UTILITY`
- `amends`: `ADR_0033, ADR_0035, ADR_0036, ADR_0037`
- `supersedes_in_part`: `TKF_CANON_LIVE_METHOD_NAME_AND_TRUE_KINK_SEMANTICS`
- `claim_status`: `PLANNING_DECISION_NO_NEW_SCIENTIFIC_EVIDENCE`

用户接受 grill-with-docs Q59–Q63 的全部推荐。原 TKF-CANON-PINN 不再作为当前方法名称；其固定 canonical 协议基保留，但条件式 FULL_PLAN 靶标改名为 **CTH-PINN（Canonical Transport Hinge-Enriched PINN）**。该方法只能主张：在来源闭合、有限尺度尖锐响应已经独立资格化的局部协议族中，显式 hinge 归纳偏置能否在有限网络容量与有限实际计算预算下改善 held-out 协议响应和完整事件保真。有限扰动证据、hinge 系数或训练收益均不能证明真实物理解映射不可微、发现真实 kink 或恢复唯一物理导数跳跃。

原 `FIELD_KINK_PLUS` 相应改为 `FIELD_HINGE_RELEVANCE_PLUS`。它只判断排除纯事件时间平移后，三尺度连续输运场是否仍呈现足以让固定 hinge 成为合理有限预算候选的有限尺度一侧响应；它不是数学不可微性证书。历史 TKF-v0/TKF-CANON 的不可辨识反例、smooth4、错结点与 held-out microview 负担继续有效，并由未来 `CTH_DIAGNOSTIC_IDENTITY_PROTOCOL` 消费。

CTH 与 smooth4 必须在系数层使用相同、可审计的物理可容许变换。共享初态和协议不变边界不能仅靠不同协议视图之间的抵消满足：所有参数相关浓度系数在共同初态上消失，blocking/no-flux 边界上的相应法向通量系数分别为零，其他来源固定边界亦逐系数保持。违反该合同属于实现无效，不是方法失败或可调 penalty。

HFO 的准稳态温度不得只作装饰。G0 必须确认存在来源支持的 `T ->` vacancy mobility/diffusion/chemical-potential 反馈；G1 在基础对象和零驱动通过后、side block 前增加一个 medium `thermal-feedback-off` 配对 intent，只冻结 transport 系数的温度反馈而继续求解同一电学与热学闭合。其事件、连续空位量和端口差异必须超过联合数值不确定性；否则记 `HFO_THERMAL_CAUSALITY_NO_GO`，关闭当前电热 HFO 方法论文路线。G1 因此由 12 增为最多 13 intents，但仍保持 `<=48 h wall / <=64 CPU-core-h / 0 PINN`；预算内不能裁决时记 `INCONCLUSIVE_BUDGET_EXHAUSTED`，不追加预算。

若 G0/G1 表明力学化学势对来源模型保真或目标 gap 事件不可忽略，当前三物理块路线停止并返回新的对象 PLAN；不得静默删除力学，也不得在本路线中自动增加第四物理块。若力学不是必要因素，须以来源证据明确冻结无力学分支。

未来方法比较还必须加入 aggregate-compute-matched 的 `independent-per-view strong raw PINNs`。CTH 除面对参数条件化 strong raw、smooth4、SA/direct Jacobian、wider raw 与 extra-work raw 外，还须回答联合协议束求解的实际价值：在五个已见协议上不能被独立求解严格支配，并须以不新增训练的 held-out microview 预测或明确的总协议束成本显示非支配效用。否则即使身份探针通过，也记 `CTH_BUNDLE_UTILITY_NO_GO`。

这些决定只修订 future plan。CTH 仍为 `SELECTED_AS_CONDITIONAL_FULL_PLAN_DESIGN_TARGET_NOT_ADMITTED / NOT_AUTHORIZED / NOT_NOVELTY_CLEARED`；G0、G1、solver、PINN、training、formal、GPU、付费计算和 Git 发布均未获授权。
