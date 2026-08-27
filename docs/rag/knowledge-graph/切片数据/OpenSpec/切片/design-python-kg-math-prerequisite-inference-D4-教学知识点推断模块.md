# D4：教学知识点推断模块 (textbook_kp_inferer.py)
> summary: 教学知识点推断模块：TextbookKPInferer用双模型投票推断小学3-6年级与高中缺失的knowledge_points，支持infer_batch断点续传。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-kg-math-prerequisite-inference-D4-教学知识点推断模块.md
> 类别：数据关联

> 检索摘要：教学知识点推断模块：TextbookKPInferer用双模型投票推断小学3-6年级与高中缺失的knowledge_points，支持infer_batch断点续传。

**背景**: 教材数据中小学3-6年级、高中知识点的 `knowledge_points` 字段为空，需要 LLM 推断补全。

```python
class TextbookKPInferer:
    """教学知识点推断器"""

    def __init__(self, voter: DualModelVoter):
        self.voter = voter

    async def infer_section(
        self,
        stage: str,          # 学段
        grade: str,          # 年级
        semester: str,       # 册次
        chapter_name: str,   # 章节名称
        section_name: str,   # 小节名称
        existing_kps: List[str] = None  # 已有知识点
    ) -> Dict:
        """
        推断单个小节的教学知识点

        Returns:
            {
                'knowledge_points': [...],
                'confidence': 0.0-1.0,
                'notes': '推断依据'
            }
        """

    async def infer_batch(
        self,
        sections: List[Dict],
        resume: bool = True  # 断点续传
    ) -> List[Dict]:
        """批量推断"""
```

**提示词 (textbook_kg.txt)**：

```
输入：
- 学段、年级、册次
- 章节名称、小节名称
- 已有知识点（如为空则需推断）

输出：
{
    "knowledge_points": ["知识点1", "知识点2", ...],
    "confidence": 0.85,
    "notes": "依据人教版七年级上册1.1节标准教学内容"
}
```

> 证据：详见 `2.OpenSpec design 决策/design-python-kg-math-prerequisite-inference.md`（§D4：教学知识点推断模块 (textbook_kp_inferer.py)）
