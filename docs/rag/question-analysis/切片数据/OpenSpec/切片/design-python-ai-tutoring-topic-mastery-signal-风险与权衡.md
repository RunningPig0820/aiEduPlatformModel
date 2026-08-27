# 风险与权衡

> summary: 列举信号题型化风险（题型名稳定靠 prompt/改名漏改纠错/snapshot 脱钩冷启动/历史口径变化）与缓解，明细见正文。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-python-ai-tutoring-topic-mastery-signal-风险与权衡.md
> 类别：开发难点

---

### 风险与权衡

> 检索摘要：列举信号题型化风险（题型名稳定靠 prompt/改名漏改纠错/snapshot 脱钩冷启动/历史口径变化）与缓解，明细见正文。

- [题型名稳定仅靠 prompt 约束] → LLM 天生爱换说法，纯一句「别换说法」不够。缓解：few-shot 锚定 + 「最常见最短命名」约束 + 后端字面归一化兜底（不完美，但本期不做同义词聚类）。
- [改名漏改纠错提示词 → 掌握度静默丢失] → `_schema_instructions` 与模型字段名脱节。缓解：tasks 3.1 显式列出，测试断言纠错提示词含 topic_label。
- [mastery_snapshot 脱钩后题型名无候选接地] → 题型名由模型自由生成，冷启动无约束。缓解：few-shot + 规范约束；后续题型库聚合后可由后端回填先验（不在本期）。
- [历史数据口径变化] → 旧数据知识点粒度、新数据题型粒度。缓解：后端并行过渡（旧表保留），Python 无需处理。

> 证据：详见 `2.OpenSpec design 决策/design-python-ai-tutoring-topic-mastery-signal.md`（§风险与权衡）
