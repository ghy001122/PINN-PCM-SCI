# 项目状态

更新时间：2026-08-30

- `phase_id`: `PHK_V22_ONE_WEEK_SPRINT_ACTIVE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `claim_status`: `GPU_PROFILE_VERIFIED_NEURAL_METHOD_RESULT_NOT_YET_ESTABLISHED`
- `authorization_scope`: `PHK_V22R_V11_FULL_SPRINT_EXPLICITLY_AUTHORIZED`
- `candidate_status`: `NOT_FROZEN`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_BENCHMARK_REUSED`
- `reference_status`: `THREE_EXTRA_FINE_REFERENCES_AVAILABLE_TWO_STRESS_UNREAD_SEALED`
- `implementation_status`: `V11_FOUR_ARM_EXECUTION_STACK_VERIFIED`
- `method_selection_status`: `NOT_YET_SELECTED_FOUR_ARM_FALLBACK`
- `compute_status`: `AUTODL_V100_PROFILE_COMPLETE_NOMINAL_NOT_RUN`
- `contract_status`: `V11_FOUR_ARM_FROZEN_NOMINAL_GATE_PASSED`
- `cloud_budget_cny_hard_cap`: `150`
- `cloud_estimated_cumulative_spend_cny_at_profile_closeout`: `3.6619446915`
- `next_research_execution_authorized`: `true`
- `final_deadline`: `2026-09-04T23:59:00+08:00`

## VERIFIED

- 用户已在 2026-08-30 当前任务中明确批准 PHK-V2.2R 完整后续冲刺，授权从 v1.1
  对齐开始，按冻结门连续推进 nominal、条件性 sealed confirmation、图表、复现材料和论文
  初稿；不需要 routine 再批准。AutoDL 150 元硬上限及当前仓库选择性 commit/push 授权保持，
  作者联系、凭据披露和投稿系统操作仍未授权。
- GPU profile 收口时的 AutoDL 环境为 `Tesla V100-PCIE-32GB`，Python 3.11.9、
  PyTorch 2.5.1+cu118、CUDA 11.8，且 FP64 probe 有效；当时 GPU 空闲且无训练进程。
  这是历史时间点快照，不表示此刻实例、tmux 或 GPU 的实时状态。
- run `20260830T0122-phk-v22r-d1-gpu-profile-cf372713` 已完成五臂 100-update
  profile。五臂均 `COMPLETE` 且有限；四个 primary arms 的速度为
  0.5203–0.5673 s/update，峰值显存为 0.302–1.158 GB。
- profile 单价为 1.88 元/小时；阶段估算支出 0.1619446910 元，含既有 3.5 元后累计估算
  3.6619446915 元。该账本是平台单价下的运行估算，不冒充最终账单。
- strict PHA 成本比 1.627636 小于 1.8× 上限，但相对 `MF_PLUS_SAMPLER` 的 primary
  改善为 0，低于冻结的 10% 要求；本地裁决为
  `STRICT_PHA_PRIMARY_GAIN_GATE_FAILED`，动作是
  `REMOVE_STRICT_PHA_FROM_CRITICAL_PATH_WITHOUT_GATE_TUNING`。
- 预声明 generic-RAR P0 截止已过且未形成稳定实现，因此 v1.1 使用四臂 fallback；
  strict PHA、generic RAR、Route B/C 都不进入本周后续实验轴。
- 三场 strong-form PINN、四个 primary arms、训练器、prediction carrier、本地 evaluator、
  sealed gate 与 decision core 的既有实现基础保持；V2.1 与全部历史 No-Go 原样有效。
- nominal extra-fine 仍是 local development-only reference；两份 stress extra-fine 的字节
  seal 保持有效，且仍未读取 field 或 metric。
- P0 v1.1 已将 program/method contracts、runner、decision machine、两阶段 freeze、cloud
  run card、manuscript 与 claim registry 对齐。聚焦测试 16/16、PHK-V2.1+V2.2R 组合
  回归 47/47 及 `DOCUMENT_CONSISTENCY_VALID` 已通过；nominal 入口只接受固定四臂、1000
  updates、scratch start、seed 17、Band A、final checkpoint only。

## IN PROGRESS

- P1 四臂 nominal 已激活但尚无结果入库；实际启动前先复查实例、GPU、tmux 与重复进程，
  并显式设置有效的 `OMP_NUM_THREADS`，再按冻结 run card 执行。

## UNKNOWN

- 四臂 nominal 的基本 competence、排序和 `MF_PLUS_SAMPLER` 可归因增益尚未测量。
- candidate 能否冻结、两个 stress case 的六份 prediction 是否形成、开封后的事件身份与
  confirmation 分支均未知；不得从 profile 通过、carrier 存在或 GPU 就绪推断正面结果。

## 交付路由

- 当前稿件：`paper/paper_v22r/`
- 当前执行入口：`active_phase.md`
- 唯一 live plan：`docs/plans/NEXT_ACTIONS.md`
- 当前决策：`docs/adr/0048-activate-phk-v22r-v11-four-arm-sprint-after-gpu-profile.md`
- profile 事实：`docs/experiment/2026-08-30-phk-v22r-gpu-profile-closeout.md`
- P0 v1.1 对齐事实：`docs/experiment/2026-08-30-phk-v22r-v11-alignment-closeout.md`
- 跨工具协作与数据路由：
  `docs/governance/2026-08-30-sprint-collaboration-and-data-routing.md`
- 当前 v1.1 机器合同：`configs/phk_v22r/program_contract.json` 与
  `configs/phk_v22r/method_contract.json`
- 历史 V2.1：`paper/paper_v21/`
