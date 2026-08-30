# 2026-08-30 PHK-V2.2R v1.1 alignment closeout

- `status`: `P0_V11_ALIGNMENT_COMPLETE_P1_NOMINAL_ACTIVE`
- `evidence_role`: `ENGINEERING_CONTRACT_AND_ENTRYPOINT_VERIFICATION_ONLY`
- `alignment_commit`: `69109cd324a6d5bf4690fe981086dc2f987eceed`
- `program_contract_sha256`: `A413F56A2317CEFF15FFF2D3BD183C11D990F2E47E8BA33F7316F11567275272`
- `method_contract_sha256`: `FEEFB36A4D86CACFA6CBAA8C263E7071421415CE88B4F7FBF6BA5F31B9B71D4F`

## VERIFIED

P0 将 v1.1 program/method contracts、四臂-only nominal runner、full-only
decision、confirmation plan/final candidate freeze 两阶段 schema、AutoDL run
card、manuscript 和 claim registry 对齐。可执行 nominal 身份固定为：

- `STRONG_RAW`、`MF_ONLY`、`SAMPLER_ONLY`、`MF_PLUS_SAMPLER`；
- FP64、seed 17、Band A、scratch start；
- `512/128/128` collocation 点，Adam，严格 1000 updates；
- 无 early stop、warm start、L-BFGS、continuation、额外 checkpoint 或 arm override；
- nominal reference 只在本地 development evaluation 使用，两个 stress references 继续密封。

验证门禁为 PHK-V2.2R 聚焦测试 16/16、PHK-V2.1+V2.2R 组合回归 47/47，以及
`DOCUMENT_CONSISTENCY_VALID`。这些门禁证明机器合同和入口一致，不证明训练 competence、
四臂排序、可归因增益或 sealed-case 泛化。

## Evidence boundary

本记录关闭 profile 之后的 P0 对齐阶段，不覆盖
[GPU profile closeout](2026-08-30-phk-v22r-gpu-profile-closeout.md) 的历史事实，也没有执行
四臂 nominal、读取 stress reference、冻结 candidate 或建立正向神经方法结果。

GPU、进程和 tmux 是否空闲属于启动时实时状态，不写成 P0 的持久事实。下一步只能按
[v1.1 AutoDL run card](../../cloud/phk_v22r_autodl/README.md) 执行 P1 nominal，并在启动前
重新核验实例、GPU、进程、部署 commit、合同哈希与预算。
