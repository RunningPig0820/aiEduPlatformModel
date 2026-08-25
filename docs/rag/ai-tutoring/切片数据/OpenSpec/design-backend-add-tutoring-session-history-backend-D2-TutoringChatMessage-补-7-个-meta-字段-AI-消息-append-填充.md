# design-backend-add-tutoring-session-history-backend

> summary: 面试问答：答疑会话历史后端需补TutoringChatMessage的7个meta字段
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D2. `TutoringChatMessage` 补 7 个 meta 字段 + AI 消息 append 填充
> 模块: ai-tutoring ｜ 节: design-backend-add-tutoring-session-history-backend

---

### D2. `TutoringChatMessage` 补 7 个 meta 字段 + AI 消息 append 填充

给 `TutoringChatMessage` 增加 7 个可空字段（`@JsonProperty` snake_case，与 Java↔Python 契约一致）：`type / denied / decide_reason / round / question_kps / eval / status`。

**填充位置：仅 `buildStream.doOnComplete`（行 616）**，AI 回复 append 时填 meta。行 753（`ensurePersisted`）是 start 的用户消息，meta 恒 null（前端对 user 消息不建 agentFlow）。填充后 Redis append + 行 618 `archiveTranscript` 重写 COS，meta 自动进 COS，无需改归档器。

**meta 取值 = `buildMeta` 同源镜像**（action/allowedType/guard/session 均在 buildStream 参数作用域），保证历史复原与 live SSE 渲染逐字段一致：

| 字段 | 取值 | 依据 |
|---|---|---|
| `type` | `allowedType.name().toLowerCase()` | **生效类型**（护栏降级后），非 `action.type`——`deriveTurnFlow.guideStep/clarify` 依赖此值，live 的 SSE meta.type 也是 allowedType |
| `denied` | `guard.isAllowed() ? null : ActionType.fromCodeOrDefault(action.getType()).name().toLowerCase()` | 护栏拒绝时的原始请求类型（如 reveal），eval 门控判定用 |
| `decide_reason` | `action.getReason()` | Python 决策自由文本 |
| `round` | `session.getRoundCount()` | applySideEffects 已跑完（postDecide 步骤 7 在 buildStream 前），即当前轮次 |
| `question_kps` | `action.getQuestionKps()` | List\<String\>，前端 `Array.isArray` 判定 |
| `eval` | `action.getEval()` | `EvalInfo` 对象（snake_case 内字段）——命名兼容见 Risk R2 |
| `status` | `session.getStatus()?.name()` | ACTIVE/ARCHIVED/TERMINATED；最后一轮 reveal/end 收尾后为 ARCHIVED → 前端 ⑥ 归档点亮 |

用户消息（行 175/202/204/215/753）meta 全空，不填。
