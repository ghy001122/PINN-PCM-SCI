# Codex 项目上下文

## 当前：训练期电学耦合与事后修复已完成

本轮结果见[paper_v30](paper/paper_v30/README.md)、[当前终局](docs/experiment/2026-09-13-phk-v23-lf11-training-coupling-terminal-closeout.md)和[状态](PROJECT_STATE.md)。实际实例已关闭；[后续计划](docs/plans/NEXT_ACTIONS.md)只作待批提案。旧 P_F 未触发记录及 V29 结论保留。

用户于2026-09-14另行授权本轮重要成果发布及[V30独立复评交付](docs/notes/2026-09-14-lf11-v30-results-cloud-review-handoff.md)。该操作不产生新训练、求解或stress授权。

## 历史 V29：剩余 PDE 固定目标反事实已完成

VERIFIED：D_C/P1/P_kappa 已完成，未通过冻结的剩余 PDE 独立预测增量。当前 [paper_v29](paper/paper_v29/README.md)和[项目状态](PROJECT_STATE.md)保存实际数值与论文；真实实例已回收关闭。用户已另行明确授权本轮成果发布及[独立复评交付](docs/notes/2026-09-13-lf11-v29-results-cloud-review-handoff.md)。下一计划为 PROPOSED_NOT_AUTHORIZED，授权只以 [active_phase](active_phase.md)为准。以下段落保存各轮历史事实及当时授权，不产生继续执行权限。

## 历史 V28：电学消元匹配冲刺已完成

VERIFIED：2026-09-13 的[电学消元完整执行](docs/notes/2026-09-13-lf11-elimination-authorized-sprint.md)已完成。D_E/P_E 均超过同层 B_E，P_E−D_E 未通过冻结 A/B，P_F 未触发。GPU 已回收关机，实际证据见 [PROJECT_STATE.md](PROJECT_STATE.md)、[终局](docs/experiment/2026-09-13-phk-v23-lf11-electrical-elimination-terminal-closeout.md)与 [paper_v28](paper/paper_v28/README.md)。用户已另行授权本轮成果发布与[独立复评交付](docs/notes/2026-09-13-lf11-v28-results-cloud-review-handoff.md)；下一科学执行未授权，见 [active_phase.md](active_phase.md)。以下 V27 和更早段落只保留各自历史身份。

## 历史：同父三臂与条件归一化已完成

VERIFIED：D_I/D_B/P_U 与 R/G/N 六个合法固定终点，新增 6500 Adam updates、1500 次完整评估；五个匹配差分的 A/B 均未通过，D_N 未触发。该轮入口为 [paper_v27](paper/paper_v27/README.md)、[终局](docs/experiment/2026-09-12-phk-v23-lf11-joint-terminal-closeout.md)。CPU 训练及随后授权的[云端独立复评交接](docs/notes/2026-09-12-lf11-v27-results-cloud-review-handoff.md)均为历史。当前授权仅以本页顶部和 active_phase 为准；旧门、旧分支按各自日期保留。


## 历史：paper_v26 V续拟合与接触读出终局

VERIFIED：200次V-only评估接受99步，可见V误差0.8215%→0.5618%，T/phase完全不变。固定参考能量误差49.20%→28.28%；带符号底流积分下降的99.41%来自边界迹项。零训练接触端点强基线能量误差2.187%→0.644%。原0.5%拟合门未达，新D_B/P_U及归一化未运行，不是失败方法。

该段仅记录 paper_v26 轮次。最新事实和授权以本页顶部、PROJECT_STATE.md 与 active_phase.md 为准。

## 项目标识

- 项目：`PINN-PCM-SCI`
- 本地工作区：`E:\Python demo\PINN-PCM-SCI`
- 云端：`https://github.com/ghy001122/PINN-PCM-SCI`
- 研究形态：纯软件闭环
- 最终目标：从 idea 筛选到中科院二区 SCI 定位的完整论文初稿及可复现材料

## 权威链

本文件是路由页，不单独授权科研动作。完整读取顺序为：

`AGENTS.md` → `CODEX_CONTEXT.md` → `docs/README.md` → `docs/governance/PINN_PCM_Norms_2026-08-14.md` → `rules.md` → `active_phase.md` → `PROJECT_STATE.md` → `docs/plans/NEXT_ACTIONS.md`

解释规则：

- `docs/README.md` 负责文档分类、读取触发条件和覆盖关系，不建立新的科学权威。
- 完整研究规范定义项目硬约束、默认偏好和冲突处理。
- `rules.md` 仅提供日常执行摘要，不建立平行权威。
- `active_phase.md` 决定当前允许做什么。
- `PROJECT_STATE.md` 只记录已经核验的状态，不凭计划宣称完成。
- `docs/plans/NEXT_ACTIONS.md` 是唯一 live plan，给出阶段内的下一步入口，不自动扩大授权。

## 授权路由

当前允许和禁止的工作只由 `active_phase.md` 记录。计划、历史会话、内部记忆、已有代码或 `docs/plans/NEXT_ACTIONS.md` 中的候选事项均不自动产生研究授权。

历史 LF11 用户授权的稀疏等观测冲刺已完成，四臂均数值合法，终局为 `LF11_VALID_FOUR_ARM_NO_MATCHED_INCREMENT`。正式更新6000，必要Adam方程×参数头诊断完成，latent条件未触发。后验波形感知插值将同观测电流NRMSE从103.08%降至0.428%，原裁决保持。详细事实、边界与唯一未授权后续见[LF11终局](docs/experiment/2026-09-11-phk-v23-lf11-terminal-closeout.md)及[paper_v24](paper/paper_v24/README.md)。当前无新研究执行授权，stress sealed/unread，实例已关闭。

历史 LF10 已完成并关闭为 `LF10_FEASIBLE_DIRECTION_SCREEN_NEGATIVE_PAPER_STRENGTHENED`。CTRL 与 PROJ 各保留一个身份有效的 25-update safety prefix，但均未完成 200 accepted updates；full path/control 因前提未满足而未运行，不得称失败。方向机制结论为 `NO_EXTENDED_FEASIBLE_PATH_FOUND`，同时建立 `INTERFACE_EFFECT_STREAM_REPLICATED` 与 `PHYSICS_FORGETTING_STREAM_REPLICATED`。没有完整 PINN Pareto、direct `LF_ONLY` 增益或 candidate。其原终局路由和paper_v23保留，不授权重启dense refinement。

LF9 已完成并关闭为 `LF9_NO_SAFE_MIXED_FORM_SCREEN`。ER-S 与 ER-CV 均保留一个身份有效的 25-update safety prefix，并在最小冻结学习率的第二块因 temperature preservation 停滞；无臂完成 200 accepted updates。filtered full path 与 no-filter control 因前提未满足而未运行，不得称失败。其历史证据不被 LF10 改写。

LF8 已完成并关闭为 `LF8_FILTER_STALLED_WITH_VALID_PREFIX`。它保留一个 25-step strong-form safety prefix，但完整路径和 control 未到达；该历史结果不被 LF9 激活改写。

LF7 已完成并关闭。P0-S 是有效的 1,200-update fixed-small-step 负面 arm；P0-F 在接受 25、尝试 150 updates 后发生 post-step rollback identity drift，无合法 endpoint，因此不能比较 filter 增量。终局为 `LF7_MATCHED_SCREEN_INCOMPLETE_IDENTITY_INVALID`，candidate 为 none，后续执行未授权。权威事实见 ADR 0068、terminal closeout 与 `active_phase.md`。

涉及当前研究对象、方法边界或论文措辞时读取 `CONTEXT.md`；需要决策理由时再读取 `docs/adr/`。处理 V2.2R 的方法替换、止损、故事分支或稿后升级时，在当前合同之后读取 `docs/notes/2026-08-29-phk-v22r-recent-research-strategy-integration.md`；该笔记不授权动作。实验事实、参考审查、其他研究笔记和历史归档按 `docs/README.md` 的触发条件读取。

## 状态词汇

- `lifecycle_state`：文件、代码或阶段在工作流中的状态。
- `claim_status`：科学主张获得何种证据支持。
- 二者相互独立；完成实现或交付不等于科学主张成立。

科学表述使用：

- `VERIFIED`：由当前可核验的一手证据直接支持。
- `SUPPORTED_INTERPRETATION`：证据支持但仍含解释步骤。
- `HYPOTHESIS`：待检验假设。
- `UNKNOWN`：现有证据不足。

## 会改变路线、需用户确认的事项

- 新一轮数值研究或正式执行的启动；
- 科学核心、材料/器件对象、物理拓扑或新增 PDE/动力学；
- 原始参数唯一性或反问题主张；
- 正式实验预算、GPU 租用或长时间运行；
- 对研究规范硬约束的任何修改。
# LF5 terminal handoff (2026-09-06)

`PHK_V23_LF5_CYCLE_RESOLVED_TEMPORAL_ZERO_LEVEL_ALIGNMENT_AND_CONDITIONAL_PHYSICS_PILOT_EXECUTE`
retains the CPU outcome `LF5_TZL_ALIGNMENT_NOT_SUPPORTED_CPU`. On 2026-09-06
the user explicitly overrode that stop condition and authorized the otherwise
unchanged DEV-T as `POST_QUALIFICATION_USER_OVERRIDE_EXPLORATORY`. The trajectory
completed 400 updates but failed its temporal-stream identity check before
checkpoint writing; P0 was not run. Recovery/hash verification and shutdown
completed, with TCP closed and SSH refusal. The terminal outcome is
`LF5_NUMERICAL_OR_IDENTITY_INVALID`; no retry or next research is authorized.

# LF6 terminal handoff (2026-09-07)

`PHK_V23_LF6_EVENT_FRONTIER_RANK_BAND_AND_SAFETY_GATED_PHYSICS_PILOT_EXECUTE`
completed from activation `55d552670ba0f727f781d4051b84efde474996f9`, with a
pre-P0 engineering repair at `074eec7f76b4661deda1a622b5343bf992fa2715` that
did not rerun development or change the scientific identity. DEV-U and DEV-R
completed 400 matched updates each; DEV-R was the frozen safety selection, but
neither arm passed strict, so no rank-specific increment was established. P0
completed 1200 pure-physics updates and matched its frozen stream. It reduced
the fixed-blind physics objective by about 98.7% while destroying field and
event preservation, including zero final recall in both cycles. This is a
valid bounded physics-forgetting result, not a numerical failure, PINN Pareto,
direct-LF_ONLY gain, or candidate. Recovery and hash checks completed; the
shutdown proof records TCP closure and SSH refusal before local adjudication,
without asserting an unrecorded exact observation time. Stress remains
sealed/unread and no next research execution is authorized.

# LF7 terminal handoff (2026-09-08)

`PHK_V23_LF7_COMPETENCE_FILTERED_BLOCKWISE_BACKTRACKING_PHYSICS_REFINEMENT_PILOT_EXECUTE`
ran from activation `1dbee129d8b958accc71b97bf2ade3201587b441`. P0-S
completed 1,200 updates and reduced the fixed-blind objective to
`0.6030763369` of DEV-R, but lost the event carrier and field accuracy. P0-F
accepted 25 of 150 attempted updates before a post-step rollback identity error;
it has no valid endpoint and was not retried. Post-run forensics identified
nonempty Adam snapshot tensor aliasing; the terminal-tree fix was not executed
scientifically and does not change the result. Recovery, hash verification,
shutdown and post-shutdown local adjudication completed. No mechanism
attribution, PINN Pareto, candidate or next research authorization exists;
stress remains sealed/unread.

# LF8 terminal handoff (2026-09-08)

`PHK_V23_LF8_IDENTITY_CORRECT_COMPETENCE_FILTER_COMPLETION_AND_SCHEDULE_ATTRIBUTION_EXECUTE`
ran from activation `70b4d30bc36cff0c745cc1eb0fc67f9081cd94f0`. The corrected
filter accepted 25 of 150 attempted updates at learning rate `7.8125e-6`,
strictly reduced fixed-blind `J` to `4.8743140406`, and retained a recoverable
safety-valid endpoint. A second block at the same minimum rate failed temperature
preservation and rolled back exactly, so the path stalled. The 1,200-update path
and conditional schedule control were not reached. Recovery, shutdown and local
adjudication completed; the result establishes neither filter attribution nor a
PINN Pareto/candidate. Strong-form rescue is closed, the mixed weak/control-volume
route requires new authorization, and stress remains sealed/unread.

# LF9 terminal handoff (2026-09-09)

`PHK_V23_LF9_EQUATION_ROUTED_THERMAL_CONTROL_VOLUME_REFINEMENT_EXECUTE` ran from
activation `c38fa80d2fa2ceb0b1bd1fa9faf70440f2a07159` with two pre-step runtime
fixes, ending at deployed base `bc3950a13935a9ded70d4a8b6cc2862deb4a3fd8` and
source identity `LF9-BUNDLE-A8A03C2D2A049F2025793B6B9BA8C7C6412EDF594DBF2042BA3C59F1B9CE5D8B`.
Both valid screens accepted 25 of 150 attempted updates and then stalled on the
second-block temperature gate at `7.8125e-6`. Neither reached the 200-update
selection prerequisite, so full/control were not run. Recovery, shutdown and
post-shutdown local adjudication completed; no mixed-form increment, PINN Pareto,
candidate or next research authorization exists. Stress remains sealed/unread.

# LF10 terminal handoff (2026-09-09)

`PHK_V23_LF10_EVENT_COMPETENCE_FEASIBLE_DIRECTION_AND_HEADLINE_EVIDENCE_REPLICATION_EXECUTE`
ran from activation `f5e05f4dec416df2a3598e433d4edcb9f7ba299c`. CTRL and
PROJ were identity-valid and each retained one 25-update safety prefix, but
neither completed the frozen 200-update screen; full refinement and its control
were therefore not run. Post-shutdown nominal evaluation established
`INTERFACE_EFFECT_STREAM_REPLICATED` and
`PHYSICS_FORGETTING_STREAM_REPLICATED`; direct `LF_ONLY` led the
mean-symmetric-difference predicate in all 375 available role-grid comparisons.
The claim is
`VALID_REPLICATED_INTERFACE_AND_FORGETTING_EVIDENCE_NO_EXTENDED_REFINEMENT_PATH`.
Recovery, shutdown and local adjudication completed; no complete PINN Pareto,
candidate or new research authorization exists, and stress remains sealed/unread.
