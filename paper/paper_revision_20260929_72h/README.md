# 72小时成稿与联合重构交付

任务：`PCM-20260929-72H-MANUSCRIPT-JOINT-01`。本轮完成二维主稿整合和一个固定联合重构对照，保留全部历史反例与不利证据，不追加研究路线。

**VERIFIED：**在同一共同RC读出下，N/F/S的完整电流联合RMS分别为 **116.823 / 102.533 / 171.691 μA**。N比F差13.94%；比S低31.96%，但热非劣未通过。首轮联合门未通过，第二初始化不触发。N/F各完成600 Adam更新及100次L-BFGS完整评价；S在187次评价后因Wolfe线搜索失败回滚，保存第75个接受步，未宣称收敛或用尽700次。

**SUPPORTED_INTERPRETATION：**本轮固定神经消元原型没有建立所需联合增量，结果完整进入补充S25。它不改写原二维E/F与E/F_cov配置收益，也不构成神经表示普遍无效或真实材料验证。唯一后续动作是作者终审与稿件/数据访问安排。

| 交付 | 入口 |
|---|---|
| 连续主稿 | [PDF](manuscript.pdf) · [DOCX](manuscript.docx) · [Markdown](manuscript.md) |
| 完整补充S1—S25 | [PDF](supplement.pdf) · [DOCX](supplement.docx) · [Markdown](supplement.md) |
| 本轮量化结果、分项门及成本 | [结果报告](results-report.md) |
| 完整历史与RC梯度、事件边界 | [方法说明](gradient-method-note.md) |
| 本轮独立保存数组复算 | [最小评分包](scoring-subset/README.md) |
| 主张—源表—图件 | [证据映射](manuscript-evidence-map.md) |
| 真实构建与视觉核验 | [构建记录](manuscript-build.md) |
| 作者终审 | [一页清单](author-final-checklist.md) |
| 执行来源与冻结约定 | [用户指令](instructions.md) · [综合评估](assessment.md) · [配置](config.json) |
| 接受终点、优化器、完整数组及实际源码 | [运行目录](../../outputs/runs/20260929-joint-reconstruction/) |

稿件改动集中于主文6.3的一段解释和补充S25：统一PCHIP/CS/条件热证据，保留全角色表、固定12.5 V图，明确储能分配交叉项与热—电流闭合恒等式的条件，并给出联合方法、真实结果与失效分项。未重做历史条件热积分或历史大型评分包。

三端点锁定后才在本地读取评分源；最小包不提供训练入口或神经AD残差重算。实例产物已回收、传输校验及数组/检查点可读性核验通过。2026-09-29 08:05 UTC关闭命令成功，后续SSH拒绝连接，见[关闭记录](../../outputs/runs/20260929-joint-reconstruction/shutdown.json)。首次关闭请求因SSH连接被关闭未执行，原失败记录已保留。

实际训练输入、日志、接受态与数值缓存保留于本地和实例数据目录 `/root/autodl-tmp/pinn-joint-20260929`。关机后完成的本地评分包、报告和最终稿件**待下次已授权实例会话同步**；不为小文件复制重启GPU。完整二维场/检查点的外部获取P03仍开放，本轮新产物未发布Git、未公开上传、未发邮件或投稿。

权威文本是 `source/manuscript.md` 与 `source/supplement.md` 及其包含的S25文本；根目录Markdown/DOCX/PDF为统一构建产物。数据、许可、真实作者信息和投稿批准各自保持实际状态。
