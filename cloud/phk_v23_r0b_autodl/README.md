# PHK-V2.3 R0B minimal-v2 AutoDL run card

- `status`: `ONE_REFERENCE_BLIND_RUN_CONSUMED_COMPLETE_NO_RERUN`
- `task_id`: `PHK_V23_R0B_FIRST_SWITCH_175_MINIMAL_V2`
- `canonical_optimizer_steps`: `175`
- `scientific_schedule_denominator`: `1000`
- `cloud_shadow_optimizer_steps`: `0`

本卡只允许当前用户批准的一次 V100/FP64/seed-17 `STRONG_RAW` scratch replay。不得上传 nominal/stress reference、local evaluation、teacher probe、sealed path 或历史 reference-derived artifact。

该授权已由 run `20260831T095149-phk-v23-r0b-first-switch-175-8d072e2` 消耗。运行、回收、哈希核验和 AutoDL shutdown 均已完成；SSH 复核为 `Connection refused`。不得再次执行下方命令。结果见 [R0B closeout](../../docs/experiment/2026-08-31-phk-v23-r0b-first-switch-175-closeout.md)。

## 启动前

1. 本地合同、focused tests、legacy regression 与 document consistency 全过并形成选择性 source commit。
2. 远端 checkout 必须等于该 source commit；工作区、run directory 与进程身份无漂移。
3. `nvidia-smi` 必须显示 `Tesla V100-PCIE-32GB` 且无其他训练进程。
4. Python 固定 `/root/autodl-tmp/envs/pinn-pcm-sci-py311/bin/python`；显式 `OMP_NUM_THREADS=1`。
5. 实时显示单价、1 h/5 CNY 本阶段上限、34 h/95 CNY V2.3 上限与 150 CNY 项目上限均须通过。

## 唯一命令

```bash
cd /root/autodl-tmp/PINN-PCM-SCI
OMP_NUM_THREADS=1 /root/autodl-tmp/envs/pinn-pcm-sci-py311/bin/python \
  -m pinn_pcm_sci.phk_v23_r0b run \
  --output-root /root/autodl-tmp/PINN-PCM-SCI/outputs/runs/<RUN_ID> \
  --device cuda:0 \
  --source-identity <SOURCE_COMMIT> \
  --hourly-price-cny 1.88
```

run 必须在唯一 tmux `phk_train` 中运行。不得覆盖既有目录、重跑、改 seed、延长到 176 或 1000 steps、实施 recovery/PJGR、打开 reference 或运行第二臂。

## 回收与关机

只回收 run root 下的 checkpoint、training log、start/final manifest、reference-blind telemetry、transition diagnostic bundle、prediction carrier、environment 与 summary。先核对远端/本地 SHA-256、run/contract/source identity 和 `checkpoint.update=175`、`training_config.updates=1000`，随后立即执行 AutoDL 关机并确认 SSH 拒绝连接。关机前不得打开 nominal reference；stress 永不打开。

本地 reference-blind adjudication 完成并不可变写入后，若且仅若 machine decision 要求，运行 CPU gradient-only factorial；最后才允许生成 nominal non-voting appendix。任何结果都不自动授权 R1。
