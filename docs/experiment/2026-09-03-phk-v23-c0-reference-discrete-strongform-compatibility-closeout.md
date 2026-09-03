# PHK-V2.3 C0 reference/discrete/strong-form compatibility audit 收口

- `phase_id`: `PHK_V23_C0_REFERENCE_DISCRETE_STRONGFORM_COMPATIBILITY_AUDIT_EXECUTE`
- `run_id`: `20260903T030442Z-phk-v23-c0-compatibility-17dac74`
- `source_commit`: `17dac7448241d100c15cdeae24da90464a2a6ea7`
- `lifecycle_state`: `COMPLETE`
- `diagnostic_outcome`: `C0_OUTPUT_TRANSFORM_INADMISSIBLE`
- `secondary_outcome`: `null`
- `next_recommendation`: `OUTPUT_REPARAMETERIZATION_REQUIRED_BEFORE_LOW_FIDELITY`
- `next_research_execution_authorized`: `false`

## 执行身份

唯一一次正式诊断在本地 CPU/FP64 上完成，wall time 为 `34.0156218 s`，GPU hours 与 cloud cost 均为 0。未构造或加载 neural model/checkpoint，未 forward/backward，未调用 optimizer，未重放 reference solver，也未读取 stress。当前 AutoDL 实例由用户此前例外保留；C0 没有连接、使用或关闭它。

执行前后所有合同、实现、五份 nominal carrier 与 E2 prediction carrier 的 SHA-256 均保持一致；R1X readiness pool 的冻结 tensor SHA-256 为 `FF863ADFDFCA7B6C7B421DCF21F9527E60E7A83053FC26643055C35793755828`。

## Reference readiness

event-competent extra-fine reference 在 native dense 与冻结 2048-point Sobol pool 上均通过原 R1X readiness：

| Window | Dense T activation | Dense cold growth | Dense QJ q95 | Sobol T activation | Sobol cold growth | Sobol QJ q95 |
|---|---:|---:|---:|---:|---:|---:|
| W1 | 0.170646 | 0.107999 | 1.22714 | 0.173077 | 0.121795 | 1.30068 |
| W3 | 0.173957 | 0.113120 | 1.22945 | 0.160256 | 0.121795 | 1.09547 |

原生 FVM edge-dissipation QJ sensitivity 也给出同一通过结论。pool 对 dense cold-growth support 的捕获比为 W1 `1.12774`、W3 `1.07669`；不存在 readiness gate misalignment 或 pool 漏检。cold-state kinetic growth 的实际 ROI 临界温度范围为 `0.502315–0.504220`，中位数 `0.503245`，高于单独的 `Tc=0.45`。

相反，E2 field 在同一 pool 上 W1/W3 cold-growth 均为 0；W1 thermal activation 为 0，W3 为 `0.0576923`。因此 E2 readiness 失败来自其局域场没有越过 cold-growth threshold，不是 deterministic pool 漏掉 reference support。

## Initial/boundary compatibility

解析 `phi0` 在 bottom 的 outward-normal derivative RMS 为 `0.0233291`，最大绝对值约 `0.0583751`；其他三边接近 0。extra-fine native Neumann graph Laplacian 与解析 Laplacian 的差异主要局限于边界/seed：strict-interior RMS `5.24810e-4`，two-layer boundary-strip RMS `0.767238`，bottom-seed RMS `2.18390`，全域符号一致率 `0.998891`。

这是一个真实的初值—bottom no-flux 边界层不相容，但 event region 的 strict-interior 公式保持一致，未达到 dominant mismatch 门。

## Event-aligned mechanism 与 strong-form compatibility

extra-fine reference 的 cycle-1 pre/onset/peak/early-recovery saved times 为 `0.2400/0.2425/0.3500/0.3875`；cycle-2 为 `1.4975/1.5000/1.5850/1.6525`。在 strict interior：

| Stage | dphi RMS | eps2 Lap RMS | barrier RMS | thermal tilt RMS | kinetic RHS RMS | saved-cadence residual RMS |
|---|---:|---:|---:|---:|---:|---:|
| C1 onset | 1.81055 | 0.0908694 | 0.0356438 | 0.411891 | 1.81698 | 0.0341143 |
| C1 peak | 0.136337 | 0.114246 | 0.0526717 | 0.0598036 | 0.129107 | 0.0182339 |
| C2 onset | 1.84707 | 0.0983542 | 0.0325396 | 0.418086 | 1.85379 | 0.0366847 |
| C2 peak | 0.495868 | 0.121573 | 0.0485264 | 0.158659 | 0.470647 | 0.0272960 |

全部八个 event-aligned snapshots 的 native-vs-continuous phase RHS sign agreement 为 `1.0`。saved-cadence strong residual 相对 space/time/replay/native floor 的最大比值为 `1.91408`，低于冻结 compatible 门 `2.0`，远低于 mismatch 门 `10`。因此 strong-form 子裁决为 compatible；现有 carrier 仍不提供 cellwise internal-step residual，故该结论不是 continuum truth 或 exact internal-step residual claim。

## 决定性 output-transform 结果

legacy potential `V=waveform*sigmoid(latent)`、temperature hard envelope 和 phase hard-IC/bounds 在 W1/W3 nominal event support 上均无 violation；所需 phase latent 有限（范围 `-2.88176–1.80972`），大 latent 仅作 conditioning diagnostic。

E2 top-Dirichlet hard lift 强制 `V >= waveform*z_fraction`，但 nominal event support 中：

| Window | Fine violation fraction | Extra-fine violation fraction | Extra-fine q95 relative excess | Extra-fine max shortfall |
|---|---:|---:|---:|---:|
| W1 | 0.705836 | 0.697612 | 0.0430390 | 0.0249487 |
| W3 | 0.672805 | 0.668327 | 0.0402211 | 0.0223934 |

两窗、fine/extra-fine 均同时超过冻结的 `0.001` fraction 与 `0.01` q95 门，threshold-normalized evidence score 为 `4.30390`。E2 prediction 自身严格满足该 transform；问题不是实现漂移，而是该 hard lift 从数学上排除了 fine/extra-fine nominal reference 在 W1/W3 event support 中约 67%–70% 的 potential values。

## 裁决与边界

`VERIFIED`: PRIMARY=`C0_OUTPUT_TRANSFORM_INADMISSIBLE`，SECONDARY=`null`；reference readiness 通过、pool 未漏检、phase strong-form 子裁决 compatible，stress 仍 sealed/unread。

`SUPPORTED_INTERPRETATION`: E2 的负结果受 hard-lift 结构性表示排除混杂，不能作为“即使精确 top BC 也仍无效”的干净科学证据。

`HYPOTHESIS`: 一个既精确满足 top Dirichlet 又不施加 `V>=waveform*z_fraction` 下界的可容许参数化，可能是 low-fidelity-guided route 的必要前置；尚未实现或测试。

`UNKNOWN`: output reparameterization 能否恢复 competence、low-fidelity guidance 的增量、PJGR、其他 seed、stress 与 formal OOD。

C0 只收紧 E2 hard-lift 的解释边界；E1、R1a 与 V2.2R 的独立负面事实继续有效。唯一下一建议为 `OUTPUT_REPARAMETERIZATION_REQUIRED_BEFORE_LOW_FIDELITY`，但当前不授权执行。

## 交付与验证

- [compact scalar artifact](artifacts/20260903T030442Z-phk-v23-c0-compatibility-17dac74.json)
- [run manifest](manifests/20260903T030442Z-phk-v23-c0-compatibility-17dac74.json)
- 20/20 C0 focused tests 通过；受影响 regression suite 135/135 通过。
- experiment ledger、document consistency 与 strict JSON/identity gates 通过。
