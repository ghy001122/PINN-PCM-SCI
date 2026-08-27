# PHK-V2 S0 program contract 预注册记录

- `date`: `2026-08-27`
- `phase_id`: `PHK_V2_S0_CONTRACT_AND_BASELINE_FREEZE`
- `record_status`: `PRE_RESULT_PROGRAM_CONTRACT_FROZEN`
- `scientific_evidence_status`: `NO_REPRO_ORACLE_EVENT_OR_METHOD_EVIDENCE`
- `supersedes`: `NONE_SCIENTIFIC`; 只由 ADR 0045 覆盖上一完成 GOAL 的当前授权语义
- `preserves`: `ALL_PRIOR_NO_GO_FAILED_INTENTS_AND_V1_MANUSCRIPT`

## 1. 冻结输入与身份

| 载体 | 作用 | bytes | SHA256 |
| --- | --- | ---: | --- |
| `E:/PINN-PCM/后续研究总规划.md` | 用户提供的规划输入；不是项目权威或科学证据 | 34035 | `3A178D7F98D4333B1AB76AC226A7816209053525D6477A37AF2DAD47A85F3C70` |
| `docs/references/2026-08-27-phk-pinn-primary-source-baseline-audit.md` | R0 一手来源、代码固定点、许可与方法身份审查 | 25341 | `3F72722F844780EEA42E395C47C99568D8235AC6C0A70AB338BC74DAF6803C97` |
| `docs/adr/0045-adopt-phk-v2-strong-baseline-and-two-module-execution.md` | 用户目标的项目内接受理由与授权边界 | 3725 | `2108285B48250FF33D8EBCB9CDB8F0BF8D247E2570DAEC2BA0454C1648DDB084` |
| `docs/plans/NEXT_ACTIONS.md` | 唯一 live plan | 19507 | `A043F99DC36DC1C117466E7B770130FA6D5D862BD3247640978290202F9B4E8F` |
| `configs/phk_v2/program_contract.json` | 机器可读 program contract | 8077 | `0E1D89DD23F93C90160AC82ECE60ADA154410F4DDC33578CB892207FE8B445A8` |
| `archive/2026-08-27-goal-paper-one-shot-v1-complete.md` | 完整保留的上一 GOAL 合同与完成记录 | 19644 | `A133F92A13F6D7C7DEFEF4034F84FB3909F6D16F65DBEF6F362482174E062911` |

本记录在任何 `PHK_REDUCED_WALL_CELL_2D_V1` 数值求解、PINN 训练或方法结果之前写入。R0 报告已经完成来源静态审查，但没有运行作者代码、solver、PINN、GPU 或 formal。

## 2. 从规划输入纠正并冻结的承重项

1. Sharp-PINNs 正式论文身份不含 repo 配置中的 causal/RAR 长预算 recipe；两者分别固定为 `SHARP_PINNS_PAPER_REPLICATION_V1` 与 `SHARP_PINNS_REPO_RECIPE_4B7029E`。
2. Sharp 是主 phase-field domain anchor，不是唯一 evidence baseline；jaxpi2 adaptive pseudo-time 是 mandatory general strong/KC falsification control。
3. Sharp/PF GPL 和 jaxpi/PirateNet Penn 许可源码不直接并入主库；项目实现必须 clean-room，外来仓库只作隔离 comparator。
4. Causality-RBAR 官方代码链接当前 404，不声称作者代码复现。
5. Miquel GGST 模型包含未公开物性、保密成分且无代码，只允许启发透明 reduced wall-cell，不建立 author replay/open oracle 身份。
6. PHA-MF 与 field-selective KC 是仅有的两个 load-bearing 模块；sampling、causal、loss balance、staggered 和 pseudo-time 均为公共协议或控制。

## 3. 当前环境与资源门

2026-08-27 在项目虚拟环境核验：

```text
python=3.11.9
platform=Windows-10-10.0.26200-SP0
torch=2.5.1+cpu
cuda_available=false
cuda_devices=0
nvidia_smi=NOT_FOUND
```

因此当前可启动 R0/S0、CPU 官方 smoke、对象合同与有界 oracle engineering；development/formal GPU 阶段在本地 CUDA 设备出现且前置门通过前保持 `RESOURCE_NOT_YET_AVAILABLE`。该资源事实不是科学 No-Go，不授权付费或云端替代。

## 4. 下一次必须先冻结的载体

在第一次 PHK 对象数值结果前，必须写入并哈希：

- `configs/phk_v2/object_numerical_contract.json`；
- Q-only qualification intent ladder；
- complete-case candidate universe 与 `Q/D/I1/I2/F_A/F_O/R` split manifest；
- event、hard guards、space/time/replay convergence 和 evaluator normalizers/floors；
- CPU intent、失败与 gross-compute accounting schema。

在第一次 PINN 训练前，还必须冻结 strong baseline 候选、公共 training protocol、checkpoint 规则、method arms、seed schedule 与 formal 访问守卫。任何运行后对对象、event、pool、margin 或 failure semantics 的修改都定义新合同，不能回写本记录。

## 5. 当前可说与不可说

`VERIFIED`：用户目标已被整理为经一手来源纠正、带预算与自动门禁的 PHK-V2 program contract；旧 GOAL 已归档且证据保持不变。

`UNKNOWN`：任何官方 baseline 是否能在本机复现；新 wall-cell 是否能形成合格 event/oracle；strong raw、PHA-MF、KC、组合或 formal 是否有效。

不得声称：Sharp/PF/jaxpi2 已复现、PHK 对象已资格化、任何模块涨点、GPU/formal 已运行、实验验证、作者模型重放、SOTA 或二区接收保证。

