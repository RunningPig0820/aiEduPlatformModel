# 数据加工流水线

> summary: 数据加工流水线
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-math-complete-graph-04-数据加工流水线.md
> 类别：操作流程

---

> 检索摘要：教材数据从 JSON 到可导入 Neo4j 的关系文件分几步？代码怎么组织？输出哪些文件？迁移计划各阶段怎么执行？

## 代码目录结构（D1）

核心代码放 edukg/core：
- edukg/core/textbook/：config.py（配置，含 URI 版本）、uri_generator.py（URI 生成器）、filters.py（知识点过滤规则）、data_generator.py（数据生成器）、kp_matcher.py（知识点匹配器）、README.md
- edukg/core/llm_inference/：dual_model_voter.py（双模型投票）、textbook_kp_inferer.py（教学知识点推断，新增）、prompt_templates.py（提示词加载）、prompts/textbook_kg.txt（推断提示词）、prompts/kp_match.txt（匹配提示词）

scripts 只做命令行入口：edukg/scripts/kg_data/ 下 generate_textbook_data.py、infer_textbook_kp.py、match_textbook_kp.py。

## 两阶段流程（D2）

第一阶段：数据生成（无 LLM）——输入教材原始 JSON，过滤非知识点标记，输出标准化 JSON 文件。
第二阶段：LLM 增强——输入第一阶段输出 + Neo4j EduKG 数据，输出推断的教学知识点 + 匹配关系，支持断点续传。

## 输出文件结构（D6）

输出到 edukg/data/edukg/math/5_教材目录/output/：
- 节点：textbooks.json、chapters.json、sections.json、textbook_kps.json
- 关系：contains_relations.json（CONTAINS）、in_unit_relations.json（IN_UNIT）、matches_kg_relations.json（MATCHES_KG 推理结果）
- import_summary.json（导入统计摘要）
- progress/（进度文件目录：infer_kp_state.json、match_kg_state.json、*.lock）

## 迁移计划（Migration Plan）

1. 数据生成（已完成）：运行 generate_textbook_data.py，输出节点与 CONTAINS/IN_UNIT 关系 JSON
2. 教学知识点推断（待执行）：运行 infer_textbook_kp.py --resume，输出更新后的 textbook_kps.json，重新生成 in_unit_relations.json
3. 知识图谱匹配（待执行）：运行 match_textbook_kp.py --resume，输出 matches_kg_relations.json
4. 数据清洗（新增）：运行 clean_textbook_data.py，清理"通用"标签、规范 Section 名称，输出清洗报告
5. 知识点属性扩展（新增）：运行 enhance_kp_attributes.py --resume，推断 difficulty/importance/cognitive_level/topic，输出增强后的 textbook_kps.json
6. 人工验证和导入：检查输出文件数据质量，执行 Cypher 导入，验证导入结果

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D1 / §D2 / §D6 / §Migration Plan）
