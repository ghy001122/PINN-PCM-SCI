# PHK-V2.3 R1X E1 infrastructure preflight blocker

- `task_id`: `PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE`
- `trajectory`: `PHK_V23_R1X_E1_CLEAN_COUPLING_EXPLORATION`
- `record_role`: `INFRASTRUCTURE_PREFLIGHT_NOT_SCIENTIFIC_RUN`
- `status`: `AWAITING_AUTODL_RESTART_CAMPAIGN_AUTHORIZATION_REMAINS_ACTIVE`
- `activation_commit`: `22f3b06b27838baf0822a7ae910b18652644ed27`
- `scientific_gpu_runs_consumed`: `0`
- `optimizer_updates_executed`: `0`
- `gpu_hours`: `0`
- `incremental_cost_cny`: `0`
- `scientific_claim_change`: `NONE`
- `stress_reference_status`: `TWO_STRESS_REFERENCES_SEALED_UNREAD`
- `date`: `2026-09-02`

## 已完成

- R1X 三份合同、ADR 0053、唯一 live plan、cold-state coupling homotopy、staged trainer seam、E1/E2/E3/confirmation machine tree、run card 与内容寻址部署 manifest 已写入并推送。
- R1X focused tests 37/37 通过；V2.2R、R0A、R0B、R0C、R1a、R1X 与文档一致性合并回归 99/99 通过。
- experiment ledger validator、`DOCUMENT_CONSISTENCY_VALID` 与 Git whitespace gate 通过。
- activation commit、本地 `main` 与远端 `PINN-PCM-SCI/main` 在连接探针前均为 `22f3b06b27838baf0822a7ae910b18652644ed27`。

## 阻塞事实

对此前已核验 endpoint `region-46.seetacloud.com:28355` 使用既有专用 SSH key 做了一次只读 preflight；连接在 SSH banner 阶段返回 `Connection refused`。因此无法核验当前 V100、空闲进程、远端环境、实时页面单价或部署 bundle，也没有启动 tmux、创建远端输出、运行 optimizer step 或使用 GPU。

## 恢复条件

用户只需重新启动 AutoDL 实例，并提供当前 SSH endpoint（host/port）和实例页面显示的实时单价。既有具名 campaign 科学授权继续有效，不需要重新批准 E1。恢复后必须重新核验本地/远端 source identity、V100/FP64 环境、无重复进程、云端无 nominal/stress reference，再启动冻结 E1。

不得用 CPU 训练、猜测 endpoint、沿用旧实时单价或换用其他 GPU。若 E1 完成，仍须按合同先回收与哈希核验、立即关机并验证，之后才能本地 nominal 评价。
