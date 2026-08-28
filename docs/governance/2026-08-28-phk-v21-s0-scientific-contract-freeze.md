# PHK-V2.1 S0 scientific contract freeze

- `record_id`: `PHK_V21_S0_SCIENTIFIC_CONTRACT_FREEZE_V1`
- `effective_date`: `2026-08-28`
- `status`: `FROZEN_BEFORE_FIRST_VOTING_SOLVE`
- `route`: `PHK_V21_REPEATABLE_EVENT`
- `authorization_source`: 用户批准执行《总体审查结论》末尾 GOAL
- `preserves`: `PHK_V2_COMPLETE_ORACLE_NO_GO_AND_ALL_PRIOR_EVIDENCE`

## 1. 冻结结论

`VERIFIED`：E1 已选择固定 logit-primary phase Newton；E2 在非投票工程沙盒完成 41/41 case records，并选择工程候选 `PHK_V21_E2_STAGE2_0A1813B1D968F573`。在任何 PHK-V2.1 voting oracle、作者指标复现或 neural run 之前，以下五份科学合同已完成、可解析并相互绑定。自本记录生效后，任何结果导向的对象、split、阈值、case、seed、预算、统计 margin 或停止规则改动都被禁止。

| 冻结载体 | 合同/manifest identity | 文件 SHA256 |
| --- | --- | --- |
| `configs/phk_v21/object_numerical_contract.json` | `PHK_V21_REPEATABLE_EVENT_2D_NUMERICAL_V1` | `BDC86AE4C1417E16A8772A88F7738B59D4F0D7BB3B272D1FFEC9E9572CF9CBDD` |
| `configs/phk_v21/case_split_manifest.json` | `PHK_V21_CASE_SPLIT_V1` | `FC4F27D92618BBDF222961340C7BDA3FA8CB3FEF918D0CF343A48A5387F4BAB7` |
| `configs/phk_v21/oracle_and_floor_contract.json` | `PHK_V21_ORACLE_FLOOR_V1` | `E596A5D50BB79A241928D98AC000BDCDD3AD7AF0B207BD5882F2D1C2EBB2E5FB` |
| `configs/phk_v21/baseline_replication_contract.json` | `PHK_V21_SHARP_PF_REPLICATION_V1` | `195C039C181DCF012F94B77DA5D03EFF3244CDCA2F4A63FF5DEDB6FD7747EBC4` |
| `configs/phk_v21/method_contract.json` | `PHK_V21_PHA_KC_METHOD_V1` | `F1E918E6C71557BF7ABBAE11519208BD3D042D04AC6AF04471F33CCB046A001D` |

共同上游 program contract 为 `PHK_V21_REPEATABLE_EVENT_PROGRAM_V1`，文件 SHA256 为 `B47CB3E131326077EF8D3EC50473B4F6A06D61E63B09861ECEF834901BE4D2A2`。split 的内部 canonical manifest SHA256 为 `8ECC41A76972F302A5456FFE3643C22E1FB68963E8A4BD4B272B46960FB99931`；其 128 个完整 case 互斥分配为 D=24、I1=12、I2=12、F_A=32、F_O=32、R=16。工程 search cases 不属于这些 scientific pools。

## 2. 实现与评价身份

首个 voting solve 使用以下已测试实现身份：

- `pinn_pcm_sci/phk_v21_benchmark.py`: `2CA60CCB157EA2B5F06C887F363C9D21BEC221225CE67D9A1352B73ED446822D`
- `pinn_pcm_sci/phk_v21_evaluator.py`: `0BCE2837094B208B3A6E5080655416ED908C36CAC3D5DB5018A2DF83E09596FC`
- `pinn_pcm_sci/phk_v21_runner.py`: `179C4C8EFF3541AB61B975515499DF5E89EA77F83CBAFCF9975EF903CBECF35C`
- qualification test bundle canonical SHA256: `74108DA25341248031BEF48CFB962826205BC878B1D4866F47CF52B715E85DCC`

这些身份实现固定的 14-intent 顺序：manufactured、zero-drive、nominal coarse/medium/fine/extra-fine、medium-half-dt、fine exact replay、Joule-off、conductivity-off、latent-off、wide-heater、narrow-interface 和 pseudo-transient cross-check。每个 intent 先写不可变 intent，再计算；失败不替换、不救援、不动态切换 solver。只有 terminal summary 能裁决完整 oracle gate。

六个端点为 phase-region symmetric difference、phase flux、event time、localized region geometry、recovery 和 terminal-current trace。component floor 在 neural work 前按 `max(space_delta,time_delta,replay_delta,solver_delta)` 封存；zero/Joule-off 的预期身份是 no-event control，不得被误判为 event failure。

## 3. baseline 与方法边界

[一手来源与复现身份审计](../references/2026-08-27-phk-v2-1-baseline-reproduction-identity-audit.md)文件 SHA256 为 `EDA89F42F357C5CA156F702D4343D8097B02A8590B80F0D6E8A5EB4ACE0E34BD`。Sharp/PF 的 `OFFICIAL_PAPER_METRIC_REPRODUCTION`、`PINNED_REPO_RECIPE_REPLICATION` 与 `CLEAN_ROOM_COMPARATOR_ADAPTATION` 三种证据身份互斥；GPL 代码只允许隔离运行，不并入本项目实现。至少三 seed、作者指标容差、失败语义与 neural floor seal 均已在 baseline contract 固定。

方法合同固定 strong raw、四臂瓶颈诊断、等预算 PHA×KC 2×2、capacity/compute/mechanism challengers、complete-case formal OOD、统计区间和停止表。PINN 必须实际包含 PDE/本构残差；sampling、causal training 与 loss balancing 是共同训练协议或对照，不作为额外 headline idea。adaptive pseudo-time 是 KC 必须面对的正交反证 control。

## 4. 自动停止与主张边界

从本记录开始可按授权自动执行 S1。任何 oracle event/control/convergence/floor 硬门失败立即形成 `PHK_V21_ORACLE_NO_GO_STOP_BEFORE_PINN`，不得进入作者指标复现或训练。后续各门同理按 live plan 的预注册停止表收口。

在实际门通过前仍然没有 PHK-V2.1 qualified oracle/event、Sharp/PF 指标复现、neural floor、strong raw、PHA-MF、KC、组合、formal/OOD 或正向论文证据。对象始终只称透明、无量纲、literature-inspired synthetic benchmark；不称材料校准、实验器件验证、作者模型复现、SOTA 或期刊接收。

