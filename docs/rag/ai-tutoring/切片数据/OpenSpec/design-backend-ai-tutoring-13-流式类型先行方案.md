# design-backend-ai-tutoring

> summary: AI辅导采用类型先行的流式交互方案
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 13. 流式：类型先行（方案 ②）
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-backend-ai-tutoring-13-流式类型先行方案.md
> 类别：架构设计

---

### 13. 流式：类型先行（方案 ②）

**决定**：MVP 就做流式，但用"类型先行"协议保证护栏安全——即决策 2 的两段式：`decide`（非流式，先出 type）→ Java 校验 → `generate`（流式正文）。**绝不**边流式边拦截（那样答案可能已漏出）。

前端 SSE 事件：
- `event: meta, data: {"session_id", "type": "hint", "round_count": 1}` （护栏已通过的类型先行到达）
- `event: token, data: {"content": "先找题目里的已知条件..."}` （正文流）
- `event: done, data: {"session_id", "status", "eval": {...}}`
