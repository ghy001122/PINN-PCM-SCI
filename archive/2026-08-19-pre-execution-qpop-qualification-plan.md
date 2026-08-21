# 已归档计划：Q-POP 复现与物理合同资格化

- `archived_at`: `2026-08-19`
- `lifecycle_state`: `SUPERSEDED`
- `superseded_by`: `docs/plans/NEXT_ACTIONS.md`
- `scientific_claim_status`: `NO_NUMERICAL_EVIDENCE`

本文件保存用户批准正式执行计划之前的 live plan。它只记录当时等待批准的入口，不再决定当前授权或行动。

## 当时状态

- `authorization_state`: `WAITING_FOR_USER_APPROVAL`
- `execution_authorized`: `false`

## 当时唯一动作

等待用户批准一份有界的 Q-POP-IMT 复现与物理合同执行计划。在批准前，只允许审阅和完善该计划，不下载、安装或运行求解器。

## 当时目标与范围

确认一个固定 Q-POP-IMT 版本能否在受支持环境中复现指定二维 VO₂ 案例，并形成经论文、模型文档与可执行代码核对的 `PhysicalContract`。获准后固定 commit、环境和唯一案例，复现作者基准，执行网格、时间步、非线性容差与守恒检查，并形成 `QUALIFIED`、`INVALID` 或 `BLOCKED` 的单一处置。

## 当时停止条件

- 固定环境无法在批准预算内建立；
- 作者基准不能稳定复现且无单一、可解释的实现原因；
- 网格、时间步或求解器容差不收敛；
- 守恒或方程闭合不成立；
- 目标结构事件在冻结模型中不存在；
- 需要新增高场缺陷、Poole–Frenkel、完整力学或其他未授权物理才能继续。

达到任一停止条件即收口，不启动 PINN、替代 oracle、开放式修复或预算扩张。
