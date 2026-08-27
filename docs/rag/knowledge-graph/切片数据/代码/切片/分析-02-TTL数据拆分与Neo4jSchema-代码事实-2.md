# 分析-02-TTL数据拆分与Neo4jSchema-代码事实-2
> summary: TTL数据拆分与Neo4jSchema代码事实-2（schema 建约束与验证）
> 来源: 切片 ｜ 锚点: 代码事实-2
> 节: 分析-02-TTL数据拆分与Neo4jSchema
> COS路径: rag-slices/knowledge-graph/代码/分析-02-TTL数据拆分与Neo4jSchema-代码事实-2.md
> 类别：架构设计
> target: 开发对账

---

## 代码事实

### 关键机制：create_neo4j_schema（唯一约束，不含性能索引）

1. **节点标签**：`NODE_LABELS` 6 个（Subject/Stage/Grade/Textbook/Chapter/KnowledgePoint）（create_neo4j_schema.py:45-52）
2. **唯一约束**：`UNIQUE_CONSTRAINTS` 3 个——
   - `kp_uri_unique`（KnowledgePoint.uri）、`subject_code_unique`（Subject.code）、`textbook_isbn_unique`（Textbook.isbn）（create_neo4j_schema.py:56-61）
   - Cypher：`CREATE CONSTRAINT IF NOT EXISTS {name} FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE`（create_neo4j_schema.py:117-120）
3. **性能索引延迟**：注释与 README 明确"性能索引延迟到数据导入后创建（design.md D4）"——先建索引再批量插入会导致导入时间 10x+ 和索引碎片化（create_neo4j_schema.py:9,180；kg_split/README.md:129-137）
4. **关系类型**：`RELATIONSHIP_TYPES` 10 个仅作文档参考，Neo4j 关系类型使用时自动创建无需预定义（create_neo4j_schema.py:64-81）
5. **容错**：单个约束创建失败只 `continue` 记录错误，不中断整体（create_neo4j_schema.py:129-131）；`--dry-run` 只打印 Cypher 不执行（create_neo4j_schema.py:175-181）

### 关键机制：validate_schema（验证标签与约束）

1. 用 `CALL db.labels()` 取现有标签、`SHOW CONSTRAINTS` 取约束（validate_schema.py:78-88）
2. 比对 `EXPECTED_LABELS`（6）与 `EXPECTED_CONSTRAINTS`（3），缺任一标记 missing（validate_schema.py:90-139）
3. 全过 → 退出码 0；缺 → 退出码 1 并提示"请先运行 create_neo4j_schema.py"（validate_schema.py:190-197）；连接异常 → 退出码 1（validate_schema.py:199-201）
4. 明确"不验证性能索引"（validate_schema.py:9）

### 边界与降级

- 输入文件不存在 → 日志报错 + `sys.exit(1)`（split_main_ttl.py:302-304；split_material_ttl.py:436-438）
- rdflib 未安装 → split_material_ttl 提示安装并退出（split_material_ttl.py:28-32）
- 拆分后三元组数量不等 → 打 ✗ 但**不中断**，照常返回 stats（split_main_ttl.py:260）
- material 中无名称的实体（如 C9 图片无 P7）→ 归 unknown；`--skip-unknown` 可跳过（split_material_ttl.py:348-350）
- 约束创建失败 → 记录错误 continue（create_neo4j_schema.py:129-131）
- Neo4j 连接失败 → create/validate 主流程 catch Exception → `sys.exit(1)`（create_neo4j_schema.py:201-203；validate_schema.py:199-201）

> 证据：详见 `3.代码/分析-02-TTL数据拆分与Neo4jSchema.md`（§代码事实）
