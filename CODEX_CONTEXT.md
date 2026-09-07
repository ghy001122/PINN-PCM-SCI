# Codex 项目上下文

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

当前具名 LF7 已明确授权并通过 CPU 零步资格。它从 exact LF6 DEV-R 分别执行固定小步长 P0-S 与 fresh competence-filtered backtracking P0-F，以区分“较小步长已足够”和“function-space filter/rollback load-bearing”。两臂共用冻结的 1,200-step physics stream；P0-F 的 medium 只参加 accept/reject，因此不得称 fully label-free。GPU 结果尚不存在。执行边界见 LF7 四合同、ADR 0067、CPU qualification 与 `active_phase.md`；额外 rescue、seed、sparse/OOD/stress、weak-form/control-volume、PJGR/R2 或投稿不在授权内。

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
