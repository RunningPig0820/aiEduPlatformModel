# 答案生成与引用判定
> summary: 答案生成与引用判定
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-python-rag-project-intro-assistant-pipeline-07-答案生成与引用判定.md
> 类别：操作流程

---

## 文档说明
> 本文件由 OpenSpec 设计素材（spec-python-rag-project-intro-assistant-pipeline.md）按业务主题「答案生成与引用判定」重切合并。
> ⚠️设计阶段素材：真实实现以权威度 0.8 的 canonical 真相源 + 代码为准（代码已部分落地）；含 ✅已落地 / ⚠️构想未实现 / ❓待决策 内容，引用需核对代码。

### Requirement: doubao 流式生成
> 检索摘要：生成阶段怎么流式输出——doubao 基于精排块与改写 query、只基于检索上下文不编造？

系统 SHALL 基于精排 Top-K 块与改写 query 调 doubao 流式生成（温度 0.2，`include_usage` 取 usage），按 token 事件流式输出；只基于检索上下文，语料未覆盖不编造。

#### Scenario: 流式输出
- **WHEN** 精排完成进入生成
- **THEN** token 事件逐增量输出，done 前不含截断

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-project-intro-assistant-pipeline.md`（§Requirement: doubao 流式生成）
