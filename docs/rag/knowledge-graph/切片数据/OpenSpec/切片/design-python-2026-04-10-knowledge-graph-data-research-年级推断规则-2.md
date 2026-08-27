# 年级推断规则（续）
> summary: 年级推断核心是教材→年级映射表 TEXTBOOK_TO_GRADE（必修/选择性必修/七八九年级），学段反向推断作 fallback。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-年级推断规则-2.md
> 类别：数据关联

---

### 四、年级推断规则（教材→年级映射）（续）

> 检索摘要：年级推断核心是教材→年级映射表 TEXTBOOK_TO_GRADE（必修/选择性必修/七八九年级），学段反向推断作 fallback。

### 4.2 章节 → 学期推断
> 检索摘要：章节→学期推断基于 main.ttl 的 mark 字段（如 6.2.1 第6章第2节第1小节），通常上学期1-4章下学期5-8章，缺失时按教材序号。

# 从 main.ttl 的 mark 字段推断
# mark: "6.2.1" 表示 第6章 第2节 第1小节
# 通常上学期学1-4章，下学期学5-8章

### 4.2.1 mark 字段解析兼容（新增）
> 检索摘要：mark 字段格式不统一（6.2.1/6-2-1/第六章第二节/Chapter 6.2.1），parse_mark_field 兼容解析返回(章节,小节,序号)，无法解析 fallback。

问题：mark 字段格式可能不统一（如 "6.2.1"、"6-2-1"、"第六章第二节"）。
import re

def parse_mark_field(mark: str) -> tuple:
"""
解析 mark 字段，返回 (章节, 小节, 小节序号)
支持多种格式：6.2.1, 6-2-1, 第六章第二节, Chapter 6.2.1
"""
if not mark:
return (None, None, None)

    # 格式1: 6.2.1 或 6-2-1
    match = re.match(r'(\d+)[.\-](\d+)(?:[.\-](\d+))?', mark)
    if match:
        chapter = int(match.group(1))
        section = int(match.group(2))
        subsection = int(match.group(3)) if match.group(3) else 0
        return (chapter, section, subsection)

    # 格式2: 第六章第二节
    chinese_nums = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
                    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
    match = re.match(r'第([一二三四五六七八九十]+)章(?:第([一二三四五六七八九十]+)节)?', mark)
    if match:
        chapter = chinese_nums.get(match.group(1), 0)
        section = chinese_nums.get(match.group(2), 0) if match.group(2) else 0
        return (chapter, section, 0)

    # 格式3: Chapter 6.2.1
    match = re.match(r'Chapter\s*(\d+)(?:\.(\d+))?(?:\.(\d+))?', mark, re.IGNORECASE)
    if match:
        chapter = int(match.group(1))
        section = int(match.group(2)) if match.group(2) else 0
        subsection = int(match.group(3)) if match.group(3) else 0
        return (chapter, section, subsection)

    # 无法解析，返回 (0, 0, 0) 作为 fallback
    return (0, 0, 0)

Fallback 策略：若章节信息完全缺失，按教材序号作为顺序（第1章、第2章）。

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§四、年级推断规则（教材→年级映射）（续））
