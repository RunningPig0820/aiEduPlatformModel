# design-backend-tutoring-agent-workflow-backend

> summary: 面试问答：后端D3阶段解决masterySignals序列化的契约问题
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D3. masterySignals 序列化（隐性坑）：新建 SseMasterySignalDTO
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-agent-workflow-backend

---

### D3. masterySignals 序列化（隐性坑）：新建 SseMasterySignalDTO

领域 `MasterySignalItem.kpLabel` 标了 `@JsonProperty("kp_label")`（Java↔Python 内部契约 snake_case）。若直接把 `List<MasterySignalItem>` 放进 `SseMetaDTO.masterySignals`，Jackson 会按字段上的 `@JsonProperty` 序列化成 `{kp_label, signal}`——**不符合前端 camelCase 契约**（spec 要求 `{kpLabel, signal}`）。

- 新建 `SseMasterySignalDTO {kpLabel, signal}`（camelCase，sse dto 包）。
- `buildMeta` 映射：`action.getMasterySignals() → List<SseMasterySignalDTO>`（kpLabel/signal 一一透传）。
