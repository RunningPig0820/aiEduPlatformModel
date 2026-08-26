# 换题判定为什么放在 Java 而不是 Python？"短路"省了什么？

> summary: 换题判定为什么放在 Java 而不是 Python？"短路"省了什么？
> 权威度: 1.0 ｜ 来源: 引导问题 ｜ 锚点: 换题判定为什么放在 Java 而不是 Python？"短路"省了什么？
> 模块: ai-tutoring ｜ 节: Agent架构
> COS路径: rag-slices/ai-tutoring/引导问题/引导问题-60-Agent架构-换题判定为什么放在Java而不是Py.md
> 类别：架构设计

## 回答

**核心结论**：Python 无状态，区分不了"本轮刚换 vs 早几轮已换"，只有 Java 知道何时收到新图——判定放 Java，Python 短路省调用。

**分层展开**：
- **判定权在 Java**：Java 在 sendMessage 时检测新图 URL / 新题文本首次出现在 history → 本轮置 is_new_question=true（Java 有"新图进来"的一手信息）。
- **Python 短路**：decide 看到 is_new_question=true → 直接返回 type=switch（new_question 填新题文本），**不调 LLM**——100% 准、省一次模型调用和时间。
- **为什么不能放 Python 从 history 推断**：Python 无状态，每次都是全量 history，区分不了"本轮刚换 vs 早几轮已换"，从历史推断换题会误判。
- **Java 侧重置**：换题后重置 answer_request_count/轮次计数，新题从零开始。
- **追问点**："换题是高频场景吗？" → 是——学生做完一题贴下一题是最常见的打断；确定性短路让换题零延迟、零 token，还防模型被旧题带偏（提示词也约束"不要被历史中占多数的旧题带偏"）。
