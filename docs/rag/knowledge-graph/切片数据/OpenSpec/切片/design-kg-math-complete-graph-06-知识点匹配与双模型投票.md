# 知识点匹配与双模型投票

> summary: 知识点匹配与双模型投票
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-math-complete-graph-06-知识点匹配与双模型投票.md
> 类别：架构设计

---

> 检索摘要：教材知识点怎么匹配到 EduKG Concept？双模型投票怎么工作？粗筛 top-20 怎么避免 LLM 调用爆炸？精确匹配怎么增强？

## 匹配流程（D4.1）

目标：将 TextbookKP 匹配到 EduKG Concept，创建 MATCHES_KG 关系。使用 DualModelVoter 双模型投票：

```python
voter = DualModelVoter()
prompt = format_kp_match_prompt(
    textbook_kp_name="正数和负数的概念",
    textbook_kp_description="大于0的数叫正数，小于0的数叫负数",
    kg_kp_name="正数",
    kg_kp_description="数学概念..."
)
result = await voter.vote(prompt)
if result['consensus'] and result['result']['is_match']:
    # 创建 MATCHES_KG 关系
```

匹配阈值：≥0.9 建 MATCHES_KG；0.7-0.9 建 MATCHES_KG_CANDIDATE 候选关系；<0.7 不匹配。

## 粗筛机制设计（D4.2）

问题：原方案遍历所有图谱知识点（5000+），LLM 调用量爆炸。

解决方案：两阶段匹配。教材知识点 → 粗筛（top-20 候选）→ LLM 双模型投票 → 匹配结果。

粗筛方式对比：
- difflib（原方案）：字符相似度匹配，无依赖、速度快，但语义理解弱
- 向量检索（新方案）：Embedding 语义匹配，自动理解同义词、语义强，需安装依赖

## 精确匹配增强（D4.4）

标准化处理 _normalize_name：转小写、去空格（半角/全角）、统一括号（全角（）→半角()）。

同义词映射 SYNONYM_MAP（完整词匹配，防止过度匹配）：
- "加法": ["加", "加法运算", "相加", "求和"]
- "百分数": ["百分比", "百分率"]

## 异常处理和输出完整性（D4.5）

- LLM 调用失败时 continue，不中断整个知识点
- 输出所有教材知识点（含未匹配），增加 matched 字段

## 风险缓解（R1）

风险：LLM 匹配可能不准确导致知识点匹配率低。缓解：双模型投票 + 置信度阈值 + 候选关系保留（MATCHES_KG_CANDIDATE）。

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D4.1 / §D4.2 / §D4.4 / §D4.5 / §R1）
