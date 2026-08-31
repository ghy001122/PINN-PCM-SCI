# PHK-V2.3 R1a ConFIG AutoDL run card

- `status`: `ONE_REFERENCE_BLIND_RUN_AUTHORIZED_NOT_YET_CONSUMED`
- `task_id`: `PHK_V23_R1A_CONFIG_COMPETENCE_RECOVERY`
- `device`: `Tesla V100-PCIE-32GB`
- `dtype`: `FP64`
- `seed`: `17`
- `arm`: `STRONG_RAW`
- `optimizer_updates`: `1000`
- `checkpoint_policy`: `FINAL_ONLY`

只允许一次 standard-ConFIG shared-solver-backbone competence-recovery run。云端不得存在 nominal/stress reference、evaluator、teacher probe、checkpoint selection、第二 arm、第二 seed、R1b 或 PJGR。

## 唯一命令

```bash
cd /root/autodl-tmp/PINN-PCM-SCI
OMP_NUM_THREADS=1 /root/autodl-tmp/envs/pinn-pcm-sci-py311/bin/python \
  -m pinn_pcm_sci.phk_v23_r1a_config run \
  --output-root /root/autodl-tmp/PINN-PCM-SCI/outputs/runs/<RUN_ID> \
  --device cuda:0 \
  --source-identity <DEPLOYMENT_BUNDLE_IDENTITY> \
  --hourly-price-cny <CURRENT_LIVE_PRICE>
```

## 回收与关机

回收并核验 checkpoint、training log、start/final manifests、ConFIG mechanism telemetry、prediction、environment 和 run summary。逐文件远端/本地 SHA-256 一致后，立即执行 `/usr/bin/shutdown -h now` 并确认 SSH 断开。只有关机确认后，才允许在本地读取 nominal reference 并运行冻结 evaluator。stress references 始终不可达。

## 已执行结果

- `run_id`: `20260831T144554Z-phk-v23-r1a-config-5d8accc`
- `source_commit`: `5d8accc0ac3d4bee81f696d400afac6bdd0eef32`
- `device`: `Tesla V100-PCIE-32GB`
- `updates/config_applications`: `1000/1000`
- `wall_seconds_including_prediction`: `606.0168335074559`
- `estimated_incremental_cost_cny`: `0.31647545749833805`
- `autodl_shutdown`: `CONFIRMED_CONNECTION_REFUSED`
- `local_adjudication`: `R1A_CONFIG_RAW_NO_COMPETENCE`

完整证据见 [R1a closeout](../../docs/experiment/2026-08-31-phk-v23-r1a-config-closeout.md)。本 run card 不授权重跑、R1b、PJGR 或 stress。
