# 稿件构建与交付来源

本轮复用已经验证的Markdown解析、python-docx、Microsoft Word COM导出和Bundled Poppler渲染链。已有环境记录明确LibreOffice不可用，不重复失败安装或引入另一套正文。

权威文本为source/manuscript.md、source/supplement.md；补充明确包含source/auxiliary-section.md和source/joint-result-section.md。tables和references.md由构建展开。manuscript.md、supplement.md、DOCX及PDF是这些源的派生格式；不要单独修改派生正文。

构建入口依次为prepare_document.py、build_docx.py以及仓库既有paper/advisor_review_20260924/render_with_word.ps1。DOCX使用Codex bundled Python；科研图只从保存数组读取，使用项目Python。公式采用旧已核验图的精确内容缓存，新公式单独渲染。未修改的历史图、表和公式为硬链接，其内容不得原位编辑，且不算独立备份。

实际构建运行时路径：

- DOCX Python：C:/Users/CJ/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe。
- PDF渲染：C:/Users/CJ/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe。
- Word：本机既有Microsoft Word COM导出，只打开本轮生成文件。
- 公式与图：项目Python的Matplotlib，PNG是构建输入，不是可删除的临时预览。

完整图表由继承稿的已锁定源表加本轮neuristor-all-roles.csv组成。新增Figure S28的保存数组身份在build/auxiliary-figure-source.json；draw_manuscript_auxiliary.py无ODE推进、历史重放或参数选择。新增联合原型结果按根任务实际记录进入S25.5，未执行／无效终点不得写成比较胜出。

S25.5已替换为三个实际接受态、联合门未通过和不触发seed43的完整结果。最终构建统一从Markdown展开，逐页视觉检查主稿和完整补充；真实页数、文件身份和具体发现保存在build/visual-review.json。初版占位不进入终稿。最终审核页PNG可在核验完成后依精确白名单清理；最终DOCX/PDF、公式和科学图保留。
