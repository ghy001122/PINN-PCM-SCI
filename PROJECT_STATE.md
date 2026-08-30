# 项目状态

更新时间：2026-08-30

- `phase_id`: `PHK_V23_R0A_CPU_DIAGNOSTICS_AND_CONTRACT`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `V22R_TERMINAL_NO_GO_PRESERVED_R0A_INCONCLUSIVE_NO_METHOD_EVIDENCE`
- `authorization_scope`: `R0A_CLOSEOUT_REVIEW_AND_SELECTIVE_GIT_PUSH_ONLY`
- `candidate_status`: `NOT_FROZEN`
- `object_status`: `PHK_V21_FIXED_DISCRETIZATION_BENCHMARK_REUSED`
- `reference_status`: `NOMINAL_LOCAL_DIAGNOSTIC_COMPLETE_TWO_STRESS_UNREAD_SEALED`
- `implementation_status`: `R0A_READ_ONLY_DIAGNOSTIC_EXECUTED_ONCE_AND_CLOSED`
- `method_selection_status`: `NO_CANDIDATE_ALL_FOUR_ARMS_INELIGIBLE`
- `compute_status`: `R0A_CPU_9_321135_SECONDS_GPU_ZERO_CLOUD_COST_ZERO`
- `contract_status`: `PHK_V23_R0A_EXECUTED_ONCE_NO_NEXT_STAGE_AUTHORIZED`
- `paper_status`: `ENGLISH_ADVISOR_DRAFT_FIVE_FIGURE_PACKAGE_VALID`
- `cloud_budget_cny_hard_cap`: `150`
- `cloud_estimated_cumulative_spend_cny`: `4.81005806532574`
- `diagnostic_outcome`: `R0A_INCONCLUSIVE`
- `root_cause_status`: `PRIMARY_NOT_IDENTIFIED`
- `next_recommendation`: `R0B_FIRST_SWITCH_175_NOT_AUTHORIZED`
- `next_research_execution_authorized`: `false`

## VERIFIED

- run `20260830T-phk-v23-r0a-cpu-001` 在本地 CPU/FP64 完成一次 read-only R0A，wall time `9.321135 s`；GPU 与新增云费用均为 0，stress 未读。
- 参数与缓冲 combined SHA-256 前后均为 `E972D7724BF436520F13792CB857300D5C38E5713D9AEC6C322CA3D7B4CF47BF`；state tensors、模型模式与 persistent gradients 均未改变。RNG 检查只证明 post-checkpoint-load-to-exit 不变；entry-to-exit 因 legacy model 构造消耗 CPU RNG 而不成立，收口修复后未重跑。
- sampled prediction 最大 T 为 `0.100121`、最大 phase 为 `0.027510`，ROI positive kinetic-growth fraction 全为 0；reference/prediction Joule q95 比为 `1.94795`。
- reference-T phase teacher 与 reference-constitutive-QJ thermal teacher 的 residual improvement ratios 分别为 `0.758656` 与 `0.880520`，均未达到冻结 `10×` 门。机器裁决为 `R0A_INCONCLUSIVE`。
- final phase head 的 `THERMAL_PDE↔PHASE_PDE` 与 `PHASE_PDE↔PHASE_BC` cosine 分别为 `-0.997743` 与 `-0.934733`；这是终局静态冲突测量，不等于训练期 primary root cause。
- P0 v1.1 固定了四臂、FP64、seed 17、Band A、scratch、`512/128/128`、Adam 1000 updates 与 final checkpoint only。聚焦测试 16/16、PHK-V2.1+V2.2R 组合回归 47/47 和文档一致性门禁在 nominal 启动前通过。
- run `20260830T112225-phk-v22r-v11-nominal-69109cd` 在 Tesla V100-PCIE-32GB 上完成四臂训练。云端保持 reference-blind，四个 checkpoint、prediction、training log、start/final manifest、ledger、environment 与 summary 均回收到本地。
- 本地回收目录共 26 个文件、860,924,050 bytes。`summary.json` 与四份 prediction 的 SHA-256 全部与云端值一致后，实例已关闭；随后 SSH 探测返回 connection refused。
- nominal 阶段估算支出 1.1481133733 元；累计估算 4.8100580653 元，低于 150 元硬上限。该数字按展示单价 1.88 元/小时估算，不冒充平台账单。
- 四臂训练均有限且 PDE loss 下降，但四臂相场最大值均只约 0.029993，整个时间轴的 `phase >= 0.5` 活动比例为 0。参考两周期 ROI 峰值为 0.068698 与 0.061983。
- 四臂各自均触发 cycle 1/2 的 event missing、ROI peak below minimum 与 recovery failure。决策机返回 `MVP_NO_GO_NO_BASIC_COMPETENCE`，原因是 `ALL_FOUR_ARMS_FAILED_FROZEN_COMPETENCE_GUARDS`。
- `selected_arm=null`、`strongest_comparator=null`、`confirmation_training_authorized=false`、`stress_unseal_authorized=false` 与 `terminal_no_rescue=true`。两份 stress references 继续密封未读。
- `paper/paper_v22r/` 已形成完整英文导师评阅初稿、五张主图、表格、Supplement、复现说明、claim audit、研究决策记录和 reviewer-risk self-check；专用门禁输出 `PHK_V22R_TERMINAL_PACKAGE_VALID`。

## SUPPORTED_INTERPRETATION

- 四臂共同落入近初始相态解；在本固定合同下，PDE loss 下降没有转化为事件 competence。
- 四臂相同的 primary 0.00515 是“预测活动集合为空”时参考稀疏事件的平均支撑，并非高精度证据。
- 因所有 arms 都不 eligible，本轮不能比较 combined gain，也不能把 sampler-only 的部分较低 scalar error 写成组件收益。

## UNKNOWN

- 低 electrothermal state、potential boundary mismatch、phase output Jacobian、final gradient conflict、causal-window 切换或优化预算中哪一项主导失败。
- 新 seed、更长预算、continuation、其他优化器或新架构能否恢复事件；这些没有执行，也不能从当前 No-Go 推断。
- 两个 stress case、formal OOD、多 seed 稳健性、连续体精度、材料校准和实验有效性。

## 交付入口

- 终局运行记录：[2026-08-30 nominal terminal closeout](docs/experiment/2026-08-30-phk-v22r-v11-nominal-terminal-closeout.md)
- R0A 收口：[2026-08-30 PHK-V2.3 R0A CPU diagnostics](docs/experiment/2026-08-30-phk-v23-r0a-cpu-diagnostics-closeout.md)
- 运行 manifest：[20260830T112225... manifest](docs/experiment/manifests/20260830T112225-phk-v22r-v11-nominal-69109cd.json)
- 英文稿与复现包：[paper/paper_v22r](paper/paper_v22r/README.md)
- 当前授权：[active_phase.md](active_phase.md)
- 唯一 live plan：[docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)
- 历史 P0：[alignment closeout](docs/experiment/2026-08-30-phk-v22r-v11-alignment-closeout.md)
- 历史 profile：[GPU profile closeout](docs/experiment/2026-08-30-phk-v22r-gpu-profile-closeout.md)

PHK-V2.1、PHK-V2、V1 与更早 No-Go 均保持原样，不被本次有效 PINN 负面结果改写。
