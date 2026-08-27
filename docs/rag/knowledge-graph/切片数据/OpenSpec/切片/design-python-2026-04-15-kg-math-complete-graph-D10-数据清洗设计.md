# 数据清洗设计（清理冗余标签）

> summary: 数据清洗：DataCleaner清理"（通用）"冗余标签与Section序号前缀、末尾冒号，先检测候选重复数据再人工确认。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-15-kg-math-complete-graph-D10-数据清洗设计.md
> 类别：操作流程

---

### D10：数据清洗设计（清理冗余标签）

> 检索摘要：数据清洗：DataCleaner清理"（通用）"冗余标签与Section序号前缀、末尾冒号，先检测候选重复数据再人工确认。

**问题**: 部分章节带有"（通用）"字样，部分 Section 带有序号前缀和不规范标点

**解决方案**:

```python
# 清理规则
class DataCleaner:
    """数据清洗器"""

    # "通用"标签处理
    GENERIC_SUFFIXES = ["（通用）", "(通用)", "（综合）", "(综合)"]

    # Section 标签清洗
    SECTION_CLEANUP_PATTERNS = [
        r"^\d+\.\d+-",           # 移除前缀如 "3.1-"
        r"^\d+\.\d+\.\d+-",      # 移除前缀如 "18.1.1-"
        r":$|：$",               # 移除末尾冒号
    ]

    def clean_section_label(self, label: str) -> str:
        """清洗 Section 标签"""
        for pattern in self.SECTION_CLEANUP_PATTERNS:
            label = re.sub(pattern, "", label)
        return label.strip()

    def detect_generic_duplicate(self, chapters: List) -> List:
        """检测"通用"标签的重复数据"""
        duplicates = []
        # 检查是否有同名但带/不带"通用"的章节
        for chapter in chapters:
            if any(suffix in chapter['label'] for suffix in self.GENERIC_SUFFIXES):
                # 查找对应的非通用版本
                base_name = chapter['label'].replace("（通用）", "").replace("(通用)", "")
                duplicates.append({
                    'generic': chapter,
                    'base_name': base_name
                })
        return duplicates
```

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D10：数据清洗设计（清理冗余标签））
