# PHK-V2.3 LF0 AutoDL run card

- `task_id`: `PHK_V23_LF0_EXACT_TOP_WARMSTART_ATTRIBUTION_EXECUTE`
- `status`: `SOURCE_MANIFEST_PENDING_DO_NOT_START_GPU_RUN`
- `device`: `Tesla V100-PCIE-32GB`
- `dtype`: `FP64`
- `seed`: `17`
- `arm`: `STRONG_RAW`
- `maximum_scientific_gpu_runs`: `3`
- `first_run`: `A_EXACT_TOP_SCRATCH`

本目录只承载 LF0 的零步云端前检和运行卡。最终
`deployed-source-manifest.json` 必须在 LF0 源码提交后生成，并同时绑定 LF0
program、method、data、decision 四份合同；该文件生成并由 focused tests 验证
前，不得启动 GPU 科学轨迹。

## 云端输入边界

源码必须解压到一个新的绝对部署根，不得覆盖或从 R1X 部署根运行。唯一允许的
低保真训练载体是：

```text
outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz
```

medium carrier 与源码归档分开上传，并由 LF0 合同及 deployed-source manifest
同时绑定路径、大小和 SHA-256。云端禁止存在 fine、extra-fine、stress carrier、
nominal frozen evaluator、旧 checkpoint 或旧 prediction。medium 不得被替换为
其他分辨率，也不得作为阈值、checkpoint selection 或 early-stop 来源。

## 唯一零步前检

以下变量均须是绝对路径；`PYTHONPATH=.` 不合格：

```bash
DEPLOY_ROOT=/root/autodl-tmp/PHK-V23-LF0-DEPLOY-<SOURCE_COMMIT>
MEDIUM_CARRIER="$DEPLOY_ROOT/outputs/runs/20260828T-phk-v21-s1-q-04-nominal-medium/result-intent-04.npz"
SOURCE_IDENTITY=LF0-BUNDLE-<CONTENT_DIGEST>

cd "$DEPLOY_ROOT"
PYTHONPATH="$DEPLOY_ROOT" OMP_NUM_THREADS=1 \
  /root/autodl-tmp/envs/pinn-pcm-sci-py311/bin/python \
  "$DEPLOY_ROOT/cloud/phk_v23_lf0_autodl/preflight.py" \
  --source-identity "$SOURCE_IDENTITY" \
  --deployment-root "$DEPLOY_ROOT" \
  --medium-carrier "$MEDIUM_CARRIER"
```

前检只验证 source/contract/medium identity、唯一载体边界、V100/FP64 身份和
无重复 LF0 训练进程；它不得构造 optimizer、加载 checkpoint 或执行 optimizer
step。仅当输出 `REMOTE_LF0_PREFLIGHT_VALID` 时，才可在 tmux 中使用同一个绝对
`DEPLOY_ROOT` 启动冻结机器树所选运行。

## 运行与观察

LF0 runner 的最终 CLI 以 source commit 中的 focused test 为准。启动时必须同时
满足：

```text
PYTHONPATH=<absolute DEPLOY_ROOT>
OMP_NUM_THREADS=1
output root=/root/autodl-tmp/PHK-V23-LF0-RUNS/<RUN_ID>
device=cuda:0
source identity=<deployed-source identity>
medium carrier=<the exact allowed path above>
```

只允许 tail 日志、`nvidia-smi`、tmux attach、文件存在性和进程检查。观察不得
修改 sampler、loss、运行步数、checkpoint policy 或机器分支。

## 回收与关机

每条 A、B 或 conditional C 运行结束后：

1. 回收该 runner summary 精确列出的 checkpoint、training log、sampler identity、
   start/final manifests、prediction、environment 和 attribution telemetry；
2. 对允许产物执行一次远端/本地 size 与 SHA-256 对账；
3. 立即执行 `/usr/bin/shutdown -h now`；
4. 以 `Connection refused` 或平台等价状态验证关机；
5. 仅在关机确认后，本地运行冻结 nominal evaluation 与 LF0 adjudication。

若冻结机器树需要下一条 GPU 运行，返回：

```text
AWAITING_AUTODL_RESTART_CAMPAIGN_AUTHORIZATION_REMAINS_ACTIVE
```

用户重启实例后继续同一已授权 campaign；不得让 GPU 空闲等待。stress 始终为
`TWO_STRESS_REFERENCES_SEALED_UNREAD`。
