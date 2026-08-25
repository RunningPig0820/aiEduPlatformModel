# decide 决策器的动作闭集是哪六个？提示词里怎么约束模型不乱输出？

> summary: 动作闭集六值——hint / approach / reveal / concept / switch / end，每个动作都有严格的语义边界。
> 权威度: 1.0 ｜ 来源: 引导问题 ｜ 锚点: decide 决策器的动作闭集是哪六个？提示词里怎么约束模型不乱输出？
> 模块: ai-tutoring ｜ 节: Agent架构
> 类别：Agent架构

## 回答

**核心结论**：动作闭集六值——hint / approach / reveal / concept / switch / end，每个动作都有严格的语义边界。

**分层展开**：
- **hint**：一条引导性反问，推学生走一步（"这题要先设哪个未知数？"），零步骤零答案。
- **approach**：思路步骤大纲（步骤名 + 关键公式），不给完整演算和最终数值。
- **reveal**：完整解答——**仅当学生明确要答案**（"给答案""直接说答案"），且 Java 护栏 2 次计数放行；答错/答偏绝不触发 reveal。
- **concept**：澄清/追问/引导回题——接住不在答题的内容（闲聊/状态/模糊输入），不终止会话。
- **switch**：换题，new_question 必填（新题文本/图片）。
- **end**：收尾，end_reason 联动（COMPLETED/ANSWER_REVEALED/ABANDONED/ROUND_LIMIT）。
- **提示词怎么约束不乱输出**：① 闭集 JSON schema（bind_tools function calling，ActionMeta 作 tool）；② 两分法——在答题（无论对错）绝不 end/reveal；③ 先想一步原则——默认 hint，只有明确求助/卡住才升 approach；④ exercise_complete 联动——end=COMPLETED 必须 correct && exercise_complete。
- **追问点**："hint 和 approach 区别？" → hint 只推一步反问，approach 是完整思路骨架——先想一步原则：默认 hint，卡住才 approach。
