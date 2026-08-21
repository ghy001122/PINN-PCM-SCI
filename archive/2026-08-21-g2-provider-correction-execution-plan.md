# Live plan：G2 provider 修正与单次 clean integration

- `lifecycle_state`: `ACTIVE`
- `blocker_id`: `NONE`
- `authorization_state`: `G2_PROVIDER_CORRECTION_APPROVED`
- `authorization`: `USER_CONFIRMED_GRILL_WITH_DOCS_OPTION_A_2026-08-20`
- `execution_authorized`: `true`
- `claim_status`: `NO_SCIENTIFIC_CLAIMS`

## 当前唯一动作

在 20 分钟本地窗口内，以 TDD 将 pybind11 Python sdist 与 CMake provider
Git 源码分成两个已锁定工件。测试通过后，登记并执行一次使用新环境合同、
clean prefix `/opt/qpop-cpc-v1-env-g2-final-002` 和独立 evidence root 的
`resolve → preflight → build → verify`，环境墙钟上限 120 分钟、CPU、两个
build jobs。只有 verify 通过才登记一次 30 分钟上限的 canonical native
Q-POP smoke。

## 停止边界

- 首个依赖、来源、配置、ABI、编译、测试、verify、转换或 evaluator 失败即落账收口；
- 不自动进行第二次集成；只有可证明的方法外执行损坏可按原配置精确重放；
- 不改变 Q-POP CPC v1、KC 科学合同、PhysicalContract 目标或 benchmark；
- 不启动 G3、PINN、pilot、GPU 或 formal。

授权事实见 `docs/experiment/2026-08-20-g2-provider-correction-authorization.md`。
