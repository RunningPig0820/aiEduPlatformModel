# design-backend-ai-tutoring

> summary: 答疑AI后端微服务拓扑架构总览
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 架构总览（微服务拓扑）
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-backend-ai-tutoring-架构总览微服务拓扑.md
> 类别：架构设计

---

## 架构总览（微服务拓扑）

```
┌────────────────────────────────────────────────────────────────┐
│ 前端（学生端）                                                  │
│   │  REST / SSE（登录态在 Java）                                │
│   ▼                                                            │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ Java API 网关 + 答疑域服务（两个角色）                        │   │
│ │ 角色1 对外网关：认证(HttpSession) / 路由 / SSE 透传            │   │
│ │ 角色2 答疑域服务：会话 / 护栏 / 掌握度 / 错误事件 / KG / COS     │   │
│ │                                                            │   │
│ │  一次学生消息的编排（Java 主导）：                            │   │
│ │  ① 安全预检（关键词）                                        │   │
│ │  ② 组装上下文 {history, counters, 掌握度快照, subject=math}   │   │
│ │  ③ 调 Python decide（非流式）→ action 元数据                  │   │
│ │  ④ 护栏校验 action（答案/轮次/换题/收尾）→ 落库副作用          │   │
│ │  ⑤ 调 Python generate（流式）→ SSE 透传前端                   │   │
│ └──────────────┬────────────────────────────────────────────┘   │
│                │ 内部 token（复用 llm-gateway internalToken 模式）│
│                ▼                                                │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ Python 答疑 agent（ai-edu-ai-service 现有 LLM 服务内的模块）  │   │
│ │  · 无状态、纯智能，不碰 MySQL/KG/COS                        │   │
│ │  · POST /api/tutoring/decide   决策（快，出 action 元数据）   │   │
│ │  · POST /api/tutoring/generate 生成（流式，出正文）           │   │
│ └──────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```
