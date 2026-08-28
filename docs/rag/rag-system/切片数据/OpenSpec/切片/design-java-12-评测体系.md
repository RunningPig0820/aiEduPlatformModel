# 评测体系

> summary: 评测体系（design-java-rag-project-intro-assistant）：复用run_eval链、新增边界拒答类型+precision_at_k+is_quoted校验、评估集5类场景ValueError校验、baseline报告白盒展示
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-java-12-评测体系.md
> 类别：数据关联

---

### D10. 评估复用 run_eval 链 + 三处扩展

> 检索摘要：评估复用run_eval链：新增边界拒答类型+precision_at_k+is_quoted校验，baseline报告白盒展示hit@k质量分成本

- `eval_dataset.py` `VALID_TYPES` 增加 `边界拒答`;`expected` 断言 = "必须触发固定话术且不产生 token 流"。
- `eval_agent.py` 新增 `precision_at_k`(召回 top-k 中相关块占比,纯函数);`judge_quality` prompt 升级原子声明模式(RAGAS Faithfulness 思想)可选。
- 新增 is_quoted 纯函数 `lcs_quote_match` 单测 + 入评估(`quoted_keys ⊆ 召回块`)。
- baseline 报告经 `GET /api/rag/assistant/eval/report` 白盒展示(hit@k/质量分/成本/耗时)。
- **为什么**:"证明有效"不能靠感觉(用户明确要求可量化/可复现/可追溯);现有链完整可复用,只需扩展。
- **备选**:重新造评估轮 → 重复建设。

### Requirement: 评估集扩面（5 类场景 + 格式校验）

> 检索摘要：RAG助手评估集覆盖5类（项目介绍/操作流程/数据关联/难点技术/边界拒答）每类≥1条每模块≥5条，缺字段/非法类型加载抛ValueError不静默

目标 D10 已定义 `VALID_TYPES` 增加 `边界拒答`、每模块 ≥5 条。本块独有:系统 SHALL 扩充 RAG 助手评估集覆盖 **5 类场景**:项目介绍类、操作流程类、数据关联类、难点技术类、**边界拒答类**(每类 ≥1 条、每模块 ≥5 条);评估集含缺字段/非法类型用例 → **加载器抛 ValueError**(沿用 `eval_dataset.py` 格式校验,不静默)。

### Requirement: precision_at_k 指标（相关判定细节）

> 检索摘要：precision_at_k相关判定沿用expected_references的节号匹配（非语义判断），计算相关块占比0~1纳入聚合指标展示

目标 D10 已定义 `precision_at_k`(召回 top-k 中相关块占比,纯函数)。本块独有:相关判定**沿用 expected_references 的节号匹配**(非语义判断),计算相关块占比 0~1,纳入聚合指标展示。

### Requirement: baseline 报告可复现与对比（落盘路径）

> 检索摘要：每次语料/参数/提示词变更后重跑--compare生成对比报告（hit@k/质量分/成本/耗时↑↓=），trace落jsonl聚合报告落reports/<version>.json结构与run_eval.py一致

目标 Context 已提 `run_eval.py --compare` 版本对比。本块独有:系统 SHALL 复用 `run_eval.py` 的可复现执行与版本对比能力(`--compare`),**每次语料/参数/提示词变更后重跑评测生成对比报告**(对比 hit@k/质量分/成本/耗时 ↑/↓/=);**trace 落盘 jsonl、聚合报告落盘 `reports/<version>.json`**,结构与既有 `run_eval.py` 一致。

### Requirement: 评估报告白盒展示（字段全集与无报告语义）

> 检索摘要：报告接口返回最新baseline（hit@3/质量分/avg耗时/avg成本/条数/版本/judged），尚未跑评测返回明确的"暂无评估报告"提示不报错

目标 D10 已定义 `GET /api/rag/assistant/eval/report` 白盒展示。本块独有:接口返回最新报告**含 judged 字段**(hit@3、质量分、avg 耗时、avg 成本、**条数、版本、judged**);WHEN 尚未跑过评测 → THEN 返回明确的"暂无评估报告"提示,**不报错**。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-java-rag-project-intro-assistant.md`（§D10/§补充 eval-评估集扩面/§补充 eval-precision_at_k/§补充 eval-baseline报告落盘/§补充 eval-评估报告白盒展示）
