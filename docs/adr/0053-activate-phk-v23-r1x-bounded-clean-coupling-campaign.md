# ADR 0053: 激活 PHK-V2.3 R1X 有界 clean-coupling campaign

- `status`: `ACCEPTED_ACTIVE`
- `date`: `2026-09-02`
- `decision_id`: `ADR_0053_ACTIVATE_PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN`
- `supersedes_authority`: `ADR_0052_R1A_AUTHORIZATION_ONLY`
- `preserves`: `V22R_R0A_R0B_R0C_R1A_EVIDENCE_WITHOUT_REWRITE`

## Context

PHK-V2.2R 四臂均无基本事件能力。R0C 表明 raw-gradient 小不等同于 Adam 有效更新小；R1a 表明 standard ConFIG 能按定义消除四组方向冲突并降低 PDE loss，但仍没有任何 `phase>=0.5` 活动。当前尚存的高价值问题是：避免随机 phase head 污染早期反馈后，先建立两周期电热驱动，再逐步恢复 phase 学习与完整耦合，能否恢复 raw competence。

## Decision

接受用户在 2026-09-02 明确给出的 `PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE`。该授权仅覆盖：最多三条 seed-17、V100/FP64、from-scratch、reference-blind non-voting exploration，以及首条 competence signal 后最多一条完全冻结的 from-scratch confirmation。

机器树、cold-state coupling homotopy、readiness、E2 互斥单轴、E3 延长、评价顺序与运行数量上限由三份 R1X 合同共同冻结。GPU 小时、费用与日历不再是本 campaign 的停止门，但必须逐条记录。每条云端运行完成后必须先回收并核验产物，立即关闭 AutoDL 并验证关机，之后才可在本地读取 nominal development reference。

## Consequences

- R1X 是 solver competence recovery，不自动构成论文 headline innovation。
- ConFIG、staggered blocks、coupling homotopy 与 output lift 均透明标记为 shared solver backbone。
- nominal reference 不得进入云端训练、trigger、alpha、sampler、初始化、checkpoint selection 或 threshold；stress 始终 sealed/unread。
- 若三条 exploration 均未恢复 competence、E2 无 material phase signal、E3 失败、confirmation 失败或出现科学数值 invalid，则 pure-scratch 路线终止。
- 本 ADR 不授权 PJGR、R2、low-fidelity、其他 seed、stress 或投稿。

## Governing contracts

- [program contract](../../configs/phk_v23/program_contract_r1x_bounded_clean_coupling.json)
- [method contract](../../configs/phk_v23/method_contract_r1x_clean_coupling.json)
- [exploration contract](../../configs/phk_v23/exploration_contract_r1x_bounded_clean_coupling.json)
- [live plan](../plans/NEXT_ACTIONS.md)
