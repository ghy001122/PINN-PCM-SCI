# 2026-08-29 PHK-V2.2R 近期研究策略整合

## 身份与边界

- `source_conversation_id`: `6a8f9ed2-a678-83ee-ac63-3fc48de531f8`
- `source_title`: `润色学术论文`
- `source_role`: `LIVE_READ_DISCUSSION_CONTEXT_NOT_PRIMARY_EVIDENCE`
- `integration_role`: `PROJECT_LOCAL_INTERPRETIVE_GUIDANCE`
- `status`: `INTEGRATED_WITHOUT_NEW_AUTHORIZATION`
- `scientific_claim_change`: `NONE`

本记录整合该实时会话最近几次关于一周冲刺、方法组合、结果分支、止损措施和论文故事的讨论。会话提供的是研究策略上下文，不是文献原始来源、运行事实或独立授权。发生冲突时，`active_phase.md`、`PROJECT_STATE.md`、V2.2R program/method contracts、ADR 0047 和 live plan 依次约束本记录；本记录不得改变当前 blocker、截止时间、预算、sealed 规则或历史 No-Go。

## 已纳入当前路线的原则

1. **开发功利、确认冻结**：nominal 开发阶段可以在合同上限内调参、迁移和重组模块；candidate freeze 后不得根据 stress 结果修改方法、阈值、损失、预算、seed 或评价口径。
2. **S-first 最短关键路径**：strong raw、field-selective anisotropic MF、physics sampler 与 MF+sampler 构成主体；strict PHA 只做一次全导数 100-update 探针，失败即退出关键路径。
3. **功能槽而非模块堆砌**：表示负责场与轴向尺度分配，采样负责稀缺 phase/Joule support，训练协议负责时序刚性，device-QoI extractor 负责把场误差传递到器件输出。只有可归因的协同增量才能写入贡献。
4. **一次 A→B**：只有全部 physics-only A arms 都不具基本求解能力时才进入 sparse-reference-assisted B；A 有 competence 但无 proposed 增量时直接 No-Go，不能借 B 继续寻找正结果。
5. **四种证据故事**：真实结果只可支持主要精度、sharp-transition regime 条件优势、accuracy–cost Pareto 或 sparse-data physics-informed increment。标题、摘要和贡献随证据分支调整，结论不得先于结果。
6. **低风险增益优先**：Sobol uniform floor 和确定性 device-QoI 已进入当前方法/评价设计；same-arm nominal-to-stress warm start 仍只是 program contract 允许的共同协议 pivot，不自动成为默认正式协议。

## 十类止损思路在当前合同中的映射

| 止损思路 | 当前允许的最窄用法 | 禁止越界 |
|---|---|---|
| 1. 功能等价替换 | 只在 nominal、冻结配置数和最多两个 functional pivots 内替换表示或采样槽 | stress 开封后换模块或新增研究轴 |
| 2. 小型结构魔改 | 只做可归因、可计算匹配的场选择、残差分支或 interface/background 分工 | 无界网络搜索和事后扩大预算 |
| 3. 指标重构 | 使用已冻结的 primary、co-primary、guards、secondary 与 device-QoI 层级 | 看结果后换阈值、删不利指标或“任一变好即成功” |
| 4. 条件优势 | 若 stress 显示清晰 regime 差异，可写 bounded regime-aware claim | formal OOD、材料或器件泛化 |
| 5. Pareto 转向 | 由实测精度、wall time、显存和参数量形成 accuracy-cost 边界 | 用 CPU 预检或估算冒充 GPU 公平证据 |
| 6. 协同架构 | candidate freeze 前可在冻结槽位内采用共同 continuation/staggered 协议 | 为某一 arm 单独加救援协议破坏公平性 |
| 7. 主模块降为辅助 | 只有消融证明独立增量时才保留；strict PHA 未过门即删除 | 失败模块改名后继续占据 headline |
| 8. 参数化统一模型 | 作为稿后多 case/geometry/protocol 扩展 | 本周新增条件化模型、SyncNet 或第二物理对象 |
| 9. 迁移与 warm start | 仅可作为所有正式 arm 共用且预先冻结的训练协议 pivot | 从 sealed reference、标签或误差场迁移 |
| 10. 降级路线 | 全部 A 不 competent 时只进入一次 B；B 再失败即停止 | 开启 C、无限救援或追逐预期正结果 |

## 论文故事与应用边界

当前最稳的故事链是：二维电—热—相态器件中的关键相区和 Joule hotspot 占比很小，普通 PINN 容易把容量与 collocation 点浪费在平滑背景；FS-PJAMF-PINN 通过场选择性各向异性频带和 phase/Joule-aware sampling 把固定预算投向局域多尺度结构，再用端电流、能量、相区面积、峰值温度和事件恢复检验局部场改善是否形成器件级价值。

物理对象必须始终称为受 wall-type PCM 启发的透明、无量纲、简化二维电热—相场数值 benchmark。它可用于快速方法验证、局域相变场代理和后续器件设计研究，但不是 GST/VO₂ 样品校准、实验数字孪生或真实器件验证。

TEGNet 式纯输出代理、SyncNet/阵列组合、参数化多几何模型、逆向设计和三-seed/formal-OOD 完整证据矩阵均属于稿后升级，不进入当前一周关键路径。若未来启用，必须重新核验原始来源、建立独立计划和获得对应授权。

## 后续使用规则

处理 V2.2R 的方法替换、止损、故事分支或稿后升级时，先读当前权威链与机器合同，再读本记录。会话中的文献判断只能作为待核验线索；正式论文引用必须回到原始论文、官方代码和许可证。若本记录与新证据冲突，保留本记录作为 2026-08-29 的策略快照，并用新的 ADR、实验记录或笔记显式覆盖，禁止静默回写。
