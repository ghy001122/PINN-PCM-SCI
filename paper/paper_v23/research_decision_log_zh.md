# PHK-V2.3 LF5 研究判断与论文路线

## 一句话裁决

LF4 仍未建立可进入 P0 的 carrier，也不是 PINN 方法结果；但它用严格 matched
三臂把 LF3 的“边界 support recall 不足”推进成了一个可归因结论：**teacher
interface exposure 是提升最差周期 recall 的有效机制，而 threshold-aligned BCE
会以显著场误差为代价修复 timing。** 这是实质机制进展，不是 candidate。

## 已验证事实

- 唯一 T0 轨迹严格完成 1200 步，P0 为 0 步；
- potential maximum-principle、phase range、finite、双周期事件、时间、
  precision、active-mass、locality 和 recovery 全部通过；
- 两周期 recall 为 `0.805842/0.768603`，均低于冻结的 `0.90`；
- 因此机器终局为 `LF3_CARRIER_NOT_ESTABLISHED`，P0 是未触发而非失败；
- 本地 extra-fine evaluator 上 LF3-T0 的 phase ROI RMS 为 `0.0390008`，
  明显好于 LF2-M0 的 `0.110564`，但仍远差于 direct `LF_ONLY` 的
  `0.00657038`；
- 云端产物已完整回收和哈希核验，实例已关机并确认 SSH 拒绝；
- 两份 stress reference 继续 sealed/unread。

## 最有论文价值的三段对照

1. **LF1：高 recall、极低 precision。** 事件被学出来，但 active mass 是
   teacher 的 5–6 倍，属于用大面积 false positive 换 recall。
2. **LF2：低连续场误差、零事件。** target measure 让整体误差下降，却被
   冷态多数类支配，证明低 weighted MSE 不能替代事件 competence。
3. **LF3：高 precision、正确质量和时间、recall 不足。** 它修复了前两类
   极端失败，却只学到较窄的事件核心，漏掉约 19%/23% 的 teacher support。

这三段比“又一次没过门”更有科研含量：它建立了 sparse-event 学习中
existence、mass、precision、recall、timing 彼此不可替代的对象特异证据。

## LF4 新增的 matched 机制证据

- DEV-G、DEV-M、DEV-C 都从 exact LF3-T0 权重出发，各 400 步、同一 base
  stream；DEV-M/DEV-C 还复用完全相同的 interface-band coordinates。
- DEV-G 的 `Rmin=0.81942`，且两周期 timing 都失败，说明普通追加全域监督不足。
- DEV-M 的 `Rmin=0.90926`，相对 DEV-G 增加 `0.08984`，precision、mass、
  locality、recovery 与 V/T 保存门均通过；因此冻结裁决支持
  `BOUNDARY_EXPOSURE_SUPPORTED`。它只证明对象特异的 teacher-interface
  exposure 增量，不声称 interface sampling 新颖。
- DEV-C 的 `Rmin=0.94158`，两周期 timing 均通过，但 phase weighted MSE
  升到 `0.02967`，约为 LF3-T0 的 `15.8` 倍，且 cycle-2 recovery 比 DEV-M
  下降。故 threshold-aligned BCE 未通过完整质量保存门，不能作为核心机制。
- 三臂分别因 timing、timing、phase error 未通过 entry，P0 合法地运行 0 步；
  机器终局为 `LF4_NO_DEVELOPMENT_ENTRY`，candidate 为 none。

这使论文叙事从“猜测边界不足”升级为“matched 证据确认暴露位置重要，但损失
形状仍须在 timing 与场保真之间取得可容许折中”。

## 为什么现在不继续跑 P0 或追加救援臂

P0 的科学问题是“physics 能否在保持合格 carrier 的同时降低残差”。三臂没有
同时满足完整 entry，强行运行会把 timing/field 缺陷和 physics forgetting 混在
一起。拼接 DEV-M 与 DEV-C、放宽 phase error 或新增中间权重都属于看过结果后
的新科学身份。因此本 campaign 在获得 boundary-exposure 归因后止损，不追加
同身份 GPU。

## 导师初稿与二区正面稿的差距

当前材料足以交付导师审阅：有完整问题、强基线、执行链、matched 机制证据、
失败机理、八张图和明确边界。若要升级为中科院二区定位的正面方法稿，最低还缺：

1. 以 interface exposure 为已验证 backbone，形成一个同时保持 field error 与
   timing 的单一 carrier 机制，并真正通过 entry；
2. 实际执行的无标签 physics refinement，并相对同架构 T0 形成 Pareto；
3. 若主张 phase latent，补同初始化/同 batch、只换 output-phase teacher 的
   matched ablation；
4. 多 seed 与完整实体级 formal OOD；
5. 面对 direct `LF_ONLY` 的预声明价值：accuracy noninferiority，或另一个在
   实验前冻结且可测的角色增量；
6. 只有候选形成后才开 stress，不能用 stress 救一个 nominal 未过门的方法。

这些是后续研究缺口，不是本次自动授权。当前唯一合法状态是
`next_research_execution_authorized=false`。

## 论文口径

允许写：在单 seed、nominal、fixed-discretization 对象中，matched 控制表明
teacher-interface exposure 相对普通全域追加监督显著提高最差周期 recall；
threshold BCE 则暴露了 timing 与场保真的冲突。该结论只属于冻结对象与组合。

禁止写：LF4 carrier 成功、threshold BCE 有质量保持增量、P0/PINN 有增量、
latent teacher 单独有效、优于
`LF_ONLY`、具有 OOD/stress 鲁棒性、达到 continuum truth、材料验证或投稿级
结论。

## LF5：CPU 前提反证与用户覆盖后的身份无效轨迹

CPU-T 先把 medium teacher 的
cycle-1/2 onset 与 recovery 重建为 `68/68/64/64` 条有效相邻时间边，invalid
fraction 为 0，并冻结 400-draw stream。DEV-M 的 onset mean-absolute residual
为 `0.2921/0.3100`，DEV-C 为 `0.7238/0.6041`；DEV-C 在两个周期都更差。
因此，LF4 中 DEV-C 的 aggregate timing 改善并不代表其逐 cell zero-level
alignment 更好。冻结门返回 `LF5_TZL_ALIGNMENT_NOT_SUPPORTED_CPU`。

用户在知晓该结果后明确覆盖停止条件，只授权不变的 DEV-T 作 exploratory
evidence。远端通过完整零步预检后完成 400 updates；base 与 spatial stream
精确匹配，但 temporal stream 从 step 1 即偏离 CPU 冻结身份，最终 SHA 为
`48A0C6B4...AAFB127` 而非 `8FD79D99...C9B3BD9`。因此机器终局按优先级为
`LF5_NUMERICAL_OR_IDENTITY_INVALID`，不得重跑；checkpoint/prediction 未写出，
P0 为 `NOT_RUN` 而不是失败。

step-400 非投票 telemetry 仍提供方向：recall 达 `0.9175/0.9174`，precision、
mass、recovery 和 phase MSE 均表现良好，但 cycle-1 timing error 仍为 `0.0094`
而未过 `0.005` 门。它提示 temporal-edge exposure 可能补 support，却没有解决
周期一 timing；因身份无效不能称 carrier 或机制成功。有效结论仍是 LF4 的
boundary-exposure 正向证据与 LF5 CPU 前提反证。unique next 为
`STOP_NO_SCIENTIFIC_RETRY`，任何新机制均须新合同与新授权。
