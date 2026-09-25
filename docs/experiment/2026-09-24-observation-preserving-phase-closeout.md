# 观测保持相态补全：执行收口

任务PCM-20260924-OBSERVATION-PRESERVING-PHASE-01；2026-09-25完成。用户9月24日执行文件授权的阶段0—3已全部完成。**VERIFIED：NO_COMPLETION_INCREMENT。** 三臂对B0的A_w及独立物理资格均未通过；阶段4未触发。没有新种子、参考求解、扩窗、解冻T或额外优化。

N的W集合误差下降34.209%，相态RMS增加7.946%；G分别改善1.706%/1.374%，S分别改善17.109%/5.025%。N独立D相态残差平方为基点10.287倍，热增加7.324%；S相态BC为6.992倍。N/S不变性质及加热事件字段验证通过，严格失败保留。一个基础初始化、原参考、共同160×80读出。

完整[论文模块](../../paper/observation_preserving_phase_20260924/README.md)、[结果](../../paper/observation_preserving_phase_20260924/results.md)、[机器裁决](../../paper/observation_preserving_phase_20260924/evidence/decision.json)构成研究证据；本治理入口不代替数值记录。运行根outputs/runs/20260924-observation-preserving-phase，基点是旧B1 E/29，所有三个新臂都冻结该基点且零修正启动。

实际1800 Adam、600完整L-BFGS，训练13031正解/13031伴随；raw审计64正解，原生读出282正解。因设备参数遗漏，三臂训练实际为同一CPU，合计34.557分钟；审计/读出为CUDA。既有轨迹未重跑，执行源码已单独保留，当前入口修复并有零更新回归。局部profile/评分内存异常均按最小范围补齐；原公式与权重不变，评分恢复使用只读磁盘映射。

云端最终退出0；完整回收校验成功，结束约47秒后请求关机，返回0并确认SSH拒绝连接。[公开关机摘录](../../paper/observation_preserving_phase_20260924/evidence/compute-closure-public.json)不包含连接凭据。完整原生数组本地可用，未新增外部访问；P03保持开放。未执行commit/push/PR。

**SUPPORTED_INTERPRETATION：**观测保持空间与理论约束成立，但本配方/预算未取得合格相态补全。没有触发确认申请，不自动把样条的局部收益作为PINN目标完成。下一步只供作者基于现有证据决定论文定位或另立不同研究问题；本轮没有新增科研执行授权。P02、严格事件、formal OOD和材料验证仍未补齐，旧阴性和旧E/F配置收益不改写。

2026-09-25 后续交付授权：用户要求提交本轮重要成果至云端，见[发布记录](../notes/2026-09-25-observation-preserving-phase-results-release.md)。上文未发布措辞保留科研收口时点身份；此次发布不改变科学裁决与 P03 数据边界。
