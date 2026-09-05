# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料与器件”的纯软件研究项目。目标是形成证据闭合、可复现、达到中科院二区定位的论文初稿；这不是期刊接收承诺，合成数值证据也不等于实验验证。

## 当前状态

- `phase_id`: `PHK_V23_LF4_THRESHOLD_ALIGNED_INTERFACE_BAND_MECHANISM_AND_CONDITIONAL_PHYSICS_PILOT_EXECUTE`
- `lifecycle_state`: `EXECUTING_GPU_PENDING_ACTIVATION_COMMIT`
- `blocker_id`: `NONE`
- `claim_status`: `LF4_CPU_GEOMETRY_SUPPORT_ONLY_GPU_MECHANISM_UNTESTED`
- `next_research_execution_authorized`: `true`

LF4 已通过零更新 CPU-G：冻结的四个 interface-band pool 均非空，LF3-T0 的错分主要集中在 reference interface boundary，且 matched M0/G/C 与条件 P0 的数据流、随机数账本和固定 physics pool 身份均已闭合。该证据只支持边界几何与可执行性，不是 GPU 机制增量或 PINN 候选证据。

当前仅授权本具名 LF4：一条 matched DEV-M→条件 DEV-C 机制轨迹，以及仅在 DEV-C 通过后执行的 label-free P0。不得自动扩展为额外臂、多 seed、OOD、stress、PJGR/R2 或投稿；LF3 与更早终局保持原证据边界。

## 当前入口

- 授权边界：[active_phase.md](active_phase.md)
- 已核验状态：[PROJECT_STATE.md](PROJECT_STATE.md)
- 唯一 live plan：[docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)
- 当前激活决定：[ADR 0061](docs/adr/0061-activate-phk-v23-lf4-interface-band-pilot.md)
- LF4 CPU 资格：[CPU-G qualification](docs/experiment/2026-09-05-phk-v23-lf4-cpu-qualification.md)
- 上一终局：[LF3 terminal closeout](docs/experiment/2026-09-05-phk-v23-lf3-terminal-closeout.md)
- 当前论文初稿：[paper/paper_v23](paper/paper_v23/README.md)
- 上一关闭决定：[ADR 0060](docs/adr/0060-close-phk-v23-lf3-carrier-not-established.md)
- LF2 终局：[LF2 terminal closeout](docs/experiment/2026-09-04-phk-v23-lf2-terminal-closeout.md)
- LF1 终局：[LF1 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf1-terminal-closeout.md)
- LF0 结果：[LF0 terminal closeout](docs/experiment/2026-09-03-phk-v23-lf0-terminal-closeout.md)
- C0 结果：[compatibility closeout](docs/experiment/2026-09-03-phk-v23-c0-reference-discrete-strongform-compatibility-closeout.md)
- 上一论文包：[paper/paper_v22r](paper/paper_v22r/README.md)
- 文档地图：[docs/README.md](docs/README.md)
- 当前研究口径：[CONTEXT.md](CONTEXT.md)
