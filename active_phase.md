# 当前阶段

- `phase_id`: `PRE_RESEARCH_INITIALIZED`
- `phase_name`: Codex 项目初始化完成，等待研究启动指令
- `lifecycle_state`: `ACTIVE`
- `authorization_scope`: `GOVERNANCE_ONLY`
- `claim_status`: `NO_SCIENTIFIC_CLAIMS`
- `effective_date`: `2026-08-16`

## 当前允许

- 读取和维护项目入口、规范、状态与计划文档；
- 对项目文件做一次与真实改动直接相关的语义一致性检查；
- 向用户报告初始化结果和待决事项。

## 当前不允许

- 正式文献调研或 idea 筛选；
- 选择材料、器件、物理方程、PINN 架构或论文主张；
- 创建研究数据、求解器、训练代码、实验配置或论文科学内容；
- 运行数值求解、训练、参数扫描、消融或 OOD 评估；
- 将治理文件或 Git 状态表述为学术研究成果。

## 阶段事实

- 本阶段只建立 Codex 项目骨架。
- `formal_research_started = false`
- `scientific_execution_count = 0`
- `scientific_evidence_count = 0`

## 退出条件

只有用户明确指示开始正式学术研究，并确认或接受一个有界的 Phase 0 研究计划后，才能更新本文件进入研究阶段。更新阶段状态本身不代表任何科学 claim 成立。
