# 本版本的构建与复算入口

本文件对应 `paper_revision_20260926_core`。权威正文为 `source/manuscript.md` 和 `source/supplement.md`；表格与引用由同一稿源展开。历史目录保留各自的构建方式，不用于生成本版 PDF。

## 本机已实际使用的文档构建

在仓库根 `E:\Python demo\PINN-PCM-SCI` 使用 PowerShell：

```powershell
.\.venv\Scripts\python.exe paper/paper_revision_20260926_core/prepare_document.py
& 'C:/Users/CJ/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' paper/paper_revision_20260926_core/build_docx.py
& paper/advisor_review_20260924/render_with_word.ps1 -DocxPath 'E:/Python demo/PINN-PCM-SCI/paper/paper_revision_20260926_core/manuscript.docx' -OutputDir 'E:/Python demo/PINN-PCM-SCI/paper/paper_revision_20260926_core/build/layout-manuscript-final'
& paper/advisor_review_20260924/render_with_word.ps1 -DocxPath 'E:/Python demo/PINN-PCM-SCI/paper/paper_revision_20260926_core/supplement.docx' -OutputDir 'E:/Python demo/PINN-PCM-SCI/paper/paper_revision_20260926_core/build/layout-supplement-final'
```

第一步使用项目 Python 3.11、Matplotlib 生成完整 Markdown 和公式图片。第二步使用已打包的 Python 3.12.14、python-docx 1.2.0 与 Pillow；`--document supplement` 可仅重建补充。第三、四步使用已安装的 Microsoft Word 导出 PDF，再由打包的 Poppler 按 130 dpi 渲染页面。最终 PDF 从相应布局目录复制到本交付目录根部。此环境没有 LibreOffice，已记录打包渲染入口的失败和实际 Word 替代路径。

这些是本机依赖的真实路径，不宣称在未配置 Word 或对应运行环境的另一台机器上直接可用。实际输入、依赖、输出身份见 [build-dependencies.json](build-dependencies.json)；逐页视觉检查见 [build/visual-review.json](build/visual-review.json)。公式在 Markdown 中可编辑，DOCX 内是同源公式图片。文档生成不进行新训练、网络推理、电学求解或相态推进。

`finalize_coverage.py` 消费已经锁定的 F_cov 分数和保存场，生成其表格、文字与物理图；`build_vo2_report.py` 消费十条已保存作者模型轨迹，生成独立报告。二者不是重启科学运行的入口。其余历史图件的原始生成依赖单独记录在构建依赖表。

## 独立数组复算

完整包位于 `D:\Temp\PINN-PCM-Standalone-20260926`。在该目录使用独立 Python 3.11 环境及 NumPy 2.1.3、SciPy 1.14.1：

```powershell
python -I recompute.py --validate-only
python -I -u recompute.py --fresh
```

`--fresh` 创建新执行目录并真正重算；不指定它时，已完成范围的核验记录会明确标为复用。实际九类独立复算已完成；新 F_cov 的首次锁定后评分与第二次核验分开保存。精确布尔判决、原数值容差、缺输入报错和原仓库拒绝访问均保留。

详见 [复算能力说明](standalone-README.md)和[访问方案](data-access-plan.md)。保存数组重评分、保存残差重新聚合、检查点推理与重新训练是不同能力；本次独立复算不包括重新计算神经 AD。外部访问尚未落实，P03 保持开放。
