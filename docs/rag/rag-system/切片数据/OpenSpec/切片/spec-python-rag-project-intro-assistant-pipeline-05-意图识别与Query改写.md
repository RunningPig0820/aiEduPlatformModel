# 意图识别与Query改写
> summary: 意图识别与Query改写
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-python-rag-project-intro-assistant-pipeline-05-意图识别与Query改写.md
> 类别：架构设计

---

## 文档说明
> 本文件由 OpenSpec 设计素材（spec-python-rag-project-intro-assistant-pipeline.md）按业务主题「意图识别与Query改写」重切合并。
> 设计阶段素材：真实实现以权威度 0.8 的 canonical 真相源 + 代码为准（代码已部分落地）；含 已落地 / 构想未实现 / 待决策 内容，引用需核对代码。

### Requirement: intent 结构化输出（扩展既有 classify）
> 检索摘要：intent 阶段怎么结构化识别——LLM 输出 anchor/candidates、失败回退关键词且不阻断链路？

系统 SHALL 在每轮开头调用 LLM（非流式、0 温度、关思考）输出结构化元数据 `{anchor, category, switch_detected, ambiguous, candidates}`；LLM 失败/超时/非闭集 → 回退关键词锚定（`ANCHOR_RULES` + `_fallback_anchor`），degraded 标记走 200，不阻断链路。

#### Scenario: 正常分类
- **WHEN** 学生问"这个项目的整体架构是什么"
- **THEN** intent 输出 `{anchor:"ai-tutoring", category:"项目介绍", switch_detected:false, ambiguous:false, candidates:["ai-tutoring"]}` 及锁定节

#### Scenario: LLM 失败兜底
- **WHEN** intent LLM 调用失败或输出非闭集类别
- **THEN** 回退 `_fallback_anchor` 得 locked_sections，intent 事件带 degraded 标记，链路继续

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-project-intro-assistant-pipeline.md`（§Requirement: intent 结构化输出）

### Requirement: Query 改写透传
> 检索摘要：Query 改写怎么透传——基于原始问题与上下文生成检索式改写、前端看前后对比？

系统 SHALL 基于原始问题与当前上下文（anchor、历史）生成改写后检索式 query，`rewrite` 事件透传 `{originalQuestion, rewrittenQuery}`。

#### Scenario: 口语改写展示
- **WHEN** 问题含口语化表达（"这个咋防抄答案"）
- **THEN** rewrite 输出检索式改写（"怎么防学生套答案"），前端展示改写前后对比

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-project-intro-assistant-pipeline.md`（§Requirement: Query 改写透传）
