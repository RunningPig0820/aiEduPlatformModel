# 知识点属性扩展设计

> summary: 知识点属性扩展：规则匹配推断difficulty、importance、cognitive_level、topic四属性，优先规则减少LLM调用成本，含人工审核点。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-15-kg-math-complete-graph-D11-知识点属性扩展设计.md
> 类别：数据存储

---

### D11：知识点属性扩展设计

> 检索摘要：知识点属性扩展：规则匹配推断difficulty、importance、cognitive_level、topic四属性，优先规则减少LLM调用成本，含人工审核点。

**目标**: 为 TextbookKP 增加教学属性，支持精准教学应用

**新增属性**:

| 属性 | 类型 | 说明 | 来源 |
|------|------|------|------|
| `difficulty` | int (1-5) | 难度等级 | 规则推断（年级基础）+ 关键词调整 |
| `importance` | str | 核心/重要/了解 | 规则匹配（关键词） |
| `cognitive_level` | str | 识记/理解/应用/分析 | 规则匹配（知识点类型） |
| `topic` | str | 所属专题 | 继承章节 topic（无需推断） |

**设计原则**: 优先使用规则匹配，减少 LLM 调用成本

**推断策略**:

| 属性 | 推断方法 | 示例 |
|------|----------|------|
| `topic` | 继承所属 Section/Chapter 的 topic | Section 属于"数与代数"章节 → topic="数与代数" |
| `difficulty` | 年级基础 + 关键词调整 | 六年级=3，"综合应用"关键词+1 → 4 |
| `importance` | 关键词匹配 | 含"概念"、"定义"→ 核心；含"拓展"→ 了解 |
| `cognitive_level` | 知识点类型匹配 | 概念类→识记；运算类→应用；推理类→分析 |

**规则映射表**:

```python
# 年级 → 基础难度
GRADE_BASE_DIFFICULTY = {
    "一年级": 1, "二年级": 1, "三年级": 2,
    "四年级": 2, "五年级": 3, "六年级": 3,
    "七年级": 3, "八年级": 4, "九年级": 4,
    "必修第一册": 4, "必修第二册": 4, "必修第三册": 5,
}

# 难度调整关键词
DIFFICULTY_KEYWORDS = {
    "+1": ["综合", "应用", "拓展", "探究", "复杂"],
    "-1": ["认识", "初步", "简单", "基础"],
}

# 重要性关键词
IMPORTANCE_KEYWORDS = {
    "核心": ["概念", "定义", "定理", "公式", "法则", "性质", "原理"],
    "重要": ["运算", "计算", "方法", "技巧", "应用"],
    "了解": ["拓展", "阅读", "活动", "兴趣", "课外"],
}

# 认知层次映射（知识点类型 → 认知层次）
COGNITIVE_LEVEL_MAP = {
    "概念类": "识记",    # 定义、概念、术语
    "理解类": "理解",    # 性质、关系、规律
    "运算类": "应用",    # 计算、运算、求解
    "推理类": "分析",    # 证明、推导、推理
}
```

**推断流程**:

```python
class KPAttributeInferer:
    """知识点属性推断器（规则匹配）"""

    def infer_attributes(self, kp_name: str, grade: str, section_topic: str) -> dict:
        # 1. topic：直接继承章节
        topic = section_topic

        # 2. difficulty：年级基础 + 关键词调整
        base = GRADE_BASE_DIFFICULTY.get(grade, 3)
        for keyword, adjust in DIFFICULTY_KEYWORDS.items():
            if keyword in kp_name:
                base += adjust
        difficulty = max(1, min(5, base))

        # 3. importance：关键词匹配
        importance = "重要"  # 默认
        for level, keywords in IMPORTANCE_KEYWORDS.items():
            if any(kw in kp_name for kw in keywords):
                importance = level
                break

        # 4. cognitive_level：知识点类型推断
        cognitive_level = "理解"  # 默认
        if any(kw in kp_name for kw in ["概念", "定义", "认识"]):
            cognitive_level = "识记"
        elif any(kw in kp_name for kw in ["计算", "运算", "求解", "应用"]):
            cognitive_level = "应用"
        elif any(kw in kp_name for kw in ["证明", "推导", "推理"]):
            cognitive_level = "分析"

        return {
            "difficulty": difficulty,
            "importance": importance,
            "cognitive_level": cognitive_level,
            "topic": topic,
        }
```

**人工审核点**:

在代码执行前，需要人工审核以下内容：
1. 规则映射表是否覆盖主要知识点类型
2. 难度调整关键词是否合理
3. 重要性关键词是否完整
4. 认知层次映射是否符合教学实际

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D11：知识点属性扩展设计）
