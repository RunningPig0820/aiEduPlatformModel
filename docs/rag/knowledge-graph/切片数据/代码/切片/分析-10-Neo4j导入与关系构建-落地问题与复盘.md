# 分析-10-Neo4j导入与关系构建-落地问题与复盘

> summary: Neo4j导入与关系构建落地问题与复盘
> 来源: 切片 ｜ 锚点: 落地问题与复盘
> 节: 分析-10-Neo4j导入与关系构建
> COS路径: rag-slices/interview/knowledge-graph/分析-10-Neo4j导入与关系构建-落地问题与复盘.md
> 类别：开发难点
> target: 面试项目问答

---

## 隐性坑与注意事项

1. **README 计数已过期**：README 概览写 Class 38/Concept 1,295/Textbook 21/Chapter 135/Section 549/TextbookKP 1,350/MATCHES_KG 1,042，实际数据文件是 Class 38/Concept 1,275/Textbook 23/Chapter 153/Section 657/TextbookKP 1,905/matched 1,847——README 只是文档，以实际 JSON 为准。
2. **默认数据路径与 README 不符**：textbooks 默认读 `5_教材目录(Textbook)/textbooks.json`（非 README 写的 output/ 下），statements 默认读 `primary_math_statements.json`（README 写 math_statement.json），concepts 默认读 `math_concepts.json`（README 写 math_complete_statement.json）。指定 --file 可绕开。
3. **静默丢关系**：关系引用的目标节点不存在时被 OPTIONAL MATCH 静默跳过、不报错——重导前必须保证节点先于关系导入（顺序即契约）。
4. **IN_UNIT 双目标**：归属关系的 section_id 既可能指向 Section 也可能指向 Chapter，脚本用 FOREACH 分支处理，两者都不存在则丢。
5. **--clear 顺序敏感**：清 TextbookKP 会连带删它的出边（IN_UNIT/MATCHES_KG/PREREQUISITE），重导需按顺序把关系脚本也重跑。
6. **clear_neo4j 不可恢复**：整库清空无确认提示，一次全删所有节点与关系。
7. **reimport_kg 与分步 import 数据源不同**：整库重建用的 statements 数据组合与分步导入脚本的路径/口径不同，两套脚本需注意。

## 方案 vs 落地的复盘（原始设计 → 实际实现 → 影响）

**导入方式（落地）**
原始方案定为方案C：CSV/JSON→MERGE 幂等批量导入；落地 11 个脚本全 MERGE + 约束 + OPTIONAL MATCH。影响：全链路可重跑不产生重复节点/关系。

**匹配未导（落地）**
原始方案未匹配记录跳过、进人工审核；落地匹配关系只导 matched 且带 kg_uri 的记录，未匹配 308+ 条跳过。影响：未匹配数据不污染图谱、只进人工审核。

**--dry-run 行为（不一致）**
原设计各脚本统一"仅打印 Cypher"；实际 classes 打印真 Cypher，concepts/relations 只打一行日志。影响：预演参考价值参差，不同脚本的 dry-run 结果不可比。

**README 默认数据路径（翻转）**
README 写 output/ 或 math_statement.json；代码默认路径不同（textbooks.json 在根目录、statements 用 primary_math_statements.json）。影响：按 README 操作会找不到文件，需 --file 指定或按代码默认路径放文件。

**导入结果计数（文档过期）**
README 概览写 Textbook 21/MATCHES_KG 1,042 等；实际数据文件 Textbook 23 / matched 1,847 等。影响：README 只是文档，以实际 JSON 为准。

**整库重建（落地）**
原始方案 reimport_kg 一键重建；落地 KGImporter 按 classes→entities→statements→relations 顺序重建，--skip-* 可跳步。影响：图谱乱了可一键整库重来。

> 证据：详见 `3.代码/分析-10-Neo4j导入与关系构建.md`（§隐性坑与注意事项 / §对账要点）｜ `4.完善文档/02-知识图谱数据入库主流程.md`
