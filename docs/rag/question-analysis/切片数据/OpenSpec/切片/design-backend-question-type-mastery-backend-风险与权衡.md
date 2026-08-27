# 风险与权衡

> summary: 列举掌握度数据底盘运行风险（embedding 区分度/阈值误并/冷启动/语义迁移等）与缓解手段，明细见正文表。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-question-type-mastery-backend-风险与权衡.md
> 类别：架构设计

---

### 风险与权衡

> 检索摘要：列举掌握度数据底盘运行风险（embedding 区分度/阈值误并/冷启动/语义迁移等）与缓解手段，明细见正文表。

- [embedding 对数学术语区分度不足] → spike 前置：候选模型对比真实题型名，区分度不达标换模型（混元优先）。
- [阈值误合并/漏合并] → 阈值 = 粒度旋钮，spike 标定；误合并只影响个别题权重（累计百分比可容忍），漏合并后续人工/别名表补。
- [向量库冷启动（无近邻建新）] → 数据量上来归一越来越准；冷启动用字符规则兜底 + 建新 canonical。
- [历史掌握度语义迁移（置信度 → 正确率）] → 数据量小，旧值作初始正确率 + `train_count=1` 平滑过渡；掌握表加列非删列，回滚无损。
- [题目文本提取（零题目状态）] → 复用 `isNewQuestion` 换题检测（已有）挂落库触发器；题目文本取该轮题目，非「最后一条用户消息」。
- [`getMastery` BREAKING] → 加新字段不删旧；前端分桶保留四档视觉；`kp-coverage` 派生不变。
- [Python 端 decide 信号粒度] → 本期 Java 从 `roundCount`/`answerRequestCount` 推断，decide/信号链路 Python 零改动；若将来要更细信号再谈契约。
- [Python 向量端点不可用] → Java 桥失败回退字符规则 + 原样落库（不阻塞）；向量是增强层，主干（题目落库/掌握表/接口）不依赖向量。

> 证据：详见 `2.OpenSpec design 决策/design-backend-question-type-mastery-backend.md`（§风险与权衡）｜ 语雀-决策记录.md D3/D6/D7/D13/D18
