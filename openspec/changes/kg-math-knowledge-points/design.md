## Context

知识图谱数学数据清洗和导入是整个项目的**试点阶段**。数学学科是唯一有原生关系数据（relateTo, subCategory）的学科，因此选择数学作为试点验证设计方案。

当前状态：
- **数据源**: `ttl/math.ttl`（4,490 个知识点）, `main.ttl`（教材信息）
- **格式问题**: TTL 使用 Unicode 编码，需要解码为中文
- **缺失信息**: 缺少年级信息，需要从教材推断
- **Neo4j schema**: 已由 `kg-neo4j-schema` change 创建

设计约束：
- 使用 RDFLib 解析 TTL 文件
- 输出中间文件格式为 JSON（便于人工检查和后续处理）
- 导入使用 Neo4j Python driver 的批量导入功能

## Goals / Non-Goals

**Goals:**
- 清洗数学知识点数据（4,490 个）
- 提取教材信息，推断年级
- 导入 Neo4j（层级结构 + 知识点节点）
- 验证数据完整性

**Non-Goals:**
- 不导入关系数据（relateTo/subCategory 在后续 change 处理）
- 不推断前置关系（PREREQUISITE 在后续 LLM 推断 change 处理）
- 不处理其他学科（物理/化学等在后续 change 处理）

## Decisions

### D1: TTL 解析方案

**决策**: 使用 RDFLib 库解析 TTL 文件

```python
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS

g = Graph()
g.parse("ttl/math.ttl", format="turtle")
```

**理由**:
- RDFLib 是标准 RDF 解析库，稳定可靠
- 支持 TTL 格式解析
- 支持命名空间和 URI 处理

**替代方案**: 手动解析 TTL 文件
- **缺点**: TTL 格式复杂，容易出现解析错误

### D2: Unicode 解码方案

**决策**: TTL 文件中的中文标签使用 Unicode 编码，需要解码

```python
# Unicode 编码格式: \u4e00\u4e01...
import codecs

def decode_unicode_label(label: str) -> str:
    """解码 Unicode 标签为中文"""
    # RDFLib 已自动解码 Unicode，直接使用 str 即可
    return str(label)
```

**理由**: RDFLib 在解析 TTL 时自动解码 Unicode，无需额外处理

### D3: 知识点类型提取

**决策**: 从 `rdf:type` 和 `edukg:knowledgeType` 提取类型信息

```python
# 类型提取规则
TYPE_MAPPING = {
    "http://edukg.org/ontology#Definition": "定义",
    "http://edukg.org/ontology#Property": "性质",
    "http://edukg.org/ontology#Theorem": "定理",
    "http://edukg.org/ontology#Formula": "公式",
    "http://edukg.org/ontology#Method": "方法",
}
```

**理由**: 保持与 EduKG 标准对齐，便于后续扩展

### D4: 年级推断规则

**决策**: 从教材信息推断年级，使用映射表

```python
# 教材 → 年级映射
TEXTBOOK_GRADE_MAP = {
    "高中数学必修第一册": "高一",
    "高中数学必修第二册": "高二",
    "高中数学选择性必修第一册": "高二",
    "高中数学选择性必修第二册": "高三",
    "高中数学选择性必修第三册": "高三",
    "初中数学七年级上册": "初一",
    "初中数学七年级下册": "初一",
    "初中数学八年级上册": "初二",
    "初中数学八年级下册": "初二",
    "初中数学九年级上册": "初三",
    "初中数学九年级下册": "初三",
}
```

**理由**: 教材名称包含年级信息，映射表便于维护和扩展

### D5: 中间文件格式

**决策**: 输出 JSON 格式中间文件

```
math_knowledge_points.json    # 清洗后的知识点数据
math_textbook_mapping.json    # 教材-知识点映射
math_final_data.json          # 合并后的最终数据
```

**理由**:
- JSON 格式便于人工检查和调试
- 便于后续脚本读取和处理
- 支持增量更新

**替代方案**: 输出 CSV 格式
- **缺点**: 不支持嵌套结构，类型信息表达不便

### D6: Neo4j 批量导入

**决策**: 使用 UNWIND Cypher 语句批量导入

```cypher
UNWIND $knowledge_points AS kp
CREATE (n:KnowledgePoint {
  uri: kp.uri,
  name: kp.name,
  subject: kp.subject,
  grade: kp.grade,
  type: kp.type
})
```

**理由**:
- UNWIND 支持批量操作，性能优于逐条插入
- 支持事务，导入失败可回滚

### D7: 数据验证策略

**决策**: 导入后验证节点数量和关键字段

```python
# 验证规则
VALIDATION_RULES = {
    "node_count": 4490,          # 预期节点数量
    "uri_unique": True,          # URI 唯一性
    "name_not_null": True,       # 名称不为空
    "type_coverage": 0.7,        # 类型覆盖率 ≥ 70%
}
```

**理由**: 数据质量直接影响后续关系推断，需提前验证

## Risks / Trade-offs

### Risk 1: 标签匹配失败
**风险**: 部分知识点无法匹配教材，导致年级信息缺失
**缓解**: 未匹配的知识点标记为 "年级未知"，后续人工补充

### Risk 2: 类型提取覆盖率不足
**风险**: 部分知识点没有类型标注
**缓解**: 统计类型覆盖率，低于阈值时调整提取规则

### Risk 3: 导入失败需要重新处理
**风险**: 导入过程中失败，需要重新清洗和导入
**缓解**: 使用事务批量导入，失败时回滚；保留中间文件便于重新导入

## Migration Plan

**执行步骤**:
1. 运行 `clean_math_data.py` → 输出 `math_knowledge_points.json`
2. 运行 `extract_textbook_info.py` → 输出 `math_textbook_mapping.json`
3. 运行 `merge_math_data.py` → 输出 `math_final_data.json`
4. 人工检查 `math_final_data.json`（抽查 10-20 条）
5. 运行 `import_math_kp_to_neo4j.py` → 导入 Neo4j
6. 运行验证脚本 → 确认数据完整性

**回滚策略**:
```cypher
// 删除所有数学知识点和相关层级节点
MATCH (n:KnowledgePoint {subject: "math"}) DETACH DELETE n
MATCH (n:Subject {code: "math"}) DETACH DELETE n
```

## Open Questions

无（设计已确定）