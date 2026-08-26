# 0023：KC 入场前必须通过收敛事件门与两级 strong-raw 门

- `status`: `ACCEPTED`
- `accepted_at`: `2026-08-21`
- `superseded_in_part_by`: `ADR_0027`
- `decision_scope`: `FUTURE_ORACLE_EVENT_AND_STRONG_RAW_ADMISSION`
- `claim_status`: `PROPOSED_METHOD_NO_NUMERICAL_EVIDENCE`

ADR 0027 已撤销本 ADR 中“路线已消耗/进入下一槽位”的全局计数语义；事件门、两级 strong-raw 门和当前合同内停止处置继续有效。

任何 PINN 运行前，候选 oracle 必须在至少两个重复周期中分别出现形成与恢复，空间时序差高于时间和空间离散分辨率，相变保持局部、部分覆盖而非整域同步翻转，且核心事件诊断随离散加密收敛；允许多点成核或不连续传播，不要求单一锐利前沿。具体时间差、覆盖率和收敛裕量必须按来源尺度在方法结果出现前冻结，不能因 KC 表现移动。

事件门通过后，每条路线只允许结果出现前登记的两级 strong-raw 梯度：一个强直接基线和一次预算匹配的容量或优化升级。若 raw 已达到 oracle/离散误差地板，路线记为已消耗并裁决 `NO_BOTTLENECK`，不得挖掘事后更难案例；若两级 raw 都不能胜任事件解析，路线记为已消耗并裁决 `RAW_INCOMPETENT_ROUTE_NO_TEST`。两种处置均禁止启动 KC；再换架构或训练协议必须进入下一路线，只有方法外执行损坏可按原合同精确重放。本 ADR 不冻结具体网络或数值阈值，也不授权运行。
