# 数据访问状态与本轮数值子集

**P03 OPEN。** 当前已发布的精选成果身份为[fa475c2](https://github.com/ghy001122/PINN-PCM-SCI/commit/fa475c257651c17fcfe83007ab0fe238c6c5995c)，发布核验版本为[9414c1d](https://github.com/ghy001122/PINN-PCM-SCI/tree/9414c1da37cb9a101bf3ed812d248f63d4454470)。[发布记录](../../docs/notes/2026-09-28-manuscript-circuit-screen-release.md)列出公开范围和排除项。既有PCHIP预测已进入精选Git成果，十条原始源电流轨迹与历史完整数据包尚未因此获得外部访问。

本轮增加一个本地评分子集：从十条本项目生成的作者模型复算数组裁取time、voltage、device/load/capacitor current与固定参数，保存197点观测、两种重构、多项式和完整评分入口。共享数组只保存一次，保留FP64、全部原时刻和来源身份。原评分电流直接来自保存模型数组，不由预测生成。本轮子集与旧稿的24.6 GB全场复算包是不同范围，不能相互替代。

实际子集入口为[scoring-subset/README.md](scoring-subset/README.md)，独立评分记录为[build/independent-reproduction.json](build/independent-reproduction.json)，实际完成状态以该记录为准。科研执行收口时没有授权公开上传、创建DOI、发送审稿链接或Git发布；用户随后单独批准将本评分子集随精选Git成果发布，范围与远端核验见[发布记录](../../docs/notes/2026-09-28-cubic-energy-comparison-release.md)。该发布使外部读者可以取得本轮保存数组评分子集，但不声称完成全论文P03，也不声称包含神经AD重新计算、检查点推理或重新训练。

现稿仅更新公开版本和真实访问状态；未改变原始结果。新的CS和能量结果作为本轮独立报告，不混入旧合成二维模型的材料验证。未修改的完整补充继续链接[原58页PDF](../paper_revision_20260927_circuit_screen/supplement.pdf)及其[Markdown源](../paper_revision_20260927_circuit_screen/source/supplement.md)。

后续数据发布依然需要作者明确批准范围和权利，并落实外部实际获取与所声明能力的复核证据。沿用[既有具体访问方案](../paper_revision_20260927_circuit_screen/data-access-plan.md)：项目合成数据、项目代码、作者MIT模型代码、第三方实验CSV及出版社图片分别处理许可；代码许可不覆盖第三方数据或图片。实验原始CSV和论文PDF不进入本轮数值子集。未创建任何外部账号记录或数据DOI。

本轮仅本地CPU工作，未为分析或文稿同步启动GPU。科研执行收口时新科学产物和最终稿件仍待同步；后续Git授权只同步本发布记录列出的精选内容，不启动AutoDL，也不把硬链接表述为独立备份。历史24.6 GB包不移动、不重跑、不删除，原归档缺口继续按既有记录保留。
