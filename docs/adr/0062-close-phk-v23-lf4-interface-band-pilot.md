# ADR 0062：以 boundary-exposure 机制证据和无 development entry 关闭 LF4

- `status`: `ACCEPTED_COMPLETE`
- `date`: `2026-09-05`
- `phase_id`: `PHK_V23_LF4_THRESHOLD_ALIGNED_INTERFACE_BAND_MECHANISM_AND_CONDITIONAL_PHYSICS_PILOT_EXECUTE`
- `activation_commit`: `5dbde1d210b6f2ff15d0f341ee316e59b49a1074`
- `machine_outcome`: `LF4_NO_DEVELOPMENT_ENTRY`
- `candidate`: `none`

## 决定

以 `LF4_NO_DEVELOPMENT_ENTRY` 关闭 LF4。三条 matched phase-only arms 均从
exact LF3-T0 权重执行 400 updates。DEV-M 相对 DEV-G 的最差周期 recall
提高 `0.0898367`，超过冻结 `0.03` 且通过质量保存条款，故接受对象特异的
`BOUNDARY_EXPOSURE_SUPPORTED`。DEV-C 相对 DEV-M 虽提高 recall 并修复 timing，
却使 phase weighted MSE 升至 `0.0296673` 且降低 cycle-2 recovery，因此拒绝
threshold-aligned BCE 的 load-bearing 机制 claim。

DEV-G、DEV-M、DEV-C 分别因双周期 timing、cycle-1 timing、phase error 未通过
完整 entry。无 selected carrier，P0 按合同为 `NOT_RUN`，不是 P0 失败；没有
PINN-specific Pareto 或 candidate。唯一后继为：

```text
P0_NOT_RUN_THREE_ARM_MECHANISM_NEGATIVE_UPDATE_PAPER
```

## 证据边界

允许写：在冻结 single-seed nominal benchmark 中，teacher-interface exposure
相对 equal-budget global-extra supervision 提升两周期 minimum recall。必须引用
既有 phase-field PINN interface sampling 与 boundary supervision 先例。

禁止写：threshold BCE 优越、LF4 carrier 成功、P0/PINN 增量、优于 direct
`LF_ONLY`、SOTA、multi-seed/OOD/stress、continuum/material/experimental validity。
两侧 softplus 是标准 BCE-with-logits，不是新损失。

## 后续边界

`next_research_execution_authorized=false`。任何 DEV-M/DEV-C 混合、loss 权重、
新 seed、full-from-LF1-B0 confirmation、OOD、stress、PJGR/R2 或投稿都需要新的
明确授权。两份 stress references 保持 `TWO_STRESS_REFERENCES_SEALED_UNREAD`。
