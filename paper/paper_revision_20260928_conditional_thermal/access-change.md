# 对外稿访问声明更新

任务 `PCM-20260928-CONDITIONAL-THERMAL-CLOSURE-01`。本次仅形成新的对外稿，不追溯修改冻结交付。权威文字为[新 Markdown 源](manuscript/source/manuscript.md)，可读稿为[展开 Markdown](manuscript/manuscript.md)、[DOCX](manuscript/manuscript.docx)及[PDF](manuscript/manuscript.pdf)。

**VERIFIED（既有发布记录）：**[科学提交 709b10f 中的电路 V/I 评分子集](https://github.com/ghy001122/PINN-PCM-SCI/tree/709b10fd28fc8fc80c9103acd68be02c35ac2816/paper/paper_revision_20260928_circuit_comparison/scoring-subset)已公开。其范围包括十套本项目生成的作者模型电压／三支电流、有限电压观测、锁定 PCHIP／CS 数组和多项式、评分代码及结果；来源是[既有发布核验](../../docs/notes/2026-09-28-cubic-energy-comparison-release.md)。新稿删除已过时的“只有预测，无法独立原数组重评分”描述。

**VERIFIED（范围边界）：**该子集支持保存数组重评分。既有隔离目录复算精确一致是该子集的证据；不表示新 ODE/PDE 积分、神经 AD、检查点推理或重新训练。旧二维 PINN 全预测／参考场及检查点仍为另一份本地范围，P03 保持开放；未把本轮条件热缓存表述为已经公开。

修改位置只有 `Data, code and author declarations` 中两个访问段，科学文字、数值、图、表、摘要和结论均保留。AI 辅助、作者责任、资助／利益冲突待补等声明不变；补充材料继续沿用[原 58 页 PDF](../paper_revision_20260927_circuit_screen/supplement.pdf)。[精确源差分](manuscript/build/access-only.diff)与[构建输入记录](manuscript/build/preparation.json)可核查范围。本轮没有 Git 推送、数据公开、作者联系或投稿。

新报告的条件热和迟滞结果独立交付，不追加为旧主文的新科学章节，也不把公开评分子集称为材料实验数据。此次读取既有发布记录用于修正文义，没有重新执行旧科学评分。
