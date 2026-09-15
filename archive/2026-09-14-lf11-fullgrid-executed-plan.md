# 全网格软电学反事实与干净确认

- `phase_id`: `PHK_V23_LF11_FULLGRID_AND_CLEAN_CONFIRMATION`
- `lifecycle_state`: `EXECUTE`
- `blocker_id`: `NONE`
- `claim_status`: `VALID_FULLGRID_B_SIGNAL_CLEAN_PAIRS_PENDING`
- `next_research_execution_authorized`: `true`

执行依据：[用户完整指令](../notes/2026-09-14-lf11-fullgrid-authorized-sprint.md)。旧建议已[归档](../../archive/2026-09-14-lf11-v30-next-plan-superseded.md)，最新用户文件优先于报告。

1. F_full从V28 E0出发，仅电学残差改全3200单元均值；原128抽样、时刻和T/phase目标不变。1500 Adam＋300完整评估，推理解≤278。
2. 回收并确认GPU关闭后评分；保留network/projected及所有旧控制，按原A/B与完整事件解释。依据共同projected器件Pareto和原场非劣选唯一soft；不唯一即停止扩训。
3. 唯一soft确定后，29/43从零初始化，各2400 Adam＋600观测评估（V/T/phase各200），再共享父态和一次校准分叉E/soft，各1500＋300。默认不使用可选seed救援，不恢复旧V门。
4. 总上限12300 Adam＋2700完整评估；训练正/伴随各54000，校准审计各1000，推理1390。旧seed17与新seed分开，非新case/formal OOD。
5. paper_v31按事后修复、共同读出、全空间反事实及条件干净确认组织；不将通用算法分别包装创新。剩余PDE独立必要性UNKNOWN。

阶段A执行进展：F_full有效终点及全部评价已保存，E仍通过同一B层；F_raw已按冻结规则唯一锁定。阶段A GPU已回收关机；用户已确认重新启动，当前继续已授权29/43两组配对，不重跑A，不新增授权或比较臂。整轮尚未完成。
