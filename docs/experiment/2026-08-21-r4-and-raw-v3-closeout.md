# R4 与 raw-v3 有界执行收口，2026-08-21

## 结论

- `VERIFIED_IMPLEMENTATION`：四场动态电子序参量 reduced oracle、初值精确结构表示、非初始 checkpoint 选择和独立磁盘评价链已实现。
- `INVALID_EXECUTION`：R4 固定信号 pilot 在 `dt=1 ns` 和唯一修正 `dt=0.1 ns` 下均因耦合 η–μ 局部反应不收敛而在首个完整案例前失败；因此没有形成可判定的 R4 信号结果。
- `VERIFIED_DEVELOPMENT_NEGATIVE`：作者随包参考 artifact 确有强结构事件，但修复后的强 raw-v3 仍预测恒定相区，裁决 `RAW_EVENT_NOT_RESOLVED`。
- `BOUNDARY`：KC 判别 pilot 与 formal 均未打开；本轮不支持 KC 成功、KC 一般性失败、实验验证或 SOTA 主张。

## 本轮取得的实现进展

1. 新增 `DynamicOrderOracleCase` 深模块，把 φ、T、η、μ 四个独立状态、局部 η–μ 隐式反应、扩散、电路、热方程和 artifact 输出收敛到单一接口。
2. smoke `20260821T082417Z-smoke-r4-dynamic-order-001` 完成两个时间步，所有场有限，最大平衡违规 `6.1528436921e-11`。
3. CPC v1 随包参考 artifact `20260821T025742Z-smoke-g3-qpop-reference-import-001` 的 38 个场快照覆盖 8141 节点与 16000 三角单元；η 从 `5.3322589e-05` 到 `1.1192457725`，冻结阈值下相区占比从 `0.4465053433` 到 `1.0`，动态范围 `0.5534946567`。
4. 结构网络改为 `η(x,t)=1.6·tanh(initial_latent(x)+t·network(x,t))`，在 raw、identity 和 KC 中严格共享初值合同；checkpoint selector 排除 step 0；PHA/Fourier 修正也在初始时刻严格归零。
5. raw-v3 smoke `20260821T084645Z-smoke-n1-checkpoint-v3-001` 选出 step 1，证明非初始 checkpoint、序列化和独立 evaluator 控制流畅通。
6. raw-v3 pilot `20260821T084708Z-pilot-n1-checkpoint-v3-001` 完成固定四臂 screen 与唯一 1000-update 续跑，共 1600 次更新；最终选择 grouped-mean + joint 的 step 900。

## 失败根源

### 已证实的实现问题

- 原 η 输出头只有 `1e-3` 量级初始化，且没有初值精确时间残差结构；在已有 N2 稀疏锚点诊断中，1000 次更新后预测 η 的标准差仍仅约 `3.12e-05`，属于显著梯度饥饿。
- step 0 与同一初始 audit 集共同定义归一化尺度，使所有非零残差在初始化时天然等于 1；旧 selector 又允许 step 0，当后续最大违规稍高时会错误偏好未训练模型。
- 这两项已经通过 TDD 修复，因而不能再作为 raw-v3 失败的充分解释。

### 修复后仍存的科学/数值瓶颈

- `SUPPORTED_INTERPRETATION`：当前七未知量强形式残差与有限 3×24 网络/固定预算形成近初始结构吸引域。器件 NRMSE 从约 1 移动到 `0.9934716030`，而相区动态始终为 `0.0`，说明优化并非整体停滞，而是结构事件通道未被解析。
- raw-v3 最终结构误差 `0.2290643041` 高于门槛 `0.2190643041`，物理最大违规 `1.1427834250` 高于非劣门 `1.0483889664`；继续放大训练或网络属于未预登记救援，不能产生可信方法证据。
- R3 的全局稳定 μ 代数闭合已证实没有事件；R4 恢复动态 μ 后，异质 50×20 网格上的 η–μ 反应在 `0.1 ns` 仍不收敛。R4 只能裁为执行无效，不能裁为无信号。
- 作者参考 artifact 的真实事件排除了“oracle 本身没有事件”作为当前 raw 失败根因；但它仍是 `QPOP_CPC_V1_BUNDLED_REFERENCE_UNQUALIFIED`，不能用于 formal。

## 门控裁决

- `R4-S1 = INVALID_EXECUTION`
- `N1_RAW_V3 = RAW_EVENT_NOT_RESOLVED`
- `KC_PILOT = NOT_OPENED`
- `FORMAL = NOT_OPENED`
- `positive_method_claim_count = 0`

R4 旧 manifest 的 `gate_outcome` 正确记录为 `R4_EXECUTION_FAILED`，但当时的 `route_disposition` 写成了 `R4_NO_SIGNAL`。不可变记录不改写；当前代码已新增合同测试，后续执行失败将使用 `R4_EXECUTION_INVALID`，并确保 intent 记录真实 `dt`。

## 下一路线边界

当前 R3、R4 和七未知量 Q-POP PINN 路线到此关闭。若继续论文 idea，只能在新的、预先具备可验证结构事件的二维电—热—相态 substrate 上，从一个 raw 事件能力 smoke 重新开始；不得复用本轮失败为 KC 寻找正结果，也不得在 raw 能力门前打开 KC、formal 或 GPU。

## 证据入口

- `docs/experiment/manifests/20260821T082417Z-smoke-r4-dynamic-order-001.json`
- `docs/experiment/manifests/20260821T082444Z-pilot-r4-dynamic-order-signal-001.json`
- `docs/experiment/manifests/20260821T082826Z-pilot-r4-dynamic-order-signal-002.json`
- `docs/experiment/manifests/20260821T084645Z-smoke-n1-checkpoint-v3-001.json`
- `docs/experiment/manifests/20260821T084708Z-pilot-n1-checkpoint-v3-001.json`
- `outputs/runs/20260821T084708Z-pilot-n1-checkpoint-v3-001/pilot_summary.json`
