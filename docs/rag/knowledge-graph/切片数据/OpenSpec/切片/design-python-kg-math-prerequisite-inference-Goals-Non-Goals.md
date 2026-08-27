# Goals / Non-Goals
> summary: 目标：按教材章节顺序推断TEACHES_BEFORE、LLM多模型投票推断PREREQUISITE、定义依赖抽取、推断教学知识点并融合多证据输出JSON；非目标：不处理其他学科、不做人工审核、不处理高中数据。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-kg-math-prerequisite-inference-Goals-Non-Goals.md
> 类别：数据关联

> 检索摘要：目标：按教材章节顺序推断TEACHES_BEFORE、LLM多模型投票推断PREREQUISITE、定义依赖抽取、推断教学知识点并融合多证据输出JSON；非目标：不处理其他学科、不做人工审核、不处理高中数据。

**Goals:**
- 基于教材章节顺序推断 TEACHES_BEFORE
- 从定义文本抽取定义依赖
- LLM 多模型投票推断 PREREQUISITE
- 从教材章节推断教学知识点（补全缺失数据）
- 融合多证据来源
- 输出 JSON 文件（手动验证后导入）
- 支持 LLM 任务断点续传

**Non-Goals:**
- 不处理其他学科（物理/化学等）
- 不做人工审核（Demo 阶段自动化）
- 不处理高中数据（知识点数据源缺失）

> 证据：详见 `2.OpenSpec design 决策/design-python-kg-math-prerequisite-inference.md`（§Goals / Non-Goals）
