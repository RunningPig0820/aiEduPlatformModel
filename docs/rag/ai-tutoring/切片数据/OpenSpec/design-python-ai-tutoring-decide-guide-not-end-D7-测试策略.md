# design-python-ai-tutoring-decide-guide-not-end

> summary: 制定AI辅导规则的测试策略，含语义断言与real用例
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D7. 测试策略
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring-decide-guide-not-end
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-python-ai-tutoring-decide-guide-not-end-D7-测试策略.md
> 类别：开发难点

---

### D7. 测试策略

- **prompt 语义断言**（`test_prompts.py`，文本断言）：新增"作答→引导"档、无关→concept继续、end 收紧三类、reveal 门禁、end 不给答案四组断言；与既有 `test_end_vs_concept_distinction`/`test_first_message_defaults_to_hint`/`test_think_one_step_first_in_prompt` 并列
- **real 用例**（可选，`tests/tutoring/real/`）：实测 LLM 对"答错"输入的分类行为，人工验收
- 因 LLM 分类无法确定性单测，文本断言保证**规则存在**，real 用例保证**模型遵守**；Java 护栏兜底偶发
