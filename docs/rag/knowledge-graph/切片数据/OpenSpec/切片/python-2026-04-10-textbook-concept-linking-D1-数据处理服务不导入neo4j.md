# D1 数据处理服务（不导入 Neo4j）
> summary: 生成 JSON/TTL 文件不直接导入 Neo4j，理由为避免自动创建低质量 Concept、人工确认保准确、匹配报告可追踪、支持回滚和调整。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/python-2026-04-10-textbook-concept-linking-D1-数据处理服务不导入neo4j.md
> 类别：数据关联

> 检索摘要：生成 JSON/TTL 文件不直接导入 Neo4j，理由为避免自动创建低质量 Concept、人工确认保准确、匹配报告可追踪、支持回滚和调整。

**决策**: 生成 JSON/TTL 文件，不直接导入 Neo4j

**理由**:
- 避免自动创建低质量 Concept
- 人工确认确保数据准确
- 匹配报告便于追踪
- 支持回滚和调整

**替代方案**:
- 自动导入 Neo4j：可能创建重复/低质量节点，无法回滚

```
输出文件:
├── edukg/data/eduBureau/math/
│   ├── ocr_result.json              # OCR 结果
│   ├── classes.json                 # Class 定义（Neo4j格式）
│   ├── concepts.json                # Concept 知识点（Neo4j格式）
│   ├── statements.json              # Statement 定义（Neo4j格式）
│   └── relations.json               # 关系（Neo4j格式）
├── edukg/data/output/
│   ├── curriculum_kps.json          # 课标知识点（中间文件）
│   ├── kp_comparison_report.json    # 对比报告
│   ├── textbook_chapters.json       # 章节结构
│   └── matching_report.json         # 匹配报告
```

**JSON 格式要求**:
- 符合 Neo4j 导入格式
- 参考 EduKG 现有数据格式:
  - Class: `edukg/data/edukg/math/1_概念类(Class)/math_classes.json`
  - Entity: `edukg/data/edukg/math/8_全部关联关系(Complete)/math_entities_complete.json`
  - Relation: `edukg/data/edukg/math/8_全部关联关系(Complete)/math_knowledge_relations.json`

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-textbook-concept-linking.md`（§D1 数据处理服务（不导入 Neo4j））
