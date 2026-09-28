# 固定样条与能量辨别成果云端提交

2026-09-28 用户另行明确要求将重要交付结果整合并提交至 `ghy001122/PINN-PCM-SCI`。沿用 `codex/paper-revision-results`，发布基线为 `9414c1da37cb9a101bf3ed812d248f63d4454470`。此授权 supersedes 本任务科研收口时的 Git 未授权措辞；科研阶段仍为 `CLOSED`，下一研究执行授权仍为 `false`。

发布状态：`PUBLISHED_REMOTE_VERIFIED`。

成果提交：[709b10fd28fc8fc80c9103acd68be02c35ac2816](https://github.com/ghy001122/PINN-PCM-SCI/commit/709b10fd28fc8fc80c9103acd68be02c35ac2816)。已推送至 `codex/paper-revision-results`，并核对远端分支指向同一提交；本核验记录随后单独同步。

## 纳入范围

- [完整交付入口](../../paper/paper_revision_20260928_circuit_comparison/README.md)：17页主稿的 Markdown、PDF、DOCX，沿用58页补充的链接，修改说明、构建依赖、访问边界和数据处理记录。
- [固定CS与能量报告](../../paper/paper_revision_20260928_circuit_comparison/results-report.md)：十套锁定CS预测、十四条角色/来源步长配对、波形/峰/分解/电荷/能量指标、15张新增物理与诊断图。
- [最小独立评分子集](../../paper/paper_revision_20260928_circuit_comparison/scoring-subset/README.md)：十条本项目生成的作者模型源数组、锁定PCHIP/CS预测、固定配置、评分代码、测试和完整结果；它支持保存数组重评分，不提供ODE/PDE、神经推理、AD或重新训练能力。
- 本轮配置、实现、聚焦测试、实验清单、收口记录和当前状态入口。

**VERIFIED：**CS对静息9 V极小误差及抑制两个角色的器件电流RMS较小，对12.5 V、15.8 V和激发两个角色较大；方向在两套保存来源步长上稳定。CS存在保存查询点负器件电流与负瞬时耗散；总能量、区间能量和电流RMS不形成统一排序。独立目录重评分与首次结果精确一致。

**SUPPORTED_INTERPRETATION：**固定CS未形成统一替代优势，焦耳能量补充了时域失效诊断，但不构成新PINN方法或实验材料增量。

**UNKNOWN：**绝对用途充分性、连续真解误差、实验增量和内部热状态。唯一后续建议仍是先取得具名实验记录的测量接线、通道、驱动和C/RL说明；未授权校准或新pilot。

## 排除与边界

不纳入第三方实验CSV、`data.zip`、出版社或预印本PDF、模型检查点、参考场、历史24.6 GB全量包、重复ZIP、页面检查缓存、AutoDL连接/部署控制脚本、外部Skill及工作区其他未提交修改。冻结科研执行记录中的“当时未发布”保持历史事实。

本轮数值子集的Git获取因此闭合，但它不等于全论文数据外部访问闭合，P03保持 `OPEN`；本次不创建DOI、不投稿、不启动新训练、推理、ODE/PDE推进或下一pilot。Git发布与科学结论分开记录。

## 发布核验

发布前运行与本轮新增接口相关的聚焦测试、文档一致性门禁、限定暂存清单检查、对象完整性检查和敏感信息模式检查；不重算科学结果或重建稿件。八项聚焦测试通过，文档门禁返回 `DOCUMENT_CONSISTENCY_VALID`；限定清单189个文件、约66.9 MiB，最大单文件3.05 MiB。可移交清单38项的长度与SHA-256全部匹配，未暂存第三方原始资产、凭据、实例登录信息、外部Skill或工作区其他修改。首次成果推送后，远端分支身份与成果提交一致。
