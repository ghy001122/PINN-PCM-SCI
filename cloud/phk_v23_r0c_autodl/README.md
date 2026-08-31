# PHK-V2.3 R0C effective-update AutoDL run card

- `status`: `ONE_REFERENCE_BLIND_RUN_CONSUMED_COMPLETE_DO_NOT_RERUN`
- `task_id`: `PHK_V23_R0C_EFFECTIVE_UPDATE_25_V100`
- `canonical_optimizer_steps`: `25`
- `scientific_schedule_denominator`: `1000`
- `cloud_shadow_optimizer_steps`: `0`

只允许一次 V100/FP64/seed-17 `STRONG_RAW` scratch replay。云端不得出现 nominal/stress reference、evaluator、teacher probe、recovery、PJGR、checkpoint selection 或第二个 arm。

## 唯一命令

```bash
cd /root/autodl-tmp/PINN-PCM-SCI
OMP_NUM_THREADS=1 /root/autodl-tmp/envs/pinn-pcm-sci-py311/bin/python \
  -m pinn_pcm_sci.phk_v23_r0c run \
  --output-root /root/autodl-tmp/PINN-PCM-SCI/outputs/runs/<RUN_ID> \
  --device cuda:0 \
  --source-identity <DEPLOYMENT_BUNDLE_IDENTITY> \
  --hourly-price-cny 1.88
```

只回收 checkpoint、training log、start/final manifest、R0C telemetry/summary、environment 和 run summary。远端/本地哈希核验后立即关闭实例；随后仅在本地对 reference-blind telemetry 运行机器裁决。

## 已消费结果

该命令已由 run `20260831T072029Z-phk-v23-r0c-effective-update-25-ec84907d` 消费。25/25 updates 完成，产物远端/本地哈希一致，AutoDL 已关闭且 SSH 探针为 `Connection refused`。机器裁决为 `R0C_ADAM_PRECONDITIONING_COMPENSATES_RAW_GRADIENT`。不得再次执行本卡命令；结果见 [R0C closeout](../../docs/experiment/2026-08-31-phk-v23-r0c-effective-update-25-closeout.md)。
