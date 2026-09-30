# 一页主张—证据—限制表

科学基线：`f4e6202`。数值事实为 **VERIFIED**；跨配置解释为 **SUPPORTED_INTERPRETATION**。完整来源见[证据映射](manuscript-evidence-map.md)，显示值不改历史判据。

| Claim | Evidence | Limitation | Manuscript location |
|---|---|---|---|
| C1：训练时将grounded电学子问题与神经T/φ状态耦合。 | 共享面电阻、局部焦耳沉积及完整一阶隐式反馈的实际实现。 | 特定物理接口适配；不声称发明隐式微分或通用solver-in-the-loop。 | §3.1 Neural states and electrical elimination；§3.2 Consistent local Joule deposition and remaining residuals |
| C2a：共同末端修复不能消除所测E/F状态与器件差异。 | 两协议、两seed的四对；同一参考／读出下比较相态、I、P，完整器件门保留。 | 分别离线拟合；非formal OOD。配置变化不隔离VJP因果；器件门不等于严格双周期。 | §4.1 Four paired full-label comparisons；§6.3 What the experiment identifies |
| C2b：F_cov未复制E的联合收益。 | shorter／spatial／fine，seed29/43电流相对改善约52.68%／66.55%，相态同表；完整A/B另附。 | 混合测度覆盖增强，非纯覆盖或严格匹配；12条敏感性行来自两个终点。 | §4.2 Coverage-enhanced soft electrical control |
| C3：额外内部残差及对强插值的优势有明确边界。 | E/D_E具名配对；original/43/fine的B_E反例同时保留old/refined/spatial参考。 | D_E仍含物理反馈；B_E信息使用不同。不能推出物理无效、等价或普遍排名。 | §4.3 Matched removal of the interior residual package；§4.4 The strong interpolation counterexample |
| B1：改善端口及恢复事件不保证内部相态质量。 | 完整窗口／窗外／全程指标及事件；相态与严格事件失败相邻呈现。 | 只缺W内相态；V/T及未来相态仍可用，非在线预测。 | §5 Port improvement does not guarantee internal phase reconstruction；S20 |
| 计算代价与辅助结果限定适用范围。 | 记录的父态／校准／训练／读出计数；S21—S25完整不利结果；VO₂ N/F/S联合门失败。 | 无跨环境加速比；集总辅助结果不改写二维收益，不构成材料或新算法验证。 | §4.5 Accuracy and actual numerical work；§3.5、§6.3；§6.4 Diagnostic studies beyond the primary 2D reconstruction task；S21—S26 |

**复算与访问：**新核心ROI及I/P包已完成[本地隔离复算](core-scoring/independent-verification.json)，十个候选、两协议spatial参考的30/30指标通过；全部1001时刻，原160×80相态的3872个ROI单元及fine电学读出。原科研数据根与旧bundle均禁访问，缺输入测试通过，回退0次。原完整A/B仅冻结复制，未重新裁决；未执行检查点推理、神经AD重算或再训练。基线精选稿件／源码及具名辅助评分子集已公开；本轮新包与稿件尚未公开，完整二维场／大型检查点访问仍未闭合，P03保持开放。
