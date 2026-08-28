# 2026-08-29 PHK-V2.2R full-shape CPU preflight

- `status`: `COMPLETE_ALL_FIVE_ARMS_FINITE`
- `evidence_role`: `ENGINEERING_PREFLIGHT_NON_VOTING`
- `case_control`: `FULL`
- `seed`: `17`
- `device`: `cpu`
- `dtype`: `float64`
- `updates_per_arm`: `1`
- `interior_boundary_initial_points`: `512/128/128`
- `reference_fields_read`: `false`

## VERIFIED

| Run ID | Arm | Parameters | Final loss | PDE loss | Gradient norm before clip | Wall seconds | Final-manifest SHA256 |
|---|---|---:|---:|---:|---:|---:|---|
| `20260829-phk-v22r-strong-raw-fullshape-001` | `STRONG_RAW` | 39,939 | 0.4175774771 | 0.1176333339 | 0.5182210062 | 6.0823522 | `7D79A5EF8715D8F69182786D3556D3CC948D9EF4B6CBA0A207BBE4BA2535E0A6` |
| `20260829-phk-v22r-mf-only-fullshape-001` | `MF_ONLY` | 54,915 | 1.0214088136 | 0.7303129431 | 660.4438979242 | 8.4168758 | `B12D94CD7D3BB1D75736D394EF72383A685EA2B618D36BA5EC812659AA9AEF36` |
| `20260829-phk-v22r-sampler-only-fullshape-001` | `SAMPLER_ONLY` | 39,939 | 0.5212579361 | 0.2210256299 | 0.6491544686 | 12.7235405 | `7D1C15760EC0C10E0E3BED14FD55C31BE0C02BA12A32BD7FD60456A2B70D1A67` |
| `20260829-phk-v22r-mf-plus-sampler-fullshape-001` | `MF_PLUS_SAMPLER` | 54,915 | 1.3237987785 | 1.0331856200 | 824.6650210563 | 14.2672602 | `AEA051F7956461D028DDB2508616DF43BEEA05E27255E7AC506D7B28E9EECB80` |
| `20260829-phk-v22r-strict-pha-probe-fullshape-001` | `STRICT_PHA_PROBE` | 62,277 | 1.3212803142 | 1.0295628040 | 813.3538788703 | 2.3914976 | `DD14046A6856679A61C0EAF715DD8F3CFDC3DEC94A6DCA767B199D276105C945` |

五臂均完成一次真实 Adam 更新，强残差、混合边界/初值、二阶自动微分、反向传播、
梯度裁剪、checkpoint、JSONL 日志和最终 manifest 均成功写出；所有最终 loss 与记录的
残差量均为有限值。训练 manifest 明确记录 `training_labels_used=false`、
`anchor_fields_used=false` 和 `reference_fields_read=false`。

## 非投票边界

本记录不能用于方法排序、Route A/B 决策、strict-PHA 1.8× 成本门或论文结果表。
原因是每臂只有一步、网络独立初始化，且多个 CPU 进程同时运行；首次 sampler refresh、
候选池构造、缓存和进程争用使 wall time 不可比较。表中 loss 只用于证明完整批量形状下
数值有限，不能解释为 raw、MF、sampler 或 routing 的效果。

下一项可投票证据必须来自同一 AutoDL GPU、冻结配置下的 100-update profile；随后才可
按预算执行 nominal pilot。本地 smoke 目录保持 Git 忽略，不包含任何 reference field。
