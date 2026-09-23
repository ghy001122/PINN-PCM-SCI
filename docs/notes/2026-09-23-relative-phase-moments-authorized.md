# 相对相态残差与时间矩：本轮授权及来源整合

任务 `PCM-20260922-RELATIVE-PHASE-MOMENTS-01`；执行日期 2026-09-23。
用户明确要求吸收三份评审／规划并执行 `E:/PINN-PCM/CODEX_Execution_Instructions.md`。该当前授权 supersedes 旧 B1 收口中的后续禁止执行范围，但不改写旧结果。完整输入指令存于本轮运行目录 `input/execution-instructions.md`。

本地阶段 0—2直接执行；已授权GPU实例通过公钥连接确认，V100 32GB，故按本轮指令，数值前置门通过后可执行阶段3，无费用上限。执行完回收结果并及时关闭。阶段4确认、额外case、新参考、stress、commit/push/PR及公开上传均未授权。

论文去向：同一二维电—热—相态离线缺测重建中的相态目标适配与消融。H_R/H_delta/H_T/H_M均为 HYPOTHESIS；不把代数恒等式或实现通过称为性能证据。唯一开发初始化29；复用合法B1观测父态，D/P/L/R/I/RI/RIM/G各600 Adam及100次完整L-BFGS评估，先锁定全部终点再按原参考统一评分。没有新实体或formal OOD；新初始化和full-label确认另行批准。原阈值、窗外代价、严格事件均保留。

三份材料的取舍：采用 Gemini 对任务必要性、强基线、连续误差和简洁表达的提醒；不采纳“梯度冲突已证明”“物理无用”或通过制造插值崩溃取得优势。Assessment的分阶段建议是评估提案，实际执行采用用户指定文件中的单seed八臂预算；不混入其双seed四臂提案。Research_Plan的相态坐标与时间组织方案按指定执行文件落实，独立sanity附件不作为项目测试或真实训练证据。

停止条件：16/32求积仍超过目标1%或梯度范数5%则 QUADRATURE_UNRESOLVED；校准不可辨或非有限则 INVALID；预算不完整则 BUDGET_INCOMPLETE；有效八臂无增量则 NO_INCREMENT_WITHIN_SCREEN_BUDGET。不得救援扫片宽、调阈值或换seed。旧B1原A_w 0/12、两个初始化、B_E反例及六臂负续训全部保留。

来源差异：完整latent residual已见 `E:/PINN-PCM/PINN_PCM_后续研究总规划_20260910.md` §7及 `决策报告.md` 条件A，不是新创意。新增适配为固定观测clip尺度的平滑有限logit、与原热块分离的共享phase panel积分、匹配近邻控制。结果之前不宣称算法贡献成立。

- Feng et al., Integral regularization PINNs for evolution equations, arXiv:2503.23729v1, §3.1 Eq.(10)—(20), https://arxiv.org/html/2503.23729v1 。已读原区间端点残差与局部残差组合；I为本对象适配，不移植自适应采样，也非原论文完整复现。
- Kharazmi et al., VPINNs, arXiv:1912.00873, https://arxiv.org/abs/1912.00873 。核对摘要/元数据，Legendre测试及分部积分已有先例。
- Saleh et al., ICML2024, PMLR235:43077–43111, https://proceedings.mlr.press/v235/saleh24a.html 。核对原会议摘要中随机积分替代后平方的偏差；本轮明确使用离散Gauss目标，不移植delayed target。
- De Ryck et al., ICLR2024, arXiv:2310.05801, https://arxiv.org/abs/2310.05801 。预条件化为相关先例，不给当前非线性目标提供现成收敛保证。

实现依据上述数学接口独立编写，不复制论文代码。Word评审完整读取正文及表格，确认无嵌入图、批注；本机bundled运行时不含LibreOffice，未渲染版面，不声称核验页码。指定read_thread工具本轮不可用，历史任务内容未作为当前授权或证据。
