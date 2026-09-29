# 本轮主张与证据映射

本轮写作继承现有权威稿，全部S1—S24历史方法、六臂、八臂、N/G/S、B1、S23和F_cov结果保留。新增材料仅在S25形成一个辅助节；正文6.3用一段连接中心问题。权威文本为source/manuscript.md、source/supplement.md及其明确包含的source/auxiliary-section.md和source/joint-result-section.md；根目录Markdown是构建展开件。

| 论文位置／主张 | 直接证据 | 边界 |
|---|---|---|
| 摘要、4.1：E/F共同修复后器件增量 | tables/full-label-main.md及继承S16共同读出表 | 两协议分别重训，非formal OOD；配置收益非VJP单独因果 |
| 4.2：B_E反例；5.1：D_E边界 | 继承正文与S17原配对源表 | 强反例不隐藏；剩余PDE必要性未确立 |
| 4.3：E/F_cov与连续效应 | tables/fcov-continuous-primary.md；S24三个完整表 | 12行是两个初始化的敏感性条件 |
| S21—S23：失败与条件相态演化 | 完整继承表、公式、空间相态及局部热源图 | 不合并不同轮次性能，不把C2接缝等同可行性证明 |
| 6.3与S25a：全角色温度、电流和闭合 | tables/neuristor-all-roles.csv；上轮results/temperature.csv、closure.csv | 直接取冻结数表，无本轮重积分或重评分 |
| S25.2：两条恒等式及交叉项 | 共同KCL热方程、同系数的代数推导 | 非新定理或因果贡献率；非零r_T,KCL须保留 |
| Figure S28：固定12.5 V展示 | build/auxiliary-figure-source.json所指保存数组；draw_manuscript_auxiliary.py只绘图 | 原2.362—2.862 μs窗口，无对齐或重新挑选 |
| S25.3：历史反转、负耗散与能源表示差 | 已发布条件热results-report.md、history-diagnostics.json和旧能量窗口CSV | 无实验温度真值；源两步长非误差界 |
| S25.4—S25.5：联合原型 | 本轮冻结config、实际准入、训练／接受终点和结果记录 | 未完成方法不参加胜出裁决；传统基线和实现失败必须保留 |
| 数据声明 | 709b10f电路V/I公开子集、d068bdf条件热公开包、旧二维数据访问记录 | 新局部公开不关闭旧二维全场P03 |

历史可复算入口仍分别指向原记录，不重做大型归档：[完整S1—S24来源](../paper_revision_20260927_circuit_screen/source/supplement.md)、[条件热全部数组和评分](../paper_revision_20260928_conditional_thermal/reproduction.md)、[电路能量最小子集](../paper_revision_20260928_circuit_comparison/scoring-subset/README.md)。缺失输入必须显式报错，不生成替代值。

初版写作先于联合计算完成；S25.5现已以seed29三个接受终点和未通过联合门的实际出口替换。Table S25b—S25d记录共同读出、F原生读出、各资格分项、准确成本和S线搜索回滚；不触发seed43。真实结果来自outputs/runs/20260929-joint-reconstruction/seed-29-results.json，不重新推进、训练或评分。最终页数与逐页视觉检查见build/visual-review.json。
