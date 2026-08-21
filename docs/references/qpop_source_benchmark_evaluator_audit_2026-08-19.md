# Q-POP-IMT 一手来源、基准与 evaluator 审计

- 审计日期：2026-08-19
- 审计范围：Q-POP-IMT 论文、CPC Program Library 数据集、DOE-COMMS 官方 GitHub、官方 README/LICENSE/代码与环境文档
- 证据边界：已从 CPC 官方地址下载程序 ZIP、复核发布方 SHA-256 并只读检查归档、嵌入 Git 与参考输出；未执行归档内代码、未安装 Q-POP 依赖、未运行求解器
- 科学主张状态：`NO_SCIENTIFIC_CLAIMS`
- 当前 G2 准入：`SOURCE_AUDIT_COMPLETE_ENVIRONMENT_REBOOT_PENDING`

## 1. 决策摘要

| 审计项 | 状态 | 结论 |
| --- | --- | --- |
| 论文、CPC 数据集与开发仓库身份 | `VERIFIED` | 论文明确链接 CPC 数据集 DOI `10.17632/p3395559s6.1` 和开发仓库 `https://github.com/DOE-COMMS/Q-POP-Modules`。 |
| CPC v1 对应的 Git tag/commit | `VERIFIED` | 官方 ZIP 内含嵌入仓库，HEAD 为 `6047117bb9f40355db260aae59ec427de2050b94`，即 `v1.1.0-1-g6047117`；该提交相对 `v1.1.0` 只改变 `.gitignore` 与 `.DS_Store`，求解器和 canonical input 内容与 `v1.1.0` 相同。 |
| 唯一作者案例的案例身份 | `VERIFIED` | 采用论文中明确标为 “Example of usage” 的 VO2 内禀电压自振荡案例；论文的均匀零电压 Landau 势校验只作为辅助验证，不作为竞争基准候选。 |
| 唯一作者案例的可执行快照 | `VERIFIED` | CPC ZIP 的 tracked `imt/examples/input.xml` 与 untracked reference-run `intrinsic-voltage-osc/input.xml` 字节一致，SHA-256 为 `d7df895f...a6bd7`。 |
| 官方 evaluator | `ABSENT` | 论文、完整 CPC ZIP 与开发仓库均未提供独立评分入口或冻结指标聚合；登记 `OFFICIAL_EVALUATOR_NOT_PROVIDED`。 |
| 许可 | `VERIFIED` | CPC 数据集登记 MIT；官方仓库 `LICENSE` 为 MIT，`Copyright (c) 2023 DOE-COMMS`。 |

来源、许可、canonical case 与 evaluator 状态已经达到 G2 source subgate。Q-POP smoke 仍不能启动，因为 Windows 已完成 WSL 2/Ubuntu 20.04 安装命令但明确等待重启；重启后还须验证发行版并建立冻结 legacy solver 环境。

## 2. 一手来源身份链

1. 论文：[Shi et al., *Q-POP-IMT: An open-source phase-field software for simulating insulator-metal transition processes in quantum materials*, Computer Physics Communications 315 (2025) 109751](https://doi.org/10.1016/j.cpc.2025.109751)。论文的 Program Summary 指向以下两个程序来源，并登记 MIT：
   - CPC Library program files：[Mendeley Data version 1, DOI 10.17632/p3395559s6.1](https://data.mendeley.com/datasets/p3395559s6/1)
   - Developer repository：[DOE-COMMS/Q-POP-Modules](https://github.com/DOE-COMMS/Q-POP-Modules)
2. CPC v1 的官方文件清单接口只列出一个文件：[`Q-POP-Modules.zip`](https://data.mendeley.com/public-api/datasets/p3395559s6/files?folder_id=root&version=1)。冻结元数据为：
   - file id：`9dd9bd1c-a4e3-4163-99f2-ba5e547a6e12`
   - size：`51,866,371` bytes
   - SHA-256：`9e0814d5cc0d01a554152d04e68b565d0b54260430d883b4b5ada0f0f7bced16`
   - created：`2025-07-18T08:17:53.851Z`
   - last modified：`2025-07-18T08:20:20.239Z`
3. 官方 Git refs（2026-08-19 只读核验）：
   - `v1.0.0` -> [`6a653afd5f51728de02a010b460160a72267c528`](https://github.com/DOE-COMMS/Q-POP-Modules/commit/6a653afd5f51728de02a010b460160a72267c528)，该提交时间为 2024-04-24，消息为 “Improved installation documentation”。
   - `v1.1.0` -> [`ff57cd7a6066e0065697b48864fbbf888fb14385`](https://github.com/DOE-COMMS/Q-POP-Modules/commit/ff57cd7a6066e0065697b48864fbbf888fb14385)，该提交时间为 2025-05-25，消息为 “Validated the code and tested a 3D simulation”。
   - 归档 ZIP 生成前的仓库提交还包括 [`d8910b670c38349cb403a19d4f550d7d51e30802`](https://github.com/DOE-COMMS/Q-POP-Modules/commit/d8910b670c38349cb403a19d4f550d7d51e30802)，时间为 2025-07-17，消息为 “Reduced solver tolerances in input.xml in examples folder”。
   - 2026-08-19 的 remote `main` HEAD 为 [`bcfad845e79cd5d0f827af8556d5029dcf500b0d`](https://github.com/DOE-COMMS/Q-POP-Modules/commit/bcfad845e79cd5d0f827af8556d5029dcf500b0d)，时间为 2025-11-13，消息为 “Revised a potential bug in calculating voltage drop in post-processing”。

### 2.1 版本关系裁决

`VERIFIED`：论文、CPC v1 与开发仓库属于同一 Q-POP-IMT 发行链。

`VERIFIED`：下载文件大小为 `51,866,371` bytes，实测 SHA-256 与发布方元数据完全一致。ZIP 内共有 4,388 个条目，无绝对路径或 `..` 路径穿越，并包含完整嵌入 `.git`。其冻结 HEAD 为 `6047117bb9f40355db260aae59ec427de2050b94`（2025-06-06，`v1.1.0-1-g6047117`）。该提交相对 `v1.1.0` 只改动 `.gitignore` 与 `.DS_Store`；`imt/qpop-imt.py` 和 `imt/examples/input.xml` 的 Git blob 在两个 ref 间一致。

ZIP 的工作树不是 clean checkout：三个 `.DS_Store` 有差异，且 `imt/examples/intrinsic-voltage-osc/` 是 untracked overlay。该 overlay 的 `input.xml` 与 tracked canonical input 字节相同，另附作者参考输出。因此冻结 source identity 为：

> `CPC DOI 10.17632/p3395559s6.1 + archive SHA-256 9e0814d5...ced16 + embedded Git HEAD 6047117... + CPC reference-output overlay`

不得用归档后的 `d8910b...` 或当前 `main` 替换 CPC source。内容等价只用于说明 solver/case 与 `v1.1.0` 的关系，不把 tag 本身冒充 CPC 包身份。

## 3. 许可

- CPC v1 页面将数据集许可登记为 `MIT License`。
- 官方仓库的冻结许可原文见 [`LICENSE` at v1.0.0](https://github.com/DOE-COMMS/Q-POP-Modules/blob/v1.0.0/LICENSE)：`MIT License`，`Copyright (c) 2023 DOE-COMMS`，要求在软件副本或实质部分中保留版权与许可声明，并包含标准无担保条款。
- 当前 HEAD 与 `v1.0.0` 的 `LICENSE` Git blob 均为 `f2b4fce4e2cd71bf1f9f97fe60d092ece1d297d0`；该许可文件在这两个已核验点一致。

CPC ZIP 内含 `LICENSE`，SHA-256 为 `d4b43b2369dbb7a8ca6a8d18717f6292e47875aa59a64e7fad8b4cd77287237f`，内容为同一 MIT 许可。许可一致不能替代版本内容一致，但本来源链的许可核对已闭合。

## 4. 唯一 canonical case

### 4.1 选择规则的应用

论文包含两类算例，角色不同：

1. “Code validation” 使用均匀 VO2、零电压，将序参量随环境温度的计算与直接最小化 Landau 势比较；这是实现校验，不是论文的 usage example。
2. “Example of usage” 明确用 Q-POP-IMT 模拟 VO2 的内禀电压自振荡；论文说明采用外电路边界条件、`C = 0`、室温，并把它作为软件使用示例。

因此按“论文明确案例优先”冻结案例身份为：

> `QPOP_IMT_VO2_INTRINSIC_VOLTAGE_SELF_OSCILLATION_AUTHOR_EXAMPLE`

不得改选均匀零电压校验或更容易收敛的输入作为 canonical benchmark；均匀校验只能作为 qualification 中的辅助子检查。

### 4.2 当前 README 参数化及其边界

官方仓库当前 [`README.md`](https://github.com/DOE-COMMS/Q-POP-Modules/blob/bcfad845e79cd5d0f827af8556d5029dcf500b0d/README.md) 将同一 usage example 参数化为：VO2 矩形器件、300 K、9 V 直流、`5e5 Ohm` 串联电阻、`0 nF` 电容、`3e6 W/(m^2 K)` 散热系数、`100 x 40 x 20 nm` 尺寸、平面 mesh `100 x 40`、终止时间 `2000 ns`、`SOP=1.119`、`EOP=-1.293`，以及边缘半圆成核设置。README 报告该完整案例在 16 个 AMD EPYC 7742 CPU 进程上约需 2 小时。

这些数值已由 CPC ZIP 中 tracked canonical input 与 reference-run input 的字节一致性复核，可作为 `CPC_V1_AUTHOR_INPUT` 写入 `BenchmarkContract`。G2 smoke 只能复制该输入并缩短 `endtime`；不得改物理、材料参数、网格、边界或求解器语义。

## 5. EvaluatorAudit

- `status`: `ABSENT`
- `official_evaluator_id`: `OFFICIAL_EVALUATOR_NOT_PROVIDED`
- `reason`：
  1. 论文给出物理/实现验证方法和图示，但未给出一个从预测文件读取、计算冻结指标并聚合结果的官方 evaluator 程序。
  2. 当前官方仓库的文件树包含主求解器、示例输入、文档、PVD 可视化和日志输出；未发现名为 evaluator/metric/reference-result 的 IMT 基准评分入口。`stash/py/*.test.py` 属于历史/通用测试路径，不能据文件名冒充论文案例 evaluator。
  3. CPC v1 ZIP 的全部 4,388 个条目已检查；排除嵌入 `.git` 与 reference-run 场数据后，没有 evaluator/metric/score/benchmark 类入口，相关文本也没有 RMSE、reference-result 或 metric-aggregation 合同。

因此必须明确登记 `OFFICIAL_EVALUATOR_NOT_PROVIDED`。项目后续依据 CPC reference output、论文物理观测量与 `BenchmarkContract` 建立的脚本只能称 `frozen project evaluator`；不得从论文曲线自行构造“官方”阈值或把示例图称为官方评分。

论文中的均匀 Landau 势比较是 validation procedure；README 的电压自振荡图和 `log.txt` 诊断是示例输出。两者都不自动等于官方 benchmark evaluator。

## 6. Linux/WSL 启动合同

官方当前环境文档 [`docs/prepare.md` at remote HEAD](https://github.com/DOE-COMMS/Q-POP-Modules/blob/bcfad845e79cd5d0f827af8556d5029dcf500b0d/docs/prepare.md) 明确建议 Ubuntu 20.04，并记录：

- GNU Compiler Collection 9；
- OpenMPI 3.1.6（官方称全部测试使用该版本）；
- Boost 1.71.0（官方称全部测试使用该版本）；
- PETSc 3.15.1（官方称全部测试使用该版本）；
- DOLFIN/FEniCS `2019.1.0.post0`，含 Python interface；
- MUMPS 等线性求解组件由 PETSc 配置提供。

官方根 README 的启动形式为：

```text
mpirun -np 8 python <path-to-qpop-imt.py>
```

程序从工作目录读取 `input.xml`，并把输出写入当前工作目录。根 README 声明输出场为 `eta.pvd`、`psi.pvd`、`phi.pvd`、`T.pvd`、`n.pvd`、`p.pvd`，同时生成 `log.txt`。

边界：官方文档没有声明或验证 WSL2，也没有冻结 Python minor version。专用 WSL2 Ubuntu 20.04 是项目隔离实现选择，不是上游支持主张；不得把项目 Python 3.11 默认值强行施加到 legacy Q-POP runtime，必须以固定 solver 环境的实际兼容性为准。

2026-08-19 已执行 Windows 的 `wsl --install -d Ubuntu-20.04 --no-launch`，并可读取 WSL `2.7.12.0` 与 kernel `6.18.33.2-2` 版本。系统同时明确存在待重启状态；在 Windows 重启、发行版完成初始化并核对 `/etc/os-release` 与 WSL 版本前，不得安装 solver 依赖或启动 Q-POP。此时总体 G2 状态是 `PAUSED_PENDING_WINDOWS_REBOOT`，尚未产生 gate outcome。

## 7. 已发现的语义差异与资格化风险

### 7.1 电子序参量输出名不一致

- 根 README 将电子序参量输出列为 `psi.pvd`。
- 当前 [`imt/README.md`](https://github.com/DOE-COMMS/Q-POP-Modules/blob/bcfad845e79cd5d0f827af8556d5029dcf500b0d/imt/README.md) 将其列为 `mu.pvd`。
- 当前 [`imt/qpop-imt.py`](https://github.com/DOE-COMMS/Q-POP-Modules/blob/bcfad845e79cd5d0f827af8556d5029dcf500b0d/imt/qpop-imt.py) 实际构造 `mu.pvd` 输出，而论文物理符号使用电子序参量 `psi`。

归档代码已经消除了“应该读取哪个文件”的来源歧义。CPC v1 的实际混合未知量为 `eta, mu, gamma_e, gamma_h, phi, T, Ib`；归档参考输出实际包含 `eta.pvd`、`mu.pvd`、`phi.pvd`、`T.pvd`、`n.pvd`、`p.pvd` 与 `Tcvar.pvd`，不存在 `psi.pvd`。因此这是 `DOCUMENTATION_ALIAS + EXECUTABLE_DETAIL`，不是 G2 来源阻塞：converter 必须登记 `source_name=mu`、`physical_symbol=psi`，且不得请求不存在的 `psi.pvd`。`n/p` 是从 `gamma_e/gamma_h` 推导的输出；全部独立未知量、推导量与单位的逐项闭合仍须在 G3 `PhysicalContract` 中完成。

### 7.2 归档版本与当前 main 的后处理差异

当前 remote `main` 的归档后提交消息明确涉及电压降后处理潜在 bug 修复，而 canonical case 的独立器件量正是电压/外电路轨迹。CPC v1 source 已经固定，作者案例复现必须保持其原始后处理不变；不得把当前 `main` 的修复拼接进 CPC 物理场。该修复对 `log.txt` 电压列和论文曲线的影响要在 G3 单独审计，并决定器件端点是否可被资格化。这是 G3 的有效性风险，不再是 G2 的来源歧义。

### 7.3 CPC v1 参考输出并非完整 2000 ns 轨迹

CPC v1 已完整只读检查，但 reference-run overlay 不能被默认视为完整作者轨迹：canonical input 的 `endtime` 是 `2000 ns`，而随包 `log.txt` 停在 step 757、`512.0793 ns`，末尾累计 `Nfail=240`、`Tfail=44`；PVD 时间序列也未覆盖完整终止时间。它仍是官方 CPC 包中的作者参考 artifact，但既不是官方 evaluator，也不能未经资格化充当“完整参考真值”。G3 必须解释中止/缺失边界并执行冻结的完整案例；若完整复现失败或目标结构事件不存在，则按预声明规则裁决 `INVALID`。

## 8. G2 后续最小核验清单

1. 重启 Windows；重启前不继续发行版初始化、依赖安装或 Q-POP 执行。
2. 重启后核验 `wsl --version`、`wsl -l -v`、Ubuntu 20.04 `/etc/os-release` 与 WSL 2 运行状态，并把实际版本写入环境身份。
3. 依照冻结的官方环境文档，在该发行版中建立 legacy solver 依赖；记录实际版本和来源，不对 Windows 全局 Python 或项目 Python 3.11 环境施加变更。
4. 以 CPC source identity 与 `CPC_V1_AUTHOR_INPUT` 建立 `BenchmarkContract`，冻结 `EvaluatorAudit=ABSENT`，并为 `log/PVD` 准备只读的 `frozen project evaluator` adapter；不得发明官方阈值。
5. 执行 G2 最短原生 smoke：只缩短 `endtime`，至少完成一个有效非线性步，贯通原生输出、artifact converter、磁盘 evaluator、manifest 与 index；最多允许一次纯基础设施修正，并保留原失败。
6. smoke 通过才进入 G3；若环境、字段或磁盘读取无法闭合，则按 G2 合同裁决并停止。

来源子门已达到 `VERIFIED`；总体 G2 当前仅为 `PAUSED_PENDING_WINDOWS_REBOOT`，尚未产生通过、失败或阻塞处置。本审计不证明 Q-POP 数值有效、物理合格、可复现，也不产生任何 KC/PINN 方法结论。
