# design-python-2026-08-12-tutoring-agent-protocol

> summary: 面试问答中agent协议支持master/sub两层嵌套结构
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 5. 两层嵌套(level: master/sub)
> 模块: ai-tutoring ｜ 节: design-python-2026-08-12-tutoring-agent-protocol
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-python-2026-08-12-tutoring-agent-protocol-5-两层嵌套level-master-sub.md
> 类别：架构设计

---

### 5. 两层嵌套(level: master/sub)

协议含 `level` 字段,为主 agent 预留:主 agent 的思考阶段(解析意图→选 agent→编排)与子 agent 的思考阶段(感知→...→记忆)可嵌套展示。本次只有 `sub` 层。
