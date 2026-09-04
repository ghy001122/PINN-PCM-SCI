# PHK-V2.3 LF1 Run A interim closeout

- `phase_id`: `PHK_V23_LF1_EVENT_PRESERVING_MULTIFIDELITY_PILOT`
- `lifecycle_state`: `ACTIVE`
- `machine_outcome`: `LF1_A_VALID_RUN_B_REQUIRED`
- `unique_next`: `RUN_B_AFTER_AUTODL_RESTART`
- `next_research_execution_authorized`: `true`
- `candidate`: `none`
- `scientific_gpu_runs`: `1/3`
- `stress_status`: `TWO_STRESS_REFERENCES_SEALED_UNREAD`

## VERIFIED

- 两次启动工程故障都发生在模型/optimizer step 之前，共执行 0 个更新且不消耗科学轨迹。第一处是部署白名单漏掉 PHK-V2.1 物理加载器会哈希校验的 `tests/test_phk_v21_benchmark.py`；补齐 runtime closure 后，4 个 cloud focused tests 与隔离解包 `load_case_physics()` 回归通过。第二处是 tmux 键盘模拟把 `C-m` 作为字面 CLI 参数；改为直接 tmux 命令执行后才进入 step 1。科学合同、seed、数据、步数和物理对象均未改变。
- 有效 Run A 在 Tesla V100-PCIE-32GB、FP64、seed 17 上恰好执行 1200 个 pure-physics updates；最终 `pde_loss=0.0052725901`，`total_loss=0.0090127998`，完整运行及 prediction wall time 为 722.434 s，估算费用 0.377271 CNY。
- range-preserving exact-top potential guard 在四个窗口与全局均 PASS，最大越界和 violation fraction 都为 0；云端未读取 medium labels、fine/extra-fine evaluator 或 stress。
- 远端与本地 summary 及其 8 个绑定产物的大小和 SHA-256 全部一致；physics batch ledger 恰有 1200 条。完整回收后实例已执行关机，随后 SSH 返回 `Connection refused`。
- 关机后本地 nominal evaluation 显示 Run A 有限、phase range PASS，但 `phase_max=0.0299932`、`phase>=0.5` 占比为 0，两个周期事件均缺失；LF_ONLY medium direct comparator 仍通过两周期事件，事件时刻为 0.2381 和 1.49545。
- 冻结 decision tree 唯一映射为 `LF1_A_VALID_RUN_B_REQUIRED`，不是终局，也不触发 Run C。

## SUPPORTED_INTERPRETATION

新 potential 表示修复了 LF0 暴露的 admissibility seam，但单独从 scratch 训练仍不能恢复 phase event。Run A 是有效的表示类别对照；LF1 主体假设仍必须由 Run B 的 event-balanced distillation 与 persistent replay 检验。

## HYPOTHESIS

事件均衡蒸馏可能让 B0 转移 medium 的两个事件，而固定权重 replay 可能在完整 PINN physics closure 中避免事件拓扑被灾难性遗忘。Run A 对此既不证实也不否证。

## UNKNOWN

- B0 是否通过 frozen data-transfer gate；
- B1 是否保留两周期事件并把 fixed full-physics objective 降到冻结比例；
- 条件 C 是否可达；
- multi-seed、stress、formal OOD 与 headline method increment。

## 下一步和边界

当前唯一动作是等待用户重启同一 AutoDL 端点，然后复用冻结工程重试 source identity 执行远端零步前检与 Run B。不得运行 C，除非 B 先达到冻结 provisional 条件；不得新增 seed、权重扫描、optimizer、phase-latent teacher、PJGR/R2 或 stress。当前没有方法 candidate，也没有投稿级正面证据。

## 证据入口

- [compact interim artifact](artifacts/20260903T140233Z-phk-v23-lf1-a-interim-dc091be.json)
- [Run A summary](../../outputs/runs/20260903T134252Z-phk-v23-lf1-a-range-preserving-dc091be-er1/summary.json)
- [local nominal adjudication](../../outputs/runs/20260903T140233Z-phk-v23-lf1-local-after-a/adjudication.json)
- [engineering-retry source manifest](../../cloud/phk_v23_lf1_autodl/deployed-source-manifest-engineering-retry1.json)
