# 下一研究提案

- `phase_id`: `PHK_V23_LF11_FULLGRID_CONFIRMATION_COMPLETE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `VALID_FULLGRID_AND_TWO_CLEAN_PAIRS_COMPLETE`
- `next_research_execution_authorized`: `false`

上一执行计划已[归档](../../archive/2026-09-14-lf11-fullgrid-executed-plan.md)。

## 最优先的下一科学决策

PROPOSED_NOT_AUTHORIZED。

当前优先问题是：训练期耦合的增量能否在一个完整新协议上同时经受锁定soft＋projection和同求解层B_E；其中B_E必须保留，因为本轮seed43对它未达到10%门。两个干净配对已支持对soft的B层，继续救同一nominal或seed43的单门，信息价值较低。

1. 冻结一个仅改变脉冲间隔的新完整协议，保留材料、方程、几何和其余脉冲参数。先确定新协议本身及参考生成/数值有效性范围，不读取既有sealed stress选case；固定相同稀疏掩码规则和全部评价。新case自身support训练明确称重建/适配，不能称零样本或无观测泛化。

2. 使用当前冻结底座和共同拟合配方，保留两个预声明初始化、每对E/F_raw及同层B_E；优先沿用每seed2400 Adam＋600次父态拟合、两臂各1500＋300的上限，推理/求解预算按新协议非零时刻数在执行前明确。本提案尚未授权参考生成或这些训练。

3. 先判断E对两个强对照是否分别通过原A/B与非劣条件，再判完整双周期。若只有对soft增量而对B_E仍不足，收窄为约束实施方式的有限收益，不继续堆模块或更换较弱基线；若出现反向结果则保留并停止扩矩阵。首图并列两个协议的每seed相态、电流、功率与B_E，事件代价另表，避免按版本罗列结果。

4. 把当前论文主线固定为“训练期电学约束＋一致焦耳接口→共同投影下的状态/器件增量→空间积分反事实→干净初始化→完整新协议”。隐式VJP的唯一因果作用、剩余热/phase PDE独立必要性及材料标定仍UNKNOWN，不为这些尚未建立的主张自动增加对照。

论文以电学约束实施和一致局部焦耳耦合为主体，以匹配增量建立贡献。新物理、材料、掩码、协议、参考生成及formal OOD需独立明确范围，不能从本提案推断授权。
