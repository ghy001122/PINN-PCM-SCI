# PLAN-PHK-V2.2R-V1：极速方法抢救与正向证据冲刺

- `phase_id`: `PHK_V22_ONE_WEEK_SPRINT_ACTIVE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `claim_status`: `IMPLEMENTATION_VERIFIED_NEURAL_METHOD_RESULT_NOT_YET_ESTABLISHED`
- `authorization_state`: `PHK_V22R_EXPLICIT_EXECUTION_AUTHORIZED`
- `plan_status`: `ACTIVE_D0_CORE_VERIFIED_REFERENCE_SEALING`
- `current_stage`: `D0_CORE_VERIFIED_STRESS_REFERENCES_RUNNING_GPU_HANDOFF_PENDING`
- `next_research_execution_authorized`: `true`
- `supersedes`: `PLAN_PHK_V21_V1_COMPLETED_AT_S1_ORACLE_NO_GO`
- `preserves`: `PHK_V21_ORACLE_NO_GO_AND_ALL_PRIOR_EVIDENCE`
- `program_contract`: `configs/phk_v22r/program_contract.json`
- `method_contract`: `configs/phk_v22r/method_contract.json`
- `decision_record`: `docs/adr/0047-adopt-phk-v22r-rapid-method-rescue-sprint.md`
- `final_deadline`: `2026-09-04T23:59:00+08:00`

## 已完成

1. 冻结 V2.2R program/method contracts、ADR、数据角色、证据门和论文骨架。
2. 实现三场强形式 PINN、完整 IC/BC、对角二阶 AD、四个 primary arms 和
   一次 strict-PHA probe。
3. 实现四窗口等额 replay、physics-aware mixture、reference-blind training、
   checkpoint、prediction carrier、本地 evaluator、stress access gate、nominal
   adjudicator、candidate freeze writer 和云预算 ledger。
4. 12 项聚焦测试全部通过；document consistency 在核心实现前已通过。
5. 两个 stress reference 的 pre-compute intent 已写入，唯一 solve 已并行启动。

## 现在执行

1. 等待两个 solver 完成，只核验退出状态、carrier 字节哈希和 seal，不读场或指标。
2. 用户账号创建 AutoDL V100 32 GB（次选 A100）实例并提供 SSH 登录端点后，立即运行
   四臂 100-update profile 与一次 strict-PHA probe；记录平台显示的实时单价。
3. 若 profile 有限且预算投影通过，执行 nominal 四臂 1000–2000 updates pilot；
   下载 checkpoint/prediction/log，所有 reference comparison 留在本地。
4. 用 nominal evaluator 和 machine decision 在 2026-08-30 23:59 前选择：
   `MF_PLUS_SAMPLER`、单次 B 或 `MVP_NO_GO_NO_ATTRIBUTABLE_GAIN`。
5. 只有正向 nominal 决策才写 `candidate_freeze.json` 并打开 stress carrier；随后执行
   两 case × 一 seed × selected/strongest/equal-compute-raw。

## 硬停止

| 条件 | 动作 |
|---|---|
| strict PHA >1.8× MF、OOM、非有限或不足规定增益 | 删除 routing，不调 gate |
| 所有 A arms 均无基本 competence | 只允许一次 Route B |
| A 有 competence 但组合无可归因增益 | `MVP_NO_GO_NO_ATTRIBUTABLE_GAIN` |
| B 未击败 sparse raw、data-only 与 medium interpolation | `MVP_NO_GO_NO_PHYSICS_INFORMED_INCREMENT` |
| stress solve 失败 | 该 case 降为 medium descriptive，不冒充确认性证据 |
| sealed case 不支持正向门 | 保留真实 No-Go/条件适用域/Pareto 边界，不回调参 |
| AutoDL 累计或投影将超过人民币 150 元 | 立即停止新的云运行并下载已有产物 |

2026-09-02 23:59 后不增加任何 experiment axis，只完成已冻结运行、评价、图表、
稿件和真实缺陷修复。
