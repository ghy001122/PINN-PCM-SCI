# 通俗学术故事：参考答案自己都没过关，就不该急着训练 PINN

## 30 秒版本

我们原本想研究 PINN 能不能更好地模拟一个二维氧化物开关器件。但 PINN 要训练和比较，首先得有一份可信的“参考答案”。我们没有默认传统求解器输出就是真值，而是先冻结一整套资格考试。两个公开来源对象都无法在同一来源链里闭合；于是启用透明合成对象。零驱动检查通过，但第一个真正受驱动的参考求解在预先规定的 Newton 上限内失败。我们按规则停止，没有调参数救结果，也没有训练 PINN。论文的价值不是“PINN 赢了”，而是证明了：参考解也必须先被验证；参考求解器先失败时，保留失败比制造不可解释的漂亮曲线更科学。

## 完整故事

### 1. 最初想解决什么

PINN 研究常见的叙述是：先用传统求解器生成参考数据，再训练网络，最后比较误差。但这里隐藏了一个前提——传统求解器产生的参考过程必须可信。如果对象说明不完整、边界条件含隐含默认值、数值结果没做收敛检查，或者所谓“开关事件”只是事后挑出来的，那么网络误差再小也没有清楚的科学含义。

我们面对的还是一个难对象：电流产生焦耳热，温度改变输运，移动缺陷又反过来改变电导。它不是一个简单方程，而是一条电—热—缺陷状态因果链。

### 2. 我们没有直接开始训练

研究先给参考对象安排了层层资格考试：

1. 来源、许可和模型身份能否闭合？
2. 二维物理合同是否完整、透明、可独立实现？
3. 数值求解是否在空间、时间和重复运行上稳定？
4. 目标事件是否真的形成、可定位、可恢复？
5. strong raw baseline 是否有能力？
6. 只有前面全部通过，PINN、消融、OOD 和 formal 比较才有资格开始。

这些规则都在看见新结果前写死，包括失败 intent 也要计账、不得偷偷换案例、不得放宽阈值、不得重跑到成功为止。

### 3. 来源对象为什么没直接用

第一条路线是公开的 COMSOL 忆阻器示例。它能说明模型大致有什么物理，但本项目需要的执行权利、完整默认树和独立可用参考输出没有一起闭合。第二条 PCMO 路线有很好的 reaction–drift 物理故事，却是集总点器件模型，电流依赖未公开的 Sentaurus 查找表。把不同论文、软件和猜测拼成一个“作者模型”会制造虚假的来源身份，因此两条路线都按预定门关闭。

### 4. 透明合成对象发生了什么

预注册 fallback 是一个完全透明的二维轴对称电热—守恒缺陷输运对象。它不是某种真实材料的标定模型，而是一台所有齿轮都能看到的工程试验机。

零驱动 Q0 先通过：400 个时间步里，缺陷状态保持 0.5，温度保持 300 K，质量、热和端口电流计账都闭合。这说明基本装配和数据链条在简单工况下正常。

但 Q0 不是“参考答案通过”。真正受驱动的 QN 一开始，输运 Newton 就在预先冻结的 20 次迭代上限内没达到残差阈值，甚至没有产生可供评价的场。按照规则，这个 intent 被记为失败，后续 3–13 全部停止。

### 5. 为什么不把迭代次数改大

诊断显示，把步长或迭代上限改掉，很可能能越过眼前这一关。但这恰恰是最容易发生结果偏差的地方：看见失败后调到成功，再把新设置包装成“原计划”。

我们把问题拆成两个：

- 原来冻结的配置通过了吗？没有。
- 改过的新配置以后能成功吗？不知道，需要新合同和新研究。

这不是反对调试，而是拒绝用调试覆盖已经发生的预注册结果。

### 6. 为什么“没有训练 PINN”反而是结果的一部分

没有受驱动 reference field，就没有跨分辨率 oracle；没有 oracle floor，就不知道神经网络误差是不是低于数值不确定性；没有合格事件，就不知道网络是否保持了真正关心的器件行为。此时训练 PINN 只能证明代码会跑，不能证明方法好坏。

所以停止训练不是项目漏做了关键实验，而是资格化规则起作用：它阻止了一个不合格的参考过程变成虚假的 PINN 证据。

## 给导师的讲法

> 这不是一篇正向 PINN 算法论文，而是一篇 reference-solver qualification 与 method-limits 论文。我们把来源、对象、数值、事件、oracle、baseline 和方法门预先冻结。来源对齐对象未闭合，透明合成对象的 Q0 实现守卫通过，但首个 driven QN 在生成场之前超过冻结 Newton 上限。我们按 no-rescue 规则停止，因此结论严格限于 `SYN_EDT_2D_V1_NUMERICAL_CONTRACT_NO_GO`。文章的贡献是 failure-preserving workflow、透明 benchmark candidate、完整终局记录和 claim-boundary template。

## 给审稿人的讲法

> The absence of PINN training is not an omitted experiment. It is the preregistered consequence of an upstream reference-solver gate failing before an oracle and its uncertainty floor existed. Continuing to train would have produced implementation activity, not interpretable method evidence. We therefore preserve the failed intent, report the unreached gates, and bound the conclusion to the frozen numerical contract.

## Cover letter 核心段落

> This manuscript addresses a prerequisite that is often implicit in physics-informed machine-learning studies: the reference process must itself be qualified before it can support a neural accuracy claim. We preregistered an ordered source-to-method workflow for an electrothermal defect-transport case. Two source-aligned routes did not close under their fixed contracts. A transparent synthetic fallback passed a zero-drive implementation guard but failed its first driven qualification intent under the frozen Newton limit before any oracle field was produced. We stopped before PINN training, retained the failed intent, and report the resulting numerical-contract No-Go without extrapolating it to physical solvability or machine-learning performance. We believe this failure-preserving case study offers a reusable template for more credible multiphysics PINN evaluation.

## 可以说什么

- 参考求解器在成为 PINN benchmark 前接受了预结果冻结的顺序资格化。
- Q0 通过零驱动实现与产物链守卫。
- 首个受驱动 QN 在冻结 Newton 上限内失败，并且失败被完整保留和计账。
- 本次冻结数值合同是 No-Go。
- 停止规则避免未资格化参考过程被包装成方法证据。
- 全部结论来自透明合成计算与有界来源审查，不是实验验证。

## 不能说什么

- 不能说 PINN 失败或成功，因为没有训练 PINN。
- 不能说物理方程不可解，因为只测试了一个冻结数值合同。
- 不能说目标事件不存在，因为没有得到合格受驱动场。
- 不能说 Q0 是 oracle PASS。
- 不能说诊断证明全局 Jacobian 正确。
- 不能说对象是 VO₂、GST 或经过标定的真实 PCM 器件。
- 不能说没有发现 exact prior-art collision 就等于世界首创。
- 不能把公开 GitHub 仓库等同于期刊发表、实验数据或第三方许可。

## 一页 PPT 叙事

**标题：参考解也需要资格化**

- **问题：** PINN 评价通常默认传统求解器是真值，但多物理 reference 可能在来源、数值或事件层先失效。
- **设计：** 结果前冻结 source → object → numerical → event → oracle → baseline → PINN/formal 顺序门。
- **执行：** 两条来源路线未闭合；透明二维合成 fallback 启用。
- **观察：** Q0 零驱动守卫通过；首个 driven QN 在产生场前超过 frozen Newton limit。
- **纪律：** 失败计账、无 rescue、后续 3–13 不启动、诊断不参与科学投票。
- **结论：** `NUMERICAL_CONTRACT_NO_GO`，不是 physical No-Go，也不是 PINN No-Go。
- **价值：** 当参考求解器先失败时，停止并保全失败，防止制造不可解释的机器学习证据。
