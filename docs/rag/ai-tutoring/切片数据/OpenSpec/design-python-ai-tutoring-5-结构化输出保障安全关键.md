# design-python-ai-tutoring

> summary: 面试问答中说明结构化输出保障的四段降级方案
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 5. 结构化输出保障(安全关键)
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-python-ai-tutoring-5-结构化输出保障安全关键.md
> 类别：开发难点

---

### 5. 结构化输出保障(安全关键)

`bind_tools([ActionMeta]) + 手动解析 tool_call` → 失败 JSON mode → 失败正则提取 + Pydantic 校验 → 失败兜底 `ActionMeta(type=hint, degraded=true)`。四段降级管线是**硬需求**,保证 API 绝不返回畸形 ActionMeta。兜底时 `degraded=true` 置位,Java 靠该信号监控 Python 降级频次(Java 侧核实后补的字段)。
- 重试域划分:Python 内部不重试 LLM 调用(快速失败交 Java 重试);Python 内部重试 schema 解析(带纠错 prompt)
- **冒烟测试结论(2026-08-04, task 1.3)**:deepseek-v4-flash 实测 function calling ✅ 可用(返回标准 tool_call)、json_mode ✅ 可用(返回干净 JSON)。→ structured.py 默认路径走 **function_calling**,json_mode 作为第一级兜底(不跳级,四段管线顺序不变)
- **实现发现(task 3.1)**:stage ① 用 **`bind_tools([ActionMeta])` 而非 `with_structured_output`** —— langchain-openai 1.x 的 `with_structured_output` 默认走 `response_format=json_schema`(Structured Outputs),deepseek 实测返回 400"response_format type unavailable";`bind_tools` 走原生 tool-calling 实测可用。tool_call args 交给 Pydantic 校验,不合法则降级 ②。真实模型已验证 stage ① 直接走通
