# 当前阶段

- `phase_id`: `PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE`
- `phase_name`: PHK-V2.3 R1X 有界 clean-coupling campaign（pure-scratch terminal stop）
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED`
- `claim_status`: `V22R_TERMINAL_NO_GO_AND_R1A_NO_COMPETENCE_PRESERVED_R1X_PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED`
- `next_research_execution_authorized`: `false`
- `authorization_scope`: `NONE_NEW_CONTRACT_REQUIRED_FOR_LOW_FIDELITY`
- `plan_status`: `PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED`
- `contract_status`: `PHK_V23_R1X_CAMPAIGN_CONSUMED_COMPLETE`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_OBJECT_REUSED_WITHOUT_CONTINUUM_ORACLE_CLAIM`
- `method_selection_status`: `NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE`
- `candidate_status`: `NOT_FROZEN`
- `reference_status`: `CLOUD_REFERENCE_BLIND_LOCAL_NOMINAL_AFTER_COMPLETE_RECOVERY_STRESS_SEALED_UNREAD`
- `compute_status`: `AUTODL_RETAINED_RUNNING_BY_EXPLICIT_USER_OVERRIDE_GPU_IDLE_NO_R1X_PROCESS`
- `diagnostic_outcome`: `PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED`
- `git_authorization`: `SELECTIVE_R1X_COMMIT_PUSH_MAIN_AUTHORIZED`
- `external_publication_authorization`: `NOT_AUTHORIZED`
- `effective_date`: `2026-09-03`

## 当前授权边界

R1X campaign 已按冻结机器树执行两条 non-voting explorations。E1 因两窗 readiness 失败路由到 E2 top-Dirichlet hard lift；E2 虽精确满足 top potential boundary 并提高电热驱动，但五次 readiness 仍失败，且始终没有 material phase signal。冻结树因此禁止 E3 和 confirmation，并终止 pure-scratch competence recovery。

当前没有新科研执行授权。后续若进入 low-fidelity-guided route，必须新建合同并由用户明确 `EXECUTE`；也可保留当前 bounded-negative package。实例因用户对本条运行的明确例外而保持开机，但这不构成科研授权。未来默认仍为 GPU 使用结束后及时关机，除非用户再次明确覆盖。

## 明确禁止

- 重跑 E1/E2、使用第三条 exploration 槽绕过冻结分支、执行 E3 或 confirmation；
- low-fidelity、PJGR、R2、其他 seed、延长训练或新增 trick，除非新合同与新授权生效；
- stress 读取/预测、benchmark/PDE/reference/evaluator 改写；
- 投稿、对外披露或把 non-voting development evidence 写成方法增益。

## 证据边界

- `VERIFIED`: V2.2R terminal No-Go、R0A、R0B、R0C 与 R1a `R1A_CONFIG_RAW_NO_COMPETENCE` 保持不变。
- `VERIFIED`: E2 在 V100/FP64/seed 17 上从 scratch 完成 300 warm-up updates；top BC RMS 为 0，但 W1 thermal activation 与 W1/W3 cold kinetic-growth 在五次检查中均为 0，未进入 ramp/full closure。
- `VERIFIED`: E2 `phase_max=0.0295885`、activity=0；本地 frozen evaluator 判定两周期各自失败 event/ROI peak/recovery；E3 与 confirmation 均不可达。
- `VERIFIED`: E2 产物已完整回收并核对远端/本地 hash；云端未读 nominal/stress。用户明确要求本次不关机，当前 SSH 可达、GPU 0%/0 MiB、无 R1X 训练进程。
- `SUPPORTED_INTERPRETATION`: hard top-Dirichlet conditioning 改善了全局与局部电热量，但不足以建立同时覆盖 W1/W3 ROI 的 cold kinetic drive。
- `HYPOTHESIS`: low-fidelity state/drive guidance 可能是离开低相态兼容轨迹所需的下一类机制；尚未执行。
- `UNKNOWN`: low-fidelity、PJGR、其他 seed、stress、formal OOD 和 R2 结果。

R1X 最终结果见 [E2/campaign closeout](docs/experiment/2026-09-03-phk-v23-r1x-e2-pure-scratch-stop-closeout.md)，E1 结果见 [E1 closeout](docs/experiment/2026-09-03-phk-v23-r1x-e1-et-not-ready-closeout.md)，恢复决定见 [ADR 0054](docs/adr/0054-resume-r1x-after-verified-engineering-repair.md)，原科学合同见 [ADR 0053](docs/adr/0053-activate-phk-v23-r1x-bounded-clean-coupling-campaign.md)，唯一 live plan 见 [NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)。

~~~text
PHASE_ID=PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE
BLOCKER_ID=PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED
METHOD_SELECTION_STATUS=NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE
NEXT_RESEARCH_EXECUTION_AUTHORIZED=false
CURRENT_STAGE=PURE_SCRATCH_COMPETENCE_RECOVERY_FAILED
~~~
