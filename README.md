# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料/器件”的纯软件研究项目。目标是以可复现、证据闭合的方式推进到中科院二区 SCI 定位的论文初稿；该定位不是接收承诺，合成数值证据也不等同于实验验证。

## 当前状态

- `phase_id`: `PHK_V22_ONE_WEEK_SPRINT_ACTIVE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `authorization_scope`: `PHK_V22R_EXPLICIT_EXECUTION_AUTHORIZED`
- `claim_status`: `IMPLEMENTATION_VERIFIED_NEURAL_METHOD_RESULT_NOT_YET_ESTABLISHED`

当前执行 [PHK-V2.2R 极速方法抢救冲刺](docs/plans/NEXT_ACTIONS.md)：保留 PHK-V2.1 Oracle No-Go，以现有 nominal extra-fine 为 development-only fixed-discretization reference，默认实现 `FS-PJAMF-PINN` 的 strong raw、各向异性多频和 phase/Joule-aware sampling；两个 stress extra-fine 在候选冻结前密封。

第七天终点是包含完整方法主体和有限真实单-seed结果的导师评审稿，不是 formal OOD、多 seed、实验材料校准或 SOTA 证据。任何正向主张仍由实际 nominal 与 sealed-case 运行决定。

三场强残差、四个 primary arms、physics sampler、prediction/evaluator、stress
封存门和 machine decision 已实现并通过 13 项聚焦测试；两份 stress extra-fine
也已成功生成、通过字节哈希复核并保持未开封。这只建立实现和 reference 身份，尚未
建立方法效果。用户已授权本轮代码/求解/PINN、两份 stress extra-fine、AutoDL
总额不超过人民币 150 元、论文制品以及当前仓库 commit/push；作者联系和期刊投稿
未授权。边界见 [program contract](configs/phk_v22r/program_contract.json) 与
[method contract](configs/phk_v22r/method_contract.json)，决定理由见
[ADR 0047](docs/adr/0047-adopt-phk-v22r-rapid-method-rescue-sprint.md)。

历史 PHK-V2.1 仍固定为 `PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN`，无 Sharp/PF/PINN/PHA/KC/formal 方法证据；其 [terminal summary](outputs/runs/20260828T-phk-v21-s1-q-terminal-summary-001/summary.json)与 [paper_v21](paper/paper_v21/README.md)保持原样。V2、V1 和全部更早 No-Go 同样不回写。

当前授权读 [active_phase.md](active_phase.md)，已核验事实读 [PROJECT_STATE.md](PROJECT_STATE.md)，研究与论文口径读 [CONTEXT.md](CONTEXT.md)，完整文档路由读 [docs/README.md](docs/README.md)。
