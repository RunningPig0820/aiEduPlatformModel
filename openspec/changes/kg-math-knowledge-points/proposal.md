> **执行顺序: 2/5** | **设计成本: 无** | **前置依赖: kg-neo4j-schema**

## Why

知识图谱数据整理项目需要将数学学科的 TTL 数据清洗并导入 Neo4j。数学是**试点学科**（唯一有原生关系数据的学科），处理数学数据可以验证整体设计方案的可行性。

当前数据问题：
- TTL 文件使用 Unicode 编码，需要解码
- 数据格式不统一（v0.1 vs v3.0）
- 缺少年级信息，需要从教材信息推断
- 知识点类型信息（定义/性质/定理/公式/方法）需要提取

## What Changes

1. **数据清洗脚本**
   - 解析 `ttl/math.ttl` 提取知识点（4,490 个）
   - 解码 Unicode 标签为中文
   - 提取知识点名称、描述、类型、学科路径
   - 去重、清洗无效数据
   - 输出标准化 JSON 文件

2. **教材信息提取**
   - 解析 `main.ttl` 提取教材信息
   - 通过标签匹配知识点与教材
   - 推断年级信息（补充初中映射）
   - 输出教材-知识点映射 JSON

3. **数据合并脚本**
   - 合并知识点数据 + 教材信息
   - 填充年级、章节字段
   - 输出最终导入数据 JSON

4. **Neo4j 导入脚本**
   - 导入学科/学段/年级节点（层级结构）
   - 导入教材/章节节点
   - 导入知识点节点（含类型信息）
   - 验证节点数量

5. **性能索引创建（数据导入后）**
   - 创建单字段索引：name, uri, subject, grade
   - 创建复合索引：subject + grade
   - 验证索引全部 online
   - **为什么在导入后创建？** 先创建索引再批量插入会导致性能下降 10x+

## Capabilities

### New Capabilities

- `ttl-data-cleaner`: TTL 文件解析和清洗能力，支持 Unicode 解码、数据去重、格式标准化
- `textbook-info-extractor`: 教材信息提取能力，支持标签匹配和年级推断
- `knowledge-point-importer`: 知识点批量导入 Neo4j 能力，支持层级结构创建
- `kp-index-creator`: 性能索引创建能力，在数据导入后创建查询优化索引

### Modified Capabilities

无（这是新能力，不修改现有能力）

## Impact

- **新脚本**: `clean_math_data.py`, `extract_textbook_info.py`, `merge_math_data.py`, `import_math_kp_to_neo4j.py`, `create_kp_indexes.py`
- **中间文件**: `math_knowledge_points.json`, `math_textbook_mapping.json`, `math_final_data.json`
- **Neo4j**: 新增约 4,490 个 KnowledgePoint 节点，5 个性能索引（数据导入后创建）
- **依赖**: 依赖 `kg-neo4j-schema` change 完成并测试通过（仅需要唯一性约束）