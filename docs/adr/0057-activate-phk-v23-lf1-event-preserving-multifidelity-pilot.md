# ADR 0057：激活 PHK-V2.3 LF1 event-preserving multi-fidelity pilot

- `status`: `ACCEPTED_COMPLETE`
- `date`: `2026-09-03`
- `phase_id`: `PHK_V23_LF1_EVENT_PRESERVING_MULTIFIDELITY_PILOT`
- `supersedes_authorization_only`: `PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE_COMPLETE`
- `preserves_scientific_evidence`: `V22R_R0A_R0B_R0C_R1A_R1X_C0_LF0`

## 决定

接受用户当前明确的继续执行指令，实施最多三条 V100/FP64/seed-17 科学轨迹的 single-seed nominal pilot。主路线只含两项耦合改动：可容许的 exact-top potential 表示，以及 event/topology-aware medium distillation 加 persistent replay。它直接检验 LF0 暴露的“data-only 未跨过事件阈值、physics closure 遗忘事件”瓶颈。

potential fraction 固定为

\[
p(h,\zeta)=\frac{\exp h}{\exp h+1-\zeta},\qquad V=w(t)p,
\]

数值实现用按 `h` 正负选择的代数等价比值，既保持 `0<=p<=1` 与顶边精确值，也保留顶边有限法向导数；禁止 output clipping 和新增可训练参数。

Run A 是 1200-step scratch physics category control。Run B 是 1200-step event-balanced medium-only B0，再在 B0 gate 通过后执行 1200-step full physics 加固定 `0.1` event replay。Run C 仅在 B provisional 时从 exact B0 checkpoint、optimizer state 和 data-stream draw 1201 继续到 2400，作为等额 data-only update control。

## 选择理由

LF1 CPU 诊断显示旧八分层 sampler 的事件点仅约占 0.2%，旧 B0 对 direct LF_ONLY 事件支撑的两周期 recall 都为 0；与此同时 event-point phase output Jacobian 中位数约 1.019，并未饱和。新 potential 表示对 medium 的 441,600 个可重构点全部通过可容许性与机器精度重构。因此当前最小可证伪假设是“事件监督被总体 field loss 稀释”，而不是立即更换 optimizer、延长普通 B0 或引入新的 phase latent teacher。

## 证据与论文边界

LF1 最多建立 single-seed nominal event-transfer 与 PINN-specific residual-reduction pilot。它不是多 seed、formal OOD、stress、continuum truth、实验验证或投稿就绪证据。direct LF_ONLY 是披露的 non-PINN medium comparator；只有 B final 通过 frozen competence、相对 LF_ONLY/B0 的 noninferiority、固定 physics ratio，并在条件 C 后仍显示 PINN-specific value，才可称 `PROVISIONAL_SIGNAL`。

精确机器合同见 [program](../../configs/phk_v23/program_contract_lf1_event_preserving_multifidelity.json)、[method](../../configs/phk_v23/method_contract_lf1_event_preserving_multifidelity.json)、[data](../../configs/phk_v23/data_contract_lf1_medium_event_replay.json) 与 [decision](../../configs/phk_v23/decision_contract_lf1_event_preserving.json)。CPU 事实见 [qualification](../experiment/2026-09-03-phk-v23-lf1-cpu-qualification.md)。

## 禁止项

本决定不授权新 seed、phase-latent teacher 后备、PJGR、R2、stress、评价器/物理对象/阈值修改、第四条轨迹、提交推送或投稿。每条 GPU 运行回收后必须关机；任何 terminal outcome 均不自动产生下一科研授权。

## 终局覆盖（2026-09-04）

Run A 与 Run B 已按冻结合同完成、回收、核验和关机。B0 与 B final 均获得两周期 competence，固定 full-physics objective ratio 为 `0.0571112`；但 B final 相对 B0 与 direct `LF_ONLY` 的 phase noninferiority 和 temperature preservation 失败。冻结树终局为 `LF1_DATA_ONLY_VALUE_NO_PINN_GAIN`，唯一下一建议为 `RETAIN_DATA_ONLY_VALUE_AS_NON_PINN_BASELINE_STOP_METHOD_CLAIM`。条件 C 未触发，candidate 为 none，stress sealed/unread；本 ADR 不授权后续科学执行。
