# design-python-ai-tutoring-decide-guide-not-end

> summary: 收紧AI辅导reveal答案的触发门禁，仅学生明确要答案才放行
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D5. `reveal` 门禁收紧
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring-decide-guide-not-end
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-python-ai-tutoring-decide-guide-not-end-D5-reveal-门禁收紧.md
> 类别：开发难点

---

### D5. `reveal` 门禁收紧

仅当**历史中学生明确表达要答案**（"给答案""答案是多少""直接说答案"）才输出 `reveal`；答错、答偏绝不触发。Java 答案护栏（首次 reveal 降级 approach、answer_request_count 计数）仍是兜底，Python 侧收紧是减少误触发、避免第二次 reveal 放行。
