# PHK-V2.3 LF5 temporal zero-level pilot 终局收口

- `phase_id`: `PHK_V23_LF5_CYCLE_RESOLVED_TEMPORAL_ZERO_LEVEL_ALIGNMENT_AND_CONDITIONAL_PHYSICS_PILOT_EXECUTE`
- `lifecycle_state`: `COMPLETE`
- `CPU_T_outcome`: `LF5_TZL_ALIGNMENT_NOT_SUPPORTED_CPU`
- `GPU_evidence_role`: `POST_QUALIFICATION_USER_OVERRIDE_EXPLORATORY`
- `machine_outcome`: `LF5_NUMERICAL_OR_IDENTITY_INVALID`
- `scientific_gpu_trajectories`: `1`
- `optimizer_updates`: `400 DEV-T + 0 P0`
- `candidate`: `none`
- `next_research_execution_authorized`: `false`
- `unique_next`: `STOP_NO_SCIENTIFIC_RETRY`
- `stress_reference_status`: `TWO_STRESS_REFERENCES_SEALED_UNREAD`

## 终局裁决

CPU-T 的机制前提反证不被用户覆盖改写。用户随后授权完全不变的 400-step
DEV-T 作探索性轨迹。正式部署通过零步 source/input/V100/preflight 后完成全部
400 updates，但 terminal identity check 发现 temporal stream 从 step 1 即与
CPU 冻结 ledger 不同：

| stream | frozen SHA | observed SHA | result |
|---|---|---|---|
| base draws 1201–1600 | `3870D0C1...62F692E4A` | same | PASS |
| spatial band 400 | `4DB1728C...C69DEC4` | same | PASS |
| temporal edge 400 | `8FD79D99...C9B3BD9` | `48A0C6B4...AAFB127` | FAIL; first batch |

该 failure 在 400 次 optimizer update 后发生，故消耗唯一科学轨迹且禁止
retry/resume。异常先于 checkpoint 与 prediction 写出；P0 为
`NOT_RUN_HIGHER_PRIORITY_IDENTITY_FAILURE`，不是失败。机器终局为：

```text
LF5_NUMERICAL_OR_IDENTITY_INVALID
→ no valid DEV-T checkpoint/prediction
→ P0 NOT_RUN
→ candidate = none
→ STOP_NO_SCIENTIFIC_RETRY
```

## 非投票方向性 telemetry

step-400 raw telemetry 不能参与 carrier gate，但提供如下有界方向：

| metric | cycle 1 | cycle 2 |
|---|---:|---:|
| recall | 0.917526 | 0.917423 |
| precision | 0.909710 | 0.945744 |
| active-mass ratio | 1.008591 | 0.970054 |
| event-time absolute error | 0.009400 | 0.001250 |
| recovery | 1.0 | 1.0 |

phase maximum 为 `0.987161`，phase weighted MSE 为 `0.000783624`，finite、
phase range、potential maximum principle 与 locality 均通过。若仅忽略 identity，
冻结 carrier gate 仍会因 cycle-1 timing `0.0094>0.005` 失败。因此本结果至多支持
`SUPPORTED_INTERPRETATION`：额外 temporal-edge supervision 可能补齐 support
recall，却没有修复 cycle-1 aggregate timing。不得称 trained carrier、TZL 单因素
增量或 PINN result。

## 工程执行与来源身份

- start HEAD：`d86ddf1d206c611087a1b5284acda69efdfda9fa`；
- activation HEAD：`fe629d6b120c1caaa891692a92062b6fe5ce8178`；
- deployment binding HEAD：`ea8ddcad74337db7f65d74f6f1ec71577747e52a`；
- dependency closure HEAD：`4bec07a8afd3cddcbc0bbf6f5d9557df31e2d12b`；
- executed source HEAD：`eba0ffec8c20a23064488ad42adbaf4e2acc424f`；
- executed source identity：`LF5-BUNDLE-07D66D6DC077C4988A7F14CADCE4DAAD028F0810901403A9F74143AA273A0664`；
- executed archive SHA：`DC084782AC0EBEC8A9755FE0971192170C3A28CA9C635E14AA0D5E5097E51F4E`；
- executed manifest SHA：`909A6656E8A650649A1F8ED5B6552647EC27989E79DD6BBC0EC0F3D8AEDF3C68`。

两次合法首步前 engineering attempts 均为 0 update：首次 bundle 缺失
`tests/test_phk_v21_benchmark.py`，经真实隔离 physics-load regression 修复；第二次
源码通过但没有按合同路径单独上传 medium/checkpoint，经 path+size+SHA preflight
regression 修复。第三次才进入科学轨迹。三次均未改变 loss、initialization、
stream seed/call order、optimizer、budget 或 gate。

## 回收、关机与本地边界

有效轨迹目录：
`outputs/runs/20260905T172640Z-phk-v23-lf5-temporal-eba0ffe`。

| raw file | size | SHA-256 |
|---|---:|---|
| `manifest-start.json` | 1687 | `812C077A...D4BCC` |
| `dev-t-batch-hashes.jsonl` | 107892 | `8E555FC2...DB5BE` |
| `dev-t-telemetry.jsonl` | 38081 | `CE9361A3...C6016` |

远端/本地 size 与 SHA 全部一致。关机前 LF5 process=0、GPU compute process=0、
memory/utilization=`0/0`。随后执行 shutdown；TCP 28355 closed，SSH 明确返回
`Connection refused`。

由于无合法 checkpoint/prediction，本地 frozen evaluator 没有可评对象，故未读
fine、extra-fine、direct `LF_ONLY`。local adjudication 只记录高优先级 identity
failure，不重新解释既有强基线。P0 physics ratio、PINN Pareto 与 candidate signal
均未定义。

## 论文与证据边界

[paper_v23](../../paper/paper_v23/README.md) 已更新 CPU premise rejection、用户
覆盖身份、三次部署边界、identity-invalid trajectory、非投票 telemetry 与 P0
NOT_RUN panel。当前最大诚实贡献仍是 LF4 的 bounded
`BOUNDARY_EXPOSURE_SUPPORTED`，外加 LF5 对 DEV-C→TZL 前提的有效反证和一条
“support 改善不等于 timing 改善”的方向性观察。

禁止写：LF5 carrier/TZL/PINN 成功、优于 direct `LF_ONLY`、P0 失败、strong
baseline gain、SOTA、multi-seed/OOD/stress、continuum/material/experimental
validity 或 submission readiness。

证据见 [terminal artifact](artifacts/20260905T150045Z-phk-v23-lf5-terminal.json)
与 [terminal manifest](manifests/20260905T150045Z-phk-v23-lf5-terminal.json)。
