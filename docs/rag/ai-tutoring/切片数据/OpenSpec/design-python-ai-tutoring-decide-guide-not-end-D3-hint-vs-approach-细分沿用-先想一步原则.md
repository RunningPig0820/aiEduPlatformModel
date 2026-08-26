# design-python-ai-tutoring-decide-guide-not-end

> summary: 明确Python decide中hint与approach的细分规则
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D3. hint vs approach 细分（沿用"先想一步原则"）
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring-decide-guide-not-end
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-python-ai-tutoring-decide-guide-not-end-D3-hint-vs-approach-细分沿用-先想一步原则.md
> 类别：开发难点

---

### D3. hint vs approach 细分（沿用"先想一步原则"）

- 答错**默认 `hint`**（只推一步：先设哪个未知数、先看哪句条件）
- 学生**明确卡住/求助**（"我不会""太难了""给个思路"）→ `approach`（思路大纲）
- **答对但未独立解出**（`correct=true, exercise_complete=false`）→ `approach` 续推思路（不给最终数值），不 `end`

复用现有「先想一步原则：默认 hint，只有明确求助才 approach」段落，只需把"作答"档挂到该原则下。
