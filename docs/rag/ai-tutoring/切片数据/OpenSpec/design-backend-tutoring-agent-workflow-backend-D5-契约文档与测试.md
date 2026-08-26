# design-backend-tutoring-agent-workflow-backend

> summary: 面试问答：后端D5阶段契约文档更新与测试验证
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D5. 契约文档与测试
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-agent-workflow-backend
> 类别：架构设计

---

### D5. 契约文档与测试

- `tutoring-agent-events/api.md`（本 change 剩余真实工作）：line 77 decide agent 事件"仍不中继"改为"透传"；meta 事件示例补 `decideReason`/`questionKps`/`masterySignals` 字段说明。
- 后端测试已在工作区更新：`sendMessage_decideThinkingRelayedFirst` 断言 decide agent 事件透传；meta 新字段断言（decideReason/questionKps/masterySignals）——TutoringAppServiceTest 42/42、TutoringLlmClientTest 3/3 绿。
