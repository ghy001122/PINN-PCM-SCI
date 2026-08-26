# Live plan：ETPF-KC-v1 机制优先执行

- `phase_id`: `ETPF_KC_BOUNDED_EXECUTION`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `authorization_state`: `USER_APPROVED_2026-08-21`
- `execution_authorized`: `true`
- `claim_status`: `PROPOSED_METHOD_NO_NUMERICAL_EVIDENCE`

## 当前执行链

1. K0：冻结 `m∈[-1,1]`、Q‑POP结构量映射、倾斜双稳态自由能、面内零热流、厚度散热及3 nm缺陷来源。
2. K1：先通过0D四周期可逆动力学和二维制造解，再运行最短 artifact/evaluator smoke。
3. K2/K2Q：用解析 spinodal 暴露确定唯一动态驱动，完成固定3×3事件门及网格/时间资格化。
4. K3：合格后执行单协议 strong-raw；失败只允许一次预注册稀疏锚点诊断并关闭路线。
5. K4：raw通过后比较 activity-matched raw、identity、general monotone、dynamics-misaligned、KC和固定 strong-native raw。

## 止损

- K1失败：`LOCAL_KINETICS_NO_GO`。
- K2失败：`MECHANISM_BENCHMARK_NO_SIGNAL`，不建立第三个 substrate。
- K3失败：`RAW_EVENT_NOT_RESOLVED`，不启动 KC。
- K4失败：`KC_SCIENTIFIC_NO_GO` 或 `INCONCLUSIVE_BUDGET_EXHAUSTED`。
- formal、GPU、外部费用与完整 Q‑POP transfer 未授权。

> 该计划已由 K2Q 的 `ETPF_QUALIFICATION_INVALID` 终局裁决覆盖；保留为历史授权合同。
