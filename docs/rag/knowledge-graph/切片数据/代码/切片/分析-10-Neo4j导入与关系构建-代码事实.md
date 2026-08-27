# 分析-10-Neo4j导入与关系构建-代码事实

> summary: Neo4j导入与关系构建代码事实
> 来源: 切片 ｜ 锚点: 代码事实
> 节: 分析-10-Neo4j导入与关系构建
> COS路径: rag-slices/knowledge-graph/代码/分析-10-Neo4j导入与关系构建-代码事实.md
> 类别：架构设计
> target: 开发对账

---

## 代码事实

### 端点清单（CLI 统一参数）
| 参数 | 作用 | 证据 |
|---|---|---|
| `python import_*.py` | 正常导入（MERGE 幂等） | import/README.md:131-136 |
| `--dry-run` | 预演：多数脚本打印 Cypher 不执行 | import_math_classes.py:310-314 |
| `--clear` | 先清本类节点/关系再导入 | import_textbooks.py:234-235 |
| `--clear-only` | 仅清不导入 | import_textbooks.py:220-223 |
| `--stats` | 仅查库统计 | import_math_concepts.py:294-296 |
| `--file PATH` | 指定数据文件 | import_textbooks.py:211 |
| `--batch-size N` | 批量大小 | import_math_concepts.py:265 |

### 关键机制
1. **MERGE 幂等**：所有节点用 `MERGE (x:Label {uri: ...}) SET ...`（如 `import_textbooks.py:149-160`），关系用 `MERGE (a)-[:REL]->(b)`，重复导入更新属性/跳过已存在关系——README"重复导入"节明示支持安全重跑（README:150-154）。
2. **约束**：`CREATE CONSTRAINT xxx_uri_unique IF NOT EXISTS FOR (n:Label) REQUIRE n.uri IS UNIQUE`，Class/Textbook/Chapter/Section 还建 `id` 唯一约束（如 `import_math_classes.py:84-108`）。
3. **缺失目标静默跳过**：关系导入用 `OPTIONAL MATCH ... WHERE target IS NOT NULL`（`import_math_classes.py:199-209` SUB_CLASS_OF 父类可能外部本体、`import_math_concepts.py:187-195` HAS_TYPE Class 可能缺失）；`import_in_unit_relations.py:103-116` 用 FOREACH+CASE 先匹配 Section、无则落 Chapter——目标不在则不建关系、不报错。
4. **匹配关系只导已匹配**：`import_matches_kg.py` 过滤 `r.get('matched') and r.get('kg_uri')`（:96-106），SET 关系属性 confidence/method（:121-131），未匹配记录跳过（README:125 "308 条未匹配后续人工审核"）。
5. **RELATED_TO 跨类型**：`import_math_relations.py:118-123` 用 `MATCH (from {uri}) MATCH (to {uri})` 不带 label，Concept 与 Statement 均可作起终点。
6. **PART_OF/BELONGS_TO 从 TTL 正则解析**：`import_partof_belongsto.py:76-123` 按行 `re.match(r'<(http://edukg.org/knowledge/0.1/instance/math#\d+)>')` 取主体，`re.findall(r'ns3:partOf...')`/`ns3:belongsTo` 取宾语。
7. **整库清空与重建**：`clear_neo4j.py:26-31` 先删全部关系再删全部节点；`reimport_kg.py:504-518` 按 classes→entities→statements→relations(HAS_TYPE/RELATED_TO/PART_OF/BELONGS_TO) 顺序重建，`--skip-*` 可跳步。
8. **校验**：`verify_import.py` 查 5 项（Concept 总数/v0.2 小学节点/重复 URI/无类型 Concept/v0.1 vs v0.2 分布）；`analyze_textbook_matching.py` 把教材 JSON 的 knowledge_points 与 Concept label 做集合精确匹配，产出 `kp_matching_result.json`。

### 枚举/常量/配置
| 类型 | 名称 | 取值 | 出处 |
|---|---|---|---|
| 节点标签 | Class/Concept/Statement/Textbook/Chapter/Section/TextbookKP | 7 类 | import/README.md:159-170 |
| 关系类型 | SUB_CLASS_OF/HAS_TYPE/RELATED_TO/PART_OF/BELONGS_TO/CONTAINS/IN_UNIT/MATCHES_KG | 8 类 | import/README.md:172-181 |
| URI 版本 | v0.1（EduKG 原始） / v0.2（小学新增，uri CONTAINS '0.2'） | verify_import.py:82-92 |
| 匹配方法 | method 属性：standard/llm 等（按数据） | import_matches_kg.py:141-147 |
| 批大小 | Concept/Statement 500、Relation 1000、reimport Class 100 | 各脚本 batch_size |
| 导入顺序 | EduKG 5 步 + 教材 6 步，共 11 步 | import/README.md:7-26 |

### 边界与降级
- `--dry-run` 表现不一致：`import_math_classes` 真打印 Cypher（:132-142），`import_math_concepts` 只打一行"[DRY-RUN] 将导入 N 个知识点"（:299-301），`import_math_relations` 也只打日志（:247-249）——预演参考价值参差。
- `--clear` 是本类节点级删除，不是整库（`import_textbooks.py:114-127` 只删 Textbook 与 Textbook 的 CONTAINS）；整库清空要用 `clear_neo4j.py`。
- 连接失败：每个脚本 `test_connection()` 失败 `sys.exit(1)`（如 `import_math_classes.py:288-291`）。
- 数据文件缺失：`load_data` 抛 FileNotFoundError 退出（如 `import_textbooks.py:78-87`）。

## 设计要点

- **方案 C：计算与存储分离**（语雀 D2）：关系处理在 Python/JSON 完成，Neo4j 只是最后仓库；CSV/JSON 可教研维护、权威基准冻结。
- **MERGE 幂等作为安全网**：全链路可重跑，失败后重导不产生重复节点/关系（README:150-154）。
- **OPTIONAL MATCH 容错**：外部本体（Class 父类）、未匹配类型等缺失目标静默跳过，不因少量脏数据中断整批。
- **约束先建**：uri/id 唯一约束兜底防重，与 MERGE 双保险。
- **顺序即契约**：节点先于引用它的关系，READM 明确"必须按以下顺序导入"（README:7-9）。

> 证据：详见 `3.代码/分析-10-Neo4j导入与关系构建.md`（§代码事实 / §设计要点）
