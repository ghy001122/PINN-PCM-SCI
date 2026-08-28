# 项目状态

更新时间：2026-08-29

- `phase_id`: `PHK_V22_ONE_WEEK_SPRINT_ACTIVE`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `AUTODL_INSTANCE_ENDPOINT_PENDING_USER_ACTION`
- `claim_status`: `IMPLEMENTATION_VERIFIED_NEURAL_METHOD_RESULT_NOT_YET_ESTABLISHED`
- `authorization_scope`: `PHK_V22R_EXPLICIT_EXECUTION_AUTHORIZED`
- `candidate_status`: `NOT_FROZEN`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_BENCHMARK_REUSED`
- `reference_status`: `THREE_EXTRA_FINE_REFERENCES_AVAILABLE_TWO_STRESS_UNREAD_SEALED`
- `implementation_status`: `THREE_FIELD_PINN_SAMPLER_PREDICTION_EVALUATOR_AND_DECISION_CORE_VERIFIED`
- `method_selection_status`: `NOT_YET_SELECTED_S_FIRST`
- `compute_status`: `LOCAL_CPU_FULLSHAPE_PREFLIGHT_COMPLETE_CUDA_UNAVAILABLE_AUTODL_AUTHORIZED_NOT_PROVISIONED`
- `cloud_budget_cny_hard_cap`: `150`
- `next_research_execution_authorized`: `true`
- `final_deadline`: `2026-09-04T23:59:00+08:00`

## VERIFIED

- 当前用户命令及 ADR 0047 已明确授权本轮代码、配置、两份 stress
  extra-fine、PINN/GPU、AutoDL 不超过人民币 150 元、论文和当前仓库
  commit/push；作者联系和投稿系统操作未授权。
- `configs/phk_v22r/program_contract.json` 固定研究边界；
  `configs/phk_v22r/method_contract.json` 在任何 nominal 神经结果前固定网络、
  强残差、损失、采样、因果窗口、公平性和增益门。
- 已实现 `v/theta/phi` 三场强形式 PINN、所需对角二阶 AD、完整混合 IC/BC、
  strong-raw/MF-only/sampler-only/MF+sampler 与一次 strict-PHA probe。
- 已实现 reference-blind 训练、四窗口等额 replay、0.35/0.25/0.25/0.15
  Sobol/残差/phase/Joule 采样、checkpoint、prediction carrier、本地 evaluator、
  stress fail-closed gate、nominal machine adjudicator 和 cloud budget ledger。
- `tests/test_phk_v22r_pinn.py` 当前 13/13 通过；覆盖物理导数、全臂有限反传、
  strict gate 全导数、采样语义、边界、真实一步优化、reference-blind prediction、
  stress 封存和候选裁决；V2.1 与 V2.2R 扩展组合回归共 44/44 通过。
- paper_v22r 已预写 Abstract、Introduction、Physical Model、Method、Evaluation、
  conditional Results、Limitations、References 和 claim-to-artifact registry。
- PHK-V2.1 的 `PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN` 与所有旧证据保持不变。
- nominal extra-fine 仍仅为 development-only reference，SHA256 为
  `0CE36347433983DB3631C9CD92E3FBFDAEF5A692D3370736071696135FFB73CE`，
  从未进入 V2.2R 训练或 sampler。
- narrow-interface extra-fine 已完成唯一 solve：154,751,976 bytes，SHA256
  `C2C01F31E23869DB1E54A5938F5DFCFC6491EA6583D49B8635C56678F09BD0CD`；
  wide-heater extra-fine 已完成唯一 solve：155,426,149 bytes，SHA256
  `1A72CD23B10E6E048BC72936A43A41F165A9B37758E012CD296574D50D27422A`。
  两者独立字节复核通过并保持 `SEALED_UNREAD_PENDING_CANDIDATE_FREEZE`；没有
  读取场或计算事件/误差指标。
- 五个冻结方法臂均在 FP64、seed 17、完整 `512/128/128` 点形状下完成一次真实 CPU
  优化更新，所有 loss、残差、梯度、checkpoint 与 manifest 均有限且完整；该并发
  一步运行仅为非投票工程预检，不能用于方法排序或 strict-PHA 成本判断。

## IN PROGRESS

- 本地可执行工作已交接到 GPU 边界；在用户账号创建 AutoDL 实例并提供 SSH 端点及
  页面实时单价前，GPU profile 和 nominal pilot 不能启动。

## UNKNOWN

- 四个 physics-only arms 的 nominal competence、排序和可归因增益尚未测量。
- strict PHA 的实际 GPU 成本与 100-update 增益尚未测量。
- 候选能否冻结、stress fields 开封后的事件身份和 confirmation 是否通过均未知；
  不得从成功生成 carrier 推断正面方法结果。
- Route B 尚未触发；只有所有 route-A arms 都缺乏基本 competence 才允许实现并执行。

## 交付路由

- 当前稿件：`paper/paper_v22r/`
- 当前执行入口：`active_phase.md`
- 唯一 live plan：`docs/plans/NEXT_ACTIONS.md`
- 机器合同：`configs/phk_v22r/program_contract.json` 与
  `configs/phk_v22r/method_contract.json`
- 历史 V2.1：`paper/paper_v21/`
