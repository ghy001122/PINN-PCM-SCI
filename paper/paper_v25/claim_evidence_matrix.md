# 主张—证据—边界

| 主张 | 状态 | 证据 | 界限 |
|---|---|---|---|
| 温度输出区间不足以解释原主要拟合缺口 | VERIFIED | evidence/s0.json; 包络下界0.0015038294，原可见误差0.178232659 | 不证明有限网络能精确拟合全部点；343点不可精确匹配 |
| 可见温度拟合改善93.62%，相态保持 | VERIFIED | evidence/s1-result.json; fit-telemetry.jsonl | 训练/开发误差；优化与适配器未独立消融 |
| 完整nominal参考上温度和能量误差也改善 | VERIFIED | evidence/evaluation.json; tables/fixed-endpoints.md | 既有已观察nominal，不是盲测或OOD |
| 剩余V误差偏向底部 | VERIFIED / SUPPORTED_INTERPRETATION | 最低两z层贡献53.17%平方误差、占16.25%测度 | 分布事实已验证；边界/优化/表达的唯一根因未证明 |
| 顶部电流不能替代双电极与耗散一致性 | VERIFIED | 顶部NRMSE0.07218，底部7.81254，能量误差0.49201 | 固定离散读出；相关指标不能重复包装为独立物理发现 |
| 新的PDE/归一化方法获得增量 | UNKNOWN / NOT_RUN | S1仅V拟合门未过，全部后续未运行 | 不是已运行失败，也不支持否定这些方法 |
| Fourier适配器有独立方法创新 | UNKNOWN | 只有顺序开发结果，无等预算无适配反事实 | 通用技巧算共同底座，不列独立创新 |
| 氧化物材料实验或formal OOD已验证 | UNKNOWN / NOT_ESTABLISHED | 本轮无对应证据 | 保持合成二维对象身份 |
