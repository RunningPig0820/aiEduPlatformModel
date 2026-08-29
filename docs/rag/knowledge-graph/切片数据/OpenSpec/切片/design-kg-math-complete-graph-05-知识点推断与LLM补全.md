# 知识点推断与 LLM 补全

> summary: 知识点推断与 LLM 补全
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-math-complete-graph-05-知识点推断与LLM补全.md
> 类别：数据关联

---

> 检索摘要：小学3-6年级和高中知识点为空怎么补？TextbookKPInferer 怎么推断？知识点属性（难度/重要性/认知维度/专题）怎么扩展？

## 教学知识点推断（D3）

问题：小学 3-6 年级、高中数据源 knowledge_points 为空。

解决方案：LLM 推断补全，调用 llm_inference.TextbookKPInferer：

```python
inferer = TextbookKPInferer(voter)
result = await inferer.infer_section(
    stage="小学", grade="三年级", semester="上册",
    chapter_name="时、分、秒", section_name="秒的认识",
    existing_kps=[]  # 为空则完全推断
)
# 输出
{
    "knowledge_points": ["秒的概念", "秒与分的关系", "时间的读写"],
    "confidence": 0.85,
    "notes": "依据人教版三年级上册时、分、秒单元内容"
}
```

提示词（textbook_kg.txt）：输入学段、年级、册次、章节名称、小节名称、已有知识点（为空则需推断）；输出 knowledge_points 列表、confidence（0.0-1.0）、notes 推断依据。

风险缓解（R2）：LLM 推断的知识点可能不准确，使用教研员角色提示词 + 保留置信度 + 人工验证。

## 知识点属性扩展（D11）

目标：为 TextbookKP 增加教学属性，支持精准教学应用。设计原则：优先使用规则匹配，减少 LLM 调用成本。

新增属性：
- difficulty：int (1-5)，难度等级，规则推断（年级基础）+ 关键词调整
- importance：核心/重要/了解，规则匹配（关键词）
- cognitive_level：识记/理解/应用/分析，规则匹配（知识点类型）
- topic：所属专题，继承章节 topic（无需推断）

推断策略：
- topic：直接继承所属 Section/Chapter 的 topic
- difficulty：年级基础 + 关键词调整（如六年级=3，"综合应用"关键词+1 → 4）
- importance：关键词匹配（含"概念""定义"→核心；含"拓展"→了解）
- cognitive_level：知识点类型匹配（概念类→识记；运算类→应用；推理类→分析）

规则映射表（KPAttributeInferer）：
- GRADE_BASE_DIFFICULTY：一年级=1、二年级=1、三年级=2、四年级=2、五年级=3、六年级=3、七年级=3、八年级=4、九年级=4、必修第一册=4、必修第二册=4、必修第三册=5
- DIFFICULTY_KEYWORDS：+1 关键词 ["综合","应用","拓展","探究","复杂"]；-1 关键词 ["认识","初步","简单","基础"]
- IMPORTANCE_KEYWORDS：核心=["概念","定义","定理","公式","法则","性质","原理"]；重要=["运算","计算","方法","技巧","应用"]；了解=["拓展","阅读","活动","兴趣","课外"]
- COGNITIVE_LEVEL_MAP：概念类→识记；理解类→理解；运算类→应用；推理类→分析

推断流程：difficulty 取年级基础值按关键词加减并夹取到 1-5；importance 默认"重要"，命中关键词则取对应等级；cognitive_level 默认"理解"，含概念/定义/认识→识记，计算/运算/求解/应用→应用，证明/推导/推理→分析；topic 直接继承章节。

人工审核点：规则映射表是否覆盖主要知识点类型、难度调整关键词是否合理、重要性关键词是否完整、认知层次映射是否符合教学实际。

风险缓解（R6）：不同章节推断的 difficulty/importance 可能不一致，使用统一标准 + 建立属性校验规则。

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D3 / §D11 / §R2 / §R6）
