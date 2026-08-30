# 当前阶段

- `phase_id`: `PHK_V22_ONE_WEEK_SPRINT_ACTIVE`
- `phase_name`: PHK-V2.2R v1.1 四臂 Method-MVP 与论文初稿冲刺
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `authorization_scope`: `PHK_V22R_V11_FULL_SPRINT_EXPLICITLY_AUTHORIZED`
- `authorization_package`: `V11_ALIGNMENT_FOUR_ARM_NOMINAL_CONDITIONAL_SEALED_MANUSCRIPT_AUTODL_150CNY_GIT_PUSH`
- `plan_status`: `P0_V11_ALIGNMENT_COMPLETE_P1_NOMINAL_ACTIVE`
- `contract_status`: `V11_FOUR_ARM_CONTRACT_FROZEN_AND_GATE_VALID`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_OBJECT_REUSED_WITHOUT_CONTINUUM_ORACLE_CLAIM`
- `method_selection_status`: `NOT_YET_SELECTED_FOUR_ARM_FALLBACK`
- `claim_status`: `GPU_PROFILE_VERIFIED_NEURAL_METHOD_RESULT_NOT_YET_ESTABLISHED`
- `compute_authorization`: `LOCAL_CPU_AND_AUTODL_UP_TO_150_CNY_AUTHORIZED`
- `formal_or_gpu_authorization`: `BOUNDED_SINGLE_SEED_METHOD_MVP_AUTHORIZED`
- `git_or_external_publication_authorization`: `CURRENT_REPOSITORY_COMMIT_AND_PUSH_AUTHORIZED_SUBMISSION_NOT_AUTHORIZED`
- `next_research_execution_authorized`: `true`
- `current_stage`: `P1_FOUR_ARM_NOMINAL_EXECUTION`
- `nominal_start_gate`: `PASSED_16_FOCUSED_47_COMBINED_DOCUMENT_CONSISTENCY_VALID`
- `route_selection_deadline`: `2026-08-30T23:59:00+08:00`
- `experiment_axis_freeze_deadline`: `2026-09-02T23:59:00+08:00`
- `final_deadline`: `2026-09-04T23:59:00+08:00`
- `effective_date`: `2026-08-30`

## 当前允许

- P0 v1.1 已闭合；P1 每次先实时核验实例、GPU 与重复进程，再在已配置的 AutoDL V100
  32 GB 上以 FP64、seed 17、Band A、
  `512/128/128` 点和 scratch start 执行固定 1000 updates 的
  `STRONG_RAW`、`MF_ONLY`、`SAMPLER_ONLY`、`MF_PLUS_SAMPLER` nominal 比较。
- nominal extra-fine 只在本地用于 development scoring 与预注册裁决；云端保持
  reference-blind。只有 `MF_PLUS_SAMPLER` 通过完整组合增益门才允许晋级。
- 正向 nominal 裁决后冻结 candidate、strongest comparator 与参数匹配/实测时间预算 raw，
  先生成并核验两个 stress case × 三臂的六份 prediction carrier，再一次性本地开封评价。
- 按真实 PASS、bounded/Pareto 或 No-Go 分支完成图表、Results、Discussion、Supplement、
  claim audit、复现材料和英文论文初稿；分支 No-Go 不授权制造正结论，也不取消初稿交付目标。
- AutoDL 累计按量计费不得超过人民币 150 元；每轮付费训练或结果回收完成后直接关机。
- 自动完成本地评价、图表、稿件、验证及当前仓库选择性 commit/push；不得把无关脏工作树
  变更纳入本轮提交。

## 当前禁止

- 运行旧 run card 的 `--mode pilot` 或重跑旧 profile；v1.1 runner 只接受固定 nominal。
- 本轮新增 generic RAR、重跑或调优 strict PHA、启用 Route B/C、KC、SRPG、SIREN、
  continuation、warm start、新物理对象或 extra-extra-fine；generic-RAR 的预声明 P0 截止已过，
  strict PHA 已按冻结增益门退出关键路径。
- 在 candidate freeze 与六份 carrier 身份核验完成前读取任一 stress extra-fine field 或指标；
- 把任何 extra-fine field、mask、event time 或本地 reference comparison 上传云端；
- 开封 sealed case 后修改方法、超参、预算、指标、阈值、seed、checkpoint 或 comparator；
- 隐藏失败 case/seed/metric、制造结果、抹除模块来源或虚报原创性；
- 联系作者、提交期刊、上传投稿系统或披露凭据。

## 当前证据

`VERIFIED`：GPU profile 收口时，AutoDL 实例核验为 Tesla V100-PCIE-32GB；Python 3.11.9、
PyTorch 2.5.1+cu118、CUDA 11.8 与 FP64 probe 有效。当时 GPU 空闲、没有重复训练进程且
`phk_train` tmux 会话存在；这些是时间点快照，不能替代 nominal 启动前的实时复查。

`VERIFIED`：五臂 100-update GPU profile 已完成，五臂均有限。四个 primary arms 的
seconds/update 为 0.5203–0.5673，峰值显存不超过 1.158 GB；按 1.88 元/小时估算的
profile 阶段支出为 0.161945 元，累计估算为 3.661945 元，远低于 150 元硬上限。

`VERIFIED`：strict PHA 相对 MF 的成本比为 1.627636，成本门 1.8× 通过；但 primary
改善为 0，低于预声明 10%，且 profile 时两者 hard guards 均未通过，因此增益门失败并形成
`REMOVE_STRICT_PHA_FROM_CRITICAL_PATH_WITHOUT_GATE_TUNING`。该 100-update 结果只关闭
strict-PHA 路由，不是四臂 nominal 排序或正向方法证据。

`VERIFIED`：两份 stress extra-fine 仍为
`SEALED_UNREAD_PENDING_CANDIDATE_FREEZE`；本轮 profile 只读取 nominal development
reference 评价两份允许的 profile prediction，没有读取任何 stress field 或指标。

`VERIFIED`：用户在 2026-08-30 当前任务中明确解除“等待再次授权”，批准执行完整后续冲刺，
并要求持续推进至论文初稿；当前不再存在用户授权 blocker。实例、tmux、进程与 GPU 的
实时状态必须在每次云端执行前复查，不从旧快照推断。

`VERIFIED`：P0 v1.1 已完成版本化 program/method contracts、四臂-only runner、full-only
decision、两阶段 confirmation/final-freeze schema、cloud run card、manuscript 与 claim
registry 对齐。聚焦测试 16/16、PHK-V2.1+V2.2R 组合回归 47/47 与
`DOCUMENT_CONSISTENCY_VALID` 均通过；旧 `pilot`、1500 updates、Route B、functional
pivot 与 equal-compute freeze 顺序不再是可执行路径。

`UNKNOWN`：四臂 nominal competence、排序、组合可归因增益、candidate freeze、六份 stress
prediction 与 sealed confirmation 均尚未建立，因此任何正面方法结论仍未成立。

~~~text
PHASE_ID=PHK_V22_ONE_WEEK_SPRINT_ACTIVE
BLOCKER_ID=NONE
METHOD_SELECTION_STATUS=NOT_YET_SELECTED_FOUR_ARM_FALLBACK
NEXT_RESEARCH_EXECUTION_AUTHORIZED=true
CURRENT_STAGE=P1_FOUR_ARM_NOMINAL_EXECUTION
~~~
