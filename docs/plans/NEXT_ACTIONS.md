# PLAN-PHK-V2.3-LF1：admissible event-preserving multi-fidelity pilot（已完成）

- `phase_id`: `PHK_V23_LF1_EVENT_PRESERVING_MULTIFIDELITY_PILOT`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE_TERMINAL`
- `claim_status`: `V22R_R0_R1A_R1X_C0_LF0_EVIDENCE_PRESERVED_LF1_DATA_ONLY_VALUE_NO_PINN_GAIN`
- `next_research_execution_authorized`: `false`
- `authorization_state`: `CONSUMED_AND_CLOSED`
- `plan_status`: `LF1_TERMINAL_COMPLETE`
- `current_stage`: `LF1_DATA_ONLY_VALUE_NO_PINN_GAIN_TERMINAL`
- `supersedes`: `PLAN_PHK_V23_LF0_TERMINAL_COMPLETE`
- `preserves`: `V22R_R0A_R0B_R0C_R1A_R1X_C0_LF0_EVIDENCE`
- `contracts`: `configs/phk_v23/{program_contract_lf1_event_preserving_multifidelity,method_contract_lf1_event_preserving_multifidelity,data_contract_lf1_medium_event_replay,decision_contract_lf1_event_preserving}.json`
- `decision`: `docs/adr/0057-activate-phk-v23-lf1-event-preserving-multifidelity-pilot.md`
- `next_recommendation`: `RETAIN_DATA_ONLY_VALUE_AS_NON_PINN_BASELINE_STOP_METHOD_CLAIM`

## 终局

LF1 已按冻结顺序执行 Run A 与 Run B，共使用 `2/3` 条 scientific GPU trajectories。Run A 是有效但无事件的 range-preserving scratch control。Run B0 通过 data-transfer gate并获得两周期 competence；B final 在 persistent replay 下保留 competence且把固定 physics objective 降到 B0 的 `0.0571112`。

B final 没有通过相对 B0 与 direct `LF_ONLY` 的 phase noninferiority 和 temperature preservation，因此机器结果为：

```text
LF1_DATA_ONLY_VALUE_NO_PINN_GAIN
→ RETAIN_DATA_ONLY_VALUE_AS_NON_PINN_BASELINE_STOP_METHOD_CLAIM
```

条件 C 仅在 provisional gate 全部通过时运行，本次没有触发。两条 GPU 运行均已完整回收、哈希核验和关机；本地 nominal evaluation 在关机验证后完成；stress 始终 sealed/unread。

## 对论文的可用证据

| 证据 | 可写结论 | 不可写结论 |
|---|---|---|
| LF0 + LF1 CPU diagnosis | 普通 field distillation 稀释稀疏事件监督 | 一般性 low-fidelity 失败 |
| Run A | 新 potential 表示有效但不独自恢复事件 | 表示本身构成方法增益 |
| Run B0 | event-balanced data-only 蒸馏可转移两周期 competence | PINN-specific value |
| Run B final | persistent replay 避免冷态坍塌并降低 physics residual | 相对强 data-only baseline 的冻结增量 |
| C 未运行 | provisional gate 未达到，compute control 不可达 | C 失败或 C 支持任一方向 |

这些材料可进入导师初稿的 failure-analysis、solver-recovery 与强 data-only baseline 章节，但不能形成正向 headline PINN 方法主张。中科院二区投稿所需的 multi-seed、formal OOD/stress、强基线统计与核心方法增量均未建立。

## 停止与后续边界

当前没有授权下一研究阶段。不得把未使用的第三条额度用于 C、救援运行或新方法，不得启动 phase-latent teacher、PJGR、R2、新 seed、stress、formal OOD 或投稿。后续若要继续，应先由用户选择是否建立一个直接面向 accuracy–physics Pareto 的新最小合同；本完成态不自动产生该授权。

终局证据见 [LF1 terminal closeout](../experiment/2026-09-03-phk-v23-lf1-terminal-closeout.md) 与 [compact artifact](../experiment/artifacts/20260903T155306Z-phk-v23-lf1-terminal-dc091be.json)。
