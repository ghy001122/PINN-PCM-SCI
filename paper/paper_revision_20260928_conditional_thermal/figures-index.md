# 条件热响应与本构闭合图件索引

所有图件仅从已保存数组绘制，不重新推进温度、不重放历史、不改变冻结插值。
固定主展示为12.5 V、0.5 ns；以下覆盖全部五工况、七个器件角色。源步长比较见结果表，不将细步源记录视为连续真解。

## 固定12.5 V展示

- [全程温度、误差与闭合](figures/conditional-single_12p5V-A.png)
- [全程迟滞、电阻与两类电流](figures/single_12p5V-history-closure.png)
- [沿用2.362–2.862 μs窗口](figures/single_12p5V-fixed-first-peak.png)

## 全工况图件

| 工况／角色 | PNG | 矢量PDF |
|---|---|---|
| conditional-single_9V-A | [查看](figures/conditional-single_9V-A.png) | [下载](figures/conditional-single_9V-A.pdf) |
| conditional-single_12p5V-A | [查看](figures/conditional-single_12p5V-A.png) | [下载](figures/conditional-single_12p5V-A.pdf) |
| single_12p5V-history-closure | [查看](figures/single_12p5V-history-closure.png) | [下载](figures/single_12p5V-history-closure.pdf) |
| single_12p5V-fixed-first-peak | [查看](figures/single_12p5V-fixed-first-peak.png) | [下载](figures/single_12p5V-fixed-first-peak.pdf) |
| conditional-single_15p8V-A | [查看](figures/conditional-single_15p8V-A.png) | [下载](figures/conditional-single_15p8V-A.pdf) |
| conditional-pair_excitation-A | [查看](figures/conditional-pair_excitation-A.png) | [下载](figures/conditional-pair_excitation-A.pdf) |
| conditional-pair_excitation-B | [查看](figures/conditional-pair_excitation-B.png) | [下载](figures/conditional-pair_excitation-B.pdf) |
| conditional-pair_inhibition-A | [查看](figures/conditional-pair_inhibition-A.png) | [下载](figures/conditional-pair_inhibition-A.pdf) |
| conditional-pair_inhibition-B | [查看](figures/conditional-pair_inhibition-B.png) | [下载](figures/conditional-pair_inhibition-B.pdf) |

## 全部十套输入对应的条件数组

热响应包含Q_ref、V_ref、P、CS和4/8点求积逐点差；分解、历史与原始输入的关联见冻结配置。

| 保存系统 | 热响应 | 误差分解 | P历史 | CS历史 | 来源核对 |
|---|---|---|---|---|---|
| single_9V-1ns | [NPZ](arrays/single_9V-1ns/thermal.npz) | [NPZ](arrays/single_9V-1ns/decomposition.npz) | [NPZ](arrays/single_9V-1ns/history-P.npz) | [NPZ](arrays/single_9V-1ns/history-CS.npz) | [JSON](arrays/single_9V-1ns/source-history-check.json) |
| single_9V-0p5ns | [NPZ](arrays/single_9V-0p5ns/thermal.npz) | [NPZ](arrays/single_9V-0p5ns/decomposition.npz) | [NPZ](arrays/single_9V-0p5ns/history-P.npz) | [NPZ](arrays/single_9V-0p5ns/history-CS.npz) | [JSON](arrays/single_9V-0p5ns/source-history-check.json) |
| single_12p5V-1ns | [NPZ](arrays/single_12p5V-1ns/thermal.npz) | [NPZ](arrays/single_12p5V-1ns/decomposition.npz) | [NPZ](arrays/single_12p5V-1ns/history-P.npz) | [NPZ](arrays/single_12p5V-1ns/history-CS.npz) | [JSON](arrays/single_12p5V-1ns/source-history-check.json) |
| single_12p5V-0p5ns | [NPZ](arrays/single_12p5V-0p5ns/thermal.npz) | [NPZ](arrays/single_12p5V-0p5ns/decomposition.npz) | [NPZ](arrays/single_12p5V-0p5ns/history-P.npz) | [NPZ](arrays/single_12p5V-0p5ns/history-CS.npz) | [JSON](arrays/single_12p5V-0p5ns/source-history-check.json) |
| single_15p8V-1ns | [NPZ](arrays/single_15p8V-1ns/thermal.npz) | [NPZ](arrays/single_15p8V-1ns/decomposition.npz) | [NPZ](arrays/single_15p8V-1ns/history-P.npz) | [NPZ](arrays/single_15p8V-1ns/history-CS.npz) | [JSON](arrays/single_15p8V-1ns/source-history-check.json) |
| single_15p8V-0p5ns | [NPZ](arrays/single_15p8V-0p5ns/thermal.npz) | [NPZ](arrays/single_15p8V-0p5ns/decomposition.npz) | [NPZ](arrays/single_15p8V-0p5ns/history-P.npz) | [NPZ](arrays/single_15p8V-0p5ns/history-CS.npz) | [JSON](arrays/single_15p8V-0p5ns/source-history-check.json) |
| pair_excitation-1ns | [NPZ](arrays/pair_excitation-1ns/thermal.npz) | [NPZ](arrays/pair_excitation-1ns/decomposition.npz) | [NPZ](arrays/pair_excitation-1ns/history-P.npz) | [NPZ](arrays/pair_excitation-1ns/history-CS.npz) | [JSON](arrays/pair_excitation-1ns/source-history-check.json) |
| pair_excitation-0p5ns | [NPZ](arrays/pair_excitation-0p5ns/thermal.npz) | [NPZ](arrays/pair_excitation-0p5ns/decomposition.npz) | [NPZ](arrays/pair_excitation-0p5ns/history-P.npz) | [NPZ](arrays/pair_excitation-0p5ns/history-CS.npz) | [JSON](arrays/pair_excitation-0p5ns/source-history-check.json) |
| pair_inhibition-1ns | [NPZ](arrays/pair_inhibition-1ns/thermal.npz) | [NPZ](arrays/pair_inhibition-1ns/decomposition.npz) | [NPZ](arrays/pair_inhibition-1ns/history-P.npz) | [NPZ](arrays/pair_inhibition-1ns/history-CS.npz) | [JSON](arrays/pair_inhibition-1ns/source-history-check.json) |
| pair_inhibition-0p5ns | [NPZ](arrays/pair_inhibition-0p5ns/thermal.npz) | [NPZ](arrays/pair_inhibition-0p5ns/decomposition.npz) | [NPZ](arrays/pair_inhibition-0p5ns/history-P.npz) | [NPZ](arrays/pair_inhibition-0p5ns/history-CS.npz) | [JSON](arrays/pair_inhibition-0p5ns/source-history-check.json) |

边界：本包是作者模型记录上的条件响应分析。图中R-law电流为无反馈诊断，不替换既有KCL电流。
温度差使用绝对K；没有工程用途容差，不能凭视觉接近宣布工程合格、PINN增量或材料验证。
