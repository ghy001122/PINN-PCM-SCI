# ADR 0060：以 carrier recall 未达标关闭 PHK-V2.3 LF3

- `status`: `ACCEPTED_COMPLETE`
- `date`: `2026-09-05`
- `phase_id`: `PHK_V23_LF3_MEASURE_DECOUPLED_STARTUP_SCALED_PHASE_LATENT_CARRIER_PILOT_EXECUTE`
- `activation_commit`: `97a5b74cf79332115397d07c83b400c942859fb4`
- `preserves_scientific_evidence`: `V22R_R0A_R0B_R0C_R1A_R1X_C0_LF0_LF1_LF2`

## 决定

以 `LF3_CARRIER_NOT_ESTABLISHED` 关闭 LF3。唯一 T0 轨迹恢复了合法、局域、
时刻准确的两周期事件，并通过 precision、active-mass、locality、recovery、
potential 与连续场误差门；但 cycle-1/2 hard recall 为
`0.805842/0.768603<0.90`，所以 conjunctive carrier gate 失败。P0 按冻结合同
执行 0 步并记为 `NOT_TRIGGERED`，不是方法失败；candidate 为 none。

`unique_next=STOP_LATENT_CARRIER_ROUTE_RETAIN_NEGATIVE_ADVISOR_DRAFT`。
完成 `paper/paper_v23` failure-analysis + bounded solver-recovery 导师初稿，
不继续在同一 latent carrier 路线上进行结果导向的延长、调权或额外 GPU 救援。

## 理由

LF3 相对 LF1 的 5–6 倍过宽事件和 LF2 的零事件冷态形成实质恢复：主导拓扑
误差已变为高 precision 下的 boundary support 漏检。但它同时远差于 direct
`LF_ONLY` 强基线，而且 P0 未运行，不能把组合级 data-only near-pass 写成
phase-logit 单因素增益、合格 carrier 或 PINN-specific gain。

本地 fixed-physics 报告曾沿用 LF2 role 键；一次 local-only 身份修复把实际
LF3-T0 checkpoint 标为 `LF3_T0_LATENT_CARRIER` 并把 ratio 键改为
`P0_to_T0`。pool、checkpoint、scalar、reference metrics 与机器裁决均未改变，
也未新增 GPU 科学轨迹。

## 后续边界

当前 `next_research_execution_authorized=false`。第二轨迹、新 seed、matched
output-phase ablation、OOD、stress、PJGR/R2、kinetic teacher、物理对象或
frozen evaluator 修改与投稿均需新的明确授权。两份 stress references 保持
`TWO_STRESS_REFERENCES_SEALED_UNREAD`。终局证据见
[LF3 closeout](../experiment/2026-09-05-phk-v23-lf3-terminal-closeout.md)，
论文边界见 [paper_v23](../../paper/paper_v23/README.md)。
