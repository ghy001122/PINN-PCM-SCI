# 构建与复核说明

本轮交付根：`E:\Python demo\PINN-PCM-SCI\paper\paper_revision_20260927_circuit_screen`。权威正文只有 `source/manuscript.md` 与 `source/supplement.md`；根目录Markdown、DOCX及PDF是导出。数学公式在Markdown中可编辑，DOCX沿用原构建链的公式图片，不声称原生Word公式对象。

## 已实际执行

1. 原CSV核对摘要与Table 2a，没有重评分旧场；见 `display-verification.json`。
2. `prepare_document.py`展开源表并渲染公式；`build_docx.py`生成两份DOCX。项目Python用于前者，捆绑文档Python用于后者。
3. 复用 `paper/advisor_review_20260924/render_with_word.ps1`：Microsoft Word导出PDF，捆绑Poppler渲染页面。主稿17页、补充58页；全部页面作接触表检查，公式、修改段落和表格作整页重点检查，见 `build/visual-review.json`。既有Windows缺LibreOffice的故障没有触发重复安装。
4. 云端SciPy 1.14.1执行6项聚焦测试和十份保存输入分析。预测锁定一次，评分在工程修正后复用预测继续；回收读取核验后关机。实例缺Matplotlib，图件在本地生成。

`circuit-screen/attempt1-analysis-source.py`保留初次工程中止版本；`circuit-screen/scoring-source.py`与成功评分的源码身份一致。当前入口仅在分解图坐标范围上增加留白；科学公式、参数和评分不变。

## 从保存预测复核

以下从项目根运行，十条原生输入在 `input-inventory.json` 中逐个列出。缺输入即失败，不生成替代轨迹或回退到其他工作区。本轮筛查与历史完整独立数据包是不同复算范围。

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_voltage_circuit_screen.py -v
.\.venv\Scripts\python.exe scripts/run_voltage_circuit_screen.py --config configs/voltage_circuit_screen_20260927.json --mode score
.\.venv\Scripts\python.exe scripts/run_voltage_circuit_screen.py --config configs/voltage_circuit_screen_20260927.json --mode figures
.\.venv\Scripts\python.exe paper/paper_revision_20260927_circuit_screen/finalize_screen_report.py
```

`--mode predict`/`all`拒绝覆盖已有锁定预测，不能用于重复本轮已完成的预测。这些入口没有网络推理、神经AD、电学正解或ODE/PDE推进。聚合保存残差不等于重新计算神经AD。

```powershell
.\.venv\Scripts\python.exe paper/paper_revision_20260927_circuit_screen/prepare_document.py
& 'C:/Users/CJ/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' paper/paper_revision_20260927_circuit_screen/build_docx.py
& paper/advisor_review_20260924/render_with_word.ps1 -DocxPath paper/paper_revision_20260927_circuit_screen/manuscript.docx -OutputDir paper/paper_revision_20260927_circuit_screen/build/render-manuscript
& paper/advisor_review_20260924/render_with_word.ps1 -DocxPath paper/paper_revision_20260927_circuit_screen/supplement.docx -OutputDir paper/paper_revision_20260927_circuit_screen/build/render-supplement
```

构建依赖及文件身份见 `build-dependencies.json`。页面PNG核对后可清理；公式PNG是构建依赖，保留。历史完整复算沿用[原包说明](../paper_revision_20260926_core/standalone-README.md)，本轮未重复运行24.6 GB完整包，未扩大其验证能力。

十份原NPZ保持全部时刻和FP64精度。T/R/H及保存电流不进入预测接口。五条开发CSV及封存协议均未读取数值。原作者代码MIT来源与第三方数据/PDF权利分别保留，见[来源清单](../paper_revision_20260926_core/literature/source-manifest.json)与[访问方案](data-access-plan.md)。
