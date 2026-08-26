# 0024：科学运行前冻结来源候选顺序并隔离 oracle 案例角色

- `status`: `ACCEPTED`
- `accepted_at`: `2026-08-22`
- `decision_scope`: `FUTURE_SOURCE_SCAN_ORACLE_INDEPENDENCE_AND_CASE_ROLES`
- `claim_status`: `PROPOSED_METHOD_NO_NUMERICAL_EVIDENCE`

有界 VO₂ 来源扫描在找到三个合格候选或预声明查询族耗尽时停止；一个合格活动对象即可提出路线，后备不足保持为空，不得降低来源门，零个合格对象才可申请扩大材料范围。活动对象与后备顺序必须在首次科学运行前冻结，只有新的来源事实触发既定否决条件时才可删除或重排，不能根据活动路线结果推测哪个后备更容易产生 KC 优势。

作者代码可以作为参考生成器，但合格 oracle 还必须具有独立的方程—代码核对、事件/守恒 evaluator、时空离散收敛审计，以及与生成器分离的 PINN 残差实现；只有出现实质不一致时才建设第二套完整 solver。公开参考 case 只用于来源复现/资格化，不能进入 formal；完整案例必须分入互斥的来源资格化、方法开发、未触碰 formal 和未触碰储备角色，同一几何、协议或轨迹的时间片不得跨池。本 ADR 不授权来源扫描、下载、实现或运行。
