# Live plan：QPOP-TAPF-v1 有界执行

- `phase_id`: `TAPF_BOUNDED_EXECUTION`
- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `authorization_state`: `USER_APPROVED_2026-08-21`
- `execution_authorized`: `true`
- `claim_status`: `PROPOSED_NEW_SUBSTRATE_NO_NUMERICAL_EVIDENCE`

## P0：科学合同

- 三个未知量：`φ`、`T`、`η`。
- 方程：准静态导电、Joule 热/散热、Allen–Cahn 结构动力学和串联电阻外电路。
- Q‑POP 只提供几何、低/中场工作域、自由能稳定极小值差和高低相本构范围；不读取瞬态场拟合 benchmark。
- 独立 SciPy oracle 与 PyTorch PINN 残差不共享离散实现。

## P1：smoke

- seam：`ThermodynamicPhaseFieldContract` 与 `ThermodynamicPhaseFieldCase.solve()`。
- TDD 覆盖零驱动保持、已知均匀态、平衡、artifact 往返、事件诊断和失败落账。
- smoke 上限30分钟；失败只允许一次直接相关工程修正。

## P2：固定事件门

- 静态电热门确定唯一 `V*`，随后冻结 `0.9V*、1.0V*、1.1V*` × `0.8R0、R0、1.2R0` 九个完整案例。
- 至少3/9案例同时满足：两个形成—恢复周期、相区动态范围 `≥0.20`、前沿位移 `≥0.25L`、平衡违规 `≤1%`。
- 失败即 `BENCHMARK_NO_EVENT_OR_NOT_QUALIFIED`，不得搜索新参数。

## P3/P4：条件执行

- P3 strong-raw 固定一个 `4×64 tanh` 三场协议、Adam 3000 + L-BFGS 200、90分钟上限；相区动态须达到 oracle 的70%，结构误差须比最佳时间常数预测降低25%，physics max `≤1.25`。
- P3 失败即关闭路线；通过后 P4 只比较 activity-matched raw、identity、general monotone、dynamics-misaligned 与 KC-eta。
- P4 不通过时形成 `KC_SCIENTIFIC_NO_GO` 或 `INCONCLUSIVE_BUDGET_EXHAUSTED`；不更换 substrate 救援。

## 禁止与归档

- formal、GPU 和付费计算未授权；
- 不重开 R3/R4、七未知量、PHA、双时钟或组合救援；
- 每次真实 run 保留 intent、manifest、index；达到任一门裁决后只更新一次状态。
