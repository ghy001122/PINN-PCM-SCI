# 观测保持相态补全重要成果发布

2026-09-25 用户明确授权将本轮重要交付结果及研究进程提交至 `ghy001122/PINN-PCM-SCI`，沿用 `codex/paper-revision-results`，继承 `a96303c2110ae1a79984ed7dcddf0c01ab07bec1`。

- 发布状态：`PREPARED_PENDING_PUSH`；推送后另行记录远端核验。
- 科研状态：`CLOSED`；`next_research_execution_authorized=false`。
- 科学裁决：**VERIFIED：NO_COMPLETION_INCREMENT**。

## 交付位置及证据边界

[论文模块与结果入口](../../paper/observation_preserving_phase_20260924/README.md)包含理论及方法边界、可直接入稿的英文段落、完整连续指标和20对裁决、两周期事件、独立D及全程物理审计、误差分解、真实成本、图件和来源。相关实现位于 `pinn_pcm_sci/phk_v23_observation_preserving_phase*.py`，冻结配置和针对性测试分别位于 `configs/phk_v23/` 与 `tests/`。

[执行授权与评审整合](2026-09-24-observation-preserving-phase-authorized.md)和[实验收口](../experiment/2026-09-24-observation-preserving-phase-closeout.md)保留研究问题、强控制、预算、停止条件、实际进度及偏差。公开证据保留零更新资格、终点锁定、评分及裁决、不变性验证、设备偏差和脱敏关机事实；实际执行的旧runner与修复后的当前runner分别保存，避免把未来CUDA修复冒充本次CPU轨迹。

**VERIFIED：**三臂1800 Adam/600完整L-BFGS完成，N/G/S均未通过原A_w或独立D物理资格。N集合误差下降34.209%，相态RMS增加7.946%，D内raw相态残差平方为基点10.287倍。N/S观测保持和加热事件不变性质成立，严格双周期失败保留，阶段4不触发。GPU用于后续审计/读出，完成后已校验回收并关闭。

本次发布是精简证据与源码交付；完整原生时空数组、参考输入、模型权重、优化器状态和部署/回收包仍本地保存，P03未闭合。连接资料、机器专用回收脚本及工作区无关改动不纳入提交。P02方法增量未建立，不以Git发布替代科学结论。

## 核验

科研收口已有聚焦、继承接口及设备传播回归记录；本次不重新运行科学计算。发布前核验文档一致性、提交差异和精确文件清单，推送后核对远端提交身份。本次授权不新增训练、求解、GPU任务或投稿。
