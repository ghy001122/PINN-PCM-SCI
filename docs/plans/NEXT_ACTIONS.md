# PLAN-PHK-V2.2R-V1.1：四臂 Method-MVP 与论文初稿冲刺

- `phase_id`: `PHK_V22_ONE_WEEK_SPRINT_ACTIVE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `claim_status`: `GPU_PROFILE_VERIFIED_NEURAL_METHOD_RESULT_NOT_YET_ESTABLISHED`
- `authorization_state`: `PHK_V22R_V11_FULL_SPRINT_EXPLICITLY_AUTHORIZED`
- `plan_status`: `P0_COMPLETE_P1_NOMINAL_ACTIVE`
- `current_stage`: `P1_FOUR_ARM_NOMINAL_EXECUTION`
- `next_research_execution_authorized`: `true`
- `supersedes`: `PLAN_PHK_V22R_V1_FORWARD_EXECUTION_AFTER_PROFILE`
- `preserves`: `PHK_V21_ORACLE_NO_GO_AND_ALL_PRIOR_EVIDENCE`
- `program_contract`: `configs/phk_v22r/program_contract.json`
- `method_contract`: `configs/phk_v22r/method_contract.json`
- `decision_record`: `docs/adr/0048-activate-phk-v22r-v11-four-arm-sprint-after-gpu-profile.md`
- `profile_record`: `docs/experiment/2026-08-30-phk-v22r-gpu-profile-closeout.md`
- `route_selection_deadline`: `2026-08-30T23:59:00+08:00`
- `experiment_axis_freeze_deadline`: `2026-09-02T23:59:00+08:00`
- `final_deadline`: `2026-09-04T23:59:00+08:00`

## 已完成

1. V2.2R v1 工程基础、两份 stress reference byte seal 与五臂 full-shape CPU preflight
   已完成；stress references 仍未读。
2. AutoDL V100 32 GB、Python 3.11.9、CUDA 11.8、PyTorch 2.5.1+cu118 与 FP64 已验证。
3. 五臂 100-update GPU profile 已完成且有限；四个 primary arms 的 nominal 成本投影在
   150 元硬上限内。
4. strict PHA 成本门通过但开发增益门失败，已按预声明规则退出关键路径且禁止调 gate。
5. generic-RAR P0 截止已过，进入四臂 fallback；本周不再增加 generic RAR 或 Route B/C。
6. 用户已明确解除等待状态并一次性批准 v1.1 对齐、后续有界训练、条件性 sealed 评价与
   论文初稿连续执行。
7. P0 v1.1 已完成机器合同、runner、decision、两阶段 freeze、run card、manuscript 与
   registry 对齐；聚焦测试 16/16、组合回归 47/47 和文档一致性门禁均通过。

## 现在执行

1. **P1 nominal 四臂**：立即在当前 V100 上执行 `STRONG_RAW`、`MF_ONLY`、
   `SAMPLER_ONLY`、`MF_PLUS_SAMPLER`；FP64、Band A、`512/128/128`、Adam、1000
   updates。无 early stop、warm start、L-BFGS、续训或事后救援。
2. **P2 本地裁决**：下载 checkpoint/prediction/log/manifest，保持云端 reference-blind；
   只在本地对 nominal development reference 评分。只有 `MF_PLUS_SAMPLER` 同时通过
   basic competence、相对 strongest component、相对 strong raw 与 non-inferiority 门才晋级；
   否则形成预声明 No-Go 并转入真实论文分支。
3. **P3 候选冻结与确认载体**：正向 nominal 后冻结 selected、strongest comparator 和
   `PARAMETER-MATCHED, MEASURED-TIME-BUDGET RAW CONTROL`；生成两个 stress case ×
   三臂的六份 scratch prediction。六份 carrier 全部核验后才写 candidate freeze。
4. **P4 一次性开封与初稿**：本地一次性开封两个 stress references，禁止反馈训练；按
   `SEALED_ACCURACY_PASS`、`SEALED_BOUNDED_NARROW_INTERFACE_PASS`、
   `SEALED_PARETO_PASS`、`SEALED_NO_POSITIVE_STORY` 或 hard-blocked 分支完成五张主图、
   Results、Discussion、Supplement、复现材料与英文初稿。
5. 每轮付费训练/结果回收结束后直接关机；AutoDL 累计或投影达到 150 元前必须停止新运行。

## 硬停止

| 条件 | 动作 |
|---|---|
| P0 合同、runner、测试或文档门禁失败 | 不运行 nominal；只修复直接阻塞项 |
| 任一 nominal arm 非有限、OOM 或执行身份不完整 | 记录该失败；不得换 seed、延长 updates 或隐藏 |
| strong raw 不具基本 competence | full 不得晋级；按冻结 No-Go 收口 |
| full 不满足相对 strongest component/raw 的组合增益或保持门 | `ROUTE_A_NO_ATTRIBUTABLE_COMBINATION_GAIN`；不运行 sealed |
| 六份 stress carrier 未全部形成并核验 | 不写 candidate freeze，不开封 reference |
| sealed case 不支持预声明正向门 | 保留真实 No-Go、bounded regime 或 Pareto 边界，不回调参 |
| AutoDL 累计或投影将超过人民币 150 元 | 立即停止新的云运行，下载已有产物并关机 |

2026-09-02 23:59 后不增加 experiment axis；只完成已冻结运行、评价、图表、稿件与真实
缺陷修复。任何 deadline amendment 都必须版本化，不能静默顺延。
