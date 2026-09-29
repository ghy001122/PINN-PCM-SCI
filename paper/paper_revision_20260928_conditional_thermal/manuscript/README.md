# 访问声明更新版主稿

本版本由冻结主稿派生，唯一正文来源为 `source/manuscript.md`。展开[Markdown](manuscript.md)、[DOCX](manuscript.docx)及[PDF](manuscript.pdf)保留旧科学内容，仅更新数据访问段：电路 V/I 评分子集已公开；二维完整场包的外部访问仍未闭合。

[差分](build/access-only.diff)仅含两个访问段；[输入记录](build/preparation.json)列出真实来源。原六张图、六张表、24 张公式图及参考文献复用，不重新分析或绘图。Markdown 中公式仍可编辑，DOCX 公式沿用图片，不声称原生 Word 公式。

`prepare.py` 读取冻结源及原展开清单，逐段验证后生成新权威源／展开稿／渲染清单；`build_docx.py` 复用原构建代码。继承资产是硬链接，不能作为独立备份，也不能原位修改。原冻结稿、图表和补充保持不变。

构建依赖为项目 Python、捆绑文档运行时 Python（python-docx、Pillow）、已安装 Microsoft Word 和捆绑 Poppler。使用原先已成功的 Word COM 导出链；本机已确认 LibreOffice 不可用，不重复安装或试错。补充继续使用[原稿 PDF](../../paper_revision_20260927_circuit_screen/supplement.pdf)，未重建。

从仓库根复建当前访问更新：

```powershell
.\.venv\Scripts\python.exe paper/paper_revision_20260928_conditional_thermal/manuscript/prepare.py
& 'C:/Users/CJ/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' paper/paper_revision_20260928_conditional_thermal/manuscript/build_docx.py --document manuscript
& paper/advisor_review_20260924/render_with_word.ps1 -DocxPath paper/paper_revision_20260928_conditional_thermal/manuscript/manuscript.docx -OutputDir paper/paper_revision_20260928_conditional_thermal/manuscript/build/render
Copy-Item -LiteralPath paper/paper_revision_20260928_conditional_thermal/manuscript/build/render/manuscript.pdf -Destination paper/paper_revision_20260928_conditional_thermal/manuscript/manuscript.pdf
```

视觉检查记录位于 `build/visual-review.json`。普通页面 PNG 和重复导出 PDF 在核验后可依数据规范清理；真实构建所需公式图片必须保留。新稿为本地交付，未推送或投稿。
