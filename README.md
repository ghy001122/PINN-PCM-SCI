# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物/相变材料与器件”的纯软件研究项目。目标是以可复现、证据闭合的方式形成中科院二区定位的论文初稿；这不是期刊接收承诺，合成数值证据也不等于实验验证。

## 当前状态

- `phase_id`: `PHK_V22_ONE_WEEK_SPRINT_TERMINAL_NO_GO`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `MVP_NO_GO_NO_BASIC_COMPETENCE_ADVISOR_DRAFT_COMPLETE`

PHK-V2.2R v1.1 四臂 nominal 已完成。四臂均有限执行且 PDE loss 下降，但都没有产生两次局域相变事件；冻结决策为 `MVP_NO_GO_NO_BASIC_COMPETENCE`。因此没有候选、没有 confirmation、没有 stress 解封，也没有正向方法增益主张。AutoDL 实例已在产物哈希核验后关闭，累计估算支出 4.810058 元。

现有证据支持的核心表述是：在固定单 seed、1000-update、fixed-discretization nominal 协议下，physics-loss 收敛与小的全域平均误差没有构成局域事件 competence 证书。它不表示 PINN 全局失败，不支持 continuum、formal OOD、材料校准或实验主张。

## 当前入口

- 授权边界：[active_phase.md](active_phase.md)
- 已核验状态：[PROJECT_STATE.md](PROJECT_STATE.md)
- 唯一 live plan：[docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)
- 终局运行记录：[nominal terminal closeout](docs/experiment/2026-08-30-phk-v22r-v11-nominal-terminal-closeout.md)
- 英文导师初稿与五图复现包：[paper/paper_v22r](paper/paper_v22r/README.md)
- 文档地图：[docs/README.md](docs/README.md)
- 当前研究口径：[CONTEXT.md](CONTEXT.md)

PHK-V2.1 的 `PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN`、PHK-V2、V1 与更早历史结果均保持原样。本轮只新增一项边界清楚的 neural Method-MVP 负面证据。
