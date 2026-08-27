# 知识图谱匹配流程 (MATCHES_KG)

> summary: 将TextbookKP匹配到EduKG Concept创建MATCHES_KG关系，用DualModelVoter投票，阈值≥0.9匹配、0.7-0.9候选。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-15-kg-math-complete-graph-D4-1-知识图谱匹配流程.md
> 类别：数据关联

---

### D4.1：知识图谱匹配流程 (MATCHES_KG)

> 检索摘要：将TextbookKP匹配到EduKG Concept创建MATCHES_KG关系，用DualModelVoter投票，阈值≥0.9匹配、0.7-0.9候选。

**目标**: 将 TextbookKP 匹配到 EduKG Concept

**匹配流程**:

```python
from edukg.core.llm_inference import DualModelVoter
from edukg.core.llm_inference.prompt_templates import format_kp_match_prompt

voter = DualModelVoter()

# 匹配教材知识点到知识图谱
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

**匹配阈值**：
- ≥ 0.9：MATCHES_KG
- 0.7 - 0.9：MATCHES_KG_CANDIDATE
- < 0.7：不匹配

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D4.1：知识图谱匹配流程 (MATCHES_KG)）
