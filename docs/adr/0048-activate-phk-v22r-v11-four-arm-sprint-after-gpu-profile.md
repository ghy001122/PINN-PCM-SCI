# ADR 0048：在 GPU profile 后激活 PHK-V2.2R v1.1 四臂冲刺

- `status`: `ACCEPTED_ACTIVE`
- `date`: `2026-08-30`
- `phase_id`: `PHK_V22_ONE_WEEK_SPRINT_ACTIVE`
- `supersedes`: `ADR_0047_FORWARD_EXECUTION_AFTER_GPU_PROFILE_ONLY`
- `preserves`: `ADR_0047_LAUNCH_HISTORY_PHK_V21_NO_GO_AND_ALL_PRIOR_EVIDENCE`
- `decision_source`: 当前用户明确命令与会话 `01a04cca-1ec8-7b61-afba-9442cbbbc023`
- `profile_record`: `docs/experiment/2026-08-30-phk-v22r-gpu-profile-closeout.md`

## 决定

接受目标会话形成的 v1.1 收缩，并由当前用户命令解除此前“等待再次授权”的即时暂停。
执行从 P0 版本化对齐开始，随后在同一 V100 上连续推进四臂 nominal、条件性 candidate
freeze、六份 stress prediction、一次性本地开封、图表、复现材料和论文初稿。到达预声明
PASS、bounded/Pareto、No-Go 或真正执行阻塞时按相应分支收口，不为获得正结论移动标准。

generic-RAR 的预声明 P0 截止已经过去且未形成稳定实现，采用四臂 fallback：

1. `STRONG_RAW`
2. `MF_ONLY`
3. `SAMPLER_ONLY`
4. `MF_PLUS_SAMPLER`

只有 `MF_PLUS_SAMPLER` 可作为 proposed method 晋级。nominal 固定为 FP64、seed 17、
Band A、scratch start、`512/128/128` 点、Adam、1000 updates 与 final checkpoint only。
Route B/C、functional pivots、generic RAR、strict PHA、early stop、warm start、L-BFGS、
SIREN 与 continuation 本周停用。

## Profile 消费

GPU profile 的五臂均有限。Strict PHA 的成本比 1.627636 通过 1.8× 成本门，但 primary
改善为 0，未达到 10% 增益门，因此按既有合同删除 routing 且不得调 gate。该结果只消费
strict-PHA 探针，不对四个 primary arms 排序，也不建立任何正面方法主张。

旧 v1 program/method contracts、runner、decision machine、cloud run card 与稿件仍含
strict PHA、functional pivots 或 A→B 语义。它们不得直接运行 nominal；P0 必须先版本化
修订并同时通过聚焦测试、组合回归与文档一致性门禁。

## 授权

用户明确批准完整后续冲刺，不再要求 routine 阶段性批准。授权包括必要的本地代码与配置
修改、V100 有界训练、结果回收、本地 nominal/sealed 评价、图表、复现材料、论文初稿及
当前仓库选择性 commit/push。AutoDL 累计硬上限保持人民币 150 元；每轮付费训练或结果
回收完成后直接关机。作者联系、凭据披露、期刊投稿和投稿系统上传仍未授权。

## 不变边界

- PHK-V2.1 与全部历史 No-Go、失败 intent 和论文包不回写。
- 对象始终是 synthetic, dimensionless, phase-change-memory-inspired electrothermal
  wall-cell fixed-discretization benchmark；不是 continuum truth、材料校准、数字孪生或实验验证。
- nominal reference 仅供本地开发裁决；stress references 在 candidate 与六份 prediction
  carrier 冻结核验前不可读，并且永不上传云端。
- 正向结果只能来自冻结评价；实现、GPU profile、Git 或稿件完成均不证明方法有效。
