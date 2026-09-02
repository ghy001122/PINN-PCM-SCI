# PHK-V2.3 R1X AutoDL run card

- `status`: `AWAITING_AUTODL_RESTART_CAMPAIGN_AUTHORIZATION_REMAINS_ACTIVE`
- `task_id`: `PHK_V23_R1X_BOUNDED_CLEAN_COUPLING_CAMPAIGN_EXECUTE`
- `first_trajectory`: `E1_CLEAN_COUPLING_EXPLORATION`
- `role`: `NON_VOTING_DEVELOPMENT_EXPLORATION`
- `device`: `Tesla V100-PCIE-32GB`
- `dtype`: `FP64`
- `seed`: `17`
- `arm`: `STRONG_RAW`
- `maximum_optimizer_updates_e1`: `1800`
- `checkpoint_policy`: `GLOBAL_FINAL_ONLY`

云端只包含 source bundle 和 reference-blind 训练入口，不得包含 nominal/stress reference、evaluator 或 teacher probe。每条轨迹必须从 scratch；不得读取上一条 checkpoint、optimizer state 或随机状态。

## E1 唯一命令

```bash
cd /root/autodl-tmp/PINN-PCM-SCI
OMP_NUM_THREADS=1 /root/autodl-tmp/envs/pinn-pcm-sci-py311/bin/python \
  -m pinn_pcm_sci.phk_v23_r1x run \
  --output-root /root/autodl-tmp/PINN-PCM-SCI/outputs/runs/<RUN_ID> \
  --device cuda:0 \
  --source-identity <DEPLOYMENT_BUNDLE_IDENTITY> \
  --hourly-price-cny <CURRENT_LIVE_PRICE> \
  --variant E1_CLEAN_COUPLING_EXPLORATION
```

后续 E2/E3/confirmation 只可使用本 campaign machine tree 唯一选出的参数；不得同时部署多个分支。

## 实时观察

仅允许 tail 日志、`nvidia-smi`、tmux attach、文件存在性和进程检查。观察不得改变配置、alpha、stage 或停止时间。

## 回收、关机与评价顺序

1. 回收 checkpoint、training log、R1X telemetry、start/final manifests、prediction、environment 和 summary。
2. 核验远端与本地每个允许产物的 size 和 SHA-256。
3. 立即执行 `/usr/bin/shutdown -h now` 并以 `Connection refused` 或平台等价状态验证关机。
4. 仅在关机验证通过后，本地运行 frozen nominal evaluator 与 R1X adjudicator。
5. 若 machine tree 需要下一条轨迹，保持 campaign 授权并等待用户重新启动实例；不得让 GPU 空闲等待。

stress references 在整个 campaign 中始终 sealed/unread。
