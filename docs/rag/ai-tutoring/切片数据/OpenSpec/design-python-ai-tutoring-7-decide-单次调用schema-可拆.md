# design-python-ai-tutoring

> summary: 面试问答中提及decide单次调用的schema拆分设计
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 7. decide 单次调用,schema 可拆
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-python-ai-tutoring-7-decide-单次调用schema-可拆.md
> 类别：架构设计

---

### 7. decide 单次调用,schema 可拆

MVP 单次调用出 7 类判断。`Eval` 与 `Decision`(type/new_question/end_reason/safety_flag)拆成独立子结构——将来拆双次调用时模型与 schema 不变,只改编排。联调判错率高再拆。
