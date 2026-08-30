# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料/器件”的纯软件研究项目。目标是以可复现、证据闭合的方式推进到中科院二区 SCI 定位的论文初稿；该定位不是接收承诺，合成数值证据也不等同于实验验证。

## 当前状态

- `phase_id`: `PHK_V22_ONE_WEEK_SPRINT_ACTIVE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `authorization_scope`: `PHK_V22R_V11_FULL_SPRINT_EXPLICITLY_AUTHORIZED`
- `claim_status`: `GPU_PROFILE_VERIFIED_NEURAL_METHOD_RESULT_NOT_YET_ESTABLISHED`

当前执行 [PHK-V2.2R v1.1 四臂 Method-MVP 与论文初稿冲刺](docs/plans/NEXT_ACTIONS.md)：保留 PHK-V2.1 Oracle No-Go，以 nominal extra-fine 为本地 development-only fixed-discretization reference。GPU profile 已完成；strict PHA 增益门失败并退出关键路径，generic-RAR 截止已过，因此后续固定为 strong raw、MF-only、sampler-only 与 MF+sampler 四臂，两个 stress extra-fine 继续密封。

第七天终点是包含完整方法主体和有限真实单-seed结果的导师评审稿，不是 formal OOD、多 seed、实验材料校准或 SOTA 证据。任何正向主张仍由实际 nominal 与 sealed-case 运行决定。

三场强残差、四个 primary arms、physics sampler、prediction/evaluator、stress 封存门和
decision core 已实现；两份 stress extra-fine 已完成字节 seal 且未开封。V100 五臂
100-update profile 均有限，四个 primary arms 为 0.5203–0.5673 s/update；profile 只支持
工程成本与 strict-PHA 路由裁决，不支持方法排序。用户现已明确批准完整后续冲刺；P0 v1.1
合同、runner、run card 与文档已对齐，聚焦测试 16/16、组合回归 47/47 和文档一致性门禁
通过，当前进入尚未产生结果的四臂 nominal 阶段。AutoDL 总额仍不超过人民币 150 元，当前
仓库可选择性 commit/push；作者联系和期刊投稿未授权。当前决定见
[ADR 0048](docs/adr/0048-activate-phk-v22r-v11-four-arm-sprint-after-gpu-profile.md)，
profile 事实见[收口记录](docs/experiment/2026-08-30-phk-v22r-gpu-profile-closeout.md)，P0
事实见[对齐收口](docs/experiment/2026-08-30-phk-v22r-v11-alignment-closeout.md)，跨工具协作与
数据位置见[冲刺工作流](docs/governance/2026-08-30-sprint-collaboration-and-data-routing.md)。

历史 PHK-V2.1 仍固定为 `PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN`，无 Sharp/PF/PINN/PHA/KC/formal 方法证据；其 [terminal summary](outputs/runs/20260828T-phk-v21-s1-q-terminal-summary-001/summary.json)与 [paper_v21](paper/paper_v21/README.md)保持原样。V2、V1 和全部更早 No-Go 同样不回写。

当前授权读 [active_phase.md](active_phase.md)，已核验事实读 [PROJECT_STATE.md](PROJECT_STATE.md)，研究与论文口径读 [CONTEXT.md](CONTEXT.md)，完整文档路由读 [docs/README.md](docs/README.md)。
V2.2R 的近期方法替换、止损和论文故事讨论已按当前合同收录为[研究策略整合笔记](docs/notes/2026-08-29-phk-v22r-recent-research-strategy-integration.md)；该笔记不改变授权或科学状态。
