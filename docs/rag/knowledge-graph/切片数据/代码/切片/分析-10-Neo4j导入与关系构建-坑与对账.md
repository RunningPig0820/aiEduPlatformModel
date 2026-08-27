# 分析-10-Neo4j导入与关系构建-坑与对账

> summary: Neo4j导入与关系构建坑与对账
> 来源: 切片 ｜ 锚点: 坑与对账
> 节: 分析-10-Neo4j导入与关系构建
> COS路径: rag-slices/knowledge-graph/代码/分析-10-Neo4j导入与关系构建-坑与对账.md
> 类别：开发难点
> target: 开发对账

---

## 隐性坑与注意事项

- **README 计数已过期**：README 概览写 Class 38/Concept 1,295/Textbook 21/Chapter 135/Section 549/TextbookKP 1,350/MATCHES_KG 1,042，但实际数据文件是 Class 38/Concept 1,275/Textbook 23/Chapter 153/Section 657/TextbookKP 1,905/matched 1,847——README 只是文档，以实际 JSON 为准。
- **默认数据路径与 README 不符**：`import_textbooks.py:53-57` 默认读 `5_教材目录(Textbook)/textbooks.json`（非 README 写的 `output/textbooks.json`）；`import_math_statements.py:46-50` 默认读 `primary_math_statements.json`（README 写 `math_statement.json`）；`import_math_concepts.py` 默认读 `math_concepts.json`（README 写 `math_complete_statement.json`）。指定 --file 可绕开。
- **静默丢关系**：MATCH 目标不存在的关系被 OPTIONAL MATCH+WHERE 静默跳过，不报错——重导前必须保证节点先于关系导入（顺序即契约）。
- **IN_UNIT 双目标**：`in_unit_relations.json` 的 section_id 既可能指向 Section 也可能指向 Chapter，脚本用 FOREACH 分支处理，两者都不存在则丢。
- **--clear 顺序敏感**：如 `import_textbook_kps.py:100-112` 的 clear 会连带删 IN_UNIT/MATCHES_KG/PREREQUISITE 关系，清 TextbookKP 会破坏其出边——重导需按顺序把关系脚本也重跑。
- **clear_neo4j 不可恢复**：整库清空无确认提示，`MATCH (n) DELETE n` 一次全删。
- **reimport_kg 与分步 import 数据源不同**：reimport 用 `math_statements_uri.json`+`math_statement.json` 组合（content 按 uri 映射），与分步 `import_math_statements.py` 路径不同，两套脚本口径需注意。

## 对账要点（方案 vs 代码现状复盘）

**✅落地：导入方式——方案C CSV/JSON→MERGE 幂等批量导入**
原始方案 D2 定为方案C：CSV/JSON→MERGE 幂等批量导入；代码现状 11 个脚本全 MERGE + 约束 + OPTIONAL MATCH，与方案一致。业务影响：全链路可重跑不产生重复节点/关系。

**✅落地：匹配未导——未匹配记录跳过、人工审核**
原始方案未匹配记录跳过、进人工审核；代码现状 import_matches_kg 过滤 matched && kg_uri 才导。业务影响：308+ 条未匹配记录不落图、只进人工审核流程。

**⚠️不一致：--dry-run 行为——各脚本应统一"仅打印 Cypher"**
原始设计各脚本统一"仅打印 Cypher"；实际 import_math_classes 打印真 Cypher，concepts/relations 只打一行日志。业务影响：预演参考价值参差，不同脚本 dry-run 结果不可比。

**⚠️翻转：README 默认数据路径**
README 写 output/ 或 math_statement.json；代码默认路径不同（textbooks.json 根目录、primary_math_statements.json）。业务影响：按 README 跑会找不到文件，需指定 --file 或按代码默认路径放文件。

**⚠️文档过期：导入结果计数**
README 概览写 Textbook 21/MATCHES_KG 1,042 等；实际数据文件 Textbook 23 / matched 1,847 等。业务影响：README 只是文档，以实际 JSON 为准。

**✅落地：整库重建——reimport_kg 一键重建**
原始方案 reimport_kg 一键重建；代码现状 KGImporter 按 classes→entities→statements→relations 顺序重建，--skip-* 可跳步。业务影响：图谱乱了可一键整库重来。

> 证据：详见 `3.代码/分析-10-Neo4j导入与关系构建.md`（§隐性坑与注意事项 / §对账要点）
