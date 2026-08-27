# 分析-10-Neo4j导入与关系构建-业务链路

> summary: Neo4j导入与关系构建业务链路
> 来源: 切片 ｜ 锚点: 业务链路
> 节: 分析-10-Neo4j导入与关系构建
> COS路径: rag-slices/knowledge-graph/代码/分析-10-Neo4j导入与关系构建-业务链路.md
> 类别：业务流程
> target: 开发对账

---

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

**文字链路复述**：入库分两段共 11 步——先 EduKG 基础图谱（Class→Concept→Statement→RELATED_TO→PART_OF/BELONGS_TO，5 步），再人教版教材数据（Textbook→Chapter→Section→TextbookKP→IN_UNIT→MATCHES_KG，6 步），节点必须先于引用它的关系。每步 MERGE 幂等：节点已存在→更新属性、关系已存在→跳过；关系引用的目标节点缺失时用 OPTIONAL MATCH + WHERE IS NOT NULL 静默跳过、不报错。全部导完后跑校验：verify_import 查 Concept 总数/v0.2 小学节点/重复 URI/无类型/版本分布，analyze_textbook_matching 算教材知识点对 Concept 的精确匹配率产出 kp_matching_result.json；运维侧 clear_neo4j 先删全部关系再删全部节点做整库清空，reimport_kg 按依赖顺序一键整库重建（--skip-* 可跳步）。

> 证据：详见 `3.代码/分析-10-Neo4j导入与关系构建.md`（§业务描述与业务场景 / §职责 / §高层业务调用链）
