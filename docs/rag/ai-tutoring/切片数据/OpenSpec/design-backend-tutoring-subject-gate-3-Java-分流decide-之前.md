# design-backend-tutoring-subject-gate

> summary: 介绍Java在decide前的分流规则与失败降级处理
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 3. Java 分流（decide 之前）
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-subject-gate
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-backend-tutoring-subject-gate-3-Java-分流decide-之前.md
> 类别：操作流程

---

### 3. Java 分流（decide 之前）

- **拍题（建会话）**：先 subject-classify → math 才建会话；非 math 不建，返回「仅支持数学」提示（SSE 直接返回提示流，无会话行）。
- **换题（消息带新图）**：新图先 subject-classify → 非 math 跳过该新题（不结算旧题为该题、不记录新题），返回提示；math 正常走 is_new_question→switch 结算。
- **失败降级**：classify 异常/超时 → 按 math 放行（不阻断答疑；数据污染见 Risks 治理）。
- **会话记录真实 subject**：`TutoringSession.start(studentId, subject)` 传 classify 结果（不再无条件 "math"）。
