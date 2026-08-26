# 0032：延后 side 方法选择并约束 HFO PINN 训练比较

- `status`: `ACCEPTED`
- `accepted_at`: `2026-08-25`
- `decision_scope`: `HFO_POST_G1_PINN_METHOD_AND_TRAINING_PLANNING`
- `amends`: `ADR_0031`
- `supersedes_in_part`: `2026-08-24_HFO_POST_G1_ROADMAP_Q30_Q36`
- `claim_status`: `PROPOSED_METHOD_NO_NUMERICAL_EVIDENCE`

用户接受引用会话“深度论文审查”对 Q30–Q36 的对抗性修订。Q24 的三物理块公共 backbone 继续保留，但先前 Q30 预选 transport-only SRF 的决定撤回：`SIDE+` 只打开方法候选梯级，必须先定位 side 载荷并比较 SA/Jacobian 式直接参数切线与物理输出割线控制；只有 raw 胜任、简单近邻不足且载荷主要位于输运块时，transport-only 一侧架构才可另立设计。fixed-slot latent slots 继续不准作为正面机制。

Q31 条件接受 cKC-NP：只有未来 `TEMPORAL+` 后，才允许端点归一、空间无关、有界正速率的低维时钟；它只作用于输运块并完整回拉时间导数，电学、热学、外加波形、跨视图配对和评价均留在物理时间。transport 参数必须来源冻结，clock 不得读取空间、温度或状态，也不得被解释为真实器件时钟或热松弛。

Q32 接受一次性的 backbone 资格比较：raw-coordinate、参数量匹配 wider raw 和来源尺度 deterministic spatial Fourier 三臂在 development 上比较，胜者随后冻结为所有方法的公共编码。Q33 改为归因轨完全不使用 curriculum；累计 time-prefix 只可作为 temporal comparator，并须与 full-horizon 控制匹配总 residual-point、PDE AD、optimizer closure 和 wall-clock，任何 coefficient homotopy、伪初态或按 loss/event 改前缀均禁止进入科学证据。

Q34 保留冻结方程块权重；best-method 轨最多允许一个组内有界、均值归一且不改变 IC/BC、质量、no-flux 或端口守卫的 pointwise weighting comparator，并在确定性二阶段优化前冻结。Q35 保留固定-support attribution，best-method 轨最多单列一种 residual/causal adaptive sampling baseline，完整计入候选池和自动微分成本。Q36 接受统一 FP64、固定更新数的 Adam→确定性二阶段调度；诊断只记录，除预声明实现有效性失败外不在线控制训练。

本 ADR 记录未来方法与训练比较的边界，不冻结网络规模、频率、prefix 数、权重上下限、采样比例、预算或实用效应门，也不授权来源检索、solver、PINN、training、formal、GPU、付费计算或 Git 发布。当前 G0–G1 阻塞状态及 ADR 0031 的对象、事件和 TKB 前门保持不变。
