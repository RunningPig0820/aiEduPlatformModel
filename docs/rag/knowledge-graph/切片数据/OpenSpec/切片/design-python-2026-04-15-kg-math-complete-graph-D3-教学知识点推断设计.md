# 教学知识点推断设计

> summary: 小学3-6年级与高中知识点全空，用TextbookKPInferer推断补全，输出knowledge_points、confidence与notes，提供textbook_kg.txt提示词。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-15-kg-math-complete-graph-D3-教学知识点推断设计.md
> 类别：操作流程

---

### D3：教学知识点推断设计

> 检索摘要：小学3-6年级与高中知识点全空，用TextbookKPInferer推断补全，输出knowledge_points、confidence与notes，提供textbook_kg.txt提示词。

**问题**: 小学3-6年级、高中数据源 `knowledge_points` 为空

**解决方案**: LLM 推断补全

```python
# 调用 llm_inference.TextbookKPInferer
inferer = TextbookKPInferer(voter)

result = await inferer.infer_section(
    stage="小学",
    grade="三年级",
    semester="上册",
    chapter_name="时、分、秒",
    section_name="秒的认识",
    existing_kps=[]  # 为空则完全推断
)

# 输出
{
    "knowledge_points": ["秒的概念", "秒与分的关系", "时间的读写"],
    "confidence": 0.85,
    "notes": "依据人教版三年级上册时、分、秒单元内容"
}
```

**提示词 (textbook_kg.txt)**：

```
输入：
- 学段、年级、册次
- 章节名称、小节名称
- 已有知识点（如为空则需推断）

输出：
{
    "knowledge_points": [...],
    "confidence": 0.0-1.0,
    "notes": "推断依据"
}
```

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D3：教学知识点推断设计）
