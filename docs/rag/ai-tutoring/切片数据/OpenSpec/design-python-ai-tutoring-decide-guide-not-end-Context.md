# design-python-ai-tutoring-decide-guide-not-end

> summary: 解决Python decide误将答错判为结束会话的问题
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Context
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring-decide-guide-not-end

---

## Context

现状（已核实代码与规范）：
- `_DECIDE_SYSTEM`（`core/tutoring/prompts.py`）只有两档分类：**完全与学习无关 → `end`**、**过简/模糊但相关 → `concept`**。缺"作答但答错 → 引导"档，模型把"作答不属于题目答案"误归为"无关内容"→ 输出 `type=end`，Java `terminate()` 直接结束会话。
- `ai-tutoring` spec 的「回答错误」场景只约束了 `eval/mastery_signals`，**未约束 `type`**；「区分无关与澄清」requirement 是两档，规范层面同样缺"作答"档——prompt 只是忠实执行了规范里的两档。
- Java 侧零题目状态，无法语义区分"答错 vs 真无关"；`type=end` 且 `end_reason` 为空 → Java `terminate()`，终止回复正文 = `action.summary`。所以答错被误判为 end 后 Java 只能照单执行，**分类权必须在 Python decide**。
- 另一个 bug 源：答错时 decide 偶发输出 `reveal`（把答错误判为"学生要答案"）。Java 答案护栏拦首次（answer_request_count 0→1 降级 approach），但第二次 reveal 放行完整答案并 `ANSWER_REVEALED` 收尾，打断引导。
