# 投稿候选稿：训练期电学消元与共同事后修复

2026-09-16，本地成稿交付。依据用户 `Paper_Sprint.md` 授权完成；保留 `paper_v32`，本包不自动提交或推送。研究证据继承 `codex/v32-research-results@ea29be9a9d33497b075873bcdc7673df43db7221`，没有新科研运行。

随后用户另行明确授权发布及跨会话独立复评。本包发布分支为`codex/paper-submission-results`，实际提交号由发布后的交付消息提供；[完整评估请求](../../docs/notes/2026-09-16-paper-submission-cloud-review-handoff.md)与本稿同版本。下文未发布记录保留为此前成稿阶段事实，不表示本包禁止已获授权的发布。

## 阅读入口

- [完整英文正文 PDF](manuscript.pdf) 与 [可编辑正文](manuscript.md)。
- [合并补充材料 PDF](supplement.pdf) 与 [可编辑补充](supplement.md)：方法细节、必要反事实、完整事件、计算量、复现及主张边界。
- [参考文献](references.md) 与 [BibTeX](references.bib)。
- [统一结果表](tables/unified-results.csv)、[逐配对效应](tables/paired-effects.csv)、[完整事件](tables/complete-events.csv)、[本轮报告性延迟变化分析](tables/latency-change-report-only.csv)。
- 六组主图位于 `figures/`，每组保留 PNG/PDF；数据、算法与文字源分别是 `analysis-provenance.json`、`build_analysis.py` 和 `source/`。

## 本轮形成的完整论证

**VERIFIED：** 既有四个协议/初始化配对中，消元方法经过与 soft 相同的电学重求解后，仍保留电流和功率收益。新稿围绕这一问题完整定义隐式电学层、局部半电阻焦耳沉积、热单元残差与 E/F 目标，不将 solver、VJP、FV 或优化器分别包装为原创模块。

**SUPPORTED_INTERPRETATION：** 同状态修复、共同投影、全空间 soft、干净配对和新完整协议共同支持受限方法包贡献。它们不能单独识别 VJP 因果，也没有证明剩余热/phase PDE 的独立必要性。

**本轮新增的是成稿与已有结果分析。** 将两个协议的 B_E 各计一次，统一绝对误差、百分点和相对变化；从保存的事件表复算第二事件延迟变化，保留 F29 对这一变化略优于 E29 的反证；用保存的带符号功率曲线解释分脉冲能量抵消。正文纳入全部关键不利结果，补充材料保留完整事件和主张矩阵。没有把已有成果重复称为本轮新增训练结果。

## 最优先的剩余问题

1. **固定数值参考的边界。** 新协议 seed43 的 S 门只有 4.4453125e-6 绝对裕量；连续体和参考扰动稳健性尚未验证。补充 S9 仅提出固定模型、两协议时间参考细化的最小待批项，不执行、不阻塞本稿。
2. **投稿定位与证据强度。** 当前是合成无量纲二维计算方法研究，不能称材料标定氧化物器件；严格双周期仍失败，D_E 很强。针对目标期刊调整叙事时必须保留这些事实，不增加未完成贡献。
3. **投稿行政与数据归档。** 作者、基金、利益声明需要真实信息；公开精选包不含全部 dense 轨迹，正式提交前应落实完整数据归档或准确的获取说明。当前稿件明确披露该范围。

停止新增 seed、协议、权重搜索、结构模块和事件单门救援。本轮零训练、零 checkpoint 加载/前反向、零新电学/参考求解、stress 未读，未启用 GPU。未执行 commit/push/PR。

## 重建文稿，不执行科学模型

在仓库根目录依次运行：

```powershell
.\.venv\Scripts\python.exe paper\paper_submission\build_analysis.py
.\.venv\Scripts\python.exe paper\paper_submission\prepare_document.py
& 'C:\Users\CJ\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' paper\paper_submission\build_pdf.py
```

前两步使用已有 NumPy/Matplotlib 环境；第三步仅使用现成的 ReportLab 排版环境。其他机器可使用相同依赖的 Python，PDF 构建读取前一步记录的字体路径。`prepare_document.py` 将 `source/*.md` 中的表格/参考文献 include 展开为交付的完整 Markdown；后续编辑正文应修改 `source/` 中的文字或对应 CSV 生成逻辑后重建，避免只改展开文件。

数字、公式、引用与图文的针对性校对记录位于 `build/review-summary.json`；PDF 逐页预览位于 `build/preview/`，属于本地 QA 中间材料。此检查不替代独立科研复现，也不触发新资格门。
