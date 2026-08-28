# milestone-05-self-check Specification

## Purpose

M5 交付"自我检查"切片——is_quoted 引用硬校验（原清单 #7）+ 评估扩展。is_quoted 用 LCS 硬匹配（8 中/12 英），`done` 后补发 `quoted_keys`，非 LLM 自述；评估链扩展边界拒答类型、precision_at_k、is_quoted 入评估，baseline 报告白盒展示。前端以引用高亮/灰显折叠 + 评估报告一屏验收。

## ADDED Requirements

### Requirement: is_quoted 确定性硬匹配

M5 SHALL 交付引用自我检查：生成完成后对精排块 text/summary 与最终 answer 做 LCS 最长公共子串匹配，任意连续 8 中文字符（或 12 英文字符）命中 → 该块 quoted=true；`done` 后补发 `quoted_keys`。全未命中 → answer 标注"引用未能精确匹配"。窗口大小可调（`config/settings.py`）。

#### Scenario: 命中引用

- **WHEN** answer 含某块连续 8 中文字符（或 12 英文字符）
- **THEN** 该块进入 quotedKeys，前端高亮

#### Scenario: 未命中标注

- **WHEN** 所有块均未命中
- **THEN** quotedKeys 为空，answer 标注"引用未能精确匹配"

#### Scenario: 英文边界

- **WHEN** 命中连续 12 英文字符
- **THEN** quoted=true；11 字符命中 = false（边界正确）

### Requirement: 引用校验入评估（改写答案场景）

M5 SHALL 将 is_quoted 实现为纯函数（可单测）并纳入评估：断言 `quoted_keys ⊆ 召回块集合`（引用不得指向未召回内容）；评估集 SHALL 含"改写答案"用例（LLM 改写用词后引用是否仍命中，如"类型先行流式"→"type先行"），验证 8 字符窗口漏判率。

#### Scenario: 引用属于召回块

- **WHEN** 某轮评估生成完成
- **THEN** 断言 quoted_keys 全部 ∈ 该轮召回块，越界即失败

#### Scenario: 改写答案引用命中

- **WHEN** 评估集含 LLM 改写用词后的答案
- **THEN** 评估记录该块引用命中与否，用于 8 字符窗口漏判率评估（漏判 → 调窗口）

### Requirement: 评估扩展与报告白盒展示

M5 SHALL 交付评估切片：`eval_dataset.py` VALID_TYPES 增加 `边界拒答`；`eval_agent.py` 新增 `precision_at_k` 纯函数；重跑 baseline 报告（hit@3/质量分/成本/耗时/版本）；提供 `GET /api/rag/assistant/eval/report` 供前端展示"证明有效"一屏。

#### Scenario: 边界拒答评估

- **WHEN** 评估集用例类型=边界拒答
- **THEN** 断言命中固定低置信话术 + 无生成 token，判定通过

#### Scenario: 报告白盒展示

- **WHEN** 前端请求评估报告
- **THEN** 返回最新 baseline（hit@3/质量分/avg 耗时/avg 成本/条数/版本）；未跑过 → "暂无评估报告"

### Requirement: 里程碑对接测试验收

M5 SHALL 以引用高亮 + 评估展示用例作为完成标准：RAG-QUOTE-001~005（命中/未命中/英文边界/全未命中/改写命中）、RAG-CONTRACT-001（done 含 quotedKeys）、评估扩展用例（边界拒答/precision_at_k/is_quoted 校验）。

#### Scenario: 对接测试全绿

- **WHEN** 前端完成引用高亮/灰显折叠与评估报告一屏对接
- **THEN** RAG-QUOTE-001~005、RAG-CONTRACT-001、评估扩展用例通过，M5 视为完成

#### Scenario: 前端可见物

- **WHEN** 一轮生成完成
- **THEN** 引用块高亮、未引用块灰显折叠；评估入口展示最新 baseline 报告
