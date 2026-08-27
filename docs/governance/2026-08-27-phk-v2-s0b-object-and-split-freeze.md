# PHK-V2 S0B 对象、数值与 complete-case split 冻结

- `date`: `2026-08-27`
- `status`: `S0B_PRE_FIRST_SOLVE_FREEZE_COMPLETE`
- `scientific_evidence`: `NONE_NO_PHK_SOLVE_OR_TRAINING`
- `object_id`: `PHK_REDUCED_WALL_CELL_2D_V1_NUMERICAL_V1`
- `program_contract_sha256`: `0E1D89DD23F93C90160AC82ECE60ADA154410F4DDC33578CB892207FE8B445A8`

## 冻结载体

| 文件 | bytes | SHA256 | 作用 |
| --- | ---: | --- | --- |
| `configs/phk_v2/object_numerical_contract.json` | 9186 | `3B3B9A369F4AFDFFB201394DD294E7196BAF04E5B36BAFE126291CA9CB3EA157` | 首次 PHK 求解前的无量纲物理、几何、波形、数值、事件、守卫、收敛和 12-intent 合同 |
| `configs/phk_v2/case_split_manifest.json` | 308712 | `EBFDA2D59049AC989E8AA6C9622D92CF077D4B808961AB5807D178BF09DF57ED` | 324 个 complete-case 候选的 write-once pool manifest；内部 canonical manifest hash `55261CCA82ED2B71A9D3A81E28FC957B4873086CECB09D28EEE9B73B2CD73E09` |
| `pinn_pcm_sci/phk_contract.py` | 12418 | `ED2CA2C3C231DE4FFC08CEB754A4F4CD2E8AC3FAD4E22E3DCB8ECD330CE77CE0` | fail-closed contract loader、waveform 和 outcome-blind complete-case identity/split |
| `pinn_pcm_sci/phk_runner.py` | 2918 | `10792B94588FB04918F5C9A0A1B0DD9D56B3DE1DC1FD9FCD7029091E30F99772` | write-once split freeze process seam；尚无 solver/training subcommand |

split pool counts 固定为 `D=48, I1=19, I2=21, F_A=26, F_O=150, R=60`。`F_O` 保留整族 narrow-heater 或 narrow-interface holdout；reserve 规则先于 orthogonal/hash partition。formal 实际打开的 case 数只能按 program contract 的预先 power 规则选择前缀，不能按结果挑 case。

## 身份与科学边界

- 所有数值系数明确为 `ENGINEERING_DIMENSIONLESS_CONTRACT_VALUES`。Miquel 只提供 wall-cell 与因果链启发；本对象不是其 GGST 模型重放、材料校准或实验验证。
- 物理链闭合 current continuity、Joule heating、latent heat、temperature/phase-dependent conductivity 与 dynamic phase field。
- 12-intent ladder、事件 ROI/阈值、空间/时间/replay floors、thermal/Joule controls 与 no-rescue 已在首解前固定。
- 7 项 TDD 测试验证 strict loader、精确 waveform、case SHA、互斥 split、orthogonal/reserve precedence 与 write-once carrier；这些测试只证明合同/身份实现，不证明 PDE、solver、event 或方法正确。
- 本记录写入时没有运行 PHK solver、官方 baseline、PINN、GPU 或 formal，没有生成科学 run/ledger。

下一阶段先实现 manufactured/zero-drive 的独立数值 seam，并在隔离目录对固定外部 baseline 做 CPU smoke。任何首个 PHK 数值 intent 必须引用上述 exact hashes。

