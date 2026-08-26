# design-python-ai-tutoring

> summary: 面试问答中明确AI辅导审批归属Java侧实现
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 4. 审批(护栏)归属 Java,Python 不实现
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-python-ai-tutoring-4-审批护栏归属-JavaPython-不实现.md
> 类别：开发难点

---

### 4. 审批(护栏)归属 Java,Python 不实现

**选择**: Java 侧确定性代码做动作出口审批。Python 只按契约输出 action,不做任何审批。
**原因**: ①数据在 Java,审批后果(计数器/归档/掌握度)必须回 Java 执行;②球员不能当裁判——LLM 本能是有求必应;③**防提示词攻击**——LLM 层可被骗,Java 审批只读 type+count、不读对话,骗不了;④**规则数字可页面/配置运营控制**——轮次/要答案次数/频率走配置中心或后台。
**备选**: 审批放 Python(脚本/图节点)——技术上可行,但规则与 LLM 同居一个进程,可被"合理化";且后果仍须回 Java,省不了调用。
