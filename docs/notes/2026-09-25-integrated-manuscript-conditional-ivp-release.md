# W+A 连续主稿与条件演化成果发布

2026-09-25 用户另行明确要求将本轮重要交付结果及研究进程提交至 `ghy001122/PINN-PCM-SCI`。沿用 `codex/paper-revision-results`，基线为 `e2e14b5ce390de930646e1cba9a606a8191cff80`。本授权 supersedes 本轮此前 Git 未授权措辞；科研执行保持 CLOSED，后续执行授权为 false。

- 发布状态：`READY_FOR_PUSH`，提交后核验远端。
- 任务：`PCM-20260925-INTEGRATED-MANUSCRIPT-FEASIBILITY-02`。

## 交付与研究进程

[交付入口](../../paper/paper_revision_20260925_integrated/README.md)包含16页连续主稿、52页完整补充的 Markdown/PDF/DOCX、权威正文源、完整图表、修改说明、主张—源表—图件映射及真实构建依赖。[条件演化报告](../../paper/paper_revision_20260925_integrated/conditional-evolution-report.md)配有[紧凑执行证据](../../paper/paper_revision_20260925_integrated/evidence/conditional-phase/README.md)，覆盖逐内部步记录、三个残差层级、两热口径、接缝、开发参考、活跃支持、工程故障恢复及回收关机。发布同时包含必要实现、冻结配置、工程测试和实验索引。

**VERIFIED：** 两条轨迹共3168接受主步、6361次Newton/线性求解，三个数值门通过；两热口径均在预算内。全域 Ephi_D_80 为 B0 0.0669435757、粗步0.0207595909、细步0.0207429571，ROI方向一致。非零接缝仍存在；细步活跃支持召回率由0.974612降至0.763383，精确率由0.410817升至0.890215，不能只呈现有利指标。

**SUPPORTED_INTERPRETATION：** `CONDITIONAL_IVP_SUPPORTS_FURTHER_WITNESS_SEARCH`；唯一建议是考虑另行审批的有界原修正族证人搜索。**UNKNOWN：** 原C²修正族可行性与神经方法特有相态增量。P02、严格双周期、材料验证及P03完整数组外部访问保持开放。

本次不重跑科研或文档渲染。完整场数组、模型检查点、参考数组、部署回收包、连接脚本和可再生成的页面缓存不纳入精简发布。紧凑证据与本地原件的逐项映射见 publication-map.json；原运行清单保留执行时路径，不把精简发布冒充完整重现闭环。实例回收与关闭沿用已核验的执行记录。

## 发布验证

发布前文档门禁返回 `DOCUMENT_CONSISTENCY_VALID`；限定发布清单为301个文件，导航目标完整，紧凑证据副本、科研源码及已检查PDF身份与原记录一致，实际稿件构建输入身份核对通过。无关外部 Skill 和其他工作区改动不纳入提交。新增限定路径的 Git 属性，保留稿件与证据字节身份；继承图件SVG的合法路径空格及原始日志尾空行不作正文格式错误。最终远端身份核验记录随后补齐。Git发布不构成新增科学增量、数据完整公开或投稿。
