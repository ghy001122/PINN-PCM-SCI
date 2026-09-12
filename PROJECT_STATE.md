# 项目状态

更新时间：2026-09-12

- `phase_id`: `PHK_V23_LF11_FOLLOWUP_FIT_AND_ELECTRIC_BLOCK_SPRINT_COMPLETE`
- `lifecycle_state`: `CLOSED`
- `blocker_id`: `NONE`
- `claim_status`: `VALID_THERMAL_FIT_REPAIR_NO_NEW_PINN_COMPARISON`
- `next_research_execution_authorized`: `false`

## 最新VERIFIED

VERIFIED：温度包络下界0.1504%；可见T误差17.8233%→1.1375%，三个T拟合门均过，phase不变。可见V误差0.8215%未达0.5%，是唯一未满足的拟合条件。完整nominal参考ROI T误差28.2210%→1.7475%，能量误差106.7402%→49.2006%。

本轮实际1200 Adam更新、400次固定目标/梯度评估；仅CPU，训练正常结束后评价，无GPU实例、stress读取或新物理。S=0.001188671875、raw Ephi=0.027268375553与父状态相同；top-current NRMSE7.2178%，bottom-current NRMSE781.2535%，严格器件未通过。

## 解释与未运行

SUPPORTED_INTERPRETATION：主要温度拟合缺口已可修复，剩余V误差偏向底部。最下两z层占16.25%测度、贡献53.17%V平方误差。尚未证明优化/表示/边界唯一根因；适配器与额外优化也未独立消融。
新的D_B/P_U、R/N/G/D_N未运行，不是执行失败；没有新的PINN匹配增量、独立seed或formal OOD。

[本轮终局](docs/experiment/2026-09-12-phk-v23-lf11-followup-terminal-closeout.md)与[paper_v25](paper/paper_v25/README.md)保存事实和复现。[历史LF11](docs/experiment/2026-09-11-phk-v23-lf11-terminal-closeout.md)、[paper_v24](paper/paper_v24/README.md)、LF10及旧稿均保留。

本轮成果的云端阅读路径、证据边界与最优先问题见[独立复评交接](docs/notes/2026-09-12-lf11-followup-results-cloud-review-handoff.md)。发布与评估不授权新训练。
