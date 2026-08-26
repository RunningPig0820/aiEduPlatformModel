# 把答疑的完整调用链路画出来，前端 / Java / Python 各自负责什么？

> summary: 前端（纯交互）→ Java（平台层）→ Python（纯智能），内部 token 鉴权，各端职责单一、边界清晰。
> 权威度: 1.0 ｜ 来源: 引导问题 ｜ 锚点: 把答疑的完整调用链路画出来，前端 / Java / Python 各自负责什么？
> 模块: ai-tutoring ｜ 节: 业务流程图
> COS路径: ai-tutoring/rag-slices/引导问题/引导问题-46-业务流程图-把答疑的完整调用链路画出来前端Jav.md
> 类别：业务流程

## 回答

**核心结论**：前端（纯交互）→ Java（平台层）→ Python（纯智能），内部 token 鉴权，各端职责单一、边界清晰。

**分层展开**：
- **前端 React**：纯交互/渲染/会话状态机/SSE 消费/离线兜底；不碰智能逻辑、不直连 COS（transcript 由后端代理），本地只存 sessionId 元数据。
- **Java 平台层**：认证（HttpSession）、护栏（确定性规则）、编排 orchestrate、掌握度/错误事件落库、COS 归档；不暴露 Python 内部端点，护栏只读 type+count 不看对话（防提示词攻击）。
- **Python 纯智能**：decide/generate/question-understand/subject-classify；无状态（零题目状态，题目从 history 推断）；不碰 MySQL/KG/COS，只吃 Java 传的全量上下文。
- **数据流**：前端发消息 → Java orchestrate → 调 Python decide（SSE 中继）→ 等 meta → Java postDecide 护栏 → 落库 → 调 Python generate → buildStream 流式回前端。
- **三个设计要点**：审批归属 Java（"球员不能当裁判"）；Python 无状态可水平扩展；会话状态只有 3 态（ACTIVE/ARCHIVED/TERMINATED），不随题目/对话增长。
