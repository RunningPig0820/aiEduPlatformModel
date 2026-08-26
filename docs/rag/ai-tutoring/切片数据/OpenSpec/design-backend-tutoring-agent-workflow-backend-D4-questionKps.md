# design-backend-tutoring-agent-workflow-backend

> summary: 面试问答：后端D4阶段新增questionKps字段的契约透传
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D4. questionKps
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-agent-workflow-backend
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-backend-tutoring-agent-workflow-backend-D4-questionKps.md
> 类别：架构设计

---

### D4. questionKps

- `ActionMeta` 新增 `@JsonProperty("question_kps") List<String> questionKps`（Python decide 模型读题顺手列涉及知识点，可空，不额外调用 LLM）。
- `SseMetaDTO.questionKps`（List<String>）透传。
- Python 未下发时（后端先部署/未改 Python）→ Java 透传 null → 前端显示占位"—"（前端 design D4，数据驱动）。
