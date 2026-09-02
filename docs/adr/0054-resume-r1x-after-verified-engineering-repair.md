# 在已验证工程修复后恢复 R1X 原科学任务

R1X 的两次启动均在首个 optimizer step 前因隔离部署依赖不完整而终止，科学轨迹计数保持为零；随后完整传递依赖已写入内容寻址清单，并由只含清单文件的隔离 physics-load 回归验证。用户于 2026-09-03 明确覆盖旧合同的一次 engineering-retry 限制，决定继续原 `PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE`，不改变其科学身份、三条 exploration/一条 confirmation 上限、机器树、seed、reference/stress 边界或停止条件。

该决定同时确立通用规则：已经明确授权的科学任务若在首个 optimizer step 前因纯工程故障终止，且没有形成科学轨迹，只有在根因明确并由针对性隔离回归证明完全修复后，才可重新执行相同冻结任务；工程启动不消耗科学 run 配额，且这一规则覆盖更早合同中的工程 retry 次数限制。任何科学输入、方法、物理、seed、阈值或停止条件变化仍需独立授权。

## Consequences

- R1X 以 `E1_CLEAN_COUPLING_EXPLORATION`、`NON_VOTING_DEVELOPMENT_EXPLORATION` 和 0/3 exploration 计数恢复。
- 云端必须先通过 bundle identity、isolated physics load、V100、空闲进程及 reference-absence 前检，随后才进入 E1。
- 2026-09-02 engineering-blocked closeout 保持历史事实，不被改写成科学失败；若 E1 产生科学轨迹，后续仍完全遵循 ADR 0053 的机器树与每条运行后立即关机规则。
