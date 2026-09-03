# ADR 0056：激活 PHK-V2.3 LF0 exact-top warm-start attribution campaign

- `status`: `ACCEPTED_ACTIVE`
- `date`: `2026-09-03`
- `phase_id`: `PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE`
- `supersedes_authorization_only`: `PHK_V23_C0_REFERENCE_DISCRETE_STRONGFORM_COMPATIBILITY_AUDIT_EXECUTE_COMPLETE`
- `preserves_scientific_evidence`: `V22R_R0A_R0B_R0C_R1A_R1X_C0`

## 决定

接受用户当前明确的 `EXECUTE`，实施一个最多三条科学 GPU 轨迹的 single-seed nominal development campaign。先在 CPU 上资格化无 E2 内部下界的 exact-top raw potential transform 与唯一 medium low-fidelity source；资格通过后固定执行 A（1200-step exact-top scratch）和 B（800-step medium-only warm-start、200-step anchor 归零、1000-step pure physics），仅在 B 满足预声明 provisional 增量门时执行 C（2000-step exact-top scratch compute control）。

每条 GPU 轨迹必须从 scratch 开始、保持 V100/FP64/seed-17 与原 PDE/本构/几何/参数/evaluator，云端只允许 medium method input，不允许 fine、extra-fine 或 stress。每条运行完成后先回收产物，再立即关闭 AutoDL 并验证；需要下一轨迹时等待用户重启，原 campaign 授权继续有效。

## 方法与数据边界

exact-top potential 采用

\[
V=w(t)\{\zeta+(1-\zeta)h_V\},
\]

其中 `h_V` 是未经 sigmoid、tanh 或 clipping 的原始 ModifiedMLP 输出。medium carrier 是明确披露的低保真 method input；fine/extra-fine 只用于 GPU 关机后的本地 development evaluation。训练仍是普通 Adam summed-loss PINN；不使用 ConFIG、PJGR、新 seed、stress 或其他新增模块。

## 证据与论文边界

本 campaign 最多产生 single-seed nominal solver competence 或 provisional low-fidelity attribution signal。exact-top、warm-start 与 anchor annealing 默认都是 shared solver/backbone，不自动成为 headline innovation。V2.2R、R0A、R0B、R0C、R1a、R1X 与 C0 证据均原样保留。

精确机器合同见 [program](../../configs/phk_v23/program_contract_lf0_exact_top_warmstart.json)、[method](../../configs/phk_v23/method_contract_lf0_exact_top_warmstart.json)、[data](../../configs/phk_v23/data_contract_lf0_medium_only.json) 与 [decision](../../configs/phk_v23/decision_contract_lf0_attribution.json)。
