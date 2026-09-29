# 条件热响应与迟滞本构闭合交付

任务 `PCM-20260928-CONDITIONAL-THERMAL-CLOSURE-01` 已完成批准范围。

**VERIFIED：**40条主响应及40条求积核对完成，最大温差1.14e-13 K；10条来源历史逐位复现，20条无反馈历史重放完成。五工况、两来源步长及全部原生数组保留。

**SUPPORTED_INTERPRETATION：**误差已进入动态温度和本构闭合；唯一下一建议是聚焦热输入时序与合法状态估计，采用同信息传统物理估计为强基线。尚未建立用途合格线、PINN增量、连续真解认证或实验/二维材料验证。无自动后续计算。

- [完整研究报告与全角色表](results-report.md)
- [固定12.5 V展示与全部工况索引](figures-index.md)
- [冻结配置](config.json)、[实际执行记录](execution.json)、[唯一后续决策](decision.json)
- [完整温度表](results/temperature.csv)、[三层差分](results/decomposition.csv)、[本构/原电流闭合表](results/closure.csv)
- [历史与反转明细](results/history-diagnostics.json)、[数值资格](results/numerical.csv)、[来源步长敏感性](results/source-step-sensitivity.csv)
- [复算与真实依赖](reproduction.md)、[数据保留状态](data-handling-record.json)
- [仅更新访问段的新主稿PDF](manuscript/manuscript.pdf)、[DOCX](manuscript/manuscript.docx)、[权威Markdown](manuscript/source/manuscript.md)
- [访问段修改说明](access-change.md)、[既有请求的发送确认项](author-contact-status.md)

旧稿科学结论不变。旧电路V/I评分子集已公开，旧二维全场P03仍开放。测量请求未发送；本轮没有使用GPU、投稿或读取实验/留出数值。

## 后续发布状态

用户在科研收口后另行明确批准包含科研数组、稿件和运行产物的170文件完整批次公开推送。本轮派生交付已随[成果提交 `d068bdf`](https://github.com/ghy001122/PINN-PCM-SCI/commit/d068bdf466ccc40f73a2b4c11e5ade7179fd9eeb)发布并核验远端分支；范围和限制见[发布记录](../../docs/notes/2026-09-29-conditional-thermal-closure-release.md)。该发布使本目录派生数组、表格、图件和源码可通过Git获取；完整原始T/R/g/H源轨迹及旧二维PINN全场仍未包含，因而不关闭全论文P03，也不产生新科研执行授权。
