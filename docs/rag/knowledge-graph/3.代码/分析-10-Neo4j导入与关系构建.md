# 分析-10 Neo4j导入与关系构建（代码真相）

> summary: 解答「图谱数据怎么安全进 Neo4j」——11 个 import 脚本按依赖顺序（Class→Concept→Statement→关系→教材→章节→小节→知识点→归属→匹配）执行，全部 MERGE 幂等可重跑，--dry-run 预演/--clear 清旧库/--stats 查数，关系用 OPTIONAL MATCH 跳过缺失目标，clear_neo4j 一键清库、reimport_kg 整库重建，verify_import 查重复 URI 与 v0.2 小学节点。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-source/knowledge-graph/代码/分析-10-Neo4j导入与关系构建.md
> 类别：数据存储

## 业务描述与业务场景

**业务描述**：清洗/推断/匹配好的 JSON 数据要落进 Neo4j 才能被答疑、学习路径、页面消费。这段代码把 7 类节点（Class/Concept/Statement/Textbook/Chapter/Section/TextbookKP）和 8 类关系（SUB_CLASS_OF/HAS_TYPE/RELATED_TO/PART_OF/BELONGS_TO/CONTAINS/IN_UNIT/MATCHES_KG）按依赖顺序批量写入，且支持反复重跑不产生重复数据。

**业务场景**：
- 数据管道跑完一次匹配，教研点一下导入，全部教材知识点挂进图谱，反复导入不会重复建点
- 匹配失败的 308+ 条记录被跳过（不导入），只进人工审核流程
- 图谱乱了要重来：先 clear_neo4j 一键清库，再按顺序全部重导，或者 reimport_kg 一键整库重建

## 职责

**职责**：处理后的 JSON/TTL → Neo4j 节点与关系（MERGE 幂等、--clear/--dry-run/--stats 三种运行模式、约束创建、缺失目标静默跳过）。
**不做什么**：不做数据清洗/推断/匹配（那是上游 pipeline）、不做图查询服务（那是 ai-service/Java）、不清非本模块数据之外的东西。
**分工要点**：import/ 11 个脚本（两段式：EduKG 基础图谱 5 个 + 人教版教材 6 个），verify/ 校验脚本，tools/ 清库与重建脚本；统一 `edukg/scripts/kg_data/` 下。本主题仅 Python 管道单端。

## 高层业务调用链（教材知识点→Neo4j 图谱入库）

```
【第一部分：EduKG 基础图谱】（依赖顺序，节点先于关系）
1. import_math_classes.py        Class 节点 + SUB_CLASS_OF
2. import_math_concepts.py       Concept 节点 + HAS_TYPE→Class
3. import_math_statements.py     Statement 节点 + HAS_TYPE
4. import_math_relations.py      RELATED_TO（Concept↔Concept / Statement→Concept）
5. import_partof_belongsto.py    PART_OF + BELONGS_TO（从 math_instance.ttl 正则解析）
        │
【第二部分：人教版教材数据】（必须先有 Textbook→Chapter→Section→TextbookKP 节点）
6. import_textbooks.py           Textbook 节点（23 册）
7. import_chapters.py            Chapter 节点 + CONTAINS(Textbook→Chapter)
8. import_sections.py            Section 节点 + CONTAINS(Chapter→Section)
9. import_textbook_kps.py        TextbookKP 节点（含 difficulty/importance/cognitive_level/topic）
10. import_in_unit_relations.py  IN_UNIT（TextbookKP→Section，兼容落 Chapter）
11. import_matches_kg.py         MATCHES_KG（仅 matched=true 且 kg_uri 非空，带 confidence/method）
        │
        ├── 每步 MERGE 幂等：节点已存在→更新属性；关系已存在→跳过
        ├── 缺失目标节点 → OPTIONAL MATCH + WHERE IS NOT NULL 静默跳过
        ▼
校验/运维
  verify_import.py          Concept 总数/v0.2 小学节点/重复 URI/无类型/版本分布
  analyze_textbook_matching.py  教材知识点 vs Concept label 精确匹配率 → kp_matching_result.json
  clear_neo4j.py            MATCH ()-[r]->() DELETE r + MATCH (n) DELETE n（整库清空）
  reimport_kg.py            一键整库重建（--skip-* 可跳步）
```

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

## 隐性坑与注意事项
- **README 计数已过期**：README 概览写 Class 38/Concept 1,295/Textbook 21/Chapter 135/Section 549/TextbookKP 1,350/MATCHES_KG 1,042，但实际数据文件是 Class 38/Concept 1,275/Textbook 23/Chapter 153/Section 657/TextbookKP 1,905/matched 1,847——README 只是文档，以实际 JSON 为准。
- **默认数据路径与 README 不符**：`import_textbooks.py:53-57` 默认读 `5_教材目录(Textbook)/textbooks.json`（非 README 写的 `output/textbooks.json`）；`import_math_statements.py:46-50` 默认读 `primary_math_statements.json`（README 写 `math_statement.json`）；`import_math_concepts.py` 默认读 `math_concepts.json`（README 写 `math_complete_statement.json`）。指定 --file 可绕开。
- **静默丢关系**：MATCH 目标不存在的关系被 OPTIONAL MATCH+WHERE 静默跳过，不报错——重导前必须保证节点先于关系导入（顺序即契约）。
- **IN_UNIT 双目标**：`in_unit_relations.json` 的 section_id 既可能指向 Section 也可能指向 Chapter，脚本用 FOREACH 分支处理，两者都不存在则丢。
- **--clear 顺序敏感**：如 `import_textbook_kps.py:100-112` 的 clear 会连带删 IN_UNIT/MATCHES_KG/PREREQUISITE 关系，清 TextbookKP 会破坏其出边——重导需按顺序把关系脚本也重跑。
- **clear_neo4j 不可恢复**：整库清空无确认提示，`MATCH (n) DELETE n` 一次全删。
- **reimport_kg 与分步 import 数据源不同**：reimport 用 `math_statements_uri.json`+`math_statement.json` 组合（content 按 uri 映射），与分步 `import_math_statements.py` 路径不同，两套脚本口径需注意。

## 设计要点
- **方案 C：计算与存储分离**（语雀 D2）：关系处理在 Python/JSON 完成，Neo4j 只是最后仓库；CSV/JSON 可教研维护、权威基准冻结。
- **MERGE 幂等作为安全网**：全链路可重跑，失败后重导不产生重复节点/关系（README:150-154）。
- **OPTIONAL MATCH 容错**：外部本体（Class 父类）、未匹配类型等缺失目标静默跳过，不因少量脏数据中断整批。
- **约束先建**：uri/id 唯一约束兜底防重，与 MERGE 双保险。
- **顺序即契约**：节点先于引用它的关系，READM 明确"必须按以下顺序导入"（README:7-9）。

## 对账要点
| 对账分类 | 项 | 语雀/design 口径 | 代码现状 | 结论 |
|---|---|---|---|---|
| 方案vs实现 | 导入方式 | D2：方案C CSV/JSON→MERGE 幂等批量导入 | 11 脚本全 MERGE + 约束 + OPTIONAL MATCH | ✅ 落地 |
| 方案vs实现 | 匹配未导 | 未匹配记录跳过、人工审核 | import_matches_kg 过滤 matched && kg_uri | ✅ 落地 |
| 接口契约 | --dry-run 行为 | 各脚本统一"仅打印 Cypher" | classes 打印真 Cypher，concepts/relations 只打日志 | ⚠️不一致 |
| 注释vs运行行为 | README 默认数据路径 | README 写 output/ 或 math_statement.json | 代码默认路径不同（textbooks.json 根目录、primary_math_statements.json） | ⚠️翻转 |
| 注释vs运行行为 | 导入结果计数 | README 概览（Textbook 21/MATCHES_KG 1042 等） | 实际数据文件 Textbook 23 / matched 1847 等 | ⚠️文档过期 |
| 方案vs实现 | 整库重建 | reimport_kg 一键重建 | KGImporter 顺序 classes→entities→statements→relations，--skip-* | ✅ 落地 |

## 已读代码清单
- **Python 管道（edukg）**：
  - `edukg/scripts/kg_data/import/README.md`（导入顺序 11 步/脚本详解/参数/重复导入）
  - `edukg/scripts/kg_data/import/import_math_classes.py`（MathClassImporter: create_constraints/import_classes/import_relationships OPTIONAL MATCH）
  - `edukg/scripts/kg_data/import/import_math_concepts.py`（MathConceptImporter: import_concepts MERGE/import_type_relations）
  - `edukg/scripts/kg_data/import/import_math_statements.py`（StatementImporter: import_statements/import_has_type_relations）
  - `edukg/scripts/kg_data/import/import_math_relations.py`（MathRelationImporter: import_relations MATCH by uri）
  - `edukg/scripts/kg_data/import/import_partof_belongsto.py`（PartOfBelongsToImporter: parse_ttl 正则/import_relations）
  - `edukg/scripts/kg_data/import/import_textbooks.py`（TextbookImporter: clear_textbooks/import_textbooks）
  - `edukg/scripts/kg_data/import/import_chapters.py`（ChapterImporter: import_chapters/import_contains_textbook_chapter）
  - `edukg/scripts/kg_data/import/import_sections.py`（SectionImporter: import_sections/import_contains_chapter_section）
  - `edukg/scripts/kg_data/import/import_textbook_kps.py`（TextbookKPImporter: clear_kps/import_kps）
  - `edukg/scripts/kg_data/import/import_in_unit_relations.py`（InUnitRelationImporter: FOREACH 分支 Section/Chapter）
  - `edukg/scripts/kg_data/import/import_matches_kg.py`（MatchesKGImporter: matched 过滤/import_matches_kg_relations）
  - `edukg/scripts/kg_data/verify/verify_import.py`（Concept 数/v0.2/重复 URI/无类型/版本分布）
  - `edukg/scripts/kg_data/verify/analyze_textbook_matching.py`（exclude_kps 过滤/精确匹配/kp_matching_result.json）
  - `edukg/scripts/kg_data/tools/clear_neo4j.py`（整库清空）
  - `edukg/scripts/kg_data/tools/reimport_kg.py`（KGImporter: import_classes/import_entities/import_statements/import_has_type_relations/import_related_to_relations/import_partof_belongsto）
- **Python 桥（ai-service）**：未直读（脚本仅经 `edukg.core.neo4j.client.Neo4jClient` 连库）。
- **Java**：无（本主题不涉）。
- **前端**：无（本主题不涉）。
> 本主题跨 1 端（Python edukg）；仅 Python 端有实际读取。
