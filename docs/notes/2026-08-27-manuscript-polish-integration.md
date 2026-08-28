# 2026-08-27 外部会话论文润色整合记录

## 身份与边界

- `source_conversation_id`: `6a8f9ed2-a678-83ee-ac63-3fc48de531f8`
- `source_title`: `润色学术论文`
- `source_role`: `UNTRUSTED_EDITORIAL_INPUT`
- `integration_role`: `PROJECT_LOCAL_VERIFIED_DERIVATIVE`
- `scientific_claim_change`: `NONE`

该会话基于公开 GitHub 快照生成了仓库审查、英文重构稿、中文稿和通俗故事等交付。会话中的 `chatgpt-content-reference` 附件不能从当前 Codex 文件接口直接下载；随后请求的内联英文稿最终完成，但当前 thread reader 对单条长消息实行 20,000 字符截断，不能提供可校验的完整文件字节。本次因此以可读的完整审查结论、内联稿可见部分和 live repo 为三方输入，生成项目内可内容寻址的派生版本；没有把不可完整读取的附件冒充为逐字导入原件，也没有导入重复压缩包。

## 接纳的编辑判断

以下判断先与 live authority、S1/S2 records、manifests、代码和现有论文包核对后接纳：

- 论文主线从“终局审计清单”集中为 reference-solver qualification 与 failure-preserving stop；
- 标题更新为 *When the Reference Solver Fails First: Failure-Preserving Qualification Before PINN Training in an Electrothermal Defect-Transport Case Study*；
- 新增三个研究问题和四项有界方法学贡献；
- Q0、QN 和 reduced diagnostic 分别保持 implementation evidence、execution failure 和 non-scientific diagnostic；
- “没有训练 PINN”明确写成上游门失败后的预注册结果，而非缺失实验；
- 数据可得性更新为 2026-08-27 已完成的精选 GitHub 同步，同时保留 production dirty-tree 身份；
- PI-BSNet 的主引用更新为 2026 年 3 月 TMLR 记录，ICLR 2026 AI&PDE workshop poster 作为来源沿革保留。

## 新增或更新文件

- `paper/paper_v1/manuscript.md`：英文主稿的聚焦重构；
- `paper/references.bib`：C12 主记录更新；
- `paper/manuscript_zh.md`：与英文证据边界一致的完整中文稿；
- `paper/plain_language_story_zh.md`：30 秒故事、完整叙事、导师/审稿人/cover-letter 口径、可说/不可说清单和单页 PPT；
- `paper/paper_v1/README.md` 与 `paper/paper_v1/package-manifest.json`：包路由和内容寻址更新。

## 未接纳或未改变

- 不接纳把 `SYN_EDT_2D_V1` 写成已标定结构相变材料、VO₂/GST、潜热移动边界或实验器件模型；
- 不接纳 oracle、event、PINN/CTH、GPU、OOD、formal、SOTA 或期刊接收主张；
- 内联长稿可见部分提出了额外 `B01–B06` 背景引用，但完整匹配 BibTeX 受 thread-reader 截断而不可核验；本次不把这些新键写入正式稿，避免产生悬空或猜测引用；
- 不修改任何生产运行、S0/S2 合同、实验 ledger、图源数据或历史 No-Go；
- 不把源会话的编辑判断计入科学 evidence ledger。

## 来源核验

PI-BSNet 的正式记录采用 OpenReview TMLR 页面 `tHO2zEqmzm`；会话提到的 ICLR 2026 AI&PDE workshop 页面 `x1TWOnfTX8` 仅作为相关载体保留。其余 C01–C13 身份沿用已经过项目 S1 与论文终审核对的 `paper/references.bib`。
