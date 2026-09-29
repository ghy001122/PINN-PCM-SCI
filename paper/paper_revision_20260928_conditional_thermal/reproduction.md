# 运行与保存数组复算

本包为 `PCM-20260928-CONDITIONAL-THERMAL-CLOSURE-01` 的本地科研交付。它不是已经公开的独立数据包；旧公开电路子集不包含本包新增的温度和历史数组。没有将旧大包复制或重复解压。

## 实际执行

批准基线 `390ca72aee60a0f483697d52b72674bf07dd7297`；本地 Python 3.11.9、NumPy 2.1.1、SciPy 1.14.1，FP64。计算入口在导入数值库前将 OMP/OpenBLAS/MKL/NumExpr 线程上限设为4。CPU执行，无GPU启动或云端依赖。

工作目录为仓库根。已执行一次的入口如下，**结果存在时会拒绝自动重复**：

```powershell
.\.venv\Scripts\python.exe scripts/run_conditional_thermal_closure.py compute
```

40条主响应与40条8点核对属于同一冻结任务；不能删除执行记录来救援或重复选择结果。10条源历史核对通过后才执行20条候选历史重放。源码身份及各输入身份见 `execution.json` 和 `config.json`；运行源码原样保存于 `code/`，不是未说明的新算法版本。

## 从保存数组重建表格与报告

```powershell
.\.venv\Scripts\python.exe scripts/run_conditional_thermal_closure.py score
.\.venv\Scripts\python.exe paper/paper_revision_20260928_conditional_thermal/write_report.py
```

评分仅读取保存条件温度、源比较量、锁定预测和已重放的R/g/H，重算误差/差分/本构诊断代数和窗口聚合；不会再次热推进或历史重放。不含检查点推理、神经AD或训练。缺输入会报错，没有回退数据源、伪造字段或自动调用原模拟器。

绘图使用 `scripts/plot_conditional_thermal_closure.py`，仅消费保存数组。该脚本采用已安装的绘图库环境；依赖和实际生成身份见 `figures/render-record.json`。稿件使用 `manuscript/` 下原样式构建入口、已有公式图片及本机Word；`manuscript/build/preparation.json` 列出真实依赖，`visual-review.json` 记录17页检查。科学报告和对外稿是不同交付，后者仅改访问段。

## 输入与数组语义

| 内容 | 相对仓库根的路径／身份 |
|---|---|
| 原十套time/V/I/T/R/g/H | `outputs/runs/20260926-core-revision-vo2-bridge/vo2/<id>.npz` |
| 锁定预测与系数 | `paper/paper_revision_20260928_circuit_comparison/scoring-subset/predictions/{PCHIP,CS}/<id>.npz` |
| 原完整物理合同 | 配置字段 `source_contract` |
| 新响应、复核温差 | 本目录 `arrays/<id>/thermal.npz` |
| 原生三层差分 | `arrays/<id>/decomposition.npz` |
| P/CS已接受无反馈历史 | `arrays/<id>/history-{P,CS}.npz` |
| 源语义核对 | `arrays/<id>/source-history-check.json` |
| 完整窗口表与事件明细 | `results/` |

`thermal.npz` 保存全部原生时刻的四种温度、4点减8点温差。8点温度可由主温度减该差重建，无需冗余保存另一整套字段。`decomposition.npz` 保存P/CS总差与三层项；RMS不是可加分量。历史数组保存电阻、g、完整六种历史状态、I_R和r_close，I_KCL仍从原锁定预测读取。全部采用原生FP64，无丢点、降精度或波形对齐。

热输入入口与历史函数无文件读取能力，只接收明确参数和函数/温度数组。源T/H在温度资格通过后才用于历史核对，随后只参与评分。模型纯迟滞类被复用，源模型 `simulate` 和 `run` 均未调用。

## 必要验证与能力边界

5项热合成测试和4项历史小型测试已在执行前通过；见 `engineering-verification.json`。没有重跑旧插值、旧能量或全仓科学测试。保存数组评分已实际执行一次，当前包未声称另做过仓库隔离的外部复算。旧电路子集的隔离复算证明仍属于其原任务。

新输出保存在稳定项目目录，远端同步待下次已授权实例会话；单份期间不删除唯一缓存。原数组、原锁定插值、旧模型和旧科学评分均保留。数据处理遵循项目2026-09-28规范。
