# PLAN-LF11-JOINT：终局与唯一下一步提案

- `phase_id`: `PHK_V23_LF11_JOINT_BC_PDE_COMPLETE`
- `lifecycle_state`: `CLOSED`
- `blocker_id`: `NONE`
- `claim_status`: `VALID_MATCHED_CONSTRAINT_STUDY_NO_DECLARED_INCREMENT`
- `next_research_execution_authorized`: `false`

## 已完成，本计划不继续当前训练

VERIFIED：主线三臂及条件 R/G/N 已完整收口，实际新增 6500 Adam updates、1500 次完整评估；五个匹配差分的 A/B 均未通过，D_N 未触发。R 重用的 P_U Adam1000 前缀没有重复计数。无科学重试或第二备选。详见[终局](../experiment/2026-09-12-phk-v23-lf11-joint-terminal-closeout.md)及[paper_v27](../../paper/paper_v27/README.md)。

执行语义保留于[原授权文件](../notes/2026-09-12-lf11-joint-authorized-sprint.md)与[冻结配置](../../configs/phk_v23/lf11_joint_sprint.json)。旧 V 门未通过及旧未运行分支不改写；本轮未设替代资格门。当前无自动执行权限。

## 优先问题与唯一首选

SUPPORTED_INTERPRETATION：主要待处理接口是“自身电势 → 接触电流 / 焦耳读出”的电学相容性。当前神经网络在一些相态指标上已接近或优于强插值，但电学读出仍差；电学块归一化没有把这些局部优势转化为器件增量。

HYPOTHESIS / PROPOSED_NOT_AUTHORIZED：研究**电学子问题消元的耦合 PINN**。这是下一轮的结构提案，不是已完成模块，不再追加当前 R/G/N 或 V-only。

1. **单一模块与信息边界。** 复用既有正导电率、谐和面电导及混合电边界，构造 \(A(\sigma)V^*=b(U,\sigma)\)。仅用模型自身 T/phase 和已知物理求解瞬时电学子问题，电流及焦耳沉积共用同一面网络；T/phase 原表示、方程和空间微分方式保持，热源来自该电学层。禁止参考场、teacher 通量或电流标签进入训练。训练空间网格先按已知几何固定，例如现有 80×40 网格；不得按参考误差选网格。

2. **实现的必要核验。** 用小型人工正导电率网格验证解、带符号电学恒等式及完整参数梯度 \(dV^*=A^{-1}(db-dA\,V^*)\)；实际实现使用正向/伴随求解，不构造稠密逆，也不 detach T/phase。只做与这些接口有关的工程测试，不重跑历史 S0/S1、V-only 或新的拟合资格门。离散电学相容不保证热平衡、σ、相态或绝对器件精度。

3. **立即进入同父匹配。** 建议固定本轮 D_I 的 T/phase 终点作为共同开发父态，fresh optimizer；该选择按无内部 PDE 控制的角色确定，不选参考最优 checkpoint。D_E 与 P_E 共用电学层、观测及热/相态 IC/BC；P_E 仅额外加入明确记录的热/相态内部 PDE 残差。D_E 是带电学求解的对照，不包装成无物理信息的数据网络。B_E 必须在同一个 contact 插值的 T/phase 上使用同一电学层，不能仅给 proposed 求解器。原 B 系列、旧 PINN 与 native solver 分别保留信息和计算角色。公共标度仅在共同父态一次冻结。

4. **首轮建议预算及评价。** D_E/P_E 各最多 1000 Adam + 200 次完整固定目标/梯度评估，合计 2000/400；固定时间积分池、线性求解容差及最后接受态，记录实际电学正向/伴随求解次数和所有优化评估。A/B 沿用本轮两层门，严格器件门单列；比较 P_E−D_E 并面对 B_E，完整报告双周期事件、双端电流、功率轨迹、能量和场误差。首图并列 D_E/P_E/B_E 的场—事件—器件量。不能把构造保证的电学守恒当作经验方法增量。

5. **停止与真正贡献。** 仅守恒改善、P_E 不超过 D_E，或面对同样求解的 B_E 无竞争力，都不足以形成正面 PINN 方法主张；按具体接口结果收口，不自动串联另一方法。若首次出现可信 A 或 B，再另批最近强 PINN 对照：同样焦耳耦合、软电学残差的匹配模型，以隔离消元模块本身，随后两套从头独立初始化、新 mask 和完整新协议。新案例适配与零样本泛化分开，不把更换 optimizer seed 或从已用父态删切片称为独立确认。

来源与新颖性：可微求解器训练已有[Solver-in-the-Loop 原始工作](https://proceedings.neurips.cc/paper/2020/hash/43e4e6a6f341e00671e123714de019a8-Abstract.html)，本仓库已有同一电导矩阵与电学求解入口。差异需由本项目耦合场—事件—器件的匹配收益证明，不能把线性求解或守恒恒等式命名为新发明。该提案仍须新的用户执行授权；当前不求解、不训练、不改冻结对象、不读 stress。用户后续授权的是已有成果发布及[云端独立复评](../notes/2026-09-12-lf11-v27-results-cloud-review-handoff.md)，允许评估后调整此提案，不自动执行。
