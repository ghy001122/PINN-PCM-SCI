# PHK-V2.3 LF4 interface-band mechanism pilot 终局收口

- `phase_id`: `PHK_V23_LF4_THRESHOLD_ALIGNED_INTERFACE_BAND_MECHANISM_AND_CONDITIONAL_PHYSICS_PILOT_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `machine_outcome`: `LF4_NO_DEVELOPMENT_ENTRY`
- `mechanism_outcome`: `BOUNDARY_EXPOSURE_SUPPORTED`
- `scientific_gpu_arms`: `3/3 development; 0/1 conditional P0`
- `optimizer_updates`: `1200 development + 0 P0`
- `candidate`: `none`
- `next_research_execution_authorized`: `false`
- `unique_next`: `P0_NOT_RUN_THREE_ARM_MECHANISM_NEGATIVE_UPDATE_PAPER`
- `stress_reference_status`: `TWO_STRESS_REFERENCES_SEALED_UNREAD`

## 终局裁决

`VERIFIED`：三条 FP64/V100/seed-17 development arms 均从 exact LF3-T0
weights 完成固定 400 updates，V/T 参数 bitwise 不变，全部 finite、phase-range
valid、potential-admissible，并产生局域双周期事件。

| arm | recall C1/C2 | timing error C1/C2 | phase weighted MSE | entry |
|---|---:|---:|---:|---|
| DEV-G global-extra MSE | 0.840206 / 0.819419 | 0.013867 / 0.006160 | 0.00130870 | FAIL: timing×2 |
| DEV-M interface-band MSE | 0.937285 / 0.909256 | 0.010533 / 0.005000 | 0.00120963 | FAIL: cycle-1 timing |
| DEV-C threshold BCE | 0.941581 / 0.975499 | 0.001900 / 0.002500 | 0.0296673 | FAIL: phase error |

没有臂通过完整 conjunctive entry；selected carrier 为 none。P0 为
`NOT_RUN_NO_DEVELOPMENT_ENTRY`，不是 P0 失败。机器终局为：

```text
LF4_NO_DEVELOPMENT_ENTRY
→ P0_NOT_RUN
→ candidate = none
→ P0_NOT_RUN_THREE_ARM_MECHANISM_NEGATIVE_UPDATE_PAPER
```

## 实质机制进展

CPU-G 先确认 LF3-T0 的 481 FN 中 455 个、227 FP 中 199 个位于 teacher
four-neighbour boundary distance 0。GPU matched screen 随后给出：

- `Rmin(G)=0.819419`，`Rmin(M)=0.909256`，`M−G=+0.0898367`；
- DEV-M 保持 precision `0.9092/0.9462`、mass `1.0309/0.9610`、recovery
  `1/1`、locality、timing non-worsening、V/T quality，并超过冻结 `0.03`；
- 因此 `BOUNDARY_EXPOSURE_SUPPORTED=true`：在本 single-seed nominal 对象中，
  teacher-interface exposure 相对 equal-budget global extras 显著提高 minimum
  recall。该结果不主张 interface sampling 原创或全局有效。

DEV-C 的 `C−M=+0.0323249`，且两周期 timing 均通过；但 cycle-2 recovery
从 `1.0` 降至 `0.767857`，phase weighted MSE 是 LF3-T0 的 `15.82` 倍、
DEV-M 的 `24.53` 倍。完整质量保存条款失败，故
`threshold_aligned_supported=false`。两侧 softplus 仅按标准 BCE-with-logits
归因，不称新损失。

## 执行、回收与关机

- start HEAD：`7df29ef730ad60156dfae5abd4a3ef41fa69a109`；
- activation HEAD：`5dbde1d210b6f2ff15d0f341ee316e59b49a1074`；
- cloud source：`LF4-BUNDLE-EF532BCCF7FAC4482BEBD56A49DFAFE2D5F2FD4B2043540BD4414B6668CA644F`；
- activation-source archive SHA-256：`780BAC482BC1DD538FBAB33180EF15F2270A684908C1D7168320D20C045AFC2E`；
- run：`outputs/runs/20260905T102817Z-phk-v23-lf4-interface-band-5dbde1d`；
- run summary SHA-256：`692833FA52787AE9B204A64AC84D11E9AA15352459498EF3A2D066F7CB313ED2`；
- 6 个 summary-bound artifacts、summary 与两份 launcher logs 均通过远端/
  本地 SHA-256 对账；development batch ledger 为 1200 行；
- 首次 launcher 在 runner import 与 optimizer 构造前因 base interpreter 缺少
  `h5py` 退出；无 output root、GPU process 或 optimizer update。既有项目环境
  通过 `torch+h5py+CUDA+V100` 隔离回归和完整 zero-step preflight 后，以不变
  科学身份执行一次合法 engineering retry；
- 有效运行 wall time `75.9031 s`；结束后 LF4 process=0、GPU compute process=0、
  memory used=0 MiB；
- 回收对账后执行关机；TCP `28355` closed 且 SSH 返回 `Connection refused`。

## 关机后本地评价、强基线与论文

只有关机验证后，本地 nominal evaluator 才读取 fine/extra-fine、direct
`LF_ONLY` 与 frozen evaluator。canonical adjudication：

```text
outputs/runs/20260905T102817Z-phk-v23-lf4-local-adjudication-5dbde1d/adjudication.json
SHA256=4301BEF71B49B17EA0EA164314A0FF5F9CBF11367C2EA92AF0509D75F0D94289
```

裁决仍为 `LF4_NO_DEVELOPMENT_ENTRY`。由于没有 selected prediction，LF4 不产生
对 direct `LF_ONLY` 的新 accuracy candidate 比较；LF3-T0 相对 direct baseline
的既有显著差距保持。不存在 physics ratio、PINN Pareto、strong-baseline gain、
SOTA 或 paper-positive claim。

[paper_v23](../../paper/paper_v23/README.md) 已更新为八图导师稿：新增 boundary
geometry、matched DEV-G/M/C ablation 与 physics-Pareto stopping figure，并将
中央叙事提升为“boundary exposure 有界正向机制证据 + threshold loss/entry/P0
负面边界”。prior-art closure 检查 12 个一手来源，未发现完整功能碰撞，但明确
interface sampling、boundary supervision、implicit-surface two-sided labels 与
BCE primitive 均有先例。

证据见[terminal artifact](artifacts/20260905T082728Z-phk-v23-lf4-terminal.json)
与[terminal manifest](manifests/20260905T082728Z-phk-v23-lf4-terminal.json)。LF4
完成不自动授权任何新科研动作；stress 始终 sealed/unread。
