# design-frontend-add-ai-tutoring-frontend

> summary: 介绍独立的AI答疑SSE客户端实现方案
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 2. 独立 tutoring SSE 客户端,不复用 llm.js
> 模块: ai-tutoring ｜ 节: design-frontend-add-ai-tutoring-frontend
> 类别：架构设计

---

### 2. 独立 tutoring SSE 客户端,不复用 llm.js

`llm.js` 的 `streamChat` 只处理 `token`/`done`,不认识 `meta` 且无 `denied` 概念。新增 `api/modules/tutoring.js`,用原生 `fetch`(credentials:'include')实现通用 SSE 解析,按事件名分发:

```js
// 通用 SSE 读取器:解析 event:/data: 行,按 event 名调用对应 handler
function readSSE(response, { onMeta, onToken, onDone, onError }) {
  // event: meta → onMeta(JSON)
  // event: token → onToken(data.content)
  // event: done → onDone(data)
  // event: error → onError(new Error(...))
}
```
客户端导出(非流式走 `request.js` axios,流式走 fetch):
- `startSession(message, handlers)` → `POST /api/tutoring/sessions`(SSE)
- `sendMessage(sessionId, content, handlers)` → `POST /api/tutoring/sessions/{id}/messages`(SSE)
- `requestAnswer(sessionId, handlers)` → `POST /api/tutoring/sessions/{id}/request-answer`(SSE)
- `getSession(sessionId)` → axios
- `archiveSession(sessionId)` → axios
- `getMastery(studentId)` → axios(未来图谱用)
- `recognize(file)` → `POST /api/tutoring/ocr`(FormData,axios,**超时放宽到 30s**)

每次 SSE 调用返回 `cancel()` 函数(组件卸载/停止生成时调用)。
