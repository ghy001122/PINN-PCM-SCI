# ADR 0064：以 temporal stream identity failure 关闭 PHK-V2.3 LF5

- `status`: `ACCEPTED_COMPLETE`
- `date`: `2026-09-06`
- `phase_id`: `PHK_V23_LF5_CYCLE_RESOLVED_TEMPORAL_ZERO_LEVEL_ALIGNMENT_AND_CONDITIONAL_PHYSICS_PILOT_EXECUTE`
- `activation_commit`: `fe629d6b120c1caaa891692a92062b6fe5ce8178`
- `executed_source_commit`: `eba0ffec8c20a23064488ad42adbaf4e2acc424f`
- `machine_outcome`: `LF5_NUMERICAL_OR_IDENTITY_INVALID`
- `candidate`: `none`

## 决定

保持 CPU-T 的 `LF5_TZL_ALIGNMENT_NOT_SUPPORTED_CPU` 原样。用户在知晓该结果
后，明确授权不变的 DEV-T 作为
`POST_QUALIFICATION_USER_OVERRIDE_EXPLORATORY`。两个首步前部署故障分别由缺失
的 runtime dependency 与未闭合的单独训练输入引起；两次均为零 scientific
update，且只在隔离回归通过后以同一科学身份继续。

第三次部署通过 source、input、GPU 与防泄漏零步预检，并完成固定 400 个
DEV-T updates。base stream 与 spatial-band stream 的最终 SHA 精确匹配；新增
temporal stream 从 step 1 偏离 CPU 冻结 ledger，最终为
`48A0C6B48F6A606B9681E7C349CC5FB089D3D129EF6A40077564E08C9AAFB127`，
而冻结值是
`8FD79D99DAA0175026017BB0025BEFEF896BCB383F46F906A3E800427C9B3BD9`。
runner 按合同在 checkpoint 写出前抛出 identity error。首个 optimizer step 后
不得 retry/resume，故以高优先级 `LF5_NUMERICAL_OR_IDENTITY_INVALID` 关闭。

无合法 checkpoint/prediction，P0 为 `NOT_RUN_HIGHER_PRIORITY_IDENTITY_FAILURE`，
不是 P0 失败。unique next 为 `STOP_NO_SCIENTIFIC_RETRY`。

## 证据解释

step-400 telemetry 显示 finite/potential/phase validity 通过，recall
`0.9175/0.9174`、precision `0.9097/0.9457`、mass `1.0086/0.9701`、phase
weighted MSE `0.0007836`，但 cycle-1 timing error 为 `0.0094`。因为 temporal
identity 无效且没有 checkpoint，这些数值只能作为非投票方向性观察。它们最多
提示 temporal-edge exposure 可能补充 support，却没有解决 cycle-1 timing；不得
称 carrier、TZL 增量、PINN 结果或 candidate。

## 生命周期与后续边界

三份远端 raw 文件已回收并逐文件核对 size/SHA。关机前训练/GPU process 为零，
V100 memory/utilization 为 `0/0`；关机后 TCP 关闭且 SSH 返回
`Connection refused`。fine、extra-fine、direct `LF_ONLY` 与 frozen evaluator
未被 LF5 读取，因为不存在 identity-valid prediction。stress 保持 sealed/unread。

`next_research_execution_authorized=false`。LF5 不得科学重试；任何 matched
control、kinetic/dphi-dt teacher、新 seed、sparse/OOD/stress、PJGR/R2 或投稿
均须新的 PLAN 与 EXECUTE。
