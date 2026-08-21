# Live plan：G2 quota-recovery bounded resume

- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `authorization_state`: `G2_QUOTA_RECOVERY_RESUME_APPROVED`
- `resume_authorization`: `USER_EXPLICIT_QUOTA_RECOVERY_RESUME_2026-08-20`
- `resume_authorization_outcome`: `ACTIVE_NOT_YET_CONSUMED`
- `execution_authorized`: `true`
- `execution_started_at`: `2026-08-19`
- `calendar_stop`: `2026-09-17`
- `claim_status`: `NO_NUMERICAL_EVIDENCE`

## G2 environment-preflight stop, 2026-08-19（历史，已被后续授权取代）

Attempts 001 and 002 consumed the original environment-resolution attempt and its sole infrastructure-correction replay. Exact PETSc SOWING bindings to `/usr/bin/gcc-9` and `/usr/bin/g++-9` were implemented and tested but had not then been executed. This historical stop and its evidence remain frozen in `docs/references/qpop_wsl_environment_preflight_2026-08-19.md`; the user has now explicitly authorized one additional attempt.

## 当前唯一动作

先执行不改环境的 WSL admission，确认冻结 spec、Python 3.8 runtime、专用发行版和新 prefix 未被污染。通过后立即为唯一环境 run 登记 intent，并按冻结顺序执行 `resolve → preflight → build → verify`。任一依赖、配置、源码、ABI、编译、测试或 verify 失败都直接收口为新的 `G2_ENVIRONMENT_BLOCKED_FINAL`，不得修复后启动第二次集成 build。只有 verify 通过才执行一次 canonical native smoke；仍不启动 G3 或 PINN。

## 已完成门

- `G1 = SMOKE_PASS`：`20260819T054521Z-smoke-pipeline-fixture-001` 已完成非科学 fixture 的转换、一次模型更新、磁盘产物、跨进程 evaluator、manifest/index 与确定性重评分。该门只有工程含义。

## 后续原目标（当前仍未授权执行）

在一个月日历和有界 CPU 预算内，依次完成工程链 smoke、Q-POP-IMT 资格化、PhysicalContract、raw/identity/KC 物理 smoke、raw-time 瓶颈 pilot 和 KC 2×2 pilot。只有这些门全部通过，才冻结 formal 合同并单独申请精确 formal/GPU 预算。

## 顺序门与准入

1. **G1 pipeline smoke**：fixture → HDF5 → 最小模型更新 → prediction → 独立 evaluator → manifest/index。
2. **G2 Q-POP smoke**：固定一手来源、许可、版本、唯一作者案例和 evaluator；专用 WSL2 环境跑通最短链路。
3. **G3 oracle qualification pilot**：完整作者案例、论文—文档—代码核对、离散/容差/守恒资格化；单一处置 `QUALIFIED/INVALID/BLOCKED`。
4. **G4 physical pipeline smoke**：验证 raw/identity/KC、完整 pullback、分段强形式、无旁路和独立磁盘评分。
5. **G5 raw bottleneck pilot**：只用 development 完整案例；处置 `BOTTLENECK_PRESENT/NO_BOTTLENECK/INCONCLUSIVE_BUDGET_EXHAUSTED/INVALID`。
6. **G6 KC pilot**：执行冻结 2×2 优化协议和必要对照；处置 `KC_PILOT_GO/KC_SCIENTIFIC_NO_GO/INCONCLUSIVE_BUDGET_EXHAUSTED/INVALID`。

任何门未通过均停止，不跳门、不换 oracle、不追加协议、不开放 formal/PHA 数据。

## 必需产物

- 每次成功、失败、中断和重放的 run manifest 与 append-only experiment index；
- artifact、prediction 与 evaluator 的版本化磁盘协议及 golden tests；
- `EvaluatorAudit`、`BenchmarkContract`、`PhysicalContract` 与 `OracleErrorBudget`；
- complete-case split 及 development/KC-formal/PHA-reserve 角色隔离证据；
- G1–G6 各自唯一 gate outcome、失败台账和 claim 边界；
- 若且仅若 G6 通过，形成 G7 formal freeze 与一次预算批准请求。

## 停止条件

- 固定环境无法在批准预算内建立；
- 作者基准不能稳定复现且无单一、可解释的实现原因；
- 网格、时间步或求解器容差不收敛；
- 守恒或方程闭合不成立；
- 目标结构事件在冻结模型中不存在；
- 需要新增高场缺陷、Poole–Frenkel、完整力学或其他未授权物理才能继续。

达到任一停止条件即记录边界并收口，不启动下游门、替代 oracle、开放式修复或预算扩张。smoke/pilot 不产生 formal 结果或正面科学 claim。
