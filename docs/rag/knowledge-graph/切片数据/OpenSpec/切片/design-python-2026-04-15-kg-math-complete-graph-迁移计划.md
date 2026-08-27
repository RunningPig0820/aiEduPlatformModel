# Migration Plan 迁移计划

> summary: 迁移计划：数据生成已完成，知识点推断/图谱匹配/数据清洗/属性扩展/人工导入待执行，各阶段用--resume续传。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-15-kg-math-complete-graph-迁移计划.md
> 类别：操作流程

---

### Migration Plan 迁移计划

> 检索摘要：迁移计划：数据生成已完成，知识点推断/图谱匹配/数据清洗/属性扩展/人工导入待执行，各阶段用--resume续传。

**执行步骤**：

1. **数据生成（已完成）**：
   - ✅ 运行 `generate_textbook_data.py`
   - ✅ 输出 textbooks.json, chapters.json, sections.json, textbook_kps.json
   - ✅ 输出 contains_relations.json, in_unit_relations.json

2. **教学知识点推断（待执行）**：
   - 运行 `infer_textbook_kp.py --resume`
   - 输出更新后的 `textbook_kps.json`
   - 重新生成 `in_unit_relations.json`

3. **知识图谱匹配（待执行）**：
   - 运行 `match_textbook_kp.py --resume`
   - 输出 `matches_kg_relations.json`

4. **数据清洗（新增）**：
   - 运行 `clean_textbook_data.py`
   - 清理"通用"标签、规范 Section 名称
   - 输出清洗报告

5. **知识点属性扩展（新增）**：
   - 运行 `enhance_kp_attributes.py --resume`
   - 推断 difficulty, importance, cognitive_level, topic
   - 输出增强后的 textbook_kps.json

6. **人工验证和导入**：
   - 检查输出文件数据质量
   - 执行 Cypher 导入
   - 验证导入结果

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§Migration Plan 迁移计划）
