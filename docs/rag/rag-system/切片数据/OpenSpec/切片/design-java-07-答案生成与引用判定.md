# 答案生成与引用判定

> summary: 答案生成与引用判定（design-java-rag-project-intro-assistant）：doubao流式生成（温度0.2/include_usage/只基于检索上下文）、is_quoted LCS硬匹配（8中/12英）done后补发、全部未命中兜底标注
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-java-07-答案生成与引用判定.md
> 类别：操作流程

---

### D6. is_quoted 用 LCS 硬匹配,`done` 后补发,非 LLM 自述

> 检索摘要：is_quoted用LCS最长公共子串硬匹配非LLM自述：8中/12英字符命中即引用，done后补发quoted_keys前端先灰后亮，窗口可调、评估集加改写用例

生成完成后,遍历每个精排块的 `text`/`summary`,与最终 answer 做最长公共子串匹配,任意**连续 8 中文字符(或 12 英文字符)**命中 → `is_quoted=true`。前端 `rerank` 先发块(灰显),`done` 补 `quoted_keys`(高亮)。
- **为什么**:引用判定不依赖 LLM 主观自述(spec 硬性要求确定性),纯函数可单测可入评估。8 中文字符窗口对单 token chunk 不友好 → 生成完才匹配,故 `done` 后置补发。
- **风险(Python 侧校准)**:doubao 生成可能改写用词(如"类型先行流式"→"type先行"),导致 8 字符窗口**漏判**。→ 窗口大小可调(`config/settings.py`);评估集加"改写答案"用例验证窗口够不够;漏判时块灰显但答案仍完整(非致命,前端无需报错)。
- **备选**:LLM 自报引用 → 不可靠;流中实时匹配 → chunk 粒度导致匹配窗口撕裂。

### Requirement: doubao 流式生成（模型参数与生成纪律）

> 检索摘要：doubao强模型温度0.2 include_usage取usage按token事件流式输出，生成只基于检索上下文语料未覆盖不编造

目标 D7/D8 已覆盖生成层超时与 usage 取流(include_usage)。本块独有:系统 SHALL 基于精排 Top-K 块与改写后 query 调用 doubao 流式生成答案(**强模型、温度 0.2、`include_usage` 取 usage**),按 token 事件流式输出;**生成只基于检索上下文,语料未覆盖不编造**。

### Requirement: is_quoted 确定性硬匹配（全部未命中兜底）

> 检索摘要：top-K块全部未命中时answer标注"基于现有知识库,引用未能精确匹配"，quotedKeys为空不假装存在引用

目标 D6 已定义 LCS 硬匹配、8 中/12 英窗口与 done 后补发 quoted_keys。本块独有:**全部未命中场景**——WHEN top-K 块全部未命中 → THEN answer 标注"基于现有知识库,引用未能精确匹配",`quotedKeys` 为空,**不假装存在引用**。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-java-rag-project-intro-assistant.md`（§D6/§补充 pipeline-doubao流式生成/§补充 guardrails-is_quoted全部未命中兜底）
