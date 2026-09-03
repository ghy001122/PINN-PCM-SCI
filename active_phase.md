# 当前阶段

- `phase_id`: `PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE`
- `phase_name`: PHK-V2.3 LF0 exact-top warm-start attribution campaign（执行中）
- `lifecycle_state`: `AWAITING`
- `blocker_id`: `AWAITING_AUTODL_RESTART_CAMPAIGN_AUTHORIZATION_REMAINS_ACTIVE`
- `claim_status`: `C0_OUTPUT_TRANSFORM_INADMISSIBLE_PRESERVED_LF0_CPU_QUALIFIED_NO_GPU_SCIENTIFIC_RESULT`
- `next_research_execution_authorized`: `true`
- `authorization_scope`: `LF0_CPU_GATE_THEN_A_B_AND_CONDITIONAL_C_ONLY`
- `plan_status`: `LF0_CPU_QUALIFIED_AWAITING_AUTODL_RESTART`
- `contract_status`: `LF0_FOUR_CONTRACTS_FROZEN_CPU_QUALIFIED`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_OBJECT_REUSED_WITHOUT_CONTINUUM_ORACLE_CLAIM`
- `method_selection_status`: `NO_CANDIDATE_LF0_ATTRIBUTION_PENDING`
- `candidate_status`: `NOT_FROZEN`
- `reference_status`: `MEDIUM_DECLARED_METHOD_INPUT_FINE_EXTRA_LOCAL_EVAL_ONLY_STRESS_SEALED_UNREAD`
- `compute_status`: `LF0_CPU_QUALIFIED_GPU_ENDPOINT_OFFLINE_RUN_A_NOT_STARTED`
- `diagnostic_outcome`: `LF0_CPU_QUALIFIED`
- `next_recommendation`: `RESTART_AUTODL_AND_EXECUTE_LF0_RUN_A`
- `git_authorization`: `SELECTIVE_LF0_COMMIT_PUSH_MAIN_AUTHORIZED`
- `external_publication_authorization`: `NOT_AUTHORIZED`
- `effective_date`: `2026-09-03`

## 当前授权边界

用户已明确授权 LF0。实现、CPU/FP64 资格门和部署包已经完成；CPU 结果为 `LF0_CPU_QUALIFIED`。当前已知 AutoDL 端点不可达，尚未启动 Run A，也没有形成 LF0 GPU 科学轨迹。实例重启后直接执行 Run A、Run B，并仅在 B 通过预声明 provisional 增量门时执行 Run C。科学 GPU 轨迹最多三条，固定 seed 17，不允许第四条轨迹、stress、PJGR、R2、其他 seed 或投稿。

云端训练仅可读取已声明 medium low-fidelity method input；fine/extra-fine 只可在每条 GPU 运行回收、关机并验证后用于本地 development evaluation。每条运行结束后默认立即关闭 AutoDL；如下一分支仍需 GPU，则等待用户重启并继续同一授权 campaign。

~~~text
PHASE_ID=PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE
BLOCKER_ID=AWAITING_AUTODL_RESTART_CAMPAIGN_AUTHORIZATION_REMAINS_ACTIVE
METHOD_SELECTION_STATUS=NO_CANDIDATE_LF0_ATTRIBUTION_PENDING
NEXT_RESEARCH_EXECUTION_AUTHORIZED=true
CURRENT_STAGE=LF0_CPU_QUALIFIED_AWAITING_AUTODL_RESTART
~~~
