# 实际执行与复算入口

本轮使用既有项目Python 3.11.9、NumPy 2.1.1、SciPy 1.14.1和本地CPU。下列命令已经执行；预测和打包入口拒绝覆盖现有锁定结果，不用它们重复本轮已完成的十套CS。

从项目根执行的必要工程检查，合计8项通过：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_cubic_energy_comparison.py -v
.\.venv\Scripts\python.exe -m unittest tests.test_circuit_energy_tools -v
```

首次预测、锁定、导出子集与评分的实际顺序：

```powershell
.\.venv\Scripts\python.exe scripts/run_cubic_energy_comparison.py --config configs/cubic_energy_comparison_20260928.json --mode predict
.\.venv\Scripts\python.exe scripts/run_cubic_energy_comparison.py --config configs/cubic_energy_comparison_20260928.json --mode package
.\.venv\Scripts\python.exe paper/paper_revision_20260928_circuit_comparison/scoring-subset/scripts/run_cubic_energy_comparison.py --root paper/paper_revision_20260928_circuit_comparison/scoring-subset --config config.json --mode score
.\.venv\Scripts\python.exe paper/paper_revision_20260928_circuit_comparison/verify_independent.py
```

独立验证入口已经完成一次：复制到工作区外、验证复制内容、拒绝读取研究仓库数据、评分、比较完整JSON、临时移开必需输入确认报错后恢复。既有虚拟环境仅作运行依赖例外。验证副本在核验后清理；验证脚本也拒绝覆盖该次目录。实际记录、隔离运行器、日志和评分耗时均保存在`build/independent-*`。后续接收者应自行复制完整`scoring-subset/`到其工作目录并按[包内入口](scoring-subset/README.md)运行，不需要原研究工作区。

由保存数值生成本轮图表与报告的实际命令：

```powershell
.\.venv\Scripts\python.exe paper/paper_revision_20260928_circuit_comparison/make_figures.py
.\.venv\Scripts\python.exe paper/paper_revision_20260928_circuit_comparison/write_results_report.py
```

图例位置作过一次排版修正；报告表头和能力措辞作过一次修正，均未重新拟合或评分。主稿构建另见[实际文档构建说明](build-and-reproduction-manuscript.md)。未改动的完整补充直接链接旧版本。

`comparison/predictions-locked.json`记录预测源码身份和1次预测成本，`comparison/execution-package.json`记录打包成本，`scoring-subset/results/execution-score.json`记录首次评分成本，`build/independent-score-execution.json`记录独立评分成本。独立评分与首次评分是本轮两次完整评分；旧PCHIP零次重新拟合、原系统零次重新推进、神经网络零次查询/训练、实验CSV零次数值读取。

能量功能测试中的一次手算期望值错误在科学评分前修正；文稿首次准备发生的内存故障通过复用已核验公式图片解决。这两项工程记录不改变科学设置。旧冻结评分函数原样复用，跨平台浮点标量只按预固定FP64运算尺度核对，不改变旧科学阈值。
