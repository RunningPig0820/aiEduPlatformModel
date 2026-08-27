# 分析-02-TTL数据拆分与Neo4jSchema-代码事实-3
> summary: TTL数据拆分与Neo4jSchema代码事实-3（枚举常量与设计要点）
> 来源: 切片 ｜ 锚点: 代码事实-3
> 节: 分析-02-TTL数据拆分与Neo4jSchema
> COS路径: rag-slices/knowledge-graph/代码/分析-02-TTL数据拆分与Neo4jSchema-代码事实-3.md
> 类别：架构设计
> target: 开发对账

---

## 代码事实

### 枚举/常量/配置

| 类型 | 名称 | 取值 | 出处 |
|---|---|---|---|
| 默认学科 | DEFAULT_SUBJECTS | biology/chemistry/chinese/geo/history/math/physics/politics（8） | split_main_ttl.py:40 |
| URI 学科正则 | SUBJECT_URI_PATTERN | `instance/([^/#]+)[#/]` | split_main_ttl.py:43 |
| 学科关键词 | SUBJECT_KEYWORDS | 数学→math/物理→physics/化学→chemistry/生物·生物学→biology/历史→history/地理→geo/语文→chinese/英语→english/思想政治·政治→politics（10 词） | split_material_ttl.py:44-56 |
| 教材类型 URI | TEXTBOOK_CLASS_URI | `.../3.0/ontology/class/resource#C3` | split_material_ttl.py:62 |
| 名称属性 URI | NAME_PROPERTY_URI | `.../data_property/resource#P4` | split_material_ttl.py:65 |
| 图片路径属性 URI | IMAGE_PATH_PROPERTY_URI | `.../data_property/resource#P7` | split_material_ttl.py:68 |
| 包含关系 | PARENT_CHILD_RELATIONS | P13(hasLesson)/P2(hasUnit)/P3(hasSection)；P5 已移除 | split_material_ttl.py:70-79 |
| 节点标签 | NODE_LABELS | Subject/Stage/Grade/Textbook/Chapter/KnowledgePoint（6） | create_neo4j_schema.py:45-52 |
| 唯一约束 | UNIQUE_CONSTRAINTS | kp_uri_unique(KnowledgePoint.uri)/subject_code_unique(Subject.code)/textbook_isbn_unique(Textbook.isbn) | create_neo4j_schema.py:56-61 |
| 关系类型 | RELATIONSHIP_TYPES | HAS_STAGE/HAS_GRADE/USE_TEXTBOOK/HAS_CHAPTER/HAS_KNOWLEDGE_POINT/PREREQUISITE/TEACHES_BEFORE/PREREQUISITE_ON/PREREQUISITE_CANDIDATE/RELATED_TO/SUB_CATEGORY（10） | create_neo4j_schema.py:66-81 |
| Neo4j 连接 | NEO4J_URI/USER/PASSWORD/DATABASE | bolt://localhost:7687 / neo4j / (env) / neo4j | edukg/config/settings.py:31-36 |
| 三元组量级 | main.ttl / material.ttl | 约 16MB / 3.5MB | kg_split/README.md:9-10 |

## 设计要点

- **性能索引延迟创建**：先建唯一约束（防重复）→ 批量导入 → 后建性能索引，避免批量导入 10x 变慢与索引碎片化（create_neo4j_schema.py:9；kg_split/README.md:129-137）。
- **material 用 RDF 类型而非 URI 模式识别学科**：main.ttl 实体 URI 含学科前缀可直接正则，material.ttl 实体 URI 不体现学科，故改用 C3 类型 + P4 名称关键词 + 关系传播（split_material_ttl.py:8-12,164-173）。
- **关系传播 BFS 化**：只沿真实包含关系（P13/P2/P3）递归传播，保证"教材→章→节→子节"全链路学科一致（split_material_ttl.py:237-243）。
- **不验证不阻断**：拆分三元组数量校验仅告警；约束创建失败单条 continue——拆分/schema 工序让"数据质量门禁"更靠后的导入/校验阶段把关。
- **dry-run 友好**：create_neo4j_schema 支持 `--dry-run` 只打印 Cypher，validate 支持 `--verbose`，便于 CI 前预览。

> 证据：详见 `3.代码/分析-02-TTL数据拆分与Neo4jSchema.md`（§代码事实 / §设计要点）
