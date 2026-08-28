# PHK-V2.1 强基线复现与伪时间控制身份审计

- 日期：2026-08-27
- 状态：`SOURCE_AUDIT_COMPLETE_PREREGISTRATION_INPUT_ONLY`
- 适用对象：PHK-V2.1 的 Sharp-PINNs、PF-PINNs 与 adaptive pseudo-time 比较器预注册
- 科学状态：`UNKNOWN`；本审计未运行求解器、PINN、训练、GPU 或指标计算
- 继承边界：不回写、不重解释、也不解除 PHK-V2 已封存的 Oracle No-Go
- 来源边界：只使用论文、出版社页面、论文指定官方仓库及固定提交；未使用二手综述作为事实来源

## 1. 有界结论

`VERIFIED`：三个候选对象均已闭合到论文和论文指定代码身份，但“论文指标复现”“固定仓库 recipe 复跑”和“在 PHK 接口中的 clean-room 比较器适配”是三种不同证据，必须分开登记：

1. **Sharp-PINNs** 的正式论文方法是 AC/CH staggered training、random Fourier embedding、modified MLP、hard output constraint、gradient-norm weighting 和周期性重采样；当前官方仓库的 2D recipe 额外加入 causal weighting、RAR，并把关键预算从论文的 1,000 steps 改成 800,000 epochs，不能静默当作论文指标复现。[正式论文](https://doi.org/10.1016/j.cma.2025.118346) [开放全文](https://arxiv.org/html/2502.11942) [固定 README](https://github.com/NanxiiChen/sharp-pinns/blob/4b7029e3e1e0b82482d245ba12e3ec0945d87ed9/README.md)
2. **PF-PINNs** 的正式论文方法是尺度归一化、界面加密/自适应采样和 random-batch NTK weighting；固定仓库中的 1D、2D 配置与论文叙述在 collocation、IC、NTK batch 和 epochs 上存在多处差异，二者也必须分开。[正式论文](https://doi.org/10.1016/j.jcp.2025.113843) [出版社页面与代码声明](https://www.sciencedirect.com/science/article/pii/S0021999125001263) [固定 README](https://github.com/ChuanjieCui/PF-PINNs/blob/a25f75b5fd40657e5ce98467d7afd0d0052464d1/README.md)
3. **jaxpi2 adaptive pseudo-time** 是通过“上一参数迭代的输出 + 当前 PDE 残差”形成的残差松弛，并与 collocation resampling 联用；它不是物理时间坐标重参数化，也不是 KC。它适合作为 PHK-V2.1 中检验“通用残差延拓是否已解释收益”的强反事实控制。[论文](https://arxiv.org/html/2604.23528) [官方方法文档](https://sifanexisted.github.io/jaxpi2/methods/pseudo-time)

`SUPPORTED_INTERPRETATION`：在成本和判别力之间，最合理的原域复现组合是：Sharp 2D two-pits 的论文表格/图形靶点；PF 的 1D activation 数值/趋势靶点与 2D semicircular pit 场级靶点；jaxpi2 仅做官方机制验证和 PHK 等预算 clean-room 控制，不把 Allen–Cahn 的近 float32-floor 数字当作 PHK 涨点目标。

`UNKNOWN`：上述任何对象能否在本机按预注册容差复现、任何模块能否在已资格化 PHK benchmark 上提升端点、以及 PHA-MF 或 field-selective KC 是否有独立增益，均尚无执行证据。

## 2. 必须互斥的三类证据标签

| 标签 | 必要条件 | 可以支持的表述 | 不能支持的表述 |
|---|---|---|---|
| `OFFICIAL_PAPER_METRIC_REPRODUCTION` | 原论文 PDE、域、参数、参考解、网络/训练配置、预算和 evaluator 均被冻结；与原文明确表或图比较 | “在原论文身份下复现了/未复现某一预声明指标或排序” | “运行了作者仓库，所以复现了论文” |
| `PINNED_REPO_RECIPE_REPLICATION` | 只用一个指定仓库、一个完整 SHA、一个 recipe 和对应数据；记录偏离论文之处 | “复跑固定提交中的作者 recipe” | “仓库 recipe 等同正式论文配置” |
| `CLEAN_ROOM_COMPARATOR_ADAPTATION` | 依据论文公式在项目接口中重新实现；同一 PHK oracle、support、优化器、参数量/预算和 evaluator 下比较 | “公式导出的 PHK 适配比较器在本 benchmark 上的结果” | “官方 Sharp/PF/jaxpi2 复现结果” |

这些标签不能在一次 run 后事后更换；跨两个 PF 仓库拼接源码、配置、数据或结果也不形成第四种合法身份。[PF 出版社代码声明](https://www.sciencedirect.com/science/article/pii/S0021999125001263)

## 3. 固定来源与许可

截至 2026-08-27，远程默认分支身份经只读 `git ls-remote` 核对如下；链接固定到完整 commit，后续默认分支漂移不改变本审计身份。

| 对象 | 正式载体 | 固定官方代码身份 | 代码许可与边界 |
|---|---|---|---|
| Sharp-PINNs | CMAME 447 (2025) 118346；[DOI](https://doi.org/10.1016/j.cma.2025.118346)，[arXiv 2502.11942](https://arxiv.org/html/2502.11942) | NanxiiChen/sharp-pinns [`4b7029e3e1e0b82482d245ba12e3ec0945d87ed9`](https://github.com/NanxiiChen/sharp-pinns/commit/4b7029e3e1e0b82482d245ba12e3ec0945d87ed9) | [GPL-3.0](https://github.com/NanxiiChen/sharp-pinns/blob/4b7029e3e1e0b82482d245ba12e3ec0945d87ed9/LICENSE)；隔离运行或按论文公式 clean-room 实现，不能把复制的 GPL 源码并入拟采用不兼容许可的主实现 |
| PF-PINNs | JCP 529 (2025) 113843；[DOI](https://doi.org/10.1016/j.jcp.2025.113843) | ChuanjieCui/PF-PINNs [`a25f75b5fd40657e5ce98467d7afd0d0052464d1`](https://github.com/ChuanjieCui/PF-PINNs/commit/a25f75b5fd40657e5ce98467d7afd0d0052464d1)；NanxiiChen/PF-PINNs [`f8a4980108504a984695b75d2665b27d5f26cc0b`](https://github.com/NanxiiChen/PF-PINNs/commit/f8a4980108504a984695b75d2665b27d5f26cc0b) | 两个官方仓库均为 GPL-3.0；[固定许可](https://github.com/ChuanjieCui/PF-PINNs/blob/a25f75b5fd40657e5ce98467d7afd0d0052464d1/LICENSE)。正式复跑一次只能选择其中一个完整 SHA |
| jaxpi2 | arXiv:2604.23528v1；截至本审计未发现正式 DOI，[开放全文](https://arxiv.org/html/2604.23528) | sifanexisted/jaxpi2 [`77a5c1315a056388271822c35ad512a5a192b60d`](https://github.com/sifanexisted/jaxpi2/commit/77a5c1315a056388271822c35ad512a5a192b60d) | 根仓库 [Apache-2.0](https://github.com/sifanexisted/jaxpi2/blob/77a5c1315a056388271822c35ad512a5a192b60d/LICENSE)；论文文本为 CC BY-NC-SA 4.0。依赖与外来资产仍须按固定环境单独留 provenance，根许可证不能替代依赖审计 |

## 4. Sharp-PINNs：论文指标身份

### 4.1 方法与配置

`VERIFIED`：正式论文针对耦合 Allen–Cahn/Cahn–Hilliard 腐蚀相场，以 staggered schedule 交替优化两个方程块；RFF、modified MLP、KKS hard output constraint 与 gradient-norm weighting 构成同一完整方法。论文附录给出默认 RFF 维数 64、空间/时间频率尺度 2.0/0.4、隐藏宽度 128、6 层、域内点 `40×20×30`、BC 500、IC 800、staggering period 25、初始学习率 `5e-4`。[论文方法与附录](https://arxiv.org/html/2502.11942)

`VERIFIED`：优先靶点 2D two-pits 使用 `[-50,50]×[0,50] μm²`、`t∈[0,10] s`，两个初始坑半径均为 5 μm、中心距 30 μm；论文报告 1,000 Adam steps，学习率从 `5e-4` 开始、每 100 epochs 乘 0.9。[论文算例](https://arxiv.org/html/2502.11942)

### 4.2 可登记的数值与图形靶点

| 原文对象 | 指标或图形目标 | 预注册用途 |
|---|---|---|
| Table 1，2D two-pits | absolute (L^2) error `6.066e-4`；FEniCS 1.62 min、PINN 7.68 min | error 为 point-estimate 对照值；时间只作同论文硬件背景，不作跨硬件 PASS 阈值 |
| Fig. 4 | `t={0,2.273,4.803,9.528} s` 的 PINN/FEniCS/error contours；最大时刻误差在 `t=4.803 s` 为 `4.516e-3` | 场图和逐时刻 evaluator 复核，防止仅复述全局均值 |
| Table 2 / Figs. 5–6 | 完整 Sharp `6.066e-4`；去 stagger `3.974e-2`；去 hard constraint `8.494e-3`；去 modified MLP `1.554e-2`；去 Fourier `1.671e-2`；plain `2.006e-1` | 原域模块排序与形貌 sanity check；不能直接当作 PHK 归因结果 |

上述数值均来自同一正式论文。[Table 1、Table 2 与图 4–6](https://arxiv.org/html/2502.11942)

`VERIFIED`：3D two-pits 在论文 Table 1 为 `2.834e-3`，而 Table 3 的完整 Sharp 行为 `1.345e-3`。这是原文内部的表格身份冲突；PHK-V2.1 不应把 3D two-pits 设为首个复现靶点。若未来复现，必须分别记录表号并从场数据重算同一 evaluator，不能事后选取较容易命中的数值。[正式论文](https://arxiv.org/html/2502.11942)

### 4.3 固定仓库 recipe 与论文的漂移

`VERIFIED`：固定提交的 2D two-pits recipe 使用 256 维输入 embedding、隐藏宽度 200、6 层、32 causal segments、800,000 epochs、`20×20×50` 域内网格、BC 200、IC 500、RAR base 40,000/RAR 6,000，并启用 causal weighting、hard constraint、Fourier、modified MLP 和 RAR。[固定 README](https://github.com/NanxiiChen/sharp-pinns/blob/4b7029e3e1e0b82482d245ba12e3ec0945d87ed9/README.md) [固定 2D 入口](https://github.com/NanxiiChen/sharp-pinns/blob/4b7029e3e1e0b82482d245ba12e3ec0945d87ed9/main-2d-2pits.py)

因此：

- 论文 1,000-step 身份记为 `SHARP_PAPER_2D_2PITS_V1`；
- 固定仓库 800,000-epoch 身份记为 `SHARP_REPO_2D_2PITS_4B7029E`；
- 在 PHK 方程和输出接口中重新实现的版本只能记为 `SHARP_FORMULA_DERIVED_PHK_A_PRIME`。

### 4.4 种子、时间与可复现性限制

`VERIFIED`：论文可检索全文没有报告主结果的随机 seed、重复次数、误差条或跨 seed 方差；固定 2D 主入口也未发现显式 seed 初始化。因此作者表值只能作为 point estimates，不能被解释为置信区间或稳定性阈值。[论文](https://arxiv.org/html/2502.11942) [固定入口](https://github.com/NanxiiChen/sharp-pinns/blob/4b7029e3e1e0b82482d245ba12e3ec0945d87ed9/main-2d-2pits.py)

`VERIFIED`：论文硬件为 AMD EPYC 7543、NVIDIA A40 48 GB；FEniCS 与 PINN 分别在 CPU/GPU 上计时。因此 7.68 min 或论文 3D 的 5–10× speedup 不能作为本项目的跨硬件复现门，只能报告本机同设备、同精度、同 evaluator 的等预算相对时间。[正式论文](https://doi.org/10.1016/j.cma.2025.118346)

## 5. PF-PINNs：论文指标身份

### 5.1 方法与 1D activation 靶点

`VERIFIED`：PF-PINNs 的论文身份包括 min–max normalization/de-normalization、初态/界面局部加密、自适应移动界面采样和 random-batch NTK loss weighting；参考场由 FEniCS 生成。[论文](https://doi.org/10.1016/j.jcp.2025.113843) [出版社摘要与数据声明](https://www.sciencedirect.com/science/article/pii/S0021999125001263)

`VERIFIED`：论文 1D activation-controlled pencil-electrode 使用 4×16 网络、学习率 `1e-3`、约 `15×15` 域内点、从 5,000 candidates 选 512 adaptive points、IC 128、BC 64、random-batch NTK batch 512、4,000 iterations，采样/权重每 100 iterations 更新。[正式论文](https://doi.org/10.1016/j.jcp.2025.113843)

论文 Table 3 给出以下同配置权重对照；它既是低成本 numerical target，也是“相对趋势”靶点：

| 权重配置 | MSE | (R^2) | 论文时间 |
|---|---:|---:|---:|
| standard / no weighting | `4.351e-2` | `-0.299` | 28 s |
| random-batch NTK 64 | `5.801e-4` | `0.971` | 31 s |
| random-batch NTK 128 | `4.182e-4` | `0.979` | 32 s |
| random-batch NTK 256 | `1.923e-5` | `0.999` | 34 s |
| random-batch NTK 512 | `7.565e-5` | `0.997` | 44 s |
| mini-batch NTK 512 | `3.917e-4` | `0.980` | 63 s |
| full gradient weighting | `1.937e-2` | `-0.244` | 32 s |

数值来自论文 Table 3。[正式论文](https://doi.org/10.1016/j.jcp.2025.113843)

`VERIFIED`：batch 256 的 point estimate 优于 512，故预注册不得把“NTK batch 越大越好”作为作者结论。合理的论文复现目标是：重算同一 evaluator，检查 random-batch NTK 相对无权重和 full-gradient weighting 的方向性优势，并报告各 batch 的实际排序；不得通过只选择最好 batch 事后声明复现。

### 5.2 2D semicircular-pit 靶点

`VERIFIED`：论文 2D 算例使用 `[-50,50]×[0,50] μm²`、`t∈[0,50] s`、底部半径 5 μm 的半圆初始坑；网络为 8×16，域内点 3,375 (`15³`)、BC 256、IC 512、从 60,000 candidates 选 8,000 RAR points、random-batch NTK batch 512；训练 300,000 iterations，学习率 `1e-3` 每 50,000 iterations 减半。[正式论文](https://doi.org/10.1016/j.jcp.2025.113843)

`VERIFIED`：适合冻结的图/指标是 Fig. 11 在 `t={0,5.12,10.24,20.48,40.96} s` 的相场/误差图，五个时刻平均 MSE `6.658e-4`；Fig. 12 的平均坑半径与 `sqrt(t)` 关系，论文报告 (R^2=0.988)。论文也显示局部界面误差可接近 0.5，因此全局 MSE 不能替代界面和结构端点。[正式论文](https://doi.org/10.1016/j.jcp.2025.113843)

`SUPPORTED_INTERPRETATION`：PHK-V2.1 的 PF 原域资格化应同时保存场级 MSE、界面局部误差和结构轨迹；只命中 `6.658e-4` 而界面位置错误，不足以作为强基线通过。

### 5.3 固定仓库 recipe 与论文的漂移

`VERIFIED`：ChuanjieCui 固定提交的 1D activation recipe 使用 `10×10` 域内点、IC 64、NTK batch 32，而论文是约 `15×15`、IC 128、batch 512；固定 2D recipe 使用 800,000 epochs、BC 128、IC 256，而论文为 300,000 iterations、BC 256、IC 512。[固定 README](https://github.com/ChuanjieCui/PF-PINNs/blob/a25f75b5fd40657e5ce98467d7afd0d0052464d1/README.md)

因此：

- 论文 1D activation 身份记为 `PF_PAPER_1D_ACTIVATION_V1`；
- 论文 2D semicircular-pit 身份记为 `PF_PAPER_2D_SEMICIRCLE_V1`；
- 固定提交 recipe 记为 `PF_REPO_A25F75B_<CASE>`；
- PHK 中的 NTK/sampling 公式适配只能记为 `PF_FORMULA_DERIVED_PHK_A_PRIME`。

`VERIFIED`：论文可检索正文未报告上述主表/主图的 seed schedule、重复次数或多 seed 不确定度；其中“average MSE”是所列时刻/评价点上的平均，不是 seed 均值。固定主配置也未提供可直接继承的多 seed 报告协议。[论文](https://doi.org/10.1016/j.jcp.2025.113843) [固定仓库](https://github.com/ChuanjieCui/PF-PINNs/tree/a25f75b5fd40657e5ce98467d7afd0d0052464d1)

## 6. jaxpi2：adaptive pseudo-time 控制身份

### 6.1 真实机制

`VERIFIED`：论文把伪时间写成相邻参数迭代输出之间的残差松弛项，并指出它只有与新 collocation points 重采样结合时，才能暴露有限训练点上隐藏的 spurious solution。adaptive 版本用残差局部 Jacobian 尺度的有限差分/Barzilai–Borwein 风格代理选择步长，并配合平滑、裁剪和 shrink；默认从 `tau=1` 开始，每 1,000 iterations 更新。固定步长结果则从 `{0.01,0.1,1,10,100}` 中依赖参考解选最好者。[方法与实验](https://arxiv.org/html/2604.23528) [官方方法文档](https://sifanexisted.github.io/jaxpi2/methods/pseudo-time)

这给出两个不得混淆的事实：

- best-fixed-τ 是有 oracle 才能事后选择的上界型 comparator，不是无参考场部署时可自由调参的公平默认值；
- adaptive pseudo-time 改写的是训练残差延拓，不是输入物理时间的严格单调映射；把它称为 KC 或用它替代 field-selective KC 消融均属身份错误。

### 6.2 强基线与可用靶点

`VERIFIED`：论文主基线不是普通 MLP，而是 3-block/9-layer PirateNet、宽度 256、Tanh，结合 SOAP、causal training、gradient-norm learning-rate annealing 和适用时的 exact periodic constraints；典型训练预算 100,000 iterations，2D/3D batch 分别为 4,096/8,192。[论文附录](https://arxiv.org/html/2604.23528)

Table 1 使用全时空 relative (L^2) point estimates：

| benchmark | baseline | best fixed pseudo-time | τ | adaptive pseudo-time |
|---|---:|---:|---:|---:|
| Allen–Cahn | `5.17e-6` | `3.26e-6` | 1 | `3.05e-6` |
| Gray–Scott | `4.14e-1` | `1.07e-1` | 100 | `1.52e-2` |
| Ginzburg–Landau | `1.74e-1` | `5.46e-2` | 1 | `7.75e-3` |

这些数值和完整十题表来自论文 Table 1。[论文结果](https://arxiv.org/html/2604.23528)

`VERIFIED`：作者指出 Allen–Cahn strong baseline 已接近 float32 precision floor，伪时间增益自然较小；它适合验证官方实现链，但不适合作为 PHK-V2.1 的主要涨点判别题。[论文讨论](https://arxiv.org/html/2604.23528)

### 6.3 种子和成本限制

`VERIFIED`：Table 1 是点估计，未声明多 seed 汇总；五个随机种子只明确用于 Fig. 9–10 的更新频率、shrink 和强基线组件鲁棒性消融。Table 2 的 wall-time 是单张 H200 上每 100 iterations 的 mean±SD，但正文未说明重复次数；Allen–Cahn 为 baseline `2.50±0.08 s`、pseudo-time `2.63±0.07 s`。[论文结果与成本](https://arxiv.org/html/2604.23528)

`VERIFIED`：固定仓库以 Python 3.11/JAX 栈为主，并包含 W&B 和外部 SOAP_JAX 等依赖；即便根仓库为 Apache-2.0，正式复跑仍应隔离环境、关闭不必要外联并保存完整依赖锁定，而不是把整个栈静默并入主项目。[固定 README](https://github.com/sifanexisted/jaxpi2/blob/77a5c1315a056388271822c35ad512a5a192b60d/README.md) [固定 pyproject](https://github.com/sifanexisted/jaxpi2/blob/77a5c1315a056388271822c35ad512a5a192b60d/pyproject.toml)

### 6.4 PHK-V2.1 中应冻结的控制

`SUPPORTED_INTERPRETATION`：控制身份建议为 `ADAPTIVE_PSEUDO_TIME_PHK_CLEANROOM_V1`，只把论文方程和更新规则移植到**同一个已资格化 PHK strong-raw baseline**，并保持网络、采样支持、优化器、初始条件、seed、训练预算和 evaluator 一致。该控制的目的不是复制 jaxpi2 Table 1，而是回答：

> 在不引入 field-selective kinetics clock 的条件下，通用 residual relaxation + resampling 是否已经解释 strong-raw 的误差下降？

若该控制已达到 KC 或 PHA-MF+KC 的预声明主端点且物理端点非劣，则 KC 的独立主张必须失败或缩界；不得通过给 KC 更多训练、不同采样或不同 optimizer 保住正结论。

## 7. 可直接送入预注册的冻结条款

以下是来源审计建议，不是科学 PASS：

1. **身份冻结。** 每个 run 必须在启动前声明三类证据标签之一、论文/仓库版本、完整 SHA、配置哈希、数据/参考解身份和 evaluator；标签不得事后切换。
2. **Sharp 原域靶点。** 首选 `SHARP_PAPER_2D_2PITS_V1` 的 Fig. 4 + Table 2；以作者 point estimate 和完整六臂排序为外部对照，不以 7.68 min 作为跨硬件门。若因预算只运行缩减消融，必须在启动前列出保留臂，不能把缩减结果称为 Table 2 完整复现。
3. **PF 原域靶点。** 先做 `PF_PAPER_1D_ACTIVATION_V1` 的 Table 3 evaluator/方向性检查，再做 `PF_PAPER_2D_SEMICIRCLE_V1` 的场 MSE、界面误差和半径轨迹；两者缺一时只能称部分资格化。
4. **种子补充。** Sharp/PF 的作者主结果没有可继承的方差；PHK-V2.1 应预先固定至少 3 个本地 seeds，保存每个 run，报告逐 seed 值、median 和离散度。作者 point estimate 不能用作本地置信区间，也不能通过挑 seed 命中。
5. **容差先验。** “命中作者数字”的绝对/相对容差、场插值、norm、时刻和界面抽取方法必须在首个计票 run 前冻结；本来源审计不凭空发明容差。未先冻结 evaluator 的相似图形不构成 metric reproduction。
6. **neural floor。** 只有完成预声明 seed/reporting 协议的最强合格 baseline 才能封存为 neural floor；paper point estimate、repo smoke 或单 seed best run 均不能成为 floor。
7. **等预算适配。** Sharp/PF/jaxpi2 的 PHK clean-room 版本必须共享 oracle、case split、训练 support、seed 和 evaluator；参数量、gradient evaluations、wall-time 采用哪一个作为主预算需在执行前指定，并完整报告其余预算。
8. **许可隔离。** Sharp/PF 原代码和派生修改留在 GPL 隔离 comparator 环境；主库只接纳有清晰 provenance 的公式级 clean-room 实现。jaxpi2 虽为 Apache-2.0，仍需逐项保留依赖与第三方资产来源。
9. **失败保全。** 任一官方原域复现若未命中，不得从 repo recipe、另一官方 PF 仓库或另一 seed 拼接证据；保留失败身份，再按预注册降级为 repo-recipe replication 或 clean-room adaptation。
10. **主张边界。** 原域复现只证明实现/评价链能回收作者题目的某些结果；它不资格化 PHK oracle，不证明 PCM 物理有效，也不证明 PHA-MF、KC 或组合优于 baseline。

## 8. 最终状态

- `VERIFIED`：Sharp、PF 和 jaxpi2 的论文、官方仓库、完整提交、许可证、主要方法、可复现图/表靶点以及 paper-vs-repo 配置漂移已闭合。
- `SUPPORTED_INTERPRETATION`：上述靶点足以形成 PHK-V2.1 的原域 baseline 资格化和 adaptive pseudo-time 反事实控制，不需要把三个上游仓库拼成一个新“官方方法”。
- `UNKNOWN`：本地依赖能否成功复跑、作者 point estimates 的跨 seed 波动、本地预注册容差内是否命中、任何 PHK 端点是否改善。
- `NOT_AUTHORIZED_BY_THIS_AUDIT`：本审计不启动求解、训练、GPU、formal/OOD，不修改 PHK-V2 或 PHK-V2.1 合同、状态、代码与 ledger，也不产生科学 PASS。
