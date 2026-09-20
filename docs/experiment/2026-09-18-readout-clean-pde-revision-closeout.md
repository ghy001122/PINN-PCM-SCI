# 投稿前共同读出、clean PDE消融与修订终局

状态：CLOSED。继承17ad7c9c；执行依据为用户批准的[六阶段计划](../notes/2026-09-18-readout-clean-pde-authorized-plan.md)。本轮结束于2026-09-18T16:09:50.957740+00:00。发布和实际投稿未授权，均未执行。

## 实质性结果

**VERIFIED：**The complete E/F device criterion remains satisfied in 4/4, 4/4 and 4/4 pairs with the finer reader under the original, time-refined and space-refined references, respectively. This supports the two tested reader levels, without certifying arbitrary-grid or continuum accuracy. The original-protocol seed-43 comparison against B_E loses its device-advantage criterion under the spatial reference with the finer reader; robustness is therefore specific to the E/F comparison.

**VERIFIED：**Neither clean pair meets either prescribed residual-increment criterion under any of the three references or two readers. D_E has lower raw phase, current and power RMS errors throughout these comparisons, with other outcomes mixed. This bounded counterexample does not prove equivalence or universal residual redundancy.

固定数组还完成了阈值邻域/补集FN-FP、精确log-conductivity带符号拆分、功率/累计能量抵消分析。它们为报告性解释，不是新增因果识别。完整数值、相对效应、百分点、逆向比较、事件及三参考/两读出判据见[新稿](../../paper/paper_revision_20260918/README.md)。

**SUPPORTED_INTERPRETATION：**方法贡献应限定为训练期电学约束与一致耦合的指定方法包收益。剩余残差的独立预测作用由本次clean对照实际裁定，不能用“包含残差”代替有效性证明。

**UNKNOWN/未建立：**普遍必要性、孤立VJP因果、连续体收敛、任意网格/材料泛化、稳定严格双周期和材料实验验证。六个历史相态续训负结果与相态/strict参考敏感性继续公开保留。

## 执行与复现

新增训练3000 Adam、600完整评估，电学正解27688、伴随23596；硬上限分别3000、600、58392、54500。两D_E都保存最后接受状态。十个历史细读出和两个D_E双读出完成；零新增参考轨迹、零stress。GPU已真实回收关机；用户之后重启的实例再次关闭确认。C盘本任务临时包已迁回E盘工作区。

扩展隔离评分包含90个对象/读出/参考记录，复现48个历史记录。NumPy-only环境无torch，实际模型前向和线性求解均为0；数值容差rtol2e-10/atol2e-12，布尔一致。此为同代码独立目录算术复算，不是第三方科学复现。完整数组按独立ZIP分包保留在本地，尚未公开。

正文25页、补充43页已逐页渲染并视觉检查；此为内部AI辅助检查。编辑源稿、图表、来源、主张矩阵、修订回应、附信和复现说明已整合。作者事实、期刊适配、许可与公开归档、最终作者批准仍是实际投稿待办，不等同于新的自动科研授权。

## 停止与下一动作

本轮批准的有界科学执行关闭。不追加κ/η/λ、相态头、strict单门救援、seed、协议或材料迁移。优先由作者完成投稿事实与目标期刊选择，再按正式指南适配和批准发布完整数组；不得把完整本地候选稿或阴性消融宣称为期刊接收。
