# 项目状态

更新时间：2026-09-13

- `phase_id`: `PHK_V23_LF11_ELECTRICAL_ELIMINATION_COMPLETE`
- `lifecycle_state`: `COMPLETE`
- `blocker_id`: `NONE`
- `claim_status`: `VALID_STRONG_BASELINE_GAIN_NO_MATCHED_REMAINING_PDE_INCREMENT`
- `next_research_execution_authorized`: `false`

## 当前 VERIFIED

[完整电学消元冲刺](docs/notes/2026-09-13-lf11-elimination-authorized-sprint.md)已执行收口。E0/B_E 零训练，D_E/P_E 各完成 1500 Adam / 300 次完整固定评估，接受 147/146 个 L-BFGS 步，四个固定角色均数值合法。当前[终局](docs/experiment/2026-09-13-phk-v23-lf11-electrical-elimination-terminal-closeout.md)、[paper_v28](paper/paper_v28/README.md)、[精简证据](paper/paper_v28/evidence/README.md)含实际结果，不能继续称训练中。

- D_E、P_E 均对同层强插值 B_E 通过冻结 A/B。P_E 的 S/Ephi 降低 41.85%/32.69%，电流/功率误差降低 59.85%/61.18%；D_E 也取得 44.12%/34.45%、58.09%/58.93% 的对应增益。
- P_E 对同父 D_E 未通过 A/B：S/Ephi 上升 4.07%/2.68%，电流/功率仅改善 4.20%/5.49%。能量改善 24.07%不能替代功率轨迹门。P_F 未触发、未运行，非失败端点。
- 固定 σ 的 V27 D_I→E0 电压替换使底流误差 506.741%→2.555%、功率误差 28.071%→2.641%；T/phase 完全不变，EV 上升 3.79%。这是电学接口修复，不是训练或相态增量。
- P_E 两周期 timing 较 D_E 改善，但第一周期 recall 0.88249<0.9，第二周期 timing 0.00753>0.005。所有角色严格器件门均为 false，恢复率均为 1。
- 同一固定无标签审计中，P_E 的 J_Tphi 比 D_E 高 0.58%，热/相态子项高 0.44%/8.25%，BC 低 4.81%。本轮未建立更低的剩余内部残差，不能套用旧“残差下降而事件变差”结果。
- 完整隐式梯度及局部产热检查通过；实际 CUDA T/phase 方向导数相对误差 3.64e-9 / 1.02e-10。主线共有 31286 次训练正解及 31286 次伴随解；四角色另含 1112 次细网格推理电解，分别计数。

## 解释、论文和最优先问题

SUPPORTED_INTERPRETATION：已形成“电学接口修复—同层强基线增益—剩余物理独立性”三层证据。前两层有正面有界结果，第三层未通过冻结比较；这不是所有 PINN 失败，也还不是完整的正面 PINN 方法优势。通用电学求解、隐式微分、FV 和守恒恒等式不分别算独立创新。paper_v28 已整合实际比较、四组图、主张矩阵和旧阶段可保留证据。

HYPOTHESIS：剩余 PDE 的有效优化影响可能受尺度或方向冲突制约。一次共同校准下，满权重热/相态项约 0.000497/0.0000443，观测项为 1；仅凭 loss 小不能确定梯度影响或根因。下一步应先在固定父态和 D_E 上分解观测/BC/热/相态对 T/phase 的实际更新影响，再决定一个可检验修正，详见[唯一提案](docs/plans/NEXT_ACTIONS.md)。本轮未追加调权或其他模块。

UNKNOWN：匹配 P_F 下消元必要性、独立初始化、干净的新掩码、完整案例/OOD、连续体真值及材料标定均未建立。当前仍是合成、无量纲、PCM-inspired 二维 wall-cell，旧数据全为已见开发数据。

## 执行与发布边界

实际 V100 任务已完成，产物已回收核验，真实实例已执行关机并确认之后连接被拒绝；[本次关机回执](paper/paper_v28/evidence/compute-closure.json)不是旧记录。其后才本地读取 nominal 参考。stress 未读取，未增加观测、新初始化或新物理。没有待运行云分支，没有新科研执行授权；用户随后明确授权本轮成果提交、推送及[云端独立评估交付](docs/notes/2026-09-13-lf11-v28-results-cloud-review-handoff.md)。原始运行记录的未发布字段保留为科研收口快照；本轮发布由所属提交与交付消息识别，不改变科学结论。

## 保留历史

V27：同父 D_I/D_B/P_U 和 R/G/N 六个合法终点，6500 Adam / 1500 完整评估；五个匹配差分 A/B 均未通过，D_N 未触发。D_B 的总 BC 降低而 heater 项与接触迹恶化；P_U 的旧独立 AD 物理目标下降却付出底流/功率代价。N 的局部 electric-amplitude 通道证据没有转化成冻结增量。该轮 [终局](docs/experiment/2026-09-12-phk-v23-lf11-joint-terminal-closeout.md)、[paper_v27](paper/paper_v27/README.md)与已发布 [V27 交接](docs/notes/2026-09-12-lf11-v27-results-cloud-review-handoff.md)保持历史身份。

V26 的 V-only 0.5618% 仍未通过原 0.5% 门，其当轮条件臂仍是未运行。V23/V24/V25/V26 的界面暴露、物理遗忘、拟合修复、固定 σ 接触分解均保留；本轮不同父态、校准、预算和电学接口的联合变化不追溯改写这些裁决。