# PHK-V2.3 R0B 首次窗口切换 175-step 最小诊断收口

- `date`: `2026-08-31`
- `run_id`: `20260831T095149-phk-v23-r0b-first-switch-175-8d072e2`
- `task_id`: `PHK_V23_R0B_FIRST_SWITCH_175_MINIMAL_V2`
- `execution_status`: `COMPLETED`
- `diagnostic_outcome`: `R0B_PRECURSOR_CANDIDATE_IDENTIFIED`
- `primary_precursor_candidate`: `GRADIENT_STARVATION`
- `causal_root_cause_identified`: `false`
- `claim_status`: `V22R_TERMINAL_NO_GO_PRESERVED_R0B_GRADIENT_STARVATION_PRECURSOR_NO_METHOD_EVIDENCE`
- `next_research_execution_authorized`: `false`
- `stress_reference_status`: `TWO_STRESS_REFERENCES_SEALED_UNREAD`

## 总裁决

`VERIFIED`：唯一一次 V100/FP64/seed-17 `STRONG_RAW` scratch replay 完成了 `175/175` 个 canonical Adam updates，科学 schedule denominator 保持 `1000`，云端 shadow optimizer steps 为 `0`。reference-blind machine adjudication 在 nominal reference 打开前不可变写入，最早且唯一持续支持的前兆为：

```text
status = R0B_PRECURSOR_CANDIDATE_IDENTIFIED
PRIMARY_PRECURSOR_CANDIDATE = GRADIENT_STARVATION
onset_step = 10
confirmation_step = 25
reason = EARLIEST_UNIQUE_PERSISTENT_REFERENCE_BLIND_PRECURSOR
causal_root_cause_identified = false
next_stage_authorized = false
```

随后还分别在 step `75/100` 与 `110/120` 得到 `GRADIENT_CONFLICT` 和 `ELECTROTHERMAL_DRIVE_DEFICIT` 的持续支持。它们是时间顺序证据，不是因果根因证明。首次 W1→W1+W2 切换没有触发冻结的 material-shock 条件；因此本地 factorial 固定为 `FACTORIAL_NOT_RUN_NOT_NEEDED`。

## 执行身份与完整性

`VERIFIED`：

- source commit：`8d072e2ece0668583adad4b3cefff3e978436f05`；三份 R0B 合同 SHA-256 分别为 `7AD60F79...52B`、`724EC715...2DD`、`F23E508D...5F4`。
- 设备：`Tesla V100-PCIE-32GB`；dtype：FP64；seed：17；初始化：scratch；arm：`STRONG_RAW`。
- run wall time：`186.262694 s`；observer time：`61.748540 s`；按 `1.88 CNY/h` 估算增量费用 `0.0972705 CNY`。这是展示单价估算，不是平台账单。
- checkpoint `update=175`，其内嵌 `training_config.updates=1000`；final manifest 状态为 `DIAGNOSTIC_PREFIX`，不能冒充完整 nominal 训练。
- prediction shape 为 `[1001, 12800]`，全部 finite；完整时间轴 phase 最大值 `0.0924472 < 0.5`。
- 28 条 telemetry 全部回收；每次 callback 均保持 model state、既有 `.grad`、model mode，以及 Python/NumPy/Torch CPU/CUDA RNG。
- checkpoint、prediction、telemetry、transition bundle、log、start/final manifest、environment 与 summary 的本地大小和 SHA-256 均与远端 summary 一致。
- 云端 run、telemetry、checkpoint 和 prediction 均未读取 nominal/stress reference；两份 stress references 从未打开。

## 远端前检与关机

`VERIFIED_INFRASTRUCTURE_ONLY`：初版精简部署包漏带一份被 PHK-V2.1 物理合同哈希绑定的 `tests/test_phk_v21_benchmark.py`，远端前检因此为 6 pass / 4 `FileNotFoundError`。当时没有训练、checkpoint 或科研输出。补传 source commit 中 SHA-256 为 `F2D8F7AC...629` 的原文件后，远端 R0B focused tests 为 `10/10 OK`，V100 为 `0 MiB / 0%`，随后才启动正式 replay。临时部署清单的完整 commit SHA 也在上传前纠正并逐文件校验；错误身份未进入远端正式运行。

`VERIFIED`：正式运行完成、产物下载并逐哈希核验后立即执行 AutoDL shutdown；随后 SSH 探针返回 `Connection refused`。实例已关闭，不再产生本阶段 GPU 费用。

## Reference-blind 时间证据

### VERIFIED

- 冻结 starvation 门要求 phase-head total-objective gradient norm 不高于最大其他 head 的 `10%`。step 10 的实际比值为 `0.0099061`，step 25 进一步为 `0.00396457`，连续满足门并最早确认。
- step 75 和 100 的 phase-head loss-pair 最小 cosine 分别为 `-0.990902` 与 `-0.997150`，随后满足 material conflict 门。
- W1 最大温度在 step 110/120 分别降至 `0.210910/0.196440`，均低于冻结的 `0.225` 门；对应 ROI positive-growth fraction 均为 `0`，随后满足 electrothermal-deficit 门。
- W1 phase 最大值从 step 150 的 `0.02391267` 到 step 151 的 `0.02391226` 只发生极小变化，未形成需要本地 factorial 的 switch-associated material shock。
- step 175 的 W1 phase 最大值为 `0.02384678`，最终 training loss 为 `0.04924763`。损失下降仍未构成事件 competence。

### SUPPORTED_INTERPRETATION

- phase head 从训练早期开始获得的总目标梯度相对其他 heads 过小；冲突和低电热驱动是在更晚时刻出现的并存机制。因此，未来若另立 R1a，最有信息增益的单一干预轴是预注册的 phase-head gradient materiality / balancing 机制，而不是先加 PJGR、换 seed 或延长训练。
- 本结果只支持“梯度饥饿是最早持续前兆”。单轨迹观察不能证明它是独立充分原因，也不能证明修复它一定恢复相变事件。

### UNKNOWN

- 哪个具体 loss term、参数化或 optimizer interaction 造成 phase-head gradient materiality 下降。
- 单一 head-aware balancing 干预能否恢复 competence，以及之后是否仍需要处理 gradient conflict 或 electrothermal drive。
- PJGR、其他 seed、更长预算、stress、formal OOD 或正向方法增益的结果。

## Nominal non-voting appendix

reference-blind decision 固定后，才在本地打开 nominal development reference。该 appendix 不参与 precursor 投票，也不改变下一阶段授权：

- time-averaged phase-region symmetric difference：`0.00515`；
- phase ROI continuous RMS：`0.1111426`；
- hard guards：失败；两周期均为 event missing、ROI peak below minimum、recovery failure。

该结果只说明 175-step diagnostic prefix 仍不具 event competence；R0B 本来就不是 competence recovery run。它不改写 V2.2R 的 1000-step terminal No-Go，也不构成新的方法比较。

## 产物与下一步边界

- [compact machine artifact](artifacts/20260831T095149-phk-v23-r0b-first-switch-175-8d072e2.json)
- [experiment manifest](manifests/20260831T095149-phk-v23-r0b-first-switch-175-8d072e2.json)
- raw run：`outputs/runs/20260831T095149-phk-v23-r0b-first-switch-175-8d072e2/`（git-ignored）

本阶段在 `R0B_PRECURSOR_CANDIDATE_IDENTIFIED` 收口。下一研究执行未授权；允许的后续仅是只读审查，或另行制定一个以 phase-head gradient materiality 为唯一原子轴的 R1a `PLAN_ONLY` 合同。不得自动运行 R1、PJGR、第二次 R0B、stress、其他 seed、预算延长、作者联系或投稿。

本记录不 supersede PHK-V2.2R terminal closeout、R0A closeout、bounded-negative advisor draft 或 stress seals。
