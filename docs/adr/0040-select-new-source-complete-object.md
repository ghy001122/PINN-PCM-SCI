# 0040：新对象来源筛选后接受有界不选择对象

- `status`: `ACCEPTED`
- `accepted_at`: `2026-08-25`
- `decision_scope`: `NEW_SOURCE_COMPLETE_OBJECT_BOUNDED_NO_SELECTION`
- `evidence`: [`2026-08-25 新对象 source-complete 审查`](../references/2026-08-25-new-object-source-complete-review.md)
- `claim_status`: `BOUNDED_SOURCE_CONTRACT_NO_GO_NO_METHOD_EVIDENCE`

## 背景

当前阶段允许在最多新增 20 项一手来源、深审最多 4 个对象家族的范围内选择一个来源完整的二维及以上氧化物器件对象；任一决定对象身份、物理参数、合法重建、机器可读验证量或完整实体拆分的硬缺口都必须拒绝候选。阶段保持 `0 object build / 0 solve / 0 training / 0 PINN / 0 GPU`，对象通过前不得预选 CTH、cKC 或其他方法。

本轮复用既有 VO₂ 与 related-oxide 来源账本后，只把具备 version of record、作者固定 COMSOL 资产和明确仓库许可的 2025 Pd/Ta₂O₅/TaOₓ/Pd 家族提升到深审。固定模型树自身的二维器件、电—热—vacancy 方程链、IC/BC、界面、本构、单位和绝对时间定义可读，但论文与固定模型对 vacancy hopping distance `a` 给出互不相容的 `0.32 nm` 与 `0.16 nm`。该参数同时进入扩散与场驱动跃迁速度；同一来源家族没有勘误、换算或版本说明。

固定 `.mph` 另有 `SolutionNative totalSize = 0`、没有 raw 数值导出，以及六个文件名只有五个唯一内容且仅覆盖同一器件的稀疏 `K1/K2` 变体。这些是独立次级失败，不改变最早的 paper–model alignment 否决。

## 决定

接受 `NEW_OBJECT_SOURCE_COMPLETE_BOUNDED_NO_GO`，并记录：

- `object_selection_status=NO_OBJECT_SELECTED`；
- `method_selection_status=NOT_REACHED`；
- 当前新对象来源筛选停止，不继续填满来源或家族预算；
- 不选择 Pd/Ta₂O₅/TaOₓ/Pd、CTH、cKC 或任何其他对象/方法进入实现；
- 不重开 HFO-NP-v1、Q-POP、R1、R2/FerroX、R3 或其他历史路线；
- object build、solver、PINN、training、pilot、formal OOD、GPU 与付费计算继续关闭。

## 被拒绝的替代方案

1. **采用论文的 `a=0.32 nm` 并忽略模型值。** 拒绝，因为这会把纸面版本单方面指定为 canonical，而作者固定模型的实际输运速度不同。
2. **采用模型的 `a=0.16 nm` 并解释为半跳距。** 拒绝，因为同一来源家族没有这种定义；该解释会补造决定事件时标的物理语义。
3. **先重新求解 `.mph` 或补做 clean-room oracle 再决定。** 拒绝，因为当前没有数值执行授权，而且新结果不能消除最早的来源—模型参数冲突。
4. **继续搜索直至用满 20 项来源或 4 个家族。** 拒绝，因为预声明规则要求在决定性失败形成后收口，不能为凑预算扩展路线。

## 后果

该决定只是否决本轮单一候选家族及其三项固定一手载体，不是否定 TaOₓ、氧化物忆阻器、传统求解器或 PINN 的一般可行性。当前没有可信 oracle、方法 Go/No-Go、论文首图或可写正向方法主张；保留的交付是可复核的来源不一致负证据。

只有新的明确 PLAN、用户批准，以及足以改变最早失败的新一手资产（例如作者勘误或固定模型版本说明）才能重开该候选。单独补回 solution payload、增加案例或更换方法不能覆盖本 ADR。
