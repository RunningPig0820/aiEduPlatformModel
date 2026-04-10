## Context

### 项目背景

知识图谱数据处理项目已完成数学学科的核心数据导入：
- **kg-neo4j-schema**：Neo4j schema 初始化（节点标签、唯一性约束）
- **kg-math-knowledge-points**：EduKG 数据导入（Class 39, Concept 1,295, Statement 2,932）
- **kg-math-native-relations**：关系导入（RELATED_TO 10,183, SUB_CLASS_OF 38, PART_OF 298, BELONGS_TO 619）

### 当前问题

**教材数据与知识点数据割裂**：

```
教材数据 (本地 JSON)              知识点数据 (Neo4j EduKG)
┌─────────────────────┐          ┌─────────────────────┐
│ 学段: 初中          │          │ uri: instance#1047  │
│ 年级: 七年级        │    ??    │ label: 余弦定理     │
│ 教材: 上册          │ ───────▶ │ type: 数学定理      │
│ 章节: 有理数        │          │ source: EduKG       │
│ 知识点: 正数和负数  │          │ relatedTo: 三角形   │
└─────────────────────┘          └─────────────────────┘
```

**名称不一致问题**：
- 教材：`正数和负数的概念` vs EduKG：`正数的定义`
- 精确匹配率仅 6% (24/346)

### 设计约束

1. **输出 JSON 文件**：不直接导入 Neo4j，由人工验证后手动导入
2. **两部分分离**：数据生成 + 推理
3. **核心代码放入 `edukg/core/textbook/`**，scripts 只做命令行入口
4. **复用双模型推理**：依赖 `edukg/core/llm_inference/` 模块

## Goals / Non-Goals

**Goals:**
1. 解析教材 JSON 数据，输出标准格式 JSON
2. 生成教材-章节-小节-知识点层级结构数据
3. 使用双模型推理匹配教材知识点到 EduKG Concept
4. 输出所有关系数据（CONTAINS, IN_UNIT, MATCHES_KG）

**Non-Goals:**
1. 不直接导入 Neo4j（人工验证后手动导入）
2. 不处理其他学科（仅数学）
3. 不实现新的 LLM 推理机制（复用 `llm_inference` 模块）
4. 不修改已有的 EduKG 节点数据

## Decisions

### D1: 目录结构设计

**核心代码放入 `edukg/core/textbook/`**：

```
edukg/core/textbook/
├── __init__.py
├── data_generator.py         # 教材数据生成器
├── uri_generator.py          # URI 生成逻辑
├── kp_matcher.py             # 知识点匹配器（调用 llm_inference）
├── filters.py                # 知识点过滤规则
└── config.py                 # 配置
```

**scripts 只做命令行入口**：

```
edukg/scripts/kg_data/
├── generate_textbook_data.py # 数据生成命令行入口
└── match_textbook_kp.py      # 知识点匹配命令行入口
```

**理由**:
- 核心逻辑可复用（API 也可调用）
- scripts 保持轻量，只做参数解析和调用
- 便于单元测试

### D2: 数据生成模块 (data_generator.py)

```python
"""
教材数据生成器
从原始 JSON 文件提取节点和关系数据
"""

class TextbookDataGenerator:
    """教材数据生成器"""

    def __init__(self, data_dir: str, output_dir: str):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.uri_generator = URIGenerator()

    def discover_files(self) -> List[str]:
        """发现教材 JSON 文件"""

    def generate_all(self) -> Dict[str, str]:
        """
        生成所有数据文件

        Returns:
            {'textbooks': 'path/to/textbooks.json', ...}
        """

    def generate_textbooks(self) -> List[Dict]:
        """生成教材节点数据"""

    def generate_chapters(self) -> List[Dict]:
        """生成章节节点数据"""

    def generate_sections(self) -> List[Dict]:
        """生成小节节点数据"""

    def generate_textbook_kps(self) -> List[Dict]:
        """生成教材知识点节点数据（含过滤）"""

    def generate_relations(self) -> Dict[str, List[Dict]]:
        """生成关系数据"""
```

### D3: URI 生成模块 (uri_generator.py)

```python
"""
URI 生成逻辑
版本: v3.1
"""

class URIGenerator:
    """URI 生成器"""

    URI_PREFIX = "http://edukg.org/knowledge/3.1"

    GRADE_ENCODING = {
        "一年级": "g1", "二年级": "g2", "三年级": "g3",
        "四年级": "g4", "五年级": "g5", "六年级": "g6",
        "七年级": "g7", "八年级": "g8", "九年级": "g9",
        "必修第一册": "bixiu1", "必修第二册": "bixiu2", "必修第三册": "bixiu3",
    }

    SEMESTER_ENCODING = {"上册": "s", "下册": "x"}

    def textbook_id(self, publisher: str, grade: str, semester: str) -> str:
        """生成教材 ID: renjiao-g1s"""

    def chapter_id(self, textbook_id: str, order: int) -> str:
        """生成章节 ID: renjiao-g1s-1"""

    def section_id(self, chapter_id: str, order: int) -> str:
        """生成小节 ID: renjiao-g1s-1-1"""

    def textbookkp_uri(self, stage: str, seq: int) -> str:
        """生成知识点 URI: textbook-primary-00001"""
```

### D4: 知识点匹配模块 (kp_matcher.py)

```python
"""
知识点匹配器
复用 edukg/core/llm_inference/dual_model_voter.py
"""

from edukg.core.llm_inference import DualModelVoter

class KPMatcher:
    """知识点匹配器"""

    def __init__(self, voter: DualModelVoter = None):
        self.voter = voter or DualModelVoter()

    def exact_match(self, textbook_kp: str, kg_concepts: List[str]) -> Optional[str]:
        """精确匹配"""

    async def llm_match(self, textbook_kp: Dict, kg_concepts: List[Dict]) -> List[Dict]:
        """
        LLM 语义匹配

        Returns:
            [{'kg_uri': ..., 'confidence': 0.9, 'method': 'llm_vote'}, ...]
        """

    async def match_all(self, textbook_kps: List[Dict],
                        kg_concepts: List[Dict]) -> List[Dict]:
        """批量匹配所有知识点"""
```

### D5: 过滤规则 (filters.py)

```python
"""
知识点过滤规则
"""

NON_KNOWLEDGE_POINT_MARKERS = {
    "数学活动", "小结", "整理和复习", "本章综合与测试",
    "本节综合与测试", "复习题", "★数学乐园", "☆摆一摆，想一想",
    "构建知识体系", "习题训练", "章前引言", "测试",
    "部分中英文词汇索引", "构建知识体系和应用",
}

def is_valid_knowledge_point(name: str) -> bool:
    """判断是否为有效知识点"""
    if not name or not name.strip():
        return False
    name = name.strip()
    if name in NON_KNOWLEDGE_POINT_MARKERS:
        return False
    if name.startswith("复习题"):
        return False
    return True
```

### D6: 数据模型设计

**节点设计**：

| 节点类型 | 约束 | 属性 |
|---------|------|------|
| Textbook | `uri UNIQUE`, `id UNIQUE` | uri, id, label, stage, grade, semester, publisher, edition |
| Chapter | `uri UNIQUE`, `id UNIQUE` | uri, id, label, order |
| Section | `uri UNIQUE`, `id UNIQUE` | uri, id, label, order, mark |
| TextbookKP | `uri UNIQUE` | uri, label, stage, grade |

**关系设计（4 种）**：

| 关系类型 | 起点 → 终点 | 语义 |
|---------|------------|------|
| **CONTAINS** | Textbook → Chapter → Section | 目录层级 |
| **IN_UNIT** | TextbookKP → Section | 知识点所属单元 |
| **PREREQUISITE** | TextbookKP → TextbookKP/Concept | 先修关系 |
| **MATCHES_KG** | TextbookKP → Concept | 匹配图谱 |

### D7: 输出文件结构

```
edukg/data/edukg/math/5_教材目录/output/
├── textbooks.json           # 教材节点
├── chapters.json            # 章节节点
├── sections.json            # 小节节点
├── textbook_kps.json        # 教材知识点节点
├── contains_relations.json  # CONTAINS 关系
├── in_unit_relations.json   # IN_UNIT 关系
├── matches_kg_relations.json # MATCHES_KG 关系（推理结果）
└── import_summary.json      # 导入统计摘要
```

## Risks / Trade-offs

### R1: 知识点匹配率低

**风险**：当前精确匹配率仅 6%

**缓解**：双模型推理提高匹配率，保留未匹配记录

### R2: 手动导入验证成本

**风险**：人工验证 JSON 数据需要时间

**缓解**：
- 输出详细的统计摘要
- 提供 Cypher 导入脚本模板
- 分批验证导入

### R3: 推理依赖

**风险**：依赖 `edukg/core/llm_inference/` 模块

**缓解**：先完成 kg-math-prerequisite-inference

## Migration Plan

**执行步骤**：

1. **开发核心模块**：
   - 创建 `edukg/core/textbook/` 目录
   - 实现 `uri_generator.py`
   - 实现 `filters.py`
   - 实现 `data_generator.py`
   - 实现 `kp_matcher.py`

2. **开发命令行入口**：
   - 创建 `generate_textbook_data.py`
   - 创建 `match_textbook_kp.py`

3. **运行数据生成**：
   - 运行数据生成脚本
   - 输出 JSON 文件

4. **运行推理**：
   - 运行匹配脚本（调用 llm_inference）
   - 输出 matches_kg_relations.json

5. **验证和导入**：
   - 人工验证后手动导入 Neo4j

## Open Questions

1. **Q1**：是否需要先完成 kg-math-prerequisite-inference？
   - 是，推理部分依赖 `edukg/core/llm_inference/` 模块

2. **Q2**：JSON 导入脚本是否需要自动生成？
   - 可选，提供 Cypher 模板即可