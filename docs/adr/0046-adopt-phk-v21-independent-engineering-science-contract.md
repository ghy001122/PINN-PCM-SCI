# ADR 0046：采纳 PHK‑V2.1 独立工程—科学双阶段合同

- `status`: `ACCEPTED_ACTIVE`
- `date`: `2026-08-27`
- `decision_scope`: `PHK_V21_REPEATABLE_EVENT_LOCAL_EXECUTION`
- `supersedes`: `PHK_V2_COMPLETE_NO_FURTHER_EXECUTION_AUTHORIZATION_SEMANTICS_ONLY`
- `preserves`: `PHK_V2_ORACLE_NO_GO_AND_ALL_PRIOR_EVIDENCE`

## 决定

接受用户提供的《总体审查结论》末尾 GOAL，建立独立的 `PHK_V21_REPEATABLE_EVENT` 路线。PHK‑V2 的对象、12-intent 梯、intent 9 失败、Oracle No-Go、论文与复现包均保持历史原貌；PHK‑V2.1 不重跑或覆盖这些载体。

本路线先执行非投票工程阶段：用最小红色复现诊断控制分支，在预先列出的求解方案中固定一个方案，并在 32 个预生成 coarse engineering cases 与最多 3 个 medium promotions 内选择一个满足两周期形成—恢复事件和全部控制可执行性的候选。工程阶段可以调整求解器与对象参数，但不得形成科学主张。

只有工程候选通过后，才另行写入新对象、split、oracle/floor、baseline replication 与 method contracts，并开始正式科学资格化。正式结果开放后不得移动对象、事件阈值、case、seed、预算或统计 margin。

Oracle、controls、收敛与 neural floor 通过后，依次执行 Sharp/PF 固定身份的指标复现、四臂瓶颈诊断、等预算 PHA×KC 2×2、容量/计算/门控/时钟挑战者与 complete-case formal OOD。正面主张要求两个预声明 co-primary 中至少一个显著优于最强合格 baseline、另一个及关键物理端点非劣；否则按对应冻结 No-Go 收口。

## 理由

PHK‑V2 已经证明旧对象有局域第一周期事件，但 recovery/event 与控制求解未闭合。直接训练 PINN 会让对象、oracle、baseline 与方法同时不可判定。把可调整工程沙盒与不可调整 scientific freeze 分开，可在不篡改旧失败的前提下先消除 qualified-substrate 瓶颈。

## 边界

- 只允许本地项目内研究、开放源码的合法隔离复现、clean-room 实现、CPU 求解、本地可用 GPU、统计图表与本地稿件；
- 不允许付费/云端计算、凭据披露、作者联系、投稿、外部上传或 Git 远程操作；
- Sharp/PF GPL 源码不得并入主库；
- 路线 B 累积编程、SRPG、history encoder 与旧 324-case split 均不进入本合同；
- 任一上游门失败立即停止相应下游，失败 intent、case 与 seed 全部保留。

## 机器合同

- [program contract](../../configs/phk_v21/program_contract.json)
- [engineering contract](../../configs/phk_v21/engineering_contract.json)
- [S0 预注册记录](../governance/2026-08-27-phk-v21-s0-program-and-engineering-preregistration.md)
