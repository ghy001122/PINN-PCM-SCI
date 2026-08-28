# 当前阶段

- `phase_id`: `PHK_V22_ONE_WEEK_SPRINT_ACTIVE`
- `phase_name`: PHK-V2.2R 极速方法抢救与正向证据冲刺
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `AUTODL_INSTANCE_ENDPOINT_PENDING_USER_ACTION`
- `authorization_scope`: `PHK_V22R_EXPLICIT_EXECUTION_AUTHORIZED`
- `authorization_package`: `LOCAL_CPU_SOLVER_PINN_GPU_AUTODL_150CNY_GIT_PUSH_AND_MANUSCRIPT`
- `plan_status`: `ACTIVE_D0_FULLSHAPE_PREFLIGHT_VERIFIED_GPU_PROFILE_PENDING`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_OBJECT_REUSED_WITHOUT_CONTINUUM_ORACLE_CLAIM`
- `method_selection_status`: `NOT_YET_SELECTED_S_FIRST`
- `claim_status`: `IMPLEMENTATION_VERIFIED_NEURAL_METHOD_RESULT_NOT_YET_ESTABLISHED`
- `compute_authorization`: `LOCAL_CPU_AND_AUTODL_UP_TO_150_CNY_AUTHORIZED`
- `formal_or_gpu_authorization`: `BOUNDED_SINGLE_SEED_METHOD_MVP_AUTHORIZED`
- `git_or_external_publication_authorization`: `CURRENT_REPOSITORY_COMMIT_AND_PUSH_AUTHORIZED_SUBMISSION_NOT_AUTHORIZED`
- `next_research_execution_authorized`: `true`
- `current_stage`: `D0_LOCAL_HANDOFF_COMPLETE_AUTODL_PROFILE_PENDING`
- `route_selection_deadline`: `2026-08-30T23:59:00+08:00`
- `experiment_axis_freeze_deadline`: `2026-09-02T23:59:00+08:00`
- `final_deadline`: `2026-09-04T23:59:00+08:00`
- `effective_date`: `2026-08-29`

## 当前允许

- 执行两份已启动的 stress extra-fine 唯一 solve，并在完成后仅写字节 seal；
- 执行四个 primary arms 和一次 100-update strict-PHA GPU probe；
- nominal reference 仅供本地 development scoring、checkpoint 和 A→B 决策；
- 根据冻结裁决写入 `candidate_freeze.json`，随后执行单 seed 三臂 stress matrix；
- 自动完成本地评价、图表、稿件、验证及当前仓库 commit/push；
- AutoDL 按量计费累计不得超过人民币 150 元。

## 当前禁止

- 在 `candidate_freeze.json` 为 `FROZEN` 前读取任一 stress extra-fine field 或指标；
- 把任何 extra-fine field、mask、event time 或本地 reference comparison 上传云端；
- 改写 PHK-V2.1 No-Go，开启 KC、SRPG、Route C、新物理对象或 extra-extra-fine；
- 看过 sealed case 后修改方法、超参、预算、指标、阈值、seed、A/B/R/S 路线；
- 隐藏失败 case/seed/metric、制造结果、抹除模块来源或虚报原创性；
- 直接并入受许可证限制的外部源代码；
- 联系作者、提交期刊、上传投稿系统或披露凭据。

## 当前证据

`VERIFIED`：V2.2R 三场强残差、混合 IC/BC、对角 AD、四臂、strict routing
全导数、采样、训练、prediction/evaluator、sealed gate 与 decision core 已实现，
13 项聚焦测试通过。实现存在与测试通过不是方法效果证据。

`VERIFIED`：两份 stress extra-fine 唯一 solve 已完成并通过声明值—实际值 SHA256
复核。两者仍为 `SEALED_UNREAD_PENDING_CANDIDATE_FREEZE`，尚未打开场或指标；
nominal extra-fine 从未作为训练标签、anchor 或 sampler feature。

`VERIFIED`：五个方法臂已在完整 `512/128/128` 点形状、FP64、seed 17 下各完成一次
真实 CPU 优化更新；loss、残差、梯度、checkpoint 和 manifest 均有限且完整。该并发
一步预检为 `ENGINEERING_PREFLIGHT_NON_VOTING`，不得据此比较臂排序或成本。

`UNKNOWN`：尚无 GPU profile、nominal arm 排序、可归因增益或 sealed confirmation，
因此任何正面方法结论仍未建立。

`UNKNOWN`：AutoDL 实例尚未由用户账号实际创建或提供 SSH endpoint；授权不等于凭据。

~~~text
PHASE_ID=PHK_V22_ONE_WEEK_SPRINT_ACTIVE
BLOCKER_ID=AUTODL_INSTANCE_ENDPOINT_PENDING_USER_ACTION
METHOD_SELECTION_STATUS=NOT_YET_SELECTED_S_FIRST
NEXT_RESEARCH_EXECUTION_AUTHORIZED=true
CURRENT_STAGE=D0_LOCAL_HANDOFF_COMPLETE_AUTODL_PROFILE_PENDING
~~~
