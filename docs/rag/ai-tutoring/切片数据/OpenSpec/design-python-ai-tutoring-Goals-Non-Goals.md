# design-python-ai-tutoring

> summary: Python AI答疑agent的目标与非目标范围定义
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Goals / Non-Goals
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-python-ai-tutoring-Goals-Non-Goals.md
> 类别：项目介绍

---

## Goals / Non-Goals

**Goals:**
- Python 答疑 agent 独立模块: `decide`(非流式出动作元数据)/ `generate`(流式 SSE 出正文)两端点
- 类型先行流式: `meta`(护栏放行的 type)→ `token`(正文)→ `done`,护栏拒绝时无 token
- 动作类型闭集契约(hint/approach/reveal/concept/switch/end),与 Java 契约对齐
- 结构化输出四段降级管线,保证绝不吐畸形 ActionMeta
- 每轮输出掌握度信号(mastery_signals),label 接地到 mastery_snapshot
- 拍题 OCR 前置:照片 → OCR → 学生确认 → 进答疑
- 测试用 deepseek-v4-flash 走流程(非免费),生产模型配置驱动

**Non-Goals:**
- **不做护栏判断**(答案出口/轮次/换题/收尾都归 Java 侧 ai-tutoring change)
- 不做会话生命周期/落库/URI 解析(Java 侧)
- 不做 LangGraph 多步 agent / 举一反三 / 错题集(阶段 2,契约预留)
- 不建独立服务进程(挂在 `ai-edu-ai-service` 内)
- 不做行为风控/多学科(仅数学)
