# ADR 0047：采纳 PHK-V2.2R 极速方法抢救冲刺

- `status`: `ACCEPTED_ACTIVE`
- `date`: `2026-08-29`
- `phase_id`: `PHK_V22_ONE_WEEK_SPRINT_ACTIVE`
- `decision_source`: 当前用户明确执行命令及其指定的完整会话 `6a8f9ed2-a678-83ee-ac63-3fc48de531f8`
- `machine_contract`: `configs/phk_v22r/program_contract.json`

## 决定

在不回写 PHK-V2.1 Oracle No-Go 的前提下，启动独立的 `PHK-V2.2R / RAPID METHOD-RESCUE AND POSITIVE-EVIDENCE SPRINT`。七天终点是包含完整方法主体、有限真实数值结果、图表和复现入口的投稿形态导师评审稿，不假装已经形成 formal OOD、多 seed 或实验验证证据。

默认关键路径采用 S-first：`strong raw → anisotropic MF → phase/Joule sampler → MF+sampler`。论文候选方法暂名 `FS-PJAMF-PINN`。Strict PHA 只做一次 100-update 严格自动微分探针；实际 Joule 梯度不进入输出 gate。若成本、数值稳定性或开发增益门失败，routing 立即退出关键路径。

开发评分只使用 nominal extra-fine；它不得成为训练标签或采样特征。narrow-interface 与 wide-heater 各生成一次 extra-fine，但在候选冻结前保持 sealed。最新 V2.2R 合同将第七天正式证据压缩为 `2 sealed cases × 1 seed × 3 arms`；早期会话中的三-seed完整矩阵改为稿后第一升级，不再阻塞初稿。

只允许一次 A→B：全部 physics-only arms 都不具基本 competence 时，才启用 1% medium、全场、分层 Sobol anchors。A 已具 competence 但 proposed 无可归因增量时直接 No-Go；B 未击败 same-anchor raw、data-only 与 medium interpolation 时停止，不开启 C。

## 授权

用户已明确授权本轮代码、配置、CPU/长时间求解、PINN/GPU训练、两份 stress extra-fine、论文与图表、当前仓库 Git commit/push，以及 AutoDL 不超过人民币 150 元的付费 GPU。云端不得接收任一 extra-fine reference field；checkpoint、预测和日志下载后，只在本地开封评价。作者联系、期刊投稿和投稿系统上传仍未授权。

## 理由

PHK-V2.1 已经提供稳定的二维局域电—热—相态对象和固定离散 carrier；阻塞点是 event-time 连续极限资格门，而不是所有场或求解器均不可用。将该 carrier 诚实地改作 fixed-discretization development benchmark，可以立即检验 PINN 表示和 support 分配，而不伪造 continuum truth。S-first 比先重写严格 routing 更可能在一周内形成可训练竖切和第一张可信方法图。

## 不变边界

- `PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN` 及所有历史产物、失败和 `NOT_REACHED` 语义不变。
- benchmark 始终是透明、无量纲、literature-inspired synthetic wall-cell，不是材料校准、作者模型重放或实验器件。
- 正向结果只能来自实际评价；“positive-evidence sprint”不是预先保证正结论。
- Fourier、adaptive sampling、staggered/continuation 等来源身份必须透明；PCM 定向接口和组合贡献不得冒充底层模块首创。

## 截止与止损

- 2026-08-30 23:59 前选定 S、PHA、B 或 No-Go。
- 2026-09-02 23:59 后禁止新增实验轴。
- 2026-09-04 23:59 前交付完整初稿。
- stress 开封只允许形成 PASS、No-Go、regime-aware 或 Pareto 边界，不得返回开发集重调。
