# PINN-PCM-SCI

面向“物理信息神经网络 × 氧化物相变材料/器件”的纯软件研究项目。目标是以可复现、证据闭合的方式推进到中科院二区 SCI 定位的论文初稿；该定位不是期刊接收承诺，合成数值证据也不等同于实验验证。

## 当前状态

- `phase_id`: `BOUNDED_METHOD_IMPLEMENTATION_NEGATIVE_CLOSEOUT`
- `lifecycle_state`: `AWAITING_NEW_SCIENTIFIC_ROUTE`
- `blocker_id`: `RAW_EVENT_NOT_RESOLVED_AFTER_BOUNDED_IMPLEMENTATION_REPAIRS`
- `claim_status`: `BOUNDED_NEGATIVE_DEVELOPMENT_RESULT_NO_FORMAL_EVIDENCE`

Q‑POP 专用环境、原生最短 smoke、HDF5 转换、独立 evaluator、七未知量 raw/identity/KC PINN、完整导数回拉和训练协议已经实现。作者随包参考轨迹确认存在结构事件，但修复初值表示与 checkpoint 选择后的强 raw 基线仍不能解析相区动态；R4 动态电子序参量约化在固定 pilot 网格上数值不收敛。因此当前实现路线已经有界收口，KC 判别 pilot、formal、GPU 和正面方法主张均未开放。

当前执行边界只由 [active_phase.md](active_phase.md) 决定；已核验状态见 [PROJECT_STATE.md](PROJECT_STATE.md)，唯一 live plan 见 [docs/plans/NEXT_ACTIONS.md](docs/plans/NEXT_ACTIONS.md)。研究口径见 [CONTEXT.md](CONTEXT.md)，完整文档路由见 [docs/README.md](docs/README.md)。
