# design-python-2026-08-12-tutoring-agent-protocol

> summary: 面试问答中工具阶段协议预留暂不实现真实工具
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 4. 工具阶段(tool)协议预留,不实现真工具
> 模块: ai-tutoring ｜ 节: design-python-2026-08-12-tutoring-agent-protocol
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-python-2026-08-12-tutoring-agent-protocol-4-工具阶段tool协议预留不实现真工具.md
> 类别：架构设计

---

### 4. 工具阶段(tool)协议预留,不实现真工具

事件协议包含 `tool` 阶段与字段,但本次**不接入真实工具**。答疑子 agent 作为可插拔单元的边界是稳定的契约(decide/generate/ActionMeta);将来知识图谱 agent 建成后,答疑通过工具调用它(模型主动触发,见 Context 中的演进)。
