# 现稿补强与 VO2 作者模型成果云端提交

2026-09-26 用户另行明确要求将重要交付结果提交至 `ghy001122/PINN-PCM-SCI`。沿用 `codex/paper-revision-results`，基线 `90508f05a6f233a485413c7589cc74420015cbea`。此授权 supersedes 本轮此前 Git 未授权措辞；科研仍为 CLOSED，下一研究执行授权为 false。

发布状态：`PUBLISHED_REMOTE_VERIFIED`。

## 纳入范围

[完整交付入口](../../paper/paper_revision_20260926_core/README.md)：16页主稿、58页补充的 Markdown/PDF/DOCX、权威正文源、图表、证据映射、真实构建依赖、F_cov 报告、五工况报告、独立复算记录及待审下一研究计划。同时提交相关训练/读出/作者模型实现、工程测试、文档构建与复算入口、冻结配置、紧凑执行证据、阶段和实验索引。

[紧凑证据](../../paper/paper_revision_20260926_core/evidence/core-revision/README.md)包含完整优化预算、两条终点、全部评分方向、五工况两步长比较、工程故障与恢复、结果回收和关机。原运行路径与云端副本一一映射，冻结运行清单不追溯改写。

**VERIFIED：**E 相对 F_cov 的原 A/B 规则分别通过12/12；这只是两个初始化的敏感性条件。F_cov 相对 F 的端口改善伴随集合误差增加，完整不利结果保留。作者模型五工况两步长完成，但定量实验复现仍为 **UNKNOWN**。

## 排除与来源边界

完整场数组、参考数组、检查点、大型回收包、页面/公式缓存、连接与部署控制脚本、工作区其他未提交改动及外部 Skill 不纳入。完整本地数据包尚无外部获取闭合，P03 保持 OPEN；本次不创建 DOI、不投稿、不启动下一 pilot。

作者模型代码来自固定提交 `217d4f0ed6bfc680240021b07142a121cb4963d1`，按原 MIT LICENSE 保留代码、README 和来源记录。来源属于 Zhang 等后续 Collective dynamics 论文，不冒充 Qiu 原始数据。source-manifest.json 的 publication_authorized=false 保留获取时历史状态；本次授权只覆盖随原 MIT 许可再分发的代码/说明，不覆盖 data.zip 与出版社/预印本 PDF，后者均排除。元数据中的本地路径仅为来源说明，不承诺对应文件可从云端获取。

## 验证

不重复训练、推理、作者模型积分或稿件渲染。发布前核对限定清单、依赖、既有构建制品身份及文档一致性；推送后核对远端提交。

发布前文档门禁返回 `DOCUMENT_CONSISTENCY_VALID`。限定清单416个文件，排除了无关工作区修改；92项实际构建输入、构建入口及交付输出身份一致。现有报告的末尾空行按原产物保留，不改写冻结证据。

成果提交：[539130a2837594c4d8ae3d67fadddda3e862548a](https://github.com/ghy001122/PINN-PCM-SCI/commit/539130a2837594c4d8ae3d67fadddda3e862548a)。已推送并通过远端分支核验；此核验记录随后单独同步。科研保持 CLOSED，完整数据外部访问仍未闭合。
