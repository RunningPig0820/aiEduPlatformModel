# 权限与安全
> summary: 权限与安全
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-python-rag-project-intro-assistant-guardrails-09-权限与安全.md
> 类别：业务流程

---

### is_quoted 确定性引用（LCS 硬匹配）
> 检索摘要：怎么判定回答真的引用了召回块？精排块与 answer 做 LCS 最长公共子串，连续 8 中文字符命中即 is_quoted，纯函数可入评估。

系统 SHALL 生成完成后对精排块 text/summary 与最终 answer 做 LCS 最长公共子串匹配，任意**连续 8 中文字符（或 12 英文字符）**命中 → is_quoted=true；done 后补发 `quotedKeys`。非 LLM 自述，纯函数可单测可入评估。

#### Scenario: 命中引用
- **WHEN** answer 含精排块原文连续 ≥8 中文字符
- **THEN** quotedKeys 含该块 blockId

#### Scenario: 改写未命中
- **WHEN** answer 全部改写、无连续 8 字命中
- **THEN** quotedKeys 不含该块（前端灰显兜底）

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-project-intro-assistant-guardrails.md`（§is_quoted 确定性引用（LCS 硬匹配））
