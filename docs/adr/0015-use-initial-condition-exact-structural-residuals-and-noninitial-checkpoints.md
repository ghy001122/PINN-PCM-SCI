# 使用初值精确的结构残差表示和非初始 checkpoint

raw-time、identity-clock 与 KC 的结构场统一表示为满足冻结初值的解析基项加时间消失残差，使 `t=0` 的 η 严格等于 PhysicalContract 初值；任何 Fourier/PHA 修正也必须乘以时间门控并在 `t=0` 消失。physics audit 的 step 0 只用于冻结残差归一化尺度，不得参加 checkpoint 选择；正式候选从第一次参数更新后开始，仍按最大归一化原物理违规、总违规和最早步的 oracle-blind 顺序选择。该决策修复了小输出头梯度饥饿与“初始化天然归一化为 1 而被选中”的实现陷阱，但不声称这些修复足以解析结构事件；修复后的 raw-v3 负面结果必须保留。
