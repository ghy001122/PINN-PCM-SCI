# 本轮主稿构建与审阅

权威文字为 `source/manuscript.md`。正文只更新可用性段落中的公开版本与实际访问范围；其余原文、数字、表和图保持不变。展开版Markdown、DOCX和PDF由同一来源生成，不维护三个独立正文。DOCX公式沿用高分辨率图片，公式源仍可在Markdown编辑，不声称原生Word公式。

本轮完成一份主稿DOCX和一次Word/PDF导出，最终主稿17页。24个不变公式与原render-manifest逐式核对后复用原PNG；6张科学图、6张表和参考文献来自原有冻结交付。继承资产采用硬链接节约空间，不算独立备份，不能在本目录直接修改它们。真实输入和源码身份见 `build-dependencies.json`。

最初准备尝试重复渲染不变公式时发生内存分配失败，未生成DOCX。之后发现一个图的替代文本包含方括号，初始资产清单未匹配该图；按解析后的完整manifest补齐。一次修复脚本因Windows默认编码停止，随后显式UTF-8完成。工程经过见 `build/preparation-engineering-record.json`。所有失败均在最终DOCX产生之前，没有重算任何科学量；仅有一份成功主稿构建。

最终沿用原Microsoft Word COM → PDF → 捆绑Poppler页面渲染链。当前Windows环境的规范renderer缺LibreOffice已由原交付记录确认，本轮没有重复安装或伪称使用了LibreOffice。Poppler仍提示Symbol/ArialUnicode别名字体，但实际17页逐页图像检查未见缺字、重叠或截断。第16页是实际修改页；第1页摘要、第2–7页公式、第10页Table 2a及第17页引文均检查。宽表保留原分页和重复表头，不重新排版继承内容。

补充未修改，继续使用[原58页补充PDF](../paper_revision_20260927_circuit_screen/supplement.pdf)、[原DOCX](../paper_revision_20260927_circuit_screen/supplement.docx)及[权威源](../paper_revision_20260927_circuit_screen/source/supplement.md)，本轮没有重建。

以下是已实际运行并成功产出当前文件的命令，从仓库根执行。准备阶段只展开保存表格和复用公式图，不运行科学分析。

```powershell
.\.venv\Scripts\python.exe paper/paper_revision_20260928_circuit_comparison/prepare_document.py
& 'C:/Users/CJ/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' paper/paper_revision_20260928_circuit_comparison/build_docx.py --document manuscript
& paper/advisor_review_20260924/render_with_word.ps1 -DocxPath paper/paper_revision_20260928_circuit_comparison/manuscript.docx -OutputDir paper/paper_revision_20260928_circuit_comparison/build/render-manuscript
Copy-Item -LiteralPath 'paper/paper_revision_20260928_circuit_comparison/build/render-manuscript/manuscript.pdf' -Destination 'paper/paper_revision_20260928_circuit_comparison/manuscript.pdf'
.\.venv\Scripts\python.exe paper/paper_revision_20260928_circuit_comparison/record_build.py
```

普通页面PNG和重复导出PDF在最终核验后可清理；24个公式PNG是实际构建依赖，保留。原稿和继承资产不清理。此次文稿仅本地保存；AutoDL离线待同步按总交付清单记录。
