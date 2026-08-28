# 引导问题体系
> summary: 引导问题体系
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-python-rag-project-intro-assistant-guardrails-11-引导问题体系.md
> 类别：操作流程

---

### clarify 澄清轮
> 检索摘要：问题模糊时怎么澄清？intent ambiguous 且候选≥2 触发 clarify 事件，固定话术加候选与默认项，不召回不生成只澄清一次。

系统 SHALL 在 intent `ambiguous=true` 且 candidates ≥2 时发 `clarify` 事件（固定话术 + candidates + default），不 recall/generate、0 token、不计答案轮次、写 history；下一条重跑 intent；仍模糊不再二次澄清，直接默认当前功能。

候选判定（C4 定稿）：主源 = intent LLM `candidates`（2~4 个模块闭集）；LLM 未给/给<2 → 会话最近 N 轮锚过模块去重兜底；仍 <2 → 不触发 clarify。default = current_project > 会话最后锚定。

#### Scenario: 多候选澄清
- **WHEN** 问"这个功能的流转"且会话内多功能候选
- **THEN** `clarify`（"您的问题涉及多个功能，请明确功能名。默认回答当前功能：RAG项目" + candidates + default）

#### Scenario: 澄清一次后仍模糊
- **WHEN** 学生答"就那个嘛"仍无明确功能名
- **THEN** 不二次澄清，直接按 default 进入链路

#### Scenario: 点选候选重发（权威锚定）
- **WHEN** 学生点选候选 chip（如 [RAG项目]），前端**重发原问题 + `current_project=rag-system`**（含 clarify 轮 history）
- **THEN** intent 以 `current_project` 为**权威消歧锚点**直接锚定 `anchor=rag-system`，**不因问题本身含糊再拉 ambiguous**
- **AND** 点选模块与会话锚点不同 → `switch` 事件照常触发

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-project-intro-assistant-guardrails.md`（§clarify 澄清轮）

### switch 上下文切换（重置上下文）
> 检索摘要：学生切换功能时上下文怎么处理？intent switch_detected 触发 switch 事件携带新旧锚点，重置锚点/召回/轮次后按新锚点走链路。

系统 SHALL 在 intent 判定 `switch_detected=true` 时发出 `switch` 事件（`{from_anchor, to_anchor}`）并**重置上下文**（锚点/召回/轮次计数），随后按新锚点走 rewrite→recall→generate；不掐断任何在途流（在途流完成或被 is_disconnected 取消）。

#### Scenario: 切换功能
- **WHEN** 学生从 AI答疑 切到 RAG 项目提问（switch_detected=true）
- **THEN** 发 `switch` 事件 + 重置上下文 → 走新锚点链路

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-project-intro-assistant-guardrails.md`（§switch 上下文切换（重置上下文））
