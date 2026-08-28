# PHK-V2.1 S1 intent 02 no-event carrier reconciliation

- `record_id`: `PHK_V21_S1_NO_EVENT_CARRIER_TYPE_AMENDMENT_001`
- `status`: `VERIFIED_IMPLEMENTATION_DEFECT_RECONCILED_WITHOUT_SOLVER_RERUN`
- `effective_date`: `2026-08-28`
- `scientific_effect`: `NONE`

## 结论

Production intent `20260828T-phk-v21-s1-q-02-zero-drive` 完成 1000 个冻结时间步，hard numerical guards 通过，两个周期的 `event_time` 均为 `null`、`peak_roi_fraction` 均为 `0.0`。然而运行时 `dataclasses.asdict` 保留了 dataclass 中 cycles 的 tuple 类型，而 `_no_event` 只接受 list；同一个 tuple 在 JSON 持久化时被转换成 list。因此 runner 错误写入 `expected_no_event_passed=false`、`CONTROL_FALSE_EVENT` 和停止 disposition。

这是 carrier-type 判定缺陷，不是求解失败、false event、物理门失败或阈值争议。原始 result、report、intent 和 manifest 均保持不可变，原始 CPU 计账继续有效；intent 02 solver 不重跑。

## 不可变来源

| 载体 | SHA256 |
| --- | --- |
| intent 02 manifest | `971D30AD94B4659648925DC271982B09408CD276752ADD02BA2977936526C95B` |
| intent 02 report | `5E3350F8C56F88BEAA7B67F2F09CFEEF731903865F41904B3CF6C1CCAE9EFD0A` |
| intent 02 result | `A4135C71CC10B86E04DA49F85114EF3DE595CB0CFCB2FDAAB840200C7AAD032C` |
| original frozen runner | `179C4C8EFF3541AB61B975515499DF5E89EA77F83CBAFCF9975EF903CBECF35C` |

## 最小修复与继续边界

[机器 amendment](../../configs/phk_v21/s1_implementation_amendment_001.json) SHA256 为 `B50BBADEC521F435EA1AFA923146237851D0B8F8C87922A97C3CBD974C98B6AE`。修复后的 runner SHA256 为 `F801B9F1EA89D2B09364BBC9AEDDBDED8FEDF8DAD125A6C6DB7F569192274E1F`；回归测试文件 SHA256 为 `9150282EBA9250E6918E84C6C9E91B74E91323976E72B75E7DB07F286247DC9D`。19 项 benchmark/evaluator/runner 测试通过，且 production intent 03 的顺序与 immutable-carrier reconciliation 检查通过。

修复只允许 list 或 tuple 作为同一两周期 carrier，并从原 report 的两个 cycle 重新计算 no-event Boolean。它不修改 object、PDE、solver、mesh、time step、event threshold、case identity、split、floor、预算、intent 02 数值或任何主张。后续 intents 必须显式绑定该 amendment；terminal summary 必须同时展示原错误记录与 correction，不能静默改写历史。

当前仍无 qualified oracle/event 或方法证据。该 reconciliation 只解除一个已证实的执行层错误停止，不构成 S1 PASS。

