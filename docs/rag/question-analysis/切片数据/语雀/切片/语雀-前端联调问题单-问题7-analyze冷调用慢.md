# analyze 冷调用慢

> summary: analyze-question 冷调用 curl 实测约 5s，浏览器端偶发超 30s 被前端超时截断，根因是冷调用 LLM 推理慢且无缓存。
> 权威度: 0.8
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/语雀/语雀-前端联调问题单-问题7-analyze冷调用慢.md
> 类别：开发难点
> 状态：⚠️ 待办

---

### 问题7：analyze 冷调用慢
> 状态：⚠️ 待办
> 检索摘要：analyze-question 冷调用 curl 实测约 5s，浏览器端偶发超 30s 被前端超时截断，根因是冷调用 LLM 推理慢且无缓存。

| 属性 | 内容 |
|---|---|
| 现象 | curl 实测 ~5s，浏览器端偶发超 30s 被前端超时截断 |
| 触发流程 | 题型分析首次调用 analyze-question |
| 根因 | 冷调用 LLM 推理慢 + 无缓存 |
| 修复方案 | 待优化（P2）：可用缓存/预热/流式 |
| 状态 | ⚠️ 待办（P2） |
| 证据 | 语雀-方案设计1-问题6 |

> 证据：详见 `1.语雀/语雀-前端联调问题单.md`（§问题7）｜ 完善文档 02-题型分析主流程怎么走.md
