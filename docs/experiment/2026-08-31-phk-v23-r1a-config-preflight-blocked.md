# PHK-V2.3 R1a ConFIG preflight blocker

- `task_id`: `PHK_V23_R1A_CONFIG_COMPETENCE_RECOVERY`
- `record_role`: `INFRASTRUCTURE_PREFLIGHT_NOT_SCIENTIFIC_RUN`
- `status`: `R1A_BUDGET_OR_INFRASTRUCTURE_BLOCKED`
- `scientific_gpu_runs_consumed`: `0`
- `scientific_claim_change`: `NONE`
- `date`: `2026-08-31`

## 已完成

- 冻结 R1a program/method contracts、ADR 0052、唯一 live plan 和 shared-solver attribution。
- 在原 trainer 中只增加一个 gradient-combiner seam；默认 `None` 路径继续执行原 `total.backward()`，ConFIG 逻辑位于单独 adapter。
- 8 项 R1a focused tests、R0B/R0C regressions、8 项 legacy-safe tests、experiment ledger 与 `DOCUMENT_CONSISTENCY_VALID` 均通过。
- 部署 bundle `R1A-CONFIG-BUNDLE-D37FE6C0C044109EAF5EA583680D69A94D6F9830C687F0C330C120C4B3928244` 对 16 个运行依赖文件闭合哈希。

## 阻塞事实

使用此前核验的 endpoint `region-46.seetacloud.com:28355` 和既有专用 SSH key 做了两次只读连接探针，两次均在 SSH banner 阶段返回 `Connection refused`。因此无法核验当前 V100 身份、空闲状态、远端 bundle、tmux 或实时页面价格，也未启动训练、未创建远端输出、未使用 GPU、未产生增量云费用。

## 恢复条件

用户启动 AutoDL 实例并提供当前 SSH endpoint（host/port）和实例页面显示的实时单价。恢复时先重新核验本地 HEAD/dirty whitelist、V100/空闲状态、远端环境、source hashes、预算和 reference-blind 边界；全部通过后才消费唯一 R1a run。不得以 CPU 训练、旧价格推定、第二 endpoint 猜测或其他 GPU 替代。
