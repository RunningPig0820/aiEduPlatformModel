# 单元/专题层级设计

> summary: 教材缺少中间"单元"概念，对比新增Unit节点/Chapter加topic/Section加unit_id三方案，建议方案B（Chapter.topic字段）。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-15-kg-math-complete-graph-D12-单元专题层级设计.md
> 类别：数据存储

---

### D12：单元/专题层级设计

> 检索摘要：教材缺少中间"单元"概念，对比新增Unit节点/Chapter加topic/Section加unit_id三方案，建议方案B（Chapter.topic字段）。

**背景**: 教材的"章"过大、"节"过细，缺少中间的"单元"概念

**设计方案**:

```
当前层级：教材 → 章 → 节 → 知识点
新增层级：教材 → 章 → 单元(Unit) → 节 → 知识点
```

**实现方式**:

| 方案 | 说明 | 优点 | 缺点 |
|------|------|------|------|
| **A: 新增 Unit 节点** | 创建 Unit 节点类型，建立 CONTAINS 关系 | 结构清晰，支持跨年级专题 | 需要修改现有数据模型 |
| **B: Chapter 增加 topic 字段** | 为 Chapter 增加 topic 属性，标注所属专题 | 改动小，不影响现有关系 | 无法细化到节级别 |
| **C: Section 增加 unit_id 字段** | 为 Section 增加所属单元标识 | 简单，不改变节点结构 | 需要人工或 LLM 划分 |

**建议**: 采用方案 B（Chapter 增加 topic 字段），后续迭代可扩展为方案 A

```python
# 方案 B 实现
class ChapterEnhancer:
    """章节专题增强"""

    # 人教版数学专题分类
    MATH_TOPICS = {
        "数与代数": ["有理数", "整式的加减", "一元一次方程", ...],
        "图形与几何": ["几何图形初步", "相交线与平行线", "三角形", ...],
        "统计与概率": ["数据的收集与整理", "概率初步", ...],
        "综合与实践": ["数学活动", "课题学习", ...]
    }

    def assign_topic(self, chapter_name: str) -> str:
        """为章节分配专题"""
        for topic, keywords in self.MATH_TOPICS.items():
            for keyword in keywords:
                if keyword in chapter_name:
                    return topic
        return "其他"
```

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D12：单元/专题层级设计）
